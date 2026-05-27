# routes/panel_routes.py
from flask import Blueprint, render_template, session

panel_bp = Blueprint('panel', __name__)

@panel_bp.route('/dashboard')
def dashboard():
    # Ruta de entrada pública. 
    # La lógica de Jinja2 en las plantillas (base.html y panel.html) se encargará de 
    # mostrar u ocultar los elementos dinámicamente según si existe 'session.usuario'.
    return render_template('panel.html')