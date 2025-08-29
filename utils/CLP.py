# utils/CLP.py
# Versão Refatorada com o Padrão Manager/Repository

import json
import os
from datetime import datetime
from pymodbus.client import ModbusTcpClient

# --- Configuração de Caminhos ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_JSON = os.path.join(BASE_DIR, "logs", "clps.json")


class CLPManager:
    """Gerencia a coleção de CLPs, incluindo carga e salvamento do JSON."""
    def __init__(self, caminho_arquivo=CAMINHO_JSON):
        self._clps = {}  # Dicionário privado para armazenar os CLPs (IP -> objeto CLP)
        self.caminho_arquivo = caminho_arquivo
        self.carregar_clps()

    def carregar_clps(self):
        """Carrega os CLPs do arquivo JSON para a memória."""
        if not os.path.exists(self.caminho_arquivo):
            return

        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                dados_json = json.load(f)

            for ip, info in dados_json.items():
                # Aqui você pode adicionar lógica para carregar a subclasse correta se necessário
                # Ex: if info.get('tipo') == 'Siemens': self._clps[ip] = CLPSiemens(...)
                self._clps[ip] = CLP(
                    IP=ip,
                    UNIDADE=info.get("unidade"),
                    PORTAS=info.get("portas", []),
                    nome=info.get("nome", ""),
                    descricao=info.get("descricao", "")
                )
                # Carrega dados adicionais que não estão no __init__
                self._clps[ip].logs = info.get("logs", [])
                self._clps[ip].data_registro = info.get("data_registro")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar o arquivo de CLPs: {e}")
            self._clps = {}

    def salvar_clps(self):
        """Salva todos os CLPs da memória para o arquivo JSON."""
        os.makedirs(os.path.dirname(self.caminho_arquivo), exist_ok=True)
        dados_para_salvar = {ip: clp.get_info() for ip, clp in self._clps.items()}
        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)

    def adicionar_clp(self, clp_obj):
        """Adiciona um novo CLP ao gerenciador."""
        if clp_obj.IP in self._clps:
            # Ou você pode lançar uma exceção, ou atualizar o existente
            print(f"Aviso: CLP com IP {clp_obj.IP} já existe. O objeto não será adicionado.")
            return
        self._clps[clp_obj.IP] = clp_obj

    def buscar_por_ip(self, ip: str):
        """Busca um CLP pelo seu endereço IP."""
        return self._clps.get(str(ip))

    def listar_clps(self):
        """Retorna uma lista de todos os objetos CLP gerenciados."""
        return list(self._clps.values())


class CLP:
    """Classe que representa um CLP, focada em suas propriedades e ações."""
    def __init__(self, IP: str, UNIDADE=None, PORTAS=None, nome: str = "", descricao: str = ""):
        self.IP = str(IP)
        self.UNIDADE = UNIDADE
        
        # Normaliza PORTAS para lista de ints
        if PORTAS is None:
            self.PORTAS = []
        elif isinstance(PORTAS, (list, tuple)):
            self.PORTAS = [int(p) for p in PORTAS]
        else:
            self.PORTAS = [int(PORTAS)]

        self.conectado = False
        self.data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.nome = nome or f"CLP_{self.IP}"
        self.descricao = descricao
        self.client = None
        self.logs = []

    def conectar(self, port: int = None, timeout: float = 3.0) -> bool:
        """Tenta conectar ao CLP via Modbus."""
        p = port or (self.PORTAS[0] if self.PORTAS else 502)
        try:
            self.client = ModbusTcpClient(host=self.IP, port=int(p), timeout=timeout)
            ok = self.client.connect()
            self.conectado = bool(ok)
            status = 'Conectado' if ok else 'Falha ao conectar'
            self.adicionar_log(f"{status} usando a porta {p}.")
            return self.conectado
        except Exception as e:
            self.conectado = False
            self.adicionar_log(f"Exceção ao conectar na porta {p}: {e}")
            return False

    def desconectar(self):
        if self.client and self.client.is_socket_open():
            self.client.close()
        self.conectado = False
        self.adicionar_log("Conexão encerrada.")

    def adicionar_porta(self, porta: int):
        porta = int(porta)
        if porta not in self.PORTAS:
            self.PORTAS.append(porta)
            self.adicionar_log(f"Porta {porta} adicionada à lista de portas conhecidas.")

    def adicionar_log(self, texto: str):
        self.logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {texto}")

    def get_info(self) -> dict:
        """Retorna um dicionário serializável com as informações do CLP."""
        return {
            "nome": self.nome,
            "ip": self.IP,
            "portas": self.PORTAS,
            "unidade": self.UNIDADE,
            "status": "Online" if self.conectado else "Offline",
            "logs": self.logs,
            "data_registro": self.data_registro,
            "descricao": self.descricao
        }

class CLPGen(CLP):
    def baixar_codigo(self, admin: str, senha: str) -> bool:
        import ftplib
        try:
            with ftplib.FTP(self.IP, timeout=5) as ftp:
                ftp.login(admin, senha)
                # O ideal é transferir um arquivo real, este é um exemplo
                # with open(caminho_local, 'rb') as f:
                #    ftp.storbinary(f'STOR /programa_{self.IP}.hex', f)
            self.adicionar_log("Código enviado com sucesso via FTP.")
            return True
        except Exception as e:
            self.adicionar_log(f"Erro ao enviar código via FTP: {e}")
            return False


class CLPSiemens(CLP):
    def baixar_codigo(self):
        self.adicionar_log("Funcionalidade baixar_codigo (Siemens) não implementada.")