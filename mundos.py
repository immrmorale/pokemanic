"""
mundos.py - Las eras del juego (una por cada Regi), sus objetos, sus piezas armadas, el clima y el plan de salas de una partida.

    import mundos
    rec = mundos.nuevo_recorrido()          # plan entero de la partida
    mundos.tipo_sala(rec)                   # 'combate', 'tienda', 'jefe', 'regi' o 'final'
    mundos.destinos_siguientes(rec, azar)   # lo que muestran las puertas de la sala actual
    mundos.avanzar(rec)                     # pasa a la sala siguiente (False si se termino el juego)

Orden de las eras (la historia de la humanidad): Glaciacion (Regice), Edad de Piedra (Regirock), Edad de los Metales (Registeel),
Edad Media (Regidrago), Edad Moderna (Regieleki) y al final El Origen: Regigigas y despues Arceus.
"""

import random

SALAS_POR_ERA = 30
SALA_JEFE, SALA_REGI = 15, 30          # numero de sala (desde 1) del semijefe y del Regi
TIENDA_HUECO = (5, 10)                 # la tienda sale cada 5 a 10 salas
TIENDA_COMPENSA = 15                   # si sale pronto, la siguiente tarda mas: hueco_siguiente >= 15 - hueco_anterior
PUERTAS_POR_SALA = ((1, 20), (2, 50), (3, 30))   # (cantidad de salidas, peso) en las salas de combate
PROB_SEGUIR_CLIMA = 0.6                # chance de que la sala siguiente tenga el mismo clima

# terrenos: color, si bloquea el paso, que tipos lo cruzan igual y si frena proyectiles (solido)
TERRENOS = {
    'suelo': {'color': None, 'bloquea': False},
    'pared': {'color': None, 'bloquea': True, 'solido': True},
    'puerta': {'color': (120, 70, 30), 'bloquea': True, 'solido': True},
    'entrada': {'color': (60, 40, 25), 'bloquea': True, 'solido': True},
    'puente': {'color': (135, 95, 55), 'bloquea': False},
    'alfombra': {'color': (150, 40, 50), 'bloquea': False},
    'agua': {'color': (40, 105, 215), 'bloquea': True, 'pasan': ('agua', 'volador')},
    'charco': {'color': (100, 155, 225), 'bloquea': False},
    'hielo': {'color': (185, 232, 250), 'bloquea': False},
    'nieve': {'color': (240, 246, 252), 'bloquea': False},
    'hierba': {'color': (55, 145, 55), 'bloquea': False},
    'fuego': {'color': (240, 110, 30), 'bloquea': False},
    'ceniza': {'color': (75, 70, 65), 'bloquea': False},
    'arena': {'color': (222, 198, 132), 'bloquea': False},
    'lodo': {'color': (105, 78, 48), 'bloquea': False},
    'lava': {'color': (225, 60, 20), 'bloquea': True, 'pasan': ('fuego', 'dragon', 'volador')},
    'roca_volcanica': {'color': (58, 48, 48), 'bloquea': False},
    'toxico': {'color': (140, 60, 175), 'bloquea': False},
    'sombra': {'color': (28, 22, 40), 'bloquea': False},
    'aceite': {'color': (38, 36, 30), 'bloquea': False},
    'cable': {'color': (245, 225, 60), 'bloquea': False},
    'corriente': {'color': (205, 240, 255), 'bloquea': False},
    'cinta_n': {'color': (95, 95, 100), 'bloquea': False}, 'cinta_s': {'color': (95, 95, 100), 'bloquea': False},
    'cinta_e': {'color': (95, 95, 100), 'bloquea': False}, 'cinta_o': {'color': (95, 95, 100), 'bloquea': False},
    # maquinas: casillas solidas que ayudan a ciertos tipos si estas cerca (ver AURAS en entorno.py)
    'cascada': {'color': (120, 195, 255), 'bloquea': True, 'solido': True, 'maquina': True},
    'cascada_helada': {'color': (210, 245, 255), 'bloquea': True, 'solido': True, 'maquina': True},
    'fogata': {'color': (255, 140, 40), 'bloquea': True, 'solido': True, 'maquina': True},
    'fogata_apagada': {'color': (80, 70, 60), 'bloquea': True, 'solido': True, 'maquina': True},
    'brasero': {'color': (255, 150, 40), 'bloquea': True, 'solido': True, 'maquina': True},
    'brasero_apagado': {'color': (90, 80, 70), 'bloquea': True, 'solido': True, 'maquina': True},
    'forja': {'color': (230, 90, 30), 'bloquea': True, 'solido': True, 'maquina': True},
    'forja_apagada': {'color': (85, 65, 55), 'bloquea': True, 'solido': True, 'maquina': True},
    'horno': {'color': (200, 70, 30), 'bloquea': True, 'solido': True, 'maquina': True, 'pegado_a_pared': True},
    'horno_apagado': {'color': (80, 60, 55), 'bloquea': True, 'solido': True, 'maquina': True},
    'generador': {'color': (250, 210, 0), 'bloquea': True, 'solido': True, 'maquina': True},
    'generador_roto': {'color': (90, 85, 60), 'bloquea': True, 'solido': True, 'maquina': True},
    'altar': {'color': (230, 120, 200), 'bloquea': True, 'solido': True, 'maquina': True},
    'cristal_dragonico': {'color': (120, 60, 250), 'bloquea': True, 'solido': True, 'maquina': True},
    'iman': {'color': (170, 175, 200), 'bloquea': True, 'solido': True, 'maquina': True},
    'monolito': {'color': (150, 130, 90), 'bloquea': True, 'solido': True, 'maquina': True},
}

