import socket
from IPS import portas
from concurrent.futures import ThreadPoolExecutor
from biblis import log



HOST = "127.0.0.1"
PORT = 5000

ips_coletados = open("ips_coletados.txt", "a")

def escanear(ip):
    log.log_and_print(f"Iniciando escaneamento para {ip}")
    portas.escanear_portas(ip)
    log.log_and_print(f"Escaneamento finalizado para {ip}")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
log.log_and_print("Conectado ao coletor!")

max_threads = 10

with ThreadPoolExecutor(max_workers=max_threads) as executor:
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            ips = data.decode().strip().split("\n")
            for ip in ips:
                if ip:
                    log.log_and_print(f"Recebido: {ip}")
                    ips_coletados.write(ip + "\n")
                    ips_coletados.flush()
                    executor.submit(escanear, ip)
    except KeyboardInterrupt:
        log.log_and_print("\nEncerrando...")
    finally:
        client_socket.close()