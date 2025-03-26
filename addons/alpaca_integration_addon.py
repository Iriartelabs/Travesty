"""
Addon: Alpaca Integration
Descripción: Integración con la API de Alpaca para trading automatizado
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from addon_system import AddonRegistry
import json
import os
from datetime import datetime
from config import Config  # Importamos Config para acceder a las rutas

# Ruta del archivo de credenciales (fuera del directorio del proyecto)
# Usa la carpeta "data" dentro del proyecto para mayor portabilidad
CREDENTIALS_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data', 'alpaca_credentials.json')
print(f"[INFO] Archivo de credenciales Alpaca: {CREDENTIALS_FILE}")

# Función para cargar credenciales
def load_credentials():
    """Carga las credenciales desde el archivo"""
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                credentials = json.load(f)
                return credentials
        except Exception as e:
            print(f"Error cargando credenciales: {e}")
    return {
        'api_key': '',
        'api_secret': '',
        'base_url': 'https://paper-api.alpaca.markets/v2'
    }

# Función para guardar credenciales
def save_credentials(api_key, api_secret, base_url):
    """Guarda las credenciales en un archivo"""
    credentials = {
        'api_key': api_key,
        'api_secret': api_secret,
        'base_url': base_url
    }
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
        
        # Depuración - mostrar información sobre el archivo
        print(f"[DEBUG] Guardando credenciales en: {CREDENTIALS_FILE}")
        print(f"[DEBUG] Directorio existe: {os.path.exists(os.path.dirname(CREDENTIALS_FILE))}")
        
        # Guardar el archivo
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f)
        
        print(f"[DEBUG] Credenciales guardadas correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error guardando credenciales: {e}")
        print(f"[ERROR] Ruta del archivo: {CREDENTIALS_FILE}")
        print(f"[ERROR] Permisos de escritura: {os.access(os.path.dirname(CREDENTIALS_FILE), os.W_OK)}")
        return False

# Cargar credenciales al iniciar
CREDENTIALS = load_credentials()
ALPACA_API_KEY = CREDENTIALS.get('api_key', '')
ALPACA_API_SECRET = CREDENTIALS.get('api_secret', '')
ALPACA_BASE_URL = CREDENTIALS.get('base_url', 'https://paper-api.alpaca.markets/v2')

# Definir las funciones de vista para nuestro addon
def alpaca_dashboard():
    """Main view for Alpaca integration dashboard"""
    # Cargar credenciales actuales
    credentials = load_credentials()
    
    return render_template(
        'alpaca_dashboard.html',
        api_key=credentials.get('api_key', ''),
        api_secret=credentials.get('api_secret', ''),
        base_url=credentials.get('base_url', '')
    )

def alpaca_settings():
    """View for managing Alpaca API settings"""
    # Simplemente mostrar las credenciales actuales (solo lectura)
    return render_template(
        'alpaca_settings.html',
        api_key=ALPACA_API_KEY,
        api_secret=ALPACA_API_SECRET,
        base_url=ALPACA_BASE_URL
    )

def register_addon():
    """Register the Alpaca integration addon in the system"""
    # Registrar el dashboard principal
    AddonRegistry.register('alpaca_integration', {
        'name': 'Alpaca Integration',
        'description': 'Integración con la API de Alpaca para trading automatizado',
        'route': '/alpaca',
        'view_func': alpaca_dashboard,
        'template': 'alpaca_dashboard.html',
        'icon': 'robot',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    # Registrar la vista de configuración (esta es la clave para añadir rutas adicionales)
    AddonRegistry.register('alpaca_settings', {
        'name': 'Alpaca Settings',
        'description': 'Configuración de la API de Alpaca',
        'route': '/alpaca/settings',
        'view_func': alpaca_settings,
        'template': 'alpaca_settings.html',
        'icon': 'cog',
        'active': False,  # No mostrar en la barra lateral
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })

# Register automatically when imported
if __name__ != '__main__':
    register_addon()
