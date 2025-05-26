from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone
from app import mongo
from app.schemas import PropuestaSchema
from google import genai

propuestas_bp = Blueprint('propuestas', __name__)
db = mongo.db.v_propuestas
db_politicos = mongo.db.v_politicos
db_votantes = mongo.db.v_votantes

propuesta_schema = PropuestaSchema()

# Obtener todas las propuestas
@propuestas_bp.route('/', methods=['GET'])
def get_propuestas():
    try:
        propuestas = []
        for propuesta in db.find():
            # Convertir ObjectId a string
            propuesta['_id'] = str(propuesta['_id'])
            
            # Manejar el caso donde id_politico puede ser ObjectId o dict ($oid)
            id_politico = propuesta.get('id_politico')
            if isinstance(id_politico, dict):
                id_politico = id_politico.get('$oid', id_politico)
            
            # Obtener datos completos del político
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
    try:
        propuestas = []
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

# Obtener una propuesta por ID
@propuestas_bp.route('/<id>', methods=['GET'])
def get_propuesta(id):
    propuesta = db.find_one({'_id': ObjectId(id)})
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'})

    propuesta['_id'] = str(propuesta['_id'])
    propuesta['id_politico'] = str(propuesta['id_politico']) if 'id_politico' in propuesta else None
    return jsonify(propuesta)

# Obtener propuestas por político
@propuestas_bp.route('/politico/<id_politico>', methods=['GET'])
def get_propuestas_por_politico(id_politico):
    try:
        # Verificar si el político existe
        existe = mongo.db.v_politicos.find_one({'_id': ObjectId(id_politico)})
        if not existe:
            return jsonify({'error': 'Político no encontrado'})

        # Buscar propuestas con ese id_politico
        propuestas = db.find({'id_politico': id_politico})
        resultado = []

        for propuesta in propuestas:
            propuesta['_id'] = str(propuesta['_id'])

            resultado.append(propuesta)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Actualizar una propuesta
@propuestas_bp.route('/<id>', methods=['PUT'])
def update_propuesta(id):
    try:
        data = request.json
        errores = propuesta_schema.validate(data, partial=True)
        if errores:
            return jsonify({'errores': errores})

        result = db.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Propuesta no encontrada'})

        updated_propuesta = db.find_one({'_id': ObjectId(id)})
        updated_propuesta['_id'] = str(updated_propuesta['_id'])
        updated_propuesta['id_politico'] = str(updated_propuesta['id_politico']) if 'id_politico' in updated_propuesta else None
        return jsonify(updated_propuesta)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Eliminar una propuesta
