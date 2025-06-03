from flask import Blueprint, request, jsonify  # Importa herramientas de Flask para rutas, solicitudes y respuestas
from bson import ObjectId  # Para trabajar con IDs de documentos en MongoDB
from app import mongo  # Importa la instancia de conexión a MongoDB
from app.schemas import PoliticoSchema  # Importa el esquema de validación para políticos

# Crea un Blueprint para agrupar las rutas relacionadas con políticos
politicos_bp = Blueprint('politicos', __name__)

# Accede a la colección de políticos en la base de datos
db = mongo.db.v_politicos

# Instancia del esquema para validar datos de políticos
politico_schema = PoliticoSchema()

# Ruta para crear un nuevo político con validación
@politicos_bp.route('/', methods=['POST'])
def create_politico():
    try:
        data = request.json  # Obtiene los datos JSON enviados en la solicitud

        # Valida y deserializa los datos usando el esquema
        politico_data = politico_schema.load(data)

        # Inserta el nuevo político en la base de datos
        result = db.insert_one(politico_data)

        # Busca el político recién creado para devolverlo como respuesta
        politico_creado = db.find_one({'_id': result.inserted_id})
        politico_creado['_id'] = str(politico_creado['_id'])  # Convierte ObjectId a string para JSON

        return jsonify(politico_creado), 201  # Devuelve el político creado con código 201 (Creado)

    except Exception as e:
        # Devuelve un error interno del servidor si ocurre una excepción
        return jsonify({'error': str(e)}), 500

# Ruta para obtener todos los políticos
@politicos_bp.route('/', methods=['GET'])
def get_politicos():
    politicos = []  # Lista para almacenar los políticos encontrados
    for doc in db.find():  # Itera sobre todos los documentos de la colección
        doc['_id'] = str(doc['_id'])  # Convierte ObjectId a string para JSON
        politicos.append(doc)
    return jsonify(politicos)  # Devuelve la lista de políticos

# Ruta para obtener un político por su ID
@politicos_bp.route('/<id>', methods=['GET'])
def get_politico(id):
    politico = db.find_one({'_id': ObjectId(id)})  # Busca el político por su ID
    if not politico:
        return jsonify({'error': 'Político no encontrado'})  # Devuelve error si no se encuentra

    politico['_id'] = str(politico['_id'])  # Convierte ObjectId a string para JSON
    return jsonify(politico)

# Ruta para obtener un político por su correo
@politicos_bp.route('/correo/<correo>', methods=['GET'])
def get_politico_by_correo(correo):
    politico = db.find_one({'correo': correo})  # Busca el político por el campo 'correo'
    if not politico:
        return jsonify({'error': 'Político no encontrado'})  # Devuelve error si no se encuentra

    politico['_id'] = str(politico['_id'])  # Convierte ObjectId a string para JSON
    return jsonify(politico)

# Ruta para actualizar un político con validación parcial
@politicos_bp.route('/<id>', methods=['PUT'])
def update_politico(id):
    try:
        data = request.json  # Obtiene los datos JSON de la solicitud

        # Valida los datos parcialmente (solo los campos enviados)
        errores = politico_schema.validate(data, partial=True)
        if errores:
            return jsonify({'errores': errores})  # Devuelve los errores de validación si los hay

        # Actualiza el político en la base de datos
        result = db.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Político no encontrado'})  # Si no se encontró, devuelve error

        # Obtiene el documento actualizado para devolverlo
        updated_politico = db.find_one({'_id': ObjectId(id)})
        updated_politico['_id'] = str(updated_politico['_id'])  # Convierte ObjectId a string para JSON
        return jsonify(updated_politico)

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Devuelve error si ocurre una excepción

# Ruta para eliminar un político por ID
@politicos_bp.route('/<id>', methods=['DELETE'])
def delete_politico(id):
    db.delete_one({'_id': ObjectId(id)})  # Elimina el político por su ID
    return jsonify({'message': 'Político eliminado'})  # Devuelve mensaje de confirmación
