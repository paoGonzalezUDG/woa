"""
Interfaz web local para el proyecto WOA (Streamlit).
Ejecutar con:   streamlit run app.py
"""
import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from experimentos import PARAMS_DEFAULT, barrido
from funciones import FUNCIONES
from woa import woa
import paso_a_paso
import visual

st.set_page_config(page_title="WOA - Proyecto final", layout="wide")
st.title("Whale Optimization Algorithm (WOA)")

# ----------------------------- Barra lateral -------------------------------
st.sidebar.header("Problema")
nombre = st.sidebar.selectbox("Funcion", list(FUNCIONES))
cfg = FUNCIONES[nombre]
st.sidebar.code(cfg["formula"], language=None)

if cfg["dim"] is None:
    dim = st.sidebar.number_input("Dimension (n)", 2, 100, cfg["dim_default"])
else:
    dim = cfg["dim"]
    st.sidebar.write(f"Dimension fija: {dim}")
lb = st.sidebar.number_input("Limite inferior", value=float(cfg["lb"]),
                             key=f"lb_{nombre}")
ub = st.sidebar.number_input("Limite superior", value=float(cfg["ub"]),
                             key=f"ub_{nombre}")

st.sidebar.header("Parametros de WOA")
n_ballenas = st.sidebar.number_input("Numero de ballenas", 2, 1000,
                                     PARAMS_DEFAULT["n_ballenas"])
max_iter = st.sidebar.number_input("Iteraciones", 1, 5000,
                                   PARAMS_DEFAULT["max_iter"])
a_inicial = st.sidebar.number_input("a inicial (baja a 0)", 0.1, 10.0,
                                    PARAMS_DEFAULT["a_inicial"], step=0.5)
b = st.sidebar.number_input("b (forma de la espiral)", 0.0, 10.0,
                            PARAMS_DEFAULT["b"], step=0.5)
p_umbral = st.sidebar.slider("Umbral p (rodear vs espiral)", 0.0, 1.0,
                             PARAMS_DEFAULT["p_umbral"], 0.05)
seed = st.sidebar.number_input("Semilla (reproducibilidad)", 0, 10**6, 0)

params = dict(n_ballenas=int(n_ballenas), max_iter=int(max_iter),
              a_inicial=a_inicial, b=b, p_umbral=p_umbral)

if lb >= ub:
    st.error("El limite inferior debe ser menor que el superior.")
    st.stop()

st.sidebar.caption("Colores de las ballenas en las animaciones: "
                   ":blue[azul = rodear], :orange[naranja = buscar], "
                   ":green[verde = espiral], gris = posicion inicial.")

tab1, tab_pp, tab2, tab3, tab4, tab5 = st.tabs(
    ["Una ejecucion", "Paso a paso", "Comparar (visual)", "Experimento",
     "Sesgo al centro", "Como funciona"])


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
    return woa(funcion_desplazada(nom, s), lb, ub, d, seed=seed,
               guardar_posiciones=True, n_ballenas=n_ballenas,
               max_iter=max_iter, a_inicial=a_inicial, b=b, p_umbral=p_umbral)


def armar_casos(nom, lb, ub, seed, configs):
    """configs: tupla de (params_dict_como_tupla, desplazamiento, titulo)."""
    casos = []
    for p_t, s, titulo in configs:
        p = dict(p_t)
        res = corrida(nom, 2, lb, ub, seed, s, **p)
        casos.append(dict(f=funcion_desplazada(nom, s), lb=lb, ub=ub, res=res,
                          optimo=FUNCIONES[nom]["optimo_x"](2) + s,
                          titulo=titulo))
    return casos


@st.cache_data(show_spinner=False)
def gif_cacheado(nom, lb, ub, seed, configs):
    return visual.gif_paneles(armar_casos(nom, lb, ub, seed, configs))


def mostrar(fig):
    st.pyplot(fig)
    plt.close(fig)


