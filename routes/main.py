from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
import os
from datetime import datetime
from services.cache_manager import load_processed_data
from services.data_processor import process_trading_data
from services.file_handler import save_uploaded_file, validate_csv_files, copy_file
from services.trades_manager import save_trade_file, get_available_dates, load_trades_by_date
from config import Config
from addon_system import AddonRegistry

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
def index():
    """Página principal con dashboard"""
    # Cargar datos procesados desde caché
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    # Obtener información de addons disponibles
    sidebar_items = AddonRegistry.get_sidebar_items()
    
    return render_template('index.html',
                          processed_data=processed_data,
                          sidebar_items=sidebar_items)

@main_bp.route('/upload')
def upload():
    """Página de carga de archivos"""
    # Verificar si existe archivo predeterminado
    has_default_file = os.path.exists(Config.DEFAULT_TRADES_PATH)
    
    # Obtener archivos disponibles
    available_dates = get_available_dates()
    
    return render_template('upload.html',
                          has_default_file=has_default_file,
                          available_dates=available_dates,
                          config=Config)

@main_bp.route('/upload_file', methods=['POST'])
def upload_file():
    """Procesa archivo subido por el usuario"""
    # Manejar subida de archivo nuevo
    if 'trades' not in request.files:
        flash('Debes subir un archivo CSV', 'error')
        return redirect(url_for('main.upload'))
    
    # Obtener archivo
    file = request.files['trades']
    
    # Verificar que el archivo tenga contenido
    if file.filename == '':
        flash('El archivo debe tener contenido', 'error')
        return redirect(url_for('main.upload'))
    
    # Ruta temporal para guardar archivo
    temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_trades.csv')
    
    try:
        # Guardar archivo temporalmente
        save_uploaded_file(file, temp_path)
        
        # Validar archivo CSV
        if not validate_csv_files([temp_path]):
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            flash('El archivo CSV no es válido', 'error')
            return redirect(url_for('main.upload'))
        
        # Obtener fecha del formulario si está disponible
        year = month = day = None
        if 'trade_date' in request.form and request.form['trade_date']:
            try:
                trade_date = datetime.strptime(request.form['trade_date'], '%Y-%m-%d')
                year = trade_date.year
                month = trade_date.month
                day = trade_date.day
            except ValueError:
                pass  # Si hay error en el formato, se detectará del CSV
        
        # Guardar archivo en la estructura organizada
        file_info = save_trade_file(temp_path, year, month, day)
        
        # Procesar los datos para mostrar inmediatamente
        processed_data = process_trading_data(file_info['path'])
        
        # Actualizar datos procesados
        from app import update_processed_data
        update_processed_data(processed_data)
        
        # Copiar también al archivo predeterminado para compatibilidad
        copy_file(temp_path, Config.DEFAULT_TRADES_PATH)
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        flash(f'Datos para {file_info["date_str"]} cargados correctamente', 'success')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        flash(f'Error al procesar archivo: {str(e)}', 'error')
        return redirect(url_for('main.upload'))

@main_bp.route('/load_date/<int:year>/<int:month>/<int:day>')
def load_date(year, month, day):
    """Carga datos para una fecha específica"""
    try:
        # Cargar datos para la fecha
        processed_data = load_trades_by_date(year, month, day)
        
        if not processed_data:
            flash(f'No se encontraron datos para la fecha {year}-{month:02d}-{day:02d}', 'error')
            return redirect(url_for('main.upload'))
        
        # Actualizar datos procesados
        from app import update_processed_data
        update_processed_data(processed_data)
        
        flash(f'Datos para {year}-{month:02d}-{day:02d} cargados correctamente', 'success')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f'Error al cargar datos: {str(e)}', 'error')
        return redirect(url_for('main.upload'))