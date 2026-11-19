# Proyecto final: Whale Optimization Algorithm (WOA)

Implementacion en Python del algoritmo de optimizacion de la ballena
(Mirjalili y Lewis, 2016) para minimizar las **primeras 5 funciones de prueba**
de la pagina de Wikipedia *Test functions for optimization*: Rastrigin,
Ackley, Sphere, Rosenbrock y Beale.

Objetivo del proyecto (criterios del profesor): implementar el algoritmo,
hacer experimentos que varien sus parametros, observar el efecto sobre el
resultado y entregar un reporte escrito (portada, introduccion, desarrollo,
experimentacion, resultados, conclusiones, bibliografia). **Lo que se evalua
es la discusion de los resultados en el reporte**, no el codigo.

---

## Como usar el proyecto

### 1. Descargarlo e instalar (solo la primera vez)

Requiere Python 3.10 o mayor.

```
git clone https://github.com/paoGonzalezUDG/woa.git
cd woa
pip install -r requirements.txt
```

Si el proyecto ya esta en tu computadora, para traer los cambios mas
recientes: `git pull`.

### 2. Abrir la interfaz

Desde la terminal (por ejemplo la de VS Code), dentro de la carpeta del
proyecto:

```
streamlit run app.py
```

Se abre sola en el navegador; si no, entra a <http://localhost:8501>.
Para cerrarla: `Ctrl + C` en la terminal.

En la **barra de la izquierda** se elige la funcion, los limites del dominio,
los parametros de WOA y la semilla. Todas las pestanas usan esos valores.

### 3. Ver el algoritmo paso a paso (para entender las formulas)

1. Abre la pestana **Paso a paso** (la segunda).
2. En la barra izquierda elige una funcion. **Ackley** es la mas clara para
   empezar.
3. Usa los controles:
   - **Iteracion t** (slider) y **Ballena #**: eligen que ballena ver y en
     que momento.
   - **Ballena >**, **< Ballena**, **Iteracion >**: avanzan o retroceden.
   - **Buscar ejemplo de** + **Siguiente ejemplo**: saltan directo a una
     ballena que use rodear, buscar o espiral.
4. Lo que aparece:
   - **Derecha:** el calculo completo con los numeros reales, en el orden
     del algoritmo: `a` -> `r1, r2` -> `A, C` -> decision por `p` -> decision
     por `|A|` -> `D` -> nueva posicion -> si mejoro.
   - **Izquierda:** el mapa con la ballena antes -> despues (flecha), la
     presa, y una linea punteada con todos los lugares a los que pudo llegar.
   - **Abajo:** de donde sale `A`, la decision por `p` y el factor de la
     espiral.

Sugerencia para estudiar: hacer el calculo **a mano** con los numeros que
aparecen y comparar con la pantalla.

### 4. Ver los efectos de los parametros (para la discusion)

- **Comparar (visual):** elige un parametro y dos valores (A y B). Muestra
  una animacion lado a lado con la misma semilla, la fraccion de ballenas que
  usa cada regla con el tiempo, la dispersion y la convergencia. Se puede
  cambiar a "Pausar en un momento" para explicar un instante. Comparacion
  recomendada: **Ackley con `a_inicial` 1 contra 3**.
- **Experimento:** varia un parametro con muchas corridas (30 por defecto).
  Da la tabla y boxplots, y se puede descargar el CSV. Estos son los datos
  validos para el reporte; las animaciones son de una sola corrida.
- **Sesgo al centro:** la misma funcion con el optimo movido de lugar, con
  animacion y estadistica.

### 5. Ver la version detallada en el codigo

Abre `paso_a_paso.py`. La funcion importante es `woa_detallado` (primeras
~70 lineas): es el mismo algoritmo que `woa.py`, pero en cada paso guarda un
diccionario con `r1, r2, A, C, p, l`, la regla, `D` y las posiciones antes y
despues. Conviene leerla junto a `woa.py`. El resto del archivo
(`explicacion`, `figura_movimiento`, `figura_decisiones`) solo convierte esos
numeros en el texto y las graficas de la pestana.

Para ver los numeros sin la interfaz (ballena 0, iteracion 0):

