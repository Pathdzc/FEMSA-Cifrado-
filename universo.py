"""
Universo conciliado.

Toma el archivo tal como llegó (todo como texto) y arma una tabla de trabajo con
UNA fila por equipo, donde cada equipo queda clasificado en exactamente un
"estado de control". Así los porcentajes siempre suman 100% del universo.

Reglas de oro (ver docs/modelo_datos.md):
  - El archivo original NUNCA se modifica: todo se calcula sobre una copia.
  - Los supuestos vienen de docs/dudas_y_supuestos.md. Si FEMSA responde algo
    distinto, se cambia aquí y en ese documento.
"""
import re
import pandas as pd

ND = "No disponible"

# Valores que significan "no hay dato".
# "No aplica" NO está aquí porque sí es información.
# "Sin dato" se trata igual que "No disponible" (supuesto 7).
SIN_DATO = {"", "No disponible", "No diponible", "Sin dato"}

# Errores de captura conocidos -> valor corregido.
# El valor original se conserva en el archivo; esto solo afecta la copia de trabajo.
CORRECCIONES = {
    "Fuente de Datos": {"Iinventario macOS": "Inventario macOS"},
}

# Valores imposibles: se reportan como hallazgo y se tratan como sin dato.
VALORES_INVALIDOS = {
    "Versión SO": {"Windows 15"},
}

REGION_ESPERADA = {
    "Argentina": "Sudamérica",
    "Brasil": "Sudamérica",
    "Colombia": "Sudamérica",
    "Uruguay": "Sudamérica",
    "Venezuela": "Sudamérica",
    "México": "Norteamérica",
    "Costa Rica": "Centroamérica",
    "Guatemala": "Centroamérica",
    "Nicaragua": "Centroamérica",
    "Panamá": "Centroamérica",
}

# Qué banderas debería tener cada valor de "Fuente de Datos".
# (En MDM, En AD, En MacOS); None = no se puede afirmar nada de esa bandera.
FUENTE_ESPERADA = {
    "MDM+AD": ("Sí", "Sí", None),
    "MDM": ("Sí", "No", None),
    "AD": ("No", "Sí", None),
    "Inventario macOS": (None, None, "Sí"),
}

# Estados de control: mutuamente excluyentes, en orden de gravedad (peor primero).
ESTADOS_CONTROL = [
    "No cifrado",
    "Sin visibilidad",
    "Cifrado fuera de política",
    "Cifrado, política sin verificar",
    "Cumple",
]


def normalizar(datos: pd.DataFrame) -> pd.DataFrame:
    """Copia de trabajo limpia. Los valores sin dato quedan como ND."""
    df = datos.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].where(~df[col].isin(SIN_DATO), ND)

    for col, mapa in CORRECCIONES.items():
        if col in df.columns:
            df[col] = df[col].replace(mapa)

    for col, invalidos in VALORES_INVALIDOS.items():
        if col in df.columns:
            df[col] = df[col].where(~df[col].isin(invalidos), ND)

    # Banderas: solo "Sí" o "No"; cualquier otra cosa queda como sin dato.
    for col in ["En MDM", "En AD", "En MacOS"]:
        if col in df.columns:
            df[col] = df[col].replace({"Si": "Sí", "SI": "Sí", "NO": "No"})
            df[col] = df[col].where(df[col].isin(["Sí", "No"]), ND)

    return df


def _numero_id(equipo_id: str):
    m = re.fullmatch(r"PC-(\d+)", str(equipo_id))
    return int(m.group(1)) if m else None


def estado_control(fila) -> str:
    """Un solo estado por fila."""
    cifrado = fila["Estado de Cifrado"]
    detalle = fila["Tecnología de cifrado State"]

    if cifrado == "Not encrypted":
        return "No cifrado"
    if cifrado != "Encrypted":
        return "Sin visibilidad"
    if detalle == "Success":
        return "Cumple"
    if detalle == "No aplica" and fila["Sistema Operativo"] == "macOS":
        return "Cumple"
    if detalle == ND:
        return "Cifrado, política sin verificar"
    return "Cifrado fuera de política"


