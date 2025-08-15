import subprocess
import time
import json

processos = []
dist = "clp\\IPS\\"

def iniciar_programa(delay: int = 4):
    """Inicia o coletor, o emissor e o kernel, cada um em seu CMD."""
    
    # Inicia o coletor
    p1 = subprocess.Popen(
        f'start "Coletor" cmd /k python {dist}coletor.py',
        shell=True
    )
    processos.append(p1)
    
    time.sleep(delay)
    
    # Inicia o consumidor
    p2 = subprocess.Popen(
        f'start "Consumidor" cmd /k python {dist}consumidor.py',
        shell=True
    )
    processos.append(p2)
    
    # Inicia o kernel
    p3 = subprocess.Popen(
        f'start "Kernel" cmd /k python {dist}kernel.py',
        shell=True
    )
    processos.append(p3)
    
    # Salva os PIDs (apenas do Popen, não do processo CMD em si)
    with open("processos.json", "w") as f:
        json.dump([p.pid for p in processos], f)

if __name__ == "__main__":
    iniciar_programa()