# objetos: tamaño en pixeles, material, vida (None = no se rompe), forma y color del dibujo provisorio
# extras: empujable (se desliza al golpearlo con lucha/psiquico o con una embestida), explota, arde (el fuego lo rompe de una),
# al_romper (terreno que deja), cobertura (sirve para cubrirse, se reparte alrededor del centro), solido False (se pasa por encima)
OBJETOS = {
    # era glacial
    'bloque_de_hielo': {'tam': (58, 58), 'material': 'hielo', 'vida': 45, 'color': (170, 225, 245), 'empujable': True, 'al_romper': 'charco', 'cobertura': True},
    'pino_nevado': {'tam': (64, 64), 'material': 'madera', 'vida': 90, 'forma': 'circulo', 'color': (40, 90, 70), 'arde': True, 'cobertura': True},
    'roca_nevada': {'tam': (62, 54), 'material': 'piedra', 'vida': 120, 'forma': 'circulo', 'color': (200, 210, 220), 'cobertura': True},
    'estalagmita_de_hielo': {'tam': (40, 40), 'material': 'hielo', 'vida': 35, 'forma': 'circulo', 'color': (200, 240, 255), 'al_romper': 'charco', 'cobertura': True},
    'hueso_de_mamut': {'tam': (70, 26), 'material': 'hueso', 'vida': 40, 'color': (235, 225, 200)},
    'craneo_de_mamut': {'tam': (74, 64), 'material': 'hueso', 'vida': 90, 'forma': 'circulo', 'color': (225, 215, 190), 'cobertura': True},
    'pila_de_pieles': {'tam': (48, 40), 'material': 'tela', 'vida': 15, 'color': (130, 95, 60), 'arde': True},
    # edad de piedra
    'tronco': {'tam': (64, 28), 'material': 'madera', 'vida': 30, 'color': (115, 75, 40), 'arde': True, 'empujable': True},
    'roca': {'tam': (58, 52), 'material': 'piedra', 'vida': 110, 'forma': 'circulo', 'color': (125, 120, 115), 'cobertura': True},
    'menhir': {'tam': (40, 50), 'material': 'piedra', 'vida': 180, 'color': (140, 135, 120), 'cobertura': True},
    'choza': {'tam': (100, 90), 'material': 'planta', 'vida': 70, 'forma': 'circulo', 'color': (170, 140, 80), 'arde': True},
    'lanza': {'tam': (14, 50), 'material': 'madera', 'vida': 8, 'color': (150, 110, 70), 'arde': True},
    'cesto': {'tam': (36, 36), 'material': 'planta', 'vida': 10, 'forma': 'circulo', 'color': (190, 160, 90), 'arde': True},
    'arbol': {'tam': (70, 70), 'material': 'madera', 'vida': 90, 'forma': 'circulo', 'color': (40, 110, 40), 'arde': True, 'cobertura': True},
    'arbusto': {'tam': (50, 44), 'material': 'planta', 'vida': 20, 'forma': 'circulo', 'color': (70, 140, 60), 'arde': True},
    'hueso': {'tam': (40, 20), 'material': 'hueso', 'vida': 10, 'color': (230, 225, 210), 'solido': False},
    # edad de los metales
    'yunque': {'tam': (50, 34), 'material': 'metal', 'vida': None, 'color': (70, 70, 80)},
    'armadura': {'tam': (40, 56), 'material': 'metal', 'vida': 70, 'color': (170, 140, 90), 'cobertura': True},
    'anfora': {'tam': (32, 40), 'material': 'ceramica', 'vida': 8, 'forma': 'circulo', 'color': (190, 110, 60)},
    'mesa_de_mercado': {'tam': (100, 44), 'material': 'madera', 'vida': 40, 'color': (150, 100, 55), 'arde': True},
    'columna': {'tam': (52, 52), 'material': 'piedra', 'vida': None, 'forma': 'circulo', 'color': (210, 200, 175), 'cobertura': True},
    'carro_de_bronce': {'tam': (100, 60), 'material': 'metal', 'vida': 110, 'color': (175, 120, 60)},
    'estatua_de_bronce': {'tam': (56, 66), 'material': 'metal', 'vida': 150, 'color': (180, 125, 60), 'cobertura': True},
    'lingotes': {'tam': (44, 30), 'material': 'metal', 'vida': 60, 'color': (200, 150, 70)},
    'caja': {'tam': (48, 48), 'material': 'madera', 'vida': 25, 'color': (175, 125, 70), 'empujable': True, 'arde': True, 'cobertura': True},
    'barril': {'tam': (46, 46), 'material': 'madera', 'vida': 30, 'forma': 'circulo', 'color': (140, 90, 45), 'empujable': True, 'arde': True, 'cobertura': True},
    # edad media
    'carreta': {'tam': (110, 66), 'material': 'madera', 'vida': 80, 'color': (120, 80, 40), 'arde': True, 'cobertura': True},
    'fardo_de_heno': {'tam': (60, 48), 'material': 'planta', 'vida': 18, 'color': (225, 195, 90), 'arde': True},
    'barril_de_polvora': {'tam': (44, 44), 'material': 'madera', 'vida': 12, 'forma': 'circulo', 'color': (60, 40, 30), 'explota': True},
    'estatua_de_caballero': {'tam': (58, 70), 'material': 'piedra', 'vida': 160, 'color': (150, 150, 145), 'cobertura': True},
    'lapida': {'tam': (40, 50), 'material': 'piedra', 'vida': 60, 'color': (120, 120, 120)},
    'pozo': {'tam': (76, 76), 'material': 'piedra', 'vida': None, 'forma': 'circulo', 'color': (110, 105, 100), 'cobertura': True},
    'valla': {'tam': (78, 20), 'material': 'madera', 'vida': 25, 'color': (150, 110, 60), 'arde': True},
    'estandarte': {'tam': (30, 60), 'material': 'tela', 'vida': 15, 'color': (170, 30, 40), 'arde': True},
    'escamas_de_dragon': {'tam': (46, 36), 'material': 'piedra', 'vida': 50, 'color': (110, 70, 200)},
    # edad moderna (revolucion industrial hasta hoy)
    'caja_de_carbon': {'tam': (50, 50), 'material': 'madera', 'vida': 35, 'color': (55, 45, 40), 'empujable': True, 'arde': True, 'cobertura': True},
    'barril_de_petroleo': {'tam': (44, 44), 'material': 'metal', 'vida': 20, 'forma': 'circulo', 'color': (30, 30, 30), 'explota': True, 'al_romper': 'aceite'},
    'engranaje': {'tam': (80, 80), 'material': 'metal', 'vida': 200, 'forma': 'circulo', 'color': (130, 110, 80), 'cobertura': True},
    'chatarra': {'tam': (60, 50), 'material': 'metal', 'vida': 70, 'color': (110, 90, 75), 'cobertura': True},
    'vagoneta': {'tam': (60, 50), 'material': 'metal', 'vida': 90, 'color': (90, 70, 60), 'empujable': True},
    'tuberia': {'tam': (120, 30), 'material': 'metal', 'vida': 80, 'color': (100, 110, 100)},
    'auto': {'tam': (120, 64), 'material': 'metal', 'vida': 150, 'color': (190, 40, 40), 'cobertura': True},
    'poste_de_luz': {'tam': (26, 26), 'material': 'metal', 'vida': 60, 'forma': 'circulo', 'color': (80, 80, 90)},
    'bolsa_de_basura': {'tam': (38, 38), 'material': 'basura', 'vida': 8, 'forma': 'circulo', 'color': (25, 25, 25)},
    'contenedor': {'tam': (90, 54), 'material': 'metal', 'vida': 120, 'color': (40, 110, 60), 'empujable': True, 'cobertura': True},
    'hidrante': {'tam': (30, 30), 'material': 'metal', 'vida': 40, 'forma': 'circulo', 'color': (220, 40, 30), 'al_romper': 'charco'},
    'maquina_expendedora': {'tam': (54, 44), 'material': 'vidrio', 'vida': 40, 'color': (60, 120, 210)},
    'banco_de_plaza': {'tam': (90, 30), 'material': 'madera', 'vida': 35, 'color': (130, 90, 50), 'arde': True},
    'cabina_telefonica': {'tam': (50, 50), 'material': 'vidrio', 'vida': 45, 'color': (200, 30, 30), 'cobertura': True},
    'tacho_de_basura': {'tam': (36, 36), 'material': 'basura', 'vida': 20, 'forma': 'circulo', 'color': (110, 120, 110), 'empujable': True},
    # el origen
    'pilar_de_cristal': {'tam': (50, 50), 'material': 'vidrio', 'vida': 90, 'color': (200, 150, 255), 'cobertura': True},
    'columna_rota': {'tam': (56, 46), 'material': 'piedra', 'vida': 120, 'forma': 'circulo', 'color': (190, 180, 210), 'cobertura': True},
    'estatua_de_titan': {'tam': (80, 90), 'material': 'piedra', 'vida': None, 'color': (160, 150, 190)},
    # tienda (no se rompen)
    'estante': {'tam': (360, 50), 'material': 'madera', 'vida': None, 'color': (110, 70, 40)},
    'mostrador': {'tam': (130, 34), 'material': 'madera', 'vida': None, 'color': (140, 95, 55)},
    'kecleon': {'tam': (46, 46), 'material': 'tela', 'vida': None, 'forma': 'circulo', 'color': (120, 200, 90)},
    'mesa': {'tam': (110, 50), 'material': 'madera', 'vida': None, 'color': (125, 85, 50)},
    'maceta': {'tam': (40, 40), 'material': 'planta', 'vida': None, 'forma': 'circulo', 'color': (60, 150, 70)},
}

