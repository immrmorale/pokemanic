"""
herramientas.py - Programas aparte para preparar el juego (no se usan mientras jugas).

    python herramientas.py descargar           baja los sprites y retratos del PMD (SpriteCollab)
    python herramientas.py datos               arma datos_pokeapi.json desde la PokeAPI
    python herramientas.py recortar hoja.png   recorta sprites de una hoja y los deja en assets/mundo
    python herramientas.py hojas               baja todas las hojas (menos pokemon) de BW y los PMD a assets/hojas (via archive.org)
    python herramientas.py tiles               recorta los tiles de las mazmorras del PMD y los pone como terrenos de cada era
    python herramientas.py efectos             arma los efectos de golpes, cura, nivel... con los Attack Effects del PMD
    python herramientas.py salas               muestra en texto algunas salas generadas
    python herramientas.py plan                muestra el plan de salas de una partida
    python herramientas.py visor               ventana para mirar salas generadas sin jugar
    python herramientas.py sincronizar         baja stats, tipos y movimientos de la PokeAPI (formato viejo de datos_pokeapi.json)
    python herramientas.py verificar           compara la tabla de tipos y los movimientos con la PokeAPI
"""

import json
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

    main()


# ==================== generar datos ====================

def herramienta_datos():
    """Pide a la PokeAPI stats, movimientos, descripcion y evoluciones y los guarda en datos_pokeapi.json."""
    pokemones = datos.pokemones.pokemones

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
            if ver_plan:                                            # plan de una partida: T tienda, J semijefe, R regi, A arceus
                y += 10
                letras = {'combate': '.', 'tienda': 'T', 'jefe': 'J', 'regi': 'R', 'final': 'A'}
                for i, plan in enumerate(rec['plan']):
                    ventana.blit(chica.render(mundos.ERAS[i]['clave'][:8].ljust(9) + ''.join(letras[t] for t in plan), True, (220, 220, 140)), (x, y)); y += 18
            pygame.display.flip(); reloj.tick(30)

    main()


# ==================== sincronizar pokeapi ====================

def herramienta_sincronizar():
    """Baja de la PokeAPI stats, altura, peso, tipos y movimientos y los guarda en datos_pokeapi.json."""
    pokemones = datos.pokemones.pokemones

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

    main()


# ==================== verificar pokeapi ====================

