# Pokemanic

Juego de acción en Python con Pygame. Recorrés la historia de la humanidad sala por sala con un equipo de hasta 3 pokemon, peleás en tiempo real y enfrentás a un Regi al final de cada era, hasta llegar a Regigigas y Arceus.

```
python main.py
```

Necesita `pygame`. Las partidas se guardan en la carpeta `partidas/`. En la misma carpeta tienen que estar los 8 `.py`, `config.json`, `datos_pokeapi.json`, `cache_pokeapi.json` y la carpeta `assets` (sprites del PMD).

---

## Índice

1. [Archivos](#archivos)
2. [Controles](#controles)
3. [Cómo se juega](#cómo-se-juega)
4. [Roles](#roles)
5. [Niveles y stats](#niveles-y-stats)
6. [Evoluciones](#evoluciones)
7. [Amistad: pokemon que se unen](#amistad-pokemon-que-se-unen)
8. [Hall](#hall)
8a. [Tutorial, boss rush y otros modos](#tutorial-boss-rush-y-otros-modos)
8b. [Pokemon nuevos y lo que los hace únicos](#pokemon-nuevos-y-lo-que-los-hace-únicos)
8c. [Estados y curaciones](#estados-y-curaciones)
9. [Eras y salas](#eras-y-salas)
10. [Jefes](#jefes)
11. [Tienda](#tienda)
12. [Clima](#clima)
13. [Características de cada tipo](#características-de-cada-tipo)
14. [Tabla de tipos](#tabla-de-tipos)
15. [Gráficos e interfaz](#gráficos-e-interfaz)
16. [Herramientas](#herramientas)

---

## Archivos

| Archivo | Qué tiene |
|---|---|
| `main.py` | el juego: menús, la partida y el bucle principal |
| `datos.py` | ataques, pokemones (especies, tipos, roles), MT, tienda y mundos (eras, terrenos, objetos) |
| `sistema.py` | opciones (`config.json`), partidas guardadas (`partidas/`), pantalla, controles (teclado y joystick) y animaciones |
| `mundo.py` | generación de salas, entorno (terrenos, objetos, clima) y efectos (partículas) |
| `combate.py` | progreso (niveles, IV/EV, evoluciones, amistad) e IA de enemigos y jefes |
| `mecanicas.py` | la mecánica única de cada línea evolutiva nueva (pasivas y especiales) y lo que hacen algunos enemigos |
| `modos.py` | textos y números del tutorial, el boss rush, los titanes, los minijuegos, las charlas de tus amigos y las misiones |
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
| Bailar (amigar / confundir) | V | palanca der (R3) |
| Evolucionar (mantener) | C | cruz abajo |
| Usar la curación del lugar 1 del [cinturón](#estados-y-curaciones) | Z | sin asignar (se elige en Controles) |
| Menú de equipo | TAB | Back |
| Pausa | ESC | Start |

**Modo de combate** (Ajustes > Combate):
- **mouse:** apuntás con el mouse.
- **teclas:** atacás hacia donde caminaste por última vez.
- **mixto:** usa teclas hasta que movés el mouse.

**Teclas secretas:**
- **F1** (en el menú principal o jugando): menú debug para poner cualquier pokemon en el equipo. Están agrupados por tipo (en el orden de la [tabla de tipos](#tabla-de-tipos), según el tipo principal de la primera forma de cada línea), y adentro de cada tipo por generación, con cada línea evolutiva junta (Pichu, Pikachu y Raichu van seguidos aunque Pichu sea de la 2ª). Con el Konami se suman los jefes, ordenados igual.
- **F2** (jugando): saltar a cualquier sala, tienda o jefe. TAB o Shift cambian de era.
- **Código Konami** (↑ ↑ ↓ ↓ ← → ← → B A) en Ajustes o en la pausa: menú de trucos (vida infinita, sin recarga, todas las MT, monedas infinitas, un golpe mata, subir 5 niveles). Los trucos no se guardan.

---

## Cómo se juega

- **Partida nueva:** se abre el tiempo (la apertura del Explorers of Time) y flotás en el túnel como una lucecita sin forma. Llega Celebi dormido, se despierta, te ve y te pregunta tu **nombre**, tu **género** (chico, chica o prefiero no decirlo; cambia los textos) y **qué pokemon sos** (como armar tu cuerpo en Deltarune: ese pokemon sos vos y lo controlás). Uno por rol, y todos evolucionan:
  - **Mudkip** (agua, tanque → Swampert): aguanta los golpes y pelea de cerca.
  - **Torchic** (fuego, atacante → Blaziken): pega fuerte.
  - **Riolu** (lucha, velocista → Lucario): rápido, vive del parry y del combo.
  - **Natu** (psíquico/volador, estratega → Xatu): controla la sala con estados y desde lejos.
- **Partidas:** al tocar *Jugar* elegís una de las **3 partidas guardadas**. Se guarda sola al entrar a cada sala, al completarla y al comprar (equipo, niveles, experiencia, EV, MT, objetos, monedas, el camino recorrido y tu perfil).
- **Si cae todo el equipo** se pierde el viaje y Celebi te lleva al [hall](#hall). Tus amigos se quedan.
- Peleás con un solo pokemon a la vez. Los otros dos esperan en la **banca**. Cambiar de pokemon tiene una espera de 2 s. Si cambiás en el agua a uno que no nada, nada solo hasta la orilla.
- Cada sala de combate trae enemigos, a veces en 2 o 3 oleadas. Al limpiar la sala aparece una **llave**, y con la llave se abren las puertas.
- Cada puerta muestra un cartel con lo que hay detrás: una variante de sala, la tienda, el jefe o la era siguiente.
- **Volver atrás:** con la sala completada, la puerta por la que entraste queda abierta y te lleva a la sala anterior. Las salas hechas quedan hechas (sin enemigos, sin monedas ni experiencia de nuevo); en ellas solo sigue abierta la puerta que tomaste.
- **La vida no se recupera sola.** Al limpiar una sala, los que siguen en pie recuperan un **12%**. Si tu pokemon activo cae, entra solo el siguiente que esté vivo.
- **Energía:** la barra azul debajo de la vida. Correr y esquivar la gastan; se recarga sola y también al pegar, hacer parry o esquivar perfecto. Si se vacía, quedás agotado hasta recuperar un poco. Al empezar a correr arrancás con un pique.
- **Enemigos:** avisan antes de atacar. Un anillo rojo es un golpe, una línea con mira es un disparo y una línea naranja es una embestida. Como mucho tres te atacan cuerpo a cuerpo al mismo tiempo. Si te escondés en hierba o sombra (si tu tipo puede), casi no te ven.
- **Maniobras** (desde la segunda era, cada vez más seguido): los pegadores a veces encadenan un **segundo golpe** más rápido y, si les pegás de lejos y te escapás mucho rato, **saltan** hasta donde estás (línea naranja). Los tiradores, si te quedás quieto o te escondés, tiran un **mortero** (un círculo rojo en el piso que se llena) y con poca vida se van atrás de sus compañeros. Los rápidos, si su embestida no te toca, a veces **giran y embisten de nuevo**.
- **IA de los enemigos:** son rápidos y atacan seguido (más todavía en cada era). Los que pegan de cerca te rodean desde distintos ángulos y se tiran hacia vos al pegar; los tiradores te siguen con la mira, se mueven de costado mientras recargan y en eras avanzadas tiran ráfagas; todos pueden esquivar tus disparos de un salto, y con poca vida se enfurecen (más rápidos y agresivos). Hay 13 enemigos + 3 por era + 1 cada 3 salas, en 2 a 4 oleadas (la primera más grande); la siguiente entra cuando quedan 3, así que no te dejan respirar.
- **Si quedás trabado** adentro de algo que no podés pisar (se derritió el hielo debajo, cambiaste en el agua a uno que no nada), salís nadando solo hasta lo más cercano. A los enemigos les pasa lo mismo.
- **Tipos de enemigo según su rol:**
  - **Pegadores** (tanques y atacantes): van directo hacia vos.
  - **Tiradores** (estrategas): disparan de lejos y se esconden para recargar.
  - **Rápidos** (velocistas): te rodean y embisten en línea recta.

### Estilo, rachas y nota de la sala

- **Estilo** (arriba a la derecha, a la izquierda del minimapa; de D a S): sale de cinco cosas:
  - **Ritmo:** cada cuánto le pegás a un enemigo. Golpes seguidos (menos de 0,7 s entre uno y otro) rinden todo; si pasan 3 s, casi nada.
  - **Movimiento:** moverte mientras peleás suma de a poco; quedarte quieto lo baja rápido.
  - **Combos:** terminar el combo de 3 golpes.
  - **Relevos:** cambiar de pokemon peleando y pegar con el que entra (ese golpe además pega x1,4).
  - **Sinergias:** usar las asistencias (F / G) de tus compañeros.
  Matar da poco. Baja si te pegan, si te quedás sin hacer nada o si repetís siempre el mismo ataque. **Cuando no quedan enemigos deja de sumar.** Cada rango pega más: C +5%, B +10%, A +17%, S +25%.
- **Racha:** bajas seguidas en menos de 3 s dan monedas extra.
- **Nota de la sala** (S, A, B, C, D) al limpiarla, sobre 100: ritmo (25), movimiento (20), combos (20), relevos (15) y sinergias (20). Se ven los puntos de cada parte. S y A dan monedas, experiencia y a veces un objeto.

### Caminos, tesoros y premios por explorar

- **La llave de la sala:** al limpiar una sala aparece una llave que vuela sola hacia vos y abre las puertas. Si tocás una puerta cerrada, te dice por qué no se abre.
- **Minimapa** (en la esquina de arriba a la derecha; con jefe, debajo de su barra): el mapa del Mystery Dungeon, con el piso en azul, los bordes de las paredes en blanco, vos (titilando), los enemigos en rojo, el jefe en violeta, los que quieren ser tus amigos en amarillo, los objetos en celeste, la llave y las puertas (cruces rojas mientras están cerradas, escaleras cuando se abren). No aparece en la tienda, el tesoro ni el hall.
- **Puertas del tesoro (TESORO llave):** cuando una sala tiene 2 o más salidas, a veces una lleva a una **sala del tesoro**. Hace falta una **Llave del Tesoro** (salen al romper cosas o con buena nota; ya no se venden en la tienda). Adentro hay 3 premios y te llevás uno: **Caramelos Raros** (x2) o una **mejora para todo el equipo** para siempre: Proteína (+8% daño), Hierro (−8% daño recibido), Carburante (+6% velocidad), Calcio (−8% recargas), Zinc (energía y parry), Más PS (cura a todos y revive).
- **Salas de desafío (★):** 50% más enemigos; la nota da el doble y más chance de objeto.
- **Romper cosas** a veces suelta una Baya Oran (cura 15% al agarrarla), una llave o un caramelo.
- **Caramelo Raro:** sube un nivel; se usa desde la ficha del pokemon.

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
| Romper objetos | 1 + (nivel de la sala ÷ 6) |
| Comprar en la tienda | el precio ÷ 6 |

- Los pokemon de la **banca ganan 3/4** de la experiencia.
- **Ajuste elástico:** si vas por encima del nivel de los enemigos comunes de la sala ganás menos experiencia, y si vas por debajo, más (cada 2,5 niveles de diferencia se duplica o se divide por 2, entre x0,1 y x2,5). Así tendés a ir **2 niveles arriba** de los comunes: el semijefe queda parejo con vos y el Regi de cada era un poco arriba. Sirve también para que la banca no quede atrás.
- `XP_MULT` es 0,2 (con 0,4 terminabas la Era Glacial 11 niveles arriba de los enemigos). Todo se ajusta arriba de todo en `combate.py`.
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
1. Peleando no se interrumpe nada: el que puede evolucionar muestra **EVO** en el HUD (junto a tu nombre o en su panel de la banca).
2. Cuando no hay peligro (sala limpia) aparece abajo un aviso con los dos retratos: **mantené C** (abajo en la cruz del control) y evoluciona ahí mismo, con destello, sin menús. Si no querés, ignoralo y seguí.
3. También podés hacerlo cuando quieras desde el menú de equipo (TAB): entrá a su ficha y elegí **Evolucionar**.

La evolución conserva el nivel, los IV, los EV y las MT enseñadas.

**Tipos de requisito:**
- **Nivel:** llegar a ese nivel.
- **Piedra u objeto:** tenerlo en la mochila. Riolu los vende en la tienda (2 por tienda; el Cristal Paradoja no), y el Regi lo suelta si alguien de tu equipo lo necesita.
- **Cordón Unión:** reemplaza a las evoluciones por intercambio de los juegos.
- **Amistad:** sube con cada sala que completás: +2 para el que pelea y +1 para los de la banca. Pichu y Riolu necesitan 20.
- **Saber una MT:** Piloswine evoluciona en Mamoswine sabiendo **Poder Pasado**.

**Piedras y objetos nuevos:** Piedra Fuego, Agua, Hoja, Hielo, Solar, Lunar, Día y Noche, Armadura Auspiciosa y Maldita (Charcadet), Mineral Negro (Scyther → Kleavor) y el **Cristal Paradoja**.
- **Eevee:** Piedra Agua → Vaporeon, Trueno → Jolteon, Fuego → Flareon, Solar → Espeon, Lunar → Umbreon, Hoja → Leafeon, Hielo → Glaceon, y con amistad → Sylveon.
- **Formas regionales:** el Growlithe de Hisui evoluciona con Piedra Fuego; Diglett de Alola (26), Grimer de Alola (38), Ponyta de Galar (40) y Zorua de Hisui (30) evolucionan en su misma forma.
- **Nincada** evoluciona en Ninjask a nivel 20 y, si hay lugar en el equipo o la reserva, aparece también **Shedinja**.
- **Formas paradoja:** el viaje en el tiempo las trae. Con un Cristal Paradoja (no se vende: lo suelta el Regi), Donphan se vuelve **Colmilargo**, Salamence **Bramaluna**, Tyranitar **Ferropúas** y Amoonguss **Furioseta**.

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
- Si tu equipo está lleno (3), el nuevo va a la **reserva** (hasta 3; si está llena, elegís a quién dejar ir). Los cambios entre el equipo y la reserva **solo se hacen en la tienda** (Chikorita rosa la cuida), así no se puede ir cambiando cuando uno quiere.
- Si te vas de la sala sin hablarle, se va.

**Cuándo es más probable:**
- Con pokemon comunes, porque depende del ratio de captura de la especie.
- Si sos de más nivel que él.
- Según su **naturaleza** (ver abajo).
- Si le **bailaste** cuando tenía poca vida.
- Con el **Lazo Amistad** de la tienda, que duplica la chance.

Los jefes nunca se unen.

**Uno por sala y una de espera:** cuando alguien quiere unirse, en el resto de esa sala ya no se ofrece nadie más, y la **sala siguiente es de espera** (nadie se ofrece). **Excepción:** a los que les bailaste les queda una chance (la mitad de lo normal) de querer unirse igual, así que bailando podés amigar a más de uno.

**Mínimo de amigos:** desde la **segunda sala de la Era Glacial** el primero que derrotás quiere unirse seguro (si esa sala es una tienda o un tesoro, pasa a la siguiente de pelea); los demás de esa sala, no. En cada era hay **al menos 2** ofertas: la primera antes de la sala 11 y la segunda antes de la 23. Además, cada sala de combate que completás sin que nadie quiera unirse suma +2,5% de chance para la siguiente (se reinicia cuando alguien quiere).

### Naturalezas

Cada pokemon (enemigos, tu inicial y los que se unen) nace con una de las **25 naturalezas** de los juegos, al azar. Sube un 10% un stat y baja un 10% otro (las 5 neutras no cambian nada), y además dice **qué tan fácil se amiga**. En la ficha, el stat que sube se ve en verde y el que baja en rojo.

| Se amiga | Naturalezas |
|---|---|
| muy fácil (x1,5 a x1,8) | Afable, Amable, Dócil, Alegre, Plácida |
| fácil (x1,1 a x1,4) | Ingenua, Mansa, Serena, Floja, Activa, Modesta |
| normal | Fuerte, Osada, Rara, Alocada, Pícara, Seria |
| cuesta (x0,5 a x0,8) | Huraña, Grosera, Agitada, Tímida, Miedosa, Firme, Audaz, Cauta |

Las de los enemigos también cambian un poco su daño (si le suben o le bajan el ataque).

### Baile

Con **V** (R3 en el control) tu pokemon baila un momento. Gasta 30 de energía y tiene 6 s de espera. Afecta a los que estén cerca:
- **Con poca vida** (menos del 40%): **se encariñan**. Asienten y les aparece un corazoncito arriba de la cabeza. Cada baile suma +70% de chance de que quieran unirse cuando los derrotes (hasta 3 bailes).
- **Con vida:** el 55% de las veces **se confunden** por 4,5 s. Les salen estrellitas, tropiezan, caminan sin rumbo, no te atacan y le pegan a sus compañeros si chocan con ellos.

Los jefes y los Regis chiquitos no se dejan. En la tienda y en el hall no se baila.

Todo el que se une queda como **amigo para siempre**, aunque después pierdas ese viaje: lo vas a encontrar en el hall.

---

## Hall

Es a donde volvés cuando cae todo tu equipo (como la casa de Hades). Una pantalla sin enemigos:
- **Tus amigos pasean** por el hall. Acercate y apretá **E** para hablarles: ahí elegís quién viene al próximo viaje (hasta 3). Si tu equipo está lleno, lo cambiás por alguien que no esté peleando.
- **Celebi** está al lado del portal: te cuenta cuántos viajes hiciste, cuántas eras derrotaste y cuántos amigos tenés.
- **El portal** (puerta del norte, *VIAJE TEMPORAL*) arranca otro viaje desde la Era Glacial.
- **Cada viaje empieza de cero:** todos vuelven a su primera forma (un Swampert vuelve a ser Mudkip) y al nivel 5, sin monedas ni objetos. Lo que conservan son sus IV, su amistad y su sinergia. La charla muestra su mejor viaje (hasta qué forma y nivel llegó).

**Dónde queda** (Ajustes > Hall):
- **Automático:** el claro del bosque donde aparece Celebi, con las ruinas del templo, hasta que derrotes una era. Después, el lugar atemporal.
- **Atemporal:** una isla flotando en el flujo del tiempo, con el piso de la última era que derrotaste.
- **Celebi:** siempre el claro del bosque.

**Animaciones:** tus amigos caminan y al quedarse quietos se sientan, se acuestan, miran para arriba o duermen. Asienten cuando les hablás y saltan de alegría cuando los llevás al viaje. Al caer el equipo, el último se desmaya antes de que se oscurezca la pantalla.

---

## Tutorial, boss rush y otros modos

**Tutorial** (menú principal, o al empezar una partida nueva): la **isla de práctica de Celebi**. Te presta a Riolu y vas paso por paso, sin apuro y sin poder perder: moverte, correr, esquivar, el combo, disparar, los especiales, el **parry** (contra un Mankey que pega despacito), los **relevos** (se suma Torchic), las asistencias, **bailar y hacer un amigo** (un Machop cansado), romper cosas, una **sala de verdad en chiquito** (dos enemigos, la nota, la llave y la puerta), **comprar** en la tienda y los lazos de equipo. Abajo a la izquierda Celebi dice qué hay que hacer y cuánto llevás. **F9** saltea un paso. Los textos están en `modos.py` (`TUTORIAL`).

**Boss rush** (menú principal): elegís **3 pokemon cualesquiera** (no los jefes, ni Celebi, ni Missingno) y peleás contra **los 12 jefes seguidos**: el semijefe y el Regi de cada era, Regigigas y Arceus (y lo que venga después). Entre era y era hay una tienda; arrancás con 150 monedas y los jefes dan las suyas.
- Tu equipo **sube solo** al nivel de cada jefe (1 menos que el semijefe, 3 menos que el Regi) y entre jefe y jefe recupera la **mitad de la vida** (los caídos se levantan).
- Se puede jugar en **Normal** o en **Fácil**. Al terminar (o al caer) te dice cuántos jefes y en cuánto tiempo.

**Boss rush con tu partida:** en el refugio de Celebi, en la **estatua del salón de los modos**. Van los amigos que tengas en el equipo. No se pierde nada: tu equipo, tus monedas y tu mochila quedan guardados aparte y vuelven al terminar, con un premio para el próximo viaje (40 monedas por jefe y 400 más si lo completás).

**Modo fácil:** se prende y se apaga en la misma estatua (queda guardado en la partida). Recibís 40% menos de daño, las salas curan 25% en vez de 12%, y los enemigos avisan más, atacan menos seguido, de a dos como mucho y sin maniobras. Vale para los viajes y para el boss rush.

**Sala de los titanes** (desde la estatua o la puerta del salón): los jefes que ya derrotaste te esperan cada uno en su pedestal; los que no, son una sombra. Hablales con E: cuentan algo y te ofrecen la **revancha** (una pelea contra ese jefe solo, con tu equipo subido a su nivel).

**Minijuegos** (la cancha del refugio; tu equipo entra prestado, con la vida llena, y dan monedas para el próximo viaje):
- **Contrarreloj:** 90 segundos; cuenta cuántos derrotás (reaparecen enseguida).
- **Supervivencia:** sin curas, y cada 20 segundos se suma un enemigo más. Cuenta cuánto aguantás.
- **Lluvia de monedas:** 45 segundos juntando monedas mientras los tiradores te apuntan.

**Amigos del refugio:** cada uno habla distinto según su especie, su tipo, su naturaleza y cuánto te quiere. Si le preguntás **¿Necesitás algo?** te pide un **favor** para el próximo viaje (uno a la vez); si lo cumplís con él en el equipo, sube su amistad.

**Misiones del tablón:** ahora son 16 (parrys, bailes, amigos nuevos, romper cosas, compras, tesoros, desafíos, arreglar una era, terminar un boss rush, ganar revanchas, jugar minijuegos...). Casi todas se pueden volver a tomar después de cumplirlas.

### Lazos de equipo

Además de la sinergia que da cada uno desde la banca, **el equipo entero** gana algo si sus pokemon se complementan. Cuentan todos los que están en pie (también el que pelea) y se ven en el menú de equipo, arriba a la derecha. La lista completa está en *Glosario > Lazos de equipo*: de cada lazo dice **quiénes** lo forman, **por qué** van juntos y **qué da**. Además, la pestaña *Habilidad* de la ficha de cada pokemon dice qué lazos puede formar y con quién. Los datos están en `mecanicas.py` (`RESONANCIA` y `LAZOS`).
- **Resonancia de tipo:** dos pokemon que comparten un tipo dan +5% de lo que ese tipo hace mejor (fuego, lucha, dragón y siniestro: daño; agua, tierra, roca y acero: defensa; eléctrico, volador y bicho: velocidad; hielo, veneno, psíquico y fantasma: recargas; planta, hada y normal: energía). Los tres del mismo tipo: +9%.
- **Lazos por su historia** (unos 25): Compañeros de Hoenn (Mudkip y Torchic), Familia Eevee, Rivales de dojo (Mankey y Machop), Maestro y aprendiz (Lucario con los que pelean con los puños), Fósiles revividos, Cazadora de cuervos (Tinkaton y Corviknight), Tragamisil cargado (Cramorant y Arrokuda), Espada y escudo (Gardevoir y Gallade), Trío elemental (fuego, agua y planta), Paradojas...
- Lo que suman los lazos a una misma cosa tiene un tope de 18%.

### Más movimiento en pantalla

Contador de **golpes seguidos** debajo del minimapa (se corta si pasás 1,6 s sin pegar o si te pegan), los enemigos que caen dejan su **silueta en blanco** un instante, los que embisten o esquivan dejan **estela**, y con menos del 25% de vida los bordes de la pantalla **laten en rojo**. La llegada de Celebi en la partida nueva también es otra: entra dormido por el túnel en espiral dejando brillitos, y cuando te descubre te da una vuelta alrededor.

---

## Pokemon nuevos y lo que los hace únicos

Se sumaron **más de 60 líneas evolutivas** (datos de la PokeAPI y sprites de SpriteCollab):

| Tipo | Líneas |
|---|---|
| Normal | Lillipup, Zigzagoon, Eevee (y sus 8 evoluciones), Whismur, Wooloo |
| Fuego | Charcadet (Armarouge / Ceruledge), Litten, Growlithe de Hisui |
| Planta | Shroomish, Snivy, Fomantis, Chikorita (Bayleef y Meganium), Sprigatito, Foongus (+ Furioseta) |
| Hielo | Swinub |
| Veneno | Zubat, Grimer de Alola, Croagunk, Skrelp |
| Tierra | Sandile, Diglett de Alola, Phanpy (+ Colmilargo) |
| Volador | Noibat, Cramorant, Arrokuda |
| Psíquico | Ponyta de Galar, Espurr, Ralts (Gardevoir / Gallade), Elgyem |
| Bicho | Wimpod, Scyther (Scizor / Kleavor), Nincada, Joltik, Sewaddle |
| Roca | Rockruff, Anorith, Tyrunt, Larvitar (+ Ferropúas) |
| Fantasma | Shuppet, Litwick, Phantump, Greavard |
| Dragón | Axew, Bagon (+ Bramaluna), Dreepy, Druddigon |
| Siniestro | Zorua y Zorua de Hisui, Pawniard, Impidimp |
| Acero | Mawile, Honedge, Klink, Aron |
| Hada | Cleffa, Tinkatink, Flabébé |

**Los que todavía no tienen sprites propios:** solo **Amoonguss y Furioseta**. SpriteCollab (de donde salen todos los sprites) todavía no tiene sus animaciones, solo el retrato; mientras tanto usan las de Foongus (más grande, y Furioseta oscurecido). El día que aparezcan, `python herramientas.py descargar` las baja y el juego usa las suyas solo. Missingno no está en SpriteCollab. A unos 170 pokemon les falta la animación de desmayarse (*Faint*): SpriteCollab no la tiene y el juego usa la de recibir un golpe.

**Formas origen y Arceus Beta:** también están los sprites de **Dialga, Palkia y Giratina en su forma origen** (`dialga_origen`, `palkia_origen`, `giratina_origen`, cargados como jefes con sus stats de la PokeAPI; son los subjefes de la fase 2 de Arceus Beta, ver más abajo) y los de **Arceus Beta**.

**Dónde aparecen:** cada era suma los suyos (los de hielo y frío en la Glacial, fósiles y bestias en la de Piedra, los de acero en la de los Metales, dragones, hadas y fantasmas en la Edad Media, ciudad y tecnología en la Moderna, y las formas paradoja y las evoluciones finales en El Origen).

**Mecánicas únicas** (`mecanicas.py`): cada línea tiene una **pasiva** o un **especial propio en R**, sacado de lo que dice su Pokédex. Se ven en su ficha, en la Pokédex y en *Glosario > Pokemon únicos*. Algunas:

| Línea | Mecánica |
|---|---|
| Chikorita | **Rastro de pasto:** deja pasto por donde camina; parado en su pasto se cura |
| Sprigatito | **Bomba floral (R):** flores que explotan al segundo (1, 2 o 3 según la evolución) |
| Foongus | **Humo tóxico (R):** nube de esporas que envenena y frena |
| Zubat | **Supersónico (R):** chillido en cono que aturde y confunde |
| Diglett de Alola | **Bajo tierra (R):** 3 s intocable, pasa por debajo de agua, hielo y lava y sale golpeando |
| Noibat | **Predicción (R, 40 s):** 5 s esquivando solo; si algo viene muy rápido el tiempo se frena. **Oído fino:** flechas hacia los enemigos de fuera de la pantalla |
| Elgyem | **Control mental (R, 25 s):** el enemigo más cercano pelea de tu lado |
| Joltik | **Cobardía:** con poca vida cambia solo al siguiente pokemon |
| Zorua | **Ilusión (R, 20 s):** toma la forma de un enemigo, no lo atacan hasta que pega y ese golpe hace el doble |
| Mawile | **Mandíbula trasera:** el golpe muerde adelante y atrás, a veces paraliza y arrastra |
| Honedge | **Tajo teledirigido (R):** la embestida persigue al enemigo (Aegislash cambia entre espada y escudo) |
| Eevee y evoluciones | Adaptable, Absorbe Agua, Pelaje de agujas, Absorbe Fuego, Premonición, Sudor venenoso, Fotosíntesis, Cuerpo helado, Cintas calmantes |

**Balance:** las pasivas son chicas y siempre están; lo fuerte va en especiales con mucha espera. Las de contacto (Piel tosca, Púas de hierro, Sudor venenoso...) castigan al que te pega cuerpo a cuerpo.

**Como enemigos:** Diglett de Alola te entierra (mirá el círculo), Mawile te paraliza y arrastra, Zubat te aturde con su chillido (anillo amarillo), Foongus suelta esporas, Zorua aparece disfrazado de otro, Elgyem te controla la mente (caminás al revés) y Joltik escapa con poca vida.

**MT nuevas:** Poder Pasado, Danza Aleteo, Fuerza Lunar y Vozarrón, y los básicos nuevos (Tijera X, Zumbido, Pin Misil, Carantoña, Beso Drenaje, Brillo Mágico, Fuerza Lunar, Vozarrón, Filo Amargo) también se venden como MT de combate.

---

## Estados y curaciones

**Estados del jugador** (iconos arriba de la cabeza): algunos golpes enemigos te los dejan según su tipo (veneno envenena 12%, fuego quema 10%, eléctrico paraliza 10%, psíquico y fantasma confunden), y algunos pokemon tienen los suyos.
- **Envenenado:** pierde vida de a poco (nunca te deja en 0). **Quemado:** pierde vida y pega 20% menos. **Paralizado:** más lento y a veces no le sale el especial.
- **Dormido:** no se mueve ni ataca hasta que le pegan. **Confundido:** camina al revés. **Aturdido:** un instante sin poder hacer nada.
- Cada pokemon tiene los suyos: si cambiás, el que entra no los trae. Los de veneno y acero no se envenenan, los de fuego no se queman y los eléctricos no se paralizan.

**Curaciones** (Chikorita rosa vende 5 al azar en cada tienda): van al **cinturón**, el cuarto de círculo marrón de abajo a la derecha, que tiene **5 lugares** numerados del 1 al 5. Con el cinturón lleno no se puede comprar otra.
- Con **Z** se usa la del **lugar 1** en el que pelea; las de atrás avanzan un lugar. Si esa no le sirve ahora (vida llena, no tiene ese estado, un Revivir en alguien que está en pie), no se gasta y te avisa.
- En la **mochila** (arriba de todo) se pueden **usar** en quien quieras (también en la banca o la reserva), **subir**, **bajar** o **tirar**.
- Las partidas de antes: las curaciones que tenías pasan al cinturón en orden; las que no entran se venden solas y te devuelven lo que costaron.
- La Poción Máxima de Celebi también va al cinturón (si hay lugar).

| Grupo | Objetos |
|---|---|
| Bayas | Zumo de Baya (20 PS), Baya Aranja (10), Baya Zidra (30); Zreza (parálisis), Atania (sueño), Meloc (veneno), Safre (quemadura), Perasi (congelamiento), Caquic (confusión), Ziuela (todos) |
| Amargos (baratos, bajan un poco la amistad) | Polvo Curación (todos los estados), Polvo Energía (50), Raíz Energía (200), Hierba Revivir (revive con la mitad) |
| Líquidos | Agua Fresca (50), Refresco (60), Limonada (80), Leche Mu-mu (100) |
| Remedios | Remedio (60), Superremedio (100), Hiperremedio (150) |
| Pociones | Poción (20), Superpoción (50), Hiperpoción (200), **Poción Máxima** (toda la vida; no se vende: Celebi te da una al empezar cada viaje y en cada era nueva, y solo se lleva una) |
| Comidas | Galleta Lava, Porcehelado, Crepe Luminalia, Bizcocho Jubileo (todos los estados) |
| Revivir | Revivir (mitad de la vida), Máximo Revivir (toda) |

Al romper cosas a veces sale una Baya Aranja, una Ziuela o un Zumo de Baya.

---

## Eras y salas

La partida sigue la historia de la humanidad:
- **5 eras de 30 salas** cada una.
- Al final, **El Origen**, con 3 salas fijas: tienda, Regigigas y Arceus.
- En cada era, el **semijefe** está en la sala 15 y el **Regi** en la sala 30.
- **Portal de Celebi:** cuando cae el Regi, Celebi aparece al lado de la puerta y la vuelve un portal del tiempo (no hace falta la llave). Hablale con E para cruzar ya, o juntá las monedas y cruzá cuando quieras: el túnel del tiempo te lleva a la era siguiente.
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

**Fases 2 y 3:** al terminar la fase 1 la pantalla se pone blanca y **el piso se vuelve un triángulo** (la imagen `assets/interfaz/arena_arceus_beta.png`), con Arceus Beta arriba de la punta.

**La última piedad:** apenas aparece el triángulo, Arceus Beta se queda quieto (no recibe daño) y te deja **elegir contra quién pelear**. Quedás parado en el anillo gris del medio y tenés **7 segundos** para pararte arriba de un círculo (medio segundo arriba para que cuente): **rojo → Giratina Origen**, **azul → Dialga Origen**, **violeta → Palkia Origen**. Si no elegís, Arceus elige por vos. El subjefe se pelea en una **arena de 10×8 casillas** (un poco más grande que el círculo de la fase 1) con piso de **World Abyss** rodeada de vacío; tiene el 55% de la vida de Arceus Beta. Al ganarle te da monedas y experiencia, volvés al triángulo y **Arceus Beta sigue con sus tablas**. Cada subjefe tiene una mecánica en su sala y arranca siempre con su movimiento de efecto; el número entre paréntesis es la espera antes de repetirlo.

| Subjefe | Mecánica de la sala | Movimientos |
|---|---|---|
| **Giratina Origen** | **El mundo al revés:** cada tanto la sala se tiñe de rojo oscuro (titila antes de avisar) y por 5 s **los controles se invierten**. | **Golpe Umbrío** (5 s): se vuelve una sombra (`assets/interfaz/sombra_giratina.png`) que persigue tu última posición 3 s y sale de golpe donde termina · **Bola Sombra** (4 s): carga 3 s quieto, sin daño de contacto, y tira 3 bolas grandes y lentas · **Garra Dragón** (3 s): 3 embestidas cortas con zarpazo; la última es más grande y te empuja más lejos · **Cometa Draco** (6 s): 10 meteoritos en lugares al azar y Giratina queda quieto 3 s · **Esfera Aural** (4 s): esfera naranja que te sigue 7 s y rompe el piso por donde pasa durante 3 s · **Cara Susto** (7 s, el primero): grito en onda que cubre toda la arena y te deja lento 3 s (se esquiva con el esquive) |
| **Dialga Origen** | **El reloj:** en el medio de la arena hay un reloj; cada vuelta completa (12 s) Dialga **rebobina** y volvés a donde estabas 3 s antes. Los últimos 3 s se marca en el piso a dónde volverías. | **Distorsión** (5 s): carga 2 s con el piso azul salvo 3 zonas seguras; la onda te lastima y te congela 1 s en lo azul, y solo te congela 0,5 s en las zonas seguras · **Pulso Dragón** (4 s): 3 ondas con un hueco que cambia de lado (zigzag) · **Cola Férrea** (3 s, si estás cerca): coletazo en semicírculo detrás de él; si te pega recibís +15% de daño unos segundos · **Foco Resplandor** (5 s): 3 bolas de luz al azar; explotan en un área chica que lastima y otra 3 veces más grande que deja la pantalla blanca 0,5 s · **Joya de Luz** (5 s): 7 rocas que rebotan 6 s dejando hilos de luz (poco daño, pero muchos); se rompen pegándoles y a los 7 s se van · **Eco Metálico** (7 s, el primero): 3 arcos que rebotan hasta 10 s hasta tocarte; no lastiman, te bajan la defensa |
| **Palkia Origen** | **Los bordes conectados:** si empujás contra un borde de la arena aparecés del otro lado; tus ataques a distancia también cruzan. | **Corte Vacío** (6 s): 2 cortes que pasan por el medio (en + o en x) y abren vacío partiendo la arena en 4 durante 5 s · **Vasto Impacto** (4 s): salta, su sombra te sigue y cae haciendo un pliegue que te tira hacia el centro y después te empuja lejos · **Torbellino** (5 s): 3 remolinos que se mueven 3 s; si te agarran quedás girando (**E** para escapar) y te lastiman cada 0,5 s · **Hidrobomba** (7 s): chorro que va girando hacia tu última posición 5 s; si te pega te empuja hasta la pared · **Trueno** (3 s): 4 rayos rápidos que rebotan de pared en pared 2 s · **Gravedad** (7 s, el primero): 6 s sin correr ni esquivar, más lento, piso violeta; los ataques de Palkia también van más lentos |

Los efectos que tenés encima se ven abajo en el medio de la pantalla. Los números están en `SUBJEFE`, `ELECCION`, `GIRATINA`, `DIALGA` y `PALKIA` en `combate.py`.

**Piso de la arena (World Abyss):** el terreno `abismo` usa la hoja *Dungeons - World Abyss B16F - B30F* del Explorers of Time/Darkness (https://www.spriters-resource.com/ds_dsi/pokemonmysterydungeonexplorersoftimedarkness/asset/86145/). Spriters Resource no deja bajarla automático: bajala a mano, ponela en `assets/hojas/time_darkness/` con el nombre de siempre (`DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Time _ Darkness - Dungeons - World Abyss B16F - B30F.png`) y corré `python herramientas.py tiles`. Hasta entonces la arena se dibuja violeta oscuro.

Al vencer a Arceus Beta el piso y las paredes vuelven y se puede salir. Los sprites están en `assets/sprites/pokemones/sprite_arceus_beta` (la forma Beta de SpriteCollab, `0493/0019`). Los números de cada movimiento están en `MOVS_BETA` en `combate.py` y los de las tablas en `BETA` y `TABLAS_BETA`.

**Arena de El Origen:** la sala de Regigigas y la de Arceus es **redonda y más grande** (23 × 23 casillas en vez de 21 × 15).

**Premios:**
- **Monedas:** 120 el semijefe, 250 el Regi.
- **Una MT** que alguien de tu equipo pueda aprender.
- **El Regi**, además, suelta el objeto de evolución que necesite alguien de tu equipo.

**Otras monedas:** cada enemigo suelta 4 + número de era, y completar una sala da 10 + 3 × era.

---

## Tienda

El local cambia de nombre según la era: **Puesto de trueque** (Glacial), **Mercado de trueque** (Piedra), **Bazar** (Metales), **Mercado** (Edad Media), **Almacén** (Moderna) y **Bazar del tiempo** (El Origen). Es una sala más grande que la pantalla (la cámara la recorre) y está **partida en 3** por dos paredes: arriba, de izquierda a derecha, tres mostradores **del color del pokemon que los atiende**, con **5 objetos al azar** cada uno. Acercate a un objeto del mostrador y apretá E para comprarlo (el que tenés más cerca se marca y muestra su nombre; abajo a la izquierda dice qué hace).

| Mostrador | Atiende | Vende |
|---|---|---|
| Izquierda (rosa) | **Chikorita rosa** | 5 curaciones (vida o estados). Van al [cinturón](#estados-y-curaciones). En la punta de su mostrador (**♥ Curar**) cura al que pelea (30 $ + 15 por era) o cura y revive a todo el equipo (70 $ + 30 por era). También cuida la reserva |
| Medio (azul) | **Riolu** | 3 que potencian (Ataque X, Defensa X, Velocidad X, Especial X, Directo o los de tipo) y 2 de evolución (piedras, Cordón Unión, armaduras, Mineral Negro, Garra Afilada). Si alguien de tu equipo necesita uno, casi siempre está. El Cristal Paradoja no se vende |
| Derecha (verde con la raya roja) | **Kecleon** | 5 MT. Si hay alguna que tu equipo puede aprender, al menos una de esas |

Ya no se venden Repelentes, Lazo Amistad, la Llave del Tesoro, el Caramelo Raro, el Amuleto Moneda ni los equipables que no son de tipo (Éter, Cinta Fuerte, Garra Rápida, Polvo Veloz, Chaleco Asalto, Cinta Focus, Pluma Ágil). Las llaves y los caramelos siguen saliendo al romper cosas y en las salas del tesoro.

**Objetos equipables y de equipo:** los que dicen *(lo lleva un pokemon)* van a la mochila y se equipan desde la ficha: **cada pokemon lleva hasta 2** y solo cuentan mientras ese pokemon pelea. Los que dicen *(todo el equipo)* valen para todos.

| Tipo de objeto | Ejemplos | Para quién |
|---|---|---|
| Por 3 salas (Riolu) | Ataque X (+25% daño), Defensa X (−20% daño recibido), Velocidad X, Especial X (recargas más rápidas), Directo (20% de críticos x1,8) | todo el equipo |
| De tipo (Riolu) | +20% de daño a los ataques de ese tipo (ver cada tipo) | un pokemon |
| Evolución (Riolu) | Piedras, Garra Afilada, Cordón Unión, Armadura Auspiciosa y Maldita, Mineral Negro | el que evoluciona |
| MT (Kecleon) | enseñan un movimiento en una casilla. Se gastan al usarlas | un pokemon |
| Curaciones (Chikorita rosa) | bayas, pociones, remedios, polvos, comidas y revivir | el que elijas (van al cinturón) |

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

## Gráficos e interfaz

Toda la interfaz usa piezas de **Pokémon Blanco/Negro** (y la letra de HeartGold/SoulSilver, que es la misma de BW):

- **Logo y títulos:** POKE con la letra de los nombres de mazmorra de Explorers of Sky (amarilla con borde azul) y MANIC con las **letras Unown** de la hoja de HGSS. Los títulos de los menús y los carteles grandes usan esa misma letra del PMD.
- **Sección Ataques** (menú principal y pausa): todos los ataques del juego por categoría (básicos, especiales, asistencias, MT de combate y MT especiales), con qué hacen en palabras, sus números y quiénes los usan.
- **Bordes de agua, hielo y pasto alto:** cada parche del PMD trae pegado alrededor el piso de *su* mazmorra, que no es el de la sala (por eso el agua tenía un borde de otro color). Ahora ese piso ajeno se saca (se ve el piso de verdad hasta la orilla) y la orilla del agua se pinta con el tono del piso de la sala, un poco más oscuro. Se hace solo al cargar cada tileset (`mundo.py`: `_calar` y `_con_orilla`), así que vale para todas las eras y para los tiles que agregues.
- **Cosas con sprites del PMD:** cajas, vasijas (barriles, ánforas, cestos), fardos de heno, troncos y el puesto del mercado salen del mapa *Sky Peak 8th Station* del Explorers of Sky (`python herramientas.py props`). En el mapa las vasijas vienen de a dos, una tapando a la otra: se arma una sola entera con la mitad que se ve bien, espejada.
- **Fuego en el piso:** ya no es un cuadrado naranja. El piso de la era queda chamuscado (una mancha oscura sin bordes rectos) y arriba arden tres llamas de la fogata de ese mismo mapa (`assets/efectos/llama.png`), cada una a su ritmo, con un resplandor que late.
- **Casas del refugio:** todavía se dibujan en el código. Las del PMD son las hojas **Huts** del Red Rescue Team (Pikachu Hut, Mudkip Hut, Torchic Hut... están con su link en `assets/hojas/faltan.txt`); Spriters Resource no deja bajarlas automático. Bajalas a `assets/hojas/red_rescue/Huts`, corré `python herramientas.py props` y el barrio las usa solas.
- **Terrenos con tiles del PMD:** además de piso, paredes y agua, ahora hay tilesets de vacío (el abismo de Chasm Cave), ceniza, roca volcánica, charcos y el techo de la torre de Regidrago; la lava, el aceite, la arena movediza y las corrientes son el agua animada del PMD con otros colores. El fuego y el agua electrificada usan las llamas y chispas del PMD, las cascadas el agua de la era cayendo con la salpicadura del PMD, y la alfombra de la tienda es la del Secret Bazaar.
- **Efectos:** estelas al esquivar, embestir y arrancar a correr; silueta blanca en el enemigo golpeado; pausa de impacto en remates, parrys y bajas; la cámara acompaña el golpe; nube de humo de Poké Transfer al morir.

- **Letra:** la de los juegos de DS, recortada letra por letra de `assets/DS _ DSi - Pokemon HeartGold _ SoulSilver - Miscellaneous - Fonts.png` (`sistema.tipografia`). Tiene tildes, ñ, ¿ ¡ y el símbolo de Pokédólar (₽, que reemplaza al `$`). Se agranda en pixeles enteros (x1, x2, x3) para que no se vea borrosa, y tiene una versión con borde para leer sobre el piso.
- **HUD del combate** (como la batalla de BW): tu pokemon con la barra de HP del jugador (con la placa oscura, la etiqueta HP y el ícono Lv) y las barras de experiencia y energía; la raya blanca de la energía marca cuánto gasta un esquive. El daño reciente queda en blanco en la barra y se vacía de a poco, y la placa tiembla al recibir un golpe. La banca va en los **paneles en flecha** del menú de equipo (verde: asistencia lista; rojo: debilitado). Abajo a la derecha, un **cuarto de círculo marrón medio transparente** (como la tela de un mostrador, con flecos y costura) es el **cinturón**: 5 círculos negros con las curaciones y su número (el orden en que se usan con Z; el 1 tiene el borde dorado). **Alrededor** van los 6 ataques, **E, Q, Shift, R** (tus movimientos) y **F, G** (las asistencias de la banca), en los **botones octogonales de la pantalla táctil** (con la textura de puntitos y el borde del color del tipo) y con el nombre debajo; la espera se cierra como un abanico. Arriba a la derecha va el **minimapa** en la esquina y el **estilo** a su izquierda. Los jefes usan la barra del rival.
- **En la pelea:** números de daño que saltan (amarillos si es súper eficaz, grises si resiste, naranjas en contraataques, rojos los que recibís), íconos de estado de BW arriba de los enemigos (BRN, PAR, FRZ), destello de pantalla en el parry, el esquive perfecto y el remate, y aviso amarillo con "!" en el momento del parry.
- **Carteles:** el nombre de la sala y los jefes entran barriendo en una franja inclinada con rayas de color (rojas en los jefes); los avisos chicos caen desde arriba con una raya de color.
- **Menús:** el logo (POKE + MANIC en letras Unown) cae al abrir el título; los botones son los paneles en flecha de BW y entran escalonados desde la izquierda (el elegido se corre y titila). El fondo de grilla de BW se mueve en diagonal con la **Pokéball de la pantalla táctil** girando. La pausa entra con una franja inclinada y la Pokéball grande girando detrás.

Las piezas recortadas están en `assets/interfaz/hud` (las arma `python herramientas.py hud` desde las hojas de `assets/hojas/blanco_negro`). Si falta alguna, el juego dibuja una forma básica.

---

## Herramientas

Programas aparte para preparar el juego. No se usan mientras jugás.

```
python herramientas.py props               cajas, vasijas, heno y troncos del PMD (mapa Sky Peak 8th Station) y las casas del refugio (hojas Huts del Red Rescue Team, si las bajaste)
python herramientas.py descargar           baja sprites y retratos del PMD (SpriteCollab) a assets/sprites/pokemones
python herramientas.py datos               agrega a datos_pokeapi.json los pokemon que faltan (stats, movimientos, evoluciones). Si pokeapi.co no responde
                                           usa el espejo de GitHub (PokeAPI/api-data). Con 'datos todo' los vuelve a pedir todos
python herramientas.py minimapa            recorta las piezas del minimapa (Map Sprites del Explorers of Time/Darkness)
python herramientas.py recortar hoja.png   recorta sprites de una hoja y los guarda en assets/mundo
python herramientas.py viaje               recorta el túnel del viaje temporal (Explorers of Sky > Time Travel) para la partida nueva
python herramientas.py hud                 recorta las barras de HP, íconos de estado, la Pokéball y los paneles en flecha de BW a assets/interfaz/hud
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
