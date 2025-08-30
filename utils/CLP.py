# utils/CLP.py (Refatorado para ser um gerenciador de dicionários)
import json
import os
from . import clp_functions # Importa as novas funções

# --- Configuração de Caminhos ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_JSON = os.path.join(BASE_DIR, "logs", "clps.json")

# Dicionário em memória para armazenar os CLPs (IP -> dicionário do CLP)
_clps = {}

def carregar_clps(caminho_arquivo=CAMINHO_JSON):
    """Carrega os CLPs do arquivo JSON para a memória."""
    global _clps
    if not os.path.exists(caminho_arquivo):
        _clps = {}
        return

    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados_json = json.load(f)
            # Garante que os dados carregados sejam dicionários
            _clps = {ip: clp for ip, clp in dados_json.items() if isinstance(clp, dict)}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar o arquivo de CLPs: {e}")
        _clps = {}

def salvar_clps(caminho_arquivo=CAMINHO_JSON):
    """Salva todos os CLPs da memória para o arquivo JSON."""
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    # Usamos get_info para garantir que apenas dados serializáveis sejam salvos
    dados_para_salvar = {ip: clp_functions.get_info(clp) for ip, clp in _clps.items()}
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)

def adicionar_clp(clp: dict):
    """Adiciona um novo CLP (dicionário) ao gerenciador."""
    ip = clp.get("IP")
    if not ip:
        print("Aviso: Dicionário de CLP sem IP. Não foi possível adicionar.")
        return
    if ip in _clps:
        # Atualiza as portas se o CLP já existir
        portas_existentes = set(_clps[ip].get("PORTAS", []))
        portas_novas = set(clp.get("PORTAS", []))
        portas_existentes.update(portas_novas)
        _clps[ip]["PORTAS"] = sorted(list(portas_existentes))
        print(f"Aviso: CLP com IP {ip} já existe. Portas atualizadas.")
        return
    _clps[ip] = clp

def buscar_por_ip(ip: str):
    """Busca um CLP (dicionário) pelo seu endereço IP."""
    return _clps.get(str(ip))

def listar_clps():
    """Retorna uma lista de todos os dicionários de CLP gerenciados."""
    return list(_clps.values())

# --- Carregamento Inicial ---
# Carrega os CLPs do arquivo JSON assim que o módulo é importado.
carregar_clps()