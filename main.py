import pygame
def menu():
    ejecutando = True
    pygame.init()
    pygame.display.set_caption("pokemanic")
    while ejecutando:
        ventana = pygame.display.set_mode((1000, 600))
        for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_z]:
             ejecutando = False
        
        jugar = pygame.draw.rect(ventana, (200, 0, 0), (250, 120, 200, 80))
        ajustes = pygame.draw.rect(ventana, (0,200, 0), (250, 240, 200, 80))
        salir = pygame.draw.rect(ventana, (0, 0, 200), (250, 360, 200, 80))
        if salir.collidepoint(pygame.mouse.get_pos()):
            ejecutando = False
        if jugar.collidepoint(pygame.mouse.get_pos()):
            juego(ventana, ejecutando)
    
        pygame.display.flip()
def juego(ventana, ejecutando):
    ventana.fill((0, 0, 0))
    x = 500
    y = 400
    vida = 100
    while ejecutando:
        v = 5
        velocidad = float(v)
        direccion = ()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_z]:
             ejecutando = False
        if teclas[pygame.K_w] and  personaje.top > 50:
            y -= velocidad
            direccion = "arriba"
        if teclas[pygame.K_s] and  personaje.bottom < 550:
            y += velocidad
            direccion = "abajo"
        if teclas[pygame.K_a] and  personaje.left > 50:
            x -= velocidad
            direccion = "izquierda"
        if teclas[pygame.K_d] and personaje.right < 950:
            x += velocidad
            direccion = "derecha"
        ventana.fill((0, 0, 0))
        escenario = pygame.draw.rect(ventana, (255, 255, 255), (50, 50, 900,500))
        personaje = pygame.draw.rect(ventana, (255, 60, 255), (x, y, 40, 40))
        pygame.display.flip()
        #reloj = pygame.time.clock()
        #reloj.tick(60)
menu()
pygame.quit()
