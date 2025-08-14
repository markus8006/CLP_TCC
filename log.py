import logging 

logging.basicConfig(
    filename="app.log",
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