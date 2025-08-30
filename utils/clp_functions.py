# utils/clp_functions.py
from datetime import datetime
from pymodbus.client import ModbusTcpClient

# Este dicionário em memória manterá as conexões de cliente ativas, usando o IP como chave.
_active_clients = {}

def criar_clp(IP: str, UNIDADE=None, PORTAS=None, nome: str = "", descricao: str = ""):
    """Cria um novo dicionário para representar um CLP."""
    if PORTAS is None:
        portas_list = []
    elif isinstance(PORTAS, (list, tuple)):
        portas_list = [int(p) for p in PORTAS]
    else:
        portas_list = [int(PORTAS)]

    return {
        "IP": str(IP),
        "UNIDADE": UNIDADE,
        "PORTAS": portas_list,
        "conectado": False,
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": nome or f"CLP_{IP}",
        "descricao": descricao,
        "logs": [],
    }

def conectar(clp: dict, port: int = None, timeout: float = 3.0) -> bool:
    """Tenta conectar ao CLP via Modbus e atualiza o dicionário."""
    ip = clp["IP"]
    p = port or (clp["PORTAS"][0] if clp["PORTAS"] else 502)
    try:
        client = ModbusTcpClient(host=ip, port=int(p), timeout=timeout)
        ok = client.connect()
        clp["conectado"] = bool(ok)
        if ok:
            _active_clients[ip] = client
        status = 'Conectado' if ok else 'Falha ao conectar'
        adicionar_log(clp, f"{status} usando a porta {p}.")
        return clp["conectado"]
    except Exception as e:
        clp["conectado"] = False
        adicionar_log(clp, f"Exceção ao conectar na porta {p}: {e}")
        return False

def desconectar(clp: dict):
    """Desconecta do CLP."""
    ip = clp["IP"]
    client = _active_clients.get(ip)
    if client and client.is_socket_open():
        client.close()
        if ip in _active_clients:
            del _active_clients[ip]
    clp["conectado"] = False
    adicionar_log(clp, "Conexão encerrada.")

def get_client(ip: str):
    """Obtém o objeto de cliente Modbus ativo para um determinado IP."""
    return _active_clients.get(ip)

def adicionar_porta(clp: dict, porta: int):
    """Adiciona uma nova porta à lista do CLP."""
    porta = int(porta)
    if porta not in clp["PORTAS"]:
        clp["PORTAS"].append(porta)
        adicionar_log(clp, f"Porta {porta} adicionada à lista de portas conhecidas.")

def adicionar_log(clp: dict, texto: str):
    """Adiciona uma entrada de log ao CLP."""
    if "logs" not in clp:
        clp["logs"] = []
    clp["logs"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {texto}")

def get_info(clp: dict) -> dict:
    """Retorna um dicionário serializável com as informações do CLP."""
    # Garante que o status está atualizado
    clp["status"] = "Online" if clp.get("conectado") else "Offline"
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Padroniza as chaves para corresponderem às da função 'criar_clp'
    return {
        "IP": clp.get("IP"),  # Chave corrigida de "ip" para "IP"
        "UNIDADE": clp.get("UNIDADE"),
        "PORTAS": clp.get("PORTAS", []), # Chave corrigida de "portas" para "PORTAS"
        "conectado": clp.get("conectado", False),
        "data_registro": clp.get("data_registro"),
        "nome": clp.get("nome"),
        "descricao": clp.get("descricao"),
        "logs": clp.get("logs", []),
        "status": clp.get("status"), # Adicionamos o status aqui também
    }