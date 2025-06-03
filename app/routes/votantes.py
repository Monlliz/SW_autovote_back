from flask import Blueprint, request, jsonify
from bson import ObjectId
from app import mongo
import bcrypt
import jwt
from app.schemas import VotanteSchema  # importamos el schema para validación de datos
from app.config import Config
from app.auth import token_required  # importa el decorador para protección de rutas con token

votantes_bp = Blueprint('votantes', __name__)
db = mongo.db.v_votantes  # colección MongoDB donde se almacenan los votantes

# Acceso directo a las variables de clase
votante_schema = VotanteSchema()  # instancia del esquema para validar datos de votantes

#*************************************************************************************************************
# -------------------
# 1. Hashear contraseña
# -------------------
def hash_password(password):
    """
    Genera un hash seguro para la contraseña usando bcrypt.
    bcrypt.gensalt() genera una sal aleatoria para proteger contra ataques de rainbow table.
    Devuelve la contraseña hasheada en formato string para que sea compatible con MongoDB.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')  # Guardamos como string para que MongoDB no tenga problemas

# -------------------
# 2. Verificar contraseña
# -------------------
def check_password(password, hashed):
    """
    Compara la contraseña en texto plano con el hash almacenado.
    Devuelve True si coinciden, False en caso contrario.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

#-------------------------
#3. Crear Token
#-------------------------

#Palabra secreta para firmar el JWT, se obtiene de configuración segura
SECRET_KEY = Config.SECRET_KEY
JWT_ALGORITHM = Config.JWT_ALGORITHM

def generar_token(votante_id):
    """
    Crea un token JWT firmado con el ID del votante.
    Este token se puede usar para autenticación y autorización en futuras peticiones.
    """
    payload = {
        "votante_id": str(votante_id)
    }
    token = jwt.encode(payload, SECRET_KEY, JWT_ALGORITHM)
    return token


#****************************************************************************************************************    
# Crear votante con validación
@votantes_bp.route('/', methods=['POST'])
def create_votante():
    """
    Endpoint para crear un nuevo votante.
    Valida los datos con el esquema, hashea la contraseña y guarda en la base de datos.
    Devuelve el votante creado con su ID convertido a string para JSON.
    """
    try:
        data = request.json
        errores = votante_schema.validate(data)  # Validar datos con Marshmallow
        if errores:
            return jsonify({'errores': errores})  # Devolver errores de validación
        
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
    """
    Obtiene la lista completa de votantes.
    Convierte el campo _id a string para compatibilidad JSON.
    """
    votantes = []
    for doc in db.find():
        doc['_id'] = str(doc['_id'])
        votantes.append(doc)
    return jsonify(votantes)

# Obtener un votante por ID
@votantes_bp.route('/<id>', methods=['GET'])
def get_votante(id):
    """
    Obtiene un votante específico a partir de su ID.
    Si no existe, devuelve un error.
    """
    votante = db.find_one({'_id': ObjectId(id)})
    if not votante:
        return jsonify({'error': 'Votante no encontrado'})

    votante['_id'] = str(votante['_id'])
    return jsonify(votante)

# Obtener un votante por CORREO
@votantes_bp.route('/correo/<correo>', methods=['GET'])
def get_votante_by_correo(correo):
    """
    Busca un votante usando su correo electrónico.
    Ideal para operaciones de login o recuperación.
    """
    votante = db.find_one({'correo': correo})
    if not votante:
        return jsonify({'error': 'Votante no encontrado'})

    votante['_id'] = str(votante['_id'])
    return jsonify(votante)


#-----------------------------------------MANUAL------------------------------
#Buscar por correo y contraseña
@votantes_bp.route('/login/', methods=['POST'])
def get_votante_by_login():
    """
    Endpoint para iniciar sesión.
    Recibe correo y contraseña, valida contra la base y devuelve token JWT si es correcto.
    """
    data = request.json
    correo = data['correo']
    password = data['password']
    
    votante = db.find_one({'correo': correo})
    
    if not votante:
        return jsonify({'error': 'Votante no encontrado'}), 404

    #validar contraseña
    res = check_password(password, votante['password'])
    
    if not res:
        return jsonify({"error": "Contraseña inválida"}), 401
    
    token = generar_token(votante['_id'])  # Generar token con el ID correcto
    
    votante['_id'] = str(votante['_id'])
    
    # Devolver datos del votante junto con token para autenticación futura
    return jsonify({"votante": votante, "token": token})

# Actualizar votante MANUAL
@votantes_bp.route('/manual/<id>', methods=['PUT'])
@token_required #autorizacion de token 
def update_votante_manual(id):
    """
    Actualiza parcialmente un votante solo si el token es válido.
    Valida datos parcialmente para permitir actualizaciones parciales.
    """
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
    """
    Actualiza un votante con validación de los datos.
    Similar a la ruta manual pero sin protección de token.
    """
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
    """
    Elimina un votante por ID.
    No valida existencia previa, elimina directamente.
    """
    db.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Votante eliminado'})

# Obetener preguntas de preferenicas
@votantes_bp.route('/preguntas', methods=['GET'])
def get_preguntas():
    """
    Devuelve las preguntas de preferencias políticas para las diferentes categorías.
    Estas preguntas se usan para valorar la orientación política del votante.
    """
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
                "La protección del medio ambiente debe ser una prioridad, incluso si implica costos económicos significativos.",
                "Las empresas deberían ser responsables de los daños ambientales que ocasionan.",
                "El desarrollo económico sostenible es compatible con el crecimiento industrial tradicional."
            ]
        }
    ]
}
    return jsonify(preguntas)
