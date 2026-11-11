"""
datos.py - Todo lo que es informacion del juego (no dibuja nada):

    ataques     habilidades y sinergias de ataques.py
    pokemones   especies, movimientos, tabla de tipos, roles, asistencias (antes pokemones.py)
    mts         Maquinas Tecnicas que se compran y se enseñan
    tienda      objetos de Kecleon, inventario y lo que hace cada cosa comprada
    mundos      eras, terrenos, objetos, piezas, climas y el plan de salas de la partida

    from datos import pokemones, mundos, mts, tienda, ataques
"""

import json
import os
import random
import unicodedata
from types import SimpleNamespace
import mecanicas


# ==================== ataques ====================

habilidades = {
    'ataque_rapido': {'nombre': 'Ataque Rápido', 'api': 'quick-attack', 'tipo': 'normal', 'modo': 'embestida', 'daño': 18, 'distancia': 200, 'velocidad': 16, 'area': 14, 'enfriamiento': 2800, 'retroceso': 10, 'efecto': None},
    'velocidad_extrema': {'nombre': 'Velocidad Extrema', 'api': 'extreme-speed', 'tipo': 'normal', 'modo': 'embestida', 'daño': 30, 'distancia': 280, 'velocidad': 20, 'area': 16, 'enfriamiento': 4500, 'retroceso': 20, 'efecto': None},
    'chorro_agua': {'nombre': 'Acua Jet', 'api': 'aqua-jet', 'tipo': 'agua', 'modo': 'embestida', 'daño': 22, 'distancia': 220, 'velocidad': 16, 'area': 16, 'enfriamiento': 3200, 'retroceso': 15, 'efecto': None},
    'envite_igneo': {'nombre': 'Envite Ígneo', 'api': 'flare-blitz', 'tipo': 'fuego', 'modo': 'embestida', 'daño': 40, 'distancia': 240, 'velocidad': 14, 'area': 20, 'enfriamiento': 5500, 'retroceso': 30, 'efecto': {'tipo': 'quemar', 'duracion': 2500, 'probabilidad': 40}},
    'placaje_electrico': {'nombre': 'Placaje Eléctrico', 'api': 'volt-tackle', 'tipo': 'electrico', 'modo': 'embestida', 'daño': 38, 'distancia': 240, 'velocidad': 15, 'area': 20, 'enfriamiento': 5500, 'retroceso': 25, 'efecto': {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 30}},
    'voltio_cruel': {'nombre': 'Voltio Cruel', 'api': 'wild-charge', 'tipo': 'electrico', 'modo': 'embestida', 'daño': 34, 'distancia': 230, 'velocidad': 15, 'area': 18, 'enfriamiento': 5000, 'retroceso': 25, 'efecto': {'tipo': 'paralizar', 'duracion': 1200, 'probabilidad': 20}},
    'carga_dragon': {'nombre': 'Carga Dragón', 'api': 'dragon-rush', 'tipo': 'dragon', 'modo': 'embestida', 'daño': 38, 'distancia': 230, 'velocidad': 14, 'area': 22, 'enfriamiento': 5500, 'retroceso': 35, 'efecto': {'tipo': 'ralentizar', 'duracion': 1200, 'probabilidad': 20}},
    'pajaro_osado': {'nombre': 'Pájaro Osado', 'api': 'brave-bird', 'tipo': 'volador', 'modo': 'embestida', 'daño': 42, 'distancia': 280, 'velocidad': 17, 'area': 20, 'enfriamiento': 6000, 'retroceso': 30, 'efecto': None},
    'a_bocajarro': {'nombre': 'A Bocajarro', 'api': 'close-combat', 'tipo': 'lucha', 'modo': 'embestida', 'daño': 36, 'distancia': 170, 'velocidad': 14, 'area': 22, 'enfriamiento': 5000, 'retroceso': 35, 'efecto': None},
    'puño_dinamico': {'nombre': 'Puño Dinámico', 'api': 'dynamic-punch', 'tipo': 'lucha', 'modo': 'embestida', 'daño': 34, 'distancia': 150, 'velocidad': 12, 'area': 24, 'enfriamiento': 5500, 'retroceso': 40, 'efecto': {'tipo': 'ralentizar', 'duracion': 1800, 'probabilidad': 60}},
    'excavar': {'nombre': 'Excavar', 'api': 'dig', 'tipo': 'tierra', 'modo': 'embestida', 'daño': 26, 'distancia': 260, 'velocidad': 12, 'area': 18, 'enfriamiento': 4500, 'retroceso': 15, 'efecto': None},
    'rodar': {'nombre': 'Rodar', 'api': 'rollout', 'tipo': 'roca', 'modo': 'embestida', 'daño': 24, 'distancia': 260, 'velocidad': 13, 'area': 22, 'enfriamiento': 4200, 'retroceso': 20, 'efecto': None},
    'trueno': {'nombre': 'Trueno', 'api': 'thunder', 'tipo': 'electrico', 'modo': 'proyectil', 'daño': 44, 'distancia': 420, 'velocidad': 7, 'area': 28, 'enfriamiento': 6000, 'cantidad': 1, 'abanico': 0, 'atraviesa': False, 'retroceso': 15, 'efecto': {'tipo': 'paralizar', 'duracion': 1700, 'probabilidad': 40}},
    'fragmento_hielo': {'nombre': 'Fragmento de Hielo', 'api': 'ice-shard', 'tipo': 'hielo', 'modo': 'proyectil', 'daño': 18, 'distancia': 340, 'velocidad': 18, 'area': 10, 'enfriamiento': 2600, 'cantidad': 1, 'abanico': 0, 'atraviesa': False, 'retroceso': 10, 'efecto': None},
    'tornado': {'nombre': 'Tornado', 'api': 'gust', 'tipo': 'volador', 'modo': 'proyectil', 'daño': 12, 'distancia': 300, 'velocidad': 10, 'area': 12, 'enfriamiento': 3200, 'cantidad': 3, 'abanico': 36, 'atraviesa': False, 'retroceso': 10, 'efecto': None},
    'shuriken_agua': {'nombre': 'Shuriken de Agua', 'api': 'water-shuriken', 'tipo': 'agua', 'modo': 'proyectil', 'daño': 13, 'distancia': 360, 'velocidad': 14, 'area': 10, 'enfriamiento': 3000, 'cantidad': 3, 'abanico': 30, 'atraviesa': False, 'retroceso': 5, 'efecto': None},
    'lanzallamas': {'nombre': 'Lanzallamas', 'api': 'flamethrower', 'tipo': 'fuego', 'modo': 'proyectil', 'daño': 14, 'distancia': 260, 'velocidad': 11, 'area': 16, 'enfriamiento': 3800, 'cantidad': 3, 'abanico': 24, 'atraviesa': False, 'retroceso': 5, 'efecto': {'tipo': 'quemar', 'duracion': 2200, 'probabilidad': 30}},
    'rayo_solar': {'nombre': 'Rayo Solar', 'api': 'solar-beam', 'tipo': 'planta', 'modo': 'proyectil', 'daño': 46, 'distancia': 460, 'velocidad': 8, 'area': 26, 'enfriamiento': 6500, 'cantidad': 1, 'abanico': 0, 'atraviesa': True, 'retroceso': 15, 'efecto': None},
    'huesomerang': {'nombre': 'Huesomerang', 'api': 'bonemerang', 'tipo': 'tierra', 'modo': 'proyectil', 'daño': 26, 'distancia': 380, 'velocidad': 11, 'area': 16, 'enfriamiento': 4000, 'cantidad': 1, 'abanico': 0, 'atraviesa': True, 'retroceso': 10, 'efecto': None},
    'disparo_lodo': {'nombre': 'Disparo Lodo', 'api': 'mud-shot', 'tipo': 'tierra', 'modo': 'proyectil', 'daño': 18, 'distancia': 320, 'velocidad': 10, 'area': 14, 'enfriamiento': 3000, 'cantidad': 1, 'abanico': 0, 'atraviesa': False, 'retroceso': 5, 'efecto': {'tipo': 'ralentizar', 'duracion': 1800, 'probabilidad': 50}},
    'surf': {'nombre': 'Surf', 'api': 'surf', 'tipo': 'agua', 'modo': 'area', 'daño': 30, 'area': 170, 'enfriamiento': 5200, 'retroceso': 0, 'efecto': None},
    'descarga': {'nombre': 'Descarga', 'api': 'discharge', 'tipo': 'electrico', 'modo': 'area', 'daño': 28, 'area': 150, 'enfriamiento': 4500, 'retroceso': 0, 'efecto': {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 30}},
    'onda_trueno': {'nombre': 'Onda Trueno', 'api': 'thunder-wave', 'tipo': 'electrico', 'modo': 'area', 'daño': 0, 'area': 190, 'enfriamiento': 6500, 'retroceso': 0, 'efecto': {'tipo': 'paralizar', 'duracion': 2000, 'probabilidad': 100}},
    'ventisca': {'nombre': 'Ventisca', 'api': 'blizzard', 'tipo': 'hielo', 'modo': 'area', 'daño': 26, 'area': 180, 'enfriamiento': 5500, 'retroceso': 0, 'efecto': {'tipo': 'ralentizar', 'duracion': 2500, 'probabilidad': 70}},
    'terremoto': {'nombre': 'Terremoto', 'api': 'earthquake', 'tipo': 'tierra', 'modo': 'area', 'daño': 34, 'area': 200, 'enfriamiento': 6000, 'retroceso': 0, 'efecto': None},
    'ataque_arena': {'nombre': 'Ataque Arena', 'api': 'sand-attack', 'tipo': 'tierra', 'modo': 'area', 'daño': 0, 'area': 170, 'enfriamiento': 5000, 'retroceso': 0, 'efecto': {'tipo': 'ralentizar', 'duracion': 3000, 'probabilidad': 100}},
    'danza_espada': {'nombre': 'Danza Espada', 'api': 'swords-dance', 'tipo': 'normal', 'modo': 'buff', 'duracion': 8000, 'enfriamiento': 14000, 'mejoras': {'daño': 1.5}},
    'agilidad': {'nombre': 'Agilidad', 'api': 'agility', 'tipo': 'psiquico', 'modo': 'buff', 'duracion': 7000, 'enfriamiento': 12000, 'mejoras': {'velocidad': 1.35, 'cooldown': 0.8}},
    'corpulencia': {'nombre': 'Corpulencia', 'api': 'bulk-up', 'tipo': 'lucha', 'modo': 'buff', 'duracion': 8000, 'enfriamiento': 15000, 'mejoras': {'daño': 1.25, 'resistencia': 0.8}},
    'paz_mental': {'nombre': 'Paz Mental', 'api': 'calm-mind', 'tipo': 'psiquico', 'modo': 'buff', 'duracion': 9000, 'enfriamiento': 14000, 'mejoras': {'daño': 1.3, 'cooldown': 0.85}},
    'danza_dragon': {'nombre': 'Danza Dragón', 'api': 'dragon-dance', 'tipo': 'dragon', 'modo': 'buff', 'duracion': 8000, 'enfriamiento': 14000, 'mejoras': {'daño': 1.25, 'velocidad': 1.25}},
    'defensa_ferrea': {'nombre': 'Defensa Férrea', 'api': 'iron-defense', 'tipo': 'acero', 'modo': 'buff', 'duracion': 6000, 'enfriamiento': 12000, 'mejoras': {'resistencia': 0.5}},
    'pulimento': {'nombre': 'Pulimento', 'api': 'rock-polish', 'tipo': 'roca', 'modo': 'buff', 'duracion': 6000, 'enfriamiento': 11000, 'mejoras': {'velocidad': 1.5}},
    'descanso': {'nombre': 'Descanso', 'api': 'rest', 'tipo': 'psiquico', 'modo': 'curar', 'cura': 0.5, 'duracion': 2500, 'dormir': True, 'enfriamiento': 20000},
    'recuperacion': {'nombre': 'Recuperación', 'api': 'recover', 'tipo': 'normal', 'modo': 'curar', 'cura': 0.3, 'duracion': 1200, 'dormir': False, 'enfriamiento': 16000},
    'respiro': {'nombre': 'Respiro', 'api': 'roost', 'tipo': 'volador', 'modo': 'curar', 'cura': 0.3, 'duracion': 1200, 'dormir': False, 'enfriamiento': 14000},
    'sintesis': {'nombre': 'Síntesis', 'api': 'synthesis', 'tipo': 'planta', 'modo': 'curar', 'cura': 0.35, 'duracion': 1200, 'dormir': False, 'enfriamiento': 15000},
    'proteccion': {'nombre': 'Protección', 'api': 'protect', 'tipo': 'normal', 'modo': 'escudo', 'duracion': 900, 'enfriamiento': 8000},
    'deteccion': {'nombre': 'Detección', 'api': 'detect', 'tipo': 'lucha', 'modo': 'escudo', 'duracion': 900, 'enfriamiento': 8000},
    # expansion
    'poder_pasado': {'nombre': 'Poder Pasado', 'api': 'ancient-power', 'tipo': 'roca', 'modo': 'proyectil', 'daño': 20, 'distancia': 380, 'velocidad': 10, 'area': 14, 'enfriamiento': 5000, 'cantidad': 3, 'abanico': 30, 'atraviesa': False, 'retroceso': 15, 'efecto': None},
    'danza_aleteo': {'nombre': 'Danza Aleteo', 'api': 'quiver-dance', 'tipo': 'bicho', 'modo': 'buff', 'duracion': 8000, 'enfriamiento': 14000, 'mejoras': {'daño': 1.25, 'velocidad': 1.2, 'cooldown': 0.9}},
    'fuerza_lunar_mt': {'nombre': 'Fuerza Lunar', 'api': 'moonblast', 'tipo': 'hada', 'modo': 'proyectil', 'daño': 44, 'distancia': 440, 'velocidad': 9, 'area': 24, 'enfriamiento': 6000, 'cantidad': 1, 'abanico': 0, 'atraviesa': False, 'retroceso': 30, 'efecto': None},
    'vozarron_mt': {'nombre': 'Vozarrón', 'api': 'hyper-voice', 'tipo': 'normal', 'modo': 'area', 'daño': 30, 'area': 170, 'enfriamiento': 5500, 'retroceso': 40, 'efecto': None},
}

sinergias = {
    'trueno_apoyo': {'nombre': 'Trueno', 'api': 'thunder', 'tipo': 'electrico', 'modo': 'rayos', 'cantidad': 4, 'daño': 40, 'efecto': {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 40}, 'enfriamiento': 40000},
    'refuerzo': {'nombre': 'Refuerzo', 'api': 'helping-hand', 'tipo': 'normal', 'modo': 'buff_equipo', 'duracion': 10000, 'mejoras': {'daño': 1.4}, 'enfriamiento': 35000},
    'viento_afin': {'nombre': 'Viento Afín', 'api': 'tailwind', 'tipo': 'volador', 'modo': 'buff_equipo', 'duracion': 10000, 'mejoras': {'velocidad': 1.3, 'cooldown': 0.85}, 'enfriamiento': 35000},
    'foco_energia': {'nombre': 'Foco Energía', 'api': 'focus-energy', 'tipo': 'normal', 'modo': 'buff_equipo', 'duracion': 10000, 'mejoras': {'daño': 1.25, 'cooldown': 0.85}, 'enfriamiento': 35000},
    'pantalla_luz': {'nombre': 'Pantalla de Luz', 'api': 'light-screen', 'tipo': 'psiquico', 'modo': 'buff_equipo', 'duracion': 8000, 'mejoras': {'resistencia': 0.5}, 'enfriamiento': 40000},
    'reflejo': {'nombre': 'Reflejo', 'api': 'reflect', 'tipo': 'psiquico', 'modo': 'buff_equipo', 'duracion': 8000, 'mejoras': {'resistencia': 0.55}, 'enfriamiento': 40000},
    'remolino': {'nombre': 'Remolino', 'api': 'whirlwind', 'tipo': 'normal', 'modo': 'desaparecer', 'cantidad': 3, 'enfriamiento': 50000},
    'canto': {'nombre': 'Canto', 'api': 'sing', 'tipo': 'normal', 'modo': 'efecto_sala', 'daño': 0, 'efecto': {'tipo': 'paralizar', 'duracion': 3500, 'probabilidad': 100}, 'enfriamiento': 45000},
    'aromaterapia': {'nombre': 'Aromaterapia', 'api': 'aromatherapy', 'tipo': 'planta', 'modo': 'curar_equipo', 'cura': 0.35, 'enfriamiento': 45000},
    'deseo': {'nombre': 'Deseo', 'api': 'wish', 'tipo': 'normal', 'modo': 'curar_equipo', 'cura': 0.3, 'enfriamiento': 45000},
    'velo_sagrado': {'nombre': 'Velo Sagrado', 'api': 'safeguard', 'tipo': 'normal', 'modo': 'escudo_equipo', 'duracion': 3500, 'enfriamiento': 50000},
    'terremoto_apoyo': {'nombre': 'Terremoto', 'api': 'earthquake', 'tipo': 'tierra', 'modo': 'onda', 'area': 400, 'daño': 40, 'efecto': None, 'enfriamiento': 40000},
    'surf_apoyo': {'nombre': 'Surf', 'api': 'surf', 'tipo': 'agua', 'modo': 'onda', 'area': 400, 'daño': 38, 'efecto': None, 'enfriamiento': 40000},
    'ventisca_apoyo': {'nombre': 'Ventisca', 'api': 'blizzard', 'tipo': 'hielo', 'modo': 'efecto_sala', 'daño': 22, 'efecto': {'tipo': 'ralentizar', 'duracion': 5000, 'probabilidad': 100}, 'enfriamiento': 45000},
    'onda_trueno_apoyo': {'nombre': 'Onda Trueno', 'api': 'thunder-wave', 'tipo': 'electrico', 'modo': 'efecto_sala', 'daño': 0, 'efecto': {'tipo': 'paralizar', 'duracion': 3000, 'probabilidad': 100}, 'enfriamiento': 40000},
    'tumba_rocas': {'nombre': 'Tumba Rocas', 'api': 'rock-tomb', 'tipo': 'roca', 'modo': 'efecto_sala', 'daño': 15, 'efecto': {'tipo': 'ralentizar', 'duracion': 4000, 'probabilidad': 100}, 'enfriamiento': 38000},
    'tormenta_arena': {'nombre': 'Tormenta Arena', 'api': 'sandstorm', 'tipo': 'roca', 'modo': 'efecto_sala', 'daño': 10, 'efecto': {'tipo': 'ralentizar', 'duracion': 5000, 'probabilidad': 100}, 'enfriamiento': 38000},
    'giro_fuego': {'nombre': 'Giro Fuego', 'api': 'fire-spin', 'tipo': 'fuego', 'modo': 'anillo', 'cantidad': 12, 'daño': 18, 'velocidad': 10, 'distancia': 320, 'area': 10, 'efecto': {'tipo': 'quemar', 'duracion': 2000, 'probabilidad': 40}, 'enfriamiento': 40000},
    'shuriken_apoyo': {'nombre': 'Shuriken de Agua', 'api': 'water-shuriken', 'tipo': 'agua', 'modo': 'anillo', 'cantidad': 12, 'daño': 16, 'velocidad': 12, 'distancia': 340, 'area': 9, 'efecto': None, 'enfriamiento': 38000},
}

ataques = SimpleNamespace(habilidades=habilidades, sinergias=sinergias)

EFECTOS_FRASE = {'quemar': 'puede quemar (le va sacando vida de a poco)', 'paralizar': 'puede paralizar (no se mueve ni ataca un rato)',
                 'dormir': 'duerme a los enemigos (el proximo golpe pega x1,5 y los despierta)', 'ralentizar': 'puede frenarlos (se mueven a la mitad)',
                 'empujar': 'empuja lejos'}
BUFF_FRASE = {'daño': 'pegas', 'defensa': 'recibis', 'velocidad': 'te moves', 'enfriamiento': 'tus recargas tardan'}


def explicar_movimiento(datos, casilla=None):
    """Lo que hace un movimiento contado en palabras (para la seccion de ataques y la ficha). casilla 0 = E (combo y parry)."""
    if not datos: return 'Sin datos.'
    forma, tipo = datos.get('forma'), datos.get('tipo') or 'normal'
    cantidad = int(datos.get('cantidad') or 1)
    if forma == 'cuerpo':
        frase = 'Golpe cuerpo a cuerpo de tipo ' + tipo + '.'
        if casilla in (None, 0): frase += ' En E sale como combo de 3 golpes con un remate que barre; apretalo justo cuando te van a pegar y es un parry.'
    elif forma == 'proyectil':
        frase = 'Dispara ' + ('un proyectil' if cantidad == 1 else str(cantidad) + ' proyectiles en abanico') + ' de tipo ' + tipo
        frase += (' que atraviesan a los enemigos.' if cantidad > 1 else ' que atraviesa a los enemigos.') if datos.get('atraviesa') else '.'
    elif forma == 'area':
        frase = ('Una onda de tipo ' + tipo + ' alrededor tuyo que pega a todos los que esten cerca.') if datos.get('daño') else \
                'Una onda alrededor tuyo que no hace daño pero afecta a todos los que alcanza.'
    elif forma == 'embestida':
        frase = 'Te tiras hacia adelante y golpeas a todo lo que tocas en el camino (tipo ' + tipo + ').'
    elif forma == 'buff':
        partes = []
        for clave, valor in (datos.get('buffs') or {}).items():
            if clave == 'sprint': partes.append('correr no gasta energia'); continue
            cambio = round(abs(valor - 1) * 100)
            if clave == 'defensa': partes.append('recibis ' + str(cambio) + '% menos daño')
            elif clave == 'enfriamiento': partes.append('tus recargas son ' + str(cambio) + '% mas rapidas')
            else: partes.append(BUFF_FRASE.get(clave, clave) + ' ' + str(cambio) + '% mas')
        frase = 'Te potencia ' + str(round(float(datos.get('duracion', 0)) / 1000, 1)).replace('.0', '') + ' segundos: ' + ', '.join(partes) + '.'
    elif forma == 'curar':
        frase = 'Te curas el ' + str(int(datos.get('porcentaje', 0))) + '% de la vida al instante.'
    elif forma == 'mecanica':
        frase = 'Especial propio de su línea (' + datos.get('nombre', '') + '): ' + datos.get('desc', '') + '.'
    else: frase = 'Movimiento de tipo ' + tipo + '.'
    ef = datos.get('efecto')
    if ef and ef.get('tipo') in EFECTOS_FRASE:
        prob = ef.get('probabilidad', 100)
        frase += ' ' + EFECTOS_FRASE[ef['tipo']].capitalize() + ('' if prob >= 100 else ' (' + str(int(prob)) + '% de las veces)') + '.'
    return frase