# ----------------------------- Una ejecucion -------------------------------
with tab1:
    if st.button("Ejecutar WOA", type="primary"):
        res = woa(cfg["f"], lb, ub, int(dim), seed=int(seed),
                  guardar_posiciones=True, **params)
        st.session_state["res"] = (res, nombre, int(dim), lb, ub)

    if "res" in st.session_state:
        res, nom_r, dim_r, lb_r, ub_r = st.session_state["res"]
        cfg_r = FUNCIONES[nom_r]
        x_opt = cfg_r["optimo_x"](dim_r)
        c1, c2, c3 = st.columns(3)
        c1.metric("Mejor fitness", f"{res['mejor_f']:.3e}")
        c2.metric("Error vs optimo", f"{abs(res['mejor_f'] - cfg_r['optimo_f']):.3e}")
        c3.metric("Distancia a x* real",
                  f"{np.linalg.norm(res['mejor_x'] - x_opt):.3e}")
        st.write(f"Funcion: {nom_r} | dim = {dim_r} | mejor x encontrado:")
        st.code(np.array2string(res["mejor_x"], precision=6), language=None)

        col_a, col_b = st.columns(2)
        with col_a:
            fig, ax = plt.subplots(figsize=(5, 4.5))
            ax.semilogy(res["curva"] + 1e-300)
            ax.set_xlabel("Iteracion"); ax.set_ylabel("Mejor fitness (log)")
            ax.set_title("Convergencia"); ax.grid(alpha=.3)
            mostrar(fig)
        with col_b:
            if dim_r == 2:
                it = st.slider("Iteracion a visualizar", 0,
                               len(res["posiciones"]) - 1, 0)
                caso = dict(f=cfg_r["f"], lb=lb_r, ub=ub_r, res=res,
                            optimo=x_opt, titulo="Posicion de las ballenas")
                mostrar(visual.figura_paneles(
                    [caso], it / max(1, len(res["posiciones"]) - 1)))
            else:
                fig, ax = plt.subplots(figsize=(5, 4.5))
                idx = np.arange(dim_r)
                ax.bar(idx - 0.2, res["mejor_x"], 0.4, label="encontrado")
                ax.bar(idx + 0.2, x_opt, 0.4, label="optimo real")
                ax.set_xlabel("Variable i"); ax.legend()
                ax.set_title("Mejor solucion vs optimo")
                mostrar(fig)
        st.subheader("Que regla uso cada ballena en cada momento")
        mostrar(visual.figura_reglas(
            [dict(res=res, titulo=f"{nom_r}, dim {dim_r}")], [a_inicial]))
    else:
        st.info("Ajusta los parametros a la izquierda y pulsa Ejecutar WOA.")

# ------------------------------- Paso a paso --------------------------------
@st.cache_data(show_spinner=False)
def corrida_detallada(nom, lb, ub, seed, p_t):
    return paso_a_paso.woa_detallado(FUNCIONES[nom]["f"], lb, ub, 2,
                                     seed=seed, **dict(p_t))


with tab_pp:
    st.write("Congela **una ballena en una iteracion** y muestra con los "
             "numeros reales como decidio su movimiento. Usa la funcion, los "
             "parametros y la semilla de la barra lateral.")
    if cfg["dim"] is None:
        st.caption(f"{nombre} es de n dimensiones; aqui se usa en 2D para "
                   "poder dibujarla. Las formulas son iguales en n "
                   "dimensiones (se aplican a cada coordenada).")
    if params["n_ballenas"] * params["max_iter"] > 200_000:
        st.warning("Demasiadas ballenas x iteraciones para el paso a paso. "
                   "Reduce alguno de los dos en la barra lateral.")
    else:
        p_t = tuple(sorted(params.items()))
        det = corrida_detallada(nombre, lb, ub, int(seed), p_t)
        iters = det["iteraciones"]
        T, N = len(iters), params["n_ballenas"]
        # Si cambian los parametros, reiniciar la posicion de la lupa
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
        c1.slider("Iteracion t", 0, T - 1, key="pp_t")
        c2.number_input("Ballena #", 0, N - 1, key="pp_i")
        b1, b2, b3, b4, b5 = st.columns([1, 1, 1, 1.4, 1.4])
        b1.button("< Ballena", on_click=mover, kwargs=dict(di=-1))
        b2.button("Ballena >", on_click=mover, kwargs=dict(di=1))
        b3.button("Iteracion >", on_click=mover, kwargs=dict(dt=1))
        b4.selectbox("Buscar ejemplo de", [0, 1, 2], key="pp_regla",
                     format_func=lambda k: paso_a_paso.NOMBRES[k].capitalize(),
                     label_visibility="collapsed")
        b5.button("Siguiente ejemplo", on_click=ir_a_regla)

        it = iters[st.session_state.pp_t]
        d = it["ballenas"][st.session_state.pp_i]
        cuenta = np.bincount([x["regla"] for x in it["ballenas"]],
                             minlength=3)
        st.caption(f"En esta iteracion: a = {it['a']:.3f} | rodear "
                   f"{cuenta[0]}, buscar {cuenta[1]}, espiral {cuenta[2]} | "
                   f"presa: f = {it['presa_f']:.3e}"
                   + (f" -> mejoro a {it['nueva_presa_f']:.3e} (ballena "
                      f"#{it['i_mejor']})" if it["mejoro"] else
                      " (no mejoro en esta iteracion)"))

        col_a, col_b = st.columns([1.1, 1])
        with col_a:
            zoom = st.toggle("Acercar al movimiento", value=True)
            mostrar(paso_a_paso.figura_movimiento(cfg["f"], lb, ub, it, d,
                                                  b, zoom))
            st.caption("La **linea punteada** son todos los lugares a los "
                       "que pudo llegar esta ballena con los mismos C y D si "
                       "solo cambiara A (o l en la espiral). Muestra que el "
                       "movimiento ocurre sobre una linea, no en cualquier "
                       "direccion.")
        with col_b:
            st.markdown(paso_a_paso.explicacion(
                it, d, params["max_iter"], a_inicial, b, p_umbral))
        mostrar(paso_a_paso.figura_decisiones(it, d, b, p_umbral, a_inicial))

