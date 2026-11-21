"""
Grafica interactiva (Plotly) con todas las cajas: filas = funciones,
columnas = parametros. Lee resultados/7_panorama/finales.csv (una fila por
corrida), asi que no hay que volver a correr nada.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PARAMS = ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"]
TITULOS = {"n_ballenas": "Ballenas", "max_iter": "Vueltas",
           "a_inicial": "a inicial", "b": "b (espiral)",
           "p_umbral": "p (umbral)"}
AZUL, AZUL_FONDO, ROJO = "#9ecae1", "#deebf7", "#d62728"


def leer(ruta):
    return pd.read_csv(ruta)


def piso_de(valores):
    """Valor donde se dibujan los ceros exactos (log no acepta 0)."""
    pos = valores[valores > 0]
    if len(pos) == 0:
        return 1e-16
    return 10.0 ** (np.floor(np.log10(pos.min())) - 1)


def marcas_log(piso, maximo, n=6):
    """Marcas del eje log: potencias de 10 (unas n) y el piso como "0"."""
    lo = np.log10(piso)
    hi = int(np.ceil(np.log10(max(maximo, piso * 10))))
    paso = max(1, int(np.ceil((hi - lo) / n)))
    ks = [k for k in range(hi, int(lo), -paso) if k - lo >= 0.6 * paso]
    ks = sorted(ks)
    vals = [piso] + [10.0 ** k for k in ks]
    textos = ["0"] + [("1" if k == 0 else f"10<sup>{k}</sup>") for k in ks]
    return vals, textos


def figura_cajas(df, funciones, por_defecto, ver_puntos=False):
    """df: columnas funcion, parametro, valor, corrida, mejor_f.
    por_defecto: dict parametro -> valor por defecto (franja azul)."""
    filas = len(funciones)
    fig = make_subplots(
        rows=filas, cols=len(PARAMS), shared_yaxes="rows",
        horizontal_spacing=0.025, vertical_spacing=0.06 if filas > 1 else 0,
        column_titles=[TITULOS[p] for p in PARAMS], row_titles=funciones)
    for i, nom in enumerate(funciones, start=1):
        d_f = df[df["funcion"] == nom]
        piso = piso_de(d_f["mejor_f"].to_numpy())
        hay_ceros = (d_f["mejor_f"] <= 0).any()
        for j, par in enumerate(PARAMS, start=1):
            d_p = d_f[d_f["parametro"] == par]
            vals = sorted(d_p["valor"].unique())
            etiquetas = [f"{v:g}" for v in vals]
            for v, et in zip(vals, etiquetas):
                y = d_p.loc[d_p["valor"] == v, "mejor_f"].to_numpy()
                es_def = np.isclose(v, por_defecto[par])
                fig.add_trace(go.Box(
                    y=np.maximum(y, piso), x=[et] * len(y),
                    name=f"{TITULOS[par]} = {et}"
                         + (" (por defecto)" if es_def else ""),
                    boxmean=True, boxpoints="all" if ver_puntos else
                    "outliers", jitter=0.4, pointpos=0,
                    fillcolor=AZUL if es_def else "white",
                    line=dict(color="black", width=1.2),
                    marker=dict(color="rgba(0,0,0,0.45)", size=4),
                    showlegend=False,
                    hoverlabel=dict(namelength=-1)),
                    row=i, col=j)
                if es_def:   # franja de fondo: se ve aunque la caja sea 0
                    k = etiquetas.index(et)
                    fig.add_vrect(x0=k - 0.45, x1=k + 0.45, row=i, col=j,
                                  fillcolor=AZUL_FONDO, line_width=0,
                                  layer="below")
            fig.update_xaxes(type="category", categoryorder="array",
                             categoryarray=etiquetas, row=i, col=j)
            if hay_ceros:
                fig.add_hline(y=piso, row=i, col=j, line_dash="dot",
                              line_color="gray", line_width=1)
        fig.update_yaxes(type="log", row=i, col=1,
                         exponentformat="power", showexponent="all",
                         title_text="mejor valor final")
        if hay_ceros:   # el piso se etiqueta "0" en el eje (no encima)
            vals, textos = marcas_log(piso, d_f["mejor_f"].max())
            fig.update_yaxes(tickvals=vals, ticktext=textos, row=i, col=1)
    for j in range(1, len(PARAMS) + 1):
        fig.update_xaxes(title_text="valor probado", row=filas, col=j)
    fig.update_yaxes(type="log", gridcolor="rgba(0,0,0,0.08)")
    fig.update_layout(height=280 * filas + 120 if filas > 1 else 480,
                      margin=dict(l=70, r=40, t=60, b=50),
                      plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color="#222"), boxgap=0.35,
                      hoverlabel=dict(bgcolor="white"))
    return fig
