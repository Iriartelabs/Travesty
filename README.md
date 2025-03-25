# Analizador de Trading DAS

Una aplicación web sencilla para analizar datos de trading exportados desde DAS Trader.

## Características

- Dashboard con métricas clave de rendimiento
- Análisis por símbolo
- Análisis temporal (por hora del día)
- Comparación de estrategias de compra/venta
- Listado detallado de operaciones
- Gráficos interactivos
- Recomendaciones personalizadas

## Requisitos

- Python 3.6+
- Flask
- Pandas
- NumPy
- (Opcional) Un servidor web para despliegue

## Instalación

1. Clona este repositorio o descarga los archivos

```bash
git clone https://github.com/tu-usuario/das-trader-analyzer.git
cd das-trader-analyzer
```

2. Crea un entorno virtual (recomendado)

```bash
python -m venv venv
```

3. Activa el entorno virtual

En Windows:
```bash
venv\Scripts\activate
```

En macOS/Linux:
```bash
source venv/bin/activate
```

4. Instala las dependencias

```bash
pip install -r requirements.txt
```

## Uso

1. Coloca tus archivos CSV exportados de DAS Trader en la carpeta `data` o prepárate para subirlos a través de la interfaz web.

2. Inicia la aplicación

```bash
python app.py
```

3. Abre tu navegador web y visita `http://localhost:5000`

4. Si los archivos CSV están en la carpeta `data`, puedes hacer clic en "Usar archivos existentes". De lo contrario, sube los archivos a través del formulario.

## Despliegue en servidor web

### Opción 1: Despliegue con Gunicorn (Linux/macOS)

1. Instala Gunicorn
```bash
pip install gunicorn
```

2. Ejecuta la aplicación con Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Opción 2: Despliegue en PythonAnywhere

1. Crea una cuenta en [PythonAnywhere](https://www.pythonanywhere.com/)
2. Sube los archivos a través de la consola o mediante Git
3. Configura una nueva aplicación web
4. Establece la ruta al archivo WSGI y asegúrate de que apunte a tu app.py

### Opción 3: Despliegue en Heroku

1. Crea un archivo `Procfile` con el siguiente contenido:
```
web: gunicorn app:app
```

2. Instala el CLI de Heroku y sigue las instrucciones para desplegar

```bash
heroku login
git init
git add .
git commit -m "Aplicación inicial"
heroku create
git push heroku master
```

## Estructura de archivos

```
das-trader-analyzer/
├── app.py                # Aplicación principal
├── utils/
│   └── data_processor.py # Procesamiento de datos
├── templates/            # Plantillas HTML
│   ├── base.html         # Plantilla base
│   ├── index.html        # Página de inicio
│   ├── dashboard.html    # Dashboard principal
│   └── ...               # Otras plantillas
├── static/               # Archivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── uploads/          # Carpeta para archivos subidos (temporal)
├── data/                 # Carpeta para archivos de datos predeterminados
│   ├── Orders.csv
│   ├── Trades.csv
│   └── Tickets.csv
└── requirements.txt      # Dependencias
```

## Personalización

Puedes personalizar la aplicación modificando las plantillas HTML en la carpeta `templates/` o los estilos CSS en `static/css/style.css`.

## Licencia

Este proyecto está disponible bajo la licencia MIT.

## Autor

Creado por [Tu Nombre]