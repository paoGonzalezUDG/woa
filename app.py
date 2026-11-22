"""
Interfaz web local para el proyecto WOA (Streamlit).
Ejecutar con:   streamlit run app.py

Todos los textos de la interfaz estan en lenguaje sencillo a proposito: la
idea es que la app sirva para entender el algoritmo y escribir el reporte.
"""
import io
import os
import re
import time
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from algoritmo.funciones import FUNCIONES
from algoritmo.woa import woa
from experimentos import PARAMS_DEFAULT, barrido
from interfaz import (cajas, combinaciones, diseno, paso_a_paso, visual,
                      visual3d)

st.set_page_config(page_title="WOA - Proyecto final", layout="wide")
# Secciones (arriba) grandes; subsecciones (adentro) como botoncitos, para
# que se note cual esta dentro de cual.
st.markdown("""<style>
div[data-testid="stTabs"] [data-testid="stTab"] p {
    font-size: 1.12rem; font-weight: 600; }
div[data-testid="stTabs"] div[data-testid="stTabs"] [data-testid="stTab"] {
    border-radius: 999px; padding: 0.15rem 0.9rem; margin-right: 0.4rem;
    background: rgba(128, 128, 128, 0.14); }
div[data-testid="stTabs"] div[data-testid="stTabs"]
        [data-testid="stTab"][aria-selected="true"],
div[data-testid="stTabs"] div[data-testid="stTabs"]
        [data-testid="stTab"][data-selected="true"] {
    background: rgba(255, 75, 75, 0.2); }
div[data-testid="stTabs"] div[data-testid="stTabs"] [data-testid="stTab"] p {
    font-size: 0.92rem; font-weight: 500; }
div[data-testid="stTabs"] div[data-testid="stTabs"]
        .react-aria-SelectionIndicator { display: none; }
/* Barra lateral: botones nativos de ocultar/mostrar siempre visibles y con
   texto (Streamlit solo los muestra al pasar el mouse y sin letrero). */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button {
    display: inline-flex !important; visibility: visible !important;
    opacity: 1 !important; }
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stExpandSidebarButton"] {
    width: auto !important; gap: 0.3rem; padding: 0.25rem 0.7rem !important;
    border-radius: 999px !important; border: 1px solid #ff9f9f !important;
    background: rgba(255, 75, 75, 0.12) !important; }
[data-testid="stSidebarCollapseButton"] button::after {
    content: "Ocultar ajustes"; font-size: 0.85rem; font-weight: 600; }
[data-testid="stExpandSidebarButton"]::after {
    content: "Mostrar ajustes"; font-size: 0.85rem; font-weight: 600; }
.woa-cargando {
    position: relative; overflow: hidden;
    display: flex; align-items: center; gap: 1rem;
    padding: 0.9rem 1.2rem 1.1rem; border-radius: 0.6rem;
    margin-bottom: 0.6rem; font-size: 1.05rem;
    background: #fff4e5; color: #4a2c00; border: 2px solid #ff9f1c; }
.woa-cargando b { color: #b35c00; }
.woa-rueda {
    width: 2rem; height: 2rem; flex: none; border-radius: 50%;
    border: 4px solid #ffd8a8; border-top-color: #e8590c;
    border-right-color: #e8590c;
    animation: woa-girar 0.7s linear infinite; }
.woa-barra {
    position: absolute; left: 0; bottom: 0; height: 5px; width: 35%;
    background: #e8590c; border-radius: 3px;
    animation: woa-avanzar 1.3s ease-in-out infinite; }
@keyframes woa-girar { to { transform: rotate(360deg); } }
@keyframes woa-avanzar { 0% { left: -35%; } 100% { left: 100%; } }
</style>""", unsafe_allow_html=True)

CARPETA_APP = os.path.dirname(os.path.abspath(__file__))
CARPETA_RES = os.path.join(CARPETA_APP, "resultados")
ARCHIVO_REPORTE = os.path.join(CARPETA_APP, "docs", "reporte_referencia.md")

# Nombres sencillos para mostrar en pantalla
NOMBRE_PARAM = {"n_ballenas": "Ballenas", "max_iter": "Vueltas",
                "a_inicial": "Exploración inicial (a)",
                "b": "Apertura de la espiral (b)",
                "p_umbral": "Umbral rodear/espiral (p)",
                "dim": "Número de variables"}
CORTO_PARAM = {"n_ballenas": "ballenas", "max_iter": "vueltas",
               "a_inicial": "a", "b": "b", "p_umbral": "umbral p",
               "dim": "variables"}
NOMBRE_COLUMNA = {"media": "Promedio", "desv_est": "Variación",
                  "mediana": "Mediana", "mejor": "Mejor", "peor": "Peor",
                  "tiempo_medio_s": "Seg. por corrida", "funcion": "Función",
                  "caso": "Caso", "optimo_en": "Mínimo en",
                  "dist_optimo": "Distancia al mínimo real",
                  "dist_centro": "Distancia al centro (0)",
                  **{k: v for k, v in NOMBRE_PARAM.items()}}
NOMBRE_COLUMNA["dim"] = "Variables"
COLUMNAS_NUMERO = ["Promedio", "Variación", "Mediana", "Mejor", "Peor",
                   "Distancia al mínimo real", "Distancia al centro (0)"]


# Lo que sale al pasar el mouse por el encabezado de cada columna
AYUDA_COLUMNA = {
    "Mejor": "La corrida que MEJOR salió de todas: el número más chico, el "
             "más cerca del mínimo. 0 = esa corrida llegó exacto.",
    "Peor": "La corrida que PEOR salió de todas: el número más grande. Dice "
            "qué tan mal puede salir con mala suerte. Si también es casi 0, "
            "el algoritmo es confiable.",
    "Mediana": "La corrida típica: la de en medio si ordenas todas las "
               "corridas de mejor a peor. Las corridas raras no la mueven.",
    "Promedio": "La suma de todas las corridas entre cuántas son. Una sola "
                "corrida mala lo jala hacia arriba (por eso también vemos la "
                "mediana).",
    "Variación": "Qué tan distintas salieron las corridas entre sí "
                 "(desviación estándar). 0 = todas dieron lo mismo.",
    "Seg. por corrida": "Cuánto tardó cada corrida, en promedio, en esta "
                        "computadora. Cambia un poco cada vez.",
    "Distancia al mínimo real": "Qué tan lejos quedó, en promedio, el mejor "
                                "punto encontrado del verdadero mínimo.",
    "Distancia al centro (0)": "Qué tan lejos quedó, en promedio, el mejor "
                               "punto encontrado del centro (0, ..., 0).",
    "Mínimo en": "Dónde está el mínimo en cada eje: 0 = en el centro "
                 "(original); otro número = movido de lugar.",
    "Caso": "Original = la función normal; movida = la misma función con el "
            "mínimo en otro lugar.",
    "Lugar": "Posición de esta combinación entre todas (1 = la mejor). Se "
             "ordenan por mediana; si empatan, por promedio y luego por la "
             "peor corrida.",
    "Ballenas × vueltas": "Cómo se repartió el mismo esfuerzo (6,000 "
                          "movimientos) entre ballenas y vueltas.",
    "¿Por defecto?": "Marcada = la combinación de los valores normales "
                     "(30 × 200, a = 2, b = 1, p = 0.5).",
}


def num_corto(x):
    """0 se ve como 0 (no 0.00e+00); lo demas en notacion cientifica."""
    return "0" if x == 0 else f"{x:.2e}"


def tabla_bonita(df):
    """Renombra columnas a lenguaje sencillo y formatea los numeros."""
    df = df.rename(columns=NOMBRE_COLUMNA)
    fmt = {c: num_corto for c in COLUMNAS_NUMERO if c in df}
    if "Seg. por corrida" in df:
        fmt["Seg. por corrida"] = "{:.3f}"
    for c in ("Exploración inicial (a)", "Apertura de la espiral (b)",
              "Umbral rodear/espiral (p)"):
        if c in df:
            fmt[c] = "{:g}"
    return df.style.format(fmt)


def mostrar_tabla(df):
    """Tabla con nombres sencillos y un (i) en cada encabezado conocido."""
    t = tabla_bonita(df)
    st.dataframe(t, hide_index=True, column_config={
        c: st.column_config.Column(help=AYUDA_COLUMNA[c])
        for c in t.data.columns if c in AYUDA_COLUMNA})


def mostrar(fig):
    st.pyplot(fig)
    plt.close(fig)


COMO_LEER_NUMEROS = """
- Los números son el **error**: qué tan lejos quedó del mínimo real, que en
  las 5 funciones es **0**. Más cerca de 0 = mejor.
- `1.5e-15` es notación científica: 0.0000000000000015, o sea, **casi cero**.
  `3.2e+01` = 32.
- **Promedio vs. mediana.** Si 5 corridas dan 1, 1, 1, 1 y 96, el promedio es
  20 (lo jala la corrida mala) pero la mediana es 1 (la corrida típica). Por
  eso conviene ver las dos.
- **Variación**: qué tan distintas salieron las corridas entre sí.
- **Mejor y peor**: la corrida que mejor salió y la que peor salió. Por
  ejemplo, en Beale la mediana es casi 0 pero la peor es 0.76: casi siempre
  sale bien, pero a veces se atora. Si la peor también es casi 0, el
  algoritmo es confiable.
- Pasa el mouse sobre el nombre de cada columna para ver qué significa.
"""
COMO_LEER_CAJAS = """
- **Cajas:** una por cada valor probado. La línea naranja es la mediana, la
  caja guarda la mitad de las corridas (caja alta = resultados muy
  distintos) y los circulitos son corridas raras. Más abajo = mejor.
- **Líneas:** cómo fue mejorando el resultado vuelta por vuelta.
- La escala es **logarítmica**: cada raya es 10, 100 o más veces más chica
  que la anterior. Sirve para ver números muy pequeños.
"""

# ----------------------------- Barra lateral -------------------------------
VALORES_ARTICULO = dict(
    sb_ballenas=PARAMS_DEFAULT["n_ballenas"],
    sb_vueltas=PARAMS_DEFAULT["max_iter"],
    sb_a=PARAMS_DEFAULT["a_inicial"], sb_b=PARAMS_DEFAULT["b"],
    sb_p=PARAMS_DEFAULT["p_umbral"], sb_semilla=0)
for _k, _v in VALORES_ARTICULO.items():      # valor inicial, solo una vez
    st.session_state.setdefault(_k, _v)


