"""
entorno.py - Lo que pasa en la sala mientras jugas: terrenos que reaccionan a los ataques, objetos que se rompen,
maquinas que ayudan a ciertos tipos y el clima.

    ent = entorno.crear(sala)
    entorno.actualizar(ent, contexto, ahora)          # cada frame (contexto: jugador, enemigos y como dañarlos)
    entorno.reaccionar(ent, x, y, radio, tipo, ahora)  # un ataque de ese tipo toco esa zona
    entorno.dibujar(ent, ventana, cx, cy, ahora)      # piso, terrenos y objetos
    entorno.dibujar_clima(ent, ventana, ahora)        # lluvia, niebla, etc. por encima de todo

Los dibujos son formas basicas con el nombre de cada cosa hasta que lleguen los sprites.
"""

import math
import os
import random
import pygame
import mundos
import generacion
from pokemones import normalizar_tipo
from animaciones import direccion_vector, AnimadorPokemon, tiene_sprites

TICK = 500                    # ms entre cada daño de terreno
DAÑO_CHOQUE = 8               # daño por tick si estas en agua electrificada
DURACION_ELECTRICO = 3000
DURACION_FUEGO = (2200, 3400)
PROB_MONEDAS = 0.35           # chance de que un objeto roto suelte monedas
EXPLOSION = {'radio': 120, 'daño': 45}
EMPUJAN = {'lucha': 11.0, 'psiquico': 14.0}    # tipos que empujan objetos al pegarles (fuerza)
FUERZA_EMBESTIDA = 9.0
CONDUCEN = ('agua', 'charco', 'cable', 'cascada')
INMUNES_CHOQUE = ('electrico', 'tierra', 'volador')

# lo que le pasa a un terreno cuando lo toca un ataque: (terreno, tipo del ataque) -> accion
# 'convertir' cambia el terreno (con probabilidad opcional), 'electrificar' electrifica el agua conectada,
# 'encender'/'apagar' fuego, 'invertir' da vuelta una cinta, 'pulso' descarga un generador, 'cortocircuito' lo hace explotar
REACCIONES = {
    ('agua', 'hielo'): ('convertir', 'hielo'), ('agua', 'electrico'): ('electrificar',), ('agua', 'veneno'): ('convertir', 'toxico'),
    ('charco', 'hielo'): ('convertir', 'hielo'), ('charco', 'electrico'): ('electrificar',), ('charco', 'fuego'): ('convertir', 'suelo'),
    ('charco', 'veneno'): ('convertir', 'toxico'),
    ('hielo', 'fuego'): ('convertir', 'agua'), ('nieve', 'fuego'): ('convertir', 'charco'),
    ('hierba', 'fuego'): ('encender',), ('aceite', 'fuego'): ('encender',),
    ('fuego', 'agua'): ('apagar',), ('fuego', 'hielo'): ('apagar',),
    ('arena', 'agua'): ('convertir', 'lodo'), ('lodo', 'fuego'): ('convertir', 'arena'),
    ('lava', 'agua'): ('convertir', 'roca_volcanica'), ('lava', 'hielo'): ('convertir', 'roca_volcanica'),
    ('toxico', 'agua'): ('convertir', 'charco'), ('sombra', 'fuego'): ('convertir', 'suelo'),
    ('suelo', 'planta'): ('convertir', 'hierba', 0.35), ('ceniza', 'planta'): ('convertir', 'hierba', 0.5),
    ('suelo', 'siniestro'): ('convertir', 'sombra', 0.25),
    ('cable', 'tierra'): ('convertir', 'suelo'), ('cable', 'agua'): ('electrificar',), ('cinta', 'electrico'): ('invertir',),
    ('cascada', 'hielo'): ('convertir', 'cascada_helada'), ('cascada_helada', 'fuego'): ('convertir', 'cascada'),
    ('cascada', 'electrico'): ('electrificar',),
    ('brasero', 'agua'): ('convertir', 'brasero_apagado'), ('brasero_apagado', 'fuego'): ('convertir', 'brasero'),
    ('fogata', 'agua'): ('convertir', 'fogata_apagada'), ('fogata', 'hielo'): ('convertir', 'fogata_apagada'), ('fogata_apagada', 'fuego'): ('convertir', 'fogata'),
    ('forja', 'agua'): ('convertir', 'forja_apagada'), ('forja_apagada', 'fuego'): ('convertir', 'forja'),
    ('horno', 'agua'): ('convertir', 'horno_apagado'), ('horno', 'hielo'): ('convertir', 'horno_apagado'),
    ('horno_apagado', 'fuego'): ('convertir', 'horno'),
    ('generador', 'electrico'): ('pulso',), ('generador', 'agua'): ('cortocircuito',), ('generador_roto', 'electrico'): ('convertir', 'generador'),
}

# que le hace cada terreno a quien lo pisa: 'todos' vale para los tipos que no aparecen
# velocidad/daño/enfriamiento/defensa/regen son multiplicadores, tick es daño cada TICK ms
PISADAS = {
    'agua': {'agua': {'velocidad': 1.3}},
    'charco': {'agua': {'velocidad': 1.15}},
    'hielo': {'todos': {'resbala': True}, 'hielo': {'velocidad': 1.7, 'sprint_gratis': True}, 'volador': {}},
    'nieve': {'todos': {'velocidad': 0.7}, 'hielo': {'velocidad': 1.25}, 'volador': {}, 'normal': {}},
    'hierba': {'planta': {'oculto': True, 'velocidad': 1.2}, 'bicho': {'oculto': True, 'velocidad': 1.2}},
    'fuego': {'todos': {'tick': 6}, 'fuego': {'daño': 1.2}, 'dragon': {}, 'volador': {'tick': 3}},
    'arena': {'todos': {'velocidad': 0.8}, 'tierra': {'velocidad': 1.15}, 'roca': {}, 'acero': {}, 'volador': {}, 'normal': {}},
    'lodo': {'todos': {'velocidad': 0.6}, 'tierra': {'velocidad': 1.2}, 'agua': {'velocidad': 1.05}, 'volador': {}, 'normal': {}},
    'lava': {'fuego': {'daño': 1.35, 'velocidad': 1.1}, 'dragon': {'daño': 1.15}, 'volador': {'tick': 2}},
    'toxico': {'todos': {'tick': 4}, 'veneno': {'daño': 1.3, 'velocidad': 1.15}, 'acero': {}, 'volador': {}},
    'sombra': {'siniestro': {'oculto': True, 'daño': 1.25}, 'fantasma': {'oculto': True, 'velocidad': 1.15}},
    'aceite': {'todos': {'resbala': True}, 'acero': {}, 'volador': {}},
    'cable': {'todos': {'tick': 5}, 'electrico': {'regen': 3.0, 'enfriamiento': 0.8}, 'tierra': {}, 'volador': {}},
    'corriente': {'todos': {'velocidad': 0.9}, 'volador': {'velocidad': 1.5, 'sprint_gratis': True}},
    'roca_volcanica': {'fuego': {'regen': 1.5}, 'roca': {'defensa': 0.9}},
    'ceniza': {'fuego': {'regen': 1.5}},
}
for _lado, _v in {'n': (0, -2.2), 's': (0, 2.2), 'e': (2.2, 0), 'o': (-2.2, 0)}.items():   # cintas: te llevan (acero pesa mas, volador ni las toca)
    PISADAS['cinta_' + _lado] = {'todos': {'empuje': _v}, 'acero': {'empuje': (_v[0] * 0.4, _v[1] * 0.4)}, 'volador': {}}

