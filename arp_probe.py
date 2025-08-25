# arp_probe.py
import sys
from scapy.all import srp, Ether, ARP, conf
import ipaddress

conf.verb = 0

def arp_scan(network_cidr, iface=None, timeout=2):
    net = ipaddress.ip_network(network_cidr, strict=False)
    target = str(net)
    print(f"[+] ARP probing {target} ... (iface={iface})")
    ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target),
                     timeout=timeout, iface=iface, verbose=False)
    hosts = []
    for snd, rcv in ans:
        hosts.append((rcv.psrc, rcv.hwsrc))
    return hosts

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: sudo python3 arp_probe.py 192.168.0.0/24 [iface]")
        sys.exit(1)
    network = sys.argv[1]
    iface = sys.argv[2] if len(sys.argv) >= 3 else None
    results = arp_scan(network, iface=iface)
    if results:
        print("Hosts encontrados:")
        for ip, mac in results:
            print(f" - {ip}  MAC:{mac}")
    else:
        print("Nenhum host respondeu ARP nesse range.")
