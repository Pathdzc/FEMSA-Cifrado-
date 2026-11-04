"""
Reglas v1 sobre el archivo unificado de 25 columnas.
"""
import pandas as pd
from universo import ND, REGION_ESPERADA

SI, NO, SIN_INFO, NO_APLICA = "Sí", "No", "Sin información", "No aplica"
RESULTADOS = [SI, NO, SIN_INFO, NO_APLICA]
SEVERIDADES = ["Alta", "Media", "Baja"]


def c01_disco_cifrado(f):
    v = f["Estado de Cifrado"]
    if v == "Encrypted":
        return SI, "Disco cifrado"
    if v == "Not encrypted":
        return NO, "La fuente reporta el disco sin cifrar"
    return SIN_INFO, "Sin estado de cifrado"


def c02_cifrado_conforme_politica(f):
    if f["Estado de Cifrado"] != "Encrypted":
        return NO_APLICA, "Solo aplica a equipos cifrados"
    d = f["Tecnología de cifrado State"]
    if d == "Success":
        return SI, "Cifrado conforme a la política"
    if d == "No aplica" and f["Sistema Operativo"] == "macOS":
        return SI, "macOS: la fuente no reporta detalle de política"
    if d == ND:
        return SIN_INFO, "Cifrado, pero sin detalle para verificar la política"
    return NO, d


def c03_listo_para_cifrarse(f):
    if f["Estado de Cifrado"] == "Encrypted":
        return NO_APLICA, "Ya está cifrado"
    v = f["Encryption Readiness"]
    if v == "Ready":
        return SI, "Cumple requisitos para cifrarse"
    if v == "Not ready":
        return NO, "No cumple los requisitos para cifrarse"
    return SIN_INFO, "Sin dato de requisitos"


def c04_tpm_compatible(f):
    so = f["Sistema Operativo"]
    if so == "macOS":
        return NO_APLICA, "macOS no usa TPM"
    if so != "Windows":
        return SIN_INFO, "Sistema operativo desconocido"
    v = f["Estado TPM"]
    if v == "TPM 2":
        return SI, "TPM 2"
    if v == "TPM 1.2":
        return NO, "TPM 1.2: versión antigua"
    return SIN_INFO, f"TPM: {v}"


def v01_gestionado_mdm(f):
    v = f["En MDM"]
    if v == "Sí":
        return SI, "Aparece en MDM"
    if v == "No":
        return NO, "No aparece en MDM: no hay fuente automática de su estado de cifrado"
    return SIN_INFO, "Bandera En MDM con valor no reconocido"


def v02_registrado_ad(f):
    if f["Sistema Operativo"] == "macOS":
        return NO_APLICA, "macOS se controla por inventario"
    v = f["En AD"]
    if v == "Sí":
        return SI, "Aparece en AD"
    if v == "No":
        return NO, "Equipo Windows que no aparece en AD"
    return SIN_INFO, "Bandera En AD con valor no reconocido"


def v03_actividad_reciente(f):
    v = f["Banda Recencia"]
    if v in ("0-30 días", "31-90 días"):
        return SI, f"Último logon: {v}"
    if v in ("91-180 días", ">180 días"):
        return NO, f"Último logon: {v}"
    return SIN_INFO, "Sin fecha de último logon"


def v04_usuario_asignado(f):
    v = f["UsuarioID"]
    if v == "No asignado":
        return NO, "Equipo sin usuario responsable"
    if v == ND:
        return SIN_INFO, "Sin dato de usuario"
    return SI, "Tiene usuario asignado"


def q01_equipo_unico(f):
    if f["equipo_repetido"]:
        return NO, "EquipoID repetido en el archivo"
    return SI, "EquipoID único"


def q02_fuente_consistente(f):
    v = f["fuente_consistente"]
    if v == "Sí":
        return SI, "Fuente de Datos coincide con las banderas"
    if v == "No":
        return NO, (
            f"Fuente de Datos = '{f['Fuente de Datos']}' pero En MDM/En AD/En MacOS = "
            f"{f['En MDM']}/{f['En AD']}/{f['En MacOS']}"
        )
    return SIN_INFO, "Fuente de Datos no reconocida"


