"""
Gestión de providers de trading
"""
import importlib
import json
import os
from flask import current_app
from config import Config

class TradingProviderRegistry:
    """Registro de providers de trading disponibles en el sistema"""
    
    _providers = {}
    _provider_info = {}
    _active_provider = None
    
    @classmethod
    def initialize(cls):
        """Inicializa el registro de providers y carga los disponibles"""
        cls._providers = {}
        cls._provider_info = {}
        cls._active_provider = None
        
        # Cargar providers disponibles
        cls._load_providers()
        
        # Cargar configuración activa
        cls._load_active_provider()
    
    @classmethod
    def _load_providers(cls):
        """Carga los providers disponibles en el sistema"""
        # Carpeta donde se encuentran los providers
        providers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'providers')
        
        # Verificar si existe la carpeta
        if not os.path.exists(providers_path):
            print(f"La carpeta de providers no existe: {providers_path}")
            return
        
        # Buscar archivos Python en la carpeta de providers
        for filename in os.listdir(providers_path):
            if filename.endswith('.py') and not filename.startswith('__'):
                provider_name = filename[:-3]  # Quitar extensión .py
                
                try:
                    # Importar dinámicamente el módulo del provider
                    module = importlib.import_module(f'providers.{provider_name}')
                    
                    # Verificar si el módulo tiene la información del provider
                    if hasattr(module, 'provider_info'):
                        cls._provider_info[provider_name] = module.provider_info
                        
                        # Verificar si está disponible (paquetes requeridos instalados)
                        if module.provider_info.get('available', True):
                            # Instanciar el provider si tiene la clase correspondiente
                            provider_class_name = provider_name.capitalize() + 'Provider'
                            if hasattr(module, provider_class_name):
                                provider_class = getattr(module, provider_class_name)
                                
                                # Cargar configuración guardada
                                config = cls._load_provider_config(provider_name)
                                
                                # Crear instancia del provider con la configuración
                                provider_instance = provider_class(
                                    api_key=config.get('api_key'),
                                    api_secret=config.get('api_secret'),
                                    base_url=config.get('base_url')
                                )
                                
                                # Registrar el provider
                                cls._providers[provider_name] = provider_instance
                except Exception as e:
                    print(f"Error al cargar provider {provider_name}: {e}")
    
    @classmethod
    def _load_provider_config(cls, provider_name):
        """Carga la configuración guardada para un provider"""
        config_path = os.path.join(Config.CONFIG_PATH, 'providers', f'{provider_name}.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar configuración de {provider_name}: {e}")
        
        return {}
    
    @classmethod
    def _load_active_provider(cls):
        """Carga el provider activo desde la configuración"""
        config_path = os.path.join(Config.CONFIG_PATH, 'providers', 'active.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    active_provider = data.get('active_provider')
                    
                    if active_provider and active_provider in cls._providers:
                        cls._active_provider = active_provider
            except Exception as e:
                print(f"Error al cargar provider activo: {e}")
    
    @classmethod
    def get_providers(cls):
        """Devuelve el diccionario de providers disponibles"""
        return cls._providers
    
    @classmethod
    def get_provider_info(cls):
        """Devuelve la información de todos los providers"""
        return cls._provider_info
    
    @classmethod
    def get_provider(cls, provider_name):
        """Obtiene un provider específico por nombre"""
        return cls._providers.get(provider_name)
    
    @classmethod
    def get_active_provider(cls):
        """Obtiene el provider activo actual"""
        if cls._active_provider:
            return cls._providers.get(cls._active_provider)
        return None
    
    @classmethod
    def get_active_provider_name(cls):
        """Obtiene el nombre del provider activo"""
        return cls._active_provider
    
    @classmethod
    def register_provider(cls, provider_name, provider_instance):
        """Registra un nuevo provider en el sistema"""
        cls._providers[provider_name] = provider_instance
    
    @classmethod
    def set_active_provider(cls, provider_name):
        """Establece el provider activo"""
        if provider_name in cls._providers:
            cls._active_provider = provider_name
            
            # Guardar en configuración
            config_path = os.path.join(Config.CONFIG_PATH, 'providers')
            if not os.path.exists(config_path):
                os.makedirs(config_path)
                
            with open(os.path.join(config_path, 'active.json'), 'w') as f:
                json.dump({'active_provider': provider_name}, f)
            
            return True
        return False
    
    @classmethod
    def save_provider_config(cls, provider_name, config):
        """Guarda la configuración de un provider"""
        if provider_name not in cls._provider_info:
            return False
        
        # Guardar en el sistema de archivos
        config_path = os.path.join(Config.CONFIG_PATH, 'providers')
        if not os.path.exists(config_path):
            os.makedirs(config_path)
            
        with open(os.path.join(config_path, f'{provider_name}.json'), 'w') as f:
            json.dump(config, f)
        
        # Si hay una instancia del provider, actualizarla
        if provider_name in cls._providers:
            provider = cls._providers[provider_name]
            
            # Inicializar con la nueva configuración
            if hasattr(provider, 'initialize'):
                provider.initialize(config)
        
        return True