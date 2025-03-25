from flask import Flask, render_template, request, redirect, url_for, flash
import os
import csv
import json
from datetime import datetime
import importlib

# Importar el sistema de addons
from addon_system import AddonRegistry, load_addons_from_directory, create_addon_template

# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = 'das_trader_analyzer_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite de 16MB para subidas

# Asegurar que existan las carpetas necesarias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('addons', exist_ok=True)

# Rutas para los archivos CSV predeterminados
DEFAULT_ORDERS_PATH = 'data/Orders.csv'
DEFAULT_TRADES_PATH = 'data/Trades.csv'
DEFAULT_TICKETS_PATH = 'data/Tickets.csv'

# Variable global para almacenar resultados (accesible para addons)
processed_data = None

def calculate_metrics(orders):
    """Calcula métricas a partir de las órdenes procesadas"""
    if not orders:
        return {
            'totalPL': 0,
            'winRate': 0,
            'profitFactor': 0,
            'avgWin': 0,
            'avgLoss': 0,
            'maxDrawdown': 0,
            'totalTrades': 0,
            'winningTrades': 0,
            'losingTrades': 0
        }
    
    # Identificar operaciones ganadoras y perdedoras
    winning_orders = [o for o in orders if o.get('pnl', 0) > 0]
    losing_orders = [o for o in orders if o.get('pnl', 0) <= 0]
    
    # Calcular métricas básicas
    total_trades = len(orders)
    winning_trades = len(winning_orders)
    losing_trades = len(losing_orders)
    
    total_pl = sum(o.get('pnl', 0) for o in orders)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Calcular ganancias y pérdidas totales
    total_gain = sum(o.get('pnl', 0) for o in winning_orders) if winning_orders else 0
    total_loss = abs(sum(o.get('pnl', 0) for o in losing_orders)) if losing_orders else 0
    
    # Profit factor
    profit_factor = (total_gain / total_loss) if total_loss > 0 else total_gain
    
    # Promedios
    avg_win = (total_gain / winning_trades) if winning_trades > 0 else 0
    avg_loss = (total_loss / losing_trades) if losing_trades > 0 else 0
    
    # Calcular drawdown
    # Ordenamos por tiempo
    sorted_orders = sorted(orders, key=lambda x: x.get('time', ''))
    max_drawdown = 0
    peak = 0
    running_pl = 0
    
    for order in sorted_orders:
        running_pl += order.get('pnl', 0)
        if running_pl > peak:
            peak = running_pl
        
        drawdown = peak - running_pl
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return {
        'totalPL': total_pl,
        'winRate': win_rate,
        'profitFactor': profit_factor,
        'avgWin': avg_win,
        'avgLoss': avg_loss,
        'maxDrawdown': max_drawdown,
        'totalTrades': total_trades,
        'winningTrades': winning_trades,
        'losingTrades': losing_trades
    }

def analyze_by_symbol(orders):
    """Analiza rendimiento por símbolo"""
    symbols = {}
    
    for order in orders:
        symbol = order.get('symb', 'Unknown')
        
        if symbol not in symbols:
            symbols[symbol] = {
                'totalPL': 0,
                'totalTrades': 0,
                'winningTrades': 0
            }
        
        symbols[symbol]['totalPL'] += order.get('pnl', 0)
        symbols[symbol]['totalTrades'] += 1
        if order.get('pnl', 0) > 0:
            symbols[symbol]['winningTrades'] += 1
    
    # Convertir a lista y calcular win rate
    symbol_stats = []
    for symbol, stats in symbols.items():
        win_rate = (stats['winningTrades'] / stats['totalTrades'] * 100) if stats['totalTrades'] > 0 else 0
        
        symbol_stats.append({
            'symbol': symbol,
            'totalPL': stats['totalPL'],
            'totalTrades': stats['totalTrades'],
            'winRate': win_rate
        })
    
    # Ordenar por P&L total (descendente)
    return sorted(symbol_stats, key=lambda x: x['totalPL'], reverse=True)

