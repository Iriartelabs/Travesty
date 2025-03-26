from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g
import os
import csv
import json
import pickle
from datetime import datetime, timedelta
import importlib

# Importar la configuración
from config import get_config

# Importar el sistema de addons
from addon_system import AddonRegistry, load_addons_from_directory, create_addon_template

# Importar el módulo de base de datos
from db_integration import (
    init_app, 
    import_data_to_db, 
    get_all_processed_data,
    get_processed_orders_from_db,
    get_daily_metrics,
    get_symbol_performance,
    get_time_performance,
    get_buysell_performance,
    get_available_symbols,
    get_available_date_range,
    get_trading_alerts,
    add_trading_alert,
    disable_trading_alert,
    check_trading_alerts,
    get_triggered_alerts,
    summarize_database_stats
)

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config.from_object(get_config())

# Asegurar que existan las carpetas necesarias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('addons', exist_ok=True)

# Rutas para los archivos CSV predeterminados
DEFAULT_ORDERS_PATH = 'data/Orders.csv'
DEFAULT_TRADES_PATH = 'data/Trades.csv'
DEFAULT_TICKETS_PATH = 'data/Tickets.csv'

# Ruta para el archivo de caché de datos procesados
DATA_CACHE_PATH = 'data/processed_cache.pkl'

# Variable global para almacenar resultados (accesible para addons)
processed_data = None

# Inicializar la integración con la base de datos
init_app(app)

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
    
    # Obtener estadísticas de la base de datos
    db_stats = summarize_database_stats()
    
    # Obtener rango de fechas disponibles
    date_range = get_available_date_range()
    
    return render_template(
        'index.html', 
        has_default_files=has_default_files,
        db_stats=db_stats,
        date_range=date_range
    )

