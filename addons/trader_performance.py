"""
Addon: Trader Performance Analysis
Description: Provides detailed performance breakdown for each trader
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash
import json
from collections import defaultdict

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
    from app import processed_data
    
    if processed_data is None:
        flash('No data available. Please upload files first.', 'error')
        return redirect(url_for('index'))
    
    # Analyze trader performance
    trader_data = analyze_trader_performance(processed_data['processed_orders'])
    trader_json = json.dumps(trader_data)
    
    return render_template(
        'trader_performance.html',
        trader_performance=trader_data,
        trader_json=trader_json
    )

def register_addon():
    """
    Register the trader performance addon in the system
    """
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

# Automatically register when imported
if __name__ != '__main__':
    register_addon()
