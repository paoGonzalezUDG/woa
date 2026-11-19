"""
El algoritmo WOA: reglas, reproducibilidad, limites y estadistica.

Varias pruebas usan woa_detallado (que anota cada numero al azar) para
recalcular a mano cada movimiento y comparar con lo que hizo el codigo.
"""
import numpy as np
import pytest

from algoritmo.funciones import FUNCIONES
from algoritmo.woa import woa
from interfaz.paso_a_paso import woa_detallado

CONFIGS = [
    {},
    dict(n_ballenas=7, max_iter=40, a_inicial=3.0, b=2.0, p_umbral=0.8),
    dict(n_ballenas=15, max_iter=25, a_inicial=0.5, b=0.0, p_umbral=0.2),
    dict(n_ballenas=2, max_iter=1),
]


def _cfg(nombre):
    c = FUNCIONES[nombre]
    return c["f"], c["lb"], c["ub"]


# --------------------------------------------------------------------------
# Propiedades basicas
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nombre", list(FUNCIONES))
def test_misma_semilla_mismo_resultado(nombre):
    f, lb, ub = _cfg(nombre)
    r1 = woa(f, lb, ub, 2, seed=42)
    r2 = woa(f, lb, ub, 2, seed=42)
    assert np.array_equal(r1["mejor_x"], r2["mejor_x"])
    assert np.array_equal(r1["curva"], r2["curva"])


def test_distinta_semilla_distinto_resultado():
    f, lb, ub = _cfg("Rastrigin")
    xs = {tuple(woa(f, lb, ub, 5, seed=s, max_iter=20)["mejor_x"])
          for s in range(5)}
    assert len(xs) == 5


