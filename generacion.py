"""
generacion.py - Generacion de niveles con una matriz de 15 columnas x 11 filas.

Uso desde mainpruebititas.py:

    import generacion
    ESC = generacion.crear_escenario()
    nivel = generacion.generar_nivel()      # diccionario con paredes, puertas, piedras y agua

Simbolos de la matriz:
    p  pared (rectangulo negro)        .  vacio
    d  puerta marron                   a  agua (lago azul)
    r  roca (en la plantilla es una zona donde puede aparecer una)

Reglas: las paredes del interior vienen en tramos de 2 a 4 casillas (siempre tienen otra pared
al lado), en frente de las puertas y en el centro nunca hay nada, y desde el centro se llega a
todas las puertas sin cruzar paredes, rocas ni agua.
"""

import random
from itertools import groupby
import pygame

COLUMNAS, FILAS = 15, 11
TAM_CASILLA = 120            # lado de cada casilla en pixeles
TAM_ROCA, DESVIO_ROCA = 100, 10
PROB_ROCA, PROB_AGUA = 0.6, 0.8
SEGMENTOS_PARED = (2, 4)     # cuantos tramos de pared aparecen dentro del escenario
LARGO_PARED = (2, 4)         # largo de cada tramo en casillas
PROFUNDIDAD_PUERTA = 2       # casillas libres en frente de cada puerta

COLOR_PARED = (0, 0, 0)
COLOR_AGUA = (30, 110, 230)

PARED, VACIO, PUERTA, ROCAS, AGUA = 'p', '.', 'd', 'r', 'a'

PLANTILLA = [
    "pppppppdppppppp",
    "p.............p",
    "p.rr.......rr.p",
    "p.r..aaaaa..r.p",
    "p.............p",
    "d..r.......r..d",
    "p.............p",
    "p.r..aaaaa..r.p",
    "p.rr.......rr.p",
    "p.............p",
    "pppppppdppppppp",
]
assert len(PLANTILLA) == FILAS and all(len(f) == COLUMNAS for f in PLANTILLA)


def crear_escenario():
    """Reemplaza ESC = pygame.Rect(0, 0, ...)"""
    return pygame.Rect(0, 0, COLUMNAS * TAM_CASILLA, FILAS * TAM_CASILLA)


def crear_area(escenario):
    """Reemplaza AREA = ESC.inflate(-80, -80): zona por donde se puede caminar."""
    return escenario.inflate(-2 * TAM_CASILLA, -2 * TAM_CASILLA)


def _zonas_libres():
    """Casillas donde nunca aparece nada: el centro y el frente de cada puerta."""
    fc, cc = FILAS // 2, COLUMNAS // 2
    zona = {(f, c) for f in range(fc - 1, fc + 2) for c in range(cc - 1, cc + 2)}
    for f, c in ((f, c) for f in range(FILAS) for c in range(COLUMNAS) if PLANTILLA[f][c] == PUERTA):
        df = 1 if f == 0 else -1 if f == FILAS - 1 else 0
        dc = 1 if c == 0 else -1 if c == COLUMNAS - 1 else 0
        zona.update((f + df * k, c + dc * k) for k in range(1, PROFUNDIDAD_PUERTA + 1))
    return zona


