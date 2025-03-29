"""
Gestión de providers de trading
"""
import os
import json

class TradingProviderRegistry:
    """Registro central de proveedores de trading"""
    providers = {}
    provider_info = {}
    active_provider = None
    active_provider_name = None
    
    @classmethod
    def register_provider(cls, name, provider_instance):
        """Registra un nuevo provider en el sistema"""
        cls.providers[name] = provider_instance
        
    @classmethod
    def register_provider_info(cls, name, info):
        """Registra información del provider"""
        cls.provider_info[name] = info
        
    @classmethod
    def get_provider(cls, name=None):
        """Obtiene un provider específico por nombre o el activo si no se especifica"""
        if name:
            return cls.providers.get(name)
        return cls.active_provider
    
    @classmethod
    def get_providers(cls):
        """Devuelve todos los providers registrados"""
        return cls.providers
    
    @classmethod
    def get_provider_info(cls):
        """Devuelve información de todos los providers"""
        return cls.provider_info
    
    @classmethod
    def get_active_provider_name(cls):
        """Obtiene el nombre del provider activo"""
        return cls.active_provider_name
    
    @classmethod
    def set_active_provider(cls, name):
        """Establece el provider activo"""
        if name in cls.providers:
            cls.active_provider = cls.providers[name]
            cls.active_provider_name = name
            
            # Guardar en configuración
            config_path = os.path.join('config', 'providers')
            if not os.path.exists(config_path):
                os.makedirs(config_path)
                
            with open(os.path.join(config_path, 'active.json'), 'w') as f:
                json.dump({'active_provider': name}, f)
            
            return True
        return False
    
    @classmethod
    def initialize_provider(cls, name, config):
        """Inicializa o reinicializa un provider con una configuración específica"""
        if name not in cls.providers:
            return False
            
        # Esta es una implementación básica. En un sistema real,
        # cada provider tendría su propia lógica de inicialización.
        provider = cls.providers[name]
        if hasattr(provider, 'initialize'):
            return provider.initialize(config)
        return True
    
    @classmethod
    def save_provider_config(cls, name, config):
        """Guarda la configuración de un provider"""
        if name not in cls.provider_info:
            return False
        
        # Guardar en el sistema de archivos
        config_path = os.path.join('config', 'providers')
        if not os.path.exists(config_path):
            os.makedirs(config_path)
            
        with open(os.path.join(config_path, f'{name}.json'), 'w') as f:
            json.dump(config, f)
        
        # Si hay una instancia del provider, actualizarla
        if name in cls.providers:
            return cls.initialize_provider(name, config)
        
        return True
    
    @classmethod
    def load_provider_config(cls, name):
        """Carga la configuración guardada para un provider"""
        config_path = os.path.join('config', 'providers', f'{name}.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar configuración de {name}: {e}")
        
        return {}
    
    @classmethod
    def load_active_provider(cls):
        """Carga el provider activo desde la configuración"""
        config_path = os.path.join('config', 'providers', 'active.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    active_provider = data.get('active_provider')
                    
                    if active_provider and active_provider in cls.providers:
                        cls.active_provider = cls.providers[active_provider]
                        cls.active_provider_name = active_provider
            except Exception as e:
                print(f"Error al cargar provider activo: {e}")
    
    @classmethod
    def initialize(cls):
        """Inicializa el sistema de providers"""
        # Cargar provider activo
        cls.load_active_provider()