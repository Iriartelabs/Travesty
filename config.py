import os

class Config:
    """Configuración base para la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'app-secret-key'
    
    # Rutas de datos
    DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    
    # Ruta de archivo predeterminado
    DEFAULT_TRADES_PATH = os.path.join(DATA_FOLDER, 'trades.csv')
    
    # Ruta de caché
    DATA_CACHE_PATH = os.path.join(DATA_FOLDER, 'processed_cache.pkl')
    
    # Configuración de addons
    ADDONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'addons')
    ADDONS_DIR = ADDONS_FOLDER  # Para compatibilidad
    ENABLE_ADDONS = True
    
    
    CACHE_ENABLED =  True

class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuración para entorno de producción"""
    DEBUG = False
    TESTING = False
    
# Mapeo de configuraciones
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

# Configuración por defecto
default_config = 'development'

def get_config(env=None):
    """Obtiene la configuración según el entorno"""
    env = env or default_config
    return config_by_name[env]