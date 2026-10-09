import re
import yaml
import pandas as pd
from pathlib import Path
import os

REGLAS_PATH = Path(os.environ.get("REGLAS_PATH", "/app/app/reglas.yaml"))


def cargar_reglas():
    with open(REGLAS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalizar_valor(v):
    if pd.isna(v):
        return "No disponible"
    return str(v).strip()


def aplicar_reglas(df: pd.DataFrame):
    reglas = cargar_reglas()
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    for col in df.columns:
        df[col] = df[col].apply(normalizar_valor)

    columnas_faltantes = [c for c in reglas["columnas_esperadas"] if c not in df.columns]

    df["Inventario_Valido"] = df["EquipoID"].apply(
        lambda x: "Sí" if re.match(r"^PC-\d+$", str(x)) else "No"
    )

    duplicados = df["EquipoID"].duplicated(keep=False)
    df.loc[duplicados, "Inventario_Valido"] = "No"

    valores_ok = {v.lower() for v in reglas["valores_cifrado_ok"]}
    valores_no = {v.lower() for v in reglas["valores_cifrado_no"]}
    sin_evidencia = {v.lower() for v in reglas["valores_sin_evidencia"]}

    def evaluar_cifrado(v):
        t = str(v).strip().lower()
        if t in valores_ok:
            return "Cumple"
        if t in valores_no:
            return "No Cumple"
        if t in sin_evidencia:
            return "Sin Evidencia"
        return "Sin Evidencia"

    df["Resultado_Cifrado"] = df["Estado de Cifrado"].apply(evaluar_cifrado)

    def evaluar_universo(v):
        return "Sí" if str(v).strip().lower() == "activa" else "No"

    df["En_Universo_Control"] = df["Estado de Cuenta"].apply(evaluar_universo)

    def calidad_registro(row):
        missing = 0
        for c in reglas["campos_criticos"]:
            if str(row.get(c, "No disponible")).strip() in reglas["valores_sin_evidencia"]:
                missing += 1
        if missing >= 3:
            return "Baja"
        if missing >= 1:
            return "Media"
        return "Alta"

    df["Calidad_Registro"] = df.apply(calidad_registro, axis=1)

    def consistencia_fuentes(row):
        os_name = row.get("Sistema Operativo", "")
        en_macos = row.get("En MacOS", "No")
        if "macos" in str(os_name).lower() and en_macos != "Sí":
            return "Inconsistente"
        return "Consistente"

    df["Cobertura_Fuentes"] = df.apply(consistencia_fuentes, axis=1)

    def dictamen(row):
        if row["Inventario_Valido"] == "No":
            return "No Cumple"
        if row["Resultado_Cifrado"] == "No Cumple":
            return "No Cumple"
        if row["Resultado_Cifrado"] == "Sin Evidencia":
            return "Sin Evidencia"
        return "Cumple"

    df["Dictamen_Final"] = df.apply(dictamen, axis=1)

    def severidad(row):
        if row["Dictamen_Final"] == "No Cumple" and row["En_Universo_Control"] == "Sí":
            return "Crítico"
        if row["Dictamen_Final"] == "Sin Evidencia":
            return "Alto"
        if row["Calidad_Registro"] == "Media" or row["Cobertura_Fuentes"] == "Inconsistente":
            return "Medio"
        return "Bajo"

    df["Severidad"] = df.apply(severidad, axis=1)

    resumen = {
        "total_registros": int(len(df)),
        "columnas_faltantes": columnas_faltantes,
        "inventario_valido": int((df["Inventario_Valido"] == "Sí").sum()),
        "en_universo_control": int((df["En_Universo_Control"] == "Sí").sum()),
        "cumple": int((df["Dictamen_Final"] == "Cumple").sum()),
        "no_cumple": int((df["Dictamen_Final"] == "No Cumple").sum()),
        "sin_evidencia": int((df["Dictamen_Final"] == "Sin Evidencia").sum()),
        "criticos": int((df["Severidad"] == "Crítico").sum()),
        "altos": int((df["Severidad"] == "Alto").sum()),
        "medios": int((df["Severidad"] == "Medio").sum()),
        "bajos": int((df["Severidad"] == "Bajo").sum()),
    }

    incidencias = df[df["Severidad"].isin(["Crítico", "Alto", "Medio"])].copy()

    return df, resumen, incidencias
