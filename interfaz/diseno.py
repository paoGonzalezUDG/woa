"""
Tablas del diseno experimental (seccion 3 del reporte), armadas desde las
constantes de experimentos.py (PARAMS_DEFAULT, BARRIDOS, REPARTOS, SESGO,
CASOS_ROSENBROCK) y de algoritmo/funciones.py. Asi no se desfasan de lo que
realmente se corre.

- La app las muestra en Resultados > Diseño del experimento.
- `python -m interfaz.diseno` escribe docs/diseno_experimental.pdf
  (HTML impreso con Edge o Chrome en modo headless; no necesita librerias).
"""
import html
import os
import re
import subprocess
import tempfile

import pandas as pd

from algoritmo.funciones import FUNCIONES
from experimentos import (BARRIDOS, CARPETA_TABLA_25, CASOS_ROSENBROCK,
                          FILA_25_DOS_VARIABLES, N_COMBINACIONES,
                          PARAMS_DEFAULT, REPARTOS, SESGO, TABLA_25)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(RAIZ, "docs", "diseno_experimental.pdf")
CSV_TABLA_25 = os.path.join(RAIZ, CARPETA_TABLA_25, "corridas.csv")

# Corridas por configuracion: experimentos.main() usa 30 (5 con --rapido).
N_CORRIDAS = 30
# Zonas de busqueda que no vienen de Wikipedia (dominio infinito alla).
ZONA_ELEGIDA = {"Sphere", "Rosenbrock"}

NOMBRE_BLOQUE = {"n_ballenas": "Ballenas", "max_iter": "Vueltas",
                 "a_inicial": "Exploración (a)", "b": "Espiral (b)",
                 "p_umbral": "Umbral (p)"}
COLUMNAS_PAR = {"n_ballenas": "Ballenas", "max_iter": "Vueltas",
                "a_inicial": "a", "b": "b", "p_umbral": "p"}


def _g(x):
    return f"{x:g}"


def _miles(x):
    return f"{int(x):,}"


def _dims():
    """'10 / 2': variables de las funciones de n variables y de las de 2."""
    libres = sorted({c["dim_default"] for c in FUNCIONES.values()
                     if c["dim"] is None})
    fijas = sorted({c["dim"] for c in FUNCIONES.values() if c["dim"]})
    return " / ".join(str(d) for d in libres + fijas)


def _semillas(n):
    return f"0–{n - 1}"


def _que_se_ve(par, v):
    """Explicacion corta de la fila, comparando con el valor por defecto."""
    d = PARAMS_DEFAULT[par]
    if par == "n_ballenas":
        return "Menos ballenas que la base" if v < d else "Más ballenas que la base"
    if par == "max_iter":
        txt = "Menos vueltas que la base" if v < d else "Más vueltas que la base"
        return txt + (" (las del artículo)" if v == 500 else "")
    if par == "a_inicial":
        if v <= 1:
            return "Nunca busca otra presa (|A| < 1 siempre)"
        return ("Explora menos tiempo antes de afinar" if v < d
                else "Explora más tiempo antes de afinar")
    if par == "b":
        return "Espiral más cerrada" if v < d else "Espiral más abierta"
    espiral = round((1 - v) * 100)
    return f"~{espiral} % espiral, ~{100 - espiral} % rodear o buscar"


def _caso_rosenbrock(caso, cambios):
    """Si el caso mueve varios ajustes, los escribe entre parentesis."""
    if len(cambios) <= 1:
        return caso
    p = {**PARAMS_DEFAULT, **cambios}
    return (f"{caso} ({p['n_ballenas']}×{p['max_iter']}, "
            f"a = {_g(p['a_inicial'])}, b = {_g(p['b'])}, "
            f"p = {_g(p['p_umbral'])})")


