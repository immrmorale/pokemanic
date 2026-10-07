import pygame
import random
import math
import sys
from pokemones import pokemones, movimientos
from animaciones import direcciones, direccion_vector, AnimadorPokemon


def main():
    pygame.init()
    W, H = 1000, 600
    ventana = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Pokemanic')
    fuente = pygame.font.Font(None, 24)

    def debug_menu(pokemon):
        scroll = 0
        botones = []
        f_titulo = pygame.font.Font(None, 32)
        while True:
            columnas, bw, bh, bn, sy = 4, 210, 62, 28, 18
            filas = math.ceil(len(pokemones) / columnas)
            max_scroll = max(0, 80 + filas * (bh + bn + sy) - H)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'salir', pokemon
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_F1):
                    return pokemon, pokemon
                if e.type == pygame.MOUSEWHEEL:
                    scroll = max(0, min(scroll - e.y * 60, max_scroll))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for r, nombre in botones:
                        if r.collidepoint(e.pos):
                            return nombre, nombre

            ventana.fill((20, 20, 20))
            botones = []
            ventana.blit(f_titulo.render('MENU DEBUG', True, 'white'), (25, 15))
            ventana.blit(fuente.render('F1 o ESC para cerrar - rueda del mouse para desplazarte', True, (200, 200, 200)), (25, 45))
            for i, nombre in enumerate(pokemones):
                x = 30 + i % columnas * 240
                y = 85 + i // columnas * (bh + bn + sy) - scroll
                r = pygame.Rect(x, y, bw, bh)
                nr = pygame.Rect(x, y + bh, bw, bn)
                if r.bottom < 65 or nr.top > H:
                    continue
                pygame.draw.rect(ventana, (80, 160, 80) if nombre == pokemon else (200, 200, 200), r)
                pygame.draw.rect(ventana, (50, 50, 50), nr)
                ventana.blit(fuente.render(nombre.replace('_', ' ').title(), True, 'white'), (x + 8, y + 20))
                ventana.blit(fuente.render(nombre, True, 'white'), (x + 8, y + bh + 5))
                botones.append((r, nombre))
            pygame.display.flip()

    def jugar(pokemon):
        ESC = pygame.Rect(0, 0, 2400, 1600)
        PARED = 40
        AREA = ESC.inflate(-80, -80)
        VEL_ENEMIGO = 1
        VEL_P_ENEMIGO = 8
        DIST_P_ENEMIGO = 250
        DETECCION = 350
        DISPARO = 500
        DAÑOS = {'tirador': 5, 'melee': 10, 'grande': 25}
        CD_ENEMIGO, CD_JEFE, CD_PIEDRA = 1500, 5000, 2000
        DURACION_PIEDRA = 5000
        CANT_ENEMIGOS, CANT_PIEDRAS = 10, 30
        TAM_JEFE, BALAS_JEFE, PIEDRAS_POR_USO = 160, 24, 4
        DAÑO_JEFE, DAÑO_PIEDRA = 35, 15

        def mover(rect, dx, dy, piedras):
            r = rect.copy(); r.x += dx
            if not any(r.colliderect(p) for p in piedras): rect.x += dx
            r = rect.copy(); r.y += dy
            if not any(r.colliderect(p) for p in piedras): rect.y += dy

        def crear_piedras():
            piedras = []
            centro = pygame.Rect(ESC.centerx - 250, ESC.centery - 250, 500, 500)
            while len(piedras) < CANT_PIEDRAS:
                p = pygame.Rect(random.randint(PARED + 50, ESC.width - PARED - 100), random.randint(PARED + 50, ESC.height - PARED - 100), 50, 50)
                if p.colliderect(centro) or any(p.colliderect(x.inflate(15, 15)) for x in piedras):
                    continue
                piedras.append(p)
            return piedras

        def crear_puertas():
            return [
                pygame.Rect(ESC.centerx - 30, 0, 60, PARED),
                pygame.Rect(ESC.centerx - 30, ESC.bottom - PARED, 60, PARED),
                pygame.Rect(0, ESC.centery - 30, PARED, 60),
                pygame.Rect(ESC.right - PARED, ESC.centery - 30, PARED, 60)
            ]

        def stats_pokemon(nombre):
            datos = pokemones[nombre]
            s = datos.get('estadisticas_juego') or {}
            max_vida = int(datos.get('vida') or datos.get('vida_base') or s.get('vida') or 100)
            velocidad = float(s.get('velocidad', datos.get('velocidad_movimiento', datos.get('velocidad', 5))))
            tamaño = int(s.get('tamaño', datos.get('tamaño', 40)))
            hitbox = int(s.get('hitbox', datos.get('hitbox', tamaño)))
            return datos, max_vida, velocidad, tamaño, hitbox

        def crear_jugador(nombre, centro):
            nombre = nombre if nombre in pokemones else 'pikachu'
            datos, vida, velocidad, tamaño, hitbox = stats_pokemon(nombre)
            rect = pygame.Rect(0, 0, hitbox, hitbox)
            rect.center = centro
            return {'nombre': nombre, 'datos': datos, 'max_vida': vida, 'vida': vida, 'velocidad': velocidad, 'tamaño': tamaño,
                    'hitbox': hitbox, 'rect': rect, 'direccion': 'sur', 'moviendose': False, 'ultimo_golpe': -1000,
                    'ultimo_proyectil': -1000, 'atacando': False, 'llave': False, 'animador': AnimadorPokemon(nombre, rect, tamaño)}

        def cambiar_pokemon(j, nombre):
            if nombre not in pokemones: return
            centro = j['rect'].center
            nuevo = crear_jugador(nombre, centro)
            nuevo['llave'] = False
            j.clear(); j.update(nuevo)

        def reiniciar_jugador(j):
            datos, vida, velocidad, tamaño, hitbox = stats_pokemon(j['nombre'])
            j.update({'datos': datos, 'max_vida': vida, 'vida': vida, 'velocidad': velocidad, 'tamaño': tamaño, 'hitbox': hitbox,
                      'direccion': 'sur', 'moviendose': False, 'ultimo_golpe': -1000, 'ultimo_proyectil': -1000, 'atacando': False})
            j['rect'] = pygame.Rect(0, 0, hitbox, hitbox)
            j['rect'].center = ESC.center
            j['animador'] = AnimadorPokemon(j['nombre'], j['rect'], tamaño)

        def mover_jugador(j, piedras):
            t = pygame.key.get_pressed()
            dx, dy = t[pygame.K_d] - t[pygame.K_a], t[pygame.K_s] - t[pygame.K_w]
            j['moviendose'] = bool(dx or dy)
            if not j['moviendose']: return
            dirs = {(1,-1):'noreste',(1,1):'sureste',(-1,-1):'noroeste',(-1,1):'suroeste',(1,0):'este',(-1,0):'oeste',(0,-1):'norte',(0,1):'sur'}
            j['direccion'] = dirs[(dx, dy)]
            n = math.hypot(dx, dy)
            mover(j['rect'], dx / n * j['velocidad'], 0, piedras)
            mover(j['rect'], 0, dy / n * j['velocidad'], piedras)
            j['rect'].clamp_ip(AREA)

        def ataque(j, tipo):
            a = (j['datos'].get('ataques_estadisticas') or {}).get(tipo)
            if a is not None: return a
            nombre = j['datos'].get('ataque_cuerpo' if tipo == 'cuerpo' else 'ataque_proyectil')
            return movimientos.get(nombre)

        def atacar_cuerpo(j, objetivos):
            datos = ataque(j, 'cuerpo')
            if not datos: return
            ahora = pygame.time.get_ticks()
            if j['atacando'] or ahora - j['ultimo_golpe'] < datos.get('enfriamiento', 300): return
            j['ultimo_golpe'] = ahora; j['atacando'] = True
            anim = j['animador'].buscar_ataque()
            if anim: j['animador'].cambiar(anim, direcciones.index(j['direccion']), False)
            vx, vy = direccion_vector[j['direccion']]
            d, area = datos.get('distancia', 50), datos.get('area', 20)
            r = pygame.Rect(0, 0, d, area * 2); r.center = (round(j['rect'].centerx + vx * d / 2), round(j['rect'].centery + vy * d / 2))
            for objetivo in objetivos:
                if objetivo['vida'] > 0 and r.colliderect(objetivo['rect']):
                    recibir_ataque(objetivo, datos, j['direccion'])

        def atacar_proyectil(j, proyectiles):
            datos = ataque(j, 'proyectil')
            if not datos: return
            ahora = pygame.time.get_ticks()
            if j['atacando'] or ahora - j['ultimo_proyectil'] < datos.get('enfriamiento', 300): return
            j['ultimo_proyectil'] = ahora
            vx, vy = direccion_vector[j['direccion']]
            d = max(20, j['hitbox'] // 2)
            x, y = j['rect'].centerx + vx * d, j['rect'].centery + vy * d
            tamaño = max(2, datos.get('area', 8) * 2)
            proyectiles.append({'x': float(x), 'y': float(y), 'direccion': j['direccion'], 'datos': datos, 'rect': pygame.Rect(0,0,tamaño,tamaño), 'distancia': 0, 'activo': True, 'golpeados': []})

        def actualizar_jugador(j):
            a = j['animador']
            if j['atacando'] and a.esta_terminada(): j['atacando'] = False
            d = direcciones.index(j['direccion'])
            if j['atacando']:
                anim = a.buscar_ataque()
                if anim: a.cambiar(anim, d, False)
                else: j['atacando'] = False
            else: a.cambiar('walk' if j['moviendose'] else 'idle', d, True)
            a.actualizar()

        def dañar_jugador(j, daño):
            j['vida'] = max(0, j['vida'] - daño)

        def recibir_ataque(obj, datos, direccion=None):
            obj['vida'] = max(0, obj['vida'] - datos.get('daño', 0))
            efecto = datos.get('efecto'); ahora = pygame.time.get_ticks()
            if efecto and random.randint(1, 100) <= efecto.get('probabilidad', 100):
                obj['estado'] = efecto.get('tipo'); obj['estado_hasta'] = ahora + efecto.get('duracion', 1000); obj['proximo_estado'] = ahora + 700
            retroceso = datos.get('retroceso', 0)
            if retroceso and direccion in direccion_vector:
                vx, vy = direccion_vector[direccion]
                obj['rect'].x += vx * retroceso; obj['rect'].y += vy * retroceso; obj['rect'].clamp_ip(AREA)

        def crear_enemigo(piedras):
            tipos = {'tirador': (40,100,(0,120,255)), 'melee': (40,100,(255,0,0)), 'grande': (60,180,(180,0,180))}
            while True:
                tipo = random.choice(list(tipos)); tamaño, vida, color = tipos[tipo]
                r = pygame.Rect(random.randint(PARED+10, ESC.width-PARED-tamaño-10), random.randint(PARED+10, ESC.height-PARED-tamaño-10), tamaño, tamaño)
                if pygame.Vector2(r.center).distance_to(ESC.center) <= 300 or any(r.colliderect(p) for p in piedras): continue
                ahora = pygame.time.get_ticks()
                return {'tipo': tipo, 'rect': r, 'vida': vida, 'max_vida': vida, 'daño': DAÑOS[tipo], 'color': color, 'ultimo_golpe': 0, 'ultimo_disparo': 0,
                        'quieto_hasta': 0, 'cambio': ahora, 'dx': random.choice([-1,0,1]), 'dy': random.choice([-1,0,1]), 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0}

        def actualizar_estado(e):
            ahora = pygame.time.get_ticks()
            if e['estado'] == 'quemar' and e['proximo_estado'] <= ahora < e['estado_hasta']:
                e['vida'] = max(0, e['vida'] - 3); e['proximo_estado'] = ahora + 700
            if ahora >= e['estado_hasta']: e['estado'] = None

        def crear_proyectil(x, y, dx, dy, daño, jefe=False):
            return {'x': float(x), 'y': float(y), 'dx': dx, 'dy': dy, 'daño': daño, 'jefe': jefe, 'distancia': 0, 'activo': True, 'rect': pygame.Rect(int(x)-8, int(y)-8, 16, 16)}

        def actualizar_proyectil(p, j, piedras):
            p['x'] += p['dx'] * VEL_P_ENEMIGO; p['y'] += p['dy'] * VEL_P_ENEMIGO; p['distancia'] += VEL_P_ENEMIGO
            p['rect'].center = round(p['x']), round(p['y'])
            if p['distancia'] >= DIST_P_ENEMIGO or not ESC.colliderect(p['rect']) or any(p['rect'].colliderect(x) for x in piedras):
                p['activo'] = False; return
            if p['rect'].colliderect(j['rect']): dañar_jugador(j, p['daño']); p['activo'] = False

        def actualizar_proyectil_pokemon(p, objetivos, piedras):
            vx, vy = direccion_vector[p['direccion']]
            paso = p['datos'].get('velocidad', 8)
            p['x'] += vx * paso; p['y'] += vy * paso; p['distancia'] += paso; p['rect'].center = round(p['x']), round(p['y'])
            if p['distancia'] >= p['datos'].get('distancia', 250) or not ESC.colliderect(p['rect']) or any(p['rect'].colliderect(x) for x in piedras):
                p['activo'] = False; return
            for o in objetivos:
                if o['vida'] <= 0 or o in p['golpeados']: continue
                a = p['datos'].get('area', 0); zona = o['rect'].inflate(a*2, a*2)
                if zona.colliderect(p['rect']):
                    recibir_ataque(o, p['datos'], p['direccion']); p['golpeados'].append(o)
                    if not p['datos'].get('atraviesa', False): p['activo'] = False; return

        def actualizar_enemigo(e, j, piedras, proyectiles):
            ahora = pygame.time.get_ticks()
            if ahora < e['quieto_hasta'] or e['estado'] == 'paralizar': return
            distancia = pygame.Vector2(e['rect'].center).distance_to(j['rect'].center)
            if distancia <= DETECCION:
                ex = (j['rect'].centerx > e['rect'].centerx) - (j['rect'].centerx < e['rect'].centerx)
                ey = (j['rect'].centery > e['rect'].centery) - (j['rect'].centery < e['rect'].centery)
                vel = 0.45 * (VEL_ENEMIGO) if e['estado'] == 'ralentizar' else VEL_ENEMIGO
                mover(e['rect'], ex*vel, 0, piedras); mover(e['rect'], 0, ey*vel, piedras)
                if e['tipo'] == 'tirador' and distancia <= DISPARO and ahora - e['ultimo_disparo'] >= CD_ENEMIGO:
                    v = pygame.Vector2(j['rect'].center) - pygame.Vector2(e['rect'].center)
                    if v.length():
                        v.normalize_ip(); proyectiles.append(crear_proyectil(e['rect'].centerx+v.x*30, e['rect'].centery+v.y*30, v.x, v.y, DAÑOS['tirador']))
                        e['ultimo_disparo'] = ahora
            else:
                if ahora >= e['cambio']:
                    e['dx'], e['dy'] = random.choice([-1,0,1]), random.choice([-1,0,1]); e['cambio'] = ahora + random.randint(500,1500)
                mover(e['rect'], e['dx']*VEL_ENEMIGO, 0, piedras); mover(e['rect'], 0, e['dy']*VEL_ENEMIGO, piedras)
            e['rect'].clamp_ip(AREA)
            if e['tipo'] in ('melee','grande') and e['rect'].colliderect(j['rect']) and ahora-e['ultimo_golpe'] >= 500:
                dañar_jugador(j, e['daño']); e['ultimo_golpe'] = ahora; e['quieto_hasta'] = ahora+500
                v = pygame.Vector2(e['rect'].center) - pygame.Vector2(j['rect'].center)
                if v.length():
                    v.normalize_ip()
                    e['rect'].x += v.x * 70
                    e['rect'].y += v.y * 70
                    e['rect'].clamp_ip(AREA)

        def crear_jefe(piedras):
            while True:
                r = pygame.Rect(random.randint(PARED+100, ESC.width-PARED-TAM_JEFE-100), random.randint(PARED+100, ESC.height-PARED-TAM_JEFE-100), TAM_JEFE, TAM_JEFE)
                if pygame.Vector2(r.center).distance_to(ESC.center) <= 400 or any(r.colliderect(p.inflate(20,20)) for p in piedras): continue
                ahora = pygame.time.get_ticks()
                return {'rect': r, 'vida': 500, 'max_vida': 500, 'daño': DAÑO_JEFE, 'ultimo_golpe': 0, 'ultimo_disparo': ahora, 'ultimo_poder': ahora,
                        'cambio': ahora, 'dx': random.choice([-1,0,1]), 'dy': random.choice([-1,0,1])}

        def crear_piedras_verdes(jefe):
            nuevas = []
            for _ in range(PIEDRAS_POR_USO):
                for _ in range(20):
                    a, d = random.uniform(0, math.tau), random.randint(120,400)
                    r = pygame.Rect(int(jefe['rect'].centerx + math.cos(a)*d), int(jefe['rect'].centery + math.sin(a)*d), 45, 45)
                    if not AREA.contains(r) or r.colliderect(jefe['rect']) or any(r.colliderect(x['rect']) for x in nuevas): continue
                    nuevas.append({'rect': r, 'tiempo': pygame.time.get_ticks(), 'daño': 0}); break
            return nuevas

        def actualizar_jefe(jefe, j, piedras, proyectiles, verdes):
            ahora = pygame.time.get_ticks()
            d = pygame.Vector2(jefe['rect'].center).distance_to(j['rect'].center)
            if d <= DETECCION + 150:
                ex = (j['rect'].centerx > jefe['rect'].centerx) - (j['rect'].centerx < jefe['rect'].centerx)
                ey = (j['rect'].centery > jefe['rect'].centery) - (j['rect'].centery < jefe['rect'].centery)
                mover(jefe['rect'], ex, 0, piedras); mover(jefe['rect'], 0, ey, piedras)
            else:
                if ahora >= jefe['cambio']:
                    jefe['dx'], jefe['dy'] = random.choice([-1,0,1]), random.choice([-1,0,1]); jefe['cambio'] = ahora + random.randint(500,1500)
                mover(jefe['rect'], jefe['dx'], 0, piedras); mover(jefe['rect'], 0, jefe['dy'], piedras)
            jefe['rect'].clamp_ip(AREA)
            if ahora - jefe['ultimo_disparo'] >= CD_JEFE:
                for i in range(BALAS_JEFE):
                    a = i * math.tau / BALAS_JEFE; dx, dy = math.cos(a), math.sin(a); r = TAM_JEFE//2+10
                    proyectiles.append(crear_proyectil(jefe['rect'].centerx+dx*r, jefe['rect'].centery+dy*r, dx, dy, 25, True))
                jefe['ultimo_disparo'] = ahora
            if ahora - jefe['ultimo_poder'] >= CD_PIEDRA:
                verdes.extend(crear_piedras_verdes(jefe)); jefe['ultimo_poder'] = ahora
            if jefe['rect'].colliderect(j['rect']) and ahora-jefe['ultimo_golpe'] >= 700:
                dañar_jugador(j, jefe['daño']); jefe['ultimo_golpe'] = ahora

        def crear_nivel(numero):
            piedras = crear_piedras()
            jefe = crear_jefe(piedras) if numero > 0 and numero % 3 == 0 else None
            return {'piedras': piedras, 'enemigos': [] if jefe else [crear_enemigo(piedras) for _ in range(CANT_ENEMIGOS)], 'jefe': jefe,
                    'proyectiles_pokemon': [], 'proyectiles_enemigos': [], 'verdes': [], 'puertas': crear_puertas(), 'llave': None}

        def actualizar_nivel(nivel, j):
            ahora = pygame.time.get_ticks(); piedras = nivel['piedras']; enemigos = nivel['enemigos']; jefe = nivel['jefe']
            mover_jugador(j, piedras); actualizar_jugador(j)
            objetivos = enemigos[:] + ([jefe] if jefe else [])
            for p in nivel['proyectiles_pokemon']: actualizar_proyectil_pokemon(p, objetivos, piedras)
            nivel['proyectiles_pokemon'] = [p for p in nivel['proyectiles_pokemon'] if p['activo']]
            for e in enemigos:
                actualizar_estado(e)
                if e['vida'] > 0: actualizar_enemigo(e, j, piedras, nivel['proyectiles_enemigos'])
            nivel['enemigos'] = [e for e in enemigos if e['vida'] > 0]
            if jefe:
                actualizar_jefe(jefe, j, piedras, nivel['proyectiles_enemigos'], nivel['verdes'])
                if jefe['vida'] <= 0: nivel['jefe'] = None
            for p in nivel['proyectiles_enemigos']: actualizar_proyectil(p, j, piedras)
            nivel['proyectiles_enemigos'] = [p for p in nivel['proyectiles_enemigos'] if p['activo']]
            for p in nivel['verdes'][:]:
                if ahora - p['tiempo'] >= DURACION_PIEDRA: nivel['verdes'].remove(p); continue
                if j['rect'].colliderect(p['rect']) and ahora-p['daño'] >= 500: dañar_jugador(j, DAÑO_PIEDRA); p['daño'] = ahora
            derrotados = not nivel['enemigos'] and nivel['jefe'] is None
            if derrotados and nivel['llave'] is None and not j['llave']:
                nivel['llave'] = pygame.Rect(ESC.centerx-15, ESC.centery-15, 30, 30)
            if nivel['llave'] and j['rect'].colliderect(nivel['llave']): j['llave'] = True; nivel['llave'] = None
            if j['vida'] <= 0: return 'muerte'
            if j['llave'] and any(j['rect'].colliderect(p.inflate(20,20)) for p in nivel['puertas']): return 'siguiente'

        def dibujar_rect(rect, cx, cy, color, forma='rect'):
            r = pygame.Rect(rect.x-cx, rect.y-cy, rect.width, rect.height)
            (pygame.draw.ellipse if forma == 'ellipse' else pygame.draw.rect)(ventana, color, r)

        def dibujar_jugador(j, cx, cy):
            centro = j['rect'].center; j['rect'].center = centro[0]-cx, centro[1]-cy
            ok = j['animador'].dibujar(ventana); j['rect'].center = centro
            if ok: return
            r = pygame.Rect(0,0,j['tamaño'],j['tamaño']); r.center = centro[0]-cx, centro[1]-cy; pygame.draw.rect(ventana, (255,50,255), r)

        def barra(rect, vida, max_vida, alto=5):
            pygame.draw.rect(ventana, (80,0,0), rect)
            pygame.draw.rect(ventana, (0,200,0), (rect[0], rect[1], max(0, vida*rect[2]//max(1,max_vida)), rect[3]))

        def dibujar_objetos(nivel, j):
            cx = max(0, min(j['rect'].centerx-W//2, ESC.width-W)); cy = max(0, min(j['rect'].centery-H//2, ESC.height-H))
            ventana.fill('black')
            dibujar_rect(ESC, cx, cy, 'white')
            paredes = [pygame.Rect(0,0,ESC.width,PARED), pygame.Rect(0,ESC.bottom-PARED,ESC.width,PARED), pygame.Rect(0,0,PARED,ESC.height), pygame.Rect(ESC.right-PARED,0,PARED,ESC.height)]
            for p in paredes: dibujar_rect(p,cx,cy,'black')
            for p in nivel['piedras']: dibujar_rect(p,cx,cy,(100,100,100),'ellipse')
            for p in nivel['verdes']: dibujar_rect(p['rect'],cx,cy,(0,220,80),'ellipse')
            for p in nivel['puertas']: dibujar_rect(p,cx,cy,(120,70,30))
            for p in nivel['proyectiles_enemigos']:
                pygame.draw.circle(ventana, (255,50,0) if p['jefe'] else (255,150,0), (round(p['x']-cx),round(p['y']-cy)), 9 if p['jefe'] else 8)
            for p in nivel['proyectiles_pokemon']:
                pygame.draw.circle(ventana, (80,180,255), (round(p['x']-cx),round(p['y']-cy)), max(2,p['datos'].get('area',8)))
            dibujar_jugador(j,cx,cy)
            for e in nivel['enemigos']:
                dibujar_rect(e['rect'],cx,cy,e['color'])
                barra((e['rect'].x-cx,e['rect'].y-cy-9,e['rect'].width,5),e['vida'],e['max_vida'])
            if nivel['jefe']:
                b = nivel['jefe']; dibujar_rect(b['rect'],cx,cy,(255,140,0)); barra((b['rect'].x-cx,b['rect'].y-cy-12,b['rect'].width,8),b['vida'],b['max_vida'],8)
            if nivel['llave']: dibujar_rect(nivel['llave'],cx,cy,'yellow')
            pygame.draw.rect(ventana,(80,0,0),(20,20,300,25))
            pygame.draw.rect(ventana,(0,200,0),(20,20,min(300,j['vida']*300//max(1,j['max_vida'])),25))
            pygame.display.flip()

        j = crear_jugador(pokemon, ESC.center)
        nivel_numero = 0
        reloj = pygame.time.Clock()
        while True:
            reiniciar_jugador(j); nivel = crear_nivel(nivel_numero)
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: return 'salir', j['nombre']
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_x: return 'salir', j['nombre']
                        if e.key == pygame.K_F1: return 'debug', j['nombre']
                        if e.key == pygame.K_e: atacar_cuerpo(j, nivel['enemigos'][:] + ([nivel['jefe']] if nivel['jefe'] else []))
                        if e.key == pygame.K_q: atacar_proyectil(j, nivel['proyectiles_pokemon'])
                resultado = actualizar_nivel(nivel, j)
                dibujar_objetos(nivel, j)
                if resultado == 'siguiente': nivel_numero += 1; break
                if resultado == 'muerte': return 'juego_terminado', j['nombre']
                reloj.tick(60)

    pokemon = 'pikachu' if 'pikachu' in pokemones else next(iter(pokemones))
    botones = {'jugar': pygame.Rect(150,120,200,60), 'ajustes': pygame.Rect(150,210,200,60), 'salir': pygame.Rect(150,300,200,60)}
    reloj = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_x):
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F1:
                r, p = debug_menu(pokemon)
                if r == 'salir': pygame.quit(); sys.exit()
                if p in pokemones: pokemon = p
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and botones['jugar'].collidepoint(e.pos):
                while True:
                    resultado, seleccionado = jugar(pokemon)
                    if resultado == 'salir': pygame.quit(); sys.exit()
                    if resultado == 'debug':
                        r, p = debug_menu(pokemon)
                        if r == 'salir': pygame.quit(); sys.exit()
                        if p in pokemones: pokemon = p
                        continue
                    break
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and botones['salir'].collidepoint(e.pos):
                pygame.quit(); sys.exit()

        ventana.fill('black')
        for nombre, color in [('jugar',(200,0,0)),('ajustes',(0,200,0)),('salir',(0,0,200))]:
            pygame.draw.rect(ventana,color,botones[nombre])
        ventana.blit(fuente.render('Jugar',True,'white'),(220,140))
        ventana.blit(fuente.render('Ajustes',True,'white'),(215,230))
        ventana.blit(fuente.render('Salir',True,'white'),(225,320))
        ventana.blit(fuente.render('F1: Menu debug',True,'white'),(700,20))
        ventana.blit(fuente.render('Pokemon: '+pokemon,True,'white'),(700,45))
        pygame.display.flip(); reloj.tick(60)


if __name__ == '__main__':
    main()
