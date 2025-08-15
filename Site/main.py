from flask import Flask, render_template, jsonify

app = Flask(__name__)

def carregar_clps():
    with open("dados.json", "r", encoding = "utf-8") as f:
        return json.load(f)
    clps = []
    for ip, portas in dados.items():
        clps.append({"ip": ip, "portas": portas})
    return clps
    
@app.route('/')
def index():
    clps = carregar_clps()
    return render_template('index.html', clps = clps)

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