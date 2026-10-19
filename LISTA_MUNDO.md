# Pokemanic: lista de lo que se agregó al mundo

Todo se dibuja con formas básicas y el nombre encima hasta que lleguen los sprites. El color del piso indica la era.

## Archivos

| Archivo | Qué tiene |
|---|---|
| `mundos.py` | Las eras, sus objetos, las piezas armadas, los climas y el plan de la partida (tiendas, jefes). Casi todo lo que se quiera tocar está acá, como datos. |
| `generacion.py` | Generador de salas: combate, tienda y arena de jefe. |
| `entorno.py` | Lo que pasa durante el juego: terrenos que reaccionan a los ataques, objetos que se rompen, máquinas, clima. |
| `tienda.py` | Objetos de la tienda (ninguno cura) y sus efectos. |
| `ia.py` | IA de enemigos y jefes. |
| `visor_mundo.py` | Herramienta para mirar salas generadas sin jugar: `python visor_mundo.py`. |
| `main.py` | Conecta todo lo anterior: salas, oleadas, monedas, tienda, carteles, flechas de enemigos, recorrido. |

## Estructura de la partida

| Orden | Era | Regi (sala 30) | Semijefe (sala 15, provisorio) | Color del piso |
|---|---|---|---|---|
| 1 | Era Glacial | Regice | Walrein | celeste hielo |
| 2 | Edad de Piedra | Regirock | Golem | marrón tierra |
| 3 | Edad de los Metales | Registeel | Corviknight | bronce |
| 4 | Edad Media | Regidrago | Garchomp | piedra marrón |
| 5 | Edad Moderna | Regieleki | Magnezone | azul noche |
| 6 | El Origen | Regigigas, y después **Arceus** | - | lila |

- Cada era tiene 30 salas. El Origen tiene 3: tienda, Regigigas y Arceus.
- **Tienda:** sale cada 5 a 10 salas. Si sale pronto, la siguiente tarda más: `hueco_siguiente >= 15 - hueco_anterior`. Así, si sale en la sala 5, la próxima no aparece hasta 10 salas después. Nunca cae en una sala de jefe. Se configura con `TIENDA_HUECO` y `TIENDA_COMPENSA`.
- **Puertas (como en Hades):** después de limpiar la sala, cada salida muestra lo que hay detrás: la variante de la sala que sigue ("Bosque encantado"), TIENDA, JEFE, REGI o FINAL. Salís por el norte y entrás a la sala siguiente por el sur.
- **Oleadas:** las salas de combate tienen de 1 a 3 oleadas. Antes de cada una se marca con un círculo rojo dónde van a salir los enemigos.
- **La vida no se recupera entre salas** (sin curas, como en Hades). Para volver al comportamiento anterior: `RESTAURAR_VIDA_ENTRE_SALAS = True` en `main.py`.
- Los enemigos son más fuertes según la era y la sala (`mundos.escala`).
- **Semijefes:** cada era tiene su campo `'jefe'` en `mundos.ERAS`. Para usar un Ultraente o un mítico hay que agregarlo a `pokemones.py` (datos y sprites) y cambiar ese nombre. Celebi ya está en los datos y viaja en el tiempo, así que encaja bien con la idea de las eras.

## Cómo se genera una sala (`generacion.py`)

Ideas tomadas de Spelunky (plantillas armadas a mano y validar o reintentar), Brogue (mapas de Dijkstra) y Hades (sala grande, puertas con premio, oleadas).

1. **Silueta:** rectángulo, esquinas cortadas, cruz, columnas, o **cueva** hecha con autómata celular (con pasillos serpenteantes que la mantienen abierta).
2. **Simetría:** a veces se espeja la sala (izquierda/derecha, arriba/abajo o las dos) para que parezca diseñada.
3. **Especiales:** río que serpentea con puentes y una cascada donde nace; laguna; foso con 4 puentes; costa; cintas transportadoras; cables.
4. **Terreno:** manchas orgánicas que crecen al azar y después se suavizan.
5. **Máquinas** que ayudan a ciertos tipos (ver más abajo).
6. **Piezas:** grupitos armados a mano por era, que se rotan y se espejan. Por ejemplo: fogata con troncos, círculo de piedras, cementerio, herrería, estacionamiento.
7. **Cobertura:** objetos para cubrirse repartidos parejo alrededor del centro (muestreo de Poisson).
8. **Sueltos:** el resto de los objetos, también separados entre sí.
9. **Validación:** caminos de 2 casillas de ancho entre la entrada, el centro y las salidas. Nada de lava, tóxico ni cables en el camino principal. Si un objeto encierra un hueco, se saca. En las cuevas, los huecos sueltos se vuelven roca.

