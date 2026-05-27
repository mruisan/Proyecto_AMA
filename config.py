# config.py
import os

class Config:
    # Clave secreta para firmar las cookies de sesión (Requisito de seguridad)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave_secreta_para_desarrollo_ama_2026'
    
    # Configuración de MongoDB (Apuntando por defecto al contenedor Docker local)
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/ama_db'