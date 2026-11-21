"""
Pruebas de humo de la app (Streamlit AppTest, sin navegador).

Revisan que cada pestana cargue sin errores con las 5 funciones, con ajustes
extremos y con entradas invalidas, y que los numeros que muestra la app
coincidan con el algoritmo.
"""
import base64
import json
import os

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from algoritmo.funciones import FUNCIONES
from algoritmo.woa import woa
from conftest import RAIZ
from interfaz.paso_a_paso import woa_detallado

APP = os.path.join(RAIZ, "app.py")
FUNC = list(FUNCIONES)


def nueva_app():
    at = AppTest.from_file(APP, default_timeout=600)
    at.run()
    _sin_errores(at)
    # Vista estatica en Comparar y Sesgo: generar GIFs en cada prueba es lento
    for r in at.radio:
        if r.key in ("modo_c", "modo_s"):
            r.set_value("Pausar en un momento")
    return at.run()


def _sin_errores(at):
    assert not at.exception, [e.value for e in at.exception]


def _textos(elementos):
    return [str(e.value) for e in elementos]


def _arr(v):
    """Plotly 6 manda los arreglos como {'dtype', 'bdata' (base64), 'shape'}."""
    if isinstance(v, dict) and "bdata" in v:
        a = np.frombuffer(base64.b64decode(v["bdata"]), dtype=v["dtype"])
        return a.reshape([int(s) for s in str(v["shape"]).split(",")]) \
            if "shape" in v else a
    return np.array(v, dtype=float)


def _spec_3d(at):
    """La Simulacion 3D se muestra con st.iframe (HTML con plotly.js y JS
    propio). Saca data, layout y frames del HTML para revisarlos."""
    iframes = at.get("iframe")
    assert len(iframes) == 1
    html = iframes[0].proto.srcdoc
    assert "plotly_relayouting" in html          # el JS para girar al reproducir
    i = html.rindex("var fig = ") + len("var fig = ")
    spec, _ = json.JSONDecoder().raw_decode(html, i)
    return dict(data=spec["data"], layout=spec["layout"],
                frames=spec["frames"])


def boton(at, etiqueta, key=None):
    for b in at.button:
        if b.label == etiqueta and (key is None or b.key == key):
            return b
    raise AssertionError(f"no hay boton {etiqueta!r}")


def elegir_funcion(at, nombre):
    at.sidebar.selectbox[0].set_value(nombre)
    return at.run()


@pytest.fixture(scope="module")
def app():
    return nueva_app()


# --------------------------------------------------------------------------
def test_carga_inicial():
    at = AppTest.from_file(APP, default_timeout=600).run()   # con animaciones
    _sin_errores(at)
    assert not at.warning, _textos(at.warning)
    assert [t.label for t in at.tabs] == [
        "Empieza aquí", "Una corrida", "Simulación 3D", "Paso a paso",
        "Comparar", "Muchas corridas", "Sesgo al centro", "Resultados",
        "Reporte"]


@pytest.mark.parametrize("nombre", FUNC)
def test_una_corrida_muestra_lo_mismo_que_el_algoritmo(app, nombre):
    at = elegir_funcion(app, nombre)
    boton(at, "Correr", key=None).click().run()
    _sin_errores(at)
    cfg = FUNCIONES[nombre]
    dim = cfg["dim"] or cfg["dim_default"]
    r = woa(cfg["f"], cfg["lb"], cfg["ub"], dim, seed=0)
    assert at.metric[0].value == f"{r['mejor_f']:.2e}"
    dist = np.linalg.norm(r["mejor_x"] - cfg["optimo_x"](dim))
    assert at.metric[1].value == f"{dist:.2e}"
    assert at.metric[2].label == "Tiempo de ejecución"
    assert at.metric[2].value.endswith(" s")


