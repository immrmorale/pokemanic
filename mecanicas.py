"""
mecanicas.py - Lo que hace unico a cada linea evolutiva de la expansion (y a Chikorita): una pasiva o un especial propio,
inspirado en lo que dice su Pokedex.

    LINEAS[especie] = (clave, etapa)        etapa 1, 2 o 3: las evoluciones lo hacen mas fuerte
    MECANICAS[clave] = {'nombre', 'desc', 'clase': 'pasiva' | 'especial', ...}
    especial_de(especie) -> (nombre, datos) para la casilla R (o None si su mecanica es pasiva)
    texto_de(especie) -> 'Nombre: que hace' (para la ficha, la pokedex y el glosario)
    armar(c) -> los ganchos que llama el combate (c trae las funciones del juego que hacen falta)

Balance: las pasivas son chicas y siempre estan; lo fuerte va en especiales con mucha espera (Prediccion, Control
Mental, Ilusion...). Las de 'contacto' castigan al que te pega cuerpo a cuerpo.
"""

import math
import random
import pygame


# ---------------------------------------------------------------- datos

def _linea(clave, *especies):
    return {e: (clave, i + 1) for i, e in enumerate(especies)}


LINEAS = {}
for _clave, _especies in (
        ('olfato', ('lillipup', 'herdier', 'stoutland')),
        ('recogida', ('zigzagoon', 'linoone')),
        ('adaptable', ('eevee',)),
        ('absorbe_agua', ('vaporeon',)), ('agujas', ('jolteon',)), ('absorbe_fuego', ('flareon',)), ('premonicion', ('espeon',)),
        ('sudor_venenoso', ('umbreon',)), ('fotosintesis', ('leafeon',)), ('cuerpo_helado', ('glaceon',)), ('cintas', ('sylveon',)),
        ('vozarron', ('whismur', 'loudred', 'exploud')),
        ('lana', ('wooloo', 'dubwool')),
        ('calor', ('charcadet',)), ('canon_armadura', ('armarouge',)), ('filo_amargo', ('ceruledge',)),
        ('intimidacion', ('litten', 'torracat', 'incineroar')),
        ('guardian', ('growlithe_hisui', 'arcanine_hisui')),
        ('espora', ('shroomish', 'breloom')),
        ('mirada', ('snivy', 'servine', 'serperior')),
        ('cuchilla_solar', ('fomantis', 'lurantis')),
        ('rastro_pasto', ('chikorita', 'bayleef', 'meganium')),
        ('bomba_floral', ('sprigatito', 'floragato', 'meowscarada')),
        ('humo_toxico', ('foongus', 'amoonguss', 'brute_bonnet')),
        ('sebo', ('swinub', 'piloswine', 'mamoswine')),
        ('supersonico', ('zubat', 'golbat', 'crobat')),
        ('glotoneria', ('grimer_alola', 'muk_alola')),
        ('punos_toxicos', ('croagunk', 'toxicroak')),
        ('tinta_toxica', ('skrelp', 'dragalge')),
        ('autoestima', ('sandile', 'krokorok', 'krookodile')),
        ('bajo_tierra', ('diglett_alola', 'dugtrio_alola')),
        ('rodada', ('phanpy', 'donphan', 'great_tusk')),
        ('prediccion', ('noibat', 'noivern')),
        ('tragamisil', ('cramorant',)), ('helice', ('arrokuda', 'barraskewda')),
        ('cuerno_sanador', ('ponyta_galar', 'rapidash_galar')),
        ('oleada_psiquica', ('espurr', 'meowstic')),
        ('sincronia', ('ralts', 'kirlia')), ('agujero_negro', ('gardevoir',)), ('tajo_psiquico', ('gallade',)),
        ('control_mental', ('elgyem', 'beheeyem')),
        ('huida', ('wimpod',)), ('plancha', ('golisopod',)),
        ('tecnico_veloz', ('scyther',)), ('tecnico', ('scizor',)), ('hacha_piedra', ('kleavor',)),
        ('impulso', ('nincada', 'ninjask')), ('superguarda', ('shedinja',)),
        ('cobardia', ('joltik', 'galvantula')),
        ('abrigo_hojas', ('sewaddle', 'swadloon', 'leavanny')),
        ('roca_afilada', ('rockruff', 'lycanroc')),
        ('armadura_fosil', ('anorith', 'armaldo')),
        ('mandibula', ('tyrunt', 'tyrantrum')),
        ('chorro_arena', ('larvitar', 'pupitar', 'tyranitar')), ('pua_hierro', ('iron_thorns',)),
        ('rencor', ('shuppet', 'banette')),
        ('absorbe_almas', ('litwick', 'lampent', 'chandelure')),
        ('raices', ('phantump', 'trevenant')),
        ('ultimos_respetos', ('greavard', 'houndstone')),
        ('guillotina', ('axew', 'fraxure', 'haxorus')),
        ('vuelo', ('bagon', 'shelgon', 'salamence', 'roaring_moon')),
        ('dracoflechas', ('dreepy', 'drakloak', 'dragapult')),
        ('piel_tosca', ('druddigon',)),
        ('ilusion', ('zorua', 'zoroark', 'zorua_hisui', 'zoroark_hisui')),
        ('cuerpo_cuchillas', ('pawniard', 'bisharp', 'kingambit')),
        ('bromista', ('impidimp', 'morgrem', 'grimmsnarl')),
        ('mandibula_trasera', ('mawile',)),
        ('tajo_teledirigido', ('honedge', 'doublade', 'aegislash')),
        ('engranajes', ('klink', 'klang', 'klinklang')),
        ('come_hierro', ('aron', 'lairon', 'aggron')),
        ('metronomo', ('cleffa', 'clefairy', 'clefable')),
        ('martillo', ('tinkatink', 'tinkatuff', 'tinkaton')),
        ('jardin', ('flabebe', 'floette', 'florges'))):
    LINEAS.update(_linea(_clave, *_especies))
LINEAS['great_tusk'] = ('rodada', 3); LINEAS['roaring_moon'] = ('vuelo', 3); LINEAS['brute_bonnet'] = ('humo_toxico', 3)


def _p(nombre, desc, **extra): return dict({'nombre': nombre, 'desc': desc, 'clase': 'pasiva'}, **extra)
def _e(nombre, desc, enfriamiento, tipo, **extra): return dict({'nombre': nombre, 'desc': desc, 'clase': 'especial', 'enfriamiento': enfriamiento, 'tipo': tipo}, **extra)


