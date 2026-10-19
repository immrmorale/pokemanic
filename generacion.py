"""
generacion.py - Generacion procedural de salas (estilo Hades): combate, tienda y arena de jefe.

    import generacion
    sala = generacion.generar_sala(era, 'bosque encantado', 'sur', ['norte', 'este'])
    sala = generacion.generar_tienda(era, ['oeste', 'este'])
    sala = generacion.generar_arena(era)

Como se arma una sala (por capas, y despues se valida):
    1. silueta      rectangulo, esquinas cortadas, cruz, columnas o cueva (automata celular)
    2. simetria     a veces la sala se espeja (izq/der, arriba/abajo o las dos) para que se vea diseñada
    3. especiales   rio que serpentea con puentes, laguna, foso, costa, cintas, cables
    4. terreno      manchas organicas (crecen y se suavizan) de hierba, hielo, lodo, sombra...
    5. maquinas     cascadas, fogatas, generadores... que ayudan a ciertos tipos
    6. piezas       grupitos armados a mano de cada era (fogata con troncos, cementerio, herreria...)
    7. cobertura    objetos para cubrirse repartidos parejo alrededor del centro (muestreo de Poisson)
    8. sueltos      el resto de los objetos, tambien separados entre si
    9. validacion   caminos anchos entre puertas y centro, sin peligros en el camino, sin huecos encerrados por objetos
Se generan varias candidatas y se queda la de mejor puntaje.

Cada sala es un diccionario con:
    'matriz'      terreno de cada casilla (nombres de mundos.TERRENOS)
    'objetos'     objetos sueltos (mundos.OBJETOS) con su rect, vida y material
    'puertas'     salidas: {'rect', 'lado'}       'entrada' lado por donde entras
    'inicio'      punto donde aparece el jugador  'esc' tamaño total de la sala
    'alcanzables' casillas a las que se llega caminando desde la entrada
"""

import math
import random
import pygame
import mundos

TAM_CASILLA = 80
COLUMNAS, FILAS = 21, 15                    # 1680 x 1200 pixeles
TIENDA_CASILLA, TIENDA_COLUMNAS, TIENDA_FILAS = 40, 25, 15   # 1000 x 600: entra justo en la pantalla
PROFUNDIDAD_PUERTA = 2                      # casillas libres en frente de cada puerta
CANDIDATAS = 5                              # salas validas que se comparan
INTENTOS = 30
LARGO_PARED = (2, 4)
LADOS = ('norte', 'sur', 'este', 'oeste')
OPUESTO = {'norte': 'sur', 'sur': 'norte', 'este': 'oeste', 'oeste': 'este'}
PASO_LADO = {'norte': (1, 0), 'sur': (-1, 0), 'oeste': (0, 1), 'este': (0, -1)}   # hacia adentro de la sala (fila, columna)
PELIGROSOS = ('lava', 'toxico', 'fuego', 'cable', 'aceite')                       # nunca en el camino principal
PISABLES = ('suelo', 'hierba', 'arena', 'nieve', 'sombra', 'lodo', 'ceniza', 'roca_volcanica', 'alfombra', 'hielo')   # donde se apoyan objetos
ABIERTO_IDEAL = 0.68                        # proporcion de piso libre que se busca

COLOR_PARED = (0, 0, 0)
COLOR_AGUA = mundos.TERRENOS['agua']['color']


def crear_escenario(columnas=COLUMNAS, filas=FILAS, tam=TAM_CASILLA):
    return pygame.Rect(0, 0, columnas * tam, filas * tam)


def crear_area(escenario, tam=TAM_CASILLA):
    """Zona por donde se puede caminar (sin el borde de paredes)."""
    return escenario.inflate(-2 * tam, -2 * tam)


def _elegir(azar, pesos, defecto):
    """Elige una clave de un diccionario {opcion: peso}."""
    if not pesos: return defecto
    return azar.choices(list(pesos), list(pesos.values()))[0]


# ---------- puertas y zonas libres ----------

def _casillas_puerta(lado, columnas, filas):
    """Las 3 casillas del borde que ocupa la puerta de un lado."""
    fc, cc = filas // 2, columnas // 2
    if lado == 'norte': return [(0, cc + k) for k in (-1, 0, 1)]
    if lado == 'sur': return [(filas - 1, cc + k) for k in (-1, 0, 1)]
    if lado == 'oeste': return [(fc + k, 0) for k in (-1, 0, 1)]
    return [(fc + k, columnas - 1) for k in (-1, 0, 1)]


def _frente(lado, columnas, filas, profundidad=PROFUNDIDAD_PUERTA):
    """Casillas de adentro justo en frente de una puerta."""
    df, dc = PASO_LADO[lado]
    return {(f + df * k, c + dc * k) for f, c in _casillas_puerta(lado, columnas, filas) for k in range(1, profundidad + 1)}


def _adentro_de_puerta(lado, columnas, filas):
    """Primera casilla de adentro en frente del medio de una puerta."""
    f, c = _casillas_puerta(lado, columnas, filas)[1]
    return f + PASO_LADO[lado][0], c + PASO_LADO[lado][1]