@pytest.mark.parametrize("nombre", FUNC)
def test_simulacion_3d(app, nombre):
    at = elegir_funcion(app, nombre)
    _sin_errores(at)
    spec = _spec_3d(at)
    assert len(spec["frames"]) == 80
    assert spec["data"][0]["type"] == "surface"
    # 30 ballenas en el primer cuadro, dentro de la zona de busqueda
    xs = _arr(spec["data"][1]["x"])
    assert len(xs) == 30
    assert xs.min() >= FUNCIONES[nombre]["lb"] and xs.max() <= FUNCIONES[nombre]["ub"]
    # Cada cuadro trae su explicacion (fase, conteos y novedad)
    textos = [fr["layout"]["annotations"][0]["text"] for fr in spec["frames"]]
    assert textos[0].startswith("<b>Inicio.</b>")
    assert "Explorando" in textos[1] and "Afinando" in textos[-1]
    assert all("rodean" in t for t in textos[1:])
    # Al terminar la animacion, el titulo dice cuanto tardo el algoritmo
    titulos = [fr["layout"]["title"]["text"] for fr in spec["frames"]]
    assert "Terminó" in titulos[-1] and "tardó" in titulos[-1]
    assert not any("Terminó" in t for t in titulos[:-1])
    assert any("Tiempo de ejecución del algoritmo" in m.value
               for m in at.markdown)
    # Controles en filas distintas: botones arriba de la barra de vueltas
    assert spec["layout"]["updatemenus"][0]["y"] > spec["layout"]["sliders"][0]["y"] + 0.04


def test_simulacion_3d_opciones(app):
    at = elegir_funcion(app, "Ackley")
    at.radio(key="cam_3d").set_value("Girar sola").run()
    at.toggle(key="rastro_3d").set_value(True).run()
    at.slider(key="opac_3d").set_value(50).run()
    _sin_errores(at)
    spec = _spec_3d(at)
    assert spec["data"][0]["opacity"] == 0.5
    assert spec["data"][3]["mode"] == "lines"          # camino de la presa
    camaras = [fr["layout"]["scene"]["camera"]["eye"]["x"]
               for fr in spec["frames"]]
    assert len(set(round(c, 3) for c in camaras)) > 40  # la camara gira
    assert all(fr["traces"] == [1, 2, 3] for fr in spec["frames"])


def test_simulacion_3d_sin_escala_log(app):
    at = elegir_funcion(app, "Rosenbrock")
    at.toggle[0].set_value(False).run()          # "Aplanar los picos"
    _sin_errores(at)
    spec = _spec_3d(at)
    assert _arr(spec["data"][0]["z"]).max() > 1e6      # sin aplanar
    for vel in ("Lenta", "Rápida"):
        at.select_slider[0].set_value(vel).run()
        _sin_errores(at)


# --------------------------------------------------------------------------
# Ajustes extremos en la barra lateral
# --------------------------------------------------------------------------
@pytest.mark.parametrize("ajuste", [
    {"sb_ballenas": 2}, {"sb_vueltas": 1}, {"sb_vueltas": 2}, {"sb_a": 0.1},
    {"sb_a": 10.0}, {"sb_b": 0.0}, {"sb_b": 10.0}, {"sb_p": 0.0},
    {"sb_p": 1.0}, {"sb_semilla": 999_999},
])
def test_ajustes_extremos(ajuste):
    at = nueva_app()
    for k, v in ajuste.items():
        w = at.sidebar.slider(key=k) if k == "sb_p" else \
            at.sidebar.number_input(key=k)
        w.set_value(v)
    at.run()
    _sin_errores(at)
    boton(at, "Correr", key=None).click().run()
    _sin_errores(at)


@pytest.mark.parametrize("dim", [2, 30])
def test_dimension_extrema(dim):
    at = nueva_app()
    at.sidebar.number_input(key="sb_dim_Rastrigin").set_value(dim).run()
    boton(at, "Correr", key=None).click().run()
    _sin_errores(at)


def test_zona_invalida_muestra_error_y_no_truena():
    at = nueva_app()
    at.number_input(key="lb_Rastrigin").set_value(10.0).run()
    _sin_errores(at)
    assert any("Desde" in t for t in _textos(at.error))


def test_demasiados_movimientos_avisa_en_vez_de_congelarse():
    at = nueva_app()
    at.sidebar.number_input(key="sb_ballenas").set_value(1000)
    at.sidebar.number_input(key="sb_vueltas").set_value(5000)
    at.run(timeout=60)                      # sin el limite tardaria minutos
    _sin_errores(at)
    avisos = [t for t in _textos(at.warning) if "demasiados movimientos" in t]
    assert len(avisos) == 4                 # 3D, Paso a paso, Comparar, Sesgo


def test_boton_volver_a_valores_del_articulo():
    at = nueva_app()
    at.sidebar.number_input(key="sb_ballenas").set_value(77)
    at.sidebar.slider(key="sb_p").set_value(0.9)
    at.run()
    at.sidebar.button[0].click().run()
    _sin_errores(at)
    assert at.session_state["sb_ballenas"] == 30
    assert at.session_state["sb_p"] == 0.5
    assert not at.warning, _textos(at.warning)