def q03_so_consistente(f):
    so, ver, tpm = f["Sistema Operativo"], f["Versión SO"], f["Estado TPM"]
    if so not in ("Windows", "macOS"):
        return SIN_INFO, "Sistema operativo desconocido"

    problemas = []
    es_mac_ver = ver.startswith("26.") or ver.lower().startswith("macos")
    es_win_ver = ver.startswith("10.0.") or ver.lower().startswith("windows")

    if so == "Windows" and es_mac_ver:
        problemas.append(f"versión de macOS ({ver})")
    if so == "macOS" and es_win_ver:
        problemas.append(f"versión de Windows ({ver})")
    if so == "macOS" and tpm in ("TPM 2", "TPM 1.2"):
        problemas.append(f"Mac con {tpm}")
    if so == "Windows" and tpm == "No aplica":
        problemas.append("Windows con TPM 'No aplica'")

    if problemas:
        return NO, f"{so} con " + "; ".join(problemas)
    if ver == ND:
        return SIN_INFO, "Sin versión válida (vacía o 'Windows 15')"
    return SI, "SO, versión y TPM consistentes"


def q04_pais_region(f):
    pais, region = f["País"], f["Región"]
    if pais == ND:
        return SIN_INFO, "Sin país"
    esperada = REGION_ESPERADA.get(pais)
    if esperada is None:
        return SIN_INFO, f"País no reconocido: {pais}"
    if region == esperada:
        return SI, "Región consistente"
    return NO, f"{pais} debería ser {esperada}, viene {region}"


def q05_antiguedad_banda(f):
    meses, banda = f["Antigüedad Meses"], f["Banda Antigüedad"]
    try:
        m = int(float(meses))
    except ValueError:
        return SIN_INFO, "Sin antigüedad en meses"

    esperada = "<1 año" if m < 12 else ("1-2 años" if m < 36 else "3-4 años")
    if banda == esperada:
        return SI, "Banda consistente"
    return NO, f"{m} meses debería ser '{esperada}', viene '{banda}'"


def q06_etiqueta_fuente_vs_calculo(f):
    etiqueta = f["Estado de Cumplimiento"]
    if etiqueta != "Compliant":
        return SIN_INFO, f"La fuente no da veredicto ({etiqueta})"
    if f["estado_control"] == "Cumple":
        return SI, "La etiqueta Compliant coincide con nuestro cálculo"
    return NO, f"La fuente dice Compliant, nuestro cálculo: {f['estado_control']}"


REGLAS = [
    {"id": "C01", "categoria": "Cumplimiento", "severidad": "Alta", "funcion": c01_disco_cifrado,
     "nombre": "Disco cifrado"},
    {"id": "C02", "categoria": "Cumplimiento", "severidad": "Media", "funcion": c02_cifrado_conforme_politica,
     "nombre": "Cifrado conforme a la política"},
    {"id": "C03", "categoria": "Cumplimiento", "severidad": "Media", "funcion": c03_listo_para_cifrarse,
     "nombre": "Equipo sin cifrar cumple requisitos para cifrarse"},
    {"id": "C04", "categoria": "Cumplimiento", "severidad": "Media", "funcion": c04_tpm_compatible,
     "nombre": "TPM 2 en Windows"},
    {"id": "V01", "categoria": "Visibilidad", "severidad": "Alta", "funcion": v01_gestionado_mdm,
     "nombre": "Equipo gestionado en MDM"},
    {"id": "V02", "categoria": "Visibilidad", "severidad": "Media", "funcion": v02_registrado_ad,
     "nombre": "Equipo Windows registrado en AD"},
    {"id": "V03", "categoria": "Visibilidad", "severidad": "Baja", "funcion": v03_actividad_reciente,
     "nombre": "Actividad en los últimos 90 días"},
    {"id": "V04", "categoria": "Visibilidad", "severidad": "Baja", "funcion": v04_usuario_asignado,
     "nombre": "Usuario responsable asignado"},
    {"id": "Q01", "categoria": "Calidad de datos", "severidad": "Media", "funcion": q01_equipo_unico,
     "nombre": "EquipoID único"},
    {"id": "Q02", "categoria": "Calidad de datos", "severidad": "Baja", "funcion": q02_fuente_consistente,
     "nombre": "Fuente de Datos consistente con banderas"},
    {"id": "Q03", "categoria": "Calidad de datos", "severidad": "Baja", "funcion": q03_so_consistente,
     "nombre": "SO consistente con versión y TPM"},
    {"id": "Q04", "categoria": "Calidad de datos", "severidad": "Baja", "funcion": q04_pais_region,
     "nombre": "País consistente con región"},
    {"id": "Q05", "categoria": "Calidad de datos", "severidad": "Baja", "funcion": q05_antiguedad_banda,
     "nombre": "Antigüedad consistente con banda"},
    {"id": "Q06", "categoria": "Calidad de datos", "severidad": "Media", "funcion": q06_etiqueta_fuente_vs_calculo,
     "nombre": "Etiqueta Compliant de la fuente coincide con el cálculo"},
]


