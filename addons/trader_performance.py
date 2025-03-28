"""
Addon: Trader Performance Analysis
Description: Provides detailed performance breakdown for each trader
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash
import json
from collections import defaultdict

from config import Config
from services.cache_manager import load_processed_data

# Control de registro único
_is_registered = False

def analyze_trader_performance(orders):
    """
    Analyze trading performance broken down by individual traders
    
    Args:
        orders (list): List of processed orders
    
    Returns:
        list: Detailed performance metrics for each trader
    """
    # Initialize data structures
    trader_performance = defaultdict(lambda: {
        'totalTrades': 0,
        'totalPL': 0,
        'winningTrades': 0,
        'losingTrades': 0,
        'avgTradeSize': 0,
        'totalCommission': 0,
        'totalRouteFee': 0
    })
    
    # Process each order
    for order in orders:
        trader = order.get('Trader', 'Unknown')
        
        # Update trader performance metrics
        trader_performance[trader]['totalTrades'] += 1
        trader_performance[trader]['totalPL'] += order.get('pnl', 0)
        trader_performance[trader]['totalCommission'] += order.get('totalCommission', 0)
        trader_performance[trader]['totalRouteFee'] += order.get('totalRouteFee', 0)
        
        # Track winning/losing trades
        if order.get('pnl', 0) > 0:
            trader_performance[trader]['winningTrades'] += 1
        else:
            trader_performance[trader]['losingTrades'] += 1
    
    # Calculate additional metrics
    result = []
    for trader, stats in trader_performance.items():
        # Prevent division by zero
        if stats['totalTrades'] > 0:
            stats['winRate'] = (stats['winningTrades'] / stats['totalTrades']) * 100
            stats['avgPL'] = stats['totalPL'] / stats['totalTrades']
        else:
            stats['winRate'] = 0
            stats['avgPL'] = 0
        
        result.append({
            'trader': trader,
            'totalTrades': stats['totalTrades'],
            'totalPL': round(stats['totalPL'], 2),
            'winningTrades': stats['winningTrades'],
            'losingTrades': stats['losingTrades'],
            'winRate': round(stats['winRate'], 2),
            'avgPL': round(stats['avgPL'], 2),
            'totalCommission': round(stats['totalCommission'], 2),
            'totalRouteFee': round(stats['totalRouteFee'], 2)
        })
    
    # Sort by total P&L in descending order
    return sorted(result, key=lambda x: x['totalPL'], reverse=True)

def trader_performance_view():
    """
    View function for trader performance addon
    
    Returns:
        Rendered HTML template with trader performance data
    """
    # Agregar mensaje de depuración
    print("[DEBUG] Entrando en trader_performance_view()")
    
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
    
    # Analyze trader performance using the obtained data
    trader_data = analyze_trader_performance(processed_orders)
    
    print(f"[DEBUG] Datos de rendimiento por trader: {trader_data}")
    
    trader_json = json.dumps(trader_data)
    
    return render_template(
        'trader_performance.html',
        trader_performance=trader_data,
        trader_json=trader_json,
        processed_data=processed_data
    )

def register_addon():
    """
    Register the trader performance addon in the system
    """
    global _is_registered
    if _is_registered:
        return
        
    AddonRegistry.register('trader_performance', {
        'name': 'Trader Performance',
        'description': 'Detailed performance analysis by individual traders',
        'route': '/trader_performance',
        'view_func': trader_performance_view,
        'template': 'trader_performance.html',
        'icon': 'users',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    _is_registered = True

# Automatically register when imported
if __name__ != '__main__':
    register_addon()
