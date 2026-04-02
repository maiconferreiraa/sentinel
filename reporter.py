import datetime
import os

def generate_html_report(results, cliente_name, hp_ip):
    """
    Gera o laudo técnico em HTML com gráficos e tabelas.
    hp_ip: Necessário para o tablet carregar a logo via rede local.
    """
    agora = datetime.datetime.now()
    data_formatada = agora.strftime('%d-%m-%Y_%H-%M')
    data_visual = agora.strftime('%d/%m/%Y %H:%M')
    
    # Nome do arquivo único para o laudo
    nome_arq = f"Laudo_{cliente_name}_{data_formatada}.html"
    
    # Pasta onde o arquivo será salvo (o app.py já garante que ela existe)
    caminho_final = os.path.join("reports", nome_arq)
    
    # URL da logo servida pelo Flask no seu HP
    logo_url = f"http://{hp_ip}:5000/logo.jpg"
    
    # Métricas para o Dashboard e Gráfico
    estaveis = len([r for r in results if r['status'] == "Estável"])
    alertas = len([r for r in results if r['status'] == "Alerta"])
    criticos = len([r for r in results if r['status'] in ["Crítico", "Instável"]])
    score = int((estaveis / len(results)) * 100) if results else 0

    # Início do HTML do Laudo
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #0f172a; --success: #10b981; --danger: #ef4444; --warning: #f59e0b; --bg: #f1f5f9;
            }}
            @page {{ size: auto; margin: 10mm; }}
            @media print {{
                body {{ background: white !important; }}
                .container {{ box-shadow: none !important; border: none !important; width: 100% !important; }}
                .no-print {{ display: none; }}
            }}
            body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--primary); margin: 0; padding: 20px; }}
            .container {{ max-width: 1050px; margin: auto; background: white; padding: 40px; border-radius: 16px; border-top: 10px solid var(--primary); box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; }}
            .logo {{ max-height: 70px; }}

            .dashboard {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
            .card {{ padding: 15px; border-radius: 10px; background: #fff; border: 1px solid #e2e8f0; border-left: 5px solid #64748b; }}
            .card .value {{ font-size: 24px; font-weight: 800; display: block; }}
            .card .label {{ font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b; }}

            table {{ width: 100%; border-collapse: separate; border-spacing: 0 8px; }}
            th {{ color: #64748b; padding: 10px; font-size: 11px; text-transform: uppercase; text-align: left; }}
            td {{ padding: 15px; background: #fff; border-top: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; font-size: 13px; }}
            td:first-child {{ border-left: 1px solid #f1f5f9; border-radius: 8px 0 0 8px; }}
            td:last-child {{ border-right: 1px solid #f1f5f9; border-radius: 0 8px 8px 0; }}

            .badge {{ padding: 5px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; color: white; text-transform: uppercase; }}
            .status-ok {{ background: var(--success); }}
            .status-fail {{ background: var(--danger); }}
            .status-alert {{ background: var(--warning); }}

            .guide-section {{ background: #f8fafc; border-radius: 12px; padding: 25px; margin-top: 30px; border: 1px solid #e2e8f0; }}
            .guide-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .guide-item h4 {{ margin: 0 0 5px 0; font-size: 12px; color: var(--primary); border-left: 3px solid var(--primary); padding-left: 10px; }}
            .guide-item p {{ margin: 0; font-size: 11px; color: #64748b; line-height: 1.5; }}

            .signature-box {{ margin-top: 40px; display: flex; justify-content: space-between; align-items: center; }}
            .line {{ border-top: 2px solid #333; width: 250px; text-align: center; padding-top: 5px; font-weight: 700; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="margin:0; letter-spacing:-1px;">Auditoria de Infraestrutura Digital</h1>
                    <p style="margin:5px 0; color:#64748b;">Cliente: <strong>{cliente_name}</strong> | Gerado em: {data_visual}</p>
                </div>
                <img src="{logo_url}" alt="Logo" class="logo" onerror="this.style.display='none'">
            </div>

            <div class="dashboard">
                <div class="card" style="border-left-color: #3b82f6;"><span class="label">Dispositivos</span><span class="value">{len(results)}</span></div>
                <div class="card" style="border-left-color: var(--success);"><span class="label">Saúde da Rede</span><span class="value" style="color:var(--success)">{score}%</span></div>
                <div class="card" style="border-left-color: var(--warning);"><span class="label">Alertas</span><span class="value" style="color:var(--warning)">{alertas}</span></div>
                <div class="card" style="border-left-color: var(--danger);"><span class="label">Críticos</span><span class="value" style="color:var(--danger)">{criticos}</span></div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Ativo / IP</th>
                        <th>Perda</th>
                        <th>Latência</th>
                        <th>Jitter</th>
                        <th>Estado</th>
                        <th>Intervenção Sugerida</th>
                    </tr>
                </thead>
                <tbody>
    """

    for r in results:
        html += f"""
                <tr>
                    <td><strong>{r['dispositivo']}</strong><br><small style="color:#64748b">{r['ip']}</small></td>
                    <td>{r['loss']}%</td>
                    <td>{r['latency']}ms</td>
                    <td>{r['jitter']}ms</td>
                    <td><span class="badge {r['classe']}">{r['status']}</span></td>
                    <td style="font-size:11px; font-style:italic;">{r['intervencao']}</td>
                </tr>
        """

    html += f"""
                </tbody>
            </table>

            <div class="guide-section">
                <h3 style="margin:0 0 15px 0; font-size: 14px; text-transform: uppercase;">Guia de Referência Técnica</h3>
                <div class="guide-grid">
                    <div class="guide-item">
                        <h4>Perda de Dados (Packet Loss)</h4>
                        <p>O ideal é 0%. Perdas indicam falhas físicas em cabos ou interferência eletromagnética grave.</p>
                    </div>
                    <div class="guide-item">
                        <h4>Jitter (Estabilidade)</h4>
                        <p>Variação no tempo de resposta. Acima de 35ms causa "engasgos" e perda de frames no vídeo.</p>
                    </div>
                </div>
            </div>

            <div class="signature-box">
                <div style="width:200px;"><canvas id="chart"></canvas></div>
                <div class="signature">
                    <div class="line">Maicon Ferreira</div>
                    <small style="color:#64748b">Engenheiro de Controle e Automação</small><br>
                    <span style="font-size:10px; background:var(--primary); color:white; padding:3px 8px; border-radius:4px; margin-top:10px; display:inline-block;">LAUDO CERTIFICADO</span>
                </div>
            </div>

            <script>
                new Chart(document.getElementById('chart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Ok', 'Alerta', 'Erro'],
                        datasets: [{{
                            data: [{estaveis}, {alertas}, {criticos}],
                            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{ cutout: '75%', plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 10 }} }} }} }} }}
                }});
            </script>
        </div>
    </body>
    </html>
    """
    
    # Salva o arquivo fisicamente na pasta reports
    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(html)
        
    return nome_arq  # Retorna o nome para o app.py criar o link de download