# piezas armadas a mano (como los "chunks" de Spelunky): se rotan, se espejan y se ubican donde entren
# '.' no importa, '_' tiene que quedar libre, el resto sale de LEYENDA_BASE o de la leyenda de la pieza (objeto, terreno o maquina)
LEYENDA_BASE = {'~': 'agua', '"': 'hierba', ',': 'nieve', 's': 'sombra', '=': 'puente', 'c': 'charco', 'i': 'hielo', 'a': 'arena', 'k': 'cable'}
PIEZAS = {
    # glaciacion
    'campamento helado': {'mapa': ['_p_', 'pFp', '_p_'], 'leyenda': {'F': 'fogata', 'p': 'pila_de_pieles'}},
    'esqueleto de mamut': {'mapa': ['h.h', '.C.', 'h.h'], 'leyenda': {'C': 'craneo_de_mamut', 'h': 'hueso_de_mamut'}},
    'bloques de hielo': {'mapa': ['cbc', 'b.b', 'cbc'], 'leyenda': {'b': 'bloque_de_hielo'}},
    'pinar nevado': {'mapa': [',P,', 'P,P', ',P,'], 'leyenda': {'P': 'pino_nevado'}},
    'estalagmitas': {'mapa': ['e.e', '...', 'e.e'], 'leyenda': {'e': 'estalagmita_de_hielo'}},
    # edad de piedra
    'fogata': {'mapa': ['.t.', 'tFt', '.t.'], 'leyenda': {'F': 'fogata', 't': 'tronco'}},
    'circulo de piedras': {'mapa': ['.m.m.', 'm___m', '._M_.', 'm___m', '.m.m.'], 'leyenda': {'m': 'menhir', 'M': 'monolito'}},
    'choza': {'mapa': ['lC', 'pc'], 'leyenda': {'C': 'choza', 'l': 'lanza', 'p': 'pila_de_pieles', 'c': 'cesto'}},
    'arboleda': {'mapa': ['"A"', 'A"A', '"A"'], 'leyenda': {'A': 'arbol'}},
    'rocas': {'mapa': ['R.R'], 'leyenda': {'R': 'roca'}},
    # edad de los metales
    'herreria': {'mapa': ['aFy', '_l_'], 'leyenda': {'F': 'forja', 'a': 'armadura', 'y': 'yunque', 'l': 'lingotes'}},
    'puesto de mercado': {'mapa': ['oM.o'], 'leyenda': {'M': 'mesa_de_mercado', 'o': 'anfora'}},
    'columnata': {'mapa': ['C.C.C'], 'leyenda': {'C': 'columna'}},
    'carga de bronce': {'mapa': ['xK.x'], 'leyenda': {'K': 'carro_de_bronce', 'x': 'caja'}},
    'estatua': {'mapa': ['_._', '_E_'], 'leyenda': {'E': 'estatua_de_bronce'}},
    # edad media
    'polvorin': {'mapa': ['bbB'], 'leyenda': {'b': 'barril', 'B': 'barril_de_polvora'}},
    'cementerio': {'mapa': ['l.l.l', 'sssss', 'l.l.l'], 'leyenda': {'l': 'lapida'}},
    'establo': {'mapa': ['vvv', 'f.f'], 'leyenda': {'v': 'valla', 'f': 'fardo_de_heno'}},
    'santuario del dragon': {'mapa': ['e.e', '.D.', 'e.e'], 'leyenda': {'D': 'cristal_dragonico', 'e': 'escamas_de_dragon'}},
    'campamento': {'mapa': ['b.b', '_F_'], 'leyenda': {'F': 'brasero', 'b': 'barril'}},
    # edad moderna
    'esquina': {'mapa': ['PtB'], 'leyenda': {'P': 'poste_de_luz', 't': 'tacho_de_basura', 'B': 'bolsa_de_basura'}},
    'estacionamiento': {'mapa': ['A..A..'], 'leyenda': {'A': 'auto'}},
    'obra': {'mapa': ['vxv', '.R.'], 'leyenda': {'v': 'valla', 'x': 'caja_de_carbon', 'R': 'barril_de_petroleo'}},
    'subestacion': {'mapa': ['kGk'], 'leyenda': {'G': 'generador'}},
    'fuente': {'mapa': ['h~~h', '.~~.'], 'leyenda': {'h': 'hidrante'}},
    # el origen
    'santuario': {'mapa': ['p.p', '.L.', 'p.p'], 'leyenda': {'L': 'altar', 'p': 'pilar_de_cristal'}},
    'ruinas': {'mapa': ['c.c'], 'leyenda': {'c': 'columna_rota'}},
}

