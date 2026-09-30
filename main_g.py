import pygame
import random
import sys

pygame.init()

ventana = pygame.display.set_mode((1000, 600))
pygame.display.set_caption("Pokemanic")
reloj = pygame.time.Clock()

ESCENARIO = pygame.Rect(50, 50, 900, 500)

VELOCIDAD_JUGADOR = 5
VELOCIDAD_ENEMIGO = 1
VELOCIDAD_PROYECTIL = 8
DISTANCIA_PROYECTIL = 500
DAÑO_JUGADOR = 25
DAÑO_PROYECTIL = 25
DAÑO_ENEMIGO = 10


def nuevo_enemigo():
    return {
        "rect": pygame.Rect(
            random.randint(50, 910),
            random.randint(50, 510),
            40,
            40
        ),
        "vida": 100,
        "ultimo_golpe": 0,
        "quieto_hasta": 0
    }


def nuevo_proyectil(jugador, direccion):
    j = jugador["rect"]

    if direccion == "arriba":
        x = j.centerx
        y = j.centery - 30
        dx = 0
        dy = -1

    elif direccion == "abajo":
        x = j.centerx
        y = j.centery + 30
        dx = 0
        dy = 1

    elif direccion == "izquierda":
        x = j.centerx - 30
        y = j.centery
        dx = -1
        dy = 0

    else:
        x = j.centerx + 30
        y = j.centery
        dx = 1
        dy = 0

    return {
        "x": float(x),
        "y": float(y),
        "dx": dx,
        "dy": dy,
        "distancia": 0,
        "rect": pygame.Rect(x - 8, y - 8, 16, 16),
        "activo": True
    }


def crear_puertas():
    """
    Crea 4 puertas:
    - Arriba
    - Abajo
    - Izquierda
    - Derecha
    """

    puertas = []

    puertas.append(
        pygame.Rect(
            ESCENARIO.centerx - 30,
            ESCENARIO.top - 5,
            60,
            20
        )
    )

    puertas.append(
        pygame.Rect(
            ESCENARIO.centerx - 30,
            ESCENARIO.bottom - 15,
            60,
            20
        )
    )

    puertas.append(
        pygame.Rect(
            ESCENARIO.left - 5,
            ESCENARIO.centery - 30,
            20,
            60
        )
    )

    puertas.append(
        pygame.Rect(
            ESCENARIO.right - 15,
            ESCENARIO.centery - 30,
            20,
            60
        )
    )

    return puertas


