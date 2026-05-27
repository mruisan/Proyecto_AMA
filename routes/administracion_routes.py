# routes/administracion_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, session, make_response, request
from extensions import mongo
from datetime import datetime
import io 
from bson.objectid import ObjectId 
from werkzeug.security import generate_password_hash

# Importaciones específicas de ReportLab
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. DECLARACIÓN DEL BLUEPRINT 
admin_bp = Blueprint('admin', __name__, url_prefix='/administracion')

# ========================================================
# VISTAS DE AUDITORÍA
# ========================================================
@admin_bp.route('/auditoria')
def ver_logs():
    if 'usuario' not in session or session['usuario'].get('rol') != 'admin':
        return redirect(url_for('auth.login'))
    lista_logs = list(mongo.db.logs.find().sort("fecha", -1))
    return render_template('administracion.html', logs=lista_logs, seccion='auditoria')

@admin_bp.route('/auditoria/pdf')
def exportar_pdf():
    if 'usuario' not in session or session['usuario'].get('rol') != 'admin':
        return "Acceso denegado", 403
    lista_logs = list(mongo.db.logs.find().sort("fecha", -1))
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    story = []
    styles = getSampleStyleSheet()
    style_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18)
    
    story.append(Paragraph("REGISTRO OFICIAL DE AUDITORÍA DE SEGURIDAD", style_titulo))
    table_data = [["Fecha (UTC)", "Acción", "Usuario", "Descripción", "IP Origen"]]
    for log in lista_logs:
        table_data.append([
            log.get('fecha', '').strftime('%d/%m/%Y %H:%M:%S'),
            str(log.get('accion', '')),
            str(log.get('usuario', '')),
            str(log.get('descripcion', '')),
            str(log.get('ip_origen', ''))
        ])
    log_table = Table(table_data, colWidths=[120, 110, 85, 315, 102])
    log_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(log_table)
    doc.build(story)
    
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Disposition'] = f"attachment; filename=Auditoria_{datetime.now().strftime('%Y%m%d')}.pdf"
    response.headers['Content-Type'] = 'application/pdf'
    return response

# ========================================================
# VISTAS DE GESTIÓN DE USUARIOS
# ========================================================
@admin_bp.route('/usuarios')
def gestionar_usuarios():
    if 'usuario' not in session or session['usuario'].get('rol') != 'admin':
        return redirect(url_for('panel.dashboard'))
    lista_usuarios = list(mongo.db.usuarios.find().sort("usuario", 1))
    return render_template('administracion.html', usuarios=lista_usuarios, seccion='usuarios')

# ========================================================
# ACCIONES DE GESTIÓN (CRUD)
# ========================================================
@admin_bp.route('/usuarios/cambiar_rol/<id_usuario>', methods=['POST'])
def cambiar_rol(id_usuario):
    nuevo_rol = request.form.get('nuevo_rol')
    mongo.db.usuarios.update_one({"_id": ObjectId(id_usuario)}, {"$set": {"rol": nuevo_rol}})
    flash("Rol de usuario actualizado.", "success")
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/usuarios/alternar_estado/<id_usuario>', methods=['POST'])
def alternar_estado(id_usuario):
    usuario = mongo.db.usuarios.find_one({"_id": ObjectId(id_usuario)})
    if usuario and usuario['usuario'] != session['usuario']['usuario']:
        nuevo_estado = not usuario.get('activo', True)
        mongo.db.usuarios.update_one({"_id": ObjectId(id_usuario)}, {"$set": {"activo": nuevo_estado}})
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/usuarios/registrar', methods=['POST'])
def registrar_usuario():
    existe = mongo.db.usuarios.find_one({"usuario": request.form.get("usuario")})
    if existe:
        flash("Error: El usuario ya existe.", "danger")
        return redirect(url_for('admin.gestionar_usuarios'))
    
    mongo.db.usuarios.insert_one({
        "usuario": request.form.get("usuario"),
        "nombre": request.form.get("nombre"),
        "apellidos": request.form.get("apellidos"),
        "correo": request.form.get("correo"),
        "rol": request.form.get("rol", "militar"),
        "password": generate_password_hash(request.form.get("password")),
        "activo": True,
        "cambiar_password": True 
    })
    flash("Usuario registrado exitosamente.", "success")
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/usuarios/editar/<id_usuario>', methods=['POST'])
def editar_usuario(id_usuario):
    mongo.db.usuarios.update_one({"_id": ObjectId(id_usuario)}, {"$set": {
        "nombre": request.form.get("nombre"),
        "apellidos": request.form.get("apellidos"),
        "correo": request.form.get("correo")
    }})
    flash("Datos del usuario actualizados correctamente.", "success")
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/usuarios/restablecer_password/<id_usuario>', methods=['POST'])
def restablecer_password(id_usuario):
    mongo.db.usuarios.update_one(
        {"_id": ObjectId(id_usuario)}, 
        {"$set": {
            "password": generate_password_hash("12345678"),
            "cambiar_password": True
        }}
    )
    flash("Contraseña restablecida a '12345678'. El usuario deberá cambiarla al acceder.", "info")
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/usuarios/eliminar/<id_usuario>', methods=['POST'])
def eliminar_usuario(id_usuario):
    usuario = mongo.db.usuarios.find_one({"_id": ObjectId(id_usuario)})
    if usuario and usuario['usuario'] != 'admin':
        mongo.db.usuarios.delete_one({"_id": ObjectId(id_usuario)})
        flash(f"Usuario {usuario['usuario']} eliminado.", "danger")
    return redirect(url_for('admin.gestionar_usuarios'))