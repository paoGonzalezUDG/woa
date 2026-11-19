"""
Version "con lupa" de WOA para la pestana Paso a paso de app.py.

Hace EXACTAMENTE lo mismo que woa.py (mismos numeros aleatorios en el mismo
orden, por eso con la misma semilla da el mismo resultado), pero anota todo
lo que pasa con cada ballena en cada iteracion: r1, r2, A, C, p, l, la regla
elegida, la distancia D y la posicion antes y despues.
"""
import matplotlib.pyplot as plt
import numpy as np

from interfaz import visual

NOMBRES = ["Rodear la presa", "Buscar otra zona", "Espiral"]


def woa_detallado(f, lb, ub, dim, n_ballenas=30, max_iter=200, a_inicial=2.0,
                  b=1.0, p_umbral=0.5, seed=None):
    rng = np.random.default_rng(seed)
    X = rng.uniform(lb, ub, size=(n_ballenas, dim))
    fit = np.array([f(x) for x in X])
    i_mejor = np.argmin(fit)
    mejor_x, mejor_f = X[i_mejor].copy(), fit[i_mejor]

    iteraciones = []
    for t in range(max_iter):
        a = a_inicial * (1 - t / max_iter)
        it = dict(t=t, a=a, X_inicio=X.copy(), presa=mejor_x.copy(),
                  presa_f=float(mejor_f), ballenas=[])
        for i in range(n_ballenas):
            r1, r2 = rng.random(), rng.random()
            A = 2 * a * r1 - a
            C = 2 * r2
            l = rng.uniform(-1, 1)
            p = rng.random()
            d = dict(i=i, r1=r1, r2=r2, A=A, C=C, l=l, p=p,
                     x_antes=X[i].copy(), f_antes=float(fit[i]), j=None)
            if p < p_umbral:
                if abs(A) < 1:
                    objetivo = mejor_x.copy()
                    D = np.abs(C * mejor_x - X[i])
                    X[i] = mejor_x - A * D
                    d["regla"] = 0
                else:
                    j = int(rng.integers(n_ballenas))
                    objetivo = X[j].copy()
                    D = np.abs(C * objetivo - X[i])
                    X[i] = objetivo - A * D
                    d["regla"], d["j"] = 1, j
            else:
                objetivo = mejor_x.copy()
                D = np.abs(mejor_x - X[i])
                X[i] = D * np.exp(b * l) * np.cos(2 * np.pi * l) + mejor_x
                d["regla"] = 2
            d.update(objetivo=objetivo, D=D, x_nuevo=X[i].copy())
            it["ballenas"].append(d)

        X = np.clip(X, lb, ub)
        fit = np.array([f(x) for x in X])
        for d in it["ballenas"]:
            d["x_final"] = X[d["i"]].copy()
            d["f_despues"] = float(fit[d["i"]])
        i_mejor = np.argmin(fit)
        it["mejoro"] = bool(fit[i_mejor] < mejor_f)
        if it["mejoro"]:
            mejor_f, mejor_x = fit[i_mejor], X[i_mejor].copy()
        it["i_mejor"] = int(i_mejor)
        it["nueva_presa"], it["nueva_presa_f"] = mejor_x.copy(), float(mejor_f)
        iteraciones.append(it)

    return dict(iteraciones=iteraciones, mejor_x=mejor_x,
                mejor_f=float(mejor_f))


def buscar_ejemplo(iteraciones, regla, t, i):
    """Siguiente (t, i) despues de (t, i) donde una ballena use 'regla'."""
    n = len(iteraciones[0]["ballenas"])
    total = len(iteraciones) * n
    k0 = t * n + i
    for paso in range(1, total + 1):
        k = (k0 + paso) % total
        tt, ii = divmod(k, n)
        if iteraciones[tt]["ballenas"][ii]["regla"] == regla:
            return tt, ii
    return None