# climas posibles y con cuales se conectan (asi no pasa de lluvia a sol de una sala a la otra)
VECINOS_CLIMA = {
    'despejado': ('sol', 'nublado', 'tormenta_arena'), 'sol': ('despejado', 'tormenta_arena'), 'nublado': ('despejado', 'lluvia', 'niebla', 'nieve'),
    'lluvia': ('nublado', 'tormenta_electrica'), 'tormenta_electrica': ('lluvia',), 'niebla': ('nublado',),
    'nieve': ('nublado', 'granizo'), 'granizo': ('nieve',), 'tormenta_arena': ('despejado', 'sol'),
}

# cada era: su Regi, el semijefe de la sala 15, colores, enemigos, que tan seguido sale cada clima y las variantes de sala
# formato de una variante:
#   'forma': {silueta: peso}  ('rect', 'esquinas', 'cruz', 'columnas', 'cueva')     'simetria': {modo: peso}  ('no', 'h', 'v', 'hv')
#   'piezas': {pieza: peso}  'num_piezas': (min, max)                            'interior': True si no le llega el clima
#   'terrenos': [(terreno, (min, max) manchas, (min, max) casillas)]             'maquinas': [(maquina, (min, max))]
#   'especiales': ['rio', 'foso', 'costa', 'cintas', 'cables']                  'objetos': {objeto: peso} sueltos, 'cantidad': (min, max)
ERAS = [
    {'clave': 'glaciacion', 'nombre': 'Era Glacial', 'regi': 'regice', 'jefe': 'walrein',
     'suelo': (196, 222, 236), 'pared': (85, 115, 140), 'clima_regi': 'granizo',
     'clima': {'nieve': 4, 'granizo': 2, 'nublado': 2, 'despejado': 1, 'niebla': 1},
     'enemigos': ['snorunt', 'glalie', 'froslass', 'spheal', 'sealeo', 'walrein', 'vanillite', 'vanillish', 'vanilluxe', 'sneasel',
                  'weavile', 'lapras', 'squirtle', 'wartortle'],
     'variantes': {
         'glaciar': {'forma': {'rect': 2, 'esquinas': 2}, 'simetria': {'no': 2, 'h': 1}, 'terrenos': [('hielo', (2, 4), (8, 16)), ('nieve', (2, 3), (6, 12))],
                     'piezas': {'bloques de hielo': 2, 'estalagmitas': 1}, 'num_piezas': (1, 3), 'objetos': {'roca_nevada': 2, 'bloque_de_hielo': 2}, 'cantidad': (3, 6)},
         'lago congelado': {'forma': {'esquinas': 2, 'rect': 1}, 'especiales': ['laguna'], 'terrenos': [('hielo', (1, 2), (6, 10)), ('nieve', (1, 3), (4, 8))],
                            'piezas': {'pinar nevado': 2, 'bloques de hielo': 1}, 'num_piezas': (1, 2), 'objetos': {'pino_nevado': 2, 'roca_nevada': 1}, 'cantidad': (3, 6)},
         'tundra': {'forma': {'rect': 2, 'cruz': 1}, 'simetria': {'no': 1, 'hv': 1}, 'terrenos': [('nieve', (3, 5), (8, 16))], 'maquinas': [('cascada', (0, 1))],
                    'piezas': {'esqueleto de mamut': 2, 'pinar nevado': 2, 'campamento helado': 1}, 'num_piezas': (2, 3), 'objetos': {'pino_nevado': 3, 'roca_nevada': 2}, 'cantidad': (3, 7)},
         'cueva de hielo': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('sombra', (2, 3), (5, 10)), ('hielo', (2, 3), (5, 10))], 'maquinas': [('cascada', (1, 2))],
                            'piezas': {'estalagmitas': 3, 'campamento helado': 1}, 'num_piezas': (1, 3), 'objetos': {'estalagmita_de_hielo': 3, 'bloque_de_hielo': 1}, 'cantidad': (2, 5)},
         'grieta': {'forma': {'rect': 1, 'esquinas': 1}, 'especiales': ['rio'], 'terrenos': [('nieve', (2, 3), (5, 10)), ('hielo', (1, 2), (4, 8))],
                    'piezas': {'bloques de hielo': 1, 'esqueleto de mamut': 1}, 'num_piezas': (1, 2), 'objetos': {'roca_nevada': 2, 'estalagmita_de_hielo': 2}, 'cantidad': (3, 6)},
     },
     'arena': {'forma': {'esquinas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('hielo', (3, 4), (8, 12)), ('nieve', (1, 2), (5, 8))], 'maquinas': [('cascada', (2, 2))],
               'piezas': {'estalagmitas': 1}, 'num_piezas': (1, 1), 'objetos': {}, 'cantidad': (0, 0)}},

    {'clave': 'piedra', 'nombre': 'Edad de Piedra', 'regi': 'regirock', 'jefe': 'golem',
     'suelo': (150, 130, 95), 'pared': (70, 55, 40), 'clima_regi': 'tormenta_arena',
     'clima': {'despejado': 3, 'sol': 2, 'nublado': 2, 'lluvia': 2, 'tormenta_electrica': 0.5, 'niebla': 1, 'tormenta_arena': 1},
     'enemigos': ['geodude', 'graveler', 'golem', 'sandshrew', 'sandslash', 'cubone', 'marowak', 'mankey', 'primeape', 'timburr',
                  'chikorita', 'riolu', 'torchic', 'wooper', 'quagsire'],
     'variantes': {
         'pradera': {'forma': {'rect': 2, 'esquinas': 1}, 'simetria': {'no': 2, 'h': 1}, 'terrenos': [('hierba', (3, 5), (6, 14))],
                     'piezas': {'arboleda': 3, 'rocas': 2, 'fogata': 1}, 'num_piezas': (2, 4), 'objetos': {'arbusto': 3, 'roca': 2, 'arbol': 2}, 'cantidad': (3, 7)},
         'aldea de cazadores': {'forma': {'rect': 1, 'cruz': 1}, 'terrenos': [('hierba', (1, 2), (4, 8)), ('lodo', (1, 2), (3, 6))],
                                'piezas': {'choza': 3, 'fogata': 2, 'rocas': 1}, 'num_piezas': (3, 4), 'objetos': {'cesto': 2, 'tronco': 2, 'lanza': 1}, 'cantidad': (2, 5)},
         'cueva rupestre': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('sombra', (3, 5), (5, 10))],
                            'piezas': {'fogata': 2, 'rocas': 2}, 'num_piezas': (1, 3), 'objetos': {'roca': 3, 'hueso': 2}, 'cantidad': (3, 6)},
         'circulo de piedras': {'forma': {'esquinas': 1, 'rect': 1}, 'simetria': {'hv': 2, 'h': 1}, 'terrenos': [('hierba', (2, 3), (5, 10))],
                                'piezas': {'circulo de piedras': 3, 'rocas': 1}, 'num_piezas': (1, 2), 'objetos': {'menhir': 2, 'arbusto': 2}, 'cantidad': (2, 4)},
         'valle volcanico': {'forma': {'rect': 1, 'esquinas': 1}, 'terrenos': [('lava', (1, 3), (3, 6)), ('roca_volcanica', (2, 3), (4, 8)), ('ceniza', (1, 2), (4, 8))],
                             'piezas': {'rocas': 2}, 'num_piezas': (1, 2), 'objetos': {'roca': 3, 'hueso': 1}, 'cantidad': (3, 6)},
         'rio': {'forma': {'rect': 1}, 'especiales': ['rio'], 'terrenos': [('hierba', (2, 4), (5, 10)), ('lodo', (1, 2), (3, 6))],
                 'piezas': {'arboleda': 2, 'choza': 1}, 'num_piezas': (1, 3), 'objetos': {'arbol': 2, 'arbusto': 2, 'roca': 1}, 'cantidad': (3, 6)},
     },
     'arena': {'forma': {'esquinas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('arena', (3, 4), (6, 10))], 'maquinas': [('monolito', (2, 2))],
               'piezas': {'rocas': 1}, 'num_piezas': (2, 2), 'objetos': {}, 'cantidad': (0, 0)}},

    {'clave': 'metales', 'nombre': 'Edad de los Metales', 'regi': 'registeel', 'jefe': 'corviknight',
     'suelo': (176, 132, 82), 'pared': (70, 45, 25), 'clima_regi': 'sol',
     'clima': {'despejado': 3, 'sol': 3, 'nublado': 2, 'tormenta_arena': 2, 'lluvia': 1},
     'enemigos': ['magnemite', 'magneton', 'machop', 'machoke', 'machamp', 'gurdurr', 'conkeldurr', 'combusken', 'blaziken', 'fletchling',
                  'fletchinder', 'talonflame', 'corvisquire', 'lucario', 'mareanie'],
     'variantes': {
         'forja': {'forma': {'rect': 2, 'columnas': 1}, 'interior': True, 'terrenos': [('ceniza', (1, 3), (4, 8))], 'maquinas': [('iman', (0, 1))],
                   'piezas': {'herreria': 3, 'carga de bronce': 1}, 'num_piezas': (2, 3), 'objetos': {'lingotes': 2, 'armadura': 2, 'caja': 1}, 'cantidad': (2, 5)},
         'mina de cobre': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('sombra', (2, 4), (5, 10)), ('lodo', (1, 2), (3, 6))],
                           'piezas': {'carga de bronce': 2}, 'num_piezas': (1, 2), 'objetos': {'lingotes': 2, 'caja': 2, 'barril': 1}, 'cantidad': (3, 6)},
         'mercado': {'forma': {'cruz': 2, 'rect': 1}, 'simetria': {'h': 1, 'v': 1, 'no': 1}, 'terrenos': [('arena', (1, 2), (4, 8))],
                     'piezas': {'puesto de mercado': 3, 'estatua': 1, 'carga de bronce': 1}, 'num_piezas': (3, 4), 'objetos': {'anfora': 3, 'caja': 2, 'barril': 2}, 'cantidad': (3, 6)},
         'templo de bronce': {'forma': {'columnas': 2, 'rect': 1}, 'simetria': {'hv': 2, 'h': 1}, 'maquinas': [('brasero', (2, 2))],
                              'piezas': {'columnata': 2, 'estatua': 2}, 'num_piezas': (2, 3), 'objetos': {'anfora': 2, 'armadura': 1}, 'cantidad': (2, 4)},
         'puerto antiguo': {'forma': {'rect': 1}, 'especiales': ['costa'], 'terrenos': [('arena', (2, 3), (4, 8))],
                            'piezas': {'carga de bronce': 2, 'puesto de mercado': 1}, 'num_piezas': (1, 3), 'objetos': {'anfora': 3, 'barril': 2, 'caja': 2}, 'cantidad': (3, 6)},
     },
     'arena': {'forma': {'columnas': 1}, 'simetria': {'hv': 1}, 'maquinas': [('iman', (2, 2)), ('forja', (1, 1))], 'piezas': {'estatua': 1}, 'num_piezas': (1, 1), 'objetos': {}, 'cantidad': (0, 0)}},

    {'clave': 'medieval', 'nombre': 'Edad Media', 'regi': 'regidrago', 'jefe': 'garchomp',
     'suelo': (128, 112, 88), 'pared': (52, 42, 32), 'clima_regi': 'tormenta_electrica',
     'clima': {'nublado': 3, 'lluvia': 3, 'niebla': 2, 'despejado': 2, 'tormenta_electrica': 1, 'sol': 1},
     'enemigos': ['gible', 'gabite', 'golett', 'golurk', 'samurott_hisui', 'oshawott', 'dewott', 'samurott', 'rookidee', 'drifloon',
                  'drifblim', 'natu', 'xatu', 'hawlucha', 'froakie', 'frogadier'],
     'variantes': {
         'patio del castillo': {'forma': {'rect': 2, 'columnas': 1}, 'simetria': {'h': 2, 'hv': 1, 'no': 1}, 'terrenos': [('arena', (1, 2), (5, 10))], 'maquinas': [('brasero', (2, 4))],
                                'piezas': {'polvorin': 2, 'campamento': 2}, 'num_piezas': (2, 3), 'objetos': {'estatua_de_caballero': 2, 'estandarte': 2, 'carreta': 1, 'caja': 2}, 'cantidad': (3, 6)},
         'bosque encantado': {'forma': {'rect': 1, 'esquinas': 2}, 'especiales': ['rio'], 'terrenos': [('hierba', (3, 5), (6, 14)), ('lodo', (0, 2), (3, 6))], 'maquinas': [('altar', (0, 1))],
                              'piezas': {'arboleda': 3}, 'num_piezas': (2, 3), 'objetos': {'arbol': 3, 'arbusto': 3}, 'cantidad': (3, 7)},
         'aldea': {'forma': {'rect': 1, 'cruz': 1}, 'terrenos': [('hierba', (1, 2), (4, 8)), ('lodo', (1, 2), (4, 8)), ('charco', (0, 2), (2, 4))],
                   'piezas': {'establo': 3, 'campamento': 1}, 'num_piezas': (2, 4), 'objetos': {'carreta': 2, 'barril': 2, 'pozo': 1}, 'cantidad': (2, 5)},
         'mazmorra': {'forma': {'columnas': 1, 'cruz': 1}, 'interior': True, 'simetria': {'hv': 1, 'no': 1}, 'terrenos': [('sombra', (3, 5), (6, 12)), ('charco', (1, 2), (2, 5))],
                      'maquinas': [('brasero', (2, 4))], 'piezas': {'cementerio': 2, 'polvorin': 1}, 'num_piezas': (1, 3), 'objetos': {'barril': 2, 'caja': 2}, 'cantidad': (2, 5)},
         'foso del castillo': {'forma': {'rect': 1}, 'especiales': ['foso'], 'simetria': {'hv': 1}, 'maquinas': [('brasero', (2, 4))],
                               'piezas': {'polvorin': 1}, 'num_piezas': (0, 1), 'objetos': {'barril': 2, 'estandarte': 2, 'estatua_de_caballero': 1}, 'cantidad': (3, 6)},
         'guarida del dragon': {'forma': {'cueva': 1}, 'interior': True, 'terrenos': [('lava', (1, 2), (3, 6)), ('roca_volcanica', (2, 3), (4, 8))],
                                'piezas': {'santuario del dragon': 2}, 'num_piezas': (1, 2), 'objetos': {'escamas_de_dragon': 3, 'roca': 2}, 'cantidad': (3, 6)},
     },
     'arena': {'forma': {'esquinas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('roca_volcanica', (2, 3), (4, 8))], 'maquinas': [('cristal_dragonico', (2, 2)), ('brasero', (2, 2))],
               'piezas': {}, 'num_piezas': (0, 0), 'objetos': {}, 'cantidad': (0, 0)}},

    {'clave': 'moderna', 'nombre': 'Edad Moderna', 'regi': 'regieleki', 'jefe': 'magnezone',
     'suelo': (70, 78, 122), 'pared': (24, 24, 44), 'clima_regi': 'tormenta_electrica',
     'clima': {'nublado': 3, 'lluvia': 2, 'niebla': 2, 'tormenta_electrica': 2, 'despejado': 2, 'sol': 1},
     'enemigos': ['pichu', 'pikachu', 'raichu', 'mareep', 'flaaffy', 'ampharos', 'shinx', 'luxio', 'luxray', 'electrike',
                  'manectric', 'magneton', 'toxapex', 'clodsire', 'greninja', 'annihilape'],
     'variantes': {
         'fabrica': {'forma': {'rect': 1, 'columnas': 1}, 'interior': True, 'especiales': ['cintas'], 'terrenos': [('aceite', (1, 2), (3, 6))],
                     'maquinas': [('horno', (1, 2)), ('iman', (0, 1))], 'piezas': {'obra': 2}, 'num_piezas': (1, 2),
                     'objetos': {'caja_de_carbon': 3, 'engranaje': 1, 'chatarra': 2, 'tuberia': 1, 'vagoneta': 1}, 'cantidad': (3, 6)},
         'calle': {'forma': {'rect': 2, 'cruz': 1}, 'simetria': {'h': 1, 'no': 2}, 'terrenos': [('charco', (1, 3), (2, 5))],
                   'piezas': {'estacionamiento': 2, 'esquina': 3}, 'num_piezas': (2, 4), 'objetos': {'poste_de_luz': 2, 'hidrante': 2, 'contenedor': 1}, 'cantidad': (2, 5)},
         'plaza': {'forma': {'esquinas': 2, 'cruz': 1}, 'simetria': {'hv': 2, 'h': 1}, 'terrenos': [('hierba', (2, 3), (4, 8))],
                   'piezas': {'fuente': 2, 'esquina': 1}, 'num_piezas': (1, 3), 'objetos': {'banco_de_plaza': 3, 'poste_de_luz': 2, 'arbol': 2}, 'cantidad': (3, 6)},
         'callejon': {'forma': {'cruz': 2, 'rect': 1}, 'terrenos': [('sombra', (3, 5), (5, 10)), ('charco', (1, 2), (2, 4))],
                      'piezas': {'esquina': 3, 'obra': 1}, 'num_piezas': (2, 4), 'objetos': {'bolsa_de_basura': 4, 'contenedor': 2, 'cabina_telefonica': 1}, 'cantidad': (3, 7)},
         'central electrica': {'forma': {'rect': 1, 'columnas': 1}, 'simetria': {'hv': 1, 'h': 1}, 'especiales': ['cables'], 'maquinas': [('generador', (1, 2))],
                               'piezas': {'subestacion': 3}, 'num_piezas': (1, 3), 'objetos': {'poste_de_luz': 2, 'chatarra': 2, 'maquina_expendedora': 1}, 'cantidad': (2, 5)},
         'alcantarilla': {'forma': {'cruz': 1, 'rect': 1}, 'interior': True, 'especiales': ['rio'], 'terrenos': [('toxico', (1, 3), (3, 6)), ('charco', (1, 3), (2, 5))],
                          'piezas': {'esquina': 1}, 'num_piezas': (0, 2), 'objetos': {'bolsa_de_basura': 3, 'tuberia': 2, 'tacho_de_basura': 2}, 'cantidad': (3, 6)},
     },
     'arena': {'forma': {'rect': 1}, 'simetria': {'hv': 1}, 'especiales': ['cables'], 'terrenos': [('charco', (3, 4), (3, 6))], 'maquinas': [('generador', (2, 2))],
               'piezas': {}, 'num_piezas': (0, 0), 'objetos': {}, 'cantidad': (0, 0)}},

    {'clave': 'origen', 'nombre': 'El Origen', 'regi': 'regigigas', 'final': 'arceus', 'jefe': None,
     'suelo': (204, 194, 236), 'pared': (88, 78, 130), 'clima_regi': None, 'clima_final': 'sol',
     'plan_fijo': ['tienda', 'regi', 'final'],             # cuando caen los 5 Regis: tienda, Regigigas y despues Arceus
     'clima': {'despejado': 2, 'tormenta_electrica': 1, 'niebla': 1},
     'enemigos': ['garchomp', 'lucario', 'annihilape', 'greninja', 'xatu', 'golurk', 'weavile', 'luxray', 'blaziken', 'corviknight'],
     'variantes': {
         'templo de los titanes': {'forma': {'columnas': 1}, 'simetria': {'hv': 1}, 'terrenos': [('sombra', (2, 4), (5, 9))], 'maquinas': [('monolito', (1, 2))],
                                   'piezas': {'santuario': 2, 'ruinas': 2}, 'num_piezas': (2, 3), 'objetos': {'pilar_de_cristal': 2, 'columna_rota': 2, 'estatua_de_titan': 1}, 'cantidad': (2, 4)},
     },
     'arena': {'forma': {'columnas': 1}, 'simetria': {'hv': 1}, 'maquinas': [('altar', (2, 2)), ('monolito', (2, 2))], 'piezas': {'ruinas': 1}, 'num_piezas': (1, 2),
               'objetos': {}, 'cantidad': (0, 0)}},
]


