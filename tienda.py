"""
tienda.py - Objetos de la tienda (nada cura) y lo que hacen sobre el jugador.

    j['inventario'] = tienda.inventario_nuevo()
    tienda.mult(j['inventario'], 'daño')       # multiplicador de todo lo comprado para esa clave
    tienda.nueva_sala(j['inventario'], tipo)   # descuenta las salas que les quedan a los objetos temporales
"""

import random
import mts

SALAS_X = 3          # cuantas salas de combate duran los objetos X

# precio, descripcion, color del dibujo provisorio y efecto:
#   'repelente': salas con menos enemigos          'temporal': (clave, multiplicador, salas)
#   'permanente': {clave: multiplicador}           'tipo': (tipo, multiplicador) potencia los ataques de ese tipo
#   'critico': (probabilidad, salas)
ITEMS = {
    'repelente': {'nombre': 'Repelente', 'precio': 60, 'color': (170, 90, 200), 'repelente': 3, 'desc': '35% menos enemigos por 3 salas'},
    'superrepelente': {'nombre': 'Superrepelente', 'precio': 100, 'color': (200, 70, 160), 'repelente': 5, 'desc': '35% menos enemigos por 5 salas'},
    'maxirepelente': {'nombre': 'Maxirepelente', 'precio': 150, 'color': (230, 60, 120), 'repelente': 8, 'desc': '35% menos enemigos por 8 salas'},
    'ataque_x': {'nombre': 'Ataque X', 'precio': 90, 'color': (220, 70, 60), 'temporal': ('daño', 1.25, SALAS_X), 'desc': '+25% de daño por 3 salas'},
    'defensa_x': {'nombre': 'Defensa X', 'precio': 90, 'color': (70, 110, 220), 'temporal': ('defensa', 0.8, SALAS_X), 'desc': '20% menos daño recibido por 3 salas'},
    'velocidad_x': {'nombre': 'Velocidad X', 'precio': 80, 'color': (90, 200, 220), 'temporal': ('velocidad', 1.2, SALAS_X), 'desc': '+20% de velocidad por 3 salas'},
    'especial_x': {'nombre': 'Especial X', 'precio': 90, 'color': (200, 90, 220), 'temporal': ('enfriamiento', 0.8, SALAS_X), 'desc': 'recargas 20% mas rapidas por 3 salas'},
    'directo': {'nombre': 'Directo', 'precio': 80, 'color': (240, 170, 40), 'critico': (0.2, SALAS_X), 'desc': '20% de golpes criticos (x1.8) por 3 salas'},
    'eter': {'nombre': 'Eter', 'precio': 120, 'color': (120, 200, 255), 'permanente': {'regen': 1.5, 'gasto': 0.75}, 'desc': 'la energia vuelve 50% mas rapido y el sprint gasta menos'},
    'cinta_fuerte': {'nombre': 'Cinta Fuerte', 'precio': 200, 'color': (230, 200, 60), 'permanente': {'daño': 1.12}, 'desc': '+12% de daño para siempre'},
    'garra_rapida': {'nombre': 'Garra Rapida', 'precio': 180, 'color': (200, 200, 200), 'permanente': {'enfriamiento': 0.9}, 'desc': 'recargas 10% mas rapidas para siempre'},
    'polvo_veloz': {'nombre': 'Polvo Veloz', 'precio': 160, 'color': (230, 230, 150), 'permanente': {'velocidad': 1.1}, 'desc': '+10% de velocidad para siempre'},
    'chaleco_asalto': {'nombre': 'Chaleco Asalto', 'precio': 200, 'color': (70, 70, 140), 'permanente': {'defensa': 0.88}, 'desc': '12% menos daño recibido para siempre'},
    'amuleto_moneda': {'nombre': 'Amuleto Moneda', 'precio': 150, 'color': (250, 210, 60), 'permanente': {'monedas': 1.5}, 'desc': '+50% de monedas para siempre'},
    # objetos de tipo: +20% a los ataques de ese tipo
    'agua_mistica': {'nombre': 'Agua Mistica', 'precio': 140, 'color': (60, 130, 240), 'tipo': ('agua', 1.2)},
    'carbon': {'nombre': 'Carbon', 'precio': 140, 'color': (60, 50, 50), 'tipo': ('fuego', 1.2)},
    'iman': {'nombre': 'Iman', 'precio': 140, 'color': (245, 220, 40), 'tipo': ('electrico', 1.2)},
    'antiderretir': {'nombre': 'Antiderretir', 'precio': 140, 'color': (150, 220, 255), 'tipo': ('hielo', 1.2)},
    'cinturon_negro': {'nombre': 'Cinturon Negro', 'precio': 140, 'color': (30, 30, 30), 'tipo': ('lucha', 1.2)},
    'arena_fina': {'nombre': 'Arena Fina', 'precio': 140, 'color': (200, 170, 100), 'tipo': ('tierra', 1.2)},
    'pico_afilado': {'nombre': 'Pico Afilado', 'precio': 140, 'color': (230, 230, 230), 'tipo': ('volador', 1.2)},
    'piedra_dura': {'nombre': 'Piedra Dura', 'precio': 140, 'color': (180, 160, 60), 'tipo': ('roca', 1.2)},
    'colmillo_dragon': {'nombre': 'Colmillo Dragon', 'precio': 140, 'color': (110, 60, 250), 'tipo': ('dragon', 1.2)},
    'gafas_de_sol': {'nombre': 'Gafas de Sol', 'precio': 140, 'color': (110, 85, 70), 'tipo': ('siniestro', 1.2)},
    'hechizo': {'nombre': 'Hechizo', 'precio': 140, 'color': (115, 85, 150), 'tipo': ('fantasma', 1.2)},
    'cuchara_torcida': {'nombre': 'Cuchara Torcida', 'precio': 140, 'color': (250, 90, 140), 'tipo': ('psiquico', 1.2)},
    'flecha_venenosa': {'nombre': 'Flecha Venenosa', 'precio': 140, 'color': (160, 60, 160), 'tipo': ('veneno', 1.2)},
    'revestimiento_metalico': {'nombre': 'Revest. Metalico', 'precio': 140, 'color': (180, 180, 200), 'tipo': ('acero', 1.2)},
    'semilla_milagro': {'nombre': 'Semilla Milagro', 'precio': 140, 'color': (120, 200, 80), 'tipo': ('planta', 1.2)},
    'pañuelo_seda': {'nombre': 'Pañuelo Seda', 'precio': 140, 'color': (230, 230, 210), 'tipo': ('normal', 1.2)},
}
for _clave, _item in ITEMS.items():
    if 'tipo' in _item: _item['desc'] = '+20% de daño a los ataques de tipo ' + _item['tipo'][0]

