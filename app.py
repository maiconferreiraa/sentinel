import os
import subprocess
import socket
import datetime
import re
from flask import Flask, render_template_string, request, jsonify, send_from_directory, send_file
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES DO ENGENHEIRO MAICON
# ==========================================
MEU_HOSTNAME = "maicon-G5-5590"
# O IP do HP na rede do cliente (mude se o roteador der outro IP)
MEU_IP_LOCAL = "172.23.26.59" 
BASE_DIR = os.getcwd()
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGO_FILENAME = "logo.jpg"

NOMES_MANUAIS = {
    "172.23.26.118": "NVR Principal VMI",
    "172.23.26.10": "Switch POE Central",
}

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def get_device_name(ip):
    if ip in NOMES_MANUAIS: return NOMES_MANUAIS[ip]
    try:
        # Tenta resolver o nome via DNS local
        name = socket.gethostbyaddr(ip)[0]
        return name if name != MEU_HOSTNAME else None
    except:
        return f"Câmera IP {ip.split('.')[-1]}"

def check_port(ip, port):
    """ Verifica se portas comuns de CFTV estão abertas """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((ip, port)) == 0

def get_network_details(ip):
    """ Realiza a varredura real de Ping e Jitter (Roda no HP) """
    if ip == MEU_IP_LOCAL: return None
    
    # Filtro: Só processa se for dispositivo de vídeo ou estiver na lista manual
    is_cctv = any(check_port(ip, p) for p in [554, 8000, 37777, 80, 8080])
    if not is_cctv and ip not in NOMES_MANUAIS: return None

    # Executa 6 pings rápidos
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
        intervencao = f"Perda de {loss}% de pacotes. Verifique cabos/conectores."
    elif jitter > 35:
        status, classe = "Instável", "status-fail"
        intervencao = f"Jitter elevado ({jitter}ms). Possível sobrecarga no Switch."
    elif avg_lat > 100:
        status, classe = "Alerta", "status-alert"
        intervencao = "Latência alta. Verificar distância do cabeamento."
    
    return {
        "ip": ip, "dispositivo": get_device_name(ip), "loss": loss, 
        "latency": avg_lat, "jitter": jitter, "status": status, 
        "classe": classe, "intervencao": intervencao
    }

# --- INTERFACE QUE APARECERÁ NO SEU TABLET ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Pro v6.2</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; color: #0f172a; text-align: center; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 20px; max-width: 450px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #0f172a; }
        input { width: 90%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 18px; background: #10b981; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 18px; margin-top: 10px; cursor: pointer; transition: 0.3s; }
        button:active { transform: scale(0.98); }
        #status { margin-top: 25px; font-weight: bold; color: #3b82f6; min-height: 60px; line-height: 1.4; }
        .btn-download { background: #3b82f6; display: none; text-decoration: none; padding: 15px; color: white; border-radius: 10px; margin-top: 20px; font-weight: bold; display: block; }
    </style>
</head>
<body>
    <div class="card">
        <img src="/logo.jpg" style="max-height: 60px; margin-bottom: 20px;" onerror="this.style.display='none'">
        <h2 style="margin:0">CCTV-Sentinel Pro</h2>
        <p style="color:#64748b; margin-bottom:20px;">Auditoria de Infraestrutura VMI</p>
        
        <input type="text" id="cli" placeholder="Nome do Cliente" value="Condominio_Horizonte">
        <input type="text" id="net" placeholder="Faixa de Rede (ex: 172.23.26.)" value="172.23.26.">
        
        <button id="btn" onclick="runAudit()">INICIAR VARREDURA REAL</button>
        
        <div id="status">Aguardando comando do tablet...</div>
        <a id="downloadLink" class="btn-download" style="display:none;" target="_blank">ABRIR LAUDO TÉCNICO</a>
    </div>

    <script>
        function runAudit() {
            const btn = document.getElementById('btn');
            const status = document.getElementById('status');
            const dl = document.getElementById('downloadLink');
            
            const cli = document.getElementById('cli').value;
            const net = document.getElementById('net').value;

            if(!net.includes('.')) { alert("Formato de rede inválido!"); return; }

            btn.disabled = true;
            btn.style.opacity = "0.5";
            dl.style.display = "none";
            status.innerHTML = "🚀 Varredura em curso...<br><small>O HP está testando cada IP na rede local.</small>";
            
            fetch('/audit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cliente: cli, rede: net})
            })
            .then(res => res.json())
            .then(data => {
                status.innerHTML = "✅ Auditoria Finalizada!";
                btn.disabled = false;
                btn.style.opacity = "1";
                dl.href = "/download/" + data.filename;
                dl.style.display = "block";
                // Abre o laudo automaticamente no tablet após 1 segundo
                setTimeout(() => { window.location.href = dl.href; }, 1000);
            })
            .catch(err => {
                status.innerText = "❌ Erro: Perda de conexão com o HP.";
                btn.disabled = false;
                btn.style.opacity = "1";
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
    
    # Lista de IPs de 1 a 254
    ips = [f"{rede}{i}" for i in range(1, 255)]
    
    # Dispara 40 threads para ser ultra rápido no HP
    with ThreadPoolExecutor(max_workers=40) as exe:
        results = [r for r in list(exe.map(get_network_details, ips)) if r]
    
    import reporterr
    # Passamos o IP local para o reporter carregar a logo via rede
    filename = reporterr.generate_html_report(results, req['cliente'], MEU_IP_LOCAL)
    return jsonify({"filename": filename})

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(REPORTS_DIR, filename)

if __name__ == "__main__":
    # Roda o servidor na porta 5000 acessível por qualquer dispositivo no Wi-Fi
    app.run(host='0.0.0.0', port=5000)