# CLAUDE.md

Proyecto escolar: WOA (Whale Optimization Algorithm) en Python sobre las 5
primeras funciones de Wikipedia "Test functions for optimization". Equipo:
Paola y Diana. Se evalua el REPORTE escrito (discusion de resultados), no el
codigo. Ellas deben escribir el reporte; ayudar a entender, no redactarlo.

Todo en espanol (codigo, comentarios, interfaz). Sin acentos en el codigo.

## Archivos (no hace falta leerlos todos)
- `woa.py`: `woa(f, lb, ub, dim, n_ballenas, max_iter, a_inicial, b, p_umbral, seed, guardar_posiciones)` -> dict(mejor_x, mejor_f, curva, posiciones, presas, reglas). reglas: 0 rodear, 1 buscar, 2 espiral.
- `funciones.py`: `FUNCIONES[nombre] = dict(f, dim (None = n libre), dim_default, lb, ub, optimo_x(n), optimo_f, formula)`.
- `experimentos.py`: `PARAMS_DEFAULT`, `correr()`, `resumen()`, `barrido()`; `main()` genera `resultados/`.
- `paso_a_paso.py`: `woa_detallado()` replica woa.py anotando cada paso.
- `visual.py`: graficas/GIF con matplotlib + Pillow (no hay plotly).
- `app.py`: Streamlit, 6 pestanas. Solo UI.
- `resultados/`: CSV y PNG generados (30 corridas). Usarlos en vez de recorrer.

## Reglas
- NO cambiar la logica de `woa.py` ni el orden de llamadas a `rng`: los
  resultados de `resultados/` y `paso_a_paso.py` dependen de eso. Si se toca,
  verificar que `woa()` y `woa_detallado()` sigan dando lo mismo.
- Colores fijos: azul rodear, naranja buscar, verde espiral (`visual.COLORES_REGLAS`).
- Probar la app sin navegador: `streamlit.testing.v1.AppTest.from_file("app.py")`.
- Entorno: Windows, Python 3.10, streamlit 1.65 (`st.image(width="stretch")`).
- Repo propio en esta carpeta (remote woa.git). La carpeta padre
  `c:\laragon\www` es OTRO repo (mexware): no hacer commits ahi.
