"""
mts.py - Maquinas Tecnicas: movimientos que se le enseñan a un pokemon en una de sus 4 casillas (E, Q, Shift, R).

    mts.MTS['mt_trueno']           # nombre, tipo, precio y los datos del movimiento listos para el combate
    mts.puede_aprender('pikachu', 'mt_trueno')
    mts.datos('mt_trueno')         # datos del movimiento (None si no es una MT)

Salen de ataques.habilidades. Las que curan no estan (en este juego nada cura).
Al usarla se gasta (salvo con el truco de MT infinitas).
"""

from ataques import habilidades
from pokemones import _oficiales

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
    if h['modo'] in ('buff', 'escudo'): return 180
    return 120 + round(h.get('daño', 20) * 3) + (40 if h.get('efecto') else 0)


MTS = {'mt_' + clave: {'nombre': 'MT ' + h['nombre'], 'api': h['api'], 'tipo': h['tipo'], 'precio': _precio(h), 'datos': _convertir(h)}
       for clave, h in habilidades.items() if h['modo'] != 'curar'}


def datos(nombre):
    mt = MTS.get(nombre)
    return mt['datos'] if mt else None


def puede_aprender(pokemon, clave):
    """True si la especie aprende ese movimiento (segun la PokeAPI). Sin datos, cualquiera puede."""
    lista = (_oficiales.get(pokemon) or {}).get('movimientos')
    return lista is None or MTS[clave]['api'] in lista


def aprendibles(pokemon):
    return [k for k in MTS if puede_aprender(pokemon, k)]
