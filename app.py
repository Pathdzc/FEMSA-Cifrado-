import os
import json
import subprocess
import pandas as pd

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from config import COLUMNAS
from cargar_datos import cargar_datos

app = Flask(__name__)
app.secret_key = "femsa-local-secret"

UPLOAD_FOLDER = "uploads"
SALIDAS_DIR = "salidas"
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def cargar_resumen():
    ruta = os.path.join(SALIDAS_DIR, "resumen_reglas.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_universo():
    ruta = os.path.join(SALIDAS_DIR, "universo_conciliado.csv")
    if not os.path.exists(ruta):
        return None
    return pd.read_csv(ruta)


def cargar_resultados():
    ruta = os.path.join(SALIDAS_DIR, "resultados_reglas.csv")
    if not os.path.exists(ruta):
        return None
    return pd.read_csv(ruta)


def info_archivo_actual(ruta_archivo):
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return None

    datos = cargar_datos(ruta_archivo)
    return {
        "archivo": os.path.basename(ruta_archivo),
        "filas": len(datos),
        "columnas": len(datos.columns),
        "columnas_ok": list(datos.columns) == COLUMNAS,
    }


def ruta_archivo_actual():
    return os.path.join(UPLOAD_FOLDER, "archivo_actual")


@app.route("/", methods=["GET", "POST"])
def inicio():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(SALIDAS_DIR, exist_ok=True)

    mensaje_error = None
    archivo_info = None

    if request.method == "POST":
        if "archivo" not in request.files:
            flash("No se encontró ningún archivo en la solicitud.", "error")
            return redirect(url_for("inicio"))

        archivo = request.files["archivo"]

        if archivo.filename == "":
            flash("Debes seleccionar un archivo.", "error")
            return redirect(url_for("inicio"))

        if not allowed_file(archivo.filename):
            flash("Formato no permitido. Solo se aceptan CSV, XLSX o XLS.", "error")
            return redirect(url_for("inicio"))

        nombre_seguro = secure_filename(archivo.filename)
        extension = nombre_seguro.rsplit(".", 1)[1].lower()
        ruta_destino = os.path.join(UPLOAD_FOLDER, f"archivo_actual.{extension}")

        archivo.save(ruta_destino)

        try:
            env = os.environ.copy()
            env["ARCHIVO_DATOS"] = ruta_destino

            resultado = subprocess.run(
                ["python", "scripts/evaluar.py"],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            if resultado.returncode != 0:
                mensaje_error = resultado.stderr or resultado.stdout or "La evaluación falló."
                flash(f"Error al evaluar el archivo: {mensaje_error}", "error")
            else:
                flash("Archivo cargado y evaluado correctamente.", "ok")

        except Exception as e:
            flash(f"Error al ejecutar la evaluación: {e}", "error")

        return redirect(url_for("inicio"))

    # detectar archivo ya cargado
    archivo_actual = None
    for nombre in os.listdir(UPLOAD_FOLDER):
        if nombre.startswith("archivo_actual."):
            archivo_actual = os.path.join(UPLOAD_FOLDER, nombre)
            break

    archivo_info = info_archivo_actual(archivo_actual)
    resumen = cargar_resumen()

    return render_template(
        "index.html",
        archivo_info=archivo_info,
        resumen=resumen,
    )


@app.route("/universo")
def universo():
    df = cargar_universo()
    if df is None:
        return render_template("universo.html", universo=None, filtros={}, total=0)

    estado = request.args.get("estado_control", "")
    pais = request.args.get("pais", "")
    so = request.args.get("so", "")

    filtrado = df.copy()

    if estado:
        filtrado = filtrado[filtrado["estado_control"] == estado]
    if pais:
        filtrado = filtrado[filtrado["País"] == pais]
    if so:
        filtrado = filtrado[filtrado["Sistema Operativo"] == so]

    estados = sorted(df["estado_control"].dropna().unique().tolist())
    paises = sorted(df["País"].dropna().unique().tolist())
    sistemas = sorted(df["Sistema Operativo"].dropna().unique().tolist())

    return render_template(
        "universo.html",
        universo=filtrado.to_dict(orient="records"),
        total=len(filtrado),
        filtros={
            "estado_control": estado,
            "pais": pais,
            "so": so,
            "estados": estados,
            "paises": paises,
            "sistemas": sistemas,
        },
    )


@app.route("/reglas")
def reglas():
    resumen = cargar_resumen()
    if not resumen:
        return render_template("reglas.html", reglas=None)

    return render_template("reglas.html", reglas=resumen.get("reglas", []))


@app.route("/cobertura")
def cobertura():
    resumen = cargar_resumen()
    if not resumen:
        return render_template("cobertura.html", cobertura=None, universo=None)

    return render_template(
        "cobertura.html",
        cobertura=resumen.get("cobertura", []),
        universo=resumen.get("universo", {}),
    )

@app.route("/graficas")
def graficas():
    df = cargar_universo()
    if df is None:
        return render_template("graficas.html", datos=None)

    estados = df["estado_control"].value_counts()
    tabla_pais = pd.crosstab(df["País"], df["estado_control"])
    tabla_so = pd.crosstab(df["Sistema Operativo"], df["estado_control"])
    resumen = cargar_resumen()
    reglas = resumen.get("reglas", []) if resumen else []

    datos = {
        "estados": {
            "labels": estados.index.tolist(),
            "values": [int(v) for v in estados.values],
        },
                "por_pais": {
            "paises": tabla_pais.index.tolist(),
            "estados": {
                estado: [int(v) for v in tabla_pais[estado]]
                for estado in tabla_pais.columns
            },
        },
        "por_so": {
            "sistemas": tabla_so.index.tolist(),
            "estados": {
                estado: [int(v) for v in tabla_so[estado]]
                for estado in tabla_so.columns
            },
        },
                "reglas": {
            "nombres": [f'{r["regla"]} · {r["nombre_regla"]}' for r in reglas],
            "Sí": [int(r.get("Sí", 0) or 0) for r in reglas],
            "No": [int(r.get("No", 0) or 0) for r in reglas],
            "Sin información": [int(r.get("Sin información", 0) or 0) for r in reglas],
            "No aplica": [int(r.get("No aplica", 0) or 0) for r in reglas],
        },
    }
    return render_template("graficas.html", datos=datos)

if __name__ == "__main__":
    app.run(debug=True)
