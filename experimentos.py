"""
Utilidades para correr experimentos con WOA y script para generar los
resultados del reporte (tablas CSV y graficas PNG en la carpeta resultados/).
Al terminar SIEMPRE actualiza la guia del reporte (tablas del Anexo A) y
avisa si algun numero escrito a mano en el texto ya no coincide.

Uso:  python experimentos.py            (corre todo y actualiza; ~20 min)
      python experimentos.py --rapido   (5 corridas, para probar; no toca
                                         la guia)
      python experimentos.py --solo-sesgo          (6_sesgo_centro)
      python experimentos.py --solo-panorama       (7_panorama)
      python experimentos.py --solo-combinaciones  (8_combinaciones, ~12 min)
      python experimentos.py --solo-tabla-25       (9_tabla_25, ~1 min)
      python experimentos.py --solo-reporte        (solo la guia, al instante)
"""
import argparse
import os
import time

import numpy as np
import pandas as pd

from algoritmo.funciones import FUNCIONES
from algoritmo.woa import woa

PARAMS_DEFAULT = dict(n_ballenas=30, max_iter=200, a_inicial=2.0,
                      b=1.0, p_umbral=0.5)


def correr(nombre_f, dim=None, n_corridas=30, seed_base=0, lb=None, ub=None,
           **params):
    """Corre WOA n_corridas veces (semillas distintas) sobre una funcion.
    Devuelve (mejores_f, curvas) con curvas de forma (n_corridas, iter+1)."""
    cfg = FUNCIONES[nombre_f]
    dim = cfg["dim"] or dim or cfg["dim_default"]
    lb = cfg["lb"] if lb is None else lb
    ub = cfg["ub"] if ub is None else ub
    p = {**PARAMS_DEFAULT, **params}
    finales, curvas, tiempos = [], [], []
    for k in range(n_corridas):
        t0 = time.perf_counter()
        r = woa(cfg["f"], lb, ub, dim, seed=seed_base + k, **p)
        tiempos.append(time.perf_counter() - t0)
        finales.append(r["mejor_f"])
        curvas.append(r["curva"])
    return np.array(finales), np.array(curvas), np.array(tiempos)


def resumen(finales, tiempos=None):
    d = dict(media=np.mean(finales), desv_est=np.std(finales, ddof=1)
             if len(finales) > 1 else 0.0,
             mediana=np.median(finales), mejor=np.min(finales),
             peor=np.max(finales))
    if tiempos is not None:
        d["tiempo_medio_s"] = float(np.mean(tiempos))
    return d


def barrido(nombre_f, parametro, valores, n_corridas=30, dim=None, **fijos):
    """Varia UN parametro y deja el resto en su valor por defecto.
    parametro puede ser un parametro de WOA o 'dim'.
    Devuelve (DataFrame resumen, dict valor -> finales, dict valor -> curvas)."""
    filas, finales_d, curvas_d = [], {}, {}
    for v in valores:
        if parametro == "dim":
            fin, cur, tie = correr(nombre_f, dim=int(v), n_corridas=n_corridas,
                                   **fijos)
        else:
            kw = {**fijos, parametro: v}
            if parametro in ("n_ballenas", "max_iter"):
                kw[parametro] = int(v)
            fin, cur, tie = correr(nombre_f, dim=dim, n_corridas=n_corridas,
                                   **kw)
        filas.append({parametro: v, **resumen(fin, tie)})
        finales_d[v], curvas_d[v] = fin, cur
    return pd.DataFrame(filas), finales_d, curvas_d


# --------------------------------------------------------------------------
# Script principal: genera todo lo que necesita el reporte
# --------------------------------------------------------------------------
BARRIDOS = {
    "n_ballenas": [10, 30, 50, 100],
    "max_iter": [50, 100, 200, 500],
    "a_inicial": [1.0, 2.0, 3.0],
    "b": [0.5, 1.0, 2.0],
    "p_umbral": [0.2, 0.5, 0.8],
}

# Experimento de sesgo al centro: funciones con el optimo en el origen y
# cuanto se mueve el optimo (en cada eje) para la version desplazada.
SESGO = {"Rastrigin": 2.0, "Ackley": 1.5, "Sphere": 30.0}


def desplazar(f, s):
    """f(x - s): la misma funcion con el optimo movido s en cada eje."""
    return lambda x: f(np.asarray(x) - s)


def experimento_sesgo(n, plt):
    carpeta = "resultados/6_sesgo_centro"
    os.makedirs(carpeta, exist_ok=True)
    filas = []
    fig, axs = plt.subplots(1, len(SESGO), figsize=(12, 4))
    for ax, (nombre, s) in zip(axs, SESGO.items()):
        cfg = FUNCIONES[nombre]
        dim = cfg["dim"] or cfg["dim_default"]
        datos = []
        for caso, sv in (("original", 0.0), ("desplazada", s)):
            f = cfg["f"] if sv == 0 else desplazar(cfg["f"], sv)
            fin = np.array([woa(f, cfg["lb"], cfg["ub"], dim, seed=k,
                                **PARAMS_DEFAULT)["mejor_f"]
                            for k in range(n)])
            filas.append({"funcion": nombre, "caso": caso,
                          "optimo_en": sv, "dim": dim, **resumen(fin)})
            datos.append(fin)
        ax.boxplot(datos, tick_labels=["mínimo en el centro",
                                       f"mínimo movido {s:g}"])
        ax.set_yscale("symlog", linthresh=1e-12)
        ax.set_title(f"{nombre} ({dim} variables)")
    axs[0].set_ylabel("Mejor valor final")
    fig.suptitle("Misma función, mínimo movido de lugar (sesgo al centro)")
    fig.tight_layout()
    fig.savefig(f"{carpeta}/comparacion.png", dpi=130)
    plt.close(fig)
    pd.DataFrame(filas).to_csv(f"{carpeta}/resumen.csv", index=False)
    print("sesgo al centro listo")


