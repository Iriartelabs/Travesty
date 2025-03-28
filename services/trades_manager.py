"""
Módulo para gestionar archivos de trading con organización temporal
"""
import os
import json
import shutil
import pandas as pd
from datetime import datetime
from config import Config
from services.cache_manager import save_processed_data
from services.data_processor import process_trading_data

# Ruta del índice de archivos
INDEX_FILE = os.path.join(Config.DATA_FOLDER, 'trades', 'index.json')

def ensure_directories():
    """Asegura que existan los directorios necesarios"""
    trades_dir = os.path.join(Config.DATA_FOLDER, 'trades')
    os.makedirs(trades_dir, exist_ok=True)
    
    # Crear archivo de índice si no existe
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def detect_date_from_csv(file_path):
    """
    Intenta detectar la fecha del archivo CSV basándose en su contenido
    
    Args:
        file_path (str): Ruta al archivo CSV
        
    Returns:
        tuple: (año, mes, día) o None si no se puede detectar
    """
    try:
        # Leer las primeras filas del archivo
        df = pd.read_csv(file_path, nrows=5)
        
        # Buscar en la columna de tiempo
        if 'time' in df.columns:
            # Intentar varios formatos comunes
            for row in df['time']:
                if not pd.isna(row):
                    for fmt in ['%m/%d/%y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S']:
                        try:
                            dt = datetime.strptime(str(row), fmt)
                            return (dt.year, dt.month, dt.day)
                        except ValueError:
                            continue
        
        # Si no se pudo detectar, usar la fecha actual
        now = datetime.now()
        return (now.year, now.month, now.day)
    
    except Exception as e:
        print(f"Error al detectar fecha del CSV: {e}")
        # Si falla, usar la fecha actual
        now = datetime.now()
        return (now.year, now.month, now.day)

def save_trade_file(file_path, year=None, month=None, day=None):
    """
    Guarda un archivo de trading en la estructura organizada
    
    Args:
        file_path (str): Ruta al archivo CSV temporal
        year (int, optional): Año de los datos
        month (int, optional): Mes de los datos
        day (int, optional): Día de los datos
        
    Returns:
        dict: Información del archivo guardado
    """
    ensure_directories()
    
    # Si no se especifican fecha, intentar detectarla
    if not all([year, month, day]):
        year, month, day = detect_date_from_csv(file_path)
    
    # Crear directorio para la fecha
    date_dir = os.path.join(Config.DATA_FOLDER, 'trades', str(year), f"{month:02d}", f"{day:02d}")
    os.makedirs(date_dir, exist_ok=True)
    
    # Ruta de destino
    dest_path = os.path.join(date_dir, 'trades.csv')
    
    # Copiar archivo
    shutil.copy2(file_path, dest_path)
    
    # Obtener estadísticas básicas
    df = pd.read_csv(dest_path)
    stats = {
        'total_rows': len(df),
        'symbols': df['symb'].nunique() if 'symb' in df.columns else 0,
        'first_time': df['time'].min() if 'time' in df.columns else None,
        'last_time': df['time'].max() if 'time' in df.columns else None
    }
    
    # Crear entrada para el índice
    file_info = {
        'year': year,
        'month': month,
        'day': day,
        'date_str': f"{year}-{month:02d}-{day:02d}",
        'path': dest_path,
        'import_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stats': stats
    }
    
    # Actualizar índice
    update_index(file_info)
    
    return file_info

def update_index(file_info):
    """
    Actualiza el archivo de índice con la nueva información
    
    Args:
        file_info (dict): Información del archivo
    """
    try:
        # Leer índice actual
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Verificar si ya existe la entrada para esta fecha
        date_key = file_info['date_str']
        existing_idx = None
        
        for i, entry in enumerate(index):
            if entry.get('date_str') == date_key:
                existing_idx = i
                break
        
        if existing_idx is not None:
            # Actualizar entrada existente
            index[existing_idx] = file_info
        else:
            # Agregar nueva entrada
            index.append(file_info)
        
        # Guardar índice actualizado
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
            
    except Exception as e:
        print(f"Error al actualizar índice: {e}")

def get_available_dates():
    """
    Obtiene las fechas disponibles en el índice
    
    Returns:
        list: Lista de diccionarios con información de archivos disponibles
    """
    ensure_directories()
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Ordenar por fecha (más reciente primero)
        index.sort(key=lambda x: x.get('date_str', ''), reverse=True)
        
        return index
    
    except Exception as e:
        print(f"Error al obtener fechas disponibles: {e}")
        return []

def load_trades_by_date(year, month, day):
    """
    Carga los datos de trading para una fecha específica
    
    Args:
        year (int): Año
        month (int): Mes
        day (int): Día
        
    Returns:
        dict: Datos procesados o None si no existe
    """
    file_path = os.path.join(Config.DATA_FOLDER, 'trades', str(year), f"{month:02d}", f"{day:02d}", 'trades.csv')
    
    if not os.path.exists(file_path):
        return None
    
    try:
        # Procesar datos
        processed_data = process_trading_data(file_path)
        
        # Añadir información de fecha
        processed_data['date_info'] = {
            'year': year,
            'month': month,
            'day': day,
            'date_str': f"{year}-{month:02d}-{day:02d}"
        }
        
        return processed_data
    
    except Exception as e:
        print(f"Error al cargar datos por fecha: {e}")
        return None

def load_trades_by_range(start_date, end_date):
    """
    Carga datos de trading para un rango de fechas
    
    Args:
        start_date (str): Fecha de inicio (formato: 'YYYY-MM-DD')
        end_date (str): Fecha de fin (formato: 'YYYY-MM-DD')
        
    Returns:
        dict: Datos procesados consolidados
    """
    # TODO: Implementar consolidación de datos por rango
    # Esta será parte de la segunda fase
    pass