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
from datos import mts, tienda
from sistema import controles, opciones, partidas, animaciones
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
    INICIALES = ('electrike', 'sandshrew', 'mareanie')
    SUEÑO = 8000                                     # ms sin tocar nada para que los pokemon del escenario se duerman
    _fuentes = {}
    _paneles = {}


    def fuente(tam):
        """Fuente del tamaño pedido (se crea una sola vez)."""
        if tam not in _fuentes: _fuentes[tam] = pygame.font.Font(None, tam)
        return _fuentes[tam]


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
        for x in range(0, W, t.get_width()):
            for y in range(0, H, t.get_height()): ventana.blit(t, (x, y))
        return True


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


    def boton(ventana, rect, texto, elegido=False, tam=34, valor=None):
        """Barra de opciones de BW (si no esta, boton oscuro con borde blanco como el menu de pausa). valor: texto a la derecha con < >."""
        caja(ventana, rect, 'boton_elegido' if elegido else 'boton', OSCURO, 3)
        t = fuente(tam).render(texto, True, 'white')
        if valor is None: ventana.blit(t, t.get_rect(center=rect.center))
        else:
            ventana.blit(t, t.get_rect(midleft=(rect.x + 18, rect.centery)))
            v = fuente(tam).render('< ' + str(valor) + ' >', True, (230, 230, 120) if elegido else (220, 220, 220))
            ventana.blit(v, v.get_rect(midright=(rect.right - 18, rect.centery)))
        if elegido: dibujar_esquinas(ventana, rect.inflate(10, 10))


    def titulo(ventana, texto, x=60, y=40, tam=72, color=None):
        """Titulo grande de un menu."""
        ventana.blit(fuente(tam).render(texto, True, color or TINTA), (x, y))


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
        """Dibuja POKEMANIC (las letras Unown flotan un poco). donde: como en get_rect (center=..., topright=...)."""
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
        t = fuente(20).render(tipo, True, 'black')
        r = pygame.Rect(x, y, t.get_width() + 14, 22)
        pygame.draw.rect(ventana, COLORES_TIPO.get(tipo, (150, 150, 150)), r, border_radius=8)
        ventana.blit(t, (x + 7, y + 4))
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
        filas = ['volumen', 'modo', 'resolucion', 'pantalla_completa', 'estilo_equipo', 'controles', 'glosario', 'volver']
        textos = {'volumen': 'Sonido', 'modo': 'Combate', 'resolucion': 'Resolucion', 'pantalla_completa': 'Pantalla completa',
                  'estilo_equipo': 'Menu de equipo', 'controles': 'Controles', 'glosario': 'Glosario', 'volver': 'Volver'}
        ayudas = {'modo': {'mouse': 'Apuntas con el mouse', 'teclas': 'Atacas hacia donde caminaste por ultima vez', 'mixto': 'Teclas hasta que moves el mouse'},
                  'estilo_equipo': {'clasico': 'Lista como en los juegos de Pokemon', 'escenario': 'Tus pokemon parados en un escenario (se duermen si esperas)'}}
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

        while True:
            botones = [pygame.Rect(100, 116 + i * 54, 520, 46) for i in range(len(filas))]
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
            if accion in ('modo', 'resolucion', 'pantalla_completa', 'estilo_equipo', 'volumen'): cambiar(accion, 1)
            fondo(ventana)
            titulo(ventana, 'AJUSTES', 100, 40)
            valores = {'volumen': config['volumen'], 'modo': config['modo'].title(), 'resolucion': config['resolucion'],
                       'pantalla_completa': 'Si' if config['pantalla_completa'] else 'No', 'estilo_equipo': config['estilo_equipo'].title()}
            for i, clave in enumerate(filas): boton(ventana, botones[i], textos[clave], i == elegido, 32, valores.get(clave))
            clave = filas[elegido]
            ayuda = ayudas.get(clave, {}).get(config.get(clave)) if clave in ayudas else None
            if clave == 'volumen':
                for i in range(10): pygame.draw.rect(ventana, 'white' if i < config['volumen'] // 10 else (90, 90, 90), (660 + i * 28, 140, 22, 16))
            if ayuda:
                for k, linea in enumerate(ajustar_texto(ayuda, fuente(26), 300)): ventana.blit(fuente(26).render(linea, True, 'white'), (660, 130 + elegido * 56 + k * 24))
            ventana.blit(fuente(22).render('Flechas: elegir y cambiar   ENTER: entrar   ESC: volver', True, (240, 240, 240)), (100, H - 40))
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
            botones = {i: pygame.Rect(100, 110 + (i - scroll) * alto, 640, alto - 6) for i in range(scroll, min(len(filas), scroll + visibles))}
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
            titulo(ventana, 'CONTROLES', 100, 36, 60)
            if dispositivo == 'control' and not controles.hay_control():
                ventana.blit(fuente(24).render('(no hay ningun control conectado)', True, TINTA), (440, 56))
            for i, b in botones.items():
                clave = filas[i]
                if clave == 'dispositivo': boton(ventana, b, 'Dispositivo', i == elegido, 28, dispositivo.title())
                elif clave == 'perfil': boton(ventana, b, 'Perfil', i == elegido, 28, c['perfil_' + dispositivo] + 1)
                elif clave == 'restaurar': boton(ventana, b, 'Restaurar preset de este perfil', i == elegido, 28)
                elif clave == 'volver': boton(ventana, b, 'Volver', i == elegido, 28)
                else:
                    caja(ventana, b, 'boton_elegido' if i == elegido else 'boton', OSCURO, 2)
                    ventana.blit(fuente(28).render(nombres[clave], True, 'white'), (b.x + 16, b.y + 8))
                    tecla = fuente(28).render(str(perfil_actual.get(clave, '-')).upper(), True, (240, 220, 120))
                    ventana.blit(tecla, tecla.get_rect(midright=(b.right - 16, b.centery)))
                    if i == elegido: dibujar_esquinas(ventana, b.inflate(8, 8))
            ventana.blit(fuente(22).render('ENTER sobre una accion: cambiarla   izq/der: dispositivo y perfil   ESC: volver', True, (240, 240, 240)), (100, H - 36))
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
            titulo(ventana, 'MENU DEBUG', 100, 40, 64, (250, 220, 120))
            for i, (clave, texto) in enumerate(TRUCOS):
                valor = ('x' + str(t.get(clave, 0))) if clave == 'subir_niveles' else ('Si' if t.get(clave) else 'No')
                boton(ventana, botones[i], texto, i == elegido, 28, valor)
            boton(ventana, botones[-1], 'Volver', elegido == len(TRUCOS), 28)
            ventana.blit(fuente(22).render('Truquitos de prueba: no se guardan', True, (230, 230, 230)), (100, H - 36))
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
            'Escondido en hierba o sombra (si tu tipo puede) los enemigos casi no te ven.']
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
        s['Tienda'] = ['Aparece cada 5 a 10 salas. Chikorita vende objetos: acercate y apreta ' + tecla('interactuar') + '.',
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
                            'Cuando alguien puede evolucionar te avisa: entra al menu de equipo (' + tecla('equipo') + ') y elegi Evolucionar.']
        s['Amistad'] = ['Los pokemon no se capturan: a veces uno que derrotaste se queda con corazones porque quiere unirse a vos.',
                        'Acercate y apreta ' + tecla('interactuar') + ' para hablarle. Si tu equipo esta lleno (3), elegi a quien mandar a la reserva.',
                        'Es mas probable con los pokemon comunes, si sos de mas nivel y con el Lazo Amistad. Los jefes no se unen.',
                        'Si te vas de la sala sin hablarle, se va.']
        s['Salas y eras'] = ['5 eras de 30 salas: Glacial, Piedra, Metales, Media y Moderna. Al final, El Origen: Regigigas y Arceus.',
                             'Semijefe en la sala 15 y el Regi de la era en la 30. Las puertas muestran que hay detras.',
                             'Limpia la sala para que aparezca la llave; con la llave se abren las puertas.',
                             'La vida no se recupera sola: al limpiar una sala el equipo recupera un 12%.',
                             'Con la sala completada podes volver por la puerta por la que entraste; las salas hechas quedan hechas.']
        s['Partidas'] = ['Hay 3 partidas guardadas (Jugar > elegis una ranura).',
                         'Se guarda sola al entrar a cada sala, al completarla y al comprar: equipo, niveles, experiencia, EV, MT, objetos, monedas y por donde ibas.',
                         'Si cae todo el equipo podes reintentar la sala desde como estabas al entrar.']
        return s


    def glosario(ui):
        """Glosario: secciones con terrenos, maquinas, climas, tipos y controles, con scroll."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        secciones = secciones_glosario(ui['config'])
        nombres = list(secciones)
        elegido, scroll = 0, 0
        reloj = pygame.time.Clock()
        panel = pygame.Rect(320, 100, W - 350, H - 150)
        while True:
            lineas = []
            for linea in secciones[nombres[elegido]]: lineas += ajustar_texto(linea, fuente(24), panel.width - 30) or ['']
            maximo = max(0, len(lineas) * 22 - panel.height + 30)
            botones = [pygame.Rect(40, 96 + i * 44, 250, 38) for i in range(len(nombres))]
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
            titulo(ventana, 'GLOSARIO', 40, 26, 60)
            for i, b in enumerate(botones): boton(ventana, b, nombres[i], i == elegido, 26)
            caja(ventana, panel, 'panel', PANEL)
            ventana.set_clip(panel.inflate(-10, -10))
            for i, linea in enumerate(lineas):
                y = panel.y + 14 + i * 22 - scroll
                if panel.y - 20 < y < panel.bottom:
                    color = (240, 200, 80) if linea.startswith('[') else (235, 235, 235)
                    ventana.blit(fuente(24).render(linea, True, color), (panel.x + 15, y))
            ventana.set_clip(None)
            ventana.blit(fuente(22).render('arriba/abajo: seccion   izq/der o rueda: desplazar   ESC: volver', True, (240, 240, 240)), (40, H - 36))
            ui['presentar'](); reloj.tick(60)


    # ---------- partidas guardadas ----------

    def elegir_partida(ui, resumenes):
        """Las 3 ranuras de guardado. Devuelve ('continuar' | 'nueva', ranura), None si volves o 'salir'."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        elegido, reloj = 0, pygame.time.Clock()
        while True:
            cajas = [pygame.Rect(60, 120 + k * 140, W - 120, 120) for k in range(len(resumenes))]
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
                r = preguntar(ui, 'Partida ' + str(ranura) + ': ' + resumen.get('era', '') + ', sala ' + str(resumen.get('sala', '?')),
                              ['Continuar', 'Empezar de nuevo (borra esta)', 'Borrar', 'Cancelar'])
                if r == 'salir': return 'salir'
                if r == 0: return 'continuar', ranura
                if r == 1 and preguntar(ui, 'Seguro? Se pierde la partida ' + str(ranura), ['Si, empezar de nuevo', 'No']) == 0: return 'nueva', ranura
                if r == 2 and preguntar(ui, 'Seguro que borras la partida ' + str(ranura) + '?', ['Si, borrar', 'No']) == 0:
                    partidas.borrar(ranura); resumenes[accion] = None
            fondo(ventana)
            titulo(ventana, 'Partidas', 60, 30, 64)
            for k, r in enumerate(cajas):
                caja(ventana, r, 'boton_elegido' if k == elegido else 'boton', OSCURO, 2)
                resumen = resumenes[k]
                ventana.blit(fuente(34).render('Partida ' + str(k + 1), True, 'white'), (r.x + 18, r.y + 12))
                if not resumen:
                    ventana.blit(fuente(26).render('Vacia - empezar una partida nueva', True, (190, 190, 190)), (r.x + 18, r.y + 54)); continue
                ventana.blit(fuente(24).render(resumen.get('era', '') + ' - sala ' + str(resumen.get('sala', '?')) + '/' + str(resumen.get('salas', '?')) +
                                               '   $ ' + str(resumen.get('monedas', 0)), True, (240, 220, 120)), (r.x + 200, r.y + 18))
                ventana.blit(fuente(20).render('guardada ' + str(resumen.get('fecha', '')), True, (190, 190, 190)), (r.right - 210, r.y + 18))
                x = r.x + 18
                for nombre, nivel in resumen.get('equipo', []):
                    img = ui['retrato'](nombre, 44)
                    if img: ventana.blit(img, (x, r.y + 56))
                    ventana.blit(fuente(24).render(nombre.replace('_', ' ').title() + ' Nv ' + str(nivel), True, 'white'), (x + 50, r.y + 70))
                    x += 250
                if k == elegido: dibujar_esquinas(ventana, r.inflate(8, 8))
            ventana.blit(fuente(22).render('ENTER o clic: elegir   ESC: volver   (se guarda sola al entrar a cada sala y al completarla)', True, 'white'), (60, H - 36))
            ui['presentar'](); reloj.tick(60)


    # ---------- inicial ----------

    def elegir_inicial(ui):
        """Elegis tu primer pokemon: Electrike, Sandshrew o Mareanie."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        animadores = []
        for i, n in enumerate(INICIALES):
            a = AnimadorPokemon(n, pygame.Rect(0, 0, 10, 10), 120); a.rect.center = (W // 2 + (i - 1) * 300, 300); a.cambiar('idle', 0, True)
            animadores.append(a)
        elegido = 1
        reloj = pygame.time.Clock()
        while True:
            cajas = [pygame.Rect(W // 2 + (i - 1) * 300 - 130, 170, 260, 330) for i in range(3)]
            for e in controles.eventos():
                if e.type == pygame.QUIT: return 'salir'
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: return None
                    if e.key in (pygame.K_LEFT, pygame.K_a): elegido = (elegido - 1) % 3
                    if e.key in (pygame.K_RIGHT, pygame.K_d): elegido = (elegido + 1) % 3
                    if e.key in (pygame.K_RETURN, pygame.K_e): return INICIALES[elegido]
                if e.type == pygame.MOUSEMOTION:
                    for i, c in enumerate(cajas):
                        if c.collidepoint(ui['a_logico'](e.pos)): elegido = i
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, c in enumerate(cajas):
                        if c.collidepoint(ui['a_logico'](e.pos)): return INICIALES[i]
            fondo_menu(ui, pygame.time.get_ticks(), False)
            velo = pygame.Surface((W, 90), pygame.SRCALPHA); velo.fill((0, 0, 0, 120)); ventana.blit(velo, (0, 36))   # que el titulo se lea sobre el fondo
            titulo(ventana, 'Elegi tu compañero', 60, 50, 64, 'white')
            for i, (n, a) in enumerate(zip(INICIALES, animadores)):
                c = cajas[i]
                velo = pygame.Surface(c.size, pygame.SRCALPHA); velo.fill((0, 0, 0, 170 if i == elegido else 110)); ventana.blit(velo, c)
                pygame.draw.rect(ventana, 'white', c, 3)
                a.cambiar('walk' if i == elegido else 'idle', 0, True); a.actualizar()
                if not a.dibujar(ventana): pygame.draw.circle(ventana, (200, 200, 200), a.rect.center, 40)
                t = fuente(40).render(n.title(), True, 'white'); ventana.blit(t, t.get_rect(center=(c.centerx, c.y + 210)))
                x = c.x + 20
                for tipo in pokemones[n].get('tipo', []): x += chip_tipo(ventana, normalizar_tipo(tipo), x, c.y + 240)
                ventana.blit(fuente(22).render('Rol: ' + ROL_POKEMON.get(n, '-'), True, (220, 220, 220)), (c.x + 20, c.y + 274))
                if i == elegido: dibujar_esquinas(ventana, c.inflate(6, 6))
            ventana.blit(fuente(24).render('izq/der: elegir   ENTER: empezar   ESC: volver', True, 'white'), (60, H - 40))
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
            filas += [('evo', r_) for r_ in evos] + ([('activar', None)] if i != j['activo'] else []) + [('volver', None)]
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
                if clase in ('stat', 'sinergia', 'evo', 'activar', 'volver'):
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
                    total = progreso.stat(m['nombre'], valor, m['nivel'], m['ivs'][valor], m['evs'][valor])
                    ventana.blit(fuente(24).render(progreso.NOMBRE_STAT[valor], True, 'white'), (r.x + 8, r.y + 7))
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
            return [nombres[valor] + ': ' + acc['movs'](m)[valor] + ' - ' + acc['info_movs'](m)[valor] + '.',
                    'ENTER: enseñar una MT. Las de combate van en cualquier casilla; las especiales solo en Shift o R.']
        if clase == 'item':
            clave = m['items'][valor] if valor < len(m['items']) else None
            if clave: return [tienda.ITEMS[clave]['nombre'] + ': ' + tienda.ITEMS[clave]['desc'] + '.', 'Solo cuenta mientras este pokemon pelea. ENTER: cambiar o sacar.']
            return ['Ranura vacia. ENTER: equipar un objeto de la mochila (Cinta Fuerte, Carbon, Eter...).', 'Cada pokemon lleva hasta ' + str(tienda.MAX_EQUIPADOS) + ' objetos.']
        if clase == 'evo': return ['Requisito: ' + progreso.texto_requisito(valor) + '. Conserva nivel, IV, EV, MT y objetos.']
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


    def lista_detallada(ui, titulo_, filas, pie=''):
        """Lista con scroll: cada fila tiene un nombre y abajo una linea que explica que hace. Devuelve el indice elegido, None o 'salir'."""
        ventana, W, H = ui['ventana'], ui['W'], ui['H']
        elegido, reloj, alto = 0, pygame.time.Clock(), 50
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
            titulo(ventana, titulo_, 40, 26, 48)
            for k in range(inicio, min(len(filas), inicio + visibles)):
                r = pygame.Rect(40, 100 + (k - inicio) * alto, W - 80, alto - 6)
                caja(ventana, r, 'boton_elegido' if k == elegido else 'boton', OSCURO, 2)
                nombre, desc = filas[k]
                ventana.blit(fuente(26).render(nombre, True, 'white'), (r.x + 12, r.y + 5))
                ventana.blit(fuente(20).render(desc, True, (205, 205, 205)), (r.x + 12, r.y + 26))
                if k == elegido: dibujar_esquinas(ventana, r.inflate(6, 4), margen=4, largo=10, grosor=2)
            ventana.blit(fuente(22).render(pie + '   ENTER: elegir   ESC: volver', True, 'white'), (40, H - 36))
            ui['presentar'](); reloj.tick(60)


    def mochila(ui, j, acc):
        """Lo que tenes: objetos para equipar, MT, piedras, lo que llevan puesto tus pokemon y lo que es de todo el equipo, con lo que hace cada cosa."""
        inv = j['inventario']
        filas = []
        for k_, n in inv['objetos'].items():
            if n > 0: filas.append((tienda.ITEMS[k_]['nombre'] + '  x' + str(n), tienda.ITEMS[k_]['desc']))
        for m in j['equipo'] + j.get('reserva', []):
            for k_ in m.get('items', []): filas.append((tienda.ITEMS[k_]['nombre'] + '  (lo lleva ' + m['nombre'].title() + ')', tienda.ITEMS[k_]['desc']))
        for k_ in dict.fromkeys(inv['comprados']):
            if 'permanente' in tienda.ITEMS[k_]: filas.append((tienda.ITEMS[k_]['nombre'] + '  (equipo)', tienda.ITEMS[k_]['desc']))
        for linea in tienda.activos(inv): filas.append((linea, 'activo para todo el equipo (el numero son las salas que le quedan)'))
        if not filas: filas = [('Vacia', 'Las cosas se consiguen en la tienda y de los jefes.')]
        r = lista_detallada(ui, 'Mochila', filas, 'Objetos, MT y piedras se usan desde la ficha de cada pokemon.')
        return 'salir' if r == 'salir' else None


    def reserva(ui, j, acc):
        """Los que se unieron con el equipo lleno. Se pueden traer al equipo."""
        lista = acc['reserva']()
        if not lista:
            r = preguntar(ui, 'La reserva esta vacia', ['Ok'], 'cuando se te une alguien con el equipo lleno, viene aca')
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
