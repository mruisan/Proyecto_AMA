# crear_usuarios.py
import sys
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from config import Config

def administrar_usuarios():
    print("==================================================")
    print("   AMA - SCRIPT DE ADMINISTRACIÓN DE USUARIOS")
    print("==================================================")
    
    # 1. Conexión directa a MongoDB
    try:
        client = MongoClient(Config.MONGO_URI)

        # Extraemos el nombre de la base de datos desde la URI
        db_name = Config.MONGO_URI.split('/')[-1].split('?')[0]
        db = client[db_name]
        coleccion = db['usuarios']
        print(f" -> Conectado con éxito a la base de datos: '{db_name}'\n")
    except Exception as e:
        print(f" [!] Error crítico al conectar a MongoDB: {e}")
        sys.exit(1)

    # ========================================================
    # BLOQUE 1: ELIMINACIÓN DE USUARIOS ANTIGUOS / CORRUPTOS
    # ========================================================
    # Añade aquí los usuarios que quieras borrar de la base de datos
    usuarios_a_borrar = ["admin", "user01", "user02"]
    
    print(" Pasando escoba de limpieza...")
    for usuario in usuarios_a_borrar:
        resultado = coleccion.delete_one({"usuario": usuario})
        if resultado.deleted_count > 0:
            print(f"   [-] Usuario '{usuario}' eliminado correctamente.")
            
    print(" Limpieza completada.\n" + "-"*50)

    # ========================================================
    # BLOQUE 2: CREACIÓN DE NUEVOS USUARIOS (CON CIFRADO)
    # ========================================================
    # Aquí puedes añadir, quitar o modificar los usuarios que necesites
    nuevos_usuarios = [
        {
            "usuario": "admin",
            "nombre": "Administrador",
            "apellidos": "General",
            "correo": "admin@armada.mde.es",
            "password": "admin",  # <--- Escrita en texto plano, el script lo cifra
            "rol": "admin"
        },
        {
            "usuario": "user01",
            "nombre": "Juan",
            "apellidos": "Pérez García",
            "correo": "juan.perez@armada.mde.es",
            "password": "user01",
            "rol": "usuario"
        },
        {
            "usuario": "user02",
            "nombre": "Carlos",
            "apellidos": "Sánchez",
            "correo": "carlos@armada.mde.es",
            "password": "user02",
            "rol": "usuario"
        }
    ]

    print(" Insertando nuevos usuarios con cifrado seguro...")
    for datos in nuevos_usuarios:
        # Ciframos la contraseña antes de mandarla a MongoDB
        password_plana = datos["password"]
        datos["password"] = generate_password_hash(password_plana)
        
        # Insertamos en la colección de usuarios
        coleccion.insert_one(datos)
        print(f"   [+] Usuario '{datos['usuario']}' creado (Contraseña encriptada: '{password_plana}').")

    print("\n Proceso finalizado con éxito. Base de datos lista.")
    print("==================================================")

if __name__ == '__main__':
    administrar_usuarios()