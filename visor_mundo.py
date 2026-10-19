"""
visor_mundo.py - Para mirar salas generadas sin jugar.

    python visor_mundo.py

Teclas:
    <- / ->     cambiar de era               arriba / abajo   cambiar de variante
    T           combate / tienda / arena     ESPACIO          otra semilla (otra sala)
    C           probar los climas            P                ver el plan de una partida
    S           guardar captura (visor_XXXX.png)   ESC        salir
"""

import random
import pygame
import mundos
import generacion
import entorno

W, H = 1180, 720
PANEL = 300                                  # ancho del panel de texto de la derecha
TIPOS = ('combate', 'tienda', 'arena')
CLIMAS = [None] + list(entorno.CLIMAS)


def generar(era, variante, tipo, semilla):
    """Sala y su entorno segun lo elegido en el visor."""
    if tipo == 'tienda': sala = generacion.generar_tienda(era, ['oeste', 'este'], semilla)
    elif tipo == 'arena': sala = generacion.generar_arena(era, ['norte'], semilla)
    else:
        azar = random.Random(semilla)
        entrada = azar.choice(generacion.LADOS)
        salidas = azar.sample([l for l in generacion.LADOS if l != entrada], azar.randint(1, 3))
        sala = generacion.generar_sala(era, variante, entrada, salidas, semilla)
    return sala, entorno.crear(sala)


def main():
    pygame.init()
    ventana = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Pokemanic - visor de mundos')
    fuente, chica = pygame.font.Font(None, 26), pygame.font.Font(None, 20)
    era, ivar, itipo, iclima, semilla = 0, 0, 0, 0, random.randrange(10 ** 6)
    ver_plan = False
    rec = mundos.nuevo_recorrido()
    sala, ent = None, None
    reloj = pygame.time.Clock()
    while True:
        variantes = list(mundos.ERAS[era]['variantes'])
        ivar %= len(variantes)
        if sala is None:
            sala, ent = generar(era, variantes[ivar], TIPOS[itipo], semilla)
            if CLIMAS[iclima]: entorno.iniciar_clima(ent, CLIMAS[iclima], 0, None)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): pygame.quit(); return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RIGHT: era = (era + 1) % len(mundos.ERAS); ivar = 0
                elif e.key == pygame.K_LEFT: era = (era - 1) % len(mundos.ERAS); ivar = 0
                elif e.key == pygame.K_DOWN: ivar += 1
                elif e.key == pygame.K_UP: ivar -= 1
                elif e.key == pygame.K_t: itipo = (itipo + 1) % len(TIPOS)
                elif e.key == pygame.K_SPACE: semilla = random.randrange(10 ** 6)
                elif e.key == pygame.K_c: iclima = (iclima + 1) % len(CLIMAS)
                elif e.key == pygame.K_p: ver_plan = not ver_plan; rec = mundos.nuevo_recorrido()
                elif e.key == pygame.K_s:
                    nombre = 'visor_' + str(semilla) + '.png'
                    pygame.image.save(ventana, nombre); print('guardado', nombre)
                    continue
                else: continue
                sala = None                                     # cambio algo: se regenera
        if sala is None: continue
        ventana.fill((15, 15, 18))
        lienzo = pygame.Surface(sala['esc'].size)              # la sala entera a tamaño real y despues se achica
        ahora = pygame.time.get_ticks()
        entorno.dibujar(ent, lienzo, 0, 0, ahora)
        for puerta in sala['puertas']: pygame.draw.rect(lienzo, (60, 180, 80), puerta['rect'])
        pygame.draw.circle(lienzo, (255, 60, 255), [round(v) for v in sala['inicio']], 18)      # donde aparece el jugador
        entorno.dibujar_clima(ent, lienzo, ahora)
        escala = min((W - PANEL - 20) / lienzo.get_width(), (H - 20) / lienzo.get_height())
        chico = pygame.transform.smoothscale(lienzo, (round(lienzo.get_width() * escala), round(lienzo.get_height() * escala)))
        ventana.blit(chico, (10, 10))
        x = W - PANEL + 10                                      # panel con los datos de la sala
        lineas = [(mundos.ERAS[era]['nombre'], fuente, mundos.ERAS[era]['suelo']), ('Regi: ' + mundos.ERAS[era]['regi'], chica, None),
                  ('Variante: ' + (variantes[ivar] if TIPOS[itipo] == 'combate' else TIPOS[itipo]), chica, None),
                  ('Forma: ' + sala.get('forma', '-') + '   simetria: ' + sala.get('simetria', '-'), chica, None),
                  ('Interior' if sala.get('interior') else 'Exterior', chica, None),
                  ('Clima: ' + (CLIMAS[iclima] or 'ninguno (C para probar)'), chica, None),
                  ('Objetos: ' + str(len(sala['objetos'])) + '   semilla ' + str(semilla), chica, None),
                  ('Piezas: ' + (', '.join(sala.get('piezas', [])) or '-'), chica, None), ('', chica, None)]
        lineas += [(t, chica, (170, 170, 170)) for t in ('<- -> era    arriba/abajo variante', 'T tipo de sala   ESPACIO otra', 'C clima   P plan   S captura')]
        y = 14
        for texto, f, color in lineas:
            for parte in [texto[i:i + 40] for i in range(0, max(1, len(texto)), 40)]:
                ventana.blit(f.render(parte, True, color or (235, 235, 235)), (x, y)); y += f.get_height() + 4
        if ver_plan:                                            # plan de una partida: T tienda, J semijefe, R regi, A arceus
            y += 10
            letras = {'combate': '.', 'tienda': 'T', 'jefe': 'J', 'regi': 'R', 'final': 'A'}
            for i, plan in enumerate(rec['plan']):
                ventana.blit(chica.render(mundos.ERAS[i]['clave'][:8].ljust(9) + ''.join(letras[t] for t in plan), True, (220, 220, 140)), (x, y)); y += 18
        pygame.display.flip(); reloj.tick(30)


if __name__ == '__main__':
    main()
