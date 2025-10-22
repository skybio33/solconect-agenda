"""
Serviço de Exportação Automática para AWS S3
Exporta dados do dashboard para Amazon S3 a cada 5 minutos
"""

import os
import json
import csv
import io
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# AWS SDK
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Flask e modelos
from flask import current_app
from src.models.task import Task, db
from src.models.user import User

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSS3Exporter:
    """Classe para gerenciar exportação automática para AWS S3"""
    
    def __init__(self, app=None):
        self.app = app
        self.s3_client = None
        self.bucket_name = None
        self.export_thread = None
        self.running = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar com aplicação Flask"""
        self.app = app
        
        # Configurações da AWS
        app.config.setdefault('AWS_S3_ENABLED', os.environ.get('AWS_S3_ENABLED', 'false').lower() == 'true')
        app.config.setdefault('AWS_ACCESS_KEY_ID', os.environ.get('AWS_ACCESS_KEY_ID'))
        app.config.setdefault('AWS_SECRET_ACCESS_KEY', os.environ.get('AWS_SECRET_ACCESS_KEY'))
        app.config.setdefault('AWS_S3_BUCKET_NAME', os.environ.get('AWS_S3_BUCKET_NAME'))
        app.config.setdefault('AWS_S3_REGION', os.environ.get('AWS_S3_REGION', 'us-east-1'))
        app.config.setdefault('EXPORT_INTERVAL_MINUTES', int(os.environ.get('EXPORT_INTERVAL_MINUTES', '5')))
        
        # Inicializar serviço se habilitado
        if app.config['AWS_S3_ENABLED']:
            self._init_aws_service()
            self.start_auto_export()
    
    def _init_aws_service(self):
        """Inicializar serviço da AWS S3"""
        try:
            # Obter credenciais
            access_key = self.app.config.get('AWS_ACCESS_KEY_ID')
            secret_key = self.app.config.get('AWS_SECRET_ACCESS_KEY')
            region = self.app.config.get('AWS_S3_REGION')
            
            if not access_key or not secret_key:
                logger.error("Credenciais AWS não configuradas")
                return False
            
            # Criar cliente S3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Configurar bucket
            self.bucket_name = self.app.config.get('AWS_S3_BUCKET_NAME')
            if not self.bucket_name:
                self.bucket_name = self._create_bucket()
            
            # Testar conexão
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            logger.info("✅ Serviço AWS S3 inicializado com sucesso")
            return True
            
        except NoCredentialsError:
            logger.error("❌ Credenciais AWS não encontradas")
            return False
        except ClientError as e:
            logger.error(f"❌ Erro ao conectar com AWS S3: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar AWS S3: {e}")
            return False
    
    def _create_bucket(self):
        """Criar bucket S3 para exportações"""
        try:
            bucket_name = f"solconect-dashboard-exports-{int(time.time())}"
            region = self.app.config.get('AWS_S3_REGION')
            
            if region == 'us-east-1':
                # us-east-1 não precisa de LocationConstraint
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            # Configurar versionamento
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configurar lifecycle para limpeza automática
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'DeleteOldVersions',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'exports/'},
                        'NoncurrentVersionExpiration': {'NoncurrentDays': 30}
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            logger.info(f"✅ Bucket S3 criado: {bucket_name}")
            return bucket_name
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar bucket S3: {e}")
            return None
    
    def export_tasks_to_csv(self) -> str:
        """Exportar tarefas para formato CSV"""
        try:
            with self.app.app_context():
                # Buscar todas as tarefas
                tasks = Task.query.all()
                
                # Criar CSV em memória
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Cabeçalhos
                headers = [
                    'ID', 'Título', 'Cliente', 'Descrição', 'Área de Negócio',
                    'Fase', 'Responsável', 'Prazo', 'Preço Compra', 'Preço Venda',
                    'Margem Markup', 'Criado em', 'Atualizado em'
                ]
                writer.writerow(headers)
                
                # Dados das tarefas
                for task in tasks:
                    row = [
                        task.id,
                        task.title,
                        task.client or '',
                        task.description or '',
                        task.business_area,
                        task.phase,
                        task.responsible or '',
                        task.deadline or '',
                        task.purchase_price,
                        task.sale_price,
                        task.markup_margin,
                        task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else '',
                        task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else ''
                    ]
                    writer.writerow(row)
                
                csv_content = output.getvalue()
                output.close()
                
                logger.info(f"✅ CSV gerado com {len(tasks)} tarefas")
                return csv_content
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar CSV: {e}")
            return ""
    
    def export_tasks_to_json(self) -> str:
        """Exportar tarefas para formato JSON"""
        try:
            with self.app.app_context():
                # Buscar todas as tarefas
                tasks = Task.query.all()
                
                # Converter para dicionários
                tasks_data = [task.to_dict() for task in tasks]
                
                # Adicionar metadados
                export_data = {
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'total_tasks': len(tasks_data),
                    'dashboard_version': '1.0.0',
                    'export_location': 'AWS S3',
                    'bucket_name': self.bucket_name,
                    'tasks': tasks_data
                }
                
                json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ JSON gerado com {len(tasks)} tarefas")
                return json_content
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar JSON: {e}")
            return ""
    
    def generate_summary_report(self) -> str:
        """Gerar relatório resumo em texto"""
        try:
            with self.app.app_context():
                # Estatísticas das tarefas
                total_tasks = Task.query.count()
                
                # Tarefas por fase
                phases = ['prospeccao', 'proposta', 'execucao', 'pos-venda']
                phase_names = {
                    'prospeccao': 'Prospecção e Geração de Leads',
                    'proposta': 'Proposta e Negociação',
                    'execucao': 'Execução e Entrega',
                    'pos-venda': 'Pós-Venda e Relacionamento'
                }
                
                phase_stats = {}
                for phase in phases:
                    count = Task.query.filter_by(phase=phase).count()
                    phase_stats[phase] = count
                
                # Tarefas por área de negócio
                business_areas = ['solvente', 'solar', 'eletricos', 'servicos-eletricos', 'mercado-livre']
                area_names = {
                    'solvente': 'Solvente Dielétrico',
                    'solar': 'Energia Solar',
                    'eletricos': 'Produtos Elétricos',
                    'servicos-eletricos': 'Serviços Elétricos',
                    'mercado-livre': 'Mercado Livre de Energia'
                }
                
                area_stats = {}
                for area in business_areas:
                    count = Task.query.filter_by(business_area=area).count()
                    area_stats[area] = count
                
                # Valores financeiros
                total_purchase = db.session.query(db.func.sum(Task.purchase_price)).scalar() or 0
                total_sale = db.session.query(db.func.sum(Task.sale_price)).scalar() or 0
                total_profit = total_sale - total_purchase
                
                # Gerar relatório
                report = f"""
