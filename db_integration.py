import os
import pandas as pd
import csv
import tempfile
from datetime import datetime, timedelta
from flask import current_app, g
import mysql.connector
from mysql.connector import pooling

# Configuración de la conexión a la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'das_app_user',
    'password': 'secure_password_here',
    'database': 'das_trader_analyzer',
    'port': 3306,
    'raise_on_warnings': True
}

# Crear un pool de conexiones para mejorar el rendimiento
connection_pool = None

def init_db_pool(app=None):
    """Inicializa el pool de conexiones a la base de datos"""
    global connection_pool
    
    if connection_pool is None:
        # Si se proporciona una aplicación Flask, usar su configuración
        if app:
            config = {
                'host': app.config.get('DB_HOST', 'localhost'),
                'user': app.config.get('DB_USER', 'das_app_user'),
                'password': app.config.get('DB_PASSWORD', 'secure_password_here'),
                'database': app.config.get('DB_NAME', 'das_trader_analyzer'),
                'port': app.config.get('DB_PORT', 3306),
                'raise_on_warnings': True
            }
        else:
            config = DB_CONFIG
            
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="das_analyzer_pool",
                pool_size=5,
                **config
            )
            if app:
                app.logger.info("Pool de conexiones de base de datos inicializado")
        except Exception as e:
            if app:
                app.logger.error(f"Error al inicializar pool de base de datos: {e}")
            else:
                print(f"Error al inicializar pool de base de datos: {e}")
            return False
    
    return True

def get_db_connection():
    """Obtiene una conexión desde el pool"""
    if connection_pool is None:
        init_db_pool()
    
    return connection_pool.get_connection()

def get_db():
    """Obtiene una conexión de base de datos en el contexto de Flask"""
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db

def close_db(e=None):
    """Cierra la conexión de base de datos al finalizar la solicitud"""
    db = g.pop('db', None)
    
    if db is not None:
        db.close()

def init_app(app):
    """Inicializa la integración de la base de datos con la aplicación Flask"""
    init_db_pool(app)
    app.teardown_appcontext(close_db)

