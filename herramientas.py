"""
herramientas.py - Programas aparte para preparar el juego (no se usan mientras jugas).

    python herramientas.py descargar           baja los sprites y retratos del PMD (SpriteCollab)
    python herramientas.py caras celebi ...    baja las demas caras del retrato (feliz, sorprendido, preocupado...) para las charlas
    python herramientas.py animaciones [poke]  dice que hace cada animacion de los sprites y cual usa cada ataque (y lo guarda en asignacion_animaciones.json)
    python herramientas.py sonidos             baja los gritos de todos los pokemon (PokeAPI) a assets/sonidos/gritos
    python herramientas.py datos               arma datos_pokeapi.json desde la PokeAPI
    python herramientas.py recortar hoja.png   recorta sprites de una hoja y los deja en assets/mundo
    python herramientas.py hojas               baja todas las hojas (menos pokemon) de BW y los PMD a assets/hojas (via archive.org)
    python herramientas.py tiles               arma los tilesets con bordes (autotile) y el agua animada del PMD para cada era y variante de sala
    python herramientas.py decorados           rocas, hielo, pinos (piezas sueltas del PMD) y arbustos/arboles (Poke Transfer de BW) para los objetos
    python herramientas.py cielo               recorta el cielo y las nubes del Explorers of Sky para la intro
    python herramientas.py minimapa            recorta las piezas del minimapa (Map Sprites del Explorers of Time/Darkness)
    python herramientas.py viaje               recorta el tunel del viaje temporal del Explorers of Sky para la partida nueva
    python herramientas.py efectos             arma los efectos de golpes, proyectiles por tipo, cura, nivel... con los Attack Effects del PMD
    python herramientas.py objetos             recorta los iconos de la tienda de la hoja 'Items' de BW a assets/interfaz/objetos
    python herramientas.py paneles             recorta fondos, botones y paneles de los menus de BW a assets/interfaz/paneles
    python herramientas.py hud                 recorta barras de HP, iconos de estado, la Pokeball y los paneles en flecha de BW a assets/interfaz/hud
    python herramientas.py casas               recorta el jardin, el interior y la bandera de cada choza ('Huts' del Red Rescue Team) para el barrio del refugio
    python herramientas.py arenas              recorta la arena ya dibujada de cada jefe ('Dungeon Boss Rooms' del Red Rescue Team) y guarda su piso
    python herramientas.py estados             recorta los estados animados (llama, Zzz, calavera, pajaritos...) del Red Rescue Team a assets/efectos
    python herramientas.py clima               recorta la lluvia, nieve, granizo, niebla, sol, brasas y sombras de nubes del Red Rescue Team a assets/clima
    python herramientas.py aldea               el arbol suelto, tocon, cerca, matas, flores y las chozas de la plaza ('Huts' del Red Rescue Team)
    python herramientas.py logo                pasa assets/typo_logo_pokemanic.png a assets/interfaz/logo.png (pixeles originales, sin fondo)
    python herramientas.py chispas             estrellitas y brillos de los golpes ('Miscellaneous - Effects' del Red Rescue Team)
    python herramientas.py icono               el icono de Pokemanic.exe (la cara de Celebi) para crear_exe.bat
    python herramientas.py portal              el portal violeta de las escenas ('Dimensional Hole' del Explorers of Time/Darkness)
    python herramientas.py espiritu            el aura redonda del espiritu ('Moonlight' del Explorers of Sky)
    python herramientas.py salas               muestra en texto algunas salas generadas
    python herramientas.py plan                muestra el plan de salas de una partida
    python herramientas.py visor               ventana para mirar salas generadas sin jugar
"""

import json
import math
import os
import random
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import pygame
import datos
from datos import mundos
from mundo import generacion, entorno


# ==================== descargar assets ====================

def herramienta_descargar():
    """Baja de SpriteCollab las animaciones y retratos de cada pokemon a assets/sprites/pokemones."""
    pokemones = datos.pokemones.pokemones

    BASE = 'https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/'
    DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sprites', 'pokemones')
    RETRATOS = ('Normal', 'Pain')
    CARAS = ('Happy', 'Surprised', 'Worried', 'Determined', 'Inspired', 'Joyous', 'Sigh', 'Sad', 'Shouting', 'Teary-Eyed', 'Stunned')   # las de 'caras'
    FORMAS = {'samurott_hisui': '0001', 'dialga_origen': '0001', 'palkia_origen': '0001', 'giratina_origen': '0001', 'arceus_beta': '0019'}
    SALTEAR = ('missigno',)
    SOLO_RETRATO = ('amoonguss', 'brute_bonnet')     # SpriteCollab todavia no tiene sus animaciones: se baja el retrato solo


    def bajar(url, intentos=3):
        """Baja una URL (reintenta unas veces). None si no se pudo."""
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
        """Baja una URL a un archivo si todavia no esta. True si quedo guardado."""
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
        """Baja los sprites (AnimData.xml y hojas) y el retrato de un pokemon desde SpriteCollab."""
        dex = '%04d' % datos['pokedex']
        forma = FORMAS.get(nombre)
        subruta = dex + ('/' + forma if forma else '')
        carpeta = os.path.join(DESTINO, 'sprite_' + nombre)
        if not guardar(BASE + 'sprite/' + subruta + '/AnimData.xml', os.path.join(carpeta, 'AnimData.xml')):
            if nombre in SOLO_RETRATO:                              # sin animaciones: al menos el retrato para los menus
                for emocion in RETRATOS: guardar(BASE + 'portrait/' + subruta + '/' + emocion + '.png', os.path.join(carpeta, 'portrait', emocion + '.png'))
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


    if len(sys.argv) > 2 and sys.argv[1] == 'caras':               # 'caras <pokemon>...': las demas caras del retrato (para las charlas)
        for nombre in sys.argv[2:]:
            carpeta = os.path.join(DESTINO, 'sprite_' + nombre, 'portrait')
            subruta = '%04d' % pokemones[nombre]['pokedex'] + ('/' + FORMAS[nombre] if nombre in FORMAS else '')
            caras = [e for e in CARAS if guardar(BASE + 'portrait/' + subruta + '/' + e + '.png', os.path.join(carpeta, e + '.png'))]
            print(nombre + ':', ', '.join(caras) or 'ninguna')
        return


    def main():
        """Baja todo lo que falta de todos los pokemon, de a varios a la vez."""
        pendientes = [(n, d) for n, d in pokemones.items() if n not in SALTEAR]
        with ThreadPoolExecutor(max_workers=6) as pool:
            for nombre, cantidad, faltan in pool.map(lambda x: descargar(*x), pendientes):
                print(nombre.ljust(18), cantidad, 'animaciones', '| faltan:' if faltan else '', ', '.join(faltan))
        print('listo: ' + DESTINO)
        print('\nanalizando las animaciones y asignandolas a los ataques...')
        herramienta_animaciones()

    main()


# ==================== analizar animaciones ====================

# Que hace cada animacion del PMD (los nombres del AnimData.xml), para leer el reporte sin abrir las hojas.
QUE_HACE_ANIMACION = {
    'idle': 'quieto, respirando', 'walk': 'caminar', 'sleep': 'dormido', 'eventsleep': 'dormido (escena)', 'wake': 'despertarse',
    'hurt': 'recibe un golpe', 'faint': 'se desmaya', 'cringe': 'se encoge del susto', 'attack': 'ataque basico (generico)',
    'strike': 'golpe hacia adelante', 'quickstrike': 'golpe rapido', 'multistrike': 'varios golpes seguidos', 'multiscratch': 'arañazos',
    'punch': 'puñetazo', 'jab': 'pinchazo / picotazo', 'chop': 'golpe de canto (karate)', 'kick': 'patada', 'bite': 'mordida',
    'slam': 'se tira con todo el cuerpo', 'head': 'cabezazo', 'tumble': 'voltereta', 'ricochet': 'rebota y vuelve', 'leapforth': 'salta hacia adelante',
    'tailwhip': 'coletazo', 'swing': 'barrido en arco', 'double': 'dos golpes', 'rotate': 'gira sobre si mismo', 'twirl': 'pirueta',
    'shoot': 'dispara algo hacia adelante', 'spattack': 'ataque especial (carga y suelta)', 'emit': 'emite energia', 'charge': 'carga energia',
    'shock': 'descarga electrica', 'rumble': 'hace temblar el suelo', 'rearup': 'se para en dos patas y embiste', 'sink': 'se hunde en el suelo',
    'hop': 'saltito', 'hover': 'flota en el aire', 'float': 'flota', 'flaparound': 'aletea', 'dance': 'baile', 'pose': 'pose de victoria',
    'nod': 'asiente', 'shake': 'se sacude', 'sit': 'sentado', 'laying': 'acostado', 'eat': 'come', 'lookup': 'mira hacia arriba',
    'hitground': 'golpea el suelo', 'lostbalance': 'pierde el equilibrio', 'pain': 'dolor', 'pull': 'tira de algo', 'trip': 'se tropieza',
    'tumbleback': 'voltereta hacia atras', 'deepbreath': 'respira hondo', 'withdraw': 'se esconde / se cubre', 'sing': 'canta', 'special0': 'especial del pokemon', 'special1': 'especial del pokemon',
}


def herramienta_animaciones(solo=None):
    """Lee el AnimData.xml de cada pokemon, dice que hace cada animacion y que animacion le toca a cada uno de sus ataques
    (la misma eleccion que hace el juego con AnimadorPokemon.buscar_movimiento). Guarda todo en asignacion_animaciones.json.

        solo: nombre de un pokemon para ver solo ese (si no, todos)."""
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')               # no hace falta abrir ventana
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    import sistema
    anim = sistema.animaciones
    pk = datos.pokemones
    raiz = os.path.dirname(os.path.abspath(__file__))
    os.chdir(raiz)                                                   # el juego busca los sprites en assets/... relativo a la carpeta
    DESTINO = os.path.join(raiz, 'asignacion_animaciones.json')
    genericas = set(anim.AnimadorPokemon.nombres_ataque) | {n for t in anim.AnimadorPokemon.nombres_forma.values() for n in t}

    def leer_xml(carpeta):
        """Animaciones del AnimData.xml: nombre -> (cantidad de frames, de quien es copia o None)."""
        hojas = {}
        try: raiz_xml = ET.parse(os.path.join(carpeta, 'AnimData.xml')).getroot()
        except (OSError, ET.ParseError): return None
        for a in raiz_xml.find('Anims').findall('Anim'):
            nombre = a.findtext('Name')
            if not nombre: continue
            copia = a.findtext('CopyOf')
            frames = len(a.find('Durations').findall('Duration')) if a.find('Durations') is not None else 0
            hojas[anim._normalizar_nombre(nombre)] = (frames, anim._normalizar_nombre(copia) if copia else None)
        return hojas

    def origen(animador, movimiento, tipo, forma, elegida):
        """Por que se eligio esa animacion: por el nombre del ataque, por su tipo, por su forma o la generica."""
        nombre = anim._normalizar_nombre(movimiento or '')
        for clave, anims in anim.ANIM_MOVIMIENTO:
            if clave in nombre and any(a in animador.sprites for a in anims):
                return 'nombre (' + clave + ')'
        if any(a in animador.sprites for a in anim.ANIM_TIPO.get(tipo, {}).get(forma, ())): return 'tipo (' + str(tipo) + ')'
        if elegida is None: return 'ninguna'
        if elegida in anim.AnimadorPokemon.nombres_forma.get(forma, ()): return 'forma (' + str(forma) + ')'
        return 'generica'

    reporte, sin_xml, a_mano, usadas_total = {}, [], [], {}
    nombres = [solo] if solo else sorted(pk.pokemones)
    for nombre in nombres:
        if nombre not in pk.pokemones:
            print('no existe el pokemon', nombre); return
        carpeta = anim._buscar_carpeta(anim._base(anim._normalizar_nombre(nombre)))
        hojas = leer_xml(carpeta) if carpeta else None
        if not hojas:
            sin_xml.append(nombre); continue
        animador = object.__new__(anim.AnimadorPokemon)                # sin cargar las hojas: solo hace falta saber cuales tiene
        animador.sprites = dict.fromkeys(hojas)
        juego = pk.datos_juego(nombre)
        ataques = [(n, pk.buscar_movimiento(n)) for n in juego['basicos'] if n] + list(juego['especiales'])
        asignadas = {}
        for mov, d in ataques:
            d = d or {}
            tipo, forma = d.get('tipo'), d.get('forma', 'proyectil')
            elegida = animador.buscar_movimiento(mov, tipo, forma)
            como = origen(animador, mov, tipo, forma, elegida)
            asignadas[mov] = {'animacion': elegida, 'por': como, 'tipo': tipo, 'forma': forma,
                              'que_hace': QUE_HACE_ANIMACION.get(elegida, '?') if elegida else None}
            usadas_total[elegida] = usadas_total.get(elegida, 0) + 1
            if como in ('generica', 'ninguna'): a_mano.append((nombre, mov, elegida))
        especiales = sorted(a for a in hojas if a not in genericas and a not in anim.AnimadorPokemon.RITMO_XML and a not in ('idle', 'walk'))
        sin_usar = [a for a in especiales if a not in {v['animacion'] for v in asignadas.values()}]
        reporte[nombre] = {'animaciones': {a: {'frames': f, 'copia_de': c, 'que_hace': QUE_HACE_ANIMACION.get(a, '?')} for a, (f, c) in sorted(hojas.items())},
                           'ataques': asignadas, 'especiales_sin_usar': sin_usar}

        print('\n' + nombre.upper() + '  (' + str(len(hojas)) + ' animaciones)')
        for mov, v in asignadas.items():
            print('   ' + mov.ljust(22) + '-> ' + str(v['animacion']).ljust(13) + ('[' + v['por'] + ']').ljust(24) + (v['que_hace'] or ''))
        if sin_usar: print('   especiales que no usa ningun ataque:', ', '.join(sin_usar))

    if solo and nombres[0] in sin_xml: print(solo, 'no tiene AnimData.xml (corre: python herramientas.py descargar)'); return
    print('\n==================== resumen ====================')
    print('pokemon analizados:', len(reporte), '| sin AnimData.xml:', len(sin_xml), ('(' + ', '.join(sin_xml) + ')') if sin_xml else '')
    print('animaciones usadas por los ataques:', ', '.join(a + ' x' + str(c) for a, c in sorted(usadas_total.items(), key=lambda x: -x[1]) if a))
    if a_mano:
        print('ataques que quedaron con la animacion generica (para sumar a ANIM_MOVIMIENTO o ANIM_TIPO en sistema.py):', len(a_mano))
        for nombre, mov, elegida in a_mano[:40]: print('   ', nombre.ljust(18), mov.ljust(22), elegida)
        if len(a_mano) > 40: print('    ... y', len(a_mano) - 40, 'mas (ver el json)')
    if not solo:
        with open(DESTINO, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, ensure_ascii=False, indent=1)
        print('guardado:', DESTINO)


# ==================== sonidos ====================

def herramienta_sonidos():
    """Baja el grito de cada pokemon (los de PokeAPI: github.com/PokeAPI/cries) a assets/sonidos/gritos/<nombre>.ogg.
    Usa el grito clasico (el de los juegos de DS) si existe, y si no el actual. Los que ya estan no se vuelven a bajar."""
    pokemones = datos.pokemones.pokemones
    BASE = 'https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/'
    DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'sonidos', 'gritos')
    os.makedirs(DESTINO, exist_ok=True)

    def bajar(url):
        """Baja una URL (None si falla)."""
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'pokemanic-sonidos'}), timeout=30) as r: return r.read()
        except (urllib.error.URLError, OSError): return None

    def uno(nombre):
        """Baja el grito de un pokemon."""
        ruta = os.path.join(DESTINO, nombre + '.ogg')
        if os.path.isfile(ruta): return nombre, 'ya estaba'
        dex = pokemones[nombre].get('pokedex')
        if not isinstance(dex, int): return nombre, 'sin numero de pokedex'
        for version in ('legacy', 'latest'):
            datos_ = bajar(BASE + version + '/' + str(dex) + '.ogg')
            if datos_:
                with open(ruta, 'wb') as f: f.write(datos_)
                return nombre, version
        return nombre, 'no esta'

    with ThreadPoolExecutor(max_workers=6) as pool:
        resultados = list(pool.map(uno, sorted(pokemones)))
    cuenta = {}
    for nombre, como in resultados: cuenta[como] = cuenta.get(como, 0) + 1
    faltan = [n for n, como in resultados if como in ('no esta', 'sin numero de pokedex')]
    print('gritos:', ', '.join(k + ' ' + str(v) for k, v in sorted(cuenta.items())))
    if faltan: print('sin grito:', ', '.join(faltan))
    print('listo: ' + DESTINO)


# ==================== generar datos ====================

