# routes/ocio_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mongo
from bson.objectid import ObjectId
from models.log_model import LogAuditoria

ocio_bp = Blueprint('ocio', __name__, url_prefix='/ocio')

@ocio_bp.route('/')
def listar_planes():
    # RUTA LIBERADA: Se elimina la restricción obligatoria de inicio de sesión.
    # Cualquier visitante o compañero puede consultar y filtrar las propuestas de actividades.
    
    # 1. Capturamos los criterios independientes y opcionales del formulario de ocio
    categoria = request.args.get('categoria', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()  # Recibe YYYY-MM-DD
    fecha_hasta = request.args.get('fecha_hasta', '').strip()  # Recibe YYYY-MM-DD
    lugar = request.args.get('lugar', '').strip()
    que_plan = request.args.get('que_plan', '').strip()
    
    # 2. Construimos el filtro dinámico incremental para MongoDB
    filtro = {}
    
    if categoria:
        filtro['categoria'] = categoria
        
    if lugar:
        # Búsqueda por coincidencia parcial en la localización (insensible a mayúsculas)
        filtro['lugar'] = {"$regex": lugar, "$options": "i"}
        
    if que_plan:
        # Busca texto libre tanto en el título como en la descripción de la actividad
        filtro['$or'] = [
            {"titulo": {"$regex": que_plan, "$options": "i"}},
            {"descripcion": {"$regex": que_plan, "$options": "i"}}
        ]
        
    # Lógica de filtrado de fechas adaptada a strings ISO (YYYY-MM-DDTHH:MM)
    if fecha_desde or fecha_hasta:
        filtro['fecha'] = {}
        if fecha_desde:
            # Compara directamente en orden alfabético-temporal (ej: '2026-05-20' <= '2026-05-24T18:00')
            filtro['fecha']['$gte'] = fecha_desde
        if fecha_hasta:
            # Añadimos 'T23:59' al límite superior para incluir los eventos de la tarde/noche de ese día
            filtro['fecha']['$lte'] = f"{fecha_hasta}T23:59"

    # 3. Recupera los planes aplicando el filtro dinámico, ordenados de más reciente a más antiguo
    planes = list(mongo.db.ocio.find(filtro).sort("_id", -1))
    
    # Variable de control para saber si se ha aplicado algún filtro en la interfaz
    ha_filtrado = bool(categoria or fecha_desde or fecha_hasta or lugar or que_plan)
    
    # 4. Enviamos los resultados junto con los parámetros para mantener los valores en los inputs
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
    # RUTA PROTEGIDA: Exige inicio de sesión únicamente al querer publicar una nueva propuesta
    if 'usuario' not in session:
        flash("Debes iniciar sesión para proponer un plan o actividad de ocio.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # CAPTURA SANEADA: Extraemos el identificador de la nueva estructura de sesión
        creador = session['usuario']['usuario']
        categoria = request.form.get('categoria')
        # Captura el string nativo 'YYYY-MM-DDTHH:MM' directo del selector de Bootstrap
        fecha = request.form.get('fecha', '').strip()
        lugar = request.form.get('lugar', '').strip()
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        contacto = request.form.get('contacto', '').strip()

        # ESTRUCTURA SANEADA: Guardamos con la clave exacta que buscar.html espera
        nuevo_plan = {
            "creador_usuario": creador,
            "categoria": categoria,
            "fecha": fecha,  # Guardado limpio en la base de datos
            "lugar": lugar,
            "titulo": titulo,
            "descripcion": descripcion,
            "contacto": contacto
        }

        mongo.db.ocio.insert_one(nuevo_plan)
        
        # Registro en la tabla de auditoría para seguridad de la app
        LogAuditoria.registrar("PUBLICACION_OCIO", f"Usuario {creador} propuso actividad: {titulo}")
        
        flash("Actividad propuesta con éxito en el tablón.", "success")
        return redirect(url_for('ocio.listar_planes'))

    return render_template('ocio/crear.html')

@ocio_bp.route('/eliminar/<string:plan_id>', methods=['POST'])
def eliminar_plan(plan_id):
    # RUTA PROTEGIDA: Requiere sesión activa absoluta para la retirada del sistema
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    usuario_actual = session['usuario']['usuario']
    rol_actual = session['usuario']['rol']

    plan = mongo.db.ocio.find_one({"_id": ObjectId(plan_id)})
    
    if not plan:
        flash("La actividad ya no existe o ha sido cancelada.", "danger")
        return redirect(url_for('ocio.listar_planes'))

    # VALIDACIÓN STRICTA: El borrado solo procede si eres el dueño legítimo o el admin
    if plan.get('creador_usuario') == usuario_actual or rol_actual == 'admin':
        mongo.db.ocio.delete_one({"_id": ObjectId(plan_id)})
        LogAuditoria.registrar("ELIMINACION_OCIO", f"Actividad {plan_id} eliminada por {usuario_actual}")
        flash("La propuesta de actividad ha sido eliminada correctamente.", "success")
    else:
        flash("No tienes permisos para cancelar esta actividad.", "danger")
        
    return redirect(url_for('ocio.listar_planes'))