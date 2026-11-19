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

from funciones import FUNCIONES
from woa import woa

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


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    n = 5 if args.rapido else 30
    os.makedirs("resultados", exist_ok=True)

    # 1) Tabla base: parametros del paper, 30 corridas por funcion
    filas = []
    plt.figure(figsize=(8, 5))
    for nombre in FUNCIONES:
        fin, cur, tie = correr(nombre, n_corridas=n)
        filas.append({"funcion": nombre, **resumen(fin, tie)})
        plt.semilogy(np.mean(cur, axis=0) + 1e-300, label=nombre)
    pd.DataFrame(filas).to_csv("resultados/base.csv", index=False)
    plt.xlabel("Iteracion"); plt.ylabel("Mejor fitness medio (log)")
    plt.legend(); plt.title("Convergencia con parametros por defecto")
    plt.tight_layout(); plt.savefig("resultados/base_convergencia.png", dpi=150)
    plt.close()
    print("base listo")

    # 2) Barridos de parametros por funcion
    for nombre in FUNCIONES:
        for par, vals in BARRIDOS.items():
            df, fin_d, cur_d = barrido(nombre, par, vals, n_corridas=n)
            df.to_csv(f"resultados/{nombre}_{par}.csv", index=False)
            fig, ax = plt.subplots(1, 2, figsize=(11, 4))
            ax[0].boxplot([fin_d[v] for v in vals], tick_labels=[str(v) for v in vals])
            ax[0].set_yscale("symlog", linthresh=1e-12)
            ax[0].set_xlabel(par); ax[0].set_ylabel("Mejor fitness final")
            for v in vals:
                ax[1].semilogy(np.mean(cur_d[v], axis=0) + 1e-300, label=f"{par}={v}")
            ax[1].set_xlabel("Iteracion"); ax[1].legend()
            fig.suptitle(f"{nombre}: efecto de {par}")
            fig.tight_layout()
            fig.savefig(f"resultados/{nombre}_{par}.png", dpi=130)
            plt.close(fig)
        print(nombre, "listo")


if __name__ == "__main__":
    main()
