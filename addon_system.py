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
    
    @classmethod
    def register(cls, name, metadata):
        """Registra un nuevo addon en el sistema"""
        if name in cls._addons:
            logger.warning(f"El addon '{name}' ya está registrado. Se sobrescribirá.")
        
        # Validar metadata requerida
        required_fields = ['name', 'route', 'view_func', 'template', 'icon', 'description']
        for field in required_fields:
            if field not in metadata:
                logger.error(f"El addon '{name}' no tiene el campo requerido '{field}'")
                return False
        
        cls._addons[name] = metadata
        cls._routes[metadata['route']] = metadata['view_func']
        
        # Agregar a la barra lateral si está activo
        if metadata.get('active', True):
            cls._sidebar_items.append({
                'name': metadata['name'],
                'route': metadata['route'],
                'icon': metadata['icon']
            })
        
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
        if cls._initialized:
            logger.warning("El sistema de addons ya está inicializado.")
            return
        
        # Registrar cada addon como un Blueprint
        for name, metadata in cls._addons.items():
            route = metadata['route']
            view_func = metadata['view_func']
            
            # Crear y registrar el blueprint
            blueprint = Blueprint(name, __name__, template_folder='templates')
            blueprint.route(route)(view_func)
            app.register_blueprint(blueprint)
            
            logger.info(f"Ruta '{route}' registrada para el addon '{name}'")
        
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
    
    # [Resto del código de create_addon_template permanece igual]
    
    return True