# objetos que van a la mochila: evolucion (se usan desde el menu de equipo con TAB) y las MT
ITEMS.update({
    'piedra_trueno': {'nombre': 'Piedra Trueno', 'precio': 220, 'color': (250, 220, 40), 'objeto': True, 'desc': 'hace evolucionar a Pikachu y Magneton'},
    'piedra_alba': {'nombre': 'Piedra Alba', 'precio': 220, 'color': (120, 220, 230), 'objeto': True, 'desc': 'hace evolucionar a Snorunt en Froslass'},
    'garra_afilada': {'nombre': 'Garra Afilada', 'precio': 220, 'color': (200, 200, 220), 'objeto': True, 'desc': 'hace evolucionar a Sneasel'},
    'cordon_union': {'nombre': 'Cordon Union', 'precio': 240, 'color': (240, 140, 60), 'objeto': True,
                     'desc': 'evoluciona a los que en los juegos evolucionan por intercambio (Graveler, Machoke, Gurdurr)'},
    'lazo_amistad': {'nombre': 'Lazo Amistad', 'precio': 110, 'color': (250, 120, 170), 'temporal': ('amistad', 2.0, SALAS_X),
                     'desc': 'el doble de chance de que un pokemon quiera unirse por 3 salas'},
})
for _clave, _mt in mts.MTS.items():
    ITEMS[_clave] = {'nombre': _mt['nombre'], 'precio': _mt['precio'], 'color': (90, 90, 200), 'objeto': True, 'mt': True,
                     'desc': 'enseña ' + _mt['nombre'][3:] + ' (tipo ' + _mt['tipo'] + ') en una casilla desde el menu de equipo'}
EVOLUCION = ('piedra_trueno', 'piedra_alba', 'garra_afilada', 'cordon_union')

