"""
ia.py - Inteligencia de los enemigos: te buscan esquivando obstaculos, atacan de cerca o de lejos y se cubren.

    ia.preparar(enemigo)                 # al crearlo: elige su estilo segun el rol del pokemon
    ia.actualizar(enemigo, ctx)          # cada frame
    ia.actualizar_jefe(jefe, ctx)        # jefes y Regis
    ia.dibujar_avisos(ventana, lista, cx, cy, ahora)   # los avisos antes de cada ataque

Estilos (segun el rol del pokemon):
    'pegador'  tanque / atacante   va por el camino mas corto y te pega de cerca
    'tirador'  estratega           se queda a distancia, dispara si te ve, se aleja si te acercas y se esconde para recargar
    'rapido'   velocista           te da vueltas y se tira en embestida en linea recta
Estados: 'patrulla' (no te vio) -> 'caza' (te vio, le pegaste o le avisaron: va a donde te vio por ultima vez).
Todo ataque se avisa antes (anillo, linea o mira) y como mucho MAX_ATACANTES te pegan de cerca a la vez: dificil pero justo.
"""

import math
import random
import pygame
import entorno
import mundos
from pokemones import ROL_POKEMON

MAX_ATACANTES = 2          # pegadores/rapidos atacando a la vez
DETECCION = 380            # distancia a la que te ven (si no hay nada en el medio)
OIDO = 130                 # tan cerca te sienten aunque no te vean
GRITO = 320                # al verte avisan a los compañeros que esten a esta distancia
PENSAR = 150               # ms entre decisiones (el movimiento es cada frame)

ESTILOS = {
    'pegador': {'vel': 1.9, 'alcance': 62, 'aviso': 380, 'cd': 1100},
    'tirador': {'vel': 1.6, 'rango': (230, 400), 'aviso': 380, 'cd': 1700, 'vel_bala': 6.5, 'dist_bala': 560},
    'rapido': {'vel': 2.4, 'orbita': 170, 'aviso': 480, 'cd': 2300, 'vel_embestida': 9.5, 'dist_embestida': 280},
}
ESTILO_ROL = {'tanque': 'pegador', 'atacante': 'pegador', 'estratega': 'tirador', 'velocista': 'rapido'}
VECINOS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def preparar(e, estilo=None):
    """Agrega al enemigo lo que necesita la ia."""
    estilo = estilo or ESTILO_ROL.get(ROL_POKEMON.get(e['nombre']), 'pegador')
    e.update({'estilo': estilo, 'estado_ia': 'patrulla', 'ultima_vista': None, 'cd_ataque': 0, 'aviso': None, 'embestida_ia': None,
              'meta': None, 'cubrirse_hasta': 0, 'pensar': 0, 'resto_ia': [0.0, 0.0], 'vida_ant': e['vida'], 'grito': 0,
              'paseo': 0, 'giro': random.choice((-1, 1)), 'origen': e['rect'].center})


# ---------- mapa del lugar ----------

def _pasa(ent, tipos):
    """Casillas bloqueadas para esos tipos (terreno + objetos solidos)."""
    clave = ('bloq', ent['version'], tuple(sorted(tipos)))
    if clave not in ent['cache']:
        m = ent['m']
        malas = {(f, c) for f, fila in enumerate(m) for c, t in enumerate(fila)
                 if mundos.TERRENOS[t]['bloquea'] and not any(x in mundos.TERRENOS[t].get('pasan', ()) for x in tipos)}
        if 'fantasma' not in tipos:
            for o in ent['objetos']:
                if o['solido']: malas |= o['celdas']
        ent['cache'][clave] = malas
    return ent['cache'][clave]


def mapa_flujo(ent, destino, tipos):
    """Mapa de Dijkstra (como en Brogue): distancia en casillas desde cada casilla hasta destino. Se guarda mientras no cambie nada."""
    meta = entorno.casilla(ent, *destino)
    clave = ('flujo', ent['version'], meta, tuple(sorted(tipos)))
    if clave not in ent['cache']:
        malas, m = _pasa(ent, tipos), ent['m']
        dist, pendientes = {meta: 0}, [meta]
        for f, c in pendientes:                                  # BFS: con 4 vecinos alcanza y es rapido
            for a, b in VECINOS[:4]:
                nxt = (f + a, c + b)
                if nxt not in dist and 0 <= nxt[0] < len(m) and 0 <= nxt[1] < len(m[0]) and nxt not in malas:
                    dist[nxt] = dist[(f, c)] + 1; pendientes.append(nxt)
        ent['cache'][clave] = dist
    return ent['cache'][clave]


