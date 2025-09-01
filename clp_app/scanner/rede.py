# clp_app/scanner/rede.py
from threading import Thread, Lock, Event
from queue import Queue, Full, Empty
# CORREÇÃO: Usaremos a função 'sniff' padrão, que é mais robusta
from scapy.all import sniff, IP, get_working_ifaces
from concurrent.futures import ThreadPoolExecutor
import time
import socket
import logging

from utils import log
from clp_app.scanner import portas
from utils import CLP as clp_manager
from utils import clp_functions

# Configurações
QUEUE_MAXSIZE = 2000
WORKER_THREADS = 10
IP_TTL_SECONDS = 300
INTERFACE = None
BPF_FILTER = "arp or (tcp and (tcp[tcpflags] & (tcp-syn) != 0))"
IGNORE_LOCAL = True
LOG_PREFIX = "[Coletor]"

fila = Queue(maxsize=QUEUE_MAXSIZE)
_ips_last_seen = {}
_ips_lock = Lock()
_shutdown_evt = Event()

# --- Threads Globais para Controle ---
_sniffer_thread = None
_consumer_thread = None

def _get_local_ips():
    local_ips = set()
    try:
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
        for a in addrs:
            local_ips.add(a[4][0])
    except Exception:
        pass
    local_ips.add("127.0.0.1")
    return local_ips

_LOCAL_IPS = _get_local_ips() if IGNORE_LOCAL else set()

def _should_process_ip(ip: str) -> bool:
    now = time.time()
    with _ips_lock:
        last = _ips_last_seen.get(ip)
        if last is None or (now - last) >= IP_TTL_SECONDS:
            _ips_last_seen[ip] = now
            return True
        return False

# --- LÓGICA DE COLETA REFEITA PARA MAIOR ROBUSTEZ ---

def analisar_pacote(pkt):
    """Função chamada para cada pacote capturado."""
    if IP not in pkt: return
    ip_src = pkt[IP].src
    if IGNORE_LOCAL and ip_src in _LOCAL_IPS: return
    if not _should_process_ip(ip_src): return
    try:
        fila.put_nowait(ip_src)
    except Full:
        pass

def sniff_loop():
    """Função que executa o 'sniff' e bloqueia até ser parada."""
    global _shutdown_evt
    log.log_coleta(f"{LOG_PREFIX} Iniciando a escuta de pacotes...")
    try:
        # O 'stop_filter' verifica o nosso evento de parada a cada pacote
        sniff(prn=analisar_pacote, 
              filter=BPF_FILTER, 
              store=False, 
              iface=INTERFACE,
              stop_filter=lambda p: _shutdown_evt.is_set())
        log.log_coleta(f"{LOG_PREFIX} Escuta de pacotes terminada normalmente.")
    except Exception as e:
        log.log_coleta(f"{LOG_PREFIX} ERRO DURANTE A EXECUÇÃO DO SNIFFER: {e}", level=logging.ERROR)

def start_system():
    """Inicia os processos de coleta (sniffer e consumidor)."""
    global _sniffer_thread, _consumer_thread
    
    # Verifica se há interfaces de rede antes de tudo
    if not get_working_ifaces():
        log.log_coleta(f"{LOG_PREFIX} ERRO CRÍTICO: Nenhuma interface de rede funcional encontrada. Verifique a instalação do Npcap.", level=logging.CRITICAL)
        return None, None

    _shutdown_evt.clear()

    # Inicia o consumidor
    _consumer_thread = Thread(target=consumidor, daemon=True)
    _consumer_thread.start()

    # Inicia o sniffer na sua própria thread
    _sniffer_thread = Thread(target=sniff_loop, daemon=True)
    _sniffer_thread.start()

    return _sniffer_thread, _consumer_thread

def stop_system(timeout=10):
    """Para os processos de coleta."""
    global _sniffer_thread, _consumer_thread
    
    # Sinaliza para as threads pararem
    _shutdown_evt.set()
    log.log_coleta(f"{LOG_PREFIX} Sinal de parada enviado.")

    # Aguarda a thread do sniffer terminar (o sniff_loop vai parar)
    if _sniffer_thread is not None:
        _sniffer_thread.join(timeout=2.0)
        if _sniffer_thread.is_alive():
            log.log_coleta(f"{LOG_PREFIX} Sniffer não parou a tempo.", level=logging.WARNING)
        else:
            log.log_coleta(f"{LOG_PREFIX} Sniffer parado com sucesso.")

    # Aguarda a thread do consumidor terminar
    if _consumer_thread is not None:
        _consumer_thread.join(timeout)


def consumidor():
    """Consumidor que processa os IPs da fila."""
    def escanear_e_salvar_job(ip):
        try:
            portas_abertas = portas.escanear_portas(ip, portas_alvo=[502, 80, 443, 21])
            if portas_abertas:
                clp_existente = clp_manager.buscar_por_ip(ip)
                if clp_existente:
                    for porta in portas_abertas:
                        clp_functions.adicionar_porta(clp_existente, porta)
                else:
                    novo_clp = clp_functions.criar_clp(IP=ip, PORTAS=portas_abertas)
                    clp_manager.adicionar_clp(novo_clp)
                clp_manager.salvar_clps()
        except Exception:
            pass 

    with ThreadPoolExecutor(max_workers=WORKER_THREADS) as executor:
        while not _shutdown_evt.is_set():
            try:
                ip = fila.get(timeout=1)
                executor.submit(escanear_e_salvar_job, ip)
                fila.task_done()
            except Empty:
                continue