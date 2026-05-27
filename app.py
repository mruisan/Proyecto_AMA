# app.py
from flask import Flask, redirect, url_for
from config import Config
from extensions import mongo
from werkzeug.security import generate_password_hash # IMPORTANTE: Para cifrar los usuarios base

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializamos MONGO vinculándolo a esta app
    mongo.init_app(app)

    # ======================================================================
    # RUTA INICIAL: REDIRIGE AL DASHBOARD PÚBLICO GENERAL (PANTALLA INICIAL)
    # ======================================================================
    @app.route('/')
    def index():
        return redirect(url_for('panel.dashboard'))

    # =============================================
    # CONTROL DE USUARIOS BASE CROSSED CON CIFRADO
    # =============================================
    @app.before_request
    def inicializar_usuarios_base():
        try:
            # 1. Crear el Administrador del sistema
            if not mongo.db.usuarios.find_one({"usuario": "admin"}):
                mongo.db.usuarios.insert_one({
                    "usuario": "admin",
                    "nombre": "Administrador",
                    "apellidos": "General",
                    "correo": "admin@armada.mde.es",
                    "password": generate_password_hash("admin"),  # CIFRADO SEGURO
                    "rol": "admin"
                })
                print(" -> Usuario 'admin' creado con éxito (Contraseña Cifrada).")

            # 2. Crear un Usuario normal de pruebas si no existe con hash seguro
            if not mongo.db.usuarios.find_one({"usuario": "user01"}):
                mongo.db.usuarios.insert_one({
                    "usuario": "user01",
                    "nombre": "Juan",
                    "apellidos": "Pérez García",
                    "correo": "juan.perez@armada.mde.es",
                    "password": generate_password_hash("user01"), # CIFRADO SEGURO
                    "rol": "militar" # Cambiado 'usuario' por tu rol estandar 'militar'
                })
                print(" -> Usuario de prueba 'user01' creado con éxito (Contraseña Cifrada).")
                
        except Exception as e:
            print(f"Error al inicializar los usuarios base: {e}")

    # ========================================================
    # REGISTRO DE RUTAS (DENTRO DE CREATE_APP)
    # ========================================================
    from routes.auth_routes import auth_bp
    from routes.panel_routes import panel_bp
    from routes.habitabilidad_routes import habitabilidad_bp
    from routes.administracion_routes import admin_bp
    from routes.servicios_routes import servicios_bp
    from routes.mercado_routes import mercado_bp
    from routes.ocio_routes import ocio_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(panel_bp)
    app.register_blueprint(habitabilidad_bp)
    app.register_blueprint(admin_bp)              
    app.register_blueprint(servicios_bp)
    app.register_blueprint(mercado_bp)
    app.register_blueprint(ocio_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)