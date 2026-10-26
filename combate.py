"""
combate.py - Los pokemon peleando: como suben de nivel y como piensan los enemigos.

    progreso   niveles, experiencia, IV/EV, evoluciones y amistad
    ia         enemigos que te buscan, atacan avisando y se cubren; jefes

    from combate import progreso, ia
"""

import math
import random
from types import SimpleNamespace
import pygame
import datos
from datos import mundos
from sistema import animaciones
from mundo import entorno


# ==================== progreso ====================

def armar_progreso():
    """Niveles, experiencia, stats con IV y EV, evoluciones y amistad (pokemon que se unen a tu equipo).

        m = progreso.nuevo('electrike', 5)          # miembro nuevo: nivel, xp, IVs al azar, EVs en 0
        progreso.multiplicadores(m)                  # cuanto pegan, aguantan y corren segun nivel, IV y EV
        progreso.dar_xp(m, 120)                      # devuelve los niveles que subio
        progreso.evoluciones(m, objetos)             # a que puede evolucionar ahora (por nivel, piedra, amistad...)

    Las cuentas de stats son las de los juegos: stat = (2*base + IV + EV/4) * nivel/100 + 5 (PS: + nivel + 10).
    El juego usa la proporcion contra un pokemon de referencia (nivel 10, IV 15, EV 0), asi un nivel 10 normal juega igual que antes.
    """
    pokemones, _oficiales, datos_juego = datos.pokemones.pokemones, datos.pokemones._oficiales, datos.pokemones.datos_juego
    tiene_sprites = animaciones.tiene_sprites

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

    return SimpleNamespace(**locals())


progreso = armar_progreso()


# ==================== ia ====================

