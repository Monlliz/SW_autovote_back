from flask import Blueprint, request, jsonify
from bson import ObjectId
from app import mongo
import bcrypt
import jwt
from app.schemas import VotanteSchema  # importamos el schema
from app.config import Config
from app.auth import token_required  # importa el decorador

votantes_bp = Blueprint('votantes', __name__)
db = mongo.db.v_votantes



# Acceso directo a las variables de clase
votante_schema = VotanteSchema()

#*************************************************************************************************************
# -------------------
# 1. Hashear contraseña
# -------------------
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')# Guardamos como string para que MongoDB no tenga problemas

# -------------------
# 2. Verificar contraseña
# -------------------
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

#-------------------------
#3. Crear Token
#-------------------------

#Palabra secreta
SECRET_KEY = Config.SECRET_KEY
JWT_ALGORITHM = Config.JWT_ALGORITHM

def generar_token(votante_id):
    payload = {
        "votante_id": str(votante_id)
    }
    token = jwt.encode(payload, SECRET_KEY, JWT_ALGORITHM)
    return token


#****************************************************************************************************************    
# Crear votante con validación
@votantes_bp.route('/', methods=['POST'])
def create_votante():
    try:
        data = request.json
        errores = votante_schema.validate(data)
        if errores:
            return jsonify({'errores': errores})
        
          # Hash de la contraseña
        if 'password' in data:
            password_plano = data['password']
            data['password'] = hash_password(password_plano)
            
        #Guardar en la base de datos
        result = db.insert_one(data)
        
        votante_creado = db.find_one({'_id': result.inserted_id}) # Buscar el votante creado
        votante_creado['_id'] = str(votante_creado['_id']) # Convertir _id a string para poder enviarlo en JSON

        return jsonify(votante_creado), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Obtener todos los votantes
@votantes_bp.route('/', methods=['GET'])
def get_votantes():
    votantes = []
    for doc in db.find():
        doc['_id'] = str(doc['_id'])
        votantes.append(doc)
    return jsonify(votantes)

# Obtener un votante por ID
@votantes_bp.route('/<id>', methods=['GET'])
def get_votante(id):
    votante = db.find_one({'_id': ObjectId(id)})
    if not votante:
        return jsonify({'error': 'Votante no encontrado'})

    votante['_id'] = str(votante['_id'])
    return jsonify(votante)

# Obtener un votante por CORREO
@votantes_bp.route('/correo/<correo>', methods=['GET'])
def get_votante_by_correo(correo):
    votante = db.find_one({'correo': correo})
    if not votante:
        return jsonify({'error': 'Votante no encontrado'})

    votante['_id'] = str(votante['_id'])
    return jsonify(votante)


#-----------------------------------------MANUAL------------------------------
#Buscar por correo y contraseña
@votantes_bp.route('/login/', methods=['POST'])
def get_votante_by_login():
    data = request.json
    correo = data['correo']
    password = data['password']
    
    votante = db.find_one({'correo': correo})
    #validar contraseña
    res = check_password(password,votante['password'])
    token = generar_token('_id')

    if not res:
        return jsonify({"Contraseña invalida"}) 
    
    if not votante:
        return jsonify({'error': 'Votante no encontrado'})

    votante['_id'] = str(votante['_id'])
     
    print(jsonify(votante))
    return jsonify({"votante": votante, "token": token})

# Actualizar votante MANUAL
@votantes_bp.route('/manual/<id>', methods=['PUT'])
@token_required #autorizacion de token 
def update_votante_manual(id):
    try:
        data = request.json
        errores = votante_schema.validate(data, partial=True)
        if errores:
            return jsonify({'errores': errores})
        
        result = db.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Votante no encontrado'})
        
        updated_votante = db.find_one({'_id': ObjectId(id)})
        updated_votante['_id'] = str(updated_votante['_id'])
        return jsonify(updated_votante)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
#--------------------------------FIN MANUAL------------------------------------------------------------


# Actualizar votante con validación
@votantes_bp.route('/<id>', methods=['PUT'])
def update_votante(id):
    try:
        data = request.json
        errores = votante_schema.validate(data, partial=True)
        if errores:
            return jsonify({'errores': errores})
        
        result = db.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Votante no encontrado'})
        
        updated_votante = db.find_one({'_id': ObjectId(id)})
        updated_votante['_id'] = str(updated_votante['_id'])
        return jsonify(updated_votante)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Eliminar votante
@votantes_bp.route('/<id>', methods=['DELETE'])
def delete_votante(id):
    db.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Votante eliminado'})

# Obetener preguntas de preferenicas
@votantes_bp.route('/preguntas', methods=['GET'])
def get_preguntas():
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
    ]}
    
    return jsonify(preguntas)