"""
Los resultados guardados y el reporte:
  1) Regenerar TODOS los experimentos desde cero y comparar con resultados/.
  2) Revisar que los numeros escritos a mano en el reporte coincidan con los
     CSV (redondeados a las cifras que se escribieron).
"""
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from conftest import RAIZ
from interfaz import reporte

RES = os.path.join(RAIZ, "resultados")
REPORTE = os.path.join(RAIZ, "docs", "reporte_referencia.md")


def _csvs(carpeta):
    return sorted(os.path.relpath(os.path.join(r, a), carpeta)
                  for r, _, archs in os.walk(carpeta) for a in archs
                  if a.endswith(".csv"))


# --------------------------------------------------------------------------
# 1) Reproducir todos los experimentos (30 corridas, ~3-4 min)
# --------------------------------------------------------------------------
@pytest.mark.lento
def test_regenerar_experimentos_da_los_mismos_numeros(tmp_path):
    subprocess.run([sys.executable, os.path.join(RAIZ, "experimentos.py")],
                   cwd=tmp_path, check=True, capture_output=True)
    nuevos = os.path.join(tmp_path, "resultados")
    assert _csvs(nuevos) == _csvs(RES), "no se generaron los mismos archivos"
    for rel in _csvs(RES):
        a = pd.read_csv(os.path.join(RES, rel))
        b = pd.read_csv(os.path.join(nuevos, rel))
        assert list(a.columns) == list(b.columns), rel
        for col in a.columns:
            if col == "tiempo_medio_s":      # el tiempo cambia en cada maquina
                continue
            if a[col].dtype == object:
                assert list(a[col]) == list(b[col]), (rel, col)
            else:
                assert np.allclose(a[col], b[col], rtol=1e-9, atol=0), (rel, col)
    pngs = [os.path.join(r, x) for r, _, xs in os.walk(nuevos) for x in xs
            if x.endswith(".png")]
    assert len(pngs) == 33


def test_panorama_cuadra_con_los_csv():
    """finales.csv (una fila por corrida) da las mismas medianas que los CSV
    de cada funcion."""
    df = pd.read_csv(os.path.join(RES, "7_panorama", "finales.csv"))
    assert len(df) == 5 * 17 * 30
    for num, nom in enumerate(["Rastrigin", "Ackley", "Sphere", "Rosenbrock",
                               "Beale"], start=1):
        for par in ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"]:
            tabla = pd.read_csv(os.path.join(RES, f"{num}_{nom}", f"{par}.csv"))
            d = df[(df.funcion == nom) & (df.parametro == par)]
            med = d.groupby("valor")["mejor_f"].median()
            assert np.allclose(med.to_numpy(), tabla["mediana"].to_numpy(),
                               rtol=1e-9, atol=0), (nom, par)


def test_combinaciones_cuadran():
    """resumen.csv completo y sus lugares son reproducibles."""
    import sys
    sys.path.insert(0, RAIZ)
    from experimentos import combinaciones, ordenar_combinaciones
    res = pd.read_csv(os.path.join(RES, "8_combinaciones", "resumen.csv"))
    assert len(res) == 5 * len(combinaciones())
    otra = ordenar_combinaciones(res.drop(columns="lugar"))
    assert list(otra["lugar"]) == list(res["lugar"])
    for nom in res.funcion.unique():
        assert res[res.funcion == nom].lugar.min() == 1


def test_estructura_de_resultados():
    carpetas = sorted(d for d in os.listdir(RES)
                      if os.path.isdir(os.path.join(RES, d)))
    assert carpetas == ["0_base", "1_Rastrigin", "2_Ackley", "3_Sphere",
                        "4_Rosenbrock", "5_Beale", "6_sesgo_centro",
                        "7_panorama", "8_combinaciones"]
    for d in carpetas[1:6]:
        for p in ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"]:
            for ext in ("csv", "png"):
                assert os.path.exists(os.path.join(RES, d, f"{p}.{ext}"))


