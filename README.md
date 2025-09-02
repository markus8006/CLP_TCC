# CLP TCC - Ferramenta de Gestão de CLPs

Este projeto é uma aplicação web desenvolvida para detetar, gerir e interagir com Controladores Lógicos Programáveis (CLPs) numa rede local. A aplicação combina um scanner de rede passivo com um servidor web para fornecer uma interface de utilizador intuitiva e centralizada.

## Funcionalidades Principais

- **Deteção Automática de CLPs:** Escuta o tráfego de rede (pacotes ARP e TCP SYN) para descobrir novos dispositivos na rede de forma passiva.
- **Scanning de Portas:** Verifica portas abertas nos dispositivos detetados para identificar serviços relevantes (ex: Modbus na porta 502).
- **Interface Web com Flask:** Uma interface de utilizador simples e reativa para visualizar e gerir os CLPs encontrados.
- **Detalhes do Dispositivo:** Exibe informações detalhadas sobre cada CLP, incluindo endereço IP, nome, portas abertas e logs de atividade.
- **Interação Modbus:** Permite a conexão a CLPs via Modbus TCP para ler registos de holding.
- **Gestão de Tags:** Permite adicionar e filtrar CLPs por tags personalizadas para melhor organização.
- **Logging:** Regista as atividades do scanner e da aplicação em ficheiros de log separados para fácil depuração.

## Como Executar

### Pré-requisitos

- Python 3.7+
- Npcap: Essencial para utilizadores de Windows, para o funcionamento correto do Scapy.  
  **Importante:** Durante a instalação do Npcap, certifique-se de marcar a opção "Install Npcap in WinPcap API-compatible Mode".

### Instalação

1. Clone o repositório:
    ```bash
    git clone https://github.com/markus8006/clp_tcc.git
    cd clp_tcc
    ```

2. Crie e ative um ambiente virtual (recomendado):
    - Criar o ambiente:
      ```bash
      python -m venv .venv
      ```

    - Ativar no Windows:
      ```bash
      .venv\Scripts\activate
      ```

    - Ativar no macOS/Linux:
      ```bash
      source .venv/bin/activate
      ```

3. Instale as dependências a partir do arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

### Execução

Com o ambiente virtual ativado, inicie a aplicação a partir da raiz do projeto:
```bash
python run.py

A aplicação estará acessível no seu navegador no endereço http://127.0.0.1:5000
.

Estrutura do Projeto
/clp_app/
    /api/
        routes.py       # Rotas da API para interagir com os CLPs (conectar, ler registos, etc.)
    /scanner/
        portas.py       # Funções para scanning de portas (Nmap com fallback para Scapy)
        rede.py         # Lógica de sniffing de rede com Scapy para descoberta de IPs
        service.py      # Serviço para gerir o ciclo de vida do processo de scanning
    /server/
        /static/         # Ficheiros estáticos (CSS, JS, imagens)
        /templates/      # Templates HTML (Flask/Jinja2)
        server.py       # Ficheiro principal do servidor Flask e rotas das páginas
/configs/
    settings.py     # Configurações globais da aplicação (atualmente não utilizado)
# Arquivos de log e dados
/logs/
    app.log             # Logs gerais da aplicação web
    clps.json           # Base de dados JSON para persistir os CLPs encontrados
    coleta.log          # Logs específicos do scanner de rede
/utils/
    CLP.py              # Gestor de dados dos CLPs (carregar/salvar JSON)
    clp_functions.py    # Funções de negócio para criar e interagir com CLPs (conectar, desconectar)
    log.py              # Módulo para configuração e gestão de logging
.gitignore
requirements.txt        # Dependências do Python para o projeto
run.py                  # Ponto de entrada para iniciar a aplicação

Tecnologias Utilizadas
Backend:

Flask: Micro-framework web para a construção do servidor e da API.

Scapy: Biblioteca para manipulação e sniffing de pacotes de rede.

Pymodbus: Biblioteca para comunicação através do protocolo Modbus.

Frontend:

HTML5 / CSS3: Estrutura e estilo das páginas web.

JavaScript (Vanilla): Para interatividade do lado do cliente e atualizações dinâmicas via Fetch API.

Chart.js: Para a visualização de gráficos de métricas.

Contribuições

Contribuições são bem-vindas! Se encontrar um bug ou tiver uma sugestão, sinta-se à vontade para abrir uma issue ou enviar um pull request.


Se precisar de mais algum ajuste ou explicação, é só avisar!
