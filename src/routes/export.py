"""
Rotas para gerenciar exportação automática para Google Drive
"""

from flask import Blueprint, request, jsonify
from src.services.google_drive_export import drive_exporter
import logging

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)

@export_bp.route('/google-drive/status', methods=['GET'])
def get_export_status():
    """Obter status da exportação automática"""
    try:
        status = drive_exporter.get_status()
        return jsonify({
            "success": True,
            "status": status
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao obter status: {str(e)}"
        }), 500

@export_bp.route('/google-drive/manual', methods=['POST'])
def manual_export():
    """Executar exportação manual"""
    try:
        result = drive_exporter.manual_export()
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Erro na exportação manual: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro na exportação manual: {str(e)}"
        }), 500

@export_bp.route('/google-drive/start', methods=['POST'])
def start_auto_export():
    """Iniciar exportação automática"""
    try:
        drive_exporter.start_auto_export()
        
        return jsonify({
            "success": True,
            "message": "Exportação automática iniciada"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao iniciar exportação: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao iniciar exportação: {str(e)}"
        }), 500

@export_bp.route('/google-drive/stop', methods=['POST'])
def stop_auto_export():
    """Parar exportação automática"""
    try:
        drive_exporter.stop_auto_export()
        
        return jsonify({
            "success": True,
            "message": "Exportação automática parada"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao parar exportação: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao parar exportação: {str(e)}"
        }), 500

@export_bp.route('/google-drive/config', methods=['POST'])
def update_export_config():
    """Atualizar configurações de exportação"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados não fornecidos"
            }), 400
        
        # Validar intervalo
        interval = data.get('interval_minutes')
        if interval and (not isinstance(interval, int) or interval < 1 or interval > 1440):
            return jsonify({
                "success": False,
                "message": "Intervalo deve ser entre 1 e 1440 minutos"
            }), 400
        
        # Atualizar configurações (em produção, isso seria salvo no banco)
        if interval:
            drive_exporter.app.config['EXPORT_INTERVAL_MINUTES'] = interval
        
        # Reiniciar se necessário
        if drive_exporter.running and interval:
            drive_exporter.stop_auto_export()
            drive_exporter.start_auto_export()
        
        return jsonify({
            "success": True,
            "message": "Configurações atualizadas"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao atualizar configurações: {str(e)}"
        }), 500

@export_bp.route('/google-drive/test', methods=['POST'])
def test_google_drive():
    """Testar conexão com Google Drive"""
    try:
        if not drive_exporter.service:
            return jsonify({
                "success": False,
                "message": "Serviço Google Drive não inicializado"
            }), 400
        
        # Testar listando arquivos na pasta
        try:
            results = drive_exporter.service.files().list(
                q=f"'{drive_exporter.folder_id}' in parents" if drive_exporter.folder_id else None,
                pageSize=1,
                fields="files(id, name)"
            ).execute()
            
            return jsonify({
                "success": True,
                "message": "Conexão com Google Drive OK",
                "folder_id": drive_exporter.folder_id
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Erro ao acessar Google Drive: {str(e)}"
            }), 400
            
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro no teste: {str(e)}"
        }), 500

@export_bp.route('/formats/csv', methods=['GET'])
def export_csv():
    """Exportar dados em formato CSV"""
    try:
        csv_content = drive_exporter.export_tasks_to_csv()
        
        if not csv_content:
            return jsonify({
                "success": False,
                "message": "Erro ao gerar CSV"
            }), 500
        
        return jsonify({
            "success": True,
            "content": csv_content,
            "filename": f"solconect_tasks_{drive_exporter.app.config.get('EXPORT_TIMESTAMP', 'export')}.csv"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao exportar CSV: {str(e)}"
        }), 500

@export_bp.route('/formats/json', methods=['GET'])
def export_json():
    """Exportar dados em formato JSON"""
    try:
        json_content = drive_exporter.export_tasks_to_json()
        
        if not json_content:
            return jsonify({
                "success": False,
                "message": "Erro ao gerar JSON"
            }), 500
        
        return jsonify({
            "success": True,
            "content": json_content,
            "filename": f"solconect_backup_{drive_exporter.app.config.get('EXPORT_TIMESTAMP', 'export')}.json"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao exportar JSON: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao exportar JSON: {str(e)}"
        }), 500

@export_bp.route('/formats/report', methods=['GET'])
def export_report():
    """Gerar relatório resumo"""
    try:
        report_content = drive_exporter.generate_summary_report()
        
        if not report_content:
            return jsonify({
                "success": False,
                "message": "Erro ao gerar relatório"
            }), 500
        
        return jsonify({
            "success": True,
            "content": report_content,
            "filename": f"solconect_report_{drive_exporter.app.config.get('EXPORT_TIMESTAMP', 'export')}.txt"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao gerar relatório: {str(e)}"
        }), 500
