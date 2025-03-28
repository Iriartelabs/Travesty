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

# Control de registro único
_is_registered = False

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
    global ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL
    
    # Verificar si estamos en modo guardar
    if request.args.get('save') == '1':
        api_key = request.args.get('api_key', '')
        api_secret = request.args.get('api_secret', '')
        base_url = request.args.get('base_url', 'https://paper-api.alpaca.markets/v2')
        
        # Guardar las credenciales
        if save_credentials(api_key, api_secret, base_url):
            # Actualizar variables globales
            ALPACA_API_KEY = api_key
            ALPACA_API_SECRET = api_secret
            ALPACA_BASE_URL = base_url
            flash('Configuración guardada con éxito', 'success')
        else:
            flash('Error al guardar la configuración', 'danger')
    
    # Renderizar la plantilla con las credenciales actuales
    return render_template(
        'alpaca_settings.html',
        api_key=ALPACA_API_KEY,
        api_secret=ALPACA_API_SECRET,
        base_url=ALPACA_BASE_URL,
        credentials_file=CREDENTIALS_FILE
    )

def submit_order():
    """Endpoint para enviar órdenes reales a Alpaca"""
    import requests
    import json
    
    # Verificar que es una petición POST
    if request.method != 'POST':
        return jsonify({
            'success': False,
            'message': 'Este endpoint solo acepta peticiones POST'
        })
    
    # Cargar credenciales
    credentials = load_credentials()
    
    # Verificar que hay credenciales configuradas
    if not credentials.get('api_key') or not credentials.get('api_secret'):
        return jsonify({
            'success': False,
            'message': 'No hay credenciales de API configuradas'
        })
    
    # Obtener datos del formulario
    try:
        # Intentar obtener datos como JSON primero
        if request.is_json:
            data = request.get_json()
        else:
            # Si no es JSON, obtener de form data
            data = request.form
            
        symbol = data.get('symbol', '').upper()
        order_type = data.get('orderType', 'market')
        side = data.get('side', 'buy')
        qty = float(data.get('qty', 1))
        
        # Validar datos básicos
        if not symbol:
            return jsonify({
                'success': False,
                'message': 'Debe especificar un símbolo válido'
            })
            
        # Preparar datos de la orden
        order_data = {
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': order_type,
            'time_in_force': 'day'
        }
        
        # Añadir precio límite si es necesario
        if order_type in ['limit', 'stop_limit'] and 'limitPrice' in data:
            order_data['limit_price'] = float(data.get('limitPrice'))
        
        # Configurar headers y URL
        headers = {
            'APCA-API-KEY-ID': credentials.get('api_key'),
            'APCA-API-SECRET-KEY': credentials.get('api_secret'),
            'Content-Type': 'application/json'
        }
        
        # Determinar el endpoint correcto
        base_url = credentials.get('base_url')
        if not base_url.endswith('/'):
            base_url += '/'
        
        orders_url = f"{base_url}orders"
        
        # Enviar la orden a Alpaca
        response = requests.post(
            orders_url,
            headers=headers,
            data=json.dumps(order_data),
            timeout=10
        )
        
        # Procesar respuesta
        if response.status_code in [200, 201]:
            order_response = response.json()
            print(f"[INFO] Orden enviada con éxito: {order_response.get('id')}")
            return jsonify({
                'success': True,
                'message': 'Orden enviada correctamente',
                'order': order_response
            })
        else:
            error_msg = f"Error al enviar orden: {response.status_code} - {response.text}"
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            })
            
    except Exception as e:
        error_msg = f"Error procesando la orden: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        })

def get_positions():
    """Endpoint para obtener posiciones reales de Alpaca"""
    import requests
    
    # Cargar credenciales
    credentials = load_credentials()
    
    # Verificar que hay credenciales configuradas
    if not credentials.get('api_key') or not credentials.get('api_secret'):
        return jsonify({
            'success': False,
            'message': 'No hay credenciales de API configuradas'
        })
    
    try:
        # Configurar headers y URL
        headers = {
            'APCA-API-KEY-ID': credentials.get('api_key'),
            'APCA-API-SECRET-KEY': credentials.get('api_secret')
        }
        
        # Determinar el endpoint correcto
        base_url = credentials.get('base_url')
        if not base_url.endswith('/'):
            base_url += '/'
        
        positions_url = f"{base_url}positions"
        
        # Consultar las posiciones en Alpaca
        response = requests.get(
            positions_url,
            headers=headers,
            timeout=10
        )
        
        # Procesar respuesta
        if response.status_code == 200:
            positions = response.json()
            return jsonify({
                'success': True,
                'positions': positions
            })
        else:
            error_msg = f"Error al obtener posiciones: {response.status_code} - {response.text}"
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            })
            
    except Exception as e:
        error_msg = f"Error al obtener posiciones: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        })

