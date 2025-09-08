from database import create_connection, insert_activo, insert_transaccion, get_transacciones

conn = create_connection()

# Insertar datos de ejemplo
if conn:
    insert_activo(conn,"AAPL","Apple Inc","accion")
    insert_transaccion(conn,"2023-10-01","AAPL",170.5,10,5.0)

    print("Transacciones:", get_transacciones(conn))

    conn.close()

