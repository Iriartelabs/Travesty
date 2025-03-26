import json
from flask import Blueprint, render_template, redirect, url_for, flash

from config import Config
from services.cache_manager import load_processed_data
from addon_system import AddonRegistry

analysis_bp = Blueprint('analysis', __name__)

def get_processed_data():
    """Obtener datos procesados"""
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return None
    
    return processed_data

@analysis_bp.route('/symbols')
def symbols():
    """Análisis por símbolo"""
    # Obtener datos procesados
    processed_data = get_processed_data()
    
    if processed_data is None:
        return redirect(url_for('main.index'))
    
    symbols_data = processed_data.get('symbol_performance', [])
    symbols_json = json.dumps(symbols_data)
    
    return render_template(
        'symbols.html', 
        symbols=symbols_data, 
        symbols_json=symbols_json,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@analysis_bp.route('/time')
def time_analysis():
    """Análisis por hora del día"""
    processed_data = get_processed_data()
    
    if processed_data is None:
        return redirect(url_for('main.index'))
    
    time_data = processed_data.get('time_performance', [])
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

@analysis_bp.route('/buysell')
def buysell():
    """Análisis por tipo (compra/venta)"""
    processed_data = get_processed_data()
    
    if processed_data is None:
        return redirect(url_for('main.index'))
    
    buysell_data = processed_data.get('buysell_performance', [])
    buysell_json = json.dumps(buysell_data)
    
    return render_template(
        'buysell.html', 
        buysell=buysell_data, 
        buysell_json=buysell_json,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@analysis_bp.route('/trades')
def trades():
    """Lista detallada de operaciones"""
    processed_data = get_processed_data()
    
    if processed_data is None:
        return redirect(url_for('main.index'))
    
    processed_orders = processed_data.get('processed_orders', [])
    
    # Ordenar por fecha (más reciente primero)
    sorted_orders = sorted(processed_orders, key=lambda x: x.get('time', ''), reverse=True)
    
    return render_template(
        'trades.html', 
        orders=sorted_orders,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )

@analysis_bp.route('/manage-addons')
def manage_addons():
    """Página para gestionar addons"""
    processed_data = get_processed_data()
    
    # Obtener la lista de addons registrados
    registered_addons = AddonRegistry.get_all_addons()
    
    return render_template(
        'manage_addons.html',
        addons=registered_addons,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )
