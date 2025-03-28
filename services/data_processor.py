import pandas as pd
import numpy as np
from datetime import datetime

def safe_float(value):
    """Convierte un valor a float de forma segura"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def process_trading_data(orders_path, trades_path, tickets_path):
    """Procesa los datos de trading a partir de los archivos CSV"""
    try:
        # Cargar los archivos CSV
        orders_df = pd.read_csv(orders_path)
        trades_df = pd.read_csv(trades_path)
        tickets_df = pd.read_csv(tickets_path) if not tickets_path.endswith('Tickets.csv') else pd.DataFrame()
        
        # Convertir columnas numéricas
        numeric_columns = {
            'orders': ['qty', 'lvsqty', 'price', 'stopprice', 'trailprice'],
            'trades': ['qty', 'price'],
            'tickets': ['qty', 'price', 'commission', 'RouteFee']
        }
        
        for col in numeric_columns['orders']:
            if col in orders_df.columns:
                orders_df[col] = orders_df[col].apply(safe_float)
        
        for col in numeric_columns['trades']:
            if col in trades_df.columns:
                trades_df[col] = trades_df[col].apply(safe_float)
        
        if not tickets_df.empty:
            for col in numeric_columns['tickets']:
                if col in tickets_df.columns:
                    tickets_df[col] = tickets_df[col].apply(safe_float)
        
        # Procesar y relacionar datos
        processed_orders = _process_orders(orders_df, trades_df, tickets_df)
        
        # Calcular métricas
        metrics = _calculate_metrics(processed_orders)
        
        # Análisis por símbolo
        symbol_performance = _analyze_by_symbol(processed_orders)
        
        # Análisis por hora del día
        time_performance = _analyze_by_time_of_day(processed_orders)
        
        # Análisis por tipo (compra/venta)
        buysell_performance = _analyze_by_buysell(processed_orders)
        
        # Crear curva de equidad
        equity_curve = _create_equity_curve(processed_orders)
        
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
        return _get_empty_result()

def _get_empty_result():
    """Devuelve una estructura vacía de resultados"""
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

def _process_orders(orders_df, trades_df, tickets_df):
    """Relaciona órdenes con trades y tickets"""
    processed_orders = []
    
    # Convertir DataFrames a diccionarios para facilitar búsquedas
    trades_by_order = trades_df.groupby('OrderID')
    tickets_dict = {row['TradeID']: row for _, row in tickets_df.iterrows()} if not tickets_df.empty else {}
    
    for _, order in orders_df.iterrows():
        order_id = order['OrderID']
        order_trades = []
        
        # Buscar trades para esta orden
        if order_id in trades_by_order.groups:
            order_trades_df = trades_by_order.get_group(order_id)
            
            for _, trade in order_trades_df.iterrows():
                trade_dict = trade.to_dict()
                trade_id = trade['TradeID']
                
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
        total_qty = sum(safe_float(t['qty']) for t in order_trades) if order_trades else 0
        
        # Calcular precio promedio ponderado
        if total_qty > 0:
            avg_price = sum(safe_float(t['qty']) * safe_float(t['price']) for t in order_trades) / total_qty
        else:
            avg_price = 0
        
        total_commission = sum(safe_float(t['commission']) for t in order_trades)
        total_route_fee = sum(safe_float(t['routeFee']) for t in order_trades)
        
        # Calcular P&L
        pnl = 0
        order_price = safe_float(order['price'])
        
        if order['B/S'] == 'B':  # Compra
            pnl = (order_price - avg_price) * total_qty if total_qty > 0 else 0
        else:  # Venta
            pnl = (avg_price - order_price) * total_qty if total_qty > 0 else 0
        
        # Restar comisiones y fees
        pnl = pnl - total_commission - total_route_fee
        
        # Extraer la hora de la operación
        time_str = order['time']
        hour = 0
        date = ""
        
        try:
            dt = datetime.strptime(time_str, '%m/%d/%y %H:%M:%S')
            hour = dt.hour
            date = dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        
        # Crear objeto de orden procesada
        processed_order = order.to_dict()
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

def _calculate_metrics(orders):
    """Calcula métricas a partir de las órdenes procesadas"""
    if not orders:
        return _get_empty_result()['metrics']
    
    # Identificar operaciones ganadoras y perdedoras
    winning_orders = [o for o in orders if o['pnl'] > 0]
    losing_orders = [o for o in orders if o['pnl'] <= 0]
    
    # Calcular métricas básicas
    total_trades = len(orders)
    winning_trades = len(winning_orders)
    losing_trades = len(losing_orders)
    
    total_pl = sum(o['pnl'] for o in orders)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Calcular ganancias y pérdidas totales
    total_gain = sum(o['pnl'] for o in winning_orders) if winning_orders else 0
    total_loss = abs(sum(o['pnl'] for o in losing_orders)) if losing_orders else 0
    
    # Profit factor
    profit_factor = (total_gain / total_loss) if total_loss > 0 else total_gain
    
    # Promedios
    avg_win = (total_gain / winning_trades) if winning_trades > 0 else 0
    avg_loss = (total_loss / losing_trades) if losing_trades > 0 else 0
    
    # Calcular drawdown
    sorted_orders = sorted(orders, key=lambda x: x.get('time', ''))
    max_drawdown = 0
    peak = 0
    running_pl = 0
    
    for order in sorted_orders:
        running_pl += order['pnl']
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

def _analyze_by_symbol(orders):
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
        
        symbols[symbol]['totalPL'] += order['pnl']
        symbols[symbol]['totalTrades'] += 1
        if order['pnl'] > 0:
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

def _analyze_by_time_of_day(orders):
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
        
        hours[hour]['totalPL'] += order['pnl']
        hours[hour]['totalTrades'] += 1
        if order['pnl'] > 0:
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

def _analyze_by_buysell(orders):
    """Analiza rendimiento por tipo (compra/venta)"""
    buys = [o for o in orders if o.get('B/S') == 'B']
    sells = [o for o in orders if o.get('B/S') == 'S']
    
    # Estadísticas de compras
    buy_pl = sum(o['pnl'] for o in buys)
    buy_count = len(buys)
    buy_winners = len([o for o in buys if o['pnl'] > 0])
    buy_win_rate = (buy_winners / buy_count * 100) if buy_count > 0 else 0
    
    # Estadísticas de ventas
    sell_pl = sum(o['pnl'] for o in sells)
    sell_count = len(sells)
    sell_winners = len([o for o in sells if o['pnl'] > 0])
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

def _create_equity_curve(orders):
    """Crea la curva de equidad"""
    # Ordenar por tiempo
    sorted_orders = sorted(orders, key=lambda x: x.get('time', ''))
    
    equity_curve = []
    running_pl = 0
    
    for i, order in enumerate(sorted_orders):
        running_pl += order['pnl']
        
        equity_curve.append({
            'tradeNumber': i + 1,
            'time': order.get('time', ''),
            'date': order.get('date', ''),
            'symbol': order.get('symb', ''),
            'pnl': order['pnl'],
            'equity': running_pl
        })
    
    return equity_curve
