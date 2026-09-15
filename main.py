
import pygame
import random
import sys



class Jugador:
    #hay que hacerle las colisiones, bajarle el cooldown, mejorar la distancia de la hitbox
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)

        self.vida = 100
        self.velocidad = 5

        self.ultimo_golpe = 0
        self.tiempo_entre_golpes = 200

    def mover(self):
        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_w] and self.rect.top > 50:
            self.rect.y -= self.velocidad

        if teclas[pygame.K_s] and self.rect.bottom < 550:
            self.rect.y += self.velocidad

        if teclas[pygame.K_a] and self.rect.left > 50:
            self.rect.x -= self.velocidad

        if teclas[pygame.K_d] and self.rect.right < 950:
            self.rect.x += self.velocidad

    def atacar(self, enemigo):
        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_e]:
            ahora = pygame.time.get_ticks()

            # Evita atacar muchas veces seguidas
            if ahora - self.ultimo_golpe >= self.tiempo_entre_golpes:

                # Zona de ataque delante del jugador
                hitbox = pygame.Rect(
                    self.rect.x,
                    self.rect.y,
                    100,
                    150
                )

                if hitbox.colliderect(enemigo.rect):
                    enemigo.recibir_danio(10)
                    self.ultimo_golpe = ahora

    def recibir_danio(self, cantidad):
        self.vida -= cantidad

        if self.vida < 0:
            self.vida = 0

    def dibujar(self, ventana):
        pygame.draw.rect(
            ventana,
            (255, 50, 255),
            self.rect
        )



class Enemigo:
    #hay que agregarle para que tenga colision con el usuario, y que cuando te ataque luego retroceda
    def __init__(self):
        x = random.randint(50, 900)
        y = random.randint(50, 500)
        self.rect = pygame.Rect(x, y, 40, 40)

        self.vida = 100
        self.velocidad = 1

        self.ultimo_golpe = 0
        self.tiempo_entre_golpes = 500
        self.quieto_hasta = 0
        self.tiempo_quieto = 500

    def perseguir(self, jugador):
        ahora = pygame.time.get_ticks()

        if ahora < self.quieto_hasta:
            return

        if self.rect.x < jugador.rect.x:
            self.rect.x += self.velocidad

        elif self.rect.x > jugador.rect.x:
            self.rect.x -= self.velocidad

        if self.rect.y < jugador.rect.y:
            self.rect.y += self.velocidad

        elif self.rect.y > jugador.rect.y:
            self.rect.y -= self.velocidad

    def retroceder(self, dx, dy, dist=30):
        # dx y dy son las  direcciónes de la que se aleja del jugador
        largo = (dx ** 2 + dy ** 2) ** 0.5

        if largo == 0:
            return 

        dx_norm = dx / largo
        dy_norm = dy / largo

        nueva_x = self.rect.x + dx_norm * dist
        nueva_y = self.rect.y + dy_norm * dist

        # clamping: no dejamos que se salga del escenario (50 a 950 / 50 a 550)
        nueva_x = max(50, min(nueva_x, 950 - self.rect.width))
        nueva_y = max(50, min(nueva_y, 550 - self.rect.height))

        self.rect.x = nueva_x
        self.rect.y = nueva_y

    def atacar(self, jugador):
        zona_ataque = self.rect.inflate(8, 8)

        if zona_ataque.colliderect(jugador.rect):
            ahora = pygame.time.get_ticks()

            if ahora - self.ultimo_golpe >= self.tiempo_entre_golpes:
                jugador.recibir_danio(10)
                self.ultimo_golpe = ahora
                self.quieto_hasta = ahora + self.tiempo_quieto
                #direccion
                dx = self.rect.centerx - jugador.rect.centerx
                dy = self.rect.centery - jugador.rect.centery
                self.retroceder(dx, dy, dist=100)



    def recibir_danio(self, cantidad):
        self.vida -= cantidad

        if self.vida < 0:
            self.vida = 0

    def esta_vivo(self):
        return self.vida > 0

    def dibujar(self, ventana):
        pygame.draw.rect(
            ventana,
            (255, 0, 0),
            self.rect
        )


