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
from interfaz import paso_a_paso, visual, visual3d

st.set_page_config(page_title="WOA - Proyecto final", layout="wide")

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


def tabla_bonita(df):
    """Renombra columnas a lenguaje sencillo y formatea los numeros."""
    df = df.rename(columns=NOMBRE_COLUMNA)
    fmt = {c: "{:.2e}" for c in COLUMNAS_NUMERO if c in df}
    if "Seg. por corrida" in df:
        fmt["Seg. por corrida"] = "{:.3f}"
    return df.style.format(fmt)


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


st.sidebar.header("1. Elige la función")
nombre = st.sidebar.selectbox(
    "Función", list(FUNCIONES),
    help="Es el “terreno” donde las ballenas buscan el punto más bajo. "
         "Cada una tiene una trampa distinta (ver la pestaña Empieza aquí).")
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

(tab_inicio, tab1, tab_3d, tab_pp, tab2, tab3, tab4, tab_res,
 tab_rep) = st.tabs(["Empieza aquí", "Una corrida", "Simulación 3D",
                     "Paso a paso", "Comparar", "Muchas corridas",
                     "Sesgo al centro", "Resultados", "Reporte"])


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
| Si quieres... | Ve a la pestaña |
|---|---|
| Ver el algoritmo funcionando | **Una corrida** |
| Ver a las ballenas moverse sobre el terreno en 3D | **Simulación 3D** |
| Entender las fórmulas con números reales | **Paso a paso** |
| Ver por qué un ajuste cambia el resultado | **Comparar** |
| Sacar datos confiables (muchas repeticiones) | **Muchas corridas** |
| Ver el hallazgo más interesante del proyecto | **Sesgo al centro** |
| Ver y descargar las tablas y gráficas del reporte | **Resultados** |
| Leer la guía para escribir el reporte | **Reporte** |

Los ajustes de la **barra izquierda** se usan en todas las pestañas. Pasa el
mouse sobre el ⓘ de cada uno para ver qué hace.
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
        t0 = time.perf_counter()
        res = woa(cfg["f"], lb, ub, int(dim), seed=int(seed),
                  guardar_posiciones=True, **params)
        res["tiempo"] = time.perf_counter() - t0
        st.session_state["res"] = (res, nombre, int(dim), lb, ub)

    if "res" in st.session_state:
        res, nom_r, dim_r, lb_r, ub_r = st.session_state["res"]
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
        st.caption(f"{nom_r} con {dim_r} variables. Mejor punto encontrado: "
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
        res_3d = corrida(nombre, 2, lb, ub, int(seed), 0.0, **params)
        with st.spinner("Preparando la simulación..."):
            t0 = time.perf_counter()
            fig_3d = visual3d.figura_3d(
                cfg["f"], lb, ub, res_3d, cfg["optimo_x"](2), log=log_3d,
                ms=VELOCIDAD_3D[vel_3d], camara=CAMARAS_3D[cam_3d],
                rastro=rastro_3d, opacidad=1 - opac_3d / 100,
                a_inicial=params["a_inicial"], tiempo=res_3d["tiempo"])
            t_dibujo = time.perf_counter() - t0
        # Se muestra como pagina propia (no st.plotly_chart) para poder agregar
        # el JavaScript que deja girar la grafica mientras se reproduce.
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
    if not es_pesado(params):
        p_t = tuple(sorted(params.items()))
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
    st.info("**Qué observar:** " + QUE_OBSERVAR[par_c])
    modo = st.radio("Vista", ["Animación", "Pausar en un momento"],
                    horizontal=True, key="modo_c",
                    label_visibility="collapsed")

    if not es_pesado(*(dict(c[0]) for c in configs)):
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
                   "pestaña **Resultados**.")

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

    if st.button("Correr", key="btn_exp", type="primary"):
        try:
            valores = [float(v) for v in texto.split(",") if v.strip()]
        except ValueError:
            st.error("Revisa los valores: deben ser números separados por "
                     "comas, por ejemplo 10, 30, 50."); st.stop()
        if par in ("n_ballenas", "max_iter", "dim"):
            valores = [int(v) for v in valores]
        fijos = {k: v for k, v in params.items() if k != par}
        with st.spinner("Corriendo... (puede tardar un poco)"):
            df, fin, cur = barrido(nombre, par, valores,
                                   n_corridas=int(n_corridas),
                                   dim=int(dim), lb=lb, ub=ub, **fijos)
        st.session_state["exp"] = (df, fin, cur, par, nombre)

    if "exp" in st.session_state:
        df, fin, cur, par_r, nom_r = st.session_state["exp"]
        st.markdown(f"#### {nom_r}: efecto de {NOMBRE_PARAM[par_r].lower()}")
        st.dataframe(tabla_bonita(df), hide_index=True)
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
""")

    st.markdown(f"#### Ahora con muchas corridas ({int(dim)} variables)")
    c1, c2 = st.columns([1, 3])
    n_s = c1.number_input("Repeticiones", 2, 100, 20, key="n_s")
    if st.button("Correr", key="btn_sesgo", type="primary"):
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
        st.session_state["sesgo"] = (pd.DataFrame(filas), datos, nombre, d)

    if "sesgo" in st.session_state:
        df_s, datos, nom_s, d_s = st.session_state["sesgo"]
        st.caption(f"{nom_s} con {d_s} variables")
        st.dataframe(tabla_bonita(df_s), hide_index=True)
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
    num, _, resto = nombre_carpeta.partition("_")
    return f"{num}. {resto}"


def mostrar_archivo(ruta, clave):
    """Muestra un .csv (tabla) o .png (imagen) con su boton de descarga."""
    nombre_arch = os.path.basename(ruta)
    with open(ruta, "rb") as fh:
        datos = fh.read()
    if ruta.endswith(".csv"):
        st.dataframe(tabla_bonita(pd.read_csv(ruta)), hide_index=True)
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


with tab_res:
    st.write("Las tablas y gráficas que usamos en el reporte. Cada "
             "configuración se corrió **30 veces**.")
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
