import pygame
import random
import math
import sys
import time
import datos
from datos import mundos, mts, tienda
from sistema import controles, pantalla, opciones, partidas, animaciones
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
    fuente = pygame.font.Font(None, 24)

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
            f = pygame.font.Font(None, 32)
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
            f_titulo, f_texto = pygame.font.Font(None, 36), pygame.font.Font(None, 26)
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

        def debug_menu(equipo, activo):
            """Menu debug (F1): grilla con todos los pokemon jugables (con el Konami tambien los jefes).
            Devuelve (resultado, nombre elegido, espacio)."""
            pygame.mouse.set_visible(True)
            lista = list(JUGABLES)                           # con el codigo Konami adentro de este menu se suman los jefes
            scroll = 0
            botones = []
            f_titulo = pygame.font.Font(None, 32)
            while True:
                columnas, bw, bh, bn, sy = 4, 210, 62, 28, 18
                filas = math.ceil(len(lista) / columnas)
                max_scroll = max(0, 80 + filas * (bh + bn + sy) - H)

                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir', None, None
                    if e.type == controles.KONAMI:
                        lista = list(JUGABLES) + [n for n, d in pokemones.items() if d.get('boss') and tiene_sprites(n) and n not in JUGABLES]
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
                ventana.blit(f_titulo.render('MENU DEBUG', True, 'white'), (25, 15))
                ventana.blit(fuente.render('F1 o ESC para cerrar - rueda del mouse para desplazarte - clic para elegir espacio', True, (200, 200, 200)), (25, 45))
                for i, nombre in enumerate(lista):
                    x = 30 + i % columnas * 240
                    y = 85 + i // columnas * (bh + bn + sy) - scroll
                    r = pygame.Rect(x, y, bw, bh)
                    nr = pygame.Rect(x, y + bh, bw, bn)
                    if r.bottom < 65 or nr.top > H:
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
                    botones.append((r, nombre))
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
            f_grande, f_med, f_peq = pygame.font.Font(None, 96), pygame.font.Font(None, 30), pygame.font.Font(None, 18)
            reloj_t = pygame.time.Clock()
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
                menus.fondo_menu(ui, pygame.time.get_ticks())
                t = f_grande.render('POKEMANIC', True, 'white')
                ventana.blit(f_grande.render('POKEMANIC', True, (20, 40, 25)), t.get_rect(center=(W // 2 + 4, 134)))
                ventana.blit(t, t.get_rect(center=(W // 2, 130)))
                p = f_med.render('presione cualquier tecla para empezar', True, 'white')
                franja = p.get_rect(center=(W // 2, H - 75)).inflate(40, 42)      # franja oscura para que se lea sobre el fondo
                velo = pygame.Surface(franja.size, pygame.SRCALPHA); velo.fill((0, 0, 0, 120)); ventana.blit(velo, franja)
                ventana.blit(p, p.get_rect(center=(W // 2, H - 85)))
                s = f_peq.render('(menos esc, es para salir)', True, 'white')
                ventana.blit(s, s.get_rect(center=(W // 2, H - 58)))
                pantalla.presentar(); reloj_t.tick(60)

        def menu_principal(equipo):
            """Menu principal: jugar, pokedex, ajustes, glosario y salir. Devuelve la opcion elegida."""
            pygame.mouse.set_visible(True)
            orden = ['jugar', 'pokedex', 'ajustes', 'glosario', 'salir']
            botones = {o: pygame.Rect(100, 170 + i * 80, 300, 60) for i, o in enumerate(orden[:4])}
            botones['salir'] = pygame.Rect(0, 0, 84, 84)
            botones['salir'].center = (W - 100, H - 80)
            f_titulo, f_boton, f_info = pygame.font.Font(None, 64), pygame.font.Font(None, 44), pygame.font.Font(None, 24)
            seleccion = 0
            reloj_m = pygame.time.Clock()
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
                menus.fondo_menu(ui, pygame.time.get_ticks())
                t = f_titulo.render('POKEMANIC', True, 'white')
                ventana.blit(t, t.get_rect(topright=(W - 60, 50)))
                for o in orden[:4]:
                    velo = pygame.Surface(botones[o].size, pygame.SRCALPHA); velo.fill((0, 0, 0, 110)); ventana.blit(velo, botones[o])
                    pygame.draw.rect(ventana, 'white', botones[o], 3)
                    txt = f_boton.render(o, True, 'white')
                    ventana.blit(txt, txt.get_rect(center=botones[o].center))
                cx, cy = botones['salir'].center
                pygame.draw.circle(ventana, 'white', (cx, cy), 40, 3)
                pygame.draw.line(ventana, 'white', (cx + 16, cy), (cx - 12, cy), 4)
                pygame.draw.line(ventana, 'white', (cx - 12, cy), (cx - 2, cy - 10), 4)
                pygame.draw.line(ventana, 'white', (cx - 12, cy), (cx - 2, cy + 10), 4)
                pygame.draw.line(ventana, 'white', (cx - 21, cy - 14), (cx - 21, cy + 14), 4)
                dibujar_esquinas(ventana, botones[orden[seleccion]].inflate(10, 10) if seleccion < 4 else botones['salir'].inflate(6, 6))
                ventana.blit(f_info.render('Combate: ' + config['modo'] + ('   (control conectado)' if controles.hay_control() else ''), True, 'white'), (20, H - 34))
                pantalla.presentar(); reloj_m.tick(60)

        def menu_pausa(fondo):
            """Menu de pausa sobre la partida congelada ('fondo'). Devuelve 'seguir', 'menu' o 'cerrar'."""
            pygame.mouse.set_visible(True)
            tinte = pygame.Surface((W, H), pygame.SRCALPHA)
            tinte.fill((110, 110, 110, 165))
            opciones = [('seguir', 'seguir jugando'), ('ajustes', 'ajustes'), ('pokedex', 'pokedex'), ('glosario', 'glosario'), ('salir', 'salir')]
            botones = [pygame.Rect(150, 150 + i * 72, 320, 56) for i in range(len(opciones))]
            f_titulo, f_boton = pygame.font.Font(None, 80), pygame.font.Font(None, 38)
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
                if accion == 'pokedex':
                    if pokedex() == 'salir': return 'cerrar'
                if accion == 'salir' and confirmar('¿Volver al menú principal?'): return 'menu'
                ventana.blit(fondo, (0, 0))
                ventana.blit(tinte, (0, 0))
                ventana.blit(f_titulo.render('PAUSA', True, (25, 25, 25)), (150, 95))
                for i, r in enumerate(botones):
                    pygame.draw.rect(ventana, (35, 35, 35), r)
                    pygame.draw.rect(ventana, 'white', r, 3)
                    txt = f_boton.render(opciones[i][1], True, 'white')
                    ventana.blit(txt, txt.get_rect(center=r.center))
                dibujar_esquinas(ventana, botones[seleccion].inflate(12, 12))
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
            mec = a['mecanica']
            if mec == 'impacto': return 'golpe de área en el punto apuntado (daño ' + str(a['daño']) + ', radio ' + str(a['area']) + ')'
            if mec == 'escudo': return 'el activo recibe solo el 25% del daño durante ' + str(a['duracion'] // 1000) + ' s'
            if mec == 'furia': return 'daño x1.6 y recargas x0.7 durante ' + str(a['duracion'] // 1000) + ' s'
            if mec == 'carrera': return 'velocidad x1.6 y sprint sin gasto durante ' + str(a['duracion'] // 1000) + ' s'
            if mec == 'curar': return 'cura el ' + str(a['porcentaje']) + '% de la vida del activo'
            if mec == 'desvanecer': return 'les saca el ' + str(a['porcentaje']) + '% de la vida a los enemigos comunes en un radio de ' + str(a['area']) + ' y el ' + str(a['porcentaje_jefe']) + '% a un jefe'
            return 'aplica ' + str((a.get('efecto') or {}).get('tipo')) + ' a todos los enemigos cercanos'

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
                for i, (n, dat) in enumerate(g['especiales']): texto(['Shift: ', 'R: '][i] + n.replace('_', ' ').title() + ' - ' + descripcion_movimiento(dat))
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
            f_nombre, f_sec, f_txt = pygame.font.Font(None, 42), pygame.font.Font(None, 28), pygame.font.Font(None, 22)
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
            f_titulo = pygame.font.Font(None, 32)
            while True:
                columnas, bw, bh, bn, sy = 4, 210, 62, 28, 18
                filas = math.ceil(len(entradas) / columnas)
                max_scroll = max(0, 80 + filas * (bh + bn + sy) - H)
                for e in controles.eventos():
                    if e.type == pygame.QUIT:
                        return 'salir'
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                        return None
                    if e.type == pygame.MOUSEWHEEL:
                        scroll = max(0, min(scroll - e.y * 60, max_scroll))
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for r, i in botones:
                            if r.collidepoint(pantalla.a_logico(e.pos)):
                                if ver_ficha(entradas, i) == 'salir': return 'salir'
                                break
                ventana.fill((20, 20, 20))
                botones = []
                ventana.blit(f_titulo.render('POKEDEX', True, 'white'), (25, 15))
                ventana.blit(fuente.render('ESC para volver - rueda del mouse para desplazarte - clic para ver la ficha', True, (200, 200, 200)), (25, 45))
                for i, nombre in enumerate(entradas):
                    x = 30 + i % columnas * 240
                    y = 85 + i // columnas * (bh + bn + sy) - scroll
                    r = pygame.Rect(x, y, bw, bh)
                    nr = pygame.Rect(x, y + bh, bw, bn)
                    if r.bottom < 65 or nr.top > H:
                        continue
                    pygame.draw.rect(ventana, (200, 200, 200), r)
                    pygame.draw.rect(ventana, (50, 50, 50), nr)
                    img = retrato_menu(nombre, bh - 12)
                    if img: ventana.blit(img, (x + 6, y + 6))
                    ventana.blit(fuente.render(nombre.replace('_', ' ').title(), True, 'black'), (x + bh, y + 22))
                    numero = pokemones[nombre].get('pokedex')
                    tipos_txt = ' / '.join(normalizar_tipo(t) for t in pokemones[nombre].get('tipo', []))
                    ventana.blit(fuente.render(('#' + str(numero) + ' - ' if numero else '') + tipos_txt, True, 'white'), (x + 8, y + bh + 5))
                    botones.append((r, i))
                pantalla.presentar()

        return pokedex, descripcion_asistencia

    pokedex, descripcion_asistencia = armar_pokedex()

    def jugar(nombres, config, ranura=None, cargada=None):
        """Una partida entera: arma el equipo, recorre las salas una por una y devuelve como termino
        ('menu', 'salir' o 'juego_terminado') junto con el pokemon activo.
        Adentro se arman por grupos (reglas, equipo, movimiento, ataques, enemigos, salas, dibujo, extras) las funciones que usa el bucle."""
        pausa = {'total': 0}

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
        VEL_ORILLA = 3.5                            # pixeles por frame al nadar hasta la orilla (cambiaste en el agua a uno que no nada)
        trucos = config['trucos']                   # menu secreto (Konami): vida infinita, sin recarga...
        DISTANCIA_COMPRA = 95                       # que tan cerca de una vitrina hay que estar para comprar
        VEL_P_ENEMIGO = 8                           # balas del anillo de los jefes (las de los tiradores van en ia.py)
        DIST_P_ENEMIGO = 250
        DAÑO_ENEMIGO = 10                           # daño base de un enemigo (se escala con la era y la sala)
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
                miembro.update({'vida': vida, 'max_vida': vida, 'asist': asistencia_de(nombre), 'asist_listo': 0})
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
                return mts.MTS[nombre]['nombre'][3:] if nombre in mts.MTS else nombre.replace('_', ' ').title()

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
                g = juego_de(m)
                m['max_vida'] = progreso.vida_max(m)
                rect = pygame.Rect(0, 0, g['ancho'], g['alto'])
                rect.center = centro or j['rect'].center
                j.update({'nombre': nombre, 'datos': pokemones[nombre], 'juego': g, 'tipos': g['tipos'], 'rol': g['rol'], 'max_vida': m['max_vida'],
                          'mults': progreso.multiplicadores(m), 'nivel': m['nivel'],
                          'vida': m['max_vida'] if vida is None else min(vida, m['max_vida']), 'velocidad': g['velocidad'], 'tamaño': g['tamaño'],
                          'ancho': g['ancho'], 'alto': g['alto'], 'rect': rect, 'ultimo_golpe': -1000, 'ultimo_proyectil': -1000, 'esp_ultimo': [-100000, -100000],
                          'atacando': False, 'anim_ataque': None, 'embestida': None, 'animador': AnimadorPokemon(nombre, rect, g['tamaño'])})

            def crear_jugador(nombres, centro, modo):
                """Arrancas solo con tu inicial; el resto del equipo se suma por amistad."""
                equipo = [n for n in dict.fromkeys(nombres) if n in pokemones][:3] or ['electrike']
                j = {'modo': modo, 'uso': 'teclas' if modo == 'teclas' else 'mouse', 't_mouse': 0, 'pos_mouse': pantalla.raton(), 'ultimo_dir': (0, 1), 'direccion': 'sur', 'moviendose': False, 'corriendo': False, 'llave': False, 'energia': ENERGIA_MAX, 'agotado': False, 'buffs': {},
                     'resto': [0.0, 0.0], 'aim': (0.0, 1.0), 'dir_ataque': 0, 'ultimo_cambio': -10000, 'equipo': [crear_miembro(n) for n in equipo], 'activo': 0, 'sinergia': {},
                     'monedas': 0, 'inventario': tienda.inventario_nuevo(), 'entorno': {}, 'oculto': False, 'inercia': [0.0, 0.0], 'reserva': [],
                     'frio': 0.0, 'congelado_hasta': 0, 'resto_iman': [0.0, 0.0]}
                aplicar_pokemon(j, equipo[0], centro=centro)
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
                j['activo'] = indice; j['ultimo_cambio'] = ahora; j['buffs'] = {}
                aplicar_pokemon(j, m['nombre'], m['vida'])
                actualizar_sinergia(j)
                efectos.cambio(mundo['ef'], *j['rect'].center)
                if mundo['ent']:                                  # cambiaste en el agua a uno que no nada: va nadando hasta la orilla
                    j['a_la_orilla'] = entorno.orilla(mundo['ent'], j['rect'], j['tipos'])
                    if j['a_la_orilla'] and mundo.get('nivel'): cartel(mundo['nivel'], m['nombre'].replace('_', ' ').title() + ' nada hasta la orilla')
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
                return j['velocidad'] * mult_buff(j, 'velocidad') * (1 + j['sinergia'].get('velocidad', 0)) * sprint * mod(j, 'velocidad') * j['mults']['velocidad']

            return (crear_miembro, juego_de, nombre_mov, datos_mov, actualizar_sinergia, aplicar_pokemon, crear_jugador, guardar_activo,
                    cambiar_slot, equipar_debug, reiniciar_jugador, mult_buff, velocidad_actual)

        (crear_miembro, juego_de, nombre_mov, datos_mov, actualizar_sinergia, aplicar_pokemon, crear_jugador, guardar_activo, cambiar_slot,
         equipar_debug, reiniciar_jugador, mult_buff, velocidad_actual) = armar_equipo()

        def armar_movimiento():
            """Mover al jugador, la camara y hacia donde apunta."""
            def mover_jugador(j, piedras):
                """Mueve al jugador segun las teclas o la palanca: correr gasta energia, el hielo resbala y las cintas empujan."""
                if tiempo() < max(j['congelado_hasta'], j.get('atrapado_hasta', 0)):
                    j['moviendose'] = j['corriendo'] = False; j['inercia'] = [0.0, 0.0]; return
                dx, dy = controles.direccion()                   # teclas del perfil, palanca o cruz del control
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
                    j['energia'] = min(ENERGIA_MAX, j['energia'] + REGEN_ENERGIA * mod(j, 'regen') * (1 + j['sinergia'].get('energia', 0)))
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
                datos['daño'] = round(base * j['juego']['mult_daño'] * mult_buff(j, 'daño') * (1 + j['sinergia'].get('daño', 0)) * extra * stat
                                      * (100 if trucos.get('golpe_letal') else 1))
                return datos

            def enfriamiento_de(j, datos):
                """Espera (ms) antes de poder repetir el ataque, con rol, sinergia, buffs y terreno."""
                try: base = max(0, int(float(datos.get('enfriamiento', 300))))
                except (TypeError, ValueError): base = 300
                if trucos.get('sin_enfriamiento'): return 0
                return round(base * j['juego']['mult_enfriamiento'] * (1 - j['sinergia'].get('enfriamiento', 0)) * mult_buff(j, 'enfriamiento') * mod(j, 'enfriamiento'))

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
                return bool(j['embestida'] or j.get('esquive') or j.get('a_la_orilla'))

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
                espera = enfriamiento_de(j, {'enfriamiento': COMBO['espera']})
                iniciar_ataque(j, 'cuerpo', espera * 2)
                tocados = golpear(j, datos, objetivos, nivel['efectos'], COMBO['arco'][paso], COMBO['alcance'][paso])
                j['ultimo_golpe'] = ahora
                if paso == 2:                                           # remate: recuperacion un poco mas larga y vuelve al primer golpe
                    j['combo'] = 0; j['combo_listo'] = ahora + enfriamiento_de(j, {'enfriamiento': COMBO['recuperacion']})
                    nivel['temblor'] = max(nivel['temblor'], ahora + 90)
                else: j['combo'] = paso + 1; j['combo_listo'] = ahora + espera
                if contra and tocados: j['contra_hasta'] = 0; cartel(nivel, 'Contraataque!', 600)
                if carrera and tocados: cartel(nivel, 'Golpe en carrera!', 600)
                if tocados:
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
                if not gratis and (j['agotado'] or j['energia'] < costo): cartel(nivel, 'Sin energia para esquivar', 500); return
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
                j['contra_hasta'] = tiempo() + ESQUIVE['contra_dura']
                efectos.destello(mundo['ef'], *j['rect'].center)
                if mundo.get('nivel'): cartel(mundo['nivel'], 'Esquive perfecto! (tu proximo golpe es un contraataque)', 900)

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
                efectos.cambio(mundo['ef'], *donde)                              # destello blanco
                nivel['temblor'] = max(nivel['temblor'], ahora + 120)            # sacudoncito de pantalla
                cartel(nivel, 'Parry!', 700)

            def usar_especial(j, indice, nivel):
                """Especial 1 o 2 (Shift / R): proyectil, golpe, area, embestida, buff o cura, segun el movimiento."""
                nombre, base = j['juego']['especiales'][indice]
                datos = preparar(j, base)
                if not descongelar(j, datos.get('tipo')): return
                forma = datos.get('forma', 'proyectil')
                ahora = tiempo(); enfriamiento = enfriamiento_de(j, datos)
                if ocupado(j) or ahora - j['esp_ultimo'][indice] < enfriamiento: return
                j['esp_ultimo'][indice] = ahora
                iniciar_ataque(j, forma, enfriamiento)
                entorno.al_usar_movimiento(nivel['ent'], nombre, ahora)     # ej. viento hielo trae granizo
                objetivos = objetivos_de(nivel)
                if forma == 'proyectil': lanzar(j, datos, nivel['proyectiles_pokemon'])
                elif forma == 'cuerpo': golpear(j, datos, objetivos, nivel['efectos'])
                elif forma == 'area': area_efecto(j, datos, objetivos, nivel['efectos'])
                elif forma == 'embestida': iniciar_embestida(j, datos)
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
                entorno.al_usar_movimiento(nivel['ent'], a['nombre'], ahora)   # hidrobomba trae lluvia, llamarada sol, trueno tormenta...
                fuerza = progreso.multiplicadores(m)['especial']                   # la asistencia escala con el nivel del que la tira
                if mec == 'impacto':
                    datos = {'tipo': a['tipo'], 'daño': round(a['daño'] * a['mult_daño'] * fuerza), 'area': a['area'], 'retroceso': 30, 'efecto': a['efecto']}
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
                    datos = {'tipo': 'normal', 'daño': round(a['daño'] * fuerza), 'area': a['area'], 'retroceso': 0, 'efecto': a['efecto']}
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

            def dañar_jugador(j, daño, tipo=None, evitable=True):
                """Le saca vida al jugador: tipos, buffs, sinergia, tienda y defensa (nada si esta el truco de vida infinita).
                evitable: golpes, balas y rayos se esquivan (mientras dura la invulnerabilidad del esquive no pegan y es esquive perfecto);
                el piso que quema o lastima no."""
                try: daño = max(0, float(daño))
                except (TypeError, ValueError): daño = 0
                if evitable and daño > 0 and tiempo() < j.get('inv_hasta', 0): esquive_perfecto(j); return
                if tipo: daño = daño_con_tipo(daño, tipo, j['tipos'])
                daño *= mult_buff(j, 'defensa') * (1 - j['sinergia'].get('defensa', 0)) * mod(j, 'defensa') * j['mults']['defensa']
                if trucos.get('vida_infinita'): return
                j['vida'] = max(0, j['vida'] - daño)
                if tipo and normalizar_tipo(tipo) == 'hielo' and 'hielo' not in j['tipos'] and tiempo() >= j['congelado_hasta']:   # los de hielo no se congelan
                    j['frio'] = min(FRIO_MAX, j['frio'] + FRIO_POR_DAÑO * daño / max(1, j['max_vida']))

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
                if obj.get('contragolpe_hasta', 0) > tiempo(): daño = round(daño * PARRY['contragolpe'])   # le hiciste parry: pega mas
                elif obj.get('estado') == 'dormir' and obj.get('estado_hasta', 0) > tiempo() and daño > 0:
                    daño = round(daño * 1.5); obj['estado'] = None; obj['estado_hasta'] = 0   # golpe a uno dormido: pega mas y lo despierta
                if obj.get('mult_recibido', 1.0) != 1.0 and daño: daño = max(1, round(daño * obj['mult_recibido']))   # coraza, Lento Inicio...
                obj['vida'] = max(0, obj['vida'] - daño)
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
                    recibir_ataque, intentar_parry, parry_exitoso, esquivar, actualizar_esquive, ocupado)

        (enfriamiento_de, actualizar_embestida, usar_basico, usar_especial, usar_asistencia, actualizar_jugador, dañar_jugador,
         recibir_ataque, intentar_parry, parry_exitoso, esquivar, actualizar_esquive, ocupado) = armar_ataques()

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
                vida = round(100 * progreso.crecimiento(nombre, nv, 'hp'))
                e = {'tipo': tipo, 'nombre': nombre, 'nivel': nv, 'animador': AnimadorPokemon(nombre, r, visual), 'direccion': 'sur', 'prev': r.center, 'rect': r,
                     'vida': vida, 'max_vida': vida, 'daño': round(DAÑO_ENEMIGO * progreso.crecimiento(nombre, nv, 'attack')), 'color': COLORES_TIPO.get(tipo, (150, 150, 150)), 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0, 'entorno': {}}
                ia.preparar(e, estilo)
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
                        cartel(nivel, 'Regigigas llama a los Regis!', 1600)

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
                r.center = centro
                return ok

            def actualizar_estado(e):
                """Estados alterados: la quemadura saca vida cada 0,7 s; al vencerse el estado se borra."""
                ahora = tiempo()
                if e['estado'] == 'quemar' and e['proximo_estado'] <= ahora < e['estado_hasta']:
                    e['vida'] = max(0, e['vida'] - 3); e['proximo_estado'] = ahora + 700
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
                    else: dañar_jugador(j, proyectil['daño'], proyectil.get('tipo'))

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
                f_titulo = pygame.font.Font(None, 32)
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
                nivel['carteles'].append({'texto': texto, 'sub': subtitulo, 'inicio': ahora, 'hasta': ahora + duracion, 'grande': grande})

            def repartir(total, partes):
                """Divide la cantidad de enemigos en oleadas (la primera un poco mas grande)."""
                base = [total // partes] * partes
                for i in range(total % partes): base[i] += 1
                return base

            def crear_nivel(rec, destino, entrada, j, registro=None, llegada=None):
                """Arma la sala actual del recorrido: mapa, entorno, puertas con su destino, enemigos y el cartel de entrada.
                registro: la sala ya estaba en el historial (volviste o cargaste la partida): se arma igual que la primera vez
                y, si ya la habias completado, sin enemigos y con las puertas abiertas. llegada: lado de la puerta por la que entras
                cuando volves para atras (apareces en la puerta por la que habias salido)."""
                nuevo = registro is None
                if nuevo:
                    era, tipo = rec['era'], mundos.tipo_sala(rec)
                    destinos = mundos.destinos_siguientes(rec, random)
                    if tipo == 'tienda': destinos = destinos[:2]; lados = ['oeste', 'este'][:len(destinos)]; variante = None
                    elif tipo in ('jefe', 'regi', 'final'): destinos = destinos[:1]; lados = ['norte']; variante = None
                    else:
                        variantes = mundos.ERAS[era]['variantes']
                        variante = destino['variante'] if destino and destino.get('variante') in variantes else random.choice(list(variantes))
                        lados = random.sample([l for l in generacion.LADOS if l != entrada], len(destinos))
                    registro = {'era': era, 'sala': rec['sala'], 'tipo': tipo, 'semilla': random.random(), 'variante': variante, 'entrada': entrada,
                                'lados': lados, 'destinos': destinos, 'clima': rec['clima'], 'completada': False, 'salida': None, 'vitrinas': None}
                    rec['historial'].append(registro); rec['pos'] = len(rec['historial']) - 1
                era, tipo, semilla = registro['era'], registro['tipo'], registro['semilla']
                if tipo == 'tienda': sala = generacion.generar_tienda(era, registro['lados'], semilla)
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
                         'efectos': [], 'verdes': [], 'puertas': sala['puertas'], 'llave': None, 'completado': tipo == 'tienda' or hecha, 'monedas': [], 'carteles': [],
                         'oleadas': [], 'apariciones': [], 'vitrinas': [], 'salida': None, 'nivel_enemigos': progreso.nivel_de_sala(era, registro['sala'], tipo),
                         'amigo': None, 'entrando_hasta': tiempo() + DURACION_ENTRADA, 'saliendo': None, 'frame': 0, 'temblor': 0, 'llegada': None,
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
                    if registro['vitrinas'] is None:
                        tipos_equipo = {normalizar_tipo(t) for m in j['equipo'] for t in pokemones[m['nombre']].get('tipo', [])}
                        necesita = {r['objeto'] for m in j['equipo'] for r in progreso.requisitos(m['nombre']) if 'objeto' in r}
                        items = tienda.surtido(random, tipos_equipo, sala['vitrinas'], [m['nombre'] for m in j['equipo']], necesita)
                        registro['vitrinas'] = [[i_, False] for i_ in items]
                    nivel['vitrinas'] = [dict(v, item=i_, vendido=vendido) for v, (i_, vendido) in zip(sala['vitrinas'], registro['vitrinas'])]
                    titulo = 'Tienda de Chikorita'
                elif hecha:
                    titulo = (sala.get('variante') or tipo).capitalize() if tipo == 'combate' else mundos.jefe_de(era, tipo).title()
                    titulo += ' (completada)'
                elif tipo in ('jefe', 'regi', 'final'):
                    nombre = mundos.jefe_de(era, tipo)
                    nv = nivel['nivel_enemigos']
                    vida = round((VIDA_JEFE if tipo == 'jefe' else VIDA_REGI * (1.5 if tipo == 'final' else 1)) * progreso.crecimiento(nombre, nv, 'hp'))
                    nivel['jefe'] = crear_jefe(nivel, nombre, vida, nv)
                    titulo = nombre.title()
                else:
                    total = max(3, round(esc['cantidad'] * tienda.factor_enemigos(j['inventario'])))
                    partes = 1 if registro['sala'] < 3 else random.choice((2, 2, 3))
                    oleadas = repartir(total, partes)
                    nivel['enemigos'] = [crear_enemigo(nivel) for _ in range(oleadas[0])]   # la primera oleada ya esta (sin verte todavia)
                    nivel['oleadas'] = oleadas[1:]
                    titulo = sala['variante'].capitalize()
                clima_txt = 'Interior' if ent['clima'] is None else entorno.CLIMAS[ent['clima']]['nombre']
                sub = datos_era['nombre'] + '  -  Sala ' + str(registro['sala'] + 1) + '/' + str(mundos.salas_de(rec, era)) + '  -  ' + clima_txt
                cartel(nivel, titulo, 2800 if not hecha else 1600, sub, grande=True)
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
                cartel(nivel, 'Arceus desaparecio...', 2400, 'algo cae del cielo', grande=True)
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
                cartel(nivel, 'Arceus Beta', 2800, 'flota sobre el vacio delante tuyo', grande=True)
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

            def soltar_monedas(nivel, j, x, y, cantidad):
                """Deja una pila de monedas en el piso (el amuleto moneda de la tienda las multiplica)."""
                cantidad = max(1, round(cantidad * tienda.mult(j['inventario'], 'monedas')))
                nivel['monedas'].append({'x': float(x), 'y': float(y), 'valor': cantidad})

            def tecla_de(accion):
                """Tecla asignada a una accion en el perfil de teclado, para mostrarla en los carteles."""
                return str(controles.perfil('teclado').get(accion, '?')).upper()

            def ganar_xp(nivel, j, cantidad):
                """Experiencia: el que pelea toda, los de la banca la mitad. Avisa si alguien sube de nivel o ya puede evolucionar."""
                for i, m in enumerate(j['equipo']):
                    subidos = progreso.dar_xp(m, cantidad if i == j['activo'] else cantidad * progreso.PARTE_BANCA)
                    if not subidos: continue
                    antes = m['max_vida']; m['max_vida'] = progreso.vida_max(m)
                    if i == j['activo']:
                        j['vida'] += m['max_vida'] - antes; j['max_vida'] = m['max_vida']; j['mults'] = progreso.multiplicadores(m); j['nivel'] = m['nivel']
                        efectos.nivel(mundo['ef'], *j['rect'].center)
                    else: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] - antes)
                    cartel(nivel, m['nombre'].title() + ' subio al nivel ' + str(m['nivel']) + '!')   # si ya puede evolucionar, pregunta ofrecer_evolucion

            def quiza_amigo(nivel, j, e):
                """A veces un pokemon derrotado quiere unirse a vos (no se captura: se hace tu amigo). Uno por sala como mucho."""
                if nivel['amigo'] or e.get('jefe') or e.get('mini'): return
                if random.random() >= progreso.prob_unirse(e['nombre'], e['nivel'], j['nivel'], tienda.mult(j['inventario'], 'amistad')): return
                e['vida'] = 1; e['amigable'] = True; e['aviso'] = None; e['embestida_ia'] = None
                if not e['animador'].cambiar('sit', 0, True): e['animador'].cambiar('idle', 0, True)
                nivel['amigo'] = e
                cartel(nivel, e['nombre'].title() + ' quiere ser tu amigo! (acercate y apreta ' + tecla_de('interactuar') + ')', 2400)

            def hablar_amigo(nivel, j):
                """Interactuar con el que quiere unirse. Devuelve True si estaba cerca."""
                e = nivel['amigo']
                if not e or math.hypot(e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery) > 90: return False
                nombre = e['nombre'].title()
                r = pausado(menus.preguntar, ui, nombre + ' (Nv ' + str(e['nivel']) + ') quiere unirse a tu equipo!', ['Que se una', 'Dejarlo ir'],
                            'tu equipo: ' + ', '.join(m['nombre'].title() for m in j['equipo']))
                if r == 0:
                    nuevo = crear_miembro(e['nombre'], e['nivel'])
                    if len(j['equipo']) < 3: j['equipo'].append(nuevo); actualizar_sinergia(j); cartel(nivel, nombre + ' se unio a tu equipo!')
                    else: j['reserva'].append(nuevo); cartel(nivel, nombre + ' se fue a la reserva (' + tecla_de('equipo') + ' > Reserva)', 2200)
                    efectos.corazones(mundo['ef'], *e['rect'].center)
                elif r == 1: cartel(nivel, nombre + ' se fue')
                else: return True
                nivel['amigo'] = None
                return True

            def premio_jefe(nivel, j, jefe):
                """Los jefes dejan una MT que tu equipo pueda aprender (y el Regi, ademas, un objeto de evolucion si alguien lo necesita)."""
                inv = j['inventario']['objetos']
                posibles = sorted({k for m in j['equipo'] for k in mts.aprendibles(m['nombre'])}) or list(mts.MTS)
                mt = random.choice(posibles)
                inv[mt] = inv.get(mt, 0) + 1
                cartel(nivel, 'Conseguiste ' + mts.MTS[mt]['nombre'] + '!', 2200)
                necesita = [r['objeto'] for m in j['equipo'] for r in progreso.requisitos(m['nombre']) if 'objeto' in r]
                if nivel['tipo'] != 'jefe' and necesita:
                    obj = random.choice(necesita); inv[obj] = inv.get(obj, 0) + 1
                    cartel(nivel, 'Conseguiste ' + tienda.ITEMS[obj]['nombre'] + '!', 2400)

            def vitrina_cercana(nivel, j):
                """La vitrina sin vender mas cerca del jugador (si esta al alcance)."""
                libres = [v for v in nivel['vitrinas'] if not v['vendido']]
                if not libres: return None
                v = min(libres, key=lambda v: math.hypot(v['pos'][0] - j['rect'].centerx, v['pos'][1] - j['rect'].centery))
                return v if math.hypot(v['pos'][0] - j['rect'].centerx, v['pos'][1] - j['rect'].centery) <= DISTANCIA_COMPRA else None

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

            def comprar_cercano(nivel, j):
                """E en la tienda: compra lo que tenes adelante. Devuelve True si habia algo para comprar."""
                v = vitrina_cercana(nivel, j) if nivel['tipo'] == 'tienda' else None
                if not v: return False
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
                actualizar_jugador(j)
                if (j['corriendo'] or j['embestida'] or j.get('esquive')) and nivel['frame'] % 4 == 0: efectos.polvo(mundo['ef'], j['rect'].centerx, j['rect'].bottom)
                efectos.actualizar(mundo['ef'])
                contexto = {'ent': ent, 'jugador': j, 'enemigos': enemigos + ([jefe] if jefe else []), 'ahora': ahora,
                            'dañar_jugador': lambda d, t: dañar_jugador(j, d, t),
                            'dañar_enemigo': lambda e, d, t, ef: recibir_ataque(e, {'tipo': t, 'daño': d, 'efecto': ef, 'retroceso': 0}),
                            'disparar': lambda x, y, dx, dy, d, t, v, dist, tam=16: nivel['proyectiles_enemigos'].append(crear_proyectil(x, y, dx, dy, round(d), False, t, v, dist, tam)),
                            'impacto': lambda x, y, r, ms: impacto(nivel, x, y, r, ms),
                            'parry': lambda e: intentar_parry(j, e, nivel),           # la IA lo llama antes de pegarte
                            'forzar_cambio': lambda: forzar_cambio(j), 'quitar_objeto': lambda: quitar_objeto(j)}   # Llave Giro y Desarme de Arceus Beta
                entorno.actualizar(ent, dict(contexto, dañar_jugador=lambda d, t: dañar_jugador(j, d, t, evitable=False)), ahora)   # terreno, maquinas, fuego, clima, explosiones
                if ahora >= j['congelado_hasta']:                        # el frio de los golpes de hielo se va solo
                    if j['frio'] >= FRIO_MAX:
                        j['congelado_hasta'] = ahora + DURACION_CONGELADO; j['frio'] = 0.0
                        cartel(nivel, 'Te congelaste! (un movimiento de fuego o lucha te descongela)', 1600)
                    j['frio'] = max(0.0, j['frio'] - DESCARGA_FRIO)
                for ev in ent['eventos']:                                # lo que paso en el entorno: monedas, cosas rotas, explosiones
                    if ev[0] == 'monedas' and not nivel['revisita']: soltar_monedas(nivel, j, ev[1], ev[2], ev[3])
                    elif ev[0] == 'roto':
                        efectos.romper(mundo['ef'], ev[1], ev[2], ev[3])
                        if not nivel['revisita']: ganar_xp(nivel, j, 2 + nivel['nivel_enemigos'] // 3)   # en salas repetidas no se farmea
                    elif ev[0] == 'explosion': efectos.explosion(mundo['ef'], ev[1], ev[2], ev[3])
                ent['eventos'] = []
                nivel['efectos'] = [x for x in nivel['efectos'] if ahora < x['hasta']]
                for proyectil in nivel['proyectiles_pokemon']: actualizar_proyectil_pokemon(proyectil, objetivos, solidos_p)
                nivel['proyectiles_pokemon'] = [proyectil for proyectil in nivel['proyectiles_pokemon'] if proyectil['activo']]
                contexto_ia = dict(contexto, enemigos=enemigos)
                for e in enemigos:
                    actualizar_estado(e)
                    if e['vida'] > 0: ia.actualizar(e, contexto_ia)
                    actualizar_animacion_enemigo(e)
                for e in enemigos:                                      # los que caen: monedas, experiencia y a veces quieren ser tus amigos
                    if e['vida'] <= 0:
                        soltar_monedas(nivel, j, *e['rect'].center, MONEDAS_ENEMIGO + nivel['sala']['era'])
                        ganar_xp(nivel, j, progreso.xp_por_derrota(e['nombre'], e['nivel'], j['nivel']))
                        efectos.romper(mundo['ef'], *e['rect'].center, e['color'])
                        quiza_amigo(nivel, j, e)
                nivel['enemigos'] = [e for e in enemigos if e['vida'] > 0 and not e.get('amigable')]
                if nivel['amigo']:
                    actualizar_animacion_enemigo(nivel['amigo'])
                    if nivel['frame'] % 45 == 0: efectos.corazones(mundo['ef'], *nivel['amigo']['rect'].center)
                if nivel['oleadas'] and not nivel['apariciones'] and len(nivel['enemigos']) <= 1:   # oleada nueva: primero se marca donde salen
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
                for proyectil in nivel['proyectiles_enemigos']: actualizar_proyectil(proyectil, j, solidos_p, nivel['proyectiles_pokemon'])
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
                    cartel(nivel, 'Sala completada!' + ('  (podes volver por donde entraste)' if any(p_.get('atras') for p_ in nivel['puertas']) else ''))
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
                if nivel['llave'] and j['rect'].colliderect(nivel['llave']):
                    j['llave'] = True; nivel['llave'] = None
                    cartel(nivel, 'Conseguiste la llave!')                # se ve un segundo y se va solo
                if j['vida'] <= 0:
                    guardar_activo(j)
                    vivos = [i for i, m in enumerate(j['equipo']) if m['vida'] > 0]
                    if not vivos: return 'muerte'
                    cambiar_slot(j, vivos[0], True)
                if nivel['saliendo']:                                   # saliendo: se cierra la pantalla y pasa a la sala de atras
                    if ahora >= nivel['saliendo']['hasta']: nivel['salida'] = nivel['saliendo']['puerta']; return 'siguiente'
                elif j['llave'] and ahora >= nivel['entrando_hasta']:
                    for puerta in nivel['puertas']:
                        tocando = j['rect'].colliderect(puerta['rect'].inflate(20, 20))
                        if not tocando: puerta['armada'] = True              # una puerta sirve recien cuando te alejaste de ella
                        if puerta.get('bloqueada') or (puerta.get('atras') and not nivel['completado']): continue
                        if tocando and puerta.get('armada'):
                            cx, cy = camara(j)
                            nivel['saliendo'] = {'puerta': puerta, 'hasta': ahora + 320}
                            efectos.transicion(mundo['ef'], 'salir', ahora, (j['rect'].centerx - cx, j['rect'].centery - cy))
                            break

            return menu_niveles, cartel, crear_nivel, tecla_de, hablar_amigo, vitrina_cercana, comprar_cercano, actualizar_nivel, bloque_cercano, empujar_bloque

        menu_niveles, cartel, crear_nivel, tecla_de, hablar_amigo, vitrina_cercana, comprar_cercano, actualizar_nivel, bloque_cercano, empujar_bloque = armar_salas()

        def armar_dibujo():
            """Todo lo que se dibuja jugando: jugador, HUD, indicadores, carteles, tienda y objetos."""
            def dibujar_rect(rect, cx, cy, color, forma='rect'):
                """Rectangulo (o elipse) del mundo dibujado en la pantalla segun la camara."""
                r = pygame.Rect(rect.x-cx, rect.y-cy, rect.width, rect.height)
                (pygame.draw.ellipse if forma == 'ellipse' else pygame.draw.rect)(ventana, color, r)

            def dibujar_jugador(j, cx, cy):
                """Dibuja al pokemon activo (un cuadrado rosa si no tiene sprites)."""
                centro = j['rect'].center; j['rect'].center = centro[0]-cx, centro[1]-cy
                ok = j['animador'].dibujar(ventana); j['rect'].center = centro
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

            f_hud, f_hud_g, f_hud_b = pygame.font.Font(None, 20), pygame.font.Font(None, 26), pygame.font.Font(None, 30)

            f_hud_b.set_bold(True)

            f_tipo = pygame.font.Font(None, 18)
            f_cartel, f_cartel_sub = pygame.font.Font(None, 64), pygame.font.Font(None, 28)   # carteles grandes (antes se cargaban en cada frame)
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

            def dibujar_hud(j, nivel, rec):
                """HUD: vida, energia y experiencia del activo, la banca con sus asistencias, monedas, especiales y la barra del jefe."""
                ahora = tiempo()
                circulo_poke((44, 86), 34, j['nombre'])
                barra_hud((80, 68, 240, 36), j['vida'], j['max_vida'])
                if j['frio'] > 0:                                         # barra de congelamiento arriba de la vida
                    pygame.draw.rect(ventana, (225, 245, 255), (83, 71, 234, 7))
                    pygame.draw.rect(ventana, (90, 200, 255), (83, 71, int(234 * j['frio'] / FRIO_MAX), 7))
                if ahora < j['congelado_hasta']: pygame.draw.circle(ventana, (120, 215, 255), (44, 86), 37, 4)
                t = render(f_hud, str(int(j['vida'])) + '/' + str(j['max_vida']), 'white')
                sombra_t = render(f_hud, str(int(j['vida'])) + '/' + str(j['max_vida']), (30, 30, 30))
                ventana.blit(sombra_t, sombra_t.get_rect(center=(216, 88))); ventana.blit(t, t.get_rect(center=(215, 86)))
                pygame.draw.rect(ventana, (60, 60, 60), (80, 108, 240, 6))
                pygame.draw.rect(ventana, (120, 120, 160) if j['agotado'] else (0, 160, 230), (80, 108, int(240 * j['energia'] / ENERGIA_MAX), 6))
                activo = j['equipo'][j['activo']]
                pygame.draw.rect(ventana, (150, 110, 255), (80, 114, int(240 * progreso.progreso_nivel(activo)), 3))   # experiencia
                nombre_t = con_sombra(f_hud_b, j['nombre'].replace('_', ' '), 'white', (84, 117))
                con_sombra(f_hud_g, 'Nv ' + str(activo['nivel']) + (' +' + str(activo['puntos']) + ' EV' if activo['puntos'] else ''), (255, 220, 90), (92 + nombre_t.get_width(), 120))
                monedas = render(f_hud_g, '$ ' + str(j['monedas']), (250, 215, 60))   # monedas y objetos de la tienda andando
                ventana.blit(monedas, (12, 140))
                for i, linea in enumerate(tienda.activos(j['inventario'])): ventana.blit(render(f_hud, linea, (230, 230, 230)), (12, 164 + i * 16))
                esperando = ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO
                k = 0
                for i, m in enumerate(j['equipo']):
                    if i == j['activo']: continue
                    cy = 14 + k * 30
                    circulo_poke((86, cy), 11, m['nombre'], esperando or m['vida'] <= 0)
                    con_sombra(f_hud, str(i + 1), 'white', (68, cy - 6))
                    barra_hud((100, cy - 8, 100, 16), m['vida'], m['max_vida'])
                    con_sombra(f_hud, m['nombre'].replace('_', ' '), 'white', (103, cy + 9))
                    resto = max(0, m['asist_listo'] - ahora)
                    listo = resto == 0 and m['vida'] > 0
                    texto = ('F' if k == 0 else 'G') + ' ' + m['asist']['nombre'].replace('_', ' ') + ' ' + ('LISTO' if not resto else str(resto // 1000 + 1) + 's')
                    ventana.blit(render(f_hud, texto, (0, 150, 0) if listo else (90, 90, 90)), (206, cy - 5))
                    k += 1
                for i, (nombre, datos) in enumerate(j['juego']['especiales']):
                    radio = 30 - i * 6
                    cx, cy = W - 60 - i * 85, H - 62
                    enfriamiento = max(1, enfriamiento_de(j, datos))
                    restante = max(0, enfriamiento - (ahora - j['esp_ultimo'][i]))
                    pygame.draw.circle(ventana, 'white', (cx, cy), radio)
                    pygame.draw.circle(ventana, 'black', (cx, cy), radio, 3)
                    tecla = render(f_hud_g, 'Shift' if i == 0 else 'R', 'black')
                    ventana.blit(tecla, tecla.get_rect(center=(cx, cy)))
                    if restante:
                        ventana.blit(sombra_circular(radio, 160), (cx - radio, cy - radio))
                        s = render(f_hud, str(round(restante / 1000, 1)), 'white')
                        ventana.blit(s, s.get_rect(center=(cx, cy)))
                    n = render(f_hud, nombre.replace('_', ' '), (60, 60, 60))
                    ventana.blit(n, n.get_rect(center=(cx, cy + radio + 12)))
                for k, (tecla_txt, clave, base) in enumerate((('E', 'ultimo_golpe', j['juego']['basicos'][0]), ('Q', 'ultimo_proyectil', j['juego']['basicos'][1]))):
                    cx, cy = W - 296 + k * 66, H - 56
                    pygame.draw.circle(ventana, (235, 235, 235), (cx, cy), 20)
                    pygame.draw.circle(ventana, 'black', (cx, cy), 20, 2)
                    t = render(f_hud_g, tecla_txt, 'black'); ventana.blit(t, t.get_rect(center=(cx, cy)))
                    if k == 0 and j.get('combo') and ahora - j.get('ultimo_golpe', -10000) <= COMBO['ventana']:
                        pygame.draw.arc(ventana, (255, 200, 60), (cx - 22, cy - 22, 44, 44), 0, math.tau * j['combo'] / 3, 4)   # combo en curso
                    elif k == 1:
                        dm = datos_mov(base) or {}
                        espera = enfriamiento_de(j, dict(dm, enfriamiento=float(dm.get('enfriamiento', 800)) * BASICO_DISTANCIA['enfriamiento']))
                        if ahora - j[clave] < espera: ventana.blit(sombra_circular(20, 140), (cx - 20, cy - 20))
                    n = render(f_tipo, nombre_mov(base), (40, 40, 40))
                    ventana.blit(n, n.get_rect(center=(cx, cy + 30)))
                if j['energia'] < ESQUIVE['energia'] * mod(j, 'gasto'):      # sin energia para esquivar: aviso chiquito
                    ventana.blit(render(f_hud, 'sin energia para esquivar', (160, 200, 255)), (84, 98))
                lugar = render(f_hud, mundos.ERAS[rec['era']]['nombre'] + ' - Sala ' + str(rec['sala'] + 1) + '/' + str(mundos.salas_de(rec)), 'white')
                ventana.blit(lugar, lugar.get_rect(midtop=(W // 2, 6)))
                if nivel['jefe']:
                    b = nivel['jefe']
                    ventana.blit(render(f_hud, b['nombre'].replace('_', ' ').title() + ' - ' + b['tipo'], 'white'), (W - 300, 4))
                    barra_hud((W - 300, 22, 280, 20), b['vida'], b['max_vida'])
                    if b['estilo'] in ia.FASES_JEFE:                 # la barra de los jefes con fases se parte donde cambian
                        cortes = ia.FASES_JEFE[b['estilo']]
                        for k in cortes: pygame.draw.line(ventana, 'black', (W - 300 + round(280 * k), 20), (W - 300 + round(280 * k), 43), 4)
                        total = ia.TOTAL_FASES.get(b['estilo'], len(cortes) + 1)
                        ventana.blit(render(f_hud, 'Fase ' + str(b['fase']) + '/' + str(total), 'white'), (W - 300, 45))

            ZONAS_HUD = [pygame.Rect(0, 0, 340, 200), pygame.Rect(W - 310, 0, 310, 50), pygame.Rect(W - 330, H - 125, 330, 125),
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

            def dibujar_carteles(nivel):
                """Cartel grande al entrar (nombre de la sala, era y clima) y los chiquitos que duran un segundo."""
                ahora = tiempo()
                nivel['carteles'] = [c for c in nivel['carteles'] if ahora < c['hasta']]
                y_chico = 110
                for c in nivel['carteles']:
                    vida = (c['hasta'] - ahora) / max(1, c['hasta'] - c['inicio'])
                    alfa = max(0, min(255, round(255 * min(1.0, vida * 4, (ahora - c['inicio']) / 150 + 0.01))))   # aparece y se desvanece
                    if c['grande']:
                        t = render(f_cartel, c['texto'], 'white')
                        s = render(f_cartel_sub, c['sub'] or '', (230, 230, 230))
                        caja = pygame.Surface((max(t.get_width(), s.get_width()) + 60, 110), pygame.SRCALPHA)
                        caja.fill((0, 0, 0, 150))
                        caja.blit(t, t.get_rect(midtop=(caja.get_width() // 2, 14)))
                        caja.blit(s, s.get_rect(midtop=(caja.get_width() // 2, 70)))
                        caja.set_alpha(alfa)
                        ventana.blit(caja, caja.get_rect(midtop=(W // 2, 150)))
                    else:
                        t = render(f_hud_b, c['texto'], 'white')
                        caja = pygame.Surface((t.get_width() + 30, 40), pygame.SRCALPHA)
                        caja.fill((20, 60, 30, 190))
                        caja.blit(t, t.get_rect(center=(caja.get_width() // 2, 20)))
                        caja.set_alpha(alfa)
                        ventana.blit(caja, caja.get_rect(midtop=(W // 2, y_chico))); y_chico += 46

            def dibujar_tienda(nivel, j, cx, cy):
                """Objetos en los estantes y mesas con nombre y precio, y que vas a comprar con E."""
                for v in nivel['vitrinas']:
                    item = tienda.ITEMS[v['item']]
                    x, y = v['pos'][0] - cx, v['pos'][1] - cy
                    caja = pygame.Rect(0, 0, 30, 30); caja.center = (x, y - 4)
                    icono = None if v['vendido'] else menus.icono_objeto(v['item'], 34)   # icono del objeto de BW si esta
                    if icono:
                        brillo = 3 + round(2 * math.sin(tiempo() / 300 + x / 50))      # el objeto flota un poquito
                        pygame.draw.ellipse(ventana, (20, 20, 20), (x - 13, y + 8, 26, 7))
                        ventana.blit(icono, icono.get_rect(center=(x, y - 4 - brillo)))
                    else:
                        pygame.draw.rect(ventana, (60, 60, 60) if v['vendido'] else item['color'], caja, border_radius=6)
                        pygame.draw.rect(ventana, (20, 20, 20), caja, 2, border_radius=6)
                    nombre = render(f_tipo, 'VENDIDO' if v['vendido'] else item['nombre'], 'white')
                    ventana.blit(nombre, nombre.get_rect(midtop=(x, y + 14)))
                    if not v['vendido']:
                        precio = render(f_tipo, str(item['precio']) + ' $', (250, 215, 60) if j['monedas'] >= item['precio'] else (220, 90, 90))
                        ventana.blit(precio, precio.get_rect(midtop=(x, y + 28)))
                v = vitrina_cercana(nivel, j)
                if v:
                    item = tienda.ITEMS[v['item']]
                    panel = pygame.Rect(0, 0, 560, 58); panel.midbottom = (W // 2, H - 14)
                    pygame.draw.rect(ventana, (25, 25, 25), panel, border_radius=8)
                    pygame.draw.rect(ventana, item['color'], panel, 2, border_radius=8)
                    ventana.blit(render(f_hud_b, 'E: comprar ' + item['nombre'] + ' (' + str(item['precio']) + ' $)', 'white'), (panel.x + 14, panel.y + 8))
                    ventana.blit(render(f_hud, item['desc'], (210, 210, 210)), (panel.x + 14, panel.y + 34))

            def dibujar_objetos(nivel, j, rec):
                """Dibuja un frame de la partida: sala, puertas, balas, efectos, pokemon, jefe, clima, HUD y carteles."""
                cx, cy = camara(j)
                ahora = tiempo()
                if ahora < nivel['temblor']:                              # terremotos y puñetazos de Regigigas
                    fuerza = min(10, 2 + (nivel['temblor'] - ahora) // 40)
                    cx += random.randint(-fuerza, fuerza); cy += random.randint(-fuerza, fuerza)
                ventana.fill('black')
                entorno.dibujar(nivel['ent'], ventana, cx, cy, ahora, j['tipos'])   # piso de la era, terrenos, maquinas y objetos
                ia.dibujar_suelo(ventana, nivel['jefe'], cx, cy, ahora, COLORES_TIPO)   # Arceus Beta: el triangulo, charcos, rastros y arena
                for puerta in nivel['puertas'] if not nivel['ent'].get('guardado') else ():   # puertas con el cartel (en la torre de Regidrago no hay)
                    r = puerta['rect'].move(-cx, -cy)
                    abierta = j['llave'] and not puerta.get('bloqueada') and (not puerta.get('atras') or nivel['completado'])
                    entorno.dibujar_puerta(ventana, r, abierta, ahora)    # cerrada con tablas o abierta brillando
                    if 'destino' in puerta and (not puerta.get('atras') or nivel['completado']):
                        t = render(f_hud_b, mundos.etiqueta_destino(puerta['destino']), 'white')
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
                for moneda in nivel['monedas']:
                    pygame.draw.circle(ventana, (250, 210, 50), (round(moneda['x'] - cx), round(moneda['y'] - cy)), 8)
                    pygame.draw.circle(ventana, (150, 110, 20), (round(moneda['x'] - cx), round(moneda['y'] - cy)), 8, 2)
                dibujar_jugador(j,cx,cy)
                dibujar_congelado(j, cx, cy)
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
                    barra((e['rect'].x-cx,e['rect'].y-cy-9,e['rect'].width,5),e['vida'],e['max_vida'])
                    con_sombra(f_tipo, e['nombre'].replace('_', ' ') + ' Nv' + str(e['nivel']) + ' (' + e['tipo'] + ')', 'white', (e['rect'].x-cx, e['rect'].bottom-cy+2))
                if nivel['amigo']:                                         # el que quiere unirse: sentado con un corazon
                    e = nivel['amigo']
                    dibujar_enemigo(e, cx, cy)
                    pygame.draw.circle(ventana, (255, 110, 160), (e['rect'].centerx - cx, e['rect'].top - cy - 14), 9)
                    if math.hypot(e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery) < 90:
                        t = render(f_hud_b, tecla_de('interactuar') + ': hablar', 'white')
                        ventana.blit(t, t.get_rect(midbottom=(e['rect'].centerx - cx, e['rect'].top - cy - 26)))
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
                if nivel['tipo'] == 'tienda': dibujar_tienda(nivel, j, cx, cy)
                efectos.dibujar(mundo['ef'], ventana, cx, cy)              # chispas, pedazos, explosiones, brillitos
                entorno.dibujar_clima(nivel['ent'], ventana, ahora)
                dibujar_indicadores(nivel, cx, cy)
                dibujar_hud(j, nivel, rec)
                efectos.dibujar_transicion(mundo['ef'], ventana, ahora)    # circulo negro al entrar o salir de la sala
                dibujar_carteles(nivel)
                pantalla.presentar()

            return dibujar_objetos

        dibujar_objetos = armar_dibujo()

        def armar_extras():
            """Pantalla final, acciones del menu de equipo (TAB) y trucos."""
            def pantalla_final():
                """Cuando cae Arceus."""
                pygame.mouse.set_visible(True)
                f_g, f_c = pygame.font.Font(None, 90), pygame.font.Font(None, 30)
                reloj_f = pygame.time.Clock()
                while True:
                    for e in controles.eventos():
                        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE)): return
                    ventana.fill((20, 15, 35))
                    t = f_g.render('GANASTE!', True, (250, 220, 120))
                    ventana.blit(t, t.get_rect(center=(W // 2, H // 2 - 40)))
                    s = f_c.render('Venciste a los Regis, a Regigigas y a Arceus - ENTER para volver', True, 'white')
                    ventana.blit(s, s.get_rect(center=(W // 2, H // 2 + 30)))
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
                    progreso.evolucionar(m, req['a'])
                    m['asist'] = asistencia_de(m['nombre']); m['max_vida'] = progreso.vida_max(m); m['vida'] = round(m['max_vida'] * proporcion)
                    if i == j['activo']: aplicar_pokemon(j, m['nombre'], m['vida'])
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
                        texto = datos.describir_movimiento(d)
                        if k == 0 and d.get('forma') == 'cuerpo':
                            texto = 'combo de 3 golpes (el 3ro es un remate); ' + texto.replace('golpe cuerpo a cuerpo, ', '').split(', espera')[0] + \
                                    '. Apretalo justo cuando te van a pegar para hacer parry'
                        salida.append(texto)
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

                return {'movs': movs, 'evolucionar': evolucionar, 'enseñar': enseñar, 'activar': lambda i: cambiar_slot(j, i, True),
                        'refrescar': refrescar, 'reserva': lambda: j['reserva'], 'traer': traer, 'info_movs': info_movs, 'equipar': equipar,
                        'sinergia': elegir_sinergia, 'asistencia': texto_asistencia}

            def aplicar_trucos(nivel, j):
                """Los trucos que hacen algo una sola vez (subir niveles)."""
                veces = trucos.pop('subir_niveles', 0)
                for _ in range(veces):
                    for m in j['equipo']: progreso.dar_xp(m, progreso.xp_para(m['nombre'], m['nivel'] + 5) - m['xp'])
                if veces:
                    acciones_equipo(j)['refrescar'](); j['nivel'] = j['equipo'][j['activo']]['nivel']
                    cartel(nivel, 'Truco: +' + str(5 * veces) + ' niveles')

            def ofrecer_evolucion(nivel, j):
                """Cartel que pregunta si evolucionar apenas un pokemon del equipo llega a su nivel, consigue el objeto o la amistad.
                Si decis que no, vuelve a preguntar cuando sube otro nivel o conseguis otro objeto (y siempre se puede desde el menu de equipo).
                Una pregunta por cuadro. Devuelve 'salir' si cerraron la ventana."""
                objetos = j['inventario']['objetos']
                for i, m in enumerate(j['equipo']):
                    for req in progreso.evoluciones(m, objetos):
                        marca = objetos.get(req['objeto'], 0) if 'objeto' in req else m['nivel']   # como estaba cuando dijiste que no
                        no = m['evo_no'] = m.get('evo_no') or {}
                        if req['a'] in no and marca <= no[req['a']]:
                            no[req['a']] = marca; continue                       # ya dijiste que no (si gastaste el objeto, recuerda cuantos quedan)
                        nombre = m['nombre'].title()
                        r = pausado(menus.preguntar, ui, nombre + ' quiere evolucionar en ' + req['a'].title() + '!', ['Evolucionar', 'Todavia no'],
                                    'requisito: ' + progreso.texto_requisito(req) + ' (despues tambien se puede desde ' + tecla_de('equipo') + ')')
                        if r == 'salir': return 'salir'
                        if r == 0:
                            acciones_equipo(j)['evolucionar'](i, req)
                            pausado(menus.animacion_evolucion, ui, m['nombre'])
                            if i == j['activo']: efectos.evolucion(mundo['ef'], *j['rect'].center)
                            aplicar_trucos(nivel, j)
                            cartel(nivel, nombre + ' evoluciono en ' + m['nombre'].title() + '!', 2000)
                            nivel['guardar'] = True
                        else: no[req['a']] = marca
                        return None
                return None

            return pantalla_final, acciones_equipo, aplicar_trucos, ofrecer_evolucion

        pantalla_final, acciones_equipo, aplicar_trucos, ofrecer_evolucion = armar_extras()

        def armar_guardado():
            """Pasar la partida a datos guardables (equipo, mochila, recorrido) y armarla de vuelta al cargar."""
            CAMPOS = ('nombre', 'nivel', 'xp', 'ivs', 'evs', 'puntos', 'amistad', 'movs', 'items', 'sinergia', 'vida', 'evo_no')

            def serializar(j, rec):
                """Todo lo que hace falta para seguir la partida despues."""
                guardar_activo(j)
                miembro = lambda m: {k: m.get(k) for k in CAMPOS}
                azar = rec['azar'].getstate()
                return {'jugador': {'equipo': [miembro(m) for m in j['equipo']], 'activo': j['activo'], 'reserva': [miembro(m) for m in j['reserva']],
                                    'monedas': j['monedas'], 'inventario': j['inventario']},
                        'recorrido': {'plan': rec['plan'], 'era': rec['era'], 'sala': rec['sala'], 'semilla': rec['semilla'], 'clima': rec['clima'],
                                      'azar': [azar[0], list(azar[1]), azar[2]], 'historial': rec['historial'], 'pos': rec['pos']},
                        'resumen': {'equipo': [[m['nombre'], m['nivel']] for m in j['equipo']], 'era': mundos.ERAS[rec['era']]['nombre'],
                                    'sala': rec['sala'] + 1, 'salas': mundos.salas_de(rec), 'monedas': j['monedas'], 'fecha': time.strftime('%d/%m/%Y %H:%M')}}

            def revivir(d):
                """Un miembro del equipo desde lo guardado (la vida maxima y la asistencia se recalculan)."""
                m = crear_miembro(d['nombre'], d.get('nivel', progreso.NIVEL_INICIAL))
                m.update({k: d[k] for k in CAMPOS if k in d and k != 'vida'})
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
                aplicar_pokemon(j, j['equipo'][j['activo']]['nombre'], j['equipo'][j['activo']]['vida'])
                actualizar_sinergia(j)
                azar = random.Random()
                a = rd['azar']; azar.setstate((a[0], tuple(a[1]), a[2]))
                rec = {'plan': rd['plan'], 'era': rd['era'], 'sala': rd['sala'], 'semilla': rd.get('semilla'), 'clima': rd['clima'], 'azar': azar,
                       'historial': rd['historial'], 'pos': rd['pos']}
                return j, rec

            def guardar_partida(j, rec):
                """Autoguardado en la ranura de esta partida (al entrar a cada sala, al completarla y al comprar)."""
                if ranura: partidas.guardar(ranura, serializar(j, rec))

            return restaurar, guardar_partida

        restaurar, guardar_partida = armar_guardado()

        if cargada: j, rec = restaurar(cargada); visita = rec['pos']
        else:
            j = crear_jugador(nombres, ESC.center, config['modo'])
            rec = mundos.nuevo_recorrido()                           # plan de la partida: eras, salas, tiendas, jefes y clima
            visita = None
        destino, entrada, llegada = None, 'sur', None
        reloj = pygame.time.Clock()
        while True:
            if visita is not None:                                   # una sala del historial: volviste, seguiste para adelante o cargaste
                registro = rec['historial'][visita]; rec['pos'] = visita
                rec['era'], rec['sala'], rec['clima'] = registro['era'], registro['sala'], registro['clima']
                nivel = crear_nivel(rec, None, registro['entrada'], j, registro, llegada)
            else: nivel = crear_nivel(rec, destino, entrada, j)
            reiniciar_jugador(j, nivel['inicio'])
            df, dc = generacion.PASO_LADO[nivel.get('llegada_lado') or nivel['sala']['entrada'] or 'sur']   # arranca en la puerta y camina para adentro
            j['rect'].center = (round(nivel['inicio'][0] - dc * 70), round(nivel['inicio'][1] - df * 70))
            cx, cy = camara(j)
            efectos.transicion(mundo['ef'], 'entrar', tiempo(), (j['rect'].centerx - cx, j['rect'].centery - cy))
            if nivel['tipo'] == 'tienda' or nivel['revisita']: j['llave'] = True   # tienda o sala ya hecha: las puertas ya estan abiertas
            guardar_partida(j, rec)
            reiniciar_nivel = False
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
                    if 'interactuar' in acciones and (ia.salir_arena(j, tiempo()) or comprar_cercano(nivel, j) or hablar_amigo(nivel, j) or empujar_bloque(nivel, j)):
                        acciones = [a for a in acciones if a != 'basico1']   # si estabas comprando o hablando, no ataca
                    if 'esquivar' in acciones: esquivar(j, nivel)
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
                resultado = actualizar_nivel(nivel, j)
                dibujar_objetos(nivel, j, rec)
                if resultado is None and ofrecer_evolucion(nivel, j) == 'salir': return 'salir', j['nombre']
                if nivel.pop('guardar', False): guardar_partida(j, rec)
                if resultado == 'siguiente':
                    puerta = nivel['salida']
                    guardar_activo(j)
                    if puerta.get('atras'):                              # para atras: a la sala anterior, por la puerta por la que habias salido
                        visita = rec['pos'] - 1; llegada = rec['historial'][visita]['salida']; break
                    if rec['pos'] < len(rec['historial']) - 1:           # para adelante por una sala que ya hiciste
                        visita = rec['pos'] + 1; llegada = None; break
                    nivel['registro']['salida'] = puerta['lado']
                    if puerta['destino']['tipo'] == 'fin' or not mundos.avanzar(rec):
                        pausado(pantalla_final); return 'menu', j['nombre']
                    destino, entrada = puerta['destino'], generacion.OPUESTO[puerta['lado']]   # salis por el norte: entras por el sur
                    visita, llegada = None, None
                    break
                if resultado == 'muerte': return 'juego_terminado', j['nombre']
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
                cargada, inicial = None, None
                if modo == 'continuar':
                    cargada = partidas.cargar(ranura)
                    if not cargada: menus.preguntar(ui, 'No se pudo leer la partida ' + str(ranura), ['Ok']); continue
                else:
                    inicial = [n for n in equipo_menu if n] or menus.elegir_inicial(ui)   # Electrike, Sandshrew o Mareanie
                    if inicial == 'salir': pygame.quit(); sys.exit()
                    if not inicial: continue
                    partidas.borrar(ranura)
                while True:
                    resultado, _ = jugar(inicial if isinstance(inicial, list) else [inicial], config, ranura, cargada)
                    pygame.mouse.set_visible(True)
                    if resultado == 'salir': opciones.guardar(config); pygame.quit(); sys.exit()
                    if resultado != 'juego_terminado': break
                    cargada = partidas.cargar(ranura)                  # cayo todo el equipo: se puede reintentar desde que entraste a la sala
                    r = menus.preguntar(ui, 'Cayo todo tu equipo...', ['Reintentar la sala', 'Volver al menu'] if cargada else ['Volver al menu'],
                                        'se vuelve a como estabas al entrar a la sala' if cargada else None)
                    if r == 'salir': pygame.quit(); sys.exit()
                    if not cargada or r != 0: break
        if accion == 'pokedex':
            if pokedex() == 'salir': pygame.quit(); sys.exit()
        if accion == 'ajustes' and menus.ajustes(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'glosario' and menus.glosario(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'salir' and confirmar('¿Seguro que quieres salir?'): opciones.guardar(config); pygame.quit(); sys.exit()

if __name__ == '__main__':
    main()