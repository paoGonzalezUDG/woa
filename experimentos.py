"""
Utilidades para correr experimentos con WOA y script para generar los
resultados del reporte (tablas CSV y graficas PNG en la carpeta resultados/).

Uso:  python experimentos.py            (corre todo; tarda unos minutos)
      python experimentos.py --rapido   (menos corridas, para probar)
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


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true",
                    help="5 corridas en vez de 30 (solo para probar)")
    ap.add_argument("--solo-sesgo", action="store_true",
                    help="correr solo el experimento de sesgo al centro")
    args = ap.parse_args()
    n = 5 if args.rapido else 30
    if args.solo_sesgo:
        experimento_sesgo(n, plt)
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
    for num, nombre in enumerate(FUNCIONES, start=1):
        carpeta = f"resultados/{num}_{nombre}"
        os.makedirs(carpeta, exist_ok=True)
        for par, vals in BARRIDOS.items():
            df, fin_d, cur_d = barrido(nombre, par, vals, n_corridas=n)
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

    # 3) Sesgo al centro: misma funcion con el optimo movido de lugar
    experimento_sesgo(n, plt)


if __name__ == "__main__":
    main()
