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
from mundo import entorno, generacion


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
    EV_POR_PUNTO, EV_MAX_STAT, EV_MAX = 10, 300, 900      # cada punto que te dan al subir de nivel son 10 EV; hasta 300 por stat (30 puntos) y 900 en total
    PUNTOS_POR_NIVEL = 1
    XP_MULT = 0.6                      # que tan rapido se sube (antes 0.22 y despues 0.4: jugando sin trucos te quedabas abajo de los enemigos)
    PARTE_BANCA = 0.75                 # los de la banca ganan 3/4 de la experiencia (asi no quedan atras)
    USO_STAT = {'hp': 'vida maxima', 'attack': 'daño de golpes y embestidas', 'defense': 'aguante (junto con Def. Esp.)',
                'special-attack': 'daño de disparos, ondas y asistencias', 'special-defense': 'aguante (junto con Defensa)', 'speed': 'velocidad al moverte'}
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
        """Stat base oficial de la especie (de la PokeAPI), o 60 si no hay datos."""
        return ((_oficiales.get(nombre) or {}).get('stats') or {}).get(clave) or 60


    def stat(nombre, clave, nivel, iv=15, ev=0):
        """Stat real como en los juegos."""
        b = (2 * base(nombre, clave) + iv + ev // 4) * nivel / 100
        return math.floor(b + nivel + 10) if clave == 'hp' else math.floor(b + 5)


    def _curva(nombre):
        """Curva de crecimiento de la especie (de la PokeAPI; 'medium' si no hay datos)."""
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
                'evs': {s: 0 for s in STATS}, 'puntos': 0, 'amistad': 0, 'movs': movs_iniciales(nombre),
                'items': [], 'sinergia': None}                 # objetos equipados (hasta 2) y la pasiva que eligio el jugador (None = la de su rol)


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


    def motivo_sin_ev(m, clave):
        """Por que no se puede poner un punto en ese stat (texto para mostrar) o None si se puede."""
        if m['puntos'] <= 0: return 'No tenes puntos: ganas 1 por cada nivel que sube'
        if m['evs'][clave] >= EV_MAX_STAT: return NOMBRE_STAT[clave] + ' ya esta al maximo (' + str(EV_MAX_STAT) + ' EV)'
        if sum(m['evs'].values()) >= EV_MAX: return 'Llegaste al maximo de EV en total (' + str(EV_MAX) + ')'
        return None


    def gastar_punto(m, clave):
        """Pone un punto de EV en ese stat (si hay puntos y no esta al tope)."""
        if motivo_sin_ev(m, clave): return False
        m['evs'][clave] = min(EV_MAX_STAT, m['evs'][clave] + EV_POR_PUNTO)
        m['puntos'] -= 1
        return True


    def _jugable(nombre):
        """Si el pokemon existe en el juego y tiene sprites (asi se puede evolucionar a el)."""
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
        """Texto de un requisito de evolucion ('nivel 16', 'amistad 220', 'piedra trueno')."""
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
        """Vida maxima de un miembro: la de su especie por el multiplicador de nivel, IV y EV."""
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
        """Cuantos enemigos de cuerpo a cuerpo estan atacando o embistiendo ahora (para que no ataquen todos a la vez)."""
        return sum(1 for o in enemigos if o['vida'] > 0 and o.get('estilo') in ('pegador', 'rapido') and (o.get('aviso') or o.get('embestida_ia')))


    def actualizar(e, ctx):
        """
        ctx = {'ent': entorno, 'jugador': j, 'enemigos': [...], 'ahora': ms, 'dañar_jugador': f(daño, tipo),
               'disparar': f(x, y, dx, dy, daño, tipo, vel, distancia), 'parry': f(enemigo) -> True si el jugador bloqueo su golpe}
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
                em['pego'] = True
                if ctx.get('parry', lambda e: False)(e): return              # te choco justo cuando golpeabas: parry
                ctx['dañar_jugador'](e['daño'] * 1.3, e['tipo'])
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
            e['cd_ataque'] = ahora + p['cd']
            if math.hypot(jx - ex, jy - ey) <= (p['alcance'] + max(j['rect'].size) / 2) * 1.25:
                if not ctx.get('parry', lambda e: False)(e): ctx['dañar_jugador'](e['daño'], e['tipo'])   # salvo que le hagas parry
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
             'puño': 3000, 'aviso_puño': 850, 'aviso_serie': 550, 'radio_puño': 95, 'daño_puño': 1.4, 'serie': 3,
             'lento': 10000, 'def_lento': 0.3,                       # Lento Inicio: 10 s quieto y con la defensa subida
             'giga': 7500, 'aviso_giga': 900, 'vel_giga': 17, 'largo_giga': 900, 'ancho_giga': 170, 'daño_giga': 2.0, 'recarga_giga': 1200,
             'proteccion': 12000, 'dura_proteccion': 3000, 'daño_para_proteger': 0.05,
             'agarre': 6500, 'aviso_agarre': 500, 'radio_agarre': 140, 'sostener': 600, 'vel_lanzar': 20, 'daño_lanzar': 1.6, 'vuelo_max': 1500}


    # Arceus: 3 fases (100-65%, 65-20% y 20-0%). Usa un movimiento por vez, elegido al azar entre los de su fase (MOVS_ARCEUS):
    #   Hiperrayo           rayo del ancho de Arceus que sale de el y va siguiendo por donde estabas; despues recarga 3 s quieto
    #   Velocidad Extrema   embiste rapidisimo hacia vos; si choca contra una pared NO queda aturdido
    #   Vozarron            salen de el 3 circulos que se van agrandando durante 5 s
    #   Meteoros            caen 7 meteoritos rapidos donde estas, cada uno avisado 1 s antes
    #   Sentencia           el sello cae del cielo, de tipo normal: chica en la fase 2 y grande en la 3
    #   Proteccion          escudo 3 s: quieto, sin atacar y sin recibir daño
    #   Recuperacion        3 s quieto juntando estrellitas sin atacar; si le pegas se corta, si no se cura un poco
    #   Recuperacion, Velocidad Extrema e Hiperrayo nunca van juntos: entre uno y otro de esos tres pasa 'pausa_exclusivos'
    MOVS_ARCEUS = {1: ('hiperrayo', 'velocidad_extrema', 'vozarron', 'meteoros'),
                   2: ('sentencia', 'hiperrayo', 'vozarron', 'meteoros'),
                   3: ('hiperrayo', 'velocidad_extrema', 'vozarron', 'meteoros', 'sentencia', 'proteccion', 'recuperacion')}
    EXCLUSIVOS_ARCEUS = ('recuperacion', 'velocidad_extrema', 'hiperrayo')
    ARCEUS = {'vel': 1.3, 'fases': (0.65, 0.20), 'primer_mov': 1500, 'pausa': (700, 1300), 'pausa_exclusivos': 2500,
              'espera': {'hiperrayo': 9000, 'velocidad_extrema': 5000, 'vozarron': 8000, 'meteoros': 7000, 'sentencia': 5500,     # cada cuanto puede repetir cada uno
                         'proteccion': 12000, 'recuperacion': 16000},
              'aviso_hiperrayo': 900, 'dura_hiperrayo': 2200, 'retraso_hiperrayo': 450, 'giro_hiperrayo': 0.025, 'largo_hiperrayo': 1600,
              'tick_hiperrayo': 400, 'daño_hiperrayo': 0.55, 'recarga_hiperrayo': 3000,
              'aviso_extrema': 450, 'vel_extrema': 24, 'largo_extrema': 950, 'daño_extrema': 1.3,
              'aviso_vozarron': 600, 'circulos': 3, 'entre_circulos': 550, 'dura_vozarron': 5000, 'radio_vozarron': 760, 'grosor_vozarron': 22, 'daño_vozarron': 0.9,
              'meteoros': 7, 'entre_meteoros': 260, 'aviso_meteoro': 1000, 'radio_meteoro': 58, 'daño_meteoro': 0.75,
              'aviso_sentencia': 1000, 'aviso_serie': 650,
              'sentencia_chica': {'radio': 130, 'serie': 3, 'daño': 1.2}, 'sentencia_grande': {'radio': 175, 'serie': 2, 'daño': 1.5},   # el sello original medía 150
              'dura_proteccion': 3000, 'daño_para_proteger': 0.04, 'dura_recuperacion': 3000, 'cura': 0.08}
    TIPOS_ARCEUS = tuple(datos.pokemones.TABLA_TIPOS)

    # Arceus Beta: flota sobre el vacio delante del piso que te queda y va de un lado al otro (3 fases, por ahora todas como la primera)
    #   1  aparece con las tablas girando a su alrededor; cada tabla tira ataques de su tipo, mas grandes que los normales
    BETA = {'tam': 300, 'ancho': 240, 'alto': 200, 'vaiven': 220, 'periodo': 2600, 'fases': (2 / 3, 1 / 3),
            'orbita': (310, 420), 'giro': 0.00035, 'primer_ataque': (1500, 5000), 'ataque_tabla': (5500, 8500),
            'aviso_marca': 900, 'radio_marca': 95, 'daño_marca': 0.7, 'vel_bala': 5.5, 'dist_bala': 750, 'tam_bala': 30, 'daño_bala': 0.55, 'abanico': 0.35}
    TIPOS_TABLA = tuple(t for t in TIPOS_ARCEUS if t not in ('normal', 'agua', 'dragon', 'acero', 'fantasma'))   # sin agua, dragon, acero ni fantasma (y en los juegos no hay tabla normal)
    FORMA_TABLA = {t: 'marca' for t in ('electrico', 'tierra', 'roca', 'psiquico', 'fantasma', 'hada', 'dragon')}   # cae donde estas
    FORMA_TABLA.update({t: 'abanico' for t in ('fuego', 'volador', 'veneno', 'bicho', 'lucha', 'siniestro')})        # 3 balas en abanico
    ESTILO_JEFE = {'regigigas': 'regigigas', 'arceus': 'arceus', 'arceus_beta': 'beta', 'regice': 'regice', 'regirock': 'regirock',
                   'registeel': 'registeel', 'regieleki': 'regieleki', 'regidrago': 'regidrago'}

    # Regice: 2 fases (50%)
    #   1  rayo hielo que deja escarcha y al final un bloque de hielo (se empuja con E y se desliza por la escarcha); muros de hielo
    #   2  coraza de hielo (se rompe chocandole un bloque), el rayo rebota en las paredes 5 s y caen estalactitas
    REGICE = {'vel': 1.2, 'fases': (0.5,), 'rayo': 7000, 'rayo_fase2': 8500, 'aviso_rayo': 1100, 'largo_rayo': 1600, 'ancho_rayo': 46, 'daño_rayo': 1.3, 'haz': 400,
              'muro': 5000, 'bloques': 3, 'max_bloques': 12, 'max_glaciares': 3,
              'largo_rebote': 2600, 'rebotes': 4, 'dura_rebote': 5000, 'tick_rebote': 400, 'daño_rebote': 0.5,
              'mult_coraza': 0.2, 'mult_rota': 1.6,
              'estalactita': 1300, 'aviso_estalactita': 1000, 'radio_estalactita': 55, 'daño_estalactita': 0.9}
    # Regirock: 3 fases (75% y 25%)
    #   1  roca afilada, avalancha (6 rocas en hexagono alrededor tuyo) y llama refuerzos
    #   2  avalancha, roca afilada, fuerza bruta y arena movediza alrededor de las rocas que deja la roca afilada
    #   3  se parte en 5 rocas rodantes que rebotan y tiran lanzarrocas; cuando se quedan sin vida explotan
    REGIROCK = {'vel': 1.3, 'fases': (0.75, 0.25), 'roca': 3200, 'aviso_roca': 600, 'paso_roca': 72, 'cada_roca': 65, 'radio_roca': 40, 'largo_roca': 13,
                'dura_roca': 700, 'daño_roca': 1.1, 'max_rocas': 6, 'radio_movediza': 110,
                'fuerza': 5000, 'aviso_fuerza': 900, 'largo_fuerza': 750, 'ancho_fuerza': 180, 'vel_fuerza': 15, 'daño_fuerza': 1.6, 'aturdido': 3000,
                'avalancha': 6500, 'aviso_avalancha': 700, 'vuelo_avalancha': 800, 'radio_hexagono': 150, 'radio_avalancha': 55, 'daño_avalancha': 1.0,
                'dura_roca_avalancha': 5000,
                'rodantes': 5, 'tam_rodante': 54, 'vel_rodante': 3.6, 'lanza': 2600, 'vel_lanza': 5, 'dist_lanza': 300, 'daño_lanza': 0.45,
                'daño_rodante': 0.7, 'espera_explosion': 1100, 'radio_explosion': 110, 'daño_explosion': 1.2}
    # Registeel: 3 fases (75% y 25%)
    #   1  sierras que rebotan y llama refuerzos
    #   2  sierras, minas e iman (atrae o aleja al jugador y a las minas; las minas que le explotan cerca lo lastiman)
    #   3  sierras, iman, Foco Resplandor (rayo que sigue donde estabas) y Cuerpo Pesado (cae del cielo)
    REGISTEEL = {'vel': 1.0, 'fases': (0.75, 0.25), 'mina': 4200, 'minas_de_a': 3, 'espera_mina': 1300, 'radio_mina': 100, 'daño_mina': 1.0,
                 'daño_bala_mina': 0.5, 'vel_bala_mina': 6, 'dist_bala_mina': 450, 'daño_mina_jefe': 0.03,
                 'sierra': 3600, 'sierras_de_a': 2, 'vel_sierra': 7, 'dura_sierra': 7000, 'radio_sierra': 34, 'daño_sierra': 0.9,
                 'iman': 9000, 'dura_iman': 4000, 'fuerza_iman': 2.4, 'fuerza_mina': 2.0,
                 'foco': 7500, 'aviso_foco': 900, 'dura_foco': 3500, 'retraso': 500, 'giro_foco': 0.03, 'largo_foco': 1500, 'ancho_foco': 30,
                 'tick_foco': 300, 'daño_foco': 0.4,
                 'pesado': 9000, 'sube': 450, 'sigue': 1300, 'quieto': 300, 'cae': 350, 'alto_salto': 800, 'radio_pesado': 150, 'daño_pesado': 1.6}
    # Regieleki: 5 rayos; al perder un cuarto de vida se mete en las torres; sin torres se teletransporta con alto voltaje y usa Jaula Voltio
    REGIELEKI = {'vel': 2.6, 'rayos': 2600, 'aviso_rayos': 500, 'balas': 5, 'abanico': 0.6, 'vel_bala': 10, 'dist_bala': 700, 'daño_bala': 0.55,
                 'umbral': 0.75, 'torres': 6, 'radio_torres': 5, 'cambio': 1500, 'quedarse': 5000, 'golpes_torre': 3, 'vel_viaje': 26,
                 'linea': 2500, 'ancho_linea': 14, 'daño_linea': 0.5, 'tele': 2000, 'onda': 3000, 'radio_onda': 330, 'daño_onda': 1.1, 'segunda_onda': 700,
                 'jaula': 9000, 'primera_jaula': 1500, 'lado_jaula': 220, 'grosor_jaula': 16, 'golpes_jaula': 2, 'dura_jaula': 7000, 'daño_jaula': 0.5}
    # Regidrago: 3 fases (75% y 25%)
    #   1  Enfado (embiste dejando fuego) y llama 5 de su tipo
    #   2  te muerde y te sube a su torre: Cometa Draco, bocas que tiran Dragoaliento y al 25% Draco Energia; despues la torre se rompe
    #   3  en la sala de nuevo, todo junto menos llamar refuerzos
    REGIDRAGO = {'vel': 1.4, 'fases': (0.75, 0.25), 'refuerzos': 0.9,
                 'enfado': 4200, 'aviso_enfado': 850, 'largo_enfado': 800, 'ancho_enfado': 170, 'vel_enfado': 15, 'daño_enfado': 1.5, 'fuego_cada': 170,
                 'aviso_mordida': 800, 'vel_mordida': 16, 'dura_mordida': 1800, 'daño_mordida': 0.8, 'subida': 1500, 'fundido': 700, 'rompe': 900,
                 'torre': (15, 3, 2), 'vaiven': 380, 'periodo': 1400,
                 'cometa': 4500, 'aviso_cometa': 1100, 'cada_meteoro': 110, 'radio_meteoro': 70, 'paso_meteoro': 95, 'largo_cometa': 900, 'daño_meteoro': 1.2,
                 'boca': 3000, 'max_bocas': 4, 'disparos_boca': 3, 'cada_boca': 1700, 'aviso_boca': 650,
                 'vel_aliento': 7, 'dist_aliento': 950, 'tam_aliento': 30, 'daño_aliento': 0.55, 'abanico_aliento': 0.18,
                 'carga_draco': 2000, 'dura_draco': 10000, 'giro_draco': 0.018, 'largo_draco': 1800, 'ancho_draco': 40, 'tick_draco': 300, 'daño_draco': 0.35,
                 'draco': 26000, 'primer_draco': 9000, 'retraso_draco': 450, 'vida_boca': 0.035}
    COLOR_TORRE = {'gris': (130, 130, 130), 'cargada': (250, 220, 40), 'rota': (120, 75, 35)}
    # donde se parte la barra de vida de cada jefe con fases (Regieleki cambia de fase por las torres, no por la vida)
    FASES_JEFE = {'arceus': ARCEUS['fases'], 'beta': BETA['fases'], 'regidrago': REGIDRAGO['fases'], 'regice': REGICE['fases'],
                  'regirock': REGIROCK['fases'], 'registeel': REGISTEEL['fases'], 'regieleki': (REGIELEKI['umbral'],)}
    TOTAL_FASES = {'regieleki': 3}


    def preparar_jefe(b):
        """Pone en un jefe todos los campos que usan sus ataques (avisos, rayos, tablas, minas, torres...) y su estilo."""
        b.update({'aviso': None, 'prox_rafaga': 0, 'prox_pisoton': 0, 'resto_ia': [0.0, 0.0], 'estilo': ESTILO_JEFE.get(b['nombre'], 'jefe'),
                  'prox_terremoto': None, 'prox_puño': None, 'serie': 0,
                  'fase': 1, 'haz': None, 'libre_en': None, 'fin_exclusivo': 0, 'meteoros': [], 'vozarron': [], 'recupera': None,
                  'tablas': [], 'marcas': [], 'inicio_beta': None, 'centro_beta': None,
                  'prox': {}, 'muros': [], 'filas_roca': [], 'circulos': [], 'dash': None, 'aturdido_hasta': 0, 'minas': [], 'sierras': [],
                  'iman_hasta': 0, 'iman_a': None, 'torres': None, 'torre': None, 'modo': 'libre', 'viaje': None, 'lineas': [], 'ondas': [],
                  'escondido': False, 'vida_guardada': b['vida'], 'prox_linea': 0,
                  'etapa': None, 'cometas': [], 'bocas': [], 'draco': None, 'invulnerable': False, 'sin_contacto': False, 'sin_estados': False,
                  'fundido': None, 'plataforma': None, 'mordida': None, 'pedido': None,
                  'mult_recibido': 1.0, 'mensajes': [], 'anim_forzada': None, 'coraza': False, 'coraza_rota': False, 'estalactitas': [],
                  'caidas': [], 'rocas_avalancha': [], 'rodantes': [], 'partido': False, 'iman_modo': None, 'foco': None, 'rastro': [],
                  'altura': 0, 'salto': None, 'jaula': None, 'lento_hasta': None, 'despierto': False, 'escudo_hasta': 0, 'agarre': None})


    def _fase(b, cortes):
        """Fase segun la vida que le queda (cortes de mayor a menor, ej. (0.75, 0.25) -> fases 1, 2 y 3)."""
        k = b['vida'] / max(1, b['max_vida'])
        return 1 + sum(1 for c in cortes if k <= c)


    def _rastrear(b, j, ahora):
        """Guarda por donde fue pasando el jugador (para los rayos que siguen donde estabas, no donde estas)."""
        b['rastro'].append((ahora, j['rect'].center))
        while len(b['rastro']) > 2 and b['rastro'][1][0] < ahora - 1500: b['rastro'].pop(0)


    def _pos_anterior(b, j, ahora, retraso):
        """Donde estaba el jugador hace 'retraso' ms."""
        for t, pos in reversed(b['rastro']):
            if t <= ahora - retraso: return pos
        return b['rastro'][0][1] if b['rastro'] else j['rect'].center


    def _girar_hacia(ang, quiero, maximo):
        """Gira un angulo hacia otro, como mucho 'maximo' radianes."""
        dif = (quiero - ang + math.pi) % math.tau - math.pi
        return ang + max(-maximo, min(maximo, dif))


    def _toca_linea(j, puntos, ancho):
        """Si el jugador esta tocando alguno de los tramos de una linea quebrada (rayos que rebotan)."""
        mitad = max(j['rect'].size) / 2
        return any(_dist_segmento(j['rect'].center, a, b) <= ancho + mitad for a, b in zip(puntos, puntos[1:]))


    def _trazar(ent, desde, d, largo, rebotes=0):
        """Camino de un rayo: sigue derecho hasta una pared y, si le quedan rebotes, rebota. Devuelve los puntos de la linea."""
        pared = lambda x, y: mundos.TERRENOS[entorno.terreno_en(ent, x, y)].get('solido')
        (x, y), (dx, dy), paso = desde, d, 8
        puntos, recorrido = [(x, y)], 0
        while recorrido < largo:
            nx, ny = x + dx * paso, y + dy * paso
            if pared(nx, ny):
                if rebotes <= 0: break
                rebotes -= 1
                choca_x, choca_y = pared(nx, y), pared(x, ny)
                if choca_x: dx = -dx
                if choca_y: dy = -dy
                if not (choca_x or choca_y): dx, dy = -dx, -dy
                puntos.append((x, y))
                continue
            x, y = nx, ny; recorrido += paso
        puntos.append((x, y))
        return puntos


    def _animar(b, nombres, ahora, duracion):
        """Le pone al jefe una animacion por un rato (la primera de 'nombres' que tenga su sprite)."""
        b['anim_forzada'] = (nombres, ahora + duracion)


    def _dash_gigas(b, ctx):
        """Gigaimpacto: carga en linea recta hasta donde estabas; despues queda quieto recargando."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        G, d = GIGAS, b['dash']
        paso = min(G['vel_giga'], d['restante'])
        d['resto'][0] += d['dir'][0] * paso; d['resto'][1] += d['dir'][1] * paso
        px, py = int(d['resto'][0]), int(d['resto'][1])
        d['resto'][0] -= px; d['resto'][1] -= py
        quiero = b['rect'].move(px, py)
        entorno.mover(ent, b['rect'], px, py, [b['tipo']])
        d['restante'] -= paso
        if not d['pego'] and _en_franja(b, j, G['ancho_giga']): ctx['dañar_jugador'](b['daño'] * G['daño_giga'], 'normal'); d['pego'] = True
        choco = (px or py) and b['rect'].topleft != quiero.topleft
        if choco or d['restante'] <= 0:
            b['dash'] = None; b['aturdido_hasta'] = ahora + G['recarga_giga']
            ctx['impacto'](*b['rect'].center, 120, 450 if choco else 200)


    def _agarron(b, ctx):
        """Agarron: te sostiene un momento y te tira para atras. Solo lastima si chocas contra una pared."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        G, g = GIGAS, b['agarre']
        if g['etapa'] == 'sostiene':
            j['rect'].center = (round(b['rect'].centerx + g['dir'][0] * (max(b['rect'].size) / 2 + 30)), round(b['rect'].centery + g['dir'][1] * (max(b['rect'].size) / 2 + 30)))
            if ahora >= g['hasta']: g.update(etapa='vuela', hasta=ahora + G['vuelo_max'], resto=[0.0, 0.0])
            return
        g['resto'][0] += g['dir'][0] * G['vel_lanzar']; g['resto'][1] += g['dir'][1] * G['vel_lanzar']
        px, py = int(g['resto'][0]), int(g['resto'][1])
        g['resto'][0] -= px; g['resto'][1] -= py
        quiero = j['rect'].move(px, py)
        entorno.mover(ent, j['rect'], px, py, j['tipos'])
        if j['rect'].topleft != quiero.topleft:                    # choco contra la pared
            ctx['dañar_jugador'](b['daño'] * G['daño_lanzar'], 'lucha')
            ctx['impacto'](*j['rect'].center, 60, 400)
            b['agarre'] = None; j['atrapado_hasta'] = 0
        elif ahora >= g['hasta']: b['agarre'] = None; j['atrapado_hasta'] = 0


    def actualizar_regigigas(b, ctx):
        """Lento Inicio: los primeros 10 s esta quieto con la defensa subida y al despertar usa Terremoto.
        Despues: Terremoto, Megapuño (3 seguidos), Gigaimpacto, Proteccion (3 s quieto sin recibir daño) y Agarron (te tira contra la pared)."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        mitad = max(j['rect'].size) / 2
        G, p = GIGAS, b['prox']
        if b['lento_hasta'] is None: b['lento_hasta'] = ahora + G['lento']; b['mult_recibido'] = G['def_lento']
        if not b['despierto']:
            if ahora < b['lento_hasta']: return
            b.update(despierto=True, mult_recibido=1.0, vida_ref=b['vida'])
            b['mensajes'].append(('Regigigas desperto!', 1800))
            p.update(puño=ahora + 2500, giga=ahora + 4000, proteccion=ahora + 6000, agarre=ahora + 3000, ref=ahora + 2500)
            b['prox_terremoto'] = ahora + G['terremoto']
            b['aviso'] = {'hasta': ahora + G['aviso_terremoto'], 'clase': 'terremoto', 'inicio': ahora}
            return
        b['invulnerable'] = ahora < b['escudo_hasta']
        if b['invulnerable']: return                               # Proteccion: quieto detras del escudo
        if ahora >= p['ref']: p['ref'] = ahora + 2500; b['vida_ref'] = b['vida']
        if b['agarre']: _agarron(b, ctx); return
        if b['dash']: _dash_gigas(b, ctx); return
        if ahora < b['aturdido_hasta']: return
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'terremoto':
                if dist <= G['radio_terremoto'] + mitad: ctx['dañar_jugador'](b['daño'] * G['daño_terremoto'], 'tierra')
                ctx['impacto'](bx, by, G['radio_terremoto'], G['temblor'])
            elif a['clase'] == 'agarre':
                p['agarre'] = ahora + G['agarre']
                if dist <= G['radio_agarre'] + mitad:
                    b['agarre'] = {'etapa': 'sostiene', 'hasta': ahora + G['sostener'], 'dir': _dir((bx, by), (jx, jy))}
                    j['atrapado_hasta'] = ahora + 10 ** 7
            elif a['clase'] == 'gigaimpacto':
                b['dash'] = {'dir': a['dir'], 'restante': a['largo'], 'pego': False, 'resto': [0.0, 0.0]}
            else:
                mx, my = a['mira']
                if math.hypot(jx - mx, jy - my) <= GIGAS['radio_puño'] + mitad: ctx['dañar_jugador'](b['daño'] * GIGAS['daño_puño'], 'normal')
                ctx['impacto'](mx, my, GIGAS['radio_puño'], 250)
                b['serie'] -= 1
                if b['serie'] > 0: b['aviso'] = {'hasta': ahora + GIGAS['aviso_serie'], 'clase': 'puño', 'inicio': ahora, 'mira': (jx, jy)}
                else: p['puño'] = ahora + G['puño']                   # la espera arranca cuando termina la serie
            return
        if dist < G['radio_agarre'] and ahora >= p['agarre']:
            p['agarre'] = ahora + G['agarre']
            b['aviso'] = {'hasta': ahora + G['aviso_agarre'], 'clase': 'agarre', 'inicio': ahora}; return
        if ahora >= p['proteccion'] and b['vida'] <= b['vida_ref'] - b['max_vida'] * G['daño_para_proteger']:   # le estan pegando mucho: se cubre
            p['proteccion'] = ahora + G['proteccion']; b['escudo_hasta'] = ahora + G['dura_proteccion']; b['invulnerable'] = True; return
        if ahora >= b['prox_terremoto'] and dist < G['radio_terremoto'] * 1.3:
            b['prox_terremoto'] = ahora + G['terremoto']
            b['aviso'] = {'hasta': ahora + G['aviso_terremoto'], 'clase': 'terremoto', 'inicio': ahora}; return
        if ahora >= p['giga'] and dist > 250:
            p['giga'] = ahora + G['giga']
            b['aviso'] = {'hasta': ahora + G['aviso_giga'], 'clase': 'gigaimpacto', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy)),
                          'largo': min(G['largo_giga'], dist + 150), 'ancho': G['ancho_giga']}; return
        if ahora >= p['puño']:
            b['serie'] = G['serie']
            b['aviso'] = {'hasta': ahora + G['aviso_puño'], 'clase': 'puño', 'inicio': ahora, 'mira': (jx, jy)}; return
        if dist > 140: _ir_a(ent, b, (jx, jy), G['vel'], [])


    def _dist_segmento(p, a, b):
        """Distancia de un punto a un segmento (para saber si un rayo te toco)."""
        ax, ay = a; bx, by = b
        largo = (bx - ax) ** 2 + (by - ay) ** 2 or 1
        k = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / largo))
        return math.hypot(p[0] - ax - k * (bx - ax), p[1] - ay - k * (by - ay))


    def fase_arceus(b, cortes=None):
        """Fase de Arceus (o de Arceus Beta) segun la vida que le queda. No vuelve atras aunque Recuperacion lo cure."""
        b['fase'] = max(b['fase'], _fase(b, cortes or ARCEUS['fases']))
        return b['fase']


    def _terminar(b, ahora, exclusivo=False):
        """Termino un movimiento de Arceus: espera un poco antes del siguiente (y anota cuando termino Recuperacion, Velocidad Extrema o Hiperrayo)."""
        b['libre_en'] = ahora + random.randint(*ARCEUS['pausa'])
        if exclusivo: b['fin_exclusivo'] = ahora


    def _proteger(b, ahora):
        """Proteccion: escudo 3 s; mientras dura no se mueve, no ataca y no recibe daño."""
        b['escudo_hasta'] = ahora + ARCEUS['dura_proteccion']; b['invulnerable'] = True
        b['prox']['proteccion'] = ahora + ARCEUS['espera']['proteccion']
        _terminar(b, b['escudo_hasta'])


    def _aviso_sentencia(b, ahora, espera, mira):
        """Marca de una Sentencia en el piso: donde cae, cuando y de que tamaño (chica en la fase 2, grande en la 3). Siempre de tipo normal."""
        s = ARCEUS['sentencia_grande'] if b['fase'] == 3 else ARCEUS['sentencia_chica']
        return {'hasta': ahora + espera, 'clase': 'sentencia', 'inicio': ahora, 'mira': mira, 'tipo': 'normal', 'radio': s['radio'], 'daño': s['daño']}


    def _elegir_arceus(b, ctx):
        """Elige al azar el proximo movimiento entre los de su fase que ya esten listos.
        Recuperacion, Velocidad Extrema e Hiperrayo no se usan uno pegado al otro."""
        ent, j, ahora, A, p = ctx['ent'], ctx['jugador'], ctx['ahora'], ARCEUS, b['prox']
        (jx, jy), (bx, by) = j['rect'].center, b['rect'].center
        listos = []
        for mov in MOVS_ARCEUS[b['fase']]:
            if ahora < p.get(mov, 0): continue
            if mov in EXCLUSIVOS_ARCEUS and ahora < b['fin_exclusivo'] + A['pausa_exclusivos']: continue
            if mov == 'hiperrayo' and not ve(ent, (bx, by), (jx, jy)): continue
            if mov == 'velocidad_extrema' and math.hypot(jx - bx, jy - by) < 200: continue
            if mov == 'recuperacion' and b['vida'] >= b['max_vida']: continue
            listos.append(mov)
        if not listos: return
        mov = random.choice(listos)
        p[mov] = ahora + A['espera'][mov]
        if mov == 'hiperrayo':
            ang = math.atan2(jy - by, jx - bx)
            b['aviso'] = {'hasta': ahora + A['aviso_hiperrayo'], 'clase': 'hiperrayo', 'inicio': ahora, 'ang': ang, 'ancho': b['rect'].width // 2,
                          'fin': (bx + math.cos(ang) * A['largo_hiperrayo'], by + math.sin(ang) * A['largo_hiperrayo'])}
            _animar(b, ('charge', 'spattack'), ahora, A['aviso_hiperrayo'])
        elif mov == 'velocidad_extrema':
            b['aviso'] = {'hasta': ahora + A['aviso_extrema'], 'clase': 'velocidad_extrema', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy)),
                          'largo': min(A['largo_extrema'], math.hypot(jx - bx, jy - by) + 150), 'ancho': b['rect'].width}
        elif mov == 'vozarron':
            b['aviso'] = {'hasta': ahora + A['aviso_vozarron'], 'clase': 'vozarron', 'inicio': ahora}
            _animar(b, ('spattack', 'charge'), ahora, A['aviso_vozarron'] + 300)
        elif mov == 'meteoros':                                     # cada meteorito apunta a donde estas cuando le toca salir
            b['meteoros'].extend({'sale': ahora + i * A['entre_meteoros'], 'pos': None} for i in range(A['meteoros']))
            _animar(b, ('spattack', 'charge'), ahora, 600)
            _terminar(b, ahora)
        elif mov == 'sentencia':
            b['serie'] = (A['sentencia_grande'] if b['fase'] == 3 else A['sentencia_chica'])['serie']
            b['aviso'] = _aviso_sentencia(b, ahora, A['aviso_sentencia'], (jx, jy))
        elif mov == 'proteccion': _proteger(b, ahora)
        else:
            b['recupera'] = {'inicio': ahora, 'hasta': ahora + A['dura_recuperacion'], 'vida': b['vida']}
            _animar(b, ('deepbreath', 'pose'), ahora, A['dura_recuperacion'])


    def _hiperrayo_arceus(b, ctx):
        """Hiperrayo disparando: sale de Arceus y gira despacio hacia donde estabas hace un rato (se esquiva). Al terminar recarga quieto."""
        j, ahora, A, h = ctx['jugador'], ctx['ahora'], ARCEUS, b['haz']
        bx, by = b['rect'].center
        px, py = _pos_anterior(b, j, ahora, A['retraso_hiperrayo'])
        h['ang'] = _girar_hacia(h['ang'], math.atan2(py - by, px - bx), A['giro_hiperrayo'])
        h['desde'], h['fin'] = (bx, by), (bx + math.cos(h['ang']) * A['largo_hiperrayo'], by + math.sin(h['ang']) * A['largo_hiperrayo'])
        if ahora >= h['prox'] and _dist_segmento(j['rect'].center, h['desde'], h['fin']) <= h['ancho'] + max(j['rect'].size) / 2:
            ctx['dañar_jugador'](b['daño'] * A['daño_hiperrayo'], 'normal'); h['prox'] = ahora + A['tick_hiperrayo']
        if ahora >= h['hasta']:
            b['haz'] = None; b['anim_forzada'] = None
            b['aturdido_hasta'] = ahora + A['recarga_hiperrayo']        # recarga: quieto (estrellitas arriba de la cabeza)
            _terminar(b, b['aturdido_hasta'], exclusivo=True)


    def _extrema_arceus(b, ctx):
        """Velocidad Extrema: embiste en linea recta muy rapido. Si choca contra una pared se frena, pero no queda aturdido."""
        ent, j, ahora, A, d = ctx['ent'], ctx['jugador'], ctx['ahora'], ARCEUS, b['dash']
        paso = min(A['vel_extrema'], d['restante'])
        d['resto'][0] += d['dir'][0] * paso; d['resto'][1] += d['dir'][1] * paso
        px, py = int(d['resto'][0]), int(d['resto'][1])
        d['resto'][0] -= px; d['resto'][1] -= py
        quiero = b['rect'].move(px, py)
        entorno.mover(ent, b['rect'], px, py, [b['tipo']])
        d['restante'] -= paso
        if not d['pego'] and _en_franja(b, j, b['rect'].width): ctx['dañar_jugador'](b['daño'] * A['daño_extrema'], 'normal'); d['pego'] = True
        choco = (px or py) and b['rect'].topleft != quiero.topleft
        if choco or d['restante'] <= 0:
            b['dash'] = None
            if choco: ctx['impacto'](*b['rect'].center, 80, 250)
            _terminar(b, ahora, exclusivo=True)


    def _recuperacion_arceus(b, ctx):
        """Recuperacion: si le pegaste mientras juntaba estrellitas se corta; si aguanto los 3 s se cura un poco."""
        ahora, r = ctx['ahora'], b['recupera']
        if b['vida'] < r['vida']:
            b['recupera'] = None; b['anim_forzada'] = None
            b['mensajes'].append(('Le cortaste la Recuperacion!', 1400))
            _terminar(b, ahora, exclusivo=True)
        elif ahora >= r['hasta']:
            b['vida'] = min(b['max_vida'], b['vida'] + round(b['max_vida'] * ARCEUS['cura']))
            b['recupera'] = None
            b['mensajes'].append(('Arceus se curo', 1400))
            _terminar(b, ahora, exclusivo=True)


    def _actualizar_meteoros(b, ctx):
        """Meteoros: cada uno sale apuntando a donde estas, avisa 1 s con una sombra y cae."""
        j, ahora, A = ctx['jugador'], ctx['ahora'], ARCEUS
        for m in b['meteoros'][:]:
            if m['pos'] is None:
                if ahora >= m['sale']: m.update(pos=j['rect'].center, inicio=ahora, hasta=ahora + A['aviso_meteoro'])
                continue
            if ahora < m['hasta']: continue
            b['meteoros'].remove(m)
            x, y = m['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= A['radio_meteoro'] + max(j['rect'].size) / 2: ctx['dañar_jugador'](b['daño'] * A['daño_meteoro'], 'normal')
            ctx['impacto'](x, y, A['radio_meteoro'], 150)


    def _actualizar_vozarron(b, ctx):
        """Vozarron: los 3 circulos se agrandan durante 5 s; cada uno te pega una sola vez si su borde te pasa por encima."""
        j, ahora, A = ctx['jugador'], ctx['ahora'], ARCEUS
        jx, jy = j['rect'].center
        for o in b['vozarron'][:]:
            if ahora >= o['hasta']: b['vozarron'].remove(o); continue
            if ahora < o['inicio']: continue
            radio = A['radio_vozarron'] * (ahora - o['inicio']) / A['dura_vozarron']
            if not o['pego'] and abs(math.hypot(jx - o['pos'][0], jy - o['pos'][1]) - radio) <= A['grosor_vozarron'] + max(j['rect'].size) / 2:
                ctx['dañar_jugador'](b['daño'] * A['daño_vozarron'], 'normal'); o['pego'] = True


    def actualizar_arceus(b, ctx):
        """Arceus: usa un movimiento por vez, elegido al azar entre los de su fase (ver MOVS_ARCEUS), con una pausa entre uno y otro."""
        ent, j, ahora, A, p = ctx['ent'], ctx['jugador'], ctx['ahora'], ARCEUS, b['prox']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        mitad = max(j['rect'].size) / 2
        if b['libre_en'] is None:
            b.update(libre_en=ahora + A['primer_mov'], fin_exclusivo=ahora - A['pausa_exclusivos'], vida_ref=b['vida']); p['ref'] = ahora + 2500
        fase_arceus(b)
        _rastrear(b, j, ahora)
        _actualizar_meteoros(b, ctx)                                # los meteoros y los circulos siguen aunque el haga otra cosa
        _actualizar_vozarron(b, ctx)
        if ahora >= p['ref']: p['ref'] = ahora + 2500; b['vida_ref'] = b['vida']
        b['invulnerable'] = ahora < b['escudo_hasta']
        if b['invulnerable']: return                               # Proteccion: quieto y sin atacar detras del escudo
        if b['haz']: _hiperrayo_arceus(b, ctx); return
        if b['dash']: _extrema_arceus(b, ctx); return
        if b['recupera']: _recuperacion_arceus(b, ctx); return
        if ahora < b['aturdido_hasta']: return                     # recargando despues del Hiperrayo: quieto
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'hiperrayo':
                b['haz'] = {'ang': a['ang'], 'desde': (bx, by), 'fin': a['fin'], 'ancho': a['ancho'], 'hasta': ahora + A['dura_hiperrayo'], 'prox': ahora}
                ctx['impacto'](bx, by, 60, 300)
                _animar(b, ('spattack', 'shoot'), ahora, A['dura_hiperrayo'])
            elif a['clase'] == 'velocidad_extrema':
                b['dash'] = {'dir': a['dir'], 'restante': a['largo'], 'pego': False, 'resto': [0.0, 0.0]}
            elif a['clase'] == 'vozarron':
                b['vozarron'].extend({'pos': (bx, by), 'inicio': ahora + i * A['entre_circulos'], 'hasta': ahora + i * A['entre_circulos'] + A['dura_vozarron'], 'pego': False}
                                     for i in range(A['circulos']))
                ctx['impacto'](bx, by, 80, 250)
                _terminar(b, ahora)
            else:                                                   # Sentencia
                mx, my = a['mira']
                if math.hypot(jx - mx, jy - my) <= a['radio'] + mitad: ctx['dañar_jugador'](b['daño'] * a['daño'], a['tipo'])
                ctx['impacto'](mx, my, a['radio'], 350)
                b['serie'] -= 1
                if b['serie'] > 0: b['aviso'] = _aviso_sentencia(b, ahora, A['aviso_serie'], (jx, jy))
                else: _terminar(b, ahora)
            return
        if 'proteccion' in MOVS_ARCEUS[b['fase']] and ahora >= p.get('proteccion', 0) and b['vida'] <= b['vida_ref'] - b['max_vida'] * A['daño_para_proteger']:
            _proteger(b, ahora); return                             # le estan pegando mucho: se cubre
        if ahora >= b['libre_en']:
            _elegir_arceus(b, ctx)
            if b['aviso'] or b['recupera'] or b['invulnerable']: return
        if dist > 160: _ir_a(ent, b, (jx, jy), A['vel'], [])


    # ---------- Arceus Beta ----------

    def pos_tabla(b, t, ahora):
        """Donde esta una tabla de Arceus Beta: gira en ovalo alrededor de el."""
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
        """Arceus Beta flota de lado a lado con todas sus tablas girando alrededor; cada tabla ataca sola con su tipo."""
        j, ahora = ctx['jugador'], ctx['ahora']
        mitad = max(j['rect'].size) / 2
        if b['inicio_beta'] is None:                                # llega con las tablas ya girando, repartidas en dos anillos
            b['inicio_beta'], b['centro_beta'] = ahora, b['rect'].center
            b['tablas'] = [{'tipo': tipo, 'ang': i * math.tau / len(TIPOS_TABLA), 'radio': BETA['orbita'][i % 2], 'nace': ahora,
                            'prox': ahora + random.randint(*BETA['primer_ataque']), 'pos': b['rect'].center} for i, tipo in enumerate(TIPOS_TABLA)]
        fase_arceus(b, BETA['fases'])
        b['rect'].centerx = round(b['centro_beta'][0] + math.sin((ahora - b['inicio_beta']) / BETA['periodo']) * BETA['vaiven'])
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
        """Vector de largo 1 de 'desde' hacia 'hacia'."""
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


    def _bloque_glaciar(b, ctx, puntos):
        """Al final del rayo hielo de la primera fase queda un bloque de hielo para empujar con E (como mucho unos pocos a la vez)."""
        ent, j, R = ctx['ent'], ctx['jugador'], REGICE
        if sum(1 for o in ent['objetos'] if o['nombre'] == 'bloque_glaciar') >= R['max_glaciares'] or len(puntos) < 2: return
        (x0, y0), (x, y) = puntos[-2], puntos[-1]
        dx, dy = _dir((x0, y0), (x, y))
        for atras in (110, 160, 70, 210):                          # un poco antes de la pared, asi se puede pasar por detras
            if entorno.poner_objeto(ent, 'bloque_glaciar', (x - dx * atras, y - dy * atras), [j['rect'].inflate(20, 20), b['rect']]): return


    def _actualizar_estalactitas(b, ctx):
        """Estalactitas de la segunda fase: una sombra que crece en el piso y despues cae el hielo."""
        j, ahora, R = ctx['jugador'], ctx['ahora'], REGICE
        for e in b['estalactitas'][:]:
            if ahora < e['hasta']: continue
            b['estalactitas'].remove(e)
            x, y = e['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_estalactita'] + max(j['rect'].size) / 2:
                ctx['dañar_jugador'](b['daño'] * R['daño_estalactita'], 'hielo')
            ctx['impacto'](x, y, R['radio_estalactita'], 120)


    def actualizar_regice(b, ctx):
        """Regice: muros de hielo y rayo hielo que deja escarcha. Fase 1: el rayo deja un bloque de hielo para empujar.
        Fase 2: coraza de hielo (se rompe con un bloque), el rayo rebota en las paredes 5 s y caen estalactitas."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        R, p = REGICE, b['prox']
        if not p: p.update(rayo=ahora + 2500, muro=ahora + 1500, estalactita=0)
        fase = b['fase'] = _fase(b, R['fases'])
        if fase == 2 and not (b['coraza'] or b['coraza_rota']):
            b['coraza'] = True; p['estalactita'] = ahora + 1500
            ctx['impacto'](bx, by, 120, 400)
        b['mult_recibido'] = R['mult_coraza'] if b['coraza'] else R['mult_rota'] if b['coraza_rota'] else 1.0
        haz = b['haz']
        if haz:
            if ahora >= haz['hasta']: b['haz'] = None
            elif haz.get('tick') and ahora >= haz['prox'] and _toca_linea(j, haz['puntos'], R['ancho_rayo']):
                ctx['dañar_jugador'](b['daño'] * R['daño_rebote'], 'hielo'); haz['prox'] = ahora + haz['tick']
        _actualizar_estalactitas(b, ctx)
        if fase == 2 and ahora >= p['estalactita']:
            p['estalactita'] = ahora + R['estalactita']
            for pos in ((jx + random.randint(-80, 80), jy + random.randint(-80, 80)), entorno.punto_libre(ent, random)):
                b['estalactitas'].append({'pos': pos, 'inicio': ahora, 'hasta': ahora + R['aviso_estalactita']})
        if ahora >= p['muro']: p['muro'] = ahora + R['muro']; _muro_hielo(b, ctx)
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            puntos = a['puntos']
            for k in range(len(puntos) - 1): entorno.congelar_linea(ent, puntos[k], puntos[k + 1], R['ancho_rayo'] * 1.6)
            if a.get('rebota'):
                b['haz'] = {'puntos': puntos, 'hasta': ahora + R['dura_rebote'], 'tick': R['tick_rebote'], 'prox': ahora,
                            'ancho': R['ancho_rayo'], 'color': ((120, 200, 255), (235, 250, 255))}
            else:
                if _toca_linea(j, puntos, R['ancho_rayo']): ctx['dañar_jugador'](b['daño'] * R['daño_rayo'], 'hielo')
                b['haz'] = {'puntos': puntos, 'hasta': ahora + R['haz'], 'ancho': R['ancho_rayo'], 'color': ((120, 200, 255), (235, 250, 255))}
                if fase == 1: _bloque_glaciar(b, ctx, puntos)
            return
        if b['haz'] and b['haz'].get('tick'): return               # quieto mientras dura el rayo que rebota
        if ahora >= p['rayo']:
            p['rayo'] = ahora + (R['rayo'] if fase == 1 else R['rayo_fase2'])
            d = _dir((bx, by), (jx, jy))
            puntos = _trazar(ent, (bx, by), d, R['largo_rebote'] if fase == 2 else R['largo_rayo'], R['rebotes'] if fase == 2 else 0)
            b['aviso'] = {'hasta': ahora + R['aviso_rayo'], 'clase': 'rayo_hielo', 'inicio': ahora, 'puntos': puntos, 'fin': puntos[-1], 'rebota': fase == 2}
            return
        if dist > 220: _ir_a(ent, b, (jx, jy), R['vel'], [])


    def _poner_roca(b, ctx, puntos):
        """Deja una roca de Regirock al final de una fila (hasta un maximo por sala)."""
        ent, j = ctx['ent'], ctx['jugador']
        if sum(1 for o in ent['objetos'] if o.get('de_regi') and o['nombre'] == 'roca_afilada') >= REGIROCK['max_rocas']: return
        for punto in reversed(puntos[-3:]):
            if entorno.poner_objeto(ent, 'roca_afilada', punto, [j['rect'].inflate(10, 10), b['rect']]):
                ctx['impacto'](*punto, 30, 120)
                if b['fase'] >= 2:                                  # segunda fase: arena movediza alrededor de la roca
                    for f, c in entorno._casillas_circulo(ent, *punto, REGIROCK['radio_movediza']):
                        if ent['m'][f][c] in generacion.PISABLES: entorno.cambiar(ent, f, c, 'arena_movediza')
                return


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


    def _en_franja(b, j, ancho):
        """El que embiste pega en todo el ancho de su franja, no solo con el cuerpo."""
        return math.hypot(j['rect'].centerx - b['rect'].centerx, j['rect'].centery - b['rect'].centery) <= max(max(b['rect'].size), ancho) / 2 + max(j['rect'].size) / 2


    def _dash_regirock(b, ctx):
        """Fuerza bruta de Regirock: carga en linea recta, rompe las rocas que toca y queda aturdido si choca."""
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
        if not d['pego'] and _en_franja(b, j, REGIROCK['ancho_fuerza']): ctx['dañar_jugador'](b['daño'] * REGIROCK['daño_fuerza'], 'lucha'); d['pego'] = True
        if (px or py) and b['rect'].topleft != quiero.topleft:            # choco contra una roca o una pared
            for o in golpeados:
                if o['vida'] is not None: entorno.romper(ent, o, 'lucha')
            b['dash'] = None; b['aturdido_hasta'] = ahora + REGIROCK['aturdido']
            ctx['impacto'](*b['rect'].center, 120, 500)
        elif d['restante'] <= 0: b['dash'] = None


    def _actualizar_avalancha(b, ctx):
        """Las rocas de la avalancha vuelan, caen (lastiman si estas abajo) y quedan un rato como obstaculo."""
        ent, j, ahora, R = ctx['ent'], ctx['jugador'], ctx['ahora'], REGIROCK
        for c in b['caidas'][:]:
            if ahora < c['hasta']: continue
            b['caidas'].remove(c)
            x, y = c['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_avalancha'] + max(j['rect'].size) / 2:
                ctx['dañar_jugador'](b['daño'] * R['daño_avalancha'], 'roca')
            ctx['impacto'](x, y, R['radio_avalancha'], 150)
            o = entorno.poner_objeto(ent, 'roca_avalancha', (x, y), [j['rect'].inflate(10, 10), b['rect']])
            if o: o['expira'] = ahora + R['dura_roca_avalancha']
        viejas = [o for o in ent['objetos'] if o['nombre'] == 'roca_avalancha' and ahora >= o.get('expira', 0)]
        for o in viejas: ent['objetos'].remove(o); ctx['impacto'](*o['rect'].center, 30, 80)
        if viejas: ent['version'] += 1


    def _partir_regirock(b, ctx):
        """Tercera fase: Regirock se parte en 5 rocas rodantes (entre todas tienen la vida que le quedaba)."""
        ahora, R = ctx['ahora'], REGIROCK
        bx, by = b['rect'].center
        vida = max(1, round(b['vida'] / R['rodantes']))
        b.update(partido=True, escondido=True, invulnerable=True, sin_contacto=True, aviso=None, dash=None, filas_roca=[])
        for i in range(R['rodantes']):
            ang = i * math.tau / R['rodantes'] + random.uniform(-0.3, 0.3)
            r = pygame.Rect(0, 0, R['tam_rodante'], R['tam_rodante']); r.center = (round(bx + math.cos(ang) * 40), round(by + math.sin(ang) * 40))
            b['rodantes'].append({'rect': r, 'x': float(r.centerx), 'y': float(r.centery), 'v': [math.cos(ang) * R['vel_rodante'], math.sin(ang) * R['vel_rodante']],
                                  'vida': vida, 'max_vida': vida, 'tipo': 'roca', 'nombre': 'regirock', 'atacable': True, 'de_jefe': True,
                                  'estado': None, 'estado_hasta': 0, 'proximo_estado': 0, 'prox_lanza': ahora + 1500 + i * 400, 'golpe': 0, 'explota': None})
        ctx['impacto'](bx, by, 160, 700)


    def _actualizar_rodantes(b, ctx):
        """Las rocas rodantes rebotan en las paredes y en las rocas, tiran lanzarrocas y al quedarse sin vida explotan."""
        ent, j, ahora, R = ctx['ent'], ctx['jugador'], ctx['ahora'], REGIROCK
        duros = entorno.solidos_proyectil(ent)
        mitad = max(j['rect'].size) / 2
        for r in b['rodantes'][:]:
            x, y = r['rect'].center
            if r['vida'] <= 0:
                if r['explota'] is None: r['explota'] = ahora + R['espera_explosion']
                elif ahora >= r['explota']:
                    b['rodantes'].remove(r)
                    if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_explosion'] + mitad: ctx['dañar_jugador'](b['daño'] * R['daño_explosion'], 'roca')
                    ctx['impacto'](x, y, R['radio_explosion'], 400)
                continue
            if not (r['estado'] in ('paralizar', 'dormir') and r['estado_hasta'] > ahora):
                if (round(r['x']), round(r['y'])) != (x, y): r['x'], r['y'] = float(x), float(y)       # lo empujo un golpe
                caja = r['rect'].copy()
                for i in (0, 1):
                    nuevo = [r['x'], r['y']]; nuevo[i] += r['v'][i]
                    caja.center = (round(nuevo[0]), round(nuevo[1]))
                    if caja.collidelist(duros) != -1: r['v'][i] = -r['v'][i]
                    else: r['x'], r['y'] = nuevo
                r['rect'].center = (round(r['x']), round(r['y']))
            if r['rect'].colliderect(j['rect']) and ahora >= r['golpe']:
                ctx['dañar_jugador'](b['daño'] * R['daño_rodante'], 'roca'); r['golpe'] = ahora + 800
            if ahora >= r['prox_lanza']:                            # lanzarrocas: 6 rocas chicas alrededor
                r['prox_lanza'] = ahora + R['lanza'] + random.randint(-300, 300)
                giro = random.uniform(0, math.tau)
                for k in range(6):
                    ang = giro + k * math.tau / 6
                    ctx['disparar'](*r['rect'].center, math.cos(ang), math.sin(ang), b['daño'] * R['daño_lanza'], 'roca', R['vel_lanza'], R['dist_lanza'], 20)
        if b['rodantes']:
            b['rect'].center = (sum(r['rect'].centerx for r in b['rodantes']) // len(b['rodantes']), sum(r['rect'].centery for r in b['rodantes']) // len(b['rodantes']))
        b['vida'] = sum(max(0, r['vida']) for r in b['rodantes']) or (1 if b['rodantes'] else 0)   # mientras alguna explota no termina


    def actualizar_regirock(b, ctx):
        """Regirock: fase 1 roca afilada y avalancha; fase 2 ademas Fuerza bruta y arena movediza; fase 3 se parte en 5 rocas rodantes."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        R, p = REGIROCK, b['prox']
        if not p: p.update(roca=ahora + 1500, fuerza=ahora + 2500, avalancha=ahora + 4000)
        _avanzar_filas(b, ctx)
        _actualizar_avalancha(b, ctx)
        if b['partido']: b['fase'] = 3; _actualizar_rodantes(b, ctx); return
        fase = b['fase'] = _fase(b, R['fases'])
        if fase == 3: _partir_regirock(b, ctx); return
        if ahora < b['aturdido_hasta']: return
        if b['dash']: _dash_regirock(b, ctx); return
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'fuerza_bruta': b['dash'] = {'dir': a['dir'], 'restante': R['largo_fuerza'], 'pego': False, 'resto': [0.0, 0.0]}
            elif a['clase'] == 'avalancha':                         # tira 6 rocas que caen en hexagono alrededor tuyo
                giro = random.uniform(0, math.tau)
                for k in range(6):
                    ang = giro + k * math.tau / 6
                    b['caidas'].append({'pos': (jx + math.cos(ang) * R['radio_hexagono'], jy + math.sin(ang) * R['radio_hexagono']),
                                        'desde': (bx, by), 'inicio': ahora, 'hasta': ahora + R['vuelo_avalancha']})
            else: b['filas_roca'].append({'x': bx, 'y': by, 'dir': a['dir'], 'paso': 0, 'prox': ahora, 'puntos': [], 'inicio': max(b['rect'].size) / 2})
            return
        if ahora >= p['avalancha']:                                 # se queda quieto haciendo el lanzamiento
            p['avalancha'] = ahora + R['avalancha']
            _animar(b, ('rearup', 'shoot', 'attack', 'swing'), ahora, R['aviso_avalancha'])
            b['aviso'] = {'hasta': ahora + R['aviso_avalancha'], 'clase': 'avalancha', 'inicio': ahora}; return
        if fase >= 2 and ahora >= p['fuerza']:
            p['fuerza'] = ahora + R['fuerza']
            b['aviso'] = {'hasta': ahora + R['aviso_fuerza'], 'clase': 'fuerza_bruta', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy))}; return
        if ahora >= p['roca']:
            p['roca'] = ahora + R['roca']
            b['aviso'] = {'hasta': ahora + R['aviso_roca'], 'clase': 'roca_afilada', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy))}; return
        if dist > 240: _ir_a(ent, b, (jx, jy), R['vel'], [])


    def _actualizar_minas(b, ctx):
        """Las minas de Registeel que se cumplen explotan y sueltan 8 balas en estrella."""
        j, ahora = ctx['jugador'], ctx['ahora']
        R = REGISTEEL
        for m in b['minas'][:]:
            if ahora < m['hasta']: continue
            b['minas'].remove(m)
            x, y = m['pos']
            if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_mina'] + max(j['rect'].size) / 2: ctx['dañar_jugador'](b['daño'] * R['daño_mina'], 'acero')
            ctx['impacto'](x, y, R['radio_mina'], 150)
            if not b['invulnerable'] and math.hypot(b['rect'].centerx - x, b['rect'].centery - y) <= R['radio_mina'] + max(b['rect'].size) / 2:
                b['vida'] = max(1, b['vida'] - round(b['max_vida'] * R['daño_mina_jefe']))
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


    def _iman(b, ctx):
        """Iman: atrae (o aleja) al jugador y a las minas. Registeel se queda quieto mientras dura."""
        ent, j, R = ctx['ent'], ctx['jugador'], REGISTEEL
        (jx, jy), (bx, by) = j['rect'].center, b['rect'].center
        signo = 1 if b['iman_modo'] == 'atraer' else -1
        b['iman_a'] = (jx, jy)
        dx, dy = _dir((jx, jy), (bx, by))
        resto = j.setdefault('resto_iman', [0.0, 0.0])
        resto[0] += dx * R['fuerza_iman'] * signo; resto[1] += dy * R['fuerza_iman'] * signo
        px, py = int(resto[0]), int(resto[1])
        resto[0] -= px; resto[1] -= py
        entorno.mover(ent, j['rect'], px, py, j['tipos'])
        for m in b['minas']:
            mx, my = m['pos']
            if signo > 0 and math.hypot(bx - mx, by - my) < max(b['rect'].size) / 2 + 20: continue   # ya llego: queda pegada a el
            ux, uy = _dir((mx, my), (bx, by))
            m['pos'] = (mx + ux * R['fuerza_mina'] * signo, my + uy * R['fuerza_mina'] * signo)


    def _actualizar_foco(b, ctx):
        """Foco Resplandor: un rayo que va siguiendo por donde estabas (no donde estas), asi se puede esquivar."""
        j, ahora, R = ctx['jugador'], ctx['ahora'], REGISTEEL
        f = b['foco']
        bx, by = b['rect'].center
        px, py = _pos_anterior(b, j, ahora, R['retraso'])
        f['ang'] = _girar_hacia(f['ang'], math.atan2(py - by, px - bx), R['giro_foco'])
        f['fin'] = (bx + math.cos(f['ang']) * R['largo_foco'], by + math.sin(f['ang']) * R['largo_foco'])
        if ahora >= f['prox'] and _dist_segmento(j['rect'].center, (bx, by), f['fin']) <= R['ancho_foco'] + max(j['rect'].size) / 2:
            ctx['dañar_jugador'](b['daño'] * R['daño_foco'], 'acero'); f['prox'] = ahora + R['tick_foco']
        if ahora >= f['hasta']: b['foco'] = None


    def _cuerpo_pesado(b, ctx):
        """Cuerpo Pesado: Registeel salta fuera de la pantalla, su sombra te sigue, se frena y cae."""
        j, ahora, R, p = ctx['jugador'], ctx['ahora'], REGISTEEL, b['prox']
        s = b['salto']
        k = (ahora - s['inicio']) / max(1, R[s['etapa']])
        if s['etapa'] == 'sube':
            b['altura'] = round(R['alto_salto'] * min(1.0, k))
            if k >= 1: s.update(etapa='sigue', inicio=ahora)
        elif s['etapa'] == 'sigue':
            jx, jy = j['rect'].center
            b['rect'].center = (round(b['rect'].centerx + (jx - b['rect'].centerx) * 0.12), round(b['rect'].centery + (jy - b['rect'].centery) * 0.12))
            if k >= 1: s.update(etapa='quieto', inicio=ahora)
        elif s['etapa'] == 'quieto':
            if k >= 1: s.update(etapa='cae', inicio=ahora)
        else:
            b['altura'] = round(R['alto_salto'] * max(0.0, 1 - k))
            if k >= 1:
                x, y = b['rect'].center
                if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_pesado'] + max(j['rect'].size) / 2:
                    ctx['dañar_jugador'](b['daño'] * R['daño_pesado'], 'acero')
                ctx['impacto'](x, y, R['radio_pesado'], 600)
                b.update(salto=None, altura=0, invulnerable=False, sin_contacto=False)
                p['pesado'] = ahora + R['pesado']


    def actualizar_registeel(b, ctx):
        """Registeel: fase 1 sierras; fase 2 sierras, minas e iman (atrae o aleja); fase 3 sierras, iman, Foco Resplandor y Cuerpo Pesado."""
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        dist = math.hypot(jx - bx, jy - by)
        R, p = REGISTEEL, b['prox']
        if not p: p.update(mina=ahora + 1500, sierra=ahora + 2000, iman=ahora + 2500, foco=ahora + 2500, pesado=ahora + 5000)
        _rastrear(b, j, ahora)
        fase = b['fase'] = _fase(b, R['fases'])
        _actualizar_minas(b, ctx)
        _actualizar_sierras(b, ctx)
        if b['salto']: _cuerpo_pesado(b, ctx); return
        if b['foco']: _actualizar_foco(b, ctx); return
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            if a['clase'] == 'foco':
                px, py = _pos_anterior(b, j, ahora, R['retraso'])
                b['foco'] = {'ang': math.atan2(py - by, px - bx), 'fin': a['mira'], 'hasta': ahora + R['dura_foco'], 'prox': ahora}
            return
        if ahora < b['iman_hasta']: _iman(b, ctx); return
        b['iman_a'] = None
        if fase >= 2 and ahora >= p['iman']:
            p['iman'] = ahora + R['iman']; b['iman_hasta'] = ahora + R['dura_iman']
            b['iman_modo'] = 'alejar' if b['iman_modo'] == 'atraer' else 'atraer'
            return
        if fase == 3 and ahora >= p['pesado']:
            p['pesado'] = ahora + 10 ** 7                           # se vuelve a contar cuando cae
            b.update(salto={'etapa': 'sube', 'inicio': ahora}, invulnerable=True, sin_contacto=True)
            ctx['impacto'](bx, by, 80, 200); return
        if fase == 3 and ahora >= p['foco']:
            p['foco'] = ahora + R['foco']
            b['aviso'] = {'hasta': ahora + R['aviso_foco'], 'clase': 'foco', 'inicio': ahora, 'mira': (jx, jy)}; return
        if fase == 2 and ahora >= p['mina']:
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
        """Las torres electricas de Regieleki, en ronda alrededor del centro de la arena."""
        ent, j = ctx['ent'], ctx['jugador']
        sala, tam = ent['sala'], ent['tam']
        cx, cy = sala['columnas'] * tam / 2, sala['filas'] * tam / 2
        b['torres'] = []
        for i in range(REGIELEKI['torres']):
            ang = i * math.tau / REGIELEKI['torres']
            punto = (cx + math.cos(ang) * REGIELEKI['radio_torres'] * tam, cy + math.sin(ang) * REGIELEKI['radio_torres'] * tam)
            o = entorno.poner_objeto(ent, 'torre_electrica', punto, [j['rect'], b['rect']])
            if o: o['color'] = COLOR_TORRE['gris']; b['torres'].append({'obj': o, 'estado': 'gris', 'entro': 0, 'golpes': 0})


    def _rayos5(b, ctx):
        """Regieleki dispara 5 balas electricas en abanico hacia el jugador."""
        j, R = ctx['jugador'], REGIELEKI
        bx, by = b['rect'].center
        base = math.atan2(j['rect'].centery - by, j['rect'].centerx - bx)
        for i in range(R['balas']):
            ang = base + (i - (R['balas'] - 1) / 2) * R['abanico'] / 2
            ctx['disparar'](bx + math.cos(ang) * 60, by + math.sin(ang) * 60, math.cos(ang), math.sin(ang), b['daño'] * R['daño_bala'], 'electrico', R['vel_bala'], R['dist_bala'])


    def _ir_a_torre(b, ctx, torre):
        """Regieleki viaja a una torre dejando una linea electrica que lastima."""
        ahora = ctx['ahora']
        desde = b['rect'].center
        b['modo'], b['viaje'], b['escondido'] = 'viaje', torre, False
        b['lineas'].append({'a': desde, 'b': torre['obj']['rect'].center, 'hasta': ahora + REGIELEKI['linea']})


    def _salir_de_torre(b, ctx):
        """Regieleki deja la torre (rota si le pegaron) y pasa a otra; sin torres libres empieza a teletransportarse."""
        t = b['torre']
        if t['estado'] != 'rota': t['estado'] = 'gris'; t['obj']['color'] = COLOR_TORRE['gris']
        libres = [o for o in b['torres'] if o['estado'] == 'gris' and o is not t]
        if not libres:
            if t['estado'] == 'gris': t['estado'] = 'cargada'; t['obj']['color'] = COLOR_TORRE['cargada']; t['entro'] = ctx['ahora']; return
            b['torre'], b['modo'], b['escondido'] = None, 'tele', False
            b['prox']['tele'] = ctx['ahora']; b['prox']['jaula'] = ctx['ahora'] + REGIELEKI['primera_jaula']
            _rayos5(b, ctx)
            return
        b['torre'] = None
        _rayos5(b, ctx)
        _ir_a_torre(b, ctx, random.choice(libres))


    def _jaula_voltio(b, ctx):
        """Jaula Voltio: un cuadrado electrico alrededor del jugador. Lastima si lo tocas y se rompe con 2 ataques."""
        ent, j, ahora, R = ctx['ent'], ctx['jugador'], ctx['ahora'], REGIELEKI
        cx, cy = j['rect'].center
        m, g = R['lado_jaula'] // 2, R['grosor_jaula']
        lados = (pygame.Rect(cx - m, cy - m, 2 * m, g), pygame.Rect(cx - m, cy + m - g, 2 * m, g),
                 pygame.Rect(cx - m, cy - m, g, 2 * m), pygame.Rect(cx + m - g, cy - m, g, 2 * m))
        b['jaula'] = {'piezas': [entorno.poner_barrera(ent, 'jaula_voltio', r) for r in lados], 'golpes': 0, 'hasta': ahora + R['dura_jaula'], 'prox': 0, 'nace': ahora}
        ctx['impacto'](cx, cy, 60, 150)


    def _actualizar_jaula(b, ctx):
        """Cuenta los golpes que le das a la jaula (cualquier lado) y la saca cuando se rompe o se le acaba el tiempo."""
        ent, j, ahora, R = ctx['ent'], ctx['jugador'], ctx['ahora'], REGIELEKI
        jaula = b['jaula']
        if not jaula: return
        golpeada = False
        for o in jaula['piezas']:
            if o['vida'] < o['max_vida']: golpeada = True
            o['vida'] = o['max_vida']
        if golpeada: jaula['golpes'] += 1
        if ahora >= jaula['prox'] and any(j['rect'].inflate(8, 8).colliderect(o['rect']) for o in jaula['piezas']):
            ctx['dañar_jugador'](b['daño'] * R['daño_jaula'], 'electrico'); jaula['prox'] = ahora + 500
        if jaula['golpes'] >= R['golpes_jaula'] or ahora >= jaula['hasta']:
            for o in jaula['piezas']:
                if o in ent['objetos']: ent['objetos'].remove(o)
            ent['version'] += 1
            ctx['impacto'](*j['rect'].center, 80, 200 if jaula['golpes'] >= R['golpes_jaula'] else 0)
            b['jaula'] = None


    def actualizar_regieleki(b, ctx):
        """Regieleki: rafagas de 5 rayos; con 3/4 de vida se esconde en torres (pegarle a la torre le pega a el);
        sin torres se teletransporta y suelta ondas electricas."""
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
            if daño > 0 and t is b['torre'] and b['modo'] == 'torre' and t['estado'] == 'cargada':
                b['vida'] -= daño; t['golpes'] += 1
                if t['golpes'] >= R['golpes_torre']: t['estado'] = 'rota'; o['color'] = COLOR_TORRE['rota']
            o['vida'] = o['max_vida']
        b['lineas'] = [l for l in b['lineas'] if ahora < l['hasta']]
        if ahora >= b['prox_linea'] and any(_dist_segmento((jx, jy), l['a'], l['b']) <= R['ancho_linea'] + mitad for l in b['lineas']):
            ctx['dañar_jugador'](b['daño'] * R['daño_linea'], 'electrico'); b['prox_linea'] = ahora + 500
        for o in b['ondas'][:]:
            if ahora >= o['hasta']: b['ondas'].remove(o); continue
            if ahora < o['inicio']: continue
            radio = R['radio_onda'] * (ahora - o['inicio']) / R['onda']
            if not o['pego'] and abs(math.hypot(jx - o['pos'][0], jy - o['pos'][1]) - radio) <= 22 + mitad:
                ctx['dañar_jugador'](b['daño'] * R['daño_onda'], 'electrico'); o['pego'] = True
        a = b['aviso']
        if a and ahora >= a['hasta']: b['aviso'] = None; _rayos5(b, ctx)
        _actualizar_jaula(b, ctx)
        if b['modo'] == 'tele' and not b['jaula'] and ahora >= p.get('jaula', 0):
            p['jaula'] = ahora + R['jaula']; _jaula_voltio(b, ctx)
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
                t.update(estado='cargada', entro=ahora); t['obj']['color'] = COLOR_TORRE['cargada']
                b['modo'], b['viaje'], b['escondido'] = 'torre', None, True
                b['aviso'] = {'hasta': ahora + R['aviso_rayos'], 'clase': 'rafaga', 'inicio': ahora, 'mira': (jx, jy)}
            else: b['rect'].center = (round(bx + (tx - bx) / d * R['vel_viaje']), round(by + (ty - by) / d * R['vel_viaje']))
        elif b['modo'] == 'torre':
            t = b['torre']
            if (t['estado'] == 'rota' and ahora - t['entro'] >= R['cambio']) or ahora - t['entro'] >= R['quedarse']: _salir_de_torre(b, ctx)
        elif ahora >= p['tele']:                                    # sin torres: se teletransporta con alto voltaje
            p['tele'] = ahora + R['tele']
            b['rect'].center = entorno.punto_libre(ent, random, (jx, jy), 220)
            for espera in (0, R['segunda_onda']):
                b['ondas'].append({'pos': b['rect'].center, 'inicio': ahora + espera, 'hasta': ahora + espera + R['onda'], 'pego': False})
            ctx['impacto'](*b['rect'].center, 60, 150)
        b['vida_guardada'] = b['vida']
        b['fase'] = 1 if b['modo'] == 'libre' else 3 if b['modo'] == 'tele' else 2


    # ---------- Regidrago ----------

    def _dash_regidrago(b, ctx):
        """Enfado: como Fuerza Bruta pero no se aturde, y va dejando fuego."""
        ent, j = ctx['ent'], ctx['jugador']
        R, d = REGIDRAGO, b['dash']
        paso = min(R['vel_enfado'], d['restante'])
        d['resto'][0] += d['dir'][0] * paso; d['resto'][1] += d['dir'][1] * paso
        px, py = int(d['resto'][0]), int(d['resto'][1])
        d['resto'][0] -= px; d['resto'][1] -= py
        quiero = b['rect'].move(px, py)
        entorno.mover(ent, b['rect'], px, py, [b['tipo']])
        d['restante'] -= paso; d['fuego'] -= paso
        if d['fuego'] <= 0:
            d['fuego'] = R['fuego_cada']
            entorno.encender(ent, *entorno.casilla(ent, *b['rect'].center))
        if not d['pego'] and _en_franja(b, j, R['ancho_enfado']): ctx['dañar_jugador'](b['daño'] * R['daño_enfado'], 'dragon'); d['pego'] = True
        if (px or py) and b['rect'].topleft != quiero.topleft: ctx['impacto'](*b['rect'].center, 90, 300); b['dash'] = None
        elif d['restante'] <= 0: b['dash'] = None


    def _cometa(b, ctx, puntos):
        primero = ctx['ahora'] + REGIDRAGO['aviso_cometa']
        b['cometas'].append({'puntos': [{'pos': p, 'cae': primero + i * REGIDRAGO['cada_meteoro'], 'cayo': False} for i, p in enumerate(puntos)], 'inicio': ctx['ahora']})


    def _cometa_torre(b, ctx):
        """Banda de meteoritos de punta a punta de la torre, a la altura donde estas."""
        R, plat, j = REGIDRAGO, b['plataforma'], ctx['jugador']
        y = max(plat.top + R['radio_meteoro'] // 2, min(plat.bottom - R['radio_meteoro'] // 2, j['rect'].centery))
        xs = list(range(plat.left + R['radio_meteoro'] // 2, plat.right, R['paso_meteoro']))
        if random.random() < 0.5: xs.reverse()
        _cometa(b, ctx, [(x, y) for x in xs])


    def _cometa_suelo(b, ctx):
        """Banda de meteoritos que pasa por donde estas, en cualquier direccion."""
        R, (jx, jy) = REGIDRAGO, ctx['jugador']['rect'].center
        ang = random.uniform(0, math.tau)
        n = R['largo_cometa'] // R['paso_meteoro']
        _cometa(b, ctx, [(jx + math.cos(ang) * (i - n / 2) * R['paso_meteoro'], jy + math.sin(ang) * (i - n / 2) * R['paso_meteoro']) for i in range(n + 1)])


    def _actualizar_cometas(b, ctx):
        j, ahora, R = ctx['jugador'], ctx['ahora'], REGIDRAGO
        for c in b['cometas'][:]:
            for m in c['puntos']:
                if m['cayo'] or ahora < m['cae']: continue
                m['cayo'] = True
                x, y = m['pos']
                if math.hypot(j['rect'].centerx - x, j['rect'].centery - y) <= R['radio_meteoro'] + max(j['rect'].size) / 2: ctx['dañar_jugador'](b['daño'] * R['daño_meteoro'], 'dragon')
                ctx['impacto'](x, y, R['radio_meteoro'], 120)
            if all(m['cayo'] for m in c['puntos']): b['cometas'].remove(c)


    def _boca(b, ctx, pos):
        boca = {'pos': pos, 'prox': ctx['ahora'] + 600, 'disparos': REGIDRAGO['disparos_boca'], 'mira': None, 'hasta': 0, 'nace': ctx['ahora']}
        if b['fase'] == 3:                                          # en la tercera fase se les puede pegar
            vida = max(1, round(b['max_vida'] * REGIDRAGO['vida_boca']))
            r = pygame.Rect(0, 0, 64, 64); r.center = (round(pos[0]), round(pos[1]))
            boca.update(rect=r, vida=vida, max_vida=vida, tipo='dragon', atacable=True, de_jefe=True, estado=None, estado_hasta=0, proximo_estado=0)
        b['bocas'].append(boca)


    def _boca_torre(b, ctx):
        """Las bocas salen del vacio alrededor de la torre (arriba o a los costados)."""
        plat = b['plataforma']
        lado = random.choice(('arriba', 'arriba', 'izq', 'der'))
        if lado == 'arriba': pos = (random.randint(plat.left + 60, plat.right - 60), plat.top - 90)
        else: pos = (plat.left - 100 if lado == 'izq' else plat.right + 100, random.randint(plat.top + 40, plat.bottom - 40))
        _boca(b, ctx, pos)


    def _actualizar_bocas(b, ctx):
        """Cada boca apunta a un punto (en la torre, o cerca tuyo) y tira Dragoaliento: 3 llamaradas en abanico."""
        j, ahora, R = ctx['jugador'], ctx['ahora'], REGIDRAGO
        jx, jy = j['rect'].center
        for boca in b['bocas'][:]:
            if boca.get('atacable'):
                if boca['vida'] <= 0: b['bocas'].remove(boca); ctx['impacto'](*boca['rect'].center, 50, 150); continue
                boca['pos'] = boca['rect'].center                   # por si la empujo un golpe
            x, y = boca['pos']
            if boca['mira'] and ahora >= boca['hasta']:
                base = math.atan2(boca['mira'][1] - y, boca['mira'][0] - x)
                for k in (-1, 0, 1):
                    ang = base + k * R['abanico_aliento']
                    ctx['disparar'](x, y, math.cos(ang), math.sin(ang), b['daño'] * R['daño_aliento'], 'dragon', R['vel_aliento'], R['dist_aliento'], R['tam_aliento'])
                boca['mira'], boca['prox'] = None, ahora + R['cada_boca']
                boca['disparos'] -= 1
                if boca['disparos'] <= 0: b['bocas'].remove(boca)
            elif not boca['mira'] and ahora >= boca['prox']:
                plat = b['plataforma']
                boca['mira'] = (random.randint(plat.left, plat.right), random.randint(plat.top, plat.bottom)) if plat else (jx + random.randint(-140, 140), jy + random.randint(-140, 140))
                boca['hasta'] = ahora + R['aviso_boca']


    def _empezar_draco(b, ctx, volver):
        """Draco Energia: se queda quieto y no recibe daño; carga 2 s y despues un rayo que te sigue 10 s."""
        j, ahora, R = ctx['jugador'], ctx['ahora'], REGIDRAGO
        bx, by = b['rect'].center
        b.update(etapa='draco', invulnerable=volver, sin_estados=True, aviso=None, dash=None)   # en la tercera fase se le puede pegar
        if volver: b['bocas'] = []
        b['draco'] = {'inicio': ahora, 'dispara': ahora + R['carga_draco'], 'fin': ahora + R['carga_draco'] + R['dura_draco'], 'prox': 0, 'volver': volver,
                      'ang': math.atan2(j['rect'].centery - by, j['rect'].centerx - bx)}


    def _actualizar_draco(b, ctx):
        j, ahora, R = ctx['jugador'], ctx['ahora'], REGIDRAGO
        d = b['draco']
        bx, by = b['rect'].center
        px, py = _pos_anterior(b, j, ahora, R['retraso_draco'])      # apunta a donde estabas: se puede esquivar
        quiero = math.atan2(py - by, px - bx)
        if ahora < d['dispara']: d['ang'] = quiero; return
        d['ang'] = _girar_hacia(d['ang'], quiero, R['giro_draco'])
        d['fin_rayo'] = (bx + math.cos(d['ang']) * R['largo_draco'], by + math.sin(d['ang']) * R['largo_draco'])
        if ahora >= d['prox'] and _dist_segmento(j['rect'].center, (bx, by), d['fin_rayo']) <= R['ancho_draco'] + max(j['rect'].size) / 2:
            ctx['dañar_jugador'](b['daño'] * R['daño_draco'], 'dragon'); d['prox'] = ahora + R['tick_draco']
        if ahora < d['fin']: return
        b.update(draco=None, invulnerable=False)
        if d['volver']:                                             # se rompe la torre
            b.update(etapa='rompe', fin_etapa=ahora + R['rompe'], fundido=(ahora, ahora + R['rompe'], True))
            ctx['impacto'](bx, by, 300, R['rompe'])
        else:
            b.update(etapa='suelo', sin_estados=False); b['prox']['draco'] = ahora + R['draco']


    def subir_regidrago(b, plataforma, ahora):
        """Ya estan arriba de la torre: Regidrago flota delante, moviendose de un lado al otro."""
        R = REGIDRAGO
        b.update(plataforma=plataforma, etapa='torre', fase=2, invulnerable=False, sin_contacto=True, sin_estados=True, cometas=[], bocas=[],
                 inicio_torre=ahora, fundido=(ahora, ahora + R['fundido'], False), centro_torre=(plataforma.centerx, plataforma.bottom + b['rect'].height // 2 + 10))
        b['rect'].center = b['centro_torre']
        b['prox'].update(cometa=ahora + 1800, boca=ahora + 1000)


    def bajar_regidrago(b, centro, ahora):
        """La torre se rompio: de vuelta en la sala, tercera fase."""
        R = REGIDRAGO
        b['rect'].center = centro
        b.update(plataforma=None, etapa='suelo', fase=3, invulnerable=False, sin_contacto=False, sin_estados=False, cometas=[], bocas=[],
                 fundido=(ahora, ahora + R['fundido'], False))
        b['prox'].update(enfado=ahora + 2500, cometa=ahora + 1500, boca=ahora + 3500, draco=ahora + R['primer_draco'])


    def alfa_fundido(b, ahora):
        """Pantalla blanca al subir y al romperse la torre."""
        if not b.get('fundido'): return 0
        inicio, fin, sube = b['fundido']
        k = max(0.0, min(1.0, (ahora - inicio) / max(1, fin - inicio)))
        if not sube and k >= 1: b['fundido'] = None
        return round(255 * (k if sube else 1 - k))


    def actualizar_regidrago(b, ctx):
        ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
        jx, jy = j['rect'].center
        bx, by = b['rect'].center
        R, p = REGIDRAGO, b['prox']
        _rastrear(b, j, ahora)
        if b['etapa'] is None: b['etapa'] = 'suelo'; p.update(enfado=ahora + 2500)
        if b['invulnerable']: b['vida'] = b['vida_guardada']
        if b['fase'] == 1: b['vida'] = max(b['vida'], b['max_vida'] * R['fases'][0])        # cada fase se juega entera
        elif b['fase'] == 2: b['vida'] = max(b['vida'], b['max_vida'] * R['fases'][1])
        b['vida_guardada'] = b['vida']
        _actualizar_cometas(b, ctx)
        _actualizar_bocas(b, ctx)
        etapa = b['etapa']
        if etapa == 'draco': _actualizar_draco(b, ctx); return
        if etapa == 'rompe':
            if ahora >= b['fin_etapa']: b['etapa'], b['pedido'] = 'esperando', 'bajar'
            return
        if etapa == 'esperando': return
        if etapa == 'mordida':
            if b['aviso']:
                if ahora < b['aviso']['hasta']: return
                b['aviso'] = None
            dx, dy = _dir((bx, by), (jx, jy))
            b['rect'].center = (round(bx + dx * R['vel_mordida']), round(by + dy * R['vel_mordida']))
            if b['rect'].colliderect(j['rect']) or ahora >= b['mordida']:
                ctx['dañar_jugador'](b['daño'] * R['daño_mordida'], 'dragon'); ctx['impacto'](jx, jy, 60, 300)
                b.update(etapa='subida', fin_etapa=ahora + R['subida'], fundido=(ahora, ahora + R['subida'], True), sin_contacto=True)
                j['atrapado_hasta'] = ahora + 10 ** 7
            return
        if etapa == 'subida':                                       # te lleva en la boca y sube
            b['rect'].y -= 2
            j['rect'].center = (b['rect'].centerx, b['rect'].centery + 30)
            if ahora >= b['fin_etapa']: b['etapa'], b['pedido'] = 'esperando', 'subir'
            return
        if etapa == 'torre':
            b['rect'].centerx = round(b['centro_torre'][0] + math.sin((ahora - b['inicio_torre']) / R['periodo']) * R['vaiven'])
            if b['vida'] <= b['max_vida'] * R['fases'][1]: _empezar_draco(b, ctx, True); return
            if ahora >= p['cometa']: p['cometa'] = ahora + R['cometa']; _cometa_torre(b, ctx)
            if ahora >= p['boca'] and len(b['bocas']) < R['max_bocas']: p['boca'] = ahora + R['boca']; _boca_torre(b, ctx)
            return
        if b['fase'] == 1 and b['vida'] <= b['max_vida'] * R['fases'][0]:   # 75%: te muerde
            b.update(etapa='mordida', invulnerable=True, sin_estados=True, dash=None, cometas=[], mordida=ahora + R['aviso_mordida'] + R['dura_mordida'])
            b['aviso'] = {'hasta': ahora + R['aviso_mordida'], 'clase': 'mordida', 'inicio': ahora}
            return
        if b['dash']: _dash_regidrago(b, ctx); return
        a = b['aviso']
        if a:
            if ahora < a['hasta']: return
            b['aviso'] = None
            b['dash'] = {'dir': a['dir'], 'restante': R['largo_enfado'], 'pego': False, 'resto': [0.0, 0.0], 'fuego': R['fuego_cada'] // 2}
            return
        if b['fase'] == 3:
            if ahora >= p['draco']: _empezar_draco(b, ctx, False); return
            if ahora >= p['cometa']: p['cometa'] = ahora + R['cometa']; _cometa_suelo(b, ctx)
            if ahora >= p['boca'] and len(b['bocas']) < R['max_bocas']:
                p['boca'] = ahora + R['boca']; _boca(b, ctx, entorno.punto_libre(ent, random, (jx, jy), 300))
        if ahora >= p['enfado']:
            p['enfado'] = ahora + R['enfado']
            b['aviso'] = {'hasta': ahora + R['aviso_enfado'], 'clase': 'enfado', 'inicio': ahora, 'dir': _dir((bx, by), (jx, jy)),
                          'largo': R['largo_enfado'], 'ancho': R['ancho_enfado']}; return
        if math.hypot(jx - bx, jy - by) > 260: _ir_a(ent, b, (jx, jy), R['vel'], [])


    def actualizar_jefe(b, ctx):
        """Te sigue por el mapa de flujo, tira rafagas en abanico apuntadas y si estas cerca pisotea (todo avisado)."""
        if b['estilo'] == 'regigigas': actualizar_regigigas(b, ctx); return
        if b['estilo'] == 'beta': actualizar_beta(b, ctx); return
        if b['estilo'] == 'arceus': actualizar_arceus(b, ctx); return
        if b['estilo'] == 'regice': actualizar_regice(b, ctx); return
        if b['estilo'] == 'regirock': actualizar_regirock(b, ctx); return
        if b['estilo'] == 'registeel': actualizar_registeel(b, ctx); return
        if b['estilo'] == 'regieleki': actualizar_regieleki(b, ctx); return
        if b['estilo'] == 'regidrago': actualizar_regidrago(b, ctx); return
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


    def _dibujar_boca(ventana, pos, ang, abierta):
        """Cabeza de dragon de piedra, como la de Regidrago, mirando hacia ang."""
        x, y = pos
        p = lambda d, a: (x + math.cos(ang + a) * d, y + math.sin(ang + a) * d)
        abre = 0.25 + 0.35 * abierta
        pygame.draw.circle(ventana, (95, 75, 70), (round(x), round(y)), 30)
        pygame.draw.polygon(ventana, (200, 120, 45), [p(18, -1.1), p(62, -abre), p(40, -0.05), p(14, -0.2)])
        pygame.draw.polygon(ventana, (200, 120, 45), [p(18, 1.1), p(62, abre), p(40, 0.05), p(14, 0.2)])
        pygame.draw.polygon(ventana, (40, 25, 25), [p(14, -0.2), p(40, -0.05), p(40, 0.05), p(14, 0.2)])
        pygame.draw.circle(ventana, (40, 30, 30), (round(x), round(y)), 30, 3)
        for s in (-1, 1): pygame.draw.circle(ventana, (255, 70, 60), [round(v) for v in p(14, s * 0.9)], 5)


    def _dibujar_regidrago(ventana, e, x, y, cx, cy, ahora):
        R = REGIDRAGO
        W, H = ventana.get_size()
        for c in e['cometas']:                                      # banda roja y los meteoritos cayendo de a uno
            quedan = [m for m in c['puntos'] if not m['cayo']]
            if not quedan: continue
            velo = pygame.Surface((W, H), pygame.SRCALPHA)
            a0 = (quedan[0]['pos'][0] - cx, quedan[0]['pos'][1] - cy); a1 = (c['puntos'][-1]['pos'][0] - cx, c['puntos'][-1]['pos'][1] - cy)
            pygame.draw.line(velo, (230, 30, 30, 70), a0, a1, R['radio_meteoro'] * 2)
            for punta in (a0, a1): pygame.draw.circle(velo, (230, 30, 30, 70), [round(v) for v in punta], R['radio_meteoro'])
            ventana.blit(velo, (0, 0))
            for m in quedan:
                mx, my = round(m['pos'][0] - cx), round(m['pos'][1] - cy)
                k = max(0.0, min(1.0, 1 - (m['cae'] - ahora) / R['aviso_cometa']))
                pygame.draw.circle(ventana, (255, 60, 40), (mx, my), R['radio_meteoro'], 2)
                pygame.draw.circle(ventana, (255, 60, 40), (mx, my), max(1, round(R['radio_meteoro'] * k)), 2)
                falta = m['cae'] - ahora
                if falta < 450:
                    t = falta / 450
                    px, py = mx - 180 * t, my - 320 * t
                    pygame.draw.line(ventana, (255, 170, 60), (px - 60, py - 100), (px, py), 10)
                    pygame.draw.circle(ventana, (120, 60, 160), (round(px), round(py)), 22)
                    pygame.draw.circle(ventana, (255, 200, 90), (round(px), round(py)), 22, 4)
        for boca in e['bocas']:
            bx, by = boca['pos'][0] - cx, boca['pos'][1] - cy
            mira = boca['mira']
            ang = math.atan2(mira[1] - boca['pos'][1], mira[0] - boca['pos'][0]) if mira else math.atan2(y - by, x - bx) + math.pi
            if mira:
                k = max(0.0, min(1.0, 1 - (boca['hasta'] - ahora) / R['aviso_boca']))
                pygame.draw.line(ventana, (170, 90, 255), (bx, by), (mira[0] - cx, mira[1] - cy), 1 + round(4 * k))
                pygame.draw.circle(ventana, (170, 90, 255), (round(mira[0] - cx), round(mira[1] - cy)), 18, 2)
            _dibujar_boca(ventana, (bx, by), ang, 1.0 if mira else 0.2)
            if boca.get('atacable'):
                pygame.draw.rect(ventana, (60, 0, 0), (bx - 30, by - 44, 60, 5))
                pygame.draw.rect(ventana, (230, 200, 40), (bx - 30, by - 44, round(60 * max(0, boca['vida']) / boca['max_vida']), 5))
        d = e['draco']
        if d:
            if ahora < d['dispara']:                                # carga: anillos que se cierran
                k = (ahora - d['inicio']) / R['carga_draco']
                for i in range(3):
                    r = round(140 * (1 - ((k * 3 + i / 3) % 1)) + 20)
                    pygame.draw.circle(ventana, (190, 80, 255), (x, y), r, 3)
                pygame.draw.circle(ventana, (255, 170, 255), (x, y), round(10 + 40 * k))
                pygame.draw.line(ventana, (190, 80, 255), (x, y), (x + math.cos(d['ang']) * R['largo_draco'], y + math.sin(d['ang']) * R['largo_draco']), 1)
            elif d.get('fin_rayo'):
                fin = (d['fin_rayo'][0] - cx, d['fin_rayo'][1] - cy)
                ancho = R['ancho_draco'] + round(math.sin(ahora / 40) * 6)
                pygame.draw.line(ventana, (130, 40, 210), (x, y), fin, ancho * 2)
                pygame.draw.line(ventana, (255, 190, 255), (x, y), fin, ancho)
                pygame.draw.circle(ventana, (255, 220, 255), (x, y), ancho)


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
                elif a['clase'] == 'hiperrayo':                     # franja del ancho de Arceus hacia donde va a salir el rayo, cada vez mas marcada
                    fx, fy = a['fin'][0] - cx, a['fin'][1] - cy
                    velo = pygame.Surface(ventana.get_size(), pygame.SRCALPHA)
                    pygame.draw.line(velo, (255, 240, 180, 50 + round(110 * k)), (x, y), (fx, fy), max(2, round(a['ancho'] * 2 * k)))
                    ventana.blit(velo, (0, 0))
                    pygame.draw.line(ventana, (255, 90, 40), (x, y), (fx, fy), 2)
                    pygame.draw.circle(ventana, (255, 250, 220), (x, y), round(10 + 30 * k), 3)
                elif a['clase'] == 'vozarron':                      # Arceus junta aire: 3 anillos que laten alrededor suyo
                    for i in range(3):
                        pygame.draw.circle(ventana, (255, 245, 210), (x, y), round(max(e['rect'].size) / 2 + 10 + i * 18 + 14 * k), 3)
                elif a['clase'] == 'rayo_hielo':                    # linea celeste fija que se va engrosando (con los rebotes)
                    puntos = [(px - cx, py - cy) for px, py in a.get('puntos', ((e['rect'].centerx, e['rect'].centery), a['fin']))]
                    pygame.draw.lines(ventana, (200, 240, 255), False, puntos, 2 + round(REGICE['ancho_rayo'] * k * 0.8))
                    pygame.draw.lines(ventana, (60, 140, 230), False, puntos, 2)
                elif a['clase'] == 'avalancha':                     # junta las rocas para tirarlas
                    for i in range(6):
                        ang = ahora / 150 + i * math.tau / 6
                        pygame.draw.circle(ventana, (140, 115, 80), (round(x + math.cos(ang) * 70), round(y - 40 + math.sin(ang) * 25)), round(8 + 10 * k))
                elif a['clase'] == 'foco':                          # Foco Resplandor cargando
                    mx, my = a['mira'][0] - cx, a['mira'][1] - cy
                    pygame.draw.line(ventana, (230, 235, 255), (x, y), (mx, my), 1 + round(3 * k))
                    pygame.draw.circle(ventana, (230, 235, 255), (x, y), round(10 + 30 * k), 3)
                elif a['clase'] == 'agarre':                        # manos que se abren alrededor de Regigigas
                    radio = GIGAS['radio_agarre']
                    pygame.draw.circle(ventana, (255, 150, 40), (x, y), radio, 3)
                    for i in range(2):
                        ang = math.pi * i + ahora / 300
                        pygame.draw.circle(ventana, (255, 200, 120), (round(x + math.cos(ang) * radio * (1 - 0.4 * k)), round(y + math.sin(ang) * radio * (1 - 0.4 * k))), 18, 4)
                elif a['clase'] == 'roca_afilada':                  # por donde van a salir las rocas
                    for i in range(1, REGIROCK['largo_roca'] + 1, 2):
                        d = max(e['rect'].size) / 2 + i * REGIROCK['paso_roca']
                        pygame.draw.circle(ventana, (150, 110, 60), (round(x + a['dir'][0] * d), round(y + a['dir'][1] * d)), 6, 2)
                elif a['clase'] == 'mordida':                       # colmillos que se cierran
                    r = max(e['rect'].size) // 2 + 40
                    pygame.draw.circle(ventana, (255, 50, 40), (x, y), round(r * (1.3 - 0.3 * k)), 4)
                    for lado in (-1, 1):
                        for i in (-1, 0, 1):
                            bx_ = x + i * 26
                            by_ = y + lado * (r * (1 - 0.7 * k))
                            pygame.draw.polygon(ventana, (255, 240, 230), [(bx_ - 10, by_), (bx_ + 10, by_), (bx_, by_ - lado * 26)])
                elif a['clase'] in ('fuerza_bruta', 'enfado', 'gigaimpacto', 'velocidad_extrema'):   # franja roja por donde va a embestir
                    W, H = ventana.get_size()
                    velo = pygame.Surface((W, H), pygame.SRCALPHA)
                    largo, ancho = a.get('largo', REGIROCK['largo_fuerza']), a.get('ancho', REGIROCK['ancho_fuerza'])
                    fin = (x + a['dir'][0] * largo, y + a['dir'][1] * largo)
                    pygame.draw.line(velo, (230, 30, 30, 70 + round(90 * k)), (x, y), fin, ancho)
                    pygame.draw.circle(velo, (230, 30, 30, 70 + round(90 * k)), (round(fin[0]), round(fin[1])), ancho // 2)
                    ventana.blit(velo, (0, 0))
                    pygame.draw.line(ventana, (255, 60, 40), (x, y), fin, 2)
                elif a['clase'] == 'sentencia':                     # el sello de Arceus (tipo normal) y al final una columna de luz que baja del cielo
                    centro = (round(a['mira'][0] - cx), round(a['mira'][1] - cy))
                    dibujar_sello(ventana, centro, a['radio'], (colores or {}).get(a['tipo'], (255, 255, 255)), k, ahora)
                    if k > 0.7:
                        caida = (k - 0.7) / 0.3
                        pygame.draw.line(ventana, (255, 250, 225), (centro[0], centro[1] - 600), (centro[0], centro[1] - round(600 * (1 - caida))), round(4 + a['radio'] * 0.3 * caida))
            for m in e.get('meteoros', ()):                         # Meteoros: sombra que se llena y el meteorito que baja en diagonal
                if m['pos'] is None: continue
                k = min(1.0, (ahora - m['inicio']) / max(1, m['hasta'] - m['inicio']))
                mx, my = round(m['pos'][0] - cx), round(m['pos'][1] - cy)
                radio = ARCEUS['radio_meteoro']
                pygame.draw.circle(ventana, (60, 40, 30), (mx, my), max(1, round(radio * k)))
                pygame.draw.circle(ventana, (255, 120, 50), (mx, my), radio, 2)
                if k > 0.45:
                    v = (k - 0.45) / 0.55
                    px, py = mx + 280 * (1 - v), my - 460 * (1 - v)
                    pygame.draw.line(ventana, (255, 200, 120), (px + 60, py - 100), (px, py), 6)
                    pygame.draw.circle(ventana, (255, 150, 60), (round(px), round(py)), 17)
                    pygame.draw.circle(ventana, (255, 240, 200), (round(px), round(py)), 8)
            for o in e.get('vozarron', ()):                         # Vozarron: circulos que se agrandan
                if ahora < o['inicio']: continue
                radio = round(ARCEUS['radio_vozarron'] * (ahora - o['inicio']) / ARCEUS['dura_vozarron'])
                if radio > 4:
                    centro = (round(o['pos'][0] - cx), round(o['pos'][1] - cy))
                    pygame.draw.circle(ventana, (200, 190, 150), centro, radio, ARCEUS['grosor_vozarron'] // 2)
                    pygame.draw.circle(ventana, (255, 250, 230), centro, radio, 3)
            r = e.get('recupera')
            if r:                                                   # Recuperacion: estrellitas que llegan hasta Arceus y un anillo que se llena
                k = min(1.0, (ahora - r['inicio']) / max(1, r['hasta'] - r['inicio']))
                radio = max(e['rect'].size) // 2 + 24
                for i in range(10):
                    v = ((ahora / 900) + i / 10) % 1
                    ang = i * math.tau / 10 + ahora / 1500
                    sx, sy = x + math.cos(ang) * (radio + 110 * (1 - v)), y + math.sin(ang) * (radio + 110 * (1 - v))
                    largo = 4 + 4 * v
                    pygame.draw.line(ventana, (255, 240, 120), (sx - largo, sy), (sx + largo, sy), 2)
                    pygame.draw.line(ventana, (255, 240, 120), (sx, sy - largo), (sx, sy + largo), 2)
                pygame.draw.circle(ventana, (120, 110, 60), (x, y), radio, 3)
                pygame.draw.arc(ventana, (255, 240, 140), pygame.Rect(x - radio, y - radio, radio * 2, radio * 2), math.pi / 2, math.pi / 2 + math.tau * k, 5)
            haz = e.get('haz')
            if haz:
                puntos = [(px - cx, py - cy) for px, py in haz.get('puntos', (haz.get('desde'), haz.get('fin')))]
                ancho = haz.get('ancho', 30)
                afuera, adentro = haz.get('color', ((255, 200, 80), (255, 255, 240)))
                if haz.get('tick'): ancho += round(math.sin(ahora / 50) * 4)
                pygame.draw.lines(ventana, afuera, False, puntos, ancho * 2)
                pygame.draw.lines(ventana, adentro, False, puntos, ancho)
                for p_ in puntos[1:-1]: pygame.draw.circle(ventana, adentro, [round(v) for v in p_], ancho)   # que los rebotes no se corten
            f = e.get('foco')
            if f and f.get('fin'):                                  # Foco Resplandor
                fin = (f['fin'][0] - cx, f['fin'][1] - cy)
                ancho = REGISTEEL['ancho_foco'] + round(math.sin(ahora / 40) * 4)
                pygame.draw.line(ventana, (150, 160, 200), (x, y), fin, ancho * 2)
                pygame.draw.line(ventana, (245, 248, 255), (x, y), fin, ancho)
            for st in e.get('estalactitas', ()):                    # sombra que crece y la estalactita que cae
                k = min(1.0, (ahora - st['inicio']) / max(1, st['hasta'] - st['inicio']))
                sx, sy = round(st['pos'][0] - cx), round(st['pos'][1] - cy)
                radio = REGICE['radio_estalactita']
                pygame.draw.circle(ventana, (40, 70, 110), (sx, sy), max(1, round(radio * k)))
                pygame.draw.circle(ventana, (150, 210, 255), (sx, sy), radio, 2)
                if k > 0.55:
                    yy = sy - round(400 * (1 - k) / 0.45)
                    pygame.draw.polygon(ventana, (210, 240, 255), [(sx - 14, yy - 46), (sx + 14, yy - 46), (sx, yy)])
                    pygame.draw.polygon(ventana, (90, 150, 210), [(sx - 14, yy - 46), (sx + 14, yy - 46), (sx, yy)], 2)
            if e.get('coraza'):                                     # coraza de hielo de Regice
                radio = max(e['rect'].size) // 2 + 18
                puntos = [(x + math.cos(ahora / 900 + i * math.tau / 6) * radio, y + math.sin(ahora / 900 + i * math.tau / 6) * radio) for i in range(6)]
                velo = pygame.Surface(ventana.get_size(), pygame.SRCALPHA)
                pygame.draw.polygon(velo, (170, 225, 255, 70), puntos)
                ventana.blit(velo, (0, 0))
                pygame.draw.polygon(ventana, (210, 245, 255), puntos, 4)
            for c in e.get('caidas', ()):                           # rocas de la avalancha volando hacia el hexagono
                k = min(1.0, (ahora - c['inicio']) / max(1, c['hasta'] - c['inicio']))
                tx, ty = round(c['pos'][0] - cx), round(c['pos'][1] - cy)
                radio = REGIROCK['radio_avalancha']
                pygame.draw.circle(ventana, (70, 50, 35), (tx, ty), max(1, round(radio * k)))
                pygame.draw.circle(ventana, (255, 60, 40), (tx, ty), radio, 2)
                ox, oy = c['desde'][0] - cx, c['desde'][1] - cy
                rx, ry = ox + (tx - ox) * k, oy + (ty - oy) * k - math.sin(k * math.pi) * 220
                pygame.draw.circle(ventana, (140, 115, 80), (round(rx), round(ry)), 22)
                pygame.draw.circle(ventana, (60, 45, 30), (round(rx), round(ry)), 22, 3)
            for r in e.get('rodantes', ()):                         # las 5 rocas de Regirock
                pos = (r['rect'].centerx - cx, r['rect'].centery - cy)
                radio = r['rect'].width // 2
                if r['explota'] is not None:
                    k = 1 - (r['explota'] - ahora) / REGIROCK['espera_explosion']
                    pygame.draw.circle(ventana, (255, 60, 40), pos, REGIROCK['radio_explosion'], 2)
                    pygame.draw.circle(ventana, (255, 60, 40), pos, max(1, round(REGIROCK['radio_explosion'] * k)), 2)
                color = (220, 60, 40) if r['explota'] is not None and (ahora // 90) % 2 else (140, 115, 80)
                pygame.draw.circle(ventana, color, pos, radio)
                ang = ahora / 120 * (1 if r['v'][0] >= 0 else -1)
                for i in range(3):
                    a_ = ang + i * math.tau / 3
                    pygame.draw.line(ventana, (70, 55, 40), pos, (pos[0] + math.cos(a_) * radio * 0.8, pos[1] + math.sin(a_) * radio * 0.8), 3)
                pygame.draw.circle(ventana, (60, 45, 30), pos, radio, 3)
                if r['vida'] > 0:
                    pygame.draw.rect(ventana, (60, 0, 0), (pos[0] - radio, pos[1] - radio - 10, radio * 2, 5))
                    pygame.draw.rect(ventana, (230, 200, 40), (pos[0] - radio, pos[1] - radio - 10, round(radio * 2 * r['vida'] / max(1, r['max_vida'])), 5))
            sal = e.get('salto')
            if sal and sal['etapa'] != 'sube':                      # sombra de Cuerpo Pesado
                radio = REGISTEEL['radio_pesado']
                k = 1 - e['altura'] / REGISTEEL['alto_salto']
                velo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                pygame.draw.circle(velo, (0, 0, 0, 60 + round(80 * k)), (radio, radio), max(8, round(radio * (0.3 + 0.7 * k))))
                ventana.blit(velo, (x - radio, y - radio))
                pygame.draw.circle(ventana, (255, 60, 40) if sal['etapa'] in ('quieto', 'cae') else (200, 200, 210), (x, y), radio, 3)
            jaula = e.get('jaula')
            if jaula:                                               # Jaula Voltio (cambia de color con cada golpe)
                color = ((255, 240, 80), (255, 150, 40))[min(1, jaula['golpes'])]
                for o in jaula['piezas']:
                    r = o['rect'].move(-cx, -cy)
                    pygame.draw.rect(ventana, (60, 50, 10), r)
                    azar = random.Random(ahora // 60 + r.x)
                    largo = max(r.size); vertical = r.height > r.width
                    puntos = [(r.centerx + (0 if vertical else -largo / 2 + largo * i / 8) + (azar.randint(-6, 6) if vertical else 0),
                               r.centery + (-largo / 2 + largo * i / 8 if vertical else 0) + (0 if vertical else azar.randint(-6, 6))) for i in range(9)]
                    pygame.draw.lines(ventana, color, False, puntos, 3)
                    pygame.draw.rect(ventana, color, r, 2)
            if e.get('lento_hasta') and not e.get('despierto'):     # Lento Inicio: defensa subida y un anillo que se llena
                k = 1 - max(0, e['lento_hasta'] - ahora) / GIGAS['lento']
                radio = max(e['rect'].size) // 2 + 30
                pygame.draw.circle(ventana, (120, 130, 160), (x, y), radio, 6)
                pygame.draw.arc(ventana, (240, 240, 255), pygame.Rect(x - radio, y - radio, radio * 2, radio * 2), math.pi / 2, math.pi / 2 + math.tau * k, 6)
                if fuente:
                    t = fuente.render('Lento Inicio', True, (230, 230, 245))
                    ventana.blit(t, t.get_rect(midbottom=(x, y - radio - 6)))
            if e.get('escudo_hasta', 0) > ahora:                    # Proteccion
                radio = max(e['rect'].size) // 2 + 26
                velo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                pygame.draw.circle(velo, (120, 255, 160, 70), (radio, radio), radio)
                ventana.blit(velo, (x - radio, y - radio))
                pygame.draw.circle(ventana, (200, 255, 210), (x, y), radio + round(math.sin(ahora / 80) * 3), 4)
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
            if e.get('iman_a') and e.get('iman_hasta', 0) > ahora:   # iman: violeta atrae, naranja aleja
                ix, iy = e['iman_a'][0] - cx, e['iman_a'][1] - cy
                aleja = e.get('iman_modo') == 'alejar'
                color = (255, 150, 60) if aleja else (170, 120, 255)
                for i in range(3):
                    k = ((ahora / 400) + i / 3) % 1
                    if aleja: k = 1 - k
                    pygame.draw.circle(ventana, color, (round(ix + (x - ix) * k), round(iy + (y - iy) * k)), 6, 2)
                pygame.draw.circle(ventana, color, (x, y), round(max(e['rect'].size) / 2 + 20 + math.sin(ahora / 100) * 8), 3)
            for l in e.get('lineas', ()):                           # camino de Regieleki entre torres
                pygame.draw.line(ventana, (255, 240, 80), (l['a'][0] - cx, l['a'][1] - cy), (l['b'][0] - cx, l['b'][1] - cy), REGIELEKI['ancho_linea'])
                pygame.draw.line(ventana, (255, 255, 220), (l['a'][0] - cx, l['a'][1] - cy), (l['b'][0] - cx, l['b'][1] - cy), 3)
            for o in e.get('ondas', ()):                            # alto voltaje
                radio = round(REGIELEKI['radio_onda'] * max(0, ahora - o['inicio']) / REGIELEKI['onda'])
                if radio > 2:
                    pygame.draw.circle(ventana, (255, 230, 50), (round(o['pos'][0] - cx), round(o['pos'][1] - cy)), radio, 6)
                    pygame.draw.circle(ventana, (255, 255, 200), (round(o['pos'][0] - cx), round(o['pos'][1] - cy)), radio, 2)
            if e.get('cometas') or e.get('bocas') or e.get('draco'): _dibujar_regidrago(ventana, e, x, y, cx, cy, ahora)
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
            alfa = alfa_fundido(e, ahora) if e.get('fundido') else 0
            if alfa:
                velo = pygame.Surface(ventana.get_size()); velo.fill((255, 255, 255)); velo.set_alpha(alfa)
                ventana.blit(velo, (0, 0))
            if e.get('grito', 0) > ahora and fuente:
                t = fuente.render('!', True, (255, 230, 40))
                ventana.blit(t, t.get_rect(midbottom=(x, e['rect'].top - cy - 10)))

    return SimpleNamespace(**locals())


ia = armar_ia()
