# models/inmueble_model.py
from datetime import datetime

class Inmueble:
    def __init__(self, propietario_tip, titulo, descripcion, ubicacion, precio, tipo, plazas=1):
        self.propietario_tip = propietario_tip  # Quién lo publica (usuario)
        self.titulo = titulo
        self.descripcion = descripcion
        self.ubicacion = ubicacion              
        self.precio = float(precio)             
        self.tipo = tipo                        # "Alquiler", "Intercambio" o "Compartido"
        self.plazas = int(plazas)
        self.fecha_publicacion = datetime.utcnow()

    def to_dict(self):
        return {
            "propietario_tip": self.propietario_tip,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "ubicacion": self.ubicacion,
            "precio": self.precio,
            "tipo": self.tipo,
            "plazas": self.plazas,
            "fecha_publicacion": self.fecha_publicacion
        }