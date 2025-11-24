from flask import Flask, jsonify
import time
import sys
import os

app = Flask(__name__)

# Configuration: Can inject delay via environment variable
ARTIFICIAL_DELAY = float(os.environ.get('BACKEND_DELAY', '0'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'backend',
        'delay_configured': f'{ARTIFICIAL_DELAY}s'
    }), 200

@app.route('/api/products')
def get_products():
    """Simulated data API that can be slowed down"""
    # Simulate processing time or chaos-injected delay
    if ARTIFICIAL_DELAY > 0:
        print(f"[BACKEND] Sleeping for {ARTIFICIAL_DELAY} seconds (chaos injection)")
        time.sleep(ARTIFICIAL_DELAY)
    
    products = [
        {"id": 1, "name": "Laptop", "price": 999.99},
        {"id": 2, "name": "Mouse", "price": 29.99},
        {"id": 3, "name": "Keyboard", "price": 79.99},
        {"id": 4, "name": "Monitor", "price": 349.99}
    ]
    
    return jsonify({
        'status': 'success',
        'products': products,
        'source': 'backend-database'
    }), 200

if __name__ == '__main__':
    # Write PID for chaos experiments
    with open('backend.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    port = int(os.environ.get('BACKEND_PORT', '5001'))
    print(f"[BACKEND] Starting on port {port} with delay={ARTIFICIAL_DELAY}s")
    app.run(host='127.0.0.1', port=port, debug=False)
