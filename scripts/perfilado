"""
Perfilado de datos.

Revisa columna por columna: celdas vacías, valores que indican falta de dato,
valores distintos, espacios extra, duplicados y algunas consistencias básicas
entre columnas. NO modifica los datos.

Uso (desde la carpeta raíz del proyecto):
    python scripts/perfilado.py

Resultados:
    - salidas/perfilado.md
    - salidas/perfilado_resumen.json

La carpeta salidas/ no se sube al repositorio.
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ARCHIVO_DATOS, COLUMNAS
from cargar_datos import cargar_datos

SALIDA_MD = "salidas/perfilado.md"
SALIDA_JSON = "salidas/perfilado_resumen.json"

# Valores que significan "no hay dato".
# "No aplica" NO está aquí porque sí es información.
SIN_DATO = ["", "No disponible", "No diponible", "Sin dato", "No asignado"]

# Columnas identificadoras: no se listan sus valores en el reporte
COLUMNAS_ID = ["EquipoID", "UsuarioID"]

MAX_VALORES = 30   # si una columna tiene más valores distintos, no se listan

# Valores sospechosos conocidos, detectados en el perfilado inicial
VALORES_SOSPECHOSOS = {
    "Tipo de Red": ["No diponible"],
    "Fuente de Datos": ["Iinventario macOS"],
    "Versión SO": ["Windows 15"],
}

# Mapa esperado de país -> región
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
    "No disponible": "No disponible",
}


def agregar(reporte, texto=""):
    reporte.append(texto)


def limpiar_serie(serie):
    """Convierte a texto y recorta espacios sin modificar el origen."""
    return serie.astype(str).str.strip()


def contar_sin_dato(serie):
    limpios = limpiar_serie(serie)
    vacias = (limpios == "").sum()
    sin_dato = limpios.isin(SIN_DATO[1:]).sum()  # ya contamos "" aparte
    return int(vacias), int(sin_dato)


def porcentaje(parte, total):
    if total == 0:
        return 0.0
    return parte / total * 100


# Cargar datos
datos = cargar_datos(ARCHIVO_DATOS)
total = len(datos)
reporte = []

# Resumen general
agregar(reporte, "# Perfilado de datos")
agregar(reporte)
agregar(reporte, f"- Archivo: `{os.path.basename(ARCHIVO_DATOS)}`")
agregar(reporte, f"- Filas: {total:,}")
agregar(reporte, f"- Columnas encontradas: {len(datos.columns)}")
agregar(reporte, f"- Columnas esperadas: {len(COLUMNAS)}")
agregar(reporte, f"- Se consideran sin dato: celdas vacías y {', '.join(SIN_DATO[1:])}")
agregar(reporte)

# Estructura
faltan = [c for c in COLUMNAS if c not in datos.columns]
sobran = [c for c in datos.columns if c not in COLUMNAS]
orden_correcto = list(datos.columns) == COLUMNAS

agregar(reporte, "## Estructura")
agregar(reporte)
agregar(reporte, f"- Orden de columnas correcto: {'Sí' if orden_correcto else 'No'}")
agregar(reporte, f"- Columnas esperadas que faltan: {', '.join(faltan) if faltan else 'ninguna'}")
agregar(reporte, f"- Columnas que no esperábamos: {', '.join(sobran) if sobran else 'ninguna'}")
agregar(reporte)

# Duplicados
duplicados_equipoid = None
if "EquipoID" in datos.columns:
    duplicados_equipoid = int(datos["EquipoID"].duplicated().sum())

duplicados_fila = int(datos.duplicated().sum())

agregar(reporte, "## Duplicados")
agregar(reporte)
if duplicados_equipoid is not None:
    agregar(reporte, f"- EquipoID repetidos: {duplicados_equipoid:,}")
else:
    agregar(reporte, "- EquipoID repetidos: no se pudo evaluar (no existe la columna)")
agregar(reporte, f"- Filas completamente repetidas: {duplicados_fila:,}")
agregar(reporte)

# Resumen por columna
agregar(reporte, "## Resumen por columna")
agregar(reporte)
agregar(reporte, "| Columna | Vacías | Sin dato | % sin información | Valores distintos | Con espacios extra |")
agregar(reporte, "|---|---:|---:|---:|---:|---:|")

perfil_columnas = []

for columna in datos.columns:
    valores = datos[columna].astype(str)
    limpios = valores.str.strip()

    vacias = int((limpios == "").sum())
    sin_dato = int(limpios.isin(SIN_DATO[1:]).sum())
    sin_info = vacias + sin_dato
    pct_sin_info = porcentaje(sin_info, total)
    distintos = int(limpios.nunique())
    espacios = int((valores != limpios).sum())

    agregar(reporte, f"| {columna} | {vacias:,} | {sin_dato:,} | {pct_sin_info:.1f}% | {distintos:,} | {espacios:,} |")

    perfil_columnas.append({
        "columna": columna,
        "vacias": vacias,
        "sin_dato": sin_dato,
        "porcentaje_sin_informacion": round(pct_sin_info, 2),
        "valores_distintos": distintos,
        "espacios_extra": espacios,
    })

agregar(reporte)

# Valores sospechosos conocidos
agregar(reporte, "## Valores sospechosos conocidos")
agregar(reporte)

hallazgos_sospechosos = []

hubo_sospechosos = False
for columna, sospechosos in VALORES_SOSPECHOSOS.items():
    if columna not in datos.columns:
        continue

    limpios = limpiar_serie(datos[columna])
    for valor in sospechosos:
        cantidad = int((limpios == valor).sum())
        if cantidad > 0:
            hubo_sospechosos = True
            agregar(reporte, f"- {columna}: '{valor}' aparece en {cantidad:,} fila(s)")
            hallazgos_sospechosos.append({
                "columna": columna,
                "valor": valor,
                "filas": cantidad
            })

if not hubo_sospechosos:
    agregar(reporte, "- No se detectaron valores sospechosos conocidos.")
agregar(reporte)

# Consistencia entre columnas
agregar(reporte, "## Consistencia entre columnas")
agregar(reporte)

consistencias = {}

# País vs Región
if "País" in datos.columns and "Región" in datos.columns:
    inconsistentes = 0
    evaluadas = 0

    paises = limpiar_serie(datos["País"])
    regiones = limpiar_serie(datos["Región"])

    for pais, region in zip(paises, regiones):
        if pais in REGION_ESPERADA:
            evaluadas += 1
            if region != REGION_ESPERADA[pais]:
                inconsistentes += 1

    consistencias["pais_region"] = {
        "evaluadas": evaluadas,
        "inconsistentes": inconsistentes
    }
    agregar(reporte, f"- País / Región inconsistentes: {inconsistentes:,} de {evaluadas:,} filas evaluadas")

# Sistema Operativo vs En MacOS
if "Sistema Operativo" in datos.columns and "En MacOS" in datos.columns:
    inconsistentes = 0
    evaluadas = 0

    so = limpiar_serie(datos["Sistema Operativo"])
    en_macos = limpiar_serie(datos["En MacOS"])

    for sistema, bandera in zip(so, en_macos):
        if sistema == "macOS":
            evaluadas += 1
            if bandera != "Sí":
                inconsistentes += 1

    consistencias["so_en_macos"] = {
        "evaluadas": evaluadas,
        "inconsistentes": inconsistentes
    }
    agregar(reporte, f"- macOS con 'En MacOS' distinto de 'Sí': {inconsistentes:,} de {evaluadas:,} filas evaluadas")

# Antigüedad Meses vs Banda Antigüedad
if "Antigüedad Meses" in datos.columns and "Banda Antigüedad" in datos.columns:
    inconsistentes = 0
    evaluadas = 0

    antig = limpiar_serie(datos["Antigüedad Meses"])
    banda = limpiar_serie(datos["Banda Antigüedad"])

    for meses, b in zip(antig, banda):
        if meses == "" or meses in SIN_DATO:
            continue
        try:
            m = int(meses)
        except ValueError:
            continue

        evaluadas += 1

        if m < 12:
            esperada = "<1 año"
        elif m < 36:
            esperada = "1-2 años"
        else:
            esperada = "3-4 años"

        if b != esperada:
            inconsistentes += 1

    consistencias["antiguedad_banda"] = {
        "evaluadas": evaluadas,
        "inconsistentes": inconsistentes
    }
    agregar(reporte, f"- Antigüedad Meses / Banda Antigüedad inconsistentes: {inconsistentes:,} de {evaluadas:,} filas evaluadas")

if not consistencias:
    agregar(reporte, "- No se pudieron evaluar consistencias por falta de columnas.")
agregar(reporte)

# Valores por columna
agregar(reporte, "## Valores por columna")
agregar(reporte)

for columna in datos.columns:
    agregar(reporte, f"### {columna}")
    agregar(reporte)

    if columna in COLUMNAS_ID:
        agregar(reporte, f"Columna identificadora: {datos[columna].nunique():,} valores distintos (no se listan).")
        agregar(reporte)
        continue

    conteo = limpiar_serie(datos[columna]).value_counts(dropna=False)

    if len(conteo) > MAX_VALORES:
        agregar(reporte, f"{len(conteo):,} valores distintos (demasiados para listar).")
        agregar(reporte)
        continue

    agregar(reporte, "| Valor | Filas | % |")
    agregar(reporte, "|---|---:|---:|")
    for valor, filas in conteo.items():
        texto = valor if valor != "" else "(vacío)"
        agregar(reporte, f"| {texto} | {filas:,} | {porcentaje(filas, total):.1f}% |")
    agregar(reporte)

# Resumen JSON
resumen = {
    "archivo": os.path.basename(ARCHIVO_DATOS),
    "filas": total,
    "columnas_encontradas": len(datos.columns),
    "columnas_esperadas": len(COLUMNAS),
    "orden_correcto": orden_correcto,
    "faltan": faltan,
    "sobran": sobran,
    "duplicados_equipoid": duplicados_equipoid,
    "duplicados_fila": duplicados_fila,
    "sin_dato_definidos": SIN_DATO,
    "columnas": perfil_columnas,
    "valores_sospechosos": hallazgos_sospechosos,
    "consistencias": consistencias,
}

# Guardar salidas
os.makedirs(os.path.dirname(SALIDA_MD), exist_ok=True)

with open(SALIDA_MD, "w", encoding="utf-8") as archivo:
    archivo.write("\n".join(reporte))

with open(SALIDA_JSON, "w", encoding="utf-8") as archivo:
    json.dump(resumen, archivo, ensure_ascii=False, indent=2)

print(f"Listo: perfilado de {total:,} filas guardado en {SALIDA_MD}")
print(f"Resumen JSON guardado en {SALIDA_JSON}")
