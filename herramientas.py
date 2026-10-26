"""
herramientas.py - Programas aparte para preparar el juego (no se usan mientras jugas).

    python herramientas.py descargar           baja los sprites y retratos del PMD (SpriteCollab)
    python herramientas.py datos               arma datos_pokeapi.json desde la PokeAPI
    python herramientas.py recortar hoja.png   recorta sprites de una hoja y los deja en assets/mundo
    python herramientas.py hojas               baja todas las hojas (menos pokemon) de BW y los PMD a assets/hojas (via archive.org)
    python herramientas.py tiles               arma los tilesets con bordes (autotile) y el agua animada del PMD para cada era y variante de sala
    python herramientas.py decorados           rocas, hielo, pinos (piezas sueltas del PMD) y arbustos/arboles (Poke Transfer de BW) para los objetos
    python herramientas.py cielo               recorta el cielo y las nubes del Explorers of Sky para la intro
    python herramientas.py efectos             arma los efectos de golpes, proyectiles por tipo, cura, nivel... con los Attack Effects del PMD
    python herramientas.py objetos             recorta los iconos de la tienda de la hoja 'Items' de BW a assets/interfaz/objetos
    python herramientas.py paneles             recorta fondos, botones y paneles de los menus de BW a assets/interfaz/paneles
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
        """Baja todo lo que falta de todos los pokemon, de a varios a la vez."""
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
        """JSON de la PokeAPI (una URL completa o el nombre de un pokemon)."""
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
        """Arma datos_pokeapi.json con stats, movimientos, evoluciones y descripciones de todos los pokemon."""
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
        """Datos de un pokemon de la PokeAPI (None para los inventados, como Arceus Beta)."""
        slug = nombre.replace('_', '-')
        if nombre in ('arceus_beta', 'missigno'):
            return None
        peticion = urllib.request.Request(BASE + slug, headers={'User-Agent': 'Pokemanic-PokeAPI-Sync/1.0'})
        with urllib.request.urlopen(peticion, timeout=15) as respuesta:
            return json.loads(respuesta.read().decode('utf-8'))


    def main():
        """Actualiza stats, tipos y movimientos de datos_pokeapi.json (formato viejo)."""
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
        """JSON de la PokeAPI (guardado para no pedir dos veces lo mismo)."""
        if ruta not in cache:
            pedido = urllib.request.Request(API + ruta, headers={'User-Agent': 'pokemanic-verificacion'})
            with urllib.request.urlopen(pedido, timeout=30) as r:
                cache[ruta] = json.loads(r.read().decode('utf-8'))
        return cache[ruta]


    def verificar_tipos():
        """Compara la tabla de tipos del juego con la de la PokeAPI y muestra las diferencias."""
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
        """Revisa que cada pokemon pueda aprender en los juegos sus especiales y asistencias."""
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
             'toxico': ('Brine Cave', 'agua'), 'sombra': ('Dark Wasteland', 'suelo'), 'agua': ('4th Station Pass', 'agua')},
        'glaciacion': dict(base('Vast Ice Mountain'), agua=('Ice Aegis Cave', 'agua')),
        'glaciacion/cueva de hielo': base('Ice Aegis Cave'),
        'piedra': base('Tiny Meadow'),
        'piedra/aldea de cazadores': base('Forest Path'),
        'piedra/cueva rupestre': base('Limestone Cavern'),
        'piedra/valle volcanico': base('Barren Valley'),
        'piedra/rio': base('Lush Prairie'),
        'metales': base('Deep Boulder Quarry'),
        'metales/mina de cobre': base('Deep Limestone Cavern'),
        'metales/mercado': base('Shimmer Desert'),
        'metales/templo de bronce': base('Temporal Tower'),
        'metales/puerto antiguo': base('Side Path'),
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
                 'Shimmer Desert': (12, 8), 'Murky Forest': (16, 8)}
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

    def main():
        """Arma cada tileset del PLAN: piezas, variantes, paletas del agua y brillos."""
        pygame.init(); pygame.display.set_mode((1, 1))
        hojas, hechos, faltan = {}, 0, set()
        for destino, terrenos in PLAN.items():
            carpeta = os.path.join(assets, 'mundo', *destino.split('/'), 'terrenos')
            for terreno, (lugar, grupo) in terrenos.items():
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
    TRANSFER = {'arbusto': [(0, 1)], 'arbol': [(1, 2), (1, 3)], 'maceta': [(2, 1)]}
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
                'piedra_trueno': 77, 'piedra_alba': 291, 'garra_afilada': 321, 'baya_oran': 106,
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
    elif orden == 'decorados': herramienta_decorados()
    elif orden == 'cielo': herramienta_cielo()
    elif orden == 'efectos': herramienta_efectos()
    elif orden == 'objetos': herramienta_objetos()
    elif orden == 'paneles': herramienta_paneles()
    elif orden == 'salas': ver_salas()
    elif orden == 'plan': ver_plan()
    elif orden == 'visor': herramienta_visor()
    elif orden == 'sincronizar': herramienta_sincronizar()
    elif orden == 'verificar': herramienta_verificar()
    else: print(__doc__)
