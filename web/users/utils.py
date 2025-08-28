from flask import Blueprint, jsonify, request, redirect
from utils.CLP import CLP, CLPGen
from threading import Thread

def _run_in_thread(target, *args, **kwargs):
    """Executa target(...) em uma Thread daemon e retorna o objeto Thread."""
    t = Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


clp_bp = Blueprint("utils", __name__, url_prefix="/clp")

@clp_bp.route("/<ip>/connect", methods=["POST"])
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
            return jsonify({"ok": False, "message": "Falha na conexão"})

    _run_in_thread(job)
    return jsonify({"ok": True, "message": "Conexão iniciada em background"})


@clp_bp.route("/<ip>/disconnect", methods=["POST"])
def clp_disconnect(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404

    try:
        obj.desconectar()
        return jsonify({"ok": True, "message": "Desconectado", "status": obj.get_info()["status"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@clp_bp.route("/<ip>/baixar_codigo", methods=["POST"])
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


@clp_bp.route("/<ip>/add_port", methods=["POST"])
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


@clp_bp.route("/<ip>/info", methods=["GET"])
def clp_info(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404
    return jsonify({"ok": True, "clp": obj.get_info()})