# maquinas: (radio en casillas, {tipo: efectos}) mientras estes cerca
AURAS = {
    'cascada': (2.2, {'agua': {'daño': 1.3, 'regen': 3.0, 'enfriamiento': 0.85}}),
    'cascada_helada': (2.2, {'hielo': {'daño': 1.3, 'regen': 2.0, 'enfriamiento': 0.85}}),
    'brasero': (1.8, {'fuego': {'daño': 1.3, 'enfriamiento': 0.9}}),
    'fogata': (2.0, {'fuego': {'daño': 1.3, 'regen': 2.0}, 'normal': {'regen': 1.5}}),
    'forja': (2.2, {'fuego': {'daño': 1.3, 'enfriamiento': 0.9}, 'acero': {'defensa': 0.8, 'daño': 1.15}}),
    'horno': (2.4, {'fuego': {'daño': 1.35, 'regen': 2.0}, 'acero': {'defensa': 0.85}}),
    'generador': (2.2, {'electrico': {'enfriamiento': 0.75, 'regen': 3.0}}),
    'altar': (2.0, {'psiquico': {'enfriamiento': 0.8, 'daño': 1.15}, 'fantasma': {'daño': 1.2}, 'hada': {'enfriamiento': 0.8}}),
    'cristal_dragonico': (2.4, {'dragon': {'daño': 1.3, 'velocidad': 1.1}}),
    'iman': (2.0, {'acero': {'defensa': 0.75}, 'electrico': {'regen': 1.5}}),
    'monolito': (2.0, {'roca': {'defensa': 0.75, 'daño': 1.15}, 'tierra': {'defensa': 0.85}}),
}

# cuanto daño le hace cada tipo a cada material (lo que no aparece es x1)
MATERIALES = {
    'madera': {'fuego': 3.0, 'lucha': 2.0, 'roca': 1.5, 'planta': 0.5},
    'piedra': {'lucha': 3.0, 'roca': 2.0, 'tierra': 2.0, 'acero': 2.0, 'fuego': 0.3, 'electrico': 0.3},
    'metal': {'fuego': 2.0, 'tierra': 2.0, 'lucha': 1.5, 'acero': 0.5, 'electrico': 0.5},
    'basura': {'fuego': 3.0, 'veneno': 0.2},
    'vidrio': {'roca': 3.0, 'lucha': 2.0, 'acero': 2.0, 'electrico': 2.0, 'psiquico': 1.5},
    'hielo': {'fuego': 4.0, 'lucha': 2.0, 'roca': 2.0, 'acero': 2.0, 'hielo': 0.0},
    'planta': {'fuego': 4.0, 'volador': 2.0, 'bicho': 2.0, 'hielo': 2.0, 'agua': 0.5, 'planta': 0.0},
    'tela': {'fuego': 4.0, 'volador': 2.0, 'bicho': 2.0},
    'ceramica': {'lucha': 2.0, 'roca': 2.0, 'tierra': 2.0},
    'hueso': {'lucha': 2.0, 'tierra': 2.0, 'roca': 1.5, 'fuego': 0.5},
}

# climas: multiplican el daño de cada tipo, cambian velocidades y algunos lastiman (chip) a los que no son inmunes
# el clima de la sala dura toda la sala (sin chip); el que traen los movimientos dura DURACION_CLIMA y si lastima
CLIMAS = {
    'despejado': {'nombre': 'Despejado', 'mult': {}},
    'nublado': {'nombre': 'Nublado', 'mult': {}},
    'nieve': {'nombre': 'Nevada', 'mult': {'hielo': 1.2}, 'velocidad': {'hielo': 1.15}},
    'lluvia': {'nombre': 'Lluvia', 'mult': {'agua': 1.4, 'fuego': 0.6}, 'velocidad': {'agua': 1.15}},
    'sol': {'nombre': 'Dia soleado', 'mult': {'fuego': 1.4, 'agua': 0.6}, 'velocidad': {'planta': 1.2}},
    'granizo': {'nombre': 'Granizo', 'mult': {'hielo': 1.4}, 'velocidad': {'hielo': 1.2}, 'chip': 2, 'inmunes': ('hielo',)},
    'tormenta_arena': {'nombre': 'Tormenta de arena', 'mult': {'roca': 1.3, 'tierra': 1.15}, 'velocidad': {'tierra': 1.15}, 'chip': 2,
                       'inmunes': ('roca', 'tierra', 'acero')},
    'niebla': {'nombre': 'Niebla', 'mult': {'fantasma': 1.2, 'siniestro': 1.2}, 'deteccion': 0.6},
    'tormenta_electrica': {'nombre': 'Tormenta electrica', 'mult': {'electrico': 1.3}, 'velocidad': {'electrico': 1.15}},
}
DURACION_CLIMA = 15000

# movimientos que cambian el clima (los de asistencia/especiales, para que no llueva con cada golpe)
CLIMA_MOVIMIENTO = {
    'danza_lluvia': 'lluvia', 'hidrobomba': 'lluvia', 'dia_soleado': 'sol', 'llamarada': 'sol', 'rayo_solar': 'sol',
    'granizo': 'granizo', 'nevada': 'granizo', 'ventisca': 'granizo', 'viento_hielo': 'granizo',
    'tormenta_arena': 'tormenta_arena', 'terremoto': 'tormenta_arena', 'avalancha': 'tormenta_arena',
    'niebla': 'niebla', 'bola_sombra': 'niebla', 'pulso_umbrio': 'niebla', 'trueno': 'tormenta_electrica',
}

_fuentes, _textos = {}, {}
CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'mundo')
_imagenes, _escaladas = {}, {}


def imagen(tipo, nombre, era=None):
    """Sprite de assets/mundo/<era>/<tipo>/<nombre>.png o, si no hay, de assets/mundo/<tipo>/<nombre>.png. None si no existe."""
    clave = (tipo, nombre, era)
    if clave not in _imagenes:
        rutas = ([os.path.join(CARPETA_ASSETS, era, tipo, nombre + '.png')] if era else []) + [os.path.join(CARPETA_ASSETS, tipo, nombre + '.png')]
        _imagenes[clave] = None
        for ruta in rutas:
            if os.path.isfile(ruta):
                try: _imagenes[clave] = pygame.image.load(ruta).convert_alpha(); break
                except pygame.error: pass
    return _imagenes[clave]