def herramienta_datos():
    """Pide a la PokeAPI stats, movimientos, descripcion y evoluciones y los guarda en datos_pokeapi.json."""
    pokemones = datos.pokemones.pokemones

    CAMBIOS = {'samurott_hisui': 'samurott-hisui', 'meowstic': 'meowstic-male', 'lycanroc': 'lycanroc-midday', 'aegislash': 'aegislash-shield',
               'dialga_origen': 'dialga-origin', 'palkia_origen': 'palkia-origin', 'giratina_origen': 'giratina-origin'}
    SALTAR = ('arceus_beta', 'missigno')
    ESPEJO = 'https://raw.githubusercontent.com/PokeAPI/api-data/master/data'   # la misma PokeAPI guardada en GitHub (si pokeapi.co no responde)
    _indices = {}


    def _json(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'pokemanic'}), timeout=20) as r:
            return json.loads(r.read().decode('utf-8'))


    def _por_espejo(url):
        """La misma pagina desde el espejo de GitHub: ahi todo esta por numero, asi que los nombres se buscan en el indice."""
        ruta = url.split('/api/v2/', 1)[1].strip('/')
        recurso, clave = ruta.split('/', 1)
        if not clave.isdigit():
            if recurso not in _indices:
                _indices[recurso] = {r['name']: r['url'].strip('/').rsplit('/', 1)[1] for r in _json(ESPEJO + '/api/v2/' + recurso + '/index.json')['results']}
            clave = _indices[recurso][clave]
        return _json(ESPEJO + '/api/v2/' + recurso + '/' + clave + '/index.json')


    def pedir(url):
        """JSON de la PokeAPI (una URL completa o el nombre de un pokemon). Si pokeapi.co no responde, usa el espejo de GitHub."""
        if url.startswith('/api/v2/'): url = 'https://pokeapi.co' + url        # el espejo guarda los enlaces sin el dominio
        elif not url.startswith('http'):
            url = 'https://pokeapi.co/api/v2/pokemon/' + url
        if not _indices.get('_sin_api'):
            try: return _json(url)
            except Exception: _indices['_sin_api'] = True              # no responde: de aca en adelante, directo al espejo
        return _por_espejo(url)


    def como_evoluciona(hijo):
        """Nivel, piedra u otra condicion para evolucionar a ese hijo de la cadena."""
        d = (hijo.get('evolution_details') or [{}])[0]
        return {'a': hijo['species']['name'], 'disparador': (d.get('trigger') or {}).get('name'), 'nivel': d.get('min_level'),
                'objeto': (d.get('item') or {}).get('name'), 'amistad': d.get('min_happiness')}


    def buscar_cadena(nodo, objetivo, padre=None):
        """Busca a un pokemon en su cadena evolutiva: (de quien viene, a quienes evoluciona, como)."""
        if nodo['species']['name'] == objetivo:
            return padre, [n['species']['name'] for n in nodo['evolves_to']], [como_evoluciona(n) for n in nodo['evolves_to']]
        for hijo in nodo['evolves_to']:
            r = buscar_cadena(hijo, objetivo, nodo['species']['name'])
            if r:
                return r
        return None


    def descripcion(especie):
        """Texto de la pokedex en castellano (o en ingles si no hay)."""
        textos = [t['flavor_text'] for t in especie['flavor_text_entries'] if t['language']['name'] == 'es']
        if not textos:
            textos = [t['flavor_text'] for t in especie['flavor_text_entries'] if t['language']['name'] == 'en']
        return ' '.join(textos[-1].replace('\n', ' ').replace('\f', ' ').split()) if textos else None


    def main():
        """Arma datos_pokeapi.json con stats, movimientos, evoluciones y descripciones de todos los pokemon.
        Conserva lo que ya estaba: solo pide los que faltan (con 'python herramientas.py datos todo' pide todos de nuevo)."""
        todo = len(sys.argv) > 2 and sys.argv[2] == 'todo'
        salida = {}
        if not todo and os.path.isfile('datos_pokeapi.json'):
            with open('datos_pokeapi.json', encoding='utf-8') as f: salida = json.load(f)
        for nombre in pokemones:
            if nombre in SALTAR or (nombre in salida and not todo): continue
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

    main()


# ==================== recortar assets ====================

def herramienta_recortar(ruta):
    """Para recortar sprites de una hoja (por ejemplo de The Spriters Resource) y dejarlos donde el juego los busca.

        python herramientas.py recortar ruta/a/la/hoja.png

        clic izquierdo y arrastrar   marcar el sprite (se recorta solo al borde del dibujo)
        escribir                     nombre del objeto o terreno (TAB completa con la primera sugerencia)
        ENTER                        guardar en assets/mundo/[era/]<objetos|terrenos>/<nombre>.png
        F1                           objetos / terrenos            F2   para todas las eras o solo una
        B y clic                     elegir el color de fondo (se vuelve transparente). Arranca con el de la esquina
        rueda                        zoom          clic derecho y arrastrar   moverse por la hoja
        ESC                          salir

    A la derecha se ve la lista de lo que todavia no tiene sprite.
    """
    W, H = 1280, 760
    PANEL = 330


    def main(ruta):
        """Ventana para recortar a mano sprites de una hoja y guardarlos como objetos o terrenos del mundo."""
        pygame.init()
        ventana = pygame.display.set_mode((W, H))
        pygame.display.set_caption('Recortar assets - ' + os.path.basename(ruta))
        hoja = pygame.image.load(ruta).convert_alpha()
        fuente, chica = pygame.font.Font(None, 26), pygame.font.Font(None, 19)
        fondo = hoja.get_at((0, 0))                                 # color de fondo de la hoja
        zoom, vista = 2.0, [0.0, 0.0]
        seleccion, arrastre, paneo, eligiendo_fondo = None, None, None, False
        nombre, tipo, iera, mensaje = '', 'objetos', 0, ''
        eras = [None] + [e['clave'] for e in mundos.ERAS]
        reloj = pygame.time.Clock()

        def a_hoja(pos):
            """De pixeles de la ventana a pixeles de la hoja (segun zoom y desplazamiento)."""
            return int((pos[0] + vista[0]) / zoom), int((pos[1] + vista[1]) / zoom)

        def recorte():
            """La seleccion achicada al borde del dibujo, con el fondo transparente."""
            if not seleccion or seleccion.width < 1 or seleccion.height < 1: return None
            pedazo = hoja.subsurface(seleccion.clip(hoja.get_rect())).copy()
            for x in range(pedazo.get_width()):
                for y in range(pedazo.get_height()):
                    if pedazo.get_at((x, y))[:3] == fondo[:3]: pedazo.set_at((x, y), (0, 0, 0, 0))
            borde = pedazo.get_bounding_rect()
            return pedazo.subsurface(borde).copy() if borde.width and borde.height else None

        def nombres_conocidos():
            """Nombres de objetos o terrenos que ya usa el juego (para sugerirlos al guardar)."""
            return sorted(mundos.OBJETOS) if tipo == 'objetos' else sorted(mundos.TERRENOS)

        while True:
            sugerencias = [n for n in nombres_conocidos() if n.startswith(nombre)][:8] if nombre else []
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: pygame.quit(); return
                    elif e.key == pygame.K_F1: tipo = 'terrenos' if tipo == 'objetos' else 'objetos'
                    elif e.key == pygame.K_F2: iera = (iera + 1) % len(eras)
                    elif e.key == pygame.K_TAB and sugerencias: nombre = sugerencias[0]
                    elif e.key == pygame.K_BACKSPACE: nombre = nombre[:-1]
                    elif e.key == pygame.K_b and not nombre: eligiendo_fondo = True; mensaje = 'clic en el color de fondo'
                    elif e.key == pygame.K_RETURN:
                        img = recorte()
                        if img and nombre:
                            carpeta = os.path.join(entorno.CARPETA_ASSETS, *([eras[iera]] if eras[iera] else []), tipo)
                            os.makedirs(carpeta, exist_ok=True)
                            pygame.image.save(img, os.path.join(carpeta, nombre + '.png'))
                            mensaje = 'guardado ' + os.path.join(*([eras[iera]] if eras[iera] else []), tipo, nombre + '.png')
                            entorno._imagenes.clear()
                            nombre = ''
                        else: mensaje = 'falta marcar el sprite o escribir el nombre'
                    elif e.unicode and (e.unicode.isalnum() or e.unicode in '_ñ'): nombre += e.unicode.lower()
                if e.type == pygame.MOUSEWHEEL:
                    antes = a_hoja(pygame.mouse.get_pos())
                    zoom = max(0.5, min(8.0, zoom * (1.25 if e.y > 0 else 0.8)))
                    mx, my = pygame.mouse.get_pos()
                    vista = [antes[0] * zoom - mx, antes[1] * zoom - my]  # el zoom se centra en el mouse
                if e.type == pygame.MOUSEBUTTONDOWN and e.pos[0] < W - PANEL:
                    if e.button == 1 and eligiendo_fondo:
                        x, y = a_hoja(e.pos)
                        if hoja.get_rect().collidepoint(x, y): fondo = hoja.get_at((x, y)); mensaje = 'fondo: ' + str(tuple(fondo)[:3])
                        eligiendo_fondo = False
                    elif e.button == 1: arrastre = a_hoja(e.pos)
                    elif e.button == 3: paneo = (e.pos, list(vista))
                if e.type == pygame.MOUSEBUTTONUP:
                    if e.button == 1 and arrastre:
                        x, y = a_hoja(e.pos)
                        seleccion = pygame.Rect(min(x, arrastre[0]), min(y, arrastre[1]), abs(x - arrastre[0]) + 1, abs(y - arrastre[1]) + 1)
                        arrastre = None
                    if e.button == 3: paneo = None
                if e.type == pygame.MOUSEMOTION and paneo:
                    vista = [paneo[1][0] - (e.pos[0] - paneo[0][0]), paneo[1][1] - (e.pos[1] - paneo[0][1])]

            ventana.fill((40, 40, 46))
            grande = pygame.transform.scale(hoja, (round(hoja.get_width() * zoom), round(hoja.get_height() * zoom)))
            ventana.blit(grande, (-vista[0], -vista[1]))
            marco = None
            if arrastre:
                x, y = a_hoja(pygame.mouse.get_pos())
                marco = pygame.Rect(min(x, arrastre[0]), min(y, arrastre[1]), abs(x - arrastre[0]) + 1, abs(y - arrastre[1]) + 1)
            elif seleccion: marco = seleccion
            if marco:
                pygame.draw.rect(ventana, (255, 60, 60), (marco.x * zoom - vista[0], marco.y * zoom - vista[1], marco.width * zoom, marco.height * zoom), 2)
            pygame.draw.rect(ventana, (22, 22, 26), (W - PANEL, 0, PANEL, H))       # panel derecho
            x, y = W - PANEL + 12, 12
            textos = [('Destino: ' + tipo + ('  (' + eras[iera] + ')' if eras[iera] else '  (todas las eras)'), fuente),
                      ('Nombre: ' + nombre + '_', fuente), ('F1 tipo  F2 era  TAB completar  ENTER guardar', chica), (mensaje, chica)]
            for t, f in textos:
                ventana.blit(f.render(t, True, (235, 235, 235)), (x, y)); y += f.get_height() + 6
            pygame.draw.rect(ventana, fondo, (x, y, 18, 18)); ventana.blit(chica.render('color de fondo (B para cambiar)', True, (200, 200, 200)), (x + 26, y + 2)); y += 30
            img = recorte()
            if img:                                                 # vista previa del recorte
                escala = min(4, 150 / max(img.get_size()))
                prev = pygame.transform.scale(img, (max(1, round(img.get_width() * escala)), max(1, round(img.get_height() * escala))))
                pygame.draw.rect(ventana, (70, 70, 80), (x, y, 160, 160)); ventana.blit(prev, prev.get_rect(center=(x + 80, y + 80)))
                ventana.blit(chica.render(str(img.get_width()) + 'x' + str(img.get_height()) + ' px', True, (200, 200, 200)), (x + 170, y + 70))
            y += 170
            for s in sugerencias: ventana.blit(chica.render('> ' + s, True, (250, 220, 120)), (x, y)); y += 18
            if not sugerencias:                                     # lo que todavia no tiene sprite
                faltan = [n for n in nombres_conocidos() if not entorno.imagen(tipo, n, eras[iera])]
                ventana.blit(chica.render('Sin sprite (' + str(len(faltan)) + '):', True, (200, 200, 200)), (x, y)); y += 20
                for n in faltan[:(H - y) // 17]: ventana.blit(chica.render(n, True, (160, 160, 160)), (x, y)); y += 17
            pygame.display.flip(); reloj.tick(60)

    main(ruta)


# ==================== visor de mundos ====================

def herramienta_visor():
    """Para mirar salas generadas sin jugar.

        python herramientas.py visor

    Teclas:
        <- / ->     cambiar de era               arriba / abajo   cambiar de variante
        T           combate / tienda / arena     ESPACIO          otra semilla (otra sala)
        C           probar los climas            P                ver el plan de una partida
        S           guardar captura (visor_XXXX.png)   ESC        salir
    """
    W, H = 1180, 720
    PANEL = 300                                  # ancho del panel de texto de la derecha
    TIPOS = ('combate', 'tienda', 'arena')
    CLIMAS = [None] + list(entorno.CLIMAS)


    def generar(era, variante, tipo, semilla):
        """Sala y su entorno segun lo elegido en el visor."""
        if tipo == 'tienda': sala = generacion.generar_tienda(era, ['oeste', 'este'], semilla)
        elif tipo == 'arena': sala = generacion.generar_arena(era, ['norte'], semilla)
        else:
            azar = random.Random(semilla)
            entrada = azar.choice(generacion.LADOS)
            salidas = azar.sample([l for l in generacion.LADOS if l != entrada], azar.randint(1, 3))
            sala = generacion.generar_sala(era, variante, entrada, salidas, semilla)
        return sala, entorno.crear(sala)


    def main():
        """Ventana para mirar salas generadas de cualquier era y variante sin jugar."""
        pygame.init()
        ventana = pygame.display.set_mode((W, H))
        pygame.display.set_caption('Pokemanic - visor de mundos')
        fuente, chica = pygame.font.Font(None, 26), pygame.font.Font(None, 20)
        era, ivar, itipo, iclima, semilla = 0, 0, 0, 0, random.randrange(10 ** 6)
        ver_plan = False
        rec = mundos.nuevo_recorrido()
        sala, ent = None, None
        reloj = pygame.time.Clock()
        while True:
            variantes = list(mundos.ERAS[era]['variantes'])
            ivar %= len(variantes)
            if sala is None:
                sala, ent = generar(era, variantes[ivar], TIPOS[itipo], semilla)
                if CLIMAS[iclima]: entorno.iniciar_clima(ent, CLIMAS[iclima], 0, None)
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): pygame.quit(); return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RIGHT: era = (era + 1) % len(mundos.ERAS); ivar = 0
                    elif e.key == pygame.K_LEFT: era = (era - 1) % len(mundos.ERAS); ivar = 0
                    elif e.key == pygame.K_DOWN: ivar += 1
                    elif e.key == pygame.K_UP: ivar -= 1
                    elif e.key == pygame.K_t: itipo = (itipo + 1) % len(TIPOS)
                    elif e.key == pygame.K_SPACE: semilla = random.randrange(10 ** 6)
                    elif e.key == pygame.K_c: iclima = (iclima + 1) % len(CLIMAS)
                    elif e.key == pygame.K_p: ver_plan = not ver_plan; rec = mundos.nuevo_recorrido()
                    elif e.key == pygame.K_s:
                        nombre = 'visor_' + str(semilla) + '.png'
                        pygame.image.save(ventana, nombre); print('guardado', nombre)
                        continue
                    else: continue
                    sala = None                                     # cambio algo: se regenera
            if sala is None: continue
            ventana.fill((15, 15, 18))
            lienzo = pygame.Surface(sala['esc'].size)              # la sala entera a tamaño real y despues se achica
            ahora = pygame.time.get_ticks()
            entorno.dibujar(ent, lienzo, 0, 0, ahora)
            for puerta in sala['puertas']: pygame.draw.rect(lienzo, (60, 180, 80), puerta['rect'])
            pygame.draw.circle(lienzo, (255, 60, 255), [round(v) for v in sala['inicio']], 18)      # donde aparece el jugador
            entorno.dibujar_clima(ent, lienzo, ahora)
            escala = min((W - PANEL - 20) / lienzo.get_width(), (H - 20) / lienzo.get_height())
            chico = pygame.transform.smoothscale(lienzo, (round(lienzo.get_width() * escala), round(lienzo.get_height() * escala)))
            ventana.blit(chico, (10, 10))
            x = W - PANEL + 10                                      # panel con los datos de la sala
            lineas = [(mundos.ERAS[era]['nombre'], fuente, mundos.ERAS[era]['suelo']), ('Regi: ' + mundos.ERAS[era]['regi'], chica, None),
                      ('Variante: ' + (variantes[ivar] if TIPOS[itipo] == 'combate' else TIPOS[itipo]), chica, None),
                      ('Forma: ' + sala.get('forma', '-') + '   simetria: ' + sala.get('simetria', '-'), chica, None),
                      ('Interior' if sala.get('interior') else 'Exterior', chica, None),
                      ('Clima: ' + (CLIMAS[iclima] or 'ninguno (C para probar)'), chica, None),
                      ('Objetos: ' + str(len(sala['objetos'])) + '   semilla ' + str(semilla), chica, None),
                      ('Piezas: ' + (', '.join(sala.get('piezas', [])) or '-'), chica, None), ('', chica, None)]
            lineas += [(t, chica, (170, 170, 170)) for t in ('<- -> era    arriba/abajo variante', 'T tipo de sala   ESPACIO otra', 'C clima   P plan   S captura')]
            y = 14
            for texto, f, color in lineas:
                for parte in [texto[i:i + 40] for i in range(0, max(1, len(texto)), 40)]:
                    ventana.blit(f.render(parte, True, color or (235, 235, 235)), (x, y)); y += f.get_height() + 4
            if ver_plan:                                            # plan de una partida: T tienda, S subjefe, J semijefe, R regi, A arceus
                y += 10
                letras = {'combate': '.', 'tienda': 'T', 'subjefe': 'S', 'jefe': 'J', 'regi': 'R', 'final': 'A'}
                for i, plan in enumerate(rec['plan']):
                    ventana.blit(chica.render(mundos.ERAS[i]['clave'][:8].ljust(9) + ''.join(letras[t] for t in plan), True, (220, 220, 140)), (x, y)); y += 18
            pygame.display.flip(); reloj.tick(30)

    main()


# ==================== pruebas ====================

# ==================== bajar las hojas de spriters-resource ====================