def valores_por_defecto():
    st.session_state.update(VALORES_ARTICULO)


st.sidebar.caption("Estos ajustes se usan en *Ver el algoritmo* y "
                   "*Probar tú*.")
st.sidebar.header("1. Elige la función")
nombre = st.sidebar.selectbox(
    "Función", list(FUNCIONES),
    help="Es el “terreno” donde las ballenas buscan el punto más bajo. "
         "Cada una tiene una trampa distinta (ver la sección Inicio).")
cfg = FUNCIONES[nombre]

if cfg["dim"] is None:
    dim = st.sidebar.number_input(
        "Número de variables", 2, 100, cfg["dim_default"],
        key=f"sb_dim_{nombre}",
        help="Cuántos números tiene cada punto. Con 2 variables un punto es "
             "(x, y) y se puede dibujar como mapa. Con 10 ya no se puede "
             "dibujar, pero el algoritmo funciona igual.")
else:
    dim = cfg["dim"]
    st.sidebar.caption(f"{nombre} solo existe con {dim} variables (x, y).")

with st.sidebar.expander("Fórmula y zona de búsqueda"):
    st.code(cfg["formula"], language=None)
    lb = st.number_input("Desde", value=float(cfg["lb"]), key=f"lb_{nombre}",
                         help="Límite inferior de la zona donde se permite "
                              "buscar, en cada variable.")
    ub = st.number_input("Hasta", value=float(cfg["ub"]), key=f"ub_{nombre}",
                         help="Límite superior de la zona de búsqueda.")

st.sidebar.header("2. Ajusta el algoritmo")
n_ballenas = st.sidebar.number_input(
    "Ballenas", 2, 1000, key="sb_ballenas",
    help="Cuántas buscan al mismo tiempo. Más ballenas cubren más terreno, "
         "pero cada vuelta tarda más.")
max_iter = st.sidebar.number_input(
    "Vueltas (iteraciones)", 1, 5000, key="sb_vueltas",
    help="Una vuelta = todas las ballenas se mueven una vez. Ejemplo: 30 "
         "ballenas y 200 vueltas = 6,000 movimientos en total.")
a_inicial = st.sidebar.number_input(
    "Exploración inicial (a)", 0.1, 10.0, step=0.5, key="sb_a",
    help="Es el “reloj” del algoritmo: empieza en este valor y baja hasta 0. "
         "Mientras es grande, las ballenas exploran zonas nuevas; cuando es "
         "chico, se quedan afinando cerca de la mejor. El artículo usa 2.")
b = st.sidebar.number_input(
    "Apertura de la espiral (b)", 0.0, 10.0, step=0.5, key="sb_b",
    help="Qué tan lejos salta una ballena cuando se mueve en espiral "
         "alrededor de la mejor. El artículo usa 1.")
p_umbral = st.sidebar.slider(
    "Umbral rodear/espiral (p)", 0.0, 1.0, step=0.05, key="sb_p",
    help="En cada movimiento se “echa un volado”. Con 0.5 es mitad y mitad: "
         "la mitad de las veces la ballena rodea o busca, y la otra mitad "
         "hace espiral. Con 0.8, el 80% rodea o busca y solo el 20% hace "
         "espiral.")
seed = st.sidebar.number_input(
    "Semilla", 0, 10**6, key="sb_semilla",
    help="Fija el azar, como barajar las cartas siempre igual. Con la misma "
         "semilla sale exactamente el mismo resultado; con otra, cambia. Así "
         "cualquiera puede repetir nuestros experimentos.")
st.sidebar.button("Volver a los valores por defecto",
                  on_click=valores_por_defecto)

params = dict(n_ballenas=int(n_ballenas), max_iter=int(max_iter),
              a_inicial=a_inicial, b=b, p_umbral=p_umbral)

CORTO_AJUSTE = {"n_ballenas": "ballenas", "max_iter": "vueltas",
                "a_inicial": "a", "b": "b", "p_umbral": "p"}


def texto_ajustes(nom, d, p, semilla, zona=None, cambia=None):
    """Una linea con los ajustes usados, para que cada captura diga con que
    parametros salio. En negritas lo que NO esta en su valor por defecto;
    'cambia' = el ajuste que se esta variando (se escribe aparte)."""
    partes = [f"**{nom}**"] + ([] if cambia == "dim" else [f"{d} variables"])
    for k in ("n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"):
        if k == cambia:
            continue
        v, dfl = p[k], PARAMS_DEFAULT[k]
        txt = (f"{v:g} {CORTO_AJUSTE[k]}" if k in ("n_ballenas", "max_iter")
               else f"{CORTO_AJUSTE[k]} = {v:g}")
        partes.append(f"**{txt}** (normal {dfl:g})"
                      if not np.isclose(v, dfl) else txt)
    partes.append(f"semilla {semilla}")
    cfg_n = FUNCIONES[nom]
    if zona and (zona[0] != cfg_n["lb"] or zona[1] != cfg_n["ub"]):
        partes.append(f"**zona {zona[0]:g} a {zona[1]:g}**")
    return "⚙️ Ajustes: " + " · ".join(partes)

st.sidebar.divider()
st.sidebar.caption("Colores de las ballenas: :blue[azul = rodear], "
                   ":orange[naranja = buscar], :green[verde = espiral], "
                   "gris = posición inicial. La X amarilla es la mejor "
                   "ballena y la estrella roja, el mínimo real.")

if lb >= ub:
    st.error("En la zona de búsqueda, “Desde” tiene que ser menor que “Hasta”.")
    st.stop()

st.title("El algoritmo de la ballena (WOA)")
st.caption("Ballenas virtuales buscando el punto más bajo de 5 funciones "
           "matemáticas. Proyecto final.")

# Precarga: se ve mientras se preparan las pestanas y se borra al terminar
# (ultima linea del archivo). Usar parar() en lugar de st.stop() para que
# no se quede pegado.
cargando = st.empty()
cargando.markdown(
    '<div class="woa-cargando"><div class="woa-rueda"></div>'
    "<div><b>⏳ Cargando…</b> preparando las gráficas y animaciones. Puede "
    "tardar unos segundos; cuando desaparezca este aviso, todo está listo."
    '</div><div class="woa-barra"></div></div>', unsafe_allow_html=True)


def parar():
    cargando.empty()
    st.stop()


# 5 secciones; las que tienen varias partes llevan sus propias pestanas.
SECCIONES = {
    "Inicio": [],
    "Ver el algoritmo": ["Una corrida", "Simulación 3D", "Paso a paso",
                         "Comparar"],
    "Probar tú": ["Muchas corridas", "Sesgo al centro"],
    "Resultados": ["Diseño del experimento", "Todas las cajas",
                   "Mejor combinación", "Tablas y descargas"],
    "Reporte": [],
}
INTRO_SECCION = {
    "Ver el algoritmo": "Mira cómo se mueven las ballenas y por qué. Usa los "
                        "ajustes de la barra izquierda.",
    "Probar tú": "Corre tus propios experimentos con muchas repeticiones "
                 "(tardan unos segundos o minutos).",
    "Resultados": "Los experimentos ya hechos para el reporte (30 corridas "
                  "cada uno, salvo la Tabla 1 de 25 ejecuciones: 1 corrida "
                  "por fila). No usan la barra izquierda: abren al "
                  "instante.",
}
(sec_inicio, sec_ver, sec_probar, sec_res, sec_rep) = st.tabs(list(SECCIONES))
with sec_ver:
    st.caption(INTRO_SECCION["Ver el algoritmo"])
    tab1, tab_3d, tab_pp, tab2 = st.tabs(SECCIONES["Ver el algoritmo"])
with sec_probar:
    st.caption(INTRO_SECCION["Probar tú"])
    tab3, tab4 = st.tabs(SECCIONES["Probar tú"])
with sec_res:
    st.caption(INTRO_SECCION["Resultados"])
    tab_diseno, tab_cajas, tab_comb, tab_res = st.tabs(SECCIONES["Resultados"])
tab_inicio, tab_rep = sec_inicio, sec_rep


# --------------------------- Utilidades cacheadas ---------------------------
def funcion_desplazada(nom, s):
    """f(x - s): la misma funcion, con el optimo movido s unidades en cada eje."""
    f = FUNCIONES[nom]["f"]
    if s == 0:
        return f
    return lambda x: f(np.asarray(x) - s)


@st.cache_data(show_spinner=False)
def corrida(nom, d, lb, ub, seed, s, n_ballenas, max_iter, a_inicial, b,
            p_umbral):
    """Como woa(), pero guarda en 'tiempo' los segundos que tardo. Queda en
    cache: si se repite la misma corrida, se reporta el tiempo de la primera."""
    t0 = time.perf_counter()
    res = woa(funcion_desplazada(nom, s), lb, ub, d, seed=seed,
              guardar_posiciones=True, n_ballenas=n_ballenas,
              max_iter=max_iter, a_inicial=a_inicial, b=b, p_umbral=p_umbral)
    return {**res, "tiempo": time.perf_counter() - t0}


def armar_casos(nom, lb, ub, seed, configs):
    """configs: tupla de (params_dict_como_tupla, desplazamiento, titulo)."""
    casos = []
    for p_t, s, titulo in configs:
        p = dict(p_t)
        res = corrida(nom, 2, lb, ub, seed, s, **p)
        casos.append(dict(f=funcion_desplazada(nom, s), lb=lb, ub=ub, res=res,
                          optimo=FUNCIONES[nom]["optimo_x"](2) + s,
                          titulo=f"{titulo} "
                                 f"({visual.texto_tiempo(res['tiempo'])})"))
    return casos


@st.cache_data(show_spinner=False)
def gif_cacheado(nom, lb, ub, seed, configs):
    return visual.gif_paneles(armar_casos(nom, lb, ub, seed, configs))


def aviso_2d():
    if cfg["dim"] is None:
        st.caption(f"Para poder dibujarla, aquí {nombre} se usa con 2 "
                   "variables. Con más variables funciona igual, solo que ya "
                   "no se puede dibujar.")


# Las pestanas que corren solas (3D, Paso a paso, Comparar, Sesgo) se vuelven
# a calcular con cada clic; con demasiados movimientos la app se congela.
LIMITE_MOVIMIENTOS = 200_000           # ballenas x vueltas


