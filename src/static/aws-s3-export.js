/**
 * Interface para gerenciar exportação automática para AWS S3
 */

class AWSS3ExportManager {
    constructor() {
        this.baseUrl = '/api/aws';
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
        if (document.getElementById('aws-s3-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'aws-s3-panel';
        panel.className = 'export-panel aws-panel';
        panel.innerHTML = `
            <div class="export-header aws-header">
                <h3>
                    <i class="fab fa-aws"></i>
                    Backup AWS S3
                </h3>
                <button class="btn-toggle" onclick="toggleAWSPanel()">
                    <i class="fas fa-chevron-down"></i>
                </button>
            </div>
            
            <div class="export-content" id="aws-export-content">
                <div class="export-status" id="aws-export-status">
                    <div class="status-item">
                        <span class="status-label">Status:</span>
                        <span class="status-value" id="aws-status-text">Carregando...</span>
                        <div class="status-indicator" id="aws-status-indicator"></div>
                    </div>
                    
                    <div class="status-item">
                        <span class="status-label">Bucket:</span>
                        <span class="status-value" id="aws-bucket-name">-</span>
                    </div>
                    
                    <div class="status-item">
                        <span class="status-label">Região:</span>
                        <span class="status-value" id="aws-region">-</span>
                    </div>
                    
                    <div class="status-item">
                        <span class="status-label">Intervalo:</span>
                        <span class="status-value" id="aws-interval-text">-</span>
                    </div>
                </div>
                
                <div class="export-controls">
                    <div class="control-group">
                        <label for="aws-export-interval">Intervalo (minutos):</label>
                        <input type="number" id="aws-export-interval" min="1" max="1440" value="5">
                        <button class="btn btn-secondary" onclick="updateAWSInterval()">
                            <i class="fas fa-save"></i> Salvar
                        </button>
                    </div>
                    
                    <div class="control-buttons">
                        <button class="btn btn-primary" onclick="manualAWSExport()" id="aws-manual-export-btn">
                            <i class="fas fa-cloud-upload-alt"></i> Backup Agora
                        </button>
                        
                        <button class="btn btn-success" onclick="startAWSAutoExport()" id="aws-start-btn">
                            <i class="fas fa-play"></i> Iniciar Auto
                        </button>
                        
                        <button class="btn btn-warning" onclick="stopAWSAutoExport()" id="aws-stop-btn">
                            <i class="fas fa-stop"></i> Parar Auto
                        </button>
                        
                        <button class="btn btn-info" onclick="testAWSConnection()" id="aws-test-btn">
                            <i class="fas fa-wifi"></i> Testar S3
                        </button>
                    </div>
                </div>
                
                <div class="export-formats">
                    <h4>Downloads Locais</h4>
                    <div class="format-buttons">
                        <button class="btn btn-outline" onclick="downloadAWSFormat('csv')">
                            <i class="fas fa-file-csv"></i> CSV
                        </button>
                        <button class="btn btn-outline" onclick="downloadAWSFormat('json')">
                            <i class="fas fa-file-code"></i> JSON
                        </button>
                        <button class="btn btn-outline" onclick="downloadAWSFormat('report')">
                            <i class="fas fa-file-alt"></i> Relatório
                        </button>
                    </div>
                </div>
                
                <div class="s3-files">
                    <h4>Arquivos no S3</h4>
                    <div class="s3-files-container" id="s3-files-container">
                        <div class="loading">Carregando arquivos...</div>
                    </div>
                    <button class="btn btn-outline btn-small" onclick="refreshS3Files()">
                        <i class="fas fa-sync"></i> Atualizar Lista
                    </button>
                </div>
                
                <div class="export-logs" id="aws-export-logs">
                    <h4>Log AWS S3</h4>
                    <div class="log-container" id="aws-log-container">
                        <div class="log-entry">
                            <span class="log-time">${new Date().toLocaleTimeString()}</span>
                            <span class="log-message">Painel AWS S3 inicializado</span>
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

        this.addAWSStyles();
    }

    addAWSStyles() {
        const styles = `
            .aws-panel {
                margin-top: 10px;
            }
            
            .aws-header {
                background: linear-gradient(135deg, #ff9900, #ff6600);
            }
            
            .s3-files {
                margin-bottom: 20px;
            }
            
            .s3-files h4 {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: 600;
                color: #4a5568;
            }
            
            .s3-files-container {
                background: #f8fafc;
                border-radius: 6px;
                padding: 10px;
                max-height: 200px;
                overflow-y: auto;
                margin-bottom: 10px;
            }
            
            .s3-file-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px;
                margin-bottom: 5px;
                background: white;
                border-radius: 4px;
                border: 1px solid #e2e8f0;
                font-size: 12px;
            }
            
            .s3-file-name {
                font-weight: 500;
                color: #2d3748;
                flex: 1;
                margin-right: 10px;
                word-break: break-all;
            }
            
            .s3-file-info {
                display: flex;
                gap: 10px;
                align-items: center;
                color: #718096;
                font-size: 11px;
            }
            
            .s3-file-size {
                min-width: 60px;
                text-align: right;
            }
            
            .s3-file-date {
                min-width: 80px;
                text-align: right;
            }
            
            .btn-small {
                padding: 6px 12px;
                font-size: 12px;
            }
            
            .loading {
                text-align: center;
                color: #718096;
                font-style: italic;
                padding: 20px;
            }
            
            .no-files {
                text-align: center;
                color: #718096;
                font-style: italic;
                padding: 20px;
            }
            
            .aws-config-info {
                background: #fff5f5;
                border: 1px solid #fed7d7;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 15px;
                font-size: 12px;
                color: #c53030;
            }
            
            .aws-config-info h5 {
                margin: 0 0 5px 0;
                font-size: 13px;
                font-weight: 600;
            }
            
            .aws-config-info ul {
                margin: 5px 0 0 15px;
                padding: 0;
            }
            
            .aws-config-info li {
                margin-bottom: 2px;
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    async loadStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/s3/status`);
            const data = await response.json();

            if (data.success) {
                this.updateStatusDisplay(data.status);
                if (data.status.enabled && data.status.service_available) {
                    this.loadS3Files();
                }
            } else {
                this.addLog('Erro ao carregar status AWS', 'error');
            }
        } catch (error) {
            this.addLog(`Erro de conexão AWS: ${error.message}`, 'error');
        }
    }

    updateStatusDisplay(status) {
        const statusText = document.getElementById('aws-status-text');
        const statusIndicator = document.getElementById('aws-status-indicator');
        const bucketName = document.getElementById('aws-bucket-name');
        const region = document.getElementById('aws-region');
        const intervalText = document.getElementById('aws-interval-text');

        if (statusText) {
            if (!status.enabled) {
                statusText.textContent = 'Desabilitado';
                statusIndicator.className = 'status-indicator offline';
                this.showConfigInfo();
            } else if (!status.service_available) {
                statusText.textContent = 'Erro Config';
                statusIndicator.className = 'status-indicator offline';
                this.showConfigInfo();
            } else if (status.running) {
                statusText.textContent = 'Executando';
                statusIndicator.className = 'status-indicator running';
                this.hideConfigInfo();
            } else {
                statusText.textContent = 'Parado';
                statusIndicator.className = 'status-indicator online';
                this.hideConfigInfo();
            }
        }

        if (bucketName) {
            bucketName.textContent = status.bucket_name || '-';
        }

        if (region) {
            region.textContent = status.region || '-';
        }

        if (intervalText) {
            intervalText.textContent = `${status.interval_minutes} min`;
        }

        // Atualizar campo de intervalo
        const intervalInput = document.getElementById('aws-export-interval');
        if (intervalInput) {
            intervalInput.value = status.interval_minutes;
        }
    }

    showConfigInfo() {
        // Remover info existente
        this.hideConfigInfo();

        const configInfo = document.createElement('div');
        configInfo.className = 'aws-config-info';
        configInfo.id = 'aws-config-info';
        configInfo.innerHTML = `
            <h5><i class="fas fa-exclamation-triangle"></i> Configuração AWS Necessária</h5>
            <p>Para ativar o backup automático, configure as variáveis:</p>
            <ul>
                <li><code>AWS_S3_ENABLED=true</code></li>
                <li><code>AWS_ACCESS_KEY_ID=sua_chave</code></li>
                <li><code>AWS_SECRET_ACCESS_KEY=sua_chave_secreta</code></li>
                <li><code>AWS_S3_BUCKET_NAME=nome_do_bucket</code></li>
                <li><code>AWS_S3_REGION=us-east-1</code></li>
            </ul>
        `;

        const statusDiv = document.getElementById('aws-export-status');
        if (statusDiv) {
            statusDiv.appendChild(configInfo);
        }
    }

    hideConfigInfo() {
        const configInfo = document.getElementById('aws-config-info');
        if (configInfo) {
            configInfo.remove();
        }
    }

    async loadS3Files() {
        try {
            const response = await fetch(`${this.baseUrl}/s3/list?limit=10`);
            const data = await response.json();

            const container = document.getElementById('s3-files-container');
            if (!container) return;

            if (data.success && data.files && data.files.length > 0) {
                container.innerHTML = '';
                data.files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 's3-file-item';
                    
                    const fileName = file.key.split('/').pop();
                    const fileSize = this.formatFileSize(file.size);
                    const fileDate = new Date(file.last_modified).toLocaleDateString();
                    
                    fileItem.innerHTML = `
                        <div class="s3-file-name" title="${file.key}">${fileName}</div>
                        <div class="s3-file-info">
                            <div class="s3-file-size">${fileSize}</div>
                            <div class="s3-file-date">${fileDate}</div>
                        </div>
                    `;
                    
                    container.appendChild(fileItem);
                });
            } else {
                container.innerHTML = '<div class="no-files">Nenhum arquivo encontrado</div>';
            }
        } catch (error) {
            const container = document.getElementById('s3-files-container');
            if (container) {
                container.innerHTML = '<div class="no-files">Erro ao carregar arquivos</div>';
            }
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    startStatusMonitoring() {
        // Atualizar status a cada 30 segundos
        this.statusInterval = setInterval(() => {
            this.loadStatus();
        }, 30000);
    }

    addLog(message, type = 'info') {
        const logContainer = document.getElementById('aws-log-container');
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
            this.addLog(`Erro de rede AWS: ${error.message}`, 'error');
            return { success: false, message: error.message };
        }
    }
}

// Instância global
let awsExportManager;

// Funções globais para os botões
function toggleAWSPanel() {
    const content = document.getElementById('aws-export-content');
    const toggle = document.querySelector('#aws-s3-panel .btn-toggle');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        toggle.classList.remove('collapsed');
    } else {
        content.classList.add('collapsed');
        toggle.classList.add('collapsed');
    }
}

async function manualAWSExport() {
    const btn = document.getElementById('aws-manual-export-btn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    btn.disabled = true;
    
    awsExportManager.addLog('Iniciando backup manual para AWS S3...', 'info');
    
    const result = await awsExportManager.makeRequest('/s3/manual', 'POST');
    
    if (result.success) {
        awsExportManager.addLog('Backup manual para AWS S3 concluído!', 'success');
        showNotification('Backup AWS S3 concluído com sucesso!', 'success');
        awsExportManager.loadS3Files(); // Atualizar lista de arquivos
    } else {
        awsExportManager.addLog(`Erro no backup: ${result.message}`, 'error');
        showNotification(`Erro no backup AWS: ${result.message}`, 'error');
    }
    
    btn.innerHTML = originalText;
    btn.disabled = false;
    
    awsExportManager.loadStatus();
}

async function startAWSAutoExport() {
    awsExportManager.addLog('Iniciando backup automático AWS S3...', 'info');
    
    const result = await awsExportManager.makeRequest('/s3/start', 'POST');
    
    if (result.success) {
        awsExportManager.addLog('Backup automático AWS S3 iniciado!', 'success');
        showNotification('Backup automático AWS S3 iniciado!', 'success');
    } else {
        awsExportManager.addLog(`Erro ao iniciar AWS: ${result.message}`, 'error');
        showNotification(`Erro ao iniciar AWS: ${result.message}`, 'error');
    }
    
    awsExportManager.loadStatus();
}

async function stopAWSAutoExport() {
    awsExportManager.addLog('Parando backup automático AWS S3...', 'warning');
    
    const result = await awsExportManager.makeRequest('/s3/stop', 'POST');
    
    if (result.success) {
        awsExportManager.addLog('Backup automático AWS S3 parado!', 'warning');
        showNotification('Backup automático AWS S3 parado!', 'info');
    } else {
        awsExportManager.addLog(`Erro ao parar AWS: ${result.message}`, 'error');
        showNotification(`Erro ao parar AWS: ${result.message}`, 'error');
    }
    
    awsExportManager.loadStatus();
}

async function testAWSConnection() {
    const btn = document.getElementById('aws-test-btn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testando...';
    btn.disabled = true;
    
    awsExportManager.addLog('Testando conexão com AWS S3...', 'info');
    
    const result = await awsExportManager.makeRequest('/s3/test', 'POST');
    
    if (result.success) {
        awsExportManager.addLog('Conexão com AWS S3 OK!', 'success');
        showNotification('Conexão com AWS S3 OK!', 'success');
    } else {
        awsExportManager.addLog(`Erro na conexão AWS: ${result.message}`, 'error');
        showNotification(`Erro na conexão AWS: ${result.message}`, 'error');
    }
    
    btn.innerHTML = originalText;
    btn.disabled = false;
}

async function updateAWSInterval() {
    const intervalInput = document.getElementById('aws-export-interval');
    const interval = parseInt(intervalInput.value);
    
    if (interval < 1 || interval > 1440) {
        showNotification('Intervalo deve ser entre 1 e 1440 minutos', 'error');
        return;
    }
    
    awsExportManager.addLog(`Atualizando intervalo AWS para ${interval} minutos...`, 'info');
    
    const result = await awsExportManager.makeRequest('/s3/config', 'POST', {
        interval_minutes: interval
    });
    
    if (result.success) {
        awsExportManager.addLog('Intervalo AWS atualizado!', 'success');
        showNotification('Intervalo AWS atualizado!', 'success');
    } else {
        awsExportManager.addLog(`Erro ao atualizar AWS: ${result.message}`, 'error');
        showNotification(`Erro ao atualizar AWS: ${result.message}`, 'error');
    }
    
    awsExportManager.loadStatus();
}

async function downloadAWSFormat(format) {
    awsExportManager.addLog(`Gerando arquivo ${format.toUpperCase()}...`, 'info');
    
    const result = await awsExportManager.makeRequest(`/formats/${format}`);
    
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
        
        awsExportManager.addLog(`Arquivo ${format.toUpperCase()} baixado!`, 'success');
        showNotification(`Arquivo ${format.toUpperCase()} baixado!`, 'success');
    } else {
        awsExportManager.addLog(`Erro ao gerar ${format}: ${result.message}`, 'error');
        showNotification(`Erro ao gerar ${format}: ${result.message}`, 'error');
    }
}

async function refreshS3Files() {
    awsExportManager.addLog('Atualizando lista de arquivos S3...', 'info');
    await awsExportManager.loadS3Files();
    awsExportManager.addLog('Lista de arquivos S3 atualizada!', 'success');
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Aguardar um pouco para garantir que outros scripts carregaram
    setTimeout(() => {
        awsExportManager = new AWSS3ExportManager();
    }, 1500);
});

// Limpar interval ao sair da página
window.addEventListener('beforeunload', () => {
    if (awsExportManager && awsExportManager.statusInterval) {
        clearInterval(awsExportManager.statusInterval);
    }
});
