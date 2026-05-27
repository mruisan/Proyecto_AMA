# routes/servicios_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mongo
from bson.objectid import ObjectId
from models.log_model import LogAuditoria

servicios_bp = Blueprint('servicios', __name__, url_prefix='/servicios')

@servicios_bp.route('/')
def listar_servicios():
    # RUTA LIBERADA: Se elimina la restricción obligatoria de inicio de sesión.
    # Cualquier visitante puede visualizar y buscar los anuncios de colaboración.
    
    # 1. Capturamos los criterios independientes del formulario avanzado
    tipo = request.args.get('tipo', '').strip()
    categoria = request.args.get('categoria', '').strip()
    descripcion = request.args.get('descripcion', '').strip()
    
    # 2. Construimos el filtro dinámico incremental para MongoDB
    filtro = {}
    
    if tipo:
        # Filtra exactamente por "Ofrecer" o "Buscar"
        filtro['tipo'] = tipo
        
    if categoria:
        # Filtra por la categoría seleccionada
        filtro['categoria'] = categoria
        
    if descripcion:
        # Filtra por texto libre tanto en la descripción como en el título
        filtro['$or'] = [
            {"descripcion": {"$regex": descripcion, "$options": "i"}},
            {"titulo": {"$regex": descripcion, "$options": "i"}}
        ]
    
    # 3. Traemos los servicios aplicando el filtro y ordenados del más reciente al más antiguo
    servicios = list(mongo.db.servicios.find(filtro).sort("_id", -1))
    
    # Variable de control para saber si el usuario ha aplicado algún filtro en la interfaz
    ha_filtrado = bool(tipo or categoria or descripcion)
    
    # 4. Enviamos los resultados junto con los parámetros para mantener los valores en la vista
    return render_template(
        'servicios/buscar.html', 
        servicios=servicios, 
        tipo=tipo, 
        categoria=categoria, 
        descripcion=descripcion,
        ha_filtrado=ha_filtrado
    )

@servicios_bp.route('/crear', methods=['GET', 'POST'])
def crear_servicio():
    # RUTA PROTEGIDA: Solo los usuarios autenticados pueden publicar un nuevo servicio
    if 'usuario' not in session:
        flash("Debes iniciar sesión para publicar un anuncio en el tablón de servicios.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        propietario = session['usuario']['usuario']
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        contacto = request.form.get('contacto', '').strip()
        
        origen = request.form.get('origen', '').strip() if categoria == 'Movilidad/Coche' else None
        destino = request.form.get('destino', '').strip() if categoria == 'Movilidad/Coche' else None
        plazas = request.form.get('plazas') if categoria == 'Movilidad/Coche' else None

        nuevo_servicio = {
            "usuario_usuario": propietario,
            "tipo": tipo,
            "categoria": categoria,
            "titulo": titulo,
            "descripcion": descripcion,
            "contacto": contacto,
            "origen": origen,
            "destino": destino,
            "plazas": int(plazas) if plazas else None
        }

        mongo.db.servicios.insert_one(nuevo_servicio)
        LogAuditoria.registrar("PUBLICACION_SERVICIO", f"Usuario {propietario} publicó anuncio: {titulo}")
        
        flash("Anuncio publicado con éxito en el tablón.", "success")
        return redirect(url_for('servicios.listar_servicios'))

    return render_template('servicios/crear.html')

@servicios_bp.route('/eliminar/<string:servicio_id>', methods=['POST'])
def eliminar_servicio(servicio_id):
    # RUTA PROTEGIDA: Requiere inicio de sesión absoluto para la retirada de elementos
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    usuario_actual = session['usuario']['usuario']
    rol_actual = session['usuario']['rol']

    servicio = mongo.db.servicios.find_one({"_id": ObjectId(servicio_id)})
    
    if not servicio:
        flash("El anuncio no existe o ya ha sido retirado.", "danger")
        return redirect(url_for('servicios.listar_servicios'))

    # Verificación estricta de rol o autoría
    if servicio.get('usuario_usuario') == usuario_actual or rol_actual == 'admin':
        mongo.db.servicios.delete_one({"_id": ObjectId(servicio_id)})
        LogAuditoria.registrar("ELIMINACION_SERVICIO", f"Anuncio {servicio_id} eliminado por {usuario_actual}")
        flash("Anuncio eliminado correctamente del sistema.", "success")
    else:
        flash("No tiene autorización para eliminar este anuncio.", "danger")
        
    return redirect(url_for('servicios.listar_servicios'))