from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import psycopg2
import uuid
import json
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'JEJA_SECRETO_2026'
URL_DB = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

def get_db():
    return psycopg2.connect(URL_DB)

@app.route('/')
def index():
    if 'vendedor' not in session: return "Acceso denegado", 403
    return render_template('pos.html')

@app.route('/inventario')
def inventario():
    return render_template('productos.html')

@app.route('/generar_link', methods=['POST'])
def generar_link():
    token = str(uuid.uuid4())
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO invitaciones (token, usado) VALUES (%s, %s)', (token, False))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"link": f"https://puntodeventa-bdc9.onrender.com/registrar/{token}"})

@app.route('/registrar/<token>', methods=['GET', 'POST'])
def registrar(token):
    if request.method == 'POST':
        session['vendedor'] = f"{request.form['nombre']} {request.form['ap_materno']}"
        return redirect(url_for('index'))
    return render_template('registro.html')

if __name__ == '__main__':
    app.run()
