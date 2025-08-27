from flask import Flask, jsonify
import logging
import os
from dotenv import load_dotenv
from services.gemini_service import GeminiService
from services.database_service import DatabaseService
from services.batch_processor import BatchProcessor

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resumen_llamadas.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Sistema de resumen de llamadas activo"})

@app.route('/procesar-resumenes', methods=['POST'])
def procesar_resumenes():
    try:
        batch_processor = BatchProcessor()
        resultado = batch_processor.procesar_consultas_pendientes()
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Error en procesamiento batch: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        db_service = DatabaseService()
        stats = db_service.obtener_estadisticas()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/procesar-consulta/<int:consulta_id>', methods=['POST'])
def procesar_consulta_individual(consulta_id):
    try:
        batch_processor = BatchProcessor()
        resultado = batch_processor.procesar_consulta_individual(consulta_id)
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Error procesando consulta individual {consulta_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/test-gemini', methods=['GET'])
def test_gemini():
    try:
        gemini_service = GeminiService()
        conexion_ok = gemini_service.test_conexion()
        return jsonify({
            "gemini_conectado": conexion_ok,
            "modelo": gemini_service.model_name
        })
    except Exception as e:
        logger.error(f"Error en test de Gemini: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')