def es_pesado(*lista_params):
    """Muestra un aviso y devuelve True si alguna corrida tardaria mucho."""
    peor = max(p["n_ballenas"] * p["max_iter"] for p in lista_params)
    if peor <= LIMITE_MOVIMIENTOS:
        return False
    st.warning(f"Son demasiados movimientos ({peor:,} = ballenas × vueltas) "
               "para esta vista: tardaría mucho en prepararse. Baja las "
               "ballenas o las vueltas en la barra izquierda (máximo "
               f"{LIMITE_MOVIMIENTOS:,}).")
    return True


SEG_POR_MOVIMIENTO = 1.4e-5      # medido: 30 x 200 con 10 variables ~ 0.08 s
LIMITE_ESPERA_S = 60


def confirmar_espera(movimientos, clave):
    """Para las pestanas que corren muchas veces: si se calcula que tardara
    mas de un minuto, avisa y pide confirmar. Devuelve True si se puede
    correr."""
    seg = movimientos * SEG_POR_MOVIMIENTO
    if seg <= LIMITE_ESPERA_S:
        return True
    minutos = seg / 60
    texto = (f"unos {minutos:.0f} minutos" if minutos < 120
             else f"unas {minutos / 60:.1f} horas")
    st.warning(f"Con estos ajustes son {movimientos:,} movimientos en total: "
               f"tardaría **{texto}** (aprox.) y la app no responde mientras "
               "tanto. Baja las repeticiones, las ballenas o las vueltas, o "
               "confirma si de verdad quieres esperar.")
    return st.checkbox(f"Sí, quiero esperar {texto}", key=f"espera_{clave}")


AYUDA_TIEMPO = ("Cuánto tardó la computadora en hacer todas las vueltas del "
                "algoritmo (sin contar lo que tarda en dibujar). Cambia un "
                "poco cada vez y de una computadora a otra; sirve para "
                "comparar ajustes en la misma máquina.")


def comparar_tiempos(casos):
    """Texto con el tiempo de cada caso y cuantas veces tardo mas uno."""
    ts = [c["res"]["tiempo"] for c in casos]
    partes = [f"**{c['titulo'].rsplit(' (', 1)[0]}**: "
              f"{visual.texto_tiempo(t)}" for c, t in zip(casos, ts)]
    txt = "⏱ Tiempo de ejecución · " + " · ".join(partes)
    lento, rapido = max(ts), min(ts)
    if rapido > 0 and lento / rapido >= 1.2:
        txt += f" (uno tardó {lento / rapido:.1f} veces lo del otro)"
    return txt


# ------------------------------- Empieza aqui -------------------------------
with tab_inicio:
    st.markdown("""
Queremos que la compu encuentre **el punto más bajo** de una función. Imagina
un terreno lleno de cerros y hoyos: hay que encontrar el hoyo más profundo
**con los ojos vendados**. En lugar de una persona, mandamos un grupo de
**ballenas** que buscan al mismo tiempo y se pasan información.
""")
    st.markdown("#### ¿Por dónde empiezo?")
    st.markdown("""
La app tiene **5 secciones** (arriba). Ve en este orden:

| Sección | Para qué | Adentro |
|---|---|---|
| **1. Ver el algoritmo** | Entender cómo se mueven las ballenas | Una corrida · Simulación 3D · Paso a paso · Comparar |
| **2. Probar tú** | Correr tus propios experimentos | Muchas corridas · Sesgo al centro |
| **3. Resultados** | Los experimentos ya hechos para el reporte | Diseño del experimento · Todas las cajas · Mejor combinación · Tablas y descargas |
| **4. Reporte** | La guía para escribir el reporte | |

Los ajustes de la **barra izquierda** se usan en *Ver el algoritmo* y
*Probar tú*. Pasa el mouse sobre el ⓘ de cada uno para ver qué hace. Si te
estorba, escóndela con **« Ocultar ajustes** (arriba de la barra) y vuelve a
abrirla con **» Mostrar ajustes**.
""")

    st.markdown("#### Palabras que vas a ver")
    with st.expander("Lo básico: ballena, presa, vuelta, corrida, semilla",
                     expanded=True):
        st.markdown("""
- **Función (el terreno).** Una fórmula que le da una "altura" a cada punto.
  Ejemplo con Sphere: en el punto (3, 4) vale 3² + 4² = **25**; en (0, 0)
  vale **0**, que es lo más bajo posible.
- **Ballena.** Un punto de prueba, por ejemplo (3, 4). Cada ballena es una
  posible respuesta.
- **Presa.** La mejor ballena encontrada hasta ahora (la más baja). Todas la
  usan de referencia.
- **Vuelta (iteración).** Una ronda en la que **todas** las ballenas se
  mueven una vez. Con 30 ballenas y 200 vueltas hay 6,000 movimientos.
- **Corrida.** Correr el algoritmo completo una vez, de la primera vuelta a
  la última.
- **Semilla.** El algoritmo usa azar, así que cada corrida sale distinta. La
  semilla "fija" ese azar, como barajar las cartas siempre igual: misma
  semilla, mismo resultado. Por eso nuestros experimentos se pueden repetir.
- **Variables.** Cuántos números tiene cada punto. Con 2 es (x, y) y se puede
  dibujar como mapa. Con 10 no se puede dibujar, pero funciona igual.
""")
    with st.expander("Las 3 maneras de moverse (y explorar vs. afinar)"):
        st.markdown("""
En cada vuelta, cada ballena hace **una** de estas tres cosas:

| Color | Movimiento | Qué hace |
|---|---|---|
| :blue[**azul**] | **Rodear la presa** | Se acerca a la mejor ballena. *Afina.* |
| :orange[**naranja**] | **Buscar otra zona** | Sigue a una ballena al azar y puede pasarse de largo. *Explora.* |
| :green[**verde**] | **Espiral** | Da vueltas alrededor de la mejor, como la red de burbujas de las ballenas reales. *Afina.* |

**Explorar vs. afinar** (en el reporte: *explorar vs. explotar*). Llegas a
una ciudad nueva y buscas dónde comer. Los primeros días **exploras**:
caminas por todos lados. Ya que encontraste una buena zona, **afinas**: te
quedas por ahí probando los lugares cercanos.

El algoritmo hace lo mismo con el **reloj `a`**: empieza en 2 (mucha
exploración, aparece el naranja) y baja a 0 (casi solo afinar).

**¿Cómo decide cada ballena?** Con dos "volados":
1. Un número al azar `p`. Si sale menor que el umbral (0.5) → rodear o
   buscar. Si no → espiral.
2. Si toca rodear o buscar, se mira `A`, que depende del reloj. Si `A` está
   entre -1 y 1 → rodear. Si no → buscar. Como el reloj baja, `A` sale cada
   vez más chico y al final ya casi no hay búsquedas.
""")
    with st.expander("Cómo leer los resultados"):
        st.markdown(COMO_LEER_NUMEROS + COMO_LEER_CAJAS)
    with st.expander("Las 5 funciones (los terrenos)"):
        st.markdown("""
| Función | Apodo | La trampa | Mínimo en |
|---|---|---|---|
| Rastrigin | Cartón de huevo | Muchísimos hoyitos que engañan | (0, ..., 0) |
| Ackley | Llanura con un pozo | Todo plano, sin pistas de hacia dónde ir | (0, 0) |
| Sphere | Tazón | Ninguna: es la más fácil | (0, ..., 0) |
| Rosenbrock | Valle del plátano | Valle largo, curvo y casi plano | (1, ..., 1) |
| Beale | Valles angostos | Valles estrechos y esquinas empinadas | (3, 0.5) |

En todas, el valor más bajo posible es **0**.
""")
    with st.expander("Las fórmulas (para el reporte)"):
        st.markdown(r"""
| Qué | Fórmula |
|---|---|
| El reloj | `a = a_inicial · (1 − vuelta / total_de_vueltas)` |
| Números al azar | `A = 2·a·r1 − a`  ·  `C = 2·r2`  (r1, r2 entre 0 y 1) |
| Rodear | `X_nueva = X* − A · \|C·X* − X\|` |
| Buscar | `X_nueva = X_rand − A · \|C·X_rand − X\|` |
| Espiral | `X_nueva = \|X* − X\| · e^(b·l) · cos(2πl) + X*` (l entre -1 y 1) |

`X` = la ballena, `X*` = la presa, `X_rand` = una ballena al azar.

*Mirjalili y Lewis (2016), The Whale Optimization Algorithm.*
""")

# ------------------------------- Una corrida --------------------------------
with tab1:
    st.write("Corre el algoritmo **una vez**, de principio a fin, con los "
             "ajustes de la izquierda.")
    if st.button("Correr", type="primary"):
        with st.spinner("Corriendo el algoritmo..."):
            t0 = time.perf_counter()
            res = woa(cfg["f"], lb, ub, int(dim), seed=int(seed),
                      guardar_posiciones=True, **params)
            res["tiempo"] = time.perf_counter() - t0
        st.session_state["res"] = (res, nombre, int(dim), lb, ub,
                                   dict(params), int(seed))

    if "res" in st.session_state:
        res, nom_r, dim_r, lb_r, ub_r, par_res, seed_r = \
            st.session_state["res"]
        cfg_r = FUNCIONES[nom_r]
        x_opt = cfg_r["optimo_x"](dim_r)
        c1, c2, c3 = st.columns(3)
        c1.metric("Mejor valor encontrado", f"{res['mejor_f']:.2e}",
                  help="Lo más bajo que encontraron. Lo ideal es 0. "
                       "1.5e-15 = 0.0000000000000015, o sea, casi cero.")
        c2.metric("Distancia al punto ideal",
                  f"{np.linalg.norm(res['mejor_x'] - x_opt):.2e}",
                  help="Qué tan lejos quedó el mejor punto encontrado del "
                       "verdadero mínimo de la función.")
        c3.metric("Tiempo de ejecución", visual.texto_tiempo(res["tiempo"]),
                  help=AYUDA_TIEMPO)
        st.markdown(texto_ajustes(nom_r, dim_r, par_res, seed_r,
                                  (lb_r, ub_r)))
        st.caption("Mejor punto encontrado: "
                   f"`{np.array2string(res['mejor_x'], precision=4)}`")

        col_a, col_b = st.columns(2)
        with col_a:
            fig, ax = plt.subplots(figsize=(5, 4.5))
            ax.semilogy(res["curva"] + 1e-300)
            ax.set_xlabel("Vuelta"); ax.set_ylabel("Mejor valor (escala log)")
            ax.set_title("Cómo fue mejorando (tardó "
                         f"{visual.texto_tiempo(res['tiempo'])})")
            ax.grid(alpha=.3)
            mostrar(fig)
            st.caption("La línea solo baja o se queda igual: la mejor "
                       "ballena nunca empeora.")
        with col_b:
            if dim_r == 2:
                it = st.slider("Vuelta a mostrar", 0,
                               len(res["posiciones"]) - 1, 0)
                caso = dict(f=cfg_r["f"], lb=lb_r, ub=ub_r, res=res,
                            optimo=x_opt, titulo="Dónde están las ballenas")
                mostrar(visual.figura_paneles(
                    [caso], it / max(1, len(res["posiciones"]) - 1)))
                st.caption("Mueve la barra: al principio están dispersas "
                           "(exploran) y al final juntas (afinan).")
            else:
                fig, ax = plt.subplots(figsize=(5, 4.5))
                idx = np.arange(dim_r)
                ax.bar(idx - 0.2, res["mejor_x"], 0.4, label="encontrado")
                ax.bar(idx + 0.2, x_opt, 0.4, label="ideal")
                ax.set_xlabel("Variable"); ax.legend()
                ax.set_title("Punto encontrado vs. punto ideal")
                mostrar(fig)
                st.caption("Con más de 2 variables no se puede dibujar el "
                           "mapa. Aquí se compara cada variable con la ideal.")
        st.markdown("#### ¿Qué hizo cada ballena en cada momento?")
        mostrar(visual.figura_reglas(
            [dict(res=res, titulo=f"{nom_r}, {dim_r} variables")],
            [a_inicial]))
        st.caption("Cada franja muestra el porcentaje de ballenas que usaron "
                   "ese movimiento. "
                   "La línea punteada es el reloj `a`: cuando baja de 1, el "
                   "naranja (buscar) desaparece.")
    else:
        st.info("Ajusta lo que quieras a la izquierda y presiona **Correr**.")

