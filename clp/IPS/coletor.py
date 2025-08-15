import socket
from scapy.all import sniff, IP
from biblis import log


HOST = "127.0.0.1"
PORT = 5000

ips_coletados = set()
ips_enviados = open("ips_enviados.txt", "a")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

log.log_and_print(f"Aguardando conexão na porta {PORT}...")
conn, addr = server_socket.accept()
log.log_and_print(f"Consumidor conectado: {addr}")

def analisar_pacote(pacote):
    if IP in pacote:
        ip_src = pacote[IP].src
        if ip_src not in ips_coletados:
            ips_enviados.write(ip_src + "\n")
            ips_enviados.flush()
            ips_coletados.add(ip_src)
            try:
                conn.sendall((ip_src + "\n").encode())
                log.log_and_print(f"Enviado: {ip_src}")
            except:
                log.log_and_print("Consumidor desconectado")
                conn.close()
                exit()

log.log_and_print("Coletando IPs (sem repetição)...")
sniff(prn=analisar_pacote, store=False)