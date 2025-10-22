# 🚀 Configuração da Exportação Automática para Google Drive

Este guia explica como configurar a exportação automática dos dados do Dashboard Solconect para o Google Drive a cada 5 minutos.

## 📋 Pré-requisitos

1. Conta Google ativa
2. Projeto no Google Cloud Console
3. Dashboard Solconect implantado no Railway

## 🔧 Passo 1: Configurar Google Cloud Console

### 1.1 Criar Projeto
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em "Novo Projeto"
3. Nome: `Solconect Dashboard Export`
4. Clique em "Criar"

### 1.2 Ativar Google Drive API
1. No menu lateral, vá em "APIs e Serviços" > "Biblioteca"
2. Pesquise por "Google Drive API"
3. Clique em "Google Drive API"
4. Clique em "Ativar"

### 1.3 Criar Service Account
1. Vá em "APIs e Serviços" > "Credenciais"
2. Clique em "Criar Credenciais" > "Conta de serviço"
3. Nome: `solconect-export-service`
4. Descrição: `Serviço para exportação automática do Dashboard Solconect`
5. Clique em "Criar e continuar"
6. Função: `Editor` (ou crie uma função personalizada com acesso ao Drive)
7. Clique em "Concluir"

### 1.4 Gerar Chave JSON
1. Na lista de contas de serviço, clique na conta criada
2. Vá na aba "Chaves"
3. Clique em "Adicionar chave" > "Criar nova chave"
4. Selecione "JSON"
5. Clique em "Criar"
6. **Salve o arquivo JSON baixado** (você precisará dele)

## 📁 Passo 2: Configurar Pasta no Google Drive

