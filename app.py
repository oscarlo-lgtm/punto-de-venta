from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CADENA DE CONEXIÓN A TU BASE DE DATOS ETERNA EN LA NUBE (Oregón - IPv4 Compatible)
URL_BASE_DATOS = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

# CONFIGURACIÓN PARA SUBIR ARCHIVOS LOCALES
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
    
    # Tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            costo_compra REAL NOT NULL,
            precio_venta REAL NOT NULL,
            imagen_url TEXT
        )
    ''')
    
    # Tabla de extras (¡Actualizada con columna de imagen!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extras (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            costo_compra REAL NOT NULL,
            precio_venta REAL NOT NULL,
            imagen_url TEXT
        )
    ''')
    
    # Si la tabla extras ya existía de antes, le agregamos la columna imagen_url si no la tiene
    try:
        cursor.execute("ALTER TABLE extras ADD COLUMN IF NOT EXISTS imagen_url TEXT;")
    except Exception as e:
        print("La columna imagen_url ya existía o se gestionó correctamente.")
    
    # Tabla de tickets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            ganancia_neta REAL NOT NULL,
            tipo TEXT NOT NULL,
            detalles TEXT
        )
    ''')
    
    conexion.commit()
    cursor.close()
    conexion.close()

iniciar_base_datos()

# --- PÁGINAS Y VISTAS ---

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

# Hoja exclusiva para ver las ganancias netas con diseño privado
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
        lista_productos = []
        if ticket['detalles']:
            try:
                lista_productos = json.loads(ticket['detalles'])
            except:
                lista_productos = []
        # Pasamos el nombre correcto de la marca directo al render
        return render_template('imprimir.html', ticket=ticket, lista_productos=lista_productos, nombre_pos="PUNTO DE VENTA JEJA", lema="(Juntos Empezamos Juntos Avanzamos)")
    return "Ticket no encontrado", 404


# --- PROCESAMIENTO DE INFORMACIÓN (Altas, Bajas, Cambios) ---

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
    cursor.execute('INSERT INTO productos (nombre, costo_compra, precio_venta, imagen_url) VALUES (%s, %s, %s, %s)', 
                   (nombre, costo_compra, precio_venta, ruta_imagen))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/guardar_extra', methods=['POST'])
def guardar_extra():
    nombre = request.form.get('nombre', 'Extra Sin Nombre')
    costo_compra = float(request.form.get('costo_compra', 0.0))
    precio_venta = float(request.form.get('precio_venta', 0.0))
    
    # ¡NUEVO!: Procesar el botón para agregar fotos también en los Extras
    ruta_imagen = ""
    if 'foto_extra' in request.files:
        archivo = request.files['foto_extra']
        if archivo and archivo.filename != '' and archivo_permitido(archivo.filename):
            nombre_limpio = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_limpio))
            ruta_imagen = f"/static/uploads/{nombre_limpio}"
            
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO extras (nombre, costo_compra, precio_venta, imagen_url) VALUES (%s, %s, %s, %s)', 
                   (nombre, costo_compra, precio_venta, ruta_imagen))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    datos = request.get_json()
    costo = float(datos.get('costo_compra', 0.0))
    precio = float(datos.get('precio_venta', 0.0))
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('UPDATE productos SET costo_compra = %s, precio_venta = %s WHERE id = %s', 
                   (costo, precio, id))
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({"success": True})

@app.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM productos WHERE id = %s', (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/editar_extra/<int:id>', methods=['POST'])
def editar_extra(id):
    datos = request.get_json()
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('UPDATE extras SET costo_compra = %s, precio_venta = %s WHERE id = %s', 
                   (float(datos['costo_compra']), float(datos['precio_venta']), id))
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({"success": True})

@app.route('/eliminar_extra/<int:id>', methods=['POST'])
def eliminar_extra(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM extras WHERE id = %s', (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/guardar_ticket', methods=['POST'])
def guardar_ticket():
    datos = request.get_json()
    tipo = datos['tipo']
    total = datos['total']
    ganancia = datos['ganancia']
    
    desglose = []
    for item in datos['productos']:
        texto_extras = ", ".join([e['nombre'] for e in item['extras']])
        desglose.append({
            "nombre": item['nombre'],
            "extras": texto_extras,
            "total_renglon": item['precio_total_renglon']
        })
    
    detalles_texto = json.dumps(desglose)
    
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute('INSERT INTO tickets (total, ganancia_neta, tipo, detalles) VALUES (%s, %s, %s, %s)', 
                       (total, ganancia, tipo, detalles_texto))
        conexion.commit()
        cursor.close()
        conexion.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error al guardar ticket: {e}")
        return jsonify({"success": False})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
