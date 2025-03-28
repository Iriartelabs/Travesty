#!/usr/bin/env python
"""
Script de migración para reorganizar el sistema de addons de DAS Trader Analyzer
según la nueva estructura:

addons/
├── nombre_addon/
│   ├── src/
│   │   └── nombre_addon.py
│   └── ui/
│       └── nombre_addon.html

Este script:
1. Crea la estructura de directorios para cada addon
2. Mueve los archivos Python a sus nuevas ubicaciones
3. Mueve las plantillas HTML correspondientes
4. Actualiza las referencias en el código si es necesario
"""

import os
import shutil
import re
import sys
import subprocess
import argparse
from pathlib import Path

def print_header(message):
    """Imprime un mensaje con formato de encabezado"""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80 + "\n")

def print_step(message):
    """Imprime un mensaje de paso con formato"""
    print(f"→ {message}")

def print_success(message):
    """Imprime un mensaje de éxito con formato"""
    print(f"✓ {message}")

def print_warning(message):
    """Imprime un mensaje de advertencia con formato"""
    print(f"⚠ {message}")

def print_error(message):
    """Imprime un mensaje de error con formato"""
    print(f"✗ {message}")

def detect_addons(addons_dir, templates_dir):
    """
    Detecta los addons existentes en la estructura actual.
    
    Returns:
        dict: Mapa de addons con sus archivos Python y HTML asociados
    """
    print_header("Detectando addons existentes")
    
    # Obtener archivos Python en el directorio de addons (excluyendo __init__.py)
    addon_files = [f for f in os.listdir(addons_dir) 
                  if f.endswith('.py') and not f.startswith('__')]
    
    # Mapa para almacenar la información de los addons
    addons_map = {}
    
    for addon_file in addon_files:
        # Nombre base del addon (sin extensión)
        addon_name = os.path.splitext(addon_file)[0]
        print_step(f"Analizando addon: {addon_name}")
        
        # Ruta completa al archivo Python
        py_path = os.path.join(addons_dir, addon_file)
        
        # Buscar archivos HTML asociados
        html_files = []
        
        # 1. Intentar con nombre coincidente (p.ej., weekday_analysis.py → weekday_analysis.html)
        main_html = f"{addon_name}.html"
        main_html_path = os.path.join(templates_dir, main_html)
        if os.path.exists(main_html_path):
            html_files.append(main_html)
            print_step(f"  - Encontrado HTML principal: {main_html}")
        
        # 2. Buscar en el código Python referencias a plantillas
        additional_templates = []
        try:
            with open(py_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Buscar referencias a render_template y variantes
                template_refs = set(re.findall(r"render_template\(['\"]([^'\"]+)['\"]", content))
                template_refs.update(re.findall(r"render_template\([^,]+,['\"]([^'\"]+)['\"]", content))
                
                for template_ref in template_refs:
                    if template_ref not in html_files and os.path.exists(os.path.join(templates_dir, template_ref)):
                        additional_templates.append(template_ref)
                        print_step(f"  - Encontrada plantilla adicional: {template_ref}")
        except Exception as e:
            print_error(f"  Error al analizar el archivo {addon_file}: {str(e)}")
        
        # Guardar información del addon
        addons_map[addon_name] = {
            'py_file': addon_file,
            'main_html': main_html if os.path.exists(main_html_path) else None,
            'additional_templates': additional_templates
        }
    
    if not addons_map:
        print_warning("No se encontraron addons en la estructura actual.")
        return {}
    
    print_success(f"Se detectaron {len(addons_map)} addons.")
    return addons_map

def create_directory_structure(addons_dir, addons_map):
    """
    Crea la nueva estructura de directorios para los addons.
    
    Args:
        addons_dir: Directorio base de addons
        addons_map: Mapa de addons detectados
    """
    print_header("Creando nueva estructura de directorios")
    
    for addon_name, addon_info in addons_map.items():
        print_step(f"Creando directorios para: {addon_name}")
        
        # Crear directorios para el addon
        addon_dir = os.path.join(addons_dir, addon_name)
        src_dir = os.path.join(addon_dir, 'src')
        ui_dir = os.path.join(addon_dir, 'ui')
        
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(ui_dir, exist_ok=True)
        
        print_success(f"Estructura creada para {addon_name}")

def copy_files(addons_dir, templates_dir, addons_map, mode="copy"):
    """
    Copia/mueve los archivos a la nueva estructura.
    
    Args:
        addons_dir: Directorio base de addons
        templates_dir: Directorio de plantillas
        addons_map: Mapa de addons detectados
        mode: "copy" para copiar, "move" para mover
    """
    action = "Copiando" if mode == "copy" else "Moviendo"
    print_header(f"{action} archivos a la nueva estructura")
    
    for addon_name, addon_info in addons_map.items():
        print_step(f"{action} archivos para: {addon_name}")
        
        # Rutas origen y destino para el archivo Python
        py_src = os.path.join(addons_dir, addon_info['py_file'])
        py_dest = os.path.join(addons_dir, addon_name, 'src', addon_info['py_file'])
        
        # Copiar/mover archivo Python
        if mode == "copy":
            shutil.copy2(py_src, py_dest)
        else:
            shutil.move(py_src, py_dest)
        print_step(f"  - {action} {addon_info['py_file']}")
        
        # Copiar/mover archivo HTML principal si existe
        if addon_info['main_html']:
            html_src = os.path.join(templates_dir, addon_info['main_html'])
            html_dest = os.path.join(addons_dir, addon_name, 'ui', addon_info['main_html'])
            
            if mode == "copy":
                shutil.copy2(html_src, html_dest)
            else:
                shutil.move(html_src, html_dest)
            print_step(f"  - {action} {addon_info['main_html']}")
        
        # Copiar/mover plantillas adicionales
        for template in addon_info['additional_templates']:
            template_src = os.path.join(templates_dir, template)
            template_dest = os.path.join(addons_dir, addon_name, 'ui', template)
            
            if os.path.exists(template_src):
                if mode == "copy":
                    shutil.copy2(template_src, template_dest)
                else:
                    shutil.move(template_src, template_dest)
                print_step(f"  - {action} {template}")
        
        print_success(f"Archivos {action.lower()[:-1]}dos para {addon_name}")

def update_addon_system(addon_system_path):
    """
    Genera el nuevo archivo addon_system.py con la lógica actualizada.
    
    Args:
        addon_system_path: Ruta al archivo addon_system.py
    """
    print_header("Actualizando sistema de addons")
    
    # Hacer copia de seguridad del archivo original
    backup_path = f"{addon_system_path}.bak"
    try:
        shutil.copy2(addon_system_path, backup_path)
        print_success(f"Copia de seguridad creada: {backup_path}")
    except Exception as e:
        print_error(f"Error al crear copia de seguridad: {str(e)}")
        return False
    
    # Contenido del nuevo archivo addon_system.py
    new_content = """
import os
import importlib.util
import inspect
from flask import Blueprint, Flask, render_template

class AddonRegistry:
    _instance = None
    addons = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def register(cls, addon_id, addon_info):
        # Añadir el addon al registro
        cls.addons[addon_id] = addon_info
    
    @classmethod
    def get_addons(cls):
        return cls.addons
    
    @classmethod
    def get_addon(cls, addon_id):
        return cls.addons.get(addon_id)

def custom_render_template(addon_id, template_name, **context):
    \"\"\"Renderiza una plantilla desde la carpeta ui/ del addon\"\"\"
    addon_info = AddonRegistry.get_addon(addon_id)
    if not addon_info:
        raise ValueError(f"No se encontró el addon con ID: {addon_id}")
    
    # Construir la ruta a la plantilla
    template_path = f"addons/{addon_id}/ui/{template_name}"
    
    return render_template(template_path, **context)

def load_addons_from_directory(app, addons_dir='addons'):
    \"\"\"Carga todos los addons desde la estructura de directorios\"\"\"
    # Obtener la lista de carpetas de addons (excluyendo __pycache__ y archivos)
    addon_folders = [f for f in os.listdir(addons_dir) 
                     if os.path.isdir(os.path.join(addons_dir, f)) and 
                     not f.startswith('__')]
    
    for addon_folder in addon_folders:
        # Ruta al archivo principal del addon
        addon_path = os.path.join(addons_dir, addon_folder, 'src', f'{addon_folder}.py')
        
        if os.path.exists(addon_path):
            try:
                # Cargar el módulo dinámicamente
                spec = importlib.util.spec_from_file_location(addon_folder, addon_path)
                addon_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(addon_module)
                
                # El addon debe registrarse a sí mismo durante la importación
                print(f"Addon cargado: {addon_folder}")
            except Exception as e:
                print(f"Error al cargar el addon {addon_folder}: {str(e)}")
    
    # Registrar addons como blueprints en la aplicación
    for addon_id, addon_info in AddonRegistry.addons.items():
        if 'blueprint' in addon_info and addon_info['blueprint'] is not None:
            # Si tiene un blueprint definido, registrarlo directamente
            app.register_blueprint(addon_info['blueprint'])
        else:
            # Crear un blueprint basado en la función de vista y la ruta
            bp = Blueprint(addon_id, __name__, 
                          template_folder=os.path.join(addons_dir, addon_id, 'ui'))
            
            # Registrar la función de vista principal
            bp.add_url_rule(addon_info['route'], 
                           view_func=addon_info['view_func'], 
                           endpoint=addon_id)
            
            # Almacenar el blueprint en la información del addon
            addon_info['blueprint'] = bp
            
            # Registrar el blueprint en la aplicación
            app.register_blueprint(bp)

def setup_addons_for_app(app):
    \"\"\"Configurar el sistema de addons para la aplicación Flask\"\"\"
    # Configurar carpeta de plantillas personalizada
    template_folder = os.path.abspath('addons')
    app.jinja_loader.searchpath.append(template_folder)
    
    # Cargar los addons
    load_addons_from_directory(app)
"""
    
    # Escribir el nuevo contenido
    try:
        with open(addon_system_path, 'w', encoding='utf-8') as f:
            f.write(new_content.strip())
        print_success(f"Sistema de addons actualizado: {addon_system_path}")
        return True
    except Exception as e:
        print_error(f"Error al actualizar el sistema de addons: {str(e)}")
        return False

def update_addon_files(addons_dir, addons_map):
    """
    Actualiza los archivos Python de los addons para usar custom_render_template.
    
    Args:
        addons_dir: Directorio base de addons
        addons_map: Mapa de addons detectados
    """
    print_header("Actualizando código de los addons")
    
    for addon_name, addon_info in addons_map.items():
        print_step(f"Actualizando código para: {addon_name}")
        
        # Ruta al archivo Python actualizado
        py_path = os.path.join(addons_dir, addon_name, 'src', addon_info['py_file'])
        
        try:
            # Leer contenido actual
            with open(py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Actualizar importaciones
            updated_imports = False
            if "from flask import" in content:
                # Actualizar importación existente de Flask
                content = re.sub(
                    r"from flask import ([^\n]+)",
                    lambda m: m.group(0).replace("render_template", "").replace(", ,", ",").replace(",,", ",").strip(",") + 
                    ("\n" if "render_template" in m.group(0) else ""),
                    content
                )
                # Añadir importación de custom_render_template si no existe
                if "from addon_system import" in content:
                    if "custom_render_template" not in content:
                        content = re.sub(
                            r"from addon_system import ([^\n]+)",
                            r"from addon_system import \1, custom_render_template",
                            content
                        )
                        updated_imports = True
                else:
                    # Añadir nueva importación
                    content = content.replace(
                        "from addon_system import AddonRegistry",
                        "from addon_system import AddonRegistry, custom_render_template"
                    )
                    updated_imports = True
            
            # Si no se pudo actualizar importaciones, añadir manualmente
            if not updated_imports and "custom_render_template" not in content:
                content = "from addon_system import custom_render_template\n" + content
            
            # Actualizar llamadas a render_template
            # Primero encontrar todas las llamadas a render_template
            render_calls = re.findall(r"render_template\s*\(\s*['\"]([^'\"]+)['\"]", content)
            
            for template in render_calls:
                # Buscar la llamada completa para reemplazarla
                old_call_pattern = fr"render_template\s*\(\s*['\"]({template})['\"]"
                
                # Reemplazar con custom_render_template
                new_call = f"custom_render_template(\n        '{addon_name}',  # ID del addon\n        '{template}'"
                
                # Hacer el reemplazo
                content = re.sub(old_call_pattern, new_call, content)
            
            # Escribir el contenido actualizado
            with open(py_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_success(f"Código actualizado para {addon_name}")
            
        except Exception as e:
            print_error(f"Error al actualizar el archivo {py_path}: {str(e)}")
    
    print_success("Todos los archivos de addons han sido actualizados.")

def update_app_py(app_py_path):
    """
    Actualiza el archivo app.py para usar el nuevo sistema de addons.
    
    Args:
        app_py_path: Ruta al archivo app.py
    """
    print_header("Actualizando app.py")
    
    # Hacer copia de seguridad del archivo original
    backup_path = f"{app_py_path}.bak"
    try:
        shutil.copy2(app_py_path, backup_path)
        print_success(f"Copia de seguridad creada: {backup_path}")
    except Exception as e:
        print_error(f"Error al crear copia de seguridad: {str(e)}")
        return False
    
    try:
        # Leer contenido actual
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar patrón de código para la inicialización de addons
        if "from addon_system import" in content:
            # Actualizar importación
            if "setup_addons_for_app" not in content:
                content = content.replace(
                    "from addon_system import",
                    "from addon_system import setup_addons_for_app,"
                )
                
            # Buscar patrón de carga de addons
            if "load_addons_from_directory" in content:
                # Reemplazar la carga de addons con la nueva función
                content = re.sub(
                    r"# Cargar addons\s+load_addons_from_directory\(app\)",
                    "# Configurar addons\nsetup_addons_for_app(app)",
                    content
                )
            else:
                # Añadir la configuración de addons antes de app.run()
                content = content.replace(
                    "if __name__ == '__main__':",
                    "# Configurar addons\nsetup_addons_for_app(app)\n\nif __name__ == '__main__':"
                )
        
        # Escribir el contenido actualizado
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Archivo app.py actualizado: {app_py_path}")
        return True
    except Exception as e:
        print_error(f"Error al actualizar app.py: {str(e)}")
        return False

def main():
    """
    Función principal que ejecuta el script de migración.
    """
    parser = argparse.ArgumentParser(
        description="Script de migración para reorganizar el sistema de addons de DAS Trader Analyzer."
    )
    
    parser.add_argument(
        "--addons-dir",
        default="addons",
        help="Directorio base donde se encuentran los addons (predeterminado: 'addons')"
    )
    
    parser.add_argument(
        "--templates-dir",
        default="templates",
        help="Directorio donde se encuentran las plantillas HTML (predeterminado: 'templates')"
    )
    
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Directorio donde se encuentra la documentación (predeterminado: 'docs')"
    )
    
    parser.add_argument(
        "--app-py",
        default="app.py",
        help="Ruta al archivo app.py (predeterminado: 'app.py')"
    )
    
    parser.add_argument(
        "--addon-system-py",
        default="addon_system.py",
        help="Ruta al archivo addon_system.py (predeterminado: 'addon_system.py')"
    )
    
    parser.add_argument(
        "--copy-only",
        action="store_true",
        help="Solo copiar archivos, sin moverlos"
    )
    
    parser.add_argument(
        "--skip-update-code",
        action="store_true",
        help="Omitir actualización del código de los addons"
    )
    
    parser.add_argument(
        "--skip-update-app",
        action="store_true",
        help="Omitir actualización del archivo app.py"
    )
    
    parser.add_argument(
        "--skip-update-docs",
        action="store_true",
        help="Omitir actualización de la documentación"
    )
    
    args = parser.parse_args()
    
    # Mostrar banner
    print("\n" + "=" * 80)
    print(" DAS Trader Analyzer - Script de Migración del Sistema de Addons")
    print("=" * 80 + "\n")
    
    print("Este script migrará el sistema de addons a una nueva estructura de directorios:")
    print("""
addons/
├── nombre_addon/
│   ├── src/
│   │   └── nombre_addon.py
│   └── ui/
│       └── nombre_addon.html
    """)
    
    # Confirmar con el usuario
    if not args.copy_only:
        print("\n⚠ ADVERTENCIA: Esta operación moverá archivos. Asegúrate de tener una copia de seguridad.\n")
        
    response = input("¿Deseas continuar? (s/n): ").lower()
    if response != 's' and response != 'y' and response != 'yes' and response != 'si':
        print("Operación cancelada.")
        sys.exit(0)
    
    # Verificar directorios
    if not os.path.isdir(args.addons_dir):
        print_error(f"El directorio de addons no existe: {args.addons_dir}")
        sys.exit(1)
    
    if not os.path.isdir(args.templates_dir):
        print_error(f"El directorio de plantillas no existe: {args.templates_dir}")
        sys.exit(1)
    
    if not os.path.isfile(args.addon_system_py):
        print_error(f"El archivo addon_system.py no existe: {args.addon_system_py}")
        sys.exit(1)
    
    # Detectar addons existentes
    addons_map = detect_addons(args.addons_dir, args.templates_dir)
    
    if not addons_map:
        print_warning("No se encontraron addons para migrar. Finalizando.")
        sys.exit(0)
    
    # Crear estructura de directorios
    create_directory_structure(args.addons_dir, addons_map)
    
    # Copiar/mover archivos
    mode = "copy" if args.copy_only else "move"
    copy_files(args.addons_dir, args.templates_dir, addons_map, mode)
    
    # Actualizar sistema de addons
    update_addon_system(args.addon_system_py)
    
    # Actualizar código de addons
    if not args.skip_update_code:
        update_addon_files(args.addons_dir, addons_map)
    
    # Actualizar app.py
    if not args.skip_update_app and os.path.isfile(args.app_py):
        update_app_py(args.app_py)
    
    # Actualizar documentación
    if not args.skip_update_docs:
        update_documentation(args.docs_dir)
    
    print_header("Migración Completada")
    print("El sistema de addons ha sido migrado exitosamente a la nueva estructura.")
    print("\nSiguientes pasos recomendados:")
    print("1. Verificar que la aplicación funcione correctamente")
    print("2. Actualizar el README.md con la nueva estructura")
    print("3. Eliminar las copias de seguridad si todo funciona correctamente")

def update_documentation(docs_dir):
    """
    Actualiza la documentación del sistema de addons.
    
    Args:
        docs_dir: Directorio de documentación
    """
    print_header("Actualizando documentación")
    
    # Ruta al archivo de documentación de addons
    addon_doc_path = os.path.join(docs_dir, "addon_development.md")
    
    if not os.path.exists(addon_doc_path):
        print_warning(f"Archivo de documentación no encontrado: {addon_doc_path}")
        print_step("Creando nueva documentación...")
        docs_dir = os.path.dirname(addon_doc_path)
        os.makedirs(docs_dir, exist_ok=True)
    else:
        # Hacer copia de seguridad
        backup_path = f"{addon_doc_path}.bak"
        shutil.copy2(addon_doc_path, backup_path)
        print_success(f"Copia de seguridad creada: {backup_path}")
    

if __name__ == "__main__":
    main()