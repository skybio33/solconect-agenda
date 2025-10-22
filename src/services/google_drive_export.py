"""
Serviço de Exportação Automática para Google Drive
Exporta dados do dashboard para Google Drive a cada 5 minutos
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

# Google Drive API
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

# Flask e modelos
from flask import current_app
from src.models.task import Task, db
from src.models.user import User

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveExporter:
    """Classe para gerenciar exportação automática para Google Drive"""
    
    def __init__(self, app=None):
        self.app = app
        self.service = None
        self.folder_id = None
        self.export_thread = None
        self.running = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar com aplicação Flask"""
        self.app = app
        
        # Configurações do Google Drive
        app.config.setdefault('GOOGLE_DRIVE_ENABLED', os.environ.get('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true')
        app.config.setdefault('GOOGLE_DRIVE_FOLDER_ID', os.environ.get('GOOGLE_DRIVE_FOLDER_ID'))
        app.config.setdefault('GOOGLE_SERVICE_ACCOUNT_KEY', os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY'))
        app.config.setdefault('EXPORT_INTERVAL_MINUTES', int(os.environ.get('EXPORT_INTERVAL_MINUTES', '5')))
        
        # Inicializar serviço se habilitado
        if app.config['GOOGLE_DRIVE_ENABLED']:
            self._init_google_service()
            self.start_auto_export()
    
    def _init_google_service(self):
        """Inicializar serviço do Google Drive"""
        try:
            # Obter credenciais do service account
            service_account_key = self.app.config.get('GOOGLE_SERVICE_ACCOUNT_KEY')
            
            if not service_account_key:
                logger.error("GOOGLE_SERVICE_ACCOUNT_KEY não configurado")
                return False
            
            # Parse das credenciais JSON
            if isinstance(service_account_key, str):
                credentials_info = json.loads(service_account_key)
            else:
                credentials_info = service_account_key
            
            # Criar credenciais
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            # Construir serviço
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Configurar pasta de destino
            self.folder_id = self.app.config.get('GOOGLE_DRIVE_FOLDER_ID')
            if not self.folder_id:
                self.folder_id = self._create_export_folder()
            
            logger.info("✅ Serviço Google Drive inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Google Drive: {e}")
            return False
    
    def _create_export_folder(self):
        """Criar pasta para exportações no Google Drive"""
        try:
            folder_metadata = {
                'name': 'Solconect Dashboard Exports',
                'mimeType': 'application/vnd.google-apps.folder',
                'description': 'Exportações automáticas do Dashboard Solconect'
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"✅ Pasta criada no Google Drive: {folder_id}")
            
            return folder_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar pasta no Google Drive: {e}")
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
RELATÓRIO DASHBOARD SOLCONECT
=============================
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

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

=============================
Exportação automática - Dashboard Solconect
"""
                
                logger.info("✅ Relatório resumo gerado")
                return report
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return ""
    
    def upload_to_drive(self, content: str, filename: str, mime_type: str) -> bool:
        """Upload de arquivo para Google Drive"""
        try:
            if not self.service:
                logger.error("Serviço Google Drive não inicializado")
                return False
            
            # Criar arquivo em memória
            file_stream = io.BytesIO(content.encode('utf-8'))
            
            # Metadados do arquivo
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            # Upload
            media = MediaIoBaseUpload(
                file_stream,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            logger.info(f"✅ Arquivo enviado: {filename} (ID: {file.get('id')})")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Erro HTTP ao enviar arquivo: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar arquivo: {e}")
            return False
    
    def perform_export(self):
        """Executar exportação completa"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            logger.info("🚀 Iniciando exportação automática...")
            
            # 1. Exportar CSV
            csv_content = self.export_tasks_to_csv()
            if csv_content:
                csv_filename = f"solconect_tasks_{timestamp}.csv"
                self.upload_to_drive(csv_content, csv_filename, 'text/csv')
            
            # 2. Exportar JSON
            json_content = self.export_tasks_to_json()
            if json_content:
                json_filename = f"solconect_backup_{timestamp}.json"
                self.upload_to_drive(json_content, json_filename, 'application/json')
            
            # 3. Gerar relatório resumo
            report_content = self.generate_summary_report()
            if report_content:
                report_filename = f"solconect_report_{timestamp}.txt"
                self.upload_to_drive(report_content, report_filename, 'text/plain')
            
            logger.info("✅ Exportação automática concluída com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro na exportação automática: {e}")
    
    def export_worker(self):
        """Worker thread para exportação automática"""
        interval_minutes = self.app.config.get('EXPORT_INTERVAL_MINUTES', 5)
        interval_seconds = interval_minutes * 60
        
        logger.info(f"🔄 Exportação automática iniciada (intervalo: {interval_minutes} minutos)")
        
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
        if not self.app.config.get('GOOGLE_DRIVE_ENABLED'):
            logger.info("⚠️ Exportação Google Drive desabilitada")
            return
        
        if not self.service:
            logger.error("❌ Serviço Google Drive não disponível")
            return
        
        if self.export_thread and self.export_thread.is_alive():
            logger.warning("⚠️ Exportação automática já está rodando")
            return
        
        self.running = True
        self.export_thread = threading.Thread(target=self.export_worker, daemon=True)
        self.export_thread.start()
        
        logger.info("✅ Exportação automática iniciada")
    
    def stop_auto_export(self):
        """Parar exportação automática"""
        self.running = False
        
        if self.export_thread and self.export_thread.is_alive():
            self.export_thread.join(timeout=5)
        
        logger.info("🛑 Exportação automática parada")
    
    def manual_export(self):
        """Executar exportação manual"""
        if not self.service:
            return {"success": False, "message": "Serviço Google Drive não disponível"}
        
        try:
            self.perform_export()
            return {"success": True, "message": "Exportação manual concluída com sucesso"}
        except Exception as e:
            logger.error(f"❌ Erro na exportação manual: {e}")
            return {"success": False, "message": f"Erro na exportação: {str(e)}"}
    
    def get_status(self):
        """Obter status da exportação automática"""
        return {
            "enabled": self.app.config.get('GOOGLE_DRIVE_ENABLED', False),
            "running": self.running,
            "service_available": self.service is not None,
            "folder_id": self.folder_id,
            "interval_minutes": self.app.config.get('EXPORT_INTERVAL_MINUTES', 5)
        }

# Instância global
drive_exporter = GoogleDriveExporter()
