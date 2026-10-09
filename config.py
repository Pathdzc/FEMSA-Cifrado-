"""
Configuración central del proyecto.

Por defecto el proyecto usa los DATOS SIMULADOS.
"""
import os

ARCHIVO_DATOS = os.environ.get("ARCHIVO_DATOS", "datos/simulados/equipos_simulados.csv")

# Base de datos (contiene datos: la carpeta datos/bd/ no se sube al repositorio)
RUTA_BD = os.environ.get("RUTA_BD", "datos/bd/proyecto.db")

# Columnas del archivo
# 25 columnas.
COLUMNAS = [
    "EquipoID", "UsuarioID", "País", "Región", "Sistema Operativo", "Versión SO",
    "Estado TPM", "Encryption Readiness", "Estado de Cifrado",
    "Tecnología de cifrado State", "Estado de Cumplimiento", "Categoría de Equipo",
    "Clase de Equipo", "Perfil de Privilegio", "Antigüedad Meses", "Banda Antigüedad",
    "Estado de Cuenta", "Mes Último Logon", "Banda Recencia", "Estado Hardware",
    "Tipo de Red", "Fuente de Datos", "En MDM", "En AD", "En MacOS",
]
