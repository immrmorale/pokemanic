"""
modos.py - Los textos y numeros de todo lo que no es el viaje: el tutorial de la isla, el boss rush, la sala de los titanes,
los minijuegos del refugio, las charlas de tus amigos y las misiones del tablon.
La logica esta en main.py (armar_modos); aca solo estan los datos, para poder cambiarlos sin tocar el juego.
"""

# ---------------------------------------------------------------- tus amigos en el refugio
# Cada amigo esta en un solo lugar del refugio a la vez y sigue una de estas rutinas segun la hora del juego: (desde que hora, donde).
# A cada uno le toca una (por su id) y la corre un poco (hasta 45 minutos antes o despues), asi no se mueven todos juntos.
RUTINAS = (((0, 'barrio'), (7, 'plaza'), (12, 'comedor'), (14, 'minijuegos'), (18, 'plaza'), (21, 'barrio')),        # madrugador
           ((0, 'barrio'), (9, 'plaza'), (13, 'comedor'), (16, 'plaza'), (20, 'comedor'), (23, 'barrio')),             # dormilon
           ((0, 'barrio'), (6, 'minijuegos'), (11, 'comedor'), (14, 'minijuegos'), (19, 'plaza'), (22, 'barrio')),     # deportista
           ((0, 'barrio'), (8, 'comedor'), (11, 'plaza'), (15, 'barrio'), (17, 'plaza'), (20, 'comedor'), (23, 'barrio')))   # charlatan
AMIGOS_POR_ZONA = 18            # como mucho en un mismo lugar (con 'desbloquear todo' son muchos)


# ---------------------------------------------------------------- escenas (llegada a la era, jefes, fin de era)
# Como te espera cada jefe la primera vez: (pose, cuando se da vuelta). pose: 'sentado' (Sit), 'dormido' (Sleep) o 'espalda'
# (mirando para el otro lado). cuando: 'entrar' (apenas entras) o 'cerca' (cuando te siente cerca, o si le pegas).
POSE_JEFE = {'walrein': ('dormido', 'cerca'), 'regice': ('espalda', 'entrar'), 'golem': ('sentado', 'cerca'), 'regirock': ('espalda', 'entrar'),
             'corviknight': ('espalda', 'cerca'), 'registeel': ('espalda', 'entrar'), 'garchomp': ('sentado', 'cerca'), 'regidrago': ('dormido', 'entrar'),
             'magnezone': ('espalda', 'cerca'), 'regieleki': ('espalda', 'entrar'), 'regigigas': ('dormido', 'entrar'), 'arceus': ('espalda', 'entrar'),
             'cramorant': ('sentado', 'cerca'), 'mamoswine': ('dormido', 'cerca'), 'tyrantrum': ('espalda', 'cerca'), 'armaldo': ('sentado', 'cerca'),
             'scizor': ('espalda', 'cerca'), 'tinkaton': ('sentado', 'cerca'), 'chandelure': ('espalda', 'cerca'), 'samurott_hisui': ('sentado', 'cerca'),
             'muk_alola': ('dormido', 'cerca')}
JEFE_GRANDE = {'peso': 1400, 'altura': 17}   # desde este peso (hectogramos) o altura (decimetros) el jefe hace temblar todo al presentarse
# Al caer el Regi Celebi sale del portal, te agarra de la mano y te lleva. En cada era dice otra cosa y te lleva distinto:
# curva: cuanto se abre el camino hasta el portal; saltos: si va dando saltitos.
RESCATE = {'glaciacion': {'frase': '¡Bien ahí! Vamos, que el portal se congela.', 'curva': 140, 'saltos': False},
           'piedra': {'frase': '¡Lo hiciste! Agarrate fuerte, que esto se mueve.', 'curva': -120, 'saltos': True},
           'metales': {'frase': '¡Eso! Rápido, antes de que se oxide el portal.', 'curva': 200, 'saltos': False},
           'medieval': {'frase': '¡Victoria! El reino está a salvo. ¡Vamos!', 'curva': -180, 'saltos': True},
           'moderna': {'frase': '¡Volvió la luz! Vamos, que se corta otra vez.', 'curva': 60, 'saltos': False},
           'origen': {'frase': 'Ya casi... falta uno solo. Vení conmigo.', 'curva': 0, 'saltos': False}}


