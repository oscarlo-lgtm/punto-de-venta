from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CADENA DE CONEXIÓN A TU BASE DE DATOS
URL_BASE_DATOS = "postgresql://postgres:B0mb0nsit03@db.zivpdzxvukcovqjekxpz.supabase.co:5432/postgres"

# CONFIGURACIÓN PARA SUBIR ARCHIVOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_SUBIDAS = os.path.join(BASE_DIR, 'static', 'uploads')
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS

# MODIFICACIÓN DE SEGURIDAD PARA RENDER
if not os.path.exists(CARPETA_SUBIDAS):
    try:
        os.makedirs(CARPETA_SUBIDAS, exist_ok=True)
    except OSError:
        pass 

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

def conectar_bd():
    return psycopg2.connect(URL_BASE_DATOS)

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL, imagen_url TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS extras (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total REAL NOT NULL, ganancia_neta REAL NOT NULL, tipo TEXT NOT NULL, detalles TEXT)''')
    conexion.commit()
    cursor.close()
    conexion.close()

# Inicializamos tablas al arrancar
iniciar_base_datos()

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

@app.route('/tickets')
def ver_tickets():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM tickets ORDER BY id DESC')
    todos_los_tickets = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('tickets.html', tickets=todos_los_tickets)

@app.route('/ganancias')
def ver_ganancias():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM tickets ORDER BY id DESC')
    todos_los_tickets = cursor.fetchall()
    total_ventas = sum(t['total'] for t in todos_los_tickets)
    total_ganancias = sum(t['ganancia_neta'] for t in todos_los_tickets)
    cursor.close()
    conexion.close()
    return render_template('ganancias.html', tickets=todos_los_tickets, total_ventas=total_ventas, total_ganancias=total_ganancias)

@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    nombre = request.form.get('nombre', 'Producto Sin Nombre')
    costo_compra = float(request.form.get('costo_compra', 0.0))
    precio_venta = float(request.form.get('precio_venta', 0.0))
    ruta_imagen = ""
    if 'foto_galeria' in request.files:
        archivo = request.files['foto_galeria']
        if archivo and archivo.filename != '' and archivo_permitido(archivo.filename):
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

# (Las rutas restantes: guardar_extra, editar_producto, eliminar_producto, etc. van aquí igual que antes)

if __name__ == '__main__':
    app.run()
