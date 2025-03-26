-- Esquema de Base de Datos para DAS Trader Analyzer
-- Permite almacenamiento histórico de datos exportados de DAS Trader

-- Creación de la base de datos
CREATE DATABASE IF NOT EXISTS das_trader_analyzer;
USE das_trader_analyzer;

-- Tabla de símbolos (instrumentos)
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    description VARCHAR(255),
    UNIQUE KEY unique_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de traders
CREATE TABLE IF NOT EXISTS traders (
    trader_id INT AUTO_INCREMENT PRIMARY KEY,
    trader_name VARCHAR(50) NOT NULL,
    UNIQUE KEY unique_trader (trader_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de cuentas
CREATE TABLE IF NOT EXISTS accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(50) NOT NULL,
    trader_id INT,
    branch VARCHAR(50),
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id),
    UNIQUE KEY unique_account (account_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de rutas de ejecución
CREATE TABLE IF NOT EXISTS routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(20) NOT NULL,
    UNIQUE KEY unique_route (route_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de órdenes (Orders)
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(20) PRIMARY KEY,
    trader_id INT NOT NULL,
    account_id INT NOT NULL,
    route_id INT NOT NULL,
    symbol_id INT NOT NULL,
    broker_symbol VARCHAR(20),
    rrno VARCHAR(20),
    side CHAR(1) NOT NULL,              -- 'B' para compra, 'S' para venta
    short_flag CHAR(1) NOT NULL,        -- 'Y' o 'N'
    market_type VARCHAR(20),
    stop_flag CHAR(1),                  -- 'Y' o 'N'
    quantity DECIMAL(15,2) NOT NULL,
    leaves_quantity DECIMAL(15,2),
    price DECIMAL(15,4),
    stop_price DECIMAL(15,4),
    trail_price DECIMAL(15,4),
    order_time DATETIME NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id),
    INDEX idx_order_date (order_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de trades
CREATE TABLE IF NOT EXISTS trades (
    trade_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    trader_id INT NOT NULL,
    account_id INT NOT NULL,
    route_id INT NOT NULL,
    symbol_id INT NOT NULL,
    broker_symbol VARCHAR(20),
    rrno VARCHAR(20),
    side CHAR(1) NOT NULL,
    short_flag CHAR(1) NOT NULL,
    market_type VARCHAR(20),
    quantity DECIMAL(15,2) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    trade_time DATETIME NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id),
    INDEX idx_trade_date (trade_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de tickets (comisiones y fees)
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    trade_id VARCHAR(20) NOT NULL,
    trader_id INT NOT NULL,
    account_id INT NOT NULL,
    route_id INT NOT NULL,
    symbol_id INT NOT NULL,
    broker_symbol VARCHAR(20),
    rrno VARCHAR(20),
    side CHAR(1) NOT NULL,
    short_flag CHAR(1) NOT NULL,
    market_type VARCHAR(20),
    quantity DECIMAL(15,2) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    commission DECIMAL(15,4) NOT NULL,
    route_fee DECIMAL(15,4) NOT NULL,
    ticket_time DATETIME NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id),
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id),
    INDEX idx_ticket_date (ticket_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para análisis procesados (para almacenar cálculos frecuentes)
CREATE TABLE IF NOT EXISTS processed_analytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,
    analytics_date DATE NOT NULL,
    analytics_type VARCHAR(50) NOT NULL,  -- 'daily', 'symbol', 'intraday', etc.
    symbol_id INT,
    trader_id INT,
    total_trades INT,
    total_pl DECIMAL(15,4),
    winning_trades INT,
    losing_trades INT,
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(10,4),
    max_drawdown DECIMAL(15,4),
    avg_win DECIMAL(15,4),
    avg_loss DECIMAL(15,4),
    analytics_data JSON,    -- Para almacenar datos variables según el tipo de análisis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id),
    FOREIGN KEY (trader_id) REFERENCES traders(trader_id),
    UNIQUE KEY unique_analytics (analytics_date, analytics_type, symbol_id, trader_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para alertas de trading
CREATE TABLE IF NOT EXISTS trading_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_name VARCHAR(100) NOT NULL,
    alert_description TEXT,
    alert_conditions JSON NOT NULL,  -- Almacena las condiciones de la alerta en formato JSON
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para registrar alertas disparadas
CREATE TABLE IF NOT EXISTS alert_triggers (
    trigger_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    trigger_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    matching_orders JSON,  -- Almacena IDs de órdenes que dispararon la alerta
    notes TEXT,
    FOREIGN KEY (alert_id) REFERENCES trading_alerts(alert_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para importaciones de datos
CREATE TABLE IF NOT EXISTS data_imports (
    import_id INT AUTO_INCREMENT PRIMARY KEY,
    import_date DATE NOT NULL,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    orders_count INT DEFAULT 0,
    trades_count INT DEFAULT 0,
    tickets_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'completed',
    notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices adicionales para consultas frecuentes
CREATE INDEX idx_order_trader_date ON orders(trader_id, order_time);
CREATE INDEX idx_order_symbol_date ON orders(symbol_id, order_time);
CREATE INDEX idx_trade_symbol_date ON trades(symbol_id, trade_time);

-- Vista para órdenes procesadas (similar a la estructura actual en memoria)
CREATE OR REPLACE VIEW vw_processed_orders AS
SELECT 
    o.order_id AS OrderID,
    t.trader_name AS Trader,
    a.account_number AS Account,
    a.branch AS Branch,
    r.route_name AS route,
    o.broker_symbol AS bkrsym,
    o.rrno AS rrno,
    o.side AS `B/S`,
    o.short_flag AS SHORT,
    o.market_type AS Market,
    o.stop_flag AS stop,
    s.symbol AS symb,
    o.quantity AS qty,
    o.leaves_quantity AS lvsqty,
    o.price AS price,
    o.stop_price AS stopprice,
    o.trail_price AS trailprice,
    o.order_time AS time,
    HOUR(o.order_time) AS hour,
    DATE(o.order_time) AS date
FROM 
    orders o
    JOIN traders t ON o.trader_id = t.trader_id
    JOIN accounts a ON o.account_id = a.account_id
    JOIN routes r ON o.route_id = r.route_id
    JOIN symbols s ON o.symbol_id = s.symbol_id;

-- Vista para análisis de rendimiento por símbolo
CREATE OR REPLACE VIEW vw_symbol_performance AS
SELECT 
    s.symbol,
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
    symbols s
    JOIN orders o ON s.symbol_id = o.symbol_id
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
GROUP BY 
    s.symbol
ORDER BY 
    totalPL DESC;

-- Procedimiento para importar órdenes desde un archivo CSV temporal
DELIMITER //

CREATE PROCEDURE import_orders_from_temp(IN temp_table_name VARCHAR(100))
BEGIN
    DECLARE import_date_val DATE;
    DECLARE orders_imported INT DEFAULT 0;
    
    -- Establecer fecha de importación
    SET import_date_val = CURDATE();
    
    -- Insertar traders que no existan
    INSERT IGNORE INTO traders (trader_name)
    SELECT DISTINCT Trader FROM temp_table_name;
    
    -- Insertar cuentas que no existan
    INSERT IGNORE INTO accounts (account_number, branch, trader_id)
    SELECT DISTINCT 
        t.Account, 
        t.Branch, 
        tr.trader_id
    FROM 
        temp_table_name t
        JOIN traders tr ON t.Trader = tr.trader_name;
    
    -- Insertar rutas que no existan
    INSERT IGNORE INTO routes (route_name)
    SELECT DISTINCT route FROM temp_table_name;
    
    -- Insertar símbolos que no existan
    INSERT IGNORE INTO symbols (symbol)
    SELECT DISTINCT symb FROM temp_table_name;
    
    -- Insertar órdenes
    INSERT INTO orders (
        order_id, trader_id, account_id, route_id, symbol_id, 
        broker_symbol, rrno, side, short_flag, market_type, 
        stop_flag, quantity, leaves_quantity, price, 
        stop_price, trail_price, order_time
    )
    SELECT 
        t.OrderID,
        tr.trader_id,
        a.account_id,
        r.route_id,
        s.symbol_id,
        t.bkrsym,
        t.rrno,
        t.`B/S`,
        t.SHORT,
        t.Market,
        t.stop,
        t.qty,
        t.lvsqty,
        t.price,
        t.stopprice,
        t.trailprice,
        STR_TO_DATE(t.time, '%Y-%m-%d %H:%i:%s')
    FROM 
        temp_table_name t
        JOIN traders tr ON t.Trader = tr.trader_name
        JOIN accounts a ON t.Account = a.account_number AND tr.trader_id = a.trader_id
        JOIN routes r ON t.route = r.route_name
        JOIN symbols s ON t.symb = s.symbol
    ON DUPLICATE KEY UPDATE 
        trader_id = VALUES(trader_id),
        account_id = VALUES(account_id),
        route_id = VALUES(route_id),
        symbol_id = VALUES(symbol_id),
        broker_symbol = VALUES(broker_symbol),
        rrno = VALUES(rrno),
        side = VALUES(side),
        short_flag = VALUES(short_flag),
        market_type = VALUES(market_type),
        stop_flag = VALUES(stop_flag),
        quantity = VALUES(quantity),
        leaves_quantity = VALUES(leaves_quantity),
        price = VALUES(price),
        stop_price = VALUES(stop_price),
        trail_price = VALUES(trail_price),
        order_time = VALUES(order_time);
        
    -- Contar órdenes importadas
    SET orders_imported = ROW_COUNT();
    
    -- Registrar la importación
    INSERT INTO data_imports (import_date, orders_count, status)
    VALUES (import_date_val, orders_imported, 'completed');
    
    -- Devolver el número de órdenes importadas
    SELECT orders_imported AS 'Orders Imported';
END //

-- Procedimiento para importar trades desde un archivo CSV temporal
CREATE PROCEDURE import_trades_from_temp(IN temp_table_name VARCHAR(100))
BEGIN
    DECLARE import_date_val DATE;
    DECLARE trades_imported INT DEFAULT 0;
    
    -- Establecer fecha de importación
    SET import_date_val = CURDATE();
    
    -- Insertar traders que no existan
    INSERT IGNORE INTO traders (trader_name)
    SELECT DISTINCT Trader FROM temp_table_name;
    
    -- Insertar cuentas que no existan
    INSERT IGNORE INTO accounts (account_number, branch, trader_id)
    SELECT DISTINCT 
        t.Account, 
        t.Branch, 
        tr.trader_id
    FROM 
        temp_table_name t
        JOIN traders tr ON t.Trader = tr.trader_name;
    
    -- Insertar rutas que no existan
    INSERT IGNORE INTO routes (route_name)
    SELECT DISTINCT route FROM temp_table_name;
    
    -- Insertar símbolos que no existan
    INSERT IGNORE INTO symbols (symbol)
    SELECT DISTINCT symb FROM temp_table_name;
    
    -- Insertar trades
    INSERT INTO trades (
        trade_id, order_id, trader_id, account_id, route_id, symbol_id, 
        broker_symbol, rrno, side, short_flag, market_type, 
        quantity, price, trade_time
    )
    SELECT 
        t.TradeID,
        t.OrderID,
        tr.trader_id,
        a.account_id,
        r.route_id,
        s.symbol_id,
        t.bkrsym,
        t.rrno,
        t.`B/S`,
        t.SHORT,
        t.Market,
        t.qty,
        t.price,
        STR_TO_DATE(t.time, '%Y-%m-%d %H:%i:%s')
    FROM 
        temp_table_name t
        JOIN traders tr ON t.Trader = tr.trader_name
        JOIN accounts a ON t.Account = a.account_number AND tr.trader_id = a.trader_id
        JOIN routes r ON t.route = r.route_name
        JOIN symbols s ON t.symb = s.symbol
    ON DUPLICATE KEY UPDATE 
        order_id = VALUES(order_id),
        trader_id = VALUES(trader_id),
        account_id = VALUES(account_id),
        route_id = VALUES(route_id),
        symbol_id = VALUES(symbol_id),
        broker_symbol = VALUES(broker_symbol),
        rrno = VALUES(rrno),
        side = VALUES(side),
        short_flag = VALUES(short_flag),
        market_type = VALUES(market_type),
        quantity = VALUES(quantity),
        price = VALUES(price),
        trade_time = VALUES(trade_time);
        
    -- Contar trades importados
    SET trades_imported = ROW_COUNT();
    
    -- Actualizar el registro de importación
    UPDATE data_imports 
    SET trades_count = trades_imported
    WHERE import_date = import_date_val 
    ORDER BY import_time DESC
    LIMIT 1;
    
    -- Devolver el número de trades importados
    SELECT trades_imported AS 'Trades Imported';
END //

-- Procedimiento para importar tickets desde un archivo CSV temporal
CREATE PROCEDURE import_tickets_from_temp(IN temp_table_name VARCHAR(100))
BEGIN
    DECLARE import_date_val DATE;
    DECLARE tickets_imported INT DEFAULT 0;
    
    -- Establecer fecha de importación
    SET import_date_val = CURDATE();
    
    -- Insertar traders que no existan
    INSERT IGNORE INTO traders (trader_name)
    SELECT DISTINCT Trader FROM temp_table_name;
    
    -- Insertar cuentas que no existan
    INSERT IGNORE INTO accounts (account_number, branch, trader_id)
    SELECT DISTINCT 
        t.Account, 
        t.Branch, 
        tr.trader_id
    FROM 
        temp_table_name t
        JOIN traders tr ON t.Trader = tr.trader_name;
    
    -- Insertar rutas que no existan
    INSERT IGNORE INTO routes (route_name)
    SELECT DISTINCT route FROM temp_table_name;
    
    -- Insertar símbolos que no existan
    INSERT IGNORE INTO symbols (symbol)
    SELECT DISTINCT symb FROM temp_table_name;
    
    -- Insertar tickets
    INSERT INTO tickets (
        ticket_id, trade_id, trader_id, account_id, route_id, symbol_id, 
        broker_symbol, rrno, side, short_flag, market_type, 
        quantity, price, commission, route_fee, ticket_time
    )
    SELECT 
        t.TicketID,
        t.TradeID,
        tr.trader_id,
        a.account_id,
        r.route_id,
        s.symbol_id,
        t.bkrsym,
        t.rrno,
        t.`B/S`,
        t.SHORT,
        t.Market,
        t.qty,
        t.price,
        t.commission,
        t.RouteFee,
        STR_TO_DATE(t.time, '%Y-%m-%d %H:%i:%s')
    FROM 
        temp_table_name t
        JOIN traders tr ON t.Trader = tr.trader_name
        JOIN accounts a ON t.Account = a.account_number AND tr.trader_id = a.trader_id
        JOIN routes r ON t.route = r.route_name
        JOIN symbols s ON t.symb = s.symbol
    ON DUPLICATE KEY UPDATE 
        trade_id = VALUES(trade_id),
        trader_id = VALUES(trader_id),
        account_id = VALUES(account_id),
        route_id = VALUES(route_id),
        symbol_id = VALUES(symbol_id),
        broker_symbol = VALUES(broker_symbol),
        rrno = VALUES(rrno),
        side = VALUES(side),
        short_flag = VALUES(short_flag),
        market_type = VALUES(market_type),
        quantity = VALUES(quantity),
        price = VALUES(price),
        commission = VALUES(commission),
        route_fee = VALUES(route_fee),
        ticket_time = VALUES(ticket_time);
        
    -- Contar tickets importados
    SET tickets_imported = ROW_COUNT();
    
    -- Actualizar el registro de importación
    UPDATE data_imports 
    SET tickets_count = tickets_imported
    WHERE import_date = import_date_val 
    ORDER BY import_time DESC
    LIMIT 1;
    
    -- Devolver el número de tickets importados
    SELECT tickets_imported AS 'Tickets Imported';
END //

-- Procedimiento para calcular P&L y métricas para un rango de fechas
CREATE PROCEDURE calculate_daily_metrics(IN start_date DATE, IN end_date DATE)
BEGIN
    -- Insertar o actualizar registros en processed_analytics para análisis diario
    INSERT INTO processed_analytics (
        analytics_date, 
        analytics_type, 
        total_trades, 
        total_pl, 
        winning_trades, 
        losing_trades, 
        win_rate, 
        profit_factor, 
        max_drawdown, 
        avg_win, 
        avg_loss,
        analytics_data
    )
    WITH daily_pnl AS (
        SELECT 
            DATE(o.order_time) AS trade_date,
            o.order_id,
            -- Calcular P&L por operación
            CASE 
                WHEN o.side = 'B' THEN 
                    (o.price - COALESCE(
                        (SELECT SUM(tr.price * tr.quantity) / SUM(tr.quantity) 
                         FROM trades tr 
                         WHERE tr.order_id = o.order_id), 0)
                    ) * o.quantity
                ELSE 
                    (COALESCE(
                        (SELECT SUM(tr.price * tr.quantity) / SUM(tr.quantity) 
                         FROM trades tr 
                         WHERE tr.order_id = o.order_id), 0)
                    - o.price) * o.quantity
            END - COALESCE(
                (SELECT SUM(tk.commission + tk.route_fee) 
                 FROM trades tr 
                 JOIN tickets tk ON tr.trade_id = tk.trade_id 
                 WHERE tr.order_id = o.order_id), 0
            ) AS pnl
        FROM orders o
        WHERE DATE(o.order_time) BETWEEN start_date AND end_date
    ),
    daily_metrics AS (
        SELECT 
            trade_date,
            COUNT(*) AS total_trades,
            SUM(pnl) AS total_pl,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS winning_trades,
            SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) AS losing_trades,
            (SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS win_rate,
            CASE 
                WHEN SUM(CASE WHEN pnl <= 0 THEN ABS(pnl) ELSE 0 END) = 0 THEN NULL
                ELSE SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl <= 0 THEN ABS(pnl) ELSE 0 END)
            END AS profit_factor,
            CASE 
                WHEN SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
            END AS avg_win,
            CASE 
                WHEN SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN pnl <= 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END)
            END AS avg_loss,
            -- JSON con todos los PNL ordenados para calcular drawdown en la aplicación
            -- o calcular el drawdown aquí con una CTE más compleja
            0 AS max_drawdown,
            JSON_OBJECT(
                'pnl_values', JSON_ARRAYAGG(pnl),
                'symbols_count', (SELECT COUNT(DISTINCT o.symbol_id) 
                                 FROM orders o 
                                 WHERE DATE(o.order_time) = trade_date)
            ) AS analytics_data
        FROM daily_pnl
        GROUP BY trade_date
    )
    SELECT 
        dm.trade_date,
        'daily',
        dm.total_trades,
        dm.total_pl,
        dm.winning_trades,
        dm.losing_trades,
        dm.win_rate,
        dm.profit_factor,
        dm.max_drawdown,
        dm.avg_win,
        dm.avg_loss,
        dm.analytics_data
    FROM daily_metrics dm
    ON DUPLICATE KEY UPDATE
        total_trades = VALUES(total_trades),
        total_pl = VALUES(total_pl),
        winning_trades = VALUES(winning_trades),
        losing_trades = VALUES(losing_trades),
        win_rate = VALUES(win_rate),
        profit_factor = VALUES(profit_factor),
        max_drawdown = VALUES(max_drawdown),
        avg_win = VALUES(avg_win),
        avg_loss = VALUES(avg_loss),
        analytics_data = VALUES(analytics_data),
        updated_at = CURRENT_TIMESTAMP;
        
    -- Devolver los registros actualizados
    SELECT 
        analytics_date,
        total_trades,
        total_pl,
        winning_trades,
        losing_trades,
        win_rate,
        profit_factor,
        avg_win,
        avg_loss
    FROM processed_analytics 
    WHERE analytics_date BETWEEN start_date AND end_date
    AND analytics_type = 'daily'
    ORDER BY analytics_date;
END //

-- Procedimiento para calcular análisis por símbolo para un rango de fechas
CREATE PROCEDURE calculate_symbol_metrics(IN start_date DATE, IN end_date DATE)
BEGIN
    -- Insertar o actualizar registros para análisis por símbolo
    INSERT INTO processed_analytics (
        analytics_date, 
        analytics_type, 
        symbol_id,
        total_trades, 
        total_pl, 
        winning_trades, 
        losing_trades, 
        win_rate, 
        avg_win, 
        avg_loss,
        analytics_data
    )
    WITH symbol_pnl AS (
        SELECT 
            s.symbol_id,
            s.symbol,
            DATE(o.order_time) AS trade_date,
            o.order_id,
            CASE 
                WHEN o.side = 'B' THEN 
                    (o.price - COALESCE(
                        (SELECT SUM(tr.price * tr.quantity) / SUM(tr.quantity) 
                         FROM trades tr 
                         WHERE tr.order_id = o.order_id), 0)
                    ) * o.quantity
                ELSE 
                    (COALESCE(
                        (SELECT SUM(tr.price * tr.quantity) / SUM(tr.quantity) 
                         FROM trades tr 
                         WHERE tr.order_id = o.order_id), 0)
                    - o.price) * o.quantity
            END - COALESCE(
                (SELECT SUM(tk.commission + tk.route_fee) 
                 FROM trades tr 
                 JOIN tickets tk ON tr.trade_id = tk.trade_id 
                 WHERE tr.order_id = o.order_id), 0
            ) AS pnl
        FROM 
            symbols s
            JOIN orders o ON s.symbol_id = o.symbol_id
        WHERE 
            DATE(o.order_time) BETWEEN start_date AND end_date
    ) AS (
        SELECT 
            symbol_id,
            symbol,
            start_date AS analytics_date,
            'symbol' AS analytics_type,
            COUNT(*) AS total_trades,
            SUM(pnl) AS total_pl,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS winning_trades,
            SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) AS losing_trades,
            (SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS win_rate,
            CASE 
                WHEN SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
            END AS avg_win,
            CASE 
                WHEN SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN pnl <= 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END)
            END AS avg_loss,
            JSON_OBJECT(
                'symbol_name', symbol,
                'date_range', CONCAT(start_date, ' to ', end_date),
                'avg_price', (SELECT AVG(price) FROM orders WHERE symbol_id = symbol_pnl.symbol_id AND DATE(order_time) BETWEEN start_date AND end_date),
                'buy_count', SUM(CASE WHEN pnl > 0 AND o.side = 'B' THEN 1 ELSE 0 END),
                'sell_count', SUM(CASE WHEN pnl > 0 AND o.side = 'S' THEN 1 ELSE 0 END)
            ) AS analytics_data
        FROM 
            symbol_pnl
            JOIN orders o ON symbol_pnl.order_id = o.order_id
        GROUP BY 
            symbol_id, symbol
    )
    SELECT 
        sm.analytics_date,
        sm.analytics_type,
        sm.symbol_id,
        sm.total_trades,
        sm.total_pl,
        sm.winning_trades,
        sm.losing_trades,
        sm.win_rate,
        sm.avg_win,
        sm.avg_loss,
        sm.analytics_data
    FROM symbol_metrics sm
    ON DUPLICATE KEY UPDATE
        total_trades = VALUES(total_trades),
        total_pl = VALUES(total_pl),
        winning_trades = VALUES(winning_trades),
        losing_trades = VALUES(losing_trades),
        win_rate = VALUES(win_rate),
        avg_win = VALUES(avg_win),
        avg_loss = VALUES(avg_loss),
        analytics_data = VALUES(analytics_data),
        updated_at = CURRENT_TIMESTAMP;
        
    -- Devolver los registros actualizados
    SELECT 
        pa.analytics_date,
        s.symbol,
        pa.total_trades,
        pa.total_pl,
        pa.winning_trades,
        pa.losing_trades,
        pa.win_rate
    FROM processed_analytics pa
    JOIN symbols s ON pa.symbol_id = s.symbol_id
    WHERE pa.analytics_date = start_date
    AND pa.analytics_type = 'symbol'
    ORDER BY pa.total_pl DESC;
END //

-- Procedimiento para calcular análisis por hora para un rango de fechas
CREATE PROCEDURE calculate_hourly_metrics(IN start_date DATE, IN end_date DATE)
BEGIN
    -- Insertar o actualizar registros para análisis por hora
    INSERT INTO processed_analytics (
        analytics_date, 
        analytics_type, 
        total_trades, 
        total_pl, 
        winning_trades, 
        losing_trades, 
        win_rate, 
        avg_win, 
        avg_loss,
        analytics_data
    )
    WITH hourly_pnl AS (
        SELECT 
            DATE(o.order_time) AS trade_date,
            HOUR(o.order_time) AS trade_hour,
            o.order_id,
            CASE 
                WHEN o.side = 'B' THEN 
                    (o.price - COALESCE(
                        (SELECT SUM(tr.price * tr.quantity) / SUM(tr.quantity) 
                         FROM trades tr 
                         WHERE tr.order_id = o.order_id), 0)
                    ) * o.quantity
                ELSE 
                    (COALESCE(
                        (SELECT SUM(tr.price * tr.quantity) / SUM(tr.quantity) 
                         FROM trades tr 
                         WHERE tr.order_id = o.order_id), 0)
                    - o.price) * o.quantity
            END - COALESCE(
                (SELECT SUM(tk.commission + tk.route_fee) 
                 FROM trades tr 
                 JOIN tickets tk ON tr.trade_id = tk.trade_id 
                 WHERE tr.order_id = o.order_id), 0
            ) AS pnl
        FROM orders o
        WHERE DATE(o.order_time) BETWEEN start_date AND end_date
    ),
    hourly_metrics AS (
        SELECT 
            start_date AS analytics_date,
            'hourly' AS analytics_type,
            trade_hour,
            COUNT(*) AS total_trades,
            SUM(pnl) AS total_pl,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS winning_trades,
            SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) AS losing_trades,
            (SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS win_rate,
            CASE 
                WHEN SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
            END AS avg_win,
            CASE 
                WHEN SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) = 0 THEN 0
                ELSE SUM(CASE WHEN pnl <= 0 THEN pnl ELSE 0 END) / 
                     SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END)
            END AS avg_loss,
            JSON_OBJECT(
                'hour', trade_hour,
                'date_range', CONCAT(start_date, ' to ', end_date)
            ) AS analytics_data
        FROM hourly_pnl
        GROUP BY trade_hour
    )
    SELECT 
        hm.analytics_date,
        hm.analytics_type,
        NULL,
        hm.total_trades,
        hm.total_pl,
        hm.winning_trades,
        hm.losing_trades,
        hm.win_rate,
        hm.avg_win,
        hm.avg_loss,
        JSON_SET(
            hm.analytics_data,
            '$.hour', hm.trade_hour
        )
    FROM hourly_metrics hm
    ON DUPLICATE KEY UPDATE
        analytics_data = JSON_SET(
            VALUES(analytics_data),
            '$.hour', hm.trade_hour
        ),
        total_trades = VALUES(total_trades),
        total_pl = VALUES(total_pl),
        winning_trades = VALUES(winning_trades),
        losing_trades = VALUES(losing_trades),
        win_rate = VALUES(win_rate),
        avg_win = VALUES(avg_win),
        avg_loss = VALUES(avg_loss),
        updated_at = CURRENT_TIMESTAMP;
        
    -- Crear resumen consolidado por hora para todas las fechas en el rango
    INSERT INTO processed_analytics (
        analytics_date, 
        analytics_type, 
        total_trades, 
        total_pl, 
        winning_trades, 
        losing_trades, 
        win_rate, 
        avg_win, 
        avg_loss,
        analytics_data
    )
    SELECT 
        end_date,
        'hourly_summary',
        NULL,
        SUM(hm.total_trades),
        SUM(hm.total_pl),
        SUM(hm.winning_trades),
        SUM(hm.losing_trades),
        CASE 
            WHEN SUM(hm.total_trades) = 0 THEN 0 
            ELSE SUM(hm.winning_trades) / SUM(hm.total_trades) * 100 
        END,
        CASE 
            WHEN SUM(hm.winning_trades) = 0 THEN 0 
            ELSE SUM(hm.total_pl * (hm.winning_trades / hm.total_trades)) / SUM(hm.winning_trades) 
        END,
        CASE 
            WHEN SUM(hm.losing_trades) = 0 THEN 0 
            ELSE SUM(hm.total_pl * (hm.losing_trades / hm.total_trades)) / SUM(hm.losing_trades) 
        END,
        JSON_OBJECT(
            'hourly_data', JSON_ARRAYAGG(
                JSON_OBJECT(
                    'hour', JSON_EXTRACT(hm.analytics_data, '$.hour'),
                    'total_trades', hm.total_trades,
                    'total_pl', hm.total_pl,
                    'win_rate', hm.win_rate
                )
            ),
            'date_range', CONCAT(start_date, ' to ', end_date)
        )
    FROM (
        SELECT 
            analytics_data,
            total_trades,
            total_pl,
            winning_trades,
            losing_trades,
            win_rate
        FROM processed_analytics
        WHERE analytics_type = 'hourly'
        AND analytics_date = start_date
    ) hm
    ON DUPLICATE KEY UPDATE
        total_trades = VALUES(total_trades),
        total_pl = VALUES(total_pl),
        winning_trades = VALUES(winning_trades),
        losing_trades = VALUES(losing_trades),
        win_rate = VALUES(win_rate),
        avg_win = VALUES(avg_win),
        avg_loss = VALUES(avg_loss),
        analytics_data = VALUES(analytics_data);
END //

DELIMITER ;

-- Crear algunos índices adicionales para mejorar el rendimiento en consultas frecuentes
CREATE INDEX idx_analytics_date_type ON processed_analytics(analytics_date, analytics_type);
CREATE INDEX idx_tickets_trade ON tickets(trade_id);
CREATE INDEX idx_trade_order ON trades(order_id);
CREATE INDEX idx_alert_active ON trading_alerts(is_active);

-- Crear un usuario para la aplicación con permisos restringidos
CREATE USER IF NOT EXISTS 'das_app_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT SELECT, INSERT, UPDATE, DELETE ON das_trader_analyzer.* TO 'das_app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE das_trader_analyzer.import_orders_from_temp TO 'das_app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE das_trader_analyzer.import_trades_from_temp TO 'das_app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE das_trader_analyzer.import_tickets_from_temp TO 'das_app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE das_trader_analyzer.calculate_daily_metrics TO 'das_app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE das_trader_analyzer.calculate_symbol_metrics TO 'das_app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE das_trader_analyzer.calculate_hourly_metrics TO 'das_app_user'@'localhost';
FLUSH PRIVILEGES;