# ---------------------------- Comparar (visual) -----------------------------
COMPARAR_DEFAULTS = {"a_inicial": (1.0, 3.0), "n_ballenas": (10, 100),
                     "max_iter": (30, 300), "b": (0.5, 2.0),
                     "p_umbral": (0.2, 0.8)}
QUE_OBSERVAR = {
    "a_inicial": "Con `a` mas grande, |A| >= 1 dura mas tiempo: la franja "
                 "**naranja (buscar)** se extiende y las ballenas siguen "
                 "dispersas por mas iteraciones. Mas exploracion, pero menos "
                 "tiempo para refinar. Fijate cuando la linea punteada a(t) "
                 "cruza a = 1: a partir de ahi ya no hay naranja.",
    "n_ballenas": "Con mas ballenas el dominio queda cubierto desde el "
                  "inicio, por eso es mas facil que alguna caiga cerca del "
                  "optimo. El costo: cada iteracion evalua f mas veces.",
    "max_iter": "La forma de a(t) es la misma, pero estirada: con mas "
                "iteraciones hay mas pasos de exploracion *y* de "
                "refinamiento. Con muy pocas, las ballenas no alcanzan a "
                "juntarse sobre el optimo.",
    "b": "b cambia que tan abierta es la espiral (puntos **verdes**). Con b "
         "grande, los saltos en espiral son mas largos alrededor de la presa.",
    "p_umbral": "p_umbral decide la proporcion entre **verde (espiral)** y "
                "azul/naranja. Con p_umbral bajo casi todo es espiral; con "
                "p_umbral alto casi nunca hay espiral y la exploracion "
                "(naranja) tiene mas peso al inicio.",
}

with tab2:
    st.write("Corre WOA **dos veces con la misma semilla**, cambiando solo UN "
             "parametro, y muestra lado a lado como se mueven las ballenas. "
             "Todo lo demas toma los valores de la barra lateral.")
    if cfg["dim"] is None:
        st.caption(f"{nombre} es de n dimensiones; para poder dibujarla, aqui "
                   "se resuelve en 2 dimensiones.")
    c1, c2, c3 = st.columns(3)
    par_c = c1.selectbox("Parametro a comparar", list(COMPARAR_DEFAULTS),
                         key="par_c")
    vA0, vB0 = COMPARAR_DEFAULTS[par_c]
    es_entero = par_c in ("n_ballenas", "max_iter")
    paso = 1 if es_entero else 0.1
    vA = c2.number_input("Valor A", value=vA0, step=paso, key=f"vA_{par_c}")
    vB = c3.number_input("Valor B", value=vB0, step=paso, key=f"vB_{par_c}")

    def config(v):
        p = {**params, par_c: int(v) if es_entero else float(v)}
        return (tuple(sorted(p.items())), 0.0, f"{par_c} = {v}")

    configs = (config(vA), config(vB))
    casos = armar_casos(nombre, lb, ub, int(seed), configs)

    st.info(QUE_OBSERVAR[par_c])
    modo = st.radio("Vista", ["Animacion", "Pausar en un momento"],
                    horizontal=True, key="modo_c")
    if modo == "Animacion":
        with st.spinner("Generando animacion..."):
            st.image(gif_cacheado(nombre, lb, ub, int(seed), configs),
                     width="stretch")
    else:
        frac = st.slider("% del recorrido", 0, 100, 10, key="frac_c") / 100
        mostrar(visual.figura_paneles(casos, frac))

    st.subheader("Que regla usan las ballenas a lo largo del tiempo")
    mostrar(visual.figura_reglas(casos, [dict(c[0])["a_inicial"]
                                         for c in configs]))
    st.subheader("Exploracion vs explotacion y convergencia")
    mostrar(visual.figura_diversidad_convergencia(casos))
    st.caption("Esto es UNA corrida en 2D, sirve para ver el mecanismo. Para "
               "conclusiones con estadistica usa la pestana Experimento "
               "(muchas corridas).")

