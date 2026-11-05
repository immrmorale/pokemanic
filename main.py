import pygame
import os
import random
import math
import sys
import time
from types import SimpleNamespace
import datos
import mecanicas
from datos import mundos, mts, tienda
from sistema import controles, pantalla, opciones, partidas, tipografia, animaciones
from mundo import generacion, entorno, efectos
from combate import ia, progreso
from interfaz import menus

_pk = datos.pokemones
pokemones, movimientos, JUGABLES, ROL_POKEMON, datos_juego = _pk.pokemones, _pk.movimientos, _pk.JUGABLES, _pk.ROL_POKEMON, _pk.datos_juego
asistencia_de, buscar_movimiento, multiplicador_tipos, normalizar_tipo, sinergia_de = _pk.asistencia_de, _pk.buscar_movimiento, _pk.multiplicador_tipos, _pk.normalizar_tipo, _pk.sinergia_de
evoluciones_de, descripcion_de, stats_oficiales, aprende_de, debilidades_de = _pk.evoluciones_de, _pk.descripcion_de, _pk.stats_oficiales, _pk.aprende_de, _pk.debilidades_de
direcciones, direccion_vector, AnimadorPokemon, cargar_retrato, tiene_sprites = animaciones.direcciones, animaciones.direccion_vector, animaciones.AnimadorPokemon, animaciones.cargar_retrato, animaciones.tiene_sprites
ajustar_texto, dibujar_esquinas = menus.ajustar_texto, menus.dibujar_esquinas


COLORES_TIPO = {'lucha': (220, 70, 70), 'hielo': (130, 220, 255), 'volador': (235, 235, 235), 'tierra': (170, 115, 65), 'electrico': (245, 220, 40), 'agua': (70, 130, 235),
               'fuego': (240, 128, 48), 'planta': (120, 200, 80), 'veneno': (160, 64, 160), 'psiquico': (249, 85, 135), 'bicho': (166, 185, 26), 'roca': (182, 161, 54),
               'fantasma': (115, 87, 151), 'dragon': (111, 53, 252), 'siniestro': (112, 87, 70), 'acero': (183, 183, 206), 'normal': (168, 167, 122), 'hada': (214, 133, 173)}

