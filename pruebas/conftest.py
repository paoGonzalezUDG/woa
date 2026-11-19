"""
Configuracion comun de las pruebas.

Correr desde la raiz del proyecto:
    python -m pytest pruebas                  (todo, ~18 min)
    python -m pytest pruebas -m "not lento"   (sin regenerar resultados, ~13 min)
    python -m pytest pruebas/test_algoritmo.py pruebas/test_funciones.py
                                              (solo algoritmo, ~15 s)
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "lento: pruebas que tardan minutos (regenerar resultados)")
