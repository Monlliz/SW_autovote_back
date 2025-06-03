from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone
from app import mongo
from app.schemas import PropuestaSchema
from google import genai

# Crear blueprint para las rutas de propuestas
propuestas_bp = Blueprint('propuestas', __name__)

# Referencias a colecciones de MongoDB
db = mongo.db.v_propuestas
db_politicos = mongo.db.v_politicos
db_votantes = mongo.db.v_votantes

# Instancia del esquema para validación
propuesta_schema = PropuestaSchema()

# ----------------------------------------
# Rutas para obtener propuestas
# ----------------------------------------

@propuestas_bp.route('/', methods=['GET'])
def get_propuestas():
    """Obtener todas las propuestas con los datos completos del político asociado"""
    try:
        propuestas = []
        for propuesta in db.find():
            # Convertir ObjectId a string para JSON
            propuesta['_id'] = str(propuesta['_id'])
            
            # Manejar id_politico que puede venir como dict {"$oid": "..."}
            id_politico = propuesta.get('id_politico')
            if isinstance(id_politico, dict):
                id_politico = id_politico.get('$oid', id_politico)
            
            # Buscar datos completos del político
            politico = db_politicos.find_one({'_id': ObjectId(id_politico)})
            if politico:
                politico['_id'] = str(politico['_id'])
                propuesta['politico'] = politico
            
            propuestas.append(propuesta)
        
        return jsonify(propuestas)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@propuestas_bp.route('/ultimas', methods=['GET'])
def get_propuestas_ultimas():
    """Obtener las últimas 5 propuestas agregadas, con datos del político"""
    try:
        propuestas = []
        # Orden descendente por _id (más reciente primero)
        for propuesta in db.find().sort('_id', -1).limit(5):
            propuesta['_id'] = str(propuesta['_id'])
            
            id_politico = propuesta.get('id_politico')
            if isinstance(id_politico, dict):
                id_politico = id_politico.get('$oid', id_politico)
            
            politico = db_politicos.find_one({'_id': ObjectId(id_politico)})
            if politico:
                politico['_id'] = str(politico['_id'])
                propuesta['politico'] = politico
            
            propuestas.append(propuesta)
        
        return jsonify(propuestas)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@propuestas_bp.route('/<id>', methods=['GET'])
def get_propuesta(id):
    """Obtener una propuesta específica por su ID"""
    propuesta = db.find_one({'_id': ObjectId(id)})
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'})

    # Convertir ObjectIds a strings para JSON
    propuesta['_id'] = str(propuesta['_id'])
    propuesta['id_politico'] = str(propuesta['id_politico']) if 'id_politico' in propuesta else None
    return jsonify(propuesta)


@propuestas_bp.route('/politico/<id_politico>', methods=['GET'])
def get_propuestas_por_politico(id_politico):
    """Obtener todas las propuestas asociadas a un político específico"""
    try:
        # Verificar si el político existe
        existe = mongo.db.v_politicos.find_one({'_id': ObjectId(id_politico)})
        if not existe:
            return jsonify({'error': 'Político no encontrado'})

        # Buscar propuestas con el id_politico indicado
        propuestas = db.find({'id_politico': id_politico})
        resultado = []

        for propuesta in propuestas:
            propuesta['_id'] = str(propuesta['_id'])
            resultado.append(propuesta)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------
# Rutas para crear, actualizar y eliminar propuestas
# ----------------------------------------

