# Imagen base oficial de Python, versión ligera
FROM python:3.12-slim

# No crear archivos .pyc y mostrar los mensajes en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Instalar librerías (en un paso aparte para que Docker lo reutilice si no cambian)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copiar el código (.dockerignore evita copiar datos reales, base de datos y secretos)
COPY . .

# 3. Crear un usuario sin privilegios y darle permiso solo a la carpeta de la base de datos
RUN useradd --create-home usuario_app \
    && mkdir -p datos/bd datos/reales \
    && chown -R usuario_app:usuario_app datos/bd

# 4. A partir de aquí todo corre sin privilegios de administrador
USER usuario_app

EXPOSE 5000
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]
