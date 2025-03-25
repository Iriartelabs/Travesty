"""
Sistema de addons para DAS Trader Analyzer
"""
import os
import importlib.util
import inspect
import logging
from flask import Blueprint, url_for

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AddonRegistry:
    """Registro central de addons"""
    _addons = {}
    _routes = {}
    _sidebar_items = []
    _initialized = False
    _app = None  # Referencia a la aplicación Flask
    
    @classmethod
    def register(cls, name, metadata):
        """Registra un nuevo addon en el sistema"""
        # Verificar si ya existe un addon con la misma ruta
        for existing_name, existing_meta in cls._addons.items():
            if existing_meta['route'] == metadata['route']:
                # Ruta duplicada detectada, actualizar en lugar de crear nuevo
                logger.warning(f"Ruta '{metadata['route']}' ya registrada. Actualizando addon '{name}'.")
                
                # Actualizar addon existente
                cls._addons[existing_name] = metadata
                
                # Actualizar entry en sidebar items
                for i, item in enumerate(cls._sidebar_items):
                    if item['route'] == metadata['route']:
                        cls._sidebar_items[i] = {
                            'name': metadata['name'],
                            'route': metadata['route'],
                            'icon': metadata['icon']
                        }
                
                return True
        
        # Verificar si el nombre ya existe
        if name in cls._addons:
            logger.warning(f"El addon '{name}' ya está registrado. Se sobrescribirá.")
            
            # Eliminar entradas antiguas de la barra lateral
            cls._sidebar_items = [item for item in cls._sidebar_items 
                                 if item['name'] != cls._addons[name]['name']]
        
        # Continuar con el registro normal
        cls._addons[name] = metadata
        cls._routes[metadata['route']] = metadata['view_func']
        
        # Agregar a la barra lateral si está activo
        if metadata.get('active', True):
            cls._sidebar_items.append({
                'name': metadata['name'],
                'route': metadata['route'],
                'icon': metadata['icon']
            })
        
        # Si la aplicación ya está inicializada, intentar registrar la ruta
        if cls._initialized and cls._app and not cls._app.debug:
            try:
                blueprint = Blueprint(name, __name__, template_folder='templates')
                blueprint.route(metadata['route'])(metadata['view_func'])
                cls._app.register_blueprint(blueprint)
                logger.info(f"Ruta '{metadata['route']}' registrada dinámicamente para el addon '{name}'")
            except Exception as e:
                logger.error(f"No se pudo registrar la ruta dinámicamente: {e}")
        
        logger.info(f"Addon '{name}' registrado correctamente.")
        return True
    
    @classmethod
    def get_addon(cls, name):
        """Obtiene la información de un addon por su nombre"""
        return cls._addons.get(name)
    
    @classmethod
    def get_all_addons(cls):
        """Obtiene todos los addons registrados"""
        return cls._addons
    
    @classmethod
    def get_sidebar_items(cls):
        """Obtiene los elementos para mostrar en la barra lateral"""
        return sorted(cls._sidebar_items, key=lambda x: x['name'])
    
    @classmethod
    def get_view_function(cls, route):
        """Obtiene la función de vista para una ruta específica"""
        return cls._routes.get(route)
    
    @classmethod
    def initialize(cls, app):
        """Inicializa el sistema de addons, registrando las rutas en Flask"""
        cls._app = app  # Guardar referencia a la aplicación
        
        if cls._initialized:
            logger.warning("El sistema de addons ya está inicializado.")
            return
        
        # Registrar cada addon como un Blueprint
        for name, metadata in cls._addons.items():
            route = metadata['route']
            view_func = metadata['view_func']
            
            # Asegurar que la ruta comienza con /
            if not route.startswith('/'):
                route = '/' + route
                metadata['route'] = route
            
            # Crear y registrar el blueprint
            blueprint_name = f"addon_{name}"
            blueprint = Blueprint(blueprint_name, __name__, template_folder='templates')
            blueprint.route(route)(view_func)
            try:
                app.register_blueprint(blueprint)
                logger.info(f"Ruta '{route}' registrada para el addon '{name}'")
            except Exception as e:
                logger.error(f"Error al registrar la ruta '{route}' para addon '{name}': {e}")
        
        # Añadir la lista de addons al contexto global de las plantillas
        @app.context_processor
        def inject_addons():
            return {
                'sidebar_items': cls.get_sidebar_items(),
                'addons': cls._addons
            }
        
        cls._initialized = True
        logger.info(f"Sistema de addons inicializado con {len(cls._addons)} addons")

