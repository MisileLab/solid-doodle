"""
SafeKnob Web Interface
Web dashboard for monitoring door safety status
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import time
from datetime import datetime

app = FastAPI(title="SafeKnob Dashboard", description="Door Safety Monitoring System")

LOG_FILE = "safeknob_log.json"

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SafeKnob Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #ff6b6b, #ee5a24);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .header p {
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.1em;
            }
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                padding: 30px;
            }
            .status-card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .status-card:hover {
                transform: translateY(-5px);
            }
            .status-indicator {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }
            .status-dot {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 15px;
                animation: pulse 2s infinite;
            }
            .safe { background-color: #2ecc71; }
            .warning { background-color: #f39c12; }
            .danger { background-color: #e74c3c; }
            @keyframes pulse {
                0% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.1); }
                100% { opacity: 1; transform: scale(1); }
            }
            .metric {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 5px;
                border-left: 4px solid #3498db;
            }
            .metric-label {
                font-weight: 600;
                color: #34495e;
            }
            .metric-value {
                font-weight: bold;
                color: #2c3e50;
            }
            .log-section {
                padding: 30px;
                background: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
            .log-entry {
                background: white;
                margin: 10px 0;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #3498db;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .log-entry.warning { border-left-color: #f39c12; }
            .log-entry.danger { border-left-color: #e74c3c; }
            .refresh-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                margin: 20px 0;
                transition: background 0.3s ease;
            }
            .refresh-btn:hover {
                background: #2980b9;
            }
            .timestamp {
                color: #7f8c8d;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔥 SafeKnob Dashboard</h1>
                <p>실시간 문 손잡이 안전 모니터링 시스템</p>
            </div>
            
            <div id="status-content">
                <div class="status-grid">
                    <div class="status-card">
                        <div class="status-indicator">
                            <div class="status-dot safe" id="status-dot"></div>
                            <h3 id="status-text">시스템 로딩 중...</h3>
                        </div>
                        <div class="metric">
                            <span class="metric-label">온도</span>
                            <span class="metric-value" id="temperature">--°C</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">조도</span>
                            <span class="metric-value" id="light-level">--</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">마지막 업데이트</span>
                            <span class="metric-value" id="last-update">--</span>
                        </div>
                    </div>
                    
                    <div class="status-card">
                        <h3>🛡️ 안전 기준</h3>
                        <div class="metric">
                            <span class="metric-label">안전</span>
                            <span class="metric-value" style="color: #2ecc71;">&lt; 30°C</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">주의</span>
                            <span class="metric-value" style="color: #f39c12;">45-55°C</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">위험</span>
                            <span class="metric-value" style="color: #e74c3c;">&gt; 55°C</span>
                        </div>
                    </div>
                </div>
                
                <button class="refresh-btn" onclick="refreshData()">📊 데이터 새로고침</button>
            </div>
            
            <div class="log-section">
                <h3>📋 최근 로그</h3>
                <div id="log-entries">
                    로그 데이터 로딩 중...
                </div>
            </div>
        </div>

        <script>
            async function fetchStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    // Update status indicator
                    const statusDot = document.getElementById('status-dot');
                    const statusText = document.getElementById('status-text');
                    
                    statusDot.className = 'status-dot ' + data.safety_level;
                    
                    const statusMap = {
                        'safe': '🟢 안전',
                        'warning': '🟡 주의',
                        'danger': '🔴 위험'
                    };
                    statusText.textContent = statusMap[data.safety_level] || '알 수 없음';
                    
                    // Update metrics
                    document.getElementById('temperature').textContent = data.temperature + '°C';
                    document.getElementById('light-level').textContent = data.light_level;
                    document.getElementById('last-update').textContent = data.last_update;
                    
                } catch (error) {
                    console.error('상태 업데이트 실패:', error);
                    document.getElementById('status-text').textContent = '연결 오류';
                }
            }
            
            async function fetchLogs() {
                try {
                    const response = await fetch('/api/logs');
                    const logs = await response.json();
                    
                    const logContainer = document.getElementById('log-entries');
                    
                    if (logs.length === 0) {
                        logContainer.innerHTML = '<p>로그 데이터가 없습니다.</p>';
                        return;
                    }
                    
                    logContainer.innerHTML = logs.slice(-10).reverse().map(log => `
                        <div class="log-entry ${log.safety_level}">
                            <strong>${log.readable_time}</strong> - 
                            온도: ${log.temperature}°C, 조도: ${log.light_level}, 
                            상태: <strong>${log.safety_level.toUpperCase()}</strong>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    console.error('로그 로딩 실패:', error);
                    document.getElementById('log-entries').innerHTML = '<p>로그 로딩 실패</p>';
                }
            }
            
            function refreshData() {
                fetchStatus();
                fetchLogs();
            }
            
            // Auto refresh every 5 seconds
            setInterval(refreshData, 5000);
            
            // Initial load
            refreshData();
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/status")
async def get_status():
    """Get current safety status"""
    try:
        if not os.path.exists(LOG_FILE):
            return {
                "temperature": 0,
                "light_level": 0,
                "safety_level": "safe",
                "last_update": "데이터 없음"
            }
        
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        if not logs:
            return {
                "temperature": 0,
                "light_level": 0,
                "safety_level": "safe", 
                "last_update": "데이터 없음"
            }
        
        latest = logs[-1]
        return {
            "temperature": latest["temperature"],
            "light_level": latest["light_level"],
            "safety_level": latest["safety_level"],
            "last_update": latest["readable_time"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status read error: {e}")

@app.get("/api/logs")
async def get_logs():
    """Get recent logs"""
    try:
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logs read error: {e}")

@app.post("/api/alert/{level}")
async def trigger_alert(level: str):
    """Manually trigger alert for testing"""
    valid_levels = ["safe", "warning", "danger"]
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail="Invalid alert level")
    
    # This would send alert to connected devices
    # For demo purposes, we'll just log it
    print(f"Manual alert triggered: {level}")
    
    return {"message": f"Alert {level} triggered", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("🔥 SafeKnob Web Dashboard Starting...")
    print("Dashboard: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)