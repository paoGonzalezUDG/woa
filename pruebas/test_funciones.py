"""Las 5 funciones de prueba: valores conocidos y que el minimo sea el minimo."""
import math

import numpy as np
import pytest

from algoritmo.funciones import (FUNCIONES, ackley, beale, rastrigin,
                                 rosenbrock, sphere)


# Valores calculados a mano (ver comentario de cada uno)
@pytest.mark.parametrize("f, x, esperado", [
    (sphere, [3, 4], 25.0),                    # 9 + 16
    (sphere, [0] * 10, 0.0),
    (rastrigin, [0, 0], 0.0),
    (rastrigin, [1, 1], 2.0),                  # 20 + 2*(1 - 10)
    (rastrigin, [0.5, 0.5], 40.5),             # 20 + 2*(0.25 + 10)
    (ackley, [1, 1], 20 - 20 * math.exp(-0.2)),  # el termino coseno se cancela con e
    (rosenbrock, [1, 1, 1], 0.0),
    (rosenbrock, [0, 0], 1.0),                 # 100*0 + (1-0)^2
    (rosenbrock, [-1, 1], 4.0),                # 100*0 + (1+1)^2
    (beale, [3, 0.5], 0.0),
    (beale, [0, 0], 14.203125),                # 1.5^2 + 2.25^2 + 2.625^2
])
def test_valores_conocidos(f, x, esperado):
    assert f(np.array(x, dtype=float)) == pytest.approx(esperado, abs=1e-12)


def test_ackley_en_el_origen_es_casi_cero():
    # Por redondeo da ~4e-16, no exactamente 0
    assert abs(ackley(np.zeros(2))) < 1e-15


@pytest.mark.parametrize("nombre", list(FUNCIONES))
def test_optimo_declarado_vale_cero(nombre):
    cfg = FUNCIONES[nombre]
    for n in ([2, 5, 10] if cfg["dim"] is None else [cfg["dim"]]):
        x = cfg["optimo_x"](n)
        assert cfg["f"](x) == pytest.approx(cfg["optimo_f"], abs=1e-12)
        assert np.all(x >= cfg["lb"]) and np.all(x <= cfg["ub"])


@pytest.mark.parametrize("nombre", list(FUNCIONES))
def test_ningun_punto_al_azar_es_menor_que_el_optimo(nombre):
    cfg = FUNCIONES[nombre]
    rng = np.random.default_rng(123)
    n = cfg["dim"] or 5
    puntos = rng.uniform(cfg["lb"], cfg["ub"], size=(20_000, n))
    valores = np.array([cfg["f"](p) for p in puntos])
    assert valores.min() >= cfg["optimo_f"] - 1e-12


@pytest.mark.parametrize("nombre", list(FUNCIONES))
def test_funciones_nunca_son_negativas(nombre):
    # La escala log de la simulacion 3D (log10(1 + f)) depende de esto
    cfg = FUNCIONES[nombre]
    rng = np.random.default_rng(7)
    n = cfg["dim"] or 3
    X = rng.uniform(cfg["lb"] * 3, cfg["ub"] * 3, size=(5_000, n))
    assert min(cfg["f"](x) for x in X) >= -1e-12


def test_rastrigin_es_simetrica():
    rng = np.random.default_rng(1)
    for _ in range(100):
        x = rng.uniform(-5, 5, 4)
        assert rastrigin(x) == pytest.approx(rastrigin(-x))
