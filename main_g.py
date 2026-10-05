import pygame
import random
import math
import sys

pygame.init()

ventana = pygame.display.set_mode((1000, 600))
pygame.display.set_caption("Pokemanic")
reloj = pygame.time.Clock()

# CONFIGURACIÓN
ESCENARIO = pygame.Rect(0, 0, 2400, 1600)
W, H = 1000, 600
PARED = 40
AREA = ESCENARIO.inflate(-PARED * 2, -PARED * 2)  # Área jugable interior

VEL_JUGADOR = 5
VEL_ENEMIGO = 1
VEL_PROYECTIL = 8

DISTANCIA_PROYECTIL = 250
DISTANCIA_DETECCION = 350
DISTANCIA_DISPARO_ENEMIGO = 500

DAÑO_JUGADOR = 25
DAÑO_PROYECTIL = 25
DAÑO_TIRADOR = 5
DAÑO_MELEE = 10
DAÑO_GRANDE = 25
DAÑO_JEFE = 35

COOLDOWN_JUGADOR = 300
COOLDOWN_ENEMIGO = 1500
COOLDOWN_JEFE = 5000
COOLDOWN_PIEDRA = 2000
DURACION_PIEDRA = 5000
DAÑO_PIEDRA = 15

CANTIDAD_ENEMIGOS = 10
CANTIDAD_PIEDRAS = 30

# JEFE
TAM_JEFE = 160
BALAS_JEFE = 24        # antes 8 (el triple)
PIEDRAS_VERDES_POR_USO = 4


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


def crear_enemigo(piedras):
    tipos = {
        "tirador": (40, 100, DAÑO_TIRADOR, (0, 120, 255)),
        "melee": (40, 100, DAÑO_MELEE, (255, 0, 0)),
        "grande": (60, 180, DAÑO_GRANDE, (180, 0, 180))
    }

    while True:
        tipo = random.choice(list(tipos))
        tamaño, vida, daño, color = tipos[tipo]

        rect = pygame.Rect(
            random.randint(PARED + 10, ESCENARIO.width - PARED - tamaño - 10),
            random.randint(PARED + 10, ESCENARIO.height - PARED - tamaño - 10),
            tamaño, tamaño
        )

        centro = pygame.Vector2(ESCENARIO.center)
        if pygame.Vector2(rect.center).distance_to(centro) <= 300:
            continue
        if any(rect.colliderect(p) for p in piedras):
            continue
        break

    ahora = pygame.time.get_ticks()
    return {
        "rect": rect, "vida": vida, "max": vida, "tipo": tipo,
        "daño": daño, "color": color, "golpe": 0, "disparo": 0,
        "quieto": 0, "cambio": ahora,
        "dx": random.choice([-1, 0, 1]), "dy": random.choice([-1, 0, 1])
    }


def crear_jefe(piedras):
    while True:
        rect = pygame.Rect(
            random.randint(PARED + 100, ESCENARIO.width - PARED - TAM_JEFE - 100),
            random.randint(PARED + 100, ESCENARIO.height - PARED - TAM_JEFE - 100),
            TAM_JEFE, TAM_JEFE
        )

        if pygame.Vector2(rect.center).distance_to(
            pygame.Vector2(ESCENARIO.center)
        ) <= 400:
            continue
        if any(rect.colliderect(p.inflate(20, 20)) for p in piedras):
            continue
        break

    ahora = pygame.time.get_ticks()
    return {
        "rect": rect, "vida": 500, "max": 500, "daño": DAÑO_JEFE,
        "golpe": 0, "disparo": ahora, "poder": ahora,
        "cambio": ahora, "dx": random.choice([-1, 0, 1]),
        "dy": random.choice([-1, 0, 1])
    }


def crear_jugador():
    return {
        "rect": pygame.Rect(ESCENARIO.centerx - 20, ESCENARIO.centery - 20, 40, 40),
        "vida": 100, "llave": False, "disparo": 0, "golpe": 0
    }


def proyectil(x, y, dx, dy, enemigo=False, jefe=False, daño=DAÑO_PROYECTIL):
    return {
        "x": float(x), "y": float(y), "dx": dx, "dy": dy,
        "dist": 0, "rect": pygame.Rect(int(x) - 8, int(y) - 8, 16, 16),
        "activo": True, "enemigo": enemigo, "jefe": jefe, "daño": daño
    }


def disparo_jugador(jugador, direccion):
    r = jugador["rect"]
    direcciones = {
        "arriba": (r.centerx, r.centery - 30, 0, -1),
        "abajo": (r.centerx, r.centery + 30, 0, 1),
        "izquierda": (r.centerx - 30, r.centery, -1, 0),
        "derecha": (r.centerx + 30, r.centery, 1, 0)
    }
    return proyectil(*direcciones[direccion])


