"""
Los resultados guardados y el reporte:
  1) Regenerar TODOS los experimentos desde cero y comparar con resultados/.
  2) Revisar que los numeros escritos a mano en el reporte coincidan con los
     CSV (redondeados a las cifras que se escribieron).
"""
import math
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from conftest import RAIZ

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
    assert len(pngs) == 30


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
    """resumen.csv cuadra con finales.csv y sus lugares son reproducibles."""
    import sys
    sys.path.insert(0, RAIZ)
    from experimentos import (PARAMS_DEFAULT, combinaciones,
                              ordenar_combinaciones)
    car = os.path.join(RES, "8_combinaciones")
    res = pd.read_csv(os.path.join(car, "resumen.csv"))
    cru = pd.read_csv(os.path.join(car, "finales.csv"))
    claves = list(PARAMS_DEFAULT)
    assert len(res) == 5 * len(combinaciones())
    assert len(cru) == len(res) * 25
    med = cru.groupby(["funcion"] + claves)["mejor_f"].median()
    r = res.set_index(["funcion"] + claves)["mediana"]
    assert np.allclose(med.loc[r.index].to_numpy(), r.to_numpy(),
                       rtol=1e-9, atol=0)
    # ordenar otra vez da los mismos lugares
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
        if rel.startswith("7_panorama") or rel.endswith("finales.csv"):
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
# 2) Numeros escritos a mano en el reporte vs. CSV
# --------------------------------------------------------------------------
def _valor(carpeta, archivo, filtro_col, filtro_val, col):
    df = pd.read_csv(os.path.join(RES, carpeta, archivo))
    if isinstance(filtro_val, str):
        fila = df[df[filtro_col] == filtro_val]
    else:
        fila = df[np.isclose(df[filtro_col], filtro_val)]
    assert len(fila) == 1, (carpeta, archivo, filtro_val)
    return float(fila.iloc[0][col])


def _coincide(real, escrito):
    """True si 'escrito' es 'real' redondeado a las cifras que tiene."""
    v = float(escrito)
    if v == 0:
        return real == 0
    mant = escrito.lower().split("e")[0].replace("-", "").replace(".", "")
    k = len(mant.lstrip("0"))                      # cifras significativas
    unidad = 10 ** (math.floor(math.log10(abs(v))) - k + 1)
    return abs(real - v) <= 0.5 * unidad * 1.0001


