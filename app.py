import os
import json
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, jsonify
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CONFIGURACIÓN DE BASE DE DATOS
# Render leerá la variable DATABASE_URL que configuraste en el panel
URL_BASE_DATOS = os.environ.get('DATABASE_URL')

# CONFIGURACIÓN PARA SUBIR ARCHIVOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_SUBIDAS = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Crear carpeta de subidas de forma segura
if not os.path.exists(CARPETA_SUBIDAS):
    try:
        os.makedirs(CARPETA_SUBIDAS, exist_ok=True)
    except OSError:
        pass

def conectar_bd():
    if not URL_BASE_DATOS:
        raise ValueError("La variable DATABASE_URL no está configurada en el entorno")
    return psycopg2.connect(URL_BASE_DATOS)

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL, imagen_url TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS extras (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total REAL NOT NULL, ganancia_neta REAL NOT NULL, tipo TEXT NOT NULL, detalles TEXT)')
    conexion.commit()
    cursor.close()
    conexion.close()

# Inicializar tablas al arrancar
try:
    iniciar_base_datos()
except Exception as e:
    print(f"Error al conectar a la BD: {e}")

# --- RUTAS ---

@app.route('/')
def inicio():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM productos ORDER BY id DESC')
    productos = cursor.fetchall()
    cursor.execute('SELECT * FROM extras ORDER BY id DESC')
    extras = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('pos.html', productos=productos, extras=extras)

@app.route('/inventario')
def inventario():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM productos ORDER BY id DESC')
    productos = cursor.fetchall()
    cursor.execute('SELECT * FROM extras ORDER BY id DESC')
    extras = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('productos.html', productos=productos, extras=extras)

@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    nombre = request.form.get('nombre', 'Producto')
    costo_compra = float(request.form.get('costo_compra', 0))
    precio_venta = float(request.form.get('precio_venta', 0))
    ruta_imagen = ""
    if 'foto_galeria' in request.files:
        archivo = request.files['foto_galeria']
        if archivo and archivo.filename != '':
            nombre_limpio = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_limpio))
            ruta_imagen = f"/static/uploads/{nombre_limpio}"
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO productos (nombre, costo_compra, precio_venta, imagen_url) VALUES (%s, %s, %s, %s)', (nombre, costo_compra, precio_venta, ruta_imagen))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

if __name__ == '__main__':
    app.run()
