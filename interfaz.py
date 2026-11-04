"""
interfaz.py - Los menus: ajustes, controles, trucos, glosario, inicial, equipo (TAB), ficha, mochila y dialogos.

    from interfaz import menus
"""

import math
import os
import random
from types import SimpleNamespace
import pygame
import datos
import mecanicas
from datos import mts, tienda
from sistema import controles, opciones, partidas, tipografia, animaciones
from mundo import entorno
from combate import progreso


# ==================== menus ====================

def armar_menus():
    """Pantallas con el mismo estilo que los menus del juego: ajustes, controles, trucos, glosario,
    eleccion del inicial, menu de equipo (TAB) y los dialogos.

    Todas reciben 'ui', un diccionario que arma main.py:
        {'ventana', 'W', 'H', 'presentar', 'raton', 'a_logico', 'retrato' (nombre, lado), 'config', 'aplicar_pantalla', 'aplicar_volumen'}
    Devuelven 'salir' si se cerro la ventana.
    """
    pokemones, normalizar_tipo, ROL_POKEMON = datos.pokemones.pokemones, datos.pokemones.normalizar_tipo, datos.pokemones.ROL_POKEMON
    AnimadorPokemon, tiene_sprites = animaciones.AnimadorPokemon, animaciones.tiene_sprites

    COLORES_TIPO = {'lucha': (220, 70, 70), 'hielo': (130, 220, 255), 'volador': (235, 235, 235), 'tierra': (170, 115, 65), 'electrico': (245, 220, 40),
                    'agua': (70, 130, 235), 'fuego': (240, 128, 48), 'planta': (120, 200, 80), 'veneno': (160, 64, 160), 'psiquico': (249, 85, 135),
                    'bicho': (166, 185, 26), 'roca': (182, 161, 54), 'fantasma': (115, 87, 151), 'dragon': (111, 53, 252), 'siniestro': (112, 87, 70),
                    'acero': (183, 183, 206), 'normal': (168, 167, 122), 'hada': (214, 133, 173)}
    GRIS, OSCURO, PANEL = (128, 128, 128), (35, 35, 35), (32, 32, 32)
    FONDOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'interfaz', 'fondos')
    PANELES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'interfaz', 'paneles')
    HAY_FONDO = os.path.isfile(os.path.join(PANELES, 'fondo.png'))
    TINTA = 'white' if HAY_FONDO else (25, 25, 25)            # texto suelto sobre el fondo de los menus: sobre el gris va oscuro, sobre el de BW blanco
    ALERTA = (255, 130, 130) if HAY_FONDO else (120, 30, 30)
    BORDES = {'boton': 8, 'boton_elegido': 8, 'panel': 6, 'miembro': 10, 'miembro_activo': 10, 'miembro_debil': 10}
    INICIALES = ('mudkip', 'torchic', 'riolu', 'natu')            # uno por rol: tanque, atacante, velocista y estratega (todos evolucionan)
    ESTILO_INICIAL = {'mudkip': 'Aguanta los golpes y pelea de cerca', 'torchic': 'Pega fuerte y sube rapido de daño',
                      'riolu': 'Rapido, vive del parry y del combo', 'natu': 'Controla la sala con estados y desde lejos'}
    SUEÑO = 8000                                     # ms sin tocar nada para que los pokemon del escenario se duerman
    _fuentes = {}
    _paneles = {}


    def fuente(tam):
        """Fuente del tamaño pedido (se crea una sola vez)."""
        return tipografia.fuente(tam)                     # la letra de los juegos de DS (sistema.tipografia)


    # ---------- piezas de BW (assets/interfaz/paneles, las recorta: python herramientas.py paneles) ----------

    def pieza(nombre):
        """assets/interfaz/paneles/<nombre>.png o None."""
        if nombre not in _paneles:
            ruta = os.path.join(PANELES, nombre + '.png')
            try: _paneles[nombre] = pygame.image.load(ruta).convert_alpha() if os.path.isfile(ruta) else None
            except pygame.error: _paneles[nombre] = None
        return _paneles[nombre]


    def caja(ventana, rect, nombre, color=OSCURO, borde=0, color_borde='white'):
        """Una pieza de BW estirada al rect sin deformar las esquinas (las esquinas se copian, los bordes y el medio se estiran).
        Si no esta la pieza, el rectangulo de siempre: color y un borde de 'borde' px."""
        rect = pygame.Rect(rect)
        img = pieza(nombre)
        if not img:
            pygame.draw.rect(ventana, color, rect)
            if borde: pygame.draw.rect(ventana, color_borde, rect, borde)
            return
        clave = (nombre, rect.size)
        if clave not in _paneles:
            w, h, b = img.get_width(), img.get_height(), BORDES.get(nombre, 6)
            e = max(1, min(2, rect.width // (b * 2), rect.height // (b * 2)))     # los pixeles al doble, si entran
            B = b * e
            sup = pygame.Surface(rect.size, pygame.SRCALPHA)
            xs = ((0, b, 0, B), (b, w - b, B, rect.width - B), (w - b, w, rect.width - B, rect.width))
            ys = ((0, b, 0, B), (b, h - b, B, rect.height - B), (h - b, h, rect.height - B, rect.height))
            for x0, x1, dx0, dx1 in xs:
                for y0, y1, dy0, dy1 in ys:
                    if dx1 > dx0 and dy1 > dy0: sup.blit(pygame.transform.scale(img.subsurface((x0, y0, x1 - x0, y1 - y0)), (dx1 - dx0, dy1 - dy0)), (dx0, dy0))
            _paneles[clave] = sup
        ventana.blit(_paneles[clave], rect)


    def fondo(ventana, nombre='fondo', color=GRIS, estirar=False):
        """Fondo de BW: repetido al doble (o estirado a la pantalla si no se puede repetir). Si no esta, el color. Devuelve si habia pieza."""
        img = pieza(nombre)
        if not img: ventana.fill(color); return False
        W, H = ventana.get_size()
        clave = (nombre, 'estirado' if estirar else 'doble')
        if clave not in _paneles: _paneles[clave] = pygame.transform.scale(img, (W, H) if estirar else (img.get_width() * 2, img.get_height() * 2))
        t = _paneles[clave]
        ahora = pygame.time.get_ticks()
        dx, dy = (0, 0) if estirar else (-(ahora // 28) % t.get_width(), -(ahora // 40) % t.get_height())   # la grilla de BW se mueve en diagonal
        for x in range(dx - (t.get_width() if dx else 0), W, t.get_width()):
            for y in range(dy - (t.get_height() if dy else 0), H, t.get_height()): ventana.blit(t, (x, y))
        if not estirar: pokeball_girando(ventana, (W - 70, H + 10), 420, ahora, 34)   # la Pokeball de la pantalla tactil, de fondo
        return True


    _girando = {}


    def pokeball_girando(ventana, centro, lado, ahora, alfa=255, vueltas_por_minuto=6):
        """La Pokeball grande de la pantalla tactil de BW girando despacio (lado en pixeles, alfa 0-255)."""
        img = hud('pokeball')
        if not img: return
        clave = (lado, alfa)
        if clave not in _girando:
            base = pygame.transform.smoothscale(img, (lado, lado)).convert_alpha()
            if alfa < 255: base.fill((255, 255, 255, alfa), special_flags=pygame.BLEND_RGBA_MULT)
            _girando[clave] = base
        angulo = (ahora * vueltas_por_minuto * 360 / 60000) % 360
        rotada = pygame.transform.rotate(_girando[clave], -angulo)
        ventana.blit(rotada, rotada.get_rect(center=centro))


    def ajustar_texto(texto, f, ancho):
        """Corta un texto en lineas que entren en 'ancho' pixeles."""
        lineas, actual = [], ''
        for palabra in str(texto).split():
            prueba = (actual + ' ' + palabra).strip()
            if not actual or f.size(prueba)[0] <= ancho: actual = prueba
            else: lineas.append(actual); actual = palabra
        if actual: lineas.append(actual)
        return lineas


    def dibujar_esquinas(pantalla, rect, color=(255, 255, 255), margen=10, largo=14, grosor=3):
        """Las esquinitas que marcan la opcion elegida."""
        r = rect.inflate(margen * 2, margen * 2)
        x1, y1, x2, y2 = r.left, r.top, r.right - 1, r.bottom - 1
        for (ax, ay), (bx, by) in (((x1, y1), (x1 + largo, y1)), ((x1, y1), (x1, y1 + largo)), ((x2, y1), (x2 - largo, y1)), ((x2, y1), (x2, y1 + largo)),
                                   ((x1, y2), (x1 + largo, y2)), ((x1, y2), (x1, y2 - largo)), ((x2, y2), (x2 - largo, y2)), ((x2, y2), (x2, y2 - largo))):
            pygame.draw.line(pantalla, color, (ax, ay), (bx, by), grosor)


    def boton(ventana, rect, texto, elegido=False, tam=34, valor=None, aparicion=1.0, variante=None):
        """Boton con los paneles en flecha del menu de equipo de BW: azul oscuro, y celeste corrido a la derecha el elegido.
        valor: texto a la derecha con < >. aparicion: 0 -> 1 mientras entra deslizandose desde la izquierda (ver aparecer).
        variante: (fila, columna) del panel de la hoja si se quiere otro color (rojo, verde)."""
        rect = pygame.Rect(rect)
        if aparicion < 1: rect = rect.move(-round((1 - aparicion) * (rect.right + 40)), 0)
        if elegido: rect = rect.move(10, 0)
        fila = (variante or (0, 0))[0]
        panel_flecha(ventana, rect, (fila, 1) if elegido else (fila, variante[1] if variante else 0))
        if elegido:                                               # brillo que late en el elegido
            if math.sin(pygame.time.get_ticks() / 140) > 0: pygame.draw.rect(ventana, (255, 255, 255), rect.inflate(4, 4), 2, border_radius=8)
        t = fuente(tam).render(texto, True, 'white')
        if valor is None: ventana.blit(t, t.get_rect(center=rect.center))
        else:
            ventana.blit(t, t.get_rect(midleft=(rect.x + 22, rect.centery)))
            v = fuente(tam).render('< ' + str(valor) + ' >', True, (255, 236, 120) if elegido else (220, 220, 220))
            ventana.blit(v, v.get_rect(midright=(rect.right - 22, rect.centery)))
        if elegido: dibujar_esquinas(ventana, rect, margen=5, largo=12)


    TITULO_POS = (40, 12)                                         # todos los menus ponen el titulo en el mismo lugar y del mismo tamaño
    CONTENIDO_Y = 96                                              # debajo del titulo arranca el contenido
    MARGEN_X = 40


    def titulo(ventana, texto, x=None, y=None, tam=None, color=None):
        """Titulo grande de un menu, con la letra de los titulos del PMD (blanca con borde negro).
        Siempre en TITULO_POS y a escala 3 (x, y y tam quedan por compatibilidad: se ignoran)."""
        ventana.blit(tipografia.fuente_titulo(3).render(texto, True, color if color not in (None, TINTA) else 'white'), TITULO_POS)


    def pie(ventana, texto, color=(230, 230, 240)):
        """La linea de ayuda de abajo (teclas) en el mismo lugar en todos los menus, sobre una franja oscura para que se lea."""
        W, H = ventana.get_size()
        t = fuente(22).render(texto, True, color)
        franja = pygame.Surface((W, 30), pygame.SRCALPHA); franja.fill((0, 0, 0, 120)); ventana.blit(franja, (0, H - 30))
        ventana.blit(t, t.get_rect(midleft=(MARGEN_X, H - 15)))


    pie_menu = pie                                                # para las funciones que tienen un parametro que se llama 'pie'


    # ---------- logo: POKE con la letra de pokemon y MANIC en Unown ----------
    FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'interfaz', 'fuentes')
    # trazos de cada letra Unown (puntos de 0 a 1 dentro de la casilla) y donde va el ojo; el ancho es relativo al alto
    UNOWN = {'M': {'ancho': 0.9, 'trazos': [[(0, 1), (0.08, 0.1), (0.5, 0.55), (0.92, 0.1), (1, 1)]], 'ojo': (0.5, 0.5)},
             'A': {'ancho': 0.8, 'trazos': [[(0, 1), (0.5, 0.02), (1, 1)]], 'ojo': (0.5, 0.62)},
             'N': {'ancho': 0.75, 'trazos': [[(0.08, 1), (0.08, 0), (0.92, 1), (0.92, 0)]], 'ojo': (0.5, 0.5)},
             'I': {'ancho': 0.35, 'trazos': [[(0.5, 0), (0.5, 1)]], 'ojo': (0.5, 0.45)},
             'C': {'ancho': 0.75, 'trazos': [[(0.55 + 0.45 * math.cos(math.radians(a)), 0.5 - 0.48 * math.sin(math.radians(a))) for a in range(45, 316, 15)]],
                   'ojo': (0.1, 0.5)}}
    _logo = {}


    def _ttf(nombre, tam):
        """Fuente .ttf de assets/interfaz/fuentes o None si no esta."""
        ruta = os.path.join(FUENTES, nombre)
        return pygame.font.Font(ruta, tam) if os.path.isfile(ruta) else None


    def _contorno(sup, color, grosor):
        """La misma superficie con un borde de color alrededor de la silueta."""
        sil = pygame.mask.from_surface(sup).to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
        nueva = pygame.Surface((sup.get_width() + grosor * 2, sup.get_height() + grosor * 2), pygame.SRCALPHA)
        for ang in range(0, 360, 30): nueva.blit(sil, (grosor + round(math.cos(math.radians(ang)) * grosor), grosor + round(math.sin(math.radians(ang)) * grosor)))
        nueva.blit(sup, (grosor, grosor))
        return nueva


    def _letra_unown(letra, alto):
        """Una letra Unown: con unown.ttf si esta, si no dibujada (trazo negro con el ojo en el medio)."""
        f = _ttf('unown.ttf', alto)
        if f: return _contorno(f.render(letra, True, (20, 20, 20)), (235, 235, 235), max(2, alto // 18))
        d = UNOWN[letra]
        g = max(4, alto // 6)
        ancho = round(alto * d['ancho']) + g * 2
        sup = pygame.Surface((ancho, alto + g * 2), pygame.SRCALPHA)
        a_px = lambda p: (g + round(p[0] * (ancho - g * 2)), g + round(p[1] * alto))
        for trazo in d['trazos']:
            puntos = [a_px(p) for p in trazo]
            for (x1, y1), (x2, y2) in zip(puntos, puntos[1:]):         # circulitos pegados a lo largo del trazo: bordes redondos y parejos
                pasos = max(1, round(math.hypot(x2 - x1, y2 - y1) / 2))
                for k in range(pasos + 1): pygame.draw.circle(sup, (20, 20, 20), (x1 + (x2 - x1) * k / pasos, y1 + (y2 - y1) * k / pasos), g / 2)
        ojo, r = a_px(d['ojo']), max(5, round(alto * 0.21))
        pygame.draw.circle(sup, (20, 20, 20), ojo, r + g // 2)
        pygame.draw.circle(sup, (245, 245, 245), ojo, r)
        pygame.draw.circle(sup, (20, 20, 20), ojo, max(2, r // 2))
        return _contorno(sup, (235, 235, 235), max(2, alto // 18))


    def _texto_pokemon(texto, alto):
        """Amarillo con borde azul y sombra, como el logo de pokemon (pokemon.ttf si esta)."""
        f = _ttf('pokemon.ttf', alto)
        if not f: f = pygame.font.Font(None, round(alto * 1.35)); f.set_bold(True)
        sup = _contorno(f.render(texto, True, (255, 203, 5)), (50, 85, 165), max(3, alto // 11))
        sombra = pygame.mask.from_surface(sup).to_surface(setcolor=(25, 40, 90), unsetcolor=(0, 0, 0, 0))
        final = pygame.Surface((sup.get_width() + 4, sup.get_height() + 6), pygame.SRCALPHA)
        final.blit(sombra, (4, 6)); final.blit(sup, (0, 0))
        return final


    def dibujar_logo(ventana, alto, ahora, **donde):
        """POKEMANIC: POKE con la letra de los titulos del PMD (amarilla con borde azul, como el logo de Pokemon) y MANIC con letras
        Unown de HGSS que flotan un poco. donde: como en get_rect (center=..., topright=...). Si faltan las hojas, el logo de antes."""
        escala = max(2, round(alto / 24))
        poke_f = tipografia.fuente_titulo(escala, (40, 70, 160))
        letras = tipografia.unown('MANIC', max(2, round(alto / 14)))
        if not hasattr(poke_f, 'escala') or not letras:
            return _logo_viejo(ventana, alto, ahora, **donde)
        poke = poke_f.render('POKE', True, (255, 214, 40))
        sombra = pygame.mask.from_surface(poke).to_surface(setcolor=(20, 30, 80), unsetcolor=(0, 0, 0, 0))
        sep = alto // 6
        caja = pygame.Rect(0, 0, poke.get_width() + sep + sum(l.get_width() + sep // 2 for l in letras), max(poke.get_height(), alto))
        for clave, valor in donde.items(): setattr(caja, clave, valor)
        ventana.blit(sombra, (caja.x + escala * 2, caja.centery - poke.get_height() // 2 + escala * 2))
        ventana.blit(poke, (caja.x, caja.centery - poke.get_height() // 2))
        x = caja.x + poke.get_width() + sep
        for i, l in enumerate(letras):
            y = caja.centery - l.get_height() // 2 + round(math.sin(ahora / 450 + i * 1.3) * alto * 0.06)
            ventana.blit(l, (x, y)); x += l.get_width() + sep // 2
        return caja


    def _logo_viejo(ventana, alto, ahora, **donde):
        """El logo dibujado (por si faltan las hojas de las letras)."""
        if alto not in _logo: _logo[alto] = (_texto_pokemon('POKE', alto), [_letra_unown(l, round(alto * 0.8)) for l in 'MANIC'])
        poke, letras = _logo[alto]
        sep = alto // 8
        caja = pygame.Rect(0, 0, poke.get_width() + sep + sum(l.get_width() + sep // 2 for l in letras), poke.get_height())
        for clave, valor in donde.items(): setattr(caja, clave, valor)
        ventana.blit(poke, caja.topleft)
        x = caja.x + poke.get_width() + sep
        for i, l in enumerate(letras):
            y = caja.centery - l.get_height() // 2 + round(math.sin(ahora / 450 + i * 1.3) * alto * 0.05)
            ventana.blit(l, (x, y)); x += l.get_width() + sep // 2
        return caja


    OBJETOS_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'interfaz', 'objetos')
    _iconos = {}


    def icono_objeto(clave, lado):
        """Icono de un objeto de la tienda: assets/interfaz/objetos/<clave>.png (las MT tambien buscan mt_<tipo>.png). None si no hay."""
        if (clave, lado) not in _iconos:
            item = tienda.ITEMS.get(clave, {})
            img = None
            for nombre in (clave, 'mt_' + str(item.get('tipo')) if item.get('mt') else None):
                ruta = os.path.join(OBJETOS_IMG, str(nombre) + '.png')
                if nombre and os.path.isfile(ruta): img = pygame.transform.scale(pygame.image.load(ruta).convert_alpha(), (lado, lado)); break
            _iconos[(clave, lado)] = img
        return _iconos[(clave, lado)]


    def chip_tipo(ventana, tipo, x, y):
        """Etiqueta redondeada del color de un tipo. Devuelve el ancho que ocupo (para poner la siguiente al lado)."""
        color = COLORES_TIPO.get(tipo, (150, 150, 150))
        t = fuente(20).render(str(tipo).upper(), True, 'white')         # como los iconos de tipo de BW: letra blanca con sombra
        r = pygame.Rect(x, y, t.get_width() + 14, t.get_height() + 8)
        oscuro = tuple(max(0, c - 70) for c in color)
        pygame.draw.rect(ventana, oscuro, r, border_radius=4)
        pygame.draw.rect(ventana, color, r.inflate(-4, -4), border_radius=3)
        pygame.draw.line(ventana, tuple(min(255, c + 60) for c in color), (r.x + 4, r.y + 3), (r.right - 5, r.y + 3), 2)   # el brillo de arriba
        ventana.blit(t, t.get_rect(center=r.center))
        return r.width + 6


    # colores de las barras de vida de Blanco/Negro (hoja Battle HUD): claro arriba y oscuro abajo
    VIDA_BW = ((0.5, (0, 248, 72), (0, 189, 33)), (0.2, (234, 255, 0), (173, 189, 0)), (0.0, (255, 0, 0), (189, 0, 0)))


    def barra_vida(ventana, rect, k, etiqueta=True):
        """Barra de vida como la de BW: verde, amarilla debajo de la mitad y roja debajo del 20%. Con etiqueta, el 'HP' verde a la izquierda."""
        rect = pygame.Rect(rect)
        k = max(0.0, min(1.0, k))
        if etiqueta:
            hp = pygame.Rect(rect.x, rect.y, max(26, round(rect.height * 1.4)), rect.height)
            pygame.draw.rect(ventana, (40, 40, 40), hp, border_radius=3)
            t = fuente(max(14, min(30, rect.height + 4))).render('HP', True, (0, 248, 72))
            ventana.blit(t, t.get_rect(center=hp.center))
            rect = rect.copy(); rect.x += hp.width - 2; rect.width -= hp.width - 2
        pygame.draw.rect(ventana, (40, 40, 40), rect, border_radius=3)
        adentro = rect.inflate(-4, -4)
        pygame.draw.rect(ventana, (248, 248, 248), adentro.inflate(2, 2))
        pygame.draw.rect(ventana, (80, 80, 80), adentro)
        claro, oscuro = next((c, o) for limite, c, o in VIDA_BW if k > limite or limite == 0.0)
        lleno = pygame.Rect(adentro.x, adentro.y, round(adentro.width * k), adentro.height)
        if lleno.width:
            pygame.draw.rect(ventana, claro, lleno)
            pygame.draw.rect(ventana, oscuro, (lleno.x, lleno.y + lleno.height * 2 // 3, lleno.width, lleno.height - lleno.height * 2 // 3))


    def barra(ventana, rect, k, color, fondo=(60, 60, 60)):
        """Barra simple (fondo, relleno de 0 a 1 y borde)."""
        pygame.draw.rect(ventana, fondo, rect)
        pygame.draw.rect(ventana, color, (rect[0], rect[1], int(rect[2] * max(0, min(1, k))), rect[3]))
        pygame.draw.rect(ventana, 'black', rect, 2)


    # ---------- piezas del HUD de BW (assets/interfaz/hud, las recorta: python herramientas.py hud) ----------

    HUD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'interfaz', 'hud')
    # barras de HP del combate: columnas del hueco donde va la vida y filas del relleno (clara arriba, oscura abajo)
    BARRAS = {'rival': {'pieza': 'barra_rival', 'hueco': (44, 91), 'filas': (8, 9), 'nv': (85, 101)},
              'jugador': {'pieza': 'barra_jugador', 'hueco': (56, 103), 'filas': (9, 10), 'nv': (80, 90)}}
    COLOR_EXP = (64, 200, 248)
    _hud = {}


    def hud(nombre, escala=1):
        """Pieza del HUD de BW agrandada x escala (pixeles enteros) o None si no esta."""
        clave = (nombre, escala)
        if clave not in _hud:
            ruta = os.path.join(HUD, nombre + '.png')
            try: img = pygame.image.load(ruta).convert_alpha() if os.path.isfile(ruta) else None
            except pygame.error: img = None
            _hud[clave] = pygame.transform.scale(img, (img.get_width() * escala, img.get_height() * escala)) if img and escala != 1 else img
        return _hud[clave]


    def _estirada(nombre, ancho, hueco, quitar=None):
        """La pieza con el hueco del medio estirado hasta 'ancho' (a escala 1): se repite una columna del hueco.
        quitar: columnas (desde, hasta) de las filas de arriba a borrar (el icono 'Lv', que se dibuja aparte)."""
        clave = ('estirada', nombre, ancho)
        if clave not in _hud:
            img = hud(nombre)
            if not img: _hud[clave] = None; return None
            img = img.copy()
            if quitar:
                for x in range(*quitar):
                    for y in range(0, 6):
                        if x < img.get_width(): img.set_at((x, y), (0, 0, 0, 0))
            w, h = img.get_size(); a, b = hueco[0] + 4, hueco[1] - 3
            extra = max(0, ancho - w)
            sup = pygame.Surface((w + extra, h), pygame.SRCALPHA)
            sup.blit(img, (0, 0), (0, 0, a, h))
            columna = img.subsurface((a, 0, 1, h))
            for x in range(a, b + extra): sup.blit(columna, (x, 0))
            sup.blit(img, (b + extra, 0), (b, 0, w - b, h))
            _hud[clave] = sup
        return _hud[clave]


    def color_vida(k):
        """(claro, oscuro) de la barra de vida de BW: verde, amarilla debajo de la mitad y roja debajo del 20%."""
        return next((c, o) for limite, c, o in VIDA_BW if k > limite or limite == 0.0)


    def barra_hp(ventana, x, y, ancho, k, cual='rival', escala=2, nivel=None, fuente_nv=None, k_atras=None):
        """Barra de HP del combate de BW ('rival': la de arriba, 'jugador': la tuya con la placa oscura) de 'ancho' pixeles de pantalla.
        Si no estan las piezas, la barra de vida de siempre. Devuelve el rect dibujado."""
        datos_b = BARRAS[cual]
        img = _estirada(datos_b['pieza'], ancho // escala, datos_b['hueco'], datos_b['nv'])
        if not img:
            r = pygame.Rect(x, y, ancho, 8 * escala); barra_vida(ventana, r, k); return r
        extra = img.get_width() - hud(datos_b['pieza']).get_width()
        grande = pygame.transform.scale(img, (img.get_width() * escala, img.get_height() * escala))
        ventana.blit(grande, (x, y))
        k = max(0.0, min(1.0, k))
        h0, h1 = datos_b['hueco'][0], datos_b['hueco'][1] + extra
        largo = round((h1 - h0 + 1) * escala * k)
        claro, oscuro = color_vida(k)
        f0, f1 = datos_b['filas']
        if k_atras is not None and k_atras > k:                     # lo que te acaban de sacar: blanco que se vacia de a poco
            hasta = round((h1 - h0 + 1) * escala * min(1.0, k_atras))
            pygame.draw.rect(ventana, (255, 255, 255), (x + h0 * escala + largo, y + f0 * escala, hasta - largo, escala))
            pygame.draw.rect(ventana, (255, 170, 150), (x + h0 * escala + largo, y + f1 * escala, hasta - largo, escala))
        if largo:
            pygame.draw.rect(ventana, claro, (x + h0 * escala, y + f0 * escala, largo, escala))
            pygame.draw.rect(ventana, oscuro, (x + h0 * escala, y + f1 * escala, largo, escala))
        if nivel is not None:                                       # el 'Lv' de BW arriba de la barra y el numero
            nv = hud('nv', escala)
            px = x + (datos_b['nv'][0] + extra) * escala
            if nv: ventana.blit(nv, (px, y - escala))
            t = (fuente_nv or tipografia.fuente(20, borde=True)).render(str(nivel), True, 'white')
            ventana.blit(t, (px + (nv.get_width() if nv else 0) + 2, y - escala - t.get_height() + (nv.get_height() if nv else 8) + 2))
        return pygame.Rect(x, y, grande.get_width(), grande.get_height())


    def barra_exp(ventana, x, y, ancho, k, color=COLOR_EXP, escala=2):
        """Barra fina de experiencia de BW (tambien sirve para la energia con otro color)."""
        img = _estirada('barra_exp', ancho // escala, (9, 88))
        if not img: barra(ventana, (x, y, ancho, 4 * escala), k, color); return
        ventana.blit(pygame.transform.scale(img, (img.get_width() * escala, img.get_height() * escala)), (x, y))
        extra = img.get_width() - hud('barra_exp').get_width()
        largo = round((88 + extra - 9 + 1) * escala * max(0.0, min(1.0, k)))
        if largo: pygame.draw.rect(ventana, color, (x + 9 * escala, y + 3 * escala, largo, escala))


    _octagonos = {}


    def boton_tactil(ventana, centro, radio, k_espera=0.0, acento=None, apagado=False):
        """Boton octogonal de la pantalla tactil de BW (Luchar / Mochila / Huir): textura de puntitos, borde blanco grueso.
        k_espera: 0 listo, 1 recien usado (se oscurece en abanico). acento: color del borde de adentro (el tipo del movimiento)."""
        clave = (radio, acento, apagado)
        if clave not in _octagonos:
            lado = radio * 2 + 4
            sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
            c = lado / 2
            puntos = lambda r: [(c + r * math.cos(math.radians(22.5 + 45 * i)), c + r * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
            pygame.draw.polygon(sup, (33, 33, 33), puntos(radio + 1))
            pygame.draw.polygon(sup, (230, 230, 230), puntos(radio - 1))
            interior = pygame.Surface((lado, lado), pygame.SRCALPHA)
            tile = hud('textura_boton', 2)
            if tile:
                for tx in range(0, lado, tile.get_width()):
                    for ty in range(0, lado, tile.get_height()): interior.blit(tile, (tx, ty))
            else: interior.fill((60, 60, 60))
            if apagado: interior.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_SUB)      # sin poder usarse: mas oscuro
            mascara = pygame.Surface((lado, lado), pygame.SRCALPHA)
            pygame.draw.polygon(mascara, (255, 255, 255, 255), puntos(radio - 5))
            interior.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            sup.blit(interior, (0, 0))
            if acento: pygame.draw.polygon(sup, acento, puntos(radio - 5), 3)
            _octagonos[clave] = sup
        sup = _octagonos[clave]
        ventana.blit(sup, sup.get_rect(center=centro))
        if k_espera > 0:                                            # la espera: un abanico oscuro que se va cerrando
            r = radio - 5
            puntos = [centro] + [(centro[0] + r * 1.08 * math.sin(math.tau * t / 24), centro[1] - r * 1.08 * math.cos(math.tau * t / 24))
                                 for t in range(0, round(24 * k_espera) + 1)]
            if len(puntos) > 2:
                capa = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
                desplazados = [(px - centro[0] + radio + 2, py - centro[1] + radio + 2) for px, py in puntos]
                pygame.draw.polygon(capa, (0, 0, 0, 165), desplazados)
                mascara = pygame.Surface(capa.get_size(), pygame.SRCALPHA)
                c = radio + 2
                pygame.draw.polygon(mascara, (255, 255, 255, 255), [(c + (radio - 5) * math.cos(math.radians(22.5 + 45 * i)), c + (radio - 5) * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)])
                capa.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                ventana.blit(capa, (centro[0] - radio - 2, centro[1] - radio - 2))


    ESTADO_ICONO = {'quemar': 'estado_brn', 'paralizar': 'estado_par', 'congelado': 'estado_frz', 'veneno': 'estado_psn', 'debilitado': 'estado_fnt'}


    def icono_estado(ventana, estado, centro, escala=2):
        """Icono de estado de BW (BRN, PAR, FRZ...) centrado en 'centro'. Dormido y frenado no tienen icono en BW: se escribe."""
        nombre = ESTADO_ICONO.get(estado)
        img = hud(nombre, escala) if nombre else None
        if img: ventana.blit(img, img.get_rect(center=centro)); return
        texto = {'dormir': 'zZ', 'ralentizar': '↓', 'confusion': '??', 'aturdido': '**'}.get(estado)
        if texto:
            color = {'ralentizar': (150, 200, 255), 'confusion': (255, 150, 200), 'aturdido': (255, 255, 160)}.get(estado, 'white')
            t = tipografia.fuente(20, borde=True).render(texto, True, color)
            ventana.blit(t, t.get_rect(center=centro))


    def panel_flecha(ventana, rect, variante=(0, 0)):
        """Panel en flecha del menu de equipo de BW (fila, columna de la hoja) estirado al rect, con las puntas sin deformar."""
        rect = pygame.Rect(rect)
        nombre = 'panel_%d_%d' % variante
        img = hud(nombre)
        if not img:
            pygame.draw.rect(ventana, (40, 90, 150), rect, border_radius=10); pygame.draw.rect(ventana, 'white', rect, 2, border_radius=10); return
        clave = ('flecha', nombre, rect.size)
        if clave not in _hud:
            w, h = img.get_size()
            e = max(1, min(3, rect.height // h + (1 if rect.height % h > h * 0.6 else 0)))
            alto = rect.height
            punta = 12                                              # las puntas (esquinas cortadas) no se estiran
            izq = pygame.transform.scale(img.subsurface((0, 0, punta, h)), (punta * alto // h, alto))
            der = pygame.transform.scale(img.subsurface((w - punta, 0, punta, h)), (punta * alto // h, alto))
            medio = pygame.transform.scale(img.subsurface((punta, 0, w - 2 * punta, h)), (max(1, rect.width - izq.get_width() - der.get_width()), alto))
            sup = pygame.Surface(rect.size, pygame.SRCALPHA)
            sup.blit(izq, (0, 0)); sup.blit(medio, (izq.get_width(), 0)); sup.blit(der, (rect.width - der.get_width(), 0))
            _hud[clave] = sup
        ventana.blit(_hud[clave], rect)


    def aparecer(t, retraso=0, dura=260):
        """0 -> 1 con frenada al final (para que las cosas entren deslizandose): t = ms desde que se abrio el menu."""
        k = max(0.0, min(1.0, (t - retraso) / dura))
        return 1 - (1 - k) ** 3


    # ---------- fondo del menu principal ----------

    _fondo = {'img': None, 'cargado': False, 'celebi': None, 'hojas': []}


    def fondo_menu(ui, ahora, con_celebi=True):
        """Fondo del titulo y del menu: assets/interfaz/fondos/menu.png si existe; si no, el Templo de la Pureza dibujado (con Celebi)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        if not _fondo['cargado']:
            _fondo['cargado'] = True
            ruta = os.path.join(FONDOS, 'menu.png')
            if os.path.isfile(ruta):
                try: _fondo['img'] = pygame.transform.smoothscale(pygame.image.load(ruta).convert(), (W, H))
                except pygame.error: pass
            if tiene_sprites('celebi'):
                _fondo['celebi'] = AnimadorPokemon('celebi', pygame.Rect(0, 0, 60, 60), 90)
                _fondo['celebi'].cambiar('idle', 0, True)
            azar = random.Random(4)
            _fondo['hojas'] = [[azar.uniform(0, W), azar.uniform(0, H), azar.uniform(0.3, 1.0), azar.uniform(0, math.tau)] for _ in range(26)]
        if _fondo['img']:
            ventana.blit(_fondo['img'], (0, 0))
        else:
            for y in range(0, H, 4):                                 # cielo verdoso del bosque
                k = y / H
                pygame.draw.rect(ventana, (round(40 + 50 * k), round(90 + 60 * k), round(70 + 30 * k)), (0, y, W, 4))
            azar = random.Random(7)
            for capa, color in ((0, (30, 70, 45)), (1, (22, 55, 35))):  # arboles lejanos y cercanos
                for i in range(14):
                    x = (i * 83 + capa * 41) % (W + 80) - 40
                    alto = azar.randint(180, 320) + capa * 60
                    pygame.draw.rect(ventana, (45, 35, 25), (x + 30, H - alto // 2, 18 + capa * 6, alto // 2))
                    pygame.draw.circle(ventana, color, (x + 40, H - alto // 2), 70 + capa * 20)
            cx = W // 2                                              # templo de la pureza: columnas cubiertas de enredaderas
            pygame.draw.polygon(ventana, (150, 155, 140), [(cx - 230, 250), (cx + 230, 250), (cx, 170)])
            pygame.draw.rect(ventana, (165, 170, 150), (cx - 240, 250, 480, 26))
            for i in range(5):
                x = cx - 200 + i * 100
                pygame.draw.rect(ventana, (175, 180, 160), (x - 16, 276, 32, 230))
                for k in range(6): pygame.draw.circle(ventana, (60, 130, 60), (x + (8 if k % 2 else -8), 290 + k * 36), 9)
            pygame.draw.rect(ventana, (120, 125, 110), (cx - 260, 506, 520, 30))
            pygame.draw.rect(ventana, (40, 90, 50), (0, 536, W, H - 536))
        for h in _fondo['hojas']:                                    # hojas que caen
            h[1] += h[2]; h[0] += math.sin(ahora / 900 + h[3]) * 0.6
            if h[1] > H: h[1] = -10; h[0] = random.uniform(0, W)
            pygame.draw.ellipse(ventana, (120, 200, 90), (h[0], h[1], 9, 5))
        if con_celebi and _fondo['celebi'] and not _fondo['img']:                  # Celebi flotando en la entrada del templo
            a = _fondo['celebi']
            a.rect.center = (W // 2, 420 + round(math.sin(ahora / 500) * 10))
            a.actualizar(); a.dibujar(ventana)


    # ---------- intro: del cielo a la isla ----------

    def intro(ui, duracion=7000):
        """Cinematica del principio: arranca en el cielo del Explorers of Sky (assets/interfaz/fondos/cielo.png y nube_<n>.png,
        los recorta: python herramientas.py cielo), las nubes suben y la camara baja hasta la isla del menu.
        Cualquier tecla o clic la saltea. Devuelve 'salir' si se cerro la ventana."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        cargar = lambda nombre: pygame.image.load(os.path.join(FONDOS, nombre)).convert_alpha() if os.path.isfile(os.path.join(FONDOS, nombre)) else None
        cielo = cargar('cielo.png')
        if not cielo: return None
        ALTO_CIELO = H * 2                                               # el cielo ocupa dos pantallas arriba de la isla
        cielo = pygame.transform.scale(cielo, (W, ALTO_CIELO + 260))
        sprites = [n for n in (cargar('nube_' + str(i) + '.png') for i in range(8)) if n]
        azar = random.Random(11)
        nubes = []
        for i in range(18):                                              # mas lejos = mas chicas, mas lentas y mas transparentes
            lejos = azar.random()
            img = sprites[i % len(sprites)] if sprites else None
            if img:
                img = pygame.transform.scale(img, (round(img.get_width() * (2 + 2.5 * (1 - lejos))), round(img.get_height() * (2 + 2.5 * (1 - lejos)))))
                if azar.random() < 0.5: img = pygame.transform.flip(img, True, False)
                img.set_alpha(round(150 + 105 * (1 - lejos)))
            nubes.append({'img': img, 'x': azar.uniform(-150, W), 'y': azar.uniform(H * 0.3, ALTO_CIELO + H * 0.6), 'paralaje': 1.25 + 0.7 * (1 - lejos),
                          'deriva': azar.uniform(-0.03, 0.03), 'lejos': lejos})
        nubes.sort(key=lambda n: -n['lejos'])
        isla = pygame.Surface((W, H))
        ui_isla = dict(ui, ventana=isla)
        borde = pygame.Surface((W, 240), pygame.SRCALPHA)                 # degrade para que el cielo se funda con la isla
        abajo = cielo.get_at((W // 2, cielo.get_height() - 1))
        for y in range(240): pygame.draw.line(borde, (abajo.r, abajo.g, abajo.b, round(255 * (1 - y / 240) ** 1.5)), (0, y), (W, y))
        aviso = fuente(20).render('cualquier tecla para saltar', True, (255, 255, 255))
        reloj = pygame.time.Clock()
        inicio = pygame.time.get_ticks()
        while True:
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN): return None
            t = pygame.time.get_ticks() - inicio
            if t >= duracion: return None
            k = max(0.0, min(1.0, (t - 900) / (duracion - 1800)))
            camara = ALTO_CIELO * k * k * (3 - 2 * k)                        # baja despacio, acelera y frena al llegar
            ventana.blit(cielo, (0, -camara))
            y_isla = ALTO_CIELO - camara
            if y_isla < H:
                fondo_menu(ui_isla, pygame.time.get_ticks())
                ventana.blit(isla, (0, y_isla))
                final = max(0.0, min(1.0, (t - (duracion - 1200)) / 900))   # el degrade se va al final, asi la isla queda igual que en el titulo
                if final < 1: borde.set_alpha(round(255 * (1 - final))); ventana.blit(borde, (0, y_isla))
            for n in nubes:                                              # las nubes suben mas rapido que la camara (parece que bajamos entre ellas)
                n['x'] += n['deriva'] * reloj.get_time() * 10
                y = n['y'] - camara * n['paralaje'] - t * 0.04 * n['paralaje']
                if n['img'] and -n['img'].get_height() < y < H: ventana.blit(n['img'], (n['x'], y))
            if t < 700:                                                  # aparece desde negro
                velo = pygame.Surface((W, H)); velo.set_alpha(round(255 * (1 - t / 700))); ventana.blit(velo, (0, 0))
            ventana.blit(aviso, aviso.get_rect(bottomright=(W - 14, H - 10)))
            ui['presentar'](); reloj.tick(60)


    # ---------- viaje temporal: el principio de una partida nueva ----------

    GENEROS = ('chico', 'chica', 'otro')
    LARGO_NOMBRE = 12
    _viaje = {'cuadros': None, 'apertura': None}


    def _cuadros_viaje(prefijo, cantidad, W, H):
        """Los cuadros assets/interfaz/fondos/<prefijo>_<n>.png escalados a la pantalla (lista vacia si no estan)."""
        cuadros = []
        for i in range(cantidad):
            ruta = os.path.join(FONDOS, prefijo + '_' + str(i) + '.png')
            if not os.path.isfile(ruta): break
            try: cuadros.append(pygame.transform.smoothscale(pygame.image.load(ruta).convert(), (W, H)))
            except pygame.error: break
        return cuadros


    def segun_genero(genero, chico, chica, otro):
        """El texto que corresponde al genero que elegiste (para los dialogos: 'bienvenido', 'bienvenida' o 'te damos la bienvenida')."""
        return {'chico': chico, 'chica': chica}.get(genero, otro)


    def fondo_viaje(ui, ahora):
        """El tunel del viaje temporal del Explorers of Sky (assets/interfaz/fondos/viaje_<n>.png, los recorta: python herramientas.py viaje).
        Si no estan, rayos de colores girando sobre azul oscuro."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        if _viaje['cuadros'] is None: _viaje['cuadros'] = _cuadros_viaje('viaje', 12, W, H)
        if _viaje['cuadros']:
            ventana.blit(_viaje['cuadros'][(ahora // 90) % len(_viaje['cuadros'])], (0, 0))
            return
        ventana.fill((20, 25, 70))
        for k in range(24):                                              # rayos que salen del centro y giran despacio
            ang = ahora / 2000 + k * math.tau / 24
            color = ((90, 200, 255), (160, 120, 255), (120, 255, 200))[k % 3]
            pygame.draw.line(ventana, color, (W // 2, H // 2), (W // 2 + math.cos(ang) * W, H // 2 + math.sin(ang) * W), 3)
        pygame.draw.circle(ventana, (230, 250, 255), (W // 2, H // 2), 40)


    def viaje_temporal(ui):
        """Partida nueva: se abre el tiempo (la apertura del Explorers of Time), aparece el tunel y Celebi llega dormido.
        Se despierta, te ve (sos una lucecita sin forma) y te habla: tu nombre, tu genero y que pokemon sos (como armar tu cuerpo en Deltarune).
        Devuelve {'nombre', 'genero', 'inicial'}, None si volves con ESC o 'salir'.
        Animaciones de Celebi: Float (llega dormido, flotando) -> Wake (se despierta) -> Idle mirandote -> Nod cuando le contestas.
        Vos: una luz que late; al elegir, un destello y aparece tu pokemon saltando (Hop) y despues quieto (Idle)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        reloj = pygame.time.Clock()
        celebi = AnimadorPokemon('celebi', pygame.Rect(0, 0, 10, 10), 100) if tiene_sprites('celebi') else None
        # celebi: 'lejos' (todavia no llego), 'durmiendo', 'despertando' o 'despierto'
        estado = {'asiente_hasta': 0, 'celebi': 'lejos', 'llego': 0, 'cuerpo': None, 'forma': 0}
        retrato = ui['retrato']('celebi', 84)
        caja_dialogo = pygame.Rect(40, H - 170, W - 80, 140)
        VELOCIDAD_TEXTO = 45                                             # letras por segundo
        CELEBI, VOS = (W // 2, 170), (W // 2, 330)                       # Celebi arriba mirando para abajo, vos abajo

        def dibujar_celebi(ahora):
            """Celebi segun en que parte esta: llega con un destello, flota dormido, se despierta y te mira."""
            if not celebi or estado['celebi'] == 'lejos': return
            k = (ahora - estado['llego']) / 500
            if k < 1:                                                    # destello al llegar
                pygame.draw.circle(ventana, (235, 255, 235), CELEBI, round(70 * (1 - k) + 10))
                for ang in range(0, 360, 45):
                    largo = 120 * (1 - k)
                    pygame.draw.line(ventana, 'white', CELEBI, (CELEBI[0] + math.cos(math.radians(ang)) * largo, CELEBI[1] + math.sin(math.radians(ang)) * largo), 3)
            if k < 0.4: return
            if estado['celebi'] == 'durmiendo': celebi.cambiar('float', 0, True) or celebi.cambiar('sleep', 0, True)
            elif estado['celebi'] == 'despertando':
                if not celebi.cambiar('wake', 0, False) or celebi.esta_terminada(): estado['celebi'] = 'despierto'
            if estado['celebi'] == 'despierto':
                celebi.cambiar('nod' if ahora < estado['asiente_hasta'] else 'idle', 0, True)
            celebi.rect.center = (CELEBI[0], CELEBI[1] + round(math.sin(ahora / 500) * 10))
            celebi.actualizar(); celebi.dibujar(ventana)

        def dibujar_vos(ahora):
            """Vos: una lucecita que late hasta que elegis que pokemon sos; despues tu pokemon (con un destello al aparecer)."""
            a = estado['cuerpo']
            k = (ahora - estado['forma']) / 600
            if a and k >= 0.3:
                if k > 1.6: a.cambiar('idle', 0, True)
                a.rect.center = VOS
                a.actualizar(); a.dibujar(ventana)
            if not a or k < 1:                                           # dorada con borde oscuro: si fuera blanca se perderia en el centro del tunel
                radio = (14 + round(math.sin(ahora / 260) * 3)) if not a else round(14 + 90 * k)
                apaga = (1 - k) if a else 1
                luz = pygame.Surface((radio * 4, radio * 4), pygame.SRCALPHA)
                for i, color in ((2.0, (255, 150, 60, 60)), (1.45, (255, 190, 90, 110)), (1.15, (70, 30, 90, 230)), (1.0, (255, 235, 170, 255))):
                    pygame.draw.circle(luz, (*color[:3], round(color[3] * apaga)), (radio * 2, radio * 2), round(radio * i))
                pygame.draw.circle(luz, (255, 255, 240, round(255 * apaga)), (radio * 2, radio * 2), max(2, radio // 2))
                ventana.blit(luz, (VOS[0] - radio * 2, VOS[1] - radio * 2))

        def escena(ahora):
            """El tunel, Celebi arriba y vos abajo."""
            fondo_viaje(ui, ahora)
            dibujar_celebi(ahora)
            dibujar_vos(ahora)

        def asentir():
            """Celebi asiente un momento (Nod) cuando le contestas."""
            estado['asiente_hasta'] = pygame.time.get_ticks() + 900

        def esperar(ms):
            """Deja correr la escena ms milisegundos. Cualquier tecla adelanta. None si ESC, 'salir' si se cerro la ventana."""
            fin = pygame.time.get_ticks() + ms
            while pygame.time.get_ticks() < fin:
                for e in controles.eventos():
                    if e.type == pygame.QUIT: return 'salir'
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None
                    if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): fin = 0
                escena(pygame.time.get_ticks())
                ui['presentar'](); reloj.tick(60)
            return 'ok'

        def apertura():
            """Se abre el tiempo: la estela que cruza, la estrella y el estallido (apertura_<n>.png); del blanco aparece el tunel.
            Cualquier tecla la saltea. None si ESC, 'salir' si se cerro la ventana."""
            if _viaje['apertura'] is None: _viaje['apertura'] = _cuadros_viaje('apertura', 22, W, H)
            cuadros = _viaje['apertura']
            blanco = pygame.Surface((W, H)); blanco.fill((255, 255, 255))
            pasos = [('cuadro', c) for c in cuadros] + [('blanco', None)] * 12 + [('aclara', k / 35) for k in range(36)]
            for clase, valor in pasos:
                for e in controles.eventos():
                    if e.type == pygame.QUIT: return 'salir'
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None
                    if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): return 'ok'
                if clase == 'cuadro':
                    ventana.blit(valor, (0, 0)); ui['presentar'](); reloj.tick(15)   # el original va lento: 15 cuadros por segundo
                    continue
                if clase == 'blanco': ventana.blit(blanco, (0, 0))
                else:                                                    # del blanco aparece el tunel (y vos, la lucecita)
                    escena(pygame.time.get_ticks())
                    blanco.set_alpha(round(255 * (1 - valor))); ventana.blit(blanco, (0, 0)); blanco.set_alpha(None)
                ui['presentar'](); reloj.tick(60)
            return 'ok'

        def caja_de_celebi(texto, cuanto):
            """La caja de dialogo de abajo con el retrato de Celebi y las primeras 'cuanto' letras del texto."""
            caja(ventana, caja_dialogo, 'panel', OSCURO, 2, (220, 220, 220))
            x = caja_dialogo.x + 20
            if retrato: ventana.blit(retrato, (x, caja_dialogo.y + 28)); x += 104
            ventana.blit(fuente(30).render('Celebi', True, (150, 240, 140)), (x, caja_dialogo.y + 10))
            for k, linea in enumerate(ajustar_texto(texto[:cuanto], fuente(30), caja_dialogo.right - x - 40)[:3]):
                ventana.blit(fuente(30).render(linea, True, 'white'), (x, caja_dialogo.y + 46 + k * 28))
            return x

        def decir(texto, opciones_=None):
            """Celebi dice algo (aparece letra por letra; ENTER lo completa y despues sigue).
            Con opciones_ devuelve el indice elegido. None si ESC, 'salir' si se cerro la ventana."""
            inicio, elegido = pygame.time.get_ticks(), 0
            botones = [pygame.Rect(W - 380, caja_dialogo.y - 16 - (len(opciones_ or ()) - k) * 52, 340, 44) for k in range(len(opciones_ or ()))]
            while True:
                ahora = pygame.time.get_ticks()
                cuanto = (ahora - inicio) * VELOCIDAD_TEXTO // 1000
                completo = cuanto >= len(texto)
                for e in controles.eventos():
                    if e.type == pygame.QUIT: return 'salir'
                    elegir = None
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE: return None
                        if opciones_ and completo and e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(opciones_)
                        if opciones_ and completo and e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(opciones_)
                        if e.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE): elegir = elegido
                    if e.type == pygame.MOUSEMOTION and completo:
                        for k, b in enumerate(botones):
                            if b.collidepoint(ui['a_logico'](e.pos)): elegido = k
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: elegir = elegido
                    if elegir is None: continue
                    if not completo: inicio = -10 ** 7; continue                # primero se completa el texto
                    if opciones_: asentir(); return elegir
                    return 0
                escena(ahora)
                caja_de_celebi(texto, cuanto)
                if completo and opciones_:
                    for k, b in enumerate(botones): boton(ventana, b, opciones_[k], k == elegido, 30)
                elif completo and (ahora // 400) % 2:                       # flechita de "segui"
                    pygame.draw.polygon(ventana, 'white', [(caja_dialogo.right - 34, caja_dialogo.bottom - 24), (caja_dialogo.right - 20, caja_dialogo.bottom - 24),
                                                           (caja_dialogo.right - 27, caja_dialogo.bottom - 16)])
                ui['presentar'](); reloj.tick(60)

        def escribir_nombre(pregunta):
            """Caja para escribir tu nombre con el teclado (hasta LARGO_NOMBRE letras). ENTER confirma. None si ESC, 'salir' si se cerro."""
            nombre = ''
            while True:
                ahora = pygame.time.get_ticks()
                for e in controles.eventos():
                    if e.type == pygame.QUIT: return 'salir'
                    if e.type != pygame.KEYDOWN: continue
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key == pygame.K_RETURN and nombre.strip(): asentir(); return nombre.strip()
                    if e.key == pygame.K_BACKSPACE: nombre = nombre[:-1]
                    elif e.unicode and e.unicode.isprintable() and len(nombre) < LARGO_NOMBRE: nombre += e.unicode
                escena(ahora)
                x = caja_de_celebi(pregunta, len(pregunta))
                campo = pygame.Rect(x, caja_dialogo.y + 82, 360, 44)
                caja(ventana, campo, 'boton_elegido', (60, 60, 90), 2)
                texto_ = fuente(32).render(nombre or 'escribí tu nombre', True, 'white' if nombre else (170, 170, 200))
                lugar = texto_.get_rect(midleft=(campo.x + 16, campo.centery))
                ventana.blit(texto_, lugar)
                if nombre and (ahora // 500) % 2: pygame.draw.line(ventana, 'white', (lugar.right + 3, campo.y + 9), (lugar.right + 3, campo.bottom - 9), 2)
                listo = fuente(24).render('ENTER: listo', True, (210, 210, 220))
                ventana.blit(listo, listo.get_rect(midleft=(campo.right + 16, campo.centery)))
                ui['presentar'](); reloj.tick(60)

        # se abre el tiempo, llega Celebi dormido, se despierta y te ve (cada paso puede cortarse con ESC o cerrando la ventana)
        r = apertura()
        if r is None or r == 'salir': return r
        r = esperar(900)                                                 # un momento solo con el tunel y tu lucecita
        if r is None or r == 'salir': return r
        estado['celebi'], estado['llego'] = 'durmiendo', pygame.time.get_ticks()
        r = esperar(2200)                                                # flota dormido
        if r is None or r == 'salir': return r
        estado['celebi'] = 'despertando'
        r = esperar(1400)                                                # se despierta y te mira
        if r is None or r == 'salir': return r
        estado['celebi'] = 'despierto'
        for texto in ('Mmm... ¿y esa lucecita?',
                      'Hace siglos que no encontraba a nadie perdido acá adentro. Estabas dando vueltas en el flujo del tiempo.',
                      'Soy Celebi. Me la paso yendo y viniendo entre épocas... alguien tiene que cuidar el tiempo, ¿no?'):
            r = decir(texto)
            if r is None or r == 'salir': return r
        nombre = escribir_nombre('¿Cómo te llamás?')
        if nombre is None or nombre == 'salir': return nombre
        r = decir(nombre + '. Me lo voy a acordar, y mirá que tengo memoria para rato. ¿Y vos sos...?', ['Chico', 'Chica', 'Prefiero no decirlo'])
        if r is None or r == 'salir': return r
        genero = GENEROS[r]
        for texto in ('El tiempo te desarmó. Pasa, aunque no muy seguido... Por ahora sos una lucecita.',
                      'Cerrá los ojos y acordate de cómo eras. ¿Qué pokemon sos?'):
            r = decir(texto)
            if r is None or r == 'salir': return r
        inicial = elegir_inicial(ui, lambda ahora: fondo_viaje(ui, ahora), '¿Que pokemon sos?')
        if inicial is None or inicial == 'salir': return inicial
        cuerpo = AnimadorPokemon(inicial, pygame.Rect(0, 0, 10, 10), 100)
        cuerpo.cambiar('hop', 0, True) or cuerpo.cambiar('idle', 0, True)   # aparece saltando de alegria
        estado['cuerpo'], estado['forma'] = cuerpo, pygame.time.get_ticks()
        r = esperar(1300)                                                # el destello y tu forma nueva
        if r is None or r == 'salir': return r
        for texto in ('¡Ahí estás! ' + inicial.title() + '. ' + segun_genero(genero, 'Bienvenido de vuelta', 'Bienvenida de vuelta', 'Qué bueno tenerte de vuelta') + ', ' + nombre + '.',
                      'Te cuento rápido: algo está quebrando las eras, una por una, desde la Glacial para acá. Yo solo no llego.',
                      'Vos arreglás cada era y yo te abro el portal a la que sigue. Agarrate, que arrancamos por el hielo.'):
            r = decir(texto)
            if r is None or r == 'salir': return r
        for k in range(40):                                              # destello blanco: entran a la era
            escena(pygame.time.get_ticks())
            velo = pygame.Surface((W, H)); velo.fill((255, 255, 255)); velo.set_alpha(round(255 * k / 39)); ventana.blit(velo, (0, 0))
            ui['presentar'](); reloj.tick(60)
        return {'nombre': nombre, 'genero': genero, 'inicial': inicial}


    def cruzar_portal(ui, era_nombre, pokemon, duracion=2600):
        """Terminaste una era y cruzaste el portal de Celebi: el tunel del tiempo con tu pokemon flotando (Float),
        Celebi adelante guiando y el nombre de la era a la que vas. Termina en un destello blanco. Cualquier tecla lo acorta.
        Devuelve 'salir' si se cerro la ventana."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        reloj = pygame.time.Clock()
        vos = AnimadorPokemon(pokemon, pygame.Rect(0, 0, 10, 10), 100)
        vos.cambiar('float', 0, True) or vos.cambiar('idle', 0, True)
        celebi = AnimadorPokemon('celebi', pygame.Rect(0, 0, 10, 10), 80) if tiene_sprites('celebi') else None
        if celebi: celebi.cambiar('idle', 4, True)                        # mirando para adelante, hacia donde van
        inicio = pygame.time.get_ticks()
        while True:
            ahora = pygame.time.get_ticks()
            t = ahora - inicio
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): inicio = min(inicio, ahora - duracion + 500)   # salta al destello final
            if t >= duracion: return None
            fondo_viaje(ui, ahora)
            if celebi:
                celebi.rect.center = (W // 2, 150 + round(math.sin(ahora / 400) * 10)); celebi.actualizar(); celebi.dibujar(ventana)
            vos.rect.center = (W // 2, 330 + round(math.sin(ahora / 450 + 1) * 12)); vos.actualizar(); vos.dibujar(ventana)
            k = min(1.0, t / 600)                                        # el nombre de la era aparece de a poco
            texto = fuente(64).render(era_nombre, True, 'white')
            sombra = fuente(64).render(era_nombre, True, (20, 30, 80))
            texto.set_alpha(round(255 * k)); sombra.set_alpha(round(200 * k))
            ventana.blit(sombra, sombra.get_rect(center=(W // 2 + 3, H - 113))); ventana.blit(texto, texto.get_rect(center=(W // 2, H - 116)))
            final = (t - (duracion - 500)) / 500
            if final > 0:                                                # destello blanco al llegar
                velo = pygame.Surface((W, H)); velo.fill((255, 255, 255)); velo.set_alpha(round(255 * min(1.0, final))); ventana.blit(velo, (0, 0))
            ui['presentar'](); reloj.tick(60)


    # ---------- dialogos ----------

    def preguntar(ui, texto, opciones_, detalle=None):
        """Caja con una pregunta y opciones. Devuelve el indice elegido (None si ESC)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        fondo = ventana.copy()
        elegido = 0
        reloj = pygame.time.Clock()
        while True:
            cuadro = pygame.Rect(0, 0, 620, 150 + 56 * len(opciones_)); cuadro.center = (W // 2, H // 2)
            botones = [pygame.Rect(cuadro.x + 60, cuadro.y + 120 + i * 56, cuadro.width - 120, 44) for i in range(len(opciones_))]
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(opciones_)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(opciones_)
                    if e.key in (pygame.K_RETURN, pygame.K_e): return elegido
                if e.type == pygame.MOUSEMOTION:
                    for i, b in enumerate(botones):
                        if b.collidepoint(ui['a_logico'](e.pos)): elegido = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, b in enumerate(botones):
                        if b.collidepoint(ui['a_logico'](e.pos)): return i
            ventana.blit(fondo, (0, 0))
            velo = pygame.Surface((W, H), pygame.SRCALPHA); velo.fill((0, 0, 0, 150)); ventana.blit(velo, (0, 0))
            caja(ventana, cuadro, 'panel', OSCURO, 2, (220, 220, 220))
            for i, linea in enumerate(ajustar_texto(texto, fuente(32), cuadro.width - 60)[:2]):
                ventana.blit(fuente(32).render(linea, True, 'white'), (cuadro.x + 30, cuadro.y + 22 + i * 30))
            if detalle: ventana.blit(fuente(22).render(detalle, True, (200, 200, 200)), (cuadro.x + 30, cuadro.y + 88))
            for i, b in enumerate(botones): boton(ventana, b, opciones_[i], i == elegido, 30)
            ui['presentar'](); reloj.tick(60)


    # ---------- ajustes ----------

    def ajustes(ui):
        """Ajustes con el formato de los otros menus. El codigo Konami abre los trucos."""
        ventana, H, config = ui['ventana'], ui['H'], ui['config']
        modos = ['mouse', 'teclas', 'mixto']
        filas = ['volumen', 'modo', 'resolucion', 'pantalla_completa', 'estilo_equipo', 'hall', 'controles', 'glosario', 'volver']
        textos = {'volumen': 'Sonido', 'modo': 'Combate', 'resolucion': 'Resolucion', 'pantalla_completa': 'Pantalla completa',
                  'estilo_equipo': 'Menu de equipo', 'hall': 'Hall', 'controles': 'Controles', 'glosario': 'Glosario', 'volver': 'Volver'}
        ayudas = {'modo': {'mouse': 'Apuntas con el mouse', 'teclas': 'Atacas hacia donde caminaste por ultima vez', 'mixto': 'Teclas hasta que moves el mouse'},
                  'estilo_equipo': {'clasico': 'Lista como en los juegos de Pokemon', 'escenario': 'Tus pokemon parados en un escenario (se duermen si esperas)'},
                  'hall': {'auto': 'Donde aparece Celebi hasta que derrotes una era; despues, el lugar atemporal',
                           'atemporal': 'Siempre el lugar atemporal: una isla flotando en el tiempo que cambia segun la era',
                           'celebi': 'Siempre el bosque donde aparece Celebi'}}
        NOMBRE_HALL = {'auto': 'Automatico', 'atemporal': 'Atemporal', 'celebi': 'Celebi'}
        elegido = 0
        reloj = pygame.time.Clock()

        def cambiar(clave, paso):
            """Cambia el valor de una opcion de ajustes hacia un lado (-1 o +1) y lo aplica."""
            if clave == 'volumen': config['volumen'] = max(0, min(100, config['volumen'] + 10 * paso)); ui['aplicar_volumen']()
            elif clave == 'modo': config['modo'] = modos[(modos.index(config['modo']) + paso) % len(modos)]
            elif clave == 'resolucion':
                lista = opciones.RESOLUCIONES
                config['resolucion'] = lista[(lista.index(config['resolucion']) + paso) % len(lista)] if config['resolucion'] in lista else lista[0]
                ui['aplicar_pantalla']()
            elif clave == 'pantalla_completa': config['pantalla_completa'] = not config['pantalla_completa']; ui['aplicar_pantalla']()
            elif clave == 'estilo_equipo':
                lista = opciones.ESTILOS_EQUIPO
                config['estilo_equipo'] = lista[(lista.index(config['estilo_equipo']) + paso) % len(lista)]
            elif clave == 'hall':
                lista = opciones.HALLS
                config['hall'] = lista[(lista.index(config['hall']) + paso) % len(lista)] if config.get('hall') in lista else lista[0]

        while True:
            botones = [pygame.Rect(MARGEN_X, CONTENIDO_Y + i * 50, 520, 42) for i in range(len(filas))]   # (mas juntos: con el Hall son 9 filas)
            accion = None
            for e in controles.eventos():
                if e.type == pygame.QUIT: opciones.guardar(config); return 'salir'
                if e.type == controles.KONAMI:
                    if trucos(ui) == 'salir': return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: opciones.guardar(config); return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(filas)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(filas)
                    if e.key in (pygame.K_LEFT, pygame.K_RIGHT): cambiar(filas[elegido], 1 if e.key == pygame.K_RIGHT else -1)
                    if e.key in (pygame.K_RETURN, pygame.K_e): accion = filas[elegido]
                if e.type == pygame.MOUSEMOTION:
                    for i, b in enumerate(botones):
                        if b.collidepoint(ui['a_logico'](e.pos)): elegido = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, b in enumerate(botones):
                        if b.collidepoint(ui['a_logico'](e.pos)): elegido = i; accion = filas[i]
            if accion == 'volver': opciones.guardar(config); return None
            if accion == 'controles' and menu_controles(ui) == 'salir': return 'salir'
            if accion == 'glosario' and glosario(ui) == 'salir': return 'salir'
            if accion in ('modo', 'resolucion', 'pantalla_completa', 'estilo_equipo', 'hall', 'volumen'): cambiar(accion, 1)
            fondo(ventana)
            titulo(ventana, 'Ajustes')
            valores = {'volumen': config['volumen'], 'modo': config['modo'].title(), 'resolucion': config['resolucion'],
                       'pantalla_completa': 'Si' if config['pantalla_completa'] else 'No', 'estilo_equipo': config['estilo_equipo'].title(),
                       'hall': NOMBRE_HALL.get(config.get('hall'), 'Automatico')}
            for i, clave in enumerate(filas): boton(ventana, botones[i], textos[clave], i == elegido, 32, valores.get(clave))
            clave = filas[elegido]
            ayuda = ayudas.get(clave, {}).get(config.get(clave)) if clave in ayudas else None
            info = pygame.Rect(600, CONTENIDO_Y, ui['W'] - 600 - MARGEN_X, 120)   # al costado: que hace la opcion elegida
            if clave == 'volumen' or ayuda:
                caja(ventana, info, 'panel', PANEL)
                ventana.blit(fuente(30).render(textos[clave], True, (255, 236, 120)), (info.x + 16, info.y + 10))
            if clave == 'volumen':
                for i in range(10): pygame.draw.rect(ventana, 'white' if i < config['volumen'] // 10 else (90, 90, 90), (info.x + 16 + i * 30, info.y + 62, 24, 18))
            if ayuda:
                for k, linea in enumerate(ajustar_texto(ayuda, fuente(24), info.width - 32)[:3]): ventana.blit(fuente(24).render(linea, True, 'white'), (info.x + 16, info.y + 52 + k * 20))
            pie(ventana, 'Flechas: elegir y cambiar   ENTER: entrar   ESC: volver')
            ui['presentar'](); reloj.tick(60)


    def menu_controles(ui):
        """Teclas configurables: Teclado / Control, 3 perfiles de cada uno, restaurar preset."""
        ventana, W, H, config = ui['ventana'], ui['W'], ui['H'], ui['config']
        c = config['controles']
        dispositivo, elegido, scroll = 'teclado', 0, 0
        reloj = pygame.time.Clock()
        while True:
            filas = ['dispositivo', 'perfil'] + [a for a, _ in controles.ACCIONES] + ['restaurar', 'volver']
            nombres = dict(controles.ACCIONES)
            perfil_actual = c[dispositivo][c['perfil_' + dispositivo]]
            alto = 40
            visibles = (H - 170) // alto
            scroll = max(0, min(scroll, len(filas) - visibles))
            if elegido < scroll: scroll = elegido
            if elegido >= scroll + visibles: scroll = elegido - visibles + 1
            botones = {i: pygame.Rect(MARGEN_X, CONTENIDO_Y + (i - scroll) * alto, 680, alto - 6) for i in range(scroll, min(len(filas), scroll + visibles))}
            accion = None
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: opciones.guardar(config); return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(filas)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(filas)
                    if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        paso = 1 if e.key == pygame.K_RIGHT else -1
                        if filas[elegido] == 'dispositivo': dispositivo = 'control' if dispositivo == 'teclado' else 'teclado'
                        if filas[elegido] == 'perfil': c['perfil_' + dispositivo] = (c['perfil_' + dispositivo] + paso) % 3
                    if e.key == pygame.K_RETURN: accion = filas[elegido]
                if e.type == pygame.MOUSEWHEEL: scroll = max(0, scroll - e.y)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, b in botones.items():
                        if b.collidepoint(ui['a_logico'](e.pos)): elegido = i; accion = filas[i]
            if accion == 'volver': opciones.guardar(config); return None
            if accion == 'dispositivo': dispositivo = 'control' if dispositivo == 'teclado' else 'teclado'
            if accion == 'perfil': c['perfil_' + dispositivo] = (c['perfil_' + dispositivo] + 1) % 3
            if accion == 'restaurar':
                if preguntar(ui, 'Restaurar el perfil ' + str(c['perfil_' + dispositivo] + 1) + ' de ' + dispositivo + '?', ['Si', 'No']) == 0:
                    controles.restaurar(dispositivo, c['perfil_' + dispositivo])
            if accion in nombres:
                def dibujar_espera():
                    """Pantalla de 'apreta una tecla' mientras se reasigna un control."""
                    velo = pygame.Surface((W, H), pygame.SRCALPHA); velo.fill((0, 0, 0, 170)); ventana.blit(velo, (0, 0))
                    t = fuente(40).render(('Apreta una tecla' if dispositivo == 'teclado' else 'Apreta un boton') + ' para: ' + nombres[accion], True, 'white')
                    ventana.blit(t, t.get_rect(center=(W // 2, H // 2)))
                    ventana.blit(fuente(24).render('ESC para cancelar', True, (200, 200, 200)), (W // 2 - 70, H // 2 + 40))
                nueva = controles.esperar_entrada(dispositivo, ui['presentar'], dibujar_espera)
                if nueva: perfil_actual[accion] = nueva
            fondo(ventana)
            titulo(ventana, 'Controles')
            if dispositivo == 'control' and not controles.hay_control():
                aviso = fuente(24).render('(no hay ningún control conectado)', True, TINTA)
                ventana.blit(aviso, aviso.get_rect(topright=(ui['W'] - MARGEN_X, 40)))
            for i, b in botones.items():
                clave = filas[i]
                if clave == 'dispositivo': boton(ventana, b, 'Dispositivo', i == elegido, 28, dispositivo.title())
                elif clave == 'perfil': boton(ventana, b, 'Perfil', i == elegido, 28, c['perfil_' + dispositivo] + 1)
                elif clave == 'restaurar': boton(ventana, b, 'Restaurar preset de este perfil', i == elegido, 28)
                elif clave == 'volver': boton(ventana, b, 'Volver', i == elegido, 28)
                else:
                    caja(ventana, b, 'boton_elegido' if i == elegido else 'boton', OSCURO, 2)
                    t_ = fuente(28).render(nombres[clave], True, 'white'); ventana.blit(t_, t_.get_rect(midleft=(b.x + 16, b.centery)))
                    tecla = fuente(28).render(str(perfil_actual.get(clave, '-')).upper(), True, (240, 220, 120))
                    ventana.blit(tecla, tecla.get_rect(midright=(b.right - 16, b.centery)))
                    if i == elegido: dibujar_esquinas(ventana, b, margen=5, largo=12)
            pie(ventana, 'ENTER sobre una acción: cambiarla   izq/der: dispositivo y perfil   ESC: volver')
            ui['presentar'](); reloj.tick(60)


    TRUCOS = [('todas_mt', 'Tener todas las MT'), ('mt_infinitas', 'Las MT no se gastan'), ('vida_infinita', 'Vida infinita'),
              ('sin_enfriamiento', 'Sin tiempo de recarga'), ('monedas_infinitas', 'Monedas infinitas'), ('golpe_letal', 'Un golpe mata'),
              ('subir_niveles', 'Subir 5 niveles al equipo (al volver al juego)')]


    def trucos(ui):
        """Menu secreto (codigo Konami en ajustes o en pausa)."""
        ventana, H, t = ui['ventana'], ui['H'], ui['config']['trucos']
        elegido = 0
        reloj = pygame.time.Clock()
        while True:
            botones = [pygame.Rect(100, 130 + i * 56, 640, 46) for i in range(len(TRUCOS) + 1)]
            accion = None
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(botones)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(botones)
                    if e.key in (pygame.K_RETURN, pygame.K_e, pygame.K_LEFT, pygame.K_RIGHT): accion = elegido
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, b in enumerate(botones):
                        if b.collidepoint(ui['a_logico'](e.pos)): accion = i
            if accion is not None:
                if accion == len(TRUCOS): return None
                clave = TRUCOS[accion][0]
                t[clave] = (t.get(clave, 0) + 1) if clave == 'subir_niveles' else not t.get(clave)
            ventana.fill((70, 40, 90))
            titulo(ventana, 'Menu debug', color=(250, 220, 120))
            for i, (clave, texto) in enumerate(TRUCOS):
                valor = ('x' + str(t.get(clave, 0))) if clave == 'subir_niveles' else ('Si' if t.get(clave) else 'No')
                boton(ventana, botones[i], texto, i == elegido, 28, valor)
            boton(ventana, botones[-1], 'Volver', elegido == len(TRUCOS), 28)
            pie(ventana, 'Truquitos de prueba: no se guardan')
            ui['presentar'](); reloj.tick(60)


    # ---------- glosario ----------

    def _efecto_txt(ef):
        """Texto de un efecto del entorno para el glosario ('daño x1.3', 'resbala'...)."""
        partes = []
        for k, v in ef.items():
            if k == 'velocidad': partes.append(('+' if v > 1 else '') + str(round((v - 1) * 100)) + '% velocidad')
            elif k == 'daño': partes.append('+' + str(round((v - 1) * 100)) + '% daño')
            elif k == 'defensa': partes.append(str(round((1 - v) * 100)) + '% menos daño recibido')
            elif k == 'enfriamiento': partes.append('recargas ' + str(round((1 - v) * 100)) + '% mas rapidas')
            elif k == 'regen': partes.append('energia x' + str(v))
            elif k == 'tick': partes.append('te lastima')
            elif k == 'oculto': partes.append('quedas escondido')
            elif k == 'resbala': partes.append('resbalas')
            elif k == 'sprint_gratis': partes.append('correr no gasta energia')
            elif k == 'empuje': partes.append('te lleva')
        return ', '.join(partes) or 'no le afecta (inmune)'


    def secciones_glosario(config):
        """Textos del glosario armados con los mismos datos que usa el juego (asi no quedan desactualizados)."""
        perfil = controles.perfil('teclado')
        tecla = lambda a: str(perfil.get(a, '-')).upper()
        s = {}
        s['Controles'] = [nombre + ': ' + tecla(a) for a, nombre in controles.ACCIONES] + ['', 'Todo se puede cambiar en Ajustes > Controles (3 perfiles de teclado y 3 de control).']
        s['Combate'] = [
            'Cuerpo a cuerpo (' + tecla('basico1') + '): combo de 3 golpes. Apreta de nuevo enseguida para encadenar; el 3ro es un remate que barre, empuja lejos e interrumpe.',
            'Cada golpe que conecta te devuelve energia y le saca espera a tus especiales: pelear de cerca rinde.',
            'Golpe en carrera: si atacas corriendo, el primer golpe pega mas y llega mas lejos.',
            'Parry: golpea justo cuando un enemigo te va a pegar (su aviso brilla amarillo con un !). Lo aturde, recibe el doble, recuperas energia, vida y especiales. Tambien devuelve las balas.',
            'Si fallas el parry tenes que esperar un poquito para intentarlo de nuevo: apretar sin parar no sirve.',
            'Esquivar (' + tecla('esquivar') + '): salto corto hacia donde caminas (quieto: para atras), invulnerable un instante. Gasta energia.',
            'Esquive perfecto: si te iban a pegar mientras esquivabas, recuperas energia y tu proximo golpe es un contraataque (x1.8).',
            'Ataque a distancia (' + tecla('basico2') + '): mas debil y tarda mas en recargar, pero es seguro.',
            'Especiales (' + tecla('especial1') + ' y ' + tecla('especial2') + '): dependen del rol del pokemon (atacante, tanque, estratega o velocista).',
            'Asistencias (' + tecla('asist1') + ' y ' + tecla('asist2') + '): las tira un pokemon de la banca; tardan mucho en recargar.',
            'Sinergia: los de la banca le dan un bonus pasivo al que esta peleando. Se elige en la ficha de cada pokemon.',
            'Cambiar de pokemon (' + tecla('poke1') + ' ' + tecla('poke2') + ' ' + tecla('poke3') + '): tiene una espera de 2 s. Si cambias en el agua a uno que no nada, nada solo hasta la orilla.',
            'Tipos: un ataque super eficaz hace x2, uno poco eficaz x0.5 y si el otro es inmune casi no le hace nada.',
            'Correr (' + tecla('correr') + ') gasta la barra azul de energia; arrancas con un pique y se recarga sola.',
            'Congelado: solo te congela un golpe fuerte de hielo (un rayo de Regice, un pokemon de hielo que te pega de lleno). Pisar hielo solo resbala.',
            'Al limpiar una sala todo el equipo recupera un poco de vida. Golpear a uno dormido lo despierta pero pega x1.5.',
            'Los enemigos avisan antes de atacar: anillo rojo = golpe, linea con mira = disparo, linea naranja = embestida.',
            'Escondido en hierba o sombra (si tu tipo puede) los enemigos casi no te ven.',
            'Los enemigos te rodean, esquivan tus disparos, los tiradores se mueven de costado y tiran rafagas, y con poca vida se enfurecen.']
        s['Estilo'] = [
            'El medidor de ESTILO (arriba a la derecha) va de D a S. Cuanto mas alto, mas pegas: C +5%, B +10%, A +17%, S +25%.',
            'Sale de 5 cosas: el RITMO (golpes seguidos, con menos de 0,7 s entre uno y otro, rinden todo), el MOVIMIENTO (moverte peleando),',
            'los COMBOS (terminar los 3 golpes), los RELEVOS (cambiar de pokemon peleando y pegar con el que entra: ese golpe pega x1,4)',
            'y las SINERGIAS (usar las asistencias F / G). Matar da poco.',
            'Variá: si repetis siempre el mismo ataque, cada golpe da cada vez menos (sale el aviso "variá tus ataques").',
            'Baja si te pegan y si te quedas quieto sin pelear. Cuando no quedan enemigos, deja de sumar.',
            'Racha: bajas seguidas en menos de 3 segundos dan monedas extra.',
            'Al limpiar la sala te ponen nota (S, A, B, C, D) sobre 100: ritmo 25, movimiento 20, combos 20, relevos 15 y sinergias 20.',
            'S y A dan monedas, experiencia y a veces un objeto (baya, llave o caramelo). En las salas de desafio (★), el doble.']
        tipos = sorted({t for tabla in (entorno.PISADAS, ) for terreno in tabla.values() for t in terreno if t != 'todos'} |
                       {t for _, (_, por_tipo) in entorno.AURAS.items() for t in por_tipo} | {t for _, t in entorno.REACCIONES})
        lineas = []
        for t in tipos:
            lineas.append('[' + t.upper() + ']')
            for terreno, tabla in entorno.PISADAS.items():
                linea = '  En ' + ('cintas' if terreno.startswith('cinta') else terreno.replace('_', ' ')) + ': ' + _efecto_txt(tabla[t]) if t in tabla else None
                if linea and linea not in lineas: lineas.append(linea)
            for maquina, (_, por_tipo) in entorno.AURAS.items():
                if t in por_tipo: lineas.append('  Cerca de ' + maquina.replace('_', ' ') + ': ' + _efecto_txt(por_tipo[t]))
            for (terreno, tipo), accion in entorno.REACCIONES.items():
                if tipo == t:
                    hace = {'convertir': 'lo convierte en ' + str(accion[1] if len(accion) > 1 else '').replace('_', ' '), 'electrificar': 'lo electrifica',
                            'encender': 'lo prende fuego', 'apagar': 'lo apaga', 'invertir': 'la da vuelta', 'pulso': 'lo descarga sobre los enemigos',
                            'cortocircuito': 'lo hace explotar'}[accion[0]]
                    lineas.append('  Sus ataques sobre ' + terreno.replace('_', ' ') + ': ' + hace)
        s['Tipos y entorno'] = lineas
        s['Clima'] = ['Cada sala tiene su clima y cambia de a poco de una sala a la otra (nunca de lluvia a sol de golpe).',
                      'Algunos movimientos traen un clima por 15 segundos (hidrobomba lluvia, llamarada sol, ventisca granizo...).', ''] + \
            [c['nombre'] + ': ' + (', '.join(t + ' x' + str(v) for t, v in c['mult'].items()) or 'sin efecto') for c in entorno.CLIMAS.values()]
        s['Objetos del mundo'] = ['Muchos objetos se rompen. El daño depende del material y del tipo del ataque:'] + \
            ['  ' + mat + ': ' + ', '.join(t + ' x' + str(v) for t, v in tabla.items()) for mat, tabla in entorno.MATERIALES.items()] + \
            ['', 'Los que tienen un punto rojo explotan (y encadenan). Lucha y psiquico empujan cajas y barriles.',
             'Lo que arde se rompe de un golpe de fuego. A veces sueltan monedas.']
        s['Tienda'] = ['Aparece cada 5 a 10 salas. Riolu vende objetos en el mostrador: acercate a una vitrina y apretá ' + tecla('interactuar') + '.',
                       'Cambia de nombre segun la era (' + ', '.join(e['tienda'] for e in datos.mundos.ERAS) + '), pero siempre atiende Riolu.',
                       'Curaciones: Chikorita rosa tiene su mostrador abajo a la derecha. Por monedas cura al que pelea o cura y revive a todo el equipo.',
                       'Siempre hay una Llave del Tesoro a la venta. Tambien cuida tu reserva: los cambios con la reserva se hacen aca.',
                       'Los objetos que dicen "lo lleva un pokemon" se equipan desde su ficha (hasta 2 cada uno) y solo cuentan mientras pelea.',
                       'Los que dicen "todo el equipo" valen para todos.',
                       'MT de combate: van en cualquier casilla (E, Q, Shift o R). MT especiales: solo en Shift o R.', ''] + \
            [it['nombre'] + ' (' + str(it['precio']) + ' $): ' + it['desc'] for k, it in tienda.ITEMS.items() if not it.get('mt')]
        s['Niveles y stats'] = [
            'Ganas experiencia derrotando pokemon, rompiendo cosas, completando salas y comprando. Los de la banca ganan la mitad.',
            'Cada nivel da ' + str(progreso.PUNTOS_POR_NIVEL) + ' punto de esfuerzo (EV): lo pones en el stat que quieras desde el menu de equipo.',
            'Cada punto son ' + str(progreso.EV_POR_PUNTO) + ' EV. Maximo ' + str(progreso.EV_MAX_STAT) + ' por stat y ' + str(progreso.EV_MAX) + ' en total (la ficha muestra cuanto llevas).',
            'Cada pokemon tiene IVs (0 a 31) al azar: dos del mismo pokemon no son iguales.',
            'PS = vida. Ataque = golpes y embestidas. At. Esp. = disparos y ataques de area. Defensas = menos daño recibido. Velocidad = caminar mas rapido.',
            'Los enemigos tambien tienen nivel: cuanto mas avanzas, mas fuertes.']
        s['Evoluciones'] = ['La mayoria evoluciona al llegar a un nivel. Otros con una piedra (Piedra Trueno, Piedra Alba...).',
                            'Los que en los juegos evolucionan por intercambio usan el Cordon Union.',
                            'Pichu y Riolu evolucionan por amistad: sube cada sala que pasan en tu equipo.',
                            'Peleando, el que puede evolucionar muestra EVO en el HUD. Con la sala limpia aparece el aviso abajo:',
                            'mantené ' + tecla('evolucionar') + ' y evoluciona ahi mismo. Tambien se puede desde el menu de equipo (' + tecla('equipo') + ').']
        s['Amistad'] = ['Los pokemon no se capturan: a veces uno que derrotaste se queda con corazones porque quiere unirse a vos.',
                        'Acercate y apreta ' + tecla('interactuar') + ' para hablarle. Con el equipo lleno (3) va a la reserva (hasta 3; si esta llena, elegis a quien dejar ir).',
                        'Los cambios entre el equipo y la reserva solo se hacen en la tienda.',
                        'Es mas probable con los pokemon comunes, si sos de mas nivel y con el Lazo Amistad. Los jefes no se unen.',
                        'Si te vas de la sala sin hablarle, se va.',
                        '[Uno por sala] Cuando alguien quiere unirse, en el resto de esa sala ya nadie mas se ofrece, y la sala siguiente es de espera.',
                        'Excepcion: a los que les bailaste les queda una chance (la mitad) de querer unirse igual: bailando podes amigar a mas de uno.',
                        '[Naturaleza] Cada pokemon nace con una de las 25 de los juegos: sube un 10% un stat y baja otro. Tambien dice que tan facil se amiga:',
                        'las de buen caracter (Afable, Docil, Amable, Alegre...) se amigan facil; las de mal caracter (Huraña, Grosera, Agitada...) cuestan.',
                        '[Baile] Con ' + tecla('bailar') + ' bailas (gasta energia, espera de 6 s). A los que tienen poca vida los encariña: corazoncitos arriba de la cabeza,',
                        'y mas chance de que quieran unirse cuando los derrotes (hasta 3 bailes). A los sanos a veces los confunde: caminan sin rumbo y le pegan a los suyos.',
                        '[Minimo de amigos] Desde la segunda sala de la Era Glacial, el primero que derrotes quiere unirse seguro. En cada era hay al menos 2 que quieren',
                        '(la 1ra antes de la sala ' + str(progreso.GARANTIA_AMISTAD[0] + 1) + ', la 2da antes de la ' + str(progreso.GARANTIA_AMISTAD[1] + 1) + '), y cada sala sin amigos hace la proxima un poco mas facil.']
        s['Salas y eras'] = ['5 eras de 30 salas: Glacial, Piedra, Metales, Media y Moderna. Al final, El Origen: Regigigas y Arceus.',
                             'Semijefe en la sala 15 y el Regi de la era en la 30. Las puertas muestran que hay detras.',
                             'Limpia la sala para que aparezca la llave; con la llave se abren las puertas.',
                             'La vida no se recupera sola: al limpiar una sala el equipo recupera un 12%.',
                             'Con la sala completada podes volver por la puerta por la que entraste; las salas hechas quedan hechas.',
                             'Algunas puertas dicen TESORO (llave): con una Llave del Tesoro entras a una sala con 3 premios y te llevas uno',
                             '(Caramelos Raros o mejoras para todo el equipo: Proteina, Hierro, Carburante, Calcio, Zinc, Mas PS).',
                             'Las puertas con ★ desafio llevan a salas con 50% mas enemigos y mejor premio.',
                             'Romper cosas a veces suelta bayas (curan), llaves o caramelos: explorar rinde.']
        s['Partidas'] = ['Hay 3 partidas guardadas (Jugar > elegis una ranura).',
                         'Se guarda sola al entrar a cada sala, al completarla y al comprar: equipo, niveles, experiencia, EV, MT, objetos, monedas y por donde ibas.',
                         'Si cae todo el equipo, Celebi te lleva al hall: el viaje se pierde, pero tus amigos se quedan.']
        s['Estados y curas'] = [
            'Algunos golpes enemigos te dejan un estado (los de veneno envenenan, fuego quema, eléctrico paraliza, psíquico y fantasma confunden),',
            'y algunos pokemon tienen los suyos (el chillido de Zubat aturde, las esporas de Foongus envenenan, Diglett te entierra...).',
            '[Envenenado] pierde vida de a poco (nunca te deja en 0). [Quemado] pierde vida y pega 20% menos. [Paralizado] más lento y a veces',
            'no le sale el especial. [Dormido] no se mueve ni ataca hasta que le pegan. [Confundido] camina al revés. [Aturdido] un instante quieto.',
            'Cada pokemon tiene sus propios estados: si cambiás, el que entra no los trae. Los de veneno y acero no se envenenan, los de fuego no se queman...',
            'Curarse: con ' + tecla('curar') + ' usás sola la curación que conviene (primero el estado, después la vida). Desde la mochila elegís cuál y en quién.',
            'Chikorita rosa vende todas las curaciones. La Poción Máxima no se vende: Celebi te da una al empezar cada viaje y en cada era nueva (solo se lleva una).',
            ''] + [it['nombre'] + ' (' + (str(it['precio']) + ' $' if it['precio'] else 'de Celebi') + '): ' + it['desc'] for k, it in tienda.ITEMS.items() if it.get('curativo')]
        s['Pokemon únicos'] = ['Cada línea de la expansión (y Chikorita) tiene algo propio, sacado de su Pokédex: una pasiva o un especial en R.',
                               'Los especiales fuertes tienen mucha espera (Predicción 40 s, Control mental 25 s, Ilusión 20 s).', ''] + \
            [mecanicas.MECANICAS[cl]['nombre'] + ' (' + ', '.join(e.replace('_', ' ').title() for e, (c_, _) in mecanicas.LINEAS.items() if c_ == cl) + '): ' + mecanicas.MECANICAS[cl]['desc']
             for cl in dict.fromkeys(c_ for c_, _ in mecanicas.LINEAS.values())] + [''] + \
            [v['nombre'] + ' (' + e.title() + ', en R): ' + v['desc'] for e, v in mecanicas.ESPECIE_ESPECIAL.items()] + ['', '[Como enemigos]'] + list(mecanicas.ENEMIGO_TXT.values())
        s['Hall'] = ['Es a donde volves al perder. Tus amigos pasean ahi: acercate y apreta ' + tecla('interactuar') + ' para hablarles.',
                     'Hablando con un amigo elegis si viene al proximo viaje (hasta 3 en el equipo).',
                     'Cada viaje empieza de cero: todos vuelven a su primera forma y al nivel ' + str(progreso.NIVEL_INICIAL) + ', con sus IV y su amistad.',
                     'El portal del norte (VIAJE TEMPORAL) te lleva otra vez a la Era Glacial. Celebi te cuenta como vas.',
                     'Ajustes > Hall: Automatico (el claro de Celebi hasta que derrotes una era, despues el lugar atemporal), siempre Atemporal o siempre Celebi.']
        return s


    def glosario(ui):
        """Glosario: secciones con terrenos, maquinas, climas, tipos y controles, con scroll."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        secciones = secciones_glosario(ui['config'])
        nombres = list(secciones)
        elegido, scroll = 0, 0
        reloj = pygame.time.Clock()
        panel = pygame.Rect(320, CONTENIDO_Y, W - 320 - MARGEN_X, H - CONTENIDO_Y - 44)
        while True:
            lineas = []
            for linea in secciones[nombres[elegido]]: lineas += ajustar_texto(linea, fuente(24), panel.width - 30) or ['']
            maximo = max(0, len(lineas) * 22 - panel.height + 30)
            paso = min(44, (H - CONTENIDO_Y - 44) // len(nombres))            # que entren todas las secciones arriba del pie
            botones = [pygame.Rect(MARGEN_X, CONTENIDO_Y + i * paso, 250, paso - 6) for i in range(len(nombres))]
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(nombres); scroll = 0
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(nombres); scroll = 0
                    if e.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN): scroll = min(maximo, scroll + 120)
                    if e.key in (pygame.K_LEFT, pygame.K_PAGEUP): scroll = max(0, scroll - 120)
                if e.type == pygame.MOUSEWHEEL: scroll = max(0, min(maximo, scroll - e.y * 40))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, b in enumerate(botones):
                        if b.collidepoint(ui['a_logico'](e.pos)): elegido = i; scroll = 0
            fondo(ventana)
            titulo(ventana, 'Glosario')
            for i, b in enumerate(botones): boton(ventana, b, nombres[i], i == elegido, 26)
            caja(ventana, panel, 'panel', PANEL)
            ventana.set_clip(panel.inflate(-10, -10))
            for i, linea in enumerate(lineas):
                y = panel.y + 14 + i * 22 - scroll
                if panel.y - 20 < y < panel.bottom:
                    color = (240, 200, 80) if linea.startswith('[') else (235, 235, 235)
                    ventana.blit(fuente(24).render(linea, True, color), (panel.x + 15, y))
            ventana.set_clip(None)
            pie(ventana, 'arriba/abajo: sección   izq/der o rueda: desplazar   ESC: volver')
            ui['presentar'](); reloj.tick(60)


    # ---------- partidas guardadas ----------

    def elegir_partida(ui, resumenes):
        """Las 3 ranuras de guardado. Devuelve ('continuar' | 'nueva', ranura), None si volves o 'salir'."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        elegido, reloj = 0, pygame.time.Clock()
        abierto = pygame.time.get_ticks()
        while True:
            cajas = [pygame.Rect(MARGEN_X, CONTENIDO_Y + 6 + k * 144, W - 2 * MARGEN_X - 12, 126) for k in range(len(resumenes))]
            accion = None
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(cajas)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(cajas)
                    if e.key in (pygame.K_RETURN, pygame.K_e): accion = elegido
                    if e.key in (pygame.K_1, pygame.K_2, pygame.K_3): accion = e.key - pygame.K_1
                if e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    for k, r in enumerate(cajas):
                        if r.collidepoint(ui['a_logico'](e.pos)):
                            elegido = k
                            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: accion = k
            if accion is not None and accion < len(resumenes):
                ranura, resumen = accion + 1, resumenes[accion]
                if not resumen: return 'nueva', ranura
                r = preguntar(ui, 'Partida ' + str(ranura) + ': ' + ('en el hall' if resumen.get('hall') else resumen.get('era', '') + ', sala ' + str(resumen.get('sala', '?'))),
                              ['Continuar', 'Empezar de nuevo (borra esta)', 'Borrar', 'Cancelar'])
                if r == 'salir': return 'salir'
                if r == 0: return 'continuar', ranura
                if r == 1 and preguntar(ui, 'Seguro? Se pierde la partida ' + str(ranura), ['Si, empezar de nuevo', 'No']) == 0: return 'nueva', ranura
                if r == 2 and preguntar(ui, 'Seguro que borras la partida ' + str(ranura) + '?', ['Si, borrar', 'No']) == 0:
                    partidas.borrar(ranura); resumenes[accion] = None
            fondo(ventana)
            t = pygame.time.get_ticks() - abierto
            titulo(ventana, 'Partidas')
            for k, r in enumerate(cajas):
                r = r.move(-round((1 - aparecer(t, k * 80)) * (r.right + 40)) + (12 if k == elegido else 0), 0)
                resumen = resumenes[k]
                panel_flecha(ventana, r, (2 if resumen else 0, 1 if k == elegido else 0))
                ventana.blit(fuente(34).render(resumen['nombre'] if resumen and resumen.get('nombre') else 'Partida ' + str(k + 1), True, 'white'), (r.x + 24, r.y + 12))
                if not resumen:
                    ventana.blit(fuente(30).render('Vacía: empezar una partida nueva', True, (200, 210, 225)), (r.x + 24, r.y + 66))
                    if k == elegido: dibujar_esquinas(ventana, r, margen=5, largo=12)
                    continue
                donde = 'En el hall' if resumen.get('hall') else resumen.get('era', '') + ' - sala ' + str(resumen.get('sala', '?')) + '/' + str(resumen.get('salas', '?'))
                amigos = ('   ' + str(resumen['amigos']) + ' amigos') if resumen.get('amigos') else ''
                info_ = fuente(24).render(donde + '   $ ' + str(resumen.get('monedas', 0)) + amigos, True, (240, 220, 120))
                ventana.blit(info_, info_.get_rect(topright=(r.right - 30, r.y + 16)))
                fecha_ = fuente(22).render('guardada ' + str(resumen.get('fecha', '')), True, (200, 200, 210))
                ventana.blit(fecha_, fecha_.get_rect(topright=(r.right - 30, r.y + 36)))
                x = r.x + 24
                for nombre, nivel in resumen.get('equipo', []):
                    img = ui['retrato'](nombre, 44)
                    if img: ventana.blit(img, (x, r.y + 62))
                    nom_ = fuente(24).render(nombre.replace('_', ' ').title() + ' Nv ' + str(nivel), True, 'white')
                    ventana.blit(nom_, nom_.get_rect(midleft=(x + 52, r.y + 84)))
                    x += 250
                if k == elegido: dibujar_esquinas(ventana, r, margen=5, largo=12)
            pie(ventana, 'ENTER o clic: elegir   ESC: volver   (se guarda sola al entrar a cada sala y al completarla)')
            ui['presentar'](); reloj.tick(60)


    # ---------- ataques: todos los movimientos del juego y que hacen ----------

    def ataques(ui):
        """Todos los ataques del juego por categoria (basicos, especiales, asistencias, MT): izq/der cambia de categoria,
        arriba/abajo elige y a la derecha se ve que hace, sus numeros y quienes lo usan."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        catalogo = datos.catalogo_ataques()
        categorias = list(catalogo)
        cat, elegido, reloj = 0, 0, pygame.time.Clock()
        abierto = pygame.time.get_ticks()
        alto, lista = 30, pygame.Rect(MARGEN_X, CONTENIDO_Y + 42, 330, H - CONTENIDO_Y - 42 - 44)
        visibles = lista.height // alto
        while True:
            filas = catalogo[categorias[cat]]
            elegido = max(0, min(elegido, len(filas) - 1))
            inicio = max(0, min(elegido - visibles // 2, len(filas) - visibles))
            pestañas = []
            x = 30
            for k, nombre in enumerate(categorias):
                ancho = fuente(24).size(nombre)[0] + 34
                pestañas.append(pygame.Rect(x, CONTENIDO_Y, ancho, 32)); x += ancho + 8
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_TAB): return None
                    if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_PAGEUP): cat = (cat - 1) % len(categorias); elegido = 0
                    if e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_PAGEDOWN): cat = (cat + 1) % len(categorias); elegido = 0
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(filas)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(filas)
                if e.type == pygame.MOUSEWHEEL: elegido = max(0, min(len(filas) - 1, elegido - e.y))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    pos = ui['a_logico'](e.pos)
                    for k, r in enumerate(pestañas):
                        if r.collidepoint(pos): cat = k; elegido = 0
                    if lista.collidepoint(pos): elegido = min(len(filas) - 1, inicio + (pos[1] - lista.y) // alto)
            fondo(ventana)
            titulo(ventana, 'Ataques')
            for k, r in enumerate(pestañas):
                panel_flecha(ventana, r, (0, 1) if k == cat else (0, 0))
                t = fuente(24).render(categorias[k], True, 'white'); ventana.blit(t, t.get_rect(center=r.center))
            caja(ventana, lista.inflate(10, 10), 'panel', PANEL)
            for k in range(inicio, min(len(filas), inicio + visibles)):
                nombre, tipo, *_ = filas[k]
                r = pygame.Rect(lista.x, lista.y + (k - inicio) * alto, lista.width, alto - 4)
                if k == elegido: panel_flecha(ventana, r, (0, 1))
                ventana.blit(fuente(24).render(nombre, True, 'white'), (r.x + 10, r.y + 6))
                pygame.draw.circle(ventana, COLORES_TIPO.get(normalizar_tipo(tipo), (150, 150, 150)), (r.right - 14, r.centery), 6)
            if filas:                                                    # el detalle del elegido
                nombre, tipo, explicacion, numeros, usan = filas[elegido]
                panel = pygame.Rect(lista.right + 24, lista.y, W - lista.right - 24 - MARGEN_X, lista.height)
                entra = aparecer(pygame.time.get_ticks() - abierto, 0, 200)
                caja(ventana, panel.move(round((1 - entra) * 60), 0), 'panel', PANEL)
                ventana.blit(fuente(48).render(nombre, True, 'white'), (panel.x + 18, panel.y + 14))
                chip_tipo(ventana, normalizar_tipo(tipo), panel.x + 20, panel.y + 56)
                y = panel.y + 96
                for bloque, color in ((explicacion, (240, 240, 240)), ('Numeros: ' + numeros, (240, 220, 120)), ('Lo usan: ' + usan, (170, 220, 255))):
                    for linea in ajustar_texto(bloque, fuente(24), panel.width - 36):
                        ventana.blit(fuente(24).render(linea, True, color), (panel.x + 18, y)); y += 20
                    y += 12
            pie(ventana, str(len(filas)) + ' ' + categorias[cat].lower() + '   izq/der: categoría   arriba/abajo: elegir   ESC: volver')
            ui['presentar'](); reloj.tick(60)


    # ---------- inicial ----------

    def _evolucion_final(nombre):
        """Ultima evolucion a la que puede llegar (siguiendo la primera rama), para mostrar en que se convierte."""
        vistos = {nombre}
        while True:
            siguientes = [r['a'] for r in progreso.requisitos(nombre) if r['a'] not in vistos]
            if not siguientes: return nombre
            nombre = siguientes[0]; vistos.add(nombre)


    def elegir_inicial(ui, dibujar_fondo=None, texto_titulo='Elegi tu compañero'):
        """Elegis tu primer pokemon: Mudkip, Torchic, Riolu o Natu (uno por rol).
        dibujar_fondo(ahora): lo que va detras (el viaje temporal lo usa con el tunel); si no, el fondo del menu.
        El elegido camina (Walk) y al confirmar salta de alegria (Hop) antes de volver."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        n_ = len(INICIALES)
        ANCHO_CAJA, SEPARACION = 220, 236
        x0 = W // 2 - SEPARACION * (n_ - 1) / 2
        animadores = []
        for i, n in enumerate(INICIALES):
            a = AnimadorPokemon(n, pygame.Rect(0, 0, 10, 10), 110); a.rect.center = (round(x0 + i * SEPARACION), 270); a.cambiar('idle', 0, True)
            animadores.append(a)
        elegido, confirmado = 1, None
        reloj = pygame.time.Clock()
        while True:
            cajas = [pygame.Rect(round(x0 + i * SEPARACION) - ANCHO_CAJA // 2, 160, ANCHO_CAJA, 360) for i in range(n_)]
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if confirmado is not None: continue
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key in (pygame.K_LEFT, pygame.K_a): elegido = (elegido - 1) % n_
                    if e.key in (pygame.K_RIGHT, pygame.K_d): elegido = (elegido + 1) % n_
                    if e.key in (pygame.K_RETURN, pygame.K_e): confirmado = pygame.time.get_ticks()
                if e.type == pygame.MOUSEMOTION:
                    for i, c in enumerate(cajas):
                        if c.collidepoint(ui['a_logico'](e.pos)): elegido = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, c in enumerate(cajas):
                        if c.collidepoint(ui['a_logico'](e.pos)): elegido = i; confirmado = pygame.time.get_ticks()
            if confirmado is not None and pygame.time.get_ticks() - confirmado > 700: return INICIALES[elegido]   # deja ver el salto de alegria
            if dibujar_fondo: dibujar_fondo(pygame.time.get_ticks())
            else: fondo_menu(ui, pygame.time.get_ticks(), False)
            velo = pygame.Surface((W, 100), pygame.SRCALPHA); velo.fill((0, 0, 0, 120)); ventana.blit(velo, (0, 0))   # que el titulo se lea sobre el fondo
            titulo(ventana, texto_titulo)
            for i, (n, a) in enumerate(zip(INICIALES, animadores)):
                c = cajas[i]
                velo = pygame.Surface(c.size, pygame.SRCALPHA); velo.fill((0, 0, 0, 170 if i == elegido else 110)); ventana.blit(velo, c)
                pygame.draw.rect(ventana, 'white', c, 3)
                if i == elegido and confirmado is not None: a.cambiar('hop', 0, True) or a.cambiar('walk', 0, True)
                else: a.cambiar('walk' if i == elegido else 'idle', 0, True)
                a.actualizar()
                if not a.dibujar(ventana): pygame.draw.circle(ventana, (200, 200, 200), a.rect.center, 40)
                t = fuente(38).render(n.title(), True, 'white'); ventana.blit(t, t.get_rect(center=(c.centerx, c.y + 190)))
                x = c.x + 16
                for tipo in pokemones[n].get('tipo', []): x += chip_tipo(ventana, normalizar_tipo(tipo), x, c.y + 214)
                ventana.blit(fuente(22).render('Rol: ' + ROL_POKEMON.get(n, '-'), True, (220, 220, 220)), (c.x + 16, c.y + 246))
                final = _evolucion_final(n)
                if final != n: ventana.blit(fuente(20).render('Llega a ser ' + final.title(), True, (240, 220, 120)), (c.x + 16, c.y + 270))
                for k, linea in enumerate(ajustar_texto(ESTILO_INICIAL.get(n, ''), fuente(20), c.width - 32)[:3]):
                    ventana.blit(fuente(20).render(linea, True, (200, 200, 200)), (c.x + 16, c.y + 298 + k * 18))
                if i == elegido: dibujar_esquinas(ventana, c.inflate(6, 6))
            pie(ventana, 'izq/der: elegir   ENTER: confirmar   ESC: volver')
            ui['presentar'](); reloj.tick(60)


    # ---------- equipo (TAB) ----------

    def equipo(ui, j, acc):
        """
        Menu de equipo. acc tiene funciones de main.py:
            'movs'(m) -> 4 nombres a mostrar    'evolucionar'(i, destino)    'enseñar'(i, casilla, mt)
            'activar'(i)    'reserva'() -> lista de la reserva    'traer'(i_reserva, i_equipo)
        """
        estilo = ui['config'].get('estilo_equipo', 'clasico')
        elegido = j['activo']
        reloj = pygame.time.Clock()
        escena = {'animadores': {}, 'quieto_desde': pygame.time.get_ticks(), 'dormidos': False}
        while True:
            equipo_ = j['equipo']
            opciones_ = list(range(len(equipo_))) + ['mochila', 'reserva', 'volver']
            elegido = min(elegido, len(opciones_) - 1)          # (antes se recortaba al equipo y nunca se podia elegir mochila ni reserva)
            accion = None
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    escena['quieto_desde'] = pygame.time.get_ticks()      # cualquier cosa los despierta
                    if escena['dormidos']: escena['dormidos'] = 'despertar'
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_TAB): return None
                    if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(opciones_)
                    if e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(opciones_)
                    if e.key in (pygame.K_RETURN, pygame.K_e): accion = opciones_[elegido]
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in escena.get('zonas', {}).items():
                        if r.collidepoint(ui['a_logico'](e.pos)): elegido = opciones_.index(i) if i in opciones_ else elegido; accion = i
            if accion == 'volver': return None
            if accion == 'mochila' and mochila(ui, j, acc) == 'salir': return 'salir'
            if accion == 'reserva' and reserva(ui, j, acc) == 'salir': return 'salir'
            if isinstance(accion, int) and ficha(ui, j, accion, acc) == 'salir': return 'salir'
            if estilo == 'escenario': _dibujar_escenario(ui, j, opciones_[elegido], escena)
            else: _dibujar_clasico(ui, j, opciones_[elegido], escena)
            ui['presentar'](); reloj.tick(60)


    def _info_corta(ventana, m, j, x, y, ancho, activo):
        """Nombre, nivel, vida y experiencia de un miembro."""
        vida = j['vida'] if activo else m['vida']
        ventana.blit(fuente(32).render(m['nombre'].replace('_', ' ').title(), True, 'white'), (x, y))
        nv = fuente(28).render('Nv ' + str(m['nivel']), True, (240, 220, 120)); ventana.blit(nv, (x + ancho - nv.get_width(), y + 2))
        barra(ventana, (x, y + 32, ancho, 12), vida / max(1, m['max_vida']), (60, 200, 90) if vida > m['max_vida'] / 3 else (220, 80, 60))
        ventana.blit(fuente(20).render(str(int(vida)) + '/' + str(m['max_vida']), True, 'white'), (x, y + 46))
        barra(ventana, (x, y + 64, ancho, 6), progreso.progreso_nivel(m), (80, 160, 255))
        extra = []
        if m['puntos']: extra.append(str(m['puntos']) + ' puntos EV')
        if progreso.evoluciones(m, j['inventario']['objetos']): extra.append('puede evolucionar!')
        if extra: ventana.blit(fuente(20).render(' - '.join(extra), True, (250, 200, 90)), (x, y + 74))


    def _dibujar_clasico(ui, j, sel, escena):
        """Como el menu de equipo de los juegos: el activo grande a la izquierda y los demas en lista."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        if not fondo(ventana, 'fondo_equipo', (60, 110, 90), estirar=True):        # el de BW tiene un degrade: se estira, no se repite
            for y in range(0, H, 24): pygame.draw.line(ventana, (70, 125, 100), (0, y), (W, y), 1)
        zonas = {}
        for i, m in enumerate(j['equipo']):
            r = pygame.Rect(40, 60, 380, 200) if i == 0 else pygame.Rect(460, 40 + (i - 1) * 120, 500, 108)
            zonas[i] = r
            vida = j['vida'] if i == j['activo'] else m['vida']
            nombre = 'miembro_debil' if vida <= 0 else 'miembro_activo' if i == j['activo'] else 'miembro'
            if pieza(nombre): caja(ventana, r, nombre)
            else:
                pygame.draw.rect(ventana, (40, 90, 150) if i == j['activo'] else (50, 70, 90), r, border_radius=14)
                pygame.draw.rect(ventana, 'white', r, 3, border_radius=14)
            img = ui['retrato'](m['nombre'], 70 if i == 0 else 56)
            if img: ventana.blit(img, (r.x + 14, r.y + 14))
            _info_corta(ventana, m, j, r.x + (100 if i == 0 else 84), r.y + 14, r.width - (120 if i == 0 else 100), i == j['activo'])
            if i == j['activo']: ventana.blit(fuente(20).render('PELEANDO', True, (180, 230, 255)), (r.x + 14, r.bottom - 26))
            if sel == i: dibujar_esquinas(ventana, r.inflate(6, 6))
        for k, (clave, texto) in enumerate((('mochila', 'Mochila'), ('reserva', 'Reserva'), ('volver', 'Volver'))):
            r = pygame.Rect(40 + k * 190, H - 90, 170, 50); zonas[clave] = r
            boton(ventana, r, texto, sel == clave, 30)
        ventana.blit(fuente(22).render('ENTER: ver ficha (stats, movimientos, evolucion)   TAB / ESC: volver al juego', True, 'white'), (40, H - 30))
        escena['zonas'] = zonas


    def _dibujar_escenario(ui, j, sel, escena):
        """Tus pokemon parados en un escenario como en la pokedex. Si no tocas nada un rato, se duermen."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        ahora = pygame.time.get_ticks()
        for y in range(0, H, 4):
            k = y / H
            pygame.draw.rect(ventana, (round(30 + 60 * k), round(40 + 50 * k), round(70 + 40 * k)), (0, y, W, 4))
        pygame.draw.ellipse(ventana, (90, 80, 70), (90, 330, W - 180, 150))          # escenario
        pygame.draw.ellipse(ventana, (120, 105, 90), (110, 320, W - 220, 130))
        if escena['dormidos'] is False and ahora - escena['quieto_desde'] > SUEÑO: escena['dormidos'] = True
        zonas = {}
        n = len(j['equipo'])
        for i, m in enumerate(j['equipo']):
            x = W // 2 + round((i - (n - 1) / 2) * 280)
            a = escena['animadores'].get(m['nombre'])
            if not a:
                a = AnimadorPokemon(m['nombre'], pygame.Rect(0, 0, 10, 10), 130); a.cambiar('idle', 0, True)
                escena['animadores'][m['nombre']] = a
            a.rect.center = (x, 360)
            if escena['dormidos'] is True: a.cambiar('sleep', 0, True)       # todos los sprites tienen Sleep
            elif escena['dormidos'] == 'despertar':                       # los que tienen Wake se despiertan con animacion
                a.despertando = a.cambiar('wake', 0, False)
                if not a.despertando: a.cambiar('idle', 0, True)
            elif getattr(a, 'despertando', False):
                if a.esta_terminada(): a.despertando = False; a.cambiar('idle', 0, True)
            else: a.cambiar('idle', 0, True)
            a.actualizar()
            if not a.dibujar(ventana): pygame.draw.circle(ventana, (200, 200, 200), (x, 360), 40)
            r = pygame.Rect(x - 125, 440, 250, 100); zonas[i] = r
            velo = pygame.Surface(r.size, pygame.SRCALPHA); velo.fill((0, 0, 0, 150)); ventana.blit(velo, r)
            _info_corta(ventana, m, j, r.x + 10, r.y + 8, r.width - 20, i == j['activo'])
            if sel == i: dibujar_esquinas(ventana, pygame.Rect(x - 90, 250, 180, 290))
            if escena['dormidos'] is True: ventana.blit(fuente(30).render('z z', True, 'white'), (x + 40, 260 + round(math.sin(ahora / 400 + i) * 6)))
        if escena['dormidos'] == 'despertar': escena['dormidos'] = False
        titulo(ventana, 'Tu equipo', 40, 30, 60, 'white')
        for k, (clave, texto) in enumerate((('mochila', 'Mochila'), ('reserva', 'Reserva'), ('volver', 'Volver'))):
            r = pygame.Rect(W - 600 + k * 190, 40, 170, 46); zonas[clave] = r
            boton(ventana, r, texto, sel == clave, 30)
        ventana.blit(fuente(22).render('ENTER: ver ficha   TAB / ESC: volver al juego', True, 'white'), (40, H - 30))
        escena['zonas'] = zonas


    def ficha(ui, j, i, acc):
        """Ficha de un miembro: stats con IV y EV (para gastar puntos), sinergia, sus 4 movimientos (para enseñar MT), sus 2 objetos y evolucion.
        Abajo, un recuadro explica lo que tenes elegido (que hace el stat, el movimiento, el objeto...)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        elegido = 0
        reloj = pygame.time.Clock()
        animador, ficha_zonas = None, {}
        aviso = {'texto': '', 'hasta': 0}
        sinergias = [None] + list(datos.pokemones.SINERGIAS)
        while True:
            m = j['equipo'][i]
            m.setdefault('items', []); m.setdefault('sinergia', None)
            if not animador or animador.pokemon != m['nombre']:
                animador = AnimadorPokemon(m['nombre'], pygame.Rect(0, 0, 10, 10), 120); animador.rect.center = (170, 170); animador.cambiar('idle', 0, True)
            evos = progreso.evoluciones(m, j['inventario']['objetos'])
            filas = [('stat', s_) for s_ in progreso.STATS] + [('sinergia', None)] + [('mov', k_) for k_ in range(4)] + [('item', r_) for r_ in range(tienda.MAX_EQUIPADOS)]
            filas += [('evo', r_) for r_ in evos] + ([('caramelo', None)] if j['inventario']['objetos'].get('caramelo_raro', 0) > 0 else [])
            filas += ([('activar', None)] if i != j['activo'] else []) + [('volver', None)]
            elegido = min(elegido, len(filas) - 1)
            accion = None
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_TAB): return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(filas)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(filas)
                    if e.key in (pygame.K_LEFT, pygame.K_a): i = (i - 1) % len(j['equipo']); animador = None
                    if e.key in (pygame.K_RIGHT, pygame.K_d): i = (i + 1) % len(j['equipo']); animador = None
                    if e.key in (pygame.K_RETURN, pygame.K_e): accion = filas[elegido]
                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                    for k_, r in ficha_zonas.items():
                        if k_ < len(filas) and r.collidepoint(ui['a_logico'](e.pos)):
                            elegido = k_
                            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: accion = filas[k_]
            if animador is None: continue
            if accion:
                clase, valor = accion
                if clase == 'volver': return None
                if clase == 'stat':
                    motivo = progreso.motivo_sin_ev(m, valor)
                    if motivo: aviso.update(texto=motivo, hasta=pygame.time.get_ticks() + 2500)
                    elif progreso.gastar_punto(m, valor): acc['refrescar']()
                if clase == 'sinergia':
                    actual = sinergias.index(m['sinergia']) if m['sinergia'] in sinergias else 0
                    acc['sinergia'](i, sinergias[(actual + 1) % len(sinergias)])
                if clase == 'activar': acc['activar'](i)
                if clase == 'caramelo': acc['caramelo'](i)
                if clase == 'evo':
                    if preguntar(ui, 'Evolucionar a ' + m['nombre'].title() + ' en ' + valor['a'].title() + '?', ['Si', 'Todavia no'],
                                 'requisito: ' + progreso.texto_requisito(valor)) == 0:
                        acc['evolucionar'](i, valor); animacion_evolucion(ui, m['nombre'])
                if clase == 'mov':
                    mt = elegir_mt(ui, j, m, valor)
                    if mt == 'salir': return 'salir'
                    if mt: acc['enseñar'](i, valor, mt)
                if clase == 'item':
                    r = elegir_objeto(ui, j, m, valor)
                    if r == 'salir': return 'salir'
                    if r is not None: acc['equipar'](i, valor, r or None)
            # ----- panel izquierdo: el pokemon -----
            fondo(ventana)
            caja(ventana, (20, 20, 300, H - 40), 'panel', PANEL)
            animador.actualizar()
            if not animador.dibujar(ventana): pygame.draw.circle(ventana, (200, 200, 200), (170, 170), 50)
            ventana.blit(fuente(40).render(m['nombre'].replace('_', ' ').title(), True, 'white'), (40, 255))
            x = 40
            for tipo in pokemones[m['nombre']].get('tipo', []): x += chip_tipo(ventana, normalizar_tipo(tipo), x, 292)
            rol = ROL_POKEMON.get(m['nombre'], '')
            ventana.blit(fuente(22).render(rol.title(), True, (200, 220, 255)), (x + 6, 296))
            ventana.blit(fuente(26).render('Nivel ' + str(m['nivel']) + '   amistad ' + str(m['amistad']), True, (240, 220, 120)), (40, 324))
            barra(ventana, (40, 350, 260, 10), progreso.progreso_nivel(m), (80, 160, 255))
            ventana.blit(fuente(20).render('falta ' + str(max(0, progreso.xp_para(m['nombre'], m['nivel'] + 1) - m['xp'])) + ' xp para el nivel ' + str(m['nivel'] + 1),
                                           True, (220, 220, 220)), (40, 366))
            total_ev = sum(m['evs'].values())
            ventana.blit(fuente(20).render('EV usados: ' + str(total_ev) + '/' + str(progreso.EV_MAX) + '  (max ' + str(progreso.EV_MAX_STAT) + ' por stat)',
                                           True, (220, 220, 220)), (40, 388))
            for k_, r in enumerate(progreso.requisitos(m['nombre'])[:3]):
                ventana.blit(fuente(20).render('Evoluciona a ' + r['a'].title() + ' (' + progreso.texto_requisito(r) + ')', True, (200, 230, 200)), (40, 412 + k_ * 20))
            for k_, linea in enumerate(ajustar_texto('Naturaleza ' + progreso.texto_naturaleza(m.get('naturaleza')), fuente(20), 270)[:2]):   # como en los juegos
                ventana.blit(fuente(20).render(linea, True, (240, 200, 230)), (40, 478 + k_ * 18))
            unico = mecanicas.texto_de(m['nombre'])                       # lo que hace unica a su linea (mecanicas.py)
            if unico:
                for k_, linea in enumerate(ajustar_texto(unico, fuente(20), 270)[:2]):
                    ventana.blit(fuente(20).render(linea, True, (160, 220, 255)), (40, 516 + k_ * 17))
            ventana.blit(fuente(20).render('izq/der: otro miembro   ENTER: usar', True, (200, 200, 200)), (40, H - 50))
            # ----- columnas de la derecha -----
            ficha_zonas = {}
            col_a, col_b, ancho_col = 340, 660, 310
            ventana.blit(fuente(28).render('Stats', True, TINTA), (col_a, 22))
            puntos = fuente(22).render('Puntos para repartir: ' + str(m['puntos']), True, ALERTA if m['puntos'] else TINTA)
            ventana.blit(puntos, (col_a + ancho_col - puntos.get_width(), 26))
            ventana.blit(fuente(28).render('Movimientos', True, TINTA), (col_b, 22))
            y_a, y_b = 52, 52
            movs_txt = acc['movs'](m)
            for k_, (clase, valor) in enumerate(filas):
                if clase in ('stat', 'sinergia', 'evo', 'caramelo', 'activar', 'volver'):
                    if clase == 'sinergia': y_a += 6
                    if clase == 'evo' and filas[k_ - 1][0] != 'evo': y_a += 6
                    r = pygame.Rect(col_a, y_a, ancho_col, 30); y_a += 34
                else:
                    if clase == 'item' and valor == 0:
                        y_b += 8; ventana.blit(fuente(28).render('Objetos (hasta ' + str(tienda.MAX_EQUIPADOS) + ')', True, TINTA), (col_b, y_b)); y_b += 30
                    r = pygame.Rect(col_b, y_b, ancho_col, 30); y_b += 34
                ficha_zonas[k_] = r
                caja(ventana, r, 'boton_elegido' if k_ == elegido else 'boton', OSCURO, 2)
                if clase == 'stat':
                    total = progreso.stat(m['nombre'], valor, m['nivel'], m['ivs'][valor], m['evs'][valor], m.get('naturaleza'))
                    efecto = progreso.factor_naturaleza(m.get('naturaleza'), valor)   # verde si la naturaleza lo sube, rojo si lo baja
                    ventana.blit(fuente(24).render(progreso.NOMBRE_STAT[valor], True, (140, 255, 150) if efecto > 1 else (255, 140, 140) if efecto < 1 else 'white'), (r.x + 8, r.y + 7))
                    ventana.blit(fuente(24).render(str(total), True, (240, 220, 120)), (r.x + 100, r.y + 7))
                    ventana.blit(fuente(20).render('EV ' + str(m['evs'][valor]) + '/' + str(progreso.EV_MAX_STAT), True, (200, 200, 200)), (r.x + 150, r.y + 8))
                    barra(ventana, (r.x + 150, r.y + 24, 120, 3), m['evs'][valor] / progreso.EV_MAX_STAT, (120, 200, 255))
                    if not progreso.motivo_sin_ev(m, valor): ventana.blit(fuente(26).render('+', True, (120, 255, 120)), (r.right - 22, r.y + 4))
                elif clase == 'sinergia':
                    clave = list(datos.pokemones.sinergia_de(m['nombre'], m['sinergia']))[0] if datos.pokemones.sinergia_de(m['nombre'], m['sinergia']) else None
                    txt = 'Sinergia: ' + datos.pokemones.SINERGIAS.get(clave, '-') + ('' if m['sinergia'] else ' (rol)')
                    ventana.blit(fuente(22).render(txt, True, (180, 230, 255)), (r.x + 8, r.y + 8))
                elif clase == 'mov':
                    ventana.blit(fuente(24).render(mts.CASILLAS[valor] + ':  ' + movs_txt[valor], True, 'white'), (r.x + 8, r.y + 7))
                    if m['movs'][valor]: ventana.blit(fuente(20).render('(MT)', True, (150, 180, 255)), (r.right - 46, r.y + 8))
                elif clase == 'item':
                    clave = m['items'][valor] if valor < len(m['items']) else None
                    icono = icono_objeto(clave, 22) if clave else None
                    if icono: ventana.blit(icono, (r.x + 6, r.y + 4))
                    ventana.blit(fuente(24).render(tienda.ITEMS[clave]['nombre'] if clave else '(vacio)', True, 'white' if clave else (150, 150, 150)), (r.x + 34, r.y + 7))
                elif clase == 'evo': ventana.blit(fuente(24).render('Evolucionar a ' + valor['a'].title() + '!', True, (250, 220, 90)), (r.x + 8, r.y + 7))
                elif clase == 'caramelo':
                    icono = icono_objeto('caramelo_raro', 22)
                    if icono: ventana.blit(icono, (r.x + 6, r.y + 4))
                    ventana.blit(fuente(24).render('Usar Caramelo Raro (x' + str(j['inventario']['objetos'].get('caramelo_raro', 0)) + ')', True, 'white'), (r.x + 34, r.y + 7))
                elif clase == 'activar': ventana.blit(fuente(24).render('Poner a pelear', True, 'white'), (r.x + 8, r.y + 7))
                else: ventana.blit(fuente(24).render('Volver', True, 'white'), (r.x + 8, r.y + 7))
                if k_ == elegido: dibujar_esquinas(ventana, r.inflate(6, 4), margen=4, largo=10, grosor=2)
            # ----- recuadro con la explicacion de lo elegido -----
            info = pygame.Rect(col_a, H - 128, col_b + ancho_col - col_a, 108)
            caja(ventana, info, 'panel', PANEL)
            lineas = _explicar(filas[elegido], m, j, acc)
            if pygame.time.get_ticks() < aviso['hasta']: lineas = [aviso['texto']] + lineas
            y = info.y + 10
            for n_, linea in enumerate(lineas):
                for parte in ajustar_texto(linea, fuente(21), info.width - 24):
                    if y > info.bottom - 20: break
                    ventana.blit(fuente(21).render(parte, True, ALERTA if n_ == 0 and pygame.time.get_ticks() < aviso['hasta'] else (235, 235, 235)), (info.x + 12, y)); y += 20
            ui['presentar'](); reloj.tick(60)


    def _explicar(fila, m, j, acc):
        """Lineas que explican la fila elegida de la ficha."""
        clase, valor = fila
        if clase == 'stat':
            return [progreso.NOMBRE_STAT[valor] + ': ' + progreso.USO_STAT[valor] + '.',
                    'IV ' + str(m['ivs'][valor]) + ' (al azar, de 0 a 31). EV ' + str(m['evs'][valor]) + ' de ' + str(progreso.EV_MAX_STAT) +
                    ' (total ' + str(sum(m['evs'].values())) + ' de ' + str(progreso.EV_MAX) + ').',
                    'ENTER: gastar 1 punto = +' + str(progreso.EV_POR_PUNTO) + ' EV. Ganas 1 punto por nivel.']
        if clase == 'sinergia':
            pasiva = datos.pokemones.sinergia_de(m['nombre'], m['sinergia'])
            txt = ', '.join('+' + str(round(v * 100, 1)) + '% ' + datos.pokemones.SINERGIAS.get(c, c) for c, v in pasiva.items())
            return ['Desde la banca le da al que pelea: ' + (txt or 'nada') + '. ENTER: cambiar (' + ', '.join(datos.pokemones.SINERGIAS.values()) + ').',
                    'Asistencia (F / G desde la banca): ' + acc['asistencia'](m)]
        if clase == 'mov':
            nombres = ['E (cuerpo a cuerpo)', 'Q (a distancia)', 'Shift (especial 1)', 'R (especial 2)']
            return [nombres[valor] + ': ' + acc['movs'](m)[valor] + '. ' + acc['info_movs'](m)[valor],
                    'ENTER: enseñar una MT. Las de combate van en cualquier casilla; las especiales solo en Shift o R.']
        if clase == 'item':
            clave = m['items'][valor] if valor < len(m['items']) else None
            if clave: return [tienda.ITEMS[clave]['nombre'] + ': ' + tienda.ITEMS[clave]['desc'] + '.', 'Solo cuenta mientras este pokemon pelea. ENTER: cambiar o sacar.']
            return ['Ranura vacia. ENTER: equipar un objeto de la mochila (Cinta Fuerte, Carbon, Eter...).', 'Cada pokemon lleva hasta ' + str(tienda.MAX_EQUIPADOS) + ' objetos.']
        if clase == 'evo': return ['Requisito: ' + progreso.texto_requisito(valor) + '. Conserva nivel, IV, EV, MT y objetos.']
        if clase == 'caramelo': return ['Caramelo Raro: ' + m['nombre'].title() + ' sube al nivel ' + str(m['nivel'] + 1) + ' al instante (con su punto de EV).']
        if clase == 'activar': return ['Lo pone a pelear ahora (sin la espera del cambio).']
        return ['Volver al equipo.']


    def elegir_objeto(ui, j, m, ranura):
        """Que objeto de la mochila se pone en la ranura. Devuelve la clave, '' para sacar el que tiene, None si cancela o 'salir'."""
        objetos = j['inventario']['objetos']
        claves = [k for k in tienda.EQUIPABLES if objetos.get(k, 0) > 0]
        filas = [(tienda.ITEMS[k]['nombre'] + '  x' + str(objetos[k]), tienda.ITEMS[k]['desc']) for k in claves]
        tiene = ranura < len(m.get('items', []))
        if tiene: filas.append(('Sacar ' + tienda.ITEMS[m['items'][ranura]]['nombre'], 'vuelve a la mochila'))
        if not filas:
            preguntar(ui, 'No tenes objetos para equipar', ['Ok'], 'se compran en la tienda (Cinta Fuerte, Carbon, Eter...)'); return None
        k = lista_detallada(ui, 'Objeto para ' + m['nombre'].title(), filas, 'Solo cuenta mientras pelea este pokemon.')
        if k == 'salir': return 'salir'
        if k is None: return None
        return claves[k] if k < len(claves) else ''


    def elegir_mt(ui, j, m, casilla):
        """Lista de las MT de la mochila que este pokemon puede aprender en esa casilla, con lo que hace cada una.
        Las MT de combate van en cualquier casilla; las especiales (recargan en segundos) solo en Shift o R."""
        trucos_ = ui['config']['trucos']
        disponibles = list(mts.MTS) if trucos_.get('todas_mt') else [k for k, n in j['inventario']['objetos'].items() if n > 0 and k in mts.MTS]
        aprende = [k for k in disponibles if mts.puede_aprender(m['nombre'], k)]
        sirven = [k for k in aprende if mts.sirve_en(k, casilla)]
        nombre_casilla = mts.CASILLAS[casilla]
        if not sirven:
            detalle = ('tenes MT especiales: esas van en Shift o R' if aprende else 'se compran en la tienda o las sueltan los jefes')
            preguntar(ui, 'No tenes MT que ' + m['nombre'].title() + ' pueda usar en ' + nombre_casilla, ['Ok'], detalle); return None
        sirven.sort(key=lambda k: (mts.MTS[k]['casillas'] != 'todas', mts.MTS[k]['nombre']))
        cantidad = lambda k: '' if trucos_.get('todas_mt') else ' x' + str(j['inventario']['objetos'][k])
        filas = [(mts.MTS[k]['nombre'][3:] + ' (' + mts.MTS[k]['tipo'] + ')' + cantidad(k),
                  ('Combate - ' if mts.MTS[k]['casillas'] == 'todas' else 'Especial - ') + datos.describir_movimiento(mts.MTS[k]['datos'])) for k in sirven]
        i = lista_detallada(ui, 'MT para ' + nombre_casilla + ' de ' + m['nombre'].title(), filas,
                            'Combate: sirven en cualquier casilla.  Especial: solo Shift o R.  La MT se gasta al usarla.')
        if i == 'salir': return 'salir'
        return sirven[i] if i is not None else None


    def lista_detallada(ui, titulo_, filas, pie='', elegido=0):
        """Lista con scroll: cada fila tiene un nombre y abajo una linea que explica que hace. Devuelve el indice elegido, None o 'salir'.
        elegido: en que fila arranca (para volver a abrirla donde estaba)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        elegido, reloj, alto = max(0, min(elegido, len(filas) - 1)), pygame.time.Clock(), 50
        visibles = (H - 170) // alto
        while True:
            inicio = max(0, min(elegido - visibles // 2, len(filas) - visibles))
            zonas = {}
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_TAB): return None
                    if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(filas)
                    if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(filas)
                    if e.key in (pygame.K_RETURN, pygame.K_e): return elegido
                if e.type == pygame.MOUSEWHEEL: elegido = max(0, min(len(filas) - 1, elegido - e.y))
                if e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    for k in range(inicio, min(len(filas), inicio + visibles)):
                        r = pygame.Rect(40, 100 + (k - inicio) * alto, W - 80, alto - 6)
                        if r.collidepoint(ui['a_logico'](e.pos)):
                            elegido = k
                            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: return k
            fondo(ventana)
            titulo(ventana, titulo_)
            for k in range(inicio, min(len(filas), inicio + visibles)):
                r = pygame.Rect(40, 100 + (k - inicio) * alto, W - 80, alto - 6)
                caja(ventana, r, 'boton_elegido' if k == elegido else 'boton', OSCURO, 2)
                nombre, desc = filas[k]
                ventana.blit(fuente(26).render(nombre, True, 'white'), (r.x + 12, r.y + 5))
                ventana.blit(fuente(20).render(desc, True, (205, 205, 205)), (r.x + 12, r.y + 26))
                if k == elegido: dibujar_esquinas(ventana, r.inflate(6, 4), margen=4, largo=10, grosor=2)
            pie_menu(ventana, pie + '   ENTER: elegir   ESC: volver')
            ui['presentar'](); reloj.tick(60)


    def mochila(ui, j, acc):
        """Lo que tenes: curaciones (se usan aca: elegis a quien), objetos para equipar, MT, piedras, lo que llevan puesto tus pokemon
        y lo que es de todo el equipo, con lo que hace cada cosa."""
        inv = j['inventario']
        elegido = 0
        while True:
            filas, claves = [], []
            curativos = [k_ for k_, n in inv['objetos'].items() if n > 0 and 'curativo' in tienda.ITEMS.get(k_, {})]
            for k_ in curativos:
                filas.append((tienda.ITEMS[k_]['nombre'] + '  x' + str(inv['objetos'][k_]) + '   (ENTER: usar)', tienda.ITEMS[k_]['desc'])); claves.append(k_)
            for k_, n in inv['objetos'].items():
                if n > 0 and k_ not in curativos: filas.append((tienda.ITEMS[k_]['nombre'] + '  x' + str(n), tienda.ITEMS[k_]['desc'])); claves.append(None)
            for m in j['equipo'] + j.get('reserva', []):
                for k_ in m.get('items', []): filas.append((tienda.ITEMS[k_]['nombre'] + '  (lo lleva ' + m['nombre'].title() + ')', tienda.ITEMS[k_]['desc'])); claves.append(None)
            for k_ in dict.fromkeys(inv['comprados']):
                if 'permanente' in tienda.ITEMS[k_]: filas.append((tienda.ITEMS[k_]['nombre'] + '  (equipo)', tienda.ITEMS[k_]['desc'])); claves.append(None)
            for linea in tienda.activos(inv): filas.append((linea, 'activo para todo el equipo (el numero son las salas que le quedan)')); claves.append(None)
            if not filas: filas, claves = [('Vacia', 'Las cosas se consiguen en la tienda, con Chikorita rosa y de los jefes.')], [None]
            r = lista_detallada(ui, 'Mochila', filas, 'Las curaciones se usan aca. Objetos, MT y piedras, desde la ficha de cada pokemon.', elegido)
            if r == 'salir': return 'salir'
            if r is None: return None
            elegido = r
            clave = claves[r]
            if not clave: continue
            miembros = [(i_, m) for i_, m in enumerate(j['equipo'])] + [(('r', i_), m) for i_, m in enumerate(j.get('reserva', []))]
            opciones_ = [m['nombre'].replace('_', ' ').title() + '  ' + (('debilitado' if m['vida'] <= 0 else str(round(m['vida'])) + '/' + str(m['max_vida']) + ' PS')
                         + (' - con estado' if m.get('estados') else '')) for _, m in miembros]
            q = preguntar(ui, '¿En quién usás ' + tienda.ITEMS[clave]['nombre'] + '?', opciones_ + ['Cancelar'], tienda.ITEMS[clave]['desc'])
            if q == 'salir': return 'salir'
            if q is None or q >= len(miembros): continue
            texto = acc['usar'](miembros[q][0], clave)
            if preguntar(ui, texto, ['Ok']) == 'salir': return 'salir'


    def reserva(ui, j, acc):
        """Los que se unieron con el equipo lleno (como mucho 3). Solo se cambian con el equipo en la tienda: Chikorita los cuida."""
        lista = acc['reserva']()
        if not lista:
            r = preguntar(ui, 'La reserva esta vacia', ['Ok'], 'cuando se te une alguien con el equipo lleno, viene aca')
            return 'salir' if r == 'salir' else None
        if not acc['cambiar_reserva']():
            filas = [(m['nombre'].replace('_', ' ').title() + ' Nv ' + str(m['nivel']), 'Esta con Chikorita: se puede traer al equipo en la tienda') for m in lista]
            r = lista_detallada(ui, 'Reserva (' + str(len(lista)) + ')', filas, 'Los cambios con la reserva se hacen en la tienda.')
            return 'salir' if r == 'salir' else None
        nombres = [m['nombre'].title() + ' Nv ' + str(m['nivel']) for m in lista[:7]]
        i = preguntar(ui, 'A quien traes al equipo?', nombres + ['Cancelar'])
        if i == 'salir': return 'salir'
        if i is None or i >= len(nombres): return None
        if len(j['equipo']) < 3: acc['traer'](i, None); return None
        k = preguntar(ui, 'Por quien lo cambias?', [m['nombre'].title() for m in j['equipo']] + ['Cancelar'])
        if k == 'salir': return 'salir'
        if k is not None and k < len(j['equipo']): acc['traer'](i, k)


    def animacion_evolucion(ui, nombre):
        """Destello blanco y el pokemon nuevo."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        a = AnimadorPokemon(nombre, pygame.Rect(0, 0, 10, 10), 160); a.rect.center = (W // 2, H // 2); a.cambiar('idle', 0, True)
        reloj = pygame.time.Clock()
        for frame in range(150):
            for e in controles.eventos():
                if e.type == pygame.QUIT: return
            k = frame / 150
            ventana.fill((round(255 * (1 - k)), round(255 * (1 - k)), 255))
            a.actualizar()
            if k > 0.4: a.dibujar(ventana)
            if k > 0.5:
                t = fuente(48).render('Evoluciono en ' + nombre.title() + '!', True, 'white')
                ventana.blit(t, t.get_rect(center=(W // 2, H - 110)))
            ui['presentar'](); reloj.tick(60)

    return SimpleNamespace(**locals())


menus = armar_menus()
