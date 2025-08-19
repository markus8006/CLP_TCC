import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from threading import Thread


app = Flask(__name__)



def carregar_clps(rota : str = "../clp/logs/dados.json") -> list:
    """
    Coleta IPs e Portas abertas do Json\n
    rota (str) : rota dos dados.json
    """
    with open(rota, "r", encoding = "utf-8") as f:
        dados = json.load(f)

    #alterar json colocando "ip" e "portas"
    clps = []
    for ip, portas in dados.items():
        clps.append({"ip": ip, "portas": portas})
    return clps

clps_por_pagina = 21

@app.route('/')
def index():
    clps = carregar_clps()

    #Numeração de páginas
    page = request.args.get('page', 1, type=int)

    inicio = (page - 1) * clps_por_pagina
    fim = inicio + clps_por_pagina
    clps_pagina = clps[inicio:fim]

    total_paginas = (len(clps) + clps_por_pagina - 1) // clps_por_pagina

    
    return render_template('index.html', clps=clps_pagina, page=page, total_paginas=total_paginas, valor=clps_por_pagina)

@app.route('/clp/<ip>')
def detalhes_clps(ip):

    #Identificação de portas abertas
    clps = carregar_clps()
    clp = next((c for c in clps if c["ip"] == ip), None)
    if clp is None:
        return "CLP não encontrado", 404

    
    portas_abertas = [porta for porta in clp["portas"]]
    
    return render_template("detalhes.html", ip=clp["ip"], portas_abertas=portas_abertas)


@app.route("/alterar", methods=["POST"])
def alterar_clps_pagina():

    #Alterar quantidade de CLPs p/ página
    global clps_por_pagina
    novo_valor  = request.form.get("novo_valor", type=int)
    if novo_valor and novo_valor > 0:
        clps_por_pagina = novo_valor
    return redirect(url_for('index'))


def iniciar_site():
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader = True)

def iniciar_web():
    Thread(target=iniciar_web, daemon=True).start()



if __name__ == '__main__':
    iniciar_web()