import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
caminho_app = os.path.join(BASE_DIR, "logs/app.log")
caminho_coleta = os.path.join(BASE_DIR, "logs/coleta.log")

# Logger principal
logging.basicConfig(
    filename=caminho_app,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# Logger exclusivo da coleta
logger_coleta = logging.getLogger("coleta")
logger_coleta.setLevel(logging.DEBUG)

# Adiciona um handler separado para o arquivo coleta.log
handler_coleta = logging.FileHandler(caminho_coleta, encoding="utf-8")
handler_coleta.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger_coleta.addHandler(handler_coleta)


def log(mensagem: str, level=logging.INFO) -> None:
    """Log geral do sistema."""
    logging.log(level, mensagem)


def log_and_print(mensagem: str, level=logging.INFO) -> None:
    """Log geral + print no terminal."""
    print(mensagem)
    logging.log(level, mensagem)


def log_coleta(mensagem: str, level=logging.INFO) -> None:
    """Log exclusivo da coleta de IPs."""
    logger_coleta.log(level, mensagem)


def carregar_logs(caminho=caminho_app):
    """Carrega logs de um arquivo específico (padrão: app.log)."""
    logs = []
    if not os.path.exists(caminho):
        logs.append({"hora": "", "nivel": "ERRO", "mensagem": "Arquivo de log não encontrado"})
        return logs

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        with open(caminho, "r", encoding="cp1252", errors="replace") as f:
            linhas = f.readlines()

    for linha in linhas:
        linha = linha.strip()
        if linha:
            partes = linha.split(" - ", 2)
            if len(partes) == 3:
                logs.append({
                    "hora": partes[0],
                    "nivel": partes[1],
                    "mensagem": partes[2]
                })
            else:
                logs.append({"hora": "", "nivel": "", "mensagem": linha})
    return logs
