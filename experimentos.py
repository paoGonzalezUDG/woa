"""
Utilidades para correr experimentos con WOA y script para generar los
resultados del reporte (tablas CSV y graficas PNG en la carpeta resultados/).

Uso:  python experimentos.py            (corre todo; tarda unos minutos)
      python experimentos.py --rapido   (menos corridas, para probar)
      python experimentos.py --solo-panorama  (solo la figura 7_panorama)
      python experimentos.py --solo-combinaciones  (8_combinaciones, ~15 min)
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
        ax.boxplot(datos, tick_labels=["optimo en 0", f"optimo en {s:g}"])
        ax.set_yscale("symlog", linthresh=1e-12)
        ax.set_title(f"{nombre} ({dim} variables)")
    axs[0].set_ylabel("Mejor fitness final")
    fig.suptitle("Misma funcion, optimo movido de lugar (sesgo al centro)")
    fig.tight_layout()
    fig.savefig(f"{carpeta}/comparacion.png", dpi=130)
    plt.close(fig)
    pd.DataFrame(filas).to_csv(f"{carpeta}/resumen.csv", index=False)
    print("sesgo al centro listo")


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
    combos = combinaciones()
    crudos, filas = [], []
    for nombre in FUNCIONES:
        for c in combos:
            fin, _, tie = correr(nombre, n_corridas=n, **c)
            filas.append({"funcion": nombre, **c, **resumen(fin, tie)})
            crudos += [{"funcion": nombre, **c, "corrida": k,
                        "mejor_f": float(x)} for k, x in enumerate(fin)]
        print(nombre, "combinaciones listo")
    res = ordenar_combinaciones(pd.DataFrame(filas))
    res.to_csv(f"{carpeta}/resumen.csv", index=False)
    crudo = pd.DataFrame(crudos)
    crudo.to_csv(f"{carpeta}/finales.csv", index=False)
    figuras_combinaciones(res, crudo, plt, carpeta)


def rehacer_figuras_combinaciones(plt, carpeta="resultados/8_combinaciones"):
    """Vuelve a dibujar desde los CSV (sin correr nada ni reescribirlos)."""
    res = ordenar_combinaciones(pd.read_csv(f"{carpeta}/resumen.csv")
                                .drop(columns="lugar", errors="ignore"))
    figuras_combinaciones(res, pd.read_csv(f"{carpeta}/finales.csv"), plt,
                          carpeta)


def figuras_combinaciones(res, crudo, plt, carpeta):
    nombres = list(FUNCIONES)
    claves = list(PARAMS_DEFAULT)
    # 1) Cajas: las 5 mejores de cada funcion + la de por defecto
    fig, axs = plt.subplots(1, len(nombres), figsize=(18, 5))
    for ax, nom in zip(axs, nombres):
        r = res[res.funcion == nom]
        empatadas = int((r.lugar == 1).sum())
        top = r.head(5)
        dfl = r[r.apply(es_default, axis=1)]
        sel = pd.concat([top, dfl]).drop_duplicates(subset=claves)
        datos, etiquetas, colores = [], [], []
        for _, f in sel.iterrows():
            m = np.ones(len(crudo), bool)
            for k in claves:
                m &= np.isclose(crudo[k], f[k])
            y = crudo.loc[m & (crudo.funcion == nom), "mejor_f"].to_numpy()
            datos.append(y)
            etiquetas.append(
                f"#{int(f['lugar'])}\n{int(f['n_ballenas'])}x"
                f"{int(f['max_iter'])}\na={f['a_inicial']:g}\nb={f['b']:g}"
                f"\np={f['p_umbral']:g}")
            colores.append("#9ecae1" if es_default(f) else "white")
        pos = np.concatenate(datos)
        pos = pos[pos > 0]
        piso = 10.0 ** (np.floor(np.log10(pos.min())) - 1) if len(pos) else 1e-16
        cajas = ax.boxplot([np.maximum(d, piso) for d in datos],
                           patch_artist=True, showmeans=True, widths=0.6,
                           meanprops=dict(marker="D", markersize=5,
                                          markerfacecolor="#d62728",
                                          markeredgecolor="white"),
                           medianprops=dict(color="black", linewidth=1.5),
                           flierprops=dict(marker="o", markersize=3, alpha=0.5))
        for k, (caja, col) in enumerate(zip(cajas["boxes"], colores), 1):
            caja.set_facecolor(col)
            if col != "white":    # franja: se ve aunque la caja sea plana
                ax.axvspan(k - 0.45, k + 0.45, color="#deebf7", zorder=0)
        ax.set_xticks(range(1, len(etiquetas) + 1), etiquetas, fontsize=7.5)
        ax.set_yscale("log")
        if (np.concatenate(datos) <= 0).any():   # piso = "0" en el eje
            alto = max(np.concatenate(datos).max(), piso * 100)
            ks = np.arange(np.ceil(np.log10(piso)) + 1,
                           np.floor(np.log10(alto)) + 1)
            ks = ks[::max(1, int(np.ceil(len(ks) / 5)))]
            ax.axhline(piso, color="gray", lw=0.8, ls=":")
            ax.set_yticks([piso] + [10.0 ** k for k in ks],
                          ["0"] + [f"$10^{{{int(k)}}}$" for k in ks])
            ax.minorticks_off()
            ax.set_ylim(piso / 3, alto * 3)
        ax.grid(axis="y", alpha=0.3)
        ax.set_title(nom + (f"\n({empatadas} empatadas en 1er lugar)"
                            if empatadas > 1 else ""), fontweight="bold")
    axs[0].set_ylabel("mejor valor final (log)")
    fig.suptitle("Las 5 mejores combinaciones de cada función (azul = la de "
                 "por defecto, con su lugar). Mismo esfuerzo: 6000 movimientos",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(f"{carpeta}/mejores.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # 2) Cruce: la ganadora de cada funcion, ¿en que lugar queda en las demas?
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
                    help="solo el experimento de combinaciones (~15 min)")
    args = ap.parse_args()
    n_comb = 5 if args.rapido else N_COMBINACIONES
    n = 5 if args.rapido else 30
    if args.solo_sesgo:
        experimento_sesgo(n, plt)
        return
    if args.solo_panorama:
        experimento_panorama(n, plt)
        return
    if args.solo_combinaciones:
        experimento_combinaciones(n_comb, plt)
        return
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
    plt.xlabel("Iteracion"); plt.ylabel("Mejor fitness medio (log)")
    plt.legend(); plt.title("Convergencia con parametros por defecto")
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
            ax[0].set_xlabel(par); ax[0].set_ylabel("Mejor fitness final")
            for v in vals:
                ax[1].semilogy(np.mean(cur_d[v], axis=0) + 1e-300, label=f"{par}={v}")
            ax[1].set_xlabel("Iteracion"); ax[1].legend()
            fig.suptitle(f"{nombre}: efecto de {par}")
            fig.tight_layout()
            fig.savefig(f"{carpeta}/{par}.png", dpi=130)
            plt.close(fig)
        print(nombre, "listo")
    guardar_panorama(todos_finales, plt)

    # 3) Sesgo al centro: misma funcion con el optimo movido de lugar
    experimento_sesgo(n, plt)

    # 4) Combinaciones de a, b y p con el mismo esfuerzo
    experimento_combinaciones(n_comb, plt)


if __name__ == "__main__":
    main()
