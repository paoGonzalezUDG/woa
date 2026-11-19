"""
Graficas y animaciones para explicar WOA visualmente (las usa app.py).

Colores fijos en todo el proyecto para las 3 reglas de movimiento:
  azul    = rodear la presa   (explotacion)
  naranja = buscar otra presa (exploracion)
  verde   = espiral           (explotacion)
"""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from PIL import Image

NOMBRES_REGLAS = ["Rodear (explota)", "Buscar (explora)", "Espiral (explota)"]
COLORES_REGLAS = np.array(["#1f77b4", "#ff7f0e", "#2ca02c"])
COLOR_INICIAL = "#bbbbbb"


# --------------------------------------------------------------------------
# Fondo: curvas de nivel de una funcion de 2 variables
# --------------------------------------------------------------------------
def fondo_contorno(ax, f, lb, ub, n=120):
    g = np.linspace(lb, ub, n)
    X, Y = np.meshgrid(g, g)
    Z = np.array([[f(np.array([x, y])) for x in g] for y in g])
    Zl = np.log1p(Z - Z.min())           # log para que se vean los detalles
    ax.contourf(X, Y, Zl, levels=30, cmap="Greys", alpha=0.45)
    ax.contour(X, Y, Zl, levels=15, colors="k", linewidths=0.3, alpha=0.3)
    ax.set_xlim(lb, ub); ax.set_ylim(lb, ub); ax.set_aspect("equal")


def leyenda_reglas(fig):
    h = [Line2D([], [], marker="o", ls="", mfc=c, mec="k", label=n)
         for c, n in zip(COLORES_REGLAS, NOMBRES_REGLAS)]
    h.append(Line2D([], [], marker="o", ls="", mfc=COLOR_INICIAL, mec="k",
                    label="inicio"))
    h.append(Line2D([], [], marker="X", ls="", mfc="yellow", mec="k", ms=10,
                    label="presa X*"))
    h.append(Line2D([], [], marker="*", ls="", mfc="red", mec="k", ms=13,
                    label="optimo real"))
    fig.legend(handles=h, loc="lower center", ncol=6, fontsize=8,
               frameon=False)


def _colores_iter(res, t):
    """Color de cada ballena en la iteracion t segun la regla que la llevo ahi."""
    n = len(res["posiciones"][0])
    if t == 0:
        return np.full(n, COLOR_INICIAL)
    return COLORES_REGLAS[res["reglas"][t - 1]]


def _iter_de_fraccion(res, frac):
    return int(round(frac * (len(res["posiciones"]) - 1)))


# --------------------------------------------------------------------------
# Paneles lado a lado (cada "caso" es una corrida con guardar_posiciones=True)
#   caso = dict(f, lb, ub, res, optimo, titulo)
# --------------------------------------------------------------------------
def _armar_figura(casos):
    fig, axs = plt.subplots(1, len(casos), figsize=(5.2 * len(casos), 5.4))
    axs = np.atleast_1d(axs)
    artistas = []
    for ax, c in zip(axs, casos):
        fondo_contorno(ax, c["f"], c["lb"], c["ub"])
        ax.scatter(*c["optimo"], marker="*", c="red", s=260, edgecolor="k",
                   zorder=5)
        sc = ax.scatter([], [], s=34, edgecolor="k", linewidth=0.5, zorder=3)
        pr = ax.scatter([], [], marker="X", c="yellow", s=150, edgecolor="k",
                        zorder=4)
        txt = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top",
                      fontsize=9, bbox=dict(fc="white", alpha=0.85, lw=0))
        artistas.append((sc, pr, txt))
    leyenda_reglas(fig)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return fig, axs, artistas


def _dibujar_cuadro(casos, axs, artistas, frac):
    for ax, c, (sc, pr, txt) in zip(axs, casos, artistas):
        res = c["res"]
        t = _iter_de_fraccion(res, frac)
        pos = np.clip(res["posiciones"][t], c["lb"], c["ub"])
        sc.set_offsets(pos[:, :2])
        sc.set_facecolors(_colores_iter(res, t))
        pr.set_offsets([res["presas"][t][:2]])
        ax.set_title(c["titulo"], fontsize=11)
        if t == 0:
            linea = "inicio aleatorio"
        else:
            cuenta = np.bincount(res["reglas"][t - 1], minlength=3)
            linea = (f"rodear {cuenta[0]} | buscar {cuenta[1]} | "
                     f"espiral {cuenta[2]}")
        txt.set_text(f"iteracion {t}/{len(res['posiciones']) - 1}\n"
                     f"mejor f = {res['curva'][t]:.2e}\n{linea}")


