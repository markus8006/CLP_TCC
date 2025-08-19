from threading import Thread
from rede import coletor
from web import server
import time


if __name__ == "__main__":
    Thread(target=coletor.coletor, daemon=True).start()
    Thread(target=coletor.consumidor, daemon=True).start()
    server.iniciar_web()


    try:
        while True:
             time.sleep(0.1)
    except KeyboardInterrupt:
        print("Programa encerrado")