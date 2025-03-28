# Guía de Desarrollo de Addons para DAS Trader Analyzer

## Introducción

<<<<<<< Updated upstream
Este documento detalla cómo desarrollar addons para la aplicación DAS Trader Analyzer, explicando la arquitectura del sistema de addons, su integración con la aplicación principal y cómo crear nuevos addons de manera efectiva.
=======
Este documento detalla cómo desarrollar addons para la aplicación DAS Trader Analyzer, explicando la arquitectura del sistema de addons, su integración con la aplicación principal y cómo crear nuevos addons de forma efectiva tanto manual como a través de la interfaz de usuario.
>>>>>>> Stashed changes

## Arquitectura de la Aplicación

DAS Trader Analyzer es una aplicación Flask modularizada que analiza datos de trading exportados desde DAS Trader. La estructura principal incluye:

- **app.py**: Punto de entrada principal que inicializa la aplicación
- **routes/**: Contiene los blueprints para las diferentes secciones de la aplicación
- **services/**: Servicios para procesamiento de datos, caché y manejo de archivos
- **templates/**: Plantillas HTML para la interfaz de usuario
- **static/**: Archivos estáticos (CSS, JavaScript, uploads)
- **addons/**: Directorio donde se almacenan los addons
- **addon_system.py**: Sistema central que gestiona el registro y carga de addons

## Sistema de Addons

El sistema de addons permite extender la funcionalidad de la aplicación sin modificar el código principal. Está implementado a través de un registro centralizado que gestiona los addons disponibles.

### Estructura del Sistema

1. **AddonRegistry**: Clase singleton en `addon_system.py` que mantiene un registro de todos los addons.
2. **load_addons_from_directory()**: Función que carga automáticamente todos los addons desde el directorio `addons/`.
3. **Integración con Flask**: Los addons se registran como blueprints de Flask.

## Limitaciones Importantes del Sistema de Addons

El sistema de addons tiene algunas limitaciones importantes que deben tenerse en cuenta al desarrollar addons:

1. **Única Ruta Principal por Addon**: El sistema no gestiona correctamente múltiples rutas separadas dentro de un blueprint. Los addons complejos deben usar una única ruta base con parámetros de acción.

2. **Formato Específico para Referencias URL**: Las referencias en plantillas HTML deben usar el formato `addon_[nombre_del_addon].[nombre_de_función]` en lugar de `[nombre_del_addon].[nombre_de_función]`.

3. **Registro de Blueprints**: El sistema agrega automáticamente el prefijo `addon_` al nombre del blueprint cuando lo registra.

## Mejores Prácticas para Desarrollar Addons

### 1. Estructura Recomendada

La estructura recomendada para cualquier addon es usar una única ruta base con un parámetro de acción:

```python
@addon_bp.route('/mi-ruta')
def main_view():
    """Función principal que maneja todas las acciones del addon"""
    try:
        # Obtener datos procesados de manera robusta
        try:
            from app import processed_data
        except ImportError:
            from config import Config
            from services.cache_manager import load_processed_data
            processed_data = load_processed_data(Config.DATA_CACHE_PATH)
            
        if processed_data is None:
            processed_data = {}
            
        # Obtener la acción solicitada
        action = request.args.get('action', 'default')
        
        if action == 'action1':
            # Lógica para acción 1
            return render_template('plantilla_accion1.html', processed_data=processed_data)
        elif action == 'action2':
            # Lógica para acción 2
            return render_template('plantilla_accion2.html', processed_data=processed_data)
        else:
            # Lógica por defecto
            return render_template('mi_plantilla.html', processed_data=processed_data)
            
    except Exception as e:
        print(f"Error en main_view: {str(e)}")
        # Manejo de errores robusto
        return render_template('mi_plantilla.html', processed_data={}, error=str(e))
```

### 2. Registro del Addon

Siempre registrar el addon con un ID único y proporcionar la ruta y función principal:

```python
def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('mi_addon_id', {
        'name': 'Nombre Mostrado',
        'description': 'Descripción del addon',
        'route': '/mi-ruta',
        'view_func': main_view,
        'template': 'mi_plantilla.html',
        'icon': 'chart-bar',  # Icono de FontAwesome
        'active': True,
        'version': '1.0.0',
        'author': 'Tu Nombre'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

### 3. Referencias URL en Plantillas

En tus plantillas HTML, siempre referencia las rutas usando el prefijo `addon_`:

```html
<a href="{{ url_for('addon_mi_addon_id.main_view', action='action1') }}">Acción 1</a>
<a href="{{ url_for('addon_mi_addon_id.main_view', action='action2') }}">Acción 2</a>
<a href="{{ url_for('addon_mi_addon_id.main_view') }}">Página Principal</a>
```

### 4. Manejo Robusto de Datos Procesados

Siempre implementa un manejo robusto de los datos procesados para evitar errores:

```python
try:
    # Intentar obtener datos procesados de diferentes maneras
    try:
        from app import processed_data
    except ImportError:
        # Si no se puede importar directamente, intentar desde la caché
        from config import Config
        from services.cache_manager import load_processed_data
        processed_data = load_processed_data(Config.DATA_CACHE_PATH)
        
    # Proporcionar un valor predeterminado si los datos son None
    if processed_data is None:
        processed_data = {}
        
    # Usar los datos procesados...
    
except Exception as e:
    print(f"Error al cargar datos procesados: {str(e)}")
    # Continuar con valor predeterminado
    processed_data = {}
```

### 5. Gestión de Formularios

Para los addons que manejan formularios, usa el mismo enfoque de una única ruta con manejo de métodos:

```python
@addon_bp.route('/mi-ruta', methods=['GET', 'POST'])
def main_view():
    """Función principal que maneja todas las acciones del addon"""
    action = request.args.get('action', 'default')
    
    # Acción para mostrar/procesar formulario
    if action == 'formulario':
        if request.method == 'POST':
            # Procesar el formulario
            campo1 = request.form.get('campo1')
            campo2 = request.form.get('campo2')
            
            # Hacer algo con los datos...
            
            flash('Formulario procesado correctamente', 'success')
            return redirect(url_for('addon_mi_addon_id.main_view'))
        else:
            # Mostrar el formulario
            return render_template('mi_formulario.html', processed_data=processed_data)
```

## Cómo Desarrollar un Nuevo Addon

<<<<<<< Updated upstream
### 1. Crear el Archivo del Addon
=======
Existen dos métodos para crear un nuevo addon: manualmente (para desarrolladores) o mediante la interfaz de usuario (para usuarios finales).

### Método 1: Crear un Addon desde la Interfaz de Usuario

1. Navega a la opción "Gestionar Addons" en la barra lateral
2. Completa el formulario con:
   - **Nombre**: Nombre visible del addon
   - **Ruta**: URL para acceder al addon (ej: `/mi-addon`)
   - **Descripción**: Breve descripción de la funcionalidad
   - **Icono**: Nombre del icono de FontAwesome sin el prefijo "fa-"
3. Haz clic en "Crear Addon"
4. Navega a "Recargar Addons" para activar el nuevo addon
5. Modifica los archivos generados siguiendo la estructura recomendada en este documento

### Método 2: Crear un Addon Manualmente

#### 1. Crear el Archivo del Addon
>>>>>>> Stashed changes

Cada addon es un archivo Python (.py) ubicado en el directorio `addons/`. Por ejemplo: `addons/mi_nuevo_addon.py`.

```python
"""
Addon: Nombre del Addon
Descripción: Breve descripción de la funcionalidad
"""
from addon_system import AddonRegistry
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
import json

<<<<<<< Updated upstream
from config import Config
from services.cache_manager import load_processed_data

def mi_funcion_vista():
    """Función principal del addon"""
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener órdenes procesadas
    processed_orders = processed_data.get('processed_orders', [])
    
    # Realizar análisis específico
    mi_analisis = realizar_analisis(processed_orders)
    
    # Convertir a JSON para usar en gráficos
    mi_analisis_json = json.dumps(mi_analisis)
    
    # Renderizar la plantilla
    return render_template(
        'mi_nuevo_addon.html',
        mi_analisis=mi_analisis,
        mi_analisis_json=mi_analisis_json,
        processed_data=processed_data
    )
=======
# Crear un blueprint para el addon
mi_addon_bp = Blueprint('mi_addon', __name__)

@mi_addon_bp.route('/mi-ruta', methods=['GET', 'POST'])
def main_view():
    """Función principal del addon"""
    try:
        # Intentar obtener datos procesados de diferentes maneras
        try:
            from app import processed_data
        except ImportError:
            # Si no se puede importar directamente, intentar desde la caché
            from config import Config
            from services.cache_manager import load_processed_data
            processed_data = load_processed_data(Config.DATA_CACHE_PATH)
            
        # Proporcionar un valor predeterminado si los datos son None
        if processed_data is None:
            flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'warning')
            processed_data = {}
            
        # Obtener la acción solicitada
        action = request.args.get('action', 'default')
        
        # === ACCIÓN 1 ===
        if action == 'accion1':
            # Lógica específica para acción 1
            return render_template(
                'accion1_template.html',
                processed_data=processed_data
            )
            
        # === ACCIÓN 2 (CON FORMULARIO) ===
        elif action == 'accion2':
            if request.method == 'POST':
                # Procesar formulario
                # ...
                flash('Formulario procesado', 'success')
                return redirect(url_for('addon_mi_addon.main_view'))
            else:
                # Mostrar formulario
                return render_template(
                    'accion2_template.html',
                    processed_data=processed_data
                )
        
        # === ACCIÓN POR DEFECTO ===
        else:
            # Obtener datos procesados
            processed_orders = processed_data.get('processed_orders', [])
            
            # Realizar análisis específico
            mi_analisis = realizar_analisis(processed_orders)
            
            # Convertir a JSON para usar en gráficos
            mi_analisis_json = json.dumps(mi_analisis)
            
            # Renderizar la plantilla principal
            return render_template(
                'mi_nuevo_addon.html',
                mi_analisis=mi_analisis,
                mi_analisis_json=mi_analisis_json,
                processed_data=processed_data
            )
            
    except Exception as e:
        print(f"Error en main_view: {str(e)}")
        return render_template(
            'mi_nuevo_addon.html',
            error=str(e),
            processed_data={}
        )
>>>>>>> Stashed changes

def realizar_analisis(orders):
    """Función que implementa el análisis específico del addon"""
    # Implementar aquí tu análisis personalizado
    return []

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('mi_nuevo_addon', {
        'name': 'Mi Nuevo Addon',
        'description': 'Descripción de la funcionalidad',
<<<<<<< Updated upstream
        'route': '/mi_ruta',
        'view_func': mi_funcion_vista,
=======
        'route': '/mi-ruta',
        'view_func': main_view,
>>>>>>> Stashed changes
        'template': 'mi_nuevo_addon.html',
        'icon': 'chart-bar',  # Icono de FontAwesome
        'active': True,
        'version': '1.0.0',
        'author': 'Tu Nombre'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

<<<<<<< Updated upstream
### 2. Crear la Plantilla HTML
=======
#### 2. Crear la Plantilla HTML Principal
>>>>>>> Stashed changes

Cada addon necesita al menos una plantilla HTML principal en el directorio `templates/`. Por ejemplo: `templates/mi_nuevo_addon.html`.

```html
{% extends 'base.html' %}

{% block title %}Mi Nuevo Addon - Analizador de Trading DAS{% endblock %}

<<<<<<< Updated upstream
{% block header %}Mi Nuevo Addon{% endblock %}
=======
{% block header %}
<div class="d-sm-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0 text-gray-800">Mi Nuevo Addon</h1>
    <a href="{{ url_for('addon_mi_nuevo_addon.main_view', action='accion1') }}" class="btn btn-primary btn-sm">
        <i class="fas fa-cog fa-sm text-white-50"></i> Acción 1
    </a>
</div>
{% endblock %}
>>>>>>> Stashed changes

{% block content %}
<div class="row">
    <!-- Contenido principal -->
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Título de la Sección</h6>
            </div>
            <div class="card-body">
                {% if error %}
                    <div class="alert alert-danger">
                        Error: {{ error }}
                    </div>
                {% endif %}
                
                <!-- Tu contenido específico -->
                <p>Contenido personalizado del addon</p>
                
                <!-- Ejemplo de visualización de datos -->
                {% if mi_analisis %}
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Campo 1</th>
                                    <th>Campo 2</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for item in mi_analisis %}
                                <tr>
                                    <td>{{ item.campo1 }}</td>
                                    <td>{{ item.campo2 }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <p class="text-center text-muted">No hay datos disponibles</p>
                {% endif %}
                
                <!-- Enlaces a otras acciones -->
                <div class="mt-4">
                    <a href="{{ url_for('addon_mi_nuevo_addon.main_view', action='accion2') }}" class="btn btn-info">
                        <i class="fas fa-edit"></i> Ir a Acción 2
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Ejemplo de gráfico -->
<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Gráfico de Ejemplo</h6>
            </div>
            <div class="card-body">
                <div class="chart-area" style="height: 400px;">
                    <canvas id="miGrafico"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Datos para los gráficos
    const miAnalisisData = {{ mi_analisis_json|default('[]')|safe }};
    
    // Configurar gráfico
    const ctx = document.getElementById('miGrafico').getContext('2d');
    new Chart(ctx, {
        type: 'bar',  // Tipo de gráfico (bar, line, pie, etc.)
        data: {
            labels: miAnalisisData.map(item => item.campo1 || ''),
            datasets: [{
                label: 'Mi Datos',
                data: miAnalisisData.map(item => item.campo2 || 0),
                backgroundColor: 'rgba(78, 115, 223, 0.8)',
                borderColor: 'rgb(78, 115, 223)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            // Otras opciones...
        }
    });
</script>
{% endblock %}
```

<<<<<<< Updated upstream
### 3. Estructura del Registro de Addons
=======
#### 3. Crear Plantillas Adicionales para Diferentes Acciones
>>>>>>> Stashed changes

Para cada acción adicional, crea una plantilla separada. Por ejemplo: `templates/accion1_template.html`.

```html
{% extends 'base.html' %}

{% block title %}Acción 1 - Mi Nuevo Addon - DAS Trader Analyzer{% endblock %}

{% block header %}
<div class="d-sm-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0 text-gray-800">Acción 1</h1>
    <a href="{{ url_for('addon_mi_nuevo_addon.main_view') }}" class="btn btn-secondary btn-sm">
        <i class="fas fa-arrow-left fa-sm text-white-50"></i> Volver
    </a>
</div>
{% endblock %}

{% block content %}
<!-- Contenido específico de la acción 1 -->
<div class="card shadow mb-4">
    <div class="card-header py-3">
        <h6 class="m-0 font-weight-bold text-primary">Detalles de Acción 1</h6>
    </div>
    <div class="card-body">
        <p>Este es el contenido específico para la Acción 1.</p>
        <!-- Más contenido... -->
    </div>
</div>
{% endblock %}
```

Y otra para la acción con formulario: `templates/accion2_template.html`.

```html
{% extends 'base.html' %}

{% block title %}Acción 2 - Mi Nuevo Addon - DAS Trader Analyzer{% endblock %}

{% block header %}
<div class="d-sm-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0 text-gray-800">Formulario - Acción 2</h1>
    <a href="{{ url_for('addon_mi_nuevo_addon.main_view') }}" class="btn btn-secondary btn-sm">
        <i class="fas fa-arrow-left fa-sm text-white-50"></i> Volver
    </a>
</div>
{% endblock %}

{% block content %}
<!-- Formulario de ejemplo -->
<div class="card shadow mb-4">
    <div class="card-header py-3">
        <h6 class="m-0 font-weight-bold text-primary">Formulario de Ejemplo</h6>
    </div>
    <div class="card-body">
        <form method="post" action="{{ url_for('addon_mi_nuevo_addon.main_view', action='accion2') }}">
            <div class="form-group">
                <label for="campo1">Campo 1</label>
                <input type="text" class="form-control" id="campo1" name="campo1" required>
            </div>
            <div class="form-group">
                <label for="campo2">Campo 2</label>
                <input type="number" class="form-control" id="campo2" name="campo2" required>
            </div>
            <button type="submit" class="btn btn-primary">Enviar</button>
            <a href="{{ url_for('addon_mi_nuevo_addon.main_view') }}" class="btn btn-secondary">Cancelar</a>
        </form>
    </div>
</div>
{% endblock %}
```

## Acceso a Datos

<<<<<<< Updated upstream
Los addons tienen acceso a los datos procesados a través del servicio de caché:
=======
Los addons tienen dos formas de acceder a los datos procesados:

### Método 1: Variable Global con Manejo Robusto (Recomendado)

```python
try:
    # Intentar obtener datos directamente
    from app import processed_data
except ImportError:
    # Si no se puede importar directamente, intentar desde la caché
    from config import Config
    from services.cache_manager import load_processed_data
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)

# Verificar que hay datos y proporcionar valor predeterminado
if processed_data is None:
    flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'warning')
    processed_data = {}

# Acceder a componentes específicos con values predeterminados
processed_orders = processed_data.get('processed_orders', [])
metrics = processed_data.get('metrics', {})
symbol_performance = processed_data.get('symbol_performance', [])
```

### Método 2: Servicio de Caché Directo
>>>>>>> Stashed changes

```python
from config import Config
from services.cache_manager import load_processed_data

# Cargar datos procesados
processed_data = load_processed_data(Config.DATA_CACHE_PATH)

# Acceder a componentes específicos
processed_orders = processed_data.get('processed_orders', [])
metrics = processed_data.get('metrics', {})
symbol_performance = processed_data.get('symbol_performance', [])
time_performance = processed_data.get('time_performance', [])
buysell_performance = processed_data.get('buysell_performance', [])
equity_curve = processed_data.get('equity_curve', [])
```

<<<<<<< Updated upstream
## Ejemplos de Addons

### Ejemplo 1: Análisis por Día de la Semana

Este addon analiza el rendimiento de trading por día de la semana.

**Archivo: addons/weekday_analysis.py**

```python
"""
Addon: Análisis por Día de la Semana
Descripción: Analiza el rendimiento de trading por día de la semana
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash
import json
from datetime import datetime

from config import Config
from services.cache_manager import load_processed_data

def analyze_by_weekday(orders):
    """Analiza rendimiento por día de la semana"""
    weekdays = {}
    
    for order in orders:
        time_str = order.get('time', '')
        if not time_str:
            continue
            
        try:
            # Probamos diferentes formatos de fecha
            try:
                dt = datetime.strptime(time_str, '%m/%d/%y %H:%M:%S')
            except ValueError:
                try:
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            
            weekday = dt.weekday()  # 0 = Lunes, 6 = Domingo
            weekday_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][weekday]
            
            if weekday_name not in weekdays:
                weekdays[weekday_name] = {
                    'totalPL': 0,
                    'totalTrades': 0,
                    'winningTrades': 0,
                    'weekday': weekday  # Guardar número para ordenar
                }
            
            weekdays[weekday_name]['totalPL'] += order.get('pnl', 0)
            weekdays[weekday_name]['totalTrades'] += 1
            if order.get('pnl', 0) > 0:
                weekdays[weekday_name]['winningTrades'] += 1
        except Exception as e:
            continue
    
    # Convertir a lista
    weekday_stats = []
    for name, stats in weekdays.items():
        win_rate = (stats['winningTrades'] / stats['totalTrades'] * 100) if stats['totalTrades'] > 0 else 0
        avg_pl = stats['totalPL'] / stats['totalTrades'] if stats['totalTrades'] > 0 else 0
        
        weekday_stats.append({
            'weekday': name,
            'weekdayNum': stats['weekday'],
            'totalPL': stats['totalPL'],
            'totalTrades': stats['totalTrades'],
            'winningTrades': stats['winningTrades'],
            'winRate': win_rate,
            'avgPL': avg_pl
        })
    
    # Ordenar por día de la semana
    weekday_stats = sorted(weekday_stats, key=lambda x: x['weekdayNum'])
    
    return weekday_stats

def weekday_analysis_view():
    """Vista para el addon de análisis por día de la semana"""
    # Obtener datos procesados usando load_processed_data
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener órdenes procesadas
    processed_orders = processed_data.get('processed_orders', [])
    
    # Realizar el análisis con los datos obtenidos
    weekday_data = analyze_by_weekday(processed_orders)
    
    # Convertir a JSON para usar en gráficos
    weekday_json = json.dumps(weekday_data)
    
    # Encontrar el mejor y peor día
    if weekday_data:
        best_day = max(weekday_data, key=lambda x: x['totalPL'])
        worst_day = min(weekday_data, key=lambda x: x['totalPL'])
        most_active_day = max(weekday_data, key=lambda x: x['totalTrades'])
    else:
        best_day = worst_day = most_active_day = None
    
    # Renderizar la plantilla
    return render_template(
        'weekday_analysis.html',
        weekday_data=weekday_data,
        weekday_json=weekday_json,
        best_day=best_day,
        worst_day=worst_day,
        most_active_day=most_active_day,
        processed_data=processed_data
    )

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('weekday_analysis', {
        'name': 'Análisis por Día',
        'description': 'Analiza el rendimiento de trading por día de la semana',
        'route': '/weekday',
        'view_func': weekday_analysis_view,
        'template': 'weekday_analysis.html',
        'icon': 'calendar-week',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

### Ejemplo 2: Sistema de Alertas de Trading

Este addon implementa un sistema de alertas basado en condiciones personalizables.

**Archivo: addons/trading_alert_addon.py**

```python
"""
Addon: Trading Alert Bot
Descripción: Sistema de alertas de trading basado en condiciones personalizables
"""
from addon_system import AddonRegistry
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
import json
from datetime import datetime, timedelta

from config import Config
from services.cache_manager import load_processed_data

# Crear un blueprint específico para las alertas
trading_alerts_bp = Blueprint('trading_alerts', __name__)

class TradingAlertSystem:
    def __init__(self):
        self.alerts = []
        self.triggered_alerts = []

    def add_alert(self, name, conditions, description):
        """Añade una nueva alerta con condiciones específicas"""
        alert = {
            'id': len(self.alerts) + 1,
            'name': name,
            'conditions': conditions,
            'description': description,
            'created_at': datetime.now(),
            'active': True
        }
        self.alerts.append(alert)
        return alert

    def check_alerts(self, orders):
        """Verifica todas las alertas contra las órdenes recientes"""
        self.triggered_alerts = []
        
        for alert in self.alerts:
            if not alert['active']:
                continue
            
            # Filtrar órdenes según condiciones de la alerta
            matching_orders = self._filter_orders(orders, alert['conditions'])
            
            if matching_orders:
                trigger_info = {
                    'alert': alert,
                    'matching_orders': matching_orders,
                    'triggered_at': datetime.now()
                }
                self.triggered_alerts.append(trigger_info)
        
        return self.triggered_alerts

    def _filter_orders(self, orders, conditions):
        """Filtra órdenes basándose en condiciones específicas"""
        matched_orders = []
        
        for order in orders:
            match = True
            
            # Condiciones de símbolo
            if 'symbol' in conditions:
                match = match and order['symb'] in conditions['symbol']
            
            # Condiciones de tipo de operación (compra/venta)
            if 'side' in conditions:
                match = match and order['B/S'] in conditions['side']
            
            # Condiciones de cantidad
            if 'min_quantity' in conditions:
                match = match and order['qty'] >= conditions['min_quantity']
            
            # Condiciones de precio
            if 'price_range' in conditions:
                min_price, max_price = conditions['price_range']
                match = match and min_price <= order['price'] <= max_price
            
            if match:
                matched_orders.append(order)
        
        return matched_orders

    def get_active_alerts(self):
        """Obtiene todas las alertas activas"""
        return [alert for alert in self.alerts if alert['active']]

    def disable_alert(self, alert_id):
        """Desactiva una alerta específica"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['active'] = False
                return True
        return False

# Instancia global del sistema de alertas
alert_system = TradingAlertSystem()

@trading_alerts_bp.route('/trading-alerts')
def trading_alerts():
    """Vista principal para gestionar alertas de trading"""
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener órdenes procesadas
    processed_orders = processed_data.get('processed_orders', [])
    
    # Verificar alertas
    triggered_alerts = alert_system.check_alerts(processed_orders)
    
    # Obtener alertas activas
    active_alerts = alert_system.get_active_alerts()
    
    return render_template(
        'trading_alerts.html',
        triggered_alerts=triggered_alerts,
        active_alerts=active_alerts,
        processed_data=processed_data
    )

@trading_alerts_bp.route('/create-alert', methods=['GET', 'POST'])
def create_alert():
    """Vista para crear nuevas alertas"""
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    # Verificar si hay datos cargados
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Recoger datos del formulario
        alert_name = request.form.get('name')
        symbol = request.form.getlist('symbol')
        side = request.form.getlist('side')
        min_quantity = float(request.form.get('min_quantity', 0))
        min_price = float(request.form.get('min_price', 0))
        max_price = float(request.form.get('max_price', float('inf')))
        
        # Construir condiciones
        conditions = {}
        if symbol:
            conditions['symbol'] = symbol
        if side:
            conditions['side'] = side
        if min_quantity > 0:
            conditions['min_quantity'] = min_quantity
        if min_price > 0 or max_price < float('inf'):
            conditions['price_range'] = (min_price, max_price)
        
        # Crear alerta
        new_alert = alert_system.add_alert(
            name=alert_name,
            conditions=conditions,
            description=f"Alerta para {', '.join(symbol)} con condiciones específicas"
        )
        
        flash(f'Alerta "{alert_name}" creada exitosamente', 'success')
        return redirect(url_for('trading_alerts.trading_alerts'))
    
    # Obtener símbolos únicos para mostrar en el formulario
    unique_symbols = set()
    for order in processed_data.get('processed_orders', []):
        if 'symb' in order and order['symb']:
            unique_symbols.add(order['symb'])
    
    return render_template(
        'create_alert.html',
        symbols=sorted(list(unique_symbols)),
        processed_data=processed_data
    )

@trading_alerts_bp.route('/disable-alert', methods=['POST'])
def disable_alert():
    """API para desactivar una alerta"""
    data = request.json
    if not data or 'alert_id' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos'})
    
    alert_id = data['alert_id']
    success = alert_system.disable_alert(alert_id)
    return jsonify({'success': success})

def register_addon():
    """Registra el addon de alertas de trading"""
    AddonRegistry.register('trading_alerts', {
        'name': 'Trading Alerts',
        'description': 'Sistema de alertas de trading con condiciones personalizables',
        'route': '/trading-alerts',
        'view_func': trading_alerts,
        'template': 'trading_alerts.html',
        'icon': 'bell',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

## Trabajando con Blueprints de Flask

Si tu addon requiere múltiples rutas, es mejor implementarlo como un Blueprint de Flask:

```python
from flask import Blueprint

# Crear un blueprint para el addon
mi_addon_bp = Blueprint('mi_addon', __name__)

@mi_addon_bp.route('/mi-ruta')
def mi_vista_principal():
    # Implementación...
    pass

@mi_addon_bp.route('/mi-ruta/detalle/<int:id>')
def detalle(id):
    # Implementación...
    pass

# Al registrar el addon:
def register_addon():
    AddonRegistry.register('mi_addon', {
        # Configuración normal...
        'view_func': mi_vista_principal,
        # Opcional: pasar blueprint directamente
        'blueprint': mi_addon_bp
    })
```

## Mejores Prácticas

1. **Modularidad**: Mantén cada addon como una unidad independiente.
2. **Manejo de Errores**: Siempre verifica que los datos estén disponibles antes de procesarlos.
3. **Documentación**: Incluye comentarios claros y documentación de funciones.
4. **Rendimiento**: Optimiza los cálculos para grandes conjuntos de datos.
5. **Encapsulación**: Evita modificar datos globales directamente.
6. **Consistencia Visual**: Mantén un estilo coherente con el resto de la aplicación.
7. **Validación de Datos**: Siempre valida los datos antes de procesarlos.
=======
## Mejores Prácticas Adicionales

1. **Modularidad**: Mantén cada addon como una unidad independiente con responsabilidades claramente definidas.

2. **Manejo de Errores**: Siempre usa bloques try/except para capturar y manejar errores de forma robusta.

3. **Valores Predeterminados**: Proporciona valores predeterminados para todos los datos que podrían ser None.

4. **URLs Correctas**: Usa siempre el formato `addon_[nombre_addon].[funcion]` en las referencias URL.

5. **Una Ruta Principal**: Usa una única ruta base con parámetros de acción para addons complejos.

6. **Validación de Datos**: Siempre valida los datos antes de procesarlos.

7. **Seguridad**: No ejecutes código no confiable o que pueda comprometer la aplicación.

8. **Documentación**: Documenta claramente el propósito, funcionalidad y uso de tu addon.

9. **Pruebas**: Implementa pruebas unitarias para tu addon para verificar su funcionamiento.

10. **Rendimiento**: Optimiza los cálculos para grandes conjuntos de datos.
>>>>>>> Stashed changes

## Depuración de Addons

Para facilitar la depuración de addons, puedes añadir mensajes de registro:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def mi_funcion():
    logger.debug("Entrando en mi_funcion()")
    logger.info("Información importante")
    logger.warning("Advertencia")
    logger.error("Error crítico")
```

<<<<<<< Updated upstream
## Conclusión

El sistema de addons de DAS Trader Analyzer proporciona una forma flexible y potente de extender la funcionalidad de la aplicación. Siguiendo esta guía, puedes crear addons que se integren perfectamente con la aplicación principal y proporcionen nuevas características a los usuarios.
=======
También puedes aprovechar los mensajes de depuración incorporados en la aplicación:

```python
# Agregar mensajes de depuración
print("[DEBUG] Entrando en main_view()")
print(f"[DEBUG] Processed data: {processed_data is not None}")
```

## Resolución de Problemas Comunes

### 1. Error: "Could not build url for endpoint..."

**Problema**: No se puede construir la URL para un endpoint del addon.

**Solución**: Asegúrate de usar el formato correcto con el prefijo `addon_`:
```html
<!-- Incorrecto -->
<a href="{{ url_for('mi_addon.main_view') }}">Enlace</a>

<!-- Correcto -->
<a href="{{ url_for('addon_mi_addon.main_view') }}">Enlace</a>
```

### 2. Error: "Ruta '/mi-ruta' ya registrada..."

**Problema**: Conflicto de rutas entre addons.

**Solución**: Usa rutas únicas para cada addon y verifica que no exista otro addon con la misma ruta:
```python
# Usa un prefijo único para tu addon
route = '/mi-prefijo-mi-ruta'
```

### 3. Error: Addon no aparece en la barra lateral

**Problema**: El addon se registra pero no aparece en la barra lateral.

**Solución**: Verifica que 'active' esté configurado como True en el registro del addon:
```python
AddonRegistry.register('mi_addon', {
    # ... otras propiedades ...
    'active': True
})
```

### 4. Error: Los datos procesados son None

**Problema**: Los datos procesados no están disponibles.

**Solución**: Implementa un manejo robusto con valores predeterminados:
```python
try:
    from app import processed_data
except ImportError:
    processed_data = None

if processed_data is None:
    processed_data = {}  # Valor predeterminado vacío
```

## Conclusión

El sistema de addons de DAS Trader Analyzer proporciona una forma flexible y potente de extender la funcionalidad de la aplicación. Siguiendo las pautas y mejores prácticas de esta documentación, podrás crear addons robustos y funcionales que se integren perfectamente con la aplicación principal.
>>>>>>> Stashed changes

## Referencia Rápida

### Estructura de Archivos
- `addon_system.py`: Sistema central de addons
- `addons/`: Directorio de addons
- `templates/`: Directorio de plantillas HTML

### Función Principal de Registro
```python
AddonRegistry.register('nombre_clave', {
    'name': 'Nombre Visible',
    'description': 'Descripción',
    'route': '/ruta',
    'view_func': funcion_vista,
    'template': 'plantilla.html',
    'icon': 'icono',
    'active': True,
    'version': '1.0.0',
    'author': 'Autor'
})
```

### Patrón Recomendado
```python
<<<<<<< Updated upstream
from config import Config
from services.cache_manager import load_processed_data

processed_data = load_processed_data(Config.DATA_CACHE_PATH)
processed_orders = processed_data.get('processed_orders', [])
=======
@addon_bp.route('/mi-ruta')
def main_view():
    """Función principal del addon"""
    try:
        # Obtener datos procesados (manejo robusto)
        try:
            from app import processed_data
        except ImportError:
            from config import Config
            from services.cache_manager import load_processed_data
            processed_data = load_processed_data(Config.DATA_CACHE_PATH)
            
        if processed_data is None:
            processed_data = {}
            
        # Obtener acción
        action = request.args.get('action', 'default')
        
        # Manejar diferentes acciones
        if action == 'accion1':
            # Lógica para acción 1
        elif action == 'accion2':
            # Lógica para acción 2
        else:
            # Acción por defecto
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Manejo de errores y vista fallback
```

### Referencias URL en Plantillas
```html
<!-- Formato correcto para URL -->
<a href="{{ url_for('addon_mi_addon.main_view') }}">Principal</a>
<a href="{{ url_for('addon_mi_addon.main_view', action='accion1') }}">Acción 1</a>
<a href="{{ url_for('addon_mi_addon.main_view', action='accion2', param='valor') }}">Acción 2</a>
>>>>>>> Stashed changes
```
