from flask import Flask
import os
from config import get_config
from services.cache_manager import load_processed_data
from services.providers import TradingProviderRegistry

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
    
    # Crear directorios necesarios si no existen
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join('config', 'providers'), exist_ok=True)
    
    # Intentar cargar datos procesados
    processed_data = load_processed_data(config.DATA_CACHE_PATH)
    
    # Importar blueprints
    from routes.main import main_bp
    from routes.analysis import analysis_bp
    from routes.config import config_bp
    
    # Importar extensiones
    from extensions import init_extensions
    
    # Inicializar extensiones
    init_extensions(app)
    
    # Registrar blueprints principales
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(config_bp)
    
    # Cargar e inicializar provider de Alpaca
    _load_alpaca_provider()
    
    # Cargar y configurar addons
    from addon_system import load_addons_from_directory, AddonRegistry
    
    # Cargar addons primero
    load_addons_from_directory()
    
    # Inicializar sistema de addons
    AddonRegistry.initialize(app)
    
    # Registrar blueprint de Alpaca
    from routes.alpaca import alpaca_bp
    app.register_blueprint(alpaca_bp)
    
    return app

def _load_alpaca_provider():
    """Carga e inicializa el provider de Alpaca Markets"""
    try:
        # Intentar importar Alpaca
        import alpaca_trade_api as tradeapi
        
        # Importar la clase AlpacaProvider
        from providers.alpaca import AlpacaProvider, provider_info
        
        # Cargar configuración guardada
        config = TradingProviderRegistry.load_provider_config('alpaca')
        
        # Crear instancia del provider
        provider = AlpacaProvider(
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret'),
            base_url=config.get('base_url')
        )
        
        # Registrar el provider y su información
        TradingProviderRegistry.register_provider('alpaca', provider)
        TradingProviderRegistry.register_provider_info('alpaca', provider_info)
        
        print("Provider de Alpaca cargado correctamente")
    except ImportError:
        print("El paquete alpaca-trade-api no está instalado")
    except Exception as e:
        print(f"Error al cargar el provider de Alpaca: {e}")

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