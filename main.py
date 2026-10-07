import pygame
import random
import sys
import math
from pokemones import pokemones, movimientos

from animaciones import direcciones, direccion_vector, AnimadorPokemon


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
                    if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_F1:
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


class Proyectil:
    def __init__(self, x, y, direccion, datos):
        self.x = float(x)
        self.y = float(y)
        self.x_inicial = float(x)
        self.y_inicial = float(y)
        self.direccion = direccion
        self.datos = datos
        self.rect = pygame.Rect(0, 0, datos['area'] * 2, datos['area'] * 2)
        self.rect.center = (round(self.x), round(self.y))
        self.distancia_recorrida = 0
        self.activo = True
        self.objetivos_golpeados = []

    def actualizar(self, enemigos):
        vx, vy = direccion_vector[self.direccion]
        largo = (vx ** 2 + vy ** 2) ** 0.5
        vx /= largo
        vy /= largo

        paso = self.datos['velocidad']
        self.x += vx * paso
        self.y += vy * paso
        self.distancia_recorrida += paso
        self.rect.center = (round(self.x), round(self.y))

        if self.distancia_recorrida >= self.datos['distancia']:
            self.activo = False
            return

        for enemigo in enemigos:
            if not enemigo.esta_vivo() or enemigo in self.objetivos_golpeados:
                continue

            zona = enemigo.rect.inflate(self.datos['area'] * 2, self.datos['area'] * 2)

            if zona.colliderect(self.rect):
                enemigo.recibir_ataque(self.datos, self.direccion)
                self.objetivos_golpeados.append(enemigo)

                if self.datos.get('atraviesa', False) is False:
                    self.activo = False
                    break

    def dibujar(self, ventana):
        radio = self.datos['area']
        pygame.draw.circle(
            ventana,
            (80, 180, 255),
            self.rect.center,
            radio
        )


