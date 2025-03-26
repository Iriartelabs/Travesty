"""
Módulo de integración con Alpaca para el sistema de alertas de trading.
Este módulo se encarga de conectar con la API de Alpaca, obtener datos de mercado
y verificar las condiciones de las alertas configuradas.
"""

import time
import threading
import logging
from datetime import datetime, timedelta
import json
import os

# Importar la biblioteca oficial de Alpaca
import alpaca_trade_api as tradeapi
from alpaca_trade_api.stream import Stream

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('alpaca_integration')

class AlpacaDataProvider:
    """
    Proveedor de datos de mercado utilizando la API de Alpaca.
    """
    def __init__(self, api_key=None, api_secret=None, base_url=None, is_paper=True):
        """
        Inicializa la conexión con Alpaca.
        
        Args:
            api_key (str, optional): API Key de Alpaca. Si es None, se busca en variables de entorno.
            api_secret (str, optional): API Secret de Alpaca. Si es None, se busca en variables de entorno.
            base_url (str, optional): URL base de la API. Si es None, se usa la URL de paper trading.
            is_paper (bool, optional): True para usar paper trading, False para trading real.
        """
        # Usar valores proporcionados o buscar en variables de entorno
        self.api_key = api_key or os.environ.get('ALPACA_API_KEY')
        self.api_secret = api_secret or os.environ.get('ALPACA_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API Key y API Secret son requeridos. Proporciónalos como parámetros o configura variables de entorno.")
        
        # Configurar URL base según modo paper o live
        if not base_url:
            self.base_url = 'https://paper-api.alpaca.markets' if is_paper else 'https://api.alpaca.markets'
        else:
            self.base_url = base_url
        
        # Inicializar cliente de API REST
        self.api = tradeapi.REST(
            self.api_key,
            self.api_secret,
            self.base_url,
            api_version='v2'
        )
        
        # Inicializar cliente de streaming para datos en tiempo real
        self.stream = Stream(
            self.api_key,
            self.api_secret,
            base_url=self.base_url,
            data_feed='iex'  # o 'sip' para datos de nivel 1 con suscripción
        )
        
        # Almacén de datos en memoria para últimos precios
        self.latest_prices = {}
        
        # Diccionario para almacenar callbacks de alertas
        self.alert_callbacks = {}
        
        # Flag para controlar el proceso en segundo plano
        self.running = False
        
        logger.info(f"AlpacaDataProvider inicializado. Modo: {'Paper' if is_paper else 'Live'}")
    
    def get_account_info(self):
        """
        Obtiene información de la cuenta.
        
        Returns:
            dict: Información de la cuenta.
        """
        try:
            account = self.api.get_account()
            return {
                'id': account.id,
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'status': account.status
            }
        except Exception as e:
            logger.error(f"Error obteniendo información de la cuenta: {e}")
            return None
    
    def get_current_price(self, symbol):
        """
        Obtiene el precio actual de un símbolo.
        
        Args:
            symbol (str): Símbolo del activo.
            
        Returns:
            float: Precio actual del símbolo o None si hay error.
        """
        try:
            # Verificar si tenemos el precio en cache
            if symbol in self.latest_prices and (datetime.now() - self.latest_prices[symbol]['timestamp']).seconds < 60:
                return self.latest_prices[symbol]['price']
            
            # Obtener último precio
            last_trade = self.api.get_latest_trade(symbol)
            price = float(last_trade.price)
            
            # Almacenar en cache
            self.latest_prices[symbol] = {
                'price': price,
                'timestamp': datetime.now()
            }
            
            return price
        except Exception as e:
            logger.error(f"Error obteniendo precio actual para {symbol}: {e}")
            return None
    
    def get_bars(self, symbol, timeframe='1D', limit=100):
        """
        Obtiene barras históricas para un símbolo.
        
        Args:
            symbol (str): Símbolo del activo.
            timeframe (str, optional): Intervalo de tiempo ('1Min', '5Min', '15Min', '1H', '1D'). Default: '1D'.
            limit (int, optional): Número máximo de barras a obtener. Default: 100.
            
        Returns:
            list: Lista de barras (dict) con datos OHLC.
        """
        try:
            bars = self.api.get_bars(symbol, timeframe, limit=limit).df
            
            # Convertir DataFrame a lista de diccionarios
            bars_list = []
            for index, row in bars.iterrows():
                bars_list.append({
                    'timestamp': index.isoformat(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })
            
            return bars_list
        except Exception as e:
            logger.error(f"Error obteniendo barras para {symbol}: {e}")
            return []
    
    def calculate_indicators(self, symbol):
        """
        Calcula indicadores técnicos comunes para un símbolo.
        
        Args:
            symbol (str): Símbolo del activo.
            
        Returns:
            dict: Diccionario con indicadores calculados.
        """
        try:
            # Obtener barras para cálculos
            bars = self.get_bars(symbol, timeframe='1D', limit=50)
            if not bars:
                return {}
            
            # Extraer precios de cierre
            closes = [bar['close'] for bar in bars]
            
            # Calcular SMA 20
            sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
            
            # Calcular RSI-14 (simplificado)
            if len(closes) >= 15:
                # Calcular cambios
                changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                # Separar ganancias y pérdidas
                gains = [c if c > 0 else 0 for c in changes]
                losses = [abs(c) if c < 0 else 0 for c in changes]
                
                # Usar los últimos 14 valores
                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14
                
                if avg_loss == 0:
                    rsi14 = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi14 = 100 - (100 / (1 + rs))
            else:
                rsi14 = None
            
            # Calcular ATR-14 (simplificado)
            if len(bars) >= 15:
                true_ranges = []
                for i in range(1, len(bars)):
                    high = bars[i]['high']
                    low = bars[i]['low']
                    prev_close = bars[i-1]['close']
                    
                    tr1 = high - low
                    tr2 = abs(high - prev_close)
                    tr3 = abs(low - prev_close)
                    
                    true_range = max(tr1, tr2, tr3)
                    true_ranges.append(true_range)
                
                atr14 = sum(true_ranges[-14:]) / 14
            else:
                atr14 = None
            
            # Retornar indicadores calculados
            return {
                'sma20': sma20,
                'rsi14': rsi14,
                'atr14': atr14,
                'price': closes[-1] if closes else None,
                'prev_close': closes[-2] if len(closes) > 1 else None,
                'daily_change_pct': ((closes[-1] / closes[-2]) - 1) * 100 if len(closes) > 1 else None
            }
        except Exception as e:
            logger.error(f"Error calculando indicadores para {symbol}: {e}")
            return {}
    
    def register_alert(self, alert_id, alert_conditions, callback):
        """
        Registra una alerta para monitoreo.
        
        Args:
            alert_id (str): Identificador único de la alerta.
            alert_conditions (dict): Condiciones de la alerta.
            callback (callable): Función a llamar cuando se cumplan las condiciones.
        """
        self.alert_callbacks[alert_id] = {
            'conditions': alert_conditions,
            'callback': callback,
            'last_triggered': None
        }
        logger.info(f"Alerta {alert_id} registrada para monitoreo")
    
    def unregister_alert(self, alert_id):
        """
        Elimina una alerta del monitoreo.
        
        Args:
            alert_id (str): Identificador único de la alerta.
        """
        if alert_id in self.alert_callbacks:
            del self.alert_callbacks[alert_id]
            logger.info(f"Alerta {alert_id} eliminada del monitoreo")
    
    def _handle_trade_update(self, trade):
        """
        Manejador para actualizaciones de trading.
        
        Args:
            trade: Datos de la actualización de trading.
        """
        logger.info(f"Actualización de trading recibida: {trade}")
        # Aquí podrías actualizar el estado de órdenes en ejecución
    
    def _handle_quote_update(self, quote):
        """
        Manejador para actualizaciones de cotizaciones.
        
        Args:
            quote: Datos de la cotización.
        """
        symbol = quote.symbol
        bid_price = float(quote.bid_price)
        ask_price = float(quote.ask_price)
        
        # Actualizar precio en cache
        self.latest_prices[symbol] = {
            'price': (bid_price + ask_price) / 2,  # Precio medio
            'bid': bid_price,
            'ask': ask_price,
            'timestamp': datetime.now()
        }
        
        # Verificar alertas para este símbolo
        self._check_alerts(symbol)
    
    def _handle_minute_bar(self, bar):
        """
        Manejador para barras de un minuto.
        
        Args:
            bar: Datos de la barra.
        """
        symbol = bar.symbol
        
        # Actualizar precio en cache
        self.latest_prices[symbol] = {
            'price': float(bar.close),
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': int(bar.volume),
            'timestamp': datetime.now()
        }
        
        # Verificar alertas para este símbolo
        self._check_alerts(symbol)
    
    def _check_alerts(self, symbol):
        """
        Verifica las alertas registradas para un símbolo específico.
        
        Args:
            symbol (str): Símbolo a verificar.
        """
        for alert_id, alert_info in self.alert_callbacks.items():
            conditions = alert_info['conditions']
            
            # Verificar si la alerta aplica para este símbolo
            if 'symbol' in conditions and conditions['symbol'] != symbol:
                continue
            
            # Evitar disparar la misma alerta demasiado seguido
            if alert_info['last_triggered'] and (datetime.now() - alert_info['last_triggered']).seconds < 300:
                continue
            
            # Obtener precio actual e indicadores
            current_price = self.get_current_price(symbol)
            indicators = self.calculate_indicators(symbol)
            
            # Variables para la evaluación de condiciones
            alert_triggered = False
            
            # Verificar condiciones de precio
            if 'price_above' in conditions and current_price > conditions['price_above']:
                alert_triggered = True
            
            if 'price_below' in conditions and current_price < conditions['price_below']:
                alert_triggered = True
                
            # Verificar condiciones de RSI
            if 'rsi_above' in conditions and indicators.get('rsi14') and indicators['rsi14'] > conditions['rsi_above']:
                alert_triggered = True
                
            if 'rsi_below' in conditions and indicators.get('rsi14') and indicators['rsi14'] < conditions['rsi_below']:
                alert_triggered = True
            
            # Verificar cruce de SMA
            if 'price_crosses_sma20' in conditions and indicators.get('sma20') and indicators.get('prev_close'):
                if (indicators['prev_close'] < indicators['sma20'] and current_price > indicators['sma20']) or \
                   (indicators['prev_close'] > indicators['sma20'] and current_price < indicators['sma20']):
                    alert_triggered = True
            
            # Verificar cambio porcentual diario
            if 'daily_change_pct_above' in conditions and indicators.get('daily_change_pct') and \
               indicators['daily_change_pct'] > conditions['daily_change_pct_above']:
                alert_triggered = True
                
            # Si se cumplieron las condiciones, llamar al callback
            if alert_triggered:
                logger.info(f"¡Alerta {alert_id} activada para {symbol}!")
                
                # Actualizar timestamp del último disparo
                self.alert_callbacks[alert_id]['last_triggered'] = datetime.now()
                
                # Preparar datos para el callback
                alert_data = {
                    'alert_id': alert_id,
                    'symbol': symbol,
                    'price': current_price,
                    'indicators': indicators,
                    'timestamp': datetime.now().isoformat(),
                    'conditions_met': conditions
                }
                
                # Llamar al callback
                try:
                    alert_info['callback'](alert_data)
                except Exception as e:
                    logger.error(f"Error en callback de alerta {alert_id}: {e}")
    
    def start_streaming(self, symbols=None):
        """
        Inicia el streaming de datos.
        
        Args:
            symbols (list, optional): Lista de símbolos para suscribirse. Si es None,
                                      se obtienen de las alertas registradas.
        """
        if self.running:
            logger.warning("El streaming ya está en ejecución")
            return
        
        # Si no se proporcionan símbolos, extraerlos de las alertas
        if symbols is None:
            symbols = set()
            for alert_info in self.alert_callbacks.values():
                if 'symbol' in alert_info['conditions']:
                    symbols.add(alert_info['conditions']['symbol'])
            symbols = list(symbols)
        
        if not symbols:
            logger.warning("No hay símbolos para monitorear")
            return
        
        # Configurar manejadores de eventos
        self.stream.subscribe_trades(self._handle_trade_update, *symbols)
        self.stream.subscribe_quotes(self._handle_quote_update, *symbols)
        self.stream.subscribe_bars(self._handle_minute_bar, *symbols)
        
        # Iniciar streaming en un hilo separado
        self.running = True
        threading.Thread(target=self._run_streaming, daemon=True).start()
        
        logger.info(f"Streaming iniciado para símbolos: {symbols}")
    
    def _run_streaming(self):
        """
        Ejecuta el bucle de streaming en un hilo separado.
        """
        try:
            self.stream.run()
        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            self.running = False
    
    def stop_streaming(self):
        """
        Detiene el streaming de datos.
        """
        if not self.running:
            logger.warning("El streaming no está en ejecución")
            return
        
        self.stream.stop()
        self.running = False
        logger.info("Streaming detenido")


class MarketAlertChecker:
    """
    Servicio para verificar alertas de mercado periódicamente.
    """
    def __init__(self, data_provider, alert_manager, check_interval=300):
        """
        Inicializa el verificador de alertas.
        
        Args:
            data_provider (AlpacaDataProvider): Proveedor de datos de mercado.
            alert_manager: Gestor de alertas del sistema.
            check_interval (int, optional): Intervalo de verificación en segundos. Default: 300 (5 min).
        """
        self.data_provider = data_provider
        self.alert_manager = alert_manager
        self.check_interval = check_interval
        self.running = False
        self.check_thread = None
        
        logger.info(f"MarketAlertChecker inicializado con intervalo de {check_interval} segundos")
    
    def start(self):
        """
        Inicia el servicio de verificación de alertas.
        """
        if self.running:
            logger.warning("El verificador de alertas ya está en ejecución")
            return
        
        self.running = True
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()
        
        logger.info("Servicio de verificación de alertas iniciado")
    
    def stop(self):
        """
        Detiene el servicio de verificación de alertas.
        """
        if not self.running:
            logger.warning("El verificador de alertas no está en ejecución")
            return
        
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=10)
        
        logger.info("Servicio de verificación de alertas detenido")
    
    def _check_loop(self):
        """
        Bucle principal para verificar alertas periódicamente.
        """
        while self.running:
            try:
                # Obtener todas las alertas activas
                active_alerts = self.alert_manager.get_active_alerts()
                
                for alert in active_alerts:
                    # Obtener datos según tipo de alerta
                    symbol = alert.get('symbol')
                    if not symbol:
                        continue
                    
                    # Registrar la alerta con el proveedor de datos
                    self.data_provider.register_alert(
                        alert['id'],
                        alert['conditions'],
                        lambda data: self._alert_triggered(data)
                    )
                
                # Asegurarse de que el streaming esté activo para estos símbolos
                symbols = list(set(alert.get('symbol') for alert in active_alerts if alert.get('symbol')))
                if symbols:
                    self.data_provider.start_streaming(symbols)
                
                # Esperar hasta el próximo ciclo
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error en ciclo de verificación: {e}")
                time.sleep(60)  # Esperar un minuto en caso de error
    
    def _alert_triggered(self, alert_data):
        """
        Callback cuando una alerta se activa.
        
        Args:
            alert_data (dict): Datos de la alerta activada.
        """
        # Notificar a través del gestor de alertas
        self.alert_manager.trigger_alert(
            alert_id=alert_data['alert_id'],
            alert_data=alert_data
        )


# Ejemplo de uso
if __name__ == "__main__":
    # Este código solo se ejecuta si el script se corre directamente
    
    # Crear una instancia del proveedor de datos
    data_provider = AlpacaDataProvider(
        api_key="TU_API_KEY",
        api_secret="TU_API_SECRET",
        is_paper=True
    )
    
    # Función de ejemplo para el callback de alertas
    def alert_callback(alert_data):
        print(f"¡ALERTA ACTIVADA! - {alert_data['symbol']} a ${alert_data['price']} - {alert_data['timestamp']}")
    
    # Registrar una alerta de ejemplo
    data_provider.register_alert(
        "mi_alerta_1",
        {
            "symbol": "AAPL",
            "price_above": 150.0
        },
        alert_callback
    )
    
    # Iniciar streaming para AAPL
    data_provider.start_streaming(["AAPL"])
    
    # Mantener el script en ejecución
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo el servicio...")
        data_provider.stop_streaming()