# ------------------------------- Simulacion 3D ------------------------------
QUE_VER_3D = {
    "Rastrigin": "Es un **cartón de huevo**: lleno de hoyitos. Fíjate cómo "
                 "algunas ballenas se quedan un rato atoradas en hoyitos "
                 "mientras otras encuentran el hoyo del centro.",
    "Ackley": "Es una **llanura con un pozo** en el centro. En la parte plana "
              "no hay pistas de hacia dónde ir; mira cómo se van juntando "
              "hasta caer al pozo.",
    "Sphere": "Es un **tazón** sin trampas: todas las ballenas resbalan al "
              "fondo. Acércate con la rueda del mouse: al final quedan todas "
              "en un puntito.",
    "Rosenbrock": "Es el **valle del plátano**: llegan rápido al valle curvo, "
                  "pero avanzar por el fondo hasta el mínimo (1, 1) es "
                  "lentísimo porque casi no baja.",
    "Beale": "Son **valles angostos** con esquinas muy empinadas. El mínimo "
             "no está en el centro sino en (3, 0.5), cerca de una orilla.",
}
VELOCIDAD_3D = {"Lenta": 300, "Normal": 150, "Rápida": 60}
CAMARAS_3D = {"Desde arriba": "arriba", "Inclinada": "inclinada",
              "Girar sola": "girar"}

with tab_3d:
    st.write("Las ballenas moviéndose sobre el terreno, en 3D. Dale "
             "**▶ Reproducir** abajo de la gráfica. Para ver otra función, "
             "cámbiala en la barra izquierda.")
    aviso_2d()
    st.info(f"**{nombre}:** " + QUE_VER_3D[nombre])

    with st.container(border=True):
        st.markdown("**Cómo verla**")
        c1, c2, c3 = st.columns([1.7, 1, 1])
        cam_3d = c1.radio(
            "Cámara", list(CAMARAS_3D), horizontal=True, key="cam_3d",
            help="La vista con la que empieza. **Desde arriba** se ve como "
                 "un mapa; **Inclinada** se ven las montañas; **Girar sola** "
                 "le da la vuelta al terreno mientras avanza. Siempre puedes "
                 "girarla tú arrastrando con el mouse.")
        vel_3d = c2.select_slider("Velocidad", list(VELOCIDAD_3D),
                                  value="Normal")
        opac_3d = c3.slider(
            "Terreno transparente", 0, 70, 10, step=10, format="%d%%",
            key="opac_3d",
            help="Súbelo para ver las ballenas que quedan detrás de una "
                 "montaña.")
        c1, c2, _ = st.columns([1.7, 1, 1])
        log_3d = c1.toggle(
            "Aplanar los picos (escala log)", value=True,
            help="Algunas funciones tienen picos altísimos (Rosenbrock llega "
                 "a millones) que aplastan todo lo demás. Así se ven los "
                 "detalles del fondo. Las ballenas siguen en el mismo lugar; "
                 "solo cambia la altura del dibujo.")
        rastro_3d = c2.toggle(
            "Camino de la presa", value=False, key="rastro_3d",
            help="Dibuja la línea que fue siguiendo la mejor ballena. Sirve "
                 "para ver si llegó directo o si saltó de un valle a otro.")

    if not es_pesado(params):
        with st.spinner("Corriendo el algoritmo..."):
            res_3d = corrida(nombre, 2, lb, ub, int(seed), 0.0, **params)
        with st.spinner("Preparando la simulación 3D..."):
            t0 = time.perf_counter()
            fig_3d = visual3d.figura_3d(
                cfg["f"], lb, ub, res_3d, cfg["optimo_x"](2), log=log_3d,
                ms=VELOCIDAD_3D[vel_3d], camara=CAMARAS_3D[cam_3d],
                rastro=rastro_3d, opacidad=1 - opac_3d / 100,
                a_inicial=params["a_inicial"], tiempo=res_3d["tiempo"])
            t_dibujo = time.perf_counter() - t0
        # Se muestra como pagina propia (no st.plotly_chart) para poder agregar
        # el JavaScript que deja girar la grafica mientras se reproduce.
        st.markdown(texto_ajustes(nombre, int(dim), params, int(seed),
                                  (lb, ub)))
        st.iframe(visual3d.html_3d(fig_3d), height=fig_3d.layout.height + 10)
        st.markdown(
            f"⏱ **Tiempo de ejecución del algoritmo:** "
            f"{visual.texto_tiempo(res_3d['tiempo'])} para "
            f"{params['max_iter']} vueltas con {params['n_ballenas']} "
            f"ballenas · preparar la simulación tardó "
            f"{visual.texto_tiempo(t_dibujo)}.",
            help=AYUDA_TIEMPO + " La animación va más lento a propósito "
                 "para que se pueda ver; el algoritmo en sí es mucho más "
                 "rápido. Al llegar a la última vuelta, el título también lo "
                 "dice.")
        st.caption("Gírala arrastrando con el mouse y acércate con la rueda, "
                   "aunque se esté reproduciendo: mientras la tienes agarrada "
                   "se detiene y al soltarla sigue. Pasa el mouse sobre una "
                   "ballena para ver su valor.")

# ------------------------------- Paso a paso --------------------------------
@st.cache_data(show_spinner=False)
def corrida_detallada(nom, lb, ub, seed, p_t):
    return paso_a_paso.woa_detallado(FUNCIONES[nom]["f"], lb, ub, 2,
                                     seed=seed, **dict(p_t))


with tab_pp:
    st.write("Congela **una ballena en una vuelta** y te muestra, con los "
             "números reales, cómo decidió moverse.")
    aviso_2d()
    st.markdown(texto_ajustes(nombre, int(dim), params, int(seed), (lb, ub)))
    if not es_pesado(params):
        p_t = tuple(sorted(params.items()))
        with st.spinner("Calculando los números de cada ballena..."):
            det = corrida_detallada(nombre, lb, ub, int(seed), p_t)
        iters = det["iteraciones"]
        T, N = len(iters), params["n_ballenas"]
        # Si cambian los ajustes, regresar al inicio
        if st.session_state.get("pp_clave") != (nombre, lb, ub, seed, p_t):
            st.session_state.update(pp_clave=(nombre, lb, ub, seed, p_t),
                                    pp_t=0, pp_i=0)

        def mover(dt=0, di=0):
            k = (st.session_state.pp_t * N + st.session_state.pp_i
                 + dt * N + di) % (T * N)
            st.session_state.pp_t, st.session_state.pp_i = divmod(k, N)

        def ir_a_regla():
            r = paso_a_paso.buscar_ejemplo(
                iters, st.session_state.pp_regla, st.session_state.pp_t,
                st.session_state.pp_i)
            if r is not None:
                st.session_state.pp_t, st.session_state.pp_i = r

        c1, c2 = st.columns([3, 1])
        if T > 1:
            c1.slider("Vuelta", 0, T - 1, key="pp_t")
        else:            # una sola vuelta: un slider de 0 a 0 truena
            c1.markdown("**Vuelta:** 0 (solo hay una)")
        c2.number_input("Ballena #", 0, N - 1, key="pp_i")
        b1, b2, b3, b4, b5 = st.columns([1, 1, 1, 1.4, 1.4])
        b1.button("◀ Ballena", on_click=mover, kwargs=dict(di=-1))
        b2.button("Ballena ▶", on_click=mover, kwargs=dict(di=1))
        b3.button("Vuelta ▶", on_click=mover, kwargs=dict(dt=1))
        b4.selectbox("Buscar un ejemplo de", [0, 1, 2], key="pp_regla",
                     format_func=lambda k: paso_a_paso.NOMBRES[k],
                     label_visibility="collapsed")
        b5.button("Ir al siguiente ejemplo", on_click=ir_a_regla)

        it = iters[st.session_state.pp_t]
        d = it["ballenas"][st.session_state.pp_i]
        cuenta = np.bincount([x["regla"] for x in it["ballenas"]],
                             minlength=3)
        st.caption(f"En esta vuelta: reloj a = {it['a']:.2f} · rodearon "
                   f"{cuenta[0]}, buscaron {cuenta[1]}, en espiral {cuenta[2]} · "
                   + (f"la mejor bajó de {it['presa_f']:.2e} a "
                      f"{it['nueva_presa_f']:.2e} (ballena #{it['i_mejor']})"
                      if it["mejoro"] else
                      f"la mejor sigue en {it['presa_f']:.2e}"))

        col_a, col_b = st.columns([1.1, 1])
        with col_a:
            zoom = st.toggle("Acercar al movimiento", value=True)
            mostrar(paso_a_paso.figura_movimiento(cfg["f"], lb, ub, it, d,
                                                  b, zoom))
            st.caption("La **línea punteada** marca todos los lugares a los "
                       "que pudo llegar esta ballena si solo cambiara el "
                       "número al azar `A` (o `l` en la espiral).")
        with col_b:
            st.markdown(paso_a_paso.explicacion(
                it, d, params["max_iter"], a_inicial, b, p_umbral))
        mostrar(paso_a_paso.figura_decisiones(it, d, b, p_umbral, a_inicial))
        st.caption("Tip para estudiar: haz las cuentas a mano con estos "
                   "números y compara con la pantalla.")

