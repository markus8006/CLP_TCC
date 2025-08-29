# portas.py
import subprocess
import re
import logging
import shutil
import time

from utils import log
from utils.CLP import CLPGen, CLP, clps

# Scapy import será usado apenas como fallback se nmap não estiver disponível
try:
    from scapy.all import sr1, IP, TCP, conf
    SCAPY_AVAILABLE = True
except Exception:
    SCAPY_AVAILABLE = False

def _parse_nmap_output(output: str):
    """Extrai portas abertas do output do nmap (lista de ints)."""
    portas_abertas = re.findall(r'(\d+)/tcp\s+open', output)
    return sorted({int(p) for p in portas_abertas})

def _scapy_syn_check(ip: str, ports, timeout=1):
    """Fallback com Scapy: envia SYN e espera SYN-ACK. Retorna lista de portas abertas."""
    if not SCAPY_AVAILABLE:
        log.log_coleta("Scapy não disponível para fallback.", level=logging.ERROR)
        return []

    conf.verb = 0
    abertas = []
    for p in ports:
        try:
            pkt = IP(dst=ip)/TCP(dport=int(p), flags="S")
            resp = sr1(pkt, timeout=timeout, verbose=False)
            if resp is None:
                # sem resposta
                continue
            if resp.haslayer(TCP):
                flags = resp[TCP].flags
                # SYN-ACK -> porta aberta
                if flags & 0x12:
                    abertas.append(int(p))
                # RST -> fechada, ignorar
        except Exception as e:
            log.log_coleta(f"Erro scapy-syn check {ip}:{p} -> {e}", level=logging.WARNING)
    return sorted(set(abertas))


def escanear_portas(ip: str, intervalo: int = 1000, timeout: int = 60, portas_alvo: list = None) -> None:
    """
    Escaneia portas abertas via nmap (ou fallback Scapy).
    - ip: endereço a ser escaneado (str)
    - intervalo: até qual porta escanear (int). Ignorado se portas_alvo fornecido.
    - timeout: tempo máximo em segundos para o comando nmap
    - portas_alvo: lista de portas específicas para verificar (ex: [502]) — se fornecido, varre apenas essas portas.
    """
    log.log_coleta(f"Escaneando {ip}...")

    # Normaliza lista de portas a verificar
    if portas_alvo:
        ports_to_check = sorted({int(p) for p in portas_alvo})
        port_spec = ",".join(map(str, ports_to_check))
    else:
        # intervalo inteiro: 1-<intervalo>
        ports_to_check = None
        port_spec = f"1-{int(intervalo)}"

    portas = []
    nmap_path = shutil.which("nmap")
    if nmap_path:
        # Monta o comando nmap: connect scan (-sT) não precisa de root, -n (sem DNS), -T4 (mais rápido)
        cmd = [nmap_path, '-sT', '-n', '-T4', '-p', port_spec, ip]
        try:
            log.log_coleta(f"Executando nmap: {' '.join(cmd)}")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if proc.returncode == 0:
                portas = _parse_nmap_output(proc.stdout)
            else:
                # nmap retornou erro (p.ex. host inacessível); ainda tentaremos fallback
                log.log_coleta(f"Nmap retornou código {proc.returncode}. stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}", level=logging.WARNING)
                portas = []
        except subprocess.TimeoutExpired as e:
            log.log_coleta(f"Nmap expirou (timeout) ao escanear {ip}: {e}", level=logging.ERROR)
            portas = []
        except Exception as e:
            log.log_coleta(f"Erro ao executar nmap para {ip}: {e}", level=logging.ERROR)
            portas = []
    else:
        log.log_coleta("Nmap não encontrado; tentando fallback com Scapy (se disponível).")
        portas = []

    # Se nmap não abriu nenhuma porta (ou nmap não disponível) e temos lista específica, tenta Scapy fallback
    if (not portas) and (ports_to_check is not None):
        portas = _scapy_syn_check(ip, ports_to_check, timeout=1)

    # Se não encontramos nada e não passamos portas_alvo, podemos tentar um SYN rápido apenas na porta Modbus (502) como auxílio
    if (not portas) and (ports_to_check is None):
        # tentativa rápida na porta 502 para detectar Modbus
        if SCAPY_AVAILABLE:
            portas = _scapy_syn_check(ip, [502], timeout=1)

    # Normaliza resultado
    portas = sorted(set(int(p) for p in portas))

    if portas:
        log.log_coleta(f"Portas abertas em {ip}: {', '.join(map(str, portas))}")
        if ip not in clps:
            # cria CLP com a lista de portas
            CLPGen(IP=ip, UNIDADE=1, PORTAS=portas, nome=f"CLP_{ip}")
            log.log_coleta(f"CLP criado para {ip} com portas {portas}.")
        else:
            # atualiza o objeto existente adicionando portas (preserva histórico)
            obj = clps[ip]
            for p in portas:
                if p not in obj.PORTAS:
                    obj.adicionar_porta(p)
            obj.adicionar_log(f"Portas atualizadas (scan): {portas}")
            obj.salvar_json()
            log.log_coleta(f"CLP {ip} atualizado com portas {obj.PORTAS}.")
    else:
        log.log_coleta(f"Nenhuma porta aberta encontrada em {ip}.")