# --------------------------------------------------------------------------
# Paso a paso
# --------------------------------------------------------------------------
def test_paso_a_paso_navegacion():
    at = elegir_funcion(nueva_app(), "Ackley")
    boton(at, "◀ Ballena").click().run()           # desde (0, 0) da la vuelta
    assert (at.session_state["pp_t"], at.session_state["pp_i"]) == (199, 29)
    boton(at, "Ballena ▶").click().run()
    assert (at.session_state["pp_t"], at.session_state["pp_i"]) == (0, 0)
    boton(at, "Vuelta ▶").click().run()
    assert (at.session_state["pp_t"], at.session_state["pp_i"]) == (1, 0)
    _sin_errores(at)


def test_paso_a_paso_siguiente_ejemplo_encuentra_la_regla_pedida(app):
    at = elegir_funcion(app, "Ackley")
    c = FUNCIONES["Ackley"]
    det = woa_detallado(c["f"], c["lb"], c["ub"], 2, seed=0)
    for regla in (0, 1, 2):
        at.selectbox(key="pp_regla").set_value(regla).run()
        boton(at, "Ir al siguiente ejemplo").click().run()
        t, i = at.session_state["pp_t"], at.session_state["pp_i"]
        assert det["iteraciones"][t]["ballenas"][i]["regla"] == regla
        _sin_errores(at)


# --------------------------------------------------------------------------
# Comparar, Muchas corridas, Sesgo
# --------------------------------------------------------------------------
@pytest.mark.parametrize("par", ["a_inicial", "n_ballenas", "max_iter", "b",
                                 "p_umbral"])
def test_comparar_cada_ajuste(app, par):
    at = elegir_funcion(app, "Ackley")
    at.selectbox(key="par_c").set_value(par).run()
    _sin_errores(at)


def _muchas_corridas(at, par, valores, reps=2):
    sel = [s for s in at.selectbox if s.label == "¿Qué ajuste quieres cambiar?"][0]
    sel.set_value(par).run()
    at.text_input(key=f"vals_{par}").set_value(valores)
    [n for n in at.number_input if n.label == "Repeticiones por valor"][0] \
        .set_value(reps)
    at.run()
    boton(at, "Correr", key="btn_exp").click().run()
    return at


@pytest.mark.parametrize("par, valores", [
    ("n_ballenas", "5, 10"), ("max_iter", "5, 10"), ("a_inicial", "1, 3"),
    ("b", "0.5, 2"), ("p_umbral", "0.2, 0.8"), ("dim", "2, 3")])
def test_muchas_corridas(app, par, valores):
    at = elegir_funcion(app, "Rastrigin")
    at = _muchas_corridas(at, par, valores)
    _sin_errores(at)
    assert len(at.dataframe) >= 1


def test_muchas_corridas_valores_invalidos(app):
    at = elegir_funcion(app, "Sphere")
    at = _muchas_corridas(at, "b", "uno, dos")
    _sin_errores(at)
    assert any("Revisa los valores" in t for t in _textos(at.error))


def test_sesgo_al_centro_estadistica(app):
    at = elegir_funcion(app, "Sphere")
    at.number_input(key="n_s").set_value(5).run()
    boton(at, "Correr", key="btn_sesgo").click().run()
    _sin_errores(at)
    df = at.session_state["sesgo"][0]
    original, movida = df["mediana"].iloc[0], df["mediana"].iloc[1]
    assert (df["tiempo_medio_s"] > 0).all()
    assert original < 1e-20 < movida


# --------------------------------------------------------------------------
# Resultados y Reporte
# --------------------------------------------------------------------------
def test_pestana_resultados_todas_las_carpetas(app):
    at = app
    carpetas = sorted(d for d in os.listdir(os.path.join(RAIZ, "resultados"))
                      if os.path.isdir(os.path.join(RAIZ, "resultados", d)))
    for c in carpetas:
        at.selectbox(key="res_carpeta").set_value(c).run()
        _sin_errores(at)
        if any(r.key == "res_param" for r in at.radio):
            for p in ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral",
                      "__todas__"]:
                at.radio(key="res_param").set_value(p).run()
                _sin_errores(at)


def test_pestana_reporte_encuentra_todas_las_imagenes(app):
    _sin_errores(app)
    assert not [t for t in _textos(app.warning) if "No se encontró" in t]