```
python -c "from paso_a_paso import woa_detallado; from funciones import ackley; r = woa_detallado(ackley, -5, 5, 2, seed=0); d = r['iteraciones'][0]['ballenas'][0]; print({k: d[k] for k in ['r1','r2','A','C','p','l','regla']})"
```

`regla`: 0 = rodear, 1 = buscar, 2 = espiral.

### 6. Regenerar los resultados del reporte

```
python experimentos.py            # todo, 30 corridas (~3 min)
python experimentos.py --rapido   # 5 corridas, solo para probar
```

Sobrescribe los archivos de `resultados/`. Con la misma semilla los numeros
salen iguales.

### Problemas comunes

| Problema | Solucion |
|---|---|
| `streamlit` no se reconoce como comando | `pip install -r requirements.txt` o `python -m streamlit run app.py` |
| `ModuleNotFoundError` | Correr los comandos dentro de la carpeta del proyecto e instalar requirements |
| La animacion tarda | La primera vez tarda ~5 s; despues queda guardada |
| El puerto 8501 esta ocupado | Cerrar la otra ventana de streamlit o usar `streamlit run app.py --server.port 8502` |

---

## Estructura

```
woa_proyecto/
├── woa.py            El algoritmo WOA. Lo mas importante para entender.
├── funciones.py      Las 5 funciones de prueba, sus dominios y optimos.
├── experimentos.py   Corre WOA muchas veces y genera tablas y graficas.
├── app.py            Interfaz web (Streamlit). Solo usa los demas archivos.
├── visual.py         Graficas y animaciones que usa app.py.
├── paso_a_paso.py    Copia "con lupa" de WOA que anota cada numero.
├── resultados/       Tablas (CSV) y graficas (PNG) para el reporte.
└── requirements.txt  Librerias necesarias.
```

| Archivo | Para que sirve | Hay que entenderlo |
|---|---|---|
| `woa.py` | Funcion `woa()`: inicializa las ballenas y en cada iteracion aplica una de las 3 reglas. Devuelve la mejor solucion y la curva de convergencia. | **Si, a fondo** |
| `funciones.py` | Formulas de las 5 funciones y el diccionario `FUNCIONES` (dominio, dimension, optimo conocido). | Si |
| `experimentos.py` | `correr()` repite WOA con semillas 0..29; `resumen()` saca media, desviacion, mediana, mejor y peor; `barrido()` varia UN parametro. Como script genera todo `resultados/`. | La idea general |
| `app.py` | Interfaz con pestanas (ver abajo). | No |
| `visual.py` | Animaciones GIF y graficas de reglas, dispersion y convergencia. | No |
| `paso_a_paso.py` | Hace exactamente lo mismo que `woa.py` (mismos resultados con la misma semilla) pero guarda r1, r2, A, C, p, l, la regla y D de cada ballena. | No |

### Pestanas de la interfaz

| Pestana | Que muestra | Para que usarla |
|---|---|---|
| Una ejecucion | Una corrida: resultado, convergencia y, en 2D, la posicion de las ballenas. | Ver el algoritmo funcionando. |
| Paso a paso | Una ballena en una iteracion, con todos los numeros y el calculo completo. | **Entender las formulas** (seccion Desarrollo). |
| Comparar (visual) | Dos valores de un parametro lado a lado: animacion, uso de reglas, dispersion. | Explicar **por que** un parametro cambia el resultado. |
| Experimento | Varia un parametro con muchas corridas: tabla y boxplots, descarga CSV. | Datos para Resultados. |
| Sesgo al centro | Misma funcion con el optimo movido de lugar. | Discusion critica (ver abajo). |
| Como funciona | Resumen de las formulas. | Consulta rapida. |

Colores en todas las graficas: **azul** = rodear, **naranja** = buscar,
**verde** = espiral, gris = posicion inicial, X amarilla = presa,
estrella roja = optimo real.

### Contenido de `resultados/`

- `base.csv` y `base_convergencia.png`: las 5 funciones con los parametros
  por defecto, 30 corridas cada una.
- `<Funcion>_<parametro>.csv/.png`: barrido de un parametro (25 archivos de
  cada tipo). Cada PNG tiene boxplot del resultado final y la convergencia
  media.

---

## El algoritmo en resumen