def cobertura(fila) -> str:
    """En qué fuentes aparece el equipo, según las banderas En MDM / En AD / En MacOS."""
    nombres = [
        n for n, col in [
            ("MDM", "En MDM"),
            ("AD", "En AD"),
            ("Inventario macOS", "En MacOS"),
        ]
        if fila[col] == "Sí"
    ]
    return " + ".join(nombres) if nombres else "Ninguna fuente"


def fuente_consistente(fila) -> str:
    """'Sí' / 'No' si 'Fuente de Datos' coincide con las banderas; 'Sin información' si no se puede evaluar."""
    esperado = FUENTE_ESPERADA.get(fila["Fuente de Datos"])
    if esperado is None:
        return "Sin información"

    reales = (fila["En MDM"], fila["En AD"], fila["En MacOS"])
    for e, r in zip(esperado, reales):
        if e is not None and r != e:
            return "No"
    return "Sí"


def construir_universo(datos: pd.DataFrame):
    """
    Regresa (filas, universo):
      filas    -> una fila por registro del archivo, normalizada y clasificada
                  (es la que se evalúa con las reglas, 100% de los registros)
      universo -> una fila por EquipoID único, con el estado de control final
    """
    filas = normalizar(datos)
    filas.insert(0, "fila_archivo", range(1, len(filas) + 1))

    filas["estado_control"] = filas.apply(estado_control, axis=1)
    filas["cobertura"] = filas.apply(cobertura, axis=1)
    filas["fuente_consistente"] = filas.apply(fuente_consistente, axis=1)
    filas["equipo_repetido"] = filas["EquipoID"].duplicated(keep=False)

    gravedad = {e: i for i, e in enumerate(ESTADOS_CONTROL)}
    filas["_gravedad"] = filas["estado_control"].map(gravedad)

    universo = (
        filas.sort_values(["EquipoID", "_gravedad"])
        .drop_duplicates("EquipoID", keep="first")
        .drop(columns="_gravedad")
        .sort_values("fila_archivo")
        .reset_index(drop=True)
    )

    filas = filas.drop(columns="_gravedad")
    universo["registros_en_archivo"] = universo["EquipoID"].map(filas["EquipoID"].value_counts())

    columnas = [
        "EquipoID",
        "País",
        "Región",
        "Sistema Operativo",
        "Categoría de Equipo",
        "Perfil de Privilegio",
        "Banda Recencia",
        "Fuente de Datos",
        "cobertura",
        "fuente_consistente",
        "Estado de Cifrado",
        "Tecnología de cifrado State",
        "Encryption Readiness",
        "estado_control",
        "registros_en_archivo",
    ]
    return filas, universo[columnas]


def resumen_universo(datos: pd.DataFrame, filas: pd.DataFrame, universo: pd.DataFrame) -> dict:
    """Números del universo. Los conteos de estado siempre suman el total."""
    total = len(universo)
    conteo = universo["estado_control"].value_counts().reindex(ESTADOS_CONTROL, fill_value=0)

    numeros = [n for n in filas["EquipoID"].map(_numero_id) if n is not None]
    ids_fuera_de_formato = int(filas["EquipoID"].map(_numero_id).isna().sum())
    rango = (min(numeros), max(numeros)) if numeros else (None, None)
    huecos = (rango[1] - rango[0] + 1 - len(set(numeros))) if numeros else 0

    return {
        "registros_en_archivo": int(len(datos)),
        "equipos_unicos": int(total),
        "registros_repetidos": int(len(filas) - total),
        "ids_fuera_de_formato": ids_fuera_de_formato,
        "rango_ids": f"PC-{rango[0]:03d} a PC-{rango[1]:03d}" if numeros else None,
        "ids_faltantes_en_rango": int(huecos),
        "estado_control": {
            e: {
                "equipos": int(conteo[e]),
                "porcentaje": round(100 * conteo[e] / total, 2) if total else 0.0,
            }
            for e in ESTADOS_CONTROL
        },
        "suma_estados": int(conteo.sum()),
        "cobertura": {k: int(v) for k, v in universo["cobertura"].value_counts().items()},
        "fuente_inconsistente": int((universo["fuente_consistente"] == "No").sum()),
    }
