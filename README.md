CLP TCC
Este projeto é uma aplicação web para detetar, gerir e interagir com controladores lógicos programáveis (CLPs) numa rede local. A aplicação utiliza uma combinação de ferramentas de scanning de rede e um servidor web para fornecer uma interface de utilizador intuitiva.

Funcionalidades
Deteção Automática de CLPs: A aplicação escuta o tráfego de rede para detetar novos dispositivos que possam ser CLPs.

Scanning de Portas: Verifica portas abertas em dispositivos detetados para identificar serviços relevantes (ex: Modbus na porta 502).

Interface Web: Uma interface de utilizador baseada na web para visualizar e gerir os CLPs detetados.

Detalhes do CLP: Exibe informações detalhadas sobre cada CLP, incluindo endereço IP, portas abertas, e logs de atividade.

Interação com CLPs: Permite a conexão a CLPs via Modbus para ler registos.

Registo de Atividades: Regista eventos importantes da aplicação e da interação com os CLPs.

Como Executar o Projeto
Pré-requisitos
Python 3.x

Npcap (ou WinPcap) para utilizadores de Windows, para o funcionamento correto do Scapy.

Instalação
Clone o repositório:

Bash

git clone https://github.com/markus8006/clp_tcc.git
cd clp_tcc
Crie e ative um ambiente virtual (recomendado):

Bash

python -m venv .venv
# No Windows
.venv\Scripts\activate
# No macOS/Linux
source .venv/bin/activate
Instale as dependências:

Bash

pip install -r requeriments.txt
Execução
Para iniciar a aplicação, execute o seguinte comando na raiz do projeto:

Bash

python run.py
A aplicação estará acessível no seu navegador em http://127.0.0.1:5000.

Estrutura do Projeto
/
|-- clp_app/
|   |-- api/
|   |   `-- routes.py       # Rotas da API para interagir com os CLPs
|   |-- scanner/
|   |   |-- portas.py       # Funções para scanning de portas
|   |   |-- rede.py         # Lógica de sniffing de rede com Scapy
|   |   `-- service.py      # Serviço para gerir o processo de scanning
|   `-- server/
|       |-- static/         # Ficheiros estáticos (CSS, JS, imagens)
|       |-- templates/      # Templates HTML (Flask/Jinja2)
|       `-- server.py       # Ficheiro principal do servidor Flask
|-- configs/
|   `-- settings.py     # Configurações da aplicação
|-- utils/
|   |-- CLP.py              # Gestor de dados dos CLPs (carregar/salvar JSON)
|   |-- clp_functions.py    # Funções para criar e interagir com CLPs
|   `-- log.py              # Configuração de logging
|-- .gitignore
|-- requeriments.txt        # Dependências do Python
`-- run.py                  # Script para iniciar a aplicação
Tecnologias Utilizadas
Backend:

Flask: Um micro-framework web para Python.

Scapy: Uma poderosa biblioteca de manipulação de pacotes de rede.

Pymodbus: Uma biblioteca para comunicação Modbus.

Frontend:

HTML5 / CSS3: Para a estrutura e estilo das páginas web.

JavaScript: Para interatividade do lado do cliente e atualizações dinâmicas.

Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.
