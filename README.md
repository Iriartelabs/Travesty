# DAS Trader Analyzer

![Estado del Proyecto](https://img.shields.io/badge/Estado-Activo-brightgreen)
![Versión](https://img.shields.io/badge/Versión-2.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![Flask](https://img.shields.io/badge/Flask-2.3.2-lightgrey)

Una aplicación web modular y avanzada para analizar datos de trading exportados desde DAS Trader, proporcionando visualizaciones interactivas, métricas de rendimiento, análisis técnico, backtesting de estrategias y un sistema extensible de addons para análisis personalizados.

![Dashboard Preview](https://via.placeholder.com/800x450?text=DAS+Trader+Analyzer+Dashboard)

## 🚀 Características

- **Dashboard completo** con métricas clave de rendimiento
- **Análisis multidimensional**:
  - Por símbolo
  - Por hora del día
  - Por día de la semana
  - Compras vs ventas
- **Visualizaciones interactivas** con gráficos dinámicos
- **Listado detallado** de todas las operaciones
- **Sistema avanzado de alertas** con:
  - Condiciones personalizables
  - Indicadores técnicos (SMA, RSI, MACD)
  - Detección de patrones (Doble Techo, Cabeza y Hombros, etc.)
  - Backtesting de estrategias
  - Gestión de riesgo y cálculo de posiciones
- **Arquitectura modular** con sistema de addons extensible y UI para gestión
- **Procesamiento automático** de archivos CSV de DAS Trader
- **Fusión de datos** para combinar archivos históricos con nuevos

## 📊 Visualizaciones Incluidas

- Curva de equidad
- Rendimiento por símbolo
- Análisis temporal (por hora)
- Comparación de estrategias de compra/venta
- Análisis por día de la semana
- Gráficos de rendimiento por trader
- Visualizaciones de indicadores técnicos
- Resultados de backtesting

## 🧠 Análisis Técnico Integrado

- **Indicadores técnicos**:
  - Medias Móviles Simples (SMA) y Exponenciales (EMA)
  - Índice de Fuerza Relativa (RSI)
  - MACD (Moving Average Convergence Divergence)
  - Bandas de Bollinger
  - Niveles de soporte y resistencia
- **Detección de patrones**:
  - Doble Techo / Doble Suelo
  - Cabeza y Hombros
- **Motor de backtesting** para probar estrategias:
  - Cruce de medias móviles
  - Estrategias basadas en RSI
  - Cálculo de ratio ganancia/pérdida

## 🔧 Tecnologías

- **Backend**: Python, Flask
- **Procesamiento de datos**: Pandas, NumPy
- **Análisis técnico**: Implementación personalizada
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualización**: Chart.js, DataTables
- **Diseño**: Bootstrap 5
- **Iconos**: Font Awesome

## 📋 Requisitos

- Python 3.8+
- Flask 2.3.2
- Pandas 2.0.1
- NumPy 1.24.3
- Otras dependencias listadas en `requirements.txt`

## 🔌 Instalación

1. **Clonar este repositorio**

```bash
git clone https://github.com/tu-usuario/das-trader-analyzer.git
cd das-trader-analyzer
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

1. **Preparar archivos de datos**

Exporta tus datos desde DAS Trader:
- Trades.csv: Historial de ejecuciones (Requerido)
- Orders.csv, Tickets.csv: (Opcionales)

2. **Iniciar la aplicación**

```bash
python app.py
```

3. **Acceder a la aplicación**

Abre tu navegador y visita `http://localhost:5000`

4. **Cargar datos**

- Utiliza el formulario en la página principal para subir tus archivos CSV
- Opción para fusionar nuevos datos con existentes
- O utiliza "Usar archivos existentes" si ya has cargado archivos previamente

## 🧩 Sistema de Addons

DAS Trader Analyzer incluye un poderoso sistema de addons que permite extender la funcionalidad sin modificar el código principal.

### Addons incluidos

- **Trading Alerts Pro**: Sistema avanzado de alertas con análisis técnico, backtesting y gestión de riesgo
- **Análisis por Día**: Analiza el rendimiento por día de la semana
- **Trader Performance**: Análisis de rendimiento por trader individual

### Crear un nuevo addon

#### Método 1: Desde la interfaz de usuario
1. Navega a "Gestionar Addons" en la barra lateral
2. Completa el formulario con nombre, ruta, descripción e icono
3. Haz clic en "Crear Addon"
4. Recarga los addons para activar

#### Método 2: Manual
1. Crea un archivo Python en el directorio `addons/`
2. Implementa tu lógica de análisis personalizada
3. Registra el addon en el sistema principal
4. Crea una plantilla HTML en `templates/`

[Ver documentación completa sobre creación de addons](docs/addon_development.md)

## 📁 Estructura del Proyecto

```
das-trader-analyzer/
├── app.py                 # Aplicación principal y punto de entrada
├── config.py              # Configuración por entornos
├── addon_system.py        # Sistema de gestión de addons
├── extensions.py          # Extensiones Flask
│
├── addons/                # Addons para extender funcionalidad
│   ├── __init__.py
│   ├── weekday_analysis.py
│   ├── trading_alert_addon.py
│   └── trader_performance.py
│
├── routes/                # Controladores y rutas
│   ├── __init__.py
│   ├── main.py            # Rutas principales
│   ├── data_upload.py     # Gestión de carga de archivos
│   └── analysis.py        # Rutas de análisis y gestión de addons
│
├── services/              # Servicios de la aplicación
│   ├── __init__.py
│   ├── data_processor.py  # Procesamiento de datos
│   ├── cache_manager.py   # Gestión de caché
│   └── file_handler.py    # Manejo de archivos
│
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── symbols.html
│   ├── trading_alerts.html
│   ├── create_alert.html
│   ├── backtest.html
│   ├── position_calculator.html
│   ├── alert_settings.html
│   └── manage_addons.html
│
├── static/                # Archivos estáticos
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── charts.js
│   └── uploads/           # Archivos temporales subidos
│
├── data/                  # Directorio para archivos de datos
│   ├── Trades.csv
│   ├── Orders.csv
│   └── processed_cache.pkl # Caché de datos procesados
│
└── requirements.txt       # Dependencias
```

## 📊 Características Avanzadas

### Sistema de Alertas de Trading

El sistema de alertas incluye:

- **Alertas básicas** basadas en condiciones de órdenes
- **Alertas técnicas** basadas en indicadores y patrones
- **Backtesting** de estrategias de trading
- **Calculadora de posiciones** con gestión de riesgo
- **Sistema de notificaciones** configurable

### Gestión de Addons

La aplicación incluye una interfaz para:

- Ver todos los addons instalados
- Crear nuevos addons desde la UI
- Recargar addons dinámicamente
- Gestionar estado (activo/inactivo)

## 🛠️ Despliegue

### Opción 1: Servidor web con Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()
```

### Opción 2: Despliegue en PythonAnywhere

1. Crea una cuenta en [PythonAnywhere](https://www.pythonanywhere.com/)
2. Sube los archivos del proyecto
3. Configura una nueva aplicación web apuntando a `app:create_app()`

### Opción 3: Despliegue en Heroku

```bash
# Crear archivo Procfile
echo "web: gunicorn app:create_app()" > Procfile

# Desplegar en Heroku
heroku login
git init
git add .
git commit -m "Versión inicial"
heroku create
git push heroku master
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes, por favor abre primero un issue para discutir lo que te gustaría cambiar.

1. Haz un fork del proyecto
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Confirma tus cambios (`git commit -m 'Añade nueva característica'`)
4. Empuja a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

### Desarrollo de Addons

Consulta la [guía de desarrollo de addons](docs/addon_development.md) para contribuir con nuevos addons.

## 📝 Licencia

Este proyecto está disponible bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📧 Contacto

Si tienes preguntas o sugerencias, no dudes en abrir un issue o contactar con el equipo de desarrollo.

---

Construido con ❤️ para traders que buscan mejorar su rendimiento a través del análisis de datos.
