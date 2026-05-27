import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from extensions import mongo
from bson.objectid import ObjectId
from models.log_model import LogAuditoria

habitabilidad_bp = Blueprint('habitabilidad', __name__, url_prefix='/alojamiento')

# Definimos la ruta base del proyecto para asegurar que las carpetas existan
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

@habitabilidad_bp.route('/')
def listar_inmuebles():
    ubicacion = request.args.get('ubicacion', '').strip()
    precio_max = request.args.get('precio_max', '').strip()
    habitaciones = request.args.get('habitaciones', '').strip()
    
    filtro = {}
    if ubicacion:
        filtro['ubicacion'] = {"$regex": ubicacion, "$options": "i"}
    if precio_max:
        try:
            filtro['precio'] = {"$lte": float(precio_max)}
        except ValueError:
            pass 
    if habitaciones:
        try:
            filtro['habitaciones'] = {"$gte": int(habitaciones)}
        except ValueError:
            pass 
    
    inmuebles = list(mongo.db.habitabilidad.find(filtro).sort("_id", -1))
    ha_filtrado = bool(ubicacion or precio_max or habitaciones)
    
    return render_template(
        'habitabilidad/buscar.html', 
        inmuebles=inmuebles, 
        ubicacion=ubicacion, 
        precio_max=precio_max, 
        habitaciones=habitaciones,
        ha_filtrado=ha_filtrado
    )

@habitabilidad_bp.route('/crear', methods=['GET', 'POST'])
def crear_inmueble():
    if 'usuario' not in session:
        flash("Debes iniciar sesión para publicar una alternativa de alojamiento.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Aseguramos que la carpeta exista antes de guardar
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # 1. Manejo del archivo de imagen
        archivo = request.files.get('imagen')
        ruta_imagen = 'img/default_house.jpg' 
        
        if archivo and archivo.filename != '':
            filename = secure_filename(archivo.filename)
            # Guardamos usando la ruta absoluta definida arriba
            archivo.save(os.path.join(UPLOAD_FOLDER, filename))
            ruta_imagen = f'uploads/{filename}'

        # 2. Captura de datos
        propietario = session['usuario']['usuario']
        nuevo_inmueble = {
            "propietario_usuario": propietario,
            "tipo_vivienda": request.form.get('tipo_vivienda'),
            "precio": float(request.form.get('precio', 0)),
            "ubicacion": request.form.get('ubicacion', '').strip(),
            "habitaciones": int(request.form.get('habitaciones', 1)),
            "titulo": request.form.get('titulo', '').strip(),
            "descripcion": request.form.get('descripcion', '').strip(),
            "contacto": request.form.get('contacto', '').strip(),
            "imagen": ruta_imagen
        }

        mongo.db.habitabilidad.insert_one(nuevo_inmueble)
        LogAuditoria.registrar("PUBLICACION_ALOJAMIENTO", f"Usuario {propietario} ofreció alojamiento: {nuevo_inmueble['titulo']}")
        
        flash("Alojamiento publicado correctamente.", "success")
        return redirect(url_for('habitabilidad.listar_inmuebles'))

    return render_template('habitabilidad/crear.html')

@habitabilidad_bp.route('/eliminar/<string:inmueble_id>', methods=['POST'])
def eliminar_inmueble(inmueble_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    inmueble = mongo.db.habitabilidad.find_one({"_id": ObjectId(inmueble_id)})
    
    if not inmueble:
        flash("El alojamiento ya no existe.", "danger")
        return redirect(url_for('habitabilidad.listar_inmuebles'))

    if inmueble.get('propietario_usuario') == session['usuario']['usuario'] or session['usuario']['rol'] == 'admin':
        # Borrar archivo físico si existe y no es la imagen por defecto
        if inmueble.get('imagen') and inmueble['imagen'] != 'img/default_house.jpg':
            try:
                # Construimos la ruta completa para el borrado
                ruta_archivo = os.path.join(BASE_DIR, 'static', inmueble['imagen'])
                if os.path.exists(ruta_archivo):
                    os.remove(ruta_archivo)
            except Exception as e:
                print(f"Error al borrar archivo: {e}")
        
        mongo.db.habitabilidad.delete_one({"_id": ObjectId(inmueble_id)})
        LogAuditoria.registrar("ELIMINACION_ALOJAMIENTO", f"Alojamiento {inmueble_id} eliminado por {session['usuario']['usuario']}")
        flash("Anuncio retirado con éxito.", "success")
    else:
        flash("No tienes permisos.", "danger")
        
    return redirect(url_for('habitabilidad.listar_inmuebles'))