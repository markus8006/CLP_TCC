from threading import Thread
from rede import coletor
from web import server
import time
from configs import settings

def monitor_threads(threads):
    """Monitora e reinicia threads de coletor/consumidor quando necessário."""
    while True:
        #print("[STATUS] coleta:", settings.status_coleta)
        if settings.status_coleta == "ativado":
            # reinicia coletor se morreu
            if not threads["coletor"].is_alive():
                #print("[INFO] Reiniciando coletor...")
                threads["coletor"] = Thread(target=coletor.coletor, daemon=True)
                threads["coletor"].start()

            if not threads["consumidor"].is_alive():
                #print("[INFO] Reiniciando consumidor...")
                threads["consumidor"] = Thread(target=coletor.consumidor, daemon=True)
                threads["consumidor"].start()

        time.sleep(0.5)


if __name__ == "__main__":
    # inicia coletor e consumidor antes de subir o servidor (server precisa rodar na main thread)
    threads = {
        "coletor": Thread(target=coletor.coletor, daemon=True),
        "consumidor": Thread(target=coletor.consumidor, daemon=True)
    }
    threads["coletor"].start()
    threads["consumidor"].start()

    # thread de monitor para reiniciar caso alguma morra
    Thread(target=monitor_threads, args=(threads,), daemon=True).start()

    # server.iniciar_web() roda bloqueante no main thread (ex.: Flask.run())
    try:
        server.iniciar_web()
    except KeyboardInterrupt:
        print("Programa encerrado")
