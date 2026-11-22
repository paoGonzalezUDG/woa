# Pendientes del proyecto

Última revisión: 21 de noviembre de 2026, después de las pruebas de humo
(292 pruebas automáticas, `experimentos.py` completo y la app en el
navegador con las 5 funciones: 0 errores).

## Para entregar (lo que les toca a ustedes)

### 1. Escribir el reporte (lo que se evalúa)

- [ ] **Escribirlo con sus propias palabras** y en tono formal, siguiendo
      [reporte_referencia.md](reporte_referencia.md) (también en la app,
      sección *Reporte*).
- [ ] **Sección 3 (experimentación): corregir la Tabla 1 de Diana.** La que
      tienen (25 corridas por función, seed 0, N = 5/15/80/120, T = 300/1000,
      b = 0.2/2.5, d = 30…) **no es lo que se corrió**. Lo real está en la
      app (*Resultados › Diseño del experimento*) y en
      `docs/diseno_experimental.pdf`: 30 corridas por configuración
      (semillas 0–29), 13 configuraciones por función y 13,125 corridas en
      total. El texto también dice que 200 vueltas es "de la literatura" y
      que siempre cambia un solo ajuste: las dos cosas son falsas.
- [ ] **Discusión de cada parámetro** (sección 4.2 de la guía, figuras 2 a
      10). Para no poner tantas gráficas, pueden usar una sola:
      `resultados/7_panorama/cajas.png` (las 25 cajas juntas).
- [ ] **Tiempo de ejecución** (lo pidió el profe): Figura 11,
      `resultados/0_base/tiempo_calidad.png`. Idea central: solo en
      Rosenbrock vale la pena gastar más tiempo.
- [ ] **Sesgo al centro y Rosenbrock** (secciones 4.3 y 4.4, figuras 12 y
      13): el hallazgo principal. Rosenbrock se atora en ~8.9 porque las
      ballenas se quedan en el centro, donde vale 9.
- [ ] **Qué parámetros convienen en cada función** (sección 4.6, figuras
      14 a 16: terrenos, mapa y cruce). Ninguna combinación gana en todas.
- [ ] **Conclusiones** (sección 5, 7 ideas) y limitaciones.

### 2. Verificar antes de entregar

- [ ] **En el artículo de WOA** (Mirjalili y Lewis, 2016):
  - [ ] Su tabla de resultados: Sphere ~1e-30, Rosenbrock ~28, Rastrigin 0
        (sección 4.5 de la guía).
  - [ ] Que use 500 vueltas y 30 ballenas.
  - [ ] Que use los rangos ±100 (Sphere) y ±30 (Rosenbrock).
- [ ] **Referencias opcionales** antes de citarlas: Kudela (2022) y Wolpert
      y Macready (1997). La sección 4.6 cita a Wolpert y Macready.
- [ ] **Confirmar con el profe el uso de IA.** Si solo la permitió para la
      interfaz, `algoritmo/woa.py` también lo generó la IA: confirmen que
      está bien o reescríbanlo ustedes (unas 50 líneas).

### 3. Prepararse para explicarlo

- [ ] **Practicar un movimiento a mano** en *Ver el algoritmo › Paso a
      paso* (uno de cada tipo: rodear, buscar y espiral).
- [ ] (Opcional) Capturas de *Simulación 3D* o *Comparar* si quieren
      figuras extra. Cada pestaña muestra una línea **⚙️ Ajustes** con los
      parámetros usados (en negritas los que no son los de por defecto):
      inclúyanla en la captura o escríbanla en el pie de figura.

## Técnico

- [ ] **Diana:** después de `git pull`, correr
      `python -m pip install -r requirements.txt`.
- [ ] (Opcional) Si cambian algo del algoritmo o de los experimentos:
      `python experimentos.py` (~20 min) regenera todo y avisa qué números
      del texto de la guía hay que corregir a mano. Después, también
      `python -m interfaz.diseno` para rehacer el PDF del diseño.

## Ya comprobado (no hace falta revisarlo otra vez)

- [x] **Diseño del experimento (22 de noviembre de 2026):** las tablas de la
      app y del PDF salen de `experimentos.py` y una prueba las compara con
      `finales.csv`, `8_combinaciones/` y `6_sesgo_centro/`.

- [x] **Pruebas de humo (21 de noviembre de 2026):**
  - [x] 292 pruebas automáticas rápidas: todas pasan.
  - [x] App en el navegador: las 14 pestañas cargan con las 5 funciones sin
        errores; los 3 botones **Correr** (Una corrida, Muchas corridas,
        Sesgo al centro) funcionan.
  - [x] `python experimentos.py --rapido` corre completo (62 archivos) y no
        toca la guía.
  - [x] Regenerar todo `resultados/` da los mismos 30 CSV (solo cambia el
        tiempo). La guía se actualiza sola y sus números coinciden.
- [x] Textos de las gráficas de `experimentos.py` como los de la app.
- [x] *Muchas corridas* y *Sesgo al centro* avisan si van a tardar más de
      un minuto.
- [x] Por qué Rosenbrock se atora en ~8.9 (sesgo al centro), comprobado.
- [x] App reorganizada en 5 secciones con subsecciones.
- [x] `python experimentos.py` actualiza también la guía del reporte.
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
