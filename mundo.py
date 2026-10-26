"""
mundo.py - La sala donde se pelea: como se genera, lo que pasa adentro y las particulas.

    generacion   salas procedurales (combate, tienda, arena de jefe)
    entorno      terrenos que reaccionan, objetos que se rompen, maquinas y clima
    efectos      particulas y la transicion al entrar o salir de una sala

    from mundo import generacion, entorno, efectos
"""

import math
import os
import random
from types import SimpleNamespace
import pygame
import datos
from datos import mundos
from sistema import animaciones


# ==================== generacion ====================

def armar_generacion():
    """Generacion procedural de salas (estilo Hades): combate, tienda y arena de jefe.

        from mundo import generacion
        sala = generacion.generar_sala(era, 'bosque encantado', 'sur', ['norte', 'este'])
        sala = generacion.generar_tienda(era, ['oeste', 'este'])
        sala = generacion.generar_arena(era)

    Como se arma una sala (por capas, y despues se valida):
        1. silueta      rectangulo, esquinas cortadas, cruz, columnas, circulo o cueva (automata celular)
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
        elif forma == 'circulo':                                    # arena redonda: lo que queda afuera del circulo es pared
            radio = min(fc, cc) - 0.5
            tapar = {(f, c) for f in range(1, filas - 1) for c in range(1, columnas - 1) if math.hypot(f - fc, c - cc) > radio}
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
        """Arena del jefe o del Regi: centro grande y libre, pocas cosas en los costados. La era puede pedir otro tamaño ('tamaño': (columnas, filas))."""
        azar = random.Random(semilla)
        datos = mundos.ARENA_REGI if tipo == 'regi' and 'plan_fijo' not in mundos.ERAS[era] else mundos.ERAS[era]['arena']
        columnas, filas = datos.get('tamaño', (COLUMNAS, FILAS))
        est = _generar(datos, 'sur', list(salidas), azar, columnas, filas, radio_centro=3)
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

    return SimpleNamespace(**locals())


generacion = armar_generacion()


# ==================== entorno ====================

def armar_entorno():
    """Lo que pasa en la sala mientras jugas: terrenos que reaccionan a los ataques, objetos que se rompen,
    maquinas que ayudan a ciertos tipos y el clima.

        ent = entorno.crear(sala)
        entorno.actualizar(ent, contexto, ahora)          # cada frame (contexto: jugador, enemigos y como dañarlos)
        entorno.reaccionar(ent, x, y, radio, tipo, ahora)  # un ataque de ese tipo toco esa zona
        entorno.dibujar(ent, ventana, cx, cy, ahora)      # piso, terrenos y objetos
        entorno.dibujar_clima(ent, ventana, ahora)        # lluvia, niebla, etc. por encima de todo

    Los dibujos son formas basicas con el nombre de cada cosa hasta que lleguen los sprites.
    """
    normalizar_tipo = datos.pokemones.normalizar_tipo
    direccion_vector, AnimadorPokemon, tiene_sprites = animaciones.direccion_vector, animaciones.AnimadorPokemon, animaciones.tiene_sprites

    TICK = 500                    # ms entre cada daño de terreno
    DAÑO_CHOQUE = 8               # daño por tick si estas en agua electrificada
    DURACION_ELECTRICO = 3000
    DURACION_FUEGO = (2200, 3400)
    PROB_MONEDAS = 0.35           # chance de que un objeto roto suelte monedas
    EXPLOSION = {'radio': 120, 'daño': 45}
    EMPUJAN = {'lucha': 11.0, 'psiquico': 14.0}    # tipos que empujan objetos al pegarles (fuerza)
    FUERZA_EMBESTIDA = 9.0
    CONDUCEN = ('agua', 'charco', 'cable', 'cascada')
    INMUNES_CHOQUE = ('electrico', 'tierra', 'volador')

    # lo que le pasa a un terreno cuando lo toca un ataque: (terreno, tipo del ataque) -> accion
    # 'convertir' cambia el terreno (con probabilidad opcional), 'electrificar' electrifica el agua conectada,
    # 'encender'/'apagar' fuego, 'invertir' da vuelta una cinta, 'pulso' descarga un generador, 'cortocircuito' lo hace explotar
    REACCIONES = {
        ('agua', 'hielo'): ('convertir', 'hielo'), ('agua', 'electrico'): ('electrificar',), ('agua', 'veneno'): ('convertir', 'toxico'),
        ('charco', 'hielo'): ('convertir', 'hielo'), ('charco', 'electrico'): ('electrificar',), ('charco', 'fuego'): ('convertir', 'suelo'),
        ('charco', 'veneno'): ('convertir', 'toxico'),
        ('hielo', 'fuego'): ('convertir', 'agua'), ('nieve', 'fuego'): ('convertir', 'charco'),
        ('hierba', 'fuego'): ('encender',), ('aceite', 'fuego'): ('encender',),
        ('fuego', 'agua'): ('apagar',), ('fuego', 'hielo'): ('apagar',),
        ('arena', 'agua'): ('convertir', 'lodo'), ('lodo', 'fuego'): ('convertir', 'arena'),
        ('lava', 'agua'): ('convertir', 'roca_volcanica'), ('lava', 'hielo'): ('convertir', 'roca_volcanica'),
        ('toxico', 'agua'): ('convertir', 'charco'), ('sombra', 'fuego'): ('convertir', 'suelo'),
        ('suelo', 'planta'): ('convertir', 'hierba', 0.35), ('ceniza', 'planta'): ('convertir', 'hierba', 0.5),
        ('suelo', 'siniestro'): ('convertir', 'sombra', 0.25),
        ('cable', 'tierra'): ('convertir', 'suelo'), ('cable', 'agua'): ('electrificar',), ('cinta', 'electrico'): ('invertir',),
        ('cascada', 'hielo'): ('convertir', 'cascada_helada'), ('cascada_helada', 'fuego'): ('convertir', 'cascada'),
        ('escarcha', 'fuego'): ('convertir', 'suelo'),
        ('cascada', 'electrico'): ('electrificar',),
        ('brasero', 'agua'): ('convertir', 'brasero_apagado'), ('brasero_apagado', 'fuego'): ('convertir', 'brasero'),
        ('fogata', 'agua'): ('convertir', 'fogata_apagada'), ('fogata', 'hielo'): ('convertir', 'fogata_apagada'), ('fogata_apagada', 'fuego'): ('convertir', 'fogata'),
        ('forja', 'agua'): ('convertir', 'forja_apagada'), ('forja_apagada', 'fuego'): ('convertir', 'forja'),
        ('horno', 'agua'): ('convertir', 'horno_apagado'), ('horno', 'hielo'): ('convertir', 'horno_apagado'),
        ('horno_apagado', 'fuego'): ('convertir', 'horno'),
        ('generador', 'electrico'): ('pulso',), ('generador', 'agua'): ('cortocircuito',), ('generador_roto', 'electrico'): ('convertir', 'generador'),
    }

    # que le hace cada terreno a quien lo pisa: 'todos' vale para los tipos que no aparecen
    # velocidad/daño/enfriamiento/defensa/regen son multiplicadores, tick es daño cada TICK ms
    PISADAS = {
        'agua': {'agua': {'velocidad': 1.3}},
        'charco': {'agua': {'velocidad': 1.15}},
        'hielo': {'todos': {'resbala': True}, 'hielo': {'velocidad': 1.7, 'sprint_gratis': True}, 'volador': {}},
        'nieve': {'todos': {'velocidad': 0.7}, 'hielo': {'velocidad': 1.25}, 'volador': {}, 'normal': {}},
        'hierba': {'planta': {'oculto': True, 'velocidad': 1.2}, 'bicho': {'oculto': True, 'velocidad': 1.2}},
        'fuego': {'todos': {'tick': 6}, 'fuego': {'daño': 1.2}, 'dragon': {}, 'volador': {'tick': 3}},
        'arena': {'todos': {'velocidad': 0.8}, 'tierra': {'velocidad': 1.15}, 'roca': {}, 'acero': {}, 'volador': {}, 'normal': {}},
        'lodo': {'todos': {'velocidad': 0.6}, 'tierra': {'velocidad': 1.2}, 'agua': {'velocidad': 1.05}, 'volador': {}, 'normal': {}},
        'lava': {'fuego': {'daño': 1.35, 'velocidad': 1.1}, 'dragon': {'daño': 1.15}, 'volador': {'tick': 2}},
        'toxico': {'todos': {'tick': 4}, 'veneno': {'daño': 1.3, 'velocidad': 1.15}, 'acero': {}, 'volador': {}},
        'sombra': {'siniestro': {'oculto': True, 'daño': 1.25}, 'fantasma': {'oculto': True, 'velocidad': 1.15}},
        'aceite': {'todos': {'resbala': True}, 'acero': {}, 'volador': {}},
        'cable': {'todos': {'tick': 5}, 'electrico': {'regen': 3.0, 'enfriamiento': 0.8}, 'tierra': {}, 'volador': {}},
        'corriente': {'todos': {'velocidad': 0.9}, 'volador': {'velocidad': 1.5, 'sprint_gratis': True}},
        'roca_volcanica': {'fuego': {'regen': 1.5}, 'roca': {'defensa': 0.9}},
        'ceniza': {'fuego': {'regen': 1.5}},
    }
    PISADAS['escarcha'] = {'todos': {'resbala': True}, 'hielo': {'velocidad': 1.3}, 'volador': {}}
    for _lado, _v in {'n': (0, -2.2), 's': (0, 2.2), 'e': (2.2, 0), 'o': (-2.2, 0)}.items():   # cintas: te llevan (acero pesa mas, volador ni las toca)
        PISADAS['cinta_' + _lado] = {'todos': {'empuje': _v}, 'acero': {'empuje': (_v[0] * 0.4, _v[1] * 0.4)}, 'volador': {}}

    # maquinas: (radio en casillas, {tipo: efectos}) mientras estes cerca
    AURAS = {
        'cascada': (2.2, {'agua': {'daño': 1.3, 'regen': 3.0, 'enfriamiento': 0.85}}),
        'cascada_helada': (2.2, {'hielo': {'daño': 1.3, 'regen': 2.0, 'enfriamiento': 0.85}}),
        'brasero': (1.8, {'fuego': {'daño': 1.3, 'enfriamiento': 0.9}}),
        'fogata': (2.0, {'fuego': {'daño': 1.3, 'regen': 2.0}, 'normal': {'regen': 1.5}}),
        'forja': (2.2, {'fuego': {'daño': 1.3, 'enfriamiento': 0.9}, 'acero': {'defensa': 0.8, 'daño': 1.15}}),
        'horno': (2.4, {'fuego': {'daño': 1.35, 'regen': 2.0}, 'acero': {'defensa': 0.85}}),
        'generador': (2.2, {'electrico': {'enfriamiento': 0.75, 'regen': 3.0}}),
        'altar': (2.0, {'psiquico': {'enfriamiento': 0.8, 'daño': 1.15}, 'fantasma': {'daño': 1.2}, 'hada': {'enfriamiento': 0.8}}),
        'cristal_dragonico': (2.4, {'dragon': {'daño': 1.3, 'velocidad': 1.1}}),
        'iman': (2.0, {'acero': {'defensa': 0.75}, 'electrico': {'regen': 1.5}}),
        'monolito': (2.0, {'roca': {'defensa': 0.75, 'daño': 1.15}, 'tierra': {'defensa': 0.85}}),
    }

    # cuanto daño le hace cada tipo a cada material (lo que no aparece es x1)
    MATERIALES = {
        'madera': {'fuego': 3.0, 'lucha': 2.0, 'roca': 1.5, 'planta': 0.5},
        'piedra': {'lucha': 3.0, 'roca': 2.0, 'tierra': 2.0, 'acero': 2.0, 'fuego': 0.3, 'electrico': 0.3},
        'metal': {'fuego': 2.0, 'tierra': 2.0, 'lucha': 1.5, 'acero': 0.5, 'electrico': 0.5},
        'basura': {'fuego': 3.0, 'veneno': 0.2},
        'vidrio': {'roca': 3.0, 'lucha': 2.0, 'acero': 2.0, 'electrico': 2.0, 'psiquico': 1.5},
        'hielo': {'fuego': 4.0, 'lucha': 2.0, 'roca': 2.0, 'acero': 2.0, 'hielo': 0.0},
        'planta': {'fuego': 4.0, 'volador': 2.0, 'bicho': 2.0, 'hielo': 2.0, 'agua': 0.5, 'planta': 0.0},
        'tela': {'fuego': 4.0, 'volador': 2.0, 'bicho': 2.0},
        'ceramica': {'lucha': 2.0, 'roca': 2.0, 'tierra': 2.0},
        'hueso': {'lucha': 2.0, 'tierra': 2.0, 'roca': 1.5, 'fuego': 0.5},
        'hielo_eterno': {'fuego': 4.0, 'otros': 0.0},
    }

    # climas: multiplican el daño de cada tipo, cambian velocidades y algunos lastiman (chip) a los que no son inmunes
    # el clima de la sala dura toda la sala (sin chip); el que traen los movimientos dura DURACION_CLIMA y si lastima
    CLIMAS = {
        'despejado': {'nombre': 'Despejado', 'mult': {}},
        'nublado': {'nombre': 'Nublado', 'mult': {}},
        'nieve': {'nombre': 'Nevada', 'mult': {'hielo': 1.2}, 'velocidad': {'hielo': 1.15}},
        'lluvia': {'nombre': 'Lluvia', 'mult': {'agua': 1.4, 'fuego': 0.6}, 'velocidad': {'agua': 1.15}},
        'sol': {'nombre': 'Dia soleado', 'mult': {'fuego': 1.4, 'agua': 0.6}, 'velocidad': {'planta': 1.2}},
        'granizo': {'nombre': 'Granizo', 'mult': {'hielo': 1.4}, 'velocidad': {'hielo': 1.2}, 'chip': 2, 'inmunes': ('hielo',)},
        'tormenta_arena': {'nombre': 'Tormenta de arena', 'mult': {'roca': 1.3, 'tierra': 1.15}, 'velocidad': {'tierra': 1.15}, 'chip': 2,
                           'inmunes': ('roca', 'tierra', 'acero')},
        'niebla': {'nombre': 'Niebla', 'mult': {'fantasma': 1.2, 'siniestro': 1.2}, 'deteccion': 0.6},
        'tormenta_electrica': {'nombre': 'Tormenta electrica', 'mult': {'electrico': 1.3}, 'velocidad': {'electrico': 1.15}},
    }
    DURACION_CLIMA = 15000

    # movimientos que cambian el clima (los de asistencia/especiales, para que no llueva con cada golpe)
    CLIMA_MOVIMIENTO = {
        'danza_lluvia': 'lluvia', 'hidrobomba': 'lluvia', 'dia_soleado': 'sol', 'llamarada': 'sol', 'rayo_solar': 'sol',
        'granizo': 'granizo', 'nevada': 'granizo', 'ventisca': 'granizo', 'viento_hielo': 'granizo',
        'tormenta_arena': 'tormenta_arena', 'terremoto': 'tormenta_arena', 'avalancha': 'tormenta_arena',
        'niebla': 'niebla', 'bola_sombra': 'niebla', 'pulso_umbrio': 'niebla', 'trueno': 'tormenta_electrica',
    }

    _fuentes, _textos = {}, {}
    CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'mundo')
    _imagenes, _escaladas = {}, {}


    def imagen(tipo, nombre, era=None):
        """Sprite de assets/mundo/<era>/<tipo>/<nombre>.png o, si no hay, de assets/mundo/<tipo>/<nombre>.png. None si no existe."""
        clave = (tipo, nombre, era)
        if clave not in _imagenes:
            rutas = ([os.path.join(CARPETA_ASSETS, era, tipo, nombre + '.png')] if era else []) + [os.path.join(CARPETA_ASSETS, tipo, nombre + '.png')]
            _imagenes[clave] = None
            for ruta in rutas:
                if os.path.isfile(ruta):
                    try: _imagenes[clave] = pygame.image.load(ruta).convert_alpha(); break
                    except pygame.error: pass
        return _imagenes[clave]


    def _escalada(img, ancho, alto=None):
        """Imagen escalada (pixel art: sin suavizar). Sin alto, mantiene la proporcion."""
        alto = alto or max(1, round(img.get_height() * ancho / img.get_width()))
        clave = (id(img), ancho, alto)
        if clave not in _escaladas: _escaladas[clave] = pygame.transform.scale(img, (ancho, alto))
        return _escaladas[clave]


    def _texto(texto, tam=16, color=(255, 255, 255)):
        """Texto renderizado una sola vez y guardado."""
        clave = (texto, tam, color)
        if clave not in _textos:
            if tam not in _fuentes: _fuentes[tam] = pygame.font.Font(None, tam)
            _textos[clave] = _fuentes[tam].render(texto, True, color)
        return _textos[clave]


    def crear(sala, clima=None, ahora=0):
        """Estado de la sala en juego. clima es el de la sala (en salas interiores no llega)."""
        ent = {'sala': sala, 'm': sala['matriz'], 'tam': sala['tam'], 'objetos': sala['objetos'], 'era': mundos.ERAS[sala['era']],
               'version': 0, 'cache': {}, 'electrico': {}, 'fuego': {}, 'reaccion': {}, 'ocupadas': set(),
               'clima': None, 'clima_hasta': None, 'clima_base': None if sala.get('interior') else clima, 'prox_clima': 0, 'prox_fuego': 0, 'charcos_lluvia': 0, 'ahora': ahora,
               'pendientes': [], 'visuales': [], 'eventos': [], 'fondo': None, 'maquinas': [], 'vacios': 0, 'celdas_vacio': set()}
        _buscar_maquinas(ent)
        ent['clima'] = ent['clima_base']
        return ent


    def _buscar_maquinas(ent):
        tam = ent['tam']
        ent['maquinas'] = [((c + 0.5) * tam, (f + 0.5) * tam, t) for f, fila in enumerate(ent['m']) for c, t in enumerate(fila)
                           if mundos.TERRENOS[t].get('maquina')]


    def tipos_de(entidad):
        """El jugador tiene 'tipos' (lista), los enemigos 'tipo' (uno solo)."""
        return [normalizar_tipo(t) for t in (entidad.get('tipos') or [entidad.get('tipo')]) if t]


    # ---------- casillas ----------

    def casilla(ent, x, y):
        return int(y // ent['tam']), int(x // ent['tam'])


    def terreno_en(ent, x, y):
        f, c = casilla(ent, x, y)
        if 0 <= f < len(ent['m']) and 0 <= c < len(ent['m'][0]): return ent['m'][f][c]
        return 'pared'


    def rect_casilla(ent, f, c):
        return pygame.Rect(c * ent['tam'], f * ent['tam'], ent['tam'], ent['tam'])


    def _casillas_rect(ent, r):
        f0, c0 = casilla(ent, r.left, r.top)
        f1, c1 = casilla(ent, r.right - 1, r.bottom - 1)
        return {(f, c) for f in range(f0, f1 + 1) for c in range(c0, c1 + 1)}


    def _casillas_circulo(ent, x, y, radio):
        """Casillas que toca un circulo."""
        tam, m = ent['tam'], ent['m']
        f0, c0 = casilla(ent, x - radio, y - radio)
        f1, c1 = casilla(ent, x + radio, y + radio)
        salida = []
        for f in range(max(0, f0), min(len(m) - 1, f1) + 1):
            for c in range(max(0, c0), min(len(m[0]) - 1, c1) + 1):
                px, py = max(c * tam, min(x, (c + 1) * tam)), max(f * tam, min(y, (f + 1) * tam))
                if math.hypot(px - x, py - y) <= radio: salida.append((f, c))
        return salida


    def cambiar(ent, f, c, nuevo):
        """Cambia el terreno de una casilla. No pone algo que bloquee debajo de alguien (lo dejaria trabado)."""
        if mundos.TERRENOS[nuevo]['bloquea'] and (f, c) in ent['ocupadas']: return False
        viejo = ent['m'][f][c]
        ent['m'][f][c] = nuevo
        ent['version'] += 1; ent['fondo'] = None
        if nuevo != 'fuego': ent['fuego'].pop((f, c), None)
        if mundos.TERRENOS[viejo].get('maquina') or mundos.TERRENOS[nuevo].get('maquina'): _buscar_maquinas(ent)
        return True


    # ---------- choques ----------

    def solidos(ent, tipos):
        """Rectangulos que no puede atravesar alguien de esos tipos (el agua no frena a los de agua, los fantasma pasan los objetos...)."""
        clave = (ent['version'], tuple(sorted(tipos)))
        if clave not in ent['cache']:
            if len(ent['cache']) > 40: ent['cache'].clear()
            bloquea = lambda t: mundos.TERRENOS[t]['bloquea'] and not any(x in mundos.TERRENOS[t].get('pasan', ()) for x in tipos)
            rects = generacion.rectangulos(ent['m'], bloquea, ent['tam'])
            if 'fantasma' not in tipos: rects += [o['rect'] for o in ent['objetos'] if o['solido']]
            ent['cache'][clave] = rects
        return ent['cache'][clave]


    def solidos_proyectil(ent):
        """Lo que frena un proyectil: paredes, maquinas y objetos (el agua y la lava no)."""
        clave = (ent['version'], 'proyectil')
        if clave not in ent['cache']:
            rects = generacion.rectangulos(ent['m'], lambda t: mundos.TERRENOS[t].get('solido'), ent['tam'])
            ent['cache'][clave] = rects + [o['rect'] for o in ent['objetos'] if o['solido']]
        return ent['cache'][clave]


    def destructibles(ent):
        """Objetos que se pueden romper (se suman a los objetivos de los ataques)."""
        return [o for o in ent['objetos'] if o['vida'] is not None and o['vida'] > 0]


    def mover(ent, rect, dx, dy, tipos):
        """Mueve un rect frenando contra lo solido para esos tipos."""
        duros = solidos(ent, tipos)
        for ax, ay in ((dx, 0), (0, dy)):
            r = rect.move(ax, ay)
            if r.collidelist(duros) == -1: rect.x, rect.y = r.x, r.y


    def punto_libre(ent, azar, lejos=None, distancia=0):
        """Centro de una casilla alcanzable, pisable y sin objetos (para hacer aparecer enemigos o jefes)."""
        ocupadas = {c for o in ent['objetos'] for c in o['celdas']}
        tam, m = ent['tam'], ent['m']
        buenas = [(f, c) for f, c in ent['sala']['alcanzables'] if (f, c) not in ocupadas and not mundos.TERRENOS[m[f][c]]['bloquea']
                  and m[f][c] not in generacion.PELIGROSOS]
        lejanas = [(f, c) for f, c in buenas if not lejos or math.hypot((c + 0.5) * tam - lejos[0], (f + 0.5) * tam - lejos[1]) >= distancia]
        f, c = azar.choice(lejanas or buenas or [(len(m) // 2, len(m[0]) // 2)])
        return int((c + 0.5) * tam), int((f + 0.5) * tam)


    # ---------- efectos sobre pokemon ----------

    def _sumar(ef, nuevos):
        for k, v in nuevos.items():
            if k in ('velocidad', 'daño', 'enfriamiento', 'defensa', 'regen'): ef[k] = ef.get(k, 1.0) * v
            elif k == 'empuje': ef[k] = (ef.get(k, (0, 0))[0] + v[0], ef.get(k, (0, 0))[1] + v[1])
            elif k == 'tick': ef[k] = ef.get(k, 0) + v
            else: ef[k] = ef.get(k) or v


    def _elegir(tabla, tipos, con_todos=True):
        """Efectos de una tabla para esos tipos. Si es doble tipo se juntan, y el daño por tick es el menor de los dos."""
        entradas = [tabla[t] for t in tipos if t in tabla]
        if not entradas: return tabla.get('todos', {}) if con_todos else {}
        ef = {}
        for e in entradas: _sumar(ef, {k: v for k, v in e.items() if k != 'tick'})
        tick = min(e.get('tick', 0) for e in entradas)
        if tick: ef['tick'] = tick
        return ef


    def efectos_de(ent, tipos, rect):
        """Todo lo que el entorno le hace a un pokemon parado en rect: terreno, maquinas cerca, agua electrificada y clima."""
        ef = {}
        _sumar(ef, _elegir(PISADAS.get(terreno_en(ent, *rect.center), {}), tipos))
        usadas = set()
        for x, y, maquina in ent['maquinas']:                      # cada tipo de maquina ayuda una sola vez
            radio, por_tipo = AURAS.get(maquina, (0, {}))
            if maquina not in usadas and math.hypot(x - rect.centerx, y - rect.centery) <= radio * ent['tam']:
                nuevos = _elegir(por_tipo, tipos, False)
                if nuevos: _sumar(ef, nuevos); usadas.add(maquina)
        if ent['electrico'] and not any(t in INMUNES_CHOQUE for t in tipos):
            zona = rect.inflate(ent['tam'] * 0.4, ent['tam'] * 0.4)
            if any((f, c) in ent['electrico'] for f, c in _casillas_rect(ent, zona)): ef['choque'] = True
        clima = CLIMAS.get(ent['clima'])
        if clima:
            _sumar(ef, _elegir({t: {'velocidad': v} for t, v in clima.get('velocidad', {}).items()}, tipos, False))
            temporal = ent['clima_hasta'] is not None                # el clima de la sala no lastima, el de un movimiento si
            if temporal and clima.get('chip') and not any(t in clima.get('inmunes', ()) for t in tipos): _sumar(ef, {'tick': clima['chip']})
        return ef


    def deteccion(ent, jugador):
        """Multiplicador del rango con que te ven los enemigos (escondido en hierba/sombra, niebla)."""
        m = 0.3 if jugador.get('oculto') else 1.0
        return m * CLIMAS.get(ent['clima'], {}).get('deteccion', 1.0)


    def mult_clima(ent, tipo):
        clima = CLIMAS.get(ent['clima'])
        return clima['mult'].get(normalizar_tipo(tipo), 1.0) if clima else 1.0


    # ---------- reacciones a ataques ----------

    def reaccionar(ent, x, y, radio, tipo, ahora):
        """Un ataque de ese tipo toco el circulo (x, y, radio): congela agua, quema hierba, electrifica, etc."""
        tipo = normalizar_tipo(tipo)
        if not tipo: return
        for f, c in _casillas_circulo(ent, x, y, radio):
            t = ent['m'][f][c]
            accion = REACCIONES.get(('cinta' if t.startswith('cinta') else t, tipo))
            if not accion or ent['reaccion'].get((f, c, tipo), 0) > ahora: continue
            ent['reaccion'][(f, c, tipo)] = ahora + 250             # no repetir la misma reaccion cada frame
            _hacer(ent, accion, f, c, ahora)


    def reaccionar_linea(ent, x0, y0, x1, y1, radio, tipo, ahora):
        """Igual que reaccionar pero a lo largo de un golpe cuerpo a cuerpo."""
        pasos = max(1, int(math.hypot(x1 - x0, y1 - y0) // max(8, radio)))
        for i in range(pasos + 1):
            reaccionar(ent, x0 + (x1 - x0) * i / pasos, y0 + (y1 - y0) * i / pasos, radio, tipo, ahora)


    def _hacer(ent, accion, f, c, ahora):
        tam = ent['tam']
        x, y = (c + 0.5) * tam, (f + 0.5) * tam
        if accion[0] == 'convertir':
            if len(accion) < 3 or random.random() < accion[2]: cambiar(ent, f, c, accion[1])
        elif accion[0] == 'electrificar': electrificar(ent, f, c, ahora)
        elif accion[0] == 'encender': encender(ent, f, c, ahora)
        elif accion[0] == 'apagar': cambiar(ent, f, c, 'ceniza')
        elif accion[0] == 'invertir':
            vuelta = {'n': 's', 's': 'n', 'e': 'o', 'o': 'e'}
            cambiar(ent, f, c, 'cinta_' + vuelta[ent['m'][f][c][-1]])
        elif accion[0] == 'pulso':
            ent['reaccion'][(f, c, 'electrico')] = ahora + 3000      # el generador tarda en recargarse
            explotar(ent, x, y, tam * 2.5, 25, 'electrico', False, {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 100}, 'chispa')
        elif accion[0] == 'cortocircuito':
            cambiar(ent, f, c, 'generador_roto')
            explotar(ent, x, y, tam * 2, 35, 'electrico', True, None, 'chispa')


    def electrificar(ent, f, c, ahora):
        """Electrifica toda el agua (y cables) conectada a esa casilla por unos segundos."""
        m = ent['m']
        vistas, pendientes = {(f, c)}, [(f, c)]
        while pendientes and len(vistas) < 90:
            a, b = pendientes.pop()
            for na, nb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= na < len(m) and 0 <= nb < len(m[0]) and (na, nb) not in vistas and m[na][nb] in CONDUCEN:
                    vistas.add((na, nb)); pendientes.append((na, nb))
        for casilla_ in vistas:
            if m[casilla_[0]][casilla_[1]] in CONDUCEN: ent['electrico'][casilla_] = ahora + DURACION_ELECTRICO


    def abrir_vacio(ent, x, y, radio, maximo):
        """El piso se rompe y queda un vacio. Nunca debajo de alguien ni delante de las puertas, y como mucho 'maximo' casillas por sala."""
        cerca_puerta = [p['rect'].inflate(ent['tam'] * 4, ent['tam'] * 4) for p in ent['sala']['puertas']]
        entrada = ent['sala'].get('inicio')
        for f, c in _casillas_circulo(ent, x, y, radio):
            if ent['vacios'] >= maximo: return
            r = rect_casilla(ent, f, c)
            if ent['m'][f][c] not in generacion.PISABLES or r.collidelist(cerca_puerta) != -1: continue
            if entrada and r.inflate(ent['tam'] * 2, ent['tam'] * 2).collidepoint(entrada): continue
            if cambiar(ent, f, c, 'vacio'): ent['vacios'] += 1; ent['celdas_vacio'].add((f, c))


    def vaciar_franja(ent, y_hasta):
        """Todo el piso por encima de y_hasta se vuelve vacio (menos debajo de alguien) y los objetos de ahi caen."""
        tam = ent['tam']
        for f in range(int(y_hasta // tam)):
            for c in range(len(ent['m'][0])):
                if ent['m'][f][c] not in ('pared', 'puerta', 'entrada', 'vacio') and cambiar(ent, f, c, 'vacio'): ent['celdas_vacio'].add((f, c))
        caen = [o for o in ent['objetos'] if o['rect'].centery < y_hasta]
        for o in caen: ent['objetos'].remove(o)
        if caen: ent['version'] += 1


    def congelar_linea(ent, a, b, radio):
        """El rayo hielo de Regice deja escarcha (resbala) a lo largo de su camino."""
        pasos = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // (ent['tam'] / 2)))
        for i in range(pasos + 1):
            for f, c in _casillas_circulo(ent, a[0] + (b[0] - a[0]) * i / pasos, a[1] + (b[1] - a[1]) * i / pasos, radio):
                if ent['m'][f][c] in generacion.PISABLES: cambiar(ent, f, c, 'escarcha')


    def poner_objeto(ent, nombre, centro, evitar=()):
        """Pone un objeto en la sala si entra (piso libre, lejos de las puertas y sin pisar a nadie). Devuelve el objeto o None."""
        m, tam = ent['m'], ent['tam']
        celdas = generacion._celdas_de(nombre, centro, tam)
        ocupadas = {c for o in ent['objetos'] for c in o['celdas']}
        for f, c in celdas:
            if not (0 <= f < len(m) and 0 <= c < len(m[0])) or mundos.TERRENOS[m[f][c]]['bloquea'] or (f, c) in ocupadas: return None
        o = generacion.crear_objeto(nombre, (round(centro[0]), round(centro[1])), celdas)
        puertas = [p['rect'].inflate(tam * 4, tam * 4) for p in ent['sala']['puertas']]
        if o['rect'].collidelist(list(evitar) + puertas) != -1: return None
        o['de_regi'] = True
        ent['objetos'].append(o); ent['version'] += 1
        return o


    def sacar_de_regi(ent):
        """Cuando cae el Regi se van sus muros, rocas y torres."""
        ent['objetos'][:] = [o for o in ent['objetos'] if not o.get('de_regi')]
        ent['version'] += 1


    def cerrar_vacios(ent):
        """El piso vuelve a donde habia vacios."""
        for f, c in ent['celdas_vacio']:
            if ent['m'][f][c] == 'vacio': cambiar(ent, f, c, 'suelo')
        ent['celdas_vacio'].clear(); ent['vacios'] = 0


    def encender(ent, f, c, ahora=None):
        if ent['m'][f][c] in ('hierba', 'aceite', 'suelo', 'ceniza', 'fuego') and cambiar(ent, f, c, 'fuego'):
            ent['fuego'][(f, c)] = (ent['ahora'] if ahora is None else ahora) + random.randint(*DURACION_FUEGO)


    def explotar(ent, x, y, radio, daño, tipo, al_jugador, efecto=None, clase='fuego'):
        """Encola una explosion: se aplica en actualizar() (asi una explosion puede romper otro barril y encadenar)."""
        ent['pendientes'].append({'x': x, 'y': y, 'radio': radio, 'daño': daño, 'tipo': tipo, 'jugador': al_jugador, 'efecto': efecto, 'clase': clase})


    # ---------- objetos ----------

    def dañar_objeto(ent, obj, datos, direccion, ahora):
        """Un ataque le pega a un objeto: daño segun material y tipo, empujes, chispas en el metal..."""
        if obj['vida'] is None or obj['vida'] <= 0: return
        tipo = normalizar_tipo(datos.get('tipo'))
        try: base = float(datos.get('daño', 0))
        except (TypeError, ValueError): base = 0
        d = mundos.OBJETOS[obj['nombre']]
        mult = 99 if d.get('arde') and tipo == 'fuego' else _mult_material(obj['material'], tipo)
        obj['vida'] -= base * mult; obj['golpe'] = ahora
        if tipo == 'electrico' and obj['material'] == 'metal' and ahora >= obj.get('chispa', 0):   # el metal conduce
            obj['chispa'] = ahora + 600
            explotar(ent, obj['rect'].centerx, obj['rect'].centery, ent['tam'] * 1.6, 12, 'electrico', False,
                     {'tipo': 'paralizar', 'duracion': 1000, 'probabilidad': 100}, 'chispa')
        fuerza = EMPUJAN.get(tipo) or (FUERZA_EMBESTIDA if datos.get('forma') == 'embestida' else 0)
        if obj['empujable'] and fuerza and direccion in direccion_vector:
            vx, vy = direccion_vector[direccion]; n = math.hypot(vx, vy) or 1
            obj['vel'] = [vx / n * fuerza, vy / n * fuerza]
        if obj['vida'] <= 0: romper(ent, obj, tipo)


    def _mult_material(material, tipo):
        tabla = MATERIALES.get(material, {})
        return tabla.get(tipo, tabla.get('otros', 1.0))


    def romper(ent, obj, tipo=None):
        """Saca el objeto, suelta monedas a veces, explota si es explosivo y deja su terreno (charco, aceite, toxico...)."""
        if obj in ent['objetos']: ent['objetos'].remove(obj)
        obj['vida'] = 0
        ent['version'] += 1
        d = mundos.OBJETOS[obj['nombre']]
        x, y = obj['rect'].center
        ent['visuales'].append({'clase': 'polvo', 'x': x, 'y': y, 'radio': max(obj['rect'].size) // 2, 'color': d['color'], 'vida': 18})
        ent['eventos'].append(('roto', x, y, d['color']))           # para las particulas y la experiencia
        if random.random() < PROB_MONEDAS: ent['eventos'].append(('monedas', x, y, random.randint(2, 6)))
        if d.get('explota'): explotar(ent, x, y, EXPLOSION['radio'], EXPLOSION['daño'], 'fuego', True)
        if d.get('al_romper'):
            for f, c in _casillas_circulo(ent, x, y, ent['tam'] * 0.8):
                if ent['m'][f][c] in generacion.PISABLES: cambiar(ent, f, c, d['al_romper'])
        if d.get('arde') and tipo == 'fuego':                       # lo que arde deja fuego donde estaba
            for f, c in _casillas_rect(ent, obj['rect']): encender(ent, f, c)


    def _actualizar_empujados(ent, ctx, ahora):
        """Objetos deslizandose: chocan con paredes, otros objetos y enemigos (les pegan). Al agua se hunden."""
        for obj in [o for o in ent['objetos'] if o['vel'][0] or o['vel'][1]]:
            rapidez = math.hypot(*obj['vel'])
            duros = generacion.rectangulos(ent['m'], lambda t: mundos.TERRENOS[t].get('solido'), ent['tam']) + \
                [o['rect'] for o in ent['objetos'] if o['solido'] and o is not obj]
            choco = False
            for i in (0, 1):
                obj['resto'][i] += obj['vel'][i]; paso = int(obj['resto'][i]); obj['resto'][i] -= paso
                r = obj['rect'].move(paso if i == 0 else 0, paso if i == 1 else 0)
                if r.collidelist(duros) != -1: choco = True
                else: obj['rect'].topleft = r.topleft                # se mueve el mismo rect (las listas de solidos lo comparten)
            for e in ctx['enemigos']:
                if e['vida'] > 0 and obj['rect'].colliderect(e['rect']):
                    ctx['dañar_enemigo'](e, round(rapidez * 3), 'normal', None); choco = True
            ent['version'] += 1
            t = terreno_en(ent, *obj['rect'].center)
            if t in ('agua', 'lava'):                               # se hunde (el hielo congela el agua, en la lava se quema)
                f, c = casilla(ent, *obj['rect'].center)
                if obj['material'] == 'hielo' and t == 'agua': cambiar(ent, f, c, 'hielo')
                romper(ent, obj, 'fuego' if t == 'lava' else None); continue
            if choco:
                if mundos.OBJETOS[obj['nombre']].get('explota') and rapidez > 6: romper(ent, obj, 'fuego'); continue
                obj['vel'] = [0.0, 0.0]
            else:
                obj['vel'] = [v * 0.94 for v in obj['vel']]
                if math.hypot(*obj['vel']) < 0.5: obj['vel'] = [0.0, 0.0]
            if not (obj['vel'][0] or obj['vel'][1]): obj['celdas'] = _casillas_rect(ent, obj['rect']) if obj['solido'] else set()


    # ---------- clima ----------

    def iniciar_clima(ent, clave, ahora, duracion=DURACION_CLIMA):
        """Clima temporal (de un movimiento o de un jefe). Sin duracion queda toda la sala. Adentro no llueve."""
        if clave not in CLIMAS or ent['sala'].get('interior'): return
        ent['clima'] = clave
        if duracion: ent['clima_hasta'] = ahora + duracion
        else: ent['clima_base'], ent['clima_hasta'] = clave, None


    def al_usar_movimiento(ent, nombre, ahora):
        """Algunos movimientos cambian el clima (lluvia, sol, granizo...)."""
        if nombre in CLIMA_MOVIMIENTO: iniciar_clima(ent, CLIMA_MOVIMIENTO[nombre], ahora)


    def _casilla_al_azar(ent, terrenos):
        m = ent['m']
        for _ in range(25):
            f, c = random.randint(1, len(m) - 2), random.randint(1, len(m[0]) - 2)
            if m[f][c] in terrenos: return f, c
        return None


    def _actualizar_clima(ent, ctx, ahora):
        """Una vez por segundo: la lluvia hace charcos y apaga el fuego, el sol derrite y seca, el granizo congela, caen rayos."""
        if ent['clima_hasta'] is not None and ahora >= ent['clima_hasta']:   # se termina el clima del movimiento: vuelve el de la sala
            ent['clima'], ent['clima_hasta'] = ent['clima_base'], None
        if not ent['clima'] or ahora < ent['prox_clima']: return
        ent['prox_clima'] = ahora + 1000
        clima = ent['clima']
        if clima == 'lluvia':
            for f, c in list(ent['fuego']): cambiar(ent, f, c, 'ceniza')
            lugar = _casilla_al_azar(ent, ('suelo', 'arena', 'ceniza'))
            if lugar and ent['charcos_lluvia'] < 30:
                cambiar(ent, *lugar, 'charco' if ent['m'][lugar[0]][lugar[1]] != 'arena' else 'lodo'); ent['charcos_lluvia'] += 1
        elif clima == 'sol':
            cambios = {'hielo': 'agua', 'nieve': 'charco', 'charco': 'suelo', 'lodo': 'arena'}
            for _ in range(2):
                lugar = _casilla_al_azar(ent, tuple(cambios))
                if lugar: cambiar(ent, *lugar, cambios[ent['m'][lugar[0]][lugar[1]]])
        elif clima == 'nieve':                                      # nieva despacio: se junta nieve y se congelan los charcos
            lugar = _casilla_al_azar(ent, ('suelo', 'charco'))
            if lugar and ent['charcos_lluvia'] < 25:
                cambiar(ent, *lugar, 'nieve' if ent['m'][lugar[0]][lugar[1]] == 'suelo' else 'hielo'); ent['charcos_lluvia'] += 1
        elif clima == 'granizo':
            for _ in range(2):
                lugar = _casilla_al_azar(ent, ('agua', 'charco'))
                if lugar: cambiar(ent, *lugar, 'hielo')
        elif clima == 'tormenta_electrica' and random.random() < 0.4:   # rayo: prefiere enemigos, metal y agua
            vivos = [e for e in ctx['enemigos'] if e['vida'] > 0]
            metal = [o for o in ent['objetos'] if o['material'] == 'metal']
            if vivos and random.random() < 0.6: x, y = random.choice(vivos)['rect'].center
            elif metal: x, y = random.choice(metal)['rect'].center
            else:
                lugar = _casilla_al_azar(ent, ('agua', 'charco', 'suelo'))
                if not lugar: return
                x, y = (lugar[1] + 0.5) * ent['tam'], (lugar[0] + 0.5) * ent['tam']
            explotar(ent, x, y, 70, 20, 'electrico', False, {'tipo': 'paralizar', 'duracion': 1000, 'probabilidad': 100}, 'rayo')
            f, c = casilla(ent, x, y)
            if ent['m'][f][c] in CONDUCEN: electrificar(ent, f, c, ahora)


    # ---------- cada frame ----------

    def actualizar(ent, ctx, ahora):
        """
        ctx = {'jugador': j, 'enemigos': [...], 'dañar_jugador': f(daño, tipo), 'dañar_enemigo': f(enemigo, daño, tipo, efecto)}
        Deja en cada pokemon ['entorno'] los efectos que tiene encima (velocidad, daño, resbala, oculto, empuje...).
        """
        j = ctx['jugador']
        ent['ahora'] = ahora
        vivos = [e for e in ctx['enemigos'] if e['vida'] > 0]
        ent['ocupadas'] = set()
        for e in [j] + vivos: ent['ocupadas'] |= _casillas_rect(ent, e['rect'])
        for e in [j] + vivos:                                       # terreno, auras, choques y clima sobre cada pokemon
            tipos = tipos_de(e)
            ef = efectos_de(ent, tipos, e['rect'])
            e['entorno'] = ef
            if e is j: j['oculto'] = bool(ef.get('oculto'))
            daño = ef.get('tick', 0) + (DAÑO_CHOQUE if ef.get('choque') else 0)
            if daño and ahora >= e.get('prox_tick', 0):
                e['prox_tick'] = ahora + TICK
                if e is j: ctx['dañar_jugador'](daño, None)
                else: ctx['dañar_enemigo'](e, daño, None, {'tipo': 'paralizar', 'duracion': 600, 'probabilidad': 100} if ef.get('choque') else None)
            if e is not j and ef.get('empuje'):                      # las cintas tambien llevan a los enemigos
                e.setdefault('resto_cinta', [0.0, 0.0])
                for i in (0, 1): e['resto_cinta'][i] += ef['empuje'][i]
                px, py = int(e['resto_cinta'][0]), int(e['resto_cinta'][1])
                e['resto_cinta'][0] -= px; e['resto_cinta'][1] -= py
                mover(ent, e['rect'], px, py, tipos)
        if ahora >= ent['prox_fuego']:                               # el fuego se esparce por la hierba y quema objetos
            ent['prox_fuego'] = ahora + 400
            for (f, c), hasta in list(ent['fuego'].items()):
                if ahora >= hasta: cambiar(ent, f, c, 'ceniza'); continue
                for nf, nc in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
                    if 0 <= nf < len(ent['m']) and 0 <= nc < len(ent['m'][0]) and ent['m'][nf][nc] in ('hierba', 'aceite') and random.random() < 0.25:
                        encender(ent, nf, nc, ahora)
                zona = rect_casilla(ent, f, c)
                for o in [o for o in ent['objetos'] if mundos.OBJETOS[o['nombre']].get('arde') and o['rect'].colliderect(zona)]:
                    romper(ent, o, 'fuego')
        ent['electrico'] = {k: v for k, v in ent['electrico'].items() if v > ahora}
        _actualizar_clima(ent, ctx, ahora)
        _actualizar_empujados(ent, ctx, ahora)
        for _ in range(10):                                         # explosiones (pueden encadenarse)
            if not ent['pendientes']: break
            lote, ent['pendientes'] = ent['pendientes'], []
            for ex in lote:
                centro = pygame.Vector2(ex['x'], ex['y'])
                for e in vivos:
                    if e['vida'] > 0 and centro.distance_to(e['rect'].center) <= ex['radio'] + max(e['rect'].size) / 2:
                        ctx['dañar_enemigo'](e, ex['daño'], ex['tipo'], ex['efecto'])
                inmune = ex['clase'] != 'fuego' and 'electrico' in tipos_de(j)       # las chispas no lastiman a los electricos
                if ex['jugador'] and not inmune and centro.distance_to(j['rect'].center) <= ex['radio']:
                    ctx['dañar_jugador'](ex['daño'] * 0.6, ex['tipo'])
                for o in destructibles(ent):
                    if centro.distance_to(o['rect'].center) <= ex['radio']:
                        dañar_objeto(ent, o, {'tipo': ex['tipo'], 'daño': ex['daño']}, None, ahora)
                ent['visuales'].append({'clase': ex['clase'], 'x': ex['x'], 'y': ex['y'], 'radio': ex['radio'], 'vida': 16})
                if ex['clase'] == 'fuego': ent['eventos'].append(('explosion', ex['x'], ex['y'], ex['radio']))
        for v in ent['visuales']: v['vida'] -= 1
        ent['visuales'] = [v for v in ent['visuales'] if v['vida'] > 0]


    # ---------- dibujo ----------

    def _aclarar(color, k):
        return tuple(max(0, min(255, x + k)) for x in color)


    def _dibujar_textura(fondo, t, r, f, c):
        """Dibujito simple para que cada terreno se distinga del piso (hasta que lleguen los sprites)."""
        azar = random.Random(f * 131 + c)
        x, y, tam = r.x, r.y, r.width
        if t in ('hielo', 'cascada_helada', 'escarcha'):                         # brillos en diagonal
            for k in (0.25, 0.6):
                pygame.draw.line(fondo, (255, 255, 255), (x + tam * k, y + tam * 0.15), (x + tam * (k + 0.25), y + tam * 0.4), 2)
        elif t in ('agua', 'charco', 'cascada'):                     # olitas
            for k in (0.3, 0.7):
                yy = y + tam * k
                pygame.draw.arc(fondo, (180, 215, 255), (x + tam * 0.15, yy - 6, tam * 0.35, 12), 0, math.pi, 2)
                pygame.draw.arc(fondo, (180, 215, 255), (x + tam * 0.5, yy - 6, tam * 0.35, 12), 0, math.pi, 2)
        elif t == 'nieve':
            for _ in range(5): pygame.draw.circle(fondo, (205, 215, 230), (x + azar.randint(6, tam - 6), y + azar.randint(6, tam - 6)), 3)
        elif t == 'hierba':                                          # matitas
            for _ in range(4):
                px, py = x + azar.randint(8, tam - 8), y + azar.randint(12, tam - 4)
                pygame.draw.line(fondo, (30, 100, 30), (px, py), (px - 4, py - 10), 2)
                pygame.draw.line(fondo, (30, 100, 30), (px, py), (px + 4, py - 10), 2)
        elif t in ('lava', 'toxico'):                                # burbujas
            color = (255, 200, 60) if t == 'lava' else (200, 120, 230)
            for _ in range(3): pygame.draw.circle(fondo, color, (x + azar.randint(8, tam - 8), y + azar.randint(8, tam - 8)), azar.randint(3, 6), 2)
        elif t in ('arena', 'lodo', 'ceniza'):                       # granitos
            for _ in range(6): fondo.set_at((x + azar.randint(2, tam - 3), y + azar.randint(2, tam - 3)), (90, 70, 40) if t != 'ceniza' else (40, 40, 40))
        elif t == 'vacio':                                           # estrellitas en el negro
            pygame.draw.rect(fondo, (70, 40, 110), r, 2)
            for _ in range(4): fondo.set_at((x + azar.randint(4, tam - 5), y + azar.randint(4, tam - 5)), (200, 180, 255))
        elif t == 'puente':                                          # tablones
            for k in range(1, 4): pygame.draw.line(fondo, (90, 60, 30), (x, y + tam * k // 4), (x + tam, y + tam * k // 4), 2)


    def _armar_fondo(ent):
        """Piso, terrenos, paredes y maquinas en una imagen (se rehace solo cuando cambia el terreno)."""
        m, tam, era = ent['m'], ent['tam'], ent['era']
        fondo = pygame.Surface((len(m[0]) * tam, len(m) * tam))
        con_sprite = set()
        for f, fila in enumerate(m):
            for c, t in enumerate(fila):
                r = pygame.Rect(c * tam, f * tam, tam, tam)
                img = imagen('terrenos', t, era['clave'])               # si hay sprite del terreno se usa ese
                if img:
                    fondo.blit(_escalada(img, tam, tam), r); con_sprite.add(t); continue
                if t == 'suelo': color = _aclarar(era['suelo'], 8 if (f + c) % 2 else -4)   # piso del color de la era
                elif t == 'pared': color = era['pared']
                else: color = mundos.TERRENOS[t]['color']
                pygame.draw.rect(fondo, color, r)
                if mundos.TERRENOS[t].get('maquina'): pygame.draw.rect(fondo, (20, 20, 20), r, 3)
                if t.startswith('cinta'):                                # flechitas de las cintas
                    dx, dy = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'o': (-1, 0)}[t[-1]]
                    cx, cy = r.center
                    pygame.draw.line(fondo, (200, 200, 60), (cx - dx * tam // 4, cy - dy * tam // 4), (cx + dx * tam // 4, cy + dy * tam // 4), 3)
                    pygame.draw.circle(fondo, (200, 200, 60), (cx + dx * tam // 4, cy + dy * tam // 4), 5)
                if t == 'cable': pygame.draw.line(fondo, (40, 40, 40), r.topleft, r.bottomright, 4)
                _dibujar_textura(fondo, t, r, f, c)
        vistos = set()                                                  # un cartel por cada mancha de terreno
        for f, fila in enumerate(m):
            for c, t in enumerate(fila):
                if t in ('suelo', 'pared', 'vacio') or t in con_sprite or (f, c) in vistos: continue
                grupo, pendientes = [(f, c)], [(f, c)]; vistos.add((f, c))
                while pendientes:
                    a, b = pendientes.pop()
                    for na, nb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= na < len(m) and 0 <= nb < len(m[0]) and (na, nb) not in vistos and m[na][nb] == t:
                            vistos.add((na, nb)); grupo.append((na, nb)); pendientes.append((na, nb))
                a, b = min(grupo, key=lambda p: (p[0] - sum(g[0] for g in grupo) / len(grupo)) ** 2 + (p[1] - sum(g[1] for g in grupo) / len(grupo)) ** 2)
                claro = sum(mundos.TERRENOS[t]['color'] or (0, 0, 0)) > 450
                txt = _texto('cinta' if t.startswith('cinta') else t.replace('_', ' '), 16, (30, 30, 30) if claro else (235, 235, 235))
                fondo.blit(txt, txt.get_rect(center=((b + 0.5) * tam, (a + 0.5) * tam)))
        ent['fondo'] = fondo


    def dibujar(ent, ventana, cx, cy, ahora, tipos_jugador=()):
        """Dibuja la sala vista desde la camara (cx, cy). Las maquinas muestran su radio solo si ayudan a tus tipos."""
        if ent['fondo'] is None: _armar_fondo(ent)
        ventana.blit(ent['fondo'], (0, 0), pygame.Rect(cx, cy, *ventana.get_size()))
        tam = ent['tam']
        for x, y, maquina in ent['maquinas']:                          # radio de ayuda de las maquinas que te sirven
            if maquina in AURAS and any(t in AURAS[maquina][1] for t in tipos_jugador): pygame.draw.circle(ventana, mundos.TERRENOS[maquina]['color'], (round(x - cx), round(y - cy)), round(AURAS[maquina][0] * tam), 1)
        for (f, c) in ent['fuego']:                                    # fuego que titila
            r = rect_casilla(ent, f, c).move(-cx, -cy)
            pygame.draw.rect(ventana, (255, 200, 40) if (ahora // 120 + f + c) % 2 else (240, 90, 20), r.inflate(-10, -10))
        for (f, c) in ent['electrico']:                                # agua electrificada
            r = rect_casilla(ent, f, c).move(-cx, -cy)
            pygame.draw.line(ventana, (255, 240, 60), r.topleft, r.bottomright, 2)
            pygame.draw.line(ventana, (255, 240, 60), r.topright, r.bottomleft, 2)
        for o in ent['objetos']:
            d = mundos.OBJETOS[o['nombre']]
            r = o['rect'].move(-cx, -cy)
            if not r.colliderect(ventana.get_rect()): continue
            img = imagen('objetos', o['nombre'], ent['era']['clave'])
            if tiene_sprites(o['nombre']):                              # un pokemon puesto como objeto (Kecleon en la tienda): animado
                if 'animador' not in o:
                    o['animador'] = AnimadorPokemon(o['nombre'], pygame.Rect(0, 0, 10, 10), max(o['rect'].size) + 30); o['animador'].cambiar('idle', 0, True)
                o['animador'].rect.center = r.center
                o['animador'].actualizar()
                if o['animador'].dibujar(ventana): continue
            if img:                                                     # sprite: mismo ancho que el objeto, apoyado abajo (un arbol sobresale hacia arriba)
                sprite = _escalada(img, r.width)
                ventana.blit(sprite, sprite.get_rect(midbottom=r.midbottom))
                if ahora - o['golpe'] < 90: pygame.draw.rect(ventana, (255, 255, 255), sprite.get_rect(midbottom=r.midbottom), 2)
            else:                                                       # sin sprite: forma basica con el nombre
                color = (255, 255, 255) if ahora - o['golpe'] < 90 else o.get('color', d['color'])
                (pygame.draw.ellipse if d.get('forma') == 'circulo' else pygame.draw.rect)(ventana, color, r)
                (pygame.draw.ellipse if d.get('forma') == 'circulo' else pygame.draw.rect)(ventana, (15, 15, 15), r, 2)
                if d.get('explota'): pygame.draw.circle(ventana, (230, 40, 30), r.center, 5)   # punto rojo = explota
                claro = sum(d['color']) > 450
                txt = _texto(o['nombre'].replace('_', ' '), 15, (20, 20, 20) if claro else (240, 240, 240))
                ventana.blit(txt, txt.get_rect(center=r.center))
            if o['vida'] is not None and o['vida'] < o['max_vida']:
                pygame.draw.rect(ventana, (60, 0, 0), (r.x, r.y - 6, r.width, 4))
                pygame.draw.rect(ventana, (230, 200, 40), (r.x, r.y - 6, int(r.width * max(0, o['vida']) / o['max_vida']), 4))
        for v in ent['visuales']:                                      # explosiones, chispas, rayos y polvo de lo que se rompe
            x, y = round(v['x'] - cx), round(v['y'] - cy)
            if v['clase'] == 'polvo': pygame.draw.circle(ventana, v['color'], (x, y), round(v['radio'] * (1.6 - v['vida'] / 18)), 2)
            elif v['clase'] == 'rayo':
                pygame.draw.line(ventana, (255, 255, 180), (x + 20, y - 400), (x - 10, y - 150), 4)
                pygame.draw.line(ventana, (255, 255, 180), (x - 10, y - 150), (x, y), 4)
                pygame.draw.circle(ventana, (255, 250, 120), (x, y), round(v['radio'] * 0.6), 3)
            else:
                color = (255, 240, 80) if v['clase'] == 'chispa' else (255, 120, 30)
                pygame.draw.circle(ventana, color, (x, y), round(v['radio'] * (1.1 - v['vida'] / 32)), 5)


    _velos = {}


    def _velo(tam, color):
        clave = (tam, color)
        if clave not in _velos:
            _velos[clave] = pygame.Surface(tam, pygame.SRCALPHA); _velos[clave].fill(color)
        return _velos[clave]


    def dibujar_clima(ent, ventana, ahora):
        """Capa del clima encima de todo y el cartelito de cuanto le queda."""
        clima = ent['clima']
        if not clima: return
        W, H = ventana.get_size()
        azar = random.Random(ahora // 50)                              # mismo dibujo durante 50 ms
        if clima == 'lluvia':
            ventana.blit(_velo((W, H), (40, 60, 120, 45)), (0, 0))
            for _ in range(90):
                x, y = azar.randint(0, W), azar.randint(0, H)
                pygame.draw.line(ventana, (150, 180, 255), (x, y), (x - 4, y + 14), 1)
        elif clima == 'granizo':
            ventana.blit(_velo((W, H), (200, 220, 255, 40)), (0, 0))
            for _ in range(70): pygame.draw.circle(ventana, (250, 250, 255), (azar.randint(0, W), azar.randint(0, H)), 2)
        elif clima == 'tormenta_arena':
            ventana.blit(_velo((W, H), (190, 150, 80, 80)), (0, 0))
            for _ in range(50):
                x, y = azar.randint(0, W), azar.randint(0, H)
                pygame.draw.line(ventana, (220, 190, 120), (x, y), (x + 18, y + 3), 1)
        elif clima == 'nieve':
            ventana.blit(_velo((W, H), (220, 230, 255, 30)), (0, 0))
            for i in range(60):                                     # copos que caen despacio
                x = (i * 97 + ahora // 40 * (1 + i % 3)) % W
                y = (i * 53 + ahora // 25 * (1 + i % 2)) % H
                pygame.draw.circle(ventana, (255, 255, 255), (x, y), 2 + i % 2)
        elif clima == 'nublado': ventana.blit(_velo((W, H), (60, 60, 70, 40)), (0, 0))
        elif clima == 'niebla': ventana.blit(_velo((W, H), (170, 170, 170, 110)), (0, 0))
        elif clima == 'sol': ventana.blit(_velo((W, H), (255, 220, 80, 35)), (0, 0))
        elif clima == 'tormenta_electrica':
            destello = any(v['clase'] == 'rayo' and v['vida'] > 12 for v in ent['visuales'])
            ventana.blit(_velo((W, H), (255, 255, 255, 70) if destello else (20, 20, 50, 70)), (0, 0))
        texto = CLIMAS[clima]['nombre'] + ('' if ent['clima_hasta'] is None else ' ' + str(max(0, (ent['clima_hasta'] - ahora) // 1000 + 1)) + 's')
        t = _texto(texto, 20, (255, 255, 255))
        ventana.blit(t, t.get_rect(midtop=(W // 2, 24)))

    return SimpleNamespace(**locals())


entorno = armar_entorno()


# ==================== efectos ====================

def armar_efectos():
    """Particulas (golpes, cosas que se rompen, explosiones, subir de nivel...) y la transicion al entrar o salir de una sala.

        ef = efectos.crear()
        efectos.golpe(ef, x, y, color)          # y romper, explosion, nivel, evolucion, corazones, polvo...
        efectos.actualizar(ef)                  # cada frame
        efectos.dibujar(ef, ventana, cx, cy)    # despues de los pokemon
        efectos.transicion(ef, 'entrar', ahora, (x, y))   # circulo que se abre desde la puerta
        efectos.dibujar_transicion(ef, ventana, ahora)

    Si existe assets/efectos/<nombre>.png (tira horizontal de frames cuadrados) se usa esa animacion en vez de las particulas.
    """
    CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'efectos')
    _tiras = {}


    def crear():
        return {'parts': [], 'anims': [], 'transicion': None}


    def _tira(nombre):
        """Frames de assets/efectos/<nombre>.png o None."""
        if nombre not in _tiras:
            _tiras[nombre] = None
            ruta = os.path.join(CARPETA, nombre + '.png')
            if os.path.isfile(ruta):
                try:
                    hoja = pygame.image.load(ruta).convert_alpha()
                    lado = hoja.get_height()
                    _tiras[nombre] = [hoja.subsurface((i * lado, 0, lado, lado)).copy() for i in range(max(1, hoja.get_width() // lado))]
                except pygame.error: pass
        return _tiras[nombre]


    def _animacion(ef, nombre, x, y, tam):
        """Si hay sprite del efecto lo usa. Devuelve True si lo encontro."""
        frames = _tira(nombre)
        if not frames: return False
        ef['anims'].append({'frames': [pygame.transform.scale(f, (tam, tam)) for f in frames], 'x': x, 'y': y, 'i': 0.0})
        return True


    def chispas(ef, x, y, color, cantidad=8, velocidad=4.0, vida=22, tam=4, gravedad=0.0, subir=0.0):
        for _ in range(cantidad):
            a, v = random.uniform(0, math.tau), random.uniform(0.4, 1.0) * velocidad
            ef['parts'].append({'x': x, 'y': y, 'vx': math.cos(a) * v, 'vy': math.sin(a) * v - subir, 'vida': random.randint(vida // 2, vida),
                                'max': vida, 'color': color, 'tam': tam, 'g': gravedad, 'forma': 'circulo'})


    def golpe(ef, x, y, color, tipo=None):
        """Cuando un ataque le pega a algo."""
        if not _animacion(ef, 'golpe_' + str(tipo), x, y, 64) and not _animacion(ef, 'golpe', x, y, 56):
            chispas(ef, x, y, color, 9, 4.5, 16, 4)
            chispas(ef, x, y, (255, 255, 255), 4, 2.5, 10, 3)


    def romper(ef, x, y, color):
        """Pedazos que saltan y caen al romper un objeto."""
        if _animacion(ef, 'romper', x, y, 72): return
        for _ in range(12):
            a, v = random.uniform(0, math.tau), random.uniform(1.5, 5)
            ef['parts'].append({'x': x, 'y': y, 'vx': math.cos(a) * v, 'vy': math.sin(a) * v - 3, 'vida': random.randint(20, 34), 'max': 34,
                                'color': color, 'tam': random.randint(4, 8), 'g': 0.35, 'forma': 'cuadrado'})


    def explosion(ef, x, y, radio):
        if _animacion(ef, 'explosion', x, y, int(radio * 2)): return
        chispas(ef, x, y, (255, 160, 40), 22, radio / 14, 30, 6)
        chispas(ef, x, y, (90, 80, 70), 12, radio / 25, 45, 9, subir=0.6)       # humo


    def nivel(ef, x, y):
        """Brillitos que suben al subir de nivel."""
        if _animacion(ef, 'nivel', x, y - 20, 80): return
        for i in range(16):
            ef['parts'].append({'x': x + random.uniform(-22, 22), 'y': y + random.uniform(-10, 20), 'vx': 0, 'vy': -random.uniform(1, 2.5),
                                'vida': 40 + i, 'max': 56, 'color': (255, 240, 120), 'tam': 3, 'g': 0, 'forma': 'estrella'})


    def evolucion(ef, x, y):
        if _animacion(ef, 'evolucion', x, y, 120): return
        chispas(ef, x, y, (255, 255, 255), 40, 6, 50, 5)
        chispas(ef, x, y, (180, 230, 255), 30, 3, 60, 4)


    def corazones(ef, x, y):
        """Un pokemon quiere unirse a tu equipo."""
        for _ in range(3):
            ef['parts'].append({'x': x + random.uniform(-12, 12), 'y': y - 20, 'vx': random.uniform(-0.3, 0.3), 'vy': -1.2, 'vida': 40, 'max': 40,
                                'color': (255, 110, 160), 'tam': 6, 'g': 0, 'forma': 'corazon'})


    def polvo(ef, x, y):
        """Polvito bajo los pies al correr o embestir."""
        ef['parts'].append({'x': x + random.uniform(-6, 6), 'y': y, 'vx': random.uniform(-0.5, 0.5), 'vy': -0.3, 'vida': 18, 'max': 18,
                            'color': (200, 190, 170), 'tam': 4, 'g': 0, 'forma': 'circulo'})


    def actualizar(ef):
        for p in ef['parts']:
            p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += p['g']; p['vx'] *= 0.94; p['vida'] -= 1
        ef['parts'] = [p for p in ef['parts'] if p['vida'] > 0][-500:]
        for a in ef['anims']: a['i'] += 0.4
        ef['anims'] = [a for a in ef['anims'] if a['i'] < len(a['frames'])]


    def dibujar(ef, ventana, cx, cy):
        for p in ef['parts']:
            x, y = round(p['x'] - cx), round(p['y'] - cy)
            t = max(1, round(p['tam'] * (0.5 + 0.5 * p['vida'] / p['max'])))
            if p['forma'] == 'cuadrado': pygame.draw.rect(ventana, p['color'], (x - t // 2, y - t // 2, t, t))
            elif p['forma'] == 'estrella':
                pygame.draw.line(ventana, p['color'], (x - t, y), (x + t, y), 2); pygame.draw.line(ventana, p['color'], (x, y - t), (x, y + t), 2)
            elif p['forma'] == 'corazon':
                pygame.draw.circle(ventana, p['color'], (x - t // 2, y), t // 2 + 1); pygame.draw.circle(ventana, p['color'], (x + t // 2, y), t // 2 + 1)
                pygame.draw.polygon(ventana, p['color'], [(x - t, y), (x + t, y), (x, y + t + 2)])
            else: pygame.draw.circle(ventana, p['color'], (x, y), t)
        for a in ef['anims']:
            frame = a['frames'][int(a['i'])]
            ventana.blit(frame, frame.get_rect(center=(round(a['x'] - cx), round(a['y'] - cy))))


    # ---------- transicion de sala ----------

    def transicion(ef, clase, ahora, centro, duracion=None):
        """'entrar': el negro se abre en circulo desde donde entras. 'salir': se cierra hacia la puerta."""
        ef['transicion'] = {'clase': clase, 'inicio': ahora, 'hasta': ahora + (duracion or (650 if clase == 'entrar' else 320)), 'centro': centro}


    def en_transicion(ef, ahora):
        t = ef['transicion']
        return bool(t) and ahora < t['hasta']


    def dibujar_transicion(ef, ventana, ahora):
        t = ef['transicion']
        if not t: return
        if ahora >= t['hasta'] and t['clase'] == 'entrar': ef['transicion'] = None; return
        W, H = ventana.get_size()
        k = max(0.0, min(1.0, (ahora - t['inicio']) / max(1, t['hasta'] - t['inicio'])))
        k = k if t['clase'] == 'entrar' else 1 - k
        radio = round(k * k * math.hypot(W, H))                # se abre rapido al final (como un iris)
        velo = pygame.Surface((W, H), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 255))
        if radio > 0: pygame.draw.circle(velo, (0, 0, 0, 0), (round(t['centro'][0]), round(t['centro'][1])), radio)
        ventana.blit(velo, (0, 0))

    return SimpleNamespace(**locals())


efectos = armar_efectos()
