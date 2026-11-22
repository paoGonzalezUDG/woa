# Proyecto final: el algoritmo de la ballena (WOA)

Programamos en Python el **Whale Optimization Algorithm** (Mirjalili y Lewis,
2016) para encontrar el punto más bajo de las **primeras 5 funciones de
prueba** de Wikipedia: Rastrigin, Ackley, Sphere, Rosenbrock y Beale. Luego
hicimos experimentos cambiando sus parámetros para ver qué efecto tiene cada
uno.

**Lo que evalúa el profe es el reporte escrito** (sobre todo la discusión de
los resultados), no el código. Para escribirlo tenemos una guía completa:

> **[docs/reporte_referencia.md](docs/reporte_referencia.md)**: todo el
> contenido del reporte en el orden que pidió el profe, explicado en
> sencillo y con los números de nuestros experimentos.
>
> **[docs/TODO.md](docs/TODO.md)**: lo que falta por hacer antes de entregar
> y lo que ya está comprobado.

---

## Contenido

1. [Empezar](#1-empezar)
2. [Qué hay en el proyecto](#2-qué-hay-en-el-proyecto)
3. [Cómo usar la app](#3-cómo-usar-la-app)
4. [La carpeta resultados](#4-la-carpeta-resultados)
5. [Ver el algoritmo en el código](#5-ver-el-algoritmo-en-el-código)
6. [Regenerar los resultados](#6-regenerar-los-resultados)
7. [Comprobar que todo está bien (pruebas)](#7-comprobar-que-todo-está-bien-pruebas)
8. [Si algo falla](#8-si-algo-falla)

---

## 1. Empezar

Necesitas Python 3.10 o más nuevo.

**La primera vez** (descargar e instalar):

```
git clone https://github.com/paoGonzalezUDG/woa.git
cd woa
pip install -r requirements.txt
```

**Para traer los cambios más recientes:** `git pull` y luego
`pip install -r requirements.txt` (por si se agregó alguna librería; por
ejemplo, la simulación 3D necesita `plotly`).

**Para abrir la app:**

```
streamlit run app.py
```

Se abre sola en el navegador (si no, entra a <http://localhost:8501>). Para
cerrarla, `Ctrl + C` en la terminal.

---

## 2. Qué hay en el proyecto

```
woa/
├── app.py               ▶ Abre la app:  streamlit run app.py
├── experimentos.py      ▶ Regenera los resultados:  python experimentos.py
│
├── algoritmo/           Lo que hay que entender
│   ├── woa.py               El algoritmo de la ballena.
│   └── funciones.py         Las 5 funciones de prueba.
├── interfaz/            Apoyo de la app (no hace falta estudiarlo)
│   ├── visual.py            Gráficas y animaciones.
│   ├── visual3d.py          Simulación 3D interactiva.
│   └── paso_a_paso.py       Versión del algoritmo que anota cada número.
│
├── resultados/          Tablas y gráficas para el reporte (una carpeta por función).
├── docs/
│   ├── reporte_referencia.md   Guía para escribir el reporte.
│   └── TODO.md                 Lo que falta por hacer antes de entregar.
├── pruebas/             Revisan que todo funcione y los números sean correctos.
│
├── README.md            Este archivo.
├── requirements.txt     Librerías que hay que instalar.
└── CLAUDE.md            Notas para el asistente de IA (se puede ignorar).
```

`README.md`, `requirements.txt`, `CLAUDE.md` y `.gitignore` se quedan en la
raíz a propósito: GitHub, `pip` y las herramientas los buscan ahí.

| Archivo | Qué hace | ¿Hay que entenderlo? |
|---|---|---|
| `algoritmo/woa.py` | Pone las ballenas al azar y en cada vuelta mueve a cada una con una de las 3 reglas (rodear, buscar o espiral). Regresa la mejor respuesta. | **Sí, bien** |
| `algoritmo/funciones.py` | Las fórmulas de las 5 funciones, su dominio y dónde está su mínimo. | Sí |
| `experimentos.py` | Repite el algoritmo 30 veces por configuración, saca promedios, genera la carpeta `resultados/` y actualiza la guía del reporte. | La idea general |
| `interfaz/paso_a_paso.py` | Hace exactamente lo mismo que `woa.py` (da los mismos resultados), pero guarda todos los números de cada ballena para mostrarlos en la app. | Ayuda a estudiar |
| `app.py`, `interfaz/visual.py` y `interfaz/visual3d.py` | La interfaz, sus dibujos y la simulación 3D. | No |

---

## 3. Cómo usar la app

Toda la app está escrita en lenguaje sencillo. Si es la primera vez, abre la
sección **Inicio**: explica las palabras básicas (vuelta, semilla,
corrida...) con ejemplos.

En la **barra de la izquierda** eliges la función y ajustas el algoritmo.
Esos valores se usan en *Ver el algoritmo* y *Probar tú*. Cada ajuste tiene un ⓘ que explica qué
hace, y el botón **Volver a los valores por defecto** lo regresa todo a como
estaba.

Colores en todas las gráficas: **azul** = rodear, **naranja** = buscar,
**verde** = espiral, gris = posición inicial, X amarilla = la mejor ballena
(la presa), estrella roja = el mínimo real.

La app tiene **5 secciones** arriba; algunas tienen subsecciones adentro.

| Sección › subsección | Qué ves | Úsala para... |
|---|---|---|
| **Inicio** | Qué es el proyecto, cómo está organizada la app y un glosario con ejemplos. | Empezar. |
| **Ver el algoritmo** › Una corrida | El algoritmo corrido una vez: el resultado, cómo fue mejorando y dónde están las ballenas. | Ver el algoritmo funcionando. |
| **Ver el algoritmo** › Simulación 3D | Las ballenas moviéndose sobre el terreno en 3D, con ▶ Reproducir, cámaras, camino de la mejor ballena y terreno transparente. Se puede girar con el mouse mientras se reproduce. | Entender **cómo es cada función** y cómo la recorren. |
| **Ver el algoritmo** › Paso a paso | Una ballena en una vuelta, con todos los números y las cuentas. | **Entender las fórmulas.** |
| **Ver el algoritmo** › Comparar | Dos valores de un ajuste lado a lado, con animación. | Entender **por qué** un ajuste cambia el resultado. |
| **Probar tú** › Muchas corridas | Un ajuste probado muchas veces: tabla, gráficas y descarga en CSV. Avisa si va a tardar más de un minuto. | Sacar datos confiables. |
| **Probar tú** › Sesgo al centro | La misma función con el mínimo movido de lugar. | El hallazgo más interesante. |
| **Resultados** › Diseño del experimento | Qué se corrió exactamente: la Tabla 1 de 25 ejecuciones por función (con su resultado), los barridos de 30 corridas, semillas y totales, sacado del código. Se descarga en PDF (`docs/diseno_experimental.pdf`; se regenera con `python -m interfaz.diseno`). | La sección 3 del reporte (experimentación). |
| **Resultados** › Todas las cajas | Todos los experimentos en una gráfica interactiva (funciones × ajustes). | Comparar todos los ajustes de un vistazo. |
| **Resultados** › Mejor combinación | 81 combinaciones de ajustes con el mismo esfuerzo: la mejor de cada función y qué ajuste importa más. | Decidir qué ajustes convienen en cada función. |
| **Resultados** › Tablas y descargas | Las gráficas y tablas de `resultados/`, con descarga (también todo en un .zip). | Bajar los archivos para el reporte. |
| **Reporte** | El reporte de referencia completo, con sus gráficas. | Leer la guía sin salir de la app. |

### Paso a paso (la mejor para estudiar)

1. Elige **Ackley** en la barra izquierda (es la más clara).
2. Muévete con los controles:
   - **Vuelta** y **Ballena #**: qué ballena ver y en qué vuelta.
   - **◀ Ballena**, **Ballena ▶**, **Vuelta ▶**: avanzar y retroceder.
   - El menú de movimientos + **Ir al siguiente ejemplo**: saltar directo a
     una ballena que use rodear, buscar o espiral.
3. A la **derecha** sale el cálculo con los números reales, en orden. A la
   **izquierda**, el dibujo: la ballena antes → después, la presa y una línea
   punteada con todos los lugares a los que pudo llegar. **Abajo**, de dónde
   salió cada decisión.

Tip: haz el cálculo **a mano** con los números de la pantalla y compara.

### Comparar

Elige un ajuste y dos valores. Corre el algoritmo dos veces con la misma
suerte (misma semilla), cambiando solo ese parámetro. Puedes ver la animación
o pausar en un momento para explicarlo. La comparación más clara: **Ackley
con `a_inicial` 1 contra 3**.

Ojo: las animaciones son de **una sola corrida**. Los datos para el reporte
deben salir de *Probar tú › Muchas corridas* o de la carpeta `resultados/`
(30 corridas).

---

## 4. La carpeta resultados

Aquí están las tablas (`.csv`, se abren en Excel) y las gráficas (`.png`)
para el reporte. Cada configuración se corrió **30 veces**.

```
resultados/
├── 0_base/          Las 5 funciones juntas con los valores por defecto
├── 1_Rastrigin/     Una carpeta por función, en el orden de Wikipedia.
├── 2_Ackley/        Dentro, un .csv + .png por parámetro probado:
├── 3_Sphere/        n_ballenas, max_iter, a_inicial, b, p_umbral
├── 4_Rosenbrock/
├── 5_Beale/
├── 6_sesgo_centro/  La misma función con el mínimo movido de lugar
├── 7_panorama/      TODAS las cajas en una figura (funciones × parámetros) + cada corrida en CSV
└── 8_combinaciones/ Varios ajustes a la vez: la mejor combinación de cada función
```

También se pueden ver en la app, sección **Resultados**.

Ejemplo: `4_Rosenbrock/a_inicial.png` muestra qué pasa en Rosenbrock al
probar `a` = 1, 2 y 3.

Cómo leer las tablas y las gráficas: [resultados/README.md](resultados/README.md).
Qué significa cada resultado y por qué pasa: [reporte de referencia](docs/reporte_referencia.md).

---

## 5. Ver el algoritmo en el código

- `algoritmo/woa.py` es el algoritmo. Las líneas con `regla[i] = ...`,
  `presas` y `reglas` solo sirven para las gráficas; no cambian el resultado.
- `interfaz/paso_a_paso.py`: la función `woa_detallado` (las primeras ~70
  líneas) es el mismo algoritmo, pero guarda en cada paso `r1, r2, A, C, p, l`,
  la regla usada, la distancia `D` y la posición antes y después. Léela junto
  a `algoritmo/woa.py`.

Para ver los números de una ballena desde la terminal, sin abrir la app
(desde la carpeta del proyecto):

```
python -c "from interfaz.paso_a_paso import woa_detallado; from algoritmo.funciones import ackley; r = woa_detallado(ackley, -5, 5, 2, seed=0); d = r['iteraciones'][0]['ballenas'][0]; print({k: d[k] for k in ['r1','r2','A','C','p','l','regla']})"
```

`regla`: 0 = rodear, 1 = buscar, 2 = espiral.

---

## 6. Regenerar los resultados

```
python experimentos.py                      # todo (~20 min) y actualiza la guía
python experimentos.py --solo-reporte       # solo actualiza la guía (al instante)
python experimentos.py --solo-sesgo         # sesgo al centro y Rosenbrock
python experimentos.py --solo-panorama      # la figura con todas las cajas
python experimentos.py --solo-combinaciones # mejor combinación (~12 min)
python experimentos.py --rapido             # 5 corridas, solo para probar
```

Esto sobrescribe la carpeta `resultados/`. Como todo usa semillas fijas, con
el mismo código salen exactamente los mismos números.

**Al terminar, siempre actualiza la guía del reporte**
(`docs/reporte_referencia.md`):

- Las tablas del **Anexo A** se vuelven a escribir solas desde los CSV.
- Los números escritos dentro del texto **no** se cambian solos (tienen
  negritas y redacción), pero el comando avisa cuáles ya no coinciden, para
  corregirlos a mano. La lista de esos números está en
  `interfaz/reporte.py` (`NUMEROS`).

Con `--rapido` la guía no se toca (con 5 corridas los números no son los
del reporte).

---

## 7. Comprobar que todo está bien (pruebas)

La carpeta `pruebas/` revisa automáticamente que todo funcione y que los
números sean correctos. Conviene correrla antes de entregar o si se cambia
algo del código.

```
python -m pytest pruebas -m "not lento"   # todo menos regenerar (~13 min, la app es lo que más tarda)
python -m pytest pruebas                  # todo, incluye regenerar resultados (~18 min)
```

Si todo sale bien, al final dice `passed` y ningún `failed`.

| Archivo | Qué revisa |
|---|---|
| `test_funciones.py` | Las 5 fórmulas con valores calculados a mano, y que el mínimo de verdad sea el mínimo. |
| `test_algoritmo.py` | Que cada movimiento de cada ballena siga su fórmula (recalculado a mano), que sea reproducible, que las ballenas no se salgan de la zona y que la frecuencia de cada movimiento coincida con la teoría. |
| `test_resultados.py` | Regenera todos los experimentos y los compara con `resultados/`; revisa que los números escritos en el reporte coincidan con los CSV. |
| `test_app.py` | Abre cada pestaña con las 5 funciones, prueba ajustes extremos y entradas inválidas, y que la app muestre los mismos números que el algoritmo. |

---

## 8. Si algo falla

| Problema | Solución |
|---|---|
| `streamlit` no se reconoce como comando | `pip install -r requirements.txt`, o usa `python -m streamlit run app.py` |
| `ModuleNotFoundError` (por ejemplo `No module named 'plotly'`) | Asegúrate de estar dentro de la carpeta del proyecto y corre `python -m pip install -r requirements.txt`. Si tienes varios Python instalados, `python -m pip` instala en el mismo que usa la app. |
| La animación tarda | La primera vez tarda unos 5 segundos; después queda guardada. |
| El puerto 8501 está ocupado | Cierra la otra ventana de streamlit o usa `streamlit run app.py --server.port 8502` |

---

**Referencia principal:** Mirjalili, S., y Lewis, A. (2016). The Whale
Optimization Algorithm. *Advances in Engineering Software, 95*, 51-67.
La bibliografía completa está en el [reporte de referencia](docs/reporte_referencia.md#6-bibliografía).