def test_csv_tienen_sentido():
    for rel in _csvs(RES):
        if (rel.startswith("7_panorama") or rel.endswith("finales.csv")
                or rel.endswith("rosenbrock.csv")):
            continue                          # una fila por corrida, aparte
        df = pd.read_csv(os.path.join(RES, rel))
        assert (df["mejor"] <= df["mediana"]).all(), rel
        assert (df["mediana"] <= df["peor"]).all(), rel
        assert (df["mejor"] <= df["media"]).all(), rel
        assert (df["media"] <= df["peor"]).all(), rel
        assert (df[["media", "mediana", "mejor", "peor"]] >= 0).all().all(), rel


def test_valor_por_defecto_repite_la_fila_base():
    # La fila del valor por defecto en cada barrido = la misma configuracion
    # que 0_base, asi que debe dar exactamente lo mismo.
    base = pd.read_csv(os.path.join(RES, "0_base", "resumen.csv"))
    defecto = {"n_ballenas": 30, "max_iter": 200, "a_inicial": 2.0, "b": 1.0,
               "p_umbral": 0.5}
    for i, fn in enumerate(base.funcion, start=1):
        fila_base = base[base.funcion == fn].iloc[0]
        for par, v in defecto.items():
            df = pd.read_csv(os.path.join(RES, f"{i}_{fn}", f"{par}.csv"))
            fila = df[np.isclose(df[par], v)].iloc[0]
            for col in ["media", "mediana", "mejor", "peor"]:
                assert fila[col] == fila_base[col], (fn, par, col)


# --------------------------------------------------------------------------
# 2) La guia del reporte vs. CSV (la lista de numeros vive en
#    interfaz/reporte.py; experimentos.py la revisa al terminar)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("archivo, filtros, col, escrito", reporte.NUMEROS)
def test_numero_del_reporte_coincide_con_csv(archivo, filtros, col, escrito):
    real = reporte.valor(archivo, filtros, col)
    assert reporte.coincide(real, escrito),         f"reporte dice {escrito}, CSV da {real:.4g}"


def test_numeros_escritos_aparecen_en_el_reporte():
    # Para que la lista no se desactualice si se edita el reporte
    texto = open(REPORTE, encoding="utf-8").read()
    for *_, escrito in reporte.NUMEROS:
        if escrito != "0":
            assert escrito in texto, f"{escrito} ya no aparece en el reporte"


def test_lugares_promedio_del_reporte():
    lp = reporte.lugares_reales()
    for nom, g, v, escrito in reporte.LUGARES:
        assert lp[nom][(g, v)] == escrito, (nom, g, v)


def test_revisar_no_encuentra_nada_desactualizado():
    assert reporte.revisar() == []


def test_anexo_a_esta_al_dia():
    """Las tablas automaticas del reporte son exactamente las de los CSV."""
    texto = open(REPORTE, encoding="utf-8").read()
    nuevo, cambiados = reporte.actualizar_texto(texto)
    assert texto.count("<!-- auto:") == 7
    assert cambiados == [] and nuevo == texto


def test_actualizar_detecta_cambios(tmp_path):
    """Si un CSV cambia, se reescribe su tabla y se avisa del numero."""
    import shutil
    res = tmp_path / "resultados"
    shutil.copytree(RES, res)
    f = res / "0_base" / "resumen.csv"
    df = pd.read_csv(f)
    df.loc[df.funcion == "Rosenbrock", "mediana"] = 1.234
    df.to_csv(f, index=False)
    copia = tmp_path / "reporte.md"
    shutil.copy(REPORTE, copia)
    cambiados, malos = reporte.actualizar_reporte(str(copia), str(res))
    assert cambiados == ["anexo_base"]
    assert "| Rosenbrock | 5.43 | 1.23 |" in copia.read_text(encoding="utf-8")
    assert any("8.56" in m and "1.23" in m for m in malos)


def test_imagenes_del_reporte_existen():
    texto = open(REPORTE, encoding="utf-8").read()
    rutas = re.findall(r"!\[.*?\]\((.+?)\)", texto)
    assert len(rutas) >= 16
    for r in rutas:
        assert os.path.exists(os.path.normpath(
            os.path.join(os.path.dirname(REPORTE), r))), r
