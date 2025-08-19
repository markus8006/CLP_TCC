from threading import Thread
from queue import Queue
from scapy.all import sniff, IP
from utils import log
from rede import portas
from concurrent.futures import ThreadPoolExecutor
import time

fila = Queue()

def coletor():
    """Inicia o coletor"""
    ips_ja_enviados = set()
    def analisar_pacote(pacote):
        if IP in pacote:
            ip_src = pacote[IP].src
            if ip_src not in ips_ja_enviados:
                fila.put(ip_src)
                ips_ja_enviados.add(ip_src)
                log.log(f"Encontrado: {ip_src}")
    sniff(prn=analisar_pacote, store=False)

def consumidor():
    """Inicia o consumidor"""
    def escanear(ip):
        log.log(f"Iniciando escaneamento: {ip}")
        portas.escanear_portas(ip)
        log.log(f"Escaneamento finalizado: {ip}")

    max_threads = 10
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        while True:
            ip = fila.get()
            executor.submit(escanear, ip)


if __name__ == "__main__":
    Thread(target=coletor, daemon=True).start()
    Thread(target=consumidor, daemon=True).start()