MECANICAS = {
    # ---------- normal
    'olfato': _p('Olfato', 'encuentra cosas: el doble de chance de objetos al romper cosas y los objetos del piso vienen desde más lejos (Stoutland: +15% monedas)'),
    'recogida': _p('Recogida', 'al limpiar una sala a veces encuentra algo tirado (25%, Linoone 35%): bayas, pociones o un caramelo'),
    'adaptable': _p('Adaptable', '+20% de daño con los ataques de su mismo tipo. Evoluciona con piedras (o con mucha amistad, en Sylveon)'),
    'absorbe_agua': _p('Absorbe Agua', 'los ataques de agua lo curan en vez de dañarlo, y en el agua se vuelve invisible para los enemigos'),
    'agujas': _p('Pelaje de agujas', 'el remate del combo dispara agujas eléctricas en abanico; los ataques eléctricos lo curan'),
    'absorbe_fuego': _p('Absorbe Fuego', 'el fuego no le hace daño: lo potencia (+30% de daño por 5 s)'),
    'premonicion': _p('Premonición', 'lee las corrientes de aire: los enemigos tardan 30% más en soltar el golpe'),
    'sudor_venenoso': _p('Sudor venenoso', 'el que le pega cuerpo a cuerpo queda envenenado'),
    'fotosintesis': _p('Fotosíntesis', 'con sol o parado en hierba se cura 1% de vida por segundo'),
    'cuerpo_helado': _p('Cuerpo helado', 'el que le pega cuerpo a cuerpo queda frenado por el frío'),
    'cintas': _p('Cintas calmantes', 'sus golpes cuerpo a cuerpo a veces (30%) calman al enemigo: se queda dormido un momento'),
    'vozarron': _e('Vozarrón', 'un grito en cono que empuja lejos y aturde (Exploud: más grande y más fuerte)', 9000, 'normal'),
    'lana': _p('Lana mullida', 'recibe 30% menos de los golpes cuerpo a cuerpo, pero el fuego le hace 50% más'),
    # ---------- fuego
    'calor': _p('Se calienta peleando', 'cada golpe que conecta suma +2% de daño (hasta +20%); se enfría si le pegan'),
    'canon_armadura': _e('Cañón Armadura', 'un disparo enorme que atraviesa todo; después queda 3 s con la guardia baja (recibe 30% más)', 10000, 'fuego'),
    'filo_amargo': _p('Filo Amargo', 'sus espadas de fuego le roban vida: sus golpes cuerpo a cuerpo lo curan'),
    'intimidacion': _p('Intimidación', 'los enemigos cerca le pegan 15% menos (Incineroar además tiene Lariat: un giro que pega alrededor)'),
    'guardian': _p('Guardián leal', 'por cada compañero debilitado pega 15% más y recibe 10% menos: no abandona a nadie'),
    # ---------- planta
    'espora': _p('Espora', 'sus golpes cuerpo a cuerpo a veces (12%, Breloom 18%) duermen al enemigo'),
    'mirada': _p('Fotosíntesis de cola', 'con sol o en hierba la energía vuelve 50% más rápido y corre 10% más (Serperior: Mirada, un especial que paraliza en cono)'),
    'cuchilla_solar': _e('Cuchilla Solar', 'junta luz un instante y suelta un corte largo en línea recta. Quieto en hierba se camufla', 8000, 'planta'),
    'rastro_pasto': _p('Rastro de pasto', 'deja pasto por donde camina; parado en su pasto se cura (más fuerte al evolucionar)'),
    'bomba_floral': _e('Bomba floral', 'tira flores que explotan al segundo (1, 2 o 3 según la evolución)', 7000, 'planta'),
    'humo_toxico': _e('Humo tóxico', 'larga una nube de esporas: los enemigos adentro se envenenan y se frenan', 10000, 'veneno'),
    # ---------- hielo
    'sebo': _p('Sebo', 'recibe 30% menos de fuego y de hielo. Piloswine evoluciona sabiendo Poder Pasado (MT)'),
    # ---------- veneno
    'supersonico': _e('Supersónico', 'un chillido en cono que aturde y confunde a los enemigos', 9000, 'volador'),
    'glotoneria': _p('Glotonería', 'cada enemigo que cae lo cura 4%, y sus golpes cuerpo a cuerpo a veces envenenan'),
    'punos_toxicos': _p('Puños tóxicos', 'los parrys y contraataques envenenan seguro; el agua lo cura y el fuego le pega 25% más (Piel Seca)'),
    'tinta_toxica': _e('Tinta tóxica', 'escupe veneno que deja un charco: los enemigos que lo pisan se envenenan', 8000, 'veneno'),
    # ---------- tierra
    'autoestima': _p('Autoestima', 'cada enemigo que derrota en la sala suma +6% de daño (hasta +30%)'),
    'bajo_tierra': _e('Bajo tierra', 'se mete bajo tierra 3 s: no lo tocan, pasa por debajo de agua, hielo y lava, y al salir golpea alrededor', 12000, 'tierra'),
    'rodada': _e('Rodada', 'se enrolla y rueda 2,5 s rebotando en las paredes; pega más cuanto más rueda', 9000, 'tierra'),
    # ---------- volador
    'prediccion': _e('Predicción', '5 s esquivando solo cualquier golpe; si algo lo va a tocar muy rápido el tiempo se frena medio segundo. Oído fino: ve venir a los enemigos de fuera de la pantalla', 40000, 'volador'),
    'tragamisil': _p('Tragamisil', 'al tocar agua atrapa un Arrokuda; cuando le pegan cuerpo a cuerpo se lo escupe al atacante (mucho daño y paraliza)'),
    'helice': _e('Hélice', 'sale disparado en línea recta muy rápido y atraviesa a los enemigos', 5000, 'agua'),
    # ---------- psiquico
    'cuerno_sanador': _e('Cuerno sanador', 'cura 20% a todo el equipo (también a la banca) y saca los estados', 30000, 'psiquico'),
    'oleada_psiquica': _e('Oleada psíquica', 'suelta el poder que guardan sus orejas: empuja muy lejos todo lo que está cerca', 10000, 'psiquico'),
    'sincronia': _p('Sincronía', 'cuando le ponen un estado, el enemigo más cercano se lo come también'),
    'agujero_negro': _e('Agujero negro', 'abre un agujero negro donde apunta: atrae a los enemigos y los lastima', 14000, 'psiquico'),
    'tajo_psiquico': _p('Filo psíquico', 'sus codos cortan: golpes cuerpo a cuerpo +20% y el parry dura 40% más'),
    'control_mental': _e('Control mental', 'controla al enemigo más cercano: pelea de tu lado 5 s (Beheeyem: dos enemigos, 7 s)', 25000, 'psiquico'),
    # ---------- bicho
    'huida': _p('Huida', 'la primera vez por sala que queda con menos de la mitad de vida, se vuelve intocable 1,5 s y corre 60% más'),
    'plancha': _p('Plancha', 'el primer golpe que da en cada sala pega x2,5'),
    'tecnico_veloz': _p('Tijeras veloces', 'el combo cuerpo a cuerpo recarga 25% más rápido'),
    'tecnico': _p('Técnico', 'sus golpes cuerpo a cuerpo pegan 30% más'),
    'hacha_piedra': _e('Hacha de piedra', 'clava piedras afiladas en el piso en línea: lastiman a los enemigos que pasan por 6 s', 10000, 'roca'),
    'impulso': _p('Impulso', 'peleando se acelera: cada 8 s +8% de velocidad y recargas 5% más rápidas (hasta 5 veces por sala)'),
    'superguarda': _p('Superguarda', 'solo le hacen daño los golpes súper eficaces y el terreno; tiene muy poca vida'),
    'cobardia': _p('Cobardía', 'con menos de 25% de vida se asusta y cambia solo al siguiente pokemon (1→2→3→1, el que pueda)'),
    'abrigo_hojas': _p('Abrigo de hojas', 'teje ropa de hojas: los compañeros de la banca se curan 1,5% cada 5 s'),
    # ---------- roca
    'roca_afilada': _e('Roca Afilada', 'una embestida rapidísima de recarga muy corta', 3500, 'roca'),
    'armadura_fosil': _p('Armadura fósil', 'el parry dura 40% más y recibe 15% menos de los disparos'),
    'mandibula': _p('Mandíbula fuerte', 'sus mordiscos (golpes cuerpo a cuerpo) pegan 40% más'),
    'chorro_arena': _p('Coraza de arena', 'recibe 15% menos. Tyranitar levanta una tormenta de arena que lastima a los enemigos (menos a roca, tierra y acero)'),
    'pua_hierro': _p('Púas de hierro', 'el que le pega cuerpo a cuerpo pierde 10% de su vida'),
    # ---------- fantasma
    'rencor': _e('Rencor', 'el daño que recibe se guarda; el especial lo devuelve x1,5 a los enemigos cercanos', 8000, 'fantasma'),
    'absorbe_almas': _p('Absorbe almas', 'cada enemigo que cae cerca le da vida (5%, 7% o 9% según la evolución)'),
    'raices': _e('Raíces', 'hace crecer raíces donde apunta: atrapan a los enemigos 2,5 s y los lastiman', 11000, 'planta'),
    'ultimos_respetos': _p('Últimos respetos', 'pega 20% más por cada compañero debilitado'),
    # ---------- dragon
    'guillotina': _p('Colmillos', 'golpes cuerpo a cuerpo +25% (Haxorus: Guillotina, un especial que remata a los que tienen menos de 30% de vida)'),
    'vuelo': _e('Vuelo', 'vuela 3 s: no lo tocan, pasa por arriba de todo y al aterrizar golpea alrededor (Bagon soñaba con esto)', 11000, 'volador'),
    'dracoflechas': _e('Dracoflechas', 'lanza Dreepys que persiguen a los enemigos (1, 2 o 3 según la evolución)', 6000, 'dragon'),
    'piel_tosca': _p('Piel tosca', 'el que le pega cuerpo a cuerpo pierde 8% de su vida'),
    # ---------- siniestro
    'ilusion': _e('Ilusión', 'toma la forma de un enemigo de la sala por 8 s: no lo atacan hasta que pega, y ese golpe hace el doble', 20000, 'siniestro'),
    'cuerpo_cuchillas': _p('Cuerpo de cuchillas', 'el que le pega cuerpo a cuerpo pierde 6% de su vida (Kingambit: +10% de daño por compañero debilitado)'),
    'bromista': _p('Bromista', 'cada golpe le roba 5 de energía al enemigo (Grimmsnarl: Pelo trenzado, un golpe enorme)'),
    # ---------- acero
    'mandibula_trasera': _p('Mandíbula trasera', 'sus mandíbulas de atrás también muerden: el golpe pega adelante y atrás, a veces paraliza y arrastra al enemigo'),
    'tajo_teledirigido': _e('Tajo teledirigido', 'una embestida de espada que persigue al enemigo más cercano (Aegislash: cambia entre espada y escudo)', 6000, 'acero'),
    'engranajes': _p('Engranajes', 'cada combo completo sube una marcha (hasta 3): +8% de velocidad y recargas por marcha; si le pegan baja una'),
    'come_hierro': _p('Come hierro', 'recibe 10% menos y al romper cosas se cura 4% (Aggron además tiene una embestida blindada)'),
    # ---------- hada
    'metronomo': _e('Metrónomo', 'mueve el dedo y sale un movimiento al azar de cualquier pokemon. Clefable no sufre daño del terreno ni del veneno', 6000, 'hada'),
    'martillo': _p('Martillo de chatarra', 'sus golpes cuerpo a cuerpo hacen el doble a los voladores y 30% más a los de acero (Tinkaton: un especial de martillazo gigante)'),
    'jardin': _e('Jardín floral', 'planta un círculo de flores por 6 s: adentro se cura 2% por segundo y recibe 20% menos', 18000, 'hada'),
}

# especiales extra de una especie en particular (ademas de su pasiva de linea)
ESPECIE_ESPECIAL = {
    'incineroar': _e('Lariat Oscuro', 'gira con los brazos abiertos y le pega a todo alrededor', 9000, 'siniestro', clave='lariat'),
    'serperior': _e('Mirada', 'una mirada en cono que paraliza a los enemigos 2,5 s', 12000, 'normal', clave='mirada_especial'),
    'haxorus': _e('Guillotina', 'un tajo que remata a los enemigos con menos de 30% de vida (a los jefes les pega fuerte)', 12000, 'dragon', clave='guillotina_especial'),
    'grimmsnarl': _e('Pelo trenzado', 'un golpe gigante con el pelo hecho músculo: mucho daño y empuja', 9000, 'hada', clave='pelo_trenzado'),
    'aggron': _e('Embestida blindada', 'una embestida que no se frena y no deja que le peguen mientras dura', 9000, 'acero', clave='blindada'),
    'tinkaton': _e('Martillazo gigante', 'un martillazo lento y enorme adelante', 10000, 'hada', clave='martillazo'),
    'tyrantrum': _e('Mordida colosal', 'muerde al de adelante, lo sacude y lo deja aturdido', 9000, 'roca', clave='mordida_colosal'),
    'galvantula': _e('Telaraña eléctrica', 'tira una red que frena y paraliza a los que quedan adentro', 9000, 'electrico', clave='telarana'),
    'leavanny': _e('Tormenta de hojas', 'hojas filosas giran alrededor 3 s', 10000, 'planta', clave='tormenta_hojas'),
    'chandelure': _e('Infierno de almas', 'llamas alrededor que pegan el doble a los que tienen un estado', 9000, 'fantasma', clave='infierno'),
    'pupitar': _e('Propulsión', 'se impulsa como un cohete en línea recta', 5000, 'roca', clave='propulsion'),
}
for _k, _v in ESPECIE_ESPECIAL.items(): MECANICAS[_v['clave']] = _v


def de(especie):
    """(clave, etapa) de la mecanica de linea de la especie, o (None, 0)."""
    return LINEAS.get(especie, (None, 0))


def especial_de(especie):
    """El especial propio de la especie para la casilla R: (nombre, datos) o None si su mecanica es solo pasiva."""
    clave, etapa = de(especie)
    m = ESPECIE_ESPECIAL.get(especie) or (MECANICAS.get(clave) if clave and MECANICAS[clave]['clase'] == 'especial' else None)
    if not m: return None
    propia = m.get('clave', clave)
    return 'mec_' + propia, {'forma': 'mecanica', 'mecanica': propia, 'etapa': max(1, etapa), 'enfriamiento': m['enfriamiento'], 'tipo': m['tipo'],
                             'nombre': m['nombre'], 'desc': m['desc'], 'daño': 0}


