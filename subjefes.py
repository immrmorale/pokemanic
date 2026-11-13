"""
subjefes.py - Los subjefes de cada era: uno en la sala 10 y otro en la sala 20 (ver SUBJEFES).

    import subjefes
    subjefes.arena(nombre)                          # como se arma su sala (se la pasa a generacion.generar_arena)
    subjefes.preparar(jefe, ent, ahora)             # al crearlo: su estilo y lo que cambia en la sala (agujeros, alcantarillas, metales...)
    subjefes.actualizar(jefe, ctx)                  # cada frame (en vez de ia.actualizar_jefe)
    subjefes.dibujar_suelo(...) / dibujar(...)      # lo de abajo de los pokemon y lo de arriba (oscuridad incluida)
    subjefes.dibujar_hud(...) / dibujar_hud_jugador(...)
    subjefes.mult_vel(j, ahora) / mult_ataque(j, ahora) / mult_recarga(j, ahora)    # lo que te hacen a vos
    subjefes.terminar(jefe, ctx)                    # cayo: se van sus pokemon, vuelve el piso y se te van los efectos

    Era Glacial         sala 10 Cramorant        sala 20 Mamoswine
    Edad de Piedra      sala 10 Tyrantrum        sala 20 Armaldo
    Edad de los Metales sala 10 Scizor           sala 20 Tinkaton
    Edad Media          sala 10 Chandelure       sala 20 Samurott de Hisui
    Edad Moderna        sala 10 Magnezone        sala 20 Muk de Alola

Los pokemon que aparecen en estas peleas (Arrokuda, Pikachu, Magnemite y Grimer) no dan monedas ni experiencia y nunca quieren
unirse; en las salas de los subjefes nadie se ofrece como amigo.
Todos los numeros estan en SUBJEFES: tiempos en ms, velocidades en pixeles por frame, daños como multiplicador del daño del subjefe.
"""

import math
import random
import pygame
from datos import mundos, tienda
from combate import ia
from mundo import entorno
from sistema import animaciones


SALAS = mundos.SALAS_SUBJEFE     # numero de sala (desde 1) de cada subjefe de la era
VIDA = 0.8                       # vida de un subjefe: el 80% de la de un semijefe
MONEDAS = 80
NIVELES_MINION = 4               # los pokemon que salen en las peleas tienen 4 niveles menos que la sala

# efectos sobre vos (van en jugador['fx_jefe'], igual que los de Giratina, Dialga y Palkia)
FX = {'sj_lento': 0.75, 'sj_lento_leve': 0.9, 'agua_lenta': 0.9, 'ataque_bajo': 0.75}
ia.NOMBRE_FX.update({'sj_lento': 'Lento', 'sj_lento_leve': 'Campo eléctrico', 'agua_lenta': 'Agua prehistórica', 'ataque_bajo': 'Ataque bajo'})

_ARENA_VACIA = {'piezas': {}, 'num_piezas': (0, 0), 'objetos': {}, 'cantidad': (0, 0), 'maquinas': []}


def _arena_de(**extra):
    return dict(dict(_ARENA_VACIA, simetria={'no': 1}, paredes=(0, 0)), **extra)


# ==================== los numeros de cada subjefe ====================

SUBJEFES = {
    # ---------- Era Glacial ----------
    # Cramorant: 9 agujeros en el hielo por los bordes; cada 3 s salen 3 Arrokuda (y un Pikachu cada tanto) que van hacia el.
    #   Si toca uno se lo traga: si no le pegas en 1,5 s lo guarda abajo de su barra (hasta 3); si le pegas usa Reserva.
    #   Buceo        bajo el hielo 4 s persiguiendo tu ultima posicion (sin comer: los Arrokuda se juntan donde esta) y sale de golpe
    #   Picotaladro  embestida con el pico amarillo: si te pega y tenes una baya en el lugar 1 del cinturon, te la roba y se cura
    #   Reserva      (le pegas mientras traga) 0 guardados: sube defensa y grita (te frena) - 1: sube ataque y velocidad - 2: los escupe y caen del cielo
    #   Tragamisil   (junto 3 sin que le pegues) los tira en triangulo hacia vos; si se trago un Pikachu, onda electrica que paraliza 2 s
    'cramorant': {'era': 0, 'titulo': 'Cramorant', 'lema': 'los agujeros del hielo', 'tam': (100, 100), 'sprite': 130, 'vel': 1.5,
                  'pausa': (900, 1500), 'primer_mov': 2500,
                  'arena': _arena_de(forma={'rect': 1}, terrenos=[('hielo', (4, 6), (10, 18)), ('nieve', (1, 2), (4, 8))]),
                  'agujeros': 9, 'cada': 3000, 'de_a': 3, 'max_peces': 9, 'pikachu': 5000, 'vel_pez': 2.3, 'vel_pika': 2.7, 'vida_minion': 0.2,
                  'traga': 1500, 'bolsa': 3,
                  'defensa': {'mult': 0.65, 'dura': 6000, 'onda': 1100, 'grosor': 34, 'lento': 3500},
                  'furia': {'ataque': 1.3, 'vel': 1.5, 'dura': 6000},
                  'escupe': {'por_pez': 2, 'aviso': 900, 'radio': 70, 'daño': 0.8, 'cada': 220},
                  'movs': {'buceo': {'espera': 7000, 'dura': 4000, 'vel': 3.4, 'retraso': 450, 'aviso': 400, 'radio': 120, 'daño': 1.0},
                           'picotaladro': {'espera': 3500, 'aviso': 550, 'vel': 15, 'largo': 520, 'daño': 0.9, 'cura': 0.4},
                           'tragamisil': {'reaccion': True, 'aviso': 550, 'vel': 7.5, 'radio': 30, 'daño': 1.25, 'dist': 1200, 'separa': 48},
                           'onda_electrica': {'reaccion': True, 'aviso': 450, 'dura': 1000, 'grosor': 32, 'radio': 380, 'daño': 0.5, 'paraliza': 2000}}},
    # Mamoswine: la sala es mas grande; cada Terratemblor rompe el borde del hielo y la sala se achica. En las nevadas se vuelve
    # semitransparente (Manto Niveo).
    #   Fuerza Equina  3 estampidas en linea recta hacia donde estabas, con 1,5 s entre una y otra (en el medio a veces tira rocas)
    #   Terratemblor   terremoto en toda la sala: pega mas cuanto mas cerca estes
    #   Alud           la sala se pone roja con una flecha 1 s (Mamoswine quieto) y despues sopla la ventisca: cubrite detras de algo
    #   Poder Pasado   5 rocas a su alrededor que tira de a una hacia vos cada 0,3 s
    'mamoswine': {'era': 0, 'titulo': 'Mamoswine', 'lema': 'el hielo que se agrieta', 'tam': (130, 115), 'sprite': 170, 'vel': 1.4,
                  'pausa': (800, 1300), 'primer_mov': 1800, 'clima': 'nublado',
                  'arena': dict(_ARENA_VACIA, forma={'rect': 2, 'esquinas': 1}, simetria={'no': 1}, paredes=(0, 0), tamaño=(27, 19),
                                terrenos=[('hielo', (3, 5), (8, 14)), ('nieve', (3, 5), (8, 14))],
                                piezas={'bloques de hielo': 1, 'estalagmitas': 1}, num_piezas=(1, 2),
                                objetos={'roca_nevada': 2, 'bloque_de_hielo': 2, 'pino_nevado': 1}, cantidad=(7, 10)),
                  'nevada': {'primera': 5000, 'cada': 16000, 'dura': 9000, 'alfa': 70},
                  'minimo': (11, 7),            # el hielo no se rompe mas alla de este rectangulo del medio (columnas, filas)
                  'movs': {'fuerza_equina': {'espera': 6500, 'veces': 3, 'aviso': 500, 'vel': 13, 'largo': 700, 'daño': 1.0, 'entre': 1500,
                                             'rocas': 0.5},
                           'terratemblor': {'espera': 8000, 'aviso': 1000, 'radio': 900, 'daño_max': 1.3, 'daño_min': 0.25},
                           'alud': {'espera': 10000, 'aviso': 1000, 'dura': 1300, 'daño': 0.9, 'cubre': 320},
                           'poder_pasado': {'espera': 5000, 'rocas': 5, 'cada': 300, 'aviso': 500, 'vel': 8.5, 'radio': 20, 'daño': 0.55, 'orbita': 95}}},

    # ---------- Edad de Piedra ----------
    # Tyrantrum: la sala esta oscura y tiene mas paredes; solo se ve el cuarto de circulo que mira Tyrantrum (las paredes lo cortan).
    #   Si estas quieto adentro, por 1 s no sabe donde estas. Si no te ve, camina para cualquier lado. Mandibula Fuerte: sus mordidas
    #   pegan muchisimo y antes de morder la boca brilla del color del colmillo.
    #   Triple Colmillo  cuando entras en su vista: embestida y mordida (igneo quema 2 s, hielo congela 1 s, rayo paraliza)
    #   Danza Dragon     sube velocidad y ataque (se junta hasta 3 veces hasta que ataca), cada 5 s
    #   Testarazo        carga de cabeza que tambien lo lastima a el
    #   Cola Dragon      barrido de 180 grados para atras: castiga quedarse a su espalda
    'tyrantrum': {'era': 1, 'titulo': 'Tyrantrum', 'lema': 'la visión del T-Rex', 'tam': (125, 115), 'sprite': 170, 'vel': 1.9,
                  'pausa': (450, 850), 'primer_mov': 1200,
                  'arena': dict(_ARENA_VACIA, forma={'rect': 1, 'esquinas': 1}, simetria={'no': 1}, paredes=(5, 7),
                                terrenos=[('arena', (2, 3), (5, 10)), ('hierba', (1, 2), (4, 8))], objetos={'roca': 2, 'menhir': 1}, cantidad=(2, 3)),
                  'vision': {'radio': 470, 'apertura': math.pi / 2, 'rayos': 28, 'quieto': 1000, 'oscuro': 170, 'luz_jugador': 90, 'giro': 0.07},
                  'paseo': (1600, 3000),
                  'colmillos': {'igneo': ('Colmillo Ígneo', (255, 140, 40), 'fuego', 'quemadura', 2000),
                                'hielo': ('Colmillo Hielo', (130, 220, 255), 'hielo', 'congelar', 1000),
                                'rayo': ('Colmillo Rayo', (255, 230, 60), 'electrico', 'paralisis', 2500)},
                  'movs': {'triple_colmillo': {'espera': 1800, 'aviso': 550, 'vel': 14, 'largo': 280, 'radio': 95, 'daño': 1.5, 'cerca': 360},
                           'danza_dragon': {'espera': 5000, 'max': 3, 'vel': 0.15, 'ataque': 0.2, 'dura': 700},
                           'testarazo': {'espera': 5500, 'aviso': 650, 'vel': 14, 'largo': 650, 'daño': 1.3, 'propio': 0.04, 'aturdido': 900},
                           'cola_dragon': {'espera': 2600, 'aviso': 500, 'radio': 230, 'daño': 1.1, 'empuje': 170, 'cerca': 240}}},
    # Armaldo: Nado Rapido: Giro Rapido deja agua prehistorica (se puede pisar): a vos te frena un 10% y a el lo acelera un 25%.
    #   Armadura de Fosil: cada Trampa Rocas lo cubre 3 s y recibe menos daño.
    #   Pin Misil     20 pinchos chicos que rebotan en las paredes (poco daño cada uno)
    #   Cortefuria    tres cortes: un arco, un arco mas grande y una X que pega mas
    #   Trampa Rocas  quieto 0,5 s: tira piedras chicas por toda la sala que se quedan; si pisas una te lastima y se rompe
    #   Giro Rapido   rueda como un trompo rebotando en las paredes; si te pega se frena. Rompe las piedras y deja agua por donde pasa
    'armaldo': {'era': 1, 'titulo': 'Armaldo', 'lema': 'el agua prehistórica', 'tam': (115, 115), 'sprite': 160, 'vel': 1.6,
                'pausa': (700, 1200), 'primer_mov': 1500,
                'arena': dict(_ARENA_VACIA, forma={'rect': 1}, simetria={'no': 1}, paredes=(0, 1), terrenos=[('arena', (2, 4), (6, 12))],
                              objetos={'roca': 1}, cantidad=(1, 2)),
                'agua': {'dura': 14000, 'rapido': 1.25},
                'armadura': {'dura': 3000, 'mult': 0.5},
                'movs': {'pin_misil': {'espera': 5500, 'aviso': 500, 'pinchos': 20, 'vel': 9.5, 'radio': 9, 'daño': 0.12, 'dura': 3500},
                         'cortefuria': {'espera': 3500, 'cerca': 290, 'avisos': (380, 380, 460), 'radios': (125, 175), 'daños': (0.6, 0.75, 1.15),
                                        'largo_x': 200, 'ancho_x': 46, 'avance': 50},
                         'trampa_rocas': {'espera': 7500, 'quieto': 500, 'piedras': 8, 'max': 16, 'radio': 22, 'daño': 0.35, 'aviso': 550},
                         'giro_rapido': {'espera': 6000, 'aviso': 500, 'dura': 3500, 'vel': 9, 'daño': 0.9}}},

    # ---------- Edad de los Metales ----------
    # Scizor: Sobrecalentamiento: despues de Puño Bala o Ida y Vuelta se queda quieto 2 s aleteando para enfriarse (sus esperas no
    #   avanzan) y el viento te empuja para atras. Mientras esos dos recargan se aleja y usa Agilidad o Danza Espada.
    #   Pinzas con ojos falsos: con Agilidad o Danza Espada choca las pinzas y salen 2 ondas que te confunden 2 s.
    #   Puño Bala      aparece al lado tuyo y pega 3 golpes rapidos de acero (5 s)
    #   Ida y Vuelta   embestida hacia vos; si no te pega, golpe rapido de bicho; despues vuelve a donde estaba (5 s). Con Agilidad, mas rapida
    #   Danza Espada   sube el ataque 3 s (3 s)              Agilidad   sube la velocidad 3 s (3 s)
    'scizor': {'era': 2, 'titulo': 'Scizor', 'lema': 'las pinzas de acero', 'tam': (100, 100), 'sprite': 140, 'vel': 2.1,
               'pausa': (350, 650), 'primer_mov': 1200,
               'arena': dict(_ARENA_VACIA, forma={'columnas': 1, 'rect': 1}, simetria={'hv': 1}, paredes=(0, 0), objetos={'caja': 1, 'barril': 1},
                             cantidad=(2, 3)),
               'lejos': 400,
               'calor': {'dura': 2000, 'radio': 560, 'fuerza': 3.2},
               'ondas': {'vel': 6.5, 'radio': 30, 'abanico': 0.35, 'dist': 950, 'confusion': 2000},
               'movs': {'puño_bala': {'espera': 5000, 'golpes': 3, 'aviso': 230, 'radio': 82, 'daño': 0.45, 'lado': 95, 'entre': 110},
                        'ida_y_vuelta': {'espera': 5000, 'aviso': 380, 'vel': 16, 'rapido': 1.4, 'largo': 560, 'daño': 0.8, 'aviso_golpe': 200,
                                         'radio': 90, 'daño_golpe': 0.7, 'vuelta': 14},
                        'danza_espada': {'espera': 3000, 'dura': 3000, 'ataque': 1.5, 'anim': 600},
                        'agilidad': {'espera': 3000, 'dura': 3000, 'vel': 1.6, 'anim': 600},
                        'sobrecalentamiento': {'reaccion': True}}},
    # Tinkaton: Martillo Clavado: si Martillo Colosal no te pega queda trabada 3 s sacando el martillo (y anda lenta por el peso).
    #   Forja: hay 5 metales de Corviknight en los bordes; cada vez que se traba se le acercan, y si uno la toca mientras esta trabada
    #   lo suma al martillo (de a uno): el Martillo Colosal crece y pega mas, pero ella y el martillo van mas lentos.
    #   Martillo Colosal  salta y su sombra te sigue 4 s; despues cae. Entre uno y otro usa por lo menos 2 movimientos
    #   Giro Vil          golpe de 360 grados con el martillo (mas grande con cada metal)
    #   Ojitos Tiernos    cara tierna: te baja el ataque
    #   Carantoña         suelta el martillo y se tira hacia vos: si te agarra no te podes mover y te lastima de a poco 2 s; despues vuelve al martillo
    'tinkaton': {'era': 2, 'titulo': 'Tinkaton', 'lema': 'la forja de Corviknight', 'tam': (100, 110), 'sprite': 140, 'vel': 1.15,
                 'pausa': (700, 1100), 'primer_mov': 1500,
                 'arena': _arena_de(forma={'rect': 1}, terrenos=[('ceniza', (1, 2), (3, 6))]),
                 'metales': {'cantidad': 5, 'radio': 30, 'vel': 2.2, 'toca': 85, 'lento': 0.12},
                 'clavado': 3000,
                 'movs': {'martillo_colosal': {'espera': 0, 'entre': 2, 'sube': 350, 'sigue': 4000, 'vel': 4.4, 'lento': 0.1, 'retraso': 300,
                                               'quieto': 350, 'aviso': 450, 'radio': 105, 'radio_metal': 22, 'daño': 1.2, 'daño_metal': 0.25},
                          'giro_vil': {'espera': 3500, 'aviso': 550, 'radio': 150, 'radio_metal': 30, 'daño': 0.9},
                          'ojitos_tiernos': {'espera': 9000, 'aviso': 650, 'radio': 560, 'dura': 6000},
                          'carantoña': {'espera': 6000, 'aviso': 450, 'vel': 15, 'largo': 650, 'agarre': 2000, 'tick': 400, 'daño': 0.12, 'vuelta': 6}}},

    # ---------- Edad Media ----------
    # Chandelure: la sala esta oscura y sin paredes; solo se ve cerca de Chandelure y de los candelabros prendidos.
    #   Candelabros falsos: 9 candelabros parecidos a el; Sofoco los prende. Si la luz de Chandelure toca la de un candelabro prendido,
    #   Poltergeist: te lo tira hasta que choca contra la pared (ahi se queda y se apaga).
    #   Robo de almas: cada 5 s tus ataques tardan mas en recargar y el se cura un poco.
    #   Fuego Fatuo  5 llamitas que iluminan cerca; si entras en su luz te persiguen y te queman 3 s (duran 5 s)
    #   Infortunio   3 franjas violetas largas por 2 s: te lastiman si las pisas, el doble si estas quemado
    #   Sofoco       2 circulos de llamas que giran y avanzan 2 s; prenden los candelabros que tocan
    'chandelure': {'era': 3, 'titulo': 'Chandelure', 'lema': 'los candelabros falsos', 'tam': (95, 110), 'sprite': 140, 'vel': 1.5,
                   'pausa': (700, 1200), 'primer_mov': 1500,
                   'arena': _arena_de(forma={'rect': 1}, terrenos=[('sombra', (2, 3), (6, 10))]),
                   'oscuro': 205, 'luz': 190, 'luz_vela': 135, 'luz_jugador': 80,
                   'candelabros': 9,
                   'poltergeist': {'espera': 1800, 'vel': 11, 'radio': 34, 'daño': 0.9},
                   'robo': {'cada': 5000, 'recarga': 0.08, 'max': 1.6, 'cura': 0.02},
                   'movs': {'fuego_fatuo': {'espera': 7000, 'llamas': 5, 'dura': 5000, 'luz': 85, 'vel': 1.6, 'vel_caza': 3.2, 'radio': 14,
                                            'daño': 0.2, 'quema': 3000},
                            'infortunio': {'espera': 5000, 'franjas': 3, 'aviso': 700, 'dura': 2000, 'ancho': 70, 'tick': 450, 'daño': 0.4},
                            'sofoco': {'espera': 4000, 'aviso': 400, 'dura': 2000, 'radio': 46, 'giro': 0.09, 'separa': 75, 'vel': 4.0, 'daño': 0.55}}},
    # Samurott de Hisui: Piso con puas: Corte Metralla deja puas que lastiman al pisarlas (se van a los 5 s o al pegarte).
    #   Postura de contraataque: si le pegas de cerca mientras ataca, hace una embestida corta hacia vos y un corte.
    #   Corte Metralla  cortes rapidos y despues tira puas por la sala        Aqua Jet    embestida rapida de agua
    #   Concha Filo     carga 0,5 s y un corte de agua grande                  Megacuerno  embestida lenta pero grande hacia donde estabas
    'samurott_hisui': {'era': 3, 'titulo': 'Samurott de Hisui', 'lema': 'la postura del samurái', 'tam': (120, 112), 'sprite': 160, 'vel': 1.9,
                       'pausa': (600, 1000), 'primer_mov': 1300,
                       'arena': dict(_ARENA_VACIA, forma={'rect': 1, 'esquinas': 1}, simetria={'hv': 1}, paredes=(0, 0),
                                     terrenos=[('hierba', (1, 2), (4, 8))], objetos={'barril': 1, 'caja': 1}, cantidad=(2, 4)),
                       'puas': {'dura': 5000, 'radio': 20, 'daño': 0.3},
                       'contra': {'espera': 2500, 'cerca': 170, 'vel': 14, 'largo': 120, 'aviso': 180, 'radio': 100, 'daño': 0.9},
                       'movs': {'corte_metralla': {'espera': 5000, 'cortes': 4, 'aviso': 210, 'entre': 90, 'radio': 95, 'daño': 0.45,
                                                   'puas': 6, 'aviso_puas': 450},
                                'aqua_jet': {'espera': 3500, 'aviso': 320, 'vel': 18, 'largo': 540, 'daño': 0.8},
                                'concha_filo': {'espera': 4500, 'cerca': 330, 'carga': 500, 'radio': 230, 'apertura': 2.4, 'daño': 1.2},
                                'megacuerno': {'espera': 6000, 'aviso': 750, 'vel': 8.5, 'largo': 720, 'radio': 105, 'daño': 1.3},
                                'contraataque': {'reaccion': True}}},

    # ---------- Edad Moderna ----------
    # Magnezone: Campo electrico: cada 6 s un campo de 4 s a su alrededor; si estas adentro te paraliza, te frena un 10% y te da una
    #   polaridad por 10 s (un - azul o un + rojo abajo de tu barra de vida).
    #   Magnemites: cuando se apaga el campo salen 2 (uno + y uno -) hacia lugares al azar; al llegar te atraen o te empujan 3 s segun tu
    #   polaridad (iguales se repelen, distintas se atraen). No lastiman ni se les puede pegar.
    #   Fijar Blanco   un cuadrado rojo en vos: por 4 s cambia los otros ataques, y enseguida usa uno (6 s de espera despues)
    #   Electrocañon   2 rayos que giran a su alrededor 3 s. Fijado: un rayo grande que sigue por donde estabas
    #   Triataque      caen del cielo ataques de fuego, hielo y electrico 3 s (queman, congelan o paralizan 1 s).
    #                  Fijado: tandas de 3 bolas lentas que te siguen, una tanda por segundo durante 3 s
    #   Chispazo       una onda electrica a su alrededor
    'magnezone': {'era': 4, 'titulo': 'Magnezone', 'lema': 'el campo eléctrico', 'tam': (110, 110), 'sprite': 150, 'vel': 1.3,
                  'pausa': (600, 1000), 'primer_mov': 1400,
                  'arena': _arena_de(forma={'rect': 1}, simetria={'hv': 1}),
                  'campo': {'primero': 2500, 'cada': 6000, 'dura': 4000, 'radio': 320, 'paraliza': 1500, 'polaridad': 10000},
                  'magnemites': {'vel': 4.5, 'dura': 3000, 'fuerza': 2.6, 'alcance': 650},
                  'fijado': 4000,
                  'movs': {'fijar_blanco': {'espera': 10000, 'aviso': 500},
                           'electrocañon': {'espera': 5000, 'aviso': 600, 'dura': 3000, 'largo': 760, 'ancho': 38, 'giro': 0.022, 'tick': 600, 'daño': 0.5,
                                            'fijado': {'aviso': 700, 'dura': 2500, 'ancho': 82, 'retraso': 450, 'giro': 0.03, 'tick': 450, 'daño': 0.75}},
                           'triataque': {'espera': 4000, 'dura': 3000, 'cada': 220, 'aviso': 700, 'radio': 58, 'cerca': 280, 'daño': 0.5, 'efecto': 1000,
                                         'fijado': {'tandas': 3, 'entre': 1000, 'vel': 3.0, 'giro': 0.05, 'dura': 3000, 'radio': 18, 'abanico': 0.45}},
                           'chispazo': {'espera': 3000, 'cerca': 290, 'aviso': 450, 'radio': 210, 'daño': 0.8}}},
    # Muk de Alola: no camina; hay 3 alcantarillas (una por pared, menos la de la entrada). Esta 4 s en una, gira 0,5 s sin atacar y
    #   se pasa a otra. Mientras esta en una, de las otras 2 sale un Grimer cada 2 s: si no lo derrotas en 2 s deja una baya o basura
    #   (no se agarran). Cuando Muk llega a una alcantarilla con basura usa Lanzamugre; con una baya, Eructo.
    #   Bomba Lodo       5 bombas que explotan a los 0,5 s y dejan charcos que lastiman cada 0,25 s (2 s de espera)
    #   Lanzamugre       basura enorme con 2 s de aviso: pega mucho y envenena 2 s
    #   Eructo           3 ondas cortadas que te empujan y te envenenan 1 s
    #   Armadura Acida   se vuelve un charco de veneno 2 s: no recibe daño pero sigue atacando
    'muk_alola': {'era': 4, 'titulo': 'Muk de Alola', 'lema': 'las alcantarillas', 'tam': (120, 110), 'sprite': 150, 'vel': 0,
                  'pausa': (500, 900), 'primer_mov': 1200,
                  'arena': _arena_de(forma={'rect': 1}, terrenos=[('charco', (1, 3), (2, 5))]),
                  'alcantarilla': {'dura': 4000, 'gira': 500, 'baja': 350, 'radio': 48},
                  'grimer': {'cada': 2000, 'tiempo': 2000, 'vida': 0.22},
                  'movs': {'bomba_lodo': {'espera': 2000, 'bombas': 5, 'aviso': 500, 'radio': 62, 'daño': 0.5, 'charco': 4000, 'tick': 250,
                                          'daño_charco': 0.06, 'abre': 170},
                           'lanzamugre': {'reaccion': True, 'aviso': 2000, 'radio': 120, 'daño': 1.4, 'veneno': 2000},
                           'eructo': {'reaccion': True, 'ondas': 3, 'entre': 260, 'vel': 7, 'radio': 46, 'daño': 0.45, 'empuje': 170, 'veneno': 1000},
                           'armadura_acida': {'espera': 8000, 'dura': 2000}}},
}