def _zonas_libres(columnas, filas, lados, radio_centro=1):
    """El centro y el frente de las puertas."""
    fc, cc = filas // 2, columnas // 2
    zona = {(f, c) for f in range(fc - radio_centro, fc + radio_centro + 1) for c in range(cc - radio_centro, cc + radio_centro + 1)}
    for lado in lados: zona |= _frente(lado, columnas, filas)
    return zona


def _matriz_base(columnas, filas, entrada, salidas):
    """Borde de paredes, piso adentro, la entrada cerrada y las salidas."""
    m = [['pared' if f in (0, filas - 1) or c in (0, columnas - 1) else 'suelo' for c in range(columnas)] for f in range(filas)]
    if entrada:
        for f, c in _casillas_puerta(entrada, columnas, filas): m[f][c] = 'entrada'
    for lado in salidas:
        for f, c in _casillas_puerta(lado, columnas, filas): m[f][c] = 'puerta'
    return m


def _adentro(m, f, c):
    return 1 <= f < len(m) - 1 and 1 <= c < len(m[0]) - 1


def _espejos(f, c, sim, filas, columnas):
    """La casilla y sus copias espejadas segun la simetria."""
    lista = {(f, c)}
    if 'h' in sim: lista.add((f, columnas - 1 - c))
    if 'v' in sim: lista.add((filas - 1 - f, c))
    if sim == 'hv': lista.add((filas - 1 - f, columnas - 1 - c))
    return lista


# ---------- 1. silueta ----------

