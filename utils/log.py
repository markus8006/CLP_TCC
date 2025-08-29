import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logs_dir = os.path.join(BASE_DIR, "logs")
caminho_app = os.path.join(logs_dir, "app.log")
caminho_coleta = os.path.join(logs_dir, "coleta.log")

# garante que a pasta de logs exista (IMPORTANTE)
os.makedirs(logs_dir, exist_ok=True)

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

# --- ALTERAÇÃO PRINCIPAL AQUI ---
# Impede que os logs da coleta "subam" para o logger principal (app.log)
logger_coleta.propagate = False


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
    """Carrega logs de um arquivo específico (padrão: app.log).
       Se o arquivo não existir, cria-o vazio e retorna lista vazia.
    """
    logs = []

    # garante diretório do caminho também (caso chamem com caminho diferente)
    dir_do_arquivo = os.path.dirname(caminho)
    if dir_do_arquivo:
        os.makedirs(dir_do_arquivo, exist_ok=True)

    # se não existe, cria um arquivo vazio e retorna lista vazia
    if not os.path.exists(caminho):
        # cria o arquivo (modo append -> cria se não existir)
        try:
            open(caminho, "a", encoding="utf-8").close()
        except Exception as e:
            # se não conseguiu criar, registra no logger e devolve mensagem de erro
            logging.error(f"Não foi possível criar o arquivo de log {caminho}: {e}")
            return [{"hora": "", "nivel": "ERRO", "mensagem": f"Não foi possível criar o arquivo de log: {e}"}]
        return []  # arquivo criado, mas sem conteúdo ainda

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        # caso o arquivo tenha outra codificação, tenta cp1252 com replace
        with open(caminho, "r", encoding="cp1252", errors="replace") as f:
            linhas = f.readlines()
    except Exception as e:
        logging.error(f"Erro ao abrir o arquivo de log {caminho}: {e}")
        return [{"hora": "", "nivel": "ERRO", "mensagem": f"Erro ao abrir arquivo de log: {e}"}]

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



if __name__ == "__main__":
    print(carregar_logs())