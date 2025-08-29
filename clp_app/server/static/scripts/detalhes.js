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

