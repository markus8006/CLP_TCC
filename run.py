# run.py (Versão Simplificada)
from clp_app.server import server
# A importação do scanner_service pode ser necessária para garantir que a instância seja criada
from clp_app.scanner.service import scanner_service 

if __name__ == "__main__":
    # O scanner agora é iniciado e parado pela interface do usuário.
    # Não iniciamos mais as threads aqui.
    
    try:
        # Inicia apenas o servidor web.
        server.iniciar_web()
    except KeyboardInterrupt:
        print("Programa encerrado")
        # É uma boa prática garantir que o scanner pare ao encerrar o programa
        scanner_service.stop()