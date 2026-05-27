# models/log_model.py
from datetime import datetime
from flask import request, session
from extensions import mongo

class LogAuditoria:
    @staticmethod
    def registrar(accion, descripcion):
        """
        Guarda de forma automática un evento en la colección 'logs' de MongoDB.
        Detecta en caliente qué usuario está logueado y su dirección IP.
        """
        # Intentamos obtener el TIP del usuario en sesión; si no hay, es un evento del sistema o login fallido
        usuario_tip = session.get('usuario', {}).get('tip', 'SISTEMA/ANÓNIMO')
        
        log_documento = {
            "usuario_tip": usuario_tip,
            "accion": accion,          
            "descripcion": descripcion, 
            "ip_origen": request.remote_addr, # Guarda la IP del cliente (Requisito de seguridad)
            "fecha": datetime.utcnow()
        }
        
        # Insertamos de fondo en la colección 'logs'
        mongo.db.logs.insert_one(log_documento)