# --------------------------------------------------------------------------
# Texto con los numeros reales de este paso
# --------------------------------------------------------------------------
def v(x):
    return "(" + ", ".join(f"{c:.3f}" for c in x) + ")"


def explicacion(it, d, max_iter, a_inicial, b, p_umbral):
    """Texto (markdown) con las cuentas de esta ballena, en lenguaje sencillo."""
    a, A, C, p, l, t = it["a"], d["A"], d["C"], d["p"], d["l"], it["t"]
    L = []
    L.append(f"**1. El reloj.** Vamos en la vuelta {t} de {max_iter}. El reloj "
             f"empieza en {a_inicial:g} y baja hasta 0:  \n"
             f"`a = {a_inicial:g} × (1 − {t}/{max_iter}) = {a:.3f}`")
    L.append("**2. Los números al azar de esta ballena.**  \n"
             f"`r1 = {d['r1']:.3f}` → `A = 2·a·r1 − a = {A:.3f}`  \n"
             f"`r2 = {d['r2']:.3f}` → `C = 2·r2 = {C:.3f}`  \n"
             f"`p = {p:.3f}` · `l = {l:.3f}`")
    if p < p_umbral:
        L.append(f"**3. ¿Espiral?** `p = {p:.3f}` es menor que {p_umbral:g}, "
                 "así que **no**: toca rodear o buscar.")
        if d["regla"] == 0:
            L.append(f"**4. ¿Rodear o buscar?** `|A| = {abs(A):.3f}` es menor "
                     "que 1 → **rodear la presa**: se acerca a la mejor "
                     "ballena.")
            L.append("**5. Las cuentas:**\n```text\n"
                     f"Ballena antes   X  = {v(d['x_antes'])}\n"
                     f"Presa (mejor)   X* = {v(d['objetivo'])}\n"
                     f"Distancia       D  = |C·X* − X| = {v(d['D'])}\n"
                     f"Nueva posición     = X* − A·D   = {v(d['x_nuevo'])}\n"
                     "```")
            L.append("Como `|A|` es menor que 1, el paso es más corto que la "
                     "distancia: la ballena cae **cerca de la presa**.")
        else:
            L.append(f"**4. ¿Rodear o buscar?** `|A| = {abs(A):.3f}` es 1 o "
                     "más → **buscar otra zona**: en vez de seguir a la "
                     f"mejor, sigue a la ballena #{d['j']}, elegida al azar.")
            L.append("**5. Las cuentas:**\n```text\n"
                     f"Ballena antes   X     = {v(d['x_antes'])}\n"
                     f"Ballena al azar Xrand = {v(d['objetivo'])}\n"
                     f"Distancia       D     = |C·Xrand − X| = {v(d['D'])}\n"
                     f"Nueva posición        = Xrand − A·D   = "
                     f"{v(d['x_nuevo'])}\n```")
            L.append("Como `|A|` es 1 o más, el paso es más largo que la "
                     "distancia: la ballena **se puede pasar de largo** y caer "
                     "en una zona nueva. Así explora.")
    else:
        g = np.exp(b * l) * np.cos(2 * np.pi * l)
        L.append(f"**3. ¿Espiral?** `p = {p:.3f}` es {p_umbral:g} o más, así "
                 "que **sí: espiral** alrededor de la presa. Aquí `A` y `C` "
                 "no se usan.")
        L.append("**4. Las cuentas:**\n```text\n"
                 f"Ballena antes   X  = {v(d['x_antes'])}\n"
                 f"Presa (mejor)   X* = {v(d['objetivo'])}\n"
                 f"Distancia       D  = |X* − X| = {v(d['D'])}\n"
                 f"Factor             = e^(b·l)·cos(2π·l) = {g:.3f}\n"
                 f"Nueva posición     = X* + D·factor = {v(d['x_nuevo'])}\n"
                 "```")
        L.append("El factor sube y baja según `l` (gráfica de abajo a la "
                 "derecha), así que la ballena puede quedar de un lado o del "
                 "otro de la presa.")
        L.append("**Dato curioso:** aunque se llama espiral, la ballena cae "
                 "sobre una **línea recta** que pasa por la presa (la línea "
                 "punteada), porque `l` es un solo número para todas las "
                 "coordenadas. La \"espiral\" está en cómo sube y baja el "
                 "factor.")
    if not np.allclose(d["x_nuevo"], d["x_final"]):
        L.append("**Se salió de la zona de búsqueda**, así que la regresamos "
                 f"a la orilla: `{v(d['x_final'])}`")
    mejoro = d["f_despues"] < d["f_antes"]
    nueva = it["mejoro"] and it["i_mejor"] == d["i"]
    L.append(f"**¿Le fue mejor?** Su valor pasó de `{d['f_antes']:.2e}` a "
             f"`{d['f_despues']:.2e}`: " + ("**mejoró**." if mejoro
                                            else "**empeoró**.")
             + (" Además, se volvió la **nueva mejor ballena** (la presa)."
                if nueva else ""))
    return "\n\n".join(L)