def create_tables_if_not_exist():
    """
    Crea las tablas en la base de datos si no existen
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    # Ruta al archivo SQL con el esquema
    schema_path = os.path.join(os.path.dirname(__file__), 'db_schema.sql')
    
    # Si no existe el archivo, no se puede continuar
    if not os.path.exists(schema_path):
        print(f"No se encontró el archivo de esquema: {schema_path}")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Leer el archivo SQL
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Ejecutar scripts SQL uno por uno
        # Dividir el script por los delimitadores
        sql_commands = schema_sql.split(';')
        
        for command in sql_commands:
            command = command.strip()
            if command:
                cursor.execute(command)
        
        # Confirmar cambios
        conn.commit()
        
        print("Tablas creadas/verificadas correctamente")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error creando tablas: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()
        
def import_orders_to_db(orders_file, app=None):
    """
    Importa órdenes a la base de datos desde un archivo CSV
    
    Args:
        orders_file: Ruta al archivo CSV de órdenes
        app: Instancia de la aplicación Flask (opcional)
    
    Returns:
        int: Número de órdenes importadas
    """
    logger = app.logger if app else None
    
    # Crear tabla temporal para importar datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Crear tabla temporal
        cursor.execute("""
        CREATE TEMPORARY TABLE temp_orders (
            OrderID VARCHAR(20),
            Trader VARCHAR(50),
            Account VARCHAR(50),
            Branch VARCHAR(50),
            route VARCHAR(20),
            bkrsym VARCHAR(20),
            rrno VARCHAR(20),
            `B/S` CHAR(1),
            SHORT CHAR(1),
            Market VARCHAR(20),
            stop CHAR(1),
            symb VARCHAR(20),
            qty DECIMAL(15,2),
            lvsqty DECIMAL(15,2),
            price DECIMAL(15,4),
            stopprice DECIMAL(15,4),
            trailprice DECIMAL(15,4),
            time VARCHAR(50)
        )
        """)
        
        # Leer el archivo CSV y cargarlo en la tabla temporal
        with open(orders_file, 'r') as f:
            csv_reader = csv.reader(f)
            header = next(csv_reader)  # Leer encabezado
            
            # Preparar sentencia INSERT
            placeholders = ', '.join(['%s'] * len(header))
            insert_query = f"INSERT INTO temp_orders ({', '.join(header)}) VALUES ({placeholders})"
            
            # Insertar datos por lotes
            batch_size = 1000
            batch_data = []
            imported_count = 0
            
            for row in csv_reader:
                batch_data.append(row)
                
                if len(batch_data) >= batch_size:
                    cursor.executemany(insert_query, batch_data)
                    imported_count += len(batch_data)
                    batch_data = []
            
            # Insertar registros restantes
            if batch_data:
                cursor.executemany(insert_query, batch_data)
                imported_count += len(batch_data)
        
        # Importar desde la tabla temporal a la tabla real
        cursor.execute("CALL import_orders_from_temp('temp_orders')")
        result = cursor.fetchone()
        orders_imported = result[0] if result else 0
        
        # Confirmar transacción
        conn.commit()
        
        if logger:
            logger.info(f"Importadas {orders_imported} órdenes a la base de datos")
        
        return orders_imported
        
    except Exception as e:
        conn.rollback()
        if logger:
            logger.error(f"Error importando órdenes: {e}")
        return 0
        
    finally:
        # Eliminar tabla temporal
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_orders")
        cursor.close()
        conn.close()

def import_trades_to_db(trades_file, app=None):
    """
    Importa trades a la base de datos desde un archivo CSV
    
    Args:
        trades_file: Ruta al archivo CSV de trades
        app: Instancia de la aplicación Flask (opcional)
    
    Returns:
        int: Número de trades importados
    """
    logger = app.logger if app else None
    
    # Crear tabla temporal para importar datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Crear tabla temporal
        cursor.execute("""
        CREATE TEMPORARY TABLE temp_trades (
            TradeID VARCHAR(20),
            OrderID VARCHAR(20),
            Trader VARCHAR(50),
            Account VARCHAR(50),
            Branch VARCHAR(50),
            route VARCHAR(20),
            bkrsym VARCHAR(20),
            rrno VARCHAR(20),
            `B/S` CHAR(1),
            SHORT CHAR(1),
            Market VARCHAR(20),
            symb VARCHAR(20),
            qty DECIMAL(15,2),
            price DECIMAL(15,4),
            time VARCHAR(50)
        )
        """)
        
        # Leer el archivo CSV y cargarlo en la tabla temporal
        with open(trades_file, 'r') as f:
            csv_reader = csv.reader(f)
            header = next(csv_reader)  # Leer encabezado
            
            # Preparar sentencia INSERT
            placeholders = ', '.join(['%s'] * len(header))
            insert_query = f"INSERT INTO temp_trades ({', '.join(header)}) VALUES ({placeholders})"
            
            # Insertar datos por lotes
            batch_size = 1000
            batch_data = []
            imported_count = 0
            
            for row in csv_reader:
                batch_data.append(row)
                
                if len(batch_data) >= batch_size:
                    cursor.executemany(insert_query, batch_data)
                    imported_count += len(batch_data)
                    batch_data = []
            
            # Insertar registros restantes
            if batch_data:
                cursor.executemany(insert_query, batch_data)
                imported_count += len(batch_data)
        
        # Importar desde la tabla temporal a la tabla real
        cursor.execute("CALL import_trades_from_temp('temp_trades')")
        result = cursor.fetchone()
        trades_imported = result[0] if result else 0
        
        # Confirmar transacción
        conn.commit()
        
        if logger:
            logger.info(f"Importados {trades_imported} trades a la base de datos")
        
        return trades_imported
        
    except Exception as e:
        conn.rollback()
        if logger:
            logger.error(f"Error importando trades: {e}")
        return 0
        
    finally:
        # Eliminar tabla temporal
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_trades")
        cursor.close()
        conn.close()

def import_tickets_to_db(tickets_file, app=None):
    """
    Importa tickets a la base de datos desde un archivo CSV
    
    Args:
        tickets_file: Ruta al archivo CSV de tickets
        app: Instancia de la aplicación Flask (opcional)
    
    Returns:
        int: Número de tickets importados
    """
    logger = app.logger if app else None
    
    # Crear tabla temporal para importar datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Crear tabla temporal
        cursor.execute("""
        CREATE TEMPORARY TABLE temp_tickets (
            TicketID VARCHAR(20),
            TradeID VARCHAR(20),
            Trader VARCHAR(50),
            Account VARCHAR(50),
            Branch VARCHAR(50),
            route VARCHAR(20),
            bkrsym VARCHAR(20),
            rrno VARCHAR(20),
            `B/S` CHAR(1),
            SHORT CHAR(1),
            Market VARCHAR(20),
            symb VARCHAR(20),
            qty DECIMAL(15,2),
            price DECIMAL(15,4),
            commission DECIMAL(15,4),
            RouteFee DECIMAL(15,4),
            time VARCHAR(50)
        )
        """)
        
        # Leer el archivo CSV y cargarlo en la tabla temporal
        with open(tickets_file, 'r') as f:
            csv_reader = csv.reader(f)
            header = next(csv_reader)  # Leer encabezado
            
            # Preparar sentencia INSERT
            placeholders = ', '.join(['%s'] * len(header))
            insert_query = f"INSERT INTO temp_tickets ({', '.join(header)}) VALUES ({placeholders})"
            
            # Insertar datos por lotes
            batch_size = 1000
            batch_data = []
            imported_count = 0
            
            for row in csv_reader:
                batch_data.append(row)
                
                if len(batch_data) >= batch_size:
                    cursor.executemany(insert_query, batch_data)
                    imported_count += len(batch_data)
                    batch_data = []
            
            # Insertar registros restantes
            if batch_data:
                cursor.executemany(insert_query, batch_data)
                imported_count += len(batch_data)
        
        # Importar desde la tabla temporal a la tabla real
        cursor.execute("CALL import_tickets_from_temp('temp_tickets')")
        result = cursor.fetchone()
        tickets_imported = result[0] if result else 0
        
        # Confirmar transacción
        conn.commit()
        
        if logger:
            logger.info(f"Importados {tickets_imported} tickets a la base de datos")
        
        return tickets_imported
        
    except Exception as e:
        conn.rollback()
        if logger:
            logger.error(f"Error importando tickets: {e}")
        return 0
        
    finally:
        # Eliminar tabla temporal
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_tickets")
        cursor.close()
        conn.close()

def import_data_to_db(orders_file, trades_file, tickets_file, app=None):
    """
    Importa todos los datos (órdenes, trades, tickets) a la base de datos
    
    Args:
        orders_file: Ruta al archivo CSV de órdenes
        trades_file: Ruta al archivo CSV de trades
        tickets_file: Ruta al archivo CSV de tickets
        app: Instancia de la aplicación Flask (opcional)
    
    Returns:
        dict: Resumen de la importación
    """
    logger = app.logger if app else None
    
    if logger:
        logger.info(f"Iniciando importación de datos a la base de datos")
    
    # Importar órdenes
    orders_imported = import_orders_to_db(orders_file, app)
    
    # Importar trades
    trades_imported = import_trades_to_db(trades_file, app)
    
    # Importar tickets
    tickets_imported = import_tickets_to_db
    
    (tickets_file, app)
    
    # Ejecutar cálculos de métricas
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Calcular métricas para el día actual
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Calcular métricas diarias
        cursor.execute(f"CALL calculate_daily_metrics('{yesterday}', '{today}')")
        cursor.fetchall()  # Consumir resultado
        
        # Calcular métricas por símbolo
        cursor.execute(f"CALL calculate_symbol_metrics('{yesterday}', '{today}')")
        cursor.fetchall()  # Consumir resultado
        
        # Calcular métricas por hora
        cursor.execute(f"CALL calculate_hourly_metrics('{yesterday}', '{today}')")
        cursor.fetchall()  # Consumir resultado
        
        conn.commit()
        
    except Exception as e:
        if logger:
            logger.error(f"Error calculando métricas: {e}")
    finally:
        cursor.close()
        conn.close()
    
    # Preparar resumen
    import_summary = {
        'orders_imported': orders_imported,
        'trades_imported': trades_imported,
        'tickets_imported': tickets_imported,
        'import_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'success' if (orders_imported > 0 and trades_imported > 0) else 'partial' if (orders_imported > 0 or trades_imported > 0) else 'failed'
    }
    
    if logger:
        logger.info(f"Importación de datos completada: {import_summary}")
    
    return import_summary

def get_processed_orders_from_db(start_date=None, end_date=None, symbols=None, limit=None):
    """
    Obtiene órdenes procesadas desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        symbols: Lista de símbolos a filtrar (opcional)
        limit: Límite de resultados (opcional)
    
    Returns:
        list: Lista de órdenes procesadas
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Construir consulta base
        query = "SELECT * FROM vw_processed_orders WHERE 1=1"
        params = []
        
        # Añadir filtros
        if start_date:
            query += " AND DATE(time) >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(time) <= %s"
            params.append(end_date)
        
        if symbols:
            placeholders = ', '.join(['%s'] * len(symbols))
            query += f" AND symb IN ({placeholders})"
            params.extend(symbols)
        
        # Ordenar por fecha/hora descendente
        query += " ORDER BY time DESC"
        
        # Añadir límite si se especifica
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        # Ejecutar consulta
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Procesar resultados
        processed_orders = []
        for row in rows:
            # Convertir datetime a string para mantener compatibilidad
            if 'time' in row and isinstance(row['time'], datetime):
                row['time'] = row['time'].strftime('%Y-%m-%d %H:%M:%S')
                
            # Obtener trades y tickets asociados
            order_id = row['OrderID']
            
            # Consultar trades
            cursor.execute("""
            SELECT t.*, 
                   DATE_FORMAT(t.trade_time, '%Y-%m-%d %H:%i:%s') as formatted_time 
            FROM trades t 
            WHERE t.order_id = %s
            """, (order_id,))
            trades = cursor.fetchall()
            
            # Calcular totales y promedios
            total_qty = sum(trade['quantity'] for trade in trades) if trades else 0
            
            if total_qty > 0:
                avg_price = sum(trade['quantity'] * trade['price'] for trade in trades) / total_qty
            else:
                avg_price = 0
                
            # Consultar comisiones y fees
            cursor.execute("""
            SELECT SUM(tk.commission) as total_commission, 
                   SUM(tk.route_fee) as total_route_fee 
            FROM trades tr 
            JOIN tickets tk ON tr.trade_id = tk.trade_id 
            WHERE tr.order_id = %s
            """, (order_id,))
            fees_result = cursor.fetchone()
            
            total_commission = fees_result['total_commission'] if fees_result and fees_result['total_commission'] else 0
            total_route_fee = fees_result['total_route_fee'] if fees_result and fees_result['total_route_fee'] else 0
            
            # Calcular P&L
            pnl = 0
            if row['B/S'] == 'B':  # Compra
                pnl = (row['price'] - avg_price) * total_qty if total_qty > 0 else 0
            else:  # Venta
                pnl = (avg_price - row['price']) * total_qty if total_qty > 0 else 0
            
            # Restar comisiones y fees
            pnl = pnl - total_commission - total_route_fee
            
            # Crear objeto de orden procesada
            processed_order = dict(row)
            processed_order.update({
                'trades': trades,
                'totalQty': total_qty,
                'avgPrice': avg_price,
                'totalCommission': total_commission,
                'totalRouteFee': total_route_fee,
                'pnl': pnl
            })
            
            processed_orders.append(processed_order)
        
        return processed_orders
        
    except Exception as e:
        print(f"Error obteniendo órdenes procesadas: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def get_daily_metrics(start_date=None, end_date=None):
    """
    Obtiene métricas diarias desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        dict: Métricas diarias
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = datetime.now().date()
        
        # Consultar métricas diarias
        cursor.execute("""
        SELECT 
            analytics_date, 
            total_trades, 
            total_pl, 
            winning_trades, 
            losing_trades, 
            win_rate, 
            profit_factor, 
            avg_win, 
            avg_loss,
            analytics_data
        FROM processed_analytics 
        WHERE analytics_type = 'daily'
        AND analytics_date BETWEEN %s AND %s
        ORDER BY analytics_date
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        
        # Si no hay datos, calcular y reintentar
        if not rows:
            cursor.execute(f"CALL calculate_daily_metrics(%s, %s)", (start_date, end_date))
            cursor.fetchall()  # Consumir resultado
            conn.commit()
            
            # Volver a consultar
            cursor.execute("""
            SELECT 
                analytics_date, 
                total_trades, 
                total_pl, 
                winning_trades, 
                losing_trades, 
                win_rate, 
                profit_factor, 
                avg_win, 
                avg_loss,
                analytics_data
            FROM processed_analytics 
            WHERE analytics_type = 'daily'
            AND analytics_date BETWEEN %s AND %s
            ORDER BY analytics_date
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
        
        # Calcular métricas globales
        total_pl = sum(row['total_pl'] for row in rows) if rows else 0
        total_trades = sum(row['total_trades'] for row in rows) if rows else 0
        winning_trades = sum(row['winning_trades'] for row in rows) if rows else 0
        losing_trades = sum(row['losing_trades'] for row in rows) if rows else 0
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calcular ganancia y pérdida total
        total_win = sum(row['avg_win'] * row['winning_trades'] for row in rows) if rows else 0
        total_loss = sum(abs(row['avg_loss']) * row['losing_trades'] for row in rows) if rows else 0
        
        # Profit factor
        profit_factor = (total_win / total_loss) if total_loss > 0 else total_win
        
        # Promedios
        avg_win = (total_win / winning_trades) if winning_trades > 0 else 0
        avg_loss = (total_loss / losing_trades) if losing_trades > 0 else 0
        
        # Preparar curva de equidad
        equity_curve = []
        running_pl = 0
        max_equity = 0
        max_drawdown = 0
        
        for idx, row in enumerate(rows):
            date_str = row['analytics_date'].strftime('%Y-%m-%d') if isinstance(row['analytics_date'], datetime) else str(row['analytics_date'])
            running_pl += row['total_pl']
            
            # Actualizar máximo equity
            if running_pl > max_equity:
                max_equity = running_pl
            
            # Calcular drawdown
            drawdown = max_equity - running_pl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            
            # Añadir punto a la curva de equidad
            equity_curve.append({
                'tradeNumber': idx + 1,
                'date': date_str,
                'pnl': row['total_pl'],
                'equity': running_pl
            })
        
        # Construir el objeto de métricas
        metrics = {
            'totalPL': total_pl,
            'winRate': win_rate,
            'profitFactor': profit_factor,
            'avgWin': avg_win,
            'avgLoss': avg_loss,
            'maxDrawdown': max_drawdown,
            'totalTrades': total_trades,
            'winningTrades': winning_trades,
            'losingTrades': losing_trades
        }
        
        return {
            'metrics': metrics,
            'equity_curve': equity_curve,
            'daily_data': rows
        }
        
    except Exception as e:
        print(f"Error obteniendo métricas diarias: {e}")
        return {
            'metrics': {
                'totalPL': 0,
                'winRate': 0,
                'profitFactor': 0,
                'avgWin': 0,
                'avgLoss': 0,
                'maxDrawdown': 0,
                'totalTrades': 0,
                'winningTrades': 0,
                'losingTrades': 0
            },
            'equity_curve': [],
            'daily_data': []
        }
        
    finally:
        cursor.close()
        conn.close()

def get_symbol_performance(start_date=None, end_date=None):
    """
    Obtiene el rendimiento por símbolo desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        list: Lista de rendimiento por símbolo
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = datetime.now().date()
        
        # Consultar métricas por símbolo
        cursor.execute("""
        SELECT 
            s.symbol,
            pa.total_trades AS totalTrades,
            pa.total_pl AS totalPL,
            pa.winning_trades AS winningTrades,
            pa.win_rate AS winRate,
            pa.analytics_data
        FROM processed_analytics pa
        JOIN symbols s ON pa.symbol_id = s.symbol_id
        WHERE pa.analytics_type = 'symbol'
        AND pa.analytics_date = %s
        ORDER BY pa.total_pl DESC
        """, (start_date,))
        
        rows = cursor.fetchall()
        
        # Si no hay datos, calcular y reintentar
        if not rows:
            cursor.execute(f"CALL calculate_symbol_metrics(%s, %s)", (start_date, end_date))
            cursor.fetchall()  # Consumir resultado
            conn.commit()
            
            # Volver a consultar
            cursor.execute("""
            SELECT 
                s.symbol,
                pa.total_trades AS totalTrades,
                pa.total_pl AS totalPL,
                pa.winning_trades AS winningTrades,
                pa.win_rate AS winRate,
                pa.analytics_data
            FROM processed_analytics pa
            JOIN symbols s ON pa.symbol_id = s.symbol_id
            WHERE pa.analytics_type = 'symbol'
            AND pa.analytics_date = %s
            ORDER BY pa.total_pl DESC
            """, (start_date,))
            
            rows = cursor.fetchall()
        
        # Procesar resultados
        symbol_performance = []
        for row in rows:
            # Convertir JSON si es necesario
            if 'analytics_data' in row and isinstance(row['analytics_data'], str):
                import json
                row['analytics_data'] = json.loads(row['analytics_data'])
            
            symbol_performance.append({
                'symbol': row['symbol'],
                'totalTrades': row['totalTrades'],
                'totalPL': row['totalPL'],
                'winningTrades': row['winningTrades'],
                'winRate': row['winRate']
            })
        
        return symbol_performance
        
    except Exception as e:
        print(f"Error obteniendo rendimiento por símbolo: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def get_time_performance(start_date=None, end_date=None):
    """
    Obtiene el rendimiento por hora desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        list: Lista de rendimiento por hora
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = datetime.now().date()
        
        # Consultar métricas por hora
        cursor.execute("""
        SELECT 
            JSON_EXTRACT(analytics_data, '$.hour') AS hour,
            total_trades AS totalTrades,
            total_pl AS totalPL,
            winning_trades AS winningTrades,
            win_rate AS winRate
        FROM processed_analytics
        WHERE analytics_type = 'hourly'
        AND analytics_date = %s
        ORDER BY JSON_EXTRACT(analytics_data, '$.hour')
        """, (start_date,))
        
        rows = cursor.fetchall()
        
        # Si no hay datos, calcular y reintentar
        if not rows:
            cursor.execute(f"CALL calculate_hourly_metrics(%s, %s)", (start_date, end_date))
            cursor.fetchall()  # Consumir resultado
            conn.commit()
            
            # Volver a consultar
            cursor.execute("""
            SELECT 
                JSON_EXTRACT(analytics_data, '$.hour') AS hour,
                total_trades AS totalTrades,
                total_pl AS totalPL,
                winning_trades AS winningTrades,
                win_rate AS winRate
            FROM processed_analytics
            WHERE analytics_type = 'hourly'
            AND analytics_date = %s
            ORDER BY JSON_EXTRACT(analytics_data, '$.hour')
            """, (start_date,))
            
            rows = cursor.fetchall()
        
        # Procesar resultados
        time_performance = []
        for row in rows:
            # Extraer hora como entero
            hour = row['hour']
            if isinstance(hour, str) and hour.startswith('"') and hour.endswith('"'):
                hour = int(hour.strip('"'))
            
            time_performance.append({
                'hour': hour,
                'totalTrades': row['totalTrades'],
                'totalPL': row['totalPL'],
                'winningTrades': row['winningTrades'],
                'winRate': row['winRate']
            })
        
        return time_performance
        
    except Exception as e:
        print(f"Error obteniendo rendimiento por hora: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def get_buysell_performance(start_date=None, end_date=None):
    """
    Obtiene el rendimiento por tipo (compra/venta) desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        list: Lista de rendimiento por tipo
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = datetime.now().date()
        
        # Consultar rendimiento por tipo
        cursor.execute("""
        SELECT 
            o.side,
            COUNT(DISTINCT o.order_id) AS totalTrades,
            SUM(
                CASE 
                    WHEN o.side = 'B' THEN (o.price - COALESCE(AVG_EXEC_PRICE.avg_price, 0)) * o.quantity
                    ELSE (COALESCE(AVG_EXEC_PRICE.avg_price, 0) - o.price) * o.quantity
                END
            ) - COALESCE(SUM(tc.commission + tc.route_fee), 0) AS totalPL,
            SUM(
                CASE WHEN 
                    (o.side = 'B' AND (o.price - COALESCE(AVG_EXEC_PRICE.avg_price, 0)) * o.quantity > 0) OR
                    (o.side = 'S' AND (COALESCE(AVG_EXEC_PRICE.avg_price, 0) - o.price) * o.quantity > 0)
                THEN 1 ELSE 0 END
            ) AS winningTrades,
            100 * (
                SUM(
                    CASE WHEN 
                        (o.side = 'B' AND (o.price - COALESCE(AVG_EXEC_PRICE.avg_price, 0)) * o.quantity > 0) OR
                        (o.side = 'S' AND (COALESCE(AVG_EXEC_PRICE.avg_price, 0) - o.price) * o.quantity > 0)
                    THEN 1 ELSE 0 END
                ) / COUNT(DISTINCT o.order_id)
            ) AS winRate
        FROM 
            orders o
            LEFT JOIN (
                SELECT 
                    tr.order_id,
                    SUM(tr.price * tr.quantity) / SUM(tr.quantity) AS avg_price
                FROM 
                    trades tr
                GROUP BY 
                    tr.order_id
            ) AS AVG_EXEC_PRICE ON o.order_id = AVG_EXEC_PRICE.order_id
            LEFT JOIN (
                SELECT 
                    tr.order_id,
                    SUM(tk.commission) AS commission,
                    SUM(tk.route_fee) AS route_fee
                FROM 
                    trades tr
                    JOIN tickets tk ON tr.trade_id = tk.trade_id
                GROUP BY 
                    tr.order_id
            ) AS tc ON o.order_id = tc.order_id
        WHERE 
            DATE(o.order_time) BETWEEN %s AND %s
        GROUP BY 
            o.side
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        
        # Procesar resultados
        buysell_performance = []
        for row in rows:
            side_type = 'Compras' if row['side'] == 'B' else 'Ventas'
            
            buysell_performance.append({
                'type': side_type,
                'totalTrades': row['totalTrades'],
                'totalPL': row['totalPL'],
                'winningTrades': row['winningTrades'],
                'winRate': row['winRate']
            })
        
        return buysell_performance
        
    except Exception as e:
        print(f"Error obteniendo rendimiento por tipo: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def get_all_processed_data(start_date=None, end_date=None):
    """
    Obtiene todos los datos procesados desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        dict: Datos procesados completos
    """
    # Si no se especifican fechas, usar últimos 30 días
    if not start_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    elif not end_date:
        end_date = datetime.now().date()
    
    # Obtener todas las métricas
    daily_data = get_daily_metrics(start_date, end_date)
    symbol_performance = get_symbol_performance(start_date, end_date)
    time_performance = get_time_performance(start_date, end_date)
    buysell_performance = get_buysell_performance(start_date, end_date)
    
    # Consultar órdenes procesadas (limitadas a 1000 para rendimiento)
    processed_orders = get_processed_orders_from_db(start_date, end_date, limit=1000)
    
    # Construir objeto de datos procesados
    processed_data = {
        'metrics': daily_data['metrics'],
        'symbol_performance': symbol_performance,
        'time_performance': time_performance,
        'buysell_performance': buysell_performance,
        'equity_curve': daily_data['equity_curve'],
        'processed_orders': processed_orders
    }
    
    return processed_data

def get_available_symbols(start_date=None, end_date=None):
    """
    Obtiene la lista de símbolos disponibles en la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
    
    Returns:
        list: Lista de símbolos
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Consulta base
        query = """
        SELECT DISTINCT s.symbol 
        FROM symbols s
        JOIN orders o ON s.symbol_id = o.symbol_id
        WHERE 1=1
        """
        params = []
        
        # Añadir filtros de fecha si se especifican
        if start_date:
            query += " AND DATE(o.order_time) >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(o.order_time) <= %s"
            params.append(end_date)
        
        # Ordenar por símbolo
        query += " ORDER BY s.symbol"
        
        # Ejecutar consulta
        cursor.execute(query, params)
        symbols = [row[0] for row in cursor.fetchall()]
        
        return symbols
        
    except Exception as e:
        print(f"Error obteniendo símbolos disponibles: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def get_available_date_range():
    """
    Obtiene el rango de fechas disponibles en la base de datos
    
    Returns:
        tuple: (fecha_inicio, fecha_fin)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Consultar fecha más antigua y más reciente
        cursor.execute("""
        SELECT 
            MIN(DATE(order_time)) as min_date, 
            MAX(DATE(order_time)) as max_date 
        FROM orders
        """)
        
        result = cursor.fetchone()
        
        if result and result[0] and result[1]:
            return (result[0], result[1])
        else:
            # Si no hay datos, devolver fecha actual
            today = datetime.now().date()
            return (today, today)
        
    except Exception as e:
        print(f"Error obteniendo rango de fechas: {e}")
        today = datetime.now().date()
        return (today, today)
        
    finally:
        cursor.close()
        conn.close()

def get_trading_alerts(active_only=True):
    """
    Obtiene las alertas de trading desde la base de datos
    
    Args:
        active_only: Si es True, solo devuelve alertas activas
    
    Returns:
        list: Lista de alertas
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Construir consulta
        query = """
        SELECT 
            alert_id,
            alert_name,
            alert_description,
            alert_conditions,
            is_active,
            created_at,
            updated_at
        FROM trading_alerts
        """
        
        if active_only:
            query += " WHERE is_active = TRUE"
            
        query += " ORDER BY created_at DESC"
        
        # Ejecutar consulta
        cursor.execute(query)
        alerts = cursor.fetchall()
        
        # Procesar resultados (convertir JSON)
        processed_alerts = []
        for alert in alerts:
            # Convertir conditions de JSON a dict si es necesario
            if 'alert_conditions' in alert and isinstance(alert['alert_conditions'], str):
                import json
                alert['alert_conditions'] = json.loads(alert['alert_conditions'])
                
            processed_alerts.append(alert)
        
        return processed_alerts
        
    except Exception as e:
        print(f"Error obteniendo alertas: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def add_trading_alert(name, conditions, description=None):
    """
    Añade una nueva alerta de trading a la base de datos
    
    Args:
        name: Nombre de la alerta
        conditions: Condiciones de la alerta (dict)
        description: Descripción de la alerta (opcional)
    
    Returns:
        int: ID de la alerta creada o None si hay error
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convertir condiciones a JSON si es un dict
        if isinstance(conditions, dict):
            import json
            conditions_json = json.dumps(conditions)
        else:
            conditions_json = conditions
            
        # Insertar alerta
        cursor.execute("""
        INSERT INTO trading_alerts (
            alert_name,
            alert_description,
            alert_conditions,
            is_active,
            created_at
        ) VALUES (%s, %s, %s, TRUE, NOW())
        """, (name, description, conditions_json))
        
        # Obtener ID insertado
        alert_id = cursor.lastrowid
        
        # Confirmar transacción
        conn.commit()
        
        return alert_id
        
    except Exception as e:
        conn.rollback()
        print(f"Error añadiendo alerta: {e}")
        return None
        
    finally:
        cursor.close()
        conn.close()

def update_trading_alert(alert_id, name=None, conditions=None, description=None, is_active=None):
    """
    Actualiza una alerta de trading existente
    
    Args:
        alert_id: ID de la alerta a actualizar
        name: Nuevo nombre (opcional)
        conditions: Nuevas condiciones (opcional)
        description: Nueva descripción (opcional)
        is_active: Nuevo estado (opcional)
    
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Construir query de actualización
        query = "UPDATE trading_alerts SET updated_at = NOW()"
        params = []
        
        if name is not None:
            query += ", alert_name = %s"
            params.append(name)
            
        if description is not None:
            query += ", alert_description = %s"
            params.append(description)
            
        if conditions is not None:
            # Convertir condiciones a JSON si es un dict
            if isinstance(conditions, dict):
                import json
                conditions_json = json.dumps(conditions)
            else:
                conditions_json = conditions
                
            query += ", alert_conditions = %s"
            params.append(conditions_json)
            
        if is_active is not None:
            query += ", is_active = %s"
            params.append(is_active)
            
        # Añadir condición WHERE
        query += " WHERE alert_id = %s"
        params.append(alert_id)
        
        # Ejecutar actualización
        cursor.execute(query, params)
        
        # Confirmar transacción
        conn.commit()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        conn.rollback()
        print(f"Error actualizando alerta: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

def disable_trading_alert(alert_id):
    """
    Desactiva una alerta de trading
    
    Args:
        alert_id: ID de la alerta a desactivar
    
    Returns:
        bool: True si la desactivación fue exitosa, False en caso contrario
    """
    return update_trading_alert(alert_id, is_active=False)

def check_trading_alerts(orders=None, start_date=None, end_date=None):
    """
    Verifica las alertas de trading contra un conjunto de órdenes
    
    Args:
        orders: Lista de órdenes (opcional)
        start_date: Fecha de inicio para filtrar órdenes (opcional)
        end_date: Fecha de fin para filtrar órdenes (opcional)
    
    Returns:
        list: Lista de alertas disparadas con órdenes coincidentes
    """
    # Obtener alertas activas
    alerts = get_trading_alerts(active_only=True)
    
    # Si no hay órdenes especificadas, obtenerlas de la base de datos
    if orders is None:
        orders = get_processed_orders_from_db(start_date, end_date)
    
    # Resultados de alertas disparadas
    triggered_alerts = []
    
    # Verificar cada alerta
    for alert in alerts:
        conditions = alert['alert_conditions']
        matching_orders = []
        
        # Verificar cada orden contra las condiciones de la alerta
        for order in orders:
            match = True
            
            # Condiciones de símbolo
            if 'symbol' in conditions and conditions['symbol']:
                match = match and order['symb'] in conditions['symbol']
            
            # Condiciones de tipo de operación (compra/venta)
            if 'side' in conditions and conditions['side']:
                match = match and order['B/S'] in conditions['side']
            
            # Condiciones de cantidad
            if 'min_quantity' in conditions and conditions['min_quantity'] > 0:
                match = match and order['qty'] >= conditions['min_quantity']
            
            # Condiciones de precio
            if 'price_range' in conditions:
                min_price, max_price = conditions['price_range']
                
                if min_price > 0:
                    match = match and order['price'] >= min_price
                    
                if max_price < float('inf'):
                    match = match and order['price'] <= max_price
            
            # Si todas las condiciones coinciden, añadir a órdenes coincidentes
            if match:
                matching_orders.append(order)
        
        # Si hay órdenes coincidentes, registrar alerta disparada
        if matching_orders:
            triggered_alerts.append({
                'alert': alert,
                'matching_orders': matching_orders,
                'triggered_at': datetime.now()
            })
            
            # Registrar el disparo de la alerta en la base de datos
            record_alert_trigger(alert['alert_id'], matching_orders)
    
    return triggered_alerts

def record_alert_trigger(alert_id, matching_orders):
    """
    Registra el disparo de una alerta en la base de datos
    
    Args:
        alert_id: ID de la alerta disparada
        matching_orders: Lista de órdenes coincidentes
    
    Returns:
        int: ID del registro o None si hay error
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convertir órdenes a JSON (solo IDs para ahorrar espacio)
        import json
        order_ids = [order['OrderID'] for order in matching_orders]
        matching_json = json.dumps(order_ids)
        
        # Insertar registro
        cursor.execute("""
        INSERT INTO alert_triggers (
            alert_id,
            trigger_time,
            matching_orders,
            notes
        ) VALUES (%s, NOW(), %s, %s)
        """, (alert_id, matching_json, f"Alerta disparada con {len(matching_orders)} órdenes coincidentes"))
        
        # Obtener ID insertado
        trigger_id = cursor.lastrowid
        
        # Confirmar transacción
        conn.commit()
        
        return trigger_id
        
    except Exception as e:
        conn.rollback()
        print(f"Error registrando disparo de alerta: {e}")
        return None
        
    finally:
        cursor.close()
        conn.close()

def get_triggered_alerts(start_date=None, end_date=None, alert_id=None):
    """
    Obtiene las alertas disparadas desde la base de datos
    
    Args:
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        alert_id: ID de la alerta específica a buscar (opcional)
    
    Returns:
        list: Lista de alertas disparadas
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Consulta base
        query = """
        SELECT 
            t.trigger_id,
            t.alert_id,
            t.trigger_time,
            t.matching_orders,
            t.notes,
            a.alert_name,
            a.alert_description,
            a.alert_conditions
        FROM alert_triggers t
        JOIN trading_alerts a ON t.alert_id = a.alert_id
        WHERE 1=1
        """
        params = []
        
        # Añadir filtros
        if start_date:
            query += " AND DATE(t.trigger_time) >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(t.trigger_time) <= %s"
            params.append(end_date)
            
        if alert_id:
            query += " AND t.alert_id = %s"
            params.append(alert_id)
            
        # Ordenar por fecha/hora descendente
        query += " ORDER BY t.trigger_time DESC"
        
        # Ejecutar consulta
        cursor.execute(query, params)
        triggers = cursor.fetchall()
        
        # Procesar resultados
        processed_triggers = []
        for trigger in triggers:
            # Convertir JSON a listas/diccionarios
            import json
            
            # Convertir matching_orders
            if 'matching_orders' in trigger and isinstance(trigger['matching_orders'], str):
                order_ids = json.loads(trigger['matching_orders'])
                
                # Obtener detalles de las órdenes
                matching_orders = []
                if order_ids:
                    # Consultar órdenes por ID
                    placeholders = ', '.join(['%s'] * len(order_ids))
                    order_query = f"""
                    SELECT * FROM vw_processed_orders 
                    WHERE OrderID IN ({placeholders})
                    """
                    
                    order_cursor = conn.cursor(dictionary=True)
                    order_cursor.execute(order_query, order_ids)
                    matching_orders = order_cursor.fetchall()
                    order_cursor.close()
                
                trigger['matching_orders'] = matching_orders
            
            # Convertir alert_conditions
            if 'alert_conditions' in trigger and isinstance(trigger['alert_conditions'], str):
                trigger['alert_conditions'] = json.loads(trigger['alert_conditions'])
                
            # Reconstruir objeto de alerta para mantener compatibilidad
            trigger['alert'] = {
                'alert_id': trigger['alert_id'],
                'name': trigger['alert_name'],
                'description': trigger['alert_description'],
                'conditions': trigger['alert_conditions']
            }
            
            processed_triggers.append(trigger)
        
        return processed_triggers
        
    except Exception as e:
        print(f"Error obteniendo alertas disparadas: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()
        
def summarize_database_stats():
    """
    Genera un resumen estadístico de la base de datos
    
    Returns:
        dict: Estadísticas de la base de datos
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Contar registros en tablas principales
        for table in ['orders', 'trades', 'tickets', 'symbols', 'traders', 'accounts', 'trading_alerts']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[f"{table}_count"] = count
        
        # Obtener rango de fechas
        cursor.execute("SELECT MIN(order_time), MAX(order_time) FROM orders")
        date_range = cursor.fetchone()
        if date_range and date_range[0] and date_range[1]:
            stats['first_date'] = date_range[0].strftime('%Y-%m-%d')
            stats['last_date'] = date_range[1].strftime('%Y-%m-%d')
            
            # Calcular días con datos
            cursor.execute("SELECT COUNT(DISTINCT DATE(order_time)) FROM orders")
            stats['days_with_data'] = cursor.fetchone()[0]
        
        # Obtener top 5 símbolos
        cursor.execute("""
        SELECT s.symbol, COUNT(*) as count
        FROM orders o
        JOIN symbols s ON o.symbol_id = s.symbol_id
        GROUP BY s.symbol
        ORDER BY count DESC
        LIMIT 5
        """)
        stats['top_symbols'] = [{'symbol': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Obtener P&L total
        cursor.execute("""
        SELECT 
            SUM(
                CASE 
                    WHEN o.side = 'B' THEN (o.price - COALESCE(AVG_EXEC_PRICE.avg_price, 0)) * o.quantity
                    ELSE (COALESCE(AVG_EXEC_PRICE.avg_price, 0) - o.price) * o.quantity
                END
            ) - COALESCE(SUM(tc.commission + tc.route_fee), 0) AS totalPL
        FROM 
            orders o
            LEFT JOIN (
                SELECT 
                    tr.order_id,
                    SUM(tr.price * tr.quantity) / SUM(tr.quantity) AS avg_price
                FROM 
                    trades tr
                GROUP BY 
                    tr.order_id
            ) AS AVG_EXEC_PRICE ON o.order_id = AVG_EXEC_PRICE.order_id
            LEFT JOIN (
                SELECT 
                    tr.order_id,
                    SUM(tk.commission) AS commission,
                    SUM(tk.route_fee) AS route_fee
                FROM 
                    trades tr
                    JOIN tickets tk ON tr.trade_id = tk.trade_id
                GROUP BY 
                    tr.order_id
            ) AS tc ON o.order_id = tc.order_id
        """)
        total_pl_result = cursor.fetchone()
        stats['total_pl'] = total_pl_result[0] if total_pl_result and total_pl_result[0] else 0
        
        # Obtener importaciones recientes
        cursor.execute("""
        SELECT 
            import_date, 
            orders_count, 
            trades_count, 
            tickets_count,
            status,
            import_time
        FROM data_imports
        ORDER BY import_time DESC
        LIMIT 5
        """)
        stats['recent_imports'] = []
        for row in cursor.fetchall():
            import_date, orders, trades, tickets, status, import_time = row
            stats['recent_imports'].append({
                'date': import_date.strftime('%Y-%m-%d'),
                'orders': orders,
                'trades': trades,
                'tickets': tickets,
                'status': status,
                'time': import_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return stats
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return {'error': str(e)}
        
    finally:
        cursor.close()
        conn.close()

def diagnose_database_connection():
    """
    Diagnostica problemas de conexión a la base de datos
    
    Returns:
        dict: Resultado del diagnóstico
    """
    result = {
        'status': 'unknown',
        'connection': False,
        'tables_exist': False,
        'data_available': False,
        'errors': []
    }
    
# Probar conexión
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        result['connection'] = True
        
        # Probar existencia de tablas principales
        required_tables = ['orders', 'trades', 'tickets', 'symbols', 'traders', 'accounts']
        existing_tables = []
        
        cursor.execute("SHOW TABLES")
        table_rows = cursor.fetchall()
        all_tables = [row[0] for row in table_rows]
        
        for table in required_tables:
            if table in all_tables:
                existing_tables.append(table)
        
        if len(existing_tables) == len(required_tables):
            result['tables_exist'] = True
        else:
            missing_tables = set(required_tables) - set(existing_tables)
            result['errors'].append(f"Faltan tablas: {', '.join(missing_tables)}")
        
        # Verificar si hay datos
        if result['tables_exist']:
            cursor.execute("SELECT COUNT(*) FROM orders")
            orders_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades")
            trades_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tickets")
            tickets_count = cursor.fetchone()[0]
            
            result['data_counts'] = {
                'orders': orders_count,
                'trades': trades_count,
                'tickets': tickets_count
            }
            
            result['data_available'] = (orders_count > 0) and (trades_count > 0)
            
            if not result['data_available']:
                result['errors'].append("No hay datos suficientes en las tablas principales")
        
        # Comprobar procedimientos almacenados
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = DATABASE()")
        procedures = cursor.fetchall()
        procedure_names = [proc[1] for proc in procedures]
        
        required_procedures = [
            'import_orders_from_temp',
            'import_trades_from_temp',
            'import_tickets_from_temp',
            'calculate_daily_metrics',
            'calculate_symbol_metrics',
            'calculate_hourly_metrics'
        ]
        
        missing_procedures = set(required_procedures) - set(procedure_names)
        if missing_procedures:
            result['errors'].append(f"Faltan procedimientos almacenados: {', '.join(missing_procedures)}")
            
        # Determinar estado general
        if result['connection'] and result['tables_exist'] and result['data_available'] and not result['errors']:
            result['status'] = 'ok'
        elif result['connection'] and result['tables_exist']:
            result['status'] = 'warning'
        else:
            result['status'] = 'error'
            
    except Exception as e:
        result['errors'].append(str(e))
        result['status'] = 'error'
        
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
    
    return result

def optimize_database():
    """
    Realiza optimizaciones básicas en la base de datos
    
    Returns:
        dict: Resultado de la optimización
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = {
        'status': 'unknown',
        'actions': [],
        'errors': []
    }
    
    try:
        # Analizar tablas principales
        tables_to_optimize = ['orders', 'trades', 'tickets', 'processed_analytics']
        
        for table in tables_to_optimize:
            try:
                # Analizar tabla
                cursor.execute(f"ANALYZE TABLE {table}")
                cursor.fetchall()  # Consumir resultado
                result['actions'].append(f"Tabla {table} analizada")
                
                # Optimizar tabla
                cursor.execute(f"OPTIMIZE TABLE {table}")
                cursor.fetchall()  # Consumir resultado
                result['actions'].append(f"Tabla {table} optimizada")
            except Exception as e:
                result['errors'].append(f"Error optimizando tabla {table}: {str(e)}")
        
        # Limpiar datos antiguos de procesamiento si hay muchos
        try:
            # Verificar cantidad de registros en processed_analytics
            cursor.execute("SELECT COUNT(*) FROM processed_analytics")
            analytics_count = cursor.fetchone()[0]
            
            if analytics_count > 10000:
                # Eliminar registros antiguos (más de 90 días)
                ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                cursor.execute(f"DELETE FROM processed_analytics WHERE analytics_date < '{ninety_days_ago}'")
                deleted_count = cursor.rowcount
                conn.commit()
                
                result['actions'].append(f"Eliminados {deleted_count} registros antiguos de análisis")
        except Exception as e:
            result['errors'].append(f"Error limpiando datos antiguos: {str(e)}")
            conn.rollback()
        
        # Determinar estado general
        if not result['errors']:
            result['status'] = 'ok'
        elif len(result['actions']) > len(result['errors']):
            result['status'] = 'partial'
        else:
            result['status'] = 'error'
            
    except Exception as e:
        result['errors'].append(str(e))
        result['status'] = 'error'
        conn.rollback()
        
    finally:
        cursor.close()
        conn.close()
    
    return result

def get_database_size():
    """
    Obtiene información sobre el tamaño de la base de datos
    
    Returns:
        dict: Información de tamaño
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener tamaño de la base de datos
        cursor.execute("""
        SELECT 
            table_schema AS database_name,
            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        GROUP BY table_schema
        """)
        
        result = cursor.fetchone()
        db_size = result[1] if result else 0
        
        # Obtener tamaño por tabla
        cursor.execute("""
        SELECT 
            table_name,
            ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
            table_rows
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY (data_length + index_length) DESC
        """)
        
        tables = []
        for row in cursor.fetchall():
            tables.append({
                'name': row[0],
                'size_mb': row[1],
                'rows': row[2]
            })
        
        return {
            'total_size_mb': db_size,
            'tables': tables
        }
        
    except Exception as e:
        print(f"Error obteniendo tamaño de base de datos: {e}")
        return {
            'total_size_mb': 0,
            'tables': [],
            'error': str(e)
        }
        
    finally:
        cursor.close()
        conn.close()

# Exportar todas las funciones necesarias para la aplicación principal
__all__ = [
    'init_db_pool',
    'get_db_connection',
    'get_db',
    'close_db',
    'init_app',
    'create_tables_if_not_exist',
    'import_orders_to_db',
    'import_trades_to_db',
    'import_tickets_to_db',
    'import_data_to_db',
    'get_processed_orders_from_db',
    'get_daily_metrics',
    'get_symbol_performance',
    'get_time_performance',
    'get_buysell_performance',
    'get_all_processed_data',
    'get_available_symbols',
    'get_available_date_range',
    'get_trading_alerts',
    'add_trading_alert',
    'update_trading_alert',
    'disable_trading_alert',
    'check_trading_alerts',
    'get_triggered_alerts',
    'summarize_database_stats',
    'diagnose_database_connection',
    'optimize_database',
    'get_database_size'
]