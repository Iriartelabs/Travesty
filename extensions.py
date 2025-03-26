def init_extensions(app):
    """
    Inicializa extensiones y registra filtros personalizados
    
    Args:
        app (Flask): Instancia de la aplicación Flask
    """
    # Filtro para formatear números
    @app.template_filter('format_number')
    def format_number(value):
        """Filtro para formatear números en las plantillas"""
        if value is None:
            return "-"
        try:
            value = float(value)
            return f"{value:,.2f}"
        except (ValueError, TypeError):
            return value

    # Filtro para formatear porcentajes
    @app.template_filter('format_percent')
    def format_percent(value):
        """Filtro para formatear porcentajes en las plantillas"""
        if value is None:
            return "-"
        try:
            value = float(value)
            return f"{value:.2f}%"
        except (ValueError, TypeError):
            return value