def armar_ia():
    """Inteligencia de los enemigos: te buscan esquivando obstaculos, atacan de cerca o de lejos y se cubren.

        ia.preparar(enemigo)                 # al crearlo: elige su estilo segun el rol del pokemon
        ia.actualizar(enemigo, ctx)          # cada frame
        ia.actualizar_jefe(jefe, ctx)        # jefes y Regis (Regigigas y Arceus tienen los suyos, ver GIGAS y ARCEUS)
        ia.dibujar_avisos(ventana, lista, cx, cy, ahora)   # los avisos antes de cada ataque

    Estilos (segun el rol del pokemon):
        'pegador'  tanque / atacante   va por el camino mas corto y te pega de cerca
        'tirador'  estratega           se queda a distancia, dispara si te ve, se aleja si te acercas y se esconde para recargar
        'rapido'   velocista           te da vueltas y se tira en embestida en linea recta
    Estados: 'patrulla' (no te vio) -> 'caza' (te vio, le pegaste o le avisaron: va a donde te vio por ultima vez).
    Todo ataque se avisa antes (anillo, linea o mira) y como mucho MAX_ATACANTES te pegan de cerca a la vez: dificil pero justo.
    """
    ROL_POKEMON = datos.pokemones.ROL_POKEMON

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

    # Regigigas: terremotos alrededor suyo y series de puñetazos grandes donde estas parado (todo avisado)
    GIGAS = {'vel': 1.5, 'terremoto': 6500, 'aviso_terremoto': 1100, 'radio_terremoto': 360, 'daño_terremoto': 1.1, 'temblor': 600,
             'puño': 3000, 'aviso_puño': 850, 'aviso_serie': 550, 'radio_puño': 95, 'daño_puño': 1.4, 'serie': 3}


    # Arceus: 3 fases (la barra de vida se parte en tercios)
    #   1  rayos normales que caen en cualquier lado y se abren en 4 balas, e Hiperrayo
    #   2  Multitipo (cambia de tipo con cada golpe que le das) y Sentencia del tipo que tenga (como los puñetazos de Regigigas pero mas grandes)
    #   3  todo junto, y cada Sentencia rompe el piso y deja un vacio
    ARCEUS = {'vel': 1.3, 'fases': (2 / 3, 1 / 3),
              'rayos': 2600, 'rayos_de_a': 3, 'aviso_rayo': 1000, 'radio_rayo': 55, 'daño_rayo': 0.8, 'daño_bala_rayo': 0.45, 'vel_bala_rayo': 6, 'dist_bala_rayo': 420,
              'hiperrayo': 5500, 'aviso_hiperrayo': 1000, 'largo_hiperrayo': 1300, 'ancho_hiperrayo': 34, 'daño_hiperrayo': 1.6, 'haz': 350,
              'sentencia': 3400, 'aviso_sentencia': 1000, 'aviso_serie': 650, 'radio_sentencia': 150, 'daño_sentencia': 1.3, 'serie': 3,
              'cambio_tipo': 450, 'radio_vacio': 45, 'max_vacios': 40, 'apurado_fase3': 0.8}
    TIPOS_ARCEUS = tuple(datos.pokemones.TABLA_TIPOS)

    # Arceus Beta: flota sobre el vacio de la mitad de arriba y va de un lado al otro (3 fases, por ahora todas como la primera)
    #   1  invoca las tablas de cada tipo; cada tabla da vueltas a su alrededor y tira ataques de su tipo, mas grandes que los normales
    BETA = {'tam': 300, 'ancho': 240, 'alto': 200, 'vaiven': 220, 'periodo': 2600,
            'tabla': 2200, 'max_tablas': 6, 'orbita': (300, 430), 'giro': 0.00035, 'ataque_tabla': (2600, 3800),
            'aviso_marca': 900, 'radio_marca': 95, 'daño_marca': 0.7, 'vel_bala': 5.5, 'dist_bala': 750, 'tam_bala': 30, 'daño_bala': 0.55, 'abanico': 0.35}
    TIPOS_TABLA = tuple(t for t in TIPOS_ARCEUS if t != 'normal')        # en los juegos no hay tabla de tipo normal
    FORMA_TABLA = {t: 'marca' for t in ('electrico', 'tierra', 'roca', 'psiquico', 'fantasma', 'hada', 'dragon')}   # cae donde estas
    FORMA_TABLA.update({t: 'abanico' for t in ('fuego', 'volador', 'veneno', 'bicho', 'lucha', 'siniestro')})        # 3 balas en abanico
    ESTILO_JEFE = {'regigigas': 'regigigas', 'arceus': 'arceus', 'arceus_beta': 'beta', 'regice': 'regice', 'regirock': 'regirock',
                   'registeel': 'registeel', 'regieleki': 'regieleki'}

    # Regice: rayo hielo largo que deja escarcha (resbala y congela al que la pisa) y muros de hielo que solo se derriten con fuego
    REGICE = {'vel': 1.2, 'rayo': 7000, 'aviso_rayo': 1100, 'largo_rayo': 1600, 'ancho_rayo': 26, 'daño_rayo': 1.3, 'haz': 400,
              'muro': 5000, 'bloques': 3, 'max_bloques': 12}
    # Regirock: roca afilada (fila de rocas que deja una roca al final) y desde la mitad de su vida fuerza bruta (se aturde si choca)
    REGIROCK = {'vel': 1.3, 'roca': 3200, 'aviso_roca': 600, 'paso_roca': 48, 'cada_roca': 55, 'radio_roca': 26, 'largo_roca': 20,
                'dura_roca': 700, 'daño_roca': 1.1, 'max_rocas': 8,
                'fuerza': 5000, 'aviso_fuerza': 900, 'largo_fuerza': 750, 'ancho_fuerza': 90, 'vel_fuerza': 15, 'daño_fuerza': 1.6, 'aturdido': 3000}
    # Registeel: minas que explotan en 8 balas, sierras que rebotan y un iman que te tira hacia el
    REGISTEEL = {'vel': 1.0, 'mina': 4200, 'minas_de_a': 3, 'espera_mina': 1300, 'radio_mina': 60, 'daño_mina': 1.0,
                 'daño_bala_mina': 0.5, 'vel_bala_mina': 6, 'dist_bala_mina': 450,
                 'sierra': 3600, 'sierras_de_a': 2, 'vel_sierra': 7, 'dura_sierra': 5000, 'radio_sierra': 20, 'daño_sierra': 0.9,
                 'iman': 12000, 'dura_iman': 5000, 'fuerza_iman': 2.4}
    # Regieleki: 5 rayos; al perder un cuarto de vida se mete en las torres; sin torres se teletransporta con alto voltaje
    REGIELEKI = {'vel': 2.6, 'rayos': 2600, 'aviso_rayos': 500, 'balas': 5, 'abanico': 0.6, 'vel_bala': 10, 'dist_bala': 700, 'daño_bala': 0.55,
                 'umbral': 0.75, 'torres': 6, 'radio_torres': 7, 'cambio': 3000, 'quedarse': 8000, 'vel_viaje': 22,
                 'linea': 2500, 'ancho_linea': 14, 'daño_linea': 0.5, 'tele': 2000, 'onda': 3000, 'radio_onda': 330, 'daño_onda': 1.1}
    COLOR_TORRE = {'gris': (130, 130, 130), 'cargada': (250, 220, 40), 'rota': (120, 75, 35)}


    def preparar_jefe(b):
        b.update({'aviso': None, 'prox_rafaga': 0, 'prox_pisoton': 0, 'resto_ia': [0.0, 0.0], 'estilo': ESTILO_JEFE.get(b['nombre'], 'jefe'),
                  'prox_terremoto': None, 'prox_puño': None, 'serie': 0,
                  'fase': 1, 'rayos': [], 'haz': None, 'prox_rayos': None, 'prox_hiperrayo': None, 'prox_sentencia': None, 'vida_tipo': b['vida'], 'prox_cambio': 0,
                  'tablas': [], 'marcas': [], 'n_tabla': 0, 'prox_tabla': None, 'inicio_beta': None, 'centro_beta': None,
                  'prox': {}, 'muros': [], 'filas_roca': [], 'circulos': [], 'dash': None, 'aturdido_hasta': 0, 'minas': [], 'sierras': [],
                  'iman_hasta': 0, 'iman_a': None, 'torres': None, 'torre': None, 'modo': 'libre', 'viaje': None, 'lineas': [], 'ondas': [],
                  'escondido': False, 'vida_guardada': b['vida'], 'prox_linea': 0})


    def actualizar_regigigas(b, ctx):
        """Camina lento hacia vos. Terremoto: anillo que se llena alrededor suyo (los voladores casi no lo sienten).
        Puñetazos: una mira grande donde estas, se cierra y golpea; vienen de a 3 seguidos."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        mitad = max(j['rect'].size) / 2
        if b['prox_terremoto'] is None: b['prox_terremoto'], b['prox_puño'] = ahora + GIGAS['terremoto'] // 2, ahora + 1500   # un respiro al entrar
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'terremoto':
                if dist <= GIGAS['radio_terremoto'] + mitad: ctx['dañar_jugador'](b['daño'] * GIGAS['daño_terremoto'], 'tierra')
                ctx['impacto'](bx, by, GIGAS['radio_terremoto'], GIGAS['temblor'])
            else:
                mx, my = a['mira']
                if math.hypot(jx - mx, jy - my) <= GIGAS['radio_puño'] + mitad: ctx['dañar_jugador'](b['daño'] * GIGAS['daño_puño'], 'normal')
                ctx['impacto'](mx, my, GIGAS['radio_puño'], 250)
                b['serie'] -= 1
                if b['serie'] > 0: b['aviso'] = {'hasta': ahora + GIGAS['aviso_serie'], 'clase': 'puño', 'inicio': ahora, 'mira': (jx, jy)}
                else: b['prox_puño'] = ahora + GIGAS['puño']          # la espera arranca cuando termina la serie
            return
        if ahora >= b['prox_terremoto'] and dist < GIGAS['radio_terremoto'] * 1.3:
            b['prox_terremoto'] = ahora + GIGAS['terremoto']
            b['aviso'] = {'hasta': ahora + GIGAS['aviso_terremoto'], 'clase': 'terremoto', 'inicio': ahora}; return
        if ahora >= b['prox_puño']:
            b['serie'] = GIGAS['serie']
            b['aviso'] = {'hasta': ahora + GIGAS['aviso_puño'], 'clase': 'puño', 'inicio': ahora, 'mira': (jx, jy)}; return
        if dist > 140: _ir_a(ent, b, (jx, jy), GIGAS['vel'], [])


    def _dist_segmento(p, a, b):
        ax, ay = a; bx, by = b
        largo = (bx - ax) ** 2 + (by - ay) ** 2 or 1
        k = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / largo))
        return math.hypot(p[0] - ax - k * (bx - ax), p[1] - ay - k * (by - ay))


    def fase_arceus(b):
        k = b['vida'] / max(1, b['max_vida'])
        return 1 if k > ARCEUS['fases'][0] else 2 if k > ARCEUS['fases'][1] else 3


    def _rayos_arceus(b, ctx, fase):
        """Rayos normales: se marcan en el piso, caen y se abren en 4 balas (arriba, abajo y a los costados)."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        mitad = max(j['rect'].size) / 2
        for r in b['rayos'][:]:
            if ahora < r['hasta']: continue
            b['rayos'].remove(r)
            x, y = r['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= ARCEUS['radio_rayo'] + mitad: ctx['dañar_jugador'](b['daño'] * ARCEUS['daño_rayo'], 'normal')
            ctx['impacto'](x, y, ARCEUS['radio_rayo'], 120)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ctx['disparar'](x, y, dx, dy, b['daño'] * ARCEUS['daño_bala_rayo'], 'normal', ARCEUS['vel_bala_rayo'], ARCEUS['dist_bala_rayo'])
        if fase == 2 or ahora < b['prox_rayos']: return
        b['prox_rayos'] = ahora + ARCEUS['rayos'] * (ARCEUS['apurado_fase3'] if fase == 3 else 1)
        for i in range(ARCEUS['rayos_de_a']):
            if i == 0: x, y = j['rect'].centerx + random.randint(-60, 60), j['rect'].centery + random.randint(-60, 60)   # uno siempre cerca tuyo
            else: x, y = entorno.punto_libre(ent, random); x += random.randint(-30, 30); y += random.randint(-30, 30)
            b['rayos'].append({'pos': (x, y), 'inicio': ahora, 'hasta': ahora + ARCEUS['aviso_rayo']})


    def actualizar_arceus(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        mitad = max(j['rect'].size) / 2
        if b['prox_rayos'] is None: b['prox_rayos'], b['prox_hiperrayo'], b['prox_sentencia'] = ahora + 1500, ahora + 4000, ahora + 1500
        fase = b['fase'] = fase_arceus(b)
        if fase >= 2 and b['vida'] < b['vida_tipo'] and ahora >= b['prox_cambio']:     # Multitipo: cada golpe le cambia el tipo (y sus debilidades)
            b['tipo'] = random.choice([t for t in TIPOS_ARCEUS if t != b['tipo']]); b['prox_cambio'] = ahora + ARCEUS['cambio_tipo']
        b['vida_tipo'] = b['vida']
        if b['haz'] and ahora >= b['haz']['hasta']: b['haz'] = None
        _rayos_arceus(b, ctx, fase)
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'hiperrayo':
                if _dist_segmento((jx, jy), (bx, by), a['fin']) <= ARCEUS['ancho_hiperrayo'] + mitad: ctx['dañar_jugador'](b['daño'] * ARCEUS['daño_hiperrayo'], 'normal')
                b['haz'] = {'desde': (bx, by), 'fin': a['fin'], 'hasta': ahora + ARCEUS['haz']}
                ctx['impacto'](bx, by, 60, 300)
                b['prox_hiperrayo'] = ahora + ARCEUS['hiperrayo'] * (ARCEUS['apurado_fase3'] if fase == 3 else 1)
            else:
                mx, my = a['mira']
                if math.hypot(jx - mx, jy - my) <= ARCEUS['radio_sentencia'] + mitad: ctx['dañar_jugador'](b['daño'] * ARCEUS['daño_sentencia'], a['tipo'])
                ctx['impacto'](mx, my, ARCEUS['radio_sentencia'], 350)
                if fase == 3: entorno.abrir_vacio(ent, mx, my, ARCEUS['radio_vacio'], ARCEUS['max_vacios'])
                b['serie'] -= 1
                if b['serie'] > 0: b['aviso'] = _aviso_sentencia(b, ahora, ARCEUS['aviso_serie'], (jx, jy), fase)
                else: b['prox_sentencia'] = ahora + ARCEUS['sentencia'] * (ARCEUS['apurado_fase3'] if fase == 3 else 1)
            return
        if fase != 2 and ahora >= b['prox_hiperrayo'] and ve(ent, (bx, by), (jx, jy)):
            n = dist or 1
            fin = (bx + (jx - bx) / n * ARCEUS['largo_hiperrayo'], by + (jy - by) / n * ARCEUS['largo_hiperrayo'])   # la direccion queda fija: se esquiva
            b['aviso'] = {'hasta': ahora + ARCEUS['aviso_hiperrayo'], 'clase': 'hiperrayo', 'inicio': ahora, 'fin': fin}; return
        if fase >= 2 and ahora >= b['prox_sentencia']:
            b['serie'] = ARCEUS['serie']
            b['aviso'] = _aviso_sentencia(b, ahora, ARCEUS['aviso_sentencia'], (jx, jy), fase); return
        if dist > 160: _ir_a(ent, b, (jx, jy), ARCEUS['vel'], [])


    def _aviso_sentencia(b, ahora, espera, mira, fase):
        return {'hasta': ahora + espera, 'clase': 'sentencia', 'inicio': ahora, 'mira': mira, 'tipo': b['tipo'], 'rompe': fase == 3}


    # ---------- Arceus Beta ----------

    def pos_tabla(b, t, ahora):
        ang = t['ang'] + (ahora - t['nace']) * BETA['giro']
        return b['rect'].centerx + math.cos(ang) * t['radio'], b['rect'].centery + math.sin(ang) * t['radio'] * 0.75


    def _ataque_tabla(b, t, ctx):
        """Cada tabla ataca con su tipo: marca donde estas, una bala grande o un abanico de 3."""
        j, ahora = ctx['jugador'], ctx['ahora']
        x, y = t['pos']
        jx, jy = j['rect'].center
        forma = FORMA_TABLA.get(t['tipo'], 'bala')
        if forma == 'marca':
            b['marcas'].append({'pos': (jx + random.randint(-40, 40), jy + random.randint(-40, 40)), 'tipo': t['tipo'], 'inicio': ahora, 'hasta': ahora + BETA['aviso_marca']})
            return
        base = math.atan2(jy - y, jx - x)
        angulos = (base - BETA['abanico'], base, base + BETA['abanico']) if forma == 'abanico' else (base,)
        for ang in angulos:
            ctx['disparar'](x, y, math.cos(ang), math.sin(ang), b['daño'] * BETA['daño_bala'], t['tipo'], BETA['vel_bala'], BETA['dist_bala'], BETA['tam_bala'])


    def actualizar_beta(b, ctx):
        j, ahora = ctx['jugador'], ctx['ahora']
        mitad = max(j['rect'].size) / 2
        if b['inicio_beta'] is None: b['inicio_beta'], b['centro_beta'], b['prox_tabla'] = ahora, b['rect'].center, ahora + 800
        b['fase'] = fase_arceus(b)
        b['rect'].centerx = round(b['centro_beta'][0] + math.sin((ahora - b['inicio_beta']) / BETA['periodo']) * BETA['vaiven'])
        if ahora >= b['prox_tabla']:                                # invoca la tabla del tipo que sigue (y la mas vieja se va)
            b['prox_tabla'] = ahora + BETA['tabla']
            tipo = TIPOS_TABLA[b['n_tabla'] % len(TIPOS_TABLA)]; b['n_tabla'] += 1
            b['tablas'].append({'tipo': tipo, 'ang': random.uniform(0, math.tau), 'radio': random.uniform(*BETA['orbita']), 'nace': ahora,
                                'prox': ahora + BETA['ataque_tabla'][0] // 2, 'pos': b['rect'].center})
            if len(b['tablas']) > BETA['max_tablas']: b['tablas'].pop(0)
        for t in b['tablas']:
            t['pos'] = pos_tabla(b, t, ahora)
            if ahora >= t['prox']: t['prox'] = ahora + random.randint(*BETA['ataque_tabla']); _ataque_tabla(b, t, ctx)
        for m in b['marcas'][:]:
            if ahora < m['hasta']: continue
            b['marcas'].remove(m)
            x, y = m['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= BETA['radio_marca'] + mitad: ctx['dañar_jugador'](b['daño'] * BETA['daño_marca'], m['tipo'])
            ctx['impacto'](x, y, BETA['radio_marca'], 150)


    # ---------- Regis ----------

    def _dir(desde, hacia):
        dx, dy = hacia[0] - desde[0], hacia[1] - desde[1]
        n = math.hypot(dx, dy) or 1
        return dx / n, dy / n


    def _muro_hielo(b, ctx):
        """Pared de 3 bloques de hielo entre Regice y vos, de costado."""
        ent, j = ctx['ent'], ctx['jugador']
        b['muros'] = [o for o in b['muros'] if o in ent['objetos']]
        if len(b['muros']) >= REGICE['max_bloques']: return
        (bx, by), (jx, jy) = b['rect'].center, j['rect'].center
        dx, dy = _dir((bx, by), (jx, jy))
        cx, cy = bx + (jx - bx) * 0.55, by + (jy - by) * 0.55
        for k in range(-(REGICE['bloques'] // 2), REGICE['bloques'] // 2 + 1):
            o = entorno.poner_objeto(ent, 'muro_de_hielo', (cx - dy * k * 64, cy + dx * k * 64), [j['rect'].inflate(30, 30), b['rect']])
            if o: b['muros'].append(o)


    def actualizar_regice(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        p = b['prox']
        if not p: p.update(rayo=ahora + 2500, muro=ahora + 1500)
        if b['haz'] and ahora >= b['haz']['hasta']: b['haz'] = None
        if ahora >= p['muro']: p['muro'] = ahora + REGICE['muro']; _muro_hielo(b, ctx)
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if _dist_segmento((jx, jy), (bx, by), a['fin']) <= REGICE['ancho_rayo'] + max(j['rect'].size) / 2: ctx['dañar_jugador'](b['daño'] * REGICE['daño_rayo'], 'hielo')
            b['haz'] = {'desde': (bx, by), 'fin': a['fin'], 'hasta': ahora + REGICE['haz'], 'ancho': REGICE['ancho_rayo'], 'color': ((120, 200, 255), (235, 250, 255))}
            entorno.congelar_linea(ent, (bx, by), a['fin'], REGICE['ancho_rayo'] * 1.6)
            return
        if ahora >= p['rayo']:
            p['rayo'] = ahora + REGICE['rayo']
            dx, dy = _dir((bx, by), (jx, jy))
            b['aviso'] = {'hasta': ahora + REGICE['aviso_rayo'], 'clase': 'rayo_hielo', 'inicio': ahora,
                          'fin': (bx + dx * REGICE['largo_rayo'], by + dy * REGICE['largo_rayo'])}; return
        if dist > 220: _ir_a(ent, b, (jx, jy), REGICE['vel'], [])


    def _poner_roca(b, ctx, puntos):
        ent, j = ctx['ent'], ctx['jugador']
        if sum(1 for o in ent['objetos'] if o.get('de_regi') and o['nombre'] == 'roca') >= REGIROCK['max_rocas']: return
        for punto in reversed(puntos[-3:]):
            if entorno.poner_objeto(ent, 'roca', punto, [j['rect'].inflate(10, 10), b['rect']]): ctx['impacto'](*punto, 30, 120); return


    def _avanzar_filas(b, ctx):
        """Roca afilada: las rocas van saliendo una detras de otra hasta chocar con algo; si no te pegaron, queda una roca al final."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        R = REGIROCK
        for fila in b['filas_roca'][:]:
            while ahora >= fila['prox']:
                fila['prox'] += R['cada_roca']; fila['paso'] += 1
                d = fila['inicio'] + fila['paso'] * R['paso_roca']
                punto = (fila['x'] + fila['dir'][0] * d, fila['y'] + fila['dir'][1] * d)
                r = pygame.Rect(0, 0, R['radio_roca'] * 2, R['radio_roca'] * 2); r.center = punto
                if r.collidelist(entorno.solidos_proyectil(ent)) != -1 or fila['paso'] > R['largo_roca']:
                    if fila['puntos']: _poner_roca(b, ctx, fila['puntos'])
                    b['filas_roca'].remove(fila); break
                b['circulos'].append({'pos': punto, 'inicio': ahora, 'hasta': ahora + R['dura_roca']})
                fila['puntos'].append(punto)
                if r.colliderect(j['rect']):
                    ctx['dañar_jugador'](b['daño'] * R['daño_roca'], 'roca'); b['filas_roca'].remove(fila); break
        b['circulos'] = [c for c in b['circulos'] if ahora < c['hasta']]


    def _dash_regirock(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        d = b['dash']
        paso = min(REGIROCK['vel_fuerza'], d['restante'])
        d['resto'][0] += d['dir'][0] * paso; d['resto'][1] += d['dir'][1] * paso
        px, py = int(d['resto'][0]), int(d['resto'][1])
        d['resto'][0] -= px; d['resto'][1] -= py
        quiero = b['rect'].move(px, py)
        golpeados = [o for o in ent['objetos'] if o['solido'] and quiero.colliderect(o['rect'])]
        entorno.mover(ent, b['rect'], px, py, [b['tipo']])
        d['restante'] -= paso
        if not d['pego'] and b['rect'].colliderect(j['rect']): ctx['dañar_jugador'](b['daño'] * REGIROCK['daño_fuerza'], 'lucha'); d['pego'] = True
        if (px or py) and b['rect'].topleft != quiero.topleft:            # choco contra una roca o una pared
            for o in golpeados:
                if o['vida'] is not None: entorno.romper(ent, o, 'lucha')
            b['dash'] = None; b['aturdido_hasta'] = ahora + REGIROCK['aturdido']
            ctx['impacto'](*b['rect'].center, 120, 500)
        elif d['restante'] <= 0: b['dash'] = None


    def actualizar_regirock(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        p = b['prox']
        if not p: p.update(roca=ahora + 1500, fuerza=ahora + 2500)
        _avanzar_filas(b, ctx)
        if ahora < b['aturdido_hasta']: return
        if b['dash']: _dash_regirock(b, ctx); return
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'fuerza_bruta': b['dash'] = {'dir': a['dir'], 'restante': REGIROCK['largo_fuerza'], 'pego': False, 'resto': [0.0, 0.0]}
            else: b['filas_roca'].append({'x': bx, 'y': by, 'dir': a['dir'], 'paso': 0, 'prox': ahora, 'puntos': [], 'inicio': max(b['rect'].size) / 2})
            return
        if b['vida'] <= b['max_vida'] / 2 and ahora >= p['fuerza']:
            p['fuerza'] = ahora + REGIROCK['fuerza']
            b['aviso'] = {'hasta': ahora + REGIROCK['aviso_fuerza'], 'clase': 'fuerza_bruta', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy))}; return
        if ahora >= p['roca']:
            p['roca'] = ahora + REGIROCK['roca']
            b['aviso'] = {'hasta': ahora + REGIROCK['aviso_roca'], 'clase': 'roca_afilada', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy))}; return
        if dist > 240: _ir_a(ent, b, (jx, jy), REGIROCK['vel'], [])


    def _actualizar_minas(b, ctx):
        j, ahora = ctx['jugador'], ctx['ahora']
        R = REGISTEEL
        for m in b['minas'][:]:
            if ahora < m['hasta']: continue
            b['minas'].remove(m)
            x, y = m['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_mina'] + max(j['rect'].size) / 2: ctx['dañar_jugador'](b['daño'] * R['daño_mina'], 'acero')
            ctx['impacto'](x, y, R['radio_mina'], 150)
            for i in range(8):
                ang = i * math.tau / 8
                ctx['disparar'](x, y, math.cos(ang), math.sin(ang), b['daño'] * R['daño_bala_mina'], 'acero', R['vel_bala_mina'], R['dist_bala_mina'])


    def _actualizar_sierras(b, ctx):
        """Las sierras rebotan en las paredes hasta que se les acaba el tiempo o te pegan."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        R = REGISTEEL
        duros = entorno.solidos_proyectil(ent)
        for s in b['sierras'][:]:
            r = pygame.Rect(0, 0, R['radio_sierra'] * 2, R['radio_sierra'] * 2)
            for i in (0, 1):
                nuevo = [s['x'], s['y']]; nuevo[i] += s['v'][i]
                r.center = nuevo
                if r.collidelist(duros) != -1: s['v'][i] = -s['v'][i]
                else: s['x'], s['y'] = nuevo
            r.center = (s['x'], s['y'])
            if r.colliderect(j['rect']): ctx['dañar_jugador'](b['daño'] * R['daño_sierra'], 'acero'); b['sierras'].remove(s)
            elif ahora >= s['hasta']: b['sierras'].remove(s)


    def actualizar_registeel(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        R, p = REGISTEEL, b['prox']
        if not p: p.update(mina=ahora + 1500, sierra=ahora + 2500, iman=ahora + 7000)
        _actualizar_minas(b, ctx)
        _actualizar_sierras(b, ctx)
        if ahora < b['iman_hasta']:                                 # iman: se queda quieto y te tira hacia el
            b['iman_a'] = (jx, jy)
            dx, dy = _dir((jx, jy), (bx, by))
            resto = j.setdefault('resto_iman', [0.0, 0.0])
            resto[0] += dx * R['fuerza_iman']; resto[1] += dy * R['fuerza_iman']
            px, py = int(resto[0]), int(resto[1])
            resto[0] -= px; resto[1] -= py
            entorno.mover(ent, j['rect'], px, py, j['tipos'])
            return
        b['iman_a'] = None
        if ahora >= p['iman']:
            p['iman'] = ahora + R['iman']; b['iman_hasta'] = ahora + R['dura_iman']; return
        if ahora >= p['mina']:
            p['mina'] = ahora + R['mina']
            for i in range(R['minas_de_a']):
                pos = (jx, jy) if i == 0 else (jx + random.randint(-220, 220), jy + random.randint(-220, 220))
                b['minas'].append({'pos': pos, 'inicio': ahora, 'hasta': ahora + R['espera_mina'] + i * 150})
        if ahora >= p['sierra']:
            p['sierra'] = ahora + R['sierra']
            base = math.atan2(jy - by, jx - bx)
            for i in range(R['sierras_de_a']):
                ang = base + (i - (R['sierras_de_a'] - 1) / 2) * 0.5
                b['sierras'].append({'x': float(bx), 'y': float(by), 'v': [math.cos(ang) * R['vel_sierra'], math.sin(ang) * R['vel_sierra']], 'hasta': ahora + R['dura_sierra']})
        if dist > 260: _ir_a(ent, b, (jx, jy), R['vel'], [])


    def _crear_torres(b, ctx):
        ent, j = ctx['ent'], ctx['jugador']
        sala, tam = ent['sala'], ent['tam']
        cx, cy = sala['columnas'] * tam / 2, sala['filas'] * tam / 2
        b['torres'] = []
        for i in range(REGIELEKI['torres']):
            ang = i * math.tau / REGIELEKI['torres']
            punto = (cx + math.cos(ang) * REGIELEKI['radio_torres'] * tam, cy + math.sin(ang) * REGIELEKI['radio_torres'] * tam)
            o = entorno.poner_objeto(ent, 'torre_electrica', punto, [j['rect'], b['rect']])
            if o: o['color'] = COLOR_TORRE['gris']; b['torres'].append({'obj': o, 'estado': 'gris', 'entro': 0, 'atacada': False})


    def _rayos5(b, ctx):
        j, R = ctx['jugador'], REGIELEKI
        bx, by = b['rect'].center
        base = math.atan2(j['rect'].centery - by, j['rect'].centerx - bx)
        for i in range(R['balas']):
            ang = base + (i - (R['balas'] - 1) / 2) * R['abanico'] / 2
            ctx['disparar'](bx + math.cos(ang) * 60, by + math.sin(ang) * 60, math.cos(ang), math.sin(ang), b['daño'] * R['daño_bala'], 'electrico', R['vel_bala'], R['dist_bala'])


    def _ir_a_torre(b, ctx, torre):
        ahora = ctx['ahora']
        desde = b['rect'].center
        b['modo'], b['viaje'], b['escondido'] = 'viaje', torre, False
        b['lineas'].append({'a': desde, 'b': torre['obj']['rect'].center, 'hasta': ahora + REGIELEKI['linea']})


    def _salir_de_torre(b, ctx):
        t = b['torre']
        t['estado'] = 'rota' if t['atacada'] else 'gris'
        t['obj']['color'] = COLOR_TORRE[t['estado']]
        libres = [o for o in b['torres'] if o['estado'] == 'gris' and o is not t]
        if not libres:
            if not t['atacada']: t['estado'] = 'cargada'; t['obj']['color'] = COLOR_TORRE['cargada']; t['entro'] = ctx['ahora']; return
            b['torre'], b['modo'], b['escondido'] = None, 'tele', False
            b['prox']['tele'] = ctx['ahora']
            return
        b['torre'] = None
        _ir_a_torre(b, ctx, random.choice(libres))


    def actualizar_regieleki(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        mitad = max(j['rect'].size) / 2
        R, p = REGIELEKI, b['prox']
        if b['torres'] is None: _crear_torres(b, ctx)
        if not p: p.update(rayos=ahora + 1500)
        if b['modo'] in ('viaje', 'torre'): b['vida'] = b['vida_guardada']          # adentro de las torres no se le puede pegar
        for t in b['torres']:                                       # pegarle a la torre donde esta le pega a el
            o = t['obj']
            daño = o['max_vida'] - o['vida']
            if daño > 0 and t is b['torre'] and b['modo'] == 'torre': b['vida'] -= daño; t['atacada'] = True
            o['vida'] = o['max_vida']
        b['lineas'] = [l for l in b['lineas'] if ahora < l['hasta']]
        if ahora >= b['prox_linea'] and any(_dist_segmento((jx, jy), l['a'], l['b']) <= R['ancho_linea'] + mitad for l in b['lineas']):
            ctx['dañar_jugador'](b['daño'] * R['daño_linea'], 'electrico'); b['prox_linea'] = ahora + 500
        for o in b['ondas'][:]:
            if ahora >= o['hasta']: b['ondas'].remove(o); continue
            radio = R['radio_onda'] * (ahora - o['inicio']) / R['onda']
            if not o['pego'] and abs(math.hypot(jx - o['pos'][0], jy - o['pos'][1]) - radio) <= 22 + mitad:
                ctx['dañar_jugador'](b['daño'] * R['daño_onda'], 'electrico'); o['pego'] = True
        a = b['aviso']
        if a and ahora >= a['hasta']: b['aviso'] = None; _rayos5(b, ctx)
        if b['modo'] == 'libre':
            if b['vida'] <= b['max_vida'] * R['umbral'] and any(t['estado'] == 'gris' for t in b['torres']):
                b['aviso'] = None
                _ir_a_torre(b, ctx, random.choice([t for t in b['torres'] if t['estado'] == 'gris']))
            elif not b['aviso']:
                if ahora >= p['rayos']:
                    p['rayos'] = ahora + R['rayos']
                    b['aviso'] = {'hasta': ahora + R['aviso_rayos'], 'clase': 'rafaga', 'inicio': ahora, 'mira': (jx, jy)}
                elif math.hypot(jx - bx, jy - by) > 280: _ir_a(ent, b, (jx, jy), R['vel'], [])
        elif b['modo'] == 'viaje':
            tx, ty = b['viaje']['obj']['rect'].center
            d = math.hypot(tx - bx, ty - by)
            if d <= R['vel_viaje']:
                b['rect'].center = (tx, ty)
                t = b['torre'] = b['viaje']
                t.update(estado='cargada', entro=ahora, atacada=False); t['obj']['color'] = COLOR_TORRE['cargada']
                b['modo'], b['viaje'], b['escondido'] = 'torre', None, True
                b['aviso'] = {'hasta': ahora + R['aviso_rayos'], 'clase': 'rafaga', 'inicio': ahora, 'mira': (jx, jy)}
            else: b['rect'].center = (round(bx + (tx - bx) / d * R['vel_viaje']), round(by + (ty - by) / d * R['vel_viaje']))
        elif b['modo'] == 'torre':
            t = b['torre']
            if (t['atacada'] and ahora - t['entro'] >= R['cambio']) or ahora - t['entro'] >= R['quedarse']: _salir_de_torre(b, ctx)
        elif ahora >= p['tele']:                                    # sin torres: se teletransporta con alto voltaje
            p['tele'] = ahora + R['tele']
            b['rect'].center = entorno.punto_libre(ent, random, (jx, jy), 220)
            b['ondas'].append({'pos': b['rect'].center, 'inicio': ahora, 'hasta': ahora + R['onda'], 'pego': False})
            ctx['impacto'](*b['rect'].center, 60, 150)
        b['vida_guardada'] = b['vida']


    def actualizar_jefe(b, ctx):
        """Te sigue por el mapa de flujo, tira rafagas en abanico apuntadas y si estas cerca pisotea (todo avisado)."""
        if b['estilo'] == 'regigigas': actualizar_regigigas(b, ctx); return
        if b['estilo'] == 'beta': actualizar_beta(b, ctx); return
        if b['estilo'] == 'arceus': actualizar_arceus(b, ctx); return
        if b['estilo'] == 'regice': actualizar_regice(b, ctx); return
        if b['estilo'] == 'regirock': actualizar_regirock(b, ctx); return
        if b['estilo'] == 'registeel': actualizar_registeel(b, ctx); return
        if b['estilo'] == 'regieleki': actualizar_regieleki(b, ctx); return
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

    def dibujar_sello(ventana, centro, radio, color, k=1.0, ahora=0):
        """El sello de la Sentencia: circulo grande, triangulo con un circulo en cada punta, circulo interior y anillos de circulitos.
        Gira despacio y se va llenando con k (0 a 1) hasta que cae."""
        x, y = centro
        g = 2 if k < 0.9 else 3
        punto = lambda ang, d: (x + math.cos(ang) * d, y + math.sin(ang) * d)
        rot = ahora / 3000 - math.pi / 2
        pygame.draw.circle(ventana, color, centro, radio, g + 1)
        pygame.draw.circle(ventana, color, centro, round(radio * 0.66), g)
        pygame.draw.circle(ventana, color, centro, round(radio * 0.5), g)
        vertices = [punto(rot + i * math.tau / 3, radio) for i in range(3)]
        pygame.draw.polygon(ventana, color, vertices, g)
        for i in range(12):                                         # circulitos entre el circulo de afuera y el del medio
            ang = rot + math.pi / 6 + i * math.tau / 12
            if i % 4: pygame.draw.circle(ventana, color, punto(ang, radio * 0.83), max(2, round(radio * 0.05)), 2)
        for i in range(9):                                          # circulitos sobre el circulo interior
            pygame.draw.circle(ventana, color, punto(rot + math.pi / 3 + i * math.tau / 9, radio * 0.58), max(2, round(radio * 0.035)), 2)
        for i in range(4):                                          # los cuatro circulos entrelazados del centro
            pygame.draw.circle(ventana, color, punto(rot + i * math.tau / 4, radio * 0.09), round(radio * 0.13), 2)
        for vx, vy in vertices:                                     # circulo en cada punta con rayos y circulitos adentro
            r = radio * 0.24
            pygame.draw.circle(ventana, (15, 10, 20), (vx, vy), round(r))
            pygame.draw.circle(ventana, color, (vx, vy), round(r), g)
            pygame.draw.circle(ventana, color, (vx, vy), round(r * 0.25), 2)
            for i in range(6):
                ang = -rot + i * math.tau / 6
                pygame.draw.line(ventana, color, (vx + math.cos(ang) * r * 0.25, vy + math.sin(ang) * r * 0.25), (vx + math.cos(ang) * r, vy + math.sin(ang) * r), 1)
                pygame.draw.circle(ventana, color, (vx + math.cos(ang + 0.5) * r * 0.62, vy + math.sin(ang + 0.5) * r * 0.62), max(2, round(r * 0.14)), 1)
        if k > 0: pygame.draw.circle(ventana, color, centro, max(1, round(radio * k)), 0 if k > 0.95 else 3)


    def dibujar_avisos(ventana, lista, cx, cy, ahora, fuente=None, colores=None):
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
                elif a['clase'] == 'terremoto':                     # anillo marron que se llena y grietas que salen del jefe
                    radio = GIGAS['radio_terremoto']
                    pygame.draw.circle(ventana, (170, 110, 50), (x, y), radio, 3)
                    pygame.draw.circle(ventana, (200, 130, 60), (x, y), max(1, round(radio * k)), 4)
                    for i in range(8):
                        ang = i * math.tau / 8 + 0.3
                        largo = radio * k
                        medio = (x + math.cos(ang + 0.15) * largo * 0.5, y + math.sin(ang + 0.15) * largo * 0.5)
                        pygame.draw.lines(ventana, (90, 60, 30), False, [(x, y), medio, (x + math.cos(ang) * largo, y + math.sin(ang) * largo)], 3)
                elif a['clase'] == 'puño':                          # mira grande donde va a caer el puño
                    mx, my = round(a['mira'][0] - cx), round(a['mira'][1] - cy)
                    radio = GIGAS['radio_puño']
                    pygame.draw.circle(ventana, (255, 60, 40), (mx, my), radio, 3)
                    pygame.draw.circle(ventana, (255, 60, 40), (mx, my), max(1, round(radio * k)), 0 if k > 0.95 else 2)
                    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        pygame.draw.line(ventana, (255, 60, 40), (mx + ox * radio * 0.6, my + oy * radio * 0.6), (mx + ox * radio * 1.2, my + oy * radio * 1.2), 3)
                elif a['clase'] == 'hiperrayo':                     # linea fija hacia donde va a salir el rayo, cada vez mas gruesa
                    fx, fy = a['fin'][0] - cx, a['fin'][1] - cy
                    pygame.draw.line(ventana, (255, 240, 180), (x, y), (fx, fy), 2 + round(ARCEUS['ancho_hiperrayo'] * k * 0.6))
                    pygame.draw.line(ventana, (255, 90, 40), (x, y), (fx, fy), 2)
                elif a['clase'] == 'rayo_hielo':                    # linea celeste fija que se va engrosando
                    fx, fy = a['fin'][0] - cx, a['fin'][1] - cy
                    pygame.draw.line(ventana, (200, 240, 255), (x, y), (fx, fy), 2 + round(REGICE['ancho_rayo'] * k * 0.8))
                    pygame.draw.line(ventana, (60, 140, 230), (x, y), (fx, fy), 2)
                elif a['clase'] == 'roca_afilada':                  # por donde van a salir las rocas
                    for i in range(1, REGIROCK['largo_roca'] + 1, 2):
                        d = max(e['rect'].size) / 2 + i * REGIROCK['paso_roca']
                        pygame.draw.circle(ventana, (150, 110, 60), (round(x + a['dir'][0] * d), round(y + a['dir'][1] * d)), 6, 2)
                elif a['clase'] == 'fuerza_bruta':                  # franja roja por donde va a embestir
                    W, H = ventana.get_size()
                    velo = pygame.Surface((W, H), pygame.SRCALPHA)
                    fin = (x + a['dir'][0] * REGIROCK['largo_fuerza'], y + a['dir'][1] * REGIROCK['largo_fuerza'])
                    pygame.draw.line(velo, (230, 30, 30, 70 + round(90 * k)), (x, y), fin, REGIROCK['ancho_fuerza'])
                    ventana.blit(velo, (0, 0))
                    pygame.draw.line(ventana, (255, 60, 40), (x, y), fin, 2)
                elif a['clase'] == 'sentencia':                     # el sello de Arceus del color de su tipo
                    centro = (round(a['mira'][0] - cx), round(a['mira'][1] - cy))
                    dibujar_sello(ventana, centro, ARCEUS['radio_sentencia'], (colores or {}).get(a['tipo'], (255, 255, 255)), k, ahora)
                    if a.get('rompe'): pygame.draw.circle(ventana, (40, 10, 60), centro, max(1, round(ARCEUS['radio_vacio'] * k)), 4)
            for r in e.get('rayos', ()):                            # rayos de Arceus: marca en el piso y una linea que baja del cielo
                k = min(1.0, (ahora - r['inicio']) / max(1, r['hasta'] - r['inicio']))
                rx, ry = round(r['pos'][0] - cx), round(r['pos'][1] - cy)
                pygame.draw.circle(ventana, (255, 250, 200), (rx, ry), ARCEUS['radio_rayo'], 2)
                pygame.draw.circle(ventana, (255, 250, 200), (rx, ry), max(1, round(ARCEUS['radio_rayo'] * k)), 0 if k > 0.95 else 2)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # hacia donde salen las 4 balas
                    pygame.draw.line(ventana, (230, 220, 160), (rx + dx * ARCEUS['radio_rayo'], ry + dy * ARCEUS['radio_rayo']), (rx + dx * (ARCEUS['radio_rayo'] + 18), ry + dy * (ARCEUS['radio_rayo'] + 18)), 2)
                if k > 0.6: pygame.draw.line(ventana, (255, 255, 230), (rx, ry - 500), (rx, ry), round(2 + 6 * (k - 0.6) / 0.4))
            haz = e.get('haz')
            if haz:
                a0, a1 = (haz['desde'][0] - cx, haz['desde'][1] - cy), (haz['fin'][0] - cx, haz['fin'][1] - cy)
                ancho = haz.get('ancho', ARCEUS['ancho_hiperrayo'])
                afuera, adentro = haz.get('color', ((255, 200, 80), (255, 255, 240)))
                pygame.draw.line(ventana, afuera, a0, a1, ancho * 2)
                pygame.draw.line(ventana, adentro, a0, a1, ancho)
            for c in e.get('circulos', ()):                         # roca afilada
                k = min(1.0, (ahora - c['inicio']) / 120)
                pos = (round(c['pos'][0] - cx), round(c['pos'][1] - cy))
                pygame.draw.circle(ventana, (140, 115, 80), pos, max(2, round(REGIROCK['radio_roca'] * k)))
                pygame.draw.circle(ventana, (60, 45, 30), pos, max(2, round(REGIROCK['radio_roca'] * k)), 3)
            for m in e.get('minas', ()):                            # minas de Registeel: titilan mas rapido antes de explotar
                k = min(1.0, (ahora - m['inicio']) / max(1, m['hasta'] - m['inicio']))
                pos = (round(m['pos'][0] - cx), round(m['pos'][1] - cy))
                pygame.draw.circle(ventana, (255, 60, 40), pos, REGISTEEL['radio_mina'], 1)
                pygame.draw.circle(ventana, (255, 60, 40), pos, max(1, round(REGISTEEL['radio_mina'] * k)), 2)
                pygame.draw.circle(ventana, (70, 70, 80), pos, 14)
                pygame.draw.circle(ventana, (255, 40, 30) if (ahora // max(40, round(250 * (1 - k)))) % 2 else (90, 20, 20), pos, 6)
            for s in e.get('sierras', ()):                          # sierras que giran
                pos = (round(s['x'] - cx), round(s['y'] - cy))
                rs = REGISTEEL['radio_sierra']
                pygame.draw.circle(ventana, (190, 190, 205), pos, rs)
                for i in range(8):
                    ang = ahora / 60 + i * math.tau / 8
                    pygame.draw.line(ventana, (90, 90, 100), (pos[0] + math.cos(ang) * rs * 0.5, pos[1] + math.sin(ang) * rs * 0.5),
                                     (pos[0] + math.cos(ang) * (rs + 6), pos[1] + math.sin(ang) * (rs + 6)), 3)
                pygame.draw.circle(ventana, (60, 60, 70), pos, 5)
            if e.get('iman_a') and e.get('iman_hasta', 0) > ahora:   # iman: lineas que te tiran hacia Registeel
                ix, iy = e['iman_a'][0] - cx, e['iman_a'][1] - cy
                for i in range(3):
                    k = ((ahora / 400) + i / 3) % 1
                    pygame.draw.circle(ventana, (170, 120, 255), (round(ix + (x - ix) * k), round(iy + (y - iy) * k)), 6, 2)
                pygame.draw.circle(ventana, (170, 120, 255), (x, y), round(max(e['rect'].size) / 2 + 20 + math.sin(ahora / 100) * 8), 3)
            for l in e.get('lineas', ()):                           # camino de Regieleki entre torres
                pygame.draw.line(ventana, (255, 240, 80), (l['a'][0] - cx, l['a'][1] - cy), (l['b'][0] - cx, l['b'][1] - cy), REGIELEKI['ancho_linea'])
                pygame.draw.line(ventana, (255, 255, 220), (l['a'][0] - cx, l['a'][1] - cy), (l['b'][0] - cx, l['b'][1] - cy), 3)
            for o in e.get('ondas', ()):                            # alto voltaje
                radio = round(REGIELEKI['radio_onda'] * (ahora - o['inicio']) / REGIELEKI['onda'])
                if radio > 2:
                    pygame.draw.circle(ventana, (255, 230, 50), (round(o['pos'][0] - cx), round(o['pos'][1] - cy)), radio, 6)
                    pygame.draw.circle(ventana, (255, 255, 200), (round(o['pos'][0] - cx), round(o['pos'][1] - cy)), radio, 2)
            if e.get('aturdido_hasta', 0) > ahora:                  # aturdido: estrellitas arriba de la cabeza
                for i in range(3):
                    ang = ahora / 200 + i * math.tau / 3
                    sx, sy = x + math.cos(ang) * 40, e['rect'].top - cy - 12 + math.sin(ang) * 10
                    pygame.draw.line(ventana, (255, 230, 60), (sx - 7, sy), (sx + 7, sy), 3)
                    pygame.draw.line(ventana, (255, 230, 60), (sx, sy - 7), (sx, sy + 7), 3)
            for m in e.get('marcas', ()):                           # ataques de las tablas que caen donde estas
                k = min(1.0, (ahora - m['inicio']) / max(1, m['hasta'] - m['inicio']))
                color = (colores or {}).get(m['tipo'], (255, 255, 255))
                mx, my = round(m['pos'][0] - cx), round(m['pos'][1] - cy)
                pygame.draw.circle(ventana, color, (mx, my), BETA['radio_marca'], 3)
                pygame.draw.circle(ventana, color, (mx, my), max(1, round(BETA['radio_marca'] * k)), 0 if k > 0.95 else 2)
            for t in e.get('tablas', ()):                           # las tablas: placa del color del tipo que brilla antes de atacar
                color = (colores or {}).get(t['tipo'], (255, 255, 255))
                placa = pygame.Rect(0, 0, 30, 42); placa.center = (round(t['pos'][0] - cx), round(t['pos'][1] - cy + math.sin(ahora / 300 + t['ang']) * 6))
                pygame.draw.rect(ventana, color, placa, border_radius=5)
                pygame.draw.rect(ventana, (255, 255, 255) if t['prox'] - ahora < 400 else (20, 20, 20), placa, 3, border_radius=5)
                pygame.draw.circle(ventana, (255, 255, 255), placa.center, 7, 2)
            if e.get('grito', 0) > ahora and fuente:
                t = fuente.render('!', True, (255, 230, 40))
                ventana.blit(t, t.get_rect(midbottom=(x, e['rect'].top - cy - 10)))

    return SimpleNamespace(**locals())


ia = armar_ia()
