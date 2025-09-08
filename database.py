import sqlite3
from sqlite3 import Error
from config.currency_config import currency_config

# Variable global para la conexión (patron singleton)
_connection = None

def get_connection():
    """Obtiene la conexiòn única a la base de datos"""
    global _connection
    if _connection is None:
        try:
            _connection = sqlite3.connect(
                'base_datos_trader_LJ.db',
                check_same_thread=False,
                timeout=30
            )
            _connection.execute("PRAGMA journal_mode=WAL")
            print("Conexión a SQLite establecida")
        except Error as e:
            print(f"Error al conectar a SQLite: {e}")
            return None
    return _connection

def close_connection():
    """Cierra la conexión a la base de datos"""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        print("Conexiòn a SQLite cerrada")

def create_tables():
    """Crea las tablas necesarias para el portafolio"""
    conn = get_connection()
    if conn:
        sql_create_activos = """
        CREATE TABLE IF NOT EXISTS activos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simbolo TEXT UNIQUE NOT NULL,
            nombre TEXT,
            tipo TEXT CHECK(tipo IN('accion','cripto','etf','cetes','otro_varaible','otro_fija'))
        );"""

        sql_create_transacciones = """
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            simbolo TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad REAL NOT NULL,
            comisiones REAL DEFAULT 0,
            FOREIGN KEY (simbolo) REFERENCES activos (simbolo)
        )"""

        sql_create_alertas = """
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            simbolo TEXT NOT NULL,
            tipo_alerta TEXT NOT NULL,
            precio_actual REAL NOT NULL,
            precio_referencia REAL NOT NULL,
            desviacion REAL NOT NULL,
            mensaje TEXT NOT NULL,
            leida BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (simbolo) REFERENCES activos (simbolo)
        );
        """

        try:
            cursor = conn.cursor()
            cursor.execute(sql_create_activos)
            cursor.execute(sql_create_transacciones)
            cursor.execute(sql_create_alertas)
            conn.commit()
            print("Tablas creadas exitosamente")
        except Error as e:
            print(f"Error al crear tablas: {e}")

def get_activos():
    """Obotiene todos los activos de la base de datos"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activos")
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener activos: {e}")
            return[]

# Funciòn para insertar un activo
def insert_activo(simbolo,nombre,tipo):
    conn = get_connection()
    if conn:
        try:
            sql = """ INSERT INTO activos(simbolo,nombre,tipo) VALUES(?,?,?)"""
            cursor = conn.cursor()
            cursor.execute(sql,(simbolo,nombre,tipo))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al insertar activo: {e}")
        return None

# Función para insertar una transaccion
def insert_transaccion(fecha,simbolo,precio,cantidad,comisiones=0):
    conn = get_connection()
    if conn:
        try:
            sql = """INSERT INTO transacciones(fecha,simbolo,precio,cantidad,comisiones) VALUES(?,?,?,?,?)"""
            cursor = conn.cursor()
            cursor.execute(sql,(fecha,simbolo,precio,cantidad,comisiones))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al insertar transaccion: {e}")
            return None

# Funciòn para consultar transacciones
def get_transacciones(simbolo=None):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if simbolo:
                cursor.execute("SELECT * FROM transacciones WHERE simbolo = ?", (simbolo,))
            else:
                cursor.execute("SELECt * FROM transacciones")
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener transacciones: {e}")
            return []
        
def get_portfolio_data():
    """Obtiene datos agrupados para el portafolio"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    t.simbolo,
                    a.nombre,
                    SUM(t.cantidad) as cantidad_total,
                    SUM(t.precio * t.cantidad) / SUM(t.cantidad) as precio_promedio,
                    SUM(t.precio * t.cantidad) as inversion_total
                FROM transacciones t
                JOIN activos a ON t.simbolo = a.simbolo
                GROUP BY t.simbolo
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener datos del portafolio: {e}")
            return []
        
