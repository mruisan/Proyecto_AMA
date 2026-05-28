# models/servicio_model.py

from datetime import datetime

class ServicioColaborativo:
    def __init__(self, usuario, tipo, categoria, titulo, descripcion, contacto=None, origen=None, destino=None, plazas=None):
        self.usuario = usuario
        self.tipo = tipo                    		# "OFRECE" o "SOLICITA"
        self.categoria = categoria          		# "Movilidad/Coche", "Informática", "Mecánica", etc.
        self.titulo = titulo
        self.descripcion = descripcion
        self.contacto = contacto
        self.fecha_publicacion = datetime.utcnow()
        
        # Campos específicos para la categoría de compartir coche
        self.origen = origen
        self.destino = destino
        self.plazas = int(plazas) if plazas else None

    def to_dict(self):
        return {
            "usuario": self.usuario,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "contacto": self.contacto,
            "fecha_publicacion": self.fecha_publicacion,
            "origen": self.origen,
            "destino": self.destino,
            "plazas": self.plazas
        }