import subprocess
import re
import json
from utils import log

import logging

dados = {}

def escanear_portas(ip : str, intervalo : int = 1000) -> None:
    """Roda um nmap -p '1-{intervalo}' para escanear portas abertas no ip
    ip (str) : ip que sera escaneado no formato x.x.x.x
    intervalo (int) : a quantidade de portas que vai escanear"""
    if ip not in dados:
        dados[ip] = {}
    log.log_and_print(f"Escaneando {ip} de 1 a {intervalo}...")
    try:
        resultado = subprocess.check_output(
            ['nmap', '-p', f'1-{intervalo}', ip],
            universal_newlines=True
        )

        # Procura por linhas com "open"
        portas_abertas = re.findall(r'(\d+)/tcp\s+open', resultado)

        if portas_abertas:
            log.log_and_print(f"Portas abertas encontradas em {ip}: {', '.join(portas_abertas)}")
            

           
            dados[ip] = [int(p) for p in portas_abertas]
            with open("dados.json", "w") as f:
                log.log_and_print(f"{ip}: Salvo no json")
                json.dump(dados, f, indent=4)  # indent=4 deixa o JSON legível (formatado)
        else:
            log.log_and_print(f"Nenhuma porta aberta encontrada em {ip}.")
    except subprocess.CalledProcessError as e:
        log.log_and_print("Erro ao executar o Nmap: " + str(e), level=logging.ERROR)


if __name__ == "__main__":
    escanear_portas("192.168.0.1")