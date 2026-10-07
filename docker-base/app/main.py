"""
Punto de entrada del contenedor (version base).

Por ahora solo comprueba que el contenedor esta bien armado:
  1. las librerias cargan
  2. la carpeta de datos se puede leer
  3. la carpeta de datos NO se puede escribir (debe ser solo lectura)
  4. la carpeta de resultados si se puede escribir

Cuando esten listas las reglas, aqui se manda llamar el modelo.
"""

import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

DATOS = Path(os.environ.get("DATOS_DIR", "data"))
SALIDA = Path(os.environ.get("SALIDA_DIR", "resultados"))


def se_puede_escribir(carpeta: Path) -> bool:
    prueba = carpeta / ".prueba_escritura"
    try:
        prueba.write_text("x")
        prueba.unlink()
        return True
    except OSError:
        return False


def main():
    chequeos = []

    try:
        import numpy
        import pandas
        chequeos.append(("Librerias cargan", True, f"pandas {pandas.__version__}, numpy {numpy.__version__}"))
    except ImportError as e:
        chequeos.append(("Librerias cargan", False, str(e)))

    existe = DATOS.is_dir()
    csvs = sorted(p.name for p in DATOS.glob("*.csv")) if existe else []
    chequeos.append(("Carpeta de datos existe", existe, f"{DATOS} ({len(csvs)} CSV: {', '.join(csvs) or 'ninguno'})"))
    chequeos.append(("Datos en solo lectura", existe and not se_puede_escribir(DATOS), str(DATOS)))

    SALIDA.mkdir(parents=True, exist_ok=True)
    chequeos.append(("Resultados se pueden escribir", se_puede_escribir(SALIDA), str(SALIDA)))

    print(f"Python {platform.python_version()} | {datetime.now():%Y-%m-%d %H:%M:%S}\n")
    for nombre, ok, detalle in chequeos:
        print(f"  [{'OK' if ok else 'FALLA'}] {nombre}: {detalle}")

    todo_ok = all(ok for _, ok, _ in chequeos)
    estado = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "ok": todo_ok,
        "chequeos": [{"chequeo": n, "ok": o, "detalle": d} for n, o, d in chequeos],
    }
    try:
        (SALIDA / "estado_contenedor.json").write_text(json.dumps(estado, indent=2, ensure_ascii=False))
    except OSError:
        pass

    print("\nContenedor listo." if todo_ok else "\nHay chequeos que fallaron.")
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