def main():
    """Arranca pygame y la ventana, y maneja el ciclo intro -> titulo -> menu principal -> partida.
    Todo lo demas (menus, pokedex, la partida) son funciones armadas adentro, que comparten la ventana y la configuracion."""
    pygame.init()
    W, H = 1000, 600
    config = opciones.cargar()                       # ajustes guardados en config.json
    controles.iniciar(config)
    ventana = pantalla.iniciar(W, H, config)        # todo se dibuja en 1000x600 y se escala a la ventana
    pygame.display.set_caption('Pokemanic')
    fuente = tipografia.fuente(24)

    retratos_menu = {}

    def armar_ayudas_menu():
        """Ayudas de los menus: retratos de las caras, volumen y la caja de confirmar."""
        def retrato_menu(nombre, lado):
            """Retrato del pokemon al tamaño pedido (guardado para no escalarlo de nuevo). None si no tiene."""
            clave = (nombre, lado)
            if clave not in retratos_menu:
                img = cargar_retrato(nombre)
                retratos_menu[clave] = pygame.transform.smoothscale(img, (lado, lado)) if img else None
            return retratos_menu[clave]

        def aplicar_volumen():
            """Pone el volumen de la musica segun los ajustes."""
            try: pygame.mixer.music.set_volume(config['volumen'] / 100)
            except pygame.error: pass

        def confirmar(mensaje):
            """Caja de 'si / no' sobre la pantalla actual. True si se confirmo (ENTER / Y)."""
            pygame.mouse.set_visible(True)
            fondo = ventana.copy()
            reloj_c = pygame.time.Clock()
            f = tipografia.fuente(32)
            while True:
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return True
                    if e.type == pygame.KEYDOWN:
                        if e.key in (pygame.K_ESCAPE, pygame.K_n):
                            return False
                        if e.key in (pygame.K_RETURN, pygame.K_y):
                            return True
                ventana.blit(fondo, (0, 0))
                velo = pygame.Surface((W, H), pygame.SRCALPHA)
                velo.fill((0, 0, 0, 150))
                ventana.blit(velo, (0, 0))
                r = pygame.Rect(250, 205, 500, 190)
                pygame.draw.rect(ventana, (35, 35, 35), r)
                pygame.draw.rect(ventana, (220, 220, 220), r, 2)
                ventana.blit(f.render(mensaje, True, 'white'), (315, 245))
                ventana.blit(f.render('ENTER / Y: Sí    ESC / N: No', True, (210, 210, 210)), (315, 300))
                pantalla.presentar(); reloj_c.tick(60)

        return retrato_menu, aplicar_volumen, confirmar

    retrato_menu, aplicar_volumen, confirmar = armar_ayudas_menu()

    def armar_menu_debug():
        """Menu debug (F1): armar el equipo con cualquier pokemon y elegir en que espacio va."""
        def elegir_espacio(nombre, equipo, activo):
            """Menu debug: en que espacio del equipo (1, 2 o 3) va el pokemon elegido. Devuelve el indice, None o 'salir'."""
            f_titulo, f_texto = tipografia.fuente(36), tipografia.fuente(26)
            cajas = [pygame.Rect(W // 2 - 345 + i * 235, 210, 220, 170) for i in range(3)]
            while True:
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir'
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            return None
                        if e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                            return e.key - pygame.K_1
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for i, r in enumerate(cajas):
                            if r.collidepoint(pantalla.a_logico(e.pos)):
                                return i
                ventana.fill((20, 20, 20))
                titulo = f_titulo.render('En que espacio queres a ' + nombre.replace('_', ' ').title() + '?', True, 'white')
                ventana.blit(titulo, titulo.get_rect(center=(W // 2, 140)))
                ayuda = f_texto.render('Clic o teclas 1 / 2 / 3 - ESC para cancelar', True, (200, 200, 200))
                ventana.blit(ayuda, ayuda.get_rect(center=(W // 2, 175)))
                raton = pantalla.raton()
                for i, r in enumerate(cajas):
                    pygame.draw.rect(ventana, (60, 60, 60) if r.collidepoint(raton) else (40, 40, 40), r)
                    pygame.draw.rect(ventana, (80, 160, 80) if i == activo else (200, 200, 200), r, 3)
                    ventana.blit(f_titulo.render('Espacio ' + str(i + 1), True, 'white'), (r.x + 12, r.y + 10))
                    ocupante = equipo[i] if i < len(equipo) else None
                    if ocupante:
                        img = retrato_menu(ocupante, 56)
                        if img: ventana.blit(img, (r.x + 12, r.y + 60))
                        ventana.blit(f_texto.render(ocupante.replace('_', ' ').title(), True, 'white'), (r.x + 76, r.y + 80))
                    if i == activo:
                        ventana.blit(f_texto.render('(activo)', True, (120, 220, 120)), (r.x + 12, r.bottom - 32))
                pantalla.presentar()

        TIPOS_ORDEN = list(_pk.TABLA_TIPOS)                 # el orden de la tabla de tipos: normal, fuego, agua, electrico, planta...
        GENERACIONES = (151, 251, 386, 493, 649, 721, 809, 905, 1025)   # ultimo numero de la pokedex de cada generacion

        def generacion_de(nombre):
            """Generacion del pokemon segun su numero de la pokedex (las formas regionales cuentan con el de la especie)."""
            dex = pokemones[nombre].get('pokedex')
            if not isinstance(dex, int): return 99
            return next((i + 1 for i, tope in enumerate(GENERACIONES) if dex <= tope), 99)

        def hijos_de(nombre):
            """A quienes evoluciona (aunque todavia no tengan sprites): PokeAPI, Eevee, formas regionales y paradojas."""
            if nombre in progreso.EVOLUCION_PROPIA: destinos = [r['a'] for r in progreso.EVOLUCION_PROPIA[nombre]]
            else:
                destinos = [ev['a'].replace('-', '_') for ev in (_pk._oficiales.get(nombre) or {}).get('evoluciones') or []]
                destinos = [d for d in destinos if (nombre, d) != ('zorua_hisui', 'zoroark')]   # el de Hisui va con el Zoroark de Hisui
            destinos += [r['a'] for r in progreso.EVOLUCION_EXTRA.get(nombre, [])]
            return [d for d in dict.fromkeys(destinos) if d in pokemones and d != nombre]

        def ordenar_debug(nombres):
            """Lista del menu F1 agrupada: por tipo (el principal de la primera forma de la linea, en el orden de la tabla de tipos),
            adentro de cada tipo por generacion y cada linea evolutiva junta (Pichu, Pikachu y Raichu van seguidos aunque Pichu sea de
            la 2da generacion). Devuelve [(tipo, [nombres])] solo con los tipos que tienen alguno."""
            padre = {}
            for n in pokemones:
                for h in hijos_de(n): padre.setdefault(h, n)
            def raiz(n):
                vistos = set()
                while n in padre and n not in vistos: vistos.add(n); n = padre[n]
                return n
            def linea(r):
                salida = [r]
                for h in sorted(hijos_de(r), key=lambda x: (generacion_de(x), pokemones[x].get('pokedex') if isinstance(pokemones[x].get('pokedex'), int) else 9999)):
                    if padre.get(h) == r: salida += linea(h)
                return salida
            lineas = {}
            for n in nombres: lineas.setdefault(raiz(n), []).append(n)
            grupos = {}
            for r, miembros in lineas.items():
                orden = linea(r)
                miembros.sort(key=lambda x: orden.index(x) if x in orden else len(orden))
                tipo = normalizar_tipo((pokemones[r].get('tipo') or ['normal'])[0])
                gen = min(generacion_de(m) for m in orden if m in pokemones)
                dex = min((pokemones[m]['pokedex'] for m in orden if isinstance(pokemones[m].get('pokedex'), int)), default=9999)
                grupos.setdefault(tipo, []).append(((gen, dex, r), miembros))
            return [(t, [n for _, ms in sorted(grupos[t]) for n in ms]) for t in TIPOS_ORDEN + sorted(set(grupos) - set(TIPOS_ORDEN)) if t in grupos]

        def debug_menu(equipo, activo):
            """Menu debug (F1): grilla con todos los pokemon jugables (con el Konami tambien los jefes), ordenados por tipo,
            generacion y linea evolutiva (ver ordenar_debug). Cada tipo arranca en una fila nueva con su titulo.
            Devuelve (resultado, nombre elegido, espacio)."""
            pygame.mouse.set_visible(True)
            lista = list(JUGABLES)                           # con el codigo Konami adentro de este menu se suman los jefes
            grupos = ordenar_debug(lista)
            scroll = 0
            botones = []
            f_titulo = tipografia.fuente(32)
            while True:
                columnas, bw, bh, bn, sy, alto_titulo = 4, 210, 62, 28, 18, 34
                filas = sum(math.ceil(len(ns) / columnas) for _, ns in grupos)
                max_scroll = max(0, 80 + filas * (bh + bn + sy) + len(grupos) * alto_titulo - H)

                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir', None, None
                    if e.type == controles.KONAMI:
                        lista = list(JUGABLES) + [n for n, d in pokemones.items() if d.get('boss') and tiene_sprites(n) and n not in JUGABLES]
                        grupos = ordenar_debug(lista)
                    if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_F1):
                        return 'ok', None, None
                    if e.type == pygame.MOUSEWHEEL:
                        scroll = max(0, min(scroll - e.y * 60, max_scroll))
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for r, nombre in botones:
                            if r.collidepoint(pantalla.a_logico(e.pos)):
                                espacio = elegir_espacio(nombre, equipo, activo)
                                if espacio == 'salir':
                                    return 'salir', None, None
                                if espacio is not None:
                                    return 'ok', nombre, espacio
                                break

                ventana.fill((20, 20, 20))
                botones = []
                posiciones, y_grupo = [], 85 - scroll
                for tipo, nombres_t in grupos:                   # titulo del tipo y sus pokemon (cada tipo arranca en una fila nueva)
                    if 64 <= y_grupo < H:
                        color_t = COLORES_TIPO.get(tipo, (200, 200, 200))
                        pygame.draw.rect(ventana, color_t, (30, y_grupo + 6, 6, alto_titulo - 14))
                        ventana.blit(f_titulo.render(tipo.title() + '  (' + str(len(nombres_t)) + ')', True, color_t), (44, y_grupo + 2))
                    y_grupo += alto_titulo
                    for k_, nombre in enumerate(nombres_t):
                        posiciones.append((nombre, 30 + k_ % columnas * 240, y_grupo + k_ // columnas * (bh + bn + sy)))
                    y_grupo += math.ceil(len(nombres_t) / columnas) * (bh + bn + sy)
                for nombre, x, y in posiciones:
                    r = pygame.Rect(x, y, bw, bh)
                    nr = pygame.Rect(x, y + bh, bw, bn)
                    if nr.bottom < 64 or nr.top > H:
                        continue
                    en_equipo = nombre in equipo
                    pygame.draw.rect(ventana, (80, 160, 80) if en_equipo else (200, 200, 200), r)
                    pygame.draw.rect(ventana, (50, 50, 50), nr)
                    img = retrato_menu(nombre, bh - 12)
                    if img: ventana.blit(img, (x + 6, y + 6))
                    ventana.blit(fuente.render(nombre.replace('_', ' ').title(), True, 'black'), (x + bh, y + 22))
                    detalle = ROL_POKEMON.get(nombre, '') or ('JEFE' if pokemones[nombre].get('boss') else '')
                    if en_equipo: detalle += ' - espacio ' + str(equipo.index(nombre) + 1)
                    ventana.blit(fuente.render(detalle, True, 'white'), (x + 8, y + bh + 5))
                    if r.top >= 64: botones.append((r, nombre))     # las que pasan por debajo del titulo no se pueden tocar
                pygame.draw.rect(ventana, (20, 20, 20), (0, 0, W, 64))      # el titulo queda fijo arriba: lo que se desplaza pasa por debajo
                ventana.blit(f_titulo.render('MENU DEBUG', True, 'white'), (25, 15))
                ventana.blit(fuente.render('F1 o ESC para cerrar - rueda del mouse para desplazarte - clic para elegir espacio', True, (200, 200, 200)), (25, 45))
                pantalla.presentar()

        def asignar_equipo(lista, nombre, espacio):
            """Pone el pokemon en ese espacio del equipo del menu (si ya estaba en otro, los intercambia)."""
            while len(lista) <= espacio: lista.append(None)            # el equipo del menu arranca vacio
            if nombre in lista:
                i = lista.index(nombre)
                lista[i], lista[espacio] = lista[espacio], lista[i]
            else:
                lista[espacio] = nombre

        return debug_menu, asignar_equipo

    debug_menu, asignar_equipo = armar_menu_debug()

    def armar_pantallas():
        """Pantalla de titulo, menu principal y menu de pausa."""
        def pantalla_titulo():
            """Pantalla de titulo sobre la isla: cualquier tecla sigue al menu, ESC pregunta si salir."""
            pygame.mouse.set_visible(True)
            f_grande, f_med, f_peq = tipografia.fuente(96), tipografia.fuente(30), tipografia.fuente(18)
            reloj_t = pygame.time.Clock()
            inicio_t = pygame.time.get_ticks()
            while True:
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir'
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            if confirmar('¿Seguro que quieres salir?'): return 'salir'
                        else:
                            return 'menu'
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        return 'menu'
                ahora = pygame.time.get_ticks()
                menus.fondo_menu(ui, ahora)
                k = menus.aparecer(ahora - inicio_t, 0, 600)              # el logo cae desde arriba al abrir
                menus.dibujar_logo(ventana, 96, ahora, center=(W // 2, round(130 - (1 - k) * 220)))
                if (ahora // 450) % 2 == 0 or ahora - inicio_t < 600:     # el cartel titila, como en los juegos
                    p = f_med.render('Presioná cualquier tecla', True, 'white')
                    franja = p.get_rect(center=(W // 2, H - 80)).inflate(80, 24)
                    pygame.draw.polygon(ventana, (14, 14, 26), [(franja.x + 20, franja.y), (franja.right, franja.y), (franja.right - 20, franja.bottom), (franja.x, franja.bottom)])
                    pygame.draw.line(ventana, (70, 200, 255), (franja.x + 20, franja.y), (franja.right, franja.y), 3)
                    ventana.blit(p, p.get_rect(center=franja.center))
                s = tipografia.fuente(20, borde=True).render('ESC: salir', True, 'white')
                ventana.blit(s, s.get_rect(bottomright=(W - 20, H - 14)))
                pantalla.presentar(); reloj_t.tick(60)

        def menu_principal(equipo):
            """Menu principal: jugar, pokedex, ajustes, glosario y salir. Devuelve la opcion elegida."""
            pygame.mouse.set_visible(True)
            orden = ['jugar', 'pokedex', 'ataques', 'ajustes', 'glosario', 'salir']
            botones = {o: pygame.Rect(80, 150 + i * 74, 320, 60) for i, o in enumerate(orden[:5])}
            botones['salir'] = pygame.Rect(0, 0, 84, 84)
            botones['salir'].center = (W - 100, H - 80)
            f_titulo, f_boton, f_info = tipografia.fuente(64), tipografia.fuente(44), tipografia.fuente(24)
            seleccion = 0
            reloj_m = pygame.time.Clock()
            abierto = pygame.time.get_ticks()
            TEXTO_MENU = {'jugar': 'Jugar', 'pokedex': 'Pokédex', 'ataques': 'Ataques', 'ajustes': 'Ajustes', 'glosario': 'Glosario'}
            while True:
                elegido = None
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'cerrar'
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            return 'titulo'
                        if e.key == pygame.K_F1:                    # menu debug de pokemon (no se avisa en ningun lado)
                            resultado_debug, nombre, espacio = debug_menu(equipo, 0)
                            if resultado_debug == 'salir': return 'cerrar'
                            if nombre: asignar_equipo(equipo, nombre, espacio)
                        if e.key in (pygame.K_w, pygame.K_UP): seleccion = (seleccion - 1) % len(orden)
                        if e.key in (pygame.K_s, pygame.K_DOWN): seleccion = (seleccion + 1) % len(orden)
                        if e.key in (pygame.K_RETURN, pygame.K_e): elegido = orden[seleccion]
                    if e.type == pygame.MOUSEMOTION:
                        for i, o in enumerate(orden):
                            if botones[o].collidepoint(pantalla.a_logico(e.pos)): seleccion = i
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for o in orden:
                            if botones[o].collidepoint(pantalla.a_logico(e.pos)): elegido = o
                if elegido: return elegido
                ahora = pygame.time.get_ticks()
                menus.fondo_menu(ui, ahora)
                menus.dibujar_logo(ventana, 64, ahora, topright=(W - 40, 40 - round((1 - menus.aparecer(ahora - abierto, 0, 400)) * 160)))
                for i, o in enumerate(orden[:5]):                     # paneles en flecha de BW que entran escalonados desde la izquierda
                    menus.boton(ventana, botones[o], TEXTO_MENU[o], seleccion == i, 44, aparicion=menus.aparecer(ahora - abierto, i * 70))
                cx, cy = botones['salir'].center
                pygame.draw.circle(ventana, 'white', (cx, cy), 40, 3)
                pygame.draw.line(ventana, 'white', (cx + 16, cy), (cx - 12, cy), 4)
                pygame.draw.line(ventana, 'white', (cx - 12, cy), (cx - 2, cy - 10), 4)
                pygame.draw.line(ventana, 'white', (cx - 12, cy), (cx - 2, cy + 10), 4)
                pygame.draw.line(ventana, 'white', (cx - 21, cy - 14), (cx - 21, cy + 14), 4)
                if seleccion == 5: dibujar_esquinas(ventana, botones['salir'].inflate(6, 6))
                ventana.blit(tipografia.fuente(24, borde=True).render('Combate: ' + config['modo'] + ('   (control conectado)' if controles.hay_control() else ''), True, 'white'), (20, H - 34))
                pantalla.presentar(); reloj_m.tick(60)

        def menu_pausa(fondo):
            """Menu de pausa sobre la partida congelada ('fondo'). Devuelve 'seguir', 'menu' o 'cerrar'."""
            pygame.mouse.set_visible(True)
            tinte = pygame.Surface((W, H), pygame.SRCALPHA)
            tinte.fill((10, 10, 25, 120))
            opciones = [('seguir', 'Seguir jugando'), ('ajustes', 'Ajustes'), ('pokedex', 'Pokédex'), ('ataques', 'Ataques'), ('glosario', 'Glosario'),
                        ('salir', 'Salir al menú')]
            botones = [pygame.Rect(60, 150 + i * 68, 340, 56) for i in range(len(opciones))]
            abierto = pygame.time.get_ticks()
            f_titulo, f_boton = tipografia.fuente(80), tipografia.fuente(38)
            seleccion = 0
            reloj_p = pygame.time.Clock()
            while True:
                accion = None
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'cerrar'
                    if e.type == controles.KONAMI and menus.trucos(ui) == 'salir': return 'cerrar'
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE: return 'seguir'
                        if e.key in (pygame.K_w, pygame.K_UP): seleccion = (seleccion - 1) % len(opciones)
                        if e.key in (pygame.K_s, pygame.K_DOWN): seleccion = (seleccion + 1) % len(opciones)
                        if e.key in (pygame.K_RETURN, pygame.K_e): accion = opciones[seleccion][0]
                    if e.type == pygame.MOUSEMOTION:
                        for i, r in enumerate(botones):
                            if r.collidepoint(pantalla.a_logico(e.pos)): seleccion = i
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for i, r in enumerate(botones):
                            if r.collidepoint(pantalla.a_logico(e.pos)): accion = opciones[i][0]
                if accion == 'seguir': return 'seguir'
                if accion == 'ajustes' and menus.ajustes(ui) == 'salir': return 'cerrar'
                if accion == 'glosario' and menus.glosario(ui) == 'salir': return 'cerrar'
                if accion == 'ataques' and menus.ataques(ui) == 'salir': return 'cerrar'
                if accion == 'pokedex':
                    if pokedex() == 'salir': return 'cerrar'
                if accion == 'salir' and confirmar('¿Volver al menú principal?'): return 'menu'
                ahora = pygame.time.get_ticks(); t = ahora - abierto
                ventana.blit(fondo, (0, 0))
                ventana.blit(tinte, (0, 0))
                menus.pokeball_girando(ventana, (W - 190, H // 2 + 40), 460, ahora, 90)   # la Pokeball de BW girando detras
                lado = menus.aparecer(t, 0, 220)                                         # la franja oscura entra desde la izquierda
                franja = [(0, 0), (round(560 * lado), 0), (round(440 * lado), H), (0, H)]
                capa = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.polygon(capa, (14, 14, 26, 220), franja)
                pygame.draw.line(capa, (70, 200, 255), franja[1], franja[2], 6)
                ventana.blit(capa, (0, 0))
                titulo_t = tipografia.fuente_titulo(4).render('Pausa', True, 'white')
                ventana.blit(titulo_t, (round(52 - (1 - lado) * 300), 22))   # arriba de los botones, sin taparse
                for i, r in enumerate(botones):
                    menus.boton(ventana, r, opciones[i][1], i == seleccion, 38, aparicion=menus.aparecer(t, 80 + i * 55))
                pantalla.presentar(); reloj_p.tick(60)

        return pantalla_titulo, menu_principal, menu_pausa

    pantalla_titulo, menu_principal, menu_pausa = armar_pantallas()

    def armar_pokedex():
        """La pokedex y la ficha de cada pokemon."""
        def descripcion_movimiento(datos_mov):
            """Texto corto de un movimiento para la ficha (el mismo que usan la tienda y el menu de equipo)."""
            return datos.describir_movimiento(datos_mov)

        def descripcion_asistencia(a):
            """Texto de lo que hace una asistencia (lo que el pokemon de la banca hace con F / G)."""
            return datos.describir_asistencia(a)

        def construir_ficha(nombre, ancho, fuente_txt):
            """Filas de la ficha de un pokemon (titulos, parrafos y espacios) ya cortadas al ancho del panel."""
            d = pokemones[nombre]
            filas = []
            def titulo(t): filas.append(('t', t))
            def texto(t):
                """Agrega un parrafo, cortado en lineas que entren en el panel."""
                for linea in ajustar_texto(t, fuente_txt, ancho): filas.append(('p', linea))
            def vacio(): filas.append(('e', ''))
            titulo('Descripción')
            texto(descripcion_de(nombre) or 'Sin descripción. Ejecutá generar_datos.py para bajar los textos de la pokédex.')
            vacio()
            unico = mecanicas.texto_de(nombre)
            if unico:
                titulo('Lo que lo hace único')
                texto(unico)
                vacio()
            if nombre in mecanicas.ENEMIGO:
                titulo('Como enemigo')
                texto(mecanicas.ENEMIGO_TXT[mecanicas.ENEMIGO[nombre]])
                vacio()
            titulo('Evolución')
            de, a = evoluciones_de(nombre)
            texto('Evoluciona de: ' + (de.capitalize() if de else 'nadie'))
            texto('Evoluciona a: ' + (', '.join(x.capitalize() for x in a) if a else 'no evoluciona'))
            vacio()
            titulo('Débil a')
            deb = debilidades_de(nombre)
            if not d.get('tipo'): texto('Sin tipo')
            if deb['x4']: texto('Muy débil (x4): ' + ', '.join(deb['x4']))
            if deb['x2']: texto('Débil (x2): ' + ', '.join(deb['x2']))
            if deb['x05'] or deb['x025']: texto('Resiste: ' + ', '.join(deb['x05'] + deb['x025']))
            if deb['x0']: texto('Inmune: ' + ', '.join(deb['x0']))
            vacio()
            try: g = datos_juego(nombre)
            except Exception: g = None
            if g:
                titulo('Ataques básicos')
                for i, n in enumerate(g['basicos']):
                    if n: texto(['E / clic izq.: ', 'Q / clic der.: '][i] + n.replace('_', ' ').title() + ' - ' + descripcion_movimiento(buscar_movimiento(n)))
                vacio()
                titulo('Habilidades especiales')
                for i, (n, dat) in enumerate(g['especiales']): texto(['Shift: ', 'R: '][i] + datos.nombre_ataque(n) + ' - ' + descripcion_movimiento(dat))
                vacio()
                titulo('Sinergia')
                etiquetas = {'daño': 'daño', 'defensa': 'menos daño recibido', 'velocidad': 'velocidad', 'enfriamiento': 'menos espera en ataques'}
                for clave, valor in g['sinergia'].items(): texto('Pasiva en la banca: +' + str(round(valor * 100, 1)) + '% de ' + etiquetas.get(clave, clave) + ' al activo')
                try:
                    a = asistencia_de(nombre)
                    texto('Asistencia (F / G desde la banca): ' + a['nombre'].replace('_', ' ').title() + ' - ' + descripcion_asistencia(a) + '. Espera ' + str(a['enfriamiento'] // 1000) + ' s')
                except Exception: pass
                vacio()
            titulo('Ataques en el juego')
            for n in d.get('ataques', []): texto(n.replace('_', ' ').title() + ' - ' + descripcion_movimiento(movimientos.get(n)))
            vacio()
            titulo('Ataques que aprende (PokéAPI)')
            aprende = aprende_de(nombre)
            texto(', '.join(aprende) if aprende else 'Sin datos. Ejecutá generar_datos.py para bajar la lista de movimientos.')
            return filas

        def ver_ficha(entradas, indice):
            """Ficha de un pokemon con su animacion, tipos y stats. Flechas cambian de pokemon, la rueda desplaza el texto."""
            f_nombre, f_sec, f_txt = tipografia.fuente(42), tipografia.fuente(28), tipografia.fuente(22)
            reloj_f = pygame.time.Clock()
            panel = pygame.Rect(335, 60, 645, 525)
            ancho_texto = panel.width - 30
            altos = {'t': 32, 'p': 21, 'e': 10}
            estado = {'indice': -1}
            def cargar(i):
                """Prepara la ficha del pokemon i de la lista (animacion, texto y desplazamiento en cero)."""
                nombre = entradas[i]
                animador = AnimadorPokemon(nombre, pygame.Rect(0, 0, 10, 10), 140)
                animador.rect.center = (170, 160)
                animador.cambiar('idle', 0, True)
                filas = construir_ficha(nombre, ancho_texto, f_txt)
                total = sum(altos[k] for k, _ in filas)
                estado.update({'indice': i, 'nombre': nombre, 'animador': animador, 'filas': filas, 'total': total, 'scroll': 0})
            cargar(indice)
            while True:
                maximo = max(0, estado['total'] - (panel.height - 20))
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir'
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE: return None
                        if e.key in (pygame.K_LEFT, pygame.K_a): cargar((estado['indice'] - 1) % len(entradas))
                        if e.key in (pygame.K_RIGHT, pygame.K_d): cargar((estado['indice'] + 1) % len(entradas))
                        if e.key in (pygame.K_UP, pygame.K_w): estado['scroll'] = max(0, estado['scroll'] - 40)
                        if e.key in (pygame.K_DOWN, pygame.K_s): estado['scroll'] = min(maximo, estado['scroll'] + 40)
                    if e.type == pygame.MOUSEWHEEL:
                        estado['scroll'] = max(0, min(estado['scroll'] - e.y * 40, maximo))
                nombre, animador = estado['nombre'], estado['animador']
                d = pokemones[nombre]
                ventana.fill((20, 20, 20))
                ventana.blit(f_sec.render('POKEDEX', True, 'white'), (20, 18))
                ventana.blit(fuente.render('← → cambiar Pokémon - rueda del mouse: desplazar - ESC: volver a la lista', True, (200, 200, 200)), (160, 24))
                pygame.draw.rect(ventana, (32, 32, 32), (20, 60, 300, 525))
                pygame.draw.rect(ventana, (32, 32, 32), panel)
                tipos = [normalizar_tipo(t) for t in d.get('tipo', [])]
                animador.actualizar()
                if not animador.dibujar(ventana):
                    pygame.draw.rect(ventana, COLORES_TIPO.get(tipos[0] if tipos else '', (120, 120, 120)), (110, 100, 120, 120))
                    ini = f_nombre.render(nombre[:2].title(), True, 'black')
                    ventana.blit(ini, ini.get_rect(center=(170, 160)))
                n = f_nombre.render(nombre.replace('_', ' ').title(), True, 'white')
                ventana.blit(n, n.get_rect(center=(170, 245)))
                x = 40
                for t in tipos:
                    chip = f_txt.render(t, True, 'black')
                    r = pygame.Rect(x, 268, chip.get_width() + 16, 24)
                    pygame.draw.rect(ventana, COLORES_TIPO.get(t, (150, 150, 150)), r, border_radius=8)
                    ventana.blit(chip, (x + 8, 272))
                    x += r.width + 8
                numero = d.get('pokedex')
                clase = ROL_POKEMON.get(nombre) or ('jefe' if d.get('boss') else 'especial')
                ventana.blit(f_txt.render(('#' + str(numero) + ' - ' if numero else '') + 'clase: ' + clase, True, (220, 220, 220)), (40, 300))
                ventana.blit(f_sec.render('Stats en el juego', True, (240, 200, 80)), (40, 330))
                try:
                    g = datos_juego(nombre)
                    ventana.blit(f_txt.render('Vida ' + str(g['max_vida']) + '   Velocidad ' + str(g['velocidad']), True, 'white'), (40, 355))
                    ventana.blit(f_txt.render('Daño x' + str(g['mult_daño']) + '   Recarga x' + str(g['mult_enfriamiento']), True, 'white'), (40, 376))
                except Exception: pass
                ventana.blit(f_sec.render('Stats oficiales', True, (240, 200, 80)), (40, 402))
                oficiales = stats_oficiales(nombre)
                if oficiales:
                    for i, (etiqueta, valor) in enumerate(oficiales):
                        y = 428 + i * 24
                        ventana.blit(f_txt.render(etiqueta, True, 'white'), (40, y))
                        pygame.draw.rect(ventana, (60, 60, 60), (130, y + 2, 140, 14))
                        pygame.draw.rect(ventana, (80, 180, 80), (130, y + 2, int(140 * min(valor, 200) / 200), 14))
                        ventana.blit(f_txt.render(str(valor), True, 'white'), (276, y))
                else:
                    ventana.blit(f_txt.render('Sin datos (ejecutá generar_datos.py)', True, (200, 200, 200)), (40, 430))
                ventana.set_clip(panel.inflate(-10, -10))
                y = panel.y + 12 - estado['scroll']
                for tipo_fila, contenido in estado['filas']:
                    alto = altos[tipo_fila]
                    if panel.y - 30 < y < panel.bottom:
                        if tipo_fila == 't': ventana.blit(f_sec.render(contenido, True, (240, 200, 80)), (panel.x + 15, y))
                        elif tipo_fila == 'p': ventana.blit(f_txt.render(contenido, True, (235, 235, 235)), (panel.x + 15, y))
                    y += alto
                ventana.set_clip(None)
                pantalla.presentar(); reloj_f.tick(60)

        def pokedex():
            """Lista de todos los pokemon ordenados por numero de pokedex; clic abre la ficha."""
            pygame.mouse.set_visible(True)
            entradas = sorted(pokemones, key=lambda n: (pokemones[n]['pokedex'] if isinstance(pokemones[n].get('pokedex'), int) else 9999, n))
            scroll = 0
            botones = []
            reloj_p = pygame.time.Clock()
            f_nombre, f_dato = tipografia.fuente(24), tipografia.fuente(22)
            columnas, bw, bh, sep = 4, 218, 78, 16                          # tarjetas: 4 columnas de 218 px (de margen a margen)
            arriba = menus.CONTENIDO_Y
            while True:
                filas = math.ceil(len(entradas) / columnas)
                max_scroll = max(0, filas * (bh + sep) - (H - arriba - 40))
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir'
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE: return None
                        if e.key in (pygame.K_DOWN, pygame.K_s): scroll = min(max_scroll, scroll + bh + sep)
                        if e.key in (pygame.K_UP, pygame.K_w): scroll = max(0, scroll - bh - sep)
                        if e.key == pygame.K_PAGEDOWN: scroll = min(max_scroll, scroll + 3 * (bh + sep))
                        if e.key == pygame.K_PAGEUP: scroll = max(0, scroll - 3 * (bh + sep))
                    if e.type == pygame.MOUSEWHEEL:
                        scroll = max(0, min(scroll - e.y * 60, max_scroll))
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for r, i in botones:
                            if r.collidepoint(pantalla.a_logico(e.pos)):
                                if ver_ficha(entradas, i) == 'salir': return 'salir'
                                break
                menus.fondo(ventana)
                botones = []
                ventana.set_clip(pygame.Rect(0, arriba - 6, W, H - arriba - 30 + 6))   # las tarjetas no se meten debajo del titulo ni del pie
                for i, nombre in enumerate(entradas):
                    x = menus.MARGEN_X + i % columnas * (bw + sep)
                    y = arriba + i // columnas * (bh + sep) - scroll
                    r = pygame.Rect(x, y, bw, bh)
                    if r.bottom < arriba or r.top > H:
                        continue
                    menus.caja(ventana, r, 'panel', (32, 32, 32))
                    img = retrato_menu(nombre, bh - 18)
                    if img: ventana.blit(img, (x + 9, y + 9))
                    numero = pokemones[nombre].get('pokedex')
                    t = f_nombre.render(nombre.replace('_', ' ').title(), True, 'white')
                    ventana.blit(t, t.get_rect(bottomleft=(x + bh + 2, r.centery - 2)))
                    if numero:                                               # el numero arriba a la derecha, los tipos debajo del nombre
                        n_t = f_dato.render('#' + str(numero), True, (150, 160, 180))
                        ventana.blit(n_t, n_t.get_rect(topright=(r.right - 10, r.y + 8)))
                    tipos_txt = '/'.join(normalizar_tipo(t_) for t_ in pokemones[nombre].get('tipo', []))
                    d = f_dato.render(tipos_txt, True, (200, 210, 225))
                    ventana.blit(d, d.get_rect(topleft=(x + bh + 2, r.centery + 4)))
                    botones.append((r, i))
                ventana.set_clip(None)
                menus.titulo(ventana, 'Pokédex')
                menus.pie(ventana, 'arriba/abajo o rueda: desplazarte   clic: ver la ficha   ESC: volver')
                pantalla.presentar(); reloj_p.tick(60)

        return pokedex, descripcion_asistencia

    pokedex, descripcion_asistencia = armar_pokedex()

    def jugar(nombres, config, ranura=None, cargada=None, perfil=None):
        """Una partida entera: arma el equipo, recorre las salas una por una y devuelve como termino ('menu' o 'salir') junto con el pokemon activo.
        Si cae todo el equipo no termina: Celebi te lleva al hall y desde ahi sale otro viaje (perfil: nombre, genero, amigos, eras derrotadas).
        Adentro se arman por grupos (reglas, equipo, movimiento, ataques, enemigos, salas, hall, dibujo, extras) las funciones que usa el bucle."""
        pausa = {'total': 0}
        viaje = {'perfil': None, 'en_hall': False}  # el perfil de la partida y si estas en el hall (entre viaje y viaje)

        def tiempo(): return pygame.time.get_ticks() - pausa['total']

        def pausado(f, *args):
            """Llama a un menu sin que el tiempo de la partida avance mientras esta abierto (los enfriamientos no corren)."""
            t0 = pygame.time.get_ticks()
            controles.contexto('menu')
            r = f(*args)
            controles.contexto('juego')
            pausa['total'] += pygame.time.get_ticks() - t0
            return r

        ESC = generacion.crear_escenario()        # tamaño de la sala actual (se cambia en el lugar al entrar a otra)
        AREA = generacion.crear_area(ESC)
        mundo = {'ent': None, 'ef': efectos.crear()}  # entorno de la sala actual (terrenos, objetos, clima) y las particulas
        RESTAURAR_VIDA_ENTRE_SALAS = False          # True: como antes, cada sala empieza con la vida llena
        DURACION_CARTEL = 1200                      # ms que se ve un cartel ("sala completada", "conseguiste la llave"...)
        BASICO_DISTANCIA = {'daño': 0.65, 'enfriamiento': 1.5, 'distancia': 0.85}   # el ataque a distancia basico es mas flojo que el de cerca
        # el ataque cuerpo a cuerpo basico (E / clic izquierdo): multiplicadores sobre los datos del movimiento
        GOLPE_CUERPO = {'daño': 1.1, 'distancia': 1.3, 'area': 1.3, 'retroceso': 1.0}
        # combo de 3 golpes: apretando de nuevo dentro de la 'ventana' sale el siguiente; el tercero es un remate.
        # Cada golpe que conecta te devuelve energia y acelera tus especiales: pelear de cerca rinde mas que quedarse lejos.
        COMBO = {'ventana': 700,                 # ms para encadenar el siguiente golpe
                 'espera': 210,                  # ms minimos entre golpe y golpe (se ajusta por rol: los velocistas encadenan mas rapido)
                 'recuperacion': 430,            # ms despues del remate hasta poder empezar otro combo
                 'daño': (0.85, 0.95, 1.7),      # multiplicador de cada golpe
                 'arco': (65, 65, 100),          # grados a cada lado de donde apuntas que alcanza el golpe (el remate barre mas)
                 'alcance': (1.0, 1.0, 1.25),
                 'avance': (6, 8, 18),           # pixeles que das para adelante con cada golpe
                 'retroceso': (0.5, 0.5, 2.4),   # empujon (el remate los manda lejos)
                 'energia': (4, 4, 10),          # energia que devuelve cada golpe que conecta
                 'recarga': (180, 180, 550),     # ms que le saca a la espera de tus dos especiales cada golpe que conecta
                 'iman': 50}                     # grados: si hay un enemigo cerca y casi adelante, el golpe se acomoda solo hacia el
        CARRERA = {'daño': 1.5, 'avance': 46}   # golpe en carrera: atacar corriendo da un primer golpe mas fuerte y largo
        # parry: golpear cuerpo a cuerpo justo cuando un enemigo te va a pegar (su aviso brilla amarillo: ese es el momento)
        PARRY = {'ventana': 320,       # ms que dura el parry desde que golpeas (y cuanto antes del golpe enemigo podes apretar)
                 'fallo': 650,         # si no bloqueaste nada, ms hasta poder abrir otra ventana (asi no sirve apretar sin parar)
                 'aturdido': 1800,     # ms que el enemigo queda aturdido (no se mueve ni ataca)
                 'contragolpe': 2.0,   # mientras esta aturdido le haces este multiplicador de daño
                 'empujon': 45,        # pixeles que sale despedido el enemigo
                 'rebote': 2.0,        # las balas que bloqueas vuelven con este multiplicador de daño
                 'energia': 30, 'recarga': 1500, 'cura': 0.03}   # premio: energia, ms menos de espera en los especiales y vida (3%)
        # esquive (Espacio / L3): un salto corto en la direccion en que caminas (o para atras) con invulnerabilidad.
        # Si te iban a pegar mientras esquivabas es un esquive perfecto: recuperas energia y tu proximo golpe es un contraataque
        ESQUIVE = {'distancia': 125, 'duracion': 190, 'invulnerable': 280, 'energia': 26, 'espera': 380,
                   'perfecto_energia': 26, 'contra': 1.8, 'contra_dura': 1600}
        DURACION_ENTRADA = 450                      # ms que el pokemon camina solo al entrar a una sala
        CURA_SALA = 0.12                            # al limpiar una sala todo el equipo recupera el 12% de su vida
        NUMEROS = {'dura': 750, 'salto': 90, 'subida': 38}   # numeros de daño: cuanto duran, el saltito al aparecer y cuanto suben
        # estilo: (letra, puntos minimos, multiplicador de daño, color). Los puntos que da y saca cada cosa
        # Estilo: sale de 5 cosas -> el ritmo (cada cuanto le pegas a alguien), cuanto te moves, los combos, los relevos (cambiar de
        # pokemon peleando) y las sinergias (asistencias F/G). Matar da poco y sin enemigos vivos no suma nada.
        ESTILO = {'rangos': (('D', 0, 1.0, (170, 170, 170)), ('C', 150, 1.05, (120, 220, 255)), ('B', 330, 1.1, (120, 255, 150)),
                             ('A', 560, 1.17, (255, 220, 80)), ('S', 820, 1.25, (255, 110, 90))),
                  'maximo': 1000,
                  'golpe': 12, 'ritmo_ms': (700, 3000), 'ritmo_piso': 0.25,   # golpe: rinde todo si el anterior fue hace <=0,7 s, casi nada si fue hace 3 s
                  'por_repeticion': 0.28, 'piso_repeticion': 0.12,            # repetir el mismo ataque rinde menos
                  'mover': 0.45,                                              # por cuadro caminando (con enemigos vivos)
                  'remate': 45, 'relevo': 70, 'asistencia': 60,               # combo completo, relevo y sinergia
                  'baja': 12, 'parry': 40, 'esquive_perfecto': 30,
                  'golpe_recibido': 160,
                  'baja_por_cuadro': 0.6, 'baja_quieto': 3.0, 'quieto_ms': 1500,
                  'racha_ms': 3000, 'monedas_racha': 3}
        # la nota de la sala (sobre 100): cuanto vale cada parte y que hace falta para el maximo
        NOTA = {'ritmo': (25, (3000, 800)),            # promedio entre golpes: 3 s -> 0, 0,8 s -> 25
                'movimiento': (20, (40, 150)),         # pixeles por segundo peleando: 40 -> 0, 150 -> 20
                'combos': (20, 0.3),                   # combos completos: 0,3 por enemigo para el maximo (minimo 2)
                'relevos': (15, 3),                    # relevos que pegaron: 3 para el maximo
                'sinergias': (20, 2)}                  # asistencias usadas: 2 para el maximo
        NOTA_PREMIO = {'S': (60, 0.5), 'A': (35, 0.25), 'B': (15, 0.0), 'C': (0, 0.0), 'D': (0, 0.0)}   # monedas (x era+1) y chance de un objeto
        RELEVO = {'ventana': 1500, 'daño': 1.4}      # cambiar de pokemon peleando: el primer golpe del que entra pega mas
        RESERVA_MAX = 3                             # pokemon en la reserva como mucho (y solo se cambian en la tienda)
        EVOLUCION = {'mantener': 900}               # ms que hay que mantener la tecla de evolucionar
        DESAFIO = {'enemigos': 1.5, 'chance': 0.35}  # salas de desafio: 50% mas enemigos; la nota da el doble y mas chance de un objeto
        PREMIO_ROMPER = (('baya_oran', 0.07), ('llave_tesoro', 0.03), ('baya_aranja', 0.03), ('baya_ziuela', 0.01), ('zumo_baya', 0.015),
                         ('caramelo_raro', 0.008))   # lo que puede haber adentro de lo que rompes
        CURAR_ESPERA = 2500                         # ms entre una curacion rapida (tecla de curarse) y la siguiente
        RECOGIBLE = {'iman': 80, 'agarrar': 30, 'vel': 7}
        DESTELLO = 140                              # ms del flash de pantalla en el parry, el esquive perfecto y el remate
        IMPACTO = {'remate': 70, 'parry': 100, 'baja': 30}   # pausa de impacto (ms): el juego se frena un instante para que el golpe pese
        ESTELA = {'dura': 220, 'cada': 2}           # copias transparentes del sprite al esquivar, embestir o arrancar a correr
        PATADA_CAMARA = {'golpe': 4, 'remate': 9, 'dura': 110}   # la camara se corre un poquito hacia donde pegas
        VEL_ORILLA = 3.5                            # pixeles por frame al nadar hasta la orilla (cambiaste en el agua a uno que no nada)
        trucos = config['trucos']                   # menu secreto (Konami): vida infinita, sin recarga...
        DISTANCIA_COMPRA = 95                       # que tan cerca de una vitrina hay que estar para comprar
        NIVEL_VIAJE = progreso.NIVEL_INICIAL        # cada viaje nuevo (desde el hall) arranca con el equipo en este nivel y en su forma base, como en Hades
        DISTANCIA_HABLAR = 90                       # que tan cerca hay que estar para hablar con Celebi o con un amigo del hall
        VEL_RESIDENTE = 1.3                         # pixeles por frame a los que pasean tus amigos por el hall
        # baile (V / R3): a los que tienen poca vida los encariña (mas chance de que quieran unirse al derrotarlos);
        # a los demas los puede confundir (caminan sin rumbo y le pegan a sus compañeros). Los jefes no se confunden
        BAILE = {'energia': 30, 'espera': 6000, 'dura': 900, 'radio': 190,
                 'debil': 0.4,                      # con menos de este porcentaje de vida se encariñan en vez de confundirse
                 'encariño': 0.7, 'max_encariño': 3, # cada baile suma +70% de chance de amistad (hasta 3 veces)
                 'confundir': 0.55, 'confundido_ms': 4500}
        AMISTAD_EXTRA = 0.5                         # a los que les bailaste: chance (x0,5) de sumarse aunque ya haya otro amigo en la sala o estes en la espera
        VEL_P_ENEMIGO = 8                           # balas del anillo de los jefes (las de los tiradores van en ia.py)
        DIST_P_ENEMIGO = 250
        DAÑO_ENEMIGO = 10                           # daño base de un enemigo (se escala con la era y la sala)
        VIDA_ENEMIGO = 125                          # vida base de un enemigo comun (antes 100: con el combo caian demasiado rapido)
        ENERGIA_MAX, GASTO_SPRINT, REGEN_ENERGIA, ENERGIA_MIN, MULT_SPRINT, COOLDOWN_CAMBIO = 100.0, 0.45, 0.45, 25.0, 1.6, 2000
        ARRANQUE = {'mult': 2.1, 'dura': 230, 'reposo': 500}   # al empezar a correr (despues de medio segundo sin correr) arrancas con un pique
        DIRS = {(1,-1):'noreste',(1,1):'sureste',(-1,-1):'noroeste',(-1,1):'suroeste',(1,0):'este',(-1,0):'oeste',(0,-1):'norte',(0,1):'sur'}
        CD_JEFE, CD_PIEDRA = 5000, 2000
        DURACION_PIEDRA = 5000
        TAM_JEFE, BALAS_JEFE, PIEDRAS_POR_USO = 160, 24, 4
        DAÑO_JEFE, DAÑO_PIEDRA = 35, 15
        VIDA_JEFE, VIDA_REGI = 600, 1000
        MONEDAS_ENEMIGO, MONEDAS_SALA, MONEDAS_JEFE, MONEDAS_REGI = 4, 10, 120, 250
        REFUERZOS_REGI = {'umbral': 0.75, 'cantidad': 5, 'niveles_menos': 3,   # al perder un cuarto de vida, el Regi llama a 5 de su tipo
                          'umbral_de': {'regidrago': ia.REGIDRAGO['refuerzos'], 'regirock': 0.9, 'registeel': 0.9}}   # (estos en su primera fase)
        MINI_REGI = {'cada': 11000, 'primera': 4000, 'de_a': 2, 'max': 4, 'vida': 1.6, 'daño': 0.8, 'tam': 58, 'niveles_menos': 4}   # Regigigas invoca Regis chiquitos
        FASES_TEXTO = {'arceus': {2: 'Sentencia: el sello cae del cielo', 3: 'Sentencia grande, Proteccion y Recuperacion'},
                       'beta': {2: 'El piso se vuelve un triangulo', 3: 'Fase 3'},
                       'regidrago': {2: 'Te llevo a lo alto de su torre', 3: 'Se rompio la torre: ahora usa todo'},
                       'regice': {2: 'Coraza de hielo: chocale un bloque de hielo'},
                       'regirock': {2: 'Fuerza Bruta y arena movediza', 3: 'Se partio en 5 rocas rodantes'},
                       'registeel': {2: 'Iman y minas', 3: 'Foco Resplandor y Cuerpo Pesado'},
                       'regieleki': {2: 'Se escondio en las torres', 3: 'Sin torres: Jaula Voltio'}}
        # cuando cae Arceus: pasas al medio de la arena, caen Sentencias alrededor que vuelven vacio el piso y las paredes (menos un circulo
        # de 'libre' casillas de radio donde quedas parado) y Arceus Beta aparece flotando sobre el vacio, delante tuyo
        LLEGADA_BETA = {'espera': 1500, 'cada': 110, 'aviso': 900, 'paso': 230, 'radio': 130, 'libre': 3.5, 'separacion': 30, 'vida': 2.0, 'nivel_mas': 4}
        # barra de congelamiento: solo la cargan los golpes fuertes de tipo hielo (un rayo de Regice, un Walrein que te pega de lleno...).
        # Pisar hielo o escarcha solo resbala. FRIO_POR_DAÑO: un golpe del 30% de tu vida te congela de una; los golpecitos se descargan solos
        FRIO_MAX, FRIO_POR_DAÑO, DESCARGA_FRIO, DURACION_CONGELADO = 100.0, 340.0, 0.6, 2000
        ESTILO_MINI = {'regieleki': 'rapido', 'regidrago': 'tirador', 'regice': 'tirador'}               # los demas pegan de cerca

        def armar_reglas():
            """Reglas generales del combate: choques, tipos, modificadores y a quien se le puede pegar."""
            def mover(rect, dx, dy, piedras):
                """Mueve un rect por x y despues por y, sin meterse en ninguno de los rects de 'piedras'."""
                r = rect.copy(); r.x += dx
                if not any(r.colliderect(piedra) for piedra in piedras): rect.x += dx
                r = rect.copy(); r.y += dy
                if not any(r.colliderect(piedra) for piedra in piedras): rect.y += dy

            def tipo_combate(datos):
                """Tipo principal de un pokemon (el primero de su lista)."""
                tipos = datos.get('tipo') or []
                return normalizar_tipo(tipos[0]) if tipos else None

            def daño_con_tipo(daño, ataque_tipo, defensa_tipo):
                """Daño final segun la tabla de tipos y el clima de la sala (minimo 1 si el ataque pegaba algo)."""
                m = multiplicador_tipos(ataque_tipo, defensa_tipo)
                if mundo['ent']: m *= entorno.mult_clima(mundo['ent'], ataque_tipo)   # lluvia potencia agua, sol potencia fuego, etc.
                if daño <= 0: return 0
                return max(1, round(daño * m))

            def mod(j, clave):
                """Multiplicador del entorno (terreno, maquinas, clima), lo de equipo comprado en la tienda y los objetos que lleva el que pelea."""
                return j['entorno'].get(clave, 1.0) * tienda.mult(j['inventario'], clave) * tienda.mult_equipados(llevados(j), clave)

            def llevados(j):
                """Objetos equipados del pokemon que esta peleando (hasta 2)."""
                return j['equipo'][j['activo']].get('items', ()) if j.get('equipo') else ()

            def objetivos_de(nivel, con_objetos=True):
                """A quien le pueden pegar los ataques: enemigos, jefe y objetos rompibles."""
                jefe = nivel['jefe']
                lista = nivel['enemigos'][:] + ([jefe] if jefe else [])
                if jefe:                                                # rocas rodantes de Regirock y bocas de Regidrago
                    lista += [x for x in jefe.get('rodantes', []) + jefe.get('bocas', []) if x.get('atacable') and x['vida'] > 0]
                return lista + (entorno.destructibles(nivel['ent']) if con_objetos else [])

            return mover, tipo_combate, daño_con_tipo, mod, objetivos_de, llevados

        mover, tipo_combate, daño_con_tipo, mod, objetivos_de, llevados = armar_reglas()

        def armar_equipo():
            """El equipo del jugador: miembros, cambio de pokemon, sinergias, debug y velocidad."""
            def crear_miembro(nombre, nivel=progreso.NIVEL_INICIAL):
                """Pokemon del equipo: nivel, xp, IV/EV y movimientos (progreso.py) mas su vida y su asistencia."""
                miembro = progreso.nuevo(nombre, nivel)
                vida = progreso.vida_max(miembro)
                miembro.update({'vida': vida, 'max_vida': vida, 'asist': asistencia_de(nombre), 'asist_listo': 0,
                                'id': '%08x' % random.getrandbits(32)})   # quien es (para reconocerlo como amigo en el hall aunque evolucione)
                reiniciar_asistencia(miembro)
                return miembro

            def juego_de(m):
                """Datos de combate de la especie con las MT enseñadas puestas en sus casillas (E, Q, Shift, R)."""
                g = dict(datos_juego(m['nombre']))
                basicos, especiales = list(g['basicos']), list(g['especiales'])
                for k, mt in enumerate(m['movs']):
                    if not mt or not mts.datos(mt) or not mts.sirve_en(mt, k): continue      # una MT especial nunca queda en E o Q
                    if k < 2: basicos[k] = mt
                    else: especiales[k - 2] = (mt, mts.datos(mt))
                g['basicos'], g['especiales'] = basicos, especiales
                return g

            def nombre_mov(nombre):
                """Nombre para mostrar de un movimiento o una MT."""
                if not nombre: return '-'
                return mts.MTS[nombre]['nombre'][3:] if nombre in mts.MTS else datos.nombre_ataque(nombre)

            def datos_mov(nombre):
                """Datos de un movimiento: de la MT si es una, si no de la lista de movimientos."""
                return mts.datos(nombre) or buscar_movimiento(nombre)

            def reiniciar_asistencia(m):
                """Al entrar a una sala la asistencia arranca con un 30% de su espera ya cargada."""
                m['asist_listo'] = tiempo() + round(m['asist']['enfriamiento'] * 0.3)

            def actualizar_sinergia(j):
                """Suma las pasivas de los pokemon vivos de la banca (cada rol da algo: daño, defensa, velocidad o recargas)."""
                total = {}
                for i, m in enumerate(j['equipo']):
                    if i == j['activo'] or m['vida'] <= 0: continue
                    for clave, valor in sinergia_de(m['nombre'], m.get('sinergia')).items(): total[clave] = total.get(clave, 0) + valor
                j['sinergia'] = total

            def aplicar_pokemon(j, nombre, vida=None, centro=None):
                """Pone en el jugador los datos del pokemon activo: tamaño, vida, velocidad, multiplicadores y su animador."""
                m = j['equipo'][j['activo']]
                j['estados'] = m.setdefault('estados', {})           # veneno, quemadura...: son de cada pokemon (el que entra no los hereda)
                g = juego_de(m)
                m['max_vida'] = progreso.vida_max(m)
                rect = pygame.Rect(0, 0, g['ancho'], g['alto'])
                rect.center = centro or j['rect'].center
                j.update({'nombre': nombre, 'datos': pokemones[nombre], 'juego': g, 'tipos': g['tipos'], 'rol': g['rol'], 'max_vida': m['max_vida'],
                          'mults': progreso.multiplicadores(m), 'nivel': m['nivel'],
                          'vida': m['max_vida'] if vida is None else min(vida, m['max_vida']), 'velocidad': g['velocidad'], 'tamaño': g['tamaño'],
                          'ancho': g['ancho'], 'alto': g['alto'], 'rect': rect, 'ultimo_golpe': -1000, 'ultimo_proyectil': -1000, 'esp_ultimo': [-100000, -100000],
                          'atacando': False, 'anim_ataque': None, 'embestida': None, 'animador': AnimadorPokemon(nombre, rect, g['tamaño'])})
                j.pop('vida_atras', None)                         # la barra de daño atrasado no pasa al pokemon nuevo

            def crear_jugador(nombres, centro, modo):
                """Arrancas solo con tu inicial; el resto del equipo se suma por amistad."""
                equipo = [n for n in dict.fromkeys(nombres) if n in pokemones][:3] or ['electrike']
                j = {'modo': modo, 'uso': 'teclas' if modo == 'teclas' else 'mouse', 't_mouse': 0, 'pos_mouse': pantalla.raton(), 'ultimo_dir': (0, 1), 'direccion': 'sur', 'moviendose': False, 'corriendo': False, 'llave': False, 'energia': ENERGIA_MAX, 'agotado': False, 'buffs': {},
                     'resto': [0.0, 0.0], 'aim': (0.0, 1.0), 'dir_ataque': 0, 'ultimo_cambio': -10000, 'equipo': [crear_miembro(n) for n in equipo], 'activo': 0, 'sinergia': {},
                     'monedas': 0, 'inventario': tienda.inventario_nuevo(), 'entorno': {}, 'oculto': False, 'inercia': [0.0, 0.0], 'reserva': [],
                     'frio': 0.0, 'congelado_hasta': 0, 'resto_iman': [0.0, 0.0], 'estilo': estilo_nuevo()}
                aplicar_pokemon(j, equipo[0], centro=centro)
                mundo['jugador'] = j
                actualizar_sinergia(j)
                return j

            def guardar_activo(j):
                """Guarda la vida del pokemon activo en su lugar del equipo (antes de cambiarlo o de salir de la sala)."""
                j['equipo'][j['activo']]['vida'] = j['vida']

            def cambiar_slot(j, indice, forzar=False):
                """Cambia al pokemon del espacio 'indice' (no si esta debilitado, atacando, congelado o en la espera de 2,5 s).
                forzar: cambia igual (cuando se debilita el activo). Devuelve True si cambio."""
                ahora = tiempo()
                if not 0 <= indice < len(j['equipo']) or indice == j['activo']: return False
                m = j['equipo'][indice]
                if m['vida'] <= 0: return False
                if not forzar and (ocupado(j) or ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO or ahora < j['congelado_hasta']): return False
                guardar_activo(j)
                mec.al_cambiar(j)
                j['activo'] = indice; j['ultimo_cambio'] = ahora; j['buffs'] = {}; j['mec'] = {}
                aplicar_pokemon(j, m['nombre'], m['vida'])
                actualizar_sinergia(j)
                efectos.cambio(mundo['ef'], *j['rect'].center)
                if mundo['ent']:                                  # cambiaste en el agua a uno que no nada: va nadando hasta la orilla
                    j['a_la_orilla'] = entorno.orilla(mundo['ent'], j['rect'], j['tipos'])
                    if j['a_la_orilla'] and mundo.get('nivel'): cartel(mundo['nivel'], m['nombre'].replace('_', ' ').title() + ' nada hasta la orilla')
                if not forzar and mundo.get('nivel') and (mundo['nivel']['enemigos'] or mundo['nivel']['jefe']):
                    j['relevo_hasta'] = ahora + RELEVO['ventana']        # relevo: el primer golpe del que entra pega mas
                return True

            def equipar_debug(j, nombre, espacio):
                """Menu debug: pone un pokemon en un espacio del equipo de la partida (o lo intercambia si ya estaba)."""
                if nombre not in pokemones or espacio < 0: return
                guardar_activo(j)
                equipo = j['equipo']; a = j['activo']
                if espacio >= len(equipo):                       # espacio vacio: se suma al equipo
                    if nombre not in [mi['nombre'] for mi in equipo] and len(equipo) < 3: equipo.append(crear_miembro(nombre, j['nivel'])); actualizar_sinergia(j)
                    return
                otros = [i for i, mi in enumerate(equipo) if mi['nombre'] == nombre]
                if otros:
                    i = otros[0]
                    if i == espacio: return
                    equipo[espacio], equipo[i] = equipo[i], equipo[espacio]
                    nuevo = equipo[espacio]
                    if i == a: j['activo'] = espacio; actualizar_sinergia(j); return
                else:
                    nuevo = crear_miembro(nombre, j['nivel'])
                    equipo[espacio] = nuevo
                if espacio == a:
                    j['buffs'] = {}
                    aplicar_pokemon(j, nombre, nuevo['vida'])
                actualizar_sinergia(j)

            def reiniciar_jugador(j, centro):
                """Al entrar a una sala: te pone en la entrada. La vida sigue como estaba (sin curas, como en Hades)."""
                guardar_activo(j)
                for m in j['equipo']:
                    if RESTAURAR_VIDA_ENTRE_SALAS: m['vida'] = m['max_vida']
                    reiniciar_asistencia(m)
                j.update({'direccion': 'norte', 'moviendose': False, 'corriendo': False, 'llave': False, 'energia': ENERGIA_MAX, 'agotado': False, 'buffs': {},
                          'resto': [0.0, 0.0], 'inercia': [0.0, 0.0], 'entorno': {}, 'oculto': False, 'frio': 0.0, 'congelado_hasta': 0, 'a_la_orilla': None,
                          'esquive': None, 'inv_hasta': 0, 'combo': 0, 'combo_listo': 0, 'contra_hasta': 0, 'parry_hasta': 0, 'parry_libre': 0,
                          'atrapado_hasta': 0, 'en_arena': False})
                aplicar_pokemon(j, j['nombre'], j['equipo'][j['activo']]['vida'], centro=centro)
                actualizar_sinergia(j)

            def mult_buff(j, clave):
                """Multiplicador de un buff activo (danza espada, agilidad...) o 1 si no hay o ya se vencio."""
                b = j['buffs'].get(clave)
                return b[0] if b and tiempo() < b[1] else 1.0

            def velocidad_actual(j):
                """Velocidad del jugador con todo encima: buffs, sinergia, correr, terreno, tienda y nivel."""
                sprint = (ARRANQUE['mult'] if tiempo() < j.get('pique_hasta', 0) else MULT_SPRINT) if j['corriendo'] else 1.0
                paralisis = ESTADOS_J['paralisis']['vel'] if tiene_estado(j, 'paralisis') else 1.0
                return (j['velocidad'] * mult_buff(j, 'velocidad') * (1 + j['sinergia'].get('velocidad', 0)) * sprint * mod(j, 'velocidad') * j['mults']['velocidad'] * paralisis
                        * mec.mult_velocidad(j))

            return (crear_miembro, juego_de, nombre_mov, datos_mov, actualizar_sinergia, aplicar_pokemon, crear_jugador, guardar_activo,
                    cambiar_slot, equipar_debug, reiniciar_jugador, mult_buff, velocidad_actual)

        (crear_miembro, juego_de, nombre_mov, datos_mov, actualizar_sinergia, aplicar_pokemon, crear_jugador, guardar_activo, cambiar_slot,
         equipar_debug, reiniciar_jugador, mult_buff, velocidad_actual) = armar_equipo()

        def armar_movimiento():
            """Mover al jugador, la camara y hacia donde apunta."""
            def mover_jugador(j, piedras):
                """Mueve al jugador segun las teclas o la palanca: correr gasta energia, el hielo resbala y las cintas empujan."""
                if tiempo() < max(j['congelado_hasta'], j.get('atrapado_hasta', 0)) or tiene_estado(j, 'sueño') or tiene_estado(j, 'aturdido'):
                    j['moviendose'] = j['corriendo'] = False; j['inercia'] = [0.0, 0.0]; return
                dx, dy = controles.direccion()                   # teclas del perfil, palanca o cruz del control
                if tiene_estado(j, 'confusion'): dx, dy = -dx, -dy           # confundido: camina para el otro lado
                j['moviendose'] = bool(dx or dy)
                if j['agotado'] and j['energia'] >= ENERGIA_MIN: j['agotado'] = False
                gratis = mult_buff(j, 'sprint') > 1 or j['entorno'].get('sprint_gratis')     # en el hielo los de hielo corren gratis
                antes = j['corriendo']
                j['corriendo'] = j['moviendose'] and controles.mantiene('correr') and (gratis or not j['agotado'])
                ahora = tiempo()
                if j['corriendo'] and not antes and ahora - j.get('dejo_de_correr', -10000) >= ARRANQUE['reposo']: j['pique_hasta'] = ahora + ARRANQUE['dura']
                if antes and not j['corriendo']: j['dejo_de_correr'] = ahora
                if j['corriendo']:
                    if not gratis: j['energia'] = max(0.0, j['energia'] - GASTO_SPRINT * mod(j, 'gasto'))
                    if j['energia'] <= 0 and not gratis: j['agotado'] = True; j['corriendo'] = False
                elif ahora >= j.get('sin_regen_hasta', 0):                 # despues de esquivar la energia tarda un poquito en volver
                    j['energia'] = min(ENERGIA_MAX, j['energia'] + REGEN_ENERGIA * mod(j, 'regen') * (1 + j['sinergia'].get('energia', 0)) * mec.regen_energia(j))
                if j['moviendose']: j['ultimo_dir'] = (dx, dy)
                n = math.hypot(dx, dy) or 1; v = velocidad_actual(j)
                deseado = (dx / n * v, dy / n * v)
                if j['entorno'].get('resbala'):                     # hielo / aceite: cuesta frenar y doblar
                    j['inercia'] = [j['inercia'][0] * 0.95 + deseado[0] * 0.05, j['inercia'][1] * 0.95 + deseado[1] * 0.05]
                else: j['inercia'] = list(deseado)
                ex, ey = j['entorno'].get('empuje', (0, 0))         # cintas transportadoras
                j['resto'][0] += j['inercia'][0] + ex; j['resto'][1] += j['inercia'][1] + ey
                px, py = int(j['resto'][0]), int(j['resto'][1])
                j['resto'][0] -= px; j['resto'][1] -= py
                if not (px or py): return
                mover(j['rect'], px, 0, piedras)
                mover(j['rect'], 0, py, piedras)
                j['rect'].clamp_ip(AREA)

            def camara(j):
                """Esquina de arriba a la izquierda de lo que se ve: centrada en el jugador sin salirse de la sala."""
                return max(0, min(j['rect'].centerx - W // 2, ESC.width - W)), max(0, min(j['rect'].centery - H // 2, ESC.height - H))

            def apuntar(j):
                """Hacia donde mira y apunta el jugador: mouse, palanca derecha o la ultima direccion caminada (segun el modo)."""
                if j['embestida']: return
                ahora = tiempo()
                palanca = controles.apuntado()                   # con control: apunta la palanca derecha
                if palanca:
                    j['uso'] = 'control'; j['aim'] = palanca; j['direccion'] = direccion_de(pygame.Vector2(palanca)); return
                if j['uso'] == 'control': j['uso'] = 'teclas'     # solto la palanca: apunta para donde camina hasta que muevas el mouse
                if j['modo'] == 'teclas': j['uso'] = 'teclas'
                else:
                    pos = pantalla.raton(); botones = pygame.mouse.get_pressed()
                    if math.hypot(pos[0] - j['pos_mouse'][0], pos[1] - j['pos_mouse'][1]) >= 3 or botones[0] or botones[2]:
                        j['uso'] = 'mouse'; j['t_mouse'] = ahora
                    j['pos_mouse'] = pos
                    if j['modo'] == 'mixto' and j['uso'] == 'mouse' and j['moviendose'] and ahora - j['t_mouse'] > 1500: j['uso'] = 'teclas'
                if j['uso'] == 'teclas':
                    dx, dy = j['ultimo_dir']; n = math.hypot(dx, dy)
                    j['aim'] = (dx / n, dy / n); j['direccion'] = DIRS[(dx, dy)]
                    return
                cx, cy = camara(j)
                mx, my = pantalla.raton()
                vx, vy = mx + cx - j['rect'].centerx, my + cy - j['rect'].centery
                n = math.hypot(vx, vy)
                if n < 4: return
                j['aim'] = (vx / n, vy / n)
                j['direccion'] = direccion_de(pygame.Vector2(vx, vy))

            def punto_apuntado(j, alcance):
                """Punto del mapa donde apunta el jugador, como mucho a 'alcance' pixeles (asistencias de area)."""
                cx, cy = camara(j)
                mx, my = pantalla.raton()
                px, py = j['rect'].center
                if j['uso'] == 'teclas': mx, my = px - cx + j['aim'][0] * 250, py - cy + j['aim'][1] * 250
                vx, vy = mx + cx - px, my + cy - py
                n = math.hypot(vx, vy)
                if n > alcance: vx, vy = vx / n * alcance, vy / n * alcance
                return px + vx, py + vy

            def direccion_de(v):
                """Una de las 8 direcciones ('norte', 'sureste'...) para un vector."""
                sx = 0 if abs(v.x) < abs(v.y) * 0.4 else (1 if v.x > 0 else -1)
                sy = 0 if abs(v.y) < abs(v.x) * 0.4 else (1 if v.y > 0 else -1)
                return DIRS.get((sx, sy), 'sur')

            return mover_jugador, camara, apuntar, punto_apuntado, direccion_de

        mover_jugador, camara, apuntar, punto_apuntado, direccion_de = armar_movimiento()

        def armar_estilo():
            """Medidor de estilo (D a S) y nota de la sala. Sube con el ritmo de tus golpes (variados), moviendote, con combos completos,
            relevos y sinergias (asistencias); baja si te pegan, si te quedas quieto o si repetis siempre lo mismo. Sin enemigos vivos
            no suma nada. Rachas de bajas dan monedas. La nota de la sala sale de las mismas 5 cosas (ver NOTA)."""
            def estilo_nuevo():
                return {'puntos': 0.0, 'rango': 0, 'ultimo': None, 'repite': 0, 'actividad': 0, 'subio': 0, 'racha': 0, 'ultima_baja': -10000,
                        'ultimo_golpe_t': None, 'pos': None}

            def stats_nuevas(enemigos):
                """Lo que se va midiendo en una sala para la nota."""
                return {'inicio': tiempo(), 'daño': 0.0, 'parrys': 0, 'enemigos': enemigos, 'max_rango': 0,
                        'huecos': 0, 'suma_huecos': 0.0, 'ultimo_golpe': None, 'distancia': 0.0, 'combate_ms': 0.0,
                        'combos': 0, 'relevos': 0, 'sinergias': 0}

            def hay_peligro(nivel):
                """Si quedan enemigos vivos (o por aparecer) en la sala."""
                if not nivel or nivel.get('completado'): return False
                jefe = nivel.get('jefe')
                return (any(e['vida'] > 0 for e in nivel.get('enemigos', ())) or (jefe is not None and jefe.get('vida', 0) > 0)
                        or bool(nivel.get('oleadas')) or bool(nivel.get('apariciones')))

            def rango_de(puntos):
                return max(i for i, (_, minimo, _, _) in enumerate(ESTILO['rangos']) if puntos >= minimo)

            def sumar_estilo(j, puntos, nivel=None):
                """Suma (o resta) puntos de estilo. Si sube de rango, la letra salta. Sin enemigos vivos no suma (solo baja)."""
                if puntos > 0 and not hay_peligro(nivel if nivel is not None else mundo.get('nivel')): return
                e = j['estilo']
                antes = e['rango']
                e['puntos'] = max(0.0, min(ESTILO['maximo'], e['puntos'] + puntos))
                e['rango'] = rango_de(e['puntos'])
                if puntos > 0: e['actividad'] = tiempo()
                if e['rango'] > antes: e['subio'] = tiempo()
                if nivel is not None and nivel.get('stats'): nivel['stats']['max_rango'] = max(nivel['stats']['max_rango'], e['rango'])

            def contar(nivel, clave, cuanto=1):
                """Suma a lo que se mide para la nota (combos, relevos, sinergias...), solo mientras hay enemigos."""
                if nivel and nivel.get('stats') and hay_peligro(nivel): nivel['stats'][clave] += cuanto

            def registrar_accion(j, clase):
                """Cada vez que usas un ataque: si es el mismo que el anterior, cuenta como repetido (rinde menos estilo)."""
                e = j['estilo']
                e['repite'] = e['repite'] + 1 if clase == e['ultimo'] else 0
                e['ultimo'] = clase

            def estilo_por_golpe(j, nivel):
                """Un golpe que conecta: mas puntos cuanto mas seguido le venis pegando (ritmo) y cuanto mas variado.
                Los golpes que tocan a varios a la vez cuentan como uno para el ritmo."""
                e, ahora = j['estilo'], tiempo()
                antes = e.get('ultimo_golpe_t')
                if antes is not None and ahora - antes < 50: return          # el mismo golpe tocando a otro enemigo
                rapido, lento = ESTILO['ritmo_ms']
                hueco = None if antes is None else ahora - antes
                ritmo = 1.0 if hueco is None or hueco <= rapido else max(ESTILO['ritmo_piso'], 1 - (hueco - rapido) / (lento - rapido))
                e['ultimo_golpe_t'] = ahora
                variedad = max(ESTILO['piso_repeticion'], 1 - ESTILO['por_repeticion'] * e['repite'])
                sumar_estilo(j, ESTILO['golpe'] * variedad * ritmo, nivel)
                if nivel and nivel.get('stats') and hay_peligro(nivel):       # para la nota: el tiempo entre golpes
                    st = nivel['stats']
                    if st['ultimo_golpe'] is not None:
                        st['huecos'] += 1; st['suma_huecos'] += min(5000, ahora - st['ultimo_golpe'])
                    st['ultimo_golpe'] = ahora

            def mult_estilo(j):
                """Multiplicador de daño del rango actual (D x1 ... S x1.25)."""
                return ESTILO['rangos'][j['estilo']['rango']][2]

            def baja(j, nivel):
                """Un enemigo menos: un poco de estilo y racha (bajas seguidas en pocos segundos dan monedas extra)."""
                e = j['estilo']; ahora = tiempo()
                e['racha'] = e['racha'] + 1 if ahora - e['ultima_baja'] <= ESTILO['racha_ms'] else 1
                e['ultima_baja'] = ahora
                sumar_estilo(j, ESTILO['baja'], nivel)
                if e['racha'] >= 3:
                    cartel(nivel, 'Racha x' + str(e['racha']) + '!', 700)
                    soltar_monedas(nivel, j, *j['rect'].center, ESTILO['monedas_racha'] * min(5, e['racha'] - 2))   # con tope

            def golpe_recibido(j, nivel):
                """Te pegaron: baja el estilo y se corta la racha."""
                sumar_estilo(j, -ESTILO['golpe_recibido'])
                j['estilo']['racha'] = 0

            def enfriar_estilo(j, nivel=None):
                """Cada cuadro: moverte con enemigos vivos suma un poquito (y cuenta para la nota); el estilo se va solo,
                despacio si venis peleando y rapido si hace rato que no haces nada."""
                e = j['estilo']
                pos = j['rect'].center
                if e.get('pos') is not None and hay_peligro(nivel):
                    movido = math.hypot(pos[0] - e['pos'][0], pos[1] - e['pos'][1])
                    if movido > 25: movido = 0                                   # teletransporte, cambio de sala: no cuenta
                    if nivel.get('stats'):
                        nivel['stats']['distancia'] += movido; nivel['stats']['combate_ms'] += 1000 / 60
                    if movido > 0.5: sumar_estilo(j, ESTILO['mover'] * min(1.0, movido / 4), nivel)
                e['pos'] = pos
                quieto = tiempo() - e['actividad'] > ESTILO['quieto_ms']
                sumar_estilo(j, -(ESTILO['baja_quieto'] if quieto else ESTILO['baja_por_cuadro'] * (1 + e['rango'] * 0.4)))

            def nota_sala(nivel, j):
                """Nota de la sala al limpiarla (S, A, B, C o D): ritmo, movimiento, combos, relevos y sinergias. Devuelve (letra, detalle)."""
                st = nivel['stats']
                def entre(valor, cero, lleno): return max(0.0, min(1.0, (valor - cero) / (lleno - cero)))
                maximo, (cero, lleno) = NOTA['ritmo']
                prom = st['suma_huecos'] / st['huecos'] if st['huecos'] else 5000
                p_ritmo = maximo * entre(prom, cero, lleno)
                maximo, (cero, lleno) = NOTA['movimiento']
                p_mov = maximo * entre(st['distancia'] / max(1.0, st['combate_ms'] / 1000), cero, lleno)
                maximo, por_enemigo = NOTA['combos']
                p_combos = maximo * min(1.0, st['combos'] / max(2.0, st['enemigos'] * por_enemigo))
                maximo, hace_falta = NOTA['relevos']
                p_relevos = maximo * min(1.0, st['relevos'] / hace_falta)
                maximo, hace_falta = NOTA['sinergias']
                p_sinergias = maximo * min(1.0, st['sinergias'] / hace_falta)
                puntos = p_ritmo + p_mov + p_combos + p_relevos + p_sinergias
                letra = next(l for l, minimo in (('S', 85), ('A', 70), ('B', 50), ('C', 30), ('D', 0)) if puntos >= minimo)
                detalle = 'Ritmo %d  -  Movimiento %d  -  Combos %d  -  Relevos %d  -  Sinergias %d' % (
                    round(p_ritmo), round(p_mov), round(p_combos), round(p_relevos), round(p_sinergias))
                return letra, detalle

            return (estilo_nuevo, stats_nuevas, hay_peligro, sumar_estilo, contar, registrar_accion, estilo_por_golpe, mult_estilo, baja,
                    golpe_recibido, enfriar_estilo, nota_sala)

        (estilo_nuevo, stats_nuevas, hay_peligro, sumar_estilo, contar, registrar_accion, estilo_por_golpe, mult_estilo, baja, golpe_recibido,
         enfriar_estilo, nota_sala) = armar_estilo()

        def armar_ataques():
            """Ataques del jugador (basicos, especiales, asistencias, embestidas) y el daño que recibe."""
            def preparar(j, datos):
                """Copia del movimiento con el daño final: rol, buffs, sinergia, tienda, critico y el stat (Ataque o At. Esp.)."""
                datos = dict(datos)
                datos['tipo'] = datos.get('tipo') or datos.get('tipo_ataque') or tipo_combate(j['datos'])
                try: base = float(datos.get('daño', 0))
                except (TypeError, ValueError): base = 0
                tipo_mov = normalizar_tipo(datos['tipo'])
                extra = mod(j, 'daño') * tienda.mult_tipo(j['inventario'], tipo_mov) * tienda.mult_tipo_equipados(llevados(j), tipo_mov) * tienda.critico(j['inventario'])
                stat = j['mults']['fisico' if datos.get('forma') in ('cuerpo', 'embestida') else 'especial']   # Ataque o At. Esp. segun el golpe
                relevo = RELEVO['daño'] if tiempo() < j.get('relevo_hasta', 0) else 1.0      # recien entrado: el primer golpe pega mas
                quemado = ESTADOS_J['quemadura']['daño'] if tiene_estado(j, 'quemadura') else 1.0
                datos['daño'] = round(base * j['juego']['mult_daño'] * mult_buff(j, 'daño') * (1 + j['sinergia'].get('daño', 0)) * extra * stat * quemado
                                      * mult_estilo(j) * relevo * (100 if trucos.get('golpe_letal') else 1))
                datos['jugador'] = True; datos['relevo'] = relevo > 1
                return datos

            def enfriamiento_de(j, datos):
                """Espera (ms) antes de poder repetir el ataque, con rol, sinergia, buffs y terreno."""
                try: base = max(0, int(float(datos.get('enfriamiento', 300))))
                except (TypeError, ValueError): base = 300
                if trucos.get('sin_enfriamiento'): return 0
                return round(base * j['juego']['mult_enfriamiento'] * (1 - j['sinergia'].get('enfriamiento', 0)) * mult_buff(j, 'enfriamiento') * mod(j, 'enfriamiento')
                             * mec.mult_recarga(j) * mec.mult_recarga_especial(j, datos))

            def iniciar_ataque(j, forma, enfriamiento):
                """Pone la animacion de ataque que corresponde a la forma del golpe, mas rapida si el ataque recarga rapido."""
                a = j['animador']
                anim = a.buscar_para(forma)
                if not anim: return
                a.ritmo = max(0.8, min(1.6, 450.0 / max(1, enfriamiento)))
                j['atacando'] = True; j['anim_ataque'] = anim; j['dir_ataque'] = direcciones.index(j['direccion'])
                a.cambiar(anim, j['dir_ataque'], False)

            def golpear(j, datos, objetivos, efectos=None, arco=None, alcance_extra=1.0):
                """Golpe cuerpo a cuerpo: le pega a todo lo que esta adelante (en un arco de 'arco' grados a cada lado, o en el rectangulo
                de siempre si no se pide arco) y deja la estela. Devuelve los enemigos (no objetos) a los que les pego."""
                ax, ay = j['aim']
                try: d = max(1, int(float(datos.get('distancia', 50)) * alcance_extra))
                except (TypeError, ValueError): d = 50
                try: area = max(1, int(float(datos.get('area', 20))))
                except (TypeError, ValueError): area = 20
                px, py = j['rect'].center
                tocados = []
                for objetivo in objetivos:
                    if objetivo['vida'] <= 0: continue
                    mitad = max(objetivo['rect'].width, objetivo['rect'].height) / 2
                    vx, vy = objetivo['rect'].centerx - px, objetivo['rect'].centery - py
                    adelante, lado = vx * ax + vy * ay, abs(vx * ay - vy * ax)
                    if arco is None: adentro = -mitad <= adelante <= d + mitad and lado <= area + mitad
                    else:
                        dist = math.hypot(vx, vy)
                        angulo = math.degrees(math.acos(max(-1.0, min(1.0, adelante / dist)))) if dist else 0
                        adentro = dist <= d + mitad + max(j['rect'].size) / 2 and (angulo <= arco or dist <= mitad + max(j['rect'].size) / 2 + 6)
                    if adentro:
                        recibir_ataque(objetivo, datos, j['direccion'])
                        if not objetivo.get('objeto'): tocados.append(objetivo)
                entorno.reaccionar_linea(mundo['ent'], px, py, px + ax * d, py + ay * d, max(20, area), datos.get('tipo'), tiempo())   # congela, quema...
                if efectos is not None:
                    ahora = tiempo()
                    if arco is None or arco < 80:
                        efectos.append({'x': px, 'y': py, 'linea': (px + ax * d, py + ay * d), 'radio': max(3, min(area, 14)), 'tipo': datos.get('tipo'), 'inicio': ahora, 'hasta': ahora + 130})
                    else:                                               # el remate barre: un abanico de estelas
                        for grados in (-arco * 0.7, 0, arco * 0.7):
                            r = math.radians(grados); bx, by = ax * math.cos(r) - ay * math.sin(r), ax * math.sin(r) + ay * math.cos(r)
                            efectos.append({'x': px, 'y': py, 'linea': (px + bx * d, py + by * d), 'radio': max(3, min(area, 12)), 'tipo': datos.get('tipo'), 'inicio': ahora, 'hasta': ahora + 180})
                return tocados

            def lanzar(j, datos, proyectiles):
                """Dispara uno o varios proyectiles (en abanico) hacia donde apunta el jugador."""
                ax, ay = j['aim']
                d = max(20, max(j['ancho'], j['alto']) // 2)
                x, y = j['rect'].centerx + ax * d, j['rect'].centery + ay * d
                try: area = max(1, int(float(datos.get('area', 8))))
                except (TypeError, ValueError): area = 8
                tamaño = max(2, area * 2)
                cantidad, abanico = int(datos.get('cantidad') or 1), math.radians(float(datos.get('abanico') or 0))   # algunas MT tiran varios en abanico
                base = math.atan2(ay, ax)
                for k in range(cantidad):
                    ang = base + (k - (cantidad - 1) / 2) * (abanico / max(1, cantidad - 1))
                    vx, vy = math.cos(ang), math.sin(ang)
                    proyectiles.append({'x': float(x), 'y': float(y), 'vx': vx, 'vy': vy, 'direccion': j['direccion'], 'datos': datos, 'rect': pygame.Rect(0,0,tamaño,tamaño), 'distancia': 0, 'activo': True, 'golpeados': []})

            def area_efecto(j, datos, objetivos, efectos, centro=None):
                """Golpe en circulo alrededor del jugador (o en 'centro'): pega a todos adentro y hace reaccionar el terreno."""
                try: radio = max(10, int(float(datos.get('area', 100))))
                except (TypeError, ValueError): radio = 100
                c = pygame.Vector2(centro or j['rect'].center)
                for o in objetivos:
                    if o['vida'] > 0 and c.distance_to(o['rect'].center) <= radio + max(o['rect'].width, o['rect'].height) / 2:
                        recibir_ataque(o, datos, direccion_de(pygame.Vector2(o['rect'].center) - c))
                ahora = tiempo()
                entorno.reaccionar(mundo['ent'], c.x, c.y, radio, datos.get('tipo'), ahora)
                efectos.append({'x': c.x, 'y': c.y, 'radio': radio, 'tipo': datos.get('tipo'), 'inicio': ahora, 'hasta': ahora + 350})

            def iniciar_embestida(j, datos):
                """Empieza una embestida: el jugador sale disparado hacia donde apunta."""
                vx, vy = j['aim']
                n = 1.0
                try: distancia = float(datos.get('distancia', 180))
                except (TypeError, ValueError): distancia = 180.0
                try: velocidad = max(1.0, float(datos.get('velocidad', 15)))
                except (TypeError, ValueError): velocidad = 15.0
                j['embestida'] = {'vx': vx / n, 'vy': vy / n, 'restante': distancia, 'velocidad': velocidad, 'datos': datos, 'golpeados': [], 'resto': [0.0, 0.0]}

            def actualizar_embestida(j, objetivos, piedras):
                """Un paso de la embestida: avanza, le pega una vez a cada uno que toca y frena contra las paredes."""
                e = j['embestida']
                paso = min(e['velocidad'], e['restante'])
                e['resto'][0] += e['vx'] * paso; e['resto'][1] += e['vy'] * paso
                px, py = int(e['resto'][0]), int(e['resto'][1])
                e['resto'][0] -= px; e['resto'][1] -= py
                antes = j['rect'].center
                mover(j['rect'], px, 0, piedras); mover(j['rect'], 0, py, piedras)
                j['rect'].clamp_ip(AREA)
                e['restante'] -= paso
                if (px or py) and j['rect'].center == antes: e['restante'] = 0
                try: area = max(1, int(float(e['datos'].get('area', 22))))
                except (TypeError, ValueError): area = 22
                zona = j['rect'].inflate(area * 2, area * 2)
                for o in objetivos:
                    if o['vida'] > 0 and o not in e['golpeados'] and zona.colliderect(o['rect']):
                        recibir_ataque(o, e['datos'], j['direccion']); e['golpeados'].append(o)
                entorno.reaccionar(mundo['ent'], j['rect'].centerx, j['rect'].centery, area + max(j['rect'].size) / 2, e['datos'].get('tipo'), tiempo())
                if e['restante'] <= 0: j['embestida'] = None

            def descongelar(j, tipo):
                """Congelado solo se puede usar un movimiento de fuego o de lucha, y te descongela (si no, hay que esperar)."""
                if tiempo() < j.get('atrapado_hasta', 0): return False
                if tiempo() >= j['congelado_hasta']: return True
                if normalizar_tipo(tipo) not in ('fuego', 'lucha'): return False
                j['congelado_hasta'] = 0; j['frio'] = 0.0
                return True

            def ocupado(j):
                """Si el jugador no puede atacar ahora: embistiendo, esquivando o nadando a la orilla."""
                return bool(j['embestida'] or j.get('esquive') or j.get('a_la_orilla') or tiene_estado(j, 'sueño') or tiene_estado(j, 'aturdido'))

            def apuntar_al_cercano(j, objetivos, alcance):
                """Iman del golpe: si hay un enemigo cerca y casi adelante, el golpe se acomoda hacia el."""
                ax, ay = j['aim']; px, py = j['rect'].center
                mejor, dist_mejor = None, None
                for o in objetivos:
                    if o['vida'] <= 0 or o.get('objeto'): continue
                    vx, vy = o['rect'].centerx - px, o['rect'].centery - py
                    dist = math.hypot(vx, vy)
                    if not dist or dist > alcance + max(o['rect'].size) / 2: continue
                    if math.degrees(math.acos(max(-1.0, min(1.0, (vx * ax + vy * ay) / dist)))) > COMBO['iman']: continue
                    if dist_mejor is None or dist < dist_mejor: mejor, dist_mejor = (vx / dist, vy / dist), dist
                if mejor: j['aim'] = mejor; j['direccion'] = direccion_de(pygame.Vector2(mejor))

            def premiar(j, energia, recarga, cura=0.0):
                """Premio por pelear bien (golpes que conectan, parry, esquive perfecto): energia, menos espera en los especiales y algo de vida."""
                j['energia'] = min(ENERGIA_MAX, j['energia'] + energia)
                if energia and j['agotado'] and j['energia'] >= ENERGIA_MIN: j['agotado'] = False
                j['esp_ultimo'] = [t - recarga for t in j['esp_ultimo']]
                if cura and not trucos.get('vida_infinita'): j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * cura)

            def abrir_parry(j, nivel):
                """Apretar el golpe abre la ventana de parry (si no la gastaste recien). Los que estan por pegarte ahora mismo quedan bloqueados."""
                ahora = tiempo()
                if ahora < j.get('parry_libre', 0): return
                ventana = PARRY['ventana'] * mod(j, 'parry')
                ventana = round(ventana * mec.mult_parry(j))                  # Armadura fosil, Filo psiquico
                j['parry_hasta'] = ahora + ventana; j['parry_libre'] = ahora + PARRY['fallo']; j['parry_dura'] = ventana
                for e in nivel['enemigos']:
                    if e['vida'] > 0 and e.get('aviso') and e['aviso']['clase'] in ('golpe', 'embestida') and e['aviso']['hasta'] - ahora <= ventana:
                        intentar_parry(j, e, nivel)

            def usar_basico(j, indice, nivel, apretado=True):
                """Ataque basico: 0 = cuerpo a cuerpo (combo de 3 golpes, abre el parry), 1 = a distancia.
                apretado False: el boton se esta manteniendo (mouse o control), sirve para seguir el combo pero no abre parry."""
                nombre = j['juego']['basicos'][indice]
                base = datos_mov(nombre) if nombre else None
                if not base or ocupado(j): return
                if not mts.datos(nombre) or mts.MTS[nombre]['casillas'] == 'todas':     # los basicos (y las MT de combate) se ajustan
                    base = dict(base)                                   # copia: no se tocan los datos originales del movimiento
                    ajustes = BASICO_DISTANCIA if indice == 1 or base.get('forma') == 'proyectil' else GOLPE_CUERPO
                    for clave, k in ajustes.items():
                        try: base[clave] = float(base.get(clave, 0)) * k
                        except (TypeError, ValueError): pass
                datos = preparar(j, base)
                if not descongelar(j, datos.get('tipo')): return
                ahora = tiempo()
                if indice == 0 and apretado: abrir_parry(j, nivel)    # el parry no depende de que el golpe este listo
                if datos.get('forma') != 'cuerpo':                     # disparo (o una MT de disparo puesta en E)
                    enfriamiento = enfriamiento_de(j, datos)
                    clave = 'ultimo_golpe' if indice == 0 else 'ultimo_proyectil'
                    if ahora - j[clave] < enfriamiento: return
                    j[clave] = ahora
                    registrar_accion(j, 'distancia' if indice == 1 else 'golpe_mt')
                    iniciar_ataque(j, datos.get('forma', 'proyectil'), enfriamiento)
                    if datos.get('forma') == 'proyectil': lanzar(j, datos, nivel['proyectiles_pokemon'])
                    else: area_efecto(j, datos, objetivos_de(nivel), nivel['efectos'])
                    return
                golpe_combo(j, datos, nivel)

            def golpe_combo(j, datos, nivel):
                """Un golpe del combo: 1 y 2 rapidos, el 3 es un remate que barre, empuja lejos e interrumpe a los enemigos comunes."""
                ahora = tiempo()
                if ahora < j.get('combo_listo', 0): return
                paso = j.get('combo', 0) if ahora - j.get('ultimo_golpe', -10000) <= COMBO['ventana'] else 0
                if paso == 0: registrar_accion(j, 'cuerpo')                # un combo entero cuenta como una sola accion
                carrera = paso == 0 and (j['corriendo'] or ahora - j.get('dejo_de_correr', -10000) < 150)
                contra = ahora < j.get('contra_hasta', 0)
                datos = dict(datos)
                datos['daño'] = round(datos['daño'] * COMBO['daño'][paso] * (CARRERA['daño'] if carrera else 1) * (ESQUIVE['contra'] if contra else 1))
                datos['retroceso'] = float(datos.get('retroceso', 0) or 20) * COMBO['retroceso'][paso]
                objetivos = objetivos_de(nivel)
                apuntar_al_cercano(j, objetivos, float(datos.get('distancia', 60)) * COMBO['alcance'][paso] + 30)
                avance = CARRERA['avance'] if carrera else COMBO['avance'][paso]
                ax, ay = j['aim']
                solidos_j = entorno.solidos(mundo['ent'], j['tipos'])
                mover(j['rect'], round(ax * avance), 0, solidos_j); mover(j['rect'], 0, round(ay * avance), solidos_j); j['rect'].clamp_ip(AREA)
                espera = round(enfriamiento_de(j, {'enfriamiento': COMBO['espera']}) * mec.mult_enfriamiento_combo(j))
                iniciar_ataque(j, 'cuerpo', espera * 2)
                tocados = golpear(j, datos, objetivos, nivel['efectos'], COMBO['arco'][paso], COMBO['alcance'][paso])
                j['ultimo_golpe'] = ahora
                if paso == 2:                                           # remate: recuperacion un poco mas larga y vuelve al primer golpe
                    j['combo'] = 0; j['combo_listo'] = ahora + enfriamiento_de(j, {'enfriamiento': COMBO['recuperacion']})
                    nivel['temblor'] = max(nivel['temblor'], ahora + 90)
                    if tocados:
                        nivel['destello'] = (ahora, (255, 255, 255)); sumar_estilo(j, ESTILO['remate'], nivel); contar(nivel, 'combos')
                        mec.remate(j, nivel, tocados)
                        nivel['pausa_hasta'] = ahora + IMPACTO['remate']
                else: j['combo'] = paso + 1; j['combo_listo'] = ahora + espera
                if contra and tocados: j['contra_hasta'] = 0; cartel(nivel, '¡Contraataque!', 600)
                if carrera and tocados: cartel(nivel, '¡Golpe en carrera!', 600)
                if tocados:
                    fuerza = PATADA_CAMARA['remate' if paso == 2 else 'golpe']
                    nivel['patada_camara'] = (j['aim'][0] * fuerza, j['aim'][1] * fuerza, ahora + PATADA_CAMARA['dura'])
                    premiar(j, COMBO['energia'][paso], COMBO['recarga'][paso])
                    if paso == 2:
                        for e in tocados:
                            if e is nivel['jefe'] or e.get('jefe') or e.get('de_jefe'): continue
                            e['aviso'] = None; e['embestida_ia'] = None          # el remate interrumpe lo que estaba por hacer
                            e['cd_ataque'] = max(e.get('cd_ataque', 0), ahora + 500)

            def esquivar(j, nivel):
                """Esquive: salto corto hacia donde caminas (si estas quieto, para atras) con invulnerabilidad. Gasta energia."""
                ahora = tiempo()
                if ocupado(j) or ahora < max(j['congelado_hasta'], j.get('atrapado_hasta', 0), j.get('esquive_listo', 0)): return
                gratis = mult_buff(j, 'sprint') > 1
                costo = ESQUIVE['energia'] * mod(j, 'gasto')
                if not gratis and (j['agotado'] or j['energia'] < costo): cartel(nivel, 'Sin energía para esquivar', 500); return
                if not gratis: j['energia'] -= costo
                dx, dy = controles.direccion()
                if not (dx or dy): dx, dy = -j['aim'][0], -j['aim'][1]
                n = math.hypot(dx, dy) or 1
                largo = mod(j, 'esquive')
                j['esquive'] = {'vx': dx / n, 'vy': dy / n, 'restante': ESQUIVE['distancia'] * (0.8 + 0.2 * largo), 'hasta': ahora + ESQUIVE['duracion'],
                                'resto': [0.0, 0.0], 'perfecto': False}
                j['inv_hasta'] = ahora + ESQUIVE['invulnerable'] * largo
                j['esquive_listo'] = ahora + ESQUIVE['espera']; j['sin_regen_hasta'] = ahora + 450
                j['inercia'] = [0.0, 0.0]
                efectos.polvo(mundo['ef'], j['rect'].centerx, j['rect'].bottom)

            def actualizar_esquive(j, piedras):
                """Un paso del esquive: avanza rapido y frena contra las paredes."""
                e = j['esquive']
                pasos_restantes = max(1, (e['hasta'] - tiempo()) / (1000 / 60))
                paso = min(e['restante'], max(4.0, e['restante'] / pasos_restantes))
                e['resto'][0] += e['vx'] * paso; e['resto'][1] += e['vy'] * paso
                px, py = int(e['resto'][0]), int(e['resto'][1])
                e['resto'][0] -= px; e['resto'][1] -= py
                mover(j['rect'], px, 0, piedras); mover(j['rect'], 0, py, piedras); j['rect'].clamp_ip(AREA)
                e['restante'] -= paso
                if e['restante'] <= 0.5 or tiempo() >= e['hasta'] + 60: j['esquive'] = None

            def esquive_perfecto(j):
                """Te iban a pegar mientras esquivabas: premio (una vez por esquive)."""
                if j.get('perfecto_hasta', 0) > tiempo(): return
                j['perfecto_hasta'] = j.get('inv_hasta', 0)
                premiar(j, ESQUIVE['perfecto_energia'], 0)
                sumar_estilo(j, ESTILO['esquive_perfecto'], mundo.get('nivel'))
                j['contra_hasta'] = tiempo() + ESQUIVE['contra_dura']
                efectos.destello(mundo['ef'], *j['rect'].center)
                if mundo.get('nivel'):
                    cartel(mundo['nivel'], 'Esquive perfecto! (tu proximo golpe es un contraataque)', 900)
                    mundo['nivel']['destello'] = (tiempo(), (170, 230, 255))

            def intentar_parry(j, e, nivel):
                """Si el jugador esta en su ventana de parry y el enemigo esta cerca, bloquea su ataque:
                el enemigo queda aturdido, sale despedido y recibe mas daño un rato. Ademas te premia. Devuelve True si hubo parry."""
                ahora = tiempo()
                if ahora >= j.get('parry_hasta', 0): return False
                alcance = max(j['rect'].size) + max(e['rect'].size) + 80        # tiene que estar mas o menos al alcance del golpe
                dx, dy = e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery
                distancia = math.hypot(dx, dy)
                if distancia > alcance: return False
                e['aviso'] = None; e['embestida_ia'] = None                     # pierde el ataque que estaba haciendo
                e['estado'], e['estado_hasta'] = 'paralizar', ahora + PARRY['aturdido']   # aturdido (la IA ya sabe que asi no ataca)
                e['contragolpe_hasta'] = e['estado_hasta']                       # mientras tanto le pegas mas fuerte (ver recibir_ataque)
                mec.al_parry(j, nivel, e)
                e['cd_ataque'] = e['estado_hasta'] + 500
                n = distancia or 1
                entorno.mover(mundo['ent'], e['rect'], round(dx / n * PARRY['empujon']), round(dy / n * PARRY['empujon']), entorno.tipos_de(e))
                parry_exitoso(j, nivel, e['rect'].center)
                return True

            def parry_exitoso(j, nivel, donde):
                """Lo que pasa con cualquier parry (golpe o bala): destello, premio y la ventana queda libre para el proximo."""
                ahora = tiempo()
                j['parry_libre'] = ahora                                         # acertaste: podes volver a intentarlo enseguida
                j['combo_listo'] = ahora                                         # y contragolpear sin esperar
                premiar(j, PARRY['energia'], PARRY['recarga'], PARRY['cura'])
                sumar_estilo(j, ESTILO['parry'], nivel)
                if nivel.get('stats'): nivel['stats']['parrys'] += 1
                efectos.cambio(mundo['ef'], *donde)                              # destello blanco
                nivel['temblor'] = max(nivel['temblor'], ahora + 120)            # sacudoncito de pantalla
                cartel(nivel, '¡Parry!', 700)
                nivel['destello'] = (ahora, (255, 240, 170)); nivel['pausa_hasta'] = ahora + IMPACTO['parry']

            def usar_especial(j, indice, nivel):
                """Especial 1 o 2 (Shift / R): proyectil, golpe, area, embestida, buff o cura, segun el movimiento."""
                nombre, base = j['juego']['especiales'][indice]
                datos = preparar(j, base)
                if not descongelar(j, datos.get('tipo')): return
                forma = datos.get('forma', 'proyectil')
                ahora = tiempo(); enfriamiento = enfriamiento_de(j, datos)
                if ocupado(j) or ahora - j['esp_ultimo'][indice] < enfriamiento: return
                j['esp_ultimo'][indice] = ahora
                if tiene_estado(j, 'paralisis') and random.random() < ESTADOS_J['paralisis']['falla']:   # paralizado: a veces no le sale
                    cartel(nivel, '¡Está paralizado! No se puede mover', 900); return
                registrar_accion(j, 'especial' + str(indice))
                iniciar_ataque(j, forma, enfriamiento)
                entorno.al_usar_movimiento(nivel['ent'], nombre, ahora)     # ej. viento hielo trae granizo
                objetivos = objetivos_de(nivel)
                if forma == 'proyectil': lanzar(j, datos, nivel['proyectiles_pokemon'])
                elif forma == 'cuerpo': golpear(j, datos, objetivos, nivel['efectos'])
                elif forma == 'area': area_efecto(j, datos, objetivos, nivel['efectos'])
                elif forma == 'embestida': iniciar_embestida(j, datos)
                elif forma == 'mecanica': mec.usar(j, datos, nivel)            # el especial propio de su linea (mecanicas.py)
                elif forma == 'buff':
                    try: duracion = int(float(datos.get('duracion', 5000)))
                    except (TypeError, ValueError): duracion = 5000
                    for clave, valor in (datos.get('buffs') or {}).items(): j['buffs'][clave] = (valor, ahora + duracion)
                elif forma == 'curar':
                    try: porcentaje = float(datos.get('porcentaje', 25))
                    except (TypeError, ValueError): porcentaje = 25
                    j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * porcentaje / 100)
                    efectos.cura(mundo['ef'], *j['rect'].center)

            def usar_asistencia(j, k, nivel):
                """Asistencia de un pokemon de la banca (F / G): impacto, escudo, furia, carrera, cura, desvanecer o masivo."""
                ahora = tiempo()
                reserva = [m for i, m in enumerate(j['equipo']) if i != j['activo']]
                if k >= len(reserva): return
                m = reserva[k]
                if m['vida'] <= 0 or ahora < m['asist_listo'] or not descongelar(j, m['asist']['tipo']): return
                a = m['asist']; mec = a['mecanica']
                objetivos = objetivos_de(nivel, mec != 'desvanecer')        # desvanecer no borra objetos
                m['asist_listo'] = ahora + a['enfriamiento']
                registrar_accion(j, 'asistencia'); sumar_estilo(j, ESTILO['asistencia'], nivel); contar(nivel, 'sinergias')   # usar la sinergia del equipo suma estilo
                entorno.al_usar_movimiento(nivel['ent'], a['nombre'], ahora)   # hidrobomba trae lluvia, llamarada sol, trueno tormenta...
                fuerza = progreso.multiplicadores(m)['especial']                   # la asistencia escala con el nivel del que la tira
                if mec == 'impacto':
                    datos = {'tipo': a['tipo'], 'daño': round(a['daño'] * a['mult_daño'] * fuerza * mult_estilo(j)), 'area': a['area'], 'retroceso': 30,
                             'efecto': a['efecto'], 'jugador': True}
                    area_efecto(j, datos, objetivos, nivel['efectos'], punto_apuntado(j, a['alcance']))
                elif mec in ('escudo', 'furia', 'carrera'):
                    for clave, valor in a['buffs'].items(): j['buffs'][clave] = (valor, ahora + a['duracion'])
                    nivel['efectos'].append({'x': j['rect'].centerx, 'y': j['rect'].centery, 'radio': 45, 'tipo': a['tipo'], 'inicio': ahora, 'hasta': ahora + 500})
                elif mec == 'curar':
                    j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * a['porcentaje'] / 100)
                    efectos.cura(mundo['ef'], *j['rect'].center)
                    nivel['efectos'].append({'x': j['rect'].centerx, 'y': j['rect'].centery, 'radio': 45, 'tipo': 'planta', 'inicio': ahora, 'hasta': ahora + 500})
                elif mec == 'desvanecer':
                    centro = pygame.Vector2(punto_apuntado(j, a['alcance']))
                    for o in objetivos:
                        if o['vida'] > 0 and centro.distance_to(o['rect'].center) <= a['area'] + max(o['rect'].width, o['rect'].height) / 2:
                            if o is nivel['jefe'] or o.get('de_jefe'): o['vida'] = max(0, o['vida'] - o['max_vida'] * a['porcentaje_jefe'] / 100)
                            else: o['vida'] = max(0, o['vida'] - o['max_vida'] * a['porcentaje'] / 100)
                    nivel['efectos'].append({'x': centro.x, 'y': centro.y, 'radio': a['area'], 'tipo': 'fantasma', 'inicio': ahora, 'hasta': ahora + 600})
                elif mec == 'masivo':
                    datos = {'tipo': 'normal', 'daño': round(a['daño'] * fuerza), 'area': a['area'], 'retroceso': 0, 'efecto': a['efecto'], 'jugador': True}
                    area_efecto(j, datos, objetivos, nivel['efectos'])

            def actualizar_jugador(j):
                """Animacion del jugador: termina el ataque en curso o camina / queda quieto al ritmo de su velocidad."""
                a = j['animador']
                if j['atacando'] and a.esta_terminada(): j['atacando'] = False
                d = direcciones.index(j['direccion'])
                if j['atacando']:
                    anim = j['anim_ataque'] or a.buscar_ataque()
                    if anim: a.cambiar(anim, j['dir_ataque'], False)
                    else: j['atacando'] = False
                else:
                    a.ritmo = max(0.6, min(3.0, velocidad_actual(j) / a.VELOCIDAD_REFERENCIA))
                    a.cambiar('walk' if j['moviendose'] else 'idle', d, True)
                a.actualizar()

            def dañar_jugador(j, daño, tipo=None, evitable=True, atacante=None):
                """Le saca vida al jugador: tipos, buffs, sinergia, tienda y defensa (nada si esta el truco de vida infinita).
                evitable: golpes, balas y rayos se esquivan (mientras dura la invulnerabilidad del esquive no pegan y es esquive perfecto);
                el piso que quema o lastima no."""
                try: daño = max(0, float(daño))
                except (TypeError, ValueError): daño = 0
                if evitable and daño > 0 and tiempo() < j.get('inv_hasta', 0): esquive_perfecto(j); return 0
                daño = mec.recibido(j, daño, tipo, atacante, evitable)            # absorbe, lana, superguarda, prediccion...
                if daño <= 0: return 0
                if tipo: daño = daño_con_tipo(daño, tipo, j['tipos'])
                daño *= mult_buff(j, 'defensa') * (1 - j['sinergia'].get('defensa', 0)) * mod(j, 'defensa') * j['mults']['defensa']
                if trucos.get('vida_infinita'): return 0
                j['vida'] = max(0, j['vida'] - daño)
                if daño >= 1 and evitable: j['estados'].pop('sueño', None)        # un golpe te despierta
                if daño >= 1: j['golpe_en'] = tiempo(); j.setdefault('vida_atras', (j['vida'] + daño) / max(1, j['max_vida']))
                if daño >= 1 and evitable and mundo.get('nivel'):        # te pegaron: baja el estilo y se corta la racha
                    golpe_recibido(j, mundo['nivel'])
                if daño >= 1 and mundo.get('nivel', {}).get('stats'): mundo['nivel']['stats']['daño'] += daño
                if daño >= 1 and mundo.get('nivel'):                     # lo que te sacaron, en rojo
                    mundo['nivel'].setdefault('numeros', []).append({'x': j['rect'].centerx, 'y': j['rect'].top, 'dx': 0, 'valor': int(round(daño)),
                                                                     'color': (255, 90, 80), 'grande': daño >= j['max_vida'] * 0.2, 'inicio': tiempo()})
                if tipo and normalizar_tipo(tipo) == 'hielo' and 'hielo' not in j['tipos'] and tiempo() >= j['congelado_hasta']:   # los de hielo no se congelan
                    j['frio'] = min(FRIO_MAX, j['frio'] + FRIO_POR_DAÑO * daño / max(1, j['max_vida']))
                return daño

            # ----- estados del jugador (cada pokemon tiene los suyos): los ponen los golpes de algunos tipos y algunas mecanicas -----
            def golpe_al_jugador(j, d, t, atacante=None):
                """Un enemigo te pega (cuerpo a cuerpo si se sabe quien): daño, la mordida de Mawile y a veces un estado segun el tipo."""
                hecho = dañar_jugador(j, d, t, atacante=atacante) or 0
                if hecho >= 1:
                    estado_por_golpe(j, t)
                    if atacante: mec.golpe_enemigo(atacante, j, hecho)
                return hecho

            ESTADOS_J = {
                'veneno': {'nombre': 'Envenenado', 'dura': 8000, 'dps': 0.015, 'color': (180, 90, 220)},   # dps: parte de la vida por segundo
                'quemadura': {'nombre': 'Quemado', 'dura': 6000, 'dps': 0.008, 'daño': 0.8, 'color': (255, 120, 60)},   # y pega 20% menos
                'paralisis': {'nombre': 'Paralizado', 'dura': 5000, 'vel': 0.6, 'falla': 0.2, 'color': (250, 220, 60)},  # mas lento y a veces falla el especial
                'sueño': {'nombre': 'Dormido', 'dura': 2200, 'color': (170, 190, 255)},          # no se mueve ni ataca; un golpe lo despierta
                'confusion': {'nombre': 'Confundido', 'dura': 3000, 'color': (255, 150, 200)},   # camina al reves
                'aturdido': {'nombre': 'Aturdido', 'dura': 900, 'color': (255, 255, 160)},        # un instante sin poder hacer nada
            }
            ESTADO_POR_TIPO = {'veneno': ('veneno', 0.12), 'fuego': ('quemadura', 0.10), 'electrico': ('paralisis', 0.10),
                               'psiquico': ('confusion', 0.07), 'fantasma': ('confusion', 0.05)}   # chance de que un golpe enemigo te deje ese estado
            INMUNES = {'veneno': ('veneno', 'acero'), 'quemadura': ('fuego',), 'paralisis': ('electrico',)}

            def tiene_estado(j, estado):
                return tiempo() < (j.get('estados') or {}).get(estado, 0)

            def poner_estado(j, estado, ms=None):
                """Le pone un estado al pokemon que pelea (si su tipo no es inmune). Devuelve True si quedo."""
                if any(t in j['tipos'] for t in INMUNES.get(estado, ())) or trucos.get('vida_infinita'): return False
                if j.get('inmune_estados_hasta', 0) > tiempo(): return False
                ahora = tiempo()
                nuevo = not tiene_estado(j, estado)
                j['estados'][estado] = max(j['estados'].get(estado, 0), ahora + (ms or ESTADOS_J[estado]['dura']))
                if nuevo and mundo.get('nivel'): cartel(mundo['nivel'], '¡' + j['nombre'].replace('_', ' ').title() + ' está ' + ESTADOS_J[estado]['nombre'].lower() + '!', 1000)
                if nuevo: mec.estado_puesto(j, estado)                   # Sincronia
                return True

            def curar_estados(m, cuales=None):
                """Le saca los estados a un pokemon (a todos, o solo los de 'cuales')."""
                est = m.get('estados')
                if not est: return
                for e in list(est):
                    if cuales is None or e in cuales: est.pop(e, None)

            def estado_por_golpe(j, tipo):
                """Un golpe enemigo que te dio: segun su tipo, a veces te deja un estado."""
                t = normalizar_tipo(tipo) if tipo else None
                if t in ESTADO_POR_TIPO and random.random() < ESTADO_POR_TIPO[t][1]: poner_estado(j, ESTADO_POR_TIPO[t][0])

            def actualizar_estados(j):
                """Cada cuadro: el veneno y la quemadura sacan vida de a poco (sin dejarte en 0) y los estados vencidos se van."""
                ahora = tiempo()
                est = j.get('estados') or {}
                for e in [e for e, hasta in est.items() if ahora >= hasta]: est.pop(e, None)
                if ahora < j.get('tick_estado', 0): return
                j['tick_estado'] = ahora + 500
                for e in ('veneno', 'quemadura'):
                    if e in est and j['vida'] > 1:
                        daño = max(1, j['max_vida'] * ESTADOS_J[e]['dps'] * 0.5)
                        j['vida'] = max(1, j['vida'] - daño)
                        if mundo.get('nivel'):
                            mundo['nivel'].setdefault('numeros', []).append({'x': j['rect'].centerx, 'y': j['rect'].top, 'dx': 0, 'valor': int(round(daño)),
                                                                             'color': ESTADOS_J[e]['color'], 'grande': False, 'inicio': ahora})

            def recibir_ataque(obj, datos, direccion=None):
                """Un enemigo, jefe u objeto recibe un ataque: daño por tipo, efecto de estado (quemar, paralizar...) y empujon."""
                color = COLORES_TIPO.get(normalizar_tipo(datos.get('tipo')), (255, 255, 255))
                efectos.golpe(mundo['ef'], *obj['rect'].center, color, normalizar_tipo(datos.get('tipo')))   # chispas del color del tipo
                if obj.get('objeto'):                                   # barriles, arboles, autos...: los maneja el entorno
                    entorno.dañar_objeto(mundo['ent'], obj, datos, direccion, tiempo()); return
                if obj.get('invulnerable'): return
                ataque_tipo = datos.get('tipo') or datos.get('tipo_ataque')
                defensa_tipo = obj.get('tipo')
                try: daño_base = float(datos.get('daño', 0))
                except (TypeError, ValueError): daño_base = 0
                daño = daño_con_tipo(daño_base, ataque_tipo, defensa_tipo)
                grande = False
                if obj.get('contragolpe_hasta', 0) > tiempo(): daño = round(daño * PARRY['contragolpe']); grande = True   # le hiciste parry: pega mas
                elif obj.get('estado') == 'dormir' and obj.get('estado_hasta', 0) > tiempo() and daño > 0:
                    daño = round(daño * 1.5); obj['estado'] = None; obj['estado_hasta'] = 0; grande = True   # golpe a uno dormido: pega mas y lo despierta
                if obj.get('mult_recibido', 1.0) != 1.0 and daño: daño = max(1, round(daño * obj['mult_recibido']))   # coraza, Lento Inicio...
                jug_mec = mundo.get('jugador') if datos.get('jugador') else None
                if jug_mec and daño: daño = max(1, round(daño * mec.mult_golpe(jug_mec, obj, datos)))   # la mecanica de su linea (Tecnico, Mandibula...)
                obj['vida'] = max(0, obj['vida'] - daño)
                if jug_mec: mec.tras_golpe(jug_mec, obj, datos, daño)
                if daño: obj['golpe_flash'] = tiempo()
                if daño and datos.get('jugador') and mundo.get('jugador'):   # golpe tuyo: estilo (y el relevo, si recien entraste)
                    jug = mundo['jugador']
                    estilo_por_golpe(jug, mundo.get('nivel'))
                    if datos.get('relevo') and tiempo() < jug.get('relevo_hasta', 0):
                        jug['relevo_hasta'] = 0; sumar_estilo(jug, ESTILO['relevo'], mundo.get('nivel')); contar(mundo.get('nivel'), 'relevos')
                        if mundo.get('nivel'): cartel(mundo['nivel'], 'Relevo!', 700)
                if daño and mundo.get('nivel'):                          # el numero que salta
                    m = multiplicador_tipos(ataque_tipo, defensa_tipo)
                    color = (255, 150, 40) if grande else (255, 235, 70) if m >= 2 else (170, 170, 170) if m < 1 else (255, 255, 255)
                    mundo['nivel'].setdefault('numeros', []).append({'x': obj['rect'].centerx + random.randint(-10, 10), 'y': obj['rect'].top,
                                                                     'dx': random.uniform(-0.6, 0.6), 'valor': int(daño), 'color': color,
                                                                     'grande': grande or daño >= obj['max_vida'] * 0.25, 'inicio': tiempo()})
                efecto = datos.get('efecto'); ahora = tiempo()
                try: probabilidad = max(0, min(100, float(efecto.get('probabilidad', 100)))) if efecto else 0
                except (TypeError, ValueError): probabilidad = 100 if efecto else 0
                if efecto and random.randint(1, 100) <= probabilidad:
                    try: duracion = max(1, int(float(efecto.get('duracion', 1000))))
                    except (TypeError, ValueError): duracion = 1000
                    obj['estado'] = efecto.get('tipo'); obj['estado_hasta'] = ahora + duracion; obj['proximo_estado'] = ahora + 700
                try: retroceso = float(datos.get('retroceso', 0))
                except (TypeError, ValueError): retroceso = 0
                if retroceso and direccion in direccion_vector:          # el empujon no los mete adentro de paredes ni objetos
                    vx, vy = direccion_vector[direccion]
                    entorno.mover(mundo['ent'], obj['rect'], round(vx * retroceso), round(vy * retroceso), entorno.tipos_de(obj)); obj['rect'].clamp_ip(AREA)

            return (enfriamiento_de, actualizar_embestida, usar_basico, usar_especial, usar_asistencia, actualizar_jugador, dañar_jugador,
                    recibir_ataque, intentar_parry, parry_exitoso, esquivar, actualizar_esquive, ocupado,
                    ESTADOS_J, tiene_estado, poner_estado, curar_estados, estado_por_golpe, actualizar_estados, golpe_al_jugador,
                    preparar, golpear, lanzar, area_efecto, iniciar_embestida, esquive_perfecto)

        (enfriamiento_de, actualizar_embestida, usar_basico, usar_especial, usar_asistencia, actualizar_jugador, dañar_jugador,
         recibir_ataque, intentar_parry, parry_exitoso, esquivar, actualizar_esquive, ocupado,
         ESTADOS_J, tiene_estado, poner_estado, curar_estados, estado_por_golpe, actualizar_estados, golpe_al_jugador,
         preparar, golpear, lanzar, area_efecto, iniciar_embestida, esquive_perfecto) = armar_ataques()

        def armar_enemigos():
            """Enemigos, proyectiles y jefes."""
            def elegir_pokemon_enemigo(era):
                """Pokemon al azar de los de la era (primero los que tienen sprites)."""
                pool = [n for n in mundos.ERAS[era]['enemigos'] if n in pokemones]
                return random.choice([n for n in pool if tiene_sprites(n)] or pool or list(JUGABLES))

            def pokemon_de_tipo(tipo, era):
                """Pokemon (no jefes) que tienen ese tipo: primero los de la era, despues cualquiera."""
                tiene = lambda n: tipo in [normalizar_tipo(t) for t in pokemones[n].get('tipo', [])]
                de_la_era = [n for n in mundos.ERAS[era]['enemigos'] if n in pokemones and tiene(n)]
                todos = [n for n in JUGABLES if tiene(n)]
                pool = de_la_era or todos
                return [n for n in pool if tiene_sprites(n)] or pool or list(JUGABLES)

            def crear_enemigo(nivel, punto=None, cazando=None, nombre=None, nv=None, estilo=None):
                """Enemigo de la era de la sala, mas fuerte cuanto mas avanzas (o el pokemon y nivel que se pidan)."""
                nombre = nombre or elegir_pokemon_enemigo(nivel['sala']['era'])
                tipo = normalizar_tipo((pokemones[nombre].get('tipo') or ['normal'])[0])
                r = pygame.Rect(0, 0, 50, 50)
                r.center = punto or entorno.punto_libre(nivel['ent'], random, nivel['sala']['inicio'], 450)
                visual = max(34, min(70, datos_juego(nombre)['tamaño'] + 8))
                nv = max(1, (nv or nivel['nivel_enemigos']) + random.randint(-1, 1))   # nivel del enemigo: mas vida y mas daño cuanto mas alto
                vida = round(VIDA_ENEMIGO * progreso.crecimiento(nombre, nv, 'hp'))
                naturaleza = progreso.naturaleza_al_azar()                # como en los juegos: cambia un stat y que tan facil es amigarlo
                daño = round(DAÑO_ENEMIGO * progreso.crecimiento(nombre, nv, 'attack') * progreso.factor_naturaleza(naturaleza, 'attack'))
                e = {'tipo': tipo, 'nombre': nombre, 'nivel': nv, 'animador': AnimadorPokemon(nombre, r, visual), 'direccion': 'sur', 'prev': r.center, 'rect': r,
                     'vida': vida, 'max_vida': vida, 'daño': daño, 'naturaleza': naturaleza, 'color': COLORES_TIPO.get(tipo, (150, 150, 150)), 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0, 'entorno': {}}
                ia.preparar(e, estilo)
                e['id_desatasco'] = random.randint(0, 9)               # cada uno se revisa en un cuadro distinto
                if cazando: e['estado_ia'] = 'caza'; e['ultima_vista'] = cazando     # las oleadas ya saben donde estas
                return e

            def crear_mini_regi(nivel, nombre, punto, cazando):
                """Regi chiquito de Regigigas: un enemigo comun un poco mas fuerte, mucho mas flojo que el Regi de verdad."""
                e = crear_enemigo(nivel, punto, cazando, nombre, nivel['nivel_enemigos'] - MINI_REGI['niveles_menos'], ESTILO_MINI.get(nombre))
                e['vida'] = e['max_vida'] = round(e['vida'] * MINI_REGI['vida']); e['vida_ant'] = e['vida']
                e['daño'] = round(e['daño'] * MINI_REGI['daño'])
                e['animador'] = AnimadorPokemon(nombre, e['rect'], MINI_REGI['tam'])
                e['mini'] = True
                return e

            def crear_aparicion(nivel, a, j):
                """La marca de aparicion se cumplio: sale el enemigo (comun, refuerzo de un Regi o Regi chiquito)."""
                if a.get('mini'): return crear_mini_regi(nivel, a['nombre'], a['pos'], j['rect'].center)
                return crear_enemigo(nivel, a['pos'], j['rect'].center, a.get('nombre'), a.get('nv'))

            def invocaciones_jefe(nivel, j, jefe):
                """Los Regis llaman refuerzos de su tipo al perder un cuarto de vida; Regigigas invoca Regis chiquitos cada tanto; Arceus avisa cada fase."""
                ahora = tiempo()
                for texto, duracion in jefe['mensajes']: cartel(nivel, texto, duracion)     # avisos de la IA (coraza rota, desperto...)
                jefe['mensajes'].clear()
                if jefe['estilo'] in FASES_TEXTO and jefe['fase'] != jefe.setdefault('fase_vista', 1):
                    jefe['fase_vista'] = jefe['fase']
                    cartel(nivel, jefe['nombre'].replace('_', ' ').title() + ' - Fase ' + str(jefe['fase']), 2400, FASES_TEXTO[jefe['estilo']].get(jefe['fase']), grande=True)
                    efectos.explosion(mundo['ef'], *jefe['rect'].center, 200); nivel['temblor'] = ahora + 700
                marcar = lambda **extra: nivel['apariciones'].append(dict({'pos': entorno.punto_libre(nivel['ent'], random, j['rect'].center, 260), 'hasta': ahora + 900}, **extra))
                if jefe['estilo'] == 'regidrago': torre_regidrago(nivel, j, jefe, ahora)
                umbral = REFUERZOS_REGI['umbral_de'].get(jefe['estilo'], REFUERZOS_REGI['umbral'])
                if jefe['nombre'] in mundos.REGIS and not jefe.get('refuerzos') and jefe['vida'] <= jefe['max_vida'] * umbral:
                    jefe['refuerzos'] = True
                    pool = pokemon_de_tipo(jefe['tipo'], nivel['sala']['era'])
                    for _ in range(REFUERZOS_REGI['cantidad']): marcar(nombre=random.choice(pool), nv=nivel['nivel_enemigos'] - REFUERZOS_REGI['niveles_menos'])
                    cartel(nivel, jefe['nombre'].title() + ' llamo refuerzos!', 1800)
                if jefe['nombre'] == 'regigigas' and jefe.get('despierto'):        # recien despues del Lento Inicio
                    jefe.setdefault('prox_mini', ahora + MINI_REGI['primera'])
                    vivos = sum(1 for e in nivel['enemigos'] if e.get('mini')) + sum(1 for a in nivel['apariciones'] if a.get('mini'))
                    if ahora >= jefe['prox_mini'] and vivos < MINI_REGI['max']:
                        jefe['prox_mini'] = ahora + MINI_REGI['cada']
                        for _ in range(min(MINI_REGI['de_a'], MINI_REGI['max'] - vivos)):
                            jefe['mini_i'] = jefe.get('mini_i', -1) + 1                # va pasando por los 5 Regis
                            marcar(nombre=mundos.REGIS[jefe['mini_i'] % len(mundos.REGIS)], mini=True)
                        cartel(nivel, '¡Regigigas llama a los Regis!', 1600)

            def torre_regidrago(nivel, j, jefe, ahora):
                """Regidrago pide subir (te mordio) o bajar (se rompio la torre). Los que estaban en la sala esperan abajo."""
                pedido, jefe['pedido'] = jefe['pedido'], None
                ent, tam = nivel['ent'], nivel['sala']['tam']
                if pedido == 'subir':
                    nivel['abajo'] = nivel['enemigos']; nivel['enemigos'], nivel['apariciones'], nivel['proyectiles_enemigos'] = [], [], []
                    plataforma = entorno.armar_torre(ent, *ia.REGIDRAGO['torre'])
                    j['rect'].center = plataforma.center; j['atrapado_hasta'] = 0; j['inercia'] = [0.0, 0.0]
                    ia.subir_regidrago(jefe, plataforma, ahora)
                    nivel['temblor'] = ahora + 500
                elif pedido == 'bajar':
                    entorno.desarmar_torre(ent)
                    nivel['enemigos'] += nivel.pop('abajo', []); nivel['proyectiles_enemigos'] = []
                    j['rect'].center = (ESC.centerx, ESC.centery + tam * 2)
                    ia.bajar_regidrago(jefe, (ESC.centerx, ESC.centery - tam * 2), ahora)
                    nivel['temblor'] = ahora + 900

            def actualizar_animacion_enemigo(e):
                """Animacion de un enemigo segun como se movio: suaviza la direccion para que no titile y camina al ritmo real."""
                a = e['animador']
                c = e['rect'].center
                dx, dy = c[0] - e['prev'][0], c[1] - e['prev'][1]
                e['prev'] = c
                forzada = e.get('anim_forzada')
                if forzada and tiempo() < forzada[1]:                  # una animacion que pidio la IA (el lanzamiento de Regirock...)
                    for nombre in forzada[0]:
                        if nombre in a.sprites and a.cambiar(nombre, direcciones.index(e['direccion']), False): break
                    a.actualizar(); return
                vs = e.setdefault('vel_suave', [0.0, 0.0])          # promedio de los ultimos frames: en diagonal la direccion no titila
                vs[0] = vs[0] * 0.8 + dx * 0.2; vs[1] = vs[1] * 0.8 + dy * 0.2
                rapidez = math.hypot(*vs)
                if rapidez > 0.4:
                    nueva = direccion_de(pygame.Vector2(vs))
                    e['dir_cuenta'] = e.get('dir_cuenta', 0) + 1 if nueva == e.get('dir_cand') else 1
                    e['dir_cand'] = nueva
                    if e['dir_cuenta'] >= 4 or e.get('camina', 0) <= 0: e['direccion'] = nueva   # gira solo si la direccion nueva se mantiene
                    e['camina'] = 8                                 # sigue caminando unos frames aunque no se mueva un pixel
                    a.ritmo = max(0.5, min(1.6, rapidez / 3.0))     # el paso de la animacion acompaña la velocidad real
                else: e['camina'] = e.get('camina', 0) - 1
                a.cambiar('walk' if e['camina'] > 0 else 'idle', direcciones.index(e['direccion']), True)
                a.actualizar()

            def dibujar_enemigo(e, cx, cy):
                """Dibuja un enemigo con un anillo del color de su tipo a los pies. False si no tiene sprite."""
                r = e['rect']
                pygame.draw.ellipse(ventana, e['color'], (r.x - cx, r.bottom - cy - 12, r.width, 14), 3)
                centro = r.center
                r.center = (centro[0] - cx, centro[1] - cy - e.get('altura', 0))   # Registeel saltando (Cuerpo Pesado)
                ok = e['animador'].dibujar(ventana)
                if ok and tiempo() - e.get('golpe_flash', -10000) < 90:    # recien golpeado: la silueta en blanco
                    cuadro = e['animador'].cuadro()
                    if cuadro: ventana.blit(silueta(cuadro[0], (255, 255, 255), 200), (cuadro[1], cuadro[2]))
                r.center = centro
                return ok

            def actualizar_estado(e):
                """Estados alterados: la quemadura saca vida cada 0,7 s; al vencerse el estado se borra."""
                ahora = tiempo()
                if e['estado'] == 'quemar' and e['proximo_estado'] <= ahora < e['estado_hasta']:
                    e['vida'] = max(0, e['vida'] - 3); e['proximo_estado'] = ahora + 700
                if e['estado'] == 'veneno' and e['proximo_estado'] <= ahora < e['estado_hasta']:   # el veneno de las mecanicas: 2% cada 0,7 s
                    e['vida'] = max(0, e['vida'] - max(2, round(e['max_vida'] * 0.02))); e['proximo_estado'] = ahora + 700
                if ahora >= e['estado_hasta']: e['estado'] = None

            def crear_proyectil(x, y, dx, dy, daño, jefe=False, tipo=None, vel=VEL_P_ENEMIGO, alcance=DIST_P_ENEMIGO, tam=16):
                """Bala de un enemigo o jefe: posicion, direccion, daño, velocidad y alcance."""
                return {'x': float(x), 'y': float(y), 'dx': dx, 'dy': dy, 'daño': daño, 'jefe': jefe, 'tipo': tipo, 'distancia': 0, 'activo': True,
                        'vel': vel, 'alcance': alcance, 'tam': tam, 'rect': pygame.Rect(int(x) - tam // 2, int(y) - tam // 2, tam, tam)}

            def actualizar_proyectil(proyectil, j, piedras, rebotados=None):
                """Mueve una bala enemiga: se apaga al llegar a su alcance o chocar, y si toca al jugador le pega."""
                v = proyectil['vel']
                proyectil['x'] += proyectil['dx'] * v; proyectil['y'] += proyectil['dy'] * v; proyectil['distancia'] += v
                proyectil['rect'].center = round(proyectil['x']), round(proyectil['y'])
                entorno.reaccionar(mundo['ent'], proyectil['x'], proyectil['y'], 8, proyectil.get('tipo'), tiempo())   # las balas de hielo tambien congelan
                if proyectil['distancia'] >= proyectil['alcance'] or not ESC.colliderect(proyectil['rect']) or proyectil['rect'].collidelist(piedras) != -1:
                    proyectil['activo'] = False; return
                if proyectil['rect'].colliderect(j['rect']):
                    proyectil['activo'] = False
                    if rebotados is not None and tiempo() < j.get('parry_hasta', 0):   # parry: la bala vuelve hacia donde vino
                        datos = {'tipo': proyectil.get('tipo'), 'daño': round(proyectil['daño'] * PARRY['rebote']), 'distancia': proyectil['alcance'],
                                 'area': 6, 'velocidad': proyectil['vel'] * 1.3, 'retroceso': 15}
                        rebotados.append({'x': proyectil['x'], 'y': proyectil['y'], 'vx': -proyectil['dx'], 'vy': -proyectil['dy'], 'direccion': j['direccion'],
                                          'datos': datos, 'rect': proyectil['rect'].copy(), 'distancia': 0, 'activo': True, 'golpeados': []})
                        if mundo.get('nivel'): parry_exitoso(j, mundo['nivel'], (proyectil['x'], proyectil['y']))
                    elif (dañar_jugador(j, proyectil['daño'], proyectil.get('tipo')) or 0) >= 1: estado_por_golpe(j, proyectil.get('tipo'))

            def actualizar_proyectil_pokemon(proyectil, objetivos, piedras):
                """Mueve un proyectil del jugador: pega a lo que toca (los que atraviesan siguen) y se apaga al chocar."""
                vx, vy = proyectil['vx'], proyectil['vy']
                try: paso = max(0.1, float(proyectil['datos'].get('velocidad', 8)))
                except (TypeError, ValueError): paso = 8.0
                proyectil['x'] += vx * paso; proyectil['y'] += vy * paso; proyectil['distancia'] += paso; proyectil['rect'].center = round(proyectil['x']), round(proyectil['y'])
                try: distancia_maxima = max(1.0, float(proyectil['datos'].get('distancia', 250)))
                except (TypeError, ValueError): distancia_maxima = 250.0
                try: a = max(0, int(float(proyectil['datos'].get('area', 0))))
                except (TypeError, ValueError): a = 0
                entorno.reaccionar(mundo['ent'], proyectil['x'], proyectil['y'], max(8, a), proyectil['datos'].get('tipo'), tiempo())
                for o in objetivos:                                     # primero los objetivos (asi pega a los objetos antes de frenar en ellos)
                    if o['vida'] <= 0 or o in proyectil['golpeados']: continue
                    zona = o['rect'].inflate(a * 2, a * 2)
                    if zona.colliderect(proyectil['rect']):
                        recibir_ataque(o, proyectil['datos'], proyectil['direccion']); proyectil['golpeados'].append(o)
                        if not proyectil['datos'].get('atraviesa', False): proyectil['activo'] = False; return
                if proyectil['distancia'] >= distancia_maxima or not ESC.colliderect(proyectil['rect']) or proyectil['rect'].collidelist(piedras) != -1:
                    proyectil['activo'] = False

            def crear_jefe(nivel, nombre, vida, nv, tam=None, centro=None):
                """Jefe, Regi o Arceus: aparece arriba del centro de la arena (o donde se pida)."""
                r = pygame.Rect(0, 0, *(tam or (TAM_JEFE, TAM_JEFE)))
                r.center = centro or (ESC.centerx, ESC.centery - nivel['sala']['tam'] * 2)
                tipo = normalizar_tipo((pokemones.get(nombre, {}).get('tipo') or ['normal'])[0])
                ahora = tiempo()
                sprite = nombre if tiene_sprites(nombre) else nombre.split('_')[0]        # sin sprites de Arceus Beta usa los de Arceus
                jefe = {'rect': r, 'nombre': nombre, 'nivel': nv, 'jefe': True, 'vida': vida, 'max_vida': vida, 'daño': round(DAÑO_JEFE * progreso.crecimiento(nombre, nv, 'attack')), 'tipo': tipo,
                        'color': COLORES_TIPO.get(tipo, (255, 140, 0)), 'ultimo_golpe': 0, 'ultimo_disparo': ahora, 'ultimo_poder': ahora,
                        'animador': AnimadorPokemon(sprite, r, ia.BETA['tam'] if tam else TAM_JEFE), 'direccion': 'sur', 'prev': r.center, 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0, 'entorno': {}}
                ia.preparar_jefe(jefe)
                return jefe

            def crear_piedras_verdes(jefe):
                """Piedras que lastiman si las pisas, alrededor del jefe (sin pisarse entre ellas ni salir de la sala)."""
                nuevas = []
                for _ in range(PIEDRAS_POR_USO):
                    for _ in range(20):
                        a, d = random.uniform(0, math.tau), random.randint(120,400)
                        r = pygame.Rect(int(jefe['rect'].centerx + math.cos(a)*d), int(jefe['rect'].centery + math.sin(a)*d), 45, 45)
                        if not AREA.contains(r) or r.colliderect(jefe['rect']) or any(r.colliderect(x['rect']) for x in nuevas): continue
                        nuevas.append({'rect': r, 'tiempo': tiempo(), 'daño': 0}); break
                return nuevas

            def actualizar_jefe(jefe, j, proyectiles, verdes, contexto):
                """Movimiento y ataques avisados en ia.py; aca el anillo de balas, las piedras verdes y el choque."""
                ahora = tiempo()
                if not (jefe['estado'] in ('paralizar', 'dormir') and jefe['estado_hasta'] > ahora) or jefe['estilo'] == 'regieleki' or jefe.get('sin_estados'): ia.actualizar_jefe(jefe, contexto)
                jefe['rect'].clamp_ip(AREA)
                if ahora - jefe['ultimo_disparo'] >= CD_JEFE and jefe['estilo'] == 'jefe':   # Regigigas, Arceus, Beta y los Regis tienen sus propios ataques
                    for i in range(BALAS_JEFE):
                        a = i * math.tau / BALAS_JEFE; dx, dy = math.cos(a), math.sin(a); r = TAM_JEFE//2+10
                        proyectiles.append(crear_proyectil(jefe['rect'].centerx+dx*r, jefe['rect'].centery+dy*r, dx, dy, round(jefe['daño'] * 0.7), True, jefe['tipo']))
                    jefe['ultimo_disparo'] = ahora
                if ahora - jefe['ultimo_poder'] >= CD_PIEDRA and jefe['estilo'] == 'jefe':       # Regigigas y Arceus usan sus propios ataques
                    verdes.extend(crear_piedras_verdes(jefe)); jefe['ultimo_poder'] = ahora
                if jefe['rect'].colliderect(j['rect']) and ahora-jefe['ultimo_golpe'] >= 700 and not jefe.get('escondido') and not jefe.get('sin_contacto'):
                    dañar_jugador(j, jefe['daño'], jefe['tipo']); jefe['ultimo_golpe'] = ahora
                jefe['color'] = COLORES_TIPO.get(jefe['tipo'], jefe['color'])     # Arceus cambia de tipo (Multitipo)

            return (crear_enemigo, crear_aparicion, invocaciones_jefe, actualizar_animacion_enemigo, dibujar_enemigo, actualizar_estado, crear_proyectil,
                    actualizar_proyectil, actualizar_proyectil_pokemon, crear_jefe, actualizar_jefe)

        (crear_enemigo, crear_aparicion, invocaciones_jefe, actualizar_animacion_enemigo, dibujar_enemigo, actualizar_estado, crear_proyectil,
         actualizar_proyectil, actualizar_proyectil_pokemon, crear_jefe, actualizar_jefe) = armar_enemigos()

        def armar_salas():
            """Las salas: crearlas, carteles, monedas, experiencia, amigos, tienda y lo que pasa en cada frame."""
            def menu_niveles(rec):
                """F2: elegir era (TAB) y sala para probar. Devuelve (era, sala), None o 'salir'."""
                pygame.mouse.set_visible(True)
                era, seleccionado = rec['era'], rec['sala']
                columnas, bw, bh, bn, sy = 4, 210, 62, 28, 18
                scroll, botones = 0, []
                reloj_debug = pygame.time.Clock()
                f_titulo = tipografia.fuente(32)
                while True:
                    total = mundos.salas_de(rec, era)
                    filas = math.ceil(total / columnas)
                    max_scroll = max(0, 80 + filas * (bh + bn + sy) - H)
                    for e in controles.eventos():
                        if e.type == pygame.QUIT:
                            return 'salir'
                        if e.type == pygame.KEYDOWN:
                            if e.key in (pygame.K_ESCAPE, pygame.K_F2):
                                return None
                            if e.key == pygame.K_TAB:
                                era = (era + (-1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1)) % len(rec['plan']); seleccionado = 0; scroll = 0; continue
                            if e.key == pygame.K_UP and seleccionado - columnas >= 0: seleccionado -= columnas
                            if e.key == pygame.K_DOWN and seleccionado + columnas < total: seleccionado += columnas
                            if e.key == pygame.K_LEFT: seleccionado = max(0, seleccionado - 1)
                            if e.key == pygame.K_RIGHT: seleccionado = min(total - 1, seleccionado + 1)
                            if e.key == pygame.K_RETURN:
                                return era, seleccionado
                            y_sel = 85 + seleccionado // columnas * (bh + bn + sy)
                            if y_sel - scroll < 65: scroll = max(0, y_sel - 85)
                            if y_sel + bh + bn - scroll > H: scroll = min(max_scroll, y_sel + bh + bn - H + 20)
                        if e.type == pygame.MOUSEWHEEL:
                            scroll = max(0, min(scroll - e.y * 60, max_scroll))
                        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                            for r, i in botones:
                                if r.collidepoint(pantalla.a_logico(e.pos)):
                                    return era, i
                    total = mundos.salas_de(rec, era)                    # la era pudo cambiar con TAB
                    seleccionado = min(seleccionado, total - 1)
                    ventana.fill((20, 20, 20))
                    botones = []
                    ventana.blit(f_titulo.render('MENU DE SALAS - ' + mundos.ERAS[era]['nombre'], True, mundos.ERAS[era]['suelo']), (25, 15))
                    ventana.blit(fuente.render('TAB / Shift+TAB: cambiar de era - flechas o clic para elegir - ENTER para ir - F2 o ESC para cerrar', True, (200, 200, 200)), (25, 45))
                    for i in range(total):
                        x = 30 + i % columnas * 240
                        y = 85 + i // columnas * (bh + bn + sy) - scroll
                        r = pygame.Rect(x, y, bw, bh)
                        nr = pygame.Rect(x, y + bh, bw, bn)
                        if r.bottom < 65 or nr.top > H:
                            continue
                        tipo = mundos.tipo_sala(rec, era, i)
                        pygame.draw.rect(ventana, (80, 160, 80) if i == seleccionado else (200, 200, 200), r)
                        pygame.draw.rect(ventana, (50, 50, 50), nr)
                        ventana.blit(fuente.render('Sala ' + str(i + 1), True, 'black'), (x + 8, y + 22))
                        detalle = tipo if tipo in ('combate', 'tienda') else tipo + ': ' + str(mundos.jefe_de(era, tipo))
                        ventana.blit(fuente.render(detalle, True, 'white'), (x + 8, y + bh + 5))
                        botones.append((r, i))
                    pantalla.presentar(); reloj_debug.tick(60)

            def cartel(nivel, texto, duracion=DURACION_CARTEL, subtitulo=None, grande=False):
                """Mensaje que se ve un rato y se va solo (no hay que cerrarlo)."""
                ahora = tiempo()
                if not grande: nivel['carteles'] = [c for c in nivel['carteles'] if c['grande']]   # uno chico nuevo reemplaza al anterior
                else: nivel['carteles'] = [c for c in nivel['carteles'] if not c['grande']]       # y uno grande nuevo, al grande anterior
                nivel['carteles'].append({'texto': texto, 'sub': subtitulo, 'inicio': ahora, 'hasta': ahora + duracion, 'grande': grande})

            def repartir(total, partes):
                """Divide la cantidad de enemigos en oleadas (la primera un poco mas grande)."""
                if partes <= 1: return [total]
                primera = round(total * 1.3 / (partes + 0.3))                  # la primera trae un poco mas
                resto = total - primera
                base = [primera] + [resto // (partes - 1)] * (partes - 1)
                for i in range(resto - sum(base[1:])): base[1 + i] += 1
                return base

            def crear_nivel(rec, destino, entrada, j, registro=None, llegada=None):
                """Arma la sala actual del recorrido: mapa, entorno, puertas con su destino, enemigos y el cartel de entrada.
                registro: la sala ya estaba en el historial (volviste o cargaste la partida): se arma igual que la primera vez
                y, si ya la habias completado, sin enemigos y con las puertas abiertas. llegada: lado de la puerta por la que entras
                cuando volves para atras (apareces en la puerta por la que habias salido)."""
                nuevo = registro is None
                if nuevo:
                    era, tipo = rec['era'], mundos.tipo_sala(rec)
                    if destino and destino.get('tipo') == 'tesoro': tipo = 'tesoro'       # elegiste la puerta del tesoro
                    destinos = mundos.destinos_siguientes(rec, random)
                    if tipo in ('tienda', 'tesoro'):
                        destinos = [d for d in destinos if d['tipo'] != 'tesoro'][:2] or destinos[:1]   # del tesoro no se va a otro tesoro
                        lados = ['oeste', 'este'][:len(destinos)]; variante = None
                    elif tipo in ('jefe', 'regi', 'final'): destinos = destinos[:1]; lados = ['norte']; variante = None
                    else:
                        variantes = mundos.ERAS[era]['variantes']
                        variante = destino['variante'] if destino and destino.get('variante') in variantes else random.choice(list(variantes))
                        lados = random.sample([l for l in generacion.LADOS if l != entrada], len(destinos))
                    registro = {'era': era, 'sala': rec['sala'], 'tipo': tipo, 'semilla': random.random(), 'variante': variante, 'entrada': entrada,
                                'lados': lados, 'destinos': destinos, 'clima': rec['clima'], 'completada': False, 'salida': None, 'vitrinas': None,
                                'desafio': bool(destino and destino.get('desafio'))}
                    rec['historial'].append(registro); rec['pos'] = len(rec['historial']) - 1
                era, tipo, semilla = registro['era'], registro['tipo'], registro['semilla']
                if tipo == 'tienda': sala = generacion.generar_tienda(era, registro['lados'], semilla)
                elif tipo == 'tesoro': sala = generacion.generar_tesoro(era, registro['lados'], semilla)
                elif tipo in ('jefe', 'regi', 'final'): sala = generacion.generar_arena(era, registro['lados'], semilla, tipo)
                else: sala = generacion.generar_sala(era, registro['variante'], registro['entrada'], registro['lados'], semilla)
                hecha = registro['completada']
                ultima = rec['pos'] == len(rec['historial']) - 1
                for puerta, d in zip(sala['puertas'], registro['destinos']):
                    puerta['destino'] = d
                    if not ultima and puerta['lado'] != registro['salida']:      # en una sala vieja solo sigue la puerta por la que saliste
                        puerta['destino'] = dict(d, cerrado=True); puerta['bloqueada'] = True
                if rec['pos'] > 0 and sala.get('entrada'):                  # la puerta por la que entraste: vuelve a la sala anterior
                    sala['puertas'].append({'lado': sala['entrada'], 'atras': True, 'destino': {'tipo': 'volver'},
                                            'rect': generacion._rect_puerta(sala['entrada'], sala['columnas'], sala['filas'], sala['tam'])})
                ESC.size = sala['esc'].size                              # la sala nueva puede tener otro tamaño (la tienda)
                AREA.update(generacion.crear_area(ESC, sala['tam']))
                datos_era = mundos.ERAS[era]
                clima = datos_era.get('clima_regi') if tipo == 'regi' else datos_era.get('clima_final') if tipo == 'final' else None
                ent = entorno.crear(sala, clima or registro['clima'], tiempo())
                mundo['ent'] = ent
                if nuevo: tienda.nueva_sala(j['inventario'], tipo)       # los objetos de "por 3 salas" se gastan solo en salas nuevas
                esc = mundos.escala(era, registro['sala'])
                nivel = {'sala': sala, 'ent': ent, 'tipo': tipo, 'escala': esc, 'enemigos': [], 'jefe': None, 'proyectiles_pokemon': [], 'proyectiles_enemigos': [],
                         'efectos': [], 'verdes': [], 'puertas': sala['puertas'], 'llave': None, 'completado': tipo in ('tienda', 'tesoro') or hecha, 'monedas': [], 'carteles': [],
                         'oleadas': [], 'apariciones': [], 'vitrinas': [], 'salida': None, 'nivel_enemigos': progreso.nivel_de_sala(era, registro['sala'], tipo),
                         'nivel_sala': progreso.nivel_de_sala(era, registro['sala']),   # el de los enemigos comunes (para el ajuste de experiencia)
                         'amigos': [], 'entrando_hasta': tiempo() + DURACION_ENTRADA, 'saliendo': None, 'frame': 0, 'temblor': 0, 'llegada': None,
                         'registro': registro, 'revisita': hecha, 'inicio': sala['inicio']}
                if llegada:                                              # volviste para atras: entras por la puerta por la que habias salido
                    puerta = next((p_ for p_ in sala['puertas'] if p_['lado'] == llegada and not p_.get('atras')), None)
                    if puerta:
                        df, dc = generacion.PASO_LADO[llegada]
                        nivel['inicio'] = (puerta['rect'].centerx + dc * sala['tam'] * 1.4, puerta['rect'].centery + df * sala['tam'] * 1.4)
                        nivel['llegada_lado'] = llegada
                mundo['ef']['parts'], mundo['ef']['anims'] = [], []
                mundo['nivel'] = nivel
                if tipo == 'tienda':
                    if registro['vitrinas'] is None or len(registro['vitrinas']) != len(sala['vitrinas']):   # (las partidas de antes tenian otra tienda)
                        necesita = {r.get('objeto') or r.get('mt') for m in j['equipo'] for r in progreso.requisitos(m['nombre']) if 'objeto' in r or 'mt' in r}
                        items = tienda.surtido_mostradores(random, sala['vitrinas'], [m['nombre'] for m in j['equipo']], necesita)
                        registro['vitrinas'] = [[i_, False] for i_ in items]
                    nivel['vitrinas'] = [dict(v, item=i_, vendido=vendido) for v, (i_, vendido) in zip(sala['vitrinas'], registro['vitrinas'])]
                    titulo = datos_era['tienda']
                elif tipo == 'tesoro':                                  # tres premios: te llevas uno
                    if registro['vitrinas'] is None: registro['vitrinas'] = [[i_, False] for i_ in tienda.premios_tesoro(random)]
                    nivel['vitrinas'] = [dict(v, item=i_, vendido=vendido) for v, (i_, vendido) in zip(sala['vitrinas'], registro['vitrinas'])]
                    titulo = 'Sala del tesoro'
                elif hecha:
                    titulo = (sala.get('variante') or tipo).capitalize() if tipo == 'combate' else mundos.jefe_de(era, tipo).title()
                    titulo += ' (completada)'
                elif tipo in ('jefe', 'regi', 'final'):
                    nombre = mundos.jefe_de(era, tipo)
                    nv = nivel['nivel_enemigos']
                    vida = round((VIDA_JEFE if tipo == 'jefe' else VIDA_REGI * (1.5 if tipo == 'final' else 1)) * progreso.crecimiento(nombre, nv, 'hp'))
                    nivel['jefe'] = crear_jefe(nivel, nombre, vida, nv)
                    nivel['stats'] = stats_nuevas(14 if tipo == 'jefe' else 22)
                    titulo = nombre.title()
                else:
                    total = max(3, round(esc['cantidad'] * tienda.factor_enemigos(j['inventario']) * (DESAFIO['enemigos'] if registro.get('desafio') else 1)))
                    partes = 1 if registro['sala'] < 1 else 2 if registro['sala'] < 4 else random.choice((2, 3, 3, 4))
                    oleadas = repartir(total, partes)
                    nivel['enemigos'] = [crear_enemigo(nivel) for _ in range(oleadas[0])]   # la primera oleada ya esta (sin verte todavia)
                    nivel['oleadas'] = oleadas[1:]
                    nivel['stats'] = stats_nuevas(total)
                    titulo = sala['variante'].capitalize() + (' - desafío' if registro.get('desafio') else '')   # (la letra de los titulos no tiene la estrella)
                clima_txt = 'Interior' if ent['clima'] is None else entorno.CLIMAS[ent['clima']]['nombre']
                sub = datos_era['nombre'] + '  -  Sala ' + str(registro['sala'] + 1) + '/' + str(mundos.salas_de(rec, era)) + '  -  ' + clima_txt
                cartel(nivel, titulo, 2800 if not hecha else 1600, sub, grande=True)
                if tipo == 'regi' and hecha: abrir_portal(nivel, False)   # volviste a la sala del Regi: el portal de Celebi sigue abierto
                return nivel

            def impacto(nivel, x, y, radio, temblor):
                """Golpe fuerte de un jefe contra el piso: polvo, piedritas y la pantalla tiembla un rato."""
                efectos.explosion(mundo['ef'], x, y, radio * 0.6)
                efectos.romper(mundo['ef'], x, y, (140, 100, 60))
                nivel['temblor'] = max(nivel['temblor'], tiempo() + temblor)

            def empezar_llegada_beta(nivel, j, arceus):
                """Arceus desaparece, pasas al medio de la arena y se preparan las Sentencias que van a caer alrededor (de afuera hacia adentro)."""
                ahora, tam, ll = tiempo(), nivel['sala']['tam'], LLEGADA_BETA
                nivel['jefe'] = None; nivel['proyectiles_enemigos'] = []
                efectos.evolucion(mundo['ef'], *arceus['rect'].center)
                cartel(nivel, 'Arceus desapareció...', 2400, 'algo cae del cielo', grande=True)
                centro, libre = ESC.center, ll['libre'] * tam
                j['rect'].center = centro                             # el piso que queda es el del medio
                efectos.evolucion(mundo['ef'], *centro)
                puntos = [(x + random.randint(-40, 40), y + random.randint(-40, 40)) for y in range(tam // 2, ESC.height, ll['paso'])
                          for x in range(tam // 2, ESC.width, ll['paso']) if math.hypot(x - centro[0], y - centro[1]) > libre + ll['radio'] * 0.5]
                puntos.sort(key=lambda p: random.uniform(0, 400) - math.hypot(p[0] - centro[0], p[1] - centro[1]))   # de afuera hacia adentro
                golpes = [{'pos': p, 'inicio': ahora + ll['espera'] + i * ll['cada']} for i, p in enumerate(puntos)]
                nivel['llegada'] = {'golpes': golpes, 'centro': centro, 'libre': libre, 'fin': ahora + ll['espera'] + len(golpes) * ll['cada'] + ll['aviso'] + 500,
                                    'nv': arceus['nivel'] + ll['nivel_mas'], 'vida': round(arceus['max_vida'] * ll['vida'])}

            def actualizar_llegada_beta(nivel, j):
                """Caen las Sentencias y vuelven vacio el piso y las paredes donde caen; al final todo es vacio menos tu circulo
                y aparece Arceus Beta flotando delante tuyo con sus tablas."""
                ahora, ent, ll = tiempo(), nivel['ent'], nivel['llegada']
                (cx_, cy_), libre = ll['centro'], ll['libre']
                dx, dy = j['rect'].centerx - cx_, j['rect'].centery - cy_
                d, lim = math.hypot(dx, dy), libre - max(j['rect'].size) / 2 - 2
                if d > lim: j['rect'].center = (round(cx_ + dx / d * lim), round(cy_ + dy / d * lim))   # mientras caen no te deja salir del circulo
                for g in ll['golpes'][:]:
                    if ahora < g['inicio'] + LLEGADA_BETA['aviso']: continue
                    ll['golpes'].remove(g)
                    entorno.vaciar_alrededor(ent, ll['centro'], libre, *g['pos'], LLEGADA_BETA['radio'])
                    impacto(nivel, *g['pos'], LLEGADA_BETA['radio'] * 0.5, 200)
                if ahora < ll['fin']: return
                entorno.vaciar_alrededor(ent, ll['centro'], libre)         # lo que haya quedado entre las Sentencias
                beta = ia.BETA
                nivel['jefe'] = crear_jefe(nivel, 'arceus_beta', ll['vida'], ll['nv'], (beta['ancho'], beta['alto']),
                                           (cx_, cy_ - libre - LLEGADA_BETA['separacion'] - beta['alto'] // 2))
                nivel['jefe']['zona'] = ia.zona_circulo((cx_, cy_), libre)     # el circulo de piso donde peleas la fase 1
                nivel['llegada'] = None
                cartel(nivel, 'Arceus Beta', 2800, 'flota sobre el vacío, frente a vos', grande=True)
                impacto(nivel, cx_, cy_ - libre, 250, 900)

            def forzar_cambio(j):
                """Llave Giro de Arceus Beta: te cambia al siguiente pokemon vivo (por la espera de cambio no podes volver por 2 s).
                Si no tenes otro pokemon en pie no pasa nada."""
                vivos = [i for i, m in enumerate(j['equipo']) if i != j['activo'] and m['vida'] > 0]
                if not vivos or not cambiar_slot(j, vivos[0], forzar=True): return False
                cartel(mundo['nivel'], 'Llave Giro: te cambio de pokemon!', 1400)
                return True

            def quitar_objeto(j):
                """Desarme de Arceus Beta: perdes un objeto al azar de la mochila. Devuelve su nombre (None si no tenias)."""
                inv = j['inventario']['objetos']
                hay = [k for k, n in inv.items() if n > 0]
                if not hay: return None
                k = random.choice(hay)
                inv[k] -= 1
                if inv[k] <= 0: del inv[k]
                return mts.MTS[k]['nombre'] if k in mts.MTS else tienda.ITEMS.get(k, {}).get('nombre', k)

            def usar_curacion(j, m, indice):
                """Gasta la curacion de ese lugar del cinturon en el miembro m (el congelamiento solo lo tiene el que pelea).
                Si no le hace nada (vida llena, no tiene ese estado...) no se gasta. Devuelve (se uso, texto)."""
                cinturon = j['inventario'].setdefault('cinturon', [])
                if not 0 <= indice < len(cinturon): return False, 'Ese lugar del cinturón está vacío'
                clave = cinturon[indice]
                activo = m is j['equipo'][j['activo']]
                if activo: guardar_activo(j)
                marcado = activo and tiempo() < j['congelado_hasta']
                if marcado: m.setdefault('estados', {})['congelado'] = tiempo() + 60000
                ok, texto = tienda.usar_curativo(m, clave)
                if marcado and 'congelado' not in m['estados']: j['congelado_hasta'] = 0; j['frio'] = 0.0   # se descongelo
                m['estados'].pop('congelado', None)
                if not ok: return False, texto
                cinturon.pop(indice)                                     # los de atras avanzan un lugar
                if activo:
                    j['vida'] = m['vida']
                    efectos.cura(mundo['ef'], *j['rect'].center)
                actualizar_sinergia(j)
                return True, texto

            def curarse_rapido(j, nivel):
                """Tecla de curarse (Z): usa la curacion del lugar 1 del cinturon en el que pelea (el orden se acomoda en la mochila).
                Si esa no le sirve ahora, no se gasta y te avisa. Tiene una espera corta para que no sea spam."""
                ahora = tiempo()
                if ahora < j.get('curar_listo', 0) or ocupado(j): return
                cinturon = j['inventario'].setdefault('cinturon', [])
                if not cinturon:
                    cartel(nivel, 'El cinturón está vacío (las curaciones las vende Chikorita rosa)', 1200)
                    j['curar_listo'] = ahora + 600; return
                clave = cinturon[0]
                ok, texto = usar_curacion(j, j['equipo'][j['activo']], 0)
                cartel(nivel, tienda.ITEMS[clave]['nombre'] + ': ' + texto + ('' if ok else ' (no se gastó)'), 1400)
                j['curar_listo'] = ahora + (CURAR_ESPERA if ok else 600)
                j['cinturon_usado'] = ahora if ok else j.get('cinturon_usado', -10000)
                if not ok: return
                a = j['animador']
                if 'eat' in a.sprites: j['atacando'], j['anim_ataque'] = True, 'eat'; a.cambiar('eat', j['dir_ataque'], False); a.indice_frame = 0; a.terminada = False

            def dar_pocion_maxima(j, nivel=None):
                """Celebi te da una Pocion Maxima si no tenes (solo se puede llevar una) y si hay lugar en el cinturon."""
                cinturon = j['inventario'].setdefault('cinturon', [])
                if 'pocion_maxima' in cinturon or len(cinturon) >= tienda.CINTURON_MAX: return False
                cinturon.append('pocion_maxima')
                if nivel: cartel(nivel, 'Celebi te dio una Poción Máxima', 2000, 'cura toda la vida (solo se puede llevar una)')
                return True

            def soltar_objeto(nivel, x, y, clave):
                """Deja un objeto en el piso (baya, llave, caramelo...): salta un poquito y se junta al pasar cerca."""
                nivel.setdefault('recogibles', []).append({'x': float(x), 'y': float(y), 'item': clave, 'inicio': tiempo(),
                                                           'vx': random.uniform(-2.5, 2.5), 'vy': random.uniform(-2.5, 2.5)})

            def actualizar_recogibles(nivel, j):
                """Los objetos del piso: frenan, se acercan si estas cerca (o si la sala esta limpia) y al tocarlos se usan o van a la mochila."""
                for r in nivel.get('recogibles', [])[:]:
                    r['vx'] *= 0.88; r['vy'] *= 0.88; r['x'] += r['vx']; r['y'] += r['vy']
                    dx, dy = j['rect'].centerx - r['x'], j['rect'].centery - r['y']
                    d = math.hypot(dx, dy)
                    if tiempo() - r['inicio'] < 350: continue                # recien salio: todavia no se agarra
                    if d < RECOGIBLE['agarrar']:
                        nivel['recogibles'].remove(r)
                        item = tienda.ITEMS[r['item']]
                        if r['item'] == 'baya_oran':
                            j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.15); efectos.cura(mundo['ef'], *j['rect'].center)
                        else:
                            j['inventario']['objetos'][r['item']] = j['inventario']['objetos'].get(r['item'], 0) + 1
                            efectos.destello(mundo['ef'], *j['rect'].center)
                        cartel(nivel, item['nombre'] + '!', 900)
                        nivel['guardar'] = True
                    elif d < RECOGIBLE['iman'] * mec.mult_iman(j) or nivel['completado']:
                        r['x'] += dx / d * RECOGIBLE['vel']; r['y'] += dy / d * RECOGIBLE['vel']

            def soltar_monedas(nivel, j, x, y, cantidad):
                """Deja una pila de monedas en el piso (el amuleto moneda de la tienda las multiplica)."""
                cantidad = max(1, round(cantidad * tienda.mult(j['inventario'], 'monedas') * mec.mult_monedas(j)))
                nivel['monedas'].append({'x': float(x), 'y': float(y), 'valor': cantidad})

            def tecla_de(accion):
                """Tecla asignada a una accion en el perfil de teclado, para mostrarla en los carteles."""
                return str(controles.perfil('teclado').get(accion, '?')).upper()

            def ganar_xp(nivel, j, cantidad):
                """Experiencia: el que pelea toda, los de la banca 3/4. Con el ajuste elastico: cada uno gana menos si va muy arriba del nivel
                de la sala y mas si va abajo (asi la banca no queda atras). Avisa si alguien sube de nivel o ya puede evolucionar."""
                nivel_sala = nivel.get('nivel_sala', nivel['nivel_enemigos'])
                for i, m in enumerate(j['equipo']):
                    parte = cantidad if i == j['activo'] else cantidad * progreso.PARTE_BANCA
                    subidos = progreso.dar_xp(m, parte * progreso.ajuste_xp(m['nivel'], nivel_sala))
                    if not subidos: continue
                    antes = m['max_vida']; m['max_vida'] = progreso.vida_max(m)
                    if i == j['activo']:
                        j['vida'] += m['max_vida'] - antes; j['max_vida'] = m['max_vida']; j['mults'] = progreso.multiplicadores(m); j['nivel'] = m['nivel']
                        efectos.nivel(mundo['ef'], *j['rect'].center)
                    else: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] - antes)
                    cartel(nivel, m['nombre'].title() + ' subio al nivel ' + str(m['nivel']) + '!')   # si ya puede evolucionar, avisa actualizar_evolucion

            def amistad_de_era():
                """Cuantas veces alguien quiso unirse en esta era y cuantas salas van sin que nadie quiera (se reinicia al cambiar de era)."""
                am = rec.setdefault('amistad', {'era': rec['era'], 'ofertas': 0, 'salas_sin': 0})
                if am['era'] != rec['era']: am.update({'era': rec['era'], 'ofertas': 0, 'salas_sin': 0})
                return am

            def amigo_garantizado():
                """Si en esta sala alguien tiene que querer unirse si o si: la sala 2 de la Era Glacial, y en cada era la 1ra oferta
                antes de la sala GARANTIA_AMISTAD[0] y la 2da antes de la GARANTIA_AMISTAD[1] (asi cada era te deja un minimo de amigos)."""
                am = amistad_de_era()
                era_s, sala_s = progreso.SALA_AMIGO_SEGURO                   # el primer amigo del viaje: desde la sala 2 (si es tienda o tesoro, la siguiente)
                if rec['era'] == era_s and rec['sala'] >= sala_s and am['ofertas'] == 0: return True
                return any(am['ofertas'] < k + 1 and rec['sala'] >= sala for k, sala in enumerate(progreso.GARANTIA_AMISTAD))

            def quiza_amigo(nivel, j, e):
                """A veces un pokemon derrotado quiere unirse a vos (no se captura: se hace tu amigo).
                Reglas: uno por sala como mucho y despues una sala de espera sin ofertas. Si le bailaste (encariñado) tiene chance
                de sumarse igual (x AMISTAD_EXTRA), asi con el baile podes amigar a mas de uno.
                La chance depende de su especie, del nivel, de su naturaleza, del Lazo Amistad, de cuantas veces le bailaste y de las salas sin amigos."""
                if e.get('jefe') or e.get('mini'): return
                am = amistad_de_era()
                bailado = e.get('encariño', 0) > 0
                ya_hubo = nivel.get('ofertas_sala', 0) > 0                   # ya alguien quiso unirse en esta sala
                esperando = list(am.get('ultima') or ()) == [rec['era'], rec['sala'] - 1]   # la sala anterior ya te dio un amigo: esta es de espera
                if (ya_hubo or esperando) and not bailado: return
                mult = tienda.mult(j['inventario'], 'amistad') * (1 + BAILE['encariño'] * e.get('encariño', 0))
                prob = progreso.prob_unirse(e['nombre'], e['nivel'], j['nivel'], mult, e.get('naturaleza')) + progreso.PITY_AMISTAD * am['salas_sin']
                if ya_hubo or esperando: prob *= AMISTAD_EXTRA
                seguro = not ya_hubo and not esperando and amigo_garantizado()   # la garantia es solo para el primero de la sala
                if not seguro and random.random() >= prob: return
                am['ofertas'] += 1; am['salas_sin'] = 0; nivel['hubo_oferta'] = True
                if not esperando: am['ultima'] = [rec['era'], rec['sala']]    # la proxima sala es de espera
                nivel['ofertas_sala'] = nivel.get('ofertas_sala', 0) + 1
                e['vida'] = 1; e['amigable'] = True; e['aviso'] = None; e['embestida_ia'] = None; e['estado'] = None
                if not e['animador'].cambiar('sit', 0, True): e['animador'].cambiar('idle', 0, True)
                nivel.setdefault('amigos', []).append(e)
                cartel(nivel, e['nombre'].title() + ' quiere ser tu amigo (acercate y apretá ' + tecla_de('interactuar') + ')', 2400)

            def hablar_amigo(nivel, j):
                """Interactuar con el que quiere unirse (el mas cercano, si hay varios por el baile). Devuelve True si estaba cerca."""
                cerca_ = [x for x in nivel.get('amigos', ()) if math.hypot(x['rect'].centerx - j['rect'].centerx, x['rect'].centery - j['rect'].centery) <= 90]
                if not cerca_: return False
                e = min(cerca_, key=lambda x: math.hypot(x['rect'].centerx - j['rect'].centerx, x['rect'].centery - j['rect'].centery))
                nombre = e['nombre'].title()
                r = pausado(menus.preguntar, ui, nombre + ' (Nv ' + str(e['nivel']) + ') quiere unirse a tu equipo!', ['Que se una', 'Dejarlo ir'],
                            'naturaleza ' + progreso.texto_naturaleza(e.get('naturaleza')).split(' - ')[0] + '   -   tu equipo: ' + ', '.join(m['nombre'].title() for m in j['equipo']))
                if r == 0:
                    nuevo = crear_miembro(e['nombre'], e['nivel'])
                    nuevo['naturaleza'] = e.get('naturaleza') or nuevo['naturaleza']   # conserva la naturaleza con la que lo conociste
                    registrar_amigos(viaje['perfil'], [nuevo])              # queda como amigo para siempre (aunque se pierda este viaje)
                    if len(j['equipo']) < 3: j['equipo'].append(nuevo); actualizar_sinergia(j); cartel(nivel, nombre + ' se unió a tu equipo!')
                    elif len(j['reserva']) < RESERVA_MAX:
                        j['reserva'].append(nuevo); cartel(nivel, nombre + ' se fue a la reserva (se cambia en la tienda)', 2200)
                    else:                                                # reserva llena: a quien deja ir para hacerle lugar
                        k = pausado(menus.preguntar, ui, 'La reserva esta llena (' + str(RESERVA_MAX) + '). ¿A quien dejas ir?',
                                    [m['nombre'].title() + ' Nv ' + str(m['nivel']) for m in j['reserva']] + ['A ' + nombre + ' (no se une)'])
                        if k == 'salir': return True
                        if k is None or k >= len(j['reserva']): cartel(nivel, nombre + ' se fue'); nivel['amigos'].remove(e); return True
                        se_va = j['reserva'][k]
                        for item in se_va.get('items', []): j['inventario']['objetos'][item] = j['inventario']['objetos'].get(item, 0) + 1   # sus objetos quedan
                        j['reserva'][k] = nuevo
                        cartel(nivel, se_va['nombre'].title() + ' se despidio; ' + nombre + ' entro a la reserva', 2400)
                    efectos.corazones(mundo['ef'], *e['rect'].center)
                elif r == 1: cartel(nivel, nombre + ' se fue')
                else: return True
                nivel['amigos'].remove(e)
                return True

            def bailar(j, nivel):
                """V / R3: bailas un momento (Rotate, o Twirl / Hop si no tiene) y le afecta a los que estan cerca:
                - con poca vida se encariñan (Nod y corazones): mas chance de que quieran unirse cuando los derrotes;
                - con vida, a veces se confunden (Trip y estrellitas): caminan sin rumbo y le pegan a sus compañeros.
                Gasta energia y tiene espera. Los jefes y los Regis chiquitos no se dejan."""
                ahora = tiempo()
                if ocupado(j) or nivel['tipo'] in ('tienda', 'hall', 'tesoro'): return
                if ahora < j.get('baile_listo', 0): cartel(nivel, 'Todavía no podés bailar (' + str((j['baile_listo'] - ahora) // 1000 + 1) + ' s)'); return
                if j['energia'] < BAILE['energia'] * mod(j, 'gasto'): cartel(nivel, 'Sin energía para bailar'); return
                j['energia'] -= BAILE['energia'] * mod(j, 'gasto')
                j['baile_hasta'], j['baile_listo'] = ahora + BAILE['dura'], ahora + BAILE['espera']
                a = j['animador']
                paso = next((n for n in ('rotate', 'twirl', 'hop') if n in a.sprites), None)
                if paso: j['atacando'], j['anim_ataque'] = True, paso; a.cambiar(paso, j['dir_ataque'], False); a.indice_frame = 0; a.terminada = False
                encariñados = confundidos = 0
                for e in nivel['enemigos']:
                    if e['vida'] <= 0 or e.get('jefe') or e.get('mini') or e.get('amigable'): continue
                    if math.hypot(e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery) > BAILE['radio']: continue
                    if e['vida'] <= e['max_vida'] * BAILE['debil']:          # debil: se encariña con vos
                        e['encariño'] = min(BAILE['max_encariño'], e.get('encariño', 0) + 1)
                        e['anim_forzada'] = (('nod', 'hop'), ahora + 800)
                        efectos.corazones(mundo['ef'], *e['rect'].center); encariñados += 1
                    elif random.random() < BAILE['confundir']:               # sano: se marea
                        e['estado'], e['estado_hasta'] = 'confundir', ahora + BAILE['confundido_ms']
                        e['anim_forzada'] = (('trip', 'lostbalance', 'hurt'), ahora + 700)
                        confundidos += 1
                partes = []
                if encariñados: partes.append('se encariño con vos' if encariñados == 1 else str(encariñados) + ' se encariñaron con vos')
                if confundidos: partes.append('se confundio' if confundidos == 1 else str(confundidos) + ' se confundieron')
                if partes: cartel(nivel, ' y '.join(partes).capitalize() + '!', 2000, '(los encariñados quieren unirse mas facil cuando los derrotas)' if encariñados else None)

            def premio_jefe(nivel, j, jefe):
                """Los jefes dejan una MT que tu equipo pueda aprender (y el Regi, ademas, un objeto de evolucion si alguien lo necesita)."""
                inv = j['inventario']['objetos']
                if nivel['tipo'] in ('regi', 'final'):                      # derrotaste la era: cuenta para el hall (Ajustes > Hall > Automatico)
                    viaje['perfil']['eras'] = max(viaje['perfil']['eras'], nivel['sala']['era'] + 1)
                posibles = sorted({k for m in j['equipo'] for k in mts.aprendibles(m['nombre'])}) or list(mts.MTS)
                mt = random.choice(posibles)
                inv[mt] = inv.get(mt, 0) + 1
                cartel(nivel, '¡Conseguiste ' + mts.MTS[mt]['nombre'] + '!', 2200)
                necesita = [r['objeto'] for m in j['equipo'] for r in progreso.requisitos(m['nombre']) if 'objeto' in r]
                if nivel['tipo'] != 'jefe' and necesita:
                    obj = random.choice(necesita); inv[obj] = inv.get(obj, 0) + 1
                    cartel(nivel, '¡Conseguiste ' + tienda.ITEMS[obj]['nombre'] + '!', 2400)

            def abrir_portal(nivel, avisar=True):
                """Cayo el Regi: Celebi aparece al lado de la puerta y la convierte en un portal del tiempo hacia la era siguiente.
                Celebi llega flotando (Float) y despues queda mirandote (Idle). avisar=False: volviste a una sala de Regi ya hecha."""
                puerta = next((p_ for p_ in nivel['puertas'] if not p_.get('atras')), None)
                if not puerta or nivel.get('portal'): return
                tam = nivel['sala']['tam']
                pos = (puerta['rect'].centerx + tam * 1.9, puerta['rect'].bottom + tam * 1.4)   # al costado, un poco adentro (que no tape el cartel)
                r = pygame.Rect(0, 0, 40, 40); r.center = pos
                celebi = AnimadorPokemon('celebi', r, 70) if tiene_sprites('celebi') else None
                if celebi: celebi.cambiar('float', 0, True)
                nivel['portal'] = {'puerta': puerta, 'pos': pos, 'celebi': celebi, 'desde': tiempo()}
                if not avisar: return
                efectos.destello(mundo['ef'], *pos)
                destino = puerta.get('destino') or {}
                era = mundos.ERAS[destino['era']]['nombre'] if 'era' in destino and destino.get('tipo') != 'fin' else 'el final'
                cartel(nivel, 'Celebi abrió un portal', 2600, 'lleva a ' + era + ' (hablale con ' + tecla_de('interactuar') + ')', grande=True)

            def hablar_portal(nivel, j):
                """E al lado de Celebi en la sala del Regi: te ofrece cruzar el portal ahora. Devuelve True si estaba cerca."""
                p = nivel.get('portal')
                if not p or math.hypot(p['pos'][0] - j['rect'].centerx, p['pos'][1] - j['rect'].centery) > DISTANCIA_HABLAR + 20: return False
                destino = p['puerta'].get('destino') or {}
                era = mundos.ERAS[destino['era']]['nombre'] if 'era' in destino else 'la siguiente era'
                r = pausado(menus.preguntar, ui, '¡Bien ahí, ' + viaje['perfil']['nombre'] + '! Esta era ya respira tranquila. El portal va a ' + era + '.', ['¡Vamos!', 'Todavía no'],
                            'antes de cruzar podés juntar las monedas y lo que soltó el Regi')
                if r == 0 and not nivel['saliendo']:                     # cruzar ya: como si tocaras la puerta
                    cx, cy = camara(j)
                    nivel['saliendo'] = {'puerta': p['puerta'], 'hasta': tiempo() + 320}
                    efectos.transicion(mundo['ef'], 'salir', tiempo(), (j['rect'].centerx - cx, j['rect'].centery - cy))
                return True

            def vitrina_cercana(nivel, j):
                """La vitrina sin vender mas cerca del jugador (si esta al alcance y no esta mas cerca el lugar donde cura Chikorita)."""
                libres = [v for v in nivel['vitrinas'] if not v['vendido']]
                if not libres: return None
                distancia = lambda p: math.hypot(p[0] - j['rect'].centerx, p[1] - j['rect'].centery)
                v = min(libres, key=lambda v: distancia(v['pos']))
                punto = nivel['sala'].get('curandera') if nivel['tipo'] == 'tienda' else None
                if punto and distancia(punto) < distancia(v['pos']): return None
                return v if distancia(v['pos']) <= DISTANCIA_COMPRA else None

            def bloque_cercano(j):
                """El bloque de hielo de Regice que tenes al lado (si hay)."""
                cerca = [o for o in mundo['ent']['objetos'] if o['nombre'] == 'bloque_glaciar' and not (o['vel'][0] or o['vel'][1])]
                o = min(cerca, key=lambda o: math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery), default=None)
                return o if o and math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery) <= max(o['rect'].size) / 2 + 55 else None

            def empujar_bloque(nivel, j):
                """E al lado de un bloque de hielo: sale disparado para el otro lado y se desliza por la escarcha."""
                o = bloque_cercano(j)
                if not o: return False
                dx, dy = o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery
                n = math.hypot(dx, dy) or 1
                o['vel'] = [dx / n * 12, dy / n * 12]
                efectos.polvo(mundo['ef'], *o['rect'].midbottom)
                return True

            CURA = {'activo': (30, 15), 'equipo': (70, 30)}   # precio base y cuanto sube por era: curar al que pelea / curar y revivir a todos

            def curandera_cerca(nivel, j):
                """Si estas al lado del mostrador de Chikorita rosa (curaciones) en la tienda."""
                punto = nivel['sala'].get('curandera') if nivel['tipo'] == 'tienda' else None
                return punto is not None and math.hypot(punto[0] - j['rect'].centerx, punto[1] - j['rect'].centery) <= 95

            def hablar_curandera(nivel, j):
                """E al lado de Chikorita rosa: curar al que pelea o curar (y revivir) a todo el equipo, por monedas. True si estaba cerca."""
                if not curandera_cerca(nivel, j): return False
                guardar_activo(j)
                era = nivel['sala']['era']
                precio = {k: base + por_era * era for k, (base, por_era) in CURA.items()}
                activo = j['equipo'][j['activo']]
                herido = activo['vida'] < activo['max_vida'] or bool(activo.get('estados'))
                algun_herido = any(m['vida'] < m['max_vida'] or m.get('estados') for m in j['equipo'])
                saludo = 'Chikorita: ¿Te curo? Para eso estoy.' if algun_herido else 'Chikorita: ¡Están todos enteros! Mirá lo que tengo en el mostrador.'
                r = pausado(menus.preguntar, ui, saludo,
                            ['Curar a ' + activo['nombre'].replace('_', ' ').title() + ' (' + str(precio['activo']) + ' $)',
                             'Curar y revivir a todo el equipo (' + str(precio['equipo']) + ' $)', 'Nada'],
                            'tenés ' + str(j['monedas']) + ' $')
                if r not in (0, 1): return True
                if (r == 0 and not herido) or (r == 1 and not algun_herido): cartel(nivel, 'No hace falta'); return True
                clave = 'activo' if r == 0 else 'equipo'
                if j['monedas'] < precio[clave]: cartel(nivel, 'No te alcanza (' + str(precio[clave]) + ' $)'); return True
                j['monedas'] -= precio[clave]
                for m in ([activo] if clave == 'activo' else j['equipo']): m['vida'] = m['max_vida']; curar_estados(m)
                j['vida'] = activo['vida']; j['congelado_hasta'] = 0; j['frio'] = 0.0
                actualizar_sinergia(j)
                efectos.cura(mundo['ef'], *j['rect'].center); efectos.corazones(mundo['ef'], *nivel['sala']['curandera'])
                cartel(nivel, 'Chikorita te curó' if clave == 'activo' else 'Chikorita curó a todo el equipo')
                nivel['guardar'] = True
                return True

            def comprar_cercano(nivel, j):
                """E en la tienda: compra lo que tenes adelante. Devuelve True si habia algo para comprar."""
                v = vitrina_cercana(nivel, j) if nivel['tipo'] in ('tienda', 'tesoro') else None
                if not v: return False
                if nivel['tipo'] == 'tesoro':                            # el tesoro es gratis: te llevas uno y los otros se van
                    guardar_activo(j)
                    j['monedas'] += tienda.ITEMS[v['item']]['precio']     # gratis
                    mensaje = tienda.comprar(j, v['item'])
                    if v['item'] == 'caramelo_raro': j['inventario']['objetos']['caramelo_raro'] = j['inventario']['objetos'].get('caramelo_raro', 0) + 1   # son dos
                    j['vida'] = j['equipo'][j['activo']]['vida']           # Mas PS cura tambien al que pelea
                    for k_, otra in enumerate(nivel['vitrinas']):
                        otra['vendido'] = True; nivel['registro']['vitrinas'][k_][1] = True
                        if otra is not v: efectos.romper(mundo['ef'], *otra['pos'], (200, 200, 255))
                    efectos.evolucion(mundo['ef'], *v['pos'])
                    cartel(nivel, mensaje if not mensaje.startswith('Compraste') else tienda.ITEMS[v['item']]['nombre'] + ' x2!', 2400)
                    nivel['guardar'] = True
                    return True
                precio = tienda.ITEMS[v['item']]['precio']
                mensaje = tienda.comprar(j, v['item'])
                if mensaje.startswith('Compraste'):
                    v['vendido'] = True; ganar_xp(nivel, j, precio // 6)   # comprar tambien da experiencia
                    i_ = nivel['vitrinas'].index(v); nivel['registro']['vitrinas'][i_][1] = True; nivel['guardar'] = True
                cartel(nivel, mensaje)
                return True

            def actualizar_nivel(nivel, j):
                """Todo lo que pasa en un frame de la sala: jugador, entorno, enemigos, jefe, balas, monedas, llave y puertas.
                Devuelve 'siguiente' al salir por una puerta, 'muerte' si cayo todo el equipo, o None."""
                ahora = tiempo(); ent = nivel['ent']; enemigos = nivel['enemigos']; jefe = nivel['jefe']
                solidos_j, solidos_p = entorno.solidos(ent, j['tipos']), entorno.solidos_proyectil(ent)
                if mec.ignora_solidos(j): solidos_j = []                 # bajo tierra o volando: pasa por todo
                objetivos = objetivos_de(nivel)
                nivel['frame'] += 1
                if trucos.get('monedas_infinitas'): j['monedas'] = 99999
                if ahora < nivel['entrando_hasta']:                      # entrando a la sala: camina solo desde la puerta
                    ix, iy = nivel['inicio']
                    dx, dy = ix - j['rect'].centerx, iy - j['rect'].centery
                    paso = min(math.hypot(dx, dy), 3.2)
                    if paso > 0.5:
                        j['rect'].x += round(dx / math.hypot(dx, dy) * paso); j['rect'].y += round(dy / math.hypot(dx, dy) * paso)
                        j['direccion'] = direccion_de(pygame.Vector2(dx, dy)); j['moviendose'] = True
                    else: j['moviendose'] = False
                elif j.get('a_la_orilla'):                               # nadando hasta la orilla (no choca contra el agua)
                    ox, oy = j['a_la_orilla']
                    dx, dy = ox - j['rect'].centerx, oy - j['rect'].centery
                    d = math.hypot(dx, dy)
                    if d <= VEL_ORILLA: j['rect'].center = (round(ox), round(oy)); j['a_la_orilla'] = None
                    else:
                        j['rect'].x += round(dx / d * VEL_ORILLA); j['rect'].y += round(dy / d * VEL_ORILLA)
                        j['direccion'] = direccion_de(pygame.Vector2(dx, dy))
                        if nivel['frame'] % 6 == 0: efectos.polvo(mundo['ef'], j['rect'].centerx, j['rect'].bottom)
                    j['moviendose'] = True
                elif j.get('esquive'): actualizar_esquive(j, solidos_j); j['moviendose'] = True
                elif j['embestida']: actualizar_embestida(j, objetivos, solidos_j); j['moviendose'] = True
                else: mover_jugador(j, solidos_j)
                if (not j.get('a_la_orilla') and not j.get('esquive') and not j['embestida'] and ahora >= nivel['entrando_hasta']
                        and nivel['frame'] % 6 == 0 and j['rect'].collidelist(solidos_j) != -1):
                    j['a_la_orilla'] = entorno.orilla(ent, j['rect'], j['tipos'])   # quedaste adentro de algo (se derritio el hielo...): salis nadando
                actualizar_jugador(j)
                if (j.get('esquive') or j['embestida'] or (j['corriendo'] and ahora < j.get('pique_hasta', 0))) and nivel['frame'] % ESTELA['cada'] == 0:
                    cuadro = j['animador'].cuadro()                  # estela: una copia transparente del sprite
                    if cuadro:
                        color = (150, 230, 255) if j.get('esquive') else COLORES_TIPO.get(normalizar_tipo((j['embestida'] or {}).get('datos', {}).get('tipo')), (255, 255, 255)) if j['embestida'] else (255, 240, 180)
                        nivel.setdefault('estela', []).append({'img': cuadro[0], 'x': cuadro[1], 'y': cuadro[2], 'inicio': ahora, 'color': color})
                enfriar_estilo(j, nivel)
                actualizar_estados(j)
                actualizar_recogibles(nivel, j)
                if (j['corriendo'] or j['embestida'] or j.get('esquive')) and nivel['frame'] % 4 == 0: efectos.polvo(mundo['ef'], j['rect'].centerx, j['rect'].bottom)
                efectos.actualizar(mundo['ef'])
                contexto = {'ent': ent, 'jugador': j, 'enemigos': enemigos + ([jefe] if jefe else []), 'ahora': ahora,
                            'dañar_jugador': lambda d, t, a=None: golpe_al_jugador(j, d, t, a),
                            'aviso_mult': mec.aviso_mult(j),
                            'dañar_enemigo': lambda e, d, t, ef: recibir_ataque(e, {'tipo': t, 'daño': d, 'efecto': ef, 'retroceso': 0}),
                            'disparar': lambda x, y, dx, dy, d, t, v, dist, tam=16: nivel['proyectiles_enemigos'].append(crear_proyectil(x, y, dx, dy, round(d), False, t, v, dist, tam)),
                            'impacto': lambda x, y, r, ms: impacto(nivel, x, y, r, ms),
                            'parry': lambda e: intentar_parry(j, e, nivel),           # la IA lo llama antes de pegarte
                            'era': nivel['sala']['era'], 'proyectiles': nivel['proyectiles_pokemon'],
                            'forzar_cambio': lambda: forzar_cambio(j), 'quitar_objeto': lambda: quitar_objeto(j)}   # Llave Giro y Desarme de Arceus Beta
                entorno.actualizar(ent, dict(contexto, dañar_jugador=lambda d, t, a=None: dañar_jugador(j, d, t, evitable=False)), ahora)   # terreno, maquinas, fuego, clima, explosiones
                if ahora >= j['congelado_hasta']:                        # el frio de los golpes de hielo se va solo
                    if j['frio'] >= FRIO_MAX:
                        j['congelado_hasta'] = ahora + DURACION_CONGELADO; j['frio'] = 0.0
                        cartel(nivel, '¡Te congelaste! (un movimiento de fuego o lucha te descongela)', 1600)
                    j['frio'] = max(0.0, j['frio'] - DESCARGA_FRIO)
                for ev in ent['eventos']:                                # lo que paso en el entorno: monedas, cosas rotas, explosiones
                    if ev[0] == 'monedas' and not nivel['revisita']: soltar_monedas(nivel, j, ev[1], ev[2], ev[3])
                    elif ev[0] == 'roto':
                        efectos.romper(mundo['ef'], ev[1], ev[2], ev[3])
                        if not nivel['revisita']:                       # en salas repetidas no se farmea
                            ganar_xp(nivel, j, 1 + nivel['nivel_enemigos'] // 6)   # (antes daba el doble)
                            sorteo = random.random() / mec.mult_romper(j)   # explorar rinde: a veces adentro hay algo (Olfato: el doble)
                            mec.objeto_roto(j)
                            for clave, chance in PREMIO_ROMPER:
                                if sorteo < chance: soltar_objeto(nivel, ev[1], ev[2], clave); break
                                sorteo -= chance
                    elif ev[0] == 'explosion': efectos.explosion(mundo['ef'], ev[1], ev[2], ev[3])
                ent['eventos'] = []
                mec.cuadro(j, nivel)                                     # la mecanica de su linea (pasto, impulso, bajo tierra, bombas...)
                mec.nubes_enemigas(j, nivel)
                nivel['efectos'] = [x for x in nivel['efectos'] if ahora < x['hasta']]
                for proyectil in nivel['proyectiles_pokemon']: actualizar_proyectil_pokemon(proyectil, objetivos, solidos_p)
                nivel['proyectiles_pokemon'] = [proyectil for proyectil in nivel['proyectiles_pokemon'] if proyectil['activo']]
                contexto_ia = dict(contexto, enemigos=enemigos)
                for e in enemigos:
                    actualizar_estado(e)
                    if nivel['frame'] % 10 == e.get('id_desatasco', 0) and e['rect'].collidelist(entorno.solidos(ent, entorno.tipos_de(e))) != -1:
                        salida_e = entorno.orilla(ent, e['rect'], entorno.tipos_de(e))     # un enemigo trabado tambien sale
                        if salida_e: e['rect'].center = (round(salida_e[0]), round(salida_e[1]))
                    lento = mec.lento() and nivel['frame'] % 3                # camara lenta (Prediccion): un tercio de velocidad
                    if e['vida'] > 0 and not lento and not mec.enemigo(e, j, nivel): ia.actualizar(e, contexto_ia)
                    actualizar_animacion_enemigo(e)
                for e in enemigos:                                      # los que caen: monedas, experiencia y a veces quieren ser tus amigos
                    if e['vida'] <= 0:
                        soltar_monedas(nivel, j, *e['rect'].center, MONEDAS_ENEMIGO + nivel['sala']['era'])
                        baja(j, nivel)
                        efectos.aparecer(mundo['ef'], *e['rect'].center)    # la nube de humo de Poke Transfer
                        nivel['pausa_hasta'] = max(nivel.get('pausa_hasta', 0), ahora + IMPACTO['baja'])
                        ganar_xp(nivel, j, progreso.xp_por_derrota(e['nombre'], e['nivel'], j['nivel']))
                        efectos.romper(mundo['ef'], *e['rect'].center, e['color'])
                        quiza_amigo(nivel, j, e)
                        mec.derrota(j, e, nivel)
                nivel['enemigos'] = [e for e in enemigos if e['vida'] > 0 and not e.get('amigable')]
                for amigo_ in nivel.get('amigos', ()):
                    actualizar_animacion_enemigo(amigo_)
                    if nivel['frame'] % 45 == 0: efectos.corazones(mundo['ef'], *amigo_['rect'].center)
                if nivel['oleadas'] and not nivel['apariciones'] and len(nivel['enemigos']) <= 3:   # oleada nueva (sin dejar respirar): se marca donde salen
                    for _ in range(nivel['oleadas'].pop(0)):
                        nivel['apariciones'].append({'pos': entorno.punto_libre(ent, random, j['rect'].center, 320), 'hasta': ahora + 900})
                for a in nivel['apariciones'][:]:
                    if ahora >= a['hasta']:
                        nivel['enemigos'].append(crear_aparicion(nivel, a, j)); nivel['apariciones'].remove(a)
                        efectos.aparecer(mundo['ef'], *a['pos'])
                if jefe:
                    actualizar_estado(jefe)
                    actualizar_jefe(jefe, j, nivel['proyectiles_enemigos'], nivel['verdes'], contexto)
                    if jefe['vida'] > 0: invocaciones_jefe(nivel, j, jefe)
                    actualizar_animacion_enemigo(jefe)
                    if jefe['vida'] <= 0 and jefe['estilo'] == 'arceus' and nivel['tipo'] == 'final':
                        empezar_llegada_beta(nivel, j, jefe)
                    elif jefe['vida'] <= 0:
                        nivel['jefe'] = None
                        j['atrapado_hasta'] = 0
                        ia.salir_arena(j, ahora)
                        entorno.sacar_de_regi(ent)
                        if jefe['estilo'] == 'beta': entorno.cerrar_vacios(ent); cartel(nivel, 'El piso vuelve...', 2000)
                        soltar_monedas(nivel, j, *jefe['rect'].center, MONEDAS_REGI if nivel['tipo'] != 'jefe' else MONEDAS_JEFE)
                        cartel(nivel, jefe['nombre'].title() + ' fue derrotado!', 2000)
                        efectos.explosion(mundo['ef'], *jefe['rect'].center, 160)
                        ganar_xp(nivel, j, progreso.xp_por_derrota(jefe['nombre'], jefe['nivel'], j['nivel'], True))
                        premio_jefe(nivel, j, jefe)
                        if nivel['tipo'] == 'regi': abrir_portal(nivel); j['llave'] = True   # terminaste la era: Celebi abre el portal (no hace falta la llave)
                for proyectil in nivel['proyectiles_enemigos'] if not (mec.lento() and nivel['frame'] % 3) else ():
                    actualizar_proyectil(proyectil, j, solidos_p, nivel['proyectiles_pokemon'])
                nivel['proyectiles_enemigos'] = [proyectil for proyectil in nivel['proyectiles_enemigos'] if proyectil['activo']]
                for piedra_verde in nivel['verdes'][:]:
                    if ahora - piedra_verde['tiempo'] >= DURACION_PIEDRA: nivel['verdes'].remove(piedra_verde); continue
                    if j['rect'].colliderect(piedra_verde['rect']) and ahora-piedra_verde['daño'] >= 500: dañar_jugador(j, DAÑO_PIEDRA, evitable=False); piedra_verde['daño'] = ahora
                for moneda in nivel['monedas'][:]:                       # monedas: se juntan al pasar (y vienen solas cuando termina la sala)
                    dx, dy = j['rect'].centerx - moneda['x'], j['rect'].centery - moneda['y']
                    d = math.hypot(dx, dy)
                    if d < 40: j['monedas'] += moneda['valor']; nivel['monedas'].remove(moneda); continue
                    if nivel['completado'] or d < 110: moneda['x'] += dx / d * 9; moneda['y'] += dy / d * 9
                if nivel['llegada']: actualizar_llegada_beta(nivel, j)
                derrotados = not nivel['enemigos'] and nivel['jefe'] is None and not nivel['oleadas'] and not nivel['apariciones'] and not nivel['llegada']
                if derrotados and not nivel['completado']:
                    nivel['completado'] = True; nivel['registro']['completada'] = True
                    mec.sala_limpia(j, nivel)                            # Recogida
                    if nivel['tipo'] == 'combate' and not nivel.get('hubo_oferta'): amistad_de_era()['salas_sin'] += 1   # la proxima es un poco mas facil
                    if nivel.get('stats'):                               # la nota de la sala: tiempo, daño recibido, estilo y parrys
                        letra, detalle = nota_sala(nivel, j)
                        monedas_n, chance = NOTA_PREMIO[letra]
                        if nivel['registro'].get('desafio'): monedas_n, chance = monedas_n * 2 + 20, min(1.0, chance + DESAFIO['chance'])   # desafio: el doble
                        if monedas_n: soltar_monedas(nivel, j, *j['rect'].center, monedas_n * (nivel['sala']['era'] + 1))
                        if random.random() < chance: soltar_objeto(nivel, *j['rect'].center, random.choice(('baya_oran', 'llave_tesoro', 'caramelo_raro')))
                        if letra in ('S', 'A'): ganar_xp(nivel, j, progreso.xp_por_derrota(j['nombre'], nivel['nivel_enemigos'], j['nivel']) // (1 if letra == 'S' else 2))
                        cartel(nivel, 'Nota ' + letra, 2600, detalle, grande=True)
                    else: cartel(nivel, '¡Sala limpia!')
                    if any(p_.get('atras') for p_ in nivel['puertas']): cartel(nivel, 'Podés volver por donde entraste')
                    for i, m in enumerate(j['equipo']):                  # un respiro: los que siguen en pie recuperan un poco de vida
                        if i != j['activo'] and m['vida'] > 0: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] * CURA_SALA)
                    if j['vida'] > 0: j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * CURA_SALA)
                    nivel['guardar'] = True
                    soltar_monedas(nivel, j, *ESC.center, MONEDAS_SALA + 3 * nivel['sala']['era'])
                    ganar_xp(nivel, j, progreso.xp_por_derrota(j['nombre'], nivel['nivel_enemigos'], j['nivel']))
                    for i, m in enumerate(j['equipo']): m['amistad'] = min(255, m['amistad'] + (2 if i == j['activo'] else 1))   # pasar salas juntos
                if nivel['completado'] and nivel['llave'] is None and not j['llave']:
                    nivel['llave'] = pygame.Rect(ESC.centerx-15, ESC.centery-15, 30, 30)
                    efectos.destello(mundo['ef'], *ESC.center)
                if nivel['llave']:                                       # la llave de la sala vuela hacia vos (antes podia quedar en un lugar sin llegada)
                    llave = nivel['llave']
                    dx, dy = j['rect'].centerx - llave.centerx, j['rect'].centery - llave.centery
                    d = math.hypot(dx, dy)
                    if d > 1:
                        paso_l = min(d, 3 + d * 0.06)
                        llave.move_ip(round(dx / d * paso_l), round(dy / d * paso_l))
                if nivel['llave'] and j['rect'].inflate(10, 10).colliderect(nivel['llave']):
                    j['llave'] = True; nivel['llave'] = None
                    cartel(nivel, '¡Conseguiste la llave de la sala! Las puertas se abren')
                if j['vida'] <= 0:
                    guardar_activo(j)
                    vivos = [i for i, m in enumerate(j['equipo']) if m['vida'] > 0]
                    if not vivos: return 'muerte'
                    cambiar_slot(j, vivos[0], True)
                if nivel['saliendo']:                                   # saliendo: se cierra la pantalla y pasa a la sala de atras
                    if ahora >= nivel['saliendo']['hasta']: nivel['salida'] = nivel['saliendo']['puerta']; return 'siguiente'
                elif not j['llave'] and ahora >= nivel['entrando_hasta']:   # puertas cerradas: avisa por que no se abren
                    for puerta in nivel['puertas']:
                        if puerta.get('atras') or puerta.get('bloqueada') or not j['rect'].colliderect(puerta['rect'].inflate(20, 20)): continue
                        if ahora - puerta.get('aviso', -10000) > 1800:
                            cartel(nivel, 'Las puertas se abren con la llave de la sala' if nivel['completado'] else 'Primero limpiá la sala: al terminar aparece la llave', 1500)
                            puerta['aviso'] = ahora
                elif j['llave'] and ahora >= nivel['entrando_hasta']:
                    for puerta in nivel['puertas']:
                        tocando = j['rect'].colliderect(puerta['rect'].inflate(20, 20))
                        if not tocando: puerta['armada'] = True              # una puerta sirve recien cuando te alejaste de ella
                        if puerta.get('bloqueada') or (puerta.get('atras') and not nivel['completado']): continue
                        if tocando and puerta.get('armada') and puerta.get('destino', {}).get('candado'):   # puerta del tesoro: hace falta una llave
                            objetos = j['inventario']['objetos']
                            if objetos.get('llave_tesoro', 0) <= 0:
                                if ahora - puerta.get('aviso', -10000) > 1500: cartel(nivel, 'Necesitás una Llave del Tesoro (la vende Riolu)', 1400); puerta['aviso'] = ahora
                                continue
                            objetos['llave_tesoro'] -= 1; cartel(nivel, 'Usaste una Llave del Tesoro', 1200)
                            puerta['destino']['candado'] = False            # queda abierta (si volves, no pide otra llave)
                        if tocando and puerta.get('armada'):
                            cx, cy = camara(j)
                            nivel['saliendo'] = {'puerta': puerta, 'hasta': ahora + 320}
                            efectos.transicion(mundo['ef'], 'salir', ahora, (j['rect'].centerx - cx, j['rect'].centery - cy))
                            break

            return (menu_niveles, cartel, crear_nivel, tecla_de, hablar_amigo, vitrina_cercana, comprar_cercano, actualizar_nivel, bloque_cercano, empujar_bloque, hablar_portal, bailar,
                    soltar_monedas, soltar_objeto, hablar_curandera, curandera_cerca, usar_curacion, curarse_rapido, dar_pocion_maxima)

        (menu_niveles, cartel, crear_nivel, tecla_de, hablar_amigo, vitrina_cercana, comprar_cercano, actualizar_nivel, bloque_cercano, empujar_bloque,
         hablar_portal, bailar, soltar_monedas, soltar_objeto, hablar_curandera, curandera_cerca, usar_curacion, curarse_rapido, dar_pocion_maxima) = armar_salas()

        def armar_mecanicas():
            """Las mecanicas unicas de cada linea (mecanicas.py): le pasa lo que necesitan del juego."""
            def mover_entidad(o, dx, dy, libre=False):
                """Mueve a un enemigo (o al jugador) sin meterlo en paredes ni objetos (libre: bajo tierra, sin chocar)."""
                if libre: o['rect'].move_ip(dx, dy)
                else: entorno.mover(mundo['ent'], o['rect'], dx, dy, entorno.tipos_de(o))
                o['rect'].clamp_ip(AREA)

            def poner_buff(j, clave, valor, ms):
                j['buffs'][clave] = (valor, tiempo() + ms)

            def guardar_y_aplicar(j):
                j['vida'] = j['equipo'][j['activo']]['vida']; actualizar_sinergia(j)

            def rehacer_animador(ent, nombre=None):
                """Cambia los sprites (la Ilusion de Zorua, o un enemigo disfrazado que se revela)."""
                if ent is mundo.get('jugador') or 'equipo' in ent:
                    sprites = ent.get('disfraz') or ent['nombre']
                    ent['animador'] = AnimadorPokemon(sprites, ent['rect'], ent['juego']['tamaño'] if not ent.get('disfraz') else datos_juego(sprites)['tamaño'])
                else:
                    sprites = nombre or ent['nombre']
                    ent['animador'] = AnimadorPokemon(sprites, ent['rect'], max(34, min(70, datos_juego(sprites)['tamaño'] + 8)))

            def enemigos_de_era(nivel):
                return [n for n in mundos.ERAS[nivel['sala']['era']]['enemigos'] if n in pokemones]

            c = SimpleNamespace(tiempo=tiempo, mundo=mundo, cartel=cartel, efectos=efectos, entorno=entorno, recibir_ataque=recibir_ataque,
                                preparar=preparar, area_efecto=area_efecto, objetivos_de=objetivos_de, lanzar=lanzar, iniciar_embestida=iniciar_embestida,
                                punto_apuntado=punto_apuntado, curar_estados=curar_estados, poner_estado=poner_estado, esquive_perfecto=esquive_perfecto,
                                multiplicador_tipos=multiplicador_tipos, normalizar_tipo=normalizar_tipo, tipos_de=entorno.tipos_de,
                                clima=lambda: (mundo.get('ent') or {}).get('clima'),
                                terreno_bajo=lambda j: entorno.terreno_en(mundo['ent'], *j['rect'].center) if mundo.get('ent') else None,
                                hay_peligro=hay_peligro, cambiar_slot=cambiar_slot, soltar_objeto=soltar_objeto,
                                temblor=lambda nivel, ms: nivel.__setitem__('temblor', max(nivel['temblor'], tiempo() + ms)),
                                mover_entidad=mover_entidad, poner_buff=poner_buff, guardar_y_aplicar=guardar_y_aplicar, rehacer_animador=rehacer_animador,
                                enemigos_de_era=enemigos_de_era, golpe_al_jugador=golpe_al_jugador, ventana=ventana, ENERGIA_MAX=ENERGIA_MAX)
            return mecanicas.armar(c)

        mec = armar_mecanicas()

        def armar_hall():
            """El hall (como la casa de Hades): al caer todo el equipo Celebi te trae aca. El viaje se pierde, pero tus amigos se quedan:
            pasean por el hall, les hablas con E y elegis quienes van al proximo viaje. El portal del norte arranca otro viaje desde la Era Glacial.
            El perfil de la partida guarda tu nombre, tu genero, tus amigos, las eras que derrotaste y cuantos viajes hiciste."""
            DESCANSOS = ('idle', 'idle', 'sit', 'laying', 'lookup', 'sleep')       # lo que hacen tus amigos cuando se quedan quietos en el hall
            CHARLAS = ('¡{nombre}! ¿Salimos de nuevo?', 'La próxima llegamos más lejos, {nombre}. Te lo prometo.', 'Acá se está bien... pero me pica todo de ganas de pelear.',
                       'Celebi dice que el tiempo se rompe cada vez más. No entiendo mucho, pero suena feo.', 'Todavía sueño con la Era Glacial. Qué frío, por favor.',
                       'Si me llevás, esta vez no me desmayo. Bueno... lo intento.')
            SALUDOS_CELEBI = ('Otra vez por acá, {nombre}. Tranqui, a mí me costó bastante más aprender.',
                              'Vi caer imperios enteros, {nombre}. Una mala racha no es nada.',
                              '¿Ya de vuelta? Bueno, tiempo sobra. Acá es lo único que sobra.',
                              'Te saqué justo. La próxima, mirá bien los avisos antes de que te peguen.')

            def perfil_nuevo(nombre, genero):
                """El perfil de una partida nueva (despues del viaje temporal)."""
                return {'nombre': nombre, 'genero': genero, 'amigos': [], 'eras': 0, 'viajes': 0}

            def registrar_amigos(perfil, miembros):
                """Guarda (o actualiza) a estos pokemon en tus amigos: su forma base, IV, amistad, sinergia y hasta donde llegaron (record)."""
                for m in miembros:
                    a = next((x for x in perfil['amigos'] if x['id'] == m.get('id')), None)
                    if not a:
                        a = {'id': m['id'], 'especie': progreso.forma_base(m['nombre']), 'record': [m['nombre'], m['nivel']]}
                        perfil['amigos'].append(a)
                    a.update({'ivs': dict(m['ivs']), 'amistad': max(a.get('amistad', 0), m['amistad']), 'sinergia': m.get('sinergia'), 'naturaleza': m.get('naturaleza')})
                    if m['nivel'] >= a['record'][1]: a['record'] = [m['nombre'], m['nivel']]

            def miembro_de(a):
                """Un amigo listo para viajar: en su forma base y en el nivel del principio, con sus IV, su amistad y su sinergia."""
                m = crear_miembro(a['especie'], NIVEL_VIAJE)
                m.update({'id': a['id'], 'ivs': dict(a['ivs']), 'amistad': a.get('amistad', 0), 'sinergia': a.get('sinergia'), 'naturaleza': a.get('naturaleza') or m['naturaleza']})
                m['max_vida'] = m['vida'] = progreso.vida_max(m)
                return m

            def estilo_hall(perfil):
                """Que hall toca segun Ajustes > Hall: auto = donde aparece Celebi hasta que derrotes una era, despues el atemporal."""
                eleccion = config.get('hall', 'auto')
                if eleccion in ('atemporal', 'celebi'): return eleccion
                return 'atemporal' if perfil['eras'] > 0 else 'celebi'

            def residente(a, punto):
                """Un amigo que pasea por el hall (no esta en tu equipo): se anima como los enemigos pero no pelea."""
                nombre = a['especie']
                tipo = normalizar_tipo((pokemones[nombre].get('tipo') or ['normal'])[0])
                r = pygame.Rect(0, 0, 44, 44); r.center = punto
                return {'a': a, 'nombre': nombre, 'rect': r, 'prev': r.center, 'direccion': 'sur', 'color': COLORES_TIPO.get(tipo, (150, 150, 150)),
                        'animador': AnimadorPokemon(nombre, r, max(34, min(70, datos_juego(nombre)['tamaño'] + 8))),
                        'destino': None, 'quieto_hasta': tiempo() + random.randint(500, 3000), 'pose': None, 'pose_hasta': 0}

            def pisables_hall(sala):
                """Centros de las casillas del hall donde se puede caminar (sin objetos, sin agua ni vacio)."""
                tam, m = sala['tam'], sala['matriz']
                tapadas = {c for o in sala['objetos'] for c in o['celdas']}
                return [((c + 0.5) * tam, (f + 0.5) * tam) for f in range(2, len(m) - 1) for c in range(1, len(m[0]) - 1)
                        if m[f][c] in ('suelo', 'hierba') and (f, c) not in tapadas]

            def crear_hall(j, perfil):
                """Arma el hall como una sala mas (sin enemigos, con la puerta abierta): Celebi al lado del portal y tus amigos paseando."""
                estilo = estilo_hall(perfil)
                era = 1 if estilo == 'celebi' else min(perfil['eras'], len(mundos.ERAS) - 1)   # el atemporal tiene el piso de la ultima era a la que llegaste
                sala = generacion.generar_hall(era, estilo, random.random())
                for puerta in sala['puertas']: puerta['destino'] = {'tipo': 'viaje'}
                ESC.size = sala['esc'].size
                AREA.update(generacion.crear_area(ESC, sala['tam']))
                ent = entorno.crear(sala, None, tiempo())
                mundo['ent'] = ent
                nivel = {'sala': sala, 'ent': ent, 'tipo': 'hall', 'escala': mundos.escala(0, 0), 'enemigos': [], 'jefe': None, 'proyectiles_pokemon': [],
                         'proyectiles_enemigos': [], 'efectos': [], 'verdes': [], 'puertas': sala['puertas'], 'llave': None, 'completado': True, 'monedas': [],
                         'carteles': [], 'oleadas': [], 'apariciones': [], 'vitrinas': [], 'salida': None, 'nivel_enemigos': 1, 'amigos': [],
                         'entrando_hasta': tiempo() + DURACION_ENTRADA, 'saliendo': None, 'frame': 0, 'temblor': 0, 'llegada': None,
                         'registro': {'completada': True, 'salida': None}, 'revisita': True, 'inicio': sala['inicio'], 'pisables': pisables_hall(sala)}
                en_equipo = {m.get('id') for m in j['equipo']}
                libres = random.sample(nivel['pisables'], min(len(nivel['pisables']), len(perfil['amigos'])))
                nivel['residentes'] = [residente(a, p) for a, p in zip([a for a in perfil['amigos'] if a['id'] not in en_equipo], libres)]
                mundo['ef']['parts'], mundo['ef']['anims'] = [], []
                mundo['nivel'] = nivel
                titulo = 'Claro de Celebi' if estilo == 'celebi' else 'El lugar atemporal'
                cartel(nivel, titulo, 2800, 'Hall  -  ' + str(len(perfil['amigos'])) + (' amigo' if len(perfil['amigos']) == 1 else ' amigos') + '  -  viaje ' + str(perfil['viajes'] + 1), grande=True)
                return nivel

            def actualizar_residentes(nivel):
                """Tus amigos pasean: eligen un lugar, caminan (Walk) y al llegar descansan un rato (Sit, Laying, LookUp, Sleep o quietos)."""
                ahora = tiempo()
                for r in nivel.get('residentes', ()):
                    a = r['animador']
                    if ahora < r['pose_hasta'] and r['pose']:              # asintiendo, saltando de alegria o descansando
                        if not a.cambiar(r['pose'], direcciones.index(r['direccion']), r['pose'] in DESCANSOS): a.cambiar('idle', direcciones.index(r['direccion']), True)
                        a.actualizar(); r['prev'] = r['rect'].center; continue
                    if r['destino']:
                        dx, dy = r['destino'][0] - r['rect'].centerx, r['destino'][1] - r['rect'].centery
                        d = math.hypot(dx, dy)
                        if d <= VEL_RESIDENTE:
                            r['rect'].center = (round(r['destino'][0]), round(r['destino'][1])); r['destino'] = None
                            r['pose'] = random.choice(DESCANSOS); r['pose_hasta'] = r['quieto_hasta'] = ahora + random.randint(2500, 7000)
                        else:
                            r['resto'] = r.get('resto', [0.0, 0.0])
                            r['resto'][0] += dx / d * VEL_RESIDENTE; r['resto'][1] += dy / d * VEL_RESIDENTE
                            mx, my = int(r['resto'][0]), int(r['resto'][1])
                            r['rect'].x += mx; r['rect'].y += my; r['resto'][0] -= mx; r['resto'][1] -= my
                    elif ahora >= r['quieto_hasta'] and nivel['pisables']:
                        r['destino'] = random.choice(nivel['pisables']); r['pose'] = None
                    actualizar_animacion_enemigo(r)

            def posar(r, pose, ms):
                """Un amigo del hall hace una animacion un rato (Nod al hablarle, Hop cuando viene al viaje)."""
                r['pose'], r['pose_hasta'], r['destino'] = pose, tiempo() + ms, None
                r['quieto_hasta'] = tiempo() + ms + 800
                a = r['animador']
                if a.cambiar(pose, direcciones.index(r['direccion']), False): a.indice_frame = 0; a.acumulado = 0.0; a.terminada = False   # desde el principio aunque ya la estuviera haciendo

            def cerca(j, punto, distancia=DISTANCIA_HABLAR):
                return math.hypot(punto[0] - j['rect'].centerx, punto[1] - j['rect'].centery) <= distancia

            def hablar_hall(nivel, j, perfil):
                """E en el hall: hablar con Celebi o con un amigo. Devuelve True si habia alguien cerca."""
                if nivel['tipo'] != 'hall': return False
                g = perfil['genero']
                if cerca(j, nivel['sala']['guardian'], DISTANCIA_HABLAR + 20):
                    if perfil['viajes'] <= 1: texto = 'Te saqué justo, ' + perfil['nombre'] + '. Acá no te alcanza nada, ' + menus.segun_genero(g, 'quedate tranquilo', 'quedate tranquila', 'tranqui') + '.'
                    else: texto = random.choice(SALUDOS_CELEBI).format(nombre=perfil['nombre'])
                    r = pausado(menus.preguntar, ui, texto, ['¿Qué es este lugar?', '¿Cómo venimos?', 'Nada, gracias'])
                    if r == 0: pausado(menus.preguntar, ui, 'Un rincón fuera del tiempo. Lo encontré hace... uf, ni me acuerdo. Tus amigos esperan acá: hablales y elegí quién viaja con vos.',
                                       ['Dale'], 'el portal del norte te lleva de nuevo a la Era Glacial')
                    if r == 1: pausado(menus.preguntar, ui, str(perfil['viajes']) + ' viajes, ' + str(perfil['eras']) + ' eras derrotadas y ' + str(len(perfil['amigos'])) + ' amigos. Vas mejor de lo que pensás.',
                                       ['Vamos de nuevo'])
                    return True
                r = min(nivel.get('residentes', ()), key=lambda r: math.hypot(r['rect'].centerx - j['rect'].centerx, r['rect'].centery - j['rect'].centery), default=None)
                if not r or not cerca(j, r['rect'].center): return False
                posar(r, 'nod', 900)
                a, nombre = r['a'], r['nombre'].replace('_', ' ').title()
                record = a['record'][0].replace('_', ' ').title() + ' Nv ' + str(a['record'][1])
                eleccion = pausado(menus.preguntar, ui, nombre + ': ' + random.choice(CHARLAS).format(nombre=perfil['nombre']),
                                   ['¡Vení al próximo viaje!', 'Después hablamos'],
                                   'mejor viaje: ' + record + '  -  amistad ' + str(a.get('amistad', 0)) + '  -  ' + progreso.texto_naturaleza(a.get('naturaleza')).split(' - ')[0])
                if eleccion != 0: return True
                if len(j['equipo']) < 3: j['equipo'].append(miembro_de(a))
                else:                                                      # equipo lleno: cambia por uno que no este peleando
                    opciones_ = [i for i in range(len(j['equipo'])) if i != j['activo']]
                    k = pausado(menus.preguntar, ui, '¿Por quien lo cambias?', [j['equipo'][i]['nombre'].title() for i in opciones_] + ['Cancelar'])
                    if k is None or k == 'salir' or k >= len(opciones_): return True
                    sale = j['equipo'][opciones_[k]]
                    j['equipo'][opciones_[k]] = miembro_de(a)
                    otro = next((x for x in perfil['amigos'] if x['id'] == sale.get('id')), None)
                    if otro: nivel['residentes'].append(residente(otro, j['rect'].center))
                nivel['residentes'].remove(r)
                actualizar_sinergia(j)
                efectos.corazones(mundo['ef'], *r['rect'].center)
                cartel(nivel, '¡' + nombre + ' viene al próximo viaje!')
                return True

            def volver_al_hall(j, perfil):
                """Cayo todo el equipo: el viaje se pierde. Tus amigos (equipo y reserva) quedan en el perfil y vuelven al hall en su forma base."""
                guardar_activo(j)
                registrar_amigos(perfil, j['equipo'] + j['reserva'])
                perfil['viajes'] += 1
                nuevo = crear_jugador([progreso.forma_base(j['equipo'][0]['nombre'])], ESC.center, config['modo'])
                nuevo['equipo'] = [miembro_de(a) for m in j['equipo'] for a in perfil['amigos'] if a['id'] == m.get('id')][:3] or nuevo['equipo']
                nuevo['activo'] = 0
                aplicar_pokemon(nuevo, nuevo['equipo'][0]['nombre'])
                actualizar_sinergia(nuevo)
                return nuevo

            def caida(nivel, j, rec):
                """Cayo todo el equipo: el ultimo se desmaya (Faint, o Hurt si no tiene), la pantalla se oscurece y Celebi te va a buscar.
                Devuelve 'salir' si se cerro la ventana."""
                a = j['animador']
                d = direcciones.index(j['direccion']) if j['direccion'] in direcciones else 0
                if not a.cambiar('faint', d, False): a.cambiar('hurt', d, False)
                reloj_c = pygame.time.Clock()
                f_g, f_c = tipografia.fuente_titulo(3), tipografia.fuente(30)   # la letra del juego (antes era la de pygame)
                quieta = None
                for k in range(170):
                    for e in controles.eventos():
                        if e.type == pygame.QUIT: return 'salir'
                    if k < 75:                                                # se ve como se desmaya
                        a.actualizar(); dibujar_objetos(nivel, j, rec)
                    else:                                                     # se oscurece y aparece el mensaje
                        if quieta is None: quieta = ventana.copy()
                        ventana.blit(quieta, (0, 0))
                        velo = pygame.Surface((W, H)); velo.set_alpha(min(255, (k - 75) * 6)); ventana.blit(velo, (0, 0))
                        if k > 105:
                            t = f_g.render('Cayó todo tu equipo...', True, 'white'); ventana.blit(t, t.get_rect(center=(W // 2, H // 2 - 34)))
                        if k > 130:
                            t = f_c.render('Celebi te sacó de ahí a tiempo', True, (150, 240, 140)); ventana.blit(t, t.get_rect(center=(W // 2, H // 2 + 34)))
                        pantalla.presentar()
                    reloj_c.tick(60)
                return None

            def empezar_viaje(j):
                """Cruzaste el portal: el equipo arranca con la vida llena (ya esta en su forma base y en el nivel del principio)."""
                for m in j['equipo']: m['vida'] = m['max_vida'] = progreso.vida_max(m)
                j['activo'] = 0; j['monedas'] = 0; j['inventario'] = tienda.inventario_nuevo(); j['reserva'] = []
                for m in j['equipo']: curar_estados(m)
                dar_pocion_maxima(j)                                     # Celebi te despide con una Pocion Maxima
                aplicar_pokemon(j, j['equipo'][0]['nombre'])
                actualizar_sinergia(j)

            return perfil_nuevo, registrar_amigos, crear_hall, actualizar_residentes, hablar_hall, volver_al_hall, caida, empezar_viaje

        perfil_nuevo, registrar_amigos, crear_hall, actualizar_residentes, hablar_hall, volver_al_hall, caida, empezar_viaje = armar_hall()

        def armar_dibujo():
            """Todo lo que se dibuja jugando: jugador, HUD, indicadores, carteles, tienda y objetos."""
            def dibujar_rect(rect, cx, cy, color, forma='rect'):
                """Rectangulo (o elipse) del mundo dibujado en la pantalla segun la camara."""
                r = pygame.Rect(rect.x-cx, rect.y-cy, rect.width, rect.height)
                (pygame.draw.ellipse if forma == 'ellipse' else pygame.draw.rect)(ventana, color, r)

            def dibujar_jugador(j, cx, cy):
                """Dibuja al pokemon activo (un cuadrado rosa si no tiene sprites)."""
                centro = j['rect'].center
                if mec.invisible(j):                                     # bajo tierra: solo se ve la tierra que se mueve
                    pygame.draw.ellipse(ventana, (110, 80, 50), (centro[0] - cx - 18, centro[1] - cy - 4, 36, 14))
                    if (tiempo() // 120) % 2: efectos.polvo(mundo['ef'], *centro)
                    return
                alto_v = mec.altura_vuelo(j)                             # volando: el sprite sube y queda la sombra abajo
                if alto_v: pygame.draw.ellipse(ventana, (20, 20, 20), (centro[0] - cx - 16, centro[1] - cy + 8, 32, 10))
                j['rect'].center = centro[0]-cx, centro[1]-cy - alto_v
                ok = j['animador'].dibujar(ventana); j['rect'].center = centro
                activos = [e for e in ESTADOS_J if tiene_estado(j, e)]             # estados: iconos de BW arriba de la cabeza
                for k_, e in enumerate(activos):
                    menus.icono_estado(ventana, {'veneno': 'veneno', 'quemadura': 'quemar', 'paralisis': 'paralizar', 'sueño': 'dormir'}.get(e, e),
                                       (centro[0] - cx - (len(activos) - 1) * 18 + k_ * 36, j['rect'].top - cy - 14))
                if ok: return
                r = pygame.Rect(0,0,j['tamaño'],j['tamaño']); r.center = centro[0]-cx, centro[1]-cy; pygame.draw.rect(ventana, (255,50,255), r)

            def dibujar_congelado(j, cx, cy):
                """Si el jugador esta congelado, un bloque de hielo encima."""
                if tiempo() >= j['congelado_hasta']: return
                r = j['rect'].inflate(18, 18).move(-cx, -cy)
                ventana.blit(entorno._velo(r.size, (170, 225, 255, 130)), r)   # velo celeste (se arma una vez y se reusa)
                pygame.draw.rect(ventana, (230, 250, 255), r, 3)

            def barra(rect, vida, max_vida, alto=5):
                """Barrita de vida de BW arriba de un enemigo."""
                menus.barra_vida(ventana, (rect[0], rect[1] - 1, rect[2], rect[3] + 2), vida / max(1, max_vida), False)   # barra de BW

            retratos = {}

            f_hud, f_hud_g, f_hud_b = tipografia.fuente(20), tipografia.fuente(26), tipografia.fuente(30)

            f_hud_b.set_bold(True)

            f_tipo = tipografia.fuente(18)
            f_cartel, f_cartel_sub = tipografia.fuente_titulo(3), tipografia.fuente(28)   # carteles grandes: la letra de los pisos del PMD
            _textos = {}

            def render(f, texto, color):
                """Texto ya renderizado: el HUD dibuja los mismos textos cada frame, asi se hace una sola vez."""
                clave = (id(f), texto, str(color))
                if clave not in _textos:
                    if len(_textos) > 600: _textos.clear()            # los numeros que cambian (vida, segundos) no se acumulan para siempre
                    _textos[clave] = f.render(texto, True, color)
                return _textos[clave]

            def retrato(nombre, radio):
                """Retrato redondo de un pokemon (recortado en circulo y guardado)."""
                clave = (nombre, radio)
                if clave not in retratos:
                    img = cargar_retrato(nombre)
                    if img:
                        img = pygame.transform.smoothscale(img, (radio * 2, radio * 2))
                        mascara = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                        pygame.draw.circle(mascara, (255, 255, 255, 255), (radio, radio), radio)
                        img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                    retratos[clave] = img
                return retratos[clave]

            _sombras = {}

            def sombra_circular(radio, alfa):
                """Circulo negro semitransparente (pokemon en espera, especial recargando), armado una vez por tamaño."""
                if (radio, alfa) not in _sombras:
                    _sombras[(radio, alfa)] = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                    pygame.draw.circle(_sombras[(radio, alfa)], (0, 0, 0, alfa), (radio, radio), radio)
                return _sombras[(radio, alfa)]

            def circulo_poke(centro, radio, nombre, atenuado=False):
                """Circulo blanco con la cara del pokemon (o sus iniciales); oscurecido si esta esperando o debilitado."""
                pygame.draw.circle(ventana, 'white', centro, radio)
                img = retrato(nombre, radio - 3)
                if img: ventana.blit(img, (centro[0] - radio + 3, centro[1] - radio + 3))
                else:
                    t = render(f_hud_g, nombre[:2].title(), 'black')
                    ventana.blit(t, t.get_rect(center=centro))
                pygame.draw.circle(ventana, 'black', centro, radio, 3)
                if atenuado: ventana.blit(sombra_circular(radio, 150), (centro[0] - radio, centro[1] - radio))

            def con_sombra(f, texto, color, pos):
                """Texto claro con sombra oscura: se lee sobre cualquier piso."""
                ventana.blit(render(f, texto, (20, 20, 30)), (pos[0] + 2, pos[1] + 2))
                t = render(f, texto, color); ventana.blit(t, pos)
                return t

            def barra_hud(rect, vida, max_vida):
                """Barra de vida grande del HUD (la de BW con el HP verde)."""
                menus.barra_vida(ventana, rect, max(0, vida) / max(1, max_vida))   # barra de vida de BW con el HP verde

            f_borde, f_borde2 = tipografia.fuente(20, borde=True), tipografia.fuente(40, borde=True)   # letra de DS con borde: se lee sobre cualquier piso

            def cortar(f, texto, ancho):
                """El texto recortado con '…' para que entre en 'ancho' pixeles."""
                if f.size(texto)[0] <= ancho: return texto
                while texto and f.size(texto + '…')[0] > ancho: texto = texto[:-1]
                return texto + '…'

            MINIMAPA = {'casilla': 8, 'ancho': 180, 'alto': 130, 'alfa': 215, 'cada': 30}   # el mapa de arriba a la derecha (piezas del PMD)
            _mini = {'piezas': {}, 'nivel': None, 'fondo': None, 'cuadro': -999}

            def pieza_mini(nombre, escala=1):
                """Una pieza de assets/interfaz/minimapa (la recorta: python herramientas.py minimapa), agrandada. None si falta."""
                clave = (nombre, escala)
                if clave not in _mini['piezas']:
                    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'interfaz', 'minimapa', nombre + '.png')
                    try: img = pygame.image.load(ruta).convert_alpha() if os.path.isfile(ruta) else None
                    except pygame.error: img = None
                    _mini['piezas'][clave] = pygame.transform.scale(img, (img.get_width() * escala, img.get_height() * escala)) if img else None
                return _mini['piezas'][clave]

            def fondo_minimapa(nivel, c):
                """El piso de la sala con la trama azul del PMD y los bordes blancos donde termina (paredes, vacio, objetos que no se pisan)."""
                m = nivel['ent']['m']
                filas, columnas = len(m), len(m[0])
                sup = pygame.Surface((columnas * c, filas * c), pygame.SRCALPHA)
                relleno = pieza_mini('relleno', c // 4 or 1)
                borde_h, borde_v = pieza_mini('borde_h', c // 4 or 1), pieza_mini('borde_v', c // 4 or 1)
                if not (relleno and borde_h and borde_v): return None
                def piso(f, col):
                    if not (0 <= f < filas and 0 <= col < columnas): return False
                    t = m[f][col]
                    return t not in ('pared', 'vacio', 'puerta', 'entrada') and not mundos.TERRENOS.get(t, {}).get('solido')
                for f in range(filas):
                    for col in range(columnas):
                        if not piso(f, col): continue
                        x, y = col * c, f * c
                        sup.blit(relleno, (x, y), (0, 0, c, c))
                        if not piso(f - 1, col): sup.blit(borde_h, (x, y), (0, 0, c, borde_h.get_height()))
                        if not piso(f + 1, col): sup.blit(borde_h, (x, y + c - borde_h.get_height()), (0, 0, c, borde_h.get_height()))
                        if not piso(f, col - 1): sup.blit(borde_v, (x, y), (0, 0, borde_v.get_width(), c))
                        if not piso(f, col + 1): sup.blit(borde_v, (x + c - borde_v.get_width(), y), (0, 0, borde_v.get_width(), c))
                return sup

            def dibujar_minimapa(nivel, j, derecha, arriba):
                """Minimapa como el de la pantalla de arriba del Mystery Dungeon: el piso de la sala, las puertas (escaleras), la llave
                (baldosa), los objetos del piso, los que quieren ser tus amigos, los enemigos, el jefe (outlaw), el portal y vos (titila).
                Solo en salas de pelea (la tienda, el tesoro y el hall no lo necesitan). (derecha, arriba) es la esquina del mapa;
                devuelve el rect del panel dibujado (o None si no hay mapa)."""
                if nivel['tipo'] in ('tienda', 'tesoro', 'hall') or not nivel.get('ent'): return None
                m = nivel['ent']['m']
                c = max(4, min(MINIMAPA['casilla'], MINIMAPA['ancho'] // len(m[0]), MINIMAPA['alto'] // len(m)))
                c -= c % 4                                                # las piezas son de 4 px: escala entera
                if _mini['nivel'] is not nivel or nivel['frame'] - _mini['cuadro'] >= MINIMAPA['cada']:   # el piso cambia (hielo que se derrite...)
                    _mini.update({'nivel': nivel, 'fondo': fondo_minimapa(nivel, c), 'cuadro': nivel['frame']})
                fondo_m = _mini['fondo']
                if fondo_m is None: return None
                capa = fondo_m.copy()
                tam = nivel['sala']['tam']
                esc = c // 4 or 1
                def icono(nombre, pos):
                    img = pieza_mini(nombre, esc)
                    if img: capa.blit(img, img.get_rect(center=(round(pos[0] / tam * c), round(pos[1] / tam * c))))
                for puerta in nivel['puertas']:
                    if puerta.get('bloqueada') or (puerta.get('atras') and not nivel['completado']): continue
                    icono('escalera' if j['llave'] else 'trampa', puerta['rect'].center)
                if nivel.get('llave'): icono('baldosa', nivel['llave'].center)
                for r in nivel.get('recogibles', ()): icono('objeto', (r['x'], r['y']))
                for e in nivel.get('amigos', ()): icono('compañero', e['rect'].center)
                for e in nivel['enemigos']:
                    if e['vida'] > 0: icono('enemigo', e['rect'].center)
                if nivel['jefe'] and nivel['jefe']['vida'] > 0: icono('jefe', nivel['jefe']['rect'].center)
                if nivel.get('portal'): icono('portal', nivel['portal']['pos'])
                icono('yo' if (tiempo() // 300) % 2 else 'yo_claro', j['rect'].center)
                lugar_m = capa.get_rect(topright=(derecha, arriba))
                marco = lugar_m.inflate(14, 14)                              # el panel de BW atras, para que se lea sobre cualquier piso
                panel_m = pygame.Surface(marco.size, pygame.SRCALPHA)
                menus.caja(panel_m, panel_m.get_rect(), 'panel', (20, 20, 30))
                panel_m.set_alpha(215)
                ventana.blit(panel_m, marco)
                capa.set_alpha(MINIMAPA['alfa'])
                ventana.blit(capa, lugar_m)
                return marco

            CINTURON_HUD = {'radio': 168, 'alfa': 165, 'anillo': 120, 'hueco': 17, 'desde': 192, 'hasta': 258}   # el cuarto de circulo (centro en la esquina)
            ATAQUES_HUD = {'radio': 248, 'boton': 24, 'desde': 192, 'hasta': 262}                                # el arco de los 6 ataques
            _tela = {}

            def tela_cinturon():
                """El cuarto de circulo marron medio transparente, como la tela de un mostrador (con flecos y una costura). Se arma una vez."""
                if 'sup' not in _tela:
                    R = CINTURON_HUD['radio']
                    sup = pygame.Surface((R + 8, R + 8), pygame.SRCALPHA)
                    esquina = (R + 8, R + 8)
                    pygame.draw.circle(sup, (120, 78, 44, CINTURON_HUD['alfa']), esquina, R)
                    pygame.draw.circle(sup, (92, 58, 32, CINTURON_HUD['alfa']), esquina, R, 6)
                    for k in range(0, 91, 6):                             # flecos en el borde
                        ang = math.radians(180 + k)
                        x, y = esquina[0] + (R + 3) * math.cos(ang), esquina[1] + (R + 3) * math.sin(ang)
                        pygame.draw.circle(sup, (92, 58, 32, CINTURON_HUD['alfa']), (round(x), round(y)), 3)
                    for k in range(0, 90, 4):                             # costura punteada
                        ang = math.radians(180 + k + 1)
                        x, y = esquina[0] + (R - 16) * math.cos(ang), esquina[1] + (R - 16) * math.sin(ang)
                        pygame.draw.circle(sup, (230, 200, 150, 150), (round(x), round(y)), 1)
                    _tela['sup'] = sup
                return _tela['sup']

            def lugares_cinturon():
                """Centros de los 5 circulos del cinturon (del 1 abajo a la izquierda al 5 arriba a la derecha)."""
                c = CINTURON_HUD
                return [(round(W + c['anillo'] * math.cos(math.radians(c['desde'] + (c['hasta'] - c['desde']) * i / 4))),
                         round(H + c['anillo'] * math.sin(math.radians(c['desde'] + (c['hasta'] - c['desde']) * i / 4)))) for i in range(5)]

            def dibujar_cinturon(j, ahora):
                """Abajo a la derecha: la tela marron y adentro las 5 curaciones (circulos negros con el numero del orden en que se usan con
                la tecla de curarse). La primera, que es la que sale, tiene el borde dorado."""
                tela = tela_cinturon()
                ventana.blit(tela, tela.get_rect(bottomright=(W, H)))
                cinturon = j['inventario'].get('cinturon', [])
                usado = ahora - j.get('cinturon_usado', -10000) < 250       # al usar una: el lugar 1 destella
                for i, centro in enumerate(lugares_cinturon()):
                    r = CINTURON_HUD['hueco']
                    pygame.draw.circle(ventana, (12, 12, 14), centro, r)
                    clave = cinturon[i] if i < len(cinturon) else None
                    if clave:
                        icono = menus.icono_objeto(clave, 24)
                        if icono: ventana.blit(icono, icono.get_rect(center=centro))
                        else: pygame.draw.circle(ventana, tienda.ITEMS[clave]['color'], centro, r - 7)
                    borde = (255, 215, 90) if i == 0 and clave else (90, 70, 50)
                    pygame.draw.circle(ventana, (255, 255, 255) if i == 0 and usado else borde, centro, r, 2)
                    n = render(f_borde, str(i + 1), 'white' if clave else (190, 170, 150))   # el numero, del lado de la esquina
                    k_n = (CINTURON_HUD['anillo'] - r - 10) / CINTURON_HUD['anillo']
                    ventana.blit(n, n.get_rect(center=(round(W + (centro[0] - W) * k_n), round(H + (centro[1] - H) * k_n))))
                t = render(f_borde2, tecla_de('curar'), (255, 230, 150))  # la tecla, en la esquina
                ventana.blit(t, t.get_rect(center=(W - 30, H - 28)))
                if cinturon and ahora < j.get('curar_listo', 0):          # espera corta despues de usar una
                    menus.barra_exp(ventana, W - 60, H - 8, 50, (j['curar_listo'] - ahora) / max(1, CURAR_ESPERA), (255, 215, 90))

            def dibujar_ataques(j, ahora, congelado):
                """Alrededor del cuarto de circulo: E, Q, Shift y R (los 4 movimientos) y F y G (las asistencias de la banca), en botones
                de la pantalla tactil de BW con el nombre abajo. La espera se cierra como un abanico."""
                c = ATAQUES_HUD
                banca = [m for i, m in enumerate(j['equipo']) if i != j['activo']]
                botones = [('E', j['juego']['basicos'][0], 0), ('Q', j['juego']['basicos'][1], 1),
                           ('Shift', j['juego']['especiales'][0][0], 2), ('R', j['juego']['especiales'][1][0], 3),
                           ('F', banca[0] if len(banca) > 0 else None, 4), ('G', banca[1] if len(banca) > 1 else None, 5)]
                for k, (tecla, cosa, n) in enumerate(botones):
                    ang = math.radians(c['desde'] + (c['hasta'] - c['desde']) * k / (len(botones) - 1))
                    cx, cy = round(W + c['radio'] * math.cos(ang)), round(H + c['radio'] * math.sin(ang))
                    radio = c['boton']
                    restante, k_espera, apagado = 0, 0.0, ocupado(j) or congelado
                    if n >= 4:                                            # asistencias: las tira el de la banca
                        m = cosa
                        if m is None:
                            menus.boton_tactil(ventana, (cx, cy), radio, 0.0, None, True)
                            nombre = '-'
                        else:
                            restante = max(0, m['asist_listo'] - ahora)
                            k_espera = min(1.0, restante / max(1, m['asist']['enfriamiento']))
                            apagado = apagado or m['vida'] <= 0 or ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO
                            acento = COLORES_TIPO.get(normalizar_tipo((pokemones[m['nombre']].get('tipo') or ['normal'])[0]))
                            menus.boton_tactil(ventana, (cx, cy), radio, k_espera, acento, apagado)
                            nombre = m['asist']['nombre'].replace('_', ' ').title()
                    else:
                        mov = cosa
                        datos_m = j['juego']['especiales'][n - 2][1] if n >= 2 else (datos_mov(mov) or {})
                        if n >= 2:
                            enfriamiento = max(1, enfriamiento_de(j, datos_m))
                            restante = max(0, enfriamiento - (ahora - j['esp_ultimo'][n - 2])); k_espera = restante / enfriamiento
                        elif n == 1:
                            espera = enfriamiento_de(j, dict(datos_m, enfriamiento=float(datos_m.get('enfriamiento', 800)) * BASICO_DISTANCIA['enfriamiento']))
                            restante = max(0, espera - (ahora - j['ultimo_proyectil'])); k_espera = restante / max(1, espera)
                        acento = COLORES_TIPO.get(normalizar_tipo(datos_m.get('tipo') or (j['tipos'][0] if j['tipos'] else 'normal')))
                        menus.boton_tactil(ventana, (cx, cy), radio, k_espera, acento, apagado)
                        if n == 0 and j.get('combo') and ahora - j.get('ultimo_golpe', -10000) <= COMBO['ventana']:   # combo en curso
                            pygame.draw.arc(ventana, (255, 210, 60), (cx - radio - 3, cy - radio - 3, radio * 2 + 6, radio * 2 + 6), math.pi / 2, math.pi / 2 + math.tau * j['combo'] / 3, 4)
                        nombre = nombre_mov(mov)
                    lento = restante > 0 and (n >= 2)
                    t = render(f_borde2 if len(tecla) == 1 else f_borde, tecla, 'white')
                    ventana.blit(t, t.get_rect(center=(cx, cy - (6 if lento else 0))))
                    if lento:
                        sg = render(f_borde, str(round(restante / 1000, 1)) if restante < 10000 else str(restante // 1000), (255, 230, 120))
                        ventana.blit(sg, sg.get_rect(center=(cx, cy + 11)))
                    nombre_t = render(f_borde, cortar(f_borde, nombre, 66), 'white')
                    lugar_n = nombre_t.get_rect(midtop=(cx, cy + radio - 1))
                    lugar_n.right = min(lugar_n.right, W - 2)
                    ventana.blit(nombre_t, lugar_n)

            def dibujar_estilo(j, xe, ye, ahora):
                """El estilo (la letra de D a S, la barra hasta la proxima y la racha), con el centro en (xe, ye)."""
                est = j['estilo']
                letra, minimo, mult, color = ESTILO['rangos'][est['rango']]
                siguiente = ESTILO['rangos'][est['rango'] + 1][1] if est['rango'] + 1 < len(ESTILO['rangos']) else ESTILO['maximo']
                salto = 1 if ahora - est['subio'] < 160 else 0               # al subir de rango la letra salta un tamaño
                letra_t = tipografia.fuente(20, borde=True, escala=4 + salto).render(letra, True, color)
                ventana.blit(letra_t, letra_t.get_rect(center=(xe, ye)))
                ventana.blit(render(f_borde, 'ESTILO', 'white'), render(f_borde, 'ESTILO', 'white').get_rect(midbottom=(xe, ye - 22)))
                menus.barra_exp(ventana, xe - 97, ye + 26, 194, (est['puntos'] - minimo) / max(1, siguiente - minimo), color)
                y_est = ye + 36                                               # lo de abajo se apila: nada se pisa
                if mult > 1:
                    bonus = render(f_borde, 'daño +' + str(round((mult - 1) * 100)) + '%', color)
                    ventana.blit(bonus, bonus.get_rect(midtop=(xe, y_est))); y_est += bonus.get_height() + 2
                if est['racha'] >= 2 and ahora - est['ultima_baja'] <= ESTILO['racha_ms']:
                    racha = render(f_borde2, 'x' + str(est['racha']), (255, 230, 120))
                    ventana.blit(racha, racha.get_rect(midtop=(xe, y_est))); y_est += racha.get_height() + 2
                if est['repite'] >= 3 and ahora - est['actividad'] < 1500:   # spameando lo mismo: aviso chiquito
                    variar = render(f_borde, 'variá tus ataques', (255, 160, 140))
                    ventana.blit(variar, variar.get_rect(midtop=(xe, y_est)))

            def dibujar_hud(j, nivel, rec):
                """HUD como el combate de BW: arriba a la izquierda tu pokemon (barra de HP con la placa, experiencia y energia), la banca en
                paneles en flecha, abajo a la derecha los 4 movimientos en botones de la pantalla tactil y arriba a la derecha la barra del jefe."""
                ahora = tiempo()
                activo = j['equipo'][j['activo']]
                # ----- tu pokemon -----
                congelado = ahora < j['congelado_hasta']
                circulo_poke((46, 54), 34, j['nombre'])
                if congelado: pygame.draw.circle(ventana, (120, 215, 255), (46, 54), 37, 4)
                nombre_t = render(f_borde2, j['nombre'].replace('_', ' ').title(), 'white')
                ventana.blit(nombre_t, (92, 2))
                if activo['puntos']:
                    ev = render(f_borde, '+' + str(activo['puntos']) + ' EV', (255, 220, 90))
                    ventana.blit(ev, (98 + nombre_t.get_width(), 12))
                if progreso.evoluciones(activo, j['inventario']['objetos']) and (ahora // 300) % 2:   # puede evolucionar: EVO titilando
                    evo_t = render(f_borde, 'EVO', (255, 140, 220))
                    ventana.blit(evo_t, (98 + nombre_t.get_width() + (60 if activo['puntos'] else 0), 12))
                k_vida = j['vida'] / max(1, j['max_vida'])
                atras = j.get('vida_atras', k_vida)                       # el daño reciente se vacia despues de un ratito
                if ahora - j.get('golpe_en', -10000) > 380: atras = max(k_vida, atras - 0.012)
                j['vida_atras'] = max(atras, k_vida) if atras >= k_vida else k_vida
                tiembla = ahora - j.get('golpe_en', -10000) < 220
                ox, oy = (random.randint(-3, 3), random.randint(-2, 2)) if tiembla else (0, 0)
                barra = menus.barra_hp(ventana, 86 + ox, 32 + oy, 272, k_vida, 'jugador', 2, activo['nivel'], f_borde, j['vida_atras'])
                vida_t = render(f_borde, str(int(j['vida'])) + ' / ' + str(j['max_vida']), 'white')
                ventana.blit(vida_t, vida_t.get_rect(midright=(barra.right - 10, barra.bottom - 9)))
                if congelado: menus.icono_estado(ventana, 'congelado', (barra.x + 70, barra.bottom - 9))
                ventana.blit(render(f_borde, 'EXP', (120, 210, 255)), (98, 78))
                menus.barra_exp(ventana, 128, 78, 232, progreso.progreso_nivel(activo))
                costo = ESQUIVE['energia'] * mod(j, 'gasto') / ENERGIA_MAX
                ventana.blit(render(f_borde, 'EN', (255, 230, 120) if j['energia'] / ENERGIA_MAX >= costo else (255, 120, 100)), (104, 92))
                menus.barra_exp(ventana, 128, 92, 232, j['energia'] / ENERGIA_MAX, (120, 120, 160) if j['agotado'] else (255, 214, 60))
                marca = 128 + 18 + round(costo * (232 - 36))              # cuanto gasta un esquive
                pygame.draw.line(ventana, (255, 255, 255), (marca, 92), (marca, 101), 2)
                if j['frio'] > 0:                                         # el frio de los golpes de hielo
                    ventana.blit(render(f_borde, 'FRIO', (170, 230, 255)), (92, 106))
                    menus.barra_exp(ventana, 128, 106, 232, j['frio'] / FRIO_MAX, (170, 230, 255))
                monedas = render(f_borde2, '₽' + str(j['monedas']), (255, 220, 70))   # Pokedolares
                ventana.blit(monedas, (14, 96))
                for i, linea in enumerate(tienda.activos(j['inventario'])): ventana.blit(render(f_borde, linea, (230, 230, 230)), (14, 126 + i * 15))
                # ----- la banca -----
                esperando = ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO
                k = 0
                y0 = 132 + 15 * len(tienda.activos(j['inventario']))
                for i, m in enumerate(j['equipo']):
                    if i == j['activo']: continue
                    resto = max(0, m['asist_listo'] - ahora)
                    listo = resto == 0 and m['vida'] > 0
                    r = pygame.Rect(8, y0 + k * 52, 236, 48)
                    menus.panel_flecha(ventana, r, (1, 0) if m['vida'] <= 0 else (2, 0) if listo else (0, 0))
                    circulo_poke((r.x + 26, r.centery), 17, m['nombre'], esperando or m['vida'] <= 0)
                    ventana.blit(render(f_borde, str(i + 1), (255, 240, 120)), (r.x + 8, r.y + 2))
                    if progreso.evoluciones(m, j['inventario']['objetos']) and (ahora // 300) % 2:
                        ventana.blit(render(f_borde, 'EVO', (255, 140, 220)), (r.x + 4, r.bottom - 16))
                    ventana.blit(render(f_borde, cortar(f_borde, m['nombre'].replace('_', ' ').title(), 120), 'white'), (r.x + 50, r.y + 6))
                    menus.barra_vida(ventana, (r.x + 50, r.y + 22, 100, 7), m['vida'] / max(1, m['max_vida']), False)
                    tecla = 'F' if k == 0 else 'G'
                    asist = tecla + ' ' + cortar(f_borde, m['asist']['nombre'].replace('_', ' ').title(), 70)
                    ventana.blit(render(f_borde, asist, (140, 255, 150) if listo else (190, 190, 190)), (r.x + 50, r.y + 32))
                    estado_t = render(f_borde, 'LISTO' if listo else ('-' if m['vida'] <= 0 else str(resto // 1000 + 1) + 's'), (140, 255, 150) if listo else 'white')
                    ventana.blit(estado_t, estado_t.get_rect(midright=(r.right - 18, r.centery)))
                    k += 1
                # ----- abajo a la derecha: el cinturon (cuarto de circulo) y los ataques alrededor -----
                dibujar_cinturon(j, ahora)
                dibujar_ataques(j, ahora, congelado)
                # ----- arriba a la derecha: el minimapa en la esquina y el estilo a su izquierda (debajo de la barra del jefe si hay) -----
                arriba = 100 if nivel['jefe'] else 8
                marco_m = dibujar_minimapa(nivel, j, W - 10, arriba + 7)
                xe = (marco_m.left if marco_m else W - 2) - 108             # la barra del estilo mide 194: que no se meta abajo del mapa
                ye = arriba + 46
                dibujar_estilo(j, xe, ye, ahora)
                # ----- donde estas -----
                if nivel['tipo'] == 'hall': lugar = render(f_borde, 'Hall  ·  ' + viaje['perfil']['nombre'], 'white')
                else: lugar = render(f_borde, mundos.ERAS[rec['era']]['nombre'] + '  ·  Sala ' + str(rec['sala'] + 1) + '/' + str(mundos.salas_de(rec)), 'white')
                caja_l = lugar.get_rect(midtop=(W // 2, 6)).inflate(18, 8)
                velo = pygame.Surface(caja_l.size, pygame.SRCALPHA); velo.fill((10, 10, 20, 150)); ventana.blit(velo, caja_l)
                ventana.blit(lugar, lugar.get_rect(center=caja_l.center))
                # ----- el jefe: la barra del rival de BW -----
                if nivel['jefe']:
                    b = nivel['jefe']
                    nombre_j = render(f_borde2, b['nombre'].replace('_', ' ').title(), 'white')
                    ventana.blit(nombre_j, (W - 400, 4))
                    menus.chip_tipo(ventana, b['tipo'], W - 392 + nombre_j.get_width(), 10)
                    rb = menus.barra_hp(ventana, W - 404, 34, 392, b['vida'] / max(1, b['max_vida']), 'rival', 2, b.get('nivel'), f_borde)
                    if b['estilo'] in ia.FASES_JEFE:                 # la barra de los jefes con fases se parte donde cambian
                        cortes = ia.FASES_JEFE[b['estilo']]
                        h0, h1 = rb.x + 44 * 2, rb.right - (124 - 91) * 2
                        for c in cortes:
                            xc = h0 + round((h1 - h0) * c)
                            pygame.draw.line(ventana, (32, 32, 32), (xc, rb.y + 12), (xc, rb.y + 22), 3)
                        total = ia.TOTAL_FASES.get(b['estilo'], len(cortes) + 1)
                        ventana.blit(render(f_borde, 'Fase ' + str(b['fase']) + '/' + str(total), (255, 230, 120)), (W - 404, rb.bottom + 2))

            ZONAS_HUD = [pygame.Rect(0, 0, 370, 250), pygame.Rect(W - 410, 0, 410, 80), pygame.Rect(W - 270, H - 270, 270, 270), pygame.Rect(W - 340, 0, 340, 250),
                         pygame.Rect(W // 2 - 110, 0, 220, 44)]                                      # donde no van las flechas

            def dibujar_indicadores(nivel, cx, cy):
                """Circulito con punta en el borde de la pantalla para cada enemigo que no se ve, con su cara en chiquito."""
                pantalla = pygame.Rect(0, 0, W, H)
                borde = pantalla.inflate(-70, -70)
                centro = pygame.Vector2(W / 2, H / 2)
                fuera = []
                for e in nivel['enemigos'] + ([nivel['jefe']] if nivel['jefe'] else []):
                    p = pygame.Vector2(e['rect'].centerx - cx, e['rect'].centery - cy)
                    if e['vida'] > 0 and not pantalla.inflate(-20, -20).collidepoint(p): fuera.append((centro.distance_to(p), e, p))
                for _, e, p in sorted(fuera, key=lambda x: x[0])[:8]:
                    v = p - centro
                    if not v.length(): continue
                    d = v.normalize()
                    t = min((borde.right - centro.x) / d.x if d.x > 0 else (borde.left - centro.x) / d.x if d.x < 0 else 1e9,
                            (borde.bottom - centro.y) / d.y if d.y > 0 else (borde.top - centro.y) / d.y if d.y < 0 else 1e9)
                    punto = centro + d * t
                    for zona in ZONAS_HUD:                               # si cae arriba del HUD, se corre por el borde
                        z = zona.inflate(40, 40)
                        if not z.collidepoint(punto): continue
                        vertical = abs(punto.x - borde.left) < 2 or abs(punto.x - borde.right) < 2
                        if zona.topleft == (0, 0) and not vertical: punto.x, punto.y = borde.left, z.bottom   # arriba a la izquierda: baja por el borde
                        elif vertical: punto.y = z.bottom if zona.top == 0 else z.top
                        else: punto.x = z.left if punto.x < zona.centerx else z.right
                    jefe = e is nivel['jefe']
                    radio = 26 if jefe else 21
                    lado = pygame.Vector2(-d.y, d.x)
                    punta = [punto + d * (radio + 12), punto + d * (radio - 4) + lado * 10, punto + d * (radio - 4) - lado * 10]
                    pygame.draw.polygon(ventana, e['color'], punta)
                    circulo_poke((round(punto.x), round(punto.y)), radio, e['nombre'])
                    pygame.draw.circle(ventana, (230, 40, 40) if jefe else e['color'], (round(punto.x), round(punto.y)), radio, 3)

            _siluetas = {}

            def silueta(img, color, alfa):
                """La forma de un sprite pintada de un color con transparencia (estelas, destellos de golpe). Se arma una vez y se reusa."""
                clave = (id(img), color)
                if clave not in _siluetas:
                    if len(_siluetas) > 400: _siluetas.clear()
                    _siluetas[clave] = (img, pygame.mask.from_surface(img).to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0)))
                sup = _siluetas[clave][1]
                sup.set_alpha(alfa)
                return sup

            def franja(ancho, alto, color, inclinacion=26):
                """Paralelogramo (franja inclinada) del color pedido, con transparencia."""
                sup = pygame.Surface((ancho + inclinacion, alto), pygame.SRCALPHA)
                pygame.draw.polygon(sup, color, [(inclinacion, 0), (ancho + inclinacion, 0), (ancho, alto), (0, alto)])
                return sup

            ACENTO_CARTEL = {'¡Parry!': (255, 214, 60), '¡Contraataque!': (255, 150, 40), '¡Golpe en carrera!': (255, 150, 40)}

            def dibujar_carteles(nivel):
                """Carteles: el grande (nombre de la sala, jefes, fases) es una franja inclinada que entra barriendo desde la izquierda con
                rayas de color; los chicos entran deslizandose desde arriba y se apilan. Todos se desvanecen solos."""
                ahora = tiempo()
                nivel['carteles'] = [c for c in nivel['carteles'] if ahora < c['hasta']]
                y_chico = 128
                for c in sorted(nivel['carteles'], key=lambda c_: not c_['grande']):   # primero el grande: los chicos van debajo, sin pisarlo
                    t, resto = ahora - c['inicio'], c['hasta'] - ahora
                    alfa = max(0, min(255, round(255 * min(1.0, resto / 250))))
                    if c['grande']:
                        jefe = nivel['tipo'] in ('jefe', 'regi', 'final')
                        acento = (230, 60, 70) if jefe else (70, 200, 255)
                        k_entra = menus.aparecer(t, 0, 240)
                        titulo_t = render(f_cartel, c['texto'], 'white')
                        sub_t = render(f_cartel_sub, c['sub'] or '', (235, 235, 235))
                        ancho = max(titulo_t.get_width(), sub_t.get_width()) + 140
                        alto = titulo_t.get_height() + (sub_t.get_height() + 8 if c['sub'] else 0) + 26   # la franja se ajusta al texto
                        capa = pygame.Surface((W, alto + 26), pygame.SRCALPHA)
                        x = round((W - ancho) / 2 - (1 - k_entra) * (W + ancho))
                        capa.blit(franja(ancho, alto, (14, 14, 26, 225)), (x, 13))
                        capa.blit(franja(ancho + 60, 7, (*acento, 255)), (x - 40 + round((1 - k_entra) * 200), 4))
                        capa.blit(franja(ancho + 60, 7, (*acento, 255)), (x + 10 - round((1 - k_entra) * 200), alto + 15))
                        capa.blit(franja(ancho - 40, 2, (255, 255, 255, 200)), (x + 40, 22))
                        xt = W // 2 + round((1 - menus.aparecer(t, 60, 260)) * 160)   # el texto llega un poquito despues, desde el otro lado
                        capa.blit(titulo_t, titulo_t.get_rect(midtop=(xt, 22)))
                        capa.blit(sub_t, sub_t.get_rect(midtop=(xt, 22 + titulo_t.get_height() + 4)))
                        capa.set_alpha(alfa)
                        ventana.blit(capa, (0, 130))
                        y_chico = max(y_chico, 130 + capa.get_height() + 8)
                    else:
                        texto_t = render(f_hud_b, c['texto'], 'white')
                        acento = ACENTO_CARTEL.get(c['texto'], (90, 220, 130))
                        ancho, alto = texto_t.get_width() + 46, texto_t.get_height() + 14
                        capa = franja(ancho, alto, (16, 22, 30, 220), 14)
                        pygame.draw.polygon(capa, acento, [(14, 0), (24, 0), (10, alto), (0, alto)])
                        capa.blit(texto_t, texto_t.get_rect(center=(capa.get_width() // 2 + 6, alto // 2)))
                        capa.set_alpha(alfa)
                        caida = round((1 - menus.aparecer(t, 0, 160)) * -30)
                        ventana.blit(capa, capa.get_rect(midtop=(W // 2, y_chico + caida))); y_chico += alto + 6

            SECCIONES_TIENDA = {'chikorita': ('Curaciones', 'Chikorita'), 'riolu': ('Objetos', 'Riolu'), 'kecleon': ('MT', 'Kecleon')}

            def panel_tienda(color):
                """El panel de abajo a la izquierda donde se lee que vas a comprar (no lo tapa el cuarto de circulo de los ataques)."""
                panel = pygame.Rect(14, H - 72, 600, 58)
                pygame.draw.rect(ventana, (25, 25, 25), panel, border_radius=8)
                pygame.draw.rect(ventana, color, panel, 2, border_radius=8)
                return panel

            def dibujar_tienda(nivel, j, cx, cy):
                """Tienda: el cartel de cada mostrador y sus objetos con el precio (el que tenes mas cerca se marca y muestra el nombre).
                Tesoro: los tres premios con nombre. Abajo, que vas a comprar con E."""
                cercana = vitrina_cercana(nivel, j)
                en_tienda = nivel['tipo'] == 'tienda'
                for sec in nivel['sala'].get('secciones', ()) if en_tienda else ():      # cartel arriba de cada tendero
                    titulo, quien = SECCIONES_TIENDA.get(sec['clave'], ('', ''))
                    letrero = render(f_hud_b, titulo + '  ·  ' + quien, 'white')
                    caja_l = letrero.get_rect(midbottom=(sec['centro'] - cx, sec['tendero'][1] - cy - 24)).inflate(18, 6)
                    velo = pygame.Surface(caja_l.size, pygame.SRCALPHA); velo.fill((20, 14, 24, 190)); ventana.blit(velo, caja_l)
                    pygame.draw.rect(ventana, sec['color'], caja_l, 2, border_radius=4)
                    ventana.blit(letrero, letrero.get_rect(center=caja_l.center))
                for v in nivel['vitrinas']:
                    item = tienda.ITEMS[v['item']]
                    x, y = v['pos'][0] - cx, v['pos'][1] - cy
                    if not -60 < x < W + 60 or not -60 < y < H + 60: continue
                    if v is cercana and en_tienda:                       # el que vas a comprar: un aro de luz atras
                        pygame.draw.circle(ventana, (255, 240, 150), (x, y - 6), 22, 2)
                    caja = pygame.Rect(0, 0, 30, 30); caja.center = (x, y - 4)
                    icono = None if v['vendido'] else menus.icono_objeto(v['item'], 34)   # icono del objeto de BW si esta
                    if icono:
                        brillo = 3 + round(2 * math.sin(tiempo() / 300 + x / 50))      # el objeto flota un poquito
                        pygame.draw.ellipse(ventana, (20, 20, 20), (x - 13, y + 8, 26, 7))
                        ventana.blit(icono, icono.get_rect(center=(x, y - 4 - brillo)))
                    elif v['vendido'] and en_tienda: pass                # el lugar queda vacio sobre el mostrador
                    else:
                        pygame.draw.rect(ventana, (60, 60, 60) if v['vendido'] else item['color'], caja, border_radius=6)
                        pygame.draw.rect(ventana, (20, 20, 20), caja, 2, border_radius=6)
                    if en_tienda:                                        # en el mostrador: solo el precio (los nombres no entran); el nombre del que tenes cerca
                        if v['vendido']: texto_p = render(f_borde, 'vendido', (170, 170, 170))
                        else: texto_p = render(f_borde, str(item['precio']) + ' $', (250, 215, 60) if j['monedas'] >= item['precio'] else (230, 100, 100))
                        ventana.blit(texto_p, texto_p.get_rect(midtop=(x, y + 22)))
                        if v is cercana:
                            nombre = render(f_borde, item['nombre'], 'white')
                            ventana.blit(nombre, nombre.get_rect(midbottom=(x, y - 26)))
                        continue
                    nombre = render(f_tipo, 'VENDIDO' if v['vendido'] else item['nombre'], 'white')
                    ventana.blit(nombre, nombre.get_rect(midtop=(x, y + 14)))
                    if not v['vendido']:
                        precio = render(f_tipo, 'elegi uno', (140, 255, 150))
                        ventana.blit(precio, precio.get_rect(midtop=(x, y + 28)))
                punto = nivel['sala'].get('curandera') if en_tienda else None
                if punto:                                                 # la punta del mostrador de Chikorita rosa: ahi cura por monedas
                    cura_t = render(f_borde, '♥ Curar', (255, 225, 240))
                    ventana.blit(cura_t, cura_t.get_rect(midtop=(punto[0] - cx, punto[1] - cy + 22)))
                if punto and not cercana and curandera_cerca(nivel, j):   # el aviso va en el panel de abajo (como al comprar), no tapa nada
                    panel = panel_tienda((255, 150, 200))
                    ventana.blit(render(f_hud_b, tecla_de('interactuar') + ': hablar con Chikorita (curar)', 'white'), (panel.x + 14, panel.y + 8))
                    ventana.blit(render(f_hud, 'cura al que pelea o cura y revive a todo el equipo, por monedas', (210, 210, 210)), (panel.x + 14, panel.y + 34))
                if cercana:
                    item = tienda.ITEMS[cercana['item']]
                    panel = panel_tienda(item['color'])
                    accion_t = ('E: llevarte ' + item['nombre'] + (' x2' if cercana['item'] == 'caramelo_raro' else '')) if nivel['tipo'] == 'tesoro' else \
                        'E: comprar ' + item['nombre'] + ' (' + str(item['precio']) + ' $)'
                    ventana.blit(render(f_hud_b, accion_t, 'white'), (panel.x + 14, panel.y + 8))
                    ventana.blit(render(f_hud, cortar(f_hud, item['desc'], panel.width - 28), (210, 210, 210)), (panel.x + 14, panel.y + 34))

            def dibujar_numeros(nivel, cx, cy, ahora):
                """Numeros de daño que saltan y suben: blancos, amarillos si fue super eficaz, grises si resistio, naranjas y grandes en
                los contraataques y rojos los que recibis vos. Al aparecer pegan un saltito (un tamaño mas grande)."""
                nivel['numeros'] = [n for n in nivel.get('numeros', []) if ahora - n['inicio'] < NUMEROS['dura']]
                for n in nivel['numeros']:
                    t = ahora - n['inicio']
                    escala = (3 if n['grande'] else 2) + (1 if t < NUMEROS['salto'] else 0)
                    img = tipografia.fuente(20, borde=True, escala=escala).render(str(n['valor']), True, n['color'])
                    subida = NUMEROS['subida'] * (1 - (1 - t / NUMEROS['dura']) ** 2)
                    if t > NUMEROS['dura'] * 0.6: img = img.copy(); img.set_alpha(round(255 * (1 - (t - NUMEROS['dura'] * 0.6) / (NUMEROS['dura'] * 0.4))))
                    ventana.blit(img, img.get_rect(center=(round(n['x'] - cx + n['dx'] * t / 40), round(n['y'] - cy - subida))))

            def dibujar_aviso_evolucion(nivel, j):
                """Abajo en el medio: el retrato del que quiere evolucionar, una flecha, el de su evolucion y la tecla con el anillo que se llena."""
                evo = nivel.get('evo')
                if not evo: return
                ahora = tiempo()
                m = j['equipo'][evo['i']]
                tecla = tecla_de('evolucionar')
                texto = render(f_borde2, 'Mantené ' + tecla + ': ¡' + m['nombre'].replace('_', ' ').title() + ' quiere evolucionar!', 'white')
                ancho = texto.get_width() + 200
                entra = menus.aparecer(ahora - evo['desde'], 0, 260)
                x = W // 2 - ancho // 2; y = H - 170 + round((1 - entra) * 60)
                capa = franja(ancho, 70, (16, 14, 30, 225), 22)
                pygame.draw.polygon(capa, (255, 140, 220), [(22, 0), (32, 0), (10, 70), (0, 70)])
                ventana.blit(capa, (x, y))
                circulo_poke((x + 60, y + 35), 26, m['nombre'])
                flecha = render(f_borde2, '→', (255, 220, 120)); ventana.blit(flecha, flecha.get_rect(center=(x + 104, y + 35)))
                circulo_poke((x + 148, y + 35), 26, evo['req']['a'], (ahora // 250) % 2 == 0)
                ventana.blit(texto, texto.get_rect(midleft=(x + 186, y + 35)))
                k = evo['carga'] / EVOLUCION['mantener']
                if k > 0:                                               # el anillo que se llena mientras mantenes
                    pygame.draw.arc(ventana, (255, 140, 220), (x + 120, y + 5, 56, 56), math.pi / 2, math.pi / 2 + math.tau * k, 5)
                    blanco = pygame.Surface((W, H), pygame.SRCALPHA); blanco.fill((255, 255, 255, round(90 * k * k))); ventana.blit(blanco, (0, 0))

            def dibujar_objetos(nivel, j, rec):
                """Dibuja un frame de la partida: sala, puertas, balas, efectos, pokemon, jefe, clima, HUD y carteles."""
                cx, cy = camara(j)
                ahora = tiempo()
                patada = nivel.get('patada_camara')
                if patada and ahora < patada[2]:                          # la camara acompaña el golpe
                    k = (patada[2] - ahora) / PATADA_CAMARA['dura']
                    cx += round(patada[0] * k); cy += round(patada[1] * k)
                if ahora < nivel['temblor']:                              # terremotos y puñetazos de Regigigas
                    fuerza = min(10, 2 + (nivel['temblor'] - ahora) // 40)
                    cx += random.randint(-fuerza, fuerza); cy += random.randint(-fuerza, fuerza)
                ventana.fill('black')
                entorno.dibujar(nivel['ent'], ventana, cx, cy, ahora, j['tipos'])   # piso de la era, terrenos, maquinas y objetos
                ia.dibujar_suelo(ventana, nivel['jefe'], cx, cy, ahora, COLORES_TIPO)   # Arceus Beta: el triangulo, charcos, rastros y arena
                mec.dibujar(nivel, j, cx, cy)                            # nubes, charcos, bombas, raices, jardin... y los avisos de enemigos con mecanica
                for puerta in nivel['puertas'] if not nivel['ent'].get('guardado') else ():   # puertas con el cartel (en la torre de Regidrago no hay)
                    r = puerta['rect'].move(-cx, -cy)
                    abierta = j['llave'] and not puerta.get('bloqueada') and (not puerta.get('atras') or nivel['completado'])
                    entorno.dibujar_puerta(ventana, r, abierta, ahora)    # cerrada con tablas o abierta brillando
                    portal = nivel.get('portal')
                    if portal and portal['puerta'] is puerta:            # el portal de Celebi: anillos de colores girando (como el tunel del viaje)
                        crece = min(1.0, (ahora - portal['desde']) / 800)
                        for k in range(5):
                            ang = ahora / 300 + k * 1.3
                            color = ((120, 255, 200), (90, 200, 255), (170, 130, 255))[k % 3]
                            radio = round((r.width * 0.55 - k * 9) * crece)
                            if radio < 4: continue
                            caja_p = pygame.Rect(0, 0, radio * 2, round(radio * 1.3)); caja_p.center = (r.centerx + round(math.cos(ang) * 4), r.centery + round(math.sin(ang) * 3))
                            pygame.draw.ellipse(ventana, color, caja_p, 3)
                        pygame.draw.circle(ventana, (235, 255, 250), r.center, max(2, round(10 * crece + math.sin(ahora / 150) * 3)))
                    if 'destino' in puerta and (not puerta.get('atras') or nivel['completado']):
                        etiqueta = mundos.etiqueta_destino(puerta['destino'])
                        t = render(f_hud_b, ('PORTAL: ' + etiqueta) if portal and portal['puerta'] is puerta else etiqueta, 'white')
                        df, dc = generacion.PASO_LADO[puerta['lado']]           # el cartel va un poco hacia adentro de la sala
                        centro_t = (r.centerx + dc * (r.width // 2 + 20 + t.get_width() // 2), r.centery + df * (r.height // 2 + 22))
                        fondo_t = t.get_rect(center=centro_t).inflate(12, 6)
                        pygame.draw.rect(ventana, (20, 20, 20), fondo_t, border_radius=5)
                        ventana.blit(t, t.get_rect(center=fondo_t.center))
                for piedra_verde in nivel['verdes']: dibujar_rect(piedra_verde['rect'],cx,cy,(0,220,80),'ellipse')
                for a in nivel['apariciones']:                            # donde va a salir la proxima oleada
                    k = 1 - (a['hasta'] - ahora) / 900
                    pygame.draw.circle(ventana, (230, 60, 60), (round(a['pos'][0] - cx), round(a['pos'][1] - cy)), round(10 + 20 * k), 3)
                for proyectil in nivel['proyectiles_enemigos']:              # bolas de fuego, hojas, rocas... del PMD (si no hay, un circulo)
                    tipo_p = normalizar_tipo(proyectil.get('tipo'))
                    radio_p = max(9 if proyectil['jefe'] else 8, proyectil['tam'] // 2)
                    centro_p = (round(proyectil['x']-cx), round(proyectil['y']-cy))
                    if efectos.proyectil(ventana, tipo_p, *centro_p, radio_p, ahora): continue
                    pygame.draw.circle(ventana, COLORES_TIPO.get(tipo_p, (255, 150, 0)), centro_p, radio_p)
                    pygame.draw.circle(ventana, (40, 0, 0), centro_p, radio_p, 2)
                capa_ef = pygame.Surface((W, H), pygame.SRCALPHA) if nivel['efectos'] else None
                for ef in nivel['efectos']:                                  # golpes cuerpo a cuerpo (estela) y ataques en area (onda que se abre)
                    color_ef = COLORES_TIPO.get(normalizar_tipo(ef['tipo']), (255,255,255))
                    k = max(0.0, min(1.0, (ahora - ef['inicio']) / max(1, ef['hasta'] - ef['inicio'])))
                    alfa = round(220 * (1 - k))
                    if 'linea' in ef:
                        a, b = (round(ef['x']-cx), round(ef['y']-cy)), (round(ef['linea'][0]-cx), round(ef['linea'][1]-cy))
                        pygame.draw.line(capa_ef, (*color_ef, alfa), a, b, ef['radio'] * 2)
                        pygame.draw.line(capa_ef, (255, 255, 255, alfa), a, b, max(2, ef['radio'] // 2))
                    else:
                        radio_ef = round(ef['radio'] * (0.35 + 0.65 * (1 - (1 - k) ** 2)))
                        centro_ef = (round(ef['x']-cx), round(ef['y']-cy))
                        pygame.draw.circle(capa_ef, (*color_ef, alfa // 4), centro_ef, radio_ef)
                        pygame.draw.circle(capa_ef, (*color_ef, alfa), centro_ef, radio_ef, 6)
                        pygame.draw.circle(capa_ef, (255, 255, 255, alfa), centro_ef, max(1, radio_ef - 5), 2)
                if capa_ef: ventana.blit(capa_ef, (0, 0))
                for proyectil in nivel['proyectiles_pokemon']:
                    try: radio = max(2, int(float(proyectil['datos'].get('area', 8))))
                    except (TypeError, ValueError): radio = 8
                    tipo_p = normalizar_tipo(proyectil['datos'].get('tipo'))
                    centro_p = (round(proyectil['x']-cx), round(proyectil['y']-cy))
                    if not efectos.proyectil(ventana, tipo_p, *centro_p, radio, ahora):
                        pygame.draw.circle(ventana, COLORES_TIPO.get(tipo_p, (80,180,255)), centro_p, radio)
                for r in nivel.get('recogibles', []):                    # bayas, llaves y caramelos en el piso
                    flota = round(3 * math.sin((ahora - r['inicio']) / 180))
                    pygame.draw.ellipse(ventana, (20, 20, 20), (round(r['x'] - cx) - 10, round(r['y'] - cy) + 8, 20, 6))
                    icono = menus.icono_objeto(r['item'], 28)
                    if icono: ventana.blit(icono, icono.get_rect(center=(round(r['x'] - cx), round(r['y'] - cy) - 4 + flota)))
                    if (ahora // 120) % 6 == 0: pygame.draw.circle(ventana, (255, 255, 230), (round(r['x'] - cx) + 9, round(r['y'] - cy) - 14 + flota), 2)
                for moneda in nivel['monedas']:
                    pygame.draw.circle(ventana, (250, 210, 50), (round(moneda['x'] - cx), round(moneda['y'] - cy)), 8)
                    pygame.draw.circle(ventana, (150, 110, 20), (round(moneda['x'] - cx), round(moneda['y'] - cy)), 8, 2)
                nivel['estela'] = [x for x in nivel.get('estela', []) if ahora - x['inicio'] < ESTELA['dura']]
                for x in nivel['estela']:                                # estela: copias que se desvanecen
                    alfa = round(150 * (1 - (ahora - x['inicio']) / ESTELA['dura']))
                    ventana.blit(silueta(x['img'], x['color'], alfa), (x['x'] - cx, x['y'] - cy))
                dibujar_jugador(j,cx,cy)
                dibujar_congelado(j, cx, cy)
                if ahora < j.get('baile_hasta', 0):                       # bailando: notas musicales y un anillo que muestra hasta donde llega
                    k = 1 - (j['baile_hasta'] - ahora) / BAILE['dura']
                    pygame.draw.circle(ventana, (255, 180, 220), (j['rect'].centerx - cx, j['rect'].centery - cy), round(BAILE['radio'] * (0.3 + 0.7 * k)), 2)
                    for n in range(4):
                        ang = ahora / 220 + n * math.tau / 4
                        nx, ny = round(j['rect'].centerx - cx + math.cos(ang) * 34), round(j['rect'].centery - cy - 10 + math.sin(ang) * 20 - k * 18)
                        pygame.draw.circle(ventana, (255, 240, 255), (nx, ny), 4)
                        pygame.draw.line(ventana, (255, 240, 255), (nx + 3, ny), (nx + 3, ny - 11), 2)
                        pygame.draw.line(ventana, (255, 240, 255), (nx + 3, ny - 11), (nx + 8, ny - 8), 2)
                if ahora < j.get('parry_hasta', 0):                       # ventana de parry abierta: anillo blanco que se achica
                    k = (j['parry_hasta'] - ahora) / max(1, j.get('parry_dura', PARRY['ventana']))
                    pygame.draw.circle(ventana, (255, 255, 255), (j['rect'].centerx - cx, j['rect'].centery - cy), round(max(j['rect'].size) * (0.7 + 0.5 * k)), 2)
                if ahora < j.get('inv_hasta', 0):                         # esquivando: estela celeste (invulnerable)
                    pygame.draw.ellipse(ventana, (150, 230, 255), j['rect'].inflate(14, 14).move(-cx, -cy), 2)
                if ahora < j.get('contra_hasta', 0):                      # contraataque listo: chispitas doradas alrededor
                    for k in range(3):
                        ang = ahora / 160 + k * math.tau / 3
                        pygame.draw.circle(ventana, (255, 215, 80), (round(j['rect'].centerx - cx + math.cos(ang) * 30), round(j['rect'].centery - cy + math.sin(ang) * 22)), 4)
                if ahora - j.get('ultimo_golpe', -10000) <= COMBO['ventana'] and j.get('combo'):   # puntitos del combo arriba del pokemon
                    for k in range(3):
                        lleno = k < j['combo']
                        pygame.draw.circle(ventana, (255, 230, 120) if lleno else (60, 60, 60), (j['rect'].centerx - cx - 14 + k * 14, j['rect'].top - cy - 12), 5 if lleno else 4)
                if j['oculto']: pygame.draw.circle(ventana, (200, 200, 255), (j['rect'].centerx - cx, j['rect'].top - cy - 8), 5, 2)   # escondido
                if j['uso'] == 'mouse': mx, my = pantalla.raton()
                else: mx, my = round(j['rect'].centerx - cx + j['aim'][0] * 90), round(j['rect'].centery - cy + j['aim'][1] * 90)
                pygame.draw.circle(ventana, (230, 20, 20), (mx, my), 11, 2)
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    pygame.draw.line(ventana, (230, 20, 20), (mx + ox * 6, my + oy * 6), (mx + ox * 16, my + oy * 16), 2)
                for e in nivel['enemigos']:
                    if not dibujar_enemigo(e, cx, cy): dibujar_rect(e['rect'],cx,cy,e['color'])
                    ancho_b = max(44, e['rect'].width)
                    barra((e['rect'].centerx - cx - ancho_b // 2, e['rect'].y - cy - 10, ancho_b, 6), e['vida'], e['max_vida'])
                    etiqueta = render(f_borde, e['nombre'].replace('_', ' ').title() + ' Nv' + str(e['nivel']), 'white')
                    ventana.blit(etiqueta, etiqueta.get_rect(midtop=(e['rect'].centerx - cx, e['rect'].bottom - cy + 2)))
                    if e.get('estado') and e.get('estado_hasta', 0) > ahora:          # BRN, PAR... de BW arriba de la barra
                        menus.icono_estado(ventana, e['estado'], (e['rect'].centerx - cx, e['rect'].y - cy - 20))
                    if e.get('estado') == 'confundir' and ahora < e.get('estado_hasta', 0):   # confundido: estrellitas girando arriba de la cabeza
                        for k in range(3):
                            ang = ahora / 180 + k * math.tau / 3
                            pygame.draw.circle(ventana, (255, 230, 90), (round(e['rect'].centerx - cx + math.cos(ang) * 16), round(e['rect'].top - cy - 14 + math.sin(ang) * 5)), 4)
                    for k in range(e.get('encariño', 0)):                     # encariñado por tu baile: un corazoncito por cada vez
                        hx, hy = e['rect'].centerx - cx - (e['encariño'] - 1) * 7 + k * 14, e['rect'].top - cy - 20
                        pygame.draw.circle(ventana, (255, 110, 160), (hx - 3, hy), 4); pygame.draw.circle(ventana, (255, 110, 160), (hx + 3, hy), 4)
                        pygame.draw.polygon(ventana, (255, 110, 160), [(hx - 7, hy + 1), (hx + 7, hy + 1), (hx, hy + 8)])
                for e in nivel.get('amigos', ()):                          # los que quieren unirse: sentados con un corazon
                    dibujar_enemigo(e, cx, cy)
                    pygame.draw.circle(ventana, (255, 110, 160), (e['rect'].centerx - cx, e['rect'].top - cy - 14), 9)
                    if math.hypot(e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery) < 90:
                        t = render(f_hud_b, tecla_de('interactuar') + ': hablar', 'white')
                        ventana.blit(t, t.get_rect(midbottom=(e['rect'].centerx - cx, e['rect'].top - cy - 26)))
                for r in nivel.get('residentes', ()):                       # tus amigos paseando por el hall
                    if not dibujar_enemigo(r, cx, cy): dibujar_rect(r['rect'], cx, cy, r['color'])
                    con_sombra(f_tipo, r['nombre'].replace('_', ' ').title(), 'white', (r['rect'].x - cx, r['rect'].bottom - cy + 2))
                    if math.hypot(r['rect'].centerx - j['rect'].centerx, r['rect'].centery - j['rect'].centery) <= DISTANCIA_HABLAR:
                        t = render(f_hud_b, tecla_de('interactuar') + ': hablar', 'white')
                        ventana.blit(t, t.get_rect(midbottom=(r['rect'].centerx - cx, r['rect'].top - cy - 10)))
                portal = nivel.get('portal')
                if portal and portal['celebi']:                               # Celebi al lado del portal de fin de era: llega flotando y despues te mira
                    a = portal['celebi']
                    if ahora - portal['desde'] > 1200: a.cambiar('idle', 0, True)
                    centro = a.rect.center
                    a.rect.center = (round(portal['pos'][0] - cx), round(portal['pos'][1] - cy + math.sin(ahora / 500) * 6))
                    a.actualizar(); a.dibujar(ventana); a.rect.center = centro
                    if math.hypot(portal['pos'][0] - j['rect'].centerx, portal['pos'][1] - j['rect'].centery) <= DISTANCIA_HABLAR + 20:
                        t = render(f_hud_b, tecla_de('interactuar') + ': hablar con Celebi', 'white')
                        ventana.blit(t, t.get_rect(midbottom=(portal['pos'][0] - cx, portal['pos'][1] - cy - 34)))
                if nivel['tipo'] == 'hall':                                   # Celebi al lado del portal
                    gx, gy = nivel['sala']['guardian']
                    if math.hypot(gx - j['rect'].centerx, gy - j['rect'].centery) <= DISTANCIA_HABLAR + 20:
                        t = render(f_hud_b, tecla_de('interactuar') + ': hablar con Celebi', 'white')
                        ventana.blit(t, t.get_rect(midbottom=(gx - cx, gy - cy - 34)))
                if j.get('en_arena'):                                      # Bucle Arena de Arceus Beta
                    t = render(f_hud_b, tecla_de('interactuar') + ': salir de la arena', 'white')
                    ventana.blit(t, t.get_rect(midbottom=(j['rect'].centerx - cx, j['rect'].top - cy - 22)))
                bloque = bloque_cercano(j)
                if bloque:
                    t = render(f_hud_b, tecla_de('interactuar') + ': empujar', 'white')
                    ventana.blit(t, t.get_rect(midbottom=(bloque['rect'].centerx - cx, bloque['rect'].top - cy - 8)))
                if nivel['jefe'] and not nivel['jefe'].get('escondido'):     # Regieleki adentro de una torre no se ve
                    b = nivel['jefe']
                    if not dibujar_enemigo(b, cx, cy): dibujar_rect(b['rect'].move(0, -b.get('altura', 0)),cx,cy,b.get('color',(255,140,0)))
                    barra((b['rect'].x-cx,b['rect'].y-cy-12-b.get('altura', 0),b['rect'].width,8),b['vida'],b['max_vida'],8)
                ia.dibujar_avisos(ventana, nivel['enemigos'] + ([nivel['jefe']] if nivel['jefe'] else []), cx, cy, ahora, f_hud_b, COLORES_TIPO)
                dibujar_numeros(nivel, cx, cy, ahora)
                ventana_parry = PARRY['ventana'] * mod(j, 'parry')
                for e in nivel['enemigos']:                                # el momento justo del parry: el aviso brilla amarillo
                    a_ = e.get('aviso')
                    if e['vida'] <= 0 or not a_ or a_['clase'] not in ('golpe', 'embestida') or a_['hasta'] - ahora > ventana_parry: continue
                    if math.hypot(e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery) > max(j['rect'].size) + max(e['rect'].size) + 140: continue
                    brillo = 255 if (ahora // 60) % 2 else 200
                    pygame.draw.circle(ventana, (brillo, brillo, 60), (e['rect'].centerx - cx, e['rect'].centery - cy), max(e['rect'].size) // 2 + 14, 4)
                    t = render(f_hud_b, '!', (255, 240, 80))
                    ventana.blit(t, t.get_rect(midbottom=(e['rect'].centerx - cx, e['rect'].top - cy - 14)))
                for g in (nivel['llegada'] or {}).get('golpes', ()):       # las Sentencias que vacian la arena alrededor tuyo
                    if ahora >= g['inicio']:
                        k = min(1.0, (ahora - g['inicio']) / LLEGADA_BETA['aviso'])
                        ia.dibujar_sello(ventana, (round(g['pos'][0] - cx), round(g['pos'][1] - cy)), LLEGADA_BETA['radio'], (245, 240, 220), k, ahora)
                if nivel['llave']: dibujar_rect(nivel['llave'],cx,cy,'yellow')
                if nivel['tipo'] in ('tienda', 'tesoro'): dibujar_tienda(nivel, j, cx, cy)
                efectos.dibujar(mundo['ef'], ventana, cx, cy)              # chispas, pedazos, explosiones, brillitos
                entorno.dibujar_clima(nivel['ent'], ventana, ahora)
                if nivel.get('destello') and ahora - nivel['destello'][0] < DESTELLO:   # parry, esquive perfecto, remate: un flash cortito
                    velo = pygame.Surface((W, H), pygame.SRCALPHA)
                    velo.fill((*nivel['destello'][1], round(110 * (1 - (ahora - nivel['destello'][0]) / DESTELLO))))
                    ventana.blit(velo, (0, 0))
                dibujar_indicadores(nivel, cx, cy)
                mec.dibujar_hud(j, ventana, W, H, cx, cy)
                dibujar_hud(j, nivel, rec)
                dibujar_aviso_evolucion(nivel, j)
                efectos.dibujar_transicion(mundo['ef'], ventana, ahora)    # circulo negro al entrar o salir de la sala
                dibujar_carteles(nivel)
                pantalla.presentar()

            return dibujar_objetos, silueta

        dibujar_objetos, silueta = armar_dibujo()

        def armar_extras():
            """Pantalla final, acciones del menu de equipo (TAB) y trucos."""
            def pantalla_final():
                """Cuando cae Arceus."""
                pygame.mouse.set_visible(True)
                f_g, f_c = tipografia.fuente_titulo(4), tipografia.fuente(30)
                reloj_f = pygame.time.Clock()
                while True:
                    for e in controles.eventos():
                        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE)): return
                    ventana.fill((20, 15, 35))
                    t = f_g.render('¡Ganaste!', True, (250, 220, 120))
                    ventana.blit(t, t.get_rect(center=(W // 2, H // 2 - 50)))
                    s = f_c.render('Los Regis, Regigigas y Arceus. Celebi no lo puede creer.', True, 'white')
                    ventana.blit(s, s.get_rect(center=(W // 2, H // 2 + 40)))
                    s = tipografia.fuente(24).render('ENTER para volver', True, (190, 190, 210))
                    ventana.blit(s, s.get_rect(center=(W // 2, H // 2 + 80)))
                    pantalla.presentar(); reloj_f.tick(60)

            def acciones_equipo(j):
                """Lo que puede hacer el menu de equipo (TAB) sobre el jugador."""
                def refrescar():
                    """Recalcula vida y multiplicadores despues de gastar puntos o subir de nivel desde el menu."""
                    m = j['equipo'][j['activo']]
                    antes = j['max_vida']; m['max_vida'] = progreso.vida_max(m)
                    j['vida'] = min(m['max_vida'], j['vida'] + max(0, m['max_vida'] - antes)); j['max_vida'] = m['max_vida']; j['mults'] = progreso.multiplicadores(m)
                    for o in j['equipo']:
                        if o is not m: o['max_vida'] = progreso.vida_max(o); o['vida'] = min(o['vida'], o['max_vida'])

                def evolucionar(i, req):
                    """Evoluciona al pokemon i (gasta el objeto si hacia falta) manteniendo el porcentaje de vida."""
                    guardar_activo(j)
                    m = j['equipo'][i]
                    if 'objeto' in req: j['inventario']['objetos'][req['objeto']] = max(0, j['inventario']['objetos'].get(req['objeto'], 0) - 1)
                    proporcion = m['vida'] / max(1, m['max_vida'])
                    antes = m['nombre']
                    progreso.evolucionar(m, req['a'])
                    m['asist'] = asistencia_de(m['nombre']); m['max_vida'] = progreso.vida_max(m); m['vida'] = round(m['max_vida'] * proporcion)
                    if i == j['activo']: aplicar_pokemon(j, m['nombre'], m['vida'])
                    if antes == 'nincada' and m['nombre'] == 'ninjask' and progreso._jugable('shedinja'):   # como en los juegos: queda el caparazon
                        cascara = crear_miembro('shedinja', m['nivel'])
                        registrar_amigos(viaje['perfil'], [cascara])
                        if len(j['equipo']) < 3: j['equipo'].append(cascara)
                        elif len(j['reserva']) < RESERVA_MAX: j['reserva'].append(cascara)
                        if mundo.get('nivel'): cartel(mundo['nivel'], '¡Del caparazón de Nincada salió Shedinja!', 2400)
                    actualizar_sinergia(j)

                def enseñar(i, casilla, mt):
                    """Enseña una MT en una casilla de movimiento (la MT se gasta salvo con los trucos)."""
                    m = j['equipo'][i]
                    m['movs'][casilla] = mt
                    if not (trucos.get('mt_infinitas') or trucos.get('todas_mt')):        # la MT se gasta
                        j['inventario']['objetos'][mt] = max(0, j['inventario']['objetos'].get(mt, 0) - 1)
                    if i == j['activo']: j['juego'] = juego_de(m)

                def traer(ri, k):
                    """Trae un pokemon de la reserva al equipo (al final, o cambiandolo por el del espacio k)."""
                    guardar_activo(j)
                    nuevo = j['reserva'].pop(ri)
                    if k is None: j['equipo'].append(nuevo)
                    else:
                        j['reserva'].append(j['equipo'][k]); j['equipo'][k] = nuevo
                        if k == j['activo']: aplicar_pokemon(j, nuevo['nombre'], nuevo['vida'])
                    actualizar_sinergia(j)

                def movs(m):
                    """Nombres de los 4 movimientos de un miembro (E, Q, Shift, R) con sus MT puestas."""
                    g = juego_de(m)
                    return [nombre_mov(n) for n in (g['basicos'][0], g['basicos'][1], g['especiales'][0][0], g['especiales'][1][0])]

                def info_movs(m):
                    """Que hace cada una de las 4 casillas: texto listo para mostrar (con los ajustes de los basicos y el combo)."""
                    g = juego_de(m)
                    salida = []
                    for k, n in enumerate((g['basicos'][0], g['basicos'][1], g['especiales'][0][0], g['especiales'][1][0])):
                        d = dict(datos_mov(n) or {})
                        if k < 2 and (not mts.datos(n) or mts.MTS[n]['casillas'] == 'todas'):
                            ajustes = BASICO_DISTANCIA if k == 1 or d.get('forma') == 'proyectil' else GOLPE_CUERPO
                            for clave, f in ajustes.items():
                                if clave in d: d[clave] = round(float(d[clave]) * f)
                        salida.append(datos.explicar_movimiento(d, k) + ' (' + datos.describir_movimiento(d) + ')')
                    return salida

                def equipar(i, ranura, clave):
                    """Pone (o saca, con clave None) un objeto en la ranura 0 o 1 del pokemon i. El que estaba vuelve a la mochila."""
                    m = j['equipo'][i]; items = m.setdefault('items', []); objetos = j['inventario']['objetos']
                    if ranura < len(items):
                        viejo = items.pop(ranura); objetos[viejo] = objetos.get(viejo, 0) + 1
                    if clave and objetos.get(clave, 0) > 0 and len(items) < tienda.MAX_EQUIPADOS:
                        objetos[clave] -= 1; items.insert(min(ranura, len(items)), clave)

                def elegir_sinergia(i, clave):
                    """La pasiva que da el pokemon i desde la banca (None = la de su rol)."""
                    j['equipo'][i]['sinergia'] = clave
                    actualizar_sinergia(j)

                def texto_asistencia(m):
                    """Que hace la asistencia de un miembro (F / G desde la banca)."""
                    a = m['asist']
                    return a['nombre'].replace('_', ' ').title() + ': ' + descripcion_asistencia(a) + ' (espera ' + str(a['enfriamiento'] // 1000) + ' s)'

                def caramelo(i):
                    """Caramelo Raro: el pokemon i sube un nivel (gasta un caramelo)."""
                    m = j['equipo'][i]; objetos = j['inventario']['objetos']
                    if objetos.get('caramelo_raro', 0) <= 0 or m['nivel'] >= progreso.NIVEL_MAX: return False
                    objetos['caramelo_raro'] -= 1
                    guardar_activo(j)
                    progreso.dar_xp(m, progreso.xp_para(m['nombre'], m['nivel'] + 1) - m['xp'])
                    refrescar()
                    if i == j['activo']: j['nivel'] = m['nivel']
                    return True

                def usar(i, indice):
                    """Usa la curacion de ese lugar del cinturon en el miembro i (o en el de la reserva si i es ('r', k)). Devuelve el texto."""
                    guardar_activo(j)
                    m = j['reserva'][i[1]] if isinstance(i, tuple) else j['equipo'][i]
                    return usar_curacion(j, m, indice)[1]

                return {'usar': usar,
                        'movs': movs, 'evolucionar': evolucionar, 'enseñar': enseñar, 'activar': lambda i: cambiar_slot(j, i, True),
                        'cambiar_reserva': lambda: mundo.get('nivel', {}).get('tipo') == 'tienda' or any(trucos.values()),   # solo en la tienda
                        'refrescar': refrescar, 'reserva': lambda: j['reserva'], 'traer': traer, 'info_movs': info_movs, 'equipar': equipar,
                        'sinergia': elegir_sinergia, 'asistencia': texto_asistencia, 'caramelo': caramelo, 'tecla_curar': tecla_de('curar')}

            def aplicar_trucos(nivel, j):
                """Los trucos que hacen algo una sola vez (subir niveles)."""
                veces = trucos.pop('subir_niveles', 0)
                for _ in range(veces):
                    for m in j['equipo']: progreso.dar_xp(m, progreso.xp_para(m['nombre'], m['nivel'] + 5) - m['xp'])
                if veces:
                    acciones_equipo(j)['refrescar'](); j['nivel'] = j['equipo'][j['activo']]['nivel']
                    cartel(nivel, 'Truco: +' + str(5 * veces) + ' niveles')

            def evolucion_pendiente(j):
                """(indice, requisito) del primero del equipo que ya puede evolucionar, o None."""
                for i, m in enumerate(j['equipo']):
                    if m['vida'] <= 0: continue
                    reqs = progreso.evoluciones(m, j['inventario']['objetos'])
                    if reqs: return i, reqs[0]
                return None

            def actualizar_evolucion(nivel, j, mantiene):
                """Evolucionar sin menus: cuando no hay peligro aparece el aviso y manteniendo la tecla se llena un anillo y evoluciona ahi mismo.
                Peleando no se interrumpe nada (solo se ve un 'EVO' chiquito en el HUD)."""
                pendiente = evolucion_pendiente(j)
                tranquilo = nivel['completado'] or not (nivel['enemigos'] or nivel['jefe'] or nivel['oleadas'] or nivel['apariciones'])
                if not pendiente or not tranquilo or nivel['saliendo']: nivel['evo'] = None; return
                i, req = pendiente
                evo = nivel.get('evo') if nivel.get('evo') and nivel['evo']['i'] == i else {'i': i, 'req': req, 'carga': 0, 'desde': tiempo()}
                evo['req'] = req
                evo['carga'] = min(EVOLUCION['mantener'], evo['carga'] + 1000 / 60) if mantiene else max(0, evo['carga'] - 1000 / 30)
                nivel['evo'] = evo
                if evo['carga'] < EVOLUCION['mantener']: return
                m = j['equipo'][i]; antes = m['nombre'].replace('_', ' ').title()
                acciones_equipo(j)['evolucionar'](i, req)
                centro = j['rect'].center if i == j['activo'] else (j['rect'].centerx, j['rect'].top - 30)
                efectos.evolucion(mundo['ef'], *centro); efectos.destello(mundo['ef'], *centro)
                nivel['destello'] = (tiempo(), (255, 255, 255)); nivel['temblor'] = max(nivel['temblor'], tiempo() + 200)
                aplicar_trucos(nivel, j)
                cartel(nivel, antes + ' evolucionó en ' + m['nombre'].replace('_', ' ').title() + '!', 2600, 'conserva nivel, IV, EV, MT y objetos', grande=True)
                nivel['evo'] = None; nivel['guardar'] = True

            return pantalla_final, acciones_equipo, aplicar_trucos, evolucion_pendiente, actualizar_evolucion

        pantalla_final, acciones_equipo, aplicar_trucos, evolucion_pendiente, actualizar_evolucion = armar_extras()

        def armar_guardado():
            """Pasar la partida a datos guardables (equipo, mochila, recorrido) y armarla de vuelta al cargar."""
            CAMPOS = ('id', 'nombre', 'nivel', 'xp', 'ivs', 'evs', 'puntos', 'amistad', 'naturaleza', 'movs', 'items', 'sinergia', 'vida')

            def serializar(j, rec):
                """Todo lo que hace falta para seguir la partida despues (en el hall el recorrido es el del proximo viaje, todavia sin empezar)."""
                guardar_activo(j)
                miembro = lambda m: {k: m.get(k) for k in CAMPOS}
                azar = rec['azar'].getstate()
                perfil = viaje['perfil']
                resumen = {'equipo': [[m['nombre'], m['nivel']] for m in j['equipo']], 'era': mundos.ERAS[rec['era']]['nombre'],
                           'sala': rec['sala'] + 1, 'salas': mundos.salas_de(rec), 'monedas': j['monedas'], 'fecha': time.strftime('%d/%m/%Y %H:%M'),
                           'nombre': perfil['nombre'], 'amigos': len(perfil['amigos']), 'hall': viaje['en_hall']}
                if viaje['en_hall']: resumen.update({'era': 'En el hall', 'sala': '-', 'salas': '-'})
                return {'jugador': {'equipo': [miembro(m) for m in j['equipo']], 'activo': j['activo'], 'reserva': [miembro(m) for m in j['reserva']],
                                    'monedas': j['monedas'], 'inventario': j['inventario']},
                        'recorrido': {'plan': rec['plan'], 'era': rec['era'], 'sala': rec['sala'], 'semilla': rec['semilla'], 'clima': rec['clima'],
                                      'azar': [azar[0], list(azar[1]), azar[2]], 'historial': rec['historial'], 'pos': rec['pos'], 'amistad': rec.get('amistad')},
                        'perfil': perfil, 'en_hall': viaje['en_hall'], 'resumen': resumen}

            def revivir(d):
                """Un miembro del equipo desde lo guardado (la vida maxima y la asistencia se recalculan)."""
                m = crear_miembro(d['nombre'], d.get('nivel', progreso.NIVEL_INICIAL))
                m.update({k: d[k] for k in CAMPOS if d.get(k) is not None and k != 'vida'})   # las partidas viejas no tienen 'id': queda el nuevo
                m['items'] = list(m.get('items') or [])
                m['max_vida'] = progreso.vida_max(m)
                m['vida'] = max(0, min(m['max_vida'], d.get('vida', m['max_vida'])))
                return m

            def restaurar(datos_):
                """(jugador, recorrido) de una partida guardada."""
                jd, rd = datos_['jugador'], datos_['recorrido']
                equipo = [revivir(d) for d in jd['equipo']]
                j = crear_jugador([equipo[0]['nombre']], ESC.center, config['modo'])
                j['equipo'], j['reserva'] = equipo, [revivir(d) for d in jd.get('reserva', [])]
                j['activo'] = max(0, min(len(equipo) - 1, jd.get('activo', 0)))
                if j['equipo'][j['activo']]['vida'] <= 0: j['activo'] = next((i for i, m in enumerate(equipo) if m['vida'] > 0), 0)
                j['monedas'] = jd.get('monedas', 0)
                j['inventario'] = dict(tienda.inventario_nuevo(), **jd.get('inventario', {}))
                j['monedas'] = j.get('monedas', 0) + tienda.migrar_cinturon(j['inventario'])   # partidas de antes: las curaciones pasan al cinturon
                aplicar_pokemon(j, j['equipo'][j['activo']]['nombre'], j['equipo'][j['activo']]['vida'])
                actualizar_sinergia(j)
                azar = random.Random()
                a = rd['azar']; azar.setstate((a[0], tuple(a[1]), a[2]))
                rec = {'plan': rd['plan'], 'era': rd['era'], 'sala': rd['sala'], 'semilla': rd.get('semilla'), 'clima': rd['clima'], 'azar': azar,
                       'historial': rd['historial'], 'pos': rd['pos']}
                if rd.get('amistad'): rec['amistad'] = rd['amistad']     # cuantos quisieron unirse en esta era (para el minimo de amigos)
                return j, rec

            def guardar_partida(j, rec):
                """Autoguardado en la ranura de esta partida (al entrar a cada sala, al completarla y al comprar)."""
                if ranura: partidas.guardar(ranura, serializar(j, rec))

            return restaurar, guardar_partida

        restaurar, guardar_partida = armar_guardado()

        if cargada:
            j, rec = restaurar(cargada)
            viaje['en_hall'] = cargada.get('en_hall', False)
            visita = None if viaje['en_hall'] else rec['pos']
        else:
            j = crear_jugador(nombres, ESC.center, config['modo'])
            dar_pocion_maxima(j)                                     # Celebi te da la primera Pocion Maxima
            rec = mundos.nuevo_recorrido()                           # plan de la partida: eras, salas, tiendas, jefes y clima
            visita = None
        viaje['perfil'] = (cargada or {}).get('perfil') or dict(perfil_nuevo('Viajero', 'otro'), **(perfil or {}))   # las partidas de antes del hall no tienen perfil
        registrar_amigos(viaje['perfil'], j['equipo'] + j['reserva'])   # tu inicial (y los que ya tenias) son tus primeros amigos
        destino, entrada, llegada = None, 'sur', None
        reloj = pygame.time.Clock()
        while True:
            if viaje['en_hall']: nivel = crear_hall(j, viaje['perfil'])    # entre viaje y viaje
            elif visita is not None:                                 # una sala del historial: volviste, seguiste para adelante o cargaste
                registro = rec['historial'][visita]; rec['pos'] = visita
                rec['era'], rec['sala'], rec['clima'] = registro['era'], registro['sala'], registro['clima']
                nivel = crear_nivel(rec, None, registro['entrada'], j, registro, llegada)
            else: nivel = crear_nivel(rec, destino, entrada, j)
            reiniciar_jugador(j, nivel['inicio'])
            mec.nueva_sala(j, nivel)
            df, dc = generacion.PASO_LADO[nivel.get('llegada_lado') or nivel['sala']['entrada'] or 'sur']   # arranca en la puerta y camina para adentro
            j['rect'].center = (round(nivel['inicio'][0] - dc * 70), round(nivel['inicio'][1] - df * 70))
            cx, cy = camara(j)
            efectos.transicion(mundo['ef'], 'entrar', tiempo(), (j['rect'].centerx - cx, j['rect'].centery - cy))
            if nivel['tipo'] in ('tienda', 'hall', 'tesoro') or nivel['revisita']: j['llave'] = True   # tienda, hall, tesoro o sala ya hecha: las puertas ya estan abiertas
            guardar_partida(j, rec)
            reiniciar_nivel = False
            if j.pop('pocion_nueva', False): cartel(nivel, 'Celebi te dio una Poción Máxima', 2200, 'cura toda la vida (solo se puede llevar una)')
            while True:
                controles.contexto('juego')
                pygame.mouse.set_visible(False)
                apuntar(j)
                for e in controles.eventos():
                    if e.type == pygame.QUIT: return 'salir', j['nombre']
                    acciones = controles.acciones(e)
                    if 'pausa' in acciones:
                        accion_pausa = pausado(menu_pausa, ventana.copy())
                        if accion_pausa == 'cerrar': return 'salir', j['nombre']
                        if accion_pausa == 'menu': return 'menu', j['nombre']
                        j['modo'] = config['modo']; aplicar_trucos(nivel, j)
                    if 'equipo' in acciones:
                        guardar_activo(j)
                        if pausado(menus.equipo, ui, j, acciones_equipo(j)) == 'salir': return 'salir', j['nombre']
                        aplicar_trucos(nivel, j)
                    if 'interactuar' in acciones and (ia.salir_arena(j, tiempo()) or comprar_cercano(nivel, j) or hablar_amigo(nivel, j) or hablar_curandera(nivel, j) or hablar_hall(nivel, j, viaje['perfil']) or hablar_portal(nivel, j) or empujar_bloque(nivel, j)):
                        acciones = [a for a in acciones if a != 'basico1']   # si estabas comprando o hablando, no ataca
                    if 'esquivar' in acciones: esquivar(j, nivel)
                    if 'bailar' in acciones: bailar(j, nivel)
                    if 'curar' in acciones: curarse_rapido(j, nivel)
                    if 'basico1' in acciones: usar_basico(j, 0, nivel)
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and config['modo'] != 'teclas': usar_basico(j, 0, nivel)   # el clic abre el parry
                    if 'basico2' in acciones: usar_basico(j, 1, nivel)
                    if 'especial1' in acciones: usar_especial(j, 0, nivel)
                    if 'especial2' in acciones: usar_especial(j, 1, nivel)
                    if 'asist1' in acciones: usar_asistencia(j, 0, nivel)
                    if 'asist2' in acciones: usar_asistencia(j, 1, nivel)
                    for k, clave in enumerate(('poke1', 'poke2', 'poke3')):
                        if clave in acciones: cambiar_slot(j, k)
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_F1:                   # menu debug de pokemon
                            resultado_debug, elegido, espacio = pausado(debug_menu, [mi['nombre'] for mi in j['equipo']], j['activo'])
                            if resultado_debug == 'salir': return 'salir', j['nombre']
                            if elegido: equipar_debug(j, elegido, espacio)
                        if e.key == pygame.K_F2:
                            eleccion = pausado(menu_niveles, rec)
                            if eleccion == 'salir': return 'salir', j['nombre']
                            if eleccion is not None:
                                if rec['pos'] < len(rec['historial']) - 1: del rec['historial'][rec['pos'] + 1:]   # saltar corta el camino de adelante
                                mundos.ir_a(rec, *eleccion)
                                if viaje['en_hall']: viaje['en_hall'] = False; empezar_viaje(j)   # desde el hall tambien se puede saltar
                                destino, entrada, reiniciar_nivel, visita, llegada = None, 'sur', True, None, None
                                break
                if reiniciar_nivel:
                    break
                botones = pygame.mouse.get_pressed()
                if config['modo'] != 'teclas' and botones[0]: usar_basico(j, 0, nivel, apretado=False)   # mantener el clic sigue el combo
                if config['modo'] != 'teclas' and botones[2]: usar_basico(j, 1, nivel)
                if controles.hay_control():                          # con control se puede dejar apretado el ataque
                    if controles._boton(controles.perfil('control').get('basico1', '')): usar_basico(j, 0, nivel, apretado=False)
                    if controles._boton(controles.perfil('control').get('basico2', '')): usar_basico(j, 1, nivel)
                resultado = actualizar_nivel(nivel, j) if tiempo() >= nivel.get('pausa_hasta', 0) else None   # pausa de impacto: solo se dibuja
                if nivel['tipo'] == 'hall': actualizar_residentes(nivel)
                dibujar_objetos(nivel, j, rec)
                if resultado is None: actualizar_evolucion(nivel, j, controles.mantiene('evolucionar'))
                if nivel.pop('guardar', False): guardar_partida(j, rec)
                if resultado == 'siguiente':
                    puerta = nivel['salida']
                    guardar_activo(j)
                    if puerta['destino']['tipo'] == 'viaje':                # el portal del hall: otro viaje desde la Era Glacial
                        viaje['en_hall'] = False
                        empezar_viaje(j)
                        destino, entrada, visita, llegada = None, 'sur', None, None
                        break
                    if puerta.get('atras'):                              # para atras: a la sala anterior, por la puerta por la que habias salido
                        visita = rec['pos'] - 1; llegada = rec['historial'][visita]['salida']; break
                    if rec['pos'] < len(rec['historial']) - 1:           # para adelante por una sala que ya hiciste
                        visita = rec['pos'] + 1; llegada = None; break
                    nivel['registro']['salida'] = puerta['lado']
                    if puerta['destino']['tipo'] == 'fin' or not mundos.avanzar(rec):
                        pausado(pantalla_final); return 'menu', j['nombre']
                    if nivel.get('portal') and rec['era'] != nivel['sala']['era']:     # cruzaste el portal de Celebi: el tunel del tiempo hasta la era nueva
                        if pausado(menus.cruzar_portal, ui, mundos.ERAS[rec['era']]['nombre'], j['nombre']) == 'salir': return 'salir', j['nombre']
                        if dar_pocion_maxima(j): j['pocion_nueva'] = True        # Celebi te repone la Pocion Maxima en cada era
                    destino, entrada = puerta['destino'], generacion.OPUESTO[puerta['lado']]   # salis por el norte: entras por el sur
                    visita, llegada = None, None
                    break
                if resultado == 'muerte':                                 # cayo todo el equipo: se desmaya (Faint) y Celebi te lleva al hall
                    if caida(nivel, j, rec) == 'salir': return 'salir', j['nombre']
                    j = volver_al_hall(j, viaje['perfil'])
                    rec = mundos.nuevo_recorrido()                       # el proximo viaje arranca de cero
                    viaje['en_hall'] = True
                    destino, entrada, visita, llegada = None, 'sur', None, None
                    break
                reloj.tick(60)

    equipo_menu = []                                     # vacio: se elige el inicial. El debug (F1 + Konami) puede armar uno
    ui = {'ventana': ventana, 'W': W, 'H': H, 'presentar': pantalla.presentar, 'raton': pantalla.raton, 'a_logico': pantalla.a_logico,
          'retrato': retrato_menu, 'config': config, 'aplicar_pantalla': lambda: pantalla.aplicar(config), 'aplicar_volumen': aplicar_volumen}
    estado = 'intro'

    while True:
        if estado == 'intro':                            # del cielo baja la camara hasta la isla
            if menus.intro(ui) == 'salir': pygame.quit(); sys.exit()
            estado = 'titulo'
        if estado == 'titulo':
            if pantalla_titulo() == 'salir': pygame.quit(); sys.exit()
            estado = 'menu'
            continue
        accion = menu_principal(equipo_menu)
        if accion == 'cerrar': opciones.guardar(config); pygame.quit(); sys.exit()
        if accion == 'titulo': estado = 'titulo'
        if accion == 'jugar':
            eleccion = menus.elegir_partida(ui, partidas.resumenes())           # 3 ranuras de guardado
            if eleccion == 'salir': pygame.quit(); sys.exit()
            if eleccion:
                modo, ranura = eleccion
                cargada, inicial, perfil = None, None, None
                if modo == 'continuar':
                    cargada = partidas.cargar(ranura)
                    if not cargada: menus.preguntar(ui, 'No se pudo leer la partida ' + str(ranura), ['Ok']); continue
                elif any(equipo_menu):                                  # equipo armado con el debug (F1): sin viaje temporal
                    inicial = [n for n in equipo_menu if n]
                    partidas.borrar(ranura)
                else:                                                   # partida nueva: Celebi te encuentra flotando en el tiempo
                    datos_viaje = menus.viaje_temporal(ui)              # nombre, genero e inicial (Mudkip, Torchic, Riolu o Natu)
                    if datos_viaje == 'salir': pygame.quit(); sys.exit()
                    if not datos_viaje: continue
                    inicial = [datos_viaje['inicial']]
                    perfil = {'nombre': datos_viaje['nombre'], 'genero': datos_viaje['genero']}
                    partidas.borrar(ranura)
                resultado, _ = jugar(inicial, config, ranura, cargada, perfil)   # si cae el equipo no termina: sigue en el hall
                pygame.mouse.set_visible(True)
                if resultado == 'salir': opciones.guardar(config); pygame.quit(); sys.exit()
        if accion == 'pokedex':
            if pokedex() == 'salir': pygame.quit(); sys.exit()
        if accion == 'ajustes' and menus.ajustes(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'glosario' and menus.glosario(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'ataques' and menus.ataques(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'salir' and confirmar('¿Seguro que quieres salir?'): opciones.guardar(config); pygame.quit(); sys.exit()

if __name__ == '__main__':
    main()
