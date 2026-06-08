from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import os
import psycopg2
import uuid
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'JEJA_SECRETO_2026'

URL_BASE_DATOS = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

def conectar_bd():
    return psycopg2.connect(URL_BASE_DATOS)

def iniciar_base_datos():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY, 
        nombre TEXT, ap_paterno TEXT, ap_materno TEXT, 
        fecha_nac TEXT, celular TEXT, password TEXT, 
        token TEXT UNIQUE
    )''')
    cursor.execute('CREATE TABLE IF NOT EXISTS invitaciones (id SERIAL PRIMARY KEY, token TEXT UNIQUE, usado BOOLEAN DEFAULT FALSE)')
    # Aseguramos que la tabla tickets tenga la estructura correcta
    cursor.execute('CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, total REAL, ganancia_neta REAL, tipo TEXT, detalles TEXT, vendedor TEXT)')
    conexion.commit()
    cursor.close()
    conexion.close()

iniciar_base_datos()

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
    cursor = conexion.cursor()
    cursor.execute('SELECT usado FROM invitaciones WHERE token = %s AND usado = FALSE', (token,))
    if not cursor.fetchone():
        return "Enlace inválido o ya utilizado.", 403
    
    if request.method == 'POST':
        datos = request.form
        fecha = f"{datos['dia']}/{datos['mes']}/{datos['anio']}"
        cursor.execute('''INSERT INTO usuarios (nombre, ap_paterno, ap_materno, fecha_nac, celular, password, token) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                       (datos['nombre'], datos['ap_paterno'], datos['ap_materno'], fecha, datos['celular'], datos['password'], token))
        cursor.execute('UPDATE invitaciones SET usado = TRUE WHERE token = %s', (token,))
        conexion.commit()
        session['vendedor'] = f"{datos['nombre']} {datos['ap_materno']}"
        return redirect(url_for('inicio'))
    
    cursor.close()
    conexion.close()
    return render_template('registro.html')

@app.route('/')
def inicio():
    if 'vendedor' not in session: return "Acceso denegado", 403
    return render_template('pos.html')

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