def herramienta_hojas():
    """Baja todas las hojas (menos los pokemon) de los 4 juegos a assets/hojas/<juego>/<seccion>/.
    spriters-resource tiene un Cloudflare que no deja bajar nada automatico, asi que se usa la copia del Wayback Machine (archive.org)."""
    import gzip, html, re
    raiz = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(raiz, 'assets', 'hojas')
    ARCHIVO = 'https://web.archive.org/web/2026id_/https://www.spriters-resource.com'      # id_: la imagen original tal cual
    PAGINAS = 'https://web.archive.org/web/2026/https://www.spriters-resource.com'         # las paginas sin id_: el archivo las guarda en zstd y asi las da ya abiertas
    JUEGOS = {'blanco_negro': '/ds_dsi/pokemonblackwhite/', 'red_rescue': '/game_boy_advance/pokemonmysterydungeonredrescueteam/',
              'time_darkness': '/ds_dsi/pokemonmysterydungeonexplorersoftimedarkness/', 'sky': '/ds_dsi/pokemonmysterydungeonexplorersofsky/'}

    def pedir(url, intentos=4):
        """Baja una URL (con reintentos) por archive.org."""
        for i in range(intentos):
            try:
                pedido = urllib.request.Request(url, headers={'User-Agent': 'pokemanic-hojas', 'Accept-Encoding': 'gzip'})
                with urllib.request.urlopen(pedido, timeout=60) as r:
                    datos = r.read()
                    return gzip.decompress(datos) if r.headers.get('Content-Encoding') == 'gzip' else datos
            except urllib.error.HTTPError as e:
                if e.code == 404: return None
            except Exception:
                pass
            time.sleep(3 * (i + 1))                                       # archive.org a veces corta: espera y reintenta
        return None

    def limpio(texto):
        """Nombre de archivo sin caracteres que Windows no acepta."""
        return re.sub(r'[<>:"/\\|?*]', '', texto).strip()[:80]

    def catalogo(pagina):
        """[(seccion, id, nombre, carpeta)] de la pagina del juego, sin las secciones de pokemon."""
        s = pedir(PAGINAS + pagina).decode('utf-8', 'replace')
        s = s[s.find('<div id="asset-display">'):]
        salida = []
        for parte in re.split(r'<div class="section text-shadow[^"]*" id="section-\d+">', s)[1:]:
            seccion = html.unescape(re.sub(r'<[^>]+>|arrow_drop_down|\[\d+\]', '', parte.split('</div>', 1)[0]).strip())
            if seccion.lower().startswith('pok') and 'mon' in seccion.lower() and 'square' not in seccion.lower(): continue   # los pokemon salen del PMDCollab
            for i, nombre, carpeta in re.findall(r'/asset/(\d+)/" class="iconlink">.*?title="([^"]*)".*?/media/asset_icons/(\d+)/', parte, re.S):
                salida.append((seccion, i, html.unescape(nombre), carpeta))
        return salida

    def guardada(ruta, crudo=True):
        """Direccion de la copia que tiene archive.org (o None). Se pregunta a su API antes de bajar: asi no se le pide de mas."""
        r = pedir('https://archive.org/wayback/available?url=spriters-resource.com' + ruta)
        try: copia = json.loads(r)['archived_snapshots'].get('closest') if r else None
        except ValueError: copia = None
        if not copia or copia.get('status') != '200': return None
        return re.sub(r'/web/(\d+)/', r'/web/\1id_/', copia['url'], count=1) if crudo else copia['url']

    def bajar(juego, pagina, seccion, i, nombre, carpeta):
        """Baja una hoja de spriters-resource (por archive.org) si todavia no esta."""
        lugar = os.path.join(destino, juego, limpio(seccion))
        for ext in ('.png', '.zip', '.gif'):
            if os.path.isfile(os.path.join(lugar, limpio(nombre) + ext)): return 'ya estaba'
        url, ext = guardada('/media/assets/' + carpeta + '/' + i + '.png'), '.png'
        if not url:                                                       # no es png (zip, gif): el link real esta en la pagina del asset
            p = guardada(pagina + 'asset/' + i + '/', crudo=False)
            p = pedir(p) if p else None
            m = re.search(r'/media/assets/\d+/' + i + r'\.(\w+)', p.decode('utf-8', 'replace')) if p else None
            if m: url, ext = guardada(m.group(0)), '.' + m.group(1)
        datos = pedir(url) if url else None
        if not datos or datos[:15].lower().startswith(b'<!doctype'): return 'no esta en el archivo'
        os.makedirs(lugar, exist_ok=True)
        with open(os.path.join(lugar, limpio(nombre) + ext), 'wb') as f: f.write(datos)
        return 'ok'

    def main():
        """Baja todas las hojas de BW y los PMD que faltan a assets/hojas."""
        faltan = []
        for juego, pagina in JUEGOS.items():
            lista = catalogo(pagina)
            print('==', juego, len(lista), 'hojas')
            for seccion, i, nombre, carpeta in lista:                     # de a una y con pausa: es un servicio gratis
                r = bajar(juego, pagina, seccion, i, nombre, carpeta)
                if r == 'ya estaba': continue
                print('  ', seccion, '/', nombre, '->', r)
                if r != 'ok': faltan.append(juego + ' | ' + seccion + ' | ' + nombre + ' | https://www.spriters-resource.com' + pagina + 'asset/' + i + '/')
                time.sleep(1.5)
        with open(os.path.join(destino, 'faltan.txt'), 'w', encoding='utf-8') as f: f.write('\n'.join(faltan))   # para bajarlas a mano
        print('listo:', destino, '- faltan', len(faltan), '(lista en faltan.txt)')

    main()


# ==================== tiles de las mazmorras del PMD ====================