def ve(ent, a, b):
    """True si no hay paredes, maquinas ni objetos entre a y b."""
    return not any(r.clipline(a, b) for r in entorno.solidos_proyectil(ent))


def _paso_flujo(ent, e, dist, alejarse=False):
    """Centro de la casilla vecina que acerca (o aleja) mas segun el mapa de flujo. Diagonal solo si no corta esquinas."""
    f, c = entorno.casilla(ent, *e['rect'].center)
    if (f, c) not in dist: return None
    mejor, valor = None, dist[(f, c)]
    for a, b in VECINOS:
        nxt = (f + a, c + b)
        if nxt not in dist or (a and b and ((f + a, c) not in dist or (f, c + b) not in dist)): continue
        if (dist[nxt] > valor) if alejarse else (dist[nxt] < valor): mejor, valor = nxt, dist[nxt]
    if not mejor: return None
    tam = ent['tam']
    return (mejor[1] + 0.5) * tam, (mejor[0] + 0.5) * tam


def _cobertura(ent, e, jugador):
    """Casilla cerca, pegada a algo solido y que el jugador no ve: para esconderse a recargar."""
    tam, malas = ent['tam'], _pasa(ent, [e['tipo']])
    f0, c0 = entorno.casilla(ent, *e['rect'].center)
    jx, jy = jugador['rect'].center
    mejor, puntaje = None, None
    for f in range(f0 - 4, f0 + 5):
        for c in range(c0 - 4, c0 + 5):
            if (f, c) in malas or not (0 < f < len(ent['m']) - 1 and 0 < c < len(ent['m'][0]) - 1): continue
            if not any((f + a, c + b) in malas for a, b in VECINOS[:4]): continue
            p = ((c + 0.5) * tam, (f + 0.5) * tam)
            if ve(ent, p, (jx, jy)): continue
            valor = math.hypot(p[0] - e['rect'].centerx, p[1] - e['rect'].centery) + abs(math.hypot(p[0] - jx, p[1] - jy) - 300) * 0.4
            if puntaje is None or valor < puntaje: mejor, puntaje = p, valor
    return mejor


# ---------- movimiento ----------

def _mover_hacia(ent, e, punto, vel, enemigos):
    """Camina hacia un punto, separandose de los compañeros para no amontonarse."""
    ex, ey = e['rect'].center
    dx, dy = punto[0] - ex, punto[1] - ey
    n = math.hypot(dx, dy)
    if n < 2: dx = dy = 0
    else: dx, dy = dx / n, dy / n
    for o in enemigos:                                          # separacion
        if o is e or o['vida'] <= 0: continue
        ox, oy = ex - o['rect'].centerx, ey - o['rect'].centery
        d = math.hypot(ox, oy)
        if 0 < d < 46: dx += ox / d * 0.6; dy += oy / d * 0.6
    n = math.hypot(dx, dy)
    if not n: return
    e['resto_ia'][0] += dx / n * vel; e['resto_ia'][1] += dy / n * vel
    px, py = int(e['resto_ia'][0]), int(e['resto_ia'][1])
    e['resto_ia'][0] -= px; e['resto_ia'][1] -= py
    entorno.mover(ent, e['rect'], px, py, [e['tipo']])


def _ir_a(ent, e, destino, vel, enemigos, alejarse=False):
    """Va hacia destino por el camino del mapa de flujo (o derecho si lo tiene a la vista y cerca)."""
    if not alejarse and math.hypot(destino[0] - e['rect'].centerx, destino[1] - e['rect'].centery) < ent['tam'] * 1.5 and ve(ent, e['rect'].center, destino):
        _mover_hacia(ent, e, destino, vel, enemigos); return
    paso = _paso_flujo(ent, e, mapa_flujo(ent, destino, [e['tipo']]), alejarse)
    if paso: _mover_hacia(ent, e, paso, vel, enemigos)
    elif not alejarse: _mover_hacia(ent, e, destino, vel, enemigos)