# ---------------------------------------------------------------- caminos entre salas
# A veces, al salir de una sala, antes de la siguiente hay un camino tranquilo: sin enemigos, con pokemon de la era paseando.
PASILLO = {'prob': 0.3,            # chance de que haya un camino entre dos salas
           'antes_jefe': 0.75,     # y antes del jefe o del Regi (una antesala para respirar)
           'pokes': (3, 6),        # cuantos pokemon de la era pasean
           'regalo': 0.25}         # chance de que uno te de una baya al hablarle (una vez cada uno)
NOMBRE_PASILLO = {'glaciacion': 'Sendero helado', 'piedra': 'Sendero de las cuevas', 'metales': 'Camino de las minas',
                  'medieval': 'Camino real', 'moderna': 'Avenida vacía', 'origen': 'Puente del tiempo'}
CHARLAS_PASILLO = {
    'glaciacion': ('Acá el frío no se va nunca. Por eso me gusta.', 'Más adelante el hielo cruje distinto... tené cuidado.', '¿Venís del portal? Hace mucho que no pasaba nadie.'),
    'piedra': ('Las cuevas de por acá tienen dibujos de pokemon. Alguien los hizo hace mucho.', 'No pises las rocas sueltas, se caen solas.', 'Hay algo enorme moviéndose bajo tierra.'),
    'metales': ('El ruido de las fraguas no para ni de noche.', 'Los humanos de esta era aprendieron a fundir metal. Y lo usan para todo.', 'Más adelante hay un pájaro de acero que no deja pasar a nadie.'),
    'medieval': ('Los caballeros pasan por acá a caballo. Bueno, en Rapidash.', 'Dicen que en la torre duerme un dragón de piedra.', 'El rey del castillo nos deja pasear si no rompemos nada.'),
    'moderna': ('Antes esta calle estaba llena de gente. Ahora se cortó la luz y se fueron.', 'Algo eléctrico anda suelto por la ciudad.', 'Me gusta el ruido de los cables. Me hace cosquillas.'),
    'origen': ('Acá el tiempo no corre: camina.', 'Todo empezó en este lugar. Y puede terminar acá también.', 'Sentís eso? Alguien muy grande nos está mirando.'),
}
CHARLAS_PASILLO_TODAS = ('¡Hola! Por acá no hay peleas, podés descansar.', 'Lindo día para caminar, ¿no?', 'Vos no sos de esta época, se nota.',
                         'Celebi pasó volando hace un rato. Iba apurado.', 'Si seguís derecho llegás a la próxima sala.')


