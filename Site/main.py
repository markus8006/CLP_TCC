import json
from flask import Flask, render_template, jsonify
from collections import deque


app = Flask(__name__)

def carregar_clps():
    with open("../clp/logs/dados.json", "r", encoding = "utf-8") as f:
        dados = json.load(f)

    #alterar json colocando "ip" e "portas"
    clps = []
    for ip, portas in dados.items():
        clps.append({"ip": ip, "portas": portas})
    return clps

@app.route('/')
def index():
    clps = carregar_clps()
    return render_template('index.html', clps = clps)

@app.route('/clp/<ip>')
def detalhes_clps(ip):
    clps = carregar_clps()
    clp = next((c for c in clps if c["ip"] == ip), None)
    if clp is None:
        return "CLP não encontrado", 404

    
    portas_abertas = [porta for porta in clp["portas"]]
    
    return render_template("detalhes.html", ip=clp["ip"], portas_abertas=portas_abertas)

if __name__ == '__main__':
    # Para abrir no navegador local
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader = True)