# --------------------------------- Comparar ---------------------------------
COMPARAR_DEFAULTS = {"a_inicial": (1.0, 3.0), "n_ballenas": (10, 100),
                     "max_iter": (30, 300), "b": (0.5, 2.0),
                     "p_umbral": (0.2, 0.8)}
QUE_OBSERVAR = {
    "a_inicial": "Con `a` más grande, el reloj tarda más en bajar de 1, así "
                 "que el **naranja (buscar)** dura más y las ballenas siguen "
                 "dispersas más tiempo. Exploran más, pero les queda menos "
                 "tiempo para afinar. Con `a = 1` nunca hay naranja.",
    "n_ballenas": "Con más ballenas el terreno queda cubierto desde el "
                  "principio, y es más fácil que alguna caiga cerca del "
                  "mínimo. Lo malo: cada vuelta tarda más.",
    "max_iter": "El reloj baja igual, pero más despacio: con más vueltas hay "
                "más tiempo para explorar **y** para afinar. Con muy pocas, "
                "las ballenas no alcanzan a juntarse en el mínimo.",
    "b": "`b` cambia qué tan lejos saltan las ballenas en la espiral "
         "(**verde**). Con `b` grande, los saltos alrededor de la mejor son "
         "más largos.",
    "p_umbral": "El umbral reparte los movimientos: con 0.2 casi todo es "
                "**verde (espiral)**; con 0.8 casi todo es azul/naranja, así "
                "que al principio hay más **exploración (naranja)**.",
}

with tab2:
    st.write("Corre el algoritmo **dos veces con la misma suerte** (misma "
             "semilla), cambiando **solo un ajuste**, y las pone lado a lado.")
    aviso_2d()
    c1, c2, c3 = st.columns(3)
    par_c = c1.selectbox("¿Qué ajuste quieres comparar?",
                         list(COMPARAR_DEFAULTS), key="par_c",
                         format_func=NOMBRE_PARAM.get)
    vA0, vB0 = COMPARAR_DEFAULTS[par_c]
    es_entero = par_c in ("n_ballenas", "max_iter")
    paso = 1 if es_entero else 0.1
    vA = c2.number_input("Valor A", value=vA0, step=paso, key=f"vA_{par_c}")
    vB = c3.number_input("Valor B", value=vB0, step=paso, key=f"vB_{par_c}")

    def config(v):
        p = {**params, par_c: int(v) if es_entero else float(v)}
        return (tuple(sorted(p.items())), 0.0, f"{CORTO_PARAM[par_c]} = {v:g}")

    configs = (config(vA), config(vB))
    st.markdown(texto_ajustes(nombre, int(dim), params, int(seed), (lb, ub),
                              cambia=par_c)
                + f" · se compara **{CORTO_AJUSTE[par_c]}**: A = {vA:g}, "
                  f"B = {vB:g}")
    st.info("**Qué observar:** " + QUE_OBSERVAR[par_c])
    modo = st.radio("Vista", ["Animación", "Pausar en un momento"],
                    horizontal=True, key="modo_c",
                    label_visibility="collapsed")

    if not es_pesado(*(dict(c[0]) for c in configs)):
        with st.spinner("Corriendo las dos versiones..."):
            casos = armar_casos(nombre, lb, ub, int(seed), configs)
        if modo == "Animación":
            with st.spinner("Preparando la animación (la primera vez tarda "
                            "unos segundos)..."):
                st.image(gif_cacheado(nombre, lb, ub, int(seed), configs),
                         width="stretch")
        else:
            frac = st.slider("¿En qué momento? (% del recorrido)", 0, 100, 10,
                             key="frac_c") / 100
            mostrar(visual.figura_paneles(casos, frac))

        st.markdown(comparar_tiempos(casos), help=AYUDA_TIEMPO)
        st.markdown("#### ¿Qué movimiento usan con el tiempo?")
        mostrar(visual.figura_reglas(casos, [dict(c[0])["a_inicial"]
                                             for c in configs]))
        st.markdown("#### ¿Qué tan separadas están y cómo van mejorando?")
        mostrar(visual.figura_diversidad_convergencia(casos))
        st.caption("Ojo: esto es **una sola corrida**; sirve para ver la "
                   "idea. Para sacar conclusiones usa **Muchas corridas** o la "
                   "sección **Resultados**.")

# ------------------------------ Muchas corridas -----------------------------
with tab3:
    st.write("Como el algoritmo usa azar, una sola corrida puede salir bien o "
             "mal por suerte. Aquí cada valor se repite **muchas veces** y se "
             "resume. Los demás ajustes se quedan como en la barra izquierda.")
    c1, c2, c3 = st.columns(3)
    opciones_par = ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"] \
        + (["dim"] if cfg["dim"] is None else [])
    par = c1.selectbox("¿Qué ajuste quieres cambiar?", opciones_par,
                       format_func=NOMBRE_PARAM.get)
    sugeridos = {"n_ballenas": "10, 30, 50, 100", "max_iter": "50, 100, 200, 500",
                 "a_inicial": "1, 2, 3", "b": "0.5, 1, 2",
                 "p_umbral": "0.2, 0.5, 0.8", "dim": "2, 5, 10, 30"}
    texto = c2.text_input("Valores a probar (separados por comas)",
                          sugeridos[par], key=f"vals_{par}")
    n_corridas = c3.number_input(
        "Repeticiones por valor", 2, 200, 30,
        help="Cuántas corridas por cada valor. Usamos 30 en el reporte: "
             "suficientes para que la suerte se compense.")

    try:
        valores_previos = [float(v) for v in texto.split(",") if v.strip()]
    except ValueError:
        valores_previos = []
    movs_exp = 0
    for v in valores_previos:     # ballenas x vueltas de cada valor
        q = {**params, par: v} if par != "dim" else params
        escala = v / max(int(dim), 1) if par == "dim" else 1   # mas variables
        movs_exp += q["n_ballenas"] * q["max_iter"] * escala * int(n_corridas)
    puede_exp = confirmar_espera(int(movs_exp), "exp")
    if st.button("Correr", key="btn_exp", type="primary",
                 disabled=not puede_exp):
        try:
            valores = [float(v) for v in texto.split(",") if v.strip()]
        except ValueError:
            st.error("Revisa los valores: deben ser números separados por "
                     "comas, por ejemplo 10, 30, 50."); parar()
        if par in ("n_ballenas", "max_iter", "dim"):
            valores = [int(v) for v in valores]
        fijos = {k: v for k, v in params.items() if k != par}
        with st.spinner("Corriendo... (puede tardar un poco)"):
            df, fin, cur = barrido(nombre, par, valores,
                                   n_corridas=int(n_corridas),
                                   dim=int(dim), lb=lb, ub=ub, **fijos)
        st.session_state["exp"] = (df, fin, cur, par, nombre,
                                   (int(dim), dict(params), (lb, ub)))

    if "exp" in st.session_state:
        df, fin, cur, par_r, nom_r, (d_e, p_e, z_e) = st.session_state["exp"]
        st.markdown(f"#### {nom_r}: efecto de {NOMBRE_PARAM[par_r].lower()}")
        st.markdown(texto_ajustes(nom_r, d_e, p_e, "0, 1, 2, …", z_e,
                                  cambia=par_r)
                    + " · lo demás fijo")
        mostrar_tabla(df)
        vals = list(fin)
        col_a, col_b = st.columns(2)
        with col_a:
            fig, ax = plt.subplots(figsize=(5.5, 4))
            ax.boxplot([fin[v] for v in vals], tick_labels=[str(v) for v in vals])
            ax.set_yscale("symlog", linthresh=1e-12)
            ax.set_xlabel(NOMBRE_PARAM[par_r])
            ax.set_ylabel("Mejor valor al final")
            ax.set_title("Resultado de cada corrida")
            mostrar(fig)
        with col_b:
            fig, ax = plt.subplots(figsize=(5.5, 4))
            seg = dict(zip(df[par_r], df["tiempo_medio_s"]))
            for v in vals:
                ax.semilogy(np.mean(cur[v], axis=0) + 1e-300,
                            label=f"{CORTO_PARAM[par_r]} = {v} "
                                  f"({visual.texto_tiempo(seg[v])} c/u)")
            ax.set_xlabel("Vuelta"); ax.set_ylabel("Mejor valor (promedio)")
            ax.legend(fontsize=8); ax.set_title("Cómo fue mejorando")
            mostrar(fig)
        with st.expander("¿Cómo leo esto?"):
            st.markdown(COMO_LEER_NUMEROS + COMO_LEER_CAJAS)
        buf = io.StringIO(); df.to_csv(buf, index=False)
        st.download_button("Descargar tabla (CSV)", buf.getvalue(),
                           f"{nom_r}_{par_r}.csv", "text/csv")

