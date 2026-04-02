import os
import subprocess
import socket
import datetime
import re
import tkinter as tk
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# CONFIGURAÇÕES DE PRIVACIDADE E FILTROS
# ==========================================
MEU_HOSTNAME = "maicon-G5-5590"
MEU_IP_LOCAL = "172.23.26.59"

NOMES_MANUAIS = {
    "172.23.26.118": "NVR Principal VMI",
    "172.23.26.10": "Switch POE Central",
}

def get_device_name(ip):
    if ip in NOMES_MANUAIS:
        return NOMES_MANUAIS[ip]
    try:
        name = socket.gethostbyaddr(ip)[0]
        if name == MEU_HOSTNAME: return None
        return name
    except:
        return f"Câmera IP {ip.split('.')[-1]}"

def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((ip, port)) == 0

def get_network_details(ip, rede_base):
    if ip == MEU_IP_LOCAL: return None
    
    is_cctv_port = any(check_port(ip, p) for p in [554, 8000, 37777, 80, 8080])
    if not is_cctv_port and ip not in NOMES_MANUAIS: return None

    ping_proc = subprocess.run(["ping", "-c", "6", "-i", "0.2", "-W", "1", ip], capture_output=True, text=True)
    if ping_proc.returncode != 0: return None 

    stdout = ping_proc.stdout
    loss = int(re.search(r"(\d+)% packet loss", stdout).group(1))
    latency_data = re.search(r"min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", stdout)
    avg_latency = float(latency_data.group(2))
    jitter = float(latency_data.group(4))
    ttl = int(re.search(r"ttl=(\d+)", stdout).group(1))

    nome_real = get_device_name(ip)
    if nome_real is None: return None

    status, prioridade, classe_css = "Estável", "Normal", "status-ok"
    intervencao = "Sistema em conformidade técnica."

    if loss > 0:
        status, prioridade, classe_css = "Crítico", "ALTA", "status-fail"
        intervencao = f"Perda de {loss}% de pacotes. Risco de interrupção na gravação."
    elif jitter > 35:
        status, prioridade, classe_css = "Instável", "MÉDIA", "status-fail"
        intervencao = f"Jitter elevado ({jitter}ms). Variação excessiva no sinal."
    elif avg_latency > 100:
        status, prioridade, classe_css = "Alerta", "MÉDIA", "status-alert"
        intervencao = "Latência elevada. Verificar infraestrutura física."
    
    return {
        "ip": ip, "dispositivo": nome_real, "loss": loss, "latency": avg_latency,
        "jitter": jitter, "ttl": ttl, "status": status, "prioridade": prioridade,
        "classe": classe_css, "intervencao": intervencao
    }

def iniciar_auditoria(cliente, rede_base):
    if not cliente or not rede_base:
        messagebox.showwarning("Atenção", "Preencha todos os campos!")
        return
    if not rede_base.endswith('.'): rede_base += '.'
    if not os.path.exists('reports'): os.makedirs('reports')
    
    print(f"🚀 Iniciando Auditoria para: {cliente}")
    lista_ips = [f"{rede_base}{i}" for i in range(1, 255)]
    
    with ThreadPoolExecutor(max_workers=40) as executor:
        results = list(executor.map(lambda ip: get_network_details(ip, rede_base), lista_ips))
    
    cctv_devices = [r for r in results if r is not None]
    
    if cctv_devices:
        import reporterr
        path = reporterr.generate_html_report(cctv_devices, cliente)
        messagebox.showinfo("Sucesso", f"Laudo gerado com sucesso!\nSalvo em: {path}")
    else:
        messagebox.showwarning("Aviso", "Nenhum dispositivo de CFTV encontrado na rede.")

def abrir_janela():
    root = tk.Tk()
    root.title("CCTV-Sentinel Pro v5.8")
    root.geometry("400x250")
    tk.Label(root, text="Nome do Cliente:", font=("Arial", 10, "bold")).pack(pady=5)
    ent_cliente = tk.Entry(root, width=40); ent_cliente.pack(pady=5); ent_cliente.insert(0, "Condominio_Horizonte")
    tk.Label(root, text="Faixa de Rede (ex: 172.23.26.):", font=("Arial", 10, "bold")).pack(pady=5)
    ent_rede = tk.Entry(root, width=40); ent_rede.pack(pady=5); ent_rede.insert(0, "172.23.26.")
    btn_iniciar = tk.Button(root, text="GERAR LAUDO", bg="#10b981", fg="white", 
                           font=("Arial", 12, "bold"), command=lambda: iniciar_auditoria(ent_cliente.get(), ent_rede.get()))
    btn_iniciar.pack(pady=20)
    root.mainloop()

if __name__ == "__main__":
    abrir_janela()