ESTILOS = {'sj_' + n for n in SUBJEFES}
NOMBRE_MOV = {'buceo': 'Buceo', 'picotaladro': 'Picotaladro', 'tragamisil': 'Tragamisil', 'onda_electrica': '¡Se tragó a Pikachu!',
              'fuerza_equina': 'Fuerza Equina', 'terratemblor': 'Terratemblor', 'alud': 'Alud', 'poder_pasado': 'Poder Pasado',
              'triple_colmillo': 'Triple Colmillo', 'danza_dragon': 'Danza Dragón', 'testarazo': 'Testarazo', 'cola_dragon': 'Cola Dragón',
              'pin_misil': 'Pin Misil', 'cortefuria': 'Cortefuria', 'trampa_rocas': 'Trampa Rocas', 'giro_rapido': 'Giro Rápido',
              'puño_bala': 'Puño Bala', 'ida_y_vuelta': 'Ida y Vuelta', 'danza_espada': 'Danza Espada', 'agilidad': 'Agilidad',
              'sobrecalentamiento': 'Sobrecalentamiento',
              'martillo_colosal': 'Martillo Colosal', 'giro_vil': 'Giro Vil', 'ojitos_tiernos': 'Ojitos Tiernos', 'carantoña': 'Carantoña',
              'fuego_fatuo': 'Fuego Fatuo', 'infortunio': 'Infortunio', 'sofoco': 'Sofoco',
              'corte_metralla': 'Corte Metralla', 'aqua_jet': 'Aqua Jet', 'concha_filo': 'Concha Filo', 'megacuerno': 'Megacuerno',
              'contraataque': '¡Contraataque!',
              'fijar_blanco': 'Fijar Blanco', 'electrocañon': 'Electrocañón', 'triataque': 'Triataque', 'chispazo': 'Chispazo',
              'bomba_lodo': 'Bomba Lodo', 'lanzamugre': 'Lanzamugre', 'eructo': 'Eructo', 'armadura_acida': 'Armadura Ácida'}
OSCURAS = ('tyrantrum', 'chandelure')       # salas a oscuras


def arena(nombre):
    """Como se arma la sala de ese subjefe (formato de las variantes de mundos.ERAS)."""
    return SUBJEFES[nombre]['arena']


def clima(nombre):
    """El clima con el que arranca su sala (None: el que venia)."""
    return SUBJEFES[nombre].get('clima')


def es_subjefe(b):
    return bool(b) and b.get('estilo') in ESTILOS


# ==================== utilidades ====================