# ---------------------------------------------------------------- tutorial (la isla de practica de Celebi)
# Cada paso: (clave, titulo, lo que dice Celebi). {teclas} se cambian por las teclas que tengas puestas.
# El orden es el del tutorial; que hace falta para pasar cada uno esta en main.py (paso_cumplido).
EQUIPO_TUTORIAL = ('riolu', 'torchic')          # arrancas con Riolu; Torchic se suma en el paso de los relevos
NIVEL_TUTORIAL = 12
AMIGO_TUTORIAL, RIVAL_TUTORIAL = 'machop', 'mankey'
TUTORIAL = (
    ('mover', 'Moverte', 'Bienvenido a mi isla. Acá nadie te apura. Caminá con {arriba} {izquierda} {abajo} {derecha} hasta la marca.'),
    ('correr', 'Correr', 'Mantené {correr} para correr hasta la otra marca. Correr gasta la barra azul de energía; se recarga sola.'),
    ('esquivar', 'Esquivar', 'Con {esquivar} das un salto corto hacia donde caminás y por un instante nada te toca. Esquivá 3 veces.'),
    ('combo', 'Cuerpo a cuerpo', 'Esos muñecos no pegan. Apretá {basico1} tres veces seguidas: el tercer golpe es un remate que barre y empuja. Hacé 2 combos completos.'),
    ('distancia', 'A distancia', 'De lejos se pega menos, pero es seguro. Alejate de los muñecos y dales 3 disparos con {basico2}.'),
    ('especial', 'Especiales', 'Tus dos especiales dependen de quién sos. Usá {especial1} y {especial2} (tardan unos segundos en recargar).'),
    ('parry', 'Parry', 'Ese Mankey sí pega (despacito). Cuando su anillo rojo brille AMARILLO con un "!", golpeá con {basico1}: eso es un parry. Hacé uno.'),
    ('relevo', 'Relevos', 'Te presto a Torchic. Cambiá de pokemon con {poke2} y pegale a alguien enseguida: el primer golpe del que entra pega más.'),
    ('asistencia', 'Asistencias', 'El que espera en la banca también ayuda: apretá {asist1} y tira su asistencia. Tardan mucho en recargar, guardalas para cuando haga falta.'),
    ('amistad', 'Baile y amistad', 'Acá nadie captura a nadie. Ese Machop está cansado: bailale cerca con {bailar} para que se encariñe, derrotalo y hablale con {interactuar}.'),
    ('romper', 'Romper cosas', 'Las cajas y las vasijas se rompen, y a veces tienen bayas, llaves o caramelos. Rompé una vasija.'),
    ('sala', 'Salas y llaves', 'Así son las salas del viaje: limpiás la sala, aparece la llave y se abren las puertas. Derrotá a los dos que vienen, agarrá la llave y cruzá el muelle del norte.'),
    ('comprar', 'La tienda', 'Cada mostrador vende algo distinto: curaciones, mejoras y MT. Te dejé unas monedas: acercate a un objeto y compralo con {interactuar}.'),
    ('fin', 'Sinergias y lazos', 'Lo último: los de la banca le dan un bonus al que pelea, y si tu equipo se lleva bien (mismo tipo, o historia en común) se forma un LAZO. Mirá el menú de equipo ({equipo}) y salí por una puerta cuando quieras.'),
)
CONSEJOS_TUTORIAL = {                             # lo que aparece abajo, chiquito, mientras haces el paso
    'esquivar': 'Si te iban a pegar mientras esquivabas es un esquive perfecto: recuperás energía y tu próximo golpe pega x1,8.',
    'combo': 'Cada golpe que conecta te devuelve energía y le saca espera a tus especiales: pelear de cerca rinde.',
    'parry': 'Un parry aturde al enemigo, le hacés el doble, te cura un poquito y devuelve las balas. Si fallás hay que esperar un instante.',
    'relevo': 'Cambiar tiene 2 segundos de espera. Si el que pelea cae, entra solo el siguiente.',
    'amistad': 'Con poca vida (menos del 40%) se encariñan; con mucha vida, el baile los confunde y se pegan entre ellos.',
    'romper': 'El daño a las cosas depende del material y de tu tipo: lucha rompe casi todo, el fuego quema la madera...',
    'sala': 'Arriba a la derecha se ve tu estilo (de D a S): pegá seguido, movete, hacé combos, relevos y asistencias.',
    'comprar': 'Las curaciones van al cinturón (abajo a la derecha) y se usan con {curar}.',
}
FIN_TUTORIAL = ('¡Eso es todo! Ya sabés moverte, pelear, hacer amigos y comprar.', 'El resto se aprende viajando. Cuando quieras, te espero en el flujo del tiempo.')

# ---------------------------------------------------------------- boss rush
RUSH = {'cura': 0.5,            # entre jefe y jefe todo el equipo recupera este porcentaje (y los caidos se levantan con eso)
        'cura_facil': 1.0,
        'bajo_jefe': 1, 'bajo_regi': 3,   # tu equipo sube solo hasta este nivel por debajo del jefe (como en un viaje bien jugado)
        'monedas_inicio': 150,
        'premio_jefe': 40, 'premio_completo': 400}   # monedas que vuelven con vos al refugio (boss rush con tu partida)