@app.route('/upload', methods=['POST'])
def upload_files():
    """Procesa archivos subidos por el usuario"""
    global processed_data
    
    if 'use_default' in request.form:
        # Usar archivos predeterminados
        if (os.path.exists(DEFAULT_ORDERS_PATH) and 
            os.path.exists(DEFAULT_TRADES_PATH) and 
            os.path.exists(DEFAULT_TICKETS_PATH)):
            
            # Importar a la base de datos y obtener datos procesados
            import_summary = import_data_to_db(
                DEFAULT_ORDERS_PATH, 
                DEFAULT_TRADES_PATH, 
                DEFAULT_TICKETS_PATH,
                app
            )
            
            # Verificar resultado de la importación
            if import_summary['status'] == 'success':
                flash(f"Datos importados correctamente: {import_summary['orders_imported']} órdenes, {import_summary['trades_imported']} trades", 'success')
            else:
                flash(f"Importación parcial: {import_summary['status']}", 'warning')
            
            # Obtener datos procesados desde la base de datos
            processed_data = get_all_processed_data()
            
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
        
        # Importar a la base de datos
        import_summary = import_data_to_db(
            orders_path, 
            trades_path, 
            tickets_path,
            app
        )
        
        # Verificar resultado de la importación
        if import_summary['status'] == 'success':
            flash(f"Datos importados correctamente: {import_summary['orders_imported']} órdenes, {import_summary['trades_imported']} trades", 'success')
        else:
            flash(f"Importación parcial: {import_summary['status']}", 'warning')
        
        # Obtener datos procesados desde la base de datos
        processed_data = get_all_processed_data()
        
        # Copiar archivos a la carpeta 'data' para uso futuro
        import shutil
        shutil.copy(orders_path, DEFAULT_ORDERS_PATH)
        shutil.copy(trades_path, DEFAULT_TRADES_PATH)
        shutil.copy(tickets_path, DEFAULT_TICKETS_PATH)
        
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Muestra el dashboard con resumen de métricas"""
    global processed_data
    
    # Si no hay datos en memoria, intentar cargar desde la base de datos
    if processed_data is None:
        # Obtener fecha predeterminada (últimos 30 días)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Obtener parámetros de fecha desde la URL
        if request.args.get('start_date') and request.args.get('end_date'):
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Usando rango predeterminado.', 'warning')
        
        processed_data = get_all_processed_data(start_date, end_date)
    
    if not processed_data or not processed_data.get('metrics'):
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    metrics = processed_data['metrics']
    
    # Preparar datos para gráficos
    equity_curve_data = json.dumps(processed_data['equity_curve'])
    symbols_data = json.dumps(processed_data['symbol_performance'][:5])  # Top 5 símbolos
    buysell_data = json.dumps(processed_data['buysell_performance'])
    
    # Obtener rango de fechas disponibles
    date_range = get_available_date_range()
    
    return render_template(
        'dashboard.html', 
        metrics=metrics, 
        equity_curve_data=equity_curve_data,
        symbols_data=symbols_data,
        buysell_data=buysell_data,
        processed_data=processed_data,  # Añadir variable para comprobar datos en plantillas
        sidebar_items=AddonRegistry.get_sidebar_items(),  # Añadir explícitamente items de barra lateral
        date_range=date_range
    )

@app.route('/symbols')
def symbols():
    """Análisis por símbolo"""
    global processed_data
    
    # Si no hay datos en memoria, intentar cargar desde la base de datos
    if processed_data is None:
        # Obtener fecha predeterminada (últimos 30 días)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Obtener parámetros de fecha desde la URL
        if request.args.get('start_date') and request.args.get('end_date'):
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Usando rango predeterminado.', 'warning')
        
        # Obtener rendimiento por símbolo desde la base de datos
        symbols_data = get_symbol_performance(start_date, end_date)
        symbols_json = json.dumps(symbols_data)
        
        # Obtener datos procesados completos si no están en memoria
        processed_data = get_all_processed_data(start_date, end_date)
    else:
        symbols_data = processed_data['symbol_performance']
        symbols_json = json.dumps(symbols_data)
    
    if not symbols_data:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    # Obtener rango de fechas disponibles
    date_range = get_available_date_range()
    
    return render_template(
        'symbols.html', 
        symbols=symbols_data, 
        symbols_json=symbols_json,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items(),
        date_range=date_range
    )

@app.route('/time')
def time_analysis():
    """Análisis por hora del día"""
    global processed_data
    
    # Si no hay datos en memoria, intentar cargar desde la base de datos
    if processed_data is None:
        # Obtener fecha predeterminada (últimos 30 días)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Obtener parámetros de fecha desde la URL
        if request.args.get('start_date') and request.args.get('end_date'):
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Usando rango predeterminado.', 'warning')
        
        # Obtener rendimiento por hora desde la base de datos
        time_data = get_time_performance(start_date, end_date)
        time_json = json.dumps(time_data)
        
        # Obtener datos procesados completos si no están en memoria
        processed_data = get_all_processed_data(start_date, end_date)
    else:
        time_data = processed_data['time_performance']
        time_json = json.dumps(time_data)
    
    if not time_data:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    # Encontrar las mejores y peores horas
    if time_data:
        best_hour = max(time_data, key=lambda x: x['totalPL'])
        worst_hour = min(time_data, key=lambda x: x['totalPL'])
        most_active = max(time_data, key=lambda x: x['totalTrades'])
    else:
        best_hour = worst_hour = most_active = None
    
    # Obtener rango de fechas disponibles
    date_range = get_available_date_range()
    
    return render_template(
        'time_analysis.html', 
        time_data=time_data, 
        time_json=time_json,
        best_hour=best_hour,
        worst_hour=worst_hour,
        most_active=most_active,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items(),
        date_range=date_range
    )

@app.route('/buysell')
def buysell():
    """Análisis por tipo (compra/venta)"""
    global processed_data
    
    # Si no hay datos en memoria, intentar cargar desde la base de datos
    if processed_data is None:
        # Obtener fecha predeterminada (últimos 30 días)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Obtener parámetros de fecha desde la URL
        if request.args.get('start_date') and request.args.get('end_date'):
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Usando rango predeterminado.', 'warning')
        
        # Obtener rendimiento por tipo desde la base de datos
        buysell_data = get_buysell_performance(start_date, end_date)
        buysell_json = json.dumps(buysell_data)
        
        # Obtener datos procesados completos si no están en memoria
        processed_data = get_all_processed_data(start_date, end_date)
    else:
        buysell_data = processed_data['buysell_performance']
        buysell_json = json.dumps(buysell_data)
    
    if not buysell_data:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    # Obtener rango de fechas disponibles
    date_range = get_available_date_range()
    
    return render_template(
        'buysell.html', 
        buysell=buysell_data, 
        buysell_json=buysell_json,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items(),
        date_range=date_range
    )


@app.route('/trades')
def trades():
    """Lista detallada de operaciones"""
    global processed_data
    
    # Obtener fecha predeterminada (últimos 30 días)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Obtener parámetros de fecha desde la URL
    if request.args.get('start_date') and request.args.get('end_date'):
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido. Usando rango predeterminado.', 'warning')
    
    # Obtener parámetros de filtrado adicionales
    symbol = request.args.get('symbol')
    
    # Construir lista de símbolos para filtrar
    symbols = [symbol] if symbol else None
    
    # Obtener órdenes procesadas desde la base de datos (limitadas a 1000 para rendimiento)
    processed_orders = get_processed_orders_from_db(start_date, end_date, symbols, limit=1000)
    
    # Ordenar por fecha (más reciente primero)
    sorted_orders = sorted(processed_orders, key=lambda x: x.get('time', ''), reverse=True)
    
    # Obtener lista de símbolos disponibles para el filtro
    available_symbols = get_available_symbols(start_date, end_date)
    
    # Obtener rango de fechas disponibles
    date_range = get_available_date_range()
    
    # Si processed_data no está en memoria, inicializarlo con datos básicos
    if processed_data is None:
        processed_data = get_all_processed_data(start_date, end_date)
    
    return render_template(
        'trades.html', 
        orders=sorted_orders,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items(),
        available_symbols=available_symbols,
        selected_symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        date_range=date_range
    )

@app.route('/manage_addons')
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
    
    # Obtener la variable processed_data para la navegación
    global processed_data
    if processed_data is None:
        # Intentar cargar datos básicos para navegación
        try:
            processed_data = get_all_processed_data()
        except:
            pass  # Ignorar errores, no necesitamos datos completos aquí
    
    return render_template(
        'manage_addons.html',
        addons=registered_addons,
        addon_files=addon_files,
        addon_status=addon_status,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
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
    # Reiniciar el registro (solo datos, no blueprints)
    AddonRegistry._addons = {}
    AddonRegistry._sidebar_items = []
    
    # Cargar nuevamente los addons pero sin registrar blueprints
    try:
        # Crear una copia del registry sin reinicialización de blueprints
        old_initialize = AddonRegistry.initialize
        
        # Temporalmente reemplazar el método initialize para evitar registro de blueprints
        def mock_initialize(app):
            AddonRegistry._app = app
            AddonRegistry._initialized = True
            
            # Añadir la lista de addons al contexto global de las plantillas
            @app.context_processor
            def inject_addons():
                return {
                    'sidebar_items': AddonRegistry.get_sidebar_items(),
                    'addons': AddonRegistry._addons
                }
                
            return True
            
        # Reemplazar temporalmente el método
        AddonRegistry.initialize = mock_initialize
        
        # Cargar addons
        load_addons_from_directory()
        
        # Inicializar (solo actualizará registros internos, no blueprints)
        AddonRegistry.initialize(app)
        
        # Restaurar método original
        AddonRegistry.initialize = old_initialize
        
        flash('Addons recargados con éxito. Es necesario reiniciar la aplicación para activar nuevos addons.', 'warning')
    except Exception as e:
        flash(f'Error al recargar addons: {str(e)}', 'error')
    
    return redirect(url_for('manage_addons'))
    
@app.route('/trading_alerts')
def trading_alerts():
    """Vista principal de alertas de trading"""
    # Cargar variables globales
    global processed_data
    
    # Obtener alertas activas
    active_alerts = get_trading_alerts(active_only=True)
    
    # Si no hay datos procesados, intentar cargarlos
    if processed_data is None:
        processed_data = get_all_processed_data()
    
    # Si hay órdenes, verificar alertas
    triggered_alerts = []
    if processed_data and processed_data.get('processed_orders'):
        # Usar datos de la base de datos para verificar alertas
        triggered_alerts = check_trading_alerts(processed_data['processed_orders'])
    else:
        # Obtener alertas disparadas recientes de la base de datos
        triggered_alerts = get_triggered_alerts()
    
    return render_template(
        'trading_alerts.html',
        active_alerts=active_alerts,
        triggered_alerts=triggered_alerts,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@app.route('/create_alert', methods=['GET', 'POST'])
def create_alert():
    """Vista para crear nuevas alertas"""
    global processed_data
    
    # Si hay una petición POST, procesar el formulario
    if request.method == 'POST':
        # Recoger datos del formulario
        alert_name = request.form.get('name')
        symbols = request.form.getlist('symbol')
        sides = request.form.getlist('side')
        min_quantity = float(request.form.get('min_quantity', 0) or 0)
        min_price = float(request.form.get('min_price', 0) or 0)
        max_price = float(request.form.get('max_price', 0) or float('inf'))
        
        # Construir condiciones
        conditions = {}
        if symbols:
            conditions['symbol'] = symbols
        if sides:
            conditions['side'] = sides
        if min_quantity > 0:
            conditions['min_quantity'] = min_quantity
        if min_price > 0 or max_price < float('inf'):
            conditions['price_range'] = [min_price, max_price]
        
        # Validar datos
        if not alert_name:
            flash('El nombre de la alerta es obligatorio', 'error')
            return redirect(url_for('create_alert'))
        
        if not symbols:
            flash('Debe seleccionar al menos un símbolo', 'error')
            return redirect(url_for('create_alert'))
        
        # Crear alerta
        alert_id = add_trading_alert(
            name=alert_name,
            conditions=conditions,
            description=f"Alerta para {', '.join(symbols)} con condiciones específicas"
        )
        
        if alert_id:
            flash(f'Alerta "{alert_name}" creada exitosamente', 'success')
            return redirect(url_for('trading_alerts'))
        else:
            flash('Error al crear la alerta', 'error')
            return redirect(url_for('create_alert'))
    
    # Petición GET - mostrar formulario
    # Si no hay datos procesados, intentar cargarlos
    if processed_data is None:
        processed_data = get_all_processed_data()
    
    # Obtener lista de símbolos para el formulario
    available_symbols = get_available_symbols()
    
    return render_template(
        'create_alert.html',
        symbols=available_symbols,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@app.route('/disable_alert', methods=['POST'])
def disable_alert():
    """API para desactivar una alerta"""
    data = request.json
    if not data or 'alert_id' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos'})
    
    alert_id = data['alert_id']
    
    # Desactivar alerta
    success = disable_trading_alert(alert_id)
    
    return jsonify({'success': success})
    
@app.route('/debug_routes')
def debug_routes():
    """Muestra todas las rutas registradas para depuración"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'route': str(rule)
        })
    
    # Obtener estadísticas de la base de datos
    db_stats = summarize_database_stats()
    
    # Obtener la variable processed_data para la navegación
    global processed_data
    if processed_data is None:
        try:
            processed_data = get_all_processed_data()
        except:
            pass  # Ignorar errores, no necesitamos datos completos aquí
    
    return render_template(
        'debug_routes.html', 
        routes=sorted(routes, key=lambda x: x['route']),
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items(),
        db_stats=db_stats
    )

