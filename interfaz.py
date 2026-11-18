"""
interfaz.py - Lo que se ve fuera de la sala: menus (ajustes, controles, trucos, glosario, equipo, ficha, mochila), dialogos,
la rueda de curaciones, el logo y las escenas del borde del cosmos (la partida nueva y el viaje entre eras).

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
from sistema import controles, opciones, partidas, tipografia, animaciones, sonido
from mundo import entorno, efectos
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


    _logo_nuevo = {}


    def _partes_logo(escala):
        """El logo del juego (assets/interfaz/logo.png, lo arma 'python herramientas.py logo') cortado en 'Poké' y cada letra Unown: se
        separan por las columnas vacias (y las dos que se tocan, por la columna mas vacia). Cada parte agrandada x escala sin suavizar,
        con su sombra. Devuelve (partes, tamaño): partes = [(x, dibujo, sombra, brillo)] ([] si falta el archivo)."""
        if escala not in _logo_nuevo:
            ruta, partes, tam = os.path.join(os.path.dirname(FONDOS), 'logo.png'), [], (0, 0)
            if os.path.isfile(ruta):
                img = pygame.image.load(ruta).convert_alpha()
                w, h = img.get_size()
                cuenta = [sum(img.get_at((x, y)).a > 0 for y in range(h)) for x in range(w)]
                tramos, x = [], 0
                while x < w:
                    if not cuenta[x]: x += 1; continue
                    x1 = x
                    while x1 < w and cuenta[x1]: x1 += 1
                    if tramos and x1 - x > 30:                           # dos Unown pegados: se cortan por donde menos se tocan
                        corte = min(range(x + 10, x1 - 10), key=lambda c: cuenta[c])
                        tramos += [(x, corte), (corte, x1)]
                    else: tramos.append((x, x1))
                    x = x1
                for a, b in tramos:
                    pieza = pygame.transform.scale(img.subsurface((a, 0, b - a, h)), ((b - a) * escala, h * escala))
                    mascara = pygame.mask.from_surface(pieza)
                    partes.append((a * escala, pieza, mascara.to_surface(setcolor=(12, 16, 48, 120), unsetcolor=(0, 0, 0, 0)),
                                   mascara.to_surface(setcolor=(255, 255, 255, 150), unsetcolor=(0, 0, 0, 0))))
                tam = (w * escala, h * escala)
            _logo_nuevo[escala] = (partes, tam)
        return _logo_nuevo[escala]


    def dibujar_logo(ventana, alto, ahora, **donde):
        """El logo del juego: la imagen assets/interfaz/logo.png ('Poké' amarillo y MANIC en Unown) agrandada sin suavizar. Los Unown
        flotan un poco, cada uno a su tiempo, y cada tanto un brillo cruza el 'Poké'. donde: como en get_rect (center=..., topright=...).
        Si falta la imagen, el logo armado con las letras del PMD. Devuelve el rectangulo que ocupa."""
        escala = max(2, round(alto / 24))
        partes, tam = _partes_logo(escala)
        if not partes: return _logo_letras(ventana, alto, ahora, **donde)
        caja = pygame.Rect(0, 0, *tam)
        for clave, valor in donde.items(): setattr(caja, clave, valor)
        for i, (x, pieza, sombra, brillo) in enumerate(partes):
            y = caja.y + (round(math.sin(ahora / 450 + i * 1.3) * alto * 0.05) if i else 0)   # 'Poké' quieto, los Unown flotan
            ventana.blit(sombra, (caja.x + x + escala, y + escala * 2)); ventana.blit(pieza, (caja.x + x, y))
            pasa = (ahora % 3600) / 520 * (tam[0] + 120) - 60 - x                    # el brillo: una franja que cruza todo el logo
            franja = pygame.Rect(round(pasa), 0, 14 * escala, pieza.get_height()).clip(pieza.get_rect())
            if franja.width > 0: ventana.blit(brillo, (caja.x + x + franja.x, y), franja)
        return caja


    def animacion(ventana, nombre, centro, lado, t, ms=60):
        """Un efecto de assets/efectos (tira de cuadros) que pasa una sola vez: t = ms desde que arranco. False si no esta o ya termino."""
        cuadros = efectos._frames(nombre, lado)
        if not cuadros or not 0 <= t < len(cuadros) * ms: return False
        cuadro = cuadros[int(t // ms)]
        ventana.blit(cuadro, cuadro.get_rect(center=centro))
        return True


    def _logo_letras(ventana, alto, ahora, **donde):
        """El logo armado con letras (si falta la imagen): POKE con la letra de los titulos del PMD (amarilla con borde azul) y MANIC con
        letras Unown de HGSS que flotan un poco. donde: como en get_rect. Si faltan las hojas, el logo dibujado."""
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


    # estados que tienen animacion del Red Rescue Team (assets/efectos/estado_<nombre>.png, 'python herramientas.py estados')
    ESTADO_ANIMADO = {'quemar': 'estado_quemar', 'veneno': 'estado_veneno', 'dormir': 'estado_dormir', 'ralentizar': 'estado_lento',
                      'confusion': 'estado_confuso', 'confundir': 'estado_confuso', 'aturdido': 'estado_confuso'}


    def icono_estado(ventana, estado, centro, escala=2):
        """Icono de estado de BW (BRN, PAR, FRZ...) centrado en 'centro', con la animacion del PMD encima (la llama, la calavera...).
        Dormido, frenado y confundido no tienen icono en BW: va solo la animacion (o, si falta, se escribe)."""
        nombre = ESTADO_ICONO.get(estado)
        img = hud(nombre, escala) if nombre else None
        animado = ESTADO_ANIMADO.get(estado)                            # la animacion del PMD: arriba del icono de BW, o sola si no hay icono
        arriba = (centro[0], centro[1] - (20 if img else 4))
        if animado and entorno._loop(ventana, animado, arriba, 32, pygame.time.get_ticks(), 110) and not img: return
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
    _viaje = {'cuadros': None, 'apertura': None, 'fondo': None, 'capas': None}
    COSMOS = {'ms': 240, 'alfa': 165}               # el tunel: ms por cuadro de la capa que se mueve (antes 90) y que tan marcada se ve


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


    def fondo_viaje(ui, ahora, fase=None):
        """El tunel del viaje temporal del Explorers of Sky: el cosmos quieto (viaje_fondo.png) y encima, medio transparente, la capa de
        cuadrados y rayas que va pasando despacio y fundiendo un cuadro con el siguiente (viaje_capa_<n>.png). Los recorta:
        python herramientas.py viaje. fase: por que cuadro va (si no se da, sale del reloj); asi la escena lo acelera o lo frena.
        Si faltan, los cuadros del tunel de antes; y si tampoco, rayos girando sobre azul oscuro."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        if _viaje['fondo'] is None:
            ruta = os.path.join(FONDOS, 'viaje_fondo.png')
            _viaje['fondo'] = pygame.transform.smoothscale(pygame.image.load(ruta).convert(), (W, H)) if os.path.isfile(ruta) else False
            _viaje['capas'] = []
            for i in range(12):
                ruta = os.path.join(FONDOS, 'viaje_capa_' + str(i) + '.png')
                if not os.path.isfile(ruta): break
                _viaje['capas'].append(pygame.transform.smoothscale(pygame.image.load(ruta).convert_alpha(), (W, H)))
        if _viaje['fondo'] and _viaje['capas']:
            ventana.blit(_viaje['fondo'], (0, 0))
            paso, mezcla = divmod(ahora / COSMOS['ms'] if fase is None else fase, 1)
            capas = _viaje['capas']
            for capa, alfa in ((capas[int(paso) % len(capas)], 1 - mezcla), (capas[(int(paso) + 1) % len(capas)], mezcla)):
                capa.set_alpha(round(COSMOS['alfa'] * alfa)); ventana.blit(capa, (0, 0))
            return
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


    # ---------- el borde del cosmos: la partida nueva y los viajes entre eras ----------
    # Todo con piezas del PMD: el tunel del viaje temporal (Explorers of Sky) es el cosmos, tu espiritu es el brillo del Red Rescue Team,
    # el "!" es el de los estados, Celebi usa sus animaciones (Float, Twirl, Pull...) y sus caras del retrato (las baja 'herramientas.py caras celebi').

    CARAS_CELEBI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sprites', 'pokemones', 'sprite_celebi', 'portrait')
    _caras, _portal = {}, {}


    def cara_celebi(ui, emocion, lado=80):
        """El retrato de Celebi con esa cara (Happy, Surprised, Worried...). Si falta, el normal."""
        if (emocion, lado) not in _caras:
            ruta, img = os.path.join(CARAS_CELEBI, emocion + '.png'), None
            if os.path.isfile(ruta):
                try: img = pygame.transform.scale(pygame.image.load(ruta).convert_alpha(), (lado, lado))
                except pygame.error: img = None
            _caras[(emocion, lado)] = img or ui['retrato']('celebi', lado)
        return _caras[(emocion, lado)]


    def portal(ventana, centro, radio, ahora, cierre=None):
        """El portal del tiempo: el agujero dimensional violeta del Explorers of Time/Darkness (assets/efectos/portal.png, lo arma
        'python herramientas.py portal'). Abierto late (cuadros 1 a 4); al cerrarse se agrieta y se rompe en pedazos (5 a 8).
        radio: la mitad del ancho del agujero; cierre: None abierto, 0 a 1 mientras se rompe. Si falta, el ovalo de antes."""
        radio = round(radio)
        if radio < 3 or (cierre is not None and cierre >= 1): return
        cuadros = efectos._tira('portal')
        if cuadros and len(cuadros) >= 8:
            lado = max(8, round(radio * 2 * 112 / 80 / 8) * 8)            # (el agujero mide 80 de los 112 del cuadro)
            i = (ahora // 150) % 4 if cierre is None else 4 + min(3, int(cierre * 4))
            img = efectos._frames('portal', lado)[i]
            ventana.blit(img, img.get_rect(center=(round(centro[0]), round(centro[1]))))
            brillo = efectos._frames('brillo', 24)
            if brillo and cierre is None:                                 # unos brillitos alrededor
                for k in range(3):
                    ang = ahora / 900 + k * math.tau / 3
                    b = brillo[(ahora // 120 + k) % len(brillo)]
                    ventana.blit(b, b.get_rect(center=(round(centro[0] + math.cos(ang) * radio * 1.05), round(centro[1] + math.sin(ang) * radio * 0.85))))
            return
        W, H = ventana.get_size()
        if _viaje['cuadros'] is None: _viaje['cuadros'] = _cuadros_viaje('viaje', 12, W, H)
        ancho, alto = radio * 2, max(2, round(radio * 1.6))
        disco = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        if _viaje['cuadros']: disco.blit(pygame.transform.smoothscale(_viaje['cuadros'][int(ahora // COSMOS['ms']) % len(_viaje['cuadros'])], (ancho, alto)), (0, 0))
        else: disco.fill((70, 150, 230))
        if (ancho, alto) not in _portal:
            m = pygame.Surface((ancho, alto), pygame.SRCALPHA); pygame.draw.ellipse(m, (255, 255, 255, 255), m.get_rect()); _portal[(ancho, alto)] = m
        disco.blit(_portal[(ancho, alto)], (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        ventana.blit(disco, disco.get_rect(center=centro))
        anillo = efectos._frames('cambio', 64)
        if anillo:
            a = pygame.transform.scale(anillo[(ahora // 140) % 2], (round(ancho * 1.22), round(alto * 1.22)))
            ventana.blit(a, a.get_rect(center=centro))
        brillo = efectos._frames('brillo', 30)
        if brillo:
            for k in range(5):
                ang = ahora / 700 + k * math.tau / 5
                b = brillo[(ahora // 110 + k) % len(brillo)]
                ventana.blit(b, b.get_rect(center=(round(centro[0] + math.cos(ang) * ancho * 0.6), round(centro[1] + math.sin(ang) * alto * 0.6))))


    ESTELA_COSMOS = {'cada': 90, 'dura': 260, 'alfa': 70, 'fondo': 26}   # dos copias como mucho: cada cuanto se deja una, cuanto tarda
                                                    # en irse, que tan fuerte y cuanto se corren hacia el fondo del cosmos
    _aura = {}


    def _aura_de(lado, nivel=1.0, nucleo=False):
        """El resplandor de assets/efectos/aura.png (la luz de Moonlight, 'python herramientas.py espiritu') de un tamaño: celeste
        casi blanco (o blanco, el nucleo), transparente segun cuanta luz tiene cada punto y mas apagado segun 'nivel'."""
        clave = (lado, round(nivel * 10), nucleo)
        if clave not in _aura:
            if 'base' not in _aura:                                      # una vez: de azul a celeste blanco, segun cuanta luz tiene cada pixel
                hoja = (efectos._tira('aura') or [None])[0]
                if hoja is None: _aura['base'] = None
                else:
                    tope = max(hoja.get_at((x, y))[2] for x in range(hoja.get_width()) for y in range(hoja.get_height())) or 1
                    for clase, color in (('base', (200, 236, 255)), ('blanco', (255, 255, 255))):
                        s = pygame.Surface(hoja.get_size(), pygame.SRCALPHA)
                        for x in range(hoja.get_width()):
                            for y in range(hoja.get_height()):
                                c = hoja.get_at((x, y))[2] / tope
                                s.set_at((x, y), (*color, round(255 * c ** 1.8)))   # (mas suave hacia el borde)
                        _aura[clase] = s
            base = _aura['blanco' if nucleo else 'base']
            if base is None: _aura[clave] = None
            else:
                img = pygame.transform.smoothscale(base, (lado, lado))
                if nivel < 1: img.fill((255, 255, 255, round(255 * nivel)), special_flags=pygame.BLEND_RGBA_MULT)
                _aura[clave] = img
        return _aura[clave]


    def espiritu(ventana, pos, esc, ahora, hacia=None, rapidez=0.0):
        """Tu espiritu: una luz redonda con su aura y, encima, el brillito del PMD titilando. El aura se estira hacia 'hacia' (el fondo
        del cosmos: el cosmos va para atras y la luz para adelante), mas cuanto mas rapido va. esc: 0 lejisimos, 1 adelante."""
        lado = max(8, round(125 * esc / 8) * 8)
        x, y = pos
        if _aura_de(lado) is None: return
        if hacia and lado > 16:
            dx, dy = hacia[0] - x, hacia[1] - y; n = math.hypot(dx, dy)
            if n > 4:
                dx, dy = dx / n, dy / n
                paso = (8 + min(16, rapidez * 2.4)) * max(esc, 0.3)
                for i in (5, 4, 3, 2, 1):                                 # la cola del aura, cada vez mas chica y apagada
                    img = _aura_de(max(8, round(lado * (1 - i * 0.11) / 8) * 8), 0.6 * (1 - i * 0.16))
                    ondea = math.sin(ahora / 300 + i * 0.8) * i * 1.2       # (se mece un poco, como una llama)
                    ventana.blit(img, img.get_rect(center=(round(x + dx * paso * i - dy * ondea), round(y + dy * paso * i + dx * ondea))))
        late = 1 + 0.06 * math.sin(ahora / 260)
        aura = _aura_de(max(8, round(lado * late / 8) * 8), 0.75)
        ventana.blit(aura, aura.get_rect(center=(round(x), round(y))))
        nucleo = _aura_de(max(8, round(lado * 0.32 / 8) * 8), 0.95, True)
        ventana.blit(nucleo, nucleo.get_rect(center=(round(x), round(y))))
        estrella = efectos._frames('estrellita', max(6, round(lado * 0.5 / 6) * 6)) or efectos._frames('brillo', max(6, round(lado * 0.38 / 6) * 6))
        if estrella:                                                      # la estrellita del medio, titilando
            b = estrella[(ahora // 140) % len(estrella)]
            ventana.blit(b, b.get_rect(center=(round(x), round(y))))


    def _copia_apagada(img, _cache={}):
        """La copia de la estela: en gris y oscurecida (sin color ni brillo), guardada para no rehacerla."""
        if id(img) not in _cache:
            gris = pygame.transform.grayscale(img)
            gris.fill((150, 150, 165), special_flags=pygame.BLEND_RGB_MULT)
            _cache[id(img)] = gris
        return _cache[id(img)]


    def dejar_estela(estela, img, x, y, ahora):
        """Deja una copia en la estela si ya paso un rato desde la ultima (asi nunca hay mas de dos)."""
        if not estela or ahora - estela[-1][3] >= ESTELA_COSMOS['cada']: estela.append((img, x, y, ahora))
        del estela[:-2]


    def dibujar_estela(ventana, estela, ahora, fondo=None):
        """Las copias de la estela, cada vez mas transparentes hasta que se van, corriendose hacia el fondo del cosmos."""
        for img, x, y, cuando in estela[:]:
            edad = (ahora - cuando) / ESTELA_COSMOS['dura']
            if edad >= 1: estela.remove((img, x, y, cuando)); continue
            if fondo:
                dx, dy = fondo[0] - x - img.get_width() / 2, fondo[1] - y - img.get_height() / 2; n = math.hypot(dx, dy) or 1
                x, y = x + dx / n * edad * ESTELA_COSMOS['fondo'], y + dy / n * edad * ESTELA_COSMOS['fondo']
            copia = _copia_apagada(img); copia.set_alpha(round(ESTELA_COSMOS['alfa'] * (1 - edad)))
            ventana.blit(copia, (round(x), round(y)))


    def _mira(dx, dy):
        """La direccion del sprite (0 abajo, 2 derecha, 4 arriba, 6 izquierda) para mirar hacia (dx, dy)."""
        return round((90 - math.degrees(math.atan2(dy, dx))) / 45) % 8 if dx or dy else 0


    def _suave(k):
        k = max(0.0, min(1.0, k))
        return k * k * k * (k * (k * 6 - 15) + 10)


    def _rapido(k):
        """Arranca rapido y se pasa un poquito antes de frenar (los movimientos de golpe de Celebi)."""
        k = max(0.0, min(1.0, k)); s = 1.6
        return 1 + (s + 1) * (k - 1) ** 3 + s * (k - 1) ** 2


    def viaje_temporal(ui):
        """Partida nueva en el borde del cosmos. Negro, y muy lejos un brillo; se abre el tiempo (la apertura del Explorers of Time) y
        aparece el cosmos. Tu espiritu (el brillo) se acerca serpenteando como una hoja; Celebi llega dando vueltas, pasa por la luz, sale
        de cuadro, aparece un "!" y vuelve. Te rodea, te habla (cambia de lugar y de cara), te pregunta tu nombre y tu genero (desde ahi
        los textos van segun el genero) y te pide que te materialices: elegis tu pokemon viendo su sombra, que se transforma al cambiar,
        y al elegir se materializa entre estrellas. Celebi abre el portal y se van juntos; todo se apaga.
        Devuelve {'nombre', 'genero', 'inicial'}, None si volves con ESC o 'salir'."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        reloj = pygame.time.Clock()
        FONDO_CENTRO = (W // 2, H // 2 - 40)                             # el punto de fuga del tunel (de ahi viene todo)
        ARRIBA, DERECHA, IZQUIERDA = (W // 2, 140), (W // 2 + 200, 175), (W // 2 - 200, 175)
        AL_COSTADO = (W - 150, 215)                                      # donde queda Celebi mientras elegis tu forma
        celebi = AnimadorPokemon('celebi', pygame.Rect(0, 0, 10, 10), 96) if tiene_sprites('celebi') else None
        e = {'fondo': 'negro', 'oscuro': 0, 'luz': None, 'cel': None, 'alerta': None, 'portal': 0, 'cierre': None, 'cuerpo': None, 'sombra': None,
             'blanco': 0, 'anims': [], 'habla': False, 'cara': 'Normal', 'fase': 0.0, 'vel': 1.0, 'antes': None}
        estela = []                                                      # [(imagen, x, y, cuando)] lo que van dejando atras
        caja_dialogo = pygame.Rect(40, H - 168, W - 80, 140)

        # ----- dibujo -----
        def brillo(centro, lado, ahora, alfa=255, fase=0):
            """Dibuja el brillo del PMD (tu espíritu) de un tamaño, con su titileo."""
            cuadros = efectos._frames('brillo', max(6, round(lado / 6) * 6))
            if not cuadros: return
            b = cuadros[(ahora // 110 + fase) % len(cuadros)]
            if alfa < 255: b = b.copy(); b.set_alpha(alfa)
            ventana.blit(b, b.get_rect(center=(round(centro[0]), round(centro[1]))))

        def actor(a, pos, esc, direccion, anim):
            """Dibuja un pokemon (agrandado o achicado) y devuelve (imagen, x, y) para la estela."""
            if not a.cambiar(anim, direccion, True): a.cambiar('idle', direccion, True)
            a.rect.center = (round(pos[0]), round(pos[1])); a.actualizar()
            c = a.cuadro()
            if not c: return None
            img, x, y = c
            if esc != 1:
                img = pygame.transform.scale(img, (max(1, round(img.get_width() * esc)), max(1, round(img.get_height() * esc))))
                x, y = pos[0] - (pos[0] - x) * esc, pos[1] - (pos[1] - y) * esc
            ventana.blit(img, (round(x), round(y)))
            return img, x, y

        def dibujar(ahora):
            """Dibuja la escena del cosmos entera: fondo, portal, estelas, tu luz o tu cuerpo, Celebi, el '!' y los efectos."""
            dt = 0 if e['antes'] is None else min(50, ahora - e['antes']); e['antes'] = ahora
            e['fase'] += dt / COSMOS['ms'] * e['vel']                    # el cosmos a su velocidad (la escena lo acelera o lo frena)
            if e['fondo'] == 'negro': ventana.fill((0, 0, 0))
            else: fondo_viaje(ui, ahora, e['fase'])
            oscuro = max(e['oscuro'], 0 if e['fondo'] == 'negro' else 70)      # el cosmos un poco apagado: que se lean Celebi y tu luz
            if oscuro: velo = pygame.Surface((W, H)); velo.fill((6, 8, 30)); velo.set_alpha(oscuro); ventana.blit(velo, (0, 0))
            if e['portal'] > 2: portal(ventana, (W // 2, 150), e['portal'], ahora, e['cierre'])
            dibujar_estela(ventana, estela, ahora, FONDO_CENTRO)          # la estela: dos copias apagadas que se van hacia el fondo
            if e['luz'] and not e['cuerpo']:                             # tu espiritu (o tu sombra, si estas eligiendo)
                l = e['luz']
                if e['sombra']: dibujar_sombra(ahora)
                previo = l.get('ultimo', tuple(l['pos'])); l['ultimo'] = tuple(l['pos'])
                l['rapidez'] = l.get('rapidez', 0) * 0.85 + math.hypot(l['pos'][0] - previo[0], l['pos'][1] - previo[1]) * 0.15
                if e['fondo'] == 'negro': brillo(l['pos'], 14 * l['esc'] / 0.12, ahora, round(255 * min(1.0, l['esc'] / 0.06)))   # a lo lejos, solo el brillito
                else: espiritu(ventana, l['pos'], l['esc'] * (0.55 if e['sombra'] else 1), ahora, FONDO_CENTRO, l['rapidez'] + e['vel'])
            if e['cuerpo']:
                c = e['cuerpo']; actor(c['a'], c['pos'], 1.0, 0, c.get('anim', 'idle'))
                if e['blanco'] > 0: dibujar_sombra(ahora, (255, 255, 255), e['blanco'], c['a'])
            if celebi and e['cel']:
                c = e['cel']
                previo = c.get('ultimo', tuple(c['pos']))
                dx, dy = c['pos'][0] - previo[0], c['pos'][1] - previo[1]
                if math.hypot(dx, dy) > 1.2: c['dir'] = _mira(dx, dy)
                elif c.get('mira'): c['dir'] = _mira(c['mira'][0] - c['pos'][0], c['mira'][1] - c['pos'][1])
                vivo = (math.sin(ahora / 730) * 5 + math.sin(ahora / 1270) * 3, math.sin(ahora / 480) * 6 + math.sin(ahora / 910) * 3)   # flota y se mece
                pos = (c['pos'][0] + vivo[0], c['pos'][1] + vivo[1] - (abs(math.sin(ahora / 70)) * 3 if e['habla'] else 0))
                hecho = actor(celebi, pos, c['esc'], c.get('dir', 0), c.get('anim', 'float'))
                if hecho and math.hypot(dx, dy) > 1.5: dejar_estela(estela, hecho[0], hecho[1], hecho[2], ahora)
                c['ultimo'] = tuple(c['pos'])
            if e['alerta']:                                              # el "!" de cuando Celebi te ve
                pos, desde = e['alerta']
                animacion(ventana, 'estado_alerta', pos, round(54 * min(1.0, (ahora - desde) / 150 + 0.4)), (ahora - desde) % 900, 100)
            for nombre, centro, lado, desde, ms in e['anims'][:]:
                if not animacion(ventana, nombre, centro, lado, ahora - desde, ms) and ahora - desde > 0: e['anims'].remove((nombre, centro, lado, desde, ms))
            if e['blanco'] and not e['cuerpo']:
                velo = pygame.Surface((W, H)); velo.fill((255, 255, 255)); velo.set_alpha(e['blanco']); ventana.blit(velo, (0, 0))

        def dibujar_sombra(ahora, color=(12, 12, 28), alfa=255, a=None):
            """La sombra del pokemon que estas eligiendo (o el blanco que lo cubre al materializarse), con la transformacion al cambiar."""
            k = 1.0
            if a is None:                                                 # la sombra que estas eligiendo, donde esta tu espiritu
                a, k = e['sombra']['a'], e['sombra'].get('escala', 1.0)
                a.cambiar('idle', 0, True); a.rect.center = (round(e['luz']['pos'][0]), round(e['luz']['pos'][1])); a.actualizar()
            c = a.cuadro()
            if not c: return
            img, x, y = c
            mascara = pygame.mask.from_surface(img).to_surface(setcolor=(*color, alfa), unsetcolor=(0, 0, 0, 0))
            if k != 1:
                cx_, cy_ = x + img.get_width() / 2, y + img.get_height() / 2
                mascara = pygame.transform.scale(mascara, (max(1, round(img.get_width() * k)), max(1, round(img.get_height() * k))))
                x, y = cx_ - mascara.get_width() / 2, cy_ - mascara.get_height() / 2
            if color != (255, 255, 255):                                  # un borde de luz atras, para que se lea sobre el cosmos
                borde = pygame.mask.from_surface(img).to_surface(setcolor=(220, 255, 240, 90), unsetcolor=(0, 0, 0, 0))
                borde = pygame.transform.scale(borde, (mascara.get_width() + 8, mascara.get_height() + 8))
                ventana.blit(borde, (round(x) - 4, round(y) - 4))
            ventana.blit(mascara, (round(x), round(y)))

        # ----- tiempo -----
        def correr(ms, mover=None):
            """Deja correr la escena ms milisegundos llamando a mover(k, ahora) (k de 0 a 1). Una tecla la adelanta al final.
            'ok', None si ESC o 'salir'."""
            inicio = pygame.time.get_ticks()
            while True:
                ahora = pygame.time.get_ticks()
                for ev in controles.eventos():
                    if ev.type == pygame.QUIT: return 'salir'
                    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None
                    if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): inicio = ahora - ms
                k = min(1.0, (ahora - inicio) / max(1, ms))
                if mover: mover(k, ahora)
                dibujar(ahora)
                ui['presentar'](); reloj.tick(60)
                if k >= 1: return 'ok'

        def ir(destino, ms, esc=None, anim=None, mira=None, curva=0.0, rapido=False):
            """Celebi va a 'destino' en ms: suave (arranca y frena despacio) o rapido (sale disparado y se pasa un poquito)."""
            c = e['cel']; x0, y0, e0 = c['pos'][0], c['pos'][1], c['esc']
            if anim: c['anim'] = anim
            c['mira'] = mira
            def mover(k, ahora):
                """Un paso del movimiento de Celebi en la escena (de k = 0 a 1)."""
                s = _rapido(k) if rapido else _suave(k)
                c['pos'] = [x0 + (destino[0] - x0) * s + math.sin(s * math.pi) * curva, y0 + (destino[1] - y0) * s]
                if esc is not None: c['esc'] = e0 + (esc - e0) * s
            return correr(ms, mover)

        def rodear(centro, ms, rx=170, ry=105, vueltas=1.0, desde=None, rapido=False):
            """Celebi da vueltas alrededor de un punto mirandolo, desde donde esta (suave, o de golpe si es rapido)."""
            c = e['cel']; c['anim'] = 'float'; c['mira'] = centro
            x0, y0 = c['pos']
            if desde is None: desde = math.atan2((y0 - centro[1]) / ry, (x0 - centro[0]) / rx)
            def mover(k, ahora):
                """Un paso del movimiento de Celebi en la escena (de k = 0 a 1)."""
                ang = desde + (_rapido(k) if rapido else _suave(k)) * math.tau * vueltas
                lugar = (centro[0] + math.cos(ang) * rx, centro[1] + math.sin(ang) * ry)
                entra = min(1.0, k * 6)                                   # el primer pedacito: de donde estaba al circulo
                c['pos'] = [x0 + (lugar[0] - x0) * entra, y0 + (lugar[1] - y0) * entra]
            return correr(ms, mover)

        # ----- dialogos -----
        def caja_de_celebi(texto, cuanto):
            """La caja de diálogo con la cara de Celebi y el texto que va apareciendo."""
            caja(ventana, caja_dialogo, 'panel', OSCURO, 2, (220, 220, 220))
            x = caja_dialogo.x + 20
            cara = cara_celebi(ui, e['cara'])
            if cara: ventana.blit(cara, (x, caja_dialogo.y + 30)); x += 100
            ventana.blit(fuente(30).render('Celebi', True, (150, 240, 140)), (x, caja_dialogo.y + 10))
            for k, linea in enumerate(ajustar_texto(texto[:cuanto], fuente(30), caja_dialogo.right - x - 40)[:3]):
                ventana.blit(fuente(30).render(linea, True, 'white'), (x, caja_dialogo.y + 46 + k * 28))
            return x

        def decir(texto, cara='Normal', opciones_=None, anim=None):
            """Celebi dice algo con esa cara (letra por letra; mientras habla se mueve un poquito). Con opciones_ devuelve el indice."""
            e['cara'] = cara
            if anim and e['cel']: e['cel']['anim'] = anim
            inicio, elegido = pygame.time.get_ticks(), 0
            botones = [pygame.Rect(W - 380, caja_dialogo.y - 16 - (len(opciones_ or ()) - k) * 52, 340, 44) for k in range(len(opciones_ or ()))]
            while True:
                ahora = pygame.time.get_ticks()
                cuanto = (ahora - inicio) * 45 // 1000
                completo = cuanto >= len(texto)
                e['habla'] = not completo
                for ev in controles.eventos():
                    if ev.type == pygame.QUIT: return 'salir'
                    elegir = None
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE: return None
                        if opciones_ and completo and ev.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(opciones_)
                        if opciones_ and completo and ev.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(opciones_)
                        if ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE): elegir = elegido
                    if ev.type == pygame.MOUSEMOTION and completo:
                        for k, b in enumerate(botones):
                            if b.collidepoint(ui['a_logico'](ev.pos)): elegido = k
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1: elegir = elegido
                    if elegir is None: continue
                    if not completo: inicio = -10 ** 7; continue
                    e['habla'] = False
                    if e['cel']: e['cel']['anim'] = 'float'
                    return elegir if opciones_ else 0
                dibujar(ahora)
                caja_de_celebi(texto, cuanto)
                if completo and opciones_:
                    for k, b in enumerate(botones): boton(ventana, b, opciones_[k], k == elegido, 30)
                elif completo and (ahora // 400) % 2:
                    pygame.draw.polygon(ventana, 'white', [(caja_dialogo.right - 34, caja_dialogo.bottom - 24), (caja_dialogo.right - 20, caja_dialogo.bottom - 24),
                                                           (caja_dialogo.right - 27, caja_dialogo.bottom - 16)])
                ui['presentar'](); reloj.tick(60)

        def escribir_nombre(pregunta):
            """Celebi te pregunta el nombre y lo escribís en la caja."""
            nombre = ''
            e['cara'] = 'Happy'
            while True:
                ahora = pygame.time.get_ticks()
                for ev in controles.eventos():
                    if ev.type == pygame.QUIT: return 'salir'
                    if ev.type != pygame.KEYDOWN: continue
                    if ev.key == pygame.K_ESCAPE: return None
                    if ev.key == pygame.K_RETURN and nombre.strip(): return nombre.strip()
                    if ev.key == pygame.K_BACKSPACE: nombre = nombre[:-1]
                    elif ev.unicode and ev.unicode.isprintable() and len(nombre) < LARGO_NOMBRE: nombre += ev.unicode
                dibujar(ahora)
                x = caja_de_celebi(pregunta, len(pregunta))
                campo = pygame.Rect(x, caja_dialogo.y + 82, 360, 44)
                caja(ventana, campo, 'boton_elegido', (60, 60, 90), 2)
                texto_ = fuente(32).render(nombre or 'escribí tu nombre', True, 'white' if nombre else (170, 170, 200))
                lugar = texto_.get_rect(midleft=(campo.x + 16, campo.centery)); ventana.blit(texto_, lugar)
                if nombre and (ahora // 500) % 2: pygame.draw.line(ventana, 'white', (lugar.right + 3, campo.y + 9), (lugar.right + 3, campo.bottom - 9), 2)
                listo = fuente(24).render('ENTER: listo', True, (210, 210, 220)); ventana.blit(listo, listo.get_rect(midleft=(campo.right + 16, campo.centery)))
                ui['presentar'](); reloj.tick(60)

        # ----- elegir tu forma (la sombra) -----
        def elegir_forma():
            """Elegis que pokemon eras viendo su sombra donde esta tu espiritu (la sombra se encoge y crece distinta al cambiar).
            A la derecha, que hace y en que se convierte. Devuelve el nombre, None o 'salir'."""
            animadores = [AnimadorPokemon(n, pygame.Rect(0, 0, 10, 10), 150) for n in INICIALES]
            finales = [_evolucion_final(n) for n in INICIALES]
            elegido, cambio = 1, pygame.time.get_ticks()
            e['sombra'] = {'a': animadores[elegido], 'escala': 1.0}
            info = pygame.Rect(40, 96, 400, 250)
            while True:
                ahora = pygame.time.get_ticks()
                for ev in controles.eventos():
                    if ev.type == pygame.QUIT: return 'salir'
                    nuevo = None
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE: return None
                        if ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w): nuevo = (elegido - 1) % len(INICIALES)
                        if ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s): nuevo = (elegido + 1) % len(INICIALES)
                        if pygame.K_1 <= ev.key < pygame.K_1 + len(INICIALES): nuevo = ev.key - pygame.K_1
                        if ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE) and ahora - cambio > 300: return INICIALES[elegido]
                    if ev.type == pygame.MOUSEWHEEL: nuevo = (elegido - ev.y) % len(INICIALES)
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and ahora - cambio > 300: return INICIALES[elegido]
                    if nuevo is not None and nuevo != elegido:
                        elegido, cambio = nuevo, ahora
                        e['anims'].append(('cambio', tuple(e['luz']['pos']), 200, ahora, 45))
                t = ahora - cambio                                       # la sombra vieja se encoge y crece la nueva
                e['sombra']['a'] = animadores[elegido]
                e['sombra']['escala'] = 1.0 if t > 420 else max(0.05, 1 - t / 160) if t < 160 else _suave((t - 160) / 260)
                dibujar(ahora)
                nombre = INICIALES[elegido]
                panel_flecha(ventana, (info.x, info.y, info.width, 54), (0, 1))
                ventana.blit(tipografia.fuente_titulo(2).render(nombre.title(), True, 'white'), (info.x + 22, info.y + 8))
                x = info.right - 20
                for tipo in reversed(pokemones[nombre].get('tipo', [])):
                    tipo = normalizar_tipo(tipo); x -= fuente(20).size(str(tipo).upper())[0] + 20
                    chip_tipo(ventana, tipo, x, info.y + 14)
                cuerpo = pygame.Rect(info.x, info.y + 62, info.width, info.height - 62)
                caja(ventana, cuerpo, 'panel', OSCURO, 2, (220, 220, 220))
                ventana.blit(fuente(24).render('Rol: ' + ROL_POKEMON.get(nombre, '-'), True, (255, 236, 150)), (cuerpo.x + 16, cuerpo.y + 10))
                for k, linea in enumerate(ajustar_texto(ESTILO_INICIAL.get(nombre, '') + '. ' + (mecanicas.texto_de(nombre) or ''), fuente(20), cuerpo.width - 32)[:6]):
                    ventana.blit(fuente(20).render(linea, True, (225, 225, 235)), (cuerpo.x + 16, cuerpo.y + 38 + k * 19))
                abajo = pygame.Rect(info.x, info.bottom + 10, info.width, 74)       # en que se convierte
                caja(ventana, abajo, 'panel', OSCURO, 2, (220, 220, 220))
                cara, cara_f = ui['retrato'](nombre, 52), ui['retrato'](finales[elegido], 52)
                if cara: ventana.blit(cara, (abajo.x + 20, abajo.y + 11))
                flecha = fuente(30).render('>', True, (255, 236, 150)); ventana.blit(flecha, flecha.get_rect(center=(abajo.x + 98, abajo.centery)))
                if cara_f: ventana.blit(cara_f, (abajo.x + 124, abajo.y + 11))
                ventana.blit(fuente(20).render('Llega a ser', True, (200, 200, 215)), (abajo.x + 190, abajo.y + 16))
                ventana.blit(fuente(26).render(finales[elegido].replace('_', ' ').title(), True, 'white'), (abajo.x + 190, abajo.y + 36))
                pista = fuente(24).render('<  ' + str(elegido + 1) + ' / ' + str(len(INICIALES)) + '  >', True, (230, 240, 255))
                ventana.blit(pista, pista.get_rect(midtop=(round(e['luz']['pos'][0]), round(e['luz']['pos'][1]) + 96)))
                pie(ventana, 'izq/der: cambiar   ENTER: este soy yo   ESC: volver')
                ui['presentar'](); reloj.tick(60)

        # ===== 1. negro: muy lejos, un brillo =====
        e['luz'] = {'pos': [FONDO_CENTRO[0], FONDO_CENTRO[1]], 'esc': 0.0}
        def a_lo_lejos(k, ahora):
            e['luz']['esc'] = 0.0 if k < 0.4 else 0.12 * min(1.0, (k - 0.4) / 0.06) * (0.8 + 0.2 * math.sin(ahora / 160))   # aparece de golpe, lejisimos
        r = correr(2800, a_lo_lejos)
        if r != 'ok': return r
        # ===== 2. se abre el tiempo (la apertura del Explorers of Time) y aparece el cosmos =====
        if _viaje['apertura'] is None: _viaje['apertura'] = _cuadros_viaje('apertura', 22, W, H)
        for cuadro in _viaje['apertura']:
            for ev in controles.eventos():
                if ev.type == pygame.QUIT: return 'salir'
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None
            ventana.blit(cuadro, (0, 0)); ui['presentar'](); reloj.tick(15)
        e['fondo'], e['blanco'], e['luz']['esc'], e['vel'] = 'cosmos', 255, 0.05, 1.0
        r = correr(700, lambda k, a: e.update(blanco=round(255 * (1 - k))))
        if r != 'ok': return r
        # ===== 3. tu espiritu se acerca de fondo, despacio, meciendose como una hoja que cae de costado =====
        def hoja(k, ahora):
            """Tu espíritu acercándose de fondo, serpenteando como una hoja que cae de costado."""
            l = e['luz']; s = _suave(k)
            l['esc'] = 0.05 + 0.95 * s ** 1.4
            vaiven = math.sin(k * math.pi * 2.6)                          # va y viene de costado, cada vez menos
            l['pos'] = [FONDO_CENTRO[0] + vaiven * 230 * (1 - s) ** 0.8,
                        FONDO_CENTRO[1] + (345 - FONDO_CENTRO[1]) * s - abs(vaiven) * 22 * (1 - s)]   # (en las puntas del vaiven sube un poco, como una hoja)
            e['vel'] = 1.0 + 0.5 * math.sin(k * math.pi)
        r = correr(6500, hoja)
        if r != 'ok': return r
        e['vel'] = 1.0
        VOS = [W // 2, 345]; e['luz']['pos'] = list(VOS)               # un poco abajo del resplandor del centro, asi se ve su aura
        # ===== 4. Celebi llega de lejos dando vueltas, pasa por la luz y se va de cuadro =====
        if celebi:
            e['cel'] = {'pos': [W * 0.22, H * 0.2], 'esc': 0.2, 'anim': 'twirl'}
            def vueltas(k, ahora):
                """Celebi llega de lejos dando vueltas en espiral y pasa por la luz."""
                c = e['cel']
                if k < 0.62:                                              # en espiral, acercandose (de lejos va lento, de cerca rapido)
                    kk = (k / 0.62) ** 1.5; ang = kk * math.tau * 1.6; e['vel'] = 1.0 + kk * 0.6
                    centro = (W * 0.22 + (W * 0.62 - W * 0.22) * kk, H * 0.2 + (H * 0.36 - H * 0.2) * kk)
                    radio = 130 * (1 - kk * 0.5)
                    c['pos'] = [centro[0] + math.cos(ang) * radio, centro[1] + math.sin(ang) * radio * 0.6]; c['esc'] = 0.2 + 0.6 * kk; c['anim'] = 'twirl'
                else:                                                     # pasa rozando la luz y sale por la derecha
                    kk = (k - 0.62) / 0.38; inicio = (W * 0.62 + 130 * 0.5 * math.cos(math.tau * 1.6), H * 0.36)
                    c['pos'] = [inicio[0] + (VOS[0] - 60 - inicio[0]) * min(1, kk * 2) + max(0, kk * 2 - 1) * (W + 140 - VOS[0] + 60),
                                inicio[1] + (VOS[1] - 30 - inicio[1]) * min(1, kk * 2)]
                    c['esc'] = 0.8 + 0.2 * kk; c['anim'] = 'float'; e['vel'] = 2.0 - kk
            r = correr(4600, vueltas)
            if r != 'ok': return r
            e['vel'] = 1.0
            e['alerta'] = ((W - 46, VOS[1] - 50), pygame.time.get_ticks())   # se dio cuenta: "!"
            r = correr(1000)
            if r != 'ok': return r
            e['alerta'] = None
            e['cel'].update(pos=[W + 70, VOS[1] - 40], esc=1.0)
            for paso_ in ((ir, ((VOS[0] + 170, VOS[1] - 40), 2300, 1.0, 'float', VOS)),   # vuelve despacio, frenando
                          (correr, (700,)),                                               # te mira
                          (rodear, (VOS, 2700, 170, 105, 0.75)),                          # te rodea despacio
                          (rodear, (VOS, 900, 150, 95, 1.0, None, True)),                 # y rapido
                          (ir, (ARRIBA, 450, None, None, VOS, 0.0, True)),                # sale disparado al centro
                          (ir, ((ARRIBA[0] - 38, ARRIBA[1] + 10), 230, None, None, VOS, 0.0, True)),   # unos movimientos cortitos
                          (ir, ((ARRIBA[0] + 30, ARRIBA[1] - 8), 210, None, None, VOS, 0.0, True)),
                          (ir, (ARRIBA, 420, None, None, VOS))):
                r = paso_[0](*paso_[1])
                if r != 'ok': return r
        # ===== 5. la charla =====
        def hablar(lineas):
            """Varias líneas de Celebi seguidas (algunas lo mueven antes a otro lugar)."""
            for texto, cara, *resto in lineas:
                if resto and e['cel']:
                    r_ = ir(resto[0], 900, mira=VOS, curva=40)
                    if r_ != 'ok': return r_
                r_ = decir(texto, cara)
                if r_ is None or r_ == 'salir': return r_
            return 'ok'
        r = hablar((('Qué interesante...', 'Inspired'), ('¿Un espíritu? ¿Por acá?', 'Surprised')))
        if r != 'ok': return r
        if e['cel']:                                                       # te examina un poco mas: se acerca despacio, cruza rapido y vuelve
            for destino, ms, rapido in (((VOS[0] - 90, VOS[1] - 70), 900, False), ((VOS[0] + 90, VOS[1] - 70), 380, True), (ARRIBA, 700, False)):
                r = ir(destino, ms, mira=VOS, rapido=rapido)
                if r != 'ok': return r
        r = hablar((('¡Hola! No sabía que me escuchabas.', 'Happy'),
                    ('Qué descortés de mi parte no presentarme: soy Celebi.', 'Joyous'),
                    ('Sé que todo esto te confunde... al igual que a mí me confunde verte.', 'Normal', DERECHA),
                    ('Esto es el borde del cosmos, un puente entre las distintas eras temporales. Y vos quedaste del lado de adentro, sin poder salir.', 'Worried'),
                    ('Pero puedo ayudarte... solo si me devolvés el favor.', 'Determined', IZQUIERDA),
                    ('El espacio-tiempo está siendo corrompido por fuerzas inimaginables para vos: fuerzas hambrientas que buscan poder absoluto sobre el cosmos. Y necesito que me ayudes a repararlo.', 'Worried', ARRIBA),
                    ('A cambio, te voy a sacar de acá y te voy a llevar a que vivas una vida pacífica y feliz.', 'Happy'),
                    ('Me encantaría llevarte a tu hogar, pero no tengo forma de saber cuál es: tu alma quedó separada de tu cuerpo físico.', 'Sad'),
                    ('Pero por suerte pude recuperar un poco de tu memoria... aunque está algo borrosa.', 'Sigh')))
        if r != 'ok': return r
        r = decir('¿Podrías recordarme cuál es tu nombre?', 'Normal')
        if r is None or r == 'salir': return r
        nombre = escribir_nombre('¿Podrías recordarme cuál es tu nombre?')
        if nombre is None or nombre == 'salir': return nombre
        r = hablar((('¡Perfecto! ' + nombre + '... qué lindo nombre.', 'Joyous'),))
        if r != 'ok': return r
        r = decir('¿Te acordás tu género?', 'Normal', ['Chico', 'Chica', 'Prefiero no decirlo'])
        if r is None or r == 'salir': return r
        genero = GENEROS[r]
        r = decir('Parece que hay más pedazos de vos de lo que me imaginaba dentro de tu alma.', 'Inspired')
        if r is None or r == 'salir': return r
        if e['cel']:                                                       # Celebi se corre a la derecha y vos subis un poco
            e['cel']['mira'] = VOS; x0 = e['cel']['pos'][:]
            def correrse(k, ahora):
                """Celebi se corre a un costado y tu espíritu sube un poco (antes de materializarte)."""
                s = _suave(k)
                e['cel']['pos'] = [x0[0] + (AL_COSTADO[0] - x0[0]) * s, x0[1] + (AL_COSTADO[1] - x0[1]) * s]
                e['luz']['pos'] = [VOS[0] + 60 * s, VOS[1] - 70 * s]
            r = correr(800, correrse)
            if r != 'ok': return r
        VOS = [VOS[0] + 60, VOS[1] - 70]; e['luz']['pos'] = list(VOS)
        r = hablar((('Vamos a hacer un ejercicio de concentración. Necesito que concentres toda tu identidad y que trates de materializarte.', 'Determined'),
                    ('(Pensá en cómo era tu cuerpo...)', 'Normal')))
        if r != 'ok': return r
        inicial = elegir_forma()
        if inicial is None or inicial == 'salir': return inicial
        # ===== 6. te materializas: estrellas que giran y se juntan, un destello y tu cuerpo =====
        ahora0 = pygame.time.get_ticks()
        def materializar(k, ahora):
            """Te materializás: estrellas que giran y se juntan, un destello y aparece tu pokemon."""
            if k < 0.6:
                for i in range(8):
                    ang = ahora / 260 + i * math.tau / 8; radio = 170 * (1 - k / 0.6)
                    e['anims'].append(('estrella' if i % 2 else 'brillo', (VOS[0] + math.cos(ang) * radio, VOS[1] + math.sin(ang) * radio * 0.7), 34, ahora, 40))
            elif not e.get('destello'):
                e['destello'] = True; e['anims'] += [('evolucion', tuple(VOS), 300, ahora, 50), ('cambio', tuple(VOS), 340, ahora, 45)]
                cuerpo = AnimadorPokemon(inicial, pygame.Rect(0, 0, 10, 10), 120)
                e['cuerpo'] = {'a': cuerpo, 'pos': list(VOS), 'anim': 'hop'}; e['sombra'] = None
                sonido.grito(inicial)
            e['blanco'] = round(255 * max(0.0, 1 - (k - 0.6) / 0.4)) if k >= 0.6 else 0
        r = correr(1700, materializar)
        if r != 'ok': return r
        e['blanco'] = 0
        if not e['cuerpo']:
            e['cuerpo'] = {'a': AnimadorPokemon(inicial, pygame.Rect(0, 0, 10, 10), 120), 'pos': list(VOS)}; e['sombra'] = None
        e['cuerpo']['anim'] = 'idle'
        if e['cel']:                                                       # te mira, te rodea y vuelve a su lugar
            r = rodear(VOS, 2000, 150, 95, 1.0, 0.0)
            if r != 'ok': return r
            r = ir(AL_COSTADO, 700, mira=VOS)
            if r != 'ok': return r
        r = decir('¡Muy bien, ' + nombre + '! Ahora que tenés un cuerpo, ' + segun_genero(genero, 'estás listo', 'estás lista', 'ya estás en condiciones') + ' para viajar.', 'Happy')
        if r is None or r == 'salir': return r
        # ===== 7. se abre el portal atras, suerte, y se van juntos (todo se apaga) =====
        r = correr(1300, lambda k, a: e.update(portal=round(115 * _suave(k)), vel=1.0 + k))
        if r != 'ok': return r
        r = decir('¡Mucha suerte en tu camino!', 'Joyous')
        if r is None or r == 'salir': return r
        if e['cel']:
            r = ir((VOS[0] + 50, VOS[1] - 10), 420, anim='pull', mira=VOS, rapido=True)   # te agarra
            if r != 'ok': return r
            e['anims'].append(('mano', (VOS[0] + 26, VOS[1] - 6), 72, pygame.time.get_ticks(), 65))   # (la mano del PMD)
            r = correr(450)
            if r != 'ok': return r
        inicio_c, inicio_v = (e['cel']['pos'][:] if e['cel'] else None), e['cuerpo']['pos'][:]
        def adentro(k, ahora):
            """Celebi te lleva de la mano al portal."""
            s = _suave(k)
            if e['cel']: e['cel']['pos'] = [inicio_c[0] + (W // 2 - inicio_c[0]) * s, inicio_c[1] + (150 - inicio_c[1]) * s]; e['cel']['esc'] = 1 - 0.85 * s; e['cel']['anim'] = 'pull'
            kk = max(0.0, (k - 0.12) / 0.88)
            e['cuerpo']['pos'] = [inicio_v[0] + (W // 2 - inicio_v[0]) * _suave(kk), inicio_v[1] + (150 - inicio_v[1]) * _suave(kk)]
            e['cuerpo']['anim'] = 'walk'
        r = correr(1400, adentro)
        if r != 'ok': return r
        e['cel'] = None; e['cuerpo'] = None; e['luz'] = {'pos': [W // 2, 150], 'esc': 0.3}
        def apagar(k, ahora):                                              # el portal se cierra y todo se apaga: queda un brillo que se va
            """El portal se cierra y todo se apaga (queda un brillo que se va)."""
            e['cierre'] = min(1.0, k * 1.8)                                # se agrieta y se rompe en pedazos
            e['oscuro'] = round(255 * _suave(k)); e['vel'] = 2.0 * (1 - k)
            e['luz']['esc'] = 0.3 * (1 - k)
        r = correr(1600, apagar)
        if r != 'ok': return r
        return {'nombre': nombre, 'genero': genero, 'inicial': inicial}


    def cruzar_portal(ui, era_nombre, pokemon, duracion=4200):
        """Terminaste una era: Celebi te arrastra de la mano por el cosmos hasta la siguiente. Se abre desde el blanco del portal; Celebi
        (Pull) va adelante y vos atras, serpenteando con estela mientras aparece el nombre de la era; al final se tiran al fondo del tunel,
        todo se apaga y queda un brillo (la apertura al reves). Una tecla lo adelanta. Devuelve 'salir' si se cerro la ventana."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        reloj = pygame.time.Clock()
        vos = AnimadorPokemon(pokemon, pygame.Rect(0, 0, 10, 10), 100)
        celebi = AnimadorPokemon('celebi', pygame.Rect(0, 0, 10, 10), 84) if tiene_sprites('celebi') else None
        FONDO = (W // 2, H // 2 - 40)
        estela, inicio = ([], []), pygame.time.get_ticks()
        fase, antes = 0.0, None                                          # el cosmos: tranquilo y, al tirarse al fondo, rapido
        camino = lambda t: (W / 2 + math.sin(t / 760) * 230, H * 0.62 + math.sin(t / 470) * 45)   # Celebi va adelante; vos, por el mismo camino un poco atras
        while True:
            ahora = pygame.time.get_ticks(); t = ahora - inicio
            for ev in controles.eventos():
                if ev.type == pygame.QUIT: return 'salir'
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) and t < duracion - 1500: inicio = ahora - (duracion - 1500)
            if t >= duracion: return None
            fin = max(0.0, (t - (duracion - 1500)) / 1500)                # al final: al fondo del tunel y se apaga todo
            fase += (0 if antes is None else min(50, ahora - antes)) / COSMOS['ms'] * (1.2 + 2.5 * fin); antes = ahora
            fondo_viaje(ui, ahora, fase)
            hundir = _suave(min(1.0, fin * 1.6))
            dibujar_estela(ventana, estela[0], ahora, FONDO); dibujar_estela(ventana, estela[1], ahora, FONDO)   # (una estela para cada uno)
            for k_a, (a, retraso, esc0, anim) in enumerate(((vos, 260, 1.0, 'float'), (celebi, 0, 0.9, 'pull'))):
                if not a: continue
                (x, y), (x2, y2) = camino(t - retraso), camino(t - retraso + 40)
                x, y = x + (FONDO[0] - x) * hundir, y + (FONDO[1] - y) * hundir
                esc = esc0 * (1 - 0.9 * hundir)
                if not a.cambiar(anim, _mira(x2 - x, y2 - y), True): a.cambiar('idle', _mira(x2 - x, y2 - y), True)
                a.rect.center = (round(x), round(y)); a.actualizar(); c = a.cuadro()
                if not c: continue
                img = pygame.transform.scale(c[0], (max(1, round(c[0].get_width() * esc)), max(1, round(c[0].get_height() * esc))))
                lugar = img.get_rect(center=(round(x), round(y))); ventana.blit(img, lugar)
                dejar_estela(estela[k_a], img, lugar.x, lugar.y, ahora)
            k = min(1.0, t / 600) * (1 - fin)                             # el nombre de la era
            texto = tipografia.fuente_titulo(3).render(era_nombre, True, 'white'); texto.set_alpha(round(255 * k))
            ventana.blit(texto, texto.get_rect(center=(W // 2, 90)))
            if t < 450:                                                  # viene del blanco del portal
                velo = pygame.Surface((W, H)); velo.fill((255, 255, 255)); velo.set_alpha(round(255 * (1 - t / 450))); ventana.blit(velo, (0, 0))
            if fin > 0:
                velo = pygame.Surface((W, H)); velo.set_alpha(round(255 * _suave(fin))); ventana.blit(velo, (0, 0))
                brillos = efectos._frames('brillo', max(6, round(30 * (1 - fin))))
                if brillos and fin < 0.95: b = brillos[(ahora // 110) % len(brillos)]; ventana.blit(b, b.get_rect(center=FONDO))
            ui['presentar'](); reloj.tick(60)


    # ---------- dialogos ----------

    def preguntar(ui, texto, opciones_, detalle=None):
        """Caja con una pregunta y opciones. Devuelve el indice elegido (None si ESC)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        fondo = ventana.copy()
        elegido = 0
        reloj = pygame.time.Clock()
        while True:
            lineas = ajustar_texto(texto, fuente(32), 620 - 60)[:5]            # los textos largos (charlas, titanes) agrandan la caja
            extra = max(0, len(lineas) - 2) * 30
            cuadro = pygame.Rect(0, 0, 620, 150 + extra + 56 * len(opciones_)); cuadro.center = (W // 2, H // 2)
            botones = [pygame.Rect(cuadro.x + 60, cuadro.y + 120 + extra + i * 56, cuadro.width - 120, 44) for i in range(len(opciones_))]
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
            for i, linea in enumerate(lineas):
                ventana.blit(fuente(32).render(linea, True, 'white'), (cuadro.x + 30, cuadro.y + 22 + i * 30))
            if detalle: ventana.blit(fuente(22).render(ajustar_texto(detalle, fuente(22), cuadro.width - 50)[0], True, (200, 200, 200)), (cuadro.x + 30, cuadro.y + 88 + extra))
            for i, b in enumerate(botones): boton(ventana, b, opciones_[i], i == elegido, 30)
            ui['presentar'](); reloj.tick(60)


    # ---------- rueda de curaciones ----------

    def rueda_curacion(ui, opciones_, mantener):
        """Rueda de curaciones como la de Breath of the Wild: la pelea queda congelada detras y alrededor del centro estan tus curaciones
        (cada una con su icono de BW y cuantas llevas) en botones de la pantalla tactil. Se elige con el mouse, las flechas o los numeros
        y se usa al soltar la tecla de curarse (o con ENTER / clic). opciones_: [(clave, cantidad)]. mantener(): si la tecla sigue apretada.
        Devuelve el indice elegido, None si se cancela (ESC / clic derecho) o 'salir'."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        fondo = ventana.copy()
        velo = pygame.Surface((W, H), pygame.SRCALPHA); velo.fill((8, 10, 24, 150))
        centro, n = (W // 2, H // 2 - 20), len(opciones_)
        angulo = lambda i: math.radians(-90 + 360 * i / n)
        elegido, abierto, reloj = 0, pygame.time.get_ticks(), pygame.time.Clock()
        def mas_cerca(dx, dy):
            a = math.atan2(dy, dx)
            return min(range(n), key=lambda i: abs((angulo(i) - a + math.pi) % math.tau - math.pi))
        while True:
            ahora = pygame.time.get_ticks()
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if pygame.K_1 <= e.key < pygame.K_1 + n: return e.key - pygame.K_1
                    if e.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE): return elegido
                if e.type == pygame.MOUSEMOTION:
                    x, y = ui['a_logico'](e.pos)
                    if math.hypot(x - centro[0], y - centro[1]) > 40: elegido = mas_cerca(x - centro[0], y - centro[1])
                if e.type == pygame.MOUSEBUTTONDOWN: return elegido if e.button == 1 else None
            dx, dy = controles.direccion()
            flechas = pygame.key.get_pressed()
            dx, dy = dx + flechas[pygame.K_RIGHT] - flechas[pygame.K_LEFT], dy + flechas[pygame.K_DOWN] - flechas[pygame.K_UP]
            if dx or dy: elegido = mas_cerca(dx, dy)
            if ahora - abierto > 80 and not mantener(): return elegido
            radio = round((110 if n <= 3 else 135) * aparecer(ahora - abierto, 0, 140))
            ventana.blit(fondo, (0, 0)); ventana.blit(velo, (0, 0))
            for i, (clave, cantidad) in enumerate(opciones_):
                x, y = round(centro[0] + radio * math.cos(angulo(i))), round(centro[1] + radio * math.sin(angulo(i)))
                yo = i == elegido
                boton_tactil(ventana, (x, y), 40 if yo else 33, 0.0, tienda.ITEMS[clave]['color'] if yo else None)
                icono = icono_objeto(clave, 40 if yo else 30)
                if icono: ventana.blit(icono, icono.get_rect(center=(x, y)))
                if cantidad > 1:
                    t = tipografia.fuente(20, borde=True).render('x' + str(cantidad), True, 'white'); ventana.blit(t, t.get_rect(bottomright=(x + 34, y + 34)))
                t = tipografia.fuente(20, borde=True).render(str(i + 1), True, (255, 230, 150)); ventana.blit(t, t.get_rect(topleft=(x - 34, y - 36)))
            clave = opciones_[elegido][0]
            nombre = tipografia.fuente_titulo(2).render(tienda.ITEMS[clave]['nombre'], True, 'white')
            ventana.blit(nombre, nombre.get_rect(center=centro))
            info = pygame.Rect(W // 2 - 300, H - 104, 600, 56)
            caja(ventana, info, 'panel', OSCURO, 2, (220, 220, 220))
            for k, linea in enumerate(ajustar_texto(tienda.ITEMS[clave].get('desc', ''), fuente(24), info.width - 40)[:2]):
                ventana.blit(fuente(24).render(linea, True, 'white'), (info.x + 20, info.y + 12 + k * 24))
            pie(ventana, 'soltá la tecla: usar   flechas, mouse o 1-' + str(n) + ': elegir   ESC: cancelar')
            ui['presentar'](); reloj.tick(60)


    # ---------- ajustes ----------

    def ajustes(ui):
        """Ajustes con el formato de los otros menus. El codigo Konami abre los trucos."""
        ventana, H, config = ui['ventana'], ui['H'], ui['config']
        modos = ['mouse', 'teclas', 'mixto']
        filas = ['volumen', 'efectos', 'modo', 'resolucion', 'pantalla_completa', 'estilo_equipo', 'hall', 'controles', 'glosario', 'volver']
        textos = {'volumen': 'Música', 'efectos': 'Efectos y gritos', 'modo': 'Combate', 'resolucion': 'Resolucion', 'pantalla_completa': 'Pantalla completa',
                  'estilo_equipo': 'Menu de equipo', 'hall': 'Hall', 'controles': 'Controles', 'glosario': 'Glosario', 'volver': 'Volver'}
        ayudas = {'modo': {'mouse': 'Apuntas con el mouse', 'teclas': 'Atacas hacia donde caminaste por ultima vez', 'mixto': 'Teclas hasta que moves el mouse'},
                  'estilo_equipo': {'vitrina': 'Tus pokemon en cartas y el elegido en una vitrina animada', 'clasico': 'Lista como en los juegos de Pokemon',
                                    'escenario': 'Tus pokemon parados en un escenario (se duermen si esperas)'},
                  'hall': {'auto': 'Donde aparece Celebi hasta que derrotes una era; despues, el lugar atemporal',
                           'atemporal': 'Siempre el lugar atemporal: una isla flotando en el tiempo que cambia segun la era',
                           'celebi': 'Siempre el bosque donde aparece Celebi'}}
        NOMBRE_HALL = {'auto': 'Automatico', 'atemporal': 'Atemporal', 'celebi': 'Celebi'}
        elegido = 0
        reloj = pygame.time.Clock()

        def cambiar(clave, paso):
            """Cambia el valor de una opcion de ajustes hacia un lado (-1 o +1) y lo aplica."""
            if clave == 'volumen': config['volumen'] = max(0, min(100, config['volumen'] + 10 * paso)); ui['aplicar_volumen']()
            elif clave == 'efectos': config['volumen_efectos'] = max(0, min(100, config.get('volumen_efectos', 70) + 10 * paso)); sonido.grito('pikachu', 1.0)
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
            botones = [pygame.Rect(MARGEN_X, CONTENIDO_Y + i * 46, 520, 40) for i in range(len(filas))]   # (mas juntos: son 10 filas)
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
            if accion in ('modo', 'resolucion', 'pantalla_completa', 'estilo_equipo', 'hall', 'volumen', 'efectos'): cambiar(accion, 1)
            fondo(ventana)
            titulo(ventana, 'Ajustes')
            valores = {'volumen': config['volumen'], 'efectos': config.get('volumen_efectos', 70), 'modo': config['modo'].title(), 'resolucion': config['resolucion'],
                       'pantalla_completa': 'Si' if config['pantalla_completa'] else 'No', 'estilo_equipo': config['estilo_equipo'].title(),
                       'hall': NOMBRE_HALL.get(config.get('hall'), 'Automatico')}
            for i, clave in enumerate(filas): boton(ventana, botones[i], textos[clave], i == elegido, 32, valores.get(clave))
            clave = filas[elegido]
            ayuda = ayudas.get(clave, {}).get(config.get(clave)) if clave in ayudas else None
            info = pygame.Rect(600, CONTENIDO_Y, ui['W'] - 600 - MARGEN_X, 120)   # al costado: que hace la opcion elegida
            if clave in ('volumen', 'efectos') or ayuda:
                caja(ventana, info, 'panel', PANEL)
                ventana.blit(fuente(30).render(textos[clave], True, (255, 236, 120)), (info.x + 16, info.y + 10))
            if clave in ('volumen', 'efectos'):
                nivel_v = config['volumen'] if clave == 'volumen' else config.get('volumen_efectos', 70)
                for i in range(10): pygame.draw.rect(ventana, 'white' if i < nivel_v // 10 else (90, 90, 90), (info.x + 16 + i * 30, info.y + 62, 24, 18))
                hay_musica = os.path.isdir(sonido.MUSICA) and any(not f_.endswith('.txt') for f_ in os.listdir(sonido.MUSICA))
                if clave == 'volumen' and not hay_musica:
                    ventana.blit(fuente(20).render('(todavía no hay música: ver assets/musica/LEEME.txt)', True, (220, 200, 160)), (info.x + 16, info.y + 90))
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
              ('llaves_auto', 'Llaves solas (puertas y cofres abiertos)'), ('desbloquear_todo', 'Desbloquear todo (eras, titanes y amigos)'),
              ('subir_niveles', 'Subir 5 niveles al equipo (al volver al juego)')]


    def trucos(ui):
        """Menu secreto (codigo Konami en ajustes o en pausa)."""
        ventana, H, t = ui['ventana'], ui['H'], ui['config']['trucos']
        elegido = 0
        reloj = pygame.time.Clock()
        while True:
            botones = [pygame.Rect(100, 104 + i * 50, 700, 42) for i in range(len(TRUCOS) + 1)]
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
        s['Tienda'] = ['Aparece cada 5 a 10 salas. Cambia de nombre segun la era (' + ', '.join(e['tienda'] for e in datos.mundos.ERAS) + ').',
                       'Esta partida en 3: tres mostradores, cada uno del color del pokemon que lo atiende, con 5 objetos al azar.',
                       'Acercate a un objeto del mostrador y apretá ' + tecla('interactuar') + ' para comprarlo.',
                       '[Chikorita rosa] (izquierda) 5 curaciones (vida o estados). Van al cinturón: como mucho ' + str(tienda.CINTURON_MAX) + '.',
                       '   En la punta de su mostrador (♥ Curar) cura al que pelea o cura y revive a todo el equipo, por monedas.',
                       '   Tambien cuida tu reserva: los cambios con la reserva se hacen en la tienda.',
                       '[Riolu] (medio) 3 objetos que potencian (Ataque X, Defensa X, Velocidad X, Especial X, Directo o los de tipo)',
                       '   y 2 objetos de evolucion (piedras, Cordon Union...). Si alguien de tu equipo necesita uno, casi siempre esta.',
                       '[Kecleon] (derecha) 5 MT. Si hay alguna que tu equipo puede aprender, al menos una de esas.',
                       'Los objetos que dicen "lo lleva un pokemon" se equipan desde su ficha (hasta 2 cada uno) y solo cuentan mientras pelea.',
                       'Los que dicen "todo el equipo" valen para todos.',
                       'MT de combate: van en cualquier casilla (E, Q, Shift o R). MT especiales: solo en Shift o R.', ''] + \
            [it['nombre'] + ' (' + str(it['precio']) + ' $): ' + it['desc'] for k, it in tienda.ITEMS.items()
             if k in tienda.POTENCIADORES or k in tienda.EVOLUCION_TIENDA]
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
                             'Subjefes en las salas 10 y 20, semijefe en la 15 y el Regi de la era en la 30. Las puertas muestran que hay detras.',
                             'En las peleas de subjefes nadie quiere unirse (ni los pokemon que salen en la pelea).',
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
            'Cinturón: las curaciones van en el cuarto de círculo de abajo a la derecha (como mucho ' + str(tienda.CINTURON_MAX) + '). Tocando ' + tecla('curar') + ' usás la del lugar 1',
            'en el que pelea (si no le sirve, no se gasta) y las de atrás avanzan. Manteniéndola se abre la rueda (como en Breath of the Wild): la pelea se',
            'congela y elegís cuál usar con el mouse, las flechas o los números; al soltar se usa. En la mochila las usás en quien quieras o las tirás.',
            'Chikorita rosa vende 5 curaciones al azar en cada tienda. La Poción Máxima no se vende: Celebi te da una al empezar cada viaje',
            'y en cada era nueva si tenés lugar en el cinturón (solo se lleva una).',
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
        s['Lazos de equipo'] = ['Además de la sinergia que da cada uno desde la banca, el equipo entero gana algo si sus pokemon se complementan.',
                                'Cuentan todos los que están en pie (también el que pelea). Los que tenés activos se ven en el menú de equipo, arriba a la derecha, y cuando se forma uno aparece un cartel.',
                                'Vale la línea entera: si el lazo dice Mudkip, sirven también Marshtomp y Swampert. En la ficha de cada pokemon (pestaña de habilidad) dice qué lazos puede formar.',
                                'Lo que suman varios lazos a una misma cosa tiene un tope de ' + str(round(mecanicas.TOPE_LAZOS * 100)) + '% (la energía vale el triple).',
                                '', '[Resonancia de tipo]',
                                'Por qué: los que comparten un tipo pelean parecido y se potencian. Dos del mismo tipo dan +' + str(round(mecanicas.FUERZA_RESONANCIA[2] * 100))
                                + '%; los tres, +' + str(round(mecanicas.FUERZA_RESONANCIA[3] * 100)) + '%. Qué da depende del tipo:']
        por_bono = {}
        for tipo_r, clave_r in mecanicas.RESONANCIA.items(): por_bono.setdefault(clave_r, []).append(tipo_r)
        s['Lazos de equipo'] += [mecanicas.NOMBRE_BONO[c_].capitalize() + ': ' + ', '.join(ts) + '.' for c_, ts in por_bono.items()]
        s['Lazos de equipo'] += ['', '[Lazos por su historia: ' + str(len(mecanicas.LAZOS)) + ']']
        for nombre_l, motivo, _, _, da in mecanicas.LAZOS:                 # cada lazo: quienes, por que y que da
            s['Lazos de equipo'] += [nombre_l.upper() + '  (' + mecanicas.texto_bono(da) + ')', '   Quiénes: ' + mecanicas.miembros_lazo(nombre_l) + '.',
                                     '   Por qué: ' + motivo + '.', '']
        s['Enemigos'] = ['Pegadores (tanques y atacantes): te rodean y se tiran hacia vos al pegar. A veces encadenan un segundo golpe más rápido.',
                         'Si les pegás de lejos y te escapás mucho rato, pegan un salto hasta donde estás (línea naranja).',
                         'Tiradores (estrategas): te siguen con la mira y se esconden a recargar. Si te quedás quieto o te escondés, tiran un mortero: un círculo rojo en el piso que se va llenando.',
                         'Con poca vida, los tiradores se van atrás de sus compañeros.',
                         'Rápidos (velocistas): embisten en línea recta. Si no te tocan, a veces giran y embisten de nuevo.',
                         'En la primera era casi no usan estas maniobras; en cada era las usan más seguido.',
                         'Modo fácil (estatua del salón de los modos): avisan más, atacan menos seguido, de a dos como mucho, y recibís menos daño.']
        s['Modos'] = ['Tutorial (menú principal): la isla de práctica de Celebi. Paso por paso: moverte, esquivar, combo, disparo, especiales, parry, relevos, asistencias, baile y amistad, romper cosas, la llave, la tienda y los lazos.',
                      'Boss rush (menú principal): elegí 3 pokemon cualesquiera y peleá contra todos los jefes seguidos, con una tienda entre era y era. Tu equipo sube solo al nivel de cada jefe.',
                      'Boss rush con tu partida: en el refugio de Celebi, en la estatua del salón de los modos. Van tus amigos; lo que ganes vuelve con vos como monedas para el próximo viaje.',
                      'Sala de los titanes (refugio): los jefes que ya derrotaste te esperan ahí. Podés hablarles y pedirles la revancha.',
                      'Contrarreloj (minijuegos del refugio): 90 segundos de oleadas; cuenta cuántos derrotás.',
                      'Supervivencia (minijuegos): oleadas cada vez más grandes hasta que caigas.',
                      'Modo fácil: se prende y se apaga en la estatua. Vale para los viajes y para el boss rush.']
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
                    color = (240, 200, 80) if linea.startswith('[') else (170, 255, 170) if '(+' in linea and linea[:4].isupper() else (235, 235, 235)   # titulos, nombres de lazos y texto
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




    # ---------- equipo (TAB) ----------

    def equipo(ui, j, acc):
        """
        Menu de equipo. acc tiene funciones de main.py:
            'movs'(m) -> 4 nombres a mostrar    'evolucionar'(i, destino)    'enseñar'(i, casilla, mt)
            'activar'(i)    'reserva'() -> lista de la reserva    'traer'(i_reserva, i_equipo)
        """
        estilo = ui['config'].get('estilo_equipo', 'vitrina')
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
                    if e.key == pygame.K_SPACE and isinstance(opciones_[elegido], int) and opciones_[elegido] != j['activo']:   # ponerlo a pelear sin entrar a la ficha
                        m_ = j['equipo'][opciones_[elegido]]
                        if m_['vida'] > 0: acc['activar'](opciones_[elegido]); escena['cambio'] = pygame.time.get_ticks()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in escena.get('zonas', {}).items():
                        if r.collidepoint(ui['a_logico'](e.pos)): elegido = opciones_.index(i) if i in opciones_ else elegido; accion = i
            if accion == 'volver': return None
            if accion == 'mochila' and mochila(ui, j, acc) == 'salir': return 'salir'
            if accion == 'reserva' and reserva(ui, j, acc) == 'salir': return 'salir'
            if isinstance(accion, int) and ficha(ui, j, accion, acc) == 'salir': return 'salir'
            if estilo == 'escenario': _dibujar_escenario(ui, j, opciones_[elegido], escena)
            elif estilo == 'clasico': _dibujar_clasico(ui, j, opciones_[elegido], escena)
            else: _dibujar_vitrina(ui, j, opciones_[elegido], escena, acc)
            for k, (lazo, _, da) in enumerate((j.get('lazos') or [])[:5]):     # lazos de equipo activos: chapitas arriba a la derecha
                texto_l = lazo + '  ' + ' '.join('+' + str(round(v * 100)) + '% ' + {'enfriamiento': 'recargas', 'energia': 'energía'}.get(c_, c_) for c_, v in da.items())
                t = fuente(18).render(texto_l, True, (255, 240, 170))
                chapa = t.get_rect(topright=(ui['W'] - 16, 8 + k * 24)).inflate(14, 4)
                velo = pygame.Surface(chapa.size, pygame.SRCALPHA); velo.fill((20, 18, 34, 215)); ui['ventana'].blit(velo, chapa)
                pygame.draw.rect(ui['ventana'], (220, 180, 90), chapa, 1, border_radius=4); ui['ventana'].blit(t, t.get_rect(center=chapa.center))
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


    def _suave(k):
        k = max(0.0, min(1.0, k)); return 1 - (1 - k) ** 3


    def _dibujar_vitrina(ui, j, sel, escena, acc):
        """Menu de equipo nuevo: tus pokemon en cartas a la izquierda (entran deslizandose) y a la derecha una vitrina del elegido,
        animado sobre un pedestal de su tipo, con su vida, experiencia, ataques, objetos, lo que da desde la banca y su mecanica."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        ahora = pygame.time.get_ticks()
        escena.setdefault('abierto', ahora)
        fondo(ventana)
        zonas = {}
        miembro_i = sel if isinstance(sel, int) else escena.get('ultimo_miembro', j['activo'])
        miembro_i = min(miembro_i, len(j['equipo']) - 1)
        if escena.get('ultimo_miembro') != miembro_i:
            if 'ultimo_miembro' in escena: sonido.grito(j['equipo'][min(miembro_i, len(j['equipo']) - 1)]['nombre'], 0.6)   # al elegir otro, grita
            escena['ultimo_miembro'] = miembro_i; escena['cambio'] = ahora
        t_partida = acc.get('tiempo', lambda: ahora)()
        # ----- cartas del equipo
        for i, m in enumerate(j['equipo']):
            k = _suave((ahora - escena['abierto'] - i * 70) / 300)
            r = pygame.Rect(26, 92 + i * 124, 336, 112)
            zonas[i] = r.copy()
            r = r.move(-round((1 - k) * 380) + (10 if sel == i else 0), 0)
            activo = i == j['activo']
            vida = j['vida'] if activo else m['vida']
            pieza_n = 'miembro_debil' if vida <= 0 else 'miembro_activo' if activo else 'miembro'
            if pieza(pieza_n): caja(ventana, r, pieza_n)
            else: pygame.draw.rect(ventana, (40, 90, 150) if activo else (50, 70, 90), r, border_radius=14)
            img = ui['retrato'](m['nombre'], 60)
            if img: ventana.blit(img, (r.x + 12, r.y + 12))
            ventana.blit(fuente(30).render(m['nombre'].replace('_', ' ').title(), True, 'white'), (r.x + 84, r.y + 10))
            nv = fuente(24).render('Nv ' + str(m['nivel']), True, (255, 230, 120)); ventana.blit(nv, nv.get_rect(topright=(r.right - 14, r.y + 14)))
            barra_vida(ventana, (r.x + 84, r.y + 44, r.width - 100, 14), vida / max(1, m['max_vida']))
            ventana.blit(fuente(18).render(str(int(vida)) + ' / ' + str(m['max_vida']), True, 'white'), (r.x + 84, r.y + 60))
            pygame.draw.rect(ventana, (30, 40, 70), (r.x + 84, r.y + 80, r.width - 100, 5))
            pygame.draw.rect(ventana, (80, 170, 255), (r.x + 84, r.y + 80, round((r.width - 100) * progreso.progreso_nivel(m)), 5))
            if activo: estado_t, color_t = 'PELEANDO', (150, 230, 255)
            elif vida <= 0: estado_t, color_t = 'DEBILITADO', (255, 120, 110)
            else:
                falta = max(0, m.get('asist_listo', 0) - t_partida)
                estado_t, color_t = ('Asistencia lista' if not falta else 'Asistencia en ' + str(math.ceil(falta / 1000)) + ' s'), ((140, 240, 140) if not falta else (210, 210, 220))
            ventana.blit(fuente(18).render(estado_t, True, color_t), (r.x + 84, r.y + 89))
            if m.get('puntos') or progreso.evoluciones(m, j['inventario']['objetos']):
                aviso = 'EVO' if progreso.evoluciones(m, j['inventario']['objetos']) else '+EV'
                if (ahora // 350) % 2: ventana.blit(fuente(20).render(aviso, True, (255, 140, 220)), (r.right - 50, r.y + 88))
            if sel == i: dibujar_esquinas(ventana, r.inflate(4, 4), margen=4, largo=12)
        # ----- vitrina del elegido
        m = j['equipo'][miembro_i]; activo = miembro_i == j['activo']
        tipos = [normalizar_tipo(t) for t in pokemones.get(m['nombre'], {}).get('tipo', [])]
        color = COLORES_TIPO.get(tipos[0] if tipos else '', (150, 150, 150))
        kc = _suave((ahora - escena.get('cambio', 0)) / 260)
        v = pygame.Rect(380, 92, 594, 432).move(0, round((1 - kc) * 18))
        caja(ventana, v, 'panel', (30, 32, 44))
        tira = pygame.Surface((v.width - 12, 6), pygame.SRCALPHA); tira.fill((*color, 200)); ventana.blit(tira, (v.x + 6, v.y + 6))
        nombre_t = fuente(40).render(m['nombre'].replace('_', ' ').title(), True, 'white')
        ventana.blit(nombre_t, (v.x + 20, v.y + 18))
        x_chip = v.x + 24 + nombre_t.get_width()
        for t in tipos: x_chip += chip_tipo(ventana, t, x_chip, v.y + 26)
        rol = ROL_POKEMON.get(m['nombre'], '')
        if rol: ventana.blit(fuente(22).render(rol.title() + '  -  Nv ' + str(m['nivel']), True, (255, 225, 120)), (v.x + 20, v.y + 62))
        # pedestal y sprite
        cx_, cy_ = v.x + 140, v.y + 205
        brillo = pygame.Surface((220, 220), pygame.SRCALPHA)
        for rr, a_ in ((100, 28), (72, 42), (48, 58)): pygame.draw.circle(brillo, (*color, a_), (110, 110), rr + round(3 * math.sin(ahora / 420)))
        ventana.blit(brillo, (cx_ - 110, cy_ - 120))
        pygame.draw.ellipse(ventana, tuple(max(0, c - 90) for c in color), (cx_ - 64, cy_ + 40, 128, 26))
        pygame.draw.ellipse(ventana, tuple(min(255, c + 40) for c in color), (cx_ - 64, cy_ + 36, 128, 26), 3)
        clave_a = ('vitrina', m['nombre'])
        a = escena['animadores'].get(clave_a)
        if not a: a = AnimadorPokemon(m['nombre'], pygame.Rect(0, 0, 10, 10), 120); escena['animadores'][clave_a] = a
        t_anim = ahora - escena.get('cambio', 0)
        if t_anim < 1400: a.cambiar('walk', (t_anim // 175) % 8, True)        # al elegirlo da una vuelta caminando
        elif activo and (t_anim // 2500) % 2: a.cambiar('attack', 0, True)
        else: a.cambiar('idle', 0, True)
        a.rect.center = (cx_, round(cy_ + 3 * math.sin(ahora / 320)) - 4)
        a.actualizar()
        if not a.dibujar(ventana):
            img = ui['retrato'](m['nombre'], 96)
            if img: ventana.blit(img, img.get_rect(center=(cx_, cy_)))
        if activo: ventana.blit(fuente(20).render('Peleando ahora', True, (150, 230, 255)), (cx_ - 58, cy_ + 72))
        elif m['vida'] > 0 and isinstance(sel, int): ventana.blit(fuente(20).render('ESPACIO: poner a pelear', True, (200, 220, 255)), (cx_ - 96, cy_ + 72))
        # datos a la derecha
        x0, y0, ancho = v.x + 290, v.y + 96, v.width - 310
        vida = j['vida'] if activo else m['vida']
        ventana.blit(fuente(20).render('Vida', True, (210, 215, 230)), (x0, y0))
        barra_vida(ventana, (x0 + 60, y0, ancho - 60, 14), vida / max(1, m['max_vida']), False)
        ventana.blit(fuente(20).render('Exp', True, (210, 215, 230)), (x0, y0 + 22))
        pygame.draw.rect(ventana, (30, 40, 70), (x0 + 60, y0 + 26, ancho - 60, 7))
        pygame.draw.rect(ventana, (80, 170, 255), (x0 + 60, y0 + 26, round((ancho - 60) * progreso.progreso_nivel(m)), 7))
        y = y0 + 48
        ventana.blit(fuente(24).render('Ataques', True, (255, 210, 90)), (x0, y)); y += 26
        try: nombres_m = acc['movs'](m)
        except Exception: nombres_m = []
        for tecla, n in zip(('E', 'Q', 'Shift', 'R'), nombres_m):
            chip = pygame.Rect(x0, y + 1, 46, 20)
            pygame.draw.rect(ventana, (60, 70, 110), chip, border_radius=4); pygame.draw.rect(ventana, (130, 150, 210), chip, 1, border_radius=4)
            tt = fuente(18).render(tecla, True, 'white'); ventana.blit(tt, tt.get_rect(center=chip.center))
            ventana.blit(fuente(20).render(str(n).replace('_', ' ').title()[:26], True, 'white'), (x0 + 54, y + 2)); y += 23
        y += 2
        ventana.blit(fuente(24).render('Objetos', True, (255, 210, 90)), (x0, y)); y += 26
        items = m.get('items') or []
        txt_items = ', '.join(tienda.ITEMS[i_]['nombre'] if i_ in tienda.ITEMS else i_.replace('_', ' ').title() for i_ in items) or '(sin objetos)'
        for linea in ajustar_texto(txt_items, fuente(20), ancho)[:1]:
            ventana.blit(fuente(20).render(linea, True, (230, 230, 235) if items else (150, 155, 170)), (x0, y)); y += 20
        y += 2
        ventana.blit(fuente(24).render('Desde la banca', True, (255, 210, 90)), (x0, y)); y += 24
        try:
            nombre_a, _, que_hace = acc['asistencia'](m).partition(': ')
            ventana.blit(fuente(18).render('Asistencia (F/G): ' + nombre_a, True, (220, 225, 235)), (x0, y)); y += 18
            f18 = fuente(18)
            while que_hace and f18.size(que_hace + '...')[0] > ancho: que_hace = que_hace[:-1]   # una linea: el resto en la ficha
            ventana.blit(f18.render(que_hace.rstrip() + ('...' if que_hace != acc['asistencia'](m).partition(': ')[2] else ''), True, (170, 175, 190)), (x0, y))
        except Exception: pass
        # la mecanica de la linea, abajo de todo
        unico = mecanicas.texto_de(m['nombre'])
        if unico:
            franja = pygame.Rect(v.x + 14, v.bottom - 62, v.width - 28, 50)
            pygame.draw.rect(ventana, (24, 44, 34), franja, border_radius=6); pygame.draw.rect(ventana, (90, 200, 120), franja, 1, border_radius=6)
            for k_, linea in enumerate(ajustar_texto(unico, fuente(18), franja.width - 20)[:2]):
                ventana.blit(fuente(18).render(linea, True, (170, 255, 170)), (franja.x + 10, franja.y + 6 + k_ * 20))
        # ----- botones, monedas y ayuda
        for k, (clave, texto) in enumerate((('mochila', 'Mochila'), ('reserva', 'Reserva (' + str(len(j.get('reserva', []))) + ')'), ('volver', 'Volver'))):
            r = pygame.Rect(26 + k * 190, H - 84, 176, 46); zonas[clave] = r
            boton(ventana, r, texto, sel == clave, 26, aparicion=_suave((ahora - escena['abierto'] - 200 - k * 60) / 300))
        monedas = fuente(30).render('$ ' + str(j.get('monedas', 0)), True, (255, 225, 120))
        ventana.blit(monedas, monedas.get_rect(midright=(W - 30, H - 60)))
        titulo(ventana, 'Tu equipo')
        pie(ventana, 'flechas: elegir   ENTER: ficha completa (stats, MT, objetos, evolucionar)   ESPACIO: poner a pelear   TAB / ESC: volver')
        escena['zonas'] = zonas


    PESTAÑAS_FICHA = ('Ficha', 'Ataques', 'Habilidad', 'MT')
    FORMA_TXT = {'cuerpo': 'cuerpo a cuerpo', 'proyectil': 'disparo', 'area': 'área alrededor', 'embestida': 'embestida', 'buff': 'mejora',
                 'curar': 'cura', 'mecanica': 'mecánica propia', 'estado': 'estado'}


    def _pestañas_ficha(ventana, pagina, color):
        """Las 4 pestañas de arriba a la derecha. Devuelve sus rects (para el clic)."""
        zonas = []
        for k, nombre in enumerate(PESTAÑAS_FICHA):
            r = pygame.Rect(340 + k * 160, 8, 152, 32); zonas.append(r)
            elegida = k == pagina
            caja(ventana, r.move(0, 0 if elegida else 3), 'panel', (60, 70, 110) if elegida else (32, 34, 46))
            if elegida: pygame.draw.rect(ventana, color, (r.x + 10, r.bottom - 5, r.width - 20, 4), border_radius=2)
            t = fuente(20).render(str(k + 1) + '. ' + nombre, True, 'white' if elegida else (170, 175, 190))
            ventana.blit(t, t.get_rect(center=r.move(0, 0 if elegida else 3).center))
        return zonas


    def _parrafo(ventana, texto, x, y, ancho, tam=19, color=(230, 230, 236), max_lineas=99):
        """Escribe un texto cortado en renglones y devuelve dónde terminó."""
        for linea in ajustar_texto(texto, fuente(tam), ancho)[:max_lineas]:
            ventana.blit(fuente(tam).render(linea, True, color), (x, y)); y += tam + 1
        return y


    def _pagina_ataques(ventana, m, acc, area):
        """Que hace cada una de las 4 casillas: tipo, forma, numeros, efecto y la explicacion completa."""
        try: movs, info, dats = acc['movs'](m), acc['info_movs'](m), acc['datos_movs'](m)
        except Exception: movs, info, dats = ['-'] * 4, [''] * 4, [{}] * 4
        ancho, alto = (area.width - 12) // 2, (area.height - 12) // 2
        for k in range(4):
            r = pygame.Rect(area.x + (k % 2) * (ancho + 12), area.y + (k // 2) * (alto + 12), ancho, alto)
            caja(ventana, r, 'panel', PANEL)
            d = dats[k] if k < len(dats) else {}
            tipo = normalizar_tipo(d.get('tipo')) if d.get('tipo') else None
            if tipo: pygame.draw.rect(ventana, COLORES_TIPO.get(tipo, (150, 150, 150)), (r.x + 6, r.y + 6, r.width - 12, 4))
            chip = pygame.Rect(r.x + 12, r.y + 16, 54, 22)
            pygame.draw.rect(ventana, (20, 30, 60), chip, border_radius=4); pygame.draw.rect(ventana, (130, 160, 230), chip, 1, border_radius=4)
            t = fuente(18).render(mts.CASILLAS[k], True, 'white'); ventana.blit(t, t.get_rect(center=chip.center))
            ventana.blit(fuente(24).render(str(movs[k]).replace('_', ' ').title()[:20], True, 'white'), (chip.right + 8, r.y + 15))
            y = r.y + 46; x = r.x + 12
            if tipo: x += chip_tipo(ventana, tipo, x, y)
            forma = FORMA_TXT.get(d.get('forma'), d.get('forma') or '')
            ventana.blit(fuente(19).render(forma, True, (200, 220, 255)), (x + 4, y + 4))
            y += 32
            numeros = []
            if d.get('daño'): numeros.append('daño ' + str(round(float(d['daño']))))
            if d.get('distancia') and d.get('forma') in ('proyectil', 'embestida'): numeros.append('alcance ' + str(round(float(d['distancia']))))
            if d.get('area') and d.get('forma') in ('area', 'cuerpo'): numeros.append('área ' + str(round(float(d['area']))))
            if d.get('enfriamiento'): numeros.append('espera ' + str(round(float(d['enfriamiento']) / 1000, 1)) + ' s')
            if numeros: ventana.blit(fuente(19).render('   '.join(numeros), True, (255, 225, 120)), (r.x + 12, y)); y += 22
            efecto = d.get('efecto')
            if isinstance(efecto, dict) and efecto.get('tipo'):
                ventana.blit(fuente(19).render('Efecto: ' + str(efecto['tipo']) + (' (' + str(efecto['probabilidad']) + '%)' if efecto.get('probabilidad') else ''), True, (255, 170, 200)), (r.x + 12, y)); y += 22
            texto = d.get('desc') if d.get('forma') == 'mecanica' else (info[k] if k < len(info) else '')
            _parrafo(ventana, texto, r.x + 12, y + 2, r.width - 24, 18, (220, 222, 232), max(1, (r.bottom - y - 10) // 19))


    def _pagina_habilidad(ventana, m, acc, area):
        """La mecanica de su linea (y que cambia al evolucionar), su especial propio, el rol, lo que da desde la banca y como es de enemigo."""
        caja(ventana, area, 'panel', PANEL)
        x, y, ancho = area.x + 16, area.y + 12, area.width - 32
        nombre = m['nombre']
        clave, etapa_m = mecanicas.de(nombre)
        if clave:
            mm = mecanicas.MECANICAS[clave]
            ventana.blit(fuente(30).render(mm['nombre'], True, (170, 255, 170)), (x, y))
            clase = 'Pasiva: siempre está' if mm['clase'] == 'pasiva' else 'Especial: va en la R (espera ' + str(round(mm['enfriamiento'] / 1000, 1)) + ' s)'
            ventana.blit(fuente(19).render(clase, True, (200, 220, 255)), (x + fuente(30).size(mm['nombre'])[0] + 14, y + 8)); y += 34
            y = _parrafo(ventana, mm['desc'], x, y, ancho, 19) + 6
            linea = [e for e, (c_, _) in sorted(mecanicas.LINEAS.items(), key=lambda kv: kv[1][1]) if c_ == clave]
            if len(linea) > 1:                                             # la linea entera, con este marcado
                ventana.blit(fuente(19).render('Línea:', True, (210, 215, 230)), (x, y + 4)); xx = x + 64
                for e in linea:
                    t = fuente(19).render(e.replace('_', ' ').title() + ' (' + str(mecanicas.LINEAS[e][1]) + ')', True, (255, 230, 120) if e == nombre else (180, 185, 200))
                    if e == nombre: pygame.draw.rect(ventana, (60, 80, 60), t.get_rect(topleft=(xx, y + 4)).inflate(8, 4), border_radius=4)
                    ventana.blit(t, (xx, y + 4)); xx += t.get_width() + 14
                y += 30
        else:
            ventana.blit(fuente(26).render('Sin mecánica propia', True, (200, 200, 210)), (x, y)); y += 34
        propio = mecanicas.ESPECIE_ESPECIAL.get(nombre)
        if propio:
            ventana.blit(fuente(24).render('Especial de ' + nombre.replace('_', ' ').title() + ': ' + propio['nombre'] + ' (R)', True, (255, 210, 90)), (x, y)); y += 26
            y = _parrafo(ventana, propio['desc'], x, y, ancho) + 6
        pygame.draw.line(ventana, (80, 90, 120), (x, y + 2), (x + ancho, y + 2), 1); y += 10
        rol = ROL_POKEMON.get(nombre, '')
        if rol:
            ventana.blit(fuente(24).render('Rol: ' + rol.title(), True, (255, 210, 90)), (x, y)); y += 26
            y = _parrafo(ventana, {'atacante': 'pega fuerte; su primer especial es una versión potenciada de su ataque a distancia.',
                                   'tanque': 'aguanta mucho; sus especiales lo defienden y empujan alrededor.',
                                   'estratega': 'pone estados y se cura; recarga sus especiales rápido.',
                                   'velocista': 'rápido; embiste con su tipo y se acelera.'}.get(rol, ''), x, y, ancho) + 6
        sin = datos.pokemones.sinergia_de(nombre, m.get('sinergia'))
        ventana.blit(fuente(24).render('Desde la banca', True, (255, 210, 90)), (x, y)); y += 26
        y = _parrafo(ventana, 'Sinergia: ' + (', '.join('+' + str(round(v * 100, 1)) + '% ' + datos.pokemones.SINERGIAS.get(c_, c_) for c_, v in sin.items()) or 'nada'), x, y, ancho)
        try: y = _parrafo(ventana, 'Asistencia (F / G): ' + acc['asistencia'](m), x, y, ancho) + 6
        except Exception: pass
        tipos_m = [datos.pokemones.normalizar_tipo(t) for t in datos.pokemones.pokemones[nombre].get('tipo', [])]
        posibles = mecanicas.lazos_posibles(nombre, tipos_m)                  # los lazos de equipo que puede formar
        if posibles and y < area.bottom - 60:
            ventana.blit(fuente(24).render('Lazos de equipo', True, (255, 210, 90)), (x, y)); y += 26
            for lazo, con, da in posibles:
                if y > area.bottom - 24: break
                y = _parrafo(ventana, lazo + ' (' + mecanicas.texto_bono(da) + '): ' + con + '.', x, y, ancho, 17, max_lineas=2)
            y += 6
        if nombre in mecanicas.ENEMIGO:
            ventana.blit(fuente(24).render('Como enemigo', True, (255, 210, 90)), (x, y)); y += 26
            _parrafo(ventana, mecanicas.ENEMIGO_TXT[mecanicas.ENEMIGO[nombre]], x, y, ancho)


    def _pagina_mt(ventana, m, j, area, scroll):
        """Las MT que puede aprender: en que casillas van, que hacen, cuantas tenes y cual tiene puesta. Devuelve el scroll maximo."""
        caja(ventana, area, 'panel', PANEL)
        lista = mts.aprendibles(m['nombre'])
        objetos = j['inventario']['objetos']
        alto_f = 46
        maximo = max(0, len(lista) * alto_f + 40 - area.height)
        ventana.set_clip(area.inflate(-8, -8))
        y = area.y + 10 - scroll
        ventana.blit(fuente(20).render(str(len(lista)) + ' MT que puede aprender (se enseñan desde la pestaña Ficha, en la casilla del movimiento)', True, (200, 205, 220)), (area.x + 14, y)); y += 30
        for clave in lista:
            mt = mts.MTS[clave]
            if area.y - alto_f < y < area.bottom:
                fila = pygame.Rect(area.x + 10, y, area.width - 20, alto_f - 4)
                puesta = clave in (m.get('movs') or [])
                pygame.draw.rect(ventana, (44, 58, 44) if puesta else (34, 36, 50), fila, border_radius=6)
                tipo = normalizar_tipo(mt['tipo'])
                xx = fila.x + 8 + chip_tipo(ventana, tipo, fila.x + 8, fila.y + 4)
                ventana.blit(fuente(22).render(mt['nombre'], True, 'white'), (xx + 4, fila.y + 4))
                casillas = 'E / Q / Shift / R' if mt['casillas'] == 'todas' else 'Shift / R'
                tengo = objetos.get(clave, 0)
                d_ = fuente(18).render(casillas + '   ' + datos.describir_movimiento(mt['datos'])[:70], True, (190, 200, 220)); ventana.blit(d_, (fila.x + 10, fila.y + 24))
                t = fuente(18).render(('PUESTA  ' if puesta else '') + ('tenés ' + str(tengo) if tengo else 'no tenés'), True, (140, 255, 150) if (puesta or tengo) else (150, 150, 165))
                ventana.blit(t, t.get_rect(topright=(fila.right - 10, fila.y + 6)))
            y += alto_f
        ventana.set_clip(None)
        if not lista: ventana.blit(fuente(24).render('No aprende ninguna MT', True, 'white'), (area.x + 20, area.y + 50))
        return maximo


    def ficha(ui, j, i, acc):
        """Ficha de un miembro: stats con IV y EV (para gastar puntos), sinergia, sus 4 movimientos (para enseñar MT), sus 2 objetos y evolucion.
        Abajo, un recuadro explica lo que tenes elegido (que hace el stat, el movimiento, el objeto...)."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        elegido = 0
        reloj = pygame.time.Clock()
        animador, ficha_zonas = None, {}
        aviso = {'texto': '', 'hasta': 0}
        sinergias = [None] + list(datos.pokemones.SINERGIAS)
        pagina, scroll_p, max_scroll_p, pestañas_r = 0, 0, 0, []
        while True:
            m = j['equipo'][i]
            m.setdefault('items', []); m.setdefault('sinergia', None)
            if not animador or animador.pokemon != m['nombre']:
                animador = AnimadorPokemon(m['nombre'], pygame.Rect(0, 0, 10, 10), 110); animador.cambiar('idle', 0, True)
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
                    if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4): pagina = e.key - pygame.K_1; scroll_p = 0
                    if e.key == pygame.K_q: pagina = (pagina + 1) % len(PESTAÑAS_FICHA); scroll_p = 0
                    if pagina == 0:
                        if e.key in (pygame.K_UP, pygame.K_w): elegido = (elegido - 1) % len(filas)
                        if e.key in (pygame.K_DOWN, pygame.K_s): elegido = (elegido + 1) % len(filas)
                        if e.key in (pygame.K_RETURN, pygame.K_e): accion = filas[elegido]
                    else:                                                  # en las otras pestañas arriba/abajo desplaza
                        if e.key in (pygame.K_UP, pygame.K_w): scroll_p = max(0, scroll_p - 46)
                        if e.key in (pygame.K_DOWN, pygame.K_s): scroll_p = min(max_scroll_p, scroll_p + 46)
                    if e.key in (pygame.K_LEFT, pygame.K_a): i = (i - 1) % len(j['equipo']); animador = None
                    if e.key in (pygame.K_RIGHT, pygame.K_d): i = (i + 1) % len(j['equipo']); animador = None
                if e.type == pygame.MOUSEWHEEL and pagina != 0: scroll_p = max(0, min(max_scroll_p, scroll_p - e.y * 46))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for k_, r in enumerate(pestañas_r):
                        if r.collidepoint(ui['a_logico'](e.pos)): pagina = k_; scroll_p = 0
                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION) and pagina == 0:
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
                        antes_evo = m['nombre']; acc['evolucionar'](i, valor); animacion_evolucion(ui, m['nombre'], antes_evo)
                if clase == 'mov':
                    mt = elegir_mt(ui, j, m, valor)
                    if mt == 'salir': return 'salir'
                    if mt: acc['enseñar'](i, valor, mt)
                if clase == 'item':
                    r = elegir_objeto(ui, j, m, valor)
                    if r == 'salir': return 'salir'
                    if r is not None: acc['equipar'](i, valor, r or None)
            # ----- panel izquierdo: el pokemon sobre su pedestal -----
            ahora = pygame.time.get_ticks()
            fondo(ventana)
            izq = pygame.Rect(16, 16, 312, H - 32)
            caja(ventana, izq, 'panel', PANEL)
            tipos_m = [normalizar_tipo(t) for t in pokemones[m['nombre']].get('tipo', [])]
            color_t = COLORES_TIPO.get(tipos_m[0] if tipos_m else '', (150, 150, 150))
            pygame.draw.rect(ventana, color_t, (izq.x + 6, izq.y + 6, izq.width - 12, 5))
            ventana.blit(fuente(40).render(m['nombre'].replace('_', ' ').title(), True, 'white'), (izq.x + 18, izq.y + 16))
            x = izq.x + 18
            for tipo in tipos_m: x += chip_tipo(ventana, tipo, x, izq.y + 58)
            rol = ROL_POKEMON.get(m['nombre'], '')
            ventana.blit(fuente(22).render(rol.title(), True, (200, 220, 255)), (x + 4, izq.y + 62))
            cx_, cy_ = izq.centerx, izq.y + 170
            brillo = pygame.Surface((200, 200), pygame.SRCALPHA)
            for rr, a_ in ((92, 28), (66, 42), (44, 58)): pygame.draw.circle(brillo, (*color_t, a_), (100, 100), rr + round(3 * math.sin(ahora / 420)))
            ventana.blit(brillo, (cx_ - 100, cy_ - 110))
            pygame.draw.ellipse(ventana, tuple(max(0, c - 90) for c in color_t), (cx_ - 58, cy_ + 36, 116, 24))
            pygame.draw.ellipse(ventana, tuple(min(255, c + 40) for c in color_t), (cx_ - 58, cy_ + 32, 116, 24), 3)
            animador.rect.center = (cx_, round(cy_ + 3 * math.sin(ahora / 320)) - 4)
            animador.actualizar()
            if not animador.dibujar(ventana): pygame.draw.circle(ventana, (200, 200, 200), (cx_, cy_), 50)
            y = izq.y + 236
            nv_img = hud('nv', 2)
            if nv_img: ventana.blit(nv_img, (izq.x + 18, y + 4)); xn = izq.x + 22 + nv_img.get_width()
            else: xn = izq.x + 18
            ventana.blit(fuente(30).render(str(m['nivel']), True, 'white'), (xn, y - 2))
            corazones = min(5, m['amistad'] * 6 // 256)                     # amistad: de 0 a 5 corazones
            for k_ in range(5):
                hx, hy = izq.right - 110 + k_ * 18, y + 6
                col_c = (255, 110, 150) if k_ < corazones else (70, 70, 90)
                pygame.draw.circle(ventana, col_c, (hx - 3, hy), 5); pygame.draw.circle(ventana, col_c, (hx + 3, hy), 5)
                pygame.draw.polygon(ventana, col_c, [(hx - 8, hy + 1), (hx + 8, hy + 1), (hx, hy + 9)])
            y += 34
            barra_exp(ventana, izq.x + 18, y, izq.width - 36, progreso.progreso_nivel(m))
            falta = max(0, progreso.xp_para(m['nombre'], m['nivel'] + 1) - m['xp'])
            ventana.blit(fuente(18).render('EXP: faltan ' + str(falta) + ' para el nivel ' + str(m['nivel'] + 1), True, (190, 210, 255)), (izq.x + 18, y + 12))
            y += 36
            for linea in ajustar_texto('Naturaleza ' + progreso.texto_naturaleza(m.get('naturaleza')), fuente(18), izq.width - 36)[:2]:
                ventana.blit(fuente(18).render(linea, True, (240, 200, 230)), (izq.x + 18, y)); y += 18
            y += 4
            for r_ in progreso.requisitos(m['nombre'])[:2]:
                ventana.blit(fuente(18).render('> ' + r_['a'].replace('_', ' ').title() + ': ' + progreso.texto_requisito(r_), True, (200, 240, 200)), (izq.x + 18, y)); y += 18
            unico = mecanicas.texto_de(m['nombre'])                       # lo que hace unica a su linea (mecanicas.py)
            if unico:
                franja = pygame.Rect(izq.x + 10, izq.bottom - 96, izq.width - 20, 64)
                pygame.draw.rect(ventana, (24, 44, 34), franja, border_radius=6); pygame.draw.rect(ventana, (90, 200, 120), franja, 1, border_radius=6)
                for k_, linea in enumerate(ajustar_texto(unico, fuente(18), franja.width - 16)[:3]):
                    ventana.blit(fuente(18).render(linea, True, (170, 255, 170)), (franja.x + 8, franja.y + 5 + k_ * 19))

            ventana.blit(fuente(18).render('izq/der: otro   1-4 o Q: pestaña   ESC: volver', True, (200, 200, 210)), (izq.x + 12, izq.bottom - 26))
            pestañas_r = _pestañas_ficha(ventana, pagina, color_t)
            if pagina != 0:                                               # Ataques, Habilidad o MT: la columna derecha entera
                ficha_zonas = {}
                area = pygame.Rect(340, 48, W - 356, H - 64)
                if pagina == 1: _pagina_ataques(ventana, m, acc, area)
                elif pagina == 2: _pagina_habilidad(ventana, m, acc, area)
                else: max_scroll_p = _pagina_mt(ventana, m, j, area, scroll_p)
                ui['presentar'](); reloj.tick(60); continue
            # ----- derecha: stats con las barras de BW, movimientos, objetos y acciones en paneles en flecha -----
            ficha_zonas = {}
            col_a, col_b, ancho_col = 340, 664, 316
            totales = {s_: progreso.stat(m['nombre'], s_, m['nivel'], m['ivs'][s_], m['evs'][s_], m.get('naturaleza')) for s_ in progreso.STATS}
            mejor = max(totales.values()) or 1
            ventana.blit(fuente(28).render('Stats', True, 'white'), (col_a, 46))
            puntos = fuente(22).render('Puntos: ' + str(m['puntos']), True, ALERTA if m['puntos'] else (200, 200, 210))
            ventana.blit(puntos, (col_a + ancho_col - puntos.get_width(), 52))
            ventana.blit(fuente(28).render('Movimientos', True, 'white'), (col_b, 46))
            y_a, y_b = 78, 78
            movs_txt = acc['movs'](m)
            for k_, (clase, valor) in enumerate(filas):
                if clase in ('stat', 'sinergia', 'evo', 'caramelo', 'activar', 'volver'):
                    if clase == 'sinergia': y_a += 4
                    if clase in ('evo', 'caramelo', 'activar', 'volver') and filas[k_ - 1][0] in ('stat', 'sinergia'): y_a += 8
                    r = pygame.Rect(col_a, y_a, ancho_col, 34 if clase == 'stat' else 30); y_a += r.height + 4
                else:
                    if clase == 'item' and valor == 0:
                        y_b += 6; ventana.blit(fuente(28).render('Objetos (hasta ' + str(tienda.MAX_EQUIPADOS) + ')', True, 'white'), (col_b, y_b)); y_b += 32
                    r = pygame.Rect(col_b, y_b, ancho_col, 34); y_b += 38
                ficha_zonas[k_] = r
                elegida = k_ == elegido
                fila_color = {'evo': 2, 'caramelo': 2, 'volver': 1}.get(clase, 0)          # verde evolucionar, rojo volver, azul lo demas
                panel_flecha(ventana, r.move(6 if elegida else 0, 0), (fila_color, 1 if elegida else 0))
                r = r.move(6 if elegida else 0, 0)
                if clase == 'stat':
                    efecto = progreso.factor_naturaleza(m.get('naturaleza'), valor)   # verde si la naturaleza lo sube, rojo si lo baja
                    ventana.blit(fuente(22).render(progreso.NOMBRE_STAT[valor], True, (140, 255, 150) if efecto > 1 else (255, 150, 150) if efecto < 1 else 'white'), (r.x + 18, r.y + 4))
                    ventana.blit(fuente(22).render(str(totales[valor]), True, (255, 230, 120)), (r.x + 104, r.y + 4))
                    barra_vida(ventana, (r.x + 150, r.y + 6, 126, 12), totales[valor] / mejor, False)   # la barra de HP de BW: el perfil del pokemon
                    pygame.draw.rect(ventana, (20, 30, 60), (r.x + 18, r.y + 25, 258, 4))
                    pygame.draw.rect(ventana, (110, 200, 255), (r.x + 18, r.y + 25, round(258 * m['evs'][valor] / progreso.EV_MAX_STAT), 4))   # los EV
                    if not progreso.motivo_sin_ev(m, valor) and (ahora // 300) % 2: ventana.blit(fuente(28).render('+', True, (120, 255, 120)), (r.right - 30, r.y + 2))
                elif clase == 'sinergia':
                    clave = list(datos.pokemones.sinergia_de(m['nombre'], m['sinergia']))[0] if datos.pokemones.sinergia_de(m['nombre'], m['sinergia']) else None
                    ventana.blit(fuente(22).render('Sinergia: ' + datos.pokemones.SINERGIAS.get(clave, '-') + ('' if m['sinergia'] else ' (rol)'), True, (190, 235, 255)), (r.x + 18, r.y + 7))
                elif clase == 'mov':
                    chip = pygame.Rect(r.x + 16, r.y + 7, 50, 20)
                    pygame.draw.rect(ventana, (20, 30, 60), chip, border_radius=4); pygame.draw.rect(ventana, (130, 160, 230), chip, 1, border_radius=4)
                    tt = fuente(18).render(mts.CASILLAS[valor], True, 'white'); ventana.blit(tt, tt.get_rect(center=chip.center))
                    ventana.blit(fuente(22).render(str(movs_txt[valor])[:22], True, 'white'), (r.x + 74, r.y + 8))
                    if m['movs'][valor]: ventana.blit(fuente(18).render('MT', True, (150, 200, 255)), (r.right - 40, r.y + 9))
                elif clase == 'item':
                    clave = m['items'][valor] if valor < len(m['items']) else None
                    icono = icono_objeto(clave, 24) if clave else None
                    if icono: ventana.blit(icono, (r.x + 16, r.y + 5))
                    ventana.blit(fuente(22).render(tienda.ITEMS[clave]['nombre'] if clave else '(vacío)', True, 'white' if clave else (160, 165, 180)), (r.x + 48, r.y + 8))
                elif clase == 'evo': ventana.blit(fuente(22).render('¡Evolucionar a ' + valor['a'].replace('_', ' ').title() + '!', True, (255, 240, 140)), (r.x + 18, r.y + 7))
                elif clase == 'caramelo':
                    icono = icono_objeto('caramelo_raro', 22)
                    if icono: ventana.blit(icono, (r.x + 16, r.y + 5))
                    ventana.blit(fuente(22).render('Caramelo Raro (x' + str(j['inventario']['objetos'].get('caramelo_raro', 0)) + ')', True, 'white'), (r.x + 46, r.y + 7))
                elif clase == 'activar': ventana.blit(fuente(22).render('Poner a pelear', True, 'white'), (r.x + 18, r.y + 7))
                else: ventana.blit(fuente(22).render('Volver', True, 'white'), (r.x + 18, r.y + 7))
                if elegida: dibujar_esquinas(ventana, r.inflate(4, 2), margen=3, largo=10, grosor=2)
            # ----- recuadro con la explicacion de lo elegido -----
            info = pygame.Rect(col_b, max(y_b + 8, H - 196), ancho_col, H - 16 - max(y_b + 8, H - 196))
            caja(ventana, info, 'panel', PANEL)
            pygame.draw.rect(ventana, color_t, (info.x + 6, info.y + 6, 4, info.height - 12))
            lineas = _explicar(filas[elegido], m, j, acc)
            if pygame.time.get_ticks() < aviso['hasta']: lineas = [aviso['texto']] + lineas
            y = info.y + 10
            for n_, linea in enumerate(lineas):
                for parte in ajustar_texto(linea, fuente(19), info.width - 30):
                    if y > info.bottom - 20: break
                    ventana.blit(fuente(19).render(parte, True, ALERTA if n_ == 0 and pygame.time.get_ticks() < aviso['hasta'] else (235, 235, 235)), (info.x + 18, y)); y += 19
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
        """Lo que tenes: arriba el cinturon (las curaciones, como mucho 5, en el orden en que se usan con la tecla de curarse: aca se
        usan en quien elijas, se suben, se bajan o se tiran), despues objetos para equipar, MT, piedras, lo que llevan puesto tus
        pokemon y lo que es de todo el equipo, con lo que hace cada cosa."""
        inv = j['inventario']
        cinturon = inv.setdefault('cinturon', [])
        elegido = 0
        while True:
            filas, claves = [], []
            filas.append(('Cinturón  (' + str(len(cinturon)) + '/' + str(tienda.CINTURON_MAX) + ')',
                          'Las curaciones se usan en este orden con ' + acc.get('tecla_curar', 'Z') + ' (en el que pelea). ENTER en una: usar, subir, bajar o tirar.'))
            claves.append(None)
            for i_, k_ in enumerate(cinturon):
                filas.append(('   ' + str(i_ + 1) + '.  ' + tienda.ITEMS[k_]['nombre'], tienda.ITEMS[k_]['desc'])); claves.append(('cinturon', i_))
            for i_ in range(len(cinturon), tienda.CINTURON_MAX):
                filas.append(('   ' + str(i_ + 1) + '.  (vacío)', 'Las curaciones las vende Chikorita rosa en la tienda.')); claves.append(None)
            for k_, n in inv['objetos'].items():
                if n > 0 and not tienda.es_curativo(k_): filas.append((tienda.ITEMS[k_]['nombre'] + '  x' + str(n), tienda.ITEMS[k_]['desc'])); claves.append(None)
            for m in j['equipo'] + j.get('reserva', []):
                for k_ in m.get('items', []): filas.append((tienda.ITEMS[k_]['nombre'] + '  (lo lleva ' + m['nombre'].title() + ')', tienda.ITEMS[k_]['desc'])); claves.append(None)
            for k_ in dict.fromkeys(inv['comprados']):
                if 'permanente' in tienda.ITEMS[k_]: filas.append((tienda.ITEMS[k_]['nombre'] + '  (equipo)', tienda.ITEMS[k_]['desc'])); claves.append(None)
            for linea in tienda.activos(inv): filas.append((linea, 'activo para todo el equipo (el numero son las salas que le quedan)')); claves.append(None)
            r = lista_detallada(ui, 'Mochila', filas, 'Curaciones: en el cinturón. Objetos, MT y piedras, desde la ficha de cada pokemon.', elegido)
            if r == 'salir': return 'salir'
            if r is None: return None
            elegido = r
            clave = claves[r]
            if not clave: continue
            i_ = clave[1]
            item = tienda.ITEMS[cinturon[i_]]
            acciones_ = [('usar', 'Usar')] + ([('subir', 'Subir (lugar ' + str(i_) + ')')] if i_ > 0 else []) + \
                        ([('bajar', 'Bajar (lugar ' + str(i_ + 2) + ')')] if i_ < len(cinturon) - 1 else []) + [('tirar', 'Tirar'), ('nada', 'Cancelar')]
            q = preguntar(ui, str(i_ + 1) + '. ' + item['nombre'], [t for _, t in acciones_], item['desc'])
            if q == 'salir': return 'salir'
            if q is None: continue
            accion = acciones_[q][0]
            if accion == 'subir': cinturon[i_ - 1], cinturon[i_] = cinturon[i_], cinturon[i_ - 1]; elegido = r - 1; acc['refrescar'](); continue
            if accion == 'bajar': cinturon[i_ + 1], cinturon[i_] = cinturon[i_], cinturon[i_ + 1]; elegido = r + 1; acc['refrescar'](); continue
            if accion == 'tirar':
                c = preguntar(ui, '¿Tirar ' + item['nombre'] + '?', ['Tirar', 'No'], 'se pierde (no te devuelven las monedas)')
                if c == 'salir': return 'salir'
                if c == 0: cinturon.pop(i_); acc['refrescar']()
                continue
            if accion != 'usar': continue
            miembros = [(k, m) for k, m in enumerate(j['equipo'])] + [(('r', k), m) for k, m in enumerate(j.get('reserva', []))]
            opciones_ = [m['nombre'].replace('_', ' ').title() + '  ' + (('debilitado' if m['vida'] <= 0 else str(round(m['vida'])) + '/' + str(m['max_vida']) + ' PS')
                         + (' - con estado' if m.get('estados') else '')) for _, m in miembros]
            q = preguntar(ui, '¿En quién usás ' + item['nombre'] + '?', opciones_ + ['Cancelar'], item['desc'])
            if q == 'salir': return 'salir'
            if q is None or q >= len(miembros): continue
            texto = acc['usar'](miembros[q][0], i_)
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


    def animacion_evolucion(ui, nombre, antes=None):
        """Evolucion como en los juegos: el pokemon brilla, se vuelve una silueta blanca que cambia entre la forma vieja y la nueva
        cada vez mas rapido, un destello, y aparece el nuevo con su color. ENTER / E / clic la adelantan al final."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        centro = (W // 2, H // 2 - 10)
        nuevo = AnimadorPokemon(nombre, pygame.Rect(0, 0, 10, 10), 170); nuevo.rect.center = centro; nuevo.cambiar('idle', 0, True)
        viejo = None
        if antes and antes != nombre:
            viejo = AnimadorPokemon(antes, pygame.Rect(0, 0, 10, 10), 150); viejo.rect.center = centro; viejo.cambiar('idle', 0, True)
        blancos = {}
        def silueta(a):
            """La silueta del pokemon que evoluciona (blanca, para el destello)."""
            c = a.cuadro()
            if not c: return None
            img, x, y = c
            if id(img) not in blancos:
                b = img.copy(); b.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX); blancos[id(img)] = b
            return blancos[id(img)], x, y
        chispas = [{'ang': random.uniform(0, math.tau), 'dist': random.uniform(160, 380), 'vel': random.uniform(1.5, 4), 'tam': random.randint(2, 4)} for _ in range(70)]
        reloj = pygame.time.Clock()
        inicio = pygame.time.get_ticks()
        BRILLO, CAMBIOS, DESTELLO, FIN = 700, 3900, 4400, 6600              # ms de cada parte
        nombre_v = (antes or nombre).replace('_', ' ').title(); nombre_n = nombre.replace('_', ' ').title()
        estado_grito = []
        if antes: sonido.grito(antes, 0.9)
        while True:
            t = pygame.time.get_ticks() - inicio
            for e in controles.eventos():
                if e.type == pygame.QUIT: return
                if (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE, pygame.K_ESCAPE)) or (e.type == pygame.MOUSEBUTTONDOWN):
                    if t < DESTELLO: inicio -= DESTELLO - t; t = DESTELLO
                    elif t > DESTELLO + 600: return
            if t >= FIN: return
            # fondo: degrade oscuro con rayos de luz que giran (mas fuertes cerca del destello)
            k_luz = min(1.0, t / CAMBIOS)
            ventana.fill((round(10 + 20 * k_luz), round(12 + 18 * k_luz), round(30 + 40 * k_luz)))
            rayos = pygame.Surface((W, H), pygame.SRCALPHA)
            for r_ in range(12):
                a = t / 2400 + r_ * math.tau / 12
                p1 = (centro[0] + math.cos(a - 0.06) * 900, centro[1] + math.sin(a - 0.06) * 900)
                p2 = (centro[0] + math.cos(a + 0.06) * 900, centro[1] + math.sin(a + 0.06) * 900)
                pygame.draw.polygon(rayos, (255, 255, 230, round(10 + 40 * k_luz)), [centro, p1, p2])
            ventana.blit(rayos, (0, 0))
            halo = pygame.Surface((360, 360), pygame.SRCALPHA)
            for rr, al in ((170, 25), (120, 40), (80, 60)): pygame.draw.circle(halo, (255, 255, 255, round(al * (0.3 + k_luz))), (180, 180), rr + round(6 * math.sin(t / 150)))
            ventana.blit(halo, (centro[0] - 180, centro[1] - 180))
            for c in chispas:                                              # chispas que van hacia el pokemon
                if t < DESTELLO:
                    c['dist'] -= c['vel'] * (1 + 2 * k_luz)
                    if c['dist'] < 30: c['dist'] = random.uniform(260, 400); c['ang'] = random.uniform(0, math.tau)
                else: c['dist'] += c['vel'] * 3                           # y despues del destello salen para afuera
                px, py = centro[0] + math.cos(c['ang']) * c['dist'], centro[1] + math.sin(c['ang']) * c['dist']
                pygame.draw.circle(ventana, (255, 250, 200), (round(px), round(py)), c['tam'])
            # el pokemon
            for a in (nuevo, viejo):
                if a: a.actualizar()
            if t < BRILLO:                                                 # brilla con su color
                a = viejo or nuevo
                a.dibujar(ventana)
                s = silueta(a)
                if s: s[0].set_alpha(round(255 * t / BRILLO)); ventana.blit(s[0], (s[1], s[2])); s[0].set_alpha(255)
            elif t < CAMBIOS:                                              # silueta blanca que cambia cada vez mas rapido
                k = (t - BRILLO) / (CAMBIOS - BRILLO)
                periodo = 420 * (1 - k) ** 2 + 40
                fase = int((t - BRILLO) / periodo) % 2
                a = nuevo if (fase or not viejo) else viejo
                s = silueta(a)
                if s:
                    escala = 1 + 0.06 * math.sin(t / 60)
                    img = pygame.transform.scale(s[0], (round(s[0].get_width() * escala), round(s[0].get_height() * escala)))
                    ventana.blit(img, img.get_rect(center=(s[1] + s[0].get_width() // 2, s[2] + s[0].get_height() // 2)))
                elif not a.dibujar(ventana): pygame.draw.circle(ventana, 'white', centro, 50)
            else:                                                          # el nuevo, con su color (y su pose si tiene)
                if t < DESTELLO + 50: nuevo.cambiar('pose', 0, False) if nuevo._buscar_animacion('pose') else None
                elif nuevo.esta_terminada(): nuevo.cambiar('idle', 0, True)
                if not nuevo.dibujar(ventana): pygame.draw.circle(ventana, (200, 200, 200), centro, 50)
                t_txt = (t - DESTELLO) / 500
                if t_txt > 0.3:
                    texto = fuente(46).render('¡' + nombre_v + ' evolucionó en ' + nombre_n + '!' if viejo else '¡Evolucionó en ' + nombre_n + '!', True, 'white')
                    caja_t = texto.get_rect(center=(W // 2, H - 100)).inflate(40, 20)
                    velo = pygame.Surface(caja_t.size, pygame.SRCALPHA); velo.fill((10, 10, 30, 190)); ventana.blit(velo, caja_t)
                    pygame.draw.rect(ventana, (255, 230, 120), caja_t, 2, border_radius=6)
                    ventana.blit(texto, texto.get_rect(center=caja_t.center))
            if t >= DESTELLO and not estado_grito: estado_grito.append(1); sonido.grito(nombre, 1.0)   # el nuevo grita al aparecer
            if DESTELLO - 200 < t < DESTELLO + 500:                        # el destello blanco
                velo = pygame.Surface((W, H)); velo.fill((255, 255, 255))
                velo.set_alpha(round(255 * max(0.0, 1 - abs(t - DESTELLO) / 500)))
                ventana.blit(velo, (0, 0))
            if t < DESTELLO:
                ayuda = fuente(22).render('¿Qué? ¡' + nombre_v + ' está evolucionando!', True, (230, 230, 240))
                ventana.blit(ayuda, ayuda.get_rect(center=(W // 2, H - 60)))
            ui['presentar'](); reloj.tick(60)

    return SimpleNamespace(**locals())


menus = armar_menus()
