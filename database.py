import sqlite3

def crear_base_de_datos():
    # Esto crea el archivo de la base de datos si no existe
    conexion = sqlite3.connect('punto_venta.db')
    cursor = conexion.cursor()

    # 1. Creamos la tabla de Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio_compra REAL NOT NULL,
            precio_venta REAL NOT NULL,
            existencias INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # 2. Creamos la tabla de Ventas (Maestro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL
        )
    ''')

    # 3. Creamos la tabla de Detalle de Ventas (Para saber qué productos se llevaron en cada venta)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER,
            id_producto INTEGER,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (id_venta) REFERENCES ventas(id),
            FOREIGN KEY (id_producto) REFERENCES productos(id)
        )
    ''')

    # Guardamos los cambios y cerramos
    conexion.commit()
    conexion.close()
    print("¡Base de datos y tablas creadas con éxito!")

if __name__ == "__main__":
    crear_base_de_datos()