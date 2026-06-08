from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'JEJA_SECRETO_2026'
URL_DB = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

def get_db():
    return psycopg2.connect(URL_DB)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        celular = request.form['celular']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE celular = %s AND password = %s", (celular, password))
        usuario = cur.fetchone()
        cur.close(); conn.close()
        
        if usuario:
            session['vendedor'] = usuario['nombre']
            return redirect(url_for('inicio'))
        return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/inicio')
def inicio():
    if 'vendedor' not in session: return redirect(url_for('login'))
    return render_template('pos.html')

@app.route('/registrar/<token>', methods=['GET', 'POST'])
def registrar(token):
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nombre, ap_paterno, ap_materno, celular, password) VALUES (%s, %s, %s, %s, %s)",
                    (request.form['nombre'], request.form['ap_paterno'], request.form['ap_materno'], request.form['celular'], request.form['password']))
        conn.commit()
        cur.close(); conn.close()
        return redirect(url_for('login'))
    return render_template('registro.html')

if __name__ == '__main__':
    app.run()