def get_order_history():
    """Endpoint para obtener historial de órdenes de Alpaca"""
    import requests
    
    # Cargar credenciales
    credentials = load_credentials()
    
    # Verificar que hay credenciales configuradas
    if not credentials.get('api_key') or not credentials.get('api_secret'):
        return jsonify({
            'success': False,
            'message': 'No hay credenciales de API configuradas'
        })
    
    try:
        # Configurar headers y URL
        headers = {
            'APCA-API-KEY-ID': credentials.get('api_key'),
            'APCA-API-SECRET-KEY': credentials.get('api_secret')
        }
        
        # Determinar el endpoint correcto
        base_url = credentials.get('base_url')
        if not base_url.endswith('/'):
            base_url += '/'
        
        # Usar parámetros para limitar el número de órdenes
        orders_url = f"{base_url}orders?status=all&limit=10"
        
        # Consultar las órdenes en Alpaca
        response = requests.get(
            orders_url,
            headers=headers,
            timeout=10
        )
        
        # Procesar respuesta
        if response.status_code == 200:
            orders = response.json()
            return jsonify({
                'success': True,
                'orders': orders
            })
        else:
            error_msg = f"Error al obtener historial: {response.status_code} - {response.text}"
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            })
            
    except Exception as e:
        error_msg = f"Error al obtener historial: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        })

def alpaca_create_order():
    """Endpoint para enviar órdenes reales a Alpaca (versión GET)"""
    import requests
    import json
    
    # Cargar credenciales
    credentials = load_credentials()
    
    # Verificar que hay credenciales configuradas
    if not credentials.get('api_key') or not credentials.get('api_secret'):
        return jsonify({
            'success': False,
            'message': 'No hay credenciales de API configuradas'
        })
    
    # Obtener datos de los parámetros de consulta
    try:
        symbol = request.args.get('symbol', '').upper()
        order_type = request.args.get('orderType', 'market')
        side = request.args.get('side', 'buy')
        qty = float(request.args.get('qty', 1))
        
        # Validar datos básicos
        if not symbol:
            return jsonify({
                'success': False,
                'message': 'Debe especificar un símbolo válido'
            })
            
        # Preparar datos de la orden
        order_data = {
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': order_type,
            'time_in_force': 'day'
        }
        
        # Añadir precio límite si es necesario
        if order_type in ['limit', 'stop_limit'] and 'limitPrice' in request.args:
            order_data['limit_price'] = float(request.args.get('limitPrice'))
        
        # Configurar headers y URL
        headers = {
            'APCA-API-KEY-ID': credentials.get('api_key'),
            'APCA-API-SECRET-KEY': credentials.get('api_secret'),
            'Content-Type': 'application/json'
        }
        
        # Determinar el endpoint correcto
        base_url = credentials.get('base_url')
        if not base_url.endswith('/'):
            base_url += '/'
        
        orders_url = f"{base_url}orders"
        
        # Enviar la orden a Alpaca
        response = requests.post(
            orders_url,
            headers=headers,
            data=json.dumps(order_data),
            timeout=10
        )
        
        # Procesar respuesta
        if response.status_code in [200, 201]:
            order_response = response.json()
            print(f"[INFO] Orden enviada con éxito: {order_response.get('id')}")
            return jsonify({
                'success': True,
                'message': 'Orden enviada correctamente',
                'order': order_response
            })
        else:
            error_msg = f"Error al enviar orden: {response.status_code} - {response.text}"
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            })
            
    except Exception as e:
        error_msg = f"Error procesando la orden: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg
        })

def register_addon():
    """Register the Alpaca integration addon in the system"""
    global _is_registered
    if _is_registered:
        return
        
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
    
    # Registrar el endpoint para enviar órdenes
    AddonRegistry.register('alpaca_submit_order', {
        'name': 'Alpaca Submit Order',
        'description': 'Endpoint para enviar órdenes a Alpaca',
        'route': '/alpaca/submit_order',
        'view_func': submit_order,
        'template': None,
        'icon': None,
        'active': False,  # No mostrar en la barra lateral
        # Quitamos 'methods': ['POST'] ya que parece no ser compatible
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    # Registrar el endpoint para enviar órdenes (versión GET)
    AddonRegistry.register('alpaca_create_order', {
        'name': 'Alpaca Create Order',
        'description': 'Endpoint para enviar órdenes a Alpaca (versión GET)',
        'route': '/alpaca/create_order',
        'view_func': alpaca_create_order,
        'template': None,
        'icon': None,
        'active': False,  # No mostrar en la barra lateral
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    # Registrar el endpoint para obtener posiciones
    AddonRegistry.register('alpaca_get_positions', {
        'name': 'Alpaca Get Positions',
        'description': 'Endpoint para obtener posiciones de Alpaca',
        'route': '/alpaca/get_positions',
        'view_func': get_positions,
        'template': None,
        'icon': None,
        'active': False,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    # Registrar el endpoint para obtener historial de órdenes
    AddonRegistry.register('alpaca_get_order_history', {
        'name': 'Alpaca Order History',
        'description': 'Endpoint para obtener historial de órdenes de Alpaca',
        'route': '/alpaca/get_order_history',
        'view_func': get_order_history,
        'template': None,
        'icon': None,
        'active': False,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })
    
    _is_registered = True

# Register automatically when imported
if __name__ != '__main__':
    register_addon()