def _silueta(m, azar, forma, libres, sim='no'):
    """Le da forma a la sala tapando con pared lo que queda afuera."""
    filas, columnas = len(m), len(m[0])
    fc, cc = filas // 2, columnas // 2
    tapar = set()
    if forma == 'esquinas':                                     # esquinas cortadas en diagonal
        k = azar.randint(2, 4)
        for f in range(1, filas - 1):
            for c in range(1, columnas - 1):
                a, b = min(f - 1, filas - 2 - f), min(c - 1, columnas - 2 - c)
                if a + b < k: tapar.add((f, c))
    elif forma == 'cruz':                                       # bloques en las 4 esquinas: queda una cruz
        alto, ancho = azar.randint(2, fc - 3), azar.randint(3, cc - 3)     # los brazos quedan de 5 casillas o mas
        for f in range(1, filas - 1):
            for c in range(1, columnas - 1):
                if (f <= alto or f >= filas - 1 - alto) and (c <= ancho or c >= columnas - 1 - ancho): tapar.add((f, c))
    elif forma == 'columnas':                                   # dos hileras de pilares parejos, lejos del centro
        paso = azar.choice((4, 5))
        largo = azar.random() < 0.4
        for f in (3, filas - 4):
            for c in range(3 + (columnas - 7) % paso // 2, columnas - 3, paso):
                tapar.add((f, c))
                if largo: tapar.add((f - 1 if f < fc else f + 1, c))
    elif forma == 'cueva':                                      # automata celular: bordes rocosos e irregulares
        abiertas = set(libres) | _pasillos(m, azar, libres)
        roca = {(f, c) for f in range(1, filas - 1) for c in range(1, columnas - 1)
                if (f, c) not in abiertas and azar.random() < (0.55 if min(f, c, filas - 1 - f, columnas - 1 - c) <= 3 else 0.15)}
        for _ in range(4):
            nueva = set()
            for f in range(1, filas - 1):
                for c in range(1, columnas - 1):
                    vecinas = sum((f + a, c + b) in roca or not _adentro(m, f + a, c + b) for a in (-1, 0, 1) for b in (-1, 0, 1))
                    if (f, c) not in abiertas and vecinas >= 5: nueva.add((f, c))
            roca = nueva
        tapar = roca
    tapar = {p for f, c in tapar for p in _espejos(f, c, sim, filas, columnas)}   # la silueta tambien se espeja
    for f, c in tapar:
        if (f, c) not in libres and m[f][c] == 'suelo': m[f][c] = 'pared'


def _pasillos(m, azar, libres):
    """Caminos serpenteantes de 3 de ancho desde cada puerta al centro (para que la cueva nunca quede cerrada)."""
    filas, columnas = len(m), len(m[0])
    fc, cc = filas // 2, columnas // 2
    abiertas = set()
    for lado in LADOS:
        f, c = _adentro_de_puerta(lado, columnas, filas)
        for _ in range(40):
            abiertas |= {(f + a, c + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if _adentro(m, f + a, c + b)}
            if abs(f - fc) <= 1 and abs(c - cc) <= 1: break
            if abs(f - fc) > abs(c - cc) or (abs(f - fc) == abs(c - cc) and azar.random() < 0.5): f += 1 if fc > f else -1
            else: c += 1 if cc > c else -1
            if azar.random() < 0.3:                             # se tuerce un poco para que no sea recto
                f = max(2, min(filas - 3, f + azar.choice((-1, 1)))) if lado in ('este', 'oeste') else f
                c = max(2, min(columnas - 3, c + azar.choice((-1, 1)))) if lado in ('norte', 'sur') else c
    return abiertas


# ---------- 3. especiales ----------

def _rio(m, azar, libres, sim):
    """Rio de 2 casillas que serpentea de pared a pared, con puentes y una cascada donde nace."""
    filas, columnas = len(m), len(m[0])
    vertical = azar.random() < 0.5
    largo, ancho_total = (filas, columnas) if vertical else (columnas, filas)
    centro = ancho_total // 2
    permitidas = [x for x in range(3, ancho_total - 4) if abs(x - centro) > 2 and abs(x + 1 - centro) > 2]
    pos = azar.choice(permitidas)
    celdas = []
    for paso in range(1, largo - 1):
        if azar.random() < 0.3:                                 # el rio se corre un poco (meandro)
            nuevo = pos + azar.choice((-1, 1))
            if nuevo in permitidas: pos = nuevo
        celdas.append([(paso, pos + k) if vertical else (pos + k, paso) for k in (0, 1)])
    puentes = set(azar.sample(range(2, len(celdas) - 2), 2))
    for i, fila in enumerate(celdas):
        for f, c in fila:
            if m[f][c] == 'suelo': m[f][c] = 'puente' if i in puentes or (f, c) in libres else 'agua'
    f, c = celdas[0][0]
    borde = [(0, c), (0, c + 1)] if vertical else [(f, 0), (f + 1, 0)]
    if all(m[a][b] == 'pared' for a, b in borde):
        for a, b in borde: m[a][b] = 'cascada'


def _laguna(m, azar, libres, sim):
    """Laguna redondeada lejos del centro."""
    filas, columnas = len(m), len(m[0])
    for _ in range(30):
        f, c, r = azar.randint(3, filas - 4), azar.randint(3, columnas - 4), azar.uniform(1.6, 2.8)
        if math.hypot(f - filas // 2, c - columnas // 2) < 4.5: continue
        celdas = [(a, b) for a in range(f - 3, f + 4) for b in range(c - 4, c + 5)
                  if _adentro(m, a, b) and ((a - f) / r) ** 2 + ((b - c) / (r * 1.3)) ** 2 <= 1]
        if any((a, b) in libres for a, b in celdas): continue
        for a, b in celdas:
            for x, y in _espejos(a, b, sim, filas, columnas):
                if m[x][y] == 'suelo' and (x, y) not in libres: m[x][y] = 'agua'
        return


def _foso(m, azar, libres, sim):
    """Anillo de agua alrededor del centro con un puente hacia cada lado."""
    filas, columnas = len(m), len(m[0])
    fc, cc = filas // 2, columnas // 2
    f0, f1, c0, c1 = fc - 3, fc + 3, cc - 5, cc + 5
    for f in range(f0, f1 + 1):
        for c in range(c0, c1 + 1):
            if (f in (f0, f1) or c in (c0, c1)) and m[f][c] == 'suelo':
                m[f][c] = 'puente' if abs(c - cc) <= 1 or abs(f - fc) <= 1 else 'agua'


def _costa(m, azar, libres, sim):
    """Franja de agua de 2 casillas pegada a una pared (mar, muelle), con hueco en las puertas."""
    filas, columnas = len(m), len(m[0])
    lado = azar.choice(LADOS)
    for f in range(1, filas - 1):
        for c in range(1, columnas - 1):
            borde = {'norte': f <= 2, 'sur': f >= filas - 3, 'oeste': c <= 2, 'este': c >= columnas - 3}[lado]
            if borde and m[f][c] == 'suelo' and (f, c) not in libres: m[f][c] = 'agua'


def _lineas(m, azar, libres, sim, terreno_de, cantidad, largo):
    """Tramos rectos (cintas transportadoras, cables)."""
    filas, columnas = len(m), len(m[0])
    for _ in range(azar.randint(*cantidad)):
        f, c = azar.randint(2, filas - 3), azar.randint(2, columnas - 3)
        df, dc, terreno = terreno_de(azar)
        for _ in range(azar.randint(*largo)):
            if not _adentro(m, f, c) or m[f][c] != 'suelo' or (f, c) in libres: break
            m[f][c] = terreno; f += df; c += dc


def _cintas(m, azar, libres, sim):
    def una(azar):
        lado = azar.choice(('n', 's', 'e', 'o'))
        df, dc = {'n': (-1, 0), 's': (1, 0), 'e': (0, 1), 'o': (0, -1)}[lado]
        return df, dc, 'cinta_' + lado
    _lineas(m, azar, libres, sim, una, (2, 4), (4, 7))


def _cables(m, azar, libres, sim):
    _lineas(m, azar, libres, sim, lambda azar: azar.choice(((0, 1, 'cable'), (1, 0, 'cable'))), (2, 4), (4, 8))


ESPECIALES = {'rio': _rio, 'laguna': _laguna, 'foso': _foso, 'costa': _costa, 'cintas': _cintas, 'cables': _cables}


def _agregar_paredes(m, azar, libres, sim, segmentos):
    """Tramos de pared de 1 x N casillas, separados del borde y entre si por una casilla."""
    filas, columnas = len(m), len(m[0])
    cantidad, puestos, intentos = azar.randint(*segmentos), 0, 0
    while puestos < cantidad and intentos < 200:
        intentos += 1
        f, c = azar.randint(2, filas - 3), azar.randint(2, columnas - 3)
        dc, df = (1, 0) if azar.random() < 0.5 else (0, 1)
        celdas = set()
        for i in range(azar.randint(*LARGO_PARED)): celdas |= _espejos(f + df * i, c + dc * i, sim, filas, columnas)
        if any(not (2 <= cf <= filas - 3 and 2 <= cc <= columnas - 3) or (cf, cc) in libres or m[cf][cc] != 'suelo' for cf, cc in celdas):
            continue
        if any(m[cf + a][cc + b] == 'pared' and (cf + a, cc + b) not in celdas for cf, cc in celdas for a in (-1, 0, 1) for b in (-1, 0, 1)):
            continue
        for cf, cc in celdas: m[cf][cc] = 'pared'
        puestos += 1


# ---------- 4. terreno ----------

def _mancha(m, azar, terreno, tam, libres, sim):
    """Mancha organica: crece al azar desde una casilla y despues se suaviza (se rellenan huecos y se sacan puntas)."""
    filas, columnas = len(m), len(m[0])
    cuidar = mundos.TERRENOS[terreno]['bloquea'] or terreno in PELIGROSOS
    ok = lambda f, c: _adentro(m, f, c) and m[f][c] == 'suelo' and not (cuidar and (f, c) in libres)
    for _ in range(30):
        inicio = (azar.randint(1, filas - 2), azar.randint(1, columnas - 2))
        if ok(*inicio): break
    else: return
    mancha = {inicio}
    for _ in range(tam * 6):
        if len(mancha) >= tam: break
        f, c = azar.choice(tuple(mancha))
        df, dc = azar.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        if ok(f + df, c + dc): mancha.add((f + df, c + dc))
    for _ in range(2):                                          # suavizado (como un automata celular)
        cerca = lambda f, c: sum((f + a, c + b) in mancha for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b)
        bordes = {(f + a, c + b) for f, c in mancha for a in (-1, 0, 1) for b in (-1, 0, 1)}
        mancha = {p for p in bordes if ok(*p) and (cerca(*p) >= 5 or (p in mancha and cerca(*p) >= 2))}
    for f, c in mancha:
        for x, y in _espejos(f, c, sim, filas, columnas):
            if ok(x, y): m[x][y] = terreno


def _poner_maquina(m, azar, maquina, libres, sim):
    """Cascadas y hornos van pegados a una pared (la cascada con su laguito abajo); el resto sueltas en el piso."""
    filas, columnas = len(m), len(m[0])
    if maquina == 'cascada' or mundos.TERRENOS[maquina].get('pegado_a_pared'):
        for _ in range(40):
            lado = azar.choice(LADOS)
            if lado in ('norte', 'sur'): f, c = (0 if lado == 'norte' else filas - 1), azar.randint(2, columnas - 4)
            else: f, c = azar.randint(2, filas - 4), (0 if lado == 'oeste' else columnas - 1)
            df, dc = PASO_LADO[lado]
            largo = [(f, c), (f, c + 1)] if lado in ('norte', 'sur') else [(f, c), (f + 1, c)]
            frente = [(a + df, b + dc) for a, b in largo]
            if any(m[a][b] != 'pared' for a, b in largo) or any(m[a][b] != 'suelo' or (a, b) in libres for a, b in frente):
                continue
            if maquina == 'cascada':                           # la cascada cae en la pared y deja un lago adelante
                for a, b in largo: m[a][b] = 'cascada'
                for a, b in [(a + df * k, b + dc * k) for a, b in largo for k in (1, 2)]:
                    if _adentro(m, a, b) and m[a][b] == 'suelo' and (a, b) not in libres: m[a][b] = 'agua'
            else:
                for a, b in frente: m[a][b] = maquina
            return
        return
    for _ in range(40):
        f, c = azar.randint(2, filas - 3), azar.randint(2, columnas - 3)
        lugares = _espejos(f, c, sim, filas, columnas)
        if all(m[a][b] == 'suelo' and (a, b) not in libres and not any(mundos.TERRENOS[m[a + x][b + y]].get('maquina') for x in (-1, 0, 1) for y in (-1, 0, 1))
               for a, b in lugares):
            for a, b in lugares: m[a][b] = maquina
            return


# ---------- objetos ----------

def crear_objeto(nombre, centro, celdas=()):
    """Un objeto listo para usar en el juego (vida, rect, material...)."""
    d = mundos.OBJETOS[nombre]
    r = pygame.Rect(0, 0, *d['tam']); r.center = centro
    return {'objeto': True, 'nombre': nombre, 'rect': r, 'vida': d['vida'], 'max_vida': d['vida'], 'material': d['material'],
            'solido': d.get('solido', True), 'empujable': d.get('empujable', False), 'celdas': set(celdas), 'tipo': None,
            'vel': [0.0, 0.0], 'resto': [0.0, 0.0], 'golpe': -1000}


def _celdas_de(nombre, centro, tam):
    """Casillas que tapa un objeto puesto en ese centro."""
    w, h = mundos.OBJETOS[nombre]['tam']
    x0, y0 = centro[0] - w / 2 + 1, centro[1] - h / 2 + 1
    return {(f, c) for f in range(int(y0 // tam), int((y0 + h - 2) // tam) + 1) for c in range(int(x0 // tam), int((x0 + w - 2) // tam) + 1)}


def _espejo_punto(x, y, sim, ancho, alto):
    lista = {(x, y)}
    if 'h' in sim: lista.add((ancho - x, y))
    if 'v' in sim: lista.add((x, alto - y))
    if sim == 'hv': lista.add((ancho - x, alto - y))
    return lista


def _intentar_objeto(est, nombre, x, y, espejar=True):
    """Pone el objeto (y sus copias espejadas) si entra: piso firme, fuera de zonas libres y sin pisar otro objeto."""
    m, tam = est['m'], est['tam']
    puntos = _espejo_punto(x, y, est['sim'] if espejar else 'no', len(m[0]) * tam, len(m) * tam)
    planes = []
    for px, py in puntos:
        celdas = _celdas_de(nombre, (px, py), tam)
        if any(not _adentro(m, f, c) or m[f][c] not in PISABLES or (f, c) in est['libres'] or (f, c) in est['ocupadas'] for f, c in celdas):
            return False
        if any(celdas & otras for _, _, otras in planes): return False
        planes.append((px, py, celdas))
    for px, py, celdas in planes:
        solido = mundos.OBJETOS[nombre].get('solido', True)
        est['objetos'].append(crear_objeto(nombre, (round(px), round(py)), celdas if solido else ()))
        est['ocupadas'] |= celdas
    return True


# ---------- 6. piezas ----------

def _girar(mapa, azar):
    """Rota y espeja una pieza al azar."""
    for _ in range(azar.randint(0, 3)): mapa = [''.join(fila[i] for fila in reversed(mapa)) for i in range(len(mapa[0]))]
    if azar.random() < 0.5: mapa = [fila[::-1] for fila in mapa]
    return mapa


def _poner_pieza(est, azar, nombre):
    """Busca un lugar donde entre la pieza entera y la pone (con sus copias si la sala es simetrica)."""
    m, tam = est['m'], est['tam']
    pieza = mundos.PIEZAS[nombre]
    leyenda = dict(mundos.LEYENDA_BASE); leyenda.update(pieza['leyenda'])
    mapa = _girar(pieza['mapa'], azar)
    alto, ancho = len(mapa), len(mapa[0])
    filas, columnas = len(m), len(m[0])
    for _ in range(40):
        f0, c0 = azar.randint(1, filas - 1 - alto), azar.randint(1, columnas - 1 - ancho)
        terrenos, objetos, libres_pieza = [], [], set()
        bien = True
        for i, fila in enumerate(mapa):
            for k, letra in enumerate(fila):
                f, c = f0 + i, c0 + k
                if letra == '.': continue
                if m[f][c] not in PISABLES or (f, c) in est['ocupadas']: bien = False; break
                if letra == '_': libres_pieza.add((f, c)); continue
                valor = leyenda[letra]
                if valor in mundos.OBJETOS: objetos.append((valor, (c + 0.5) * tam, (f + 0.5) * tam))
                else:
                    if (f, c) in est['libres'] and (mundos.TERRENOS[valor]['bloquea'] or valor in PELIGROSOS): bien = False; break
                    terrenos.append((f, c, valor))
            if not bien: break
        if not bien: continue
        copia_objetos, copia_ocupadas = list(est['objetos']), set(est['ocupadas'])
        if all(_intentar_objeto(est, o, x, y) for o, x, y in objetos):
            for f, c, valor in terrenos:
                for a, b in _espejos(f, c, est['sim'], filas, columnas):
                    if m[a][b] in PISABLES and (a, b) not in est['ocupadas']: m[a][b] = valor
            for f, c in libres_pieza: est['ocupadas'] |= _espejos(f, c, est['sim'], filas, columnas)   # '_' queda libre
            est['piezas'].append(nombre)
            return True
        est['objetos'], est['ocupadas'] = copia_objetos, copia_ocupadas   # no entro: se deshace
    return False


# ---------- 7 y 8. cobertura y sueltos (Poisson) ----------

def _poisson(est, azar, nombres, cantidad, separacion, radio_min, radio_max):
    """Reparte objetos sin que queden pegados entre si (muestreo de Poisson por rechazo), en un anillo alrededor del centro."""
    m, tam = est['m'], est['tam']
    cx, cy = len(m[0]) * tam / 2, len(m) * tam / 2
    puestos = 0
    for _ in range(cantidad * 25):
        if puestos >= cantidad or not nombres: break
        ang, dist = azar.uniform(0, math.tau), azar.uniform(radio_min, radio_max) * tam
        x, y = cx + math.cos(ang) * dist * 1.35, cy + math.sin(ang) * dist     # el anillo es mas ancho que alto como la sala
        if any(math.hypot(o['rect'].centerx - x, o['rect'].centery - y) < separacion * tam for o in est['objetos']): continue
        if _intentar_objeto(est, azar.choice(nombres), x, y): puestos += 1


# ---------- 9. validacion ----------

def bloqueadas(m, objetos):
    """Casillas por las que no se puede caminar (terreno que bloquea u objeto solido)."""
    malas = {(f, c) for f, fila in enumerate(m) for c, t in enumerate(fila) if mundos.TERRENOS[t]['bloquea']}
    for o in objetos:
        if o['solido']: malas |= o['celdas']
    return malas


def _alcanzables(m, objetos, inicio, malas=None):
    """Casillas a las que se llega caminando desde inicio."""
    malas = bloqueadas(m, objetos) if malas is None else malas
    vistas, pendientes = {inicio}, [inicio]
    while pendientes:
        f, c = pendientes.pop()
        for nf, nc in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
            if _adentro(m, nf, nc) and (nf, nc) not in vistas and (nf, nc) not in malas:
                vistas.add((nf, nc)); pendientes.append((nf, nc))
    return vistas


def _camino(m, malas, desde, hasta):
    """Camino mas corto entre dos casillas (BFS), o None."""
    previo, pendientes = {desde: None}, [desde]
    for actual in pendientes:
        if actual == hasta:
            camino = []
            while actual: camino.append(actual); actual = previo[actual]
            return camino
        f, c = actual
        for nxt in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
            if _adentro(m, *nxt) and nxt not in previo and nxt not in malas: previo[nxt] = actual; pendientes.append(nxt)
    return None


def _ancho_ok(m, malas, desde, metas):
    """Se llega a cada meta con un camino de 2 casillas de ancho (nada de pasadizos de una casilla en el camino principal).
    desde y cada meta son zonas (conjuntos de casillas); un bloque de 2x2 tiene que poder ir de una a las otras."""
    libre = lambda f, c: all(_adentro(m, f + a, c + b) and (f + a, c + b) not in malas for a in (0, 1) for b in (0, 1))
    dentro = lambda f, c, zona: all((f + a, c + b) in zona for a in (0, 1) for b in (0, 1))
    pendientes = [p for p in desde if dentro(*p, desde) and libre(*p)]
    vistas = set(pendientes)
    while pendientes:
        f, c = pendientes.pop()
        for nxt in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
            if nxt not in vistas and libre(*nxt): vistas.add(nxt); pendientes.append(nxt)
    return bool(vistas) and all(any(dentro(*p, meta) for p in vistas) for meta in metas)


def _validar(est, entrada, salidas):
    """Arregla y chequea la sala. Devuelve el puntaje (o None si no sirve)."""
    m, objetos = est['m'], est['objetos']
    filas, columnas = len(m), len(m[0])
    inicio = _adentro_de_puerta(entrada or 'sur', columnas, filas)
    centro = (filas // 2, columnas // 2)
    metas = [centro] + [_adentro_de_puerta(l, columnas, filas) for l in salidas]
    for _ in range(6):                                          # huecos encerrados por objetos: se saca el objeto que tapa
        malas = bloqueadas(m, objetos)
        llega = _alcanzables(m, objetos, inicio, malas)
        encerradas = {(f, c) for f in range(1, filas - 1) for c in range(1, columnas - 1) if (f, c) not in malas and (f, c) not in llega}
        culpables = [o for o in objetos if o['solido'] and any((f + a, c + b) in encerradas for f, c in o['celdas'] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if not culpables: break
        for o in culpables: objetos.remove(o)
    malas = bloqueadas(m, objetos)
    llega = _alcanzables(m, objetos, inicio, malas)
    if est['forma'] == 'cueva':                                 # en la cueva lo que quedo suelto se vuelve roca
        for f in range(1, filas - 1):
            for c in range(1, columnas - 1):
                if (f, c) not in malas and (f, c) not in llega: m[f][c] = 'pared'
    caminos = [_camino(m, malas, inicio, meta) for meta in metas]
    if any(c is None for c in caminos): return None
    for camino in caminos:                                      # nada de lava, toxico o cables en el camino principal
        for f, c in camino:
            for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if _adentro(m, f + a, c + b) and m[f + a][c + b] in PELIGROSOS: m[f + a][c + b] = 'suelo'
    zona_centro = {(centro[0] + a, centro[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
    desde, zonas = _frente(entrada or 'sur', columnas, filas), [zona_centro] + [_frente(l, columnas, filas) for l in salidas]
    if not _ancho_ok(m, malas, desde, zonas):                  # si lo angostan objetos, se despeja el camino principal
        cerca = {(f + a, c + b) for camino in caminos for f, c in camino for a in (-1, 0, 1) for b in (-1, 0, 1)}
        objetos[:] = [o for o in objetos if not (o['solido'] and o['celdas'] & cerca)]
        malas = bloqueadas(m, objetos)
        if not _ancho_ok(m, malas, desde, zonas): return None
    interior = (filas - 2) * (columnas - 2)
    abiertas = sum(1 for f in range(1, filas - 1) for c in range(1, columnas - 1) if (f, c) not in malas) / interior
    tam = est['tam']
    cx, cy = columnas * tam / 2, filas * tam / 2
    cobertura = sum(1 for o in objetos if o['solido'] and 2.5 * tam < math.hypot(o['rect'].centerx - cx, o['rect'].centery - cy) < 7.5 * tam)
    variedad = len({t for fila in m for t in fila})
    desempate = est['azar'].random() * 0.3
    return -abs(abiertas - ABIERTO_IDEAL) * 12 + min(cobertura, 8) * 0.5 + min(variedad, 8) * 0.4 + len(est['piezas']) * 0.7 + desempate


# ---------- armado ----------

def _rect_puerta(lado, columnas, filas, tam):
    celdas = _casillas_puerta(lado, columnas, filas)
    f0, c0 = min(f for f, _ in celdas), min(c for _, c in celdas)
    f1, c1 = max(f for f, _ in celdas), max(c for _, c in celdas)
    return pygame.Rect(c0 * tam, f0 * tam, (c1 - c0 + 1) * tam, (f1 - f0 + 1) * tam)


def rectangulos(m, condicion, tam):
    """Junta en rectangulos las casillas que cumplen condicion(terreno)."""
    filas, columnas = len(m), len(m[0])
    usadas, rects = set(), []
    for f in range(filas):
        for c in range(columnas):
            if not condicion(m[f][c]) or (f, c) in usadas: continue
            c1 = c
            while c1 + 1 < columnas and condicion(m[f][c1 + 1]) and (f, c1 + 1) not in usadas: c1 += 1
            f1 = f
            while f1 + 1 < filas and all(condicion(m[f1 + 1][k]) and (f1 + 1, k) not in usadas for k in range(c, c1 + 1)): f1 += 1
            usadas.update((i, k) for i in range(f, f1 + 1) for k in range(c, c1 + 1))
            rects.append(pygame.Rect(c * tam, f * tam, (c1 - c + 1) * tam, (f1 - f + 1) * tam))
    return rects


def _armar(m, objetos, tam, entrada, salidas, extra=None):
    """Diccionario final de la sala."""
    filas, columnas = len(m), len(m[0])
    lado_inicio = entrada or 'sur'
    df, dc = PASO_LADO[lado_inicio]
    inicio_casilla = _adentro_de_puerta(lado_inicio, columnas, filas)
    sala = {'matriz': m, 'objetos': objetos, 'tam': tam, 'columnas': columnas, 'filas': filas,
            'esc': pygame.Rect(0, 0, columnas * tam, filas * tam), 'entrada': entrada,
            'puertas': [{'lado': l, 'rect': _rect_puerta(l, columnas, filas, tam)} for l in salidas],
            'inicio': ((inicio_casilla[1] + 0.5 + dc * 0.5) * tam, (inicio_casilla[0] + 0.5 + df * 0.5) * tam),
            'alcanzables': _alcanzables(m, objetos, inicio_casilla), 'vitrinas': [], 'piezas': [], 'interior': False}
    sala.update(extra or {})
    return sala


def _candidata(var, entrada, salidas, azar, columnas, filas, tam, radio_centro):
    """Una sala armada capa por capa (sin validar)."""
    sim = _elegir(azar, var.get('simetria'), 'no')
    forma = _elegir(azar, var.get('forma'), 'rect')
    if var.get('especiales') and any(e in ('rio', 'costa', 'cintas', 'cables') for e in var['especiales']): sim = 'no'   # esas cosas no se espejan
    lados = LADOS if sim != 'no' else ([entrada] if entrada else []) + list(salidas)
    libres = _zonas_libres(columnas, filas, lados, radio_centro)
    m = _matriz_base(columnas, filas, entrada, salidas)
    est = {'m': m, 'tam': tam, 'sim': sim, 'forma': forma, 'libres': libres, 'ocupadas': set(), 'objetos': [], 'piezas': [], 'azar': azar}
    _silueta(m, azar, forma, libres, sim)
    for especial in var.get('especiales', []): ESPECIALES[especial](m, azar, libres, sim)
    _agregar_paredes(m, azar, libres, sim, var.get('paredes', (0, 2)))
    for terreno, manchas, casillas in var.get('terrenos', []):
        for _ in range(azar.randint(*manchas)): _mancha(m, azar, terreno, azar.randint(*casillas), libres, sim)
    for maquina, cantidad in var.get('maquinas', []):
        for _ in range(azar.randint(*cantidad)): _poner_maquina(m, azar, maquina, libres, sim)
    piezas = var.get('piezas', {})
    copias = len(_espejos(1, 1, sim, filas, columnas))
    for _ in range(math.ceil(azar.randint(*var.get('num_piezas', (0, 0))) / copias) if piezas else 0):
        _poner_pieza(est, azar, _elegir(azar, piezas, None))
    pesos = var.get('objetos', {})
    cobertura = [o for o in pesos if mundos.OBJETOS[o].get('cobertura')] or list(pesos)
    _poisson(est, azar, cobertura, math.ceil(azar.randint(2, 4) / copias), 2.4, 2.6, 6.5)          # para cubrirse cerca de la pelea
    sueltos = [o for o in pesos for _ in range(pesos[o])]
    _poisson(est, azar, sueltos, math.ceil(azar.randint(*var.get('cantidad', (0, 0))) / copias), 1.7, 3.0, 9.5)
    return est


def _generar(var, entrada, salidas, azar, columnas=COLUMNAS, filas=FILAS, tam=TAM_CASILLA, radio_centro=1):
    """Genera varias candidatas validas y se queda con la de mejor puntaje."""
    mejor, mejor_puntaje, validas = None, None, 0
    for _ in range(INTENTOS):
        est = _candidata(var, entrada, salidas, azar, columnas, filas, tam, radio_centro)
        puntaje = _validar(est, entrada, salidas)
        if puntaje is None: continue
        validas += 1
        if mejor_puntaje is None or puntaje > mejor_puntaje: mejor, mejor_puntaje = est, puntaje
        if validas >= CANDIDATAS: break
    if mejor is None:                                           # salida de emergencia: sala vacia
        mejor = {'m': _matriz_base(columnas, filas, entrada, salidas), 'objetos': [], 'piezas': [], 'sim': 'no', 'forma': 'rect'}
    return mejor


def generar_sala(era, variante, entrada='sur', salidas=('norte',), semilla=None):
    """Sala de combate de una era con la variante elegida en la puerta."""
    azar = random.Random(semilla)
    datos = mundos.ERAS[era]['variantes'][variante]
    est = _generar(datos, entrada, list(salidas), azar)
    return _armar(est['m'], est['objetos'], TAM_CASILLA, entrada, salidas,
                  {'tipo': 'combate', 'era': era, 'variante': variante, 'interior': datos.get('interior', False),
                   'piezas': est['piezas'], 'simetria': est['sim'], 'forma': est['forma']})


def generar_arena(era, salidas=('norte',), semilla=None, tipo='jefe'):
    """Arena del jefe o del Regi: centro grande y libre, pocas cosas en los costados."""
    azar = random.Random(semilla)
    est = _generar(mundos.ERAS[era]['arena'], 'sur', list(salidas), azar, radio_centro=3)
    return _armar(est['m'], est['objetos'], TAM_CASILLA, 'sur', salidas,
                  {'tipo': tipo, 'era': era, 'variante': 'arena', 'piezas': est['piezas'], 'simetria': est['sim'], 'forma': est['forma']})


def generar_tienda(era, salidas=('oeste', 'este'), semilla=None):
    """Salon de la tienda del tamaño de la pantalla: Kecleon en el mostrador, un estante arriba a la derecha,
    otro abajo a la izquierda (asi el HUD no tapa nada) y dos mesas con los objetos destacados."""
    tam, columnas, filas = TIENDA_CASILLA, TIENDA_COLUMNAS, TIENDA_FILAS
    m = _matriz_base(columnas, filas, 'sur', salidas)
    cc = columnas // 2
    for f in range(4, filas - 1):                                 # alfombra desde la entrada hasta el mostrador
        for c in range(cc - 1, cc + 2): m[f][c] = 'alfombra'
    ancho = columnas * tam
    alto = filas * tam
    objetos = [crear_objeto('estante', (ancho - 80 - 180, 65)), crear_objeto('estante', (80 + 180, alto - 65)),
               crear_objeto('kecleon', (ancho // 2, 62)), crear_objeto('mostrador', (ancho // 2, 105)),
               crear_objeto('mesa', (300, 330)), crear_objeto('mesa', (ancho - 300, 330)),
               crear_objeto('maceta', (70, 450)), crear_objeto('maceta', (ancho - 60, 450))]
    for o in objetos: o['celdas'] = _celdas_de(o['nombre'], o['rect'].center, tam)
    vitrinas = [{'pos': (ancho - 80 - 300 + i * 120, 62), 'destacado': False} for i in range(3)]      # estante de arriba
    vitrinas += [{'pos': (80 + 60 + i * 120, alto - 68), 'destacado': False} for i in range(3)]       # estante de abajo
    vitrinas += [{'pos': (300, 325), 'destacado': True}, {'pos': (ancho - 300, 325), 'destacado': True}]   # mesas
    return _armar(m, objetos, tam, 'sur', salidas, {'tipo': 'tienda', 'era': era, 'variante': 'tienda', 'vitrinas': vitrinas,
                                                    'tendero': (ancho // 2, 62), 'interior': True})


def generar_nivel(semilla=None):
    """Compatibilidad con mainprubag.py: sala con las claves viejas (paredes, piedras, puertas, agua)."""
    sala = generar_sala(3, 'patio del castillo', 'sur', ['norte', 'este', 'oeste'], semilla)
    m, tam = sala['matriz'], sala['tam']
    return {'matriz': m, 'paredes': rectangulos(m, lambda t: t == 'pared', tam), 'piedras': [o['rect'] for o in sala['objetos'] if o['solido']],
            'puertas': [p['rect'] for p in sala['puertas']], 'agua': rectangulos(m, lambda t: t == 'agua', tam)}


if __name__ == '__main__':
    letras = {'suelo': '.', 'pared': '#', 'puerta': 'D', 'entrada': 'E', 'agua': '~', 'puente': '=', 'hierba': '"', 'lava': '%', 'sombra': 's'}
    for era, var in ((3, 'bosque encantado'), (1, 'cueva rupestre'), (2, 'templo de bronce')):
        sala = generar_sala(era, var, 'sur', ['norte', 'este'])
        marcas = {c for o in sala['objetos'] for c in o['celdas']}
        print(var, '-', sala['forma'], sala['simetria'], sala['piezas'])
        for f, fila in enumerate(sala['matriz']):
            print(''.join('o' if (f, c) in marcas else letras.get(t, t[0]) for c, t in enumerate(fila)))
