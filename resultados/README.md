# Resultados de los experimentos

Cada configuración se corrió **30 veces**. Todo se genera con
`python experimentos.py`.

```
resultados/
├── 0_base/            Las 5 funciones juntas, con los valores por defecto
│   ├── resumen.csv        tabla: una fila por función
│   └── convergencia.png   gráfica: una línea por función
├── 1_Rastrigin/       Una carpeta por función, en el orden de Wikipedia
├── 2_Ackley/
├── 3_Sphere/
├── 4_Rosenbrock/
├── 5_Beale/
├── 6_sesgo_centro/    Misma función con el mínimo movido de lugar
│   ├── resumen.csv        Rastrigin, Ackley y Sphere: original vs. movida
│   └── comparacion.png    cajas: original vs. movida
└── 7_panorama/
    ├── finales.csv        el resultado de CADA corrida de los barridos
    │                      (la pestaña "Todas las cajas" de la app lo usa)
│   └── cajas.png          las 25 gráficas de caja en una sola figura:
│                          filas = funciones, columnas = parámetros
└── 8_combinaciones/   Varios ajustes a la vez (25 corridas cada combinación)
    ├── resumen.csv        81 combinaciones por función, con su lugar
    │                      (1 = la mejor; empates comparten lugar)
    ├── finales.csv        el resultado de cada corrida
    ├── mejores.png        las 5 mejores de cada función + la de por defecto
    ├── cruce.png          la ganadora de cada función, ¿qué lugar saca
    │                      en las demás?
    ├── mapa.png           qué valor de cada ajuste conviene en cada función
    │                      (lugar promedio)
    └── terrenos.png       las 5 funciones en 3D (con 2 variables)

Las 81 combinaciones: a (1, 2, 3) × b (0.5, 1, 2) × p (0.2, 0.5, 0.8) × 3
maneras de repartir el MISMO esfuerzo (ballenas × vueltas = 6000):
10×600, 30×200 y 60×100. Así la comparación es justa (más ballenas o más
vueltas siempre ayudan porque es más trabajo).
```

También se pueden ver y descargar en la app (`streamlit run app.py`),
pestaña **Resultados**.

**Dentro de cada carpeta de función** hay un par de archivos (`.csv` tabla
+ `.png` gráfica) por cada parámetro que se cambió. En cada par solo cambia
ese parámetro; los demás se quedan con su valor por defecto.

| Archivo | Parámetro que cambia | Valores probados | Valor por defecto |
|---|---|---|---|
| `n_ballenas` | Número de ballenas | 10, 30, 50, 100 | 30 |
| `max_iter` | Número de vueltas (iteraciones) | 50, 100, 200, 500 | 200 |
| `a_inicial` | Cuánto exploran al principio | 1, 2, 3 | 2 |
| `b` | Qué tan abierta es la espiral | 0.5, 1, 2 | 1 |
| `p_umbral` | Qué tan seguido usan rodear/buscar vs. espiral | 0.2, 0.5, 0.8 | 0.5 |

Ejemplo: `4_Rosenbrock/a_inicial.png` muestra qué pasa en Rosenbrock al
probar `a` = 1, 2 y 3.

## Cómo leerlos

**Tablas (`.csv`, se abren en Excel):** una fila por valor probado. Los
números son **qué tan lejos quedó del mínimo real (0)**: más cerca de 0,
mejor. `1.8e-15` = 0.0000000000000018, o sea, prácticamente 0.

| Columna | Qué significa |
|---|---|
| `media` | El promedio de las 30 corridas. Unas pocas corridas malas lo jalan mucho. |
| `mediana` | La corrida "típica", la del medio. |
| `desv_est` | Qué tan distintas salieron las corridas entre sí. |
| `mejor` / `peor` | La mejor y la peor de las 30. |
| `tiempo_medio_s` | Segundos por corrida. |

**Gráficas (`.png`):**

- **Izquierda (cajas):** una caja por valor probado. La línea naranja es la
  mediana; la caja guarda la mitad central de las corridas (caja alta =
  resultados muy variados); los circulitos son corridas raras. Más abajo es
  mejor.
- **Derecha (líneas):** cómo fue bajando el resultado vuelta por vuelta,
  promediado. Escala logarítmica: cada marca es 100 000 veces menor.

Qué significa cada resultado y por qué pasa está en
[docs/reporte_referencia.md](../docs/reporte_referencia.md).
