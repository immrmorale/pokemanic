"""
sistema.py - Lo basico para que el juego funcione: ajustes guardados, ventana, teclado/control y animaciones de los sprites.

    opciones      cargar y guardar config.json
    pantalla      dibuja en 1000x600 y escala a la ventana
    controles     teclas configurables, control (joystick) y codigo Konami
    animaciones   AnimadorPokemon: lee las hojas de sprites del PMD

    from sistema import opciones, pantalla, controles, animaciones
"""

import json
import math
import os
import re
import xml.etree.ElementTree as ET
from types import SimpleNamespace
import pygame


# ==================== opciones ====================

def armar_opciones():
    """Ajustes del juego guardados en config.json (volumen, combate, resolucion, controles...).

        config = opciones.cargar()
        opciones.guardar(config)
    """
    RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    RESOLUCIONES = ['1000x600', '1250x750', '1500x900', '1920x1152']
    ESTILOS_EQUIPO = ['clasico', 'escenario']        # menu TAB: lista como en los juegos o tus pokemon parados en un escenario
    DEFECTO = {'volumen': 50, 'modo': 'mouse', 'resolucion': '1000x600', 'pantalla_completa': False, 'estilo_equipo': 'clasico',
               'controles': None}                    # controles: los arma controles.py la primera vez


    def cargar():
        config = dict(DEFECTO)
        if os.path.isfile(RUTA):
            try:
                with open(RUTA, encoding='utf-8') as f: config.update(json.load(f))
            except (OSError, ValueError): pass
        config['trucos'] = {}                        # los trucos del menu secreto no se guardan
        return config


    def guardar(config):
        try:
            with open(RUTA, 'w', encoding='utf-8') as f: json.dump({k: v for k, v in config.items() if k != 'trucos'}, f, ensure_ascii=False, indent=1)
        except OSError: pass

    return SimpleNamespace(**locals())


opciones = armar_opciones()


# ==================== pantalla ====================

def armar_pantalla():
    """El juego se dibuja siempre en 1000x600 y se escala a la ventana (o a pantalla completa) con franjas negras si hace falta.

        ventana = pantalla.iniciar(W, H, config)    # superficie donde se dibuja todo
        pantalla.presentar()                        # en vez de pygame.display.flip()
        pantalla.raton()                            # en vez de pygame.mouse.get_pos() (ya en coordenadas del juego)
        pantalla.a_logico(e.pos)                    # posicion de un evento del mouse en coordenadas del juego
    """
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

    return SimpleNamespace(**locals())


pantalla = armar_pantalla()


# ==================== controles ====================

