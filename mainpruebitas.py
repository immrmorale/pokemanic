import pygame
import random
import math
import sys
from pokemones import pokemones, movimientos
from animaciones import direcciones, direccion_vector, AnimadorPokemon

pygame.init()
W, H = 1000, 600
ESCENARIO = pygame.Rect(0, 0, 2400, 1600)
PARED = 40
AREA = ESCENARIO.inflate(-PARED * 2, -PARED * 2)
VEL_ENEMIGO = 1
VEL_PROYECTIL_ENEMIGO = 8
DISTANCIA_PROYECTIL_ENEMIGO = 250
DISTANCIA_DETECCION = 350
DISTANCIA_DISPARO_ENEMIGO = 500
DAÑO_TIRADOR = 5
DAÑO_MELEE = 10
DAÑO_GRANDE = 25
DAÑO_JEFE = 35
COOLDOWN_ENEMIGO = 1500
COOLDOWN_JEFE = 5000
COOLDOWN_PIEDRA = 2000
DURACION_PIEDRA = 5000
DAÑO_PIEDRA = 15
CANTIDAD_ENEMIGOS = 10
CANTIDAD_PIEDRAS = 30
TAM_JEFE = 160
BALAS_JEFE = 24
PIEDRAS_VERDES_POR_USO = 4

ventana = None


def mover(rect, dx, dy, piedras):
    nuevo = rect.copy()
    nuevo.x += dx
    if not any(nuevo.colliderect(p) for p in piedras):
        rect.x += dx
    nuevo = rect.copy()
    nuevo.y += dy
    if not any(nuevo.colliderect(p) for p in piedras):
        rect.y += dy


def crear_piedras():
    piedras = []
    inicio = pygame.Rect(ESCENARIO.centerx - 250, ESCENARIO.centery - 250, 500, 500)
    while len(piedras) < CANTIDAD_PIEDRAS:
        p = pygame.Rect(
            random.randint(PARED + 50, ESCENARIO.width - PARED - 100),
            random.randint(PARED + 50, ESCENARIO.height - PARED - 100),
            50, 50
        )
        if p.colliderect(inicio):
            continue
        if any(p.colliderect(x.inflate(15, 15)) for x in piedras):
            continue
        piedras.append(p)
    return piedras


