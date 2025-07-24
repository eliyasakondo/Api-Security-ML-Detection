"""
Real-time Security Dashboard
Simple HTML dashboard to monitor API security in real-time
"""

from flask import Flask, render_template_string, jsonify, request
import json
import time
from datetime import datetime
import threading
import requests
from collections import defaultdict, deque

class SecurityDashboard:
    """Security monitoring dashboard"""
    
    def __init__(self):
        self.threat_log = deque(maxlen=100)  # Keep last 100 threats
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'sql_injection_attempts': 0,
            'xss_attempts': 0,
            'brute_force_attempts': 0,
            'scanner_attempts': 0,
            'rate_limit_hits': 0
        }
        self.recent_threats = []
        self.timeline_data = deque(maxlen=50)  # Last 50 data points
    
    def log_threat(self, threat_type, ip, description, severity="Medium"):
        """Log a security threat"""
        threat = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': threat_type,
            'ip': ip,
            'description': description,
            'severity': severity
        }
        self.threat_log.append(threat)
        self.recent_threats = list(self.threat_log)[-10:]  # Last 10 threats
        
        # Update stats
        if threat_type == 'SQL Injection':
            self.stats['sql_injection_attempts'] += 1
        elif threat_type == 'XSS':
            self.stats['xss_attempts'] += 1
        elif threat_type == 'Brute Force':
            self.stats['brute_force_attempts'] += 1
        elif threat_type == 'Scanner':
            self.stats['scanner_attempts'] += 1
        elif threat_type == 'Rate Limit':
            self.stats['rate_limit_hits'] += 1
        
        self.stats['blocked_requests'] += 1
    
    def update_timeline(self):
        """Update timeline data"""
        current_time = time.time()
        self.timeline_data.append({
            'timestamp': current_time,
            'total_requests': self.stats['total_requests'],
            'blocked_requests': self.stats['blocked_requests']
        })
    
    def get_dashboard_data(self):
        """Get all dashboard data"""
        return {
            'stats': self.stats,
            'recent_threats': self.recent_threats,
            'timeline': list(self.timeline_data),
            'threat_distribution': {
                'SQL Injection': self.stats['sql_injection_attempts'],
                'XSS': self.stats['xss_attempts'],
                'Brute Force': self.stats['brute_force_attempts'],
                'Scanner': self.stats['scanner_attempts'],
                'Rate Limit': self.stats['rate_limit_hits']
            }
        }

# Global dashboard instance
dashboard = SecurityDashboard()