Se generan hasta 5 salas válidas y se queda la de mejor puntaje: cerca del 68% de piso libre, cobertura cerca de la pelea, variedad de terrenos y piezas puestas. Tarda unos 25 ms por sala.

## Variantes por era

| Era | Variantes |
|---|---|
| Glacial | glaciar, lago congelado, tundra, cueva de hielo (interior), grieta |
| Piedra | pradera, aldea de cazadores, cueva rupestre (interior), círculo de piedras, valle volcánico, río |
| Metales | forja (interior), mina de cobre (interior), mercado, templo de bronce, puerto antiguo |
| Media | patio del castillo, bosque encantado, aldea, mazmorra (interior), foso del castillo, guarida del dragón (interior) |
| Moderna | fábrica (interior), calle, plaza, callejón, central eléctrica, alcantarilla (interior) |
| Origen | templo de los titanes |

## Objetos (rompibles salvo que diga lo contrario)

| Era | Objetos |
|---|---|
| Glacial | bloque de hielo (empujable; deja charco), pino nevado, roca nevada, estalagmita de hielo, hueso y cráneo de mamut, pila de pieles |
| Piedra | tronco (empujable), roca, menhir, choza, lanza, cesto, árbol, arbusto, hueso |
| Metales | yunque (no se rompe), armadura, ánfora, mesa de mercado, columna (no se rompe), carro de bronce, estatua de bronce, lingotes, caja, barril |
| Media | carreta, fardo de heno, **barril de pólvora (explota)**, estatua de caballero, lápida, pozo (no se rompe), valla, estandarte, escamas de dragón |
| Moderna | caja de carbón, **barril de petróleo (explota y deja aceite)**, engranaje, chatarra, vagoneta, tubería, auto, poste de luz, bolsa de basura, contenedor, **hidrante (deja charco)**, máquina expendedora, banco de plaza, cabina telefónica, tacho de basura |
| Origen | pilar de cristal, columna rota, estatua de titán (no se rompe) |
| Tienda | estantes, mostrador, Kecleon (tendero), mesas, macetas |

Cómo se comportan:
- **Daño según el material:** la madera recibe x3 del fuego, la piedra x3 de lucha, el vidrio x3 de roca, el hielo x4 del fuego. La tabla completa está en `entorno.MATERIALES`.
- **Lo que arde** (madera, heno, tela, plantas) se rompe de un golpe de fuego y deja fuego en el piso.
- **Empujables:** lucha y psíquico los mandan a volar, y cualquier embestida los empuja. Al deslizarse le pegan a los enemigos. Un bloque de hielo que cae al agua la congela.
- **Explosivos:** explotan en área, encadenan con otros barriles y también te lastiman a vos.
- **Metal + eléctrico:** suelta chispas que paralizan a los enemigos cerca.
- A veces sueltan monedas.

## Terrenos y cómo reacciona cada tipo

Pisar un terreno:

| Terreno | Efecto |
|---|---|
| agua | Bloquea. Agua y volador la cruzan (agua más rápido). |
| hielo | Todos resbalan. **Hielo: x1.7 de velocidad y sprint gratis** (dash). Volador no resbala. |
| nieve | Frena (x0.7). Hielo va más rápido. A volador y normal no les afecta. |
| hierba | **Planta y bicho quedan escondidos** (los enemigos casi no te ven) y van más rápido. |
| sombra | **Siniestro: escondido y +25% de daño.** Fantasma: escondido y más rápido. |
| arena / lodo | Frenan. Tierra va más rápido. A roca, acero, volador y normal no les afecta. |
| lava | Bloquea. Fuego, dragón y volador pasan; **fuego hace +35% de daño encima.** |
| tóxico | Lastima. **Veneno: +30% de daño.** Acero y volador son inmunes. |
| cable | Lastima. **Eléctrico: energía x3 y recargas más rápidas.** Tierra y volador son inmunes. |
| corriente de aire | **Volador: x1.5 de velocidad y sprint gratis.** Al resto lo frena un poco. |
| cinta transportadora | Te lleva. Acero pesa más; volador ni la toca. |
| aceite | Todos resbalan (salvo acero y volador). |
| fuego | Lastima. Fuego gana daño; dragón es inmune. |

Máquinas (te ayudan si estás cerca; el círculo del radio solo se ve si te sirven):