def armar_controles():
    """Teclado y control (joystick) con teclas configurables: 3 perfiles de teclado y 3 de control.

        controles.iniciar(config)
        for e in controles.eventos(): ...           # en vez de pygame.event.get(): el control tambien maneja los menus
        controles.acciones(e)                       # en el juego: que acciones dispara ese evento ('basico1', 'pausa'...)
        controles.direccion()                       # (dx, dy) de movimiento (teclas, palanca izquierda o cruz)
        controles.mantiene('correr')                # si esa accion esta apretada
        controles.apuntado()                        # vector de la palanca derecha (o None)

    En los menus el control se traduce a teclas: cruz/palanca = flechas, A = ENTER, B o Start = ESC.
    El codigo Konami (arriba arriba abajo abajo izq der izq der B A) genera un evento KONAMI.
    """
    KONAMI = pygame.USEREVENT + 7                  # evento: se completo el codigo Konami
    ACCION = pygame.USEREVENT + 8                  # evento: boton del control en el juego (e.acciones)
    SECUENCIA = ['arriba', 'arriba', 'abajo', 'abajo', 'izquierda', 'derecha', 'izquierda', 'derecha', 'b', 'a']
    ZONA_MUERTA = 0.35

    ACCIONES = [('arriba', 'Mover arriba'), ('abajo', 'Mover abajo'), ('izquierda', 'Mover a la izquierda'), ('derecha', 'Mover a la derecha'),
                ('correr', 'Correr'), ('basico1', 'Ataque cuerpo a cuerpo'), ('basico2', 'Ataque a distancia'), ('especial1', 'Especial 1'),
                ('especial2', 'Especial 2'), ('asist1', 'Asistencia 1'), ('asist2', 'Asistencia 2'), ('poke1', 'Pokemon 1'), ('poke2', 'Pokemon 2'),
                ('poke3', 'Pokemon 3'), ('interactuar', 'Interactuar / comprar'), ('equipo', 'Ver equipo'), ('pausa', 'Pausa')]
    MOVIMIENTO = ('arriba', 'abajo', 'izquierda', 'derecha')
    PRESET_TECLADO = {'arriba': 'w', 'abajo': 's', 'izquierda': 'a', 'derecha': 'd', 'correr': 'left ctrl', 'basico1': 'e', 'basico2': 'q',
                      'especial1': 'left shift', 'especial2': 'r', 'asist1': 'f', 'asist2': 'g', 'poke1': '1', 'poke2': '2', 'poke3': '3',
                      'interactuar': 'e', 'equipo': 'tab', 'pausa': 'escape'}
    PRESET_CONTROL = {'arriba': 'ninguno', 'abajo': 'ninguno', 'izquierda': 'ninguno', 'derecha': 'ninguno',     # con control se camina con la palanca
                      'correr': 'LB', 'basico1': 'X', 'basico2': 'RT', 'especial1': 'RB', 'especial2': 'Y', 'asist1': 'LT', 'asist2': 'B',
                      'poke1': 'cruz izq', 'poke2': 'cruz arriba', 'poke3': 'cruz der', 'interactuar': 'A', 'equipo': 'Back', 'pausa': 'Start'}

    estado = {'config': None, 'contexto': 'menu', 'mandos': {}, 'konami': [], 'palanca_menu': (0, 0), 'repetir': 0}

    try:                                            # API estandar de SDL (Xbox, PlayStation y Switch se llaman igual)
        from pygame._sdl2 import controller as _sdl
        BOTONES = {pygame.CONTROLLER_BUTTON_A: 'A', pygame.CONTROLLER_BUTTON_B: 'B', pygame.CONTROLLER_BUTTON_X: 'X', pygame.CONTROLLER_BUTTON_Y: 'Y',
                   pygame.CONTROLLER_BUTTON_BACK: 'Back', pygame.CONTROLLER_BUTTON_START: 'Start', pygame.CONTROLLER_BUTTON_LEFTSHOULDER: 'LB',
                   pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: 'RB', pygame.CONTROLLER_BUTTON_LEFTSTICK: 'palanca izq',
                   pygame.CONTROLLER_BUTTON_RIGHTSTICK: 'palanca der', pygame.CONTROLLER_BUTTON_DPAD_UP: 'cruz arriba',
                   pygame.CONTROLLER_BUTTON_DPAD_DOWN: 'cruz abajo', pygame.CONTROLLER_BUTTON_DPAD_LEFT: 'cruz izq', pygame.CONTROLLER_BUTTON_DPAD_RIGHT: 'cruz der'}
    except Exception:
        _sdl, BOTONES = None, {}
    GATILLOS = {} if not _sdl else {pygame.CONTROLLER_AXIS_TRIGGERLEFT: 'LT', pygame.CONTROLLER_AXIS_TRIGGERRIGHT: 'RT'}
    EN_MENU = {'A': pygame.K_RETURN, 'B': pygame.K_ESCAPE, 'Start': pygame.K_ESCAPE, 'cruz arriba': pygame.K_UP, 'cruz abajo': pygame.K_DOWN,
               'cruz izq': pygame.K_LEFT, 'cruz der': pygame.K_RIGHT, 'X': pygame.K_x, 'Y': pygame.K_y, 'LB': pygame.K_PAGEUP, 'RB': pygame.K_PAGEDOWN}
    TOKEN_TECLA = {pygame.K_UP: 'arriba', pygame.K_DOWN: 'abajo', pygame.K_LEFT: 'izquierda', pygame.K_RIGHT: 'derecha', pygame.K_b: 'b', pygame.K_a: 'a'}
    TOKEN_BOTON = {'cruz arriba': 'arriba', 'cruz abajo': 'abajo', 'cruz izq': 'izquierda', 'cruz der': 'derecha', 'B': 'b', 'A': 'a'}


    # ---------- perfiles ----------

    def iniciar(config):
        """Arma los perfiles por defecto si no hay y abre los controles conectados."""
        estado['config'] = config
        if not config.get('controles'):
            config['controles'] = {'teclado': [dict(PRESET_TECLADO) for _ in range(3)], 'control': [dict(PRESET_CONTROL) for _ in range(3)],
                                   'perfil_teclado': 0, 'perfil_control': 0}
        for dispositivo, preset in (('teclado', PRESET_TECLADO), ('control', PRESET_CONTROL)):   # acciones nuevas en perfiles viejos
            for perfil in config['controles'][dispositivo]:
                for k, v in preset.items(): perfil.setdefault(k, v)
        if _sdl:
            try:
                _sdl.init()
                for i in range(_sdl.get_count()): _abrir(i)
            except Exception: pass


    def _abrir(indice):
        try:
            if _sdl.is_controller(indice):
                mando = _sdl.Controller(indice)
                estado['mandos'][mando.as_joystick().get_instance_id()] = mando
        except Exception: pass


    def perfil(dispositivo):
        c = estado['config']['controles']
        return c[dispositivo][c['perfil_' + dispositivo]]


    def restaurar(dispositivo, indice):
        estado['config']['controles'][dispositivo][indice] = dict(PRESET_TECLADO if dispositivo == 'teclado' else PRESET_CONTROL)


    def nombre_tecla(e):
        return pygame.key.name(e.key)


    def hay_control():
        return bool(estado['mandos'])


    def contexto(nuevo=None):
        """'menu' o 'juego': cambia que hace el control."""
        if nuevo: estado['contexto'] = nuevo
        return estado['contexto']


    # ---------- eventos ----------

    def _konami(token, salida):
        """Avanza el codigo Konami. Devuelve True si hay que tragarse el evento (la B y la A del final)."""
        seq = estado['konami']
        seq.append(token)
        while seq and seq != SECUENCIA[:len(seq)]: seq.pop(0)
        if seq == SECUENCIA:
            estado['konami'] = []
            salida.append(pygame.event.Event(KONAMI))
            return True
        return len(seq) >= 9 and token == 'b'


    def eventos():
        """Como pygame.event.get() pero con el control traducido (a teclas en los menus, a acciones en el juego)."""
        salida = []
        menu = estado['contexto'] == 'menu'
        for e in pygame.event.get():
            if e.type == pygame.CONTROLLERDEVICEADDED: _abrir(e.device_index); continue
            if e.type == pygame.CONTROLLERDEVICEREMOVED: estado['mandos'].pop(e.instance_id, None); continue
            if e.type == pygame.KEYDOWN and e.key in TOKEN_TECLA and _konami(TOKEN_TECLA[e.key], salida): continue
            if e.type == pygame.CONTROLLERBUTTONDOWN and e.button in BOTONES:
                boton = BOTONES[e.button]
                if boton in TOKEN_BOTON and _konami(TOKEN_BOTON[boton], salida): continue
                if menu and boton in EN_MENU: salida.append(pygame.event.Event(pygame.KEYDOWN, key=EN_MENU[boton], mod=0, unicode='')); continue
                if not menu: salida.append(pygame.event.Event(ACCION, acciones=_acciones_boton(boton)))
                continue
            if e.type == pygame.CONTROLLERAXISMOTION and e.axis in GATILLOS and not menu:
                mando = estado['mandos'].get(e.instance_id)
                antes = mando and getattr(mando, '_gatillos', {}).get(e.axis, False)
                apretado = e.value > 0.6 * 32767
                if mando is not None:
                    if not hasattr(mando, '_gatillos'): mando._gatillos = {}
                    mando._gatillos[e.axis] = apretado
                if apretado and not antes: salida.append(pygame.event.Event(ACCION, acciones=_acciones_boton(GATILLOS[e.axis])))
                continue
            salida.append(e)
        if menu and estado['mandos']:                                # palanca izquierda en los menus = flechas (con repeticion)
            dx, dy = _palanca(0)
            ahora = pygame.time.get_ticks()
            direccion = (round(dx), round(dy)) if math.hypot(dx, dy) > 0.6 else (0, 0)
            if direccion != (0, 0) and (direccion != estado['palanca_menu'] or ahora >= estado['repetir']):
                tecla = {(0, -1): pygame.K_UP, (0, 1): pygame.K_DOWN, (-1, 0): pygame.K_LEFT, (1, 0): pygame.K_RIGHT}.get(direccion)
                if tecla: salida.append(pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=0, unicode=''))
                estado['repetir'] = ahora + (350 if direccion != estado['palanca_menu'] else 130)
            estado['palanca_menu'] = direccion
        return salida


    def _acciones_boton(boton):
        return [a for a, b in perfil('control').items() if b == boton and a not in MOVIMIENTO]


    def acciones(e):
        """Acciones de juego que dispara un evento (teclado segun el perfil, o boton del control)."""
        if e.type == ACCION: return e.acciones
        if e.type == pygame.KEYDOWN:
            tecla = nombre_tecla(e)
            return [a for a, t in perfil('teclado').items() if t == tecla and a not in MOVIMIENTO]
        return []


    # ---------- estado (lo que esta apretado) ----------

    def _palanca(cual):
        """Palanca izquierda (0) o derecha (1) del primer control, de -1 a 1."""
        for mando in estado['mandos'].values():
            try:
                ejes = (pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY) if cual == 0 else (pygame.CONTROLLER_AXIS_RIGHTX, pygame.CONTROLLER_AXIS_RIGHTY)
                x, y = mando.get_axis(ejes[0]) / 32767, mando.get_axis(ejes[1]) / 32767
                return (x, y) if math.hypot(x, y) > ZONA_MUERTA else (0.0, 0.0)
            except Exception: pass
        return (0.0, 0.0)


    def _boton(nombre):
        for mando in estado['mandos'].values():
            try:
                if nombre in ('LT', 'RT'):
                    eje = pygame.CONTROLLER_AXIS_TRIGGERLEFT if nombre == 'LT' else pygame.CONTROLLER_AXIS_TRIGGERRIGHT
                    if mando.get_axis(eje) > 0.6 * 32767: return True
                else:
                    boton = next((b for b, n in BOTONES.items() if n == nombre), None)
                    if boton is not None and mando.get_button(boton): return True
            except Exception: pass
        return False


    def mantiene(accion):
        teclas = pygame.key.get_pressed()
        tecla = perfil('teclado').get(accion)
        try:
            if tecla and teclas[pygame.key.key_code(tecla)]: return True
        except (ValueError, IndexError): pass
        return bool(estado['mandos']) and _boton(perfil('control').get(accion, ''))


    def direccion():
        """Movimiento: teclas del perfil + palanca izquierda + cruz del control."""
        dx = mantiene('derecha') - mantiene('izquierda')
        dy = mantiene('abajo') - mantiene('arriba')
        if not (dx or dy):
            px, py = _palanca(0)
            if px or py:                                          # la palanca se pasa a 8 direcciones como el teclado
                ang = round(math.atan2(py, px) / (math.pi / 4)) * math.pi / 4
                dx, dy = round(math.cos(ang)), round(math.sin(ang))
        return dx, dy


    def apuntado():
        """Hacia donde apunta la palanca derecha (vector normalizado) o None."""
        x, y = _palanca(1)
        n = math.hypot(x, y)
        return (x / n, y / n) if n else None


    def esperar_entrada(dispositivo, presentar, dibujar):
        """Para reasignar: espera una tecla (o un boton del control). ESC cancela. Devuelve el nombre o None."""
        reloj = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return None
                if dispositivo == 'teclado' and e.type == pygame.KEYDOWN:
                    return None if e.key == pygame.K_ESCAPE else nombre_tecla(e)
                if dispositivo == 'control':
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None
                    if e.type == pygame.CONTROLLERBUTTONDOWN and e.button in BOTONES: return BOTONES[e.button]
                    if e.type == pygame.CONTROLLERAXISMOTION and e.axis in GATILLOS and e.value > 0.6 * 32767: return GATILLOS[e.axis]
            dibujar(); presentar(); reloj.tick(60)

    return SimpleNamespace(**locals())


