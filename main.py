<<<<<<< HEAD
import pygame 
import time
import random
import pygame
def menu():
    ejecutando = True
    pygame.init()
    pygame.display.set_caption("pokemanic")
    jugar = pygame.draw.rect(ventana, (200, 0, 0), (250, 120, 200, 80))
    ajustes = pygame.draw.rect(ventana, (0,200, 0), (250, 240, 200, 80))
    while ejecutando:

        ventana = pygame.display.set_mode((1000, 600))
        for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_z]:
             ejecutando = False
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1: 
                if jugar.collidepoint(evento.pos):
                    juego(ventana,ejecutando)
                if salir.collidepoint(evento.pos):
                    ejecutando = False
        pygame.display.flip()
def juego(ventana, ejecutando):
    ventana.fill((0, 0, 0))
    vida = 100
    x = 500
    y = 400
    cont = 0
    xe = random.randint(0,1000)
    ye = random.randint(0,600)
    ultimo_golpe = 0
    tiempo_entre_golpes = 500
    while ejecutando:
<<<<<<< HEAD
        ventana.fill((0, 0, 0))
        personaje = pygame.draw.rect(ventana, (255, 50, 255), (x, y, 75, 75))
        enemigo = pygame.draw.rect(ventana,(255, 0, 0),(xe , ye, 75 ,75 ) )
        pygame.draw.rect(ventana, (0, 200, 0), (20, 20, vida * 2, 25))
        reloj = pygame.time.Clock()
        reloj.tick(60)
        cont += 1
        velocidad = 5
        velocidad_e = 2
        direccion = ()        
=======
        v = 5
        direccion = ()
>>>>>>> a13210ad661c49f7afc419087d3cb03c1d357157
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_z]:
             ejecutando = False
        if teclas[pygame.K_w] and  personaje.top > 0:
        if teclas[pygame.K_w] and  personaje.top > 50:
            y -= velocidad
            direccion = "arriba"
        if teclas[pygame.K_s] and  personaje.bottom < 600:
        if teclas[pygame.K_s] and  personaje.bottom < 550:
            y += velocidad
            direccion = "abajo"
        if teclas[pygame.K_a] and  personaje.left > 0:
        if teclas[pygame.K_a] and  personaje.left > 50:
            x -= velocidad
            direccion = "izquierda"
        if teclas[pygame.K_d] and personaje.right < 1000:
        if teclas[pygame.K_d] and personaje.right < 950:
            x += velocidad
            direccion = "derecha"
        if xe < x:
            xe += velocidad_e
        elif xe > x:
            xe -= velocidad_e
        if ye < y:
            ye += velocidad_e
        elif ye > y:
            ye -= velocidad_e
        if enemigo.colliderect(personaje):
            ahora = pygame.time.get_ticks()
            if ahora - ultimo_golpe >= tiempo_entre_golpes:
                vida -= 10
                ultimo_golpe = ahora
        if vida == 0:
            ejecutando = False
        pygame.display.flip()

        ventana.fill((0, 0, 0))
        escenario = pygame.draw.rect(ventana, (255, 255, 255), (50, 50, 900,500))
menu()
pygame.quit()