### 2.1 Criar Pasta de Destino
1. Acesse [Google Drive](https://drive.google.com/)
2. Clique em "Novo" > "Pasta"
3. Nome: `Solconect Dashboard Exports`
4. Clique em "Criar"

### 2.2 Compartilhar com Service Account
1. Clique com botão direito na pasta criada
2. Selecione "Compartilhar"
3. No campo "Adicionar pessoas e grupos", cole o email da service account
   - Encontre o email no arquivo JSON baixado (campo `client_email`)
   - Exemplo: `solconect-export-service@projeto-123456.iam.gserviceaccount.com`
4. Permissão: "Editor"
5. Clique em "Enviar"

### 2.3 Obter ID da Pasta
1. Abra a pasta no Google Drive
2. Copie o ID da URL (parte após `/folders/`)
   - Exemplo: `https://drive.google.com/drive/folders/1ABC123xyz...`
   - ID: `1ABC123xyz...`

## ⚙️ Passo 3: Configurar Variáveis de Ambiente no Railway

### 3.1 Acessar Railway
1. Faça login no [Railway](https://railway.app/)
2. Acesse seu projeto do Dashboard Solconect
3. Vá na aba "Variables"

### 3.2 Adicionar Variáveis
Adicione as seguintes variáveis de ambiente:

```bash
# Habilitar exportação Google Drive
GOOGLE_DRIVE_ENABLED=true

# ID da pasta no Google Drive
GOOGLE_DRIVE_FOLDER_ID=1ABC123xyz...

# Intervalo de exportação em minutos (padrão: 5)
EXPORT_INTERVAL_MINUTES=5

# Chave da Service Account (conteúdo completo do arquivo JSON)
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"..."}
```

### 3.3 Configurar GOOGLE_SERVICE_ACCOUNT_KEY
1. Abra o arquivo JSON baixado no Passo 1.4
2. Copie **todo o conteúdo** do arquivo
3. Cole como valor da variável `GOOGLE_SERVICE_ACCOUNT_KEY`
4. **Importante**: Cole o JSON completo em uma única linha

Exemplo:
```json
{"type":"service_account","project_id":"projeto-123456","private_key_id":"abc123","private_key":"-----BEGIN PRIVATE KEY-----\n...","client_email":"solconect-export-service@projeto-123456.iam.gserviceaccount.com","client_id":"123456789","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/solconect-export-service%40projeto-123456.iam.gserviceaccount.com"}
```

## 🚀 Passo 4: Deploy e Teste

### 4.1 Fazer Deploy
1. No Railway, clique em "Deploy"
2. Aguarde o deploy ser concluído
3. Verifique os logs para confirmar que não há erros

### 4.2 Testar Funcionalidade
1. Acesse seu dashboard
2. Procure pelo painel "Exportação Google Drive" na lateral
3. Clique em "Testar" para verificar a conexão
4. Clique em "Exportar Agora" para fazer uma exportação manual
5. Verifique se os arquivos aparecem na pasta do Google Drive

## 📊 Funcionalidades da Exportação

### Arquivos Gerados
A cada exportação, são criados 3 arquivos:

1. **CSV** (`solconect_tasks_YYYYMMDD_HHMMSS.csv`)
   - Dados das tarefas em formato planilha
   - Compatível com Excel, Google Sheets

2. **JSON** (`solconect_backup_YYYYMMDD_HHMMSS.json`)
   - Backup completo dos dados
   - Inclui metadados e timestamp

3. **Relatório** (`solconect_report_YYYYMMDD_HHMMSS.txt`)
   - Resumo executivo
   - Estatísticas por fase e área
   - Resumo financeiro

### Controles Disponíveis
- **Exportar Agora**: Exportação manual imediata
- **Iniciar Auto**: Ativar exportação automática
- **Parar Auto**: Desativar exportação automática
- **Testar**: Verificar conexão com Google Drive
- **Configurar Intervalo**: Alterar frequência (1-1440 minutos)

## 🔧 Configurações Avançadas

### Alterar Intervalo de Exportação
```bash
# Exportar a cada 10 minutos
EXPORT_INTERVAL_MINUTES=10

# Exportar a cada hora
EXPORT_INTERVAL_MINUTES=60

# Exportar a cada 6 horas
EXPORT_INTERVAL_MINUTES=360
```

### Desabilitar Exportação
```bash
GOOGLE_DRIVE_ENABLED=false
```

### Logs e Monitoramento
- Logs em tempo real no painel do dashboard
- Status da conexão com indicadores visuais
- Histórico das últimas 50 atividades

## 🛠️ Solução de Problemas

### Erro: "Serviço Google Drive não inicializado"
- Verifique se `GOOGLE_SERVICE_ACCOUNT_KEY` está configurado corretamente
- Confirme que o JSON está em uma única linha
- Verifique se a Google Drive API está ativada

### Erro: "Pasta não encontrada"
- Confirme o `GOOGLE_DRIVE_FOLDER_ID`
- Verifique se a pasta foi compartilhada com a service account
- Teste com uma pasta diferente

### Erro: "Permissão negada"
- Verifique as permissões da service account
- Confirme que a pasta foi compartilhada como "Editor"
- Recrie a service account se necessário

### Exportação não está funcionando
- Verifique se `GOOGLE_DRIVE_ENABLED=true`
- Confirme que o intervalo está configurado corretamente
- Verifique os logs do Railway para erros

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs no Railway
2. Teste a conexão no painel do dashboard
3. Confirme todas as variáveis de ambiente
4. Recrie a service account se necessário

## 🔒 Segurança

- A chave da service account é sensível - mantenha segura
- Use permissões mínimas necessárias
- Monitore o acesso aos arquivos no Google Drive
- Considere rotacionar as chaves periodicamente

## 📈 Benefícios

✅ **Backup Automático**: Dados salvos a cada 5 minutos
✅ **Múltiplos Formatos**: CSV, JSON e relatórios
✅ **Acesso Remoto**: Dados disponíveis no Google Drive
✅ **Histórico Completo**: Versões timestamped dos dados
✅ **Integração Simples**: Configuração via variáveis de ambiente
✅ **Monitoramento**: Interface visual para controle e status

---

**🎉 Pronto!** Sua exportação automática para Google Drive está configurada e funcionando!
