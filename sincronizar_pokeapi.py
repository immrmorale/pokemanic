import json
import os
import time
import urllib.error
import urllib.request
from pokemones import pokemones

BASE = 'https://pokeapi.co/api/v2/pokemon/'
DESTINO = os.path.join(os.path.dirname(__file__), 'datos_pokeapi.json')


def descargar(nombre):
    slug = nombre.replace('_', '-')
    if nombre in ('arceus_beta', 'missigno'):
        return None
    peticion = urllib.request.Request(BASE + slug, headers={'User-Agent': 'Pokemanic-PokeAPI-Sync/1.0'})
    with urllib.request.urlopen(peticion, timeout=15) as respuesta:
        return json.loads(respuesta.read().decode('utf-8'))


def main():
    if os.path.isfile(DESTINO):
        try:
            with open(DESTINO, 'r', encoding='utf-8') as archivo:
                datos = json.load(archivo)
        except (OSError, ValueError):
            datos = {}
    else:
        datos = {}
    errores = []
    for nombre in pokemones:
        if nombre in ('arceus_beta', 'missigno'):
            continue
        try:
            pokemon = descargar(nombre)
            if not pokemon:
                continue
            stats = {x['stat']['name']: x['base_stat'] for x in pokemon.get('stats', [])}
            moves = sorted({x['move']['name'] for x in pokemon.get('moves', [])})
            tipos = [x['type']['name'] for x in pokemon.get('types', [])]
            datos[nombre] = {
                'id': pokemon.get('id'),
                'stats': stats,
                'height_m': pokemon.get('height', 0) / 10,
                'weight_kg': pokemon.get('weight', 0) / 10,
                'types': tipos,
                'moves': moves
            }
            print(nombre + ': datos sincronizados')
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as error:
            errores.append((nombre, str(error)))
            print(nombre + ': no se pudo descargar')
        time.sleep(0.08)
    with open(DESTINO, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    print('Archivo guardado: ' + DESTINO)
    print('Pokémon guardados: ' + str(len(datos)))
    if errores:
        print('Sin actualizar: ' + ', '.join(nombre for nombre, _ in errores))
        print('Puedes volver a ejecutar el script para completar los datos faltantes.')


if __name__ == '__main__':
    main()