def texto_de(especie):
    """Lo que hace unico a esta especie, en una o dos lineas (o None)."""
    clave, _ = de(especie)
    partes = []
    if clave: partes.append(MECANICAS[clave]['nombre'] + ': ' + MECANICAS[clave]['desc'])
    if especie in ESPECIE_ESPECIAL: partes.append(ESPECIE_ESPECIAL[especie]['nombre'] + ' (R): ' + ESPECIE_ESPECIAL[especie]['desc'])
    return '  |  '.join(partes) or None


# mecanicas de los enemigos (lo que hacen cuando te los cruzas)
ENEMIGO = {
    'diglett_alola': 'excava', 'dugtrio_alola': 'excava', 'mawile': 'muerde', 'zubat': 'chilla', 'golbat': 'chilla', 'crobat': 'chilla',
    'foongus': 'esporas', 'amoonguss': 'esporas', 'brute_bonnet': 'esporas', 'zorua': 'disfraz', 'zoroark': 'disfraz', 'zorua_hisui': 'disfraz',
    'zoroark_hisui': 'disfraz', 'elgyem': 'mente', 'beheeyem': 'mente', 'joltik': 'huye', 'galvantula': 'huye',
}
ENEMIGO_TXT = {
    'excava': 'Diglett de Alola: se mete bajo tierra, aparece debajo tuyo (mirá el círculo) y te entierra un momento',
    'muerde': 'Mawile: su mordida a veces te paraliza y te arrastra hacia él',
    'chilla': 'Zubat, Golbat y Crobat: chillan cuando estás cerca (anillo amarillo) y te aturden',
    'esporas': 'Foongus: si te acercás larga una nube de esporas que envenena',
    'disfraz': 'Zorua y Zoroark: aparecen disfrazados de otro pokemon; al pegarles se revelan',
    'mente': 'Elgyem y Beheeyem: te controlan la mente (anillo violeta) y caminás al revés un rato',
    'huye': 'Joltik y Galvantula: con poca vida se asustan y escapan',
}


# ---------------------------------------------------------------- logica

