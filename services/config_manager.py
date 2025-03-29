import os
import json
from config import Config

CONFIG_FILE = os.path.join(Config.DATA_FOLDER, 'application_config.json')

def load_config():
    """Carga la configuración guardada"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
    
    return {}  # Configuración por defecto

def save_config(config_data):
    """Guarda la configuración en archivo"""
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # Guardar configuración
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False

def get_config_value(key, default=None):
    """Obtiene un valor específico de la configuración"""
    config = load_config()
    
    # Manejar claves anidadas (formato: 'section.key')
    if '.' in key:
        parts = key.split('.')
        value = config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value
    
    return config.get(key, default)

def set_config_value(key, value):
    """Establece un valor específico en la configuración"""
    config = load_config()
    
    # Manejar claves anidadas (formato: 'section.key')
    if '.' in key:
        parts = key.split('.')
        current = config
        
        # Navegar hasta la sección correcta
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Establecer el valor
        current[parts[-1]] = value
    else:
        config[key] = value
    
    return save_config(config)