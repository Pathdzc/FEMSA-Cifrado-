"""
Crea la base de datos vacía a partir de db/esquema.sql.
Si ya existe, no borra nada (solo crea lo que falte).

Uso (desde la carpeta raíz del proyecto):
    python scripts/crear_bd.py
"""
import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RUTA_BD

os.makedirs(os.path.dirname(RUTA_BD), exist_ok=True)

with open("db/esquema.sql", encoding="utf-8") as archivo:
    esquema = archivo.read()

conexion = sqlite3.connect(RUTA_BD)
conexion.executescript(esquema)

tablas = conexion.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
conexion.close()

print(f"Base de datos lista en {RUTA_BD}")
print("Tablas:", ", ".join(t[0] for t in tablas))
