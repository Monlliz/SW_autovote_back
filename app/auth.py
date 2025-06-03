from functools import wraps
from flask import request, jsonify
import jwt
from app.config import Config
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

JWT_ALGORITHM = Config.JWT_ALGORITHM
SECRET_KEY = Config.SECRET_KEY

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Obtener token del header Authorization (Bearer <token>)
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401

        try:
            # jwt.decode requiere algoritmo(s) como lista
            data = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            request.votante_id = data['votante_id']
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        return f(*args, **kwargs)
    return decorated