def describir_asistencia(a):
    """Texto de lo que hace una asistencia (lo que el pokemon de la banca hace con F / G)."""
    mec = a['mecanica']
    if mec == 'impacto': return 'golpe de area en el punto apuntado (daño ' + str(a['daño']) + ', radio ' + str(a['area']) + ')'
    if mec == 'escudo': return 'el activo recibe solo el 25% del daño durante ' + str(a['duracion'] // 1000) + ' s'
    if mec == 'furia': return 'daño x1.6 y recargas x0.7 durante ' + str(a['duracion'] // 1000) + ' s'
    if mec == 'carrera': return 'velocidad x1.6 y correr gratis durante ' + str(a['duracion'] // 1000) + ' s'
    if mec == 'curar': return 'cura el ' + str(a['porcentaje']) + '% de la vida del activo'
    if mec == 'desvanecer': return 'les saca el ' + str(a['porcentaje']) + '% de la vida a los enemigos comunes en un radio de ' + str(a['area']) + ' y el ' + str(a['porcentaje_jefe']) + '% a un jefe'
    return 'aplica ' + str((a.get('efecto') or {}).get('tipo')) + ' a todos los enemigos cercanos'


def nombre_ataque(clave):
    """Nombre para mostrar ('fuerza_rayo' -> 'Rayo potenciado', 'onda_surf' -> 'Onda de Surf', 'mtb_rayo' -> 'Rayo')."""
    if clave.startswith('fuerza_'): return clave[7:].replace('_', ' ').title() + ' potenciado'
    if clave.startswith('onda_'): return 'Onda de ' + clave[5:].replace('_', ' ').title()
    if clave.startswith('mtb_') or clave.startswith('mt_'): return clave.split('_', 1)[1].replace('_', ' ').title()
    if clave.startswith('mec_') and clave[4:] in mecanicas.MECANICAS: return mecanicas.MECANICAS[clave[4:]]['nombre']   # el especial propio de la linea
    return clave.replace('_', ' ').title()

ESTADOS_TXT = {'quemar': 'quema', 'paralizar': 'paraliza', 'dormir': 'duerme', 'ralentizar': 'frena', 'empujar': 'empuja'}
BUFFS_TXT = {'defensa': 'daño recibido', 'daño': 'daño', 'velocidad': 'velocidad', 'enfriamiento': 'recargas'}


def describir_movimiento(datos):
    """Texto corto de lo que hace un movimiento: forma, daño, alcance, efecto y espera ('golpe cuerpo a cuerpo, daño 20, quema (15%), espera 0.5 s')."""
    if not datos: return 'sin datos'
    def num(clave):
        try: return float(datos.get(clave) or 0)
        except (TypeError, ValueError): return 0.0
    forma, partes = datos.get('forma'), []
    if forma == 'buff':
        for clave, valor in (datos.get('buffs') or {}).items():
            if clave == 'sprint': partes.append('correr no gasta energía'); continue
            cambio = round((valor - 1) * 100)
            partes.append(BUFFS_TXT.get(clave, clave) + ' ' + ('+' if cambio > 0 else '') + str(cambio) + '%')
        partes.append('durante ' + str(round(num('duracion') / 1000, 1)) + ' s')
    elif forma == 'curar':
        partes.append('cura el ' + str(int(num('porcentaje'))) + '% de la vida')
    else:
        partes.append({'cuerpo': 'golpe cuerpo a cuerpo', 'proyectil': 'disparo', 'area': 'onda alrededor tuyo', 'embestida': 'embestida',
                       'mecanica': datos.get('nombre', 'especial propio')}.get(forma, str(forma)))
        if num('daño'): partes.append('daño ' + str(int(num('daño'))))
        if forma in ('proyectil', 'embestida') and num('distancia'): partes.append('alcance ' + str(int(num('distancia'))))
        if forma == 'area' and num('area'): partes.append('radio ' + str(int(num('area'))))
        if int(num('cantidad')) > 1: partes.append(str(int(num('cantidad'))) + ' a la vez')
        ef = datos.get('efecto')
        if ef: partes.append(ESTADOS_TXT.get(ef.get('tipo'), str(ef.get('tipo'))) + (' (' + str(int(ef['probabilidad'])) + '%)' if ef.get('probabilidad', 100) < 100 else ''))
        if datos.get('atraviesa'): partes.append('atraviesa')
    if num('enfriamiento'): partes.append('espera ' + str(round(num('enfriamiento') / 1000, 1)) + ' s')
    return ', '.join(partes)


# ==================== pokemones ====================

def armar_pokemones():
    """Especies, movimientos, tabla de tipos, roles, especiales, asistencias y evoluciones."""
    movimientos = {'demolicion': {'tipo': 'lucha', 'forma': 'cuerpo', 'daño': 22, 'distancia': 65, 'area': 38, 'velocidad': 0, 'enfriamiento': 450, 'retroceso': 35, 'efecto': None}, 'aura_esfera': {'tipo': 'lucha', 'forma': 'proyectil', 'daño': 28, 'distancia': 380, 'area': 15, 'velocidad': 9, 'enfriamiento': 750, 'retroceso': 10, 'efecto': None}, 'patada_ignea': {'tipo': 'fuego', 'forma': 'cuerpo', 'daño': 26, 'distancia': 72, 'area': 35, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 45, 'efecto': {'tipo': 'quemar', 'duracion': 2200, 'probabilidad': 15}}, 'llamarada': {'tipo': 'fuego', 'forma': 'proyectil', 'daño': 31, 'distancia': 360, 'area': 20, 'velocidad': 8, 'enfriamiento': 850, 'retroceso': 15, 'efecto': {'tipo': 'quemar', 'duracion': 2500, 'probabilidad': 30}}, 'chispa': {'tipo': 'electrico', 'forma': 'cuerpo', 'daño': 20, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 420, 'retroceso': 20, 'efecto': {'tipo': 'paralizar', 'duracion': 1300, 'probabilidad': 20}}, 'rayo': {'tipo': 'electrico', 'forma': 'proyectil', 'daño': 30, 'distancia': 420, 'area': 15, 'velocidad': 11, 'enfriamiento': 700, 'retroceso': 10, 'efecto': {'tipo': 'paralizar', 'duracion': 1700, 'probabilidad': 25}}, 'acua_jet': {'tipo': 'agua', 'forma': 'cuerpo', 'daño': 21, 'distancia': 78, 'area': 40, 'velocidad': 0, 'enfriamiento': 430, 'retroceso': 30, 'efecto': None}, 'hidrobomba': {'tipo': 'agua', 'forma': 'proyectil', 'daño': 34, 'distancia': 340, 'area': 24, 'velocidad': 7, 'enfriamiento': 900, 'retroceso': 30, 'efecto': {'tipo': 'empujar', 'distancia': 30}}, 'garra_dragon': {'tipo': 'dragon', 'forma': 'cuerpo', 'daño': 27, 'distancia': 70, 'area': 36, 'velocidad': 0, 'enfriamiento': 470, 'retroceso': 45, 'efecto': None}, 'pulso_dragon': {'tipo': 'dragon', 'forma': 'proyectil', 'daño': 30, 'distancia': 390, 'area': 18, 'velocidad': 9, 'enfriamiento': 780, 'retroceso': 20, 'efecto': None}, 'puño_hielo': {'tipo': 'hielo', 'forma': 'cuerpo', 'daño': 23, 'distancia': 64, 'area': 36, 'velocidad': 0, 'enfriamiento': 480, 'retroceso': 30, 'efecto': {'tipo': 'ralentizar', 'duracion': 1800, 'probabilidad': 25}}, 'rayo_hielo': {'tipo': 'hielo', 'forma': 'proyectil', 'daño': 29, 'distancia': 400, 'area': 17, 'velocidad': 9, 'enfriamiento': 760, 'retroceso': 15, 'efecto': {'tipo': 'ralentizar', 'duracion': 2400, 'probabilidad': 45}}, 'pistola_agua': {'tipo': 'agua', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'surf': {'tipo': 'agua', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'mordisco': {'tipo': 'siniestro', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'tajo_umbral': {'tipo': 'siniestro', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'pulso_umbrio': {'tipo': 'siniestro', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'finta': {'tipo': 'siniestro', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'ventisca': {'tipo': 'hielo', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'aliento_hielo': {'tipo': 'hielo', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'picotazo': {'tipo': 'volador', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'ataque_ala': {'tipo': 'volador', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'vuelo': {'tipo': 'volador', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'tajo_aereo': {'tipo': 'volador', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'doble_patada': {'tipo': 'lucha', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'golpe_karate': {'tipo': 'lucha', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'confusion': {'tipo': 'psiquico', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'psicorrayo': {'tipo': 'electrico', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'psiquico': {'tipo': 'psiquico', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'premonicion': {'tipo': 'psiquico', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'lenguetazo': {'tipo': 'fantasma', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'bola_sombra': {'tipo': 'fantasma', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'infortunio': {'tipo': 'fantasma', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'garra_umbria': {'tipo': 'fantasma', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'impactrueno': {'tipo': 'electrico', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'onda_thunder': {'tipo': 'electrico', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'excavar': {'tipo': 'tierra', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'terremoto': {'tipo': 'tierra', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'bofeton_lodo': {'tipo': 'tierra', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'lanzarrocas': {'tipo': 'roca', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'avalancha': {'tipo': 'volador', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'romperrocas': {'tipo': 'roca', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'pedrada': {'tipo': 'roca', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'enfado': {'tipo': 'dragon', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'cola_dragon': {'tipo': 'dragon', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'ascuas': {'tipo': 'fuego', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'envite_igneo': {'tipo': 'fuego', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'picotazo_veneno': {'tipo': 'volador', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'bomba_lodo': {'tipo': 'tierra', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'puya_nociva': {'tipo': 'veneno', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'colmillo_veneno': {'tipo': 'veneno', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'placaje': {'tipo': 'normal', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'ataque_rapido': {'tipo': 'normal', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'golpe_cuerpo': {'tipo': 'normal', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'hiper_rayo': {'tipo': 'electrico', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'garra_metal': {'tipo': 'acero', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'cabeza_hierro': {'tipo': 'acero', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'cañon_flash': {'tipo': 'acero', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'cola_de_hierro': {'tipo': 'acero', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'latigo_cepa': {'tipo': 'planta', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}, 'hoja_afilada': {'tipo': 'planta', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'energia_bola': {'tipo': 'planta', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'rayo_solar': {'tipo': 'electrico', 'forma': 'proyectil', 'daño': 22, 'distancia': 320, 'area': 14, 'velocidad': 8, 'enfriamiento': 800, 'retroceso': 10, 'efecto': None}, 'sentencia': {'tipo': 'normal', 'forma': 'cuerpo', 'daño': 16, 'distancia': 60, 'area': 34, 'velocidad': 0, 'enfriamiento': 500, 'retroceso': 15, 'efecto': None}}

    pokemones = {'lapras': {'pokedex': 131, 'tipo': ['agua', 'hielo'], 'peso': None, 'altura': None, 'vida_base': 130, 'vida': 144, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'acua_jet', 'ataque_proyectil': 'rayo_hielo'}, 'sneasel': {'pokedex': 215, 'tipo': ['siniestro', 'hielo'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['mordisco', 'tajo_umbral', 'pulso_umbrio', 'finta'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'tajo_umbral'}, 'weavile': {'pokedex': 461, 'tipo': ['siniestro', 'hielo'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['mordisco', 'tajo_umbral', 'pulso_umbrio', 'finta'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'tajo_umbral'}, 'snorunt': {'pokedex': 361, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'rayo_hielo', 'ataque_proyectil': 'ventisca'}, 'glalie': {'pokedex': 362, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'rayo_hielo', 'ataque_proyectil': 'ventisca'}, 'froslass': {'pokedex': 478, 'tipo': ['hielo', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'puño_hielo', 'ataque_proyectil': 'rayo_hielo'}, 'spheal': {'pokedex': 363, 'tipo': ['agua', 'hielo'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'sealeo': {'pokedex': 364, 'tipo': ['agua', 'hielo'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 118, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'walrein': {'pokedex': 365, 'tipo': ['agua', 'hielo'], 'peso': None, 'altura': None, 'vida_base': 110, 'vida': 132, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'vanillite': {'pokedex': 582, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 36, 'vida': 83, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'rayo_hielo', 'ataque_proyectil': 'ventisca'}, 'vanillish': {'pokedex': 583, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 51, 'vida': 93, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'rayo_hielo', 'ataque_proyectil': 'ventisca'}, 'vanilluxe': {'pokedex': 584, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 71, 'vida': 106, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'rayo_hielo', 'ataque_proyectil': 'ventisca'}, 'rookidee': {'pokedex': 821, 'tipo': ['volador'], 'peso': None, 'altura': None, 'vida_base': 38, 'vida': 85, 'ataques': ['picotazo', 'ataque_ala', 'vuelo', 'tajo_aereo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo', 'ataque_proyectil': 'ataque_ala'}, 'corvisquire': {'pokedex': 822, 'tipo': ['volador'], 'peso': None, 'altura': None, 'vida_base': 68, 'vida': 104, 'ataques': ['picotazo', 'ataque_ala', 'vuelo', 'tajo_aereo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo', 'ataque_proyectil': 'ataque_ala'}, 'corviknight': {'pokedex': 823, 'tipo': ['volador', 'acero'], 'peso': None, 'altura': None, 'vida_base': 98, 'vida': 124, 'ataques': ['picotazo', 'ataque_ala', 'vuelo', 'tajo_aereo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo', 'ataque_proyectil': 'ataque_ala'}, 'hawlucha': {'pokedex': 701, 'tipo': ['lucha', 'volador'], 'peso': None, 'altura': None, 'vida_base': 78, 'vida': 111, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'natu': {'pokedex': 177, 'tipo': ['psiquico', 'volador'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'}, 'xatu': {'pokedex': 178, 'tipo': ['psiquico', 'volador'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'}, 'drifloon': {'pokedex': 425, 'tipo': ['fantasma', 'volador'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 118, 'ataques': ['lenguetazo', 'bola_sombra', 'infortunio', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'bola_sombra'}, 'drifblim': {'pokedex': 426, 'tipo': ['fantasma', 'volador'], 'peso': None, 'altura': None, 'vida_base': 150, 'vida': 158, 'ataques': ['lenguetazo', 'bola_sombra', 'infortunio', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'bola_sombra'}, 'magnemite': {'pokedex': 81, 'tipo': ['electrico', 'acero'], 'peso': None, 'altura': None, 'vida_base': 25, 'vida': 76, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'magneton': {'pokedex': 82, 'tipo': ['electrico', 'acero'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'magnezone': {'pokedex': 462, 'tipo': ['electrico', 'acero'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'pichu': {'pokedex': 172, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 20, 'vida': 73, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'pikachu': {'pokedex': 25, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 35, 'vida': 83, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'chispa', 'ataque_proyectil': 'rayo'}, 'raichu': {'pokedex': 26, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'mareep': {'pokedex': 179, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'flaaffy': {'pokedex': 180, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'ampharos': {'pokedex': 181, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 118, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'chispa', 'ataque_proyectil': 'rayo'}, 'shinx': {'pokedex': 403, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'luxio': {'pokedex': 404, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'luxray': {'pokedex': 405, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'electrike': {'pokedex': 309, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'manectric': {'pokedex': 310, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'sandshrew': {'pokedex': 27, 'tipo': ['tierra'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'}, 'sandslash': {'pokedex': 28, 'tipo': ['tierra'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 109, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'}, 'geodude': {'pokedex': 74, 'tipo': ['roca', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['lanzarrocas', 'avalancha', 'romperrocas', 'pedrada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lanzarrocas', 'ataque_proyectil': 'avalancha'}, 'graveler': {'pokedex': 75, 'tipo': ['roca', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['lanzarrocas', 'avalancha', 'romperrocas', 'pedrada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lanzarrocas', 'ataque_proyectil': 'avalancha'}, 'golem': {'pokedex': 76, 'tipo': ['roca', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['lanzarrocas', 'avalancha', 'romperrocas', 'pedrada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lanzarrocas', 'ataque_proyectil': 'avalancha'}, 'cubone': {'pokedex': 104, 'tipo': ['tierra'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'}, 'marowak': {'pokedex': 105, 'tipo': ['tierra'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'}, 'wooper': {'pokedex': 194, 'tipo': ['agua', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'quagsire': {'pokedex': 195, 'tipo': ['agua', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 122, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'gible': {'pokedex': 443, 'tipo': ['dragon', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 58, 'vida': 98, 'ataques': ['garra_dragon', 'pulso_dragon', 'enfado', 'cola_dragon'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'}, 'gabite': {'pokedex': 444, 'tipo': ['dragon', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 68, 'vida': 104, 'ataques': ['garra_dragon', 'pulso_dragon', 'enfado', 'cola_dragon'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'}, 'garchomp': {'pokedex': 445, 'tipo': ['dragon', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 108, 'vida': 130, 'ataques': ['garra_dragon', 'pulso_dragon', 'enfado', 'cola_dragon'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'}, 'golett': {'pokedex': 622, 'tipo': ['tierra', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 59, 'vida': 98, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo', 'lenguetazo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'}, 'golurk': {'pokedex': 623, 'tipo': ['tierra', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 89, 'vida': 118, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo', 'lenguetazo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'}, 'mankey': {'pokedex': 56, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'primeape': {'pokedex': 57, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'annihilape': {'pokedex': 979, 'tipo': ['lucha', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 110, 'vida': 132, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'machop': {'pokedex': 66, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'machoke': {'pokedex': 67, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'machamp': {'pokedex': 68, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 118, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'demolicion', 'ataque_proyectil': 'aura_esfera'}, 'torchic': {'pokedex': 255, 'tipo': ['fuego'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['ascuas', 'llamarada', 'patada_ignea', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'}, 'combusken': {'pokedex': 256, 'tipo': ['fuego', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['ascuas', 'llamarada', 'patada_ignea', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'}, 'blaziken': {'pokedex': 257, 'tipo': ['fuego', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['ascuas', 'llamarada', 'patada_ignea', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'patada_ignea', 'ataque_proyectil': 'llamarada'}, 'riolu': {'pokedex': 447, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'lucario': {'pokedex': 448, 'tipo': ['lucha', 'acero'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'demolicion', 'ataque_proyectil': 'aura_esfera'}, 'timburr': {'pokedex': 532, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 109, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'gurdurr': {'pokedex': 533, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'conkeldurr': {'pokedex': 534, 'tipo': ['lucha'], 'peso': None, 'altura': None, 'vida_base': 105, 'vida': 128, 'ataques': ['doble_patada', 'golpe_karate', 'demolicion', 'aura_esfera'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'golpe_karate'}, 'mudkip': {'pokedex': 258, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'marshtomp': {'pokedex': 259, 'tipo': ['agua', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 106, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'swampert': {'pokedex': 260, 'tipo': ['agua', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 125, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'acua_jet', 'ataque_proyectil': 'hidrobomba'}, 'squirtle': {'pokedex': 7, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 44, 'vida': 89, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'wartortle': {'pokedex': 8, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 59, 'vida': 98, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'blastoise': {'pokedex': 9, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 79, 'vida': 111, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'froakie': {'pokedex': 656, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 41, 'vida': 87, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'frogadier': {'pokedex': 657, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 54, 'vida': 95, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'greninja': {'pokedex': 658, 'tipo': ['agua', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 72, 'vida': 107, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'acua_jet', 'ataque_proyectil': 'hidrobomba'}, 'mareanie': {'pokedex': 747, 'tipo': ['veneno', 'agua'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['picotazo_veneno', 'bomba_lodo', 'puya_nociva', 'colmillo_veneno'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'bomba_lodo'}, 'toxapex': {'pokedex': 748, 'tipo': ['veneno', 'agua'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['picotazo_veneno', 'bomba_lodo', 'puya_nociva', 'colmillo_veneno'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'bomba_lodo'}, 'oshawott': {'pokedex': 501, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'dewott': {'pokedex': 502, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 109, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'samurott': {'pokedex': 503, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 122, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'clodsire': {'pokedex': 980, 'tipo': ['veneno', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 130, 'vida': 144, 'ataques': ['picotazo_veneno', 'bomba_lodo', 'puya_nociva', 'colmillo_veneno'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'bomba_lodo'}, 'samurott_hisui': {'pokedex': 503, 'tipo': ['agua', 'siniestro'], 'peso': 'placeholder', 'altura': 'placeholder', 'vida_base': 90, 'vida': 118, 'ataques': ['pistola_agua', 'hidrobomba', 'surf', 'acua_jet'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'pistola_agua', 'ataque_proyectil': 'hidrobomba'}, 'fletchling': {'pokedex': 661, 'tipo': ['normal', 'volador'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['placaje', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'ataque_rapido'}, 'fletchinder': {'pokedex': 662, 'tipo': ['fuego', 'volador'], 'peso': None, 'altura': None, 'vida_base': 62, 'vida': 100, 'ataques': ['ascuas', 'llamarada', 'patada_ignea', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'}, 'talonflame': {'pokedex': 663, 'tipo': ['fuego', 'volador'], 'peso': None, 'altura': None, 'vida_base': 78, 'vida': 111, 'ataques': ['ascuas', 'llamarada', 'patada_ignea', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'}, 'regigigas': {'pokedex': 486, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 110, 'vida': 220, 'ataques': ['placaje', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'ataque_rapido'}, 'regice': {'pokedex': 378, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 180, 'ataques': ['rayo_hielo', 'ventisca', 'aliento_hielo', 'puño_hielo'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'rayo_hielo', 'ataque_proyectil': 'ventisca'}, 'regirock': {'pokedex': 377, 'tipo': ['roca'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 180, 'ataques': ['lanzarrocas', 'avalancha', 'romperrocas', 'pedrada'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'lanzarrocas', 'ataque_proyectil': 'avalancha'}, 'registeel': {'pokedex': 379, 'tipo': ['acero'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 180, 'ataques': ['garra_metal', 'cabeza_hierro', 'cañon_flash', 'cola_de_hierro'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'cabeza_hierro'}, 'regieleki': {'pokedex': 894, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 180, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'}, 'regidrago': {'pokedex': 895, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 200, 'vida': 400, 'ataques': ['garra_dragon', 'pulso_dragon', 'enfado', 'cola_dragon'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'}, 'chikorita': {'pokedex': 152, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'}, 'celebi': {'pokedex': 251, 'tipo': ['psiquico', 'planta'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 100, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': False, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'}, 'arceus': {'pokedex': 493, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 120, 'vida': 240, 'ataques': ['placaje', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'ataque_rapido'}, 'arceus_beta': {'pokedex': 493, 'tipo': ['normal'], 'peso': 'placeholder', 'altura': 'placeholder', 'vida_base': 150, 'vida': 300, 'ataques': ['sentencia', 'pulso_umbrio', 'terremoto', 'rayo'], 'jugable': False, 'boss': True, 'ataque_cuerpo': 'sentencia', 'ataque_proyectil': 'pulso_umbrio'}, 'missigno': {'pokedex': 'placeholder', 'tipo': [], 'peso': 'placeholder', 'altura': 'placeholder', 'vida_base': 'placeholder', 'vida': None, 'ataques': [], 'jugable': False, 'boss': False, 'ataque_cuerpo': None, 'ataque_proyectil': None}}


    # ---------- expansion: ~60 lineas evolutivas nuevas (datos de la PokeAPI, sprites de SpriteCollab) ----------
    # movimientos basicos nuevos (pasan por las plantillas de cuerpo / proyectil de mas abajo; los ajustes en AJUSTE_MOVIMIENTOS)
    movimientos.update({
        'tijera_x': {'tipo': 'bicho', 'forma': 'cuerpo'}, 'zumbido': {'tipo': 'bicho', 'forma': 'proyectil'}, 'pin_misil': {'tipo': 'bicho', 'forma': 'proyectil'},
        'carantoña': {'tipo': 'hada', 'forma': 'cuerpo'}, 'beso_drenaje': {'tipo': 'hada', 'forma': 'cuerpo'},
        'brillo_magico': {'tipo': 'hada', 'forma': 'proyectil'}, 'fuerza_lunar': {'tipo': 'hada', 'forma': 'proyectil'},
        'vozarron': {'tipo': 'normal', 'forma': 'proyectil'}, 'filo_amargo': {'tipo': 'fuego', 'forma': 'cuerpo'},
    })
    POKEMON_NUEVOS = {
        'lillipup': {'pokedex': 506, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['mordisco', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'ataque_rapido'},
        'herdier': {'pokedex': 507, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['mordisco', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'ataque_rapido'},
        'stoutland': {'pokedex': 508, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['mordisco', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'ataque_rapido'},
        'zigzagoon': {'pokedex': 263, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 38, 'vida': 85, 'ataques': ['placaje', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'ataque_rapido'},
        'linoone': {'pokedex': 264, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 78, 'vida': 110, 'ataques': ['placaje', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'ataque_rapido'},
        'eevee': {'pokedex': 133, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['placaje', 'ataque_rapido', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'ataque_rapido'},
        'vaporeon': {'pokedex': 134, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 130, 'vida': 144, 'ataques': ['acua_jet', 'hidrobomba', 'surf', 'pistola_agua'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'acua_jet', 'ataque_proyectil': 'hidrobomba'},
        'jolteon': {'pokedex': 135, 'tipo': ['electrico'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['impactrueno', 'rayo', 'onda_thunder', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'impactrueno', 'ataque_proyectil': 'rayo'},
        'flareon': {'pokedex': 136, 'tipo': ['fuego'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['ascuas', 'llamarada', 'envite_igneo', 'patada_ignea'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'},
        'espeon': {'pokedex': 196, 'tipo': ['psiquico'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'},
        'umbreon': {'pokedex': 197, 'tipo': ['siniestro'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['mordisco', 'pulso_umbrio', 'tajo_umbral', 'finta'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pulso_umbrio'},
        'leafeon': {'pokedex': 470, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'glaceon': {'pokedex': 471, 'tipo': ['hielo'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['puño_hielo', 'rayo_hielo', 'ventisca', 'aliento_hielo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'puño_hielo', 'ataque_proyectil': 'rayo_hielo'},
        'sylveon': {'pokedex': 700, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['carantoña', 'brillo_magico', 'fuerza_lunar', 'beso_drenaje'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'carantoña', 'ataque_proyectil': 'brillo_magico'},
        'whismur': {'pokedex': 293, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 64, 'vida': 101, 'ataques': ['placaje', 'vozarron', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'vozarron'},
        'loudred': {'pokedex': 294, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 84, 'vida': 114, 'ataques': ['placaje', 'vozarron', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'vozarron'},
        'exploud': {'pokedex': 295, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 104, 'vida': 127, 'ataques': ['placaje', 'vozarron', 'golpe_cuerpo', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'vozarron'},
        'wooloo': {'pokedex': 831, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 42, 'vida': 87, 'ataques': ['placaje', 'golpe_cuerpo', 'ataque_rapido', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'golpe_cuerpo'},
        'dubwool': {'pokedex': 832, 'tipo': ['normal'], 'peso': None, 'altura': None, 'vida_base': 72, 'vida': 107, 'ataques': ['placaje', 'golpe_cuerpo', 'ataque_rapido', 'hiper_rayo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'golpe_cuerpo'},
        'charcadet': {'pokedex': 935, 'tipo': ['fuego'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['ascuas', 'llamarada', 'envite_igneo', 'patada_ignea'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'},
        'armarouge': {'pokedex': 936, 'tipo': ['fuego', 'psiquico'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['patada_ignea', 'llamarada', 'psicorrayo', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'patada_ignea', 'ataque_proyectil': 'llamarada'},
        'ceruledge': {'pokedex': 937, 'tipo': ['fuego', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['filo_amargo', 'bola_sombra', 'llamarada', 'envite_igneo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'filo_amargo', 'ataque_proyectil': 'bola_sombra'},
        'litten': {'pokedex': 725, 'tipo': ['fuego'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['ascuas', 'llamarada', 'envite_igneo', 'patada_ignea'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'},
        'torracat': {'pokedex': 726, 'tipo': ['fuego'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['ascuas', 'llamarada', 'envite_igneo', 'patada_ignea'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'llamarada'},
        'incineroar': {'pokedex': 727, 'tipo': ['fuego', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['mordisco', 'llamarada', 'envite_igneo', 'pulso_umbrio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'llamarada'},
        'growlithe_hisui': {'pokedex': 58, 'tipo': ['fuego', 'roca'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['ascuas', 'pedrada', 'llamarada', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'pedrada'},
        'arcanine_hisui': {'pokedex': 59, 'tipo': ['fuego', 'roca'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['ascuas', 'pedrada', 'llamarada', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'pedrada'},
        'shroomish': {'pokedex': 285, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['latigo_cepa', 'energia_bola', 'bomba_lodo', 'hoja_afilada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'energia_bola'},
        'breloom': {'pokedex': 286, 'tipo': ['planta', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['doble_patada', 'energia_bola', 'golpe_karate', 'hoja_afilada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'energia_bola'},
        'snivy': {'pokedex': 495, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'servine': {'pokedex': 496, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'serperior': {'pokedex': 497, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'fomantis': {'pokedex': 753, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['latigo_cepa', 'hoja_afilada', 'rayo_solar', 'energia_bola'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'lurantis': {'pokedex': 754, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['latigo_cepa', 'hoja_afilada', 'rayo_solar', 'energia_bola'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'bayleef': {'pokedex': 153, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'meganium': {'pokedex': 154, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'sprigatito': {'pokedex': 906, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'floragato': {'pokedex': 907, 'tipo': ['planta'], 'peso': None, 'altura': None, 'vida_base': 61, 'vida': 100, 'ataques': ['latigo_cepa', 'hoja_afilada', 'energia_bola', 'rayo_solar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'hoja_afilada'},
        'meowscarada': {'pokedex': 908, 'tipo': ['planta', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 76, 'vida': 109, 'ataques': ['mordisco', 'hoja_afilada', 'energia_bola', 'tajo_umbral'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'hoja_afilada'},
        'foongus': {'pokedex': 590, 'tipo': ['planta', 'veneno'], 'peso': None, 'altura': None, 'vida_base': 69, 'vida': 105, 'ataques': ['latigo_cepa', 'bomba_lodo', 'energia_bola', 'puya_nociva'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'bomba_lodo'},
        'amoonguss': {'pokedex': 591, 'tipo': ['planta', 'veneno'], 'peso': None, 'altura': None, 'vida_base': 114, 'vida': 133, 'ataques': ['latigo_cepa', 'bomba_lodo', 'energia_bola', 'puya_nociva'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'bomba_lodo'},
        'brute_bonnet': {'pokedex': 986, 'tipo': ['planta', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 111, 'vida': 132, 'ataques': ['mordisco', 'energia_bola', 'tajo_umbral', 'bomba_lodo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'energia_bola'},
        'swinub': {'pokedex': 220, 'tipo': ['hielo', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['puño_hielo', 'rayo_hielo', 'bofeton_lodo', 'ventisca'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'puño_hielo', 'ataque_proyectil': 'rayo_hielo'},
        'piloswine': {'pokedex': 221, 'tipo': ['hielo', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 124, 'ataques': ['puño_hielo', 'rayo_hielo', 'bofeton_lodo', 'ventisca'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'puño_hielo', 'ataque_proyectil': 'rayo_hielo'},
        'mamoswine': {'pokedex': 473, 'tipo': ['hielo', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 110, 'vida': 131, 'ataques': ['puño_hielo', 'terremoto', 'rayo_hielo', 'ventisca'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'puño_hielo', 'ataque_proyectil': 'terremoto'},
        'zubat': {'pokedex': 41, 'tipo': ['veneno', 'volador'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['picotazo_veneno', 'ataque_ala', 'bomba_lodo', 'tajo_aereo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'ataque_ala'},
        'golbat': {'pokedex': 42, 'tipo': ['veneno', 'volador'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['picotazo_veneno', 'ataque_ala', 'bomba_lodo', 'tajo_aereo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'ataque_ala'},
        'crobat': {'pokedex': 169, 'tipo': ['veneno', 'volador'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['picotazo_veneno', 'ataque_ala', 'bomba_lodo', 'tajo_aereo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'ataque_ala'},
        'grimer_alola': {'pokedex': 88, 'tipo': ['veneno', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 80, 'vida': 112, 'ataques': ['picotazo_veneno', 'bomba_lodo', 'puya_nociva', 'pulso_umbrio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'bomba_lodo'},
        'muk_alola': {'pokedex': 89, 'tipo': ['veneno', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 105, 'vida': 128, 'ataques': ['picotazo_veneno', 'bomba_lodo', 'puya_nociva', 'pulso_umbrio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'bomba_lodo'},
        'croagunk': {'pokedex': 453, 'tipo': ['veneno', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 48, 'vida': 91, 'ataques': ['doble_patada', 'puya_nociva', 'bomba_lodo', 'golpe_karate'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'puya_nociva'},
        'toxicroak': {'pokedex': 454, 'tipo': ['veneno', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 83, 'vida': 114, 'ataques': ['doble_patada', 'puya_nociva', 'bomba_lodo', 'golpe_karate'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'doble_patada', 'ataque_proyectil': 'puya_nociva'},
        'skrelp': {'pokedex': 690, 'tipo': ['veneno', 'agua'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['picotazo_veneno', 'bomba_lodo', 'pistola_agua', 'puya_nociva'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo_veneno', 'ataque_proyectil': 'bomba_lodo'},
        'dragalge': {'pokedex': 691, 'tipo': ['veneno', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['garra_dragon', 'bomba_lodo', 'pulso_dragon', 'puya_nociva'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'bomba_lodo'},
        'sandile': {'pokedex': 551, 'tipo': ['tierra', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['mordisco', 'bofeton_lodo', 'terremoto', 'tajo_umbral'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'bofeton_lodo'},
        'krokorok': {'pokedex': 552, 'tipo': ['tierra', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['mordisco', 'bofeton_lodo', 'terremoto', 'tajo_umbral'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'bofeton_lodo'},
        'krookodile': {'pokedex': 553, 'tipo': ['tierra', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['mordisco', 'bofeton_lodo', 'terremoto', 'tajo_umbral'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'bofeton_lodo'},
        'diglett_alola': {'pokedex': 50, 'tipo': ['tierra', 'acero'], 'peso': None, 'altura': None, 'vida_base': 10, 'vida': 67, 'ataques': ['garra_metal', 'terremoto', 'bofeton_lodo', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'terremoto'},
        'dugtrio_alola': {'pokedex': 51, 'tipo': ['tierra', 'acero'], 'peso': None, 'altura': None, 'vida_base': 35, 'vida': 83, 'ataques': ['garra_metal', 'terremoto', 'bofeton_lodo', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'terremoto'},
        'phanpy': {'pokedex': 231, 'tipo': ['tierra'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 118, 'ataques': ['placaje', 'bofeton_lodo', 'terremoto', 'golpe_cuerpo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'placaje', 'ataque_proyectil': 'bofeton_lodo'},
        'donphan': {'pokedex': 232, 'tipo': ['tierra'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 118, 'ataques': ['excavar', 'terremoto', 'bofeton_lodo', 'pedrada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'excavar', 'ataque_proyectil': 'terremoto'},
        'great_tusk': {'pokedex': 984, 'tipo': ['tierra', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 115, 'vida': 134, 'ataques': ['demolicion', 'terremoto', 'golpe_karate', 'pedrada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'demolicion', 'ataque_proyectil': 'terremoto'},
        'noibat': {'pokedex': 714, 'tipo': ['volador', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['picotazo', 'tajo_aereo', 'pulso_dragon', 'vozarron'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo', 'ataque_proyectil': 'tajo_aereo'},
        'noivern': {'pokedex': 715, 'tipo': ['volador', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['picotazo', 'tajo_aereo', 'pulso_dragon', 'vozarron'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo', 'ataque_proyectil': 'tajo_aereo'},
        'cramorant': {'pokedex': 845, 'tipo': ['volador', 'agua'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['picotazo', 'hidrobomba', 'tajo_aereo', 'surf'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'picotazo', 'ataque_proyectil': 'hidrobomba'},
        'arrokuda': {'pokedex': 846, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 41, 'vida': 87, 'ataques': ['mordisco', 'hidrobomba', 'acua_jet', 'surf'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'hidrobomba'},
        'barraskewda': {'pokedex': 847, 'tipo': ['agua'], 'peso': None, 'altura': None, 'vida_base': 61, 'vida': 100, 'ataques': ['mordisco', 'hidrobomba', 'acua_jet', 'surf'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'hidrobomba'},
        'ponyta_galar': {'pokedex': 77, 'tipo': ['psiquico'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'brillo_magico'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'},
        'rapidash_galar': {'pokedex': 78, 'tipo': ['psiquico', 'hada'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['carantoña', 'psicorrayo', 'brillo_magico', 'psiquico'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'carantoña', 'ataque_proyectil': 'psicorrayo'},
        'espurr': {'pokedex': 677, 'tipo': ['psiquico'], 'peso': None, 'altura': None, 'vida_base': 62, 'vida': 100, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'},
        'meowstic': {'pokedex': 678, 'tipo': ['psiquico'], 'peso': None, 'altura': None, 'vida_base': 74, 'vida': 108, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'},
        'ralts': {'pokedex': 280, 'tipo': ['psiquico', 'hada'], 'peso': None, 'altura': None, 'vida_base': 28, 'vida': 78, 'ataques': ['confusion', 'brillo_magico', 'psicorrayo', 'fuerza_lunar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'brillo_magico'},
        'kirlia': {'pokedex': 281, 'tipo': ['psiquico', 'hada'], 'peso': None, 'altura': None, 'vida_base': 38, 'vida': 85, 'ataques': ['confusion', 'brillo_magico', 'psicorrayo', 'fuerza_lunar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'brillo_magico'},
        'gardevoir': {'pokedex': 282, 'tipo': ['psiquico', 'hada'], 'peso': None, 'altura': None, 'vida_base': 68, 'vida': 104, 'ataques': ['confusion', 'brillo_magico', 'psicorrayo', 'fuerza_lunar'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'brillo_magico'},
        'gallade': {'pokedex': 475, 'tipo': ['psiquico', 'lucha'], 'peso': None, 'altura': None, 'vida_base': 68, 'vida': 104, 'ataques': ['demolicion', 'psicorrayo', 'golpe_karate', 'psiquico'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'demolicion', 'ataque_proyectil': 'psicorrayo'},
        'elgyem': {'pokedex': 605, 'tipo': ['psiquico'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'},
        'beheeyem': {'pokedex': 606, 'tipo': ['psiquico'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['confusion', 'psicorrayo', 'psiquico', 'premonicion'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'confusion', 'ataque_proyectil': 'psicorrayo'},
        'wimpod': {'pokedex': 767, 'tipo': ['bicho', 'agua'], 'peso': None, 'altura': None, 'vida_base': 25, 'vida': 76, 'ataques': ['tijera_x', 'zumbido', 'pistola_agua', 'hidrobomba'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'zumbido'},
        'golisopod': {'pokedex': 768, 'tipo': ['bicho', 'agua'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['tijera_x', 'zumbido', 'pistola_agua', 'hidrobomba'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'zumbido'},
        'scyther': {'pokedex': 123, 'tipo': ['bicho', 'volador'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['tijera_x', 'tajo_aereo', 'zumbido', 'ataque_ala'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'tajo_aereo'},
        'scizor': {'pokedex': 212, 'tipo': ['bicho', 'acero'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['garra_metal', 'cabeza_hierro', 'tijera_x', 'zumbido'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'cabeza_hierro'},
        'kleavor': {'pokedex': 900, 'tipo': ['bicho', 'roca'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['tijera_x', 'avalancha', 'pedrada', 'zumbido'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'avalancha'},
        'nincada': {'pokedex': 290, 'tipo': ['bicho', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 31, 'vida': 80, 'ataques': ['tijera_x', 'zumbido', 'bofeton_lodo', 'pin_misil'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'zumbido'},
        'ninjask': {'pokedex': 291, 'tipo': ['bicho', 'volador'], 'peso': None, 'altura': None, 'vida_base': 61, 'vida': 100, 'ataques': ['tijera_x', 'tajo_aereo', 'zumbido', 'pin_misil'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'tajo_aereo'},
        'shedinja': {'pokedex': 292, 'tipo': ['bicho', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 1, 'vida': 61, 'ataques': ['lenguetazo', 'zumbido', 'bola_sombra', 'pin_misil'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'zumbido'},
        'joltik': {'pokedex': 595, 'tipo': ['bicho', 'electrico'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['chispa', 'zumbido', 'rayo', 'pin_misil'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'chispa', 'ataque_proyectil': 'zumbido'},
        'galvantula': {'pokedex': 596, 'tipo': ['bicho', 'electrico'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['chispa', 'zumbido', 'rayo', 'pin_misil'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'chispa', 'ataque_proyectil': 'zumbido'},
        'sewaddle': {'pokedex': 540, 'tipo': ['bicho', 'planta'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['tijera_x', 'hoja_afilada', 'zumbido', 'energia_bola'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'hoja_afilada'},
        'swadloon': {'pokedex': 541, 'tipo': ['bicho', 'planta'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['tijera_x', 'hoja_afilada', 'zumbido', 'energia_bola'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'hoja_afilada'},
        'leavanny': {'pokedex': 542, 'tipo': ['bicho', 'planta'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['tijera_x', 'hoja_afilada', 'zumbido', 'energia_bola'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'hoja_afilada'},
        'rockruff': {'pokedex': 744, 'tipo': ['roca'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['mordisco', 'pedrada', 'avalancha', 'romperrocas'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pedrada'},
        'lycanroc': {'pokedex': 745, 'tipo': ['roca'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['mordisco', 'pedrada', 'avalancha', 'romperrocas'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pedrada'},
        'anorith': {'pokedex': 347, 'tipo': ['roca', 'bicho'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['tijera_x', 'pedrada', 'avalancha', 'zumbido'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'pedrada'},
        'armaldo': {'pokedex': 348, 'tipo': ['roca', 'bicho'], 'peso': None, 'altura': None, 'vida_base': 75, 'vida': 108, 'ataques': ['tijera_x', 'pedrada', 'avalancha', 'zumbido'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'tijera_x', 'ataque_proyectil': 'pedrada'},
        'tyrunt': {'pokedex': 696, 'tipo': ['roca', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 58, 'vida': 98, 'ataques': ['mordisco', 'pulso_dragon', 'pedrada', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pulso_dragon'},
        'tyrantrum': {'pokedex': 697, 'tipo': ['roca', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 82, 'vida': 113, 'ataques': ['mordisco', 'pulso_dragon', 'pedrada', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pulso_dragon'},
        'larvitar': {'pokedex': 246, 'tipo': ['roca', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['mordisco', 'pedrada', 'avalancha', 'terremoto'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pedrada'},
        'pupitar': {'pokedex': 247, 'tipo': ['roca', 'tierra'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['mordisco', 'pedrada', 'avalancha', 'terremoto'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pedrada'},
        'tyranitar': {'pokedex': 248, 'tipo': ['roca', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 124, 'ataques': ['mordisco', 'pedrada', 'avalancha', 'terremoto'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pedrada'},
        'iron_thorns': {'pokedex': 995, 'tipo': ['roca', 'electrico'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 124, 'ataques': ['chispa', 'avalancha', 'rayo', 'pedrada'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'chispa', 'ataque_proyectil': 'avalancha'},
        'shuppet': {'pokedex': 353, 'tipo': ['fantasma'], 'peso': None, 'altura': None, 'vida_base': 44, 'vida': 89, 'ataques': ['lenguetazo', 'bola_sombra', 'infortunio', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'bola_sombra'},
        'banette': {'pokedex': 354, 'tipo': ['fantasma'], 'peso': None, 'altura': None, 'vida_base': 64, 'vida': 101, 'ataques': ['lenguetazo', 'bola_sombra', 'infortunio', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'bola_sombra'},
        'litwick': {'pokedex': 607, 'tipo': ['fantasma', 'fuego'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['ascuas', 'bola_sombra', 'llamarada', 'infortunio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'bola_sombra'},
        'lampent': {'pokedex': 608, 'tipo': ['fantasma', 'fuego'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['ascuas', 'bola_sombra', 'llamarada', 'infortunio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'bola_sombra'},
        'chandelure': {'pokedex': 609, 'tipo': ['fantasma', 'fuego'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['ascuas', 'bola_sombra', 'llamarada', 'infortunio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'ascuas', 'ataque_proyectil': 'bola_sombra'},
        'phantump': {'pokedex': 708, 'tipo': ['fantasma', 'planta'], 'peso': None, 'altura': None, 'vida_base': 43, 'vida': 88, 'ataques': ['latigo_cepa', 'bola_sombra', 'hoja_afilada', 'infortunio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'bola_sombra'},
        'trevenant': {'pokedex': 709, 'tipo': ['fantasma', 'planta'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['latigo_cepa', 'bola_sombra', 'hoja_afilada', 'infortunio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'latigo_cepa', 'ataque_proyectil': 'bola_sombra'},
        'greavard': {'pokedex': 971, 'tipo': ['fantasma'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['mordisco', 'bola_sombra', 'infortunio', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'bola_sombra'},
        'houndstone': {'pokedex': 972, 'tipo': ['fantasma'], 'peso': None, 'altura': None, 'vida_base': 72, 'vida': 107, 'ataques': ['mordisco', 'bola_sombra', 'infortunio', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'bola_sombra'},
        'axew': {'pokedex': 610, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 46, 'vida': 90, 'ataques': ['garra_dragon', 'pulso_dragon', 'cola_dragon', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'fraxure': {'pokedex': 611, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 66, 'vida': 103, 'ataques': ['garra_dragon', 'pulso_dragon', 'cola_dragon', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'haxorus': {'pokedex': 612, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 76, 'vida': 109, 'ataques': ['garra_dragon', 'pulso_dragon', 'cola_dragon', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'bagon': {'pokedex': 371, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['garra_dragon', 'pulso_dragon', 'cola_dragon', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'shelgon': {'pokedex': 372, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['garra_dragon', 'pulso_dragon', 'cola_dragon', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'salamence': {'pokedex': 373, 'tipo': ['dragon', 'volador'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['garra_dragon', 'pulso_dragon', 'tajo_aereo', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'roaring_moon': {'pokedex': 1005, 'tipo': ['dragon', 'siniestro'], 'peso': None, 'altura': None, 'vida_base': 105, 'vida': 128, 'ataques': ['garra_dragon', 'tajo_umbral', 'pulso_dragon', 'pulso_umbrio'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'tajo_umbral'},
        'dreepy': {'pokedex': 885, 'tipo': ['dragon', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 28, 'vida': 78, 'ataques': ['lenguetazo', 'pulso_dragon', 'bola_sombra', 'cola_dragon'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'pulso_dragon'},
        'drakloak': {'pokedex': 886, 'tipo': ['dragon', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 68, 'vida': 104, 'ataques': ['lenguetazo', 'pulso_dragon', 'bola_sombra', 'cola_dragon'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'pulso_dragon'},
        'dragapult': {'pokedex': 887, 'tipo': ['dragon', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 88, 'vida': 117, 'ataques': ['lenguetazo', 'pulso_dragon', 'bola_sombra', 'cola_dragon'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'pulso_dragon'},
        'druddigon': {'pokedex': 621, 'tipo': ['dragon'], 'peso': None, 'altura': None, 'vida_base': 77, 'vida': 110, 'ataques': ['garra_dragon', 'pulso_dragon', 'cola_dragon', 'enfado'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_dragon', 'ataque_proyectil': 'pulso_dragon'},
        'zorua': {'pokedex': 570, 'tipo': ['siniestro'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['mordisco', 'pulso_umbrio', 'tajo_umbral', 'finta'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pulso_umbrio'},
        'zoroark': {'pokedex': 571, 'tipo': ['siniestro'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['mordisco', 'pulso_umbrio', 'tajo_umbral', 'finta'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'pulso_umbrio'},
        'zorua_hisui': {'pokedex': 570, 'tipo': ['normal', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 35, 'vida': 83, 'ataques': ['lenguetazo', 'bola_sombra', 'infortunio', 'golpe_cuerpo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'bola_sombra'},
        'zoroark_hisui': {'pokedex': 571, 'tipo': ['normal', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 55, 'vida': 96, 'ataques': ['lenguetazo', 'bola_sombra', 'infortunio', 'golpe_cuerpo'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'lenguetazo', 'ataque_proyectil': 'bola_sombra'},
        'pawniard': {'pokedex': 624, 'tipo': ['siniestro', 'acero'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['garra_metal', 'tajo_umbral', 'pulso_umbrio', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'tajo_umbral'},
        'bisharp': {'pokedex': 625, 'tipo': ['siniestro', 'acero'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['garra_metal', 'tajo_umbral', 'pulso_umbrio', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'tajo_umbral'},
        'kingambit': {'pokedex': 983, 'tipo': ['siniestro', 'acero'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 124, 'ataques': ['garra_metal', 'tajo_umbral', 'pulso_umbrio', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'tajo_umbral'},
        'impidimp': {'pokedex': 859, 'tipo': ['siniestro', 'hada'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['mordisco', 'brillo_magico', 'pulso_umbrio', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'brillo_magico'},
        'morgrem': {'pokedex': 860, 'tipo': ['siniestro', 'hada'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['mordisco', 'brillo_magico', 'pulso_umbrio', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'brillo_magico'},
        'grimmsnarl': {'pokedex': 861, 'tipo': ['siniestro', 'hada'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['mordisco', 'brillo_magico', 'pulso_umbrio', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'brillo_magico'},
        'mawile': {'pokedex': 303, 'tipo': ['acero', 'hada'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['mordisco', 'brillo_magico', 'cabeza_hierro', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'mordisco', 'ataque_proyectil': 'brillo_magico'},
        'honedge': {'pokedex': 679, 'tipo': ['acero', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 45, 'vida': 89, 'ataques': ['garra_metal', 'bola_sombra', 'cabeza_hierro', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'bola_sombra'},
        'doublade': {'pokedex': 680, 'tipo': ['acero', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 59, 'vida': 98, 'ataques': ['garra_metal', 'bola_sombra', 'cabeza_hierro', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'bola_sombra'},
        'aegislash': {'pokedex': 681, 'tipo': ['acero', 'fantasma'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['garra_metal', 'bola_sombra', 'cabeza_hierro', 'garra_umbria'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'bola_sombra'},
        'klink': {'pokedex': 599, 'tipo': ['acero'], 'peso': None, 'altura': None, 'vida_base': 40, 'vida': 86, 'ataques': ['garra_metal', 'cañon_flash', 'cabeza_hierro', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'cañon_flash'},
        'klang': {'pokedex': 600, 'tipo': ['acero'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['garra_metal', 'cañon_flash', 'cabeza_hierro', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'cañon_flash'},
        'klinklang': {'pokedex': 601, 'tipo': ['acero'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['garra_metal', 'cañon_flash', 'cabeza_hierro', 'chispa'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'cañon_flash'},
        'aron': {'pokedex': 304, 'tipo': ['acero', 'roca'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['garra_metal', 'pedrada', 'cabeza_hierro', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'pedrada'},
        'lairon': {'pokedex': 305, 'tipo': ['acero', 'roca'], 'peso': None, 'altura': None, 'vida_base': 60, 'vida': 99, 'ataques': ['garra_metal', 'pedrada', 'cabeza_hierro', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'pedrada'},
        'aggron': {'pokedex': 306, 'tipo': ['acero', 'roca'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['garra_metal', 'pedrada', 'cabeza_hierro', 'avalancha'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'pedrada'},
        'cleffa': {'pokedex': 173, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['carantoña', 'fuerza_lunar', 'brillo_magico', 'beso_drenaje'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'carantoña', 'ataque_proyectil': 'fuerza_lunar'},
        'clefairy': {'pokedex': 35, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 70, 'vida': 105, 'ataques': ['carantoña', 'fuerza_lunar', 'brillo_magico', 'beso_drenaje'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'carantoña', 'ataque_proyectil': 'fuerza_lunar'},
        'clefable': {'pokedex': 36, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 95, 'vida': 121, 'ataques': ['carantoña', 'fuerza_lunar', 'brillo_magico', 'beso_drenaje'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'carantoña', 'ataque_proyectil': 'fuerza_lunar'},
        'tinkatink': {'pokedex': 957, 'tipo': ['hada', 'acero'], 'peso': None, 'altura': None, 'vida_base': 50, 'vida': 92, 'ataques': ['garra_metal', 'brillo_magico', 'carantoña', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'brillo_magico'},
        'tinkatuff': {'pokedex': 958, 'tipo': ['hada', 'acero'], 'peso': None, 'altura': None, 'vida_base': 65, 'vida': 102, 'ataques': ['garra_metal', 'brillo_magico', 'carantoña', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'brillo_magico'},
        'tinkaton': {'pokedex': 959, 'tipo': ['hada', 'acero'], 'peso': None, 'altura': None, 'vida_base': 85, 'vida': 115, 'ataques': ['garra_metal', 'brillo_magico', 'carantoña', 'cabeza_hierro'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'brillo_magico'},
        'flabebe': {'pokedex': 669, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 44, 'vida': 89, 'ataques': ['beso_drenaje', 'fuerza_lunar', 'brillo_magico', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'beso_drenaje', 'ataque_proyectil': 'fuerza_lunar'},
        'floette': {'pokedex': 670, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 54, 'vida': 95, 'ataques': ['beso_drenaje', 'fuerza_lunar', 'brillo_magico', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'beso_drenaje', 'ataque_proyectil': 'fuerza_lunar'},
        'florges': {'pokedex': 671, 'tipo': ['hada'], 'peso': None, 'altura': None, 'vida_base': 78, 'vida': 110, 'ataques': ['beso_drenaje', 'fuerza_lunar', 'brillo_magico', 'carantoña'], 'jugable': True, 'boss': False, 'ataque_cuerpo': 'beso_drenaje', 'ataque_proyectil': 'fuerza_lunar'},
    }
    pokemones.update(POKEMON_NUEVOS)
    # formas origen del trio de la creacion (sprites de SpriteCollab: <dex>/0001). Por ahora son jefes cargados: todavia no aparecen en ninguna era
    pokemones.update({
        'dialga_origen': {'pokedex': 483, 'tipo': ['acero', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 100, 'vida': 200,
                          'ataques': ['garra_metal', 'pulso_dragon', 'cabeza_hierro', 'garra_dragon'], 'jugable': False, 'boss': True,
                          'ataque_cuerpo': 'garra_metal', 'ataque_proyectil': 'pulso_dragon'},
        'palkia_origen': {'pokedex': 484, 'tipo': ['agua', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 90, 'vida': 180,
                          'ataques': ['acua_jet', 'hidrobomba', 'garra_dragon', 'pulso_dragon'], 'jugable': False, 'boss': True,
                          'ataque_cuerpo': 'acua_jet', 'ataque_proyectil': 'hidrobomba'},
        'giratina_origen': {'pokedex': 487, 'tipo': ['fantasma', 'dragon'], 'peso': None, 'altura': None, 'vida_base': 150, 'vida': 300,
                            'ataques': ['garra_umbria', 'bola_sombra', 'garra_dragon', 'pulso_dragon'], 'jugable': False, 'boss': True,
                            'ataque_cuerpo': 'garra_umbria', 'ataque_proyectil': 'bola_sombra'},
    })


    INMUNE_MULT = 0.2
    ESCALA_TAMAÑO = 0.7

    TABLA_TIPOS = {
        'normal': {'x05': ('roca', 'acero'), 'x0': ('fantasma',)},
        'fuego': {'x2': ('planta', 'hielo', 'bicho', 'acero'), 'x05': ('fuego', 'agua', 'roca', 'dragon')},
        'agua': {'x2': ('fuego', 'tierra', 'roca'), 'x05': ('agua', 'planta', 'dragon')},
        'electrico': {'x2': ('agua', 'volador'), 'x05': ('electrico', 'planta', 'dragon'), 'x0': ('tierra',)},
        'planta': {'x2': ('agua', 'tierra', 'roca'), 'x05': ('fuego', 'planta', 'veneno', 'volador', 'bicho', 'dragon', 'acero')},
        'hielo': {'x2': ('planta', 'tierra', 'volador', 'dragon'), 'x05': ('fuego', 'agua', 'hielo', 'acero')},
        'lucha': {'x2': ('normal', 'hielo', 'roca', 'siniestro', 'acero'), 'x05': ('veneno', 'volador', 'psiquico', 'bicho', 'hada'), 'x0': ('fantasma',)},
        'veneno': {'x2': ('planta', 'hada'), 'x05': ('veneno', 'tierra', 'roca', 'fantasma'), 'x0': ('acero',)},
        'tierra': {'x2': ('fuego', 'electrico', 'veneno', 'roca', 'acero'), 'x05': ('planta', 'bicho'), 'x0': ('volador',)},
        'volador': {'x2': ('planta', 'lucha', 'bicho'), 'x05': ('electrico', 'roca', 'acero')},
        'psiquico': {'x2': ('lucha', 'veneno'), 'x05': ('psiquico', 'acero'), 'x0': ('siniestro',)},
        'bicho': {'x2': ('planta', 'psiquico', 'siniestro'), 'x05': ('fuego', 'lucha', 'veneno', 'volador', 'fantasma', 'acero', 'hada')},
        'roca': {'x2': ('fuego', 'hielo', 'volador', 'bicho'), 'x05': ('lucha', 'tierra', 'acero')},
        'fantasma': {'x2': ('psiquico', 'fantasma'), 'x05': ('siniestro',), 'x0': ('normal',)},
        'dragon': {'x2': ('dragon',), 'x05': ('acero',), 'x0': ('hada',)},
        'siniestro': {'x2': ('psiquico', 'fantasma'), 'x05': ('lucha', 'siniestro', 'hada')},
        'acero': {'x2': ('hielo', 'roca', 'hada'), 'x05': ('fuego', 'agua', 'electrico', 'acero')},
        'hada': {'x2': ('lucha', 'dragon', 'siniestro'), 'x05': ('fuego', 'veneno', 'acero')},
    }

    TIPOS_INGLES = {
        'fighting': 'lucha', 'ice': 'hielo', 'flying': 'volador', 'ground': 'tierra', 'electric': 'electrico', 'water': 'agua',
        'fire': 'fuego', 'grass': 'planta', 'poison': 'veneno', 'psychic': 'psiquico', 'bug': 'bicho', 'rock': 'roca',
        'ghost': 'fantasma', 'dark': 'siniestro', 'steel': 'acero', 'fairy': 'hada',
    }


    def normalizar_tipo(tipo):
        """Tipo en minuscula, sin tildes y en castellano ('Psíquico' o 'psychic' -> 'psiquico')."""
        t = unicodedata.normalize('NFD', str(tipo or '').lower())
        t = ''.join(c for c in t if unicodedata.category(c) != 'Mn').strip()
        return TIPOS_INGLES.get(t, t)


    def multiplicador_tipos(ataque, defensas):
        """Multiplicador de un tipo de ataque contra uno o dos tipos (x2, x0.5; la inmunidad deja un poco de daño)."""
        fila = TABLA_TIPOS.get(normalizar_tipo(ataque))
        if not fila: return 1.0
        if isinstance(defensas, str): defensas = [defensas]
        m = 1.0
        for d in defensas or []:
            d = normalizar_tipo(d)
            if d in fila.get('x2', ()): m *= 2.0
            elif d in fila.get('x05', ()): m *= 0.5
            elif d in fila.get('x0', ()): m *= INMUNE_MULT
        return m


    ROLES = {
        'tanque': {'velocidad': 3.5, 'vida': 1.35, 'daño': 0.9, 'enfriamiento': 1.15},
        'atacante': {'velocidad': 4.7, 'vida': 1.0, 'daño': 1.3, 'enfriamiento': 1.0},
        'estratega': {'velocidad': 4.3, 'vida': 1.05, 'daño': 0.95, 'enfriamiento': 0.9},
        'velocista': {'velocidad': 6.0, 'vida': 0.8, 'daño': 0.8, 'enfriamiento': 0.7},
    }

    ROL_POKEMON = {
        'lapras': 'tanque', 'sneasel': 'velocista', 'weavile': 'velocista', 'snorunt': 'estratega', 'glalie': 'tanque', 'froslass': 'estratega',
        'spheal': 'tanque', 'sealeo': 'tanque', 'walrein': 'tanque', 'vanillite': 'estratega', 'vanillish': 'estratega', 'vanilluxe': 'atacante',
        'rookidee': 'velocista', 'corvisquire': 'velocista', 'corviknight': 'tanque', 'hawlucha': 'velocista', 'natu': 'estratega', 'xatu': 'estratega',
        'drifloon': 'estratega', 'drifblim': 'estratega', 'magnemite': 'estratega', 'magneton': 'atacante', 'magnezone': 'atacante',
        'pichu': 'velocista', 'pikachu': 'velocista', 'raichu': 'atacante', 'mareep': 'estratega', 'flaaffy': 'estratega', 'ampharos': 'atacante',
        'shinx': 'velocista', 'luxio': 'atacante', 'luxray': 'atacante', 'electrike': 'velocista', 'manectric': 'velocista',
        'sandshrew': 'tanque', 'sandslash': 'atacante', 'geodude': 'tanque', 'graveler': 'tanque', 'golem': 'tanque', 'cubone': 'estratega',
        'marowak': 'atacante', 'wooper': 'tanque', 'quagsire': 'tanque', 'gible': 'atacante', 'gabite': 'atacante', 'garchomp': 'atacante',
        'golett': 'tanque', 'golurk': 'tanque', 'mankey': 'velocista', 'primeape': 'atacante', 'annihilape': 'atacante', 'machop': 'atacante',
        'machoke': 'tanque', 'machamp': 'atacante', 'torchic': 'atacante', 'combusken': 'atacante', 'blaziken': 'atacante', 'riolu': 'velocista',
        'lucario': 'atacante', 'timburr': 'tanque', 'gurdurr': 'tanque', 'conkeldurr': 'tanque', 'mudkip': 'tanque', 'marshtomp': 'tanque',
        'swampert': 'tanque', 'squirtle': 'tanque', 'wartortle': 'tanque', 'blastoise': 'tanque', 'froakie': 'velocista', 'frogadier': 'velocista',
        'greninja': 'velocista', 'mareanie': 'estratega', 'toxapex': 'tanque', 'oshawott': 'atacante', 'dewott': 'atacante', 'samurott': 'atacante',
        'clodsire': 'tanque', 'samurott_hisui': 'atacante', 'fletchling': 'velocista', 'fletchinder': 'velocista', 'talonflame': 'velocista',
        'chikorita': 'estratega',
    }
    ROL_POKEMON.update({
        'lillipup': 'velocista',
        'herdier': 'atacante',
        'stoutland': 'tanque',
        'zigzagoon': 'velocista',
        'linoone': 'velocista',
        'eevee': 'velocista',
        'vaporeon': 'tanque',
        'jolteon': 'velocista',
        'flareon': 'atacante',
        'espeon': 'estratega',
        'umbreon': 'tanque',
        'leafeon': 'atacante',
        'glaceon': 'estratega',
        'sylveon': 'estratega',
        'whismur': 'estratega',
        'loudred': 'estratega',
        'exploud': 'atacante',
        'wooloo': 'tanque',
        'dubwool': 'tanque',
        'charcadet': 'atacante',
        'armarouge': 'estratega',
        'ceruledge': 'atacante',
        'litten': 'atacante',
        'torracat': 'atacante',
        'incineroar': 'tanque',
        'growlithe_hisui': 'tanque',
        'arcanine_hisui': 'atacante',
        'shroomish': 'estratega',
        'breloom': 'atacante',
        'snivy': 'velocista',
        'servine': 'velocista',
        'serperior': 'estratega',
        'fomantis': 'atacante',
        'lurantis': 'atacante',
        'bayleef': 'estratega',
        'meganium': 'tanque',
        'sprigatito': 'velocista',
        'floragato': 'velocista',
        'meowscarada': 'velocista',
        'foongus': 'estratega',
        'amoonguss': 'tanque',
        'brute_bonnet': 'atacante',
        'swinub': 'tanque',
        'piloswine': 'tanque',
        'mamoswine': 'atacante',
        'zubat': 'velocista',
        'golbat': 'velocista',
        'crobat': 'velocista',
        'grimer_alola': 'tanque',
        'muk_alola': 'tanque',
        'croagunk': 'atacante',
        'toxicroak': 'atacante',
        'skrelp': 'estratega',
        'dragalge': 'estratega',
        'sandile': 'velocista',
        'krokorok': 'atacante',
        'krookodile': 'atacante',
        'diglett_alola': 'velocista',
        'dugtrio_alola': 'velocista',
        'phanpy': 'tanque',
        'donphan': 'tanque',
        'great_tusk': 'tanque',
        'noibat': 'velocista',
        'noivern': 'velocista',
        'cramorant': 'estratega',
        'arrokuda': 'velocista',
        'barraskewda': 'velocista',
        'ponyta_galar': 'velocista',
        'rapidash_galar': 'estratega',
        'espurr': 'estratega',
        'meowstic': 'estratega',
        'ralts': 'estratega',
        'kirlia': 'estratega',
        'gardevoir': 'estratega',
        'gallade': 'atacante',
        'elgyem': 'estratega',
        'beheeyem': 'estratega',
        'wimpod': 'velocista',
        'golisopod': 'tanque',
        'scyther': 'velocista',
        'scizor': 'atacante',
        'kleavor': 'atacante',
        'nincada': 'tanque',
        'ninjask': 'velocista',
        'shedinja': 'estratega',
        'joltik': 'velocista',
        'galvantula': 'estratega',
        'sewaddle': 'estratega',
        'swadloon': 'tanque',
        'leavanny': 'atacante',
        'rockruff': 'velocista',
        'lycanroc': 'velocista',
        'anorith': 'atacante',
        'armaldo': 'tanque',
        'tyrunt': 'atacante',
        'tyrantrum': 'atacante',
        'larvitar': 'tanque',
        'pupitar': 'tanque',
        'tyranitar': 'tanque',
        'iron_thorns': 'tanque',
        'shuppet': 'estratega',
        'banette': 'atacante',
        'litwick': 'estratega',
        'lampent': 'estratega',
        'chandelure': 'atacante',
        'phantump': 'estratega',
        'trevenant': 'tanque',
        'greavard': 'tanque',
        'houndstone': 'tanque',
        'axew': 'atacante',
        'fraxure': 'atacante',
        'haxorus': 'atacante',
        'bagon': 'atacante',
        'shelgon': 'tanque',
        'salamence': 'atacante',
        'roaring_moon': 'atacante',
        'dreepy': 'velocista',
        'drakloak': 'velocista',
        'dragapult': 'velocista',
        'druddigon': 'tanque',
        'zorua': 'velocista',
        'zoroark': 'atacante',
        'zorua_hisui': 'velocista',
        'zoroark_hisui': 'atacante',
        'pawniard': 'atacante',
        'bisharp': 'atacante',
        'kingambit': 'tanque',
        'impidimp': 'estratega',
        'morgrem': 'velocista',
        'grimmsnarl': 'tanque',
        'mawile': 'tanque',
        'honedge': 'atacante',
        'doublade': 'tanque',
        'aegislash': 'tanque',
        'klink': 'tanque',
        'klang': 'tanque',
        'klinklang': 'atacante',
        'aron': 'tanque',
        'lairon': 'tanque',
        'aggron': 'tanque',
        'cleffa': 'estratega',
        'clefairy': 'estratega',
        'clefable': 'estratega',
        'tinkatink': 'atacante',
        'tinkatuff': 'atacante',
        'tinkaton': 'atacante',
        'flabebe': 'estratega',
        'floette': 'estratega',
        'florges': 'estratega',
    })

    FORMA_HITBOX = {
        'lapras': (1.0, 0.8), 'swampert': (1.0, 0.8), 'walrein': (1.0, 0.85), 'golem': (1.0, 0.85), 'glalie': (1.0, 0.9), 'drifblim': (0.9, 1.0),
        'machamp': (0.85, 1.0), 'xatu': (0.7, 1.0), 'garchomp': (0.85, 1.0), 'corviknight': (1.0, 0.9), 'talonflame': (1.0, 0.9),
        'quagsire': (0.95, 1.0), 'conkeldurr': (0.95, 1.0), 'luxray': (1.0, 0.85), 'manectric': (1.0, 0.85), 'blastoise': (0.95, 1.0),
        'annihilape': (0.85, 1.0), 'lucario': (0.75, 1.0), 'blaziken': (0.75, 1.0), 'greninja': (0.8, 1.0), 'toxapex': (1.0, 0.8),
    }

    _oficiales = {}
    _ruta_oficiales = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos_pokeapi.json')
    if os.path.isfile(_ruta_oficiales):
        try:
            with open(_ruta_oficiales, encoding='utf-8') as _f: _oficiales = json.load(_f)
        except (OSError, ValueError): _oficiales = {}
    for _n, _o in _oficiales.items():
        if _n in pokemones:
            if pokemones[_n].get('altura') is None: pokemones[_n]['altura'] = _o.get('altura')
            if pokemones[_n].get('peso') is None: pokemones[_n]['peso'] = _o.get('peso')
            pokemones[_n]['stats_base'] = _o.get('stats')

    # ---------- balance de los movimientos basicos ----------
    # Muchos basicos tenian datos de relleno (16 de daño, tipo equivocado) o un proyectil en la casilla de cuerpo a cuerpo
    # (Snorunt pegaba con Rayo Hielo x1.6 desde lejos). Cada basico queda en una de dos plantillas y se corrigen los tipos.
    CUERPO_BASE = {'forma': 'cuerpo', 'daño': 19, 'distancia': 66, 'area': 36, 'velocidad': 0, 'enfriamiento': 450, 'retroceso': 30, 'efecto': None}
    PROYECTIL_BASE = {'forma': 'proyectil', 'daño': 24, 'distancia': 360, 'area': 15, 'velocidad': 9, 'enfriamiento': 780, 'retroceso': 10, 'efecto': None}
    QUEMA, PARALIZA, FRENA = ({'tipo': 'quemar', 'duracion': 2200, 'probabilidad': 15}, {'tipo': 'paralizar', 'duracion': 1300, 'probabilidad': 15},
                              {'tipo': 'ralentizar', 'duracion': 1800, 'probabilidad': 25})
    AJUSTE_MOVIMIENTOS = {
        # cuerpo a cuerpo
        'demolicion': {'daño': 22}, 'patada_ignea': {'daño': 22, 'efecto': QUEMA}, 'chispa': {'daño': 20, 'efecto': PARALIZA}, 'acua_jet': {'daño': 20},
        'garra_dragon': {'daño': 22}, 'puño_hielo': {'daño': 20, 'efecto': FRENA}, 'pistola_agua': {'daño': 18}, 'mordisco': {'daño': 20},
        'picotazo': {'daño': 18}, 'doble_patada': {'daño': 20}, 'confusion': {'daño': 18}, 'lenguetazo': {'daño': 18, 'efecto': PARALIZA},
        'impactrueno': {'daño': 18, 'efecto': PARALIZA}, 'excavar': {'daño': 20}, 'lanzarrocas': {'daño': 20}, 'ascuas': {'daño': 18, 'efecto': QUEMA},
        'picotazo_veneno': {'tipo': 'veneno', 'daño': 18}, 'placaje': {'daño': 18}, 'garra_metal': {'daño': 20}, 'latigo_cepa': {'daño': 18},
        # a distancia
        'aura_esfera': {'daño': 26}, 'llamarada': {'daño': 28, 'enfriamiento': 850, 'efecto': {'tipo': 'quemar', 'duracion': 2500, 'probabilidad': 25}},
        'rayo': {'daño': 26, 'efecto': {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 20}}, 'hidrobomba': {'daño': 30, 'enfriamiento': 900},
        'pulso_dragon': {'daño': 26}, 'rayo_hielo': {'daño': 26, 'efecto': {'tipo': 'ralentizar', 'duracion': 2200, 'probabilidad': 35}},
        'psicorrayo': {'tipo': 'psiquico'}, 'avalancha': {'tipo': 'roca', 'daño': 26}, 'bomba_lodo': {'tipo': 'veneno', 'daño': 26},
        'hiper_rayo': {'tipo': 'normal', 'daño': 32, 'enfriamiento': 1000}, 'rayo_solar': {'tipo': 'planta', 'daño': 30, 'enfriamiento': 950},
        'terremoto': {'daño': 26}, 'hoja_afilada': {'daño': 24},
        # basicos nuevos de la expansion
        'tijera_x': {'daño': 20}, 'carantoña': {'daño': 20}, 'beso_drenaje': {'daño': 16, 'drena': 0.5}, 'filo_amargo': {'daño': 20, 'drena': 0.25},
        'zumbido': {'daño': 24}, 'pin_misil': {'daño': 11, 'cantidad': 3, 'abanico': 14, 'enfriamiento': 820},
        'brillo_magico': {'daño': 24}, 'fuerza_lunar': {'daño': 28, 'enfriamiento': 900}, 'vozarron': {'daño': 22, 'atraviesa': True},
    }
    for _n, _mov in movimientos.items():
        if _n == 'sentencia': continue
        plantilla = CUERPO_BASE if _mov['forma'] == 'cuerpo' else PROYECTIL_BASE
        _nuevo = dict(plantilla, tipo=_mov['tipo'])
        if _mov['forma'] == 'proyectil' and _mov.get('efecto') and _mov['efecto'].get('tipo') == 'empujar': _nuevo['efecto'] = _mov['efecto']
        _nuevo.update(AJUSTE_MOVIMIENTOS.get(_n, {}))
        movimientos[_n] = _nuevo
    # los que tenian un proyectil como golpe cuerpo a cuerpo
    for _n in ('snorunt', 'glalie', 'vanillite', 'vanillish', 'vanilluxe'):
        if _n in pokemones: pokemones[_n].update({'ataque_cuerpo': 'puño_hielo', 'ataque_proyectil': 'rayo_hielo'})
    for _n, _d in pokemones.items():
        if movimientos.get(_d.get('ataque_cuerpo'), {}).get('forma') != 'cuerpo' and _d.get('jugable') and not _d.get('boss'):
            _d['ataque_cuerpo'] = next((a for a in _d.get('ataques', []) if movimientos.get(a, {}).get('forma') == 'cuerpo'), 'placaje')


    def fuerza_especie(nombre):
        """Las especies mas fuertes (evoluciones finales) pegan un poco mas: 1.0 con 300 de stats base totales, hasta x1.25 con 600."""
        stats = (_oficiales.get(nombre) or {}).get('stats') or {}
        total = sum(stats.values()) if stats else 400
        return round(max(0.92, min(1.25, 1 + (total - 300) / 1200)), 3)


    JUGABLES = [n for n, d in pokemones.items() if d.get('jugable') and not d.get('boss') and n in ROL_POKEMON]

    DASH_TIPO = {
        'electrico': 'placaje_electrico', 'agua': 'cascada', 'volador': 'pajaro_osado', 'lucha': 'patada_salto_alta', 'tierra': 'taladradora',
        'hielo': 'esquirla_helada', 'fuego': 'rueda_fuego', 'dragon': 'carga_dragon', 'siniestro': 'persecucion', 'acero': 'puño_bala',
        'psiquico': 'cabezazo_zen', 'roca': 'rodar', 'fantasma': 'sombra_vil',
    }
    DASH_DEFECTO = 'velocidad_extrema'

    ESPECIALES = {
        'defensa_ferrea': {'tipo': 'acero', 'forma': 'buff', 'buffs': {'defensa': 0.6}, 'duracion': 4500, 'enfriamiento': 12000},
        'danza_espada': {'tipo': 'normal', 'forma': 'buff', 'buffs': {'daño': 1.4}, 'duracion': 5000, 'enfriamiento': 13000},
        'agilidad': {'tipo': 'psiquico', 'forma': 'buff', 'buffs': {'velocidad': 1.4, 'enfriamiento': 0.85}, 'duracion': 5000, 'enfriamiento': 11000},
        'paz_mental': {'tipo': 'psiquico', 'forma': 'buff', 'buffs': {'daño': 1.25, 'defensa': 0.85}, 'duracion': 6000, 'enfriamiento': 14000},
        'recuperacion': {'tipo': 'normal', 'forma': 'curar', 'porcentaje': 20, 'enfriamiento': 18000},
        'hipnosis': {'tipo': 'psiquico', 'forma': 'area', 'daño': 0, 'area': 160, 'retroceso': 0, 'efecto': {'tipo': 'dormir', 'duracion': 2600, 'probabilidad': 100}, 'enfriamiento': 10000},
        'onda_trueno': {'tipo': 'electrico', 'forma': 'area', 'daño': 6, 'area': 170, 'retroceso': 0, 'efecto': {'tipo': 'paralizar', 'duracion': 2200, 'probabilidad': 100}, 'enfriamiento': 9000},
        'viento_hielo': {'tipo': 'hielo', 'forma': 'area', 'daño': 10, 'area': 190, 'retroceso': 0, 'efecto': {'tipo': 'ralentizar', 'duracion': 3500, 'probabilidad': 100}, 'enfriamiento': 8000},
    }
    for _tipo, _nombre in DASH_TIPO.items():
        ESPECIALES[_nombre] = {'tipo': _tipo, 'forma': 'embestida', 'daño': 24, 'distancia': 190, 'area': 22, 'velocidad': 15, 'retroceso': 20, 'efecto': None, 'enfriamiento': 3500}
    ESPECIALES[DASH_DEFECTO] = {'tipo': 'normal', 'forma': 'embestida', 'daño': 22, 'distancia': 200, 'area': 22, 'velocidad': 16, 'retroceso': 20, 'efecto': None, 'enfriamiento': 3500}

    ESTADO_TIPO = {'electrico': 'onda_trueno', 'hielo': 'viento_hielo'}


    def buscar_movimiento(nombre):
        """Datos de un movimiento (especiales primero, despues los normales). None si no existe."""
        if nombre in ESPECIALES: return ESPECIALES[nombre]
        return movimientos.get(nombre)


    def _potenciado(nombre):
        """Version fuerte de un movimiento para el especial de los atacantes: mas daño, area y alcance, y atraviesa."""
        base = dict(movimientos[nombre])
        base['daño'] = round(base['daño'] * 1.6)
        base['area'] = round(base['area'] * 1.4)
        base['distancia'] = round(base['distancia'] * 1.2)
        base['enfriamiento'] = 3500
        base['atraviesa'] = True
        return base


    def _especiales_de(nombre, rol, tipos):
        """Los 2 especiales segun el rol: atacante (potenciado + danza espada), tanque (defensa + onda),
        estratega (estado + cura) y velocista (embestida de su tipo + agilidad)."""
        datos = pokemones[nombre]
        basicos = (datos.get('ataque_cuerpo'), datos.get('ataque_proyectil'))
        propios = [a for a in datos.get('ataques', []) if a in movimientos]
        libres = [a for a in propios if a not in basicos]
        tipo = tipos[0] if tipos else 'normal'
        if rol == 'atacante':
            proy = [a for a in libres if movimientos[a]['forma'] == 'proyectil'] or [a for a in propios if movimientos[a]['forma'] == 'proyectil']
            primero = proy[0] if proy else None
            return [('fuerza_' + primero, _potenciado(primero)) if primero else ('danza_espada', ESPECIALES['danza_espada']), ('danza_espada', ESPECIALES['danza_espada'])]
        if rol == 'tanque':
            fuente = (libres or propios or [None])[0]
            if fuente:
                area = dict(movimientos[fuente]); area.update({'forma': 'area', 'daño': round(area['daño'] * 1.4), 'area': 120, 'retroceso': 45, 'enfriamiento': 6000})
                segundo = ('onda_' + fuente, area)
            else:
                segundo = ('hipnosis', ESPECIALES['hipnosis'])
            return [('defensa_ferrea', ESPECIALES['defensa_ferrea']), segundo]
        if rol == 'estratega':
            estado = ESTADO_TIPO.get(tipo, 'hipnosis')
            apoyo = 'paz_mental' if 'psiquico' in tipos else 'recuperacion'
            return [(estado, ESPECIALES[estado]), (apoyo, ESPECIALES[apoyo])]
        dash = DASH_TIPO.get(tipo, DASH_DEFECTO)
        return [(dash, ESPECIALES[dash]), ('agilidad', ESPECIALES['agilidad'])]


    SINERGIAS = {'daño': 'más daño', 'defensa': 'menos daño recibido', 'velocidad': 'más velocidad', 'enfriamiento': 'recargas más rápidas',
                 'energia': 'la energía vuelve más rápido'}
    SINERGIA_ROL = {'atacante': 'daño', 'tanque': 'defensa', 'velocista': 'velocidad', 'estratega': 'enfriamiento'}


    def sinergia_de(nombre, elegida=None):
        """Pasiva que da el pokemon desde la banca: la que elegiste en su ficha o, si no elegiste, la de su rol.
        Mas fuerte cuanto mas vida base tiene (5% a 10%; la de energia vale el triple porque se nota menos)."""
        d = pokemones[nombre]
        fuerza = 0.05 + 0.05 * max(0.0, min(1.0, (float(d.get('vida_base') or 60) - 40) / 70.0))
        clave = elegida if elegida in SINERGIAS else SINERGIA_ROL.get(ROL_POKEMON.get(nombre))
        if clave == 'energia': fuerza *= 3
        return {clave: round(fuerza, 3)} if clave else {}


    def datos_juego(nombre):
        """Todo lo que el combate necesita de una especie: vida, velocidad, tamaño, hitbox, multiplicadores y movimientos."""
        d = pokemones[nombre]
        rol = ROL_POKEMON.get(nombre, 'atacante')
        r = ROLES[rol]
        tipos = [normalizar_tipo(t) for t in d.get('tipo', [])]
        base = float(d.get('vida_base') or 60)
        vida = max(1, round(float(d.get('vida') or 100) * r['vida']))
        velocidad = r['velocidad'] + max(-0.4, min(0.4, (70 - base) / 100.0))
        altura = d.get('altura')
        if isinstance(altura, (int, float)) and altura > 0: tamaño = round(max(34, min(110, 26 + (altura ** 0.5) * 17)))
        else: tamaño = round(34 + min(base, 150) * 0.2)
        tamaño = max(24, round(tamaño * ESCALA_TAMAÑO))
        ra, rh = FORMA_HITBOX.get(nombre, (1.0, 1.0))
        ancho = max(14, round(tamaño * 0.7 * ra))
        alto = max(14, round(tamaño * 0.7 * rh))
        return {'nombre': nombre, 'tipos': tipos, 'rol': rol, 'max_vida': vida, 'velocidad': round(velocidad, 2), 'tamaño': tamaño, 'ancho': ancho, 'alto': alto,
                'mult_daño': round(r['daño'] * fuerza_especie(nombre), 3), 'mult_enfriamiento': r['enfriamiento'], 'basicos': [d.get('ataque_cuerpo'), d.get('ataque_proyectil')],
                'especiales': _con_mecanica(nombre, _especiales_de(nombre, rol, tipos)), 'sinergia': sinergia_de(nombre)}


    def _con_mecanica(nombre, especiales):
        """Si la linea tiene un especial propio (mecanicas.py), va en la casilla R en lugar del segundo especial del rol."""
        propio = mecanicas.especial_de(nombre)
        return [especiales[0], propio] if propio else especiales


    ASIST_MEC = {
        'impacto': {'daño': 60, 'area': 110, 'alcance': 520, 'enfriamiento': 60000, 'efecto': None},
        'escudo': {'duracion': 5000, 'buffs': {'defensa': 0.25}, 'enfriamiento': 60000},
        'furia': {'duracion': 7000, 'buffs': {'daño': 1.6, 'enfriamiento': 0.7}, 'enfriamiento': 70000},
        'carrera': {'duracion': 6000, 'buffs': {'velocidad': 1.6, 'sprint': 2.0}, 'enfriamiento': 45000},
        'curar': {'porcentaje': 40, 'enfriamiento': 80000},
        'desvanecer': {'area': 160, 'alcance': 520, 'porcentaje': 60, 'porcentaje_jefe': 8, 'enfriamiento': 90000},
        'masivo': {'area': 480, 'daño': 8, 'duracion': 3500, 'enfriamiento': 55000},
    }

    ASIST_IMPACTO = {
        'electrico': ('trueno', 'thunder'), 'agua': ('hidrobomba', 'hydro-pump'), 'hielo': ('ventisca', 'blizzard'), 'lucha': ('onda_certera', 'focus-blast'),
        'tierra': ('terremoto', 'earthquake'), 'volador': ('vendaval', 'hurricane'), 'fuego': ('llamarada', 'fire-blast'), 'dragon': ('cometa_draco', 'draco-meteor'),
        'roca': ('avalancha', 'rock-slide'), 'siniestro': ('pulso_umbrio', 'dark-pulse'), 'acero': ('foco_resplandor', 'flash-cannon'),
        'fantasma': ('bola_sombra', 'shadow-ball'), 'psiquico': ('psiquico', 'psychic'), 'planta': ('rayo_solar', 'solar-beam'),
        'veneno': ('bomba_lodo', 'sludge-bomb'), 'normal': ('hiperrayo', 'hyper-beam'),
    }
    ASIST_ESCUDO = (('refugio', 'withdraw'), ('defensa_ferrea', 'iron-defense'), ('pantalla_luz', 'light-screen'), ('reflejo', 'reflect'), ('proteccion', 'protect'))
    ASIST_CARRERA = (('viento_afin', 'tailwind'), ('agilidad', 'agility'), ('velocidad_extrema', 'extreme-speed'), ('ataque_rapido', 'quick-attack'))
    ASIST_CURAR = (('recuperacion', 'recover'), ('aromaterapia', 'aromatherapy'), ('campana_cura', 'heal-bell'), ('deseo', 'wish'), ('descanso', 'rest'))
    ASIST_DESVANECER = (('memento', 'memento'), ('mismo_destino', 'destiny-bond'), ('canto_mortal', 'perish-song'), ('explosion', 'explosion'))
    ASIST_MASIVO = {
        'electrico': ('onda_trueno', 'thunder-wave', 'paralizar'), 'hielo': ('viento_hielo', 'icy-wind', 'ralentizar'),
        'agua': ('viento_hielo', 'icy-wind', 'ralentizar'), 'veneno': ('canto', 'sing', 'dormir'),
    }
    ASIST_ESPECIE = {
        'pikachu': ('impacto', ('trueno', 'thunder', 'electrico')), 'pichu': ('impacto', ('trueno', 'thunder', 'electrico')),
        'froslass': ('desvanecer', ('mismo_destino', 'destiny-bond', 'fantasma')),
    }


    def _aprende(nombre, ingles):
        """Si la especie aprende ese movimiento en los juegos (sin datos de la PokeAPI cuenta como que si)."""
        lista = _oficiales.get(nombre, {}).get('movimientos')
        return lista is None or ingles in lista


    def _elegir(nombre, candidatos):
        """El primer movimiento de la lista que la especie aprende de verdad (o el primero si no hay datos)."""
        for c in candidatos:
            if _oficiales.get(nombre, {}).get('movimientos') is not None and _aprende(nombre, c[1]): return c
        return candidatos[0]


    def asistencia_de(nombre):
        """Asistencia de un pokemon (lo que hace desde la banca con F / G) segun su rol y sus tipos."""
        rol = ROL_POKEMON.get(nombre, 'atacante')
        tipos = [normalizar_tipo(t) for t in pokemones[nombre].get('tipo', [])] or ['normal']
        if nombre in ASIST_ESPECIE:
            mec, mov = ASIST_ESPECIE[nombre]
        elif rol == 'atacante':
            mec = 'impacto'
            mov = _elegir(nombre, [ASIST_IMPACTO[t] for t in tipos if t in ASIST_IMPACTO] or [ASIST_IMPACTO['normal']])
        elif rol == 'tanque': mec, mov = 'escudo', _elegir(nombre, ASIST_ESCUDO)
        elif rol == 'velocista': mec, mov = 'carrera', _elegir(nombre, ASIST_CARRERA)
        elif tipos[0] in ('fantasma', 'psiquico') or 'fantasma' in tipos: mec, mov = 'desvanecer', _elegir(nombre, ASIST_DESVANECER)
        elif tipos[0] in ASIST_MASIVO: mec, mov = 'masivo', ASIST_MASIVO[tipos[0]]
        else: mec, mov = 'curar', _elegir(nombre, ASIST_CURAR)
        datos = dict(ASIST_MEC[mec])
        datos.update({'mecanica': mec, 'nombre': mov[0], 'ingles': mov[1], 'tipo': mov[2] if len(mov) > 2 and mec in ('impacto', 'desvanecer') else (tipos[0] if mec == 'impacto' else 'normal')})
        if mec == 'impacto' and len(mov) < 3: datos['tipo'] = next((t for t in tipos if ASIST_IMPACTO.get(t) == mov), tipos[0])
        if mec == 'masivo': datos['efecto'] = {'tipo': mov[2], 'duracion': datos['duracion'], 'probabilidad': 100}
        datos['mult_daño'] = ROLES[rol]['daño']
        return datos


    EVOLUCION_A = {
        'pichu': ['pikachu'], 'pikachu': ['raichu'], 'sneasel': ['weavile'], 'snorunt': ['glalie', 'froslass'], 'spheal': ['sealeo'], 'sealeo': ['walrein'],
        'vanillite': ['vanillish'], 'vanillish': ['vanilluxe'], 'rookidee': ['corvisquire'], 'corvisquire': ['corviknight'], 'natu': ['xatu'],
        'drifloon': ['drifblim'], 'magnemite': ['magneton'], 'magneton': ['magnezone'], 'mareep': ['flaaffy'], 'flaaffy': ['ampharos'],
        'shinx': ['luxio'], 'luxio': ['luxray'], 'electrike': ['manectric'], 'sandshrew': ['sandslash'], 'geodude': ['graveler'], 'graveler': ['golem'],
        'cubone': ['marowak'], 'wooper': ['quagsire'], 'gible': ['gabite'], 'gabite': ['garchomp'], 'golett': ['golurk'], 'mankey': ['primeape'],
        'primeape': ['annihilape'], 'machop': ['machoke'], 'machoke': ['machamp'], 'torchic': ['combusken'], 'combusken': ['blaziken'],
        'riolu': ['lucario'], 'timburr': ['gurdurr'], 'gurdurr': ['conkeldurr'], 'mudkip': ['marshtomp'], 'marshtomp': ['swampert'],
        'squirtle': ['wartortle'], 'wartortle': ['blastoise'], 'froakie': ['frogadier'], 'frogadier': ['greninja'], 'mareanie': ['toxapex'],
        'oshawott': ['dewott'], 'dewott': ['samurott'], 'fletchling': ['fletchinder'], 'fletchinder': ['talonflame'], 'chikorita': ['bayleef'],
    }
    EVOLUCION_DE_EXTRA = {'clodsire': 'wooper (forma de Paldea)', 'samurott_hisui': 'dewott (forma de Hisui)'}
    NOMBRES_STATS = (('hp', 'PS'), ('attack', 'Ataque'), ('defense', 'Defensa'), ('special-attack', 'At. Esp.'), ('special-defense', 'Def. Esp.'), ('speed', 'Velocidad'))


    def _limpiar(n):
        """Nombre con espacios en vez de guiones."""
        return str(n).replace('-', ' ').replace('_', ' ')


    def evoluciones_de(nombre):
        """(de quien evoluciona, [a quienes evoluciona]) con los datos de la PokeAPI o la tabla propia."""
        oficial = _oficiales.get(nombre, {})
        if 'evoluciona_a' in oficial or 'evoluciona_de' in oficial:
            de = oficial.get('evoluciona_de')
            return (_limpiar(de) if de else None), [_limpiar(x) for x in oficial.get('evoluciona_a', [])]
        de = EVOLUCION_DE_EXTRA.get(nombre)
        if not de:
            previos = [k for k, v in EVOLUCION_A.items() if nombre in v]
            de = previos[0] if previos else None
        return (_limpiar(de) if de else None), [_limpiar(x) for x in EVOLUCION_A.get(nombre, [])]


    def descripcion_de(nombre):
        """Texto de la pokedex (PokeAPI) o None."""
        return _oficiales.get(nombre, {}).get('descripcion')


    def stats_oficiales(nombre):
        """[(etiqueta, valor)] de los stats base oficiales, o None."""
        s = _oficiales.get(nombre, {}).get('stats')
        return [(etiqueta, s[clave]) for clave, etiqueta in NOMBRES_STATS if clave in s] if s else None


    def aprende_de(nombre):
        """Movimientos que aprende en los juegos (PokeAPI) o None."""
        lista = _oficiales.get(nombre, {}).get('movimientos')
        return [_limpiar(m) for m in lista] if lista else None


    def debilidades_de(nombre):
        """Tipos agrupados por cuanto le pegan: x4, x2, x0.5, x0.25 y x0."""
        tipos = [normalizar_tipo(t) for t in pokemones[nombre].get('tipo', [])]
        res = {'x4': [], 'x2': [], 'x05': [], 'x025': [], 'x0': []}
        for atk, fila in TABLA_TIPOS.items():
            m = 1.0
            for d in tipos:
                if d in fila.get('x0', ()): m = 0.0; break
                if d in fila.get('x2', ()): m *= 2.0
                elif d in fila.get('x05', ()): m *= 0.5
            clave = {4.0: 'x4', 2.0: 'x2', 0.5: 'x05', 0.25: 'x025', 0.0: 'x0'}.get(m)
            if clave: res[clave].append(atk)
        return res

    return SimpleNamespace(**locals())


pokemones = armar_pokemones()


# ==================== mts ====================

def armar_mts():
    """Maquinas Tecnicas: movimientos que se le enseñan a un pokemon en una de sus 4 casillas (E, Q, Shift, R).

        mts.MTS['mt_trueno']           # nombre, tipo, precio y los datos del movimiento listos para el combate
        mts.puede_aprender('pikachu', 'mt_trueno')
        mts.datos('mt_trueno')         # datos del movimiento (None si no es una MT)

    Salen de ataques.habilidades. Las que curan no estan (en este juego nada cura).
    Al usarla se gasta (salvo con el truco de MT infinitas).
    """
    _oficiales = pokemones._oficiales

    MEJORAS = {'daño': 'daño', 'velocidad': 'velocidad', 'cooldown': 'enfriamiento', 'resistencia': 'defensa'}   # nombres de ataques.py -> del combate


    def _convertir(h):
        """Pasa una habilidad de ataques.py al formato que usa el combate (forma, buffs, etc.)."""
        modo = h['modo']
        if modo in ('buff', 'escudo'):
            buffs = {MEJORAS[k]: v for k, v in (h.get('mejoras') or {}).items() if k in MEJORAS} if modo == 'buff' else {'defensa': 0.1}
            return {'tipo': h['tipo'], 'forma': 'buff', 'buffs': buffs, 'duracion': h['duracion'], 'enfriamiento': h['enfriamiento']}
        datos = {'tipo': h['tipo'], 'forma': modo, 'daño': h.get('daño', 0), 'enfriamiento': h['enfriamiento'], 'retroceso': h.get('retroceso', 0),
                 'efecto': h.get('efecto'), 'area': h.get('area', 20)}
        for clave in ('distancia', 'velocidad', 'cantidad', 'abanico', 'atraviesa'):
            if clave in h: datos[clave] = h[clave]
        return datos


    def _precio(h):
        """Precio de una MT: las de buff y escudo valen 180, las de ataque segun su daño y si tienen efecto."""
        if h['modo'] in ('buff', 'escudo'): return 180
        return 120 + round(h.get('daño', 20) * 3) + (40 if h.get('efecto') else 0)


    # MT especiales: los movimientos grandes (embestidas, areas, buffs, disparos fuertes). Tardan segundos en recargar: solo van en Shift o R
    MTS = {'mt_' + clave: {'nombre': 'MT ' + h['nombre'], 'api': h['api'], 'tipo': h['tipo'], 'precio': _precio(h), 'datos': _convertir(h), 'casillas': 'especial'}
           for clave, h in habilidades.items() if h['modo'] != 'curar'}
    # MT de combate: golpes y disparos con tiempos de ataque basico. Van en cualquier casilla (E, Q, Shift o R) y las aprenden los de su tipo
    _movs = pokemones.movimientos
    MTS.update({'mtb_' + clave: {'nombre': 'MT ' + clave.replace('_', ' ').title(), 'api': None, 'tipo': m['tipo'], 'precio': 90 + round(m['daño'] * 3),
                                 'datos': dict(m), 'casillas': 'todas'}
                for clave, m in _movs.items() if clave != 'sentencia' and m['forma'] in ('cuerpo', 'proyectil')})
    CASILLAS = ('E', 'Q', 'Shift', 'R')


    def sirve_en(clave, casilla):
        """Si la MT se puede poner en esa casilla (0 E, 1 Q, 2 Shift, 3 R): las de combate en todas, las especiales solo en Shift y R."""
        mt = MTS.get(clave)
        return bool(mt) and (mt['casillas'] == 'todas' or casilla >= 2)


    def datos(nombre):
        """Datos de combate de una MT (como un movimiento) o None si no es una MT."""
        mt = MTS.get(nombre)
        return mt['datos'] if mt else None


    def puede_aprender(pokemon, clave):
        """True si la especie aprende ese movimiento (segun la PokeAPI). Sin datos, cualquiera puede.
        Las MT de combate las aprenden los pokemon de su tipo (y los que ya lo usan); las de tipo normal, todos."""
        mt = MTS[clave]
        if mt['casillas'] == 'todas':
            tipos = [pokemones.normalizar_tipo(t) for t in (pokemones.pokemones.get(pokemon) or {}).get('tipo', [])]
            return mt['tipo'] in tipos or mt['tipo'] == 'normal' or clave[4:] in (pokemones.pokemones.get(pokemon) or {}).get('ataques', [])
        lista = (_oficiales.get(pokemon) or {}).get('movimientos')
        return lista is None or mt['api'] in lista


    def aprendibles(pokemon):
        """MT que puede aprender ese pokemon."""
        return [k for k in MTS if puede_aprender(pokemon, k)]

    return SimpleNamespace(**locals())


mts = armar_mts()


def catalogo_ataques():
    """Todos los ataques del juego por categoria: [(nombre, tipo, explicacion, numeros, quienes lo usan)]."""
    P = pokemones
    nombre_p = lambda n: n.replace('_', ' ').title()
    lista_usan = lambda usan: (', '.join(nombre_p(n) for n in sorted(usan)[:8]) + (' y ' + str(len(usan) - 8) + ' mas' if len(usan) > 8 else '')) if usan else 'nadie por ahora'
    basicos, especiales, asistencias = {}, {}, {}
    for n in P.JUGABLES:
        g = P.datos_juego(n)
        for k, mov in enumerate(g['basicos']):
            if mov: basicos.setdefault(mov, (k, set()))[1].add(n)
        for clave, dat in g['especiales']: especiales.setdefault(clave, (dat, set()))[1].add(n)
        a = P.asistencia_de(n)
        asistencias.setdefault(a['nombre'] + '|' + a['mecanica'], (a, set()))[1].add(n)
    cat = {}
    cat['Basicos'] = [(nombre_ataque(m), P.movimientos[m]['tipo'], explicar_movimiento(P.movimientos[m], k), describir_movimiento(P.movimientos[m]), lista_usan(usan))
                      for m, (k, usan) in sorted(basicos.items()) if m in P.movimientos]
    cat['Especiales'] = [(nombre_ataque(c), dat.get('tipo', 'normal'), explicar_movimiento(dat, 2), describir_movimiento(dat), lista_usan(usan))
                         for c, (dat, usan) in sorted(especiales.items())]
    cat['Asistencias'] = [(nombre_ataque(a['nombre']), a.get('tipo', 'normal'), 'Desde la banca (F / G): ' + describir_asistencia(a) + '.',
                           'espera ' + str(a['enfriamiento'] // 1000) + ' s', lista_usan(usan)) for _, (a, usan) in sorted(asistencias.items())]
    for titulo, casillas in (('MT de combate', 'todas'), ('MT especiales', 'especial')):
        cat[titulo] = [(mt['nombre'][3:], mt['tipo'], explicar_movimiento(mt['datos'], 0 if casillas == 'todas' else 2) +
                        (' Va en cualquier casilla.' if casillas == 'todas' else ' Solo va en Shift o R.'), describir_movimiento(mt['datos']),
                        lista_usan([n for n in P.JUGABLES if mts.puede_aprender(n, clave)]))
                       for clave, mt in sorted(mts.MTS.items(), key=lambda x: x[1]['nombre']) if mt['casillas'] == casillas]
    return cat


# ==================== tienda ====================

def armar_tienda():
    """Objetos de la tienda (nada cura) y lo que hacen sobre el jugador.

        j['inventario'] = tienda.inventario_nuevo()
        tienda.mult(j['inventario'], 'daño')       # multiplicador de todo lo comprado para esa clave
        tienda.nueva_sala(j['inventario'], tipo)   # descuenta las salas que les quedan a los objetos temporales
    """
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
        # equipables: van a la mochila y se le ponen a un pokemon (hasta 2 cada uno); solo cuentan mientras ese pokemon pelea
        'eter': {'nombre': 'Eter', 'precio': 120, 'color': (120, 200, 255), 'equipable': {'regen': 1.5, 'gasto': 0.75}, 'desc': 'la energia vuelve 50% mas rapido y correr y esquivar gastan 25% menos'},
        'cinta_fuerte': {'nombre': 'Cinta Fuerte', 'precio': 200, 'color': (230, 200, 60), 'equipable': {'daño': 1.15}, 'desc': '+15% de daño'},
        'garra_rapida': {'nombre': 'Garra Rapida', 'precio': 180, 'color': (200, 200, 200), 'equipable': {'enfriamiento': 0.88}, 'desc': 'recargas 12% mas rapidas'},
        'polvo_veloz': {'nombre': 'Polvo Veloz', 'precio': 160, 'color': (230, 230, 150), 'equipable': {'velocidad': 1.12}, 'desc': '+12% de velocidad'},
        'chaleco_asalto': {'nombre': 'Chaleco Asalto', 'precio': 200, 'color': (70, 70, 140), 'equipable': {'defensa': 0.85}, 'desc': '15% menos daño recibido'},
        'cinturon_focus': {'nombre': 'Cinta Focus', 'precio': 190, 'color': (230, 120, 60), 'equipable': {'parry': 1.5}, 'desc': 'la ventana de parry dura 50% mas (es mas facil acertarlo)'},
        'pluma_agil': {'nombre': 'Pluma Agil', 'precio': 170, 'color': (170, 220, 250), 'equipable': {'esquive': 1.4}, 'desc': 'el esquive dura 40% mas (mas invulnerable) y llega mas lejos'},
        # de equipo: valen para todos
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
        'polvo_plata': {'nombre': 'Polvo Plata', 'precio': 140, 'color': (200, 200, 210), 'tipo': ('bicho', 1.2)},
        'pluma_hada': {'nombre': 'Pluma Hada', 'precio': 140, 'color': (250, 160, 210), 'tipo': ('hada', 1.2)},
    }
    for _clave, _item in ITEMS.items():
        if 'tipo' in _item: _item['desc'] = '+20% de daño a los ataques de tipo ' + _item['tipo'][0]; _item['equipable'] = {}
        if 'equipable' in _item: _item['desc'] += ' (lo lleva un pokemon)'
        elif not _item.get('objeto') and not _item.get('recogible'): _item['desc'] += ' (todo el equipo)'
    MAX_EQUIPADOS = 2

    # objetos que van a la mochila: evolucion (se usan desde el menu de equipo con TAB) y las MT
    ITEMS.update({
        'piedra_trueno': {'nombre': 'Piedra Trueno', 'precio': 220, 'color': (250, 220, 40), 'objeto': True, 'desc': 'hace evolucionar a Pikachu y Magneton'},
        'piedra_alba': {'nombre': 'Piedra Alba', 'precio': 220, 'color': (120, 220, 230), 'objeto': True, 'desc': 'hace evolucionar a Snorunt en Froslass'},
        'garra_afilada': {'nombre': 'Garra Afilada', 'precio': 220, 'color': (200, 200, 220), 'objeto': True, 'desc': 'hace evolucionar a Sneasel'},
        'cordon_union': {'nombre': 'Cordon Union', 'precio': 240, 'color': (240, 140, 60), 'objeto': True,
                         'desc': 'evoluciona a los que en los juegos evolucionan por intercambio (Graveler, Machoke, Gurdurr, Scyther, Phantump)'},
        'piedra_fuego': {'nombre': 'Piedra Fuego', 'precio': 220, 'color': (240, 110, 50), 'objeto': True, 'desc': 'hace evolucionar a Eevee en Flareon y al Growlithe de Hisui'},
        'piedra_agua': {'nombre': 'Piedra Agua', 'precio': 220, 'color': (70, 130, 235), 'objeto': True, 'desc': 'hace evolucionar a Eevee en Vaporeon'},
        'piedra_hoja': {'nombre': 'Piedra Hoja', 'precio': 220, 'color': (100, 190, 80), 'objeto': True, 'desc': 'hace evolucionar a Eevee en Leafeon'},
        'piedra_hielo': {'nombre': 'Piedra Hielo', 'precio': 220, 'color': (150, 220, 255), 'objeto': True, 'desc': 'hace evolucionar a Eevee en Glaceon'},
        'piedra_solar': {'nombre': 'Piedra Solar', 'precio': 220, 'color': (250, 160, 40), 'objeto': True, 'desc': 'hace evolucionar a Eevee en Espeon'},
        'piedra_lunar': {'nombre': 'Piedra Lunar', 'precio': 220, 'color': (120, 110, 160), 'objeto': True, 'desc': 'hace evolucionar a Eevee en Umbreon y a Clefairy'},
        'piedra_dia': {'nombre': 'Piedra Dia', 'precio': 220, 'color': (240, 240, 200), 'objeto': True, 'desc': 'hace evolucionar a Floette'},
        'piedra_noche': {'nombre': 'Piedra Noche', 'precio': 220, 'color': (60, 50, 90), 'objeto': True, 'desc': 'hace evolucionar a Lampent y a Doublade'},
        'armadura_auspiciosa': {'nombre': 'Armadura Auspiciosa', 'precio': 240, 'color': (240, 180, 60), 'objeto': True, 'desc': 'hace evolucionar a Charcadet en Armarouge'},
        'armadura_maldita': {'nombre': 'Armadura Maldita', 'precio': 240, 'color': (110, 70, 160), 'objeto': True, 'desc': 'hace evolucionar a Charcadet en Ceruledge'},
        'mineral_negro': {'nombre': 'Mineral Negro', 'precio': 240, 'color': (60, 60, 60), 'objeto': True, 'desc': 'hace evolucionar a Scyther en Kleavor'},
        'cristal_paradoja': {'nombre': 'Cristal Paradoja', 'precio': 400, 'color': (190, 120, 255), 'objeto': True,
                             'desc': 'un pedazo del tiempo roto: transforma a Donphan, Salamence y Tyranitar en su forma paradoja'},
        'llave_tesoro': {'nombre': 'Llave del Tesoro', 'precio': 130, 'color': (200, 200, 220), 'objeto': True,
                         'desc': 'abre una puerta con candado: detras hay una sala del tesoro con premios para elegir'},
        'caramelo_raro': {'nombre': 'Caramelo Raro', 'precio': 260, 'color': (120, 140, 255), 'objeto': True,
                          'desc': 'sube un nivel al pokemon que elijas (desde su ficha)'},
        # mejoras de las salas del tesoro: gratis (se elige una de tres) y para siempre, para todo el equipo
        'proteina': {'nombre': 'Proteina', 'precio': 0, 'color': (230, 90, 70), 'mejora': True, 'permanente': {'daño': 1.08}, 'desc': '+8% de daño para todo el equipo, para siempre'},
        'hierro': {'nombre': 'Hierro', 'precio': 0, 'color': (230, 210, 80), 'mejora': True, 'permanente': {'defensa': 0.92}, 'desc': '8% menos daño recibido para todo el equipo, para siempre'},
        'carburante': {'nombre': 'Carburante', 'precio': 0, 'color': (90, 200, 230), 'mejora': True, 'permanente': {'velocidad': 1.06}, 'desc': '+6% de velocidad para todo el equipo, para siempre'},
        'calcio': {'nombre': 'Calcio', 'precio': 0, 'color': (240, 150, 70), 'mejora': True, 'permanente': {'enfriamiento': 0.92}, 'desc': 'recargas 8% mas rapidas para todo el equipo, para siempre'},
        'zinc': {'nombre': 'Zinc', 'precio': 0, 'color': (220, 190, 70), 'mejora': True, 'permanente': {'regen': 1.25, 'parry': 1.1}, 'desc': 'la energia vuelve 25% mas rapido y el parry dura 10% mas (todo el equipo)'},
        'mas_ps': {'nombre': 'Mas PS', 'precio': 0, 'color': (90, 200, 120), 'mejora': True, 'cura_equipo': 0.5, 'desc': 'todo el equipo se cura la mitad de su vida (y revive a los debilitados con un 25%)'},
        'baya_oran': {'nombre': 'Baya Oran', 'precio': 0, 'color': (60, 120, 230), 'recogible': True,
                      'desc': 'cura el 15% de la vida del que pelea al agarrarla (la sueltan cosas rotas y salas con buena nota)'},
        'lazo_amistad': {'nombre': 'Lazo Amistad', 'precio': 110, 'color': (250, 120, 170), 'temporal': ('amistad', 2.0, SALAS_X),
                         'desc': 'el doble de chance de que un pokemon quiera unirse por 3 salas'},
    })
    # ---------- curaciones (las vende Chikorita rosa; se usan desde la mochila o con la tecla de curarse) ----------
    # 'ps': cuanta vida cura ('todo' = toda), 'estados': cuales saca ('todos' = todos), 'revive': con que parte de la vida revive a un debilitado,
    # 'amargo': baja un poco la amistad (como en los juegos), 'unico': solo se puede llevar uno
    TODOS_ESTADOS = ('veneno', 'quemadura', 'paralisis', 'sueño', 'confusion', 'aturdido', 'congelado')
    CURATIVOS = {
        # bayas
        'zumo_baya': ('Zumo de Baya', 25, {'ps': 20}, (230, 120, 160)),
        'baya_aranja': ('Baya Aranja', 15, {'ps': 10}, (70, 130, 235)),
        'baya_zidra': ('Baya Zidra', 40, {'ps': 30}, (240, 220, 80)),
        'baya_zreza': ('Baya Zreza', 20, {'estados': ('paralisis',)}, (230, 60, 70)),
        'baya_atania': ('Baya Atania', 20, {'estados': ('sueño',)}, (110, 80, 200)),
        'baya_meloc': ('Baya Meloc', 20, {'estados': ('veneno',)}, (250, 170, 190)),
        'baya_safre': ('Baya Safre', 20, {'estados': ('quemadura',)}, (90, 170, 220)),
        'baya_perasi': ('Baya Perasi', 20, {'estados': ('congelado',)}, (240, 230, 150)),
        'baya_caquic': ('Baya Caquic', 20, {'estados': ('confusion', 'aturdido')}, (240, 150, 60)),
        'baya_ziuela': ('Baya Ziuela', 60, {'estados': 'todos'}, (120, 200, 90)),
        # amargos (baratos, pero al pokemon no le gustan)
        'polvo_curacion': ('Polvo Curación', 30, {'estados': 'todos', 'amargo': True}, (220, 220, 200)),
        'polvo_energia': ('Polvo Energía', 35, {'ps': 50, 'amargo': True}, (200, 210, 140)),
        'raiz_energia': ('Raíz Energía', 140, {'ps': 200, 'amargo': True}, (160, 120, 80)),
        # liquidos
        'agua_fresca': ('Agua Fresca', 55, {'ps': 50}, (140, 200, 250)),
        'refresco': ('Refresco', 65, {'ps': 60}, (250, 220, 120)),
        'limonada': ('Limonada', 85, {'ps': 80}, (250, 240, 150)),
        'leche_mumu': ('Leche Mu-mu', 110, {'ps': 100}, (245, 245, 235)),
        # remedios
        'remedio': ('Remedio', 60, {'ps': 60}, (180, 140, 220)),
        'superremedio': ('Superremedio', 100, {'ps': 100}, (150, 110, 220)),
        'hiperremedio': ('Hiperremedio', 150, {'ps': 150}, (120, 80, 210)),
        # pociones
        'pocion': ('Poción', 30, {'ps': 20}, (160, 90, 220)),
        'superpocion': ('Superpoción', 70, {'ps': 50}, (230, 140, 60)),
        'hiperpocion': ('Hiperpoción', 220, {'ps': 200}, (240, 100, 160)),
        'pocion_maxima': ('Poción Máxima', 0, {'ps': 'todo', 'unico': True}, (90, 160, 240)),   # no se vende: te la da Celebi
        # comidas que curan estados
        'galleta_lava': ('Galleta Lava', 70, {'estados': 'todos'}, (220, 90, 50)),
        'porcehelado': ('Porcehelado', 70, {'estados': 'todos'}, (200, 230, 250)),
        'crepe_luminalia': ('Crepe Luminalia', 70, {'estados': 'todos'}, (250, 200, 120)),
        'bizcocho_jubileo': ('Bizcocho Jubileo', 70, {'estados': 'todos'}, (240, 190, 140)),
        # revivir
        'hierba_revivir': ('Hierba Revivir', 120, {'revive': 0.5, 'amargo': True}, (120, 180, 80)),
        'revivir': ('Revivir', 200, {'revive': 0.5}, (250, 220, 90)),
        'maximo_revivir': ('Máximo Revivir', 400, {'revive': 1.0}, (250, 180, 60)),
    }

    def _texto_cura(c):
        """'cura 50 PS', 'saca el veneno', 'revive con la mitad de la vida'..."""
        partes = []
        if 'revive' in c: partes.append('revive a un debilitado con ' + ('toda la vida' if c['revive'] >= 1 else 'la mitad de la vida'))
        if c.get('ps') == 'todo': partes.append('cura toda la vida')
        elif c.get('ps'): partes.append('cura ' + str(c['ps']) + ' PS')
        nombres = {'veneno': 'el veneno', 'quemadura': 'la quemadura', 'paralisis': 'la parálisis', 'sueño': 'el sueño', 'confusion': 'la confusión',
                   'aturdido': 'el aturdimiento', 'congelado': 'el congelamiento'}
        if c.get('estados') == 'todos': partes.append('saca todos los estados')
        elif c.get('estados'): partes.append('saca ' + ' y '.join(nombres[e] for e in c['estados']))
        if c.get('amargo'): partes.append('es amargo: baja un poco la amistad')
        if c.get('unico'): partes.append('solo se puede llevar una y te la da Celebi')
        return ', '.join(partes)

    for _clave, (_nombre, _precio, _cura, _color) in CURATIVOS.items():
        ITEMS[_clave] = {'nombre': _nombre, 'precio': _precio, 'color': _color, 'objeto': True, 'curativo': _cura, 'desc': _texto_cura(_cura)}
    CURACIONES = tuple(k for k in CURATIVOS if ITEMS[k]['precio'] > 0)       # lo que vende Chikorita rosa

    def usar_curativo(m, clave):
        """Usa una curacion en un miembro del equipo. Devuelve (se uso, texto). No gasta nada si no hace falta."""
        c = ITEMS[clave]['curativo']
        nombre = m['nombre'].replace('_', ' ').title()
        est = m.setdefault('estados', {})
        if m['vida'] <= 0:
            if 'revive' not in c: return False, nombre + ' está debilitado: hace falta algo para revivirlo'
            m['vida'] = max(1, round(m['max_vida'] * c['revive'])); est.clear()
            texto = nombre + ' revivió'
        else:
            if 'revive' in c: return False, nombre + ' no está debilitado'
            cuales = TODOS_ESTADOS if c.get('estados') == 'todos' else (c.get('estados') or ())
            saca = [e for e in cuales if e in est]
            cura = (m['max_vida'] - m['vida']) if c.get('ps') == 'todo' else min(c.get('ps') or 0, m['max_vida'] - m['vida'])
            if not saca and cura < 1: return False, nombre + (' no tiene ese problema' if cuales and not c.get('ps') else ' tiene la vida llena')
            for e in saca: est.pop(e, None)
            m['vida'] = min(m['max_vida'], m['vida'] + cura)
            texto = nombre + (' recuperó ' + str(round(cura)) + ' PS' if cura >= 1 else ' se siente mejor')
        if c.get('amargo'): m['amistad'] = max(0, m.get('amistad', 0) - 5); texto += ' (le pareció amargo)'
        return True, texto

    for _clave, _mt in mts.MTS.items():
        ITEMS[_clave] = {'nombre': _mt['nombre'], 'precio': _mt['precio'], 'color': (90, 200, 120) if _mt['casillas'] == 'todas' else (90, 90, 200),
                         'objeto': True, 'mt': True,
                         'desc': ('MT de combate: ' if _mt['casillas'] == 'todas' else 'MT especial (solo Shift o R): ') + _mt['nombre'][3:]
                                 + ' (tipo ' + _mt['tipo'] + '). ' + describir_movimiento(_mt['datos'])}
    EVOLUCION = ('piedra_trueno', 'piedra_alba', 'garra_afilada', 'cordon_union', 'piedra_fuego', 'piedra_agua', 'piedra_hoja', 'piedra_hielo',
                 'piedra_solar', 'piedra_lunar', 'piedra_dia', 'piedra_noche', 'armadura_auspiciosa', 'armadura_maldita', 'mineral_negro', 'cristal_paradoja')

    COMUNES = ('repelente', 'superrepelente', 'maxirepelente', 'ataque_x', 'defensa_x', 'velocidad_x', 'especial_x', 'directo', 'eter', 'lazo_amistad')
    DESTACADOS = ('cinta_fuerte', 'garra_rapida', 'polvo_veloz', 'chaleco_asalto', 'amuleto_moneda', 'cinturon_focus', 'pluma_agil', 'caramelo_raro')
    EQUIPABLES = tuple(k for k, v in ITEMS.items() if 'equipable' in v)
    MEJORAS = tuple(k for k, v in ITEMS.items() if v.get('mejora'))


    def premios_tesoro(azar):
        """Los 3 premios de una sala del tesoro: dos mejoras distintas y caramelos raros."""
        return azar.sample(MEJORAS, 2) + ['caramelo_raro']
    DE_TIPO = tuple(k for k, v in ITEMS.items() if 'tipo' in v)


    def inventario_nuevo():
        """Inventario vacio de una partida nueva."""
        return {'permanente': {}, 'temporal': [], 'repelente': 0, 'tipos': {}, 'critico': [0.0, 0], 'comprados': [], 'objetos': {}, 'cinturon': []}


    CINTURON_MAX = 5     # curaciones que se pueden llevar: van en el cinturon (el cuarto de circulo de abajo a la derecha) y se usan en orden


    def es_curativo(clave):
        """Si el objeto es una curacion (va al cinturon en vez de a la mochila)."""
        return 'curativo' in ITEMS.get(clave, {})


    def migrar_cinturon(inv):
        """Partidas de antes: las curaciones estaban sueltas en la mochila. Pasan al cinturon en orden hasta llenarlo; las que no
        entran se venden solas. Devuelve cuantas monedas te devuelven por esas."""
        cinturon = inv.setdefault('cinturon', [])
        devolver = 0
        for clave in [k for k in list(inv['objetos']) if es_curativo(k)]:
            for _ in range(max(0, inv['objetos'].pop(clave))):
                if len(cinturon) < CINTURON_MAX: cinturon.append(clave)
                else: devolver += ITEMS[clave]['precio']
        return devolver


    def mult(inv, clave):
        """Multiplicador de todo lo comprado para esa clave ('daño', 'defensa', 'velocidad', 'enfriamiento', 'regen', 'gasto', 'monedas')."""
        m = inv['permanente'].get(clave, 1.0)
        for c, v, salas in inv['temporal']:
            if c == clave and salas > 0: m *= v
        return m


    def mult_tipo(inv, tipo):
        """Multiplicador de daño de ese tipo por los objetos potenciadores comprados (carbon, agua mistica...)."""
        return inv['tipos'].get(tipo, 1.0)


    def critico(inv):
        """Multiplicador de un golpe: x1.8 si sale critico."""
        prob, salas = inv['critico']
        return 1.8 if salas > 0 and random.random() < prob else 1.0


    def factor_enemigos(inv):
        """Con un repelente activo aparece el 65% de los enemigos."""
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
        if comunes: comunes[0] = 'llave_tesoro'                   # siempre hay una llave para las salas del tesoro
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


    # los 3 mostradores de la tienda (5 objetos cada uno, al azar)
    POTENCIADORES = ('ataque_x', 'defensa_x', 'velocidad_x', 'especial_x', 'directo') + DE_TIPO   # Riolu: los X y los de tipo
    EVOLUCION_TIENDA = tuple(k for k in EVOLUCION if k != 'cristal_paradoja')                     # Riolu: sin el Cristal Paradoja (lo suelta el Regi)
    MTS_TIENDA = tuple(k for k, v in ITEMS.items() if v.get('mt'))                                # Kecleon
    POR_MOSTRADOR = 5


    def surtido_mostradores(azar, vitrinas, equipo=(), necesita=()):
        """Que objeto va en cada vitrina segun su mostrador ('chikorita', 'riolu' o 'kecleon'):
            Chikorita rosa  5 curaciones distintas (vida o estados) al azar
            Riolu           3 potenciadores (Ataque X, Defensa X..., Directo o los de tipo) y 2 objetos de evolucion; si alguien del
                            equipo necesita uno para evolucionar, casi siempre esta
            Kecleon         5 MT al azar (si hay alguna que tu equipo puede aprender, al menos una de esas)"""
        necesarios = [k for k in necesita if k in EVOLUCION_TIENDA]
        evolucion = azar.sample(EVOLUCION_TIENDA, 2)
        if necesarios and azar.random() < 0.7 and not set(necesarios) & set(evolucion):
            evolucion[0] = azar.choice(necesarios)
        mts_ = azar.sample(MTS_TIENDA, min(POR_MOSTRADOR, len(MTS_TIENDA)))
        posibles = sorted({k for n in equipo for k in mts.aprendibles(n)})
        if posibles and not set(posibles) & set(mts_): mts_[-1] = azar.choice(posibles)
        listas = {'chikorita': azar.sample(CURACIONES, POR_MOSTRADOR), 'riolu': azar.sample(POTENCIADORES, 3) + evolucion, 'kecleon': mts_}
        usados = {k: 0 for k in listas}
        salida = []
        for v in vitrinas:
            lista = listas.get(v.get('mostrador'), listas['riolu'])
            salida.append(lista[usados.get(v.get('mostrador'), 0) % len(lista)])
            if v.get('mostrador') in usados: usados[v['mostrador']] += 1
        return salida


    def comprar(j, clave):
        """Intenta comprar: devuelve el texto para el cartel."""
        item, inv = ITEMS[clave], j['inventario']
        if j['monedas'] < item['precio']: return 'No te alcanza (' + str(item['precio']) + ' $)'
        cinturon = inv.setdefault('cinturon', [])
        if es_curativo(clave) and len(cinturon) >= CINTURON_MAX:
            return 'Cinturón lleno: ya llevás ' + str(CINTURON_MAX) + ' curaciones (en la mochila podés tirar alguna)'
        j['monedas'] -= item['precio']
        inv['comprados'].append(clave)
        if es_curativo(clave):                                            # las curaciones van al cinturon, al final de la fila
            cinturon.append(clave)
            return 'Compraste ' + item['nombre'] + ' (lugar ' + str(len(cinturon)) + ' del cinturón)'
        if item.get('objeto') or 'equipable' in item: inv['objetos'][clave] = inv['objetos'].get(clave, 0) + 1   # a la mochila
        if 'repelente' in item: inv['repelente'] += item['repelente']
        if 'temporal' in item: inv['temporal'].append(list(item['temporal']))
        if 'critico' in item: inv['critico'] = [item['critico'][0], inv['critico'][1] + item['critico'][1]]
        for c, v in item.get('permanente', {}).items(): inv['permanente'][c] = inv['permanente'].get(c, 1.0) * v
        if 'cura_equipo' in item:
            for m in j['equipo']:
                m['vida'] = max(m['vida'], round(m['max_vida'] * 0.25)) if m['vida'] <= 0 else min(m['max_vida'], m['vida'] + m['max_vida'] * item['cura_equipo'])
        if item.get('mejora'): return item['nombre'] + ': ' + item['desc']
        if 'equipable' in item: return 'Compraste ' + item['nombre'] + ': ponéselo a un pokemon desde su ficha'
        return 'Compraste ' + item['nombre']


    def mult_equipados(items, clave):
        """Multiplicador de los objetos que lleva el pokemon que pelea para esa clave ('daño', 'defensa', 'parry'...)."""
        m = 1.0
        for k in items or ():
            m *= ITEMS.get(k, {}).get('equipable', {}).get(clave, 1.0)
        return m


    def mult_tipo_equipados(items, tipo):
        """+20% por cada objeto de ese tipo que lleve el pokemon que pelea (Carbon para fuego...)."""
        m = 1.0
        for k in items or ():
            t = ITEMS.get(k, {}).get('tipo')
            if t and t[0] == tipo: m *= t[1]
        return m

    return SimpleNamespace(**locals())


tienda = armar_tienda()


# ==================== mundos ====================

def armar_mundos():
    """Las eras del juego (una por cada Regi), sus objetos, sus piezas armadas, el clima y el plan de salas de una partida.

        from datos import mundos
        rec = mundos.nuevo_recorrido()          # plan entero de la partida
        mundos.tipo_sala(rec)                   # 'combate', 'tienda', 'jefe', 'regi' o 'final'
        mundos.destinos_siguientes(rec, azar)   # lo que muestran las puertas de la sala actual
        mundos.avanzar(rec)                     # pasa a la sala siguiente (False si se termino el juego)

    Orden de las eras (la historia de la humanidad): Glaciacion (Regice), Edad de Piedra (Regirock), Edad de los Metales (Registeel),
    Edad Media (Regidrago), Edad Moderna (Regieleki) y al final El Origen: Regigigas y despues Arceus.
    """
    SALAS_POR_ERA = 30
    SALA_JEFE, SALA_REGI = 15, 30          # numero de sala (desde 1) del semijefe y del Regi
    TIENDA_HUECO = (5, 10)                 # la tienda sale cada 5 a 10 salas
    TIENDA_COMPENSA = 15                   # si sale pronto, la siguiente tarda mas: hueco_siguiente >= 15 - hueco_anterior
    PUERTAS_POR_SALA = ((1, 20), (2, 50), (3, 30))   # (cantidad de salidas, peso) en las salas de combate
    PROB_SEGUIR_CLIMA = 0.6                # chance de que la sala siguiente tenga el mismo clima
    PROB_TESORO = 0.4                      # chance de que una de las puertas (si hay 2 o mas) sea de una sala del tesoro
    PROB_DESAFIO = 0.2                     # chance de que una puerta de combate sea de desafio (mas enemigos, mejor premio)

    # terrenos: color, si bloquea el paso, que tipos lo cruzan igual y si frena proyectiles (solido)
    TERRENOS = {
        'suelo': {'color': None, 'bloquea': False},
        'pared': {'color': None, 'bloquea': True, 'solido': True},
        'puerta': {'color': (120, 70, 30), 'bloquea': True, 'solido': True},
        'entrada': {'color': (60, 40, 25), 'bloquea': True, 'solido': True},
        'puente': {'color': (135, 95, 55), 'bloquea': False},
        'alfombra': {'color': (150, 40, 50), 'bloquea': False},
        'agua': {'color': (40, 105, 215), 'bloquea': True, 'pasan': ('agua', 'volador')},
        'charco': {'color': (100, 155, 225), 'bloquea': False},
        'hielo': {'color': (185, 232, 250), 'bloquea': False},
        'nieve': {'color': (240, 246, 252), 'bloquea': False},
        'hierba': {'color': (55, 145, 55), 'bloquea': False},
        'fuego': {'color': (240, 110, 30), 'bloquea': False},
        'ceniza': {'color': (75, 70, 65), 'bloquea': False},
        'arena': {'color': (222, 198, 132), 'bloquea': False},
        'lodo': {'color': (105, 78, 48), 'bloquea': False},
        'lava': {'color': (225, 60, 20), 'bloquea': True, 'pasan': ('fuego', 'dragon', 'volador')},
        'roca_volcanica': {'color': (58, 48, 48), 'bloquea': False},
        'toxico': {'color': (140, 60, 175), 'bloquea': False},
        'sombra': {'color': (28, 22, 40), 'bloquea': False},
        'aceite': {'color': (38, 36, 30), 'bloquea': False},
        'cable': {'color': (245, 225, 60), 'bloquea': False},
        'corriente': {'color': (205, 240, 255), 'bloquea': False},
        'cinta_n': {'color': (95, 95, 100), 'bloquea': False}, 'cinta_s': {'color': (95, 95, 100), 'bloquea': False},
        'cinta_e': {'color': (95, 95, 100), 'bloquea': False}, 'cinta_o': {'color': (95, 95, 100), 'bloquea': False},
        # maquinas: casillas solidas que ayudan a ciertos tipos si estas cerca (ver AURAS en entorno.py)
        'cascada': {'color': (120, 195, 255), 'bloquea': True, 'solido': True, 'maquina': True},
        'cascada_helada': {'color': (210, 245, 255), 'bloquea': True, 'solido': True, 'maquina': True},
        'fogata': {'color': (255, 140, 40), 'bloquea': True, 'solido': True, 'maquina': True},
        'fogata_apagada': {'color': (80, 70, 60), 'bloquea': True, 'solido': True, 'maquina': True},
        'brasero': {'color': (255, 150, 40), 'bloquea': True, 'solido': True, 'maquina': True},
        'brasero_apagado': {'color': (90, 80, 70), 'bloquea': True, 'solido': True, 'maquina': True},
        'forja': {'color': (230, 90, 30), 'bloquea': True, 'solido': True, 'maquina': True},
        'forja_apagada': {'color': (85, 65, 55), 'bloquea': True, 'solido': True, 'maquina': True},
        'horno': {'color': (200, 70, 30), 'bloquea': True, 'solido': True, 'maquina': True, 'pegado_a_pared': True},
        'horno_apagado': {'color': (80, 60, 55), 'bloquea': True, 'solido': True, 'maquina': True},
        'generador': {'color': (250, 210, 0), 'bloquea': True, 'solido': True, 'maquina': True},
        'generador_roto': {'color': (90, 85, 60), 'bloquea': True, 'solido': True, 'maquina': True},
        'altar': {'color': (230, 120, 200), 'bloquea': True, 'solido': True, 'maquina': True},
        'cristal_dragonico': {'color': (120, 60, 250), 'bloquea': True, 'solido': True, 'maquina': True},
        'iman': {'color': (170, 175, 200), 'bloquea': True, 'solido': True, 'maquina': True},
        'monolito': {'color': (150, 130, 90), 'bloquea': True, 'solido': True, 'maquina': True},
        # lo que deja la Sentencia de Arceus en su ultima fase: no se cruza (ni volando), pero los ataques pasan por arriba
        'vacio': {'color': (12, 6, 24), 'bloquea': True},
        'escarcha': {'color': (200, 238, 255), 'bloquea': False},                 # piso que congela el rayo hielo de Regice
        'torre_dragon': {'color': (128, 128, 136), 'bloquea': False},             # techo de la torre a donde te lleva Regidrago
        'arena_movediza': {'color': (186, 150, 86), 'bloquea': False},            # la que deja Regirock alrededor de sus rocas
        'abismo': {'color': (44, 32, 68), 'bloquea': False},                      # piso de la arena de los subjefes de Arceus Beta (World Abyss)
    }

    # objetos: tamaño en pixeles, material, vida (None = no se rompe), forma y color del dibujo provisorio
    # extras: empujable (se desliza al golpearlo con lucha/psiquico o con una embestida), explota, arde (el fuego lo rompe de una),
    # al_romper (terreno que deja), cobertura (sirve para cubrirse, se reparte alrededor del centro), solido False (se pasa por encima)
    OBJETOS = {
        # era glacial
        'bloque_de_hielo': {'tam': (58, 58), 'material': 'hielo', 'vida': 45, 'color': (170, 225, 245), 'empujable': True, 'al_romper': 'charco', 'cobertura': True},
        'pino_nevado': {'tam': (64, 64), 'material': 'madera', 'vida': 90, 'forma': 'circulo', 'color': (40, 90, 70), 'arde': True, 'cobertura': True},
        'roca_nevada': {'tam': (62, 54), 'material': 'piedra', 'vida': 120, 'forma': 'circulo', 'color': (200, 210, 220), 'cobertura': True},
        'estalagmita_de_hielo': {'tam': (40, 40), 'material': 'hielo', 'vida': 35, 'forma': 'circulo', 'color': (200, 240, 255), 'al_romper': 'charco', 'cobertura': True},
        'hueso_de_mamut': {'tam': (70, 26), 'material': 'hueso', 'vida': 40, 'color': (235, 225, 200)},
        'craneo_de_mamut': {'tam': (74, 64), 'material': 'hueso', 'vida': 90, 'forma': 'circulo', 'color': (225, 215, 190), 'cobertura': True},
        'pila_de_pieles': {'tam': (48, 40), 'material': 'tela', 'vida': 15, 'color': (130, 95, 60), 'arde': True},
        # edad de piedra
        'tronco': {'tam': (64, 28), 'material': 'madera', 'vida': 30, 'color': (115, 75, 40), 'arde': True, 'empujable': True},
        'roca': {'tam': (58, 52), 'material': 'piedra', 'vida': 110, 'forma': 'circulo', 'color': (125, 120, 115), 'cobertura': True},
        'menhir': {'tam': (40, 50), 'material': 'piedra', 'vida': 180, 'color': (140, 135, 120), 'cobertura': True},
        'choza': {'tam': (100, 90), 'material': 'planta', 'vida': 70, 'forma': 'circulo', 'color': (170, 140, 80), 'arde': True},
        'lanza': {'tam': (14, 50), 'material': 'madera', 'vida': 8, 'color': (150, 110, 70), 'arde': True},
        'cesto': {'tam': (36, 36), 'material': 'planta', 'vida': 10, 'forma': 'circulo', 'color': (190, 160, 90), 'arde': True},
        'arbol': {'tam': (70, 70), 'material': 'madera', 'vida': 90, 'forma': 'circulo', 'color': (40, 110, 40), 'arde': True, 'cobertura': True},
        'arbusto': {'tam': (50, 44), 'material': 'planta', 'vida': 20, 'forma': 'circulo', 'color': (70, 140, 60), 'arde': True},
        'hueso': {'tam': (40, 20), 'material': 'hueso', 'vida': 10, 'color': (230, 225, 210), 'solido': False},
        # edad de los metales
        'yunque': {'tam': (50, 34), 'material': 'metal', 'vida': None, 'color': (70, 70, 80)},
        'armadura': {'tam': (40, 56), 'material': 'metal', 'vida': 70, 'color': (170, 140, 90), 'cobertura': True},
        'anfora': {'tam': (32, 40), 'material': 'ceramica', 'vida': 8, 'forma': 'circulo', 'color': (190, 110, 60)},
        'mesa_de_mercado': {'tam': (100, 44), 'material': 'madera', 'vida': 40, 'color': (150, 100, 55), 'arde': True},
        'columna': {'tam': (52, 52), 'material': 'piedra', 'vida': None, 'forma': 'circulo', 'color': (210, 200, 175), 'cobertura': True},
        'carro_de_bronce': {'tam': (100, 60), 'material': 'metal', 'vida': 110, 'color': (175, 120, 60)},
        'estatua_de_bronce': {'tam': (56, 66), 'material': 'metal', 'vida': 150, 'color': (180, 125, 60), 'cobertura': True},
        'lingotes': {'tam': (44, 30), 'material': 'metal', 'vida': 60, 'color': (200, 150, 70)},
        'caja': {'tam': (48, 48), 'material': 'madera', 'vida': 25, 'color': (175, 125, 70), 'empujable': True, 'arde': True, 'cobertura': True},
        'barril': {'tam': (46, 46), 'material': 'madera', 'vida': 30, 'forma': 'circulo', 'color': (140, 90, 45), 'empujable': True, 'arde': True, 'cobertura': True},
        # edad media
        'carreta': {'tam': (110, 66), 'material': 'madera', 'vida': 80, 'color': (120, 80, 40), 'arde': True, 'cobertura': True},
        'fardo_de_heno': {'tam': (60, 48), 'material': 'planta', 'vida': 18, 'color': (225, 195, 90), 'arde': True},
        'barril_de_polvora': {'tam': (44, 44), 'material': 'madera', 'vida': 12, 'forma': 'circulo', 'color': (60, 40, 30), 'explota': True},
        'estatua_de_caballero': {'tam': (58, 70), 'material': 'piedra', 'vida': 160, 'color': (150, 150, 145), 'cobertura': True},
        'lapida': {'tam': (40, 50), 'material': 'piedra', 'vida': 60, 'color': (120, 120, 120)},
        'pozo': {'tam': (76, 76), 'material': 'piedra', 'vida': None, 'forma': 'circulo', 'color': (110, 105, 100), 'cobertura': True},
        'valla': {'tam': (78, 20), 'material': 'madera', 'vida': 25, 'color': (150, 110, 60), 'arde': True},
        'estandarte': {'tam': (30, 60), 'material': 'tela', 'vida': 15, 'color': (170, 30, 40), 'arde': True},
        'escamas_de_dragon': {'tam': (46, 36), 'material': 'piedra', 'vida': 50, 'color': (110, 70, 200)},
        # edad moderna (revolucion industrial hasta hoy)
        'caja_de_carbon': {'tam': (50, 50), 'material': 'madera', 'vida': 35, 'color': (55, 45, 40), 'empujable': True, 'arde': True, 'cobertura': True},
        'barril_de_petroleo': {'tam': (44, 44), 'material': 'metal', 'vida': 20, 'forma': 'circulo', 'color': (30, 30, 30), 'explota': True, 'al_romper': 'aceite'},
        'engranaje': {'tam': (80, 80), 'material': 'metal', 'vida': 200, 'forma': 'circulo', 'color': (130, 110, 80), 'cobertura': True},
        'chatarra': {'tam': (60, 50), 'material': 'metal', 'vida': 70, 'color': (110, 90, 75), 'cobertura': True},
        'vagoneta': {'tam': (60, 50), 'material': 'metal', 'vida': 90, 'color': (90, 70, 60), 'empujable': True},
        'tuberia': {'tam': (120, 30), 'material': 'metal', 'vida': 80, 'color': (100, 110, 100)},
        'auto': {'tam': (120, 64), 'material': 'metal', 'vida': 150, 'color': (190, 40, 40), 'cobertura': True},
        'poste_de_luz': {'tam': (26, 26), 'material': 'metal', 'vida': 60, 'forma': 'circulo', 'color': (80, 80, 90)},
        'bolsa_de_basura': {'tam': (38, 38), 'material': 'basura', 'vida': 8, 'forma': 'circulo', 'color': (25, 25, 25)},
        'contenedor': {'tam': (90, 54), 'material': 'metal', 'vida': 120, 'color': (40, 110, 60), 'empujable': True, 'cobertura': True},
        'hidrante': {'tam': (30, 30), 'material': 'metal', 'vida': 40, 'forma': 'circulo', 'color': (220, 40, 30), 'al_romper': 'charco'},
        'maquina_expendedora': {'tam': (54, 44), 'material': 'vidrio', 'vida': 40, 'color': (60, 120, 210)},
        'banco_de_plaza': {'tam': (90, 30), 'material': 'madera', 'vida': 35, 'color': (130, 90, 50), 'arde': True},
        'cabina_telefonica': {'tam': (50, 50), 'material': 'vidrio', 'vida': 45, 'color': (200, 30, 30), 'cobertura': True},
        'tacho_de_basura': {'tam': (36, 36), 'material': 'basura', 'vida': 20, 'forma': 'circulo', 'color': (110, 120, 110), 'empujable': True},
        # el origen
        'pilar_de_cristal': {'tam': (50, 50), 'material': 'vidrio', 'vida': 90, 'color': (200, 150, 255), 'cobertura': True},
        'columna_rota': {'tam': (56, 46), 'material': 'piedra', 'vida': 120, 'forma': 'circulo', 'color': (190, 180, 210), 'cobertura': True},
        'estatua_de_titan': {'tam': (80, 90), 'material': 'piedra', 'vida': None, 'color': (160, 150, 190)},
        # lo que arman los Regis en su sala (se va cuando caen)
        'muro_de_hielo': {'tam': (62, 62), 'material': 'hielo_eterno', 'vida': 60, 'color': (150, 215, 245), 'al_romper': 'charco'},
        'torre_electrica': {'tam': (110, 110), 'material': 'torre', 'vida': 100000, 'color': (130, 130, 130)},
        'roca_afilada': {'tam': (96, 88), 'material': 'piedra', 'vida': 170, 'forma': 'circulo', 'color': (125, 110, 95), 'cobertura': True},
        'bloque_glaciar': {'tam': (58, 58), 'material': 'hielo', 'vida': None, 'color': (175, 230, 250), 'empujable': True},   # se empuja con E
        'roca_avalancha': {'tam': (64, 60), 'material': 'piedra', 'vida': 80, 'forma': 'circulo', 'color': (130, 112, 92)},
        'jaula_voltio': {'tam': (16, 16), 'material': 'jaula', 'vida': 100000, 'color': (255, 240, 80)},
        # tienda (no se rompen)
        'estante': {'tam': (360, 50), 'material': 'madera', 'vida': None, 'color': (110, 70, 40), 'mueble': 'estante'},
        'mostrador': {'tam': (130, 34), 'material': 'madera', 'vida': None, 'color': (140, 95, 55)},
        'kecleon': {'tam': (46, 46), 'material': 'tela', 'vida': None, 'forma': 'circulo', 'color': (120, 200, 90)},
        'chikorita_rosa': {'tam': (36, 36), 'material': 'tela', 'vida': None, 'forma': 'circulo', 'color': (240, 150, 200)},   # cura al equipo en la tienda
        'riolu': {'tam': (36, 36), 'material': 'tela', 'vida': None, 'forma': 'circulo', 'color': (90, 140, 220)},            # atiende el mostrador de la tienda
        # los 3 mostradores de la tienda: cada uno del color del pokemon que atiende ('mostrador': se dibuja la madera con la tela de ese color)
        'mostrador_chikorita': {'tam': (400, 36), 'material': 'madera', 'vida': None, 'color': (240, 150, 200), 'mostrador': True},
        'mostrador_riolu': {'tam': (360, 36), 'material': 'madera', 'vida': None, 'color': (90, 140, 220), 'mostrador': True},
        'mostrador_kecleon': {'tam': (360, 36), 'material': 'madera', 'vida': None, 'color': (120, 200, 90), 'mostrador': True, 'franja': (220, 60, 70)},
        'mesa': {'tam': (110, 50), 'material': 'madera', 'vida': None, 'color': (125, 85, 50), 'mueble': 'mesa'},
        # el refugio de Celebi (dibujados en mundo.py)
        'edificio': {'tam': (220, 150), 'material': 'piedra', 'vida': None, 'color': (200, 120, 90), 'mueble': 'edificio'},
        'casa_refugio': {'tam': (170, 120), 'material': 'madera', 'vida': None, 'color': (200, 120, 90), 'mueble': 'casa'},
        'tablon': {'tam': (64, 56), 'material': 'madera', 'vida': None, 'color': (150, 100, 55), 'mueble': 'tablon'},
        'telescopio': {'tam': (36, 40), 'material': 'piedra', 'vida': None, 'color': (120, 140, 210), 'mueble': 'telescopio'},
        'banco': {'tam': (84, 30), 'material': 'madera', 'vida': None, 'color': (170, 115, 65), 'mueble': 'banco'},
        'cartel': {'tam': (70, 60), 'material': 'madera', 'vida': None, 'color': (200, 160, 100), 'mueble': 'cartel'},
        'maceta': {'tam': (40, 40), 'material': 'planta', 'vida': None, 'forma': 'circulo', 'color': (60, 150, 70)},
        # hall (a donde volves al perder; no se rompe nada)
        'celebi': {'tam': (40, 40), 'material': 'tela', 'vida': None, 'forma': 'circulo', 'color': (150, 230, 120)},   # cuida el hall y te manda de viaje
    }

    # piezas armadas a mano (como los "chunks" de Spelunky): se rotan, se espejan y se ubican donde entren
    # '.' no importa, '_' tiene que quedar libre, el resto sale de LEYENDA_BASE o de la leyenda de la pieza (objeto, terreno o maquina)
    LEYENDA_BASE = {'~': 'agua', '"': 'hierba', ',': 'nieve', 's': 'sombra', '=': 'puente', 'c': 'charco', 'i': 'hielo', 'a': 'arena', 'k': 'cable'}
    PIEZAS = {
        # glaciacion
        'campamento helado': {'mapa': ['_p_', 'pFp', '_p_'], 'leyenda': {'F': 'fogata', 'p': 'pila_de_pieles'}},
        'esqueleto de mamut': {'mapa': ['h.h', '.C.', 'h.h'], 'leyenda': {'C': 'craneo_de_mamut', 'h': 'hueso_de_mamut'}},
        'bloques de hielo': {'mapa': ['cbc', 'b.b', 'cbc'], 'leyenda': {'b': 'bloque_de_hielo'}},
        'pinar nevado': {'mapa': [',P,', 'P,P', ',P,'], 'leyenda': {'P': 'pino_nevado'}},
        'estalagmitas': {'mapa': ['e.e', '...', 'e.e'], 'leyenda': {'e': 'estalagmita_de_hielo'}},
        # edad de piedra
        'fogata': {'mapa': ['.t.', 'tFt', '.t.'], 'leyenda': {'F': 'fogata', 't': 'tronco'}},
        'circulo de piedras': {'mapa': ['.m.m.', 'm___m', '._M_.', 'm___m', '.m.m.'], 'leyenda': {'m': 'menhir', 'M': 'monolito'}},
        'choza': {'mapa': ['lC', 'pc'], 'leyenda': {'C': 'choza', 'l': 'lanza', 'p': 'pila_de_pieles', 'c': 'cesto'}},
        'arboleda': {'mapa': ['"A"', 'A"A', '"A"'], 'leyenda': {'A': 'arbol'}},
        'rocas': {'mapa': ['R.R'], 'leyenda': {'R': 'roca'}},
        # edad de los metales
        'herreria': {'mapa': ['aFy', '_l_'], 'leyenda': {'F': 'forja', 'a': 'armadura', 'y': 'yunque', 'l': 'lingotes'}},
        'puesto de mercado': {'mapa': ['oM.o'], 'leyenda': {'M': 'mesa_de_mercado', 'o': 'anfora'}},
        'columnata': {'mapa': ['C.C.C'], 'leyenda': {'C': 'columna'}},
        'carga de bronce': {'mapa': ['xK.x'], 'leyenda': {'K': 'carro_de_bronce', 'x': 'caja'}},
        'estatua': {'mapa': ['_._', '_E_'], 'leyenda': {'E': 'estatua_de_bronce'}},
        # edad media
        'polvorin': {'mapa': ['bbB'], 'leyenda': {'b': 'barril', 'B': 'barril_de_polvora'}},
        'cementerio': {'mapa': ['l.l.l', 'sssss', 'l.l.l'], 'leyenda': {'l': 'lapida'}},
        'establo': {'mapa': ['vvv', 'f.f'], 'leyenda': {'v': 'valla', 'f': 'fardo_de_heno'}},
        'santuario del dragon': {'mapa': ['e.e', '.D.', 'e.e'], 'leyenda': {'D': 'cristal_dragonico', 'e': 'escamas_de_dragon'}},
        'campamento': {'mapa': ['b.b', '_F_'], 'leyenda': {'F': 'brasero', 'b': 'barril'}},
        # edad moderna
        'esquina': {'mapa': ['PtB'], 'leyenda': {'P': 'poste_de_luz', 't': 'tacho_de_basura', 'B': 'bolsa_de_basura'}},
        'estacionamiento': {'mapa': ['A..A..'], 'leyenda': {'A': 'auto'}},
        'obra': {'mapa': ['vxv', '.R.'], 'leyenda': {'v': 'valla', 'x': 'caja_de_carbon', 'R': 'barril_de_petroleo'}},
        'subestacion': {'mapa': ['kGk'], 'leyenda': {'G': 'generador'}},
        'fuente': {'mapa': ['h~~h', '.~~.'], 'leyenda': {'h': 'hidrante'}},
        # el origen
        'santuario': {'mapa': ['p.p', '.L.', 'p.p'], 'leyenda': {'L': 'altar', 'p': 'pilar_de_cristal'}},
        'ruinas': {'mapa': ['c.c'], 'leyenda': {'c': 'columna_rota'}},
    }

    # climas posibles y con cuales se conectan (asi no pasa de lluvia a sol de una sala a la otra)
    VECINOS_CLIMA = {
        'despejado': ('sol', 'nublado', 'tormenta_arena'), 'sol': ('despejado', 'tormenta_arena'), 'nublado': ('despejado', 'lluvia', 'niebla', 'nieve'),
        'lluvia': ('nublado', 'tormenta_electrica'), 'tormenta_electrica': ('lluvia',), 'niebla': ('nublado',),
        'nieve': ('nublado', 'granizo'), 'granizo': ('nieve',), 'tormenta_arena': ('despejado', 'sol'),
    }

    # cada era: su Regi, el semijefe de la sala 15, colores, enemigos, que tan seguido sale cada clima y las variantes de sala
    # formato de una variante:
    #   'forma': {silueta: peso}  ('rect', 'esquinas', 'cruz', 'columnas', 'cueva')     'simetria': {modo: peso}  ('no', 'h', 'v', 'hv')
    #   'piezas': {pieza: peso}  'num_piezas': (min, max)                            'interior': True si no le llega el clima
    #   'terrenos': [(terreno, (min, max) manchas, (min, max) casillas)]             'maquinas': [(maquina, (min, max))]
    #   'especiales': ['rio', 'foso', 'costa', 'cintas', 'cables']                  'objetos': {objeto: peso} sueltos, 'cantidad': (min, max)
    ERAS = [
        {'clave': 'glaciacion', 'nombre': 'Era Glacial', 'tienda': 'Puesto de trueque', 'regi': 'regice', 'jefe': 'walrein',
         'suelo': (196, 222, 236), 'pared': (85, 115, 140), 'clima_regi': 'granizo',
         'clima': {'nieve': 4, 'granizo': 2, 'nublado': 2, 'despejado': 1, 'niebla': 1},
         'enemigos': ['snorunt', 'glalie', 'froslass', 'spheal', 'sealeo', 'walrein', 'vanillite', 'vanillish', 'vanilluxe', 'sneasel',
                      'weavile', 'lapras', 'squirtle', 'wartortle',
                      'swinub', 'piloswine', 'zubat', 'golbat', 'wooloo', 'dubwool', 'cleffa', 'clefairy', 'glaceon', 'arrokuda', 'barraskewda', 'cramorant'],
         'variantes': {
             'glaciar': {'forma': {'rect': 2, 'esquinas': 2}, 'simetria': {'no': 2, 'h': 1}, 'terrenos': [('hielo', (2, 4), (8, 16)), ('nieve', (2, 3), (6, 12))],
                         'piezas': {'bloques de hielo': 2, 'estalagmitas': 1}, 'num_piezas': (1, 3), 'objetos': {'roca_nevada': 2, 'bloque_de_hielo': 2}, 'cantidad': (3, 6)},
             'lago congelado': {'forma': {'esquinas': 2, 'rect': 1}, 'especiales': ['laguna'], 'terrenos': [('hielo', (1, 2), (6, 10)), ('nieve', (1, 3), (4, 8))],
                                'piezas': {'pinar nevado': 2, 'bloques de hielo': 1}, 'num_piezas': (1, 2), 'objetos': {'pino_nevado': 2, 'roca_nevada': 1}, 'cantidad': (3, 6)},
             'tundra': {'forma': {'rect': 2, 'cruz': 1}, 'simetria': {'no': 1, 'hv': 1}, 'terrenos': [('nieve', (3, 5), (8, 16))], 'maquinas': [('cascada', (0, 1))],
                        'piezas': {'esqueleto de mamut': 2, 'pinar nevado': 2, 'campamento helado': 1}, 'num_piezas': (2, 3), 'objetos': {'pino_nevado': 3, 'roca_nevada': 2}, 'cantidad': (3, 7)},
             'cueva de hielo': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('sombra', (2, 3), (5, 10)), ('hielo', (2, 3), (5, 10))], 'maquinas': [('cascada', (1, 2))],
                                'piezas': {'estalagmitas': 3, 'campamento helado': 1}, 'num_piezas': (1, 3), 'objetos': {'estalagmita_de_hielo': 3, 'bloque_de_hielo': 1}, 'cantidad': (2, 5)},
             'grieta': {'forma': {'rect': 1, 'esquinas': 1}, 'especiales': ['rio'], 'terrenos': [('nieve', (2, 3), (5, 10)), ('hielo', (1, 2), (4, 8))],
                        'piezas': {'bloques de hielo': 1, 'esqueleto de mamut': 1}, 'num_piezas': (1, 2), 'objetos': {'roca_nevada': 2, 'estalagmita_de_hielo': 2}, 'cantidad': (3, 6)},
         },
         'arena': {'forma': {'esquinas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('hielo', (3, 4), (8, 12)), ('nieve', (1, 2), (5, 8))], 'maquinas': [('cascada', (2, 2))],
                   'piezas': {'estalagmitas': 1}, 'num_piezas': (1, 1), 'objetos': {}, 'cantidad': (0, 0)}},

        {'clave': 'piedra', 'nombre': 'Edad de Piedra', 'tienda': 'Mercado de trueque', 'regi': 'regirock', 'jefe': 'golem',
         'suelo': (150, 130, 95), 'pared': (70, 55, 40), 'clima_regi': 'tormenta_arena',
         'clima': {'despejado': 3, 'sol': 2, 'nublado': 2, 'lluvia': 2, 'tormenta_electrica': 0.5, 'niebla': 1, 'tormenta_arena': 1},
         'enemigos': ['geodude', 'graveler', 'golem', 'sandshrew', 'sandslash', 'cubone', 'marowak', 'mankey', 'primeape', 'timburr',
                      'chikorita', 'riolu', 'torchic', 'wooper', 'quagsire',
                      'lillipup', 'herdier', 'zigzagoon', 'linoone', 'anorith', 'armaldo', 'tyrunt', 'tyrantrum', 'larvitar', 'pupitar', 'rockruff', 'lycanroc', 'phanpy', 'donphan', 'sandile', 'krokorok', 'diglett_alola', 'shroomish', 'breloom', 'croagunk', 'litten', 'torracat', 'flareon', 'leafeon', 'eevee'],
         'variantes': {
             'pradera': {'forma': {'rect': 2, 'esquinas': 1}, 'simetria': {'no': 2, 'h': 1}, 'terrenos': [('hierba', (3, 5), (6, 14))],
                         'piezas': {'arboleda': 3, 'rocas': 2, 'fogata': 1}, 'num_piezas': (2, 4), 'objetos': {'arbusto': 3, 'roca': 2, 'arbol': 2}, 'cantidad': (3, 7)},
             'aldea de cazadores': {'forma': {'rect': 1, 'cruz': 1}, 'terrenos': [('hierba', (1, 2), (4, 8)), ('lodo', (1, 2), (3, 6))],
                                    'piezas': {'choza': 3, 'fogata': 2, 'rocas': 1}, 'num_piezas': (3, 4), 'objetos': {'cesto': 2, 'tronco': 2, 'lanza': 1}, 'cantidad': (2, 5)},
             'cueva rupestre': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('sombra', (3, 5), (5, 10))],
                                'piezas': {'fogata': 2, 'rocas': 2}, 'num_piezas': (1, 3), 'objetos': {'roca': 3, 'hueso': 2}, 'cantidad': (3, 6)},
             'circulo de piedras': {'forma': {'esquinas': 1, 'rect': 1}, 'simetria': {'hv': 2, 'h': 1}, 'terrenos': [('hierba', (2, 3), (5, 10))],
                                    'piezas': {'circulo de piedras': 3, 'rocas': 1}, 'num_piezas': (1, 2), 'objetos': {'menhir': 2, 'arbusto': 2}, 'cantidad': (2, 4)},
             'valle volcanico': {'forma': {'rect': 1, 'esquinas': 1}, 'terrenos': [('lava', (1, 3), (3, 6)), ('roca_volcanica', (2, 3), (4, 8)), ('ceniza', (1, 2), (4, 8))],
                                 'piezas': {'rocas': 2}, 'num_piezas': (1, 2), 'objetos': {'roca': 3, 'hueso': 1}, 'cantidad': (3, 6)},
             'rio': {'forma': {'rect': 1}, 'especiales': ['rio'], 'terrenos': [('hierba', (2, 4), (5, 10)), ('lodo', (1, 2), (3, 6))],
                     'piezas': {'arboleda': 2, 'choza': 1}, 'num_piezas': (1, 3), 'objetos': {'arbol': 2, 'arbusto': 2, 'roca': 1}, 'cantidad': (3, 6)},
         },
         'arena': {'forma': {'esquinas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('arena', (3, 4), (6, 10))], 'maquinas': [('monolito', (2, 2))],
                   'piezas': {'rocas': 1}, 'num_piezas': (2, 2), 'objetos': {}, 'cantidad': (0, 0)}},

        {'clave': 'metales', 'nombre': 'Edad de los Metales', 'tienda': 'Bazar', 'regi': 'registeel', 'jefe': 'corviknight',
         'suelo': (176, 132, 82), 'pared': (70, 45, 25), 'clima_regi': 'sol',
         'clima': {'despejado': 3, 'sol': 3, 'nublado': 2, 'tormenta_arena': 2, 'lluvia': 1},
         'enemigos': ['magnemite', 'magneton', 'machop', 'machoke', 'machamp', 'gurdurr', 'conkeldurr', 'combusken', 'blaziken', 'fletchling',
                      'fletchinder', 'talonflame', 'corvisquire', 'lucario', 'mareanie',
                      'aron', 'lairon', 'klink', 'klang', 'pawniard', 'bisharp', 'honedge', 'doublade', 'mawile', 'tinkatink', 'tinkatuff', 'scyther', 'scizor', 'nincada', 'ninjask', 'charcadet', 'whismur', 'loudred', 'growlithe_hisui', 'stoutland'],
         'variantes': {
             'forja': {'forma': {'rect': 2, 'columnas': 1}, 'interior': True, 'terrenos': [('ceniza', (1, 3), (4, 8))], 'maquinas': [('iman', (0, 1))],
                       'piezas': {'herreria': 3, 'carga de bronce': 1}, 'num_piezas': (2, 3), 'objetos': {'lingotes': 2, 'armadura': 2, 'caja': 1}, 'cantidad': (2, 5)},
             'mina de cobre': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('sombra', (2, 4), (5, 10)), ('lodo', (1, 2), (3, 6))],
                               'piezas': {'carga de bronce': 2}, 'num_piezas': (1, 2), 'objetos': {'lingotes': 2, 'caja': 2, 'barril': 1}, 'cantidad': (3, 6)},
             'mercado': {'forma': {'cruz': 2, 'rect': 1}, 'simetria': {'h': 1, 'v': 1, 'no': 1}, 'terrenos': [('arena', (1, 2), (4, 8))],
                         'piezas': {'puesto de mercado': 3, 'estatua': 1, 'carga de bronce': 1}, 'num_piezas': (3, 4), 'objetos': {'anfora': 3, 'caja': 2, 'barril': 2}, 'cantidad': (3, 6)},
             'templo de bronce': {'forma': {'columnas': 2, 'rect': 1}, 'simetria': {'hv': 2, 'h': 1}, 'maquinas': [('brasero', (2, 2))],
                                  'piezas': {'columnata': 2, 'estatua': 2}, 'num_piezas': (2, 3), 'objetos': {'anfora': 2, 'armadura': 1}, 'cantidad': (2, 4)},
             'puerto antiguo': {'forma': {'rect': 1}, 'especiales': ['costa'], 'terrenos': [('arena', (2, 3), (4, 8))],
                                'piezas': {'carga de bronce': 2, 'puesto de mercado': 1}, 'num_piezas': (1, 3), 'objetos': {'anfora': 3, 'barril': 2, 'caja': 2}, 'cantidad': (3, 6)},
         },
         'arena': {'forma': {'columnas': 1}, 'simetria': {'hv': 1}, 'maquinas': [('iman', (2, 2)), ('forja', (1, 1))], 'piezas': {'estatua': 1}, 'num_piezas': (1, 1), 'objetos': {}, 'cantidad': (0, 0)}},

        {'clave': 'medieval', 'nombre': 'Edad Media', 'tienda': 'Mercado', 'regi': 'regidrago', 'jefe': 'garchomp',
         'suelo': (128, 112, 88), 'pared': (52, 42, 32), 'clima_regi': 'tormenta_electrica',
         'clima': {'nublado': 3, 'lluvia': 3, 'niebla': 2, 'despejado': 2, 'tormenta_electrica': 1, 'sol': 1},
         'enemigos': ['gible', 'gabite', 'golett', 'golurk', 'samurott_hisui', 'oshawott', 'dewott', 'samurott', 'rookidee', 'drifloon',
                      'drifblim', 'natu', 'xatu', 'hawlucha', 'froakie', 'frogadier',
                      'axew', 'fraxure', 'bagon', 'shelgon', 'druddigon', 'ralts', 'kirlia', 'gallade', 'ponyta_galar', 'rapidash_galar', 'flabebe', 'floette', 'impidimp', 'morgrem', 'phantump', 'trevenant', 'litwick', 'lampent', 'shuppet', 'banette', 'greavard', 'houndstone', 'sewaddle', 'swadloon', 'leavanny', 'fomantis', 'lurantis', 'sprigatito', 'floragato', 'foongus', 'kleavor', 'zorua_hisui', 'dreepy', 'drakloak', 'espeon', 'umbreon', 'sylveon', 'arcanine_hisui'],
         'variantes': {
             'patio del castillo': {'forma': {'rect': 2, 'columnas': 1}, 'simetria': {'h': 2, 'hv': 1, 'no': 1}, 'terrenos': [('arena', (1, 2), (5, 10))], 'maquinas': [('brasero', (2, 4))],
                                    'piezas': {'polvorin': 2, 'campamento': 2}, 'num_piezas': (2, 3), 'objetos': {'estatua_de_caballero': 2, 'estandarte': 2, 'carreta': 1, 'caja': 2}, 'cantidad': (3, 6)},
             'bosque encantado': {'forma': {'rect': 1, 'esquinas': 2}, 'especiales': ['rio'], 'terrenos': [('hierba', (3, 5), (6, 14)), ('lodo', (0, 2), (3, 6))], 'maquinas': [('altar', (0, 1))],
                                  'piezas': {'arboleda': 3}, 'num_piezas': (2, 3), 'objetos': {'arbol': 3, 'arbusto': 3}, 'cantidad': (3, 7)},
             'aldea': {'forma': {'rect': 1, 'cruz': 1}, 'terrenos': [('hierba', (1, 2), (4, 8)), ('lodo', (1, 2), (4, 8)), ('charco', (0, 2), (2, 4))],
                       'piezas': {'establo': 3, 'campamento': 1}, 'num_piezas': (2, 4), 'objetos': {'carreta': 2, 'barril': 2, 'pozo': 1}, 'cantidad': (2, 5)},
             'mazmorra': {'forma': {'columnas': 1, 'cruz': 1}, 'interior': True, 'simetria': {'hv': 1, 'no': 1}, 'terrenos': [('sombra', (3, 5), (6, 12)), ('charco', (1, 2), (2, 5))],
                          'maquinas': [('brasero', (2, 4))], 'piezas': {'cementerio': 2, 'polvorin': 1}, 'num_piezas': (1, 3), 'objetos': {'barril': 2, 'caja': 2}, 'cantidad': (2, 5)},
             'foso del castillo': {'forma': {'rect': 1}, 'especiales': ['foso'], 'simetria': {'hv': 1}, 'maquinas': [('brasero', (2, 4))],
                                   'piezas': {'polvorin': 1}, 'num_piezas': (0, 1), 'objetos': {'barril': 2, 'estandarte': 2, 'estatua_de_caballero': 1}, 'cantidad': (3, 6)},
             'guarida del dragon': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('lava', (1, 2), (3, 6)), ('roca_volcanica', (2, 3), (4, 8))],
                                    'piezas': {'santuario del dragon': 2}, 'num_piezas': (1, 2), 'objetos': {'escamas_de_dragon': 3, 'roca': 2}, 'cantidad': (3, 6)},
         },
         'arena': {'forma': {'esquinas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('roca_volcanica', (2, 3), (4, 8))], 'maquinas': [('cristal_dragonico', (2, 2)), ('brasero', (2, 2))],
                   'piezas': {}, 'num_piezas': (0, 0), 'objetos': {}, 'cantidad': (0, 0)}},

        {'clave': 'moderna', 'nombre': 'Edad Moderna', 'tienda': 'Almacén', 'regi': 'regieleki', 'jefe': 'magnezone',
         'suelo': (70, 78, 122), 'pared': (24, 24, 44), 'clima_regi': 'tormenta_electrica',
         'clima': {'nublado': 3, 'lluvia': 2, 'niebla': 2, 'tormenta_electrica': 2, 'despejado': 2, 'sol': 1},
         'enemigos': ['pichu', 'pikachu', 'raichu', 'mareep', 'flaaffy', 'ampharos', 'shinx', 'luxio', 'luxray', 'electrike',
                      'manectric', 'magneton', 'toxapex', 'clodsire', 'greninja', 'annihilape',
                      'joltik', 'galvantula', 'elgyem', 'beheeyem', 'espurr', 'meowstic', 'grimer_alola', 'muk_alola', 'skrelp', 'dragalge', 'noibat', 'noivern', 'wimpod', 'golisopod', 'zorua', 'zoroark', 'snivy', 'servine', 'crobat', 'incineroar', 'vaporeon', 'jolteon', 'exploud', 'armarouge', 'ceruledge', 'klinklang', 'dugtrio_alola'],
         'variantes': {
             'fabrica': {'forma': {'rect': 1, 'columnas': 1}, 'interior': True, 'especiales': ['cintas'], 'terrenos': [('aceite', (1, 2), (3, 6))],
                         'maquinas': [('horno', (1, 2)), ('iman', (0, 1))], 'piezas': {'obra': 2}, 'num_piezas': (1, 2),
                         'objetos': {'caja_de_carbon': 3, 'engranaje': 1, 'chatarra': 2, 'tuberia': 1, 'vagoneta': 1}, 'cantidad': (3, 6)},
             'calle': {'forma': {'rect': 2, 'cruz': 1}, 'simetria': {'h': 1, 'no': 2}, 'terrenos': [('charco', (1, 3), (2, 5))],
                       'piezas': {'estacionamiento': 2, 'esquina': 3}, 'num_piezas': (2, 4), 'objetos': {'poste_de_luz': 2, 'hidrante': 2, 'contenedor': 1}, 'cantidad': (2, 5)},
             'plaza': {'forma': {'esquinas': 2, 'cruz': 1}, 'simetria': {'hv': 2, 'h': 1}, 'terrenos': [('hierba', (2, 3), (4, 8))],
                       'piezas': {'fuente': 2, 'esquina': 1}, 'num_piezas': (1, 3), 'objetos': {'banco_de_plaza': 3, 'poste_de_luz': 2, 'arbol': 2}, 'cantidad': (3, 6)},
             'callejon': {'forma': {'cruz': 2, 'rect': 1}, 'terrenos': [('sombra', (3, 5), (5, 10)), ('charco', (1, 2), (2, 4))],
                          'piezas': {'esquina': 3, 'obra': 1}, 'num_piezas': (2, 4), 'objetos': {'bolsa_de_basura': 4, 'contenedor': 2, 'cabina_telefonica': 1}, 'cantidad': (3, 7)},
             'central electrica': {'forma': {'rect': 1, 'columnas': 1}, 'simetria': {'hv': 1, 'h': 1}, 'especiales': ['cables'], 'maquinas': [('generador', (1, 2))],
                                   'piezas': {'subestacion': 3}, 'num_piezas': (1, 3), 'objetos': {'poste_de_luz': 2, 'chatarra': 2, 'maquina_expendedora': 1}, 'cantidad': (2, 5)},
             'alcantarilla': {'forma': {'cruz': 1, 'rect': 1}, 'interior': True, 'especiales': ['rio'], 'terrenos': [('toxico', (1, 3), (3, 6)), ('charco', (1, 3), (2, 5))],
                              'piezas': {'esquina': 1}, 'num_piezas': (0, 2), 'objetos': {'bolsa_de_basura': 3, 'tuberia': 2, 'tacho_de_basura': 2}, 'cantidad': (3, 6)},
         },
         'arena': {'forma': {'rect': 1}, 'simetria': {'hv': 1}, 'especiales': ['cables'], 'terrenos': [('charco', (3, 4), (3, 6))], 'maquinas': [('generador', (2, 2))],
                   'piezas': {}, 'num_piezas': (0, 0), 'objetos': {}, 'cantidad': (0, 0)}},

        {'clave': 'origen', 'nombre': 'El Origen', 'tienda': 'Bazar del tiempo', 'regi': 'regigigas', 'final': 'arceus', 'jefe': None,
         'suelo': (204, 194, 236), 'pared': (88, 78, 130), 'clima_regi': None, 'clima_final': 'sol',
         'plan_fijo': ['tienda', 'regi', 'final'],             # cuando caen los 5 Regis: tienda, Regigigas y despues Arceus
         'clima': {'despejado': 2, 'tormenta_electrica': 1, 'niebla': 1},
         'enemigos': ['garchomp', 'lucario', 'annihilape', 'greninja', 'xatu', 'golurk', 'weavile', 'luxray', 'blaziken', 'corviknight',
                      'great_tusk', 'roaring_moon', 'iron_thorns', 'dragapult', 'tyranitar', 'salamence', 'kingambit', 'haxorus', 'gardevoir', 'mamoswine', 'meowscarada', 'aegislash', 'tinkaton', 'florges', 'chandelure', 'krookodile', 'grimmsnarl', 'zoroark_hisui', 'serperior', 'clefable', 'aggron', 'toxicroak', 'golisopod'],
         'variantes': {
             'templo de los titanes': {'forma': {'columnas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('sombra', (2, 4), (5, 9))], 'maquinas': [('monolito', (1, 2))],
                                       'piezas': {'santuario': 2, 'ruinas': 2}, 'num_piezas': (2, 3), 'objetos': {'pilar_de_cristal': 2, 'columna_rota': 2, 'estatua_de_titan': 1}, 'cantidad': (2, 4)},
         },
         'arena': {'forma': {'circulo': 1}, 'tamaño': (23, 23), 'simetria': {'hv': 1}, 'maquinas': [('altar', (2, 2)), ('monolito', (2, 2))],
                   'piezas': {'ruinas': 1}, 'num_piezas': (1, 2), 'objetos': {}, 'cantidad': (0, 0)}},   # Regigigas y Arceus: arena redonda y mas grande
    ]
    REGIS = tuple(e['regi'] for e in ERAS if 'plan_fijo' not in e)     # los 5 Regis de las eras (no Regigigas)
    ARENA_REGI = {'forma': {'circulo': 1}, 'tamaño': (19, 19), 'simetria': {'no': 1}, 'paredes': (0, 0),   # sala de los 5 Regis: redonda, grande y vacia
                  'piezas': {}, 'num_piezas': (0, 0), 'objetos': {}, 'cantidad': (0, 0)}


    def planificar(azar):
        """Lista de listas de tipos de sala (una por era). La tienda nunca cae en un jefe."""
        normales = [e for e in ERAS if 'plan_fijo' not in e]
        total = len(normales) * SALAS_POR_ERA
        plano = ['combate'] * total
        for e in range(len(normales)):                              # los jefes fijos de cada era
            plano[e * SALAS_POR_ERA + SALA_JEFE - 1] = 'jefe'
            plano[e * SALAS_POR_ERA + SALA_REGI - 1] = 'regi'
        ultima, hueco_ant = -1, None                                # indice de la ultima tienda y cuanto tardo
        while True:
            minimo = TIENDA_HUECO[0] if hueco_ant is None else max(TIENDA_HUECO[0], TIENDA_COMPENSA - hueco_ant)
            opciones = [h for h in range(minimo, TIENDA_HUECO[1] + 1) if ultima + h < total and plano[ultima + h] == 'combate']
            if not opciones:                                        # todas caian en jefe: se corre una o dos salas
                opciones = [h for h in (TIENDA_HUECO[1] + 1, TIENDA_HUECO[1] + 2) if ultima + h < total and plano[ultima + h] == 'combate']
            if not opciones: break                                  # no entra otra tienda antes del final
            hueco = azar.choice(opciones)
            ultima += hueco; hueco_ant = hueco
            plano[ultima] = 'tienda'
        plan = [plano[e * SALAS_POR_ERA:(e + 1) * SALAS_POR_ERA] for e in range(len(normales))]
        return plan + [list(e['plan_fijo']) for e in ERAS if 'plan_fijo' in e]


    def clima_inicial(azar, era):
        """Clima al azar segun lo comun que es en la era."""
        pesos = ERAS[era]['clima']
        return azar.choices(list(pesos), list(pesos.values()))[0]


    def siguiente_clima(azar, era, actual):
        """Clima de la sala que viene: casi siempre sigue igual o pasa a uno vecino, y segun lo que es comun en la era."""
        pesos = ERAS[era]['clima']
        if actual not in pesos: return clima_inicial(azar, era)     # cambio de era: arranca de cero
        if azar.random() < PROB_SEGUIR_CLIMA: return actual
        vecinos = [v for v in VECINOS_CLIMA.get(actual, ()) if pesos.get(v)]
        if not vecinos: return actual
        return azar.choices(vecinos, [pesos[v] for v in vecinos])[0]


    def nuevo_recorrido(semilla=None):
        """Estado de una partida: el plan entero, en que sala estas y el clima que viene arrastrando."""
        azar = random.Random(semilla)
        return {'plan': planificar(azar), 'era': 0, 'sala': 0, 'semilla': semilla, 'clima': clima_inicial(azar, 0), 'azar': azar,
                'historial': [], 'pos': -1}               # salas por las que pasaste (para volver y para guardar) y en cual estas


    def tipo_sala(rec, era=None, sala=None):
        """Que hay en una sala del plan: 'combate', 'tienda', 'jefe', 'regi' o 'final'."""
        return rec['plan'][rec['era'] if era is None else era][rec['sala'] if sala is None else sala]


    def salas_de(rec, era=None):
        """Cuantas salas tiene una era."""
        return len(rec['plan'][rec['era'] if era is None else era])


    def siguiente(rec):
        """(era, sala) de la sala que viene, o None si la actual es la ultima."""
        if rec['sala'] + 1 < salas_de(rec): return rec['era'], rec['sala'] + 1
        if rec['era'] + 1 < len(rec['plan']): return rec['era'] + 1, 0
        return None


    def avanzar(rec):
        """Pasa a la sala siguiente y le elige el clima (si cambia de era, el clima arranca de nuevo)."""
        pos = siguiente(rec)
        if pos is None: return False
        cambio_era = pos[0] != rec['era']
        rec['era'], rec['sala'] = pos
        rec['clima'] = clima_inicial(rec['azar'], rec['era']) if cambio_era else siguiente_clima(rec['azar'], rec['era'], rec['clima'])
        return True


    def ir_a(rec, era, sala):
        """Salto directo (menu debug F2)."""
        rec['era'], rec['sala'] = era, sala
        rec['clima'] = clima_inicial(rec['azar'], era)


    def destinos_siguientes(rec, azar):
        """Lo que hay detras de cada puerta: variantes distintas si la que viene es de combate, una sola si es especial."""
        pos = siguiente(rec)
        if pos is None: return [{'tipo': 'fin', 'variante': None, 'era': rec['era']}]
        era, sala = pos
        tipo = tipo_sala(rec, era, sala)
        if tipo != 'combate' or era != rec['era']:                  # tienda, jefe, regi o cambio de era: una sola puerta
            variante = azar.choice(list(ERAS[era]['variantes'])) if tipo == 'combate' else None
            return [{'tipo': tipo, 'variante': variante, 'era': era, 'desde': rec['era']}]
        cantidad = azar.choices([c for c, _ in PUERTAS_POR_SALA], [p for _, p in PUERTAS_POR_SALA])[0]
        variantes = azar.sample(list(ERAS[era]['variantes']), min(cantidad, len(ERAS[era]['variantes'])))
        destinos = [{'tipo': 'combate', 'variante': v, 'era': era, 'desde': rec['era'], 'desafio': azar.random() < PROB_DESAFIO} for v in variantes]
        if len(destinos) >= 2 and azar.random() < PROB_TESORO:       # una de las puertas lleva a una sala del tesoro (con candado)
            destinos[-1] = {'tipo': 'tesoro', 'variante': None, 'era': era, 'desde': rec['era'], 'candado': True}
        return destinos


    def jefe_de(era, tipo):
        """Pokemon que pelea en una sala de jefe, de Regi o la final."""
        datos = ERAS[era]
        return datos.get('final') if tipo == 'final' else datos['regi'] if tipo == 'regi' else datos['jefe']


    def etiqueta_destino(destino):
        """Texto del cartel arriba de una puerta."""
        if destino['tipo'] == 'volver': return 'VOLVER'
        if destino['tipo'] == 'viaje': return 'VIAJE TEMPORAL'                # el portal del hall: empieza otro viaje desde la Era Glacial
        if destino['tipo'] == 'zona': return {'barrio': 'AL BARRIO', 'plaza': 'A LA PLAZA'}.get(destino.get('zona'), str(destino.get('zona', '')).upper())
        if destino['tipo'] == 'tesoro': return 'TESORO (llave)' if destino.get('candado') else 'TESORO'
        if destino.get('cerrado'): return 'camino no tomado'
        era = ERAS[destino['era']]
        if destino['tipo'] == 'tienda': return era['tienda'].upper()         # el nombre cambia con la era (siempre la atiende Chikorita)
        if destino['tipo'] in ('jefe', 'regi', 'final'): return destino['tipo'].upper() + ': ' + str(jefe_de(destino['era'], destino['tipo'])).title()
        if destino['tipo'] == 'fin': return 'FINAL'
        if destino['era'] != destino.get('desde', destino['era']): return era['nombre']
        return destino['variante'].capitalize() + (' ★ desafío' if destino.get('desafio') else '')


    def escala(era, sala):
        """Cuanto mas fuertes son los enemigos segun por donde vas."""
        return {'vida': 1 + 0.3 * era + 0.01 * sala, 'daño': 1 + 0.18 * era + 0.005 * sala, 'cantidad': 13 + 3 * era + sala // 3}

    return SimpleNamespace(**locals())


mundos = armar_mundos()
