"""
Rotas para gerenciar exportação automática para AWS S3
"""

from flask import Blueprint, request, jsonify
from src.services.aws_s3_export import s3_exporter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

aws_export_bp = Blueprint('aws_export', __name__)

@aws_export_bp.route('/s3/status', methods=['GET'])
def get_export_status():
    """Obter status da exportação automática"""
    try:
        status = s3_exporter.get_status()
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

@aws_export_bp.route('/s3/manual', methods=['POST'])
def manual_export():
    """Executar exportação manual"""
    try:
        result = s3_exporter.manual_export()
        
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

@aws_export_bp.route('/s3/start', methods=['POST'])
def start_auto_export():
    """Iniciar exportação automática"""
    try:
        s3_exporter.start_auto_export()
        
        return jsonify({
            "success": True,
            "message": "Exportação automática AWS S3 iniciada"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao iniciar exportação: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao iniciar exportação: {str(e)}"
        }), 500

@aws_export_bp.route('/s3/stop', methods=['POST'])
def stop_auto_export():
    """Parar exportação automática"""
    try:
        s3_exporter.stop_auto_export()
        
        return jsonify({
            "success": True,
            "message": "Exportação automática AWS S3 parada"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao parar exportação: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao parar exportação: {str(e)}"
        }), 500

@aws_export_bp.route('/s3/config', methods=['POST'])
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
        
        # Atualizar configurações
        if interval:
            s3_exporter.app.config['EXPORT_INTERVAL_MINUTES'] = interval
        
        # Reiniciar se necessário
        if s3_exporter.running and interval:
            s3_exporter.stop_auto_export()
            s3_exporter.start_auto_export()
        
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

@aws_export_bp.route('/s3/test', methods=['POST'])
def test_s3_connection():
    """Testar conexão com AWS S3"""
    try:
        if not s3_exporter.s3_client:
            return jsonify({
                "success": False,
                "message": "Cliente S3 não inicializado"
            }), 400
        
        # Testar listando objetos no bucket
        try:
            s3_exporter.s3_client.head_bucket(Bucket=s3_exporter.bucket_name)
            
            return jsonify({
                "success": True,
                "message": "Conexão com AWS S3 OK",
                "bucket_name": s3_exporter.bucket_name,
                "region": s3_exporter.app.config.get('AWS_S3_REGION')
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Erro ao acessar bucket S3: {str(e)}"
            }), 400
            
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro no teste: {str(e)}"
        }), 500

@aws_export_bp.route('/s3/list', methods=['GET'])
def list_exports():
    """Listar últimas exportações"""
    try:
        limit = request.args.get('limit', 10, type=int)
        result = s3_exporter.list_exports(limit)
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        logger.error(f"Erro ao listar exportações: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao listar exportações: {str(e)}"
        }), 500

@aws_export_bp.route('/formats/csv', methods=['GET'])
def export_csv():
    """Exportar dados em formato CSV"""
    try:
        csv_content = s3_exporter.export_tasks_to_csv()
        
        if not csv_content:
            return jsonify({
                "success": False,
                "message": "Erro ao gerar CSV"
            }), 500
        
        return jsonify({
            "success": True,
            "content": csv_content,
            "filename": f"solconect_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao exportar CSV: {str(e)}"
        }), 500

@aws_export_bp.route('/formats/json', methods=['GET'])
def export_json():
    """Exportar dados em formato JSON"""
    try:
        json_content = s3_exporter.export_tasks_to_json()
        
        if not json_content:
            return jsonify({
                "success": False,
                "message": "Erro ao gerar JSON"
            }), 500
        
        return jsonify({
            "success": True,
            "content": json_content,
            "filename": f"solconect_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao exportar JSON: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao exportar JSON: {str(e)}"
        }), 500

@aws_export_bp.route('/formats/report', methods=['GET'])
def export_report():
    """Gerar relatório resumo"""
    try:
        report_content = s3_exporter.generate_summary_report()
        
        if not report_content:
            return jsonify({
                "success": False,
                "message": "Erro ao gerar relatório"
            }), 500
        
        return jsonify({
            "success": True,
            "content": report_content,
            "filename": f"solconect_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao gerar relatório: {str(e)}"
        }), 500
