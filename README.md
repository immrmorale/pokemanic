# Pokemanic

Juego de acción en Python con Pygame. Recorrés la historia de la humanidad sala por sala con un equipo de hasta 3 pokemon, peleás en tiempo real y enfrentás a un Regi al final de cada era, hasta llegar a Regigigas y Arceus.

```
python main.py
```

Necesita `pygame`. En la misma carpeta tienen que estar los 7 `.py`, `config.json`, `datos_pokeapi.json`, `cache_pokeapi.json` y la carpeta `assets` (sprites del PMD).

---

## Índice

1. [Archivos](#archivos)
2. [Controles](#controles)
3. [Cómo se juega](#cómo-se-juega)
4. [Roles](#roles)
5. [Niveles y stats](#niveles-y-stats)
6. [Evoluciones](#evoluciones)
7. [Amistad: pokemon que se unen](#amistad-pokemon-que-se-unen)
8. [Eras y salas](#eras-y-salas)
9. [Jefes](#jefes)
10. [Tienda](#tienda)
11. [Clima](#clima)
12. [Características de cada tipo](#características-de-cada-tipo)
13. [Tabla de tipos](#tabla-de-tipos)
14. [Herramientas](#herramientas)

---

## Archivos

| Archivo | Qué tiene |
|---|---|
| `main.py` | el juego: menús, la partida y el bucle principal |
| `datos.py` | ataques, pokemones (especies, tipos, roles), MT, tienda y mundos (eras, terrenos, objetos) |
| `sistema.py` | opciones (`config.json`), pantalla, controles (teclado y joystick) y animaciones |
| `mundo.py` | generación de salas, entorno (terrenos, objetos, clima) y efectos (partículas) |
| `combate.py` | progreso (niveles, IV/EV, evoluciones, amistad) e IA de enemigos y jefes |
| `interfaz.py` | menús: ajustes, controles, glosario, inicial, equipo, ficha, mochila |
| `herramientas.py` | programas aparte para preparar el juego (ver [Herramientas](#herramientas)) |

---

## Controles

Todas las teclas se pueden cambiar en **Ajustes > Controles**. Hay 3 perfiles de teclado y 3 de control (joystick).

| Acción | Teclado | Control |
|---|---|---|
| Moverse | W A S D | palanca izquierda |
| Correr (gasta energía) | Ctrl izquierdo | LB |
| Ataque cuerpo a cuerpo | E / clic izquierdo | X |
| Ataque a distancia | Q / clic derecho | RT |
| Especial 1 / Especial 2 | Shift izquierdo / R | RB / Y |
| Asistencia 1 / Asistencia 2 | F / G | LT / B |
| Cambiar al pokemon 1, 2 o 3 | 1 / 2 / 3 | cruz izq / arriba / der |
| Interactuar, comprar, hablar | E | A |
| Menú de equipo | TAB | Back |
| Pausa | ESC | Start |

**Modo de combate** (Ajustes > Combate):
- **mouse:** apuntás con el mouse.
- **teclas:** atacás hacia donde caminaste por última vez.
- **mixto:** usa teclas hasta que movés el mouse.

**Teclas secretas:**
- **F1** (en el menú principal o jugando): menú debug para poner cualquier pokemon en el equipo.
- **F2** (jugando): saltar a cualquier sala, tienda o jefe. TAB o Shift cambian de era.
- **Código Konami** (↑ ↑ ↓ ↓ ← → ← → B A) en Ajustes o en la pausa: menú de trucos (vida infinita, sin recarga, todas las MT, monedas infinitas, un golpe mata, subir 5 niveles). Los trucos no se guardan.

---

## Cómo se juega

- Elegís tu compañero inicial: **Electrike** (eléctrico, velocista), **Sandshrew** (tierra, tanque) o **Mareanie** (veneno/agua, estratega).
- Peleás con un solo pokemon a la vez. Los otros dos esperan en la **banca**. Cambiar de pokemon tiene una espera de 2,5 s.
- Cada sala de combate trae enemigos, a veces en 2 o 3 oleadas. Al limpiar la sala aparece una **llave**, y con la llave se abren las puertas.
- Cada puerta muestra un cartel con lo que hay detrás: una variante de sala, la tienda, el jefe o la era siguiente.
- **La vida no se recupera entre salas.** Si tu pokemon activo cae, entra solo el siguiente que esté vivo. La partida termina cuando caen todos.
- **Energía:** la barra azul debajo de la vida. Correr la gasta y se recarga sola. Si se vacía, quedás agotado hasta recuperar un poco.
- **Enemigos:** avisan antes de atacar. Un anillo rojo es un golpe, una línea con mira es un disparo y una línea naranja es una embestida. Como mucho dos te atacan cuerpo a cuerpo al mismo tiempo. Si te escondés en hierba o sombra (si tu tipo puede), casi no te ven.
- **Tipos de enemigo según su rol:**
  - **Pegadores** (tanques y atacantes): van directo hacia vos.
  - **Tiradores** (estrategas): disparan de lejos y se esconden para recargar.
  - **Rápidos** (velocistas): te rodean y embisten en línea recta.

### Ataques

| Botón | Qué hace |
|---|---|
| Cuerpo a cuerpo | rápido y fuerte, pero tenés que estar cerca |
| A distancia | 65% del daño y tarda 1,5 veces más en recargar, pero es seguro |
| Especiales (2) | dependen del rol del pokemon (ver [Roles](#roles)) |
| Asistencias (2) | las tira un pokemon de la banca; tardan mucho en recargar (45 a 90 s) |

Cada pokemon tiene 4 casillas de movimiento (E, Q, Shift, R). Desde la ficha del menú de equipo podés reemplazar una con una **MT**.

---

## Roles

Cada pokemon tiene un rol que cambia sus números, sus especiales, su asistencia y el bonus que da desde la banca.

| Rol | Velocidad | Vida | Daño | Recarga | Especiales | Asistencia desde la banca | Sinergia (banca) |
|---|---|---|---|---|---|---|---|
| **Tanque** | 3,5 | x1,35 | x0,9 | x1,15 (más lenta) | Defensa Férrea + onda de área de su ataque | **Escudo:** el activo recibe solo el 25% del daño por 5 s | menos daño recibido |
| **Atacante** | 4,7 | x1 | x1,3 | x1 | proyectil potenciado (+60% daño, atraviesa) + Danza Espada | **Impacto:** golpe de área (60 de daño) donde apuntás | más daño |
| **Estratega** | 4,3 | x1,05 | x0,95 | x0,9 | estado en área (paraliza, ralentiza o duerme) + Recuperación o Paz Mental | **Curar** 40%, **Desvanecer** (fantasma/psíquico: borra enemigos comunes) o **Masivo** (estado a toda la sala) | recargas más rápidas |
| **Velocista** | 6 | x0,8 | x0,8 | x0,7 (más rápida) | embestida de su tipo + Agilidad | **Carrera:** +60% velocidad y correr gratis por 6 s | más velocidad |

**Sinergia:** cada pokemon de la banca le da al que pelea un bonus pasivo de 3% a 7% según su rol. Cuanta más vida base tiene la especie, mayor es el bonus.

Algunos pokemon tienen una asistencia propia:
- **Pikachu y Pichu:** Trueno.
- **Froslass:** Mismo Destino (desvanecer).

---

## Niveles y stats

- Tu pokemon empieza en **nivel 5**. El máximo es **100**.
- **Stats como en los juegos:** `stat = (2·base + IV + EV/4) · nivel/100 + 5`. Los PS suman además `nivel + 10`. Las bases salen de la PokeAPI (`datos_pokeapi.json`).
- **IV:** cada pokemon nace con IVs al azar de 0 a 31 en cada stat. Por eso dos del mismo pokemon no son iguales.
- **EV:** cada nivel da **1 punto**, que equivale a 10 EV. Lo ponés en el stat que quieras desde la ficha del menú de equipo. El máximo es 252 EV por stat y 510 en total.
- **Qué hace cada stat:**
  - PS: la vida.
  - Ataque: golpes y embestidas.
  - At. Esp.: disparos y ataques de área.
  - Defensa y Def. Esp.: menos daño recibido.
  - Velocidad: caminar más rápido.

### Cómo se gana experiencia

| Cómo | Cuánto |
|---|---|
| Derrotar a un pokemon | fórmula de 5ª generación: más contra los de más nivel, menos contra los débiles. Los jefes dan el triple |
| Completar una sala | lo mismo que derrotar a tu propia especie al nivel de la sala |
| Romper objetos | 2 + (nivel de la sala ÷ 3) |
| Comprar en la tienda | el precio ÷ 6 |

- Los pokemon de la **banca ganan la mitad** de la experiencia.
- Cada especie sube con su propia **curva** (rápida, media, media-lenta o lenta), como en los juegos.

### Nivel de los enemigos

Va de 4 a 15 en la primera era y sube 11 niveles por era. El semijefe tiene +3 y el Regi +5.

| Era | Sala 1 | Sala 30 | Semijefe (sala 15) | Regi (sala 30) |
|---|---|---|---|---|
| Era Glacial | 4 | 15 | 12 | 20 |
| Edad de Piedra | 15 | 26 | 23 | 31 |
| Edad de los Metales | 26 | 37 | 34 | 42 |
| Edad Media | 37 | 48 | 45 | 53 |
| Edad Moderna | 48 | 59 | 56 | 64 |
| El Origen | 60 | — | — | Regigigas 62 · Arceus 66 |

---

## Evoluciones

**Cómo evolucionar:**
1. Cuando un pokemon puede evolucionar, aparece un cartel que avisa.
2. Abrí el menú de equipo (TAB), entrá a su ficha y elegí **Evolucionar**.

La evolución conserva el nivel, los IV, los EV y las MT enseñadas.

**Tipos de requisito:**
- **Nivel:** llegar a ese nivel.
- **Piedra u objeto:** tenerlo en la mochila. Se compran en la tienda, y el Regi lo suelta si alguien de tu equipo lo necesita.
- **Cordón Unión:** reemplaza a las evoluciones por intercambio de los juegos.
- **Amistad:** sube con cada sala que completás: +2 para el que pelea y +1 para los de la banca. Pichu y Riolu necesitan 20.

| Pokemon | Evoluciona a | Requisito |
|---|---|---|
| Pichu | Pikachu | amistad 20 |
| Pikachu | Raichu | Piedra Trueno |
| Electrike | Manectric | nivel 26 |
| Mareep | Flaaffy | nivel 15 |
| Flaaffy | Ampharos | nivel 30 |
| Shinx | Luxio | nivel 15 |
| Luxio | Luxray | nivel 30 |
| Magnemite | Magneton | nivel 30 |
| Magneton | Magnezone | Piedra Trueno |
| Sandshrew | Sandslash | nivel 22 |
| Cubone | Marowak | nivel 28 |
| Geodude | Graveler | nivel 25 |
| Graveler | Golem | Cordón Unión |
| Gible | Gabite | nivel 24 |
| Gabite | Garchomp | nivel 48 |
| Golett | Golurk | nivel 43 |
| Wooper | Quagsire **o** Clodsire | nivel 20 |
| Mudkip | Marshtomp | nivel 16 |
| Marshtomp | Swampert | nivel 36 |
| Squirtle | Wartortle | nivel 16 |
| Wartortle | Blastoise | nivel 36 |
| Froakie | Frogadier | nivel 16 |
| Frogadier | Greninja | nivel 36 |
| Oshawott | Dewott | nivel 17 |
| Dewott | Samurott | nivel 36 |
| Mareanie | Toxapex | nivel 38 |
| Spheal | Sealeo | nivel 32 |
| Sealeo | Walrein | nivel 44 |
| Snorunt | Glalie | nivel 42 |
| Snorunt | Froslass | Piedra Alba |
| Vanillite | Vanillish | nivel 35 |
| Vanillish | Vanilluxe | nivel 47 |
| Sneasel | Weavile | Garra Afilada |
| Torchic | Combusken | nivel 16 |
| Combusken | Blaziken | nivel 36 |
| Fletchling | Fletchinder | nivel 17 |
| Fletchinder | Talonflame | nivel 35 |
| Rookidee | Corvisquire | nivel 18 |
| Corvisquire | Corviknight | nivel 38 |
| Natu | Xatu | nivel 25 |
| Drifloon | Drifblim | nivel 28 |
| Mankey | Primeape | nivel 28 |
| Primeape | Annihilape | nivel 35 |
| Machop | Machoke | nivel 28 |
| Machoke | Machamp | Cordón Unión |
| Timburr | Gurdurr | nivel 25 |
| Gurdurr | Conkeldurr | Cordón Unión |
| Riolu | Lucario | amistad 20 |

Solo se evoluciona a pokemon que están en el juego, así que Chikorita no evoluciona: Bayleef no está.

---

## Amistad: pokemon que se unen

En este juego **los pokemon no se capturan**. Cuando derrotás a uno, a veces se queda con corazones porque quiere unirse a vos:
- Acercate y apretá **E** para hablarle.
- Si tu equipo está lleno (3), el nuevo va a la **reserva**. Desde TAB > Reserva lo podés cambiar por uno del equipo.
- Si te vas de la sala sin hablarle, se va.

**Cuándo es más probable:**
- Con pokemon comunes, porque depende del ratio de captura de la especie.
- Si sos de más nivel que él.
- Con el **Lazo Amistad** de la tienda, que duplica la chance.

Los jefes nunca se unen, y como mucho se une uno por sala.

---

## Eras y salas

La partida sigue la historia de la humanidad:
- **5 eras de 30 salas** cada una.
- Al final, **El Origen**, con 3 salas fijas: tienda, Regigigas y Arceus.
- En cada era, el **semijefe** está en la sala 15 y el **Regi** en la sala 30.
- La **tienda** aparece cada 5 a 10 salas.

| Era | Regi (sala 30) | Semijefe (sala 15) | Climas comunes | Variantes de sala | Enemigos |
|---|---|---|---|---|---|
| **Era Glacial** | Regice | Walrein | nieve, granizo, nublado | glaciar, lago congelado, tundra, cueva de hielo, grieta | Snorunt, Glalie, Froslass, Spheal, Sealeo, Walrein, Vanillite, Vanillish, Vanilluxe, Sneasel, Weavile, Lapras, Squirtle, Wartortle |
| **Edad de Piedra** | Regirock | Golem | despejado, sol, nublado, lluvia | pradera, aldea de cazadores, cueva rupestre, círculo de piedras, valle volcánico, río | Geodude, Graveler, Golem, Sandshrew, Sandslash, Cubone, Marowak, Mankey, Primeape, Timburr, Chikorita, Riolu, Torchic, Wooper, Quagsire |
| **Edad de los Metales** | Registeel | Corviknight | despejado, sol, tormenta de arena | forja, mina de cobre, mercado, templo de bronce, puerto antiguo | Magnemite, Magneton, Machop, Machoke, Machamp, Gurdurr, Conkeldurr, Combusken, Blaziken, Fletchling, Fletchinder, Talonflame, Corvisquire, Lucario, Mareanie |
| **Edad Media** | Regidrago | Garchomp | nublado, lluvia, niebla | patio del castillo, bosque encantado, aldea, mazmorra, foso del castillo, guarida del dragón | Gible, Gabite, Golett, Golurk, Samurott de Hisui, Oshawott, Dewott, Samurott, Rookidee, Drifloon, Drifblim, Natu, Xatu, Hawlucha, Froakie, Frogadier |
| **Edad Moderna** | Regieleki | Magnezone | nublado, lluvia, niebla, tormenta eléctrica | fábrica, calle, plaza, callejón, central eléctrica, alcantarilla | Pichu, Pikachu, Raichu, Mareep, Flaaffy, Ampharos, Shinx, Luxio, Luxray, Electrike, Manectric, Magneton, Toxapex, Clodsire, Greninja, Annihilape |
| **El Origen** | Regigigas, y después **Arceus** | — | despejado, tormenta eléctrica, niebla | templo de los titanes | Garchomp, Lucario, Annihilape, Greninja, Xatu, Golurk, Weavile, Luxray, Blaziken, Corviknight |

**Cómo se arma cada sala:** es procedural, al estilo Hades. Se generan varias candidatas y queda la mejor. Se construye por capas:
1. Forma: rectángulo, esquinas cortadas, cruz, columnas o cueva.
2. A veces simetría.
3. Elementos especiales: río con puentes, laguna, foso, costa, cintas o cables.
4. Manchas de terreno.
5. Máquinas.
6. Piezas armadas a mano de cada era: fogata con troncos, herrería, cementerio…
7. Objetos para cubrirse.

Siempre queda un camino ancho entre las puertas y el centro, sin peligros en el medio.

**Objetos del mundo:** muchos se rompen, y a veces sueltan monedas.
- El daño depende del **material** y del **tipo** del ataque (ver cada tipo más abajo).
- Lo que **arde** se rompe de un golpe de fuego.
- Los que tienen un **punto rojo explotan** y pueden encadenar explosiones.
- Lucha, psíquico y las embestidas **empujan** cajas y barriles.

---

## Jefes

| Jefe | Dónde | Vida base | Clima que trae |
|---|---|---|---|
| Walrein, Golem, Corviknight, Garchomp, Magnezone | sala 15 de cada era | 600 | — |
| Regice | Era Glacial, sala 30 | 1000 | granizo |
| Regirock | Edad de Piedra, sala 30 | 1000 | tormenta de arena |
| Registeel | Edad de los Metales, sala 30 | 1000 | sol |
| Regidrago | Edad Media, sala 30 | 1000 | tormenta eléctrica |
| Regieleki | Edad Moderna, sala 30 | 1000 | tormenta eléctrica |
| Regigigas | El Origen | 1000 | — |
| **Arceus** (final) | El Origen | 1500 | sol |

La vida base se multiplica según el nivel del jefe.

**Cómo pelean:**
- Te siguen por el mapa.
- Tiran **ráfagas de 5 balas en abanico** apuntadas a vos.
- Si estás cerca, dan un **pisotón** en área.
- Todo se avisa antes: una línea con mira para la ráfaga y un círculo rojo que se llena para el pisotón.
- También tienen un anillo de balas y piedras verdes.

**Los 5 Regis** (Regice, Regirock, Registeel, Regidrago y Regieleki): cuando pierden **un cuarto de su vida** llaman a **5 pokemon de su mismo tipo**. Primero aparecen las marcas rojas donde van a salir.

**Sala de los Regis:** redonda, grande (25 × 25 casillas) y vacía. Cuando cae el Regi se van los muros, rocas y torres que haya armado.

**Regice:**
- **Rayo Hielo** cada 7 s: una línea celeste fija que se va engrosando y después dispara un rayo ancho y muy largo. El piso por donde pasa queda **escarcha**: resbala.
- **Barra de congelamiento:** mientras pisás escarcha se carga una barra celeste (se dibuja arriba de tu barra de vida); fuera de la escarcha se descarga sola. Llena, **te congelás 3 s**. Congelado no podés moverte ni atacar, salvo con un **movimiento de hielo**, que te descongela.
- **Muro de hielo** cada 5 s: 3 bloques de hielo entre él y vos que **solo se rompen con fuego** (el fuego también derrite la escarcha).

**Regirock:**
- **Roca Afilada:** una fila de rocas que sale hacia vos y se frena al chocar con otra roca o con la pared. Si no te pegó, deja una roca al final.
- **Fuerza Bruta** (desde la mitad de su vida): una franja roja marca hacia dónde va a embestir. Si choca contra una roca (la rompe) o una pared, **queda aturdido 3 s**.

**Registeel:**
- **Minas:** pone 3 minas (una donde estás) que explotan al rato y largan balas en 8 direcciones.
- **Sierras:** tira 2 sierras que rebotan en las paredes durante 5 s o hasta que te pegan.
- **Imán:** se queda quieto y te tira hacia él durante 5 s.

**Regieleki:**
- Su sala tiene **6 torres eléctricas** (cuadrados grises). Tira **5 rayos** en abanico.
- Al perder un cuarto de vida **se mete en una torre** (se pone amarilla) y no se le puede pegar. Pegarle a esa torre le pega a él. Si le pegaste, a los 3 s se pasa a otra torre y la anterior queda **marrón** (no puede volver); si no le pegaste, a los 8 s se cambia igual y la torre vuelve a gris. En el camino deja una **línea amarilla** que lastima, y al llegar tira los 5 rayos.
- Sin torres: **se teletransporta** cada 2 s y larga **Alto Voltaje**, una onda que crece durante 3 s.

**Regigigas** pelea distinto:
- **Terremoto:** un anillo marrón con grietas se llena alrededor suyo y después pega a todo lo que esté adentro. Es de tipo tierra, así que a los voladores casi no les hace nada. La pantalla tiembla.
- **Puñetazos grandes:** una mira roja aparece donde estás parado, se cierra y cae el puño. Vienen de a 3 seguidos, cada uno apuntado a donde te moviste.
- **Regis chiquitos:** cada 11 s llama a 2 versiones chicas de los Regis (con menos vida y daño que los de verdad), como mucho 4 a la vez. Regieleki embiste, Regice y Regidrago disparan de lejos y los demás pegan de cerca.
- No tira piedras verdes.

**Arceus** tiene la barra de vida partida en **3 fases** (un tercio cada una), y avisa con un cartel cuando cambia:
1. **Rayos e Hiperrayo:** caen rayos de tipo normal en cualquier lugar del mapa (uno siempre cerca tuyo). Primero se marca un círculo en el piso y, al caer, cada rayo se abre en 4 balas: arriba, abajo, izquierda y derecha. Además tira **Hiperrayo**: una línea fija hacia donde estabas que se va engrosando; salí de la línea antes de que dispare.
2. **Multitipo y Sentencia:** cada golpe que le das le cambia el tipo (y con eso sus debilidades). Tira **Sentencia** como los puñetazos de Regigigas pero más grande, de a 3 seguidas: aparece el **sello de Arceus** (círculo con un triángulo y un círculo en cada punta) del color de su tipo, girando y llenándose hasta que cae.
3. **Todo junto:** rayos, Hiperrayo, Multitipo y Sentencia, más seguido. **Cada Sentencia rompe el piso** y deja un **vacío** que nadie puede cruzar, ni volando (los ataques sí pasan por arriba). Nunca aparece debajo de nadie ni delante de las puertas.

Arceus no tira el anillo de balas ni las piedras verdes.

**Arceus Beta:** cuando vencés a Arceus, desaparece y empiezan a caer Sentencias por toda la mitad de arriba de la arena hasta que queda vacía. Si estabas arriba, te pasa a la mitad de abajo. Ahí aparece **Arceus Beta**, mucho más grande que vos, flotando sobre el vacío y moviéndose de un lado al otro; se le pega desde el borde o a distancia. Tiene el doble de vida que Arceus y su barra también se parte en 3 fases.
1. **Tablas:** cada 2,2 s invoca la tabla del tipo que sigue (las 17, todas menos normal; como mucho 6 a la vez). Las tablas dan vueltas a su alrededor, brillan antes de atacar y tiran ataques de su tipo más grandes que los normales:
   - eléctrico, tierra, roca, psíquico, fantasma, hada y dragón: una marca grande que cae donde estás;
   - fuego, volador, veneno, bicho, lucha y siniestro: 3 balas grandes en abanico;
   - agua, planta, hielo y acero: una bala grande apuntada.
2. y 3. **Por definir** (por ahora sigue con las tablas).

Al vencer a Arceus Beta el piso vuelve y se puede salir. Los sprites se buscan en `assets/sprites/pokemones/sprite_arceus_beta`; si no están, usa los de Arceus.

**Arena de El Origen:** la sala de Regigigas y la de Arceus es **redonda y más grande** (23 × 23 casillas en vez de 21 × 15). Regidrago todavía pelea como los demás jefes.

**Premios:**
- **Monedas:** 120 el semijefe, 250 el Regi.
- **Una MT** que alguien de tu equipo pueda aprender.
- **El Regi**, además, suelta el objeto de evolución que necesite alguien de tu equipo.

**Otras monedas:** cada enemigo suelta 4 + número de era, y completar una sala da 10 + 3 × era.

---

## Tienda

La atiende Kecleon. Acercate a una vitrina y apretá E para comprar.

**Cómo están acomodadas las vitrinas:**
- **Estantes:** objetos comunes y una MT que alguien de tu equipo puede aprender.
- **Mesas:** objetos permanentes. Uno suele ser del tipo de tu equipo o el objeto de evolución que alguien necesita.

**Nada cura.**

| Tipo de objeto | Ejemplos |
|---|---|
| Por 3 salas | Ataque X (+25% daño), Defensa X (−20% daño recibido), Velocidad X, Especial X (recargas más rápidas), Directo (20% de críticos x1,8), Lazo Amistad |
| Repelentes | Repelente, Superrepelente, Maxirepelente: 35% menos enemigos por 3, 5 u 8 salas |
| Permanentes | Éter (energía), Cinta Fuerte (+12% daño), Garra Rápida, Polvo Veloz, Chaleco Asalto, Amuleto Moneda (+50% monedas) |
| De tipo | +20% de daño a los ataques de ese tipo (ver cada tipo) |
| Evolución | Piedra Trueno, Piedra Alba, Garra Afilada, Cordón Unión |
| MT | enseñan un movimiento en una casilla. Se gastan al usarlas |

---

## Clima

**Cómo cambia:**
- Cada sala tiene un clima y cambia de a poco: nunca pasa de lluvia a sol de golpe.
- En los lugares cerrados (cuevas, mazmorras, fábricas…) no hay clima.
- Algunos movimientos traen un clima por **15 segundos**:
  - Hidrobomba: lluvia.
  - Llamarada y Rayo Solar: sol.
  - Ventisca y Viento Hielo: granizo.
  - Terremoto y Avalancha: tormenta de arena.
  - Bola Sombra y Pulso Umbrío: niebla.
  - Trueno: tormenta eléctrica.
- **El granizo y la tormenta de arena lastiman** a los que no son inmunes, pero solo cuando los trae un movimiento.

| Clima | Daño | Velocidad | Qué hace en la sala |
|---|---|---|---|
| Lluvia | agua x1,4 · fuego x0,6 | agua +15% | hace charcos y lodo, apaga el fuego |
| Día soleado | fuego x1,4 · agua x0,6 | planta +20% | derrite el hielo, seca charcos y lodo |
| Nevada | hielo x1,2 | hielo +15% | junta nieve y congela charcos |
| Granizo | hielo x1,4 | hielo +20% | congela el agua. Lastima a todos menos hielo |
| Tormenta de arena | roca x1,3 · tierra x1,15 | tierra +15% | lastima a todos menos roca, tierra y acero |
| Niebla | fantasma x1,2 · siniestro x1,2 | — | los enemigos te ven a menos distancia (60%) |
| Tormenta eléctrica | eléctrico x1,3 | eléctrico +15% | caen rayos (prefieren enemigos, metal y agua) |
| Nublado / Despejado | — | — | — |

---

## Características de cada tipo

Además de la tabla de tipos, cada tipo cambia cómo te va en el mundo:
- **Terreno:** qué pasa cuando lo pisás.
- **Máquinas:** te ayudan si estás cerca. Muestran su radio solo si te sirven.
- **Reacciones:** qué hacen tus ataques sobre el terreno.
- **Materiales:** cuánto daño le hacés a los objetos.

| Tipo | Pokemon en el juego |
|---|---|
| Normal | Fletchling · jefes: Regigigas, Arceus |
| Fuego | Torchic, Combusken, Blaziken, Fletchinder, Talonflame |
| Agua | Squirtle, Wartortle, Blastoise, Mudkip, Marshtomp, Swampert, Froakie, Frogadier, Greninja, Oshawott, Dewott, Samurott, Samurott de Hisui, Wooper, Quagsire, Spheal, Sealeo, Walrein, Lapras, Mareanie, Toxapex |
| Eléctrico | Pichu, Pikachu, Raichu, Mareep, Flaaffy, Ampharos, Shinx, Luxio, Luxray, Electrike, Manectric, Magnemite, Magneton, Magnezone · jefe: Regieleki |
| Planta | Chikorita (y Celebi en el menú) |
| Hielo | Snorunt, Glalie, Froslass, Vanillite, Vanillish, Vanilluxe, Sneasel, Weavile, Spheal, Sealeo, Walrein, Lapras · jefe: Regice |
| Lucha | Mankey, Primeape, Annihilape, Machop, Machoke, Machamp, Timburr, Gurdurr, Conkeldurr, Riolu, Lucario, Combusken, Blaziken, Hawlucha |
| Veneno | Mareanie, Toxapex, Clodsire |
| Tierra | Sandshrew, Sandslash, Cubone, Marowak, Geodude, Graveler, Golem, Gible, Gabite, Garchomp, Golett, Golurk, Wooper, Quagsire, Clodsire, Marshtomp, Swampert |
| Volador | Rookidee, Corvisquire, Corviknight, Fletchling, Fletchinder, Talonflame, Natu, Xatu, Drifloon, Drifblim, Hawlucha |
| Psíquico | Natu, Xatu |
| Roca | Geodude, Graveler, Golem · jefe: Regirock |
| Fantasma | Drifloon, Drifblim, Golett, Golurk, Froslass, Annihilape |
| Dragón | Gible, Gabite, Garchomp · jefe: Regidrago |
| Siniestro | Sneasel, Weavile, Greninja, Samurott de Hisui |
| Acero | Magnemite, Magneton, Magnezone, Lucario, Corviknight · jefe: Registeel |
| Bicho / Hada | ningún pokemon todavía (están en la tabla de tipos) |

### 🔥 Fuego
- **Terreno:**
  - en fuego: +20% daño.
  - en lava: +35% daño, +10% velocidad, y la cruza.
  - en roca volcánica y ceniza: energía x1,5.
- **Máquinas:** brasero y forja (+30% daño, recargas más rápidas), fogata y horno (+30–35% daño, energía x2).
- **Sus ataques:**
  - prenden fuego la hierba y el aceite (el fuego se esparce);
  - derriten hielo y nieve, secan charcos, lodo y sombra;
  - vuelven a encender braseros, fogatas, forjas y hornos apagados.
- **Clima:** x1,4 con sol, x0,6 con lluvia.
- **Materiales:** hielo, planta y tela x4; madera y basura x3; metal x2; hueso x0,5; piedra x0,3. Rompe de un golpe todo lo que arde.
- **Especial de velocista:** Rueda Fuego · **Asistencia de atacante:** Llamarada · **Objeto:** Carbón.

### 💧 Agua
- **Terreno:** cruza el agua (no lo frena). En agua +30% velocidad, en charco +15%, en lodo +5%.
- **Máquinas:** cascada (+30% daño, energía x3, recargas más rápidas).
- **Sus ataques:**
  - apagan el fuego;
  - convierten arena en lodo, lava en roca volcánica y tóxico en charco;
  - apagan braseros, fogatas, forjas y hornos;
  - **hacen explotar los generadores** (cortocircuito);
  - electrifican los cables.
- **Clima:** x1,4 con lluvia, x0,6 con sol.
- **Materiales:** planta x0,5.
- **Especial de velocista:** Cascada · **Asistencia:** Hidrobomba (atacante), Viento Hielo masivo (estratega) · **Objeto:** Agua Mística.

### ⚡ Eléctrico
- **Terreno:** en cables energía x3 y recargas −20% (a los demás los cables los lastiman).
- **Máquinas:** generador (recargas −25%, energía x3), imán (energía x1,5).
- **Sus ataques:**
  - **electrifican toda el agua conectada** (agua, charcos, cascadas) por 3 s, y los que estén adentro reciben daño y se paralizan;
  - descargan el generador sobre los enemigos;
  - arreglan generadores rotos;
  - dan vuelta las cintas transportadoras;
  - contra objetos de metal sueltan una chispa que paraliza.
- **Defensa:** inmune al agua electrificada y a las chispas de las explosiones eléctricas.
- **Clima:** x1,3 y +15% velocidad con tormenta eléctrica.
- **Materiales:** vidrio x2; metal x0,5; piedra x0,3.
- **Especial:** Placaje Eléctrico (velocista), Onda Trueno paraliza en área (estratega) · **Asistencia:** Trueno (atacante), Onda Trueno masiva (estratega) · **Objeto:** Imán.

### 🌿 Planta
- **Terreno:** en hierba **queda escondido** (los enemigos casi no lo ven) y +20% velocidad.
- **Sus ataques:** hacen crecer hierba sobre el suelo (35%) y la ceniza (50%).
- **Clima:** +20% velocidad con sol.
- **Materiales:** madera x0,5; no le hace nada a las plantas.
- **Asistencia de atacante:** Rayo Solar · **Objeto:** Semilla Milagro.

### ❄️ Hielo
- **Terreno:**
  - en hielo **+70% velocidad y correr no gasta energía**, y no resbala;
  - en nieve +25% velocidad, mientras a los demás los frena.
- **Máquinas:** cascada helada (+30% daño, energía x2, recargas más rápidas).
- **Sus ataques:**
  - **congelan el agua y los charcos** (se puede caminar por arriba);
  - apagan el fuego, enfrían la lava;
  - congelan cascadas;
  - apagan fogatas y hornos.
- **Clima:** x1,2 con nevada, x1,4 con granizo (y no lo lastima).
- **Materiales:** planta x2; no le hace nada al hielo.
- **Especial:** Esquirla Helada (velocista), Viento Hielo ralentiza en área (estratega) · **Asistencia:** Ventisca (atacante), Viento Hielo masivo (estratega) · **Objeto:** Antiderretir.

###  Lucha
- **Sus ataques:** **empujan** cajas, barriles y bloques de hielo; lo que se desliza le pega a los enemigos.
- **Materiales:** piedra x3; madera, vidrio, hielo, cerámica y hueso x2; metal x1,5. Es el mejor para romper cosas.
- **Especial de velocista:** Patada Salto Alta · **Asistencia de atacante:** Onda Certera · **Objeto:** Cinturón Negro.

###  Veneno
- **Terreno:** en tóxico +30% daño y +15% velocidad (a los demás los envenena).
- **Sus ataques:** vuelven **tóxica** el agua y los charcos.
- **Materiales:** basura x0,2.
- **Asistencia:** Bomba Lodo (atacante), Canto duerme a toda la sala (estratega) · **Objeto:** Flecha Venenosa.

###  Tierra
- **Terreno:** en arena +15% velocidad y en lodo +20% (a los demás los frenan); los cables no lo lastiman.
- **Máquinas:** monolito (−15% daño recibido).
- **Sus ataques:** desactivan los cables (los vuelven suelo).
- **Defensa:** inmune al agua electrificada.
- **Clima:** x1,15 y +15% velocidad con tormenta de arena (y no lo lastima).
- **Materiales:** piedra, metal, cerámica y hueso x2.
- **Especial de velocista:** Taladradora · **Asistencia de atacante:** Terremoto · **Objeto:** Arena Fina.

###  Volador
- **Terreno:**
  - vuela por encima de casi todo: **cruza agua y lava**;
  - no resbala en hielo ni aceite;
  - no lo frenan nieve, arena ni lodo, y las cintas no lo llevan;
  - el fuego y la lava apenas lo lastiman;
  - en corriente de aire +50% velocidad y correr gratis.
- **Defensa:** inmune al agua electrificada.
- **Materiales:** planta y tela x2.
- **Especial de velocista:** Pájaro Osado · **Asistencia de atacante:** Vendaval · **Objeto:** Pico Afilado.

###  Psíquico
- **Máquinas:** altar (recargas −20%, +15% daño).
- **Sus ataques:** **empujan** objetos, más fuerte que lucha.
- **Materiales:** vidrio x1,5.
- **Especial de velocista:** Cabezazo Zen · **Asistencia:** Psíquico (atacante), Desvanecer (estratega) · **Objeto:** Cuchara Torcida.

###  Roca
- **Terreno:** no lo frena la arena; en roca volcánica −10% daño recibido.
- **Máquinas:** monolito (−25% daño recibido, +15% daño).
- **Clima:** x1,3 con tormenta de arena (y no lo lastima).
- **Materiales:** vidrio x3; piedra, hielo y cerámica x2; madera y hueso x1,5.
- **Especial de velocista:** Rodar · **Asistencia de atacante:** Avalancha · **Objeto:** Piedra Dura.

###  Fantasma
- **Terreno:** en sombra **queda escondido** y +15% velocidad. **Atraviesa los objetos** (no lo frenan cajas, rocas ni barriles).
- **Máquinas:** altar (+20% daño).
- **Clima:** x1,2 con niebla.
- **Especial de velocista:** Sombra Vil · **Asistencia:** Bola Sombra (atacante, trae niebla), Desvanecer (estratega) · **Objeto:** Hechizo.

###  Dragón
- **Terreno:** **cruza la lava** y en ella +15% daño; el fuego no lo lastima.
- **Máquinas:** cristal dragónico (+30% daño, +10% velocidad).
- **Especial de velocista:** Carga Dragón · **Asistencia de atacante:** Cometa Draco · **Objeto:** Colmillo Dragón.

###  Siniestro
- **Terreno:** en sombra **queda escondido** y +25% daño.
- **Sus ataques:** a veces llenan de sombra el suelo (25%).
- **Clima:** x1,2 con niebla.
- **Especial de velocista:** Persecución · **Asistencia de atacante:** Pulso Umbrío (trae niebla) · **Objeto:** Gafas de Sol.

###  Acero
- **Terreno:** no resbala en aceite, no lo frena la arena, el tóxico no lo lastima, y las cintas lo llevan menos (pesa más).
- **Máquinas:** imán (−25% daño recibido), forja (−20% daño recibido, +15% daño), horno (−15% daño recibido).
- **Clima:** la tormenta de arena no lo lastima.
- **Materiales:** piedra, vidrio y hielo x2; metal x0,5.
- **Especial de velocista:** Puño Bala · **Asistencia de atacante:** Foco Resplandor · **Objeto:** Revestimiento Metálico.

###  Normal
- **Terreno:** no lo frenan nieve, arena ni lodo.
- **Máquinas:** fogata (energía x1,5).
- **Especial de velocista:** Velocidad Extrema · **Asistencia de atacante:** Hiperrayo · **Objeto:** Pañuelo Seda.

###  Bicho y  Hada
No hay pokemon de estos tipos todavía.
- **Bicho:** se esconde en la hierba (+20% velocidad) y hace x2 a planta y tela.
- **Hada:** el altar le acelera las recargas un 20%.

---

## Tabla de tipos

Daño que hace el tipo de la **fila** (atacante) contra el tipo de la **columna** (defensor).

- **2** = súper eficaz (x2)
- **½** = poco eficaz (x0,5)
- **0** = no le afecta. **En este juego vale x0,2**: igual hace un poquito de daño, para que nunca quede imposible.
- **·** = normal (x1)

Si el defensor tiene dos tipos, se multiplican. Por ejemplo, hielo contra Garchomp (dragón/tierra) es 2 × 2 = **x4**.

| Ataca ↓ / Defiende → | NOR | FUE | AGU | ELE | PLA | HIE | LUC | VEN | TIE | VOL | PSI | BIC | ROC | FAN | DRA | SIN | ACE | HAD |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Normal** | · | · | · | · | · | · | · | · | · | · | · | · | ½ | 0 | · | · | ½ | · |
| **Fuego** | · | ½ | ½ | · | **2** | **2** | · | · | · | · | · | **2** | ½ | · | ½ | · | **2** | · |
| **Agua** | · | **2** | ½ | · | ½ | · | · | · | **2** | · | · | · | **2** | · | ½ | · | · | · |
| **Eléctrico** | · | · | **2** | ½ | ½ | · | · | · | 0 | **2** | · | · | · | · | ½ | · | · | · |
| **Planta** | · | ½ | **2** | · | ½ | · | · | ½ | **2** | ½ | · | ½ | **2** | · | ½ | · | ½ | · |
| **Hielo** | · | ½ | ½ | · | **2** | ½ | · | · | **2** | **2** | · | · | · | · | **2** | · | ½ | · |
| **Lucha** | **2** | · | · | · | · | **2** | · | ½ | · | ½ | ½ | ½ | **2** | 0 | · | **2** | **2** | ½ |
| **Veneno** | · | · | · | · | **2** | · | · | ½ | ½ | · | · | · | ½ | ½ | · | · | 0 | **2** |
| **Tierra** | · | **2** | · | **2** | ½ | · | · | **2** | · | 0 | · | ½ | **2** | · | · | · | **2** | · |
| **Volador** | · | · | · | ½ | **2** | · | **2** | · | · | · | · | **2** | ½ | · | · | · | ½ | · |
| **Psíquico** | · | · | · | · | · | · | **2** | **2** | · | · | ½ | · | · | · | · | 0 | ½ | · |
| **Bicho** | · | ½ | · | · | **2** | · | ½ | ½ | · | ½ | **2** | · | · | ½ | · | **2** | ½ | ½ |
| **Roca** | · | **2** | · | · | · | **2** | ½ | · | ½ | **2** | · | **2** | · | · | · | · | ½ | · |
| **Fantasma** | 0 | · | · | · | · | · | · | · | · | · | **2** | · | · | **2** | · | ½ | · | · |
| **Dragón** | · | · | · | · | · | · | · | · | · | · | · | · | · | · | **2** | · | ½ | 0 |
| **Siniestro** | · | · | · | · | · | · | ½ | · | · | · | **2** | · | · | **2** | · | ½ | · | ½ |
| **Acero** | · | ½ | ½ | ½ | · | **2** | · | · | · | · | · | · | **2** | · | · | · | ½ | **2** |
| **Hada** | · | ½ | · | · | · | · | **2** | ½ | · | · | · | · | · | · | **2** | **2** | ½ | · |

Abreviaturas: NOR normal · FUE fuego · AGU agua · ELE eléctrico · PLA planta · HIE hielo · LUC lucha · VEN veneno · TIE tierra · VOL volador · PSI psíquico · BIC bicho · ROC roca · FAN fantasma · DRA dragón · SIN siniestro · ACE acero · HAD hada.

---

## Herramientas

Programas aparte para preparar el juego. No se usan mientras jugás.

```
python herramientas.py descargar           baja sprites y retratos del PMD (SpriteCollab) a assets/sprites/pokemones
python herramientas.py datos               arma datos_pokeapi.json desde la PokeAPI (stats, movimientos, evoluciones)
python herramientas.py recortar hoja.png   recorta sprites de una hoja y los guarda en assets/mundo
python herramientas.py visor               ventana para mirar salas generadas sin jugar
python herramientas.py salas               dibuja en texto algunas salas generadas
python herramientas.py plan                muestra el plan de salas de una partida
python herramientas.py verificar           compara tipos y movimientos con la PokeAPI (hoy no anda: espera la tabla de tipos vieja)
python herramientas.py sincronizar         NO USAR: pisa datos_pokeapi.json con un formato viejo (sin evoluciones ni movimientos)
```

**Teclas del visor:**
- ← → era · ↑ ↓ variante.
- T: tipo de sala (combate, tienda o arena).
- ESPACIO: otra sala.
- C: probar los climas.
- P: ver el plan de una partida.
- S: guardar una captura.
- ESC: salir.
