# seed.py
from pymongo import MongoClient
from models.usuario_model import Usuario
from config import Config

def poblar_base_datos():
    # Conectamos directamente a MongoDB usando la URI de configuración
    client = MongoClient(Config.MONGO_URI)
    db = client.get_default_database()
    
    # Limpiamos la colección usuarios por si acaso para no duplicar datos en las pruebas
    db.usuarios.delete_many({})
    
    print("Creando usuarios de prueba con cifrado seguro...")
    
    # Creamos un usuario Administrador (Rol: admin)
    admin = Usuario(
        tip="ADMIN123",
        nombre="Mando de Control General",
        password="adminpassword",  # Se guardará encriptada automáticamente en el modelo
        rol="admin",
        email="admin@armada.mde.es"
    )
    
    # Creamos un usuario Normal (Rol: usuario)
    militar = Usuario(
        tip="12345678A",
        nombre="Marinero Pérez González",
        password="userpassword",
        rol="usuario",
        email="perez@armada.mde.es"
    )

    # Insertamos los diccionarios generados en MongoDB
    db.usuarios.insert_one(admin.to_dict())
    db.usuarios.insert_one(militar.to_dict())
    
    print("¡Base de datos inicializada correctamente!")
    print("-> Usuario Admin: TIP: ADMIN123 | Pass: adminpassword")
    print("-> Usuario Normal: TIP: 12345678A | Pass: userpassword")

if __name__ == '__main__':
    poblar_base_datos()