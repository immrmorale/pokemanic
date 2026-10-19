"""
progreso.py - Niveles, experiencia, stats con IV y EV, evoluciones y amistad (pokemon que se unen a tu equipo).

    m = progreso.nuevo('electrike', 5)          # miembro nuevo: nivel, xp, IVs al azar, EVs en 0
    progreso.multiplicadores(m)                  # cuanto pegan, aguantan y corren segun nivel, IV y EV
    progreso.dar_xp(m, 120)                      # devuelve los niveles que subio
    progreso.evoluciones(m, objetos)             # a que puede evolucionar ahora (por nivel, piedra, amistad...)

Las cuentas de stats son las de los juegos: stat = (2*base + IV + EV/4) * nivel/100 + 5 (PS: + nivel + 10).
El juego usa la proporcion contra un pokemon de referencia (nivel 10, IV 15, EV 0), asi un nivel 10 normal juega igual que antes.
"""

import math
import random
from pokemones import pokemones, _oficiales, datos_juego
from animaciones import tiene_sprites

NIVEL_INICIAL = 5
NIVEL_REF = 10                     # a este nivel con IV 15 y EV 0 los numeros son los de siempre
NIVEL_MAX = 100
STATS = ('hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed')
NOMBRE_STAT = {'hp': 'PS', 'attack': 'Ataque', 'defense': 'Defensa', 'special-attack': 'At. Esp.', 'special-defense': 'Def. Esp.', 'speed': 'Velocidad'}
EV_POR_PUNTO, EV_MAX_STAT, EV_MAX = 10, 252, 510      # cada punto que te dan al subir de nivel son 10 EV
PUNTOS_POR_NIVEL = 1
XP_MULT = 0.22                     # que tan rapido se sube (simulado: quedas 2 a 5 niveles arriba de los enemigos)
PARTE_BANCA = 0.5                  # los de la banca ganan la mitad de la experiencia
AMISTAD_EVOLUCION = 20             # amistad que necesitan Pichu, Riolu... (se gana pasando salas juntos)
PROB_AMISTAD = 0.07                # chance base de que un pokemon derrotado quiera unirse (por su ratio de captura / 255)

# evoluciones que en los juegos dependen de cosas que aca no hay (hora, lugar, un movimiento...)
EVOLUCION_ESPECIAL = {
    'sneasel': {'objeto': 'garra_afilada'}, 'magneton': {'objeto': 'piedra_trueno'}, 'pichu': {'amistad': AMISTAD_EVOLUCION},
    'riolu': {'amistad': AMISTAD_EVOLUCION}, 'primeape': {'nivel': 35},
}
OBJETO_POKEAPI = {'thunder-stone': 'piedra_trueno', 'dawn-stone': 'piedra_alba', 'razor-claw': 'garra_afilada',
                  'fire-stone': 'piedra_fuego', 'water-stone': 'piedra_agua', 'leaf-stone': 'piedra_hoja', 'ice-stone': 'piedra_hielo'}


def base(nombre, clave):
    return ((_oficiales.get(nombre) or {}).get('stats') or {}).get(clave) or 60


