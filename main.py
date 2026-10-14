import pygame
import random
import math
import sys
from pokemones import pokemones, movimientos, JUGABLES, ROL_POKEMON, datos_juego, asistencia_de, buscar_movimiento, multiplicador_tipos, normalizar_tipo, sinergia_de, evoluciones_de, descripcion_de, stats_oficiales, aprende_de, debilidades_de
from animaciones import direcciones, direccion_vector, AnimadorPokemon, cargar_retrato, tiene_sprites


COLORES_TIPO = {'lucha': (220, 70, 70), 'hielo': (130, 220, 255), 'volador': (235, 235, 235), 'tierra': (170, 115, 65), 'electrico': (245, 220, 40), 'agua': (70, 130, 235),
               'fuego': (240, 128, 48), 'planta': (120, 200, 80), 'veneno': (160, 64, 160), 'psiquico': (249, 85, 135), 'bicho': (166, 185, 26), 'roca': (182, 161, 54),
               'fantasma': (115, 87, 151), 'dragon': (111, 53, 252), 'siniestro': (112, 87, 70), 'acero': (183, 183, 206), 'normal': (168, 167, 122), 'hada': (214, 133, 173)}

def ajustar_texto(texto, fuente, ancho):
    lineas, actual = [], ''
    for palabra in str(texto).split():
        prueba = (actual + ' ' + palabra).strip()
        if not actual or fuente.size(prueba)[0] <= ancho: actual = prueba
        else: lineas.append(actual); actual = palabra
    if actual: lineas.append(actual)
    return lineas


def dibujar_esquinas(pantalla, rect, color=(255, 255, 255), margen=10, largo=14, grosor=3):
    r = rect.inflate(margen * 2, margen * 2)
    x1, y1, x2, y2 = r.left, r.top, r.right - 1, r.bottom - 1
    pygame.draw.line(pantalla, color, (x1, y1), (x1 + largo, y1), grosor)
    pygame.draw.line(pantalla, color, (x1, y1), (x1, y1 + largo), grosor)
    pygame.draw.line(pantalla, color, (x2, y1), (x2 - largo, y1), grosor)
    pygame.draw.line(pantalla, color, (x2, y1), (x2, y1 + largo), grosor)
    pygame.draw.line(pantalla, color, (x1, y2), (x1 + largo, y2), grosor)
    pygame.draw.line(pantalla, color, (x1, y2), (x1, y2 - largo), grosor)
    pygame.draw.line(pantalla, color, (x2, y2), (x2 - largo, y2), grosor)
    pygame.draw.line(pantalla, color, (x2, y2), (x2, y2 - largo), grosor)


