"""
Addon: Trading Alert Bot
Descripción: Sistema de alertas de trading basado en condiciones personalizables
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash, request, jsonify
import json
from datetime import datetime, timedelta

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
                order_time = datetime.strptime(order['time'], '%Y-%m-%d %H:%M:%S')
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
        """
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['active'] = False
                return True
        return False

# Instancia global del sistema de alertas
alert_system = TradingAlertSystem()

def trading_alerts_view():
    """
    Vista principal para gestionar alertas de trading
    """
    from app import processed_data
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    # Verificar alertas
    triggered_alerts = alert_system.check_alerts(processed_data['processed_orders'])
    
    # Obtener alertas activas
    active_alerts = alert_system.get_active_alerts()
    
    return render_template(
        'trading_alerts.html',
        triggered_alerts=triggered_alerts,
        active_alerts=active_alerts
    )

def create_alert_view():
    """
    Vista para crear nuevas alertas
    """
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
        return redirect(url_for('trading_alerts'))
    
    return render_template('create_alert.html')

def register_addon():
    """
    Registra el addon de alertas de trading
    """
    AddonRegistry.register('trading_alerts', {
        'name': 'Trading Alerts',
        'description': 'Sistema de alertas de trading con condiciones personalizables',
        'route': '/trading_alerts',
        'view_func': trading_alerts_view,
        'template': 'trading_alerts.html',
        'icon': 'bell',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()