# teste_scapy.py
import os
from scapy.all import get_working_ifaces, conf

# Tenta desativar a verificação de rotas IPv6 que pode causar problemas
conf.ipv6_enabled = False

print("A testar a instalação do Scapy e Npcap...")
print("-" * 30)

try:
    # A função mais básica: listar as interfaces de rede que o Scapy consegue usar.
    interfaces_ativas = get_working_ifaces()
    
    if not interfaces_ativas:
        print("\nERRO: O Scapy foi executado, mas não encontrou nenhuma interface de rede funcional.")
        print("Isto pode acontecer se o Npcap não estiver instalado com o 'modo de compatibilidade WinPcap'.")
    else:
        print("\nSUCESSO! O Scapy encontrou as seguintes interfaces de rede:")
        for iface in interfaces_ativas:
            # O .name e .description podem não estar sempre disponíveis, por isso usamos .get()
            nome = iface.get('name', 'N/A')
            descricao = iface.get('description', 'N/A')
            ip = iface.get('ip', 'N/A')
            print(f"  - Nome: {nome:<25} | IP: {ip:<15} | Descrição: {descricao}")
        print("\nSe vir esta lista, a sua instalação do Scapy e Npcap está a funcionar corretamente.")

except Exception as e:
    print(f"\nFALHA CRÍTICA: Ocorreu um erro ao tentar usar o Scapy.")
    print(f"Erro: {e}")
    print("\nIsto confirma que o problema está na instalação do Scapy/Npcap e não na sua aplicação Flask.")
    print("Por favor, verifique se executou este script como Administrador.")

print("-" * 30)