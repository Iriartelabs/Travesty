import os
import importlib.util
import inspect
from flask import Blueprint, Flask, render_template, url_for

class AddonRegistry:
    _instance = None
    addons = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def register(cls, addon_id, addon_info):
        # Añadir el addon al registro
        cls.addons[addon_id] = addon_info
    
    @classmethod
    def unregister(cls, addon_id):
        """
        Elimina un addon del registro
        
        Args:
            addon_id (str): ID del addon a eliminar
        """
        if addon_id in cls.addons:
            del cls.addons[addon_id]
    
    @classmethod
    def get_addons(cls):
        return cls.addons
    
    @classmethod
    def get_addon(cls, addon_id):
        return cls.addons.get(addon_id)
    
    @classmethod
    def get_all_addons(cls):
        """Método para obtener todos los addons registrados (para compatibilidad)"""
        return cls.get_addons()
    
    @classmethod
    def get_sidebar_items(cls):
        """Devuelve los elementos para mostrar en la barra lateral"""
        sidebar_items = []
        
        for addon_id, addon_info in cls.addons.items():
            # Solo incluir addons activos
            if addon_info.get('active', True):
                # Construir URL si no está definida
                route = addon_info.get('route', f'/{addon_id}')
                
                # Crear el elemento para la barra lateral
                sidebar_item = {
                    'name': addon_info.get('name', addon_id),
                    'description': addon_info.get('description', ''),
                    'icon': addon_info.get('icon', 'puzzle-piece'),
                    'route': route,
                    'id': addon_id
                }
                
                sidebar_items.append(sidebar_item)
        
        return sidebar_items
    
    @classmethod
    def initialize(cls, app):
        """Método legacy para compatibilidad con código existente"""
        # Iterar sobre todos los addons registrados
        for addon_id, addon_info in cls.addons.items():
            # Si el addon tiene un blueprint, registrarlo en la aplicación
            if 'blueprint' in addon_info and addon_info['blueprint'] is not None:
                app.register_blueprint(addon_info['blueprint'])
            else:
                # Crear un blueprint para el addon
                bp = Blueprint(addon_id, __name__)
                
                # Registrar la ruta principal
                bp.add_url_rule(
                    addon_info['route'],
                    view_func=addon_info['view_func'],
                    endpoint=addon_id
                )
                
                # Registrar el blueprint en la aplicación
                app.register_blueprint(bp)

def custom_render_template(addon_id, template_name, **context):
    """Renderiza una plantilla desde la carpeta ui/ del addon"""
    addon_info = AddonRegistry.get_addon(addon_id)
    if not addon_info:
        raise ValueError(f"No se encontró el addon con ID: {addon_id}")
    
    # Construir la ruta a la plantilla
    template_path = f"addons/{addon_id}/ui/{template_name}"
    
    return render_template(template_path, **context)

# Función para compatibilidad con código existente
def create_addon_template(template_name, **context):
    """Función legacy para compatibilidad - renderiza una plantilla de addon desde la carpeta templates/"""
    return render_template(template_name, **context)

def load_addons_from_directory(app=None, addons_dir='addons'):
    """Carga todos los addons desde la estructura de directorios
    
    Estructura esperada:
    addons/
        nombre_addon/
            src/
                nombre_addon.py  # Archivo principal del addon
            ui/
                nombre_addon.html  # Plantilla HTML del addon
    """
    # Obtener la lista de carpetas de addons (excluyendo __pycache__ y archivos)
    addon_folders = []
    try:
        if not os.path.exists(addons_dir):
            os.makedirs(addons_dir, exist_ok=True)
            print(f"Creado directorio de addons: {addons_dir}")
            return
            
        addon_folders = [f for f in os.listdir(addons_dir) 
                       if os.path.isdir(os.path.join(addons_dir, f)) and 
                       not f.startswith('__')]
    except FileNotFoundError:
        print(f"Directorio de addons no encontrado: {addons_dir}")
        return
    
    for addon_folder in addon_folders:
        # Intentar cargar desde la nueva estructura
        addon_path = os.path.join(addons_dir, addon_folder, 'src', f'{addon_folder}.py')
        
        # Si no existe, intentar con la estructura antigua
        if not os.path.exists(addon_path):
            addon_path = os.path.join(addons_dir, f'{addon_folder}.py')
            if not os.path.exists(addon_path):
                continue
        
        try:
            # Cargar el módulo dinámicamente
            spec = importlib.util.spec_from_file_location(addon_folder, addon_path)
            addon_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(addon_module)
            
            # El addon debe registrarse a sí mismo durante la importación
            print(f"Addon cargado: {addon_folder}")
        except Exception as e:
            print(f"Error al cargar el addon {addon_folder}: {str(e)}")
    
    # Si se proporcionó una aplicación, registrar los addons como blueprints
    if app is not None:
        for addon_id, addon_info in AddonRegistry.addons.items():
            if 'blueprint' in addon_info and addon_info['blueprint'] is not None:
                # Si tiene un blueprint definido, registrarlo directamente
                app.register_blueprint(addon_info['blueprint'])
            else:
                # Crear un blueprint basado en la función de vista y la ruta
                bp = Blueprint(addon_id, __name__, 
                            template_folder=os.path.join(addons_dir, addon_id, 'ui'))
                
                # Registrar la función de vista principal
                bp.add_url_rule(addon_info['route'], 
                            view_func=addon_info['view_func'], 
                            endpoint=addon_id)
                
                # Almacenar el blueprint en la información del addon
                addon_info['blueprint'] = bp
                
                # Registrar el blueprint en la aplicación
                app.register_blueprint(bp)

def setup_addons_for_app(app):
    """Configurar el sistema de addons para la aplicación Flask"""
    # Configurar carpeta de plantillas personalizada
    template_folder = os.path.abspath('addons')
    app.jinja_loader.searchpath.append(template_folder)
    
    # Cargar los addons
    load_addons_from_directory(app)