# ------------------------------- Experimento --------------------------------
with tab3:
    st.write("Varia UN parametro, deja los demas como en la barra lateral, y "
             "repite cada valor varias veces (WOA es aleatorio).")
    c1, c2, c3 = st.columns(3)
    par = c1.selectbox("Parametro a variar",
                       ["n_ballenas", "max_iter", "a_inicial", "b",
                        "p_umbral"] + (["dim"] if cfg["dim"] is None else []))
    sugeridos = {"n_ballenas": "10, 30, 50, 100", "max_iter": "50, 100, 200, 500",
                 "a_inicial": "1, 2, 3", "b": "0.5, 1, 2",
                 "p_umbral": "0.2, 0.5, 0.8", "dim": "2, 5, 10, 30"}
    texto = c2.text_input("Valores (separados por coma)", sugeridos[par],
                          key=f"vals_{par}")
    n_corridas = c3.number_input("Corridas por valor", 2, 200, 30)

    if st.button("Correr experimento"):
        try:
            valores = [float(v) for v in texto.split(",") if v.strip()]
        except ValueError:
            st.error("Valores no validos."); st.stop()
        if par in ("n_ballenas", "max_iter", "dim"):
            valores = [int(v) for v in valores]
        fijos = {k: v for k, v in params.items() if k != par}
        with st.spinner("Corriendo..."):
            df, fin, cur = barrido(nombre, par, valores,
                                   n_corridas=int(n_corridas),
                                   dim=int(dim), lb=lb, ub=ub, **fijos)
        st.session_state["exp"] = (df, fin, cur, par, nombre)

    if "exp" in st.session_state:
        df, fin, cur, par_r, nom_r = st.session_state["exp"]
        st.subheader(f"{nom_r}: efecto de {par_r}")
        st.dataframe(df.style.format({c: "{:.3e}" for c in df.columns[1:-1]}))
        vals = list(fin)
        col_a, col_b = st.columns(2)
        with col_a:
            fig, ax = plt.subplots(figsize=(5.5, 4))
            ax.boxplot([fin[v] for v in vals], tick_labels=[str(v) for v in vals])
            ax.set_yscale("symlog", linthresh=1e-12)
            ax.set_xlabel(par_r); ax.set_ylabel("Mejor fitness final")
            ax.set_title("Distribucion de resultados finales")
            mostrar(fig)
        with col_b:
            fig, ax = plt.subplots(figsize=(5.5, 4))
            for v in vals:
                ax.semilogy(np.mean(cur[v], axis=0) + 1e-300, label=f"{par_r}={v}")
            ax.set_xlabel("Iteracion"); ax.set_ylabel("Fitness medio (log)")
            ax.legend(fontsize=8); ax.set_title("Convergencia media")
            mostrar(fig)
        buf = io.StringIO(); df.to_csv(buf, index=False)
        st.download_button("Descargar tabla (CSV)", buf.getvalue(),
                           f"{nom_r}_{par_r}.csv", "text/csv")

