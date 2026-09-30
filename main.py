import pygame
import random
import sys
import math
import os
from pokemones import pokemones, movimientos


DIRECCIONES = [
    'sur',
    'sureste',
    'este',
    'noreste',
    'norte',
    'noroeste',
    'oeste',
    'suroeste'
]

DIRECCION_VECTOR = {
    'sur': (0, 1),
    'sureste': (1, 1),
    'este': (1, 0),
    'noreste': (1, -1),
    'norte': (0, -1),
    'noroeste': (-1, -1),
    'oeste': (-1, 0),
    'suroeste': (-1, 1)
}


class AnimadorPokemon:
    def __init__(self, nombre, rect):
        self.nombre = nombre
        self.rect = rect
        self.animacion = 'idle'
        self.direccion = 0
        self.frame = 0
        self.tiempo_frame = 0
        self.frames = {}
        self.cargar_animaciones()

    def buscar_carpeta(self):
        raiz = os.path.join(os.path.dirname(__file__), 'assets', 'sprites', 'pokemones')
        opciones = [
            os.path.join(raiz, self.nombre),
            os.path.join(raiz, 'sprite_' + self.nombre[:5])
        ]

        for ruta in opciones:
            if os.path.isdir(ruta):
                return ruta

        equivalencias = {
            'lucario': 'sprite_luca',
            'blaziken': 'sprite_blazi'
        }

        if self.nombre in equivalencias:
            ruta = os.path.join(raiz, equivalencias[self.nombre])
            if os.path.isdir(ruta):
                return ruta

        return None

    def cargar_animaciones(self):
        carpeta = self.buscar_carpeta()

        if carpeta is None:
            return

        nombres = os.listdir(carpeta)

        for nombre_carpeta in nombres:
            ruta = os.path.join(carpeta, nombre_carpeta)
            if not os.path.isdir(ruta):
                continue

            animacion = nombre_carpeta.lower()
            if '_' in animacion:
                prefijo, resto = animacion.split('_', 1)
                if resto in ('walk', 'idle', 'strike', 'kick', 'attack'):
                    animacion = resto

            archivos = []
            for archivo in os.listdir(ruta):
                if archivo.lower().endswith('.png'):
                    try:
                        numero = int(os.path.splitext(archivo)[0])
                        archivos.append((numero, archivo))
                    except ValueError:
                        pass

            archivos.sort()
            imagenes = []

            for _, archivo in archivos:
                try:
                    imagenes.append(pygame.image.load(os.path.join(ruta, archivo)).convert_alpha())
                except pygame.error:
                    pass

            if len(imagenes) >= 8:
                cantidad_frames = len(imagenes) // 8
                self.frames[animacion] = []

                for direccion in range(8):
                    inicio = direccion * cantidad_frames
                    fin = inicio + cantidad_frames
                    self.frames[animacion].append(imagenes[inicio:fin])

    def cambiar(self, animacion, direccion):
        if animacion not in self.frames:
            if 'idle' in self.frames:
                animacion = 'idle'
            else:
                return

        if self.animacion != animacion or self.direccion != direccion:
            self.animacion = animacion
            self.direccion = direccion
            self.frame = 0
            self.tiempo_frame = 0

    def actualizar(self):
        if self.animacion not in self.frames:
            return

        frames = self.frames[self.animacion][self.direccion]
        if not frames:
            return

        self.tiempo_frame += 1

        if self.tiempo_frame >= 6:
            self.tiempo_frame = 0
            self.frame += 1

            if self.frame >= len(frames):
                self.frame = 0

    def esta_terminada(self):
        if self.animacion not in self.frames:
            return True

        frames = self.frames[self.animacion][self.direccion]
        return bool(frames) and self.frame >= len(frames) - 1

    def dibujar(self, ventana):
        if self.animacion in self.frames:
            frames = self.frames[self.animacion][self.direccion]
            if frames:
                imagen = frames[self.frame]
                posicion = imagen.get_rect(center=self.rect.center)
                ventana.blit(imagen, posicion)
                return True

        return False


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
        vx, vy = DIRECCION_VECTOR[self.direccion]
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
        self.rect = pygame.Rect(x, y, 40, 40)
        self.pokemon_actual = pokemon_actual
        self.nombre = self.buscar_nombre()
        self.vida = pokemon_actual['vida'] if pokemon_actual['vida'] is not None else 100
        self.velocidad = 5
        self.direccion = 'sur'
        self.ultimo_golpe = -1000
        self.ultimo_proyectil = -1000
        self.atacando = False
        self.tiempo_ataque = 0
        self.animador = AnimadorPokemon(self.nombre, self.rect)

    def buscar_nombre(self):
        for nombre, datos in pokemones.items():
            if datos is self.pokemon_actual:
                return nombre
        return 'pokemon'

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

    def atacar_cuerpo(self, enemigos):
        nombre = self.pokemon_actual.get('ataque_cuerpo')
        if nombre not in movimientos:
            return

        datos = movimientos[nombre]
        ahora = pygame.time.get_ticks()

        if ahora - self.ultimo_golpe < datos['enfriamiento']:
            return

        self.ultimo_golpe = ahora
        self.atacando = True
        self.tiempo_ataque = ahora

        vx, vy = DIRECCION_VECTOR[self.direccion]
        centro_x = self.rect.centerx + vx * datos['distancia'] / 2
        centro_y = self.rect.centery + vy * datos['distancia'] / 2
        hitbox = pygame.Rect(0, 0, datos['distancia'], datos['area'] * 2)
        hitbox.center = (round(centro_x), round(centro_y))

        for enemigo in enemigos:
            if enemigo.esta_vivo() and hitbox.colliderect(enemigo.rect):
                enemigo.recibir_ataque(datos, self.direccion)

    def atacar_proyectil(self, proyectiles):
        nombre = self.pokemon_actual.get('ataque_proyectil')
        if nombre not in movimientos:
            return

        datos = movimientos[nombre]
        ahora = pygame.time.get_ticks()

        if ahora - self.ultimo_proyectil < datos['enfriamiento']:
            return

        self.ultimo_proyectil = ahora
        vx, vy = DIRECCION_VECTOR[self.direccion]
        x = self.rect.centerx + vx * 30
        y = self.rect.centery + vy * 30
        proyectiles.append(Proyectil(x, y, self.direccion, datos))
        self.atacando = True
        self.tiempo_ataque = ahora

    def actualizar(self):
        ahora = pygame.time.get_ticks()

        if self.atacando and ahora - self.tiempo_ataque > 350:
            self.atacando = False

        if self.atacando:
            self.animador.cambiar(self.animador.frames.get('strike') and 'strike' or self.animador.frames.get('kick') and 'kick' or 'attack', DIRECCIONES.index(self.direccion))
        elif self.moviendose:
            self.animador.cambiar('walk', DIRECCIONES.index(self.direccion))
        else:
            self.animador.cambiar('idle', DIRECCIONES.index(self.direccion))

        self.animador.actualizar()

    def recibir_danio(self, cantidad):
        self.vida -= cantidad
        if self.vida < 0:
            self.vida = 0

    def dibujar(self, ventana):
        if not self.animador.dibujar(ventana):
            pygame.draw.rect(ventana, (255, 50, 255), self.rect)


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
        if retroceso > 0 and direccion in DIRECCION_VECTOR:
            vx, vy = DIRECCION_VECTOR[direccion]
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
    def __init__(self, ventana, pokemon_actual):
        self.ventana = ventana
        self.reloj = pygame.time.Clock()
        self.ejecutando = True
        self.pokemon_actual = pokemon_actual
        self.jugador = Jugador(500, 400, pokemon_actual)
        self.enemigos = [Enemigo()]
        self.proyectiles = []

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_z:
                    self.ejecutando = False

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
        self.botones_pokemon = []
        self.pokemon_actual = 'pikachu'
        self.scroll = 0
        self.scroll_maximo = 0

    def dibujar(self):
        self.ventana.fill((0, 0, 0))

        pygame.draw.rect(self.ventana, (200, 0, 0), self.boton_jugar)
        pygame.draw.rect(self.ventana, (0, 200, 0), self.boton_ajustes)
        pygame.draw.rect(self.ventana, (0, 0, 200), self.boton_salir)

        pygame.display.flip()

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False
                return 'salir'

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_z:
                    self.ejecutando = False
                    return 'salir'

                if evento.key == pygame.K_F1:
                    resultado = self.debugmenu()
                    if resultado == 'salir':
                        return 'salir'

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.boton_jugar.collidepoint(evento.pos):
                    return 'jugar'

                if self.boton_salir.collidepoint(evento.pos):
                    self.ejecutando = False
                    return 'salir'

        return None

    def debugmenu(self):
        ejecutando_debug = True
        self.scroll = 0
        reloj = pygame.time.Clock()

        while ejecutando_debug and self.ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.ejecutando = False
                    return 'salir'

                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_F1:
                        ejecutando_debug = False

                if evento.type == pygame.MOUSEWHEEL:
                    self.scroll -= evento.y * 60
                    self.scroll = max(0, min(self.scroll, self.scroll_maximo))

                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for boton, nombre in self.botones_pokemon:
                        if boton.collidepoint(evento.pos):
                            self.pokemon_actual = nombre
                            ejecutando_debug = False
                            break

            self.ventana.fill((20, 20, 20))
            self.botones_pokemon = []

            cantidad_filas = math.ceil(len(pokemones) / 4)
            alto_boton = 60
            espacio_y = 30
            contenido_alto = 80 + cantidad_filas * (alto_boton + espacio_y)
            self.scroll_maximo = max(0, contenido_alto - 550)

            for numpoke, nombre in enumerate(pokemones):
                xboton = 50 + (numpoke % 4) * 240
                yboton = 70 + (numpoke // 4) * (alto_boton + espacio_y) - self.scroll

                boton = pygame.Rect(xboton, yboton, 200, alto_boton)

                if boton.bottom >= 50 and boton.top <= 550:
                    pygame.draw.rect(self.ventana, (200, 200, 200), boton)
                    self.botones_pokemon.append((boton, nombre))

            pygame.display.flip()
            reloj.tick(60)

        return 'pokemon'

    def ejecutar(self):
        reloj = pygame.time.Clock()

        while self.ejecutando:
            resultado = self.manejar_eventos()

            if resultado == 'jugar':
                juego = Juego(self.ventana, pokemones[self.pokemon_actual])
                juego.ejecutar()

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
