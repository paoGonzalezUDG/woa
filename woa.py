"""
Whale Optimization Algorithm (WOA) - Mirjalili y Lewis (2016),
Advances in Engineering Software 95, 51-67.

Idea: cada "ballena" es una solucion candidata. La mejor solucion encontrada
hasta el momento es la "presa". En cada iteracion, cada ballena se mueve con
UNA de tres reglas:

  1) Rodear la presa      (p < 0.5 y |A| < 1)  -> EXPLOTACION
  2) Buscar otra presa    (p < 0.5 y |A| >= 1) -> EXPLORACION
  3) Espiral (burbujas)   (p >= 0.5)           -> EXPLOTACION

Parametros que controlan el comportamiento (los que exploramos en los
experimentos):
  n_ballenas  tamano de la poblacion
  max_iter    numero de iteraciones
  a_inicial   valor inicial de 'a' (el paper usa 2; baja linealmente hasta 0)
  b           forma de la espiral logaritmica (el paper usa 1)
  p_umbral    umbral de p para elegir entre (1,2) y (3) (el paper usa 0.5)

Decisiones de implementacion propias (no vienen impuestas por la teoria):
  - A y C son escalares por ballena e iteracion (asi la regla |A| < 1 queda
    bien definida).
  - Las posiciones que salen del dominio se recortan al limite (np.clip).
  - l se muestrea uniforme en [-1, 1].
"""
import numpy as np


def woa(f, lb, ub, dim, n_ballenas=30, max_iter=200, a_inicial=2.0,
        b=1.0, p_umbral=0.5, seed=None, guardar_posiciones=False):
    """Minimiza f en [lb, ub]^dim. Devuelve un diccionario con resultados."""
    rng = np.random.default_rng(seed)

    # --- 1. Inicializacion: ballenas aleatorias dentro del dominio ---------
    X = rng.uniform(lb, ub, size=(n_ballenas, dim))
    fit = np.array([f(x) for x in X])

    i_mejor = np.argmin(fit)
    mejor_x = X[i_mejor].copy()          # X*  (la presa)
    mejor_f = fit[i_mejor]

    curva = [mejor_f]                    # mejor fitness en cada iteracion
    # Solo para visualizar (no cambian el algoritmo): posiciones, presa y
    # que regla uso cada ballena (0 rodear, 1 buscar, 2 espiral) por iteracion.
    posiciones = [X.copy()] if guardar_posiciones else None
    presas = [mejor_x.copy()] if guardar_posiciones else None
    reglas = [] if guardar_posiciones else None
    regla = np.zeros(n_ballenas, dtype=int)

    # --- 2. Ciclo principal ------------------------------------------------
    for t in range(max_iter):
        # 'a' baja linealmente de a_inicial a 0: al inicio |A| puede ser > 1
        # (explora); al final |A| < 1 casi siempre (explota).
        a = a_inicial * (1 - t / max_iter)

        for i in range(n_ballenas):
            r1, r2 = rng.random(), rng.random()
            A = 2 * a * r1 - a           # Ec. (3): A en [-a, a]
            C = 2 * r2                   # Ec. (4): C en [0, 2]
            l = rng.uniform(-1, 1)
            p = rng.random()

            if p < p_umbral:
                if abs(A) < 1:
                    # (1) Rodear la presa: ir hacia la mejor solucion
                    D = np.abs(C * mejor_x - X[i])
                    X[i] = mejor_x - A * D
                    regla[i] = 0
                else:
                    # (2) Busqueda: ir hacia una ballena elegida al azar
                    x_rand = X[rng.integers(n_ballenas)]
                    D = np.abs(C * x_rand - X[i])
                    X[i] = x_rand - A * D
                    regla[i] = 1
            else:
                # (3) Espiral logaritmica alrededor de la presa
                D = np.abs(mejor_x - X[i])
                X[i] = D * np.exp(b * l) * np.cos(2 * np.pi * l) + mejor_x
                regla[i] = 2

        # Mantener las ballenas dentro del dominio
        X = np.clip(X, lb, ub)

        # Evaluar y actualizar la mejor solucion (la presa)
        fit = np.array([f(x) for x in X])
        i_mejor = np.argmin(fit)
        if fit[i_mejor] < mejor_f:
            mejor_f = fit[i_mejor]
            mejor_x = X[i_mejor].copy()

        curva.append(mejor_f)
        if guardar_posiciones:
            posiciones.append(X.copy())
            presas.append(mejor_x.copy())
            reglas.append(regla.copy())

    return dict(mejor_x=mejor_x, mejor_f=float(mejor_f),
                curva=np.array(curva), posiciones=posiciones,
                presas=presas,
                reglas=np.array(reglas) if guardar_posiciones else None)