def analyze_by_time_of_day(orders):
    """Analiza rendimiento por hora del día"""
    hours = {}
    
    for order in orders:
        hour = order.get('hour', 0)
        
        if hour not in hours:
            hours[hour] = {
                'totalPL': 0,
                'totalTrades': 0,
                'winningTrades': 0
            }
        
        hours[hour]['totalPL'] += order.get('pnl', 0)
        hours[hour]['totalTrades'] += 1
        if order.get('pnl', 0) > 0:
            hours[hour]['winningTrades'] += 1
    
    # Convertir a lista y calcular win rate
    hour_stats = []
    for hour, stats in hours.items():
        win_rate = (stats['winningTrades'] / stats['totalTrades'] * 100) if stats['totalTrades'] > 0 else 0
        
        hour_stats.append({
            'hour': hour,
            'totalPL': stats['totalPL'],
            'totalTrades': stats['totalTrades'],
            'winRate': win_rate
        })
    
    # Ordenar por hora
    return sorted(hour_stats, key=lambda x: x['hour'])

def analyze_by_buysell(orders):
    """Analiza rendimiento por tipo (compra/venta)"""
    buys = [o for o in orders if o.get('B/S') == 'B']
    sells = [o for o in orders if o.get('B/S') == 'S']
    
    # Estadísticas de compras
    buy_pl = sum(o.get('pnl', 0) for o in buys)
    buy_count = len(buys)
    buy_winners = len([o for o in buys if o.get('pnl', 0) > 0])
    buy_win_rate = (buy_winners / buy_count * 100) if buy_count > 0 else 0
    
    # Estadísticas de ventas
    sell_pl = sum(o.get('pnl', 0) for o in sells)
    sell_count = len(sells)
    sell_winners = len([o for o in sells if o.get('pnl', 0) > 0])
    sell_win_rate = (sell_winners / sell_count * 100) if sell_count > 0 else 0
    
    return [
        {
            'type': 'Compras',
            'totalPL': buy_pl,
            'totalTrades': buy_count,
            'winRate': buy_win_rate
        },
        {
            'type': 'Ventas',
            'totalPL': sell_pl,
            'totalTrades': sell_count,
            'winRate': sell_win_rate
        }
    ]

def create_equity_curve(orders):
    """Crea la curva de equidad"""
    # Ordenar por tiempo
    sorted_orders = sorted(orders, key=lambda x: x.get('time', ''))
    
    equity_curve = []
    running_pl = 0
    
    for i, order in enumerate(sorted_orders):
        running_pl += order.get('pnl', 0)
        
        equity_curve.append({
            'tradeNumber': i + 1,
            'time': order.get('time', ''),
            'date': order.get('date', ''),
            'symbol': order.get('symb', ''),
            'pnl': order.get('pnl', 0),
            'equity': running_pl
        })
    
    return equity_curve

