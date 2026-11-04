"""
Genera datos SIMULADOS. Ninguna fila viene de los datos reales.

Uso (desde la carpeta raíz del proyecto):
    python scripts/generar_datos_simulados.py
"""
import os
import sys
import random
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLUMNAS

random.seed(42)          # misma semilla = siempre los mismos datos
TOTAL_FILAS = 5563       
ID_MAXIMO = 5588         # los EquipoID van de PC-001 a PC-5588
USUARIO_MAXIMO = 4517    
SALIDA = "datos/simulados/equipos_simulados.csv"
ND = "No disponible"

# Valores posibles de cada columna 
VALORES = {
    "País": ["Argentina", "Brasil", "Colombia", "Costa Rica", "Guatemala", "México",
             "Nicaragua", ND, "Panamá", "Uruguay", "Venezuela"],
    "Sistema Operativo": ["Windows", "macOS"],
    "Versión SO": ["10.0.19043.x", "10.0.19044.x", "10.0.19045.x", "10.0.22631.x",
                   "10.0.26100.x", "10.0.26200.x", "26.0.x", "macOs (versión agrupada)",
                   "macOs 15", "Windows (versión agrupada)", "Windows 10", "Windows 15"],
    "Estado TPM": ["No aplica", ND, "TPM 1.2", "TPM 2"],
    "Encryption Readiness": ["Ready", "Not ready", ND],
    "Estado de Cifrado": ["Encrypted", "Not encrypted", ND],
    "Tecnología de cifrado State": [
        "No aplica", ND, "Success",
        "TPM not used for protection of OS volume, but is required by policy",
        "Encryption method of OS Volume is different than that set by policy",
        "Fixed Drive, not Encrypted"],
    "Estado de Cumplimiento": ["Compliant", ND, "Unknown"],
    "Categoría de Equipo": ["Laptop", ND],
    "Clase de Equipo": ["Computer"],
    "Perfil de Privilegio": ["Administrador", "Sin dato", ND, "Usuario avanzado"],
    "Antigüedad Meses": [2, 7, 13, 23, 36, None],          # None = celda en blanco
    "Estado de Cuenta": ["Habilitada", "No aplica", ND],
    "Mes Último Logon": ["2023-01", "2023-09", "2023-10", "2023-11", "2023-12", "2024-01",
                         "2024-05", "2024-06", "2024-09", "2024-10", "2024-11", "2024-12",
                         "2025-01", "2025-03", "2025-05", "2025-06", "2025-07", "2025-08",
                         "2025-09", "2025-10", ND],
    "Banda Recencia": [">180 días", "0-30 días", "31-90 días", "91-180 días", ND],
    "Estado Hardware": ["Installed", "Pending Install", ND],
    "Tipo de Red": ["CGNAT", "No diponible", "Privada"],
    "Fuente de Datos": ["MDM+AD", "Iinventario macOS", "MDM", "AD"],
    "En MDM": ["Sí", "No"],
    "En AD": ["Sí", "No"],
    "En MacOS": ["Sí", "No"],
}

# Definiciones (no supuestos)
REGION = {
    "Argentina": "Sudamérica", "Brasil": "Sudamérica", "Colombia": "Sudamérica",
    "Uruguay": "Sudamérica", "Venezuela": "Sudamérica",
    "México": "Norteamérica",
    "Costa Rica": "Centroamérica", "Guatemala": "Centroamérica",
    "Nicaragua": "Centroamérica", "Panamá": "Centroamérica",
    ND: ND,
}


def banda_antiguedad(meses):
    if meses is None: return ND
    if meses < 12: return "<1 año"
    if meses < 36: return "1-2 años"
    return "3-4 años"


#   Generar un equipo (una fila)
def generar_equipo(equipo_id):
    fila = {columna: random.choice(opciones) for columna, opciones in VALORES.items()}

    fila["EquipoID"] = f"PC-{equipo_id:03d}"
    usuario = random.randint(0, USUARIO_MAXIMO)            # 0 = sin usuario
    fila["UsuarioID"] = "No asignado" if usuario == 0 else f"U-{usuario:03d}"
    fila["Región"] = REGION[fila["País"]]
    fila["Banda Antigüedad"] = banda_antiguedad(fila["Antigüedad Meses"])
    return fila


# Generar todas las filas (IDs únicos entre PC-001 y PC-5588)
ids = sorted(random.sample(range(1, ID_MAXIMO + 1), TOTAL_FILAS))
datos = pd.DataFrame([generar_equipo(i) for i in ids], columns=COLUMNAS)

# Antigüedad vacía cuando no hay dato y entera
datos["Antigüedad Meses"] = datos["Antigüedad Meses"].astype("Int64")

# Guardar
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
datos.to_csv(SALIDA, index=False, encoding="utf-8-sig")   # Excel lee bien los acentos
print(f"Listo: {len(datos)} filas y {len(datos.columns)} columnas en {SALIDA}")