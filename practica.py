import pygame
import sys

pygame.init()

ANCHO = 800
ALTO = 600
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Enemigo que persigue")

reloj = pygame.time.Clock()

BLANCO = (255, 255, 255)
AZUL = (50, 100, 255)
ROJO = (255, 50, 50)
NEGRO = (0, 0, 0)

jugador = pygame.Rect(100, 100, 40, 40)
velocidad_jugador = 5

vida = 100

enemigo = pygame.Rect(600, 400, 40, 40)
velocidad_enemigo = 2

ultimo_golpe = 0
tiempo_entre_golpes = 500 

while True:

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    teclas = pygame.key.get_pressed()

    if teclas[pygame.K_w]:
        jugador.y -= velocidad_jugador
    if teclas[pygame.K_s]:
        jugador.y += velocidad_jugador
    if teclas[pygame.K_a]:
        jugador.x -= velocidad_jugador
    if teclas[pygame.K_d]:
        jugador.x += velocidad_jugador

    if enemigo.x < jugador.x:
        enemigo.x += velocidad_enemigo
    elif enemigo.x > jugador.x:
        enemigo.x -= velocidad_enemigo

    if enemigo.y < jugador.y:
        enemigo.y += velocidad_enemigo
    elif enemigo.y > jugador.y:
        enemigo.y -= velocidad_enemigo

    ahora = pygame.time.get_ticks()

    if enemigo.colliderect(jugador):

        if ahora - ultimo_golpe >= tiempo_entre_golpes:
            vida -= 10
            ultimo_golpe = ahora

            print("¡Te golpearon! Vida:", vida)

    if vida <= 0:
        print("GAME OVER")
        pygame.quit()
        sys.exit()

    pantalla.fill(BLANCO)

    pygame.draw.rect(pantalla, AZUL, jugador)
    pygame.draw.rect(pantalla, ROJO, enemigo)

    pygame.draw.rect(pantalla, NEGRO, (20, 20, 200, 25))
    pygame.draw.rect(pantalla, (0, 200, 0), (20, 20, vida * 2, 25))

    pygame.display.flip()
    reloj.tick(60)