@app.route('/api/symbols', methods=['GET'])
def api_symbols():
    """API para obtener símbolos disponibles"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convertir fechas si se proporcionan
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    # Obtener símbolos
    symbols = get_available_symbols(start_date, end_date)
    
    return jsonify({
        'symbols': symbols,
        'count': len(symbols)
    })

@app.route('/api/date_range', methods=['GET'])
def api_date_range():
    """API para obtener el rango de fechas disponible"""
    start_date, end_date = get_available_date_range()
    
    return jsonify({
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
    })

@app.route('/api/filter_data', methods=['POST'])
def api_filter_data():
    """API para filtrar datos según rango de fechas, símbolos, etc."""
    # Obtener parámetros del filtro
    data = request.json or {}
    
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    symbols = data.get('symbols')
    
    # Convertir fechas si se proporcionan
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    # Obtener datos filtrados
    filtered_data = get_all_processed_data(start_date, end_date)
    
    # Aplicar filtro de símbolos si se proporciona
    if symbols and filtered_data and 'processed_orders' in filtered_data:
        filtered_data['processed_orders'] = [
            order for order in filtered_data['processed_orders']
            if order['symb'] in symbols
        ]
    
    # Devolver JSON con datos filtrados
    return jsonify({
        'success': True,
        'data': {
            'metrics': filtered_data.get('metrics'),
            'symbol_performance': filtered_data.get('symbol_performance'),
            'time_performance': filtered_data.get('time_performance'),
            'buysell_performance': filtered_data.get('buysell_performance'),
            'order_count': len(filtered_data.get('processed_orders', [])),
        }
    })
    
if __name__ == '__main__':
    # Cargar los addons
    load_addons_from_directory()
    
    # Inicializar el sistema de addons
    AddonRegistry.initialize(app)
    
    # Intentar cargar datos desde la base de datos
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        processed_data = get_all_processed_data(start_date, end_date)
        app.logger.info(f"Datos cargados desde la base de datos al iniciar: {processed_data is not None}")
    except Exception as e:
        app.logger.error(f"No se pudieron cargar los datos automáticamente: {e}")
    
    # Iniciar la aplicación en modo debug
    app.run(host='0.0.0.0', port=5000, debug=True)