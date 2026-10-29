# Pokemanic

Juego de acción en Python con Pygame. Recorrés la historia de la humanidad sala por sala con un equipo de hasta 3 pokemon, peleás en tiempo real y enfrentás a un Regi al final de cada era, hasta llegar a Regigigas y Arceus.

```
python main.py
```

Necesita `pygame`. Las partidas se guardan en la carpeta `partidas/`. En la misma carpeta tienen que estar los 7 `.py`, `config.json`, `datos_pokeapi.json`, `cache_pokeapi.json` y la carpeta `assets` (sprites del PMD).

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
| `sistema.py` | opciones (`config.json`), partidas guardadas (`partidas/`), pantalla, controles (teclado y joystick) y animaciones |
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
| Esquivar (gasta energía) | Espacio | palanca izq (L3) |
| Ataque cuerpo a cuerpo / parry | E / clic izquierdo | X |
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
- **Partidas:** al tocar *Jugar* elegís una de las **3 partidas guardadas**. Se guarda sola al entrar a cada sala, al completarla y al comprar (equipo, niveles, experiencia, EV, MT, objetos, monedas y el camino recorrido). Si cae todo el equipo, podés reintentar la sala desde como estabas al entrar.
- Peleás con un solo pokemon a la vez. Los otros dos esperan en la **banca**. Cambiar de pokemon tiene una espera de 2 s. Si cambiás en el agua a uno que no nada, nada solo hasta la orilla.
- Cada sala de combate trae enemigos, a veces en 2 o 3 oleadas. Al limpiar la sala aparece una **llave**, y con la llave se abren las puertas.
- Cada puerta muestra un cartel con lo que hay detrás: una variante de sala, la tienda, el jefe o la era siguiente.
- **Volver atrás:** con la sala completada, la puerta por la que entraste queda abierta y te lleva a la sala anterior. Las salas hechas quedan hechas (sin enemigos, sin monedas ni experiencia de nuevo); en ellas solo sigue abierta la puerta que tomaste.
- **La vida no se recupera sola.** Al limpiar una sala, los que siguen en pie recuperan un **12%**. Si tu pokemon activo cae, entra solo el siguiente que esté vivo.
- **Energía:** la barra azul debajo de la vida. Correr y esquivar la gastan; se recarga sola y también al pegar, hacer parry o esquivar perfecto. Si se vacía, quedás agotado hasta recuperar un poco. Al empezar a correr arrancás con un pique.
- **Enemigos:** avisan antes de atacar. Un anillo rojo es un golpe, una línea con mira es un disparo y una línea naranja es una embestida. Como mucho dos te atacan cuerpo a cuerpo al mismo tiempo. Si te escondés en hierba o sombra (si tu tipo puede), casi no te ven.
- **Tipos de enemigo según su rol:**
  - **Pegadores** (tanques y atacantes): van directo hacia vos.
  - **Tiradores** (estrategas): disparan de lejos y se esconden para recargar.
  - **Rápidos** (velocistas): te rodean y embisten en línea recta.

### Ataques

