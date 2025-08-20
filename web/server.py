import os
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from threading import Thread
from utils import log 
from configs import settings


app = Flask(__name__)




BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

caminho_app = os.path.join(BASE_DIR, "logs\\app.log")
caminho_coleta = os.path.join(BASE_DIR, "logs\\coleta.log")

def carregar_clps(rota : str = "logs\\dados.json") -> list:
    """
    Coleta IPs e Portas abertas do Json\n
    rota (str) : rota dos dados.json
    """
    caminho = os.path.join(BASE_DIR, rota)
    with open(caminho, "r", encoding = "utf-8") as f:
        dados = json.load(f)

    #alterar json colocando "ip" e "portas"
    clps = []
    for ip, portas in dados.items():
        clps.append({"ip": ip, "portas": portas})
    return clps


@app.route('/')
def index():
    clps = carregar_clps()

    #Numeração de páginas
    page = request.args.get('page', 1, type=int)

    inicio = (page - 1) * settings.clps_por_pagina
    fim = inicio + settings.clps_por_pagina
    clps_pagina = clps[inicio:fim]

    total_paginas = (len(clps) + settings.clps_por_pagina - 1) // settings.clps_por_pagina

    
    return render_template('index.html', clps=clps_pagina, page=page, total_paginas=total_paginas, valor=settings.clps_por_pagina)

@app.route('/clp/<ip>')
def detalhes_clps(ip):

    #Identificação de portas abertas
    clps = carregar_clps()
    clp = next((c for c in clps if c["ip"] == ip), None)
    status = "deconectado"
    if clp is None:
        return "CLP não encontrado", 404

    
    portas_abertas = [porta for porta in clp["portas"]]
    
    return render_template("detalhes.html", ip=clp["ip"], portas_abertas=portas_abertas, Status=status)


@app.route("/alterar", methods=["POST"])
def alterar_clps_pagina():

    #Alterar quantidade de CLPs p/ página
    novo_valor  = request.form.get("novo_valor", type=int)
    if novo_valor and novo_valor > 0:
        setattr(settings, "clps_por_pagina", novo_valor)
    return redirect(url_for('index'))

@app.route("/alterarColeta")
def alterar_coleta_ips():
    if settings.status_coleta == "ativado":
        setattr(settings, "status_coleta", "desativado")
    else:
        setattr(settings, "status_coleta", "ativado")
    return redirect(url_for("coleta_de_ips"))

@app.route("/coletaIps")
def coleta_de_ips():
    logs = log.carregar_logs()
    return render_template("coleta.html", status=settings.status_coleta, logs=logs )




@app.route("/logs")
def logs_geral():
    logs = log.carregar_logs(caminho=caminho_coleta)  # garantir que é coleta
    return render_template("logs.html", logs=logs)


def iniciar_web() -> None:
    """Inicia o servidor web"""
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader = True)




if __name__ == '__main__':
    iniciar_web()