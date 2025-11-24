from flask import Flask, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:5001')
FRONTEND_TIMEOUT = 1.0  # Frontend only waits 1 second!

# Simple HTML template for visualization
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>E-Commerce Frontend (V1 - Bad)</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 8px; }
        .error { color: red; border: 2px solid red; padding: 10px; background: #ffebee; }
        .success { color: green; }
        .product { border: 1px solid #ddd; margin: 10px 0; padding: 10px; }
        .version { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>E-Commerce Store</h1>
        <p class="version">Frontend Version 1 (Bad - No Resilience)</p>
        <h2>Products</h2>
        {{ content | safe }}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page - fetches products from backend"""
    try:
        # BAD: Just throws exception if backend is slow/unavailable!
        response = requests.get(
            f'{BACKEND_URL}/api/products',
            timeout=FRONTEND_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        products_html = '<div class="success">Successfully loaded products from backend!</div>'
        
        for product in data['products']:
            products_html += f'''
            <div class="product">
                <strong>{product['name']}</strong> - ${product['price']}
            </div>
            '''
        
        return render_template_string(HTML_TEMPLATE, content=products_html)
    
    except requests.exceptions.Timeout:
        # BAD: Just shows error to user!
        error_html = '''
        <div class="error">
            <h3>❌ ERROR: Backend timeout!</h3>
            <p>Backend took too long to respond (> 1 second)</p>
            <p>Complete failure - no products displayed.</p>
        </div>
        '''
        return render_template_string(HTML_TEMPLATE, content=error_html), 503
    
    except requests.exceptions.RequestException as e:
        # BAD: Just shows error to user!
        error_html = f'''
        <div class="error">
            <h3>❌ ERROR: Backend unavailable!</h3>
            <p>Cannot connect to backend service.</p>
            <p>Error: {str(e)}</p>
            <p>Complete failure - no products displayed.</p>
        </div>
        '''
        return render_template_string(HTML_TEMPLATE, content=error_html), 503

@app.route('/health')
def health():
    """Health check - but doesn't verify backend connectivity"""
    return jsonify({'status': 'healthy', 'service': 'frontend-v1'}), 200

if __name__ == '__main__':
    with open('frontend.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    port = int(os.environ.get('FRONTEND_PORT', '5000'))
    print(f"[FRONTEND V1] Starting on port {port}")
    print(f"[FRONTEND V1] Backend URL: {BACKEND_URL}")
    print(f"[FRONTEND V1] Timeout: {FRONTEND_TIMEOUT}s")
    print("[FRONTEND V1] ⚠️  WARNING: No resilience patterns implemented!")
    app.run(host='127.0.0.1', port=port, debug=False)