def safe_float(value):
    """Convierte un valor a float de forma segura"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def read_csv(file_path):
    """Lee un archivo CSV y devuelve una lista de diccionarios"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def process_orders(orders, trades, tickets):
    """Relaciona órdenes con trades y tickets"""
    processed_orders = []
    
    # Convertir a diccionarios para facilitar búsquedas
    trades_by_order = {}
    for trade in trades:
        order_id = trade.get('OrderID')
        if order_id:
            if order_id not in trades_by_order:
                trades_by_order[order_id] = []
            trades_by_order[order_id].append(trade)
    
    tickets_dict = {}
    for ticket in tickets:
        trade_id = ticket.get('TradeID')
        if trade_id:
            tickets_dict[trade_id] = ticket
    
    for order in orders:
        order_id = order.get('OrderID')
        order_trades = []
        
        # Buscar trades para esta orden
        if order_id in trades_by_order:
            order_trades_list = trades_by_order[order_id]
            
            for trade in order_trades_list:
                trade_dict = trade.copy()
                trade_id = trade.get('TradeID')
                
                # Agregar comisiones y fees del ticket correspondiente
                if trade_id in tickets_dict:
                    ticket = tickets_dict[trade_id]
                    trade_dict['commission'] = safe_float(ticket.get('commission', 0))
                    trade_dict['routeFee'] = safe_float(ticket.get('RouteFee', 0))
                else:
                    trade_dict['commission'] = 0.0
                    trade_dict['routeFee'] = 0.0
                
                order_trades.append(trade_dict)
        
        # Calcular totales y promedio
        total_qty = sum(safe_float(t.get('qty', 0)) for t in order_trades) if order_trades else 0
        
        # Calcular precio promedio ponderado
        if total_qty > 0:
            avg_price = sum(safe_float(t.get('qty', 0)) * safe_float(t.get('price', 0)) for t in order_trades) / total_qty
        else:
            avg_price = 0
        
        total_commission = sum(safe_float(t.get('commission', 0)) for t in order_trades)
        total_route_fee = sum(safe_float(t.get('routeFee', 0)) for t in order_trades)
        
        # Calcular P&L
        pnl = 0
        order_price = safe_float(order.get('price', 0))
        
        if order.get('B/S') == 'B':  # Compra
            pnl = (order_price - avg_price) * total_qty if total_qty > 0 else 0
        else:  # Venta
            pnl = (avg_price - order_price) * total_qty if total_qty > 0 else 0
        
        # Restar comisiones y fees
        pnl = pnl - total_commission - total_route_fee
        
        # Extraer la hora de la operación
        time_str = order.get('time', '')
        hour = 0
        date = ""
        
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            date = dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        
        # Crear objeto de orden procesada
        processed_order = order.copy()
        processed_order.update({
            'trades': order_trades,
            'totalQty': total_qty,
            'avgPrice': avg_price,
            'totalCommission': total_commission,
            'totalRouteFee': total_route_fee,
            'pnl': pnl,
            'hour': hour,
            'date': date
        })
        
        # Solo incluir órdenes que tienen trades
        if order_trades:
            processed_orders.append(processed_order)
    
    return processed_orders

def process_trading_data(orders_path, trades_path, tickets_path):
    """Procesa los datos de trading a partir de los archivos CSV"""
    try:
        # Cargar los archivos CSV
        orders_data = read_csv(orders_path)
        trades_data = read_csv(trades_path)
        tickets_data = read_csv(tickets_path)
        
        # Procesar y relacionar datos
        processed_orders = process_orders(orders_data, trades_data, tickets_data)
        
        # Calcular métricas
        metrics = calculate_metrics(processed_orders)
        
        # Análisis por símbolo
        symbol_performance = analyze_by_symbol(processed_orders)
        
        # Análisis por hora del día
        time_performance = analyze_by_time_of_day(processed_orders)
        
        # Análisis por tipo (compra/venta)
        buysell_performance = analyze_by_buysell(processed_orders)
        
        # Crear curva de equidad
        equity_curve = create_equity_curve(processed_orders)
        
        return {
            'metrics': metrics,
            'symbol_performance': symbol_performance,
            'time_performance': time_performance,
            'buysell_performance': buysell_performance,
            'equity_curve': equity_curve,
            'processed_orders': processed_orders
        }
    
    except Exception as e:
        print(f"Error procesando datos: {e}")
        # Retornar estructura vacía para evitar errores
        return {
            'metrics': {
                'totalPL': 0,
                'winRate': 0,
                'profitFactor': 0,
                'avgWin': 0,
                'avgLoss': 0,
                'maxDrawdown': 0,
                'totalTrades': 0,
                'winningTrades': 0,
                'losingTrades': 0
            },
            'symbol_performance': [],
            'time_performance': [],
            'buysell_performance': [],
            'equity_curve': [],
            'processed_orders': []
        }

