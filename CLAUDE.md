# CLAUDE.md

Proyecto escolar: WOA (Whale Optimization Algorithm) en Python sobre las 5
primeras funciones de Wikipedia "Test functions for optimization". Equipo:
Paola y Diana. Se evalua el REPORTE escrito (discusion de resultados), no el
codigo. Ellas deben escribir el reporte; ayudar a entender, no redactarlo.

Todo en espanol. Comentarios y nombres sin acentos; los textos que ve el
usuario (app, graficas, docs) CON acentos, tono casual, sin tecnicismos
("vuelta" no "iteracion", "mejor valor" no "fitness", "afinar" para
explotar). Textos largos en st.expander; ayudas en help= de los widgets.

## Archivos (no hace falta leerlos todos)
Raiz: solo los 2 scripts que se corren (`app.py`, `experimentos.py`) y los
archivos que deben estar en la raiz (README, CLAUDE.md, requirements.txt,
.gitignore). Imports: `from algoritmo.woa import woa`,
`from algoritmo.funciones import FUNCIONES`, `from interfaz import cajas, combinaciones, visual, visual3d, paso_a_paso`.
Correr todo desde la raiz del proyecto.
- `algoritmo/woa.py`: `woa(f, lb, ub, dim, n_ballenas, max_iter, a_inicial, b, p_umbral, seed, guardar_posiciones)` -> dict(mejor_x, mejor_f, curva, posiciones, presas, reglas). reglas: 0 rodear, 1 buscar, 2 espiral.
- `algoritmo/funciones.py`: `FUNCIONES[nombre] = dict(f, dim (None = n libre), dim_default, lb, ub, optimo_x(n), optimo_f, formula)`.
- `experimentos.py`: `PARAMS_DEFAULT`, `correr()`, `resumen()`, `barrido()`; `main()` genera `resultados/`.
- `interfaz/paso_a_paso.py`: `woa_detallado()` replica woa.py anotando cada paso.
- `interfaz/visual.py`: graficas/GIF con matplotlib + Pillow.
- `interfaz/visual3d.py`: `figura_3d(f, lb, ub, res, optimo, log, ms, camara,
  rastro, opacidad)` -> figura Plotly (superficie + ballenas, 80 cuadros; los
  frames solo actualizan trazas 1, 2 y 3 si hay rastro). Altura log10(1+f).
  Plotly ignora el mouse mientras anima (cualquier cambio de datos 3D lo
  bloquea). `html_3d(fig)` arma una pagina con plotly.js adentro (dibuja hasta
  que el iframe se ve: oculto mide textos en 0 y encima botones) y JS
  propio: al agarrar/rueda pausa, al soltar sigue, y copia la camara a
  gd.layout para que los cuadros no la regresen. app.py la muestra con
  `st.iframe` (no st.plotly_chart). camara "girar" = cada frame trae su
  scene.camera. Arriba = ortografica; su zoom es aspectratio.
  Cada frame trae tambien una annotation con la explicacion (fase segun a,
  conteos, si mejoro la presa). Franjas en y: escena 0.21-1, explicacion,
  botones 0.058, barra 0. Humo exhaustivo: 480 casos, 0 fallas.
- Python del proyecto: `python` = 3.10 de Laragon; usar `python -m pip`
  (el `pip` suelto apunta a otro Python 3.13).
- `interfaz/cajas.py`: `figura_cajas(df, funciones, por_defecto, ver_puntos)`
  -> Plotly 5x5 de cajas desde `7_panorama/finales.csv` (no recorre nada).
- `interfaz/combinaciones.py`: lee `8_combinaciones/resumen.csv`; tabla top,
  `figura_lugar_promedio` (que valor de cada ajuste queda mas arriba) y
  `figura_cruce` (lugar de la ganadora de cada funcion en las demas).
- `app.py`: Streamlit, 11 pestanas: Empieza aqui (glosario), Una corrida,
  Simulacion 3D, Paso a paso, Comparar, Muchas corridas, Sesgo al centro,
  Todas las cajas, Mejor combinacion, Resultados, Reporte. Solo UI.
  Ajustes del sidebar con key `sb_*` inicializados en session_state (sin
  value=) para que el boton de reinicio no genere avisos.
- `resultados/`: CSV y PNG generados (30 corridas). Usarlos en vez de recorrer.
  `0_base/{resumen.csv,convergencia.png}` y `<n>_<Funcion>/<parametro>.{csv,png}`
  (n = orden de Wikipedia: 1 Rastrigin ... 5 Beale) y `6_sesgo_centro/`
  (`experimentos.py --solo-sesgo`, `SESGO` = {Rastrigin 2, Ackley 1.5, Sphere 30})
  y `7_panorama/{finales.csv,cajas.png}` (`--solo-panorama`, ~3.5 min):
  finales.csv = una fila por corrida (funcion, parametro, valor, corrida,
  mejor_f); cajas.png = las 25 cajas en una figura 5x5, log por fila, ceros
  en un piso marcado "0 exacto".
  `8_combinaciones/` (`--solo-combinaciones`, ~12 min): 81 combinaciones =
  `REPARTOS` (10x600, 30x200, 60x100: mismo esfuerzo 6000) x a x b x p, 25
  corridas (semillas 0-24). resumen.csv con `lugar` (mediana, luego media,
  luego peor; empates exactos comparten lugar), finales.csv (cada corrida),
  mejores.png y cruce.png. `rehacer_figuras_combinaciones()` redibuja sin
  correr.
- El reporte incrusta PNG con `![..](../resultados/...)`; sus Anexos A/B se
  generaron desde los CSV. La pestana Reporte de app.py lo muestra
  (`mostrar_markdown` separa las lineas de imagen para `st.image`).
- `docs/TODO.md`: pendientes y lo ya comprobado; actualizarlo al terminar algo.
- `docs/reporte_referencia.md`: guia del reporte (tono casual, con los numeros
  de resultados/ y del experimento de sesgo al centro). Si cambian los
  resultados, actualizar sus tablas. README = como usar el proyecto.

## Reglas
- NO cambiar la logica de `algoritmo/woa.py` ni el orden de llamadas a `rng`:
  los resultados de `resultados/` y `paso_a_paso.py` dependen de eso. Si se toca,
  verificar que `woa()` y `woa_detallado()` sigan dando lo mismo.
- Colores fijos: azul rodear, naranja buscar, verde espiral (`visual.COLORES_REGLAS`).
- Pruebas: `python -m pytest pruebas -m "not lento"` (rapidas) o sin `-m`
  (incluye regenerar todo `resultados/` y compararlo, ~5 min extra).
  `test_resultados.py` tiene la lista AFIRMACIONES con los numeros escritos a
  mano en el reporte: si se edita el reporte, actualizarla.
  Plotly 6 serializa arreglos como {dtype, bdata}: usar `_arr()` de test_app.
- Pestanas que corren solas usan `es_pesado()` (limite 200,000 movimientos).
- Tiempo de ejecucion: `corrida()` (cacheada) agrega `res["tiempo"]`; formato
  con `visual.texto_tiempo()`; `figura_3d(tiempo=)` lo pone en el titulo del
  ultimo cuadro. Se mide fuera de woa.py (no tocarlo).
- Entorno: Windows, Python 3.10, streamlit 1.65 (`st.image(width="stretch")`).
- Repo propio en esta carpeta (remote woa.git). La carpeta padre
  `c:\laragon\www` es OTRO repo (mexware): no hacer commits ahi.
