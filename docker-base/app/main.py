"""
Punto de entrada del contenedor (version base).

Por ahora solo comprueba que el contenedor esta bien armado:
  1. las librerias cargan
  2. la carpeta de datos se puede leer
  3. la carpeta de datos NO se puede escribir (debe ser solo lectura)
  4. la carpeta de resultados si se puede escribir

"""
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.reglas import aplicar_reglas

DATOS = Path(os.environ.get("DATOS_DIR", "/app/data"))
SALIDA = Path(os.environ.get("SALIDA_DIR", "/app/resultados"))


def se_puede_escribir(carpeta: Path) -> bool:
    prueba = carpeta / ".prueba_escritura"
    try:
        prueba.write_text("x")
        prueba.unlink()
        return True
    except OSError:
        return False


def escribir_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def cargar_dataset():
    csvs = sorted(DATOS.glob("*.csv"))
    xlsxs = sorted(DATOS.glob("*.xlsx"))

    if csvs:
        archivo = csvs[0]
        return archivo, pd.read_csv(archivo)
    if xlsxs:
        archivo = xlsxs[0]
        return archivo, pd.read_excel(archivo)

    return None, None


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    chequeos = []

    try:
        import numpy
        chequeos.append(("Librerías cargan", True, f"pandas {pd.__version__}, numpy {numpy.__version__}"))
    except ImportError as e:
        chequeos.append(("Librerías cargan", False, str(e)))

    existe = DATOS.is_dir()
    csvs = sorted(p.name for p in DATOS.glob("*.csv")) if existe else []
    xlsxs = sorted(p.name for p in DATOS.glob("*.xlsx")) if existe else []

    chequeos.append(("Carpeta de datos existe", existe, f"{DATOS}"))
    chequeos.append(("Datos en solo lectura", existe and not se_puede_escribir(DATOS), str(DATOS)))
    chequeos.append(("Resultados se pueden escribir", se_puede_escribir(SALIDA), str(SALIDA)))

    archivo, df = cargar_dataset()

    procesamiento = {
        "archivo_detectado": str(archivo) if archivo else None,
        "filas": 0,
        "columnas": 0,
        "procesado": False,
        "error": None,
    }

    resumen = {}
    incidencias_path = None
    enriquecido_path = None

    if df is not None:
        try:
            enriquecido, resumen, incidencias = aplicar_reglas(df)

            enriquecido_path = SALIDA / "dataset_enriquecido.csv"
            incidencias_path = SALIDA / "incidencias.csv"

            enriquecido.to_csv(enriquecido_path, index=False, encoding="utf-8-sig")
            incidencias.to_csv(incidencias_path, index=False, encoding="utf-8-sig")
            escribir_json(SALIDA / "resumen_kpis.json", resumen)

            procesamiento.update({
                "filas": int(len(df)),
                "columnas": int(len(df.columns)),
                "procesado": True,
            })
            chequeos.append(("Procesamiento de dataset", True, archivo.name))
        except Exception as e:
            procesamiento["error"] = str(e)
            chequeos.append(("Procesamiento de dataset", False, str(e)))
    else:
        chequeos.append(("Procesamiento de dataset", True, "No se encontró archivo en /app/data; contenedor base listo"))

    print(f"Python {platform.python_version()} | {datetime.now():%Y-%m-%d %H:%M:%S}\n")
    for nombre, ok, detalle in chequeos:
        print(f"  [{'OK' if ok else 'FALLA'}] {nombre}: {detalle}")

    todo_ok = all(ok for _, ok, _ in chequeos)

    estado = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "ok": todo_ok,
        "chequeos": [{"chequeo": n, "ok": o, "detalle": d} for n, o, d in chequeos],
        "procesamiento": procesamiento,
        "salidas": {
            "resumen_kpis": str(SALIDA / "resumen_kpis.json") if resumen else None,
            "dataset_enriquecido": str(enriquecido_path) if enriquecido_path else None,
            "incidencias": str(incidencias_path) if incidencias_path else None,
        }
    }

    escribir_json(SALIDA / "estado_contenedor.json", estado)

    print("\nContenedor listo." if todo_ok else "\nHay chequeos que fallaron.")
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
