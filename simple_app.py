"""
Simple API Security System for Testing
Lightweight version for demonstration and testing with dashboard integration
"""

from flask import Flask, request, jsonify
import time
import re
import logging
import requests
import threading
from collections import defaultdict, deque

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSecurityManager:
    """Simplified security manager for testing"""
    
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.sql_injection_count = 0
        self.xss_count = 0
        self.brute_force_count = 0
        self.rate_limit_storage = defaultdict(deque)
        self.start_time = time.time()
        self.dashboard_url = "http://localhost:8080"
        
        # Enhanced SQL injection patterns
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\')(.*?)(\-\-|\#)",
            r"(\-\-|\#|\/\*|\*\/)",
            r"(\bSLEEP\s*\()",
            r"(\bCOUNT\s*\()",
            r"(\bFROM\s+\w+)",
            r"(\bWHERE\s+\w+\s*=)",
            r"(\bDELETE\s+FROM)",
            r"(\bDROP\s+TABLE)",
        ]
        
        # Enhanced XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"<svg[^>]*>",
            r"<body[^>]*onload",
            r"<img[^>]*onerror",
            r"alert\s*\(",
            r"eval\s*\(",
            r"document\.cookie",
        ]
        
        self.compiled_sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.sql_patterns]
        self.compiled_xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.xss_patterns]
    
    def log_to_dashboard(self, threat_type, ip, description, severity="Medium"):
        """Log threat to dashboard asynchronously"""
        def send_log():
            try:
                response = requests.post(f"{self.dashboard_url}/api/dashboard/threat", 
                            json={
                                'type': threat_type,
                                'ip': ip,
                                'description': description,
                                'severity': severity
                            }, timeout=1)
                print(f"🚨 Logged threat to dashboard: {threat_type} - {response.status_code}")
            except Exception as e:
                print(f"❌ Failed to log to dashboard: {e}")
        
        threading.Thread(target=send_log, daemon=True).start()
    
    def update_dashboard_stats(self):
        """Update total request count in dashboard"""
        def send_update():
            try:
                requests.post(f"{self.dashboard_url}/api/dashboard/stats", 
                            json={
                                'total_requests': self.total_requests,
                                'blocked_requests': self.blocked_requests
                            }, timeout=1)
            except:
                pass  # Silently fail if dashboard is not available
        
        threading.Thread(target=send_update, daemon=True).start()
    
    def detect_sql_injection(self, text, ip="Unknown"):
        """Simple SQL injection detection"""
        if not text:
            return False
        
        for pattern in self.compiled_sql_patterns:
            if pattern.search(str(text)):
                self.sql_injection_count += 1
                self.blocked_requests += 1
                # Log to dashboard
                self.log_to_dashboard(
                    "SQL Injection", 
                    ip, 
                    f"Detected pattern: {str(text)[:50]}...",
                    "High"
                )
                return True
        return False
    
    def detect_xss(self, text, ip="Unknown"):
        """Simple XSS detection"""
        if not text:
            return False
        
        for pattern in self.compiled_xss_patterns:
            if pattern.search(str(text)):
                self.xss_count += 1
                self.blocked_requests += 1
                # Log to dashboard
                self.log_to_dashboard(
                    "XSS", 
                    ip, 
                    f"Detected XSS: {str(text)[:50]}...",
                    "High"
                )
                return True
        return False
    
    def check_rate_limit(self, ip_address):
        """Simple rate limiting"""
        current_time = time.time()
        requests = self.rate_limit_storage[ip_address]
        
        # Clean old requests
        while requests and current_time - requests[0] > 60:
            requests.popleft()
        
        # Check limit
        if len(requests) >= 100:  # 100 requests per minute
            # Log to dashboard
            self.log_to_dashboard(
                "Rate Limit", 
                ip_address, 
                f"Exceeded 100 requests per minute",
                "Medium"
            )
            return False
        
        requests.append(current_time)
        return True
    
    def check_request_security(self, request_data, ip="Unknown"):
        """Check request for security threats - enhanced version"""
        def check_value(value):
            """Recursively check a value for threats"""
            if isinstance(value, dict):
                for k, v in value.items():
                    if not check_value(v):
                        return False
            elif isinstance(value, list):
                for item in value:
                    if not check_value(item):
                        return False
            elif value is not None:
                value_str = str(value).lower()
                if self.detect_sql_injection(value_str, ip):
                    return False
                if self.detect_xss(value_str, ip):
                    return False
            return True
        
        if not check_value(request_data):
            return False, "Malicious content detected"
        
        return True, "OK"

