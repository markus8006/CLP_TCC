from flask import Blueprint, jsonify, request, redirect
from utils.CLP import CLP, CLPGen
from threading import Thread
from clp_app.scanner.service import scanner_service

def _run_in_thread(target, *args, **kwargs):
    """Executa target(...) em uma Thread daemon e retorna o objeto Thread."""
    t = Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


clp_bp = Blueprint("utils", __name__, url_prefix="/clp")

@clp_bp.route("/<ip>/connect", methods=["POST"])
def clp_connect(ip):
    obj : CLP
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404

    data = request.json or {}
    porta_selecionada = data.get("port")

    def job():
        obj.adicionar_log(f"Iniciando tentativa de conexão na {porta_selecionada}...")
        try:
            sucesso = obj.conectar(port=porta_selecionada)
            obj.adicionar_log(f"Estado após tentar conectar: {obj.conectado}")
        except Exception as e:
            obj.adicionar_log(f"Erro durante conectar: {e}")
            return jsonify({"ok": False, "messageCLP": "Falha na conexão"})

    _run_in_thread(job)
    return jsonify({"ok": True, "messageCLP": "Conexão iniciada em background"})


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


@clp_bp.route("/clp/<ip>/status", methods=["GET"])
def clp_status(ip):
    """Retorna o status atual de um CLP."""
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404


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


@clp_bp.route('/scanner/status', methods=['GET'])
def get_scanner_status():
    return jsonify({'status': scanner_service.get_status()})

@clp_bp.route('/scanner/start', methods=['POST'])
def start_scanner():
    success = scanner_service.start()
    return jsonify({'ok': success, 'status': scanner_service.get_status()})

@clp_bp.route('/scanner/stop', methods=['POST'])
def stop_scanner():
    success = scanner_service.stop()
    return jsonify({'ok': success, 'status': scanner_service.get_status()})
@clp_bp.route("/<ip>/info", methods=["GET"])
def clp_info(ip):
    obj = CLP.buscar_por_ip(ip)
    if not obj:
        return jsonify({"ok": False, "error": "CLP não encontrado"}), 404
    return jsonify({"ok": True, "clp": obj.get_info()})

# Em web/users/utils.py

@clp_bp.route("/<ip>/read_register", methods=["POST"])
def clp_read_register(ip):
    obj = CLP.buscar_por_ip(ip)
    # Verifica se o CLP está conectado
    if not obj or not obj.client or not obj.client.is_socket_open():
        return jsonify({"ok": False, "error": "CLP não conectado"}), 400

    data = request.json
    address = data.get("address")
    if address is None:
        return jsonify({"ok": False, "error": "Endereço é obrigatório"}), 400

    try:
        address = int(address)
        # Tenta ler um "Holding Register". Você pode adicionar lógica para outros tipos.
        # O endereço para a biblioteca é o endereço real - 1 (ex: 40001 -> 0)
        result = obj.client.read_holding_registers(address, 1, unit=1)

        if result.isError():
            return jsonify({"ok": False, "error": "Erro Modbus ao ler registrador"})
        
        # Retorna o valor do primeiro registrador lido
        value = result.registers[0]
        return jsonify({"ok": True, "address": address, "value": value})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