def planificar(azar):
    """Lista de listas de tipos de sala (una por era). La tienda nunca cae en un jefe."""
    normales = [e for e in ERAS if 'plan_fijo' not in e]
    total = len(normales) * SALAS_POR_ERA
    plano = ['combate'] * total
    for e in range(len(normales)):                              # los jefes fijos de cada era
        plano[e * SALAS_POR_ERA + SALA_JEFE - 1] = 'jefe'
        plano[e * SALAS_POR_ERA + SALA_REGI - 1] = 'regi'
    ultima, hueco_ant = -1, None                                # indice de la ultima tienda y cuanto tardo
    while True:
        minimo = TIENDA_HUECO[0] if hueco_ant is None else max(TIENDA_HUECO[0], TIENDA_COMPENSA - hueco_ant)
        opciones = [h for h in range(minimo, TIENDA_HUECO[1] + 1) if ultima + h < total and plano[ultima + h] == 'combate']
        if not opciones:                                        # todas caian en jefe: se corre una o dos salas
            opciones = [h for h in (TIENDA_HUECO[1] + 1, TIENDA_HUECO[1] + 2) if ultima + h < total and plano[ultima + h] == 'combate']
        if not opciones: break                                  # no entra otra tienda antes del final
        hueco = azar.choice(opciones)
        ultima += hueco; hueco_ant = hueco
        plano[ultima] = 'tienda'
    plan = [plano[e * SALAS_POR_ERA:(e + 1) * SALAS_POR_ERA] for e in range(len(normales))]
    return plan + [list(e['plan_fijo']) for e in ERAS if 'plan_fijo' in e]