# --------------------------------------------------------------------------
# Tablas
# --------------------------------------------------------------------------
def tabla_base():
    filas = [
        ("Ballenas (N)", _g(PARAMS_DEFAULT["n_ballenas"]), "Valor del artículo"),
        ("Vueltas", _g(PARAMS_DEFAULT["max_iter"]),
         "Lo elegimos nosotras para que no tardara tanto (el artículo usa "
         "500; falta verificarlo)"),
        ("a inicial", _g(PARAMS_DEFAULT["a_inicial"]),
         "Valor del artículo. Baja en línea recta; en la última vuelta vale "
         "a/vueltas (no llega a 0)"),
        ("b (espiral)", _g(PARAMS_DEFAULT["b"]), "Valor del artículo"),
        ("Umbral de p", _g(PARAMS_DEFAULT["p_umbral"]), "Valor del artículo"),
        ("Corridas por configuración", str(N_CORRIDAS),
         f"En los barridos (Tabla 5): semillas {_semillas(N_CORRIDAS)}, las "
         "mismas en todas. En la Tabla 3 es 1 corrida por fila, con la "
         "semilla indicada"),
    ]
    return pd.DataFrame(filas, columns=["Ajuste", "Valor", "Nota"])


def tabla_funciones():
    filas = []
    for i, (nom, c) in enumerate(FUNCIONES.items(), start=1):
        n = c["dim"] or c["dim_default"]
        x = ", ".join(_g(v) for v in c["optimo_x"](n))
        if n > 2:
            x = f"{_g(c['optimo_x'](n)[0])}, …, {_g(c['optimo_x'](n)[0])}"
        zona = f"{_g(c['lb'])} a {_g(c['ub'])}"
        filas.append({"#": i, "Función": nom,
                      "Variables": n if c["dim"] is None else f"{n} (fijo)",
                      "Zona de búsqueda": zona + (" *" if nom in ZONA_ELEGIDA
                                                  else ""),
                      "Mínimo": f"{_g(c['optimo_f'])} en ({x})"})
    return pd.DataFrame(filas)


def filas_barridos():
    """Base + cada valor distinto al de por defecto (un ajuste a la vez).
    Devuelve (DataFrame, lista con el conjunto de columnas que cambian)."""
    filas, cambia = [], []

    def fila(bloque, p, que):
        filas.append({"#": len(filas) + 1, "Bloque": bloque,
                      **{COLUMNAS_PAR[k]: _g(p[k]) for k in COLUMNAS_PAR},
                      "Variables": _dims(),
                      "Movimientos": _miles(p["n_ballenas"] * p["max_iter"]),
                      "Semillas": _semillas(N_CORRIDAS),
                      "Corridas": N_CORRIDAS, "Qué se ve": que})

    fila("Base", PARAMS_DEFAULT, "Punto de comparación para todo lo demás")
    cambia.append(set())
    for par, valores in BARRIDOS.items():
        for v in valores:
            if v == PARAMS_DEFAULT[par]:
                continue
            fila(NOMBRE_BLOQUE[par], {**PARAMS_DEFAULT, par: v},
                 _que_se_ve(par, v))
            cambia.append({COLUMNAS_PAR[par]})
    return pd.DataFrame(filas), cambia


def tabla_barridos():
    return filas_barridos()[0]


def filas_tabla_25():
    """Tabla 1 del reporte (diseno de Diana): 25 ejecuciones, 1 corrida cada
    una. Devuelve (DataFrame, lista con el conjunto de columnas que cambian
    en cada fila respecto a la base)."""
    fijas = {c["dim"] for c in FUNCIONES.values() if c["dim"]}
    filas, cambia = [], []
    for num, bloque, cambios, seed, texto in TABLA_25:
        p = {**PARAMS_DEFAULT, **{k: v for k, v in cambios.items()
                                  if k != "dim"}}
        if "dim" in cambios:
            dims = (f"{cambios['dim']} / "
                    + " / ".join(str(d) for d in sorted(fijas)) + "*")
        else:
            dims = _dims()
        filas.append({"#": num, "Bloque": bloque,
                      **{COLUMNAS_PAR[k]: _g(p[k]) for k in COLUMNAS_PAR},
                      "Variables": dims, "Semilla": seed,
                      "Qué se evalúa": texto})
        cols = {COLUMNAS_PAR[k] for k in cambios if k in COLUMNAS_PAR}
        if "dim" in cambios:
            cols.add("Variables")
        if bloque.startswith("1.") and seed != 0:
            cols.add("Semilla")
        cambia.append(cols)
    return pd.DataFrame(filas), cambia


