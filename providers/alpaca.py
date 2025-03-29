"""
Provider: Alpaca Markets
Descripción: Integración con la API de Alpaca Markets para datos y trading
"""
import json
import pandas as pd
from datetime import datetime, timedelta
import time

# Intentar importar el paquete de Alpaca - si no está disponible, mostrar mensaje claro
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

class AlpacaProvider:
    """Proveedor para la API de Alpaca Markets"""
    
    def __init__(self, api_key=None, api_secret=None, base_url=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url or 'https://paper-api.alpaca.markets/v2'
        self.api = None
        self.connected = False
        
        # Inicializar API si tenemos credenciales
        if api_key and api_secret:
            self.initialize({
                'api_key': api_key,
                'api_secret': api_secret,
                'base_url': self.base_url
            })
    
    def initialize(self, config):
        """Inicializa la conexión a Alpaca con la configuración dada"""
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.base_url = config.get('base_url', 'https://paper-api.alpaca.markets/v2')
        
        if not self.api_key or not self.api_secret:
            self.connected = False
            return False
        
        try:
            # Extraer solo la parte base de la URL (sin /v2)
            base_url_parts = self.base_url.split('/v2')
            api_base_url = base_url_parts[0]
            
            # Crear la instancia de la API
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url=api_base_url,
                api_version='v2'
            )
            
            # Verificar conexión con una llamada simple
            self.api.get_account()
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            print(f"Error al conectar con Alpaca: {e}")
            return False
    
    def test_connection(self):
        """Prueba la conexión a Alpaca y devuelve información de la cuenta"""
        if not self.api:
            return {
                'success': False,
                'message': 'API no inicializada. Configure sus credenciales.'
            }
        
        try:
            account = self.api.get_account()
            return {
                'success': True,
                'account_number': account.account_number,
                'status': account.status,
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'is_pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked,
                'created_at': account.created_at
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def debug_connection(self):
        """Prueba detallada de la conexión para depurar problemas"""
        debug_info = {
            'api_key_first_4': self.api_key[:4] + '...' if self.api_key else None,
            'api_secret_length': len(self.api_secret) if self.api_secret else 0,
            'base_url': self.base_url,
            'api_initialized': self.api is not None,
            'connected': self.connected
        }
        
        print("Información de depuración:")
        print(f"API Key (primeros 4 caracteres): {debug_info['api_key_first_4']}")
        print(f"API Secret (longitud): {debug_info['api_secret_length']}")
        print(f"Base URL: {debug_info['base_url']}")
        print(f"API inicializada: {debug_info['api_initialized']}")
        print(f"Conectado: {debug_info['connected']}")
        
        try:
            # Intentar una consulta simple
            print("\nIntentando obtener cuenta...")
            account = self.api.get_account()
            print("Consulta de cuenta exitosa:")
            print(f"  ID de cuenta: {account.id}")
            print(f"  Estado: {account.status}")
            
            # Intentar obtener activos
            print("\nIntentando obtener activos...")
            assets = self.api.list_assets(status='active', limit=5)
            print(f"Obtenidos {len(assets)} activos. Ejemplos:")
            for i, asset in enumerate(assets[:3]):
                print(f"  {i+1}. {asset.symbol} - {asset.name}")
                
            return True
        except Exception as e:
            print(f"\nError durante la depuración: {e}")
            
            # Si hay un error, intentar hacer una petición solo HTTP para diagnosticar
            try:
                import requests
                print("\nIntentando petición HTTP directa...")
                headers = {
                    'APCA-API-KEY-ID': self.api_key,
                    'APCA-API-SECRET-KEY': self.api_secret
                }
                # Usar la URL correcta para la petición
                url = f"{self.base_url}/account"
                print(f"URL de petición: {url}")
                response = requests.get(url, headers=headers)
                print(f"Código de respuesta: {response.status_code}")
                print(f"Respuesta: {response.text[:200]}...")
            except Exception as req_error:
                print(f"Error en petición HTTP directa: {req_error}")
                
            return False
    
    def get_account(self):
        """Obtiene información de la cuenta"""
        if not self.api:
            return None
        
        try:
            return self.api.get_account()
        except Exception as e:
            print(f"Error al obtener información de cuenta: {e}")
            return None
    
    def get_positions(self):
        """Obtiene las posiciones actuales"""
        if not self.api:
            return []
        
        try:
            positions = self.api.list_positions()
            return positions
        except Exception as e:
            print(f"Error al obtener posiciones: {e}")
            return []
    
    def get_orders(self, status='all', limit=50):
        """Obtiene las órdenes recientes"""
        if not self.api:
            return []
        
        try:
            orders = self.api.list_orders(status=status, limit=limit)
            return orders
        except Exception as e:
            print(f"Error al obtener órdenes: {e}")
            return []
    
    def submit_order(self, symbol, qty, side, type='market', time_in_force='day'):
        """Envía una orden de compra/venta"""
        if not self.api:
            return None
        
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force
            )
            return order
        except Exception as e:
            print(f"Error al enviar orden: {e}")
            return None
    
    def get_bars(self, symbols, timeframe='1D', start=None, end=None, limit=1000):
        """Obtiene datos de barras para los símbolos especificados"""
        if not self.api:
            return {}
        
        if not start:
            start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if not end:
            end = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Convertir a lista si es un solo símbolo
            if isinstance(symbols, str):
                symbols = [symbols]
            
            bars = {}
            for symbol in symbols:
                try:
                    # En la v3, utilizamos get_bars en lugar de get_barset
                    symbol_bars = self.api.get_bars(
                        symbol,
                        timeframe,
                        start=start,
                        end=end,
                        limit=limit
                    )
                    # Convertir a DataFrame para facilitar el procesamiento
                    if symbol_bars and len(symbol_bars) > 0:
                        df = pd.DataFrame([
                            {
                                'timestamp': bar.t,
                                'open': bar.o,
                                'high': bar.h,
                                'low': bar.l,
                                'close': bar.c,
                                'volume': bar.v
                            }
                            for bar in symbol_bars
                        ])
                        bars[symbol] = df
                except Exception as e:
                    print(f"Error al obtener barras para {symbol}: {e}")
            
            return bars
        except Exception as e:
            print(f"Error al obtener barras: {e}")
            return {}
    
    def get_asset(self, symbol):
        """Obtiene información sobre un activo específico"""
        if not self.api:
            return None
        
        try:
            return self.api.get_asset(symbol)
        except Exception as e:
            print(f"Error al obtener activo {symbol}: {e}")
            return None
    
    def get_assets(self, status='active', asset_class=None):
        """Obtiene lista de activos disponibles"""
        if not self.api:
            return []
        
        try:
            return self.api.list_assets(status=status, asset_class=asset_class)
        except Exception as e:
            print(f"Error al obtener activos: {e}")
            return []

# Información del provider para el registro
provider_info = {
    'name': 'alpaca',
    'display_name': 'Alpaca Markets',
    'description': 'Integración con la API de Alpaca Markets para datos de mercado y operaciones',
    'icon': 'chart-line',
    'available': ALPACA_AVAILABLE,
    'config_fields': [
        {
            'name': 'api_key',
            'display_name': 'API Key',
            'type': 'text',
            'required': True,
            'description': 'Clave de API de Alpaca Markets'
        },
        {
            'name': 'api_secret',
            'display_name': 'API Secret',
            'type': 'password',
            'required': True,
            'description': 'Clave secreta de API de Alpaca Markets'
        },
        {
            'name': 'base_url',
            'display_name': 'Entorno',
            'type': 'select',
            'options': [
                {'value': 'https://paper-api.alpaca.markets/v2', 'label': 'Paper Trading (Simulación)'},
                {'value': 'https://api.alpaca.markets/v2', 'label': 'Live Trading (Operaciones Reales)'}
            ],
            'default': 'https://paper-api.alpaca.markets/v2',
            'description': 'Entorno de operación. Recomendamos comenzar con Paper Trading.'
        }
    ]
}