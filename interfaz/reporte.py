"""
Mantiene al dia la guia del reporte (docs/reporte_referencia.md) con los CSV
de resultados/:

- Las tablas entre <!-- auto:ID --> y <!-- /auto --> se vuelven a escribir
  desde los CSV (Anexo A completo).
- Los numeros escritos a mano en el texto (lista NUMEROS) no se tocan, pero
  revisar() dice cuales ya no coinciden con los CSV.

experimentos.py llama a actualizar_reporte() al terminar; las pruebas usan
NUMEROS y coincide().
"""
import math
import os
import re

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
REPORTE = os.path.join(RAIZ, "docs", "reporte_referencia.md")

FUNCIONES_ORDEN = ["Rastrigin", "Ackley", "Sphere", "Rosenbrock", "Beale"]
PARAMS = ["n_ballenas", "max_iter", "a_inicial", "b", "p_umbral"]
ETIQUETA_PAR = {"n_ballenas": "Número de ballenas",
                "max_iter": "Vueltas (iteraciones)",
                "a_inicial": "`a` inicial", "b": "`b` (espiral)",
                "p_umbral": "Umbral de `p`"}
DEFECTO = {"n_ballenas": 30, "max_iter": 200, "a_inicial": 2.0, "b": 1.0,
           "p_umbral": 0.5}


# --------------------------------------------------------------------------
# Tablas automaticas (Anexo A)
# --------------------------------------------------------------------------
def fmt(x):
    """Formato de las tablas del anexo: 0, 2.84e-14, 0.0153, 59.7."""
    if x == 0:
        return "0"
    return f"{x:.2e}" if abs(x) < 0.01 else f"{x:.3g}"


def _fila(celdas):
    return "| " + " | ".join(celdas) + " |"


def _tabla(encabezado, filas):
    return "\n".join([_fila(encabezado), "|" + "---|" * len(encabezado)]
                     + [_fila(f) for f in filas])


def tabla_base(res=RES):
    df = pd.read_csv(os.path.join(res, "0_base", "resumen.csv"))
    filas = [[r.funcion, fmt(r.media), fmt(r.mediana), fmt(r.desv_est),
              fmt(r.mejor), fmt(r.peor), f"{r.tiempo_medio_s:.3f}"]
             for r in df.itertuples()]
    return _tabla(["Función", "Media", "Mediana", "Desv. est.", "Mejor",
                   "Peor", "Seg/corrida"], filas)


def tabla_funcion(num, nombre, res=RES):
    filas = []
    for par in PARAMS:
        df = pd.read_csv(os.path.join(res, f"{num}_{nombre}", f"{par}.csv"))
        for r in df.to_dict("records"):
            v = r[par]
            txt = f"{int(v)}" if par in ("n_ballenas", "max_iter") else f"{v:g}"
            if np.isclose(v, DEFECTO[par]):
                txt = f"**{txt}**"
            filas.append([ETIQUETA_PAR[par], txt, fmt(r["media"]),
                          fmt(r["mediana"]), fmt(r["desv_est"]),
                          fmt(r["mejor"]), fmt(r["peor"])])
    return _tabla(["Parámetro", "Valor", "Media", "Mediana", "Desv. est.",
                   "Mejor", "Peor"], filas)


def tabla_sesgo(res=RES):
    df = pd.read_csv(os.path.join(res, "6_sesgo_centro", "resumen.csv"))
    filas = [[r.funcion, str(int(r.dim)), f"{r.optimo_en:g}", fmt(r.media),
              fmt(r.mediana), fmt(r.desv_est), fmt(r.mejor), fmt(r.peor)]
             for r in df.itertuples()]
    return _tabla(["Función", "Variables", "Mínimo en", "Media", "Mediana",
                   "Desv. est.", "Mejor", "Peor"], filas)


def tabla_25(res=RES):
    """Tabla 1 del reporte (25 ejecuciones, 1 corrida cada una) con el mejor
    valor de cada funcion. Los ajustes son los de las funciones de n
    variables; la fila 25 (*) es distinta en Ackley y Beale."""
    df = pd.read_csv(os.path.join(res, "9_tabla_25", "corridas.csv"))
    n_var = df[df.funcion == "Rastrigin"].set_index("ejecucion")
    filas = []
    for k, r in n_var.iterrows():
        dims = f"{int(r.dim)} / 2" + ("*" if k == 25 else "")
        fila = [str(k), r.bloque, str(int(r.n_ballenas)),
                str(int(r.max_iter)), f"{r.a_inicial:g}", f"{r.b:g}",
                f"{r.p_umbral:g}", dims, str(int(r.seed))]
        for nom in FUNCIONES_ORDEN:
            fila.append(fmt(df[(df.funcion == nom)
                               & (df.ejecucion == k)].mejor_f.iloc[0]))
        filas.append(fila)
    return _tabla(["#", "Bloque", "Ballenas", "Vueltas", "a", "b", "p",
                   "Variables", "Semilla"] + FUNCIONES_ORDEN, filas)


