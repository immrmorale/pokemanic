import pygame
import random
import sys

pygame.init()
pygame.display.set_caption("Pokemanic")
ventana = pygame.display.set_mode((1000, 600))
reloj = pygame.time.Clock()

ESCENARIO = pygame.Rect(50, 50, 900, 500)


def nuevo_enemigo():
    x = random.randint(50, 900)
    y = random.randint(50, 500)
    return {"rect": pygame.Rect(x, y, 40, 40), "vida": 100,
            "ultimo_golpe": 0, "quieto_hasta": 0}


def jugar():
    jugador = {"rect": pygame.Rect(500, 400, 40, 40), "vida": 100, "ultimo_golpe": 0}
    for a in range(5):
        enemigo = nuevo_enemigo()
    direccion = "arriba"
    while True:
        # Eventos
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_z):
                return

        zona = pygame.Rect(0, 0, 100, 100)
        ahora = pygame.time.get_ticks()
        teclas = pygame.key.get_pressed()
        j = jugador["rect"]
        en = enemigo["rect"]

        # Movimiento del jugador
        if teclas[pygame.K_w] and j.top > 50:
            j.y -= 5
            direccion = "arriba"
        if teclas[pygame.K_s] and j.bottom < 550:
            j.y += 5
            direccion = "abajo"
        if teclas[pygame.K_a] and j.left > 50:
            j.x -= 5
            direccion = "izquierda"
        if teclas[pygame.K_d] and j.right < 950:
            j.x += 5
            direccion = "derecha"

        # Ataque del jugador
        if direccion == "arriba":
            zona.center = (j.centerx, j.centery - 50)
        elif direccion == "abajo":
            zona.center = (j.centerx, j.centery + 50)
        elif direccion == "izquierda":
            zona.center = (j.centerx - 50, j.centery)
        elif direccion == "derecha":
            zona.center = (j.centerx + 50, j.centery)
        if teclas[pygame.K_e] and ahora - jugador["ultimo_golpe"] >= 200:
            if zona.colliderect(en):
                enemigo["vida"] = max(0, enemigo["vida"] - 10)
                jugador["ultimo_golpe"] = ahora

        if enemigo["vida"] <= 0:
            enemigo = nuevo_enemigo()
        else:
            # Perseguir al jugador
            if ahora >= enemigo["quieto_hasta"]:
                if en.x < j.x:
                    en.x += 1
                elif en.x > j.x:
                    en.x -= 1
                if en.y < j.y:
                    en.y += 1
                elif en.y > j.y:
                    en.y -= 1

            # Colisión jugador-enemigo: se empuja al enemigo
            if j.colliderect(en):
                cruce_x = min(j.right, en.right) - max(j.left, en.left)
                cruce_y = min(j.bottom, en.bottom) - max(j.top, en.top)
                if cruce_x < cruce_y:
                    en.x += cruce_x if j.centerx < en.centerx else -cruce_x
                else:
                    en.y += cruce_y if j.centery < en.centery else -cruce_y
                en.clamp_ip(ESCENARIO)

            # Ataque del enemigo y retroceso
            if en.inflate(8, 8).colliderect(j) and ahora - enemigo["ultimo_golpe"] >= 500:
                jugador["vida"] = max(0, jugador["vida"] - 10)
                enemigo["ultimo_golpe"] = ahora
                enemigo["quieto_hasta"] = ahora + 500

                dx = en.centerx - j.centerx
                dy = en.centery - j.centery
                largo = (dx ** 2 + dy ** 2) ** 0.5
                if largo != 0:
                    en.x = max(50, min(en.x + dx / largo * 100, 950 - en.width))
                    en.y = max(50, min(en.y + dy / largo * 100, 550 - en.height))

        if jugador["vida"] <= 0:
            return

        # Dibujo
        ventana.fill((0, 0, 0))
        pygame.draw.rect(ventana, (255, 255, 255), ESCENARIO)
        pygame.draw.rect(ventana, (255, 50, 255), j)
        pygame.draw.rect(ventana, (255, 0, 0), en)
        pygame.draw.rect(ventana, (0, 200, 0), (20, 20, jugador["vida"] * 2, 25))
        pygame.draw.rect(ventana, (200, 0, 0), (780, 20, enemigo["vida"] * 2, 25))
        pygame.display.flip()

        reloj.tick(60)


def menu():
    boton_jugar = pygame.Rect(150, 120, 200, 60)
    boton_ajustes = pygame.Rect(150, 240, 200, 60)
    boton_salir = pygame.Rect(150, 360, 200, 60)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_z):
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if boton_jugar.collidepoint(e.pos):
                    jugar()
                elif boton_salir.collidepoint(e.pos):
                    return

        ventana.fill((0, 0, 0))
        pygame.draw.rect(ventana, (200, 0, 0), boton_jugar)
        pygame.draw.rect(ventana, (0, 200, 0), boton_ajustes)
        pygame.draw.rect(ventana, (0, 0, 200), boton_salir)
        pygame.display.flip()

        reloj.tick(60)


menu()
pygame.quit()
sys.exit()