"""
Attack Simulation Script
Simulate various attack scenarios to test the security system
"""

import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
import json

class AttackSimulator:
    """Simulate various types of attacks against the API"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def sql_injection_attacks(self, num_attacks=10):
        """Simulate SQL injection attacks"""
        print(f"Simulating {num_attacks} SQL injection attacks...")
        
        sql_payloads = [
            "1' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM information_schema.tables --",
            "admin'--",
            "1' OR 1=1#",
            "' OR 'a'='a",
            "1'; DELETE FROM users WHERE 't'='t",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
            "' UNION SELECT username, password FROM admin --",
            "1' OR SLEEP(5) --"
        ]
        
        for i in range(num_attacks):
            payload = random.choice(sql_payloads)
            
            # Try different attack vectors
            attack_vectors = [
                {'url': f"{self.base_url}/api/users", 'params': {'id': payload}},
                {'url': f"{self.base_url}/api/data", 'json': {'query': payload}},
                {'url': f"{self.base_url}/api/login", 'json': {'username': payload, 'password': 'test'}}
            ]
            
            vector = random.choice(attack_vectors)
            
            try:
                if 'params' in vector:
                    response = self.session.get(vector['url'], params=vector['params'])
                else:
                    response = self.session.post(vector['url'], json=vector['json'])
                
                print(f"SQL Injection {i+1}: {response.status_code} - {payload[:30]}...")
                
            except Exception as e:
                print(f"Error in SQL injection attack {i+1}: {e}")
            
            time.sleep(0.1)  # Small delay between attacks
    
    def xss_attacks(self, num_attacks=10):
        """Simulate XSS attacks"""
        print(f"Simulating {num_attacks} XSS attacks...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('XSS')",
            "<svg onload=alert(1)>",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "<script>document.cookie='stolen'</script>",
            "';alert(String.fromCharCode(88,83,83))//';",
            "<script>window.location='http://evil.com'</script>",
            "<object data='javascript:alert(1)'>"
        ]
        
        for i in range(num_attacks):
            payload = random.choice(xss_payloads)
            
            attack_data = {
                'name': payload,
                'message': f"Normal message with {payload}",
                'comment': payload
            }
            
            try:
                response = self.session.post(f"{self.base_url}/api/data", json=attack_data)
                print(f"XSS Attack {i+1}: {response.status_code} - {payload[:30]}...")
                
            except Exception as e:
                print(f"Error in XSS attack {i+1}: {e}")
            
            time.sleep(0.1)
    
    def dos_attacks(self, num_threads=10, requests_per_thread=20):
        """Simulate DoS attacks with high request rate"""
        print(f"Simulating DoS attack: {num_threads} threads, {requests_per_thread} requests each...")
        
        def dos_worker():
            """Worker function for DoS attack"""
            for i in range(requests_per_thread):
                try:
                    # Mix of different endpoints
                    endpoints = ['/api/health', '/api/users', '/api/data']
                    endpoint = random.choice(endpoints)
                    
                    if endpoint == '/api/data':
                        response = self.session.post(
                            f"{self.base_url}{endpoint}",
                            json={'data': f'dos_test_{i}'}
                        )
                    else:
                        response = self.session.get(f"{self.base_url}{endpoint}")
                    
                    if i % 10 == 0:
                        print(f"DoS request: {response.status_code}")
                        
                except Exception as e:
                    print(f"DoS request failed: {e}")
        
        # Launch threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(dos_worker) for _ in range(num_threads)]
            
            # Wait for completion
            for future in futures:
                future.result()
    
    def brute_force_login(self, num_attempts=20):
        """Simulate brute force login attacks"""
        print(f"Simulating {num_attempts} brute force login attempts...")
        
        usernames = ['admin', 'user', 'root', 'administrator', 'test']
        passwords = ['password', '123456', 'admin', 'qwerty', 'password123', 'letmein']
        
        for i in range(num_attempts):
            username = random.choice(usernames)
            password = random.choice(passwords)
            
            login_data = {
                'username': username,
                'password': password
            }
            
            try:
                response = self.session.post(f"{self.base_url}/api/login", json=login_data)
                print(f"Login attempt {i+1}: {response.status_code} - {username}:{password}")
                
            except Exception as e:
                print(f"Error in login attempt {i+1}: {e}")
            
            time.sleep(0.2)
    
    def scanner_simulation(self, num_scans=15):
        """Simulate vulnerability scanner behavior"""
        print(f"Simulating vulnerability scanner with {num_scans} scans...")
        
        scan_paths = [
            '/admin',
            '/admin.php',
            '/wp-admin',
            '/phpmyadmin',
            '/config.php',
            '/backup.sql',
            '/test.php',
            '/.env',
            '/robots.txt',
            '/sitemap.xml',
            '/api/admin',
            '/api/config',
            '/api/debug',
            '/api/../../../etc/passwd',
            '/api/users/../../admin'
        ]
        
        for i in range(num_scans):
            path = random.choice(scan_paths)
            
            try:
                response = self.session.get(f"{self.base_url}{path}")
                print(f"Scanner probe {i+1}: {response.status_code} - {path}")
                
            except Exception as e:
                print(f"Error in scanner probe {i+1}: {e}")
            
            time.sleep(0.1)
    
    def mixed_attack_simulation(self, duration_seconds=60):
        """Run mixed attacks for a specified duration"""
        print(f"Running mixed attack simulation for {duration_seconds} seconds...")
        
        start_time = time.time()
        attack_count = 0
        
        while time.time() - start_time < duration_seconds:
            attack_type = random.choice([
                'sql_injection', 'xss', 'brute_force', 'scanner'
            ])
            
            try:
                if attack_type == 'sql_injection':
                    self.sql_injection_attacks(1)
                elif attack_type == 'xss':
                    self.xss_attacks(1)
                elif attack_type == 'brute_force':
                    self.brute_force_login(1)
                elif attack_type == 'scanner':
                    self.scanner_simulation(1)
                
                attack_count += 1
                
            except Exception as e:
                print(f"Error in {attack_type} attack: {e}")
            
            time.sleep(random.uniform(0.1, 0.5))
        
        print(f"Mixed attack simulation completed. Total attacks: {attack_count}")
    
    def legitimate_traffic(self, num_requests=50):
        """Generate legitimate traffic to contrast with attacks"""
        print(f"Generating {num_requests} legitimate requests...")
        
        for i in range(num_requests):
            try:
                # Mix of legitimate requests
                if i % 4 == 0:
                    response = self.session.get(f"{self.base_url}/api/health")
                elif i % 4 == 1:
                    response = self.session.get(f"{self.base_url}/api/users")
                elif i % 4 == 2:
                    legitimate_data = {
                        'name': f'User{i}',
                        'email': f'user{i}@example.com',
                        'message': f'This is a legitimate message {i}'
                    }
                    response = self.session.post(f"{self.base_url}/api/data", json=legitimate_data)
                else:
                    login_data = {'username': 'admin', 'password': 'secure123'}
                    response = self.session.post(f"{self.base_url}/api/login", json=login_data)
                
                if i % 10 == 0:
                    print(f"Legitimate request {i+1}: {response.status_code}")
                
            except Exception as e:
                print(f"Error in legitimate request {i+1}: {e}")
            
            time.sleep(random.uniform(0.2, 1.0))

def main():
    """Main function to run attack simulations"""
    print("API Security Attack Simulator")
    print("=" * 40)
    
    simulator = AttackSimulator()
    
    # Check if API is running
    try:
        response = simulator.session.get(f"{simulator.base_url}/health")
        if response.status_code != 200:
            print("API is not running. Please start the application first.")
            return
    except Exception:
        print("Cannot connect to API. Please start the application first.")
        return
    
    print("API is running. Starting attack simulation...\\n")
    
    # Run different types of attacks
    simulator.legitimate_traffic(20)
    print()
    
    simulator.sql_injection_attacks(15)
    print()
    
    simulator.xss_attacks(15)
    print()
    
    simulator.brute_force_login(10)
    print()
    
    simulator.scanner_simulation(10)
    print()
    
    # Run DoS attack (be careful with this)
    print("Starting DoS simulation (5 threads)...")
    simulator.dos_attacks(num_threads=5, requests_per_thread=10)
    print()
    
    # Mixed attack pattern
    simulator.mixed_attack_simulation(30)
    
    print("\\nAttack simulation completed!")
    print("Check the security dashboard for detection results.")

if __name__ == "__main__":
    main()
