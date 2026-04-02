import os
import subprocess
import socket
import datetime
import re
from flask import Flask, render_template_string, request, jsonify, send_from_directory, send_file
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ==========================================
# IDENTIFICAÇÃO AUTOMÁTICA (HOME AUTOMATION)
# ==========================================

def get_my_ip():
    """Descobre o IP do HP na rede atual do cliente"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip_detectado = s.getsockname()[0]
    except Exception:
        ip_detectado = '127.0.0.1'
    finally:
        s.close()
    return ip_detectado

def get_mac_address(ip):
    """Busca o MAC no cache ARP do Ubuntu (ip neigh)"""
    try:
        arp_out = subprocess.check_output(["ip", "neigh", "show", ip]).decode()
        if "lladdr" in arp_out:
            return arp_out.split("lladdr")[1].split()[0].upper()
    except:
        return None
    return None

def identify_vendor(mac):
    """Identifica o fabricante pelos 6 primeiros dígitos do MAC"""
    if not mac: return "Dispositivo"
    
    # Prefixos comuns em Automação e Redes
    vendors = {
        "00:1A:3F": "Intelbras/Dahua",
        "44:19:B6": "Hikvision",
        "18:FE:34": "Espressif (Sonoff/Tuya)",
        "BC:DD:C2": "TP-Link",
        "D8:00:4D": "Apple",
        "B4:E3:F9": "Samsung",
        "00:0C:29": "VMware"
    }
    prefix = mac[:8]
    return vendors.get(prefix, "Genérico")

def get_device_name(ip):
    """Tenta Hostname -> Se falhar, tenta Fabricante pelo MAC"""
    try:
        # Tenta resolver o nome que o dispositivo dá para a rede
        name_data = socket.gethostbyaddr(ip)
        hostname = name_data[0]
        if hostname != ip:
            return hostname
    except:
        pass
    
    # Se não tem nome de rede, identifica pelo hardware
    mac = get_mac_address(ip)
    vendor = identify_vendor(mac)
    return f"{vendor} ({ip.split('.')[-1]})"

# --- CONFIGURAÇÕES DO SISTEMA ---
MEU_IP_LOCAL = get_my_ip()
BASE_DIR = os.getcwd()
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGO_FILENAME = "logo.jpg"

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

# ==========================================
# LÓGICA DE VARREDURA (PING & JITTER)
# ==========================================

def get_network_details(ip):
    """Realiza a auditoria técnica de cada IP"""
    if ip == MEU_IP_LOCAL: return None
    
    # Ping rápido: 4 pacotes, espera 1s
    ping_proc = subprocess.run(["ping", "-c", "4", "-W", "1", ip], capture_output=True, text=True)
    if ping_proc.returncode != 0: return None 

    stdout = ping_proc.stdout
    loss = int(re.search(r"(\d+)% packet loss", stdout).group(1))
    lat_match = re.search(r"min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", stdout)
    
    avg_lat = float(lat_match.group(2)) if lat_match else 0.0
    jitter = float(lat_match.group(4)) if lat_match else 0.0

    # Critérios de Engenharia
    status, classe = "Estável", "status-ok"
    intervencao = "Sistema em conformidade."
    
    if loss > 0:
        status, classe = "Crítico", "status-fail"
        intervencao = f"Perda de {loss}%. Revisar infra."
    elif jitter > 30:
        status, classe = "Alerta", "status-alert"
        intervencao = "Jitter alto. Possível interferência."
    
    return {
        "ip": ip, "dispositivo": get_device_name(ip), "loss": loss, 
        "latency": avg_lat, "jitter": jitter, "status": status, 
        "classe": classe, "intervencao": intervencao
    }

# ==========================================
# INTERFACE PARA O TABLET
# ==========================================
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Pro - Home Automation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; text-align: center; padding: 20px; }
        .card { background: white; color: #333; padding: 30px; border-radius: 20px; max-width: 450px; margin: auto; }
        input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; }
        button { width: 100%; padding: 18px; background: #10b981; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; }
        #status { margin-top: 20px; font-weight: bold; color: #3b82f6; }
        .btn-dl { background: #3b82f6; text-decoration: none; padding: 15px; color: white; border-radius: 10px; display: block; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <img src="/logo.jpg" style="max-height: 60px; margin-bottom: 10px;" onerror="this.style.display='none'">
        <h2 style="margin:0">Sentinel Pro</h2>
        <p style="color:#64748b; font-size:14px;">Home Automation Technology</p>
        
        <input type="text" id="cli" placeholder="Cliente" value="Residencia_Automação">
        <input type="text" id="net" placeholder="Faixa de Rede (ex: 192.168.0.)" value="192.168.0.">
        
        <button id="btn" onclick="runAudit()">INICIAR AUDITORIA</button>
        <div id="status">Pronto para escanear.</div>
        <a id="dl" class="btn-dl" style="display:none;" target="_blank">BAIXAR LAUDO TÉCNICO</a>
    </div>

    <script>
        function runAudit() {
            const btn = document.getElementById('btn');
            const status = document.getElementById('status');
            const dl = document.getElementById('dl');
            
            btn.disabled = true;
            dl.style.display = "none";
            status.innerHTML = "🚀 Varrendo rede...<br><small>O HP está identificando os ativos.</small>";
            
            fetch('/audit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    cliente: document.getElementById('cli').value, 
                    rede: document.getElementById('net').value
                })
            })
            .then(res => res.json())
            .then(data => {
                status.innerHTML = "✅ Auditoria Concluída!";
                btn.disabled = false;
                dl.href = "/download/" + data.filename;
                dl.style.display = "block";
            })
            .catch(err => {
                status.innerText = "❌ Erro de conexão com o HP.";
                btn.disabled = false;
            });
        }
    </script>
</body>
</html>
"""

# ==========================================
# ROTAS FLASK
# ==========================================

@app.route('/')
def home():
    return render_template_string(HTML_INTERFACE)

@app.route('/logo.jpg')
def serve_logo():
    return send_file(os.path.join(BASE_DIR, LOGO_FILENAME))

@app.route('/audit', methods=['POST'])
def audit():
    req = request.json
    rede = req['rede'] if req['rede'].endswith('.') else req['rede'] + '.'
    
    # Redescobre o IP antes de cada scan
    ip_atual = get_my_ip()
    ips = [f"{rede}{i}" for i in range(1, 255)]
    
    # 50 threads para ser ultra rápido no notebook HP
    with ThreadPoolExecutor(max_workers=50) as exe:
        results = [r for r in list(exe.map(get_network_details, ips)) if r]
    
    import reporter
    import importlib
    importlib.reload(reporter) # Garante que o reporter.py atualizado seja lido
    
    filename = reporter.generate_html_report(results, req['cliente'], ip_atual)
    return jsonify({"filename": filename})

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(REPORTS_DIR, filename)

if __name__ == "__main__":
    print(f"--- HOME AUTOMATION TECHNOLOGY ---")
    print(f"ACESSE NO TABLET: http://{MEU_IP_LOCAL}:5000")
    app.run(host='0.0.0.0', port=5000)