# ------------------------------ Sesgo al centro -----------------------------
with tab4:
    st.write("**¿El algoritmo hace trampa?** Tomamos la misma función y solo "
             "la **movemos de lugar**. Es igual de difícil; lo único que "
             "cambia es dónde está el mínimo. Si el algoritmo no tuviera "
             "preferencias, debería salir parecido.")
    aviso_2d()
    opt0 = cfg["optimo_x"](2)
    s_max = float(min(ub - opt0.max(), opt0.min() - lb))
    if s_max <= 0.01:
        st.warning("Con esta zona de búsqueda no hay espacio para mover el "
                   "mínimo.")
        s_max = 0.01
    s = st.slider("¿Cuánto movemos el mínimo? (en cada eje)", 0.0,
                  round(s_max, 2), round(min(0.3 * ub, s_max), 2),
                  key=f"s_{nombre}")

    configs_s = ((tuple(sorted(params.items())), 0.0, "Original"),
                 (tuple(sorted(params.items())), s, f"Movida {s:g}"))
    st.info("**Qué observar:** en la función movida, ¿las ballenas llegan a "
            "la estrella roja (el mínimo real) o se quedan a medio camino "
            "hacia el centro?")
    modo_s = st.radio("Vista", ["Animación", "Pausar en un momento"],
                      horizontal=True, key="modo_s",
                      label_visibility="collapsed")
    if not es_pesado(params):
        with st.spinner("Corriendo la función original y la movida..."):
            casos_s = armar_casos(nombre, lb, ub, int(seed), configs_s)
        if modo_s == "Animación":
            with st.spinner("Preparando la animación..."):
                st.image(gif_cacheado(nombre, lb, ub, int(seed), configs_s),
                         width="stretch")
        else:
            frac = st.slider("¿En qué momento? (% del recorrido)", 0, 100,
                             30, key="frac_s") / 100
            mostrar(visual.figura_paneles(casos_s, frac))
        st.markdown(comparar_tiempos(casos_s), help=AYUDA_TIEMPO)
    with st.expander("¿Por qué pasa esto?"):
        st.markdown("""
En las fórmulas de rodear y buscar, la posición de la mejor ballena se
**multiplica por un número al azar** (`C`, entre 0 y 2). Multiplicar un
punto lo acerca o lo aleja **del 0**. Por ejemplo, 30 × 0.5 = 15: el punto se
fue hacia el centro. Así, el algoritmo tiene una tendencia escondida a jalar
a las ballenas hacia el centro.

Si el mínimo está en el centro (Rastrigin, Ackley, Sphere), eso ayuda
muchísimo. Si no (Rosenbrock, Beale), estorba. Esto explica por qué le fue
"perfecto" justo en esas 3 funciones.

**También explica Rosenbrock:** con 10 variables vale 9 en el centro, y las
corridas que se "atoran en ~8.9" terminan justo ahí, pegadas al centro, en
lugar de llegar a su mínimo (1, …, 1). La gráfica está en *Resultados ›
Tablas y descargas › Sesgo al centro*.
""")

    st.markdown(f"#### Ahora con muchas corridas ({int(dim)} variables)")
    c1, c2 = st.columns([1, 3])
    n_s = c1.number_input("Repeticiones", 2, 100, 20, key="n_s")
    movs_s = 2 * int(n_s) * params["n_ballenas"] * params["max_iter"]
    with c2:
        puede_s = confirmar_espera(movs_s, "sesgo")
    if st.button("Correr", key="btn_sesgo", type="primary",
                 disabled=not puede_s):
        d = int(dim)
        filas, datos = [], {}
        with st.spinner("Corriendo..."):
            for etiqueta, sv in (("Original", 0.0), (f"Movida {s:g}", s)):
                f_s = funcion_desplazada(nombre, sv)
                opt = cfg["optimo_x"](d) + sv
                fin, dist_opt, dist_0, tiempos = [], [], [], []
                for k in range(int(n_s)):
                    t0 = time.perf_counter()
                    r = woa(f_s, lb, ub, d, seed=k, **params)
                    tiempos.append(time.perf_counter() - t0)
                    fin.append(r["mejor_f"])
                    dist_opt.append(np.linalg.norm(r["mejor_x"] - opt))
                    dist_0.append(np.linalg.norm(r["mejor_x"]))
                datos[etiqueta] = np.array(fin)
                filas.append(dict(caso=etiqueta, mediana=np.median(fin),
                                  media=np.mean(fin), peor=np.max(fin),
                                  dist_optimo=np.mean(dist_opt),
                                  dist_centro=np.mean(dist_0),
                                  tiempo_medio_s=np.mean(tiempos)))
        st.session_state["sesgo"] = (pd.DataFrame(filas), datos, nombre, d,
                                     dict(params), (lb, ub), s)

    if "sesgo" in st.session_state:
        df_s, datos, nom_s, d_s, p_s, z_s, s_s = st.session_state["sesgo"]
        st.markdown(texto_ajustes(nom_s, d_s, p_s, "0, 1, 2, …", z_s)
                    + f" · mínimo movido {s_s:g} en cada eje")
        mostrar_tabla(df_s)
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.boxplot(list(datos.values()), tick_labels=list(datos))
        ax.set_yscale("symlog", linthresh=1e-12)
        ax.set_ylabel("Mejor valor al final")
        ax.set_title("Misma función, mínimo en otro lugar")
        mostrar(fig)

# -------------------------------- Resultados --------------------------------
PARAMS_INFO = {  # archivo -> (que es, valores probados, valor por defecto)
    "n_ballenas": ("Cuántas ballenas buscan", "10, 30, 50, 100", "30"),
    "max_iter": ("Cuántas vueltas da el algoritmo", "50, 100, 200, 500",
                 "200"),
    "a_inicial": ("Cuánto exploran al principio (reloj a)", "1, 2, 3", "2"),
    "b": ("Qué tan abierta es la espiral", "0.5, 1, 2", "1"),
    "p_umbral": ("Qué tan seguido rodean/buscan vs. hacen espiral",
                 "0.2, 0.5, 0.8", "0.5"),
}


def etiqueta_carpeta(nombre_carpeta):
    if nombre_carpeta == "0_base":
        return "Las 5 funciones juntas (valores por defecto)"
    if nombre_carpeta == "6_sesgo_centro":
        return "Sesgo al centro (mínimo movido)"
    if nombre_carpeta == "7_panorama":
        return "Todas las cajas en una figura (funciones × ajustes)"
    if nombre_carpeta == "8_combinaciones":
        return "Mejor combinación de ajustes por función"
    if nombre_carpeta == "9_tabla_25":
        return "Tabla 1 del reporte: 25 ejecuciones por función"
    num, _, resto = nombre_carpeta.partition("_")
    return f"{num}. {resto}"


def mostrar_archivo(ruta, clave):
    """Muestra un .csv (tabla) o .png (imagen) con su boton de descarga."""
    nombre_arch = os.path.basename(ruta)
    with open(ruta, "rb") as fh:
        datos = fh.read()
    if ruta.endswith(".csv"):
        mostrar_tabla(pd.read_csv(ruta))
        st.download_button(f"Descargar tabla ({nombre_arch})", datos,
                           nombre_arch, "text/csv", key=f"dl_{clave}")
    elif ruta.endswith(".png"):
        st.image(datos, width="stretch")
        st.download_button(f"Descargar gráfica ({nombre_arch})", datos,
                           nombre_arch, "image/png", key=f"dl_{clave}")


@st.cache_data(show_spinner=False)
def zip_resultados(firma):
    """ZIP de toda la carpeta resultados. 'firma' cambia si cambia un archivo."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta, _ in firma:
            z.write(os.path.join(CARPETA_RES, ruta),
                    os.path.join("resultados", ruta))
    return buf.getvalue()


ARCHIVO_CAJAS = os.path.join(CARPETA_RES, "7_panorama", "finales.csv")

# Lectura de cada fila de "Todas las cajas" (numeros de resultados/; si se
# regeneran con otro codigo, revisar estos textos)
LECTURA_CAJAS = {
    "Rastrigin": """
**Rastrigin (cartón de huevo): casi todo queda en 0.** Las excepciones:
- **Vueltas = 50:** la caja es muy alta (mediana 0.000057, peor 60): no le
  alcanzan las vueltas.
- **a = 1** y **p = 0.2:** aparecen puntitos arriba (peor 25.4 y 33.1):
  algunas corridas se atoran en un hoyito, porque casi no exploran.
- **b:** no cambia nada.
""",
    "Ackley": """
**Ackley: todas las cajas están pegadas abajo** (alrededor de 4e-15, o sea,
casi 0), menos **vueltas = 50** (1.6e-8). Es fácil para el algoritmo y casi
ningún ajuste importa.
""",
    "Sphere": """
**Sphere (tazón): todo llega casi a 0**, pero se ve **qué tan fino afina**:
- **Vueltas** es lo que más mueve: de 4.6e-6 con 50 a 1.4e-89 con 500.
- **Más ballenas** también ayuda: de 8e-24 con 10 a 7e-45 con 100.
- **a = 3** es peor (4.7e-26): gasta vueltas explorando un tazón que no
  tiene trampas.
- **b:** no cambia nada.
""",
    "Rosenbrock": """
**Rosenbrock (valle del plátano): la fila más interesante.**
- **La caja de la franja azul es altísima** (de ~0.1 a ~9): 17 de las 30
  corridas se atoran en el centro, donde la función vale 9 (ver la sección
  4.4 del reporte).
- **Bajan mucho la caja:** a = 3 (mediana 0.09), 100 ballenas (0.12),
  p = 0.8 (0.26), 500 vueltas (0.40) y b = 2 (0.66).
- **Es la única función donde casi todos los ajustes importan.**
""",
    "Beale": """
**Beale (valles angostos):**
- Las cajas bajan con más ballenas, más vueltas y sobre todo con
  **p = 0.2** (mediana 7e-13 contra 9e-9 por defecto).
- En **todas** las columnas hay **puntitos arriba (~0.76)**: entre 2 y 7
  corridas de 30 se atoran en un mínimo local. **Ningún ajuste las quita.**
  Por eso el promedio de Beale sale malo aunque la mediana sea casi 0.
""",
}
CONCLUSION_CAJAS = """
1. **Vueltas** es el ajuste que más mueve las cajas en casi todas las
   funciones.
2. **b** casi no hace nada (solo un poco en Rosenbrock).
3. **No hay un valor que sea el mejor en todas:** a = 3 ayuda en Rosenbrock
   pero empeora Sphere; p = 0.2 ayuda en Beale pero atora a Rastrigin.
4. **Rosenbrock y Beale son las difíciles**, cada una por algo distinto:
   Rosenbrock por el centro y Beale por un mínimo local.

