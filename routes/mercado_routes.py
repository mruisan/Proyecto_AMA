# routes/mercado_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mongo
from bson.objectid import ObjectId
from models.log_model import LogAuditoria

mercado_bp = Blueprint('mercado', __name__, url_prefix='/mercado')

@mercado_bp.route('/')
def listar_material():
    # RUTA LIBERADA: Eliminamos el bloqueo forzoso de sesión.
    # Cualquier persona o visitante anónimo puede listar y buscar artículos en el mercado.
    
    # 1. Capturamos los nuevos criterios independientes y opcionales del formulario
    categoria = request.args.get('categoria', '').strip()
    precio_max = request.args.get('precio_max', '').strip()
    que_buscas = request.args.get('que_buscas', '').strip()
    
    # 2. Construimos el filtro dinámico incremental para MongoDB
    filtro = {}
    
    if categoria:
        # Filtra por la categoría exacta seleccionada
        filtro['categoria'] = categoria
        
    if precio_max:
        # Filtra artículos cuyo precio sea Menor o Igual ($lte) que el indicado
        try:
            filtro['precio'] = {"$lte": float(precio_max)}
        except ValueError:
            pass  # Si el formato no es numérico por algún motivo, se ignora el filtro
            
    if que_buscas:
        # Filtra por texto libre (insensible a mayúsculas/minúsculas) tanto en título como en descripción
        filtro['$or'] = [
            {"titulo": {"$regex": que_buscas, "$options": "i"}},
            {"descripcion": {"$regex": que_buscas, "$options": "i"}}
        ]
    
    # 3. Traemos los artículos aplicando el filtro y ordenados del más reciente al más antiguo
    articulos_cursor = mongo.db.mercado.find(filtro).sort("_id", -1)
    articulos = list(articulos_cursor)
    
    # Variable de control para saber si se ha aplicado algún filtro en la interfaz
    ha_filtrado = bool(categoria or precio_max or que_buscas)
    
    # 4. Enviamos el resultado y las variables para mantener los valores en los inputs del HTML
    return render_template(
        'mercado/buscar.html', 
        articulos=articulos,
        categoria=categoria,
        precio_max=precio_max,
        que_buscas=que_buscas,
        ha_filtrado=ha_filtrado
    )

@mercado_bp.route('/crear', methods=['GET', 'POST'])
def crear_articulo():
    # RUTA PROTEGIDA: Exige inicio de sesión únicamente al querer publicar algo nuevo
    if 'usuario' not in session:
        flash("Debes iniciar sesión para publicar un artículo en el mercado.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # CAPTURA CORREGIDA: Usamos la nueva estructura de sesión sin TIP
        propietario = session['usuario']['usuario']
        titulo = request.form.get('titulo', '').strip()
        categoria = request.form.get('categoria')
        estado = request.form.get('estado')
        precio = request.form.get('precio', 0)
        descripcion = request.form.get('descripcion', '').strip()
        contacto = request.form.get('contacto', '').strip()

        try:
            precio = float(precio)
        except ValueError:
            precio = 0.0

        nuevo_article = {
            "propietario_usuario": propietario,  # Clave universalizada
            "titulo": titulo,
            "categoria": categoria,
            "estado": estado,
            "precio": precio,
            "descripcion": descripcion,
            "contacto": contacto
        }

        mongo.db.mercado.insert_one(nuevo_article)
        LogAuditoria.registrar("PUBLICACION_MERCADO", f"Usuario {propietario} publicó artículo: {titulo}")
        
        flash("Artículo publicado con éxito en el portal.", "success")
        return redirect(url_for('mercado.listar_material'))

    return render_template('mercado/crear.html')

@mercado_bp.route('/eliminar/<string:articulo_id>', methods=['POST'])
def eliminar_articulo(articulo_id):
    # RUTA PROTEGIDA: Exige inicio de sesión absoluto para eliminar
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    usuario_actual = session['usuario']['usuario']
    rol_actual = session['usuario']['rol']

    # Buscar el artículo para comprobar la autoría
    articulo = mongo.db.mercado.find_one({"_id": ObjectId(articulo_id)})
    
    if not articulo:
        flash("El artículo no existe.", "danger")
        return redirect(url_for('mercado.listar_material'))

    # REQUISITO: Solo el dueño o el admin pueden borrar
    if articulo.get('propietario_usuario') == usuario_actual or rol_actual == 'admin':
        mongo.db.mercado.delete_one({"_id": ObjectId(articulo_id)})
        LogAuditoria.registrar("ELIMINACION_MERCADO", f"Artículo {articulo_id} eliminado por {usuario_actual}")
        flash("Artículo retirado correctamente.", "success")
    else:
        flash("No tiene permisos para eliminar este artículo.", "danger")
        
    return redirect(url_for('mercado.listar_material'))