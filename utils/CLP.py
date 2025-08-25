# utils/CLP.py
import json
import os
from datetime import datetime
from pymodbus.client import ModbusTcpClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_JSON = os.path.join(BASE_DIR, "logs", "clps.json")

# Dicionário global com todos os objetos CLP (acessível por import)
clps = {}


class CLP:
    """Classe base para CLPs genéricos. Cria objetos que se auto-salvam em JSON."""
    _todos_clps = []

    def __init__(self, IP: str, UNIDADE=None, PORTAS=None, nome: str = "", descricao: str = "", save: bool = True):
        """
        save: se False, não escreve no JSON (útil ao carregar do arquivo para evitar regravar).
        PORTAS: int | list | None -> internamente sempre será lista de ints.
        """
        self.IP = str(IP)
        self.UNIDADE = UNIDADE
        # normaliza PORTAS para lista de ints
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

        # adiciona nas estruturas em memória (opcionalmente salva)
        if save:
            # evita duplicatas: atualiza se já existir
            if self.IP in clps:
                existing = clps[self.IP]
                existing.UNIDADE = self.UNIDADE
                existing.PORTAS = self.PORTAS
                existing.nome = self.nome
                existing.descricao = self.descricao
                existing.data_registro = self.data_registro
                existing.logs.extend(self.logs)
            else:
                clps[self.IP] = self
                CLP._todos_clps.append(self)
            self.salvar_json()
        else:
            # apenas mantém o objeto vivo; carregador fará inserir em clps/_todos_clps
            pass

    # --------------------------
    # Conexão Modbus
    # --------------------------
    def cliente_modbus(self, port: int = None):
        """Cria o cliente Modbus usando a primeira porta conhecida ou a fornecida."""
        p = port or (self.PORTAS[0] if self.PORTAS else 502)
        try:
            self.client = ModbusTcpClient(host=self.IP, port=int(p))
        except Exception as e:
            self.logs.append(f"Erro ao criar cliente Modbus: {e}")
            self.client = None

    def conectar(self, port: int = None, timeout: float = 3.0) -> bool:
        """Tenta conectar; retorna True se conectado."""
        if not self.client:
            self.cliente_modbus(port)
        if not self.client:
            self.logs.append("Cliente Modbus não inicializado.")
            self.salvar_json()
            return False

        try:
            ok = self.client.connect()
            self.conectado = bool(ok)
            self.logs.append(f"{'Conectado' if ok else 'Falha ao conectar'} usando porta {port or (self.PORTAS[0] if self.PORTAS else 502)}")
        except Exception as e:
            self.conectado = False
            self.logs.append(f"Exceção ao conectar: {e}")
        self.salvar_json()
        return self.conectado

    def desconectar(self):
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                self.logs.append(f"Erro ao fechar conexão: {e}")
        self.conectado = False
        self.salvar_json()

    # --------------------------
    # Manipulação de portas e logs
    # --------------------------
    def adicionar_porta(self, porta: int):
        porta = int(porta)
        if porta not in self.PORTAS:
            self.PORTAS.append(porta)
            self.logs.append(f"Porta {porta} adicionada.")
            self.salvar_json()

    def remover_porta(self, porta: int):
        porta = int(porta)
        if porta in self.PORTAS:
            self.PORTAS.remove(porta)
            self.logs.append(f"Porta {porta} removida.")
            self.salvar_json()

    def adicionar_log(self, texto: str):
        self.logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {texto}")
        self.salvar_json()

    # --------------------------
    # Serialização / JSON
    # --------------------------
    def get_info(self) -> dict:
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

    @classmethod
    def salvar_todos_json(cls):
        """Salva todos os CLPs atualmente no dicionário 'clps' para o arquivo JSON."""
        os.makedirs(os.path.dirname(CAMINHO_JSON), exist_ok=True)
        dados = {ip: obj.get_info() for ip, obj in clps.items()}
        with open(CAMINHO_JSON, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def salvar_json(self):
        """Salva (wrapper de classe) — chamado ao alterar estado do objeto."""
        CLP.salvar_todos_json()

    # --------------------------
    # Carregamento do JSON
    # --------------------------
    @classmethod
    def carregar_todos(cls):
        """Carrega do arquivo JSON e popula o dicionário clps e _todos_clps.
           Se já existir um CLP com o mesmo IP em memória, ele será atualizado.
        """
        if not os.path.exists(CAMINHO_JSON):
            return

        with open(CAMINHO_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        for ip, info in data.items():
            # evita recriar duplicatas
            if ip in clps:
                # atualiza o objeto existente
                obj = clps[ip]
                obj.PORTAS = info.get("portas", obj.PORTAS)
                obj.UNIDADE = info.get("unidade", obj.UNIDADE)
                obj.nome = info.get("nome", obj.nome)
                obj.descricao = info.get("descricao", obj.descricao)
                obj.logs = info.get("logs", obj.logs)
                obj.data_registro = info.get("data_registro", obj.data_registro)
            else:
                # cria sem salvar (save=False) para evitar regravar durante o carregamento
                obj = CLP(IP=ip,
                          UNIDADE=info.get("unidade"),
                          PORTAS=info.get("portas", []),
                          nome=info.get("nome", ""),
                          descricao=info.get("descricao", ""),
                          save=False)
                obj.logs = info.get("logs", [])
                obj.data_registro = info.get("data_registro", obj.data_registro)
                clps[ip] = obj
                cls._todos_clps.append(obj)

    # --------------------------
    # Helpers
    # --------------------------
    @classmethod
    def listar_clps(cls):
        return list(clps.values())

    @classmethod
    def buscar_por_ip(cls, ip: str):
        return clps.get(str(ip))


# --------------------------
# Subclasses de exemplo
# --------------------------
class CLPGen(CLP):
    def __init__(self, IP: str, UNIDADE=None, PORTAS=None, nome: str = "", descricao: str = "", save: bool = True):
        super().__init__(IP, UNIDADE, PORTAS, nome, descricao, save=save)

    def baixar_codigo(self, admin: str, senha: str, caminho_local: str = "programa.hex") -> bool:
        import ftplib
        try:
            ftp = ftplib.FTP(self.IP, timeout=5)
            ftp.login(admin, senha)
            with open(caminho_local, 'rb') as f:
                ftp.storbinary(f'STOR /programa_{self.IP}.hex', f)
            ftp.quit()
            self.logs.append("Código enviado com sucesso via FTP.")
            self.salvar_json()
            return True
        except Exception as e:
            self.logs.append(f"Erro ao enviar código via FTP: {e}")
            self.salvar_json()
            return False


class CLPSiemens(CLP):
    def __init__(self, IP: str, UNIDADE=None, PORTAS=None, nome: str = "", descricao: str = "", save: bool = True):
        super().__init__(IP, UNIDADE, PORTAS, nome, descricao, save=save)

    def baixar_codigo(self):
        # placeholder para futura integração com TIA Openness
        self.logs.append("baixar_codigo (Siemens) não implementado.")
        self.salvar_json()