RELATÓRIO DASHBOARD SOLCONECT - AWS S3 BACKUP
============================================
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Bucket S3: {self.bucket_name}
Região AWS: {self.app.config.get('AWS_S3_REGION')}

RESUMO GERAL
------------
Total de Tarefas: {total_tasks}

DISTRIBUIÇÃO POR FASE
--------------------
"""
                
                for phase, count in phase_stats.items():
                    percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
                    report += f"{phase_names[phase]}: {count} ({percentage:.1f}%)\n"
                
                report += f"""
DISTRIBUIÇÃO POR ÁREA DE NEGÓCIO
-------------------------------
"""
                
                for area, count in area_stats.items():
                    percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
                    report += f"{area_names.get(area, area)}: {count} ({percentage:.1f}%)\n"
                
                report += f"""
RESUMO FINANCEIRO
----------------
Total Investido: R$ {total_purchase:,.2f}
Total Faturamento: R$ {total_sale:,.2f}
Lucro Bruto: R$ {total_profit:,.2f}
Margem Média: {(total_profit/total_purchase*100) if total_purchase > 0 else 0:.1f}%

INFORMAÇÕES DO BACKUP
--------------------
Localização: Amazon S3
Bucket: {self.bucket_name}
Versionamento: Habilitado
Retenção: 30 dias para versões antigas
Região: {self.app.config.get('AWS_S3_REGION')}