def clima_inicial(azar, era):
    pesos = ERAS[era]['clima']
    return azar.choices(list(pesos), list(pesos.values()))[0]


def siguiente_clima(azar, era, actual):
    """Clima de la sala que viene: casi siempre sigue igual o pasa a uno vecino, y segun lo que es comun en la era."""
    pesos = ERAS[era]['clima']
    if actual not in pesos: return clima_inicial(azar, era)     # cambio de era: arranca de cero
    if azar.random() < PROB_SEGUIR_CLIMA: return actual
    vecinos = [v for v in VECINOS_CLIMA.get(actual, ()) if pesos.get(v)]
    if not vecinos: return actual
    return azar.choices(vecinos, [pesos[v] for v in vecinos])[0]


def nuevo_recorrido(semilla=None):
    """Estado de una partida: el plan entero, en que sala estas y el clima que viene arrastrando."""
    azar = random.Random(semilla)
    return {'plan': planificar(azar), 'era': 0, 'sala': 0, 'semilla': semilla, 'clima': clima_inicial(azar, 0), 'azar': azar}


def tipo_sala(rec, era=None, sala=None):
    return rec['plan'][rec['era'] if era is None else era][rec['sala'] if sala is None else sala]


def salas_de(rec, era=None):
    return len(rec['plan'][rec['era'] if era is None else era])


