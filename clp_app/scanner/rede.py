# clp_app/scanner/rede.py

import logging
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
from clp_app.scanner import portas

from scapy.all import IP, get_working_ifaces, sniff
from utils import CLP as clp_manager
from utils import clp_functions, log

# --- Configurações do Módulo ---
QUEUE_MAXSIZE = 2000  # Tamanho máximo da fila de IPs para processamento
WORKER_THREADS = 10   # Número de threads para escanear portas simultaneamente
IP_TTL_SECONDS = 300  # Não re-escanear o mesmo IP por 5 minutos
INTERFACE = None      # Deixe como None para Scapy escolher a melhor interface
BPF_FILTER = "arp or (tcp and (tcp[tcpflags] & (tcp-syn) != 0))" # Filtro para capturar tráfego relevante
IGNORE_LOCAL = True   # Ignorar pacotes originados da própria máquina
LOG_PREFIX = "[Coletor]"

# --- Variáveis Globais de Estado ---
_fila_ips = Queue(maxsize=QUEUE_MAXSIZE)
_ips_last_seen = {}
_ips_lock = Lock()
_shutdown_evt = Event()

_sniffer_thread = None
_consumer_thread = None

# --- Funções Auxiliares ---

def _get_local_ips():
    """Obtém uma lista de todos os endereços IP locais da máquina."""
    local_ips = {"127.0.0.1"}
    try:
        # Obtém o endereço IP associado ao hostname
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None)
        for item in addrs:
            # item[4][0] contém o endereço IP
            if item[4]:
                local_ips.add(item[4][0])
    except socket.gaierror:
        # Tenta uma abordagem alternativa se a primeira falhar
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ips.add(s.getsockname()[0])
        except Exception as e:
            log.log_coleta(f"{LOG_PREFIX} Não foi possível determinar o IP local: {e}", level=logging.WARNING)
    return local_ips

# Pré-calcula os IPs locais para otimização
_LOCAL_IPS = _get_local_ips() if IGNORE_LOCAL else set()

def _should_process_ip(ip: str) -> bool:
    """Verifica se um IP deve ser processado com base no seu último tempo de varredura (TTL)."""
    if IGNORE_LOCAL and ip in _LOCAL_IPS:
        return False

    now = time.time()
    with _ips_lock:
        last_seen_time = _ips_last_seen.get(ip)
        if last_seen_time is None or (now - last_seen_time) >= IP_TTL_SECONDS:
            _ips_last_seen[ip] = now
            return True
    return False

# --- Lógica Principal: Coletor (Sniffer) e Consumidor ---

def _analisar_pacote(pkt):
    """
    Função de callback para cada pacote capturado pelo Scapy.
    Filtra e adiciona IPs relevantes à fila de processamento.
    """
    if IP not in pkt:
        return

    ip_src = pkt[IP].src
    
    if _should_process_ip(ip_src):
        try:
            _fila_ips.put_nowait(ip_src)
        except Full:
            # A fila está cheia; normal em redes com muito tráfego. Apenas ignora.
            pass

def _sniffer_loop():
    """
    Thread principal que executa a captura de pacotes.
    Bloqueia até que o evento de desligamento seja acionado.
    """
    log.log_coleta(f"{LOG_PREFIX} Iniciando a escuta de pacotes na interface '{INTERFACE or 'padrão'}'...")
    try:
        # 'stop_filter' é a maneira mais eficiente de parar o sniff
        sniff(
            prn=_analisar_pacote,
            filter=BPF_FILTER,
            store=False,
            iface=INTERFACE,
            stop_filter=lambda p: _shutdown_evt.is_set()
        )
        log.log_coleta(f"{LOG_PREFIX} Escuta de pacotes terminada.")
    except Exception as e:
        log.log_coleta(f"{LOG_PREFIX} ERRO CRÍTICO NO SNIFFER: {e}", level=logging.ERROR)
        # Em caso de erro crítico no sniffer, sinaliza para o sistema todo parar
        _shutdown_evt.set()