# ---------------------------------------------------------------- los titanes (los jefes que ya derrotaste, en el refugio)
# nombre -> (tipo de sala, lo que te dice cuando le hablas)
TITANES = {
    'walrein': ('jefe', ('Grrr... peleaste bien. El hielo de mi era ya no cruje.', 'Los Spheal preguntan por vos. Les dije que volvías.')),
    'regice': ('regi', ('...', 'Su cuerpo de hielo antiguo vibra despacio. Parece un saludo.', 'En el hielo de su pecho se ve tu reflejo, de cuando recién llegaste.')),
    'golem': ('jefe', ('Rodé mil años cuesta abajo y nadie me había frenado. Hasta vos.', 'Si querés la revancha, avisá. Pero sin trampas con el agua, ¿eh?')),
    'regirock': ('regi', ('...', 'Una de sus piedras tiene tallado algo. Parece un Celebi chiquito.', 'Los puntos de su cara titilan en orden. ¿Te está contando algo?')),
    'corviknight': ('jefe', ('Vigilé esa forja desde el aire toda mi vida. Ahora vigilo este refugio.', 'Tinkaton anda cerca, ¿no? Decile que no tengo nada que ver con su martillo.')),
    'registeel': ('regi', ('...', 'Ni un rayón. Y eso que le pegaste con todo.', 'Su metal no es de ninguna era. Celebi dice que es de antes del tiempo.')),
    'garchomp': ('jefe', ('Je. Me ganaste en mi propia guarida. Eso no se olvida.', 'Los dragones respetamos una sola cosa: al que vuelve a pelear.')),
    'regidrago': ('regi', ('...', 'Su cabeza de dragón se abre y se cierra, como si se riera.', 'Dicen que quedó a medio terminar. A vos no te pareció tan incompleto.')),
    'magnezone': ('jefe', ('BZZT. ANÁLISIS: DERROTA ACEPTADA. AMISTAD: EN PROCESO.', 'BZZT. SUGERENCIA: REVANCHA. PROBABILIDAD DE DIVERSIÓN: 97%.')),
    'regieleki': ('regi', ('...', 'No se queda quieto ni un segundo. Las chispas dibujan tu nombre en el aire.', 'Celebi le pidió que no enchufe nada en el refugio. No hizo caso.')),
    'regigigas': ('regi', ('...', 'Está dormido otra vez. Mejor no despertarlo... o sí.', 'Cuenta la leyenda que arrastró los continentes. Ahora cuida que el refugio no se mueva.')),
    'arceus': ('final', ('Quise frenar el tiempo para que nadie más se extinguiera. Vos me mostraste otra forma.', 'Mil brazos formaron el mundo. No alcanzaron para cuidarlo. Gracias por los tuyos.',
                         'Si querés medirte conmigo otra vez, acá estoy. Ya no peleo por miedo.')),
}
TITAN_AUSENTE = 'Un pedestal vacío. El nombre está tapado de polvo... todavía no lo derrotaste.'

# ---------------------------------------------------------------- minijuegos del refugio
# enemigos: cuantos hay a la vez; premio: monedas por punto para el proximo viaje (con tope)
MINIJUEGOS = {
    'contrarreloj': {'nombre': 'Contrarreloj', 'desc': '90 segundos. Derrotá a todos los que puedas: reaparecen enseguida.', 'ms': 90000, 'enemigos': 4,
                     'unidad': 'derrotados', 'premio': 6, 'tope': 150},
    'supervivencia': {'nombre': 'Supervivencia', 'desc': 'No hay curas y cada 20 segundos se suma un enemigo más. Aguantá todo lo que puedas.', 'ms': None, 'enemigos': 3,
                      'cada': 20000, 'max': 9, 'unidad': 'segundos', 'premio': 1.5, 'tope': 150},
    'monedas': {'nombre': 'Lluvia de monedas', 'desc': '45 segundos. Caen monedas por toda la cancha mientras los tiradores te apuntan. Juntá todas las que puedas.', 'ms': 45000,
                'enemigos': 3, 'estilo': 'tirador', 'cada_moneda': 450, 'unidad': 'monedas', 'premio': 1.2, 'tope': 120},
}