def tabla_25():
    return filas_tabla_25()[0]


def nota_fila_25():
    """Texto de la fila 25 para las funciones de 2 variables."""
    dos = [n for n, c in FUNCIONES.items() if c["dim"] is not None]
    p = FILA_25_DOS_VARIABLES
    return (f"\\* Fila 25: las funciones de n variables pasan a 30 variables "
            f"(con los demás valores de la base). {' y '.join(dos)} solo "
            f"existen con 2 variables, así que en la fila 25 usan un ajuste "
            f"fino: {p['n_ballenas']} ballenas, {p['max_iter']} vueltas, "
            f"a = {_g(p['a_inicial'])}, b = {_g(p['b'])}, "
            f"p = {_g(p['p_umbral'])}.")


def tabla_25_resultados(df):
    """Mejor valor de cada ejecucion (filas) en cada funcion (columnas)."""
    t = df.pivot(index="ejecucion", columns="funcion", values="mejor_f")
    t = t[list(FUNCIONES)].reset_index().rename(columns={"ejecucion": "#"})
    return t


def tabla_adicionales():
    a = ", ".join(_g(v) for v in BARRIDOS["a_inicial"])
    b = ", ".join(_g(v) for v in BARRIDOS["b"])
    p = ", ".join(_g(v) for v in BARRIDOS["p_umbral"])
    rep = ", ".join(f"{nb}×{mi}" for nb, mi in REPARTOS)
    esfuerzo = _miles(REPARTOS[0][0] * REPARTOS[0][1])
    n_comb = len(REPARTOS) * len(BARRIDOS["a_inicial"]) * len(BARRIDOS["b"]) \
        * len(BARRIDOS["p_umbral"])
    nf = len(FUNCIONES)
    sesgo = ", ".join(f"{k} +{_g(v)}" for k, v in SESGO.items())
    ses_fun = ", ".join(f"{k} ({FUNCIONES[k]['dim'] or FUNCIONES[k]['dim_default']})"
                        for k in SESGO)
    casos = "; ".join(_caso_rosenbrock(c, cambios)
                      for c, cambios in CASOS_ROSENBROCK)
    ros_dim = FUNCIONES["Rosenbrock"]["dim_default"]
    filas = [
        {"Experimento": f"Combinaciones (mismo esfuerzo: {esfuerzo} "
                        "movimientos)",
         "Qué cambia": f"Reparto ballenas×vueltas ({rep}) × a ({a}) × "
                       f"b ({b}) × p ({p})",
         "Funciones": f"Las {nf}",
         "Configuraciones": f"{n_comb} por función ({n_comb * nf} en total)",
         "Semillas": _semillas(N_COMBINACIONES),
         "Corridas": f"{N_COMBINACIONES} por configuración = "
                     f"{_miles(n_comb * nf * N_COMBINACIONES)}"},
        {"Experimento": "Sesgo al centro",
         "Qué cambia": f"La misma función con el mínimo movido en cada eje "
                       f"({sesgo}), con los valores por defecto",
         "Funciones": ses_fun,
         "Configuraciones": "2 por función: original y movida",
         "Semillas": _semillas(N_CORRIDAS),
         "Corridas": f"{N_CORRIDAS} por caso = "
                     f"{_miles(len(SESGO) * 2 * N_CORRIDAS)}"},
        {"Experimento": "¿A dónde llega Rosenbrock?",
         "Qué cambia": casos,
         "Funciones": f"Rosenbrock ({ros_dim})",
         "Configuraciones": str(len(CASOS_ROSENBROCK)),
         "Semillas": _semillas(N_CORRIDAS),
         "Corridas": f"{N_CORRIDAS} por caso = "
                     f"{_miles(len(CASOS_ROSENBROCK) * N_CORRIDAS)}"},
    ]
    return pd.DataFrame(filas)


