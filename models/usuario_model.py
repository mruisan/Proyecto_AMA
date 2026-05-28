# models/usuario_model.py

from werkzeug.security import generate_password_hash, check_password_hash

class Usuario:
    def __init__(self, usuario, nombre, password, rol='usuario', email=None):
        self.usuario = usuario.upper()       			# Usaremos el usuario (dicodef) como identificador único de acceso
        self.nombre = nombre
        self.password_hash = self.set_password(password) 	# Cifrado no reversible
        self.rol = rol               				# Roles: 'admin', 'usuario'
        self.email = email

    @staticmethod
    def set_password(password):
        """Genera un hash seguro y no reversible a partir de la contraseña en texto plano."""
        return generate_password_hash(password)

    @staticmethod
    def verificar_password(password_hash, password):
        """Compara el hash de la base de datos con la contraseña introducida en el login."""
        return check_password_hash(password_hash, password)

    def to_dict(self):
        """Convierte el objeto en un diccionario listo para ser insertado en MongoDB."""
        return {
            "tip": self.usuario,
            "nombre": self.nombre,
            "password_hash": self.password_hash,
            "rol": self.rol,
            "email": self.email
        }