B, S = "0_base", "6_sesgo_centro"
AFIRMACIONES = [
    # (carpeta, archivo, columna_filtro, valor_filtro, columna, escrito)
    (B, "resumen.csv", "funcion", "Rastrigin", "mediana", "0"),
    (B, "resumen.csv", "funcion", "Rastrigin", "media", "1.9e-15"),
    (B, "resumen.csv", "funcion", "Rastrigin", "peor", "2.8e-14"),
    (B, "resumen.csv", "funcion", "Ackley", "mediana", "3.6e-15"),
    (B, "resumen.csv", "funcion", "Ackley", "media", "3.9e-15"),
    (B, "resumen.csv", "funcion", "Ackley", "peor", "1.4e-14"),
    (B, "resumen.csv", "funcion", "Sphere", "mediana", "1.8e-34"),
    (B, "resumen.csv", "funcion", "Sphere", "media", "9.9e-32"),
    (B, "resumen.csv", "funcion", "Sphere", "peor", "2.7e-30"),
    (B, "resumen.csv", "funcion", "Rosenbrock", "mediana", "8.56"),
    (B, "resumen.csv", "funcion", "Rosenbrock", "media", "5.43"),
    (B, "resumen.csv", "funcion", "Rosenbrock", "peor", "8.90"),
    (B, "resumen.csv", "funcion", "Beale", "mediana", "8.8e-9"),
    (B, "resumen.csv", "funcion", "Beale", "media", "0.10"),
    (B, "resumen.csv", "funcion", "Beale", "peor", "0.76"),
    # max_iter
    ("3_Sphere", "max_iter.csv", "max_iter", 50, "mediana", "4.6e-6"),
    ("3_Sphere", "max_iter.csv", "max_iter", 100, "mediana", "1.9e-16"),
    ("3_Sphere", "max_iter.csv", "max_iter", 500, "mediana", "1.4e-89"),
    ("1_Rastrigin", "max_iter.csv", "max_iter", 50, "peor", "59.7"),
    ("1_Rastrigin", "max_iter.csv", "max_iter", 100, "peor", "49.8"),
    ("1_Rastrigin", "max_iter.csv", "max_iter", 500, "peor", "0"),
    ("4_Rosenbrock", "max_iter.csv", "max_iter", 50, "mediana", "8.90"),
    ("4_Rosenbrock", "max_iter.csv", "max_iter", 100, "mediana", "8.72"),
    ("4_Rosenbrock", "max_iter.csv", "max_iter", 500, "mediana", "0.40"),
    # n_ballenas
    ("4_Rosenbrock", "n_ballenas.csv", "n_ballenas", 10, "mediana", "8.90"),
    ("4_Rosenbrock", "n_ballenas.csv", "n_ballenas", 50, "mediana", "0.91"),
    ("4_Rosenbrock", "n_ballenas.csv", "n_ballenas", 100, "mediana", "0.12"),
    ("3_Sphere", "n_ballenas.csv", "n_ballenas", 10, "mediana", "8.1e-24"),
    ("3_Sphere", "n_ballenas.csv", "n_ballenas", 50, "mediana", "6.0e-39"),
    ("3_Sphere", "n_ballenas.csv", "n_ballenas", 100, "mediana", "7.3e-45"),
] + [("5_Beale", "n_ballenas.csv", "n_ballenas", n, "peor", "0.76")
     for n in (10, 30, 50, 100)] + [
    # a_inicial
    ("4_Rosenbrock", "a_inicial.csv", "a_inicial", 1.0, "mediana", "8.92"),
    ("4_Rosenbrock", "a_inicial.csv", "a_inicial", 3.0, "mediana", "0.09"),
    ("3_Sphere", "a_inicial.csv", "a_inicial", 1.0, "mediana", "2.1e-36"),
    ("3_Sphere", "a_inicial.csv", "a_inicial", 3.0, "mediana", "4.7e-26"),
    ("1_Rastrigin", "a_inicial.csv", "a_inicial", 1.0, "peor", "25.4"),
    # p_umbral
    ("4_Rosenbrock", "p_umbral.csv", "p_umbral", 0.2, "mediana", "8.43"),
    ("4_Rosenbrock", "p_umbral.csv", "p_umbral", 0.8, "mediana", "0.26"),
    ("1_Rastrigin", "p_umbral.csv", "p_umbral", 0.2, "peor", "33.1"),
    # b
    ("4_Rosenbrock", "b.csv", "b", 2.0, "mediana", "0.66"),
]
SESGO = [("Sphere", "original", "1.8e-34"), ("Sphere", "desplazada", "2.34"),
         ("Rastrigin", "original", "0"), ("Rastrigin", "desplazada", "9.84"),
         ("Ackley", "original", "3.6e-15"), ("Ackley", "desplazada", "0.028")]


@pytest.mark.parametrize("carpeta, archivo, fcol, fval, col, escrito",
                         AFIRMACIONES)
def test_numero_del_reporte_coincide_con_csv(carpeta, archivo, fcol, fval,
                                             col, escrito):
    real = _valor(carpeta, archivo, fcol, fval, col)
    assert _coincide(real, escrito), f"reporte dice {escrito}, CSV da {real:.4g}"


@pytest.mark.parametrize("funcion, caso, escrito", SESGO)
def test_numero_de_sesgo_del_reporte(funcion, caso, escrito):
    df = pd.read_csv(os.path.join(RES, S, "resumen.csv"))
    real = float(df[(df.funcion == funcion) & (df.caso == caso)].iloc[0].mediana)
    assert _coincide(real, escrito), f"reporte dice {escrito}, CSV da {real:.4g}"


def test_numeros_escritos_aparecen_en_el_reporte():
    # Para que la lista de arriba no se desactualice si se edita el reporte
    texto = open(REPORTE, encoding="utf-8").read()
    for a in AFIRMACIONES:
        if a[-1] != "0":
            assert a[-1] in texto, f"{a[-1]} ya no aparece en el reporte"


def test_imagenes_del_reporte_existen():
    texto = open(REPORTE, encoding="utf-8").read()
    rutas = re.findall(r"!\[.*?\]\((.+?)\)", texto)
    assert len(rutas) >= 11 + 25
    for r in rutas:
        assert os.path.exists(os.path.normpath(
            os.path.join(os.path.dirname(REPORTE), r))), r


def test_anexo_a_coincide_con_csv():
    # Cada fila del Anexo A se genero de los CSV; revisamos la de Rosenbrock
    texto = open(REPORTE, encoding="utf-8").read()
    df = pd.read_csv(os.path.join(RES, "4_Rosenbrock", "a_inicial.csv"))
    for _, fila in df.iterrows():
        mediana = f"{fila.mediana:.3g}" if fila.mediana >= 0.01 else \
            f"{fila.mediana:.2e}"
        assert f"| `a` inicial | " in texto and mediana in texto
