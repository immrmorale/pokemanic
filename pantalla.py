"""
pantalla.py - El juego se dibuja siempre en 1000x600 y se escala a la ventana (o a pantalla completa) con franjas negras si hace falta.

    ventana = pantalla.iniciar(W, H, config)    # superficie donde se dibuja todo
    pantalla.presentar()                        # en vez de pygame.display.flip()
    pantalla.raton()                            # en vez de pygame.mouse.get_pos() (ya en coordenadas del juego)
    pantalla.a_logico(e.pos)                    # posicion de un evento del mouse en coordenadas del juego
"""

import pygame

estado = {'real': None, 'logica': None, 'destino': pygame.Rect(0, 0, 1, 1)}


def iniciar(W, H, config):
    estado['logica'] = pygame.Surface((W, H))
    aplicar(config)
    return estado['logica']


def aplicar(config):
    """Abre la ventana con la resolucion elegida o en pantalla completa."""
    W, H = estado['logica'].get_size()
    if config.get('pantalla_completa'):
        estado['real'] = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        try: ancho, alto = (int(x) for x in config.get('resolucion', '%dx%d' % (W, H)).split('x'))
        except ValueError: ancho, alto = W, H
        estado['real'] = pygame.display.set_mode((ancho, alto))
    rw, rh = estado['real'].get_size()
    escala = min(rw / W, rh / H)                         # entra entera, sin deformar
    estado['destino'] = pygame.Rect(0, 0, round(W * escala), round(H * escala))
    estado['destino'].center = (rw // 2, rh // 2)


def presentar():
    real, logica, destino = estado['real'], estado['logica'], estado['destino']
    if destino.size == logica.get_size(): real.blit(logica, destino)
    else:
        real.fill((0, 0, 0))
        real.blit(pygame.transform.scale(logica, destino.size), destino)
    pygame.display.flip()


def a_logico(pos):
    """De pixeles de la ventana a pixeles del juego."""
    W, H = estado['logica'].get_size()
    d = estado['destino']
    return (int((pos[0] - d.x) * W / max(1, d.width)), int((pos[1] - d.y) * H / max(1, d.height)))


def raton():
    return a_logico(pygame.mouse.get_pos())
