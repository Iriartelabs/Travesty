"""
Addon: Trading Alert System
Descripción: Sistema avanzado de alertas de trading con indicadores técnicos, backtesting y notificaciones
"""
import json
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from addon_system import AddonRegistry

from config import Config
from services.cache_manager import load_processed_data, save_processed_data

# Crear un blueprint específico para las alertas
trading_alerts_bp = Blueprint('trading_alerts', __name__)

class TradingIndicators:
    """Clase para cálculo de indicadores técnicos"""
    
    @staticmethod
    def sma(data, period=20):
        """Calcular Media Móvil Simple (SMA)"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data, period=20):
        """Calcular Media Móvil Exponencial (EMA)"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(data, period=14):
        """Calcular Índice de Fuerza Relativa (RSI)"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(data, fast_period=12, slow_period=26, signal_period=9):
        """Calcular MACD (Moving Average Convergence Divergence)"""
        ema_fast = TradingIndicators.ema(data, fast_period)
        ema_slow = TradingIndicators.ema(data, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TradingIndicators.ema(macd_line, signal_period)
        
        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': macd_line - signal_line
        }
    
    @staticmethod
    def bollinger_bands(data, period=20, num_std=2):
        """Calcular Bandas de Bollinger"""
        sma = TradingIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return {
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band
        }

    @staticmethod
    def support_resistance(data, window=10):
        """Identificar niveles de soporte y resistencia simples"""
        highs = []
        lows = []
        
        # Encontrar máximos y mínimos locales
        for i in range(window, len(data) - window):
            if data.iloc[i] > max(data.iloc[i-window:i]) and data.iloc[i] > max(data.iloc[i+1:i+window+1]):
                highs.append((i, data.iloc[i]))
            
            if data.iloc[i] < min(data.iloc[i-window:i]) and data.iloc[i] < min(data.iloc[i+1:i+window+1]):
                lows.append((i, data.iloc[i]))
        
        # Agrupar niveles similares
        resistance_levels = []
        support_levels = []
        
        if highs:
            # Simplificación básica - promedio de niveles cercanos
            resistance_levels = [sum(h[1] for h in highs) / len(highs)]
        
        if lows:
            # Simplificación básica - promedio de niveles cercanos
            support_levels = [sum(l[1] for l in lows) / len(lows)]
        
        return {
            'resistance': resistance_levels,
            'support': support_levels
        }

class TradingPatterns:
    """Clase para detección de patrones de trading"""
    
    @staticmethod
    def detect_double_top(data, tolerance=0.02):
        """Detectar patrón de doble techo"""
        # Implementación simplificada
        max_idx = data.idxmax()
        if max_idx < len(data) - 10:  # Asegurar que hay suficientes datos después del máximo
            after_max = data[max_idx+1:]
            second_max_idx = after_max.idxmax()
            
            first_peak = data[max_idx]
            second_peak = after_max[second_max_idx]
            
            # Verificar si los dos picos están dentro del rango de tolerancia
            diff_pct = abs(first_peak - second_peak) / first_peak
            
            if diff_pct <= tolerance:
                # Verificar si hay una "valle" entre los dos picos
                between_peaks = data[max_idx+1:second_max_idx]
                if len(between_peaks) > 0 and min(between_peaks) < min(first_peak, second_peak):
                    return True, max_idx, second_max_idx
        
        return False, None, None
    
    @staticmethod
    def detect_double_bottom(data, tolerance=0.02):
        """Detectar patrón de doble suelo"""
        # Implementación simplificada similar al doble techo pero para mínimos
        min_idx = data.idxmin()
        if min_idx < len(data) - 10:
            after_min = data[min_idx+1:]
            second_min_idx = after_min.idxmin()
            
            first_bottom = data[min_idx]
            second_bottom = after_min[second_min_idx]
            
            diff_pct = abs(first_bottom - second_bottom) / first_bottom
            
            if diff_pct <= tolerance:
                between_bottoms = data[min_idx+1:second_min_idx]
                if len(between_bottoms) > 0 and max(between_bottoms) > max(first_bottom, second_bottom):
                    return True, min_idx, second_min_idx
        
        return False, None, None
    
    @staticmethod
    def detect_head_and_shoulders(data, tolerance=0.03):
        """Detectar patrón de cabeza y hombros"""
        # Implementación muy simplificada
        if len(data) < 30:  # Necesitamos suficientes datos
            return False, None
        
        # Dividir en tercios para simplificar
        section_size = len(data) // 3
        left = data[:section_size]
        middle = data[section_size:2*section_size]
        right = data[2*section_size:]
        
        # Encontrar máximos en cada sección
        left_max_idx = left.idxmax()
        middle_max_idx = middle.idxmax() + section_size
        right_max_idx = right.idxmax() + 2*section_size
        
        left_max = data[left_max_idx]
        middle_max = data[middle_max_idx]
        right_max = data[right_max_idx]
        
        # Verificar si el patrón se cumple aproximadamente
        if middle_max > left_max and middle_max > right_max:
            # Verificar si los hombros están aproximadamente al mismo nivel
            shoulder_diff_pct = abs(left_max - right_max) / left_max
            if shoulder_diff_pct <= tolerance:
                return True, [left_max_idx, middle_max_idx, right_max_idx]
        
        return False, None

class BacktestEngine:
    """Motor para hacer backtesting de estrategias de trading"""
    
    @staticmethod
    def test_strategy(data, strategy_func, **params):
        """
        Ejecuta un backtest de una estrategia dada
        
        Args:
            data (pandas.DataFrame): DataFrame con datos históricos
            strategy_func (function): Función que implementa la estrategia
            **params: Parámetros adicionales para la estrategia
            
        Returns:
            dict: Resultados del backtest
        """
        # Crear DataFrame para los resultados
        results = pd.DataFrame(index=data.index)
        results['price'] = data
        
        # Aplicar la estrategia para generar señales
        signals = strategy_func(data, **params)
        results['signal'] = signals
        
        # Calcular retornos
        results['returns'] = results['price'].pct_change()
        
        # Calcular retornos de la estrategia
        # Asumimos que compramos cuando signal=1 y vendemos cuando signal=-1
        results['strategy_returns'] = results['returns'] * results['signal'].shift(1)
        
        # Calcular equity curve
        results['equity_curve'] = (1 + results['strategy_returns']).cumprod()
        
        # Calcular métricas
        total_trades = (results['signal'].diff() != 0).sum()
        winning_trades = ((results['strategy_returns'] > 0) & (results['signal'].shift(1) != 0)).sum()
        
        if total_trades > 0:
            win_rate = winning_trades / total_trades * 100
        else:
            win_rate = 0
        
        max_drawdown = (results['equity_curve'].cummax() - results['equity_curve']).max()
        total_return = results['equity_curve'].iloc[-1] - 1
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'total_return': total_return,
            'equity_curve': results['equity_curve'].to_dict()
        }
    
    @staticmethod
    def sma_crossover_strategy(data, short_period=20, long_period=50):
        """
        Estrategia simple de cruce de medias móviles
        
        Args:
            data (pandas.Series): Serie con precios
            short_period (int): Período para la media corta
            long_period (int): Período para la media larga
            
        Returns:
            pandas.Series: Señales (1=compra, -1=venta, 0=mantener)
        """
        # Calcular medias móviles
        short_sma = TradingIndicators.sma(data, short_period)
        long_sma = TradingIndicators.sma(data, long_period)
        
        # Inicializar señales en 0
        signals = pd.Series(0, index=data.index)
        
        # Generar señales de cruce
        signals[short_sma > long_sma] = 1  # Compra
        signals[short_sma < long_sma] = -1  # Venta
        
        return signals
        
    @staticmethod
    def rsi_strategy(data, period=14, overbought=70, oversold=30):
        """
        Estrategia basada en RSI
        
        Args:
            data (pandas.Series): Serie con precios
            period (int): Período para RSI
            overbought (int): Nivel de sobrecompra
            oversold (int): Nivel de sobreventa
            
        Returns:
            pandas.Series: Señales (1=compra, -1=venta, 0=mantener)
        """
        # Calcular RSI
        rsi_values = TradingIndicators.rsi(data, period)
        
        # Inicializar señales en 0
        signals = pd.Series(0, index=data.index)
        
        # Generar señales
        signals[rsi_values < oversold] = 1  # Compra en sobreventa
        signals[rsi_values > overbought] = -1  # Venta en sobrecompra
        
        return signals

class NotificationManager:
    """Gestor de notificaciones para alertas de trading"""
    
    @staticmethod
    def format_notification(alert, matching_orders):
        """
        Formatea una notificación de alerta
        
        Args:
            alert (dict): Información de la alerta
            matching_orders (list): Órdenes que cumplieron la condición
            
        Returns:
            str: Mensaje formateado
        """
        message = f"🚨 ALERTA: {alert['name']}\n\n"
        
        # Añadir descripción
        message += f"{alert['description']}\n\n"
        
        # Añadir órdenes coincidentes
        message += "Órdenes detectadas:\n"
        for i, order in enumerate(matching_orders[:5]):  # Limitamos a 5 para evitar mensajes muy largos
            symbol = order.get('symb', 'Unknown')
            side = "COMPRA" if order.get('B/S') == 'B' else "VENTA"
            price = order.get('price', 0)
            qty = order.get('qty', 0)
            time_str = order.get('time', '')
            
            message += f"{i+1}. {symbol} - {side} - {qty} @ ${price:.2f} - {time_str}\n"
        
        if len(matching_orders) > 5:
            message += f"... y {len(matching_orders) - 5} más\n"
        
        message += f"\nFecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    @staticmethod
    def send_email_notification(to_email, subject, message):
        """
        Envía una notificación por email (simulado)
        
        Args:
            to_email (str): Dirección de email del destinatario
            subject (str): Asunto del email
            message (str): Contenido del email
            
        Returns:
            bool: True si el envío fue exitoso
        """
        # En una implementación real, aquí iría el código para enviar el email
        # Usando smtplib o algún servicio como SendGrid, Mailgun, etc.
        print(f"[SIMULACIÓN] Enviando email a {to_email}")
        print(f"Asunto: {subject}")
        print(f"Mensaje: {message}")
        
        # Simulamos éxito
        return True
    
    @staticmethod
    def send_telegram_notification(chat_id, bot_token, message):
        """
        Envía una notificación por Telegram (simulado)
        
        Args:
            chat_id (str): ID del chat de Telegram
            bot_token (str): Token del bot de Telegram
            message (str): Mensaje a enviar
            
        Returns:
            bool: True si el envío fue exitoso
        """
        # En una implementación real, aquí iría el código para enviar el mensaje a Telegram
        # Usando requests o python-telegram-bot
        print(f"[SIMULACIÓN] Enviando mensaje a Telegram")
        print(f"Chat ID: {chat_id}")
        print(f"Mensaje: {message}")
        
        # Simulamos éxito
        return True

class RiskManager:
    """Gestor de riesgo para operaciones de trading"""
    
    @staticmethod
    def calculate_position_size(account_size, risk_percentage, entry_price, stop_loss):
        """
        Calcula el tamaño de posición según gestión de riesgo
        
        Args:
            account_size (float): Tamaño de la cuenta en dólares
            risk_percentage (float): Porcentaje de riesgo por operación (1-100)
            entry_price (float): Precio de entrada
            stop_loss (float): Precio de stop loss
            
        Returns:
            dict: Información sobre la posición
        """
        # Verificar datos
        if risk_percentage <= 0 or risk_percentage > 100:
            raise ValueError("El porcentaje de riesgo debe estar entre 1 y 100")
        
        if entry_price <= 0 or stop_loss <= 0:
            raise ValueError("Los precios deben ser positivos")
        
        # Calcular riesgo monetario
        risk_amount = account_size * (risk_percentage / 100)
        
        # Calcular distancia al stop loss
        if entry_price > stop_loss:  # Operación larga
            stop_distance = entry_price - stop_loss
            direction = "LONG"
        else:  # Operación corta
            stop_distance = stop_loss - entry_price
            direction = "SHORT"
        
        # Calcular tamaño de posición
        if stop_distance <= 0:
            raise ValueError("La distancia al stop loss debe ser positiva")
        
        position_size = risk_amount / stop_distance
        
        # Calcular valor de la posición
        position_value = position_size * entry_price
        
        return {
            'direction': direction,
            'position_size': position_size,
            'position_value': position_value,
            'risk_amount': risk_amount,
            'stop_distance': stop_distance,
            'risk_reward_1_2': {
                'target_price': entry_price + (stop_distance * 2) if direction == "LONG" else entry_price - (stop_distance * 2),
                'profit_potential': risk_amount * 2
            },
            'risk_reward_1_3': {
                'target_price': entry_price + (stop_distance * 3) if direction == "LONG" else entry_price - (stop_distance * 3),
                'profit_potential': risk_amount * 3
            }
        }

class AdvancedTradingAlertSystem:
    """Sistema avanzado de alertas de trading"""
    
    def __init__(self):
        self.alerts = []
        self.triggered_alerts = []
        self.notification_settings = {
            'email_enabled': False,
            'email_address': '',
            'telegram_enabled': False,
            'telegram_chat_id': '',
            'telegram_bot_token': ''
        }
        self.risk_settings = {
            'account_size': 10000,
            'default_risk_percentage': 1
        }
    
    def add_alert(self, name, conditions, description, notification_channels=None):
        """
        Añade una nueva alerta con condiciones específicas
        
        Args:
            name (str): Nombre de la alerta
            conditions (dict): Condiciones para la alerta
            description (str): Descripción detallada
            notification_channels (list): Canales de notificación
            
        Returns:
            dict: Alerta creada
        """
        if notification_channels is None:
            notification_channels = ['web']
        
        alert = {
            'id': len(self.alerts) + 1,
            'name': name,
            'conditions': conditions,
            'description': description,
            'created_at': datetime.now(),
            'active': True,
            'notification_channels': notification_channels
        }
        
        self.alerts.append(alert)
        return alert
    
    def check_basic_alerts(self, orders):
        """
        Verifica alertas basadas en condiciones simples sobre órdenes
        
        Args:
            orders (list): Lista de órdenes procesadas
            
        Returns:
            list: Alertas disparadas
        """
        triggered = []
        
        for alert in self.alerts:
            if not alert['active']:
                continue
            
            # Verificar si es una alerta básica
            if 'type' not in alert['conditions'] or alert['conditions']['type'] == 'basic':
                # Filtrar órdenes según condiciones
                matching_orders = self._filter_orders(orders, alert['conditions'])
                
                if matching_orders:
                    trigger_info = {
                        'alert': alert,
                        'matching_orders': matching_orders,
                        'triggered_at': datetime.now()
                    }
                    triggered.append(trigger_info)
                    self.triggered_alerts.append(trigger_info)
                    
                    # Enviar notificaciones
                    self._send_notifications(alert, matching_orders)
        
        return triggered
    
    def check_technical_alerts(self, price_data):
        """
        Verifica alertas basadas en indicadores técnicos
        
        Args:
            price_data (pandas.DataFrame): DataFrame con datos de precios
            
        Returns:
            list: Alertas disparadas
        """
        triggered = []
        
        for alert in self.alerts:
            if not alert['active']:
                continue
            
            # Verificar si es una alerta técnica
            if 'type' in alert['conditions'] and alert['conditions']['type'] == 'technical':
                # Verificar el indicador específico
                indicator_type = alert['conditions'].get('indicator', '')
                
                if indicator_type == 'sma_crossover':
                    # Verificar cruce de medias móviles
                    short_period = alert['conditions'].get('short_period', 20)
                    long_period = alert['conditions'].get('long_period', 50)
                    
                    short_sma = TradingIndicators.sma(price_data, short_period)
                    long_sma = TradingIndicators.sma(price_data, long_period)
                    
                    # Verificar si hay un cruce reciente (en las últimas 2 barras)
                    if len(short_sma) >= 2 and len(long_sma) >= 2:
                        # Cruce hacia arriba
                        if alert['conditions'].get('direction', 'up') == 'up':
                            if short_sma.iloc[-2] <= long_sma.iloc[-2] and short_sma.iloc[-1] > long_sma.iloc[-1]:
                                trigger_info = {
                                    'alert': alert,
                                    'triggered_at': datetime.now(),
                                    'indicator_values': {
                                        'short_sma': short_sma.iloc[-1],
                                        'long_sma': long_sma.iloc[-1]
                                    }
                                }
                                triggered.append(trigger_info)
                                self.triggered_alerts.append(trigger_info)
                                
                                # Enviar notificaciones
                                self._send_notifications(alert, [], indicator_values=trigger_info['indicator_values'])
                        
                        # Cruce hacia abajo
                        elif alert['conditions'].get('direction', 'up') == 'down':
                            if short_sma.iloc[-2] >= long_sma.iloc[-2] and short_sma.iloc[-1] < long_sma.iloc[-1]:
                                trigger_info = {
                                    'alert': alert,
                                    'triggered_at': datetime.now(),
                                    'indicator_values': {
                                        'short_sma': short_sma.iloc[-1],
                                        'long_sma': long_sma.iloc[-1]
                                    }
                                }
                                triggered.append(trigger_info)
                                self.triggered_alerts.append(trigger_info)
                                
                                # Enviar notificaciones
                                self._send_notifications(alert, [], indicator_values=trigger_info['indicator_values'])
                
                elif indicator_type == 'rsi':
                    # Verificar condiciones de RSI
                    period = alert['conditions'].get('period', 14)
                    overbought = alert['conditions'].get('overbought', 70)
                    oversold = alert['conditions'].get('oversold', 30)
                    
                    rsi_values = TradingIndicators.rsi(price_data, period)
                    
                    if len(rsi_values) >= 2:
                        # Condición de sobrecompra
                        if alert['conditions'].get('condition', 'overbought') == 'overbought':
                            if rsi_values.iloc[-2] < overbought and rsi_values.iloc[-1] >= overbought:
                                trigger_info = {
                                    'alert': alert,
                                    'triggered_at': datetime.now(),
                                    'indicator_values': {
                                        'rsi': rsi_values.iloc[-1],
                                        'threshold': overbought
                                    }
                                }
                                triggered.append(trigger_info)
                                self.triggered_alerts.append(trigger_info)
                                
                                # Enviar notificaciones
                                self._send_notifications(alert, [], indicator_values=trigger_info['indicator_values'])
                        
                        # Condición de sobreventa
                        elif alert['conditions'].get('condition', 'overbought') == 'oversold':
                            if rsi_values.iloc[-2] > oversold and rsi_values.iloc[-1] <= oversold:
                                trigger_info = {
                                    'alert': alert,
                                    'triggered_at': datetime.now(),
                                    'indicator_values': {
                                        'rsi': rsi_values.iloc[-1],
                                        'threshold': oversold
                                    }
                                }
                                triggered.append(trigger_info)
                                self.triggered_alerts.append(trigger_info)
                                
                                # Enviar notificaciones
                                self._send_notifications(alert, [], indicator_values=trigger_info['indicator_values'])
                
                elif indicator_type == 'macd':
                    # Verificar señales de MACD
                    fast_period = alert['conditions'].get('fast_period', 12)
                    slow_period = alert['conditions'].get('slow_period', 26)
                    signal_period = alert['conditions'].get('signal_period', 9)
                    
                    macd_result = TradingIndicators.macd(
                        price_data, 
                        fast_period=fast_period, 
                        slow_period=slow_period, 
                        signal_period=signal_period
                    )
                    
                    macd_line = macd_result['macd_line']
                    signal_line = macd_result['signal_line']
                    
                    if len(macd_line) >= 2 and len(signal_line) >= 2:
                        # Cruce hacia arriba (señal de compra)
                        if alert['conditions'].get('signal', 'buy') == 'buy':
                            if macd_line.iloc[-2] <= signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
                                trigger_info = {
                                    'alert': alert,
                                    'triggered_at': datetime.now(),
                                    'indicator_values': {
                                        'macd': macd_line.iloc[-1],
                                        'signal': signal_line.iloc[-1]
                                    }
                                }
                                triggered.append(trigger_info)
                                self.triggered_alerts.append(trigger_info)
                                
                                # Enviar notificaciones
                                self._send_notifications(alert, [], indicator_values=trigger_info['indicator_values'])
                        
                        # Cruce hacia abajo (señal de venta)
                        elif alert['conditions'].get('signal', 'buy') == 'sell':
                            if macd_line.iloc[-2] >= signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
                                trigger_info = {
                                    'alert': alert,
                                    'triggered_at': datetime.now(),
                                    'indicator_values': {
                                        'macd': macd_line.iloc[-1],
                                        'signal': signal_line.iloc[-1]
                                    }
                                }
                                triggered.append(trigger_info)
                                self.triggered_alerts.append(trigger_info)
                                
                                # Enviar notificaciones
                                self._send_notifications(alert, [], indicator_values=trigger_info['indicator_values'])
                
                elif indicator_type == 'pattern':
                    # Verificar patrones de precio
                    pattern_type = alert['conditions'].get('pattern', '')
                    
                    if pattern_type == 'double_top':
                        is_pattern, *_ = TradingPatterns.detect_double_top(price_data)
                        if is_pattern:
                            trigger_info = {
                                'alert': alert,
                                'triggered_at': datetime.now(),
                                'pattern': 'double_top'
                            }
                            triggered.append(trigger_info)
                            self.triggered_alerts.append(trigger_info)
                            
                            # Enviar notificaciones
                            self._send_notifications(alert, [], pattern=pattern_type)
                    
                    elif pattern_type == 'double_bottom':
                        is_pattern, *_ = TradingPatterns.detect_double_bottom(price_data)
                        if is_pattern:
                            trigger_info = {
                                'alert': alert,
                                'triggered_at': datetime.now(),
                                'pattern': 'double_bottom'
                            }
                            triggered.append(trigger_info)
                            self.triggered_alerts.append(trigger_info)
                            
                            # Enviar notificaciones
                            self._send_notifications(alert, [], pattern=pattern_type)
                    
                    elif pattern_type == 'head_and_shoulders':
                        is_pattern, *_ = TradingPatterns.detect_head_and_shoulders(price_data)
                        if is_pattern:
                            trigger_info = {
                                'alert': alert,
                                'triggered_at': datetime.now(),
                                'pattern': 'head_and_shoulders'
                            }
                            triggered.append(trigger_info)
                            self.triggered_alerts.append(trigger_info)
                            
                            # Enviar notificaciones
                            self._send_notifications(alert, [], pattern=pattern_type)
        
        return triggered
    
    def _filter_orders(self, orders, conditions):
        """
        Filtra órdenes basándose en condiciones específicas
        
        Args:
            orders (list): Lista de órdenes
            conditions (dict): Diccionario de condiciones
            
        Returns:
            list: Lista de órdenes que cumplen las condiciones
        """
        matched_orders = []
        
        for order in orders:
            match = True
            
            # Condiciones de símbolo
            if 'symbol' in conditions:
                match = match and order.get('symb', '') in conditions['symbol']
            
            # Condiciones de tipo de operación (compra/venta)
            if 'side' in conditions:
                match = match and order.get('B/S', '') in conditions['side']
            
            # Condiciones de cantidad
            if 'min_quantity' in conditions:
                match = match and order.get('qty', 0) >= conditions['min_quantity']
            
            # Condiciones de precio
            if 'price_range' in conditions:
                min_price, max_price = conditions['price_range']
                match = match and min_price <= order.get('price', 0) <= max_price
            
            # Condiciones de hora
            if 'time_range' in conditions:
                try:
                    order_time = datetime.strptime(order.get('time', ''), '%m/%d/%y %H:%M:%S')
                    start_time, end_time = conditions['time_range']
                    current_time = order_time.time()
                    match = match and start_time <= current_time <= end_time
                except (ValueError, TypeError):
                    # Si hay error al parsear la fecha, no se cumple la condición
                    match = False
            
            if match:
                matched_orders.append(order)
        
        return matched_orders
    
    def _send_notifications(self, alert, matching_orders, indicator_values=None, pattern=None):
        """
        Envía notificaciones según los canales configurados
        
        Args:
            alert (dict): Información de la alerta
            matching_orders (list): Órdenes que cumplieron la condición
            indicator_values (dict): Valores de indicadores (para alertas técnicas)
            pattern (str): Patrón detectado (para alertas de patrones)
            
        Returns:
            bool: True si se enviaron todas las notificaciones correctamente
        """
        # Formatear mensaje base
        if indicator_values or pattern:
            # Es una alerta técnica
            message = f"🚨 ALERTA TÉCNICA: {alert['name']}\n\n"
            message += f"{alert['description']}\n\n"
            
            if indicator_values:
                message += "Valores del indicador:\n"
                for key, value in indicator_values.items():
                    message += f"- {key}: {value:.4f}\n"
            
            if pattern:
                message += f"Patrón detectado: {pattern}\n"
            
            message += f"\nFecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            # Es una alerta básica de órdenes
            message = NotificationManager.format_notification(alert, matching_orders)
        
        # Enviar notificaciones según canales configurados
        success = True
        
        if 'web' in alert.get('notification_channels', ['web']):
            # La notificación web se maneja automáticamente al añadir a triggered_alerts
            pass
        
        if 'email' in alert.get('notification_channels', []) and self.notification_settings['email_enabled']:
            email_success = NotificationManager.send_email_notification(
                self.notification_settings['email_address'],
                f"Alerta de Trading: {alert['name']}",
                message
            )
            success = success and email_success
        
        if 'telegram' in alert.get('notification_channels', []) and self.notification_settings['telegram_enabled']:
            telegram_success = NotificationManager.send_telegram_notification(
                self.notification_settings['telegram_chat_id'],
                self.notification_settings['telegram_bot_token'],
                message
            )
            success = success and telegram_success
        
        return success
    
    def update_notification_settings(self, settings):
        """
        Actualiza configuración de notificaciones
        
        Args:
            settings (dict): Nueva configuración
            
        Returns:
            dict: Configuración actualizada
        """
        self.notification_settings.update(settings)
        return self.notification_settings
    
    def update_risk_settings(self, settings):
        """
        Actualiza configuración de gestión de riesgo
        
        Args:
            settings (dict): Nueva configuración
            
        Returns:
            dict: Configuración actualizada
        """
        self.risk_settings.update(settings)
        return self.risk_settings
    
    def get_active_alerts(self):
        """
        Obtiene todas las alertas activas
        
        Returns:
            list: Lista de alertas activas
        """
        return [alert for alert in self.alerts if alert['active']]
    
    def get_triggered_alerts(self, limit=50):
        """
        Obtiene las alertas disparadas recientemente
        
        Args:
            limit (int): Número máximo de alertas a retornar
            
        Returns:
            list: Lista de alertas disparadas
        """
        # Ordenar por fecha (más reciente primero) y limitar
        sorted_alerts = sorted(
            self.triggered_alerts, 
            key=lambda x: x['triggered_at'], 
            reverse=True
        )
        return sorted_alerts[:limit]
    
    def disable_alert(self, alert_id):
        """
        Desactiva una alerta específica
        
        Args:
            alert_id (int): ID de la alerta a desactivar
            
        Returns:
            bool: True si la alerta fue desactivada, False en caso contrario
        """
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['active'] = False
                return True
        return False
    
    def run_backtest(self, symbol, strategy_name, **params):
        """
        Ejecuta un backtest para una estrategia específica
        
        Args:
            symbol (str): Símbolo para el backtest
            strategy_name (str): Nombre de la estrategia a probar
            **params: Parámetros adicionales para la estrategia
            
        Returns:
            dict: Resultados del backtest
        """
        # Cargar datos históricos (simulados)
        # En una implementación real, se cargarían datos reales
        # Esta es solo una simulación
        
        # Crear datos simulados
        np.random.seed(42)  # Para reproducibilidad
        n_days = 100
        
        start_price = 100
        daily_returns = np.random.normal(0.0005, 0.02, n_days)
        
        # Generar precios simulados
        prices = [start_price]
        for ret in daily_returns:
            prices.append(prices[-1] * (1 + ret))
        
        # Convertir a DataFrame
        dates = pd.date_range(start='2023-01-01', periods=n_days+1)
        price_data = pd.Series(prices, index=dates)
        
        # Seleccionar estrategia
        if strategy_name == 'sma_crossover':
            short_period = params.get('short_period', 20)
            long_period = params.get('long_period', 50)
            strategy_func = BacktestEngine.sma_crossover_strategy
            strategy_params = {
                'short_period': short_period,
                'long_period': long_period
            }
        elif strategy_name == 'rsi':
            period = params.get('period', 14)
            overbought = params.get('overbought', 70)
            oversold = params.get('oversold', 30)
            strategy_func = BacktestEngine.rsi_strategy
            strategy_params = {
                'period': period,
                'overbought': overbought,
                'oversold': oversold
            }
        else:
            raise ValueError(f"Estrategia '{strategy_name}' no implementada")
        
        # Ejecutar backtest
        results = BacktestEngine.test_strategy(price_data, strategy_func, **strategy_params)
        
        # Añadir metadatos
        results['symbol'] = symbol
        results['strategy'] = strategy_name
        results['params'] = strategy_params
        
        return results
    
    def calculate_position_size(self, symbol, entry_price, stop_loss):
        """
        Calcula el tamaño de posición recomendado
        
        Args:
            symbol (str): Símbolo del activo
            entry_price (float): Precio de entrada
            stop_loss (float): Precio de stop loss
            
        Returns:
            dict: Información sobre posición recomendada
        """
        account_size = self.risk_settings['account_size']
        risk_percentage = self.risk_settings['default_risk_percentage']
        
        try:
            position_info = RiskManager.calculate_position_size(
                account_size, 
                risk_percentage, 
                entry_price, 
                stop_loss
            )
            
            # Añadir metadatos
            position_info['symbol'] = symbol
            position_info['entry_price'] = entry_price
            position_info['stop_loss'] = stop_loss
            
            return position_info
        except ValueError as e:
            return {'error': str(e)}

# Instancia global del sistema de alertas avanzado
alert_system = AdvancedTradingAlertSystem()

@trading_alerts_bp.route('/trading-alerts')
def trading_alerts():
    """
    Vista principal para gestionar alertas de trading
    """
    # Agregar mensaje de depuración
    print("[DEBUG] Entrando en trading_alerts_view()")
    
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    print(f"[DEBUG] Processed data: {processed_data is not None}")
    
    if processed_data is None:
        print("[DEBUG] No hay datos procesados")
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener órdenes procesadas
    processed_orders = processed_data.get('processed_orders', [])
    
    print(f"[DEBUG] Número de órdenes procesadas: {len(processed_orders)}")
    
    # Verificar alertas básicas
    triggered_alerts = alert_system.check_basic_alerts(processed_orders)
    
    print(f"[DEBUG] Alertas disparadas: {len(triggered_alerts)}")
    
    # Obtener alertas activas
    active_alerts = alert_system.get_active_alerts()
    
    print(f"[DEBUG] Alertas activas: {len(active_alerts)}")
    
    # Obtener todas las alertas disparadas (básicas y técnicas)
    all_triggered_alerts = alert_system.get_triggered_alerts()
    
    # Obtener símbolos únicos para el formulario
    unique_symbols = set()
    for order in processed_orders:
        if 'symb' in order and order['symb']:
            unique_symbols.add(order['symb'])
    
    return render_template(
        'trading_alerts.html',
        triggered_alerts=all_triggered_alerts,
        active_alerts=active_alerts,
        processed_data=processed_data,
        symbols=sorted(list(unique_symbols)),
        notification_settings=alert_system.notification_settings,
        risk_settings=alert_system.risk_settings
    )

@trading_alerts_bp.route('/create-alert', methods=['GET', 'POST'])
def create_alert():
    """
    Vista para crear nuevas alertas
    """
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    print(f"[DEBUG] Processed data: {processed_data is not None}")
    
    # Verificar si hay datos cargados
    if processed_data is None:
        print("[DEBUG] No hay datos procesados")
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Recoger datos del formulario
        alert_name = request.form.get('name')
        alert_type = request.form.get('alert_type', 'basic')
        
        if alert_type == 'basic':
            # Alertas básicas basadas en órdenes
            symbol = request.form.getlist('symbol')
            side = request.form.getlist('side')
            min_quantity = float(request.form.get('min_quantity', 0))
            min_price = float(request.form.get('min_price', 0))
            max_price = float(request.form.get('max_price', float('inf')))
            
            # Construir condiciones
            conditions = {
                'type': 'basic'
            }
            
            if symbol:
                conditions['symbol'] = symbol
            if side:
                conditions['side'] = side
            if min_quantity > 0:
                conditions['min_quantity'] = min_quantity
            if min_price > 0 or max_price < float('inf'):
                conditions['price_range'] = (min_price, max_price)
            
            description = f"Alerta para {', '.join(symbol)} con condiciones específicas"
            
        elif alert_type == 'technical':
            # Alertas basadas en indicadores técnicos
            indicator_type = request.form.get('indicator_type')
            symbol = request.form.get('indicator_symbol')
            description = f"Alerta técnica para {symbol}"
            
            # Construir condiciones según el tipo de indicador
            conditions = {
                'type': 'technical',
                'indicator': indicator_type,
                'symbol': symbol
            }
            
            if indicator_type == 'sma_crossover':
                short_period = int(request.form.get('short_period', 20))
                long_period = int(request.form.get('long_period', 50))
                direction = request.form.get('crossover_direction', 'up')
                
                conditions.update({
                    'short_period': short_period,
                    'long_period': long_period,
                    'direction': direction
                })
                
                cross_type = "alcista" if direction == 'up' else "bajista"
                description = f"Alerta de cruce {cross_type} de SMA {short_period} y SMA {long_period} para {symbol}"
                
            elif indicator_type == 'rsi':
                period = int(request.form.get('rsi_period', 14))
                condition = request.form.get('rsi_condition', 'overbought')
                overbought = int(request.form.get('overbought', 70))
                oversold = int(request.form.get('oversold', 30))
                
                conditions.update({
                    'period': period,
                    'condition': condition,
                    'overbought': overbought,
                    'oversold': oversold
                })
                
                condition_text = "sobrecompra" if condition == 'overbought' else "sobreventa"
                threshold = overbought if condition == 'overbought' else oversold
                description = f"Alerta de {condition_text} (RSI {period} cruza {threshold}) para {symbol}"
                
            elif indicator_type == 'macd':
                fast_period = int(request.form.get('fast_period', 12))
                slow_period = int(request.form.get('slow_period', 26))
                signal_period = int(request.form.get('signal_period', 9))
                signal = request.form.get('macd_signal', 'buy')
                
                conditions.update({
                    'fast_period': fast_period,
                    'slow_period': slow_period,
                    'signal_period': signal_period,
                    'signal': signal
                })
                
                signal_text = "compra" if signal == 'buy' else "venta"
                description = f"Alerta de {signal_text} MACD ({fast_period},{slow_period},{signal_period}) para {symbol}"
                
            elif indicator_type == 'pattern':
                pattern = request.form.get('pattern_type', 'double_top')
                
                conditions.update({
                    'pattern': pattern
                })
                
                pattern_names = {
                    'double_top': 'Doble Techo',
                    'double_bottom': 'Doble Suelo',
                    'head_and_shoulders': 'Cabeza y Hombros'
                }
                
                pattern_name = pattern_names.get(pattern, pattern)
                description = f"Alerta de patrón {pattern_name} para {symbol}"
        else:
            flash('Tipo de alerta no válido', 'error')
            return redirect(url_for('trading_alerts.create_alert'))
        
        # Canales de notificación
        notification_channels = request.form.getlist('notification_channels')
        
        # Crear alerta
        new_alert = alert_system.add_alert(
            name=alert_name,
            conditions=conditions,
            description=description,
            notification_channels=notification_channels
        )
        
        flash(f'Alerta "{alert_name}" creada exitosamente', 'success')
        return redirect(url_for('trading_alerts.trading_alerts'))
    
    # GET request - mostrar formulario
    # Obtener símbolos únicos para mostrar en el formulario
    unique_symbols = set()
    for order in processed_data.get('processed_orders', []):
        if 'symb' in order and order['symb']:
            unique_symbols.add(order['symb'])
    
    return render_template(
        'create_alert.html',
        symbols=sorted(list(unique_symbols)),
        processed_data=processed_data,
        notification_settings=alert_system.notification_settings
    )

@trading_alerts_bp.route('/disable-alert', methods=['POST'])
def disable_alert():
    """API para desactivar una alerta"""
    data = request.json
    if not data or 'alert_id' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos'})
    
    alert_id = data['alert_id']
    success = alert_system.disable_alert(alert_id)
    return jsonify({'success': success})

@trading_alerts_bp.route('/backtest', methods=['GET', 'POST'])
def backtest():
    """
    Vista para realizar backtests de estrategias
    """
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener símbolos únicos
    unique_symbols = set()
    for order in processed_data.get('processed_orders', []):
        if 'symb' in order and order['symb']:
            unique_symbols.add(order['symb'])
    
    backtest_results = None
    
    if request.method == 'POST':
        # Obtener datos del formulario
        symbol = request.form.get('symbol')
        strategy = request.form.get('strategy')
        
        # Parámetros específicos según la estrategia
        params = {}
        
        if strategy == 'sma_crossover':
            params['short_period'] = int(request.form.get('short_period', 20))
            params['long_period'] = int(request.form.get('long_period', 50))
        elif strategy == 'rsi':
            params['period'] = int(request.form.get('rsi_period', 14))
            params['overbought'] = int(request.form.get('overbought', 70))
            params['oversold'] = int(request.form.get('oversold', 30))
        
        # Ejecutar backtest
        try:
            backtest_results = alert_system.run_backtest(symbol, strategy, **params)
            flash(f'Backtest completado para {symbol} usando estrategia {strategy}', 'success')
        except Exception as e:
            flash(f'Error al ejecutar backtest: {str(e)}', 'error')
    
    return render_template(
        'backtest.html',
        symbols=sorted(list(unique_symbols)),
        processed_data=processed_data,
        backtest_results=backtest_results
    )

@trading_alerts_bp.route('/position-calculator', methods=['GET', 'POST'])
def position_calculator():
    """
    Calculadora de tamaño de posición según gestión de riesgo
    """
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener símbolos únicos
    unique_symbols = set()
    for order in processed_data.get('processed_orders', []):
        if 'symb' in order and order['symb']:
            unique_symbols.add(order['symb'])
    
    position_info = None
    
    if request.method == 'POST':
        # Obtener datos del formulario
        symbol = request.form.get('symbol')
        entry_price = float(request.form.get('entry_price', 0))
        stop_loss = float(request.form.get('stop_loss', 0))
        
        # Verificar datos
        if entry_price <= 0 or stop_loss <= 0:
            flash('Los precios deben ser positivos', 'error')
        elif entry_price == stop_loss:
            flash('El precio de entrada y el stop loss no pueden ser iguales', 'error')
        else:
            # Calcular tamaño de posición
            try:
                position_info = alert_system.calculate_position_size(symbol, entry_price, stop_loss)
                if 'error' in position_info:
                    flash(f"Error: {position_info['error']}", 'error')
            except Exception as e:
                flash(f'Error al calcular tamaño de posición: {str(e)}', 'error')
    
    return render_template(
        'position_calculator.html',
        symbols=sorted(list(unique_symbols)),
        processed_data=processed_data,
        position_info=position_info,
        risk_settings=alert_system.risk_settings
    )

@trading_alerts_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    Configuración del sistema de alertas
    """
    if request.method == 'POST':
        # Configuración de notificaciones
        email_enabled = 'email_enabled' in request.form
        email_address = request.form.get('email_address', '')
        telegram_enabled = 'telegram_enabled' in request.form
        telegram_chat_id = request.form.get('telegram_chat_id', '')
        telegram_bot_token = request.form.get('telegram_bot_token', '')
        
        # Configuración de riesgo
        account_size = float(request.form.get('account_size', 10000))
        default_risk_percentage = float(request.form.get('default_risk_percentage', 1))
        
        # Actualizar configuración
        alert_system.update_notification_settings({
            'email_enabled': email_enabled,
            'email_address': email_address,
            'telegram_enabled': telegram_enabled,
            'telegram_chat_id': telegram_chat_id,
            'telegram_bot_token': telegram_bot_token
        })
        
        alert_system.update_risk_settings({
            'account_size': account_size,
            'default_risk_percentage': default_risk_percentage
        })
        
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('trading_alerts.settings'))
    
    return render_template(
        'alert_settings.html',
        notification_settings=alert_system.notification_settings,
        risk_settings=alert_system.risk_settings
    )

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('trading_alerts', {
        'name': 'Trading Alerts Pro',
        'description': 'Sistema avanzado de alertas de trading con indicadores técnicos, backtesting y notificaciones',
        'route': '/trading-alerts',
        'view_func': trading_alerts,
        'template': 'trading_alerts.html',
        'icon': 'bell',
        'active': True,
        'version': '2.0.0',
        'author': 'DAS Trader Analyzer Team'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
