"""
Aplicación web: esqueleto de la semana 1.

Por ahora solo comprueba que todo funciona: lee el archivo de datos
y muestra cuántas filas y columnas tiene. No muestra ningún dato.

Correr sin Docker:   flask --app app run
Correr con Docker:   docker compose up --build
Después abrir:       http://localhost:5000
"""
import os
from flask import Flask
from markupsafe import escape
from config import ARCHIVO_DATOS, COLUMNAS
from cargar_datos import cargar_datos

app = Flask(__name__)


@app.route("/")
def inicio():
    datos = cargar_datos(ARCHIVO_DATOS)
    columnas_ok = list(datos.columns) == COLUMNAS
    nombre = escape(os.path.basename(ARCHIVO_DATOS))   # escape: evita inyectar HTML

    return f"""
    <h1>Proyecto B · Discos Duros Cifrados</h1>
    <p>Archivo: {nombre}</p>
    <p>Filas: {len(datos):,}</p>
    <p>Columnas: {len(datos.columns)}</p>
    <p>Estructura esperada: {"Sí" if columnas_ok else "No, revisar el perfilado"}</p>
    """