def _d(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
def _ang(a, b): return math.atan2(b[1] - a[1], b[0] - a[0])
def _v(ang): return math.cos(ang), math.sin(ang)
def _dif(a, b): return (a - b + math.pi) % math.tau - math.pi
def _mitad(j): return max(j['rect'].size) / 2
def _datos(b): return SUBJEFES[b['sj_nombre']]
def _md(b, mov): return SUBJEFES[b['sj_nombre']]['movs'][mov]
def _jc(ctx): return ctx['jugador']['rect'].center
def _bc(b): return b['rect'].center


def _solido(ent, x, y):
    """Si en ese punto hay pared, puerta o maquina (lo que frena las balas)."""
    return bool(mundos.TERRENOS[entorno.terreno_en(ent, x, y)].get('solido'))


def _cambiar(b, ent, f, c, nuevo):
    """Cambia una casilla y se acuerda de lo que habia (para devolverlo al terminar la pelea)."""
    viejo = ent['m'][f][c]
    if viejo == nuevo or not entorno.cambiar(ent, f, c, nuevo): return False
    b['sj']['antes'].setdefault((f, c), viejo)
    return True


def _paso(b, ctx, dx, dy, vel):
    """Mueve al subjefe vel pixeles en esa direccion frenando contra lo solido. Devuelve (choco en x, choco en y)."""
    S, ent = b['sj'], ctx['ent']
    r = S['resto']
    r[0] += dx * vel; r[1] += dy * vel
    px, py = int(r[0]), int(r[1])
    r[0] -= px; r[1] -= py
    x0, y0 = b['rect'].topleft
    entorno.mover(ent, b['rect'], px, py, entorno.tipos_de(b))
    antes = b['rect'].topleft
    b['rect'].clamp_ip(S['area'])
    mx, my = b['rect'].x - x0, b['rect'].y - y0
    return (px != 0 and (mx != px or b['rect'].x != antes[0])), (py != 0 and (my != py or b['rect'].y != antes[1]))


def _ir(b, ctx, destino, vel, alejarse=False):
    """Camina hacia (o lejos de) un punto rodeando paredes (mapa de flujo de la ia)."""
    ia._ir_a(ctx['ent'], b, destino, vel, [], alejarse)
    b['rect'].clamp_ip(b['sj']['area'])


def _acercar(b, ctx, ideal, vel):
    """Se queda mas o menos a 'ideal' pixeles tuyos."""
    d = _d(_bc(b), _jc(ctx))
    if d > ideal: _ir(b, ctx, _jc(ctx), vel)
    elif d < ideal * 0.55: _ir(b, ctx, _jc(ctx), vel * 0.8, True)


def _poner(b, pos):
    b['rect'].center = (round(pos[0]), round(pos[1]))
    b['rect'].clamp_ip(b['sj']['area'])


def _buff(b, clave, ahora):
    m, hasta = b['sj']['buffs'].get(clave, (1.0, 0))
    return m if ahora < hasta else 1.0


def _vel(b, ahora, base=None):
    S = b['sj']
    return (_datos(b)['vel'] if base is None else base) * _buff(b, 'vel', ahora) * S.get('mult_vel', 1.0)


def _quemado(j, ahora):
    return ahora < (j.get('estados') or {}).get('quemadura', 0)


def _efecto(ctx, ef, ms):
    """Un efecto sobre vos: quemadura, paralisis, confusion o veneno (estados del juego), congelar, o uno de FX."""
    if not ef: return
    j, ahora = ctx['jugador'], ctx['ahora']
    if ef == 'congelar':
        if 'hielo' in j['tipos']: return
        j['congelado_hasta'] = max(j['congelado_hasta'], ahora + ms)
    elif ef in FX: ia.poner_fx(j, ef, ahora, ms)
    elif ctx.get('poner_estado'): ctx['poner_estado'](ef, ms)


def _pegar(b, ctx, daño, tipo, ef=None, ms=0):
    """Te pega (con los buffs de ataque del subjefe). Devuelve cuanta vida te saco; si te saco algo, te pone el efecto."""
    k = _buff(b, 'ataque', ctx['ahora']) * b['sj'].get('mult_ataque', 1.0)
    hecho = ia._pegar(b, ctx, daño * k, tipo)
    if hecho > 0: _efecto(ctx, ef, ms)
    return hecho


def _toca_b(b, ctx, extra=0):
    """Si el subjefe te esta tocando (con algo de margen)."""
    return _d(_bc(b), _jc(ctx)) <= max(b['rect'].size) * 0.42 + extra + _mitad(ctx['jugador']) * 0.8


def _empujar(b, direccion, vel, distancia):
    b['sj']['empuje'] = {'dir': direccion, 'vel': vel, 'restante': distancia, 'resto': [0.0, 0.0]}


def _actualizar_empuje(b, ctx):
    S, j = b['sj'], ctx['jugador']
    e = S['empuje']
    if not e: return
    e['resto'][0] += e['dir'][0] * e['vel']; e['resto'][1] += e['dir'][1] * e['vel']
    px, py = int(e['resto'][0]), int(e['resto'][1])
    e['resto'][0] -= px; e['resto'][1] -= py
    antes = j['rect'].center
    entorno.mover(ctx['ent'], j['rect'], px, py, j['tipos'])
    e['restante'] -= e['vel']
    if e['restante'] <= 0 or ((px or py) and j['rect'].center == antes): S['empuje'] = None


def _tirar_jugador(b, ctx, dx, dy, clave='resto_tira'):
    """Mueve al jugador un poquito (viento, imanes): se acumulan los decimales."""
    S, j = b['sj'], ctx['jugador']
    r = S.setdefault(clave, [0.0, 0.0])
    r[0] += dx; r[1] += dy
    px, py = int(r[0]), int(r[1])
    r[0] -= px; r[1] -= py
    if px or py: entorno.mover(ctx['ent'], j['rect'], px, py, j['tipos'])


def _arco(centro, ang, apertura, radio, n=16):
    """Puntos de un sector circular (abanico) para los golpes en arco."""
    return [centro] + [(centro[0] + math.cos(ang - apertura / 2 + apertura * i / n) * radio,
                        centro[1] + math.sin(ang - apertura / 2 + apertura * i / n) * radio) for i in range(n + 1)]


def _punto_area(b, margen=60):
    A = b['sj']['area'].inflate(-2 * margen, -2 * margen)
    return random.uniform(A.left, A.right), random.uniform(A.top, A.bottom)


def _punto_libre(b, ctx, margen=60, intentos=30):
    """Un punto del area donde no hay nada solido para el jugador (para piedras, puas, bombas...)."""
    duros = entorno.solidos(ctx['ent'], ['normal'])
    for _ in range(intentos):
        p = _punto_area(b, margen)
        if not any(r.collidepoint(p) for r in duros): return p
    return _punto_area(b, margen)


def _anillo(ent, n, profundidad=1, evitar_puertas=3):
    """n casillas repartidas parejo por el borde de adentro de la sala (lejos de las puertas). Devuelve (fila, columna)."""
    m, tam = ent['m'], ent['tam']
    filas, cols = len(m), len(m[0])
    p = profundidad
    cc = cols // 2
    anillo = []
    for c in range(p + 1, cols - p - 1):
        if abs(c - cc) > evitar_puertas: anillo += [(p, c), (filas - 1 - p, c)]
    for f in range(p + 1, filas - p - 1):
        anillo += [(f, p), (f, cols - 1 - p)]
    centro = (cols / 2, filas / 2)
    anillo = [x for x in anillo if m[x[0]][x[1]] not in ('puerta', 'entrada')]
    anillo.sort(key=lambda fc: math.atan2(fc[0] + 0.5 - centro[1], fc[1] + 0.5 - centro[0]))
    if not anillo: return []
    paso = len(anillo) / n
    desfase = random.random() * paso
    return [anillo[int(desfase + i * paso) % len(anillo)] for i in range(n)]


def _centro(ent, f, c):
    return (c + 0.5) * ent['tam'], (f + 0.5) * ent['tam']


def _marca(b, ahora, clase, dura, **extra):
    m = dict({'clase': clase, 'inicio': ahora, 'hasta': ahora + dura}, **extra)
    b['sj']['marcas'].append(m)
    return m


def _mensaje(b, texto, ms=1500):
    b['mensajes'].append((texto, ms))


# ----- golpes en el piso (los dibuja ia._dibujar_golpes), con efectos y empujes propios -----

def _golpe(jefe, ahora, forma, aviso, tipo, daño, dura=150, tick=None, ef=None, ms=0, empuje=0, infortunio=False, **extra):
    """(el jefe no se llama b: 'b' es la punta de las lineas)"""
    g = ia._golpe(jefe, ahora, forma, aviso, tipo, daño, dura, tick, **extra)
    g.update(ef=ef, ef_ms=ms, empuje=empuje, infortunio=infortunio)
    return g


def _actualizar_golpes(b, ctx):
    j, ahora = ctx['jugador'], ctx['ahora']
    for g in b['golpes'][:]:
        if ahora >= g['hasta']: b['golpes'].remove(g); continue
        if ahora < g['golpe']: continue
        if not g.get('cayo'):
            g['cayo'] = True
            if g.get('temblor'): ctx['impacto'](*ia._centro_golpe(g), g.get('radio', 60), g['temblor'])
        if not g['daño'] or not ia._toca(g, j): continue
        if g['tick'] is None:
            if g['pego']: continue
            g['pego'] = True
        elif ahora < g['prox']: continue
        else: g['prox'] = ahora + g['tick']
        daño = g['daño'] * (2 if g.get('infortunio') and _quemado(j, ahora) else 1)
        hecho = _pegar(b, ctx, daño, g['tipo'], g.get('ef'), g.get('ef_ms', 0))
        if hecho > 0 and g.get('empuje'):
            c = ia._centro_golpe(g)
            a = _ang(c, j['rect'].center)
            _empujar(b, _v(a), 11, g['empuje'])


# ----- balas propias (rebotan, siguen, empujan o solo ponen un efecto) -----

def _bala(b, ahora, pos, ang, vel, radio, daño, tipo, clase, dist=1000, dura=None, rebota=False, sigue=0, ef=None, ms=0, empuje=0, color=None, **extra):
    p = {'pos': pos, 'ang': ang, 'vel': vel, 'radio': radio, 'daño': daño, 'tipo': tipo, 'clase': clase, 'dist': dist,
         'hasta': None if dura is None else ahora + dura, 'rebota': rebota, 'sigue': sigue, 'ef': ef, 'ms': ms, 'empuje': empuje,
         'color': color, 'inicio': ahora}
    p.update(extra)
    b['sj']['proys'].append(p)
    return p


def _actualizar_proys(b, ctx):
    ent, j, ahora, S = ctx['ent'], ctx['jugador'], ctx['ahora'], b['sj']
    A = S['area']
    for p in S['proys'][:]:
        if p['hasta'] is not None and ahora >= p['hasta']: S['proys'].remove(p); continue
        if ahora < p.get('sale', 0): continue
        if p['sigue']: p['ang'] = ia._girar_hacia(p['ang'], _ang(p['pos'], j['rect'].center), p['sigue'])
        dx, dy = _v(p['ang'])
        x, y = p['pos'][0] + dx * p['vel'], p['pos'][1] + dy * p['vel']
        if p['rebota']:
            bx = _solido(ent, x, p['pos'][1]) or not A.left <= x <= A.right
            by = _solido(ent, p['pos'][0], y) or not A.top <= y <= A.bottom
            if bx: dx = -dx; x = p['pos'][0]
            if by: dy = -dy; y = p['pos'][1]
            if bx or by: p['ang'] = math.atan2(dy, dx)
        elif _solido(ent, x, y) or not A.inflate(240, 240).collidepoint(x, y):
            S['proys'].remove(p); S['marcas'].append({'clase': 'chispa', 'pos': p['pos'], 'inicio': ahora, 'hasta': ahora + 250}); continue
        p['dist'] -= p['vel']
        if p['dist'] <= 0: S['proys'].remove(p); continue
        p['pos'] = (x, y)
        if _d(p['pos'], j['rect'].center) > p['radio'] + _mitad(j) * 0.8: continue
        if ia._esquivando(j, ahora): continue
        if p['daño']: hecho = _pegar(b, ctx, p['daño'], p['tipo'], p['ef'], p['ms'])
        else:
            hecho = 1
            _efecto(ctx, p['ef'], p['ms'])
            if p.get('aviso_ef'): _mensaje(b, p['aviso_ef'], 1300)
        if hecho > 0 and p['empuje']: _empujar(b, (dx, dy), 12, p['empuje'])
        S['proys'].remove(p)


# ----- ondas que crecen (gritos, chispazos): pegan una vez cuando el borde te pasa por encima -----

def _onda(b, ahora, centro, dura, maximo, grosor, daño, tipo, ef=None, ms=0, color=(255, 255, 255), aviso_ef=None):
    b['sj']['ondas'].append({'centro': centro, 'inicio': ahora, 'dura': dura, 'max': maximo, 'grosor': grosor, 'daño': daño, 'tipo': tipo,
                             'ef': ef, 'ms': ms, 'color': color, 'pego': False, 'aviso_ef': aviso_ef})


def _actualizar_ondas(b, ctx):
    j, ahora, S = ctx['jugador'], ctx['ahora'], b['sj']
    for o in S['ondas'][:]:
        k = (ahora - o['inicio']) / o['dura']
        if k >= 1: S['ondas'].remove(o); continue
        if o['pego'] or k < 0: continue
        d = _d(j['rect'].center, o['centro'])
        if abs(d - o['max'] * k) <= o['grosor'] / 2 + _mitad(j):
            o['pego'] = True
            if ia._esquivando(j, ahora): continue
            if o['daño']: _pegar(b, ctx, o['daño'], o['tipo'], o['ef'], o['ms'])
            else:
                _efecto(ctx, o['ef'], o['ms'])
                if o['aviso_ef']: _mensaje(b, o['aviso_ef'], 1300)


# ----- dash: embestida en linea recta que te pega una vez -----

def _dash(b, ctx, a, vel, daño, tipo, extra=0, ef=None, ms=0):
    """Avanza un paso de la embestida guardada en a ('dir', 'restante'). Devuelve 'sigue', 'llego' o 'choco'.
    Si te toca te pega una vez (a['acerto'] queda en True si te saco vida)."""
    b['sin_contacto'] = True                                        # el golpe de la embestida ya pega: el choque no suma otro
    paso = min(vel, a['restante'])
    cx_, cy_ = _paso(b, ctx, a['dir'][0], a['dir'][1], paso)
    a['restante'] -= paso
    if not a.get('pego') and _toca_b(b, ctx, extra):
        a['pego'] = True
        a['acerto'] = _pegar(b, ctx, daño, tipo, ef, ms) > 0
    if cx_ or cy_: return 'choco'
    return 'llego' if a['restante'] <= 0 else 'sigue'


# ----- los pokemon que salen en las peleas -----

def _invocar(b, ctx, nombre, pos, clase, vida=0.2, intocable=False, **extra):
    """Hace salir un pokemon de la pelea (main.py lo crea como enemigo que no da premios ni se amiga). None si no se puede."""
    if not ctx.get('invocar'): return None
    e = ctx['invocar'](nombre, pos, vida, intocable)
    if not e: return None
    m = dict({'e': e, 'clase': clase, 'nace': ctx['ahora']}, **extra)
    b['sj']['minions'].append(m)
    return m


def _sacar(m, humo=True):
    """El pokemon de la pelea se va (o se lo comieron)."""
    m['e']['vida'] = 0
    if not humo: m['e']['sin_humo'] = True


# ==================== preparar, actualizar y terminar ====================

def preparar(b, ent, ahora):
    """El subjefe recien creado: su estilo, su estado y lo que cambia en su sala."""
    n = b['nombre']
    D = SUBJEFES[n]
    b.update(estilo='sj_' + n, sj_nombre=n, titulo=D['titulo'])
    tam = ent['tam']
    filas, cols = len(ent['m']), len(ent['m'][0])
    b['sj'] = {'listo': {}, 'accion': None, 'libre_en': ahora + D['primer_mov'], 'ultimo': None, 'cola': [], 'proys': [], 'ondas': [],
               'minions': [], 'marcas': [], 'buffs': {}, 'mira': math.pi / 2, 'resto': [0.0, 0.0], 'anuncio': None, 'mec': {},
               'vida_ant': b['vida'], 'antes': {}, 'empuje': None, 'golpeado': False,
               'area': pygame.Rect(tam, tam, (cols - 2) * tam, (filas - 2) * tam)}
    PREPARAR.get(n, lambda b_, e_, a_: None)(b, ent, ahora)


def actualizar(b, ctx):
    """Cada frame: la mecanica de su sala, lo que dejo suelto y un movimiento por vez."""
    S, D, n = b['sj'], _datos(b), b['sj_nombre']
    j, ahora = ctx['jugador'], ctx['ahora']
    ia._rastrear(b, j, ahora)
    S['golpeado'] = b['vida'] < S['vida_ant'] - 0.5
    S['vida_ant'] = b['vida']
    b['mult_recibido'] = _buff(b, 'defensa', ahora) * S.get('mult_def', 1.0)
    S['minions'] = [m for m in S['minions'] if m['e']['vida'] > 0]
    MECANICAS[n](b, ctx)
    _actualizar_golpes(b, ctx)
    _actualizar_proys(b, ctx)
    _actualizar_ondas(b, ctx)
    _actualizar_empuje(b, ctx)
    S['marcas'] = [m for m in S['marcas'] if ahora < m['hasta']]
    if ctx.get('jefe_quieto') or ahora < b.get('aturdido_hasta', 0): return
    a = S['accion']
    if a:
        if MOVS[n][a['mov']](b, ctx, a): return
        _fin_accion(b, ahora, a['mov'])
        return
    if S['cola']:
        _empezar(b, ahora, S['cola'].pop(0)); return
    QUIETO[n](b, ctx)
    if ahora < S['libre_en'] or S.get('no_ataca'): return
    mov = ELEGIR.get(n, _elegir)(b, ctx)
    if mov: _empezar(b, ahora, mov)


def _empezar(b, ahora, mov):
    S = b['sj']
    S['accion'] = {'mov': mov}
    S['ultimo'] = mov
    if mov in NOMBRE_MOV: S['anuncio'] = (NOMBRE_MOV[mov], ahora)


def _fin_accion(b, ahora, mov):
    S, D = b['sj'], _datos(b)
    S['listo'][mov] = ahora + D['movs'].get(mov, {}).get('espera', 0)
    S['accion'] = None
    S['libre_en'] = ahora + random.randint(*D['pausa'])
    b.update(sin_contacto=False, escondido=False, invulnerable=False)
    if b['sj_nombre'] in FIN: FIN[b['sj_nombre']](b, ahora, mov)


def _elegir(b, ctx, puede=None, pesos=None):
    """Un movimiento al azar entre los que ya estan listos (no el mismo dos veces seguidas, salvo que sea el unico)."""
    S, ahora = b['sj'], ctx['ahora']
    listos = [m for m, d in _datos(b)['movs'].items() if not d.get('reaccion') and ahora >= S['listo'].get(m, 0) and (puede is None or puede(m))]
    if not listos: return None
    otros = [m for m in listos if m != S['ultimo']] or listos
    return random.choices(otros, [(pesos or {}).get(m, 1) for m in otros])[0]


def terminar(b, ctx):
    """Cayo el subjefe: se van sus pokemon, vuelve el piso que cambio y se te sacan sus efectos."""
    S, ent, j = b.get('sj'), ctx['ent'], ctx['jugador']
    if not S: return
    for m in S['minions']: _sacar(m)
    ocupadas, ent['ocupadas'] = ent['ocupadas'], set()
    for (f, c), t in S['antes'].items():
        if b['sj_nombre'] == 'cramorant': continue                 # los agujeros del hielo quedan
        entorno.cambiar(ent, f, c, t)
    ent['ocupadas'] = ocupadas
    limpiar_jugador(j)
    if b['sj_nombre'] == 'mamoswine' and ent.get('clima_hasta'): ent['clima'], ent['clima_hasta'] = ent['clima_base'], None
    S['proys'].clear(); S['ondas'].clear(); b['golpes'].clear()


def limpiar_jugador(j):
    """Le saca al jugador lo que le dejaron los subjefes (al terminar la pelea o al entrar a otra sala)."""
    fxj = j.get('fx_jefe') or {}
    for k in FX: fxj.pop(k, None)
    j['sj_recarga'] = 1.0
    j['polaridad'] = None
    j['atrapado_hasta'] = 0


# ----- lo que te hacen a vos (main.py lo usa al moverte, al pegar y al recargar) -----

def mult_vel(j, ahora):
    m = 1.0
    for k in ('sj_lento', 'sj_lento_leve', 'agua_lenta'):
        if ia.fx(j, k, ahora): m *= FX[k]
    return m


def mult_ataque(j, ahora):
    return FX['ataque_bajo'] if ia.fx(j, 'ataque_bajo', ahora) else 1.0


def mult_recarga(j, ahora):
    return j.get('sj_recarga', 1.0)


def alfa(b):
    """Transparencia del sprite del subjefe (Manto Niveo de Mamoswine, Armadura Acida de Muk). None: normal."""
    return b.get('sj', {}).get('alfa') if b else None


# ==================== Cramorant ====================

def _prep_cramorant(b, ent, ahora):
    S = b['sj']
    S['agujeros'] = []
    for f, c in _anillo(ent, SUBJEFES['cramorant']['agujeros']):
        _cambiar(b, ent, f, c, 'agua')
        S['agujeros'].append(_centro(ent, f, c))
    ent['objetos'][:] = [o for o in ent['objetos'] if not any(ent['m'][f][c] == 'agua' for f, c in o['celdas'])]
    S['bolsa'] = 0
    S['tragando'] = None
    S['buceo'] = None


def _mec_cramorant(b, ctx):
    S, M, D = b['sj'], b['sj']['mec'], SUBJEFES['cramorant']
    ahora = ctx['ahora']
    if 'prox_peces' not in M: M.update(prox_peces=ahora + 1200, prox_pika=ahora + D['pikachu'])
    peces = [m for m in S['minions'] if m['clase'] == 'pez']
    if ahora >= M['prox_peces']:                                    # de a 3 cada 3 s, por agujeros distintos
        M['prox_peces'] = ahora + D['cada']
        libres = min(D['de_a'], D['max_peces'] - len(peces), len(S['agujeros']))
        for hoyo in random.sample(S['agujeros'], max(0, libres)):
            if _invocar(b, ctx, 'arrokuda', hoyo, 'pez', D['vida_minion']): _marca(b, ahora, 'salpica', 450, pos=hoyo)
    if any(m['clase'] == 'pika' for m in S['minions']): M['prox_pika'] = ahora + D['pikachu']   # uno solo; el siguiente tarda 5 s
    elif ahora >= M['prox_pika'] and S['agujeros']:
        hoyo = random.choice(S['agujeros'])
        c = S['area'].center
        d = _d(hoyo, c) or 1
        orilla = (hoyo[0] + (c[0] - hoyo[0]) / d * 80, hoyo[1] + (c[1] - hoyo[1]) / d * 80)   # Pikachu no nada: sale a la orilla
        if _invocar(b, ctx, 'pikachu', orilla, 'pika', D['vida_minion']): _marca(b, ahora, 'salpica', 450, pos=hoyo)
        M['prox_pika'] = ahora + D['pikachu']
    destino = S['buceo'] or _bc(b)                                  # van hacia el (si bucea, se juntan donde esta)
    for m in S['minions']:
        e = m['e']
        if _d(e['rect'].center, destino) > 26:
            ia._mover_hacia(ctx['ent'], e, destino, D['vel_pika'] if m['clase'] == 'pika' else D['vel_pez'], [])
    T = S['tragando']
    if T:
        if S['golpeado']:                                           # le pegaste mientras tragaba: Reserva
            S['tragando'] = None
            _reserva(b, ctx)
        elif ahora >= T['hasta']:
            S['tragando'] = None
            if T['clase'] == 'pika': S['cola'].append('onda_electrica')
            else:
                S['bolsa'] = min(D['bolsa'], S['bolsa'] + 1)
                if S['bolsa'] >= D['bolsa']: S['cola'].append('tragamisil')
    elif not S['accion'] and not S['buceo']:                        # comer: el que lo toca
        for m in S['minions']:
            if m['e']['rect'].colliderect(b['rect'].inflate(16, 16)):
                _sacar(m, False)
                S['tragando'] = {'clase': m['clase'], 'hasta': ahora + D['traga'], 'inicio': ahora}
                ia._animar(b, ('eat', 'charge', 'attack'), ahora, D['traga'])
                _mensaje(b, '¡Cramorant se tragó a ' + ('Pikachu!' if m['clase'] == 'pika' else 'un Arrokuda!') + ' Pegale antes de 1,5 s', 1400)
                break


def _reserva(b, ctx):
    """Le pegaste mientras se tragaba algo: segun cuantos tenia guardados."""
    S, D, ahora = b['sj'], SUBJEFES['cramorant'], ctx['ahora']
    n = S['bolsa']
    S['anuncio'] = ('Reserva', ahora)
    if n == 0:
        S['buffs']['defensa'] = (D['defensa']['mult'], ahora + D['defensa']['dura'])
        A = S['area']
        lejos = max(_d(_bc(b), p) for p in (A.topleft, A.topright, A.bottomleft, A.bottomright))
        _onda(b, ahora, _bc(b), D['defensa']['onda'], lejos, D['defensa']['grosor'], 0, 'normal', 'sj_lento', D['defensa']['lento'],
              (220, 220, 255), 'El grito de Cramorant te frenó')
        _mensaje(b, 'Reserva: Cramorant subió su defensa y gritó', 1500)
    elif n == 1:
        S['buffs']['ataque'] = (D['furia']['ataque'], ahora + D['furia']['dura'])
        S['buffs']['vel'] = (D['furia']['vel'], ahora + D['furia']['dura'])
        _mensaje(b, 'Reserva: Cramorant subió su ataque y su velocidad', 1500)
    else:
        E = D['escupe']
        for i in range(n * E['por_pez']):
            _golpe(b, ahora + i * E['cada'], 'circulo', E['aviso'], 'agua', E['daño'], pos=_punto_libre(b, ctx), radio=E['radio'],
                   dibujo='pez', temblor=150)
        S['bolsa'] = 0
        _mensaje(b, 'Reserva: ¡Cramorant escupió los Arrokuda para arriba!', 1500)
    ctx['impacto'](*_bc(b), 60, 250)


def _quieto_cramorant(b, ctx):
    S, ahora = b['sj'], ctx['ahora']
    if S['tragando']: return
    peces = [m['e'] for m in S['minions']]
    if peces:
        cerca = min(peces, key=lambda e: _d(e['rect'].center, _bc(b)))
        if _d(cerca['rect'].center, _bc(b)) < 520: _ir(b, ctx, cerca['rect'].center, _vel(b, ahora)); return
    _acercar(b, ctx, 260, _vel(b, ahora))


def _elegir_cramorant(b, ctx):
    if b['sj']['tragando']: return None
    return _elegir(b, ctx)


def _mov_buceo(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'buceo')
    j = ctx['jugador']
    if 't0' not in a:
        a.update(t0=ahora, pos=_bc(b))
        b.update(escondido=True, invulnerable=True, sin_contacto=True)
        S['buceo'] = a['pos']
        _marca(b, ahora, 'salpica', 500, pos=a['pos'])
        ctx['impacto'](*a['pos'], 50, 200)
    if ahora < a['t0'] + D['dura']:
        tx, ty = ia._pos_anterior(b, j, ahora, D['retraso'])
        x, y = a['pos']
        d = math.hypot(tx - x, ty - y)
        if d > 1: x, y = x + (tx - x) / d * min(d, D['vel']), y + (ty - y) / d * min(d, D['vel'])
        A = S['area'].inflate(-b['rect'].width, -b['rect'].height)
        a['pos'] = (max(A.left, min(A.right, x)), max(A.top, min(A.bottom, y)))
        S['buceo'] = a['pos']
        return True
    if 'sale' not in a:
        a['sale'] = ahora
        _golpe(b, ahora, 'circulo', D['aviso'], 'agua', D['daño'], pos=a['pos'], radio=D['radio'], temblor=300)
    if ahora < a['sale'] + D['aviso']: return True
    _poner(b, a['pos'])
    S['buceo'] = None
    _marca(b, ahora, 'salpica', 600, pos=_bc(b), grande=True)
    ia._animar(b, ('attack', 'hop'), ahora, 500)
    return False


def _mov_picotaladro(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'picotaladro')
    if 't0' not in a:
        ang = _ang(_bc(b), _jc(ctx))
        a.update(t0=ahora, dir=_v(ang), restante=D['largo'], etapa='aviso')
        ia._animar(b, ('charge', 'attack'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        if ahora < a['t0'] + D['aviso']: return True
        a['etapa'] = 'dash'
    r = _dash(b, ctx, a, D['vel'] * _buff(b, 'vel', ahora), D['daño'], 'volador', 10)
    if a.get('acerto') and not a.get('robo'):
        a['robo'] = True
        _robar_baya(b, ctx, D['cura'])
    return r == 'sigue'


def _robar_baya(b, ctx, cura):
    """Picotaladro: si tenes una baya en el lugar 1 del cinturon, te la roba y se cura segun lo que cura la baya."""
    j = ctx['jugador']
    cinturon = (j.get('inventario') or {}).get('cinturon') or []
    if not cinturon or not str(cinturon[0]).startswith('baya_'): return
    clave = cinturon.pop(0)
    item = tienda.ITEMS.get(clave, {})
    ps = (item.get('curativo') or {}).get('ps') or 0
    if not isinstance(ps, (int, float)): ps = 30
    b['vida'] = min(b['max_vida'], b['vida'] + round(b['max_vida'] * (0.03 + ps * cura / 100)))
    b['sj']['vida_ant'] = b['vida']
    _mensaje(b, '¡Cramorant te robó la ' + item.get('nombre', 'baya') + ' y se curó!', 1800)


def _mov_tragamisil(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'tragamisil')
    if 't0' not in a:
        a.update(t0=ahora, ang=_ang(_bc(b), _jc(ctx)))
        ia._animar(b, ('charge', 'shoot'), ahora, D['aviso'] + 300)
    if ahora < a['t0'] + D['aviso']:
        a['ang'] = ia._girar_hacia(a['ang'], _ang(_bc(b), _jc(ctx)), 0.05)
        return True
    dx, dy = _v(a['ang'])
    px, py = -dy, dx
    bx, by = _bc(b)
    s = D['separa']
    for ox, oy in ((dx * s, dy * s), (-dx * s * 0.6 + px * s, -dy * s * 0.6 + py * s), (-dx * s * 0.6 - px * s, -dy * s * 0.6 - py * s)):
        _bala(b, ahora, (bx + ox, by + oy), a['ang'], D['vel'], D['radio'], D['daño'], 'agua', 'pez', D['dist'])
    S['bolsa'] = 0
    ctx['impacto'](bx, by, 50, 200)
    return False


def _mov_onda_electrica(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'onda_electrica')
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('charge', 'shock'), ahora, D['aviso'] + 300)
    if ahora < a['t0'] + D['aviso']: return True
    _onda(b, ahora, _bc(b), D['dura'], D['radio'], D['grosor'], D['daño'], 'electrico', 'paralisis', D['paraliza'], (255, 230, 60))
    ctx['impacto'](*_bc(b), 70, 250)
    return False


# ==================== Mamoswine ====================

def _prep_mamoswine(b, ent, ahora):
    b['sj'].update(anillo=0, pendientes=set(), alud=None)


def _mec_mamoswine(b, ctx):
    S, M, D = b['sj'], b['sj']['mec'], SUBJEFES['mamoswine']
    ent, ahora = ctx['ent'], ctx['ahora']
    N = D['nevada']
    if 'prox' not in M: M['prox'] = ahora + N['primera']
    if ahora >= M['prox']:                                          # empieza a nevar: Manto Niveo
        M['prox'] = ahora + N['cada']
        entorno.iniciar_clima(ent, 'nieve', ahora, N['dura'])
        _mensaje(b, 'Nieva: Mamoswine se camufla con Manto Níveo', 1600)
    S['alfa'] = N['alfa'] if ent.get('clima') in ('nieve', 'granizo') else None
    if S['pendientes'] and ahora >= M.get('prox_grieta', 0):        # el hielo que no se pudo romper porque alguien estaba encima
        M['prox_grieta'] = ahora + 300
        _romper_casillas(b, ctx, list(S['pendientes']))


def _romper_casillas(b, ctx, casillas):
    S, ent, j = b['sj'], ctx['ent'], ctx['jugador']
    ocupadas = ent['ocupadas']
    ent['ocupadas'] = set(entorno._casillas_rect(ent, j['rect'].inflate(10, 10))) | set(entorno._casillas_rect(ent, b['rect'].inflate(10, 10)))
    rotas = set()
    for f, c in casillas:
        if (f, c) in ent['ocupadas']: S['pendientes'].add((f, c)); continue
        S['pendientes'].discard((f, c))
        if ent['m'][f][c] in ('pared', 'puerta', 'entrada', 'agua'): continue
        if _cambiar(b, ent, f, c, 'agua'): rotas.add((f, c))
    ent['ocupadas'] = ocupadas
    if rotas:
        caen = [o for o in ent['objetos'] if set(o['celdas']) & rotas]
        for o in caen: ent['objetos'].remove(o)
        if caen: ent['version'] += 1
        for f, c in list(rotas)[::3]: _marca(b, ctx['ahora'], 'grieta', 700, pos=_centro(ent, f, c))


def _romper_anillo(b, ctx):
    """Hielo que se agrieta: el borde de la sala se rompe y queda agua (la sala se achica, hasta un minimo)."""
    S, ent, D = b['sj'], ctx['ent'], SUBJEFES['mamoswine']
    filas, cols = len(ent['m']), len(ent['m'][0])
    k = S['anillo'] + 1
    if cols - 2 * (k + 1) < D['minimo'][0] or filas - 2 * (k + 1) < D['minimo'][1]: return False
    S['anillo'] = k
    casillas = [(f, c) for f in range(k, filas - k) for c in range(k, cols - k) if f in (k, filas - 1 - k) or c in (k, cols - 1 - k)]
    _romper_casillas(b, ctx, casillas)
    tam = ent['tam']
    S['area'] = pygame.Rect((k + 1) * tam, (k + 1) * tam, (cols - 2 * (k + 1)) * tam, (filas - 2 * (k + 1)) * tam)
    _mensaje(b, '¡El hielo se agrieta! La sala se achica', 1500)
    return True


def _quieto_mamoswine(b, ctx):
    _acercar(b, ctx, 220, _vel(b, ctx['ahora']))


def _elegir_mamoswine(b, ctx):
    return _elegir(b, ctx, pesos={'fuerza_equina': 1.3})


def _rocas_mamoswine(b, ctx, cantidad, cada):
    """Poder Pasado: rocas que esperan alrededor suyo y salen de a una hacia donde estas."""
    ahora, D = ctx['ahora'], _md(b, 'poder_pasado')
    for i in range(cantidad):
        _bala(b, ahora, _bc(b), 0, D['vel'], D['radio'], D['daño'], 'roca', 'roca', 1100, sale=ahora + D['aviso'] + i * cada, orbita=i,
              de=cantidad)


def _mov_fuerza_equina(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'fuerza_equina')
    if 't0' not in a: a.update(t0=ahora, i=0, etapa=None)
    if a['etapa'] is None:
        if a['i'] >= D['veces']: return False
        a.update(etapa='aviso', desde=ahora, dir=_v(_ang(_bc(b), _jc(ctx))), restante=D['largo'], pego=False, acerto=False)
        ia._animar(b, ('charge', 'walk'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        if ahora < a['desde'] + D['aviso']: return True
        a['etapa'] = 'dash'
    if a['etapa'] == 'dash':
        r = _dash(b, ctx, a, D['vel'], D['daño'], 'tierra', 12)
        if r == 'sigue': return True
        ctx['impacto'](*_bc(b), 70, 250)
        a.update(etapa='pausa', desde=ahora)
        if a['i'] < D['veces'] - 1 and random.random() < D['rocas']: _rocas_mamoswine(b, ctx, 2, 260)
    if a['etapa'] == 'pausa':
        if ahora < a['desde'] + D['entre']: return True
        a['i'] += 1; a['etapa'] = None
    return True


def _mov_terratemblor(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'terratemblor')
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('rearup', 'charge', 'attack'), ahora, D['aviso'])
        _marca(b, ahora, 'temblor', D['aviso'], pos=_bc(b), radio=D['radio'])
    if ahora < a['t0'] + D['aviso']: return True
    d = _d(_bc(b), _jc(ctx))
    k = max(0.0, 1 - d / D['radio'])
    _pegar(b, ctx, D['daño_min'] + (D['daño_max'] - D['daño_min']) * k, 'tierra')
    ctx['impacto'](*_bc(b), 220, 800)
    _romper_anillo(b, ctx)
    return False


def _cubierto(ctx, viento, largo):
    """Alud: si entre vos y de donde viene el viento hay algo (un objeto o una pared de adentro) que te tapa."""
    ent, j = ctx['ent'], ctx['jugador']
    p = j['rect'].center
    q = (p[0] - viento[0] * largo, p[1] - viento[1] * largo)
    tapan = [o['rect'] for o in ent['objetos'] if o['solido']]
    if any(r.clipline(p, q) for r in tapan): return True
    pasos = int(largo // 20)
    for i in range(2, pasos + 1):                                   # paredes de adentro (no las del borde de la sala)
        x, y = p[0] - viento[0] * 20 * i, p[1] - viento[1] * 20 * i
        f, c = entorno.casilla(ent, x, y)
        if 0 < f < len(ent['m']) - 1 and 0 < c < len(ent['m'][0]) - 1 and ent['m'][f][c] == 'pared': return True
    return False


def _mov_alud(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'alud')
    j = ctx['jugador']
    if 't0' not in a:
        a.update(t0=ahora, viento=random.choice(((1, 0), (-1, 0), (0, 1), (0, -1))), pego=False)
        S['alud'] = a
        ia._animar(b, ('rearup', 'charge'), ahora, D['aviso'])
        _mensaje(b, '¡Alud! Cubrite detrás de algo', 1200)
    if ahora < a['t0'] + D['aviso']: return True
    if 'sopla' not in a: a['sopla'] = ahora; ctx['impacto'](*j['rect'].center, 40, 300)
    if not a['pego'] and not ia._esquivando(j, ahora) and not _cubierto(ctx, a['viento'], D['cubre']):
        a['pego'] = True
        _pegar(b, ctx, D['daño'], 'hielo')
    if ahora < a['sopla'] + D['dura']: return True
    S['alud'] = None
    return False


def _mov_poder_pasado(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'poder_pasado')
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('charge', 'rotate'), ahora, D['aviso'] + D['rocas'] * D['cada'])
        _rocas_mamoswine(b, ctx, D['rocas'], D['cada'])
    return ahora < a['t0'] + D['aviso'] + D['rocas'] * D['cada']


def _proys_que_esperan(b, ctx):
    """Las rocas de Poder Pasado: giran alrededor de Mamoswine hasta que les toca salir, y salen hacia donde estas."""
    S, ahora = b['sj'], ctx['ahora']
    D = _md(b, 'poder_pasado')
    for p in S['proys']:
        if 'orbita' not in p: continue
        if ahora < p['sale']:
            ang = ahora / 300 + p['orbita'] * math.tau / p['de']
            p['pos'] = (b['rect'].centerx + math.cos(ang) * D['orbita'], b['rect'].centery + math.sin(ang) * D['orbita'] * 0.8)
        elif not p.get('salio'):
            p['salio'] = True
            p['ang'] = _ang(p['pos'], _jc(ctx))


# ==================== Tyrantrum ====================

def _prep_tyrantrum(b, ent, ahora):
    b['sj'].update(cono=[], visto=False, ultimo_visto=None, meta=None, prox_meta=0, quieto_desde=None, danza=0, boca=None)


def _tapan_vista(ent, S):
    """Casillas que cortan la vista de Tyrantrum (paredes y objetos solidos). Se rehace solo si cambia la sala."""
    if S.get('vista_version') != ent['version']:
        malas = {(f, c) for f, fila in enumerate(ent['m']) for c, t in enumerate(fila) if mundos.TERRENOS[t].get('solido')}
        for o in ent['objetos']:
            if o['solido']: malas |= set(o['celdas'])
        S['vista_malas'], S['vista_version'] = malas, ent['version']
    return S['vista_malas']


def _rayo_vista(malas, tam, origen, ang, largo, paso=16):
    dx, dy = _v(ang)
    x, y = origen
    d = 0
    while d < largo:
        nx, ny = x + dx * paso, y + dy * paso
        if (int(ny // tam), int(nx // tam)) in malas: break
        x, y = nx, ny; d += paso
    return x, y


def _mec_tyrantrum(b, ctx):
    S, D = b['sj'], SUBJEFES['tyrantrum']
    ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
    V = D['vision']
    malas = _tapan_vista(ent, S)
    o = _bc(b)
    S['cono'] = [o] + [_rayo_vista(malas, ent['tam'], o, S['mira'] - V['apertura'] / 2 + V['apertura'] * i / V['rayos'], V['radio'])
                       for i in range(V['rayos'] + 1)]
    p = j['rect'].center
    adentro = _d(o, p) <= V['radio'] + _mitad(j) and ia._en_poligono(p, S['cono'])
    quieto = not j.get('moviendose') and not j.get('esquive') and not j.get('embestida') and not j.get('atacando')
    if adentro and quieto:                                          # quieto en su vista: 1 s sin saber donde estas
        if S['quieto_desde'] is None: S['quieto_desde'] = ahora
        visto = ahora - S['quieto_desde'] >= V['quieto']
    else:
        S['quieto_desde'] = None
        visto = adentro
    if visto and not S['visto']: S['entro'] = ahora                 # recien te vio
    S['visto'] = visto
    if visto: S['ultimo_visto'] = p
    n = S['danza']
    S['mult_vel'] = 1 + _md(b, 'danza_dragon')['vel'] * n
    S['mult_ataque'] = 1 + _md(b, 'danza_dragon')['ataque'] * n


def _mirar(b, hacia, giro):
    b['sj']['mira'] = ia._girar_hacia(b['sj']['mira'], _ang(_bc(b), hacia), giro)


def _quieto_tyrantrum(b, ctx):
    S, D, ahora = b['sj'], SUBJEFES['tyrantrum'], ctx['ahora']
    vel = _vel(b, ahora)
    antes = _bc(b)
    if S['visto']:
        _mirar(b, _jc(ctx), D['vision']['giro'])
        if _d(antes, _jc(ctx)) > 150: _ir(b, ctx, _jc(ctx), vel)
        return
    if S['ultimo_visto']:                                           # va a donde te vio por ultima vez
        if _d(antes, S['ultimo_visto']) < 50: S['ultimo_visto'] = None
        else: _ir(b, ctx, S['ultimo_visto'], vel)
    else:                                                           # no sabe donde estas: camina para cualquier lado
        if not S['meta'] or _d(antes, S['meta']) < 60 or ahora >= S['prox_meta']:
            S['meta'] = entorno.punto_libre(ctx['ent'], random)
            S['prox_meta'] = ahora + random.randint(*D['paseo'])
        _ir(b, ctx, S['meta'], vel * 0.75)
    ahora_c = _bc(b)
    if _d(antes, ahora_c) > 0.5: _mirar(b, (ahora_c[0] * 2 - antes[0], ahora_c[1] * 2 - antes[1]), D['vision']['giro'])


def _elegir_tyrantrum(b, ctx):
    S, ahora = b['sj'], ctx['ahora']
    listo = lambda m: ahora >= S['listo'].get(m, 0)
    d = _d(_bc(b), _jc(ctx))
    atras = abs(_dif(_ang(_bc(b), _jc(ctx)), S['mira'])) > math.radians(100)
    if d <= _md(b, 'cola_dragon')['cerca'] and atras and listo('cola_dragon'): return 'cola_dragon'
    if S['visto']:
        if d <= _md(b, 'triple_colmillo')['cerca'] and listo('triple_colmillo'): return 'triple_colmillo'
        if d > 330 and listo('testarazo'): return 'testarazo'
        if listo('triple_colmillo'): return 'triple_colmillo'
        return None
    if listo('danza_dragon') and S['danza'] < _md(b, 'danza_dragon')['max']: return 'danza_dragon'
    return None


def _fin_tyrantrum(b, ahora, mov):
    if mov != 'danza_dragon': b['sj']['danza'] = 0                  # atacar gasta la Danza Dragon


def _mov_triple_colmillo(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'triple_colmillo')
    if 't0' not in a:
        clave = random.choice(list(SUBJEFES['tyrantrum']['colmillos']))
        a.update(t0=ahora, colmillo=clave, etapa='aviso')
        S['boca'] = clave
        S['anuncio'] = (SUBJEFES['tyrantrum']['colmillos'][clave][0], ahora)
        ia._animar(b, ('charge', 'bite', 'attack'), ahora, D['aviso'])
    nombre, color, tipo, ef, ms = SUBJEFES['tyrantrum']['colmillos'][a['colmillo']]
    if a['etapa'] == 'aviso':
        _mirar(b, _jc(ctx), 0.12)
        if ahora < a['t0'] + D['aviso']: return True
        a.update(etapa='dash', dir=_v(S['mira']), restante=D['largo'], pego=True)
    if a['etapa'] == 'dash':
        r = _dash(b, ctx, a, D['vel'] * _buff(b, 'vel', ahora) * S.get('mult_vel', 1.0), 0, tipo)
        if r == 'sigue' and _d(_bc(b), _jc(ctx)) > D['radio'] + 40: return True
        pos = (b['rect'].centerx + a['dir'][0] * 70, b['rect'].centery + a['dir'][1] * 70)
        ia._golpe(b, ahora, 'circulo', 120, tipo, 0, 200, pos=pos, radio=D['radio'], dibujo='mordida')
        a.update(etapa='muerde', desde=ahora, pos=pos)
        ia._animar(b, ('bite', 'attack'), ahora, 400)
    if a['etapa'] == 'muerde':
        if ahora < a['desde'] + 120: return True
        if not a.get('mordio'):
            a['mordio'] = True
            S['boca'] = None
            if _d(a['pos'], _jc(ctx)) <= D['radio'] + _mitad(ctx['jugador']):
                if _pegar(b, ctx, D['daño'], tipo, ef, ms) > 0: _mensaje(b, nombre + ': ¡qué mordida!', 1000)
            ctx['impacto'](*a['pos'], 60, 250)
        return ahora < a['desde'] + 350
    return True


def _mov_danza_dragon(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'danza_dragon')
    if 't0' not in a:
        a['t0'] = ahora
        S['danza'] = min(D['max'], S['danza'] + 1)
        ia._animar(b, ('rotate', 'charge', 'pose'), ahora, D['dura'])
        _marca(b, ahora, 'aura', D['dura'], color=(150, 90, 255))
    return ahora < a['t0'] + D['dura']


def _mov_testarazo(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'testarazo')
    if 't0' not in a:
        a.update(t0=ahora, etapa='aviso')
        ia._animar(b, ('charge', 'walk'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        _mirar(b, _jc(ctx), 0.1)
        a['dir'] = _v(S['mira'])
        if ahora < a['t0'] + D['aviso']: return True
        a.update(etapa='dash', restante=D['largo'])
    r = _dash(b, ctx, a, D['vel'] * S.get('mult_vel', 1.0), D['daño'], 'roca', 12)
    if r == 'sigue' and not a.get('pego'): return True
    if a.get('pego') or r == 'choco':                               # el golpe tambien lo lastima a el
        b['vida'] = max(1, b['vida'] - round(b['max_vida'] * D['propio']))
        S['vida_ant'] = b['vida']
        ctx['impacto'](*_bc(b), 70, 350)
        if r == 'choco':
            b['aturdido_hasta'] = ahora + D['aturdido']
            _mensaje(b, 'Tyrantrum se dio la cabeza contra la pared', 1200)
    return False


def _mov_cola_dragon(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'cola_dragon')
    if 't0' not in a:
        a.update(t0=ahora, atras=S['mira'] + math.pi)
        ia._golpe(b, ahora, 'poligono', D['aviso'], 'dragon', 0, 200, puntos=_arco(_bc(b), a['atras'], math.pi, D['radio']))
        ia._animar(b, ('swing', 'attack'), ahora, D['aviso'] + 300)
    if ahora < a['t0'] + D['aviso']: return True
    p = _jc(ctx)
    if _d(p, _bc(b)) <= D['radio'] + _mitad(ctx['jugador']) and abs(_dif(_ang(_bc(b), p), a['atras'])) <= math.pi / 2:
        if _pegar(b, ctx, D['daño'], 'dragon') > 0: _empujar(b, _v(_ang(_bc(b), p)), 12, D['empuje'])
    ctx['impacto'](b['rect'].centerx + math.cos(a['atras']) * 110, b['rect'].centery + math.sin(a['atras']) * 110, 60, 250)
    return False


# ==================== Armaldo ====================

def _prep_armaldo(b, ent, ahora):
    b['sj'].update(agua={}, piedras=[], armadura_hasta=0)


def _mec_armaldo(b, ctx):
    S, D = b['sj'], SUBJEFES['armaldo']
    ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
    for k in [k for k, hasta in S['agua'].items() if ahora >= hasta]: del S['agua'][k]
    if entorno.casilla(ent, *j['rect'].center) in S['agua'] and not ia._esquivando(j, ahora): ia.poner_fx(j, 'agua_lenta', ahora, 150)
    S['mult_vel'] = D['agua']['rapido'] if entorno.casilla(ent, *_bc(b)) in S['agua'] else 1.0
    S['mult_def'] = D['armadura']['mult'] if ahora < S['armadura_hasta'] else 1.0
    Tr = _md(b, 'trampa_rocas')
    for p in S['piedras'][:]:                                       # Trampa Rocas: si pisas una te lastima y se rompe
        if ahora < p['listo']: continue
        if _d(p['pos'], j['rect'].center) <= Tr['radio'] + _mitad(j) * 0.7 and not ia._esquivando(j, ahora):
            S['piedras'].remove(p)
            _pegar(b, ctx, Tr['daño'], 'roca')
            _marca(b, ahora, 'chispa', 300, pos=p['pos'])


def _quieto_armaldo(b, ctx):
    _acercar(b, ctx, 210, _vel(b, ctx['ahora']))


def _elegir_armaldo(b, ctx):
    d = _d(_bc(b), _jc(ctx))
    return _elegir(b, ctx, lambda m: m != 'cortefuria' or d <= _md(b, 'cortefuria')['cerca'], {'cortefuria': 1.6})


def _mov_pin_misil(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'pin_misil')
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('charge', 'shoot'), ahora, D['aviso'] + 300)
    if ahora < a['t0'] + D['aviso']: return True
    base = _ang(_bc(b), _jc(ctx))
    for i in range(D['pinchos']):
        _bala(b, ahora, _bc(b), base + i * math.tau / D['pinchos'] + random.uniform(-0.08, 0.08), D['vel'] * random.uniform(0.85, 1.1),
              D['radio'], D['daño'], 'bicho', 'pincho', 99999, D['dura'], rebota=True)
    return False


def _mov_cortefuria(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'cortefuria')
    if 't0' not in a: a.update(t0=ahora, i=0, prox=ahora)
    if a['i'] >= 3: return ahora < a['prox']
    if ahora < a['prox']: return True
    ang = _ang(_bc(b), _jc(ctx))
    dx, dy = _v(ang)
    _paso(b, ctx, dx, dy, D['avance'])
    c = _bc(b)
    aviso = D['avisos'][a['i']]
    if a['i'] < 2:
        _golpe(b, ahora, 'poligono', aviso, 'bicho', D['daños'][a['i']], 160, puntos=_arco(c, ang, 2.1 + 0.3 * a['i'], D['radios'][a['i']]))
    else:                                                           # la X: dos cortes cruzados un poco adelante
        m = (c[0] + dx * 90, c[1] + dy * 90)
        for giro in (math.pi / 4, -math.pi / 4):
            ex, ey = _v(ang + giro)
            L = D['largo_x'] / 2
            _golpe(b, ahora, 'linea', aviso, 'bicho', D['daños'][2] / 2, 160, a=(m[0] - ex * L, m[1] - ey * L), b=(m[0] + ex * L, m[1] + ey * L),
                   ancho=D['ancho_x'], dibujo='tajo')
    ia._animar(b, ('scratch', 'attack', 'swing'), ahora, aviso + 150)
    a['prox'] = ahora + aviso + 150
    a['i'] += 1
    return True


def _mov_trampa_rocas(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'trampa_rocas')
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('charge', 'rearup'), ahora, D['quieto'])
    if ahora < a['t0'] + D['quieto']: return True
    for _ in range(D['piedras']):
        p = _punto_libre(b, ctx, 70)
        ia._golpe(b, ahora, 'circulo', D['aviso'], 'roca', 0, 100, pos=p, radio=D['radio'] + 6, dibujo='cae', objeto='roca')
        S['piedras'].append({'pos': p, 'listo': ahora + D['aviso']})
    S['piedras'] = S['piedras'][-D['max']:]
    S['armadura_hasta'] = ahora + SUBJEFES['armaldo']['armadura']['dura']    # Armadura de Fosil
    _mensaje(b, 'Armadura de Fósil: Armaldo recibe menos daño', 1200)
    return False


def _mov_giro_rapido(b, ctx, a):
    S, ent, ahora, D = b['sj'], ctx['ent'], ctx['ahora'], _md(b, 'giro_rapido')
    if 't0' not in a:
        a.update(t0=ahora, dir=list(_v(_ang(_bc(b), _jc(ctx)))))
        ia._animar(b, ('rotate', 'charge'), ahora, D['aviso'] + D['dura'])
    if ahora < a['t0'] + D['aviso']: return True
    if ahora >= a['t0'] + D['aviso'] + D['dura']: return False
    b['sj']['girando'] = ahora + 100
    cx_, cy_ = _paso(b, ctx, a['dir'][0], a['dir'][1], D['vel'] * S.get('mult_vel', 1.0))
    if cx_: a['dir'][0] = -a['dir'][0]
    if cy_: a['dir'][1] = -a['dir'][1]
    if cx_ or cy_: ctx['impacto'](*_bc(b), 30, 120)
    for k in entorno._casillas_rect(ent, b['rect'].inflate(-30, -30)):   # deja agua prehistorica por donde pasa
        S['agua'][k] = ahora + SUBJEFES['armaldo']['agua']['dura']
    S['piedras'] = [p for p in S['piedras'] if _d(p['pos'], _bc(b)) > max(b['rect'].size) / 2 + 10]   # y rompe las piedras
    if _toca_b(b, ctx):
        _pegar(b, ctx, D['daño'], 'roca')
        ctx['impacto'](*_bc(b), 60, 250)
        return False                                                # te pego: se frena
    return True


# ==================== Scizor ====================

def _prep_scizor(b, ent, ahora):
    b['sj'].update(calor=None)


def _mec_scizor(b, ctx):
    S, D = b['sj'], SUBJEFES['scizor']
    j, ahora = ctx['jugador'], ctx['ahora']
    if S['calor'] and ahora < S['calor']:                           # el aleteo te empuja para atras
        bx, by = _bc(b)
        dx, dy = j['rect'].centerx - bx, j['rect'].centery - by
        d = math.hypot(dx, dy) or 1
        if d < D['calor']['radio']:
            k = D['calor']['fuerza'] * (1 - d / D['calor']['radio'] * 0.5)
            _tirar_jugador(b, ctx, dx / d * k, dy / d * k)


def _ataques_listos(b, ahora):
    S = b['sj']
    return [m for m in ('puño_bala', 'ida_y_vuelta') if ahora >= S['listo'].get(m, 0)]


def _quieto_scizor(b, ctx):
    S, D, ahora = b['sj'], SUBJEFES['scizor'], ctx['ahora']
    vel = _vel(b, ahora)
    if _ataques_listos(b, ahora): _acercar(b, ctx, 300, vel)
    elif _d(_bc(b), _jc(ctx)) < D['lejos']: _ir(b, ctx, _jc(ctx), vel, True)   # se aleja mientras recarga


def _elegir_scizor(b, ctx):
    S, ahora = b['sj'], ctx['ahora']
    listos = _ataques_listos(b, ahora)
    d = _d(_bc(b), _jc(ctx))
    if 'ida_y_vuelta' in listos and d > _md(b, 'ida_y_vuelta')['largo'] + 80: listos.remove('ida_y_vuelta')
    if listos: return random.choice(listos)
    apoyo = [m for m in ('agilidad', 'danza_espada') if ahora >= S['listo'].get(m, 0)]
    return random.choice(apoyo) if apoyo else None


def _fin_scizor(b, ahora, mov):
    if mov in ('puño_bala', 'ida_y_vuelta'): b['sj']['cola'].append('sobrecalentamiento')


def _ondas_pinzas(b, ctx):
    """Pinzas con ojos falsos: choca las pinzas y salen 2 ondas que confunden."""
    ahora, O = ctx['ahora'], SUBJEFES['scizor']['ondas']
    base = _ang(_bc(b), _jc(ctx))
    for lado in (-1, 1):
        _bala(b, ahora, _bc(b), base + lado * O['abanico'], O['vel'], O['radio'], 0, 'bicho', 'ojos', O['dist'], ef='confusion', ms=O['confusion'],
              aviso_ef='¡Las pinzas te confundieron!')


def _mov_danza_espada(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'danza_espada')
    if 't0' not in a:
        a['t0'] = ahora
        S['buffs']['ataque'] = (D['ataque'], ahora + D['dura'])
        ia._animar(b, ('rotate', 'swing', 'pose'), ahora, D['anim'])
        _marca(b, ahora, 'aura', D['dura'], color=(255, 90, 70))
        _ondas_pinzas(b, ctx)
    return ahora < a['t0'] + D['anim']


def _mov_agilidad(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'agilidad')
    if 't0' not in a:
        a['t0'] = ahora
        S['buffs']['vel'] = (D['vel'], ahora + D['dura'])
        ia._animar(b, ('rotate', 'pose'), ahora, D['anim'])
        _marca(b, ahora, 'aura', D['dura'], color=(120, 220, 255))
        _ondas_pinzas(b, ctx)
    return ahora < a['t0'] + D['anim']


def _mov_puño_bala(b, ctx, a):
    S, ent, ahora, D = b['sj'], ctx['ent'], ctx['ahora'], _md(b, 'puño_bala')
    if 't0' not in a:
        a.update(t0=ahora, i=0, prox=ahora + 180)
        _marca(b, ahora, 'destello', 350, pos=_bc(b))
        j = ctx['jugador']
        duros = entorno.solidos(ent, entorno.tipos_de(b))
        base = random.uniform(0, math.tau)
        for k in range(10):                                         # aparece al lado tuyo, donde entre
            ang = base + k * math.tau / 10
            r = b['rect'].copy()
            r.center = (round(j['rect'].centerx + math.cos(ang) * D['lado']), round(j['rect'].centery + math.sin(ang) * D['lado']))
            if r.collidelist(duros) == -1 and S['area'].contains(r):
                b['rect'].center = r.center; break
        _marca(b, ahora, 'destello', 350, pos=_bc(b))
    if a['i'] >= D['golpes']: return ahora < a['prox']
    if ahora < a['prox']: return True
    ang = _ang(_bc(b), _jc(ctx))
    c = (b['rect'].centerx + math.cos(ang) * 55, b['rect'].centery + math.sin(ang) * 55)
    _golpe(b, ahora, 'circulo', D['aviso'], 'acero', D['daño'], 120, pos=c, radio=D['radio'], dibujo='puño')
    ia._animar(b, ('attack', 'punch', 'swing'), ahora, D['aviso'] + 100)
    a['i'] += 1
    a['prox'] = ahora + D['aviso'] + D['entre']
    return True


def _mov_ida_y_vuelta(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'ida_y_vuelta')
    if 't0' not in a:
        a.update(t0=ahora, etapa='aviso', origen=_bc(b), dir=_v(_ang(_bc(b), _jc(ctx))))
        ia._animar(b, ('charge', 'walk'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        a['dir'] = _v(_ang(_bc(b), _jc(ctx)))
        if ahora < a['t0'] + D['aviso']: return True
        dist = min(D['largo'], _d(_bc(b), _jc(ctx)) + 40)
        a.update(etapa='dash', restante=dist)
    if a['etapa'] == 'dash':
        vel = D['vel'] * (D['rapido'] if _buff(b, 'vel', ahora) > 1 else 1)
        r = _dash(b, ctx, a, vel, D['daño'], 'bicho', 8)
        if r == 'sigue' and not a.get('pego'): return True
        if a.get('acerto'): a['etapa'] = 'vuelta'                   # te pego: vuelve
        else:
            ang = _ang(_bc(b), _jc(ctx))
            c = (b['rect'].centerx + math.cos(ang) * 50, b['rect'].centery + math.sin(ang) * 50)
            _golpe(b, ahora, 'circulo', D['aviso_golpe'], 'bicho', D['daño_golpe'], 120, pos=c, radio=D['radio'])
            ia._animar(b, ('attack', 'scratch'), ahora, D['aviso_golpe'] + 100)
            a.update(etapa='golpe', desde=ahora)
    if a['etapa'] == 'golpe':
        if ahora < a['desde'] + D['aviso_golpe'] + 120: return True
        a['etapa'] = 'vuelta'
    if a['etapa'] == 'vuelta':                                      # vuelve a donde estaba
        d = _d(_bc(b), a['origen'])
        if d <= D['vuelta']: _poner(b, a['origen']); return False
        dx, dy = (a['origen'][0] - b['rect'].centerx) / d, (a['origen'][1] - b['rect'].centery) / d
        cx_, cy_ = _paso(b, ctx, dx, dy, D['vuelta'])
        if cx_ and cy_: _marca(b, ahora, 'destello', 300, pos=_bc(b)); _poner(b, a['origen']); return False
        return True
    return True


def _mov_sobrecalentamiento(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], SUBJEFES['scizor']['calor']
    if 't0' not in a:
        a['t0'] = ahora
        S['calor'] = ahora + D['dura']
        ia._animar(b, ('hover', 'float', 'idle'), ahora, D['dura'])
        _mensaje(b, 'Scizor se sobrecalentó: aletea para enfriarse', 1300)
    if ahora < a['t0'] + D['dura']: return True
    for m in list(S['listo']): S['listo'][m] += D['dura']          # mientras se enfriaba no recargaba
    S['calor'] = None
    return False


# ==================== Tinkaton ====================

def _prep_tinkaton(b, ent, ahora):
    S = b['sj']
    S.update(metales=[{'pos': _centro(ent, f, c)} for f, c in _anillo(ent, SUBJEFES['tinkaton']['metales']['cantidad'])],
             n_metales=0, clavada=None, desde_colosal=2, martillo=None, salto=None, agarre=None)


def _mec_tinkaton(b, ctx):
    S, D, ahora = b['sj'], SUBJEFES['tinkaton'], ctx['ahora']
    Me = D['metales']
    S['mult_vel'] = max(0.4, 1 - Me['lento'] * S['n_metales'])
    C = S['clavada']
    if C and ahora < C['hasta']:                                    # trabada: los metales se le acercan
        for m in S['metales'][:]:
            d = _d(m['pos'], _bc(b))
            if d > 1:
                k = min(d, Me['vel'])
                m['pos'] = (m['pos'][0] + (b['rect'].centerx - m['pos'][0]) / d * k, m['pos'][1] + (b['rect'].centery - m['pos'][1]) / d * k)
            if not C['absorbio'] and _d(m['pos'], _bc(b)) <= Me['toca']:
                C['absorbio'] = True
                S['metales'].remove(m)
                S['n_metales'] += 1
                _marca(b, ahora, 'destello', 500, pos=_bc(b))
                _mensaje(b, '¡Tinkaton forjó un metal de Corviknight en su martillo! (' + str(S['n_metales']) + ')', 1800)
    elif C: S['clavada'] = None
    G = S['agarre']
    if G:                                                           # Carantoña: te tiene agarrado
        j = ctx['jugador']
        if ahora >= G['hasta']: S['agarre'] = None
        else:
            j['atrapado_hasta'] = max(j.get('atrapado_hasta', 0), ahora + 60)
            _poner(b, (j['rect'].centerx - 30, j['rect'].centery))
            if ahora >= G['prox']:
                G['prox'] = ahora + _md(b, 'carantoña')['tick']
                ia._pegar(b, ctx, _md(b, 'carantoña')['daño'], 'hada')


def _quieto_tinkaton(b, ctx):
    _acercar(b, ctx, 200, _vel(b, ctx['ahora']))


def _elegir_tinkaton(b, ctx):
    S = b['sj']
    colosal = S['desde_colosal'] >= _md(b, 'martillo_colosal')['entre']
    return _elegir(b, ctx, lambda m: m != 'martillo_colosal' or colosal, {'martillo_colosal': 2.5})


def _fin_tinkaton(b, ahora, mov):
    S = b['sj']
    S['desde_colosal'] = 0 if mov == 'martillo_colosal' else S['desde_colosal'] + 1


def _mov_martillo_colosal(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'martillo_colosal')
    j = ctx['jugador']
    n = S['n_metales']
    if 't0' not in a:
        a.update(t0=ahora, etapa='sube', sombra=_bc(b))
        ia._animar(b, ('hop', 'charge'), ahora, D['sube'])
    if a['etapa'] == 'sube':
        if ahora < a['t0'] + D['sube']: return True
        a.update(etapa='sigue', desde=ahora)
        b.update(escondido=True, invulnerable=True, sin_contacto=True)
        S['salto'] = a
    if a['etapa'] == 'sigue':                                       # la sombra sigue por donde estabas
        tx, ty = ia._pos_anterior(b, j, ahora, D['retraso'])
        x, y = a['sombra']
        d = math.hypot(tx - x, ty - y)
        vel = D['vel'] * max(0.4, 1 - D['lento'] * n)
        if d > 1: a['sombra'] = (x + (tx - x) / d * min(d, vel), y + (ty - y) / d * min(d, vel))
        if ahora < a['desde'] + D['sigue']: return True
        a.update(etapa='quieto', desde=ahora)
    if a['etapa'] == 'quieto':
        if ahora < a['desde'] + D['quieto']: return True
        a['radio'] = D['radio'] + D['radio_metal'] * n
        ia._golpe(b, ahora, 'circulo', D['aviso'], 'acero', 0, 150, pos=a['sombra'], radio=a['radio'], dibujo='cae', objeto='martillo')
        a.update(etapa='cae', desde=ahora)
    if a['etapa'] == 'cae':
        if ahora < a['desde'] + D['aviso']: return True
        _poner(b, a['sombra'])
        b.update(escondido=False, invulnerable=False, sin_contacto=False)
        S['salto'] = None
        ctx['impacto'](*a['sombra'], a['radio'], 600)
        pego = _d(a['sombra'], _jc(ctx)) <= a['radio'] + _mitad(j) and _pegar(b, ctx, D['daño'] + D['daño_metal'] * n, 'acero') > 0
        if pego: return False
        S['clavada'] = {'hasta': ahora + SUBJEFES['tinkaton']['clavado'], 'absorbio': False}   # no te pego: quedo trabada
        _mensaje(b, 'Martillo Clavado: ¡Tinkaton quedó trabada!', 1400)
        a.update(etapa='trabada', desde=ahora)
    if a['etapa'] == 'trabada':
        ia._animar(b, ('pull', 'charge', 'idle'), ahora, 200)
        return ahora < a['desde'] + SUBJEFES['tinkaton']['clavado']
    return True


def _mov_giro_vil(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'giro_vil')
    if 't0' not in a:
        a['t0'] = ahora
        _golpe(b, ahora, 'circulo', D['aviso'], 'siniestro', D['daño'], 180, pos=_bc(b), radio=D['radio'] + D['radio_metal'] * S['n_metales'],
               temblor=200)
        ia._animar(b, ('rotate', 'swing', 'attack'), ahora, D['aviso'] + 250)
    return ahora < a['t0'] + D['aviso'] + 200


def _mov_ojitos_tiernos(b, ctx, a):
    ahora, D, j = ctx['ahora'], _md(b, 'ojitos_tiernos'), ctx['jugador']
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('pose', 'nod', 'charge'), ahora, D['aviso'])
        _marca(b, ahora, 'corazones', D['aviso'] + 400)
    if ahora < a['t0'] + D['aviso']: return True
    if _d(_bc(b), _jc(ctx)) <= D['radio'] and not ia._esquivando(j, ahora):
        ia.poner_fx(j, 'ataque_bajo', ahora, D['dura'])
        _mensaje(b, 'Ojitos Tiernos: te bajó el ataque', 1300)
    return False


def _mov_carantoña(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'carantoña')
    j = ctx['jugador']
    if 't0' not in a:
        S['martillo'] = _bc(b)                                      # suelta el martillo
        b['sin_contacto'] = True
        a.update(t0=ahora, etapa='aviso', dir=_v(_ang(_bc(b), _jc(ctx))), restante=D['largo'])
        ia._animar(b, ('charge', 'walk'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        a['dir'] = _v(_ang(_bc(b), _jc(ctx)))
        if ahora < a['t0'] + D['aviso']: return True
        a['etapa'] = 'dash'
    if a['etapa'] == 'dash':
        r = _dash(b, ctx, a, D['vel'], 0, 'hada', 6)
        if a.get('pego') and not ia._esquivando(j, ahora) and not a.get('agarro'):
            a['agarro'] = True
            S['agarre'] = {'hasta': ahora + D['agarre'], 'prox': ahora}
            _mensaje(b, '¡Carantoña! Tinkaton te agarró', 1300)
            a.update(etapa='agarre', desde=ahora)
        elif r != 'sigue': a['etapa'] = 'vuelve'
        else: return True
    if a['etapa'] == 'agarre':
        b['sin_contacto'] = True
        if S['agarre']: return True
        a['etapa'] = 'vuelve'
    if a['etapa'] == 'vuelve':                                      # vuelve a buscar el martillo
        if _d(_bc(b), S['martillo']) < 30:
            S['martillo'] = None
            return False
        _ir(b, ctx, S['martillo'], D['vuelta'])
        if ahora > a['t0'] + 9000: _poner(b, S['martillo']); S['martillo'] = None; return False
        return True
    return True


# ==================== Chandelure ====================

def _prep_chandelure(b, ent, ahora):
    S, D = b['sj'], SUBJEFES['chandelure']
    A = S['area']
    velas = []
    for fy in (0.2, 0.5, 0.8):
        for fx in (0.18, 0.5, 0.82):
            velas.append({'pos': (A.left + A.width * fx, A.top + A.height * fy), 'luz': False, 'vuela': None})
    S.update(velas=velas[:D['candelabros']], llamas=[], sofoco=None)


def _luz_choca(b, v, D):
    return _d(_bc(b), v['pos']) <= D['luz'] + D['luz_vela']


def _mec_chandelure(b, ctx):
    S, M, D = b['sj'], b['sj']['mec'], SUBJEFES['chandelure']
    ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
    R = D['robo']
    if 'prox_robo' not in M: M['prox_robo'] = ahora + R['cada']
    if ahora >= M['prox_robo']:                                     # Robo de almas
        M['prox_robo'] = ahora + R['cada']
        j['sj_recarga'] = min(R['max'], j.get('sj_recarga', 1.0) + R['recarga'])
        b['vida'] = min(b['max_vida'], b['vida'] + round(b['max_vida'] * R['cura']))
        S['vida_ant'] = b['vida']
        _marca(b, ahora, 'alma', 700, desde=j['rect'].center)
    P = D['poltergeist']
    if ahora >= M.get('prox_polter', 0):                            # Poltergeist: su luz toca la de un candelabro prendido
        for v in S['velas']:
            if v['luz'] and not v['vuela'] and _luz_choca(b, v, D):
                M['prox_polter'] = ahora + P['espera']
                v['vuela'] = {'dir': _v(_ang(v['pos'], _jc(ctx))), 'pego': False}
                S['anuncio'] = ('Poltergeist', ahora)
                break
    for v in S['velas']:
        F = v['vuela']
        if not F: continue
        x, y = v['pos'][0] + F['dir'][0] * P['vel'], v['pos'][1] + F['dir'][1] * P['vel']
        if _solido(ent, x, y) or not S['area'].collidepoint(x, y):  # choco contra la pared: se queda y se apaga
            v['vuela'] = None; v['luz'] = False
            ctx['impacto'](*v['pos'], 50, 250)
            continue
        v['pos'] = (x, y)
        if not F['pego'] and _d(v['pos'], j['rect'].center) <= P['radio'] + _mitad(j) and not ia._esquivando(j, ahora):
            F['pego'] = True
            _pegar(b, ctx, P['daño'], 'fantasma')
    Ff = _md(b, 'fuego_fatuo')
    for ll in S['llamas'][:]:                                       # Fuego Fatuo
        if ahora >= ll['hasta']: S['llamas'].remove(ll); continue
        if not ll['caza'] and _d(ll['pos'], j['rect'].center) <= Ff['luz'] + _mitad(j): ll['caza'] = True
        if ll['caza']: ll['ang'] = _ang(ll['pos'], j['rect'].center); vel = Ff['vel_caza']
        else:
            if random.random() < 0.03: ll['ang'] += random.uniform(-1.2, 1.2)
            vel = Ff['vel']
        x, y = ll['pos'][0] + math.cos(ll['ang']) * vel, ll['pos'][1] + math.sin(ll['ang']) * vel
        if not S['area'].collidepoint(x, y): ll['ang'] += math.pi; continue
        ll['pos'] = (x, y)
        if _d(ll['pos'], j['rect'].center) <= Ff['radio'] + _mitad(j) * 0.8 and not ia._esquivando(j, ahora):
            S['llamas'].remove(ll)
            _pegar(b, ctx, Ff['daño'], 'fuego')
            _efecto(ctx, 'quemadura', Ff['quema'])
    So = S['sofoco']
    if So:                                                          # Sofoco: los circulos de llamas
        Sd = _md(b, 'sofoco')
        if ahora >= So['hasta']: S['sofoco'] = None
        elif ahora >= So['sale']:
            So['centro'] = (So['centro'][0] + So['dir'][0] * Sd['vel'], So['centro'][1] + So['dir'][1] * Sd['vel'])
            So['giro'] += Sd['giro']
            for i, c in enumerate(_circulos_sofoco(So, Sd)):
                for v in S['velas']:
                    if not v['luz'] and _d(c, v['pos']) <= Sd['radio'] + 30:
                        v['luz'] = True
                        _marca(b, ahora, 'chispa', 300, pos=v['pos'])
                if not So['pego'][i] and _d(c, j['rect'].center) <= Sd['radio'] + _mitad(j) and not ia._esquivando(j, ahora):
                    So['pego'][i] = True
                    _pegar(b, ctx, Sd['daño'], 'fuego')


def _circulos_sofoco(So, Sd):
    return [(So['centro'][0] + math.cos(So['giro'] + k * math.pi) * Sd['separa'], So['centro'][1] + math.sin(So['giro'] + k * math.pi) * Sd['separa'])
            for k in (0, 1)]


def _quieto_chandelure(b, ctx):
    S, D, ahora = b['sj'], SUBJEFES['chandelure'], ctx['ahora']
    prendidas = [v for v in S['velas'] if v['luz'] and not v['vuela']]
    if prendidas and ahora >= S['mec'].get('prox_polter', 0):        # va a buscar un candelabro prendido para tirartelo
        v = min(prendidas, key=lambda v_: _d(v_['pos'], _bc(b)))
        _ir(b, ctx, v['pos'], _vel(b, ahora))
        return
    _acercar(b, ctx, 260, _vel(b, ahora))


def _mov_fuego_fatuo(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'fuego_fatuo')
    for i in range(D['llamas']):
        ang = i * math.tau / D['llamas'] + random.uniform(-0.3, 0.3)
        S['llamas'].append({'pos': (b['rect'].centerx + math.cos(ang) * 50, b['rect'].centery + math.sin(ang) * 50), 'ang': ang, 'caza': False,
                            'hasta': ahora + D['dura']})
    ia._animar(b, ('charge', 'shoot'), ahora, 500)
    return False


def _mov_infortunio(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'infortunio')
    if 't0' not in a:
        a['t0'] = ahora
        A = S['area']
        for i in range(D['franjas']):
            p = _jc(ctx) if i == 0 else _punto_area(b, 80)
            ang = random.choice((0, math.pi / 2, math.pi / 4, -math.pi / 4))
            dx, dy = _v(ang)
            L = max(A.width, A.height)
            _golpe(b, ahora + i * 150, 'linea', D['aviso'], 'fantasma', D['daño'], D['dura'], D['tick'], a=(p[0] - dx * L, p[1] - dy * L),
                   b=(p[0] + dx * L, p[1] + dy * L), ancho=D['ancho'], infortunio=True)
        ia._animar(b, ('charge', 'rotate'), ahora, D['aviso'])
    return ahora < a['t0'] + D['aviso']


def _mov_sofoco(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'sofoco')
    S['sofoco'] = {'centro': _bc(b), 'dir': _v(_ang(_bc(b), _jc(ctx))), 'giro': 0.0, 'sale': ahora + D['aviso'], 'hasta': ahora + D['aviso'] + D['dura'],
                   'pego': [False, False]}
    ia._animar(b, ('charge', 'shoot'), ahora, D['aviso'] + 300)
    return False


# ==================== Samurott de Hisui ====================

def _prep_samurott_hisui(b, ent, ahora):
    b['sj'].update(puas=[])


def _mec_samurott_hisui(b, ctx):
    S, M, D = b['sj'], b['sj']['mec'], SUBJEFES['samurott_hisui']
    j, ahora = ctx['jugador'], ctx['ahora']
    P = D['puas']
    for p in S['puas'][:]:                                          # Piso con puas
        if ahora >= p['hasta']: S['puas'].remove(p); continue
        if ahora < p['listo']: continue
        if _d(p['pos'], j['rect'].center) <= P['radio'] + _mitad(j) * 0.7 and not ia._esquivando(j, ahora):
            S['puas'].remove(p)
            _pegar(b, ctx, P['daño'], 'siniestro')
    C = D['contra']                                                 # Postura de contraataque
    a = S['accion']
    if (a and a['mov'] != 'contraataque' and S['golpeado'] and _d(_bc(b), j['rect'].center) <= C['cerca']
            and ahora >= M.get('prox_contra', 0)):
        M['prox_contra'] = ahora + C['espera']
        b['golpes'][:] = [g for g in b['golpes'] if g.get('de_contra')]
        S['listo'][a['mov']] = ahora + _md(b, a['mov']).get('espera', 0)
        S['accion'] = None
        _empezar(b, ahora, 'contraataque')


def _quieto_samurott_hisui(b, ctx):
    _acercar(b, ctx, 190, _vel(b, ctx['ahora']))


def _elegir_samurott_hisui(b, ctx):
    d = _d(_bc(b), _jc(ctx))
    return _elegir(b, ctx, lambda m: m != 'concha_filo' or d <= _md(b, 'concha_filo')['cerca'],
                   {'corte_metralla': 1.3 if d < 240 else 0.6, 'megacuerno': 1.4 if d > 300 else 0.7})


def _mov_contraataque(b, ctx, a):
    ahora, C = ctx['ahora'], SUBJEFES['samurott_hisui']['contra']
    if 't0' not in a:
        a.update(t0=ahora, dir=_v(_ang(_bc(b), _jc(ctx))), restante=C['largo'], etapa='dash')
        ia._animar(b, ('attack', 'swing'), ahora, 400)
    if a['etapa'] == 'dash':
        if _dash(b, ctx, a, C['vel'], 0, 'siniestro') == 'sigue': return True
        ang = math.atan2(a['dir'][1], a['dir'][0])
        c = (b['rect'].centerx + math.cos(ang) * 60, b['rect'].centery + math.sin(ang) * 60)
        g = _golpe(b, ahora, 'circulo', C['aviso'], 'siniestro', C['daño'], 140, pos=c, radio=C['radio'], dibujo='tajo_c')
        g['de_contra'] = True
        a.update(etapa='corte', desde=ahora)
    return ahora < a['desde'] + C['aviso'] + 160


def _mov_corte_metralla(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'corte_metralla')
    if 't0' not in a: a.update(t0=ahora, i=0, prox=ahora)
    if a['i'] < D['cortes']:
        if ahora < a['prox']: return True
        ang = _ang(_bc(b), _jc(ctx))
        _paso(b, ctx, *_v(ang), 18)
        c = (b['rect'].centerx + math.cos(ang) * 55, b['rect'].centery + math.sin(ang) * 55)
        _golpe(b, ahora, 'circulo', D['aviso'], 'siniestro', D['daño'], 110, pos=c, radio=D['radio'])
        ia._animar(b, ('swing', 'attack', 'scratch'), ahora, D['aviso'] + 80)
        a['i'] += 1
        a['prox'] = ahora + D['aviso'] + D['entre']
        return True
    if not a.get('puas'):                                           # despues tira las puas por la sala
        a['puas'] = True
        P = SUBJEFES['samurott_hisui']['puas']
        for _ in range(D['puas']):
            p = _punto_libre(b, ctx, 60)
            ia._golpe(b, ahora, 'circulo', D['aviso_puas'], 'siniestro', 0, 80, pos=p, radio=P['radio'] + 6)
            S['puas'].append({'pos': p, 'listo': ahora + D['aviso_puas'], 'hasta': ahora + D['aviso_puas'] + P['dura']})
        a['fin'] = ahora + 250
    return ahora < a['fin']


def _mov_aqua_jet(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'aqua_jet')
    if 't0' not in a:
        a.update(t0=ahora, etapa='aviso')
        ia._animar(b, ('charge', 'walk'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        a['dir'] = _v(_ang(_bc(b), _jc(ctx)))
        if ahora < a['t0'] + D['aviso']: return True
        a.update(etapa='dash', restante=D['largo'])
    b['sj']['estela_agua'] = ahora + 120
    return _dash(b, ctx, a, D['vel'], D['daño'], 'agua', 8) == 'sigue' and not a.get('pego')


def _mov_concha_filo(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'concha_filo')
    if 't0' not in a:
        ang = _ang(_bc(b), _jc(ctx))
        a.update(t0=ahora, ang=ang)
        _golpe(b, ahora, 'poligono', D['carga'], 'agua', D['daño'], 200, puntos=_arco(_bc(b), ang, D['apertura'], D['radio']), temblor=200)
        ia._animar(b, ('charge', 'swing'), ahora, D['carga'] + 250)
    return ahora < a['t0'] + D['carga'] + 220


def _mov_megacuerno(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'megacuerno')
    if 't0' not in a:
        a.update(t0=ahora, etapa='aviso', dir=_v(_ang(_bc(b), _jc(ctx))), restante=D['largo'])
        ia._animar(b, ('charge', 'walk'), ahora, D['aviso'])
    if a['etapa'] == 'aviso':
        if ahora < a['t0'] + D['aviso']: return True
        a['etapa'] = 'dash'
    r = _dash(b, ctx, a, D['vel'], D['daño'], 'bicho', D['radio'] - 40)
    if r == 'sigue': return True
    ctx['impacto'](*_bc(b), 90, 350)
    return False


# ==================== Magnezone ====================

def _prep_magnezone(b, ent, ahora):
    b['sj'].update(campo_hasta=0, fijado_hasta=0, rayos=None, magnes=[])


def _mec_magnezone(b, ctx):
    S, M, D = b['sj'], b['sj']['mec'], SUBJEFES['magnezone']
    ent, j, ahora = ctx['ent'], ctx['jugador'], ctx['ahora']
    C = D['campo']
    if 'prox' not in M: M['prox'] = ahora + C['primero']
    if ahora >= M['prox'] and S['campo_hasta'] <= ahora:            # Campo electrico
        S['campo_hasta'] = ahora + C['dura']
        M['prox'] = S['campo_hasta'] + C['cada']
        M['dio'] = False
        M['magnes_listos'] = False
        _mensaje(b, '¡Campo eléctrico!', 1000)
    if ahora < S['campo_hasta']:
        if _d(_bc(b), j['rect'].center) <= C['radio'] + _mitad(j) * 0.5 and not ia._esquivando(j, ahora):
            ia.poner_fx(j, 'sj_lento_leve', ahora, 200)
            if not M['dio']:
                M['dio'] = True
                _efecto(ctx, 'paralisis', C['paraliza'])
                signo = random.choice((-1, 1))
                j['polaridad'] = (signo, ahora + C['polaridad'])
                _mensaje(b, 'Polaridad ' + ('negativa (-)' if signo < 0 else 'positiva (+)'), 1400)
    elif S['campo_hasta'] and not M.get('magnes_listos'):          # se apago: salen los Magnemite
        M['magnes_listos'] = True
        for signo in (1, -1):
            m = _invocar(b, ctx, 'magnemite', _bc(b), 'magnemite', 0.2, True, signo=signo, meta=_punto_area(b, 120), llego=None)
            if m: m['e']['polaridad_sj'] = signo
    if j.get('polaridad') and ahora >= j['polaridad'][1]: j['polaridad'] = None
    Mg = D['magnemites']
    for m in S['minions']:
        if m['clase'] != 'magnemite': continue
        e = m['e']
        if m['llego'] is None:
            if _d(e['rect'].center, m['meta']) > 12: ia._mover_hacia(ent, e, m['meta'], Mg['vel'], [])
            else: m['llego'] = ahora
            if ahora - m['nace'] > 4000: m['llego'] = ahora
            continue
        if ahora >= m['llego'] + Mg['dura']: _sacar(m); continue
        pol = j.get('polaridad')
        if not pol: continue
        dx, dy = e['rect'].centerx - j['rect'].centerx, e['rect'].centery - j['rect'].centery
        d = math.hypot(dx, dy) or 1
        if d > Mg['alcance'] or d < 30: continue
        k = Mg['fuerza'] * (1 - d / Mg['alcance'] * 0.6) * (1 if pol[0] != m['signo'] else -1)   # distintas se atraen, iguales se repelen
        _tirar_jugador(b, ctx, dx / d * k, dy / d * k, 'resto_iman_' + str(m['signo']))


def _quieto_magnezone(b, ctx):
    _acercar(b, ctx, 300, _vel(b, ctx['ahora']))


def _fijado(b, ahora):
    return ahora < b['sj']['fijado_hasta']


def _elegir_magnezone(b, ctx):
    S, ahora = b['sj'], ctx['ahora']
    d = _d(_bc(b), _jc(ctx))
    if _fijado(b, ahora):
        listos = [m for m in ('electrocañon', 'triataque') if ahora >= S['listo'].get(m, 0)]
        return random.choice(listos) if listos else None
    return _elegir(b, ctx, lambda m: m != 'chispazo' or d <= _md(b, 'chispazo')['cerca'], {'fijar_blanco': 1.5})


def _mov_fijar_blanco(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'fijar_blanco')
    if 't0' not in a:
        a['t0'] = ahora
        ia._animar(b, ('charge', 'shoot'), ahora, D['aviso'])
    if ahora < a['t0'] + D['aviso']: return True
    S['fijado_hasta'] = ahora + SUBJEFES['magnezone']['fijado']
    _mensaje(b, 'Magnezone te fijó como blanco', 1200)
    return False


def _fin_magnezone(b, ahora, mov):
    S = b['sj']
    if mov == 'fijar_blanco': S['libre_en'] = ahora + 250             # enseguida usa otro ataque (y 4 + 6 s hasta el proximo Fijar Blanco)


def _rayo_toca(j, a, c, ancho):
    return ia._dist_segmento(j['rect'].center, a, c) <= ancho / 2 + _mitad(j) * 0.8


def _mov_electrocañon(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'electrocañon')
    j = ctx['jugador']
    bc = _bc(b)
    if 't0' not in a:
        fij = _fijado(b, ahora)
        F = D['fijado'] if fij else D
        a.update(t0=ahora, fijado=fij, ang=_ang(bc, _jc(ctx)), prox=0, F=F)
        S['rayos'] = a
        ia._animar(b, ('charge', 'shoot'), ahora, F['aviso'] + F['dura'])
    F = a['F']
    if a['fijado']:                                                 # un rayo grande que sigue por donde estabas
        tx, ty = ia._pos_anterior(b, j, ahora, F['retraso'])
        a['ang'] = ia._girar_hacia(a['ang'], math.atan2(ty - bc[1], tx - bc[0]), F['giro'])
        angulos = [a['ang']]
    else:                                                           # dos rayos que giran a su alrededor
        if ahora >= a['t0'] + F['aviso']: a['ang'] += D['giro']
        angulos = [a['ang'], a['ang'] + math.pi]
    a['puntas'] = [(bc[0] + math.cos(g) * D['largo'], bc[1] + math.sin(g) * D['largo']) for g in angulos]
    if ahora < a['t0'] + F['aviso']: return True
    if ahora >= a['t0'] + F['aviso'] + F['dura']: S['rayos'] = None; return False
    if ahora >= a['prox'] and any(_rayo_toca(j, bc, p, F['ancho']) for p in a['puntas']):
        a['prox'] = ahora + F['tick']
        _pegar(b, ctx, F['daño'], 'electrico')
    return True


TRI = (('fuego', 'quemadura'), ('hielo', 'congelar'), ('electrico', 'paralisis'))


def _mov_triataque(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'triataque')
    if 't0' not in a:
        a.update(t0=ahora, fijado=_fijado(b, ahora), i=0, prox=ahora)
        ia._animar(b, ('charge', 'shoot'), ahora, D['dura'])
    if a['fijado']:                                                 # tandas de 3 bolas lentas que te siguen
        F = D['fijado']
        if a['i'] >= F['tandas']: return False
        if ahora < a['prox']: return True
        base = _ang(_bc(b), _jc(ctx))
        for k, (tipo, ef) in enumerate(TRI):
            _bala(b, ahora, _bc(b), base + (k - 1) * F['abanico'], F['vel'], F['radio'], D['daño'], tipo, 'tri', 2000, F['dura'], sigue=F['giro'],
                  ef=ef, ms=D['efecto'])
        a['i'] += 1
        a['prox'] = ahora + F['entre']
        return True
    if ahora >= a['t0'] + D['dura']: return False                   # caen del cielo
    if ahora < a['prox']: return True
    a['prox'] = ahora + D['cada']
    tipo, ef = TRI[a['i'] % 3]
    a['i'] += 1
    j = ctx['jugador']
    for _ in range(10):
        ang, r = random.uniform(0, math.tau), random.uniform(0, D['cerca'])
        p = (j['rect'].centerx + math.cos(ang) * r, j['rect'].centery + math.sin(ang) * r)
        if S['area'].collidepoint(p): break
    dibujo = {'fuego': 'tri_fuego', 'hielo': 'cae', 'electrico': 'rayo_cielo'}[tipo]
    _golpe(b, ahora, 'circulo', D['aviso'], tipo, D['daño'], 150, ef=ef, ms=D['efecto'], pos=p, radio=D['radio'], dibujo=dibujo, objeto='chuzo')
    return True


def _mov_chispazo(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'chispazo')
    if 't0' not in a:
        a['t0'] = ahora
        _golpe(b, ahora, 'circulo', D['aviso'], 'electrico', D['daño'], 180, pos=_bc(b), radio=D['radio'], dibujo='rayo_cielo', temblor=150)
        ia._animar(b, ('charge', 'shock'), ahora, D['aviso'] + 200)
    return ahora < a['t0'] + D['aviso'] + 200


# ==================== Muk de Alola ====================

def _prep_muk_alola(b, ent, ahora):
    S = b['sj']
    A = S['area']
    tam = ent['tam']
    S['alcantarillas'] = [(A.centerx - 4 * tam, A.top + 70), (A.left + 70, A.centery), (A.right - 70, A.centery)]
    S.update(en=0, etapa='en', desde=ahora, grimers={}, items={0: [], 1: [], 2: []}, acida_hasta=0)
    _poner(b, S['alcantarillas'][0])


def _mec_muk_alola(b, ctx):
    S, D = b['sj'], SUBJEFES['muk_alola']
    j, ahora = ctx['jugador'], ctx['ahora']
    Al, Gr = D['alcantarilla'], D['grimer']
    b['invulnerable'] = ahora < S['acida_hasta'] or S['etapa'] == 'baja'
    S['alfa'] = 120 if ahora < S['acida_hasta'] else None
    S['no_ataca'] = S['etapa'] != 'en'
    if S['etapa'] == 'en' and ahora >= S['desde'] + Al['dura'] and not S['accion']:
        S.update(etapa='gira', desde=ahora)
        ia._animar(b, ('rotate', 'idle'), ahora, Al['gira'])
    elif S['etapa'] == 'gira' and ahora >= S['desde'] + Al['gira']:
        S.update(etapa='baja', desde=ahora)
        b.update(escondido=True, sin_contacto=True)
        _marca(b, ahora, 'charco_muk', Al['baja'], pos=_bc(b))
    elif S['etapa'] == 'baja' and ahora >= S['desde'] + Al['baja']:     # sale por otra alcantarilla
        S['en'] = random.choice([i for i in range(3) if i != S['en']])
        _poner(b, S['alcantarillas'][S['en']])
        b.update(escondido=False, sin_contacto=False)
        S.update(etapa='en', desde=ahora)
        _marca(b, ahora, 'charco_muk', 500, pos=_bc(b))
        items = S['items'][S['en']]
        if any(i['clase'] == 'basura' for i in items): S['cola'].append('lanzamugre')
        if any(i['clase'] == 'baya' for i in items): S['cola'].append('eructo')
        if items: _mensaje(b, 'Muk encontró ' + ' y '.join(sorted({'basura' if i['clase'] == 'basura' else 'una baya' for i in items})), 1300)
        S['items'][S['en']] = []
        g = S['grimers'].pop(S['en'], None)                          # el Grimer de esa alcantarilla se vuelve abajo
        if g: _sacar(g['m'])
    for i, pos in enumerate(S['alcantarillas']):                    # de las otras dos salen Grimer
        if i == S['en'] or S['etapa'] == 'baja': continue
        g = S['grimers'].get(i)
        if g and g['m']['e']['vida'] <= 0:                          # lo derrotaste: el proximo sale a los 2 s del anterior
            S['grimers'].pop(i); S['mec'][('prox', i)] = g['nace'] + Gr['cada']; continue
        if g and ahora >= g['hasta']:                               # no lo derrotaste a tiempo: deja algo y se va
            S['grimers'].pop(i)
            _sacar(g['m'])
            clase = random.choice(('baya', 'basura'))
            off = random.uniform(-50, 50), random.uniform(-50, 50)
            S['items'][i].append({'clase': clase, 'pos': (pos[0] + off[0] * 0.6 + (40 if i == 1 else -40 if i == 2 else 0),
                                                          pos[1] + off[1] * 0.6 + (40 if i == 0 else 0))})
            S['items'][i] = S['items'][i][-4:]
            S['mec'][('prox', i)] = ahora + 100
            continue
        if not g and ahora >= S['mec'].setdefault(('prox', i), ahora + 600):
            S['mec'][('prox', i)] = ahora + Gr['cada']
            m = _invocar(b, ctx, 'grimer_alola', pos, 'grimer', Gr['vida'])
            if m:
                S['grimers'][i] = {'m': m, 'hasta': ahora + Gr['tiempo'], 'nace': ahora}
                _marca(b, ahora, 'charco_muk', 400, pos=pos)


def _quieto_muk_alola(b, ctx):
    pass                                                            # Muk no camina


def _elegir_muk_alola(b, ctx):
    return _elegir(b, ctx, pesos={'bomba_lodo': 2})


def _mov_bomba_lodo(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'bomba_lodo')
    j = ctx['jugador']
    base = _jc(ctx)
    for i in range(D['bombas']):
        if i == 0: p = base
        else:
            ang = i * math.tau / (D['bombas'] - 1) + random.uniform(-0.3, 0.3)
            p = (base[0] + math.cos(ang) * D['abre'], base[1] + math.sin(ang) * D['abre'])
        g = _golpe(b, ahora, 'circulo', D['aviso'], 'veneno', D['daño'], 150, pos=p, radio=D['radio'], dibujo='charco', desde=_bc(b), temblor=80)
        _golpe(b, ahora + D['aviso'], 'circulo', 0, 'veneno', D['daño_charco'], D['charco'], D['tick'], pos=p, radio=D['radio'] - 6, suelo=True)
    ia._animar(b, ('shoot', 'attack'), ahora, 400)
    return False


def _mov_lanzamugre(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'lanzamugre')
    if 't0' not in a:
        a['t0'] = ahora
        _golpe(b, ahora, 'circulo', D['aviso'], 'veneno', D['daño'], 160, ef='veneno', ms=D['veneno'], pos=_jc(ctx), radio=D['radio'],
               dibujo='basura', temblor=400)
        ia._animar(b, ('charge', 'shoot'), ahora, D['aviso'])
    return ahora < a['t0'] + D['aviso'] + 150


def _mov_eructo(b, ctx, a):
    ahora, D = ctx['ahora'], _md(b, 'eructo')
    if 't0' not in a: a.update(t0=ahora, i=0)
    if a['i'] >= D['ondas']: return False
    if ahora < a['t0'] + a['i'] * D['entre']: return True
    _bala(b, ahora, _bc(b), _ang(_bc(b), _jc(ctx)), D['vel'], D['radio'], D['daño'], 'veneno', 'eructo', 1100, ef='veneno', ms=D['veneno'],
          empuje=D['empuje'])
    ia._animar(b, ('shoot', 'attack'), ahora, 300)
    a['i'] += 1
    return True


def _mov_armadura_acida(b, ctx, a):
    S, ahora, D = b['sj'], ctx['ahora'], _md(b, 'armadura_acida')
    S['acida_hasta'] = ahora + D['dura']
    _mensaje(b, 'Armadura Ácida: Muk no recibe daño', 1200)
    return False


# ==================== tablas ====================

PREPARAR = {'cramorant': _prep_cramorant, 'mamoswine': _prep_mamoswine, 'tyrantrum': _prep_tyrantrum, 'armaldo': _prep_armaldo,
            'scizor': _prep_scizor, 'tinkaton': _prep_tinkaton, 'chandelure': _prep_chandelure, 'samurott_hisui': _prep_samurott_hisui,
            'magnezone': _prep_magnezone, 'muk_alola': _prep_muk_alola}


def _mec_mamoswine_todo(b, ctx):
    _mec_mamoswine(b, ctx)
    _proys_que_esperan(b, ctx)


MECANICAS = {'cramorant': _mec_cramorant, 'mamoswine': _mec_mamoswine_todo, 'tyrantrum': _mec_tyrantrum, 'armaldo': _mec_armaldo,
             'scizor': _mec_scizor, 'tinkaton': _mec_tinkaton, 'chandelure': _mec_chandelure, 'samurott_hisui': _mec_samurott_hisui,
             'magnezone': _mec_magnezone, 'muk_alola': _mec_muk_alola}
QUIETO = {'cramorant': _quieto_cramorant, 'mamoswine': _quieto_mamoswine, 'tyrantrum': _quieto_tyrantrum, 'armaldo': _quieto_armaldo,
          'scizor': _quieto_scizor, 'tinkaton': _quieto_tinkaton, 'chandelure': _quieto_chandelure, 'samurott_hisui': _quieto_samurott_hisui,
          'magnezone': _quieto_magnezone, 'muk_alola': _quieto_muk_alola}
ELEGIR = {'cramorant': _elegir_cramorant, 'mamoswine': _elegir_mamoswine, 'tyrantrum': _elegir_tyrantrum, 'armaldo': _elegir_armaldo,
          'scizor': _elegir_scizor, 'tinkaton': _elegir_tinkaton, 'samurott_hisui': _elegir_samurott_hisui, 'magnezone': _elegir_magnezone,
          'muk_alola': _elegir_muk_alola}
FIN = {'tyrantrum': _fin_tyrantrum, 'scizor': _fin_scizor, 'tinkaton': _fin_tinkaton, 'magnezone': _fin_magnezone}
MOVS = {'cramorant': {'buceo': _mov_buceo, 'picotaladro': _mov_picotaladro, 'tragamisil': _mov_tragamisil, 'onda_electrica': _mov_onda_electrica},
        'mamoswine': {'fuerza_equina': _mov_fuerza_equina, 'terratemblor': _mov_terratemblor, 'alud': _mov_alud, 'poder_pasado': _mov_poder_pasado},
        'tyrantrum': {'triple_colmillo': _mov_triple_colmillo, 'danza_dragon': _mov_danza_dragon, 'testarazo': _mov_testarazo,
                      'cola_dragon': _mov_cola_dragon},
        'armaldo': {'pin_misil': _mov_pin_misil, 'cortefuria': _mov_cortefuria, 'trampa_rocas': _mov_trampa_rocas, 'giro_rapido': _mov_giro_rapido},
        'scizor': {'puño_bala': _mov_puño_bala, 'ida_y_vuelta': _mov_ida_y_vuelta, 'danza_espada': _mov_danza_espada, 'agilidad': _mov_agilidad,
                   'sobrecalentamiento': _mov_sobrecalentamiento},
        'tinkaton': {'martillo_colosal': _mov_martillo_colosal, 'giro_vil': _mov_giro_vil, 'ojitos_tiernos': _mov_ojitos_tiernos,
                     'carantoña': _mov_carantoña},
        'chandelure': {'fuego_fatuo': _mov_fuego_fatuo, 'infortunio': _mov_infortunio, 'sofoco': _mov_sofoco},
        'samurott_hisui': {'corte_metralla': _mov_corte_metralla, 'aqua_jet': _mov_aqua_jet, 'concha_filo': _mov_concha_filo,
                           'megacuerno': _mov_megacuerno, 'contraataque': _mov_contraataque},
        'magnezone': {'fijar_blanco': _mov_fijar_blanco, 'electrocañon': _mov_electrocañon, 'triataque': _mov_triataque, 'chispazo': _mov_chispazo},
        'muk_alola': {'bomba_lodo': _mov_bomba_lodo, 'lanzamugre': _mov_lanzamugre, 'eructo': _mov_eructo, 'armadura_acida': _mov_armadura_acida}}


# ==================== dibujo ====================

_ICONOS = {}


def _icono(nombre, alto):
    """Un pokemon en chiquito (el primer cuadro de su sprite), para la barra del jefe. None si no tiene sprite."""
    clave = (nombre, alto)
    if clave not in _ICONOS:
        img = None
        try:
            if animaciones.tiene_sprites(nombre):
                a = animaciones.AnimadorPokemon(nombre, pygame.Rect(0, 0, alto, alto), alto)
                c = a.cuadro()
                if c: img = c[0]
        except Exception: img = None
        _ICONOS[clave] = img
    return _ICONOS[clave]


class _Capa:
    """Una capa transparente del tamaño de la pantalla que se crea recien cuando se dibuja algo en ella (asi no se pagan blits de mas)."""
    def __init__(self, ventana): self.ventana, self.sup = ventana, None
    def __call__(self):
        if self.sup is None: self.sup = pygame.Surface(self.ventana.get_size(), pygame.SRCALPHA)
        return self.sup
    def poner(self):
        if self.sup is not None: self.ventana.blit(self.sup, (0, 0))


def _pt(p, cx, cy):
    return round(p[0] - cx), round(p[1] - cy)


_OSCURA = {}


def _oscuridad(ventana, alfa, luces, cx, cy):
    """La sala a oscuras: una capa negra con agujeros de luz (circulos con borde suave y poligonos), sin que se pisen entre si."""
    W, H = ventana.get_size()
    if _OSCURA.get('tam') != (W, H): _OSCURA.update(tam=(W, H), sup=pygame.Surface((W, H), pygame.SRCALPHA))
    capa = _OSCURA['sup']
    capa.fill((4, 4, 14, alfa))
    for luz in luces:
        if luz[0] == 'c':
            _, p, r = luz
            x, y = _pt(p, cx, cy)
            r = round(r)
            if x + r < 0 or y + r < 0 or x - r > W or y - r > H or r <= 0: continue
            clave = (r, alfa)
            if clave not in _OSCURA:                                # el sello de cada luz se arma una sola vez
                sello = pygame.Surface((2 * r + 2, 2 * r + 2), pygame.SRCALPHA)
                sello.fill((4, 4, 14, 255))
                for k, a in ((1.0, 0.6), (0.82, 0.32), (0.62, 0.08)):
                    pygame.draw.circle(sello, (4, 4, 14, round(alfa * a)), (r + 1, r + 1), max(1, round(r * k)))
                _OSCURA[clave] = sello
            capa.blit(_OSCURA[clave], (x - r - 1, y - r - 1), special_flags=pygame.BLEND_RGBA_MIN)
        else:
            _, puntos, k = luz
            if len(puntos) < 3: continue
            pts = [_pt(p, cx, cy) for p in puntos]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            caja = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 2, max(ys) - min(ys) + 2)
            sello = pygame.Surface(caja.size, pygame.SRCALPHA)
            sello.fill((4, 4, 14, 255))
            pygame.draw.polygon(sello, (4, 4, 14, round(alfa * k)), [(p[0] - caja.x, p[1] - caja.y) for p in pts])
            capa.blit(sello, caja.topleft, special_flags=pygame.BLEND_RGBA_MIN)
    ventana.blit(capa, (0, 0))


def dibujar_suelo(ventana, b, cx, cy, ahora, colores=None):
    """Lo de los subjefes que va en el piso, debajo de los pokemon."""
    if not es_subjefe(b): return
    S, n = b['sj'], b['sj_nombre']
    colores = colores or {}
    capa = _Capa(ventana)
    if n == 'cramorant':
        for h in S['agujeros']:                                     # el agua de los agujeros se mueve
            x, y = _pt(h, cx, cy)
            for i in range(2):
                r = 14 + ((ahora // 12 + i * 20) % 34)
                pygame.draw.circle(capa(), (220, 245, 255, max(0, 160 - r * 4)), (x, y), r, 2)
        if S['buceo']:                                              # Cramorant bajo el hielo
            x, y = _pt(S['buceo'], cx, cy)
            pygame.draw.ellipse(capa(), (10, 30, 60, 150), (x - 55, y - 22, 110, 44))
            for i in range(3):
                r = 20 + ((ahora // 10 + i * 18) % 50)
                pygame.draw.circle(capa(), (200, 235, 255, max(0, 200 - r * 3)), (x, y), r, 2)
    elif n == 'armaldo':
        tam = 80
        for (f, c), hasta in S['agua'].items():                     # agua prehistorica
            k = max(0.0, min(1.0, (hasta - ahora) / 1500))
            pygame.draw.rect(capa(), (40, 150, 170, round(110 * k)), (c * tam - cx, f * tam - cy, tam, tam))
            if (f + c + ahora // 400) % 3 == 0:
                pygame.draw.line(capa(), (170, 240, 230, round(150 * k)), (c * tam - cx + 12, f * tam - cy + 40), (c * tam - cx + 40, f * tam - cy + 36), 2)
        for p in S['piedras']:
            if ahora < p['listo']: continue
            x, y = _pt(p['pos'], cx, cy)
            pygame.draw.polygon(capa(), (130, 110, 85, 255), [(x - 16, y + 8), (x - 6, y - 12), (x + 12, y - 9), (x + 17, y + 9)])
            pygame.draw.polygon(capa(), (60, 45, 30, 255), [(x - 16, y + 8), (x - 6, y - 12), (x + 12, y - 9), (x + 17, y + 9)], 2)
            pygame.draw.line(capa(), (230, 210, 160, 200), (x - 4, y - 8), (x + 8, y - 6), 2)
    elif n == 'samurott_hisui':
        for p in S['puas']:
            if ahora < p['listo']: continue
            x, y = _pt(p['pos'], cx, cy)
            alfa_ = 255 if p['hasta'] - ahora > 800 or (ahora // 100) % 2 else 120
            for k in range(3):
                ang = k * math.tau / 3 + 0.5
                pygame.draw.polygon(capa(), (60, 50, 90, alfa_), [(x + math.cos(ang) * 6, y + math.sin(ang) * 6), (x + math.cos(ang + 0.5) * 22, y + math.sin(ang + 0.5) * 22),
                                                                (x + math.cos(ang + 1.0) * 6, y + math.sin(ang + 1.0) * 6)])
            pygame.draw.circle(capa(), (180, 170, 220, alfa_), (x, y), 5)
    elif n == 'tinkaton':
        for m in S['metales']:                                      # los metales de Corviknight
            x, y = _pt(m['pos'], cx, cy)
            pygame.draw.polygon(capa(), (90, 100, 130, 255), [(x - 26, y + 14), (x - 18, y - 14), (x + 20, y - 18), (x + 28, y + 10)])
            pygame.draw.polygon(capa(), (200, 210, 235, 255), [(x - 26, y + 14), (x - 18, y - 14), (x + 20, y - 18), (x + 28, y + 10)], 3)
            pygame.draw.line(capa(), (240, 245, 255, 220), (x - 12, y - 6), (x + 14, y - 10), 2)
        if S.get('martillo'):                                       # el martillo que solto para la Carantoña
            x, y = _pt(S['martillo'], cx, cy)
            pygame.draw.line(capa(), (180, 120, 150, 255), (x, y), (x + 30, y - 40), 6)
            pygame.draw.rect(capa(), (230, 140, 170, 255), (x - 30, y - 10, 60 + 6 * S['n_metales'], 34), border_radius=8)
        salto = S.get('salto')
        if salto and salto.get('etapa') in ('sigue', 'quieto'):     # la sombra de Martillo Colosal
            x, y = _pt(salto['sombra'], cx, cy)
            r = _md(b, 'martillo_colosal')['radio'] + _md(b, 'martillo_colosal')['radio_metal'] * S['n_metales']
            pygame.draw.ellipse(capa(), (20, 10, 30, 150), (x - 60, y - 22, 120, 44))
            pygame.draw.circle(capa(), (255, 150, 200, 150), (x, y), r, 2)
        C = S.get('clavada')
        if C and ahora < C['hasta']:
            x, y = _pt(_bc(b), cx, cy)
            pygame.draw.polygon(capa(), (90, 70, 60, 200), [(x - 70, y + 50), (x - 20, y + 30), (x + 30, y + 52), (x - 10, y + 64)])
    elif n == 'chandelure':
        for v in S['velas']:                                        # los candelabros falsos
            x, y = _pt(v['pos'], cx, cy)
            pygame.draw.circle(capa(), (40, 30, 55, 255), (x, y + 18), 14)
            pygame.draw.line(capa(), (110, 90, 140, 255), (x, y + 10), (x, y - 6), 4)
            pygame.draw.arc(capa(), (150, 130, 180, 255), (x - 22, y - 16, 44, 22), math.pi, math.tau, 4)
            for dx in (-20, 0, 20):
                pygame.draw.rect(capa(), (220, 220, 235, 255), (x + dx - 3, y - 18 - (6 if dx == 0 else 0), 6, 10))
                if v['luz']:
                    k = 3 * math.sin(ahora / 90 + dx)
                    pygame.draw.circle(capa(), (170, 90, 255, 230), (x + dx, round(y - 24 - (6 if dx == 0 else 0) + k * 0.3)), 6)
                    pygame.draw.circle(capa(), (235, 200, 255, 255), (x + dx, round(y - 24 - (6 if dx == 0 else 0))), 3)
    elif n == 'muk_alola':
        Al = SUBJEFES['muk_alola']['alcantarilla']
        for i, pos in enumerate(S['alcantarillas']):                 # las tapas de las alcantarillas
            x, y = _pt(pos, cx, cy)
            pygame.draw.circle(capa(), (35, 35, 40, 255), (x, y), Al['radio'])
            pygame.draw.circle(capa(), (110, 110, 120, 255), (x, y), Al['radio'], 5)
            for k in range(-2, 3): pygame.draw.line(capa(), (80, 80, 90, 255), (x - 30, y + k * 10), (x + 30, y + k * 10), 2)
            for it in S['items'][i]:
                ix, iy = _pt(it['pos'], cx, cy)
                if it['clase'] == 'baya':
                    pygame.draw.circle(capa(), (230, 70, 90, 255), (ix, iy), 11)
                    pygame.draw.line(capa(), (80, 170, 70, 255), (ix, iy - 10), (ix + 6, iy - 18), 3)
                else:
                    pygame.draw.ellipse(capa(), (60, 70, 60, 255), (ix - 15, iy - 12, 30, 26))
                    pygame.draw.line(capa(), (140, 150, 120, 255), (ix - 4, iy - 12), (ix + 4, iy - 18), 3)
        if ahora < S.get('acida_hasta', 0):                         # Armadura Acida: un charco de veneno
            x, y = _pt(_bc(b), cx, cy)
            pygame.draw.ellipse(capa(), (150, 60, 200, 170), (x - 75, y + 10, 150, 50))
            pygame.draw.ellipse(capa(), (210, 150, 255, 220), (x - 75, y + 10, 150, 50), 3)
    elif n == 'magnezone':
        if ahora < S['campo_hasta']:                                # el campo electrico
            x, y = _pt(_bc(b), cx, cy)
            r = SUBJEFES['magnezone']['campo']['radio']
            pygame.draw.circle(capa(), (255, 230, 80, 45 + round(15 * math.sin(ahora / 80))), (x, y), r)
            azar = random.Random(ahora // 70)
            for _ in range(6):
                a1, a2 = azar.uniform(0, math.tau), azar.uniform(0, math.tau)
                ia._zigzag(capa(), (x + math.cos(a1) * r * azar.random(), y + math.sin(a1) * r * azar.random()),
                           (x + math.cos(a2) * r * azar.random(), y + math.sin(a2) * r * azar.random()), (255, 245, 150, 160), 2, azar, 5, 10)
            pygame.draw.circle(capa(), (255, 240, 120, 200), (x, y), r, 3)
    capa.poner()
    if n not in OSCURAS: ia._dibujar_golpes(ventana, b, cx, cy, ahora, colores, True)


def dibujar(ventana, b, j, cx, cy, ahora, fuente=None, colores=None):
    """Lo de los subjefes que va arriba de los pokemon: ataques, balas, la oscuridad y el nombre del movimiento."""
    if not es_subjefe(b): return
    S, n = b['sj'], b['sj_nombre']
    colores = colores or {}
    x, y = _pt(_bc(b), cx, cy)
    capa = _Capa(ventana)
    a = S.get('accion') or {}
    # ----- avisos propios de cada uno -----
    if a.get('mov') in ('picotaladro', 'fuerza_equina', 'testarazo', 'ida_y_vuelta', 'aqua_jet', 'megacuerno', 'carantoña') and a.get('etapa') == 'aviso':
        d = a.get('dir') or (0, 1)
        largo = a.get('restante') or 450
        color = {'picotaladro': (255, 220, 40), 'aqua_jet': (80, 170, 255), 'carantoña': (255, 150, 210)}.get(a['mov'], (255, 160, 40))
        ancho = 90 if a['mov'] == 'megacuerno' else 8
        pygame.draw.line(capa(), (*color, 130), (x, y), (x + d[0] * largo, y + d[1] * largo), ancho)
        pygame.draw.line(capa(), (*color, 230), (x, y), (x + d[0] * largo, y + d[1] * largo), 3)
    if n == 'cramorant':
        if a.get('mov') == 'picotaladro' and a.get('etapa') == 'dash':   # el pico amarillo
            d = a['dir']
            pygame.draw.polygon(capa(), (255, 220, 40, 255), [(x + d[0] * 70, y + d[1] * 70), (x - d[1] * 18, y + d[0] * 18), (x + d[1] * 18, y - d[0] * 18)])
        if a.get('mov') == 'tragamisil' and 't0' in a:
            d = _v(a['ang'])
            pygame.draw.line(capa(), (90, 160, 255, 160), (x, y), (x + d[0] * 600, y + d[1] * 600), 6)
        T = S.get('tragando')
        if T:                                                       # tragando: el anillo de 1,5 s para pegarle
            k = max(0.0, min(1.0, (ahora - T['inicio']) / SUBJEFES['cramorant']['traga']))
            pygame.draw.arc(capa(), (255, 240, 120, 230), (x - 70, y - 70, 140, 140), math.pi / 2, math.pi / 2 + math.tau * (1 - k), 6)
    if n == 'tyrantrum' and S.get('boca'):                          # Mandibula Fuerte: la boca brilla del color del colmillo
        color = SUBJEFES['tyrantrum']['colmillos'][S['boca']][1]
        d = _v(S['mira'])
        p = (x + d[0] * 48, y + d[1] * 30 - 18)
        pygame.draw.circle(capa(), (*color, 110), [round(v) for v in p], 34 + round(5 * math.sin(ahora / 60)))
        pygame.draw.circle(capa(), (*color, 230), [round(v) for v in p], 16)
    if n == 'mamoswine' and S.get('alud'):
        A = S['alud']
        vx, vy = A['viento']
        W, H = ventana.get_size()
        if 'sopla' not in A:                                        # aviso: todo rojo y la flecha del viento
            capa().fill((255, 30, 30, 60 + (40 if (ahora // 120) % 2 else 0)))
            c = (W // 2, H // 2)
            pts = [(c[0] + vx * 120, c[1] + vy * 120), (c[0] - vy * 60, c[1] + vx * 60), (c[0] + vy * 60, c[1] - vx * 60)]
            pygame.draw.line(capa(), (255, 240, 240, 230), (c[0] - vx * 140, c[1] - vy * 140), c, 24)
            pygame.draw.polygon(capa(), (255, 240, 240, 230), pts)
        else:                                                       # la ventisca
            azar = random.Random(11)
            for i in range(90):
                fx_, fy_ = azar.random(), azar.random()
                av = ((ahora / 500) * (1.5 + azar.random()) + fx_) % 1
                px = (av if vx > 0 else 1 - av if vx < 0 else fx_) * W
                py = (av if vy > 0 else 1 - av if vy < 0 else fy_) * H
                pygame.draw.line(capa(), (235, 250, 255, 230), (px, py), (px - vx * 40, py - vy * 40), 3)
    if n == 'tinkaton' and S.get('agarre'):
        jx, jy = _pt(j['rect'].center, cx, cy)
        for k in range(3):
            ang = ahora / 150 + k * math.tau / 3
            pygame.draw.circle(capa(), (255, 150, 210, 230), (round(jx + math.cos(ang) * 28), round(jy - 20 + math.sin(ang) * 10)), 6)
    if n == 'scizor' and S.get('calor') and ahora < S['calor']:     # el viento del aleteo
        for i in range(10):
            ang = i * math.tau / 10 + ahora / 400
            r0 = 60 + ((ahora // 4 + i * 37) % 300)
            pygame.draw.line(capa(), (230, 240, 255, max(0, 200 - r0 // 2)), (x + math.cos(ang) * r0, y + math.sin(ang) * r0),
                             (x + math.cos(ang) * (r0 + 30), y + math.sin(ang) * (r0 + 30)), 3)
        pygame.draw.circle(capa(), (255, 120, 60, 90), (x, y), 60 + round(4 * math.sin(ahora / 50)))
    if n == 'magnezone':
        R = S.get('rayos')
        if R and R.get('puntas'):
            F = R['F']
            activo = ahora >= R['t0'] + F['aviso']
            for p in R['puntas']:
                q = _pt(p, cx, cy)
                if not activo: pygame.draw.line(capa(), (255, 240, 120, 150), (x, y), q, 3)
                else:
                    pygame.draw.line(capa(), (255, 230, 60, 190), (x, y), q, F['ancho'])
                    pygame.draw.line(capa(), (255, 255, 230, 255), (x, y), q, max(4, F['ancho'] // 4))
        if _fijado(b, ahora):                                       # el cuadrado rojo de Fijar Blanco
            jx, jy = _pt(j['rect'].center, cx, cy)
            r = 36 + round(4 * math.sin(ahora / 90))
            caja = pygame.Rect(0, 0, 2 * r, 2 * r); caja.center = (jx, jy)
            pygame.draw.rect(capa(), (255, 40, 40, 230), caja, 3)
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                pygame.draw.line(capa(), (255, 40, 40, 255), (jx + sx * r, jy + sy * r), (jx + sx * (r - 14), jy + sy * r), 5)
                pygame.draw.line(capa(), (255, 40, 40, 255), (jx + sx * r, jy + sy * r), (jx + sx * r, jy + sy * (r - 14)), 5)
        for m in S['minions']:                                      # el + o el - de cada Magnemite
            if m['clase'] != 'magnemite': continue
            mx, my = _pt(m['e']['rect'].center, cx, cy)
            _signo(capa(), (mx, my - 42), m['signo'], 11)
            if m['llego'] is not None:
                pygame.draw.circle(capa(), ((255, 80, 80) if m['signo'] > 0 else (80, 140, 255)) + (120,), (mx, my), 40 + round(10 * math.sin(ahora / 70)), 3)
    if n == 'chandelure':
        for ll in S['llamas']:                                      # Fuego Fatuo
            p = _pt(ll['pos'], cx, cy)
            pygame.draw.circle(capa(), (150, 80, 255, 230), p, 12 + round(2 * math.sin(ahora / 60)))
            pygame.draw.circle(capa(), (240, 210, 255, 255), p, 5)
        So = S.get('sofoco')
        if So:
            Sd = _md(b, 'sofoco')
            for c in _circulos_sofoco(So, Sd):
                p = _pt(c, cx, cy)
                activo = ahora >= So['sale']
                pygame.draw.circle(capa(), (255, 120, 40, 200 if activo else 90), p, Sd['radio'])
                pygame.draw.circle(capa(), (255, 230, 120, 255), p, Sd['radio'], 4)
        for v in S['velas']:
            if v['vuela']: pygame.draw.circle(capa(), (170, 90, 255, 120), _pt(v['pos'], cx, cy), 40, 3)
    if n == 'armaldo' and ahora < S.get('armadura_hasta', 0):        # Armadura de Fosil: circulo marron claro
        pygame.draw.circle(capa(), (200, 160, 110, 90), (x, y), 78)
        pygame.draw.circle(capa(), (225, 190, 140, 230), (x, y), 78, 4)
    if n == 'armaldo' and ahora < S.get('girando', 0):
        for k in range(3):
            ang = ahora / 40 + k * math.tau / 3
            pygame.draw.arc(capa(), (230, 220, 200, 220), (x - 66, y - 66, 132, 132), ang, ang + 1.4, 5)
    if n == 'samurott_hisui' and ahora < S.get('estela_agua', 0):
        pygame.draw.circle(capa(), (90, 170, 255, 110), (x, y), 64)
    for m in S['marcas']:                                           # destellos, auras, salpicaduras...
        if not m['inicio'] <= ahora < m['hasta']: continue          # (en la pausa de impacto no se actualizan)
        k = (ahora - m['inicio']) / max(1, m['hasta'] - m['inicio'])
        if m['clase'] == 'aura':
            pygame.draw.circle(capa(), (*m['color'], round(150 * (1 - k))), (x, y), round(60 + 30 * k), 4)
        elif m['clase'] in ('destello', 'chispa'):
            p = _pt(m['pos'], cx, cy)
            pygame.draw.circle(capa(), (255, 255, 255, round(220 * (1 - k))), p, round(10 + (40 if m['clase'] == 'destello' else 18) * k), 3)
        elif m['clase'] == 'salpica':
            p = _pt(m['pos'], cx, cy)
            r = round((70 if m.get('grande') else 40) * k) + 6
            pygame.draw.circle(capa(), (200, 235, 255, round(220 * (1 - k))), p, r, 4)
            for i in range(5):
                ang = i * math.tau / 5
                pygame.draw.circle(capa(), (220, 245, 255, round(230 * (1 - k))), (round(p[0] + math.cos(ang) * r), round(p[1] + math.sin(ang) * r - 20 * math.sin(k * math.pi))), 4)
        elif m['clase'] == 'grieta':
            p = _pt(m['pos'], cx, cy)
            azar = random.Random(id(m))
            for _ in range(3):
                ang = azar.uniform(0, math.tau)
                pygame.draw.line(capa(), (230, 250, 255, round(255 * (1 - k))), p, (p[0] + math.cos(ang) * 40, p[1] + math.sin(ang) * 40), 3)
        elif m['clase'] == 'temblor':
            r = round(m['radio'] * k)
            pygame.draw.circle(capa(), (150, 100, 50, 160), (x, y), max(4, r), 8)
            pygame.draw.circle(capa(), (150, 100, 50, 60), (x, y), m['radio'] // 4, 0)
        elif m['clase'] == 'corazones':
            for i in range(4):
                ang = ahora / 200 + i * math.tau / 4
                hx, hy = round(x + math.cos(ang) * 50), round(y - 50 + math.sin(ang) * 16 - 20 * k)
                pygame.draw.circle(capa(), (255, 120, 180, 230), (hx - 4, hy), 5); pygame.draw.circle(capa(), (255, 120, 180, 230), (hx + 4, hy), 5)
                pygame.draw.polygon(capa(), (255, 120, 180, 230), [(hx - 9, hy + 1), (hx + 9, hy + 1), (hx, hy + 10)])
        elif m['clase'] == 'alma':                                  # Robo de almas: una lucecita que va de vos a Chandelure
            px_, py_ = m['desde'][0] + (b['rect'].centerx - m['desde'][0]) * k, m['desde'][1] + (b['rect'].centery - m['desde'][1]) * k
            pygame.draw.circle(capa(), (190, 120, 255, 230), _pt((px_, py_ - 40 * math.sin(k * math.pi)), cx, cy), 9)
        elif m['clase'] == 'charco_muk':
            p = _pt(m['pos'], cx, cy)
            pygame.draw.ellipse(capa(), (150, 60, 200, round(200 * (1 - k))), (p[0] - 60, p[1] - 10, 120, 40))
    capa.poner()
    arriba = _Capa(ventana)                                         # lo que va arriba de la oscuridad (una sola capa)
    # ----- la oscuridad -----
    if n == 'tyrantrum':
        V = SUBJEFES['tyrantrum']['vision']
        luces = [('p', S['cono'], 0.05), ('c', _bc(b), 80), ('c', j['rect'].center, V['luz_jugador'])]
        _oscuridad(ventana, V['oscuro'], luces, cx, cy)
        capa2 = arriba
        if len(S['cono']) > 2:
            pygame.draw.polygon(capa2(), (255, 220, 120, 26 if not S['visto'] else 45), [_pt(p, cx, cy) for p in S['cono']])
            pygame.draw.lines(capa2(), (255, 220, 140, 120), False, [_pt(p, cx, cy) for p in S['cono'][1:]], 2)
        if S['quieto_desde'] is not None and not S['visto']:        # quieto en su vista: el reloj de 1 s arriba tuyo
            k = min(1.0, (ahora - S['quieto_desde']) / V['quieto'])
            jx, jy = _pt(j['rect'].center, cx, cy)
            pygame.draw.arc(capa2(), (255, 240, 160, 230), (jx - 22, jy - 70, 44, 44), math.pi / 2, math.pi / 2 + math.tau * (1 - k), 5)
    if n == 'chandelure':
        D = SUBJEFES['chandelure']
        luces = [('c', _bc(b), D['luz']), ('c', j['rect'].center, D['luz_jugador'])]
        luces += [('c', v['pos'], D['luz_vela']) for v in S['velas'] if v['luz']]
        luces += [('c', ll['pos'], _md(b, 'fuego_fatuo')['luz']) for ll in S['llamas']]
        if S.get('sofoco'): luces += [('c', c, 95) for c in _circulos_sofoco(S['sofoco'], _md(b, 'sofoco'))]
        _oscuridad(ventana, D['oscuro'], luces, cx, cy)
        capa2 = arriba
        pygame.draw.circle(capa2(), (170, 110, 255, 60), (x, y), D['luz'], 2)
        for v in S['velas']:
            if v['luz']: pygame.draw.circle(capa2(), (170, 110, 255, 50), _pt(v['pos'], cx, cy), D['luz_vela'], 2)
    if n in OSCURAS: ia._dibujar_golpes(ventana, b, cx, cy, ahora, colores, True)
    ia._dibujar_golpes(ventana, b, cx, cy, ahora, colores, False)
    _dibujar_golpes_propios(ventana, b, cx, cy, ahora)
    # ----- balas y ondas -----
    capa = arriba
    for p in S['proys']:
        pos = _pt(p['pos'], cx, cy)
        if p['clase'] == 'pez':
            ang = p['ang']
            pygame.draw.ellipse(capa(), (90, 130, 200, 255), (pos[0] - 22, pos[1] - 10, 44, 20))
            pygame.draw.polygon(capa(), (60, 90, 150, 255), [(pos[0] - math.cos(ang) * 22, pos[1] - math.sin(ang) * 22),
                                                         (pos[0] - math.cos(ang) * 36 - math.sin(ang) * 10, pos[1] - math.sin(ang) * 36 + math.cos(ang) * 10),
                                                         (pos[0] - math.cos(ang) * 36 + math.sin(ang) * 10, pos[1] - math.sin(ang) * 36 - math.cos(ang) * 10)])
        elif p['clase'] == 'pincho':
            d = _v(p['ang'])
            pygame.draw.line(capa(), (230, 230, 180, 255), (pos[0] - d[0] * 12, pos[1] - d[1] * 12), (pos[0] + d[0] * 6, pos[1] + d[1] * 6), 4)
        elif p['clase'] == 'roca':
            pygame.draw.circle(capa(), (150, 120, 90, 255), pos, p['radio'])
            pygame.draw.circle(capa(), (70, 50, 35, 255), pos, p['radio'], 3)
        elif p['clase'] == 'ojos':                                   # las ondas de las pinzas con ojos falsos
            ang = p['ang']
            caja = pygame.Rect(0, 0, p['radio'] * 2, p['radio'] * 2); caja.center = pos
            pygame.draw.arc(capa(), (255, 230, 120, 255), caja, -ang - 1.0, -ang + 1.0, 5)
            pygame.draw.circle(capa(), (255, 255, 255, 255), pos, 5); pygame.draw.circle(capa(), (30, 30, 30, 255), pos, 2)
        elif p['clase'] == 'eructo':
            ang = p['ang']
            caja = pygame.Rect(0, 0, p['radio'] * 2, p['radio'] * 2); caja.center = pos
            for corte in (-0.9, 0.2):
                pygame.draw.arc(capa(), (190, 90, 230, 255), caja, -ang + corte, -ang + corte + 0.7, 8)
        elif p['clase'] == 'tri':
            color = colores.get(p['tipo'], (255, 255, 255))
            pygame.draw.circle(capa(), (*color, 230), pos, p['radio'])
            pygame.draw.circle(capa(), (255, 255, 255, 255), pos, p['radio'], 3)
        else: pygame.draw.circle(capa(), (*colores.get(p['tipo'], (255, 255, 255)), 230), pos, p['radio'])
    for o in S['ondas']:
        r = round(o['max'] * max(0.0, min(1.0, (ahora - o['inicio']) / o['dura'])))
        if r > 3:
            c = _pt(o['centro'], cx, cy)
            pygame.draw.circle(capa(), (*o['color'], 120), c, r, o['grosor'])
            pygame.draw.circle(capa(), (*o['color'], 230), c, r, 3)
    capa.poner()
    pol = j.get('polaridad')
    if pol and ahora < pol[1]: _signo(ventana, _pt((j['rect'].centerx, j['rect'].top - 26), cx, cy), pol[0], 10)
    if fuente and S.get('anuncio') and ahora - S['anuncio'][1] < 1200 and not b.get('escondido'):
        t = fuente.render(S['anuncio'][0], True, (255, 235, 190))
        ventana.blit(t, t.get_rect(midbottom=(x, b['rect'].top - cy - 26)))


def _dibujar_golpes_propios(ventana, b, cx, cy, ahora):
    """Lo que ia._dibujar_golpes no sabe dibujar: los Arrokuda que caen, la basura de Lanzamugre y el fuego del Triataque."""
    for g in b['golpes']:
        dib = g.get('dibujo')
        if dib not in ('pez', 'basura', 'tri_fuego', 'tajo_c') or ahora < g['inicio']: continue
        k = min(1.0, (ahora - g['inicio']) / max(1, g['golpe'] - g['inicio']))
        x, y = _pt(g['pos'], cx, cy)
        if dib == 'tajo_c' and ahora >= g['golpe']:
            pygame.draw.arc(ventana, (230, 230, 255), (x - g['radio'], y - g['radio'], 2 * g['radio'], 2 * g['radio']), 0.3, 2.8, 6)
            continue
        if ahora >= g['golpe'] or k < 0.35: continue
        alto = round(500 * (1 - k))
        if dib == 'pez':
            pygame.draw.ellipse(ventana, (90, 130, 200), (x - 14, y - alto - 30, 28, 48))
            pygame.draw.ellipse(ventana, (40, 60, 110), (x - 14, y - alto - 30, 28, 48), 2)
        elif dib == 'basura':
            r = round(30 + 40 * k)
            pygame.draw.ellipse(ventana, (70, 80, 70), (x - r, y - alto - r, 2 * r, round(1.7 * r)))
            pygame.draw.ellipse(ventana, (30, 35, 30), (x - r, y - alto - r, 2 * r, round(1.7 * r)), 3)
            pygame.draw.line(ventana, (160, 170, 140), (x - 8, y - alto - r), (x + 10, y - alto - r - 22), 5)
        elif dib == 'tri_fuego':
            pygame.draw.circle(ventana, (255, 150, 40), (x, y - alto), 18)
            pygame.draw.circle(ventana, (255, 240, 150), (x, y - alto), 8)


def _signo(sup, centro, signo, r):
    """El + rojo o el - azul de la polaridad."""
    x, y = round(centro[0]), round(centro[1])
    color = (240, 60, 60) if signo > 0 else (60, 130, 250)
    pygame.draw.circle(sup, (20, 20, 30), (x, y), r + 4)
    pygame.draw.circle(sup, color, (x, y), r + 4, 2)
    pygame.draw.line(sup, color, (x - r + 3, y), (x + r - 3, y), 4)
    if signo > 0: pygame.draw.line(sup, color, (x, y - r + 3), (x, y + r - 3), 4)


def dibujar_hud(ventana, b, rb, ahora, fuente):
    """Abajo de la barra del subjefe: los Arrokuda que se trago, los metales del martillo, la Danza Dragon..."""
    if not es_subjefe(b) or not fuente: return
    S, n = b['sj'], b['sj_nombre']
    x, y = rb.x, rb.bottom + 2
    textos = []
    if n == 'cramorant':
        img = _icono('arrokuda', 26)
        for i in range(S['bolsa']):
            if img: ventana.blit(img, img.get_rect(midleft=(x + 4 + i * 30, y + 14)))
            else: pygame.draw.ellipse(ventana, (90, 130, 200), (x + 4 + i * 30, y + 6, 26, 14))
        if S['bolsa']: x += 10 + S['bolsa'] * 30
        if S.get('tragando'): textos.append(('tragando...', (255, 240, 120)))
    if n == 'tyrantrum' and S['danza']: textos.append(('Danza Dragón x' + str(S['danza']), (190, 140, 255)))
    if n == 'tinkaton' and S['n_metales']: textos.append(('Martillo +' + str(S['n_metales']), (220, 225, 245)))
    if n == 'chandelure': textos.append(('Velas prendidas: ' + str(sum(1 for v in S['velas'] if v['luz'])), (200, 160, 255)))
    if n == 'magnezone' and _fijado(b, ahora): textos.append(('Fijado', (255, 90, 90)))
    if n == 'armaldo' and ahora < S.get('armadura_hasta', 0): textos.append(('Armadura de Fósil', (225, 190, 140)))
    if _buff(b, 'defensa', ahora) < 1: textos.append(('Defensa +', (160, 200, 255)))
    if _buff(b, 'ataque', ahora) > 1: textos.append(('Ataque +', (255, 140, 120)))
    if _buff(b, 'vel', ahora) > 1: textos.append(('Velocidad +', (140, 230, 255)))
    for texto, color in textos:
        t = fuente.render(texto, True, color)
        ventana.blit(t, (x, y))
        x += t.get_width() + 12


def dibujar_hud_jugador(ventana, j, b, barra, ahora, fuente):
    """Abajo de tu barra de vida: tu polaridad (Magnezone) y cuanto mas tardan tus ataques (Chandelure)."""
    x, y = barra.x + 10, barra.bottom + 4
    pol = j.get('polaridad')
    if pol and ahora < pol[1]:
        _signo(ventana, (x + 10, y + 10), pol[0], 9)
        x += 30
    k = j.get('sj_recarga', 1.0)
    if k > 1.001 and fuente:
        t = fuente.render('Recarga +' + str(round((k - 1) * 100)) + '%', True, (200, 150, 255))
        ventana.blit(t, (x, y))