| Botón | Qué hace |
|---|---|
| Cuerpo a cuerpo | **combo de 3 golpes** (el 3º es un remate que barre, empuja lejos e interrumpe a los enemigos comunes) |
| A distancia | 65% del daño y tarda 1,5 veces más en recargar, pero es seguro |
| Especiales (2) | dependen del rol del pokemon (ver [Roles](#roles)) |
| Asistencias (2) | las tira un pokemon de la banca; tardan mucho en recargar (45 a 90 s). Escalan con el nivel del que la tira |
| Esquivar | salto corto con invulnerabilidad hacia donde caminás (quieto: para atrás) |

**Pelear de cerca rinde:** cada golpe del combo que conecta te devuelve energía y le saca espera a tus dos especiales (el remate, más). Si atacás corriendo, el primer golpe es un **golpe en carrera** (más daño y alcance). El golpe se acomoda solo hacia un enemigo cercano que tengas casi adelante.

**Parry:** golpeá cuerpo a cuerpo justo cuando un enemigo te va a pegar. El momento lo marca el propio enemigo: **su aviso brilla amarillo con un "!"**. Si acertás, queda aturdido 1,8 s y recibe el doble, y vos recuperás energía, 3% de vida y 1,5 s de espera de los especiales. Las balas que te llegan durante el parry vuelven con el doble de daño. Si no bloqueás nada, tenés que esperar un poquito para volver a intentarlo (apretar sin parar no sirve).

**Esquive perfecto:** si te iban a pegar mientras esquivabas, recuperás energía y tu próximo golpe es un **contraataque** (x1,8). El piso que quema o lastima no se esquiva.

**Congelamiento:** solo te congela un golpe fuerte de tipo hielo (un rayo de Regice, un pokemon de hielo que te pega de lleno). Los golpecitos cargan la barra celeste, que se descarga sola. Pisar hielo o escarcha solo resbala. Los de tipo hielo no se congelan.

Cada pokemon tiene 4 casillas de movimiento (E, Q, Shift, R). Desde la ficha del menú de equipo podés reemplazar una con una **MT**:
- **MT de combate:** golpes y disparos con tiempos de ataque básico. Van en **cualquier casilla**. Las aprenden los pokemon de su tipo (las de tipo normal, todos).
- **MT especiales:** embestidas, ondas, buffs y disparos grandes que tardan segundos en recargar. Van **solo en Shift o R** (en E o Q dejarían al pokemon sin ataque básico).

La ficha de cada pokemon explica qué hace cada stat, movimiento, objeto y sinergia (el recuadro de abajo muestra lo que tenés elegido).

---

## Roles

Cada pokemon tiene un rol que cambia sus números, sus especiales, su asistencia y el bonus que da desde la banca.

| Rol | Velocidad | Vida | Daño | Recarga | Especiales | Asistencia desde la banca | Sinergia (banca) |
|---|---|---|---|---|---|---|---|
| **Tanque** | 3,5 | x1,35 | x0,9 | x1,15 (más lenta) | Defensa Férrea + onda de área de su ataque | **Escudo:** el activo recibe solo el 25% del daño por 5 s | menos daño recibido |
| **Atacante** | 4,7 | x1 | x1,3 | x1 | proyectil potenciado (+60% daño, atraviesa) + Danza Espada | **Impacto:** golpe de área (60 de daño) donde apuntás | más daño |
| **Estratega** | 4,3 | x1,05 | x0,95 | x0,9 | estado en área (paraliza, ralentiza o duerme) + Recuperación o Paz Mental | **Curar** 40%, **Desvanecer** (fantasma/psíquico: borra enemigos comunes) o **Masivo** (estado a toda la sala) | recargas más rápidas |
| **Velocista** | 6 | x0,8 | x0,8 | x0,7 (más rápida) | embestida de su tipo + Agilidad | **Carrera:** +60% velocidad y correr gratis por 6 s | más velocidad |

**Sinergia:** cada pokemon de la banca le da al que pelea un bonus pasivo de 5% a 10% (cuanta más vida base tiene la especie, mayor). Por defecto es el de su rol, pero **se elige en su ficha**: más daño, menos daño recibido, más velocidad, recargas más rápidas o energía (esta vale el triple).

**Ajustes de balance:** Danza Espada da +40% por 5 s (antes +60% por 6 s), Defensa Férrea −40% de daño por 4,5 s, Recuperación cura 20% cada 18 s (antes 30% cada 15 s), Agilidad también acelera las recargas, y Desvanecer le saca el 60% de la vida a los enemigos comunes (antes los borraba). Los ataques básicos de todas las especies quedaron parejos (antes muchos tenían datos de relleno o un tipo equivocado), y las especies con más stats base pegan un poco más (x1 con 300 de total, hasta x1,25 con 600), así evolucionar se nota.

Algunos pokemon tienen una asistencia propia:
- **Pikachu y Pichu:** Trueno.
- **Froslass:** Mismo Destino (desvanecer).

---

## Niveles y stats

- Tu pokemon empieza en **nivel 5**. El máximo es **100**.
- **Stats como en los juegos:** `stat = (2·base + IV + EV/4) · nivel/100 + 5`. Los PS suman además `nivel + 10`. Las bases salen de la PokeAPI (`datos_pokeapi.json`).
- **IV:** cada pokemon nace con IVs al azar de 0 a 31 en cada stat. Por eso dos del mismo pokemon no son iguales.
- **EV:** cada nivel da **1 punto**, que equivale a 10 EV. Lo ponés en el stat que quieras desde la ficha del menú de equipo. El máximo es **300 EV por stat** y 900 en total; la ficha muestra cuánto llevás de cada uno y, si no se puede sumar, te dice por qué.
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

- Los pokemon de la **banca ganan 3/4** de la experiencia.
- La experiencia general se multiplica por `XP_MULT` (0,6 en `combate.py`; antes era 0,4, o sea +50%).
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
1. Apenas un pokemon del equipo llega a su nivel, consigue el objeto o junta la amistad, el juego se pausa y aparece un cartel (como el de los que quieren unirse) que pregunta si querés **Evolucionar** o **Todavía no**.
2. Si decís que no, vuelve a preguntar cuando sube otro nivel (o cuando conseguís otro objeto, si evoluciona con objeto). También podés hacerlo cuando quieras desde el menú de equipo (TAB): entrá a su ficha y elegí **Evolucionar**.

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

**Los 5 Regis** (Regice, Regirock, Registeel, Regidrago y Regieleki) llaman a **5 pokemon de su mismo tipo** una vez: Regice y Regieleki al perder un cuarto de su vida, y Regirock, Registeel y Regidrago al perder el 10% (en su primera fase). Primero aparecen las marcas rojas donde van a salir.

Los jefes con fases muestran en la barra de vida dónde cambian y avisan con un cartel cuando pasan a la siguiente.

**Sala de los Regis:** redonda, grande y vacía. Cuando cae el Regi se van los muros, rocas, bloques, jaulas y torres que haya armado.

**Regice** (2 fases: 100–50% y 50–0%):
- **Rayo Hielo:** una línea celeste fija que se va engrosando y después dispara un rayo ancho hasta la pared. El piso por donde pasa queda **escarcha**: resbala.
- **Congelamiento:** la escarcha solo resbala. Lo que congela es que te pegue el **Rayo Hielo** (o las estalactitas): cada golpe de hielo carga la barra celeste (arriba de tu barra de vida) según cuánto te sacó, y un golpe de lleno te congela **2 s**. Congelado no podés moverte ni atacar; un **movimiento de fuego o de lucha** te descongela al instante.
- **Muro de hielo** cada 5 s: 3 bloques entre él y vos que **solo se rompen con fuego**.
- **Fase 1:** cada Rayo Hielo deja al final un **bloque de hielo** (como mucho 3 a la vez). Parate al lado y apretá **E**: sale para el lado contrario y se desliza por la escarcha.
- **Fase 2:** se cubre con una **coraza de hielo** (recibe solo el 20% del daño). Se rompe cuando le chocás uno de los bloques de la fase 1; rota, recibe **x1,6** de daño el resto de la pelea. Además el Rayo Hielo **rebota en las paredes** y queda 5 s (Regice se queda quieto mientras dura) y caen **estalactitas**: una sombra que crece en el piso y después cae el hielo.

**Regirock** (3 fases: 100–75%, 75–25% y 25–0%):
- **Fase 1:** **Roca Afilada** (una fila de rocas que sale hacia vos y, si no te pega, deja una roca al final) y **Avalancha**: se queda quieto haciendo el lanzamiento y tira 6 rocas que caen en **hexágono** alrededor tuyo. Lastiman al caer y quedan 5 s como obstáculo.
- **Fase 2:** Avalancha, Roca Afilada y **Fuerza Bruta** (una franja roja marca hacia dónde embiste; si choca contra una roca o una pared queda aturdido 3 s). Alrededor de cada roca que deja la Roca Afilada aparece **arena movediza**: frena mucho y lastima un poquito (a los voladores no les hace nada).
- **Fase 3:** **se parte en 5 rocas rodantes** que rebotan en las paredes y en las rocas. Cada una tira **Lanzarrocas** (6 rocas chicas alrededor) y lastima si te choca. Cuando una se queda sin vida, se frena, titila y **explota**. La barra del jefe es la suma de las 5.

**Registeel** (3 fases: 100–75%, 75–25% y 25–0%):
- **Sierras** (todas las fases): 2 sierras que rebotan en las paredes durante 7 s o hasta que te pegan.
- **Fase 1:** sierras y llama refuerzos.
- **Fase 2:** además **minas** (3, una donde estás, que explotan al rato en 8 balas) e **imán**: se queda quieto 4 s y alterna entre **atraer** (violeta) y **alejar** (naranja) al jugador **y a las minas**. Las minas que le explotan cerca a él también lo lastiman.
- **Fase 3:** sierras, imán, **Foco Resplandor** (un rayo que va siguiendo por donde estabas medio segundo antes, así se puede esquivar) y **Cuerpo Pesado** (salta fuera de la pantalla, su sombra te sigue, se frena un momento y cae).

**Regidrago** (3 fases: 100–75%, 75–25% y 25–0%):
- **Fase 1:** **Enfado** (embiste dejando fuego) y llama refuerzos.
- **Fase 2:** te muerde y te lleva a lo alto de su torre: **Cometa Draco**, bocas de dragón que tiran **Dragoaliento** y al 25% **Draco Energía**; después la torre se rompe.
- **Fase 3:** de vuelta en la sala usa todo junto. **Draco Energía** sigue por donde estabas (se esquiva) y en esta fase **no lo hace invencible**. Las **bocas** que tiran Dragoaliento tienen vida y se pueden romper.

**Regieleki** (3 fases: libre, en las torres y sin torres):
- Su sala tiene **6 torres eléctricas** (cuadrados grises). Tira **5 rayos** en abanico.
- Al perder un cuarto de vida **se mete en una torre** (se pone amarilla) y no se le puede pegar. Pegarle a esa torre le pega a él. Si le pegaste, a los 3 s se pasa a otra torre y la anterior queda **marrón** (no puede volver); si no le pegaste, a los 8 s se cambia igual y la torre vuelve a gris. En el camino deja una **línea amarilla** que lastima, y al llegar tira los 5 rayos.
- Sin torres: **se teletransporta** cada 2 s y larga **Alto Voltaje**, una onda que crece durante 3 s. Además usa **Jaula Voltio**: un cuadrado eléctrico aparece alrededor tuyo, lastima si lo tocás y se rompe con **2 ataques** (si no, desaparece a los 7 s).

**Regigigas** pelea distinto:
- **Lento Inicio:** los primeros **10 s** está quieto con la **defensa subida** (recibe el 30% del daño). Un anillo alrededor suyo se va llenando; cuando despierta usa **Terremoto**.
- **Terremoto:** un anillo marrón con grietas se llena alrededor suyo y pega a todo lo que esté adentro. Es de tipo tierra, así que a los voladores casi no les hace nada. La pantalla tiembla.
- **Megapuño:** una mira roja aparece donde estás parado, se cierra y cae el puño. Vienen de a 3 seguidos.
- **Gigaimpacto:** una franja roja marca hacia dónde carga; embiste hasta donde estabas y pega muy fuerte. Después queda 1,2 s quieto recargando.
- **Protección:** si le pegás mucho seguido, se cubre con un escudo verde durante 3 s y se queda quieto sin recibir daño.
- **Agarrón:** si estás cerca, se marca un anillo naranja; si seguís adentro cuando se cierra, te agarra y te tira para atrás. **Solo lastima si chocás contra una pared.**
- **Regis chiquitos:** después de despertar, cada 11 s llama a 2 versiones chicas de los Regis, como mucho 4 a la vez.

**Arceus** tiene la barra de vida partida en **3 fases** (100–65%, 65–20% y 20–0%) y avisa con un cartel cuando cambia. Usa un movimiento por vez, elegido al azar entre los de su fase, con una pausa corta entre uno y otro:

| Movimiento | Fase 1 | Fase 2 | Fase 3 | Qué hace |
|---|:-:|:-:|:-:|---|
| **Hiperrayo** | ✔ | ✔ | ✔ | Una franja del ancho de Arceus marca hacia dónde va a salir. Después dispara un rayo de tipo normal, **del mismo ancho que Arceus**, que sale de él y va **siguiendo por donde estabas** medio segundo antes (se esquiva moviéndose). Al terminar **queda 3 s quieto recargando** (estrellitas arriba de la cabeza). |
| **Velocidad Extrema** | ✔ | | ✔ | Una franja roja corta avisa y embiste rapidísimo hacia vos. **Si choca contra una pared no queda aturdido.** |
| **Vozarrón** | ✔ | ✔ | ✔ | Salen de Arceus **3 círculos partidos en 8 arcos** (la mitad de cada tramo es hueco) que se van agrandando durante **5 s**. Cada círculo va girado medio tramo respecto del anterior, así que hay que moverse para pasar por los huecos. Cada uno te pega una vez si un arco te pasa por encima (también se salta con el esquive). |
| **Meteoros** | ✔ | ✔ | ✔ | Caen **7 meteoritos rápidos** uno atrás del otro donde estás parado, cada uno avisado **1 s** antes con una sombra. Arceus sigue haciendo otras cosas mientras caen. |
| **Sentencia (chica)** | | ✔ | | El **sello de Arceus** (círculo con un triángulo y un círculo en cada punta) aparece donde estás, gira, se llena y cae del cielo una columna de luz. Tipo normal, un poco más chico que el sello original. De a 3 seguidas. |
| **Sentencia (grande)** | | | ✔ | Igual, pero un poco **más grande** que el original. De a 2 seguidas. |
| **Protección** | | | ✔ | Escudo verde de **3 s**: no se mueve, no ataca y no recibe daño. Lo usa si le pegás mucho seguido, o cada tanto. |
| **Recuperación** | | | ✔ | Se queda **3 s quieto juntando estrellitas** (no ataca). **Si le pegás se corta**; si no, se cura un 8%. Curarse no lo devuelve a la fase anterior. |

**Recuperación, Velocidad Extrema e Hiperrayo nunca van juntos:** entre uno y otro de esos tres pasan al menos 2,5 s. Los números de cada movimiento (y qué movimientos hay en cada fase) están en `ARCEUS` y `MOVS_ARCEUS` en `combate.py`.

Arceus no tira el anillo de balas ni las piedras verdes.

**Arceus Beta:** cuando vencés a Arceus, desaparece y **quedás en el medio de la arena**. Empiezan a caer Sentencias alrededor, de afuera hacia adentro, y donde caen el **piso y las paredes se vuelven vacío**. Al final todo es vacío menos un **círculo de piso en el medio** (3,5 casillas de radio) donde estás vos. Entonces aparece **Arceus Beta** delante tuyo, mucho más grande que vos, flotando sobre el vacío con **las tablas girando a su alrededor**. Tiene el doble de vida que Arceus y su barra se parte en 3 fases (100–66%, 66–33% y 33–0%).

- **Está quieto en un punto** (solo se mueve en los movimientos que lo necesitan: embestidas, Bote, Teletransporte, Mordisco). Se le pega desde el borde o a distancia.
- **Tablas:** tiene puesta una por vez y usa los 3 movimientos de esa tabla, de a uno, con una pausa corta entre uno y otro. Arranca con la **Tabla Neutra** (sin tabla). Es del tipo de la tabla puesta (Multitipo), y arriba suyo dice qué tabla tiene y qué movimiento está usando.
- **Cambio de tabla:** tarda **2 s** (se saca la puesta y se pone la nueva) y entre un cambio y otro pasan **10 s**. Voltio Cambio la cambia enseguida (animación corta) e Ida y Vuelta al instante (sin animación).

**Fase 1** (en el círculo de piso):

| Tabla | Movimientos |
|---|---|
| **Neutra** | **Vozarrón** (como el de Arceus: círculos en arcos) · **Meteoros** (como los de Arceus) · **Gigaimpacto** (cruza la zona 3 veces por donde estás y vuelve a su lugar) |
| **Llama** | **Lanzallamas** (una línea de fuego que gira de una punta a la otra de la zona, larga hasta la mitad de la zona) · **Llamarada** (estrella de fuego de 5 puntas en el medio; entre las puntas no pega) · **Colmillo Ígneo** (mordida grande de fuego en la esquina de la zona más cerca tuyo) |
| **Trueno** | **Electrocañón** (rayo horizontal o vertical por donde estás) · **Bola Voltio** (3 bolas eléctricas lentas) · **Voltio Cambio** (rayo rápido donde estás con 0,5 s de aviso y cambia de tabla enseguida) |
| **Pradal** | **Hoja Afilada** (10 hojas, 5 de cada lado, que salen de a 2 hacia donde estás) · **Abrecaminos** (pasa por una línea que cruza el medio de la zona y la zona queda partida en dos por 10 s) · **Asta Drenaje** (pasa por una línea vertical u horizontal con un triángulo verde adelante; si te pega se cura el 25% del daño) |
| **Helada** | **Ventisca** (2 s de hielo sobre una gran parte de la zona, la del lado donde estás) · **Chuzos** (estalactitas en lugares al azar) · **Martillo Hielo** (un martillo enorme cae donde estás) |
| **Fuerte** | **Tajo Cruzado** (2 cortes en X por donde estás) · **Puño Drenaje** (puñetazo; si te pega se cura el 25% del daño) · **Llave Giro** (golpe en círculo; si te pega te cambia de pokemon y no podés volver por 2 s. Si no tenés otro pokemon en pie no pasa nada) |
| **Tóxica** | **Bomba Lodo** (3 bolas que dejan 3 charcos chicos; lastiman si los pisás) · **Picotazo Veneno** (15 agujas finas y largas, todas en vertical o todas en horizontal) · **Carga Tóxica** (pasa por una línea al azar y deja un rastro de veneno por 7 s) |
| **Terrax** | **Huesomerang** (3 huesos que van y vuelven; pegan a la ida y a la vuelta) · **Mil Flechas** (20 flechas chicas sobre la zona) · **Bucle Arena** (3 círculos de arena movediza por 4 s; si pisás uno quedás trabado hasta que apretás **E**) |
| **Cielo** | **Bote** (salta, su sombra te sigue 3 s, cae ahí y vuelve) · **Tornado** (una fila de ráfagas cruza la zona en vertical con un hueco para pasar, y después el viento te empuja 5 s para ese lado) · **Pájaro Osado** (embiste hasta donde estás y vuelve) |
| **Mental** | **Psíquico** (te levanta y te tira al lado contrario de la zona; se esquiva justo al final del aviso) · **Psicorruido** (ondas en arcos desde él) · **Teletransporte** (aparece en otro lugar sobre el vacío, afuera de la zona, y se queda ahí) |
| **Bicho** | **Corte Furia** (3 cortes donde estás, cada uno más fuerte) · **Chupavidas** (embestida; si te pega se cura el 50% del daño, pega menos que Asta Drenaje) · **Ida y Vuelta** (golpe rapidísimo sin aviso y cambia de tabla al instante) |
| **Pétrea** | **Roca Veloz** (5 piedras rápidas hacia donde estás) · **Hachazo Pétreo** (un golpe en X en un lugar al azar y después otro en cruz) · **Avalancha** (rocas en lugares al azar) |
| **Oscura** | **Alarido** (6 ataques siniestros en abanico) · **Desarme** (embestida; si te pega perdés un objeto de la mochila) · **Mordisco** (5 mordiscos: antes de cada uno aparece al lado de la zona y muerde hacia adentro) |
| **Duende** | **Fuerza Lunar** (un rayo redondo que te persigue 5 s) · **Brillo Mágico** (la pantalla queda blanca 0,5 s pero el juego sigue, y enseguida usa otro movimiento) · **Cañón Floral** (carga 2 s y tira un ataque en línea recta, horizontal o vertical, que dura 7 s) |

**Fases 2 y 3:** al terminar la fase 1 la pantalla se pone blanca y **el piso se vuelve un triángulo** (la imagen `assets/interfaz/arena_arceus_beta.png`), con Arceus Beta arriba de la punta. Por ahora sigue con las tablas sobre el triángulo; los movimientos propios de estas fases están **por definir**.

Al vencer a Arceus Beta el piso y las paredes vuelven y se puede salir. Los sprites se buscan en `assets/sprites/pokemones/sprite_arceus_beta`; si no están, usa los de Arceus. Los números de cada movimiento están en `MOVS_BETA` en `combate.py` y los de las tablas en `BETA` y `TABLAS_BETA`.

**Arena de El Origen:** la sala de Regigigas y la de Arceus es **redonda y más grande** (23 × 23 casillas en vez de 21 × 15).

**Premios:**
- **Monedas:** 120 el semijefe, 250 el Regi.
- **Una MT** que alguien de tu equipo pueda aprender.
- **El Regi**, además, suelta el objeto de evolución que necesite alguien de tu equipo.

**Otras monedas:** cada enemigo suelta 4 + número de era, y completar una sala da 10 + 3 × era.

---

## Tienda

La atiende Chikorita. Acercate a una vitrina y apretá E para comprar.

**Cómo están acomodadas las vitrinas:**
- **Estantes:** objetos comunes y una MT que alguien de tu equipo puede aprender.
- **Mesas:** objetos permanentes. Uno suele ser del tipo de tu equipo o el objeto de evolución que alguien necesita.

**Objetos equipables y de equipo:** los que dicen *(lo lleva un pokemon)* van a la mochila y se equipan desde la ficha: **cada pokemon lleva hasta 2** y solo cuentan mientras ese pokemon pelea. Los que dicen *(todo el equipo)* valen para todos.

| Tipo de objeto | Ejemplos | Para quién |
|---|---|---|
| Por 3 salas | Ataque X (+25% daño), Defensa X (−20% daño recibido), Velocidad X, Especial X (recargas más rápidas), Directo (20% de críticos x1,8), Lazo Amistad | todo el equipo |
| Repelentes | Repelente, Superrepelente, Maxirepelente: 35% menos enemigos por 3, 5 u 8 salas | todo el equipo |
| Amuleto Moneda | +50% de monedas | todo el equipo |
| Equipables | Éter (energía), Cinta Fuerte (+15% daño), Garra Rápida (−12% recargas), Polvo Veloz (+12% velocidad), Chaleco Asalto (−15% daño recibido), Cinta Focus (ventana de parry +50%), Pluma Ágil (esquive más largo) | un pokemon |
| De tipo | +20% de daño a los ataques de ese tipo (ver cada tipo) | un pokemon |
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