# Filtros personalizados para plantillas
@app.template_filter('format_number')
def format_number(value):
    """Filtro para formatear números en las plantillas"""
    if value is None:
        return "-"
    try:
        value = float(value)
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value

@app.template_filter('format_percent')
def format_percent(value):
    """Filtro para formatear porcentajes en las plantillas"""
    if value is None:
        return "-"
    try:
        value = float(value)
        return f"{value:.2f}%"
    except (ValueError, TypeError):
        return value

@app.route('/')
def index():
    """Página principal con formulario para cargar archivos o usar predeterminados"""
    has_default_files = (
        os.path.exists(DEFAULT_ORDERS_PATH) and 
        os.path.exists(DEFAULT_TRADES_PATH) and 
        os.path.exists(DEFAULT_TICKETS_PATH)
    )
    
    return render_template('index.html', has_default_files=has_default_files)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Procesa archivos subidos por el usuario"""
    global processed_data
    
    if 'use_default' in request.form:
        # Usar archivos predeterminados
        if (os.path.exists(DEFAULT_ORDERS_PATH) and 
            os.path.exists(DEFAULT_TRADES_PATH) and 
            os.path.exists(DEFAULT_TICKETS_PATH)):
            
            processed_data = process_trading_data(
                DEFAULT_ORDERS_PATH, 
                DEFAULT_TRADES_PATH, 
                DEFAULT_TICKETS_PATH
            )
            
            return redirect(url_for('dashboard'))
        else:
            flash('No se encontraron archivos predeterminados', 'error')
            return redirect(url_for('index'))
    
    else:
        # Verificar que se hayan enviado todos los archivos
        if 'orders' not in request.files or 'trades' not in request.files or 'tickets' not in request.files:
            flash('Debes subir los tres archivos CSV', 'error')
            return redirect(url_for('index'))
        
        orders_file = request.files['orders']
        trades_file = request.files['trades']
        tickets_file = request.files['tickets']
        
        # Verificar que todos los archivos tengan contenido
        if orders_file.filename == '' or trades_file.filename == '' or tickets_file.filename == '':
            flash('Todos los archivos deben tener contenido', 'error')
            return redirect(url_for('index'))
        
        # Guardar archivos temporalmente
        orders_path = os.path.join(app.config['UPLOAD_FOLDER'], 'orders.csv')
        trades_path = os.path.join(app.config['UPLOAD_FOLDER'], 'trades.csv')
        tickets_path = os.path.join(app.config['UPLOAD_FOLDER'], 'tickets.csv')
        
        orders_file.save(orders_path)
        trades_file.save(trades_path)
        tickets_file.save(tickets_path)
        
        # Procesar los datos
        processed_data = process_trading_data(orders_path, trades_path, tickets_path)
        
        # Copiar archivos a la carpeta 'data' para uso futuro
        import shutil
        shutil.copy(orders_path, DEFAULT_ORDERS_PATH)
        shutil.copy(trades_path, DEFAULT_TRADES_PATH)
        shutil.copy(tickets_path, DEFAULT_TICKETS_PATH)
        
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Muestra el dashboard con resumen de métricas"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    metrics = processed_data['metrics']
    
    # Preparar datos para gráficos
    equity_curve_data = json.dumps(processed_data['equity_curve'])
    symbols_data = json.dumps(processed_data['symbol_performance'][:5])  # Top 5 símbolos
    buysell_data = json.dumps(processed_data['buysell_performance'])
    
    return render_template(
        'dashboard.html', 
        metrics=metrics, 
        equity_curve_data=equity_curve_data,
        symbols_data=symbols_data,
        buysell_data=buysell_data
    )

@app.route('/symbols')
def symbols():
    """Análisis por símbolo"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    symbols_data = processed_data['symbol_performance']
    symbols_json = json.dumps(symbols_data)
    
    return render_template('symbols.html', symbols=symbols_data, symbols_json=symbols_json)

