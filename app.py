from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Tu cadena de conexión (la que ya tenías en tu código)
URL_BASE_DATOS = "postgresql://postgres:B0mb0nsit03@db.zivpdzxvukcovqjekxpz.supabase.co:5432/postgres"

# Configuración de carpetas
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CARPETA_SUBIDAS = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

def conectar_bd():
    return psycopg2.connect(URL_BASE_DATOS)

# [MANTIENE TODAS TUS RUTAS ORIGINALES: /, /inventario, /tickets, /guardar_producto, etc.]
# ... (Copia aquí exactamente todas tus rutas del archivo que me pasaste) ...

if __name__ == '__main__':
    app.run()
