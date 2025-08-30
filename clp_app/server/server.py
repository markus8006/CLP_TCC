# clp_app/server/server.py
import os
import logging
# Importamos os módulos diretamente, não mais as classes
from utils import CLP as clp_manager, clp_functions
from utils import log
from clp_app.scanner import portas as scanner_portas
from flask import Flask, render_template, jsonify, request, redirect, url_for

# -----------------------
# Configuração Inicial do App
# -----------------------

app = Flask(__name__)

# O manager já carrega os CLPs na inicialização do módulo.
# clp_manager.carregar_clps()

# Variáveis globais de estado da aplicação web
status_coleta = "desativado"
clps_por_pagina = 21


# -----------------------
# Helpers (Agora usam o manager e as funções)
# -----------------------
def obter_clps_lista() -> list:
    """Retorna uma lista de dicionários com as informações dos CLPs."""
    # A função get_info garante que os dados estão no formato correto para o template
    return [clp_functions.get_info(c) for c in clp_manager.listar_clps()]


# -----------------------
# Rotas de Frontend (Páginas Principais)
# -----------------------
@app.route('/')
def index():
    """Página principal que lista os CLPs detectados."""
    clps_lista = obter_clps_lista()

    # Lógica de paginação
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
    """Página de detalhes para um CLP específico."""
    clp_dict = clp_manager.buscar_por_ip(ip)

    if clp_dict is None:
        return "CLP não encontrado", 404

    info = clp_functions.get_info(clp_dict)
    return render_template("detalhes.html", clp=info)


@app.route("/coletaIps")
def coleta_de_ips():
    """Página para controlar e visualizar o status da coleta de IPs."""
    global status_coleta
    logs_coleta = log.carregar_logs(caminho=log.caminho_coleta)
    return render_template("coleta.html", status=status_coleta, logs=logs_coleta)


@app.route("/logs")
def logs_geral():
    """Página que exibe os logs gerais da aplicação."""
    logs = log.carregar_logs()
    return render_template("logs.html", logs=logs)


# -----------------------
# Rotas de Ação (POSTs e Redirecionamentos)
# -----------------------
@app.route('/clp/rename', methods=['POST'])
def rename_clp():
    """Endpoint da API para renomear um CLP."""
    data = request.get_json()
    if not data or not data.get('ip') or not data.get('novo_nome'):
        return jsonify({'success': False, 'message': 'IP e novo nome são obrigatórios.'}), 400

    ip = data['ip']
    novo_nome = data['novo_nome'].strip()

    try:
        clp_alvo = clp_manager.buscar_por_ip(ip)
        if clp_alvo:
            # Modifica o dicionário diretamente
            clp_alvo['nome'] = novo_nome
            clp_manager.salvar_clps()
            return jsonify({'success': True, 'message': 'Nome atualizado com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'CLP não encontrado.'}), 404
    except Exception as e:
        logging.exception("Erro ao renomear CLP")
        return jsonify({'success': False, 'message': 'Erro interno no servidor.'}), 500


@app.route("/alterar", methods=["POST"])
def alterar_clps_pagina():
    """Altera o número de CLPs exibidos por página."""
    global clps_por_pagina
    novo_valor = request.form.get("novo_valor", type=int)
    if novo_valor and novo_valor > 0:
        clps_por_pagina = novo_valor
    return redirect(url_for('index'))


@app.route("/alterarColeta")
def alterar_coleta_ips():
    """Ativa ou desativa o status da coleta de IPs."""
    global status_coleta
    status_coleta = "desativado" if status_coleta == "ativado" else "ativado"
    return redirect(url_for("coleta_de_ips"))


# -----------------------
# Rotas de API e Administrativas
# -----------------------
@app.route("/api/clps")
def api_clps():
    """Retorna um JSON com a lista de todos os CLPs."""
    return jsonify(obter_clps_lista())


@app.route('/api/scan/<ip>', methods=['POST'])
def api_scan_ip(ip):
    """Endpoint para iniciar um scan em um IP e criar/atualizar o CLP."""
    try:
        portas_abertas = scanner_portas.escanear_portas(ip, portas_alvo=[502, 80, 443])

        if not portas_abertas:
            return jsonify({"success": False, "message": f"Nenhuma porta relevante encontrada para {ip}."}), 404

        clp_existente = clp_manager.buscar_por_ip(ip)

        if clp_existente:
            for porta in portas_abertas:
                # Usa a função para adicionar a porta ao dicionário
                clp_functions.adicionar_porta(clp_existente, porta)
            clp_manager.salvar_clps()
            return jsonify({"success": True, "action": "updated", "clp": clp_functions.get_info(clp_existente)})
        else:
            # Usa a função para criar um novo dicionário de CLP
            novo_clp = clp_functions.criar_clp(IP=ip, PORTAS=portas_abertas)
            clp_manager.adicionar_clp(novo_clp)
            clp_manager.salvar_clps()
            return jsonify({"success": True, "action": "created", "clp": clp_functions.get_info(novo_clp)}), 201
    except Exception as e:
        logging.exception(f"Erro no processo de scan para {ip}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/admin/reload_clps", methods=["POST"])
def admin_reload_clps():
    """Recarrega a lista de CLPs a partir do arquivo JSON."""
    try:
        clp_manager.carregar_clps()
        return jsonify({"ok": True, "message": "CLPs recarregados com sucesso."})
    except Exception as e:
        logging.exception("Erro ao recarregar CLPs")
        return jsonify({"ok": False, "error": str(e)}), 500


# -----------------------
# Iniciar servidor
# -----------------------
def iniciar_web() -> None:
    """Inicia o servidor web Flask."""
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    iniciar_web()