Cada ballena es una solucion candidata (un vector). La mejor encontrada hasta
ahora, `mejor_x`, es la **presa** X*. En cada iteracion:

| Concepto | Formula | En `woa.py` |
|---|---|---|
| `a` baja de 2 a 0 | `a = a_inicial (1 - t/T)` | `a = a_inicial * (1 - t / max_iter)` |
| Coeficientes | `A = 2a r1 - a ; C = 2 r2` | `A = ...`, `C = ...` |
| Rodear (p<0.5, abs(A)<1) | `X = X* - A abs(C X* - X)` | primer `if` interno |
| Buscar (p<0.5, abs(A)>=1) | `X = Xrand - A abs(C Xrand - X)` | `else` interno |
| Espiral (p>=0.5) | `X = abs(X* - X) e^(bl) cos(2 pi l) + X*` | `else` externo |

Al inicio `a` es grande, abs(A) >= 1 es frecuente y hay **exploracion**. Al
final `a` tiende a 0, abs(A) < 1 y hay **explotacion**.

## Las 5 funciones

| Funcion | Dimension | Dominio | Minimo | Dificultad |
|---|---|---|---|---|
| Rastrigin | n (10) | +-5.12 | f(0,...,0) = 0 | Muchisimos minimos locales |
| Ackley | 2 | +-5 | f(0,0) = 0 | Casi plana con un hoyo en el centro |
| Sphere | n (10) | +-100 * | f(0,...,0) = 0 | La mas facil, un solo "tazon" |
| Rosenbrock | n (10) | +-30 * | f(1,...,1) = 0 | Valle largo, curvo y casi plano |
| Beale | 2 | +-4.5 | f(3, 0.5) = 0 | Valles estrechos, minimos locales |

\* Dominio elegido por nosotras (en Wikipedia es infinito).

---

## Decisiones propias (deben aparecer en el reporte)

- Sphere y Rosenbrock: dominio +-100 y +-30.
- Rastrigin, Sphere y Rosenbrock: n = 10 por defecto.
- A y C son escalares por ballena e iteracion; l ~ U[-1, 1]; las posiciones
  fuera del dominio se recortan al limite (`np.clip`).
- Parametros por defecto: 30 ballenas, 200 iteraciones, a_inicial = 2,
  b = 1, p_umbral = 0.5.
- Semilla de la corrida k = k: todo es reproducible.

## Experimentos

`experimentos.py` varia un parametro a la vez, con 30 corridas por valor:

| Parametro | Valores |
|---|---|
| n_ballenas | 10, 30, 50, 100 |
| max_iter | 50, 100, 200, 500 |
| a_inicial | 1, 2, 3 |
| b | 0.5, 1, 2 |
| p_umbral | 0.2, 0.5, 0.8 |

### Observaciones de la corrida incluida (verificar con la suya)

- Rastrigin, Ackley y Sphere llegan a error ~1e-15 o menor con los parametros
  por defecto.
- `max_iter` es el parametro con efecto mas claro en todas las funciones.
- `a_inicial = 3` mejora mucho Rosenbrock (mediana 8.56 -> 0.09) pero empeora
  Sphere: es el equilibrio exploracion/explotacion.
- Con `a_inicial = 1` nunca hay exploracion (abs(A) <= 1 siempre).
- `b` casi no tiene efecto, salvo en Rosenbrock.
- Beale: el peor caso es 0.762 en TODAS las configuraciones (minimo local);
  por eso la media (0.10) y la mediana (~1e-8) son tan distintas.
- Rosenbrock es la mas dificil: muchas corridas se quedan en ~8.9.
  Hipotesis NO verificada sobre la causa.
- **Sesgo al centro:** las 3 funciones "faciles" tienen el optimo en el
  origen. Al mover el optimo (pestana *Sesgo al centro*) el resultado empeora
  mucho (Sphere 10D: 1e-34 -> 1.77). Causa probable: el termino C*X* jala
  hacia el 0.

---

## Bibliografia

- Mirjalili, S. y Lewis, A. (2016). The Whale Optimization Algorithm.
  *Advances in Engineering Software*, 95, 51-67.
  doi:10.1016/j.advengsoft.2016.01.008
- Wikipedia, "Test functions for optimization".
- https://seyedalimirjalili.com/woa
