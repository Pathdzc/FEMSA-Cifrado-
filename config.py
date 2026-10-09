"""
Configuración central del proyecto.

Por defecto el proyecto usa los DATOS SIMULADOS.
Para usar los datos reales (solo en tu máquina), guarda el archivo en
datos/reales/ y define la variable de entorno antes de correr:

    Windows (PowerShell):  $env:ARCHIVO_DATOS = "datos/reales/equipos.csv"
    Mac / Linux:           export ARCHIVO_DATOS=datos/reales/equipos.csv

La carpeta datos/reales/ está en .gitignore: nunca se sube al repositorio.
"""
import os

ARCHIVO_DATOS = os.environ.get("ARCHIVO_DATOS", "datos/simulados/equipos_simulados.csv")

# Base de datos (contiene datos: la carpeta datos/bd/ no se sube al repositorio)
RUTA_BD = os.environ.get("RUTA_BD", "datos/bd/proyecto.db")

# Columnas del archivo de FEMSA, en el mismo orden.
# Confirmado: 25 columnas.
COLUMNAS = [
    "EquipoID", "UsuarioID", "País", "Región", "Sistema Operativo", "Versión SO",
    "Estado TPM", "Encryption Readiness", "Estado de Cifrado",
    "Tecnología de cifrado State", "Estado de Cumplimiento", "Categoría de Equipo",
    "Clase de Equipo", "Perfil de Privilegio", "Antigüedad Meses", "Banda Antigüedad",
    "Estado de Cuenta", "Mes Último Logon", "Banda Recencia", "Estado Hardware",
    "Tipo de Red", "Fuente de Datos", "En MDM", "En AD", "En MacOS",
]