@pytest.mark.parametrize("nombre", list(FUNCIONES))
@pytest.mark.parametrize("kw", CONFIGS)
def test_propiedades_de_una_corrida(nombre, kw):
    f, lb, ub = _cfg(nombre)
    dim = FUNCIONES[nombre]["dim"] or 4
    r = woa(f, lb, ub, dim, seed=3, guardar_posiciones=True, **kw)
    T = kw.get("max_iter", 200)
    curva = r["curva"]
    assert len(curva) == T + 1
    assert np.all(np.diff(curva) <= 0), "la mejor ballena nunca empeora"
    assert curva[-1] == r["mejor_f"]
    assert f(r["mejor_x"]) == pytest.approx(r["mejor_f"], rel=1e-12, abs=1e-300)
    P = np.array(r["posiciones"])
    assert P.shape == (T + 1, kw.get("n_ballenas", 30), dim)
    assert P.min() >= lb and P.max() <= ub, "ninguna ballena fuera de la zona"
    assert r["reglas"].shape == (T, kw.get("n_ballenas", 30))
    assert set(np.unique(r["reglas"])) <= {0, 1, 2}
    # la presa guardada en cada vuelta es la mejor posicion vista hasta ahi
    for t in (0, T // 2, T):
        assert f(r["presas"][t]) == pytest.approx(curva[t], rel=1e-12,
                                                  abs=1e-300)


def test_guardar_posiciones_no_cambia_el_resultado():
    f, lb, ub = _cfg("Beale")
    a = woa(f, lb, ub, 2, seed=9)
    b = woa(f, lb, ub, 2, seed=9, guardar_posiciones=True)
    assert np.array_equal(a["mejor_x"], b["mejor_x"])


# --------------------------------------------------------------------------
# woa_detallado (pestana Paso a paso) == woa
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nombre", list(FUNCIONES))
@pytest.mark.parametrize("kw", CONFIGS)
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_paso_a_paso_da_lo_mismo_que_woa(nombre, kw, seed):
    f, lb, ub = _cfg(nombre)
    dim = FUNCIONES[nombre]["dim"] or 3
    r1 = woa(f, lb, ub, dim, seed=seed, **kw)
    r2 = woa_detallado(f, lb, ub, dim, seed=seed, **kw)
    assert np.array_equal(r1["mejor_x"], r2["mejor_x"])
    assert r1["mejor_f"] == r2["mejor_f"]


# --------------------------------------------------------------------------
# Cada formula, recalculada a mano con los numeros anotados
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nombre", ["Rastrigin", "Rosenbrock", "Beale"])
@pytest.mark.parametrize("kw", CONFIGS[:3])
def test_cada_movimiento_sigue_su_formula(nombre, kw):
    f, lb, ub = _cfg(nombre)
    a0 = kw.get("a_inicial", 2.0)
    b = kw.get("b", 1.0)
    p_umbral = kw.get("p_umbral", 0.5)
    det = woa_detallado(f, lb, ub, 3 if FUNCIONES[nombre]["dim"] is None
                        else 2, seed=5, **kw)
    T = len(det["iteraciones"])
    vistas = {0: 0, 1: 0, 2: 0}
    for it in det["iteraciones"]:
        t = it["t"]
        a = a0 * (1 - t / T)
        assert it["a"] == pytest.approx(a)
        X_actual = it["X_inicio"].copy()
        for d in it["ballenas"]:
            A, C, l, p = d["A"], d["C"], d["l"], d["p"]
            assert A == pytest.approx(2 * a * d["r1"] - a)
            assert C == pytest.approx(2 * d["r2"])
            assert -1 <= l <= 1 and 0 <= p < 1
            assert np.array_equal(d["x_antes"], X_actual[d["i"]])
            presa, x = it["presa"], d["x_antes"]
            if p < p_umbral and abs(A) < 1:
                assert d["regla"] == 0
                esperado = presa - A * np.abs(C * presa - x)
            elif p < p_umbral:
                assert d["regla"] == 1
                # Xrand es la ballena j TAL COMO ESTABA en ese momento (si ya
                # se movio en esta vuelta, su posicion nueva)
                assert np.array_equal(d["objetivo"], X_actual[d["j"]])
                esperado = d["objetivo"] - A * np.abs(C * d["objetivo"] - x)
            else:
                assert d["regla"] == 2
                esperado = (np.abs(presa - x) * np.exp(b * l)
                            * np.cos(2 * np.pi * l) + presa)
            assert np.allclose(d["x_nuevo"], esperado, rtol=1e-12, atol=1e-12)
            assert np.array_equal(d["x_final"], np.clip(d["x_nuevo"], lb, ub))
            X_actual[d["i"]] = d["x_nuevo"]
            vistas[d["regla"]] += 1
    if kw.get("a_inicial", 2.0) > 1:
        assert all(v > 0 for v in vistas.values()), vistas


# --------------------------------------------------------------------------
# Casos extremos de los parametros
# --------------------------------------------------------------------------
def test_umbral_0_siempre_espiral_y_umbral_1_nunca():
    f, lb, ub = _cfg("Sphere")
    r0 = woa(f, lb, ub, 3, seed=1, p_umbral=0.0, guardar_posiciones=True)
    r1 = woa(f, lb, ub, 3, seed=1, p_umbral=1.0, guardar_posiciones=True)
    assert np.all(r0["reglas"] == 2)
    assert not np.any(r1["reglas"] == 2)


@pytest.mark.parametrize("a0", [0.1, 0.5, 1.0])
def test_con_a_inicial_hasta_1_nunca_hay_busqueda(a0):
    f, lb, ub = _cfg("Ackley")
    r = woa(f, lb, ub, 2, seed=2, a_inicial=a0, guardar_posiciones=True)
    assert not np.any(r["reglas"] == 1)


# --------------------------------------------------------------------------
# Estadistica: la frecuencia de cada regla coincide con la teoria
# --------------------------------------------------------------------------
@pytest.mark.parametrize("p_umbral", [0.2, 0.5, 0.8])
def test_frecuencia_de_espiral_coincide_con_el_umbral(p_umbral):
    f, lb, ub = _cfg("Sphere")
    r = woa(f, lb, ub, 2, seed=0, n_ballenas=50, max_iter=400,
            p_umbral=p_umbral, guardar_posiciones=True)
    frac_espiral = np.mean(r["reglas"] == 2)          # 20,000 movimientos
    assert frac_espiral == pytest.approx(1 - p_umbral, abs=0.015)


@pytest.mark.parametrize("a0", [2.0, 3.0])
def test_frecuencia_de_rodear_vs_buscar_coincide_con_la_teoria(a0):
    # A es uniforme en [-a, a], asi que P(|A| < 1) = min(1, 1/a)
    f, lb, ub = _cfg("Sphere")
    T = 400
    r = woa(f, lb, ub, 2, seed=0, n_ballenas=50, max_iter=T, a_inicial=a0,
            guardar_posiciones=True)
    R = r["reglas"]
    no_espiral = R != 2
    obs = (R == 0).sum() / no_espiral.sum()
    a_t = a0 * (1 - np.arange(T) / T)
    peso = no_espiral.sum(axis=1)
    teoria = np.sum(np.minimum(1, 1 / a_t) * peso) / peso.sum()
    assert obs == pytest.approx(teoria, abs=0.015)


# --------------------------------------------------------------------------
# Que el algoritmo de verdad optimice
# --------------------------------------------------------------------------
def test_sphere_converge_a_casi_cero():
    f, lb, ub = _cfg("Sphere")
    for s in range(5):
        assert woa(f, lb, ub, 10, seed=s)["mejor_f"] < 1e-20


@pytest.mark.parametrize("nombre", list(FUNCIONES))
def test_le_gana_a_la_busqueda_al_azar(nombre):
    # Mismo numero de evaluaciones (30 ballenas x 201 = 6030 puntos)
    f, lb, ub = _cfg(nombre)
    dim = FUNCIONES[nombre]["dim"] or 10
    woa_f, azar_f = [], []
    for s in range(10):
        woa_f.append(woa(f, lb, ub, dim, seed=s)["mejor_f"])
        rng = np.random.default_rng(1000 + s)
        azar_f.append(min(f(x) for x in rng.uniform(lb, ub, (6030, dim))))
    assert np.median(woa_f) < np.median(azar_f)


def test_mas_vueltas_nunca_empeora_la_mediana_en_sphere():
    f, lb, ub = _cfg("Sphere")
    medianas = [np.median([woa(f, lb, ub, 5, seed=s, max_iter=T)["mejor_f"]
                           for s in range(10)]) for T in (20, 50, 100)]
    assert medianas[0] > medianas[1] > medianas[2]


def test_sesgo_al_centro_se_reproduce():
    # Hallazgo del reporte: misma funcion movida de lugar sale mucho peor
    f, lb, ub = _cfg("Sphere")
    movida = lambda x: f(np.asarray(x) - 30.0)
    orig = np.median([woa(f, lb, ub, 10, seed=s)["mejor_f"] for s in range(10)])
    desp = np.median([woa(movida, lb, ub, 10, seed=s)["mejor_f"]
                      for s in range(10)])
    assert orig < 1e-20 and desp > 1e-3
