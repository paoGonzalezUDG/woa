# Pendientes del proyecto

Última revisión: 19 de noviembre de 2026, después de correr todas las pruebas
(`pruebas/`).

## Para entregar (lo que les toca a ustedes)

- [ ] **Escribir el reporte con sus propias palabras** y en tono formal. La
      guía con todo el contenido y los números está en
      [reporte_referencia.md](reporte_referencia.md).
- [ ] **Confirmar con el profe el uso de IA.** Si solo la permitió para la
      interfaz, `algoritmo/woa.py` también lo generó la IA: confirmen que está
      bien o reescríbanlo ustedes (son unas 50 líneas).
- [ ] **Verificar en el artículo de WOA** (Mirjalili y Lewis, 2016):
  - [ ] Su tabla de resultados: Sphere ~1e-30, Rosenbrock ~28, Rastrigin 0
        (sección 4.5 del reporte de referencia).
  - [ ] Que use 500 vueltas y 30 ballenas.
  - [ ] Que use los rangos ±100 (Sphere) y ±30 (Rosenbrock).
- [ ] **Verificar las referencias opcionales** antes de citarlas: Kudela
      (2022) y Wolpert y Macready (1997).
- [ ] **Practicar un movimiento a mano** en la pestaña *Paso a paso* (uno de
      cada tipo: rodear, buscar y espiral) para poder explicarlo.
- [ ] (Opcional) Tomar capturas de la *Simulación 3D* o de *Comparar* si
      quieren figuras extra en el reporte.
- [ ] **Tiempo de ejecución** (sugerencia del profe, 21 de noviembre de
      2026): la app ya lo muestra en *Una corrida*, *Simulación 3D* (al
      terminar la animación y abajo de ella), *Comparar*, *Sesgo al centro*
      y *Muchas corridas*; las tablas de `resultados/` ya traían
      `tiempo_medio_s`. Falta comentarlo en el reporte (por ejemplo: más
      ballenas o más vueltas = más tiempo; ¿vale la pena?).

- [ ] **Figura resumen de cajas** (21 de noviembre de 2026):
      `resultados/7_panorama/cajas.png` junta las 25 gráficas de caja en una
      sola (filas = funciones, columnas = parámetros; franja azul = valor
      por defecto). En la app está interactiva en la pestaña *Todas las
      cajas*. Pueden usarla en el reporte en lugar de varias de las
      figuras 2 a 10 y dejar las sueltas solo en el anexo.

- [ ] **Mejor combinación por función** (21 de noviembre de 2026):
      `resultados/8_combinaciones/` y la pestaña *Mejor combinación*. 81
      combinaciones (a × b × p × 3 repartos del mismo esfuerzo), 25 corridas
      cada una. Para el reporte: `cruce.png` muestra que la ganadora de una
      función no sirve para todas (la de Beale queda 73 de 81 en Rastrigin).
      La de por defecto nunca queda entre las 20 mejores. Discútanlo con sus
      palabras. La guía ya tiene la **sección 4.6** (visual: terrenos.png,
      mapa.png y cruce.png, con fichas por función y pistas del por qué).

## Técnico

- [x] Subir los cambios a GitHub (19 de noviembre de 2026).
- [ ] **Diana:** después de `git pull`, correr
      `python -m pip install -r requirements.txt` (se agregó `plotly`).
- [x] Textos de las gráficas de `experimentos.py` cambiados a los de la
      app ("Vuelta", "mejor valor") y `resultados/` regenerado: los números
      salieron idénticos (21 de noviembre de 2026).
- [x] *Muchas corridas* y *Sesgo al centro* calculan cuánto van a tardar
      y, si pasa de un minuto, piden confirmar antes de correr.
- [x] Por qué Rosenbrock se atora en ~8.9: las corridas atoradas terminan
      pegadas al centro (0, …, 0), donde vale 9 (sesgo al centro). Con
      `a = 3` ninguna se atora. Sección 4.4 de la guía y
      `resultados/6_sesgo_centro/rosenbrock.png`.
- [x] App reorganizada en 5 secciones con subsecciones (21 de noviembre de
      2026).
- [x] `python experimentos.py` actualiza también la guía del reporte: las
      tablas del Anexo A se reescriben solas y avisa si algún número del
      texto ya no coincide (`--solo-reporte` para hacer solo eso).

## Ya comprobado (no hace falta revisarlo otra vez)

- [x] Las 5 funciones dan los valores correctos en puntos calculados a mano.
- [x] Cada movimiento de cada ballena sigue su fórmula (recalculado a mano).
- [x] La frecuencia de rodear/buscar/espiral coincide con la teoría.
- [x] Regenerar todos los experimentos da **exactamente** los mismos números
      que `resultados/`.
- [x] Los números escritos en el reporte coinciden con los CSV. Se corrigió
      uno: Rosenbrock con `b = 2` es 0.66, no 0.67.
- [x] El reporte ya no dice que 200 vueltas es el valor del artículo.
- [x] Todas las pestañas de la app abren sin errores con las 5 funciones y
      con ajustes extremos. Se corrigieron dos fallas:
  - [x] Con 1 vuelta, *Paso a paso* tronaba.
  - [x] Con muchas ballenas × vueltas, la app se congelaba varios minutos en
        cada clic; ahora muestra un aviso.
- [x] *Simulación 3D*: ya se puede girar y acercar mientras se reproduce (al
      agarrarla se detiene y al soltarla sigue). También tiene vistas desde
      arriba / inclinada / girar sola, camino de la presa y terreno
      transparente.
- [x] *Simulación 3D*: explicación en vivo en cada cuadro, leyenda más
      clara y controles sin encimarse. Pruebas de humo: 5 funciones × todas
      las opciones de dibujo + 20 ajustes extremos × 3 cámaras = 480 casos,
      0 fallas (textos, conteos, fases, cámara, límites del terreno).
