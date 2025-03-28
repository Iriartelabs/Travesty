import os
import pickle

def save_processed_data(data, cache_path):
    """
    Guarda los datos procesados en un archivo de caché
    
    Args:
        data (dict): Datos procesados a guardar
        cache_path (str): Ruta del archivo de caché
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        # Guardar datos en caché
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"[INFO] Datos guardados en caché: {cache_path}")
    except Exception as e:
        print(f"[ERROR] No se pudieron guardar los datos en caché: {e}")

def load_processed_data(cache_path):
    """
    Carga los datos procesados desde un archivo de caché
    
    Args:
        cache_path (str): Ruta del archivo de caché
    
    Returns:
        dict or None: Datos procesados o None si no se pueden cargar
    """
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            print(f"[INFO] Datos cargados desde caché: {cache_path}")
            return data
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar datos desde caché: {e}")
    return None