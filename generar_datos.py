import json
import time
import urllib.request
from pokemones import pokemones

CAMBIOS = {'samurott_hisui': 'samurott-hisui'}
SALTAR = ('arceus_beta', 'missigno')


def pedir(slug):
    url = 'https://pokeapi.co/api/v2/pokemon/' + slug
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'pokemanic'}), timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    salida = {}
    for nombre in pokemones:
        if nombre in SALTAR: continue
        slug = CAMBIOS.get(nombre, nombre.replace('_', '-'))
        try:
            datos = pedir(slug)
        except Exception as error:
            print('falla', nombre, error)
            continue
        salida[nombre] = {
            'altura': datos['height'],
            'peso': datos['weight'],
            'stats': {s['stat']['name']: s['base_stat'] for s in datos['stats']},
        }
        print('ok', nombre)
        time.sleep(0.2)
    with open('datos_pokeapi.json', 'w', encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
