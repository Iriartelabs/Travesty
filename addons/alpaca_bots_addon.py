"""
Addon: Alpaca Trading Bots
Descripción: Sistema de bots de trading automático para operar en Alpaca con DAS Trader Analyzer
"""
from addon_system import AddonRegistry
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
import json
import pandas as pd
import numpy as np
import time
import threading
import uuid
from datetime import datetime, timedelta
import requests

# Control de registro único
_is_registered = False

# Función para obtener credenciales de Alpaca
def get_alpaca_credentials():
    """Obtiene credenciales de Alpaca desde el archivo del sistema"""
    try:
        with open('data/alpaca_credentials.json', 'r') as f:
            credentials = json.load(f)
            return credentials.get('api_key'), credentials.get('api_secret')
    except Exception as e:
        print(f"Error al leer credenciales: {str(e)}")
        return None, None

# Crear un blueprint para el addon
alpaca_bots_bp = Blueprint('alpaca_bots', __name__)

# Registro de bots activos
active_bots = {}

# Clase para representar un bot de trading
class TradingBot:
    def __init__(self, bot_id, name, strategy, symbols, api_key, api_secret, paper_trading=True, params=None):
        self.bot_id = bot_id
        self.name = name
        self.strategy = strategy
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper_trading = paper_trading
        self.params = params or {}
        self.status = "stopped"  # stopped, running, error
        self.error_message = ""
        self.created_at = datetime.now()
        self.last_run = None
        self.trades = []
        self.thread = None
        self.stop_event = threading.Event()
        
    def to_dict(self):
        """Convierte el bot a un diccionario para JSON"""
        return {
            "bot_id": self.bot_id,
            "name": self.name,
            "strategy": self.strategy,
            "symbols": self.symbols,
            "api_key": self.api_key[:5] + "***",  # Ocultar clave API por seguridad
            "paper_trading": self.paper_trading,
            "params": self.params,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "last_run": self.last_run.strftime("%Y-%m-%d %H:%M:%S") if self.last_run else None,
            "trades_count": len(self.trades)
        }
    
    def start(self):
        """Inicia el bot en un hilo separado"""
        if self.status == "running":
            return False
        
        self.stop_event.clear()
        self.status = "running"
        self.error_message = ""
        self.thread = threading.Thread(target=self._run_bot)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self):
        """Detiene el bot"""
        if self.status != "running":
            return False
        
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.status = "stopped"
        return True
    
    def _run_bot(self):
        """Función principal que ejecuta la estrategia del bot"""
        try:
            self.last_run = datetime.now()
            
            # Seleccionar la estrategia
            if self.strategy == "sma_crossover":
                strategy_func = self._sma_crossover_strategy
            elif self.strategy == "rsi_strategy":
                strategy_func = self._rsi_strategy
            elif self.strategy == "macd_strategy":
                strategy_func = self._macd_strategy
            else:
                raise ValueError(f"Estrategia desconocida: {self.strategy}")
            
            # Ejecutar la estrategia en un bucle
            while not self.stop_event.is_set():
                for symbol in self.symbols:
                    try:
                        # Obtener datos de mercado
                        market_data = self._get_market_data(symbol)
                        
                        # Ejecutar la estrategia
                        signal = strategy_func(market_data, symbol)
                        
                        # Procesar la señal (comprar, vender, mantener)
                        if signal:
                            self._process_signal(signal, symbol)
                    
                    except Exception as e:
                        error_msg = f"Error procesando símbolo {symbol}: {str(e)}"
                        print(error_msg)
                        # No detener el bot por un error en un símbolo
                
                # Esperar antes del siguiente ciclo
                time.sleep(self.params.get("check_interval", 60))
        
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            print(f"Error en bot {self.name}: {str(e)}")
    
    def _get_market_data(self, symbol):
        """Obtiene datos de mercado para un símbolo"""
        # Determinar el endpoint según sea paper trading o cuenta real
        base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"
        
        # Parámetros para obtener barras (velas)
        timeframe = self.params.get("timeframe", "1Day")
        limit = self.params.get("data_points", 100)
        
        # Hacer solicitud a la API de Alpaca
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
        endpoint = f"{base_url}/v2/stocks/{symbol}/bars"
        params = {
            "timeframe": timeframe,
            "limit": limit
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Error al obtener datos de Alpaca: {response.text}")
        
        # Procesar la respuesta
        data = response.json()
        
        # Convertir a DataFrame
        bars = data.get("bars", [])
        if not bars:
            raise Exception(f"No hay datos disponibles para {symbol}")
        
        # Crear DataFrame
        df = pd.DataFrame(bars)
        df['timestamp'] = pd.to_datetime(df['t'])
        df.set_index('timestamp', inplace=True)
        
        # Renombrar columnas
        df.rename(columns={
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }, inplace=True)
        
        return df
    
    def _process_signal(self, signal, symbol):
        """Procesa una señal de trading"""
        # Implementar lógica para enviar órdenes a Alpaca
        
        if signal['action'] in ['buy', 'sell']:
            # Determinar el endpoint según sea paper trading o cuenta real
            base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"
            
            # Preparar la orden
            order_data = {
                "symbol": symbol,
                "qty": signal.get('quantity', 1),
                "side": "buy" if signal['action'] == 'buy' else "sell",
                "type": "market",
                "time_in_force": "day"
            }
            
            # Enviar la orden
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "Content-Type": "application/json"
            }
            
            response = requests.post(f"{base_url}/v2/orders", headers=headers, json=order_data)
            
            if response.status_code == 200 or response.status_code == 201:
                order_response = response.json()
                
                # Registrar la operación
                trade = {
                    "symbol": symbol,
                    "action": signal['action'],
                    "quantity": signal.get('quantity', 1),
                    "price": signal.get('price', 0),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "order_id": order_response.get('id', ''),
                    "status": order_response.get('status', '')
                }
                
                self.trades.append(trade)
                print(f"Orden enviada: {trade}")
                return True
            else:
                error_msg = f"Error al enviar orden: {response.text}"
                print(error_msg)
                return False
    
    # Estrategias de trading
    def _sma_crossover_strategy(self, data, symbol):
        """Estrategia de cruce de medias móviles"""
        from addons.trading_alert_addon import TradingIndicators
        
        # Obtener parámetros
        short_period = self.params.get("short_period", 9)
        long_period = self.params.get("long_period", 21)
        
        # Calcular medias móviles
        data['sma_short'] = TradingIndicators.sma(data['close'], period=short_period)
        data['sma_long'] = TradingIndicators.sma(data['close'], period=long_period)
        
        # Verificar tamaño de datos
        if len(data) < long_period + 2:
            return None
        
        # Verificar cruce
        curr_short = data['sma_short'].iloc[-1]
        curr_long = data['sma_long'].iloc[-1]
        prev_short = data['sma_short'].iloc[-2]
        prev_long = data['sma_long'].iloc[-2]
        
        # Señal de compra: cruce de SMA corta por encima de SMA larga
        if prev_short <= prev_long and curr_short > curr_long:
            return {
                'action': 'buy',
                'symbol': symbol,
                'price': data['close'].iloc[-1],
                'quantity': self._calculate_position_size(symbol, data['close'].iloc[-1]),
                'reason': f"Cruce alcista de SMA{short_period} por encima de SMA{long_period}"
            }
        
        # Señal de venta: cruce de SMA corta por debajo de SMA larga
        elif prev_short >= prev_long and curr_short < curr_long:
            return {
                'action': 'sell',
                'symbol': symbol,
                'price': data['close'].iloc[-1],
                'quantity': self._calculate_position_size(symbol, data['close'].iloc[-1]),
                'reason': f"Cruce bajista de SMA{short_period} por debajo de SMA{long_period}"
            }
        
        return None
    
    def _rsi_strategy(self, data, symbol):
        """Estrategia basada en RSI"""
        from addons.trading_alert_addon import TradingIndicators
        
        # Obtener parámetros
        period = self.params.get("rsi_period", 14)
        overbought = self.params.get("overbought", 70)
        oversold = self.params.get("oversold", 30)
        
        # Calcular RSI
        data['rsi'] = TradingIndicators.rsi(data['close'], period=period)
        
        # Verificar tamaño de datos
        if len(data) < period + 2:
            return None
        
        curr_rsi = data['rsi'].iloc[-1]
        prev_rsi = data['rsi'].iloc[-2]
        
        # Señal de compra: RSI sale de la zona de sobreventa
        if prev_rsi <= oversold and curr_rsi > oversold:
            return {
                'action': 'buy',
                'symbol': symbol,
                'price': data['close'].iloc[-1],
                'quantity': self._calculate_position_size(symbol, data['close'].iloc[-1]),
                'reason': f"RSI salió de la zona de sobreventa (RSI: {curr_rsi:.2f})"
            }
        
        # Señal de venta: RSI entra en la zona de sobrecompra
        elif prev_rsi <= overbought and curr_rsi > overbought:
            return {
                'action': 'sell',
                'symbol': symbol,
                'price': data['close'].iloc[-1],
                'quantity': self._calculate_position_size(symbol, data['close'].iloc[-1]),
                'reason': f"RSI entró en la zona de sobrecompra (RSI: {curr_rsi:.2f})"
            }
        
        return None
    
    def _macd_strategy(self, data, symbol):
        """Estrategia basada en MACD"""
        from addons.trading_alert_addon import TradingIndicators
        
        # Obtener parámetros
        fast_period = self.params.get("fast_period", 12)
        slow_period = self.params.get("slow_period", 26)
        signal_period = self.params.get("signal_period", 9)
        
        # Calcular MACD
        macd_result = TradingIndicators.macd(data['close'], 
                                           fast_period=fast_period,
                                           slow_period=slow_period,
                                           signal_period=signal_period)
        
        data['macd'] = macd_result['macd_line']
        data['signal'] = macd_result['signal_line']
        data['histogram'] = macd_result['histogram']
        
        # Verificar tamaño de datos
        if len(data) < slow_period + signal_period + 2:
            return None
        
        # Verificar cruce de MACD y señal
        curr_macd = data['macd'].iloc[-1]
        curr_signal = data['signal'].iloc[-1]
        prev_macd = data['macd'].iloc[-2]
        prev_signal = data['signal'].iloc[-2]
        
        # Señal de compra: MACD cruza por encima de la línea de señal
        if prev_macd <= prev_signal and curr_macd > curr_signal:
            return {
                'action': 'buy',
                'symbol': symbol,
                'price': data['close'].iloc[-1],
                'quantity': self._calculate_position_size(symbol, data['close'].iloc[-1]),
                'reason': "MACD cruzó por encima de la línea de señal"
            }
        
        # Señal de venta: MACD cruza por debajo de la línea de señal
        elif prev_macd >= prev_signal and curr_macd < curr_signal:
            return {
                'action': 'sell',
                'symbol': symbol,
                'price': data['close'].iloc[-1],
                'quantity': self._calculate_position_size(symbol, data['close'].iloc[-1]),
                'reason': "MACD cruzó por debajo de la línea de señal"
            }
        
        return None
    
    def _calculate_position_size(self, symbol, price):
        """Calcula el tamaño óptimo de la posición"""
        # Obtener balance de la cuenta
        base_url = "https://paper-api.alpaca.markets" if self.paper_trading else "https://api.alpaca.markets"
        
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
        response = requests.get(f"{base_url}/v2/account", headers=headers)
        
        if response.status_code != 200:
            # Si hay error, usar un valor predeterminado
            print(f"Error al obtener balance: {response.text}")
            return 1
        
        account = response.json()
        cash = float(account.get('cash', 0))
        
        # Aplicar gestión de riesgo
        risk_percentage = self.params.get("risk_percentage", 2) / 100
        max_risk_amount = cash * risk_percentage
        
        # Calcular precio de stop loss (simplificado)
        # En una implementación real, esto dependería de la estrategia y volatilidad
        stop_loss_pct = self.params.get("stop_loss_pct", 1) / 100
        stop_price = price * (1 - stop_loss_pct)
        
        # Calcular riesgo por acción
        risk_per_share = price - stop_price
        
        # Calcular tamaño de posición
        if risk_per_share <= 0:
            return 1
        
        position_size = int(max_risk_amount / risk_per_share)
        
        # Aplicar límites
        min_position = self.params.get("min_position", 1)
        max_position = self.params.get("max_position", 100)
        
        position_size = max(min_position, min(position_size, max_position))
        
        return position_size

