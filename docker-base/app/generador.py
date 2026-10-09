import os
import random
import pandas as pd
import numpy as np

def generar_datos_simulados(num_registros=20000):
    np.random.seed(42)
    random.seed(42)

    paises = ["México", "Colombia", "Brasil", "Argentina", "Chile"]
    regiones = ["NORTE", "SUR", "CENTRO", "LATAM"]
    sistemas_operativos = ["Windows 11", "Windows 10", "macOS Sonoma", "macOS Ventura"]
    versiones_so = ["10.0.19045", "10.0.22631", "14.2.1", "13.6.3"]
    tpm_estados = ["Ready", "Not Ready", "Disabled", "N/A"]
    readiness = ["Ready", "Not Ready", "Unknown"]
    estados_cifrado = ["Encrypted", "Unencrypted", "Pending", "Unknown"]
    tecnologias_cifrado = ["BitLocker", "FileVault", "None"]
    cumplimiento_estados = ["Compliant", "Non-Compliant", "Pending"]
    categorias = ["Laptop", "Desktop", "Workstation"]
    clases = ["Standard", "VIP", "Critical"]
    perfiles_privilegio = ["User", "Admin", "Domain Admin"]
    estados_cuenta = ["Active", "Inactive", "Disabled"]
    recencia_bandas = ["0-30 días", "31-60 días", "61-90 días", ">90 días"]
    hardware_estados = ["Good", "Fair", "Deprecated"]
    red_tipos = ["VPN", "Corporate Wi-Fi", "Ethernet", "Public"]
    fuentes = ["Intune", "Jamf", "Active Directory", "SCCM"]

    data = []

    for i in range(1, num_registros + 1):
        so = np.random.choice(sistemas_operativos)
        es_mac = "macOS" in so
        
        cifrado = np.random.choice(estados_cifrado, p=[0.70, 0.18, 0.07, 0.05])
        
        if es_mac:
            tec = "FileVault" if cifrado == "Encrypted" else "None"
            en_mdm = np.random.choice([True, False], p=[0.85, 0.15])
            en_ad = np.random.choice([True, False], p=[0.30, 0.70])
            en_macos = True
        else:
            tec = "BitLocker" if cifrado == "Encrypted" else "None"
            en_mdm = np.random.choice([True, False], p=[0.90, 0.10])
            en_ad = np.random.choice([True, False], p=[0.95, 0.05])
            en_macos = False

        row = {
            "EquipoID": f"EQ-{100000 + i}",
            "UsuarioID": f"USR-{random.randint(10000, 99999)}",
            "País": np.random.choice(paises),
            "Región": np.random.choice(regiones),
            "Sistema Operativo": so,
            "Versión SO": np.random.choice(versiones_so),
            "Estado TPM": "N/A" if es_mac else np.random.choice(tpm_estados, p=[0.8, 0.1, 0.05, 0.05]),
            "Encryption Readiness": np.random.choice(readiness),
            "Estado de Cifrado": cifrado,
            "Tecnología de cifrado State": tec,
            "Estado de Cumplimiento": np.random.choice(cumplimiento_estados),
            "Categoría de Equipo": np.random.choice(categorias),
            "Clase de Equipo": np.random.choice(clases),
            "Perfil de Privilegio": np.random.choice(perfiles_privilegio),
            "Antigüedad Meses": random.randint(1, 60),
            "Banda Antigüedad": np.random.choice(["0-12m", "13-24m", "25-36m", ">36m"]),
            "Estado de Cuenta": np.random.choice(estados_cuenta),
            "Mes Último Logon": f"2026-0{random.randint(1, 9)}",
            "Banda Recencia": np.random.choice(recencia_bandas),
            "Estado Hardware": np.random.choice(hardware_estados),
            "Tipo de Red": np.random.choice(red_tipos),
            "Fuente de Datos": np.random.choice(fuentes),
            "En MDM": en_mdm,
            "En AD": en_ad,
            "En MacOS": en_macos
        }
        data.append(row)

    df = pd.DataFrame(data)

    output_dir = os.getenv("DATOS_DIR", "/app/data")
    raw_path = os.path.join(output_dir, "raw")
    os.makedirs(raw_path, exist_ok=True)

    filepath = os.path.join(raw_path, "dataset_simulado_femsa.csv")
    df.to_csv(filepath, index=False)
    print(f"[+] Dataset simulado de 20,000 registros creado exitosamente en: {filepath}")

if __name__ == "__main__":
    generar_datos_simulados()
