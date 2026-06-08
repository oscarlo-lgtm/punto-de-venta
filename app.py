from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'JEJA_ADMIN_SECRET_2026' # Cambia esto por una clave muy secreta

# CADENA DE CONEXIÓN
URL_BASE_DATOS = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

# CONFIGURACIÓN
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_SUBIDAS = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

def conectar_bd():
    return psycopg2.connect(URL_BASE_DATOS)

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    # Tablas existentes
    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL, imagen_url TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS extras (id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, costo_compra REAL NOT NULL, precio_venta REAL NOT NULL, imagen_url TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total REAL NOT NULL, ganancia_neta REAL NOT NULL, tipo TEXT NOT NULL, detalles TEXT, vendedor TEXT)')
    # Nueva tabla de usuarios para control
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY, 
                        nombre TEXT NOT NULL, 
                        token TEXT UNIQUE NOT NULL, 
                        es_admin BOOLEAN DEFAULT FALSE)''')
    conexion.commit()
    cursor.close()
    conexion.close()

iniciar_base_datos()

# --- ACCESO Y SEGURIDAD ---

@app.route('/vendedor/<token>')
def acceso_vendedor(token):
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM usuarios WHERE token = %s', (token,))
    user = cursor.fetchone()
    cursor.close()
    conexion.close()
    if user:
        session['vendedor'] = user['nombre']
        return redirect(url_for('inicio'))
    return "Token inválido", 403

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        clave = request.form.get('clave')
        # Aquí defines tus 3 claves maestras (cámbialas por seguridad)
        if clave in ['admin123', 'seguridad456', 'clave789']:
            session['admin_autenticado'] = True
            return redirect(url_for('ver_ganancias'))
        flash('Clave incorrecta')
    return render_template('login_admin.html')

# --- PÁGINAS ---

@app.route('/')
def inicio():
    if 'vendedor' not in session: return "Acceso no autorizado", 403
    # ... (aquí iría tu lógica de carga de productos igual que antes)
    return render_template('pos.html')

@app.route('/ganancias')
def ver_ganancias():
    if not session.get('admin_autenticado'):
        return redirect(url_for('login_admin'))
    # ... (tu lógica de ganancias aquí)
    return "Panel de Ganancias Privado"

@app.route('/guardar_ticket', methods=['POST'])
def guardar_ticket():
    datos = request.get_json()
    vendedor = session.get('vendedor', 'Desconocido')
    # Guardar en BD incluyendo el campo 'vendedor'
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