# ---------------------------------------------------------------- charlas de tus amigos en el refugio
# Primero lo que dice su especie (si tiene), despues su tipo y su naturaleza, y si no una general. {nombre} sos vos.
CHARLAS_ESPECIE = {
    'riolu': ('Siento tu aura desde la otra punta de la plaza, {nombre}. Hoy está tranquila.', 'Estuve practicando el parry con Machop. Me duele todo.'),
    'lucario': ('El aura de las eras rotas llega hasta acá. Tenemos que volver.',),
    'mudkip': ('Con la aleta de la cabeza siento el agua de la fuente. Va a llover en algún siglo.', '¿Me llevás? Prometo no meterme en todos los charcos.'),
    'torchic': ('¡Pío! Tengo fuego adentro y ganas de correr. ¿Vamos?', 'Celebi no me deja prender la fogata del patio. Dice que "ya pasó una vez".'),
    'natu': ('...', 'Natu te mira fijo. Después mira el portal. Después a vos otra vez.'),
    'xatu': ('Ya vi cómo termina el próximo viaje. No te lo voy a contar.',),
    'pikachu': ('¡Pika! Guardé electricidad en los cachetes por si salimos.',),
    'pichu': ('¡Pi! Me electrocuté solo otra vez. No le digas a nadie.',),
    'eevee': ('Todavía no sé en qué quiero convertirme. Celebi dice que tengo tiempo. Qué gracioso, Celebi.',),
    'snorunt': ('En el refugio hace calor. Me senté un rato adentro de la fuente.',),
    'froslass': ('En la Era Glacial yo era la que asustaba. Acá los chiquitos me piden cuentos.',),
    'chikorita': ('Planté pasto nuevo al lado del portal. Pisalo con cuidado, ¿sí?',),
    'machop': ('¡Cien flexiones antes de cada viaje! ¿Hacés conmigo?', 'Mankey dice que me gana. Mankey dice muchas cosas.'),
    'mankey': ('¡¿QUÉ MIRÁS?! ...Ah, sos vos. Perdón. ¿Salimos a pelear?',),
    'gible': ('Mordí una columna del templo. Estaba rica. Celebi se enojó.',),
    'garchomp': ('Desde que estoy con vos casi no extraño mi guarida. Casi.',),
    'zorua': ('¿Viste a ese Celebi que andaba por el patio hace un rato? Era yo. Je.',),
    'drifloon': ('Casi me vuelo con el viento del portal. Agarrame fuerte la próxima.',),
    'magnemite': ('BZZ. LA ESTATUA DEL SALÓN TIENE HIERRO. ME GUSTA LA ESTATUA.',),
    'wooper': ('Wooo. Paaa. (Se queda mirándote con una sonrisa enorme.)',),
    'cubone': ('Me quedé mirando la luna desde el observatorio. Hoy no lloré.',),
    'litwick': ('No te asustes si te sentís cansado cerca mío. Es... sin querer.',),
    'tinkatink': ('Estoy juntando metal para un martillo más grande. No le cuentes a Corviknight.',),
    'ralts': ('Siento que estás contento de volver. Yo también.',),
    'squirtle': ('Me pongo los lentes de sol y listo: ya estoy para otro viaje.',),
    'froakie': ('Estuve entrenando sustitutos. La mitad de los que ves en la plaza no soy yo.',),
    'sneasel': ('Te guardé una moneda que "encontré". No preguntes dónde.',),
    'lapras': ('Canté un rato en el estanque. Dicen que se escuchó en tres eras distintas.',),
}
CHARLAS_TIPO = {
    'fuego': ('Acá no hace frío nunca. Igual extraño una buena fogata.', 'Si en la Era Glacial te congelan, yo te descongelo. Para eso estoy.'),
    'agua': ('La fuente está linda, pero un río de verdad es otra cosa.', 'Si llueve en el viaje, dejame pelear a mí.'),
    'planta': ('El pasto del refugio no se marchita. Es raro. Y lindo.', 'Con sol corro más rápido. Acordate.'),
    'electrico': ('Con tormenta eléctrica soy imparable. Buscá nubes negras.', 'Me pica la piel cuando el portal está por abrirse.'),
    'hielo': ('Extraño la escarcha en los pies. La Era Glacial era casa.', 'En el hielo yo no resbalo. Los demás sí. Es divertidísimo.'),
    'lucha': ('Entreno todos los días en el dojo del salón. Vení a mirar.', 'A las cajas y las rocas dejámelas a mí.'),
    'veneno': ('Nadie se sienta conmigo en el lounge. Bueno, vos sí.', 'El agua tóxica es mi spa. No me juzgues.'),
    'tierra': ('Los cables no me hacen nada. En la Edad Moderna voy primero.', 'Cavé un pozo en el patio. Celebi todavía no se dio cuenta.'),
    'volador': ('Desde arriba el refugio parece una hoja flotando en el tiempo.', 'Los terremotos me dan risa.'),
    'psiquico': ('Anoche soñé con una era que todavía no existe.', 'Sé lo que vas a preguntar. Sí, quiero ir.'),
    'bicho': ('Chiquito pero rápido. No me subestimes.', 'Encontré un rincón con hojas ricas detrás de la galería.'),
    'roca': ('Me quedé quieto tres días. Nadie lo notó. Estuvo bueno.', 'En la tormenta de arena estoy cómodo.'),
    'fantasma': ('Atravesé la pared de tu casa sin querer. Lindo diario, eh.', 'Con niebla pego más fuerte. Y asusto mejor.'),
    'dragon': ('Un dragón no descansa: junta fuerza.', 'Los Regis no me dan miedo. Bueno, Regidrago un poco.'),
    'siniestro': ('No confíes en nadie. Salvo en mí. Y en Celebi. Y bueno, en ellos también.', 'De noche se pelea mejor.'),
    'acero': ('Me lustré con arena del patio. ¿Se nota?', 'El veneno no me hace nada. Mandame adelante.'),
    'hada': ('Le puse flores a la estatua del salón. Quedó preciosa.', 'Los dragones me tienen miedo. Yo no entiendo por qué.'),
    'normal': ('No tengo nada especial... dice la gente. Vos sabés que no es así.', 'Dormí como dieciséis horas. Estoy listo.'),
}
CHARLAS_NATURALEZA = {            # segun que tan facil se amiga su naturaleza: (desde, hasta, frases)
    'carinosa': (1.3, 9, ('¡{nombre}! ¡Volviste! ¡Te extrañé un montón!', '¿Me rascás atrás de la oreja? Dale, un ratito.')),
    'arisca': (0, 0.85, ('Hmpf. No es que te estuviera esperando.', 'Voy si querés. Pero no me hables en el camino.')),
}
CHARLAS_GENERALES = ('¡{nombre}! ¿Salimos de nuevo?', 'La próxima llegamos más lejos, {nombre}. Te lo prometo.', 'Acá se está bien... pero me pica todo de ganas de pelear.',
                     'Celebi dice que el tiempo se rompe cada vez más. No entiendo mucho, pero suena feo.', 'Todavía sueño con la Era Glacial. Qué frío, por favor.',
                     'Si me llevás, esta vez no me desmayo. Bueno... lo intento.', 'Estuve mirando el cosmos por el telescopio. Hay estrellas que todavía no nacieron.',
                     '¿Viste la sala de los titanes? Los que derrotamos están ahí, lo más tranquilos.')
