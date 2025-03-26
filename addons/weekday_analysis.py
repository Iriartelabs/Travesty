"""
Addon: Análisis por Día de la Semana
Descripción: Analiza el rendimiento de trading por día de la semana
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash
import json
from datetime import datetime

from config import Config
from services.cache_manager import load_processed_data

def analyze_by_weekday(orders):
    """Analiza rendimiento por día de la semana"""
    print("[DEBUG] Comenzando análisis por día de la semana")
    print(f"[DEBUG] Número de órdenes: {len(orders)}")
    
    weekdays = {}
    
    for order in orders:
        time_str = order.get('time', '')
        if not time_str:
            continue
            
        try:
            # Probamos diferentes formatos de fecha
            try:
                dt = datetime.strptime(time_str, '%m/%d/%y %H:%M:%S')
            except ValueError:
                try:
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"[DEBUG] No se pudo parsear la fecha: {time_str}")
                    continue
            
            weekday = dt.weekday()  # 0 = Lunes, 6 = Domingo
            weekday_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][weekday]
            
            if weekday_name not in weekdays:
                weekdays[weekday_name] = {
                    'totalPL': 0,
                    'totalTrades': 0,
                    'winningTrades': 0,
                    'weekday': weekday  # Guardar número para ordenar
                }
            
            weekdays[weekday_name]['totalPL'] += order.get('pnl', 0)
            weekdays[weekday_name]['totalTrades'] += 1
            if order.get('pnl', 0) > 0:
                weekdays[weekday_name]['winningTrades'] += 1
        except Exception as e:
            print(f"[DEBUG] Error procesando fecha {time_str}: {e}")
            continue
    
    # Convertir a lista
    weekday_stats = []
    for name, stats in weekdays.items():
        win_rate = (stats['winningTrades'] / stats['totalTrades'] * 100) if stats['totalTrades'] > 0 else 0
        avg_pl = stats['totalPL'] / stats['totalTrades'] if stats['totalTrades'] > 0 else 0
        
        weekday_stats.append({
            'weekday': name,
            'weekdayNum': stats['weekday'],
            'totalPL': stats['totalPL'],
            'totalTrades': stats['totalTrades'],
            'winningTrades': stats['winningTrades'],
            'winRate': win_rate,
            'avgPL': avg_pl
        })
    
    # Ordenar por día de la semana
    weekday_stats = sorted(weekday_stats, key=lambda x: x['weekdayNum'])
    
    print("[DEBUG] Estadísticas de días de la semana:")
    for stat in weekday_stats:
        print(f"[DEBUG] {stat}")
    
    return weekday_stats

def weekday_analysis_view():
    """Vista para el addon de análisis por día de la semana"""
    print("[DEBUG] Entrando en weekday_analysis_view()")
    
    # Obtener datos procesados usando load_processed_data
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    print(f"[DEBUG] Processed data: {processed_data is not None}")
    
    if processed_data is None:
        print("[DEBUG] No hay datos procesados")
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener órdenes procesadas
    processed_orders = processed_data.get('processed_orders', [])
    
    print(f"[DEBUG] Número de órdenes procesadas: {len(processed_orders)}")
    
    # Realizar el análisis con los datos obtenidos
    weekday_data = analyze_by_weekday(processed_orders)
    
    print(f"[DEBUG] Datos de días de la semana: {weekday_data}")
    
    # Convertir a JSON para usar en gráficos
    weekday_json = json.dumps(weekday_data)
    
    # Encontrar el mejor y peor día
    if weekday_data:
        best_day = max(weekday_data, key=lambda x: x['totalPL'])
        worst_day = min(weekday_data, key=lambda x: x['totalPL'])
        most_active_day = max(weekday_data, key=lambda x: x['totalTrades'])
    else:
        best_day = worst_day = most_active_day = None
    
    print(f"[DEBUG] Mejor día: {best_day}")
    print(f"[DEBUG] Peor día: {worst_day}")
    print(f"[DEBUG] Día más activo: {most_active_day}")
    
    # Renderizar la plantilla
    return render_template(
        'weekday_analysis.html',
        weekday_data=weekday_data,
        weekday_json=weekday_json,
        best_day=best_day,
        worst_day=worst_day,
        most_active_day=most_active_day,
        processed_data=processed_data
    )

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('weekday_analysis', {
        'name': 'Análisis por Día',
        'description': 'Analiza el rendimiento de trading por día de la semana',
        'route': '/weekday',
        'view_func': weekday_analysis_view,
        'template': 'weekday_analysis.html',
        'icon': 'calendar-week',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