def armar(c):
    """Los ganchos del combate. c: namespace con las funciones y datos del juego (ver main.py, armar_mecanicas)."""
    from types import SimpleNamespace
    T = c.tiempo
    CONTACTO = ('cuerpo', 'embestida')                    # formas de golpe que cuentan como 'cuerpo a cuerpo'

    # ---------- ayudas
    def mec(j):
        """(clave, etapa) de la especie que pelea."""
        return de(j['nombre'])

    def es(j, clave):
        return LINEAS.get(j['nombre'], (None,))[0] == clave

    def etapa(j):
        return max(1, LINEAS.get(j['nombre'], (None, 1))[1])

    def estado(j):
        """Lo que guarda la mecanica del que pelea (se reinicia con la sala)."""
        return j.setdefault('mec', {})

    def daño(j, base, tipo, forma='proyectil'):
        """Daño de un golpe de mecanica escalado igual que cualquier ataque (rol, nivel, buffs, estilo)."""
        return c.preparar(j, {'daño': base, 'tipo': tipo, 'forma': forma})['daño']

    def area(j, nivel, centro, radio, base, tipo, retroceso=30, efecto=None, con_objetos=True):
        datos = {'tipo': tipo, 'daño': daño(j, base, tipo), 'area': radio, 'retroceso': retroceso, 'efecto': efecto, 'jugador': True}
        c.area_efecto(j, datos, c.objetivos_de(nivel, con_objetos), nivel['efectos'], centro)

    def cosa(nivel, **datos):
        """Algo que queda en la sala (bomba, nube, charco, agujero, raices, piedras, jardin, flecha...)."""
        datos.setdefault('inicio', T())
        nivel.setdefault('mec_cosas', []).append(datos)
        return datos

    def enemigos_vivos(nivel):
        return [e for e in nivel['enemigos'] if e['vida'] > 0]

    def debilitados(j):
        return sum(1 for m in j['equipo'] if m['vida'] <= 0)

    def cono(j, nivel, alcance, grados):
        """Enemigos (y jefe) dentro de un cono adelante del jugador."""
        ax, ay = j['aim']; px, py = j['rect'].center
        salida = []
        for o in c.objetivos_de(nivel, False):
            if o['vida'] <= 0: continue
            vx, vy = o['rect'].centerx - px, o['rect'].centery - py
            d = math.hypot(vx, vy)
            if d > alcance + max(o['rect'].size) / 2: continue
            if d < 1 or math.degrees(math.acos(max(-1.0, min(1.0, (vx * ax + vy * ay) / d)))) <= grados: salida.append(o)
        return salida

    def efecto_onda(nivel, x, y, radio, tipo, ms=500):
        nivel['efectos'].append({'x': x, 'y': y, 'radio': radio, 'tipo': tipo, 'inicio': T(), 'hasta': T() + ms})

    def poner_a(o, que, ms):
        """Le pone un estado a un enemigo (quemar, paralizar, dormir, ralentizar, confundir, veneno)."""
        if o.get('jefe') and que in ('dormir', 'paralizar', 'confundir'): ms = ms // 3     # a los jefes casi no les dura
        o['estado'] = que; o['estado_hasta'] = T() + ms; o['proximo_estado'] = T() + 700

    def golpear_a(j, o, base, tipo, retroceso=0, efecto=None):
        c.recibir_ataque(o, {'tipo': tipo, 'daño': daño(j, base, tipo, 'cuerpo'), 'retroceso': retroceso, 'efecto': efecto, 'jugador': True}, j['direccion'])

    def objetivo_cercano(j, nivel, alcance=600, sin=()):
        cand = [o for o in c.objetivos_de(nivel, False) if o['vida'] > 0 and o not in sin
                and math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery) <= alcance]
        return min(cand, key=lambda o: math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery), default=None)

    # ---------- al entrar a una sala
    def nueva_sala(j, nivel):
        """Lo que se reinicia con cada sala (contadores de Autoestima, Impulso, Plancha, Huida...)."""
        for m in j['equipo']: m.pop('mec', None)
        j['mec'] = {}
        nivel['mec_cosas'] = []

    def al_cambiar(j):
        """Cambiaste de pokemon: lo que era del que salio se va (ilusion, bajo tierra, vuelo, prediccion...)."""
        e = estado(j)
        for k in ('ilusion_hasta', 'bajo_hasta', 'vuelo_hasta', 'prediccion_hasta', 'rodada_hasta', 'teledirigido', 'espada_hasta', 'escudo_hasta', 'marchas', 'calor'):
            e.pop(k, None)
        j.pop('ilusion_hasta', None)
        if j.get('disfraz'): j.pop('disfraz'); c.rehacer_animador(j)

    # ---------- golpes tuyos
    def mult_golpe(j, o, datos):
        """Multiplicador del daño de un golpe del jugador segun su mecanica (antes de aplicarlo)."""
        clave = mec(j)[0]; e = estado(j); forma = datos.get('forma'); m = 1.0
        contacto = forma in CONTACTO
        tipo = c.normalizar_tipo(datos.get('tipo')) if datos.get('tipo') else None
        if clave == 'adaptable' and tipo in j['tipos']: m *= 1.2
        elif clave == 'calor': m *= 1 + e.get('calor', 0.0)
        elif clave == 'autoestima': m *= 1 + min(0.30, 0.06 * e.get('bajas', 0))
        elif clave == 'guardian': m *= 1 + 0.15 * debilitados(j)
        elif clave == 'ultimos_respetos': m *= 1 + 0.20 * debilitados(j)
        elif clave == 'cuerpo_cuchillas' and j['nombre'] == 'kingambit': m *= 1 + 0.10 * debilitados(j)
        elif clave == 'tecnico' and contacto: m *= 1.3
        elif clave == 'mandibula' and contacto: m *= 1.4
        elif clave == 'tajo_psiquico' and contacto: m *= 1.2
        elif clave == 'guillotina' and contacto: m *= 1.25
        elif clave == 'martillo' and contacto:
            if 'volador' in c.tipos_de(o): m *= 2.0
            elif 'acero' in c.tipos_de(o): m *= 1.3
        elif clave == 'plancha' and not e.get('plancha_usada') and not o.get('objeto'): m *= 2.5; e['plancha_usada'] = True
        elif clave == 'vuelo' and j['nombre'] in ('bagon',) and forma == 'embestida': m *= 1.3
        if clave in ('rodada', 'vuelo') and j['nombre'] in ('great_tusk', 'roaring_moon') and c.clima() in ('sol', 'despejado'): m *= 1.2   # Protosintesis
        if e.get('espada_hasta', 0) > T(): m *= 1.3                    # Aegislash en modo espada
        if j.get('ilusion_hasta', 0) > T() and not o.get('objeto'): m *= 2.0     # el golpe desde la ilusion
        if e.get('fuego_hasta', 0) > T(): m *= 1.3                     # Flareon potenciado por fuego
        return m

    def tras_golpe(j, o, datos, hecho):
        """Despues de un golpe del jugador que conecto (o es el objetivo; hecho es el daño)."""
        clave = mec(j)[0]; e = estado(j); contacto = datos.get('forma') in CONTACTO
        if o.get('objeto'): return
        if datos.get('drena') and hecho:                                # Beso Drenaje, Filo Amargo
            j['vida'] = min(j['max_vida'], j['vida'] + hecho * datos['drena'])
        if clave == 'filo_amargo' and contacto and hecho: j['vida'] = min(j['max_vida'], j['vida'] + hecho * 0.25)
        if clave == 'calor' and hecho: e['calor'] = min(0.20, e.get('calor', 0.0) + 0.02)
        if clave == 'espora' and contacto and random.random() < (0.12 if etapa(j) == 1 else 0.18): poner_a(o, 'dormir', 2000)
        if clave == 'cintas' and contacto and random.random() < 0.30: poner_a(o, 'dormir', 1500)
        if clave == 'glotoneria' and contacto and random.random() < 0.25: poner_a(o, 'veneno', 4000)
        if clave == 'bromista': j['energia'] = min(c.ENERGIA_MAX, j['energia'] + 5)
        if clave == 'mandibula_trasera' and contacto and random.random() < 0.30:
            poner_a(o, 'paralizar', 1200)
            dx, dy = j['rect'].centerx - o['rect'].centerx, j['rect'].centery - o['rect'].centery
            d = math.hypot(dx, dy) or 1
            c.mover_entidad(o, round(dx / d * min(40, d - 30)), round(dy / d * min(40, d - 30)))
        if j.get('ilusion_hasta', 0) > T(): termina_ilusion(j)

    def remate(j, nivel, tocados):
        """El tercer golpe del combo conecto."""
        clave = mec(j)[0]; e = estado(j)
        if clave == 'agujas':                                          # Jolteon: agujas en abanico
            c.lanzar(j, {'tipo': 'electrico', 'daño': daño(j, 10, 'electrico'), 'distancia': 300, 'area': 7, 'velocidad': 13, 'cantidad': 5,
                         'abanico': 50, 'retroceso': 4, 'efecto': {'tipo': 'paralizar', 'duracion': 800, 'probabilidad': 15}, 'jugador': True}, nivel['proyectiles_pokemon'])
        if clave == 'engranajes' and tocados:
            e['marchas'] = min(3, e.get('marchas', 0) + 1)
            c.poner_buff(j, 'velocidad', 1 + 0.08 * e['marchas'], 600000); c.poner_buff(j, 'enfriamiento', 1 - 0.08 * e['marchas'], 600000)

    def mult_enfriamiento_combo(j):
        return 0.75 if es(j, 'tecnico_veloz') else 1.0

    def mult_parry(j):
        return 1.4 if mec(j)[0] in ('armadura_fosil', 'tajo_psiquico') else 1.0

    def al_parry(j, nivel, atacante=None):
        """Hiciste parry: Croagunk envenena, Aegislash pasa a escudo."""
        clave = mec(j)[0]; e = estado(j)
        if clave == 'punos_toxicos' and atacante: poner_a(atacante, 'veneno', 5000)
        if j['nombre'] == 'aegislash': e['escudo_hasta'] = T() + 5000; e.pop('espada_hasta', None); c.cartel(nivel, 'Modo escudo', 700)

    # ---------- golpes que recibis
    def recibido(j, cuanto, tipo, atacante=None, evitable=True):
        """Modifica el daño que le llega al jugador (antes de los buffs y la defensa). Devuelve el daño nuevo."""
        clave = mec(j)[0]; e = estado(j); ahora = T()
        t = c.normalizar_tipo(tipo) if tipo else None
        nivel = c.mundo.get('nivel')
        if e.get('bajo_hasta', 0) > ahora or e.get('vuelo_hasta', 0) > ahora: return 0      # bajo tierra / volando: no lo tocan
        if evitable and e.get('prediccion_hasta', 0) > ahora and cuanto > 0:               # Prediccion: lo esquiva solo
            c.esquive_perfecto(j); return 0
        if clave == 'superguarda' and evitable and c.multiplicador_tipos(t or 'normal', j['tipos']) < 2:
            if nivel and ahora - e.get('aviso_guarda', 0) > 1500: c.cartel(nivel, 'Superguarda: no le hace nada', 700); e['aviso_guarda'] = ahora
            return 0
        if clave == 'metronomo' and j['nombre'] == 'clefable' and not evitable: return 0   # Muro Magico
        if t == 'agua' and clave in ('absorbe_agua', 'punos_toxicos'): j['vida'] = min(j['max_vida'], j['vida'] + cuanto * 0.25); return 0
        if t == 'electrico' and clave == 'agujas': j['vida'] = min(j['max_vida'], j['vida'] + cuanto * 0.25); return 0
        if t == 'fuego' and clave == 'absorbe_fuego':
            e['fuego_hasta'] = ahora + 5000
            if nivel and ahora - e.get('aviso_fuego', 0) > 2000: c.cartel(nivel, '¡Absorbe Fuego! +30% de daño', 900); e['aviso_fuego'] = ahora
            return 0
        m = 1.0
        if clave == 'sebo' and t in ('fuego', 'hielo'): m *= 0.7
        if clave == 'lana':
            if atacante: m *= 0.7
            if t == 'fuego': m *= 1.5
        if clave == 'punos_toxicos' and t == 'fuego': m *= 1.25
        if clave == 'intimidacion' and atacante and math.hypot(atacante['rect'].centerx - j['rect'].centerx, atacante['rect'].centery - j['rect'].centery) < 220: m *= 0.85
        if clave == 'armadura_fosil' and not atacante and evitable: m *= 0.85
        if clave == 'chorro_arena' or clave == 'come_hierro': m *= 0.85 if clave == 'chorro_arena' else 0.9
        if clave == 'vuelo' and j['nombre'] == 'shelgon': m *= 0.7
        if clave == 'guardian': m *= max(0.7, 1 - 0.10 * debilitados(j))
        if e.get('escudo_hasta', 0) > ahora: m *= 0.7
        if e.get('espada_hasta', 0) > ahora: m *= 1.15
        if e.get('guardia_baja_hasta', 0) > ahora: m *= 1.3
        if nivel and dentro_jardin(nivel, j): m *= 0.8
        if clave == 'calor' and cuanto * m >= 1: e['calor'] = 0.0                       # se enfria
        if clave == 'engranajes' and cuanto * m >= 1 and e.get('marchas'):
            e['marchas'] -= 1
            c.poner_buff(j, 'velocidad', 1 + 0.08 * e['marchas'], 600000); c.poner_buff(j, 'enfriamiento', 1 - 0.08 * e['marchas'], 600000)
        if clave == 'rencor' and cuanto * m >= 1: e['rencor'] = min(j['max_vida'] * 0.6, e.get('rencor', 0) + cuanto * m)
        if atacante and cuanto * m >= 1 and evitable: contacto(j, atacante, nivel)
        return cuanto * m

    def contacto(j, atacante, nivel):
        """Te pegaron cuerpo a cuerpo: lo que le pasa al atacante (veneno, frio, pinchos, el Arrokuda de Cramorant...)."""
        clave = mec(j)[0]; e = estado(j)
        if clave == 'sudor_venenoso': poner_a(atacante, 'veneno', 5000)
        elif clave == 'cuerpo_helado': poner_a(atacante, 'ralentizar', 2500)
        elif clave in ('piel_tosca', 'cuerpo_cuchillas', 'pua_hierro'):
            atacante['vida'] = max(0, atacante['vida'] - atacante['max_vida'] * {'piel_tosca': 0.08, 'cuerpo_cuchillas': 0.06, 'pua_hierro': 0.10}[clave])
            atacante['golpe_flash'] = T()
        elif clave == 'ultimos_respetos' and j['nombre'] == 'houndstone' and random.random() < 0.2: poner_a(atacante, 'ralentizar', 2000)
        elif clave == 'tragamisil' and e.get('arrokuda'):
            e['arrokuda'] = False
            golpear_a(j, atacante, 45, 'agua', 40, {'tipo': 'paralizar', 'duracion': 1800, 'probabilidad': 100})
            if nivel: c.cartel(nivel, '¡Tragamisil! Le escupió el Arrokuda', 1000)

    def estado_puesto(j, que):
        """Te pusieron un estado: Sincronia se lo pasa al enemigo mas cercano."""
        if not es(j, 'sincronia'): return
        nivel = c.mundo.get('nivel')
        o = objetivo_cercano(j, nivel, 400) if nivel else None
        conv = {'veneno': 'veneno', 'quemadura': 'quemar', 'paralisis': 'paralizar', 'sueño': 'dormir', 'confusion': 'confundir', 'aturdido': 'paralizar'}
        if o and que in conv: poner_a(o, conv[que], 3000); c.cartel(nivel, 'Sincronía: ' + o['nombre'].title() + ' también', 800)

    # ---------- al derrotar / limpiar
    def derrota(j, o, nivel):
        clave = mec(j)[0]; e = estado(j)
        if clave == 'autoestima': e['bajas'] = e.get('bajas', 0) + 1
        if clave == 'glotoneria': j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.04)
        if clave == 'absorbe_almas' and math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery) < 260:
            j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * (0.03 + 0.02 * etapa(j)))
            c.efectos.cura(c.mundo['ef'], *j['rect'].center)

    def sala_limpia(j, nivel):
        if es(j, 'recogida') and random.random() < (0.25 if etapa(j) == 1 else 0.35):
            clave = random.choice(('baya_aranja', 'zumo_baya', 'pocion', 'baya_ziuela', 'superpocion', 'baya_zidra', 'caramelo_raro'))
            c.soltar_objeto(nivel, *j['rect'].center, clave)
            c.cartel(nivel, '¡Recogida! Encontró algo tirado', 1200)

    def mult_romper(j):
        return 2.0 if es(j, 'olfato') else 1.0

    def mult_iman(j):
        return 2.0 if es(j, 'olfato') else 1.0

    def mult_monedas(j):
        return 1.15 if j['nombre'] == 'stoutland' else 1.0

    def objeto_roto(j):
        if es(j, 'come_hierro'):
            j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.04); c.efectos.cura(c.mundo['ef'], *j['rect'].center)

    def aviso_mult(j):
        return 1.3 if es(j, 'premonicion') else 1.0

    def regen_energia(j):
        return 1.5 if es(j, 'mirada') and (c.clima() in ('sol', 'despejado') or c.terreno_bajo(j) == 'hierba') else 1.0

    def mult_velocidad(j):
        e = estado(j); m = 1.0
        if es(j, 'mirada') and (c.clima() in ('sol', 'despejado') or c.terreno_bajo(j) == 'hierba'): m *= 1.1
        if es(j, 'impulso'): m *= 1 + 0.08 * e.get('impulsos', 0) * (0.5 if j['nombre'] == 'nincada' else 1)
        if e.get('huida_hasta', 0) > T(): m *= 1.6
        if e.get('vuelo_hasta', 0) > T(): m *= 1.4
        if e.get('bajo_hasta', 0) > T(): m *= 1.3
        if j['nombre'] == 'shelgon': m *= 0.85
        return m

    def mult_recarga(j):
        e = estado(j); m = 1.0
        if es(j, 'impulso'): m *= 1 - 0.05 * e.get('impulsos', 0)
        return m

    def mult_recarga_especial(j, datos):
        """Bromista: los especiales que no pegan (buffs, curas, estados) recargan 30% mas rapido."""
        if es(j, 'bromista') and (datos.get('forma') in ('buff', 'curar') or not datos.get('daño')): return 0.7
        return 1.0

    def ignora_solidos(j):
        e = estado(j); ahora = T()
        return e.get('bajo_hasta', 0) > ahora or e.get('vuelo_hasta', 0) > ahora

    def invisible(j):
        """No se dibuja el sprite (bajo tierra)."""
        return estado(j).get('bajo_hasta', 0) > T()

    def altura_vuelo(j):
        e = estado(j); ahora = T()
        if e.get('vuelo_hasta', 0) <= ahora: return 0
        falta = e['vuelo_hasta'] - ahora; total = 3000
        return round(28 * math.sin(math.pi * min(1.0, (total - falta) / total)) + 6)

    # ---------- por cuadro
    def cuadro(j, nivel):
        """Todo lo que la mecanica hace solo, cada cuadro (y las cosas que quedaron en la sala)."""
        ahora = T(); clave, et = mec(j); e = estado(j); peligro = c.hay_peligro(nivel)
        # pasivas de terreno / clima
        bajo = c.terreno_bajo(j)
        if clave == 'rastro_pasto': rastro_pasto(j, nivel, et)
        if clave == 'fotosintesis' and (c.clima() in ('sol', 'despejado') or bajo == 'hierba') and nivel['frame'] % 60 == 0:
            j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.01)
        if clave == 'absorbe_agua' and bajo in ('agua', 'charco'): j['oculto'] = True
        if clave == 'cuchilla_solar' and bajo in ('hierba', 'sombra') and not j['moviendose']:
            if ahora - e.get('quieto_desde', ahora) > 1200: j['oculto'] = True
        if j['moviendose']: e['quieto_desde'] = ahora
        if clave == 'tragamisil' and bajo in ('agua', 'charco') and not e.get('arrokuda'):
            e['arrokuda'] = True; c.cartel(nivel, 'Cramorant atrapó un Arrokuda', 900)
        if clave == 'impulso' and peligro and ahora >= e.get('prox_impulso', ahora + 8000):
            if 'prox_impulso' in e and e.get('impulsos', 0) < 5: e['impulsos'] = e.get('impulsos', 0) + 1; c.cartel(nivel, 'Impulso: más rápido', 600)
            e['prox_impulso'] = ahora + 8000
        if clave == 'abrigo_hojas' and nivel['frame'] % 300 == 0:
            for i, m in enumerate(j['equipo']):
                if i != j['activo'] and m['vida'] > 0: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] * 0.015)
        if clave == 'chorro_arena' and j['nombre'] == 'tyranitar' and peligro and nivel['frame'] % 60 == 0:
            for o in enemigos_vivos(nivel):
                if not set(c.tipos_de(o)) & {'roca', 'tierra', 'acero'}: o['vida'] = max(1, o['vida'] - max(1, o['max_vida'] * 0.015))
            for _ in range(6): c.efectos.polvo(c.mundo['ef'], j['rect'].centerx + random.randint(-400, 400), j['rect'].centery + random.randint(-260, 260))
        # vida baja: Huida y Cobardia
        if clave == 'huida' and j['vida'] < j['max_vida'] * 0.5 and not e.get('huida_usada') and peligro:
            e['huida_usada'] = True; e['huida_hasta'] = ahora + 3000; j['inv_hasta'] = max(j.get('inv_hasta', 0), ahora + 1500)
            c.cartel(nivel, '¡Huida! Wimpod sale corriendo', 900)
        if clave == 'cobardia' and 0 < j['vida'] < j['max_vida'] * 0.25 and ahora >= e.get('cobardia_lista', 0) and len(j['equipo']) > 1:
            n = len(j['equipo'])
            for k in range(1, n):
                destino = (j['activo'] + k) % n
                if j['equipo'][destino]['vida'] > 0:
                    nombre = j['nombre'].title()
                    if c.cambiar_slot(j, destino, True):
                        estado(j)['cobardia_lista'] = ahora + 10000
                        c.cartel(nivel, '¡' + nombre + ' se asustó y se escondió!', 1200)
                    break
        # timers de especiales
        if e.get('bajo_hasta') and ahora >= e['bajo_hasta']:
            e.pop('bajo_hasta'); area(j, nivel, j['rect'].center, 110 + 20 * et, 30 + 10 * et, 'tierra', 40, {'tipo': 'paralizar', 'duracion': 700, 'probabilidad': 100})
            c.efectos.explosion(c.mundo['ef'], *j['rect'].center, 90); c.temblor(nivel, 200)
        if e.get('vuelo_hasta') and ahora >= e['vuelo_hasta']:
            e.pop('vuelo_hasta'); area(j, nivel, j['rect'].center, 130, 40 + 10 * et, 'dragon', 45)
            c.efectos.explosion(c.mundo['ef'], *j['rect'].center, 110); c.temblor(nivel, 220)
        if e.get('rodada_hasta'):
            if ahora >= e['rodada_hasta']: e.pop('rodada_hasta'); j['embestida'] = None
            elif not j['embestida']:
                e['rodada_vueltas'] = e.get('rodada_vueltas', 0) + 1
                ax, ay = j['aim']
                if e.get('rodada_rebote'): ax, ay = -ax, -ay; j['aim'] = (ax, ay)
                c.iniciar_embestida(j, {'tipo': 'tierra', 'daño': daño(j, 16 + 6 * e['rodada_vueltas'], 'tierra', 'embestida'), 'distancia': 260,
                                        'velocidad': 10 + 2 * et, 'area': 26, 'retroceso': 30, 'forma': 'embestida', 'jugador': True})
                e['rodada_rebote'] = True
        if e.get('teledirigido') and j['embestida']:                    # Honedge: la embestida persigue
            o = e['teledirigido']
            if o['vida'] > 0:
                dx, dy = o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery
                d = math.hypot(dx, dy) or 1
                j['embestida']['vx'], j['embestida']['vy'] = dx / d, dy / d
                j['aim'] = (dx / d, dy / d)
        elif e.get('teledirigido') and not j['embestida']: e.pop('teledirigido')
        if j.get('ilusion_hasta') and ahora >= j['ilusion_hasta']: termina_ilusion(j)
        if e.get('lento_hasta') and ahora >= e['lento_hasta']: e.pop('lento_hasta')
        if e.get('prediccion_hasta', 0) > ahora and not e.get('lento_hasta'):     # algo muy rapido viene: camara lenta
            for o in enemigos_vivos(nivel):
                av = o.get('aviso')
                if av and av.get('hasta', 0) - ahora < 260 and math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery) < 220:
                    e['lento_hasta'] = ahora + 450; e['lento_usado'] = e.get('lento_usado', 0) + 1; break
        actualizar_cosas(j, nivel)

    def lento():
        """Si el tiempo esta frenado (Prediccion de Noibat): los enemigos y sus balas se mueven a un tercio."""
        j = c.mundo.get('jugador')
        return bool(j) and estado(j).get('lento_hasta', 0) > T()

    # ---------- rastro de pasto (Chikorita)
    def rastro_pasto(j, nivel, et):
        ent = nivel['ent']; ahora = T(); e = estado(j)
        rastro = nivel.setdefault('rastro_pasto', {})
        for celda, (viejo, hasta) in list(rastro.items()):
            if ahora >= hasta:
                if ent['m'][celda[0]][celda[1]] == 'hierba': c.entorno.cambiar(ent, celda[0], celda[1], viejo)
                rastro.pop(celda)
        f, k = c.entorno.casilla(ent, *j['rect'].center)
        if not (0 <= f < len(ent['m']) and 0 <= k < len(ent['m'][0])): return
        viejo = ent['m'][f][k]
        if (f, k) not in rastro and viejo in ('suelo', 'nieve', 'arena', 'tierra', 'ceniza', 'escarcha') and len(rastro) < 24 and ahora >= e.get('prox_pasto', 0):
            if c.entorno.cambiar(ent, f, k, 'hierba'): rastro[(f, k)] = (viejo, ahora + 9000)
            e['prox_pasto'] = ahora + 350
        if (f, k) in rastro and nivel['frame'] % 30 == 0:
            j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * (0.005 + 0.0025 * (et - 1)))
            if nivel['frame'] % 90 == 0: c.efectos.cura(c.mundo['ef'], *j['rect'].center)

    # ---------- especiales
    def usar(j, datos, nivel):
        """Usa el especial de mecanica (casilla R)."""
        clave = datos['mecanica']; et = datos.get('etapa', 1); ahora = T(); e = estado(j)
        px, py = j['rect'].center; ax, ay = j['aim']
        if clave == 'vozarron':
            for o in cono(j, nivel, 170 + 50 * et, 40 + 5 * et):
                golpear_a(j, o, 14 + 8 * et, 'normal', 60 + 20 * et, {'tipo': 'paralizar', 'duracion': 700 + 200 * et, 'probabilidad': 100})
            efecto_onda(nivel, px + ax * 90, py + ay * 90, 120 + 30 * et, 'normal')
        elif clave == 'canon_armadura':
            c.lanzar(j, {'tipo': 'fuego', 'daño': daño(j, 70, 'fuego'), 'distancia': 620, 'area': 30, 'velocidad': 12, 'retroceso': 50, 'atraviesa': True,
                         'efecto': {'tipo': 'quemar', 'duracion': 2500, 'probabilidad': 50}, 'jugador': True}, nivel['proyectiles_pokemon'])
            e['guardia_baja_hasta'] = ahora + 3000; c.temblor(nivel, 150)
        elif clave == 'cuchilla_solar':
            largo = 340 + 60 * et
            for o in c.objetivos_de(nivel, True):
                if o['vida'] <= 0: continue
                vx, vy = o['rect'].centerx - px, o['rect'].centery - py
                adelante, lado = vx * ax + vy * ay, abs(vx * ay - vy * ax)
                if 0 <= adelante <= largo and lado <= 34 + max(o['rect'].size) / 2:
                    c.recibir_ataque(o, {'tipo': 'planta', 'daño': daño(j, 34 + 14 * et, 'planta', 'cuerpo'), 'retroceso': 20, 'jugador': True}, j['direccion'])
            nivel['efectos'].append({'x': px, 'y': py, 'linea': (px + ax * largo, py + ay * largo), 'radio': 16, 'tipo': 'planta', 'inicio': ahora, 'hasta': ahora + 300})
        elif clave == 'bomba_floral':
            for k in range(et):
                dest = c.punto_apuntado(j, 320)
                ang = math.radians((k - (et - 1) / 2) * 30)
                bx = px + (dest[0] - px) * math.cos(ang) - (dest[1] - py) * math.sin(ang)
                by = py + (dest[0] - px) * math.sin(ang) + (dest[1] - py) * math.cos(ang)
                cosa(nivel, clase='bomba', x=bx, y=by, hasta=ahora + 900 + 120 * k, daño=daño(j, 28 + 6 * et, 'planta'), radio=90, j=j)
        elif clave == 'humo_toxico':
            cosa(nivel, clase='nube', x=px, y=py, radio=110 + 15 * et, hasta=ahora + 4000, tick=0, daño=daño(j, 6, 'veneno'), de_jugador=True)
        elif clave == 'supersonico':
            for o in cono(j, nivel, 230, 45):
                poner_a(o, 'confundir', 2500 + 400 * et); o['aviso'] = None
            efecto_onda(nivel, px + ax * 110, py + ay * 110, 150, 'volador')
        elif clave == 'tinta_toxica':
            dest = c.punto_apuntado(j, 300)
            cosa(nivel, clase='charco', x=dest[0], y=dest[1], radio=80 + 15 * et, hasta=ahora + 5000, tick=0, daño=daño(j, 5, 'veneno'))
            area(j, nivel, dest, 70, 18 + 6 * et, 'veneno', 10, {'tipo': 'veneno', 'duracion': 4000, 'probabilidad': 100})
        elif clave == 'bajo_tierra':
            e['bajo_hasta'] = ahora + 3000; c.efectos.polvo(c.mundo['ef'], px, py)
        elif clave == 'rodada':
            e['rodada_hasta'] = ahora + 2500; e['rodada_vueltas'] = 0; e['rodada_rebote'] = False
        elif clave == 'prediccion':
            e['prediccion_hasta'] = ahora + 5000; c.cartel(nivel, 'Predicción: lo ve todo venir', 1000)
        elif clave == 'helice':
            c.iniciar_embestida(j, {'tipo': 'agua', 'daño': daño(j, 26 + 8 * et, 'agua', 'embestida'), 'distancia': 360 + 60 * et, 'velocidad': 20 + 3 * et,
                                    'area': 22, 'retroceso': 25, 'forma': 'embestida', 'jugador': True})
            j['inv_hasta'] = max(j.get('inv_hasta', 0), ahora + 250)
        elif clave == 'cuerno_sanador':
            for m in j['equipo']:
                if m['vida'] > 0: m['vida'] = min(m['max_vida'], m['vida'] + m['max_vida'] * 0.2); c.curar_estados(m)
            c.guardar_y_aplicar(j)
            c.efectos.cura(c.mundo['ef'], px, py); efecto_onda(nivel, px, py, 160, 'hada', 700)
        elif clave == 'oleada_psiquica':
            area(j, nivel, (px, py), 150 + 25 * et, 20 + 8 * et, 'psiquico', 140)
        elif clave == 'agujero_negro':
            dest = c.punto_apuntado(j, 300)
            cosa(nivel, clase='agujero', x=dest[0], y=dest[1], radio=170, hasta=ahora + 3000, tick=0, daño=daño(j, 8, 'psiquico'))
        elif clave == 'control_mental':
            usados = []
            for _ in range(1 if et == 1 else 2):
                o = objetivo_cercano(j, nivel, 360, usados)
                if o and not o.get('jefe') and not o.get('de_jefe'):
                    o['controlado_hasta'] = ahora + (5000 if et == 1 else 7000); o['estado_ia'] = 'patrulla'; o['aviso'] = None; usados.append(o)
            c.cartel(nivel, ('Controla a ' + ', '.join(o['nombre'].title() for o in usados)) if usados else 'No hay nadie cerca para controlar', 1000)
        elif clave == 'hacha_piedra':
            for k in range(1, 6):
                cosa(nivel, clase='piedras', x=px + ax * 70 * k, y=py + ay * 70 * k, radio=34, hasta=ahora + 6000, tick=0, daño=daño(j, 12, 'roca'))
        elif clave == 'roca_afilada':
            c.iniciar_embestida(j, {'tipo': 'roca', 'daño': daño(j, 26 + 6 * et, 'roca', 'embestida'), 'distancia': 220, 'velocidad': 22, 'area': 22,
                                    'retroceso': 30, 'forma': 'embestida', 'jugador': True})
        elif clave == 'rencor':
            guardado = e.pop('rencor', 0)
            if guardado < 1: c.cartel(nivel, 'Todavía no le guarda rencor a nadie', 900); return
            for o in c.objetivos_de(nivel, False):
                if o['vida'] > 0 and math.hypot(o['rect'].centerx - px, o['rect'].centery - py) < 220:
                    c.recibir_ataque(o, {'tipo': 'fantasma', 'daño': round(guardado * 1.5), 'retroceso': 30, 'jugador': True}, j['direccion'])
            efecto_onda(nivel, px, py, 220, 'fantasma', 700)
        elif clave == 'raices':
            dest = c.punto_apuntado(j, 320)
            cosa(nivel, clase='raices', x=dest[0], y=dest[1], radio=110 + 10 * et, hasta=ahora + 2500, tick=0, daño=daño(j, 7, 'planta'), atrapados=[])
        elif clave == 'vuelo':
            e['vuelo_hasta'] = ahora + 3000
        elif clave == 'dracoflechas':
            for k in range(et):
                cosa(nivel, clase='flecha', x=float(px), y=float(py), vx=ax * 6 + random.uniform(-2, 2), vy=ay * 6 + random.uniform(-2, 2),
                     hasta=ahora + 2500, daño=daño(j, 24 + 4 * et, 'dragon'), golpeados=[])
        elif clave == 'ilusion':
            presentes = sorted({o['nombre'] for o in enemigos_vivos(nivel)} - {j['nombre']})
            disfraz = random.choice(presentes) if presentes else random.choice(('pikachu', 'eevee', 'zigzagoon', 'lillipup'))
            j['ilusion_hasta'] = ahora + 8000; j['disfraz'] = disfraz; c.rehacer_animador(j)
            for o in enemigos_vivos(nivel):
                o['estado_ia'] = 'patrulla'; o['aviso'] = None; o['embestida_ia'] = None; o['vida_ant'] = o['vida']
            c.cartel(nivel, 'Ilusión: parece un ' + disfraz.replace('_', ' ').title(), 1200)
        elif clave == 'tajo_teledirigido':
            o = objetivo_cercano(j, nivel, 500)
            if o:
                e['teledirigido'] = o
                dx, dy = o['rect'].centerx - px, o['rect'].centery - py; d = math.hypot(dx, dy) or 1; j['aim'] = (dx / d, dy / d)
            c.iniciar_embestida(j, {'tipo': 'acero', 'daño': daño(j, 26 + 8 * et, 'acero', 'embestida'), 'distancia': 420, 'velocidad': 14,
                                    'area': 24, 'retroceso': 25, 'forma': 'embestida', 'jugador': True})
            if j['nombre'] == 'aegislash': e['espada_hasta'] = ahora + 5000; e.pop('escudo_hasta', None)
        elif clave == 'metronomo':
            opcion = random.choice(('proyectil', 'area', 'cura', 'buff', 'estado'))
            tipo = random.choice(('fuego', 'agua', 'electrico', 'planta', 'hielo', 'psiquico', 'dragon', 'siniestro', 'hada', 'roca'))
            if opcion == 'proyectil':
                c.lanzar(j, {'tipo': tipo, 'daño': daño(j, 40, tipo), 'distancia': 480, 'area': 20, 'velocidad': 10, 'retroceso': 30, 'cantidad': 3, 'abanico': 30, 'jugador': True}, nivel['proyectiles_pokemon'])
            elif opcion == 'area': area(j, nivel, (px, py), 190, 34, tipo, 50)
            elif opcion == 'cura': j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.3); c.efectos.cura(c.mundo['ef'], px, py)
            elif opcion == 'buff': c.poner_buff(j, 'daño', 1.4, 6000); c.poner_buff(j, 'velocidad', 1.3, 6000)
            else: area(j, nivel, (px, py), 200, 4, 'normal', 0, {'tipo': random.choice(('dormir', 'paralizar', 'confundir')), 'duracion': 2500, 'probabilidad': 100})
            c.cartel(nivel, 'Metrónomo: ' + {'proyectil': 'una ráfaga de ' + tipo, 'area': 'una explosión de ' + tipo, 'cura': 'una cura',
                                             'buff': 'más daño y velocidad', 'estado': 'un estado para todos'}[opcion], 1000)
        elif clave == 'jardin':
            cosa(nivel, clase='jardin', x=px, y=py, radio=130, hasta=ahora + 6000, tick=0)
        # especiales de especie
        elif clave == 'lariat':
            area(j, nivel, (px, py), 120, 40, 'siniestro', 60)
            j['atacando'], j['anim_ataque'] = True, 'rotate' if 'rotate' in j['animador'].sprites else None
        elif clave == 'mirada_especial':
            for o in cono(j, nivel, 300, 35): poner_a(o, 'paralizar', 2500)
            efecto_onda(nivel, px + ax * 120, py + ay * 120, 130, 'normal')
        elif clave == 'guillotina_especial':
            for o in cono(j, nivel, 110, 60):
                if not o.get('jefe') and o['vida'] < o['max_vida'] * 0.30:
                    o['vida'] = 0; c.cartel(nivel, '¡Guillotina!', 700)
                else: golpear_a(j, o, 50, 'dragon', 40)
            nivel['efectos'].append({'x': px, 'y': py, 'linea': (px + ax * 110, py + ay * 110), 'radio': 18, 'tipo': 'dragon', 'inicio': ahora, 'hasta': ahora + 250})
        elif clave == 'pelo_trenzado':
            for o in cono(j, nivel, 150, 50): golpear_a(j, o, 60, 'hada', 120)
            efecto_onda(nivel, px + ax * 80, py + ay * 80, 110, 'hada'); c.temblor(nivel, 180)
        elif clave == 'blindada':
            c.iniciar_embestida(j, {'tipo': 'acero', 'daño': daño(j, 48, 'acero', 'embestida'), 'distancia': 300, 'velocidad': 12, 'area': 30, 'retroceso': 60,
                                    'forma': 'embestida', 'jugador': True})
            j['inv_hasta'] = max(j.get('inv_hasta', 0), ahora + 900)
        elif clave == 'martillazo':
            for o in cono(j, nivel, 140, 55):
                golpear_a(j, o, 70 * (2 if 'volador' in c.tipos_de(o) else 1), 'hada', 90, {'tipo': 'paralizar', 'duracion': 800, 'probabilidad': 100})
            c.efectos.explosion(c.mundo['ef'], px + ax * 80, py + ay * 80, 90); c.temblor(nivel, 260)
        elif clave == 'mordida_colosal':
            o = objetivo_cercano(j, nivel, 130)
            if o: golpear_a(j, o, 70, 'roca', 10, {'tipo': 'paralizar', 'duracion': 1500, 'probabilidad': 100}); c.temblor(nivel, 200)
        elif clave == 'telarana':
            dest = c.punto_apuntado(j, 280)
            area(j, nivel, dest, 110, 12, 'electrico', 0, {'tipo': 'paralizar', 'duracion': 2000, 'probabilidad': 100})
            cosa(nivel, clase='red', x=dest[0], y=dest[1], radio=110, hasta=ahora + 2000)
        elif clave == 'tormenta_hojas':
            cosa(nivel, clase='hojas', x=px, y=py, radio=100, hasta=ahora + 3000, tick=0, daño=daño(j, 10, 'planta'), j=j)
        elif clave == 'infierno':
            for o in c.objetivos_de(nivel, False):
                if o['vida'] > 0 and math.hypot(o['rect'].centerx - px, o['rect'].centery - py) < 180:
                    golpear_a(j, o, 40 * (2 if o.get('estado') and o.get('estado_hasta', 0) > ahora else 1), 'fantasma', 30, {'tipo': 'quemar', 'duracion': 3000, 'probabilidad': 60})
            efecto_onda(nivel, px, py, 180, 'fuego', 700)
        elif clave == 'propulsion':
            c.iniciar_embestida(j, {'tipo': 'roca', 'daño': daño(j, 34, 'roca', 'embestida'), 'distancia': 380, 'velocidad': 18, 'area': 24, 'retroceso': 40,
                                    'forma': 'embestida', 'jugador': True})

    def termina_ilusion(j):
        if j.get('ilusion_hasta'):
            j.pop('ilusion_hasta', None)
            if j.get('disfraz'): j.pop('disfraz'); c.rehacer_animador(j)

    def dentro_jardin(nivel, j):
        ahora = T()
        return any(x['clase'] == 'jardin' and x['hasta'] > ahora and math.hypot(x['x'] - j['rect'].centerx, x['y'] - j['rect'].centery) < x['radio']
                   for x in nivel.get('mec_cosas', ()))

    # ---------- lo que quedo en la sala
    def actualizar_cosas(j, nivel):
        ahora = T()
        cosas = nivel.get('mec_cosas')
        if not cosas: return
        for x in cosas[:]:
            cl = x['clase']
            if cl == 'bomba' and ahora >= x['hasta']:
                area(x['j'], nivel, (x['x'], x['y']), x['radio'], 0, 'planta', 40)   # el daño ya viene escalado
                for o in c.objetivos_de(nivel, True):
                    if o['vida'] > 0 and math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y']) < x['radio'] + max(o['rect'].size) / 2:
                        c.recibir_ataque(o, {'tipo': 'planta', 'daño': x['daño'], 'retroceso': 30, 'jugador': True}, None)
                c.efectos.explosion(c.mundo['ef'], x['x'], x['y'], x['radio']); cosas.remove(x); continue
            if ahora >= x['hasta']: cosas.remove(x); continue
            if cl in ('nube', 'charco', 'piedras', 'agujero', 'raices', 'hojas') and ahora >= x.get('tick', 0):
                x['tick'] = ahora + (300 if cl == 'agujero' else 600)
                if cl == 'hojas': x['x'], x['y'] = x['j']['rect'].center
                for o in enemigos_vivos(nivel) + ([nivel['jefe']] if nivel.get('jefe') and nivel['jefe']['vida'] > 0 else []):
                    d = math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y'])
                    if d > x['radio'] + max(o['rect'].size) / 2: continue
                    if cl == 'agujero' and not o.get('jefe'):          # lo chupa hacia el centro
                        paso = min(26, d)
                        if d > 1: c.mover_entidad(o, round((x['x'] - o['rect'].centerx) / d * paso), round((x['y'] - o['rect'].centery) / d * paso))
                    if cl == 'raices' and o not in x['atrapados']: poner_a(o, 'paralizar', max(300, x['hasta'] - ahora)); x['atrapados'].append(o)
                    efecto = {'tipo': 'veneno', 'duracion': 3000, 'probabilidad': 100} if cl in ('nube', 'charco') else None
                    if cl == 'nube': poner_a(o, 'ralentizar', 1200)
                    c.recibir_ataque(o, {'tipo': {'nube': 'veneno', 'charco': 'veneno', 'piedras': 'roca', 'agujero': 'psiquico', 'raices': 'planta', 'hojas': 'planta'}[cl],
                                         'daño': x['daño'], 'retroceso': 0, 'efecto': efecto, 'jugador': True}, None)
                    if cl == 'piedras': x['hasta'] = min(x['hasta'], ahora + 2500)
            if cl == 'jardin' and math.hypot(x['x'] - j['rect'].centerx, x['y'] - j['rect'].centery) < x['radio'] and nivel['frame'] % 30 == 0:
                j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.01)
            if cl == 'flecha':
                o = min((o for o in c.objetivos_de(nivel, False) if o['vida'] > 0 and o not in x['golpeados']),
                        key=lambda o: math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y']), default=None)
                if o:
                    dx, dy = o['rect'].centerx - x['x'], o['rect'].centery - x['y']; d = math.hypot(dx, dy) or 1
                    x['vx'] = x['vx'] * 0.85 + dx / d * 1.6; x['vy'] = x['vy'] * 0.85 + dy / d * 1.6
                    if d < 20 + max(o['rect'].size) / 2:
                        c.recibir_ataque(o, {'tipo': 'dragon', 'daño': x['daño'], 'retroceso': 25, 'jugador': True}, None)
                        x['golpeados'].append(o); c.efectos.golpe(c.mundo['ef'], x['x'], x['y'], (111, 53, 252), 'dragon'); x['hasta'] = ahora
                x['x'] += x['vx']; x['y'] += x['vy']

    # ---------- enemigos con mecanica
    def enemigo(e, j, nivel):
        """Lo que hacen algunos enemigos por su cuenta. Devuelve True si este cuadro ya lo manejo (no corre la IA comun)."""
        que = ENEMIGO.get(e['nombre'])
        if not que or e.get('controlado_hasta', 0) > T(): return False
        ahora = T(); ex, ey = e['rect'].center; jx, jy = j['rect'].center
        dist = math.hypot(jx - ex, jy - ey)
        m = e.setdefault('mec_e', {})
        if que == 'disfraz':
            if not m.get('listo'):
                m['listo'] = True
                otros = [n for n in c.enemigos_de_era(nivel) if n not in ENEMIGO]
                if otros: m['disfraz'] = random.choice(otros); c.rehacer_animador(e, m['disfraz'])
            elif m.get('disfraz') and e['vida'] < e['max_vida']:
                m.pop('disfraz'); c.rehacer_animador(e)
                c.cartel(nivel, '¡Era ' + e['nombre'].replace('_', ' ').title() + '!', 900); c.efectos.aparecer(c.mundo['ef'], ex, ey)
            return False
        if que == 'huye':
            if e['vida'] < e['max_vida'] * 0.3 and dist < 300:
                d = dist or 1
                c.mover_entidad(e, round((ex - jx) / d * 3), round((ey - jy) / d * 3)); e['aviso'] = None
                return True
            return False
        if e.get('estado_ia') != 'caza' or (e.get('estado_hasta', 0) > ahora and e.get('estado') in ('paralizar', 'dormir', 'confundir')): return False
        if que == 'excava':
            fase = m.get('fase')
            if not fase and dist < 420 and ahora >= m.get('listo', 0):
                m.update({'fase': 'bajo', 'hasta': ahora + 1100}); e['invulnerable'] = True; e['aviso'] = None
                c.efectos.polvo(c.mundo['ef'], ex, ey)
            if fase == 'bajo':
                d = dist or 1
                c.mover_entidad(e, round((jx - ex) / d * 5), round((jy - ey) / d * 5), True)
                if ahora >= m['hasta'] or dist < 20: m.update({'fase': 'aviso', 'hasta': ahora + 650, 'donde': (jx, jy)})
                return True
            if fase == 'aviso':
                if ahora >= m['hasta']:
                    e['rect'].center = (round(m['donde'][0]), round(m['donde'][1])); e['invulnerable'] = False
                    c.efectos.explosion(c.mundo['ef'], *m['donde'], 70)
                    if math.hypot(jx - m['donde'][0], jy - m['donde'][1]) < 55:
                        c.golpe_al_jugador(j, e['daño'] * 1.2, 'tierra', e)
                        c.poner_estado(j, 'aturdido', 1000); c.cartel(nivel, '¡Te enterró!', 800)
                    m.update({'fase': None, 'listo': ahora + 6500})
                return True
            return False
        if que in ('chilla', 'mente', 'esporas'):
            radio = {'chilla': 200, 'mente': 260, 'esporas': 150}[que]
            if not m.get('aviso_hasta') and dist < radio and ahora >= m.get('listo', 0):
                m['aviso_hasta'] = ahora + (700 if que != 'esporas' else 400); e['aviso'] = None
            if m.get('aviso_hasta'):
                if ahora < m['aviso_hasta']: return True
                m.pop('aviso_hasta'); m['listo'] = ahora + {'chilla': 7000, 'mente': 9000, 'esporas': 8000}[que]
                if que == 'esporas':
                    cosa(nivel, clase='nube_enemiga', x=ex, y=ey, radio=95, hasta=ahora + 4000, tick=0)
                elif dist < radio + 20:
                    if que == 'chilla': c.poner_estado(j, 'aturdido', 800); c.cartel(nivel, '¡Supersónico! Te aturdió', 700)
                    else: c.poner_estado(j, 'confusion', 2200); c.cartel(nivel, '¡Te controla la mente!', 800)
                return True
        return False

    def golpe_enemigo(e, j, hecho):
        """Un enemigo te pego cuerpo a cuerpo: la mordida de Mawile paraliza y arrastra."""
        if ENEMIGO.get(e['nombre']) == 'muerde' and hecho >= 1 and random.random() < 0.3:
            c.poner_estado(j, 'paralisis', 1800)
            dx, dy = e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery; d = math.hypot(dx, dy) or 1
            c.mover_entidad(j, round(dx / d * min(45, d - 25)), round(dy / d * min(45, d - 25)))

    def nubes_enemigas(j, nivel):
        """Las esporas de Foongus enemigos: si estas adentro te envenenan."""
        ahora = T()
        for x in nivel.get('mec_cosas', ()):
            if x['clase'] == 'nube_enemiga' and x['hasta'] > ahora and ahora >= x.get('tick', 0):
                x['tick'] = ahora + 500
                if math.hypot(x['x'] - j['rect'].centerx, x['y'] - j['rect'].centery) < x['radio']: c.poner_estado(j, 'veneno')

    # ---------- dibujo
    _capas = {}

    def circulo(ventana, x, y, radio, color, alfa, borde=0):
        clave = (radio, color, alfa, borde)
        if clave not in _capas:
            s = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alfa), (radio + 2, radio + 2), radio, borde)
            _capas[clave] = s
        ventana.blit(_capas[clave], (round(x - radio - 2), round(y - radio - 2)))

    def dibujar(nivel, j, cx, cy):
        """Lo que dejaron las mecanicas en la sala y los avisos de los enemigos con mecanica."""
        ventana = c.ventana; ahora = T()
        for x in nivel.get('mec_cosas', ()):
            if x['hasta'] <= ahora and x['clase'] != 'bomba': continue
            sx, sy = x['x'] - cx, x['y'] - cy
            cl = x['clase']
            if cl == 'bomba':
                k = max(0.0, min(1.0, (x['hasta'] - ahora) / 900))
                circulo(ventana, sx, sy, x['radio'], (255, 120, 160), 40)
                pygame.draw.circle(ventana, (250, 90, 150), (round(sx), round(sy)), 9)
                pygame.draw.circle(ventana, (255, 230, 120), (round(sx), round(sy)), 4)
                pygame.draw.circle(ventana, (255, 255, 255), (round(sx), round(sy)), round(x['radio'] * (1 - k)), 2)
            elif cl in ('nube', 'nube_enemiga'):
                for k in range(5):
                    ang = ahora / 900 + k * 1.26
                    circulo(ventana, sx + math.cos(ang) * x['radio'] * 0.45, sy + math.sin(ang) * x['radio'] * 0.35, round(x['radio'] * 0.55), (160, 90, 200), 55)
            elif cl == 'charco': circulo(ventana, sx, sy, x['radio'], (150, 70, 190), 90)
            elif cl == 'jardin':
                circulo(ventana, sx, sy, x['radio'], (250, 170, 210), 45)
                for k in range(10):
                    ang = k * 0.628 + ahora / 3000
                    px, py = sx + math.cos(ang) * x['radio'] * 0.8, sy + math.sin(ang) * x['radio'] * 0.8
                    pygame.draw.circle(ventana, ((250, 120, 170), (250, 230, 120), (240, 240, 250))[k % 3], (round(px), round(py)), 6)
            elif cl == 'agujero':
                for k in range(4):
                    circulo(ventana, sx, sy, max(4, round(x['radio'] * (1 - ((ahora / 600 + k / 4) % 1)))), (120, 60, 200), 50, 3)
                pygame.draw.circle(ventana, (10, 0, 20), (round(sx), round(sy)), 22)
            elif cl == 'raices':
                for k in range(8):
                    ang = k * 0.785
                    pygame.draw.line(ventana, (90, 60, 30), (round(sx), round(sy)), (round(sx + math.cos(ang) * x['radio']), round(sy + math.sin(ang) * x['radio'])), 5)
                circulo(ventana, sx, sy, x['radio'], (80, 140, 60), 40)
            elif cl == 'piedras':
                for k in range(3):
                    pygame.draw.polygon(ventana, (150, 140, 120), [(sx - 14 + k * 12, sy + 10), (sx - 8 + k * 12, sy - 14), (sx - 2 + k * 12, sy + 10)])
            elif cl == 'red':
                for k in range(6):
                    ang = k * 1.047
                    pygame.draw.line(ventana, (250, 240, 120), (round(sx), round(sy)), (round(sx + math.cos(ang) * x['radio']), round(sy + math.sin(ang) * x['radio'])), 2)
                pygame.draw.circle(ventana, (250, 240, 120), (round(sx), round(sy)), round(x['radio'] * 0.6), 2)
                pygame.draw.circle(ventana, (250, 240, 120), (round(sx), round(sy)), x['radio'], 2)
            elif cl == 'hojas':
                for k in range(8):
                    ang = ahora / 200 + k * 0.785
                    pygame.draw.circle(ventana, (110, 200, 80), (round(sx + math.cos(ang) * x['radio']), round(sy + math.sin(ang) * x['radio'])), 7)
            elif cl == 'flecha':
                pygame.draw.circle(ventana, (140, 90, 250), (round(sx), round(sy)), 9)
                pygame.draw.circle(ventana, (230, 220, 255), (round(sx), round(sy)), 4)
        # el rastro de pasto de Chikorita: un brillo verde mientras dura
        for (f, k), (_, hasta) in nivel.get('rastro_pasto', {}).items():
            if hasta - ahora < 1500 and (ahora // 150) % 2: continue
            tam = nivel['ent']['tam']
            circulo(ventana, k * tam + tam / 2 - cx, f * tam + tam / 2 - cy, tam // 3, (140, 255, 140), 35)
        # avisos de los enemigos con mecanica
        for e in nivel['enemigos']:
            m = e.get('mec_e') or {}
            ex, ey = e['rect'].centerx - cx, e['rect'].centery - cy
            if m.get('aviso_hasta'):
                que = ENEMIGO.get(e['nombre'])
                color = {'chilla': (255, 240, 120), 'mente': (200, 120, 255), 'esporas': (170, 100, 210)}.get(que, (255, 255, 255))
                radio = {'chilla': 200, 'mente': 260, 'esporas': 150}.get(que, 150)
                k = 1 - max(0.0, (m['aviso_hasta'] - ahora) / 700)
                pygame.draw.circle(ventana, color, (ex, ey), max(4, round(radio * k)), 3)
            if m.get('fase') == 'aviso':
                dx, dy = m['donde'][0] - cx, m['donde'][1] - cy
                circulo(ventana, dx, dy, 55, (200, 140, 80), 70); pygame.draw.circle(ventana, (255, 80, 60), (round(dx), round(dy)), 55, 3)
            if e.get('controlado_hasta', 0) > ahora:
                pygame.draw.circle(ventana, (200, 120, 255), (ex, e['rect'].top - cy - 10), 7, 2)

    def dibujar_hud(j, ventana, W, H, cx, cy):
        """Flechas en el borde hacia los enemigos de afuera (Noibat), la camara lenta y lo que guarda Shuppet."""
        ahora = T(); e = estado(j); nivel = c.mundo.get('nivel')
        if not nivel: return
        if es(j, 'prediccion'):
            for o in enemigos_vivos(nivel):
                sx, sy = o['rect'].centerx - cx, o['rect'].centery - cy
                if 0 <= sx <= W and 0 <= sy <= H: continue
                mx, my = W / 2, H / 2; dx, dy = sx - mx, sy - my
                k = min((W / 2 - 24) / abs(dx) if dx else 9e9, (H / 2 - 24) / abs(dy) if dy else 9e9)
                px, py = mx + dx * k, my + dy * k; ang = math.atan2(dy, dx)
                pts = [(px + math.cos(ang) * 12, py + math.sin(ang) * 12), (px + math.cos(ang + 2.5) * 10, py + math.sin(ang + 2.5) * 10),
                       (px + math.cos(ang - 2.5) * 10, py + math.sin(ang - 2.5) * 10)]
                pygame.draw.polygon(ventana, (255, 90, 80), pts); pygame.draw.polygon(ventana, (20, 20, 20), pts, 2)
        if e.get('lento_hasta', 0) > ahora:
            velo = pygame.Surface((W, H), pygame.SRCALPHA); velo.fill((60, 90, 200, 50)); ventana.blit(velo, (0, 0))
        if e.get('prediccion_hasta', 0) > ahora:
            pygame.draw.circle(ventana, (150, 220, 255), (j['rect'].centerx - cx, j['rect'].centery - cy), 34 + round(3 * math.sin(ahora / 80)), 2)
        if e.get('rencor'):
            k = e['rencor'] / max(1, j['max_vida'] * 0.6)
            pygame.draw.rect(ventana, (40, 20, 60), (j['rect'].centerx - cx - 20, j['rect'].bottom - cy + 6, 40, 5))
            pygame.draw.rect(ventana, (170, 90, 230), (j['rect'].centerx - cx - 20, j['rect'].bottom - cy + 6, round(40 * k), 5))
        if e.get('arrokuda'):
            pygame.draw.circle(ventana, (90, 140, 220), (j['rect'].centerx - cx + 18, j['rect'].top - cy - 6), 6)
        if e.get('marchas'):
            for k in range(e['marchas']): pygame.draw.circle(ventana, (200, 200, 220), (j['rect'].centerx - cx - 12 + k * 12, j['rect'].bottom - cy + 10), 4, 2)

    return SimpleNamespace(mec=mec, es=es, nueva_sala=nueva_sala, al_cambiar=al_cambiar, mult_golpe=mult_golpe, tras_golpe=tras_golpe, remate=remate,
                           mult_enfriamiento_combo=mult_enfriamiento_combo, mult_parry=mult_parry, al_parry=al_parry, recibido=recibido,
                           estado_puesto=estado_puesto, derrota=derrota, sala_limpia=sala_limpia, mult_romper=mult_romper, mult_iman=mult_iman,
                           mult_monedas=mult_monedas, objeto_roto=objeto_roto, aviso_mult=aviso_mult, regen_energia=regen_energia,
                           mult_velocidad=mult_velocidad, mult_recarga=mult_recarga, mult_recarga_especial=mult_recarga_especial,
                           ignora_solidos=ignora_solidos, invisible=invisible, altura_vuelo=altura_vuelo, cuadro=cuadro, lento=lento, usar=usar,
                           enemigo=enemigo, golpe_enemigo=golpe_enemigo, nubes_enemigas=nubes_enemigas, dibujar=dibujar, dibujar_hud=dibujar_hud,
                           termina_ilusion=termina_ilusion)