def _consumidor_loop():
    """
    Thread que consome IPs da fila e os submete para escaneamento de portas.
    Usa um ThreadPool para processar múltiplos IPs em paralelo.
    """
    log.log_coleta(f"{LOG_PREFIX} Consumidor iniciado com {WORKER_THREADS} workers.")
    
    def escanear_e_salvar_job(ip: str):
        """Função executada por cada worker para escanear e salvar dados do CLP."""
        try:
            # Lista de portas que indicam um dispositivo de interesse
            portas_abertas = portas.escanear_portas(ip, portas_alvo=[502, 102, 44818, 80, 443])
            
            if portas_abertas:
                clp_existente = clp_manager.buscar_por_ip(ip)
                if clp_existente:
                    # Atualiza portas do CLP existente
                    for porta in portas_abertas:
                        clp_functions.adicionar_porta(clp_existente, porta)
                else:
                    # Cria um novo registro de CLP
                    novo_clp = clp_functions.criar_clp(IP=ip, PORTAS=portas_abertas)
                    clp_manager.adicionar_clp(novo_clp)
                
                # Salva as alterações no arquivo de CLPs
                clp_manager.salvar_clps()
        except Exception as e:
            log.log_coleta(f"{LOG_PREFIX} Erro ao processar o IP {ip}: {e}", level=logging.ERROR)

    with ThreadPoolExecutor(max_workers=WORKER_THREADS) as executor:
        while not _shutdown_evt.is_set():
            try:
                ip_para_escanear = _fila_ips.get(timeout=1.0)
                executor.submit(escanear_e_salvar_job, ip_para_escanear)
                _fila_ips.task_done()
            except Empty:
                # Fila vazia, continua o loop para verificar o sinal de desligamento
                continue
    
    log.log_coleta(f"{LOG_PREFIX} Consumidor finalizado.")

# --- Interface Pública de Controle ---

def start_system():
    """
    Inicia e gerencia as threads de coleta e processamento.
    Retorna as threads para monitoramento externo, se necessário.
    """
    global _sniffer_thread, _consumer_thread

    # Validação prévia: verifica se há interfaces de rede funcionais
    if not get_working_ifaces():
        log.log_coleta(
            f"{LOG_PREFIX} ERRO CRÍTICO: Nenhuma interface de rede funcional encontrada. "
            "Verifique a conectividade e a instalação do Npcap/WinPcap.",
            level=logging.CRITICAL
        )
        return None, None

    # Reseta o evento de desligamento
    _shutdown_evt.clear()

    # Inicia a thread do consumidor
    _consumer_thread = Thread(target=_consumidor_loop, name="ConsumidorThread", daemon=True)
    _consumer_thread.start()

    # Inicia a thread do sniffer
    _sniffer_thread = Thread(target=_sniffer_loop, name="SnifferThread", daemon=True)
    _sniffer_thread.start()
    
    log.log_coleta(f"{LOG_PREFIX} Sistema de coleta iniciado com sucesso.")
    return _sniffer_thread, _consumer_thread

def stop_system(timeout=5.0):
    """
    Sinaliza e aguarda o encerramento gracioso das threads do sistema.
    """
    global _sniffer_thread, _consumer_thread
    
    if _shutdown_evt.is_set():
        log.log_coleta(f"{LOG_PREFIX} O sistema já está em processo de parada.", level=logging.INFO)
        return

    log.log_coleta(f"{LOG_PREFIX} Sinal de parada enviado. Aguardando finalização das threads...")
    _shutdown_evt.set()

    # Aguarda a thread do sniffer
    if _sniffer_thread and _sniffer_thread.is_alive():
        _sniffer_thread.join(timeout=2.0)
        if _sniffer_thread.is_alive():
            log.log_coleta(f"{LOG_PREFIX} Timeout ao aguardar o sniffer.", level=logging.WARNING)
    
    # Aguarda a thread do consumidor
    if _consumer_thread and _consumer_thread.is_alive():
        _consumer_thread.join(timeout=timeout)
        if _consumer_thread.is_alive():
            log.log_coleta(f"{LOG_PREFIX} Timeout ao aguardar o consumidor.", level=logging.WARNING)
    
    log.log_coleta(f"{LOG_PREFIX} Sistema parado.")