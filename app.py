from flask import Flask, render_template, request, redirect, session

app = Flask(__name__, static_folder='static')
app.secret_key = 'JEJA_SECRETO_2026'
# ... el resto de tu código de base de datos sigue igual aquí abajo ...

app = Flask(__name__)
app.secret_key = 'JEJA_SECRETO_2026'
URL_DB = "postgresql://postgres.zivpdzxvukcovqjekxpz:B0mb0nsit03@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

def get_db():
    return psycopg2.connect(URL_DB)

# RUTA 1: Login (Raíz)
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
            return redirect('/pos')
        return "Credenciales incorrectas."
    return render_template('login.html')

# RUTA 2: Registro (Usando el token)
@app.route('/registrar/<token>', methods=['GET', 'POST'])
def registrar(token):
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        # Insertar usuario
        cur.execute("""INSERT INTO usuarios (nombre, ap_paterno, ap_materno, celular, password) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (request.form['nombre'], request.form['ap_paterno'], request.form['ap_materno'], 
                     request.form['celular'], request.form['password']))
        # Marcar token como usado
        cur.execute("UPDATE invitaciones SET usado = TRUE WHERE token = %s", (token,))
        conn.commit()
        cur.close(); conn.close()
        return redirect('/') # Regresa al login después de registrarse
    return render_template('registro.html', token=token)

@app.route('/pos')
def pos():
    if 'vendedor' not in session: return redirect('/')
    return render_template('pos.html')

if __name__ == '__main__':
    app.run()
