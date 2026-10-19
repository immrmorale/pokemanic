"""
controles.py - Teclado y control (joystick) con teclas configurables: 3 perfiles de teclado y 3 de control.

    controles.iniciar(config)
    for e in controles.eventos(): ...           # en vez de pygame.event.get(): el control tambien maneja los menus
    controles.acciones(e)                       # en el juego: que acciones dispara ese evento ('basico1', 'pausa'...)
    controles.direccion()                       # (dx, dy) de movimiento (teclas, palanca izquierda o cruz)
    controles.mantiene('correr')                # si esa accion esta apretada
    controles.apuntado()                        # vector de la palanca derecha (o None)

En los menus el control se traduce a teclas: cruz/palanca = flechas, A = ENTER, B o Start = ESC.
El codigo Konami (arriba arriba abajo abajo izq der izq der B A) genera un evento KONAMI.
"""

import math
import pygame

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
