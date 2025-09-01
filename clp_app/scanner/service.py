# clp_app/scanner/service.py
from clp_app.scanner import rede

class ScannerService:
    def __init__(self):
        self._sniffer_obj = None
        self._consumer_thread = None
        self._is_running = False

    def start(self):
        """Inicia o sistema de coleta e lida com possíveis falhas."""
        if self._is_running:
            return False

        # CORREÇÃO: Verifica se o arranque foi bem-sucedido
        sniffer, consumer = rede.start_system()
        if sniffer and consumer:
            self._sniffer_obj = sniffer
            self._consumer_thread = consumer
            self._is_running = True
            return True
        else:
            # Se o sniffer ou o consumer não foram criados, o arranque falhou.
            self._is_running = False
            return False

    def stop(self):
        """Para o sistema de coleta de forma segura."""
        if not self._is_running:
            return False

        rede.stop_system()
        self._is_running = False
        self._sniffer_obj = None
        self._consumer_thread = None
        return True

    def get_status(self):
        """Verifica o estado do serviço de forma mais fiável."""
        # Se a flag de controlo estiver ativa, verifica se os processos ainda estão vivos.
        if self._is_running:
            # O sniffer tem o seu próprio método is_alive().
            sniffer_alive = self._sniffer_obj and self._sniffer_obj.is_alive()
            consumer_alive = self._consumer_thread and self._consumer_thread.is_alive()

            if sniffer_alive and consumer_alive:
                return "ativado"
            else:
                # Se algo morreu, o estado está inconsistente. Corrige-o.
                self._is_running = False

        return "desativado"

# Instância única para ser usada em toda a aplicação
scanner_service = ScannerService()