import datetime
import os

def generate_html_report(results, cliente_name):
    agora = datetime.datetime.now()
    data_formatada = agora.strftime('%d-%m-%Y_%H-%M')
    data_visual = agora.strftime('%d/%m/%Y %H:%M')
    nome_arq = f"Laudo_{cliente_name}_{data_formatada}.html"
    caminho_final = os.path.join("reports", nome_arq)
    
    estaveis = len([r for r in results if r['status'] == "Estável"])
    alertas = len([r for r in results if r['status'] == "Alerta"])
    criticos = len([r for r in results if r['status'] == "Crítico" or r['status'] == "Instável"])
    score = int((estaveis / len(results)) * 100) if results else 0

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --primary: #0f172a;
                --success: #10b981;
                --danger: #ef4444;
                --warning: #f59e0b;
                --bg: #f1f5f9;
            }}
            @page {{ size: auto; margin: 10mm; }}
            @media print {{
                body {{ background: white !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .container {{ box-shadow: none !important; border: none !important; width: 100% !important; max-width: 100% !important; padding: 0 !important; }}
                .badge {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .page-break {{ page-break-before: always; }}
                thead {{ display: table-header-group; }}
            }}
            body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--primary); margin: 0; padding: 30px; }}
            .container {{ max-width: 1100px; margin: auto; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-top: 10px solid var(--primary); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; }}
            .logo {{ max-height: 80px; }}
            .dashboard {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
            .card {{ padding: 15px; border-radius: 10px; background: #fff; border: 1px solid #e2e8f0; border-left: 5px solid #64748b; }}
            .card-total {{ border-left-color: #3b82f6; }}
            .card-ok {{ border-left-color: var(--success); }}
            .card-alert {{ border-left-color: var(--warning); }}
            .card-fail {{ border-left-color: var(--danger); }}
            .card .label {{ font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b; }}
            .card .value {{ font-size: 24px; font-weight: 800; display: block; }}
            table {{ width: 100%; border-collapse: separate; border-spacing: 0 8px; margin-bottom: 30px; }}
            th {{ color: #64748b; padding: 10px 15px; font-size: 11px; text-transform: uppercase; text-align: left; }}
            td {{ padding: 15px; background: #fff; border-top: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; font-size: 13px; }}
            td:first-child {{ border-left: 1px solid #f1f5f9; border-radius: 8px 0 0 8px; }}
            td:last-child {{ border-right: 1px solid #f1f5f9; border-radius: 0 8px 8px 0; }}
            .badge {{ padding: 6px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; color: white !important; text-transform: uppercase; display: inline-block; min-width: 80px; text-align: center; }}
            .status-ok {{ background-color: var(--success) !important; }}
            .status-fail {{ background-color: var(--danger) !important; }}
            .status-alert {{ background-color: var(--warning) !important; }}
            .guide-section {{ background: #f8fafc; border-radius: 12px; padding: 30px; border: 1px solid #e2e8f0; page-break-inside: avoid; }}
            .guide-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .guide-item h4 {{ margin: 0 0 5px 0; color: #334155; font-size: 13px; text-transform: uppercase; border-left: 3px solid var(--primary); padding-left: 10px; }}
            .guide-item p {{ margin: 0; font-size: 12px; color: #64748b; line-height: 1.5; }}
            .final-layout {{ display: flex; justify-content: space-between; align-items: center; margin-top: 30px; }}
            .footer-signature {{ text-align: center; }}
            .signature-line {{ border-bottom: 2px solid #333; width: 250px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="margin:0; letter-spacing:-1px;">Relatório de Auditoria Digital CFTV</h1>
                    <p style="margin:5px 0; color:#64748b;">Referência: <strong>{cliente_name}</strong> | Data: {data_visual}</p>
                </div>
                <img src="../logo.jpg" alt="Logo" class="logo" onerror="this.style.display='none'">
            </div>

            <div class="dashboard">
                <div class="card card-total"><span class="label">Dispositivos</span><span class="value">{len(results)}</span></div>
                <div class="card card-ok"><span class="label">Saúde Geral</span><span class="value" style="color:var(--success)">{score}%</span></div>
                <div class="card card-alert"><span class="label">Alertas</span><span class="value" style="color:var(--warning)">{alertas}</span></div>
                <div class="card card-fail"><span class="label">Críticos</span><span class="value" style="color:var(--danger)">{criticos}</span></div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Identificação / IP</th>
                        <th>Perda</th>
                        <th>Ping</th>
                        <th>Jitter</th>
                        <th>Estado</th>
                        <th>Intervenção</th>
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
                    <td style="font-size:12px; font-style:italic;">{r['intervencao']}</td>
                </tr>
        """

    html += f"""
                </tbody>
            </table>
            <div class="page-break"></div>
            <div class="guide-section">
                <h3 style="margin:0 0 20px 0; color:var(--primary); text-transform: uppercase; font-size: 16px;">📖 Guia de Interpretação Técnica</h3>
                <div class="guide-grid">
                    <div class="guide-item">
                        <h4>Identificação / IP</h4>
                        <p>Refere-se ao nome amigável do dispositivo e seu endereço único na rede. Facilita a localização física do ativo no local.</p>
                    </div>
                    <div class="guide-item">
                        <h4>Perda de Dados (Packet Loss)</h4>
                        <p>O ideal é <b>0%</b>. Qualquer perda indica que pacotes de vídeo foram descartados no trajeto, gerando falhas de imagem e lacunas na gravação.</p>
                    </div>
                    <div class="guide-item">
                        <h4>Ping (Latência)</h4>
                        <p>Mede o tempo de resposta da rede. Deve ser abaixo de <b>50ms</b>. Valores altos causam atraso severo no monitoramento e nos comandos das câmeras.</p>
                    </div>
                    <div class="guide-item">
                        <h4>Jitter (Oscilação de Sinal)</h4>
                        <p>Mede a estabilidade da latência. Se o Jitter for alto, a imagem sofrerá pequenos travamentos e perda de fluidez (stuttering).</p>
                    </div>
                    <div class="guide-item">
                        <h4>Estado (Status)</h4>
                        <p><b>Estável:</b> Operando em conformidade. <br><b>Alerta:</b> Necessita atenção preventiva. <br><b>Crítico:</b> Falha técnica ativa com risco de perda de monitoramento.</p>
                    </div>
                </div>
            </div>
            <div class="final-layout">
                <div style="width:300px;"><canvas id="healthChart"></canvas></div>
                <div class="footer-signature">
                    <div class="signature-line"></div>
                    <span style="font-weight:800; font-size:14px;">Maicon Ferreira</span><br>
                    <small style="font-size:11px; color:#64748b;">Engenheiro de Controle e Automação</small>
                    <p style="margin-top:15px; font-size:10px; color:white; background:var(--primary); padding:5px; border-radius:4px;">APROVADO TÉCNICAMENTE</p>
                </div>
            </div>
            <script>
                new Chart(document.getElementById('healthChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Estáveis', 'Alertas', 'Críticos'],
                        datasets: [{{
                            data: [{estaveis}, {alertas}, {criticos}],
                            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{ cutout: '75%', plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11, weight: 'bold' }} }} }} }} }}
                }});
            </script>
        </div>
    </body>
    </html>
    """
    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(html)
    return caminho_final