"""
mecanicas.py - Lo que hace unico a cada linea evolutiva: una pasiva o un especial propio, inspirado en lo que dice su Pokedex.
Las del juego original (Pikachu, Squirtle, Machop...) cambian la forma de moverse y de pelear: rodar, saltar, cargar golpes,
teletransportarse, agarrar y revolear, esquives que cortan o dejan cosas, disparos que vuelven...

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
        ('jardin', ('flabebe', 'floette', 'florges')),
        # ---------- las lineas del juego original
        ('ola', ('lapras',)),
        ('paso_helado', ('sneasel', 'weavile')),
        ('escarcha', ('snorunt',)), ('bloque_hielo', ('glalie',)), ('velo_fantasma', ('froslass',)),
        ('bola_nieve', ('spheal', 'sealeo', 'walrein')),
        ('manto_nieve', ('vanillite', 'vanillish', 'vanilluxe')),
        ('picado', ('rookidee', 'corvisquire', 'corviknight')),
        ('plancha_voladora', ('hawlucha',)),
        ('teletransporte', ('natu', 'xatu')),
        ('globo', ('drifloon', 'drifblim')),
        ('iman', ('magnemite', 'magneton', 'magnezone')),
        ('estatica_veloz', ('pichu', 'pikachu', 'raichu')),
        ('lana_electrica', ('mareep', 'flaaffy', 'ampharos')),
        ('cadena', ('shinx', 'luxio', 'luxray')),
        ('carrera_electrica', ('electrike', 'manectric')),
        ('bola_pinchos', ('sandshrew', 'sandslash')),
        ('rodar_explosivo', ('geodude', 'graveler', 'golem')),
        ('bumeran', ('cubone', 'marowak')),
        ('pantano', ('wooper', 'quagsire')),
        ('salto_tiburon', ('gible', 'gabite', 'garchomp')),
        ('puño_propulsado', ('golett', 'golurk')),
        ('furia', ('mankey', 'primeape', 'annihilape')),
        ('llave', ('machop', 'machoke', 'machamp')),
        ('patada_salto', ('torchic', 'combusken', 'blaziken')),
        ('aura', ('riolu', 'lucario')),
        ('viga', ('timburr', 'gurdurr', 'conkeldurr')),
        ('barro', ('mudkip', 'marshtomp', 'swampert')),
        ('caparazon', ('squirtle', 'wartortle', 'blastoise')),
        ('sustituto', ('froakie', 'frogadier', 'greninja')),
        ('baluarte', ('mareanie', 'toxapex')),
        ('corte_al_paso', ('oshawott', 'dewott', 'samurott')),
        ('alas_vendaval', ('fletchling', 'fletchinder', 'talonflame'))):
    LINEAS.update(_linea(_clave, *_especies))
LINEAS['great_tusk'] = ('rodada', 3); LINEAS['roaring_moon'] = ('vuelo', 3); LINEAS['brute_bonnet'] = ('humo_toxico', 3)
LINEAS['glalie'] = ('bloque_hielo', 2); LINEAS['froslass'] = ('velo_fantasma', 2)      # Snorunt se divide: cada rama con lo suyo
LINEAS['clodsire'] = ('pantano', 2); LINEAS['samurott_hisui'] = ('corte_al_paso', 3)


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
    'martillo': _e('Martillo propulsor', 'golpea el piso con el martillo y sale disparada hacia adelante. Sus golpes cuerpo a cuerpo hacen el doble a los voladores '
                   'y 30% más a los de acero. Tinkaton: su ESQUIVE es el martillo propulsor (sale disparada lejos y cae golpeando), y su martillazo gigante (R) la deja aturdida un momento', 6000, 'hada'),
    'jardin': _e('Jardín floral', 'planta un círculo de flores por 6 s: adentro se cura 2% por segundo y recibe 20% menos', 18000, 'hada'),
    # ---------- las lineas del juego original: formas distintas de moverse y de pelear
    'ola': _e('Surf', 'se sube a una ola y avanza en línea arrastrando a todos los que toca hasta el final', 9000, 'agua'),
    'paso_helado': _p('Paso helado', 'el esquive atraviesa a los enemigos y les hace un tajo helado que los frena. Weavile: si el esquive corta a alguien, se recarga al instante'),
    'escarcha': _p('Cuerpo de escarcha', 'sus golpes cuerpo a cuerpo a veces (25%) congelan un poco: el enemigo queda frenado. Evoluciona en Glalie o en Froslass'),
    'bloque_hielo': _e('Bloque de hielo', 'se encierra en un bloque de hielo 1,5 s (no recibe nada, no se mueve) y revienta congelando a los de alrededor', 9000, 'hielo'),
    'velo_fantasma': _e('Velo fantasma', 'se vuelve un espíritu de nieve 2,5 s: atraviesa paredes y enemigos, corre más, los enemigos la pierden de vista y los que atraviesa quedan congelados', 10000, 'hielo'),
    'bola_nieve': _e('Bola de nieve', 'se hace bola y rueda: corre mucho más y atropella a lo que toca. Cuanto más rueda más grande y más fuerte pega. Atacar (o R de nuevo) lo para', 1500, 'hielo'),
    'manto_nieve': _p('Manto de nieve', 'deja un rastro de nieve donde camina: los enemigos que lo pisan quedan frenados (dura más al evolucionar)'),
    'picado': _e('Picado', 'levanta vuelo y cae en picada hacia donde apuntás: en el aire no lo tocan y le pega a todo lo que cruza. Corviknight aterriza blindado 1 s', 6000, 'volador'),
    'plancha_voladora': _e('Plancha voladora', 'salta hacia donde apuntás (en el aire no lo tocan) y cae aplastando y aturdiendo; si cae justo encima de alguien le hace el doble', 7000, 'lucha'),
    'teletransporte': _e('Teletransporte', 'aparece donde apuntás, atravesando lo que haya en el medio. Xatu deja una premonición donde estaba: explota al segundo', 4500, 'psiquico'),
    'globo': _p('Globo', 'flota: el esquive es un planeo casi el doble de largo. Cuando lo debilitan, explota (Detonación) y lastima a todos alrededor'),
    'iman': _p('Imán', 'sus disparos se curvan solos hacia el enemigo más cercano (más fuerte al evolucionar)'),
    'estatica_veloz': _p('Estática veloz', 'el esquive deja una estela eléctrica que paraliza a los que la cruzan. Raichu esquiva más lejos; Pichu a veces se electrocuta a sí mismo'),
    'lana_electrica': _p('Lana eléctrica', 'caminando junta electricidad en la lana (corriendo, más rápido). Con la lana llena, el próximo golpe suelta una descarga alrededor que paraliza'),
    'cadena': _p('Chispa en cadena', 'el remate del combo salta en cadena a 2, 3 o 4 enemigos cercanos (según la evolución)'),
    'carrera_electrica': _p('Carrera eléctrica', 'corriendo junta carga: el primer golpe después de correr pega más (hasta +50%, Manectric +80%) y paraliza'),
    'bola_pinchos': _p('Bola de pinchos', 'esquiva hecho una bola: el esquive es más largo y lastima a lo que toca. Sandslash además deja pinchos en el camino'),
    'rodar_explosivo': _e('Rodar explosivo', 'se tira rodando y al terminar explota alrededor (más grande al evolucionar). Golem pierde 15% de su vida al explotar', 8000, 'roca'),
    'bumeran': _p('Hueso bumerán', 'su ataque a distancia es su hueso: va, vuelve y pega a la ida y a la vuelta. Hasta que no vuelve no puede tirarlo de nuevo'),
    'pantano': _e('Pantano', 'escupe barro donde apunta: un charco que frena mucho a los enemigos y en el que él se desliza rápido (Clodsire: barro venenoso)', 8000, 'tierra'),
    'salto_tiburon': _e('Salto tiburón', 'salta sobre el enemigo más cercano y lo muerde. Garchomp rebota y muerde a un segundo enemigo', 6000, 'dragon'),
    'puño_propulsado': _e('Puño propulsado', 'MANTENÉ R para cargar el puño (camina lento) y soltalo: sale propulsado hacia adelante. Más carga, más lejos y más daño (Golurk carga más rápido)', 7000, 'tierra'),
    'furia': _p('Furia', 'cada golpe que recibe lo enoja: +5% de daño y velocidad por golpe (hasta 4, 6 u 8); se le pasa si deja de pelear. Annihilape: la primera vez por sala que lo debilitan queda con 1 de vida'),
    'llave': _e('Llave', 'agarra al enemigo de adelante y lo revolea hacia donde apuntás: al que choca le pega, y al caer queda aturdido. A los jefes solo les pega', 7000, 'lucha'),
    'patada_salto': _p('Patada en salto', 'el esquive termina en una patada de fuego alrededor. Blaziken puede esquivar dos veces seguidas'),
    'aura': _p('Aura', 'lee las intenciones: la ventana de parry dura más (Riolu +20%, Lucario +40%). El parry de Lucario dispara una Esfera Aural que persigue'),
    'viga': _e('Golpe de viga', 'golpea el piso con su viga: una onda de choque avanza en línea pegándole a todo (Conkeldurr: dos ondas en abanico)', 7000, 'lucha'),
    'barro': _p('Barro', 'el remate del combo deja un charco de barro que frena a los enemigos; en el barro, el agua y los charcos se mueve mucho más rápido'),
    'caparazon': _e('Caparazón', 'se mete en el caparazón: recibe 80% menos, se desliza más rápido y empuja a los que toca. Blastoise dispara agua girando. Atacar (o R de nuevo) lo saca', 1500, 'agua'),
    'sustituto': _p('Sustituto', 'el esquive deja un sustituto de agua: los enemigos cerca lo pierden de vista y al rato revienta. Greninja: con un esquive perfecto aparece detrás del enemigo'),
    'baluarte': _e('Baluarte', 'se encierra en su cúpula de púas (2 s, Toxapex 3 s y se cura): casi no recibe daño, y el que le pega se envenena y se lastima', 10000, 'veneno'),
    'corte_al_paso': _e('Corte al paso', 'sale disparado con su vieira y un instante después todos los que cruzó reciben el tajo. Samurott corta dos veces; el de Hisui deja envenenado', 6000, 'agua'),
    'alas_vendaval': _p('Alas vendaval', 'con más de 75% de vida, esquivar no gasta energía. Fletchinder y Talonflame dejan fuego al esquivar'),
}

# especiales extra de una especie en particular (ademas de su pasiva de linea)
ESPECIE_ESPECIAL = {
    'incineroar': _e('Lariat Oscuro', 'gira con los brazos abiertos y le pega a todo alrededor', 9000, 'siniestro', clave='lariat'),
    'serperior': _e('Mirada', 'una mirada en cono que paraliza a los enemigos 2,5 s', 12000, 'normal', clave='mirada_especial'),
    'haxorus': _e('Guillotina', 'un tajo que remata a los enemigos con menos de 30% de vida (a los jefes les pega fuerte)', 12000, 'dragon', clave='guillotina_especial'),
    'grimmsnarl': _e('Pelo trenzado', 'un golpe gigante con el pelo hecho músculo: mucho daño y empuja', 9000, 'hada', clave='pelo_trenzado'),
    'aggron': _e('Embestida blindada', 'una embestida que no se frena y no deja que le peguen mientras dura', 9000, 'acero', clave='blindada'),
    'tinkaton': _e('Martillazo gigante', 'un martillazo enorme adelante que aturde... pero el peso la deja aturdida 1,2 s', 10000, 'hada', clave='martillazo'),
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


# ---------------------------------------------------------------- lazos de equipo
# Ademas de la pasiva que cada uno da desde la banca, el EQUIPO ENTERO gana algo si sus pokemon se complementan:
#   - resonancia: dos (o tres) que comparten un tipo potencian lo que ese tipo hace mejor
#   - lazos: lineas que segun su historia (la Pokedex, las regiones, lo que comen o con quien pelean) van juntas
# Cuentan los que estan en pie (tambien el que pelea). Lo que dan se suma a la sinergia (daño, defensa, velocidad, recargas, energia).
RESONANCIA = {'normal': 'energia', 'fuego': 'daño', 'agua': 'defensa', 'electrico': 'velocidad', 'planta': 'energia', 'hielo': 'enfriamiento',
              'lucha': 'daño', 'veneno': 'enfriamiento', 'tierra': 'defensa', 'volador': 'velocidad', 'psiquico': 'enfriamiento', 'bicho': 'velocidad',
              'roca': 'defensa', 'fantasma': 'enfriamiento', 'dragon': 'daño', 'siniestro': 'daño', 'acero': 'defensa', 'hada': 'energia'}
FUERZA_RESONANCIA = {2: 0.05, 3: 0.09}                  # dos del mismo tipo, o los tres (la de energia vale el triple)
TOPE_LAZOS = 0.18                                       # lo mas que pueden sumar los lazos a una misma cosa
_EEVEES = ('adaptable', 'absorbe_agua', 'agujas', 'absorbe_fuego', 'premonicion', 'sudor_venenoso', 'fotosintesis', 'cuerpo_helado', 'cintas')
# (nombre, por que van juntos, claves de linea, cuantas distintas hacen falta, lo que da)
LAZOS = (
    ('Trío elemental', 'fuego, agua y planta: el triángulo de siempre', None, 3, {'daño': 0.05, 'defensa': 0.05}),
    ('Compañeros de Hoenn', 'Mudkip y Torchic salieron juntos del mismo laboratorio', ('barro', 'patada_salto'), 2, {'daño': 0.06}),
    ('Familia Eevee', 'las evoluciones de Eevee se reconocen entre sí', _EEVEES, 2, {'enfriamiento': 0.06, 'energia': 0.12}),
    ('Rivales de dojo', 'Mankey y Machop entrenan pegándose', ('furia', 'llave'), 2, {'daño': 0.07}),
    ('Maestro y aprendiz', 'Lucario le enseña a leer el aura a los que pelean con los puños', ('aura', 'llave', 'viga', 'punos_toxicos'), 2, {'enfriamiento': 0.05, 'energia': 0.12}),
    ('Fósiles revividos', 'Anorith y Tyrunt vienen de la misma era', ('armadura_fosil', 'mandibula'), 2, {'defensa': 0.08}),
    ('Constructores', 'Timburr pone las vigas y Tinkatink los clavos', ('viga', 'martillo'), 2, {'defensa': 0.05, 'daño': 0.04}),
    ('Cazadora de cuervos', 'Tinkaton les tira piedras a los Corviknight; juntos aprendieron a respetarse', ('martillo', 'picado'), 2, {'daño': 0.08}),
    ('Filos', 'espadas, cuchillas y vieiras: se afilan entre ellos', ('cuerpo_cuchillas', 'tajo_teledirigido', 'corte_al_paso', 'tajo_psiquico', 'filo_amargo', 'tecnico', 'tecnico_veloz', 'hacha_piedra'), 2, {'daño': 0.06}),
    ('Tragamisil cargado', 'Cramorant siempre lleva un Arrokuda en el pico', ('tragamisil', 'helice'), 2, {'daño': 0.08, 'velocidad': 0.04}),
    ('Cortejo de sombras', 'velas, tocones y perros que acompañan a los que se fueron', ('absorbe_almas', 'raices', 'ultimos_respetos', 'rencor', 'globo', 'velo_fantasma'), 2, {'enfriamiento': 0.07}),
    ('Espada y escudo', 'Gardevoir protege y Gallade corta: salieron del mismo Kirlia', ('agujero_negro', 'tajo_psiquico', 'sincronia'), 2, {'daño': 0.04, 'defensa': 0.05}),
    ('Excavadores', 'Diglett y Sandshrew comparten túneles', ('bajo_tierra', 'bola_pinchos', 'salto_tiburon'), 2, {'velocidad': 0.07}),
    ('Máquinas', 'imanes y engranajes: una sola máquina', ('iman', 'engranajes', 'puño_propulsado'), 2, {'enfriamiento': 0.08}),
    ('Mares helados', 'Lapras lleva a los Spheal sobre el lomo', ('ola', 'bola_nieve'), 2, {'defensa': 0.08}),
    ('Perro y gato', 'Growlithe y Litten se pelean... y se cuidan', ('guardian', 'intimidacion', 'olfato', 'cadena'), 2, {'energia': 0.15, 'daño': 0.03}),
    ('Tramposos', 'ilusiones y bromas: nadie sabe por dónde vienen', ('ilusion', 'bromista', 'sustituto', 'paso_helado'), 2, {'velocidad': 0.07}),
    ('Sanadores', 'pasto, flores y un cuerno que cura', ('rastro_pasto', 'jardin', 'cuerno_sanador', 'abrigo_hojas', 'metronomo'), 2, {'defensa': 0.05, 'energia': 0.15}),
    ('Ninja y samurái', 'Greninja y Samurott: dos escuelas, un mismo río', ('sustituto', 'corte_al_paso'), 2, {'daño': 0.05, 'velocidad': 0.04}),
    ('Amigos del barro', 'Wooper y Mudkip comparten el charco', ('pantano', 'barro'), 2, {'velocidad': 0.07}),
    ('Montañas vivas', 'Tyranitar y Aggron mueven montañas (y se las comen)', ('chorro_arena', 'come_hierro', 'rodar_explosivo'), 2, {'defensa': 0.08}),
    ('Videntes', 'Xatu mira el futuro y Elgyem las mentes', ('teletransporte', 'control_mental', 'premonicion', 'oleada_psiquica'), 2, {'enfriamiento': 0.07}),
    ('Manada eléctrica', 'cuando corren juntos se cargan unos a otros', ('carrera_electrica', 'cadena', 'estatica_veloz', 'lana_electrica', 'agujas'), 2, {'velocidad': 0.04, 'energia': 0.12}),
    ('Dragones', 'los dragones solo respetan a otros dragones', ('salto_tiburon', 'guillotina', 'vuelo', 'dracoflechas', 'piel_tosca', 'mandibula'), 2, {'daño': 0.06}),
    ('Esporas y veneno', 'hongos, lodo y tinta: todo lo que tocan queda enfermo', ('espora', 'humo_toxico', 'glotoneria', 'tinta_toxica', 'baluarte', 'supersonico'), 2, {'enfriamiento': 0.06}),
    ('Paradojas', 'los que el tiempo trajo de donde no debía', None, 2, {'daño': 0.06, 'velocidad': 0.04}),
)
PARADOJAS = ('great_tusk', 'roaring_moon', 'iron_thorns', 'brute_bonnet')


def lazos_de(especies, tipos_de):
    """Los lazos que tiene este equipo: [(nombre, por que, {clave: valor})]. especies: los que estan en pie; tipos_de(especie) -> sus tipos."""
    especies = list(dict.fromkeys(especies))
    if len(especies) < 2: return []
    claves = {LINEAS.get(e, (None,))[0] for e in especies}
    tipos = [set(tipos_de(e)) for e in especies]
    salida = []
    for tipo, clave in RESONANCIA.items():                        # resonancia de tipo
        cuantos = sum(1 for t in tipos if tipo in t)
        if cuantos >= 2:
            fuerza = FUERZA_RESONANCIA[min(3, cuantos)] * (3 if clave == 'energia' else 1)
            salida.append(('Resonancia ' + tipo, str(cuantos) + ' pokemon de tipo ' + tipo, {clave: round(fuerza, 3)}))
    for nombre, motivo, lineas, hacen_falta, da in LAZOS:
        if nombre == 'Trío elemental': tiene = all(any(t in ts for ts in tipos) for t in ('fuego', 'agua', 'planta')) and len(especies) >= 3
        elif nombre == 'Paradojas': tiene = sum(1 for e in especies if e in PARADOJAS) >= hacen_falta
        else: tiene = len(claves & set(lineas)) >= hacen_falta
        if tiene: salida.append((nombre, motivo, dict(da)))
    return salida


NOMBRE_BONO = {'daño': 'daño', 'defensa': 'menos daño recibido', 'velocidad': 'velocidad', 'enfriamiento': 'recargas más rápidas', 'energia': 'energía'}


def _titulo(especie): return especie.replace('_', ' ').title()


def texto_bono(da):
    """'+6% daño, +4% velocidad' a partir de lo que da un lazo."""
    return ', '.join('+' + str(round(v * 100)) + '% ' + NOMBRE_BONO.get(c, c) for c, v in da.items())


def primera_de(clave):
    """El primer pokemon de la linea que tiene esa mecanica (Mudkip para 'barro'): con ese nombre se la reconoce."""
    return min((e for e, (c, _) in LINEAS.items() if c == clave), key=lambda e: (LINEAS[e][1], e), default=clave)


def miembros_lazo(nombre):
    """Quienes forman un lazo, en palabras: las lineas que cuentan (por su primer pokemon) y cuantas hacen falta."""
    lazo = next(l for l in LAZOS if l[0] == nombre)
    if nombre == 'Trío elemental': return 'uno de fuego, uno de agua y uno de planta (los tres en el equipo)'
    if nombre == 'Paradojas': return 'dos de: ' + ', '.join(_titulo(e) for e in PARADOJAS)
    lineas = [_titulo(primera_de(c)) for c in lazo[2]]
    if len(lineas) == lazo[3]: return ' y '.join(lineas) + ' (o sus evoluciones)'
    return str(lazo[3]) + ' de estas líneas: ' + ', '.join(lineas)


def lazos_posibles(especie, tipos):
    """Los lazos que este pokemon puede formar: [(nombre, con quien, lo que da)] (para su ficha y la pokedex)."""
    clave = LINEAS.get(especie, (None,))[0]
    salida = []
    for nombre, _, lineas, hacen_falta, da in LAZOS:
        if nombre == 'Trío elemental':
            if any(t in tipos for t in ('fuego', 'agua', 'planta')): salida.append((nombre, 'con los otros dos tipos del trío (fuego, agua, planta)', da))
        elif nombre == 'Paradojas':
            if especie in PARADOJAS: salida.append((nombre, 'con otra forma paradoja', da))
        elif clave in lineas:
            salida.append((nombre, 'con ' + ', '.join(_titulo(primera_de(c)) for c in lineas if c != clave), da))
    for t in tipos:
        if t in RESONANCIA: salida.append(('Resonancia ' + t, 'con otro de tipo ' + t, {RESONANCIA[t]: FUERZA_RESONANCIA[2] * (3 if RESONANCIA[t] == 'energia' else 1)}))
    return salida


def suma_lazos(lazos):
    """Todo lo que dan los lazos juntos, con el tope por cosa (la energia vale el triple, como en las sinergias)."""
    total = {}
    for _, _, da in lazos:
        for clave, valor in da.items(): total[clave] = total.get(clave, 0) + valor
    return {clave: round(min(valor, TOPE_LAZOS * (3 if clave == 'energia' else 1)), 3) for clave, valor in total.items()}


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
        if e.get('bloque_hasta') or e.get('baluarte_hasta'): j['atrapado_hasta'] = 0
        for k in ('ilusion_hasta', 'bajo_hasta', 'vuelo_hasta', 'prediccion_hasta', 'rodada_hasta', 'teledirigido', 'espada_hasta', 'escudo_hasta', 'marchas', 'calor',
                  'caparazon', 'bola', 'bloque_hasta', 'velo_hasta', 'velo_tocados', 'salto', 'carga_desde', 'baluarte_hasta', 'furia', 'lana', 'corrido',
                  'carrera', 'corte', 'explota', 'ola', 'blindado_hasta', 'doble', 'esquivando', 'martillo_salto'):
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
        if clave == 'furia': m *= 1 + 0.05 * e.get('furia', 0)
        if clave == 'carrera_electrica' and e.get('carrera') and e.get('carrera_hasta', 0) > T(): m *= 1 + e['carrera']
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
        if clave == 'escarcha' and contacto and random.random() < 0.25: poner_a(o, 'ralentizar', 2000)
        if clave == 'carrera_electrica' and e.get('carrera') and hecho: e.pop('carrera'); poner_a(o, 'paralizar', 800)
        if clave == 'lana_electrica' and e.get('lana', 0) >= 1 and hecho and c.mundo.get('nivel'):     # descarga la lana (se vacia antes: el area no la vuelve a disparar)
            e['lana'] = 0
            area(j, c.mundo['nivel'], o['rect'].center, 100 + 15 * etapa(j), 18 + 8 * etapa(j), 'electrico', 30, {'tipo': 'paralizar', 'duracion': 1200, 'probabilidad': 100})
            efecto_onda(c.mundo['nivel'], *o['rect'].center, 100 + 15 * etapa(j), 'electrico', 350)
        if j.get('ilusion_hasta', 0) > T(): termina_ilusion(j)

    def remate(j, nivel, tocados):
        """El tercer golpe del combo conecto."""
        clave = mec(j)[0]; e = estado(j)
        if clave == 'agujas':                                          # Jolteon: agujas en abanico
            c.lanzar(j, {'tipo': 'electrico', 'daño': daño(j, 10, 'electrico'), 'distancia': 300, 'area': 7, 'velocidad': 13, 'cantidad': 5,
                         'abanico': 50, 'retroceso': 4, 'efecto': {'tipo': 'paralizar', 'duracion': 800, 'probabilidad': 15}, 'jugador': True}, nivel['proyectiles_pokemon'])
        ahora = T(); et = etapa(j); px, py = j['rect'].center; ax, ay = j['aim']
        if clave == 'cadena' and tocados:                              # Shinx: el remate salta de enemigo en enemigo
            sin = list(tocados); x0, y0 = tocados[0]['rect'].center
            for _ in range(1 + et):
                cand = [o for o in enemigos_vivos(nivel) if o not in sin and math.hypot(o['rect'].centerx - x0, o['rect'].centery - y0) < 230]
                if not cand: break
                o = min(cand, key=lambda o: math.hypot(o['rect'].centerx - x0, o['rect'].centery - y0)); sin.append(o)
                golpear_a(j, o, 10 + 6 * et, 'electrico', 10, {'tipo': 'paralizar', 'duracion': 700, 'probabilidad': 40})
                nivel['efectos'].append({'x': x0, 'y': y0, 'linea': o['rect'].center, 'radio': 4, 'tipo': 'electrico', 'inicio': ahora, 'hasta': ahora + 220})
                x0, y0 = o['rect'].center
        if clave == 'barro':
            cosa(nivel, clase='barro', x=px + ax * 50, y=py + ay * 50, radio=55 + 15 * et, hasta=ahora + 4000, tick=0, veneno=False, daño=0)
        if clave == 'engranajes' and tocados:
            e['marchas'] = min(3, e.get('marchas', 0) + 1)
            c.poner_buff(j, 'velocidad', 1 + 0.08 * e['marchas'], 600000); c.poner_buff(j, 'enfriamiento', 1 - 0.08 * e['marchas'], 600000)

    def mult_enfriamiento_combo(j):
        return 0.75 if es(j, 'tecnico_veloz') else 1.0

    def mult_parry(j):
        if es(j, 'aura'): return 1.2 if etapa(j) == 1 else 1.4
        return 1.4 if mec(j)[0] in ('armadura_fosil', 'tajo_psiquico') else 1.0

    def al_parry(j, nivel, atacante=None):
        """Hiciste parry: Croagunk envenena, Aegislash pasa a escudo."""
        clave = mec(j)[0]; e = estado(j)
        if clave == 'punos_toxicos' and atacante: poner_a(atacante, 'veneno', 5000)
        if j['nombre'] == 'aegislash': e['escudo_hasta'] = T() + 5000; e.pop('espada_hasta', None); c.cartel(nivel, 'Modo escudo', 700)
        if j['nombre'] == 'lucario' and atacante:                      # Esfera Aural que persigue
            dx, dy = atacante['rect'].centerx - j['rect'].centerx, atacante['rect'].centery - j['rect'].centery; d = math.hypot(dx, dy) or 1
            cosa(nivel, clase='flecha', x=float(j['rect'].centerx), y=float(j['rect'].centery), vx=dx / d * 6, vy=dy / d * 6, hasta=T() + 2500,
                 daño=daño(j, 36, 'lucha'), golpeados=[], tipo='lucha')

    # ---------- golpes que recibis
    def recibido(j, cuanto, tipo, atacante=None, evitable=True):
        """Modifica el daño que le llega al jugador (antes de los buffs y la defensa). Devuelve el daño nuevo."""
        clave = mec(j)[0]; e = estado(j); ahora = T()
        t = c.normalizar_tipo(tipo) if tipo else None
        nivel = c.mundo.get('nivel')
        if e.get('bajo_hasta', 0) > ahora or e.get('vuelo_hasta', 0) > ahora: return 0      # bajo tierra / volando: no lo tocan
        if e.get('salto') or e.get('bloque_hasta', 0) > ahora: return 0                    # en el aire (picado, plancha) o adentro del hielo
        if e.get('baluarte_hasta', 0) > ahora and atacante and evitable and cuanto > 0:      # la cupula de puas castiga al que pega
            poner_a(atacante, 'veneno', 5000); atacante['vida'] = max(0, atacante['vida'] - atacante['max_vida'] * 0.06); atacante['golpe_flash'] = T()
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
        if e.get('caparazon'): m *= 0.15 if j['nombre'] == 'blastoise' else 0.2
        if e.get('baluarte_hasta', 0) > ahora: m *= 0.15
        if e.get('blindado_hasta', 0) > ahora: m *= 0.3
        if e.get('velo_hasta', 0) > ahora: m *= 0.5
        if clave == 'furia' and cuanto * m >= 1 and evitable:
            e['furia'] = min(2 + 2 * etapa(j), e.get('furia', 0) + 1); e['furia_hasta'] = ahora + 6000
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
        ahora = T(); nivel = c.mundo.get('nivel')
        if e.get('bola'): m *= 1.45 + 0.15 * etapa(j)
        if e.get('caparazon'): m *= 1.2
        if e.get('velo_hasta', 0) > ahora: m *= 1.35
        if e.get('carga_desde'): m *= 0.45
        if es(j, 'furia'): m *= 1 + 0.03 * e.get('furia', 0)
        if es(j, 'barro') and c.terreno_bajo(j) in ('agua', 'charco'): m *= 1.3
        if mec(j)[0] in ('barro', 'pantano') and nivel and en_cosa(nivel, j, 'barro'): m *= 1.4
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
        return e.get('bajo_hasta', 0) > ahora or e.get('vuelo_hasta', 0) > ahora or e.get('velo_hasta', 0) > ahora or bool(e.get('salto'))

    def invisible(j):
        """No se dibuja el sprite (bajo tierra)."""
        return estado(j).get('bajo_hasta', 0) > T()

    def altura_vuelo(j):
        e = estado(j); ahora = T()
        if e.get('salto'):                                             # picado, plancha, salto tiburon: una parabola
            s = e['salto']; k = min(1.0, (ahora - s['inicio']) / s['dura'])
            return round({'picado': 22, 'plancha': 46, 'tiburon': 28}.get(s['clase'], 24) * math.sin(math.pi * k))
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
        cuadro_nuevo(j, nivel, ahora, clave, et, e)
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
        if usar_nuevo(j, datos, nivel): return                         # las del juego original (caparazon, picado, llave...)
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
            c.poner_estado(j, 'aturdido', 1200)                        # el martillo pesa: queda aturdida un momento
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
            if cl in ('hueso', 'onda', 'chispa', 'llamas', 'nieve', 'barro', 'pinchos', 'premonicion', 'sustituto'):
                if cosa_nueva(j, nivel, x, ahora): cosas.remove(x)
                continue
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
                    c.recibir_ataque(o, {'tipo': x.get('tipo') or {'nube': 'veneno', 'charco': 'veneno', 'piedras': 'roca', 'agujero': 'psiquico', 'raices': 'planta', 'hojas': 'planta'}[cl],
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
                        tipo_f = x.get('tipo', 'dragon')
                        c.recibir_ataque(o, {'tipo': tipo_f, 'daño': x['daño'], 'retroceso': 25, 'jugador': True}, None)
                        x['golpeados'].append(o); c.efectos.golpe(c.mundo['ef'], x['x'], x['y'], (111, 53, 252) if tipo_f == 'dragon' else (90, 150, 255), tipo_f); x['hasta'] = ahora
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
            if dibujar_cosa_nueva(ventana, x, sx, sy, ahora): continue
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
                pygame.draw.circle(ventana, (140, 90, 250) if x.get('tipo', 'dragon') == 'dragon' else (70, 140, 255), (round(sx), round(sy)), 9)
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
        dibujar_jugador_nuevo(j, ventana, cx, cy)
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

    # ================= mecanicas de las lineas del juego original =================
    # Cambian como se mueve o pelea cada uno: modos (caparazon, bola), saltos, cargas, agarres, esquives especiales...

    def antes_de_atacar(j, nivel):
        """Metido en el caparazon o rodando como bola: atacar lo saca (y ese ataque no sale). Cargando el puño tampoco ataca. True: no atacar."""
        e = estado(j)
        if e.get('caparazon'): e.pop('caparazon'); c.cartel(nivel, 'Sale del caparazón', 500); return True
        if e.get('bola'): e.pop('bola'); c.cartel(nivel, 'Deja de rodar', 500); return True
        return bool(e.get('carga_desde'))

    def al_esquivar(j, nivel, costo):
        """Recien empezo un esquive (j['esquive'] ya esta armado): planeo, estela, sustituto, doble salto, esquive gratis..."""
        clave, et = mec(j); e = estado(j); esq = j.get('esquive'); ahora = T()
        if not esq: return
        if clave == 'globo': esq['restante'] *= 1.8; esq['hasta'] += 160
        if j['nombre'] == 'tinkaton':                                   # martillazo al piso: sale disparada y cae golpeando
            esq['restante'] *= 2.3; esq['hasta'] += 140; e['martillo_salto'] = True
            c.efectos.explosion(c.mundo['ef'], j['rect'].centerx - esq['vx'] * 26, j['rect'].centery - esq['vy'] * 26, 45); c.temblor(nivel, 90)
        if clave == 'bola_pinchos': esq['restante'] *= 1.25
        if clave == 'estatica_veloz':
            if j['nombre'] == 'raichu': esq['restante'] *= 1.4; esq['hasta'] += 60
            if j['nombre'] == 'pichu' and random.random() < 0.15:
                j['vida'] = max(1, j['vida'] - j['max_vida'] * 0.04); c.cartel(nivel, '¡Pichu se electrocutó solo!', 800)
        if clave == 'alas_vendaval' and j['vida'] >= j['max_vida'] * 0.75 and costo: j['energia'] = min(c.ENERGIA_MAX, j['energia'] + costo)
        if clave == 'patada_salto' and j['nombre'] == 'blaziken':
            if not e.get('doble'): j['esquive_listo'] = ahora + 90; e['doble'] = True        # el segundo sale enseguida
            else: e['doble'] = False
        if clave == 'sustituto':
            cosa(nivel, clase='sustituto', x=j['rect'].centerx, y=j['rect'].centery, radio=85, hasta=ahora + 1200, daño=daño(j, 16 + 8 * et, 'agua'))
            for o in enemigos_vivos(nivel):
                if math.hypot(o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery) < 300:
                    o['estado_ia'] = 'patrulla'; o['aviso'] = None; o['embestida_ia'] = None

    def al_esquive_perfecto(j, nivel):
        """Greninja: con un esquive perfecto aparece detras del enemigo mas cercano."""
        if j['nombre'] != 'greninja': return
        o = objetivo_cercano(j, nivel, 320)
        if not o: return
        dx, dy = o['rect'].centerx - j['rect'].centerx, o['rect'].centery - j['rect'].centery; d = math.hypot(dx, dy) or 1
        c.efectos.aparecer(c.mundo['ef'], *j['rect'].center)
        j['rect'].center = (round(o['rect'].centerx + dx / d * 50), round(o['rect'].centery + dy / d * 50)); c.mover_entidad(j, 0, 0, True)
        libre = c.entorno.orilla(c.mundo['ent'], j['rect'], j['tipos'])
        if libre: j['rect'].center = (round(libre[0]), round(libre[1]))
        j['aim'] = (-dx / d, -dy / d)
        c.cartel(nivel, '¡Greninja aparece por detrás!', 800)

    def disparo_basico(j, datos, nivel, indice):
        """Cubone y Marowak tiran su hueso (va y vuelve) en lugar del disparo comun. True si ya lo manejo."""
        if indice != 1 or not es(j, 'bumeran'): return False
        if any(x['clase'] == 'hueso' for x in nivel.get('mec_cosas', ())): return True     # el hueso todavia no volvio
        et = etapa(j); ax, ay = j['aim']
        cosa(nivel, clase='hueso', x=float(j['rect'].centerx), y=float(j['rect'].centery), vx=ax, vy=ay, vel=8 + 2 * et, ida=280 + 50 * et,
             recorrido=0.0, fase='ida', golpeados=[], hasta=T() + 6000, daño=round(datos.get('daño', 10) * 1.15), radio=16 + 4 * et, j=j)
        return True

    def al_caer(j, nivel):
        """El que pelea se quedo sin vida: Annihilape aguanta una vez por sala, Drifloon explota. True si sigue en pie."""
        clave = mec(j)[0]; e = estado(j)
        if j['nombre'] == 'annihilape' and not e.get('aguanto'):
            e['aguanto'] = True; j['vida'] = 1; j['inv_hasta'] = T() + 1000
            c.cartel(nivel, '¡Annihilape se niega a caer!', 1300); c.efectos.destello(c.mundo['ef'], *j['rect'].center)
            return True
        if clave == 'globo':
            area(j, nivel, j['rect'].center, 150, 40 + 12 * etapa(j), 'fantasma', 70)
            c.efectos.explosion(c.mundo['ef'], *j['rect'].center, 130); c.temblor(nivel, 250); c.cartel(nivel, '¡Detonación!', 900)
        return False

    def saltar(j, destino, ms, clase, **extra):
        """Salto o picada de un punto a otro (lo mueve cuadro), en el aire no lo tocan."""
        estado(j)['salto'] = dict({'desde': j['rect'].center, 'hasta': (round(destino[0]), round(destino[1])), 'inicio': T(), 'dura': ms,
                                   'clase': clase, 'golpeados': []}, **extra)
        j['embestida'] = None

    def actualizar_salto(j, nivel, e, ahora, et):
        s = e['salto']; k = min(1.0, (ahora - s['inicio']) / s['dura'])
        x = s['desde'][0] + (s['hasta'][0] - s['desde'][0]) * k; y = s['desde'][1] + (s['hasta'][1] - s['desde'][1]) * k
        j['rect'].center = (round(x), round(y)); c.mover_entidad(j, 0, 0, True)
        if s['clase'] == 'picado':                                       # pega a todo lo que cruza
            for o in c.objetivos_de(nivel, True):
                if o['vida'] > 0 and o not in s['golpeados'] and math.hypot(o['rect'].centerx - x, o['rect'].centery - y) < 40 + max(o['rect'].size) / 2:
                    s['golpeados'].append(o); golpear_a(j, o, 22 + 8 * et, 'volador', 35)
        if k < 1: return
        e.pop('salto'); px, py = j['rect'].center
        if s['clase'] == 'picado':
            c.efectos.polvo(c.mundo['ef'], px, py)
            if j['nombre'] == 'corviknight': e['blindado_hasta'] = ahora + 1000
        elif s['clase'] == 'plancha':
            encima = [o for o in enemigos_vivos(nivel) if math.hypot(o['rect'].centerx - px, o['rect'].centery - py) < 40]
            area(j, nivel, (px, py), 90, 34, 'lucha', 60, {'tipo': 'paralizar', 'duracion': 900, 'probabilidad': 100})
            for o in encima: golpear_a(j, o, 34, 'lucha', 0)
            c.efectos.explosion(c.mundo['ef'], px, py, 80); c.temblor(nivel, 180)
            if encima: c.cartel(nivel, '¡Plancha!', 600)
        elif s['clase'] == 'tiburon':
            o = s.get('objetivo')
            if o and o['vida'] > 0 and math.hypot(o['rect'].centerx - px, o['rect'].centery - py) < 80 + max(o['rect'].size) / 2:
                golpear_a(j, o, 30 + 10 * et, 'dragon', 40); c.efectos.golpe(c.mundo['ef'], *o['rect'].center, (111, 53, 252), 'dragon')
            else: area(j, nivel, (px, py), 60, 16 + 6 * et, 'dragon', 30)
            if s.get('rebotes', 0) > 0:
                nuevo = objetivo_cercano(j, nivel, 380, (o,) if o else ())
                if nuevo: saltar(j, nuevo['rect'].center, 300, 'tiburon', objetivo=nuevo, rebotes=s['rebotes'] - 1)

    def soltar_puño(j, nivel, e, ahora, et):
        """Golett/Golurk solto R: sale propulsado con la fuerza que junto."""
        k = min(1.0, (ahora - e.pop('carga_desde')) / (1400 if et == 1 else 900))
        c.iniciar_embestida(j, {'tipo': 'tierra', 'daño': daño(j, 18 + 50 * k + 8 * et, 'tierra', 'embestida'), 'distancia': 100 + 320 * k,
                                'velocidad': 10 + 12 * k, 'area': 26 + 10 * k, 'retroceso': 30 + 70 * k, 'forma': 'embestida', 'jugador': True})
        if k > 0.8: c.temblor(nivel, 160); c.cartel(nivel, '¡Puño a toda potencia!', 600)

    def actualizar_revoleado(nivel, o):
        """Un enemigo que revoleo Machop: vuela en linea, le pega a los que choca y al caer queda aturdido."""
        r = o['revoleado']; paso = min(16, r['restante']); antes = o['rect'].center
        c.mover_entidad(o, round(r['vx'] * paso), round(r['vy'] * paso))
        r['restante'] -= paso
        for otro in c.objetivos_de(nivel, True):
            if otro['vida'] > 0 and otro not in r['golpeados'] and otro['rect'].colliderect(o['rect'].inflate(16, 16)):
                r['golpeados'].append(otro); c.recibir_ataque(otro, {'tipo': 'lucha', 'daño': r['daño'], 'retroceso': 40, 'jugador': True}, None)
        if r['restante'] <= 0 or o['rect'].center == antes:
            o.pop('revoleado')
            c.recibir_ataque(o, {'tipo': 'lucha', 'daño': r['daño'], 'retroceso': 0, 'efecto': {'tipo': 'paralizar', 'duracion': 900, 'probabilidad': 100}, 'jugador': True}, None)
            c.efectos.explosion(c.mundo['ef'], *o['rect'].center, 50); c.temblor(nivel, 120)

    def tocando(j, nivel, margen=14):
        """Enemigos (y jefe) que estan tocando al jugador."""
        zona = j['rect'].inflate(margen, margen)
        return [o for o in c.objetivos_de(nivel, False) if o['vida'] > 0 and zona.colliderect(o['rect'])]

    def en_cosa(nivel, j, clase):
        ahora = T()
        return any(x['clase'] == clase and x['hasta'] > ahora and math.hypot(x['x'] - j['rect'].centerx, x['y'] - j['rect'].centery) < x['radio']
                   for x in nivel.get('mec_cosas', ()))

    def cuadro_nuevo(j, nivel, ahora, clave, et, e):
        """Lo que hacen solas cada cuadro las mecanicas de las lineas del juego original."""
        px, py = j['rect'].center
        if e.get('salto'): actualizar_salto(j, nivel, e, ahora, et)
        # ----- modos -----
        if e.get('caparazon'):
            for o in tocando(j, nivel, 20):
                if ahora >= o.get('mec_toque', 0): o['mec_toque'] = ahora + 500; golpear_a(j, o, 8 + 4 * et, 'agua', 50)
            if j['nombre'] == 'blastoise' and ahora >= e.get('prox_chorro', 0):          # gira tirando agua por los cañones
                e['prox_chorro'] = ahora + 350; guardado = j['aim']; ang = ahora / 300
                for k in range(2):
                    j['aim'] = (math.cos(ang + k * math.pi), math.sin(ang + k * math.pi))
                    c.lanzar(j, {'tipo': 'agua', 'daño': daño(j, 10, 'agua'), 'distancia': 260, 'area': 8, 'velocidad': 10, 'retroceso': 15, 'jugador': True},
                             nivel['proyectiles_pokemon'])
                j['aim'] = guardado
        if e.get('bola'):
            seg = min(4.0, (ahora - e['bola']) / 1000)
            for o in tocando(j, nivel, 10 + round(6 * seg)):
                if ahora >= o.get('mec_toque', 0): o['mec_toque'] = ahora + 600; golpear_a(j, o, 10 + 8 * seg + 4 * et, 'hielo', 40 + 10 * seg)
        if e.get('bloque_hasta') and ahora >= e['bloque_hasta']:
            e.pop('bloque_hasta')
            area(j, nivel, (px, py), 130, 34, 'hielo', 50, {'tipo': 'ralentizar', 'duracion': 2500, 'probabilidad': 100})
            c.efectos.explosion(c.mundo['ef'], px, py, 110); c.temblor(nivel, 150)
        if e.get('velo_hasta'):
            if ahora >= e['velo_hasta']: e.pop('velo_hasta'); e.pop('velo_tocados', None)
            else:
                j['oculto'] = True
                for o in tocando(j, nivel, 6):
                    if o not in e.setdefault('velo_tocados', []): e['velo_tocados'].append(o); poner_a(o, 'ralentizar', 2500); golpear_a(j, o, 14, 'hielo', 0)
        if e.get('baluarte_hasta'):
            if ahora >= e['baluarte_hasta']: e.pop('baluarte_hasta')
            elif j['nombre'] == 'toxapex' and nivel['frame'] % 30 == 0: j['vida'] = min(j['max_vida'], j['vida'] + j['max_vida'] * 0.01)
        # ----- esquives que hacen algo -----
        if j.get('esquive'):
            esq = j['esquive']; e['esquivando'] = True
            if clave in ('paso_helado', 'bola_pinchos'):
                for o in tocando(j, nivel, 16):
                    if o in esq.setdefault('cortados', []): continue
                    esq['cortados'].append(o)
                    if clave == 'paso_helado':
                        golpear_a(j, o, 14 + 8 * et, 'hielo', 10, {'tipo': 'ralentizar', 'duracion': 1800, 'probabilidad': 100})
                        if j['nombre'] == 'weavile' and not esq.get('recargado'): j['esquive_listo'] = ahora; esq['recargado'] = True
                    else: golpear_a(j, o, 12 + 8 * et, 'tierra', 30)
            if clave == 'bola_pinchos' and j['nombre'] == 'sandslash' and nivel['frame'] % 5 == 0:
                cosa(nivel, clase='pinchos', x=px, y=py, radio=26, hasta=ahora + 4000, tick=0, daño=daño(j, 8, 'tierra'))
            if clave == 'estatica_veloz' and nivel['frame'] % 2 == 0:
                cosa(nivel, clase='chispa', x=px, y=py, radio=20, hasta=ahora + 1200 + 300 * et, tick=0, daño=daño(j, 4 + 2 * et, 'electrico'))
            if clave == 'alas_vendaval' and et >= 2 and nivel['frame'] % 3 == 0:
                cosa(nivel, clase='llamas', x=px, y=py, radio=22, hasta=ahora + 1500, tick=0, daño=daño(j, 5 + 2 * et, 'fuego'))
        elif e.pop('esquivando', False):                                 # termino el esquive
            if e.pop('martillo_salto', False):
                area(j, nivel, (px, py), 80, 22, 'hada', 60, {'tipo': 'paralizar', 'duracion': 600, 'probabilidad': 100})
                c.efectos.explosion(c.mundo['ef'], px, py, 70); c.temblor(nivel, 140)
            if clave == 'patada_salto':
                area(j, nivel, (px, py), 70 + 10 * et, 12 + 6 * et, 'fuego', 40, {'tipo': 'quemar', 'duracion': 2000, 'probabilidad': 30})
                efecto_onda(nivel, px, py, 70 + 10 * et, 'fuego', 300)
        # ----- pasivas que juntan algo -----
        if clave == 'lana_electrica' and j['moviendose'] and e.get('lana', 0) < 1:
            e['lana'] = min(1.0, e.get('lana', 0) + (0.003 + 0.0015 * et) * (1.8 if j['corriendo'] else 1))
            if e['lana'] >= 1: c.cartel(nivel, 'Lana cargada: el próximo golpe descarga', 700)
        if clave == 'carrera_electrica':
            if j['corriendo']: e['corrido'] = e.get('corrido', 0) + 1000 / 60
            elif e.get('corrido'):
                e['carrera'] = min(0.5 if et == 1 else 0.8, e['corrido'] / 1000 * 0.3); e['corrido'] = 0; e['carrera_hasta'] = ahora + 1500
        if clave == 'manto_nieve' and j['moviendose'] and ahora >= e.get('prox_nieve', 0):
            e['prox_nieve'] = ahora + 220
            if sum(1 for x in nivel['mec_cosas'] if x['clase'] == 'nieve') < 30:
                cosa(nivel, clase='nieve', x=px, y=py + 8, radio=24 + 4 * et, hasta=ahora + 2500 + 1000 * et, tick=0)
        if clave == 'iman':                                              # los disparos se curvan hacia el enemigo mas cercano
            fuerza = 0.05 + 0.035 * et
            for p in nivel['proyectiles_pokemon']:
                o = min((o for o in enemigos_vivos(nivel) + ([nivel['jefe']] if nivel.get('jefe') and nivel['jefe']['vida'] > 0 else [])
                         if o not in p['golpeados'] and math.hypot(o['rect'].centerx - p['x'], o['rect'].centery - p['y']) < 360),
                        key=lambda o: math.hypot(o['rect'].centerx - p['x'], o['rect'].centery - p['y']), default=None)
                if not o: continue
                dx, dy = o['rect'].centerx - p['x'], o['rect'].centery - p['y']; d = math.hypot(dx, dy) or 1
                vx, vy = p['vx'] + dx / d * fuerza, p['vy'] + dy / d * fuerza; n = math.hypot(vx, vy) or 1
                p['vx'], p['vy'] = vx / n, vy / n
        if clave == 'furia' and e.get('furia') and ahora >= e.get('furia_hasta', 0): e['furia'] = 0
        # ----- especiales que siguen despues de usarlos -----
        if e.get('carga_desde') and (not c.mantiene('especial2') or ahora - e['carga_desde'] >= 2500): soltar_puño(j, nivel, e, ahora, et)
        if e.get('corte') and ahora >= e['corte']['hasta']:              # el tajo llega despues de pasar
            corte = e['corte']; hisui = j['nombre'] == 'samurott_hisui'
            for o in corte['golpeados']:
                if o['vida'] <= 0: continue
                golpear_a(j, o, 30 + 12 * et, 'siniestro' if hisui else 'agua', 20, {'tipo': 'veneno', 'duracion': 4000, 'probabilidad': 100} if hisui else None)
                nivel['efectos'].append({'x': o['rect'].left, 'y': o['rect'].top, 'linea': o['rect'].bottomright, 'radio': 5, 'tipo': 'agua', 'inicio': ahora, 'hasta': ahora + 200})
            if corte['veces'] > 1: corte['veces'] -= 1; corte['hasta'] = ahora + 180
            else: e.pop('corte')
        if e.get('explota') and not j['embestida']:
            e.pop('explota')
            area(j, nivel, (px, py), 80 + 25 * et, 26 + 14 * et, 'roca', 60)
            c.efectos.explosion(c.mundo['ef'], px, py, 70 + 25 * et); c.temblor(nivel, 150 + 50 * et)
            if j['nombre'] == 'golem': j['vida'] = max(1, j['vida'] - j['max_vida'] * 0.15)
        if e.get('ola'):
            if j['embestida']:                                            # arrastra a los que toca
                emb = j['embestida']
                for o in tocando(j, nivel, 50):
                    if not o.get('jefe'): c.mover_entidad(o, round(emb['vx'] * emb['velocidad']), round(emb['vy'] * emb['velocidad']))
            else: e.pop('ola'); area(j, nivel, (px, py), 90, 16, 'agua', 50)
        for o in nivel['enemigos']:
            if o.get('revoleado'): actualizar_revoleado(nivel, o)

    def usar_nuevo(j, datos, nivel):
        """Especiales de las lineas del juego original. True si era uno de estos."""
        clave = datos['mecanica']; et = datos.get('etapa', 1); ahora = T(); e = estado(j)
        px, py = j['rect'].center; ax, ay = j['aim']
        if clave == 'ola':
            c.iniciar_embestida(j, {'tipo': 'agua', 'daño': daño(j, 22 + 6 * et, 'agua', 'embestida'), 'distancia': 380, 'velocidad': 12, 'area': 40,
                                    'retroceso': 30, 'forma': 'embestida', 'jugador': True})
            e['ola'] = True
        elif clave == 'bloque_hielo':
            e['bloque_hasta'] = ahora + 1500; j['atrapado_hasta'] = ahora + 1500
        elif clave == 'velo_fantasma': e['velo_hasta'] = ahora + 2500; e['velo_tocados'] = []
        elif clave == 'bola_nieve': e['bola'] = ahora; c.cartel(nivel, 'Rueda (atacá o apretá R para parar)', 900)
        elif clave == 'picado': saltar(j, c.punto_apuntado(j, 260 + 60 * et), 420, 'picado')
        elif clave == 'plancha_voladora': saltar(j, c.punto_apuntado(j, 260), 600, 'plancha')
        elif clave == 'teletransporte':
            antes = (px, py); dest = c.punto_apuntado(j, 200 + 70 * et)
            j['rect'].center = (round(dest[0]), round(dest[1])); c.mover_entidad(j, 0, 0, True)
            libre = c.entorno.orilla(c.mundo['ent'], j['rect'], j['tipos'])
            if libre: j['rect'].center = (round(libre[0]), round(libre[1]))
            c.efectos.aparecer(c.mundo['ef'], *antes); c.efectos.aparecer(c.mundo['ef'], *j['rect'].center)
            if j['nombre'] == 'xatu': cosa(nivel, clase='premonicion', x=antes[0], y=antes[1], radio=110, hasta=ahora + 1000, daño=daño(j, 40, 'psiquico'))
        elif clave == 'rodar_explosivo':
            c.iniciar_embestida(j, {'tipo': 'roca', 'daño': daño(j, 14 + 6 * et, 'roca', 'embestida'), 'distancia': 280, 'velocidad': 13, 'area': 24,
                                    'retroceso': 30, 'forma': 'embestida', 'jugador': True})
            e['explota'] = True
        elif clave == 'pantano':
            dest = c.punto_apuntado(j, 300); veneno = j['nombre'] == 'clodsire'
            cosa(nivel, clase='barro', x=dest[0], y=dest[1], radio=90 + 15 * et, hasta=ahora + 6000, tick=0, veneno=veneno, daño=daño(j, 5, 'veneno') if veneno else 0)
        elif clave == 'salto_tiburon':
            o = objetivo_cercano(j, nivel, 420)
            if o: saltar(j, o['rect'].center, 350, 'tiburon', objetivo=o, rebotes=1 if j['nombre'] == 'garchomp' else 0)
            else: saltar(j, c.punto_apuntado(j, 220), 350, 'tiburon')
        elif clave == 'puño_propulsado': e['carga_desde'] = ahora
        elif clave == 'llave':
            cerca = sorted(cono(j, nivel, 110, 70), key=lambda o: math.hypot(o['rect'].centerx - px, o['rect'].centery - py))
            if not cerca: c.cartel(nivel, 'No hay nadie adelante para agarrar', 700); return True
            o = cerca[0]
            if o.get('jefe'): golpear_a(j, o, 40, 'lucha', 40); return True
            o['revoleado'] = {'vx': ax, 'vy': ay, 'restante': 220 + 70 * et, 'golpeados': [o], 'daño': daño(j, 20 + 8 * et, 'lucha', 'cuerpo')}
            poner_a(o, 'paralizar', 1500)
        elif clave == 'viga':
            for grados in ((0,) if et < 3 else (-12, 12)):
                r = math.radians(grados); vx, vy = ax * math.cos(r) - ay * math.sin(r), ax * math.sin(r) + ay * math.cos(r)
                cosa(nivel, clase='onda', x=px + vx * 40, y=py + vy * 40, vx=vx, vy=vy, restante=300 + 60 * et, hasta=ahora + 3000, prox=ahora,
                     daño=daño(j, (24 + 8 * et) * (0.7 if et >= 3 else 1), 'lucha'), golpeados=[], radio=46)   # las dos ondas de Conkeldurr pegan 70% cada una
            c.temblor(nivel, 120)
        elif clave == 'caparazon': e['caparazon'] = ahora; c.cartel(nivel, 'Adentro del caparazón (atacá o apretá R para salir)', 900)
        elif clave == 'baluarte':
            dura = 2000 if et == 1 else 3000
            e['baluarte_hasta'] = ahora + dura; j['atrapado_hasta'] = ahora + dura
        elif clave == 'corte_al_paso':
            vel, largo = 22, 240 + 40 * et
            c.iniciar_embestida(j, {'tipo': 'agua', 'daño': 1, 'distancia': largo, 'velocidad': vel, 'area': 26, 'retroceso': 0, 'forma': 'embestida', 'jugador': True})
            e['corte'] = {'hasta': ahora + largo / vel * 16.7 + 220, 'golpeados': j['embestida']['golpeados'], 'veces': 2 if et >= 3 else 1}
            j['inv_hasta'] = max(j.get('inv_hasta', 0), ahora + 250)
        elif clave == 'martillo':
            c.efectos.explosion(c.mundo['ef'], px - ax * 30, py - ay * 30, 50)
            c.iniciar_embestida(j, {'tipo': 'hada', 'daño': daño(j, 20 + 8 * et, 'hada', 'embestida'), 'distancia': 230 + 40 * et, 'velocidad': 20, 'area': 26,
                                    'retroceso': 50, 'forma': 'embestida', 'jugador': True})
        else: return False
        return True

    def cosa_nueva(j, nivel, x, ahora):
        """Lo que dejaron las mecanicas nuevas en la sala. True si la cosa ya se termino (hay que sacarla)."""
        cl = x['clase']
        if cl in ('premonicion', 'sustituto'):
            if ahora < x['hasta']: return False
            for o in c.objetivos_de(nivel, True):
                if o['vida'] > 0 and math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y']) < x['radio'] + max(o['rect'].size) / 2:
                    c.recibir_ataque(o, {'tipo': 'psiquico' if cl == 'premonicion' else 'agua', 'daño': x['daño'], 'retroceso': 30, 'jugador': True}, None)
            c.efectos.explosion(c.mundo['ef'], x['x'], x['y'], x['radio']); return True
        if ahora >= x['hasta']: return True
        if cl == 'hueso':
            if x['fase'] == 'ida':
                x['x'] += x['vx'] * x['vel']; x['y'] += x['vy'] * x['vel']; x['recorrido'] += x['vel']
                if x['recorrido'] >= x['ida']: x['fase'] = 'vuelta'; x['golpeados'] = []
            else:                                                       # vuelve a la mano
                dx, dy = j['rect'].centerx - x['x'], j['rect'].centery - x['y']; d = math.hypot(dx, dy) or 1
                if d < 26: return True
                x['x'] += dx / d * (x['vel'] + 2); x['y'] += dy / d * (x['vel'] + 2)
            for o in c.objetivos_de(nivel, True):
                if o['vida'] > 0 and o not in x['golpeados'] and math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y']) < x['radio'] + max(o['rect'].size) / 2:
                    x['golpeados'].append(o); c.recibir_ataque(o, {'tipo': 'tierra', 'daño': x['daño'], 'retroceso': 15, 'jugador': True}, None)
            return False
        if cl == 'onda':
            if ahora < x['prox']: return False
            x['prox'] = ahora + 60; x['x'] += x['vx'] * 38; x['y'] += x['vy'] * 38; x['restante'] -= 38
            c.efectos.polvo(c.mundo['ef'], x['x'], x['y'])
            for o in c.objetivos_de(nivel, True):
                if o['vida'] > 0 and o not in x['golpeados'] and math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y']) < x['radio'] + max(o['rect'].size) / 2:
                    x['golpeados'].append(o); c.recibir_ataque(o, {'tipo': 'lucha', 'daño': x['daño'], 'retroceso': 45, 'jugador': True}, None)
            return x['restante'] <= 0
        if cl in ('chispa', 'llamas', 'nieve', 'barro', 'pinchos') and ahora >= x.get('tick', 0):
            x['tick'] = ahora + 150
            for o in enemigos_vivos(nivel) + ([nivel['jefe']] if nivel.get('jefe') and nivel['jefe']['vida'] > 0 else []):
                if math.hypot(o['rect'].centerx - x['x'], o['rect'].centery - x['y']) > x['radio'] + max(o['rect'].size) / 2: continue
                marca = 'mec_rastro_' + cl                              # varios rastros encimados no suman: uno por clase cada medio segundo
                if ahora < o.get(marca, 0): continue
                o[marca] = ahora + 500
                if cl == 'nieve': poner_a(o, 'ralentizar', 1200); continue
                if cl == 'barro':
                    poner_a(o, 'ralentizar', 1500)
                    if not x.get('veneno'): continue
                tipo, efecto = {'pinchos': ('tierra', None), 'chispa': ('electrico', {'tipo': 'paralizar', 'duracion': 900, 'probabilidad': 100}),
                                'llamas': ('fuego', {'tipo': 'quemar', 'duracion': 2500, 'probabilidad': 40}),
                                'barro': ('veneno', {'tipo': 'veneno', 'duracion': 3000, 'probabilidad': 100})}[cl]
                c.recibir_ataque(o, {'tipo': tipo, 'daño': x['daño'], 'retroceso': 0, 'efecto': efecto, 'jugador': True}, None)
        return False

    def dibujar_cosa_nueva(ventana, x, sx, sy, ahora):
        cl = x['clase']
        if cl == 'nieve': circulo(ventana, sx, sy, x['radio'], (240, 248, 255), 70)
        elif cl == 'barro': circulo(ventana, sx, sy, x['radio'], (130, 70, 140) if x.get('veneno') else (120, 85, 50), 120)
        elif cl == 'chispa':
            circulo(ventana, sx, sy, x['radio'], (255, 230, 80), 60)
            if (ahora // 80) % 2: pygame.draw.circle(ventana, (255, 250, 200), (round(sx), round(sy)), 4)
        elif cl == 'llamas':
            circulo(ventana, sx, sy, x['radio'], (255, 120, 40), 90)
            pygame.draw.circle(ventana, (255, 220, 90), (round(sx), round(sy - 3 * math.sin(ahora / 90))), 6)
        elif cl == 'premonicion':
            k = max(0.0, (x['hasta'] - ahora) / 1000)
            circulo(ventana, sx, sy, x['radio'], (200, 120, 255), 40)
            pygame.draw.circle(ventana, (220, 150, 255), (round(sx), round(sy)), max(4, round(x['radio'] * k)), 3)
        elif cl == 'sustituto':
            circulo(ventana, sx, sy, 20, (120, 180, 255), 120)
            pygame.draw.circle(ventana, (200, 230, 255), (round(sx), round(sy)), 20, 2)
        elif cl == 'hueso':
            ang = ahora / 60; dx, dy = math.cos(ang) * 14, math.sin(ang) * 14
            pygame.draw.line(ventana, (240, 235, 215), (round(sx - dx), round(sy - dy)), (round(sx + dx), round(sy + dy)), 6)
            for s_ in (-1, 1): pygame.draw.circle(ventana, (250, 248, 235), (round(sx + dx * s_), round(sy + dy * s_)), 5)
        elif cl == 'pinchos':
            for k in range(3): pygame.draw.polygon(ventana, (190, 160, 110), [(sx - 12 + k * 10, sy + 8), (sx - 7 + k * 10, sy - 10), (sx - 2 + k * 10, sy + 8)])
        elif cl == 'onda':
            circulo(ventana, sx, sy, 30, (170, 130, 90), 120)
            for k in range(3): pygame.draw.polygon(ventana, (150, 140, 120), [(sx - 14 + k * 12, sy + 10), (sx - 8 + k * 12, sy - 16), (sx - 2 + k * 12, sy + 10)])
        else: return False
        return True

    def dibujar_jugador_nuevo(j, ventana, cx, cy):
        """Encima del jugador: caparazon, bola de nieve, bloque de hielo, cupula de puas, velo, carga del puño, lana y furia."""
        e = estado(j); ahora = T(); x, y = j['rect'].centerx - cx, j['rect'].centery - cy
        if e.get('caparazon'):
            circulo(ventana, x, y, 22, (150, 110, 60), 220)
            for k in range(3):
                a = ahora / 70 + k * 2.09
                pygame.draw.line(ventana, (90, 170, 230), (x, y), (round(x + math.cos(a) * 20), round(y + math.sin(a) * 20)), 3)
            pygame.draw.circle(ventana, (60, 40, 20), (x, y), 22, 2)
        if e.get('bola'):
            r = 18 + round(min(4.0, (ahora - e['bola']) / 1000) * 6)
            circulo(ventana, x, y, r, (245, 250, 255), 220)
            a = ahora / 60
            pygame.draw.circle(ventana, (200, 220, 240), (round(x + math.cos(a) * r * 0.5), round(y + math.sin(a) * r * 0.5)), 4)
        if e.get('bloque_hasta', 0) > ahora:
            caja = pygame.Surface((56, 56), pygame.SRCALPHA); caja.fill((170, 225, 255, 140)); ventana.blit(caja, (x - 28, y - 32))
            pygame.draw.rect(ventana, (230, 250, 255), (x - 28, y - 32, 56, 56), 2)
        if e.get('baluarte_hasta', 0) > ahora:
            circulo(ventana, x, y, 30, (170, 90, 200), 80)
            for k in range(10):
                a = k * 0.628
                pygame.draw.line(ventana, (230, 120, 220), (round(x + math.cos(a) * 26), round(y + math.sin(a) * 26)), (round(x + math.cos(a) * 36), round(y + math.sin(a) * 36)), 3)
        if e.get('velo_hasta', 0) > ahora: circulo(ventana, x, y, 26, (200, 220, 255), 70)
        if e.get('carga_desde'):
            k = min(1.0, (ahora - e['carga_desde']) / (1400 if etapa(j) == 1 else 900))
            pygame.draw.rect(ventana, (30, 30, 40), (x - 22, j['rect'].top - cy - 16, 44, 7))
            pygame.draw.rect(ventana, (255, 200, 60) if k < 1 else (255, 90, 60), (x - 22, j['rect'].top - cy - 16, round(44 * k), 7))
        if es(j, 'lana_electrica'):
            k = e.get('lana', 0)
            pygame.draw.rect(ventana, (40, 40, 30), (x - 20, j['rect'].bottom - cy + 6, 40, 4))
            pygame.draw.rect(ventana, (255, 230, 80) if k >= 1 and (ahora // 150) % 2 else (230, 200, 90), (x - 20, j['rect'].bottom - cy + 6, round(40 * k), 4))
        if e.get('furia'):
            for k in range(e['furia']): pygame.draw.circle(ventana, (255, 70, 50), (x - 21 + k * 6, j['rect'].top - cy - 8), 2)

    return SimpleNamespace(mec=mec, es=es, nueva_sala=nueva_sala, al_cambiar=al_cambiar, mult_golpe=mult_golpe, tras_golpe=tras_golpe, remate=remate,
                           mult_enfriamiento_combo=mult_enfriamiento_combo, mult_parry=mult_parry, al_parry=al_parry, recibido=recibido,
                           estado_puesto=estado_puesto, derrota=derrota, sala_limpia=sala_limpia, mult_romper=mult_romper, mult_iman=mult_iman,
                           mult_monedas=mult_monedas, objeto_roto=objeto_roto, aviso_mult=aviso_mult, regen_energia=regen_energia,
                           mult_velocidad=mult_velocidad, mult_recarga=mult_recarga, mult_recarga_especial=mult_recarga_especial,
                           ignora_solidos=ignora_solidos, invisible=invisible, altura_vuelo=altura_vuelo, cuadro=cuadro, lento=lento, usar=usar,
                           enemigo=enemigo, golpe_enemigo=golpe_enemigo, nubes_enemigas=nubes_enemigas, dibujar=dibujar, dibujar_hud=dibujar_hud,
                           termina_ilusion=termina_ilusion, antes_de_atacar=antes_de_atacar, al_esquivar=al_esquivar,
                           al_esquive_perfecto=al_esquive_perfecto, disparo_basico=disparo_basico, al_caer=al_caer)
