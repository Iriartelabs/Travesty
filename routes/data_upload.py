import os
import shutil
from flask import Blueprint, request, redirect, url_for, flash, current_app

from config import Config
from services.data_processor import process_trading_data
from services.cache_manager import save_processed_data
from services.file_handler import save_uploaded_file, validate_csv_files, copy_file

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_files():
    """Procesa archivos subidos por el usuario"""
    # Verificar si se usan archivos predeterminados
    if 'use_default' in request.form:
        # Rutas de archivos predeterminados
        default_paths = [
            Config.DEFAULT_ORDERS_PATH, 
            Config.DEFAULT_TRADES_PATH, 
            Config.DEFAULT_TICKETS_PATH
        ]
        
        # Validar existencia de archivos predeterminados
        if not validate_csv_files(default_paths):
            flash('No se encontraron archivos predeterminados válidos', 'error')
            return redirect(url_for('main.index'))
        
        try:
            # Procesar archivos predeterminados
            processed_data = process_trading_data(*default_paths)
            
            # Guardar en caché
            save_processed_data(processed_data, Config.DATA_CACHE_PATH)
            
            return redirect(url_for('main.dashboard'))
        
        except Exception as e:
            flash(f'Error al procesar archivos predeterminados: {str(e)}', 'error')
            return redirect(url_for('main.index'))
    
    # Manejar subida de archivos nuevos
    required_files = ['orders', 'trades', 'tickets']
    
    # Verificar que se hayan enviado todos los archivos
    for file_key in required_files:
        if file_key not in request.files:
            flash('Debes subir los tres archivos CSV', 'error')
            return redirect(url_for('main.index'))
    
    # Obtener archivos
    uploaded_files = [request.files[key] for key in required_files]
    
    # Verificar que todos los archivos tengan contenido
    if any(file.filename == '' for file in uploaded_files):
        flash('Todos los archivos deben tener contenido', 'error')
        return redirect(url_for('main.index'))
    
    # Rutas temporales para guardar archivos
    temp_paths = [
        os.path.join(current_app.config['UPLOAD_FOLDER'], f'{key}.csv') 
        for key in required_files
    ]
    
    # Rutas predeterminadas para copiar los archivos
    default_paths = [
        Config.DEFAULT_ORDERS_PATH, 
        Config.DEFAULT_TRADES_PATH, 
        Config.DEFAULT_TICKETS_PATH
    ]
    
    try:
        # Guardar archivos temporalmente
        for file, temp_path in zip(uploaded_files, temp_paths):
            save_uploaded_file(file, temp_path)
        
        # Validar archivos CSV
        if not validate_csv_files(temp_paths):
            # Limpiar archivos temporales
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            flash('Los archivos CSV no son válidos', 'error')
            return redirect(url_for('main.index'))
        
        # Procesar los datos
        processed_data = process_trading_data(*temp_paths)
        
        # Guardar en caché
        save_processed_data(processed_data, Config.DATA_CACHE_PATH)
        
        # Copiar archivos a la carpeta 'data' para uso futuro
        for temp_path, default_path in zip(temp_paths, default_paths):
            copy_file(temp_path, default_path)
        
        return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        # Limpiar archivos temporales en caso de error
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        flash(f'Error al procesar archivos: {str(e)}', 'error')
        return redirect(url_for('main.index'))