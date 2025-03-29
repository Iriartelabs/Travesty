"""
Rutas para el provider de Alpaca Markets
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from datetime import datetime, timedelta
from services.providers import TradingProviderRegistry
import json

# Crear blueprint para las rutas de Alpaca
alpaca_bp = Blueprint('alpaca', __name__, url_prefix='/alpaca')

# Verificar si el paquete de Alpaca está disponible
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

@alpaca_bp.route('/')
def index():
    """Vista principal de Alpaca"""
    # Verificar si el paquete Alpaca está instalado
    if not ALPACA_AVAILABLE:
        flash("El paquete alpaca-trade-api no está instalado. Por favor, instale con 'pip install alpaca-trade-api'", "error")
        return render_template('alpaca/error.html', error_message="Paquete no instalado")
    
    # Obtener provider de Alpaca si existe
    provider = TradingProviderRegistry.get_provider('alpaca')
    
    # Si no hay provider, mostrar página de configuración
    if not provider:
        flash("El provider de Alpaca no está configurado. Configure sus credenciales en la sección de Configuración.", "warning")
        return redirect(url_for('config.index', section='providers.alpaca'))
    
    # Verificar si el provider está configurado
    account_info = None
    connection_ok = False
    
    if provider.api_key and provider.api_secret:
        # Probar conexión
        connection_test = provider.test_connection()
        connection_ok = connection_test.get('success', False)
        if connection_ok:
            account_info = connection_test
    
    # Obtener datos si se especifica una acción
    symbol_data = None
    symbol = request.args.get('symbol', 'AAPL')
    if connection_ok and symbol:
        # Obtener datos de la última semana
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            bars = provider.get_bars(symbol, timeframe='1D', start=start_date, end=end_date)
            if symbol in bars and not bars[symbol].empty:
                symbol_data = {
                    'dates': bars[symbol]['timestamp'].dt.strftime('%Y-%m-%d').tolist(),
                    'prices': bars[symbol]['close'].tolist(),
                    'volumes': bars[symbol]['volume'].tolist(),
                    'open': bars[symbol]['open'].tolist(),
                    'high': bars[symbol]['high'].tolist(),
                    'low': bars[symbol]['low'].tolist(),
                }
        except Exception as e:
            flash(f"Error al obtener datos para {symbol}: {str(e)}", "error")
    
    # Obtener posiciones si está conectado
    positions = []
    if connection_ok:
        try:
            positions = provider.get_positions()
        except Exception as e:
            flash(f"Error al obtener posiciones: {str(e)}", "error")
    
    return render_template(
        'alpaca/dashboard.html',
        provider=provider,
        connection_ok=connection_ok,
        account_info=account_info,
        symbol=symbol,
        symbol_data=symbol_data,
        positions=positions
    )

@alpaca_bp.route('/order')
def order():
    """Vista para crear órdenes"""
    # Verificar que el provider esté disponible y configurado
    provider = TradingProviderRegistry.get_provider('alpaca')
    
    if not provider or not provider.connected:
        flash("Debe configurar y conectar el provider de Alpaca primero", "error")
        return redirect(url_for('alpaca.index'))
    
    # Obtener lista de símbolos más comunes
    common_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ']
    
    # Para formulario de nueva orden
    symbol = request.args.get('symbol', '')
    
    return render_template(
        'alpaca/order.html',
        provider=provider,
        common_symbols=common_symbols,
        symbol=symbol
    )

@alpaca_bp.route('/portfolio')
def portfolio():
    """Vista para el portafolio"""
    # Verificar que el provider esté disponible y configurado
    provider = TradingProviderRegistry.get_provider('alpaca')
    
    if not provider or not provider.connected:
        flash("Debe configurar y conectar el provider de Alpaca primero", "error")
        return redirect(url_for('alpaca.index'))
    
    # Obtener datos de la cuenta
    account = provider.get_account()
    
    # Obtener posiciones
    positions = provider.get_positions()
    
    # Obtener órdenes recientes
    orders = provider.get_orders(limit=15)
    
    return render_template(
        'alpaca/portfolio.html',
        provider=provider,
        account=account,
        positions=positions,
        orders=orders
    )

@alpaca_bp.route('/api/order', methods=['POST'])
def api_order():
    """Endpoint API para crear órdenes"""
    # Verificar que el provider esté disponible
    provider = TradingProviderRegistry.get_provider('alpaca')
    
    if not provider or not provider.connected:
        return jsonify({'success': False, 'message': 'Provider de Alpaca no configurado'})
    
    # Obtener datos de la solicitud
    data = request.json or request.form.to_dict()
    
    symbol = data.get('symbol', '').upper()
    qty = data.get('qty')
    side = data.get('side')
    order_type = data.get('type', 'market')
    time_in_force = data.get('time_in_force', 'day')
    
    # Validar campos requeridos
    if not symbol or not qty or not side:
        return jsonify({'success': False, 'message': 'Faltan campos requeridos'})
    
    try:
        qty = float(qty)
        if qty <= 0:
            return jsonify({'success': False, 'message': 'La cantidad debe ser mayor que cero'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Cantidad inválida'})
    
    if side not in ['buy', 'sell']:
        return jsonify({'success': False, 'message': 'Lado inválido. Debe ser "buy" o "sell"'})
    
    # Enviar orden
    try:
        order = provider.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )
        
        if order:
            return jsonify({
                'success': True,
                'message': f'Orden creada: {order.id}',
                'order_id': order.id,
                'status': order.status
            })
        else:
            return jsonify({'success': False, 'message': 'Error al crear orden'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@alpaca_bp.route('/test_connection')
def test_connection():
    """Endpoint para probar la conexión a Alpaca"""
    provider = TradingProviderRegistry.get_provider('alpaca')
    
    if not provider:
        flash('Provider de Alpaca no encontrado.', 'error')
        return redirect(url_for('config.index', section='providers.alpaca'))
    
    # Probar conexión
    result = provider.test_connection()
    
    if result.get('success', False):
        flash(f'Conexión exitosa. Cuenta: {result.get("account_number")}', 'success')
    else:
        flash(f'Error de conexión: {result.get("message", "Error desconocido")}', 'error')
    
    return redirect(url_for('config.index', section='providers.alpaca'))
    
@alpaca_bp.route('/debug')
def debug():
    """Vista para depurar la conexión a Alpaca"""
    # Verificar que el provider exista
    provider = TradingProviderRegistry.get_provider('alpaca')
    
    if not provider:
        flash('Provider de Alpaca no encontrado. Configure primero sus credenciales.', 'error')
        return redirect(url_for('config.index', section='providers.alpaca'))
    
    # Ejecutar la función de debug
    result = provider.debug_connection()
    
    if result:
        flash('Depuración completada exitosamente. Revisa la consola para más detalles.', 'success')
    else:
        flash('Se encontraron errores durante la depuración. Revisa la consola para más detalles.', 'error')
    
    return redirect(url_for('alpaca.index'))