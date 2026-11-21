"""
Lectura y graficas (Plotly) del experimento de combinaciones
(resultados/8_combinaciones/resumen.csv): 81 combinaciones de reparto
(ballenas x vueltas, mismo esfuerzo), a, b y p; 25 corridas cada una.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CLAVES = ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"]
AZUL = "#9ecae1"


def leer(ruta):
    df = pd.read_csv(ruta)
    df["reparto"] = (df["n_ballenas"].astype(int).astype(str) + "×"
                     + df["max_iter"].astype(int).astype(str))
    return df


def es_default(df, por_defecto):
    m = np.ones(len(df), bool)
    for k in CLAVES:
        m &= np.isclose(df[k], por_defecto[k])
    return m


def texto(fila):
    return (f"{fila['reparto']}, a={fila['a_inicial']:g}, b={fila['b']:g}, "
            f"p={fila['p_umbral']:g}")


def de_funcion(df, nombre):
    return df[df["funcion"] == nombre].sort_values("lugar")


def tabla(d, por_defecto, n=10):
    """Las n mejores + la de por defecto (si no esta entre ellas)."""
    top = d.head(n)
    dfl = d[es_default(d, por_defecto)]
    t = pd.concat([top, dfl]).drop_duplicates(subset=CLAVES)
    t = t.assign(por_defecto=es_default(t, por_defecto))
    return t[["lugar", "reparto", "a_inicial", "b", "p_umbral", "mediana",
              "media", "peor", "tiempo_medio_s", "por_defecto"]]


# Para "que ajuste importa": nombre visible y columna
AJUSTES = {"Ballenas × vueltas": "reparto", "a inicial": "a_inicial",
           "b (espiral)": "b", "p (umbral)": "p_umbral"}


def lugar_promedio(d):
    """Para cada ajuste y valor: lugar promedio de las combinaciones que lo
    usan. Menor = ese valor suele quedar mas arriba en la tabla."""
    filas = []
    for nom, col in AJUSTES.items():
        g = d.groupby(col)["lugar"].mean()
        for v, lp in g.items():
            filas.append(dict(ajuste=nom, valor=v if isinstance(v, str)
                              else f"{v:g}", lugar_prom=lp))
    out = pd.DataFrame(filas)
    # cuanto cambia el lugar segun el valor = que tanto importa ese ajuste
    rango = out.groupby("ajuste")["lugar_prom"].agg(lambda s: s.max() - s.min())
    return out, rango


def figura_lugar_promedio(d, por_defecto, total):
    out, rango = lugar_promedio(d)
    fig = make_subplots(rows=1, cols=len(AJUSTES), shared_yaxes=True,
                        horizontal_spacing=0.04,
                        subplot_titles=[f"{a}<br><sub>diferencia: "
                                        f"{rango[a]:.0f} lugares</sub>"
                                        for a in AJUSTES])
    dfl = {"reparto": f"{por_defecto['n_ballenas']}×"
                      f"{por_defecto['max_iter']}",
           "a_inicial": f"{por_defecto['a_inicial']:g}",
           "b": f"{por_defecto['b']:g}", "p_umbral": f"{por_defecto['p_umbral']:g}"}
    for j, (nom, col) in enumerate(AJUSTES.items(), start=1):
        o = out[out.ajuste == nom]
        if col == "reparto":    # ordenar por numero de ballenas
            o = o.assign(_k=o.valor.str.split("×").str[0].astype(int))
            o = o.sort_values("_k")
        mejor = o.lugar_prom.min()
        fig.add_trace(go.Scatter(
            x=o.valor, y=o.lugar_prom, showlegend=False,
            mode="lines+markers+text", line=dict(color="#c7c7c7", width=2),
            marker=dict(size=18, line=dict(color="#555", width=1),
                        color=["#2ca02c" if v == mejor else
                               (AZUL if val == dfl[col] else "white")
                               for v, val in zip(o.lugar_prom, o.valor)]),
            text=[f"{v:.0f}" for v in o.lugar_prom],
            textposition="top center", cliponaxis=False,
            hovertemplate=nom + " = %{x}<br>lugar promedio: %{y:.1f}"
                          "<extra></extra>"), row=1, col=j)
        fig.update_xaxes(type="category", row=1, col=j)
    fig.update_yaxes(range=[total + 3, -3], gridcolor="rgba(0,0,0,0.08)",
                     zeroline=False)
    fig.update_yaxes(title_text="lugar promedio (arriba = mejor)", row=1,
                     col=1)
    fig.update_layout(height=380, margin=dict(l=60, r=20, t=70, b=40),
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color="#222"))
    return fig


def cruce(df, nombres, por_defecto):
    """Filas: la mejor de cada funcion (y la de por defecto); columnas: su
    lugar en cada funcion. Devuelve (DataFrame de lugares, etiquetas)."""
    filas, etiquetas = [], []
    elegidas = []
    for nom in nombres:
        d = de_funcion(df, nom)
        g = d.iloc[0]
        n_emp = int((d.lugar == 1).sum())
        elegidas.append(g)
        etiquetas.append(f"<b>La mejor en {nom}</b>"
                         + (f" (empata con {n_emp - 1})" if n_emp > 1 else "")
                         + f"<br>{texto(g)}")
    g = df[es_default(df, por_defecto)].iloc[0]
    elegidas.append(g)
    etiquetas.append(f"<b>La de por defecto</b><br>{texto(g)}")
    for g in elegidas:
        m = np.ones(len(df), bool)
        for k in CLAVES:
            m &= np.isclose(df[k], g[k])
        sub = df[m].set_index("funcion")["lugar"]
        filas.append([int(sub[nom]) for nom in nombres])
    return pd.DataFrame(filas, columns=nombres), etiquetas


def figura_cruce(df, nombres, por_defecto, total):
    t, etiquetas = cruce(df, nombres, por_defecto)
    fig = go.Figure(go.Heatmap(
        z=t.values, x=nombres, y=etiquetas, zmin=1, zmax=total,
        colorscale="RdYlGn", reversescale=True, showscale=False,
        text=t.values, texttemplate="lugar %{text}",
        textfont=dict(size=14),
        hovertemplate="%{y}<br>Probada en <b>%{x}</b>: queda en el lugar "
                      "%{z} de " + str(total) + "<extra></extra>"))
    fig.update_yaxes(autorange="reversed", automargin=True,
                     title_text="Combinación de ajustes")
    fig.update_xaxes(side="top", title_text="Función donde se probó",
                     title_standoff=4)
    fig.update_layout(height=140 + 62 * len(etiquetas),
                      title=dict(text=f"Lugar que saca cada combinación en "
                                      f"cada función (1 = la mejor, {total} "
                                      f"= la peor)", x=0.5, y=0.99,
                                 font=dict(size=14)),
                      margin=dict(l=10, r=10, t=90, b=10),
                      paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(color="#222"))
    return fig