def _es_conexo(matriz):
    """Desde el centro se debe llegar a todas las puertas y casillas vacias (sin cruzar p, r ni a)."""
    inicio = (FILAS // 2, COLUMNAS // 2)
    vistas, pendientes = {inicio}, [inicio]
    while pendientes:
        f, c = pendientes.pop()
        for nf, nc in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
            if 0 <= nf < FILAS and 0 <= nc < COLUMNAS and (nf, nc) not in vistas \
                    and matriz[nf][nc] not in (PARED, ROCAS, AGUA):
                vistas.add((nf, nc))
                pendientes.append((nf, nc))
    return all((f, c) in vistas for f in range(FILAS) for c in range(COLUMNAS)
               if matriz[f][c] in (VACIO, PUERTA))


def _resolver_plantilla(azar, libres):
    """Cada 'r' pasa a ser roca o vacio; cada tramo seguido de 'a' es un lago entero o nada."""
    matriz = []
    for f, fila in enumerate(PLANTILLA):
        nueva = []
        for simbolo, grupo in groupby(range(COLUMNAS), key=lambda c: fila[c]):
            columnas = list(grupo)
            if simbolo == AGUA:
                sale = azar.random() < PROB_AGUA and not any((f, c) in libres for c in columnas)
                nueva += [AGUA if sale else VACIO] * len(columnas)
            elif simbolo == ROCAS:
                nueva += [ROCAS if (f, c) not in libres and azar.random() < PROB_ROCA else VACIO for c in columnas]
            else:
                nueva += [simbolo] * len(columnas)
        matriz.append(nueva)
    return matriz


def _agregar_paredes(matriz, azar, libres):
    """
    Tramos de pared de 1 x N casillas (N >= 2) dentro del escenario. Quedan separados del borde
    y de otros tramos por una casilla, asi cada uno es un rectangulo propio.
    """
    cantidad, puestos, intentos = azar.randint(*SEGMENTOS_PARED), 0, 0
    while puestos < cantidad and intentos < 200:
        intentos += 1
        f, c = azar.randint(2, FILAS - 3), azar.randint(2, COLUMNAS - 3)
        dc, df = (1, 0) if azar.random() < 0.5 else (0, 1)
        celdas = [(f + df * i, c + dc * i) for i in range(azar.randint(*LARGO_PARED))]
        if any(not (2 <= cf <= FILAS - 3 and 2 <= cc <= COLUMNAS - 3) or (cf, cc) in libres
               or matriz[cf][cc] != VACIO for cf, cc in celdas):
            continue
        if any(matriz[cf + a][cc + b] == PARED and (cf + a, cc + b) not in celdas
               for cf, cc in celdas for a in (-1, 0, 1) for b in (-1, 0, 1)):
            continue
        for cf, cc in celdas:
            matriz[cf][cc] = PARED
        puestos += 1


def crear_matriz(semilla=None):
    """Matriz ya generada. Con la misma semilla sale siempre la misma."""
    azar = random.Random(semilla)
    libres = _zonas_libres()
    for _ in range(50):
        matriz = _resolver_plantilla(azar, libres)
        _agregar_paredes(matriz, azar, libres)
        if _es_conexo(matriz):
            return matriz
    return [[VACIO if c in (ROCAS, AGUA) else c for c in fila] for fila in PLANTILLA]


def _rectangulos(matriz, simbolo):
    """Junta las casillas de un simbolo en rectangulos."""
    usadas, rects = set(), []
    for f in range(FILAS):
        for c in range(COLUMNAS):
            if matriz[f][c] != simbolo or (f, c) in usadas:
                continue
            c1 = c
            while c1 + 1 < COLUMNAS and matriz[f][c1 + 1] == simbolo and (f, c1 + 1) not in usadas:
                c1 += 1
            f1 = f
            while f1 + 1 < FILAS and all(matriz[f1 + 1][k] == simbolo and (f1 + 1, k) not in usadas
                                         for k in range(c, c1 + 1)):
                f1 += 1
            usadas.update((i, k) for i in range(f, f1 + 1) for k in range(c, c1 + 1))
            rects.append(pygame.Rect(c * TAM_CASILLA, f * TAM_CASILLA,
                                     (c1 - c + 1) * TAM_CASILLA, (f1 - f + 1) * TAM_CASILLA))
    return rects


def generar_nivel(semilla=None):
    """
    Devuelve un diccionario con:
        'matriz'   la matriz generada
        'paredes'  rectangulos negros (casillas 'p' juntadas)
        'puertas'  un Rect por cada 'd'
        'piedras'  una roca (Rect) por cada 'r'
        'agua'     rectangulos azules (casillas 'a' juntadas)
    """
    matriz = crear_matriz(semilla)
    azar = random.Random(semilla)
    piedras = []
    for f, c in ((f, c) for f in range(FILAS) for c in range(COLUMNAS) if matriz[f][c] == ROCAS):
        roca = pygame.Rect(0, 0, TAM_ROCA, TAM_ROCA)
        roca.center = (c * TAM_CASILLA + TAM_CASILLA // 2 + azar.randint(-DESVIO_ROCA, DESVIO_ROCA),
                       f * TAM_CASILLA + TAM_CASILLA // 2 + azar.randint(-DESVIO_ROCA, DESVIO_ROCA))
        piedras.append(roca)
    return {'matriz': matriz, 'paredes': _rectangulos(matriz, PARED), 'piedras': piedras,
            'puertas': _rectangulos(matriz, PUERTA), 'agua': _rectangulos(matriz, AGUA)}


if __name__ == '__main__':
    nivel = generar_nivel()
    print('\n'.join(''.join(fila) for fila in nivel['matriz']))
    print({k: len(v) for k, v in nivel.items() if k != 'matriz'}, crear_escenario().size)