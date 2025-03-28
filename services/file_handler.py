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

def validate_csv_files(file_paths):
    """
    Valida que los archivos CSV existan y no estén vacíos
    
    Args:
        file_paths (list): Lista de rutas de archivos a validar
    
    Returns:
        bool: True si todos los archivos son válidos, False en caso contrario
    """
    for path in file_paths:
        # Verificar que el archivo existe
        if not os.path.exists(path):
            print(f"Archivo no encontrado: {path}")
            return False
        
        # Verificar que el archivo no esté vacío
        if os.path.getsize(path) == 0:
            print(f"Archivo vacío: {path}")
            return False
        
        # Verificar que el archivo tenga extensión .csv
        if not path.lower().endswith('.csv'):
            print(f"El archivo no es un CSV: {path}")
            return False
    
    return True