# ---------- cada frame ----------

def _atacando(enemigos):
    return sum(1 for o in enemigos if o['vida'] > 0 and o.get('estilo') in ('pegador', 'rapido') and (o.get('aviso') or o.get('embestida_ia')))


def actualizar(e, ctx):
    """
    ctx = {'ent': entorno, 'jugador': j, 'enemigos': [...], 'ahora': ms, 'dañar_jugador': f(daño, tipo),
           'disparar': f(x, y, dx, dy, daño, tipo, vel, distancia)}
    """
    ent, j, ahora, enemigos = ctx['ent'], ctx['jugador'], ctx['ahora'], ctx['enemigos']
    if e['estado_hasta'] > ahora and e['estado'] in ('paralizar', 'dormir'): e['aviso'] = None; return   # aturdido: pierde el ataque
    p = ESTILOS[e['estilo']]
    vel = p['vel'] * e.get('mult_vel', 1.0) * (0.5 if e.get('estado') == 'ralentizar' and e['estado_hasta'] > ahora else 1.0)
    vel *= e.get('entorno', {}).get('velocidad', 1.0)
    jx, jy = j['rect'].center
    ex, ey = e['rect'].center
    dist = math.hypot(jx - ex, jy - ey)

    if ahora >= e['pensar']:                                    # ¿te ve? (cada PENSAR ms)
        e['pensar'] = ahora + PENSAR
        rango = DETECCION * entorno.deteccion(ent, j)
        golpeado = e['vida'] < e['vida_ant']; e['vida_ant'] = e['vida']
        viendo = dist < OIDO or (dist < rango and ve(ent, (ex, ey), (jx, jy)))
        if viendo or golpeado:
            if e['estado_ia'] == 'patrulla':                    # primera vez que te ve: signo de exclamacion y avisa
                e['grito'] = ahora + 700
                for o in enemigos:
                    if o is not e and o['vida'] > 0 and o.get('estado_ia') == 'patrulla' and math.hypot(o['rect'].centerx - ex, o['rect'].centery - ey) < GRITO:
                        o['estado_ia'] = 'caza'; o['ultima_vista'] = (jx, jy)
            e['estado_ia'] = 'caza'; e['ultima_vista'] = (jx, jy)
        e['te_ve'] = viendo

    if e['embestida_ia']:                                       # embestida en curso (rapido)
        em = e['embestida_ia']
        antes = e['rect'].center
        _mover_hacia(ent, e, (ex + em['dx'] * 50, ey + em['dy'] * 50), p['vel_embestida'], [])
        em['restante'] -= p['vel_embestida']
        if not em['pego'] and e['rect'].colliderect(j['rect']):
            ctx['dañar_jugador'](e['daño'] * 1.3, e['tipo']); em['pego'] = True
        if em['restante'] <= 0 or e['rect'].center == antes: e['embestida_ia'] = None; e['cd_ataque'] = ahora + p['cd']
        return

    if e['aviso']:                                              # avisando un ataque: se queda quieto y despues golpea
        if ahora < e['aviso']['hasta']: return
        _soltar_ataque(e, ctx, p)
        e['aviso'] = None
        return

    if e['estado_ia'] == 'patrulla':                            # pasea cerca de donde aparecio
        if ahora >= e['paseo'] or not e['meta']:
            e['paseo'] = ahora + random.randint(1500, 3000)
            e['meta'] = entorno.punto_libre(ent, random, e['origen'], 0) if random.random() < 0.3 else \
                (e['origen'][0] + random.randint(-160, 160), e['origen'][1] + random.randint(-160, 160))
        _ir_a(ent, e, e['meta'], vel * 0.5, enemigos)
        return

    if not e.get('te_ve'):                                      # te perdio de vista: va a donde te vio
        if e['ultima_vista']:
            _ir_a(ent, e, e['ultima_vista'], vel, enemigos)
            if math.hypot(e['ultima_vista'][0] - ex, e['ultima_vista'][1] - ey) < 30: e['ultima_vista'] = (jx, jy)   # te "huele" y sigue
        return

    libre = ahora >= e['cd_ataque']
    if e['estilo'] == 'pegador':
        if dist <= p['alcance'] + max(j['rect'].size) / 2 and libre and _atacando(enemigos) < MAX_ATACANTES:
            e['aviso'] = {'hasta': ahora + p['aviso'], 'clase': 'golpe', 'inicio': ahora}
        elif _atacando(enemigos) >= MAX_ATACANTES and dist < 150:   # ya hay dos pegando: espera dando vueltas
            _orbitar(ent, e, j, 150, vel * 0.7, enemigos)
        else: _ir_a(ent, e, (jx, jy), vel, enemigos)
    elif e['estilo'] == 'tirador':
        if ahora < e['cubrirse_hasta'] and e['meta']:           # recargando escondido
            _ir_a(ent, e, e['meta'], vel * 1.2, enemigos); return
        cerca, lejos = p['rango']
        if dist < cerca: _ir_a(ent, e, (jx, jy), vel, enemigos, alejarse=True)       # te alejas: se va para atras
        elif dist > lejos: _ir_a(ent, e, (jx, jy), vel, enemigos)
        elif libre:
            e['aviso'] = {'hasta': ahora + p['aviso'], 'clase': 'disparo', 'inicio': ahora, 'mira': (jx, jy)}
        else: _orbitar(ent, e, j, dist, vel * 0.6, enemigos)
    else:
        if libre and dist < 320 and _atacando(enemigos) < MAX_ATACANTES:
            n = dist or 1
            e['aviso'] = {'hasta': ahora + p['aviso'], 'clase': 'embestida', 'inicio': ahora, 'dir': ((jx - ex) / n, (jy - ey) / n)}
        else: _orbitar(ent, e, j, p['orbita'], vel, enemigos)


