import os
import zipfile
import shutil
import tempfile
import importlib.util
from pkg_resources import parse_version  # Para comparación de versiones
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from addon_system import AddonRegistry, load_addons_from_directory
from config import Config

# Definimos el blueprint
analysis_bp = Blueprint('analysis', __name__)

# Función para gestionar addons
@analysis_bp.route('/manage-addons')
def manage_addons():
    """Página de gestión de addons"""
    # Obtener lista de addons registrados
    registered_addons = AddonRegistry.get_all_addons()
    
    # Obtener elementos para la barra lateral
    sidebar_items = AddonRegistry.get_sidebar_items()
    
    return render_template(
        'manage_addons.html',
        addons=registered_addons,
        sidebar_items=sidebar_items
    )

# Función para recargar addons
@analysis_bp.route('/reload-addons')
def reload_addons():
    """Recarga todos los addons"""
    load_addons_from_directory()
    flash('Addons recargados correctamente', 'success')
    return redirect(url_for('analysis.manage_addons'))

# Función para crear un nuevo addon
@analysis_bp.route('/create-new-addon', methods=['POST'])
def create_new_addon():
    """Crea un nuevo addon básico"""
    name = request.form.get('name', '').strip()
    route = request.form.get('route', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'chart-bar').strip()
    
    if not name:
        flash('El nombre del addon es obligatorio', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    # Normalizar el nombre para usarlo como ID
    addon_id = name.lower().replace(' ', '_')
    
    # Si no se proporciona ruta, generarla a partir del nombre
    if not route:
        route = '/' + addon_id.replace('_', '-')
    elif not route.startswith('/'):
        route = '/' + route
    
    # Verificar si ya existe un addon con ese ID
    existing_addons = AddonRegistry.get_all_addons()
    if addon_id in existing_addons:
        flash(f'Ya existe un addon con el nombre "{name}"', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    # Crear directorios para el nuevo addon
    addon_dir = os.path.join(Config.ADDONS_DIR, addon_id)
    src_dir = os.path.join(addon_dir, 'src')
    ui_dir = os.path.join(addon_dir, 'ui')
    
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(ui_dir, exist_ok=True)
    
    # Crear archivo Python básico
    py_template = f'''"""
Addon: {name}
Descripción: {description}
Versión: 1.0.0
Autor: Tu Nombre
"""
from addon_system import AddonRegistry, custom_render_template
from flask import redirect, url_for, flash, request
import json

from config import Config
from services.cache_manager import load_processed_data

def {addon_id}_view():
    """Función principal del addon"""
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Implementar tu lógica personalizada aquí
    
    # Renderizar la plantilla
    return custom_render_template(
        '{addon_id}',  # ID del addon
        '{addon_id}.html',  # Nombre del archivo HTML
        processed_data=processed_data
    )

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('{addon_id}', {{
        'name': '{name}',
        'description': '{description}',
        'route': '{route}',
        'view_func': {addon_id}_view,
        'template': '{addon_id}.html',
        'icon': '{icon}',
        'active': True,
        'version': '1.0.0',  # <-- Puedes modificar esta versión según necesites
        'author': 'Tu Nombre'  # <-- Actualiza con tu nombre/organización
    }})

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
'''
    
    # Crear archivo HTML básico
    html_template = f'''{{{{ extends 'base.html' }}}}

{{{{ block title }}}}{name} - Travesty Analyzer{{{{ endblock }}}}

{{{{ block header }}}}{name}{{{{ endblock }}}}

{{{{ block content }}}}
<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">{name}</h6>
            </div>
            <div class="card-body">
                <p>{description}</p>
                
                <!-- Implementa tu contenido personalizado aquí -->
                <div class="alert alert-info">
                    <p>Este es un addon recién creado. Edita los archivos para implementar tu funcionalidad personalizada.</p>
                    <ul>
                        <li>Archivo Python: <code>addons/{addon_id}/src/{addon_id}.py</code>
                            <ul>
                                <li>Puedes personalizar la versión y el autor en el diccionario de registro</li>
                                <li>La versión sigue el formato semántico: MAYOR.MENOR.PARCHE (ej. 1.0.0)</li>
                            </ul>
                        </li>
                        <li>Plantilla HTML: <code>addons/{addon_id}/ui/{addon_id}.html</code></li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
{{{{ endblock }}}}
'''
    
    # Escribir archivos
    with open(os.path.join(src_dir, f'{addon_id}.py'), 'w', encoding='utf-8') as f:
        f.write(py_template)
    
    with open(os.path.join(ui_dir, f'{addon_id}.html'), 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    # Recargar addons
    load_addons_from_directory()
    
    flash(f'Addon "{name}" creado correctamente', 'success')
    return redirect(url_for('analysis.manage_addons'))

# Función para importar un addon desde un archivo ZIP
@analysis_bp.route('/import-addon-zip', methods=['POST'])
def import_addon_zip():
    """Importa un addon desde un archivo ZIP"""
    if 'addon_zip' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    file = request.files['addon_zip']
    
    if file.filename == '':
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    if not file.filename.endswith('.zip'):
        flash('El archivo debe tener extensión .zip', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    overwrite_existing = 'overwrite_existing' in request.form
    
    # Crear directorio temporal para extraer el ZIP
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(zip_path)
        
        # Verificar la estructura del ZIP
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Listar contenido del ZIP
                file_list = zip_ref.namelist()
                
                # Determinar el nombre del addon basado en el directorio de nivel superior
                # Asumimos que el ZIP contiene un directorio de nivel superior con el nombre del addon
                addon_dirs = set()
                for file_path in file_list:
                    parts = file_path.split('/')
                    if len(parts) > 1:
                        addon_dirs.add(parts[0])
                
                if not addon_dirs:
                    flash('El archivo ZIP no tiene la estructura correcta de addon. Se esperaba un directorio de nivel superior.', 'error')
                    return redirect(url_for('analysis.manage_addons'))
                
                if len(addon_dirs) > 1:
                    flash('El archivo ZIP contiene múltiples directorios de nivel superior. Solo debe contener un addon.', 'error')
                    return redirect(url_for('analysis.manage_addons'))
                
                addon_name = list(addon_dirs)[0]
                
                # Verificar si existe la estructura correcta de src y ui
                src_dir_exists = any(f.startswith(f"{addon_name}/src/") for f in file_list)
                ui_dir_exists = any(f.startswith(f"{addon_name}/ui/") for f in file_list)
                
                if not src_dir_exists or not ui_dir_exists:
                    flash(f'El addon "{addon_name}" no tiene la estructura correcta (carpetas src/ y ui/).', 'error')
                    return redirect(url_for('analysis.manage_addons'))
                
                # Verificar si existe un archivo Python principal en src/
                py_file_exists = any(f == f"{addon_name}/src/{addon_name}.py" for f in file_list)
                
                if not py_file_exists:
                    flash(f'No se encontró el archivo principal del addon en src/{addon_name}.py', 'error')
                    return redirect(url_for('analysis.manage_addons'))
                
                # Verificar si el addon ya existe
                addon_dest_path = os.path.join(Config.ADDONS_DIR, addon_name)
                if os.path.exists(addon_dest_path):
                    # Intentar cargar datos del addon existente para verificar versión
                    existing_addon_info = AddonRegistry.get_addon(addon_name)
                    
                    # Si es un reemplazo forzado, no hacer verificación
                    if overwrite_existing:
                        shutil.rmtree(addon_dest_path)
                    else:
                        # Verificar versiones
                        try:
                            # Extraer para leer la información de versión
                            with tempfile.TemporaryDirectory() as version_temp_dir:
                                # Extraer solo el archivo Python principal para verificar versión
                                zip_ref.extract(f"{addon_name}/src/{addon_name}.py", version_temp_dir)
                                
                                # Cargar módulo para obtener información
                                addon_path = os.path.join(version_temp_dir, addon_name, 'src', f'{addon_name}.py')
                                spec = importlib.util.spec_from_file_location(f"temp_{addon_name}", addon_path)
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                
                                # Buscar función register_addon para obtener datos
                                if hasattr(module, 'register_addon'):
                                    # Extraer información de versión simulando un registro
                                    version_info = {}
                                    def mock_register(id, info):
                                        nonlocal version_info
                                        version_info = info
                                    
                                    # Monkey patch temporal para obtener la información
                                    original_register = AddonRegistry.register
                                    AddonRegistry.register = mock_register
                                    module.register_addon()
                                    AddonRegistry.register = original_register
                                    
                                    # Comparar versiones
                                    if existing_addon_info and 'version' in existing_addon_info:
                                        existing_version = parse_version(existing_addon_info.get('version', '0.0.0'))
                                        new_version = parse_version(version_info.get('version', '0.0.0'))
                                        
                                        if new_version <= existing_version:
                                            flash(f'El addon "{addon_name}" ya tiene una versión igual o superior instalada. Para reemplazar, marca la opción "Sobrescribir si ya existe".', 'error')
                                            return redirect(url_for('analysis.manage_addons'))
                        except Exception as e:
                            # Si hay error en la verificación de versión, solicitar confirmación explícita
                            flash(f'No se pudo verificar la versión del addon. Para instalar, marca la opción "Sobrescribir si ya existe".', 'error')
                            return redirect(url_for('analysis.manage_addons'))
                        
                        # Si llegamos aquí, la versión es mayor y podemos reemplazar
                        shutil.rmtree(addon_dest_path)
                
                # Extraer solo el directorio del addon en la carpeta de addons
                os.makedirs(Config.ADDONS_DIR, exist_ok=True)
                
                # Extraer el ZIP
                zip_ref.extractall(Config.ADDONS_DIR)
                
                # Recargar addons
                load_addons_from_directory()
                
                flash(f'Addon "{addon_name}" importado con éxito', 'success')
                return redirect(url_for('analysis.manage_addons'))
                
        except zipfile.BadZipFile:
            flash('El archivo no es un ZIP válido', 'error')
            return redirect(url_for('analysis.manage_addons'))
        except Exception as e:
            flash(f'Error al procesar el archivo ZIP: {str(e)}', 'error')
            return redirect(url_for('analysis.manage_addons'))

# Función para exportar un addon a un archivo ZIP
@analysis_bp.route('/export-addon/<addon_id>')
def export_addon(addon_id):
    """Exporta un addon a un archivo ZIP"""
    addon_info = AddonRegistry.get_addon(addon_id)
    
    if not addon_info:
        flash(f'El addon "{addon_id}" no existe', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    addon_path = os.path.join(Config.ADDONS_DIR, addon_id)
    
    if not os.path.exists(addon_path):
        flash(f'No se encontró la carpeta del addon "{addon_id}"', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    # Crear directorio temporal para el ZIP
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_filename = f"{addon_id}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # Crear el archivo ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Agregar los archivos al ZIP
            for root, dirs, files in os.walk(addon_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calcular la ruta relativa dentro del ZIP
                    arcname = os.path.relpath(file_path, os.path.dirname(addon_path))
                    zipf.write(file_path, arcname)
        
        # Enviar el archivo al usuario
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

# Función para activar/desactivar un addon
@analysis_bp.route('/toggle-addon/<addon_id>')
def toggle_addon(addon_id):
    """Activa o desactiva un addon"""
    addon_info = AddonRegistry.get_addon(addon_id)
    
    if not addon_info:
        flash(f'El addon "{addon_id}" no existe', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    # Cambiar el estado del addon
    current_state = addon_info.get('active', True)
    addon_info['active'] = not current_state
    
    if current_state:
        flash(f'Addon "{addon_info.get("name", addon_id)}" desactivado', 'info')
    else:
        flash(f'Addon "{addon_info.get("name", addon_id)}" activado', 'success')
    
    return redirect(url_for('analysis.manage_addons'))

# Función para desinstalar un addon
@analysis_bp.route('/uninstall-addon/<addon_id>', methods=['POST'])
def uninstall_addon(addon_id):
    """Desinstala completamente un addon"""
    addon_info = AddonRegistry.get_addon(addon_id)
    
    if not addon_info:
        flash(f'El addon "{addon_id}" no existe', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    # Ruta del addon
    addon_path = os.path.join(Config.ADDONS_DIR, addon_id)
    
    if not os.path.exists(addon_path):
        flash(f'No se encontró la carpeta del addon "{addon_id}"', 'error')
        return redirect(url_for('analysis.manage_addons'))
    
    try:
        # Eliminar la carpeta del addon
        shutil.rmtree(addon_path)
        
        # Eliminar del registro
        AddonRegistry.unregister(addon_id)
        
        flash(f'Addon "{addon_info.get("name", addon_id)}" desinstalado correctamente', 'success')
    except Exception as e:
        flash(f'Error al desinstalar el addon: {str(e)}', 'error')
    
    # Recargar addons
    load_addons_from_directory()
    
    return redirect(url_for('analysis.manage_addons'))