def create_dashboard_app():
    """Create Flask app for security dashboard"""
    app = Flask(__name__)
    
    # HTML template for the dashboard
    DASHBOARD_HTML = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛡️ API Security Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(45deg, #2c3e50, #34495e);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 20px;
                background: #f8f9fa;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.3s;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
            .stat-card h3 {
                margin: 0 0 10px 0;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .stat-card .number {
                font-size: 2.5em;
                font-weight: bold;
                margin: 0;
            }
            .total { color: #3498db; }
            .blocked { color: #e74c3c; }
            .sql { color: #f39c12; }
            .xss { color: #9b59b6; }
            .brute { color: #e67e22; }
            .scanner { color: #1abc9c; }
            .rate { color: #c0392b; }
            
            .charts-section {
                padding: 20px;
            }
            .charts-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .chart-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .threats-section {
                padding: 20px;
                background: #f8f9fa;
            }
            .threats-table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .threats-table th {
                background: #34495e;
                color: white;
                padding: 15px;
                text-align: left;
            }
            .threats-table td {
                padding: 12px 15px;
                border-bottom: 1px solid #ecf0f1;
            }
            .threats-table tr:hover {
                background: #f8f9fa;
            }
            .severity-high { color: #e74c3c; font-weight: bold; }
            .severity-medium { color: #f39c12; font-weight: bold; }
            .severity-low { color: #27ae60; font-weight: bold; }
            
            /* New threat highlighting */
            .new-threat {
                animation: highlightNew 3s ease-in-out;
                background: #fff3cd !important;
            }
            
            @keyframes highlightNew {
                0% { background: #d1ecf1 !important; }
                50% { background: #b8e6f0 !important; }
                100% { background: #fff3cd !important; }
            }
            
            /* Silent notification bar */
            .notification-bar {
                position: fixed;
                top: 0;
                right: 20px;
                background: #2c3e50;
                color: white;
                padding: 10px 20px;
                border-radius: 0 0 10px 10px;
                font-size: 14px;
                opacity: 0;
                transition: opacity 0.3s ease;
                z-index: 1000;
            }
            
            .notification-bar.show {
                opacity: 1;
            }
            .severity-medium { color: #f39c12; font-weight: bold; }
            .severity-low { color: #27ae60; font-weight: bold; }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 10px;
            }
            .status-active { background: #27ae60; }
            .auto-refresh {
                text-align: center;
                padding: 10px;
                background: #ecf0f1;
                font-size: 0.9em;
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <!-- Silent notification bar -->
        <div id="notification-bar" class="notification-bar">
            <span id="notification-text"></span>
        </div>
        
        <div class="container">
            <div class="header">
                <h1>🛡️ API Security Dashboard</h1>
                <p><span class="status-indicator status-active"></span>Real-time Threat Monitoring Active</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3 class="total">Total Requests</h3>
                    <p class="number total" id="total-requests">0</p>
                </div>
                <div class="stat-card">
                    <h3 class="blocked">Blocked Requests</h3>
                    <p class="number blocked" id="blocked-requests">0</p>
                </div>
                <div class="stat-card">
                    <h3 class="sql">SQL Injection</h3>
                    <p class="number sql" id="sql-attempts">0</p>
                </div>
                <div class="stat-card">
                    <h3 class="xss">XSS Attempts</h3>
                    <p class="number xss" id="xss-attempts">0</p>
                </div>
                <div class="stat-card">
                    <h3 class="brute">Brute Force</h3>
                    <p class="number brute" id="brute-attempts">0</p>
                </div>
                <div class="stat-card">
                    <h3 class="scanner">Scanner Probes</h3>
                    <p class="number scanner" id="scanner-attempts">0</p>
                </div>
                <div class="stat-card">
                    <h3 class="rate">Rate Limits</h3>
                    <p class="number rate" id="rate-hits">0</p>
                </div>
            </div>
            
            <div class="charts-section">
                <div class="charts-grid">
                    <div class="chart-container">
                        <div id="timeline-chart"></div>
                    </div>
                    <div class="chart-container">
                        <div id="threat-distribution"></div>
                    </div>
                </div>
            </div>
            
            <div class="threats-section">
                <h2>🚨 Recent Security Events</h2>
                <table class="threats-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Type</th>
                            <th>IP Address</th>
                            <th>Severity</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody id="threats-tbody">
                        <tr>
                            <td colspan="5" style="text-align: center; color: #7f8c8d;">No threats detected yet...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="auto-refresh">
                🔄 Auto-refreshing every 3 seconds | Last updated: <span id="last-updated">Never</span>
            </div>
        </div>
        
        <script>
            // Disable any browser notifications or alerts
            window.alert = function() { return false; };
            window.confirm = function() { return false; };
            if (window.Notification) {
                window.Notification.requestPermission = function() { return Promise.resolve('denied'); };
            }
            
            // Suppress console errors that might trigger popups
            window.onerror = function() { return true; };
            
            // Track previous values for silent notifications
            let previousStats = {
                sql_injection_attempts: 0,
                xss_attempts: 0,
                brute_force_attempts: 0,
                scanner_attempts: 0,
                rate_limit_hits: 0
            };
            
            function showSilentNotification(message) {
                const notificationBar = document.getElementById('notification-bar');
                const notificationText = document.getElementById('notification-text');
                
                notificationText.textContent = message;
                notificationBar.classList.add('show');
                
                setTimeout(() => {
                    notificationBar.classList.remove('show');
                }, 2000);
            }
            
            // Auto-refresh dashboard data
            function updateDashboard() {
                fetch('/api/dashboard/data')
                    .then(response => response.json())
                    .then(data => {
                        // Check for new threats (silent notifications)
                        if (data.stats.sql_injection_attempts > previousStats.sql_injection_attempts) {
                            showSilentNotification('🚨 SQL Injection detected');
                        }
                        if (data.stats.xss_attempts > previousStats.xss_attempts) {
                            showSilentNotification('🚨 XSS Attack detected');
                        }
                        if (data.stats.brute_force_attempts > previousStats.brute_force_attempts) {
                            showSilentNotification('🚨 Brute Force attempt detected');
                        }
                        if (data.stats.scanner_attempts > previousStats.scanner_attempts) {
                            showSilentNotification('🚨 Scanner probe detected');
                        }
                        if (data.stats.rate_limit_hits > previousStats.rate_limit_hits) {
                            showSilentNotification('⚠️ Rate limit exceeded');
                        }
                        
                        // Update previous stats
                        previousStats = { ...data.stats };
                        
                        // Update statistics
                        document.getElementById('total-requests').textContent = data.stats.total_requests;
                        document.getElementById('blocked-requests').textContent = data.stats.blocked_requests;
                        document.getElementById('sql-attempts').textContent = data.stats.sql_injection_attempts;
                        document.getElementById('xss-attempts').textContent = data.stats.xss_attempts;
                        document.getElementById('brute-attempts').textContent = data.stats.brute_force_attempts;
                        document.getElementById('scanner-attempts').textContent = data.stats.scanner_attempts;
                        document.getElementById('rate-hits').textContent = data.stats.rate_limit_hits;
                        
                        // Update timeline chart
                        updateTimelineChart(data.timeline);
                        
                        // Update threat distribution
                        updateThreatDistribution(data.threat_distribution);
                        
                        // Update threats table
                        updateThreatsTable(data.recent_threats);
                        
                        // Update timestamp
                        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                    })
                    .catch(error => {
                        // Silent error handling - no alerts or console logs
                        document.getElementById('last-updated').textContent = 'Connection lost...';
                    });
            }
            
            function updateTimelineChart(timelineData) {
                const timestamps = timelineData.map(d => new Date(d.timestamp * 1000));
                const totalRequests = timelineData.map(d => d.total_requests);
                const blockedRequests = timelineData.map(d => d.blocked_requests);
                
                const trace1 = {
                    x: timestamps,
                    y: totalRequests,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Total Requests',
                    line: { color: '#3498db' }
                };
                
                const trace2 = {
                    x: timestamps,
                    y: blockedRequests,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Blocked Requests',
                    line: { color: '#e74c3c' }
                };
                
                const layout = {
                    title: 'Request Timeline',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Requests' }
                };
                
                Plotly.newPlot('timeline-chart', [trace1, trace2], layout);
            }
            
            function updateThreatDistribution(distribution) {
                const labels = Object.keys(distribution);
                const values = Object.values(distribution);
                
                const data = [{
                    labels: labels,
                    values: values,
                    type: 'pie',
                    marker: {
                        colors: ['#f39c12', '#9b59b6', '#e67e22', '#1abc9c', '#c0392b']
                    }
                }];
                
                const layout = {
                    title: 'Threat Distribution'
                };
                
                Plotly.newPlot('threat-distribution', data, layout);
            }
            
            function updateThreatsTable(threats) {
                const tbody = document.getElementById('threats-tbody');
                
                if (threats.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #7f8c8d;">No threats detected yet...</td></tr>';
                    return;
                }
                
                tbody.innerHTML = threats.map(threat => `
                    <tr>
                        <td>${threat.timestamp}</td>
                        <td>${threat.type}</td>
                        <td>${threat.ip}</td>
                        <td class="severity-${threat.severity.toLowerCase()}">${threat.severity}</td>
                        <td>${threat.description}</td>
                    </tr>
                `).join('');
            }
            
            // Initial load and setup auto-refresh
            updateDashboard();
            setInterval(updateDashboard, 3000); // Refresh every 3 seconds
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def dashboard():
        """Main dashboard page"""
        return render_template_string(DASHBOARD_HTML)
    
    @app.route('/api/dashboard/data')
    def dashboard_data():
        """API endpoint for dashboard data"""
        global dashboard
        return jsonify(dashboard.get_dashboard_data())
    
    @app.route('/api/dashboard/threat', methods=['POST'])
    def log_threat():
        """API endpoint to log a threat"""
        global dashboard
        data = request.get_json()
        dashboard.log_threat(
            data.get('type', 'Unknown'),
            data.get('ip', 'Unknown'),
            data.get('description', 'No description'),
            data.get('severity', 'Medium')
        )
        return jsonify({'status': 'logged'})
    
    @app.route('/api/dashboard/stats', methods=['POST'])
    def update_stats():
        """API endpoint to update stats"""
        global dashboard
        data = request.get_json()
        if 'total_requests' in data:
            dashboard.stats['total_requests'] = data['total_requests']
        if 'blocked_requests' in data:
            dashboard.stats['blocked_requests'] = data['blocked_requests']
        return jsonify({'status': 'updated'})
    
    return app

if __name__ == '__main__':
    print("🛡️ Starting Security Dashboard...")
    print("📊 Dashboard: http://localhost:8080")
    print("🔗 API Data: http://localhost:8080/api/dashboard/data")
    print("\nPress Ctrl+C to stop\n")
    
    app = create_dashboard_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
