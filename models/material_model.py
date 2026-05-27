# models/material_model.py
from datetime import datetime

class ArticuloMercado:
    def __init__(self, propietario_tip, titulo, descripcion, categoria, estado, precio, contacto=None):
        self.propietario_tip = propietario_tip  # usuario que lo vende
        self.titulo = titulo                    
        self.descripcion = descripcion          # Detalles del artículo
        self.categoria = categoria             
        self.estado = estado                    
        self.precio = float(precio) if precio else 0.0  # 0.0 si se regala
        self.contacto = contacto                
        self.fecha_publicacion = datetime.utcnow()

    def to_dict(self):
        return {
            "propietario_tip": self.propietario_tip,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "estado": self.estado,
            "precio": self.precio,
            "contacto": self.contacto,
            "fecha_publicacion": self.fecha_publicacion
        }