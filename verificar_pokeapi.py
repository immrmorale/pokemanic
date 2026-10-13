import json
import os
import urllib.request

from pokemones import pokemones, TABLA_TIPOS
from ataques import habilidades, sinergias

API = 'https://pokeapi.co/api/v2/'
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache_pokeapi.json')
TIPOS_EN = {'normal': 'normal', 'fuego': 'fire', 'agua': 'water', 'electrico': 'electric', 'planta': 'grass', 'hielo': 'ice',
            'lucha': 'fighting', 'veneno': 'poison', 'tierra': 'ground', 'volador': 'flying', 'psiquico': 'psychic',
            'roca': 'rock', 'fantasma': 'ghost', 'dragon': 'dragon', 'siniestro': 'dark', 'acero': 'steel'}
EN_TIPOS = {v: k for k, v in TIPOS_EN.items()}
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.isfile(CACHE) else {}


def pedir(ruta):
    if ruta not in cache:
        pedido = urllib.request.Request(API + ruta, headers={'User-Agent': 'pokemanic-verificacion'})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            cache[ruta] = json.loads(r.read().decode('utf-8'))
    return cache[ruta]


def verificar_tipos():
    print('--- tabla de tipos')
    errores = 0
    for tipo, en in TIPOS_EN.items():
        rel = pedir('type/' + en)['damage_relations']
        oficial = {}
        for clave, valor in (('double_damage_to', 2.0), ('half_damage_to', 0.5), ('no_damage_to', 0.0)):
            for t in rel[clave]:
                if t['name'] in EN_TIPOS:
                    oficial[EN_TIPOS[t['name']]] = valor
        propio = {k: float(v) for k, v in TABLA_TIPOS.get(tipo, {}).items()}
        if oficial != propio:
            errores += 1
            print(tipo, 'difiere | oficial:', oficial, '| juego:', propio)
    print('tipos con diferencias:', errores)


def verificar_movimientos():
    print('--- habilidades y sinergias que cada pokemon puede aprender')
    errores = 0
    for nombre, datos in pokemones.items():
        if not datos.get('jugable'):
            continue
        movimientos = {m['move']['name'] for m in pedir('pokemon/' + nombre.replace('_', '-'))['moves']}
        pedidos = [habilidades[c] for c in datos.get('habilidades', [])]
        if datos.get('apoyo'):
            pedidos.append(sinergias[datos['apoyo']])
        for movimiento in pedidos:
            if movimiento['api'] not in movimientos:
                errores += 1
                print(nombre, 'no aprende', movimiento['api'], '(' + movimiento['nombre'] + ')')
    print('habilidades que no aprende el pokemon:', errores)


if __name__ == '__main__':
    try:
        verificar_tipos()
        verificar_movimientos()
    finally:
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
