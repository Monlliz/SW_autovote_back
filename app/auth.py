from functools import wraps
from flask import request, jsonify
import jwt
from app.config import Config

JWT_ALGORITHM = Config.JWT_ALGORITHM
SECRET_KEY = Config.SECRET_KEY

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Verifica si el token viene en los headers
        if 'Authorization' in request.headers:
            bearer = request.headers['Authorization']
            token = bearer[7:]
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, JWT_ALGORITHM)
            request.id = data['votante_id']
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        return f(*args, **kwargs)
    return decorated