| Máquina | A quién ayuda |
|---|---|
| **cascada** | agua: +30% de daño, energía x3, recargas -15% |
| cascada helada | hielo |
| fogata / brasero | fuego (la fogata también recarga energía a normal) |
| forja / horno | fuego y acero |
| generador | eléctrico: recargas -25%, energía x3 |
| altar | psíquico, fantasma, hada |
| cristal dragónico | dragón |
| imán | acero (defensa), eléctrico |
| monolito | roca y tierra (defensa) |

Ataques que cambian el terreno (sirven tus ataques y también los de los enemigos):
- **Hielo:** congela el agua y los charcos, lo que arma **puentes de hielo** para cruzar y deslizarte. También congela cascadas, apaga fuego y enfría la lava (queda roca volcánica).
- **Fuego:** quema hierba y aceite (el fuego se esparce), derrite hielo y nieve, seca charcos, prende fogatas, braseros, forjas y hornos, y saca la sombra.
- **Eléctrico:** electrifica toda el agua conectada (lastima y paraliza a quien esté adentro o en la orilla), da vuelta las cintas y descarga los generadores.
- **Agua:** apaga fuego, fogatas, braseros y hornos, enfría la lava, convierte la arena en lodo y hace explotar los generadores (cortocircuito).
- **Veneno:** contamina el agua y los charcos (quedan tóxicos).
- **Tierra:** desactiva los cables.
- **Planta:** hace crecer hierba (tu propia cobertura).
- **Siniestro:** crea sombra.

## Clima

- Cada sala tiene clima y se muestra en el cartel al entrar: *"Bosque encantado - Edad Media - Sala 4/30 - Lluvia"*.
- **Es coherente:** el clima de la sala siguiente casi siempre es el mismo o uno vecino. Por ejemplo: lluvia → nublado → despejado → sol. Nunca pasa de lluvia a sol de una sala a la otra (`VECINOS_CLIMA`).
- **Depende de la era:** en la Era Glacial nieva y graniza seguido; en la Edad Media llueve y hay niebla; en la Moderna hay niebla y tormentas eléctricas; en la de los Metales hay sol y tormentas de arena.
- Las salas interiores (cuevas, forjas, mazmorras, la tienda) no tienen clima.
- Cada Regi trae su clima: Regice granizo, Regirock tormenta de arena, Registeel sol, Regidrago y Regieleki tormenta eléctrica. Arceus trae sol.
- **Movimientos que cambian el clima por 15 s** y después vuelve el de la sala: hidrobomba trae lluvia; llamarada y rayo solar, sol; ventisca y viento hielo, granizo; terremoto y avalancha, tormenta de arena; bola sombra y pulso umbrío, niebla; trueno, tormenta eléctrica. También funcionan danza_lluvia, dia_soleado, granizo y tormenta_arena cuando existan esos movimientos.

| Clima | Efecto |
|---|---|
| lluvia | agua x1.4, fuego x0.6. Hace charcos y apaga el fuego. |
| sol | fuego x1.4, agua x0.6. Derrite el hielo y seca los charcos. |
| nieve | hielo x1.2. Junta nieve y congela charcos. |
| granizo | hielo x1.4. Congela el agua. |
| tormenta de arena | roca x1.3. |
| niebla | los enemigos te ven a menos distancia; fantasma y siniestro x1.2. |
| tormenta eléctrica | eléctrico x1.3. Caen rayos sobre enemigos, metal y agua. |

El granizo y la tormenta de arena solo lastiman si los trajo un movimiento; el clima normal de la sala no lastima.

## Tienda (salón del tamaño de la pantalla, sin curas)

Kecleon atiende en el mostrador. Hay un estante arriba, otro abajo y dos mesas destacadas. Te acercás a un objeto y apretás **E** para comprarlo. Las monedas salen de enemigos, objetos rotos, salas completadas y jefes.

| Tipo | Objetos |
|---|---|
| Comunes | Repelente, Superrepelente y Maxirepelente (35% menos enemigos por 3/5/8 salas), Ataque X, Defensa X, Velocidad X, Especial X y Directo (golpes críticos), todos por 3 salas; Éter (energía) |
| Permanentes | Cinta Fuerte, Garra Rápida, Polvo Veloz, Chaleco Asalto, Amuleto Moneda |
| De tipo (+20% a ese tipo) | Agua Mística, Carbón, Imán, Antiderretir, Cinturón Negro, Arena Fina, Pico Afilado, Piedra Dura, Colmillo Dragón, Gafas de Sol, Hechizo, Cuchara Torcida, Flecha Venenosa, Revest. Metálico, Semilla Milagro, Pañuelo Seda. Uno de los destacados suele ser del tipo de tu equipo. |

