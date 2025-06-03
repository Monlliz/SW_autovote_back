from dotenv import load_dotenv
import os

# Carga las variables de entorno definidas en un archivo .env
load_dotenv()

class Config:
    # Clave secreta utilizada para firmar y verificar tokens JWT y otras operaciones sensibles
    SECRET_KEY = os.getenv('SECRET_KEY')

    # URI de conexión para MongoDB, extraída de las variables de entorno
    MONGO_URI = os.getenv('MONGO_URI')

    # Algoritmo que se usará para la codificación y decodificación JWT; por defecto HS256
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    PORT = int(os.environ.get("PORT", 5000))