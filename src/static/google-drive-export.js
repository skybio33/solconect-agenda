/**
 * Interface para gerenciar exportação automática para Google Drive
 */

class GoogleDriveExportManager {
    constructor() {
        this.baseUrl = '/api/export';
        this.statusInterval = null;
        this.init();
    }

    init() {
        this.createExportPanel();
        this.loadStatus();
        this.startStatusMonitoring();
    }

    createExportPanel() {
        // Verificar se já existe
        if (document.getElementById('google-drive-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'google-drive-panel';
        panel.className = 'export-panel';
        panel.innerHTML = `
            <div class="export-header">
                <h3>
                    <i class="fab fa-google-drive"></i>
                    Exportação Google Drive
                </h3>
                <button class="btn-toggle" onclick="toggleExportPanel()">
                    <i class="fas fa-chevron-down"></i>
                </button>
            </div>
            
            <div class="export-content" id="export-content">
                <div class="export-status" id="export-status">
                    <div class="status-item">
                        <span class="status-label">Status:</span>
                        <span class="status-value" id="status-text">Carregando...</span>
                        <div class="status-indicator" id="status-indicator"></div>
                    </div>
                    
                    <div class="status-item">
                        <span class="status-label">Intervalo:</span>
                        <span class="status-value" id="interval-text">-</span>
                    </div>
                    
                    <div class="status-item">
                        <span class="status-label">Última exportação:</span>
                        <span class="status-value" id="last-export">-</span>
                    </div>
                </div>
                
                <div class="export-controls">
                    <div class="control-group">
                        <label for="export-interval">Intervalo (minutos):</label>
                        <input type="number" id="export-interval" min="1" max="1440" value="5">
                        <button class="btn btn-secondary" onclick="updateInterval()">
                            <i class="fas fa-save"></i> Salvar
                        </button>
                    </div>
                    
                    <div class="control-buttons">
                        <button class="btn btn-primary" onclick="manualExport()" id="manual-export-btn">
                            <i class="fas fa-upload"></i> Exportar Agora
                        </button>
                        
                        <button class="btn btn-success" onclick="startAutoExport()" id="start-btn">
                            <i class="fas fa-play"></i> Iniciar Auto
                        </button>
                        
                        <button class="btn btn-warning" onclick="stopAutoExport()" id="stop-btn">
                            <i class="fas fa-stop"></i> Parar Auto
                        </button>
                        
                        <button class="btn btn-info" onclick="testConnection()" id="test-btn">
                            <i class="fas fa-wifi"></i> Testar
                        </button>
                    </div>
                </div>
                
                <div class="export-formats">
                    <h4>Formatos de Exportação</h4>
                    <div class="format-buttons">
                        <button class="btn btn-outline" onclick="downloadFormat('csv')">
                            <i class="fas fa-file-csv"></i> CSV
                        </button>
                        <button class="btn btn-outline" onclick="downloadFormat('json')">
                            <i class="fas fa-file-code"></i> JSON
                        </button>
                        <button class="btn btn-outline" onclick="downloadFormat('report')">
                            <i class="fas fa-file-alt"></i> Relatório
                        </button>
                    </div>
                </div>
                
                <div class="export-logs" id="export-logs">
                    <h4>Log de Atividades</h4>
                    <div class="log-container" id="log-container">
                        <div class="log-entry">
                            <span class="log-time">${new Date().toLocaleTimeString()}</span>
                            <span class="log-message">Painel de exportação inicializado</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Adicionar ao dashboard
        const sidebar = document.querySelector('.sidebar') || document.querySelector('.filters-container');
        if (sidebar) {
            sidebar.appendChild(panel);
        } else {
            document.body.appendChild(panel);
        }

        this.addStyles();
    }

    addStyles() {
        const styles = `
            .export-panel {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin: 20px 0;
                overflow: hidden;
                border: 1px solid #e2e8f0;
            }
            
            .export-header {
                background: linear-gradient(135deg, #4285f4, #34a853);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
            }
            
            .export-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .btn-toggle {
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            
            .btn-toggle.collapsed {
                transform: rotate(-90deg);
            }
            
            .export-content {
                padding: 20px;
                transition: max-height 0.3s ease;
                overflow: hidden;
            }
            
            .export-content.collapsed {
                max-height: 0;
                padding: 0 20px;
            }
            
            .export-status {
                background: #f8fafc;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .status-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .status-item:last-child {
                margin-bottom: 0;
            }
            
            .status-label {
                font-weight: 500;
                color: #4a5568;
            }
            
            .status-value {
                font-weight: 600;
                color: #2d3748;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #e2e8f0;
                margin-left: 10px;
            }
            
            .status-indicator.online {
                background: #48bb78;
                box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.2);
            }
            
            .status-indicator.offline {
                background: #f56565;
                box-shadow: 0 0 0 3px rgba(245, 101, 101, 0.2);
            }
            
            .status-indicator.running {
                background: #4299e1;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .export-controls {
                margin-bottom: 20px;
            }
            
            .control-group {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
                flex-wrap: wrap;
            }
            
            .control-group label {
                font-weight: 500;
                color: #4a5568;
                min-width: 120px;
            }
            
            .control-group input {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
                width: 80px;
            }
            
            .control-buttons {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .control-buttons .btn {
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .btn-primary {
                background: #4299e1;
                color: white;
            }
            
            .btn-primary:hover {
                background: #3182ce;
            }
            
            .btn-success {
                background: #48bb78;
                color: white;
            }
            
            .btn-success:hover {
                background: #38a169;
            }
            
            .btn-warning {
                background: #ed8936;
                color: white;
            }
            
            .btn-warning:hover {
                background: #dd6b20;
            }
            
            .btn-info {
                background: #0bc5ea;
                color: white;
            }
            
            .btn-info:hover {
                background: #00b3d7;
            }
            
            .btn-secondary {
                background: #a0aec0;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #718096;
            }
            
            .btn-outline {
                background: white;
                color: #4a5568;
                border: 1px solid #e2e8f0;
            }
            
            .btn-outline:hover {
                background: #f7fafc;
                border-color: #cbd5e0;
            }
            
            .export-formats {
                margin-bottom: 20px;
            }
            
            .export-formats h4 {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: 600;
                color: #4a5568;
            }
            
            .format-buttons {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .export-logs h4 {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: 600;
                color: #4a5568;
            }
            
            .log-container {
                background: #1a202c;
                color: #e2e8f0;
                border-radius: 6px;
                padding: 10px;
                max-height: 150px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            
            .log-entry {
                margin-bottom: 5px;
                display: flex;
                gap: 10px;
            }
            
            .log-time {
                color: #4299e1;
                min-width: 80px;
            }
            
            .log-message {
                color: #e2e8f0;
            }
            
            .log-error {
                color: #f56565;
            }
            
            .log-success {
                color: #48bb78;
            }
            
            .log-warning {
                color: #ed8936;
            }
            
            @media (max-width: 768px) {
                .control-buttons {
                    flex-direction: column;
                }
                
                .control-buttons .btn {
                    width: 100%;
                    justify-content: center;
                }
                
                .format-buttons {
                    flex-direction: column;
                }
                
                .format-buttons .btn {
                    width: 100%;
                    justify-content: center;
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    async loadStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/google-drive/status`);
            const data = await response.json();

            if (data.success) {
                this.updateStatusDisplay(data.status);
            } else {
                this.addLog('Erro ao carregar status', 'error');
            }
        } catch (error) {
            this.addLog(`Erro de conexão: ${error.message}`, 'error');
        }
    }

    updateStatusDisplay(status) {
        const statusText = document.getElementById('status-text');
        const statusIndicator = document.getElementById('status-indicator');
        const intervalText = document.getElementById('interval-text');

        if (statusText) {
            if (!status.enabled) {
                statusText.textContent = 'Desabilitado';
                statusIndicator.className = 'status-indicator offline';
            } else if (status.running) {
                statusText.textContent = 'Executando';
                statusIndicator.className = 'status-indicator running';
            } else {
                statusText.textContent = 'Parado';
                statusIndicator.className = 'status-indicator online';
            }
        }

        if (intervalText) {
            intervalText.textContent = `${status.interval_minutes} min`;
        }

        // Atualizar campo de intervalo
        const intervalInput = document.getElementById('export-interval');
        if (intervalInput) {
            intervalInput.value = status.interval_minutes;
        }
    }

    startStatusMonitoring() {
        // Atualizar status a cada 30 segundos
        this.statusInterval = setInterval(() => {
            this.loadStatus();
        }, 30000);
    }

    addLog(message, type = 'info') {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        const time = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message log-${type}">${message}</span>
        `;

        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Manter apenas os últimos 50 logs
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    async makeRequest(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            const result = await response.json();

            return result;
        } catch (error) {
            this.addLog(`Erro de rede: ${error.message}`, 'error');
            return { success: false, message: error.message };
        }
    }
}

// Instância global
let exportManager;

// Funções globais para os botões
function toggleExportPanel() {
    const content = document.getElementById('export-content');
    const toggle = document.querySelector('.btn-toggle');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        toggle.classList.remove('collapsed');
    } else {
        content.classList.add('collapsed');
        toggle.classList.add('collapsed');
    }
}

async function manualExport() {
    const btn = document.getElementById('manual-export-btn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exportando...';
    btn.disabled = true;
    
    exportManager.addLog('Iniciando exportação manual...', 'info');
    
    const result = await exportManager.makeRequest('/google-drive/manual', 'POST');
    
    if (result.success) {
        exportManager.addLog('Exportação manual concluída!', 'success');
        showNotification('Exportação concluída com sucesso!', 'success');
    } else {
        exportManager.addLog(`Erro na exportação: ${result.message}`, 'error');
        showNotification(`Erro na exportação: ${result.message}`, 'error');
    }
    
    btn.innerHTML = originalText;
    btn.disabled = false;
    
    exportManager.loadStatus();
}

async function startAutoExport() {
    exportManager.addLog('Iniciando exportação automática...', 'info');
    
    const result = await exportManager.makeRequest('/google-drive/start', 'POST');
    
    if (result.success) {
        exportManager.addLog('Exportação automática iniciada!', 'success');
        showNotification('Exportação automática iniciada!', 'success');
    } else {
        exportManager.addLog(`Erro ao iniciar: ${result.message}`, 'error');
        showNotification(`Erro ao iniciar: ${result.message}`, 'error');
    }
    
    exportManager.loadStatus();
}

async function stopAutoExport() {
    exportManager.addLog('Parando exportação automática...', 'warning');
    
    const result = await exportManager.makeRequest('/google-drive/stop', 'POST');
    
    if (result.success) {
        exportManager.addLog('Exportação automática parada!', 'warning');
        showNotification('Exportação automática parada!', 'info');
    } else {
        exportManager.addLog(`Erro ao parar: ${result.message}`, 'error');
        showNotification(`Erro ao parar: ${result.message}`, 'error');
    }
    
    exportManager.loadStatus();
}

async function testConnection() {
    const btn = document.getElementById('test-btn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testando...';
    btn.disabled = true;
    
    exportManager.addLog('Testando conexão com Google Drive...', 'info');
    
    const result = await exportManager.makeRequest('/google-drive/test', 'POST');
    
    if (result.success) {
        exportManager.addLog('Conexão com Google Drive OK!', 'success');
        showNotification('Conexão com Google Drive OK!', 'success');
    } else {
        exportManager.addLog(`Erro na conexão: ${result.message}`, 'error');
        showNotification(`Erro na conexão: ${result.message}`, 'error');
    }
    
    btn.innerHTML = originalText;
    btn.disabled = false;
}

async function updateInterval() {
    const intervalInput = document.getElementById('export-interval');
    const interval = parseInt(intervalInput.value);
    
    if (interval < 1 || interval > 1440) {
        showNotification('Intervalo deve ser entre 1 e 1440 minutos', 'error');
        return;
    }
    
    exportManager.addLog(`Atualizando intervalo para ${interval} minutos...`, 'info');
    
    const result = await exportManager.makeRequest('/google-drive/config', 'POST', {
        interval_minutes: interval
    });
    
    if (result.success) {
        exportManager.addLog('Intervalo atualizado!', 'success');
        showNotification('Intervalo atualizado!', 'success');
    } else {
        exportManager.addLog(`Erro ao atualizar: ${result.message}`, 'error');
        showNotification(`Erro ao atualizar: ${result.message}`, 'error');
    }
    
    exportManager.loadStatus();
}

async function downloadFormat(format) {
    exportManager.addLog(`Gerando arquivo ${format.toUpperCase()}...`, 'info');
    
    const result = await exportManager.makeRequest(`/formats/${format}`);
    
    if (result.success) {
        // Criar e baixar arquivo
        const blob = new Blob([result.content], {
            type: format === 'json' ? 'application/json' : 'text/plain'
        });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = result.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        exportManager.addLog(`Arquivo ${format.toUpperCase()} baixado!`, 'success');
        showNotification(`Arquivo ${format.toUpperCase()} baixado!`, 'success');
    } else {
        exportManager.addLog(`Erro ao gerar ${format}: ${result.message}`, 'error');
        showNotification(`Erro ao gerar ${format}: ${result.message}`, 'error');
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Aguardar um pouco para garantir que outros scripts carregaram
    setTimeout(() => {
        exportManager = new GoogleDriveExportManager();
    }, 1000);
});

// Limpar interval ao sair da página
window.addEventListener('beforeunload', () => {
    if (exportManager && exportManager.statusInterval) {
        clearInterval(exportManager.statusInterval);
    }
});
