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
            session['vendedor'] = f"{usuario['nombre']} {usuario['ap_materno']}"
            return redirect('/inicio')
        return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/inicio')
def inicio():
    if 'vendedor' not in session: return redirect('/')
    return render_template('pos.html')

@app.route('/registrar/<token>', methods=['GET', 'POST'])
def registrar(token):
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        # Creamos fecha uniendo los campos del formulario
        fecha = f"{request.form['anio']}-{request.form['mes']}-{request.form['dia']}"
        cur.execute("INSERT INTO usuarios (nombre, ap_paterno, ap_materno, fecha_nac, celular, password) VALUES (%s, %s, %s, %s, %s, %s)",
                    (request.form['nombre'], request.form['ap_paterno'], request.form['ap_materno'], fecha, request.form['celular'], request.form['password']))
        conn.commit()
        cur.close(); conn.close()
        return redirect('/')
    return render_template('registro.html')

if __name__ == '__main__':
    app.run()