@app.route('/time')
def time_analysis():
    """Análisis por hora del día"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    time_data = processed_data['time_performance']
    time_json = json.dumps(time_data)
    
    # Encontrar las mejores y peores horas
    if time_data:
        best_hour = max(time_data, key=lambda x: x['totalPL'])
        worst_hour = min(time_data, key=lambda x: x['totalPL'])
        most_active = max(time_data, key=lambda x: x['totalTrades'])
    else:
        best_hour = worst_hour = most_active = None
    
    return render_template(
        'time_analysis.html', 
        time_data=time_data, 
        time_json=time_json,
        best_hour=best_hour,
        worst_hour=worst_hour,
        most_active=most_active
    )

@app.route('/buysell')
def buysell():
    """Análisis por tipo (compra/venta)"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    buysell_data = processed_data['buysell_performance']
    buysell_json = json.dumps(buysell_data)
    
    return render_template('buysell.html', buysell=buysell_data, buysell_json=buysell_json)

@app.route('/trades')
def trades():
    """Lista detallada de operaciones"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    processed_orders = processed_data['processed_orders']
    
    # Ordenar por fecha (más reciente primero)
    sorted_orders = sorted(processed_orders, key=lambda x: x.get('time', ''), reverse=True)
    
    return render_template('trades.html', orders=sorted_orders)

@app.route('/addons')
def manage_addons():
    """Página para gestionar addons"""
    # Obtener la lista de addons registrados
    registered_addons = AddonRegistry.get_all_addons()
    
    # Obtener lista de archivos en la carpeta addons
    addon_files = []
    if os.path.exists('addons'):
        addon_files = [f for f in os.listdir('addons') 
                      if f.endswith('.py') and f != '__init__.py']
    
    # Comprobar si cada addon está activo
    addon_status = {}
    for file in addon_files:
        name = file[:-3]  # Quitar .py
        addon_status[name] = name in registered_addons
    
    return render_template(
        'manage_addons.html',
        addons=registered_addons,
        addon_files=addon_files,
        addon_status=addon_status
    )

@app.route('/create_addon', methods=['POST'])
def create_new_addon():
    """Crea un nuevo addon desde la interfaz"""
    name = request.form.get('name')
    route = request.form.get('route', '').lower()
    description = request.form.get('description', '')
    icon = request.form.get('icon', 'chart-bar')
    
    if not name:
        flash('Debes proporcionar un nombre para el addon', 'error')
        return redirect(url_for('manage_addons'))
    
    # Si no se proporciona ruta, crearla desde el nombre
    if not route:
        route = name.lower().replace(' ', '_')
    
    # Crear el addon
    success = create_addon_template(name, route, description, icon)
    
    if success:
        flash(f'Addon "{name}" creado con éxito', 'success')
    else:
        flash(f'Error al crear el addon "{name}"', 'error')
    
    return redirect(url_for('manage_addons'))

@app.route('/reload_addons')
def reload_addons():
    """Recarga los addons desde el directorio"""
    load_addons_from_directory()
    
    # Reinicializar el registro (esto no funcionará en producción sin reiniciar el servidor)
    AddonRegistry.initialize(app)
    
    flash('Addons recargados con éxito', 'success')
    return redirect(url_for('manage_addons'))

if __name__ == '__main__':
    # Cargar los addons
    load_addons_from_directory()
    
    # Inicializar el sistema de addons
    AddonRegistry.initialize(app)
    
    # Comprobar si hay archivos predeterminados y cargarlos
    if (os.path.exists(DEFAULT_ORDERS_PATH) and 
        os.path.exists(DEFAULT_TRADES_PATH) and 
        os.path.exists(DEFAULT_TICKETS_PATH)):
        
        processed_data = process_trading_data(
            DEFAULT_ORDERS_PATH, 
            DEFAULT_TRADES_PATH, 
            DEFAULT_TICKETS_PATH
        )
    
    # Iniciar la aplicación en modo debug
    app.run(host='0.0.0.0', port=5000, debug=True)