def _orbitar(ent, e, j, radio, vel, enemigos):
    """Da vueltas alrededor del jugador a cierta distancia (cambia de sentido si se choca)."""
    jx, jy = j['rect'].center
    ex, ey = e['rect'].center
    ang = math.atan2(ey - jy, ex - jx) + 0.35 * e['giro']
    destino = (jx + math.cos(ang) * radio, jy + math.sin(ang) * radio)
    antes = e['rect'].center
    _mover_hacia(ent, e, destino, vel, enemigos)
    if e['rect'].center == antes and random.random() < 0.05: e['giro'] *= -1


def _soltar_ataque(e, ctx, p):
    """Termina el aviso: golpe, disparo o embestida."""
    j, ahora = ctx['jugador'], ctx['ahora']
    jx, jy = j['rect'].center
    ex, ey = e['rect'].center
    a = e['aviso']
    if a['clase'] == 'golpe':
        if math.hypot(jx - ex, jy - ey) <= (p['alcance'] + max(j['rect'].size) / 2) * 1.25: ctx['dañar_jugador'](e['daño'], e['tipo'])
        e['cd_ataque'] = ahora + p['cd']
    elif a['clase'] == 'disparo':
        vx, vy = j.get('inercia', (0, 0))                        # apunta un poco adelante de donde vas
        tiempo_bala = math.hypot(jx - ex, jy - ey) / p['vel_bala']
        tx, ty = jx + vx * tiempo_bala * 0.5, jy + vy * tiempo_bala * 0.5
        n = math.hypot(tx - ex, ty - ey) or 1
        ctx['disparar'](ex, ey, (tx - ex) / n, (ty - ey) / n, e['daño'] * 0.8, e['tipo'], p['vel_bala'], p['dist_bala'])
        e['cd_ataque'] = ahora + p['cd']
        if random.random() < 0.45:                              # a veces se esconde a recargar
            e['meta'] = _cobertura(ctx['ent'], e, j)
            if e['meta']: e['cubrirse_hasta'] = ahora + 1300
    else:
        e['embestida_ia'] = {'dx': a['dir'][0], 'dy': a['dir'][1], 'restante': p['dist_embestida'], 'pego': False}


# ---------- jefes ----------

