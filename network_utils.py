import subprocess
import socket
import re

def check_ping(ip):
    # -c 1 (1 pacote), -W 1 (espera 1s)
    command = ["ping", "-c", "1", "-W", "1", ip]
    return subprocess.call(command, stdout=subprocess.DEVNULL) == 0

def get_latency(ip):
    try:
        output = subprocess.check_output(["ping", "-c", "3", "-i", "0.2", ip], universal_newlines=True)
        times = re.findall(r"time=(\d+\.\d+)", output)
        if times:
            avg_latency = sum(float(t) for t in times) / len(times)
            return round(avg_latency, 2)
    except:
        return 999
    return 999

def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((ip, port)) == 0

def get_mac_address(ip):
    try:
        # Consulta a tabela ARP do Ubuntu
        subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL)
        output = subprocess.check_output(["arp", "-n", ip], universal_newlines=True)
        mac = re.search(r"(([a-f0-9]{2}:?){6})", output.lower())
        return mac.group(0) if mac else "Não encontrado"
    except:
        return "Erro"