"""
efectos.py - Particulas (golpes, cosas que se rompen, explosiones, subir de nivel...) y la transicion al entrar o salir de una sala.

    ef = efectos.crear()
    efectos.golpe(ef, x, y, color)          # y romper, explosion, nivel, evolucion, corazones, polvo...
    efectos.actualizar(ef)                  # cada frame
    efectos.dibujar(ef, ventana, cx, cy)    # despues de los pokemon
    efectos.transicion(ef, 'entrar', ahora, (x, y))   # circulo que se abre desde la puerta
    efectos.dibujar_transicion(ef, ventana, ahora)

Si existe assets/efectos/<nombre>.png (tira horizontal de frames cuadrados) se usa esa animacion en vez de las particulas.
"""

import math
import os
import random
import pygame

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
