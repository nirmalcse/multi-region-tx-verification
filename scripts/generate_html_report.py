import json
from datetime import datetime
from pathlib import Path
from jinja2 import Template


def generate_html_report():
    """Generate HTML report from JSON results"""
    
    try:
        with open("transaction_verification_report.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No report found")
        return
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Multi-Region Transaction Verification Report</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                padding: 40px;
                background: #f8f9fa;
            }
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .metric-card h3 { color: #667eea; font-size: 0.9em; margin-bottom: 10px; }
            .metric-card .value { font-size: 2em; font-weight: bold; color: #333; }
            .metric-card.success { border-left-color: #28a745; }
            .metric-card.success h3 { color: #28a745; }
            .metric-card.danger { border-left-color: #dc3545; }
            .metric-card.danger h3 { color: #dc3545; }
            .results {
                padding: 40px;
            }
            .results h2 { color: #333; margin-bottom: 20px; }
            .region-item {
                background: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
            }
            .region-item.success {
                border-left: 4px solid #28a745;
                background: #f8fdf5;
            }
            .region-item.failed {
                border-left: 4px solid #dc3545;
                background: #fdf8f8;
            }
            .region-name { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }
            .region-status { display: flex; gap: 20px; flex-wrap: wrap; }
            .status-label {
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.9em;
                font-weight: bold;
            }
            .status-label.success { background: #d4edda; color: #155724; }
            .status-label.failed { background: #f8d7da; color: #721c24; }
            footer {
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                border-top: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🔍 Multi-Region Transaction Verification Report</h1>
                <p>Generated: {{ timestamp }}</p>
            </header>
            
            <div class="metrics">
                <div class="metric-card">
                    <h3>Total Duration</h3>
                    <div class="value">{{ duration }}s</div>
                </div>
                <div class="metric-card success">
                    <h3>Successful Verifications</h3>
                    <div class="value">{{ successful }}/{{ total }}</div>
                </div>
                <div class="metric-card {{ 'danger' if failed > 0 else '' }}">
                    <h3>Failed Verifications</h3>
                    <div class="value">{{ failed }}</div>
                </div>
                <div class="metric-card">
                    <h3>Success Rate</h3>
                    <div class="value">{{ success_rate }}%</div>
                </div>
            </div>
            
            <div class="results">
                <h2>Regional Verification Results</h2>
                {% for result in results %}
                <div class="region-item {{ 'success' if result.verified else 'failed' }}">
                    <div class="region-name">{{ result.region }}</div>
                    <div class="region-status">
                        <span class="status-label {{ 'success' if result.verified else 'failed' }}">
                            {{ result.status }}
                        </span>
                        <span>Execution Time: {{ result.execution_time }}s</span>
                        {% if result.transaction_id %}
                        <span>Transaction ID: {{ result.transaction_id }}</span>
                        {% endif %}
                        {% if result.error %}
                        <span style="color: #dc3545;">Error: {{ result.error }}</span>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <footer>
                <p>Automation Report | Generated: {{ timestamp }}</p>
                <p><small>All times in UTC</small></p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # Render template
    template = Template(html_template)
    
    successful = sum(1 for r in data['results'] if r['verified'])
    failed = len(data['results']) - successful
    success_rate = round((successful / len(data['results']) * 100), 1) if data['results'] else 0
    
    html = template.render(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        duration=round(data['total_duration_seconds'], 1),
        successful=successful,
        failed=failed,
        total=len(data['results']),
        success_rate=success_rate,
        results=data['results']
    )
    
    # Save HTML report
    Path("reports").mkdir(exist_ok=True)
    report_path = Path("reports/transaction_verification_report.html")
    report_path.write_text(html)
    print(f"✅ HTML report generated: {report_path}")


if __name__ == "__main__":
    generate_html_report()