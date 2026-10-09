from _future_ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Catálogos. Son SUPUESTOS: cuando se conozcan los valores reales (perfilado
# del archivo real), se ajustan aquí y en reglas.yaml.
# --------------------------------------------------------------------------
PAISES = {
    # país: (peso en el parque, región, probabilidad de macOS)
    "México": (0.42, "Norteamérica", 0.10),
    "Guatemala": (0.05, "Centroamérica", 0.05),
    "Costa Rica": (0.04, "Centroamérica", 0.08),
    "Panamá": (0.03, "Centroamérica", 0.08),
    "Colombia": (0.10, "Sudamérica", 0.12),
    "Ecuador": (0.03, "Sudamérica", 0.06),
    "Perú": (0.05, "Sudamérica", 0.20),
    "Brasil": (0.12, "Sudamérica", 0.22),
    "Chile": (0.06, "Sudamérica", 0.15),
    "Argentina": (0.04, "Sudamérica", 0.12),
    "Suiza": (0.04, "Europa", 0.30),
    "Alemania": (0.02, "Europa", 0.25),
}
VERSIONES_WINDOWS = (["Windows 10 21H2", "Windows 10 22H2", "Windows 11 22H2", "Windows 11 23H2", "Windows 11 24H2"],
                     [0.06, 0.20, 0.14, 0.38, 0.22])
VERSIONES_MAC = (["macOS 12", "macOS 13", "macOS 14", "macOS 15"], [0.08, 0.17, 0.40, 0.35])
BANDAS_ANTIGUEDAD = [(0, 12, "0-12 meses"), (13, 36, "13-36 meses"), (37, 60, "37-60 meses"), (61, 10_000, "Más de 60 meses")]
BANDAS_RECENCIA = [(0, 1, "0-1 meses"), (2, 3, "2-3 meses"), (4, 6, "4-6 meses"), (7, 10_000, "Más de 6 meses")]
FECHA_CORTE = pd.Period("2026-10", freq="M")

COLUMNAS = [
    "EquipoID", "UsuarioID", "País", "Región", "Sistema Operativo", "Versión SO", "Estado TPM",
    "Encryption Readiness", "Estado de Cifrado", "Tecnología de cifrado State", "Estado de Cumplimiento",
    "Categoría de Equipo", "Clase de Equipo", "Perfil de Privilegio", "Antigüedad Meses", "Banda Antigüedad",
    "Estado de Cuenta", "Mes Último Logon", "Banda Recencia", "Estado Hardware", "Tipo de Red",
    "Fuente de Datos", "En MDM", "En AD", "En MacOS",
]

# Carpeta de salida: docker-base/data/simulados (en el contenedor: /app/data/simulados).
# Es distinta de la carpeta de datos reales y en Docker se monta con escritura solo para este servicio.
SALIDA_POR_DEFECTO = Path(os.environ.get("SIMULADOS_DIR", Path(_file_).resolve().parent.parent / "data" / "simulados"))


def elegir(rng: np.random.Generator, opciones, pesos):
    p = np.asarray(pesos, dtype=float)
    return str(rng.choice(opciones, p=p / p.sum()))


def banda(valor: int, bandas) -> str:
    for lo, hi, etiqueta in bandas:
        if lo <= valor <= hi:
            return etiqueta
    return bandas[-1][2]


def generar_equipo(i: int, rng: np.random.Generator) -> dict:
    paises = list(PAISES)
    pais = elegir(rng, paises, [PAISES[p][0] for p in paises])
    _, region, prob_mac = PAISES[pais]
    so = "macOS" if rng.random() < prob_mac else "Windows"
    version = elegir(rng, *(VERSIONES_MAC if so == "macOS" else VERSIONES_WINDOWS))

    categoria = elegir(rng, ["Laptop", "Escritorio", "Workstation"], [0.68, 0.27, 0.05])
    clase = elegir(rng, ["Estándar", "Ejecutivo", "Crítico"], [0.80, 0.12, 0.08])
    privilegio = elegir(rng, ["Usuario estándar", "Administrador local", "Administrador TI"], [0.78, 0.17, 0.05])
    antiguedad = int(min(rng.exponential(26), 110))

    # TPM y readiness: los equipos viejos tienen más TPM ausente o 1.2
    if so == "macOS":
        tpm = "No aplica"
        readiness = elegir(rng, ["Listo", "No listo", "Desconocido"], [0.96, 0.02, 0.02])
    else:
        pesos_tpm = [0.55, 0.25, 0.08, 0.12] if antiguedad > 60 else [0.93, 0.03, 0.03, 0.01]
        tpm = elegir(rng, ["TPM 2.0 activo", "TPM 1.2", "TPM deshabilitado", "Sin TPM"], pesos_tpm)
        if tpm == "TPM 2.0 activo":
            readiness = "Listo" if rng.random() < 0.96 else "Desconocido"
        else:
            readiness = elegir(rng, ["No listo", "Listo", "Desconocido"], [0.80, 0.10, 0.10])

    # Presencia en fuentes de gestión
    en_mdm = rng.random() < 0.93
    en_ad = rng.random() < (0.97 if so == "Windows" else 0.40)
    en_macos = so == "macOS" and rng.random() < 0.90
    gestionado = en_mdm or en_macos

    # Estado de cifrado: depende de si está gestionado y de si puede cifrarse
    if not gestionado:
        estado = elegir(rng, ["Desconocido", "No cifrado", "Cifrado"], [0.70, 0.15, 0.15])
    elif readiness == "Listo":
        estado = elegir(rng, ["Cifrado", "Protección suspendida", "Cifrado en progreso", "No cifrado"],
                        [0.92, 0.03, 0.02, 0.03])
    else:
        estado = elegir(rng, ["No cifrado", "Cifrado", "Desconocido"], [0.75, 0.15, 0.10])

    # PATRÓN SEMBRADO 1: en Perú no se está forzando FileVault en macOS
    if pais == "Perú" and so == "macOS" and gestionado and rng.random() < 0.45:
        estado = "No cifrado"
    # PATRÓN SEMBRADO 2: en Guatemala, Windows 10 21H2 queda con protección suspendida tras actualizaciones
    if pais == "Guatemala" and version == "Windows 10 21H2" and estado == "Cifrado" and rng.random() < 0.40:
        estado = "Protección suspendida"
    # PATRÓN SEMBRADO 3: administradores locales con laptop suspenden más el cifrado
    if privilegio == "Administrador local" and categoria == "Laptop" and estado == "Cifrado" and rng.random() < 0.08:
        estado = "Protección suspendida"

    # Tecnología de cifrado. PATRÓN SEMBRADO 5: equipos viejos con más AES-CBC 128
    if estado in ("Cifrado", "Protección suspendida", "Cifrado en progreso"):
        if so == "macOS":
            tecnologia = "FileVault 2"
        else:
            pesos_alg = [0.30, 0.40, 0.30] if antiguedad > 60 else [0.65, 0.32, 0.03]
            tecnologia = elegir(rng, ["BitLocker XTS-AES 256", "BitLocker XTS-AES 128", "BitLocker AES-CBC 128"], pesos_alg)
    elif estado == "No cifrado":
        tecnologia = "Ninguna"
    else:
        tecnologia = "Desconocida"

    # Cumplimiento REPORTADO por la fuente. PATRÓN SEMBRADO 4: "Cumple" sin estar cifrado
    opciones_cumplimiento = {
        "Cifrado": (["Cumple", "No cumple"], [0.97, 0.03]),
        "No cifrado": (["No cumple", "Cumple", "Exento"], [0.85, 0.10, 0.05]),
        "Protección suspendida": (["Cumple", "No cumple"], [0.60, 0.40]),
        "Cifrado en progreso": (["Cumple", "No cumple"], [0.50, 0.50]),
        "Desconocido": (["Sin evaluar", "No cumple", "Cumple"], [0.80, 0.15, 0.05]),
    }
    cumplimiento = elegir(rng, *opciones_cumplimiento[estado])

    cuenta = elegir(rng, ["Activa", "Deshabilitada", "Bloqueada"], [0.90, 0.08, 0.02])
    meses_sin_logon = int(rng.exponential(1.2)) if cuenta == "Activa" else int(rng.integers(3, 18))
    red = elegir(rng, ["Corporativa", "VPN", "Remota", "Tienda"],
                 [0.35, 0.35, 0.25, 0.05] if categoria == "Laptop" else [0.70, 0.02, 0.03, 0.25])
    if so == "macOS":
        fuente = "Inventario MacOS" if en_macos else ("Intune" if en_mdm else "Directorio Activo")
    else:
        fuente = "Intune" if en_mdm else "Directorio Activo"

    return {
        "EquipoID": f"EQ-{i + 1:06d}",
        "UsuarioID": f"U-{int(rng.integers(10_000, 99_999))}",
        "País": pais,
        "Región": region,
        "Sistema Operativo": so,
        "Versión SO": version,
        "Estado TPM": tpm,
        "Encryption Readiness": readiness,
        "Estado de Cifrado": estado,
        "Tecnología de cifrado State": tecnologia,
        "Estado de Cumplimiento": cumplimiento,
        "Categoría de Equipo": categoria,
        "Clase de Equipo": clase,
        "Perfil de Privilegio": privilegio,
        "Antigüedad Meses": str(antiguedad),
        "Banda Antigüedad": banda(antiguedad, BANDAS_ANTIGUEDAD),
        "Estado de Cuenta": cuenta,
        "Mes Último Logon": str(FECHA_CORTE - meses_sin_logon),
        "Banda Recencia": banda(meses_sin_logon, BANDAS_RECENCIA),
        "Estado Hardware": elegir(rng, ["Operativo", "En reparación", "Dado de baja"], [0.94, 0.03, 0.03]),
        "Tipo de Red": red,
        "Fuente de Datos": fuente,
        "En MDM": "Sí" if en_mdm else "No",
        "En AD": "Sí" if en_ad else "No",
        "En MacOS": "Sí" if en_macos else "No",
    }


def inyectar_defectos(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Defectos típicos de exports reales, en proporciones pequeñas y controladas."""
    df = df.copy()
    n = len(df)

    def muestra(prop):
        return rng.choice(n, size=max(1, int(n * prop)), replace=False)

    variantes = {"México": ["Mexico", "MÉXICO", " México "], "Perú": ["Peru", "PERÚ"], "Panamá": ["Panama"]}
    for idx in muestra(0.02):                               # país escrito de otra forma
        pais = df.at[idx, "País"]
        if pais in variantes:
            df.at[idx, "País"] = str(rng.choice(variantes[pais]))

    for idx in muestra(0.01):                               # booleanos escritos de otra forma
        col = str(rng.choice(["En MDM", "En AD", "En MacOS"]))
        alternativas = {"Sí": ["SI", "si", "1"], "No": ["NO", "0"]}
        if df.at[idx, col] in alternativas:
            df.at[idx, col] = str(rng.choice(alternativas[df.at[idx, col]]))

    for col, prop in [("Versión SO", 0.010), ("Estado TPM", 0.008), ("Mes Último Logon", 0.010), ("País", 0.003)]:
        df.loc[muestra(prop), col] = None                   # vacíos

    for idx in muestra(0.005):                              # banda que no corresponde a los meses
        df.at[idx, "Banda Antigüedad"] = ("0-12 meses" if df.at[idx, "Banda Antigüedad"] != "0-12 meses"
                                          else "Más de 60 meses")

    for idx in muestra(0.003):                              # región que no corresponde al país
        df.at[idx, "Región"] = "Europa" if df.at[idx, "Región"] != "Europa" else "Sudamérica"

    mac = df.index[df["Sistema Operativo"] == "macOS"].to_numpy()
    win = df.index[df["Sistema Operativo"] == "Windows"].to_numpy()
    df.loc[rng.choice(mac, size=max(1, len(mac) // 300), replace=False), "Estado TPM"] = "TPM 2.0 activo"
    df.loc[rng.choice(win, size=max(1, len(win) // 500), replace=False), "Tecnología de cifrado State"] = "FileVault 2"
    df.loc[rng.choice(win, size=max(1, len(win) // 500), replace=False), "En MacOS"] = "Sí"

    exactos = df.loc[muestra(0.003)]                        # duplicados exactos
    contradictorios = df.loc[muestra(0.002)].copy()         # mismo EquipoID con otro estado
    contradictorios["Estado de Cifrado"] = contradictorios["Estado de Cifrado"].map(
        lambda e: "No cifrado" if e == "Cifrado" else "Cifrado")
    df = pd.concat([df, exactos, contradictorios], ignore_index=True)
    return df.sample(frac=1, random_state=int(rng.integers(0, 1_000_000))).reset_index(drop=True)


def generar_datos_simulados(num_registros: int = 5566, semilla: int = 42, con_defectos: bool = True) -> pd.DataFrame:
    """Devuelve un DataFrame con exactamente num_registros filas (incluyendo duplicados si con_defectos)."""
    rng = np.random.default_rng(semilla)
    unicos = num_registros
    if con_defectos:  # se descuentan los duplicados que se agregarán para que el total sea exacto
        while unicos + max(1, int(unicos * 0.003)) + max(1, int(unicos * 0.002)) > num_registros:
            unicos -= 1
    df = pd.DataFrame([generar_equipo(i, rng) for i in range(unicos)], columns=COLUMNAS)
    return inyectar_defectos(df, rng) if con_defectos else df


def main():
    parser = argparse.ArgumentParser(description="Genera datos simulados de cifrado de PCs")
    parser.add_argument("--filas", type=int, default=5566, help="Filas totales del archivo")
    parser.add_argument("--semilla", type=int, default=42, help="Misma semilla = mismo archivo")
    parser.add_argument("--sin-defectos", action="store_true", help="Genera datos limpios, sin errores de calidad")
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO / "equipos_simulados.csv")
    args = parser.parse_args()

    df = generar_datos_simulados(args.filas, args.semilla, con_defectos=not args.sin_defectos)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.salida, index=False, encoding="utf-8-sig")
    print(f"[+] {len(df):,} filas y {df.shape[1]} columnas en {args.salida}")


if _name_ == "_main_":
    main()
