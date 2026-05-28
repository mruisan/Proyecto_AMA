# routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from models.log_model import LogAuditoria
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario' in session:
        return redirect(url_for('panel.dashboard'))

    if request.method == 'POST':
        usuario_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()

        user = mongo.db.usuarios.find_one({"usuario": usuario_input})

        if user and check_password_hash(user['password'], password_input):
            session['usuario'] = {
                "_id": str(user['_id']),
                "usuario": user['usuario'],
                "nombre": user.get('nombre', user['usuario']),
                "apellidos": user.get('apellidos', ''),
                "rol": user.get('rol', 'usuario')
            }
            
            LogAuditoria.registrar("LOGIN_EXITOSO", f"Usuario {usuario_input} inició sesión.")
            
            # COMPROBACIÓN DE CAMBIO DE CONTRASEÑA OBLIGATORIO
            if user.get('cambiar_password', False):
                flash("Por seguridad, debes cambiar tu contraseña inicial.", "warning")
                return redirect(url_for('auth.cambiar_password_obligatorio'))
            
            flash(f"Bienvenido, {session['usuario']['nombre']}.", "success")
            return redirect(url_for('panel.dashboard'))
        else:
            flash("Credenciales incorrectas.", "danger")
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
def cambiar_password_obligatorio():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password', '').strip()
        confirmar_password = request.form.get('confirmar_password', '').strip()

        if nueva_password != confirmar_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('auth.cambiar_password_obligatorio'))

        # Actualizar contraseña y quitar flag de cambio obligatorio
        mongo.db.usuarios.update_one(
            {"_id": ObjectId(session['usuario']['_id'])},
            {"$set": {
                "password": generate_password_hash(nueva_password),
                "cambiar_password": False
            }}
        )
        flash("Contraseña actualizada con éxito.", "success")
        return redirect(url_for('panel.dashboard'))

    return render_template('cambiar_password.html')

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()
        # ... (resto de campos)

        usuario_existente = mongo.db.usuarios.find_one({"usuario": usuario_input})
        if usuario_existente:
            flash("El usuario ya existe.", "warning")
            return redirect(url_for('auth.registro'))

        mongo.db.usuarios.insert_one({
            "usuario": usuario_input,
            "password": generate_password_hash(password_input),
            "nombre": request.form.get('nombre', usuario_input),
            "apellidos": request.form.get('apellidos', ''),
            "rol": request.form.get('rol', 'militar'),
            "cambiar_password": False # Los auto-registrados no necesitan cambio forzoso
        })
        
        flash("Registro exitoso.", "success")
        return redirect(url_for('auth.login'))

    return render_template('registro.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for('auth.login'))

