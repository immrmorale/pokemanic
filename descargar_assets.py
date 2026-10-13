import os
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from pokemones import pokemones

BASE = 'https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/'
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sprites', 'pokemones')
RETRATOS = ('Normal', 'Pain')
FORMAS = {'samurott_hisui': '0001'}
SALTEAR = ('missigno', 'arceus_beta')


def bajar(url, intentos=3):
    for i in range(intentos):
        try:
            pedido = urllib.request.Request(url, headers={'User-Agent': 'pokemanic-descarga'})
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        time.sleep(1 + i)
    return None


def guardar(url, ruta):
    if os.path.isfile(ruta):
        return True
    datos = bajar(url)
    if datos is None:
        return False
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'wb') as f:
        f.write(datos)
    return True


def descargar(nombre, datos):
    dex = '%04d' % datos['pokedex']
    forma = FORMAS.get(nombre)
    subruta = dex + ('/' + forma if forma else '')
    carpeta = os.path.join(DESTINO, 'sprite_' + nombre)
    if not guardar(BASE + 'sprite/' + subruta + '/AnimData.xml', os.path.join(carpeta, 'AnimData.xml')):
        return nombre, 0, ['AnimData.xml']
    animaciones = []
    for anim in ET.parse(os.path.join(carpeta, 'AnimData.xml')).getroot().find('Anims').findall('Anim'):
        if anim.findtext('Name') and not anim.findtext('CopyOf'):
            animaciones.append(anim.findtext('Name'))
    faltan = []
    for anim in animaciones:
        archivo = anim + '-Anim.png'
        if not guardar(BASE + 'sprite/' + subruta + '/' + archivo, os.path.join(carpeta, archivo)):
            faltan.append(archivo)
    for emocion in RETRATOS:
        if not guardar(BASE + 'portrait/' + subruta + '/' + emocion + '.png', os.path.join(carpeta, 'portrait', emocion + '.png')):
            faltan.append('portrait/' + emocion + '.png')
    return nombre, len(animaciones), faltan


def main():
    pendientes = [(n, d) for n, d in pokemones.items() if n not in SALTEAR]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for nombre, cantidad, faltan in pool.map(lambda x: descargar(*x), pendientes):
            print(nombre.ljust(18), cantidad, 'animaciones', '| faltan:' if faltan else '', ', '.join(faltan))
    print('listo: ' + DESTINO)


if __name__ == '__main__':
    main()
