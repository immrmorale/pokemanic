"""
opciones.py - Ajustes del juego guardados en config.json (volumen, combate, resolucion, controles...).

    config = opciones.cargar()
    opciones.guardar(config)
"""

import json
import os

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
