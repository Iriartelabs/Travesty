from flask import Flask

from config import get_config
from services.cache_manager import load_processed_data

# Variable global para almacenar datos procesados
processed_data = None

def create_app(config_name='development'):
    """Crear y configurar la aplicación Flask"""
    global processed_data
    
    # Obtener configuración
    config = get_config(config_name)
    
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config)
    
    # Intentar cargar datos procesados
    processed_data = load_processed_data(config.DATA_CACHE_PATH)
    
    # Importar blueprints aquí para evitar importaciones circulares
    from routes.main import main_bp
    from routes.data_upload import upload_bp
    from routes.analysis import analysis_bp
    
    # Importar extensiones
    from extensions import init_extensions
    
    # Inicializar extensiones (filtros, etc.)
    init_extensions(app)
    
    # Registrar blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analysis_bp)
    
    # Cargar addons
    from addon_system import load_addons_from_directory, AddonRegistry
    load_addons_from_directory()
    
    # Inicializar sistema de addons
    AddonRegistry.initialize(app)
    
    return app

def update_processed_data(new_data=None):
    """
    Actualiza o devuelve los datos procesados globales
    
    Args:
        new_data (dict, optional): Nuevos datos para reemplazar los existentes
    
    Returns:
        dict or None: Datos procesados actuales
    """
    global processed_data
    
    if new_data is not None:
        processed_data = new_data
    
    return processed_data

def main():
    """Punto de entrada principal"""
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

if __name__ == '__main__':
    main()
