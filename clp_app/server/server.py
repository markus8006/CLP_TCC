import os
import logging
from utils import CLP as clp_manager, clp_functions
from utils import log
from clp_app.scanner import portas as scanner_portas
from flask import Flask, render_template, jsonify, request, redirect, url_for
from clp_app.api.routes import clp_bp
from clp_app.scanner.service import scanner_service

# -----------------------
# Configuração Inicial do App
# -----------------------

app = Flask(__name__)
app.register_blueprint(clp_bp)

clps_por_pagina = 21


# -----------------------
# Helpers (Agora usam o manager e as funções)
# -----------------------
def obter_clps_lista() -> list:
    """Retorna uma lista de dicionários com as informações dos CLPs."""
    return [clp_functions.get_info(c) for c in clp_manager.listar_clps()]


# -----------------------
# Rotas de Frontend (Páginas Principais)
# -----------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    """Página principal que lista os CLPs, com filtro de pesquisa por nome e tag."""
    clps_lista = obter_clps_lista()
    search_term = ""
    tag_term = "" # <-- NOVO

    if request.method == 'POST':
        search_term = request.form.get("buscar_clp", "").lower()
        tag_term = request.form.get("buscar_tag", "").lower() # <-- NOVO

        if search_term:
            clps_lista = [
                clp for clp in clps_lista
                if search_term in clp.get('nome', '').lower()
            ]
        
        # <-- NOVO: Filtra por tag se um termo de tag for fornecido
        if tag_term:
            clps_lista = [
                clp for clp in clps_lista
                if any(tag_term in tag.lower() for tag in clp.get('tags', []))
            ]

    # ... (lógica de paginação continua a mesma)
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
        valor=clps_por_pagina,
        search_term=search_term,
        tag_term=tag_term # <-- NOVO
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
    status_atual = scanner_service.get_status()
    logs_coleta = log.carregar_logs(caminho=log.caminho_coleta)
    return render_template("coleta.html", status=status_atual, logs=logs_coleta)


@app.route("/logs")
def logs_geral():
    """Página que exibe os logs gerais da aplicação."""
    logs = log.carregar_logs()
    return render_template("logs.html", logs=logs)


# -----------------------
# Rotas de Ação (POSTs e Redirecionamentos)
# -----------------------
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
    """Ativa ou desativa o status da coleta de IPs usando o serviço."""
    status_atual = scanner_service.get_status()
    if status_atual == "ativado":
        scanner_service.stop()
        log.log("Sistema de coleta de IPs desativado pelo usuário.")
    else:
        scanner_service.start()
        log.log("Sistema de coleta de IPs ativado pelo usuário.")
    return redirect(url_for("coleta_de_ips"))


# -----------------------
# Rotas de API e Administrativas
# -----------------------
@app.route("/api/clps")
def api_clps():
    """Retorna um JSON com a lista de todos os CLPs."""
    return jsonify(obter_clps_lista())

@app.route("/api/logs/coleta")
def api_logs_coleta():
    """Retorna os logs de coleta mais recentes em formato JSON."""
    logs_coleta = log.carregar_logs(caminho=log.caminho_coleta)
    return jsonify(logs_coleta)


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
                clp_functions.adicionar_porta(clp_existente, porta)
            clp_manager.salvar_clps()
            return jsonify({"success": True, "action": "updated", "clp": clp_functions.get_info(clp_existente)})
        else:
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