def bloques(res=RES):
    """ID del bloque -> tabla en markdown."""
    b = {"anexo_base": tabla_base(res), "anexo_sesgo": tabla_sesgo(res),
         "anexo_tabla25": tabla_25(res)}
    for num, nom in enumerate(FUNCIONES_ORDEN, start=1):
        b[f"anexo_{nom.lower()}"] = tabla_funcion(num, nom, res)
    return b


BLOQUE = re.compile(r"(<!-- auto:(\w+) -->\n)(.*?)(\n<!-- /auto -->)", re.S)


def actualizar_texto(texto, res=RES):
    """Reescribe cada bloque automatico. Devuelve (texto, ids cambiados)."""
    nuevos, cambiados = bloques(res), []

    def cambiar(m):
        ident = m.group(2)
        if ident not in nuevos:
            raise KeyError(f"bloque desconocido en el reporte: {ident}")
        if m.group(3) != nuevos[ident]:
            cambiados.append(ident)
        return m.group(1) + nuevos[ident] + m.group(4)

    return BLOQUE.sub(cambiar, texto), cambiados


# --------------------------------------------------------------------------
# Numeros escritos a mano en el texto
# --------------------------------------------------------------------------
B, S, C = "0_base/resumen.csv", "6_sesgo_centro/resumen.csv", \
    "8_combinaciones/resumen.csv"
ROS = "6_sesgo_centro/rosenbrock.csv"
T25 = "9_tabla_25/corridas.csv"


def _t25(f, k, escrito):
    """Mejor valor de la ejecucion k (Tabla 1, 1 corrida) en la funcion f."""
    return (T25, {"funcion": f, "ejecucion": k}, "mejor_f", escrito)


def _base(f, col, escrito):
    return (B, {"funcion": f}, col, escrito)


def _par(carpeta, par, v, col, escrito):
    return (f"{carpeta}/{par}.csv", {par: v}, col, escrito)


def _combo(f, nb, a, b, p, col, escrito):
    return (C, {"funcion": f, "n_ballenas": nb, "a_inicial": a, "b": b,
                "p_umbral": p}, col, escrito)


D = (30, 2.0, 1.0, 0.5)     # combinacion por defecto (ballenas, a, b, p)

