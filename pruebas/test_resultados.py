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
            if col.startswith("tiempo"):     # el tiempo cambia en cada maquina
                continue
            if a[col].dtype == object:
                assert list(a[col]) == list(b[col]), (rel, col)
            else:
                assert np.allclose(a[col], b[col], rtol=1e-9, atol=0), (rel, col)
    pngs = [os.path.join(r, x) for r, _, xs in os.walk(nuevos) for x in xs
            if x.endswith(".png")]
    assert len(pngs) == 34


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
                        "7_panorama", "8_combinaciones", "9_tabla_25"]
    for d in carpetas[1:6]:
        for p in ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"]:
            for ext in ("csv", "png"):
                assert os.path.exists(os.path.join(RES, d, f"{p}.{ext}"))


def test_csv_tienen_sentido():
    for rel in _csvs(RES):
        if (rel.startswith(("7_panorama", "9_tabla_25"))
                or rel.endswith("finales.csv")
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
    assert texto.count("<!-- auto:") == 8           # A.1 a A.8
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


# --------------------------------------------------------------------------
# 3) Tablas del diseno experimental (seccion 3) contra los CSV
# --------------------------------------------------------------------------
def test_diseno_cuadra_con_los_csv():
    from interfaz import diseno
    t = diseno.totales()
    fin = pd.read_csv(os.path.join(RES, "7_panorama", "finales.csv"))
    assert len(fin) == t["barridos"]
    assert set(fin.corrida) == set(range(diseno.N_CORRIDAS))
    assert fin.groupby(["funcion", "parametro", "valor"]).size().eq(
        diseno.N_CORRIDAS).all()
    # cada fila de la tabla 3 (salvo la base) es un valor que si se corrio
    barr, cambia = diseno.filas_barridos()
    col_a_par = {v: k for k, v in diseno.COLUMNAS_PAR.items()}
    for (_, fila), cols in zip(barr.iterrows(), cambia):
        for col in cols:
            par = col_a_par[col]
            assert np.isclose(fin[fin.parametro == par].valor,
                              float(fila[col])).any(), (par, fila[col])
    comb = pd.read_csv(os.path.join(RES, "8_combinaciones", "resumen.csv"))
    assert len(comb) * diseno.N_COMBINACIONES == t["combinaciones"]
    ses = pd.read_csv(os.path.join(RES, "6_sesgo_centro", "resumen.csv"))
    assert len(ses) * diseno.N_CORRIDAS == t["sesgo"]
    ros = pd.read_csv(os.path.join(RES, "6_sesgo_centro", "rosenbrock.csv"))
    assert ros.corridas.sum() == t["rosenbrock"]
    t25 = pd.read_csv(diseno.CSV_TABLA_25)
    assert len(t25) == t["tabla_25"] == 125
    assert t["total"] == 13250


def test_pdf_del_diseno_existe():
    from interfaz import diseno
    assert os.path.exists(diseno.PDF), "correr: python -m interfaz.diseno"


@pytest.mark.parametrize("funcion, par, valor, que, escrito",
                         __import__("interfaz.diseno").diseno.DATOS)
def test_numero_de_que_pasa_en_cada_funcion(funcion, par, valor, que, escrito):
    from interfaz import diseno
    fin = pd.read_csv(diseno.FINALES)
    real = diseno.dato(fin, funcion, par, valor, que)
    assert reporte.coincide(real, escrito), \
        f"{funcion} {par}={valor} {que}: texto {escrito}, CSV {real:.4g}"
    assert escrito in diseno.EXPLICACION[funcion]


def test_beale_siempre_tiene_entre_2_y_7_atoradas():
    from interfaz import diseno
    fin = pd.read_csv(diseno.FINALES)
    t = diseno.tabla_por_valor(fin, "Beale")
    assert t.iloc[:, -1].between(2, 7).all()
    assert t.iloc[:, -1].min() == 2 and t.iloc[:, -1].max() == 7


# --------------------------------------------------------------------------
# 4) Tabla 1 del reporte (diseno de Diana): 25 ejecuciones por funcion
# --------------------------------------------------------------------------
# (n_ballenas, max_iter, a, b, p, seed) de cada fila, copiados de la tabla
TABLA_DIANA = (
    [(30, 200, 2.0, 1.0, 0.5, s) for s in range(5)]
    + [(n, 200, 2.0, 1.0, 0.5, 0) for n in (5, 15, 50, 80, 120)]
    + [(30, t, 2.0, 1.0, 0.5, 0) for t in (50, 100, 300, 500, 1000)]
    + [(30, 200, a, 1.0, 0.5, 0) for a in (0.5, 1.0, 3.0)]
    + [(30, 200, 2.0, 1.0, p, 0) for p in (0.2, 0.8)]
    + [(30, 200, 2.0, b, 0.5, 0) for b in (0.2, 2.5)]
    + [(15, 100, 2.0, 1.0, 0.5, 0), (60, 400, 2.5, 1.0, 0.5, 0),
       (30, 200, 2.0, 1.0, 0.5, 0)])
CLAVES = ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral", "seed"]


def test_tabla_25_es_la_de_diana():
    df = pd.read_csv(os.path.join(RES, "9_tabla_25", "corridas.csv"))
    assert len(df) == 125
    for nom, d in df.groupby("funcion"):
        d = d.sort_values("ejecucion")
        assert list(d.ejecucion) == list(range(1, 26))
        dos = nom in ("Ackley", "Beale")
        for k, (fila, esperado) in enumerate(
                zip(d[CLAVES].itertuples(index=False), TABLA_DIANA), start=1):
            if k == 25 and dos:
                esperado = (50, 300, 1.5, 0.5, 0.3, 0)
            assert np.allclose(tuple(fila), esperado), (nom, k)
        dims = list(d.dim)
        assert dims[:24] == [2 if dos else 10] * 24, nom
        assert dims[24] == (2 if dos else 30), nom


def test_tabla_25_cuadra_con_los_barridos():
    """Filas con la misma configuracion y semilla que un barrido de 30
    corridas dan exactamente lo mismo."""
    t = pd.read_csv(os.path.join(RES, "9_tabla_25", "corridas.csv"))
    f = pd.read_csv(os.path.join(RES, "7_panorama", "finales.csv"))
    casos = {k: ("n_ballenas", 30, k - 1) for k in range(1, 6)}
    casos.update({8: ("n_ballenas", 50, 0), 11: ("max_iter", 50, 0),
                  12: ("max_iter", 100, 0), 14: ("max_iter", 500, 0),
                  17: ("a_inicial", 1.0, 0), 18: ("a_inicial", 3.0, 0),
                  19: ("p_umbral", 0.2, 0), 20: ("p_umbral", 0.8, 0)})
    for nom in t.funcion.unique():
        for k, (par, v, c) in casos.items():
            a = t[(t.funcion == nom) & (t.ejecucion == k)].mejor_f.iloc[0]
            b = f[(f.funcion == nom) & (f.parametro == par) & (f.valor == v)
                  & (f.corrida == c)].mejor_f.iloc[0]
            assert a == b, (nom, k)


def test_nota_de_beale_en_la_tabla_25():
    # notas(): "en Beale la fila 3 se atora en 0.76 y las 1, 2, 4 y 5 no"
    t = pd.read_csv(os.path.join(RES, "9_tabla_25", "corridas.csv"))
    b = t[t.funcion == "Beale"].set_index("ejecucion").mejor_f
    assert reporte.coincide(b[3], "0.76")
    assert all(b[k] < 1e-6 for k in (1, 2, 4, 5))


def test_conteos_de_la_seccion_4_7():
    t = pd.read_csv(os.path.join(RES, "9_tabla_25", "corridas.csv"))
    f = lambda nom: t[t.funcion == nom].mejor_f
    c = reporte.CONTEOS_T25
    assert (f("Rastrigin") == 0).sum() == c["rastrigin_ceros"]
    assert (f("Rosenbrock") > 7.5).sum() == c["rosenbrock_arriba_7.5"]
    assert (f("Rosenbrock") < 0.5).sum() == c["rosenbrock_abajo_0.5"]
    texto = open(REPORTE, encoding="utf-8").read()
    for frase in (f"{c['rastrigin_ceros']} de 25 ejecuciones llegan a 0",
                  f"{c['rosenbrock_arriba_7.5']} de 25 ejecuciones se quedan",
                  f"solo {c['rosenbrock_abajo_0.5']} bajan de 0.5"):
        assert frase in texto, frase
    # "Ackley: todo queda practicamente en 0, menos las de poco esfuerzo"
    ack = t[(t.funcion == "Ackley") & ~t.ejecucion.isin([11, 23])].mejor_f
    assert ack.max() < 1e-14
