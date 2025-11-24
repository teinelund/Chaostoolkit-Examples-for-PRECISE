from flask import Flask, jsonify, render_template_string
import requests
import time
import os
from datetime import datetime, timedelta
from enum import Enum

app = Flask(__name__)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:5001')
FRONTEND_TIMEOUT = 1.0

# Circuit Breaker State
class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Backend is down, fail fast
    HALF_OPEN = "half_open"  # Testing if backend recovered

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    def __init__(self, failure_threshold=3, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds to wait before retry
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        # If circuit is OPEN, check if we should try again
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                print("[CIRCUIT BREAKER] Timeout expired, entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - failing fast")
        
        try:
            result = func(*args, **kwargs)
            # Success! Reset failure count
            if self.state == CircuitState.HALF_OPEN:
                print("[CIRCUIT BREAKER] Backend recovered, closing circuit")
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                print(f"[CIRCUIT BREAKER] Threshold reached ({self.failure_count}), opening circuit")
                self.state = CircuitState.OPEN
            
            raise e

# Global circuit breaker instance
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

# Cache for graceful degradation
product_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutes
}

def get_cached_products():
    """Return cached products if available"""
    if product_cache['data'] is None:
        return None
    
    # Check if cache is still valid
    if datetime.now() - product_cache['timestamp'] > timedelta(seconds=product_cache['ttl']):
        return None
    
    return product_cache['data']

def get_fallback_products():
    """Static fallback data when backend is unavailable"""
    return [
        {"id": 0, "name": "Laptop (cached)", "price": 999.99},
        {"id": 0, "name": "Mouse (cached)", "price": 29.99},
        {"id": 0, "name": "Keyboard (cached)", "price": 79.99}
    ]

def fetch_from_backend():
    """Fetch products from backend with timeout"""
    response = requests.get(
        f'{BACKEND_URL}/api/products',
        timeout=FRONTEND_TIMEOUT
    )
    response.raise_for_status()
    data = response.json()
    
    # Update cache on successful fetch
    product_cache['data'] = data['products']
    product_cache['timestamp'] = datetime.now()
    
    return data['products'], 'backend'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>E-Commerce Frontend (V2 - Resilient)</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 8px; }
        .warning { color: orange; border: 2px solid orange; padding: 10px; background: #fff3e0; }
        .success { color: green; border: 2px solid green; padding: 10px; background: #e8f5e9; }
        .info { color: blue; border: 2px solid blue; padding: 10px; background: #e3f2fd; }
        .product { border: 1px solid #ddd; margin: 10px 0; padding: 10px; }
        .version { color: #666; font-style: italic; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .badge-live { background: #4caf50; color: white; }
        .badge-cached { background: #ff9800; color: white; }
        .badge-fallback { background: #2196f3; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>E-Commerce Store</h1>
        <p class="version">Frontend Version 2 (Resilient - With Circuit Breaker & Fallback)</p>
        <h2>Products {{ badge | safe }}</h2>
        {{ message | safe }}
        {{ content | safe }}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with resilient backend calls"""
    products = None
    source = None
    message = ""
    
    # Try to get from backend with circuit breaker protection
    try:
        products, source = circuit_breaker.call(fetch_from_backend)
        message = '<div class="success">✅ Backend is healthy and responding!</div>'
        badge = '<span class="badge badge-live">LIVE DATA</span>'
    
    except Exception as e:
        print(f"[FRONTEND V2] Backend call failed: {e}")
        
        # Try cache first (Resilience Pattern: Caching)
        cached = get_cached_products()
        if cached:
            products = cached
            source = 'cache'
            message = f'''
            <div class="warning">
                ⚠️ Backend is slow or unavailable. Showing cached data from earlier.
                <br>Circuit breaker state: {circuit_breaker.state.value}
            </div>
            '''
            badge = '<span class="badge badge-cached">CACHED DATA</span>'
        else:
            # Use static fallback (Resilience Pattern: Graceful Degradation)
            products = get_fallback_products()
            source = 'fallback'
            message = f'''
            <div class="info">
                ℹ️ Backend is temporarily unavailable. Showing default product catalog.
                <br>Circuit breaker state: {circuit_breaker.state.value}
                <br>Full functionality will resume when backend recovers.
            </div>
            '''
            badge = '<span class="badge badge-fallback">FALLBACK DATA</span>'
    
    # Render products
    products_html = ""
    for product in products:
        products_html += f'''
        <div class="product">
            <strong>{product['name']}</strong> - ${product['price']}
        </div>
        '''
    
    return render_template_string(
        HTML_TEMPLATE,
        content=products_html,
        message=message,
        badge=badge
    )

@app.route('/health')
def health():
    """Enhanced health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'frontend-v2',
        'circuit_breaker_state': circuit_breaker.state.value,
        'circuit_breaker_failures': circuit_breaker.failure_count
    }), 200

@app.route('/circuit-breaker/status')
def circuit_status():
    """Debug endpoint to check circuit breaker state"""
    return jsonify({
        'state': circuit_breaker.state.value,
        'failure_count': circuit_breaker.failure_count,
        'last_failure': circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None
    })

if __name__ == '__main__':
    with open('frontend.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    port = int(os.environ.get('FRONTEND_PORT', '5000'))
    print(f"[FRONTEND V2] Starting on port {port}")
    print(f"[FRONTEND V2] Backend URL: {BACKEND_URL}")
    print(f"[FRONTEND V2] Timeout: {FRONTEND_TIMEOUT}s")
    print("[FRONTEND V2] ✅ Resilience patterns enabled:")
    print("  - Circuit Breaker (fail fast after 3 failures)")
    print("  - Caching (5 minute TTL)")
    print("  - Graceful Degradation (static fallback)")
    app.run(host='127.0.0.1', port=port, debug=False)