CHARLAS_RECORD = ('Llegué a ser {record}. Quiero llegar más lejos.', '¿Te acordás cuando era {record}? Qué viaje ese.')
CHARLAS_AMISTAD = ('Con vos voy a cualquier era, {nombre}.', 'Sos mi persona favorita de todo el tiempo. Y mirá que hay tiempo.')   # amistad alta
# lo que te piden a veces (un favor): si lo cumplis en el proximo viaje, sube su amistad. evento: lo que cuenta (como las misiones)
FAVORES = (
    ('derrota', 15, 'Derrotá 15 enemigos conmigo en el equipo.'),
    ('sala', 6, 'Pasemos 6 salas juntos sin volver al refugio.'),
    ('nota_s', 1, 'Quiero ver una nota S. Una sola.'),
    ('jefe', 1, 'Llevame a ver caer a un jefe.'),
)
FAVOR_AMISTAD = 15

# ---------------------------------------------------------------- lo que te aconseja Celebi en el refugio (segun cuantas eras derrotaste)
CONSEJOS_CELEBI = {
    'principio': ('En la Era Glacial casi todos son de hielo y agua. Llevá fuego o lucha: descongelan y pegan fuerte.',
                  'Si alguien queda con poca vida, bailale antes de derrotarlo. Así se hacen los amigos.',
                  '¿Probaste la isla de práctica? Está en el menú principal: Tutorial. No muerde.',
                  'El parry es todo. Cuando el aviso brilla amarillo, golpeá. Riolu te lo puede explicar mejor que yo.'),
    'medio': ('Desde la Edad de Piedra los enemigos aprenden mañas: saltan si te escapás y tiran morteros si te quedás quieto. Movete, pero no huyas.',
              'Armá el equipo pensando en los lazos: dos del mismo tipo, o dos que se conozcan de antes, se potencian.',
              'Las salas de desafío dan el doble. Y las del tesoro, mejoras para siempre.',
              'Si un Regi te cuesta, andá a la sala de los titanes y pedile la revancha a los que ya venciste. Se aprende mirando.'),
    'final': ('Regigigas tarda en despertar: son diez segundos de regalo. Usalos.', 'Arceus no pelea por maldad. Acordate de eso cuando llegues.',
              'Ya arreglaste casi todo. Si querés medirte de verdad, la estatua del salón tiene el boss rush.'),
    'siempre': ('El modo fácil no le hace mal a nadie. Está en la estatua del salón, por si un día venís cansado.',
                'En la cancha hay tres juegos. Lo que ganes ahí te lo llevás como monedas al próximo viaje.',
                'Tus amigos a veces necesitan algo. Preguntales: un favor cumplido vale más que diez salas juntos.',
                'Mirá el tablón de misiones antes de salir. Tres activas a la vez, y casi todas se repiten.'),
}

