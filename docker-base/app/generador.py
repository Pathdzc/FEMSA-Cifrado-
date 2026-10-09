import random
from pathlib import Path
import pandas as pd
import os

SALIDA = Path(os.environ.get("SALIDA_DIR", "/app/resultados"))
random.seed(42)


def generar_dataset(n=5000):
    paises = ["México", "Brasil", "Colombia", "Argentina", "Chile"]
    regiones = ["Norte", "Sur", "Centro"]
    so_list = ["Windows 10", "Windows 11", "macOS Ventura", "macOS Sonoma"]
    versiones = ["22H2", "23H2", "13", "14"]
    tpm = ["Habilitado", "Deshabilitado", "No disponible"]
    readiness = ["Listo", "No listo", "No disponible"]
    estado_cifrado = ["Activo", "No cifrado", "No disponible"]
    tecnologia = ["BitLocker", "FileVault", "No disponible"]
    cumplimiento = ["Cumple", "No cumple", "No disponible"]
    categoria = ["Laptop", "Desktop", "No disponible"]
    clase = ["Corporativo", "Operativo", "Ejecutivo"]
    perfil = ["Estándar", "Privilegiado", "No disponible"]
    banda_antig = ["0-12", "13-24", "25-36", "No disponible"]
    estado_cuenta = ["Activa", "Inactiva"]
    ultimo_logon = ["2026-10", "2026-09", "2026-08", "2026-07", "No disponible"]
    banda_recencia = ["0-30 días", "31-60 días", "61-90 días", "No disponible"]
    estado_hw = ["Vigente", "Obsoleto", "No disponible"]
    tipo_red = ["Corporativa", "Remota", "No disponible"]
    fuente = ["MDM", "AD", "MacOS", "Consolidado"]
    si_no = ["Sí", "No"]

    rows = []

    for i in range(1, n + 1):
        os_name = random.choice(so_list)
        rows.append({
            "EquipoID": f"PC-{i}",
            "UsuarioID": random.choice([f"U-{random.randint(1000,9999)}", "No asignado"]),
            "País": random.choice(paises),
            "Región": random.choice(regiones),
            "Sistema Operativo": os_name,
            "Versión SO": random.choice(versiones),
            "Estado TPM": random.choices(tpm, weights=[60, 15, 25])[0],
            "Encryption Readiness": random.choices(readiness, weights=[60, 20, 20])[0],
            "Estado de Cifrado": random.choices(estado_cifrado, weights=[65, 20, 15])[0],
            "Tecnología de cifrado State": "FileVault" if "macOS" in os_name else random.choice(tecnologia),
            "Estado de Cumplimiento": random.choices(cumplimiento, weights=[60, 25, 15])[0],
            "Categoría de Equipo": random.choice(categoria),
            "Clase de Equipo": random.choice(clase),
            "Perfil de Privilegio": random.choice(perfil),
            "Antigüedad Meses": random.choice([random.randint(1, 48), None, None]),
            "Banda Antigüedad": random.choice(banda_antig),
            "Estado de Cuenta": random.choices(estado_cuenta, weights=[85, 15])[0],
            "Mes Último Logon": random.choice(ultimo_logon),
            "Banda Recencia": random.choice(banda_recencia),
            "Estado Hardware": random.choice(estado_hw),
            "Tipo de Red": random.choice(tipo_red),
            "Fuente de Datos": random.choice(fuente),
            "En MDM": random.choice(si_no),
            "En AD": random.choice(si_no),
            "En MacOS": "Sí" if "macOS" in os_name and random.random() > 0.2 else "No",
        })

    df = pd.DataFrame(rows)

    # anomalías controladas
    for idx in random.sample(range(len(df)), 50):
        df.loc[idx, "EquipoID"] = "INVALIDO"

    for idx in random.sample(range(len(df)), 120):
        df.loc[idx, "Estado de Cifrado"] = "No disponible"

    for idx in random.sample(range(len(df)), 100):
        df.loc[idx, "Estado TPM"] = "No disponible"

    return df


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    df = generar_dataset(5000)
    archivo = SALIDA / "datos_simulados.csv"
    df.to_csv(archivo, index=False, encoding="utf-8-sig")
    print(f"Datos simulados generados en: {archivo}")