# Rutas del Blueprint - versión actualizada para soportar POST
@alpaca_bots_bp.route('/alpaca-bots', methods=['GET', 'POST'])
def trading_bots_main():
    """Vista principal del addon de bots de trading con múltiples acciones"""
    try:
        # Intentar obtener datos procesados de diferentes maneras
        try:
            from app import processed_data
        except ImportError:
            # Si no se puede importar directamente, intentar desde la caché
            from config import Config
            from services.cache_manager import load_processed_data
            processed_data = load_processed_data(Config.DATA_CACHE_PATH)
        
        # Valor predeterminado por si processed_data es None
        if processed_data is None:
            processed_data = {}
        
        # Si es un POST, manejar la creación del bot
        if request.method == 'POST':
            action = request.args.get('action', '')
            if action == 'create':
                # Obtener datos del formulario
                name = request.form.get('bot_name')
                strategy = request.form.get('strategy')
                symbols = request.form.get('symbols').split(',')
                symbols = [s.strip() for s in symbols if s.strip()]
                paper_trading = 'paper_trading' in request.form
                
                # Obtener credenciales de Alpaca
                api_key, api_secret = get_alpaca_credentials()
                if not api_key or not api_secret:
                    flash('No se encontraron credenciales de Alpaca. Configure sus credenciales en el módulo de Integración Alpaca.', 'error')
                    return redirect(url_for('addon_alpaca_bots_addon.trading_bots_main', action='create'))
                
                # Validar datos
                if not name or not strategy or not symbols:
                    flash('Todos los campos son obligatorios', 'error')
                    return redirect(url_for('addon_alpaca_bots_addon.trading_bots_main', action='create'))
                
                # Parámetros específicos de la estrategia
                params = {}
                
                # Parámetros comunes
                params['check_interval'] = int(request.form.get('check_interval', 60))
                params['risk_percentage'] = float(request.form.get('risk_percentage', 2))
                params['stop_loss_pct'] = float(request.form.get('stop_loss_pct', 1))
                params['min_position'] = int(request.form.get('min_position', 1))
                params['max_position'] = int(request.form.get('max_position', 100))
                
                # Parámetros específicos según la estrategia
                if strategy == 'sma_crossover':
                    params['short_period'] = int(request.form.get('short_period', 9))
                    params['long_period'] = int(request.form.get('long_period', 21))
                
                elif strategy == 'rsi_strategy':
                    params['rsi_period'] = int(request.form.get('rsi_period', 14))
                    params['overbought'] = int(request.form.get('overbought', 70))
                    params['oversold'] = int(request.form.get('oversold', 30))
                
                elif strategy == 'macd_strategy':
                    params['fast_period'] = int(request.form.get('fast_period', 12))
                    params['slow_period'] = int(request.form.get('slow_period', 26))
                    params['signal_period'] = int(request.form.get('signal_period', 9))
                
                # Crear un ID único para el bot
                bot_id = str(uuid.uuid4())
                
                # Crear el bot
                bot = TradingBot(
                    bot_id=bot_id,
                    name=name,
                    strategy=strategy,
                    symbols=symbols,
                    api_key=api_key,
                    api_secret=api_secret,
                    paper_trading=paper_trading,
                    params=params
                )
                
                # Agregar el bot al registro
                active_bots[bot_id] = bot
                
                flash(f'Bot de trading "{name}" creado exitosamente', 'success')
                return redirect(url_for('addon_alpaca_bots_addon.trading_bots_main'))
            
            # Manejar acciones de los bots (iniciar, detener, eliminar)
            elif 'bot_id' in request.args:
                bot_id = request.args.get('bot_id')
                action = request.args.get('action')
                
                if not bot_id or bot_id not in active_bots:
                    flash('Bot no encontrado', 'error')
                    return redirect(url_for('addon_alpaca_bots_addon.trading_bots_main'))
                
                bot = active_bots[bot_id]
                
                if action == 'start':
                    if bot.start():
                        flash(f'Bot "{bot.name}" iniciado exitosamente', 'success')
                    else:
                        flash(f'No se pudo iniciar el bot "{bot.name}"', 'error')
                
                elif action == 'stop':
                    if bot.stop():
                        flash(f'Bot "{bot.name}" detenido exitosamente', 'success')
                    else:
                        flash(f'No se pudo detener el bot "{bot.name}"', 'error')
                
                elif action == 'delete':
                    # Detener el bot si está en ejecución
                    if bot.status == 'running':
                        bot.stop()
                    
                    # Eliminar el bot del registro
                    bot_name = bot.name
                    del active_bots[bot_id]
                    
                    flash(f'Bot "{bot_name}" eliminado exitosamente', 'success')
                
                return redirect(url_for('addon_alpaca_bots_addon.trading_bots_main'))
        
        # === ACCIÓN: CREAR BOT (FORMULARIO) ===
        action = request.args.get('action', 'list')
        if action == 'create' and request.method == 'GET':
            return render_template(
                'create_trading_bot.html',
                processed_data=processed_data
            )
            
        # === ACCIÓN: DETALLES DEL BOT ===
        elif action == 'details':
            bot_id = request.args.get('bot_id')
            if not bot_id or bot_id not in active_bots:
                flash('Bot no encontrado', 'error')
                return redirect(url_for('addon_alpaca_bots_addon.trading_bots_main'))
            
            bot = active_bots[bot_id]
            
            # Renderizar plantilla de detalles
            return render_template(
                'trading_bot_details.html',
                bot=bot,
                bot_data=bot.to_dict(),
                trades=bot.trades,
                processed_data=processed_data
            )
            
        # === ACCIÓN: API DE ESTADO ===
        elif action == 'api_status':
            bots_status = [bot.to_dict() for bot in active_bots.values()]
            return jsonify(bots_status)
            
        # === ACCIÓN POR DEFECTO: LISTAR BOTS ===
        else:
            # Obtener bots activos
            bots_list = [bot.to_dict() for bot in active_bots.values()]
            
            # Renderizar la plantilla principal
            return render_template(
                'alpaca_trading_bots.html',
                bots=bots_list,
                processed_data=processed_data
            )
            
    except Exception as e:
        # Log del error pero mostrar la interfaz de todas formas
        print(f"Error al procesar acción '{request.args.get('action', 'list')}': {str(e)}")
        return render_template(
            'alpaca_trading_bots.html',
            bots=[bot.to_dict() for bot in active_bots.values()],
            processed_data={}
        )

def register_addon():
    """Registra este addon en el sistema"""
    global _is_registered
    if _is_registered:
        return
        
    AddonRegistry.register('alpaca_bots_addon', {
        'name': 'Alpaca Trading Bots',
        'description': 'Sistema de bots de trading automático para operar en Alpaca',
        'route': '/alpaca-bots',
        'view_func': trading_bots_main,
        'template': 'alpaca_trading_bots.html',
        'icon': 'robot',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    _is_registered = True

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
