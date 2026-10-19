import json
import time
import urllib.request
from pokemones import pokemones

CAMBIOS = {'samurott_hisui': 'samurott-hisui'}
SALTAR = ('arceus_beta', 'missigno')


def pedir(url):
    if not url.startswith('http'):
        url = 'https://pokeapi.co/api/v2/pokemon/' + url
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'pokemanic'}), timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def como_evoluciona(hijo):
    """Nivel, piedra u otra condicion para evolucionar a ese hijo de la cadena."""
    d = (hijo.get('evolution_details') or [{}])[0]
    return {'a': hijo['species']['name'], 'disparador': (d.get('trigger') or {}).get('name'), 'nivel': d.get('min_level'),
            'objeto': (d.get('item') or {}).get('name'), 'amistad': d.get('min_happiness')}


def buscar_cadena(nodo, objetivo, padre=None):
    if nodo['species']['name'] == objetivo:
        return padre, [n['species']['name'] for n in nodo['evolves_to']], [como_evoluciona(n) for n in nodo['evolves_to']]
    for hijo in nodo['evolves_to']:
        r = buscar_cadena(hijo, objetivo, nodo['species']['name'])
        if r:
            return r
    return None


def descripcion(especie):
    textos = [t['flavor_text'] for t in especie['flavor_text_entries'] if t['language']['name'] == 'es']
    if not textos:
        textos = [t['flavor_text'] for t in especie['flavor_text_entries'] if t['language']['name'] == 'en']
    return ' '.join(textos[-1].replace('\n', ' ').replace('\f', ' ').split()) if textos else None


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
        registro = {
            'altura': datos['height'],
            'peso': datos['weight'],
            'stats': {s['stat']['name']: s['base_stat'] for s in datos['stats']},
            'movimientos': sorted(mv['move']['name'] for mv in datos['moves']),
            'experiencia_base': datos.get('base_experience'),
        }
        try:
            especie = pedir(datos['species']['url'])
            registro['descripcion'] = descripcion(especie)
            registro['ratio_captura'] = especie.get('capture_rate')
            registro['crecimiento'] = (especie.get('growth_rate') or {}).get('name')
            registro['legendario'] = especie.get('is_legendary') or especie.get('is_mythical')
            cadena = pedir(especie['evolution_chain']['url'])
            encontrado = buscar_cadena(cadena['chain'], especie['name'])
            if encontrado:
                registro['evoluciona_de'], registro['evoluciona_a'], registro['evoluciones'] = encontrado
        except Exception as error:
            print('sin especie', nombre, error)
        salida[nombre] = registro
        print('ok', nombre)
        time.sleep(0.2)
    with open('datos_pokeapi.json', 'w', encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
