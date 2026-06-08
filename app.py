from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CONFIGURACIÓN PARA SUBIR ARCHIVOS LOCALES
CARPETA_SUBIDAS = os.path.join('static', 'uploads')
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

def conectar_bd():
    conexion = sqlite3.connect('database.db')
    conexion.row_factory = sqlite3.Row
    return conexion

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            costo_compra REAL NOT NULL,
            precio_venta REAL NOT NULL,
            imagen_url TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            costo_compra REAL NOT NULL,
            precio_venta REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            ganancia_neta REAL NOT NULL,
            tipo TEXT NOT NULL,
            detalles TEXT
        )
    ''')
    
    try:
        cursor.execute('ALTER TABLE productos ADD COLUMN imagen_url TEXT')
    except sqlite3.OperationalError:
        pass
        
    conexion.commit()
    conexion.close()

iniciar_base_datos()

# --- PÁGINAS Y VISTAS ---

@app.route('/')
def inicio():
    conexion = conectar_bd()
    productos = conexion.execute('SELECT * FROM productos').fetchall()
    extras = conexion.execute('SELECT * FROM extras').fetchall()
    conexion.close()
    return render_template('pos.html', productos=productos, extras=extras)

@app.route('/inventario')
def inventario():
    conexion = conectar_bd()
    productos = conexion.execute('SELECT * FROM productos').fetchall()
    extras = conexion.execute('SELECT * FROM extras').fetchall()
    conexion.close()
    return render_template('productos.html', productos=productos, extras=extras)

@app.route('/tickets')
def ver_tickets():
    conexion = conectar_bd()
    todos_los_tickets = conexion.execute('SELECT * FROM tickets ORDER BY id DESC').fetchall()
    conexion.close()
    return render_template('tickets.html', tickets=todos_los_tickets)

@app.route('/imprimir/<int:ticket_id>')
def imprimir_ticket(ticket_id):
    conexion = conectar_bd()
    ticket = conexion.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conexion.close()
    
    if ticket:
        lista_productos = []
        if ticket['detalles']:
            try:
                lista_productos = json.loads(ticket['detalles'])
            except:
                lista_productos = []
        return render_template('imprimir.html', ticket=ticket, lista_productos=lista_productos)
    return "Ticket no encontrado", 404


# --- PROCESAMIENTO DE INVENTARIO (CON SUBIDA DE GALERÍA) ---

@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    nombre = request.form.get('nombre', 'Producto Sin Nombre')
    costo_compra = float(request.form.get('costo_compra', 0.0))
    precio_venta = float(request.form.get('precio_venta', 0.0))
    
    ruta_imagen = ""
    # Verificar si el usuario subió un archivo desde su galería
    if 'foto_galeria' in request.files:
        archivo = request.files['foto_galeria']
        if archivo and archivo.filename != '' and archivo_permitido(archivo.filename):
            nombre_limpio = secure_filename(archivo.filename)
            # Guardamos el archivo físicamente en static/uploads/
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_limpio))
            # Guardamos la ruta web relativa en la base de datos
            ruta_imagen = f"/static/uploads/{nombre_limpio}"
            
    conexion = conectar_bd()
    conexion.execute('INSERT INTO productos (nombre, costo_compra, precio_venta, imagen_url) VALUES (?, ?, ?, ?)', 
                     (nombre, costo_compra, precio_venta, ruta_imagen))
    conexion.commit()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/guardar_extra', methods=['POST'])
def guardar_extra():
    nombre = request.form.get('nombre', 'Extra Sin Nombre')
    costo_compra = float(request.form.get('costo_compra', 0.0))
    precio_venta = float(request.form.get('precio_venta', 0.0))
    conexion = conectar_bd()
    conexion.execute('INSERT INTO extras (nombre, costo_compra, precio_venta) VALUES (?, ?, ?)', (nombre, costo_compra, precio_venta))
    conexion.commit()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    # Nota: Mantenemos la edición rápida vía JSON para precios. 
    # Para cambiar de foto, es más limpio borrar el producto y volverlo a registrar con la nueva foto de la galería.
    datos = request.get_json()
    costo = float(datos.get('costo_compra', 0.0))
    precio = float(datos.get('precio_venta', 0.0))
    
    conexion = conectar_bd()
    conexion.execute('UPDATE productos SET costo_compra = ?, precio_venta = ? WHERE id = ?', 
                     (costo, precio, id))
    conexion.commit()
    conexion.close()
    return jsonify({"success": True})

@app.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    conexion = conectar_bd()
    conexion.execute('DELETE FROM productos WHERE id = ?', (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for('inventario'))

@app.route('/editar_extra/<int:id>', methods=['POST'])
def editar_extra(id):
    datos = request.get_json()
    conexion = conectar_bd()
    conexion.execute('UPDATE extras SET costo_compra = ?, precio_venta = ? WHERE id = ?', (float(datos['costo_compra']), float(datos['precio_venta']), id))
    conexion.commit()
    conexion.close()
    return jsonify({"success": True})

@app.route('/eliminar_extra/<int:id>', methods=['POST'])
def eliminar_extra(id):
    conexion = conectar_bd()
    conexion.execute('DELETE FROM extras WHERE id = ?', (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for('inventario'))


# --- GUARDAR TICKET ---

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
        cursor.execute('INSERT INTO tickets (total, ganancia_neta, tipo, detalles) VALUES (?, ?, ?, ?)', 
                       (total, ganancia, tipo, detalles_texto))
        conexion.commit()
        conexion.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error al guardar ticket: {e}")
        return jsonify({"success": False})

if __name__ == '__main__':
    app.run(debug=True)