def main():
    pygame.init()
    W, H = 1000, 600
    ventana = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Pokemanic')
    fuente = pygame.font.Font(None, 24)

    retratos_menu = {}

    def retrato_menu(nombre, lado):
        clave = (nombre, lado)
        if clave not in retratos_menu:
            img = cargar_retrato(nombre)
            retratos_menu[clave] = pygame.transform.smoothscale(img, (lado, lado)) if img else None
        return retratos_menu[clave]

    def elegir_espacio(nombre, equipo, activo):
        f_titulo, f_texto = pygame.font.Font(None, 36), pygame.font.Font(None, 26)
        cajas = [pygame.Rect(W // 2 - 345 + i * 235, 210, 220, 170) for i in range(3)]
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return None
                    if e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        return e.key - pygame.K_1
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in enumerate(cajas):
                        if r.collidepoint(e.pos):
                            return i
            ventana.fill((20, 20, 20))
            titulo = f_titulo.render('En que espacio queres a ' + nombre.replace('_', ' ').title() + '?', True, 'white')
            ventana.blit(titulo, titulo.get_rect(center=(W // 2, 140)))
            ayuda = f_texto.render('Clic o teclas 1 / 2 / 3 - ESC para cancelar', True, (200, 200, 200))
            ventana.blit(ayuda, ayuda.get_rect(center=(W // 2, 175)))
            raton = pygame.mouse.get_pos()
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
            pygame.display.flip()

    def debug_menu(equipo, activo):
        pygame.mouse.set_visible(True)
        scroll = 0
        botones = []
        f_titulo = pygame.font.Font(None, 32)
        while True:
            columnas, bw, bh, bn, sy = 4, 210, 62, 28, 18
            filas = math.ceil(len(JUGABLES) / columnas)
            max_scroll = max(0, 80 + filas * (bh + bn + sy) - H)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'salir', None, None
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_F1):
                    return 'ok', None, None
                if e.type == pygame.MOUSEWHEEL:
                    scroll = max(0, min(scroll - e.y * 60, max_scroll))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for r, nombre in botones:
                        if r.collidepoint(e.pos):
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
            for i, nombre in enumerate(JUGABLES):
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
                detalle = ROL_POKEMON.get(nombre, '')
                if en_equipo: detalle += ' - espacio ' + str(equipo.index(nombre) + 1)
                ventana.blit(fuente.render(detalle, True, 'white'), (x + 8, y + bh + 5))
                botones.append((r, nombre))
            pygame.display.flip()

    def aplicar_volumen():
        try: pygame.mixer.music.set_volume(config['volumen'] / 100)
        except pygame.error: pass

    def confirmar(mensaje):
        pygame.mouse.set_visible(True)
        fondo = ventana.copy()
        reloj_c = pygame.time.Clock()
        f = pygame.font.Font(None, 32)
        while True:
            for e in pygame.event.get():
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
            pygame.display.flip(); reloj_c.tick(60)

    def pantalla_titulo():
        pygame.mouse.set_visible(True)
        f_grande, f_med, f_peq = pygame.font.Font(None, 96), pygame.font.Font(None, 30), pygame.font.Font(None, 18)
        reloj_t = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if confirmar('¿Seguro que quieres salir?'): return 'salir'
                    else:
                        return 'menu'
                if e.type == pygame.MOUSEBUTTONDOWN:
                    return 'menu'
            ventana.fill('black')
            t = f_grande.render('POKEMANIC', True, 'white')
            ventana.blit(t, t.get_rect(center=(W // 2, 130)))
            p = f_med.render('presione cualquier tecla para empezar', True, 'white')
            ventana.blit(p, p.get_rect(center=(W // 2, H - 85)))
            s = f_peq.render('(menos esc, es para salir)', True, 'white')
            ventana.blit(s, s.get_rect(center=(W // 2, H - 58)))
            pygame.display.flip(); reloj_t.tick(60)

    def asignar_equipo(lista, nombre, espacio):
        if nombre in lista:
            i = lista.index(nombre)
            lista[i], lista[espacio] = lista[espacio], lista[i]
        else:
            lista[espacio] = nombre

    def menu_principal(equipo):
        pygame.mouse.set_visible(True)
        orden = ['jugar', 'pokedex', 'ajustes', 'salir']
        botones = {'jugar': pygame.Rect(100, 190, 300, 60), 'pokedex': pygame.Rect(100, 290, 300, 60), 'ajustes': pygame.Rect(100, 390, 300, 60), 'salir': pygame.Rect(0, 0, 84, 84)}
        botones['salir'].center = (W - 100, H - 80)
        f_titulo, f_boton, f_info = pygame.font.Font(None, 64), pygame.font.Font(None, 44), pygame.font.Font(None, 24)
        seleccion = 0
        reloj_m = pygame.time.Clock()
        while True:
            elegido = None
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'cerrar'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return 'titulo'
                    if e.key == pygame.K_F1:
                        resultado_debug, nombre, espacio = debug_menu(equipo, 0)
                        if resultado_debug == 'salir': return 'cerrar'
                        if nombre: asignar_equipo(equipo, nombre, espacio)
                    if e.key in (pygame.K_w, pygame.K_UP): seleccion = (seleccion - 1) % len(orden)
                    if e.key in (pygame.K_s, pygame.K_DOWN): seleccion = (seleccion + 1) % len(orden)
                    if e.key in (pygame.K_RETURN, pygame.K_e): elegido = orden[seleccion]
                if e.type == pygame.MOUSEMOTION:
                    for i, o in enumerate(orden):
                        if botones[o].collidepoint(e.pos): seleccion = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for o in orden:
                        if botones[o].collidepoint(e.pos): elegido = o
            if elegido: return elegido
            ventana.fill((128, 128, 128))
            t = f_titulo.render('POKEMANIC', True, 'white')
            ventana.blit(t, t.get_rect(topright=(W - 60, 50)))
            for o in orden[:3]:
                pygame.draw.rect(ventana, 'white', botones[o], 3)
                txt = f_boton.render(o, True, 'white')
                ventana.blit(txt, txt.get_rect(center=botones[o].center))
            cx, cy = botones['salir'].center
            pygame.draw.circle(ventana, 'white', (cx, cy), 40, 3)
            pygame.draw.line(ventana, 'white', (cx + 16, cy), (cx - 12, cy), 4)
            pygame.draw.line(ventana, 'white', (cx - 12, cy), (cx - 2, cy - 10), 4)
            pygame.draw.line(ventana, 'white', (cx - 12, cy), (cx - 2, cy + 10), 4)
            pygame.draw.line(ventana, 'white', (cx - 21, cy - 14), (cx - 21, cy + 14), 4)
            dibujar_esquinas(ventana, botones[orden[seleccion]].inflate(10, 10) if seleccion < 3 else botones['salir'].inflate(6, 6))
            ventana.blit(f_info.render('F1: elegir equipo - Equipo: ' + ' / '.join(equipo) + ' - Combate: ' + config['modo'], True, 'white'), (20, H - 34))
            pygame.display.flip(); reloj_m.tick(60)

    def menu_pausa(fondo):
        pygame.mouse.set_visible(True)
        tinte = pygame.Surface((W, H), pygame.SRCALPHA)
        tinte.fill((110, 110, 110, 165))
        opciones = [('seguir', 'seguir jugando'), ('ajustes', 'ajustes'), ('pokedex', 'pokedex'), ('salir', 'salir')]
        botones = [pygame.Rect(150, 170 + i * 80, 320, 56) for i in range(len(opciones))]
        f_titulo, f_boton = pygame.font.Font(None, 80), pygame.font.Font(None, 38)
        seleccion = 0
        reloj_p = pygame.time.Clock()
        while True:
            accion = None
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'cerrar'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return 'seguir'
                    if e.key in (pygame.K_w, pygame.K_UP): seleccion = (seleccion - 1) % len(opciones)
                    if e.key in (pygame.K_s, pygame.K_DOWN): seleccion = (seleccion + 1) % len(opciones)
                    if e.key in (pygame.K_RETURN, pygame.K_e): accion = opciones[seleccion][0]
                if e.type == pygame.MOUSEMOTION:
                    for i, r in enumerate(botones):
                        if r.collidepoint(e.pos): seleccion = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in enumerate(botones):
                        if r.collidepoint(e.pos): accion = opciones[i][0]
            if accion == 'seguir': return 'seguir'
            if accion == 'ajustes':
                r = ajustes(config['volumen'], config['modo'])
                if r is None: return 'cerrar'
                config['volumen'], config['modo'] = r
                aplicar_volumen()
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
            pygame.display.flip(); reloj_p.tick(60)

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
            partes.append('cura ' + str(int(num('porcentaje'))) + '% de la vida')
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
        if mec == 'curar': return 'cura el ' + str(a['porcentaje']) + '% de la vida del activo'
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
            for e in pygame.event.get():
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
            pygame.display.flip(); reloj_f.tick(60)

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
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 'salir'
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    return None
                if e.type == pygame.MOUSEWHEEL:
                    scroll = max(0, min(scroll - e.y * 60, max_scroll))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for r, i in botones:
                        if r.collidepoint(e.pos):
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
            pygame.display.flip()

    def jugar(nombres, config):
        pausa = {'total': 0}

        def tiempo(): return pygame.time.get_ticks() - pausa['total']

        def pausado(f, *args):
            t0 = pygame.time.get_ticks()
            r = f(*args)
            pausa['total'] += pygame.time.get_ticks() - t0
            return r

        ESC = pygame.Rect(0, 0, 1800, 1200)
        PARED = 40
        AREA = ESC.inflate(-80, -80)
        VEL_ENEMIGO = 1
        VEL_P_ENEMIGO = 8
        DIST_P_ENEMIGO = 250
        DETECCION = 350
        DISPARO = 500
        DAÑO_ENEMIGO = 10
        TIPOS_COMBATE = ('lucha', 'hielo', 'volador', 'tierra', 'electrico', 'agua')
        ENERGIA_MAX, GASTO_SPRINT, REGEN_ENERGIA, ENERGIA_MIN, MULT_SPRINT, COOLDOWN_CAMBIO = 100.0, 0.6, 0.35, 25.0, 1.7, 2500
        DIRS = {(1,-1):'noreste',(1,1):'sureste',(-1,-1):'noroeste',(-1,1):'suroeste',(1,0):'este',(-1,0):'oeste',(0,-1):'norte',(0,1):'sur'}
        EQUIPO_BASE = ('blastoise', 'lucario', 'pikachu', 'talonflame', 'garchomp')
        CD_ENEMIGO, CD_JEFE, CD_PIEDRA = 1500, 5000, 2000
        DURACION_PIEDRA = 5000
        CANT_ENEMIGOS, CANT_PIEDRAS = 10, 30
        TAM_JEFE, BALAS_JEFE, PIEDRAS_POR_USO = 160, 24, 4
        DAÑO_JEFE, DAÑO_PIEDRA = 35, 15

        def mover(rect, dx, dy, piedras):
            r = rect.copy(); r.x += dx
            if not any(r.colliderect(piedra) for piedra in piedras): rect.x += dx
            r = rect.copy(); r.y += dy
            if not any(r.colliderect(piedra) for piedra in piedras): rect.y += dy

        def crear_piedras():
            piedras = []
            centro = pygame.Rect(ESC.centerx - 250, ESC.centery - 250, 500, 500)
            while len(piedras) < CANT_PIEDRAS:
                piedra = pygame.Rect(random.randint(PARED + 50, ESC.width - PARED - 100), random.randint(PARED + 50, ESC.height - PARED - 100), 50, 50)
                if piedra.colliderect(centro) or any(piedra.colliderect(x.inflate(15, 15)) for x in piedras):
                    continue
                piedras.append(piedra)
            return piedras

        def tipo_combate(datos):
            tipos = datos.get('tipo') or []
            return normalizar_tipo(tipos[0]) if tipos else None

        def daño_con_tipo(daño, ataque_tipo, defensa_tipo):
            m = multiplicador_tipos(ataque_tipo, defensa_tipo)
            if daño <= 0: return 0
            return max(1, round(daño * m))

        def crear_puertas():
            return [
                pygame.Rect(ESC.centerx - 30, 0, 60, PARED),
                pygame.Rect(ESC.centerx - 30, ESC.bottom - PARED, 60, PARED),
                pygame.Rect(0, ESC.centery - 30, PARED, 60),
                pygame.Rect(ESC.right - PARED, ESC.centery - 30, PARED, 60)
            ]

        def equipo_inicial(nombre):
            lista = [nombre]
            for n in EQUIPO_BASE:
                if n in JUGABLES and n not in lista and len(lista) < 3: lista.append(n)
            return lista

        def crear_miembro(nombre):
            vida = datos_juego(nombre)['max_vida']
            miembro = {'nombre': nombre, 'vida': vida, 'max_vida': vida, 'asist': asistencia_de(nombre), 'asist_listo': 0}
            reiniciar_asistencia(miembro)
            return miembro

        def reiniciar_asistencia(m):
            m['asist_listo'] = tiempo() + round(m['asist']['enfriamiento'] * 0.3)

        def actualizar_sinergia(j):
            total = {}
            for i, m in enumerate(j['equipo']):
                if i == j['activo'] or m['vida'] <= 0: continue
                for clave, valor in sinergia_de(m['nombre']).items(): total[clave] = total.get(clave, 0) + valor
            j['sinergia'] = total

        def aplicar_pokemon(j, nombre, vida=None, centro=None):
            g = datos_juego(nombre)
            rect = pygame.Rect(0, 0, g['ancho'], g['alto'])
            rect.center = centro or j['rect'].center
            j.update({'nombre': nombre, 'datos': pokemones[nombre], 'juego': g, 'tipos': g['tipos'], 'rol': g['rol'], 'max_vida': g['max_vida'],
                      'vida': g['max_vida'] if vida is None else min(vida, g['max_vida']), 'velocidad': g['velocidad'], 'tamaño': g['tamaño'],
                      'ancho': g['ancho'], 'alto': g['alto'], 'rect': rect, 'ultimo_golpe': -1000, 'ultimo_proyectil': -1000, 'esp_ultimo': [-100000, -100000],
                      'atacando': False, 'anim_ataque': None, 'embestida': None, 'animador': AnimadorPokemon(nombre, rect, g['tamaño'])})

        def crear_jugador(nombres, centro, modo):
            equipo = []
            for n in nombres:
                if n in JUGABLES and n not in equipo: equipo.append(n)
            for n in equipo_inicial(equipo[0] if equipo else 'pikachu'):
                if len(equipo) < 3 and n not in equipo: equipo.append(n)
            j = {'modo': modo, 'uso': 'teclas' if modo == 'teclas' else 'mouse', 't_mouse': 0, 'pos_mouse': pygame.mouse.get_pos(), 'ultimo_dir': (0, 1), 'direccion': 'sur', 'moviendose': False, 'corriendo': False, 'llave': False, 'energia': ENERGIA_MAX, 'agotado': False, 'buffs': {},
                 'resto': [0.0, 0.0], 'aim': (0.0, 1.0), 'dir_ataque': 0, 'ultimo_cambio': -10000, 'equipo': [crear_miembro(n) for n in equipo], 'activo': 0, 'sinergia': {}}
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
            if nombre not in JUGABLES or not 0 <= espacio < len(j['equipo']): return
            guardar_activo(j)
            equipo = j['equipo']; a = j['activo']
            otros = [i for i, mi in enumerate(equipo) if mi['nombre'] == nombre]
            if otros:
                i = otros[0]
                if i == espacio: return
                equipo[espacio], equipo[i] = equipo[i], equipo[espacio]
                nuevo = equipo[espacio]
                if i == a: j['activo'] = espacio; actualizar_sinergia(j); return
            else:
                nuevo = crear_miembro(nombre)
                equipo[espacio] = nuevo
            if espacio == a:
                j['buffs'] = {}
                aplicar_pokemon(j, nombre, nuevo['vida'])
            actualizar_sinergia(j)

        def reiniciar_jugador(j):
            for m in j['equipo']: m['vida'] = m['max_vida']; reiniciar_asistencia(m)
            j.update({'direccion': 'sur', 'moviendose': False, 'corriendo': False, 'llave': False, 'energia': ENERGIA_MAX, 'agotado': False, 'buffs': {}, 'resto': [0.0, 0.0]})
            aplicar_pokemon(j, j['nombre'], centro=ESC.center)
            actualizar_sinergia(j)

        def mult_buff(j, clave):
            b = j['buffs'].get(clave)
            return b[0] if b and tiempo() < b[1] else 1.0

        def velocidad_actual(j):
            return j['velocidad'] * mult_buff(j, 'velocidad') * (1 + j['sinergia'].get('velocidad', 0)) * (MULT_SPRINT if j['corriendo'] else 1.0)

        def mover_jugador(j, piedras):
            t = pygame.key.get_pressed()
            dx, dy = t[pygame.K_d] - t[pygame.K_a], t[pygame.K_s] - t[pygame.K_w]
            j['moviendose'] = bool(dx or dy)
            if j['agotado'] and j['energia'] >= ENERGIA_MIN: j['agotado'] = False
            gratis = mult_buff(j, 'sprint') > 1
            j['corriendo'] = j['moviendose'] and bool(t[pygame.K_LCTRL] or t[pygame.K_RCTRL]) and (gratis or not j['agotado'])
            if j['corriendo']:
                if not gratis: j['energia'] = max(0.0, j['energia'] - GASTO_SPRINT)
                if j['energia'] <= 0 and not gratis: j['agotado'] = True; j['corriendo'] = False
            else:
                j['energia'] = min(ENERGIA_MAX, j['energia'] + REGEN_ENERGIA)
            if not j['moviendose']: return
            j['ultimo_dir'] = (dx, dy)
            n = math.hypot(dx, dy); v = velocidad_actual(j)
            j['resto'][0] += dx / n * v; j['resto'][1] += dy / n * v
            px, py = int(j['resto'][0]), int(j['resto'][1])
            j['resto'][0] -= px; j['resto'][1] -= py
            mover(j['rect'], px, 0, piedras)
            mover(j['rect'], 0, py, piedras)
            j['rect'].clamp_ip(AREA)

        def camara(j):
            return max(0, min(j['rect'].centerx - W // 2, ESC.width - W)), max(0, min(j['rect'].centery - H // 2, ESC.height - H))

        def apuntar(j):
            if j['embestida']: return
            ahora = tiempo()
            if j['modo'] == 'teclas': j['uso'] = 'teclas'
            else:
                pos = pygame.mouse.get_pos(); botones = pygame.mouse.get_pressed()
                if math.hypot(pos[0] - j['pos_mouse'][0], pos[1] - j['pos_mouse'][1]) >= 3 or botones[0] or botones[2]:
                    j['uso'] = 'mouse'; j['t_mouse'] = ahora
                j['pos_mouse'] = pos
                if j['modo'] == 'mixto' and j['uso'] == 'mouse' and j['moviendose'] and ahora - j['t_mouse'] > 1500: j['uso'] = 'teclas'
            if j['uso'] == 'teclas':
                dx, dy = j['ultimo_dir']; n = math.hypot(dx, dy)
                j['aim'] = (dx / n, dy / n); j['direccion'] = DIRS[(dx, dy)]
                return
            cx, cy = camara(j)
            mx, my = pygame.mouse.get_pos()
            vx, vy = mx + cx - j['rect'].centerx, my + cy - j['rect'].centery
            n = math.hypot(vx, vy)
            if n < 4: return
            j['aim'] = (vx / n, vy / n)
            j['direccion'] = direccion_de(pygame.Vector2(vx, vy))

        def punto_apuntado(j, alcance):
            cx, cy = camara(j)
            mx, my = pygame.mouse.get_pos()
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

        def preparar(j, datos):
            datos = dict(datos)
            datos['tipo'] = datos.get('tipo') or datos.get('tipo_ataque') or tipo_combate(j['datos'])
            try: base = float(datos.get('daño', 0))
            except (TypeError, ValueError): base = 0
            datos['daño'] = round(base * j['juego']['mult_daño'] * mult_buff(j, 'daño') * (1 + j['sinergia'].get('daño', 0)))
            return datos

        def enfriamiento_de(j, datos):
            try: base = max(0, int(float(datos.get('enfriamiento', 300))))
            except (TypeError, ValueError): base = 300
            return round(base * j['juego']['mult_enfriamiento'] * (1 - j['sinergia'].get('enfriamiento', 0)) * mult_buff(j, 'enfriamiento'))

        def iniciar_ataque(j, forma, enfriamiento):
            a = j['animador']
            anim = a.buscar_para(forma)
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
            proyectiles.append({'x': float(x), 'y': float(y), 'vx': ax, 'vy': ay, 'direccion': j['direccion'], 'datos': datos, 'rect': pygame.Rect(0,0,tamaño,tamaño), 'distancia': 0, 'activo': True, 'golpeados': []})

        def area_efecto(j, datos, objetivos, efectos, centro=None):
            try: radio = max(10, int(float(datos.get('area', 100))))
            except (TypeError, ValueError): radio = 100
            c = pygame.Vector2(centro or j['rect'].center)
            for o in objetivos:
                if o['vida'] > 0 and c.distance_to(o['rect'].center) <= radio + max(o['rect'].width, o['rect'].height) / 2:
                    recibir_ataque(o, datos, direccion_de(pygame.Vector2(o['rect'].center) - c))
            ahora = tiempo()
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
            if e['restante'] <= 0: j['embestida'] = None

        def usar_basico(j, indice, nivel):
            nombre = j['juego']['basicos'][indice]
            base = buscar_movimiento(nombre) if nombre else None
            if not base: return
            datos = preparar(j, base)
            ahora = tiempo(); enfriamiento = enfriamiento_de(j, datos)
            clave = 'ultimo_golpe' if indice == 0 else 'ultimo_proyectil'
            if j['atacando'] or j['embestida'] or ahora - j[clave] < enfriamiento: return
            j[clave] = ahora
            iniciar_ataque(j, datos.get('forma', 'cuerpo'), enfriamiento)
            if datos.get('forma') == 'proyectil': lanzar(j, datos, nivel['proyectiles_pokemon'])
            else: golpear(j, datos, nivel['enemigos'][:] + ([nivel['jefe']] if nivel['jefe'] else []), nivel['efectos'])

        def usar_especial(j, indice, nivel):
            nombre, base = j['juego']['especiales'][indice]
            datos = preparar(j, base)
            forma = datos.get('forma', 'proyectil')
            ahora = tiempo(); enfriamiento = enfriamiento_de(j, datos)
            if j['atacando'] or j['embestida'] or ahora - j['esp_ultimo'][indice] < enfriamiento: return
            j['esp_ultimo'][indice] = ahora
            iniciar_ataque(j, forma, enfriamiento)
            objetivos = nivel['enemigos'][:] + ([nivel['jefe']] if nivel['jefe'] else [])
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

        def usar_asistencia(j, k, nivel):
            ahora = tiempo()
            reserva = [m for i, m in enumerate(j['equipo']) if i != j['activo']]
            if k >= len(reserva): return
            m = reserva[k]
            if m['vida'] <= 0 or ahora < m['asist_listo']: return
            a = m['asist']; mec = a['mecanica']
            objetivos = nivel['enemigos'][:] + ([nivel['jefe']] if nivel['jefe'] else [])
            m['asist_listo'] = ahora + a['enfriamiento']
            if mec == 'impacto':
                datos = {'tipo': a['tipo'], 'daño': round(a['daño'] * a['mult_daño']), 'area': a['area'], 'retroceso': 30, 'efecto': a['efecto']}
                area_efecto(j, datos, objetivos, nivel['efectos'], punto_apuntado(j, a['alcance']))
            elif mec in ('escudo', 'furia', 'carrera'):
                for clave, valor in a['buffs'].items(): j['buffs'][clave] = (valor, ahora + a['duracion'])
                nivel['efectos'].append({'x': j['rect'].centerx, 'y': j['rect'].centery, 'radio': 45, 'tipo': a['tipo'], 'inicio': ahora, 'hasta': ahora + 500})
            elif mec == 'curar':
                j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * a['porcentaje'] / 100)
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
            daño *= mult_buff(j, 'defensa') * (1 - j['sinergia'].get('defensa', 0))
            j['vida'] = max(0, j['vida'] - daño)

        def recibir_ataque(obj, datos, direccion=None):
            ataque_tipo = datos.get('tipo') or datos.get('tipo_ataque')
            defensa_tipo = obj.get('tipo')
            try: daño_base = float(datos.get('daño', 0))
            except (TypeError, ValueError): daño_base = 0
            daño = daño_con_tipo(daño_base, ataque_tipo, defensa_tipo)
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
            if retroceso and direccion in direccion_vector:
                vx, vy = direccion_vector[direccion]
                obj['rect'].x += vx * retroceso; obj['rect'].y += vy * retroceso; obj['rect'].clamp_ip(AREA)

        pool_tipo = {}

        def elegir_pokemon_enemigo(tipo):
            if tipo not in pool_tipo:
                pool = [n for n in JUGABLES if tipo in [normalizar_tipo(t) for t in pokemones[n].get('tipo', [])]]
                pool_tipo[tipo] = [n for n in pool if tiene_sprites(n)] or pool or list(JUGABLES)
            return random.choice(pool_tipo[tipo])

        def crear_enemigo(piedras):
            while True:
                tamaño, vida = 50, 100
                r = pygame.Rect(random.randint(PARED+10, ESC.width-PARED-tamaño-10), random.randint(PARED+10, ESC.height-PARED-tamaño-10), tamaño, tamaño)
                if pygame.Vector2(r.center).distance_to(ESC.center) <= 300 or any(r.colliderect(piedra) for piedra in piedras):
                    continue
                ahora = tiempo()
                tipo = random.choice(TIPOS_COMBATE)
                nombre = elegir_pokemon_enemigo(tipo)
                visual = max(34, min(70, datos_juego(nombre)['tamaño'] + 8))
                return {'tipo': tipo, 'nombre': nombre, 'animador': AnimadorPokemon(nombre, r, visual), 'direccion': 'sur', 'prev': r.center, 'rect': r, 'vida': vida, 'max_vida': vida, 'daño': DAÑO_ENEMIGO, 'color': COLORES_TIPO[tipo], 'ultimo_golpe': 0,
                        'quieto_hasta': 0, 'cambio': ahora, 'dx': random.choice([-1,0,1]), 'dy': random.choice([-1,0,1]), 'estado': None, 'estado_hasta': 0, 'proximo_estado': 0}

        def actualizar_animacion_enemigo(e):
            a = e['animador']
            c = e['rect'].center
            dx, dy = c[0] - e['prev'][0], c[1] - e['prev'][1]
            e['prev'] = c
            if dx or dy: e['direccion'] = direccion_de(pygame.Vector2(dx, dy))
            a.ritmo = 1.0
            a.cambiar('walk' if dx or dy else 'idle', direcciones.index(e['direccion']), True)
            a.actualizar()

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

        def crear_proyectil(x, y, dx, dy, daño, jefe=False, tipo=None):
            return {'x': float(x), 'y': float(y), 'dx': dx, 'dy': dy, 'daño': daño, 'jefe': jefe, 'tipo': tipo, 'distancia': 0, 'activo': True, 'rect': pygame.Rect(int(x)-8, int(y)-8, 16, 16)}

        def actualizar_proyectil(proyectil, j, piedras):
            proyectil['x'] += proyectil['dx'] * VEL_P_ENEMIGO; proyectil['y'] += proyectil['dy'] * VEL_P_ENEMIGO; proyectil['distancia'] += VEL_P_ENEMIGO
            proyectil['rect'].center = round(proyectil['x']), round(proyectil['y'])
            if proyectil['distancia'] >= DIST_P_ENEMIGO or not ESC.colliderect(proyectil['rect']) or any(proyectil['rect'].colliderect(x) for x in piedras):
                proyectil['activo'] = False; return
            if proyectil['rect'].colliderect(j['rect']): dañar_jugador(j, proyectil['daño'], proyectil.get('tipo')); proyectil['activo'] = False

        def actualizar_proyectil_pokemon(proyectil, objetivos, piedras):
            vx, vy = proyectil['vx'], proyectil['vy']
            try: paso = max(0.1, float(proyectil['datos'].get('velocidad', 8)))
            except (TypeError, ValueError): paso = 8.0
            proyectil['x'] += vx * paso; proyectil['y'] += vy * paso; proyectil['distancia'] += paso; proyectil['rect'].center = round(proyectil['x']), round(proyectil['y'])
            try: distancia_maxima = max(1.0, float(proyectil['datos'].get('distancia', 250)))
            except (TypeError, ValueError): distancia_maxima = 250.0
            if proyectil['distancia'] >= distancia_maxima or not ESC.colliderect(proyectil['rect']) or any(proyectil['rect'].colliderect(x) for x in piedras):
                proyectil['activo'] = False; return
            for o in objetivos:
                if o['vida'] <= 0 or o in proyectil['golpeados']: continue
                try: a = max(0, int(float(proyectil['datos'].get('area', 0))))
                except (TypeError, ValueError): a = 0
                zona = o['rect'].inflate(a * 2, a * 2)
                if zona.colliderect(proyectil['rect']):
                    recibir_ataque(o, proyectil['datos'], proyectil['direccion']); proyectil['golpeados'].append(o)
                    if not proyectil['datos'].get('atraviesa', False): proyectil['activo'] = False; return

        def actualizar_enemigo(e, j, piedras, proyectiles):
            ahora = tiempo()
            if ahora < e['quieto_hasta'] or e['estado'] in ('paralizar', 'dormir'):
                return
            distancia = pygame.Vector2(e['rect'].center).distance_to(j['rect'].center)
            if distancia <= DETECCION:
                ex = (j['rect'].centerx > e['rect'].centerx) - (j['rect'].centerx < e['rect'].centerx)
                ey = (j['rect'].centery > e['rect'].centery) - (j['rect'].centery < e['rect'].centery)
                vel = 0.45 if e['estado'] == 'ralentizar' else VEL_ENEMIGO
                mover(e['rect'], ex*vel, 0, piedras)
                mover(e['rect'], 0, ey*vel, piedras)
            else:
                if ahora >= e['cambio']:
                    e['dx'], e['dy'] = random.choice([-1,0,1]), random.choice([-1,0,1])
                    e['cambio'] = ahora + random.randint(500,1500)
                mover(e['rect'], e['dx']*VEL_ENEMIGO, 0, piedras)
                mover(e['rect'], 0, e['dy']*VEL_ENEMIGO, piedras)
            e['rect'].clamp_ip(AREA)
            if e['rect'].colliderect(j['rect']) and ahora-e['ultimo_golpe'] >= 500:
                dañar_jugador(j, e['daño'], e['tipo'])
                e['ultimo_golpe'] = ahora
                e['quieto_hasta'] = ahora+500
                v = pygame.Vector2(e['rect'].center) - pygame.Vector2(j['rect'].center)
                if v.length():
                    v.normalize_ip()
                    e['rect'].x += v.x * 50
                    e['rect'].y += v.y * 50
                    e['rect'].clamp_ip(AREA)

        def crear_jefe(piedras):
            while True:
                r = pygame.Rect(random.randint(PARED+100, ESC.width-PARED-TAM_JEFE-100), random.randint(PARED+100, ESC.height-PARED-TAM_JEFE-100), TAM_JEFE, TAM_JEFE)
                if pygame.Vector2(r.center).distance_to(ESC.center) <= 400 or any(r.colliderect(piedra.inflate(20,20)) for piedra in piedras): continue
                ahora = tiempo()
                tipo = random.choice(TIPOS_COMBATE)
                return {'rect': r, 'vida': 500, 'max_vida': 500, 'daño': DAÑO_JEFE, 'tipo': tipo, 'color': COLORES_TIPO[tipo], 'ultimo_golpe': 0, 'ultimo_disparo': ahora, 'ultimo_poder': ahora,
                        'cambio': ahora, 'dx': random.choice([-1,0,1]), 'dy': random.choice([-1,0,1])}

        def crear_piedras_verdes(jefe):
            nuevas = []
            for _ in range(PIEDRAS_POR_USO):
                for _ in range(20):
                    a, d = random.uniform(0, math.tau), random.randint(120,400)
                    r = pygame.Rect(int(jefe['rect'].centerx + math.cos(a)*d), int(jefe['rect'].centery + math.sin(a)*d), 45, 45)
                    if not AREA.contains(r) or r.colliderect(jefe['rect']) or any(r.colliderect(x['rect']) for x in nuevas): continue
                    nuevas.append({'rect': r, 'tiempo': tiempo(), 'daño': 0}); break
            return nuevas

        def actualizar_jefe(jefe, j, piedras, proyectiles, verdes):
            ahora = tiempo()
            d = pygame.Vector2(jefe['rect'].center).distance_to(j['rect'].center)
            if d <= DETECCION + 150:
                ex = (j['rect'].centerx > jefe['rect'].centerx) - (j['rect'].centerx < jefe['rect'].centerx)
                ey = (j['rect'].centery > jefe['rect'].centery) - (j['rect'].centery < jefe['rect'].centery)
                mover(jefe['rect'], ex, 0, piedras); mover(jefe['rect'], 0, ey, piedras)
            else:
                if ahora >= jefe['cambio']:
                    jefe['dx'], jefe['dy'] = random.choice([-1,0,1]), random.choice([-1,0,1]); jefe['cambio'] = ahora + random.randint(500,1500)
                mover(jefe['rect'], jefe['dx'], 0, piedras); mover(jefe['rect'], 0, jefe['dy'], piedras)
            jefe['rect'].clamp_ip(AREA)
            if ahora - jefe['ultimo_disparo'] >= CD_JEFE:
                for i in range(BALAS_JEFE):
                    a = i * math.tau / BALAS_JEFE; dx, dy = math.cos(a), math.sin(a); r = TAM_JEFE//2+10
                    proyectiles.append(crear_proyectil(jefe['rect'].centerx+dx*r, jefe['rect'].centery+dy*r, dx, dy, 25, True, jefe['tipo']))
                jefe['ultimo_disparo'] = ahora
            if ahora - jefe['ultimo_poder'] >= CD_PIEDRA:
                verdes.extend(crear_piedras_verdes(jefe)); jefe['ultimo_poder'] = ahora
            if jefe['rect'].colliderect(j['rect']) and ahora-jefe['ultimo_golpe'] >= 700:
                dañar_jugador(j, jefe['daño'], jefe['tipo']); jefe['ultimo_golpe'] = ahora

        def menu_niveles(nivel_actual):
            pygame.mouse.set_visible(True)
            total = 21
            columnas, bw, bh, bn, sy = 4, 210, 62, 28, 18
            filas = math.ceil(total / columnas)
            max_scroll = max(0, 80 + filas * (bh + bn + sy) - H)
            seleccionado = max(0, min(total - 1, nivel_actual))
            scroll = 0
            botones = []
            reloj_debug = pygame.time.Clock()
            f_titulo = pygame.font.Font(None, 32)
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        return 'salir'
                    if e.type == pygame.KEYDOWN:
                        if e.key in (pygame.K_ESCAPE, pygame.K_F2):
                            return None
                        if e.key == pygame.K_UP and seleccionado - columnas >= 0: seleccionado -= columnas
                        if e.key == pygame.K_DOWN and seleccionado + columnas < total: seleccionado += columnas
                        if e.key == pygame.K_LEFT: seleccionado = max(0, seleccionado - 1)
                        if e.key == pygame.K_RIGHT: seleccionado = min(total - 1, seleccionado + 1)
                        if e.key == pygame.K_RETURN:
                            return seleccionado
                        y_sel = 85 + seleccionado // columnas * (bh + bn + sy)
                        if y_sel - scroll < 65: scroll = max(0, y_sel - 85)
                        if y_sel + bh + bn - scroll > H: scroll = min(max_scroll, y_sel + bh + bn - H + 20)
                    if e.type == pygame.MOUSEWHEEL:
                        scroll = max(0, min(scroll - e.y * 60, max_scroll))
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        for r, i in botones:
                            if r.collidepoint(e.pos):
                                return i
                ventana.fill((20, 20, 20))
                botones = []
                ventana.blit(f_titulo.render('MENU DE NIVELES', True, 'white'), (25, 15))
                ventana.blit(fuente.render('F2 o ESC para cerrar - rueda del mouse para desplazarte - clic o ENTER para elegir', True, (200, 200, 200)), (25, 45))
                for i in range(total):
                    x = 30 + i % columnas * 240
                    y = 85 + i // columnas * (bh + bn + sy) - scroll
                    r = pygame.Rect(x, y, bw, bh)
                    nr = pygame.Rect(x, y + bh, bw, bn)
                    if r.bottom < 65 or nr.top > H:
                        continue
                    pygame.draw.rect(ventana, (80, 160, 80) if i == seleccionado else (200, 200, 200), r)
                    pygame.draw.rect(ventana, (50, 50, 50), nr)
                    ventana.blit(fuente.render('Nivel ' + str(i + 1), True, 'black'), (x + 8, y + 22))
                    ventana.blit(fuente.render('jefe' if i >= 2 and (i + 1) % 3 == 0 else 'normal', True, 'white'), (x + 8, y + bh + 5))
                    botones.append((r, i))
                pygame.display.flip(); reloj_debug.tick(60)

        def crear_nivel(numero):
            piedras = crear_piedras()
            jefe = crear_jefe(piedras) if numero >= 2 and (numero + 1) % 3 == 0 else None
            return {'piedras': piedras, 'enemigos': [] if jefe else [crear_enemigo(piedras) for _ in range(CANT_ENEMIGOS)], 'jefe': jefe,
                    'proyectiles_pokemon': [], 'proyectiles_enemigos': [], 'efectos': [], 'verdes': [], 'puertas': crear_puertas(), 'llave': None, 'completado': False}

        def actualizar_nivel(nivel, j):
            ahora = tiempo(); piedras = nivel['piedras']; enemigos = nivel['enemigos']; jefe = nivel['jefe']
            objetivos = enemigos[:] + ([jefe] if jefe else [])
            if j['embestida']: actualizar_embestida(j, objetivos, piedras); j['moviendose'] = True
            else: mover_jugador(j, piedras)
            actualizar_jugador(j)
            nivel['efectos'] = [x for x in nivel['efectos'] if ahora < x['hasta']]
            for proyectil in nivel['proyectiles_pokemon']: actualizar_proyectil_pokemon(proyectil, objetivos, piedras)
            nivel['proyectiles_pokemon'] = [proyectil for proyectil in nivel['proyectiles_pokemon'] if proyectil['activo']]
            for e in enemigos:
                actualizar_estado(e)
                if e['vida'] > 0: actualizar_enemigo(e, j, piedras, nivel['proyectiles_enemigos'])
                actualizar_animacion_enemigo(e)
            nivel['enemigos'] = [e for e in enemigos if e['vida'] > 0]
            if jefe:
                actualizar_jefe(jefe, j, piedras, nivel['proyectiles_enemigos'], nivel['verdes'])
                if jefe['vida'] <= 0: nivel['jefe'] = None
            for proyectil in nivel['proyectiles_enemigos']: actualizar_proyectil(proyectil, j, piedras)
            nivel['proyectiles_enemigos'] = [proyectil for proyectil in nivel['proyectiles_enemigos'] if proyectil['activo']]
            for piedra_verde in nivel['verdes'][:]:
                if ahora - piedra_verde['tiempo'] >= DURACION_PIEDRA: nivel['verdes'].remove(piedra_verde); continue
                if j['rect'].colliderect(piedra_verde['rect']) and ahora-piedra_verde['daño'] >= 500: dañar_jugador(j, DAÑO_PIEDRA); piedra_verde['daño'] = ahora
            derrotados = not nivel['enemigos'] and nivel['jefe'] is None
            nivel['completado'] = derrotados
            if derrotados and nivel['llave'] is None and not j['llave']:
                nivel['llave'] = pygame.Rect(ESC.centerx-15, ESC.centery-15, 30, 30)
            if nivel['llave'] and j['rect'].colliderect(nivel['llave']): j['llave'] = True; nivel['llave'] = None
            if j['vida'] <= 0:
                guardar_activo(j)
                vivos = [i for i, m in enumerate(j['equipo']) if m['vida'] > 0]
                if not vivos: return 'muerte'
                cambiar_slot(j, vivos[0], True)
            if j['llave'] and any(j['rect'].colliderect(puerta.inflate(20,20)) for puerta in nivel['puertas']):
                return 'siguiente'
            if not j['llave']:
                for puerta in nivel['puertas']:
                    if j['rect'].colliderect(puerta.inflate(8, 8)):
                        if j['rect'].centerx < puerta.left: j['rect'].right = puerta.left
                        elif j['rect'].centerx > puerta.right: j['rect'].left = puerta.right
                        elif j['rect'].centery < puerta.top: j['rect'].bottom = puerta.top
                        else: j['rect'].top = puerta.bottom

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

        def barra_hud(rect, vida, max_vida):
            pygame.draw.rect(ventana, 'white', rect)
            pygame.draw.rect(ventana, (130, 0, 20), (rect[0], rect[1], int(max(0, vida) * rect[2] // max(1, max_vida)), rect[3]))
            pygame.draw.rect(ventana, 'black', rect, 3)

        def dibujar_hud(j, nivel):
            ahora = tiempo()
            circulo_poke((44, 86), 34, j['nombre'])
            barra_hud((80, 68, 240, 36), j['vida'], j['max_vida'])
            t = f_hud.render(str(int(j['vida'])) + '/' + str(j['max_vida']), True, 'white')
            ventana.blit(t, t.get_rect(center=(200, 86)))
            pygame.draw.rect(ventana, (60, 60, 60), (80, 108, 240, 6))
            pygame.draw.rect(ventana, (120, 120, 160) if j['agotado'] else (0, 160, 230), (80, 108, int(240 * j['energia'] / ENERGIA_MAX), 6))
            ventana.blit(f_hud_b.render(j['nombre'].replace('_', ' '), True, 'black'), (84, 117))
            esperando = ahora - j['ultimo_cambio'] < COOLDOWN_CAMBIO
            k = 0
            for i, m in enumerate(j['equipo']):
                if i == j['activo']: continue
                cy = 14 + k * 30
                circulo_poke((86, cy), 11, m['nombre'], esperando or m['vida'] <= 0)
                ventana.blit(f_hud.render(str(i + 1), True, 'black'), (68, cy - 6))
                barra_hud((100, cy - 8, 100, 16), m['vida'], m['max_vida'])
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
            if nivel['jefe']:
                b = nivel['jefe']
                ventana.blit(f_hud.render('JEFE - ' + b['tipo'], True, 'white'), (W - 300, 4))
                barra_hud((W - 300, 22, 280, 20), b['vida'], b['max_vida'])

        def dibujar_objetos(nivel, j):
            cx, cy = camara(j)
            ventana.fill('black')
            dibujar_rect(ESC, cx, cy, 'white')
            paredes = [pygame.Rect(0,0,ESC.width,PARED), pygame.Rect(0,ESC.bottom-PARED,ESC.width,PARED), pygame.Rect(0,0,PARED,ESC.height), pygame.Rect(ESC.right-PARED,0,PARED,ESC.height)]
            for pared in paredes: dibujar_rect(pared,cx,cy,'black')
            for piedra in nivel['piedras']: dibujar_rect(piedra,cx,cy,(100,100,100),'ellipse')
            for piedra_verde in nivel['verdes']: dibujar_rect(piedra_verde['rect'],cx,cy,(0,220,80),'ellipse')
            for puerta in nivel['puertas']: dibujar_rect(puerta,cx,cy,(60,180,80) if j['llave'] else (120,70,30))
            for proyectil in nivel['proyectiles_enemigos']:
                pygame.draw.circle(ventana, (255,50,0) if proyectil['jefe'] else (255,150,0), (round(proyectil['x']-cx),round(proyectil['y']-cy)), 9 if proyectil['jefe'] else 8)
            for ef in nivel['efectos']:
                color_ef = COLORES_TIPO.get(normalizar_tipo(ef['tipo']), (255,255,255))
                if 'linea' in ef: pygame.draw.line(ventana, color_ef, (round(ef['x']-cx), round(ef['y']-cy)), (round(ef['linea'][0]-cx), round(ef['linea'][1]-cy)), ef['radio'])
                else: pygame.draw.circle(ventana, color_ef, (round(ef['x']-cx), round(ef['y']-cy)), ef['radio'], 4)
            for proyectil in nivel['proyectiles_pokemon']:
                try: radio = max(2, int(float(proyectil['datos'].get('area', 8))))
                except (TypeError, ValueError): radio = 8
                pygame.draw.circle(ventana, (80,180,255), (round(proyectil['x']-cx),round(proyectil['y']-cy)), radio)
            dibujar_jugador(j,cx,cy)
            if j['uso'] == 'mouse': mx, my = pygame.mouse.get_pos()
            else: mx, my = round(j['rect'].centerx - cx + j['aim'][0] * 90), round(j['rect'].centery - cy + j['aim'][1] * 90)
            pygame.draw.circle(ventana, (230, 20, 20), (mx, my), 11, 2)
            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                pygame.draw.line(ventana, (230, 20, 20), (mx + ox * 6, my + oy * 6), (mx + ox * 16, my + oy * 16), 2)
            for e in nivel['enemigos']:
                if not dibujar_enemigo(e, cx, cy): dibujar_rect(e['rect'],cx,cy,e['color'])
                barra((e['rect'].x-cx,e['rect'].y-cy-9,e['rect'].width,5),e['vida'],e['max_vida'])
                ventana.blit(f_tipo.render(e['nombre'].replace('_', ' ') + ' (' + e['tipo'] + ')',True,'black'),(e['rect'].x-cx,e['rect'].bottom-cy+2))
            if nivel['jefe']:
                b = nivel['jefe']; dibujar_rect(b['rect'],cx,cy,b.get('color',(255,140,0))); barra((b['rect'].x-cx,b['rect'].y-cy-12,b['rect'].width,8),b['vida'],b['max_vida'],8)
            if nivel['llave']: dibujar_rect(nivel['llave'],cx,cy,'yellow')
            if nivel['completado']:
                r = pygame.Rect(260, 210, 480, 170)
                pygame.draw.rect(ventana, (25,25,25), r)
                pygame.draw.rect(ventana, (80,220,100), r, 3)
                f = pygame.font.Font(None, 36)
                ventana.blit(f.render('¡NIVEL COMPLETADO!', True, 'white'), (350,245))
                texto_nivel = 'Ve a buscar la llave' if not j['llave'] else 'Ve a una puerta para continuar'
                ventana.blit(pygame.font.Font(None, 24).render(texto_nivel, True, (220,220,220)), (335,295))
            dibujar_hud(j, nivel)
            pygame.display.flip()

        j = crear_jugador(nombres, ESC.center, config['modo'])
        nivel_numero = 0
        reloj = pygame.time.Clock()
        while True:
            reiniciar_jugador(j); nivel = crear_nivel(nivel_numero)
            reiniciar_nivel = False
            while True:
                pygame.mouse.set_visible(False)
                apuntar(j)
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: return 'salir', j['nombre']
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            accion_pausa = pausado(menu_pausa, ventana.copy())
                            if accion_pausa == 'cerrar': return 'salir', j['nombre']
                            if accion_pausa == 'menu': return 'menu', j['nombre']
                            j['modo'] = config['modo']
                        if e.key == pygame.K_F1:
                            resultado_debug, elegido, espacio = pausado(debug_menu, [mi['nombre'] for mi in j['equipo']], j['activo'])
                            if resultado_debug == 'salir': return 'salir', j['nombre']
                            if elegido: equipar_debug(j, elegido, espacio)
                        if e.key == pygame.K_F2:
                            nuevo_nivel = pausado(menu_niveles, nivel_numero)
                            if nuevo_nivel == 'salir': return 'salir', j['nombre']
                            if nuevo_nivel is not None:
                                nivel_numero = nuevo_nivel
                                reiniciar_nivel = True
                                break
                        if e.key == pygame.K_e: usar_basico(j, 0, nivel)
                        if e.key == pygame.K_q: usar_basico(j, 1, nivel)
                        if e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT): usar_especial(j, 0, nivel)
                        if e.key == pygame.K_r: usar_especial(j, 1, nivel)
                        if e.key == pygame.K_f: usar_asistencia(j, 0, nivel)
                        if e.key == pygame.K_g: usar_asistencia(j, 1, nivel)
                        if e.key in (pygame.K_1, pygame.K_2, pygame.K_3): cambiar_slot(j, e.key - pygame.K_1)
                if reiniciar_nivel:
                    break
                botones = pygame.mouse.get_pressed()
                if config['modo'] != 'teclas' and botones[0]: usar_basico(j, 0, nivel)
                if config['modo'] != 'teclas' and botones[2]: usar_basico(j, 1, nivel)
                resultado = actualizar_nivel(nivel, j)
                dibujar_objetos(nivel, j)
                if resultado == 'siguiente': nivel_numero += 1; break
                if resultado == 'muerte': return 'juego_terminado', j['nombre']
                reloj.tick(60)

    def ajustes(volumen, modo):
        reloj_ajustes = pygame.time.Clock()
        f_titulo = pygame.font.Font(None, 48)
        f_texto = pygame.font.Font(None, 36)
        modos = ['mouse', 'teclas', 'mixto']
        descripcion = {'mouse': 'Apuntas con el mouse: clic izq. cuerpo a cuerpo, clic der. a distancia',
                       'teclas': 'Atacas con E / Q / Shift / R hacia donde caminaste por ultima vez',
                       'mixto': 'Teclas hasta que mueves el mouse; vuelve a teclas si caminas sin tocarlo'}
        fila_sel = 0
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return None
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        return volumen, modo
                    if e.key in (pygame.K_w, pygame.K_UP):
                        fila_sel = 0
                    if e.key in (pygame.K_s, pygame.K_DOWN):
                        fila_sel = 1
                    if e.key in (pygame.K_a, pygame.K_LEFT):
                        if fila_sel == 0: volumen = max(10, volumen - 10)
                        else: modo = modos[(modos.index(modo) - 1) % len(modos)]
                    if e.key in (pygame.K_d, pygame.K_RIGHT):
                        if fila_sel == 0: volumen = min(100, volumen + 10)
                        else: modo = modos[(modos.index(modo) + 1) % len(modos)]

            ventana.fill('black')
            titulo = f_titulo.render('AJUSTES', True, 'white')
            ventana.blit(titulo, titulo.get_rect(center=(W // 2, 100)))

            fila = pygame.Rect(0, 0, 420, 70)
            fila.center = (W // 2, 240)
            pygame.draw.rect(ventana, (0, 120, 0), fila)
            ventana.blit(f_texto.render('Sonidos', True, 'white'), (fila.x + 20, fila.centery - 12))
            valor = f_texto.render('< ' + str(volumen) + ' >', True, 'white')
            ventana.blit(valor, valor.get_rect(midright=(fila.right - 20, fila.centery)))

            for i in range(10):
                color = (255, 255, 255) if i < volumen // 10 else (70, 70, 70)
                pygame.draw.rect(ventana, color, (fila.x + i * 42, fila.bottom + 25, 36, 12))

            fila2 = pygame.Rect(0, 0, 420, 70)
            fila2.center = (W // 2, 390)
            pygame.draw.rect(ventana, (0, 120, 0), fila2)
            ventana.blit(f_texto.render('Combate', True, 'white'), (fila2.x + 20, fila2.centery - 12))
            valor2 = f_texto.render('< ' + modo.title() + ' >', True, 'white')
            ventana.blit(valor2, valor2.get_rect(midright=(fila2.right - 20, fila2.centery)))
            d = fuente.render(descripcion[modo], True, (200, 200, 200))
            ventana.blit(d, d.get_rect(center=(W // 2, fila2.bottom + 30)))
            dibujar_esquinas(ventana, fila if fila_sel == 0 else fila2)

            ayuda = fuente.render('W / S: elegir opcion    A / D: cambiar    ESC: volver', True, (200, 200, 200))
            ventana.blit(ayuda, ayuda.get_rect(center=(W // 2, H - 60)))
            pygame.display.flip(); reloj_ajustes.tick(60)

    equipo_menu = [n for n in ('pikachu', 'blastoise', 'lucario') if n in JUGABLES]
    config = {'volumen': 50, 'modo': 'mouse'}
    estado = 'titulo'

    while True:
        if estado == 'titulo':
            if pantalla_titulo() == 'salir': pygame.quit(); sys.exit()
            estado = 'menu'
            continue
        accion = menu_principal(equipo_menu)
        if accion == 'cerrar': pygame.quit(); sys.exit()
        if accion == 'titulo': estado = 'titulo'
        if accion == 'jugar':
            resultado, _ = jugar(equipo_menu, config)
            pygame.mouse.set_visible(True)
            if resultado == 'salir': pygame.quit(); sys.exit()
        if accion == 'pokedex':
            if pokedex() == 'salir': pygame.quit(); sys.exit()
        if accion == 'ajustes':
            resultado_ajustes = ajustes(config['volumen'], config['modo'])
            if resultado_ajustes is None: pygame.quit(); sys.exit()
            config['volumen'], config['modo'] = resultado_ajustes
            aplicar_volumen()
        if accion == 'salir' and confirmar('¿Seguro que quieres salir?'): pygame.quit(); sys.exit()

if __name__ == '__main__':
    main()