@propuestas_bp.route('/', methods=['POST'])
def create_propuesta():
    """Crear una nueva propuesta y obtener una valoración automática vía API Gemini"""
    try:
        data = request.json
        errores = propuesta_schema.validate(data)
        
        if errores:
            return jsonify({'errores': errores})

        # Validar que el político exista en la BD
        id_politico = data.get('id_politico')
        if not id_politico or not db_politicos.find_one({'_id': ObjectId(id_politico)}):
            return jsonify({'error': 'Político no encontrado'})

        # Extraer datos de la propuesta
        categoria = data.get('categoria')
        titulo = data.get('titulo')
        descripcion = data.get('descripcion')
        
        # Obtener preguntas según la categoría para la valoración
        preguntas = obtener_preguntas(categoria)
        
        # Preparar prompt para la API de Gemini (modelo de IA)
        prompt = f"""
        Evalúa la siguiente propuesta política y responde solo con los números (separados por comas) de las calificaciones del 1 al 5, según corresponda a cada pregunta. No agregues texto adicional, solo los números en el orden de las preguntas.

        Categoría de la propuesta:
        {categoria}
        
        Título:
        {titulo}

        Propuesta:
        {descripcion}

        Preguntas:
        {preguntas}

        Devuelve la respuesta en el formato:
        número,número,número (por ejemplo: 5,4,3)
        """

        # Llamar a la API de Gemini
        client = genai.Client(api_key="AIzaSyAns4IRZ6vdnfK8dqWQv_jKoy1_ZT8jUIo")
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )

        # Obtener la respuesta que contiene las calificaciones
        calificaciones = response.text.strip()

        # Preparar datos para guardar la propuesta en BD
        propuesta_data = {
            'id_politico': ObjectId(id_politico),
            'titulo': titulo,
            'descripcion': descripcion,
            'categoria': categoria,
            'valoracion': list(map(int, calificaciones.split(','))),  # Convertir texto a lista de enteros
            'fecha_creacion': datetime.now(timezone.utc),
        }
           
        # Insertar en BD
        result = db.insert_one(propuesta_data)
        prpuesta_creada = db.find_one({'_id': result.inserted_id})
        
        # Obtener todos los votantes para generar votos automáticos si aplican
        votantes = db_votantes.find()
        for votante in votantes:
            generar_voto_si_coincide(prpuesta_creada, votante)

        # Responder con mensaje y calificaciones
        return jsonify({
            'message': 'Propuesta creada',
            'id': str(result.inserted_id),
            'valoracion': calificaciones
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@propuestas_bp.route('/<id>', methods=['PUT'])
def update_propuesta(id):
    """Actualizar una propuesta existente parcialmente"""
    try:
        data = request.json
        
        # Validar datos (parcial, porque no siempre se actualizan todos los campos)
        errores = propuesta_schema.validate(data, partial=True)
        if errores:
            return jsonify({'errores': errores})

        # Actualizar documento en BD
        result = db.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Propuesta no encontrada'})

        # Obtener propuesta actualizada para devolverla
        updated_propuesta = db.find_one({'_id': ObjectId(id)})
        updated_propuesta['_id'] = str(updated_propuesta['_id'])
        updated_propuesta['id_politico'] = str(updated_propuesta['id_politico']) if 'id_politico' in updated_propuesta else None
        return jsonify(updated_propuesta)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@propuestas_bp.route('/<id>', methods=['DELETE'])
def delete_propuesta(id):
    """Eliminar una propuesta por su ID"""
    try:
        result = db.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Propuesta no encontrada'})
        return jsonify({'message': 'Propuesta eliminada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----------------------------------------
# Funciones auxiliares para votaciones y preguntas
# ----------------------------------------

# Diccionario que asocia categorías con un ID numérico
CATEGORIA_MAP = {
    "Economía y Empleo": 1,
    "Educación": 2,
    "Salud": 3,
    "Seguridad y Justicia": 4,
    "Medio Ambiente": 5,
    "Infraestructura y Transporte": 6,
    "Política Social y Derechos Humanos": 7,
    "Gobernabilidad y Reforma Política": 8,
    "Cultura, Ciencia y Tecnología": 9,
    "Relaciones Exteriores": 10
}

def generar_voto_si_coincide(propuesta, votante):
    """
    Genera un voto automático para una propuesta si las valoraciones coinciden 100%
    con las preferencias del votante para esa categoría.
    """
    categoria = propuesta.get('categoria')
    if categoria is None:
        return
    
    cat_id = CATEGORIA_MAP.get(categoria, None)
    if cat_id is None:
        return

    valoracion_propuesta = propuesta.get('valoracion', [])
    valoracion_votante = votante.get('valoracion', {}).get(str(cat_id), [])

    # Compara las 3 respuestas de valoración (debe haber 3 para ambas)
    if len(valoracion_propuesta) == 3 and len(valoracion_votante) == 3:
        if valoracion_propuesta == valoracion_votante:
            # Revisar si ya votó para evitar duplicados
            votos = propuesta.get('votos', [])
            votante_id_str = str(votante['_id'])
            ya_voto = any(v.get('id_votante') == votante_id_str for v in votos)
            if ya_voto:
                return
            
            # Crear voto con fecha UTC actual
            voto = {
                'id_votante': votante['_id'],
                'fecha': datetime.now(timezone.utc)
            }
            
            # Agregar voto a la propuesta en la BD
            db.update_one({'_id': propuesta['_id']}, {'$push': {'votos': voto}})


def obtener_preguntas(categoria):
    """
    Devuelve las preguntas para la valoración según la categoría de la propuesta.
    """
    preguntas_por_categoria = {
        "economía y empleo": [
            "¿La propuesta fomenta la creación de empleo?",
            "¿Contribuye a la estabilidad económica?",
            "¿Promueve la innovación y competitividad?"
        ],
        "educación": [
            "¿Mejora la calidad educativa?",
            "¿Aumenta la cobertura escolar?",
            "¿Promueve la equidad en educación?"
        ],
        "salud": [
            "¿Mejora el acceso a servicios de salud?",
            "¿Contribuye a la prevención de enfermedades?",
            "¿Fortalece la infraestructura sanitaria?"
        ],
        "seguridad y justicia": [
            "¿Reduce la delincuencia?",
            "¿Mejora el acceso a la justicia?",
            "¿Fomenta la confianza en instituciones?"
        ],
        "medio ambiente": [
            "¿Protege los recursos naturales?",
            "¿Promueve la sostenibilidad ambiental?",
            "¿Fomenta la conciencia ecológica?"
        ],
        "infraestructura y transporte": [
            "¿Mejora la movilidad urbana?",
            "¿Fomenta el desarrollo de infraestructura?",
            "¿Contribuye a la seguridad vial?"
        ],
        "política social y derechos humanos": [
            "¿Garantiza derechos fundamentales?",
            "¿Promueve la inclusión social?",
            "¿Fortalece la participación ciudadana?"
        ],
        "gobernabilidad y reforma política": [
            "¿Mejora la transparencia gubernamental?",
            "¿Fortalece la democracia?",
            "¿Promueve la rendición de cuentas?"
        ],
        "cultura, ciencia y tecnología": [
            "¿Fomenta la innovación tecnológica?",
            "¿Apoya el desarrollo cultural?",
            "¿Impulsa la investigación científica?"
        ],
        "relaciones exteriores": [
            "¿Fortalece la diplomacia internacional?",
            "¿Promueve la cooperación global?",
            "¿Mejora la imagen del país en el exterior?"
        ]
    }

    return preguntas_por_categoria.get(categoria.lower(), [])


# ----------------------------------------
# Endpoints para votar y eliminar voto
# ----------------------------------------

@propuestas_bp.route('/vote', methods=['POST'])
def votar():
    """
    Endpoint para votar una propuesta.
    Requiere en el JSON: id_propuesta, id_votante
    """
    data = request.json
    
    # Validar campos necesarios
    if not data or 'id_propuesta' not in data or 'id_votante' not in data:
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
    
    try:
        propuesta = db.find_one({'_id': ObjectId(data['id_propuesta'])})
        if not propuesta:
            return jsonify({'error': 'Propuesta no encontrada'}), 404
        
        votante = db_votantes.find_one({'_id': ObjectId(data['id_votante'])})
        if not votante:
            return jsonify({'error': 'Votante no encontrado'}), 404
        
        # Verificar si ya votó para esta propuesta
        voto_existente = next(
            (v for v in propuesta.get('votos', []) if str(v.get('id_votante')) == data['id_votante']),
            None
        )
        if voto_existente:
            return jsonify({'error': 'El votante ya ha votado esta propuesta'}), 400
        
        # Crear voto con fecha UTC
        voto = {
            'id_votante': votante['_id'],
            'fecha': datetime.now(timezone.utc)
        }
        
        # Actualizar la propuesta agregando el voto
        db.update_one({'_id': propuesta['_id']}, {'$push': {'votos': voto}})
        
        return jsonify({'message': 'Voto registrado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@propuestas_bp.route('/unvote', methods=['POST'])
def eliminar_voto():
    """
    Endpoint para eliminar el voto de un votante a una propuesta.
    Requiere en JSON: id_propuesta, id_votante
    """
    data = request.json
    
    if not data or 'id_propuesta' not in data or 'id_votante' not in data:
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
    
    try:
        propuesta = db.find_one({'_id': ObjectId(data['id_propuesta'])})
        if not propuesta:
            return jsonify({'error': 'Propuesta no encontrada'}), 404
        
        votante = db_votantes.find_one({'_id': ObjectId(data['id_votante'])})
        if not votante:
            return jsonify({'error': 'Votante no encontrado'}), 404
        
        # Remover voto del votante
        db.update_one(
            {'_id': propuesta['_id']},
            {'$pull': {'votos': {'id_votante': votante['_id']}}}
        )
        
        return jsonify({'message': 'Voto eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
