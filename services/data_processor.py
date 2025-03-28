"""
Módulo para procesar datos de trading
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
from config import Config
from services.cache_manager import save_processed_data

def process_trading_data(file_path):
    """
    Procesa el archivo de trading cargado por el usuario.
    
    Args:
        file_path (str): Ruta al archivo CSV de trades
        
    Returns:
        dict: Datos procesados
    """
    processed_data = {}
    
    try:
        # Leer el archivo CSV
        trades_df = pd.read_csv(file_path)
        
        # Procesar datos para tener una estructura adecuada
        processed_trades = []
        
        # Detectar automáticamente las columnas disponibles
        column_mappings = {
            'time': ['Time', 'time', 'DATE', 'Date', 'date', 'timestamp', 'Timestamp'],
            'symbol': ['Symbol', 'symbol', 'Symb', 'symb', 'SYMBOL', 'ticker', 'Ticker'],
            'quantity': ['Qty', 'qty', 'Quantity', 'quantity', 'Size', 'size', 'QUANTITY'],
            'price': ['Price', 'price', 'PRICE', 'entry', 'Entry', 'EntryPrice'],
            'side': ['Side', 'side', 'B/S', 'Type', 'type', 'TradeType', 'Direction'],
            'pnl': ['PnL', 'pnl', 'P&L', 'Profit', 'profit', 'GainLoss', 'Net']
        }
        
        # Obtener nombres de columnas reales en el CSV
        available_columns = trades_df.columns.tolist()
        mapped_columns = {}
        
        for key, possible_names in column_mappings.items():
            for column_name in possible_names:
                if column_name in available_columns:
                    mapped_columns[key] = column_name
                    break
            
            # Si no se encontró una columna para este atributo, usar un valor predeterminado
            if key not in mapped_columns:
                mapped_columns[key] = None
        
        # Procesar cada fila utilizando los nombres de columnas mapeados
        for _, row in trades_df.iterrows():
            trade = {}
            
            # Asignar valores basados en las columnas mapeadas
            for key, column_name in mapped_columns.items():
                if column_name is not None:
                    # Para datos numéricos, asegurar que sean floats
                    if key in ['quantity', 'price', 'pnl']:
                        try:
                            trade[key] = float(row[column_name])
                        except (ValueError, TypeError):
                            trade[key] = 0.0
                    else:
                        trade[key] = str(row[column_name]) if pd.notna(row[column_name]) else ''
                else:
                    # Valores predeterminados para columnas no encontradas
                    if key in ['quantity', 'price', 'pnl']:
                        trade[key] = 0.0
                    else:
                        trade[key] = ''
            
            processed_trades.append(trade)
        
        # Calcular métricas básicas
        metrics = {
            'total_trades': len(processed_trades),
            'total_pnl': sum(trade.get('pnl', 0) for trade in processed_trades),
            'winning_trades': sum(1 for trade in processed_trades if trade.get('pnl', 0) > 0),
            'losing_trades': sum(1 for trade in processed_trades if trade.get('pnl', 0) < 0)
        }
        
        # Calcular métricas adicionales
        if metrics['total_trades'] > 0:
            metrics['win_rate'] = (metrics['winning_trades'] / metrics['total_trades']) * 100
            
            # Calcular profit factor si hay operaciones perdedoras
            total_gains = sum(trade.get('pnl', 0) for trade in processed_trades if trade.get('pnl', 0) > 0)
            total_losses = abs(sum(trade.get('pnl', 0) for trade in processed_trades if trade.get('pnl', 0) < 0))
            
            if total_losses > 0:
                metrics['profit_factor'] = total_gains / total_losses
            else:
                metrics['profit_factor'] = float('inf') if total_gains > 0 else 0
                
            # Calcular promedios
            if metrics['winning_trades'] > 0:
                metrics['avg_win'] = total_gains / metrics['winning_trades']
            else:
                metrics['avg_win'] = 0
                
            if metrics['losing_trades'] > 0:
                metrics['avg_loss'] = total_losses / metrics['losing_trades']
            else:
                metrics['avg_loss'] = 0
        else:
            metrics['win_rate'] = 0
            metrics['profit_factor'] = 0
            metrics['avg_win'] = 0
            metrics['avg_loss'] = 0
        
        # Construir datos procesados
        processed_data = {
            'processed_trades': processed_trades,
            'metrics': metrics,
            'file_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Guardar en caché si está habilitado
        if Config.CACHE_ENABLED:
            save_processed_data(processed_data, Config.DATA_CACHE_PATH)
            
        return processed_data
        
    except Exception as e:
        # En caso de error, devolver datos vacíos
        print(f"Error al procesar datos: {str(e)}")
        return {
            'processed_trades': [],
            'metrics': {},
            'error': str(e)
        }