Para el reporte, esta figura (`resultados/7_panorama/cajas.png`) puede
sustituir las 9 gráficas sueltas de la sección 4.2.
"""


@st.cache_data(show_spinner=False)
def datos_finales(firma):
    """'firma' = fecha del archivo: si se regenera, se vuelve a leer."""
    return pd.read_csv(diseno.FINALES)


@st.cache_data(show_spinner=False)
def combos_finales(firma):
    return combinaciones.leer(os.path.join(CARPETA_RES, "8_combinaciones",
                                           "resumen.csv"))


def resaltar_cambio(df, cambia):
    """Pinta (azul claro, negritas) las celdas de los ajustes que cambian
    (cambia = un conjunto de columnas por fila)."""
    estilo = pd.DataFrame("", index=df.index, columns=df.columns)
    for i, cols in enumerate(cambia):
        for col in cols:
            estilo.iloc[i, df.columns.get_loc(col)] = (
                "background-color: #d9ebf7; color: #12385c; font-weight: 700")
    return df.style.apply(lambda _: estilo, axis=None)


@st.cache_data(show_spinner=False)
def datos_tabla_25(firma):
    return pd.read_csv(diseno.CSV_TABLA_25)


with tab_diseno:
    st.write("Qué se corrió exactamente para el reporte: los valores, "
             "cuántas corridas y con qué semillas. Las tablas salen "
             "directo del código (`experimentos.py`), así que siempre "
             "coinciden con lo que hay en `resultados/`.")
    if os.path.exists(diseno.PDF):
        with open(diseno.PDF, "rb") as fh:
            st.download_button(
                "📄 Descargar en PDF", fh.read(),
                file_name="diseno_experimental.pdf", mime="application/pdf",
                help="Las mismas tablas y las notas, listas para pegar "
                     "en la sección 3 del reporte. Se vuelve a generar con "
                     "`python -m interfaz.diseno`.")
    st.subheader("1. Diseño experimental de 25 ejecuciones por función")
    st.caption("La Tabla 1 del reporte (diseño de Diana). **Una corrida por fila**, con la "
               "semilla indicada (125 en total). En azul, lo que cambia "
               "respecto a la base. Variables 10 / 2 = las funciones de n "
               "variables / Ackley y Beale.")
    df_25, cambia_25 = diseno.filas_tabla_25()
    st.dataframe(resaltar_cambio(df_25, cambia_25), hide_index=True,
                 height=35 * (len(df_25) + 1) + 3)
    st.caption(diseno.nota_fila_25())
    st.subheader("2. Resultado de cada ejecución")
    if not os.path.exists(diseno.CSV_TABLA_25):
        st.warning("Falta `resultados/9_tabla_25/corridas.csv`. Se crea con "
                   "`python experimentos.py --solo-tabla-25` (menos de 1 "
                   "min).")
    else:
        df_25r = datos_tabla_25(os.path.getmtime(diseno.CSV_TABLA_25))
        st.write("El mejor valor que encontró cada ejecución (más bajo = "
                 "mejor; el mínimo real de todas es 0).")
        res_25 = diseno.tabla_25_resultados(df_25r)
        st.dataframe(res_25.style.format(
            {c: num_corto for c in FUNCIONES}), hide_index=True,
            height=35 * (len(res_25) + 1) + 3)
        st.image(os.path.join(CARPETA_RES, "9_tabla_25", "resultados.png"),
                 width="stretch")
        st.caption("Ojo: con **una sola corrida** por fila pesa mucho el "
                   "azar. Para comparar ajustes, mejor las medianas de 30 "
                   "corridas (Tabla 5 y *Todas las cajas*).")
    st.subheader("3. Valores por defecto (configuración base)")
    st.dataframe(diseno.tabla_base(), hide_index=True)
    st.subheader("4. Funciones de prueba")
    st.dataframe(diseno.tabla_funciones(), hide_index=True)
    st.caption("\\* Sphere y Rosenbrock no tienen límite en Wikipedia: la "
               "zona de búsqueda la elegimos nosotras.")
    st.subheader("5. Barridos con 30 corridas por valor")
    st.caption("Los que usan las gráficas de caja y las medianas del "
               "reporte. En azul, el valor que cambia respecto a la base.")
    df_barr, cambia_barr = diseno.filas_barridos()
    st.dataframe(resaltar_cambio(df_barr, cambia_barr), hide_index=True)
    st.subheader("6. Experimentos adicionales")
    st.dataframe(diseno.tabla_adicionales(), hide_index=True)
    with st.expander("Notas (totales y aclaraciones)", expanded=True):
        st.markdown("\n".join(f"- {n}" for n in diseno.notas()))

    st.subheader("7. ¿Qué pasa en cada función?")
    st.write("Lo que salió de los barridos (Tabla 5), para no tener que "
             "probar ajustes uno por uno. Todos los números son de 30 "
             "corridas por valor, no de la Tabla 1 (1 corrida por fila).")
    st.dataframe(diseno.RESUMEN, hide_index=True)
    with st.expander("Lo que no hace falta probar", expanded=True):
        st.markdown(diseno.NO_HACE_FALTA)
    if not os.path.exists(diseno.FINALES):
        st.warning("Falta `resultados/7_panorama/finales.csv`. Se crea con "
                   "`python experimentos.py --solo-panorama` (unos 4 min).")
    else:
        fin_dis = datos_finales(os.path.getmtime(diseno.FINALES))
        f_dis = st.radio("Función", list(FUNCIONES), horizontal=True,
                         key="dis_func",
                         help="Elige una función para ver qué le pasa con "
                              "cada ajuste.")
        st.markdown(diseno.EXPLICACION[f_dis])
        arch_comb = os.path.join(CARPETA_RES, "8_combinaciones",
                                 "resumen.csv")
        if os.path.exists(arch_comb):
            top = combos_finales(os.path.getmtime(arch_comb))
            top = top[(top.funcion == f_dis) & (top.lugar == 1)]
            mejor = top.iloc[0]
            extra = (f" (empatan {len(top)} combinaciones en 1er lugar)"
                     if len(top) > 1 else "")
            st.info(f"🏆 **Mejor combinación** de las 81 (25 corridas "
                    f"cada una): {combinaciones.texto(mejor)}, mediana "
                    f"{num_corto(mejor.mediana)}{extra}. Más detalle en "
                    "*Resultados › Mejor combinación*.")
        with st.expander(f"Todos los números de {f_dis}"):
            t = diseno.tabla_por_valor(fin_dis, f_dis)
            st.dataframe(
                t.style.format({"Mediana": num_corto, "Peor": num_corto}),
                hide_index=True, column_config={
                    "¿Base?": st.column_config.CheckboxColumn(
                        help="Marcada = el valor por defecto (la base)."),
                    "Mediana": st.column_config.Column(
                        help=AYUDA_COLUMNA["Mediana"]),
                    "Peor": st.column_config.Column(
                        help=AYUDA_COLUMNA["Peor"])})
            if f_dis in diseno.ATORADA:
                st.caption(f"Atorada = la corrida terminó arriba de "
                           f"{diseno.ATORADA[f_dis]:g}.")


@st.cache_data(show_spinner=False)
def datos_cajas(firma):
    """'firma' = fecha del archivo: si se regenera, se vuelve a leer."""
    return cajas.leer(ARCHIVO_CAJAS)


with tab_cajas:
    st.write("Todos los experimentos en **una sola gráfica**: cada fila es "
             "una función y cada columna un ajuste. Cada caja son 30 "
             "corridas con ese valor (lo demás se queda en su valor por "
             "defecto). Pasa el mouse sobre una caja para ver sus números.")
    if not os.path.exists(ARCHIVO_CAJAS):
        st.warning("Falta `resultados/7_panorama/finales.csv`. Se crea con "
                   "`python experimentos.py --solo-panorama` (unos 4 min).")
    else:
        df_cajas = datos_cajas(os.path.getmtime(ARCHIVO_CAJAS))
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            ver_cajas = c1.radio(
                "Ver", ["Todas"] + list(FUNCIONES), horizontal=True,
                key="cajas_ver",
                help="**Todas** junta las 5 funciones (la figura para el "
                     "reporte). Elige una función para verla más grande.")
            puntos_cajas = c2.toggle(
                "Ver cada corrida", key="cajas_puntos",
                help="Dibuja un puntito por cada una de las 30 corridas, "
                     "no solo las raras.")
        funcs_cajas = list(FUNCIONES) if ver_cajas == "Todas" else [ver_cajas]
        st.plotly_chart(
            cajas.figura_cajas(df_cajas, funcs_cajas, PARAMS_DEFAULT,
                               puntos_cajas),
            width="stretch", key="cajas_fig", theme=None)
        if ver_cajas != "Todas":          # una sola funcion: su lectura
            st.info(LECTURA_CAJAS[ver_cajas])
        with st.expander("¿Cómo leo esta gráfica?"):
            st.markdown("""
**Qué es:** cada **fila** es una función y cada **columna** un ajuste.
Dentro de cada cuadrito hay una caja por cada valor probado (por ejemplo,
en *Ballenas*: 10, 30, 50 y 100). Cada caja son **30 corridas** con ese
valor; **solo cambia ese ajuste**, lo demás se queda en su valor por
defecto.

**Cómo leer una caja:**
```
   •        ← corrida rara (mucho peor o mejor que las demás)
   ┬        ← bigote: hasta dónde llegan las corridas "normales"
 ┌───┐
 │---│      ← línea punteada: el promedio
 │───│      ← raya sólida: la mediana (la corrida típica)
 └───┘      ← la caja guarda la mitad de las corridas (las 15 de en medio)
   ┴
```
- **Más abajo = mejor** (más cerca del mínimo, que es 0).
- **Caja alta** = corridas muy distintas entre sí (poco confiable).
  **Caja aplastada** = las 30 dieron casi lo mismo.
- **Franja azul** = el valor por defecto: compara las otras cajas contra
  ella para ver si ese valor ayuda o estorba.
- **0 en el eje** (línea punteada gris de abajo): ahí quedan las corridas
  que llegaron exactamente al mínimo.
- **Escala logarítmica:** cada marca del eje es **10 veces** más chica que
  la de arriba; bajar una marca = mejorar 10 veces.

