import os
import subprocess
import socket
import datetime
import re
from flask import Flask, render_template_string, request, jsonify, send_from_directory, send_file
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ==========================================
# FUNÇÃO DE AUTOMAÇÃO DE IP (MAICON FERREIRA)
# ==========================================
def get_my_ip():
    """ Descobre o IP real do notebook na rede atual do cliente automaticamente """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Tenta traçar uma rota externa (não precisa de internet real)
        s.connect(('8.8.8.8', 1))
        ip_detectado = s.getsockname()[0]
    except Exception:
        ip_detectado = '127.0.0.1'
    finally:
        s.close()
    return ip_detectado

# Configurações Iniciais Dinâmicas
MEU_IP_LOCAL = get_my_ip()
BASE_DIR = os.getcwd()
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGO_FILENAME = "logo.jpg"

# Nomes conhecidos para facilitar sua auditoria na VMI
NOMES_MANUAIS = {
    "172.23.26.118": "NVR Principal VMI",
    "172.23.26.10": "Switch POE Central",
}

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

# ==========================================
# LÓGICA DE VARREDURA DE REDE
# ==========================================

def get_device_name(ip):
    if ip in NOMES_MANUAIS: return NOMES_MANUAIS[ip]
    try:
        return f"Câmera IP {ip.split('.')[-1]}"
    except:
        return "Dispositivo Desconhecido"

def check_port(ip, port):
    """ Verifica se portas de vídeo/CCTV estão abertas """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((ip, port)) == 0

def get_network_details(ip):
    """ Realiza o Ping e Jitter real no cliente """
    if ip == MEU_IP_LOCAL: return None
    
    # Filtro inteligente: Só audita se for porta de CCTV ou estiver na lista
    is_cctv = any(check_port(ip, p) for p in [554, 8000, 37777, 80, 8080])
    if not is_cctv and ip not in NOMES_MANUAIS: return None

    # Executa pings para medir estabilidade
    ping_proc = subprocess.run(["ping", "-c", "6", "-i", "0.2", "-W", "1", ip], capture_output=True, text=True)
    if ping_proc.returncode != 0: return None 

    stdout = ping_proc.stdout
    loss = int(re.search(r"(\d+)% packet loss", stdout).group(1))
    lat_match = re.search(r"min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", stdout)
    
    avg_lat = float(lat_match.group(2)) if lat_match else 0.0
    jitter = float(lat_match.group(4)) if lat_match else 0.0

    status, classe = "Estável", "status-ok"
    intervencao = "Sistema em conformidade técnica."
    
    if loss > 0:
        status, classe = "Crítico", "status-fail"
        intervencao = f"Perda de {loss}% de pacotes. Revisar conectores."
    elif jitter > 35:
        status, classe = "Instável", "status-fail"
        intervencao = f"Jitter elevado ({jitter}ms). Possível gargalo no Switch."
    
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
    <title>Sentinel Pro v7.0</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f1f5f9; color: #0f172a; text-align: center; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 20px; max-width: 450px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #10b981; }
        input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 18px; background: #10b981; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 18px; cursor: pointer; transition: 0.3s; }
        #status { margin: 25px 0; font-weight: bold; color: #3b82f6; min-height: 50px; }
        .btn-download { background: #3b82f6; text-decoration: none; padding: 15px; color: white; border-radius: 10px; display: block; margin-top: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <img src="/logo.jpg" style="max-height: 60px; margin-bottom: 20px;" onerror="this.style.display='none'">
        <h2>Sentinel Pro Cloud-Link</h2>
        <p style="color:#64748b;">Auditoria de Campo Automatizada</p>
        
        <input type="text" id="cli" placeholder="Cliente" value="Condominio_Horizonte">
        <input type="text" id="net" placeholder="Rede (ex: 172.23.26.)" value="172.23.26.">
        
        <button id="btn" onclick="run()">INICIAR VARREDURA REAL</button>
        
        <div id="status">Aguardando comando...</div>
        <a id="dl" class="btn-download" style="display:none;" target="_blank">VER LAUDO GERADO</a>
    </div>

    <script>
        function run() {
            const btn = document.getElementById('btn');
            const status = document.getElementById('status');
            const dl = document.getElementById('dl');
            
            btn.disabled = true;
            btn.style.opacity = "0.5";
            dl.style.display = "none";
            status.innerHTML = "🚀 Varrendo rede...<br><small>O HP está disparando pings agora.</small>";
            
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
                status.innerHTML = "✅ Auditoria Completa!";
                btn.disabled = false; btn.style.opacity = "1";
                dl.href = "/download/" + data.filename;
                dl.style.display = "block";
                setTimeout(() => { window.location.href = dl.href; }, 1000);
            })
            .catch(err => {
                status.innerText = "❌ Erro: Verifique a conexão do HP.";
                btn.disabled = false; btn.style.opacity = "1";
            });
        }
    </script>
</body>
</html>
"""

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
    
    # Identifica o IP atual automaticamente antes de gerar o laudo
    ip_atual = get_my_ip()
    ips = [f"{rede}{i}" for i in range(1, 255)]
    
    with ThreadPoolExecutor(max_workers=50) as exe:
        results = [r for r in list(exe.map(get_network_details, ips)) if r]
    
    import reporter
    # Passa o ip_atual para o reporter.py carregar a logo via rede
    filename = reporter.generate_html_report(results, req['cliente'], ip_atual)
    return jsonify({"filename": filename})

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(REPORTS_DIR, filename)

if __name__ == "__main__":
    print(f"--- SENTINEL PRO ATIVADO ---")
    print(f"IP DO NOTEBOOK: {MEU_IP_LOCAL}")
    print(f"ACESSE NO TABLET: http://{MEU_IP_LOCAL}:5000")
    print(f"----------------------------")
    app.run(host='0.0.0.0', port=5000)