# ---------------------------------------------------------------- misiones del tablon
# 'repite': se puede volver a tomar despues de cumplirla (las demas son de una sola vez)
MISIONES = [
    {'id': 'limpieza', 'nombre': 'Limpieza a fondo', 'desc': 'Derrotá 50 enemigos', 'evento': 'derrota', 'meta': 50, 'premio': 150, 'repite': True},
    {'id': 'explorador', 'nombre': 'Explorador', 'desc': 'Completá 10 salas', 'evento': 'sala', 'meta': 10, 'premio': 120, 'repite': True},
    {'id': 'cazajefes', 'nombre': 'Cazajefes', 'desc': 'Derrotá a un jefe o a un Regi', 'evento': 'jefe', 'meta': 1, 'premio': 200, 'repite': True},
    {'id': 'con_estilo', 'nombre': 'Con estilo', 'desc': 'Sacá una nota S en una sala', 'evento': 'nota_s', 'meta': 1, 'premio': 150, 'repite': True},
    {'id': 'crecer', 'nombre': 'Crecer juntos', 'desc': 'Hacé evolucionar a un pokemon', 'evento': 'evolucion', 'meta': 1, 'premio': 100, 'repite': True},
    {'id': 'reflejos', 'nombre': 'Reflejos de Lucario', 'desc': 'Hacé 15 parrys', 'evento': 'parry', 'meta': 15, 'premio': 160, 'repite': True},
    {'id': 'bailarin', 'nombre': 'Alma de fiesta', 'desc': 'Encariñá a 6 pokemon bailando', 'evento': 'encariñar', 'meta': 6, 'premio': 140, 'repite': True},
    {'id': 'amigos', 'nombre': 'Nuevos amigos', 'desc': 'Sumá 3 amigos nuevos', 'evento': 'amigo', 'meta': 3, 'premio': 220, 'repite': True},
    {'id': 'demoledor', 'nombre': 'Demoledor', 'desc': 'Rompé 40 cosas', 'evento': 'romper', 'meta': 40, 'premio': 100, 'repite': True},
    {'id': 'comprador', 'nombre': 'Buen cliente', 'desc': 'Comprá 8 cosas en las tiendas', 'evento': 'compra', 'meta': 8, 'premio': 120, 'repite': True},
    {'id': 'tesoros', 'nombre': 'Buscatesoros', 'desc': 'Entrá a 2 salas del tesoro', 'evento': 'tesoro', 'meta': 2, 'premio': 180, 'repite': True},
    {'id': 'desafio', 'nombre': 'Sin miedo', 'desc': 'Completá 3 salas de desafío', 'evento': 'desafio', 'meta': 3, 'premio': 200, 'repite': True},
    {'id': 'era', 'nombre': 'Arreglar una era', 'desc': 'Derrotá al Regi de una era', 'evento': 'regi', 'meta': 1, 'premio': 300, 'repite': True},
    {'id': 'rush', 'nombre': 'Todos seguidos', 'desc': 'Terminá un boss rush (estatua del salón)', 'evento': 'rush', 'meta': 1, 'premio': 500},
    {'id': 'revancha', 'nombre': 'La revancha', 'desc': 'Ganale la revancha a 3 titanes', 'evento': 'revancha', 'meta': 3, 'premio': 250},
    {'id': 'jugueton', 'nombre': 'Juguetón', 'desc': 'Jugá 3 minijuegos del refugio', 'evento': 'minijuego', 'meta': 3, 'premio': 90},
]