# --------------------------------------------------------------------------
# Graficas
# --------------------------------------------------------------------------
def figura_movimiento(f, lb, ub, it, d, b, zoom=True):
    """Mapa: ballena antes -> despues, presa, objetivo, y TODAS las posiciones
    a las que pudo llegar con esos mismos numeros (linea punteada)."""
    a, regla, D, obj = it["a"], d["regla"], d["D"], d["objetivo"]
    col = visual.COLORES_REGLAS[regla]
    fig, ax = plt.subplots(figsize=(6, 6))
    visual.fondo_contorno(ax, f, lb, ub)
    otras = np.delete(it["X_inicio"], d["i"], axis=0)
    ax.scatter(otras[:, 0], otras[:, 1], s=14, c="#999999", alpha=0.6,
               label="otras ballenas")

    # Zona posible con los mismos C y D variando A (o l en la espiral)
    zonas = []
    if regla == 2:
        ls = np.linspace(-1, 1, 300)
        g = np.exp(b * ls) * np.cos(2 * np.pi * ls)
        zonas.append(obj + np.outer(g, D))
        ax.plot(zonas[0][:, 0], zonas[0][:, 1], ":", color=col, lw=2,
                label="lugares posibles")
    else:
        if regla == 0:
            tramos = [np.linspace(-min(a, 1), min(a, 1), 50)]
        else:
            tramos = [np.linspace(-a, -1, 50), np.linspace(1, a, 50)]
        for k, As in enumerate(tramos):
            zonas.append(obj - np.outer(As, D))
            ax.plot(zonas[-1][:, 0], zonas[-1][:, 1], ":", color=col, lw=2,
                    label="lugares posibles" if k == 0 else None)
        cx = d["C"] * obj
        ax.scatter(*cx[:2], marker="D", facecolor="none", edgecolor=col, s=80,
                   lw=1.5, label="C × a quien sigue")
        ax.plot([obj[0], cx[0]], [obj[1], cx[1]], "--", color=col, lw=0.8)

    if regla == 1:
        ax.scatter(*obj[:2], marker="D", c=col, edgecolor="k", s=90,
                   label=f"ballena al azar (#{d['j']})", zorder=5)
    ax.scatter(*it["presa"][:2], marker="X", c="yellow", edgecolor="k", s=180,
               label="presa (la mejor)", zorder=6)
    ax.scatter(*d["x_antes"][:2], s=150, c="white", edgecolor="k", lw=2,
               label="ballena antes", zorder=7)
    ax.annotate("", xy=d["x_nuevo"][:2], xytext=d["x_antes"][:2],
                arrowprops=dict(arrowstyle="->", color="k", lw=2), zorder=8)
    ax.scatter(*d["x_nuevo"][:2], s=150, c=col, edgecolor="k", lw=2,
               label="ballena después", zorder=9)
    if not np.allclose(d["x_nuevo"], d["x_final"]):
        ax.scatter(*d["x_final"][:2], s=90, marker="s", c=col, edgecolor="k",
                   label="regresada a la zona", zorder=9)

    if zoom:
        pts = np.vstack([d["x_antes"], d["x_nuevo"], it["presa"], obj]
                        + zonas)
        lo, hi = pts.min(axis=0)[:2], pts.max(axis=0)[:2]
        centro, r = (lo + hi) / 2, max((hi - lo).max() * 0.75, (ub - lb) * 0.02)
        ax.set_xlim(max(lb, centro[0] - r), min(ub, centro[0] + r))
        ax.set_ylim(max(lb, centro[1] - r), min(ub, centro[1] + r))
    ax.set_title(f"Vuelta {it['t']}, ballena #{d['i']}: "
                 f"{NOMBRES[regla].lower()}",
                 color=col, fontsize=11, fontweight="bold")
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.06),
              ncol=3, frameon=False)
    fig.tight_layout()
    return fig


