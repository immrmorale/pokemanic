import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pokemones import pokemones, JUGABLES

BASE = 'https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/'
DESTINO = os.path.join('assets', 'sprites', 'pokemones')
ANIMACIONES = ('idle', 'walk', 'attack', 'strike', 'shoot', 'charge', 'swing', 'double', 'hop', 'rotate', 'pose', 'dance', 'hurt')
FORMAS = {'samurott_hisui': '0503/0001'}
EXTRA = ('regigigas', 'regice', 'regirock', 'registeel', 'regieleki', 'regidrago', 'arceus')


def bajar(ruta, destino):
    if os.path.isfile(destino):
        return True
    try:
        req = urllib.request.Request(BASE + ruta, headers={'User-Agent': 'pokemanic'})
        with urllib.request.urlopen(req, timeout=30) as r:
            datos = r.read()
    except (urllib.error.URLError, OSError):
        return False
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'wb') as f:
        f.write(datos)
    return True


def bajar_pokemon(nombre):
    dex = pokemones[nombre].get('pokedex')
    if not isinstance(dex, int) and nombre not in FORMAS:
        return False
    repo = FORMAS.get(nombre) or '%04d' % dex
    carpeta = os.path.join(DESTINO, 'sprite_' + nombre)
    if not bajar('sprite/' + repo + '/AnimData.xml', os.path.join(carpeta, 'AnimData.xml')):
        return False
    raiz = ET.parse(os.path.join(carpeta, 'AnimData.xml')).getroot()
    for nodo in raiz.find('Anims').findall('Anim'):
        anim = nodo.findtext('Name')
        if not anim or anim.lower() not in ANIMACIONES or nodo.findtext('FrameWidth') is None:
            continue
        for sufijo in ('-Anim.png', '-Offsets.png', '-Shadow.png'):
            bajar('sprite/' + repo + '/' + anim + sufijo, os.path.join(carpeta, anim + sufijo))
    bajar('portrait/' + repo + '/Normal.png', os.path.join(carpeta, 'portrait', 'Normal.png'))
    return True


def main():
    fallos = []
    for nombre in list(JUGABLES) + list(EXTRA):
        if nombre not in pokemones:
            continue
        ok = bajar_pokemon(nombre)
        print('ok' if ok else 'FALLA', nombre)
        if not ok:
            fallos.append(nombre)
        time.sleep(0.1)
    if fallos:
        print('sin descargar:', ', '.join(fallos))


if __name__ == '__main__':
    main()
