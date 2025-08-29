// Função para mostrar mensagens GERAIS (leitura de registrador, etc.)
function showActionMsg(text, timeout=4000) {
    const el = document.getElementById('mensagem');
    if (el) {
        el.textContent = text;
        if (timeout) setTimeout(()=> el.textContent = '', timeout);
    }
}

// Função para mostrar mensagens de CONEXÃO do CLP
function showClpMsg(text, timeout=4000) {
    const el = document.getElementById('mensagemCLP');
    if (el) {
        el.textContent = text;
        if (timeout) setTimeout(()=> el.textContent = '', timeout);
    }
}

async function fetchJson(url, opts) {
    try {
        const resp = await fetch(url, opts);
        if (!resp.ok) {
            return { ok: false, error: `HTTP error! status: ${resp.status}` };
        }
        return await resp.json();
    } catch (err) {
        return { ok: false, error: err.toString() };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const ip = document.getElementById('clpIp').textContent;
    const btnConnect = document.getElementById('btnConnect');
    const btnDisconnect = document.getElementById('btnDisconnect');
    const btnReadRegister = document.getElementById('btnReadRegister');
    const logContainer = document.getElementById('logContainer');

    // Botão Conectar usa showClpMsg
    if (btnConnect) {
        btnConnect.addEventListener('click', async () => {
            const selectedPort = document.getElementById('portSelect').value;
            showClpMsg(`Iniciando conexão na porta ${selectedPort}...`);
            
            const res = await fetchJson(`/clp/${ip}/connect`, {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ port: Number(selectedPort) })
            });

            if (res.ok) {
                showClpMsg(res.message);
                setTimeout(() => atualizarInfo(ip), 3000); 
            } else {
                showClpMsg('Erro: ' + (res.error || 'unknown'));
            }
        });
    }
    
    // Botão Desconectar também usa showClpMsg
    if (btnDisconnect) {
        btnDisconnect.addEventListener('click', async () => {
            showClpMsg('Desconectando...');
            const res = await fetchJson(`/clp/${ip}/disconnect`, { method: 'POST' });
            if (res.ok) {
                showClpMsg('Desconectado');
                window.location.reload();
            } else {
                showClpMsg('Erro: ' + (res.error || 'unknown'));
            }
        });
    }

    // Botão Ler Registrador usa showActionMsg
    if (btnReadRegister) {
        btnReadRegister.addEventListener('click', async () => {
            const address = document.getElementById('inputAddress').value;
            const resultDiv = document.getElementById('readResult');
            if (!address) {
                resultDiv.innerHTML = `<span style="color: red;">Por favor, insira um endereço.</span>`;
                return;
            }
            showActionMsg(`Lendo endereço ${address}...`); // <--- Usa a função de mensagem geral
            const res = await fetchJson(`/clp/${ip}/read_register`, {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ address: Number(address) })
            });
            if (res.ok) {
                resultDiv.innerHTML = `Endereço <strong>${res.address}</strong> = <strong>${res.value}</strong>`;
                showActionMsg('Leitura concluída com sucesso!');
            } else {
                resultDiv.innerHTML = `<span style="color: red;">Erro: ${res.error}</span>`;
                showActionMsg(`Falha na leitura do endereço ${address}.`);
            }
        });
    }

    // Função para atualizar informações da página
    async function atualizarInfo(ip) {
        const statusAnterior = document.getElementById('statusText').textContent.includes('Online') ? 'Online' : 'Offline';
        const res = await fetchJson(`/clp/${ip}/info`);
        if (!res.ok) return;

        const clp = res.clp;
        const statusEl = document.getElementById('statusText');
        statusEl.textContent = 'Status: ' + clp.status;
        statusEl.className = clp.status === 'Online' ? 'status_online' : 'status_offline';

        if (logContainer && clp.logs) {
            logContainer.innerHTML = '';
            clp.logs.forEach(logLine => {
                const logEntry = document.createElement('div');
                logEntry.textContent = logLine;
                logContainer.appendChild(logEntry);
            });
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        if (clp.status === 'Online' && statusAnterior === 'Offline') {
            window.location.reload();
        }
    }

    // Inicia a atualização periódica
    setInterval(() => atualizarInfo(ip), 5000);
    atualizarInfo(ip);
});

// --- Lógica para Edição do Nome do CLP ---
document.addEventListener('DOMContentLoaded', () => {
    // Seleciona os elementos do DOM
    const viewMode = document.getElementById('viewMode');
    const editMode = document.getElementById('editMode');
    const editNameBtn = document.getElementById('editNameBtn');
    const saveNameBtn = document.getElementById('saveNameBtn');
    const cancelNameBtn = document.getElementById('cancelNameBtn');
    const clpNameSpan = document.getElementById('clpName');
    const inputClpName = document.getElementById('inputClpName');
    const clpIpSpan = document.getElementById('clpIp'); // Pega o IP do CLP

    // Função para entrar no modo de edição
    const enterEditMode = () => {
        viewMode.style.display = 'none';
        editMode.style.display = 'flex'; // Usar flex para alinhar os botões
        inputClpName.value = clpNameSpan.textContent; // Garante que o input tem o valor mais recente
        inputClpName.focus(); // Coloca o cursor no campo de texto
    };

    // Função para sair do modo de edição
    const exitEditMode = () => {
        viewMode.style.display = 'flex'; // Usar flex para alinhar o nome e o botão
        editMode.style.display = 'none';
    };

    // Função para salvar o novo nome
    const saveNewName = () => {
        const novoNome = inputClpName.value.trim();
        const clpIp = clpIpSpan.textContent;

        // Validação simples: não salvar se o nome estiver vazio ou for o mesmo
        if (!novoNome || novoNome === clpNameSpan.textContent) {
            exitEditMode();
            return;
        }

        // Envia os dados para o servidor usando Fetch API
        fetch('/clp/rename', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ip: clpIp,
                novo_nome: novoNome
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Se o servidor confirmou, atualiza o nome na tela
                clpNameSpan.textContent = novoNome;
                alert('Nome atualizado com sucesso!'); // Ou uma notificação mais elegante
            } else {
                alert('Erro ao atualizar o nome: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            alert('Ocorreu um erro de comunicação com o servidor.');
        })
        .finally(() => {
            // Sempre sai do modo de edição, seja com sucesso ou erro
            exitEditMode();
        });
    };

    // Adiciona os eventos aos botões
    if (editNameBtn) {
        editNameBtn.addEventListener('click', enterEditMode);
    }
    if (saveNameBtn) {
        saveNameBtn.addEventListener('click', saveNewName);
    }
    if (cancelNameBtn) {
        cancelNameBtn.addEventListener('click', exitEditMode);
    }
});