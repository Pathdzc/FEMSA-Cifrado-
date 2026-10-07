#!/bin/bash
# Crea la carpeta docker-base con todos sus archivos.
# Uso: bash crear_docker_base.sh
set -e
mkdir -p docker-base/app docker-base/data docker-base/resultados
cd docker-base

cat > Dockerfile <<'EOF'
# Docker base del proyecto FEMSA - discos cifrados
# Un solo contenedor donde despues va a vivir todo (modelo + interfaz).
# No se instala nada fuera del contenedor.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATOS_DIR=/app/data \
    SALIDA_DIR=/app/resultados

WORKDIR /app

# dependencias primero, para aprovechar la cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# codigo
COPY app/ app/

# usuario sin privilegios (no corre como root)
RUN useradd --create-home appuser \
 && mkdir -p /app/data /app/resultados \
 && chown -R appuser /app
USER appuser

CMD ["python", "-m", "app.main"]
EOF

cat > docker-compose.yml <<'EOF'
services:
  femsa:
    build: .
    image: femsa-cifrado:base
    container_name: femsa-cifrado
    read_only: true            # el contenedor no puede modificar su propio sistema de archivos
    tmpfs:
      - /tmp
    volumes:
      - ./data:/app/data:ro          # datos de entrada, SOLO LECTURA
      - ./resultados:/app/resultados # unico lugar donde el contenedor puede escribir
EOF

cat > requirements.txt <<'EOF'
pandas==2.2.3
numpy==2.1.3
EOF

cat > .dockerignore <<'EOF'
data/
resultados/
__pycache__/
**/__pycache__/
.pytest_cache/
.git/
*.zip
.DS_Store
EOF

cat > app/__init__.py <<'EOF'
EOF

cat > app/main.py <<'EOF'
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
EOF

cat > data/LEEME.txt <<'EOF'
Aqui van los CSV de entrada (AD, plataforma de cifrado, inventario).
El contenedor monta esta carpeta en modo solo lectura.
EOF

cat > resultados/LEEME.txt <<'EOF'
Aqui el contenedor deja sus resultados. Es la unica carpeta donde puede escribir.
EOF

echo "Listo. Ahora: cd docker-base && docker compose up --build"