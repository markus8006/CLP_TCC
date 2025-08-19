import os
import logging 

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
caminho = os.path.join(BASE_DIR, "logs/app.log")

logging.basicConfig(
    filename=caminho,
    level=logging.DEBUG,
    format= "%(asctime)s - %(levelname)s - %(message)s", 
)





def log(mensagem : str, level=logging.INFO) -> None:
    """Função que salva informações do program em um arquivo de log
       mensagem (str) : mensagem que será escrita
       level : Nivel de intensidade da mensgem, usando a biblioteca logging 
    """


    if level == logging.DEBUG:
        logging.debug(mensagem)
    elif level == logging.INFO:
        logging.info(mensagem)
    elif level == logging.WARNING:
        logging.warning(mensagem)
    elif level == logging.ERROR:
        logging.error(mensagem)
    elif level == logging.CRITICAL:
        logging.critical(mensagem)



def log_and_print(mesagem, level=logging.INFO):
    """Função que salva informações do program em um arquivo de log e escreva elas no terminal
       mensagem (str) : mensagem que será escrita
       level : Nivel de intensidade da mensgem, usando a biblioteca logging 
    """
    print(mesagem)
    log(mesagem, level=level)


if __name__ == "__main__":
    log_and_print("Esta é uma mensagem de debug.", logging.DEBUG)
    log_and_print("Esta é uma mensagem de informação.", logging.INFO)
    log_and_print("Esta é uma mensagem de aviso.", logging.WARNING)
    log_and_print("Esta é uma mensagem de erro.", logging.ERROR)
    log_and_print("Esta é uma mensagem crítica.", logging.CRITICAL)



def carregar_logs(caminho=caminho):
    """Lê o arquivo .log e retorna uma lista de dicionários."""
    logs = []
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    # Supondo formato "hora - mensagem"
                    partes = linha.split(" - ", 1)
                    if len(partes) == 2:
                        logs.append({"hora": partes[0], "mensagem": partes[1]})
                    else:
                        logs.append({"hora": "", "mensagem": linha})
        return logs
    except FileNotFoundError:
        return []