def totales():
    """Corridas ejecutadas por experimento (contando repeticiones)."""
    nf = len(FUNCIONES)
    n_comb = len(REPARTOS) * len(BARRIDOS["a_inicial"]) * len(BARRIDOS["b"]) \
        * len(BARRIDOS["p_umbral"])
    distintas = len(tabla_barridos())
    t = {
        "base": nf * N_CORRIDAS,
        "barridos": nf * sum(len(v) for v in BARRIDOS.values()) * N_CORRIDAS,
        "barridos_distintas": nf * distintas * N_CORRIDAS,
        "combinaciones": nf * n_comb * N_COMBINACIONES,
        "sesgo": len(SESGO) * 2 * N_CORRIDAS,
        "rosenbrock": len(CASOS_ROSENBROCK) * N_CORRIDAS,
        "tabla_25": nf * len(TABLA_25),
    }
    t["total"] = (t["base"] + t["barridos"] + t["combinaciones"] + t["sesgo"]
                  + t["rosenbrock"] + t["tabla_25"])
    return t


def notas():
    """Notas al pie (texto con **negritas** estilo markdown)."""
    t = totales()
    nf = len(FUNCIONES)
    distintas = len(tabla_barridos())
    return [
        f"**Tabla 3:** {len(TABLA_25)} ejecuciones por función, **una sola "
        f"corrida cada una** con la semilla indicada: {_miles(t['tabla_25'])} "
        f"corridas en las {nf} funciones (`{CARPETA_TABLA_25}/`). Con una "
        "sola corrida pesa mucho el azar: por ejemplo, en Beale la fila 3 "
        "(base, semilla 2) se atora en 0.76 y las filas 1, 2, 4 y 5 (misma "
        "configuración, otra semilla) no.",
        f"**Tabla 5:** en cada función son {distintas} configuraciones × "
        f"{N_CORRIDAS} corridas; en las {nf} funciones, "
        f"**{_miles(t['barridos_distintas'])} corridas distintas**. Son las "
        "que usan las gráficas de caja y las medianas del reporte. En los "
        "CSV de cada función la base aparece otra vez dentro de cada barrido "
        "(con las mismas semillas sale idéntica); por eso `finales.csv` "
        f"tiene {_miles(t['barridos'])} filas.",
        f"**Total ejecutado:** {_miles(t['tabla_25'])} (Tabla 3) + "
        f"{_miles(t['base'])} (base) + {_miles(t['barridos'])} (barridos) + "
        f"{_miles(t['combinaciones'])} (combinaciones) + "
        f"{_miles(t['sesgo'])} (sesgo) + {_miles(t['rosenbrock'])} "
        f"(Rosenbrock) = **{_miles(t['total'])} corridas**. Algunas se "
        "repiten: las filas de la Tabla 3 con la misma configuración y "
        "semilla que un barrido dan exactamente lo mismo.",
        "Mueven varios ajustes a la vez: las filas 23, 24 y 25 de la Tabla "
        "3, las combinaciones y la mejor combinación de Rosenbrock. En todo "
        "lo demás cambia un solo ajuste.",
        nota_fila_25(),
        "Sphere y Rosenbrock no tienen límite en Wikipedia: la zona de "
        "búsqueda (marcada con \\* en la Tabla 2) la elegimos nosotras.",
    ]


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def _negritas(txt):
    """**x** -> <b>x</b> y `x` -> <code>x</code> (texto ya escapado)."""
    txt = html.escape(txt).replace("\\*", "*")
    txt = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", txt)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", txt)


def _tabla_html(df, resaltar=None):
    cab = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    cuerpo = []
    for i, (_, fila) in enumerate(df.iterrows()):
        celdas = []
        for c, v in fila.items():
            clase = ' class="cambia"' if resaltar and c in resaltar[i] else ""
            celdas.append(f"<td{clase}>{html.escape(str(v))}</td>")
        cuerpo.append("<tr>" + "".join(celdas) + "</tr>")
    return (f"<table><thead><tr>{cab}</tr></thead><tbody>"
            + "".join(cuerpo) + "</tbody></table>")


def _corto(x):
    return "0" if x == 0 else f"{x:.2e}"


