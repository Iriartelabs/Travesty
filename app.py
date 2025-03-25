from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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

# Importar desde utils
from utils.data_processor import process_trading_data

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
        buysell_data=buysell_data,
        processed_data=processed_data,  # Añadir variable para comprobar datos en plantillas
        sidebar_items=AddonRegistry.get_sidebar_items()  # Añadir explícitamente items de barra lateral
    )

@app.route('/symbols')
def symbols():
    """Análisis por símbolo"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    symbols_data = processed_data['symbol_performance']
    symbols_json = json.dumps(symbols_data)
    
    return render_template(
        'symbols.html', 
        symbols=symbols_data, 
        symbols_json=symbols_json,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

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
        most_active=most_active,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@app.route('/buysell')
def buysell():
    """Análisis por tipo (compra/venta)"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    buysell_data = processed_data['buysell_performance']
    buysell_json = json.dumps(buysell_data)
    
    return render_template(
        'buysell.html', 
        buysell=buysell_data, 
        buysell_json=buysell_json,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@app.route('/trades')
def trades():
    """Lista detallada de operaciones"""
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('index'))
    
    processed_orders = processed_data['processed_orders']
    
    # Ordenar por fecha (más reciente primero)
    sorted_orders = sorted(processed_orders, key=lambda x: x.get('time', ''), reverse=True)
    
    return render_template(
        'trades.html', 
        orders=sorted_orders,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
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

@app.route('/disable_alert', methods=['POST'])
def disable_alert():
    """API para desactivar una alerta"""
    data = request.json
    if not data or 'alert_id' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos'})
    
    alert_id = data['alert_id']
    
    # Buscar el addon de alertas
    from importlib import import_module
    try:
        # Intentar obtener el addon de alertas
        addon_module = import_module('addons.trading_alert_addon')
        if hasattr(addon_module, 'alert_system') and hasattr(addon_module.alert_system, 'disable_alert'):
            success = addon_module.alert_system.disable_alert(alert_id)
            return jsonify({'success': success})
    except (ImportError, AttributeError) as e:
        print(f"Error al acceder al sistema de alertas: {e}")
    
    return jsonify({'success': False, 'message': 'Sistema de alertas no disponible'})

@app.route('/create_alert', methods=['GET', 'POST'])
def create_alert():
    """Vista para crear nuevas alertas"""
    # Importar dinámicamente el módulo del addon de alertas
    try:
        from addons.trading_alert_addon import create_alert_view
        return create_alert_view()
    except ImportError:
        flash('El addon de alertas no está disponible', 'error')
        return redirect(url_for('index'))
        
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
    
    return render_template(
        'debug_routes.html', 
        routes=sorted(routes, key=lambda x: x['route']),
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

if __name__ == '__main__':
    # Cargar los addons
    load_addons_from_directory()
    
    # Inicializar el sistema de addons
    AddonRegistry.initialize(app)
    
    # Comprobar si hay archivos predeterminados y cargarlos
    if (os.path.exists(DEFAULT_ORDERS_PATH) and 
        os.path.exists(DEFAULT_TRADES_PATH) and 
        os.path.exists(DEFAULT_TICKETS_PATH)):
        
        try:
            processed_data = process_trading_data(
                DEFAULT_ORDERS_PATH, 
                DEFAULT_TRADES_PATH, 
                DEFAULT_TICKETS_PATH
            )
            print(f"[INFO] Datos cargados automáticamente al iniciar: {processed_data is not None}")
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar los datos automáticamente: {e}")
    
    # Iniciar la aplicación en modo debug
    app.run(host='0.0.0.0', port=5000, debug=True)
