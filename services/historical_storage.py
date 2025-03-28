"""
Módulo para gestionar el almacenamiento histórico de datos de trading
"""
import os
import glob
import re
from datetime import datetime

class HistoricalStorage:
    """
    Clase para gestionar el almacenamiento y recuperación de datos históricos.
    
    Permite organizar datos por día, semana y mes para análisis históricos.
    """
    
    def __init__(self, base_path):
        """
        Inicializa el almacenamiento histórico.
        
        Args:
            base_path (str): Ruta base donde se almacenan los datos históricos
        """
        self.base_path = base_path
        self.day_path = os.path.join(base_path, 'day')
        self.week_path = os.path.join(base_path, 'week')
        self.month_path = os.path.join(base_path, 'month')
        
        # Crear directorios si no existen
        for path in [self.day_path, self.week_path, self.month_path]:
            os.makedirs(path, exist_ok=True)
    
    def get_available_periods(self):
        """
        Obtiene los períodos disponibles (días, semanas, meses).
        
        Returns:
            dict: Diccionario con los períodos disponibles
        """
        days = self._get_available_days()
        weeks = self._get_available_weeks()
        months = self._get_available_months()
        
        return {
            'days': days,
            'weeks': weeks,
            'months': months
        }
    
    def _get_available_days(self):
        """Obtiene los días disponibles"""
        pattern = os.path.join(self.day_path, "*")
        dirs = glob.glob(pattern)
        
        # Extraer solo el nombre del directorio (que debería ser la fecha en formato YYYYMMDD)
        days = []
        for dir_path in dirs:
            day_str = os.path.basename(dir_path)
            # Verificar que sea un formato de fecha válido
            if re.match(r'^\d{8}$', day_str):
                try:
                    # Convertir a objeto fecha para verificar validez
                    date_obj = datetime.strptime(day_str, '%Y%m%d')
                    # Formatear para mostrar
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    days.append({
                        'value': day_str,
                        'display': formatted_date
                    })
                except ValueError:
                    # Ignorar directorios con formato incorrecto
                    pass
        
        # Ordenar por fecha (más reciente primero)
        days.sort(key=lambda x: x['value'], reverse=True)
        return days
    
    def _get_available_weeks(self):
        """Obtiene las semanas disponibles"""
        pattern = os.path.join(self.week_path, "*")
        dirs = glob.glob(pattern)
        
        weeks = []
        for dir_path in dirs:
            week_str = os.path.basename(dir_path)
            # Formato esperado: YYYYWNN (ej: 2023W01)
            if re.match(r'^\d{4}W\d{2}$', week_str):
                year = week_str[:4]
                week_num = week_str[5:]
                weeks.append({
                    'value': week_str,
                    'display': f'Semana {week_num}, {year}'
                })
        
        # Ordenar por semana (más reciente primero)
        weeks.sort(key=lambda x: x['value'], reverse=True)
        return weeks
    
    def _get_available_months(self):
        """Obtiene los meses disponibles"""
        pattern = os.path.join(self.month_path, "*")
        dirs = glob.glob(pattern)
        
        months = []
        for dir_path in dirs:
            month_str = os.path.basename(dir_path)
            # Formato esperado: YYYYMM (ej: 202301)
            if re.match(r'^\d{6}$', month_str):
                try:
                    # Convertir a objeto fecha para verificar validez
                    date_obj = datetime.strptime(month_str, '%Y%m')
                    # Formatear para mostrar
                    formatted_date = date_obj.strftime('%B %Y')
                    months.append({
                        'value': month_str,
                        'display': formatted_date
                    })
                except ValueError:
                    # Ignorar directorios con formato incorrecto
                    pass
        
        # Ordenar por mes (más reciente primero)
        months.sort(key=lambda x: x['value'], reverse=True)
        return months
    
    def save_period_data(self, period_type, period_value, files):
        """
        Guarda los datos para un período específico.
        
        Args:
            period_type (str): Tipo de período ('day', 'week', 'month')
            period_value (str): Valor del período (ej: '20230101' para día)
            files (dict): Archivos a guardar
            
        Returns:
            bool: True si se guardaron correctamente, False en caso contrario
        """
        # Determinar la ruta de destino según el tipo de período
        if period_type == 'day':
            dest_dir = os.path.join(self.day_path, period_value)
        elif period_type == 'week':
            dest_dir = os.path.join(self.week_path, period_value)
        elif period_type == 'month':
            dest_dir = os.path.join(self.month_path, period_value)
        else:
            return False
        
        # Crear directorio si no existe
        os.makedirs(dest_dir, exist_ok=True)
        
        # Guardar archivos
        for file_type, file_list in files.items():
            for file in file_list:
                dest_path = os.path.join(dest_dir, file_type + '.csv')
                # Guardar el archivo
                try:
                    file.save(dest_path)
                except Exception as e:
                    print(f"Error al guardar {file_type}: {str(e)}")
                    return False
        
        return True
    
    def load_period_data(self, period_type, period_value):
        """
        Carga los datos de un período específico.
        
        Args:
            period_type (str): Tipo de período ('day', 'week', 'month')
            period_value (str): Valor del período
            
        Returns:
            dict: Rutas a los archivos cargados o None si no existe
        """
        # Determinar la ruta según el tipo de período
        if period_type == 'day':
            source_dir = os.path.join(self.day_path, period_value)
        elif period_type == 'week':
            source_dir = os.path.join(self.week_path, period_value)
        elif period_type == 'month':
            source_dir = os.path.join(self.month_path, period_value)
        else:
            return None
        
        # Verificar si existe el directorio
        if not os.path.exists(source_dir):
            return None
        
        # Buscar archivos
        file_paths = {}
        for file_type in ['orders', 'trades', 'tickets']:
            file_path = os.path.join(source_dir, file_type + '.csv')
            if os.path.exists(file_path):
                file_paths[file_type] = file_path
        
        return file_paths if file_paths else None