from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
import random
from datetime import datetime

app = Flask(__name__)

# CADENA DE CONEXIÓN
URL_BASE_DATOS = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

# CONFIGURACIÓN PARA SUBIR ARCHIVOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_SUBIDAS = os.path.join(BASE_DIR, 'static', 'uploads')
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS

os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

def conectar_bd():
    return psycopg2.connect(URL_BASE_DATOS)

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL, imagen_url TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS extras (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL, imagen_url TEXT)')
    try:
        cursor.execute("ALTER TABLE extras ADD COLUMN IF NOT EXISTS imagen_url TEXT;")
    except:
        pass
    cursor.execute('CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total REAL NOT NULL, ganancia_neta REAL NOT NULL, tipo TEXT NOT NULL, detalles TEXT)')
    conexion.commit()
    cursor.close()
    conexion.close()

iniciar_base_datos()

# --- PÁGINAS ---
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

@app.route('/imprimir/<int:ticket_id>')
def imprimir_ticket(ticket_id):
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM tickets WHERE id = %s', (ticket_id,))
    ticket = cursor.fetchone()
    cursor.close()
    conexion.close()
    if ticket:
        lista_productos = json.loads(ticket['detalles']) if ticket['detalles'] else []
        return render_template('imprimir.html', ticket=ticket, lista_productos=lista_productos, nombre_pos="PUNTO DE VENTA JEJA", lema="(Juntos Empezamos Juntos Avanzamos)")
    return "Ticket no encontrado", 404

# --- NUEVAS RUTAS DE PRESUPUESTO ---
@app.route('/guardar_presupuesto', methods=['POST'])
def guardar_presupuesto():
    # Esta ruta solo avisa al sistema que todo está bien para imprimir
    presupuesto_id = random.randint(1000, 9999)
    return jsonify({"success": True, "presupuesto_id": presupuesto_id})

@app.route('/imprimir_presupuesto/<int:id>')
def imprimir_presupuesto(id):
    ticket_datos = {"id": id, "fecha": datetime.now().strftime('%d/%m/%Y %H:%M')}
    return render_template('imprimir_presupuesto.html', ticket=ticket_datos)

# --- PROCESAMIENTO ---
@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    nombre = request.form.get('nombre', 'Producto Sin Nombre')
    costo = float(request.form.get('costo_compra', 0.0))
    precio = float(request.form.get('precio_venta', 0.0))
    ruta_imagen = ""
    if 'foto_galeria' in request.files:
        archivo = request.files['foto_galeria']
        if archivo and archivo.filename != '' and archivo_permitido(archivo.filename):
            nombre_limpio = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_limpio))
            ruta_imagen = f"/static/uploads/{nombre_limpio}"
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO productos (nombre, costo_compra, precio_venta, imagen_url) VALUES (%s, %s, %s, %s)', (nombre, costo, precio, ruta_imagen))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/guardar_extra', methods=['POST'])
def guardar_extra():
    nombre = request.form.get('nombre', 'Extra Sin Nombre')
    costo = float(request.form.get('costo_compra', 0.0))
    precio = float(request.form.get('precio_venta', 0.0))
    ruta_imagen = ""
    if 'foto_extra' in request.files:
        archivo = request.files['foto_extra']
        if archivo and archivo.filename != '' and archivo_permitido(archivo.filename):
            nombre_limpio = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_limpio))
            ruta_imagen = f"/static/uploads/{nombre_limpio}"
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO extras (nombre, costo_compra, precio_venta, imagen_url) VALUES (%s, %s, %s, %s)', (nombre, costo, precio, ruta_imagen))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/guardar_ticket', methods=['POST'])
def guardar_ticket():
    datos = request.get_json()
    tipo = datos.get('tipo', 'Venta')
    total = datos.get('total', 0)
    ganancia = datos.get('ganancia', 0)
    desglose = []
    for item in datos.get('productos', []):
        texto_extras = ", ".join([e['nombre'] for e in item['extras']])
        desglose.append({"nombre": item['nombre'], "extras": texto_extras, "total_renglon": item['precio_total_renglon']})
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO tickets (total, ganancia_neta, tipo, detalles) VALUES (%s, %s, %s, %s) RETURNING id', (total, ganancia, tipo, json.dumps(desglose)))
    ticket_id = cursor.fetchone()[0]
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({"success": True, "ticket_id": ticket_id})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