def herramienta_verificar():
    """Compara la tabla de tipos y los movimientos del juego con los de la PokeAPI (guarda lo bajado en cache_pokeapi.json)."""
    pokemones, TABLA_TIPOS = datos.pokemones.pokemones, datos.pokemones.TABLA_TIPOS
    habilidades, sinergias = datos.habilidades, datos.sinergias

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

    try:
        verificar_tipos()
        verificar_movimientos()
    finally:
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'))


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
    """Recorta las hojas 'Dungeon Tiles' del Explorers of Sky (spriters-resource) y deja una casilla por terreno en assets/mundo/<era>/terrenos.
    Todas las hojas tienen la misma grilla: casillas de 24 px con una linea de 1 px. Grupos de 3 columnas en orden:
    Legend, Walls, Wall Alt 1, Wall Alt 2, Ground, Ground Alt 1, Ground Alt 2, (Unused Ground) y Water (agua, lava o vacio segun el lugar).
    De cada grupo se usa el tile del medio del primer bloque de 3x3: el que esta rodeado de lo mismo y se puede repetir."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    # era -> {terreno: (lugar de la hoja, grupo)}. Grupos: pared, suelo, suelo2, suelo3 (variantes del suelo), agua
    PLAN = {
        'glaciacion': {'pared': ('Vast Ice Mountain', 'pared'), 'suelo': ('Vast Ice Mountain', 'suelo'), 'agua': ('Vast Ice Mountain', 'agua'),
                       'nieve': ('7th Station Pass', 'suelo'), 'hielo': ('7th Station Pass', 'agua')},
        'piedra': {'pared': ('Barren Valley', 'pared'), 'suelo': ('Barren Valley', 'suelo'), 'agua': ('Barren Valley', 'agua')},
        'metales': {'pared': ('Deep Boulder Quarry', 'pared'), 'suelo': ('Deep Boulder Quarry', 'suelo')},
        'medieval': {'pared': ('4th Station Pass', 'pared'), 'suelo': ('4th Station Pass', 'suelo'), 'agua': ('4th Station Pass', 'agua'),
                     'hierba': ('4th Station Pass', 'suelo')},
        'moderna': {'pared': ('Temporal Tower (In the Future of Darkness)', 'pared'), 'suelo': ('Temporal Tower (In the Future of Darkness)', 'suelo'),
                    'agua': ('Temporal Tower (In the Future of Darkness)', 'agua')},
        'origen': {'pared': ('Temporal Spire (In the Future of Darkness)', 'pared'), 'suelo': ('Temporal Spire (In the Future of Darkness)', 'suelo'),
                   'agua': ('Temporal Spire (In the Future of Darkness)', 'agua')},
        '': {'arena': ('Limestone Cavern', 'suelo'), 'agua': ('4th Station Pass', 'agua')},      # para todas las eras (si la era no tiene el suyo)
    }

    def buscar_hoja(lugar):
        for carpeta in (os.path.join(assets, 'hojas'), assets):          # primero assets/hojas, si no las sueltas en assets
            if not os.path.isdir(carpeta): continue
            for archivo in os.listdir(carpeta):
                if 'Dungeon Tiles' in archivo and archivo.endswith(' - ' + lugar + '.png'): return os.path.join(carpeta, archivo)
        return None

    def columna(hoja, grupo):
        agua = 21 if hoja.get_width() <= 813 else 24                       # las hojas angostas no tienen 'Unused Ground'
        return {'pared': 4, 'suelo': 13, 'suelo2': 16, 'suelo3': 19, 'agua': agua + 1}[grupo]

    def casilla(hoja, grupo):
        """3x3 tiles iguales (72 px): el juego la estira al tamaño de la casilla."""
        x, y = 9 + 25 * columna(hoja, grupo), 163 + 25
        t = hoja.subsurface((x, y, 24, 24))
        if t.get_at((12, 12))[:3] in ((255, 0, 255), (0, 128, 128)): return None   # grupo vacio en esa hoja (magenta o el fondo)
        sup = pygame.Surface((72, 72))
        for i in range(3):
            for k in range(3): sup.blit(t, (i * 24, k * 24))
        return sup

    def main():
        pygame.init(); pygame.display.set_mode((1, 1))
        hojas, hechos, faltan = {}, 0, set()
        for era, terrenos in PLAN.items():
            carpeta = os.path.join(assets, 'mundo', era, 'terrenos') if era else os.path.join(assets, 'mundo', 'terrenos')
            for terreno, (lugar, grupo) in terrenos.items():
                if lugar not in hojas:
                    ruta = buscar_hoja(lugar)
                    hojas[lugar] = pygame.image.load(ruta).convert() if ruta else None
                if not hojas[lugar]: faltan.add(lugar); continue
                os.makedirs(carpeta, exist_ok=True)
                for sufijo, g in (('', grupo), ('_2', grupo + '2'), ('_3', grupo + '3')) if grupo == 'suelo' else (('', grupo),):
                    img = casilla(hojas[lugar], g)
                    if img: pygame.image.save(img, os.path.join(carpeta, terreno + sufijo + '.png')); hechos += 1
        print(hechos, 'casillas en assets/mundo')
        if faltan: print('faltan las hojas (bajalas de spriters-resource, Explorers of Sky > Dungeon Tiles):', ', '.join(sorted(faltan)))

    main()


# ==================== efectos de ataque del PMD ====================

def herramienta_efectos():
    """Del zip 'Attack Effects' del Explorers of Sky (move_VFX/<numero>/000/<frame>.png) arma las tiras de assets/efectos:
    una fila de frames cuadrados (como las lee mundo.efectos). Los numeros no tienen nombre: se eligieron mirandolos."""
    import io, zipfile
    raiz = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(raiz, 'assets')
    ELEGIDOS = {'golpe': '0038', 'golpe_normal': '0038', 'golpe_fuego': '0008', 'golpe_agua': '0021', 'golpe_electrico': '0222',
                'golpe_hielo': '0141', 'golpe_planta': '0076', 'golpe_veneno': '0144', 'golpe_tierra': '0002', 'golpe_roca': '0182',
                'golpe_lucha': '0221', 'golpe_psiquico': '0171', 'golpe_fantasma': '0046', 'golpe_siniestro': '0122', 'golpe_dragon': '0092',
                'golpe_acero': '0166', 'golpe_volador': '0149', 'golpe_hada': '0254',
                'explosion': '0253', 'romper': '0140', 'nivel': '0125', 'evolucion': '0180', 'cura': '0105'}
    MAX_FRAMES = 12                                                 # los largos se recortan salteando frames (un golpe no puede durar 2 segundos)

    def main():
        pygame.init(); pygame.display.set_mode((1, 1))
        zips = [os.path.join(c, a) for c in (os.path.join(assets, 'hojas'), assets) if os.path.isdir(c) for a in os.listdir(c) if a.endswith('Attack Effects.zip')]
        if not zips: print('falta el zip (spriters-resource, Explorers of Sky > Miscellaneous > Attack Effects) en assets/hojas'); return
        z = zipfile.ZipFile(zips[0])
        nombres = z.namelist()
        os.makedirs(os.path.join(assets, 'efectos'), exist_ok=True)
        for efecto, numero in ELEGIDOS.items():
            rutas = sorted(n for n in nombres if n.startswith('move_VFX/' + numero + '/000/') and n.endswith('.png'))
            if not rutas: print('no esta', numero); continue
            rutas = [rutas[round(i * (len(rutas) - 1) / (MAX_FRAMES - 1))] for i in range(MAX_FRAMES)] if len(rutas) > MAX_FRAMES else rutas
            frames = [pygame.image.load(io.BytesIO(z.read(r)), 'f.png').convert_alpha() for r in rutas]
            lado = max(max(f.get_size()) for f in frames)
            tira = pygame.Surface((lado * len(frames), lado), pygame.SRCALPHA)
            for i, f in enumerate(frames): tira.blit(f, f.get_rect(center=(i * lado + lado // 2, lado // 2)))   # cada frame centrado en su cuadrado
            pygame.image.save(tira, os.path.join(assets, 'efectos', efecto + '.png'))
        print(len(ELEGIDOS), 'efectos en assets/efectos')

    main()


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
    """Dibuja el plan de una partida: T tienda, J semijefe, R regi, A arceus. Y el clima de las primeras salas."""
    rec = mundos.nuevo_recorrido()
    letras = {'combate': '.', 'tienda': 'T', 'jefe': 'J', 'regi': 'R', 'final': 'A'}
    for i, era in enumerate(rec['plan']):
        print(mundos.ERAS[i]['nombre'].ljust(22), ''.join(letras[t] for t in era))
    climas = []
    for _ in range(25): climas.append(rec['clima']); mundos.avanzar(rec)
    print('clima de las primeras salas:', ' > '.join(climas))


if __name__ == '__main__':
    orden = sys.argv[1] if len(sys.argv) > 1 else ''
    if orden == 'descargar': herramienta_descargar()
    elif orden == 'datos': herramienta_datos()
    elif orden == 'recortar' and len(sys.argv) > 2: herramienta_recortar(sys.argv[2])
    elif orden == 'hojas': herramienta_hojas()
    elif orden == 'tiles': herramienta_tiles()
    elif orden == 'efectos': herramienta_efectos()
    elif orden == 'salas': ver_salas()
    elif orden == 'plan': ver_plan()
    elif orden == 'visor': herramienta_visor()
    elif orden == 'sincronizar': herramienta_sincronizar()
    elif orden == 'verificar': herramienta_verificar()
    else: print(__doc__)
