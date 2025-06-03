from flask import Flask, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from .config import Config

# Instancia global para la conexión a MongoDB que se inicializará con la app
mongo = PyMongo()

def create_app():
    # Crear la instancia principal de la aplicación Flask
    app = Flask(__name__)
    
    # Cargar configuración desde la clase Config
    app.config.from_object(Config)
    
    # Permite que las rutas funcionen con o sin la barra final (/)
    app.url_map.strict_slashes = False

    # Inicializar extensiones con la app
    mongo.init_app(app)   # Conectar MongoDB con Flask
    CORS(app)             # Habilitar CORS para permitir peticiones desde otros orígenes

    # Importar y registrar los blueprints (módulos de rutas) con sus prefijos de URL
    from .routes.votantes import votantes_bp
    from .routes.politicos import politicos_bp
    from .routes.propuestas import propuestas_bp
    from .routes.administradores import administradores_bp
    from .routes.estadisticas import estadisticas_bp

    app.register_blueprint(votantes_bp, url_prefix='/api/votante')
    app.register_blueprint(politicos_bp, url_prefix='/api/politico')
    app.register_blueprint(propuestas_bp, url_prefix='/api/propuesta')
    app.register_blueprint(administradores_bp, url_prefix='/api/administrador')
    app.register_blueprint(estadisticas_bp, url_prefix='/api/estadisticas')

    # Ruta raíz para verificar que la API está corriendo correctamente
    @app.route('/')
    def index():
        return {'message': 'API Votaciones corriendo'}
    
    # Ruta para listar todas las rutas registradas en la aplicación
    @app.route('/routes', methods=['GET'])
    def listar_rutas():
        rutas = []
        # Itera sobre todas las reglas definidas en url_map para construir un listado de rutas
        for rule in app.url_map.iter_rules():
            rutas.append({
                'endpoint': rule.endpoint,   # nombre interno de la función que maneja la ruta
                'ruta': str(rule),           # URL de la ruta
                'metodos': list(rule.methods)  # Métodos HTTP permitidos (GET, POST, etc.)
            })
        return jsonify(rutas)

    # Manejo personalizado del error 404 - ruta no encontrada
    @app.errorhandler(404)
    def pagina_no_encontrada(e):
        return {'error': 'Ruta no encontrada'}, 404

    # Devolver la app Flask creada y configurada
    return app
