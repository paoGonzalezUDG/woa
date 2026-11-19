"""
Primeras 5 funciones de prueba de la pagina de Wikipedia
"Test functions for optimization" (en el orden en que aparecen):

    1. Rastrigin   (n dimensiones)
    2. Ackley      (2 dimensiones)
    3. Sphere      (n dimensiones)
    4. Rosenbrock  (n dimensiones)
    5. Beale       (2 dimensiones)

Todas son de MINIMIZACION. Cada funcion recibe un vector numpy x.

Dominios de busqueda:
  - Rastrigin (+-5.12), Ackley (+-5) y Beale (+-4.5) son los de Wikipedia.
  - Sphere y Rosenbrock aparecen en Wikipedia con dominio infinito, asi que
    hay que ELEGIR un rango finito. Usamos +-100 (Sphere) y +-30 (Rosenbrock).
    Es una decision nuestra: se puede cambiar en la interfaz y debe
    mencionarse en el reporte.
"""
import numpy as np


def rastrigin(x, A=10.0):
    x = np.asarray(x)
    return A * len(x) + np.sum(x ** 2 - A * np.cos(2 * np.pi * x))


def ackley(x):
    x, y = x[0], x[1]
    return (-20.0 * np.exp(-0.2 * np.sqrt(0.5 * (x ** 2 + y ** 2)))
            - np.exp(0.5 * (np.cos(2 * np.pi * x) + np.cos(2 * np.pi * y)))
            + np.e + 20.0)


def sphere(x):
    x = np.asarray(x)
    return np.sum(x ** 2)


def rosenbrock(x):
    x = np.asarray(x)
    return np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1.0 - x[:-1]) ** 2)


def beale(x):
    x, y = x[0], x[1]
    return ((1.5 - x + x * y) ** 2
            + (2.25 - x + x * y ** 2) ** 2
            + (2.625 - x + x * y ** 3) ** 2)


# dim = None  -> el usuario puede elegir la dimension
# dim = 2     -> la funcion solo esta definida para 2 variables
FUNCIONES = {
    "Rastrigin": dict(
        f=rastrigin, dim=None, dim_default=10, lb=-5.12, ub=5.12,
        optimo_x=lambda n: np.zeros(n), optimo_f=0.0,
        formula="f(x) = 10n + sum[ x_i^2 - 10 cos(2 pi x_i) ]"),
    "Ackley": dict(
        f=ackley, dim=2, dim_default=2, lb=-5.0, ub=5.0,
        optimo_x=lambda n: np.zeros(2), optimo_f=0.0,
        formula="f(x,y) = -20 exp(-0.2 sqrt(0.5(x^2+y^2))) "
                "- exp(0.5(cos 2 pi x + cos 2 pi y)) + e + 20"),
    "Sphere": dict(
        f=sphere, dim=None, dim_default=10, lb=-100.0, ub=100.0,
        optimo_x=lambda n: np.zeros(n), optimo_f=0.0,
        formula="f(x) = sum x_i^2"),
    "Rosenbrock": dict(
        f=rosenbrock, dim=None, dim_default=10, lb=-30.0, ub=30.0,
        optimo_x=lambda n: np.ones(n), optimo_f=0.0,
        formula="f(x) = sum[ 100 (x_{i+1} - x_i^2)^2 + (1 - x_i)^2 ]"),
    "Beale": dict(
        f=beale, dim=2, dim_default=2, lb=-4.5, ub=4.5,
        optimo_x=lambda n: np.array([3.0, 0.5]), optimo_f=0.0,
        formula="f(x,y) = (1.5 - x + xy)^2 + (2.25 - x + xy^2)^2 "
                "+ (2.625 - x + xy^3)^2"),
}
