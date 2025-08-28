# coletor_consumidor.py
from threading import Thread, Lock, Event
from queue import Queue, Full, Empty
from scapy.all import AsyncSniffer, IP
from utils import log
from clp_app.scanner import portas
from concurrent.futures import ThreadPoolExecutor
import time
import socket

# Configurações
QUEUE_MAXSIZE = 2000
WORKER_THREADS = 10
IP_TTL_SECONDS = 300        # tempo para "esquecer" um IP e permitir novo processamento
INTERFACE = None            # ex: "eth0" ou None (scapy escolhe)
BPF_FILTER = None  # captura ARP e SYNs (reduz ruído)
IGNORE_LOCAL = None         # ignora IPs da máquina local
LOG_PREFIX = "[Coletor]"

# fila com limite
fila = Queue(maxsize=QUEUE_MAXSIZE)

# estrutura para evitar duplicatas com TTL
_ips_last_seen = {}   # { ip_str: timestamp_last_seen }
_ips_lock = Lock()

# evento de parada
_shutdown_evt = Event()

def _get_local_ips():
    """Tenta detectar IPs locais para ignorar (IPv4)."""
    local_ips = set()
    try:
        hostname = socket.gethostname()
        # pode retornar vários endereços
        addrs = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
        for a in addrs:
            local_ips.add(a[4][0])
    except Exception:
        pass
    # também pegar 127.0.0.1
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
        # já visto recentemente -> pular
        return False

def coletor():
    """Inicia o AsyncSniffer e retorna o objeto sniffer para controle externo."""
    def analisar_pacote(pkt):
        if IP not in pkt:
            return
        ip_src = pkt[IP].src

        # ignora locais
        if IGNORE_LOCAL and ip_src in _LOCAL_IPS:
            return

        if not _should_process_ip(ip_src):
            return

        try:
            fila.put_nowait(ip_src)
            log.log_coleta(f"{LOG_PREFIX} Encontrado: {ip_src}")
        except Full:
            log.log_coleta(f"{LOG_PREFIX} Fila cheia — drop {ip_src}", level=logging.WARNING)

    # AsyncSniffer roda em background; store=False evita acumulo em memória
    sniffer = AsyncSniffer(iface=INTERFACE, prn=analisar_pacote,
                           store=False, filter=BPF_FILTER)
    sniffer.start()
    log.log_coleta(f"{LOG_PREFIX} Sniffer iniciado (iface={INTERFACE}, filter={BPF_FILTER})")
    return sniffer

def consumidor():
    """Consumidor principal que delega escaneamentos a um ThreadPoolExecutor."""
    def escanear_job(ip):
        try:
            log.log_coleta(f"{LOG_PREFIX} Iniciando escaneamento: {ip}")
            portas.escanear_portas(ip)
            log.log_coleta(f"{LOG_PREFIX} Escaneamento finalizado: {ip}")
        except Exception as e:
            log.log_coleta(f"{LOG_PREFIX} Erro ao escanear {ip}: {e}", level=logging.ERROR)

    with ThreadPoolExecutor(max_workers=WORKER_THREADS) as executor:
        log.log_coleta(f"{LOG_PREFIX} Consumidor iniciado (workers={WORKER_THREADS})")
        while not _shutdown_evt.is_set():
            try:
                ip = fila.get(timeout=1)
            except Empty:
                continue
            # envia a task ao executor
            executor.submit(escanear_job, ip)
            fila.task_done()

        # quando shutdown solicitado, aguardar fila esvaziar e finalizar tarefas pendentes
        log.log_coleta(f"{LOG_PREFIX} Shutdown solicitado — aguardando fila esvaziar...")
        while True:
            try:
                ip = fila.get_nowait()
            except Empty:
                break
            executor.submit(escanear_job, ip)
            fila.task_done()
        log.log_coleta(f"{LOG_PREFIX} Consumidor finalizado.")

# API de controle
_sniffer_obj = None
_consumer_thread = None

def start_system():
    """Inicia sniffer + consumidor. Retorna (sniffer, consumer_thread)."""
    global _sniffer_obj, _consumer_thread
    _shutdown_evt.clear()
    _sniffer_obj = coletor()
    _consumer_thread = Thread(target=consumidor, daemon=True)
    _consumer_thread.start()
    return _sniffer_obj, _consumer_thread

def stop_system(timeout=10):
    """Pede shutdown e espera finalizar."""
    _shutdown_evt.set()
    # parar sniffer
    if _sniffer_obj is not None:
        try:
            _sniffer_obj.stop()
            log.log_coleta(f"{LOG_PREFIX} Sniffer parado.")
        except Exception as e:
            log.log_coleta(f"{LOG_PREFIX} Erro ao parar sniffer: {e}", level=logging.ERROR)
    # esperar consumidor encerrar
    if _consumer_thread is not None:
        _consumer_thread.join(timeout)
        if _consumer_thread.is_alive():
            log.log_coleta(f"{LOG_PREFIX} Consumidor ainda vivo após timeout.", level=logging.WARNING)
        else:
            log.log_coleta(f"{LOG_PREFIX} Consumidor finalizado com sucesso.")

# Entrypoint para testes locais
if __name__ == "__main__":
    import logging, signal
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
