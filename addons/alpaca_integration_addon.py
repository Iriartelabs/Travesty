"""
Addon: Alpaca Market Data Integration
Descripción: Integración con la API de Alpaca para datos de mercado en tiempo real
"""

# Crear un blueprint para las rutas de este addon
alpaca_bp = Blueprint('alpaca', __name__)
from addon_system import AddonRegistry
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
import json
import threading
import time
import logging
import os
from datetime import datetime, timedelta

# Importar servicios necesarios
from config import Config
from app import processed_data  # Para acceder a los datos procesados

# Intentar importar el módulo de Alpaca
try:
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.stream import Stream
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("Biblioteca Alpaca Trade API no disponible. Ejecuta 'pip install alpaca-trade-api' para instalarla")

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instancia global para compartir entre distintas partes de la aplicación
_alpaca_integration = None

def get_alpaca_integration():
    """Obtiene la instancia global de integración con Alpaca"""
    global _alpaca_integration
    if _alpaca_integration is None:
        _alpaca_integration = AlpacaMarketIntegration()
    return _alpaca_integration

# Clase principal para el addon
class AlpacaMarketIntegration:
    """
    Clase para manejar la integración con Alpaca Markets
    """
    def __init__(self):
        self.api_key = None
        self.api_secret = None
        self.base_url = None
        self.is_paper = True
        self.data_provider = None
        self.alert_checker = None
        self.streaming_active = False
        self.active_symbols = set()
        
        # Cargar configuración desde archivo si existe
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración de Alpaca desde un archivo"""
        config_path = os.path.join(Config.DATA_FOLDER, 'alpaca_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key')
                    self.api_secret = config.get('api_secret')
                    self.base_url = config.get('base_url')
                    self.is_paper = config.get('is_paper', True)
                logger.info("Configuración de Alpaca cargada correctamente")
            except Exception as e:
                logger.error(f"Error cargando configuración de Alpaca: {e}")
    
    def save_config(self, api_key, api_secret, is_paper=True):
        """
        Guarda la configuración de Alpaca
        
        Args:
            api_key (str): API Key de Alpaca
            api_secret (str): API Secret de Alpaca
            is_paper (bool, optional): True para paper trading, False para trading real
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Actualizar atributos
            self.api_key = api_key
            self.api_secret = api_secret
            self.is_paper = is_paper
            
            # Configurar URL base según modo
            self.base_url = 'https://paper-api.alpaca.markets' if is_paper else 'https://api.alpaca.markets'
            
            # Guardar en archivo
            config_path = os.path.join(Config.DATA_FOLDER, 'alpaca_config.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump({
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'base_url': self.base_url,
                    'is_paper': is_paper
                }, f)
            
            logger.info("Configuración de Alpaca guardada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error guardando configuración de Alpaca: {e}")
            return False
    
    def initialize_provider(self):
        """Inicializa el proveedor de datos de Alpaca"""
        if not ALPACA_AVAILABLE:
            logger.error("No se pudo inicializar el proveedor de datos de Alpaca: Biblioteca no disponible")
            return False
        
        if not self.api_key or not self.api_secret:
            logger.error("No se pudo inicializar el proveedor de datos de Alpaca: Credenciales no configuradas")
            return False
        
        try:
            # Importar la clase desde el módulo apropiado
            from alpaca_integration import AlpacaDataProvider
            
            # Crear instancia del proveedor de datos
            self.data_provider = AlpacaDataProvider(
                api_key=self.api_key,
                api_secret=self.api_secret,
                base_url=self.base_url,
                is_paper=self.is_paper
            )
            
            logger.info("Proveedor de datos de Alpaca inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error inicializando proveedor de datos de Alpaca: {e}")
            return False
    
    def test_connection(self):
        """
        Prueba la conexión con Alpaca
        
        Returns:
            dict: Información de la cuenta o error
        """
        if not self.data_provider:
            if not self.initialize_provider():
                return {'success': False, 'error': 'No se pudo inicializar el proveedor de datos'}
        
        try:
            # Intentar obtener información de la cuenta
            account_info = self.data_provider.get_account_info()
            
            if account_info:
                return {
                    'success': True,
                    'account': account_info,
                    'message': 'Conexión exitosa con Alpaca'
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo obtener información de la cuenta'
                }
        except Exception as e:
            logger.error(f"Error probando conexión con Alpaca: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_market_data(self, symbol, timeframe='1D', limit=20):
        """
        Obtiene datos de mercado para un símbolo
        
        Args:
            symbol (str): Símbolo a consultar
            timeframe (str, optional): Intervalo de tiempo
            limit (int, optional): Número de barras a obtener
        
        Returns:
            dict: Datos de mercado o error
        """
        if not self.data_provider:
            if not self.initialize_provider():
                return {'success': False, 'error': 'No se pudo inicializar el proveedor de datos'}
        
        try:
            # Obtener información actual
            current_price = self.data_provider.get_current_price(symbol)
            
            # Obtener barras históricas
            bars = self.data_provider.get_bars(symbol, timeframe, limit)
            
            # Obtener indicadores
            indicators = self.data_provider.calculate_indicators(symbol)
            
            return {
                'success': True,
                'symbol': symbol,
                'current_price': current_price,
                'bars': bars,
                'indicators': indicators
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado para {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_streaming(self, symbols):
        """
        Inicia el streaming de datos para los símbolos especificados
        
        Args:
            symbols (list): Lista de símbolos a monitorear
        
        Returns:
            bool: True si se inició correctamente, False en caso contrario
        """
        if not self.data_provider:
            if not self.initialize_provider():
                return False
        
        try:
            # Añadir símbolos a la lista de activos
            self.active_symbols.update(symbols)
            
            # Iniciar streaming
            self.data_provider.start_streaming(list(self.active_symbols))
            self.streaming_active = True
            
            logger.info(f"Streaming iniciado para símbolos: {list(self.active_symbols)}")
            return True
        except Exception as e:
            logger.error(f"Error iniciando streaming: {e}")
            return False
    
    def stop_streaming(self):
        """
        Detiene el streaming de datos
        
        Returns:
            bool: True si se detuvo correctamente, False en caso contrario
        """
        if not self.data_provider or not self.streaming_active:
            return False
        
        try:
            self.data_provider.stop_streaming()
            self.streaming_active = False
            logger.info("Streaming detenido")
            return True
        except Exception as e:
            logger.error(f"Error deteniendo streaming: {e}")
            return False
    
    def register_alert_for_symbol(self, alert_id, symbol, conditions, callback):
        """
        Registra una alerta para un símbolo específico
        
        Args:
            alert_id (str): ID único de la alerta
            symbol (str): Símbolo a monitorear
            conditions (dict): Condiciones de la alerta
            callback (callable): Función a llamar cuando se active la alerta
        
        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        if not self.data_provider:
            if not self.initialize_provider():
                return False
        
        try:
            # Asegurarse de que el símbolo está en las condiciones
            full_conditions = conditions.copy()
            full_conditions['symbol'] = symbol
            
            # Registrar la alerta
            self.data_provider.register_alert(alert_id, full_conditions, callback)
            
            # Asegurarse de que el streaming está activo para este símbolo
            if symbol not in self.active_symbols:
                self.start_streaming([symbol])
            
            logger.info(f"Alerta {alert_id} registrada para símbolo {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error registrando alerta: {e}")
            return False
    
    def unregister_alert(self, alert_id):
        """
        Elimina una alerta del sistema
        
        Args:
            alert_id (str): ID de la alerta a eliminar
        
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        if not self.data_provider:
            return False
        
        try:
            self.data_provider.unregister_alert(alert_id)
            logger.info(f"Alerta {alert_id} eliminada")
            return True
        except Exception as e:
            logger.error(f"Error eliminando alerta: {e}")
            return False

# Definición de rutas para el addon

@alpaca_bp.route('/alpaca')
def alpaca_dashboard():
    """Vista principal del dashboard de Alpaca"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Verificar si hay credenciales configuradas
    has_credentials = alpaca.api_key is not None and alpaca.api_secret is not None
    
    # Información de conexión
    connection_info = None
    if has_credentials:
        connection_info = alpaca.test_connection()
    
    # Obtener símbolos disponibles (desde datos procesados)
    available_symbols = set()
    if processed_data and 'processed_orders' in processed_data:
        for order in processed_data['processed_orders']:
            if 'symb' in order and order['symb']:
                available_symbols.add(order['symb'])
    
    # Renderizar plantilla
    return render_template(
        'alpaca_dashboard.html',
        has_credentials=has_credentials,
        is_paper=alpaca.is_paper if has_credentials else True,
        connection_info=connection_info,
        available_symbols=sorted(list(available_symbols)),
        streaming_active=alpaca.streaming_active,
        active_symbols=sorted(list(alpaca.active_symbols)),
        alpaca_available=ALPACA_AVAILABLE
    )

@alpaca_bp.route('/alpaca/settings', methods=['GET', 'POST'])
def alpaca_settings():
    """Vista para configurar credenciales de Alpaca"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Procesar formulario si es POST
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        is_paper = request.form.get('is_paper', 'true') == 'true'
        
        # Validar datos
        if not api_key or not api_secret:
            flash('API Key y API Secret son obligatorios', 'error')
            return redirect(url_for('alpaca.alpaca_settings'))
        
        # Guardar configuración
        success = alpaca.save_config(api_key, api_secret, is_paper)
        
        if success:
            flash('Configuración de Alpaca guardada correctamente', 'success')
            return redirect(url_for('alpaca.alpaca_dashboard'))
        else:
            flash('Error al guardar la configuración de Alpaca', 'error')
    
    # Renderizar plantilla con valores actuales
    return render_template(
        'alpaca_settings.html',
        api_key=alpaca.api_key,
        api_secret=alpaca.api_secret,
        is_paper=alpaca.is_paper
    )

@alpaca_bp.route('/alpaca/symbol/<symbol>')
def alpaca_symbol_data(symbol):
    """Vista para mostrar datos de un símbolo específico"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Verificar si hay credenciales configuradas
    if not alpaca.api_key or not alpaca.api_secret:
        flash('Debes configurar las credenciales de Alpaca primero', 'error')
        return redirect(url_for('alpaca.alpaca_settings'))
    
    # Obtener datos del símbolo
    market_data = alpaca.get_market_data(symbol)
    
    # Renderizar plantilla
    return render_template(
        'alpaca_symbol.html',
        symbol=symbol,
        market_data=market_data
    )

@alpaca_bp.route('/alpaca/streaming/start', methods=['POST'])
def start_streaming():
    """Endpoint para iniciar streaming de datos"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Verificar si hay credenciales configuradas
    if not alpaca.api_key or not alpaca.api_secret:
        return jsonify({'success': False, 'error': 'Credenciales no configuradas'})
    
    # Obtener símbolos del formulario
    data = request.json
    symbols = data.get('symbols', [])
    
    if not symbols:
        return jsonify({'success': False, 'error': 'No se especificaron símbolos'})
    
    # Iniciar streaming
    success = alpaca.start_streaming(symbols)
    
    return jsonify({
        'success': success,
        'active_symbols': list(alpaca.active_symbols) if success else []
    })

@alpaca_bp.route('/alpaca/streaming/stop', methods=['POST'])
def stop_streaming():
    """Endpoint para detener streaming de datos"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Detener streaming
    success = alpaca.stop_streaming()
    
    return jsonify({'success': success})

@alpaca_bp.route('/alpaca/test-connection', methods=['POST'])
def test_alpaca_connection():
    """Endpoint para probar la conexión con Alpaca"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Probar conexión
    result = alpaca.test_connection()
    
    return jsonify(result)

@alpaca_bp.route('/alpaca/market-data/<symbol>', methods=['GET'])
def get_market_data(symbol):
    """Endpoint para obtener datos de mercado de un símbolo"""
    # Obtener la instancia de integración
    alpaca = get_alpaca_integration()
    
    # Obtener parámetros adicionales
    timeframe = request.args.get('timeframe', '1D')
    limit = int(request.args.get('limit', 20))
    
    # Obtener datos
    result = alpaca.get_market_data(symbol, timeframe, limit)
    
    return jsonify(result)

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('alpaca_integration', {
        'name': 'Alpaca Integration',
        'description': 'Integración con la API de Alpaca para datos de mercado en tiempo real',
        'route': '/alpaca',
        'view_func': alpaca_dashboard,
        'template': 'alpaca_dashboard.html',
        'icon': 'chart-line',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    # Inicializar la instancia de integración
    get_alpaca_integration()
    # Registrar el addon
    register_addon()