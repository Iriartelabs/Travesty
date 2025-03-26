"""
Addon: Trading Alert Bot
Descripción: Sistema de alertas de trading basado en condiciones personalizables
"""
from addon_system import AddonRegistry
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
import json
from datetime import datetime, timedelta

from config import Config
from services.cache_manager import load_processed_data

# Crear un blueprint específico para las alertas
trading_alerts_bp = Blueprint('trading_alerts', __name__)

class TradingAlertSystem:
    def __init__(self):
        self.alerts = []
        self.triggered_alerts = []

    def add_alert(self, name, conditions, description):
        """
        Añade una nueva alerta con condiciones específicas
        
        :param name: Nombre de la alerta
        :param conditions: Diccionario de condiciones para la alerta
        :param description: Descripción detallada de la alerta
        """
        alert = {
            'id': len(self.alerts) + 1,
            'name': name,
            'conditions': conditions,
            'description': description,
            'created_at': datetime.now(),
            'active': True
        }
        self.alerts.append(alert)
        return alert

    def check_alerts(self, orders):
        """
        Verifica todas las alertas contra las órdenes recientes
        
        :param orders: Lista de órdenes procesadas
        :return: Lista de alertas disparadas
        """
        self.triggered_alerts = []
        
        for alert in self.alerts:
            if not alert['active']:
                continue
            
            # Filtrar órdenes según condiciones de la alerta
            matching_orders = self._filter_orders(orders, alert['conditions'])
            
            if matching_orders:
                trigger_info = {
                    'alert': alert,
                    'matching_orders': matching_orders,
                    'triggered_at': datetime.now()
                }
                self.triggered_alerts.append(trigger_info)
        
        return self.triggered_alerts

    def _filter_orders(self, orders, conditions):
        """
        Filtra órdenes basándose en condiciones específicas
        
        :param orders: Lista de órdenes
        :param conditions: Diccionario de condiciones
        :return: Lista de órdenes que cumplen las condiciones
        """
        matched_orders = []
        
        for order in orders:
            match = True
            
            # Condiciones de símbolo
            if 'symbol' in conditions:
                match = match and order['symb'] in conditions['symbol']
            
            # Condiciones de tipo de operación (compra/venta)
            if 'side' in conditions:
                match = match and order['B/S'] in conditions['side']
            
            # Condiciones de cantidad
            if 'min_quantity' in conditions:
                match = match and order['qty'] >= conditions['min_quantity']
            
            # Condiciones de precio
            if 'price_range' in conditions:
                min_price, max_price = conditions['price_range']
                match = match and min_price <= order['price'] <= max_price
            
            # Condiciones de hora
            if 'time_range' in conditions:
                order_time = datetime.strptime(order['time'], '%m/%d/%y %H:%M:%S')
                start_time, end_time = conditions['time_range']
                match = match and start_time <= order_time.time() <= end_time
            
            if match:
                matched_orders.append(order)
        
        return matched_orders

    def get_active_alerts(self):
        """
        Obtiene todas las alertas activas
        
        :return: Lista de alertas activas
        """
        return [alert for alert in self.alerts if alert['active']]

    def disable_alert(self, alert_id):
        """
        Desactiva una alerta específica
        
        :param alert_id: ID de la alerta a desactivar
        
        :return: True si la alerta fue desactivada, False en caso contrario
        """
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['active'] = False
                return True
        return False

# Instancia global del sistema de alertas
alert_system = TradingAlertSystem()

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
    
    # Verificar alertas
    triggered_alerts = alert_system.check_alerts(processed_orders)
    
    print(f"[DEBUG] Alertas disparadas: {len(triggered_alerts)}")
    
    # Obtener alertas activas
    active_alerts = alert_system.get_active_alerts()
    
    print(f"[DEBUG] Alertas activas: {len(active_alerts)}")
    
    return render_template(
        'trading_alerts.html',
        triggered_alerts=triggered_alerts,
        active_alerts=active_alerts,
        processed_data=processed_data
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
        symbol = request.form.getlist('symbol')
        side = request.form.getlist('side')
        min_quantity = float(request.form.get('min_quantity', 0))
        min_price = float(request.form.get('min_price', 0))
        max_price = float(request.form.get('max_price', float('inf')))
        
        # Construir condiciones
        conditions = {}
        if symbol:
            conditions['symbol'] = symbol
        if side:
            conditions['side'] = side
        if min_quantity > 0:
            conditions['min_quantity'] = min_quantity
        if min_price > 0 or max_price < float('inf'):
            conditions['price_range'] = (min_price, max_price)
        
        # Crear alerta
        new_alert = alert_system.add_alert(
            name=alert_name,
            conditions=conditions,
            description=f"Alerta para {', '.join(symbol)} con condiciones específicas"
        )
        
        flash(f'Alerta "{alert_name}" creada exitosamente', 'success')
        return redirect(url_for('trading_alerts.trading_alerts'))
    
    # Obtener símbolos únicos para mostrar en el formulario
    unique_symbols = set()
    for order in processed_data.get('processed_orders', []):
        if 'symb' in order and order['symb']:
            unique_symbols.add(order['symb'])
    
    return render_template(
        'create_alert.html',
        symbols=sorted(list(unique_symbols)),
        processed_data=processed_data
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

def register_addon():
    """
    Registra el addon de alertas de trading
    """
    AddonRegistry.register('trading_alerts', {
        'name': 'Trading Alerts',
        'description': 'Sistema de alertas de trading con condiciones personalizables',
        'route': '/trading_alerts',
        'view_func': trading_alerts,
        'template': 'trading_alerts.html',
        'icon': 'bell',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