class Jugador:
    def __init__(self, x, y, pokemon_actual):
        self.pokemon_actual = pokemon_actual
        self.nombre = self.buscar_nombre()
        self.aplicar_estadisticas()
        self.rect = pygame.Rect(0, 0, self.hitbox_tamaño, self.hitbox_tamaño)
        self.rect.center = (x + 20, y + 20)
        self.direccion = 'sur'
        self.moviendose = False
        self.ultimo_golpe = -1000
        self.ultimo_proyectil = -1000
        self.atacando = False
        self.animador = AnimadorPokemon(self.nombre, self.rect, self.tamaño)

    def buscar_nombre(self):
        for nombre, datos in pokemones.items():
            if datos is self.pokemon_actual:
                return nombre
        return 'pokemon'

    def aplicar_estadisticas(self):
        stats = self.pokemon_actual.get('estadisticas_juego', {})
        self.vida = self.pokemon_actual.get('vida', 100) or 100
        self.velocidad = stats.get('velocidad', self.pokemon_actual.get('velocidad_movimiento', 5))
        self.tamaño = stats.get('tamaño', self.pokemon_actual.get('tamaño', 40))
        self.hitbox_tamaño = stats.get('hitbox', self.pokemon_actual.get('hitbox', self.tamaño))

    def cambiar_pokemon(self, nombre):
        if nombre not in pokemones:
            return

        centro = self.rect.center
        self.pokemon_actual = pokemones[nombre]
        self.nombre = nombre
        self.aplicar_estadisticas()
        self.rect = pygame.Rect(0, 0, self.hitbox_tamaño, self.hitbox_tamaño)
        self.rect.center = centro
        self.ultimo_golpe = -1000
        self.ultimo_proyectil = -1000
        self.atacando = False
        self.animador = AnimadorPokemon(self.nombre, self.rect, self.tamaño)

    def mover(self):
        teclas = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if teclas[pygame.K_w]:
            dy -= 1
        if teclas[pygame.K_s]:
            dy += 1
        if teclas[pygame.K_a]:
            dx -= 1
        if teclas[pygame.K_d]:
            dx += 1

        self.moviendose = dx != 0 or dy != 0

        if dx != 0 or dy != 0:
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
            elif dy > 0:
                self.direccion = 'sur'

            largo = (dx ** 2 + dy ** 2) ** 0.5
            dx /= largo
            dy /= largo
            self.rect.x += round(dx * self.velocidad)
            self.rect.y += round(dy * self.velocidad)
            self.rect.clamp_ip(pygame.Rect(50, 50, 900, 500))

    def obtener_ataque(self, categoria):
        ataques = self.pokemon_actual.get('ataques_estadisticas', {})
        datos = ataques.get(categoria)
        if datos is not None:
            return datos

        nombre = self.pokemon_actual.get('ataque_cuerpo' if categoria == 'cuerpo' else 'ataque_proyectil')
        if nombre not in movimientos:
            return None
        return movimientos[nombre]

    def atacar_cuerpo(self, enemigos):
        datos = self.obtener_ataque('cuerpo')
        if datos is None:
            return

        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_golpe < datos['enfriamiento'] or self.atacando:
            return

        self.ultimo_golpe = ahora
        self.atacando = True
        ataque_animacion = self.animador.buscar_ataque()
        if ataque_animacion:
            self.animador.cambiar(ataque_animacion, direcciones.index(self.direccion), False)

        vx, vy = direccion_vector[self.direccion]
        centro_x = self.rect.centerx + vx * datos['distancia'] / 2
        centro_y = self.rect.centery + vy * datos['distancia'] / 2
        hitbox = pygame.Rect(0, 0, datos['distancia'], datos['area'] * 2)
        hitbox.center = (round(centro_x), round(centro_y))

        for enemigo in enemigos:
            if enemigo.esta_vivo() and hitbox.colliderect(enemigo.rect):
                enemigo.recibir_ataque(datos, self.direccion)

    def atacar_proyectil(self, proyectiles):
        datos = self.obtener_ataque('proyectil')
        if datos is None:
            return

        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_proyectil < datos['enfriamiento'] or self.atacando:
            return

        self.ultimo_proyectil = ahora
        vx, vy = direccion_vector[self.direccion]
        x = self.rect.centerx + vx * max(20, self.hitbox_tamaño // 2)
        y = self.rect.centery + vy * max(20, self.hitbox_tamaño // 2)
        proyectiles.append(Proyectil(x, y, self.direccion, datos))

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
        self.vida -= cantidad
        if self.vida < 0:
            self.vida = 0

    def dibujar(self, ventana):
        if not self.animador.dibujar(ventana):
            tamaño = self.tamaño
            zona = pygame.Rect(0, 0, tamaño, tamaño)
            zona.center = self.rect.center
            pygame.draw.rect(ventana, (255, 50, 255), zona)


class Enemigo:
    def __init__(self):
        x = random.randint(100, 850)
        y = random.randint(100, 500)
        self.rect = pygame.Rect(x, y, 40, 40)
        self.vida = 100
        self.velocidad = 1
        self.ultimo_golpe = 0
        self.tiempo_entre_golpes = 500
        self.quieto_hasta = 0
        self.estado = None
        self.estado_hasta = 0
        self.proximo_estado = 0

    def perseguir(self, jugador):
        ahora = pygame.time.get_ticks()
        if ahora < self.quieto_hasta or self.estado == 'paralizar':
            return

        velocidad = self.velocidad
        if self.estado == 'ralentizar':
            velocidad *= 0.45

        if self.rect.x < jugador.rect.x:
            self.rect.x += velocidad
        elif self.rect.x > jugador.rect.x:
            self.rect.x -= velocidad

        if self.rect.y < jugador.rect.y:
            self.rect.y += velocidad
        elif self.rect.y > jugador.rect.y:
            self.rect.y -= velocidad

    def atacar(self, jugador):
        zona_ataque = self.rect.inflate(8, 8)
        if zona_ataque.colliderect(jugador.rect):
            ahora = pygame.time.get_ticks()
            if ahora - self.ultimo_golpe >= self.tiempo_entre_golpes:
                jugador.recibir_danio(10)
                self.ultimo_golpe = ahora
                self.quieto_hasta = ahora + 500

                dx = self.rect.centerx - jugador.rect.centerx
                dy = self.rect.centery - jugador.rect.centery
                self.retroceder(dx, dy, 70)

    def retroceder(self, dx, dy, dist):
        largo = (dx ** 2 + dy ** 2) ** 0.5
        if largo == 0:
            return

        dx_norm = dx / largo
        dy_norm = dy / largo
        self.rect.x += dx_norm * dist
        self.rect.y += dy_norm * dist
        self.rect.clamp_ip(pygame.Rect(50, 50, 900, 500))

    def recibir_ataque(self, datos, direccion=None):
        daño = datos['daño']
        self.recibir_danio(daño)

        efecto = datos.get('efecto')
        if efecto is not None:
            probabilidad = efecto.get('probabilidad', 100)
            if random.randint(1, 100) <= probabilidad:
                self.estado = efecto['tipo']
                self.estado_hasta = pygame.time.get_ticks() + efecto.get('duracion', 1000)
                self.proximo_estado = pygame.time.get_ticks() + 700

        retroceso = datos.get('retroceso', 0)
        if retroceso > 0 and direccion in direccion_vector:
            vx, vy = direccion_vector[direccion]
            self.retroceder(-vx, -vy, retroceso)

    def actualizar_estado(self):
        ahora = pygame.time.get_ticks()

        if self.estado == 'quemar' and ahora >= self.proximo_estado and ahora < self.estado_hasta:
            self.recibir_danio(3)
            self.proximo_estado = ahora + 700

        if ahora >= self.estado_hasta:
            self.estado = None

    def recibir_danio(self, cantidad):
        self.vida -= cantidad
        if self.vida < 0:
            self.vida = 0

    def esta_vivo(self):
        return self.vida > 0

    def dibujar(self, ventana):
        pygame.draw.rect(ventana, (255, 0, 0), self.rect)


class Juego:
    def __init__(self, ventana, pokemon_actual, pokemon_nombre=None):
        self.ventana = ventana
        self.reloj = pygame.time.Clock()
        self.ejecutando = True
        self.pokemon_actual = pokemon_actual
        self.pokemon_nombre = pokemon_nombre or self.buscar_nombre(pokemon_actual)
        self.jugador = Jugador(500, 400, pokemon_actual)
        self.enemigos = [Enemigo()]
        self.proyectiles = []
        self.debug = DebugMenu(ventana, self.pokemon_nombre)

    def buscar_nombre(self, datos):
        for nombre, pokemon in pokemones.items():
            if pokemon is datos:
                return nombre
        return 'pokemon'

    def abrir_debug(self):
        nombre = self.debug.abrir(self.pokemon_nombre)
        if nombre == 'salir':
            self.ejecutando = False
            return
        if nombre in pokemones and nombre != self.pokemon_nombre:
            self.pokemon_nombre = nombre
            self.pokemon_actual = pokemones[nombre]
            self.jugador.cambiar_pokemon(nombre)

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_x:
                    self.ejecutando = False

                if evento.key == pygame.K_F1:
                    self.abrir_debug()
                    continue

                if evento.key == pygame.K_e:
                    self.jugador.atacar_cuerpo(self.enemigos)

                if evento.key == pygame.K_q:
                    self.jugador.atacar_proyectil(self.proyectiles)

    def actualizar(self):
        self.jugador.mover()
        self.jugador.actualizar()

        for proyectil in self.proyectiles:
            proyectil.actualizar(self.enemigos)

        self.proyectiles = [proyectil for proyectil in self.proyectiles if proyectil.activo]

        for enemigo in self.enemigos:
            enemigo.actualizar_estado()

            if enemigo.esta_vivo():
                enemigo.perseguir(self.jugador)
                self.resolver_colision_ent(enemigo)
                enemigo.atacar(self.jugador)

        self.enemigos = [enemigo for enemigo in self.enemigos if enemigo.esta_vivo()]

        if not self.enemigos:
            self.enemigos.append(Enemigo())

        if self.jugador.vida <= 0:
            self.ejecutando = False

    def resolver_colision_ent(self, enemigo):
        jugador = self.jugador.rect
        enemigo_rect = enemigo.rect

        if not jugador.colliderect(enemigo_rect):
            return

        entrecruce_x = min(jugador.right, enemigo_rect.right) - max(jugador.left, enemigo_rect.left)
        entrecruce_y = min(jugador.bottom, enemigo_rect.bottom) - max(jugador.top, enemigo_rect.top)

        if entrecruce_x < entrecruce_y:
            if jugador.centerx < enemigo_rect.centerx:
                enemigo_rect.x += entrecruce_x
            else:
                enemigo_rect.x -= entrecruce_x
        else:
            if jugador.centery < enemigo_rect.centery:
                enemigo_rect.y += entrecruce_y
            else:
                enemigo_rect.y -= entrecruce_y

        enemigo_rect.clamp_ip(pygame.Rect(50, 50, 900, 500))

    def dibujar(self):
        self.ventana.fill((0, 0, 0))
        pygame.draw.rect(self.ventana, (255, 255, 255), (50, 50, 900, 500))

        for proyectil in self.proyectiles:
            proyectil.dibujar(self.ventana)

        self.jugador.dibujar(self.ventana)

        for enemigo in self.enemigos:
            enemigo.dibujar(self.ventana)

        pygame.draw.rect(
            self.ventana,
            (0, 200, 0),
            (20, 20, min(self.jugador.vida * 2, 300), 25)
        )

        if self.enemigos:
            pygame.draw.rect(
                self.ventana,
                (200, 0, 0),
                (780, 20, min(self.enemigos[0].vida * 2, 200), 25)
            )

        pygame.display.flip()

    def ejecutar(self):
        while self.ejecutando:
            self.manejar_eventos()
            self.actualizar()
            self.dibujar()
            self.reloj.tick(60)


class Menu:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ejecutando = True
        self.boton_jugar = pygame.Rect(150, 120, 200, 60)
        self.boton_ajustes = pygame.Rect(150, 240, 200, 60)
        self.boton_salir = pygame.Rect(150, 360, 200, 60)
        self.pokemon_actual = 'pikachu'
        self.debug = DebugMenu(ventana, self.pokemon_actual)
        self.fuente = pygame.font.Font(None, 24)

    def dibujar(self):
        self.ventana.fill((0, 0, 0))
        pygame.draw.rect(self.ventana, (200, 0, 0), self.boton_jugar)
        pygame.draw.rect(self.ventana, (0, 200, 0), self.boton_ajustes)
        pygame.draw.rect(self.ventana, (0, 0, 200), self.boton_salir)
        self.ventana.blit(self.fuente.render('Jugar', True, (255, 255, 255)), (220, 140))
        self.ventana.blit(self.fuente.render('Ajustes', True, (255, 255, 255)), (215, 260))
        self.ventana.blit(self.fuente.render('Salir', True, (255, 255, 255)), (225, 380))
        self.ventana.blit(self.fuente.render('F1: Menu debug', True, (255, 255, 255)), (700, 20))
        self.ventana.blit(self.fuente.render('Pokemon: ' + self.pokemon_actual, True, (255, 255, 255)), (700, 45))
        pygame.display.flip()

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False
                return 'salir'

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_x:
                    self.ejecutando = False
                    return 'salir'

                if evento.key == pygame.K_F1:
                    resultado = self.debug.abrir(self.pokemon_actual)
                    if resultado == 'salir':
                        self.ejecutando = False
                        return 'salir'
                    if resultado in pokemones:
                        self.pokemon_actual = resultado

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.boton_jugar.collidepoint(evento.pos):
                    return 'jugar'

                if self.boton_salir.collidepoint(evento.pos):
                    self.ejecutando = False
                    return 'salir'

        return None

    def ejecutar(self):
        reloj = pygame.time.Clock()

        while self.ejecutando:
            resultado = self.manejar_eventos()

            if resultado == 'jugar':
                juego = Juego(self.ventana, pokemones[self.pokemon_actual], self.pokemon_actual)
                juego.ejecutar()
                if juego.ejecutando is False and juego.jugador.vida <= 0:
                    self.pokemon_actual = juego.pokemon_nombre

            elif resultado == 'salir':
                return False

            self.dibujar()
            reloj.tick(60)

        return False


def main():
    pygame.init()
    pygame.display.set_caption('Pokemanic')
    ventana = pygame.display.set_mode((1000, 600))

    menu = Menu(ventana)
    menu.ejecutar()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