@propuestas_bp.route('/<id>', methods=['DELETE'])
def delete_propuesta(id):
    try:
        result = db.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Propuesta no encontrada'})
        return jsonify({'message': 'Propuesta eliminada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from google import genai

@propuestas_bp.route('/', methods=['POST'])
def create_propuesta():
    try:
        data = request.json
        errores = propuesta_schema.validate(data)
        
        if errores:
            return jsonify({'errores': errores})

        # Validar que el político exista
        id_politico = data.get('id_politico')
        if not id_politico or not db_politicos.find_one({'_id': ObjectId(id_politico)}):
            return jsonify({'error': 'Político no encontrado'})

        # Obtener datos
        categoria = data.get('categoria')
        titulo = data.get('titulo')
        descripcion = data.get('descripcion')
        preguntas = obtener_preguntas(categoria)
        
        # Crear el prompt para la API de Gemini
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

        # Llamar a la API de Gemini ❗❗DESCOMENTAR PARA HACER EL LLAMADO A LA API DE GEMINI ❗❗
        client = genai.Client(api_key="AIzaSyAns4IRZ6vdnfK8dqWQv_jKoy1_ZT8jUIo")
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )

        # Obtener la respuesta de la API de Gemini (solo los números)
        # ❗❗DESCOMENTAR PARA OBTENERLO DE LA RESPUESTA ❗❗
        calificaciones = response.text.strip()
        # calificaciones = '1,2,5'
        

        # Insertar la propuesta en la base de datos
        propuesta_data = {
            'id_politico': ObjectId(id_politico),
            'titulo': titulo,
            'descripcion': descripcion,
            'categoria': categoria,
            'valoracion': list(map(int, calificaciones.split(','))),  # Convertir a lista de enteros
            'fecha_creacion': datetime.now(timezone.utc),
        }
           
        result = db.insert_one(propuesta_data)
        prpuesta_creada = db.find_one({'_id': result.inserted_id}) # Buscar la propuesta creada
        
        # Obtener votantes
        votantes = db_votantes.find()
        
        for votante in votantes:
            generar_voto_si_coincide(prpuesta_creada, votante)

        # Devolver la propuesta y las valoraciones
        return jsonify({
            'message': 'Propuesta creada',
            'id': str(result.inserted_id),
            'valoracion': calificaciones
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Mapea categorías a IDs (ajusta según tu sistema)
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
    categoria_nombre = propuesta['categoria']
    categoria_id = CATEGORIA_MAP.get(categoria_nombre)

    if not categoria_id:
        return False  # Categoría no válida

    # Obtener las preferencias de esa categoría del votante
    preferencias_categoria = [p for p in votante['preferencias'] if p['categoria_id'] == categoria_id]

    if len(preferencias_categoria) != 3:
        return False  # Algo está mal, deberían ser 3 preguntas por categoría

    valoracion_propuesta = propuesta['valoracion']  # lista: [v1, v2, v3]

    # Comparamos cada pregunta (índice 0, 1, 2)
    coincidencias = 0
    for i in range(3):
        valor_votante = preferencias_categoria[i]['valoracion']
        valor_propuesta = valoracion_propuesta[i]
        if valor_votante == valor_propuesta:
            coincidencias += 1

    # Decide tu criterio aquí:
    if coincidencias >= 3:
        print(f"Generando voto para votante {votante['_id']} en propuesta {propuesta['id_politico']}")
        voto = {
            'id_votante': votante['_id']
        }
        
         # Insertamos el voto en la propuesta
        db.update_one(
            {'_id': propuesta['_id']},
            {'$push': {'votos': voto}}
        )

        # Insertamos la propuesta en 'propuestas_votadas' del votante
        db_votantes.update_one(
            {'_id': votante['_id']},
            {'$push': {'propuestas_votadas': propuesta['_id']}}
        )
    
        return True  # Voto generado

    else:
        print(f"No hay suficientes coincidencias para votar (solo {coincidencias}/3)")
        return False


def obtener_preguntas(nombre_categoria):
    for categoria in preguntas['categorias']:
        if categoria['nombre'].lower() == nombre_categoria.lower():
            lista_preguntas = categoria['preguntas']
            texto = "\n".join([f"{i+1}. {pregunta}" for i, pregunta in enumerate(lista_preguntas)])
            return texto
    return "No se encontraron preguntas para esta categoría."


# Cambiar estas para cambiarlas en todo el sistema
preguntas = {
    "categorias": [
        {
            "numero": 1,
            "nombre": "Economía y Empleo",
            "preguntas": [
                "El Estado debe intervenir activamente en la economía para reducir las desigualdades de ingresos entre los ciudadanos.",
                "Las empresas privadas son más eficientes que las instituciones públicas para generar empleo y riqueza.",
                "Los trabajadores deberían tener mayor participación en las decisiones de las empresas donde laboran."
            ]
        },
        {
            "numero": 2,
            "nombre": "Educación",
            "preguntas": [
                "La educación superior debería ser gratuita para todos los estudiantes, independientemente de su situación económica.",
                "Las escuelas privadas contribuyen positivamente a mejorar la calidad general del sistema educativo.",
                "Los contenidos curriculares deberían adaptarse específicamente a las necesidades de cada comunidad local."
            ]
        },
        {
            "numero": 3,
            "nombre": "Salud",
            "preguntas": [
                "El acceso a servicios de salud de calidad es un derecho que el Estado debe garantizar a todos los ciudadanos.",
                "Los seguros privados de salud mejoran la eficiencia y calidad de la atención médica.",
                "Los recursos públicos en salud deberían priorizarse hacia los sectores de menores ingresos."
            ]
        },
        {
            "numero": 4,
            "nombre": "Seguridad y Justicia",
            "preguntas": [
                "Aumentar las penas de prisión es una medida eficaz para reducir la criminalidad.",
                "Los programas de reinserción social son más importantes que el castigo para reducir la reincidencia delictiva.",
                "Las fuerzas policiales deberían tener mayores facultades para combatir la inseguridad ciudadana."
            ]
        },
        {
            "numero": 5,
            "nombre": "Medio Ambiente",
            "preguntas": [
                "La protección del medio ambiente debe ser una prioridad, incluso si esto limita el crecimiento económico.",
                "Las empresas deberían estar sujetas a regulaciones ambientales más estrictas, aunque esto aumente sus costos operativos.",
                "Los ciudadanos individuales tienen la responsabilidad principal de adoptar prácticas sostenibles para proteger el medio ambiente."
            ]
        },
        {
            "numero": 6,
            "nombre": "Infraestructura y Transporte",
            "preguntas": [
                "El transporte público debe ser subsidiado por el Estado para garantizar el acceso de todos los ciudadanos.",
                "La construcción de infraestructura debería ser realizada principalmente por empresas privadas mediante concesiones.",
                "Las inversiones en infraestructura rural deben tener la misma prioridad que las inversiones en áreas urbanas."
            ]
        },
        {
            "numero": 7,
            "nombre": "Política Social y Derechos Humanos",
            "preguntas": [
                "El Estado debe implementar políticas específicas para promover la igualdad de oportunidades entre diferentes grupos sociales.",
                "Los programas de asistencia social deberían estar condicionados al cumplimiento de requisitos específicos por parte de los beneficiarios.",
                "La diversidad cultural y étnica enriquece y fortalece la sociedad."
            ]
        },
        {
            "numero": 8,
            "nombre": "Gobernabilidad y Reforma Política",
            "preguntas": [
                "Los ciudadanos deberían tener mayor participación directa en las decisiones de política pública a través de mecanismos como consultas populares.",
                "Un gobierno eficiente es más importante que uno que permite amplia participación ciudadana en la toma de decisiones.",
                "La información sobre el funcionamiento del gobierno debe ser completamente transparente y accesible para todos los ciudadanos."
            ]
        },
        {
            "numero": 9,
            "nombre": "Cultura, Ciencia y Tecnología",
            "preguntas": [
                "El Estado debe invertir significativamente en investigación científica y desarrollo tecnológico, incluso si los beneficios no son inmediatos.",
                "La preservación y promoción de la cultura nacional debe ser una responsabilidad prioritaria del gobierno.",
                "Las universidades y centros de investigación públicos son fundamentales para el desarrollo científico del país."
            ]
        },
        {
            "numero": 10,
            "nombre": "Relaciones Exteriores",
            "preguntas": [
                "La participación en organizaciones internacionales fortalece la capacidad del país para enfrentar desafíos globales.",
                "Las decisiones de política exterior deben priorizarse según los intereses nacionales, incluso si esto genera tensiones con otros países.",
                "Los acuerdos comerciales internacionales benefician el desarrollo económico del país."
            ]
        }
    ]
}

# ---- Agrega estos endpoints al final de tu archivo, antes de las funciones auxiliares ----

@propuestas_bp.route('/<id_propuesta>/vote', methods=['PATCH'])
def add_vote(id_propuesta):
    try:
        data = request.json
        
        # Validar campos requeridos
        if 'id_votante' not in data:
            return jsonify({'error': 'El id_votante es requerido'}), 400

        # Verificar si la propuesta existe
        propuesta = db.find_one({'_id': ObjectId(id_propuesta)})
        if not propuesta:
            return jsonify({'error': 'Propuesta no encontrada'}), 404

        # Verificar si el votante existe
        votante = db_votantes.find_one({'_id': ObjectId(data['id_votante'])})
        if not votante:
            return jsonify({'error': 'Votante no encontrado'}), 404

        # Verificar si ya votó
        voto_existente = next(
            (v for v in propuesta.get('votos', []) if v['id_votante'] == data['id_votante']),
            None
        )
        if voto_existente:
            return jsonify({'error': 'Este votante ya votó por esta propuesta'}), 400

        # Agregar el voto
        result = db.update_one(
            {'_id': ObjectId(id_propuesta)},
            {
                '$push': {
                    'votos': {
                        'id_votante': data['id_votante'],
                        'fecha_voto': datetime.now(timezone.utc)
                    }
                }
            }
        )

        if result.modified_count == 0:
            return jsonify({'error': 'No se pudo registrar el voto'}), 400

        # Actualizar la lista de propuestas votadas del votante
        db_votantes.update_one(
            {'_id': ObjectId(data['id_votante'])},
            {'$addToSet': {'propuestas_votadas': id_propuesta}}
        )

        return jsonify({'message': 'Voto registrado correctamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@propuestas_bp.route('/<id_propuesta>/unvote', methods=['PATCH'])
def remove_vote(id_propuesta):
    try:
        data = request.json
        
        # Validar campos requeridos
        if 'id_votante' not in data:
            return jsonify({'error': 'El id_votante es requerido'}), 400

        # Eliminar el voto de la propuesta
        result = db.update_one(
            {'_id': ObjectId(id_propuesta)},
            {'$pull': {'votos': {'id_votante': data['id_votante']}}}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'No se encontró el voto especificado'}), 404

        # Eliminar la propuesta de la lista del votante
        db_votantes.update_one(
            {'_id': ObjectId(data['id_votante'])},
            {'$pull': {'propuestas_votadas': id_propuesta}}
        )

        return jsonify({'message': 'Voto eliminado correctamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- Las funciones auxiliares (generar_voto_si_coincide, obtener_preguntas, etc.) quedan igual ----