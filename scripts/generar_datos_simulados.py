"""
Genera datos SIMULADOS con la misma estructura y los mismos valores posibles
que el archivo real de FEMSA. Ninguna fila viene de los datos reales.

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
TOTAL_FILAS = 5563       # igual que el archivo real
ID_MAXIMO = 5588         # los EquipoID van de PC-001 a PC-5588 (hay huecos)
USUARIO_MAXIMO = 4517    # los UsuarioID van de U-001 a U-4517
DUPLICADOS = 10          # filas repetidas a propósito para probar el sistema (0 = ninguna)
SALIDA = "datos/simulados/equipos_simulados.csv"
ND = "No disponible"

# País -> región
PAISES = {
    "México": "Norteamérica",
    "Costa Rica": "Centroamérica", "Guatemala": "Centroamérica",
    "Nicaragua": "Centroamérica", "Panamá": "Centroamérica",
    "Argentina": "Sudamérica", "Brasil": "Sudamérica", "Colombia": "Sudamérica",
    "Uruguay": "Sudamérica", "Venezuela": "Sudamérica",
    ND: ND,
}
PESOS_PAISES = [45, 5, 6, 3, 4, 6, 12, 10, 3, 3, 3]

# Meses de último logon posibles (del más viejo al más reciente)
MESES_LOGON = ["2023-01", "2023-09", "2023-10", "2023-11", "2023-12", "2024-01", "2024-05",
               "2024-06", "2024-09", "2024-10", "2024-11", "2024-12", "2025-01", "2025-03",
               "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"]
PESOS_LOGON = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 5, 10, 20, 45]
MES_REFERENCIA = "2025-10"   # el mes más reciente de los datos


def elegir(opciones, pesos):
    """Elige una opción al azar respetando los pesos."""
    return random.choices(opciones, weights=pesos)[0]


def banda_antiguedad(meses):
    if meses is None: return ND
    if meses < 12: return "<1 año"
    if meses < 36: return "1-2 años"
    return "3-4 años"


def banda_recencia(mes):
    """Calcula la banda según cuántos meses pasaron desde MES_REFERENCIA."""
    a1, m1 = map(int, mes.split("-"))
    a2, m2 = map(int, MES_REFERENCIA.split("-"))
    diferencia = (a2 * 12 + m2) - (a1 * 12 + m1)
    if diferencia == 0: return "0-30 días"
    if diferencia <= 2: return "31-90 días"
    if diferencia <= 5: return "91-180 días"
    return ">180 días"


# ---------------------------------------------------------------
# PASO 1: generar un equipo (una fila)
# ---------------------------------------------------------------
def generar_equipo(equipo_id):
    pais = elegir(list(PAISES), PESOS_PAISES)
    so = elegir(["Windows", "macOS"], [85, 15])

    # 1a. ¿De qué fuente viene el equipo?
    if so == "Windows":
        fuente = elegir(["MDM+AD", "MDM", "AD"], [80, 10, 10])
    else:
        fuente = elegir(["Iinventario macOS", "MDM"], [70, 30])
    en_mdm = "Sí" if "MDM" in fuente else "No"
    en_ad = "Sí" if "AD" in fuente else "No"
    en_macos = "Sí" if fuente == "Iinventario macOS" else "No"

    # 1b. Valores por defecto: sin información
    version, tpm, readiness = ND, ND, ND
    estado, detalle, cumplimiento = ND, ND, ND
    categoria, hardware, red = ND, ND, "No diponible"

    # 1c. Windows en MDM: es donde hay más información
    if so == "Windows" and en_mdm == "Sí":
        version = elegir(["10.0.19043.x", "10.0.19044.x", "10.0.19045.x",
                          "10.0.22631.x", "10.0.26100.x", "10.0.26200.x"], [3, 5, 22, 35, 30, 5])
        tpm = elegir(["TPM 2", "TPM 1.2", ND], [90, 4, 6])
        readiness = "Ready" if tpm == "TPM 2" and random.random() < 0.95 else "Not ready"

        probabilidad = 0.92 if readiness == "Ready" else 0.20
        # Patrón escondido a propósito: en Colombia, Windows 10 (build 19045) casi no se cifra
        if pais == "Colombia" and version == "10.0.19045.x":
            probabilidad = 0.35

        if random.random() < probabilidad:
            estado = "Encrypted"
            detalle = elegir(["Success",
                              "Encryption method of OS Volume is different than that set by policy",
                              "TPM not used for protection of OS volume, but is required by policy"],
                             [90, 7, 3])
            cumplimiento = elegir(["Compliant", "Unknown"], [95, 5])
        else:
            estado = "Not encrypted"
            detalle = elegir(["Fixed Drive, not Encrypted",
                              "TPM not used for protection of OS volume, but is required by policy",
                              ND], [50, 30, 20])
            # No existe "No cumple" en los datos: algunos sin cifrar aparecen como Compliant
            cumplimiento = elegir(["Unknown", "Compliant"], [60, 40])

        categoria = elegir(["Laptop", ND], [95, 5])
        hardware = elegir(["Installed", "Pending Install", ND], [90, 5, 5])
        red = elegir(["Privada", "CGNAT", "No diponible"], [60, 30, 10])

    # 1d. Windows solo en AD: AD no sabe nada del cifrado
    elif so == "Windows":
        version = elegir(["Windows 10", "Windows (versión agrupada)", "Windows 15"], [50, 45, 5])

    # 1e. macOS (en MDM o en inventario manual)
    else:
        tpm = "No aplica"
        detalle = "No aplica"
        estado = elegir(["Encrypted", "Not encrypted"], [88, 12])
        if en_mdm == "Sí":
            version = elegir(["26.0.x", "macOs 15"], [50, 50])
            cumplimiento = "Compliant" if estado == "Encrypted" else "Unknown"
            categoria = "Laptop"
            red = elegir(["Privada", "CGNAT"], [60, 40])
        else:
            version = elegir(["macOs (versión agrupada)", "macOs 15"], [60, 40])
            categoria = "Laptop"

    # 1f. Datos que vienen de AD: cuenta y último logon
    if en_ad == "Sí":
        cuenta = "Habilitada"
        mes_logon = elegir(MESES_LOGON, PESOS_LOGON)
        recencia = banda_recencia(mes_logon)
    else:
        cuenta = "No aplica" if so == "macOS" else ND
        mes_logon, recencia = ND, ND

    # 1g. Perfil de privilegio: sin AD no se conoce
    if en_ad == "Sí":
        perfil = elegir(["Usuario avanzado", "Administrador", "Sin dato"], [65, 20, 15])
    else:
        perfil = ND

    antiguedad = elegir([2, 7, 13, 23, 36, None], [15, 20, 20, 20, 15, 10])
    usuario = "No asignado" if random.random() < 0.05 else f"U-{random.randint(1, USUARIO_MAXIMO):03d}"

    return {
        "EquipoID": f"PC-{equipo_id:03d}",
        "UsuarioID": usuario,
        "País": pais,
        "Región": PAISES[pais],
        "Sistema Operativo": so,
        "Versión SO": version,
        "Estado TPM": tpm,
        "Encryption Readiness": readiness,
        "Estado de Cifrado": estado,
        "Tecnología de cifrado State": detalle,
        "Estado de Cumplimiento": cumplimiento,
        "Categoría de Equipo": categoria,
        "Clase de Equipo": "Computer",
        "Perfil de Privilegio": perfil,
        "Antigüedad Meses": antiguedad,
        "Banda Antigüedad": banda_antiguedad(antiguedad),
        "Estado de Cuenta": cuenta,
        "Mes Último Logon": mes_logon,
        "Banda Recencia": recencia,
        "Estado Hardware": hardware,
        "Tipo de Red": red,
        "Fuente de Datos": fuente,
        "En MDM": en_mdm,
        "En AD": en_ad,
        "En MacOS": en_macos,
    }


# ---------------------------------------------------------------
# PASO 2: elegir qué IDs existen (hay huecos entre PC-001 y PC-5588)
# ---------------------------------------------------------------
ids = sorted(random.sample(range(1, ID_MAXIMO + 1), TOTAL_FILAS - DUPLICADOS))
datos = pd.DataFrame([generar_equipo(i) for i in ids], columns=COLUMNAS)

# ---------------------------------------------------------------
# PASO 3: agregar filas duplicadas a propósito
# ---------------------------------------------------------------
if DUPLICADOS > 0:
    datos = pd.concat([datos, datos.sample(DUPLICADOS, random_state=1)], ignore_index=True)
datos = datos.sample(frac=1, random_state=2).reset_index(drop=True)

# Antigüedad como número entero (sin ".0") y vacía cuando no hay dato
datos["Antigüedad Meses"] = datos["Antigüedad Meses"].astype("Int64")

# ---------------------------------------------------------------
# PASO 4: guardar
# ---------------------------------------------------------------
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
datos.to_csv(SALIDA, index=False, encoding="utf-8-sig")   # utf-8-sig: Excel lee bien los acentos
print(f"Listo: {len(datos)} filas y {len(datos.columns)} columnas en {SALIDA}")
