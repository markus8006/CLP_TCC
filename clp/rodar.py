import subprocess
import time
import json

processos = []

def iniciar_programa(delay: int = 4):
    """Inicia o coletor, o consumidor e o kernel, cada um em seu CMD."""

    # Inicia o coletor
    p1 = subprocess.Popen(
        'start "Coletor" cmd /k python -m clp.IPS.coletor',
        shell=True
    )
    processos.append(p1)

    time.sleep(delay)

    # Inicia o consumidor
    p2 = subprocess.Popen(
        'start "Consumidor" cmd /k python -m clp.IPS.consumidor',
        shell=True
    )
    processos.append(p2)

    # Inicia o kernel
    p3 = subprocess.Popen(
        'start "Kernel" cmd /k python -m clp.IPS.kernel',
        shell=True
    )
    processos.append(p3)

    # Salva os PIDs dos processos iniciados
    with open("processos.json", "w") as f:
        json.dump([p.pid for p in processos], f)

if __name__ == "__main__":
    iniciar_programa()
