import os
import shutil

def save_uploaded_file(file, destination_path):
    """
    Guarda un archivo subido en una ruta específica
    
    Args:
        file (FileStorage): Archivo subido de Flask
        destination_path (str): Ruta de destino para guardar el archivo
    
    Returns:
        str: Ruta del archivo guardado
    """
    try:
        # Asegurar que el directorio de destino existe
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Guardar el archivo
        file.save(destination_path)
        
        return destination_path
    except Exception as e:
        print(f"Error guardando archivo: {e}")
        return None

def copy_file(source_path, destination_path):
    """
    Copia un archivo de una ruta a otra
    
    Args:
        source_path (str): Ruta del archivo de origen
        destination_path (str): Ruta de destino para copiar el archivo
    
    Returns:
        bool: True si la copia fue exitosa, False en caso contrario
    """
    try:
        # Asegurar que el directorio de destino existe
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Copiar el archivo
        shutil.copy2(source_path, destination_path)
        
        return True
    except Exception as e:
        print(f"Error copiando archivo: {e}")
        return False

def validate_trades_csv(trades_path):
    """
    Valida específicamente el archivo Trades.csv
    
    Args:
        trades_path (str): Ruta del archivo Trades.csv
    
    Returns:
        bool: True si el archivo es válido, False en caso contrario
    """
    # Verificar que el archivo existe
    if not os.path.exists(trades_path):
        print(f"Archivo Trades.csv no encontrado: {trades_path}")
        return False
    
    # Verificar que el archivo no esté vacío
    if os.path.getsize(trades_path) == 0:
        print(f"Archivo Trades.csv vacío: {trades_path}")
        return False
    
    # Verificar que el archivo sea un CSV válido
    try:
        with open(trades_path, 'r', encoding='utf-8') as f:
            # Leer primera línea (encabezados)
            headers = f.readline().strip().split(',')
            
            # Verificar columnas mínimas requeridas
            required_columns = ['TradeID', 'OrderID', 'B/S', 'symb', 'qty', 'price', 'time']
            for col in required_columns:
                if col not in headers:
                    print(f"Columna requerida '{col}' no encontrada en Trades.csv")
                    return False
        
        return True
    except Exception as e:
        print(f"Error validando Trades.csv: {e}")
        return False

def get_files_in_directory(directory, extension='.csv'):
    """
    Obtiene una lista de archivos con una extensión específica en un directorio
    
    Args:
        directory (str): Ruta del directorio
        extension (str, optional): Extensión de archivos a buscar. Por defecto '.csv'
    
    Returns:
        list: Lista de rutas completas de archivos con la extensión especificada
    """
    try:
        # Obtener todos los archivos en el directorio con la extensión especificada
        return [
            os.path.join(directory, filename) 
            for filename in os.listdir(directory) 
            if filename.endswith(extension)
        ]
    except Exception as e:
        print(f"Error obteniendo archivos: {e}")
        return []