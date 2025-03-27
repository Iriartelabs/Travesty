import os
import shutil
import pandas as pd
from flask import Blueprint, request, redirect, url_for, flash, current_app

from config import Config
from services.data_processor import process_trading_data
from services.cache_manager import save_processed_data, load_processed_data
from services.file_handler import save_uploaded_file, validate_trades_csv, copy_file

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_files():
    """Procesa archivos subidos por el usuario"""
    # Verificar si se usan archivos predeterminados
    if 'use_default' in request.form:
        # Ruta de archivo predeterminado
        default_trades_path = Config.DEFAULT_TRADES_PATH
        
        # Validar existencia del archivo predeterminado
        if not validate_trades_csv(default_trades_path):
            flash('No se encontró un archivo Trades.csv válido', 'error')
            return redirect(url_for('main.index'))
        
        try:
            # Procesar archivo predeterminado
            processed_data = process_trading_data(trades_path=default_trades_path)
            
            # Guardar en caché
            save_processed_data(processed_data, Config.DATA_CACHE_PATH)
            
            return redirect(url_for('main.dashboard'))
        
        except Exception as e:
            flash(f'Error al procesar archivo predeterminado: {str(e)}', 'error')
            return redirect(url_for('main.index'))
    
    # Manejar subida de archivo nuevo
    if 'trades' not in request.files:
        flash('Debes subir el archivo Trades.csv', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener archivo
    trades_file = request.files['trades']
    
    # Verificar que el archivo tenga contenido
    if trades_file.filename == '':
        flash('El archivo debe tener contenido', 'error')
        return redirect(url_for('main.index'))
    
    # Ruta temporal para guardar archivo
    temp_trades_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'trades_new.csv')
    
    # Ruta predeterminada para copiar el archivo
    default_trades_path = Config.DEFAULT_TRADES_PATH
    
    try:
        # Guardar archivo temporalmente
        save_uploaded_file(trades_file, temp_trades_path)
        
        # Validar archivo CSV
        if not validate_trades_csv(temp_trades_path):
            # Limpiar archivo temporal
            if os.path.exists(temp_trades_path):
                os.remove(temp_trades_path)
            
            flash('El archivo Trades.csv no es válido', 'error')
            return redirect(url_for('main.index'))
        
        # Verificar si se debe fusionar con datos existentes
        merge_with_existing = 'merge' in request.form and request.form['merge'] == 'on'
        
        if merge_with_existing and os.path.exists(default_trades_path):
            # Fusionar con archivo existente
            merged_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'trades_merged.csv')
            
            # Fusionar los archivos
            success = merge_trades_files(default_trades_path, temp_trades_path, merged_path)
            
            if success:
                # Procesar los datos fusionados
                processed_data = process_trading_data(trades_path=merged_path)
                
                # Guardar en caché
                save_processed_data(processed_data, Config.DATA_CACHE_PATH)
                
                # Copiar archivo fusionado a la carpeta 'data' para uso futuro
                copy_file(merged_path, default_trades_path)
                
                # Mostrar mensaje de éxito
                flash('Datos fusionados correctamente', 'success')
            else:
                flash('Error al fusionar archivos', 'error')
                return redirect(url_for('main.index'))
        else:
            # Procesar los nuevos datos sin fusionar
            processed_data = process_trading_data(trades_path=temp_trades_path)
            
            # Guardar en caché
            save_processed_data(processed_data, Config.DATA_CACHE_PATH)
            
            # Copiar archivo a la carpeta 'data' para uso futuro
            copy_file(temp_trades_path, default_trades_path)
        
        # Limpiar archivos temporales
        for temp_file in [temp_trades_path, os.path.join(current_app.config['UPLOAD_FOLDER'], 'trades_merged.csv')]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        # Limpiar archivos temporales en caso de error
        if os.path.exists(temp_trades_path):
            os.remove(temp_trades_path)
        
        flash(f'Error al procesar archivo: {str(e)}', 'error')
        return redirect(url_for('main.index'))

def merge_trades_files(original_path, new_path, output_path):
    """
    Fusiona dos archivos CSV de trades
    
    Args:
        original_path (str): Ruta del archivo original
        new_path (str): Ruta del nuevo archivo a fusionar
        output_path (str): Ruta donde guardar el archivo fusionado
    
    Returns:
        bool: True si la fusión fue exitosa, False en caso contrario
    """
    try:
        # Cargar los archivos CSV
        original_df = pd.read_csv(original_path)
        new_df = pd.read_csv(new_path)
        
        # Verificar que ambos archivos tienen la misma estructura
        if list(original_df.columns) != list(new_df.columns):
            print("Error: Los archivos tienen diferentes columnas")
            return False
        
        # Ajustar los IDs en el nuevo DataFrame para evitar conflictos
        max_trade_id = original_df['TradeID'].max()
        max_order_id = original_df['OrderID'].max()
        
        new_df['TradeID'] = new_df['TradeID'] + max_trade_id
        new_df['OrderID'] = new_df['OrderID'] + max_order_id
        
        # Concatenar los DataFrames
        combined_df = pd.concat([original_df, new_df], ignore_index=True)
        
        # Guardar el resultado
        combined_df.to_csv(output_path, index=False)
        
        return True
    except Exception as e:
        print(f"Error al fusionar archivos: {e}")
        return False