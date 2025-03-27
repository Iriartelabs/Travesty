# Guía de Desarrollo de Addons para DAS Trader Analyzer

## Introducción

Este documento detalla cómo desarrollar addons para la aplicación DAS Trader Analyzer, explicando la arquitectura del sistema de addons, su integración con la aplicación principal y cómo crear nuevos addons tanto de forma manual como usando la interfaz de usuario integrada.

## Arquitectura de la Aplicación

DAS Trader Analyzer es una aplicación Flask modularizada que analiza datos de trading exportados desde DAS Trader. La estructura principal incluye:

- **app.py**: Punto de entrada principal que inicializa la aplicación y mantiene una variable global `processed_data`
- **routes/**: Contiene los blueprints para las diferentes secciones de la aplicación
- **services/**: Servicios para procesamiento de datos, caché y manejo de archivos
- **templates/**: Plantillas HTML para la interfaz de usuario
- **static/**: Archivos estáticos (CSS, JavaScript, uploads)
- **addons/**: Directorio donde se almacenan los addons
- **addon_system.py**: Sistema central que gestiona el registro, carga y creación de addons

## Sistema de Addons

El sistema de addons permite extender la funcionalidad de la aplicación sin modificar el código principal. Está implementado a través de un registro centralizado que gestiona los addons disponibles y proporciona herramientas tanto programáticas como visuales para su creación y gestión.

### Estructura del Sistema

1. **AddonRegistry**: Clase singleton en `addon_system.py` que mantiene un registro de todos los addons, con métodos para:
   - Registrar addons
   - Verificar duplicados de rutas
   - Inicializar rutas en Flask
   - Proporcionar elementos para la barra lateral

2. **load_addons_from_directory()**: Función que carga automáticamente todos los addons desde el directorio `addons/`.

3. **create_addon_template()**: Función para generar automáticamente plantillas de nuevos addons.

4. **Integración con Flask**: Los addons se registran como blueprints de Flask y se integran con el contexto global de la aplicación.

## Cómo Desarrollar un Nuevo Addon

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
5. Modifica los archivos generados:
   - `addons/mi_addon.py`: Para la lógica de negocio
   - `templates/mi_addon.html`: Para la interfaz de usuario

### Método 2: Crear un Addon Manualmente

#### 1. Crear el Archivo del Addon

Cada addon es un archivo Python (.py) ubicado en el directorio `addons/`. Por ejemplo: `addons/mi_nuevo_addon.py`.

```python
"""
Addon: Nombre del Addon
Descripción: Breve descripción de la funcionalidad
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash
import json

def mi_funcion_vista():
    """Función principal del addon"""
    # Hay dos formas de obtener los datos procesados:
    
    # Método 1: Importando directamente desde app.py (recomendado)
    from app import processed_data
    
    # Método 2: Cargando desde caché (alternativo)
    # from config import Config
    # from services.cache_manager import load_processed_data
    # processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
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

def realizar_analisis(orders):
    """Función que implementa el análisis específico del addon"""
    # Implementar aquí tu análisis personalizado
    return []

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('mi_nuevo_addon', {
        'name': 'Mi Nuevo Addon',
        'description': 'Descripción de la funcionalidad',
        'route': '/mi-ruta',
        'view_func': mi_funcion_vista,
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

#### 2. Crear la Plantilla HTML

Cada addon necesita una plantilla HTML en el directorio `templates/`. Por ejemplo: `templates/mi_nuevo_addon.html`.

```html
{% extends 'base.html' %}

{% block title %}Mi Nuevo Addon - Analizador de Trading DAS{% endblock %}

{% block header %}
<div class="d-sm-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0 text-gray-800">Mi Nuevo Addon</h1>
</div>
{% endblock %}

{% block content %}
<div class="row">
    <!-- Contenido principal -->
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Título de la Sección</h6>
            </div>
            <div class="card-body">
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
    const miAnalisisData = {{ mi_analisis_json|safe }};
    
    // Configurar gráfico
    const ctx = document.getElementById('miGrafico').getContext('2d');
    new Chart(ctx, {
        type: 'bar',  // Tipo de gráfico (bar, line, pie, etc.)
        data: {
            labels: miAnalisisData.map(item => item.campo1),
            datasets: [{
                label: 'Mi Datos',
                data: miAnalisisData.map(item => item.campo2),
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

### Estructura del Registro de Addons

Al registrar un addon en el sistema, se debe proporcionar un diccionario con los siguientes datos:

```python
AddonRegistry.register('nombre_clave', {
    'name': 'Nombre Mostrado',           # Nombre visible en la UI
    'description': 'Descripción',        # Descripción breve
    'route': '/ruta_url',                # URL de acceso al addon
    'view_func': funcion_vista,          # Función principal que maneja la vista
    'template': 'plantilla.html',        # Nombre del archivo de plantilla
    'icon': 'icono-fontawesome',         # Icono de FontAwesome (sin 'fa-')
    'active': True,                      # Estado activo/inactivo
    'version': '1.0.0',                  # Versión del addon
    'author': 'Autor'                    # Nombre del autor
})
```

## Acceso a Datos

Los addons tienen dos formas de acceder a los datos procesados:

### Método 1: Variable Global (Recomendado)

```python
from app import processed_data

# Verificar que hay datos
if processed_data is None:
    flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
    return redirect(url_for('main.index'))

# Acceder a componentes específicos
processed_orders = processed_data.get('processed_orders', [])
```

### Método 2: Servicio de Caché

```python
from config import Config
from services.cache_manager import load_processed_data

# Cargar datos procesados
processed_data = load_processed_data(Config.DATA_CACHE_PATH)

# Verificar que hay datos
if processed_data is None:
    flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
    return redirect(url_for('main.index'))
```

### Componentes Disponibles en los Datos Procesados

```python
# Acceder a componentes específicos
processed_orders = processed_data.get('processed_orders', [])
metrics = processed_data.get('metrics', {})
symbol_performance = processed_data.get('symbol_performance', [])
time_performance = processed_data.get('time_performance', [])
buysell_performance = processed_data.get('buysell_performance', [])
equity_curve = processed_data.get('equity_curve', [])
```

## Componentes Avanzados Disponibles

El sistema incluye varias clases para análisis técnico, detección de patrones, backtesting y gestión de riesgo que puedes utilizar en tus addons.

### Indicadores Técnicos

```python
from addons.trading_alert_addon import TradingIndicators

# Calcular Media Móvil Simple (SMA)
sma_values = TradingIndicators.sma(price_data, period=20)

# Calcular Media Móvil Exponencial (EMA)
ema_values = TradingIndicators.ema(price_data, period=20)

# Calcular RSI
rsi_values = TradingIndicators.rsi(price_data, period=14)

# Calcular MACD
macd_result = TradingIndicators.macd(price_data, fast_period=12, slow_period=26, signal_period=9)
macd_line = macd_result['macd_line']
signal_line = macd_result['signal_line']
histogram = macd_result['histogram']

# Calcular Bandas de Bollinger
bollinger = TradingIndicators.bollinger_bands(price_data, period=20, num_std=2)
middle_band = bollinger['middle']
upper_band = bollinger['upper']
lower_band = bollinger['lower']

# Calcular niveles de soporte y resistencia
levels = TradingIndicators.support_resistance(price_data, window=10)
resistance_levels = levels['resistance']
support_levels = levels['support']
```

### Detección de Patrones

```python
from addons.trading_alert_addon import TradingPatterns

# Detectar patrón de doble techo
is_double_top, first_peak_idx, second_peak_idx = TradingPatterns.detect_double_top(price_data, tolerance=0.02)

# Detectar patrón de doble suelo
is_double_bottom, first_bottom_idx, second_bottom_idx = TradingPatterns.detect_double_bottom(price_data, tolerance=0.02)

# Detectar patrón de cabeza y hombros
is_head_shoulders, peak_indices = TradingPatterns.detect_head_and_shoulders(price_data, tolerance=0.03)
```

### Backtesting de Estrategias

```python
from addons.trading_alert_addon import BacktestEngine

# Ejecutar backtest de estrategia de cruce de medias móviles
results = BacktestEngine.test_strategy(
    price_data,
    BacktestEngine.sma_crossover_strategy, 
    short_period=20,
    long_period=50
)

# Ejecutar backtest de estrategia de RSI
results = BacktestEngine.test_strategy(
    price_data,
    BacktestEngine.rsi_strategy, 
    period=14,
    overbought=70,
    oversold=30
)

# Acceder a los resultados
total_trades = results['total_trades']
win_rate = results['win_rate']
max_drawdown = results['max_drawdown']
total_return = results['total_return']
equity_curve = results['equity_curve']
```

### Gestión de Riesgo

```python
from addons.trading_alert_addon import RiskManager

# Calcular tamaño de posición según gestión de riesgo
position_info = RiskManager.calculate_position_size(
    account_size=10000,       # Tamaño de cuenta en dólares
    risk_percentage=1,        # Porcentaje de riesgo (1%)
    entry_price=150.75,       # Precio de entrada
    stop_loss=148.50          # Precio de stop loss
)

# Acceder a la información calculada
position_size = position_info['position_size']       # Cantidad de acciones
position_value = position_info['position_value']     # Valor total de la posición
risk_amount = position_info['risk_amount']           # Cantidad en riesgo (dólares)
direction = position_info['direction']               # LONG o SHORT
```

## Ejemplos de Addons Avanzados

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
    # Obtener datos procesados desde la variable global
    from app import processed_data
    
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

### Ejemplo 2: Addon Avanzado con Múltiples Rutas

Para addons más complejos con múltiples rutas, es mejor utilizar un Blueprint de Flask:

```python
"""
Addon: Analytics Suite
Descripción: Suite de herramientas avanzadas de análisis de trading
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
import json
import pandas as pd
import numpy as np
from addon_system import AddonRegistry
from addons.trading_alert_addon import TradingIndicators, BacktestEngine

# Crear un blueprint para el addon
analytics_suite_bp = Blueprint('analytics_suite', __name__)

@analytics_suite_bp.route('/analytics')
def analytics_main():
    """Vista principal del addon"""
    from app import processed_data
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Implementación...
    return render_template('analytics_suite.html', processed_data=processed_data)

@analytics_suite_bp.route('/analytics/performance')
def performance_metrics():
    """Métricas avanzadas de rendimiento"""
    from app import processed_data
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Implementación...
    return render_template('analytics_performance.html', processed_data=processed_data)

@analytics_suite_bp.route('/analytics/correlations')
def correlations():
    """Análisis de correlaciones"""
    from app import processed_data
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Implementación...
    return render_template('analytics_correlations.html', processed_data=processed_data)

@analytics_suite_bp.route('/analytics/api/data', methods=['GET'])
def api_get_data():
    """API para obtener datos en formato JSON"""
    from app import processed_data
    
    if processed_data is None:
        return jsonify({'error': 'No hay datos disponibles'})
    
    data_type = request.args.get('type', 'equity')
    
    if data_type == 'equity':
        return jsonify(processed_data.get('equity_curve', []))
    elif data_type == 'symbols':
        return jsonify(processed_data.get('symbol_performance', []))
    else:
        return jsonify({'error': 'Tipo de datos no válido'})

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('analytics_suite', {
        'name': 'Analytics Suite',
        'description': 'Suite de herramientas avanzadas de análisis de trading',
        'route': '/analytics',
        'view_func': analytics_main,
        'template': 'analytics_suite.html',
        'icon': 'chart-line',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team',
        'blueprint': analytics_suite_bp  # Pasar blueprint directamente
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

## Mejores Prácticas

1. **Modularidad**: Mantén cada addon como una unidad independiente.
2. **Manejo de Errores**: Siempre verifica que los datos estén disponibles antes de procesarlos.
3. **Documentación**: Incluye comentarios claros y documentación de funciones.
4. **Rendimiento**: Optimiza los cálculos para grandes conjuntos de datos.
5. **Encapsulación**: Evita modificar datos globales directamente.
6. **Consistencia Visual**: Mantén un estilo coherente con el resto de la aplicación.
7. **Validación de Datos**: Siempre valida los datos antes de procesarlos.
8. **Blueprints**: Para addons complejos, usa Blueprints de Flask.
9. **Seguridad**: No ejecutes código no confiable o que pueda comprometer la aplicación.
10. **Pruebas**: Implementa pruebas unitarias para tu addon.

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

También puedes aprovechar los mensajes de depuración incorporados en la aplicación:

```python
# Agregar mensajes de depuración
print("[DEBUG] Entrando en mi_funcion_vista()")
print(f"[DEBUG] Processed data: {processed_data is not None}")
```

## Uso de Componentes Avanzados

### Crear un Addon con Indicadores Técnicos

```python
"""
Addon: Indicadores Técnicos
Descripción: Visualización de indicadores técnicos para análisis de precio
"""
from addon_system import AddonRegistry
from flask import render_template, redirect, url_for, flash, request
import json
import pandas as pd
import numpy as np
from addons.trading_alert_addon import TradingIndicators

def technical_indicators_view():
    """Vista principal para el addon de indicadores técnicos"""
    from app import processed_data
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener parámetros
    symbol = request.args.get('symbol', None)
    indicator = request.args.get('indicator', 'sma')
    
    # Obtener símbolos disponibles
    symbols = set()
    for order in processed_data.get('processed_orders', []):
        if 'symb' in order and order['symb']:
            symbols.add(order['symb'])
    symbols = sorted(list(symbols))
    
    # Si no se especifica un símbolo, usar el primero disponible
    if not symbol and symbols:
        symbol = symbols[0]
    
    if not symbol:
        flash('No hay símbolos disponibles para análisis', 'warning')
        return render_template(
            'technical_indicators.html',
            symbols=symbols,
            processed_data=processed_data
        )
    
    # Filtrar órdenes por símbolo
    symbol_orders = [order for order in processed_data.get('processed_orders', []) 
                    if order.get('symb') == symbol]
    
    # Ordenar por fecha
    symbol_orders = sorted(symbol_orders, key=lambda x: x.get('time', ''))
    
    # Crear serie de precios para análisis técnico
    if symbol_orders:
        # Crear una serie de precios básica para análisis
        try:
            # Extraer fechas y precios
            dates = []
            prices = []
            for order in symbol_orders:
                try:
                    date_str = order.get('time', '')
                    dates.append(date_str)
                    prices.append(order.get('price', 0))
                except:
                    continue
            
            # Crear serie de pandas
            price_data = pd.Series(prices, index=dates)
            
            # Calcular indicadores según selección
            indicators_data = {}
            
            if indicator == 'sma':
                # Calcular SMA con diferentes períodos
                indicators_data['sma20'] = TradingIndicators.sma(price_data, period=20).tolist()
                indicators_data['sma50'] = TradingIndicators.sma(price_data, period=50).tolist()
                indicators_data['sma200'] = TradingIndicators.sma(price_data, period=200).tolist()
            
            elif indicator == 'ema':
                # Calcular EMA con diferentes períodos
                indicators_data['ema12'] = TradingIndicators.ema(price_data, period=12).tolist()
                indicators_data['ema26'] = TradingIndicators.ema(price_data, period=26).tolist()
                indicators_data['ema50'] = TradingIndicators.ema(price_data, period=50).tolist()
            
            elif indicator == 'bollinger':
                # Calcular Bandas de Bollinger
                bollinger = TradingIndicators.bollinger_bands(price_data, period=20, num_std=2)
                indicators_data['middle'] = bollinger['middle'].tolist()
                indicators_data['upper'] = bollinger['upper'].tolist()
                indicators_data['lower'] = bollinger['lower'].tolist()
            
            elif indicator == 'rsi':
                # Calcular RSI
                indicators_data['rsi'] = TradingIndicators.rsi(price_data, period=14).tolist()
            
            elif indicator == 'macd':
                # Calcular MACD
                macd_data = TradingIndicators.macd(price_data, fast_period=12, slow_period=26, signal_period=9)
                indicators_data['macd'] = macd_data['macd_line'].tolist()
                indicators_data['signal'] = macd_data['signal_line'].tolist()
                indicators_data['histogram'] = macd_data['histogram'].tolist()
            
            # Preparar datos para gráficos
            chart_data = {
                'dates': dates,
                'prices': prices,
                'indicators': indicators_data,
                'indicator_type': indicator
            }
            
            # Convertir a JSON para usar en gráficos
            chart_json = json.dumps(chart_data)
            
            return render_template(
                'technical_indicators.html',
                symbol=symbol,
                symbols=symbols,
                chart_data=chart_data,
                chart_json=chart_json,
                indicator=indicator,
                processed_data=processed_data
            )
            
        except Exception as e:
            flash(f'Error al calcular indicadores: {str(e)}', 'error')
    
    return render_template(
        'technical_indicators.html',
        symbol=symbol,
        symbols=symbols,
        indicator=indicator,
        processed_data=processed_data
    )

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('technical_indicators', {
        'name': 'Indicadores Técnicos',
        'description': 'Visualización de indicadores técnicos para análisis de precio',
        'route': '/technical-indicators',
        'view_func': technical_indicators_view,
        'template': 'technical_indicators.html',
        'icon': 'chart-line',
        'active': True,
        'version': '1.0.0',
        'author': 'DAS Trader Analyzer Team'
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

## Conclusión

El sistema de addons de DAS Trader Analyzer proporciona una forma flexible y potente de extender la funcionalidad de la aplicación. Con los nuevos componentes avanzados y la interfaz de gestión, puedes crear fácilmente addons personalizados para mejorar tu análisis de trading.

## Referencia Rápida

### Estructura de Archivos
- `addon_system.py`: Sistema central de addons con registro y creación de plantillas
- `addons/`: Directorio de addons
- `templates/`: Directorio de plantillas HTML

### Métodos Principales
```python
# Registrar addon
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

# Cargar addons desde directorio
load_addons_from_directory()

# Crear plantilla de addon
create_addon_template(name, route, description, icon)
```

### Acceso a Datos Procesados
```python
# Método 1: Variable global
from app import processed_data

# Método 2: Caché
from config import Config
from services.cache_manager import load_processed_data
processed_data = load_processed_data(Config.DATA_CACHE_PATH)
```

### Utilidades para Análisis Técnico
```python
# Importar clases de utilidades
from addons.trading_alert_addon import TradingIndicators, TradingPatterns, BacktestEngine, RiskManager

# Ejemplo: Calcular SMA
sma_values = TradingIndicators.sma(price_data, period=20)

# Ejemplo: Ejecutar backtest
results = BacktestEngine.test_strategy(price_data, BacktestEngine.sma_crossover_strategy, short_period=20, long_period=50)

# Ejemplo: Calcular posición
position_info = RiskManager.calculate_position_size(account_size=10000, risk_percentage=1, entry_price=150, stop_loss=145)
```