def _escalada(img, ancho, alto=None):
    """Imagen escalada (pixel art: sin suavizar). Sin alto, mantiene la proporcion."""
    alto = alto or max(1, round(img.get_height() * ancho / img.get_width()))
    clave = (id(img), ancho, alto)
    if clave not in _escaladas: _escaladas[clave] = pygame.transform.scale(img, (ancho, alto))
    return _escaladas[clave]


def _texto(texto, tam=16, color=(255, 255, 255)):
    """Texto renderizado una sola vez y guardado."""
    clave = (texto, tam, color)
    if clave not in _textos:
        if tam not in _fuentes: _fuentes[tam] = pygame.font.Font(None, tam)
        _textos[clave] = _fuentes[tam].render(texto, True, color)
    return _textos[clave]


def crear(sala, clima=None, ahora=0):
    """Estado de la sala en juego. clima es el de la sala (en salas interiores no llega)."""
    ent = {'sala': sala, 'm': sala['matriz'], 'tam': sala['tam'], 'objetos': sala['objetos'], 'era': mundos.ERAS[sala['era']],
           'version': 0, 'cache': {}, 'electrico': {}, 'fuego': {}, 'reaccion': {}, 'ocupadas': set(),
           'clima': None, 'clima_hasta': None, 'clima_base': None if sala.get('interior') else clima, 'prox_clima': 0, 'prox_fuego': 0, 'charcos_lluvia': 0, 'ahora': ahora,
           'pendientes': [], 'visuales': [], 'eventos': [], 'fondo': None, 'maquinas': []}
    _buscar_maquinas(ent)
    ent['clima'] = ent['clima_base']
    return ent


def _buscar_maquinas(ent):
    tam = ent['tam']
    ent['maquinas'] = [((c + 0.5) * tam, (f + 0.5) * tam, t) for f, fila in enumerate(ent['m']) for c, t in enumerate(fila)
                       if mundos.TERRENOS[t].get('maquina')]


def tipos_de(entidad):
    """El jugador tiene 'tipos' (lista), los enemigos 'tipo' (uno solo)."""
    return [normalizar_tipo(t) for t in (entidad.get('tipos') or [entidad.get('tipo')]) if t]


# ---------- casillas ----------