# Rosenbrock (10 variables) vale 9 en el centro (0, ..., 0) y 0 en su
# minimo (1, ..., 1). Se cuenta a donde llega cada corrida.
CASOS_ROSENBROCK = [
    ("Por defecto", {}),
    ("500 vueltas", {"max_iter": 500}),
    ("a = 3", {"a_inicial": 3.0}),
    ("Mejor combinación", {"n_ballenas": 10, "max_iter": 600,
                           "a_inicial": 3.0, "b": 0.5, "p_umbral": 0.8}),
]
RADIO_DESTINO = 0.5     # "llego a X" = quedo a menos de 0.5 de X


def experimento_rosenbrock(n, plt, carpeta="resultados/6_sesgo_centro"):
    os.makedirs(carpeta, exist_ok=True)
    cfg = FUNCIONES["Rosenbrock"]
    dim = cfg["dim_default"]
    minimo = cfg["optimo_x"](dim)
    filas, puntos = [], {}
    for caso, cambios in CASOS_ROSENBROCK:
        p = {**PARAMS_DEFAULT, **cambios}
        d0, d1, fs = [], [], []
        for k in range(n):
            r = woa(cfg["f"], cfg["lb"], cfg["ub"], dim, seed=k, **p)
            d0.append(np.linalg.norm(r["mejor_x"]))
            d1.append(np.linalg.norm(r["mejor_x"] - minimo))
            fs.append(r["mejor_f"])
        d0, d1, fs = map(np.array, (d0, d1, fs))
        centro = d0 < RADIO_DESTINO
        bien = d1 < RADIO_DESTINO
        filas.append({"caso": caso, **p, "corridas": n,
                      "al_centro": int(centro.sum()),
                      "al_minimo": int(bien.sum()),
                      "otro": int((~centro & ~bien).sum()),
                      "mediana": float(np.median(fs)),
                      "valor_centro_min": float(fs[centro].min())
                      if centro.any() else np.nan,
                      "valor_centro_max": float(fs[centro].max())
                      if centro.any() else np.nan})
        puntos[caso] = (d0, d1)
    df = pd.DataFrame(filas)
    df.to_csv(f"{carpeta}/rosenbrock.csv", index=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.6),
                                   gridspec_kw=dict(width_ratios=[1, 1.25]))
    d0, d1 = puntos["Por defecto"]
    ax1.scatter(d0, d1, s=45, color="#1f77b4", alpha=0.7,
                edgecolor="white")
    ax1.annotate("cerca del centro (0, …, 0)\nahí la función vale 9",
                 (0.05, np.sqrt(dim)), xytext=(0.6, 2.2), fontsize=9,
                 arrowprops=dict(arrowstyle="->", color="gray"))
    ax1.annotate("cerca del mínimo real (1, …, 1)\nahí vale 0",
                 (np.sqrt(dim), 0.05), xytext=(1.2, 0.9), fontsize=9,
                 arrowprops=dict(arrowstyle="->", color="gray"))
    ax1.set_xlabel("distancia al centro")
    ax1.set_ylabel("distancia al mínimo real")
    ax1.set_title(f"Por defecto: dónde termina cada una de las {n} corridas")
    ax1.grid(alpha=0.3)
    casos = list(df["caso"])
    y = np.arange(len(casos))[::-1]
    izq = np.zeros(len(casos))
    for col, color, et in (("al_centro", "#d62728", "se atoró en el centro"),
                           ("al_minimo", "#2ca02c", "llegó al mínimo real"),
                           ("otro", "#bbbbbb", "otro lugar")):
        v = df[col].to_numpy()
        ax2.barh(y, v, left=izq, color=color, label=et, height=0.6,
                 edgecolor="white")
        for yi, xi, vi in zip(y, izq, v):
            if vi:
                ax2.text(xi + vi / 2, yi, str(vi), ha="center",
                         va="center", color="white", fontweight="bold")
        izq += v
    ax2.set_yticks(y, casos)
    ax2.set_xlabel(f"corridas (de {n})")
    ax2.set_xlim(0, n)
    ax2.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3,
               fontsize=9, frameon=False)
    fig.suptitle("Rosenbrock (10 variables): ¿por qué se atora en ~8.9?",
                 fontsize=13, y=1.03)
    fig.tight_layout()
    fig.savefig(f"{carpeta}/rosenbrock.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("rosenbrock listo")


# Nombres para la figura panorama (texto que se ve, con acentos)
NOMBRES_PAR = {"n_ballenas": "Ballenas", "max_iter": "Vueltas",
               "a_inicial": "a inicial", "b": "b (espiral)",
               "p_umbral": "p (umbral)"}


def figura_panorama(finales, plt, ruta):
    """Una sola figura con TODAS las cajas: filas = funciones, columnas =
    parametros. finales[nombre][par][valor] = arreglo de mejores valores.
    Escala log por fila (misma escala en toda la fila para comparar
    parametros); los ceros exactos se dibujan en el piso y se marcan "0"."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    nombres = list(finales)
    pars = list(BARRIDOS)
    fig, axs = plt.subplots(len(nombres), len(pars), sharey="row",
                            figsize=(15, 3.0 * len(nombres)))
    for i, nombre in enumerate(nombres):
        todos = np.concatenate([finales[nombre][p][v] for p in pars
                                for v in BARRIDOS[p]])
        pos = todos[todos > 0]
        piso = 10.0 ** (np.floor(np.log10(pos.min())) - 1) if len(pos) else 1e-16
        hay_ceros = (todos <= 0).any()
        for j, par in enumerate(pars):
            ax = axs[i, j]
            vals = BARRIDOS[par]
            datos = [np.maximum(finales[nombre][par][v], piso) for v in vals]
            cajas = ax.boxplot(datos, tick_labels=[f"{v:g}" for v in vals],
                               patch_artist=True, showmeans=True,
                               widths=0.6,
                               meanprops=dict(marker="D", markersize=5,
                                              markerfacecolor="#d62728",
                                              markeredgecolor="white"),
                               medianprops=dict(color="black", linewidth=1.5),
                               flierprops=dict(marker="o", markersize=3,
                                               alpha=0.5))
            for k, (v, caja) in enumerate(zip(vals, cajas["boxes"]), start=1):
                por_defecto = v == PARAMS_DEFAULT[par]
                caja.set_facecolor("#9ecae1" if por_defecto else "white")
                if por_defecto:   # franja de fondo: se ve aunque la caja sea 0
                    ax.axvspan(k - 0.45, k + 0.45, color="#deebf7", zorder=0)
            ax.set_yscale("log")
            ax.grid(axis="y", alpha=0.3)
            if i == 0:
                ax.set_title(NOMBRES_PAR[par], fontsize=12, fontweight="bold")
            if i == len(nombres) - 1:
                ax.set_xlabel("valor probado")
        ax0 = axs[i, 0]
        ax0.set_ylabel(f"{nombre}\nmejor valor final", fontsize=11)
        if hay_ceros:
            ax0.set_ylim(bottom=piso / 3)
            ax0.axhline(piso, color="gray", lw=0.8, ls=":")
            for ax in axs[i]:
                ax.axhline(piso, color="gray", lw=0.8, ls=":")
            ax0.annotate("0 exacto", (0, piso), xycoords=("axes fraction", "data"),
                         xytext=(-4, 0), textcoords="offset points",
                         ha="right", va="center", fontsize=8, color="gray")
    leyenda = [Patch(facecolor="#9ecae1", edgecolor="black",
                     label="valor por defecto (los demás ajustes fijos)"),
               Line2D([], [], color="black", lw=1.5, label="mediana"),
               Line2D([], [], marker="D", ls="", markerfacecolor="#d62728",
                      markeredgecolor="white", markersize=7, label="media"),
               Line2D([], [], marker="o", ls="", color="black", alpha=0.5,
                      markersize=4, label="corrida atípica")]
    fig.legend(handles=leyenda, loc="upper center", ncol=4, fontsize=10,
               bbox_to_anchor=(0.5, 0.995), frameon=False)
    fig.suptitle("Efecto de cada ajuste en las 5 funciones (30 corridas por "
                 "caja; más abajo = mejor; escala log)", y=1.025, fontsize=13)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)


def guardar_panorama(finales, plt, carpeta="resultados/7_panorama"):
    """finales.csv (una fila por corrida, lo lee la app) + cajas.png."""
    os.makedirs(carpeta, exist_ok=True)
    filas = [dict(funcion=nom, parametro=par, valor=v, corrida=k,
                  mejor_f=float(x))
             for nom, d in finales.items() for par, vals in d.items()
             for v, arr in vals.items() for k, x in enumerate(arr)]
    pd.DataFrame(filas).to_csv(f"{carpeta}/finales.csv", index=False)
    figura_panorama(finales, plt, f"{carpeta}/cajas.png")


def experimento_panorama(n, plt):
    """Corre otra vez los barridos (sin guardar CSV) solo para la figura."""
    finales = {}
    for nombre in FUNCIONES:
        finales[nombre] = {par: barrido(nombre, par, vals, n_corridas=n)[1]
                           for par, vals in BARRIDOS.items()}
        print(nombre, "listo")
    guardar_panorama(finales, plt)


# Combinaciones: todas las de a, b y p con el MISMO esfuerzo total
# (ballenas x vueltas = 6000 movimientos), repartido de 3 maneras.
REPARTOS = [(10, 600), (30, 200), (60, 100)]
N_COMBINACIONES = 25        # corridas por combinacion


def combinaciones():
    return [dict(n_ballenas=nb, max_iter=mi, a_inicial=a, b=b, p_umbral=p)
            for nb, mi in REPARTOS for a in BARRIDOS["a_inicial"]
            for b in BARRIDOS["b"] for p in BARRIDOS["p_umbral"]]


def ordenar_combinaciones(df):
    """Lugar dentro de cada funcion: menor mediana gana; si empatan, menor
    media y luego menor peor. Si las tres empatan (ej. todas sus corridas
    llegaron a 0 exacto) comparten lugar (1, 1, 1, 4, ...)."""
    df = df.sort_values(["funcion", "mediana", "media", "peor"],
                        kind="stable").reset_index(drop=True)
    lugar, previo, pos = [], None, 0
    for f, me, mu, pe in zip(df["funcion"], df["mediana"], df["media"],
                             df["peor"]):
        pos = 1 if previo is None or previo[0] != f else pos + 1
        actual = (f, me, mu, pe)
        lugar.append(lugar[-1] if actual == previo else pos)
        previo = actual
    df["lugar"] = lugar
    return df


def es_default(fila):
    return all(np.isclose(fila[k], v) for k, v in PARAMS_DEFAULT.items())


def texto_combo(fila):
    return (f"{int(fila['n_ballenas'])}x{int(fila['max_iter'])}, "
            f"a={fila['a_inicial']:g}, b={fila['b']:g}, p={fila['p_umbral']:g}")


def experimento_combinaciones(n, plt, carpeta="resultados/8_combinaciones"):
    os.makedirs(carpeta, exist_ok=True)
    filas = []
    for nombre in FUNCIONES:
        for c in combinaciones():
            fin, _, tie = correr(nombre, n_corridas=n, **c)
            filas.append({"funcion": nombre, **c, **resumen(fin, tie)})
        print(nombre, "combinaciones listo")
    res = ordenar_combinaciones(pd.DataFrame(filas))
    res.to_csv(f"{carpeta}/resumen.csv", index=False)
    figuras_combinaciones(res, plt, carpeta)


def figuras_combinaciones(res, plt, carpeta):
    nombres = list(FUNCIONES)
    claves = list(PARAMS_DEFAULT)
    # Cruce: la ganadora de cada funcion, ¿en que lugar queda en las demas?
    lugares = np.zeros((len(nombres) + 1, len(nombres)), int)
    filas_txt = []
    ganadoras = [res[(res.funcion == nom) & (res.lugar == 1)].iloc[0]
                 for nom in nombres]
    dfl = res[res.apply(es_default, axis=1)].iloc[0]
    for i, g in enumerate(ganadoras + [dfl]):
        n_emp = int(((res.funcion == g["funcion"]) & (res.lugar == 1)).sum())
        extra = (f" (empata con {n_emp - 1})"
                 if i < len(nombres) and n_emp > 1 else "")
        filas_txt.append(("Por defecto: " if i == len(nombres) else
                          f"Mejor en {nombres[i]}{extra}: ") + texto_combo(g))
        for j, nom in enumerate(nombres):
            r = res[res.funcion == nom]
            m = np.ones(len(r), bool)
            for k in claves:
                m &= np.isclose(r[k], g[k])
            lugares[i, j] = int(r.loc[m, "lugar"].iloc[0])
    total = len(res) // len(nombres)
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.imshow(lugares, cmap="RdYlGn_r", vmin=1, vmax=total, aspect="auto")
    for i in range(lugares.shape[0]):
        for j in range(lugares.shape[1]):
            ax.text(j, i, f"{lugares[i, j]}", ha="center", va="center",
                    fontsize=11, fontweight="bold" if lugares[i, j] == 1
                    else "normal")
    ax.set_xticks(range(len(nombres)), nombres)
    ax.set_yticks(range(len(filas_txt)), filas_txt, fontsize=9)
    ax.xaxis.tick_top()
    ax.set_title(f"Lugar de cada combinación en cada función (1 = la mejor, "
                 f"{total} = la peor)", pad=28)
    fig.tight_layout()
    fig.savefig(f"{carpeta}/cruce.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    figura_mapa(res, plt, f"{carpeta}/mapa.png")
    figura_terrenos(plt, f"{carpeta}/terrenos.png")


# Grupos del mapa: (titulo, columna, valores)
GRUPOS_MAPA = [("Ballenas × vueltas", "n_ballenas", [nb for nb, _ in REPARTOS]),
               ("a inicial", "a_inicial", BARRIDOS["a_inicial"]),
               ("b (espiral)", "b", BARRIDOS["b"]),
               ("p (umbral)", "p_umbral", BARRIDOS["p_umbral"])]


def lugar_promedio_por_valor(res):
    """dict funcion -> lista (grupo, valor, lugar promedio de las
    combinaciones que usan ese valor). Menor = conviene mas."""
    out = {}
    for nom in FUNCIONES:
        r = res[res.funcion == nom]
        out[nom] = [(g, v, float(r.loc[np.isclose(r[col], v), "lugar"].mean()))
                    for g, col, vals in GRUPOS_MAPA for v in vals]
    return out


def figura_mapa(res, plt, ruta):
    """Filas = funciones, columnas = cada valor de cada ajuste; color =
    lugar promedio. Recuadro = el mejor valor de ese ajuste en esa funcion;
    punto = el valor por defecto."""
    lp = lugar_promedio_por_valor(res)
    nombres = list(FUNCIONES)
    etiquetas = []
    for g, col, vals in GRUPOS_MAPA:
        if col == "n_ballenas":
            etiquetas += [f"{nb}×{mi}" for nb, mi in REPARTOS]
        else:
            etiquetas += [f"{v:g}" for v in vals]
    M = np.array([[x[2] for x in lp[nom]] for nom in nombres])
    total = len(res) // len(nombres)
    fig, ax = plt.subplots(figsize=(13, 4.4))
    ax.imshow(M, cmap="RdYlGn_r", vmin=1, vmax=total, aspect="auto")
    dfl = {"n_ballenas": PARAMS_DEFAULT["n_ballenas"],
           **{c: PARAMS_DEFAULT[c] for _, c, _ in GRUPOS_MAPA[1:]}}
    j0 = 0
    for g, col, vals in GRUPOS_MAPA:
        for i in range(len(nombres)):
            fila = M[i, j0:j0 + len(vals)]
            jm = j0 + int(np.argmin(fila))
            ax.add_patch(plt.Rectangle((jm - 0.47, i - 0.45), 0.94, 0.9,
                                       fill=False, lw=2.5, ec="black"))
            for k, v in enumerate(vals):
                ax.text(j0 + k, i, f"{M[i, j0 + k]:.0f}", ha="center",
                        va="center", fontsize=11,
                        fontweight="bold" if j0 + k == jm else "normal")
                if np.isclose(v, dfl[col]):
                    ax.plot(j0 + k + 0.32, i - 0.28, "o", ms=5, color="#1f4e79")
        if j0:
            ax.axvline(j0 - 0.5, color="white", lw=6)
        ax.text(j0 + (len(vals) - 1) / 2, -0.95, g, ha="center", va="bottom",
                fontsize=11, fontweight="bold")
        j0 += len(vals)
    ax.set_xticks(range(len(etiquetas)), etiquetas)
    ax.set_yticks(range(len(nombres)), nombres, fontsize=11)
    ax.set_ylim(len(nombres) - 0.5, -1.2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.suptitle("¿Qué valor de cada ajuste conviene en cada función? (lugar "
                 f"promedio entre las {total} combinaciones; menor = mejor)",
                 fontsize=12)
    fig.text(0.5, -0.02, "Recuadro = el mejor valor de ese ajuste en esa "
             "función · punto azul = valor por defecto · mismo esfuerzo en "
             "todas: ballenas × vueltas = 6000", ha="center", fontsize=9.5,
             color="#444")
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)


# Apodos y zona a dibujar (la de Rosenbrock se acerca para ver el valle)
TERRENOS = {"Rastrigin": ("cartón de huevo", None),
            "Ackley": ("llanura con un pozo", None),
            "Sphere": ("tazón", None),
            "Rosenbrock": ("valle del plátano (acercado)", (-2, 2, -1, 3)),
            "Beale": ("valles angostos", None)}


def figura_terrenos(plt, ruta, n=91):   # impar: pasa por el centro
    """Las 5 funciones en 3D (version de 2 variables). Altura log10(1+f)
    para que se vean los detalles, como en la Simulacion 3D."""
    fig = plt.figure(figsize=(18, 4.2))
    for k, (nom, (apodo, zona)) in enumerate(TERRENOS.items(), start=1):
        cfg = FUNCIONES[nom]
        x0, x1, y0, y1 = zona or (cfg["lb"], cfg["ub"], cfg["lb"], cfg["ub"])
        X, Y = np.meshgrid(np.linspace(x0, x1, n), np.linspace(y0, y1, n))
        Z = np.array([[cfg["f"](np.array([x, y])) for x, y in zip(fx, fy)]
                      for fx, fy in zip(X, Y)])
        Zl = np.log10(1 + Z)
        ax = fig.add_subplot(1, len(TERRENOS), k, projection="3d")
        ax.plot_surface(X, Y, Zl, cmap="viridis", linewidth=0,
                        antialiased=True, rstride=1, cstride=1, alpha=0.95)
        ox, oy = cfg["optimo_x"](2)
        ax.scatter([ox], [oy], [np.log10(1 + cfg["optimo_f"])], color="red",
                   s=60, marker="*", depthshade=False, zorder=10)
        ax.set_title(f"{nom}\n{apodo}", fontsize=11, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
        ax.view_init(elev=35, azim=-60)
    fig.suptitle("Cómo es cada función (con 2 variables). Estrella roja = el "
                 "mínimo. Altura en escala log para ver los detalles",
                 fontsize=12, y=1.06)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# Tabla 1 del reporte (diseno de Diana): 25 ejecuciones por funcion, UNA
# corrida por fila con la semilla indicada, 125 corridas en total.
# Cada fila guarda solo lo que cambia respecto a PARAMS_DEFAULT (y dim).
# La fila 25 es distinta segun la funcion: las de n variables pasan a 30
# variables; Ackley y Beale (solo 2 variables) usan un ajuste fino.
# --------------------------------------------------------------------------
CARPETA_TABLA_25 = "resultados/9_tabla_25"
TABLA_25 = [
    (1, "1. Base y azar", {}, 0, "Referencia principal de control."),
    (2, "1. Base y azar", {}, 1, "Variabilidad por inicialización aleatoria."),
    (3, "1. Base y azar", {}, 2, "Variabilidad por inicialización aleatoria."),
    (4, "1. Base y azar", {}, 3, "Variabilidad por inicialización aleatoria."),
    (5, "1. Base y azar", {}, 4, "Variabilidad por inicialización aleatoria."),
    (6, "2. Población (N)", {"n_ballenas": 5}, 0,
     "Población mínima (alto riesgo de estancamiento)."),
    (7, "2. Población (N)", {"n_ballenas": 15}, 0,
     "Población pequeña (mitad de la base)."),
    (8, "2. Población (N)", {"n_ballenas": 50}, 0, "Población media-alta."),
    (9, "2. Población (N)", {"n_ballenas": 80}, 0,
     "Población grande (mayor cobertura inicial)."),
    (10, "2. Población (N)", {"n_ballenas": 120}, 0,
     "Población muy densa (punto de saturación)."),
    (11, "3. Iteraciones", {"max_iter": 50}, 0,
     "Convergencia temprana con pocas vueltas."),
    (12, "3. Iteraciones", {"max_iter": 100}, 0,
     "Mitad del presupuesto estándar."),
    (13, "3. Iteraciones", {"max_iter": 300}, 0, "Refinamiento extendido."),
    (14, "3. Iteraciones", {"max_iter": 500}, 0,
     "Alta precisión de convergencia."),
    (15, "3. Iteraciones", {"max_iter": 1000}, 0,
     "Límite de estabilización asintótica."),
    (16, "4. Expl. / Explot.", {"a_inicial": 0.5}, 0,
     "Explotación pura (|A| < 1 desde el inicio)."),
    (17, "4. Expl. / Explot.", {"a_inicial": 1.0}, 0,
     "Umbral límite sin búsqueda aleatoria."),
    (18, "4. Expl. / Explot.", {"a_inicial": 3.0}, 0,
     "Fase de exploración global prolongada."),
    (19, "4. Expl. / Explot.", {"p_umbral": 0.2}, 0,
     "Predomina ataque en espiral (80% espiral)."),
    (20, "4. Expl. / Explot.", {"p_umbral": 0.8}, 0,
     "Predomina cerco y búsqueda (20% espiral)."),
    (21, "5. Espiral y comb.", {"b": 0.2}, 0,
     "Espiral logarítmica muy cerrada/estrecha."),
    (22, "5. Espiral y comb.", {"b": 2.5}, 0,
     "Espiral logarítmica muy abierta/amplia."),
    (23, "5. Espiral y comb.", {"n_ballenas": 15, "max_iter": 100}, 0,
     "Escenario combinado ligero (bajo costo)."),
    (24, "5. Espiral y comb.",
     {"n_ballenas": 60, "max_iter": 400, "a_inicial": 2.5}, 0,
     "Escenario combinado intensivo (alta exploración)."),
    (25, "5. Espiral y comb.", {"dim": 30}, 0,
     "Escalabilidad a d=30 (o ajuste fino en 2D*)."),
]
# Fila 25 en Ackley y Beale (no existen con 30 variables)
FILA_25_DOS_VARIABLES = {"n_ballenas": 50, "max_iter": 300, "a_inicial": 1.5,
                         "b": 0.5, "p_umbral": 0.3}


def filas_tabla_25(nombre_f):
    """Las 25 filas de una funcion: (num, bloque, params, dim, seed, texto)."""
    cfg = FUNCIONES[nombre_f]
    filas = []
    for num, bloque, cambios, seed, texto in TABLA_25:
        cambios = dict(cambios)
        if "dim" in cambios and cfg["dim"] is not None:
            cambios = dict(FILA_25_DOS_VARIABLES)    # Ackley / Beale
        dim = cambios.pop("dim", None) or cfg["dim"] or cfg["dim_default"]
        filas.append((num, bloque, {**PARAMS_DEFAULT, **cambios}, int(dim),
                      seed, texto))
    return filas


def experimento_tabla_25(plt, carpeta=CARPETA_TABLA_25):
    """Corre las 25 filas en las 5 funciones (125 corridas, ~1 min)."""
    os.makedirs(carpeta, exist_ok=True)
    filas = []
    for nombre, cfg in FUNCIONES.items():
        for num, bloque, p, dim, seed, texto in filas_tabla_25(nombre):
            t0 = time.perf_counter()
            r = woa(cfg["f"], cfg["lb"], cfg["ub"], dim, seed=seed, **p)
            seg = time.perf_counter() - t0
            filas.append({"funcion": nombre, "ejecucion": num,
                          "bloque": bloque, **p, "dim": dim, "seed": seed,
                          "mejor_f": r["mejor_f"],
                          "distancia_optimo": float(np.linalg.norm(
                              r["mejor_x"] - cfg["optimo_x"](dim))),
                          "tiempo_s": seg, "que_se_evalua": texto})
        print(nombre, "tabla 25 lista")
    df = pd.DataFrame(filas)
    df.to_csv(f"{carpeta}/corridas.csv", index=False)
    figura_tabla_25(df, plt, f"{carpeta}/resultados.png")
    return df


def figura_tabla_25(df, plt, ruta):
    """Mapa de calor: funcion x ejecucion, color = log10 del mejor valor."""
    nombres = list(FUNCIONES)
    nums = sorted(df.ejecucion.unique())
    m = np.array([[df[(df.funcion == f) & (df.ejecucion == k)].mejor_f
                   .iloc[0] for k in nums] for f in nombres])
    # Escala recortada: todo lo que baja de 1e-16 es "practicamente 0"
    # (si no, un 1e-185 de Sphere se come todos los colores).
    abajo, arriba = -16, 2
    color = np.clip(np.log10(np.maximum(m, 1e-300)), abajo, arriba)
    fig, ax = plt.subplots(figsize=(18, 4.6))
    im = ax.imshow(color, cmap="RdYlGn_r", vmin=abajo, vmax=arriba,
                   aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m[i, j]
            txt = "0" if v == 0 else (f"{v:.0e}".replace("e-0", "e-")
                                      if v < 0.01 else f"{v:.2g}")
            ax.text(j, i, txt, ha="center", va="center", fontsize=7)
    ax.set_xticks(range(len(nums)), [str(k) for k in nums])
    ax.set_yticks(range(len(nombres)), nombres)
    ax.set_xlabel("Ejecución (fila de la Tabla 1)")
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_ticks([abajo, -12, -8, -4, 0, arriba])
    cb.set_ticklabels(["≤1e-16", "1e-12", "1e-8", "1e-4", "1", "100"])
    cb.set_label("Mejor valor (verde = casi 0)")
    ax.set_title("Tabla 1: mejor valor de cada ejecución (1 corrida por fila)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    plt.close(fig)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true",
                    help="5 corridas en vez de 30 (solo para probar)")
    ap.add_argument("--solo-sesgo", action="store_true",
                    help="correr solo el experimento de sesgo al centro")
    ap.add_argument("--solo-panorama", action="store_true",
                    help="solo la figura con todas las cajas (7_panorama)")
    ap.add_argument("--solo-combinaciones", action="store_true",
                    help="solo el experimento de combinaciones (~12 min)")
    ap.add_argument("--solo-tabla-25", action="store_true",
                    help="solo la Tabla 1 del reporte: 25 ejecuciones por "
                         "funcion, 1 corrida cada una (9_tabla_25, ~1 min)")
    ap.add_argument("--solo-reporte", action="store_true",
                    help="no correr nada: solo actualizar la guia del "
                         "reporte con los CSV que ya existen")
    args = ap.parse_args()
    n_comb = 5 if args.rapido else N_COMBINACIONES
    n = 5 if args.rapido else 30
    if args.solo_sesgo:
        experimento_sesgo(n, plt)
        experimento_rosenbrock(n, plt)
    elif args.solo_panorama:
        experimento_panorama(n, plt)
    elif args.solo_tabla_25:
        experimento_tabla_25(plt)
    elif args.solo_combinaciones:
        experimento_combinaciones(n_comb, plt)
    elif not args.solo_reporte:
        generar_todo(n, n_comb, plt)
    if args.rapido:
        print("\n(--rapido: con 5 corridas los numeros no son los del "
              "reporte, asi que la guia NO se actualizo)")
    else:
        figura_tiempo_calidad(plt)        # sale de los CSV, no corre nada
        avisar_reporte()


def avisar_reporte():
    """Al terminar: reescribe las tablas automaticas de la guia del reporte
    y avisa si algun numero escrito a mano ya no coincide."""
    from interfaz.reporte import actualizar_reporte
    cambiados, malos = actualizar_reporte()
    print("\nGuia del reporte (docs/reporte_referencia.md):")
    print("  tablas actualizadas: " + (", ".join(cambiados) if cambiados
                                       else "ya estaban al día"))
    if malos:
        print(f"  OJO: {len(malos)} numeros escritos a mano ya no coinciden "
              "con los CSV; corrijanlos en el texto (y en "
              "interfaz/reporte.py, lista NUMEROS):")
        for m in malos:
            print("   - " + m)
    else:
        print("  todos los numeros escritos a mano siguen coincidiendo")


def figura_tiempo_calidad(plt, res="resultados"):
    """Tiempo contra calidad, desde los CSV de los barridos de vueltas y de
    ballenas (no corre nada). Eje x = esfuerzo (ballenas x vueltas), que es
    exacto; arriba, los segundos aproximados (el tiempo medido tiene ruido)."""
    ruta = os.path.join(res, "0_base", "tiempo_calidad.png")
    nombres = list(FUNCIONES)
    fig, axs = plt.subplots(1, len(nombres), figsize=(18, 4.4))
    series = [("max_iter", "más vueltas (30 ballenas)", "#5e3c99", "o"),
              ("n_ballenas", "más ballenas (200 vueltas)", "#8c510a", "s")]
    nd, md = PARAMS_DEFAULT["n_ballenas"], PARAMS_DEFAULT["max_iter"]
    for k, (ax, nom) in enumerate(zip(axs, nombres), start=1):
        datos, seg_por_mov = {}, []
        for par, *_ in series:
            df = pd.read_csv(os.path.join(res, f"{k}_{nom}", f"{par}.csv"))
            if par == "max_iter":
                movs = nd * df[par].to_numpy()
            else:
                movs = df[par].to_numpy() * md
            datos[par] = (movs, df["mediana"].to_numpy(), df[par].to_numpy())
            seg_por_mov += list(df["tiempo_medio_s"].to_numpy() / movs)
        todos = np.concatenate([d[1] for d in datos.values()])
        pos = todos[todos > 0]
        piso = 10.0 ** (np.floor(np.log10(pos.min())) - 1) if len(pos) \
            else 1e-16
        for par, et, color, marca in series:
            movs, med, vals = datos[par]
            ax.plot(movs, np.maximum(med, piso), marker=marca, color=color,
                    lw=2, ms=7, label=et)
            for x, y, v in zip(movs, np.maximum(med, piso), vals):
                if x != nd * md:
                    ax.annotate(f"{int(v)}", (x, y), xytext=(0, 7),
                                textcoords="offset points", ha="center",
                                fontsize=8, color=color)
        ax.plot([nd * md], [max(datos["max_iter"][1][
            list(datos["max_iter"][2]).index(md)], piso)], "*", ms=16,
            color="#2b8cbe", mec="white", zorder=5, label="por defecto")
        ax.set_xscale("log")
        ax.set_yscale("log")
        if (todos <= 0).any():
            ks = np.arange(np.ceil(np.log10(piso)) + 1,
                           np.floor(np.log10(max(todos.max(), piso * 10)))
                           + 1)
            ks = ks[::max(1, int(np.ceil(len(ks) / 5)))]
            ax.axhline(piso, color="gray", lw=0.8, ls=":")
            ax.set_yticks([piso] + [10.0 ** e for e in ks],
                          ["0"] + [f"$10^{{{int(e)}}}$" for e in ks])
            ax.minorticks_off()
        ax.set_title(nom, fontweight="bold")
        marcas = [1500, 3000, 6000, 10000, 20000]
        ax.set_xticks(marcas, [f"{m:,}" for m in marcas], fontsize=8)
        ax.minorticks_off()
        ax.set_xlim(1200, 25000)
        ax.set_xlabel("esfuerzo (ballenas × vueltas)")
        ax.grid(alpha=0.3)
        s = float(np.median(seg_por_mov))      # segundos por movimiento
        arriba = ax.secondary_xaxis("top", functions=(lambda m, s=s: m * s,
                                                      lambda t, s=s: t / s))
        segs = [t for t in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
                if 1200 * s <= t <= 25000 * s]
        arriba.set_xticks(segs, [f"{t:g} s" for t in segs])
        arriba.minorticks_off()
        arriba.set_xlabel("≈ segundos por corrida", fontsize=8.5)
        arriba.tick_params(labelsize=8)
    axs[0].set_ylabel("mediana del mejor valor (log)")
    manijas, textos = axs[0].get_legend_handles_labels()
    fig.legend(manijas, textos, loc="lower center", ncol=3, fontsize=10,
               bbox_to_anchor=(0.5, -0.1), frameon=False)
    fig.suptitle("¿Vale la pena gastar más tiempo? Más a la derecha = más "
                 "tiempo; más abajo = mejor resultado (30 corridas por punto)",
                 fontsize=12, y=1.05)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)


def generar_todo(n, n_comb, plt):
    """Corre todos los experimentos y escribe resultados/ (~20 min)."""
    # Estructura: resultados/0_base/ y una carpeta por funcion, numeradas en
    # el orden de Wikipedia (1_Rastrigin, 2_Ackley, ...).
    os.makedirs("resultados/0_base", exist_ok=True)

    # 1) Tabla base: parametros del paper, 30 corridas por funcion
    filas = []
    plt.figure(figsize=(8, 5))
    for nombre in FUNCIONES:
        fin, cur, tie = correr(nombre, n_corridas=n)
        filas.append({"funcion": nombre, **resumen(fin, tie)})
        plt.semilogy(np.mean(cur, axis=0) + 1e-300, label=nombre)
    pd.DataFrame(filas).to_csv("resultados/0_base/resumen.csv", index=False)
    plt.xlabel("Vuelta"); plt.ylabel("Mejor valor (promedio, escala log)")
    plt.legend()
    plt.title("Cómo va mejorando cada función (valores por defecto)")
    plt.tight_layout(); plt.savefig("resultados/0_base/convergencia.png", dpi=150)
    plt.close()
    print("base listo")

    # 2) Barridos de parametros por funcion
    todos_finales = {}
    for num, nombre in enumerate(FUNCIONES, start=1):
        carpeta = f"resultados/{num}_{nombre}"
        os.makedirs(carpeta, exist_ok=True)
        for par, vals in BARRIDOS.items():
            df, fin_d, cur_d = barrido(nombre, par, vals, n_corridas=n)
            todos_finales.setdefault(nombre, {})[par] = fin_d
            df.to_csv(f"{carpeta}/{par}.csv", index=False)
            fig, ax = plt.subplots(1, 2, figsize=(11, 4))
            ax[0].boxplot([fin_d[v] for v in vals], tick_labels=[str(v) for v in vals])
            ax[0].set_yscale("symlog", linthresh=1e-12)
            ax[0].set_xlabel(NOMBRES_PAR[par])
            ax[0].set_ylabel("Mejor valor final")
            ax[0].set_title("Resultado de cada corrida")
            for v in vals:
                ax[1].semilogy(np.mean(cur_d[v], axis=0) + 1e-300,
                               label=f"{NOMBRES_PAR[par]} = {v}")
            ax[1].set_xlabel("Vuelta")
            ax[1].set_ylabel("Mejor valor (promedio)")
            ax[1].set_title("Cómo fue mejorando")
            ax[1].legend()
            fig.suptitle(f"{nombre}: efecto de {NOMBRES_PAR[par].lower()}")
            fig.tight_layout()
            fig.savefig(f"{carpeta}/{par}.png", dpi=130)
            plt.close(fig)
        print(nombre, "listo")
    guardar_panorama(todos_finales, plt)

    # 3) Sesgo al centro: misma funcion con el optimo movido de lugar, y
    #    a donde llegan las corridas de Rosenbrock
    experimento_sesgo(n, plt)
    experimento_rosenbrock(n, plt)

    # 4) Combinaciones de a, b y p con el mismo esfuerzo
    experimento_combinaciones(n_comb, plt)

    # 5) Tabla 1 del reporte: 25 ejecuciones por funcion (1 corrida cada
    #    una; no depende de --rapido)
    experimento_tabla_25(plt)


if __name__ == "__main__":
    main()