def get_all_symbols():
    """Obtiene todos los sìmbolos ùnicos de la base de datos"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT simbolo FROM transacciones")
            symbols = [row[0] for row in cursor.fetchall()]
            return symbols
        except Error as e:
            print(f"Error al obtener símbolos: {e}")
            return[]
        
def get_portfolio_with_current_prices():
    """Obtener el portafolio con precios actualizados en la moneda configurada"""
    from api.yahoo_finance import yahoo_api
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    t.simbolo,
                    COALESCE(a.nombre, t.simbolo) as nombre,
                    SUM(t.cantidad) as cantidad_total,
                    CASE 
                        WHEN SUM(t.cantidad) > 0 THEN SUM(t.precio * t.cantidad) / SUM(t.cantidad)
                        ELSE 0 
                    END as precio_promedio,
                    SUM(t.precio * t.cantidad) as inversion_total
                FROM transacciones t
                LEFT JOIN activos a ON t.simbolo = a.simbolo
                GROUP BY t.simbolo
                HAVING SUM(t.cantidad) > 0
            """)
            
            portfolio = cursor.fetchall()
            symbols = [asset[0] for asset in portfolio if asset[0]]
            
            # Obtener precios actuales en la moneda configurada
            current_prices = {}
            if symbols:
                current_prices = yahoo_api.get_multiple_prices(symbols, currency_config.get_currency())
            
            # Obtener tipo de cambio actual para conversiones
            exchange_rate = yahoo_api.get_usd_mxn_rate()
            
            portfolio_with_prices = []
            for asset in portfolio:
                symbol, name, quantity, avg_price, total_invested = asset
                
                current_price = current_prices.get(symbol, avg_price)
                current_value = quantity * current_price
                
                # Convertir precios promedio si es necesario
                if currency_config.get_currency() == "MXN":
                    # Asumimos que los precios en DB están en USD
                    avg_price_mxn = avg_price * exchange_rate
                    total_invested_mxn = total_invested * exchange_rate
                else:
                    avg_price_mxn = avg_price
                    total_invested_mxn = total_invested
                
                portfolio_with_prices.append({
                    'symbol': symbol,
                    'name': name,
                    'quantity': quantity,
                    'avg_price': avg_price_mxn,
                    'total_invested': total_invested_mxn,
                    'current_price': current_price,
                    'current_value': current_value,
                    'currency': currency_config.get_currency()
                })
            
            return portfolio_with_prices
            
        except Error as e:
            print(f"Error al obtener portafolio con precios: {e}")
            return []

def debug_portfolio_data():
    """Función para debuggear los datos del portafolio"""
    conn = get_connection()
    if conn:
        try:
            print("=== DEBUG: DATOS EN TABLAS ===")
            
            # Ver transacciones
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transacciones")
            transactions = cursor.fetchall()
            print(f"Transacciones: {len(transactions)} registros")
            for trans in transactions:
                print(f"  {trans}")
            
            # Ver activos
            cursor.execute("SELECT * FROM activos")
            assets = cursor.fetchall()
            print(f"Activos: {len(assets)} registros")
            for asset in assets:
                print(f"  {asset}")
            
            # Ver símbolos únicos
            cursor.execute("SELECT DISTINCT simbolo FROM transacciones")
            symbols = cursor.fetchall()
            print(f"Símbolos únicos: {[s[0] for s in symbols]}")
            
            return True
            
        except Error as e:
            print(f"Error en debug: {e}")
            return False
        
def insert_alerta(simbolo, tipo_alerta, precio_actual, precio_referencia, desviacion, mensaje):
    """Insertar una nueva alerta en la base de datos"""
    conn = get_connection()
    if conn:
        try:
            sql = """INSERT INTO alertas (simbolo, tipo_alerta, precio_actual, precio_referencia, desviacion, mensaje)
                     VALUES(?,?,?,?,?,?)"""
            cursor = conn.cursor()
            cursor.execute(sql, (simbolo, tipo_alerta, precio_actual, precio_referencia, desviacion, mensaje))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al insertar alerta: {e}")
            return None

def get_alertas(simbolo=None, no_leidas=False):
    """Obtener alertas de la base de datos"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            if simbolo:
                if no_leidas:
                    cursor.execute("SELECT * FROM alertas WHERE simbolo=? AND leida=FALSE ORDER BY fecha DESC", (simbolo,))
                else:
                    cursor.execute("SELECT * FROM alertas WHERE simbolo=? ORDER BY fecha DESC", (simbolo,))
            elif no_leidas:
                cursor.execute("SELECT * FROM alertas WHERE leida=FALSE ORDER BY fecha DESC")
            else:
                cursor.execute("SELECT * FROM alertas ORDER BY fecha DESC")
                
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener alertas: {e}")
            return []

def marcar_alerta_leida(alerta_id):
    """Marcar una alerta como leída"""
    conn = get_connection()
    if conn:
        try:
            sql = "UPDATE alertas SET leida=TRUE WHERE id=?"
            cursor = conn.cursor()
            cursor.execute(sql, (alerta_id,))
            conn.commit()
            return True
        except Error as e:
            print(f"Error al marcar alerta como leída: {e}")
            return False

def get_estadisticas_alertas():
    """Obtener estadísticas de alertas"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Total de alertas
            cursor.execute("SELECT COUNT(*) FROM alertas")
            total = cursor.fetchone()[0]
            
            # Alertas no leídas
            cursor.execute("SELECT COUNT(*) FROM alertas WHERE leida=FALSE")
            no_leidas = cursor.fetchone()[0]
            
            # Última alerta
            cursor.execute("SELECT MAX(fecha) FROM alertas")
            ultima_alerta = cursor.fetchone()[0]
            
            return {
                'total': total,
                'no_leidas': no_leidas,
                'ultima_alerta': ultima_alerta
            }
        except Error as e:
            print(f"Error al obtener estadísticas de alertas: {e}")
            return {'total': 0, 'no_leidas': 0, 'ultima_alerta': None}

if __name__ == "__main__":
    create_tables()
else:
    create_tables()