# 🚀 Configuração do Backup Automático AWS S3

Este guia explica como configurar o backup automático dos dados do Dashboard Solconect para Amazon S3 a cada 5 minutos.

## 📋 Pré-requisitos

1. Conta AWS ativa
2. Dashboard Solconect implantado no Railway
3. Acesso ao console AWS

## 💰 Custos Estimados

### AWS S3 (Região us-east-1)
- **Armazenamento**: $0.023 por GB/mês
- **Requisições PUT**: $0.0005 por 1.000 requisições
- **Requisições GET**: $0.0004 por 1.000 requisições
- **Transferência de dados**: Primeiros 100 GB gratuitos/mês

### Estimativa para Dashboard Solconect
- **Arquivos por mês**: ~8.640 (3 arquivos a cada 5 min)
- **Tamanho médio**: ~50 KB por backup
- **Armazenamento mensal**: ~430 MB
- **Custo estimado**: **$0.50 - $2.00/mês**

## 🔧 Passo 1: Configurar AWS IAM

### 1.1 Criar Usuário IAM
1. Acesse [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Clique em "Users" > "Create user"
3. Nome: `solconect-s3-backup`
4. Selecione "Programmatic access"
5. Clique em "Next"

### 1.2 Criar Política Personalizada
1. Na tela de permissões, clique em "Attach policies directly"
2. Clique em "Create policy"
3. Selecione a aba "JSON"
4. Cole a política abaixo:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetBucketVersioning",
                "s3:PutBucketVersioning",
                "s3:PutBucketLifecycleConfiguration"
            ],
            "Resource": "arn:aws:s3:::solconect-dashboard-exports-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListObjectVersions",
                "s3:DeleteObjectVersion"
            ],
            "Resource": "arn:aws:s3:::solconect-dashboard-exports-*/*"
        }
    ]
}
```

5. Clique em "Next" > "Review"
6. Nome da política: `SolconectS3BackupPolicy`
7. Clique em "Create policy"

### 1.3 Anexar Política ao Usuário
1. Volte para a criação do usuário
2. Pesquise por `SolconectS3BackupPolicy`
3. Selecione a política criada
4. Clique em "Next" > "Create user"

### 1.4 Obter Credenciais
1. Na tela de confirmação, clique em "Download .csv"
2. **Guarde o arquivo CSV com segurança**
3. Anote:
   - **Access Key ID**: AKIA...
   - **Secret Access Key**: wJalrXUt...

## 🪣 Passo 2: Configurar Bucket S3 (Opcional)

O sistema pode criar o bucket automaticamente, mas você pode criar manualmente:

### 2.1 Criar Bucket
1. Acesse [AWS S3 Console](https://console.aws.amazon.com/s3/)
2. Clique em "Create bucket"
3. Nome: `solconect-dashboard-exports-YYYYMMDD` (substitua pela data)
4. Região: `us-east-1` (recomendado para menor custo)
5. Mantenha configurações padrão
6. Clique em "Create bucket"

### 2.2 Configurar Versionamento
1. Clique no bucket criado
2. Vá na aba "Properties"
3. Em "Bucket Versioning", clique em "Edit"
4. Selecione "Enable"
5. Clique em "Save changes"

### 2.3 Configurar Lifecycle (Opcional)
Para limpar versões antigas automaticamente:

1. Vá na aba "Management"
2. Clique em "Create lifecycle rule"
3. Nome: `DeleteOldVersions`
4. Status: `Enabled`
5. Em "Filter", adicione prefixo: `exports/`
6. Em "Lifecycle rule actions", selecione:
   - "Delete noncurrent versions of objects"
7. Dias: `30`
8. Clique em "Create rule"

## ⚙️ Passo 3: Configurar Variáveis no Railway

### 3.1 Acessar Railway
1. Faça login no [Railway](https://railway.app/)
2. Acesse seu projeto do Dashboard Solconect
3. Vá na aba "Variables"

### 3.2 Adicionar Variáveis AWS
Adicione as seguintes variáveis de ambiente:

```bash
# Habilitar backup AWS S3
AWS_S3_ENABLED=true

# Credenciais AWS (do arquivo CSV baixado)
AWS_ACCESS_KEY_ID=AKIA1234567890EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Configurações do bucket
AWS_S3_BUCKET_NAME=solconect-dashboard-exports-20241210
AWS_S3_REGION=us-east-1

# Intervalo de backup em minutos (padrão: 5)
EXPORT_INTERVAL_MINUTES=5
```

### 3.3 Exemplo de Configuração
```
AWS_S3_ENABLED=true
AWS_ACCESS_KEY_ID=AKIA1234567890EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET_NAME=solconect-dashboard-exports-20241210
AWS_S3_REGION=us-east-1
EXPORT_INTERVAL_MINUTES=5
```

## 🚀 Passo 4: Deploy e Teste

### 4.1 Fazer Deploy
1. No Railway, clique em "Deploy"
2. Aguarde o deploy ser concluído
3. Verifique os logs para confirmar inicialização:
   ```
   ✅ Serviço de exportação AWS S3 inicializado
   ```

### 4.2 Testar Funcionalidade
1. Acesse seu dashboard: https://77h9ikc68xpz.manus.space
2. Procure pelo painel "Backup AWS S3" na lateral
3. Clique em "Testar S3" para verificar a conexão
4. Clique em "Backup Agora" para fazer um backup manual
5. Verifique se os arquivos aparecem no bucket S3

## 📊 Funcionalidades do Backup AWS S3

### Arquivos Gerados
A cada backup, são criados 3 arquivos organizados por data:

```
exports/
├── 2024/12/10/
│   ├── solconect_tasks_20241210_143000.csv
│   ├── solconect_backup_20241210_143000.json
│   └── solconect_report_20241210_143000.txt
└── 2024/12/10/
    ├── solconect_tasks_20241210_143500.csv
    ├── solconect_backup_20241210_143500.json
    └── solconect_report_20241210_143500.txt

