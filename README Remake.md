# Travesty Analyzer

![Estado del Proyecto](https://img.shields.io/badge/Estado-Activo-brightgreen)
![Versión](https://img.shields.io/badge/Versión-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.6+-yellow)
![Flask](https://img.shields.io/badge/Flask-2.3.2-lightgrey)

Una aplicación web modular para analizar datos de trading exportados desde DAS Trader, proporcionando visualizaciones interactivas, métricas clave y un sistema extensible de addons para análisis personalizados.

## 🚀 Características

- **Dashboard completo** con métricas clave de rendimiento
- **Organización temporal** de archivos de trading por fecha
- **Detección automática** de la fecha de los datos
- **Sistema de addons modular** para extender la funcionalidad
- **Gestión completa de addons** (activación, desactivación, desinstalación)
- **Versionado semántico** de addons
- **Interfaz intuitiva** con diseño responsive

## 🔧 Tecnologías

- **Backend**: Python, Flask
- **Procesamiento de datos**: Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualización**: Chart.js
- **Diseño**: Bootstrap 5
- **Iconos**: Font Awesome

## 📋 Requisitos

- Python 3.6+
- Flask 2.3.2
- Pandas 2.0.1
- NumPy 1.24.3
- Otras dependencias listadas en `requirements.txt`

## 🔌 Instalación

1. **Clonar este repositorio**

```bash
git clone https://github.com/tu-usuario/travesty-analyzer.git
cd travesty-analyzer
```

2. **Crear y activar un entorno virtual**

```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configuración**

La aplicación utiliza una estructura de configuración basada en entornos (desarrollo, producción). Puedes modificar la configuración en `config.py`.

## 💻 Uso

1. **Iniciar la aplicación**

```bash
python app.py
```

2. **Acceder a la aplicación**

Abre tu navegador y visita `http://localhost:5000`

3. **Cargar datos**

- Utiliza la sección "Upload" para subir tu archivo CSV de trading
- La aplicación detectará automáticamente la fecha del archivo o puedes especificarla manualmente
- Los archivos se organizan por fecha para facilitar análisis históricos

## 📊 Dashboard

El dashboard principal muestra métricas clave sobre tus operaciones de trading:

- Número total de operaciones
- P&L Total
- Win Rate
- Ratio de operaciones ganadoras vs perdedoras
- Profit Factor
- Ganancias y pérdidas promedio

## 🧩 Sistema de Addons

La aplicación incluye un poderoso sistema de addons que permite extender la funcionalidad sin modificar el código principal.

### Estructura de un Addon

Cada addon está organizado en su propio directorio con la siguiente estructura:

```
addons/nombre_addon/
├── src/
│   └── nombre_addon.py  # Código Python del addon
└── ui/
    └── nombre_addon.html  # Plantillas HTML del addon
```

### Gestión de Addons

La aplicación proporciona una interfaz completa para:

- Crear nuevos addons
- Importar addons desde archivos ZIP
- Exportar addons para compartir
- Activar/desactivar addons
- Desinstalar addons

### Versionado de Addons

Los addons utilizan versionado semántico (MAYOR.MENOR.PARCHE). Al importar un addon, la aplicación verifica automáticamente si la versión es superior a la instalada, evitando reemplazar versiones más recientes.

### Crear un nuevo addon

1. Ve a la sección "Gestionar Addons"
2. Utiliza el formulario "Crear Nuevo Addon"
3. Especifica nombre, ruta (opcional), descripción e icono
4. Edita los archivos generados para implementar tu funcionalidad personalizada

## 📁 Estructura del Proyecto

```
travesty-analyzer/
├── app.py                 # Aplicación principal
├── config.py              # Configuración
├── addon_system.py        # Sistema de gestión de addons
├── extensions.py          # Extensiones Flask
│
├── addons/                # Carpeta para addons
│   └── nombre_addon/      # Ejemplo de addon
│       ├── src/           # Código Python
│       └── ui/            # Plantillas HTML
│
├── routes/                # Controladores y rutas
│   ├── __init__.py
│   ├── main.py            # Rutas principales
│   └── analysis.py        # Rutas de análisis y addons
│
├── services/              # Servicios de la aplicación
│   ├── __init__.py
│   ├── data_processor.py  # Procesamiento de datos
│   ├── cache_manager.py   # Gestión de caché
│   ├── file_handler.py    # Manejo de archivos
│   └── trades_manager.py  # Gestión de datos de trading
│
├── templates/             # Plantillas HTML
│   ├── base.html          # Plantilla base
│   ├── index.html         # Dashboard
│   ├── upload.html        # Carga de archivos
│   └── manage_addons.html # Gestión de addons
│
├── static/                # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   └── uploads/           # Carpeta para archivos temporales
│
├── data/                  # Directorio para datos
│   ├── trades/            # Datos organizados por fecha
│   │   ├── index.json     # Índice de archivos importados
│   │   └── YYYY/MM/DD/    # Estructura de carpetas por fecha
│   └── processed_cache.pkl # Caché de datos procesados
│
└── requirements.txt       # Dependencias
```

## 🛠️ Despliegue

### Servidor web con Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker (próximamente)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes, por favor abre primero un issue para discutir lo que te gustaría cambiar.

1. Haz un fork del proyecto
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Confirma tus cambios (`git commit -m 'Añade nueva característica'`)
4. Empuja a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

---

# Guía de Desarrollo de Addons para Travesty Analyzer

## Introducción

Los addons son extensiones que permiten añadir nuevas funcionalidades a Travesty Analyzer sin modificar el código principal. Gracias a su arquitectura modular, puedes crear análisis personalizados, visualizaciones específicas o integraciones con otras herramientas.

## 1. Estructura de un Addon

Cada addon se organiza en su propia carpeta con una estructura específica:

```
addons/
└── nombre_addon/
    ├── src/
    │   └── nombre_addon.py     # Código Python (lógica del addon)
    └── ui/
        └── nombre_addon.html   # Plantilla HTML (interfaz de usuario)
```

Esta estructura separa claramente la lógica de negocio de la interfaz de usuario, facilitando el desarrollo y mantenimiento.

## 2. Creación de un Nuevo Addon

### 2.1 Usando la Interfaz de Usuario

La forma más sencilla de crear un nuevo addon es utilizar la interfaz de gestión de addons:

1. Ve a la sección "Gestionar Addons"
2. Utiliza el formulario "Crear Nuevo Addon"
3. Completa los campos:
   - **Nombre**: Nombre descriptivo del addon (aparecerá en el menú)
   - **Ruta** (opcional): URL personalizada (si no se especifica, se generará automáticamente)
   - **Descripción**: Breve descripción de la funcionalidad
   - **Icono**: Nombre del icono de FontAwesome (sin el prefijo "fa-")

Esto generará automáticamente la estructura básica del addon con archivos plantilla que puedes personalizar.

### 2.2 Creación Manual

También puedes crear manualmente la estructura y archivos:

1. Crea la carpeta principal: `addons/nombre_addon/`
2. Crea las subcarpetas: `src/` y `ui/`
3. Crea el archivo Python: `src/nombre_addon.py`
4. Crea la plantilla HTML: `ui/nombre_addon.html`

## 3. Desarrollo del Addon

### 3.1 Archivo Python (`nombre_addon.py`)

El archivo Python contiene la lógica de tu addon. Su estructura básica es:

```python
"""
Addon: Nombre del Addon
Descripción: Descripción breve del addon
Versión: 1.0.0
Autor: Tu Nombre
"""
from addon_system import AddonRegistry, custom_render_template
from flask import redirect, url_for, flash, request
import json

from config import Config
from services.cache_manager import load_processed_data

def nombre_addon_view():
    """Función principal del addon"""
    # Obtener datos procesados
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles. Por favor, sube los archivos primero.', 'error')
        return redirect(url_for('main.index'))
    
    # Implementar tu lógica personalizada aquí
    # Por ejemplo:
    trades = processed_data.get('processed_trades', [])
    
    # Realizar cálculos o análisis específicos
    result = analizar_datos(trades)
    
    # Renderizar la plantilla
    return custom_render_template(
        'nombre_addon',  # ID del addon
        'nombre_addon.html',  # Nombre del archivo HTML
        processed_data=processed_data,
        result=result  # Pasar tus datos procesados
    )

def analizar_datos(trades):
    """Ejemplo de función de análisis personalizada"""
    # Implementa tu análisis aquí
    return {
        'dato1': 123,
        'dato2': 'valor'
    }

def register_addon():
    """Registra este addon en el sistema"""
    AddonRegistry.register('nombre_addon', {
        'name': 'Nombre del Addon',
        'description': 'Descripción breve del addon',
        'route': '/nombre-addon',  # URL donde estará disponible
        'view_func': nombre_addon_view,  # Función que procesa la solicitud
        'template': 'nombre_addon.html',  # Plantilla HTML principal
        'icon': 'chart-bar',  # Icono de FontAwesome (sin 'fa-')
        'active': True,  # Estado inicial (activo/inactivo)
        'version': '1.0.0',  # Versión semántica (MAYOR.MENOR.PARCHE)
        'author': 'Tu Nombre'  # Autor del addon
    })

# Registrar automáticamente al importar
if __name__ != '__main__':
    register_addon()
```

### 3.2 Plantilla HTML (`nombre_addon.html`)

La plantilla HTML define la interfaz de usuario de tu addon:

```html
{% extends 'base.html' %}

{% block title %}Nombre del Addon - Travesty Analyzer{% endblock %}

{% block header %}Nombre del Addon{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Título de la Sección</h6>
            </div>
            <div class="card-body">
                <!-- Tu contenido personalizado aquí -->
                <p>Este addon muestra un análisis personalizado de tus datos de trading.</p>
                
                <!-- Ejemplo de acceso a datos -->
                {% if processed_data and processed_data.metrics %}
                <div class="alert alert-info">
                    <p>Operaciones totales: {{ processed_data.metrics.total_trades }}</p>
                    <p>Win Rate: {{ processed_data.metrics.win_rate|format_percent }}</p>
                </div>
                {% endif %}
                
                <!-- Ejemplo de acceso a resultados personalizados -->
                {% if result %}
                <div class="alert alert-success">
                    <p>Dato 1: {{ result.dato1 }}</p>
                    <p>Dato 2: {{ result.dato2 }}</p>
                </div>
                {% endif %}
                
                <!-- Ejemplo de gráfico con Chart.js -->
                <div style="height: 300px;">
                    <canvas id="myChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<!-- Scripts personalizados -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Ejemplo de creación de un gráfico
    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Rojo', 'Azul', 'Amarillo', 'Verde', 'Púrpura', 'Naranja'],
            datasets: [{
                label: 'Ejemplo de Datos',
                data: [12, 19, 3, 5, 2, 3],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
</script>
{% endblock %}
```

## 4. Acceso a Datos

Tu addon tiene acceso a los datos procesados de trading a través de la variable `processed_data`, que contiene:

- `processed_trades`: Lista de operaciones procesadas
- `metrics`: Métricas generales (total_trades, win_rate, etc.)
- `date_info`: Información de la fecha de los datos

Para acceder a estos datos:

```python
# En el archivo Python
processed_data = load_processed_data(Config.DATA_CACHE_PATH)

trades = processed_data.get('processed_trades', [])
metrics = processed_data.get('metrics', {})
```

```html
<!-- En la plantilla HTML -->
<p>Total de operaciones: {{ processed_data.metrics.total_trades }}</p>
<p>Ganancia total: ${{ processed_data.metrics.total_pnl|format_number }}</p>
```

## 5. Renderización de Plantillas

Para renderizar una plantilla HTML desde tu addon, usa la función `custom_render_template`:

```python
return custom_render_template(
    'nombre_addon',         # ID del addon
    'nombre_addon.html',    # Nombre del archivo HTML dentro de /ui
    variable1=valor1,       # Variables para la plantilla
    variable2=valor2
)
```

Esta función busca automáticamente la plantilla en la carpeta `ui/` de tu addon.

## 6. Versionado de Addons

Travesty Analyzer utiliza versionado semántico para los addons (MAYOR.MENOR.PARCHE):

1. **MAYOR**: Cambios incompatibles con versiones anteriores
2. **MENOR**: Nuevas funcionalidades manteniendo compatibilidad
3. **PARCHE**: Correcciones de errores

Al importar un addon, la aplicación verifica si la versión es superior a la instalada, evitando reemplazos accidentales de versiones más recientes.

```python
# Ejemplo de actualización de versión
'version': '1.2.3',  # Versión inicial
'version': '1.2.4',  # Corrección de errores
'version': '1.3.0',  # Nueva funcionalidad
'version': '2.0.0',  # Cambios incompatibles
```

## 7. Mejores Prácticas

Para desarrollar addons de alta calidad:

1. **Sigue la estructura recomendada** para facilitar la instalación y compatibilidad
2. **Usa versionado semántico** para una gestión clara de actualizaciones
3. **Incluye documentación adecuada** en el código y en la interfaz de usuario
4. **Maneja errores apropiadamente** para evitar que tu addon interrumpa la aplicación
5. **Proporciona retroalimentación visual** sobre el progreso de operaciones largas
6. **Respeta la interfaz de usuario principal** para mantener la coherencia visual
7. **Usa las herramientas disponibles** como Bootstrap, Chart.js y FontAwesome

## 8. Distribución de Addons

Para compartir tu addon con otros usuarios:

1. Ve a la sección "Gestionar Addons"
2. Encuentra tu addon en la lista
3. Selecciona "Exportar" en el menú de acciones
4. Se descargará un archivo ZIP con toda la estructura de tu addon
5. Comparte este archivo con otros usuarios, que pueden importarlo desde la sección "Gestionar Addons"

## 9. API Disponible

Tu addon puede utilizar las siguientes funciones y clases:

```python
# Sistema de addons
from addon_system import AddonRegistry, custom_render_template

# Configuración y caché
from config import Config
from services.cache_manager import load_processed_data, save_processed_data

# Frameworks y bibliotecas
from flask import redirect, url_for, flash, request, session
import pandas as pd
import numpy as np
import json
import datetime
```

## 10. Ejemplos de Addons

### 10.1 Addon de Análisis de Sesión

#### Archivo Python (`session_analysis.py`):

```python
def session_analysis_view():
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles', 'error')
        return redirect(url_for('main.index'))
    
    trades = processed_data.get('processed_trades', [])
    
    # Dividir operaciones en sesiones
    morning_trades = []
    afternoon_trades = []
    
    for trade in trades:
        if 'time' in trade:
            try:
                time_obj = datetime.strptime(trade['time'], '%Y-%m-%d %H:%M:%S')
                if time_obj.hour < 12:
                    morning_trades.append(trade)
                else:
                    afternoon_trades.append(trade)
            except:
                pass
    
    # Calcular métricas por sesión
    morning_metrics = calculate_session_metrics(morning_trades)
    afternoon_metrics = calculate_session_metrics(afternoon_trades)
    
    return custom_render_template(
        'session_analysis',
        'session_analysis.html',
        morning_metrics=morning_metrics,
        afternoon_metrics=afternoon_metrics,
        processed_data=processed_data
    )
```

#### Archivo HTML (`session_analysis.html`):

```html
{% extends 'base.html' %}

{% block title %}Análisis por Sesión - Travesty Analyzer{% endblock %}

{% block header %}Análisis por Sesión{% endblock %}

{% block content %}
<div class="row">
    <!-- Métricas de las sesiones -->
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Rendimiento por Sesión</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <!-- Sesión de Mañana -->
                    <div class="col-md-6">
                        <div class="card border-left-warning shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                            Sesión de Mañana (Antes de 12:00)</div>
                                        <div class="h5 mb-0 font-weight-bold text-gray-800">
                                            ${{ morning_metrics.total_pnl|format_number }}
                                        </div>
                                    </div>
                                    <div class="col-auto">
                                        <i class="fas fa-sun fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Detalles sesión mañana -->
                        <div class="card mt-4">
                            <div class="card-body">
                                <h6 class="card-title">Detalles Sesión Mañana</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Operaciones
                                        <span class="badge bg-primary rounded-pill">{{ morning_metrics.total_trades }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Win Rate
                                        <span class="badge bg-success rounded-pill">{{ morning_metrics.win_rate|format_percent }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Ganancia Promedio
                                        <span class="badge bg-info rounded-pill">${{ morning_metrics.avg_win|format_number }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Pérdida Promedio
                                        <span class="badge bg-danger rounded-pill">${{ morning_metrics.avg_loss|format_number }}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Sesión de Tarde -->
                    <div class="col-md-6">
                        <div class="card border-left-primary shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                            Sesión de Tarde (Después de 12:00)</div>
                                        <div class="h5 mb-0 font-weight-bold text-gray-800">
                                            ${{ afternoon_metrics.total_pnl|format_number }}
                                        </div>
                                    </div>
                                    <div class="col-auto">
                                        <i class="fas fa-moon fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Detalles sesión tarde -->
                        <div class="card mt-4">
                            <div class="card-body">
                                <h6 class="card-title">Detalles Sesión Tarde</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Operaciones
                                        <span class="badge bg-primary rounded-pill">{{ afternoon_metrics.total_trades }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Win Rate
                                        <span class="badge bg-success rounded-pill">{{ afternoon_metrics.win_rate|format_percent }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Ganancia Promedio
                                        <span class="badge bg-info rounded-pill">${{ afternoon_metrics.avg_win|format_number }}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Pérdida Promedio
                                        <span class="badge bg-danger rounded-pill">${{ afternoon_metrics.avg_loss|format_number }}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Gráfico comparativo -->
                <div class="row mt-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-title">Comparativa de Sesiones</h6>
                                <div style="height: 400px;">
                                    <canvas id="sessionsChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Datos para el gráfico
    const morningMetrics = {
        totalTrades: {{ morning_metrics.total_trades }},
        winRate: {{ morning_metrics.win_rate }},
        totalPnl: {{ morning_metrics.total_pnl }},
        avgWin: {{ morning_metrics.avg_win }},
        avgLoss: {{ morning_metrics.avg_loss }}
    };
    
    const afternoonMetrics = {
        totalTrades: {{ afternoon_metrics.total_trades }},
        winRate: {{ afternoon_metrics.win_rate }},
        totalPnl: {{ afternoon_metrics.total_pnl }},
        avgWin: {{ afternoon_metrics.avg_win }},
        avgLoss: {{ afternoon_metrics.avg_loss }}
    };
    
    // Crear gráfico comparativo
    const ctx = document.getElementById('sessionsChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['P&L Total', 'Win Rate', 'Operaciones', 'Ganancia Promedio', 'Pérdida Promedio'],
            datasets: [
                {
                    label: 'Sesión Mañana',
                    data: [
                        morningMetrics.totalPnl, 
                        morningMetrics.winRate, 
                        morningMetrics.totalTrades,
                        morningMetrics.avgWin,
                        Math.abs(morningMetrics.avgLoss)
                    ],
                    backgroundColor: 'rgba(255, 193, 7, 0.5)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Sesión Tarde',
                    data: [
                        afternoonMetrics.totalPnl, 
                        afternoonMetrics.winRate, 
                        afternoonMetrics.totalTrades,
                        afternoonMetrics.avgWin,
                        Math.abs(afternoonMetrics.avgLoss)
                    ],
                    backgroundColor: 'rgba(13, 110, 253, 0.5)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Valor'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Métrica'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw;
                            
                            if (context.dataIndex === 0) {
                                return `${label}: $${value.toFixed(2)}`; // P&L Total
                            } else if (context.dataIndex === 1) {
                                return `${label}: ${value.toFixed(2)}%`; // Win Rate
                            } else if (context.dataIndex === 2) {
                                return `${label}: ${value}`; // Operaciones
                            } else {
                                return `${label}: $${value.toFixed(2)}`; // Promedios
                            }
                        }
                    }
                }
            }
        }
    });
});
</script>
{% endblock %}
```

### 10.2 Addon de Visualización Avanzada

#### Archivo Python (`advanced_visualization.py`):


```python
def advanced_visualization_view():
    processed_data = load_processed_data(Config.DATA_CACHE_PATH)
    
    if processed_data is None:
        flash('No hay datos disponibles', 'error')
        return redirect(url_for('main.index'))
    
    trades = processed_data.get('processed_trades', [])
    
    # Preparar datos para gráficos
    chart_data = {
        'symbols': [],
        'pnl_values': [],
        'trade_counts': [],
        'win_rates': []
    }
    
    # Agrupar por símbolo
    symbols = {}
    for trade in trades:
        symbol = trade.get('symbol', 'Unknown')
        if symbol not in symbols:
            symbols[symbol] = {
                'count': 0,
                'pnl': 0,
                'wins': 0
            }
        
        symbols[symbol]['count'] += 1
        symbols[symbol]['pnl'] += trade.get('pnl', 0)
        if trade.get('pnl', 0) > 0:
            symbols[symbol]['wins'] += 1
    
    # Preparar datos para el gráfico
    for symbol, data in symbols.items():
        chart_data['symbols'].append(symbol)
        chart_data['pnl_values'].append(data['pnl'])
        chart_data['trade_counts'].append(data['count'])
        win_rate = (data['wins'] / data['count'] * 100) if data['count'] > 0 else 0
        chart_data['win_rates'].append(win_rate)
    
    return custom_render_template(
        'advanced_viz',
        'advanced_viz.html',
        chart_data=chart_data,
        processed_data=processed_data
    )
```

#### Archivo HTML (`advanced_viz.html`):

```html
{% extends 'base.html' %}

{% block title %}Visualización Avanzada - Travesty Analyzer{% endblock %}

{% block header %}Visualización Avanzada{% endblock %}

{% block content %}
<div class="row">
    <!-- Selector de visualización -->
    <div class="col-md-12 mb-4">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Visualización Interactiva</h6>
            </div>
            <div class="card-body">
                <div class="btn-group mb-4" role="group" aria-label="Selector de gráfico">
                    <button type="button" class="btn btn-primary" onclick="showChart('pnl')">P&L por Símbolo</button>
                    <button type="button" class="btn btn-primary" onclick="showChart('count')">Operaciones por Símbolo</button>
                    <button type="button" class="btn btn-primary" onclick="showChart('winrate')">Win Rate por Símbolo</button>
                    <button type="button" class="btn btn-primary" onclick="showChart('scatter')">Gráfico de Dispersión</button>
                    <button type="button" class="btn btn-primary" onclick="showChart('radar')">Gráfico Radar</button>
                </div>
                
                <!-- Contenedor del gráfico -->
                <div style="height: 500px;">
                    <canvas id="mainChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Tabla de datos -->
    <div class="col-md-12">
        <div class="card shadow">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Datos por Símbolo</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Símbolo</th>
                                <th class="text-end">P&L Total</th>
                                <th class="text-end">Operaciones</th>
                                <th class="text-end">Win Rate</th>
                                <th class="text-end">P&L Promedio</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for i in range(chart_data.symbols|length) %}
                            <tr>
                                <td>{{ chart_data.symbols[i] }}</td>
                                <td class="text-end {% if chart_data.pnl_values[i] > 0 %}text-success{% elif chart_data.pnl_values[i] < 0 %}text-danger{% endif %}">
                                    ${{ chart_data.pnl_values[i]|format_number }}
                                </td>
                                <td class="text-end">{{ chart_data.trade_counts[i] }}</td>
                                <td class="text-end">{{ chart_data.win_rates[i]|format_percent }}</td>
                                <td class="text-end">
                                    {% if chart_data.trade_counts[i] > 0 %}
                                        ${{ (chart_data.pnl_values[i] / chart_data.trade_counts[i])|format_number }}
                                    {% else %}
                                        -
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Variables globales para los datos del gráfico
const symbolsData = {
    symbols: {{ chart_data.symbols|tojson }},
    pnlValues: {{ chart_data.pnl_values|tojson }},
    tradeCounts: {{ chart_data.trade_counts|tojson }},
    winRates: {{ chart_data.win_rates|tojson }}
};

// Variable para almacenar la instancia del gráfico
let currentChart = null;

// Función para mostrar diferentes tipos de gráficos
function showChart(chartType) {
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    // Destruir gráfico anterior si existe
    if (currentChart) {
        currentChart.destroy();
    }
    
    // Configurar nuevo gráfico según el tipo seleccionado
    switch(chartType) {
        case 'pnl':
            createBarChart(ctx, 'P&L por Símbolo', symbolsData.symbols, symbolsData.pnlValues, 'P&L ($)', true);
            break;
        case 'count':
            createBarChart(ctx, 'Operaciones por Símbolo', symbolsData.symbols, symbolsData.tradeCounts, 'Número de Operaciones', false);
            break;
        case 'winrate':
            createBarChart(ctx, 'Win Rate por Símbolo', symbolsData.symbols, symbolsData.winRates, 'Win Rate (%)', false);
            break;
        case 'scatter':
            createScatterChart(ctx);
            break;
        case 'radar':
            createRadarChart(ctx);
            break;
    }
}

// Función para crear gráficos de barras
function createBarChart(ctx, title, labels, data, yAxisLabel, colorByValue) {
    // Generar colores basados en valores (positivo/negativo) o usar un color fijo
    const backgroundColors = colorByValue 
        ? data.map(value => value >= 0 ? 'rgba(40, 167, 69, 0.5)' : 'rgba(220, 53, 69, 0.5)')
        : Array(data.length).fill('rgba(13, 110, 253, 0.5)');
        
    const borderColors = colorByValue 
        ? data.map(value => value >= 0 ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)')
        : Array(data.length).fill('rgba(13, 110, 253, 1)');
    
    // Crear gráfico
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: !colorByValue, // Solo comenzar en cero si no son valores de P&L
                    title: {
                        display: true,
                        text: yAxisLabel
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Símbolo'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            // Formatear según el tipo de dato
                            if (chartType === 'pnl') {
                                return `P&L: $${value.toFixed(2)}`;
                            } else if (chartType === 'winrate') {
                                return `Win Rate: ${value.toFixed(2)}%`;
                            } else {
                                return `Operaciones: ${value}`;
                            }
                        }
                    }
                }
            }
        }
    });
}

// Función para crear gráfico de dispersión
function createScatterChart(ctx) {
    // Preparar datos para gráfico de dispersión
    const scatterData = symbolsData.symbols.map((symbol, index) => {
        return {
            x: symbolsData.tradeCounts[index],
            y: symbolsData.pnlValues[index],
            r: Math.max(5, Math.min(20, symbolsData.winRates[index] / 5)), // Tamaño basado en win rate
            symbol: symbol
        };
    });
    
    // Crear gráfico
    currentChart = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'P&L vs Operaciones',
                data: scatterData,
                backgroundColor: scatterData.map(d => d.y >= 0 ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)'),
                borderColor: scatterData.map(d => d.y >= 0 ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Número de Operaciones'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'P&L ($)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Relación entre P&L, Operaciones y Win Rate',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const d = context.raw;
                            return [
                                `Símbolo: ${d.symbol}`,
                                `Operaciones: ${d.x}`,
                                `P&L: $${d.y.toFixed(2)}`,
                                `Win Rate: ${symbolsData.winRates[context.dataIndex].toFixed(2)}%`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// Función para crear gráfico radar
function createRadarChart(ctx) {
    // Seleccionar los top 5 símbolos por volumen
    const topIndices = [...Array(symbolsData.symbols.length).keys()]
        .sort((a, b) => symbolsData.tradeCounts[b] - symbolsData.tradeCounts[a])
        .slice(0, 5);
    
    const topSymbols = topIndices.map(i => symbolsData.symbols[i]);
    
    // Normalizar datos para radar (0-100)
    const normalizeData = (data, indices) => {
        const values = indices.map(i => data[i]);
        const max = Math.max(...values.map(Math.abs));
        return values.map(v => (v / max) * 100);
    };
    
    const normalizedPnL = normalizeData(symbolsData.pnlValues, topIndices);
    const normalizedCounts = normalizeData(symbolsData.tradeCounts, topIndices);
    const normalizedWinRates = topIndices.map(i => symbolsData.winRates[i]);
    
    // Crear gráfico
    currentChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: topSymbols,
            datasets: [
                {
                    label: 'P&L (normalizado)',
                    data: normalizedPnL,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Operaciones (normalizado)',
                    data: normalizedCounts,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Win Rate (%)',
                    data: normalizedWinRates,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Análisis Multidimensional (Top 5 Símbolos)',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const i = context.dataIndex;
                            const label = context.dataset.label;
                            
                            if (label.includes('P&L')) {
                                return `P&L real: $${symbolsData.pnlValues[topIndices[i]].toFixed(2)}`;
                            } else if (label.includes('Operaciones')) {
                                return `Operaciones: ${symbolsData.tradeCounts[topIndices[i]]}`;
                            } else {
                                return `Win Rate: ${value.toFixed(2)}%`;
                            }
                        }
                    }
                }
            }
        }
    });
}

// Mostrar gráfico de P&L al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    showChart('pnl');
});
</script>
{% endblock %}
```

## Notas de Implementación

Estos ejemplos de addons muestran diferentes enfoques para extender la funcionalidad de Travesty Analyzer. El Addon de Análisis de Sesión divide las operaciones por hora del día, mostrando cómo filtrar y agrupar datos, mientras que el Addon de Visualización Avanzada demuestra técnicas más sofisticadas de visualización usando diferentes tipos de gráficos interactivos.

Al implementar tus propios addons, puedes combinar estas técnicas o desarrollar nuevos enfoques adaptados a tus necesidades específicas. El sistema modular te permite experimentar con diferentes análisis sin tener que modificar el código principal de la aplicación.

## Recursos Adicionales

Para desarrollar addons más avanzados, te recomendamos explorar:

- [Documentación de Chart.js](https://www.chartjs.org/docs) para crear visualizaciones personalizadas
- [Documentación de Bootstrap](https://getbootstrap.com/docs) para diseñar interfaces de usuario consistentes
- [Documentación de Pandas](https://pandas.pydata.org/docs) para análisis de datos avanzados
- [Iconos de FontAwesome](https://fontawesome.com/icons) para mejorar la interfaz visual

## Actualizaciones y Mantenimiento

Para mantener tus addons actualizados:

1. Utiliza un sistema de control de versiones como Git para seguir los cambios
2. Documenta claramente las dependencias y requisitos
3. Sigue el versionado semántico al publicar actualizaciones
4. Proporciona instrucciones claras para la instalación y uso

Recuerda que los addons bien diseñados no solo añaden funcionalidad, sino que mejoran la experiencia general de la aplicación, proporcionando análisis valiosos y visualizaciones que ayudan a los usuarios a entender mejor sus datos de trading.

