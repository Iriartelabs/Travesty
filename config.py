import os

class Config:
    """Configuración base de la aplicación"""
    # Configuraciones generales
    SECRET_KEY = os.environ.get('SECRET_KEY', 'das_trader_analyzer_secret_key')
    
    # Rutas y directorios
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    
    # Límites de carga
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Rutas de archivos predeterminados
    DEFAULT_ORDERS_PATH = os.path.join(DATA_FOLDER, 'Orders.csv')
    DEFAULT_TRADES_PATH = os.path.join(DATA_FOLDER, 'Trades.csv')
    DEFAULT_TICKETS_PATH = os.path.join(DATA_FOLDER, 'Tickets.csv')
    
    # Ruta de caché
    DATA_CACHE_PATH = os.path.join(DATA_FOLDER, 'processed_cache.pkl')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

def get_config(environment='development'):
    """Obtiene la configuración según el entorno"""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig
    }
    return configs.get(environment, DevelopmentConfig)()