def load_addons_from_directory(directory='addons'):
    """Carga automáticamente todos los addons desde un directorio"""
    if not os.path.exists(directory):
        logger.warning(f"El directorio de addons '{directory}' no existe.")
        os.makedirs(directory)
        # Crear un archivo __init__.py para marcar como paquete
        with open(os.path.join(directory, '__init__.py'), 'w') as f:
            f.write('# Paquete de addons para DAS Trader Analyzer')
        logger.info(f"Directorio de addons '{directory}' creado.")
        return
    
    # Asegurar que existe el __init__.py para que sea un paquete
    init_path = os.path.join(directory, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('# Paquete de addons para DAS Trader Analyzer')
    
    # Buscar archivos Python en el directorio
    addon_files = [f for f in os.listdir(directory) 
                  if f.endswith('.py') and f != '__init__.py']
    
    loaded_count = 0
    for filename in addon_files:
        module_name = filename[:-3]  # Quitar .py
        module_path = os.path.join(directory, filename)
        
        try:
            # Cargar el módulo dinámicamente
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Verificar si tiene función de registro
            if hasattr(module, 'register_addon'):
                module.register_addon()
                loaded_count += 1
                logger.info(f"Addon '{module_name}' cargado correctamente.")
            else:
                logger.warning(f"El archivo '{filename}' no tiene función register_addon().")
        
        except Exception as e:
            logger.error(f"Error al cargar el addon '{module_name}': {str(e)}")
    
    logger.info(f"Se cargaron {loaded_count} addons de {len(addon_files)} archivos.")

def create_addon_template(name, route, description, icon="chart-bar"):
    """Crea una plantilla para un nuevo addon"""
    if not os.path.exists('addons'):
        os.makedirs('addons')
    
    # Normalizar el nombre
    module_name = name.lower().replace(' ', '_')
    file_path = os.path.join('addons', f"{module_name}.py")
    
    # Comprobar si ya existe
    if os.path.exists(file_path):
        logger.warning(f"El addon '{module_name}' ya existe.")
        return False
    
    # Asegurar que la ruta comienza con /
    if not route.startswith('/'):
        route = '/' + route
    
    # Crear el archivo Python del addon
    template = f'''"""
Addon: {name}
Descripción: {description}
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash
import json

def {module_name}_view():
    """Vista principal para el addon {name}"""
    # Importar la variable global desde app.py
    from app import processed_data
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    # Realizar análisis específico
    # TODO: Implementar lógica de análisis personalizada
    
    # Ejemplo: datos para la plantilla
    data = {{
        'title': '{name}',
        'description': '{description}'
    }}
    
    # Renderizar la plantilla
    return render_template(
        '{module_name}.html',
        data=data,
        processed_data=processed_data
    )

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('{module_name}', {{
        'name': '{name}',
        'description': '{description}',
        'route': '{route}',
        'view_func': {module_name}_view,
        'template': '{module_name}.html',
        'icon': '{icon}',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer User'
    }})

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
'''
    
    # Guardar el archivo Python
    with open(file_path, 'w') as f:
        f.write(template)
    
    # Crear la plantilla HTML
    html_path = os.path.join('templates', f"{module_name}.html")
    
    # Usar triple comillas para la plantilla HTML para evitar problemas con las llaves
    html_template = """{% extends 'base.html' %}

{% block title %}""" + name + """ - DAS Trader Analyzer{% endblock %}

{% block header %}""" + name + """{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">""" + name + """</h6>
            </div>
            <div class="card-body">
                <p>""" + description + """</p>
                <div class="alert alert-info">
                    <p>Este es un addon personalizado. Edita los archivos:</p>
                    <ul>
                        <li><code>addons/""" + module_name + """.py</code>: Para la lógica y análisis</li>
                        <li><code>templates/""" + module_name + """.html</code>: Para la interfaz de usuario</li>
                    </ul>
                </div>
                
                <!-- Aquí va tu contenido personalizado -->
                
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
    
    # Guardar la plantilla HTML
    with open(html_path, 'w') as f:
        f.write(html_template)
    
    logger.info(f"Addon '{name}' creado con éxito. Archivos generados: {file_path} y {html_path}")
    return True