def casilla(ent, x, y):
    return int(y // ent['tam']), int(x // ent['tam'])


def terreno_en(ent, x, y):
    f, c = casilla(ent, x, y)
    if 0 <= f < len(ent['m']) and 0 <= c < len(ent['m'][0]): return ent['m'][f][c]
    return 'pared'


def rect_casilla(ent, f, c):
    return pygame.Rect(c * ent['tam'], f * ent['tam'], ent['tam'], ent['tam'])


def _casillas_rect(ent, r):
    f0, c0 = casilla(ent, r.left, r.top)
    f1, c1 = casilla(ent, r.right - 1, r.bottom - 1)
    return {(f, c) for f in range(f0, f1 + 1) for c in range(c0, c1 + 1)}


def _casillas_circulo(ent, x, y, radio):
    """Casillas que toca un circulo."""
    tam, m = ent['tam'], ent['m']
    f0, c0 = casilla(ent, x - radio, y - radio)
    f1, c1 = casilla(ent, x + radio, y + radio)
    salida = []
    for f in range(max(0, f0), min(len(m) - 1, f1) + 1):
        for c in range(max(0, c0), min(len(m[0]) - 1, c1) + 1):
            px, py = max(c * tam, min(x, (c + 1) * tam)), max(f * tam, min(y, (f + 1) * tam))
            if math.hypot(px - x, py - y) <= radio: salida.append((f, c))
    return salida


def cambiar(ent, f, c, nuevo):
    """Cambia el terreno de una casilla. No pone algo que bloquee debajo de alguien (lo dejaria trabado)."""
    if mundos.TERRENOS[nuevo]['bloquea'] and (f, c) in ent['ocupadas']: return False
    viejo = ent['m'][f][c]
    ent['m'][f][c] = nuevo
    ent['version'] += 1; ent['fondo'] = None
    if nuevo != 'fuego': ent['fuego'].pop((f, c), None)
    if mundos.TERRENOS[viejo].get('maquina') or mundos.TERRENOS[nuevo].get('maquina'): _buscar_maquinas(ent)
    return True


# ---------- choques ----------

def solidos(ent, tipos):
    """Rectangulos que no puede atravesar alguien de esos tipos (el agua no frena a los de agua, los fantasma pasan los objetos...)."""
    clave = (ent['version'], tuple(sorted(tipos)))
    if clave not in ent['cache']:
        if len(ent['cache']) > 40: ent['cache'].clear()
        bloquea = lambda t: mundos.TERRENOS[t]['bloquea'] and not any(x in mundos.TERRENOS[t].get('pasan', ()) for x in tipos)
        rects = generacion.rectangulos(ent['m'], bloquea, ent['tam'])
        if 'fantasma' not in tipos: rects += [o['rect'] for o in ent['objetos'] if o['solido']]
        ent['cache'][clave] = rects
    return ent['cache'][clave]


def solidos_proyectil(ent):
    """Lo que frena un proyectil: paredes, maquinas y objetos (el agua y la lava no)."""
    clave = (ent['version'], 'proyectil')
    if clave not in ent['cache']:
        rects = generacion.rectangulos(ent['m'], lambda t: mundos.TERRENOS[t].get('solido'), ent['tam'])
        ent['cache'][clave] = rects + [o['rect'] for o in ent['objetos'] if o['solido']]
    return ent['cache'][clave]


def destructibles(ent):
    """Objetos que se pueden romper (se suman a los objetivos de los ataques)."""
    return [o for o in ent['objetos'] if o['vida'] is not None and o['vida'] > 0]


def mover(ent, rect, dx, dy, tipos):
    """Mueve un rect frenando contra lo solido para esos tipos."""
    duros = solidos(ent, tipos)
    for ax, ay in ((dx, 0), (0, dy)):
        r = rect.move(ax, ay)
        if r.collidelist(duros) == -1: rect.x, rect.y = r.x, r.y


def punto_libre(ent, azar, lejos=None, distancia=0):
    """Centro de una casilla alcanzable, pisable y sin objetos (para hacer aparecer enemigos o jefes)."""
    ocupadas = {c for o in ent['objetos'] for c in o['celdas']}
    tam, m = ent['tam'], ent['m']
    buenas = [(f, c) for f, c in ent['sala']['alcanzables'] if (f, c) not in ocupadas and not mundos.TERRENOS[m[f][c]]['bloquea']
              and m[f][c] not in generacion.PELIGROSOS]
    lejanas = [(f, c) for f, c in buenas if not lejos or math.hypot((c + 0.5) * tam - lejos[0], (f + 0.5) * tam - lejos[1]) >= distancia]
    f, c = azar.choice(lejanas or buenas or [(len(m) // 2, len(m[0]) // 2)])
    return int((c + 0.5) * tam), int((f + 0.5) * tam)


# ---------- efectos sobre pokemon ----------

def _sumar(ef, nuevos):
    for k, v in nuevos.items():
        if k in ('velocidad', 'daño', 'enfriamiento', 'defensa', 'regen'): ef[k] = ef.get(k, 1.0) * v
        elif k == 'empuje': ef[k] = (ef.get(k, (0, 0))[0] + v[0], ef.get(k, (0, 0))[1] + v[1])
        elif k == 'tick': ef[k] = ef.get(k, 0) + v
        else: ef[k] = ef.get(k) or v


def _elegir(tabla, tipos, con_todos=True):
    """Efectos de una tabla para esos tipos. Si es doble tipo se juntan, y el daño por tick es el menor de los dos."""
    entradas = [tabla[t] for t in tipos if t in tabla]
    if not entradas: return tabla.get('todos', {}) if con_todos else {}
    ef = {}
    for e in entradas: _sumar(ef, {k: v for k, v in e.items() if k != 'tick'})
    tick = min(e.get('tick', 0) for e in entradas)
    if tick: ef['tick'] = tick
    return ef


def efectos_de(ent, tipos, rect):
    """Todo lo que el entorno le hace a un pokemon parado en rect: terreno, maquinas cerca, agua electrificada y clima."""
    ef = {}
    _sumar(ef, _elegir(PISADAS.get(terreno_en(ent, *rect.center), {}), tipos))
    usadas = set()
    for x, y, maquina in ent['maquinas']:                      # cada tipo de maquina ayuda una sola vez
        radio, por_tipo = AURAS.get(maquina, (0, {}))
        if maquina not in usadas and math.hypot(x - rect.centerx, y - rect.centery) <= radio * ent['tam']:
            nuevos = _elegir(por_tipo, tipos, False)
            if nuevos: _sumar(ef, nuevos); usadas.add(maquina)
    if ent['electrico'] and not any(t in INMUNES_CHOQUE for t in tipos):
        zona = rect.inflate(ent['tam'] * 0.4, ent['tam'] * 0.4)
        if any((f, c) in ent['electrico'] for f, c in _casillas_rect(ent, zona)): ef['choque'] = True
    clima = CLIMAS.get(ent['clima'])
    if clima:
        _sumar(ef, _elegir({t: {'velocidad': v} for t, v in clima.get('velocidad', {}).items()}, tipos, False))
        temporal = ent['clima_hasta'] is not None                # el clima de la sala no lastima, el de un movimiento si
        if temporal and clima.get('chip') and not any(t in clima.get('inmunes', ()) for t in tipos): _sumar(ef, {'tick': clima['chip']})
    return ef


def deteccion(ent, jugador):
    """Multiplicador del rango con que te ven los enemigos (escondido en hierba/sombra, niebla)."""
    m = 0.3 if jugador.get('oculto') else 1.0
    return m * CLIMAS.get(ent['clima'], {}).get('deteccion', 1.0)


def mult_clima(ent, tipo):
    clima = CLIMAS.get(ent['clima'])
    return clima['mult'].get(normalizar_tipo(tipo), 1.0) if clima else 1.0


# ---------- reacciones a ataques ----------

def reaccionar(ent, x, y, radio, tipo, ahora):
    """Un ataque de ese tipo toco el circulo (x, y, radio): congela agua, quema hierba, electrifica, etc."""
    tipo = normalizar_tipo(tipo)
    if not tipo: return
    for f, c in _casillas_circulo(ent, x, y, radio):
        t = ent['m'][f][c]
        accion = REACCIONES.get(('cinta' if t.startswith('cinta') else t, tipo))
        if not accion or ent['reaccion'].get((f, c, tipo), 0) > ahora: continue
        ent['reaccion'][(f, c, tipo)] = ahora + 250             # no repetir la misma reaccion cada frame
        _hacer(ent, accion, f, c, ahora)


def reaccionar_linea(ent, x0, y0, x1, y1, radio, tipo, ahora):
    """Igual que reaccionar pero a lo largo de un golpe cuerpo a cuerpo."""
    pasos = max(1, int(math.hypot(x1 - x0, y1 - y0) // max(8, radio)))
    for i in range(pasos + 1):
        reaccionar(ent, x0 + (x1 - x0) * i / pasos, y0 + (y1 - y0) * i / pasos, radio, tipo, ahora)


def _hacer(ent, accion, f, c, ahora):
    tam = ent['tam']
    x, y = (c + 0.5) * tam, (f + 0.5) * tam
    if accion[0] == 'convertir':
        if len(accion) < 3 or random.random() < accion[2]: cambiar(ent, f, c, accion[1])
    elif accion[0] == 'electrificar': electrificar(ent, f, c, ahora)
    elif accion[0] == 'encender': encender(ent, f, c, ahora)
    elif accion[0] == 'apagar': cambiar(ent, f, c, 'ceniza')
    elif accion[0] == 'invertir':
        vuelta = {'n': 's', 's': 'n', 'e': 'o', 'o': 'e'}
        cambiar(ent, f, c, 'cinta_' + vuelta[ent['m'][f][c][-1]])
    elif accion[0] == 'pulso':
        ent['reaccion'][(f, c, 'electrico')] = ahora + 3000      # el generador tarda en recargarse
        explotar(ent, x, y, tam * 2.5, 25, 'electrico', False, {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 100}, 'chispa')
    elif accion[0] == 'cortocircuito':
        cambiar(ent, f, c, 'generador_roto')
        explotar(ent, x, y, tam * 2, 35, 'electrico', True, None, 'chispa')


def electrificar(ent, f, c, ahora):
    """Electrifica toda el agua (y cables) conectada a esa casilla por unos segundos."""
    m = ent['m']
    vistas, pendientes = {(f, c)}, [(f, c)]
    while pendientes and len(vistas) < 90:
        a, b = pendientes.pop()
        for na, nb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
            if 0 <= na < len(m) and 0 <= nb < len(m[0]) and (na, nb) not in vistas and m[na][nb] in CONDUCEN:
                vistas.add((na, nb)); pendientes.append((na, nb))
    for casilla_ in vistas:
        if m[casilla_[0]][casilla_[1]] in CONDUCEN: ent['electrico'][casilla_] = ahora + DURACION_ELECTRICO


def encender(ent, f, c, ahora=None):
    if ent['m'][f][c] in ('hierba', 'aceite', 'suelo', 'ceniza', 'fuego') and cambiar(ent, f, c, 'fuego'):
        ent['fuego'][(f, c)] = (ent['ahora'] if ahora is None else ahora) + random.randint(*DURACION_FUEGO)


def explotar(ent, x, y, radio, daño, tipo, al_jugador, efecto=None, clase='fuego'):
    """Encola una explosion: se aplica en actualizar() (asi una explosion puede romper otro barril y encadenar)."""
    ent['pendientes'].append({'x': x, 'y': y, 'radio': radio, 'daño': daño, 'tipo': tipo, 'jugador': al_jugador, 'efecto': efecto, 'clase': clase})


# ---------- objetos ----------

def dañar_objeto(ent, obj, datos, direccion, ahora):
    """Un ataque le pega a un objeto: daño segun material y tipo, empujes, chispas en el metal..."""
    if obj['vida'] is None or obj['vida'] <= 0: return
    tipo = normalizar_tipo(datos.get('tipo'))
    try: base = float(datos.get('daño', 0))
    except (TypeError, ValueError): base = 0
    d = mundos.OBJETOS[obj['nombre']]
    mult = 99 if d.get('arde') and tipo == 'fuego' else MATERIALES.get(obj['material'], {}).get(tipo, 1.0)
    obj['vida'] -= base * mult; obj['golpe'] = ahora
    if tipo == 'electrico' and obj['material'] == 'metal' and ahora >= obj.get('chispa', 0):   # el metal conduce
        obj['chispa'] = ahora + 600
        explotar(ent, obj['rect'].centerx, obj['rect'].centery, ent['tam'] * 1.6, 12, 'electrico', False,
                 {'tipo': 'paralizar', 'duracion': 1000, 'probabilidad': 100}, 'chispa')
    fuerza = EMPUJAN.get(tipo) or (FUERZA_EMBESTIDA if datos.get('forma') == 'embestida' else 0)
    if obj['empujable'] and fuerza and direccion in direccion_vector:
        vx, vy = direccion_vector[direccion]; n = math.hypot(vx, vy) or 1
        obj['vel'] = [vx / n * fuerza, vy / n * fuerza]
    if obj['vida'] <= 0: romper(ent, obj, tipo)


def romper(ent, obj, tipo=None):
    """Saca el objeto, suelta monedas a veces, explota si es explosivo y deja su terreno (charco, aceite, toxico...)."""
    if obj in ent['objetos']: ent['objetos'].remove(obj)
    obj['vida'] = 0
    ent['version'] += 1
    d = mundos.OBJETOS[obj['nombre']]
    x, y = obj['rect'].center
    ent['visuales'].append({'clase': 'polvo', 'x': x, 'y': y, 'radio': max(obj['rect'].size) // 2, 'color': d['color'], 'vida': 18})
    ent['eventos'].append(('roto', x, y, d['color']))           # para las particulas y la experiencia
    if random.random() < PROB_MONEDAS: ent['eventos'].append(('monedas', x, y, random.randint(2, 6)))
    if d.get('explota'): explotar(ent, x, y, EXPLOSION['radio'], EXPLOSION['daño'], 'fuego', True)
    if d.get('al_romper'):
        for f, c in _casillas_circulo(ent, x, y, ent['tam'] * 0.8):
            if ent['m'][f][c] in generacion.PISABLES: cambiar(ent, f, c, d['al_romper'])
    if d.get('arde') and tipo == 'fuego':                       # lo que arde deja fuego donde estaba
        for f, c in _casillas_rect(ent, obj['rect']): encender(ent, f, c)


def _actualizar_empujados(ent, ctx, ahora):
    """Objetos deslizandose: chocan con paredes, otros objetos y enemigos (les pegan). Al agua se hunden."""
    for obj in [o for o in ent['objetos'] if o['vel'][0] or o['vel'][1]]:
        rapidez = math.hypot(*obj['vel'])
        duros = generacion.rectangulos(ent['m'], lambda t: mundos.TERRENOS[t].get('solido'), ent['tam']) + \
            [o['rect'] for o in ent['objetos'] if o['solido'] and o is not obj]
        choco = False
        for i in (0, 1):
            obj['resto'][i] += obj['vel'][i]; paso = int(obj['resto'][i]); obj['resto'][i] -= paso
            r = obj['rect'].move(paso if i == 0 else 0, paso if i == 1 else 0)
            if r.collidelist(duros) != -1: choco = True
            else: obj['rect'].topleft = r.topleft                # se mueve el mismo rect (las listas de solidos lo comparten)
        for e in ctx['enemigos']:
            if e['vida'] > 0 and obj['rect'].colliderect(e['rect']):
                ctx['dañar_enemigo'](e, round(rapidez * 3), 'normal', None); choco = True
        ent['version'] += 1
        t = terreno_en(ent, *obj['rect'].center)
        if t in ('agua', 'lava'):                               # se hunde (el hielo congela el agua, en la lava se quema)
            f, c = casilla(ent, *obj['rect'].center)
            if obj['material'] == 'hielo' and t == 'agua': cambiar(ent, f, c, 'hielo')
            romper(ent, obj, 'fuego' if t == 'lava' else None); continue
        if choco:
            if mundos.OBJETOS[obj['nombre']].get('explota') and rapidez > 6: romper(ent, obj, 'fuego'); continue
            obj['vel'] = [0.0, 0.0]
        else:
            obj['vel'] = [v * 0.94 for v in obj['vel']]
            if math.hypot(*obj['vel']) < 0.5: obj['vel'] = [0.0, 0.0]
        if not (obj['vel'][0] or obj['vel'][1]): obj['celdas'] = _casillas_rect(ent, obj['rect']) if obj['solido'] else set()


# ---------- clima ----------

def iniciar_clima(ent, clave, ahora, duracion=DURACION_CLIMA):
    """Clima temporal (de un movimiento o de un jefe). Sin duracion queda toda la sala. Adentro no llueve."""
    if clave not in CLIMAS or ent['sala'].get('interior'): return
    ent['clima'] = clave
    if duracion: ent['clima_hasta'] = ahora + duracion
    else: ent['clima_base'], ent['clima_hasta'] = clave, None


def al_usar_movimiento(ent, nombre, ahora):
    """Algunos movimientos cambian el clima (lluvia, sol, granizo...)."""
    if nombre in CLIMA_MOVIMIENTO: iniciar_clima(ent, CLIMA_MOVIMIENTO[nombre], ahora)


def _casilla_al_azar(ent, terrenos):
    m = ent['m']
    for _ in range(25):
        f, c = random.randint(1, len(m) - 2), random.randint(1, len(m[0]) - 2)
        if m[f][c] in terrenos: return f, c
    return None


def _actualizar_clima(ent, ctx, ahora):
    """Una vez por segundo: la lluvia hace charcos y apaga el fuego, el sol derrite y seca, el granizo congela, caen rayos."""
    if ent['clima_hasta'] is not None and ahora >= ent['clima_hasta']:   # se termina el clima del movimiento: vuelve el de la sala
        ent['clima'], ent['clima_hasta'] = ent['clima_base'], None
    if not ent['clima'] or ahora < ent['prox_clima']: return
    ent['prox_clima'] = ahora + 1000
    clima = ent['clima']
    if clima == 'lluvia':
        for f, c in list(ent['fuego']): cambiar(ent, f, c, 'ceniza')
        lugar = _casilla_al_azar(ent, ('suelo', 'arena', 'ceniza'))
        if lugar and ent['charcos_lluvia'] < 30:
            cambiar(ent, *lugar, 'charco' if ent['m'][lugar[0]][lugar[1]] != 'arena' else 'lodo'); ent['charcos_lluvia'] += 1
    elif clima == 'sol':
        cambios = {'hielo': 'agua', 'nieve': 'charco', 'charco': 'suelo', 'lodo': 'arena'}
        for _ in range(2):
            lugar = _casilla_al_azar(ent, tuple(cambios))
            if lugar: cambiar(ent, *lugar, cambios[ent['m'][lugar[0]][lugar[1]]])
    elif clima == 'nieve':                                      # nieva despacio: se junta nieve y se congelan los charcos
        lugar = _casilla_al_azar(ent, ('suelo', 'charco'))
        if lugar and ent['charcos_lluvia'] < 25:
            cambiar(ent, *lugar, 'nieve' if ent['m'][lugar[0]][lugar[1]] == 'suelo' else 'hielo'); ent['charcos_lluvia'] += 1
    elif clima == 'granizo':
        for _ in range(2):
            lugar = _casilla_al_azar(ent, ('agua', 'charco'))
            if lugar: cambiar(ent, *lugar, 'hielo')
    elif clima == 'tormenta_electrica' and random.random() < 0.4:   # rayo: prefiere enemigos, metal y agua
        vivos = [e for e in ctx['enemigos'] if e['vida'] > 0]
        metal = [o for o in ent['objetos'] if o['material'] == 'metal']
        if vivos and random.random() < 0.6: x, y = random.choice(vivos)['rect'].center
        elif metal: x, y = random.choice(metal)['rect'].center
        else:
            lugar = _casilla_al_azar(ent, ('agua', 'charco', 'suelo'))
            if not lugar: return
            x, y = (lugar[1] + 0.5) * ent['tam'], (lugar[0] + 0.5) * ent['tam']
        explotar(ent, x, y, 70, 20, 'electrico', False, {'tipo': 'paralizar', 'duracion': 1000, 'probabilidad': 100}, 'rayo')
        f, c = casilla(ent, x, y)
        if ent['m'][f][c] in CONDUCEN: electrificar(ent, f, c, ahora)


# ---------- cada frame ----------

def actualizar(ent, ctx, ahora):
    """
    ctx = {'jugador': j, 'enemigos': [...], 'dañar_jugador': f(daño, tipo), 'dañar_enemigo': f(enemigo, daño, tipo, efecto)}
    Deja en cada pokemon ['entorno'] los efectos que tiene encima (velocidad, daño, resbala, oculto, empuje...).
    """
    j = ctx['jugador']
    ent['ahora'] = ahora
    vivos = [e for e in ctx['enemigos'] if e['vida'] > 0]
    ent['ocupadas'] = set()
    for e in [j] + vivos: ent['ocupadas'] |= _casillas_rect(ent, e['rect'])
    for e in [j] + vivos:                                       # terreno, auras, choques y clima sobre cada pokemon
        tipos = tipos_de(e)
        ef = efectos_de(ent, tipos, e['rect'])
        e['entorno'] = ef
        if e is j: j['oculto'] = bool(ef.get('oculto'))
        daño = ef.get('tick', 0) + (DAÑO_CHOQUE if ef.get('choque') else 0)
        if daño and ahora >= e.get('prox_tick', 0):
            e['prox_tick'] = ahora + TICK
            if e is j: ctx['dañar_jugador'](daño, None)
            else: ctx['dañar_enemigo'](e, daño, None, {'tipo': 'paralizar', 'duracion': 600, 'probabilidad': 100} if ef.get('choque') else None)
        if e is not j and ef.get('empuje'):                      # las cintas tambien llevan a los enemigos
            e.setdefault('resto_cinta', [0.0, 0.0])
            for i in (0, 1): e['resto_cinta'][i] += ef['empuje'][i]
            px, py = int(e['resto_cinta'][0]), int(e['resto_cinta'][1])
            e['resto_cinta'][0] -= px; e['resto_cinta'][1] -= py
            mover(ent, e['rect'], px, py, tipos)
    if ahora >= ent['prox_fuego']:                               # el fuego se esparce por la hierba y quema objetos
        ent['prox_fuego'] = ahora + 400
        for (f, c), hasta in list(ent['fuego'].items()):
            if ahora >= hasta: cambiar(ent, f, c, 'ceniza'); continue
            for nf, nc in ((f + 1, c), (f - 1, c), (f, c + 1), (f, c - 1)):
                if 0 <= nf < len(ent['m']) and 0 <= nc < len(ent['m'][0]) and ent['m'][nf][nc] in ('hierba', 'aceite') and random.random() < 0.25:
                    encender(ent, nf, nc, ahora)
            zona = rect_casilla(ent, f, c)
            for o in [o for o in ent['objetos'] if mundos.OBJETOS[o['nombre']].get('arde') and o['rect'].colliderect(zona)]:
                romper(ent, o, 'fuego')
    ent['electrico'] = {k: v for k, v in ent['electrico'].items() if v > ahora}
    _actualizar_clima(ent, ctx, ahora)
    _actualizar_empujados(ent, ctx, ahora)
    for _ in range(10):                                         # explosiones (pueden encadenarse)
        if not ent['pendientes']: break
        lote, ent['pendientes'] = ent['pendientes'], []
        for ex in lote:
            centro = pygame.Vector2(ex['x'], ex['y'])
            for e in vivos:
                if e['vida'] > 0 and centro.distance_to(e['rect'].center) <= ex['radio'] + max(e['rect'].size) / 2:
                    ctx['dañar_enemigo'](e, ex['daño'], ex['tipo'], ex['efecto'])
            inmune = ex['clase'] != 'fuego' and 'electrico' in tipos_de(j)       # las chispas no lastiman a los electricos
            if ex['jugador'] and not inmune and centro.distance_to(j['rect'].center) <= ex['radio']:
                ctx['dañar_jugador'](ex['daño'] * 0.6, ex['tipo'])
            for o in destructibles(ent):
                if centro.distance_to(o['rect'].center) <= ex['radio']:
                    dañar_objeto(ent, o, {'tipo': ex['tipo'], 'daño': ex['daño']}, None, ahora)
            ent['visuales'].append({'clase': ex['clase'], 'x': ex['x'], 'y': ex['y'], 'radio': ex['radio'], 'vida': 16})
            if ex['clase'] == 'fuego': ent['eventos'].append(('explosion', ex['x'], ex['y'], ex['radio']))
    for v in ent['visuales']: v['vida'] -= 1
    ent['visuales'] = [v for v in ent['visuales'] if v['vida'] > 0]


# ---------- dibujo ----------

def _aclarar(color, k):
    return tuple(max(0, min(255, x + k)) for x in color)


def _dibujar_textura(fondo, t, r, f, c):
    """Dibujito simple para que cada terreno se distinga del piso (hasta que lleguen los sprites)."""
    azar = random.Random(f * 131 + c)
    x, y, tam = r.x, r.y, r.width
    if t in ('hielo', 'cascada_helada'):                         # brillos en diagonal
        for k in (0.25, 0.6):
            pygame.draw.line(fondo, (255, 255, 255), (x + tam * k, y + tam * 0.15), (x + tam * (k + 0.25), y + tam * 0.4), 2)
    elif t in ('agua', 'charco', 'cascada'):                     # olitas
        for k in (0.3, 0.7):
            yy = y + tam * k
            pygame.draw.arc(fondo, (180, 215, 255), (x + tam * 0.15, yy - 6, tam * 0.35, 12), 0, math.pi, 2)
            pygame.draw.arc(fondo, (180, 215, 255), (x + tam * 0.5, yy - 6, tam * 0.35, 12), 0, math.pi, 2)
    elif t == 'nieve':
        for _ in range(5): pygame.draw.circle(fondo, (205, 215, 230), (x + azar.randint(6, tam - 6), y + azar.randint(6, tam - 6)), 3)
    elif t == 'hierba':                                          # matitas
        for _ in range(4):
            px, py = x + azar.randint(8, tam - 8), y + azar.randint(12, tam - 4)
            pygame.draw.line(fondo, (30, 100, 30), (px, py), (px - 4, py - 10), 2)
            pygame.draw.line(fondo, (30, 100, 30), (px, py), (px + 4, py - 10), 2)
    elif t in ('lava', 'toxico'):                                # burbujas
        color = (255, 200, 60) if t == 'lava' else (200, 120, 230)
        for _ in range(3): pygame.draw.circle(fondo, color, (x + azar.randint(8, tam - 8), y + azar.randint(8, tam - 8)), azar.randint(3, 6), 2)
    elif t in ('arena', 'lodo', 'ceniza'):                       # granitos
        for _ in range(6): fondo.set_at((x + azar.randint(2, tam - 3), y + azar.randint(2, tam - 3)), (90, 70, 40) if t != 'ceniza' else (40, 40, 40))
    elif t == 'puente':                                          # tablones
        for k in range(1, 4): pygame.draw.line(fondo, (90, 60, 30), (x, y + tam * k // 4), (x + tam, y + tam * k // 4), 2)


def _armar_fondo(ent):
    """Piso, terrenos, paredes y maquinas en una imagen (se rehace solo cuando cambia el terreno)."""
    m, tam, era = ent['m'], ent['tam'], ent['era']
    fondo = pygame.Surface((len(m[0]) * tam, len(m) * tam))
    con_sprite = set()
    for f, fila in enumerate(m):
        for c, t in enumerate(fila):
            r = pygame.Rect(c * tam, f * tam, tam, tam)
            img = imagen('terrenos', t, era['clave'])               # si hay sprite del terreno se usa ese
            if img:
                fondo.blit(_escalada(img, tam, tam), r); con_sprite.add(t); continue
            if t == 'suelo': color = _aclarar(era['suelo'], 8 if (f + c) % 2 else -4)   # piso del color de la era
            elif t == 'pared': color = era['pared']
            else: color = mundos.TERRENOS[t]['color']
            pygame.draw.rect(fondo, color, r)
            if mundos.TERRENOS[t].get('maquina'): pygame.draw.rect(fondo, (20, 20, 20), r, 3)
            if t.startswith('cinta'):                                # flechitas de las cintas
                dx, dy = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'o': (-1, 0)}[t[-1]]
                cx, cy = r.center
                pygame.draw.line(fondo, (200, 200, 60), (cx - dx * tam // 4, cy - dy * tam // 4), (cx + dx * tam // 4, cy + dy * tam // 4), 3)
                pygame.draw.circle(fondo, (200, 200, 60), (cx + dx * tam // 4, cy + dy * tam // 4), 5)
            if t == 'cable': pygame.draw.line(fondo, (40, 40, 40), r.topleft, r.bottomright, 4)
            _dibujar_textura(fondo, t, r, f, c)
    vistos = set()                                                  # un cartel por cada mancha de terreno
    for f, fila in enumerate(m):
        for c, t in enumerate(fila):
            if t in ('suelo', 'pared') or t in con_sprite or (f, c) in vistos: continue
            grupo, pendientes = [(f, c)], [(f, c)]; vistos.add((f, c))
            while pendientes:
                a, b = pendientes.pop()
                for na, nb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= na < len(m) and 0 <= nb < len(m[0]) and (na, nb) not in vistos and m[na][nb] == t:
                        vistos.add((na, nb)); grupo.append((na, nb)); pendientes.append((na, nb))
            a, b = min(grupo, key=lambda p: (p[0] - sum(g[0] for g in grupo) / len(grupo)) ** 2 + (p[1] - sum(g[1] for g in grupo) / len(grupo)) ** 2)
            claro = sum(mundos.TERRENOS[t]['color'] or (0, 0, 0)) > 450
            txt = _texto('cinta' if t.startswith('cinta') else t.replace('_', ' '), 16, (30, 30, 30) if claro else (235, 235, 235))
            fondo.blit(txt, txt.get_rect(center=((b + 0.5) * tam, (a + 0.5) * tam)))
    ent['fondo'] = fondo


def dibujar(ent, ventana, cx, cy, ahora, tipos_jugador=()):
    """Dibuja la sala vista desde la camara (cx, cy). Las maquinas muestran su radio solo si ayudan a tus tipos."""
    if ent['fondo'] is None: _armar_fondo(ent)
    ventana.blit(ent['fondo'], (0, 0), pygame.Rect(cx, cy, *ventana.get_size()))
    tam = ent['tam']
    for x, y, maquina in ent['maquinas']:                          # radio de ayuda de las maquinas que te sirven
        if maquina in AURAS and any(t in AURAS[maquina][1] for t in tipos_jugador): pygame.draw.circle(ventana, mundos.TERRENOS[maquina]['color'], (round(x - cx), round(y - cy)), round(AURAS[maquina][0] * tam), 1)
    for (f, c) in ent['fuego']:                                    # fuego que titila
        r = rect_casilla(ent, f, c).move(-cx, -cy)
        pygame.draw.rect(ventana, (255, 200, 40) if (ahora // 120 + f + c) % 2 else (240, 90, 20), r.inflate(-10, -10))
    for (f, c) in ent['electrico']:                                # agua electrificada
        r = rect_casilla(ent, f, c).move(-cx, -cy)
        pygame.draw.line(ventana, (255, 240, 60), r.topleft, r.bottomright, 2)
        pygame.draw.line(ventana, (255, 240, 60), r.topright, r.bottomleft, 2)
    for o in ent['objetos']:
        d = mundos.OBJETOS[o['nombre']]
        r = o['rect'].move(-cx, -cy)
        if not r.colliderect(ventana.get_rect()): continue
        img = imagen('objetos', o['nombre'], ent['era']['clave'])
        if tiene_sprites(o['nombre']):                              # un pokemon puesto como objeto (Kecleon en la tienda): animado
            if 'animador' not in o:
                o['animador'] = AnimadorPokemon(o['nombre'], pygame.Rect(0, 0, 10, 10), max(o['rect'].size) + 30); o['animador'].cambiar('idle', 0, True)
            o['animador'].rect.center = r.center
            o['animador'].actualizar()
            if o['animador'].dibujar(ventana): continue
        if img:                                                     # sprite: mismo ancho que el objeto, apoyado abajo (un arbol sobresale hacia arriba)
            sprite = _escalada(img, r.width)
            ventana.blit(sprite, sprite.get_rect(midbottom=r.midbottom))
            if ahora - o['golpe'] < 90: pygame.draw.rect(ventana, (255, 255, 255), sprite.get_rect(midbottom=r.midbottom), 2)
        else:                                                       # sin sprite: forma basica con el nombre
            color = (255, 255, 255) if ahora - o['golpe'] < 90 else d['color']
            (pygame.draw.ellipse if d.get('forma') == 'circulo' else pygame.draw.rect)(ventana, color, r)
            (pygame.draw.ellipse if d.get('forma') == 'circulo' else pygame.draw.rect)(ventana, (15, 15, 15), r, 2)
            if d.get('explota'): pygame.draw.circle(ventana, (230, 40, 30), r.center, 5)   # punto rojo = explota
            claro = sum(d['color']) > 450
            txt = _texto(o['nombre'].replace('_', ' '), 15, (20, 20, 20) if claro else (240, 240, 240))
            ventana.blit(txt, txt.get_rect(center=r.center))
        if o['vida'] is not None and o['vida'] < o['max_vida']:
            pygame.draw.rect(ventana, (60, 0, 0), (r.x, r.y - 6, r.width, 4))
            pygame.draw.rect(ventana, (230, 200, 40), (r.x, r.y - 6, int(r.width * max(0, o['vida']) / o['max_vida']), 4))
    for v in ent['visuales']:                                      # explosiones, chispas, rayos y polvo de lo que se rompe
        x, y = round(v['x'] - cx), round(v['y'] - cy)
        if v['clase'] == 'polvo': pygame.draw.circle(ventana, v['color'], (x, y), round(v['radio'] * (1.6 - v['vida'] / 18)), 2)
        elif v['clase'] == 'rayo':
            pygame.draw.line(ventana, (255, 255, 180), (x + 20, y - 400), (x - 10, y - 150), 4)
            pygame.draw.line(ventana, (255, 255, 180), (x - 10, y - 150), (x, y), 4)
            pygame.draw.circle(ventana, (255, 250, 120), (x, y), round(v['radio'] * 0.6), 3)
        else:
            color = (255, 240, 80) if v['clase'] == 'chispa' else (255, 120, 30)
            pygame.draw.circle(ventana, color, (x, y), round(v['radio'] * (1.1 - v['vida'] / 32)), 5)


_velos = {}


def _velo(tam, color):
    clave = (tam, color)
    if clave not in _velos:
        _velos[clave] = pygame.Surface(tam, pygame.SRCALPHA); _velos[clave].fill(color)
    return _velos[clave]


def dibujar_clima(ent, ventana, ahora):
    """Capa del clima encima de todo y el cartelito de cuanto le queda."""
    clima = ent['clima']
    if not clima: return
    W, H = ventana.get_size()
    azar = random.Random(ahora // 50)                              # mismo dibujo durante 50 ms
    if clima == 'lluvia':
        ventana.blit(_velo((W, H), (40, 60, 120, 45)), (0, 0))
        for _ in range(90):
            x, y = azar.randint(0, W), azar.randint(0, H)
            pygame.draw.line(ventana, (150, 180, 255), (x, y), (x - 4, y + 14), 1)
    elif clima == 'granizo':
        ventana.blit(_velo((W, H), (200, 220, 255, 40)), (0, 0))
        for _ in range(70): pygame.draw.circle(ventana, (250, 250, 255), (azar.randint(0, W), azar.randint(0, H)), 2)
    elif clima == 'tormenta_arena':
        ventana.blit(_velo((W, H), (190, 150, 80, 80)), (0, 0))
        for _ in range(50):
            x, y = azar.randint(0, W), azar.randint(0, H)
            pygame.draw.line(ventana, (220, 190, 120), (x, y), (x + 18, y + 3), 1)
    elif clima == 'nieve':
        ventana.blit(_velo((W, H), (220, 230, 255, 30)), (0, 0))
        for i in range(60):                                     # copos que caen despacio
            x = (i * 97 + ahora // 40 * (1 + i % 3)) % W
            y = (i * 53 + ahora // 25 * (1 + i % 2)) % H
            pygame.draw.circle(ventana, (255, 255, 255), (x, y), 2 + i % 2)
    elif clima == 'nublado': ventana.blit(_velo((W, H), (60, 60, 70, 40)), (0, 0))
    elif clima == 'niebla': ventana.blit(_velo((W, H), (170, 170, 170, 110)), (0, 0))
    elif clima == 'sol': ventana.blit(_velo((W, H), (255, 220, 80, 35)), (0, 0))
    elif clima == 'tormenta_electrica':
        destello = any(v['clase'] == 'rayo' and v['vida'] > 12 for v in ent['visuales'])
        ventana.blit(_velo((W, H), (255, 255, 255, 70) if destello else (20, 20, 50, 70)), (0, 0))
    texto = CLIMAS[clima]['nombre'] + ('' if ent['clima_hasta'] is None else ' ' + str(max(0, (ent['clima_hasta'] - ahora) // 1000 + 1)) + 's')
    t = _texto(texto, 20, (255, 255, 255))
    ventana.blit(t, t.get_rect(midtop=(W // 2, 24)))