def siguiente(rec):
    """(era, sala) de la sala que viene, o None si la actual es la ultima."""
    if rec['sala'] + 1 < salas_de(rec): return rec['era'], rec['sala'] + 1
    if rec['era'] + 1 < len(rec['plan']): return rec['era'] + 1, 0
    return None


def avanzar(rec):
    """Pasa a la sala siguiente y le elige el clima (si cambia de era, el clima arranca de nuevo)."""
    pos = siguiente(rec)
    if pos is None: return False
    cambio_era = pos[0] != rec['era']
    rec['era'], rec['sala'] = pos
    rec['clima'] = clima_inicial(rec['azar'], rec['era']) if cambio_era else siguiente_clima(rec['azar'], rec['era'], rec['clima'])
    return True


def ir_a(rec, era, sala):
    """Salto directo (menu debug F2)."""
    rec['era'], rec['sala'] = era, sala
    rec['clima'] = clima_inicial(rec['azar'], era)


def destinos_siguientes(rec, azar):
    """Lo que hay detras de cada puerta: variantes distintas si la que viene es de combate, una sola si es especial."""
    pos = siguiente(rec)
    if pos is None: return [{'tipo': 'fin', 'variante': None, 'era': rec['era']}]
    era, sala = pos
    tipo = tipo_sala(rec, era, sala)
    if tipo != 'combate' or era != rec['era']:                  # tienda, jefe, regi o cambio de era: una sola puerta
        variante = azar.choice(list(ERAS[era]['variantes'])) if tipo == 'combate' else None
        return [{'tipo': tipo, 'variante': variante, 'era': era, 'desde': rec['era']}]
    cantidad = azar.choices([c for c, _ in PUERTAS_POR_SALA], [p for _, p in PUERTAS_POR_SALA])[0]
    variantes = azar.sample(list(ERAS[era]['variantes']), min(cantidad, len(ERAS[era]['variantes'])))
    return [{'tipo': 'combate', 'variante': v, 'era': era, 'desde': rec['era']} for v in variantes]