## IA de los enemigos (`ia.py`)

| Estilo | Rol | Qué hace |
|---|---|---|
| pegador | tanque / atacante | Te busca por el camino más corto y te pega de cerca. |
| tirador | estratega | Se queda a distancia, apunta adelante de donde vas, se aleja si te acercás y **se esconde detrás de objetos para recargar**. |
| rápido | velocista | Te rodea y se tira en embestida en línea recta. |

- Mapa de Dijkstra (como en Brogue) para esquivar obstáculos. Los de agua cruzan el agua y los fantasma atraviesan los objetos.
- Te ven solo si no hay nada en el medio. Cuando te ven aparece un "!" y avisan a sus compañeros cercanos. Si te pierden de vista, van a donde te vieron por última vez. Si estás escondido (hierba o sombra) o hay niebla, te ven de menos lejos.
- **Todos los ataques se avisan antes:** un anillo rojo para los golpes, una línea con mira para los disparos, una línea naranja para las embestidas.
- Como mucho **2** te pegan de cerca a la vez; el resto da vueltas. Es difícil pero justo. Se ajusta con `MAX_ATACANTES` y `ESTILOS`.
- Aturdidos (paralizados o dormidos) pierden el ataque que estaban preparando.
- **Jefes:** te siguen esquivando obstáculos, tiran ráfagas en abanico apuntadas y pisotean si estás cerca (todo avisado). Además mantienen el anillo de balas y las piedras verdes de antes.

## Cambios en la pantalla

- **Cartel al entrar** con el nombre de la sala, la era, el número de sala y el clima. Se va solo.
- **Carteles cortos** ("¡Sala completada!", "¡Conseguiste la llave!", compras): duran ~1 segundo y se van solos. Ya no hay que cerrar nada.
- **Flechas de enemigos fuera de pantalla:** un círculo con la cara del pokémon y una punta que señala dónde está. Van en el borde de la pantalla sin tapar el HUD; el del jefe tiene borde rojo.
- Monedas ($) en el HUD, objetos de la tienda activos, era y sala arriba.
- Indicador de "escondido" sobre el jugador.

## Debug

- **F2:** menú de salas. TAB cambia de era y se puede saltar a cualquier sala: tiendas, jefes, Regis, Arceus.
- **`python visor_mundo.py`:** flechas para era y variante, T para el tipo de sala, ESPACIO para otra sala, C para climas, P para el plan de una partida, S para guardar una captura.
- `python mundos.py` imprime un plan de partida y una cadena de climas.
- `python generacion.py` imprime salas de ejemplo en texto.

## Equipo, niveles y evoluciones (`progreso.py`)

- **Arrancás con un solo pokémon:** elegís entre Electrike, Sandshrew y Mareanie. El resto del equipo (hasta 3) se suma por amistad.
- **Experiencia:** sale de derrotar pokémon (fórmula de la quinta generación), romper objetos, completar salas, jefes y compras. Los de la banca ganan la mitad. Está ajustada para que quedes 2 a 5 niveles arriba de los enemigos (`XP_MULT`).
- **Niveles de los enemigos:** de 4 a 15 en la Era Glacial y +11 por era. La vida y el daño crecen con el nivel.
- **Stats como en los juegos:** `(2·base + IV + EV/4)·nivel/100 + 5`.
  - Ataque se usa para golpes y embestidas, y At. Esp. para disparos y áreas.
  - Las defensas bajan el daño recibido y la velocidad cambia lo que caminás.
- **IV y EV:** los IV salen al azar (0 a 31) para cada pokémon. Cada nivel da 1 punto de EV (10 EV) para repartir desde la ficha.
- **Evoluciones (PokéAPI):**
  - Por nivel.
  - Con piedra: Piedra Trueno, Piedra Alba, Garra Afilada.
  - Las de intercambio con el Cordón Unión.
  - Pichu y Riolu por amistad (sube cada sala que pasan en tu equipo).
  - Se hacen desde la ficha (TAB), con animación.
- **MT:** se compran en la tienda (siempre hay una que alguien de tu equipo puede aprender) y las sueltan los jefes. Se enseñan en una de las 4 casillas (E, Q, Shift, R), solo si la especie puede aprenderla según la PokéAPI, y se gastan al usarlas. Las que curan no existen.

## Amistad (no se captura)

