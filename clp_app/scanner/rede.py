# clp_app/scanner/rede.py
from threading import Thread, Lock, Event
from queue import Queue, Full, Empty
from scapy.all import AsyncSniffer, IP
from concurrent.futures import ThreadPoolExecutor
import time
import socket
import logging

# --- Imports Corrigidos ---
from utils import log
from clp_app.scanner import portas
# Adiciona os imports para o gerenciador de CLPs
from utils import CLP as clp_manager
from utils import clp_functions

# Configurações
QUEUE_MAXSIZE = 2000
WORKER_THREADS = 10
IP_TTL_SECONDS = 300
INTERFACE = None
BPF_FILTER = "arp or (tcp and (tcp[tcpflags] & (tcp-syn) != 0))" # Filtro mais específico
IGNORE_LOCAL = True
LOG_PREFIX = "[Coletor]"

# (O resto das configurações globais permanece o mesmo)
fila = Queue(maxsize=QUEUE_MAXSIZE)
_ips_last_seen = {}
_ips_lock = Lock()
_shutdown_evt = Event()

def _get_local_ips():
    """Tenta detectar IPs locais para ignorar (IPv4)."""
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
    """Verifica se o IP deve ser enfileirado (dedupe + TTL)."""
    now = time.time()
    with _ips_lock:
        last = _ips_last_seen.get(ip)
        if last is None or (now - last) >= IP_TTL_SECONDS:
            _ips_last_seen[ip] = now
            return True
        return False

def coletor():
    """Inicia o AsyncSniffer e retorna o objeto sniffer para controle externo."""
    def analisar_pacote(pkt):
        if IP not in pkt:
            return
        ip_src = pkt[IP].src

        if IGNORE_LOCAL and ip_src in _LOCAL_IPS:
            return

        if not _should_process_ip(ip_src):
            return

        try:
            fila.put_nowait(ip_src)
            log.log_coleta(f"{LOG_PREFIX} Encontrado: {ip_src}")
        except Full:
            log.log_coleta(f"{LOG_PREFIX} Fila cheia — drop {ip_src}", level=logging.WARNING)

    sniffer = AsyncSniffer(iface=INTERFACE, prn=analisar_pacote,
                           store=False, filter=BPF_FILTER)
    sniffer.start()
    log.log_coleta(f"{LOG_PREFIX} Sniffer iniciado (iface={INTERFACE}, filter={BPF_FILTER})")
    return sniffer

def consumidor():
    """
    Consumidor principal que delega escaneamentos e **SALVA** os CLPs encontrados.
    """
    def escanear_e_salvar_job(ip):
        try:
            log.log_coleta(f"{LOG_PREFIX} Iniciando escaneamento: {ip}")
            # Escaneia portas de interesse para CLPs
            portas_abertas = portas.escanear_portas(ip, portas_alvo=[502, 80, 443, 21])

            # --- LÓGICA DE PERSISTÊNCIA ADICIONADA AQUI ---
            if portas_abertas:
                log.log_coleta(f"{LOG_PREFIX} Portas abertas em {ip}: {portas_abertas}. Adicionando/Atualizando CLP.")

                clp_existente = clp_manager.buscar_por_ip(ip)

                if clp_existente:
                    # Se já existe, apenas adiciona as portas que podem ser novas
                    for porta in portas_abertas:
                        clp_functions.adicionar_porta(clp_existente, porta)
                else:
                    # Se é um CLP novo, cria o dicionário
                    novo_clp = clp_functions.criar_clp(IP=ip, PORTAS=portas_abertas)
                    clp_manager.adicionar_clp(novo_clp)

                # SALVA O ESTADO ATUALIZADO NO ARQUIVO JSON
                clp_manager.salvar_clps()
                log.log_coleta(f"{LOG_PREFIX} Escaneamento e salvamento finalizados para: {ip}")
            else:
                log.log_coleta(f"{LOG_PREFIX} Nenhuma porta de interesse encontrada para {ip}.")

        except Exception as e:
            log.log_coleta(f"{LOG_PREFIX} Erro no job de escaneamento para {ip}: {e}", level=logging.ERROR)

    with ThreadPoolExecutor(max_workers=WORKER_THREADS) as executor:
        log.log_coleta(f"{LOG_PREFIX} Consumidor iniciado (workers={WORKER_THREADS})")
        while not _shutdown_evt.is_set():
            try:
                ip = fila.get(timeout=1)
                executor.submit(escanear_e_salvar_job, ip)
                fila.task_done()
            except Empty:
                continue

        log.log_coleta(f"{LOG_PREFIX} Shutdown solicitado — aguardando fila esvaziar...")
        while not fila.empty():
            try:
                ip = fila.get_nowait()
                executor.submit(escanear_e_salvar_job, ip)
                fila.task_done()
            except Empty:
                break
        log.log_coleta(f"{LOG_PREFIX} Consumidor finalizado.")


# (API de controle e Entrypoint para testes permanecem os mesmos)
_sniffer_obj = None
_consumer_thread = None

def start_system():
    global _sniffer_obj, _consumer_thread
    _shutdown_evt.clear()
    _sniffer_obj = coletor()
    _consumer_thread = Thread(target=consumidor, daemon=True)
    _consumer_thread.start()
    return _sniffer_obj, _consumer_thread

def stop_system(timeout=10):
    _shutdown_evt.set()
    if _sniffer_obj is not None:
        try:
            _sniffer_obj.stop()
            log.log_coleta(f"{LOG_PREFIX} Sniffer parado.")
        except Exception as e:
            log.log_coleta(f"{LOG_PREFIX} Erro ao parar sniffer: {e}", level=logging.ERROR)
    if _consumer_thread is not None:
        _consumer_thread.join(timeout)
        if _consumer_thread.is_alive():
            log.log_coleta(f"{LOG_PREFIX} Consumidor ainda vivo após timeout.", level=logging.WARNING)
        else:
            log.log_coleta(f"{LOG_PREFIX} Consumidor finalizado com sucesso.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        start_system()
        print("Coletor/Consumidor rodando. Ctrl+C para parar.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Parando...")
        stop_system()
        print("Finalizado.")