controles = armar_controles()


# ==================== animaciones ====================

def armar_animaciones():
    """Animaciones de los pokemon con las hojas de sprites del PMD (AnimData.xml) o el formato viejo de carpetas."""
    direcciones = ['sur', 'sureste', 'este', 'noreste', 'norte', 'noroeste', 'oeste', 'suroeste']
    direccion_vector = {
        'sur': (0, 1),
        'suroeste': (-1, 1),
        'oeste': (-1, 0),
        'noroeste': (-1, -1),
        'norte': (0, -1),
        'noreste': (1, -1),
        'este': (1, 0),
        'sureste': (1, 1),
    }


    def _normalizar_nombre(nombre):
        return str(nombre).strip().lower().replace(' ', '_').replace('-', '_')


    _CARPETAS = {}                                   # nombre -> carpeta (o None): se busca en el disco una sola vez por nombre


    def _buscar_carpeta(nombre):
        objetivo = _normalizar_nombre(nombre)
        if objetivo in _CARPETAS: return _CARPETAS[objetivo]
        base = os.path.join('assets', 'sprites', 'pokemones')
        encontrada = None
        for ruta in (os.path.join(base, 'sprite_' + objetivo), os.path.join(base, objetivo)):
            if os.path.isdir(ruta): encontrada = ruta; break
        if not encontrada and os.path.isdir(base):
            for entrada in os.listdir(base):
                ruta = os.path.join(base, entrada)
                if _normalizar_nombre(entrada) in ('sprite_' + objetivo, objetivo) and os.path.isdir(ruta): encontrada = ruta; break
        _CARPETAS[objetivo] = encontrada
        return encontrada


    _CACHE_CARGA = {}
    _CACHE_ESCALADO = {}


    def tiene_sprites(nombre):
        return _buscar_carpeta(_normalizar_nombre(nombre)) is not None


    def _numero_direccion(nombre):
        encontrados = re.findall(r'(\d+)', nombre)
        return int(encontrados[-1]) if encontrados else None


    # Animaciones especiales de los sprites (relevadas de los AnimData.xml de los 91 pokemon).
    # Todos tienen Walk, Attack, Sleep, Hurt, Idle, Swing, Double, Hop, Charge y Rotate; el resto depende de cada uno
    # (Shock: pikachu, raichu, pichu, electrike, manectric; Kick: blaziken, hawlucha, machop...; Bite: glalie; Sing: pichu; etc).
    # Se busca por pedazo del nombre del movimiento y se usa la primera que el pokemon tenga.
    ANIM_MOVIMIENTO = (
        ('puño', ('punch', 'jab', 'strike')), ('golpe_karate', ('chop', 'punch', 'strike')), ('demolicion', ('punch', 'slam', 'strike')),
        ('patada', ('kick', 'strike')), ('mordisco', ('bite', 'attack')), ('colmillo', ('bite', 'attack')),
        ('garra', ('multiscratch', 'multistrike', 'strike')), ('tajo', ('multiscratch', 'chop', 'strike')), ('hoja_afilada', ('swing', 'shoot')),
        ('picotazo', ('jab', 'quickstrike', 'strike')), ('ataque_ala', ('flaparound', 'hover', 'swing')), ('vuelo', ('hover', 'flaparound', 'leapforth')),
        ('ataque_rapido', ('quickstrike', 'strike')), ('velocidad_extrema', ('quickstrike', 'strike')), ('acua_jet', ('quickstrike', 'strike')),
        ('cola', ('tailwhip', 'swing')), ('latigo', ('tailwhip', 'swing')), ('cabeza', ('head', 'slam', 'strike')),
        ('golpe_cuerpo', ('slam', 'tumble', 'strike')), ('placaje', ('slam', 'strike')), ('rodar', ('ricochet', 'tumble', 'rotate')),
        ('terremoto', ('rumble', 'slam', 'rearup')), ('excavar', ('sink', 'rumble')), ('romperrocas', ('slam', 'punch')),
        ('lanzarrocas', ('rearup', 'shoot')), ('pedrada', ('shoot', 'rearup')), ('avalancha', ('rearup', 'rumble')),
        ('surf', ('ricochet', 'rumble', 'swing')), ('hidrobomba', ('spattack', 'shoot')), ('ventisca', ('spattack', 'emit', 'shoot')),
        ('hiper_rayo', ('spattack', 'emit', 'shoot')), ('rayo_solar', ('spattack', 'charge')), ('enfado', ('rearup', 'rumble')),
        ('psiquico', ('emit', 'spattack', 'charge')), ('premonicion', ('emit', 'charge')), ('confusion', ('emit', 'charge')),
        ('lenguetazo', ('eat', 'attack')), ('infortunio', ('twirl', 'emit')), ('finta', ('quickstrike', 'twirl')),
        ('danza', ('dance', 'twirl', 'rotate')), ('agilidad', ('twirl', 'hop')), ('corpulencia', ('pose', 'rearup', 'deepbreath')),
        ('paz_mental', ('deepbreath', 'nod', 'charge')), ('defensa_ferrea', ('withdraw', 'pose')), ('pulimento', ('rotate', 'shake')),
        ('descanso', ('laying', 'sleep')), ('respiro', ('deepbreath', 'pose')), ('recuperacion', ('deepbreath', 'pose')), ('sintesis', ('lookup', 'pose')),
        ('proteccion', ('withdraw', 'pose')), ('deteccion', ('lookup', 'pose')), ('ataque_arena', ('swing', 'rumble')),
    )
    # Si el nombre no dice nada: por tipo y forma del movimiento.
    ANIM_TIPO = {
        'electrico': {'proyectil': ('shock', 'emit', 'shoot'), 'cuerpo': ('shock', 'strike'), 'area': ('shock', 'emit', 'rotate')},
        'lucha': {'cuerpo': ('punch', 'kick', 'chop', 'strike'), 'proyectil': ('punch', 'spattack', 'shoot')},
        'fantasma': {'proyectil': ('twirl', 'spattack', 'shoot'), 'cuerpo': ('twirl', 'strike')},
        'psiquico': {'proyectil': ('emit', 'spattack', 'shoot'), 'area': ('emit', 'rotate')},
        'volador': {'proyectil': ('hover', 'flaparound', 'shoot'), 'cuerpo': ('quickstrike', 'jab', 'strike')},
        'tierra': {'proyectil': ('rumble', 'shoot'), 'area': ('rumble', 'slam', 'swing')},
        'roca': {'cuerpo': ('slam', 'strike'), 'proyectil': ('rearup', 'shoot')},
        'dragon': {'proyectil': ('spattack', 'rearup', 'shoot'), 'cuerpo': ('strike', 'slam')},
        'hielo': {'proyectil': ('spattack', 'shoot'), 'area': ('twirl', 'rotate')},
        'acero': {'cuerpo': ('slam', 'strike'), 'proyectil': ('spattack', 'shoot')},
        'siniestro': {'cuerpo': ('bite', 'multiscratch', 'strike'), 'proyectil': ('multiscratch', 'shoot')},
        'agua': {'area': ('ricochet', 'rumble', 'swing')},
    }


    class AnimacionHoja:
        def __init__(self, nombre, indice, ancho, alto, duraciones, rush=None, hit=None, retorno=None, copia=None):
            self.nombre = nombre.lower()
            self.indice = indice
            self.ancho = ancho
            self.alto = alto
            self.duraciones = duraciones or [1]
            self.rush = rush
            self.hit = hit
            self.retorno = retorno
            self.copia = copia


    class AnimadorPokemon:
        FACTOR_VELOCIDAD = 2.0
        FACTOR_IDLE = 1.6                # idle y caminar usan las duraciones del AnimData.xml (en frames a 60 fps) por este factor
        FACTOR_CAMINAR = 1.4
        VELOCIDAD_REFERENCIA = 5.0
        RITMO_XML = ('sleep', 'eventsleep', 'wake', 'hurt', 'nod', 'pose', 'sit', 'laying', 'eat', 'lookup', 'deepbreath', 'faint', 'cringe', 'float', 'hover')   # estas van con las duraciones del AnimData.xml
        SUAVIZADO = False
        nombres_ataque = ('attack', 'strike', 'stricke', 'quickstrike', 'quick_strike', 'kick', 'punch', 'slash', 'body', 'melee', 'hit')
        nombres_forma = {
            'proyectil': ('shoot', 'charge'),
            'embestida': ('charge', 'strike', 'quickstrike', 'tackle'),
            'area': ('swing', 'double', 'rotate'),
            'buff': ('pose', 'hop', 'charge'),
            'curar': ('pose', 'hop', 'dance'),
        }

        def __init__(self, pokemon, rect, tamaño=40):
            self.pokemon = _normalizar_nombre(pokemon)
            self.rect = rect
            self.tamaño = max(1, int(tamaño or 40))
            self.carpeta = _buscar_carpeta(self.pokemon)
            self.animaciones = {}
            self.sprites = {}
            self.offsets = {}
            self.sombras = {}
            self.usando_hojas = False
            self.animacion_actual = 'idle'
            self.direccion = 0
            self.indice_frame = 0
            self.acumulado = 0.0
            self.terminada = False
            self.repetir = True
            self.ritmo = 1.0
            self.escala = 1.0
            self.altura_base = 0
            self._cargar_con_cache()
            if self.usando_hojas and self.altura_base:
                self.escala = self.tamaño / float(self.altura_base)
            self.cache = _CACHE_ESCALADO.setdefault((self.pokemon, self.tamaño), {})

        def _cargar_con_cache(self):
            c = _CACHE_CARGA.get(self.pokemon)
            if c is None:
                self._cargar()
                _CACHE_CARGA[self.pokemon] = (self.animaciones, self.sprites, self.offsets, self.sombras, self.usando_hojas, self.altura_base)
            else:
                self.animaciones, self.sprites, self.offsets, self.sombras, self.usando_hojas, self.altura_base = c

        def _cargar(self):
            if not self.carpeta:
                return
            xml = os.path.join(self.carpeta, 'AnimData.xml')
            if os.path.isfile(xml):
                self._cargar_hojas(xml)
            if not self.usando_hojas:
                self._cargar_formato_antiguo()

        def _cargar_hojas(self, xml):
            try:
                raiz = ET.parse(xml).getroot()
            except Exception:
                return
            contenedor = raiz.find('Anims')
            if contenedor is None:
                return
            for nodo in contenedor.findall('Anim'):
                nombre = nodo.findtext('Name')
                if not nombre:
                    continue
                copia = nodo.findtext('CopyOf')
                indice = nodo.findtext('Index')
                ancho = nodo.findtext('FrameWidth')
                alto = nodo.findtext('FrameHeight')
                if ancho is None or alto is None:
                    self.animaciones[nombre.lower()] = AnimacionHoja(nombre, None, None, None, [], copia=copia)
                    continue
                duraciones = []
                dur_node = nodo.find('Durations')
                if dur_node is not None:
                    textos = [d.text for d in dur_node.findall('Duration')] or (dur_node.text or '').replace(',', ' ').split()   # <Duration> sueltos (formato del PMD)
                    for valor in textos:
                        try:
                            duraciones.append(int(valor))
                        except (TypeError, ValueError):
                            pass
                self.animaciones[nombre.lower()] = AnimacionHoja(
                    nombre,
                    int(indice) if indice else 0,
                    int(ancho),
                    int(alto),
                    duraciones,
                    int(nodo.findtext('RushFrame')) if nodo.findtext('RushFrame') else None,
                    int(nodo.findtext('HitFrame')) if nodo.findtext('HitFrame') else None,
                    int(nodo.findtext('ReturnFrame')) if nodo.findtext('ReturnFrame') else None,
                    copia,
                )
            self._resolver_copias()
            cargadas = 0
            for anim in self.animaciones.values():
                if anim.copia or anim.indice is None:
                    continue
                if self._cargar_hoja(anim):
                    cargadas += 1
            self.usando_hojas = cargadas > 0
            if self.usando_hojas:
                for anim in self.animaciones.values():
                    if anim.copia and anim.nombre not in self.sprites and anim.copia.lower() in self.sprites:
                        base = anim.copia.lower()
                        self.sprites[anim.nombre] = self.sprites[base]
                        if base in self.offsets: self.offsets[anim.nombre] = self.offsets[base]
                        if base in self.sombras: self.sombras[anim.nombre] = self.sombras[base]
                self.escala = self._calcular_escala_base()

        def _resolver_copias(self):
            for anim in self.animaciones.values():
                if not anim.copia:
                    continue
                base = self.animaciones.get(anim.copia.lower())
                if base:
                    anim.indice = base.indice
                    anim.ancho = base.ancho
                    anim.alto = base.alto
                    anim.duraciones = list(base.duraciones)
                    anim.rush = base.rush
                    anim.hit = base.hit
                    anim.retorno = base.retorno

        def _cargar_hoja(self, anim):
            prefijo = anim.nombre.title().replace('_', '')
            candidatos = [
                prefijo,
                anim.nombre,
                anim.nombre.capitalize(),
            ]
            rutas = []
            for nombre in candidatos:
                ruta = os.path.join(self.carpeta, nombre + '-Anim.png')
                if os.path.isfile(ruta):
                    rutas.append((ruta, nombre))
            if not rutas and os.path.isdir(self.carpeta):
                objetivo = (anim.nombre + '-anim.png').lower()
                for archivo in os.listdir(self.carpeta):
                    if archivo.lower() == objetivo:
                        rutas.append((os.path.join(self.carpeta, archivo), os.path.splitext(archivo)[0][:-5]))
                        break
            for ruta, nombre in rutas:
                try:
                    hoja = pygame.image.load(ruta).convert_alpha()
                except Exception:
                    continue
                columnas = max(1, hoja.get_width() // anim.ancho)
                filas = max(1, hoja.get_height() // anim.alto)
                frames = []
                for direccion in range(min(8, filas)):
                    fila = []
                    for frame in range(columnas):
                        x = frame * anim.ancho
                        y = direccion * anim.alto
                        fila.append(hoja.subsurface((x, y, anim.ancho, anim.alto)).copy())
                    frames.append(fila)
                self.sprites[anim.nombre] = frames
                self._cargar_metadatos(anim, nombre)
                return True
            return False

        def _cargar_metadatos(self, anim, prefijo):
            for sufijo, destino in (('-Offsets.png', self.offsets), ('-Shadow.png', self.sombras)):
                ruta = os.path.join(self.carpeta, prefijo + sufijo)
                if os.path.isfile(ruta):
                    try:
                        destino[anim.nombre] = pygame.image.load(ruta).convert_alpha()
                    except Exception:
                        pass

        def _cargar_formato_antiguo(self):
            if not self.carpeta:
                return
            grupos = {}
            for nombre in ('idle', 'walk', 'strike', 'stricke', 'attack', 'kick', 'punch', 'slash', 'body', 'melee', 'hit'):
                ruta = os.path.join(self.carpeta, nombre)
                if not os.path.isdir(ruta):
                    continue
                archivos = []
                for archivo in os.listdir(ruta):
                    if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                        numero = _numero_direccion(archivo)
                        archivos.append((numero if numero is not None else 999999, archivo))
                archivos.sort()
                if archivos:
                    grupos[nombre] = [pygame.image.load(os.path.join(ruta, archivo)).convert_alpha() for _, archivo in archivos]
            if grupos:
                self.sprites = grupos
                self.usando_hojas = False

        def _calcular_escala_base(self):
            candidatos = []
            for nombre in ('idle', 'walk'):
                frames = self.sprites.get(nombre)
                if not frames:
                    continue
                for fila in frames:
                    for imagen in fila:
                        bbox = imagen.get_bounding_rect()
                        if bbox.height > 0:
                            candidatos.append(bbox.height)
            if not candidatos:
                return 1.0
            altura = max(candidatos)
            self.altura_base = altura
            return self.tamaño / float(altura)

        def _buscar_animacion(self, nombre):
            nombre = _normalizar_nombre(nombre)
            if nombre in self.sprites:
                return nombre
            equivalencias = {
                'idle': ('idle',),
                'walk': ('walk', 'idle'),
                'attack': self.nombres_ataque,
            }
            for candidato in equivalencias.get(nombre, (nombre,)):
                if candidato in self.sprites:
                    return candidato
            return None

        def buscar_ataque(self):
            for nombre in self.nombres_ataque:
                if nombre in self.sprites:
                    return nombre
            return None

        def buscar_para(self, forma):
            for nombre in self.nombres_forma.get(forma, ()):
                if nombre in self.sprites:
                    return nombre
            return self.buscar_ataque()

        def buscar_movimiento(self, movimiento, tipo=None, forma=None):
            # primero por el nombre del movimiento (puño -> Punch), despues por tipo y forma (electrico -> Shock), si no la de la forma
            nombre = _normalizar_nombre(movimiento or '')
            for clave, anims in ANIM_MOVIMIENTO:
                if clave in nombre:
                    for anim in anims:
                        if anim in self.sprites: return anim
            for anim in ANIM_TIPO.get(tipo, {}).get(forma, ()):
                if anim in self.sprites: return anim
            return self.buscar_para(forma)

        def disponibles(self):
            return sorted(self.sprites)

        def cambiar(self, animacion, direccion=0, repetir=True):
            encontrada = self._buscar_animacion(animacion)
            if encontrada is None:
                return False
            if self.animacion_actual != encontrada:
                self.animacion_actual = encontrada
                self.direccion = max(0, min(7, direccion))
                self.indice_frame = 0
                self.acumulado = 0.0
                self.terminada = False
            elif self.direccion != direccion:                # solo gira: sigue en el mismo frame (no reinicia la animacion)
                self.direccion = max(0, min(7, direccion))
                self.indice_frame = min(self.indice_frame, max(0, len(self._frames_actuales()) - 1))
            else:
                self.terminada = False if repetir else self.terminada
            self.repetir = repetir
            return True

        def actualizar(self):
            frames = self._frames_actuales()
            if not frames:
                if not self.repetir:
                    self.terminada = True
                return
            duracion = self._duracion_actual()
            self.acumulado += 1.0
            if self.acumulado < duracion:
                return
            self.acumulado = 0.0
            self.indice_frame += 1
            if self.indice_frame >= len(frames):
                if self.repetir:
                    self.indice_frame = 0
                else:
                    self.indice_frame = len(frames) - 1
                    self.terminada = True

        def _frames_actuales(self):
            if self.usando_hojas:
                anim = self.animaciones.get(self.animacion_actual)
                if not anim:
                    return []
                return self.sprites.get(anim.nombre, [[] for _ in range(8)])[self.direccion]
            frames = self.sprites.get(self.animacion_actual, [])
            if frames and isinstance(frames[0], list):
                return frames[min(self.direccion, len(frames) - 1)]
            return frames

        def _factor_actual(self):
            ritmo = max(0.3, self.ritmo)
            if self.animacion_actual == 'idle':
                return self.FACTOR_IDLE
            if self.animacion_actual == 'walk':
                return self.FACTOR_CAMINAR / ritmo
            return self.FACTOR_VELOCIDAD / ritmo

        def _duracion_actual(self):
            factor = self._factor_actual()
            if self.usando_hojas:
                anim = self.animaciones.get(self.animacion_actual)
                if not anim or not anim.duraciones:
                    return 1
                if self.animacion_actual in self.RITMO_XML: factor = 1.0      # dormir, despertar, asentir...: ritmo del juego original
                elif self.animacion_actual not in ('idle', 'walk'):           # los ataques mantienen su ritmo rapido
                    return max(1, math.ceil(factor))
                duracion = anim.duraciones[min(self.indice_frame, len(anim.duraciones) - 1)]
                return max(1, math.ceil(duracion * factor))
            return max(1, round(6 * factor))

        def esta_terminada(self):
            return self.terminada

        def _obtener_offset(self, imagen, animacion, direccion, frame):
            hoja = self.offsets.get(animacion)
            if hoja is None:
                return imagen.get_width() / 2, imagen.get_height() / 2
            color = None
            mejor = None
            x0 = frame * imagen.get_width()
            y0 = direccion * imagen.get_height()
            ancho = imagen.get_width()
            alto = imagen.get_height()
            for y in range(alto):
                for x in range(ancho):
                    r, g, b, a = hoja.get_at((x0 + x, y0 + y))
                    if a and g > 140 and g > r * 1.35 and g > b * 1.2:
                        mejor = (x, y)
                        break
                if mejor:
                    break
            return mejor if mejor else (ancho / 2, alto / 2)

        def _escalar(self, imagen, ancho, alto):
            if self.SUAVIZADO:
                return pygame.transform.smoothscale(imagen, (ancho, alto))
            return pygame.transform.scale(imagen, (ancho, alto))

        def dibujar(self, ventana):
            frames = self._frames_actuales()
            if not frames or self.indice_frame >= len(frames):
                return False
            clave = (self.animacion_actual, self.direccion, self.indice_frame)
            if clave not in self.cache:
                original = frames[self.indice_frame]
                if self.usando_hojas:
                    escala = self.escala
                    imagen = self._escalar(original, max(1, round(original.get_width() * escala)), max(1, round(original.get_height() * escala)))
                    ox, oy = self._obtener_offset(original, self.animacion_actual, self.direccion, self.indice_frame)
                    self.cache[clave] = (imagen, ox * escala, oy * escala)
                else:
                    bbox = original.get_bounding_rect()
                    escala = self.tamaño / bbox.height if bbox.height > 0 else 1.0
                    imagen = self._escalar(original, max(1, round(original.get_width() * escala)), max(1, round(original.get_height() * escala)))
                    self.cache[clave] = (imagen, imagen.get_width() / 2, imagen.get_height() / 2)
            imagen, ox, oy = self.cache[clave]
            ventana.blit(imagen, (round(self.rect.centerx - ox), round(self.rect.centery - oy)))
            return True


    def cargar_retrato(nombre):
        carpeta = _buscar_carpeta(_normalizar_nombre(nombre))
        if not carpeta:
            return None
        lugares = [carpeta] + [os.path.join(carpeta, sub) for sub in ('portrait', 'portraits', 'retrato', 'retratos')]
        for lugar in lugares:
            if not os.path.isdir(lugar):
                continue
            archivos = {a.lower(): a for a in os.listdir(lugar)}
            for base in ('normal', 'portrait', 'retrato', 'face', 'cara'):
                for ext in ('.png', '.jpg', '.jpeg'):
                    if base + ext in archivos:
                        try:
                            return pygame.image.load(os.path.join(lugar, archivos[base + ext])).convert_alpha()
                        except Exception:
                            pass
        return None

    return SimpleNamespace(**locals())


animaciones = armar_animaciones()
