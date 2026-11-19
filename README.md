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

---

## La carpeta `resultados/`

Tiene todo lo necesario para las secciones de **Resultados** y **Discusion**
del reporte. La genera `python experimentos.py` (52 archivos): tablas
(`.csv`, se abren en Excel) y graficas (`.png`).

### Que hay

| Archivo | Que es |
|---|---|
| `base.csv` + `base_convergencia.png` | Las 5 funciones con los **parametros por defecto** (30 ballenas, 200 iteraciones, a=2, b=1, p=0.5), 30 corridas cada una. Es el punto de referencia. |
| `<Funcion>_<parametro>.csv` + `.png` | 25 pares (5 funciones x 5 parametros). Cada uno varia **un solo parametro** y deja los demas por defecto. Ejemplo: `Rosenbrock_a_inicial` prueba a = 1, 2 y 3 en Rosenbrock. |

### Como leer los CSV

Cada fila resume **30 corridas** (semillas 0 a 29) con la misma
configuracion:

| Columna | Significado |
|---|---|
| `media` | Promedio del mejor resultado. Se ve muy afectada por corridas malas. |
| `desv_est` | Que tan distintas fueron las corridas entre si. |
| `mediana` | El valor del medio: la corrida "tipica". |
| `mejor` / `peor` | La mejor y la peor de las 30 corridas. |
| `tiempo_medio_s` | Segundos por corrida. |

Todos los valores son **error respecto al optimo**: el minimo real de las 5
funciones es 0, asi que mas cerca de 0 es mejor. Por ejemplo, `1.8e-15`
significa 0.0000000000000018, practicamente 0.

**Media contra mediana:** en Beale la media es 0.10 pero la mediana es
~1e-8. Eso indica que casi todas las corridas aciertan y unas pocas se quedan
atoradas en ~0.76, lo que jala el promedio hacia arriba. Por eso se reportan
las dos.

### Como leer las graficas

**`base_convergencia.png`: una linea por funcion.**

- Eje X: iteracion. Eje Y: el mejor valor encontrado hasta ese momento,
  promediado sobre las 30 corridas, en escala **logaritmica** (cada marca es
  100 000 veces menor).
- **Sphere** baja sin parar hasta 1e-31: es la mas facil.
- **Rosenbrock** y **Beale** se quedan planas desde temprano: estancadas.
- **Rastrigin** se ve plana hasta ~90 y luego cae de golpe. Como es un
  *promedio*, la linea solo baja cuando las ultimas corridas logran escapar
  de los minimos locales.
- Ojo al comparar: Rastrigin, Sphere y Rosenbrock estan en 10 dimensiones;
  Ackley y Beale en 2.

**Graficas de parametros (ejemplo: `Rosenbrock_a_inicial.png`).** Tienen dos
paneles:

- **Izquierda, boxplot del resultado final:** una caja por valor del
  parametro. La linea naranja es la mediana; la caja contiene el 50 % central
  de las corridas (caja alta = resultados muy variables); los bigotes marcan
  el rango normal y los circulos son corridas atipicas. Mas abajo es mejor.
  En el ejemplo: con a=1 todas quedan en ~9, con a=2 hay mucha variacion y
  con a=3 la mediana baja a ~0.09.
- **Derecha, convergencia media:** una linea por valor. En el ejemplo, a=1
  baja **mas rapido** al principio pero se estanca en ~9: explota demasiado
  pronto y nunca explora (**convergencia prematura**). a=3 es mas lenta al
  inicio porque explora mas tiempo, pero **termina mas abajo**. Es el
  equilibrio exploracion/explotacion visto en datos reales.

### Como usarla en el reporte

- **Resultados:** `base.csv` como tabla principal y
  `base_convergencia.png`. Agregar las tablas y graficas de los barridos que
  muestren algo interesante; no hace falta incluir las 25.
- **Discusion:** por cada grafica explicar **por que** pasa usando el
  mecanismo (`a`, |A|, las 3 reglas), no solo "subio o bajo". Los barridos
  con mas que decir: a_inicial y max_iter en Rosenbrock y Rastrigin,
  p_umbral en Rosenbrock, y el caso de Beale.
- **Experimentacion:** mencionar que son 30 corridas por configuracion, con
  semilla = numero de corrida, asi que todo es reproducible.

Si se cambian parametros o codigo y se vuelve a correr
`python experimentos.py`, estos archivos se sobrescriben. Con el codigo
actual salen identicos.

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
