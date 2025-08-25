# modbus_bruteforce.py
import sys
import ipaddress
from pymodbus.client import ModbusTcpClient
import socket

def modbus_check(ip, port=502, timeout=2):
    try:
        client = ModbusTcpClient(host=str(ip), port=port, timeout=timeout)
        ok = client.connect()
        client.close()
        return ok
    except Exception:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 modbus_bruteforce.py 192.168.0.0/24")
        sys.exit(1)
    network = ipaddress.ip_network(sys.argv[1])
    for host in network.hosts():
        ip = str(host)
        try:
            if modbus_check(ip):
                print("Modbus respondendo em:", ip)
        except KeyboardInterrupt:
            break
s