def herramienta_tiles():
    """Recorta las hojas de tiles de las mazmorras del PMD (Explorers of Sky 'Dungeon Tiles' y Time/Darkness 'Dungeons', de spriters-resource)
    y arma un tileset con bordes por terreno: assets/mundo/<carpeta>/terrenos/<terreno>.png + <terreno>.json (como los lee mundo.entorno).

    Todas las hojas tienen la misma grilla: casillas de 24 px separadas por una linea de 1 px desde (9, 163), 23 filas,
    y grupos de 3 columnas: Legend, Walls, Wall Alt 1, Wall Alt 2, Ground, Ground Alt 1, Ground Alt 2, (Unused Ground), Water, (Water Sparkle).
    La columna Legend dice para cada casilla que vecinos son del mismo terreno (3x3 cuadraditos, negro = igual): es un autotile.
    El juego mira los 8 vecinos de cada casilla y elige la pieza que coincide, asi salen los bordes, las esquinas y las orillas.
    El agua del PMD se anima cambiando colores: la grilla 'Water palette' de la hoja tiene una fila de colores por frame,
    y los brillos ('Water Sparkle', magenta = transparente) son otra capa con su propia paleta.

    Por terreno queda:
        <terreno>.png         las 3 columnas x 23 filas del grupo (72x552) y a la derecha sus variantes (Alt 1, Alt 2) si tiene
        <terreno>_brillo.png  los brillos del agua (si la hoja los tiene)
        <terreno>.json        mascaras de vecinos, que casillas tiene cada variante, paletas y velocidades
    Carpetas: '' sirve para todas las eras, '<era>' para una era y '<era>/<variante>' para una variante de sala ('tienda' para la tienda)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    base = lambda hoja: {'pared': (hoja, 'pared'), 'suelo': (hoja, 'suelo'), 'agua': (hoja, 'agua')}
    # carpeta -> {terreno: (lugar de la hoja, grupo)}. Grupos: pared, suelo o agua (en algunas hojas el 'agua' es lava o un vacio)
    PLAN = {
        '': {'arena': ('Side Path', 'suelo'), 'nieve': ('7th Station Pass', 'suelo'), 'hielo': ('7th Station Pass', 'agua'),
             'escarcha': ('7th Station Pass', 'agua'), 'hierba': ('4th Station Pass', 'pared'), 'lodo': ('Deep Dusk Forest 01F - 06F', 'suelo'),
             'toxico': ('Brine Cave', 'agua'), 'sombra': ('Dark Wasteland', 'suelo'), 'agua': ('4th Station Pass', 'agua'),
             'vacio': ('Chasm Cave B01F - B04F', 'pared'), 'ceniza': ('Barren Valley', 'suelo'), 'roca_volcanica': ('Deep Boulder Quarry', 'suelo'),
             'torre_dragon': ('Temporal Tower', 'suelo'),          # (el charco no lleva tileset: es agua quieta sobre el piso de la era, ver mundo.py)
             # no hay hojas con lava, aceite ni arena movediza: el agua animada del PMD con otros colores (ver RETOQUES)
             'lava': ('Brine Cave', 'agua', 'lava'), 'aceite': ('Brine Cave', 'agua', 'aceite'), 'arena_movediza': ('Shimmer Desert', 'agua', 'arena'),
             'corriente': ('4th Station Pass', 'agua', 'viento'),
             'abismo': ('World Abyss B16F - B30F', 'suelo')},          # arena de Giratina, Dialga y Palkia origen (fase 2 de Arceus Beta)
        'glaciacion': dict(base('Vast Ice Mountain'), agua=('Ice Aegis Cave', 'agua')),
        'glaciacion/cueva de hielo': base('Ice Aegis Cave'),
        'glaciacion/glaciar': base('Vast Ice Mountain Peak'),
        'glaciacion/grieta': base('Dark Ice Mountain'),
        'glaciacion/tundra': base('Icicle Forest'),
        'piedra': base('Tiny Meadow'),
        'piedra/aldea de cazadores': base('Forest Path'),
        'piedra/cueva rupestre': base('Limestone Cavern'),
        'piedra/valle volcanico': base('Barren Valley'),
        'piedra/rio': base('Drenched Bluff'),
        'metales': base('Deep Boulder Quarry'),
        'metales/mina de cobre': base('Deep Limestone Cavern'),
        'metales/mercado': base('Shimmer Desert'),
        'metales/templo de bronce': base('Temporal Tower'),
        'metales/puerto antiguo': base('Craggy Coast'),
        'medieval': base('4th Station Pass'),
        'medieval/patio del castillo': base('Temporal Tower'),
        'medieval/bosque encantado': base('Apple Woods'),
        'medieval/mazmorra': base('Deep Sealed Ruin'),
        'medieval/foso del castillo': base('Temporal Tower'),
        'medieval/guarida del dragon': base('Dark Wasteland'),
        'moderna': base('Temporal Tower (In the Future of Darkness)'),
        'moderna/fabrica': base('Temporal Spire (In the Future of Darkness)'),
        'moderna/plaza': base('Lush Prairie'),
        'moderna/callejon': base('Spacial Cliffs'),
        'moderna/central electrica': base('Amp Plains'),
        'moderna/alcantarilla': base('Brine Cave'),
        'origen': base('The Nightmare'),
        'tienda': {'pared': ('Temporal Tower', 'pared'), 'suelo': ('Temporal Tower', 'suelo')},
    }
    # cada cuantos frames (a 60 por segundo) cambian los colores del agua y de los brillos: lo dice cada hoja abajo de la paleta
    VELOCIDAD = {'Beach Cave': (20, 4), 'Tiny Meadow': (12, 8), '4th Station Pass': (10, 8), '7th Station Pass': (12, 8), 'Ice Aegis Cave': (12, 14),
                 'Forest Path': (17, 13), 'Limestone Cavern': (13, 8), 'Deep Boulder Quarry': (13, 13), 'Temporal Tower': (18, 8), 'Side Path': (12, 8),
                 'Apple Woods': (17, 9), 'Lush Prairie': (12, 8), 'Amp Plains': (18, 6), 'Brine Cave': (18, 6), 'Deep Limestone Cavern': (13, 8),
                 'Shimmer Desert': (12, 8), 'Murky Forest': (16, 8), 'Craggy Coast': (16, 8), 'Drenched Bluff': (16, 8)}
    # retoques de color: el brillo de cada color (0 oscuro, 1 claro) se pasa a esta escala de colores. Se aplica al dibujo, a los brillos
    # y a las paletas del agua, asi la lava sigue animada como el agua del PMD
    RETOQUES = {'lava': ((0, (60, 8, 0)), (0.35, (170, 30, 0)), (0.6, (240, 100, 10)), (0.85, (255, 200, 60)), (1, (255, 250, 200))),
                'aceite': ((0, (8, 6, 10)), (0.5, (38, 32, 30)), (0.8, (90, 80, 96)), (1, (210, 200, 230))),
                'arena': ((0, (90, 60, 25)), (0.5, (165, 126, 70)), (0.8, (212, 178, 110)), (1, (240, 222, 170))),
                'viento': ((0, (150, 190, 210)), (0.5, (196, 228, 244)), (1, (252, 255, 255)))}
    BITS = (128, 1, 2, 64, 0, 4, 32, 16, 8)       # cuadraditos de la leyenda (de arriba a la izquierda) -> bit: N=1 NE=2 E=4 SE=8 S=16 SO=32 O=64 NO=128
    MAGENTA = (255, 0, 255)

    def buscar_hoja(lugar):
        """Ruta de la hoja de tiles de ese lugar (en assets o cualquier subcarpeta) o None."""
        for carpeta, _, archivos in os.walk(assets):                      # assets, assets/hojas y sus subcarpetas
            if 'move_VFX' in carpeta or os.sep + 'sprites' in carpeta: continue
            for archivo in archivos:
                if ('Dungeon Tiles' in archivo or ' - Dungeons - ' in archivo) and archivo.endswith(' - ' + lugar + '.png'): return os.path.join(carpeta, archivo)
        return None

    def casilla(hoja, col, fila):
        """La casilla (col, fila) de la grilla de la hoja (24x24, sin la linea)."""
        return hoja.subsurface((9 + 25 * col, 163 + 25 * fila, 24, 24))

    def grupos(hoja):
        """Que grupo de columnas es cada cosa: {'pared': 1, 'suelo': 4, 'agua': n o None, 'brillo': n o None}."""
        fondo, linea = hoja.get_at((0, 0)), hoja.get_at((8, 300))
        x = 8                                                           # la linea de arriba de la grilla dice cuantas columnas hay
        while x + 1 < hoja.get_width() and hoja.get_at((x + 1, 162)) == linea: x += 1
        columnas = round((x - 8) / 25)
        llenas = lambda g: sum(casilla(hoja, g * 3 + k, f).get_at((12, 12)) != fondo for k in range(3) for f in range(23))
        magenta = lambda g: sum(tuple(casilla(hoja, g * 3 + k, f).get_at((2, 2)))[:3] == MAGENTA for k in range(3) for f in range(23))
        salida = {'pared': 1, 'suelo': 4, 'agua': None, 'brillo': None}
        for g in range(7, columnas // 3):
            if magenta(g) >= 10: salida['brillo'] = g if salida['agua'] == g - 1 else salida['brillo']
            elif llenas(g) >= 15: salida['agua'], salida['brillo'] = g, None
        return salida

    def leyenda(hoja):
        """Mascara de vecinos de cada casilla de la leyenda (-1 si esta vacia)."""
        fondo = hoja.get_at((0, 0))
        mascaras = []
        for fila in range(23):
            for k in range(3):
                t = casilla(hoja, k, fila)
                if t.get_at((9, 9)) == fondo: mascaras.append(-1); continue
                cuadros = [t.get_at((bx * 8 + 1, by * 8 + 1)) for by in range(3) for bx in range(3)]
                mascaras.append(sum(bit for bit, c in zip(BITS, cuadros) if c.r + c.g + c.b < 30))
        return mascaras

    def recortar(hoja, g):
        """Las 3x23 casillas del grupo sin las lineas (72x552) y que casillas tienen dibujo ('1') o estan vacias ('0')."""
        fondo = hoja.get_at((0, 0))
        sup = pygame.Surface((72, 552))
        hay = ''
        for fila in range(23):
            for k in range(3):
                t = casilla(hoja, g * 3 + k, fila)
                sup.blit(t, (k * 24, fila * 24))
                hay += '1' if t.get_at((12, 12)) != fondo or t.get_at((3, 3)) != fondo else '0'
        return sup, hay

    def paletas(hoja):
        """Grillas de colores a la derecha de las casillas ('Water palette' y 'Water Sparkle palette'): celdas de 10 px con borde de 1 px.
        Devuelve una lista de bloques, cada uno con sus filas de colores (una fila por frame)."""
        W, H = hoja.get_size()
        filas = []                                                     # (y, x) de cada linea de pixeles que cruza una fila de celdas
        for y in range(150, H):
            for x in range(W - 30 * 11, W - 11 * 11):
                if x < 0: continue
                b = hoja.get_at((x, y))
                if hoja.get_at((x + 11, y)) != b or hoja.get_at((x + 22, y)) != b or hoja.get_at((x + 5, y)) == b: continue
                n = 0
                while x + 11 * (n + 1) < W and hoja.get_at((x + 11 * (n + 1), y)) == b and hoja.get_at((x + 11 * n + 5, y)) != b: n += 1
                if n >= 8: filas.append((y, x, n)); break
        bloques, ultima = [], None
        for y, x, n in filas:
            if ultima and y == ultima[0] + 1 and x == ultima[1]: ultima = (y, x); continue   # misma fila de celdas
            ultima = (y, x)
            colores = [tuple(hoja.get_at((x + 11 * k + 5, y + 4)))[:3] for k in range(n)]
            if bloques and bloques[-1]['x'] == x and y - bloques[-1]['y'] <= 12: bloques[-1]['filas'].append(colores)
            else: bloques.append({'x': x, 'filas': [colores]})
            bloques[-1]['y'] = y
        return [b['filas'] for b in bloques if len(b['filas']) >= 2]

    def colores_de(img):
        """Todos los colores de una imagen (menos el magenta transparente)."""
        return {tuple(img.get_at((x, y)))[:3] for x in range(img.get_width()) for y in range(img.get_height())} - {MAGENTA}

    def repartir(bloques, agua, brillo):
        """Cada grilla de colores va a la capa cuyos colores cambia (algunas hojas solo tienen la de los brillos). (paleta del agua, de los brillos)."""
        capas = {'agua': colores_de(agua), 'brillo': colores_de(brillo) if brillo else set()}
        salida = {'agua': None, 'brillo': None}
        for filas in bloques:
            cambian = {fila[k] for fila in filas for k in range(len(fila)) if len({f[k] for f in filas}) > 1}
            for capa in sorted(('agua', 'brillo'), key=lambda c: -len(cambian & capas[c])):
                if cambian & capas[capa] and salida[capa] is None: salida[capa] = filas; break
        return salida['agua'], salida['brillo']

    def ordenar_paleta(filas, img):
        """Pone primero la fila de colores que tiene el dibujo (la casilla se recorto en ese frame). None si no tiene nada que ver."""
        colores = colores_de(img)
        puntos = [sum(c in colores for c in fila) for fila in filas]
        mejor = max(range(len(filas)), key=lambda i: puntos[i])
        if puntos[mejor] < 2: return None
        return [list(map(list, fila)) for fila in filas[mejor:] + filas[:mejor]]

    def retocar_color(c, escala):
        """Un color pasado a la escala de un retoque segun que tan claro es (el magenta de los brillos no se toca)."""
        c = tuple(c)[:3]
        if c == MAGENTA: return c
        luz = (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255
        for (a, ca), (b, cb) in zip(escala, escala[1:]):
            if luz <= b:
                k = (luz - a) / max(1e-6, b - a)
                return tuple(round(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
        return escala[-1][1]

    def retocar_imagen(img, escala):
        """La imagen con todos sus colores pasados por el retoque."""
        img = img.copy()
        pa = pygame.PixelArray(img)
        for c in {tuple(img.get_at((x, y)))[:3] for x in range(img.get_width()) for y in range(img.get_height())}:
            pa.replace(c, retocar_color(c, escala))
        pa.close()
        return img

    def main():
        """Arma cada tileset del PLAN: piezas, variantes, paletas del agua y brillos."""
        pygame.init(); pygame.display.set_mode((1, 1))
        hojas, hechos, faltan = {}, 0, set()
        for destino, terrenos in PLAN.items():
            carpeta = os.path.join(assets, 'mundo', *destino.split('/'), 'terrenos')
            for terreno, (lugar, grupo, *retoque) in terrenos.items():
                escala = RETOQUES[retoque[0]] if retoque else None
                if lugar not in hojas:
                    ruta = buscar_hoja(lugar)
                    hojas[lugar] = None
                    if ruta:
                        hoja = pygame.image.load(ruta).convert()
                        hojas[lugar] = {'hoja': hoja, 'grupos': grupos(hoja), 'leyenda': leyenda(hoja), 'paletas': None}
                h = hojas[lugar]
                if not h: faltan.add(lugar); continue
                g = h['grupos'][grupo]
                if g is None: continue                                  # esa hoja no tiene agua
                img, hay = recortar(h['hoja'], g)
                datos = {'hoja': lugar, 'grupo': grupo, 'mascaras': h['leyenda'], 'hay': hay, 'variantes': []}
                if grupo != 'agua':                                     # Wall Alt / Ground Alt: la misma casilla con otro dibujo (flores, piedritas)
                    for alt in (g + 1, g + 2):
                        a, hay_a = recortar(h['hoja'], alt)
                        if '1' in hay_a: datos['variantes'].append(hay_a); img = _juntar(img, a)
                os.makedirs(carpeta, exist_ok=True)
                if grupo == 'agua':
                    if h['paletas'] is None: h['paletas'] = paletas(h['hoja'])
                    cada, cada_brillo = VELOCIDAD.get(lugar, (12, 8))
                    brillo = None
                    if h['grupos']['brillo'] is not None:
                        brillo, hay_b = recortar(h['hoja'], h['grupos']['brillo'])
                        pygame.image.save(brillo, os.path.join(carpeta, terreno + '_brillo.png'))
                        datos.update(brillo=hay_b)
                    filas, filas_b = repartir(h['paletas'], img, brillo)
                    paleta = ordenar_paleta(filas, img) if filas else None
                    if paleta: datos.update(paleta=paleta, cada=cada)
                    paleta_b = ordenar_paleta(filas_b, brillo) if filas_b else None
                    if paleta_b: datos.update(paleta_brillo=paleta_b, cada_brillo=cada_brillo)
                    if escala:                                          # lava, aceite...: el agua con otros colores (dibujo, brillos y paletas)
                        img = retocar_imagen(img, escala)
                        for clave in ('paleta', 'paleta_brillo'):
                            if datos.get(clave): datos[clave] = [[list(retocar_color(c, escala)) for c in fila] for fila in datos[clave]]
                        if brillo is not None: pygame.image.save(retocar_imagen(brillo, escala), os.path.join(carpeta, terreno + '_brillo.png'))
                if terreno == 'vacio':                                  # el abismo va arriba del piso: el fondo de la hoja queda transparente
                    fondo_hoja = tuple(h['hoja'].get_at((0, 0)))[:3]
                    con_alfa = img.convert_alpha()
                    for x in range(con_alfa.get_width()):
                        for y in range(con_alfa.get_height()):
                            if tuple(con_alfa.get_at((x, y)))[:3] == fondo_hoja: con_alfa.set_at((x, y), (0, 0, 0, 0))
                    img = con_alfa; datos.update(grupo='agua', transparente=True)
                pygame.image.save(img, os.path.join(carpeta, terreno + '.png'))
                with open(os.path.join(carpeta, terreno + '.json'), 'w', encoding='utf-8') as f: json.dump(datos, f)
                for viejo in (terreno + '_2.png', terreno + '_3.png'):   # restos del formato viejo (una casilla suelta por variante)
                    if os.path.isfile(os.path.join(carpeta, viejo)): os.remove(os.path.join(carpeta, viejo))
                hechos += 1
        print(hechos, 'tilesets en assets/mundo')
        if faltan: print('faltan las hojas (spriters-resource, Explorers of Sky > Dungeon Tiles o Explorers of Time > Dungeons):', ', '.join(sorted(faltan)))

    def _juntar(a, b):
        """Pega dos imagenes una al lado de la otra."""
        sup = pygame.Surface((a.get_width() + b.get_width(), a.get_height()))
        sup.blit(a, (0, 0)); sup.blit(b, (a.get_width(), 0))
        return sup

    main()


# ==================== objetos del mundo (rocas, hielo, arbustos) ====================

def herramienta_decorados():
    """Sprites de objetos del mundo (assets/mundo/objetos/<nombre>.png, como los lee mundo.entorno.imagen):
    - rocas, bloques de hielo, pinos...: la 'pared aislada' de un tileset del PMD (la pieza de la leyenda sin vecinos) es una roca suelta.
      El fondo se saca comparando con el piso de la misma hoja: lo que es igual al piso queda transparente.
    - arbustos y arboles: copas y troncos de la hoja 'Poke Transfer' de Blanco/Negro (casillas de 32 px cada 34, fondo celeste)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    DEL_PMD = {'roca': 'Amp Plains', 'roca_nevada': 'Vast Ice Mountain', 'bloque_de_hielo': 'Dark Ice Mountain', 'estalagmita_de_hielo': 'Icicle Forest',
               'muro_de_hielo': 'Surrounded Sea', 'pino_nevado': 'Deep Dusk Forest 01F - 06F', 'pilar_de_cristal': 'The Nightmare',
               'menhir': 'Barren Valley', 'columna_rota': 'Limestone Cavern'}
    # Poke Transfer: (columna, fila) de las casillas; fila 1 copas claras, 2 copas oscuras, 3 troncos
    TRANSFER = {'maceta': [(2, 1)]}                                 # (el arbol y el arbusto ahora salen del PMD: python herramientas.py aldea)
    CELESTE = (56, 144, 184)

    def buscar(parte):
        """Ruta de una hoja que termina con ese nombre (en assets o subcarpetas) o None."""
        for carpeta, _, archivos in os.walk(assets):
            if 'move_VFX' in carpeta: continue
            for a in archivos:
                if a.endswith(parte + '.png'): return os.path.join(carpeta, a)
        return None

    def casilla(hoja, col, fila):
        """La casilla (col, fila) de la grilla de una hoja de tiles."""
        return hoja.subsurface((9 + 25 * col, 163 + 25 * fila, 24, 24))

    def roca(hoja):
        """Pared sin vecinos sobre el piso, con el piso borrado."""
        fondo = hoja.get_at((0, 0))
        aislada = lleno = None
        for fila in range(23):
            for k in range(3):
                t = casilla(hoja, k, fila)
                if t.get_at((9, 9)) == fondo: continue
                vecinos = [t.get_at((bx * 8 + 1, by * 8 + 1)) for by in range(3) for bx in range(3) if (bx, by) != (1, 1)]
                oscuros = sum(c.r + c.g + c.b < 30 for c in vecinos)
                if oscuros == 0 and aislada is None: aislada = (k, fila)
                if oscuros == 8 and lleno is None: lleno = (k, fila)
        if not aislada or not lleno: return None
        pared = casilla(hoja, 3 + aislada[0], aislada[1]).copy().convert_alpha()
        piso = casilla(hoja, 12 + lleno[0], lleno[1])
        colores = {tuple(piso.get_at((x, y)))[:3] for x in range(24) for y in range(24)}
        pendientes = [(x, y) for x in range(24) for y in (0, 23)] + [(x, y) for x in (0, 23) for y in range(24)]
        while pendientes:                                              # desde los bordes, todo lo que es color de piso se borra
            x, y = pendientes.pop()
            if not (0 <= x < 24 and 0 <= y < 24): continue
            c = pared.get_at((x, y))
            if c.a == 0 or tuple(c)[:3] not in colores: continue
            pared.set_at((x, y), (0, 0, 0, 0))
            pendientes += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        dibujo = pared.get_bounding_rect()
        return pared.subsurface(dibujo).copy()

    def main():
        """Recorta todos los objetos de DEL_PMD y TRANSFER a assets/mundo/objetos."""
        pygame.init(); pygame.display.set_mode((1, 1))
        carpeta = os.path.join(assets, 'mundo', 'objetos')
        os.makedirs(carpeta, exist_ok=True)
        hechos = []
        for nombre, lugar in DEL_PMD.items():
            ruta = buscar(' - ' + lugar)
            img = roca(pygame.image.load(ruta).convert()) if ruta else None
            if img: pygame.image.save(img, os.path.join(carpeta, nombre + '.png')); hechos.append(nombre)
        ruta = buscar(' - Poke Transfer')
        if ruta:
            hoja = pygame.image.load(ruta).convert_alpha()
            for nombre, piezas in TRANSFER.items():
                partes = []
                for col, fila in piezas:
                    p = hoja.subsurface((518 + 34 * col, 36 + 34 * fila, 32, 32)).copy()
                    pa = pygame.PixelArray(p); pa.replace(CELESTE, (0, 0, 0, 0)); pa.close()
                    partes.append(p.subsurface(p.get_bounding_rect()).copy())
                alto = sum(p.get_height() for p in partes) - 6 * (len(partes) - 1)   # el tronco asoma debajo de la copa
                sup = pygame.Surface((max(p.get_width() for p in partes), alto), pygame.SRCALPHA)
                y = alto
                for p in reversed(partes):
                    y -= p.get_height(); sup.blit(p, ((sup.get_width() - p.get_width()) // 2, y)); y += 6
                pygame.image.save(sup, os.path.join(carpeta, nombre + '.png')); hechos.append(nombre)
        print(len(hechos), 'objetos en assets/mundo/objetos:', ', '.join(hechos))

    main()


# ==================== props del PMD (cajas, vasijas, heno...) y casas del Red Rescue Team ====================

def herramienta_props():
    """Sprites de cosas hechas a mano (assets/mundo/objetos/<nombre>.png):
    - cajas, vasijas, heno, troncos y el puesto de manzanas: recortados del mapa 'Sky Peak 8th Station' del Explorers of Sky. Estan
      dibujados sobre el pasto: se borra desde el borde de cada recorte todo lo que es verde (pasto y plantitas).
      Las vasijas del mapa vienen de a dos, una tapando a la otra: se arma UNA entera con la mitad que se ve bien, espejada.
    - la llama del fuego del piso (assets/efectos/llama.png): los 4 cuadros de la fogata del mismo mapa, sin las piedras.
    - casas del refugio: las hojas 'Huts' del Red Rescue Team (Pikachu Hut, Mudkip Hut...). Hay que bajarlas a mano de Spriters Resource
      (estan en assets/hojas/faltan.txt) y dejarlas en assets/hojas/red_rescue/Huts: cada una queda como casa_<pokemon>.png y el
      barrio del refugio las usa solas (si no hay ninguna, dibuja las casas de siempre)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    # (x, y, ancho, alto) en el mapa de la 8va estacion -> nombres de objeto que usan ese recorte
    ESTACION = {(246, 124, 27, 27): ('caja',), (98, 223, 26, 28): ('anfora', 'barril', 'cesto'),
                (238, 228, 44, 34): ('fardo_de_heno',), (258, 270, 34, 30): ('tronco',), (116, 255, 48, 42): ('mesa_de_mercado',)}

    def es_pasto(c):
        """Pasto (verde) o piedra del borde del mapa (gris): lo que rodea a las cosas."""
        return (c.g > c.r and c.g > c.b * 1.25 and c.g > 90) or (abs(c.r - c.g) < 14 and abs(c.g - c.b) < 18)

    def sin_pasto(recorte):
        """Borra el pasto desde los bordes del recorte (lo que queda encerrado por el contorno oscuro del objeto no se toca)."""
        img = recorte.copy().convert_alpha()
        w, h = img.get_size()
        pendientes = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for x in (0, w - 1) for y in range(h)]
        while pendientes:
            x, y = pendientes.pop()
            if not (0 <= x < w and 0 <= y < h): continue
            c = img.get_at((x, y))
            if c.a == 0 or not es_pasto(c): continue
            img.set_at((x, y), (0, 0, 0, 0))
            pendientes += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        partes = pygame.mask.from_surface(img).connected_components(12)       # se queda con el pedazo mas grande (sin piedritas sueltas)
        if not partes: return None
        mayor = max(partes, key=lambda m_: m_.count())
        limpio = pygame.Surface((w, h), pygame.SRCALPHA)
        mayor.to_surface(limpio, setsurface=img, unsetcolor=None)
        return limpio.subsurface(limpio.get_bounding_rect()).copy()

    def vasija(par):
        """Una vasija sola y entera a partir del par del mapa: la de adelante tiene la mitad izquierda sin tapar, y es simetrica."""
        w, h = par.get_size()
        opaco = lambda x, y: par.get_at((x, y)).a > 0
        abajo = [x for y in range(h - 6, h) for x in range(w) if opaco(x, y)]       # las filas de abajo son solo de la de adelante
        izq, der = min(abajo), max(abajo)
        medio = (izq + der) // 2
        arriba = min(y for x in range(izq, medio + 1) for y in range(h) if opaco(x, y))
        ancho = der - izq + 1
        sola = pygame.Surface((ancho, h - arriba), pygame.SRCALPHA)
        for x in range(izq, medio + 1):
            for y in range(arriba, h):
                if not opaco(x, y): continue
                c = par.get_at((x, y))
                sola.set_at((x - izq, y - arriba), c); sola.set_at((ancho - 1 - (x - izq), y - arriba), c)
        return sola.subsurface(sola.get_bounding_rect()).copy()

    def llamas(mapa):
        """Los 4 cuadros de la fogata sin las piedras ni el pasto: queda solo el fuego (rojo, naranja y amarillo bien vivos)."""
        cuadros = []
        for x0 in (2, 37, 72, 107):
            c = mapa.subsurface((x0, 436, 32, 35)).copy().convert_alpha()
            for x in range(c.get_width()):
                for y in range(c.get_height()):
                    px = c.get_at((x, y))
                    vivo = px.r >= 250 and ((px.b < 90 and (px.r - px.g > 60 or px.g > 170)) or px.g > 225)   # rojo, naranja y amarillo vivos, o el blanco del medio
                    if not vivo or y > 26: c.set_at((x, y), (0, 0, 0, 0))      # (abajo de todo son los reflejos en las piedras)
            partes = pygame.mask.from_surface(c).connected_components()
            fuego = max(partes, key=lambda m_: m_.count())
            for parte in partes:                                                  # los pedacitos sueltos de abajo son brillos de las piedras: afuera
                if parte is fuego or parte.centroid()[1] < 12: continue          # (las chispas de arriba se quedan)
                for x, y in ((x, y) for x in range(c.get_width()) for y in range(c.get_height()) if parte.get_at((x, y))): c.set_at((x, y), (0, 0, 0, 0))
            cuadros.append(c)
        caja_f = cuadros[0].get_bounding_rect().unionall([c.get_bounding_rect() for c in cuadros[1:]])
        lado = max(caja_f.size)
        tira = pygame.Surface((lado * len(cuadros), lado), pygame.SRCALPHA)
        for k, c in enumerate(cuadros):                                           # cada cuadro centrado y apoyado abajo
            tira.blit(c.subsurface(caja_f), (k * lado + (lado - caja_f.width) // 2, lado - caja_f.height))
        return tira

    def casa(hoja):
        """La casa de una hoja 'Hut': sin el color de fondo y sin los carteles de texto (el pedazo mas grande)."""
        img = hoja.convert_alpha()
        pa = pygame.PixelArray(img); pa.replace(img.get_at((0, 0)), (0, 0, 0, 0)); pa.close()
        partes = pygame.mask.from_surface(img).connected_components(400)
        if not partes: return None
        mayor = max(partes, key=lambda m_: m_.count())
        limpio = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        mayor.to_surface(limpio, setsurface=img, unsetcolor=None)
        return limpio.subsurface(limpio.get_bounding_rect()).copy()

    pygame.init(); pygame.display.set_mode((1, 1))
    carpeta = os.path.join(assets, 'mundo', 'objetos')
    os.makedirs(carpeta, exist_ok=True)
    hechos = []
    ruta = next((os.path.join(c, a) for c, _, archivos in os.walk(assets) for a in archivos if a.endswith('Sky Peak 8th Station.png')), None)
    if ruta:
        mapa = pygame.image.load(ruta).convert()
        for caja_r, nombres in ESTACION.items():
            img = sin_pasto(mapa.subsurface(caja_r))
            if not img: continue
            if 'anfora' in nombres: img = vasija(img)
            for n in nombres: pygame.image.save(img, os.path.join(carpeta, n + '.png')); hechos.append(n)
        os.makedirs(os.path.join(assets, 'efectos'), exist_ok=True)
        pygame.image.save(llamas(mapa), os.path.join(assets, 'efectos', 'llama.png')); hechos.append('efectos/llama')
    else: print('falta el mapa "Maps - Sky Peak 8th Station" del Explorers of Sky')
    chozas = os.path.join(assets, 'hojas', 'red_rescue', 'Huts')
    for archivo in sorted(os.listdir(chozas)) if os.path.isdir(chozas) else ():
        if not archivo.lower().endswith('.png') or 'construction' in archivo.lower(): continue
        img = casa(pygame.image.load(os.path.join(chozas, archivo)))
        nombre = 'casa_' + archivo[:-4].lower().replace(' hut', '').replace(' ', '_')
        if img: pygame.image.save(img, os.path.join(carpeta, nombre + '.png')); hechos.append(nombre)
    if not os.path.isdir(chozas): print('casas: baja las hojas "Huts" del Red Rescue Team (assets/hojas/faltan.txt) a assets/hojas/red_rescue/Huts y corre esto de nuevo')
    print(len(hechos), 'objetos en assets/mundo/objetos:', ', '.join(hechos))


# ==================== cielo de la intro ====================

def herramienta_cielo():
    """De la hoja 'Skies' del Explorers of Sky (4 paneles de 288x216) recorta para la intro (interfaz.menus.intro):
    assets/interfaz/fondos/cielo.png (el degrade con el sol) y nube_<n>.png (cada nube del panel verde, sin el verde)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    VERDE = (76, 255, 0)

    def main():
        """Recorta el cielo y separa cada nube del fondo verde."""
        pygame.init(); pygame.display.set_mode((1, 1))
        ruta = next((os.path.join(c, a) for c, _, archivos in os.walk(assets) if 'move_VFX' not in c for a in archivos if a.endswith(' - Skies.png')), None)
        if not ruta: print('falta la hoja (spriters-resource, Explorers of Sky > Miscellaneous > Skies) en assets/hojas'); return
        hoja = pygame.image.load(ruta).convert_alpha()
        carpeta = os.path.join(assets, 'interfaz', 'fondos')
        os.makedirs(carpeta, exist_ok=True)
        pygame.image.save(hoja.subsurface((290, 0, 288, 216)), os.path.join(carpeta, 'cielo.png'))
        nubes = hoja.subsurface((0, 0, 288, 216)).copy()
        pa = pygame.PixelArray(nubes); pa.replace(VERDE, (0, 0, 0, 0)); pa.close()
        piezas = sorted(pygame.mask.from_surface(nubes).get_bounding_rects(), key=lambda r: -r.width * r.height)
        piezas = [r for r in piezas if r.width * r.height > 300]
        for i, r in enumerate(piezas): pygame.image.save(nubes.subsurface(r), os.path.join(carpeta, 'nube_' + str(i) + '.png'))
        print('cielo y', len(piezas), 'nubes en assets/interfaz/fondos')

    main()


def herramienta_minimapa():
    """De la hoja 'Map Sprites' del Explorers of Time/Darkness (el mapa de la pantalla de arriba del PMD) recorta las piezas del minimapa:
    assets/interfaz/minimapa/ yo, aliado, objeto, enemigo, jefe (outlaw), baldosa (wondertile), escalera, trampa y portal (warpzone),
    borde_h / borde_v (las rayitas blancas de las paredes), relleno (la trama azul del piso explorado) y fondo_mapa (el marron a cuadros
    que va detras del mapa, para el mapa grande de la tecla M). El verde de fondo queda transparente."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    PIEZAS = {'yo': (2, 3, 4, 4), 'yo_claro': (9, 3, 4, 4), 'aliado': (2, 10, 4, 4), 'objeto': (2, 17, 4, 4), 'enemigo': (2, 24, 4, 4),
              'jefe': (2, 31, 4, 4), 'baldosa': (3, 39, 2, 2), 'escalera': (2, 45, 4, 4), 'trampa': (2, 52, 4, 4), 'portal': (2, 59, 4, 4),
              'borde_h': (37, 79, 4, 1), 'borde_v': (46, 79, 1, 4), 'relleno': (5, 104, 4, 4), 'relleno_lleno': (31, 104, 4, 4),
              'fondo_mapa': (5, 78, 24, 24)}                                 # (el marron a cuadros de atras del mapa: el fondo del mapa grande)

    def main():
        """Recorta cada pieza de la hoja y saca el verde de fondo."""
        pygame.init(); pygame.display.set_mode((1, 1))
        ruta = next((os.path.join(c, a) for c, _, archivos in os.walk(assets) if 'move_VFX' not in c for a in archivos if a.endswith(' - Map Sprites.png')), None)
        if not ruta: print('falta la hoja (spriters-resource, Explorers of Time/Darkness > Miscellaneous > Map Sprites) en assets'); return
        hoja = pygame.image.load(ruta).convert_alpha()
        verde = tuple(hoja.get_at((0, 0)))
        carpeta = os.path.join(assets, 'interfaz', 'minimapa')
        os.makedirs(carpeta, exist_ok=True)
        for nombre, r in PIEZAS.items():
            pieza = hoja.subsurface(r).copy()
            pa = pygame.PixelArray(pieza); pa.replace(verde[:3], (0, 0, 0, 0)); pa.close()
            pygame.image.save(pieza, os.path.join(carpeta, nombre + '.png'))
        print(len(PIEZAS), 'piezas del minimapa en assets/interfaz/minimapa')

    main()


def herramienta_viaje():
    """Lo del viaje temporal (interfaz.menus.viaje_temporal y cruzar_portal), en assets/interfaz/fondos:
        viaje_<n>.png     de 'Time Travel' del Explorers of Sky (13 cuadros de 312x240 en la columna izquierda, separados por 3 px):
                          los 12 cuadros animados del tunel, recortados a 5:3 como la pantalla
        viaje_fondo.png   el cuadro 13: el cosmos quieto (sin los cuadrados ni las rayas)
        viaje_capa_<n>.png  la columna derecha: solo lo que se mueve (cuadrados y rayas), con el magenta transparente
        apertura_<n>.png  de 'Dimensional Scream' del Explorers of Time/Darkness (cuadros de 256x192 en 3 columnas, separados por 2 px):
                          la estela que cruza, la estrella y el estallido hasta quedar todo blanco (los 22 primeros cuadros)"""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    ANCHO, ALTO, PASO, CUADROS = 312, 240, 243, 12
    APERTURA = {'ancho': 256, 'alto': 192, 'paso': 258, 'paso_y': 194, 'columnas': 3, 'cuadros': 22}   # el 22 (fila 7, columna 1) es el blanco

    def buscar(final):
        """La hoja que termina con ese nombre (en assets o en assets/hojas)."""
        return next((os.path.join(c, a) for c, _, archivos in os.walk(assets) if 'move_VFX' not in c for a in archivos if a.endswith(final)), None)

    def a_cinco_tercios(hoja, x, y, ancho, alto):
        """El cuadro (x, y, ancho, alto) recortado arriba y abajo para que quede 5:3, como la pantalla."""
        recorte = round(ancho * 3 / 5)
        return hoja.subsurface((x, y + (alto - recorte) // 2, ancho, recorte))

    def main():
        """Recorta el tunel y la apertura."""
        pygame.init(); pygame.display.set_mode((1, 1))
        carpeta = os.path.join(assets, 'interfaz', 'fondos')
        os.makedirs(carpeta, exist_ok=True)
        ruta = buscar(' - Time Travel.png')
        if not ruta: print('falta la hoja (spriters-resource, Explorers of Sky > Miscellaneous > Time Travel) en assets')
        else:
            hoja = pygame.image.load(ruta).convert()
            for i in range(CUADROS): pygame.image.save(a_cinco_tercios(hoja, 0, i * PASO, ANCHO, ALTO), os.path.join(carpeta, 'viaje_' + str(i) + '.png'))
            pygame.image.save(a_cinco_tercios(hoja, 0, CUADROS * PASO, ANCHO, ALTO), os.path.join(carpeta, 'viaje_fondo.png'))
            magenta = tuple(hoja.get_at((ANCHO + 8, 5)))[:3]
            for i in range(CUADROS):
                capa = a_cinco_tercios(hoja, ANCHO + 3, i * PASO, ANCHO, ALTO).copy().convert_alpha()
                pa = pygame.PixelArray(capa); pa.replace(magenta, (0, 0, 0, 0)); pa.close()
                pygame.image.save(capa, os.path.join(carpeta, 'viaje_capa_' + str(i) + '.png'))
            print(CUADROS, 'cuadros del tunel, el cosmos quieto y la capa que se mueve en assets/interfaz/fondos')
        ruta = buscar(' - Dimensional Scream.png')
        if not ruta: print('falta la hoja (spriters-resource, Explorers of Time/Darkness > Miscellaneous > Dimensional Scream) en assets'); return
        hoja, a = pygame.image.load(ruta).convert(), APERTURA
        for i in range(a['cuadros']):
            fila, col = divmod(i, a['columnas'])
            pygame.image.save(a_cinco_tercios(hoja, col * a['paso'], fila * a['paso_y'], a['ancho'], a['alto']), os.path.join(carpeta, 'apertura_' + str(i) + '.png'))
        print(a['cuadros'], 'cuadros de la apertura en assets/interfaz/fondos')

    main()


# ==================== efectos de ataque del PMD ====================

def herramienta_efectos():
    """De los 'Attack Effects' del Explorers of Sky (move_VFX/<numero>/000/<frame>.png, el zip o la carpeta assets/efectos/move_VFX)
    arma las tiras de assets/efectos: una fila de frames cuadrados (como las lee mundo.efectos). Los numeros no tienen nombre: se eligieron mirandolos.
    proyectil_<tipo> son las bolas, hojas y rocas que vuelan (se repiten en loop). aparecer y destello salen de la hoja 'Poke Transfer' de BW."""
    import io, zipfile
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    ELEGIDOS = {'golpe': '0038', 'golpe_normal': '0038', 'golpe_fuego': '0008', 'golpe_agua': '0021', 'golpe_electrico': '0222',
                'golpe_hielo': '0141', 'golpe_planta': '0076', 'golpe_veneno': '0144', 'golpe_tierra': '0002', 'golpe_roca': '0182',
                'golpe_lucha': '0221', 'golpe_psiquico': '0171', 'golpe_fantasma': '0046', 'golpe_siniestro': '0122', 'golpe_dragon': '0092',
                'golpe_acero': '0166', 'golpe_volador': '0149', 'golpe_hada': '0254', 'golpe_bicho': '0154',
                'explosion': '0253', 'romper': '0140', 'nivel': '0125', 'evolucion': '0180', 'cura': '0105', 'cambio': '0239',
                'proyectil_fuego': '0024', 'proyectil_agua': '0183', 'proyectil_electrico': '0060', 'proyectil_hielo': '0026',
                'proyectil_planta': '0129', 'proyectil_veneno': '0029', 'proyectil_tierra': '0117', 'proyectil_roca': '0182',
                'proyectil_lucha': '0221', 'proyectil_psiquico': '0102', 'proyectil_fantasma': '0092', 'proyectil_siniestro': '0203',
                'proyectil_dragon': '0240', 'proyectil_acero': '0035', 'proyectil_volador': '0050', 'proyectil_normal': '0134',
                'proyectil_bicho': '0112', 'proyectil_hada': '0233'}
    MAX_FRAMES = 12                                                 # los largos se recortan salteando frames (un golpe no puede durar 2 segundos)
    TRANSFER = {'aparecer': 5, 'destello': 7}                       # filas de nubecitas de la hoja Poke Transfer (5 frames de 32 px)

    def tira_de(frames):
        """Pone frames en una tira horizontal de cuadrados (cada frame centrado en el suyo)."""
        lado = max(max(f.get_size()) for f in frames)
        tira = pygame.Surface((lado * len(frames), lado), pygame.SRCALPHA)
        for i, f in enumerate(frames): tira.blit(f, f.get_rect(center=(i * lado + lado // 2, lado // 2)))   # cada frame centrado en su cuadrado
        return tira

    def main():
        """Arma las tiras de todos los efectos elegidos (del zip o de la carpeta) y las de la hoja Poke Transfer."""
        pygame.init(); pygame.display.set_mode((1, 1))
        zips = [os.path.join(c, a) for c in (os.path.join(assets, 'hojas'), assets) if os.path.isdir(c) for a in os.listdir(c) if a.endswith('Attack Effects.zip')]
        carpetas = [c for c in (os.path.join(assets, 'efectos', 'move_VFX'), os.path.join(assets, 'move_VFX')) if os.path.isdir(c)]
        if zips:
            z = zipfile.ZipFile(zips[0])
            nombres = z.namelist()
            listar = lambda numero: sorted(n for n in nombres if n.startswith('move_VFX/' + numero + '/000/') and n.endswith('.png'))
            abrir = lambda r: pygame.image.load(io.BytesIO(z.read(r)), 'f.png')
        elif carpetas:
            listar = lambda numero: sorted(os.path.join(carpetas[0], numero, '000', a) for a in os.listdir(os.path.join(carpetas[0], numero, '000'))
                                           if a.endswith('.png')) if os.path.isdir(os.path.join(carpetas[0], numero, '000')) else []
            abrir = pygame.image.load
        else:
            print('faltan los Attack Effects (spriters-resource, Explorers of Sky > Miscellaneous): el zip en assets/hojas o la carpeta assets/efectos/move_VFX'); return
        os.makedirs(os.path.join(assets, 'efectos'), exist_ok=True)
        for efecto, numero in ELEGIDOS.items():
            rutas = listar(numero)
            if not rutas: print('no esta', numero); continue
            rutas = [rutas[round(i * (len(rutas) - 1) / (MAX_FRAMES - 1))] for i in range(MAX_FRAMES)] if len(rutas) > MAX_FRAMES else rutas
            pygame.image.save(tira_de([abrir(r).convert_alpha() for r in rutas]), os.path.join(assets, 'efectos', efecto + '.png'))
        hoja = next((os.path.join(c, a) for c, _, archivos in os.walk(assets) if 'move_VFX' not in c for a in archivos if a.endswith(' - Poke Transfer.png')), None)
        if hoja:
            hoja = pygame.image.load(hoja).convert_alpha()
            for efecto, fila in TRANSFER.items():
                frames = []
                for col in range(5):
                    f = hoja.subsurface((518 + 34 * col, 36 + 34 * fila, 32, 32)).copy()
                    pa = pygame.PixelArray(f); pa.replace((56, 144, 184), (0, 0, 0, 0)); pa.close()
                    frames.append(f)
                pygame.image.save(tira_de(frames), os.path.join(assets, 'efectos', efecto + '.png'))
        print(len(ELEGIDOS) + (len(TRANSFER) if hoja else 0), 'efectos en assets/efectos')

    main()


# ==================== iconos de objetos de BW ====================

def herramienta_objetos():
    """De la hoja 'Items' de Blanco/Negro recorta los iconos de la tienda a assets/interfaz/objetos/<clave>.png (como los lee interfaz.icono_objeto).
    La hoja es una grilla de 12 columnas con casillas de 40 px y una linea de 1 px; los numeros (fila * 12 + columna) se eligieron mirandola.
    Las MT usan un disco por tipo: mt_<tipo>.png (BW no tiene MT de tipo hada)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    ELEGIDOS = {'repelente': 73, 'superrepelente': 70, 'maxirepelente': 71, 'ataque_x': 62, 'defensa_x': 63, 'velocidad_x': 64, 'especial_x': 66,
                'directo': 61, 'eter': 33, 'cinta_fuerte': 295, 'garra_rapida': 148, 'polvo_veloz': 188, 'amuleto_moneda': 153,
                'agua_mistica': 173, 'carbon': 179, 'iman': 172, 'antiderretir': 176, 'cinturon_negro': 171, 'arena_fina': 167, 'pico_afilado': 174,
                'piedra_dura': 168, 'colmillo_dragon': 180, 'gafas_de_sol': 170, 'hechizo': 177, 'cuchara_torcida': 178, 'flecha_venenosa': 175,
                'revestimiento_metalico': 163, 'semilla_milagro': 169, 'pañuelo_seda': 181,
                'piedra_trueno': 77, 'piedra_alba': 291, 'garra_afilada': 321, 'baya_oran': 106, 'caramelo_raro': 57, 'llave_tesoro': 439,
                'mas_ps': 51, 'proteina': 52, 'hierro': 53, 'carburante': 54, 'calcio': 55, 'zinc': 56,
                'pocion': 12, 'superpocion': 14, 'hiperpocion': 13, 'pocion_maxima': 21, 'remedio': 15, 'superremedio': 22, 'hiperremedio': 20,
                'revivir': 23, 'maximo_revivir': 24, 'agua_fresca': 25, 'refresco': 26, 'limonada': 27, 'leche_mumu': 28, 'polvo_energia': 29,
                'raiz_energia': 30, 'polvo_curacion': 31, 'hierba_revivir': 32, 'galleta_lava': 37, 'zumo_baya': 43, 'porcehelado': 46,
                'crepe_luminalia': 260, 'bizcocho_jubileo': 261, 'baya_zreza': 100, 'baya_atania': 101, 'baya_meloc': 102, 'baya_safre': 103,
                'baya_perasi': 104, 'baya_aranja': 106, 'baya_caquic': 107, 'baya_ziuela': 108, 'baya_zidra': 109,
                'piedra_solar': 74, 'piedra_lunar': 75, 'piedra_fuego': 76, 'piedra_agua': 78, 'piedra_hoja': 79, 'piedra_dia': 289, 'piedra_noche': 290,
                'piedra_hielo': 380, 'armadura_auspiciosa': 317, 'armadura_maldita': 320, 'mineral_negro': 304, 'cristal_paradoja': 379,
                'lazo_amistad': 393, 'cordon_union': 72, 'chaleco_asalto': 147, 'pluma_agil': 145, 'polvo_plata': 152, 'pluma_hada': 144, 'cinturon_focus': 160,
                'mt_normal': 228, 'mt_lucha': 224, 'mt_volador': 239, 'mt_veneno': 237, 'mt_tierra': 238, 'mt_roca': 235, 'mt_bicho': 231,
                'mt_fantasma': 229, 'mt_acero': 234, 'mt_fuego': 232, 'mt_agua': 226, 'mt_planta': 231, 'mt_electrico': 236, 'mt_psiquico': 227,
                'mt_hielo': 230, 'mt_dragon': 225, 'mt_siniestro': 233}
    FONDO = ((211, 211, 211), (255, 0, 255))                        # gris de la casilla y las rayitas magenta de la grilla

    def buscar_hoja():
        """Ruta de la hoja 'Items' de BW o None."""
        for carpeta in (os.path.join(assets, 'hojas', 'blanco_negro'), os.path.join(assets, 'hojas'), assets):
            if not os.path.isdir(carpeta): continue
            for archivo in os.listdir(carpeta):
                if 'Black _ White' in archivo and archivo.endswith(' - Items.png'): return os.path.join(carpeta, archivo)
        return None

    def icono(hoja, numero):
        """La casilla sin el fondo, recortada al dibujo y centrada en un cuadrado."""
        fila, col = divmod(numero, 12)
        c = hoja.subsurface((1 + col * 41, 1 + fila * 41, 40, 40)).copy()
        for x in range(40):
            for y in range(40):
                if tuple(c.get_at((x, y)))[:3] in FONDO: c.set_at((x, y), (0, 0, 0, 0))
        dibujo = c.get_bounding_rect()
        lado = max(dibujo.size)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        sup.blit(c, ((lado - dibujo.width) // 2, (lado - dibujo.height) // 2), dibujo)
        return sup

    def main():
        """Recorta todos los iconos de ELEGIDOS a assets/interfaz/objetos."""
        pygame.init(); pygame.display.set_mode((1, 1))
        ruta = buscar_hoja()
        if not ruta: print('falta la hoja (spriters-resource, Black/White > Miscellaneous > Items) en assets/hojas/blanco_negro'); return
        hoja = pygame.image.load(ruta).convert_alpha()
        carpeta = os.path.join(assets, 'interfaz', 'objetos')
        os.makedirs(carpeta, exist_ok=True)
        for clave, numero in ELEGIDOS.items(): pygame.image.save(icono(hoja, numero), os.path.join(carpeta, clave + '.png'))
        print(len(ELEGIDOS), 'iconos en assets/interfaz/objetos')
        ruta = _buscar_hoja('Miscellaneous - Items & Objects.png')       # del Red Rescue Team: lo que se junta del piso en las salas
        if ruta:
            hoja = pygame.image.load(ruta).convert_alpha()
            fila = hoja.subsurface((0, 0, 150, 16)).copy()               # primera fila: moneda, semilla, manzana, banana, pincho, botella, orbe, caja, llave, lentes
            pa = pygame.PixelArray(fila); pa.replace(hoja.get_at((190, 10)), (0, 0, 0, 0)); pa.close()
            cajas = sorted((r for r in pygame.mask.from_surface(fila).get_bounding_rects() if r.width >= 8), key=lambda r: r.x)
            for nombre, i in (('moneda', 0), ('manzana', 2), ('pincho', 4), ('llave', 8)):
                if i < len(cajas): pygame.image.save(fila.subsurface(cajas[i]), os.path.join(assets, 'mundo', 'objetos', nombre + '.png'))
            print('moneda, manzana, pincho y llave (Red Rescue Team) en assets/mundo/objetos')

    main()


# ==================== paneles de los menus de BW ====================

def herramienta_paneles():
    """De las hojas 'Options Screen' y 'Party Screen' de Blanco/Negro recorta las piezas de los menus a assets/interfaz/paneles
    (como las leen interfaz.caja y interfaz.fondo). Las coordenadas se midieron en las hojas.
    Lo que rodea a cada pieza (el color de fondo de la hoja) queda transparente, menos en los fondos."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    # pieza -> (hoja, rect, recortar el borde). Las barras de opciones: la de arriba es la elegida y la gris la normal
    PIEZAS = {'fondo': ('Options Screen', (0, 0, 256, 192), False),
              'boton': ('Options Screen', (0, 282, 256, 19), True),
              'boton_elegido': ('Options Screen', (0, 210, 256, 19), True),
              'panel': ('Options Screen', (0, 321, 256, 46), True),         # sin la raya verde de la hoja que va de lado a lado
              'fondo_equipo': ('Party Screen', (2, 2, 256, 192), False),
              'miembro': ('Party Screen', (5, 201, 126, 46), True),
              'miembro_activo': ('Party Screen', (133, 201, 126, 46), True),
              'miembro_debil': ('Party Screen', (5, 249, 126, 46), True)}
    FONDO_HOJA = {(57, 57, 74), (0, 0, 0), (160, 234, 0), (191, 143, 0)}      # franja detras de las barras, negro, verde y naranja de la hoja

    def buscar_hoja(nombre):
        """Ruta de una hoja de BW con ese nombre o None."""
        for carpeta in (os.path.join(assets, 'hojas', 'blanco_negro'), os.path.join(assets, 'hojas'), assets):
            if not os.path.isdir(carpeta): continue
            for archivo in os.listdir(carpeta):
                if 'Black _ White' in archivo and archivo.endswith(' - ' + nombre + '.png'): return os.path.join(carpeta, archivo)
        return None

    def sin_borde(sup):
        """Vuelve transparente el fondo de la hoja que toca las esquinas (relleno desde las 4 esquinas, sin pasar el marco de la pieza)."""
        w, h = sup.get_size()
        pendientes = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        while pendientes:
            x, y = pendientes.pop()
            if not (0 <= x < w and 0 <= y < h): continue
            c = sup.get_at((x, y))
            if c.a == 0 or tuple(c)[:3] not in FONDO_HOJA: continue
            sup.set_at((x, y), (0, 0, 0, 0))
            pendientes += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return sup

    def main():
        """Recorta todas las PIEZAS a assets/interfaz/paneles."""
        pygame.init(); pygame.display.set_mode((1, 1))
        hojas, hechos, faltan = {}, 0, set()
        carpeta = os.path.join(assets, 'interfaz', 'paneles')
        for pieza, (hoja, rect, recortar) in PIEZAS.items():
            if hoja not in hojas:
                ruta = buscar_hoja(hoja)
                hojas[hoja] = pygame.image.load(ruta).convert_alpha() if ruta else None
            if not hojas[hoja]: faltan.add(hoja); continue
            img = hojas[hoja].subsurface(rect).copy()
            if recortar: img = sin_borde(img)
            os.makedirs(carpeta, exist_ok=True)
            pygame.image.save(img, os.path.join(carpeta, pieza + '.png')); hechos += 1
        print(hechos, 'piezas en assets/interfaz/paneles')
        if faltan: print('faltan las hojas (spriters-resource, Black/White > Miscellaneous):', ', '.join(sorted(faltan)))

    main()


def herramienta_hud():
    """De las hojas 'Battle HUD', 'Miscellaneous Icons' y 'Party Screen' de Blanco/Negro recorta las piezas del HUD y de los menus
    a assets/interfaz/hud: las barras de HP del combate (la del rival y la tuya, con la etiqueta HP y la punta de flecha),
    la de experiencia, el icono 'Lv', la Pokeball grande del fondo de la pantalla tactil, la textura de puntitos de los botones
    tactiles, los iconos de estado (PSN, BRN, PAR, FRZ, FNT) y los 12 paneles en flecha del menu de equipo (panel_<fila>_<columna>).
    Lo que rodea a cada pieza (el color de fondo de la hoja) queda transparente."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    LILA, AZUL, CAFE = (189, 189, 231), (66, 66, 255), (69, 57, 57)        # fondos de las hojas
    PIEZAS = {'barra_rival': ('Battle HUD', (617, 24, 124, 15), LILA), 'barra_jugador': ('Battle HUD', (617, 44, 120, 21), LILA),
              'barra_exp': ('Battle HUD', (640, 64, 97, 5), LILA), 'nv': ('Battle HUD', (701, 23, 8, 7), LILA),
              'pokeball_chica': ('Battle HUD', (730, 8, 8, 8), LILA), 'textura_boton': ('Battle HUD', (628, 249, 5, 5), None),
              'pokeball': ('Battle HUD', (0, 0, 512, 512), None)}
    for k, estado in enumerate(('psn', 'brn', 'par', 'frz', 'fnt')): PIEZAS['estado_' + estado] = ('Miscellaneous Icons', (79, 311 + k * 9, 19, 6), AZUL)
    for fila in range(3):
        for col in range(4): PIEZAS['panel_%d_%d' % (fila, col)] = ('Party Screen', (5 + col * 128, 201 + fila * 48, 126, 46), (160, 234, 0))
    # la alfombra roja del Secret Bazaar de Explorers of Sky (abajo a la izquierda, donde no la tapan las bolsas): se arma del tamaño que haga falta
    BAZAR = 'Secret Bazaar'
    PIEZAS.update({'alfombra_esquina': (BAZAR, (272, 232, 8, 8), None), 'alfombra_borde_h': (BAZAR, (300, 232, 24, 8), None),
                   'alfombra_borde_v': (BAZAR, (272, 214, 8, 16), None), 'alfombra_rombo': (BAZAR, (281, 217, 14, 14), (255, 90, 90)),
                   'alfombra_fondo': (BAZAR, (300, 232, 4, 3), None)})

    def buscar_hoja(nombre):
        """Busca una hoja de BW en las carpetas de assets."""
        for carpeta in (os.path.join(assets, 'hojas', 'blanco_negro'), os.path.join(assets, 'hojas', 'blanco_negro', 'Miscellaneous'), assets):
            if not os.path.isdir(carpeta): continue
            for archivo in os.listdir(carpeta):
                if archivo.endswith(' - ' + nombre + '.png') and ('Black _ White' in archivo or 'Explorers of Sky' in archivo): return os.path.join(carpeta, archivo)
        return None

    def transparente(sup, color):
        """El color de fondo de la hoja que toca los bordes de la pieza pasa a ser transparente (relleno desde los bordes)."""
        w, h = sup.get_size()
        pendientes = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
        while pendientes:
            x, y = pendientes.pop()
            if not (0 <= x < w and 0 <= y < h): continue
            c = sup.get_at((x, y))
            if c.a == 0 or tuple(c)[:3] != color: continue
            sup.set_at((x, y), (0, 0, 0, 0))
            pendientes += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return sup

    def pokeball(sup):
        """La Pokeball grande sin el fondo: todo lo que queda afuera del circulo es transparente."""
        w, h = sup.get_size(); cx, cy, r = w / 2, h / 2, w / 2 - 6
        for y in range(h):
            for x in range(w):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 > r * r: sup.set_at((x, y), (0, 0, 0, 0))
        return sup

    pygame.init(); pygame.display.set_mode((1, 1))
    hojas, hechos, faltan = {}, 0, set()
    carpeta = os.path.join(assets, 'interfaz', 'hud')
    os.makedirs(carpeta, exist_ok=True)
    for pieza, (hoja, rect, fondo) in PIEZAS.items():
        if hoja not in hojas:
            ruta = buscar_hoja(hoja)
            hojas[hoja] = pygame.image.load(ruta).convert_alpha() if ruta else None
        if not hojas[hoja]: faltan.add(hoja); continue
        img = hojas[hoja].subsurface(rect).copy()
        if fondo: img = transparente(img, fondo)
        if pieza == 'pokeball': img = pokeball(img)
        pygame.image.save(img, os.path.join(carpeta, pieza + '.png')); hechos += 1
    print(hechos, 'piezas en assets/interfaz/hud')
    if faltan: print('faltan las hojas (spriters-resource, Black/White > Miscellaneous):', ', '.join(sorted(faltan)))


# ==================== clima del Red Rescue Team ====================

def _buscar_hoja(final):
    """Ruta de la hoja (o zip) que termina con ese nombre, en assets o en cualquier subcarpeta. None si no esta."""
    assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    return next((os.path.join(c, a) for c, _, archivos in os.walk(assets) if 'move_VFX' not in c and os.sep + 'sprites' not in c
                 for a in sorted(archivos) if a.endswith(final)), None)


def herramienta_clima():
    """De las hojas 'Weather' del Red Rescue Team arma assets/clima/<efecto>/<nn>.png (como los lee mundo.entorno.dibujar_clima):
        lluvia    'Rain': cuadros de 240x160 (5 columnas, paso 248x168 desde 8,8). Los del principio y del final son la lluvia que
                  arranca y que para: se guardan solo los del medio, que se repiten en loop. El gris azulado de fondo queda transparente
        granizo   'Hail.zip': 65 cuadros de 240x160 ya transparentes (igual: solo los del medio)
        brasas    'Embers.zip': 14 cuadros de 488x328 sobre negro (se suman a la pantalla, el negro no se ve)
        nieve     'Miscellaneous Weather Effects': 16 cuadros de 64x32 que se repiten como baldosas; ventisca: 16 de 32x32
        arena     las dos franjas de la tormenta de arena (120x32, se repiten de costado)
        nubes     las sombras de las nubes (720x408): la mancha azul pasa a sombra oscura transparente
        niebla    'Fog': la niebla sobre negro (336x120, se suma a la pantalla)
        sol       'Sunny': 13 cuadros de 240x112 del destello del sol"""
    import io, zipfile
    raiz = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(raiz, 'assets', 'clima')
    FONDO = (90, 90, 120)                                           # el gris azulado de las hojas de clima

    def sin_fondo(sup, color=FONDO):
        """Copia con ese color transparente."""
        img = sup.copy().convert_alpha()
        pa = pygame.PixelArray(img); pa.replace(color, (0, 0, 0, 0)); pa.close()
        return img

    def del_medio(frames, parte=0.6):
        """Los cuadros 'llenos' (con al menos esa parte de lo que tiene el mas lleno): el loop sin el arranque ni el final."""
        llenos = [pygame.mask.from_surface(f).count() for f in frames]
        buenos = [i for i, n in enumerate(llenos) if n >= max(llenos) * parte]
        return frames[buenos[0]:buenos[-1] + 1]

    def guardar(nombre, frames):
        """Deja los cuadros en assets/clima/<nombre>/00.png, 01.png..."""
        carpeta = os.path.join(destino, nombre)
        os.makedirs(carpeta, exist_ok=True)
        for viejo in os.listdir(carpeta): os.remove(os.path.join(carpeta, viejo))
        for i, f in enumerate(frames): pygame.image.save(f, os.path.join(carpeta, '%02d.png' % i))
        print(nombre.ljust(10), len(frames), 'cuadros de', frames[0].get_size())

    def del_zip(final, filtro):
        """Los png de un zip (los que pasan el filtro), ordenados por su numero."""
        ruta = _buscar_hoja(final)
        if not ruta: print('falta', final); return []
        z = zipfile.ZipFile(ruta)
        numero = lambda n: int(''.join(ch for ch in os.path.basename(n) if ch.isdigit()) or 0)
        return [pygame.image.load(io.BytesIO(z.read(n)), 'f.png').convert_alpha() for n in sorted((n for n in z.namelist() if filtro(n)), key=numero)]

    pygame.init(); pygame.display.set_mode((1, 1))
    ruta = _buscar_hoja('Weather - Rain.png')
    if ruta:
        hoja = pygame.image.load(ruta).convert()
        guardar('lluvia', del_medio([sin_fondo(hoja.subsurface((8 + 248 * (i % 5), 8 + 168 * (i // 5), 240, 160))) for i in range(61)]))
    else: print('falta la hoja Weather - Rain')
    granizo = del_zip('Weather - Hail.zip', lambda n: n.endswith('.png') and 'Tiles' not in n)
    if granizo: guardar('granizo', del_medio(granizo))
    brasas = del_zip('Weather - Embers.zip', lambda n: n.endswith('.png'))
    if brasas: guardar('brasas', [f.convert() for f in brasas])
    ruta = _buscar_hoja('Weather - Miscellaneous Weather Effects.png')
    if ruta:
        hoja = pygame.image.load(ruta).convert()
        guardar('nieve', [sin_fondo(hoja.subsurface((8 + 72 * (i % 4), 440 + 40 * (i // 4), 64, 32))) for i in range(16)])
        guardar('ventisca', [sin_fondo(hoja.subsurface((304 + 40 * (i % 4), 440 + 40 * (i // 4), 32, 32))) for i in range(16)])
        guardar('arena', [hoja.subsurface((8 + 128 * i, 608, 120, 32)).copy() for i in range(2)])
        nubes = pygame.Surface((720, 408), pygame.SRCALPHA)           # la mancha azul de las nubes -> sombra
        pygame.mask.from_threshold(hoja.subsurface((8, 16, 720, 408)), (82, 115, 189), (12, 12, 12, 255)).to_surface(nubes, setcolor=(10, 14, 40, 255), unsetcolor=(0, 0, 0, 0))
        guardar('nubes', [nubes])
    else: print('falta la hoja Weather - Miscellaneous Weather Effects')
    ruta = _buscar_hoja('Weather - Fog.png')
    if ruta: guardar('niebla', [pygame.image.load(ruta).convert().subsurface((8, 16, 336, 120)).copy()])
    ruta = _buscar_hoja('Weather - Sunny.png')
    if ruta:
        hoja = pygame.image.load(ruta).convert()
        guardar('sol', [sin_fondo(hoja.subsurface((8 + 248 * (i % 3), 8 + 120 * (i // 3), 240, 112))) for i in range(13)])


# ==================== las chozas del Red Rescue Team (el barrio del refugio) ====================

def herramienta_casas():
    """De las hojas 'Huts' del Red Rescue Team (una por pokemon: Pikachu Hut, Mudkip Hut...) arma assets/mundo/casas/:
        <pokemon>_afuera.png    el jardin con la choza (la parte de arriba de la hoja, 312 px de alto), sin el bosque de alrededor
                                (chocaba con el del jardin vecino): queda pasto y los arboles se pegan sueltos (python herramientas.py aldea)
        <pokemon>_adentro.png   la choza por dentro (la parte de abajo, sobre negro): solo el pedazo mas grande, sin carteles ni llamitas sueltas
        <pokemon>_bandera.png   los cuadros de la bandera que flamea, en una tira (va en el mastil del jardin)
    Las usa mundo.generacion: el barrio es una fila de jardines y 'Tu casa' es la choza por dentro."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    destino = os.path.join(assets, 'mundo', 'casas')
    ALTO = 312                                                      # alto del jardin (las hojas mas viejas, de otro alto, no se usan)
    NEGRO = (0, 0, 0, 255)

    def una(ruta, nombre):
        """Recorta el jardin, el interior y la bandera de una hoja. False si la hoja tiene otra forma."""
        hoja = pygame.image.load(ruta).convert_alpha()
        w, h = hoja.get_size()
        negro = lambda x, y: tuple(hoja.get_at((x, y))) == NEGRO
        if h < ALTO + 200 or not (negro(1, ALTO) and negro(w - 2, ALTO)) or negro(w - 2, ALTO - 4): return False
        ancho_caja = next((x for x in range(w) if not any(negro(x, y) for y in range(40))), 0)      # el recuadro negro de las banderas
        alto_caja = 72 if ancho_caja else 0                           # (todas las hojas lo tienen del mismo alto)
        afuera = hoja.subsurface((0, 0, w, ALTO)).copy()
        if ancho_caja and alto_caja: afuera.fill(PISOS_RRT[0], (0, 0, ancho_caja, alto_caja))   # el recuadro de las banderas: pasto
        afuera = _sin_bosque(afuera)                                  # sin el bosque de alrededor: los arboles van sueltos (herramienta_aldea)
        pygame.image.save(afuera, os.path.join(destino, nombre + '_afuera.png'))
        abajo = hoja.subsurface((0, ALTO, w, h - ALTO)).copy()        # el interior: el pedazo mas grande de lo que no es negro
        pa = pygame.PixelArray(abajo); pa.replace((0, 0, 0), (0, 0, 0, 0)); pa.close()
        mayor = max(pygame.mask.from_surface(abajo).connected_components(2000), key=lambda m_: m_.count())
        caja = mayor.get_bounding_rects()[0]
        solo = pygame.Surface(abajo.get_size(), pygame.SRCALPHA)       # (lo que no es de ese pedazo, aunque caiga adentro del recorte, no va)
        mayor.to_surface(solo, setsurface=abajo, unsetcolor=None)
        adentro = pygame.Surface(caja.size); adentro.fill((0, 0, 0))
        adentro.blit(solo, (0, 0), caja)
        pygame.image.save(adentro, os.path.join(destino, nombre + '_adentro.png'))
        caja_b = hoja.subsurface((0, 0, ancho_caja, min(alto_caja, 44))).copy()   # las banderas: los dibujitos de color del recuadro (el texto es blanco)
        pa = pygame.PixelArray(caja_b); pa.replace((0, 0, 0), (0, 0, 0, 0)); pa.close()
        cuadros = [r for r in pygame.mask.from_surface(caja_b).get_bounding_rects() if r.width >= 14 and r.height >= 10 and r.width <= 40]
        cuadros = [r for r in cuadros if sum(1 for x in range(r.x, r.right, 2) for y in range(r.y, r.bottom, 2) if min(caja_b.get_at((x, y))[:3]) < 200) > 12]
        cuadros.sort(key=lambda r: (r.y // 12, r.x))
        if cuadros:
            lado_w, lado_h = max(r.width for r in cuadros), max(r.height for r in cuadros)
            tira = pygame.Surface((lado_w * len(cuadros), lado_h), pygame.SRCALPHA)
            for i, r in enumerate(cuadros): tira.blit(caja_b, (i * lado_w, lado_h - r.height), r)
            pygame.image.save(tira, os.path.join(destino, nombre + '_bandera.png'))
        print(nombre.ljust(11), 'jardin', afuera.get_size(), 'interior', adentro.get_size(), 'bandera', len(cuadros), 'cuadros')
        return True

    pygame.init(); pygame.display.set_mode((1, 1))
    os.makedirs(destino, exist_ok=True)
    hechas = 0
    for carpeta, _, archivos in os.walk(assets):
        if os.sep + 'mundo' in carpeta or os.sep + 'sprites' in carpeta: continue
        for archivo in sorted(archivos):
            if ' - Huts - ' not in archivo or not archivo.endswith(' Hut.png'): continue
            hechas += una(os.path.join(carpeta, archivo), archivo.split(' - Huts - ')[1][:-8].lower())
    print(hechas, 'chozas en assets/mundo/casas' if hechas else 'faltan las hojas "Huts" del Red Rescue Team (assets/hojas/faltan.txt)')


# ==================== la aldea: arboles sueltos, flores, cercas y las chozas de la plaza ====================

# colores de las hojas 'Huts' del Red Rescue Team: los tres pisos (pasto, claro y arena), el bosque azulado y la sombra de los arboles
PISOS_RRT = ((112, 200, 80), (176, 240, 120), (248, 248, 192))
BOSQUE_RRT = {(16, 184, 152), (0, 128, 136), (0, 96, 104), (0, 160, 144), (0, 56, 72), (0, 32, 48)}
SOMBRA_RRT = (32, 136, 128)
ARBOL_RRT = {(16, 112, 56), (32, 136, 64), (16, 88, 48), (8, 72, 40), (40, 160, 88), (72, 192, 88), (56, 176, 88), (80, 224, 96), (88, 240, 104), (0, 48, 48), (120, 64, 48)}   # el arbol verde
BORDES_RRT = {(80, 184, 144), (96, 192, 112), (160, 216, 104), (163, 73, 73), (0, 0, 0)}     # bordecitos del pasto y el fondo de la hoja


def _es_piso_rrt(c, margen=24):
    """Si ese color es pasto, claro o arena de las hojas de chozas (o casi)."""
    return any(max(abs(c[i] - b[i]) for i in range(3)) <= margen for b in PISOS_RRT)


def _suelto(hoja, caja, minimo=30, sombra=True, centro=None):
    """Recorta de una hoja de chozas lo que hay en 'caja' sin el piso: desde los bordes se borra el pasto, el claro, la arena y el bosque.
    Quedan las cosas (arbol, choza, cerca...) sobre transparente; la sombra azulada pasa a ser una sombra negra que deja ver el piso.
    minimo: los pedacitos mas chicos se tiran (matitas de pasto). centro: si se da, solo queda el pedazo que toca ese punto de la caja."""
    sub = hoja.subsurface(pygame.Rect(caja).clip(hoja.get_rect())).copy().convert_alpha()
    w, h = sub.get_size()
    afuera = lambda c: c[3] == 0 or c[:3] in BOSQUE_RRT or c[:3] in BORDES_RRT or (not sombra and c[:3] == SOMBRA_RRT) or _es_piso_rrt(c)
    pendientes = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for x in (0, w - 1) for y in range(h)]
    visto = set()
    while pendientes:
        p = pendientes.pop()
        if p in visto or not (0 <= p[0] < w and 0 <= p[1] < h): continue
        visto.add(p)
        if not afuera(tuple(sub.get_at(p))): continue
        sub.set_at(p, (0, 0, 0, 0))
        pendientes += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
    limpio = pygame.Surface((w, h), pygame.SRCALPHA)
    for parte in pygame.mask.from_surface(sub).connected_components(minimo):       # sin las matitas sueltas
        if centro and not parte.get_at(centro): continue
        if parte.get_bounding_rects()[0].height <= 3: continue                    # ni las rayitas del borde del claro
        parte.to_surface(limpio, setsurface=sub, unsetcolor=None)
    pa = pygame.PixelArray(limpio); pa.replace(SOMBRA_RRT, (0, 0, 0, 70)); pa.close()   # la sombra sirve sobre cualquier piso
    vecinos = lambda x, y: [tuple(limpio.get_at((x + a, y + b))) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + a < w and 0 <= y + b < h]
    orilla = [(x, y) for x in range(w) for y in range(h) if limpio.get_at((x, y)).a == 255                     # el bordecito verde entre la sombra y el pasto
              and all(v[3] < 255 for v in vecinos(x, y)) and any(v[3] == 70 for v in vecinos(x, y))]
    for p in orilla: limpio.set_at(p, (0, 0, 0, 35))                  # queda como el borde suave de la sombra
    return limpio.subsurface(limpio.get_bounding_rect()).copy()


def _sin_bosque(jardin):
    """El jardin de una choza sin el bosque azulado que lo rodea (chocaba con el del jardin de al lado): se borra el bosque con su
    sombra, sus troncos y el bordecito de la sombra, y ahi va pasto. Los arboles se ponen despues, sueltos (mundo.generar_barrio).
    Los colores del bosque salen de la franja de arriba del jardin (ahi no hay otra cosa); se borra solo lo que esta pegado al bosque."""
    w, h = jardin.get_size()
    color = lambda p: tuple(jardin.get_at(p))[:3]
    del_bosque = {color((x, y)) for x in range(60, w - 60) for y in range(48)}
    del_bosque = {c for c in del_bosque if not _es_piso_rrt(c)} | BOSQUE_RRT | {SOMBRA_RRT} | ARBOL_RRT   # (el arbol verde del jardin tambien: toca el bosque)
    bosque = set()
    pendientes = [(x, y) for x in range(w) for y in range(h) if color((x, y)) in BOSQUE_RRT]
    while pendientes:
        p = pendientes.pop()
        if p in bosque or not (0 <= p[0] < w and 0 <= p[1] < h) or color(p) not in del_bosque: continue
        bosque.add(p)
        pendientes += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
    resto = pygame.mask.Mask((w, h))                                 # puntitos que quedaron sueltos al lado de lo borrado (pedazos de tronco)
    for x in range(w):
        for y in range(h):
            if (x, y) not in bosque and not _es_piso_rrt(color((x, y))): resto.set_at((x, y), 1)
    for parte in resto.connected_components():
        caja = parte.get_bounding_rects()[0]
        if parte.count() > 16 and not (parte.count() < 300 and (caja.x == 0 or caja.right == w)): continue
        puntos = [(x, y) for x in range(caja.x, caja.right) for y in range(caja.y, caja.bottom) if parte.get_at((x, y))]
        if parte.count() <= 16 and any((x + a, y + b) in bosque for x, y in puntos for a in (-1, 0, 1) for b in (-1, 0, 1)): bosque.update(puntos)
        elif parte.count() < 300 and (caja.x == 0 or caja.right == w): bosque.update(puntos)                # media flor cortada por el borde de la hoja
    limpio = jardin.copy()
    for p in bosque: limpio.set_at(p, (*PISOS_RRT[0], 255))
    return limpio


def herramienta_aldea():
    """De las hojas 'Huts' del Red Rescue Team saca las cosas sueltas de la aldea (el fondo de pasto se vuelve transparente):
        assets/mundo/objetos/arbol.png, arbol_bosque.png (el mismo en azulado), arbusto.png, tocon.png, cerca.png, cerca_v.png, cartel.png, mata.png
        assets/mundo/objetos/flor_roja.png, flor_amarilla.png   las flores que se mueven: tira de 4 cuadros
        assets/mundo/objetos/parcela_<nombre>.png               las chozas de la plaza con su patio: agua, fuego, planta, roca, hoja y las obras
        assets/mundo/medieval/objetos/arbol.png                 el arbol azulado, para los bosques de la Edad Media
        assets/mundo/casas/borde_calle.png                      el borde de abajo de la calle del barrio (arena -> pasto)
    El arbol es UNO solo y se pega suelto donde haga falta (barrio, plaza, hall, isla y eras): ya no se usan tiras de arboles pegados."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    objetos, casas = os.path.join(raiz, 'assets', 'mundo', 'objetos'), os.path.join(raiz, 'assets', 'mundo', 'casas')
    pygame.init(); pygame.display.set_mode((1, 1))
    os.makedirs(objetos, exist_ok=True); os.makedirs(casas, exist_ok=True)
    hechos = []
    def hoja_de(nombre):
        ruta = _buscar_hoja(' - Huts - ' + nombre + '.png')
        return pygame.image.load(ruta).convert_alpha() if ruta else None
    def guardar(img, carpeta, nombre):
        pygame.image.save(img, os.path.join(carpeta, nombre + '.png')); hechos.append(nombre + ' ' + str(img.get_size()))
    agua = hoja_de('Water Hut')
    if agua:
        arbol = _suelto(agua, (388, 163, 92, 84), centro=(46, 30))        # el arbol redondo de la derecha del jardin, con su sombra
        guardar(arbol, objetos, 'arbol')
        verdes = sorted(ARBOL_RRT - {(0, 48, 48), (120, 64, 48)}, key=sum)
        azules = sorted(BOSQUE_RRT | {(32, 208, 168), (72, 224, 184), (0, 72, 88)}, key=sum)   # del mas oscuro al mas claro, como los verdes
        bosque = arbol.copy()
        pa = pygame.PixelArray(bosque)
        for v, a in zip(verdes, azules): pa.replace(v, a)                  # la misma copa con los colores del bosque del PMD
        pa.close()
        guardar(bosque, objetos, 'arbol_bosque')
        medieval = os.path.join(raiz, 'assets', 'mundo', 'medieval', 'objetos')
        os.makedirs(medieval, exist_ok=True); guardar(bosque, medieval, 'arbol')   # el bosque de la Edad Media usa el azulado
        guardar(_suelto(agua, (388, 116, 44, 44), centro=(20, 22)), objetos, 'tocon')
        guardar(_suelto(agua, (74, 282, 66, 28), sombra=False), objetos, 'cerca')
        guardar(_suelto(agua, (140, 192, 24, 92), sombra=False), objetos, 'cerca_v')
        guardar(_suelto(agua, (54, 292, 28, 30), sombra=False), objetos, 'cartel')
        for nombre, y in (('flor_roja', 560), ('flor_amarilla', 623)):     # 'Flower Frames': 4 cuadros en recuadros blancos
            tira = pygame.Surface((32 * 4, 30), pygame.SRCALPHA)
            for i in range(4):
                cuadro = agua.subsurface((43 + 63 * i, y, 32, 30)).copy()
                pa = pygame.PixelArray(cuadro); pa.replace((255, 255, 255), (0, 0, 0, 0)); pa.replace((0, 0, 0), (0, 0, 0, 0)); pa.close()
                tira.blit(cuadro, (32 * i, 0))
            guardar(tira, objetos, nombre)
        borde = agua.subsurface((0, 340, 150, 28)).copy()                 # debajo de la calle: la arena y la franja clara (despues sigue el pasto)
        doble = pygame.Surface((300, 28)); doble.blit(borde, (0, 0)); doble.blit(pygame.transform.flip(borde, True, False), (150, 0))   # espejado: se repite sin cortes
        guardar(doble, casas, 'borde_calle')
        mata = pygame.mask.Mask(agua.get_size())                          # una matita de pasto (las marquitas claras del piso)
        for x in range(395, 470):
            for y in range(236, 262):
                if tuple(agua.get_at((x, y)))[:3] == (160, 216, 104): mata.set_at((x, y), 1)
        partes = sorted(mata.connected_components(4), key=lambda m_: -m_.count())
        if partes:
            caja = partes[0].get_bounding_rects()[0].inflate(8, 4).clip(agua.get_rect())
            img = pygame.Surface(caja.size, pygame.SRCALPHA)
            for x in range(caja.w):
                for y in range(caja.h):
                    if mata.get_at((caja.x + x, caja.y + y)): img.set_at((x, y), (160, 216, 104, 255))
            guardar(img.subsurface(img.get_bounding_rect()).copy(), objetos, 'mata')
    pikachu = hoja_de('Pikachu Hut')
    if pikachu: guardar(_suelto(pikachu, (94, 158, 28, 32), sombra=False), objetos, 'arbusto')   # una mata del cerco
    # las chozas de la plaza: (hoja, caja del patio en la hoja)
    PARCELAS = {'agua': ('Water Hut', (164, 84, 226, 216)), 'fuego': ('Fire Hut', (106, 124, 228, 216)), 'planta': ('Plant Hut', (100, 136, 232, 214)),
                'roca': ('Rock Hut', (100, 124, 232, 222)), 'hoja': ('Grass Hut', (100, 150, 232, 200)),
                'obra_fuego': ('Fire Hut (Construction)', (18, 8, 226, 216)), 'obra_agua': ('Water Hut (Construction)', (18, 8, 226, 222))}
    for nombre, (hoja_n, caja) in PARCELAS.items():
        hoja = hoja_de(hoja_n)
        if hoja: guardar(_suelto(hoja, caja, minimo=26 if nombre == 'planta' else 100, sombra=False), objetos, 'parcela_' + nombre)   # (las piedritas del camino de la de planta son chicas)
    print(len(hechos), 'piezas de la aldea:', ', '.join(hechos) if hechos else 'faltan las hojas "Huts" del Red Rescue Team (assets/hojas/faltan.txt)')


# ==================== chispas de los golpes (hoja 'Effects' del Red Rescue Team) ====================

def herramienta_chispas():
    """De la hoja 'Miscellaneous - Effects' del Red Rescue Team saca dos efectos (tiras de cuadros cuadrados, como las lee mundo.efectos):
        assets/efectos/estrella.png   la estrellita amarilla que salta cuando un golpe conecta (chica, grande, grande, chica)
        assets/efectos/brillo.png     el brillito blanco (frenesi, hitos de la cadena de golpes)"""
    ruta = _buscar_hoja('Red Rescue Team - Miscellaneous - Effects.png')
    if not ruta: print('falta la hoja Miscellaneous - Effects del Red Rescue Team'); return
    pygame.init(); pygame.display.set_mode((1, 1))
    hoja = pygame.image.load(ruta).convert_alpha()
    fondo = tuple(hoja.get_at((0, 0)))
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'efectos')
    for nombre, caja, orden in (('estrella', (20, 22, 46, 28), (0, 1, 1, 0)), ('brillo', (4, 74, 62, 24), (0, 1, 2, 1, 0))):
        zona = hoja.subsurface(caja).copy()
        pa = pygame.PixelArray(zona); pa.replace(fondo, (0, 0, 0, 0)); pa.close()
        cajas = sorted(pygame.mask.from_surface(zona).get_bounding_rects(), key=lambda r: r.x)
        cajas = [r for r in cajas if r.width * r.height >= 30]          # (sin puntitos sueltos)
        lado = max(max(r.size) for r in cajas)
        tira = pygame.Surface((lado * len(orden), lado), pygame.SRCALPHA)
        for i, k in enumerate(orden):
            r = cajas[min(k, len(cajas) - 1)]
            tira.blit(zona, (i * lado + (lado - r.width) // 2, (lado - r.height) // 2), r)
        pygame.image.save(tira, os.path.join(destino, nombre + '.png'))
        print(nombre, len(cajas), 'dibujos ->', len(orden), 'cuadros de', lado, 'px')


# ==================== el portal y el espiritu (escenas del cosmos) ====================

def herramienta_portal():
    """De 'Dimensional Hole' del Explorers of Time/Darkness arma assets/efectos/portal.png: los 8 cuadros del portal violeta
    (4 latiendo, 2 agrietandose y 2 rompiendose en pedazos) en cuadrados de 112 px, todos alineados al mismo centro.
    Es el portal de las escenas: para ir entre eras, en la llegada a cada era y al final de la partida nueva."""
    ruta = _buscar_hoja(' - Dimensional Hole.png')
    if not ruta: print('falta la hoja Dimensional Hole del Explorers of Time/Darkness'); return
    pygame.init(); pygame.display.set_mode((1, 1))
    hoja = pygame.image.load(ruta).convert()
    verde, gris = tuple(hoja.get_at((0, 0)))[:3], tuple(hoja.get_at((5, 5)))[:3]
    fuera = pygame.mask.from_threshold(hoja, verde, (2, 2, 2, 255)); fuera.invert()
    piezas = sorted((c for c in fuera.connected_components() if c.count() > 2000), key=lambda c: (c.get_bounding_rects()[0].y // 40, c.get_bounding_rects()[0].x))
    tira = pygame.Surface((112 * len(piezas), 112), pygame.SRCALPHA)
    for i, pieza in enumerate(piezas):
        caja = pieza.get_bounding_rects()[0]
        cuadro = pygame.Surface(caja.size, pygame.SRCALPHA)
        cuadro.blit(pieza.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)), (0, 0), caja)
        cuadro.blit(hoja.subsurface(caja), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pa = pygame.PixelArray(cuadro); pa.replace(gris, (0, 0, 0, 0)); pa.close()
        tira.blit(cuadro, (i * 112 + 16, 24))                    # (el cuadro de 80x64 queda centrado; el ultimo se pasa con los pedazos)
    pygame.image.save(tira, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'efectos', 'portal.png'))
    print(len(piezas), 'cuadros del portal en assets/efectos/portal.png')


def herramienta_espiritu():
    """El espiritu de la partida nueva: assets/efectos/aura.png, la luz redonda del cielo de 'Moonlight' del Explorers of Sky (el
    resplandor de la luna sin el cielo ni las estrellas: la mediana de cada anillo alrededor del centro, asi queda redonda), y
    assets/efectos/estrellita.png, la estrella que titila del efecto 0038 de los Attack Effects del Explorers of Sky, y
    assets/efectos/mano.png, la mano rosa del efecto 0200 (cuando Celebi te agarra de la mano)."""
    ruta = _buscar_hoja(' - Moonlight.png')
    if not ruta: print('falta la hoja Moonlight del Explorers of Sky'); return
    pygame.init(); pygame.display.set_mode((1, 1))
    hoja = pygame.image.load(ruta).convert()
    panel = pygame.Rect(316, 0, 311, 240)
    zona = lambda x, y: sum(hoja.get_at((x + a, y + b))[2] for a in range(-12, 13, 4) for b in range(-12, 13, 4))   # azul alrededor (una estrella sola no gana)
    cx, cy = max(((x, y) for x in range(panel.x + 30, panel.right - 30, 3) for y in range(panel.y + 30, panel.bottom - 30, 3)), key=lambda p: zona(*p))
    cielo = hoja.get_at((panel.x + 6, panel.bottom - 6))
    RADIO = 70
    anillos = {}
    for y in range(cy - RADIO, cy + RADIO + 1):
        for x in range(cx - RADIO, cx + RADIO + 1):
            d = round(math.hypot(x - cx, y - cy))
            if d <= RADIO: anillos.setdefault(d, []).append(tuple(hoja.get_at((x, y)))[:3])
    perfil = {d: [sorted(c[k] for c in v)[len(v) // 2] for k in range(3)] for d, v in anillos.items()}   # la mediana: las estrellas no cuentan
    aura = pygame.Surface((RADIO * 2 + 1, RADIO * 2 + 1))
    for y in range(RADIO * 2 + 1):
        for x in range(RADIO * 2 + 1):
            d = round(math.hypot(x - RADIO, y - RADIO))
            if d <= RADIO: aura.set_at((x, y), [max(0, perfil[d][k] - cielo[k]) for k in range(3)])
    pygame.image.save(aura, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'efectos', 'aura.png'))
    print('aura del espiritu en assets/efectos/aura.png (centro', (cx, cy), ')')
    zip_ = next((os.path.join(c, a) for c, _, archivos in os.walk(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'))
                 for a in archivos if a.endswith('Explorers of Sky - Miscellaneous - Attack Effects.zip')), None)
    if not zip_: print('falta Attack Effects.zip del Explorers of Sky (la estrellita del espiritu)'); return
    import zipfile, io
    z = zipfile.ZipFile(zip_)
    cuadros = sorted(n for n in z.namelist() if n.startswith('move_VFX/0038/000/') and n.endswith('.png'))
    estrellas = [pygame.image.load(io.BytesIO(z.read(cuadros[i * len(cuadros) // 6]))).convert_alpha() for i in range(6)]   # la estrella y sus crucecitas, titilando
    lado = max(max(e.get_size()) for e in estrellas)   # (sin recortar: asi la estrella queda siempre en el centro del cuadro)
    lado = max(max(e.get_size()) for e in estrellas)
    tira = pygame.Surface((lado * len(estrellas), lado), pygame.SRCALPHA)
    for i, e in enumerate(estrellas): tira.blit(e, e.get_rect(center=(i * lado + lado // 2, lado // 2)))
    pygame.image.save(tira, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'efectos', 'estrellita.png'))
    print('la estrellita del espiritu (efecto 0038 del Explorers of Sky) en assets/efectos/estrellita.png')
    cuadros = sorted(n for n in z.namelist() if n.startswith('move_VFX/0200/000/') and n.endswith('.png'))[:9]   # la mano rosa (los primeros 9)
    tira = pygame.Surface((64 * len(cuadros), 64), pygame.SRCALPHA)
    for i, n in enumerate(cuadros): tira.blit(pygame.image.load(io.BytesIO(z.read(n))).convert_alpha(), (i * 64 + 4, 0))
    pygame.image.save(tira, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'efectos', 'mano.png'))
    print('la mano de Celebi (efecto 0200 del Explorers of Sky) en assets/efectos/mano.png')


# ==================== el icono del ejecutable ====================

def herramienta_icono():
    """Arma assets/interfaz/icono.ico (el icono de Pokemanic.exe) con la cara de Celebi del retrato del PMD, agrandada sin suavizar.
    El .ico lleva adentro un PNG de 256x256 (lo entiende Windows desde Vista)."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    cara = os.path.join(raiz, 'assets', 'sprites', 'pokemones', 'sprite_celebi', 'portrait', 'Happy.png')
    if not os.path.isfile(cara): cara = os.path.join(os.path.dirname(cara), 'Normal.png')
    pygame.init(); pygame.display.set_mode((1, 1))
    temporal = os.path.join(raiz, 'assets', 'interfaz', 'icono_256.png')
    pygame.image.save(pygame.transform.scale(pygame.image.load(cara), (256, 256)), temporal)
    png = open(temporal, 'rb').read(); os.remove(temporal)
    import struct
    ico = struct.pack('<HHH', 0, 1, 1) + struct.pack('<BBBBHHII', 0, 0, 0, 0, 1, 32, len(png), 22) + png
    open(os.path.join(raiz, 'assets', 'interfaz', 'icono.ico'), 'wb').write(ico)
    print('assets/interfaz/icono.ico listo')


# ==================== el logo ====================

def herramienta_logo():
    """Pasa el logo del juego (assets/typo_logo_pokemanic.png: pixel art agrandado sobre un fondo azul liso) a assets/interfaz/logo.png:
    a su tamaño de pixel original (un pixel por bloque) y con el fondo transparente. El borde azul de 'Poké' se queda (es casi del color
    del fondo, pero no igual: el fondo se borra desde afuera y solo lo que es exactamente de su color).
    La pantalla de titulo y el menu lo agrandan sin suavizar (menus.dibujar_logo); si falta, arman el logo con las letras del PMD."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    origen = os.path.join(raiz, 'assets', 'typo_logo_pokemanic.png')
    if not os.path.isfile(origen): print('falta assets/typo_logo_pokemanic.png'); return
    pygame.init(); pygame.display.set_mode((1, 1))
    hoja = pygame.image.load(origen).convert()
    w, h = hoja.get_size()
    fondo = tuple(hoja.get_at((2, 2)))[:3]
    lejos = lambda c, margen: max(abs(c[i] - fondo[i]) for i in range(3)) > margen
    puntos = [(x, y) for y in range(0, h, 2) for x in range(0, w, 2) if lejos(hoja.get_at((x, y)), 12)]
    x0, y0, x1, y1 = min(p[0] for p in puntos), min(p[1] for p in puntos), max(p[0] for p in puntos), max(p[1] for p in puntos)
    y_medio, largos, n, antes = (y0 + y1) // 2, {}, 0, None
    for x in range(x0, x1):                                          # el lado del bloque: el largo mas comun de un tramo del mismo color
        c = tuple(hoja.get_at((x, y_medio)))[:3]
        if c == antes: n += 1
        else: largos[n] = largos.get(n, 0) + 1; n, antes = 1, c
    lado = max((l for l in largos if l > 3), key=lambda l: largos[l])
    def cortes(horizontal, fase):                                    # cuantos cambios de color caen justo en la grilla con esa fase
        """Cuántos cambios de color caen justo en la grilla con esa fase (para encontrar el tamaño del pixel del logo)."""
        total = 0
        for k in range(8):
            fijo = (y0 + (y1 - y0) * (k + 1) // 9) if horizontal else (x0 + (x1 - x0) * (k + 1) // 9)
            for v in range((x0 if horizontal else y0) - lado + fase, (x1 if horizontal else y1), lado):
                if v < 1: continue
                a_, b_ = ((v - 1, fijo), (v, fijo)) if horizontal else ((fijo, v - 1), (fijo, v))
                total += hoja.get_at(a_) != hoja.get_at(b_)
        return total
    fx, fy = max(range(lado), key=lambda f: cortes(True, f)), max(range(lado), key=lambda f: cortes(False, f))
    gx, gy = x0 - lado + fx, y0 - lado + fy                          # donde arranca la grilla (un bloque antes del logo)
    while gx > x0 - lado * 2: gx -= lado
    while gy > y0 - lado * 2: gy -= lado
    cols, filas = (x1 - gx) // lado + 3, (y1 - gy) // lado + 3
    chico = pygame.Surface((cols, filas), pygame.SRCALPHA)
    for f in range(filas):
        for c in range(cols):
            x, y = gx + c * lado + lado // 2, gy + f * lado + lado // 2
            chico.set_at((c, f), (*tuple(hoja.get_at((x, y)))[:3], 255) if 0 <= x < w and 0 <= y < h else (*fondo, 255))
    pendientes = [(c, f) for c in range(cols) for f in (0, filas - 1)] + [(c, f) for c in (0, cols - 1) for f in range(filas)]
    while pendientes:                                                # el fondo se borra desde afuera
        c, f = pendientes.pop()
        if not (0 <= c < cols and 0 <= f < filas): continue
        p = chico.get_at((c, f))
        if p.a == 0 or lejos(p, 3): continue
        chico.set_at((c, f), (0, 0, 0, 0))
        pendientes += [(c + 1, f), (c - 1, f), (c, f + 1), (c, f - 1)]
    logo = chico.subsurface(chico.get_bounding_rect()).copy()
    destino = os.path.join(raiz, 'assets', 'interfaz', 'logo.png')
    pygame.image.save(logo, destino)
    print('logo', logo.get_size(), 'pixeles (bloques de', lado, 'px) ->', destino)


# ==================== arenas de los jefes (Dungeon Boss Rooms del Red Rescue Team) ====================

def herramienta_arenas():
    """De las hojas 'Dungeon Boss Rooms' (y dos 'Friend Areas') del Red Rescue Team arma la arena ya dibujada de cada jefe:
        assets/mundo/arenas/<era>_<tipo>.png    el recorte de la hoja: la plataforma y un margen alrededor (sin carteles ni esquinas negras)
        assets/mundo/arenas/<era>_<tipo>.json   {'k': cuanto se agranda, 'piso': poligono de la plataforma en pixeles del recorte, 'brasas': si flotan brasas}
    tipo es 'jefe' (el jefe de la era), 'regi' o 'final' (Arceus). mundo.generacion.generar_arena las usa solas si estan: el piso caminable
    es el poligono (medido a mano sobre cada hoja, en pixeles de la hoja) y todo lo demas es pared invisible.
    Cada entrada: hoja, k, margen, zona de la hoja que sirve (x, y, ancho, alto) y poligono."""
    import json as _json
    raiz = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(raiz, 'assets', 'mundo', 'arenas')
    circulo = lambda cx, cy, r, n=20: [(round(cx + r * math.cos(i * 2 * math.pi / n)), round(cy + r * math.sin(i * 2 * math.pi / n))) for i in range(n)]
    ARENAS = {
        'glaciacion_jefe': ('Dungeon Boss Rooms - Frosty Grotto', 6, 64, (24, 0, 408, 352), [(140, 84), (330, 84), (355, 108), (358, 270), (335, 298), (140, 298), (108, 275), (102, 110)]),
        'glaciacion_regi': ('Friend Areas - Frigid Cavern', 4, 64, (0, 0, 480, 360),
                            [(150, 112), (330, 112), (400, 140), (425, 190), (370, 235), (350, 300), (320, 345), (160, 345), (130, 300), (110, 235), (55, 190), (80, 140)]),
        'piedra_jefe': ('Dungeon Boss Rooms - Wish Cave', 7, 56, (0, 0, 384, 328), [(106, 80), (278, 80), (278, 274), (106, 274)]),
        'piedra_regi': ('Dungeon Boss Rooms - Mt. Faraway', 6, 64, (0, 0, 504, 448), [(150, 108), (385, 108), (398, 130), (398, 320), (380, 338), (150, 338), (135, 320), (135, 130)]),
        'metales_jefe': ('Dungeon Boss Rooms - Mt. Steel', 6, 64, (12, 12, 430, 330),
                         [(20, 135), (110, 132), (150, 142), (300, 142), (340, 132), (440, 135), (440, 190), (345, 195), (340, 260), (300, 278), (165, 278), (120, 260), (115, 195), (20, 190)]),
        'metales_regi': ('Dungeon Boss Rooms - Magma Cavern', 6, 56, (24, 22, 384, 328), [(125, 85), (315, 85), (325, 100), (325, 290), (310, 300), (125, 300), (110, 290), (110, 100)], True),
        'medieval_jefe': ('Dungeon Boss Rooms - Northern Range', 7, 64, (0, 0, 456, 432), [(160, 147), (295, 147), (335, 180), (342, 240), (300, 285), (150, 285), (118, 240), (118, 185)]),
        'medieval_regi': ('Dungeon Boss Rooms - Sky Tower', 5, 64, (0, 0, 528, 496),
                          [(200, 170), (290, 150), (340, 185), (385, 215), (400, 300), (385, 380), (330, 420), (240, 425), (160, 395), (125, 330), (120, 260), (150, 200)]),
        'moderna_jefe': ('Dungeon Boss Rooms - Lightning Field', 6, 48, (46, 22, 384, 328), [(105, 90), (350, 90), (355, 300), (330, 325), (125, 325), (105, 300)]),
        'moderna_regi': ('Dungeon Boss Rooms - Mt. Thunder', 6, 64, (24, 45, 384, 290), [(140, 78), (300, 78), (340, 105), (350, 200), (352, 290), (300, 302), (130, 302), (92, 285), (95, 180), (105, 105)]),
        'origen_regi': ('Dungeon Boss Rooms - Stormy Sea', 7, 40, (0, 0, 444, 362), [(130, 95), (365, 95), (375, 110), (375, 310), (360, 322), (130, 322), (118, 310), (118, 110)]),
        # el sello de Silver Trench esta cortado abajo y a la derecha: se arma entero espejando el cuarto de arriba a la izquierda
        'origen_final': ('Dungeon Boss Rooms - Silver Trench', 7, 60, (0, 0, 480, 470), circulo(240, 235, 130), False, (240, 235)),
    }

    def main():
        """Recorta cada arena alrededor de su plataforma y guarda el poligono en pixeles del recorte."""
        pygame.init(); pygame.display.set_mode((1, 1))
        os.makedirs(destino, exist_ok=True)
        for nombre, (hoja, k, margen, zona, piso, *resto) in ARENAS.items():
            ruta = _buscar_hoja(hoja + '.png')
            if not ruta: print('falta la hoja', hoja); continue
            img = pygame.image.load(ruta).convert()
            if len(resto) > 1:                                         # espejar: el cuarto de arriba a la izquierda, cuatro veces
                ex, ey = resto[1]
                cuarto = img.subsurface((0, 0, ex, ey))
                img = pygame.Surface((ex * 2, ey * 2))
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)): img.blit(pygame.transform.flip(cuarto, bool(dx), bool(dy)), (dx * ex, dy * ey))
            zona = pygame.Rect(zona).clip(img.get_rect())
            xs, ys = [p[0] for p in piso], [p[1] for p in piso]
            caja = pygame.Rect(min(xs) - margen, min(ys) - margen, max(xs) - min(xs) + 2 * margen, max(ys) - min(ys) + 2 * margen).clip(zona)
            pygame.image.save(img.subsurface(caja), os.path.join(destino, nombre + '.png'))
            datos_a = {'k': k, 'piso': [(x - caja.x, y - caja.y) for x, y in piso], 'brasas': bool(resto and resto[0])}
            with open(os.path.join(destino, nombre + '.json'), 'w', encoding='utf-8') as f: _json.dump(datos_a, f)
            print(nombre.ljust(16), hoja.split(' - ')[1].ljust(16), 'recorte', caja.size, '-> sala de', (caja.width * k, caja.height * k))

    main()


# ==================== estados animados del Red Rescue Team ====================

def herramienta_estados():
    """De la hoja 'Status Effects' del Red Rescue Team (filas de cuadros de 16 px desde x=104; el hielo es de 32) arma las tiras
    animadas de assets/efectos/estado_<nombre>.png (una fila de cuadros cuadrados, como todos los efectos): la llama de la quemadura,
    los Zzz del sueño, la calavera del veneno, los pajaritos de la confusion, la flecha para abajo (frenado), el signo de pregunta,
    el escudo y el puño. interfaz.menus.icono_estado las dibuja arriba de la cabeza del pokemon."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    FILAS = {'quemar': (112, 16, 7), 'confuso': (128, 16, 8), 'hielo': (144, 32, 6), 'fuerza': (176, 16, 8), 'lento': (192, 16, 11),
             'dormir': (232, 16, 10), 'veneno': (248, 16, 15), 'duda': (48, 16, 10), 'alerta': (32, 16, 9), 'escudo': (96, 16, 13)}   # nombre: (y, lado, cuadros)
    pygame.init(); pygame.display.set_mode((1, 1))
    ruta = _buscar_hoja('Miscellaneous - Status Effects.png')
    if not ruta: print('falta la hoja Status Effects del Red Rescue Team'); return
    hoja = pygame.image.load(ruta).convert_alpha()
    fondo = hoja.get_at((330, 8))
    for nombre, (y, lado, cuadros) in FILAS.items():
        tira = hoja.subsurface((104, y, lado * cuadros, lado)).copy()
        pa = pygame.PixelArray(tira); pa.replace(fondo, (0, 0, 0, 0)); pa.close()
        pygame.image.save(tira, os.path.join(raiz, 'assets', 'efectos', 'estado_' + nombre + '.png'))
    print(len(FILAS), 'estados animados en assets/efectos')


def ver_salas():
    """Dibuja en texto algunas salas generadas (para ver como quedan sin abrir el juego)."""
    letras = {'suelo': '.', 'pared': '#', 'puerta': 'D', 'entrada': 'E', 'agua': '~', 'puente': '=', 'hierba': '"', 'lava': '%', 'sombra': 's'}
    for era, var in ((3, 'bosque encantado'), (1, 'cueva rupestre'), (2, 'templo de bronce')):
        sala = generacion.generar_sala(era, var, 'sur', ['norte', 'este'])
        marcas = {c for o in sala['objetos'] for c in o['celdas']}
        print(var, '-', sala['forma'], sala['simetria'], sala['piezas'])
        for f, fila in enumerate(sala['matriz']):
            print(''.join('o' if (f, c) in marcas else letras.get(t, t[0]) for c, t in enumerate(fila)))


def ver_plan():
    """Dibuja el plan de una partida: T tienda, S subjefe, J semijefe, R regi, A arceus. Y el clima de las primeras salas."""
    rec = mundos.nuevo_recorrido()
    letras = {'combate': '.', 'tienda': 'T', 'subjefe': 'S', 'jefe': 'J', 'regi': 'R', 'final': 'A'}
    for i, era in enumerate(rec['plan']):
        print(mundos.ERAS[i]['nombre'].ljust(22), ''.join(letras[t] for t in era))
    climas = []
    for _ in range(25): climas.append(rec['clima']); mundos.avanzar(rec)
    print('clima de las primeras salas:', ' > '.join(climas))


if __name__ == '__main__':
    orden = sys.argv[1] if len(sys.argv) > 1 else ''
    if orden in ('descargar', 'caras'): herramienta_descargar()
    elif orden == 'animaciones': herramienta_animaciones(sys.argv[2] if len(sys.argv) > 2 else None)
    elif orden == 'sonidos': herramienta_sonidos()
    elif orden == 'datos': herramienta_datos()
    elif orden == 'recortar' and len(sys.argv) > 2: herramienta_recortar(sys.argv[2])
    elif orden == 'hojas': herramienta_hojas()
    elif orden == 'tiles': herramienta_tiles()
    elif orden == 'decorados': herramienta_decorados()
    elif orden == 'props': herramienta_props()
    elif orden == 'cielo': herramienta_cielo()
    elif orden == 'minimapa': herramienta_minimapa()
    elif orden == 'viaje': herramienta_viaje()
    elif orden == 'efectos': herramienta_efectos()
    elif orden == 'objetos': herramienta_objetos()
    elif orden == 'paneles': herramienta_paneles()
    elif orden == 'hud': herramienta_hud()
    elif orden == 'clima': herramienta_clima()
    elif orden == 'estados': herramienta_estados()
    elif orden == 'arenas': herramienta_arenas()
    elif orden == 'casas': herramienta_casas()
    elif orden == 'aldea': herramienta_aldea()
    elif orden == 'logo': herramienta_logo()
    elif orden == 'chispas': herramienta_chispas()
    elif orden == 'icono': herramienta_icono()
    elif orden == 'portal': herramienta_portal()
    elif orden == 'espiritu': herramienta_espiritu()
    elif orden == 'salas': ver_salas()
    elif orden == 'plan': ver_plan()
    elif orden == 'visor': herramienta_visor()
    else: print(__doc__)