# (archivo, filtros, columna, como esta escrito en el reporte)
NUMEROS = [
    _base("Rastrigin", "mediana", "0"), _base("Rastrigin", "media", "1.9e-15"),
    _base("Rastrigin", "peor", "2.8e-14"),
    _base("Ackley", "mediana", "3.6e-15"), _base("Ackley", "media", "3.9e-15"),
    _base("Ackley", "peor", "1.4e-14"),
    _base("Sphere", "mediana", "1.8e-34"), _base("Sphere", "media", "9.9e-32"),
    _base("Sphere", "peor", "2.7e-30"),
    _base("Rosenbrock", "mediana", "8.56"),
    _base("Rosenbrock", "media", "5.43"), _base("Rosenbrock", "peor", "8.90"),
    _base("Beale", "mediana", "8.8e-9"), _base("Beale", "media", "0.10"),
    _base("Beale", "peor", "0.76"),
    # vueltas
    _par("3_Sphere", "max_iter", 50, "mediana", "4.6e-6"),
    _par("3_Sphere", "max_iter", 100, "mediana", "1.9e-16"),
    _par("3_Sphere", "max_iter", 500, "mediana", "1.4e-89"),
    _par("1_Rastrigin", "max_iter", 50, "peor", "59.7"),
    _par("1_Rastrigin", "max_iter", 100, "peor", "49.8"),
    _par("1_Rastrigin", "max_iter", 500, "peor", "0"),
    _par("4_Rosenbrock", "max_iter", 50, "mediana", "8.90"),
    _par("4_Rosenbrock", "max_iter", 100, "mediana", "8.72"),
    _par("4_Rosenbrock", "max_iter", 500, "mediana", "0.40"),
    # ballenas
    _par("4_Rosenbrock", "n_ballenas", 10, "mediana", "8.90"),
    _par("4_Rosenbrock", "n_ballenas", 50, "mediana", "0.91"),
    _par("4_Rosenbrock", "n_ballenas", 100, "mediana", "0.12"),
    _par("3_Sphere", "n_ballenas", 10, "mediana", "8.1e-24"),
    _par("3_Sphere", "n_ballenas", 50, "mediana", "6.0e-39"),
    _par("3_Sphere", "n_ballenas", 100, "mediana", "7.3e-45"),
] + [_par("5_Beale", "n_ballenas", n, "peor", "0.76")
     for n in (10, 30, 50, 100)] + [
    # a inicial, p, b
    _par("4_Rosenbrock", "a_inicial", 1.0, "mediana", "8.92"),
    _par("4_Rosenbrock", "a_inicial", 3.0, "mediana", "0.09"),
    _par("3_Sphere", "a_inicial", 1.0, "mediana", "2.1e-36"),
    _par("3_Sphere", "a_inicial", 3.0, "mediana", "4.7e-26"),
    _par("1_Rastrigin", "a_inicial", 1.0, "peor", "25.4"),
    _par("4_Rosenbrock", "p_umbral", 0.2, "mediana", "8.43"),
    _par("4_Rosenbrock", "p_umbral", 0.8, "mediana", "0.26"),
    _par("1_Rastrigin", "p_umbral", 0.2, "peor", "33.1"),
    _par("4_Rosenbrock", "b", 2.0, "mediana", "0.66"),
    # sesgo al centro (seccion 4.3)
    (S, {"funcion": "Sphere", "caso": "original"}, "mediana", "1.8e-34"),
    (S, {"funcion": "Sphere", "caso": "desplazada"}, "mediana", "2.34"),
    (S, {"funcion": "Rastrigin", "caso": "original"}, "mediana", "0"),
    (S, {"funcion": "Rastrigin", "caso": "desplazada"}, "mediana", "9.84"),
    (S, {"funcion": "Ackley", "caso": "original"}, "mediana", "3.6e-15"),
    (S, {"funcion": "Ackley", "caso": "desplazada"}, "mediana", "0.028"),
    # Rosenbrock: a donde llegan las corridas (seccion 4.4)
    (ROS, {"caso": "Por defecto"}, "al_centro", "17"),
    (ROS, {"caso": "Por defecto"}, "al_minimo", "13"),
    (ROS, {"caso": "500 vueltas"}, "al_centro", "6"),
    (ROS, {"caso": "500 vueltas"}, "al_minimo", "23"),
    (ROS, {"caso": "500 vueltas"}, "mediana", "0.40"),
    (ROS, {"caso": "a = 3"}, "al_centro", "0"),
    (ROS, {"caso": "a = 3"}, "al_minimo", "29"),
    (ROS, {"caso": "a = 3"}, "mediana", "0.092"),
    (ROS, {"caso": "Mejor combinación"}, "al_centro", "0"),
    (ROS, {"caso": "Mejor combinación"}, "al_minimo", "30"),
    (ROS, {"caso": "Mejor combinación"}, "mediana", "0.023"),
    (ROS, {"caso": "Por defecto"}, "valor_centro_min", "8.2"),
    (ROS, {"caso": "Por defecto"}, "valor_centro_max", "8.9"),
    # combinaciones (seccion 4.6)
    _combo("Ackley", 10, 2.0, 1.0, 0.8, "mediana", "0"),
    _combo("Ackley", *D, "mediana", "3.6e-15"),
    _combo("Ackley", *D, "lugar", "56"),
    _combo("Rastrigin", *D, "lugar", "21"),
    _combo("Sphere", 10, 2.0, 1.0, 0.5, "mediana", "7.4e-80"),
    _combo("Sphere", *D, "mediana", "2.0e-34"),
    _combo("Sphere", *D, "lugar", "33"),
    _combo("Rosenbrock", 10, 3.0, 0.5, 0.8, "mediana", "0.020"),
    _combo("Rosenbrock", *D, "mediana", "8.57"),
    _combo("Rosenbrock", *D, "lugar", "47"),
    _combo("Beale", 60, 3.0, 2.0, 0.2, "mediana", "1.7e-15"),
    _combo("Beale", *D, "mediana", "7.8e-9"),
    _combo("Beale", *D, "lugar", "38"),
    _combo("Rastrigin", 60, 1.0, 0.5, 0.2, "mediana", "32.8"),
    _combo("Rastrigin", 10, 1.0, 0.5, 0.2, "mediana", "15"),
] + [
    # Tabla 1: 25 ejecuciones, 1 corrida cada una (seccion 4.7)
    _t25("Rastrigin", 16, "51.8"), _t25("Rastrigin", 11, "6.1e-6"),
    _t25("Ackley", 11, "6.3e-8"), _t25("Ackley", 23, "5.7e-12"),
    _t25("Sphere", 11, "6.9e-5"), _t25("Sphere", 15, "1.4e-185"),
    _t25("Sphere", 23, "1.3e-11"), _t25("Sphere", 25, "2.2e-33"),
    _t25("Rosenbrock", 1, "6.15"), _t25("Rosenbrock", 2, "8.57"),
    _t25("Rosenbrock", 3, "0.17"), _t25("Rosenbrock", 4, "8.90"),
    _t25("Rosenbrock", 5, "0.15"),
    _t25("Rosenbrock", 18, "0.088"), _t25("Rosenbrock", 22, "0.071"),
    _t25("Rosenbrock", 24, "0.025"), _t25("Rosenbrock", 25, "28.7"),
    _t25("Beale", 3, "0.76"),
]