def evaluar(filas: pd.DataFrame, reglas=REGLAS) -> pd.DataFrame:
    """Una fila por (registro, regla). Nunca se salta un registro."""
    salida = []
    for r in reglas:
        res = filas.apply(r["funcion"], axis=1, result_type="expand")
        res.columns = ["cumple", "detalle"]

        bloque = pd.DataFrame({
            "fila_archivo": filas["fila_archivo"].values,
            "EquipoID": filas["EquipoID"].values,
            "regla": r["id"],
            "nombre_regla": r["nombre"],
            "categoria": r["categoria"],
            "cumple": res["cumple"].values,
            "detalle": res["detalle"].values,
        })
        bloque["severidad"] = bloque["cumple"].map({NO: r["severidad"]})
        salida.append(bloque)

    return pd.concat(salida, ignore_index=True)


def resumen_por_regla(resultados: pd.DataFrame) -> pd.DataFrame:
    tabla = (
        resultados.pivot_table(
            index=["regla", "nombre_regla", "categoria"],
            columns="cumple",
            values="fila_archivo",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(columns=RESULTADOS, fill_value=0)
        .reset_index()
    )
    tabla.columns.name = None
    tabla["evaluados"] = tabla[RESULTADOS].sum(axis=1)

    sev = {r["id"]: r["severidad"] for r in REGLAS}
    tabla["severidad_si_falla"] = tabla["regla"].map(sev)

    orden = {r["id"]: i for i, r in enumerate(REGLAS)}
    return tabla.sort_values("regla", key=lambda s: s.map(orden)).reset_index(drop=True)


def agregar_a_universo(universo: pd.DataFrame, resultados: pd.DataFrame) -> pd.DataFrame:
    """Para cada equipo: cuántas reglas falla, cuáles, y su severidad máxima."""
    fallas = resultados[resultados["cumple"] == NO]
    rango = {s: i for i, s in enumerate(SEVERIDADES)}

    por_equipo = fallas.groupby("EquipoID").agg(
        reglas_fallidas=("regla", "nunique"),
        lista_fallas=("regla", lambda s: ", ".join(sorted(set(s)))),
        severidad_maxima=("severidad", lambda s: min(s, key=lambda x: rango[x])),
    )

    u = universo.merge(por_equipo, left_on="EquipoID", right_index=True, how="left")
    u["reglas_fallidas"] = u["reglas_fallidas"].fillna(0).astype(int)
    u["lista_fallas"] = u["lista_fallas"].fillna("")
    u["severidad_maxima"] = u["severidad_maxima"].fillna("Sin fallas")
    return u


def verificar_cobertura(filas: pd.DataFrame, universo: pd.DataFrame, resultados: pd.DataFrame, reglas=REGLAS):
    """
    Chequeos que prueban que la evaluación fue completa.
    Regresa una lista de (chequeo, ok, detalle).
    """
    n_filas, n_reglas = len(filas), len(reglas)
    esperadas = n_filas * n_reglas
    por_fila = resultados.groupby("fila_archivo")["regla"].nunique()

    return [
        ("Todas las evaluaciones existen", len(resultados) == esperadas,
         f"{len(resultados):,} de {esperadas:,} ({n_filas:,} registros x {n_reglas} reglas)"),
        ("Cada registro tiene todas las reglas",
         bool(len(por_fila) == n_filas and (por_fila == n_reglas).all()), ""),
        ("Sin resultados vacíos ni desconocidos",
         bool(resultados["cumple"].isin(RESULTADOS).all()), ""),
        ("Toda falla tiene severidad",
         bool(resultados.loc[resultados["cumple"] == NO, "severidad"].notna().all()), ""),
        ("Cada equipo está en un solo estado de control",
         bool(universo["EquipoID"].is_unique and universo["estado_control"].notna().all()),
         f"{len(universo):,} equipos únicos"),
        ("Los estados de control suman el universo",
         int(universo["estado_control"].value_counts().sum()) == len(universo), ""),
    ]
