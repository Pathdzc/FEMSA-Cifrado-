"""
Arma el universo conciliado y evalúa TODAS las reglas sobre TODOS los equipos.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ARCHIVO_DATOS, COLUMNAS, RUTA_BD
from cargar_datos import cargar_datos
from universo import construir_universo, resumen_universo, ESTADOS_CONTROL
from reglas import REGLAS, evaluar, resumen_por_regla, agregar_a_universo, verificar_cobertura, RESULTADOS

CARPETA_SALIDAS = "salidas"

COLUMNAS_BD = [
    "equipo_id", "usuario_id", "pais", "region", "sistema_operativo", "version_so",
    "estado_tpm", "encryption_readiness", "estado_cifrado", "detalle_cifrado",
    "estado_cumplimiento", "categoria_equipo", "clase_equipo", "perfil_privilegio",
    "antiguedad_meses", "banda_antiguedad", "estado_cuenta", "mes_ultimo_logon",
    "banda_recencia", "estado_hardware", "tipo_red", "fuente_datos", "en_mdm", "en_ad", "en_macos",
]


def hash_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def guardar_en_bd(datos, resultados, ruta_archivo):
    """Guarda carga + equipos + evaluaciones."""
    if not os.path.exists(RUTA_BD):
        raise SystemExit(f"No existe la base {RUTA_BD}. Corre primero: python scripts/crear_bd.py")

    con = sqlite3.connect(RUTA_BD)
    con.execute("PRAGMA foreign_keys = ON")

    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        h_archivo = hash_archivo(ruta_archivo)

        fila_anterior = con.execute("SELECT hash_carga FROM cargas ORDER BY id DESC LIMIT 1").fetchone()
        h_anterior = fila_anterior[0] if fila_anterior else None

        h_carga = hashlib.sha256(f"{h_anterior}|{h_archivo}|{fecha}|{len(datos)}".encode()).hexdigest()

        cur = con.execute(
            "INSERT INTO cargas (fecha_carga, nombre_archivo, hash_archivo, total_filas, hash_anterior, hash_carga) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (fecha, os.path.basename(ruta_archivo), h_archivo, len(datos), h_anterior, h_carga),
        )
        carga_id = cur.lastrowid

        marcadores = ", ".join("?" * (len(COLUMNAS_BD) + 1))
        sql = f"INSERT INTO equipos (carga_id, {', '.join(COLUMNAS_BD)}) VALUES ({marcadores})"

        ids_bd = []
        for _, fila in datos[COLUMNAS].iterrows():
            ids_bd.append(con.execute(sql, (carga_id, *fila.tolist())).lastrowid)

        fila_a_id = {i + 1: id_bd for i, id_bd in enumerate(ids_bd)}

        con.executemany(
            "INSERT INTO resultados (carga_id, equipo_ref, regla, cumple, detalle, severidad) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (carga_id, fila_a_id[int(f)], r, c, d, s if isinstance(s, str) else None)
                for f, r, c, d, s in resultados[["fila_archivo", "regla", "cumple", "detalle", "severidad"]]
                .itertuples(index=False)
            ],
        )

        con.commit()
        return carga_id

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def escribir_md(ruta, archivo, res_u, tabla_reglas, cobertura, segundos):
    total = res_u["equipos_unicos"]
    L = [
        "# Universo conciliado y reglas v1",
        "",
        f"- Archivo: `{archivo}`",
        f"- Registros en el archivo: {res_u['registros_en_archivo']:,}",
        f"- Equipos únicos (universo): {total:,}",
        f"- Registros repetidos: {res_u['registros_repetidos']:,}",
        f"- Rango de EquipoID: {res_u['rango_ids']} · IDs faltantes en el rango: {res_u['ids_faltantes_en_rango']:,}",
        f"- Tiempo de evaluación: {segundos:.1f} s",
        "",
        "## Estado de control (cada equipo en un solo estado)",
        "",
        "| Estado | Equipos | % del universo |",
        "|---|---:|---:|",
    ]

    for e in ESTADOS_CONTROL:
        v = res_u["estado_control"][e]
        L.append(f"| {e} | {v['equipos']:,} | {v['porcentaje']:.1f}% |")

    L += [
        f"| **Total** | **{res_u['suma_estados']:,}** | **100%** |",
        "",
        "## Cobertura por fuente",
        "",
        "| Fuentes donde aparece | Equipos |",
        "|---|---:|",
    ]

    for k, v in res_u["cobertura"].items():
        L.append(f"| {k} | {v:,} |")

    L += [
        "",
        f"Equipos donde 'Fuente de Datos' no coincide con las banderas: {res_u['fuente_inconsistente']:,}",
        "",
        "## Resultado por regla",
        "",
        "| Regla | Nombre | Sí | No | Sin información | No aplica | Evaluados | Severidad si falla |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]

    for _, r in tabla_reglas.iterrows():
        L.append(
            f"| {r['regla']} | {r['nombre_regla']} | {r['Sí']:,} | {r['No']:,} | "
            f"{r['Sin información']:,} | {r['No aplica']:,} | {r['evaluados']:,} | {r['severidad_si_falla']} |"
        )

    L += ["", "## Verificación de cobertura (100%)", ""]

    for chequeo, ok, detalle in cobertura:
        L.append(f"- [{'OK' if ok else 'FALLA'}] {chequeo}{': ' + detalle if detalle else ''}")

    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Universo conciliado + reglas v1")
    parser.add_argument("--bd", action="store_true", help="guardar la carga en la base de datos")
    args = parser.parse_args()

    inicio = time.perf_counter()
    datos = cargar_datos(ARCHIVO_DATOS)

    faltan = [c for c in COLUMNAS if c not in datos.columns]
    if faltan:
        raise SystemExit(f"Al archivo le faltan columnas: {faltan}. Corre primero scripts/perfilado.py")

    filas, universo = construir_universo(datos)
    resultados = evaluar(filas)
    universo = agregar_a_universo(universo, resultados)
    tabla_reglas = resumen_por_regla(resultados)
    cobertura = verificar_cobertura(filas, universo, resultados)
    res_u = resumen_universo(datos, filas, universo)
    segundos = time.perf_counter() - inicio

    os.makedirs(CARPETA_SALIDAS, exist_ok=True)

    universo.to_csv(f"{CARPETA_SALIDAS}/universo_conciliado.csv", index=False, encoding="utf-8-sig")
    resultados.to_csv(f"{CARPETA_SALIDAS}/resultados_reglas.csv", index=False, encoding="utf-8-sig")

    archivo = os.path.basename(ARCHIVO_DATOS)
    escribir_md(f"{CARPETA_SALIDAS}/resumen_reglas.md", archivo, res_u, tabla_reglas, cobertura, segundos)

    resumen_json = {
        "archivo": archivo,
        "universo": res_u,
        "reglas": [
            {**{k: (int(v) if k in RESULTADOS + ["evaluados"] else v) for k, v in fila.items()}}
            for fila in tabla_reglas.to_dict("records")
        ],
        "cobertura": [{"chequeo": c, "ok": bool(o), "detalle": d} for c, o, d in cobertura],
        "segundos": round(segundos, 2),
    }

    with open(f"{CARPETA_SALIDAS}/resumen_reglas.json", "w", encoding="utf-8") as f:
        json.dump(resumen_json, f, ensure_ascii=False, indent=2)

    print(
        f"Universo: {res_u['equipos_unicos']:,} equipos · {len(REGLAS)} reglas · "
        f"{len(resultados):,} evaluaciones · {segundos:.1f} s"
    )

    for e in ESTADOS_CONTROL:
        v = res_u["estado_control"][e]
        print(f"  {e:33s} {v['equipos']:6,}  {v['porcentaje']:5.1f}%")

    print("Cobertura:")
    for chequeo, ok, detalle in cobertura:
        print(f"  [{'OK' if ok else 'FALLA'}] {chequeo}{' · ' + detalle if detalle else ''}")

    print(f"Archivos en {CARPETA_SALIDAS}/")

    if args.bd:
        carga_id = guardar_en_bd(datos, resultados, ARCHIVO_DATOS)
        print(f"Guardado en {RUTA_BD} como carga #{carga_id}")

    if not all(ok for _, ok, _ in cobertura):
        sys.exit(1)


if __name__ == "__main__":
    main()