reports/
└── 2024/12/10/
    └── solconect_report_20241210_143000.txt

latest/
└── index.json (índice dos últimos arquivos)
```

### Controles Disponíveis
- **Backup Agora**: Backup manual imediato
- **Iniciar Auto**: Ativar backup automático
- **Parar Auto**: Desativar backup automático
- **Testar S3**: Verificar conexão com AWS
- **Configurar Intervalo**: Alterar frequência (1-1440 minutos)
- **Lista de Arquivos**: Ver últimos 10 backups no S3

### Metadados dos Arquivos
Cada arquivo no S3 inclui metadados:
- `dashboard`: solconect
- `export_time`: timestamp UTC
- `version`: 1.0.0

## 🔧 Configurações Avançadas

### Alterar Região AWS
```bash
# Para São Paulo (menor latência do Brasil)
AWS_S3_REGION=sa-east-1

# Para Virginia (menor custo)
AWS_S3_REGION=us-east-1
```

### Alterar Intervalo de Backup
```bash
# Backup a cada 10 minutos
EXPORT_INTERVAL_MINUTES=10

# Backup a cada hora
EXPORT_INTERVAL_MINUTES=60

# Backup a cada 6 horas
EXPORT_INTERVAL_MINUTES=360
```

### Desabilitar Backup
```bash
AWS_S3_ENABLED=false
```

### Bucket Personalizado
```bash
# Use seu próprio bucket
AWS_S3_BUCKET_NAME=meu-bucket-personalizado
```

## 🛠️ Solução de Problemas

### Erro: "Cliente S3 não inicializado"
- Verifique se `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` estão configurados
- Confirme que as credenciais estão corretas
- Verifique se `AWS_S3_ENABLED=true`

### Erro: "Bucket não encontrado"
- Confirme o nome do bucket em `AWS_S3_BUCKET_NAME`
- Verifique se o bucket existe na região especificada
- Teste com um bucket diferente

### Erro: "Permissão negada"
- Verifique se a política IAM está correta
- Confirme que o usuário tem as permissões necessárias
- Recrie o usuário IAM se necessário

### Backup não está funcionando
- Verifique se `AWS_S3_ENABLED=true`
- Confirme que o intervalo está configurado corretamente
- Verifique os logs do Railway para erros
- Teste a conexão manualmente

### Arquivos não aparecem no S3
- Verifique se está olhando a região correta
- Confirme o nome do bucket
- Aguarde alguns minutos (pode haver delay)
- Verifique os logs de erro

## 📈 Monitoramento e Logs

### Logs em Tempo Real
- Painel do dashboard mostra últimas 50 atividades
- Status da conexão com indicadores visuais
- Informações de bucket e região
- Lista dos últimos arquivos enviados

### Logs do Railway
```
✅ Serviço de exportação AWS S3 inicializado
🚀 Iniciando exportação automática para AWS S3...
✅ Arquivo enviado para S3: exports/2024/12/10/solconect_tasks_20241210_143000.csv
✅ Exportação automática para AWS S3 concluída com sucesso!
```

### Monitoramento AWS
- CloudWatch para métricas de uso
- S3 Access Logs para auditoria
- Billing Dashboard para custos

## 🔒 Segurança

### Boas Práticas
- Use credenciais IAM específicas (não root)
- Aplique princípio do menor privilégio
- Monitore acessos via CloudTrail
- Rotacione credenciais periodicamente

### Criptografia
- S3 usa criptografia AES-256 por padrão
- Dados em trânsito protegidos via HTTPS
- Metadados não contêm informações sensíveis

### Controle de Acesso
- Bucket privado por padrão
- Acesso apenas via credenciais IAM
- Versionamento para recuperação
- Lifecycle rules para limpeza automática

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs no Railway
2. Teste a conexão no painel do dashboard
3. Confirme todas as variáveis de ambiente
4. Verifique permissões IAM
5. Teste com bucket diferente se necessário

## 💡 Dicas de Otimização

### Reduzir Custos
- Use região `us-east-1` (mais barata)
- Configure lifecycle rules para deletar versões antigas
- Monitore uso via AWS Billing Dashboard

### Melhorar Performance
- Use região mais próxima para menor latência
- Configure CloudFront se precisar de acesso global
- Use S3 Transfer Acceleration se necessário

### Organização
- Mantenha estrutura de pastas por data
- Use tags nos objetos para categorização
- Configure notificações S3 se necessário

## 🎉 Benefícios

✅ **Backup Automático**: Dados salvos a cada 5 minutos
✅ **Alta Durabilidade**: 99.999999999% (11 9's) de durabilidade
✅ **Versionamento**: Histórico completo de mudanças
✅ **Escalabilidade**: Cresce automaticamente com seus dados
✅ **Custo Baixo**: Apenas $0.50-2.00/mês
✅ **Acesso Global**: Disponível de qualquer lugar
✅ **Integração**: API completa para automação

---

**🚀 Pronto!** Seu backup automático para AWS S3 está configurado e funcionando!
