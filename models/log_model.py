# models/log_model.py

from datetime import datetime
from flask import request, session
from extensions import mongo

class LogAuditoria:
    @staticmethod
    def registrar(accion, descripcion):
        """
        Registra eventos generales en la colección 'logs'.
        """
        usuario = session.get('usuario', {}).get('tip', 'SISTEMA/ANÓNIMO')
        
        log_documento = {
            "usuario": usuario,
            "accion": accion,          
            "descripcion": descripcion, 
            "ip_origen": request.remote_addr,
            "fecha": datetime.utcnow()
        }
        
        mongo.db.logs.insert_one(log_documento)

    @staticmethod
    def registrar_edicion(tipo, id_objeto, datos_anteriores, datos_nuevos):
        """
        Registra cambios detallados en la colección 'logs'.
        Calcula automáticamente las diferencias (diff) entre los datos.
        """
        # OBTENEMOS EL USURUARIO REGISTRADO
        usuario = session.get('usuario', {}).get('tip', 'SISTEMA/ANÓNIMO')
        
        # CALCULAR LOS CAMBIOS QUE CAMBIARON
        cambios = {}
        for clave, valor_nuevo in datos_nuevos.items():
            valor_anterior = datos_anteriores.get(clave)
            # Comparamos ignorando si el valor anterior no existe
            if str(valor_anterior) != str(valor_nuevo):
                cambios[clave] = {
                    "anterior": valor_anterior,
                    "nuevo": valor_nuevo
                }
        
        if cambios:
            log_documento = {
                "usuario": usuario,
                "accion": tipo,
                "objeto_id": id_objeto,
                "detalles": cambios,
                "ip_origen": request.remote_addr,
                "fecha": datetime.utcnow()
            }
            mongo.db.logs.insert_one(log_documento)
