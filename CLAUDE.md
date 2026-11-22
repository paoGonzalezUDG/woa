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
`from algoritmo.funciones import FUNCIONES`, `from interfaz import cajas, combinaciones, reporte, visual, visual3d, paso_a_paso`.
Correr todo desde la raiz del proyecto.
- `algoritmo/woa.py`: `woa(f, lb, ub, dim, n_ballenas, max_iter, a_inicial, b, p_umbral, seed, guardar_posiciones)` -> dict(mejor_x, mejor_f, curva, posiciones, presas, reglas). reglas: 0 rodear, 1 buscar, 2 espiral.
- `algoritmo/funciones.py`: `FUNCIONES[nombre] = dict(f, dim (None = n libre), dim_default, lb, ub, optimo_x(n), optimo_f, formula)`.
- `experimentos.py`: `PARAMS_DEFAULT`, `correr()`, `resumen()`, `barrido()`; `main()` genera `resultados/` (`generar_todo`) y al final `avisar_reporte()`.
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
- `interfaz/diseno.py`: tablas del diseno experimental (seccion 3) armadas
  desde las constantes de experimentos.py; `filas_barridos()`, `totales()`,
  `notas()`. `python -m interfaz.diseno` escribe `docs/diseno_experimental.pdf`
  (HTML impreso con Edge/Chrome headless; no hay reportlab). Si cambian los
  experimentos, regenerar el PDF. Pestana Resultados > Diseño del experimento.
  Seccion 5 "Que pasa en cada funcion": `EXPLICACION`, `RESUMEN`,
  `NO_HACE_FALTA` (texto a mano) y `DATOS` (sus numeros; una prueba los
  compara con finales.csv: si cambian los resultados, corregir el texto).
- `interfaz/combinaciones.py`: lee `8_combinaciones/resumen.csv`; tabla top,
  `figura_lugar_promedio` (que valor de cada ajuste queda mas arriba) y
  `figura_cruce` (lugar de la ganadora de cada funcion en las demas).
- `app.py`: Streamlit, 5 secciones (st.tabs, `SECCIONES`) con subpestanas
  adentro: Inicio (glosario) | Ver el algoritmo: Una corrida, Simulacion 3D,
  Paso a paso, Comparar | Probar tu: Muchas corridas, Sesgo al centro |
  Resultados: Diseño del experimento, Todas las cajas, Mejor combinacion,
  Tablas y descargas |
  Reporte. CSS al inicio: secciones grandes, subsecciones como botones
  (selectores `[data-testid=stTab]`, streamlit 1.65). Solo UI.
  `texto_ajustes()` pone una linea "⚙️ Ajustes: ..." (lo distinto al valor
  por defecto en negritas) en Una corrida, 3D, Paso a paso, Comparar, Muchas
  corridas y Sesgo, para que cada captura diga con que parametros salio.
  Precarga: `cargando = st.empty()` arriba de las pestanas con un aviso
  animado (CSS `.woa-cargando`); la ultima linea del archivo lo borra. Usar
  `parar()` en vez de `st.stop()` despues de ese punto (si no, el aviso se
  queda pegado).
  `confirmar_espera()` pide confirmar si Muchas corridas / Sesgo al centro
  tardarian mas de 1 min (`SEG_POR_MOVIMIENTO`).
  Ajustes del sidebar con key `sb_*` inicializados en session_state (sin
  value=) para que el boton de reinicio no genere avisos.
- `resultados/`: CSV y PNG generados (30 corridas). Usarlos en vez de recorrer.
  `0_base/{resumen.csv,convergencia.png,tiempo_calidad.png}` (esta ultima
  sale de los CSV de max_iter y n_ballenas: x = ballenas x vueltas, arriba
  segundos aprox.; se redibuja en cada `experimentos.py` salvo --rapido) y `<n>_<Funcion>/<parametro>.{csv,png}`
  (n = orden de Wikipedia: 1 Rastrigin ... 5 Beale) y `6_sesgo_centro/`
  (`experimentos.py --solo-sesgo`, `SESGO` = {Rastrigin 2, Ackley 1.5, Sphere 30};
  tambien `rosenbrock.{csv,png}`: a donde llega cada corrida, centro (vale 9)
  o minimo (1,...,1), con `CASOS_ROSENBROCK`; numeros en ROSEN de las pruebas)
  y `7_panorama/{finales.csv,cajas.png}` (`--solo-panorama`, ~3.5 min):
  finales.csv = una fila por corrida (funcion, parametro, valor, corrida,
  mejor_f); cajas.png = las 25 cajas en una figura 5x5, log por fila, ceros
  en un piso marcado "0 exacto".
  `8_combinaciones/` (`--solo-combinaciones`, ~12 min): 81 combinaciones =
  `REPARTOS` (10x600, 30x200, 60x100: mismo esfuerzo 6000) x a x b x p, 25
  corridas (semillas 0-24). resumen.csv con `lugar` (mediana, luego media,
  luego peor; empates exactos comparten lugar), cruce.png, mapa.png (lugar
  promedio por valor) y terrenos.png. Seccion 4.6 del reporte usa estas
  figuras; sus numeros
  estan en COMBOS y test_lugares_promedio_del_reporte (test_resultados).
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
  `interfaz/reporte.py` tiene NUMEROS y LUGARES (numeros escritos a mano en
  el reporte; los usan las pruebas y `experimentos.py`): si se edita el
  reporte, actualizarlos. Las tablas del Anexo A van entre
  `<!-- auto:ID -->` y `<!-- /auto -->` y se regeneran solas
  (`actualizar_reporte()`); `experimentos.py` lo llama al terminar
  (`--solo-reporte` = solo eso). La pestana Reporte oculta esas marcas.
  Plotly 6 serializa arreglos como {dtype, bdata}: usar `_arr()` de test_app.
- Pestanas que corren solas usan `es_pesado()` (limite 200,000 movimientos).
- Tiempo de ejecucion: `corrida()` (cacheada) agrega `res["tiempo"]`; formato
  con `visual.texto_tiempo()`; `figura_3d(tiempo=)` lo pone en el titulo del
  ultimo cuadro. Se mide fuera de woa.py (no tocarlo).
- Entorno: Windows, Python 3.10, streamlit 1.65 (`st.image(width="stretch")`).
- Repo propio en esta carpeta (remote woa.git). La carpeta padre
  `c:\laragon\www` es OTRO repo (mexware): no hacer commits ahi.
