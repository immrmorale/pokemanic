"""
recortar_assets.py - Para recortar sprites de una hoja (por ejemplo de The Spriters Resource) y dejarlos donde el juego los busca.

    python recortar_assets.py ruta/a/la/hoja.png

    clic izquierdo y arrastrar   marcar el sprite (se recorta solo al borde del dibujo)
    escribir                     nombre del objeto o terreno (TAB completa con la primera sugerencia)
    ENTER                        guardar en assets/mundo/[era/]<objetos|terrenos>/<nombre>.png
    F1                           objetos / terrenos            F2   para todas las eras o solo una
    B y clic                     elegir el color de fondo (se vuelve transparente). Arranca con el de la esquina
    rueda                        zoom          clic derecho y arrastrar   moverse por la hoja
    ESC                          salir

A la derecha se ve la lista de lo que todavia no tiene sprite.
"""

import os
import sys
import pygame
import mundos
import entorno

W, H = 1280, 760
PANEL = 330


def main(ruta):
    pygame.init()
    ventana = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Recortar assets - ' + os.path.basename(ruta))
    hoja = pygame.image.load(ruta).convert_alpha()
    fuente, chica = pygame.font.Font(None, 26), pygame.font.Font(None, 19)
    fondo = hoja.get_at((0, 0))                                 # color de fondo de la hoja
    zoom, vista = 2.0, [0.0, 0.0]
    seleccion, arrastre, paneo, eligiendo_fondo = None, None, None, False
    nombre, tipo, iera, mensaje = '', 'objetos', 0, ''
    eras = [None] + [e['clave'] for e in mundos.ERAS]
    reloj = pygame.time.Clock()

    def a_hoja(pos):
        return int((pos[0] + vista[0]) / zoom), int((pos[1] + vista[1]) / zoom)

    def recorte():
        """La seleccion achicada al borde del dibujo, con el fondo transparente."""
        if not seleccion or seleccion.width < 1 or seleccion.height < 1: return None
        pedazo = hoja.subsurface(seleccion.clip(hoja.get_rect())).copy()
        for x in range(pedazo.get_width()):
            for y in range(pedazo.get_height()):
                if pedazo.get_at((x, y))[:3] == fondo[:3]: pedazo.set_at((x, y), (0, 0, 0, 0))
        borde = pedazo.get_bounding_rect()
        return pedazo.subsurface(borde).copy() if borde.width and borde.height else None

    def nombres_conocidos():
        return sorted(mundos.OBJETOS) if tipo == 'objetos' else sorted(mundos.TERRENOS)

    while True:
        sugerencias = [n for n in nombres_conocidos() if n.startswith(nombre)][:8] if nombre else []
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: pygame.quit(); return
                elif e.key == pygame.K_F1: tipo = 'terrenos' if tipo == 'objetos' else 'objetos'
                elif e.key == pygame.K_F2: iera = (iera + 1) % len(eras)
                elif e.key == pygame.K_TAB and sugerencias: nombre = sugerencias[0]
                elif e.key == pygame.K_BACKSPACE: nombre = nombre[:-1]
                elif e.key == pygame.K_b and not nombre: eligiendo_fondo = True; mensaje = 'clic en el color de fondo'
                elif e.key == pygame.K_RETURN:
                    img = recorte()
                    if img and nombre:
                        carpeta = os.path.join(entorno.CARPETA_ASSETS, *([eras[iera]] if eras[iera] else []), tipo)
                        os.makedirs(carpeta, exist_ok=True)
                        pygame.image.save(img, os.path.join(carpeta, nombre + '.png'))
                        mensaje = 'guardado ' + os.path.join(*([eras[iera]] if eras[iera] else []), tipo, nombre + '.png')
                        entorno._imagenes.clear()
                        nombre = ''
                    else: mensaje = 'falta marcar el sprite o escribir el nombre'
                elif e.unicode and (e.unicode.isalnum() or e.unicode in '_ñ'): nombre += e.unicode.lower()
            if e.type == pygame.MOUSEWHEEL:
                antes = a_hoja(pygame.mouse.get_pos())
                zoom = max(0.5, min(8.0, zoom * (1.25 if e.y > 0 else 0.8)))
                mx, my = pygame.mouse.get_pos()
                vista = [antes[0] * zoom - mx, antes[1] * zoom - my]  # el zoom se centra en el mouse
            if e.type == pygame.MOUSEBUTTONDOWN and e.pos[0] < W - PANEL:
                if e.button == 1 and eligiendo_fondo:
                    x, y = a_hoja(e.pos)
                    if hoja.get_rect().collidepoint(x, y): fondo = hoja.get_at((x, y)); mensaje = 'fondo: ' + str(tuple(fondo)[:3])
                    eligiendo_fondo = False
                elif e.button == 1: arrastre = a_hoja(e.pos)
                elif e.button == 3: paneo = (e.pos, list(vista))
            if e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1 and arrastre:
                    x, y = a_hoja(e.pos)
                    seleccion = pygame.Rect(min(x, arrastre[0]), min(y, arrastre[1]), abs(x - arrastre[0]) + 1, abs(y - arrastre[1]) + 1)
                    arrastre = None
                if e.button == 3: paneo = None
            if e.type == pygame.MOUSEMOTION and paneo:
                vista = [paneo[1][0] - (e.pos[0] - paneo[0][0]), paneo[1][1] - (e.pos[1] - paneo[0][1])]

        ventana.fill((40, 40, 46))
        grande = pygame.transform.scale(hoja, (round(hoja.get_width() * zoom), round(hoja.get_height() * zoom)))
        ventana.blit(grande, (-vista[0], -vista[1]))
        marco = None
        if arrastre:
            x, y = a_hoja(pygame.mouse.get_pos())
            marco = pygame.Rect(min(x, arrastre[0]), min(y, arrastre[1]), abs(x - arrastre[0]) + 1, abs(y - arrastre[1]) + 1)
        elif seleccion: marco = seleccion
        if marco:
            pygame.draw.rect(ventana, (255, 60, 60), (marco.x * zoom - vista[0], marco.y * zoom - vista[1], marco.width * zoom, marco.height * zoom), 2)
        pygame.draw.rect(ventana, (22, 22, 26), (W - PANEL, 0, PANEL, H))       # panel derecho
        x, y = W - PANEL + 12, 12
        textos = [('Destino: ' + tipo + ('  (' + eras[iera] + ')' if eras[iera] else '  (todas las eras)'), fuente),
                  ('Nombre: ' + nombre + '_', fuente), ('F1 tipo  F2 era  TAB completar  ENTER guardar', chica), (mensaje, chica)]
        for t, f in textos:
            ventana.blit(f.render(t, True, (235, 235, 235)), (x, y)); y += f.get_height() + 6
        pygame.draw.rect(ventana, fondo, (x, y, 18, 18)); ventana.blit(chica.render('color de fondo (B para cambiar)', True, (200, 200, 200)), (x + 26, y + 2)); y += 30
        img = recorte()
        if img:                                                 # vista previa del recorte
            escala = min(4, 150 / max(img.get_size()))
            prev = pygame.transform.scale(img, (max(1, round(img.get_width() * escala)), max(1, round(img.get_height() * escala))))
            pygame.draw.rect(ventana, (70, 70, 80), (x, y, 160, 160)); ventana.blit(prev, prev.get_rect(center=(x + 80, y + 80)))
            ventana.blit(chica.render(str(img.get_width()) + 'x' + str(img.get_height()) + ' px', True, (200, 200, 200)), (x + 170, y + 70))
        y += 170
        for s in sugerencias: ventana.blit(chica.render('> ' + s, True, (250, 220, 120)), (x, y)); y += 18
        if not sugerencias:                                     # lo que todavia no tiene sprite
            faltan = [n for n in nombres_conocidos() if not entorno.imagen(tipo, n, eras[iera])]
            ventana.blit(chica.render('Sin sprite (' + str(len(faltan)) + '):', True, (200, 200, 200)), (x, y)); y += 20
            for n in faltan[:(H - y) // 17]: ventana.blit(chica.render(n, True, (160, 160, 160)), (x, y)); y += 17
        pygame.display.flip(); reloj.tick(60)


if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit()
    main(sys.argv[1])