JEFE = {'vel': 1.4, 'rafaga': 2600, 'aviso_rafaga': 550, 'balas_rafaga': 5, 'abanico': 0.5, 'pisoton': 3200, 'aviso_pisoton': 650, 'radio_pisoton': 160}


def preparar_jefe(b):
    b.update({'aviso': None, 'prox_rafaga': 0, 'prox_pisoton': 0, 'resto_ia': [0.0, 0.0], 'estilo': 'jefe'})


def actualizar_jefe(b, ctx):
    """Te sigue por el mapa de flujo, tira rafagas en abanico apuntadas y si estas cerca pisotea (todo avisado)."""
    ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
    jx, jy = j['rect'].center
    bx, by = b['rect'].center
    dist = math.hypot(jx - bx, jy - by)
    if b['aviso']:
        if ahora < b['aviso']['hasta']: return
        if b['aviso']['clase'] == 'rafaga':
            base = math.atan2(jy - by, jx - bx)
            for i in range(JEFE['balas_rafaga']):
                ang = base + (i - (JEFE['balas_rafaga'] - 1) / 2) * JEFE['abanico'] / 2
                ctx['disparar'](bx, by, math.cos(ang), math.sin(ang), b['daño'] * 0.6, b['tipo'], 7, 650)
        elif dist <= JEFE['radio_pisoton'] + max(j['rect'].size) / 2: ctx['dañar_jugador'](b['daño'] * 1.2, b['tipo'])
        b['aviso'] = None
        return
    if dist < JEFE['radio_pisoton'] * 0.9 and ahora >= b['prox_pisoton']:
        b['prox_pisoton'] = ahora + JEFE['pisoton']
        b['aviso'] = {'hasta': ahora + JEFE['aviso_pisoton'], 'clase': 'pisoton', 'inicio': ahora}; return
    if ahora >= b['prox_rafaga'] and ve(ent, (bx, by), (jx, jy)):
        b['prox_rafaga'] = ahora + JEFE['rafaga']
        b['aviso'] = {'hasta': ahora + JEFE['aviso_rafaga'], 'clase': 'rafaga', 'inicio': ahora, 'mira': (jx, jy)}; return
    if dist > 120: _ir_a(ent, b, (jx, jy), JEFE['vel'], [])


# ---------- dibujo ----------

def dibujar_avisos(ventana, lista, cx, cy, ahora, fuente=None):
    """Anillos, lineas y miras que avisan cada ataque, y el '!' cuando un enemigo te descubre."""
    for e in lista:
        if e['vida'] <= 0: continue
        x, y = e['rect'].centerx - cx, e['rect'].centery - cy
        a = e.get('aviso')
        if a:
            k = min(1.0, (ahora - a['inicio']) / max(1, a['hasta'] - a['inicio']))
            if a['clase'] == 'golpe':
                r = max(e['rect'].size) // 2 + 30
                pygame.draw.circle(ventana, (255, 60, 40), (x, y), round(r * (1.4 - 0.4 * k)), 3)
            elif a['clase'] in ('disparo', 'rafaga'):
                mx, my = a['mira'][0] - cx, a['mira'][1] - cy
                pygame.draw.line(ventana, (255, 70, 50), (x, y), (mx, my), 1 + round(2 * k))
                pygame.draw.circle(ventana, (255, 70, 50), (round(mx), round(my)), 14, 2)
            elif a['clase'] == 'embestida':
                d = ESTILOS['rapido']['dist_embestida']
                pygame.draw.line(ventana, (255, 160, 40), (x, y), (x + a['dir'][0] * d, y + a['dir'][1] * d), 2 + round(4 * k))
            elif a['clase'] == 'pisoton':
                pygame.draw.circle(ventana, (255, 60, 40), (x, y), JEFE['radio_pisoton'], 2)
                pygame.draw.circle(ventana, (255, 60, 40), (x, y), round(JEFE['radio_pisoton'] * k), 0 if k > 0.95 else 2)
        if e.get('grito', 0) > ahora and fuente:
            t = fuente.render('!', True, (255, 230, 40))
            ventana.blit(t, t.get_rect(midbottom=(x, e['rect'].top - cy - 10)))
