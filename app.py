from flask import Flask, render_template, request, redirect, session
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder='static')
app.secret_key = 'JEJA_SECRETO_2026'

# Tu conexión a Supabase
URL_DB = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

def get_db():
    return psycopg2.connect(URL_DB)

# RUTA: Login (Raíz)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE celular = %s AND password = %s", 
                    (request.form['celular'], request.form['password']))
        user = cur.fetchone()
        cur.close(); conn.close()
        if user:
            session['vendedor'] = user['nombre']
            return redirect('/pos')
        return "Datos incorrectos, intenta de nuevo."
    return render_template('login.html')

# RUTA: Registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nombre, ap_paterno, ap_materno, celular, password) VALUES (%s, %s, %s, %s, %s)",
                    (request.form['nombre'], request.form['ap_paterno'], request.form['ap_materno'], 
                     request.form['celular'], request.form['password']))
        conn.commit()
        cur.close(); conn.close()
        return redirect('/')
    return render_template('registro.html')

# RUTA: Sistema POS
@app.route('/pos')
def pos():
    if 'vendedor' not in session: return redirect('/')
    return render_template('pos.html')

# RUTA: Procesar Venta
@app.route('/agregar_venta', methods=['POST'])
def agregar_venta():
    if 'vendedor' not in session: return redirect('/')
    # Aquí puedes agregar luego la lógica para guardar en BD
    return "Venta registrada con éxito. <a href='/pos'>Regresar al sistema</a>"

# RUTA: Logout
@app.route('/logout')
def logout():
    session.pop('vendedor', None)
    return redirect('/')

if __name__ == '__main__':
    app.run()
