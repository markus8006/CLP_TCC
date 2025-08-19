from threading import Thread
from rede import coletor
from web import server


if __name__ == "__main__":
    coletor.iniciar_rede()
    server.iniciar_web()