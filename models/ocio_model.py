# models/ocio_model.py
from datetime import datetime

class EventoOcio:
    def __init__(self, organizador_tip, titulo, descripcion, categoria, fecha_evento, lugar, participantes=None):
        self.organizador_tip = organizador_tip  # TIP del militar que organiza
        self.titulo = titulo                    # Ej: "Torneo de Fútbol Sala San Juan"
        self.descripcion = descripcion          # Detalles de la actividad
        self.categoria = categoria              # "Deportes", "Cultural", "Gastronomía", "Otros"
        self.fecha_evento = fecha_evento        # Fecha y hora de la actividad
        self.lugar = lugar                      # Ubicación (Ej: Polideportivo de la Base)
        self.participantes = participantes if participantes is list else [] # Lista de TIPs apuntados
        self.fecha_publicacion = datetime.utcnow()

    def to_dict(self):
        return {
            "organizador_tip": self.organizador_tip,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "fecha_evento": self.fecha_evento,
            "lugar": self.lugar,
            "participantes": self.participantes,
            "fecha_publicacion": self.fecha_publicacion
        }