# ------------------------------ Sesgo al centro -----------------------------
with tab4:
    st.write("Prueba: tomar **la misma funcion** y solo moverla de lugar, "
             "f(x - s). La dificultad es identica; lo unico que cambia es "
             "donde esta el optimo. Si WOA fuera imparcial, el resultado "
             "deberia ser parecido.")
    opt0 = cfg["optimo_x"](2)
    s_max = float(min(ub - opt0.max(), opt0.min() - lb))
    if s_max <= 0.01:
        st.warning("Con estos limites no cabe un desplazamiento del optimo.")
        s_max = 0.01
    s = st.slider("Desplazamiento s (en cada eje)", 0.0, round(s_max, 2),
                  round(min(0.3 * ub, s_max), 2), key=f"s_{nombre}")

    configs_s = ((tuple(sorted(params.items())), 0.0, "Original"),
                 (tuple(sorted(params.items())), s,
                  f"Desplazada s = {s:g}"))
    casos_s = armar_casos(nombre, lb, ub, int(seed), configs_s)
    st.info("Fijate a donde se juntan las ballenas en la funcion desplazada "
            "comparado con la estrella roja (el optimo real). La causa "
            "principal: en las reglas de rodear y buscar se usa `C * X*`, "
            "con C aleatorio en [0, 2], y multiplicar por un numero tiende "
            "a jalar los puntos hacia el 0.")
    modo_s = st.radio("Vista", ["Animacion", "Pausar en un momento"],
                      horizontal=True, key="modo_s")
    if modo_s == "Animacion":
        with st.spinner("Generando animacion..."):
            st.image(gif_cacheado(nombre, lb, ub, int(seed), configs_s),
                     width="stretch")
    else:
        frac = st.slider("% del recorrido", 0, 100, 30, key="frac_s") / 100
        mostrar(visual.figura_paneles(casos_s, frac))

    st.subheader(f"Con estadistica: {int(dim)} dimensiones, varias corridas")
    n_s = st.number_input("Corridas", 2, 100, 20, key="n_s")
    if st.button("Correr comparacion"):
        d = int(dim)
        filas, datos = [], {}
        with st.spinner("Corriendo..."):
            for etiqueta, sv in (("Original", 0.0), (f"Desplazada s={s:g}", s)):
                f_s = funcion_desplazada(nombre, sv)
                opt = cfg["optimo_x"](d) + sv
                fin, dist_opt, dist_0 = [], [], []
                for k in range(int(n_s)):
                    r = woa(f_s, lb, ub, d, seed=k, **params)
                    fin.append(r["mejor_f"])
                    dist_opt.append(np.linalg.norm(r["mejor_x"] - opt))
                    dist_0.append(np.linalg.norm(r["mejor_x"]))
                datos[etiqueta] = np.array(fin)
                filas.append(dict(caso=etiqueta, mediana=np.median(fin),
                                  media=np.mean(fin), peor=np.max(fin),
                                  dist_media_al_optimo=np.mean(dist_opt),
                                  dist_media_al_origen=np.mean(dist_0)))
        st.session_state["sesgo"] = (pd.DataFrame(filas), datos, nombre, d)

    if "sesgo" in st.session_state:
        df_s, datos, nom_s, d_s = st.session_state["sesgo"]
        st.write(f"{nom_s}, dimension {d_s}")
        st.dataframe(df_s.style.format({c: "{:.3e}" for c in df_s.columns[1:]}))
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.boxplot(list(datos.values()), tick_labels=list(datos))
        ax.set_yscale("symlog", linthresh=1e-12)
        ax.set_ylabel("Mejor fitness final")
        ax.set_title("Misma funcion, distinto lugar del optimo")
        mostrar(fig)

# ------------------------------ Como funciona -------------------------------
with tab5:
    st.markdown(f"""
**Idea.** Cada ballena es una solucion candidata. La mejor solucion encontrada
hasta ahora es la *presa* X*. En cada iteracion cada ballena se mueve segun:

- `a` baja linealmente de {a_inicial} a 0 con las iteraciones.
- `A = 2a r1 - a` (en [-a, a]) y `C = 2 r2` (en [0, 2]), con r1, r2 aleatorios en [0, 1].
- `p` aleatorio en [0, 1] y `l` aleatorio en [-1, 1].

| Condicion | Movimiento | Tipo | Color |
|---|---|---|---|
| p < {p_umbral} y abs(A) < 1 | `X = X* - A * abs(C X* - X)` (rodear la presa) | Explotacion | azul |
| p < {p_umbral} y abs(A) >= 1 | `X = Xrand - A * abs(C Xrand - X)` (ir hacia otra ballena al azar) | Exploracion | naranja |
| p >= {p_umbral} | `X = abs(X* - X) * exp(b l) * cos(2 pi l) + X*` (espiral, b = {b}) | Explotacion | verde |

Al inicio `a` es grande, abs(A) >= 1 es frecuente y domina la exploracion.
Al final `a` tiende a 0, abs(A) < 1 y domina la explotacion.

Referencia: Mirjalili y Lewis (2016), *The Whale Optimization Algorithm*,
Advances in Engineering Software 95, 51-67.
""")