============================================
Backup automático - Dashboard Solconect
Powered by AWS S3
"""
                
                logger.info("✅ Relatório resumo gerado")
                return report
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return ""
    
    def upload_to_s3(self, content: str, key: str, content_type: str = 'text/plain') -> bool:
        """Upload de arquivo para S3"""
        try:
            if not self.s3_client:
                logger.error("Cliente S3 não inicializado")
                return False
            
            # Upload do arquivo
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                Metadata={
                    'dashboard': 'solconect',
                    'export_time': datetime.utcnow().isoformat(),
                    'version': '1.0.0'
                }
            )
            
            logger.info(f"✅ Arquivo enviado para S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Erro ao enviar para S3: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            return False
    
    def perform_export(self):
        """Executar exportação completa"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            date_folder = datetime.now().strftime('%Y/%m/%d')
            
            logger.info("🚀 Iniciando exportação automática para AWS S3...")
            
            # 1. Exportar CSV
            csv_content = self.export_tasks_to_csv()
            if csv_content:
                csv_key = f"exports/{date_folder}/solconect_tasks_{timestamp}.csv"
                self.upload_to_s3(csv_content, csv_key, 'text/csv')
            
            # 2. Exportar JSON
            json_content = self.export_tasks_to_json()
            if json_content:
                json_key = f"exports/{date_folder}/solconect_backup_{timestamp}.json"
                self.upload_to_s3(json_content, json_key, 'application/json')
            
            # 3. Gerar relatório resumo
            report_content = self.generate_summary_report()
            if report_content:
                report_key = f"reports/{date_folder}/solconect_report_{timestamp}.txt"
                self.upload_to_s3(report_content, report_key, 'text/plain')
            
            # 4. Criar arquivo de índice (latest)
            index_content = json.dumps({
                'last_export': datetime.utcnow().isoformat(),
                'files': {
                    'csv': csv_key if csv_content else None,
                    'json': json_key if json_content else None,
                    'report': report_key if report_content else None
                },
                'bucket': self.bucket_name,
                'total_tasks': Task.query.count() if self.app else 0
            }, indent=2)
            
            self.upload_to_s3(index_content, 'latest/index.json', 'application/json')
            
            logger.info("✅ Exportação automática para AWS S3 concluída com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro na exportação automática: {e}")
    
    def export_worker(self):
        """Worker thread para exportação automática"""
        interval_minutes = self.app.config.get('EXPORT_INTERVAL_MINUTES', 5)
        interval_seconds = interval_minutes * 60
        
        logger.info(f"🔄 Exportação automática AWS S3 iniciada (intervalo: {interval_minutes} minutos)")
        
        while self.running:
            try:
                # Aguardar intervalo
                time.sleep(interval_seconds)
                
                if self.running:  # Verificar se ainda está rodando
                    self.perform_export()
                    
            except Exception as e:
                logger.error(f"❌ Erro no worker de exportação: {e}")
                time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    def start_auto_export(self):
        """Iniciar exportação automática"""
        if not self.app.config.get('AWS_S3_ENABLED'):
            logger.info("⚠️ Exportação AWS S3 desabilitada")
            return
        
        if not self.s3_client:
            logger.error("❌ Cliente S3 não disponível")
            return
        
        if self.export_thread and self.export_thread.is_alive():
            logger.warning("⚠️ Exportação automática já está rodando")
            return
        
        self.running = True
        self.export_thread = threading.Thread(target=self.export_worker, daemon=True)
        self.export_thread.start()
        
        logger.info("✅ Exportação automática AWS S3 iniciada")
    
    def stop_auto_export(self):
        """Parar exportação automática"""
        self.running = False
        
        if self.export_thread and self.export_thread.is_alive():
            self.export_thread.join(timeout=5)
        
        logger.info("🛑 Exportação automática AWS S3 parada")
    
    def manual_export(self):
        """Executar exportação manual"""
        if not self.s3_client:
            return {"success": False, "message": "Cliente S3 não disponível"}
        
        try:
            self.perform_export()
            return {"success": True, "message": "Exportação manual para AWS S3 concluída com sucesso"}
        except Exception as e:
            logger.error(f"❌ Erro na exportação manual: {e}")
            return {"success": False, "message": f"Erro na exportação: {str(e)}"}
    
    def list_exports(self, limit=10):
        """Listar últimas exportações"""
        try:
            if not self.s3_client:
                return {"success": False, "message": "Cliente S3 não disponível"}
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='exports/',
                MaxKeys=limit
            )
            
            files = []
            if 'Contents' in response:
                for obj in sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True):
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'url': f"https://{self.bucket_name}.s3.{self.app.config.get('AWS_S3_REGION')}.amazonaws.com/{obj['Key']}"
                    })
            
            return {"success": True, "files": files}
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar exportações: {e}")
            return {"success": False, "message": str(e)}
    
    def get_status(self):
        """Obter status da exportação automática"""
        return {
            "enabled": self.app.config.get('AWS_S3_ENABLED', False),
            "running": self.running,
            "service_available": self.s3_client is not None,
            "bucket_name": self.bucket_name,
            "region": self.app.config.get('AWS_S3_REGION'),
            "interval_minutes": self.app.config.get('EXPORT_INTERVAL_MINUTES', 5)
        }

# Instância global
s3_exporter = AWSS3Exporter()