def create_simple_app():
    """Create a simple Flask app for testing"""
    app = Flask(__name__)
    security_manager = SimpleSecurityManager()
    
    @app.before_request
    def before_request():
        security_manager.total_requests += 1
        security_manager.update_dashboard_stats()
        
        # Rate limiting
        if not security_manager.check_rate_limit(request.remote_addr):
            return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.after_request
    def after_request(response):
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    @app.route('/')
    def index():
        """Main page"""
        return {
            'status': 'running',
            'message': 'API Security System Active',
            'security_level': 'medium',
            'version': '1.0.0'
        }
    
    @app.route('/health')
    def health():
        """Health check"""
        return {
            'status': 'healthy',
            'uptime': time.time() - security_manager.start_time,
            'total_requests': security_manager.total_requests,
            'blocked_requests': security_manager.blocked_requests
        }
    
    @app.route('/api/health')
    def api_health():
        """API health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0'
        })
    
    @app.route('/api/data', methods=['POST'])
    def submit_data():
        """Submit data with security checks"""
        try:
            data = request.get_json() or {}
            
            # Security check
            is_safe, message = security_manager.check_request_security(data, request.remote_addr)
            
            if not is_safe:
                logger.warning(f"Blocked request from {request.remote_addr}: {message}")
                return jsonify({'error': 'Malicious request detected'}), 400
            
            # Process data
            result = {
                'message': 'Data processed successfully',
                'id': int(time.time()),
                'processed_at': time.time()
            }
            
            logger.info(f"Data processed from {request.remote_addr}")
            return jsonify(result), 201
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/users', methods=['GET'])
    def get_users():
        """Get users list"""
        users = [
            {'id': 1, 'username': 'admin', 'role': 'administrator'},
            {'id': 2, 'username': 'user1', 'role': 'user'},
            {'id': 3, 'username': 'user2', 'role': 'user'}
        ]
        return jsonify({'users': users})
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """User login"""
        try:
            data = request.get_json() or {}
            username = data.get('username', '')
            password = data.get('password', '')
            
            # Security check on login data
            is_safe, message = security_manager.check_request_security(data, request.remote_addr)
            if not is_safe:
                return jsonify({'error': 'Malicious request detected'}), 400
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            # Simple authentication
            if username == 'admin' and password == 'secure123':
                return jsonify({
                    'message': 'Login successful',
                    'token': f"token_{int(time.time())}",
                    'expires': time.time() + 3600
                })
            else:
                # Log brute force attempt
                security_manager.brute_force_count += 1
                security_manager.log_to_dashboard(
                    "Brute Force", 
                    request.remote_addr, 
                    f"Failed login attempt: {username}",
                    "Medium"
                )
                return jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/security/stats')
    def security_stats():
        """Security statistics"""
        return jsonify({
            'total_requests': security_manager.total_requests,
            'blocked_requests': security_manager.blocked_requests,
            'sql_injection_attempts': security_manager.sql_injection_count,
            'xss_attempts': security_manager.xss_count,
            'brute_force_attempts': security_manager.brute_force_count,
            'anomaly_detections': 0,  # Placeholder
            'uptime': time.time() - security_manager.start_time
        })
    
    return app

if __name__ == '__main__':
    print("🛡️  Starting Simple API Security System")
    print("=" * 50)
    print("📋 Health check: http://localhost:5000/health")
    print("🔗 API endpoints: http://localhost:5000/api/")
    print("🧪 Run 'python attack_simulator.py' in another terminal to test")
    print("\nPress Ctrl+C to stop\n")
    
    app = create_simple_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