class Juego:
    def __init__(self, ventana):
        self.ventana = ventana
        self.reloj = pygame.time.Clock()

        self.ejecutando = True

        self.jugador = Jugador(500, 400)
        self.enemigo = Enemigo()

    def manejar_eventos(self):
        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                self.ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_z:
                    self.ejecutando = False

    def actualizar(self):
        self.jugador.mover()

        self.jugador.atacar(self.enemigo)

        if self.enemigo.esta_vivo():
            self.enemigo.perseguir(self.jugador)
            self.resolver_colision_ent()
            self.enemigo.atacar(self.jugador)
        else:
            # Si el enemigo muere, aparece otro
            self.enemigo = Enemigo()

        if self.jugador.vida <= 0:
            self.ejecutando = False

    def resolver_colision_ent(self):
        jugador = self.jugador.rect
        enemigo = self.enemigo.rect

        if not jugador.colliderect(enemigo):
            return

        entrecruce_x = min(jugador.right, enemigo.right) - max(
            jugador.left, enemigo.left
        )
        entrecruce_y = min(jugador.bottom, enemigo.bottom) - max(
            jugador.top, enemigo.top
        )

        if entrecruce_x < entrecruce_y:
            if jugador.centerx < enemigo.centerx:
                enemigo.x += entrecruce_x
            else:
                enemigo.x -= entrecruce_x
        else:
            if jugador.centery < enemigo.centery:
                enemigo.y += entrecruce_y
            else:
                enemigo.y -= entrecruce_y

        enemigo.clamp_ip(pygame.Rect(50, 50, 900, 500))

    def dibujar(self):

        # Fondo
        self.ventana.fill((0, 0, 0))

        # Escenario
        pygame.draw.rect(
            self.ventana,
            (255, 255, 255),
            (50, 50, 900, 500)
        )

        # Jugador
        self.jugador.dibujar(self.ventana)

        # Enemigo
        self.enemigo.dibujar(self.ventana)

        # Barra de vida
        pygame.draw.rect(
            self.ventana,
            (0, 200, 0),
            (20, 20, self.jugador.vida * 2, 25)
        )

        # Barra de vida del enemigo
        pygame.draw.rect(
            self.ventana,
            (200, 0, 0),
            (780, 20, self.enemigo.vida * 2, 25)
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

        # Botones
        self.boton_jugar = pygame.Rect(
            150, 110, 200, 60
        )

        self.boton_ajustes = pygame.Rect(
            150, 230, 200, 60
        )

        self.boton_salir = pygame.Rect(
            150, 350, 200, 60
        )

    def dibujar(self):

        self.ventana.fill((0, 0, 0))

        pygame.draw.rect(
            self.ventana,
            (200, 0, 0),
            self.boton_jugar
        )

        pygame.draw.rect(
            self.ventana,
            (0, 200, 0),
            self.boton_ajustes
        )

        pygame.draw.rect(
            self.ventana,
            (0, 0, 200),
            self.boton_salir
        )

        pygame.display.flip()

    def manejar_eventos(self):

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                self.ejecutando = False
                return "salir"

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_z:
                    self.ejecutando = False
                    return "salir"

            if evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 1:

                    if self.boton_jugar.collidepoint(evento.pos):
                        return "jugar"

                    if self.boton_salir.collidepoint(evento.pos):
                        self.ejecutando = False
                        return "salir"

        return None

    def ejecutar(self):

        while self.ejecutando:

            resultado = self.manejar_eventos()

            if resultado == "jugar":
                juego = Juego(self.ventana)
                juego.ejecutar()

            elif resultado == "salir":
                return False

            self.dibujar()

            pygame.time.Clock().tick(60)

        return False


def main():

    pygame.init()

    pygame.display.set_caption("Pokemanic")

    ventana = pygame.display.set_mode((1000, 600))

    menu = Menu(ventana)

    menu.ejecutar()

    pygame.quit()
    sys.exit()


# Ejecutar programa
if __name__ == "__main__":
    main()
