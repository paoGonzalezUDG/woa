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

## Técnico

- [x] Subir los cambios a GitHub (19 de noviembre de 2026).
- [ ] **Diana:** después de `git pull`, correr
      `python -m pip install -r requirements.txt` (se agregó `plotly`).
- [ ] (Opcional) Cambiar los textos de las gráficas de `experimentos.py`
      ("Iteracion", "fitness") a los de la app ("Vuelta", "mejor valor") y
      regenerar `resultados/` (~5 min). Los números no cambian.
- [ ] (Opcional) *Muchas corridas* y la parte estadística de *Sesgo al
      centro* no tienen límite: con muchas ballenas, vueltas o repeticiones
      pueden tardar varios minutos después de presionar **Correr**.
- [ ] (Opcional) Investigar por qué Rosenbrock se atora en ~8.9 (hoy es una
      hipótesis).

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
- [x] *Simulación 3D*: mientras se reproduce no se puede girar con el mouse
      (límite de Plotly). Se agregaron vistas desde arriba / inclinada /
      girar sola, camino de la presa y terreno transparente.
- [x] *Simulación 3D*: explicación en vivo en cada cuadro, leyenda más
      clara y controles sin encimarse. Pruebas de humo: 5 funciones × todas
      las opciones de dibujo + 20 ajustes extremos × 3 cámaras = 480 casos,
      0 fallas (textos, conteos, fases, cámara, límites del terreno).