def stat(nombre, clave, nivel, iv=15, ev=0):
    """Stat real como en los juegos."""
    b = (2 * base(nombre, clave) + iv + ev // 4) * nivel / 100
    return math.floor(b + nivel + 10) if clave == 'hp' else math.floor(b + 5)


def _curva(nombre):
    return (_oficiales.get(nombre) or {}).get('crecimiento') or 'medium'


def xp_para(nombre, nivel):
    """Experiencia total para llegar a ese nivel segun la curva de crecimiento de la especie."""
    n = max(1, nivel)
    curva = _curva(nombre)
    if curva == 'fast': return round(4 * n ** 3 / 5)
    if curva == 'slow': return round(5 * n ** 3 / 4)
    if curva == 'medium-slow': return max(0, round(6 / 5 * n ** 3 - 15 * n ** 2 + 100 * n - 140))
    return n ** 3                                                # medium (y las raras van como medium)


def movs_iniciales(nombre):
    """None en cada casilla = usa el movimiento de la especie (si evoluciona, cambia solo). Una MT reemplaza la casilla."""
    return [None, None, None, None]


def nuevo(nombre, nivel=NIVEL_INICIAL, azar=random):
    """Un pokemon nuevo para el equipo con IVs al azar (0 a 31)."""
    return {'nombre': nombre, 'nivel': nivel, 'xp': xp_para(nombre, nivel), 'ivs': {s: azar.randint(0, 31) for s in STATS},
            'evs': {s: 0 for s in STATS}, 'puntos': 0, 'amistad': 0, 'movs': movs_iniciales(nombre)}


def multiplicadores(m):
    """Proporcion contra el pokemon de referencia. vida/fisico/especial crecen con el nivel; defensa y velocidad solo con IV y EV."""
    n, L, iv, ev = m['nombre'], m['nivel'], m['ivs'], m['evs']
    ref = lambda c: stat(n, c, NIVEL_REF)
    propio = lambda c: stat(n, c, L, iv[c], ev[c])
    neutro = lambda c: stat(n, c, L)
    defensa = (neutro('defense') + neutro('special-defense')) / max(1, propio('defense') + propio('special-defense'))
    return {'vida': propio('hp') / ref('hp'), 'fisico': propio('attack') / ref('attack'), 'especial': propio('special-attack') / ref('special-attack'),
            'defensa': defensa, 'velocidad': 1 + 0.5 * (propio('speed') / neutro('speed') - 1)}


def crecimiento(nombre, nivel, clave='hp'):
    """Lo mismo para enemigos (IV promedio, sin EV): cuanto mas nivel, mas vida y mas daño."""
    return stat(nombre, clave, nivel) / stat(nombre, clave, NIVEL_REF)


def xp_por_derrota(enemigo, nivel_enemigo, nivel_propio, jefe=False):
    """Formula de quinta generacion: se gana mas contra los de mas nivel y menos contra los debiles."""
    b = (_oficiales.get(enemigo) or {}).get('experiencia_base') or 60
    x = b * nivel_enemigo / 5 * ((2 * nivel_enemigo + 10) / (nivel_enemigo + nivel_propio + 10)) ** 2.5 + 1
    return max(1, round(x * XP_MULT * (3 if jefe else 1)))


def dar_xp(m, cantidad):
    """Suma experiencia. Devuelve los niveles nuevos (cada uno da puntos de EV)."""
    if m['nivel'] >= NIVEL_MAX: return []
    m['xp'] += max(0, round(cantidad))
    subidos = []
    while m['nivel'] < NIVEL_MAX and m['xp'] >= xp_para(m['nombre'], m['nivel'] + 1):
        m['nivel'] += 1; m['puntos'] += PUNTOS_POR_NIVEL; subidos.append(m['nivel'])
    return subidos


def progreso_nivel(m):
    """0 a 1: cuanto falta para el proximo nivel (para la barra de experiencia)."""
    a, b = xp_para(m['nombre'], m['nivel']), xp_para(m['nombre'], m['nivel'] + 1)
    return max(0.0, min(1.0, (m['xp'] - a) / max(1, b - a)))


def gastar_punto(m, clave):
    """Pone un punto de EV en ese stat (si hay puntos y no esta al tope)."""
    if m['puntos'] <= 0 or m['evs'][clave] >= EV_MAX_STAT or sum(m['evs'].values()) >= EV_MAX: return False
    m['evs'][clave] = min(EV_MAX_STAT, m['evs'][clave] + EV_POR_PUNTO)
    m['puntos'] -= 1
    return True


def _jugable(nombre):
    return nombre in pokemones and tiene_sprites(nombre)


def requisitos(nombre):
    """Como evoluciona cada especie: lista de {'a', 'nivel' | 'objeto' | 'amistad'} (solo a pokemon que estan en el juego)."""
    salida = []
    for ev in (_oficiales.get(nombre) or {}).get('evoluciones') or []:
        destino = ev['a'].replace('-', '_')
        if not _jugable(destino): continue
        req = dict(EVOLUCION_ESPECIAL.get(nombre, {}))
        if not req:
            if ev.get('disparador') == 'trade': req = {'objeto': 'cordon_union'}
            elif ev.get('objeto'): req = {'objeto': OBJETO_POKEAPI.get(ev['objeto'], ev['objeto'].replace('-', '_'))}
            elif ev.get('nivel'): req = {'nivel': ev['nivel']}
            else: req = {'nivel': 35}
        req['a'] = destino
        salida.append(req)
    return salida


def texto_requisito(req):
    if 'nivel' in req: return 'nivel ' + str(req['nivel'])
    if 'amistad' in req: return 'amistad ' + str(req['amistad'])
    return req['objeto'].replace('_', ' ')


def evoluciones(m, objetos=None):
    """A que puede evolucionar ahora: los de nivel/amistad si ya llego, los de objeto si lo tenes en la mochila."""
    objetos = objetos or {}
    listas = []
    for req in requisitos(m['nombre']):
        if 'nivel' in req and m['nivel'] >= req['nivel']: listas.append(req)
        elif 'amistad' in req and m['amistad'] >= req['amistad']: listas.append(req)
        elif 'objeto' in req and objetos.get(req['objeto'], 0) > 0: listas.append(req)
    return listas


def evolucionar(m, destino):
    """Cambia la especie y conserva nivel, IV, EV y las MT enseñadas."""
    m['nombre'] = destino
    m['xp'] = max(m['xp'], xp_para(destino, m['nivel']))         # otra curva: que no baje de nivel


def prob_unirse(enemigo, nivel_enemigo, nivel_propio, mult=1.0):
    """Chance de que un pokemon derrotado quiera unirse (no es capturar: se hace tu amigo). Mas facil si sos de mas nivel."""
    ratio = ((_oficiales.get(enemigo) or {}).get('ratio_captura') or 45) / 255
    ventaja = max(0.6, min(1.5, 1 + (nivel_propio - nivel_enemigo) * 0.05))
    return min(0.5, PROB_AMISTAD * ratio * ventaja * mult)


def nivel_de_sala(era, sala, tipo='combate'):
    """Nivel de los enemigos: 4 a 15 en la primera era, +11 por era. Jefes un poco mas."""
    if era >= 5: return {'tienda': 60, 'regi': 62, 'final': 66}.get(tipo, 60)
    base_ = 4 + 11 * era + round(sala * 11 / 30)
    return base_ + {'jefe': 3, 'regi': 5}.get(tipo, 0)


def vida_max(m):
    return max(1, round(datos_juego(m['nombre'])['max_vida'] * multiplicadores(m)['vida']))
