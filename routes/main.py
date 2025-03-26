import os
import json
from flask import Blueprint, render_template, redirect, url_for, flash

from config import Config
from addon_system import AddonRegistry
from services.cache_manager import load_processed_data

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal con formulario para cargar archivos"""
    default_files = [
        Config.DEFAULT_ORDERS_PATH, 
        Config.DEFAULT_TRADES_PATH, 
        Config.DEFAULT_TICKETS_PATH
    ]
    
    # Usar os.path.exists para verificar archivos
    has_default_files = all(os.path.exists(path) for path in default_files)
    
    return render_template('index.html', has_default_files=has_default_files)

@main_bp.route('/dashboard')
def dashboard():
    """Muestra el dashboard con resumen de métricas"""
    # Intentar cargar desde caché
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    metrics = processed_data.get('metrics', {})
    
    # Preparar datos para gráficos
    equity_curve_data = json.dumps(processed_data.get('equity_curve', []))
    symbols_data = json.dumps(processed_data.get('symbol_performance', [])[:5])  # Top 5 símbolos
    buysell_data = json.dumps(processed_data.get('buysell_performance', []))
    
    return render_template(
        'dashboard.html', 
        metrics=metrics, 
        equity_curve_data=equity_curve_data,
        symbols_data=symbols_data,
        buysell_data=buysell_data,
        processed_data=processed_data,
        sidebar_items=AddonRegistry.get_sidebar_items()
    )
