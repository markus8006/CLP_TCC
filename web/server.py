import os
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from threading import Thread
from utils import log
from utils.CLP import CLP, CLPGen, clps

app = Flask(__name__)

status_coleta = "desativado"
clps_por_pagina = 21

# BASE_DIR usado apenas se você precisar formar caminhos relativos aos templates/logs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- Ao iniciar o módulo, carrega os CLPs do JSON (popula 'clps') ---
CLP.carregar_todos()


def obter_clps_lista() -> list:
    """
    Retorna uma lista de dicionários com as informações dos CLPs
    (usado para paginação e exibição).
    """
    return [c.get_info() for c in CLP.listar_clps()]


@app.route('/')
def index():
    clps_lista = obter_clps_lista()

    # paginação
    page = request.args.get('page', 1, type=int)
    inicio = (page - 1) * clps_por_pagina
    fim = inicio + clps_por_pagina
    clps_pagina = clps_lista[inicio:fim]
    total_paginas = (len(clps_lista) + clps_por_pagina - 1) // clps_por_pagina

    return render_template(
        'index.html',
        clps=clps_pagina,
        page=page,
        total_paginas=total_paginas,
        valor=clps_por_pagina
    )


@app.route('/clp/<ip>')
def detalhes_clps(ip):
    # busca o objeto CLP pelo IP
    obj = CLP.buscar_por_ip(ip)
    if obj is None:
        return "CLP não encontrado", 404

    info = obj.get_info()
    portas_abertas = info.get("portas", [])
    status = info.get("status", "Offline")

    return render_template("detalhes.html", ip=info["ip"], portas_abertas=portas_abertas, Status=status, clp=info)


@app.route("/alterar", methods=["POST"])
def alterar_clps_pagina():
    # Alterar quantidade de CLPs por página
    global clps_por_pagina
    novo_valor = request.form.get("novo_valor", type=int)
    if novo_valor and novo_valor > 0:
        clps_por_pagina = novo_valor
    return redirect(url_for('index'))


@app.route("/alterarColeta")
def alterar_coleta_ips():
    global status_coleta
    status_coleta = "desativado" if status_coleta == "ativado" else "ativado"
    return redirect(url_for("coleta_de_ips"))


@app.route("/coletaIps")
def coleta_de_ips():
    global status_coleta
    return render_template("coleta.html", status=status_coleta)


@app.route("/logs")
def logs_geral():
    logs = log.carregar_logs()
    return render_template("logs.html", logs=logs)


# ------ Exemplo: endpoint para retornar JSON com todos os CLPs ------
@app.route("/api/clps")
def api_clps():
    """Retorna JSON com todos os CLPs (útil para front-end dinâmico)."""
    return jsonify(obter_clps_lista())


def iniciar_web() -> None:
    """Inicia o servidor web"""
    # obs: em produção remova debug=True e use servidor WSGI apropriado
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=True)


if __name__ == '__main__':
    iniciar_web()