def jefe_de(era, tipo):
    """Pokemon que pelea en una sala de jefe, de Regi o la final."""
    datos = ERAS[era]
    return datos.get('final') if tipo == 'final' else datos['regi'] if tipo == 'regi' else datos['jefe']


def etiqueta_destino(destino):
    """Texto del cartel arriba de una puerta."""
    era = ERAS[destino['era']]
    if destino['tipo'] == 'tienda': return 'TIENDA'
    if destino['tipo'] in ('jefe', 'regi', 'final'): return destino['tipo'].upper() + ': ' + str(jefe_de(destino['era'], destino['tipo'])).title()
    if destino['tipo'] == 'fin': return 'FINAL'
    if destino['era'] != destino.get('desde', destino['era']): return era['nombre']
    return destino['variante'].capitalize()


def escala(era, sala):
    """Cuanto mas fuertes son los enemigos segun por donde vas."""
    return {'vida': 1 + 0.3 * era + 0.01 * sala, 'daño': 1 + 0.18 * era + 0.005 * sala, 'cantidad': 6 + era + sala // 6}


if __name__ == '__main__':
    rec = nuevo_recorrido()
    letras = {'combate': '.', 'tienda': 'T', 'jefe': 'J', 'regi': 'R', 'final': 'A'}
    for i, era in enumerate(rec['plan']):                       # dibuja el plan: T tienda, J semijefe, R regi, A arceus
        print(ERAS[i]['nombre'].ljust(22), ''.join(letras[t] for t in era))
    climas = []
    for _ in range(25): climas.append(rec['clima']); avanzar(rec)
    print('clima de las primeras salas:', ' > '.join(climas))
