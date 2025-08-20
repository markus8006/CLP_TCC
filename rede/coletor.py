from threading import Thread, Lock
from queue import Queue, Full, Empty
from scapy.all import sniff, IP
from utils import log
from rede import portas
from concurrent.futures import ThreadPoolExecutor
import time
import logging

# fila com limite opcional
fila = Queue(maxsize=2000)

# set com proteção para evitar duplicatas (thread-safe)
_ips_ja_enviados = set()
_ips_lock = Lock()

def coletor():
    """Inicia o coletor (sniff)"""
    def analisar_pacote(pacote):
        if IP in pacote:
            ip_src = pacote[IP].src
            with _ips_lock:
                if ip_src in _ips_ja_enviados:
                    return
                _ips_ja_enviados.add(ip_src)
            try:
                fila.put(ip_src, timeout=1)
                log.log_coleta(f"Encontrado: {ip_src}")
            except Full:
                log.log_coleta(f"Fila cheia. Ignorando {ip_src}", level=logging.WARNING)

    sniff(prn=analisar_pacote, store=False)  # chama analisar_pacote para cada pacote

def consumidor():
    """Inicia o consumidor que escaneia IPs"""
    def escanear(ip):
        try:
            log.log_coleta(f"Iniciando escaneamento: {ip}")
            portas.escanear_portas(ip)
            log.log_coleta(f"Escaneamento finalizado: {ip}")
        except Exception as e:
            log.log_coleta(f"Erro ao escanear {ip}: {e}", level=logging.ERROR)

    max_threads = 10
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        while True:
            try:
                ip = fila.get(timeout=2)  # timeout para permitir checks/encerramento futuro
            except Empty:
                continue
            executor.submit(escanear, ip)
            fila.task_done()


if __name__ == "__main__":
    Thread(target=coletor, daemon=True).start()
    Thread(target=consumidor, daemon=True).start()
    # manter o main vivo em testes locais
    while True:
        time.sleep(1)