def disparo_enemigo(enemigo, jugador):
    e, j = enemigo["rect"], jugador["rect"]
    v = pygame.Vector2(j.center) - pygame.Vector2(e.center)

    if not v.length():
        return None

    v = v.normalize()
    return proyectil(
        e.centerx + v.x * 30,
        e.centery + v.y * 30,
        v.x, v.y, True, False, DAÑO_TIRADOR
    )


def disparos_jefe(jefe):
    v = []
    radio = jefe["rect"].width // 2 + 10
    for i in range(BALAS_JEFE):
        a = i * (2 * math.pi / BALAS_JEFE)
        dx, dy = math.cos(a), math.sin(a)
        x = jefe["rect"].centerx + dx * radio
        y = jefe["rect"].centery + dy * radio
        v.append(proyectil(x, y, dx, dy, True, True))
    return v


def piedras_verdes(jefe, piedras):
    nuevas = []
    for _ in range(PIEDRAS_VERDES_POR_USO):
        for _ in range(20):
            a = random.uniform(0, math.pi * 2)
            distancia = random.randint(120, 400)
            x = jefe["rect"].centerx + math.cos(a) * distancia
            y = jefe["rect"].centery + math.sin(a) * distancia
            p = pygame.Rect(int(x), int(y), 45, 45)

            if not AREA.contains(p) or p.colliderect(jefe["rect"]):
                continue
            if any(p.colliderect(o["rect"]) for o in piedras + nuevas):
                continue

            nuevas.append({"rect": p, "tiempo": pygame.time.get_ticks(), "daño": 0})
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
    r = jugador["rect"]
    x = max(0, min(r.centerx - W // 2, ESCENARIO.width - W))
    y = max(0, min(r.centery - H // 2, ESCENARIO.height - H))
    return x, y


def pantalla(rect, cx, cy):
    return pygame.Rect(rect.x - cx, rect.y - cy, rect.width, rect.height)


def jugar(niveles):
    jugador = crear_jugador()
    piedras = crear_piedras()
    es_nivel_jefe = niveles > 0 and niveles % 3 == 0
    # En el nivel del jefe aparece solo el jefe
    enemigos = [] if es_nivel_jefe else [crear_enemigo(piedras) for _ in range(CANTIDAD_ENEMIGOS)]
    jefe = crear_jefe(piedras) if es_nivel_jefe else None
    puertas = crear_puertas()
    proyectiles = []
    verdes = []
    llave = None
    direccion = "arriba"

    while True:
        ahora = pygame.time.get_ticks()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_z:
                return niveles, False

            if e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                if ahora - jugador["disparo"] >= COOLDOWN_JUGADOR:
                    proyectiles.append(disparo_jugador(jugador, direccion))
                    jugador["disparo"] = ahora

        teclas = pygame.key.get_pressed()
        j = jugador["rect"]

        dx = (teclas[pygame.K_d] - teclas[pygame.K_a]) * VEL_JUGADOR
        dy = (teclas[pygame.K_s] - teclas[pygame.K_w]) * VEL_JUGADOR

        if teclas[pygame.K_w]: direccion = "arriba"
        if teclas[pygame.K_s]: direccion = "abajo"
        if teclas[pygame.K_a]: direccion = "izquierda"
        if teclas[pygame.K_d]: direccion = "derecha"

        mover(j, dx, 0, piedras)
        mover(j, 0, dy, piedras)
        j.clamp_ip(AREA)

        # ATAQUE MELEE
        zona = j.inflate(80, 80)
        if direccion == "arriba": zona.centery -= 45
        elif direccion == "abajo": zona.centery += 45
        elif direccion == "izquierda": zona.centerx -= 45
        else: zona.centerx += 45

        if teclas[pygame.K_e] and ahora - jugador["golpe"] >= 200:
            golpe = False

            for enemigo in enemigos:
                if zona.colliderect(enemigo["rect"]):
                    enemigo["vida"] -= DAÑO_JUGADOR
                    golpe = True

            if jefe and zona.colliderect(jefe["rect"]):
                jefe["vida"] -= DAÑO_JUGADOR
                golpe = True

            if golpe:
                jugador["golpe"] = ahora

        # ENEMIGOS
        for enemigo in enemigos[:]:
            if enemigo["vida"] <= 0:
                enemigos.remove(enemigo)
                continue

            r = enemigo["rect"]
            distancia = pygame.Vector2(r.center).distance_to(j.center)

            if distancia <= DISTANCIA_DETECCION and ahora >= enemigo["quieto"]:
                ex = (j.centerx > r.centerx) - (j.centerx < r.centerx)
                ey = (j.centery > r.centery) - (j.centery < r.centery)
                mover(r, ex * VEL_ENEMIGO, ey * VEL_ENEMIGO, piedras)

                if (
                    enemigo["tipo"] == "tirador"
                    and distancia <= DISTANCIA_DISPARO_ENEMIGO
                    and ahora - enemigo["disparo"] >= COOLDOWN_ENEMIGO
                ):
                    p = disparo_enemigo(enemigo, jugador)
                    if p:
                        proyectiles.append(p)
                        enemigo["disparo"] = ahora
            else:
                if ahora >= enemigo["cambio"]:
                    enemigo["dx"] = random.choice([-1, 0, 1])
                    enemigo["dy"] = random.choice([-1, 0, 1])
                    enemigo["cambio"] = ahora + random.randint(500, 1500)

                mover(
                    r,
                    enemigo["dx"] * VEL_ENEMIGO,
                    enemigo["dy"] * VEL_ENEMIGO,
                    piedras
                )

            r.clamp_ip(AREA)

            if enemigo["tipo"] in ("melee", "grande") and j.colliderect(r):
                if ahora - enemigo["golpe"] >= 500:
                    jugador["vida"] -= enemigo["daño"]
                    enemigo["golpe"] = ahora
                    enemigo["quieto"] = ahora + 500

        # JEFE
        if jefe:
            r = jefe["rect"]

            if jefe["vida"] <= 0:
                jefe = None
            else:
                distancia = pygame.Vector2(r.center).distance_to(j.center)

                if distancia <= DISTANCIA_DETECCION + 150:
                    mover(
                        r,
                        (j.centerx > r.centerx) - (j.centerx < r.centerx),
                        (j.centery > r.centery) - (j.centery < r.centery),
                        piedras
                    )
                else:
                    if ahora >= jefe["cambio"]:
                        jefe["dx"] = random.choice([-1, 0, 1])
                        jefe["dy"] = random.choice([-1, 0, 1])
                        jefe["cambio"] = ahora + random.randint(500, 1500)
                    mover(r, jefe["dx"], jefe["dy"], piedras)

                r.clamp_ip(AREA)

                if ahora - jefe["disparo"] >= COOLDOWN_JEFE:
                    proyectiles.extend(disparos_jefe(jefe))
                    jefe["disparo"] = ahora

                if ahora - jefe["poder"] >= COOLDOWN_PIEDRA:
                    verdes.extend(piedras_verdes(jefe, verdes))
                    jefe["poder"] = ahora

                if j.colliderect(r) and ahora - jefe["golpe"] >= 700:
                    jugador["vida"] -= DAÑO_JEFE
                    jefe["golpe"] = ahora

        # PIEDRAS VERDES
        for p in verdes[:]:
            if ahora - p["tiempo"] >= DURACION_PIEDRA:
                verdes.remove(p)
                continue

            if j.colliderect(p["rect"]) and ahora - p["daño"] >= 500:
                jugador["vida"] -= DAÑO_PIEDRA
                p["daño"] = ahora

        # PROYECTILES
        for p in proyectiles:
            if not p["activo"]:
                continue

            p["x"] += p["dx"] * VEL_PROYECTIL
            p["y"] += p["dy"] * VEL_PROYECTIL
            p["dist"] += VEL_PROYECTIL
            p["rect"].center = (round(p["x"]), round(p["y"]))

            if p["dist"] >= DISTANCIA_PROYECTIL or not ESCENARIO.colliderect(p["rect"]):
                p["activo"] = False
                continue

            if any(p["rect"].colliderect(x) for x in piedras):
                p["activo"] = False
                continue

            if p["enemigo"]:
                if p["rect"].colliderect(j):
                    jugador["vida"] -= p["daño"]
                    p["activo"] = False
            else:
                for enemigo in enemigos:
                    if p["rect"].colliderect(enemigo["rect"]):
                        enemigo["vida"] -= p["daño"]
                        p["activo"] = False
                        break

                if p["activo"] and jefe and p["rect"].colliderect(jefe["rect"]):
                    jefe["vida"] -= p["daño"]
                    p["activo"] = False

        proyectiles = [p for p in proyectiles if p["activo"]]

        # LLAVE
        todos_derrotados = len(enemigos) == 0 and jefe is None

        if todos_derrotados and llave is None and not jugador["llave"]:
            llave = pygame.Rect(0, 0, 30, 30)
            llave.center = ESCENARIO.center

        if llave and j.colliderect(llave):
            jugador["llave"] = True
            llave = None

        # MUERTE
        if jugador["vida"] <= 0:
            return niveles, False

        # PUERTAS / SIGUIENTE NIVEL
        if jugador["llave"] and any(j.colliderect(p.inflate(20, 20)) for p in puertas):
            return niveles + 1, True

        # DIBUJADO
        cx, cy = camara(jugador)
        ventana.fill((0, 0, 0))

        suelo = pantalla(ESCENARIO, cx, cy)
        pygame.draw.rect(ventana, (255, 255, 255), suelo)

        # Paredes
        for p in [
            pygame.Rect(0, 0, ESCENARIO.width, PARED),
            pygame.Rect(0, ESCENARIO.bottom - PARED, ESCENARIO.width, PARED),
            pygame.Rect(0, 0, PARED, ESCENARIO.height),
            pygame.Rect(ESCENARIO.right - PARED, 0, PARED, ESCENARIO.height)
        ]:
            pygame.draw.rect(ventana, (0, 0, 0), pantalla(p, cx, cy))

        # Piedras
        for p in piedras:
            pygame.draw.ellipse(ventana, (100, 100, 100), pantalla(p, cx, cy))

        for p in verdes:
            pygame.draw.ellipse(ventana, (0, 220, 80), pantalla(p["rect"], cx, cy))

        # Puertas
        for p in puertas:
            pygame.draw.rect(ventana, (120, 70, 30), pantalla(p, cx, cy))

        # Proyectiles
        for p in proyectiles:
            x, y = round(p["x"] - cx), round(p["y"] - cy)
            if -20 <= x <= W + 20 and -20 <= y <= H + 20:
                color = (255, 50, 0) if p.get("jefe") else (
                    (255, 150, 0) if p["enemigo"] else (80, 180, 255)
                )
                pygame.draw.circle(ventana, color, (x, y), 9 if p.get("jefe") else 8)

        # Jugador
        pygame.draw.rect(ventana, (255, 50, 255), pantalla(j, cx, cy))

        # Enemigos
        for e in enemigos:
            r = pantalla(e["rect"], cx, cy)
            pygame.draw.rect(ventana, e["color"], r)
            pygame.draw.rect(ventana, (80, 0, 0), (r.x, r.y - 9, r.width, 5))
            pygame.draw.rect(
                ventana, (0, 200, 0),
                (r.x, r.y - 9, max(0, e["vida"] * r.width // e["max"]), 5)
            )

        # Jefe
        if jefe:
            r = pantalla(jefe["rect"], cx, cy)
            pygame.draw.rect(ventana, (255, 140, 0), r)
            pygame.draw.rect(ventana, (80, 0, 0), (r.x, r.y - 12, r.width, 8))
            pygame.draw.rect(
                ventana, (255, 0, 0),
                (r.x, r.y - 12, max(0, jefe["vida"] * r.width // jefe["max"]), 8)
            )

        # Llave
        if llave:
            pygame.draw.rect(ventana, (255, 255, 0), pantalla(llave, cx, cy))

        # Interfaz
        pygame.draw.rect(ventana, (80, 0, 0), (20, 20, 200, 25))
        pygame.draw.rect(ventana, (0, 200, 0), (20, 20, max(0, jugador["vida"] * 2), 25))

        if jugador["llave"]:
            pygame.draw.rect(ventana, (255, 255, 0), (230, 20, 25, 25))

        texto = pygame.font.Font(None, 28).render(
            "Niveles comp.: " + str(niveles), True, (180, 0, 255)
        )
        ventana.blit(texto, (270, 20))

        pygame.display.flip()
        reloj.tick(60)


def menu():
    jugar_boton = pygame.Rect(150, 120, 200, 60)
    ajustes_boton = pygame.Rect(150, 210, 200, 60)
    salir_boton = pygame.Rect(150, 300, 200, 60)

    niveles = 0

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_z:
                return

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if jugar_boton.collidepoint(e.pos):
                    niveles, _ = jugar(niveles)
                elif salir_boton.collidepoint(e.pos):
                    return

        ventana.fill((0, 0, 0))
        pygame.draw.rect(ventana, (200, 0, 0), jugar_boton)
        pygame.draw.rect(ventana, (0, 200, 0), ajustes_boton)
        pygame.draw.rect(ventana, (0, 0, 200), salir_boton)
        pygame.display.flip()
        reloj.tick(60)


menu()
pygame.quit()
sys.exit()