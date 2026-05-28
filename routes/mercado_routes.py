# routes/mercado_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mongo
from bson.objectid import ObjectId
from bson.errors import InvalidId
from models.log_model import LogAuditoria

mercado_bp = Blueprint('mercado', __name__, url_prefix='/mercado')

@mercado_bp.route('/')
def listar_material():
    categoria = request.args.get('categoria', '').strip()
    precio_max = request.args.get('precio_max', '').strip()
    que_buscas = request.args.get('que_buscas', '').strip()
    
    filtro = {}
    if categoria:
        filtro['categoria'] = categoria
        
    if precio_max:
        try:
            filtro['precio'] = {"$lte": float(precio_max)}
        except ValueError:
            pass
            
    if que_buscas:
        filtro['$or'] = [
            {"titulo": {"$regex": que_buscas, "$options": "i"}},
            {"descripcion": {"$regex": que_buscas, "$options": "i"}}
        ]
    
    articulos = list(mongo.db.mercado.find(filtro).sort("_id", -1))
    ha_filtrado = bool(categoria or precio_max or que_buscas)
    
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
    if 'usuario' not in session:
        flash("Debes iniciar sesión para publicar un artículo en el mercado.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        propietario = session['usuario']['usuario']
        titulo = request.form.get('titulo', '').strip()
        
        try:
            precio = float(request.form.get('precio', 0))
        except ValueError:
            precio = 0.0

        nuevo_articulo = {
            "propietario_usuario": propietario,
            "titulo": titulo,
            "categoria": request.form.get('categoria'),
            "estado": request.form.get('estado'),
            "precio": precio,
            "descripcion": request.form.get('descripcion', '').strip(),
            "contacto": request.form.get('contacto', '').strip()
        }

        mongo.db.mercado.insert_one(nuevo_articulo)
        LogAuditoria.registrar("PUBLICACION_MERCADO", f"Usuario {propietario} publicó artículo: {titulo}")
        
        flash("Artículo publicado con éxito en el portal.", "success")
        return redirect(url_for('mercado.listar_material'))

    return render_template('mercado/crear.html')

@mercado_bp.route('/eliminar/<string:articulo_id>', methods=['POST'])
def eliminar_articulo(articulo_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    articulo = mongo.db.mercado.find_one({"_id": ObjectId(articulo_id)})
    if not articulo:
        flash("El artículo no existe.", "danger")
        return redirect(url_for('mercado.listar_material'))

    if articulo.get('propietario_usuario') == session['usuario']['usuario'] or session['usuario']['rol'] == 'admin':
        mongo.db.mercado.delete_one({"_id": ObjectId(articulo_id)})
        LogAuditoria.registrar("ELIMINACION_MERCADO", f"Artículo {articulo_id} eliminado.")
        flash("Artículo retirado correctamente.", "success")
    else:
        flash("No tiene permisos para eliminar este artículo.", "danger")
        
    return redirect(url_for('mercado.listar_material'))

@mercado_bp.route('/editar/<articulo_id>', methods=['GET', 'POST'])
def editar_articulo(articulo_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesión para editar un artículo.", "danger")
        return redirect(url_for('auth.login'))

    try:
        obj_id = ObjectId(articulo_id)
    except InvalidId:
        flash("ID de artículo no válido.", "danger")
        return redirect(url_for('mercado.listar_material'))

    # 1. Recuperar estado ANTERIOR para el log
    articulo_anterior = mongo.db.mercado.find_one({"_id": obj_id})
    if not articulo_anterior:
        flash("El artículo no existe.", "danger")
        return redirect(url_for('mercado.listar_material'))

    # Verificar permisos
    if session['usuario']['usuario'] != articulo_anterior.get('propietario_usuario') and session['usuario']['rol'] != 'admin':
        flash("No tienes permiso para editar este artículo.", "danger")
        return redirect(url_for('mercado.listar_material'))

    if request.method == 'POST':
        datos_actualizados = {
            "categoria": request.form.get('categoria'),
            "estado": request.form.get('estado'),
            "titulo": request.form.get('titulo', '').strip(),
            "descripcion": request.form.get('descripcion', '').strip(),
            "contacto": request.form.get('contacto', '').strip(),
            "precio": float(request.form.get('precio', 0))
        }

        # 2. Actualizar en BD
        mongo.db.mercado.update_one({"_id": obj_id}, {"$set": datos_actualizados})
        
        # 3. Registrar auditoría detallada
        LogAuditoria.registrar_edicion("EDICION_MERCADO", articulo_id, articulo_anterior, datos_actualizados)
        
        flash('Artículo actualizado correctamente', 'success')
        return redirect(url_for('mercado.listar_material'))
    
    return render_template('mercado/editar.html', articulo=articulo_anterior)