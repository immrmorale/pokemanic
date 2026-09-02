import pygame

velocidad = 1
ancho = 800
alto = 600
x = 100
y = 100
direccion = ()
ejecutando = True
pygame.init()
ventana = pygame.display.set_mode((ancho, alto))
pygame.display.set_caption("Intento")
while ejecutando:

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_w] and  personaje.top > 0:
        y -= velocidad
        direccion = "arriba"
    if teclas[pygame.K_s] and  personaje.bottom < 600:
        y += velocidad
        direccion = "abajo"
    if teclas[pygame.K_a] and  personaje.left > 0:
        x -= velocidad
        direccion = "izquierda"
    if teclas[pygame.K_d] and personaje.right < 800:
        x += velocidad
        direccion = "derecha"
    if teclas[pygame.K_z]:
        ejecutando = False
    ventana.fill((0, 0, 0))
    personaje = pygame.draw.rect(ventana, (200, 60, 200), (x, y, 50, 50))
    pygame.display.flip()
pygame.quit()