def figura_decisiones(it, d, b, p_umbral, a_inicial):
    """Tres mini-graficas: de donde salio A, la decision por p y el factor de
    la espiral."""
    a, regla = it["a"], d["regla"]
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.2))

    # A en funcion de r1
    ax = axs[0]
    r = np.linspace(0, 1, 100)
    ax.axhspan(-1, 1, color=visual.COLORES_REGLAS[0], alpha=0.12)
    ax.text(0.02, 0.9, "|A| < 1: rodear", fontsize=8, transform=ax.transAxes,
            color=visual.COLORES_REGLAS[0])
    ax.plot(r, 2 * a * r - a, "k-", label=f"A = 2·a·r1 − a  (a = {a:.2f})")
    ax.scatter([d["r1"]], [d["A"]], s=80, c=visual.COLORES_REGLAS[regla],
               edgecolor="k", zorder=5)
    lim = max(a_inicial, 1.2)
    ax.set_ylim(-lim, lim); ax.set_xlim(0, 1)
    ax.set_xlabel("r1"); ax.set_ylabel("A"); ax.legend(fontsize=7, loc="lower right")
    ax.set_title("¿De dónde sale A?", fontsize=10)

    # p contra el umbral
    ax = axs[1]
    ax.barh([0], [p_umbral], color="#cccccc", height=0.5)
    ax.barh([0], [1 - p_umbral], left=p_umbral, color=visual.COLORES_REGLAS[2],
            alpha=0.5, height=0.5)
    ax.text(p_umbral / 2, 0.38, "rodear / buscar", ha="center", fontsize=8)
    ax.text((1 + p_umbral) / 2, 0.38, "espiral", ha="center", fontsize=8)
    ax.axvline(d["p"], color="k", lw=2)
    ax.text(d["p"], -0.42, f"p = {d['p']:.3f}", ha="center", fontsize=9)
    ax.set_xlim(0, 1); ax.set_ylim(-0.6, 0.6); ax.set_yticks([])
    ax.set_title(f"¿Espiral? (volado p, umbral {p_umbral:g})", fontsize=10)

    # factor de la espiral
    ax = axs[2]
    ls = np.linspace(-1, 1, 300)
    ax.plot(ls, np.exp(b * ls) * np.cos(2 * np.pi * ls), "k-")
    ax.axhline(0, color="k", lw=0.5)
    g = np.exp(b * d["l"]) * np.cos(2 * np.pi * d["l"])
    usado = regla == 2
    ax.scatter([d["l"]], [g], s=80, edgecolor="k", zorder=5,
               c=visual.COLORES_REGLAS[2] if usado else "white")
    ax.set_xlabel("l"); ax.set_ylabel("factor = e^(b·l)·cos(2π·l)")
    ax.set_title("Factor de la espiral" + ("" if usado else " (no se usó)"),
                 fontsize=10)
    fig.tight_layout()
    return fig
