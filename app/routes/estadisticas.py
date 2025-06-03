from flask import Blueprint, jsonify  # Importa herramientas de Flask para rutas y respuestas JSON
from app import mongo  # Importa la instancia de la base de datos MongoDB desde la app principal

# Crea un Blueprint para agrupar las rutas relacionadas con estadísticas
estadisticas_bp = Blueprint('estadisticas', __name__)

# Define las colecciones que se utilizarán para obtener estadísticas
db_propuestas = mongo.db.v_propuestas
db_politicos = mongo.db.v_politicos
db_votantes = mongo.db.v_votantes

# Ruta para obtener un resumen de conteos (para un dashboard)
@estadisticas_bp.route('/dashboard', methods=['GET'])
def resumen_conteos():
    try:
        # Cuenta el número total de documentos en cada colección
        total_votantes = db_votantes.count_documents({})
        total_politicos = db_politicos.count_documents({})
        total_propuestas = db_propuestas.count_documents({})

        # Devuelve los totales en formato JSON con código de estado 200 (OK)
        return jsonify({
            'votantes': total_votantes,
            'politicos': total_politicos,
            'propuestas': total_propuestas
        }), 200

    except Exception as e:
        # Si ocurre un error, devuelve un mensaje con el error y código de estado 500 (Error interno del servidor)
        return jsonify({'error': str(e)}), 500