COMUNES = ('repelente', 'superrepelente', 'maxirepelente', 'ataque_x', 'defensa_x', 'velocidad_x', 'especial_x', 'directo', 'eter', 'lazo_amistad')
DESTACADOS = ('cinta_fuerte', 'garra_rapida', 'polvo_veloz', 'chaleco_asalto', 'amuleto_moneda')
DE_TIPO = tuple(k for k, v in ITEMS.items() if 'tipo' in v)


def inventario_nuevo():
    return {'permanente': {}, 'temporal': [], 'repelente': 0, 'tipos': {}, 'critico': [0.0, 0], 'comprados': [], 'objetos': {}}


def mult(inv, clave):
    """Multiplicador de todo lo comprado para esa clave ('daño', 'defensa', 'velocidad', 'enfriamiento', 'regen', 'gasto', 'monedas')."""
    m = inv['permanente'].get(clave, 1.0)
    for c, v, salas in inv['temporal']:
        if c == clave and salas > 0: m *= v
    return m


def mult_tipo(inv, tipo):
    return inv['tipos'].get(tipo, 1.0)


def critico(inv):
    """Multiplicador de un golpe: x1.8 si sale critico."""
    prob, salas = inv['critico']
    return 1.8 if salas > 0 and random.random() < prob else 1.0


def factor_enemigos(inv):
    return 0.65 if inv['repelente'] > 0 else 1.0


def nueva_sala(inv, tipo):
    """Al entrar a una sala con enemigos se gasta una sala de cada objeto temporal."""
    if tipo not in ('combate', 'jefe', 'regi'): return
    inv['repelente'] = max(0, inv['repelente'] - 1)
    inv['temporal'] = [[c, v, s - 1] for c, v, s in inv['temporal'] if s - 1 > 0]
    inv['critico'][1] = max(0, inv['critico'][1] - 1)


def activos(inv):
    """Textos cortos de lo que tenes andando (para el HUD)."""
    lineas = []
    if inv['repelente']: lineas.append('Repelente ' + str(inv['repelente']))
    for c, v, s in inv['temporal']: lineas.append(c + ' x' + str(v) + ' (' + str(s) + ')')
    if inv['critico'][1]: lineas.append('Directo (' + str(inv['critico'][1]) + ')')
    return lineas


def surtido(azar, tipos_equipo, vitrinas, equipo=(), necesita=()):
    """Que objeto va en cada vitrina: comunes en los estantes (una MT que alguien de tu equipo puede aprender),
    permanentes en las mesas (uno suele ser del tipo de tu equipo o el objeto que alguien necesita para evolucionar)."""
    comunes = azar.sample(COMUNES, min(len(COMUNES), sum(1 for v in vitrinas if not v['destacado'])))
    posibles = sorted({k for n in equipo for k in mts.aprendibles(n)})
    if posibles and comunes: comunes[-1] = azar.choice(posibles)
    propios = [k for k in DE_TIPO if ITEMS[k]['tipo'][0] in tipos_equipo]
    destacados = azar.sample(DESTACADOS, 2)
    if propios and azar.random() < 0.6: destacados[1] = azar.choice(propios)
    elif azar.random() < 0.3: destacados[1] = azar.choice(DE_TIPO)
    if necesita and azar.random() < 0.7: destacados[0] = azar.choice(list(necesita))
    salida, ic, idd = [], 0, 0
    for v in vitrinas:
        if v['destacado']: salida.append(destacados[idd % len(destacados)]); idd += 1
        else: salida.append(comunes[ic % len(comunes)]); ic += 1
    return salida


def comprar(j, clave):
    """Intenta comprar: devuelve el texto para el cartel."""
    item, inv = ITEMS[clave], j['inventario']
    if j['monedas'] < item['precio']: return 'No te alcanza (' + str(item['precio']) + ' $)'
    j['monedas'] -= item['precio']
    inv['comprados'].append(clave)
    if item.get('objeto'): inv['objetos'][clave] = inv['objetos'].get(clave, 0) + 1   # a la mochila
    if 'repelente' in item: inv['repelente'] += item['repelente']
    if 'temporal' in item: inv['temporal'].append(list(item['temporal']))
    if 'critico' in item: inv['critico'] = [item['critico'][0], inv['critico'][1] + item['critico'][1]]
    for c, v in item.get('permanente', {}).items(): inv['permanente'][c] = inv['permanente'].get(c, 1.0) * v
    if 'tipo' in item:
        t, v = item['tipo']; inv['tipos'][t] = inv['tipos'].get(t, 1.0) * v
    return 'Compraste ' + item['nombre']