# Conteos de la seccion 4.7 (los revisa test_resultados)
CONTEOS_T25 = {"rastrigin_ceros": 21, "rosenbrock_arriba_7.5": 14,
               "rosenbrock_abajo_0.5": 8}

# Lugares promedio de la seccion 4.6 (figura mapa.png):
# (funcion, grupo, valor, lugar escrito)
R_, A_, B_, P_ = "Ballenas × vueltas", "a inicial", "b (espiral)", \
    "p (umbral)"
LUGARES = [("Rastrigin", R_, 10, 18), ("Rastrigin", R_, 60, 61),
           ("Rastrigin", A_, 1.0, 51), ("Rastrigin", P_, 0.2, 53),
           ("Sphere", R_, 10, 14), ("Sphere", R_, 60, 68),
           ("Sphere", B_, 0.5, 42), ("Sphere", B_, 1.0, 41),
           ("Sphere", B_, 2.0, 41),
           ("Rosenbrock", A_, 3.0, 21), ("Rosenbrock", A_, 1.0, 63),
           ("Beale", P_, 0.2, 16), ("Beale", P_, 0.8, 65)]


def coincide(real, escrito):
    """True si 'escrito' es 'real' redondeado a las cifras que tiene."""
    v = float(escrito)
    if v == 0:
        return real == 0
    mant = escrito.lower().split("e")[0].replace("-", "").replace(".", "")
    k = len(mant.lstrip("0"))                      # cifras significativas
    unidad = 10 ** (math.floor(math.log10(abs(v))) - k + 1)
    return abs(real - v) <= 0.5 * unidad * 1.0001


def valor(archivo, filtros, col, res=RES):
    df = pd.read_csv(os.path.join(res, archivo))
    m = np.ones(len(df), bool)
    for k, v in filtros.items():
        m &= (df[k] == v).to_numpy() if isinstance(v, str) \
            else np.isclose(df[k], v)
    if m.sum() != 1:
        raise ValueError(f"{archivo} {filtros}: {m.sum()} filas")
    return float(df.loc[m, col].iloc[0])


def lugares_reales(res=RES):
    from experimentos import lugar_promedio_por_valor
    df = pd.read_csv(os.path.join(res, C))
    return {nom: {(g, v): round(x) for g, v, x in filas}
            for nom, filas in lugar_promedio_por_valor(df).items()}


def revisar(res=RES):
    """Lista de textos con los numeros del reporte que ya no cuadran."""
    malos = []
    for archivo, filtros, col, escrito in NUMEROS:
        real = valor(archivo, filtros, col, res)
        if not coincide(real, escrito):
            malos.append(f"{archivo} {filtros} {col}: el reporte dice "
                         f"{escrito}, ahora da {real:.3g}")
    lp = lugares_reales(res)
    for nom, g, v, escrito in LUGARES:
        if lp[nom][(g, v)] != escrito:
            malos.append(f"lugar promedio {nom} {g}={v}: el reporte dice "
                         f"{escrito}, ahora da {lp[nom][(g, v)]}")
    return malos


def actualizar_reporte(ruta=REPORTE, res=RES):
    """Reescribe las tablas automaticas y avisa de numeros desactualizados.
    Devuelve (bloques cambiados, numeros a revisar)."""
    with open(ruta, encoding="utf-8") as fh:
        texto = fh.read()
    nuevo, cambiados = actualizar_texto(texto, res)
    if nuevo != texto:
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(nuevo)
    return cambiados, revisar(res)
