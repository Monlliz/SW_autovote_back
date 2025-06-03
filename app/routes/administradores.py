from flask import Blueprint, jsonify  # Importa herramientas de Flask para crear rutas y respuestas en formato JSON
from bson import ObjectId  # Importa ObjectId para trabajar con identificadores de documentos en MongoDB
from app import mongo  # Importa la instancia de la base de datos MongoDB desde la aplicación principal

# Crea un Blueprint para agrupar las rutas relacionadas con los administradores
administradores_bp = Blueprint('administradores', __name__)

# Define la colección de MongoDB donde se almacenan los administradores
db = mongo.db.v_administradores

# Ruta para obtener todos los administradores
@administradores_bp.route('/', methods=['GET'])
def get_votantes():
    administradores = []  # Lista donde se almacenarán los documentos encontrados
    for doc in db.find():  # Recorre todos los documentos en la colección
        doc['_id'] = str(doc['_id'])  # Convierte el ObjectId a cadena para poder ser serializado en JSON
        administradores.append(doc)  # Agrega el documento a la lista
    return jsonify(administradores)  # Devuelve la lista de administradores en formato JSON

# Ruta para obtener un administrador por su ID
@administradores_bp.route('/<id>', methods=['GET'])
def get_votante(id):
    administrador = db.find_one({'_id': ObjectId(id)})  # Busca el documento cuyo _id coincide con el ID proporcionado
    if not administrador:
        return jsonify({'error': 'Votante no encontrado'})  # Si no se encuentra, devuelve un mensaje de error

    administrador['_id'] = str(administrador['_id'])  # Convierte el ObjectId a cadena para JSON
    return jsonify(administrador)  # Devuelve el documento encontrado en formato JSON

# Ruta para obtener un administrador por su correo electrónico
@administradores_bp.route('/correo/<correo>', methods=['GET'])
def get_votante_by_correo(correo):
    administradores_bp = db.find_one({'correo': correo})  # Busca un documento cuyo campo 'correo' coincida con el correo proporcionado
    if not administradores_bp:
        return jsonify({'error': 'Votante no encontrado'})  # Si no se encuentra, devuelve un mensaje de error

    administradores_bp['_id'] = str(administradores_bp['_id'])  # Convierte el ObjectId a cadena para JSON
    return jsonify(administradores_bp)  # Devuelve el documento encontrado en formato JSON