def html_diseno():
    barr, cambia = filas_barridos()
    t25, cambia25 = filas_tabla_25()
    nf = len(FUNCIONES)
    notas_html = "".join(f"<li>{_negritas(n)}</li>" for n in notas())
    if os.path.exists(CSV_TABLA_25):
        res = tabla_25_resultados(pd.read_csv(CSV_TABLA_25))
        for c in FUNCIONES:
            res[c] = res[c].map(_corto)
        res_html = (f"<h2>Tabla 4. Mejor valor de cada ejecución de la "
                    f"Tabla 3 (1 corrida)</h2>{_tabla_html(res)}")
    else:
        res_html = ""
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Diseño experimental - WOA</title>
<style>
@page {{ size: letter landscape; margin: 14mm; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; color: #1c2b3a;
        font-size: 10pt; }}
h1 {{ font-size: 17pt; margin: 0 0 2px; color: #12385c; }}
h2 {{ font-size: 12pt; margin: 18px 0 6px; color: #12385c;
      break-after: avoid; page-break-after: avoid; }}
p.sub {{ margin: 0 0 10px; color: #555; }}
table {{ border-collapse: collapse; width: 100%; page-break-inside: auto; }}
tr {{ page-break-inside: avoid; }}
th {{ background: #12385c; color: white; text-align: left;
      padding: 5px 6px; font-weight: 600; }}
td {{ border-bottom: 1px solid #d6dee6; padding: 4px 6px; }}
tbody tr:nth-child(even) td {{ background: #f4f7fa; }}
td.cambia {{ background: #d9ebf7 !important; font-weight: 700; }}
ul {{ padding-left: 18px; }} li {{ margin: 3px 0; }}
code {{ font-family: Consolas, monospace; font-size: 9pt; }}
.aviso {{ color: #555; font-size: 9pt; }}
</style></head><body>
<h1>Diseño experimental</h1>
<p class="sub">WOA sobre las 5 primeras funciones de Wikipedia. Generado desde
el código del proyecto (<code>experimentos.py</code>).</p>
<h2>Tabla 1. Valores por defecto (configuración base)</h2>
{_tabla_html(tabla_base())}
<h2>Tabla 2. Funciones de prueba</h2>
{_tabla_html(tabla_funciones())}
<h2>Tabla 3. Diseño experimental de {len(TABLA_25)} ejecuciones por función
matemática</h2>
<p class="aviso">Una corrida por fila. En azul, lo que cambia respecto a la
base. Variables: {_dims()} = las funciones de n variables / Ackley y Beale.
{_negritas(nota_fila_25())}</p>
{_tabla_html(t25, cambia25)}
{res_html}
<h2>Tabla 5. Barridos con {N_CORRIDAS} corridas por valor (los que usan las
gráficas; igual en las {nf} funciones)</h2>
{_tabla_html(barr, cambia)}
<h2>Tabla 6. Experimentos adicionales</h2>
{_tabla_html(tabla_adicionales())}
<h2>Notas</h2>
<ul>{notas_html}</ul>
</body></html>"""


NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def generar_pdf(ruta=PDF):
    """Imprime html_diseno() a PDF con Edge o Chrome (headless)."""
    exe = next((n for n in NAVEGADORES if os.path.exists(n)), None)
    if exe is None:
        raise RuntimeError("No encontre Edge ni Chrome para hacer el PDF.")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pagina = os.path.join(tmp, "diseno.html")
        with open(pagina, "w", encoding="utf-8") as fh:
            fh.write(html_diseno())
        subprocess.run([exe, "--headless", "--disable-gpu",
                        "--no-pdf-header-footer",
                        f"--user-data-dir={os.path.join(tmp, 'perfil')}",
                        f"--print-to-pdf={os.path.abspath(ruta)}",
                        "file:///" + pagina.replace("\\", "/")],
                       check=True, capture_output=True, timeout=120)
    return ruta


# --------------------------------------------------------------------------
# Que pasa en cada funcion (texto escrito a mano con numeros de
# resultados/7_panorama/finales.csv; DATOS los revisa una prueba)
# --------------------------------------------------------------------------
FINALES = os.path.join(RAIZ, "resultados", "7_panorama", "finales.csv")
# Arriba de esto una corrida cuenta como "atorada": Rosenbrock se queda
# cerca de 9 (el centro) y Beale en su minimo local (~0.76).
ATORADA = {"Rosenbrock": 7.5, "Beale": 0.5}
BASE = ("n_ballenas", 30)          # la base aparece dentro de cada barrido


def dato(fin, funcion, par, valor, que):
    """Un numero de finales.csv: mediana, peor, ceros (corridas en 0
    exacto), bajo_1e-8 o atoradas (ver ATORADA)."""
    s = fin[(fin.funcion == funcion) & (fin.parametro == par)
            & (fin.valor == valor)].mejor_f
    if que == "ceros":
        return int((s == 0).sum())
    if que == "bajo_1e-8":
        return int((s < 1e-8).sum())
    if que == "atoradas":
        return int((s > ATORADA[funcion]).sum())
    return float(getattr(s, "max" if que == "peor" else "median")())


# (funcion, parametro, valor, que, escrito): cada uno aparece en el texto
DATOS = [
    ("Rastrigin", *BASE, "ceros", "28"),
    ("Rastrigin", "max_iter", 50, "ceros", "0"),
    ("Rastrigin", "max_iter", 50, "peor", "59.7"),
    ("Rastrigin", "max_iter", 100, "peor", "49.8"),
    ("Rastrigin", "a_inicial", 1.0, "peor", "25.4"),
    ("Rastrigin", "p_umbral", 0.2, "peor", "33.1"),
    ("Ackley", *BASE, "mediana", "3.6e-15"),
    ("Ackley", "max_iter", 50, "mediana", "1.6e-8"),
    ("Ackley", "max_iter", 50, "bajo_1e-8", "11"),
    ("Ackley", "n_ballenas", 10, "mediana", "2.1e-14"),
    ("Sphere", *BASE, "mediana", "1.8e-34"),
    ("Sphere", "max_iter", 50, "mediana", "4.6e-6"),
    ("Sphere", "max_iter", 500, "mediana", "1.4e-89"),
    ("Sphere", "n_ballenas", 10, "mediana", "8.1e-24"),
    ("Sphere", "n_ballenas", 100, "mediana", "7.3e-45"),
    ("Sphere", "a_inicial", 3.0, "mediana", "4.7e-26"),
    ("Sphere", "a_inicial", 1.0, "mediana", "2.1e-36"),
    ("Sphere", "p_umbral", 0.2, "mediana", "7.7e-29"),
    ("Rosenbrock", *BASE, "atoradas", "17"),
    ("Rosenbrock", *BASE, "mediana", "8.56"),
    ("Rosenbrock", "a_inicial", 3.0, "mediana", "0.09"),
    ("Rosenbrock", "a_inicial", 3.0, "atoradas", "1"),
    ("Rosenbrock", "n_ballenas", 100, "mediana", "0.12"),
    ("Rosenbrock", "n_ballenas", 100, "atoradas", "2"),
    ("Rosenbrock", "p_umbral", 0.8, "mediana", "0.26"),
    ("Rosenbrock", "p_umbral", 0.8, "atoradas", "2"),
    ("Rosenbrock", "max_iter", 500, "mediana", "0.40"),
    ("Rosenbrock", "max_iter", 500, "atoradas", "6"),
    ("Rosenbrock", "b", 2.0, "mediana", "0.66"),
    ("Rosenbrock", "b", 2.0, "atoradas", "10"),
    ("Rosenbrock", "a_inicial", 1.0, "atoradas", "30"),
    ("Rosenbrock", "max_iter", 50, "atoradas", "30"),
    ("Rosenbrock", "p_umbral", 0.2, "atoradas", "29"),
    ("Rosenbrock", "n_ballenas", 10, "atoradas", "28"),
    ("Beale", *BASE, "mediana", "8.8e-9"),
    ("Beale", *BASE, "atoradas", "4"),
    ("Beale", "p_umbral", 0.2, "mediana", "7.4e-13"),
    ("Beale", "n_ballenas", 100, "mediana", "7e-11"),
    ("Beale", "max_iter", 500, "mediana", "3.5e-10"),
    ("Beale", "p_umbral", 0.8, "mediana", "3.6e-7"),
    ("Beale", "a_inicial", 1.0, "mediana", "6.2e-7"),
]

EXPLICACION = {
    "Rastrigin": """
**Cómo es:** muchos hoyitos (mínimos locales) y el mínimo real en el
centro, con 10 variables.

**Con los valores por defecto ya queda resuelta:** 28 de 30 corridas llegan
a 0 exacto y las otras 2 quedan prácticamente en 0.

- **Lo único que necesita son suficientes vueltas.** Con 50, ninguna
  corrida (0 de 30) llega a 0 y la peor se queda en 59.7. Con 100, una
  sola se atora (49.8). De 200 en adelante ya está.
- **La empeora quitarle exploración:** con a = 1 la peor corrida queda en
  25.4 y con p = 0.2 en 33.1. Algunas corridas caen en un hoyito y ya no
  salen.
- **No hace falta probar:** b, ni más ballenas. Todas esas cajas están en 0
  o casi.
- **La trampa:** llega a 0 tan fácil porque el mínimo está en el centro.
  Si se mueve, cuesta mucho más (ver *Probar tú › Sesgo al centro*).
""",
    "Ackley": """
**Cómo es:** un embudo con muchas ondas chiquitas; 2 variables y el mínimo
en el centro.

**Es la más fácil: casi cualquier ajuste la resuelve.** Con los valores
por defecto la mediana es 3.6e-15, que en la práctica es 0 (es el error de
redondeo de la computadora).

- **Solo se nota con muy pocas vueltas:** con 50, la mediana sube a 1.6e-8
  y solo 11 de 30 corridas bajan de 1e-8. Con 100 ya llegan todas.
- **Lo demás no importa:** con cualquier valor de ballenas, a, b o p la
  mediana queda entre 0 y 2.1e-14 (10 ballenas). Esas diferencias son
  redondeo, no mérito del ajuste.
- **No hace falta probar nada más.** Lo único interesante en Ackley es el
  sesgo al centro.
""",
    "Sphere": """
**Cómo es:** un tazón liso, sin trampas; 10 variables y el mínimo en el
centro.

**Siempre llega prácticamente a 0.** Lo que cambian los ajustes es *qué tan
fino* afina: números como 1.8e-34 (la base) contra 1.4e-89. Para fines
prácticos los dos son 0.

- **Más vueltas = mucho más fino:** la mediana va de 4.6e-6 con 50 vueltas
  a 1.4e-89 con 500.
- **Más ballenas también:** de 8.1e-24 con 10 a 7.3e-45 con 100.
- **Explorar es desperdicio aquí:** a = 3 empeora (4.7e-26) y a = 1 mejora
  (2.1e-36). p = 0.2 también empeora (7.7e-29). Como no hay trampas, conviene
  ir directo a afinar.
- **b no cambia nada.**
- **La trampa:** es la que más sufre el sesgo al centro (ver *Probar tú ›
  Sesgo al centro*).
""",
    "Rosenbrock": """
**Cómo es:** un valle largo y curvo ("plátano") con el mínimo en
(1, …, 1). El centro (0, …, 0) vale 9; 10 variables.

**Es la difícil, y donde casi todos los ajustes importan.** Con los valores
por defecto, 17 de 30 corridas se quedan arriba de 7.5 (cerca de 9, en el
centro) y la mediana es 8.56.

- **La arreglan** (de más a menos): a = 3 (mediana 0.09, solo 1 corrida
  atorada), 100 ballenas (0.12, 2 atoradas), p = 0.8 (0.26, 2 atoradas),
  500 vueltas (0.40, 6 atoradas) y b = 2 (0.66, 10 atoradas).
- **La arruinan:** a = 1 (30 de 30 atoradas), 50 vueltas (30 de 30),
  p = 0.2 (29 de 30) y 10 ballenas (28 de 30).
- **Lo que tienen en común las que ayudan:** salir del centro explorando
  más (a = 3), usando menos la espiral (p = 0.8) o gastando más esfuerzo.
- **Para el reporte:** fíjense en la mediana y en cuántas corridas se
  atoran. El promedio mezcla las que llegan con las atoradas y confunde.
""",
    "Beale": """
**Cómo es:** valles angostos y un mínimo local; 2 variables y el mínimo en
(3, 0.5).

**Casi siempre llega, pero unas cuantas corridas se atoran.** Con los
valores por defecto la mediana es 8.8e-9 (casi 0), pero 4 de 30 corridas se
quedan en ~0.76, que es un mínimo local.

- **Ningún ajuste quita las atoradas:** en todas las configuraciones hay
  entre 2 y 7 corridas en ~0.76. Por eso el promedio de Beale sale malo
  aunque la mediana sea casi 0.
- **Lo que sí hacen los ajustes es afinar las que llegan:** p = 0.2
  (mediana 7.4e-13), 100 ballenas (7e-11) y 500 vueltas (3.5e-10).
- **La empeoran un poco:** p = 0.8 (3.6e-7) y a = 1 (6.2e-7).
- **b casi no cambia nada.**
- **Para el reporte:** den la mediana y cuántas corridas se atoraron, no
  solo el promedio.
""",
}

# Resumen de un vistazo (lo mismo que EXPLICACION, en una frase por celda)
RESUMEN = pd.DataFrame([
    ("Rastrigin", "No cambia", "Necesita 200 o más", "a = 1 empeora",
     "No cambia", "p = 0.2 empeora"),
    ("Ackley", "No cambia", "Solo 50 se nota", "No cambia", "No cambia",
     "No cambia"),
    ("Sphere", "Más = más fino", "Más = mucho más fino",
     "a = 3 empeora, a = 1 mejora", "No cambia", "p = 0.2 empeora"),
    ("Rosenbrock", "Más ayuda mucho; 10 la arruina",
     "Más ayuda; 50 la arruina", "a = 3 la arregla; a = 1 la arruina",
     "b = 2 ayuda", "p = 0.8 ayuda; p = 0.2 la arruina"),
    ("Beale", "Más afina", "Más afina", "a = 1 empeora un poco",
     "Casi no cambia", "p = 0.2 afina; p = 0.8 empeora"),
], columns=["Función", "Ballenas", "Vueltas", "a", "b", "p"])

NO_HACE_FALTA = """
- **b casi nunca importa.** Solo se nota en Rosenbrock (b = 2 ayuda).
- **En Rastrigin, Ackley y Sphere, los valores por defecto ya llegan
  prácticamente a 0.** Mover ajustes ahí solo cambia qué tan fino afina, no
  si llega.
- **Lo que de verdad cambia resultados está en Rosenbrock** (casi todo
  importa) **y en Beale** (algunas corridas se atoran y ningún ajuste lo
  arregla).
- **No hay un valor que gane en todas:** a = 3 arregla Rosenbrock pero
  empeora Sphere; p = 0.2 afina Beale pero atora a Rastrigin y arruina
  Rosenbrock.
"""


def tabla_por_valor(fin, funcion):
    """Mediana, peor y corridas en 0 (o atoradas) de cada valor probado."""
    filas = []
    for par, valores in BARRIDOS.items():
        for v in valores:
            fila = {"Ajuste": NOMBRE_BLOQUE[par], "Valor": _g(v),
                    "¿Base?": v == PARAMS_DEFAULT[par],
                    "Mediana": dato(fin, funcion, par, v, "mediana"),
                    "Peor": dato(fin, funcion, par, v, "peor")}
            if funcion in ATORADA:
                fila[f"Atoradas (de {N_CORRIDAS})"] = dato(fin, funcion, par, v,
                                                "atoradas")
            else:
                fila[f"En 0 exacto (de {N_CORRIDAS})"] = dato(fin, funcion, par, v,
                                                   "ceros")
            filas.append(fila)
    return pd.DataFrame(filas)


if __name__ == "__main__":
    print("PDF escrito en", generar_pdf())