class DebugMenu:
    def __init__(self, ventana, pokemon_actual='pikachu'):
        self.ventana = ventana
        self.pokemon_actual = pokemon_actual
        self.scroll = 0
        self.scroll_maximo = 0
        self.botones_pokemon = []
        self.fuente = pygame.font.Font(None, 24)
        self.fuente_titulo = pygame.font.Font(None, 32)

    def abrir(self, pokemon_actual=None):
        if pokemon_actual in pokemones:
            self.pokemon_actual = pokemon_actual
        ejecutando = True
        self.scroll = 0
        reloj = pygame.time.Clock()
        columnas = 4
        ancho_boton = 210
        alto_boton = 62
        alto_nombre = 28
        espacio_y = 18
        filas = math.ceil(len(pokemones) / columnas)
        contenido_alto = 80 + filas * (alto_boton + alto_nombre + espacio_y)
        self.scroll_maximo = max(0, contenido_alto - 580)
        while ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return 'salir'
                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_ESCAPE, pygame.K_F1):
                        ejecutando = False
                if evento.type == pygame.MOUSEWHEEL:
                    self.scroll -= evento.y * 60
                    self.scroll = max(0, min(self.scroll, self.scroll_maximo))
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for boton, nombre in self.botones_pokemon:
                        if boton.collidepoint(evento.pos):
                            self.pokemon_actual = nombre
                            ejecutando = False
                            break
            self.ventana.fill((20, 20, 20))
            self.botones_pokemon = []
            titulo = self.fuente_titulo.render('MENU DEBUG', True, (255, 255, 255))
            ayuda = self.fuente.render('F1 o ESC para cerrar - rueda del mouse para desplazarte', True, (200, 200, 200))
            self.ventana.blit(titulo, (25, 15))
            self.ventana.blit(ayuda, (25, 45))
            for numpoke, nombre in enumerate(pokemones):
                xboton = 30 + (numpoke % columnas) * 240
                yboton = 85 + (numpoke // columnas) * (alto_boton + alto_nombre + espacio_y) - self.scroll
                boton = pygame.Rect(xboton, yboton, ancho_boton, alto_boton)
                nombre_rect = pygame.Rect(xboton, yboton + alto_boton, ancho_boton, alto_nombre)
                if boton.bottom >= 65 and nombre_rect.top <= 600:
                    color = (80, 160, 80) if nombre == self.pokemon_actual else (200, 200, 200)
                    pygame.draw.rect(self.ventana, color, boton)
                    pygame.draw.rect(self.ventana, (50, 50, 50), nombre_rect)
                    texto = self.fuente.render(nombre.replace('_', ' ').title(), True, (255, 255, 255))
                    self.ventana.blit(texto, (xboton + 8, yboton + 20))
                    texto_nombre = self.fuente.render(nombre, True, (255, 255, 255))
                    self.ventana.blit(texto_nombre, (xboton + 8, yboton + alto_boton + 5))
                    self.botones_pokemon.append((boton, nombre))
            pygame.display.flip()
            reloj.tick(60)
        return self.pokemon_actual


class ProyectilPokemon:
    def __init__(self, x, y, direccion, datos):
        self.x = float(x)
        self.y = float(y)
        self.direccion = direccion
        self.datos = datos
        self.rect = pygame.Rect(0, 0, max(2, datos.get('area', 8) * 2), max(2, datos.get('area', 8) * 2))
        self.rect.center = (round(self.x), round(self.y))
        self.distancia_recorrida = 0
        self.activo = True
        self.objetivos_golpeados = []

    def actualizar(self, objetivos, piedras):
        vx, vy = direccion_vector[self.direccion]
        largo = math.hypot(vx, vy)
        vx /= largo
        vy /= largo
        paso = self.datos.get('velocidad', 8)
        self.x += vx * paso
        self.y += vy * paso
        self.distancia_recorrida += paso
        self.rect.center = (round(self.x), round(self.y))
        if self.distancia_recorrida >= self.datos.get('distancia', 250):
            self.activo = False
            return
        if not ESCENARIO.colliderect(self.rect) or any(self.rect.colliderect(p) for p in piedras):
            self.activo = False
            return
        for objetivo in objetivos:
            if not objetivo.esta_vivo() or objetivo in self.objetivos_golpeados:
                continue
            zona = objetivo.rect.inflate(self.datos.get('area', 0) * 2, self.datos.get('area', 0) * 2)
            if zona.colliderect(self.rect):
                objetivo.recibir_ataque(self.datos, self.direccion)
                self.objetivos_golpeados.append(objetivo)
                if not self.datos.get('atraviesa', False):
                    self.activo = False
                    break

    def dibujar(self, ventana, cx, cy):
        radio = max(2, self.datos.get('area', 8))
        pygame.draw.circle(ventana, (80, 180, 255), (round(self.x - cx), round(self.y - cy)), radio)


class ProyectilEnemigo:
    def __init__(self, x, y, dx, dy, daño, jefe=False):
        self.x = float(x)
        self.y = float(y)
        self.dx = dx
        self.dy = dy
        self.daño = daño
        self.jefe = jefe
        self.distancia = 0
        self.activo = True
        self.rect = pygame.Rect(int(x) - 8, int(y) - 8, 16, 16)

    def actualizar(self, jugador, piedras):
        self.x += self.dx * VEL_PROYECTIL_ENEMIGO
        self.y += self.dy * VEL_PROYECTIL_ENEMIGO
        self.distancia += VEL_PROYECTIL_ENEMIGO
        self.rect.center = (round(self.x), round(self.y))
        if self.distancia >= DISTANCIA_PROYECTIL_ENEMIGO or not ESCENARIO.colliderect(self.rect):
            self.activo = False
            return
        if any(self.rect.colliderect(p) for p in piedras):
            self.activo = False
            return
        if self.rect.colliderect(jugador.rect):
            jugador.recibir_danio(self.daño)
            self.activo = False

    def dibujar(self, ventana, cx, cy):
        color = (255, 50, 0) if self.jefe else (255, 150, 0)
        pygame.draw.circle(ventana, color, (round(self.x - cx), round(self.y - cy)), 9 if self.jefe else 8)


class Jugador:
    def __init__(self, x, y, nombre):
        self.nombre = nombre if nombre in pokemones else 'pikachu'
        self.pokemon_actual = pokemones[self.nombre]
        self.aplicar_estadisticas()
        self.rect = pygame.Rect(0, 0, self.hitbox_tamaño, self.hitbox_tamaño)
        self.rect.center = (x, y)
        self.direccion = 'sur'
        self.moviendose = False
        self.ultimo_golpe = -1000
        self.ultimo_proyectil = -1000
        self.atacando = False
        self.llave = False
        self.animador = AnimadorPokemon(self.nombre, self.rect, self.tamaño)

    def aplicar_estadisticas(self):
        datos = self.pokemon_actual
        stats = datos.get('estadisticas_juego') or {}
        self.max_vida = int(datos.get('vida') or datos.get('vida_base') or stats.get('vida') or 100)
        self.vida = self.max_vida
        self.velocidad = float(stats.get('velocidad', datos.get('velocidad_movimiento', datos.get('velocidad', 5))))
        self.tamaño = int(stats.get('tamaño', datos.get('tamaño', 40)))
        self.hitbox_tamaño = int(stats.get('hitbox', datos.get('hitbox', self.tamaño)))

    def cambiar_pokemon(self, nombre):
        if nombre not in pokemones:
            return
        centro = self.rect.center
        self.nombre = nombre
        self.pokemon_actual = pokemones[nombre]
        self.aplicar_estadisticas()
        self.rect = pygame.Rect(0, 0, self.hitbox_tamaño, self.hitbox_tamaño)
        self.rect.center = centro
        self.ultimo_golpe = -1000
        self.ultimo_proyectil = -1000
        self.atacando = False
        self.llave = False
        self.animador = AnimadorPokemon(self.nombre, self.rect, self.tamaño)

    def reiniciar_nivel(self, centro):
        self.aplicar_estadisticas()
        self.rect = pygame.Rect(0, 0, self.hitbox_tamaño, self.hitbox_tamaño)
        self.rect.center = centro
        self.direccion = 'sur'
        self.moviendose = False
        self.ultimo_golpe = -1000
        self.ultimo_proyectil = -1000
        self.atacando = False
        self.animador = AnimadorPokemon(self.nombre, self.rect, self.tamaño)

    def mover(self, piedras):
        teclas = pygame.key.get_pressed()
        dx = (teclas[pygame.K_d] - teclas[pygame.K_a])
        dy = (teclas[pygame.K_s] - teclas[pygame.K_w])
        self.moviendose = dx != 0 or dy != 0
        if not self.moviendose:
            return
        if dx > 0 and dy < 0:
            self.direccion = 'noreste'
        elif dx > 0 and dy > 0:
            self.direccion = 'sureste'
        elif dx < 0 and dy < 0:
            self.direccion = 'noroeste'
        elif dx < 0 and dy > 0:
            self.direccion = 'suroeste'
        elif dx > 0:
            self.direccion = 'este'
        elif dx < 0:
            self.direccion = 'oeste'
        elif dy < 0:
            self.direccion = 'norte'
        else:
            self.direccion = 'sur'
        largo = math.hypot(dx, dy)
        dx /= largo
        dy /= largo
        mover(self.rect, dx * self.velocidad, 0, piedras)
        mover(self.rect, 0, dy * self.velocidad, piedras)
        self.rect.clamp_ip(AREA)

    def obtener_ataque(self, categoria):
        ataques = self.pokemon_actual.get('ataques_estadisticas', {}) or {}
        datos = ataques.get(categoria)
        if datos is not None:
            return datos
        nombre = self.pokemon_actual.get('ataque_cuerpo' if categoria == 'cuerpo' else 'ataque_proyectil')
        if nombre in movimientos:
            return movimientos[nombre]
        return None

    def atacar_cuerpo(self, objetivos):
        datos = self.obtener_ataque('cuerpo')
        if not datos:
            return
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_golpe < datos.get('enfriamiento', 300) or self.atacando:
            return
        self.ultimo_golpe = ahora
        self.atacando = True
        ataque_animacion = self.animador.buscar_ataque()
        if ataque_animacion:
            self.animador.cambiar(ataque_animacion, direcciones.index(self.direccion), False)
        vx, vy = direccion_vector[self.direccion]
        distancia = datos.get('distancia', 50)
        area = datos.get('area', 20)
        centro_x = self.rect.centerx + vx * distancia / 2
        centro_y = self.rect.centery + vy * distancia / 2
        hitbox = pygame.Rect(0, 0, distancia, area * 2)
        hitbox.center = (round(centro_x), round(centro_y))
        for objetivo in objetivos:
            if objetivo.esta_vivo() and hitbox.colliderect(objetivo.rect):
                objetivo.recibir_ataque(datos, self.direccion)

    def atacar_proyectil(self, proyectiles):
        datos = self.obtener_ataque('proyectil')
        if not datos:
            return
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_proyectil < datos.get('enfriamiento', 300) or self.atacando:
            return
        self.ultimo_proyectil = ahora
        vx, vy = direccion_vector[self.direccion]
        distancia = max(20, self.hitbox_tamaño // 2)
        x = self.rect.centerx + vx * distancia
        y = self.rect.centery + vy * distancia
        proyectiles.append(ProyectilPokemon(x, y, self.direccion, datos))

    def actualizar(self):
        if self.atacando and self.animador.esta_terminada():
            self.atacando = False
        direccion = direcciones.index(self.direccion)
        if self.atacando:
            ataque_animacion = self.animador.buscar_ataque()
            if ataque_animacion:
                self.animador.cambiar(ataque_animacion, direccion, False)
            else:
                self.atacando = False
        elif self.moviendose:
            self.animador.cambiar('walk', direccion, True)
        else:
            self.animador.cambiar('idle', direccion, True)
        self.animador.actualizar()

    def recibir_danio(self, cantidad):
        self.vida = max(0, self.vida - cantidad)

    def dibujar(self, ventana, cx, cy):
        centro = self.rect.center
        self.rect.center = (centro[0] - cx, centro[1] - cy)
        dibujado = self.animador.dibujar(ventana)
        self.rect.center = centro
        if dibujado:
            return
        zona = pygame.Rect(0, 0, self.tamaño, self.tamaño)
        zona.center = (self.rect.centerx - cx, self.rect.centery - cy)
        pygame.draw.rect(ventana, (255, 50, 255), zona)


class Enemigo:
    def __init__(self, piedras):
        tipos = {
            'tirador': (40, 100, DAÑO_TIRADOR, (0, 120, 255)),
            'melee': (40, 100, DAÑO_MELEE, (255, 0, 0)),
            'grande': (60, 180, DAÑO_GRANDE, (180, 0, 180))
        }
        while True:
            self.tipo = random.choice(list(tipos))
            tamaño, vida, daño, color = tipos[self.tipo]
            self.rect = pygame.Rect(
                random.randint(PARED + 10, ESCENARIO.width - PARED - tamaño - 10),
                random.randint(PARED + 10, ESCENARIO.height - PARED - tamaño - 10),
                tamaño, tamaño
            )
            if pygame.Vector2(self.rect.center).distance_to(ESCENARIO.center) <= 300:
                continue
            if any(self.rect.colliderect(p) for p in piedras):
                continue
            break
        self.vida = vida
        self.max_vida = vida
        self.daño = daño
        self.color = color
        self.velocidad = VEL_ENEMIGO
        self.ultimo_golpe = 0
        self.ultimo_disparo = 0
        self.quieto_hasta = 0
        self.cambio = pygame.time.get_ticks()
        self.dx = random.choice([-1, 0, 1])
        self.dy = random.choice([-1, 0, 1])
        self.estado = None
        self.estado_hasta = 0
        self.proximo_estado = 0

    def esta_vivo(self):
        return self.vida > 0

    def recibir_danio(self, cantidad):
        self.vida = max(0, self.vida - cantidad)

    def recibir_ataque(self, datos, direccion=None):
        self.recibir_danio(datos.get('daño', 0))
        efecto = datos.get('efecto')
        ahora = pygame.time.get_ticks()
        if efecto and random.randint(1, 100) <= efecto.get('probabilidad', 100):
            self.estado = efecto.get('tipo')
            self.estado_hasta = ahora + efecto.get('duracion', 1000)
            self.proximo_estado = ahora + 700
        retroceso = datos.get('retroceso', 0)
        if retroceso and direccion in direccion_vector:
            vx, vy = direccion_vector[direccion]
            self.rect.x += vx * retroceso
            self.rect.y += vy * retroceso

    def actualizar_estado(self):
        ahora = pygame.time.get_ticks()
        if self.estado == 'quemar' and ahora >= self.proximo_estado and ahora < self.estado_hasta:
            self.recibir_danio(3)
            self.proximo_estado = ahora + 700
        if ahora >= self.estado_hasta:
            self.estado = None

    def actualizar(self, jugador, piedras, proyectiles_enemigos):
        ahora = pygame.time.get_ticks()
        if ahora < self.quieto_hasta or self.estado == 'paralizar':
            return
        distancia = pygame.Vector2(self.rect.center).distance_to(jugador.rect.center)
        if distancia <= DISTANCIA_DETECCION:
            ex = (jugador.rect.centerx > self.rect.centerx) - (jugador.rect.centerx < self.rect.centerx)
            ey = (jugador.rect.centery > self.rect.centery) - (jugador.rect.centery < self.rect.centery)
            velocidad = self.velocidad * (0.45 if self.estado == 'ralentizar' else 1)
            mover(self.rect, ex * velocidad, 0, piedras)
            mover(self.rect, 0, ey * velocidad, piedras)
            if self.tipo == 'tirador' and distancia <= DISTANCIA_DISPARO_ENEMIGO and ahora - self.ultimo_disparo >= COOLDOWN_ENEMIGO:
                v = pygame.Vector2(jugador.rect.center) - pygame.Vector2(self.rect.center)
                if v.length():
                    v = v.normalize()
                    proyectiles_enemigos.append(ProyectilEnemigo(self.rect.centerx + v.x * 30, self.rect.centery + v.y * 30, v.x, v.y, DAÑO_TIRADOR))
                    self.ultimo_disparo = ahora
        else:
            if ahora >= self.cambio:
                self.dx = random.choice([-1, 0, 1])
                self.dy = random.choice([-1, 0, 1])
                self.cambio = ahora + random.randint(500, 1500)
            mover(self.rect, self.dx * self.velocidad, 0, piedras)
            mover(self.rect, 0, self.dy * self.velocidad, piedras)
        self.rect.clamp_ip(AREA)
        if self.tipo in ('melee', 'grande') and self.rect.colliderect(jugador.rect) and ahora - self.ultimo_golpe >= 500:
            jugador.recibir_danio(self.daño)
            self.ultimo_golpe = ahora
            self.quieto_hasta = ahora + 500
            dx = self.rect.centerx - jugador.rect.centerx
            dy = self.rect.centery - jugador.rect.centery
            self.retroceder(dx, dy, 70)

    def retroceder(self, dx, dy, distancia):
        largo = math.hypot(dx, dy)
        if not largo:
            return
        self.rect.x += dx / largo * distancia
        self.rect.y += dy / largo * distancia
        self.rect.clamp_ip(AREA)

    def dibujar(self, ventana, cx, cy):
        r = pygame.Rect(self.rect.x - cx, self.rect.y - cy, self.rect.width, self.rect.height)
        pygame.draw.rect(ventana, self.color, r)
        pygame.draw.rect(ventana, (80, 0, 0), (r.x, r.y - 9, r.width, 5))
        pygame.draw.rect(ventana, (0, 200, 0), (r.x, r.y - 9, max(0, self.vida * r.width // self.max_vida), 5))


class Jefe:
    def __init__(self, piedras):
        while True:
            self.rect = pygame.Rect(
                random.randint(PARED + 100, ESCENARIO.width - PARED - TAM_JEFE - 100),
                random.randint(PARED + 100, ESCENARIO.height - PARED - TAM_JEFE - 100),
                TAM_JEFE, TAM_JEFE
            )
            if pygame.Vector2(self.rect.center).distance_to(pygame.Vector2(ESCENARIO.center)) <= 400:
                continue
            if any(self.rect.colliderect(p.inflate(20, 20)) for p in piedras):
                continue
            break
        ahora = pygame.time.get_ticks()
        self.vida = 500
        self.max_vida = 500
        self.daño = DAÑO_JEFE
        self.ultimo_golpe = 0
        self.ultimo_disparo = ahora
        self.ultimo_poder = ahora
        self.cambio = ahora
        self.dx = random.choice([-1, 0, 1])
        self.dy = random.choice([-1, 0, 1])

    def esta_vivo(self):
        return self.vida > 0

    def recibir_danio(self, cantidad):
        self.vida = max(0, self.vida - cantidad)

    def recibir_ataque(self, datos, direccion=None):
        self.recibir_danio(datos.get('daño', 0))
        retroceso = datos.get('retroceso', 0)
        if retroceso and direccion in direccion_vector:
            vx, vy = direccion_vector[direccion]
            self.rect.x += vx * retroceso
            self.rect.y += vy * retroceso

    def actualizar(self, jugador, piedras, proyectiles_enemigos, verdes):
        ahora = pygame.time.get_ticks()
        distancia = pygame.Vector2(self.rect.center).distance_to(jugador.rect.center)
        if distancia <= DISTANCIA_DETECCION + 150:
            ex = (jugador.rect.centerx > self.rect.centerx) - (jugador.rect.centerx < self.rect.centerx)
            ey = (jugador.rect.centery > self.rect.centery) - (jugador.rect.centery < self.rect.centery)
            mover(self.rect, ex, 0, piedras)
            mover(self.rect, 0, ey, piedras)
        elif ahora >= self.cambio:
            self.dx = random.choice([-1, 0, 1])
            self.dy = random.choice([-1, 0, 1])
            self.cambio = ahora + random.randint(500, 1500)
        else:
            mover(self.rect, self.dx, 0, piedras)
            mover(self.rect, 0, self.dy, piedras)
        self.rect.clamp_ip(AREA)
        if ahora - self.ultimo_disparo >= COOLDOWN_JEFE:
            for i in range(BALAS_JEFE):
                a = i * (2 * math.pi / BALAS_JEFE)
                dx, dy = math.cos(a), math.sin(a)
                radio = self.rect.width // 2 + 10
                x = self.rect.centerx + dx * radio
                y = self.rect.centery + dy * radio
                proyectiles_enemigos.append(ProyectilEnemigo(x, y, dx, dy, 25, True))
            self.ultimo_disparo = ahora
        if ahora - self.ultimo_poder >= COOLDOWN_PIEDRA:
            verdes.extend(piedras_verdes(self, verdes))
            self.ultimo_poder = ahora
        if self.rect.colliderect(jugador.rect) and ahora - self.ultimo_golpe >= 700:
            jugador.recibir_danio(self.daño)
            self.ultimo_golpe = ahora

    def dibujar(self, ventana, cx, cy):
        r = pygame.Rect(self.rect.x - cx, self.rect.y - cy, self.rect.width, self.rect.height)
        pygame.draw.rect(ventana, (255, 140, 0), r)
        pygame.draw.rect(ventana, (80, 0, 0), (r.x, r.y - 12, r.width, 8))
        pygame.draw.rect(ventana, (255, 0, 0), (r.x, r.y - 12, max(0, self.vida * r.width // self.max_vida), 8))


def piedras_verdes(jefe, piedras):
    nuevas = []
    for _ in range(PIEDRAS_VERDES_POR_USO):
        for _ in range(20):
            a = random.uniform(0, math.pi * 2)
            distancia = random.randint(120, 400)
            x = jefe.rect.centerx + math.cos(a) * distancia
            y = jefe.rect.centery + math.sin(a) * distancia
            p = pygame.Rect(int(x), int(y), 45, 45)
            if not AREA.contains(p) or p.colliderect(jefe.rect):
                continue
            if any(p.colliderect(o['rect']) for o in piedras + nuevas):
                continue
            nuevas.append({'rect': p, 'tiempo': pygame.time.get_ticks(), 'daño': 0})
            break
    return nuevas


def crear_puertas():
    return [
        pygame.Rect(ESCENARIO.centerx - 30, 0, 60, PARED),
        pygame.Rect(ESCENARIO.centerx - 30, ESCENARIO.bottom - PARED, 60, PARED),
        pygame.Rect(0, ESCENARIO.centery - 30, PARED, 60),
        pygame.Rect(ESCENARIO.right - PARED, ESCENARIO.centery - 30, PARED, 60)
    ]


def camara(jugador):
    r = jugador.rect
    x = max(0, min(r.centerx - W // 2, ESCENARIO.width - W))
    y = max(0, min(r.centery - H // 2, ESCENARIO.height - H))
    return x, y


class Nivel:
    def __init__(self, jugador, numero):
        self.jugador = jugador
        self.numero = numero
        self.piedras = crear_piedras()
        self.enemigos = [] if numero > 0 and numero % 3 == 0 else [Enemigo(self.piedras) for _ in range(CANTIDAD_ENEMIGOS)]
        self.jefe = Jefe(self.piedras) if numero > 0 and numero % 3 == 0 else None
        self.proyectiles_pokemon = []
        self.proyectiles_enemigos = []
        self.verdes = []
        self.puertas = crear_puertas()
        self.llave = None
        self.direccion = jugador.direccion

    def objetivos(self):
        lista = self.enemigos[:]
        if self.jefe:
            lista.append(self.jefe)
        return lista

    def actualizar(self):
        ahora = pygame.time.get_ticks()
        self.jugador.mover(self.piedras)
        self.jugador.actualizar()
        objetivos = self.objetivos()
        for proyectil in self.proyectiles_pokemon:
            proyectil.actualizar(objetivos, self.piedras)
        self.proyectiles_pokemon = [p for p in self.proyectiles_pokemon if p.activo]
        for enemigo in self.enemigos:
            enemigo.actualizar_estado()
            if enemigo.esta_vivo():
                enemigo.actualizar(self.jugador, self.piedras, self.proyectiles_enemigos)
        self.enemigos = [e for e in self.enemigos if e.esta_vivo()]
        if self.jefe:
            self.jefe.actualizar(self.jugador, self.piedras, self.proyectiles_enemigos, self.verdes)
            if not self.jefe.esta_vivo():
                self.jefe = None
        for proyectil in self.proyectiles_enemigos:
            proyectil.actualizar(self.jugador, self.piedras)
        self.proyectiles_enemigos = [p for p in self.proyectiles_enemigos if p.activo]
        for p in self.verdes[:]:
            if ahora - p['tiempo'] >= DURACION_PIEDRA:
                self.verdes.remove(p)
                continue
            if self.jugador.rect.colliderect(p['rect']) and ahora - p['daño'] >= 500:
                self.jugador.recibir_danio(DAÑO_PIEDRA)
                p['daño'] = ahora
        todos_derrotados = len(self.enemigos) == 0 and self.jefe is None
        if todos_derrotados and self.llave is None and not self.jugador.llave:
            self.llave = pygame.Rect(0, 0, 30, 30)
            self.llave.center = ESCENARIO.center
        if self.llave and self.jugador.rect.colliderect(self.llave):
            self.jugador.llave = True
            self.llave = None
        if self.jugador.vida <= 0:
            return 'muerte'
        if self.jugador.llave and any(self.jugador.rect.colliderect(p.inflate(20, 20)) for p in self.puertas):
            return 'siguiente'
        return None

    def dibujar(self, ventana):
        cx, cy = camara(self.jugador)
        ventana.fill((0, 0, 0))
        suelo = pygame.Rect(ESCENARIO.x - cx, ESCENARIO.y - cy, ESCENARIO.width, ESCENARIO.height)
        pygame.draw.rect(ventana, (255, 255, 255), suelo)
        paredes = [
            pygame.Rect(0, 0, ESCENARIO.width, PARED),
            pygame.Rect(0, ESCENARIO.bottom - PARED, ESCENARIO.width, PARED),
            pygame.Rect(0, 0, PARED, ESCENARIO.height),
            pygame.Rect(ESCENARIO.right - PARED, 0, PARED, ESCENARIO.height)
        ]
        for p in paredes:
            pygame.draw.rect(ventana, (0, 0, 0), pygame.Rect(p.x - cx, p.y - cy, p.width, p.height))
        for p in self.piedras:
            pygame.draw.ellipse(ventana, (100, 100, 100), pygame.Rect(p.x - cx, p.y - cy, p.width, p.height))
        for p in self.verdes:
            r = p['rect']
            pygame.draw.ellipse(ventana, (0, 220, 80), pygame.Rect(r.x - cx, r.y - cy, r.width, r.height))
        for p in self.puertas:
            pygame.draw.rect(ventana, (120, 70, 30), pygame.Rect(p.x - cx, p.y - cy, p.width, p.height))
        for p in self.proyectiles_enemigos:
            p.dibujar(ventana, cx, cy)
        for p in self.proyectiles_pokemon:
            p.dibujar(ventana, cx, cy)
        self.jugador.dibujar(ventana, cx, cy)
        for enemigo in self.enemigos:
            enemigo.dibujar(ventana, cx, cy)
        if self.jefe:
            self.jefe.dibujar(ventana, cx, cy)
        if self.llave:
            pygame.draw.rect(ventana, (255, 255, 0), pygame.Rect(self.llave.x - cx, self.llave.y - cy, self.llave.width, self.llave.height))
        pygame.draw.rect(ventana, (80, 0, 0), (20, 20, 300, 25))
        pygame.draw.rect(ventana, (0, 200, 0), (20, 20, min(300, self.jugador.vida * 300 // max(1, self.jugador.max_vida)), 25))
        pygame.display.flip()

    def ejecutar(self):
        reloj = pygame.time.Clock()
        ejecutando = True
        while ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_x:
                        return 'salir'
                    if evento.key == pygame.K_F1:
                        return 'debug'
                    if evento.key == pygame.K_e:
                        self.jugador.atacar_cuerpo(self.objetivos())
                    if evento.key == pygame.K_q:
                        self.jugador.atacar_proyectil(self.proyectiles_pokemon)
            resultado = self.actualizar()
            self.dibujar(ventana)
            if resultado:
                return resultado
            reloj.tick(60)
        return 'salir'


class Menu:
    def __init__(self, ventana):
        self.ventana = ventana
        self.pokemon_actual = 'pikachu' if 'pikachu' in pokemones else next(iter(pokemones))
        self.debug = DebugMenu(ventana, self.pokemon_actual)
        self.fuente = pygame.font.Font(None, 24)
        self.boton_jugar = pygame.Rect(150, 120, 200, 60)
        self.boton_ajustes = pygame.Rect(150, 210, 200, 60)
        self.boton_salir = pygame.Rect(150, 300, 200, 60)

    def dibujar(self):
        self.ventana.fill((0, 0, 0))
        pygame.draw.rect(self.ventana, (200, 0, 0), self.boton_jugar)
        pygame.draw.rect(self.ventana, (0, 200, 0), self.boton_ajustes)
        pygame.draw.rect(self.ventana, (0, 0, 200), self.boton_salir)
        self.ventana.blit(self.fuente.render('Jugar', True, (255, 255, 255)), (220, 140))
        self.ventana.blit(self.fuente.render('Ajustes', True, (255, 255, 255)), (215, 230))
        self.ventana.blit(self.fuente.render('Salir', True, (255, 255, 255)), (225, 320))
        self.ventana.blit(self.fuente.render('F1: Menu debug', True, (255, 255, 255)), (700, 20))
        self.ventana.blit(self.fuente.render('Pokemon: ' + self.pokemon_actual, True, (255, 255, 255)), (700, 45))
        pygame.display.flip()

    def ejecutar(self):
        reloj = pygame.time.Clock()
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_x):
                    return False
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F1:
                    resultado = self.debug.abrir(self.pokemon_actual)
                    if resultado == 'salir':
                        return False
                    if resultado in pokemones:
                        self.pokemon_actual = resultado
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.boton_jugar.collidepoint(evento.pos):
                        resultado = self.jugar()
                        if resultado == 'salir':
                            return False
                    elif self.boton_salir.collidepoint(evento.pos):
                        return False
            self.dibujar()
            reloj.tick(60)

    def jugar(self):
        jugador = Jugador(ESCENARIO.centerx, ESCENARIO.centery, self.pokemon_actual)
        nivel = 0
        while True:
            jugador.reiniciar_nivel(ESCENARIO.center)
            nivel_objeto = Nivel(jugador, nivel)
            while True:
                resultado = nivel_objeto.ejecutar()
                if resultado == 'debug':
                    seleccionado = self.debug.abrir(self.pokemon_actual)
                    if seleccionado == 'salir':
                        return 'salir'
                    if seleccionado in pokemones and seleccionado != self.pokemon_actual:
                        self.pokemon_actual = seleccionado
                        jugador.cambiar_pokemon(seleccionado)
                    continue
                if resultado == 'siguiente':
                    nivel += 1
                    break
                if resultado == 'muerte':
                    return 'juego_terminado'
                if resultado == 'salir':
                    return 'salir'


def main():
    global ventana
    pygame.init()
    ventana = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Pokemanic')
    Menu(ventana).ejecutar()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
