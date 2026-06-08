from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import os
import psycopg2
import uuid
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'JEJA_SECRETO_2026'

URL_BASE_DATOS = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_SUBIDAS = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

def conectar_bd():
    return psycopg2.connect(URL_BASE_DATOS)

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, nombre TEXT, costo_compra REAL, precio_venta REAL, imagen_url TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS extras (id SERIAL PRIMARY KEY, nombre TEXT, costo_compra REAL, precio_venta REAL, imagen_url TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total REAL, ganancia_neta REAL, tipo TEXT, detalles TEXT, vendedor TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, nombre TEXT, token TEXT UNIQUE, es_admin BOOLEAN DEFAULT FALSE)')
    cursor.execute('CREATE TABLE IF NOT EXISTS invitaciones (id SERIAL PRIMARY KEY, token TEXT UNIQUE, usado BOOLEAN DEFAULT FALSE)')
    conexion.commit()
    cursor.close()
    conexion.close()

iniciar_base_datos()

# --- RUTAS DE ADMINISTRACIÓN Y GENERACIÓN ---

@app.route('/generar_link', methods=['POST'])
def generar_link():
    token = str(uuid.uuid4())
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO invitaciones (token, usado) VALUES (%s, %s)', (token, False))
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({"link": f"https://puntodeventa-bdc9.onrender.com/registrar/{token}"})

@app.route('/registrar/<token>', methods=['GET', 'POST'])
def registrar_usuario(token):
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM invitaciones WHERE token = %s AND usado = FALSE', (token,))
    invitacion = cursor.fetchone()
    
    if not invitacion:
        return "Este enlace ya fue utilizado o no es válido.", 403
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cursor.execute('INSERT INTO usuarios (nombre, token, es_admin) VALUES (%s, %s, %s)', (nombre, token, False))
        cursor.execute('UPDATE invitaciones SET usado = TRUE WHERE token = %s', (token,))
        conexion.commit()
        session['vendedor'] = nombre
        cursor.close()
        conexion.close()
        return redirect(url_for('inicio'))
    
    return render_template('registro.html', token=token)

# --- PÁGINAS PRINCIPALES ---

@app.route('/')
def inicio():
    if 'vendedor' not in session: return "Acceso denegado. Registrate primero.", 403
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

@app.route('/ganancias')
def ver_ganancias():
    # Protegido por session['admin']
    if not session.get('admin'): 
        clave = request.args.get('clave')
        if clave == 'JEJA2026': # Clave de acceso
            session['admin'] = True
        else:
            return "Acceso restringido a administradores.", 403
            
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM tickets ORDER BY id DESC')
    tickets = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('ganancias.html', tickets=tickets)

@app.route('/guardar_ticket', methods=['POST'])
def guardar_ticket():
    datos = request.get_json()
    vendedor = session.get('vendedor', 'Invitado')
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO tickets (total, ganancia_neta, tipo, detalles, vendedor) VALUES (%s, %s, %s, %s, %s)', 
                   (datos['total'], datos['ganancia'], datos['tipo'], json.dumps(datos['productos']), vendedor))
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
