import os
import subprocess
import socket
import datetime
import re
from flask import Flask, render_template_string, request, jsonify, send_from_directory, send_file
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES DO MAICON FERREIRA
# ==========================================
MEU_HOSTNAME = "maicon-G5-5590"
MEU_IP_LOCAL = "172.23.26.59" # IP do teu HP na rede do cliente
BASE_DIR = os.getcwd()
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGO_FILENAME = "logo.jpg" # O nome exato da tua imagem na raiz

NOMES_MANUAIS = {
    "172.23.26.118": "NVR Principal VMI",
    "172.23.26.10": "Switch POE Central",
}

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def get_device_name(ip):
    if ip in NOMES_MANUAIS: return NOMES_MANUAIS[ip]
    try:
        name = socket.gethostbyaddr(ip)[0]
        return name if name != MEU_HOSTNAME else None
    except:
        return f"Câmera IP {ip.split('.')[-1]}"

def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((ip, port)) == 0

def get_network_details(ip):
    if ip == MEU_IP_LOCAL: return None
    is_cctv_port = any(check_port(ip, p) for p in [554, 8000, 37777, 80, 8080])
    if not is_cctv_port and ip not in NOMES_MANUAIS: return None

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
        intervencao = f"Perda de {loss}% de pacotes. Risco de queda."
    elif jitter > 35:
        status, classe = "Instável", "status-fail"
        intervencao = f"Jitter elevado ({jitter}ms). Vídeo com travamentos."
    
    return {
        "ip": ip, "dispositivo": get_device_name(ip), "loss": loss, 
        "latency": avg_lat, "jitter": jitter, "status": status, 
        "classe": classe, "intervencao": intervencao
    }

# --- INTERFACE WEB PARA O TABLET ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Pro v6.1</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f1f5f9; color: #0f172a; text-align: center; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 20px; max-width: 450px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #0f172a; }
        input { width: 90%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; }
        button { width: 95%; padding: 18px; background: #10b981; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 18px; margin-top: 10px; cursor: pointer; }
        #status { margin-top: 25px; font-weight: bold; color: #3b82f6; min-height: 50px; }
        .btn-download { background: #3b82f6; display: none; text-decoration: none; padding: 15px; color: white; border-radius: 10px; margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <img src="/logo.jpg" alt="VMI Sistemas" style="max-height: 60px; margin-bottom: 20px;" onerror="this.style.display='none'">
        <h2>CCTV-Sentinel Pro</h2>
        <p>Auditoria de Campo - Engenharia</p>
        <input type="text" id="cli" placeholder="Cliente" value="Condominio_Horizonte">
        <input type="text" id="net" placeholder="Rede (ex: 172.23.26.)" value="172.23.26.">
        <button id="btn" onclick="run()">INICIAR VARREDURA</button>
        <div id="status">Aguardando comando...</div>
        <a id="downloadLink" class="btn-download" target="_blank">ABRIR LAUDO GERADO</a>
    </div>

    <script>
        function run() {
            const btn = document.getElementById('btn');
            const status = document.getElementById('status');
            const dl = document.getElementById('downloadLink');
            
            btn.disabled = true;
            btn.style.opacity = "0.5";
            dl.style.display = "none";
            status.innerHTML = "🚀 Auditoria em progresso...<br><small>O HP está a varrer a rede local.</small>";
            
            // Procure por esta linha no seu JavaScript dentro do app.py:
            fetch('/audit', {  // <-- Use apenas '/audit' (caminho relativo)
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    cliente: document.getElementById('cli').value, 
                    rede: document.getElementById('net').value
                })
            })
            .then(res => res.json())
            .then(data => {
                status.innerHTML = "✅ Concluído!";
                btn.disabled = false;
                btn.style.opacity = "1";
                // O link aponta para a rota de download do Flask
                dl.href = "/download/" + data.filename;
                dl.style.display = "block";
                // Redireciona automaticamente após 1.5 segundos
                setTimeout(() => { window.location.href = dl.href; }, 1500);
            })
            .catch(err => {
                status.innerText = "❌ Erro na conexão com o HP. Verifica se o servidor está a correr.";
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

# --- NOVO: Rota para servir a tua LOGO ---
@app.route('/logo.jpg')
def serve_logo():
    # Procura a imagem na raiz do projeto (junto ao app.py)
    return send_file(os.path.join(BASE_DIR, LOGO_FILENAME), mimetype='image/jpeg')

@app.route('/audit', methods=['POST'])
def audit():
    req = request.json
    rede = req['rede'] if req['rede'].endswith('.') else req['rede'] + '.'
    ips = [f"{rede}{i}" for i in range(1, 255)]
    
    with ThreadPoolExecutor(max_workers=40) as exe:
        results = [r for r in list(exe.map(get_network_details, ips)) if r]
    
    # Importamos o reporter corrigido
    import reporter
    # Passamos o IP do HP para o reporter usar no link da imagem
    filename = reporter.generate_html_report(results, req['cliente'], MEU_IP_LOCAL)
    return jsonify({"filename": filename})

@app.route('/download/<path:filename>')
def download(filename):
    # Serve o arquivo HTML gerado dentro da pasta reports
    return send_from_directory(REPORTS_DIR, filename)

if __name__ == "__main__":
    # 0.0.0.0 liberta o acesso para o teu Tablet na rede Wi-Fi
    app.run(host='0.0.0.0', port=5000)