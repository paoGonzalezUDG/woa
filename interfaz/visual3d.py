"""
Simulacion 3D interactiva (Plotly) de las ballenas sobre la funcion.

La funcion de 2 variables se dibuja como un terreno (superficie) y las
ballenas como puntos encima. Se puede girar, hacer zoom y reproducir la
animacion vuelta por vuelta. Usa los mismos colores que el resto de la app.
"""
import numpy as np
import plotly.graph_objects as go

from interfaz.visual import COLOR_INICIAL, COLORES_REGLAS, NOMBRES_REGLAS

REGLA_CORTA = ["rodear", "buscar", "espiral"]


def _altura(v, log):
    """Altura del dibujo. Con log, los picos enormes se aplanan (todas las
    funciones valen >= 0, asi que log10(1 + v) siempre existe)."""
    return np.log10(1 + v) if log else v


def figura_3d(f, lb, ub, res, optimo, log=True, n_cuadros=80, ms=150,
              n_malla=100):
    """res: resultado de woa(..., guardar_posiciones=True) en 2 variables."""
    g = np.linspace(lb, ub, n_malla)
    Z = np.array([[f(np.array([x, y])) for x in g] for y in g])
    H = _altura(Z, log)
    elevar = 0.015 * (H.max() - H.min())   # para que no se escondan debajo
    T = len(res["posiciones"]) - 1
    cuadros = np.unique(np.linspace(0, T, min(n_cuadros, T + 1))
                        .round().astype(int))

    def ballenas(t):
        P = np.clip(res["posiciones"][t][:, :2], lb, ub)
        vals = np.array([f(p) for p in P])
        if t == 0:
            colores, reglas = [COLOR_INICIAL] * len(P), ["inicio"] * len(P)
        else:
            r = res["reglas"][t - 1]
            colores = list(COLORES_REGLAS[r])
            reglas = [REGLA_CORTA[k] for k in r]
        texto = [f"Ballena #{i} ({reglas[i]})<br>valor = {vals[i]:.2e}"
                 for i in range(len(P))]
        return go.Scatter3d(
            x=P[:, 0], y=P[:, 1], z=_altura(vals, log) + elevar,
            mode="markers", text=texto, hoverinfo="text", showlegend=False,
            marker=dict(size=5, color=colores,
                        line=dict(width=1, color="black")))

    def presa(t):
        p = res["presas"][t][:2]
        v = f(p)
        return go.Scatter3d(
            x=[p[0]], y=[p[1]], z=[_altura(v, log) + 2 * elevar],
            mode="markers", name="mejor ballena (presa)",
            text=[f"Mejor ballena<br>valor = {v:.2e}"], hoverinfo="text",
            marker=dict(size=9, color="yellow", symbol="x",
                        line=dict(width=2, color="black")))

    def titulo(t):
        if t == 0:
            extra = "inicio: ballenas al azar"
        else:
            c = np.bincount(res["reglas"][t - 1], minlength=3)
            extra = f"rodear {c[0]} · buscar {c[1]} · espiral {c[2]}"
        return (f"Vuelta {t} de {T} · mejor valor = {res['curva'][t]:.2e}"
                f" · {extra}")

    superficie = go.Surface(
        x=g, y=g, z=H, opacity=0.9, showscale=False,
        colorscale=[[0, "#f4f4f4"], [1, "#8a8a8a"]],   # bajo = claro
        hovertemplate="x = %{x:.2f}<br>y = %{y:.2f}<extra></extra>")
    v_opt = f(np.asarray(optimo))
    minimo = go.Scatter3d(
        x=[optimo[0]], y=[optimo[1]], z=[_altura(v_opt, log) + 2 * elevar],
        mode="markers", name="mínimo real", hoverinfo="text",
        text=[f"Mínimo real ({optimo[0]:g}, {optimo[1]:g})"],
        marker=dict(size=7, color="red", symbol="diamond",
                    line=dict(width=1, color="black")))
    # Entradas solo para la leyenda de colores (no se dibujan)
    leyenda = [go.Scatter3d(x=[None], y=[None], z=[None], mode="markers",
                            name=n, marker=dict(size=6, color=c))
               for n, c in zip(NOMBRES_REGLAS, COLORES_REGLAS)]

    fig = go.Figure(data=[superficie, ballenas(0), presa(0), minimo]
                    + leyenda)
    # Cada cuadro solo actualiza las ballenas (traza 1) y la presa (traza 2)
    fig.frames = [go.Frame(data=[ballenas(t), presa(t)], traces=[1, 2],
                           name=str(t), layout=go.Layout(title_text=titulo(t)))
                  for t in cuadros]

    reproducir = dict(frame=dict(duration=ms, redraw=True), fromcurrent=True,
                      transition=dict(duration=0))
    pausar = dict(frame=dict(duration=0, redraw=False), mode="immediate",
                  transition=dict(duration=0))
    fig.update_layout(
        title=dict(text=titulo(0), x=0.5, xanchor="center", font=dict(size=14)),
        height=680, margin=dict(l=0, r=0, t=50, b=12),
        legend=dict(orientation="h", y=1.0, x=0.5, xanchor="center",
                    yanchor="bottom", bgcolor="rgba(255,255,255,0.7)"),
        scene=dict(
            domain=dict(y=[0.12, 1]),     # deja espacio abajo para los controles
            xaxis_title="x", yaxis_title="y",
            zaxis_title="altura (log)" if log else "valor de la función",
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.6),
            camera=dict(eye=dict(x=1.2, y=-1.2, z=0.85))),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.02, y=0.0,
            xanchor="left", yanchor="bottom", showactive=False,
            buttons=[dict(label="▶ Reproducir", method="animate",
                          args=[None, reproducir]),
                     dict(label="⏸ Pausa", method="animate",
                          args=[[None], pausar])])],
        sliders=[dict(
            x=0.22, y=0.0, len=0.76, xanchor="left", yanchor="bottom",
            currentvalue=dict(prefix="Vuelta: ", font=dict(color="#333")),
            pad=dict(t=0, b=0), ticklen=0,
            font=dict(color="rgba(0,0,0,0)"),   # oculta los 80 numeritos
            steps=[dict(method="animate", label=str(t),
                        args=[[str(t)], dict(mode="immediate",
                                             frame=dict(duration=0,
                                                        redraw=True),
                                             transition=dict(duration=0))])
                   for t in cuadros])])
    return fig
