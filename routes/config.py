"""
Rutas para la configuración de la aplicación
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
import json
import os
from config import Config
from services.providers import TradingProviderRegistry

config_bp = Blueprint('config', __name__, url_prefix='/config')

@config_bp.route('/')
@config_bp.route('/<section>')
def index(section='general'):
    """Vista principal de configuración"""
    # Obtener todos los providers disponibles
    provider_info = TradingProviderRegistry.get_provider_info()
    providers = TradingProviderRegistry.get_providers()
    active_provider = TradingProviderRegistry.get_active_provider_name()
    
    # Si es una sección de provider específico, cargar su configuración
    provider_config = None
    if section.startswith('providers.'):
        provider_name = section.split('.')[-1]
        if provider_name in provider_info:
            provider_config = TradingProviderRegistry.load_provider_config(provider_name)
    
    # Cargar configuración general
    general_config = _load_general_config()
    
    return render_template(
        'configuration.html',
        section=section,
        providers=provider_info,
        active_provider=active_provider,
        provider_config=provider_config,
        general_config=general_config
    )

@config_bp.route('/save_provider_config', methods=['POST'])
def save_provider_config():
    """Guarda la configuración de un provider"""
    provider_name = request.form.get('provider')
    if not provider_name:
        flash('Provider no especificado', 'error')
        return redirect(url_for('config.index', section='providers'))
    
    # Obtener datos del formulario según los campos configurados
    provider_info = TradingProviderRegistry.get_provider_info().get(provider_name)
    if not provider_info:
        flash(f'Provider {provider_name} no encontrado', 'error')
        return redirect(url_for('config.index', section='providers'))
    
    # Construir configuración a partir del formulario
    config = {}
    for field in provider_info.get('config_fields', []):
        field_name = field.get('name')
        field_type = field.get('type')
        
        if field_type == 'checkbox':
            config[field_name] = field_name in request.form
        else:
            config[field_name] = request.form.get(field_name, '')
    
    # Guardar configuración
    if TradingProviderRegistry.save_provider_config(provider_name, config):
        flash(f'Configuración de {provider_name} guardada con éxito', 'success')
    else:
        flash(f'Error al guardar configuración de {provider_name}', 'error')
    
    return redirect(url_for('config.index', section=f'providers.{provider_name}'))

@config_bp.route('/set_active_provider', methods=['POST'])
def set_active_provider():
    """Establece el provider activo"""
    provider_name = request.form.get('provider')
    if not provider_name:
        flash('Provider no especificado', 'error')
        return redirect(url_for('config.index', section='providers'))
    
    if TradingProviderRegistry.set_active_provider(provider_name):
        flash(f'Provider {provider_name} activado con éxito', 'success')
    else:
        flash(f'Error al activar provider {provider_name}', 'error')
    
    return redirect(url_for('config.index', section='providers'))

@config_bp.route('/save_general_config', methods=['POST'])
def save_general_config():
    """Guarda la configuración general de la aplicación"""
    # Obtener datos del formulario
    app_name = request.form.get('app_name', 'Travesty Analyzer')
    theme = request.form.get('theme', 'default')
    language = request.form.get('language', 'es')
    
    # Crear configuración
    config = {
        'app_name': app_name,
        'theme': theme,
        'language': language
    }
    
    # Guardar configuración en archivo
    config_path = os.path.join('config', 'general.json')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    flash('Configuración general guardada con éxito', 'success')
    return redirect(url_for('config.index', section='general'))

def _load_general_config():
    """Carga la configuración general de la aplicación"""
    config_path = os.path.join('config', 'general.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar configuración general: {e}")
    
    # Configuración por defecto
    return {
        'app_name': 'Travesty Analyzer',
        'theme': 'default',
        'language': 'es'
    }