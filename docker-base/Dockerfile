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