- **Quién se te une:** a veces un pokémon derrotado se queda sentado con corazones. Te acercás, apretás interactuar (E) y elegís "Que se una" o "Dejarlo ir".
- **Chance:** sale del ratio de captura de la especie / 255 × 7%. Es más fácil si sos de más nivel, y el Lazo Amistad lo duplica.
- **Límites:** uno por sala como mucho. Los jefes no se unen. Si tenés el equipo lleno, va a la **Reserva** (TAB > Reserva para cambiarlo).

## Menú de equipo (TAB)

- **Dos estilos** (Ajustes > Menú de equipo):
  - **clásico:** como el menú de los juegos.
  - **escenario:** tus pokémon parados como en la Pokédex. Si no tocás nada por 8 s se duermen (Sleep; todos los sprites la tienen) y se despiertan con Wake los que la tienen.
- **Ficha:** stats con IV y EV (apretás sobre un stat para gastar un punto), movimientos (enseñar MT), evolucionar y poner a pelear.
- **Mochila y reserva:** la mochila muestra MT, piedras y objetos permanentes; la reserva, los que se unieron con el equipo lleno.

## Ajustes, controles y trucos

- **Ajustes** (mismo estilo que los otros menús): sonido, modo de combate, resolución (1000x600 a 1920x1152), pantalla completa, estilo del menú de equipo, controles y glosario. Se guardan en `config.json`.
- **Controles:**
  - Teclado y control (Xbox, PlayStation y Switch con el mapeo estándar de SDL), cada uno con 3 perfiles.
  - Cualquier acción se reasigna desde el menú, y "Restaurar preset" vuelve a las teclas de fábrica.
  - Con control: la palanca izquierda mueve, la derecha apunta y la cruz cambia de pokémon. En los menús, A confirma y B vuelve.
- **Código Konami** (↑↑↓↓←→←→BA) en Ajustes o en Pausa: menú debug con todas las MT, MT que no se gastan, vida infinita, sin recarga, monedas infinitas, un golpe mata y +5 niveles.
- **F1 + Konami** (en el menú o jugando): menú debug de pokémon, también con los jefes (Regis y Arceus jugables). F1 solo ya no hace nada.

## Efectos (`efectos.py`)

- **Entrada y salida:** al entrar a una sala la pantalla se abre en círculo y el pokémon camina solo desde la puerta; al salir, se cierra.
- **Partículas:** chispas del color del tipo en cada golpe, pedazos al romper o derrotar, explosiones, polvito al correr, brillitos al subir de nivel y corazones de amistad.
- **Sprites:** si ponés `assets/efectos/<nombre>.png` (tira de frames), se usa esa animación en vez de las partículas.

## Balance

- **Ataque básico a distancia:** ahora hace 65% del daño, tarda 1.5× en recargar y llega al 85% del alcance (`BASICO_DISTANCIA` en `main.py`). Las MT no tienen ese recorte.

## Glosario

Está en el menú principal, en Pausa y en Ajustes. Se arma con los mismos datos del juego (terrenos, máquinas, climas, materiales, tienda, controles), así que no se desactualiza.

## Sprites del mundo

Para que el juego use sprites en lugar de formas, se ponen PNG en estas carpetas:
- `assets/mundo/objetos/<nombre>.png` y `assets/mundo/terrenos/<terreno>.png`: valen para todas las eras.
- `assets/mundo/<era>/objetos/...` y `assets/mundo/<era>/terrenos/...`: solo para esa era. Por ejemplo, `assets/mundo/glaciacion/terrenos/suelo.png` es el piso de la Era Glacial.

Los nombres son los de `mundos.OBJETOS` y `mundos.TERRENOS`. Si falta un sprite, se dibuja la forma básica.
- Los objetos se escalan al ancho del objeto y se apoyan abajo, así un árbol sobresale hacia arriba.
- Los terrenos se estiran a la casilla.

La estructura completa de carpetas está en `assets/LEEME_assets.txt`.

Para recortar sprites de una hoja descargada: `python recortar_assets.py hoja.png`. Marcás el sprite con el mouse, escribís el nombre (TAB completa) y apretás ENTER. El color de fondo se vuelve transparente solo. La lista de la derecha muestra lo que todavía no tiene sprite.

## Pendiente

- Conseguir los sprites de objetos, terrenos y máquinas (ver "Sprites del mundo").
- Elegir los semijefes (Ultraentes o míticos).
- Los links de assets de Notion: no tengo acceso a Notion; si los pegás, los integro.
- Balance: vida y daño de enemigos y jefes, precios, monedas.
