import os

class Config:
    """Configuración base para la aplicación"""
    # Ruta de carpetas
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Límite de 16MB para subidas
    
    # Clave secreta (para sesiones, CSRF, etc.)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'das_trader_analyzer_secret_key'
    
    # Configuración de base de datos
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or 3306
    DB_NAME = os.environ.get('DB_NAME') or 'das_trader_analyzer'
    DB_USER = os.environ.get('DB_USER') or 'das_app_user'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'secure_password_here'
    
    # Configuración de almacenamiento
    CACHE_TYPE = 'simple'  # Para Flask-Caching

class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo"""
    DEBUG = True
    
class TestingConfig(Config):
    """Configuración para entorno de pruebas"""
    TESTING = True
    DB_NAME = 'das_trader_analyzer_test'
    
class ProductionConfig(Config):
    """Configuración para entorno de producción"""
    DEBUG = False
    
    # Clave secreta más segura en producción
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Usar conexión SSL para base de datos en producción
    DB_SSL = True
    
    # Limitar intentos de login
    LOGIN_ATTEMPTS = 5
    
    # Cache más avanzado
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')

# Configuración por defecto según el entorno
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    
    'default': DevelopmentConfig
}

def get_config():
    """Obtiene la configuración según el entorno definido en variables de entorno"""
    env = os.environ.get('FLASK_ENV') or 'default'
    return config.get(env, config['default'])
