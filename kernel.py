import subprocess
import time

# Lista com os títulos das janelas que queremos fechar
janelas = ["Coletor - python coletor.py", "Consumidor - python consumidor.py", "Kernel"]

def fechar_todas():
    for janela in janelas:
        try:
            # /F força o fechamento, /FI filtra pelo título da janela
            subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq {janela}"', shell=True)
            print(f"{janela} fechada com sucesso!")
        except Exception as e:
            print(f"Erro ao terminar processo {janela}: {e}")

if __name__ == "__main__":
    print("Executando kernel...")
    try:
        while True:
            comando = input(">> ")
            if comando.lower() in ["quit", "sair", "exit"]:
                fechar_todas()
                break
            else:
                print(f"Comando '{comando}' não reconhecido.")
    except KeyboardInterrupt:
        fechar_todas()