**Cómo comparar:** las 5 gráficas de una fila usan la misma escala. **El
ajuste cuyas cajas se mueven más es el que más importa** en esa función; si
quedan a la misma altura, casi no importa.
""")
        with st.expander("¿Qué dice cada fila?"):
            for nom_l in FUNCIONES:
                st.markdown(LECTURA_CAJAS[nom_l])
        with st.expander("¿Qué se concluye de toda la gráfica?"):
            st.markdown(CONCLUSION_CAJAS)
        st.caption("La versión en imagen para el reporte está en "
                   "`resultados/7_panorama/cajas.png`.")

ARCHIVO_COMB = os.path.join(CARPETA_RES, "8_combinaciones", "resumen.csv")


@st.cache_data(show_spinner=False)
def datos_comb(firma):
    """'firma' = fecha del archivo: si se regenera, se vuelve a leer."""
    return combinaciones.leer(ARCHIVO_COMB)


with tab_comb:
    st.write("Aquí se movieron **varios ajustes a la vez** para buscar la "
             "mejor combinación de cada función. Se probaron todas las "
             "combinaciones de **a** (1, 2, 3), **b** (0.5, 1, 2) y **p** "
             "(0.2, 0.5, 0.8), y tres maneras de repartir el mismo esfuerzo "
             "entre ballenas y vueltas (10×600, 30×200 y 60×100). En total "
             "son **81 combinaciones**, cada una corrida **25 veces**.")
    with st.expander("¿Por qué el mismo esfuerzo y no más ballenas o vueltas?"):
        st.markdown("""
Más ballenas o más vueltas **siempre** ayudan, porque es más trabajo (eso ya
se ve en *Todas las cajas*). Si los metiéramos libres, ganaría siempre
"100 ballenas × 500 vueltas" y no aprenderíamos nada. Por eso todas las
combinaciones hacen **6,000 movimientos** (ballenas × vueltas): la pregunta
es *cómo conviene repartirlos* y qué valores de a, b y p usar, con el
mismo trabajo. Así la comparación es justa.
""")
    if not os.path.exists(ARCHIVO_COMB):
        st.warning("Falta `resultados/8_combinaciones/resumen.csv`. Se crea "
                   "con `python experimentos.py --solo-combinaciones` "
                   "(unos 12 min).")
    else:
        df_comb = datos_comb(os.path.getmtime(ARCHIVO_COMB))
        total_comb = int(df_comb.groupby("funcion").size().max())
        f_comb = st.radio("Función", list(FUNCIONES), horizontal=True,
                          key="comb_func",
                          help="Elige la función para ver su mejor "
                               "combinación.")
        d_comb = combinaciones.de_funcion(df_comb, f_comb)
        mejor_c = d_comb.iloc[0]
        dfl_c = d_comb[combinaciones.es_default(d_comb, PARAMS_DEFAULT)].iloc[0]
        empatadas = int((d_comb.lugar == 1).sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Mejor combinación", combinaciones.texto(mejor_c),
                  help="La que tiene la mediana más baja. Si empatan, gana "
                       "la de menor promedio y luego la de peor corrida más "
                       "baja.")
        c2.metric("Lugar de la de por defecto",
                  f"{int(dfl_c.lugar)} de {total_comb}",
                  help="30 ballenas × 200 vueltas, a = 2, b = 1, p = 0.5 "
                       "(los valores por defecto; a, b y p son los del "
                       "artículo, las 200 vueltas las elegimos nosotras).")
        c3.metric("Empatadas en 1er lugar", empatadas,
                  help="Combinaciones cuyas 25 corridas dieron exactamente "
                       "lo mismo que la mejor (normalmente: todas en 0).")
        if empatadas > 1:
            st.info(f"**{empatadas} combinaciones empatan en 1er lugar** "
                    "(llegaron al mínimo en todas sus corridas). En esta "
                    "función no hay una sola ganadora: muchas combinaciones "
                    "sirven igual de bien.")

        st.markdown("##### ¿Qué ajuste importa más en esta función?")
        st.caption("Para cada valor, el **lugar promedio** de las "
                   "combinaciones que lo usan (más arriba = mejor). Verde = "
                   "el mejor valor; azul = el valor por defecto. Si los "
                   "puntos de un ajuste quedan casi a la misma altura, ese "
                   "ajuste casi no importa aquí; si están muy separados "
                   "(\"diferencia\" grande), es el que más importa.")
        st.plotly_chart(
            combinaciones.figura_lugar_promedio(d_comb, PARAMS_DEFAULT,
                                                total_comb),
            width="stretch", key="comb_lugar", theme=None)

        st.markdown("##### Las 10 mejores (y la de por defecto)")
        t_comb = combinaciones.tabla(d_comb, PARAMS_DEFAULT).rename(columns={
            "lugar": "Lugar", "reparto": "Ballenas × vueltas",
            "por_defecto": "¿Por defecto?"})
        mostrar_tabla(t_comb)

        st.markdown("##### ¿La mejor de una función sirve para las demás?")
        st.caption("Cada **fila** es una combinación de ajustes (la que "
                   "ganó en una función, y la de por defecto). Cada "
                   "**columna** es una función donde se probó. Los números "
                   f"son el **lugar** que saca ahí (1 = la mejor, "
                   f"{total_comb} = la peor), no ballenas ni vueltas. "
                   "\"10×600\" = 10 ballenas × 600 vueltas. Verde = buen "
                   "lugar, rojo = mal lugar.")
        st.plotly_chart(
            combinaciones.figura_cruce(df_comb, list(FUNCIONES),
                                       PARAMS_DEFAULT, total_comb),
            width="stretch", key="comb_cruce", theme=None)
        with st.expander("¿Cómo leo esto?"):
            st.markdown(f"""
- **Lugar:** se ordenan las {total_comb} combinaciones de cada función de la
  mejor (1) a la peor. Se compara primero la **mediana** de sus 25 corridas
  (la corrida típica); si empatan, el **promedio**; luego la **peor** corrida.
- **Empates:** si dos combinaciones dieron exactamente lo mismo (por ejemplo,
  las 25 corridas en 0), comparten lugar.
- **Lugar promedio:** si las combinaciones con a = 3 suelen quedar arriba en
  la tabla, a = 3 tiene un lugar promedio bajo. Así se ve qué valor de cada
  ajuste conviene, aunque los demás ajustes cambien.
- **Tabla de colores:** si una fila es verde en su función y roja en otras,
  esa combinación sirve para una función pero no para todas.
- **Mismas semillas** para todas las combinaciones: la corrida 1 de cada una
  empieza con las ballenas en el mismo lugar, así la comparación es pareja.
""")
        st.caption("Las versiones en imagen para el reporte están en "
                   "`resultados/8_combinaciones/` (mapa.png y cruce.png).")

with tab_res:
    st.write("Las tablas y gráficas que usamos en el reporte. Cada "
             "configuración se corrió **30 veces**, salvo la Tabla 1 de "
             "25 ejecuciones (`9_tabla_25`), que es **1 corrida por fila**.")
    if not os.path.isdir(CARPETA_RES):
        st.warning("No existe la carpeta resultados/. Se crea con "
                   "`python experimentos.py`.")
    else:
        firma = tuple(sorted(
            (os.path.relpath(os.path.join(r, a), CARPETA_RES),
             os.path.getmtime(os.path.join(r, a)))
            for r, _, archs in os.walk(CARPETA_RES) for a in archs))
        carpetas = sorted(d for d in os.listdir(CARPETA_RES)
                          if os.path.isdir(os.path.join(CARPETA_RES, d)))
        c1, c2 = st.columns([3, 1])
        carpeta = c1.selectbox("¿Qué quieres ver?", carpetas,
                               format_func=etiqueta_carpeta, key="res_carpeta")
        c2.download_button("Descargar todo (.zip)", zip_resultados(firma),
                           "resultados.zip", "application/zip")
        ruta_c = os.path.join(CARPETA_RES, carpeta)
        archivos = sorted(os.listdir(ruta_c))
        params_aqui = [p for p in PARAMS_INFO if f"{p}.csv" in archivos]

        if params_aqui:                      # carpeta de una funcion
            opciones = params_aqui + ["__todas__"]
            elegido = st.radio(
                "Ajuste", opciones, horizontal=True, key="res_param",
                format_func=lambda p: "Todas las gráficas"
                if p == "__todas__" else NOMBRE_PARAM[p])
            if elegido == "__todas__":
                cols = st.columns(2)
                for k, p in enumerate(params_aqui):
                    with cols[k % 2]:
                        st.markdown(f"**{NOMBRE_PARAM[p]}**")
                        st.image(os.path.join(ruta_c, f"{p}.png"),
                                 width="stretch")
            else:
                que_es, vals_p, def_p = PARAMS_INFO[elegido]
                st.info(f"**{que_es}.** Se probó con {vals_p} (normalmente "
                        f"{def_p}). Todo lo demás se quedó igual.")
                mostrar_archivo(os.path.join(ruta_c, f"{elegido}.png"),
                                f"{carpeta}_{elegido}_png")
                mostrar_archivo(os.path.join(ruta_c, f"{elegido}.csv"),
                                f"{carpeta}_{elegido}_csv")
        else:                                # base o sesgo: mostrar todo
            for a in [x for x in archivos if x.endswith(".png")] + \
                     [x for x in archivos if x.endswith(".csv")]:
                mostrar_archivo(os.path.join(ruta_c, a), f"{carpeta}_{a}")
        with st.expander("¿Cómo leo esto?"):
            st.markdown(COMO_LEER_NUMEROS + COMO_LEER_CAJAS)

# --------------------------------- Reporte ----------------------------------
IMAGEN_MD = re.compile(r"^!\[(.*?)\]\((.+?)\)\s*$")


def mostrar_markdown(texto, carpeta_base):
    """st.markdown no muestra imagenes con ruta local: se separan y se
    muestran con st.image."""
    bloque = []
    for linea in texto.splitlines():
        if linea.startswith("<!-- "):       # marcas de tablas automaticas
            continue
        m = IMAGEN_MD.match(linea)
        if m:
            if bloque:
                st.markdown("\n".join(bloque))
                bloque = []
            ruta = os.path.normpath(os.path.join(carpeta_base, m.group(2)))
            if os.path.exists(ruta):
                st.image(ruta, width="stretch")
            else:
                st.warning(f"No se encontró la imagen {m.group(2)}")
        else:
            bloque.append(linea)
    if bloque:
        st.markdown("\n".join(bloque))


with tab_rep:
    if not os.path.exists(ARCHIVO_REPORTE):
        st.warning("No se encontró docs/reporte_referencia.md")
    else:
        with open(ARCHIVO_REPORTE, encoding="utf-8") as fh:
            texto_rep = fh.read()
        st.download_button("Descargar la guía (.md)", texto_rep,
                           "reporte_referencia.md", "text/markdown")
        mostrar_markdown(texto_rep, os.path.dirname(ARCHIVO_REPORTE))

cargando.empty()      # todo listo: quitar el aviso de "Cargando..."
