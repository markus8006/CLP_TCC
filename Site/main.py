from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    clps_detectados = [
        {"ip": "192.168.0.10", "portas": [502, 80]},
        {"ip": "192.168.0.11", "portas": [502]},
    ]
    return render_template('index.html', clps = clps_detectados)

@app.route('/dados_clps')
def dados_clps():
    clps_detectados = [
        {"ip": "192.168.0.10"},
        {"ip": "192.168.0.11"}
    ]
    return jsonify(clps_detectados)

if __name__ == '__main__':
    # Para abrir no navegador local
    app.run(host='127.0.0.1', port=5000, debug=True)