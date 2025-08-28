# clp_app/scanner/service.py
from threading import Thread, Event
from clp_app.scanner.rede import coletor
import time

class ScannerService:
    def __init__(self):
        self._sniffer_thread = None
        self._consumer_thread = None
        self._is_running = False
        self._shutdown_event = Event()

    def start(self):
        if self._is_running:
            return False  # Já está rodando

        self._shutdown_event.clear()
        # Usamos os componentes originais do seu módulo coletor
        self._sniffer_thread = Thread(target=coletor.coletor, daemon=True)
        self._consumer_thread = Thread(target=coletor.consumidor, daemon=True)

        self._sniffer_thread.start()
        self._consumer_thread.start()
        self._is_running = True
        return True

    def stop(self):
        if not self._is_running:
            return False # Já está parado

        # O seu módulo coletor já tem uma lógica de parada! Vamos usá-la.
        coletor.stop_system()
        self._is_running = False
        return True

    def get_status(self):
        if self._is_running and self._sniffer_thread.is_alive():
            return "ativado"
        self._is_running = False
        return "desativado"

# Criamos uma instância única (Singleton) para ser usada em toda a aplicação
scanner_service = ScannerService()