def jugar(niveles_comp):
    jugador = {
        "rect": pygame.Rect(500, 400, 40, 40),
        "vida": 100,
        "llave": False,
        "llave_disponible": False,
        "ultimo_golpe": 0,
        "ultimo_disparo": 0
    }

    enemigos = [nuevo_enemigo() for _ in range(5)]
    proyectiles = []

    puertas = crear_puertas()

    direccion = "arriba"

    while True:
        ahora = pygame.time.get_ticks()

        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                return niveles_comp, False

            if e.type == pygame.KEYDOWN:

                if e.key == pygame.K_z:
                    return niveles_comp, False

                if e.key == pygame.K_q:

                    if ahora - jugador["ultimo_disparo"] >= 300:
                        proyectiles.append(
                            nuevo_proyectil(jugador, direccion)
                        )

                        jugador["ultimo_disparo"] = ahora

        teclas = pygame.key.get_pressed()
        j = jugador["rect"]

        if teclas[pygame.K_w] and j.top > 50:
            j.y -= VELOCIDAD_JUGADOR
            direccion = "arriba"

        if teclas[pygame.K_s] and j.bottom < 550:
            j.y += VELOCIDAD_JUGADOR
            direccion = "abajo"

        if teclas[pygame.K_a] and j.left > 50:
            j.x -= VELOCIDAD_JUGADOR
            direccion = "izquierda"

        if teclas[pygame.K_d] and j.right < 950:
            j.x += VELOCIDAD_JUGADOR
            direccion = "derecha"

        zona = pygame.Rect(0, 0, 80, 80)

        if direccion == "arriba":
            zona.center = (j.centerx, j.centery - 45)

        elif direccion == "abajo":
            zona.center = (j.centerx, j.centery + 45)

        elif direccion == "izquierda":
            zona.center = (j.centerx - 45, j.centery)

        else:
            zona.center = (j.centerx + 45, j.centery)

        if teclas[pygame.K_e] and ahora - jugador["ultimo_golpe"] >= 200:

            golpeo = False

            for enemigo in enemigos:

                if zona.colliderect(enemigo["rect"]):
                    enemigo["vida"] -= DAÑO_JUGADOR
                    golpeo = True

            if golpeo:
                jugador["ultimo_golpe"] = ahora

        for proyectil in proyectiles:

            if not proyectil["activo"]:
                continue

            proyectil["x"] += proyectil["dx"] * VELOCIDAD_PROYECTIL
            proyectil["y"] += proyectil["dy"] * VELOCIDAD_PROYECTIL
            proyectil["distancia"] += VELOCIDAD_PROYECTIL

            proyectil["rect"].center = (
                round(proyectil["x"]),
                round(proyectil["y"])
            )

            if proyectil["distancia"] >= DISTANCIA_PROYECTIL:
                proyectil["activo"] = False
                continue

            if not ESCENARIO.colliderect(proyectil["rect"]):
                proyectil["activo"] = False
                continue

            for enemigo in enemigos:

                if enemigo["vida"] <= 0:
                    continue

                if proyectil["rect"].colliderect(enemigo["rect"]):

                    enemigo["vida"] -= DAÑO_PROYECTIL
                    proyectil["activo"] = False
                    break

        proyectiles = [
            proyectil
            for proyectil in proyectiles
                if proyectil["activo"]]

        for enemigo in enemigos[:]:

            en = enemigo["rect"]

            if enemigo["vida"] <= 0:
                enemigos.remove(enemigo)
                continue

            if ahora >= enemigo["quieto_hasta"]:
                if en.x < j.x:
                    en.x += VELOCIDAD_ENEMIGO
                elif en.x > j.x:
                    en.x -= VELOCIDAD_ENEMIGO
                if en.y < j.y:
                    en.y += VELOCIDAD_ENEMIGO
                elif en.y > j.y:
                    en.y -= VELOCIDAD_ENEMIGO

            if j.colliderect(en):
                if j.centerx < en.centerx:
                    en.x += 1
                else:
                    en.x -= 1
                if j.centery < en.centery:
                    en.y += 1
                else:
                    en.y -= 1
                en.clamp_ip(ESCENARIO)

            if (
                en.inflate(8, 8).colliderect(j)
                and ahora - enemigo["ultimo_golpe"] >= 500
            ):

                jugador["vida"] -= DAÑO_ENEMIGO
                enemigo["ultimo_golpe"] = ahora
                enemigo["quieto_hasta"] = ahora + 500

                dx = en.centerx - j.centerx
                dy = en.centery - j.centery
                distancia = (dx ** 2 + dy ** 2) ** 0.5

                if distancia:

                    en.x += int(dx / distancia * 100)
                    en.y += int(dy / distancia * 100)

                    en.clamp_ip(ESCENARIO)

        if len(enemigos) == 0:
            jugador["llave_disponible"] = True

        if jugador["llave_disponible"] and not jugador["llave"]:
            llave = pygame.Rect(0, 0, 30, 30)
            llave.center = ESCENARIO.center

            if j.colliderect(llave):
                jugador["llave"] = True

        if jugador["vida"] <= 0:
            return niveles_comp, False

        if jugador["llave"]:

            for puerta in puertas:

                if j.colliderect(puerta):

                    niveles_comp += 1

                    return niveles_comp, True

        ventana.fill((0, 0, 0))
        pygame.draw.rect(ventana,(255, 255, 255),ESCENARIO)

        for puerta in puertas:

            pygame.draw.rect(ventana,(120, 70, 30),puerta)

        for proyectil in proyectiles:

            pygame.draw.circle(ventana,(80, 180, 255),proyectil["rect"].center,8)

        pygame.draw.rect(ventana,(255, 50, 255),j)

        for enemigo in enemigos:
            en = enemigo["rect"]
            pygame.draw.rect(ventana,(255, 0, 0),en)
            pygame.draw.rect(ventana,(80, 0, 0),(en.x, en.y - 9, 40, 5))
            pygame.draw.rect(ventana,(0, 200, 0),(en.x, en.y - 9,max(0, enemigo["vida"] * 40 // 100),5))
        if jugador["llave_disponible"] and not jugador["llave"]:
            llave = pygame.Rect(0, 0, 30, 30)
            llave.center = ESCENARIO.center
        pygame.draw.rect(ventana,(255, 255, 0),llave)
        pygame.draw.rect(ventana,(0, 200, 0),(20, 20, jugador["vida"] * 2, 25))
        if jugador["llave"]:
            pygame.draw.rect(ventana,(255, 255, 0),(230, 20, 25, 25))

        fuente = pygame.font.Font(None, 28)
        texto_niveles = fuente.render("Niveles comp.: " + str(niveles_comp),True,(255, 255, 255))
        ventana.blit(texto_niveles,(75, 20))
        pygame.display.flip()
        reloj.tick(60)

def menu():
    jugar_boton = pygame.Rect(150, 120, 200, 60)
    ajustes_boton = pygame.Rect(150, 210, 200, 60)
    salir_boton = pygame.Rect(150, 300, 200, 60)
    niveles_comp = 0
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_z:
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if jugar_boton.collidepoint(e.pos):
                    niveles_comp, continuar = jugar(niveles_comp)
                elif ajustes_boton.collidepoint(e.pos):
                    pass
                elif salir_boton.collidepoint(e.pos):
                    return
        ventana.fill((0, 0, 0))
        pygame.draw.rect(ventana,(200, 0, 0),jugar_boton)
        pygame.draw.rect(ventana,(0, 200, 0),ajustes_boton)
        pygame.draw.rect(ventana,(0, 0, 200),salir_boton)
        pygame.display.flip()
        reloj.tick(60)
menu()
pygame.quit()
sys.exit()