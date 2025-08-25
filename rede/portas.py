import subprocess
import re
import logging
from utils import log
from utils.CLP import CLPGen, CLP, clps

def escanear_portas(ip: str, intervalo: int = 1000, timeout: int = 30) -> None:
    """
    Escaneia portas abertas via nmap e cria/atualiza CLP automaticamente.
    - ip: endereço a ser escaneado (str)
    - intervalo: até qual porta escanear (int)
    - timeout: tempo máximo em segundos para o comando nmap
    """
    log.log(f"Escaneando {ip} de 1 a {intervalo}...")
    try:
        resultado = subprocess.check_output(
            ['nmap', '-p', f'1-{intervalo}', ip],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
            timeout=timeout
        )

        # captura portas como strings; ex: "80" "502" ...
        portas_abertas = re.findall(r'(\d+)/tcp\s+open', resultado)

        if portas_abertas:
            # normaliza: lista de ints única e ordenada
            portas = sorted({int(p) for p in portas_abertas})
            log.log_coleta(f"Portas abertas em {ip}: {', '.join(map(str, portas))}")

            if ip not in clps:
                # cria CLP com lista de portas
                CLPGen(IP=ip, UNIDADE=1, PORTAS=portas, nome=f"CLP_{ip}")
                log.log_coleta(f"CLP criado para {ip} com portas {portas}.")
            else:
                # atualiza o objeto existente (substitui lista de portas)
                obj = clps[ip]
                obj.PORTAS = portas
                obj.adicionar_log(f"Portas atualizadas para: {portas}")
                obj.salvar_json()
                log.log_coleta(f"CLP {ip} atualizado com portas {portas}.")

        else:
            log.log_coleta(f"Nenhuma porta aberta encontrada em {ip}.")

    except subprocess.CalledProcessError as e:
        log.log_and_print(f"Erro ao executar o Nmap (CalledProcessError): {e.output if hasattr(e, 'output') else e}", level=logging.ERROR)
    except subprocess.TimeoutExpired as e:
        log.log_and_print(f"Nmap expirou (timeout): {e}", level=logging.ERROR)
    except FileNotFoundError:
        log.log_and_print("Nmap não encontrado. Instale o nmap no sistema.", level=logging.ERROR)
    except Exception as e:
        log.log_and_print(f"Erro inesperado ao escanear {ip}: {e}", level=logging.ERROR)
