# web.py
import os
import json
import logging
from threading import Thread
from flask import Flask, render_template, jsonify, request, redirect, url_for

from utils import log
from utils.CLP import CLP, CLPGen, clps

app = Flask(__name__)

status_coleta = "desativado"
clps_por_pagina = 21

# BASE_DIR usado apenas se você precisar formar caminhos relativos aos templates/logs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Ao iniciar o módulo, carrega os CLPs do JSON (popula 'clps') ---
CLP.carregar_todos()


# -----------------------
# Helpers
# -----------------------
def obter_clps_lista() -> list:
    """Retorna uma lista de dicionários com as informações dos CLPs (usado para paginação e exibição)."""
    return [c.get_info() for c in CLP.listar_clps()]


def _run_in_thread(target, *args, **kwargs):
    """Executa target(...) em uma Thread daemon e retorna o objeto Thread."""
    t = Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


# -----------------------
# Rotas de frontend
# -----------------------
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
    obj = CLP.buscar_por_ip(ip)
    if obj is None:
        return "CLP não encontrado", 404
    info = obj.get_info()
    return render_template("detalhes.html", clp=info)


@app.route("/alterar", methods=["POST"])
def alterar_clps_pagina():
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


# -----------------------
# Endpoints para executar métodos do CLP
# -----------------------
@app.route("/clp/<ip>/connect", methods=["POST"])
def clp_connect(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404

    def job():
        obj.adicionar_log("Iniciando tentativa de conexão...")
        try:
            sucesso = obj.conectar()
            obj.adicionar_log(f"Estado após tentar conectar: {obj.conectado}")
        except Exception as e:
            obj.adicionar_log(f"Erro durante conectar: {e}")

    _run_in_thread(job)
    return jsonify({"ok": True, "message": "Conexão iniciada em background"})


@app.route("/clp/<ip>/disconnect", methods=["POST"])
def clp_disconnect(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404

    try:
        obj.desconectar()
        return jsonify({"ok": True, "message": "Desconectado", "status": obj.get_info()["status"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/clp/<ip>/baixar_codigo", methods=["POST"])
def clp_baixar_codigo(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404

    data = request.json or {}
    admin = data.get("admin")
    senha = data.get("senha")
    caminho_local = data.get("caminho_local", "programa.hex")

    if not admin or not senha:
        return jsonify({"ok": False, "error": "admin e senha são obrigatórios"}), 400

    def job():
        obj.adicionar_log("Iniciando envio do código via FTP...")
        try:
            sucesso = obj.baixar_codigo(admin=admin, senha=senha, caminho_local=caminho_local)
            obj.adicionar_log(f"Envio finalizado: {'sucesso' if sucesso else 'falha'}")
        except Exception as e:
            obj.adicionar_log(f"Erro ao enviar código: {e}")

    _run_in_thread(job)
    return jsonify({"ok": True, "message": "Envio iniciado em background"})


@app.route("/clp/<ip>/add_port", methods=["POST"])
def clp_add_port(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404

    data = request.json or {}
    porta = data.get("porta")
    if porta is None:
        return jsonify({"ok": False, "error": "porta obrigatória"}), 400

    try:
        obj.adicionar_porta(int(porta))
        return jsonify({"ok": True, "message": "Porta adicionada", "portas": obj.PORTAS})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/clp/<ip>/info", methods=["GET"])
def clp_info(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404
    return jsonify({"ok": True, "clp": obj.get_info()})


# -----------------------
# Rota utilitária: recarregar CLPs do JSON em runtime
# -----------------------
@app.route("/admin/reload_clps", methods=["POST"])
def admin_reload_clps():
    try:
        CLP.carregar_todos()
        return jsonify({"ok": True, "message": "CLPs recarregados a partir do JSON"})
    except Exception as e:
        logging.exception("Erro ao recarregar CLPs")
        return jsonify({"ok": False, "error": str(e)}), 500


# -----------------------
# Iniciar servidor
# -----------------------
def iniciar_web() -> None:
    """Inicia o servidor web (note sobre use_reloader abaixo)."""
    # Atenção: use_reloader=True pode executar o módulo duas vezes (duplicando efeitos colaterais / threads).
    # Em dev você pode querer debug=True mas use_reloader=False para evitar duplicatas.
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)


if __name__ == '__main__':
    iniciar_web()
