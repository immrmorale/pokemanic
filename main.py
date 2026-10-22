import pygame
import random
import math
import sys
import datos
from datos import mundos, mts, tienda
from sistema import controles, pantalla, opciones, animaciones
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
            clave = (nombre, lado)
            if clave not in retratos_menu:
                img = cargar_retrato(nombre)
                retratos_menu[clave] = pygame.transform.smoothscale(img, (lado, lado)) if img else None
            return retratos_menu[clave]

        def aplicar_volumen():
            try: pygame.mixer.music.set_volume(config['volumen'] / 100)
            except pygame.error: pass

        def confirmar(mensaje):
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
            pygame.mouse.set_visible(True)
            f_med, f_peq = pygame.font.Font(None, 30), pygame.font.Font(None, 18)
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
                menus.dibujar_logo(ventana, 90, pygame.time.get_ticks(), center=(W // 2, 130))
                p = f_med.render('presione cualquier tecla para empezar', True, 'white')
                franja = p.get_rect(center=(W // 2, H - 75)).inflate(40, 42)      # franja oscura para que se lea sobre el fondo
                velo = pygame.Surface(franja.size, pygame.SRCALPHA); velo.fill((0, 0, 0, 120)); ventana.blit(velo, franja)
                ventana.blit(p, p.get_rect(center=(W // 2, H - 85)))
                s = f_peq.render('(menos esc, es para salir)', True, 'white')
                ventana.blit(s, s.get_rect(center=(W // 2, H - 58)))
                pantalla.presentar(); reloj_t.tick(60)

        def menu_principal(equipo):
            pygame.mouse.set_visible(True)
            orden = ['jugar', 'pokedex', 'ajustes', 'glosario', 'salir']
            botones = {o: pygame.Rect(100, 170 + i * 80, 300, 60) for i, o in enumerate(orden[:4])}
            botones['salir'] = pygame.Rect(0, 0, 84, 84)
            botones['salir'].center = (W - 100, H - 80)
            f_boton, f_info = pygame.font.Font(None, 44), pygame.font.Font(None, 24)
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
                menus.dibujar_logo(ventana, 56, pygame.time.get_ticks(), topright=(W - 50, 45))
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
        def descripcion_movimiento(datos):
            if not datos: return 'sin datos'
            def num(clave):
                try: return float(datos.get(clave) or 0)
                except (TypeError, ValueError): return 0.0
            forma = datos.get('forma')
            partes = []
            if datos.get('tipo'): partes.append(normalizar_tipo(datos['tipo']))
            if forma == 'buff':
                etiquetas = {'defensa': 'daño recibido x', 'daño': 'daño x', 'velocidad': 'velocidad x', 'enfriamiento': 'recargas x'}
                for clave, valor in (datos.get('buffs') or {}).items():
                    partes.append('sprint sin gasto' if clave == 'sprint' else etiquetas.get(clave, clave + ' x') + str(valor))
                partes.append('durante ' + str(round(num('duracion') / 1000, 1)) + ' s')
            elif forma == 'curar':
                partes.append('cura ' + str(int(num('porcentaje'))) + '% de la vida (la mitad a los de la banca)')
            else:
                partes.append({'cuerpo': 'cuerpo a cuerpo', 'proyectil': 'proyectil', 'area': 'de área', 'embestida': 'embestida'}.get(forma, str(forma)))
                partes.append('daño ' + str(int(num('daño'))))
                if num('distancia'): partes.append('alcance ' + str(int(num('distancia'))))
                if num('area'): partes.append('radio ' + str(int(num('area'))))
                if datos.get('efecto'): partes.append('efecto ' + str(datos['efecto'].get('tipo')))
                if datos.get('atraviesa'): partes.append('atraviesa')
            if num('enfriamiento'): partes.append('espera ' + str(round(num('enfriamiento') / 1000, 1)) + ' s')
            return ', '.join(partes)

        def descripcion_asistencia(a):
            mec = a['mecanica']
            if mec == 'impacto': return 'golpe de área en el punto apuntado (daño ' + str(a['daño']) + ', radio ' + str(a['area']) + ')'
            if mec == 'escudo': return 'el activo recibe solo el 25% del daño durante ' + str(a['duracion'] // 1000) + ' s'
            if mec == 'furia': return 'daño x1.6 y recargas x0.7 durante ' + str(a['duracion'] // 1000) + ' s'
            if mec == 'carrera': return 'velocidad x1.6 y sprint sin gasto durante ' + str(a['duracion'] // 1000) + ' s'
            if mec == 'curar': return 'cura el ' + str(a['porcentaje']) + '% de la vida del activo y la mitad a los demas'
            if mec == 'desvanecer': return 'elimina enemigos comunes en un radio de ' + str(a['area']) + ' y le quita el ' + str(a['porcentaje_jefe']) + '% a un jefe'
            return 'aplica ' + str((a.get('efecto') or {}).get('tipo')) + ' a todos los enemigos cercanos'

        def construir_ficha(nombre, ancho, fuente_txt):
            d = pokemones[nombre]
            filas = []
            def titulo(t): filas.append(('t', t))
            def texto(t):
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
            f_nombre, f_sec, f_txt = pygame.font.Font(None, 42), pygame.font.Font(None, 28), pygame.font.Font(None, 22)
            reloj_f = pygame.time.Clock()
            panel = pygame.Rect(335, 60, 645, 525)
            ancho_texto = panel.width - 30
            altos = {'t': 32, 'p': 21, 'e': 10}
            estado = {'indice': -1}
            def cargar(i):
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

        return pokedex

    pokedex = armar_pokedex()

    def jugar(nombres, config):
        pausa = {'total': 0}

        def tiempo(): return pygame.time.get_ticks() - pausa['total']

        def pausado(f, *args):
            t0 = pygame.time.get_ticks()
            controles.contexto('menu')
            pygame.mouse.set_visible(True)                       # en la partida el cursor se esconde (se apunta con la mira); en los menus se ve
            r = f(*args)
            controles.contexto('juego')
            pausa['total'] += pygame.time.get_ticks() - t0
            return r

        ESC = generacion.crear_escenario()        # tamaño de la sala actual (se cambia en el lugar al entrar a otra)
        AREA = generacion.crear_area(ESC)
        mundo = {'ent': None, 'ef': efectos.crear()}  # entorno de la sala actual (terrenos, objetos, clima) y las particulas
        RESTAURAR_VIDA_ENTRE_SALAS = False          # True: como antes, cada sala empieza con la vida llena
        CURA_SALA = 0.06                            # al pasar de sala los que siguen en pie recuperan esta parte de su vida
        CURA_BANCA = 0.5                            # los movimientos que curan: el que pelea todo, los de la banca la mitad
        PROB_BAYA, CURA_BAYA = 0.06, 0.12           # a veces un enemigo suelta una Baya Oran: cura al que pelea al agarrarla
        DURACION_CARTEL = 1200                      # ms que se ve un cartel ("sala completada", "conseguiste la llave"...)
        BASICO_DISTANCIA = {'daño': 0.65, 'enfriamiento': 1.5, 'distancia': 0.85}   # el ataque a distancia basico es mas flojo que el de cerca
        DURACION_ENTRADA = 450                      # ms que el pokemon camina solo al entrar a una sala
        trucos = config['trucos']                   # menu secreto (Konami): vida infinita, sin recarga...
        DISTANCIA_COMPRA = 95                       # que tan cerca de una vitrina hay que estar para comprar
        VEL_P_ENEMIGO = 8                           # balas del anillo de los jefes (las de los tiradores van en ia.py)
        DIST_P_ENEMIGO = 250
        DAÑO_ENEMIGO = 10                           # daño base de un enemigo (se escala con la era y la sala)
        ENERGIA_MAX, GASTO_SPRINT, REGEN_ENERGIA, ENERGIA_MIN, MULT_SPRINT, COOLDOWN_CAMBIO = 100.0, 0.6, 0.35, 25.0, 1.7, 2500
        DIRS = {(1,-1):'noreste',(1,1):'sureste',(-1,-1):'noroeste',(-1,1):'suroeste',(1,0):'este',(-1,0):'oeste',(0,-1):'norte',(0,1):'sur'}
        CD_JEFE, CD_PIEDRA = 5000, 2000
        DURACION_PIEDRA = 5000
        TAM_JEFE, BALAS_JEFE, PIEDRAS_POR_USO = 160, 24, 4
        DAÑO_JEFE, DAÑO_PIEDRA = 35, 15
        VIDA_JEFE, VIDA_REGI = 600, 1000
        MONEDAS_ENEMIGO, MONEDAS_SALA, MONEDAS_JEFE, MONEDAS_REGI = 4, 10, 120, 250

        def armar_reglas():
            """Reglas generales del combate: choques, tipos, modificadores y a quien se le puede pegar."""
            def mover(rect, dx, dy, piedras):
                r = rect.copy(); r.x += dx
                if not any(r.colliderect(piedra) for piedra in piedras): rect.x += dx
                r = rect.copy(); r.y += dy
                if not any(r.colliderect(piedra) for piedra in piedras): rect.y += dy

            def tipo_combate(datos):
                tipos = datos.get('tipo') or []
                return normalizar_tipo(tipos[0]) if tipos else None

            def daño_con_tipo(daño, ataque_tipo, defensa_tipo):
                m = multiplicador_tipos(ataque_tipo, defensa_tipo)
                if mundo['ent']: m *= entorno.mult_clima(mundo['ent'], ataque_tipo)   # lluvia potencia agua, sol potencia fuego, etc.
                if daño <= 0: return 0
                return max(1, round(daño * m))

            def mod(j, clave):
                """Multiplicador del entorno (terreno, maquinas, clima) por lo comprado en la tienda."""
                return j['entorno'].get(clave, 1.0) * tienda.mult(j['inventario'], clave)

            def objetivos_de(nivel, con_objetos=True):
                """A quien le pueden pegar los ataques: enemigos, jefe y objetos rompibles."""
                lista = nivel['enemigos'][:] + ([nivel['jefe']] if nivel['jefe'] else [])
                return lista + (entorno.destructibles(nivel['ent']) if con_objetos else [])

            return mover, tipo_combate, daño_con_tipo, mod, objetivos_de

        mover, tipo_combate, daño_con_tipo, mod, objetivos_de = armar_reglas()

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
                    if not mt or not mts.datos(mt): continue
                    if k < 2: basicos[k] = mt
                    else: especiales[k - 2] = (mt, mts.datos(mt))
                g['basicos'], g['especiales'] = basicos, especiales
                return g

            def nombre_mov(nombre):
                if not nombre: return '-'
                return mts.MTS[nombre]['nombre'][3:] if nombre in mts.MTS else nombre.replace('_', ' ')

            def datos_mov(nombre):
                return mts.datos(nombre) or buscar_movimiento(nombre)

            def reiniciar_asistencia(m):
                m['asist_listo'] = tiempo() + round(m['asist']['enfriamiento'] * 0.3)

            def actualizar_sinergia(j):
                total = {}
                for i, m in enumerate(j['equipo']):
                    if i == j['activo'] or m['vida'] <= 0: continue
                    for clave, valor in sinergia_de(m['nombre']).items(): total[clave] = total.get(clave, 0) + valor
                j['sinergia'] = total

            def aplicar_pokemon(j, nombre, vida=None, centro=None):
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
                     'monedas': 0, 'inventario': tienda.inventario_nuevo(), 'entorno': {}, 'oculto': False, 'inercia': [0.0, 0.0], 'reserva': []}
                aplicar_pokemon(j, equipo[0], centro=centro)
                actualizar_sinergia(j)
                return j

            def guardar_activo(j):
                j['equipo'][j['activo']]['vida'] = j['vida']

            def cambiar_slot(j, indice, forzar=False):
                ahora = tiempo()
                if not 0 <= indice < len(j['equipo']) or indice == j['activo']: return False
                m = j['equipo'][indice]
                if m['vida'] <= 0: return False
                if not forzar and (j['atacando'] or j['embestida'] or ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO): return False
                guardar_activo(j)
                j['activo'] = indice; j['ultimo_cambio'] = ahora; j['buffs'] = {}
                aplicar_pokemon(j, m['nombre'], m['vida'])
                actualizar_sinergia(j)
                return True

            def equipar_debug(j, nombre, espacio):
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
                """Al entrar a una sala: te pone en la entrada. La vida sigue como estaba, mas un poquito para los que siguen en pie."""
                guardar_activo(j)
                for m in j['equipo']:
                    if RESTAURAR_VIDA_ENTRE_SALAS: m['vida'] = m['max_vida']
                    elif m['vida'] > 0: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] * CURA_SALA)
                    reiniciar_asistencia(m)
                j.update({'direccion': 'norte', 'moviendose': False, 'corriendo': False, 'llave': False, 'energia': ENERGIA_MAX, 'agotado': False, 'buffs': {},
                          'resto': [0.0, 0.0], 'inercia': [0.0, 0.0], 'entorno': {}, 'oculto': False})
                aplicar_pokemon(j, j['nombre'], j['equipo'][j['activo']]['vida'], centro=centro)
                actualizar_sinergia(j)

            def mult_buff(j, clave):
                b = j['buffs'].get(clave)
                return b[0] if b and tiempo() < b[1] else 1.0

            def velocidad_actual(j):
                return j['velocidad'] * mult_buff(j, 'velocidad') * (1 + j['sinergia'].get('velocidad', 0)) * (MULT_SPRINT if j['corriendo'] else 1.0) * mod(j, 'velocidad') * j['mults']['velocidad']

            return (crear_miembro, juego_de, nombre_mov, datos_mov, actualizar_sinergia, aplicar_pokemon, crear_jugador, guardar_activo,
                    cambiar_slot, equipar_debug, reiniciar_jugador, mult_buff, velocidad_actual)

        (crear_miembro, juego_de, nombre_mov, datos_mov, actualizar_sinergia, aplicar_pokemon, crear_jugador, guardar_activo, cambiar_slot,
         equipar_debug, reiniciar_jugador, mult_buff, velocidad_actual) = armar_equipo()

        def armar_movimiento():
            """Mover al jugador, la camara y hacia donde apunta."""
            def mover_jugador(j, piedras):
                dx, dy = controles.direccion()                   # teclas del perfil, palanca o cruz del control
                j['moviendose'] = bool(dx or dy)
                if j['agotado'] and j['energia'] >= ENERGIA_MIN: j['agotado'] = False
                gratis = mult_buff(j, 'sprint') > 1 or j['entorno'].get('sprint_gratis')     # en el hielo los de hielo corren gratis
                j['corriendo'] = j['moviendose'] and controles.mantiene('correr') and (gratis or not j['agotado'])
                if j['corriendo']:
                    if not gratis: j['energia'] = max(0.0, j['energia'] - GASTO_SPRINT * tienda.mult(j['inventario'], 'gasto'))
                    if j['energia'] <= 0 and not gratis: j['agotado'] = True; j['corriendo'] = False
                else:
                    j['energia'] = min(ENERGIA_MAX, j['energia'] + REGEN_ENERGIA * mod(j, 'regen'))
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
                return max(0, min(j['rect'].centerx - W // 2, ESC.width - W)), max(0, min(j['rect'].centery - H // 2, ESC.height - H))

            def apuntar(j):
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
                cx, cy = camara(j)
                mx, my = pantalla.raton()
                px, py = j['rect'].center
                if j['uso'] == 'teclas': mx, my = px - cx + j['aim'][0] * 250, py - cy + j['aim'][1] * 250
                vx, vy = mx + cx - px, my + cy - py
                n = math.hypot(vx, vy)
                if n > alcance: vx, vy = vx / n * alcance, vy / n * alcance
                return px + vx, py + vy

            def direccion_de(v):
                sx = 0 if abs(v.x) < abs(v.y) * 0.4 else (1 if v.x > 0 else -1)
                sy = 0 if abs(v.y) < abs(v.x) * 0.4 else (1 if v.y > 0 else -1)
                return DIRS.get((sx, sy), 'sur')

            return mover_jugador, camara, apuntar, punto_apuntado, direccion_de

        mover_jugador, camara, apuntar, punto_apuntado, direccion_de = armar_movimiento()

        def armar_ataques():
            """Ataques del jugador (basicos, especiales, asistencias, embestidas) y el daño que recibe."""
            def preparar(j, datos):
                datos = dict(datos)
                datos['tipo'] = datos.get('tipo') or datos.get('tipo_ataque') or tipo_combate(j['datos'])
                try: base = float(datos.get('daño', 0))
                except (TypeError, ValueError): base = 0
                extra = mod(j, 'daño') * tienda.mult_tipo(j['inventario'], normalizar_tipo(datos['tipo'])) * tienda.critico(j['inventario'])
                stat = j['mults']['fisico' if datos.get('forma') in ('cuerpo', 'embestida') else 'especial']   # Ataque o At. Esp. segun el golpe
                datos['daño'] = round(base * j['juego']['mult_daño'] * mult_buff(j, 'daño') * (1 + j['sinergia'].get('daño', 0)) * extra * stat
                                      * (100 if trucos.get('golpe_letal') else 1))
                return datos

            def enfriamiento_de(j, datos):
                try: base = max(0, int(float(datos.get('enfriamiento', 300))))
                except (TypeError, ValueError): base = 300
                if trucos.get('sin_enfriamiento'): return 0
                return round(base * j['juego']['mult_enfriamiento'] * (1 - j['sinergia'].get('enfriamiento', 0)) * mult_buff(j, 'enfriamiento') * mod(j, 'enfriamiento'))

            def iniciar_ataque(j, forma, enfriamiento, movimiento=None, tipo=None):
                a = j['animador']
                anim = a.buscar_movimiento(movimiento, normalizar_tipo(tipo), forma)   # Punch, Kick, Shock... si el sprite la tiene
                if not anim: return
                a.ritmo = max(0.8, min(1.6, 450.0 / max(1, enfriamiento)))
                j['atacando'] = True; j['anim_ataque'] = anim; j['dir_ataque'] = direcciones.index(j['direccion'])
                a.cambiar(anim, j['dir_ataque'], False)

            def golpear(j, datos, objetivos, efectos=None):
                ax, ay = j['aim']
                try: d = max(1, int(float(datos.get('distancia', 50))))
                except (TypeError, ValueError): d = 50
                try: area = max(1, int(float(datos.get('area', 20))))
                except (TypeError, ValueError): area = 20
                px, py = j['rect'].center
                for objetivo in objetivos:
                    if objetivo['vida'] <= 0: continue
                    mitad = max(objetivo['rect'].width, objetivo['rect'].height) / 2
                    vx, vy = objetivo['rect'].centerx - px, objetivo['rect'].centery - py
                    adelante, lado = vx * ax + vy * ay, abs(vx * ay - vy * ax)
                    if -mitad <= adelante <= d + mitad and lado <= area + mitad:
                        recibir_ataque(objetivo, datos, j['direccion'])
                entorno.reaccionar_linea(mundo['ent'], px, py, px + ax * d, py + ay * d, max(20, area), datos.get('tipo'), tiempo())   # congela, quema...
                if efectos is not None:
                    ahora = tiempo()
                    efectos.append({'x': px, 'y': py, 'linea': (px + ax * d, py + ay * d), 'radio': max(3, min(area, 14)), 'tipo': datos.get('tipo'), 'inicio': ahora, 'hasta': ahora + 130})

            def lanzar(j, datos, proyectiles):
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
                vx, vy = j['aim']
                n = 1.0
                try: distancia = float(datos.get('distancia', 180))
                except (TypeError, ValueError): distancia = 180.0
                try: velocidad = max(1.0, float(datos.get('velocidad', 15)))
                except (TypeError, ValueError): velocidad = 15.0
                j['embestida'] = {'vx': vx / n, 'vy': vy / n, 'restante': distancia, 'velocidad': velocidad, 'datos': datos, 'golpeados': [], 'resto': [0.0, 0.0]}

            def actualizar_embestida(j, objetivos, piedras):
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

            def usar_basico(j, indice, nivel):
                nombre = j['juego']['basicos'][indice]
                base = datos_mov(nombre) if nombre else None
                if not base: return
                if indice == 1 and not mts.datos(nombre):            # el basico a distancia: menos daño, mas recarga y menos alcance
                    base = dict(base)
                    for clave, k in BASICO_DISTANCIA.items():
                        try: base[clave] = float(base.get(clave, 0)) * k
                        except (TypeError, ValueError): pass
                datos = preparar(j, base)
                ahora = tiempo(); enfriamiento = enfriamiento_de(j, datos)
                clave = 'ultimo_golpe' if indice == 0 else 'ultimo_proyectil'
                if j['atacando'] or j['embestida'] or ahora - j[clave] < enfriamiento: return
                j[clave] = ahora
                iniciar_ataque(j, datos.get('forma', 'cuerpo'), enfriamiento, nombre, datos['tipo'])
                if datos.get('forma') == 'proyectil': lanzar(j, datos, nivel['proyectiles_pokemon'])
                else: golpear(j, datos, objetivos_de(nivel), nivel['efectos'])

            def usar_especial(j, indice, nivel):
                nombre, base = j['juego']['especiales'][indice]
                datos = preparar(j, base)
                forma = datos.get('forma', 'proyectil')
                ahora = tiempo(); enfriamiento = enfriamiento_de(j, datos)
                if j['atacando'] or j['embestida'] or ahora - j['esp_ultimo'][indice] < enfriamiento: return
                j['esp_ultimo'][indice] = ahora
                iniciar_ataque(j, forma, enfriamiento, nombre, datos['tipo'])
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
                    curar_equipo(j, porcentaje / 100)

            def curar_equipo(j, parte, banca=CURA_BANCA):
                """Cura al que pelea esa parte de su vida y a los de la banca que siguen en pie 'banca' veces eso. Los debilitados no vuelven."""
                j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * parte)
                for i, m in enumerate(j['equipo']):
                    if i != j['activo'] and m['vida'] > 0: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] * parte * banca)
                efectos.cura(mundo['ef'], *j['rect'].center)

            def usar_asistencia(j, k, nivel):
                ahora = tiempo()
                reserva = [m for i, m in enumerate(j['equipo']) if i != j['activo']]
                if k >= len(reserva): return
                m = reserva[k]
                if m['vida'] <= 0 or ahora < m['asist_listo']: return
                a = m['asist']; mec = a['mecanica']
                objetivos = objetivos_de(nivel, mec != 'desvanecer')        # desvanecer no borra objetos
                m['asist_listo'] = ahora + a['enfriamiento']
                entorno.al_usar_movimiento(nivel['ent'], a['nombre'], ahora)   # hidrobomba trae lluvia, llamarada sol, trueno tormenta...
                if mec == 'impacto':
                    datos = {'tipo': a['tipo'], 'daño': round(a['daño'] * a['mult_daño']), 'area': a['area'], 'retroceso': 30, 'efecto': a['efecto']}
                    area_efecto(j, datos, objetivos, nivel['efectos'], punto_apuntado(j, a['alcance']))
                elif mec in ('escudo', 'furia', 'carrera'):
                    for clave, valor in a['buffs'].items(): j['buffs'][clave] = (valor, ahora + a['duracion'])
                    nivel['efectos'].append({'x': j['rect'].centerx, 'y': j['rect'].centery, 'radio': 45, 'tipo': a['tipo'], 'inicio': ahora, 'hasta': ahora + 500})
                elif mec == 'curar':
                    curar_equipo(j, a['porcentaje'] / 100)
                    nivel['efectos'].append({'x': j['rect'].centerx, 'y': j['rect'].centery, 'radio': 45, 'tipo': 'planta', 'inicio': ahora, 'hasta': ahora + 500})
                elif mec == 'desvanecer':
                    centro = pygame.Vector2(punto_apuntado(j, a['alcance']))
                    for o in objetivos:
                        if o['vida'] > 0 and centro.distance_to(o['rect'].center) <= a['area'] + max(o['rect'].width, o['rect'].height) / 2:
                            if o is nivel['jefe']: o['vida'] = max(0, o['vida'] - o['max_vida'] * a['porcentaje_jefe'] / 100)
                            else: o['vida'] = 0
                    nivel['efectos'].append({'x': centro.x, 'y': centro.y, 'radio': a['area'], 'tipo': 'fantasma', 'inicio': ahora, 'hasta': ahora + 600})
                elif mec == 'masivo':
                    datos = {'tipo': 'normal', 'daño': a['daño'], 'area': a['area'], 'retroceso': 0, 'efecto': a['efecto']}
                    area_efecto(j, datos, objetivos, nivel['efectos'])

            def actualizar_jugador(j):
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

            def dañar_jugador(j, daño, tipo=None):
                try: daño = max(0, float(daño))
                except (TypeError, ValueError): daño = 0
                if tipo: daño = daño_con_tipo(daño, tipo, j['tipos'])
                daño *= mult_buff(j, 'defensa') * (1 - j['sinergia'].get('defensa', 0)) * mod(j, 'defensa') * j['mults']['defensa']
                if trucos.get('vida_infinita'): return
                j['vida'] = max(0, j['vida'] - daño)

            def recibir_ataque(obj, datos, direccion=None):
                color = COLORES_TIPO.get(normalizar_tipo(datos.get('tipo')), (255, 255, 255))
                efectos.golpe(mundo['ef'], *obj['rect'].center, color, normalizar_tipo(datos.get('tipo')))   # chispas del color del tipo
                if obj.get('objeto'):                                   # barriles, arboles, autos...: los maneja el entorno
                    entorno.dañar_objeto(mundo['ent'], obj, datos, direccion, tiempo()); return
                ataque_tipo = datos.get('tipo') or datos.get('tipo_ataque')
                defensa_tipo = obj.get('tipo')
                try: daño_base = float(datos.get('daño', 0))
                except (TypeError, ValueError): daño_base = 0
                daño = daño_con_tipo(daño_base, ataque_tipo, defensa_tipo)
                obj['vida'] = max(0, obj['vida'] - daño)
                efecto = datos.get('efecto'); ahora = tiempo()
                obj['golpe_hasta'] = ahora + 280                       # pone la animacion Hurt un ratito
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
                    recibir_ataque, curar_equipo)

        (enfriamiento_de, actualizar_embestida, usar_basico, usar_especial, usar_asistencia, actualizar_jugador, dañar_jugador,
         recibir_ataque, curar_equipo) = armar_ataques()

        def armar_enemigos():
            """Enemigos, proyectiles y jefes."""
            def elegir_pokemon_enemigo(era):
                """Pokemon al azar de los de la era (primero los que tienen sprites)."""
                pool = [n for n in mundos.ERAS[era]['enemigos'] if n in pokemones]
                return random.choice([n for n in pool if tiene_sprites(n)] or pool or list(JUGABLES))

            def crear_enemigo(nivel, punto=None, cazando=None):
                """Enemigo de la era de la sala, mas fuerte cuanto mas avanzas."""
                nombre = elegir_pokemon_enemigo(nivel['sala']['era'])
                tipo = normalizar_tipo((pokemones[nombre].get('tipo') or ['normal'])[0])
                r = pygame.Rect(0, 0, 50, 50)
                r.center = punto or entorno.punto_libre(nivel['ent'], random, nivel['sala']['inicio'], 450)
                visual = max(34, min(70, datos_juego(nombre)['tamaño'] + 8))
                nv = max(1, nivel['nivel_enemigos'] + random.randint(-1, 1))   # nivel del enemigo: mas vida y mas daño cuanto mas alto
                vida = round(100 * progreso.crecimiento(nombre, nv, 'hp'))
                e = {'tipo': tipo, 'nombre': nombre, 'nivel': nv, 'animador': AnimadorPokemon(nombre, r, visual), 'direccion': 'sur', 'prev': r.center, 'rect': r,
                     'vida': vida, 'max_vida': vida, 'daño': round(DAÑO_ENEMIGO * progreso.crecimiento(nombre, nv, 'attack')), 'color': COLORES_TIPO.get(tipo, (150, 150, 150)), 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0, 'entorno': {}}
                ia.preparar(e)
                if cazando: e['estado_ia'] = 'caza'; e['ultima_vista'] = cazando     # las oleadas ya saben donde estas
                return e

            def actualizar_animacion_enemigo(e):
                a = e['animador']
                c = e['rect'].center
                dx, dy = c[0] - e['prev'][0], c[1] - e['prev'][1]
                e['prev'] = c
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
                d = direcciones.index(e['direccion'])
                especial = anim_especial_enemigo(e, a)
                if especial: a.ritmo = 1.0; a.cambiar(especial[0], d, especial[1])
                elif e.get('amigable') and e['camina'] <= 0: a.cambiar('sit', 0, True) or a.cambiar('idle', d, True)   # el que se quiere unir se sienta
                else: a.cambiar('walk' if e['camina'] > 0 else 'idle', d, True)
                a.actualizar()

            def anim_especial_enemigo(e, a):
                """(animacion, repetir) si el enemigo esta dormido, golpeado o atacando; None si solo camina."""
                ahora = tiempo()
                if e['estado'] == 'dormir' and e['estado_hasta'] > ahora: return 'sleep', True
                if e.get('golpe_hasta', 0) > ahora: return 'hurt', False
                clase = (e.get('aviso') or {}).get('clase') or ('embestida' if e.get('embestida_ia') else None)
                if not clase: return None
                cache = e.setdefault('anims', {})                     # se busca una sola vez por clase de ataque
                if clase not in cache:
                    forma = {'golpe': 'cuerpo', 'disparo': 'proyectil', 'rafaga': 'proyectil', 'pisoton': 'area'}.get(clase, clase)
                    cache[clase] = a.buscar_movimiento(None, e['tipo'], forma)
                return (cache[clase], False) if cache[clase] else None

            def dibujar_enemigo(e, cx, cy):
                r = e['rect']
                pygame.draw.ellipse(ventana, e['color'], (r.x - cx, r.bottom - cy - 12, r.width, 14), 3)
                centro = r.center
                r.center = (centro[0] - cx, centro[1] - cy)
                ok = e['animador'].dibujar(ventana)
                r.center = centro
                return ok

            def actualizar_estado(e):
                ahora = tiempo()
                if e['estado'] == 'quemar' and e['proximo_estado'] <= ahora < e['estado_hasta']:
                    e['vida'] = max(0, e['vida'] - 3); e['proximo_estado'] = ahora + 700
                if ahora >= e['estado_hasta']: e['estado'] = None

            def crear_proyectil(x, y, dx, dy, daño, jefe=False, tipo=None, vel=VEL_P_ENEMIGO, alcance=DIST_P_ENEMIGO):
                return {'x': float(x), 'y': float(y), 'dx': dx, 'dy': dy, 'daño': daño, 'jefe': jefe, 'tipo': tipo, 'distancia': 0, 'activo': True,
                        'vel': vel, 'alcance': alcance, 'rect': pygame.Rect(int(x)-8, int(y)-8, 16, 16)}

            def actualizar_proyectil(proyectil, j, piedras):
                v = proyectil['vel']
                proyectil['x'] += proyectil['dx'] * v; proyectil['y'] += proyectil['dy'] * v; proyectil['distancia'] += v
                proyectil['rect'].center = round(proyectil['x']), round(proyectil['y'])
                entorno.reaccionar(mundo['ent'], proyectil['x'], proyectil['y'], 8, proyectil.get('tipo'), tiempo())   # las balas de hielo tambien congelan
                if proyectil['distancia'] >= proyectil['alcance'] or not ESC.colliderect(proyectil['rect']) or proyectil['rect'].collidelist(piedras) != -1:
                    proyectil['activo'] = False; return
                if proyectil['rect'].colliderect(j['rect']): dañar_jugador(j, proyectil['daño'], proyectil.get('tipo')); proyectil['activo'] = False

            def actualizar_proyectil_pokemon(proyectil, objetivos, piedras):
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

            def crear_jefe(nivel, nombre, vida, nv):
                """Jefe, Regi o Arceus: aparece arriba del centro de la arena."""
                r = pygame.Rect(0, 0, TAM_JEFE, TAM_JEFE)
                r.center = (ESC.centerx, ESC.centery - nivel['sala']['tam'] * 2)
                tipo = normalizar_tipo((pokemones.get(nombre, {}).get('tipo') or ['normal'])[0])
                ahora = tiempo()
                jefe = {'rect': r, 'nombre': nombre, 'nivel': nv, 'jefe': True, 'vida': vida, 'max_vida': vida, 'daño': round(DAÑO_JEFE * progreso.crecimiento(nombre, nv, 'attack')), 'tipo': tipo,
                        'color': COLORES_TIPO.get(tipo, (255, 140, 0)), 'ultimo_golpe': 0, 'ultimo_disparo': ahora, 'ultimo_poder': ahora,
                        'animador': AnimadorPokemon(nombre, r, TAM_JEFE), 'direccion': 'sur', 'prev': r.center, 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0, 'entorno': {}}
                ia.preparar_jefe(jefe)
                return jefe

            def crear_piedras_verdes(jefe):
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
                if not (jefe['estado'] in ('paralizar', 'dormir') and jefe['estado_hasta'] > ahora): ia.actualizar_jefe(jefe, contexto)
                jefe['rect'].clamp_ip(AREA)
                if ahora - jefe['ultimo_disparo'] >= CD_JEFE:
                    for i in range(BALAS_JEFE):
                        a = i * math.tau / BALAS_JEFE; dx, dy = math.cos(a), math.sin(a); r = TAM_JEFE//2+10
                        proyectiles.append(crear_proyectil(jefe['rect'].centerx+dx*r, jefe['rect'].centery+dy*r, dx, dy, round(jefe['daño'] * 0.7), True, jefe['tipo']))
                    jefe['ultimo_disparo'] = ahora
                if ahora - jefe['ultimo_poder'] >= CD_PIEDRA:
                    verdes.extend(crear_piedras_verdes(jefe)); jefe['ultimo_poder'] = ahora
                if jefe['rect'].colliderect(j['rect']) and ahora-jefe['ultimo_golpe'] >= 700:
                    dañar_jugador(j, jefe['daño'], jefe['tipo']); jefe['ultimo_golpe'] = ahora

            return (crear_enemigo, actualizar_animacion_enemigo, dibujar_enemigo, actualizar_estado, crear_proyectil, actualizar_proyectil,
                    actualizar_proyectil_pokemon, crear_jefe, actualizar_jefe)

        (crear_enemigo, actualizar_animacion_enemigo, dibujar_enemigo, actualizar_estado, crear_proyectil, actualizar_proyectil,
         actualizar_proyectil_pokemon, crear_jefe, actualizar_jefe) = armar_enemigos()

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

            def crear_nivel(rec, destino, entrada, j):
                """Arma la sala actual del recorrido: mapa, entorno, puertas con su destino, enemigos y el cartel de entrada."""
                era, tipo = rec['era'], mundos.tipo_sala(rec)
                destinos = mundos.destinos_siguientes(rec, random)
                semilla = random.random()
                if tipo == 'tienda':
                    destinos = destinos[:2]
                    sala = generacion.generar_tienda(era, ['oeste', 'este'][:len(destinos)], semilla)
                elif tipo in ('jefe', 'regi', 'final'):
                    destinos = destinos[:1]
                    sala = generacion.generar_arena(era, ['norte'], semilla, tipo)
                else:
                    variantes = mundos.ERAS[era]['variantes']
                    variante = destino['variante'] if destino and destino.get('variante') in variantes else random.choice(list(variantes))
                    lados = random.sample([l for l in generacion.LADOS if l != entrada], len(destinos))
                    sala = generacion.generar_sala(era, variante, entrada, lados, semilla)
                for puerta, d in zip(sala['puertas'], destinos): puerta['destino'] = d
                ESC.size = sala['esc'].size                              # la sala nueva puede tener otro tamaño (la tienda)
                AREA.update(generacion.crear_area(ESC, sala['tam']))
                datos_era = mundos.ERAS[era]
                clima = datos_era.get('clima_regi') if tipo == 'regi' else datos_era.get('clima_final') if tipo == 'final' else None
                ent = entorno.crear(sala, clima or rec['clima'], tiempo())
                mundo['ent'] = ent
                tienda.nueva_sala(j['inventario'], tipo)
                esc = mundos.escala(era, rec['sala'])
                nivel = {'sala': sala, 'ent': ent, 'tipo': tipo, 'escala': esc, 'enemigos': [], 'jefe': None, 'proyectiles_pokemon': [], 'proyectiles_enemigos': [],
                         'efectos': [], 'verdes': [], 'puertas': sala['puertas'], 'llave': None, 'completado': tipo == 'tienda', 'monedas': [], 'bayas': [], 'carteles': [],
                         'oleadas': [], 'apariciones': [], 'vitrinas': [], 'salida': None, 'nivel_enemigos': progreso.nivel_de_sala(era, rec['sala'], tipo),
                         'amigo': None, 'entrando_hasta': tiempo() + DURACION_ENTRADA, 'saliendo': None, 'frame': 0}
                mundo['ef']['parts'], mundo['ef']['anims'] = [], []
                if tipo == 'tienda':
                    tipos_equipo = {normalizar_tipo(t) for m in j['equipo'] for t in pokemones[m['nombre']].get('tipo', [])}
                    necesita = {r['objeto'] for m in j['equipo'] for r in progreso.requisitos(m['nombre']) if 'objeto' in r}
                    items = tienda.surtido(random, tipos_equipo, sala['vitrinas'], [m['nombre'] for m in j['equipo']], necesita)
                    nivel['vitrinas'] = [dict(v, item=i, vendido=False) for v, i in zip(sala['vitrinas'], items)]
                    titulo = 'Tienda de Chikorita'
                elif tipo in ('jefe', 'regi', 'final'):
                    nombre = mundos.jefe_de(era, tipo)
                    nv = nivel['nivel_enemigos']
                    vida = round((VIDA_JEFE if tipo == 'jefe' else VIDA_REGI * (1.5 if tipo == 'final' else 1)) * progreso.crecimiento(nombre, nv, 'hp'))
                    nivel['jefe'] = crear_jefe(nivel, nombre, vida, nv)
                    titulo = nombre.title()
                else:
                    total = max(3, round(esc['cantidad'] * tienda.factor_enemigos(j['inventario'])))
                    partes = 1 if rec['sala'] < 3 else random.choice((2, 2, 3))
                    oleadas = repartir(total, partes)
                    nivel['enemigos'] = [crear_enemigo(nivel) for _ in range(oleadas[0])]   # la primera oleada ya esta (sin verte todavia)
                    nivel['oleadas'] = oleadas[1:]
                    titulo = sala['variante'].capitalize()
                clima_txt = 'Interior' if ent['clima'] is None else entorno.CLIMAS[ent['clima']]['nombre']
                sub = datos_era['nombre'] + '  -  Sala ' + str(rec['sala'] + 1) + '/' + str(mundos.salas_de(rec)) + '  -  ' + clima_txt
                cartel(nivel, titulo, 2800, sub, grande=True)
                return nivel

            def soltar_monedas(nivel, j, x, y, cantidad):
                cantidad = max(1, round(cantidad * tienda.mult(j['inventario'], 'monedas')))
                nivel['monedas'].append({'x': float(x), 'y': float(y), 'valor': cantidad})

            def tecla_de(accion):
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
                    cartel(nivel, m['nombre'].title() + ' subio al nivel ' + str(m['nivel']) + '!')
                    if progreso.evoluciones(m, j['inventario']['objetos']): cartel(nivel, m['nombre'].title() + ' puede evolucionar! (' + tecla_de('equipo') + ')', 2200)

            def quiza_amigo(nivel, j, e):
                """A veces un pokemon derrotado quiere unirse a vos (no se captura: se hace tu amigo). Uno por sala como mucho."""
                if nivel['amigo'] or e.get('jefe'): return
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

            def comprar_cercano(nivel, j):
                """E en la tienda: compra lo que tenes adelante. Devuelve True si habia algo para comprar."""
                v = vitrina_cercana(nivel, j) if nivel['tipo'] == 'tienda' else None
                if not v: return False
                precio = tienda.ITEMS[v['item']]['precio']
                mensaje = tienda.comprar(j, v['item'])
                if mensaje.startswith('Compraste'):
                    v['vendido'] = True; ganar_xp(nivel, j, precio // 6)   # comprar tambien da experiencia
                    for o in nivel['ent']['objetos']:                    # Chikorita asiente cuando le compras
                        if o['nombre'] == 'chikorita' and 'animador' in o: o['animador'].cambiar('nod', 0, False)
                cartel(nivel, mensaje)
                return True

            def actualizar_nivel(nivel, j):
                ahora = tiempo(); ent = nivel['ent']; enemigos = nivel['enemigos']; jefe = nivel['jefe']
                solidos_j, solidos_p = entorno.solidos(ent, j['tipos']), entorno.solidos_proyectil(ent)
                objetivos = objetivos_de(nivel)
                nivel['frame'] += 1
                if trucos.get('monedas_infinitas'): j['monedas'] = 99999
                if ahora < nivel['entrando_hasta']:                      # entrando a la sala: camina solo desde la puerta
                    ix, iy = nivel['sala']['inicio']
                    dx, dy = ix - j['rect'].centerx, iy - j['rect'].centery
                    paso = min(math.hypot(dx, dy), 3.2)
                    if paso > 0.5:
                        j['rect'].x += round(dx / math.hypot(dx, dy) * paso); j['rect'].y += round(dy / math.hypot(dx, dy) * paso)
                        j['direccion'] = direccion_de(pygame.Vector2(dx, dy)); j['moviendose'] = True
                    else: j['moviendose'] = False
                elif j['embestida']: actualizar_embestida(j, objetivos, solidos_j); j['moviendose'] = True
                else: mover_jugador(j, solidos_j)
                actualizar_jugador(j)
                if (j['corriendo'] or j['embestida']) and nivel['frame'] % 4 == 0: efectos.polvo(mundo['ef'], j['rect'].centerx, j['rect'].bottom)
                efectos.actualizar(mundo['ef'])
                contexto = {'ent': ent, 'jugador': j, 'enemigos': enemigos + ([jefe] if jefe else []), 'ahora': ahora,
                            'dañar_jugador': lambda d, t: dañar_jugador(j, d, t),
                            'dañar_enemigo': lambda e, d, t, ef: recibir_ataque(e, {'tipo': t, 'daño': d, 'efecto': ef, 'retroceso': 0}),
                            'disparar': lambda x, y, dx, dy, d, t, v, dist: nivel['proyectiles_enemigos'].append(crear_proyectil(x, y, dx, dy, round(d), False, t, v, dist))}
                entorno.actualizar(ent, contexto, ahora)                 # terreno, maquinas, fuego, clima, objetos empujados, explosiones
                for ev in ent['eventos']:                                # lo que paso en el entorno: monedas, cosas rotas, explosiones
                    if ev[0] == 'monedas': soltar_monedas(nivel, j, ev[1], ev[2], ev[3])
                    elif ev[0] == 'roto': efectos.romper(mundo['ef'], ev[1], ev[2], ev[3]); ganar_xp(nivel, j, 2 + nivel['nivel_enemigos'] // 3)
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
                        if random.random() < PROB_BAYA: nivel['bayas'].append({'x': e['rect'].centerx + 18, 'y': e['rect'].centery})
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
                    if ahora >= a['hasta']: nivel['enemigos'].append(crear_enemigo(nivel, a['pos'], j['rect'].center)); nivel['apariciones'].remove(a)
                if jefe:
                    actualizar_estado(jefe)
                    actualizar_jefe(jefe, j, nivel['proyectiles_enemigos'], nivel['verdes'], contexto)
                    actualizar_animacion_enemigo(jefe)
                    if jefe['vida'] <= 0:
                        nivel['jefe'] = None
                        soltar_monedas(nivel, j, *jefe['rect'].center, MONEDAS_REGI if nivel['tipo'] != 'jefe' else MONEDAS_JEFE)
                        cartel(nivel, jefe['nombre'].title() + ' fue derrotado!', 2000)
                        efectos.explosion(mundo['ef'], *jefe['rect'].center, 160)
                        ganar_xp(nivel, j, progreso.xp_por_derrota(jefe['nombre'], jefe['nivel'], j['nivel'], True))
                        premio_jefe(nivel, j, jefe)
                for proyectil in nivel['proyectiles_enemigos']: actualizar_proyectil(proyectil, j, solidos_p)
                nivel['proyectiles_enemigos'] = [proyectil for proyectil in nivel['proyectiles_enemigos'] if proyectil['activo']]
                for piedra_verde in nivel['verdes'][:]:
                    if ahora - piedra_verde['tiempo'] >= DURACION_PIEDRA: nivel['verdes'].remove(piedra_verde); continue
                    if j['rect'].colliderect(piedra_verde['rect']) and ahora-piedra_verde['daño'] >= 500: dañar_jugador(j, DAÑO_PIEDRA); piedra_verde['daño'] = ahora
                for moneda in nivel['monedas'][:]:                       # monedas: se juntan al pasar (y vienen solas cuando termina la sala)
                    dx, dy = j['rect'].centerx - moneda['x'], j['rect'].centery - moneda['y']
                    d = math.hypot(dx, dy)
                    if d < 40: j['monedas'] += moneda['valor']; nivel['monedas'].remove(moneda); continue
                    if nivel['completado'] or d < 110: moneda['x'] += dx / d * 9; moneda['y'] += dy / d * 9
                for baya in nivel['bayas'][:]:                           # las bayas no vienen solas: hay que ir a buscarlas
                    if math.hypot(j['rect'].centerx - baya['x'], j['rect'].centery - baya['y']) < 36:
                        nivel['bayas'].remove(baya); curar_equipo(j, CURA_BAYA, 0); cartel(nivel, 'Baya Oran! +' + str(round(CURA_BAYA * 100)) + '% de vida', 1400)
                derrotados = not nivel['enemigos'] and nivel['jefe'] is None and not nivel['oleadas'] and not nivel['apariciones']
                if derrotados and not nivel['completado']:
                    nivel['completado'] = True
                    cartel(nivel, 'Sala completada!')
                    soltar_monedas(nivel, j, *ESC.center, MONEDAS_SALA + 3 * nivel['sala']['era'])
                    ganar_xp(nivel, j, progreso.xp_por_derrota(j['nombre'], nivel['nivel_enemigos'], j['nivel']))
                    for i, m in enumerate(j['equipo']): m['amistad'] = min(255, m['amistad'] + (2 if i == j['activo'] else 1))   # pasar salas juntos
                if nivel['completado'] and nivel['llave'] is None and not j['llave']:
                    nivel['llave'] = pygame.Rect(ESC.centerx-15, ESC.centery-15, 30, 30)
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
                elif j['llave']:
                    for puerta in nivel['puertas']:
                        if j['rect'].colliderect(puerta['rect'].inflate(20, 20)):
                            cx, cy = camara(j)
                            nivel['saliendo'] = {'puerta': puerta, 'hasta': ahora + 320}
                            efectos.transicion(mundo['ef'], 'salir', ahora, (j['rect'].centerx - cx, j['rect'].centery - cy))

            return menu_niveles, cartel, crear_nivel, tecla_de, hablar_amigo, vitrina_cercana, comprar_cercano, actualizar_nivel

        menu_niveles, cartel, crear_nivel, tecla_de, hablar_amigo, vitrina_cercana, comprar_cercano, actualizar_nivel = armar_salas()

        def armar_dibujo():
            """Todo lo que se dibuja jugando: jugador, HUD, indicadores, carteles, tienda y objetos."""
            def dibujar_rect(rect, cx, cy, color, forma='rect'):
                r = pygame.Rect(rect.x-cx, rect.y-cy, rect.width, rect.height)
                (pygame.draw.ellipse if forma == 'ellipse' else pygame.draw.rect)(ventana, color, r)

            def dibujar_jugador(j, cx, cy):
                centro = j['rect'].center; j['rect'].center = centro[0]-cx, centro[1]-cy
                ok = j['animador'].dibujar(ventana); j['rect'].center = centro
                if ok: return
                r = pygame.Rect(0,0,j['tamaño'],j['tamaño']); r.center = centro[0]-cx, centro[1]-cy; pygame.draw.rect(ventana, (255,50,255), r)

            def barra(rect, vida, max_vida, alto=5):
                pygame.draw.rect(ventana, (80,0,0), rect)
                pygame.draw.rect(ventana, (0,200,0), (rect[0], rect[1], int(max(0, vida*rect[2]//max(1,max_vida))), rect[3]))

            retratos = {}

            f_hud, f_hud_g, f_hud_b = pygame.font.Font(None, 20), pygame.font.Font(None, 26), pygame.font.Font(None, 30)

            f_hud_b.set_bold(True)

            f_tipo = pygame.font.Font(None, 18)

            def retrato(nombre, radio):
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

            def circulo_poke(centro, radio, nombre, atenuado=False):
                pygame.draw.circle(ventana, 'white', centro, radio)
                img = retrato(nombre, radio - 3)
                if img: ventana.blit(img, (centro[0] - radio + 3, centro[1] - radio + 3))
                else:
                    t = f_hud_g.render(nombre[:2].title(), True, 'black')
                    ventana.blit(t, t.get_rect(center=centro))
                pygame.draw.circle(ventana, 'black', centro, radio, 3)
                if atenuado:
                    velo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                    pygame.draw.circle(velo, (0, 0, 0, 150), (radio, radio), radio)
                    ventana.blit(velo, (centro[0] - radio, centro[1] - radio))

            barras = {}                                              # vida que muestra cada barra (persigue a la real para que se note el cambio)

            def barra_hud(rect, vida, max_vida, clave=None):
                """Barra de vida. Si baja queda un pedazo naranja que se va achicando; si sube se llena en verde y despues se pone roja."""
                x, y, w, h = rect
                real = max(0, vida) / max(1, max_vida)
                b = barras.setdefault(clave, {'vista': real, 't': tiempo()})
                ahora = tiempo(); dt = min(100, ahora - b['t']); b['t'] = ahora
                paso = dt * 0.0006 if abs(real - b['vista']) < 0.5 else dt * 0.0015      # ritmo por tiempo real: igual en cualquier pc
                b['vista'] = max(real, b['vista'] - paso) if b['vista'] > real else min(real, b['vista'] + paso)
                pygame.draw.rect(ventana, 'white', rect)
                if b['vista'] > real:                                # daño: rojo hasta la vida real y naranja hasta lo que tenia
                    pygame.draw.rect(ventana, (255, 150, 40), (x, y, int(w * b['vista']), h))
                    pygame.draw.rect(ventana, (130, 0, 20), (x, y, int(w * real), h))
                else:                                                # cura: rojo hasta lo que se ve y verde hasta lo nuevo
                    pygame.draw.rect(ventana, (60, 210, 90), (x, y, int(w * real), h))
                    pygame.draw.rect(ventana, (130, 0, 20), (x, y, int(w * b['vista']), h))
                pygame.draw.rect(ventana, 'black', rect, 3)

            def dibujar_hud(j, nivel, rec):
                ahora = tiempo()
                circulo_poke((44, 86), 34, j['nombre'])
                barra_hud((80, 68, 240, 36), j['vida'], j['max_vida'], ('hud', j['nombre']))
                t = f_hud.render(str(int(j['vida'])) + '/' + str(j['max_vida']), True, 'white')
                ventana.blit(t, t.get_rect(center=(200, 86)))
                pygame.draw.rect(ventana, (60, 60, 60), (80, 108, 240, 6))
                pygame.draw.rect(ventana, (120, 120, 160) if j['agotado'] else (0, 160, 230), (80, 108, int(240 * j['energia'] / ENERGIA_MAX), 6))
                activo = j['equipo'][j['activo']]
                pygame.draw.rect(ventana, (150, 110, 255), (80, 114, int(240 * progreso.progreso_nivel(activo)), 3))   # experiencia
                nombre_t = f_hud_b.render(j['nombre'].replace('_', ' '), True, 'black')
                ventana.blit(nombre_t, (84, 117))
                ventana.blit(f_hud_g.render('Nv ' + str(activo['nivel']) + (' +' + str(activo['puntos']) + ' EV' if activo['puntos'] else ''), True, (40, 40, 90)),
                             (92 + nombre_t.get_width(), 120))
                monedas = f_hud_g.render('$ ' + str(j['monedas']), True, (250, 215, 60))   # monedas y objetos de la tienda andando
                ventana.blit(monedas, (12, 140))
                for i, linea in enumerate(tienda.activos(j['inventario'])): ventana.blit(f_hud.render(linea, True, (230, 230, 230)), (12, 164 + i * 16))
                esperando = ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO
                k = 0
                for i, m in enumerate(j['equipo']):
                    if i == j['activo']: continue
                    cy = 14 + k * 30
                    circulo_poke((86, cy), 11, m['nombre'], esperando or m['vida'] <= 0)
                    ventana.blit(f_hud.render(str(i + 1), True, 'black'), (68, cy - 6))
                    barra_hud((100, cy - 8, 100, 16), m['vida'], m['max_vida'], ('banca', m['nombre']))
                    ventana.blit(f_hud.render(m['nombre'].replace('_', ' '), True, 'black'), (103, cy + 9))
                    resto = max(0, m['asist_listo'] - ahora)
                    listo = resto == 0 and m['vida'] > 0
                    texto = ('F' if k == 0 else 'G') + ' ' + m['asist']['nombre'].replace('_', ' ') + ' ' + ('LISTO' if not resto else str(resto // 1000 + 1) + 's')
                    ventana.blit(f_hud.render(texto, True, (0, 150, 0) if listo else (90, 90, 90)), (206, cy - 5))
                    k += 1
                for i, (nombre, datos) in enumerate(j['juego']['especiales']):
                    radio = 30 - i * 6
                    cx, cy = W - 60 - i * 85, H - 62
                    enfriamiento = max(1, enfriamiento_de(j, datos))
                    restante = max(0, enfriamiento - (ahora - j['esp_ultimo'][i]))
                    pygame.draw.circle(ventana, 'white', (cx, cy), radio)
                    pygame.draw.circle(ventana, 'black', (cx, cy), radio, 3)
                    tecla = f_hud_g.render('Shift' if i == 0 else 'R', True, 'black')
                    ventana.blit(tecla, tecla.get_rect(center=(cx, cy)))
                    if restante:
                        velo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                        pygame.draw.circle(velo, (0, 0, 0, 160), (radio, radio), radio)
                        ventana.blit(velo, (cx - radio, cy - radio))
                        s = f_hud.render(str(round(restante / 1000, 1)), True, 'white')
                        ventana.blit(s, s.get_rect(center=(cx, cy)))
                    n = f_hud.render(nombre.replace('_', ' '), True, (60, 60, 60))
                    ventana.blit(n, n.get_rect(center=(cx, cy + radio + 12)))
                lugar = f_hud.render(mundos.ERAS[rec['era']]['nombre'] + ' - Sala ' + str(rec['sala'] + 1) + '/' + str(mundos.salas_de(rec)), True, 'white')
                ventana.blit(lugar, lugar.get_rect(midtop=(W // 2, 6)))
                if nivel['jefe']:
                    b = nivel['jefe']
                    ventana.blit(f_hud.render(b['nombre'].title() + ' - ' + b['tipo'], True, 'white'), (W - 300, 4))
                    barra_hud((W - 300, 22, 280, 20), b['vida'], b['max_vida'])

            ZONAS_HUD = [pygame.Rect(0, 0, 340, 200), pygame.Rect(W - 310, 0, 310, 50), pygame.Rect(W - 230, H - 125, 230, 125),
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
                        t = pygame.font.Font(None, 64).render(c['texto'], True, 'white')
                        s = pygame.font.Font(None, 28).render(c['sub'] or '', True, (230, 230, 230))
                        caja = pygame.Surface((max(t.get_width(), s.get_width()) + 60, 110), pygame.SRCALPHA)
                        caja.fill((0, 0, 0, 150))
                        caja.blit(t, t.get_rect(midtop=(caja.get_width() // 2, 14)))
                        caja.blit(s, s.get_rect(midtop=(caja.get_width() // 2, 70)))
                        caja.set_alpha(alfa)
                        ventana.blit(caja, caja.get_rect(midtop=(W // 2, 150)))
                    else:
                        t = f_hud_b.render(c['texto'], True, 'white')
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
                    icono = None if v['vendido'] else menus.icono_objeto(v['item'], 32)   # el icono del BW si esta, si no el cuadradito de color
                    if icono: ventana.blit(icono, icono.get_rect(center=caja.center))
                    else:
                        pygame.draw.rect(ventana, (60, 60, 60) if v['vendido'] else item['color'], caja, border_radius=6)
                        pygame.draw.rect(ventana, (20, 20, 20), caja, 2, border_radius=6)
                    nombre = f_tipo.render('VENDIDO' if v['vendido'] else item['nombre'], True, 'white')
                    ventana.blit(nombre, nombre.get_rect(midtop=(x, y + 14)))
                    if not v['vendido']:
                        precio = f_tipo.render(str(item['precio']) + ' $', True, (250, 215, 60) if j['monedas'] >= item['precio'] else (220, 90, 90))
                        ventana.blit(precio, precio.get_rect(midtop=(x, y + 28)))
                v = vitrina_cercana(nivel, j)
                if v:
                    item = tienda.ITEMS[v['item']]
                    panel = pygame.Rect(0, 0, 560, 58); panel.midbottom = (W // 2, H - 14)
                    pygame.draw.rect(ventana, (25, 25, 25), panel, border_radius=8)
                    pygame.draw.rect(ventana, item['color'], panel, 2, border_radius=8)
                    ventana.blit(f_hud_b.render('E: comprar ' + item['nombre'] + ' (' + str(item['precio']) + ' $)', True, 'white'), (panel.x + 14, panel.y + 8))
                    ventana.blit(f_hud.render(item['desc'], True, (210, 210, 210)), (panel.x + 14, panel.y + 34))

            def dibujar_objetos(nivel, j, rec):
                cx, cy = camara(j)
                ahora = tiempo()
                ventana.fill('black')
                entorno.dibujar(nivel['ent'], ventana, cx, cy, ahora, j['tipos'])   # piso de la era, terrenos, maquinas y objetos
                for puerta in nivel['puertas']:                           # puertas con el cartel de lo que hay detras
                    r = puerta['rect'].move(-cx, -cy)
                    pygame.draw.rect(ventana, (60, 180, 80) if j['llave'] else (120, 70, 30), r)
                    if 'destino' in puerta:
                        t = f_hud_b.render(mundos.etiqueta_destino(puerta['destino']), True, 'white')
                        df, dc = generacion.PASO_LADO[puerta['lado']]           # el cartel va un poco hacia adentro de la sala
                        centro_t = (r.centerx + dc * (r.width // 2 + 20 + t.get_width() // 2), r.centery + df * (r.height // 2 + 22))
                        fondo_t = t.get_rect(center=centro_t).inflate(12, 6)
                        pygame.draw.rect(ventana, (20, 20, 20), fondo_t, border_radius=5)
                        ventana.blit(t, t.get_rect(center=fondo_t.center))
                for piedra_verde in nivel['verdes']: dibujar_rect(piedra_verde['rect'],cx,cy,(0,220,80),'ellipse')
                for a in nivel['apariciones']:                            # donde va a salir la proxima oleada
                    k = 1 - (a['hasta'] - ahora) / 900
                    pygame.draw.circle(ventana, (230, 60, 60), (round(a['pos'][0] - cx), round(a['pos'][1] - cy)), round(10 + 20 * k), 3)
                for proyectil in nivel['proyectiles_enemigos']:
                    color = COLORES_TIPO.get(normalizar_tipo(proyectil.get('tipo')), (255, 150, 0))
                    pygame.draw.circle(ventana, color, (round(proyectil['x']-cx),round(proyectil['y']-cy)), 9 if proyectil['jefe'] else 8)
                    pygame.draw.circle(ventana, (40, 0, 0), (round(proyectil['x']-cx),round(proyectil['y']-cy)), 9 if proyectil['jefe'] else 8, 2)
                for ef in nivel['efectos']:
                    color_ef = COLORES_TIPO.get(normalizar_tipo(ef['tipo']), (255,255,255))
                    if 'linea' in ef: pygame.draw.line(ventana, color_ef, (round(ef['x']-cx), round(ef['y']-cy)), (round(ef['linea'][0]-cx), round(ef['linea'][1]-cy)), ef['radio'])
                    else: pygame.draw.circle(ventana, color_ef, (round(ef['x']-cx), round(ef['y']-cy)), ef['radio'], 4)
                for proyectil in nivel['proyectiles_pokemon']:
                    try: radio = max(2, int(float(proyectil['datos'].get('area', 8))))
                    except (TypeError, ValueError): radio = 8
                    pygame.draw.circle(ventana, COLORES_TIPO.get(normalizar_tipo(proyectil['datos'].get('tipo')), (80,180,255)), (round(proyectil['x']-cx),round(proyectil['y']-cy)), radio)
                for moneda in nivel['monedas']:
                    pygame.draw.circle(ventana, (250, 210, 50), (round(moneda['x'] - cx), round(moneda['y'] - cy)), 8)
                    pygame.draw.circle(ventana, (150, 110, 20), (round(moneda['x'] - cx), round(moneda['y'] - cy)), 8, 2)
                for baya in nivel['bayas']:                              # Baya Oran: bolita azul con una hojita
                    bx, by = round(baya['x'] - cx), round(baya['y'] - cy + math.sin(tiempo() / 250) * 2)
                    pygame.draw.circle(ventana, (60, 110, 220), (bx, by), 9); pygame.draw.circle(ventana, (20, 40, 90), (bx, by), 9, 2)
                    pygame.draw.circle(ventana, (170, 210, 255), (bx - 3, by - 3), 3)
                    pygame.draw.ellipse(ventana, (70, 170, 60), (bx - 2, by - 15, 10, 6))
                dibujar_jugador(j,cx,cy)
                if j['oculto']: pygame.draw.circle(ventana, (200, 200, 255), (j['rect'].centerx - cx, j['rect'].top - cy - 8), 5, 2)   # escondido
                if j['uso'] == 'mouse': mx, my = pantalla.raton()
                else: mx, my = round(j['rect'].centerx - cx + j['aim'][0] * 90), round(j['rect'].centery - cy + j['aim'][1] * 90)
                pygame.draw.circle(ventana, (230, 20, 20), (mx, my), 11, 2)
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    pygame.draw.line(ventana, (230, 20, 20), (mx + ox * 6, my + oy * 6), (mx + ox * 16, my + oy * 16), 2)
                for e in nivel['enemigos']:
                    if not dibujar_enemigo(e, cx, cy): dibujar_rect(e['rect'],cx,cy,e['color'])
                    barra((e['rect'].x-cx,e['rect'].y-cy-9,e['rect'].width,5),e['vida'],e['max_vida'])
                    ventana.blit(f_tipo.render(e['nombre'].replace('_', ' ') + ' Nv' + str(e['nivel']) + ' (' + e['tipo'] + ')',True,'black'),(e['rect'].x-cx,e['rect'].bottom-cy+2))
                if nivel['amigo']:                                         # el que quiere unirse: sentado con un corazon
                    e = nivel['amigo']
                    dibujar_enemigo(e, cx, cy)
                    pygame.draw.circle(ventana, (255, 110, 160), (e['rect'].centerx - cx, e['rect'].top - cy - 14), 9)
                    if math.hypot(e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery) < 90:
                        t = f_hud_b.render(tecla_de('interactuar') + ': hablar', True, 'white')
                        ventana.blit(t, t.get_rect(midbottom=(e['rect'].centerx - cx, e['rect'].top - cy - 26)))
                if nivel['jefe']:
                    b = nivel['jefe']
                    if not dibujar_enemigo(b, cx, cy): dibujar_rect(b['rect'],cx,cy,b.get('color',(255,140,0)))
                    barra((b['rect'].x-cx,b['rect'].y-cy-12,b['rect'].width,8),b['vida'],b['max_vida'],8)
                ia.dibujar_avisos(ventana, nivel['enemigos'] + ([nivel['jefe']] if nivel['jefe'] else []), cx, cy, ahora, f_hud_b)
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
                    m = j['equipo'][j['activo']]
                    antes = j['max_vida']; m['max_vida'] = progreso.vida_max(m)
                    j['vida'] = min(m['max_vida'], j['vida'] + max(0, m['max_vida'] - antes)); j['max_vida'] = m['max_vida']; j['mults'] = progreso.multiplicadores(m)
                    for o in j['equipo']:
                        if o is not m: o['max_vida'] = progreso.vida_max(o); o['vida'] = min(o['vida'], o['max_vida'])

                def evolucionar(i, req):
                    guardar_activo(j)
                    m = j['equipo'][i]
                    if 'objeto' in req: j['inventario']['objetos'][req['objeto']] = max(0, j['inventario']['objetos'].get(req['objeto'], 0) - 1)
                    proporcion = m['vida'] / max(1, m['max_vida'])
                    progreso.evolucionar(m, req['a'])
                    m['asist'] = asistencia_de(m['nombre']); m['max_vida'] = progreso.vida_max(m); m['vida'] = round(m['max_vida'] * proporcion)
                    if i == j['activo']: aplicar_pokemon(j, m['nombre'], m['vida'])
                    actualizar_sinergia(j)

                def enseñar(i, casilla, mt):
                    m = j['equipo'][i]
                    m['movs'][casilla] = mt
                    if not (trucos.get('mt_infinitas') or trucos.get('todas_mt')):        # la MT se gasta
                        j['inventario']['objetos'][mt] = max(0, j['inventario']['objetos'].get(mt, 0) - 1)
                    if i == j['activo']: j['juego'] = juego_de(m)

                def traer(ri, k):
                    guardar_activo(j)
                    nuevo = j['reserva'].pop(ri)
                    if k is None: j['equipo'].append(nuevo)
                    else:
                        j['reserva'].append(j['equipo'][k]); j['equipo'][k] = nuevo
                        if k == j['activo']: aplicar_pokemon(j, nuevo['nombre'], nuevo['vida'])
                    actualizar_sinergia(j)

                def movs(m):
                    g = juego_de(m)
                    return [nombre_mov(n) for n in (g['basicos'][0], g['basicos'][1], g['especiales'][0][0], g['especiales'][1][0])]

                return {'movs': movs, 'evolucionar': evolucionar, 'enseñar': enseñar, 'activar': lambda i: cambiar_slot(j, i, True),
                        'refrescar': refrescar, 'reserva': lambda: j['reserva'], 'traer': traer}

            def aplicar_trucos(nivel, j):
                """Los trucos que hacen algo una sola vez (subir niveles)."""
                veces = trucos.pop('subir_niveles', 0)
                for _ in range(veces):
                    for m in j['equipo']: progreso.dar_xp(m, progreso.xp_para(m['nombre'], m['nivel'] + 5) - m['xp'])
                if veces:
                    acciones_equipo(j)['refrescar'](); j['nivel'] = j['equipo'][j['activo']]['nivel']
                    cartel(nivel, 'Truco: +' + str(5 * veces) + ' niveles')

            return pantalla_final, acciones_equipo, aplicar_trucos

        pantalla_final, acciones_equipo, aplicar_trucos = armar_extras()

        j = crear_jugador(nombres, ESC.center, config['modo'])
        rec = mundos.nuevo_recorrido()                               # plan de la partida: eras, salas, tiendas, jefes y clima
        destino, entrada = None, 'sur'
        reloj = pygame.time.Clock()
        PASO, MAX_ATRASO = 1000 / 60, 250                            # un paso de logica (ms) y lo maximo que se recupera por frame
        acumulado = PASO
        while True:
            nivel = crear_nivel(rec, destino, entrada, j)
            reiniciar_jugador(j, nivel['sala']['inicio'])
            df, dc = generacion.PASO_LADO[nivel['sala']['entrada'] or 'sur']   # arranca en la puerta y camina para adentro
            j['rect'].center = (nivel['sala']['inicio'][0] - dc * 70, nivel['sala']['inicio'][1] - df * 70)
            cx, cy = camara(j)
            efectos.transicion(mundo['ef'], 'entrar', tiempo(), (j['rect'].centerx - cx, j['rect'].centery - cy))
            if nivel['tipo'] == 'tienda': j['llave'] = True          # la tienda no tiene enemigos: las puertas ya estan abiertas
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
                    if 'interactuar' in acciones and (comprar_cercano(nivel, j) or hablar_amigo(nivel, j)):
                        acciones = [a for a in acciones if a != 'basico1']   # si estabas comprando o hablando, no ataca
                    if 'basico1' in acciones: usar_basico(j, 0, nivel)
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
                                mundos.ir_a(rec, *eleccion)
                                destino, entrada, reiniciar_nivel = None, 'sur', True
                                break
                if reiniciar_nivel:
                    break
                botones = pygame.mouse.get_pressed()
                if config['modo'] != 'teclas' and botones[0]: usar_basico(j, 0, nivel)
                if config['modo'] != 'teclas' and botones[2]: usar_basico(j, 1, nivel)
                if controles.hay_control():                          # con control se puede dejar apretado el ataque
                    if controles._boton(controles.perfil('control').get('basico1', '')): usar_basico(j, 0, nivel)
                    if controles._boton(controles.perfil('control').get('basico2', '')): usar_basico(j, 1, nivel)
                acumulado += min(reloj.tick(60), MAX_ATRASO)            # ms reales desde el frame anterior (tope: despues de un menu no corre de golpe)
                resultado = None
                while acumulado >= PASO and not resultado:              # la logica avanza siempre 60 veces por segundo real:
                    acumulado -= PASO                                   # si la pc dibuja a 30 fps, hace 2 pasos por dibujo
                    resultado = actualizar_nivel(nivel, j)
                dibujar_objetos(nivel, j, rec)
                if resultado == 'siguiente':
                    puerta = nivel['salida']
                    if puerta['destino']['tipo'] == 'fin' or not mundos.avanzar(rec):
                        pausado(pantalla_final); return 'menu', j['nombre']
                    destino, entrada = puerta['destino'], generacion.OPUESTO[puerta['lado']]   # salis por el norte: entras por el sur
                    break
                if resultado == 'muerte': return 'juego_terminado', j['nombre']

    equipo_menu = []                                     # vacio: se elige el inicial. El debug (F1 + Konami) puede armar uno
    ui = {'ventana': ventana, 'W': W, 'H': H, 'presentar': pantalla.presentar, 'raton': pantalla.raton, 'a_logico': pantalla.a_logico,
          'retrato': retrato_menu, 'config': config, 'aplicar_pantalla': lambda: pantalla.aplicar(config), 'aplicar_volumen': aplicar_volumen}
    estado = 'titulo'

    while True:
        if estado == 'titulo':
            if pantalla_titulo() == 'salir': pygame.quit(); sys.exit()
            estado = 'menu'
            continue
        accion = menu_principal(equipo_menu)
        if accion == 'cerrar': opciones.guardar(config); pygame.quit(); sys.exit()
        if accion == 'titulo': estado = 'titulo'
        if accion == 'jugar':
            inicial = [n for n in equipo_menu if n] or menus.elegir_inicial(ui)   # Electrike, Sandshrew o Mareanie
            if inicial == 'salir': pygame.quit(); sys.exit()
            if inicial:
                resultado, _ = jugar(inicial if isinstance(inicial, list) else [inicial], config)
                pygame.mouse.set_visible(True)
                if resultado == 'salir': opciones.guardar(config); pygame.quit(); sys.exit()
        if accion == 'pokedex':
            if pokedex() == 'salir': pygame.quit(); sys.exit()
        if accion == 'ajustes' and menus.ajustes(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'glosario' and menus.glosario(ui) == 'salir': pygame.quit(); sys.exit()
        if accion == 'salir' and confirmar('¿Seguro que quieres salir?'): opciones.guardar(config); pygame.quit(); sys.exit()

if __name__ == '__main__':
    main()