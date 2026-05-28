# routes/ocio_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mongo
from bson.objectid import ObjectId
from bson.errors import InvalidId
from models.log_model import LogAuditoria

ocio_bp = Blueprint('ocio', __name__, url_prefix='/ocio')

@ocio_bp.route('/')
def listar_planes():
    categoria = request.args.get('categoria', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()
    lugar = request.args.get('lugar', '').strip()
    que_plan = request.args.get('que_plan', '').strip()
    
    filtro = {}
    if categoria:
        filtro['categoria'] = categoria
    if lugar:
        filtro['lugar'] = {"$regex": lugar, "$options": "i"}
    if que_plan:
        filtro['$or'] = [
            {"titulo": {"$regex": que_plan, "$options": "i"}},
            {"descripcion": {"$regex": que_plan, "$options": "i"}}
        ]
        
    if fecha_desde or fecha_hasta:
        filtro['fecha'] = {}
        if fecha_desde:
            filtro['fecha']['$gte'] = fecha_desde
        if fecha_hasta:
            filtro['fecha']['$lte'] = f"{fecha_hasta}T23:59"

    planes = list(mongo.db.ocio.find(filtro).sort("_id", -1))
    ha_filtrado = bool(categoria or fecha_desde or fecha_hasta or lugar or que_plan)
    
    return render_template(
        'ocio/buscar.html', 
        planes=planes,
        categoria=categoria,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        lugar=lugar,
        que_plan=que_plan,
        ha_filtrado=ha_filtrado
    )

@ocio_bp.route('/crear', methods=['GET', 'POST'])
def crear_plan():
    if 'usuario' not in session:
        flash("Debes iniciar sesión para proponer un plan.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nuevo_plan = {
            "creador_usuario": session['usuario']['usuario'],
            "categoria": request.form.get('categoria'),
            "fecha": request.form.get('fecha', '').strip(),
            "lugar": request.form.get('lugar', '').strip(),
            "titulo": request.form.get('titulo', '').strip(),
            "descripcion": request.form.get('descripcion', '').strip(),
            "contacto": request.form.get('contacto', '').strip()
        }

        mongo.db.ocio.insert_one(nuevo_plan)
        LogAuditoria.registrar("PUBLICACION_OCIO", f"Propuesta creada: {nuevo_plan['titulo']}")
        
        flash("Actividad propuesta con éxito.", "success")
        return redirect(url_for('ocio.listar_planes'))

    return render_template('ocio/crear.html')

@ocio_bp.route('/eliminar/<string:plan_id>', methods=['POST'])
def eliminar_plan(plan_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    plan = mongo.db.ocio.find_one({"_id": ObjectId(plan_id)})
    if not plan:
        flash("La actividad ya no existe.", "danger")
        return redirect(url_for('ocio.listar_planes'))

    if plan.get('creador_usuario') == session['usuario']['usuario'] or session['usuario']['rol'] == 'admin':
        mongo.db.ocio.delete_one({"_id": ObjectId(plan_id)})
        LogAuditoria.registrar("ELIMINACION_OCIO", f"Actividad {plan_id} eliminada.")
        flash("Actividad eliminada correctamente.", "success")
    else:
        flash("No tienes permisos.", "danger")
        
    return redirect(url_for('ocio.listar_planes'))

@ocio_bp.route('/editar/<plan_id>', methods=['GET', 'POST'])
def editar_plan(plan_id):
    if 'usuario' not in session:
        flash("Debes iniciar sesión para editar.", "danger")
        return redirect(url_for('auth.login'))

    try:
        obj_id = ObjectId(plan_id)
    except InvalidId:
        return redirect(url_for('ocio.listar_planes'))

    # 1. Recuperar estado ANTERIOR para el log
    plan_anterior = mongo.db.ocio.find_one({"_id": obj_id})
    if not plan_anterior:
        flash("La actividad no existe.", "danger")
        return redirect(url_for('ocio.listar_planes'))

    # Verificar permisos
    if session['usuario']['usuario'] != plan_anterior.get('creador_usuario') and session['usuario']['rol'] != 'admin':
        flash("No tienes permiso.", "danger")
        return redirect(url_for('ocio.listar_planes'))

    if request.method == 'POST':
        datos_actualizados = {
            "categoria": request.form.get('categoria'),
            "fecha": request.form.get('fecha', '').strip(),
            "lugar": request.form.get('lugar', '').strip(),
            "titulo": request.form.get('titulo', '').strip(),
            "descripcion": request.form.get('descripcion', '').strip(),
            "contacto": request.form.get('contacto', '').strip()
        }

        # 2. Actualizar en BD
        mongo.db.ocio.update_one({"_id": obj_id}, {"$set": datos_actualizados})
        
        # 3. Registrar auditoría detallada
        LogAuditoria.registrar_edicion("EDICION_OCIO", plan_id, plan_anterior, datos_actualizados)
        
        flash("Actividad actualizada correctamente.", "success")
        return redirect(url_for('ocio.listar_planes'))
    
    return render_template('ocio/editar.html', plan=plan_anterior)