def figura_paneles(casos, frac):
    """Imagen estatica en un momento del recorrido (frac en [0, 1])."""
    fig, axs, art = _armar_figura(casos)
    _dibujar_cuadro(casos, axs, art, frac)
    return fig


def gif_paneles(casos, n_cuadros=60, ms_por_cuadro=130, dpi=75):
    """Animacion GIF de los paneles. Devuelve los bytes del GIF.
    Los cuadros se toman por fraccion del recorrido, asi dos corridas con
    distinto max_iter avanzan 'al mismo ritmo relativo'."""
    fig, axs, art = _armar_figura(casos)
    fig.set_dpi(dpi)
    cuadros = []
    for frac in np.linspace(0, 1, n_cuadros):
        _dibujar_cuadro(casos, axs, art, frac)
        fig.canvas.draw()
        img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB")
        cuadros.append(img.quantize(colors=128))
    plt.close(fig)
    cuadros += [cuadros[-1]] * 12                 # pausa al final
    buf = io.BytesIO()
    cuadros[0].save(buf, format="GIF", save_all=True,
                    append_images=cuadros[1:], duration=ms_por_cuadro, loop=0)
    return buf.getvalue()


# --------------------------------------------------------------------------
# Graficas de comportamiento a lo largo del tiempo
# --------------------------------------------------------------------------
def figura_reglas(casos, a_iniciales):
    """Fraccion de ballenas que usa cada regla en cada iteracion, con a(t)."""
    fig, axs = plt.subplots(1, len(casos), figsize=(5.2 * len(casos), 3.4),
                            sharey=True)
    axs = np.atleast_1d(axs)
    for ax, c, a0 in zip(axs, casos, a_iniciales):
        R = c["res"]["reglas"]                       # (iter, ballenas)
        T, n = R.shape
        frac = np.stack([(R == k).mean(axis=1) for k in range(3)])
        # suavizado para que la tendencia se lea (ventana ~5% del recorrido)
        w = max(1, T // 20)
        ventana = np.ones(w)
        norma = np.convolve(np.ones(T), ventana, mode="same")  # bordes bien
        frac = np.array([np.convolve(f, ventana, mode="same") / norma
                         for f in frac])
        x = np.linspace(0, 100, T)
        ax.stackplot(x, frac, colors=COLORES_REGLAS, labels=NOMBRES_REGLAS,
                     alpha=0.85)
        ax2 = ax.twinx()
        ax2.plot(x, a0 * (1 - np.arange(T) / T), "k--", lw=1.5, label="a(t)")
        ax2.axhline(1, color="k", lw=0.6, ls=":")
        ax2.set_ylim(0, max(3, a0) * 1.05)
        ax2.set_ylabel("a(t)  (linea punteada: a = 1)", fontsize=8)
        ax.set_xlim(0, 100); ax.set_ylim(0, 1)
        ax.set_xlabel("% del recorrido"); ax.set_title(c["titulo"], fontsize=10)
    axs[0].set_ylabel("Fraccion de ballenas")
    axs[0].legend(loc="lower left", fontsize=7)
    fig.tight_layout()
    return fig


def diversidad(res, lb, ub):
    """Distancia media de las ballenas a su centro, relativa al dominio."""
    return np.array([np.mean(np.linalg.norm(P - P.mean(axis=0), axis=1))
                     for P in res["posiciones"]]) / (ub - lb)


def figura_diversidad_convergencia(casos, colores=("#d62728", "#9467bd")):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 3.6))
    for c, col in zip(casos, colores):
        res = c["res"]
        x = np.linspace(0, 100, len(res["curva"]))
        a1.semilogy(x, diversidad(res, c["lb"], c["ub"]) + 1e-300, color=col,
                    label=c["titulo"])
        a2.semilogy(x, res["curva"] + 1e-300, color=col, label=c["titulo"])
    a1.set_title("Dispersion de las ballenas\n(alta = exploran, baja = explotan)",
                 fontsize=10)
    a1.set_xlabel("% del recorrido"); a1.set_ylabel("distancia media al centro")
    a2.set_title("Convergencia (mejor fitness)", fontsize=10)
    a2.set_xlabel("% del recorrido"); a2.set_ylabel("mejor f (log)")
    for a in (a1, a2):
        a.grid(alpha=.3); a.legend(fontsize=8)
    fig.tight_layout()
    return fig
