"""
Pruebas del universo conciliado y las reglas con casos armados a mano.

Solo usa librerías que ya trae Python (unittest), así no se agrega nada a requirements.txt.

Uso (desde la carpeta raíz del proyecto):
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COLUMNAS
from universo import construir_universo, resumen_universo
from reglas import REGLAS, evaluar, verificar_cobertura, agregar_a_universo


BASE = {
    "EquipoID": "PC-001",
    "UsuarioID": "U-001",
    "País": "México",
    "Región": "Norteamérica",
    "Sistema Operativo": "Windows",
    "Versión SO": "10.0.22631.x",
    "Estado TPM": "TPM 2",
    "Encryption Readiness": "Ready",
    "Estado de Cifrado": "Encrypted",
    "Tecnología de cifrado State": "Success",
    "Estado de Cumplimiento": "Compliant",
    "Categoría de Equipo": "Laptop",
    "Clase de Equipo": "Computer",
    "Perfil de Privilegio": "Administrador",
    "Antigüedad Meses": "13",
    "Banda Antigüedad": "1-2 años",
    "Estado de Cuenta": "Habilitada",
    "Mes Último Logon": "2025-10",
    "Banda Recencia": "0-30 días",
    "Estado Hardware": "Installed",
    "Tipo de Red": "Privada",
    "Fuente de Datos": "MDM+AD",
    "En MDM": "Sí",
    "En AD": "Sí",
    "En MacOS": "No",
}


def equipo(**cambios):
    fila = dict(BASE)
    fila.update(cambios)
    return fila


def armar(*equipos):
    return pd.DataFrame(list(equipos), columns=COLUMNAS).astype(str)


def resultado(resultados, equipo_id, regla):
    r = resultados[(resultados["EquipoID"] == equipo_id) & (resultados["regla"] == regla)]
    return r.iloc[0]["cumple"]


class TestUniverso(unittest.TestCase):
    def setUp(self):
        self.datos = armar(
            equipo(EquipoID="PC-001"),  # sano
            equipo(
                EquipoID="PC-002",
                **{
                    "Estado de Cifrado": "Not encrypted",
                    "Tecnología de cifrado State": "Fixed Drive, not Encrypted",
                },
            ),
            equipo(
                EquipoID="PC-003",
                **{
                    "Estado de Cifrado": "No disponible",
                    "Fuente de Datos": "AD",
                    "En MDM": "No",
                },
            ),
            equipo(
                EquipoID="PC-004",
                **{
                    "Tecnología de cifrado State": "TPM not used for protection of OS volume, but is required by policy",
                },
            ),
            equipo(
                EquipoID="PC-005",
                **{
                    "Sistema Operativo": "macOS",
                    "Versión SO": "macOs 15",
                    "Estado TPM": "No aplica",
                    "Tecnología de cifrado State": "No aplica",
                    "Fuente de Datos": "Iinventario macOS",
                    "En MacOS": "Sí",
                },
            ),
            equipo(
                EquipoID="PC-006",
                **{
                    "Tecnología de cifrado State": "No diponible",
                },
            ),
            equipo(EquipoID="PC-008"),  # PC-007 falta
            equipo(
                EquipoID="PC-008",
                **{
                    "Estado de Cifrado": "Not encrypted",
                },
            ),  # repetido
        )

        self.filas, self.universo = construir_universo(self.datos)
        self.estado = self.universo.set_index("EquipoID")["estado_control"]

    def test_original_no_se_modifica(self):
        antes = self.datos.copy()
        construir_universo(self.datos)
        pd.testing.assert_frame_equal(self.datos, antes)

    def test_estados_de_control(self):
        self.assertEqual(self.estado["PC-001"], "Cumple")
        self.assertEqual(self.estado["PC-002"], "No cifrado")
        self.assertEqual(self.estado["PC-003"], "Sin visibilidad")
        self.assertEqual(self.estado["PC-004"], "Cifrado fuera de política")
        self.assertEqual(self.estado["PC-005"], "Cumple")  # macOS + No aplica
        self.assertEqual(self.estado["PC-006"], "Cifrado, política sin verificar")

    def test_repetido_se_queda_con_el_peor_estado(self):
        self.assertEqual(self.estado["PC-008"], "No cifrado")
        self.assertEqual(len(self.universo), 7)
        self.assertEqual(len(self.filas), 8)

    def test_resumen_suma_100(self):
        res = resumen_universo(self.datos, self.filas, self.universo)
        self.assertEqual(res["suma_estados"], res["equipos_unicos"])
        self.assertAlmostEqual(
            sum(v["porcentaje"] for v in res["estado_control"].values()),
            100,
            delta=0.1,
        )
        self.assertEqual(res["ids_faltantes_en_rango"], 1)  # PC-007
        self.assertEqual(res["registros_repetidos"], 1)

    def test_correccion_de_typo_en_fuente(self):
        fila = self.filas.set_index("EquipoID").loc["PC-005"]
        self.assertEqual(fila["Fuente de Datos"], "Inventario macOS")


class TestReglas(unittest.TestCase):
    def setUp(self):
        self.datos = armar(
            equipo(EquipoID="PC-001"),
            equipo(
                EquipoID="PC-002",
                **{
                    "Estado de Cifrado": "Not encrypted",
                    "Encryption Readiness": "Not ready",
                    "Estado TPM": "TPM 1.2",
                    "Banda Recencia": ">180 días",
                    "UsuarioID": "No asignado",
                },
            ),
            equipo(
                EquipoID="PC-003",
                **{
                    "Fuente de Datos": "MDM+AD",
                    "En AD": "No",
                    "En MDM": "No",
                    "País": "Brasil",
                    "Región": "Norteamérica",
                    "Antigüedad Meses": "36",
                    "Banda Antigüedad": "1-2 años",
                },
            ),
            equipo(
                EquipoID="PC-004",
                **{
                    "Sistema Operativo": "macOS",
                    "Estado TPM": "TPM 2",
                    "Versión SO": "10.0.19045.x",
                    "Estado de Cifrado": "Not encrypted",
                },
            ),
            equipo(
                EquipoID="PC-005",
                **{
                    "Versión SO": "Windows 15",
                    "Antigüedad Meses": "",
                },
            ),
            equipo(EquipoID="PC-005"),
        )

        self.filas, self.universo = construir_universo(self.datos)
        self.res = evaluar(self.filas)

    def test_cobertura_100(self):
        chequeos = verificar_cobertura(self.filas, self.universo, self.res)
        self.assertTrue(all(ok for _, ok, _ in chequeos), chequeos)
        self.assertEqual(len(self.res), len(self.filas) * len(REGLAS))

    def test_equipo_sano_no_falla_nada(self):
        fallas = self.res[
            (self.res["EquipoID"] == "PC-001") & (self.res["cumple"] == "No")
        ]
        self.assertEqual(len(fallas), 0, fallas[["regla", "detalle"]].to_string())

    def test_cumplimiento(self):
        self.assertEqual(resultado(self.res, "PC-002", "C01"), "No")
        self.assertEqual(resultado(self.res, "PC-002", "C02"), "No aplica")
        self.assertEqual(resultado(self.res, "PC-002", "C03"), "No")
        self.assertEqual(resultado(self.res, "PC-002", "C04"), "No")
        self.assertEqual(resultado(self.res, "PC-004", "C04"), "No aplica")

    def test_visibilidad(self):
        self.assertEqual(resultado(self.res, "PC-002", "V03"), "No")
        self.assertEqual(resultado(self.res, "PC-002", "V04"), "No")
        self.assertEqual(resultado(self.res, "PC-003", "V01"), "No")
        self.assertEqual(resultado(self.res, "PC-003", "V02"), "No")
        self.assertEqual(resultado(self.res, "PC-004", "V02"), "No aplica")

    def test_calidad(self):
        self.assertEqual(resultado(self.res, "PC-003", "Q02"), "No")
        self.assertEqual(resultado(self.res, "PC-003", "Q04"), "No")
        self.assertEqual(resultado(self.res, "PC-003", "Q05"), "No")
        self.assertEqual(resultado(self.res, "PC-004", "Q03"), "No")
        self.assertEqual(resultado(self.res, "PC-005", "Q03"), "Sin información")
        self.assertEqual(resultado(self.res, "PC-005", "Q05"), "Sin información")
        self.assertEqual(resultado(self.res, "PC-005", "Q01"), "No")
        self.assertEqual(resultado(self.res, "PC-002", "Q06"), "No")

    def test_severidad_solo_en_fallas(self):
        self.assertTrue(self.res.loc[self.res["cumple"] != "No", "severidad"].isna().all())
        sev = self.res[
            (self.res["EquipoID"] == "PC-002") & (self.res["regla"] == "C01")
        ].iloc[0]["severidad"]
        self.assertEqual(sev, "Alta")

    def test_resumen_por_equipo(self):
        u = agregar_a_universo(self.universo, self.res).set_index("EquipoID")
        self.assertEqual(u.loc["PC-001", "reglas_fallidas"], 0)
        self.assertEqual(u.loc["PC-001", "severidad_maxima"], "Sin fallas")
        self.assertEqual(u.loc["PC-002", "severidad_maxima"], "Alta")


if __name__ == "__main__":
    unittest.main()
