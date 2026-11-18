# Cómo está hecho Pokemanic

Esta es la explicación del código, para vos. No la lee el juego. La primera parte cuenta cómo está armado todo y qué pasa cuando jugás.
La segunda parte es el índice de cada archivo con **todas** sus funciones y qué hace cada una, en el orden en que aparecen en el código.
Ese índice sale del código mismo (los docstrings), así que si cambiás algo podés regenerarlo y queda al día.

---

## 1. Qué es cada archivo

| Archivo | Para qué está | Lo que tiene adentro |
|---|---|---|
| `main.py` | El juego en sí | La ventana, el título, el menú, la pokédex y **la partida** (`jugar`), todo adentro de `main()` |
| `sistema.py` | Lo básico | Ajustes (`config.json`), partidas guardadas, la letra de DS, la ventana, teclado y control, las animaciones de los sprites del PMD y el sonido |
| `datos.py` | Los datos del juego | Pokémon, movimientos, tabla de tipos, roles, MT, la tienda, las eras, terrenos, objetos y el plan de salas. No dibuja nada |
| `modos.py` | Textos y números de los modos | Tutorial, boss rush, titanes, minijuegos, charlas, misiones, los caminos entre salas y las escenas (poses de los jefes, frases de Celebi) |
| `mundo.py` | La sala | `generacion` (arma las salas), `entorno` (terrenos que reaccionan, objetos, clima, dibujo de la sala) y `efectos` (partículas y transiciones) |
| `combate.py` | Cómo pelean | `progreso` (niveles, experiencia, evoluciones) e `ia` (cómo piensan los enemigos y los jefes legendarios) |
| `mecanicas.py` | Lo único de cada línea evolutiva | Una pasiva o un especial propio para cada familia (Pikachu rueda, Squirtle se mete en el caparazón...) |
| `subjefes.py` | Los subjefes de las salas 10 y 20 | Cramorant, Mamoswine, Tyrantrum... cada uno con su arena, su mecánica y sus ataques |
| `interfaz.py` | Lo que se ve fuera de la sala | Menús, botones de BW, diálogos, la rueda de curaciones, el logo y las escenas del borde del cosmos |
| `herramientas.py` | Programas aparte | Bajan y recortan los assets (sprites, hojas, efectos, clima, chozas, logo...). No se usan mientras jugás |
| `descargar_assets.py`, `visor_mundo.py` | Atajos | Llaman a `herramientas.py descargar` y `herramientas.py visor` |
| `datos_pokeapi.json` | Datos de la PokeAPI | Stats, tipos, movimientos y evoluciones de cada especie (lo arma `herramientas.py datos`) |

`config.json` (tus ajustes) y `partidas/` (las partidas guardadas) se crean solos al jugar y no se suben a git.

---

## 2. Cómo está organizado el código

**Módulos armados por funciones.** Casi todos los archivos tienen funciones `armar_algo()` que definen adentro sus funciones y al final
devuelven `SimpleNamespace(**locals())`. Por eso desde afuera se usan como `entorno.crear(...)`, `menus.boton(...)`, `ia.actualizar(...)`.
Lo que empieza con `_` es interno de ese módulo.

**`main.py` es una sola función grande.** `main()` arma la ventana y la configuración y adentro define todo lo demás. La partida es
`jugar(...)`, que también está adentro y se divide en grupos `armar_reglas`, `armar_equipo`, `armar_ataques`, `armar_salas`, `armar_dibujo`...
Cada grupo devuelve sus funciones y se desarman en variables. Así todas comparten el mismo estado sin variables globales. El encabezado de
`main.py` tiene la lista de grupos y qué hace cada uno.

**El estado son diccionarios.** No hay clases (salvo `AnimadorPokemon` y las letras). Los diccionarios que vas a ver todo el tiempo:

| Nombre | Qué es |
|---|---|
| `config` | Tus ajustes (volumen, resolución, controles, trucos del menú secreto). Se guarda en `config.json` |
| `perfil` | Lo que queda entre viajes: tu nombre y género, tus amigos, cuántas eras derrotaste, los titanes, las misiones |
| `viaje` | Dónde estás: en el refugio o de viaje, en qué zona del refugio, si es boss rush o tutorial |
| `rec` | El recorrido: el plan de salas de cada era (`plan`), en qué era y sala estás y el `historial` de salas por las que pasaste |
| `registro` | Una sala del historial: tipo, variante, semilla, puertas y a dónde llevan, si la completaste y por dónde saliste |
| `j` | El jugador: el equipo, el pokémon que pelea, vida, energía, estilo, buffs, combos, frenesí, inventario |
| `nivel` | La sala en juego: el entorno, los enemigos, el jefe, las balas, las monedas, los carteles, la llave, las escenas |
| `ent` | El entorno de la sala (en `mundo.py`): la matriz de terrenos, los objetos, el fuego, el clima, los lagos |
| `mundo` | Lo que comparten todos: `mundo['nivel']`, `mundo['jugador']`, `mundo['ent']` y `mundo['ef']` (las partículas) |

**El tiempo.** Todo lo que pasa en una partida se mide con `tiempo()` (milisegundos), que no corre cuando pausás o abrís un menú. Los menús
se abren con `pausado(menú, ...)`, que descuenta ese rato.

**Las coordenadas.** La sala se mide en píxeles del mundo; cada casilla mide `sala['tam']` (80 px). La cámara (`camara(j)`) dice qué parte se ve.
La pantalla lógica es siempre de 1000x600 y `sistema.pantalla` la agranda a la ventana.

**Las imágenes.** Todo sale de hojas del PMD y de Blanco/Negro que están en `assets/`. `herramientas.py` las recorta una vez y las guarda
listas para usar (por ejemplo `assets/efectos/estrella.png`). Si falta algo, el juego dibuja una forma simple para no romperse.

---

## 3. Qué pasa cuando jugás

1. **Arranque** (`main()`): carga `config.json`, los controles y el sonido, abre la ventana y pasa por la intro del cielo y el título con el logo.
2. **Menú principal** (`menu_principal`): Jugar, Tutorial, Boss rush, Modo prueba, Pokédex, Ataques, Ajustes, Glosario y Salir.
3. **Partida nueva**: `menus.viaje_temporal` es la escena del borde del cosmos. Primero negro y un brillo lejano, después la apertura y el
   cosmos, Celebi, la charla, tu nombre, tu género y tu forma (la sombra del pokémon). Devuelve nombre, género e inicial.
4. **`jugar(...)`**: arma el jugador (`crear_jugador`) y el recorrido (`mundos.nuevo_recorrido`), y corre el loop de salas:
   - **Crear la sala** (`crear_nivel`): según el plan, una sala de combate, una tienda, un tesoro, un subjefe, un jefe, un Regi o un camino.
     Ahí se generan la sala (`generacion.generar_*`), el entorno (`entorno.crear`) y los enemigos o el jefe. Si es la primera sala de una era,
     arranca la escena de llegada; si hay jefe, su entrada.
   - **Cada cuadro** (60 por segundo): primero los eventos del teclado y del control (`controles.eventos` → acciones como `basico1`, `curar` o
     `mapa`). Después `actualizar_nivel`, que mueve todo: escenas, jugador, entorno, enemigos, jefe, balas, monedas, la llave y las puertas.
     Al final `dibujar_objetos`, que dibuja la sala, los pokémon, los efectos, el clima y el HUD.
   - **Puertas**: al limpiar la sala aparece la llave y se abren. Al cruzar una, a veces hay un **camino tranquilo** antes (`hay_pasillo`).
     Después se avanza en el plan (`mundos.avanzar`) y se arma la sala siguiente.
   - **Fin de era**: cae el Regi, Celebi te lleva de la mano al portal (`empezar_rescate`), cruzás el cosmos (`menus.cruzar_portal`) y llegás
     a la era siguiente.
   - **Si cae todo tu equipo**: Celebi te lleva al **refugio** (`volver_al_hall`). El próximo viaje empieza de cero, pero tus amigos y lo que
     ganaste en el perfil quedan.
5. **Guardado**: `guardar_partida` guarda en `partidas/partida_<n>.json` cada vez que cambiás de sala.

---

## 4. Los sistemas, uno por uno

**Combate** (`armar_ataques`, `armar_estilo`):
- `usar_basico` / `golpe_combo`: el combo de 3 golpes. El tercero es el remate y **remata** a los enemigos con poca vida (`rematar`).
- `supercombo` / `nivel_super`: el **combo de combos**. Cada remate que conecta sube un nivel (x2... x5), con más daño y menos espera, y un
  especial justo después es un **enlace**.
- `eco_de_baja`: la **cadena de bajas**. El golpe que derrota a un enemigo rebota al más cercano (hasta 3 veces).
- `recibir_ataque`: todo daño a un enemigo pasa por acá (tipos, críticos, números que saltan, estados, empujones, robo de vida, doble golpe).
- `dañar_jugador`: todo daño que recibís pasa por acá (esquive, defensas, frenesí de los tanques).
- `abrir_parry` / `intentar_parry` / `esquivar`: parry y esquive.
- `baja`: rachas y **frenesí**. Con 3 bajas seguidas entrás en frenesí y te sumás la habilidad de tu rol o tipo (`habilidad_de`): cámara lenta,
  doble golpe, más vida, parry automático o robo de vida.
- `curarse_rapido` + `menus.rueda_curacion`: tocar Z usa la primera curación; mantener Z abre la rueda.

**Enemigos y jefes** (`armar_enemigos`, `combate.ia`, `subjefes.py`): `crear_enemigo` y `crear_jefe` arman cada uno. La IA está en
`ia.actualizar` (comunes) e `ia.actualizar_jefe` (legendarios con su guion de ataques). Los subjefes usan `subjefes.actualizar`.

**Escenas** (`armar_salas` y `armar_dibujo`): `nivel['cine']` dice qué escena está pasando; mientras hay una, no se dibuja el HUD
(`nivel['cinematica']`) y a veces no te podés mover (`nivel['bloqueo']`).
- `empezar_llegada_era`: el portal se abre, salen Celebi y tu pokémon, y Celebi se va por otro portal en el cielo.
- `preparar_intro_jefe`: el jefe espera sentado, dormido o de espaldas (`modos.POSE_JEFE`), se da vuelta de a poco y ruge.
- `empezar_rescate`: Celebi te agarra de la mano y te lleva al portal (`modos.RESCATE` cambia la frase y el camino en cada era).
- `actualizar_cine` mueve la escena cada cuadro y `dibujar_cine` la dibuja.

**Mapas** (`armar_dibujo`): `dibujar_minimapa` es el de arriba a la derecha y `mapa_completo` el de la tecla M. Este último muestra
`mapa_era` en un viaje (las salas del historial puestas una al lado de la otra según la puerta por la que saliste) y `mapa_refugio` en el refugio.

**El refugio** (`armar_hall`): `crear_hall` arma cada zona (plaza, barrio, salón, minijuegos, galería...). Ahí están `hablar_hall`, los amigos que
pasean (`residente`, `actualizar_residentes`), las misiones, los titanes y el portal. Los caminos entre salas también viven acá
(`hay_pasillo`, `poblar_pasillo`, `hablar_pasillo`). En el refugio no se rompe nada (`ent['intocable']`).

**El mundo** (`mundo.py`):
- `generacion.generar_sala` arma una sala de combate capa por capa (silueta, especiales, paredes, manchas de terreno, máquinas, objetos)
  y se queda con la mejor de varias candidatas que pasan `_validar` (que se pueda llegar a todas las puertas).
- `generar_pasillo` usa la forma `camino`.
- `entorno.reaccionar` hace que los ataques cambien el terreno: el fuego quema el pasto, el hielo congela el agua y el fuego derrite el
  hielo con `derretir` (lago si era agua, charco si era piso).
- `entorno.dibujar` dibuja la sala y `dibujar_clima` el clima.

**Interfaz** (`interfaz.py`): `boton`, `panel_flecha` y `boton_tactil` son las piezas de BW con las que se arma todo. `dibujar_logo` dibuja el
logo, y `viaje_temporal` y `cruzar_portal` son las escenas del cosmos.

---

## 5. Cómo agregar cosas

- **Un pokémon jugable**: que esté en `datos_pokeapi.json` (`python herramientas.py datos`) con sus sprites (`python herramientas.py descargar`),
  y en `datos.py` darle rol (`ROL_POKEMON`) y marcarlo jugable. Su mecánica va en `mecanicas.py` (`LINEAS` y `MECANICAS`).
- **Un movimiento**: en los datos de movimientos de `datos.py` (forma `cuerpo`, `proyectil`, `area`, `embestida`, `buff` o `curar`).
- **Una era**: un diccionario más en `mundos.ERAS` (variantes de sala, enemigos, jefe, Regi, clima, tienda) y sus tiles en `assets/mundo/<era>`.
- **Un objeto de la tienda**: en `tienda.ITEMS` de `datos.py`, con su ícono en `assets/interfaz/objetos`.
- **Textos de modos, charlas y escenas**: en `modos.py`; no hace falta tocar el código.
- **Un truco del menú secreto**: en `TRUCOS` de `interfaz.py`; después leelo con `trucos.get('clave')` en `main.py`.

---

## 6. Cómo probar

- **Jugando**: `python main.py`. En el juego, F1 abre el menú debug de pokémon y F2 salta a cualquier sala. En el modo prueba, F3 elige
  modo, era y sala, F4 saca las recargas y F5 da vida infinita. El código Konami (en Ajustes o en la pausa) abre el menú secreto.
- **Salas sin jugar**: `python herramientas.py visor` (ventana para mirar salas generadas), `salas` y `plan`.
- **El ejecutable**: `crear_exe.bat` arma `dist/Pokemanic/Pokemanic.exe` (ver README).

---

## 7. Índice de cada archivo, función por función

Cada función con su línea y qué hace. Las que están adentro de otras van con sangría.

### `main.py` (6553 líneas)

> main.py - El juego en si: la ventana, los menus y la partida. Todo vive adentro de main(), en funciones armadas por grupos
> (armar_*) que comparten la ventana, la configuracion y el estado de la partida.
>
> main()
>     armar_ayudas_menu / armar_menu_debug / armar_pantallas / armar_pokedex     retratos, debug (F1), titulo, menu, pausa, pokedex
>     jugar(...)                      una partida: arma el jugador y el recorrido y corre el loop de salas (al final del archivo)
>         armar_reglas                daño por tipo, objetos que se llevan, a quien le pegan los ataques
>         armar_equipo                crear miembros, cambiar de pokemon, buffs y velocidad
>         armar_movimiento            mover al jugador, la camara y hacia donde apunta
>         armar_estilo                estilo (D a S), rachas, frenesi, contador de golpes y nota de la sala
>         armar_ataques               combo, combo de combos, cadena de bajas, parry, esquive, especiales, daño recibido y estados
>         armar_enemigos              enemigos, sus balas, jefes e invocaciones
>         armar_salas                 crear cada sala, escenas (llegada a la era, jefes, Celebi al portal), cada cuadro de la sala,
>                                     puertas, tienda, monedas y curaciones (rueda incluida)
>         armar_mecanicas             el puente con mecanicas.py (lo unico de cada linea evolutiva)
>         armar_hall                  el refugio de Celebi, los caminos entre salas, amigos, misiones y el portal
>         armar_dibujo                todo lo que se ve: la sala, el HUD, el minimapa, el mapa grande (M) y las escenas
>         armar_extras                evoluciones, menu de equipo (TAB) y trucos
>         armar_modos                 tutorial, boss rush, titanes y minijuegos
>         armar_guardado              guardar y cargar la partida
>
> Estado (todo diccionarios): config (config.json), viaje (refugio o viaje, zona, modo), perfil (lo que queda entre viajes:
> nombre, amigos, eras, titanes), rec (el recorrido: plan de salas e historial), j (el jugador), nivel (la sala en juego) y
> mundo ('ent' entorno, 'ef' efectos, 'nivel', 'jugador'). tiempo() es el reloj de la partida (no corre en las pausas).

- `main()` (l. 58): Arranca pygame y la ventana, y maneja el ciclo intro -> titulo -> menu principal -> partida.
  - `armar_ayudas_menu()` (l. 73): Ayudas de los menus: retratos de las caras, volumen y la caja de confirmar.
    - `retrato_menu(nombre, lado)` (l. 75): Retrato del pokemon al tamaño pedido (guardado para no escalarlo de nuevo). None si no tiene.
    - `aplicar_volumen()` (l. 83): Pone el volumen de la musica segun los ajustes.
    - `confirmar(mensaje)` (l. 87): Caja de 'si / no' sobre la pantalla actual. True si se confirmo (ENTER / Y).
  - `armar_menu_debug()` (l. 117): Menu debug (F1): armar el equipo con cualquier pokemon y elegir en que espacio va.
    - `elegir_espacio(nombre, equipo, activo)` (l. 119): Menu debug: en que espacio del equipo (1, 2 o 3) va el pokemon elegido. Devuelve el indice, None o 'salir'.
    - `generacion_de(nombre)` (l. 158): Generacion del pokemon segun su numero de la pokedex (las formas regionales cuentan con el de la especie).
    - `hijos_de(nombre)` (l. 164): A quienes evoluciona (aunque todavia no tengan sprites): PokeAPI, Eevee, formas regionales y paradojas.
    - `ordenar_debug(nombres)` (l. 173): Lista del menu F1 agrupada: por tipo (el principal de la primera forma de la linea, en el orden de la tabla de tipos),
      - `raiz(n)` (l. 180): La primera forma de una línea evolutiva (para ordenar la lista del menú debug).
      - `linea(r)` (l. 185): Una especie y todas sus evoluciones en orden (para la lista del menú debug).
    - `debug_menu(equipo, activo, titulo_menu, sin_espacio)` (l. 203): Menu debug (F1): grilla con todos los pokemon jugables (con el Konami tambien los jefes), ordenados por tipo,
    - `asignar_equipo(lista, nombre, espacio)` (l. 291): Pone el pokemon en ese espacio del equipo del menu (si ya estaba en otro, los intercambia).
  - `armar_pantallas()` (l. 304): Pantalla de titulo, menu principal y menu de pausa.
    - `pantalla_titulo()` (l. 306): Pantalla de titulo sobre la isla: cualquier tecla sigue al menu, ESC pregunta si salir.
    - `menu_principal(equipo)` (l. 344): Menu principal: jugar, pokedex, ajustes, glosario y salir. Devuelve la opcion elegida.
    - `menu_pausa(fondo, retirarse)` (l. 387): Menu de pausa sobre la partida congelada ('fondo'). Devuelve 'seguir', 'menu', 'refugio' (retirarse del viaje) o 'cerrar'.
  - `armar_pokedex()` (l. 445): La pokedex y la ficha de cada pokemon.
    - `descripcion_movimiento(datos_mov)` (l. 447): Texto corto de un movimiento para la ficha (el mismo que usan la tienda y el menu de equipo).
    - `descripcion_asistencia(a)` (l. 451): Texto de lo que hace una asistencia (lo que el pokemon de la banca hace con F / G).
    - `mios()` (l. 462): Pokemon que tenes: los que fueron tus amigos o estuvieron en tu equipo en cualquiera de las partidas guardadas,
    - `gris(nombre, lado)` (l. 481): El retrato en gris (los que todavia no tenes, en la vista 'todos').
    - `construir_pestañas(nombre, ancho, fuente_txt)` (l. 493): Lo que va en cada pestaña de la ficha, ya cortado al ancho: ('t', titulo), ('p', parrafo), ('e', espacio),
      - `titulo(p, t)` (l. 498): Agrega un título a una pestaña de la ficha.
      - `texto(p, t)` (l. 499): Agrega un párrafo (cortado en renglones) a una pestaña de la ficha.
      - `vacio(p)` (l. 501): Agrega un renglón vacío a una pestaña de la ficha.
    - **Info**
    - **Combate**
    - **Movimientos**
    - `suave(k)` (l. 553): 0 -> 1 que frena al final (para las animaciones de la interfaz).
    - `ver_ficha(entradas, indice, tengo)` (l. 557): Ficha de un pokemon: a la izquierda su sprite animado sobre un pedestal de su tipo y sus stats, a la derecha
      - `cargar(i, direccion)` (l. 568): Carga el pokemon i de la lista en la ficha: su animador y las animaciones que se pueden mostrar.
      - `otra_animacion()` (l. 579): Pasa a la siguiente animación del pokemon en la ficha.
      - `ir_pestaña(k)` (l. 582): Cambia de pestaña en la ficha (y se acuerda para qué lado se desliza).
      - **Tarjeta de la izquierda**
      - **Pestañas**
    - `pokedex()` (l. 715): Lista de la pokedex: buscador (escribis y filtra), filtro por tipos, ver todos (marcando los tuyos) o solo los tuyos.
      - `entradas()` (l. 730): La lista de la pokédex con el buscador y los filtros de tipo aplicados.
      - `filtro_cambiado()` (l. 741): Al cambiar el filtro de la pokédex: vuelve arriba de la lista.
      - **Buscador, vista y tipos**
      - **Tarjetas**
  - `jugar(nombres, config, ranura, cargada, perfil, prueba, en_refugio, modo)` (l. 862): Una partida entera: arma el equipo, recorre las salas una por una y devuelve como termino ('menu' o 'salir') junto con el pokemon activo.
    - `tiempo()` (l. 879): Milisegundos de partida sin contar las pausas (todo el combate mide con este reloj).
    - `es_facil()` (l. 881): Si esta puesto el modo facil: el del boss rush que estas jugando o el de tu partida.
    - `hora()` (l. 888): La hora del juego en minutos del dia (se guarda en el perfil; arranca a las 8).
    - `avanzar_reloj()` (l. 892): Cada cuadro: la hora avanza con el tiempo jugado (un minuto por segundo); al pasar la medianoche cuenta un dia mas.
    - `pausado(f, *args, **kwargs)` (l. 901): Llama a un menu sin que el tiempo de la partida avance mientras esta abierto (los enfriamientos no corren).
    - `habilidad_de(j)` (l. 1009): La habilidad de frenesi del pokemon que pelea (aunque no este en frenesi).
    - `habilidad_frenesi(j)` (l. 1013): La habilidad activa ahora (None si no esta en frenesi).
    - `armar_reglas()` (l. 1060): Reglas generales del combate: choques, tipos, modificadores y a quien se le puede pegar.
      - `mover(rect, dx, dy, piedras)` (l. 1062): Mueve un rect por x y despues por y, sin meterse en ninguno de los rects de 'piedras'.
      - `tipo_combate(datos)` (l. 1069): Tipo principal de un pokemon (el primero de su lista).
      - `daño_con_tipo(daño, ataque_tipo, defensa_tipo)` (l. 1074): Daño final segun la tabla de tipos y el clima de la sala (minimo 1 si el ataque pegaba algo).
      - `mod(j, clave)` (l. 1081): Multiplicador del entorno (terreno, maquinas, clima), lo de equipo comprado en la tienda y los objetos que lleva el que pelea.
      - `llevados(j)` (l. 1085): Objetos equipados del pokemon que esta peleando (hasta 2).
      - `objetivos_de(nivel, con_objetos)` (l. 1089): A quien le pueden pegar los ataques: enemigos, jefe y objetos rompibles.
    - `armar_equipo()` (l. 1101): El equipo del jugador: miembros, cambio de pokemon, sinergias, debug y velocidad.
      - `crear_miembro(nombre, nivel)` (l. 1103): Pokemon del equipo: nivel, xp, IV/EV y movimientos (progreso.py) mas su vida y su asistencia.
      - `juego_de(m)` (l. 1112): Datos de combate de la especie con las MT enseñadas puestas en sus casillas (E, Q, Shift, R).
      - `nombre_mov(nombre)` (l. 1123): Nombre para mostrar de un movimiento o una MT.
      - `datos_mov(nombre)` (l. 1128): Datos de un movimiento: de la MT si es una, si no de la lista de movimientos.
      - `reiniciar_asistencia(m)` (l. 1132): Al entrar a una sala la asistencia arranca con un 30% de su espera ya cargada.
      - `actualizar_sinergia(j)` (l. 1136): Suma las pasivas de los pokemon vivos de la banca (cada rol da algo: daño, defensa, velocidad o recargas).
      - `aplicar_pokemon(j, nombre, vida, centro)` (l. 1152): Pone en el jugador los datos del pokemon activo: tamaño, vida, velocidad, multiplicadores y su animador.
      - `crear_jugador(nombres, centro, modo)` (l. 1167): Arrancas solo con tu inicial; el resto del equipo se suma por amistad.
      - `guardar_activo(j)` (l. 1179): Guarda la vida del pokemon activo en su lugar del equipo (antes de cambiarlo o de salir de la sala).
      - `cambiar_slot(j, indice, forzar)` (l. 1183): Cambia al pokemon del espacio 'indice' (no si esta debilitado, atacando, congelado o en la espera de 2,5 s).
      - `equipar_debug(j, nombre, espacio)` (l. 1205): Menu debug: pone un pokemon en un espacio del equipo de la partida (o lo intercambia si ya estaba).
      - `reiniciar_jugador(j, centro)` (l. 1229): Al entrar a una sala: te pone en la entrada. La vida sigue como estaba (sin curas, como en Hades).
      - `mult_buff(j, clave)` (l. 1242): Multiplicador de un buff activo (danza espada, agilidad...) o 1 si no hay o ya se vencio.
      - `velocidad_actual(j)` (l. 1247): Velocidad del jugador con todo encima: buffs, sinergia, correr, terreno, tienda y nivel.
    - `armar_movimiento()` (l. 1263): Mover al jugador, la camara y hacia donde apunta.
      - `mover_jugador(j, piedras)` (l. 1265): Mueve al jugador segun las teclas o la palanca: correr gasta energia, el hielo resbala y las cintas empujan.
      - `camara(j)` (l. 1300): Esquina de arriba a la izquierda de lo que se ve: centrada en el jugador sin salirse de la sala.
      - `apuntar(j)` (l. 1305): Hacia donde mira y apunta el jugador: mouse, palanca derecha o la ultima direccion caminada (segun el modo).
      - `asistido(j, aim, alcance, grados)` (l. 1338): Apuntado asistido (teclas o control sin la palanca derecha): el enemigo mas cercano dentro de un cono adelante, o None.
      - `punto_apuntado(j, alcance)` (l. 1351): Punto del mapa donde apunta el jugador, como mucho a 'alcance' pixeles (asistencias de area).
      - `direccion_de(v)` (l. 1369): Una de las 8 direcciones ('norte', 'sureste'...) para un vector.
    - `armar_estilo()` (l. 1379): Medidor de estilo (D a S) y nota de la sala. Sube con el ritmo de tus golpes (variados), moviendote, con combos completos,
      - `estilo_nuevo()` (l. 1383): El estado del medidor de estilo al empezar.
      - `stats_nuevas(enemigos)` (l. 1387): Lo que se va midiendo en una sala para la nota.
      - `hay_peligro(nivel)` (l. 1393): Si quedan enemigos vivos (o por aparecer) en la sala.
      - `rango_de(puntos)` (l. 1400): La letra de estilo (D a S) que corresponde a esos puntos.
      - `sumar_estilo(j, puntos, nivel)` (l. 1403): Suma (o resta) puntos de estilo. Si sube de rango, la letra salta. Sin enemigos vivos no suma (solo baja).
      - `contar(nivel, clave, cuanto)` (l. 1414): Suma a lo que se mide para la nota (combos, relevos, sinergias...), solo mientras hay enemigos.
      - `registrar_accion(j, clase)` (l. 1418): Cada vez que usas un ataque: si es el mismo que el anterior, cuenta como repetido (rinde menos estilo).
      - `estilo_por_golpe(j, nivel)` (l. 1424): Un golpe que conecta: mas puntos cuanto mas seguido le venis pegando (ritmo) y cuanto mas variado.
      - `mult_estilo(j)` (l. 1446): Multiplicador de daño del rango actual (D x1 ... S x1.25).
      - `baja(j, nivel)` (l. 1450): Un enemigo menos: un poco de estilo y racha (bajas seguidas en pocos segundos dan monedas extra).
      - `golpe_recibido(j, nivel)` (l. 1473): Te pegaron: baja el estilo y se corta la racha.
      - `enfriar_estilo(j, nivel)` (l. 1480): Cada cuadro: moverte con enemigos vivos suma un poquito (y cuenta para la nota); el estilo se va solo,
      - `nota_sala(nivel, j)` (l. 1495): Nota de la sala al limpiarla (S, A, B, C o D): ritmo, movimiento, combos, relevos y sinergias. Devuelve (letra, detalle).
        - `entre(valor, cero, lleno)` (l. 1498): Qué tan lleno está un valor entre un mínimo y un máximo (0 a 1), para la nota de la sala.
    - `armar_ataques()` (l. 1522): Ataques del jugador (basicos, especiales, asistencias, embestidas) y el daño que recibe.
      - `preparar(j, datos)` (l. 1524): Copia del movimiento con el daño final: rol, buffs, sinergia, tienda, critico y el stat (Ataque o At. Esp.).
      - `enfriamiento_de(j, datos)` (l. 1541): Espera (ms) antes de poder repetir el ataque, con rol, sinergia, buffs y terreno.
      - `iniciar_ataque(j, forma, enfriamiento, movimiento, tipo)` (l. 1550): Pone la animacion del ataque (por su nombre, tipo y forma: puño -> Punch, electrico -> Shock, proyectil -> Shoot),
      - `golpear(j, datos, objetivos, efectos, arco, alcance_extra)` (l. 1560): Golpe cuerpo a cuerpo: le pega a todo lo que esta adelante (en un arco de 'arco' grados a cada lado, o en el rectangulo
      - `lanzar(j, datos, proyectiles)` (l. 1594): Dispara uno o varios proyectiles (en abanico) hacia donde apunta el jugador.
      - `area_efecto(j, datos, objetivos, efectos, centro)` (l. 1609): Golpe en circulo alrededor del jugador (o en 'centro'): pega a todos adentro y hace reaccionar el terreno.
      - `iniciar_embestida(j, datos)` (l. 1621): Empieza una embestida: el jugador sale disparado hacia donde apunta.
      - `actualizar_embestida(j, objetivos, piedras)` (l. 1631): Un paso de la embestida: avanza, le pega una vez a cada uno que toca y frena contra las paredes.
      - `descongelar(j, tipo)` (l. 1654): Congelado solo se puede usar un movimiento de fuego o de lucha, y te descongela (si no, hay que esperar).
      - `ocupado(j)` (l. 1662): Si el jugador no puede atacar ahora: embistiendo, esquivando o nadando a la orilla.
      - `apuntar_al_cercano(j, objetivos, alcance)` (l. 1666): Iman del golpe: si hay un enemigo cerca y casi adelante, el golpe se acomoda hacia el.
      - `premiar(j, energia, recarga, cura)` (l. 1679): Premio por pelear bien (golpes que conectan, parry, esquive perfecto): energia, menos espera en los especiales y algo de vida.
      - `abrir_parry(j, nivel)` (l. 1686): Apretar el golpe abre la ventana de parry (si no la gastaste recien). Los que estan por pegarte ahora mismo quedan bloqueados.
      - `usar_basico(j, indice, nivel, apretado)` (l. 1697): Ataque basico: 0 = cuerpo a cuerpo (combo de 3 golpes, abre el parry), 1 = a distancia.
      - `golpe_combo(j, datos, nivel, movimiento)` (l. 1726): Un golpe del combo: 1 y 2 rapidos, el 3 es un remate que barre, empuja lejos e interrumpe a los enemigos comunes.
      - `esquivar(j, nivel)` (l. 1769): Esquive: salto corto hacia donde caminas (si estas quieto, para atras) con invulnerabilidad. Gasta energia.
      - `actualizar_esquive(j, piedras)` (l. 1791): Un paso del esquive: avanza rapido y frena contra las paredes.
      - `esquive_perfecto(j)` (l. 1805): Te iban a pegar mientras esquivabas: premio (una vez por esquive).
      - `intentar_parry(j, e, nivel)` (l. 1818): Si el jugador esta en su ventana de parry y el enemigo esta cerca, bloquea su ataque
      - `parry_exitoso(j, nivel, donde)` (l. 1837): Lo que pasa con cualquier parry (golpe o bala): destello, premio y la ventana queda libre para el proximo.
      - `usar_especial(j, indice, nivel)` (l. 1851): Especial 1 o 2 (Shift / R): proyectil, golpe, area, embestida, buff o cura, segun el movimiento.
        - `soltar()` (l. 1869): El especial sale, despues de la carga.
      - `usar_asistencia(j, k, nivel)` (l. 1891): Asistencia de un pokemon de la banca (F / G): impacto, escudo, furia, carrera, cura, desvanecer o masivo.
      - `actualizar_jugador(j)` (l. 1926): Animacion del jugador: termina el ataque en curso o camina / queda quieto al ritmo de su velocidad.
      - `dañar_jugador(j, daño, tipo, evitable, atacante)` (l. 1940): Le saca vida al jugador: tipos, buffs, sinergia, tienda y defensa (nada si esta el truco de vida infinita).
    - **Estados del jugador (cada pokemon tiene los suyos): los ponen los golpes de algunos tipos y algunas mecanicas**
      - `golpe_al_jugador(j, d, t, atacante)` (l. 1974): Un enemigo te pega (cuerpo a cuerpo si se sabe quien): daño, la mordida de Mawile y a veces un estado segun el tipo.
      - `tiene_estado(j, estado)` (l. 1994): Si el pokemon que pelea tiene ese estado ahora (veneno, quemadura...).
      - `poner_estado(j, estado, ms)` (l. 1997): Le pone un estado al pokemon que pelea (si su tipo no es inmune). Devuelve True si quedo.
      - `curar_estados(m, cuales)` (l. 2008): Le saca los estados a un pokemon (a todos, o solo los de 'cuales').
      - `estado_por_golpe(j, tipo)` (l. 2015): Un golpe enemigo que te dio: segun su tipo, a veces te deja un estado.
      - `actualizar_estados(j)` (l. 2020): Cada cuadro: el veneno y la quemadura sacan vida de a poco (sin dejarte en 0) y los estados vencidos se van.
      - `nivel_super(j)` (l. 2035): Nivel del combo de combos (0 si no hay o se vencio la ventana).
      - `supercombo(j, ahora, conecto)` (l. 2040): Un remate (o un enlace) que conecto sube el combo de combos y abre otra ventana para seguirlo. Devuelve el nivel.
      - `rematar(nivel, tocados, tipo)` (l. 2048): El remate termina a los enemigos comunes que quedaron con poca vida (y su baja rebota como cualquier otra).
      - `eco_de_baja(muerto, datos, daño)` (l. 2056): Cadena de bajas: el golpe que derrota a un enemigo rebota al mas cercano (no a los jefes). Si ese tambien cae, sigue
      - `recibir_ataque(obj, datos, direccion)` (l. 2073): Un enemigo, jefe u objeto recibe un ataque: daño por tipo, efecto de estado (quemar, paralizar...) y empujon.
    - `armar_enemigos()` (l. 2139): Enemigos, proyectiles y jefes.
      - `elegir_pokemon_enemigo(era)` (l. 2141): Pokemon al azar de los de la era (primero los que tienen sprites).
      - `pokemon_de_tipo(tipo, era)` (l. 2146): Pokemon (no jefes) que tienen ese tipo: primero los de la era, despues cualquiera.
      - `crear_enemigo(nivel, punto, cazando, nombre, nv, estilo)` (l. 2154): Enemigo de la era de la sala, mas fuerte cuanto mas avanzas (o el pokemon y nivel que se pidan).
      - `crear_mini_regi(nivel, nombre, punto, cazando)` (l. 2174): Regi chiquito de Regigigas: un enemigo comun un poco mas fuerte, mucho mas flojo que el Regi de verdad.
      - `crear_aparicion(nivel, a, j)` (l. 2183): La marca de aparicion se cumplio: sale el enemigo (comun, refuerzo de un Regi o Regi chiquito).
      - `invocaciones_jefe(nivel, j, jefe)` (l. 2191): Los Regis llaman refuerzos de su tipo al perder un cuarto de vida; Regigigas invoca Regis chiquitos cada tanto; Arceus avisa cada fase.
      - `torre_regidrago(nivel, j, jefe, ahora)` (l. 2221): Regidrago pide subir (te mordio) o bajar (se rompio la torre). Los que estaban en la sala esperan abajo.
      - `actualizar_animacion_enemigo(e)` (l. 2238): Animacion de un enemigo segun como se movio: suaviza la direccion para que no titile y camina al ritmo real.
      - `dibujar_enemigo(e, cx, cy)` (l. 2263): Dibuja un enemigo con un anillo del color de su tipo a los pies. False si no tiene sprite.
      - `actualizar_estado(e)` (l. 2284): Estados alterados: la quemadura saca vida cada 0,7 s; al vencerse el estado se borra.
      - `crear_proyectil(x, y, dx, dy, daño, jefe, tipo, vel, alcance, tam)` (l. 2293): Bala de un enemigo o jefe: posicion, direccion, daño, velocidad y alcance.
      - `actualizar_proyectil(proyectil, j, piedras, rebotados)` (l. 2298): Mueve una bala enemiga: se apaga al llegar a su alcance o chocar, y si toca al jugador le pega.
      - `actualizar_proyectil_pokemon(proyectil, objetivos, piedras)` (l. 2316): Mueve un proyectil del jugador: pega a lo que toca (los que atraviesan siguen) y se apaga al chocar.
      - `crear_jefe(nivel, nombre, vida, nv, tam, centro, tam_sprite)` (l. 2339): Jefe, Regi o Arceus: aparece arriba del centro de la arena (o donde se pida).
      - `crear_piedras_verdes(jefe)` (l. 2352): Piedras que lastiman si las pisas, alrededor del jefe (sin pisarse entre ellas ni salir de la sala).
      - `actualizar_jefe(jefe, j, proyectiles, verdes, contexto)` (l. 2363): Movimiento y ataques avisados en ia.py; aca el anillo de balas, las piedras verdes y el choque.
    - `armar_salas()` (l. 2387): Las salas: crearlas, carteles, monedas, experiencia, amigos, tienda y lo que pasa en cada frame.
      - `subjefe_rush(rec, era, sala)` (l. 2391): En el boss rush los subjefes de la era van seguidos: el primero y despues el segundo.
      - `previa_sala(era, i, tipo)` (l. 2397): Una sala de ejemplo de ese lugar del plan, dibujada entera (mapa y objetos) para el menu F2. Se arma una sola vez.
      - `miniatura(previa, ancho, alto)` (l. 2415): La sala achicada para que entre en (ancho, alto) sin deformarse.
      - `menu_niveles(rec)` (l. 2423): F2: elegir era (pestañas arriba) y sala (con una vista del mapa). La ultima carta salta a la era siguiente.
      - `cartel(nivel, texto, duracion, subtitulo, grande)` (l. 2526): Mensaje que se ve un rato y se va solo (no hay que cerrarlo).
      - `repartir(total, partes)` (l. 2533): Divide la cantidad de enemigos en oleadas (la primera un poco mas grande).
    - **Escenas: mientras duran no hay HUD (nivel['cinematica']) y en algunas no te podes mover (nivel['bloqueo'])**
      - `empezar_llegada_era(nivel)` (l. 2543): Primera sala de una era: se abre un portal en la puerta, salen tu pokemon y Celebi, se cierra, y Celebi sube, abre otro
      - `preparar_intro_jefe(nivel, titulo, sub)` (l. 2552): El jefe te espera sentado, dormido o de espaldas (modos.POSE_JEFE). Cuando entras (o te siente cerca) se da vuelta de a poco,
      - `empezar_rescate(nivel, j)` (l. 2564): Cayo el Regi: Celebi sale de un portal en la puerta, viene volando, te agarra de la mano y te lleva corriendo hasta el portal
      - `actualizar_cine(nivel, j, ahora)` (l. 2574): Un cuadro de la escena que este pasando. Devuelve True si la pelea tiene que esperar (enemigos y jefe quietos).
      - `camino_rescate(c, k, destino)` (l. 2636): Por donde te lleva Celebi hasta el portal (k de 0 a 1): una curva de costado y, en algunas eras, a los saltitos.
      - `crear_nivel(rec, destino, entrada, j, registro, llegada)` (l. 2644): Arma la sala actual del recorrido: mapa, entorno, puertas con su destino, enemigos y el cartel de entrada.
      - `crear_prueba(rec, j)` (l. 2774): Sala del modo prueba: una arena de la era sin puertas, con muñecos (no atacan, no se mueren y miden tu daño)
        - `libre_cerca(x, y)` (l. 2808): La casilla pisable mas cercana a (x, y), para que los muñecos no queden en el agua o en una pared.
        - `muñeco(x, y)` (l. 2816): Pone un muñeco de práctica (modo prueba) en un lugar libre.
        - `enemigo(estilo)` (l. 2825): Crea un enemigo del modo prueba con el estilo pedido.
      - `menu_prueba(fondo_juego, rec)` (l. 2844): F3 en el modo prueba: elegir modo, era y tipo de sala (con flechas o clic) y aplicar. Devuelve True si cambio algo, o 'salir'.
        - `valor(f)` (l. 2854): El texto de cada opción del menú del modo prueba.
        - `aplicar()` (l. 2859): Aplica lo elegido en el menú del modo prueba (modo, era y sala).
      - `suave_ui(k)` (l. 2898): Curva que frena al final (0 a 1), para que las cosas de la pantalla entren deslizándose.
      - `enemigos_de_era_lista(era)` (l. 2901): Los pokemon de la era que tienen sprites (o, si no hay, cualquiera jugable).
      - `actualizar_muñeco(nivel, e, ahora)` (l. 2904): Un muñeco: no se mueve ni ataca, vuelve a su lugar, anota el daño que recibe y se cura solo si lo dejas de pegar.
      - `impacto(nivel, x, y, radio, temblor)` (l. 2915): Golpe fuerte de un jefe contra el piso: polvo, piedritas y la pantalla tiembla un rato.
      - `empezar_llegada_beta(nivel, j, arceus)` (l. 2921): Arceus desaparece, pasas al medio de la arena y se preparan las Sentencias que van a caer alrededor (de afuera hacia adentro).
      - `actualizar_llegada_beta(nivel, j)` (l. 2937): Caen las Sentencias y vuelven vacio el piso y las paredes donde caen; al final todo es vacio menos tu circulo
      - `empezar_subjefe(nivel, j, beta, nombre)` (l. 2960): La ultima piedad de Arceus Beta: elegiste un circulo del triangulo. Arceus Beta espera afuera, se arma la arena de
      - `terminar_subjefe(nivel, j, sub, contexto)` (l. 2978): Le ganaste al subjefe: monedas y experiencia, vuelve el triangulo y Arceus Beta sigue la pelea.
      - `forzar_cambio(j)` (l. 2993): Llave Giro de Arceus Beta: te cambia al siguiente pokemon vivo (por la espera de cambio no podes volver por 2 s).
      - `quitar_objeto(j)` (l. 3001): Desarme de Arceus Beta: perdes un objeto al azar de la mochila. Devuelve su nombre (None si no tenias).
      - `usar_curacion(j, m, indice)` (l. 3011): Gasta la curacion de ese lugar del cinturon en el miembro m (el congelamiento solo lo tiene el que pelea).
      - `curarse_rapido(j, nivel, rueda)` (l. 3032): Tecla de curarse (Z): dos toques usan la curacion del lugar 1 del cinturon en el que pelea; con rueda=True (mantenerla) se
      - `dar_pocion_maxima(j, nivel)` (l. 3060): Celebi te da una Pocion Maxima si no tenes (solo se puede llevar una) y si hay lugar en el cinturon.
      - `soltar_objeto(nivel, x, y, clave)` (l. 3068): Deja un objeto en el piso (baya, llave, caramelo...): salta un poquito y se junta al pasar cerca.
      - `actualizar_recogibles(nivel, j)` (l. 3073): Los objetos del piso: frenan, se acercan si estas cerca (o si la sala esta limpia) y al tocarlos se usan o van a la mochila.
      - `soltar_monedas(nivel, j, x, y, cantidad)` (l. 3093): Deja una pila de monedas en el piso (el amuleto moneda de la tienda las multiplica).
      - `tecla_de(accion)` (l. 3098): Tecla asignada a una accion en el perfil de teclado, para mostrarla en los carteles.
      - `ganar_xp(nivel, j, cantidad)` (l. 3102): Experiencia: el que pelea toda, los de la banca 3/4. Con el ajuste elastico: cada uno gana menos si va muy arriba del nivel
      - `amistad_de_era()` (l. 3117): Cuantas veces alguien quiso unirse en esta era y cuantas salas van sin que nadie quiera (se reinicia al cambiar de era).
      - `amigo_garantizado()` (l. 3123): Si en esta sala alguien tiene que querer unirse si o si: la sala 2 de la Era Glacial, y en cada era la 1ra oferta
      - `quiza_amigo(nivel, j, e)` (l. 3131): A veces un pokemon derrotado quiere unirse a vos (no se captura: se hace tu amigo).
      - `hablar_amigo(nivel, j)` (l. 3157): Interactuar con el que quiere unirse (el mas cercano, si hay varios por el baile). Devuelve True si estaba cerca.
      - `bailar(j, nivel)` (l. 3188): V / R3: bailas un momento (Rotate, o Twirl / Hop si no tiene) y le afecta a los que estan cerca
      - `premio_jefe(nivel, j, jefe)` (l. 3220): Los jefes dejan una MT que tu equipo pueda aprender (y el Regi, ademas, un objeto de evolucion si alguien lo necesita).
      - `abrir_portal(nivel, avisar)` (l. 3234): Cayo el Regi: Celebi aparece al lado de la puerta y la convierte en un portal del tiempo hacia la era siguiente.
      - `hablar_portal(nivel, j)` (l. 3251): E al lado de Celebi en la sala del Regi: te ofrece cruzar el portal ahora. Devuelve True si estaba cerca.
      - `vitrina_cercana(nivel, j)` (l. 3265): La vitrina sin vender mas cerca del jugador (si esta al alcance y no esta mas cerca el lugar donde cura Chikorita).
      - `bloque_cercano(j)` (l. 3275): El bloque de hielo de Regice que tenes al lado (si hay).
      - `empujar_bloque(nivel, j)` (l. 3281): E al lado de un bloque de hielo: sale disparado para el otro lado y se desliza por la escarcha.
      - `curandera_cerca(nivel, j)` (l. 3293): Si estas al lado del mostrador de Chikorita rosa (curaciones) en la tienda.
      - `hablar_curandera(nivel, j)` (l. 3298): E al lado de Chikorita rosa: curar al que pelea o curar (y revivir) a todo el equipo, por monedas. True si estaba cerca.
      - `comprar_cercano(nivel, j)` (l. 3325): E en la tienda: compra lo que tenes adelante. Devuelve True si habia algo para comprar.
      - `invocar_minion(nivel, nombre, pos, vida, intocable)` (l. 3351): Un pokemon de la pelea de un subjefe (Arrokuda, Pikachu, Magnemite, Grimer): lo mueve el subjefe, no da monedas
      - `actualizar_nivel(nivel, j)` (l. 3363): Todo lo que pasa en un frame de la sala: jugador, entorno, enemigos, jefe, balas, monedas, llave y puertas.
    - `armar_mecanicas()` (l. 3638): Las mecanicas unicas de cada linea (mecanicas.py): le pasa lo que necesitan del juego.
      - `mover_entidad(o, dx, dy, libre)` (l. 3640): Mueve a un enemigo (o al jugador) sin meterlo en paredes ni objetos (libre: bajo tierra, sin chocar).
      - `poner_buff(j, clave, valor, ms)` (l. 3646): Le pone un buff al jugador por unos milisegundos (lo usan las mecánicas).
      - `guardar_y_aplicar(j)` (l. 3649): Después de que una mecánica tocó al equipo: la vida del que pelea y la sinergia al día.
      - `rehacer_animador(ent, nombre)` (l. 3652): Cambia los sprites (la Ilusion de Zorua, o un enemigo disfrazado que se revela).
      - `enemigos_de_era(nivel)` (l. 3661): Los pokemon de la era de la sala (para las mecánicas que invocan o copian).
    - `armar_hall()` (l. 3679): El hall (como la casa de Hades): al caer todo el equipo Celebi te trae aca. El viaje se pierde, pero tus amigos se quedan
      - `charla_de(a, perfil)` (l. 3684): Lo que dice un amigo del refugio: segun su especie, su tipo, su naturaleza, cuanto te quiere y hasta donde llegaron juntos (modos.py).
      - `pedir_favor(a, perfil, nombre)` (l. 3698): Un amigo te pide algo para el proximo viaje (uno a la vez): si lo cumplis con el en el equipo, sube su amistad.
      - `perfil_nuevo(nombre, genero)` (l. 3713): El perfil de una partida nueva (despues del viaje temporal).
      - `registrar_amigos(perfil, miembros)` (l. 3717): Guarda (o actualiza) a estos pokemon en tus amigos: su forma (la evolucion que alcanzaron no se pierde aunque caiga el equipo),
      - `desbloquear_todo(perfil)` (l. 3729): Truco: todas las eras derrotadas, todos los titanes en su sala y un amigo de cada especie que se puede jugar.
      - `miembro_de(a)` (l. 3739): Un amigo listo para viajar: en la forma que alcanzo (sus evoluciones se quedan) y en el nivel del principio, con sus IV, su
      - `estilo_hall(perfil)` (l. 3747): Que hall toca segun Ajustes > Hall: auto = donde aparece Celebi hasta que derrotes una era, despues el atemporal.
      - `residente(a, punto)` (l. 3753): Un amigo que pasea por el hall (no esta en tu equipo): se anima como los enemigos pero no pelea.
      - `pisables_hall(sala)` (l. 3762): Centros de las casillas del hall donde se puede caminar (sin objetos, sin agua ni vacio).
      - `crear_hall(j, perfil)` (l. 3769): Arma la zona del refugio en la que estas (plaza, barrio, minijuegos, dojo o una habitacion): sin enemigos, con las puertas
      - `zona_amigo(a, h)` (l. 3825): Donde esta un amigo a esa hora: su rutina (modos.RUTINAS, una por id) corrida hasta 45 minutos.
      - `amigos_en(perfil, zona, en_equipo)` (l. 3832): Los amigos (que no estan en tu equipo) que a esta hora estan en esa zona del refugio.
      - `salida_hacia(nivel, zona_destino)` (l. 3836): La puerta de la zona que lleva a otra (desde las habitaciones se sale a la plaza); si no hay, cualquiera.
      - `mover_amigos(nivel, perfil, zona)` (l. 3843): Una vez por segundo: al que ya le toca estar en otro lado camina hasta la puerta y se va; el que llega entra por una puerta.
      - `actualizar_residentes(nivel)` (l. 3856): Tus amigos pasean: eligen un lugar y caminan (arrancan despacio y frenan al llegar; a veces se paran a mirar); al llegar
      - `posar(r, pose, ms)` (l. 3895): Un amigo del hall hace una animacion un rato (Nod al hablarle, Hop cuando viene al viaje).
      - `cerca(j, punto, distancia)` (l. 3902): Si el jugador está a menos de cierta distancia de un punto (para hablar o usar algo).
      - `hay_pasillo(nivel, puerta, rec)` (l. 3905): Si antes de la sala que sigue hay un camino tranquilo (no en el boss rush ni en el tutorial, ni saliendo de otro camino).
      - `poblar_pasillo(nivel)` (l. 3912): Pokemon de la era paseando por el camino (los mismos cada vez que pasas: salen de la semilla de la sala).
      - `hablar_pasillo(nivel, j)` (l. 3921): E en un camino: el pokemon mas cercano te dice algo de su era y, a veces, te regala una baya.
      - `hablar_hall(nivel, j, perfil)` (l. 3933): E en el hall: hablar con Celebi o con un amigo (o, en un camino, con los pokemon de la era). Devuelve True si habia alguien cerca.
      - `hablar_con(nivel, j, perfil, r)` (l. 3962): Charlar con un amigo del refugio (y llevarlo al proximo viaje si queres).
    - **El refugio de Celebi: zonas, cosas para tocar y misiones**
      - `_hoja(nombre)` (l. 3990): Ruta de una hoja suelta del Explorers of Sky en assets.
      - `imagen_refugio(ruta)` (l. 3999): Un pedazo de una hoja de assets (cargado una vez) para los cuadros del refugio.
      - `estado_misiones(perfil)` (l. 4011): Las misiones del perfil (las arma si es una partida vieja que no las tenía).
      - `mision_evento(evento, cantidad)` (l. 4017): Algo paso en el viaje (derrota, sala, jefe, nota_s, evolucion): suma a las misiones activas que lo cuentan.
      - `tablon_misiones(perfil)` (l. 4042): El tablon: activar o dejar misiones (hasta 3 a la vez).
      - `ver_imagen(ruta, titulo, texto)` (l. 4063): Un cuadro de la galeria (o el cielo) en grande con su marco y una linea que lo cuenta.
      - `observatorio()` (l. 4082): El telescopio: el cosmos (los cielos del PMD que se van fundiendo) con estrellas fugaces. Las estrellas guardan los otros modos.
      - `accion_punto(nivel, j, perfil, p)` (l. 4113): E al lado de algo del refugio (carteles, cuadros, camas, telescopio...). Devuelve 'salir' si se cerro la ventana.
      - `dibujar_refugio(nivel, j, cx, cy)` (l. 4179): Encima del refugio: carteles de los edificios, las cosas que se pueden tocar (con 'E: ...' si estas cerca), los cuadros de
      - `punto_cercano(nivel, j)` (l. 4219): El punto del refugio al alcance (cartel, cama, telescopio...) más cercano al jugador.
      - `revisar_pasos(nivel, j)` (l. 4223): Entrar o salir de una habitacion del refugio caminando por su puerta. True si hay que cambiar de zona.
      - `crear_dojo(j)` (l. 4236): El dojo del salon: la sala de prueba (muñecos y enemigos que reaparecen) para probar pokemon. Lo que cambies con F1 aca
      - `volver_al_hall(j, perfil)` (l. 4247): Cayo todo el equipo: el viaje se pierde. Tus amigos (equipo y reserva) quedan en el perfil y vuelven al hall evolucionados como
      - `caida(nivel, j, rec)` (l. 4260): Cayo todo el equipo: el ultimo se desmaya (Faint, o Hurt si no tiene), la pantalla se oscurece y Celebi te va a buscar.
      - `empezar_viaje(j)` (l. 4286): Cruzaste el portal: el equipo arranca con la vida llena (ya esta en su forma base y en el nivel del principio).
    - `armar_dibujo()` (l. 4304): Todo lo que se dibuja jugando: jugador, HUD, indicadores, carteles, tienda y objetos.
      - `dibujar_rect(rect, cx, cy, color, forma)` (l. 4306): Rectangulo (o elipse) del mundo dibujado en la pantalla segun la camara.
      - `pies(animador)` (l. 4313): (x, y, ancho) de los pies de un pokemon en el mundo: lo mas bajo de su dibujo (cada cuadro se mide una vez).
      - `cuerpos_de(nivel, j)` (l. 4325): Los pies de los pokemon de la sala (para sus sombras). De paso, los que caminan por la hierba la sacuden.
      - `dibujar_jugador(j, cx, cy)` (l. 4339): Dibuja al pokemon activo (un cuadrado rosa si no tiene sprites).
      - `dibujar_congelado(j, cx, cy)` (l. 4357): Si el jugador esta congelado, un bloque de hielo encima.
      - `barra(rect, vida, max_vida, alto)` (l. 4364): Barrita de vida de BW arriba de un enemigo.
      - `borde_peligro()` (l. 4380): Los bordes de la pantalla en rojo (se arma una vez): mas fuerte en las esquinas, nada en el medio.
      - `borde_frenesi()` (l. 4394): Los bordes de la pantalla en naranja (como los del peligro, se arma una vez): se ven mientras dura el frenesi.
      - `render(f, texto, color)` (l. 4404): Texto ya renderizado: el HUD dibuja los mismos textos cada frame, asi se hace una sola vez.
      - `retrato(nombre, radio)` (l. 4412): Retrato redondo de un pokemon (recortado en circulo y guardado).
      - `sombra_circular(radio, alfa)` (l. 4427): Circulo negro semitransparente (pokemon en espera, especial recargando), armado una vez por tamaño.
      - `circulo_poke(centro, radio, nombre, atenuado)` (l. 4434): Circulo blanco con la cara del pokemon (o sus iniciales); oscurecido si esta esperando o debilitado.
      - `dibujar_corte(nivel, ahora)` (l. 4448): Al entrar en frenesi, una franja cruzada como en Persona: entra de golpe desde la derecha con la cara de tu pokemon,
      - `con_sombra(f, texto, color, pos)` (l. 4487): Texto claro con sombra oscura: se lee sobre cualquier piso.
      - `cortar(f, texto, ancho)` (l. 4495): El texto recortado con '…' para que entre en 'ancho' pixeles.
      - `pieza_mini(nombre, escala)` (l. 4504): Una pieza de assets/interfaz/minimapa (la recorta: python herramientas.py minimapa), agrandada. None si falta.
      - `fondo_minimapa(nivel, c)` (l. 4514): El piso de la sala con la trama azul del PMD y los bordes blancos donde termina (paredes, vacio, objetos que no se pisan).
        - `piso(f, col)` (l. 4522): Si una casilla es piso (para el minimapa).
      - `dibujar_minimapa(nivel, j, derecha, arriba)` (l. 4538): Minimapa como el de la pantalla de arriba del Mystery Dungeon: el piso de la sala, las puertas (escaleras), la llave
        - `icono(nombre, pos)` (l. 4554): Pone un ícono del PMD en el minimapa en el lugar de la sala que corresponde.
      - `tela_cinturon()` (l. 4588): El cuarto de circulo marron medio transparente, como la tela de un mostrador (con flecos y una costura). Se arma una vez.
      - `lugares_cinturon()` (l. 4607): Centros de los 5 circulos del cinturon (del 1 abajo a la izquierda al 5 arriba a la derecha).
      - `dibujar_cinturon(j, ahora)` (l. 4613): Abajo a la derecha: la tela marron y adentro las 5 curaciones (circulos negros con el numero del orden en que se usan con
      - `dibujar_ataques(j, ahora, congelado)` (l. 4638): Alrededor del cuarto de circulo: E, Q, Shift y R (los 4 movimientos) y F y G (las asistencias de la banca), en botones
      - `dibujar_estilo(j, xe, ye, ahora)` (l. 4688): El estilo (la letra de D a S, la barra hasta la proxima y la racha), con el centro en (xe, ye).
      - `dibujar_prueba(nivel, j)` (l. 4709): Panel del modo prueba: modo, daño que le hiciste a los muñecos, teclas y lo que hace la mecanica del pokemon.
      - `dibujar_hud(j, nivel, rec)` (l. 4740): HUD como el combate de BW: arriba a la izquierda tu pokemon (barra de HP con la placa, experiencia y energia), la banca en
      - **Tu pokemon**
      - **La banca**
      - **Abajo a la derecha: el cinturon (cuarto de circulo) y los ataques alrededor**
      - **Arriba a la derecha: el minimapa en la esquina y el estilo a su izquierda (debajo de la barra del jefe si hay)**
      - **Donde estas**
      - **El jefe: la barra del rival de BW**
      - `dibujar_indicadores(nivel, cx, cy)` (l. 4840): Circulito con punta en el borde de la pantalla para cada enemigo que no se ve, con su cara en chiquito.
      - `silueta(img, color, alfa)` (l. 4873): La forma de un sprite pintada de un color con transparencia (estelas, destellos de golpe). Se arma una vez y se reusa.
      - `franja(ancho, alto, color, inclinacion)` (l. 4883): Paralelogramo (franja inclinada) del color pedido, con transparencia.
      - `dibujar_carteles(nivel)` (l. 4891): Carteles: el grande (nombre de la sala, jefes, fases) es una franja inclinada que entra barriendo desde la izquierda con
      - `panel_tienda(color)` (l. 4946): El panel de abajo a la izquierda donde se lee que vas a comprar (no lo tapa el cuarto de circulo de los ataques).
      - `dibujar_tienda(nivel, j, cx, cy)` (l. 4953): Tienda: el cartel de cada mostrador y sus objetos con el precio (el que tenes mas cerca se marca y muestra el nombre).
      - `dibujar_numeros(nivel, cx, cy, ahora)` (l. 5010): Numeros de daño que saltan y suben: blancos, amarillos si fue super eficaz, grises si resistio, naranjas y grandes en
      - `dibujar_aviso_evolucion(nivel, j)` (l. 5022): Abajo en el medio: el retrato del que quiere evolucionar, una flecha, el de su evolucion y la tecla con el anillo que se llena.
      - `dibujar_objetos(nivel, j, rec)` (l. 5045): Dibuja un frame de la partida: sala, puertas, balas, efectos, pokemon, jefe, clima, HUD y carteles.
      - `luces_de(nivel, j, cx)` (l. 5314): Lo que alumbra en la sala aparte de la sala misma: vos (los de fuego, mas), los enemigos de fuego y electricos, las balas de
      - `dibujar_celebi_cine(a, x, y, cx, cy, ahora, anim, direccion, esc)` (l. 5341): Celebi en una escena (en coordenadas de la sala), flotando, con brillitos detras.
      - `nivel_cuadro(ahora)` (l. 5351): El número de cuadro (a 60 por segundo) de un momento.
      - `dibujar_cine(nivel, j, cx, cy, ahora)` (l. 5353): Lo que se ve de las escenas: los portales y Celebi (la entrada del jefe no necesita nada: es el jefe mismo).
    - **El mapa grande (tecla M)**
      - `fondo_mapa()` (l. 5398): Atras del mapa grande: el marron a cuadros del mapa de la pantalla de arriba del PMD (se arma una vez).
      - `bloque_pmd(rect, lleno, esc)` (l. 5410): Un bloque del mapa del PMD: la trama azul con el borde blanco (lleno: el azul parejo, la sala donde estas).
      - `icono_mapa(nombre, pos, esc)` (l. 5425): Dibuja un ícono del mapa del PMD agrandado en ese lugar de la pantalla.
      - `etiqueta(texto, pos, color)` (l. 5429): Un texto chico con borde, centrado debajo de un punto (nombres del mapa).
      - `disposicion_era(rec, era)` (l. 5432): Donde va cada sala de la era en el mapa: la primera en (0, 0) y cada una al lado de la anterior, para el lado de la puerta
      - `mapa_era(rec, j, ahora, corrido, zoom)` (l. 5447): El mapa de la era como en un metroidvania: cada sala y cada camino por los que pasaste (los bloques azules del PMD), las puertas
        - `tam_de(r)` (l. 5459): El tamaño del bloque de cada sala en el mapa de la era.
      - `mapa_refugio(nivel, j, ahora, corrido, zoom)` (l. 5498): El mapa de la zona del refugio donde estas, grande: el piso con los bloques del PMD y todo lo que hay (las puertas de las chozas
      - `flecha_mapa(punta, ahora, color)` (l. 5538): Flecha que apunta para abajo y rebota, con la punta en 'punta' (marca un lugar en el mapa).
      - `flecha_borde(p, vista, texto, color)` (l. 5544): Un lugar que quedo fuera de la vista del mapa: una flecha en el borde apuntando para alla, con su nombre.
      - `mapa_completo(nivel, j, rec)` (l. 5556): Tecla M: el mapa grande sobre el fondo marron del PMD. En un viaje, el de la era; en el refugio, el de la zona donde estas
    - `armar_extras()` (l. 5587): Pantalla final, acciones del menu de equipo (TAB) y trucos.
      - `pantalla_final()` (l. 5589): Cuando cae Arceus.
      - `acciones_equipo(j)` (l. 5606): Lo que puede hacer el menu de equipo (TAB) sobre el jugador.
        - `refrescar()` (l. 5608): Recalcula vida y multiplicadores despues de gastar puntos o subir de nivel desde el menu.
        - `evolucionar(i, req)` (l. 5616): Evoluciona al pokemon i (gasta el objeto si hacia falta) manteniendo el porcentaje de vida.
        - `enseñar(i, casilla, mt)` (l. 5635): Enseña una MT en una casilla de movimiento (la MT se gasta salvo con los trucos).
        - `traer(ri, k)` (l. 5643): Trae un pokemon de la reserva al equipo (al final, o cambiandolo por el del espacio k).
        - `movs(m)` (l. 5653): Nombres de los 4 movimientos de un miembro (E, Q, Shift, R) con sus MT puestas.
        - `info_movs(m)` (l. 5658): Que hace cada una de las 4 casillas: texto listo para mostrar (con los ajustes de los basicos y el combo).
        - `equipar(i, ranura, clave)` (l. 5671): Pone (o saca, con clave None) un objeto en la ranura 0 o 1 del pokemon i. El que estaba vuelve a la mochila.
        - `elegir_sinergia(i, clave)` (l. 5679): La pasiva que da el pokemon i desde la banca (None = la de su rol).
        - `texto_asistencia(m)` (l. 5684): Que hace la asistencia de un miembro (F / G desde la banca).
        - `caramelo(i)` (l. 5689): Caramelo Raro: el pokemon i sube un nivel (gasta un caramelo).
        - `usar(i, indice)` (l. 5700): Usa la curacion de ese lugar del cinturon en el miembro i (o en el de la reserva si i es ('r', k)). Devuelve el texto.
        - `datos_movs(m)` (l. 5706): Los datos de las 4 casillas (E, Q, Shift, R) con las MT puestas, para la pestaña Ataques de la ficha.
      - `aplicar_trucos(nivel, j)` (l. 5717): Los trucos que hacen algo una sola vez (subir niveles).
      - `evolucion_pendiente(j)` (l. 5726): (indice, requisito) del primero del equipo que ya puede evolucionar, o None.
      - `actualizar_evolucion(nivel, j, mantiene)` (l. 5734): Evolucionar sin menus: cuando no hay peligro aparece el aviso y manteniendo la tecla se llena un anillo y evoluciona ahi mismo.
    - `armar_modos()` (l. 5760): Lo que no es el viaje: el tutorial de la isla de Celebi, el boss rush (libre o con tu partida), los titanes del refugio y
      - `plan_era_rush(k, e)` (l. 5765): Las peleas de una era en el boss rush, en el orden de un viaje: una tienda antes (menos en la primera), el primer subjefe
      - `letra(tam, borde)` (l. 5775): Las letras de los paneles (se arman una vez).
      - `panel(caja, color)` (l. 5780): Fondo oscuro medio transparente con borde, para los carteles de los modos.
      - `reloj_txt(ms)` (l. 5785): Milisegundos como minutos:segundos.
      - `nivel_suelto(sala, tipo, nv, modo_prueba)` (l. 5788): Una sala fuera del viaje (como la del modo prueba): no hay registro que guardar y si cae el equipo no se pierde nada.
    - **El tutorial: la isla de practica de Celebi**
      - `muñeco_en(nivel, nombre, punto, nv)` (l. 5807): Un muñeco de practica: no pega, no se mueve y no se muere.
      - `de_practica(nivel, j, nombre, punto, estilo, vida, daño, **extra)` (l. 5814): Un enemigo de verdad pero flojito (para practicar el parry, el baile y las salas). 'unico': si cae no reaparece.
      - `vasijas(nivel)` (l. 5822): Cuántos barriles y cajas quedan sanos en la sala (minijuego de romper).
      - `crear_tutorial(j)` (l. 5825): La sala del tutorial en la que estas: la isla (casi todos los pasos) o la tienda de practica (comprar y salir).
      - `empezar_paso(nivel, j, clave)` (l. 5849): Prepara lo que hace falta para el paso: la marca a la que ir, el rival del parry, Torchic, el Machop cansado, la pelea de la sala...
      - `poner_amigo(nivel, j)` (l. 5880): El Machop cansado del paso de la amistad (con poca vida: el baile lo encariña).
      - `paso_cumplido(nivel, j, clave)` (l. 5886): Si ya hiciste lo que pide el paso. d['n'] / d['de'] es lo que se muestra como avance (2/3).
      - `actualizar_tutorial(nivel, j, resultado)` (l. 5921): Un cuadro del tutorial: empieza el paso que toca, mira si lo cumpliste y pasa al siguiente. Salir por la puerta de la isla
      - `dibujar_tutorial(nivel, j, cx, cy)` (l. 5940): El panel de Celebi arriba (el paso, lo que hay que hacer y cuanto llevas), el consejo y la marca a la que hay que ir.
    - **Boss rush: todos los jefes seguidos**
      - `recorrido_rush(solo)` (l. 5972): El plan del boss rush: en cada era sus dos subjefes, el semijefe y el Regi (con una tienda antes, menos en la primera) y al
      - `empezar_rush(j, pedido, propio)` (l. 5981): Arranca el boss rush. Con tu partida (propio): tu equipo de verdad, tus monedas y tu mochila quedan guardados aparte y vuelven al terminar.
      - `preparar_rush(nivel, j)` (l. 5994): Antes de cada jefe del rush: el equipo sube solo hasta un poco menos que el jefe (como llegarias en un viaje) y, si no es el
      - `pantalla_rush(r, gano, ms, premio)` (l. 6010): Como te fue en el boss rush: cuantos jefes, en cuanto tiempo y lo que te llevas.
      - `terminar_rush(j, gano)` (l. 6031): Se termino el boss rush (ganaste, cayo el equipo o te retiraste). Si era con tu partida vuelve tu equipo de verdad al
      - `dibujar_rush(nivel)` (l. 6051): La chapita del boss rush abajo al medio: por que jefe vas y cuanto tiempo llevas.
    - **Los titanes: los jefes que ya derrotaste te esperan en el refugio**
      - `crear_titanes(sala, perfil)` (l. 6062): Un titan por pedestal. Los que todavia no derrotaste se ven como una sombra.
      - `titan_cercano(nivel, j)` (l. 6075): El titán de la sala de los titanes al que estás parado al lado.
      - `hablar_titan(nivel, j, perfil)` (l. 6079): E al lado de un titan: te cuenta algo y te ofrece la revancha (un boss rush de un solo jefe). Devuelve True si habia uno cerca.
      - `dibujar_titan(t, j, cx, cy)` (l. 6093): El titan sobre su pedestal (una sombra si todavia no lo derrotaste), con su nombre y el cartelito para hablarle.
    - **Minijuegos de la cancha**
      - `crear_minijuego(j, clave)` (l. 6113): Arma el minijuego en una arena: tu equipo entra con la vida llena (es prestado, como en el dojo) y los enemigos reaparecen solos.
      - `actualizar_minijuego(nivel, j, resultado)` (l. 6131): Lleva la cuenta del minijuego y lo termina cuando se acaba el tiempo (o, en supervivencia, cuando cae todo el equipo).
      - `dibujar_minijuego(nivel)` (l. 6161): Arriba al medio: el nombre, el tiempo y los puntos. Antes de empezar, la cuenta regresiva en grande.
    - **Lo que llama el bucle de la partida**
      - `actualizar_modo(nivel, j, resultado)` (l. 6177): Despues de cada cuadro: el tutorial y el minijuego avanzan, y el boss rush termina si cayo el equipo.
      - `dibujar_modo(nivel, j, cx, cy)` (l. 6188): El panel del modo en curso: tutorial, minijuego o boss rush.
    - `armar_guardado()` (l. 6200): Pasar la partida a datos guardables (equipo, mochila, recorrido) y armarla de vuelta al cargar.
      - `serializar(j, rec)` (l. 6204): Todo lo que hace falta para seguir la partida despues (en el hall el recorrido es el del proximo viaje, todavia sin empezar).
      - `revivir(d)` (l. 6220): Un miembro del equipo desde lo guardado (la vida maxima y la asistencia se recalculan).
      - `restaurar(datos_)` (l. 6229): (jugador, recorrido) de una partida guardada.
      - `guardar_partida(j, rec)` (l. 6249): Autoguardado en la ranura de esta partida (al entrar a cada sala, al completarla y al comprar).

### `sistema.py` (1451 líneas)

> sistema.py - Lo basico para que el juego funcione: ajustes guardados, ventana, teclado/control y animaciones de los sprites.
>
>     opciones      cargar y guardar config.json
>     partidas      las 3 partidas guardadas (carpeta partidas/)
>     tipografia    la letra de los juegos de DS (recortada de la hoja de HeartGold/SoulSilver)
>     pantalla      dibuja en 1000x600 y escala a la ventana
>     controles     teclas configurables, control (joystick) y codigo Konami
>     animaciones   AnimadorPokemon: lee las hojas de sprites del PMD
>
>     from sistema import opciones, partidas, tipografia, pantalla, controles, animaciones

- **Opciones**
- `armar_opciones()` (l. 26): Ajustes del juego guardados en config.json (volumen, combate, resolucion, controles...).
  - `cargar()` (l. 40): Lee config.json sobre los valores por defecto (los trucos siempre arrancan apagados).
  - `guardar(config)` (l. 53): Guarda la configuracion en config.json (sin los trucos).
- **Partidas**
- `armar_partidas()` (l. 67): Partidas guardadas: 3 ranuras en la carpeta partidas/ (partida_1.json ...). Guardan el equipo (niveles, experiencia, EV,
  - `_ruta(ranura)` (l. 81): El archivo de una ranura de partida.
  - `cargar(ranura)` (l. 85): Los datos de la partida guardada en esa ranura, o None si no hay (o el archivo esta roto).
  - `guardar(ranura, datos)` (l. 93): Guarda la partida (primero en un archivo temporal, asi un corte no deja el guardado a medias).
  - `borrar(ranura)` (l. 104): Borra la partida de una ranura.
  - `resumenes()` (l. 109): Lo que se muestra de cada ranura en el menu (None si esta vacia).
- **Tipografia**
- `armar_tipografia()` (l. 121): La letra de los juegos de Pokemon de DS (la de HeartGold/SoulSilver, igual a la de Blanco/Negro), recortada letra por letra de
  - `_cargar()` (l. 146): Lee la hoja una vez: por cada letra, sus pixeles de tinta y de sombra y su ancho.
  - `_color(c)` (l. 170): Un color de pygame como (r, g, b).
  - `sombra_de(color)` (l. 175): Sombra que contrasta: oscura para letras claras y gris clara para letras oscuras (como en los juegos).
  - `class FuenteDS` (l. 182): Misma forma de usar que pygame.font.Font (render, size, get_height, get_linesize).
    - `__init__(self, escala, borde)` (l. 186): Una letra de un tamaño (y con borde o no).
    - `set_bold(self, valor)` (l. 189): No hace nada: está para que se pueda usar como una fuente de pygame.
    - `get_height(self)` (l. 190): Alto de un renglón de esta letra.
    - `get_linesize(self)` (l. 191): Alto de un renglón con el espacio entre renglones.
    - `_glifo(self, letra)` (l. 192): El dibujo de una letra (o la más parecida si no está).
    - `size(self, texto)` (l. 196): Ancho y alto que ocupa un texto.
    - `render(self, texto, antialias, color, fondo)` (l. 200): El texto dibujado con esta letra (como Font.render de pygame, guardado en caché).
- **Letra de los titulos de Explorers of Sky y letras Unown de HGSS**
  - `_cargar_titulo()` (l. 237): Lee la hoja de la letra de los titulos del PMD: cada letra como superficie blanca (con su sombreado) sin el fondo negro.
  - `_cargar_unown()` (l. 257): Las 28 letras Unown de la fila dorada de la hoja de letras de HGSS, en negro sobre transparente.
  - `_con_borde(sup, color, grosor)` (l. 278): La superficie con un borde de 'grosor' pixeles del color pedido alrededor de lo que no es transparente.
  - `class FuenteTitulo` (l. 290): La letra de los nombres de mazmorra del PMD (blanca con borde negro). render(texto, aa, color) tiñe la letra con el color.
    - `__init__(self, escala, borde)` (l. 292): Una letra de un tamaño (y con borde o no).
    - `set_bold(self, valor)` (l. 295): No hace nada: está para que se pueda usar como una fuente de pygame.
    - `get_height(self)` (l. 296): Alto de un renglón de esta letra.
    - `get_linesize(self)` (l. 297): Alto de un renglón con el espacio entre renglones.
    - `size(self, texto)` (l. 298): Ancho y alto que ocupa un texto.
    - `render(self, texto, antialias, color, fondo)` (l. 300): El texto dibujado con esta letra (como Font.render de pygame, guardado en caché).
  - `fuente_titulo(escala, borde)` (l. 318): La letra de los titulos del PMD (o la de DS si falta la hoja).
  - `unown(texto, escala, borde)` (l. 325): Palabra escrita con letras Unown (las de HGSS), con borde. None si falta la hoja. Devuelve una superficie por letra.
  - `escala_de(tam)` (l. 340): Cuanto se agranda la letra para el tamaño de pygame que pedian (la letra de pygame de 24 se parece a la de DS al x1).
  - `fuente(tam, borde, escala)` (l. 345): La letra de DS para ese tamaño (o la de pygame si no esta la hoja). escala: forzar x1, x2...
- **Pantalla**
- `armar_pantalla()` (l. 360): El juego se dibuja siempre en 1000x600 y se escala a la ventana (o a pantalla completa) con franjas negras si hace falta.
  - `iniciar(W, H, config)` (l. 371): Crea la superficie de 1000x600 donde se dibuja todo y abre la ventana.
  - `aplicar(config)` (l. 379): Abre la ventana con la resolucion elegida o en pantalla completa.
  - `poner_cursor()` (l. 403): Cursor de manito (assets/interfaz/cursor.png o el dibujo de MANO).
  - `presentar()` (l. 417): Pasa lo dibujado a la ventana: si hay que agrandarlo se escala directo sobre la ventana (sin crear una imagen nueva por frame).
  - `cursor(superficie, pos, escala)` (l. 432): La flechita del juego: blanca con borde azul oscuro y un brillo celeste, como los menus de BW. La punta esta en pos.
  - `a_logico(pos)` (l. 448): De pixeles de la ventana a pixeles del juego.
  - `raton()` (l. 455): Posicion del mouse en coordenadas del juego.
- **Controles**
- `armar_controles()` (l. 467): Teclado y control (joystick) con teclas configurables: 3 perfiles de teclado y 3 de control.
- **Perfiles**
  - `iniciar(config)` (l. 519): Arma los perfiles por defecto si no hay y abre los controles conectados.
  - `_abrir(indice)` (l. 537): Abre el control conectado en ese indice (si es un control reconocido por SDL).
  - `perfil(dispositivo)` (l. 546): Perfil elegido del teclado o del control: {accion: tecla o boton}.
  - `restaurar(dispositivo, indice)` (l. 552): Vuelve un perfil a las teclas de fabrica.
  - `nombre_tecla(e)` (l. 557): Nombre de la tecla de un evento ('e', 'left shift'...).
  - `hay_control()` (l. 562): Si hay algun control conectado.
  - `contexto(nuevo)` (l. 567): 'menu' o 'juego': cambia que hace el control.
- **Eventos**
  - `_konami(token, salida)` (l. 575): Avanza el codigo Konami. Devuelve True si hay que tragarse el evento (la B y la A del final).
  - `eventos()` (l. 587): Como pygame.event.get() pero con el control traducido (a teclas en los menus, a acciones en el juego).
  - `_acciones_boton(boton)` (l. 623): Acciones de juego asignadas a un boton del control (sin las de caminar).
  - `acciones(e)` (l. 628): Acciones de juego que dispara un evento (teclado segun el perfil, o boton del control).
- **Estado (lo que esta apretado)**
  - `_palanca(cual)` (l. 639): Palanca izquierda (0) o derecha (1) del primer control, de -1 a 1.
  - `_boton(nombre)` (l. 650): Si ese boton (o gatillo LT / RT) esta apretado en algun control.
  - `mantiene(accion)` (l. 664): Si la accion esta apretada ahora, en el teclado o en el control.
  - `direccion()` (l. 674): Movimiento: teclas del perfil + palanca izquierda + cruz del control.
  - `apuntado()` (l. 686): Hacia donde apunta la palanca derecha (vector normalizado) o None.
  - `inclinacion()` (l. 693): Cuanto esta inclinada la palanca derecha (0 a 1): para elegir a que distancia cae lo que se tira en un punto.
  - `esperar_entrada(dispositivo, presentar, dibujar)` (l. 698): Para reasignar: espera una tecla (o un boton del control). ESC cancela. Devuelve el nombre o None.
- **Animaciones**
- `armar_animaciones()` (l. 720): Animaciones de los pokemon con las hojas de sprites del PMD (AnimData.xml) o el formato viejo de carpetas.
  - `_normalizar_nombre(nombre)` (l. 735): Nombre en minuscula con guiones bajos ('Samurott Hisui' -> 'samurott_hisui').
  - `_buscar_carpeta(nombre)` (l. 743): Carpeta de sprites del pokemon en assets/sprites/pokemones (se busca en el disco una sola vez por nombre).
  - `_propias(nombre)` (l. 768): Si el pokemon tiene sus propias animaciones (no las de su especie base).
  - `_base(nombre)` (l. 773): El pokemon del que salen los sprites (chikorita_rosa usa los de chikorita; Amoonguss, los de Foongus mientras no tenga los suyos).
  - `teñir(hoja, tono)` (l. 780): Cambia el tono de los colores verdes de una hoja (los ojos, el contorno y lo demas quedan igual).
  - `tiene_sprites(nombre)` (l. 799): Si el pokemon (o el pokemon base de un tinte, como chikorita_rosa) tiene sprites para animarse. Una carpeta con solo el
  - `_numero_direccion(nombre)` (l. 812): Ultimo numero en el nombre de un archivo (formato viejo: idle_3.png -> 3).
  - `class _HojasPerezosas` (l. 879): Diccionario animacion -> frames que lee cada hoja recien la primera vez que se pide.
    - `__init__(self, cargar)` (l. 883): cargar(nombre) lee la hoja de esa animacion cuando se pide por primera vez.
    - `__getitem__(self, nombre)` (l. 888): Frames de la animacion: los lee si hace falta (y resuelve las copias).
    - `get(self, nombre, defecto)` (l. 898): Como dict.get, pero leyendo la hoja si hace falta.
  - `class AnimacionHoja` (l. 903): Clase.
    - `__init__(self, nombre, indice, ancho, alto, duraciones, rush, hit, retorno, copia)` (l. 904): Datos de una animacion del AnimData.xml: tamaño de cada frame, duracion de cada uno y frames especiales.
  - `class AnimadorPokemon` (l. 917): Clase.
    - `__init__(self, pokemon, rect, tamaño)` (l. 936): pokemon: nombre (o variante de color), rect: donde se dibuja (el centro), tamaño: alto en pixeles en pantalla.
    - `_cargar_con_cache(self)` (l. 965): Comparte las hojas entre todos los animadores del mismo pokemon (se leen una sola vez).
    - `_cargar(self)` (l. 974): Carga las animaciones: hojas del PMD si hay AnimData.xml, si no el formato viejo de carpetas.
    - `_cargar_hojas(self, xml)` (l. 984): Lee el AnimData.xml: que animaciones hay, el tamaño de sus frames y sus duraciones.
    - `_resolver_copias(self)` (l. 1041): Las animaciones 'CopyOf' toman los datos de la animacion que copian.
    - `_ruta_hoja(self, anim)` (l. 1056): (archivo, prefijo) de la hoja <Anim>-Anim.png de esa animacion, o None si no esta. No la lee.
    - `_leer_hoja(self, anim, ruta, nombre)` (l. 1077): Lee la hoja de una animacion y la corta en frames: una fila por direccion (hasta 8), una columna por frame.
    - `_cargar_metadatos(self, anim, prefijo)` (l. 1097): Offsets de la animacion (<Anim>-Offsets.png). Las -Shadow.png no se leen: el juego dibuja sus propias sombras.
    - `_cargar_formato_antiguo(self)` (l. 1107): Formato viejo: una carpeta por animacion con una imagen por direccion.
    - `_calcular_escala_base(self)` (l. 1128): Cuanto agrandar los sprites para que el pokemon mida 'tamaño' (se mide el dibujo mas alto de idle y walk).
    - `_buscar_animacion(self, nombre)` (l. 1146): Nombre real de una animacion pedida ('attack' busca strike, punch...). None si no tiene ninguna.
    - `buscar_ataque(self)` (l. 1161): La primera animacion de ataque que tenga el pokemon.
    - `buscar_para(self, forma)` (l. 1168): Animacion para una forma de ataque (proyectil -> Shoot, area -> Swing...).
    - `buscar_movimiento(self, movimiento, tipo, forma)` (l. 1175): Animacion para un movimiento: por su nombre (puño -> Punch), por tipo y forma, o la de la forma.
    - `disponibles(self)` (l. 1187): Nombres de todas las animaciones que tiene el pokemon.
    - `cambiar(self, animacion, direccion, repetir)` (l. 1191): Pasa a otra animacion (o solo gira si es la misma). repetir=False la deja en el ultimo frame y marca terminada.
    - `actualizar(self)` (l. 1216): Avanza un frame del juego: pasa al siguiente frame de la animacion cuando se cumple su duracion.
    - `_frames_actuales(self)` (l. 1247): Frames de la animacion actual en la direccion actual.
    - `_fila(self)` (l. 1255): Fila de la hoja (direccion); algunas hojas tienen una sola y se usa esa.
    - `_factor_actual(self)` (l. 1265): Multiplicador de las duraciones: caminar va al ritmo de la velocidad, los ataques al ritmo del ataque.
    - `_duracion_actual(self)` (l. 1274): Cuantos frames del juego dura el frame actual de la animacion.
    - `esta_terminada(self)` (l. 1290): Si la animacion sin repetir llego al final.
    - `_obtener_offset(self, imagen, animacion, direccion, frame)` (l. 1294): Punto del frame que va en el centro del rect (el pixel verde de la hoja de offsets del PMD).
    - `_escalar(self, imagen, ancho, alto)` (l. 1315): Agranda un frame (sin suavizar, para que se vean los pixeles).
    - `cuadro(self)` (l. 1321): (imagen, x, y) del frame actual ya escalado y donde va su esquina de arriba a la izquierda, o None (para estelas y destellos).
    - `dibujar(self, ventana)` (l. 1329): Dibuja el frame actual centrado en el rect (escalado una sola vez y guardado). False si no hay frames.
  - `cargar_retrato(nombre)` (l. 1353): Retrato del pokemon (portrait/Normal.png del PMD), teñido si es una variante de color. None si no tiene.
- **Sonido**
- `armar_sonido()` (l. 1381): Gritos de los pokemon (assets/sonidos/gritos/<nombre>.ogg, los baja 'python herramientas.py sonidos') y musica
  - `listo()` (l. 1393): Arranca el mezclador la primera vez (False si no hay audio).
  - `iniciar(config)` (l. 1403): Arranca el sonido con la configuración (volumen).
  - `volumen()` (l. 1407): Aplica el volumen de la musica de los ajustes.
  - `grito(nombre, fuerza)` (l. 1413): El grito de un pokemon (las variantes de color usan el de su especie).
  - `_archivo(pista)` (l. 1426): El archivo de música de una pista (o el de la pista de respaldo si falta).
  - `musica(pista)` (l. 1435): Cambia la musica (con un fundido). Si ya suena el mismo archivo, sigue sin cortarse.

### `datos.py` (1916 líneas)

> datos.py - Todo lo que es informacion del juego (no dibuja nada):
>
>     ataques     habilidades y sinergias de ataques.py
>     pokemones   especies, movimientos, tabla de tipos, roles, asistencias (antes pokemones.py)
>     mts         Maquinas Tecnicas que se compran y se enseñan
>     tienda      objetos de Kecleon, inventario y lo que hace cada cosa comprada
>     mundos      eras, terrenos, objetos, piezas, climas y el plan de salas de la partida
>
>     from datos import pokemones, mundos, mts, tienda, ataques

- **Ataques**
- `explicar_movimiento(datos, casilla)` (l. 101): Lo que hace un movimiento contado en palabras (para la seccion de ataques y la ficha). casilla 0 = E (combo y parry).
- `describir_asistencia(a)` (l. 138): Texto de lo que hace una asistencia (lo que el pokemon de la banca hace con F / G).
- `nombre_ataque(clave)` (l. 150): Nombre para mostrar ('fuerza_rayo' -> 'Rayo potenciado', 'onda_surf' -> 'Onda de Surf', 'mtb_rayo' -> 'Rayo').
- `describir_movimiento(datos)` (l. 162): Texto corto de lo que hace un movimiento: forma, daño, alcance, efecto y espera ('golpe cuerpo a cuerpo, daño 20, quema (15%), espera 0.5 s').
  - `num(clave)` (l. 165): Un número de los datos del movimiento (0 si no hay).
- **Pokemones**
- `armar_pokemones()` (l. 193): Especies, movimientos, tabla de tipos, roles, especiales, asistencias y evoluciones.
- **Expansion: ~60 lineas evolutivas nuevas (datos de la PokeAPI, sprites de SpriteCollab)**
  - `normalizar_tipo(tipo)` (l. 405): Tipo en minuscula, sin tildes y en castellano ('Psíquico' o 'psychic' -> 'psiquico').
  - `multiplicador_tipos(ataque, defensas)` (l. 412): Multiplicador de un tipo de ataque contra uno o dos tipos (x2, x0.5; la inmunidad deja un poco de daño).
- **Balance de los movimientos basicos**
  - `fuerza_especie(nombre)` (l. 662): Las especies mas fuertes (evoluciones finales) pegan un poco mas: 1.0 con 300 de stats base totales, hasta x1.25 con 600.
  - `buscar_movimiento(nombre)` (l. 695): Datos de un movimiento (especiales primero, despues los normales). None si no existe.
  - `_potenciado(nombre)` (l. 701): Version fuerte de un movimiento para el especial de los atacantes: mas daño, area y alcance, y atraviesa.
  - `_especiales_de(nombre, rol, tipos)` (l. 712): Los 2 especiales segun el rol: atacante (potenciado + danza espada), tanque (defensa + onda),
  - `sinergia_de(nombre, elegida)` (l. 745): Pasiva que da el pokemon desde la banca: la que elegiste en su ficha o, si no elegiste, la de su rol.
  - `datos_juego(nombre)` (l. 755): Todo lo que el combate necesita de una especie: vida, velocidad, tamaño, hitbox, multiplicadores y movimientos.
  - `_con_mecanica(nombre, especiales)` (l. 776): Si la linea tiene un especial propio (mecanicas.py), va en la casilla R en lugar del segundo especial del rol.
  - `_aprende(nombre, ingles)` (l. 813): Si la especie aprende ese movimiento en los juegos (sin datos de la PokeAPI cuenta como que si).
  - `_elegir(nombre, candidatos)` (l. 819): El primer movimiento de la lista que la especie aprende de verdad (o el primero si no hay datos).
  - `asistencia_de(nombre)` (l. 826): Asistencia de un pokemon (lo que hace desde la banca con F / G) segun su rol y sus tipos.
  - `_limpiar(n)` (l. 863): Nombre con espacios en vez de guiones.
  - `evoluciones_de(nombre)` (l. 868): (de quien evoluciona, [a quienes evoluciona]) con los datos de la PokeAPI o la tabla propia.
  - `descripcion_de(nombre)` (l. 881): Texto de la pokedex (PokeAPI) o None.
  - `stats_oficiales(nombre)` (l. 886): [(etiqueta, valor)] de los stats base oficiales, o None.
  - `aprende_de(nombre)` (l. 892): Movimientos que aprende en los juegos (PokeAPI) o None.
  - `debilidades_de(nombre)` (l. 898): Tipos agrupados por cuanto le pegan: x4, x2, x0.5, x0.25 y x0.
- **Mts**
- `armar_mts()` (l. 920): Maquinas Tecnicas: movimientos que se le enseñan a un pokemon en una de sus 4 casillas (E, Q, Shift, R).
  - `_convertir(h)` (l. 935): Pasa una habilidad de ataques.py al formato que usa el combate (forma, buffs, etc.).
  - `_precio(h)` (l. 948): Precio de una MT: las de buff y escudo valen 180, las de ataque segun su daño y si tienen efecto.
  - `sirve_en(clave, casilla)` (l. 965): Si la MT se puede poner en esa casilla (0 E, 1 Q, 2 Shift, 3 R): las de combate en todas, las especiales solo en Shift y R.
  - `datos(nombre)` (l. 971): Datos de combate de una MT (como un movimiento) o None si no es una MT.
  - `puede_aprender(pokemon, clave)` (l. 977): True si la especie aprende ese movimiento (segun la PokeAPI). Sin datos, cualquiera puede.
  - `aprendibles(pokemon)` (l. 988): MT que puede aprender ese pokemon.
- `catalogo_ataques()` (l. 998): Todos los ataques del juego por categoria: [(nombre, tipo, explicacion, numeros, quienes lo usan)].
- **Tienda**
- `armar_tienda()` (l. 1028): Objetos de la tienda (nada cura) y lo que hacen sobre el jugador.
- **Curaciones (las vende Chikorita rosa; se usan desde la mochila o con la tecla de curarse)**
  - `_texto_cura(c)` (l. 1167): 'cura 50 PS', 'saca el veneno', 'revive con la mitad de la vida'...
  - `usar_curativo(m, clave)` (l. 1185): Usa una curacion en un miembro del equipo. Devuelve (se uso, texto). No gasta nada si no hace falta.
  - `premios_tesoro(azar)` (l. 1220): Los 3 premios de una sala del tesoro: dos mejoras distintas y caramelos raros.
  - `inventario_nuevo()` (l. 1226): Inventario vacio de una partida nueva.
  - `es_curativo(clave)` (l. 1234): Si el objeto es una curacion (va al cinturon en vez de a la mochila).
  - `migrar_cinturon(inv)` (l. 1239): Partidas de antes: las curaciones estaban sueltas en la mochila. Pasan al cinturon en orden hasta llenarlo; las que no
  - `mult(inv, clave)` (l. 1251): Multiplicador de todo lo comprado para esa clave ('daño', 'defensa', 'velocidad', 'enfriamiento', 'regen', 'gasto', 'monedas').
  - `mult_tipo(inv, tipo)` (l. 1259): Multiplicador de daño de ese tipo por los objetos potenciadores comprados (carbon, agua mistica...).
  - `critico(inv)` (l. 1264): Multiplicador de un golpe: x1.8 si sale critico.
  - `factor_enemigos(inv)` (l. 1270): Con un repelente activo aparece el 65% de los enemigos.
  - `nueva_sala(inv, tipo)` (l. 1275): Al entrar a una sala con enemigos se gasta una sala de cada objeto temporal.
  - `activos(inv)` (l. 1283): Textos cortos de lo que tenes andando (para el HUD).
  - `surtido_mostradores(azar, vitrinas, equipo, necesita)` (l. 1299): Que objeto va en cada vitrina segun su mostrador ('chikorita', 'riolu' o 'kecleon')
  - `comprar(j, clave)` (l. 1322): Intenta comprar: devuelve el texto para el cartel.
  - `mult_equipados(items, clave)` (l. 1347): Multiplicador de los objetos que lleva el pokemon que pelea para esa clave ('daño', 'defensa', 'parry'...).
  - `mult_tipo_equipados(items, tipo)` (l. 1355): +20% por cada objeto de ese tipo que lleve el pokemon que pelea (Carbon para fuego...).
- **Mundos**
- `armar_mundos()` (l. 1371): Las eras del juego (una por cada Regi), sus objetos, sus piezas armadas, el clima y el plan de salas de una partida.
  - `sol(hora)` (l. 1405): Donde esta el sol: (altura de 0 a 1, hacia donde caen las sombras (dx, dy)). De noche la altura es 0. A la mañana las
  - `momento(hora)` (l. 1414): 'noche', 'mañana', 'dia' o 'tarde' segun la hora (minutos del dia).
  - `texto_hora(hora)` (l. 1419): La hora como en un reloj de 24 h: '07:05'.
  - `luz(hora)` (l. 1425): El color con el que se tiñe la pantalla a esa hora (blanco de dia, azul de noche, rosado al amanecer, naranja al atardecer).
  - `_pesos_hora(pesos, hora)` (l. 1435): Los pesos de los climas con lo que suma o resta la hora.
  - `clima_refugio(hora, dia)` (l. 1442): El clima del refugio: el mismo durante un rato (cambia cada 3 horas del juego) y segun la hora.
  - `planificar(azar)` (l. 1780): Lista de listas de tipos de sala (una por era). La tienda nunca cae en un jefe.
  - `clima_inicial(azar, era, hora)` (l. 1804): Clima al azar segun lo comun que es en la era (y la hora).
  - `siguiente_clima(azar, era, actual, hora)` (l. 1810): Clima de la sala que viene: casi siempre sigue igual o pasa a uno vecino, segun lo que es comun en la era y la hora
  - `nuevo_recorrido(semilla)` (l. 1821): Estado de una partida: el plan entero, en que sala estas y el clima que viene arrastrando.
  - `tipo_sala(rec, era, sala)` (l. 1828): Que hay en una sala del plan: 'combate', 'tienda', 'subjefe', 'jefe', 'regi' o 'final'.
  - `salas_de(rec, era)` (l. 1833): Cuantas salas tiene una era.
  - `siguiente(rec)` (l. 1838): (era, sala) de la sala que viene, o None si la actual es la ultima.
  - `avanzar(rec, hora)` (l. 1845): Pasa a la sala siguiente y le elige el clima segun la hora (si cambia de era, el clima arranca de nuevo).
  - `ir_a(rec, era, sala, hora)` (l. 1855): Salto directo (menu debug F2).
  - `destinos_siguientes(rec, azar)` (l. 1861): Lo que hay detras de cada puerta: variantes distintas si la que viene es de combate, una sola si es especial.
  - `subjefe_de(era, sala)` (l. 1878): El subjefe de esa sala de la era (sala desde 0): el primero en la sala 10 y el segundo en la 20.
  - `jefe_de(era, tipo, sala)` (l. 1885): Pokemon que pelea en una sala de subjefe (segun la sala), de jefe, de Regi o la final.
  - `etiqueta_destino(destino)` (l. 1892): Texto del cartel arriba de una puerta.
  - `escala(era, sala)` (l. 1908): Cuanto mas fuertes son los enemigos segun por donde vas.

### `modos.py` (239 líneas)

> modos.py - Los textos y numeros de todo lo que no es el viaje: el tutorial de la isla, el boss rush, la sala de los titanes,
> los minijuegos del refugio, las charlas de tus amigos y las misiones del tablon.
> La logica esta en main.py (armar_modos); aca solo estan los datos, para poder cambiarlos sin tocar el juego.

- **Tus amigos en el refugio**
- **Escenas (llegada a la era, jefes, fin de era)**
- **Caminos entre salas**
- **Tutorial (la isla de practica de Celebi)**
- **Boss rush**
- **Los titanes (los jefes que ya derrotaste, en el refugio)**
- **Minijuegos del refugio**
- **Charlas de tus amigos en el refugio**
- **Lo que te aconseja Celebi en el refugio (segun cuantas eras derrotaste)**
- **Misiones del tablon**

### `mundo.py` (3964 líneas)

> mundo.py - La sala donde se pelea: como se genera, lo que pasa adentro y las particulas.
>
>     generacion   salas procedurales (combate, tienda, arena de jefe)
>     entorno      terrenos que reaccionan, objetos que se rompen, maquinas y clima
>     efectos      particulas y la transicion al entrar o salir de una sala
>
>     from mundo import generacion, entorno, efectos

- **Generacion**
- `armar_generacion()` (l. 24): Generacion procedural de salas (estilo Hades): combate, tienda y arena de jefe.
  - `crear_escenario(columnas, filas, tam)` (l. 73): Rect del tamaño total de una sala (columnas x filas casillas).
  - `crear_area(escenario, tam)` (l. 78): Zona por donde se puede caminar (sin el borde de paredes).
  - `_elegir(azar, pesos, defecto)` (l. 83): Elige una clave de un diccionario {opcion: peso}.
- **Puertas y zonas libres**
  - `_casillas_puerta(lado, columnas, filas)` (l. 91): Las 3 casillas del borde que ocupa la puerta de un lado.
  - `_frente(lado, columnas, filas, profundidad)` (l. 100): Casillas de adentro justo en frente de una puerta.
  - `_adentro_de_puerta(lado, columnas, filas)` (l. 106): Primera casilla de adentro en frente del medio de una puerta.
  - `_zonas_libres(columnas, filas, lados, radio_centro)` (l. 112): El centro y el frente de las puertas.
  - `_matriz_base(columnas, filas, entrada, salidas)` (l. 120): Borde de paredes, piso adentro, la entrada cerrada y las salidas.
  - `_adentro(m, f, c)` (l. 130): Si (f, c) esta adentro de la matriz.
  - `_espejos(f, c, sim, filas, columnas)` (l. 135): La casilla y sus copias espejadas segun la simetria.
- **1. silueta**
  - `_silueta(m, azar, forma, libres, sim)` (l. 146): Le da forma a la sala tapando con pared lo que queda afuera.
  - `_pasillos(m, azar, libres)` (l. 201): Caminos serpenteantes de 3 de ancho desde cada puerta al centro (para que la cueva nunca quede cerrada).
- **3. especiales**
  - `_rio(m, azar, libres, sim)` (l. 221): Rio de 2 casillas que serpentea de pared a pared, con puentes y una cascada donde nace.
  - `_laguna(m, azar, libres, sim)` (l. 245): Laguna redondeada lejos del centro.
  - `_foso(m, azar, libres, sim)` (l. 260): Anillo de agua alrededor del centro con un puente hacia cada lado.
  - `_costa(m, azar, libres, sim)` (l. 271): Franja de agua de 2 casillas pegada a una pared (mar, muelle), con hueco en las puertas.
  - `_lineas(m, azar, libres, sim, terreno_de, cantidad, largo)` (l. 281): Tramos rectos (cintas transportadoras, cables).
  - `_cintas(m, azar, libres, sim)` (l. 292): Fabrica: lineas de cintas transportadoras en una misma direccion.
    - `una(azar)` (l. 294): Una cinta transportadora al azar (dirección y terreno).
  - `_cables(m, azar, libres, sim)` (l. 302): Central electrica: lineas de cables en el piso.
  - `_agregar_paredes(m, azar, libres, sim, segmentos)` (l. 310): Tramos de pared de 1 x N casillas, separados del borde y entre si por una casilla.
- **4. terreno**
  - `_mancha(m, azar, terreno, tam, libres, sim)` (l. 330): Mancha organica: crece al azar desde una casilla y despues se suaviza (se rellenan huecos y se sacan puntas).
  - `_poner_maquina(m, azar, maquina, libres, sim)` (l. 354): Cascadas y hornos van pegados a una pared (la cascada con su laguito abajo); el resto sueltas en el piso.
- **Objetos**
  - `crear_objeto(nombre, centro, celdas)` (l. 386): Un objeto listo para usar en el juego (vida, rect, material...).
  - `_celdas_de(nombre, centro, tam)` (l. 395): Casillas que tapa un objeto puesto en ese centro.
  - `_espejo_punto(x, y, sim, ancho, alto)` (l. 402): Los puntos espejados de (x, y) segun la simetria de la sala (para poner objetos espejados).
  - `_intentar_objeto(est, nombre, x, y, espejar)` (l. 411): Pone el objeto (y sus copias espejadas) si entra: piso firme, fuera de zonas libres y sin pisar otro objeto.
- **6. piezas**
  - `_girar(mapa, azar)` (l. 431): Rota y espeja una pieza al azar.
  - `_poner_pieza(est, azar, nombre)` (l. 438): Busca un lugar donde entre la pieza entera y la pone (con sus copias si la sala es simetrica).
- **7 y 8. cobertura y sueltos (Poisson)**
  - `_poisson(est, azar, nombres, cantidad, separacion, radio_min, radio_max)` (l. 477): Reparte objetos sin que queden pegados entre si (muestreo de Poisson por rechazo), en un anillo alrededor del centro.
- **9. validacion**
  - `bloqueadas(m, objetos)` (l. 492): Casillas por las que no se puede caminar (terreno que bloquea u objeto solido).
  - `_alcanzables(m, objetos, inicio, malas)` (l. 500): Casillas a las que se llega caminando desde inicio.
  - `_camino(m, malas, desde, hasta)` (l. 512): Camino mas corto entre dos casillas (BFS), o None.
  - `_ancho_ok(m, malas, desde, metas)` (l. 526): Se llega a cada meta con un camino de 2 casillas de ancho (nada de pasadizos de una casilla en el camino principal).
  - `_validar(est, entrada, salidas)` (l. 540): Arregla y chequea la sala. Devuelve el puntaje (o None si no sirve).
- **Armado**
  - `_rect_puerta(lado, columnas, filas, tam)` (l. 585): Rect en pixeles de la puerta de ese lado (3 casillas en el medio de la pared).
  - `rectangulos(m, condicion, tam)` (l. 593): Junta en rectangulos las casillas que cumplen condicion(terreno).
  - `_armar(m, objetos, tam, entrada, salidas, extra)` (l. 609): Diccionario final de la sala.
  - `_candidata(var, entrada, salidas, azar, columnas, filas, tam, radio_centro)` (l. 624): Una sala armada capa por capa (sin validar).
  - `_generar(var, entrada, salidas, azar, columnas, filas, tam, radio_centro)` (l. 652): Genera varias candidatas validas y se queda con la de mejor puntaje.
  - `generar_sala(era, variante, entrada, salidas, semilla)` (l. 667): Sala de combate de una era con la variante elegida en la puerta.
  - `generar_pasillo(era, entrada, salidas, semilla)` (l. 680): Camino tranquilo entre dos salas: largo y angosto (para el lado al que vas), con el piso, las manchas y los adornos de una
  - `generar_arena(era, salidas, semilla, tipo, datos)` (l. 694): Arena del jefe o del Regi: centro grande y libre, pocas cosas en los costados. La era puede pedir otro tamaño ('tamaño': (columnas, filas)).
- **Arenas ya dibujadas (assets/mundo/arenas/<era>_<tipo>.png + .json, las arma 'python herramientas.py arenas')**
  - `_arena_pmd(clave)` (l. 709): Los datos de una arena dibujada ({'k', 'piso', 'brasas', 'imagen': el dibujo ya agrandado}) o None si no esta.
  - `_arena_dibujada(era, salidas, azar, tipo, datos)` (l. 723): La arena de un jefe sobre un 'Dungeon Boss Room' del PMD: el dibujo entero es el fondo, la plataforma (el poligono medido) es
    - `borde(lado)` (l. 741): La ultima casilla de piso yendo desde el medio hacia ese lado.
  - `generar_tienda(era, salidas, semilla)` (l. 787): La tienda: un salon grande (como 3 salas de ancho) partido en 3 habitaciones por paredes con un paso en el medio.
- **El refugio de Celebi (el hall): plaza, barrio y habitaciones**
  - `_adentro_poligono(x, y, puntos)` (l. 876): Si un punto está adentro de un polígono (el piso de las arenas dibujadas).
  - `generar_habitacion(nombre, era, choza)` (l. 886): Una habitacion del refugio con su fondo del PMD agrandado x2. El piso es el poligono medido; lo demas, pared invisible.
    - `a_mundo(x, y)` (l. 900): Pasa un punto de la imagen de la habitación a coordenadas de la sala.
  - `generar_plaza(era, estilo, semilla)` (l. 926): La plaza del refugio (el plano): el portal arriba al medio con decoracion de la era a los costados, el patiecito de arriba a
    - `camino(f0, c0, f1, c1, ancho_c)` (l. 941): Pinta un camino de piso entre dos casillas.
    - `obj(nombre, x, y, color, sprite)` (l. 971): Crea un objeto y lo agrega a la sala.
    - `choza(parcela, zona, titulo, color, c_puerta, f_arriba, f_calle)` (l. 977): Una choza con la puerta en la columna c_puerta, la parte de arriba en la fila f_arriba y su caminito hasta la fila f_calle.
  - `_barrio_dibujado(era, estilo, semilla)` (l. 1041): El barrio de antes (si faltan las chozas del PMD): una calle con casas. La tuya, la tiendita de Celebi (adentro, el bazar) y las de tus amigos (todavia cerradas).
- **El barrio con las chozas del Red Rescue Team (assets/mundo/casas, las arma 'python herramientas.py casas')**
  - `_imagen_casa(nombre)` (l. 1081): Imagen de assets/mundo/casas/<nombre>.png (None si no esta).
  - `_tope(rect, tam)` (l. 1093): Un objeto que no se ve y no deja pasar (lo que no se pisa de una parcela).
  - `_poner_parcela(objetos, nombre, cx, y, tam, k)` (l. 1100): Pone la choza 'nombre' con su patio (el dibujo del PMD agrandado x k) con la puerta en cx y la parte de arriba en y. Del patio
  - `choza_de(tipos)` (l. 1116): La choza que le toca a un pokemon con esos tipos (None si no hay chozas).
  - `_habitacion_choza(choza)` (l. 1123): Datos de 'Tu casa' cuando es una choza del PMD por dentro (como una entrada de HABITACIONES). El piso es redondo: sale del tamaño del dibujo.
  - `_pieza_aldea(nombre)` (l. 1135): Una pieza suelta de la aldea (arbol, tocon, cerca, flor...) de assets/mundo/objetos, o None. Las recorta: python herramientas.py aldea.
  - `_flor_animada(nombre, x, y, k)` (l. 1144): Una flor del PMD que se mueve (va y vuelve: cuadros 1-2-3-4-3-2), para la lista 'animados' de la sala. None si falta la tira.
  - `generar_barrio(era, estilo, semilla, choza)` (l. 1160): El barrio: una fila de jardines con chozas del Red Rescue Team y la calle de arena por delante. La tuya (la choza del tipo de tu
  - `generar_minijuegos(era, estilo, semilla)` (l. 1253): La sala de los minijuegos: una cancha de pasto con tres carteles (contrarreloj, supervivencia y lluvia de monedas).
  - `generar_titanes(era)` (l. 1275): La sala de los titanes: un salon largo del Origen con un pedestal para cada jefe (los que ya derrotaste estan ahi parados).
  - `generar_isla(semilla)` (l. 1293): La isla de practica de Celebi (el tutorial): pasto en el medio, una vuelta de arena y el mar alrededor. Al oeste el claro
    - `obj(nombre, c, f)` (l. 1314): Crea un objeto y lo agrega a la sala.
  - `generar_tesoro(era, salidas, semilla)` (l. 1334): Sala del tesoro: el salon de la tienda sin tendero, con tres pedestales en el medio (se elige uno de los premios).
- **Entorno**
- `armar_entorno()` (l. 1357): Lo que pasa en la sala mientras jugas: terrenos que reaccionan a los ataques, objetos que se rompen,
  - `imagen(tipo, nombre, era)` (l. 1495): Sprite de assets/mundo/<era>/<tipo>/<nombre>.png o, si no hay, de assets/mundo/<tipo>/<nombre>.png. None si no existe.
- **Tilesets del PMD (los arma: python herramientas.py tiles)**
  - `_normalizar(mascara)` (l. 1520): Saca de la mascara las esquinas que no cuentan (las que no tienen sus dos lados vecinos).
  - `capa(terreno, era, variante)` (l. 1527): Tileset de un terreno o None. Busca de lo mas especifico a lo general
  - `_calar(img, brillo, d)` (l. 1553): Los parches del PMD (agua, hielo, hierba alta...) traen pegado alrededor el piso de SU mazmorra, que no es el de la sala
    - `borde_abierto(m)` (l. 1564): Pixeles del borde de la pieza por donde ya no sigue el terreno (lados y esquinas).
  - `_con_orilla(cp, piso)` (l. 1594): El mismo tileset de agua con la orilla pintada en el tono del piso de la sala (un poco mas oscuro, como tierra mojada),
  - `_cargar_capa(ruta, terreno)` (l. 1612): Lee un tileset (.png + .json) y arma el indice mascara -> piezas. None si esta roto o vacio.
  - `_pieza(cp, mascara, f, c)` (l. 1641): (pieza, variante) del tileset para esa mascara de vecinos. Si no esta exacta, la mas parecida (primero los lados, despues las esquinas).
    - `diferencia(m2)` (l. 1646): Que tan distinta es otra mascara: pesan mas los lados que las esquinas.
  - `_pintar(sup, desde, hacia)` (l. 1659): Cambia los colores de una fila de la paleta por los de otra (como el agua del PMD). En dos pasos para no pisar colores.
  - `_tile(cp, i, variante, tam, frame, brillo)` (l. 1667): Pieza i del tileset al tamaño de la casilla, con los colores del frame de su paleta (los brillos con el magenta transparente).
  - `_mancha(cp, i, variante, tam, mascara, frame)` (l. 1683): La pieza recortada con bordes redondos del lado donde no sigue el mismo terreno (asi un parche de nieve no queda cuadrado).
  - `_mascara(m, f, c, iguales)` (l. 1699): Bits de los vecinos que son del mismo terreno (afuera de la sala cuenta como igual).
  - `_frame(ahora, cada, cantidad)` (l. 1708): Frame de una paleta que cambia cada 'cada' frames del juego original (60 por segundo).
- **Maquinas y puertas**
  - `_loop(ventana, nombre, centro, lado, ahora, ms)` (l. 1719): Dibuja un efecto de assets/efectos en loop centrado en 'centro'. False si no hay sprite.
  - `_llama(ventana, centro, lado, ahora, apagada)` (l. 1729): Fuego de fogatas, braseros y hornos (o un hilito de humo si esta apagado).
  - `_base_maquina(t, tam, lados)` (l. 1743): Lo que no se mueve de cada maquina (piedras, metal, troncos), dibujado una sola vez por tamaño de casilla.
  - `_cascada_pmd(ventana, t, r, ahora, lados, ent)` (l. 1805): Cascada con el agua animada del tileset del PMD de la era cayendo (se desplaza para abajo), el borde de roca con la pared
  - `_maquina(ventana, t, r, ahora, lados, ent)` (l. 1837): Una maquina en el rect r de la pantalla: la base y lo que se mueve (agua que cae, llamas, chispas, brillos).
  - `_puerta(sup, r, abierta, ahora)` (l. 1889): Una puerta en el rect r: marco de piedra y hueco oscuro. Cerrada tiene tablas y candado; con la llave late en verde.
  - `dibujar_puerta(ventana, rect, abierta, ahora)` (l. 1908): Para main: una puerta de salida en la pantalla (cerrada con tablas, o abierta y brillando si tenes la llave).
  - `_escalada(img, ancho, alto)` (l. 1913): Imagen escalada (pixel art: sin suavizar). Sin alto, mantiene la proporcion.
  - `_texto(texto, tam, color)` (l. 1921): Texto renderizado una sola vez y guardado.
  - `crear(sala, clima, ahora)` (l. 1929): Estado de la sala en juego. clima es el de la sala (en salas interiores no llega).
  - `derretir(ent, f, c)` (l. 1945): El hielo que se derrite vuelve a lo que era: si ahi habia un lago, agua; si era hielo del piso, un charco que se puede pisar
  - `_buscar_maquinas(ent)` (l. 1951): Lista (x, y, maquina) de todas las maquinas de la sala (se rehace si cambia alguna).
  - `tipos_de(entidad)` (l. 1958): El jugador tiene 'tipos' (lista), los enemigos 'tipo' (uno solo).
- **Casillas**
  - `casilla(ent, x, y)` (l. 1965): (fila, columna) de la casilla donde esta el punto (x, y).
  - `terreno_en(ent, x, y)` (l. 1970): Terreno en el punto (x, y); afuera de la sala cuenta como pared.
  - `rect_casilla(ent, f, c)` (l. 1977): Rect en pixeles de la casilla (f, c).
  - `_casillas_rect(ent, r)` (l. 1982): Casillas que toca un rect.
  - `_casillas_circulo(ent, x, y, radio)` (l. 1989): Casillas que toca un circulo.
  - `cambiar(ent, f, c, nuevo)` (l. 2002): Cambia el terreno de una casilla. No pone algo que bloquee debajo de alguien (lo dejaria trabado).
- **Choques**
  - `solidos(ent, tipos)` (l. 2015): Rectangulos que no puede atravesar alguien de esos tipos (el agua no frena a los de agua, los fantasma pasan los objetos...).
  - `solidos_proyectil(ent)` (l. 2027): Lo que frena un proyectil: paredes, maquinas y objetos (el agua y la lava no).
  - `destructibles(ent)` (l. 2036): Objetos que se pueden romper (se suman a los objetivos de los ataques). En el refugio ninguno.
  - `mover(ent, rect, dx, dy, tipos)` (l. 2042): Mueve un rect frenando contra lo solido para esos tipos.
  - `orilla(ent, rect, tipos)` (l. 2050): Si alguien de esos tipos quedo adentro de algo que no puede pisar (cambiaste a uno que no nada en medio del agua),
  - `punto_libre(ent, azar, lejos, distancia)` (l. 2068): Centro de una casilla alcanzable, pisable y sin objetos (para hacer aparecer enemigos o jefes).
- **Efectos sobre pokemon**
  - `_sumar(ef, nuevos)` (l. 2081): Junta efectos: los multiplicadores se multiplican, los empujes se suman y lo demas se queda con el primero.
  - `_elegir(tabla, tipos, con_todos)` (l. 2090): Efectos de una tabla para esos tipos. Si es doble tipo se juntan, y el daño por tick es el menor de los dos.
  - `efectos_de(ent, tipos, rect)` (l. 2101): Todo lo que el entorno le hace a un pokemon parado en rect: terreno, maquinas cerca, agua electrificada y clima.
  - `deteccion(ent, jugador)` (l. 2122): Multiplicador del rango con que te ven los enemigos (escondido en hierba/sombra, niebla).
  - `mult_clima(ent, tipo)` (l. 2128): Cuanto potencia (o debilita) el clima de la sala a un tipo de ataque.
- **Reacciones a ataques**
  - `reaccionar(ent, x, y, radio, tipo, ahora)` (l. 2136): Un ataque de ese tipo toco el circulo (x, y, radio): congela agua, quema hierba, electrifica, etc.
  - `reaccionar_linea(ent, x0, y0, x1, y1, radio, tipo, ahora)` (l. 2148): Igual que reaccionar pero a lo largo de un golpe cuerpo a cuerpo.
  - `_hacer(ent, accion, f, c, ahora)` (l. 2155): Aplica la reaccion de un terreno a un ataque (convertir, electrificar, encender, apagar, invertir cintas, generadores).
  - `electrificar(ent, f, c, ahora)` (l. 2176): Electrifica toda el agua (y cables) conectada a esa casilla por unos segundos.
  - `vaciar_alrededor(ent, centro, libre, x, y, radio)` (l. 2189): Piso y paredes se vuelven vacio (toda la sala, o solo el circulo x, y, radio) menos un circulo de piso en el medio (centro, libre).
  - `congelar_linea(ent, a, b, radio)` (l. 2205): El rayo hielo de Regice deja escarcha (resbala) a lo largo de su camino.
  - `poner_objeto(ent, nombre, centro, evitar)` (l. 2213): Pone un objeto en la sala si entra (piso libre, lejos de las puertas y sin pisar a nadie). Devuelve el objeto o None.
  - `poner_barrera(ent, nombre, rect)` (l. 2228): Pared fina de un jefe (Jaula Voltio) con el tamaño exacto de rect. No tapa casillas y no la dibuja el entorno.
  - `sacar_de_regi(ent)` (l. 2237): Cuando cae el Regi se van sus muros, rocas y torres.
  - `armar_torre(ent, columnas, filas, fila0)` (l. 2243): Regidrago te lleva arriba de una torre: queda un rectangulo gris en el medio y todo lo demas es vacio. Devuelve el rectangulo.
  - `desarmar_torre(ent)` (l. 2255): Se rompe la torre: vuelve la sala como estaba.
  - `armar_plataforma(ent, es_piso, protegido)` (l. 2264): Arceus Beta cambia la arena: donde es_piso(f, c) queda piso y todo lo demas se vuelve vacio (las puertas no se tocan).
  - `cerrar_vacios(ent)` (l. 2284): El piso vuelve a donde habia vacios (y las paredes que se habian vuelto vacio vuelven a ser pared).
  - `encender(ent, f, c, ahora)` (l. 2294): Prende fuego una casilla que puede arder (hierba, aceite, suelo...) por un rato.
  - `explotar(ent, x, y, radio, daño, tipo, al_jugador, efecto, clase)` (l. 2300): Encola una explosion: se aplica en actualizar() (asi una explosion puede romper otro barril y encadenar).
- **Objetos**
  - `dañar_objeto(ent, obj, datos, direccion, ahora)` (l. 2307): Un ataque le pega a un objeto: daño segun material y tipo, empujes, chispas en el metal...
  - `_mult_material(material, tipo)` (l. 2327): Multiplicador de daño de un tipo de ataque contra un material (la madera arde, el hielo se rompe con fuego...).
  - `romper(ent, obj, tipo)` (l. 2333): Saca el objeto, suelta monedas a veces, explota si es explosivo y deja su terreno (charco, aceite, toxico...).
  - `_actualizar_empujados(ent, ctx, ahora)` (l. 2351): Objetos deslizandose: chocan con paredes, otros objetos y enemigos (les pegan). Al agua se hunden.
- **Clima**
  - `iniciar_clima(ent, clave, ahora, duracion)` (l. 2391): Clima temporal (de un movimiento o de un jefe). Sin duracion queda toda la sala. Adentro no llueve.
  - `al_usar_movimiento(ent, nombre, ahora)` (l. 2399): Algunos movimientos cambian el clima (lluvia, sol, granizo...).
  - `_casilla_al_azar(ent, terrenos)` (l. 2404): Una casilla al azar de esos terrenos (o None si no encontro en 25 intentos).
  - `_actualizar_clima(ent, ctx, ahora)` (l. 2413): Una vez por segundo: la lluvia hace charcos y apaga el fuego, el sol derrite y seca, el granizo congela, caen rayos.
- **Cada frame**
  - `actualizar(ent, ctx, ahora)` (l. 2455): ctx = {'jugador': j, 'enemigos': [...], 'dañar_jugador': f(daño, tipo), 'dañar_enemigo': f(enemigo, daño, tipo, efecto)}
- **Dibujo**
  - `_aclarar(color, k)` (l. 2516): Color mas claro (k > 0) o mas oscuro (k < 0).
  - `_dibujar_textura(fondo, t, r, f, c)` (l. 2521): Dibujito simple para que cada terreno se distinga del piso (hasta que lleguen los sprites).
  - `_poner_tile(ent, fondo, cp, terreno, f, c, r)` (l. 2555): Pieza del tileset segun los vecinos. Si el terreno se anima (agua del PMD) queda anotado para redibujarlo cada frame.
  - `_alfombra(ancho, alto)` (l. 2573): Alfombra roja del Secret Bazaar del tamaño pedido (pixeles al doble): bordes y esquinas recortados de la hoja y rombos
  - `_dibujar_charcos(fondo, celdas, tam)` (l. 2596): Charcos: agua quieta y semitransparente sobre el piso de la era (se ve el piso a traves), con los bordes redondeados,
  - `_armar_fondo(ent)` (l. 2622): Piso, terrenos, paredes y maquinas en una imagen (se rehace solo cuando cambia el terreno).
  - `_chamuscado(tam, semilla)` (l. 2723): Mancha de piso quemado para multiplicar sobre el piso: oscura en el medio y sin bordes rectos (una de 4 formas).
  - `_resplandor(lado)` (l. 2739): Circulo naranja que se apaga hacia afuera, para sumarlo sobre lo que arde (se arma una vez por tamaño).
  - `_tono(color, k)` (l. 2750): El color aclarado (k > 1) u oscurecido (k < 1).
  - `_dibujar_mostrador(ventana, r, color, franja)` (l. 2755): Mostrador de la tienda: el frente de madera, la tela del color del tendero colgando con flecos y la tapa clara arriba.
  - `_dibujar_edificio(ventana, r, color, casa)` (l. 2774): Edificio o casa del refugio: paredes claras con vigas, techo del color del lugar, ventanas y la puerta.
  - `_dibujar_tablon(ventana, r, color)` (l. 2800): El tablón de madera dibujado (solo si falta su sprite).
  - `_dibujar_telescopio(ventana, r, color)` (l. 2811): El telescopio dibujado (solo si falta su sprite).
  - `_dibujar_banco(ventana, r, color)` (l. 2820): El banco dibujado (solo si falta su sprite).
  - `_dibujar_cartel(ventana, r, color)` (l. 2828): El cartel dibujado (solo si falta su sprite).
  - `_dibujar_estante(ventana, r, color)` (l. 2836): Estante de la tienda: madera con dos tablas, sombra abajo y patitas (las cosas van arriba, ver dibujar_tienda).
  - `_dibujar_mesa(ventana, r, color)` (l. 2850): Mesa de los destacados: patas de madera y un mantel del color del tendero con borde claro.
  - `_sprite_de(d, img, r)` (l. 2861): El dibujo de un objeto al tamaño que va y donde se pone: del ancho del objeto y apoyado abajo; los que tienen 'escala' (el arbol
  - `_blanca(sprite)` (l. 2871): La silueta del dibujo en blanco suave (para el destello cuando le pegan), guardada.
  - `dibujar_copas(ent, ventana, cx, cy, rects)` (l. 2878): Despues de dibujar a los pokemon: la copa de cada arbol se vuelve a dibujar medio transparente arriba de los que estan parados
  - `_brillo_pasto(ent, ventana, cx, cy, ahora, vista)` (l. 2897): Gotitas de rocio que titilan en las matas de hierba (sobre todo a la mañana). Las casillas de hierba se buscan una vez por
  - `_brillo_suave(radio, color)` (l. 2921): Un circulo de color que se apaga hacia el borde, para sumar encima (se arma una vez por tamaño y color).
- **El sol: el pasto que brilla, las sombras de los pokemon, los rayos y el agua que destella**
  - `sol_de(ent)` (l. 2955): El sol en la sala ahora: (fuerza de 0 a 1, altura de 0 a 1, hacia donde caen las sombras (dx, dy), color de la luz: rosado al
  - `_capa(nombre, tam)` (l. 2965): Una superficie de trabajo del tamaño de la pantalla (se arma una vez y se reusa).
  - `_solido(nombre, color, tam)` (l. 2972): Una superficie de un solo color para multiplicar (blit con BLEND_RGB_MULT es rapido; fill con special_flags, no).
  - `teñir(ventana, color)` (l. 2982): Multiplica toda la pantalla por un color (la luz del dia).
  - `_canales(sup)` (l. 2987): Dos copias de la superficie con los canales de color corridos, moviendo sus bytes (la forma de mezclar canales sin numpy)
  - `_por(sup, veces)` (l. 2994): La superficie multiplicada por 2, 4, 8... (sumandola a si misma).
  - `_mezclar(sup, color, banderas, lleno)` (l. 3000): sup mezclada con un color parejo (fill con special_flags es lento: se usa una superficie llena y blit).
  - `_armar_luz_pasto(ent)` (l. 3006): Lo que brilla del pasto al sol, pixel por pixel pero todo de una (mezclando superficies): solo lo verde (cuanto mas verde
  - `_banda()` (l. 3040): La franja de luz que pasa con el viento: diagonales que se repiten (la textura empalma sola al repetirse).
  - `_manchas()` (l. 3052): Manchas de sol que se cuelan entre las hojas: las sombras de nubes del Red Rescue Team al reves (luz), bien suaves.
  - `_luz_del_sol(ent, ventana, cx, cy, ahora)` (l. 3065): El sol en el pasto: brillan las puntas de las hojas (siempre un poco), mas cuando pasa la franja del viento y adentro de las
  - `_mancha_sombra(largo, grueso, angulo, alfa)` (l. 3084): Una sombra suave (elipse que se apaga hacia el borde) de ese largo y grosor, girada; se arma una vez por medida.
  - `dibujar_sombras(ent, ventana, cx, cy, cuerpos)` (l. 3104): La sombra de cada pokemon: una suave bajo los pies y, afuera con sol, la que tira el sol (larga a la mañana y a la tarde,
  - `_textura_rayos(tam, angulo, semilla)` (l. 3127): Rayos de sol que bajan en diagonal desde el lado del sol, suaves (se dibujan chicos y se agrandan suavizados) y que se
  - `_rayos(ent, ventana, ahora)` (l. 3151): Rayos de sol (como en un bosque): bajan en diagonal desde el lado del sol, mas cuando el sol esta bajo (a la mañana y a la
  - `_destellos_agua(ent, ventana, cx, cy, ahora, vista)` (l. 3169): Con sol, el agua destella: la estrellita del PMD aparece y se apaga sobre el agua, cada una a su tiempo (mas seguido con
  - `sacudir(ent, x, y, ahora)` (l. 3190): Alguien pasa por la hierba: la mata se sacude (como el pasto alto de los juegos de Pokemon).
  - `_sacudidas(ent, ventana, cx, cy, ahora)` (l. 3198): Las matas que se sacuden (ver sacudir): la casilla del fondo va de lado a lado y se aquieta.
  - `dibujar(ent, ventana, cx, cy, ahora, tipos_jugador, cuerpos)` (l. 3208): Dibuja la sala vista desde la camara (cx, cy). Las maquinas muestran su radio solo si ayudan a tus tipos. cuerpos: los pies
  - `_velo(tam, color)` (l. 3320): Superficie de un color (con transparencia) de ese tamaño, armada una vez y reusada.
  - `_reflejo(tam)` (l. 3328): Rayitas claras para sumarle al agua que no tiene paleta (se mueven de lado a lado).
  - `_particulas(cantidad, W, H, ahora, vx, vy)` (l. 3342): Posiciones de las particulas del clima en este momento: cada una arranca en un lugar fijo y avanza con el tiempo
- **El clima del Red Rescue Team (assets/clima/<efecto>/<nn>.png, los arma 'python herramientas.py clima')**
  - `_cuadros_clima(nombre)` (l. 3353): Los cuadros de assets/clima/<nombre> en orden (lista vacia si no estan: se dibuja el clima de antes, con lineas y circulos).
  - `_cuadro_clima(nombre, ahora, ms, escala, alfa)` (l. 3366): El cuadro que toca ahora, agrandado. Se agranda una sola vez por cuadro (queda guardado hasta que cambia).
  - `_embaldosar(ventana, img, dx, dy, banderas)` (l. 3379): Repite img por toda la ventana, corrida (dx, dy) pixeles (da la vuelta sola).
  - `_reflejo_sol(ventana, ahora)` (l. 3393): El destello del sol del PMD como un reflejo en la lente: cada tanto aparece de a poco, se corre despacio y se va.
  - `area_sala(ent, cx, cy, ventana)` (l. 3416): El rectangulo de la sala en la pantalla (lo de afuera es negro: ahi no nieva ni llueve).
  - `_nevar(ent, ventana, ahora, cantidad, alfa)` (l. 3421): Copos del Red Rescue Team (cada uno recortado de la hoja) cayendo de verdad sobre la sala: cada copo tiene su lugar en el piso
  - `_sombras_de_nubes(ent, ventana, ahora, alfa, velocidad)` (l. 3470): Las sombras de las nubes del PMD pasando despacio por el piso (pegadas al mundo: si caminas, quedan atras).
  - `_ambiente(ent, ventana, ahora, noche)` (l. 3479): Lo que flota en el aire cuando no hay clima fuerte: adentro (o a oscuras) polvito que brilla despacio; afuera de dia, polen
  - `_hay_brasas(ent)` (l. 3518): Si en la sala hay lava, hornos o braseros (flotan brasas en el aire). Se mira una vez por sala.
- **La luz: de noche (y en las salas a oscuras) solo se ve cerca de las pocas cosas que alumbran**
  - `a_oscuras(ent, variante, semilla, tipo)` (l. 3544): Decide (siempre igual para la misma sala) si es una sala a oscuras: solo pasa en las de combate; en las cuevas y mazmorras
  - `oscuridad_de(ent, hora_luz, tipo)` (l. 3552): Que tan oscura esta la sala ahora (0: nada, hasta 255). hora_luz: el color del dia (mundos.luz). Las salas de jefes no (tienen
  - `_sello_luz(radio)` (l. 3564): El agujero de una luz en la oscuridad: transparente en el medio y cada vez mas oscuro hasta el borde (para BLEND_RGBA_MIN).
  - `_brillo_luz(radio, color)` (l. 3581): El color de una luz para sumar encima (mas fuerte en el medio y nada en el borde).
  - `fuentes_de_luz(ent)` (l. 3596): Las luces fijas de la sala (maquinas prendidas, lava, postes...): [(x, y, radio, color, titila)] en el mundo. Se arma una vez por
  - `dibujar_oscuridad(ent, ventana, cx, cy, ahora, alfa, extra)` (l. 3608): Tapa la sala con la oscuridad y le abre agujeros de luz: las fuentes de la sala (las mas cercanas, como mucho LUZ['max_fuentes']),
  - `_luciernagas(ent, ventana, cx, cy, ahora, fuerza, cantidad)` (l. 3638): Luciernagas de la noche: puntitos verde-amarillos que vagan pegados al mundo y se prenden y se apagan (solo sobre la sala).
  - `_luciernagas_en(ent, ventana, cx, cy, ahora, fuerza, cantidad)` (l. 3645): (ayudante interno)
  - `dibujar_clima(ent, ventana, ahora, cartel)` (l. 3659): Capa del clima encima de todo y el cartelito de cuanto le queda. Usa los cuadros animados del Red Rescue Team
  - `cartel_clima(ent, ventana, ahora)` (l. 3669): El cartelito de arriba con el clima y cuanto le queda (aparte, para dibujarlo encima de la oscuridad).
  - `_clima_en_sala(ent, ventana, ahora)` (l. 3678): Las capas del clima (ver dibujar_clima).
- **Efectos**
- `armar_efectos()` (l. 3736): Particulas (golpes, cosas que se rompen, explosiones, subir de nivel...) y la transicion al entrar o salir de una sala.
  - `crear()` (l. 3752): Estado vacio de las particulas, animaciones y la transicion.
  - `_tira(nombre)` (l. 3757): Frames de assets/efectos/<nombre>.png o None.
  - `_frames(nombre, tam)` (l. 3774): Frames del efecto al tamaño pedido (se escalan una sola vez) o None.
  - `_animacion(ef, nombre, x, y, tam, velocidad)` (l. 3783): Si hay sprite del efecto lo usa. Devuelve True si lo encontro.
  - `proyectil(ventana, tipo, x, y, radio, ahora)` (l. 3791): Dibuja un proyectil animado del tipo (bola de fuego, hoja, roca...) centrado en (x, y) de la pantalla. False si no hay sprite.
  - `cura(ef, x, y)` (l. 3801): Brillos verdes al curarse.
  - `cambio(ef, x, y)` (l. 3809): Destello al cambiar de pokemon.
  - `aparecer(ef, x, y)` (l. 3814): Nubecita de BW donde aparece un enemigo.
  - `destello(ef, x, y)` (l. 3819): Estrellitas (aparece la llave, monedas).
  - `chispas(ef, x, y, color, cantidad, velocidad, vida, tam, gravedad, subir)` (l. 3824): Particulas que salen en todas direcciones desde (x, y).
  - `golpe(ef, x, y, color, tipo)` (l. 3832): Cuando un ataque le pega a algo.
  - `estrellas(ef, x, y, cantidad, radio)` (l. 3841): Estrellitas amarillas del Red Rescue Team alrededor de (x, y): la chispa de un golpe que conecta.
  - `brillos(ef, x, y, cantidad, radio)` (l. 3847): Brillitos blancos del Red Rescue Team (frenesi, hitos de la cadena de golpes).
  - `baja(ef, x, y, color, tipo)` (l. 3853): Un enemigo derrotado: un anillo de luz, el golpe de su tipo en grande, estrellas y chispas de su color para todos lados.
  - `rastro(ef, x, y, color)` (l. 3862): La colita de un proyectil: una chispa de su color que queda atras y se apaga (si ya hay muchas particulas, no).
  - `romper(ef, x, y, color)` (l. 3869): Pedazos que saltan y caen al romper un objeto.
  - `explosion(ef, x, y, radio)` (l. 3878): Explosion (animacion del PMD o chispas de fuego y humo).
  - `nivel(ef, x, y)` (l. 3885): Brillitos que suben al subir de nivel.
  - `evolucion(ef, x, y)` (l. 3893): Destello grande al evolucionar o cuando aparece Arceus Beta.
  - `corazones(ef, x, y)` (l. 3900): Un pokemon quiere unirse a tu equipo.
  - `polvo(ef, x, y)` (l. 3907): Polvito bajo los pies al correr o embestir.
  - `actualizar(ef)` (l. 3913): Avanza un frame las particulas (con gravedad y friccion) y las animaciones; borra las terminadas.
  - `dibujar(ef, ventana, cx, cy)` (l. 3922): Dibuja particulas y animaciones segun la camara.
- **Transicion de sala**
  - `transicion(ef, clase, ahora, centro, duracion)` (l. 3941): 'entrar': el negro se abre en circulo desde donde entras. 'salir': se cierra hacia la puerta.
  - `dibujar_transicion(ef, ventana, ahora)` (l. 3946): Pantalla negra con un circulo que se abre (al entrar) o se cierra (al salir) desde la puerta.

### `combate.py` (5058 líneas)

> combate.py - Los pokemon peleando: como suben de nivel y como piensan los enemigos.
>
>     progreso   niveles, experiencia, IV/EV, evoluciones y amistad
>     ia         enemigos que te buscan, atacan avisando y se cubren; jefes
>
>     from combate import progreso, ia

- **Progreso**
- `armar_progreso()` (l. 23): Niveles, experiencia, stats con IV y EV, evoluciones y amistad (pokemon que se unen a tu equipo).
  - `base(nombre, clave)` (l. 124): Stat base oficial de la especie (de la PokeAPI), o 60 si no hay datos.
  - `stat(nombre, clave, nivel, iv, ev, naturaleza)` (l. 129): Stat real como en los juegos (la naturaleza sube o baja un 10% los que no son PS).
  - `factor_naturaleza(naturaleza, clave)` (l. 135): 1.1 si la naturaleza sube ese stat, 0.9 si lo baja, 1 si no (o si no tiene).
  - `naturaleza_al_azar(azar)` (l. 141): Una de las 25 naturalezas, todas con la misma chance (como en los juegos).
  - `texto_naturaleza(naturaleza)` (l. 146): 'Alegre (+Velocidad -At. Esp.) - se amiga facil' para las fichas y las charlas.
  - `_curva(nombre)` (l. 155): Curva de crecimiento de la especie (de la PokeAPI; 'medium' si no hay datos).
  - `xp_para(nombre, nivel)` (l. 160): Experiencia total para llegar a ese nivel segun la curva de crecimiento de la especie.
  - `movs_iniciales(nombre)` (l. 170): None en cada casilla = usa el movimiento de la especie (si evoluciona, cambia solo). Una MT reemplaza la casilla.
  - `nuevo(nombre, nivel, azar)` (l. 175): Un pokemon nuevo para el equipo con IVs al azar (0 a 31).
  - `multiplicadores(m)` (l. 182): Proporcion contra el pokemon de referencia. vida/fisico/especial crecen con el nivel; defensa y velocidad solo con IV y EV.
  - `crecimiento(nombre, nivel, clave)` (l. 193): Lo mismo para enemigos (IV promedio, sin EV): cuanto mas nivel, mas vida y mas daño.
  - `xp_por_derrota(enemigo, nivel_enemigo, nivel_propio, jefe)` (l. 198): Formula de quinta generacion: se gana mas contra los de mas nivel y menos contra los debiles.
  - `ajuste_xp(nivel_propio, nivel_sala)` (l. 205): Multiplicador elastico de la experiencia: 1 si vas MARGEN_NIVEL arriba de la sala, menos si vas mas arriba, mas si vas abajo.
  - `dar_xp(m, cantidad)` (l. 210): Suma experiencia. Devuelve los niveles nuevos (cada uno da puntos de EV).
  - `progreso_nivel(m)` (l. 220): 0 a 1: cuanto falta para el proximo nivel (para la barra de experiencia).
  - `motivo_sin_ev(m, clave)` (l. 226): Por que no se puede poner un punto en ese stat (texto para mostrar) o None si se puede.
  - `gastar_punto(m, clave)` (l. 234): Pone un punto de EV en ese stat (si hay puntos y no esta al tope).
  - `_jugable(nombre)` (l. 242): Si el pokemon existe en el juego y tiene sprites (asi se puede evolucionar a el).
  - `requisitos(nombre)` (l. 247): Como evoluciona cada especie: lista de {'a', 'nivel' | 'objeto' | 'amistad'} (solo a pokemon que estan en el juego).
  - `texto_requisito(req)` (l. 268): Texto de un requisito de evolucion ('nivel 16', 'amistad 220', 'piedra trueno').
  - `evoluciones(m, objetos)` (l. 276): A que puede evolucionar ahora: los de nivel/amistad si ya llego, los de objeto si lo tenes en la mochila.
  - `forma_base(nombre)` (l. 288): La primera forma de su linea evolutiva que esta en el juego (Swampert -> Mudkip). Cada viaje nuevo arranca desde ahi.
  - `evolucionar(m, destino)` (l. 295): Cambia la especie y conserva nivel, IV, EV y las MT enseñadas.
  - `prob_unirse(enemigo, nivel_enemigo, nivel_propio, mult, naturaleza)` (l. 301): Chance de que un pokemon derrotado quiera unirse (no es capturar: se hace tu amigo).
  - `nivel_de_sala(era, sala, tipo)` (l. 310): Nivel de los enemigos: 4 a 15 en la primera era, +11 por era. Jefes un poco mas.
  - `vida_max(m)` (l. 317): Vida maxima de un miembro: la de su especie por el multiplicador de nivel, IV y EV.
- **Ia**
- `armar_ia()` (l. 329): Inteligencia de los enemigos: te buscan esquivando obstaculos, atacan de cerca o de lejos y se cubren.
  - `preparar(e, estilo)` (l. 379): Agrega al enemigo lo que necesita la ia.
- **Mapa del lugar**
  - `_pasa(ent, tipos)` (l. 391): Casillas bloqueadas para esos tipos (terreno + objetos solidos).
  - `mapa_flujo(ent, destino, tipos)` (l. 405): Mapa de Dijkstra (como en Brogue): distancia en casillas desde cada casilla hasta destino. Se guarda mientras no cambie nada.
  - `ve(ent, a, b)` (l. 421): True si no hay paredes, maquinas ni objetos entre a y b.
  - `_paso_flujo(ent, e, dist, alejarse)` (l. 426): Centro de la casilla vecina que acerca (o aleja) mas segun el mapa de flujo. Diagonal solo si no corta esquinas.
  - `_cobertura(ent, e, jugador)` (l. 440): Casilla cerca, pegada a algo solido y que el jugador no ve: para esconderse a recargar.
- **Movimiento**
  - `_mover_hacia(ent, e, punto, vel, enemigos)` (l. 459): Camina hacia un punto, separandose de los compañeros para no amontonarse.
  - `_ir_a(ent, e, destino, vel, enemigos, alejarse)` (l. 479): Va hacia destino por el camino del mapa de flujo (o derecho si lo tiene a la vista y cerca).
- **Cada frame**
  - `_atacando(enemigos)` (l. 490): Cuantos enemigos de cuerpo a cuerpo estan atacando o embistiendo ahora (para que no ataquen todos a la vez).
  - `_parametros(e, ctx)` (l. 495): Los numeros del estilo del enemigo ajustados por la era (mas apurados) y por la furia (con poca vida).
  - `_chance(p, clave, ctx)` (l. 512): Chance de una maniobra segun la era (en el modo facil y en el tutorial no hay).
  - `_esquivar_balas(e, ctx, p, ahora)` (l. 519): Si una bala tuya viene derecho hacia el y esta por llegar, a veces salta de costado.
  - `actualizar(e, ctx)` (l. 536): ctx = {'ent': entorno, 'jugador': j, 'enemigos': [...], 'ahora': ms, 'dañar_jugador': f(daño, tipo), 'era': n,
  - `_orbitar(ent, e, j, radio, vel, enemigos)` (l. 684): Da vueltas alrededor del jugador a cierta distancia (cambia de sentido si se choca o de vez en cuando).
  - `_soltar_ataque(e, ctx, p)` (l. 695): Termina el aviso: golpe (con una acometida hacia vos), disparo (rafaga apuntando adelante de donde vas) o embestida.
- **Jefes**
  - `preparar_jefe(b)` (l. 913): Pone en un jefe todos los campos que usan sus ataques (avisos, rayos, tablas, minas, torres...) y su estilo.
  - `_fase(b, cortes)` (l. 932): Fase segun la vida que le queda (cortes de mayor a menor, ej. (0.75, 0.25) -> fases 1, 2 y 3).
  - `_rastrear(b, j, ahora)` (l. 938): Guarda por donde fue pasando el jugador (para los rayos que siguen donde estabas, no donde estas).
  - `_pos_anterior(b, j, ahora, retraso)` (l. 944): Donde estaba el jugador hace 'retraso' ms.
  - `_girar_hacia(ang, quiero, maximo)` (l. 951): Gira un angulo hacia otro, como mucho 'maximo' radianes.
  - `_toca_linea(j, puntos, ancho)` (l. 957): Si el jugador esta tocando alguno de los tramos de una linea quebrada (rayos que rebotan).
  - `_trazar(ent, desde, d, largo, rebotes)` (l. 963): Camino de un rayo: sigue derecho hasta una pared y, si le quedan rebotes, rebota. Devuelve los puntos de la linea.
  - `_animar(b, nombres, ahora, duracion)` (l. 984): Le pone al jefe una animacion por un rato (la primera de 'nombres' que tenga su sprite).
  - `_dash_gigas(b, ctx)` (l. 989): Gigaimpacto: carga en linea recta hasta donde estabas; despues queda quieto recargando.
  - `_agarron(b, ctx)` (l. 1007): Agarron: te sostiene un momento y te tira para atras. Solo lastima si chocas contra una pared.
  - `actualizar_regigigas(b, ctx)` (l. 1027): Lento Inicio: los primeros 10 s esta quieto con la defensa subida y al despertar usa Terremoto.
  - `_dist_segmento(p, a, b)` (l. 1091): Distancia de un punto a un segmento (para saber si un rayo te toco).
  - `fase_arceus(b, cortes)` (l. 1099): Fase de Arceus (o de Arceus Beta) segun la vida que le queda. No vuelve atras aunque Recuperacion lo cure.
  - `_terminar(b, ahora, exclusivo)` (l. 1105): Termino un movimiento de Arceus: espera un poco antes del siguiente (y anota cuando termino Recuperacion, Velocidad Extrema o Hiperrayo).
  - `_proteger(b, ahora)` (l. 1111): Proteccion: escudo 3 s; mientras dura no se mueve, no ataca y no recibe daño.
  - `_aviso_sentencia(b, ahora, espera, mira)` (l. 1118): Marca de una Sentencia en el piso: donde cae, cuando y de que tamaño (chica en la fase 2, grande en la 3). Siempre de tipo normal.
  - `_elegir_arceus(b, ctx)` (l. 1124): Elige al azar el proximo movimiento entre los de su fase que ya esten listos.
  - `_hiperrayo_arceus(b, ctx)` (l. 1164): Hiperrayo disparando: sale de Arceus y gira despacio hacia donde estabas hace un rato (se esquiva). Al terminar recarga quieto.
  - `_extrema_arceus(b, ctx)` (l. 1179): Velocidad Extrema: embiste en linea recta muy rapido. Si choca contra una pared se frena, pero no queda aturdido.
  - `_recuperacion_arceus(b, ctx)` (l. 1197): Recuperacion: si le pegaste mientras juntaba estrellitas se corta; si aguanto los 3 s se cura un poco.
  - `_actualizar_meteoros(b, ctx)` (l. 1211): Meteoros: cada uno sale apuntando a donde estas, avisa 1 s con una sombra y cae.
  - `ondas_en_arcos(pos, ahora, cantidad, entre, dura, radio, grosor, daño, arcos, lleno, tipo)` (l. 1225): Circulos que salen de pos partidos en 'arcos' pedazos (cada uno ocupa 'lleno' de su tramo y el resto es hueco).
  - `radio_onda(o, ahora)` (l. 1234): Radio de un circulo del Vozarron (o del Psicorruido) en este momento.
  - `tramos_onda(o)` (l. 1239): (desde, hasta) en radianes de cada arco de un circulo.
  - `_toca_arco(o, p, radio, mitad)` (l. 1245): Si un punto (con su hitbox) esta sobre alguno de los arcos del circulo (no en un hueco).
  - `_actualizar_vozarron(b, ctx)` (l. 1255): Vozarron: los 3 circulos partidos en arcos se agrandan durante 5 s; cada uno te pega una sola vez si un arco te pasa por encima
  - `_vozarron(b, ahora)` (l. 1267): Los 3 circulos en arcos del Vozarron saliendo de Arceus (o de Arceus Beta).
  - `actualizar_arceus(b, ctx)` (l. 1274): Arceus: usa un movimiento por vez, elegido al azar entre los de su fase (ver MOVS_ARCEUS), con una pausa entre uno y otro.
- **Arceus Beta**
  - `pos_tabla(b, t, ahora)` (l. 1326): Donde esta una tabla de Arceus Beta: gira en ovalo alrededor de el.
  - `zona_circulo(centro, radio)` (l. 1334): Zona redonda (fase 1).
  - `zona_poligono(vertices)` (l. 1340): Zona con forma de poligono (el triangulo). 'radio' es mas o menos el de un circulo del mismo tamaño (para medir los ataques).
  - `_lados(vertices)` (l. 1347): Los lados de un poligono: pares de vertices seguidos (el ultimo con el primero).
  - `_en_poligono(p, vertices)` (l. 1352): Si un punto esta adentro de un poligono (aunque sea concavo, como la estrella de la Llamarada).
  - `dentro_zona(z, p, margen)` (l. 1361): Si el punto esta adentro de la zona, a por lo menos 'margen' pixeles del borde.
  - `ajustar_zona(z, p, margen)` (l. 1367): El punto de la zona mas cerca de p (yendo hacia el centro), a 'margen' del borde.
  - `caja_zona(z)` (l. 1383): (x0, y0, x1, y1) del rectangulo que encierra la zona.
  - `punto_zona(z, margen)` (l. 1389): Un punto al azar adentro de la zona.
  - `esquinas_zona(z)` (l. 1398): Las esquinas de la zona: las puntas del triangulo (un poco hacia adentro) o 4 puntos en diagonal del circulo.
  - `afuera_zona(z, distancia)` (l. 1406): Un punto al azar sobre el vacio, a 'distancia' pixeles del borde de la zona.
  - `cruzar_zona(z, por, ang, extra)` (l. 1422): Los dos extremos de una recta que pasa por 'por' con angulo 'ang' y atraviesa toda la zona (sobresale 'extra' pixeles).
  - `_mas_cerca_primero(b, a, c)` (l. 1435): Los dos extremos de una recta con el mas cercano a Arceus Beta primero (por ahi entra).
  - `_linea_por(p, ang, largo)` (l. 1441): Los extremos de una linea de 'largo' pixeles centrada en p.
  - `_limitar(ent, b, p)` (l. 1447): El punto mas cercano a p donde Arceus Beta entra entero en la sala (sin meterse en las paredes del borde).
  - `_poner_beta(b, ctx, pos)` (l. 1454): Arceus Beta aparece en pos de golpe (teletransporte), con un destello donde estaba y donde aparece.
  - `_centro_casilla(ent, p)` (l. 1462): Centro de la casilla donde cae p.
- **Golpes de Arceus Beta**
  - `_pegar(b, ctx, daño, tipo, efecto, cura)` (l. 1470): Le pega al jugador y devuelve cuanta vida le saco (nada si lo esquivo). Con 'cura' Arceus Beta se cura esa parte del daño;
  - `_golpe(jefe, ahora, forma, aviso, tipo, daño, dura, tick, **extra)` (l. 1486): Ataque de Arceus Beta en el piso: se avisa 'aviso' ms y despues pega durante 'dura' ms (una vez, o cada 'tick' ms si tiene).
  - `_toca(g, j)` (l. 1497): Si el jugador (con su hitbox) esta adentro de un golpe.
  - `_centro_golpe(g)` (l. 1509): El medio de un golpe (para el temblor).
  - `_actualizar_golpes(b, ctx)` (l. 1517): Los golpes en el piso: el Lanzallamas gira, la Fuerza Lunar te sigue, y cada uno pega si estas adentro cuando le toca.
  - `_arena(b, g, ctx)` (l. 1545): Bucle Arena: si pisas el circulo quedas trabado hasta que apretas interactuar (o hasta que se va la arena).
  - `salir_arena(j, ahora)` (l. 1553): Apretaste interactuar: salis de la arena movediza (y por un rato no te vuelve a atrapar). True si estabas atrapado.
  - `_actualizar_cargas(b, ctx)` (l. 1560): Hojas, rocas y bolas que esperan al lado de Arceus Beta: cuando les toca salen hacia donde estas en ese momento.
  - `_actualizar_balas(b, ctx)` (l. 1571): Ataques propios de Arceus Beta que viajan: agujas (Picotazo Veneno), rafagas (Tornado) y huesos que van y vuelven (Huesomerang).
  - `_soltar_en_piso(ent, j, z)` (l. 1598): Si el jugador quedo sobre el vacio (o adentro de algo solido), lo corre hacia el centro de la zona hasta que este en el piso.
  - `_actualizar_lanzado(b, ctx)` (l. 1610): Psiquico: te lleva por el aire hasta el lado contrario de la zona y te tira contra el piso.
  - `_actualizar_viento(b, ctx)` (l. 1623): Tornado: durante un rato el viento te empuja para donde pasaron las rafagas.
  - `_abrir_grieta(b, ctx, vertical)` (l. 1634): Abrecaminos: una franja de casillas que pasa por el medio de la zona se vuelve vacio por un rato y la parte en dos.
  - `_cerrar_grieta(b, ent)` (l. 1660): Se cierra la grieta del Abrecaminos: vuelve el piso.
- **Tablas**
  - `_cambiar_tabla(b, ahora, anim)` (l. 1670): Se saca la tabla puesta y se pone otra al azar. 'anim': ms de la animacion (0 = al instante, sin animacion).
  - `_actualizar_cambio(b, ahora)` (l. 1680): Animacion de cambio de tabla: la primera mitad se saca la puesta y la segunda se pone la nueva (ahi cambia de tipo).
  - `tablas_fuera(b, ahora)` (l. 1688): Las tablas que no estan girando: la puesta y la que se esta sacando o poniendo.
- **Guion: los pasos de cada movimiento**
  - `_paso(clase, **datos)` (l. 1700): Un paso del guion de un jefe (la IA los va haciendo en orden).
  - `_ir_casa(vel)` (l. 1705): Paso: Arceus Beta vuelve volando a su lugar.
  - `_correr_guion(b, ctx)` (l. 1710): Hace los pasos del movimiento en curso. Devuelve True mientras quede guion.
  - `_avanzar_beta(b, ctx, p)` (l. 1735): Arceus Beta vuela hacia el destino del paso (le pega al jugador si el paso tiene golpe). True al llegar.
  - `_bote(b, ctx, p)` (l. 1759): Bote: salta fuera de la pantalla, su sombra te sigue (por donde estabas hace un rato), se frena un momento y cae. True al caer.
- **Movimientos de cada tabla**
  - `_espera(b, ms)` (l. 1784): Agrega una espera al guion del jefe.
  - `_mov_vozarron(b, ctx)` (l. 1788): Neutra - Vozarron: igual que el de Arceus (circulos partidos en arcos).
    - `salen(b, ctx)` (l. 1793): Suelta las ondas del ataque (paso del guion).
  - `_mov_meteoros(b, ctx)` (l. 1801): Neutra - Meteoros: igual que los de Arceus (7 meteoritos donde estas, avisados con una sombra).
  - `_mov_gigaimpacto(b, ctx)` (l. 1809): Neutra - Gigaimpacto: cruza la zona de un lado al otro 3 veces (cada vez por donde estas) y vuelve a su lugar.
    - `pasar(b, ctx)` (l. 1812): Hacia dónde cruza la arena la embestida (paso del guion).
  - `_mov_lanzallamas(b, ctx)` (l. 1821): Llama - Lanzallamas: una linea de fuego que sale de el y gira de una punta a la otra de la zona, larga hasta la mitad de la zona.
  - `_mov_llamarada(b, ctx)` (l. 1836): Llama - Llamarada: una estrella de fuego de 5 puntas en el medio de la zona (entre las puntas se esta a salvo).
  - `_mov_colmillo_fuego(b, ctx)` (l. 1848): Llama - Colmillo Igneo: una mordida grande de fuego en la esquina de la zona que te queda mas cerca.
  - `_mov_electrocañon(b, ctx)` (l. 1857): Trueno - Electrocañon: un rayo electrico horizontal o vertical que cruza la zona por donde estas.
  - `_mov_bola_voltio(b, ctx)` (l. 1866): Trueno - Bola Voltio: 3 bolas electricas lentas (no tan grandes) que salen de a una hacia donde estas.
  - `_mov_voltio_cambio(b, ctx)` (l. 1876): Trueno - Voltio Cambio: un rayo rapido donde estas (avisado medio segundo) y enseguida cambia de tabla.
  - `_mov_hoja_afilada(b, ctx)` (l. 1883): Pradal - Hoja Afilada: 10 hojas (5 de cada lado) que salen de a 2 hacia donde estas en ese momento.
  - `_mov_abrecaminos(b, ctx)` (l. 1894): Pradal - Abrecaminos: pasa volando por una linea que cruza el medio de la zona y la zona queda partida en dos un rato.
  - `_mov_asta_drenaje(b, ctx)` (l. 1904): Pradal - Asta Drenaje: pasa por una linea vertical u horizontal con un triangulo verde adelante; si te pega se cura el 25% del daño.
  - `_mov_ventisca(b, ctx)` (l. 1913): Helada - Ventisca: muchos ataques de hielo pasan 2 s por una gran parte de la zona (la del lado donde estas).
  - `_mov_chuzos(b, ctx)` (l. 1928): Helada - Chuzos: caen estalactitas de hielo en lugares al azar de la zona (la primera donde estas).
  - `_mov_martillo_hielo(b, ctx)` (l. 1937): Helada - Martillo Hielo: un martillo de hielo enorme cae donde estas.
  - `_mov_tajo_cruzado(b, ctx)` (l. 1945): Fuerte - Tajo Cruzado: 2 cortes en forma de X que cruzan la zona por donde estas.
  - `_mov_puño_drenaje(b, ctx)` (l. 1956): Fuerte - Puño Drenaje: un puñetazo donde estas; si te pega se cura el 25% del daño.
  - `_mov_llave_giro(b, ctx)` (l. 1964): Fuerte - Llave Giro: un golpe en circulo donde estas; si te pega te cambia de pokemon (y no podes volver por 2 s).
  - `_mov_bomba_lodo(b, ctx)` (l. 1971): Toxica - Bomba Lodo: tira 3 bolas que dejan 3 charcos chicos en el piso; lastiman si los pisas.
  - `_mov_picotazo_veneno(b, ctx)` (l. 1982): Toxica - Picotazo Veneno: 15 agujas de veneno finas y largas que cruzan la zona, todas en vertical o todas en horizontal.
  - `_mov_carga_toxica(b, ctx)` (l. 1996): Toxica - Carga Toxica: pasa por una linea al azar que cruza la zona y deja un rastro de veneno que dura 7 s.
  - `_mov_huesomerang(b, ctx)` (l. 2007): Terrax - Huesomerang: tira 3 huesos que van y vuelven hacia el (pegan a la ida y a la vuelta).
  - `_mov_mil_flechas(b, ctx)` (l. 2022): Terrax - Mil Flechas: caen 20 flechas (circulos chicos) sobre la zona; algunas donde estas.
  - `_mov_bucle_arena(b, ctx)` (l. 2032): Terrax - Bucle Arena: 3 circulos de arena movediza por 4 s (uno donde estas); si pisas uno quedas trabado hasta apretar interactuar.
  - `_mov_bote(b, ctx)` (l. 2041): Cielo - Bote: salta, su sombra sigue por donde estabas durante 3 s, cae ahi y vuelve a su lugar.
  - `_mov_tornado(b, ctx)` (l. 2046): Cielo - Tornado: una fila de rafagas cruza la zona en vertical (con un hueco para pasar) y despues el viento te empuja
  - `_mov_embestida_simple(b, M, tipo, efecto)` (l. 2063): Embestida hasta donde estas (y un poco mas) y vuelta a su lugar: Pajaro Osado, Chupavidas y Desarme.
    - `mira(b, ctx)` (l. 2065): A qué punto apunta la embestida (paso del guion).
  - `_mov_pajaro_osado(b, ctx)` (l. 2074): Cielo - Pajaro Osado: embiste hasta donde estas y vuelve a su lugar.
  - `_mov_psiquico(b, ctx)` (l. 2079): Mental - Psiquico: te levanta y te tira al lado contrario de la zona (se esquiva justo cuando termina el aviso).
    - `lanzar(b, ctx)` (l. 2082): Tira el ataque marcado (paso del guion).
  - `_mov_psicorruido(b, ctx)` (l. 2095): Mental - Psicorruido: ondas que salen de el partidas en arcos (como el Vozarron).
    - `salen(b, ctx)` (l. 2099): Suelta las ondas del ataque (paso del guion).
  - `_mov_teletransporte(b, ctx)` (l. 2108): Mental - Teletransporte: desaparece y aparece en otro lugar sobre el vacio, afuera de la zona (y se queda ahi).
    - `irse(b, ctx)` (l. 2111): El jefe desaparece (Teletransporte).
    - `volver(b, ctx)` (l. 2114): El jefe vuelve a aparecer lejos de donde estaba (Teletransporte).
  - `_mov_corte_furia(b, ctx)` (l. 2124): Bicho - Corte Furia: 3 cortes donde estas (cada uno en una direccion al azar); cada uno pega mas que el anterior.
    - `cortar(i)` (l. 2127): Arma el corte número i de Corte Furia.
      - `f(b, ctx)` (l. 2129): El golpe en sí (paso del guion).
  - `_mov_chupavidas(b, ctx)` (l. 2138): Bicho - Chupavidas: embiste hasta donde estas; si te pega se cura el 50% del daño (pega menos que Asta Drenaje).
  - `_mov_ida_y_vuelta(b, ctx)` (l. 2143): Bicho - Ida y Vuelta: va rapidisimo a donde estas sin avisar, vuelve y cambia de tabla al instante (sin animacion).
  - `_mov_roca_veloz(b, ctx)` (l. 2151): Petrea - Roca Veloz: 5 piedras que salen rapido, de a una, hacia donde estas en ese momento.
  - `_mov_hachazo_petreo(b, ctx)` (l. 2162): Petrea - Hachazo Petreo: un golpe en forma de X en un lugar al azar y despues otro en forma de cruz.
    - `hachazo(cruz)` (l. 2165): Arma un hachazo de Hachazo Pétreo (en cruz o en X).
      - `f(b, ctx)` (l. 2167): El golpe en sí (paso del guion).
  - `_mov_avalancha(b, ctx)` (l. 2178): Petrea - Avalancha: caen rocas en lugares al azar de la zona (la primera donde estas).
  - `_mov_alarido(b, ctx)` (l. 2188): Oscura - Alarido: 6 ataques siniestros que salen de el en abanico hacia donde estas.
    - `gritar(b, ctx)` (l. 2191): Suelta las balas del Alarido en abanico.
  - `_mov_desarme(b, ctx)` (l. 2203): Oscura - Desarme: embiste hasta donde estas; si te pega perdes un objeto de la mochila.
  - `_mov_mordisco(b, ctx)` (l. 2208): Oscura - Mordisco: 5 mordiscos; antes de cada uno aparece en un lugar al azar al lado de la zona y muerde hacia adentro.
    - `morder(b, ctx)` (l. 2211): El mordisco de Arceus Beta desde afuera de la arena.
  - `_mov_fuerza_lunar(b, ctx)` (l. 2224): Duende - Fuerza Lunar: un rayo redondo que persigue por donde estabas durante 5 s.
  - `_mov_brillo_magico(b, ctx)` (l. 2233): Duende - Brillo Magico: la pantalla queda blanca medio segundo pero el juego sigue (y enseguida viene otro movimiento).
  - `_mov_cañon_floral(b, ctx)` (l. 2240): Duende - Cañon Floral: carga 2 s y despues un ataque en linea recta (horizontal o vertical) por donde estas, que dura 7 s.
    - `disparar(b, ctx)` (l. 2243): Dispara el Cañón Floral cruzando la arena.
  - `_elegir_beta(b, ctx)` (l. 2266): Elige al azar uno de los 3 movimientos de la tabla puesta (no repite el ultimo).
- **El triangulo (fases 2 y 3)**
  - `_celda_cerca(z, f, c, tam, extra)` (l. 2276): Si alguna parte de la casilla queda a menos de 'extra' pixeles de la zona.
  - `_limpiar_beta(b, ctx)` (l. 2285): Corta todo lo que Arceus Beta tenia en marcha (al cambiar de fase).
  - `_armar_triangulo(b, ctx)` (l. 2296): Termino la fase 1: el piso se vuelve el triangulo de la imagen y Arceus Beta pasa arriba de la punta.
  - `_transicion(b, ctx)` (l. 2314): Paso de la fase 1 a la 2: se corta todo, la pantalla se pone blanca y aparece el triangulo. True mientras dura.
  - `circulos_eleccion(b)` (l. 2333): Los 3 circulos del triangulo en el mundo: (subjefe, centro, radio x, radio y, color).
  - `_circulo_bajo(b, p)` (l. 2341): El subjefe del circulo donde esta parado p (None si no esta arriba de ninguno).
  - `_eleccion(b, ctx)` (l. 2348): La ultima piedad: Arceus Beta espera quieto (sin recibir daño) a que te pares arriba de un circulo.
  - `volver_al_triangulo(b, ctx)` (l. 2373): Ganaste contra el subjefe: vuelve el piso del triangulo, quedas en el medio y Arceus Beta sigue con sus tablas.
  - `actualizar_beta(b, ctx)` (l. 2384): Arceus Beta: quieto en su lugar con las tablas girando; usa los movimientos de la tabla puesta y cada 10 s cambia de tabla.
- **Dibujo de Arceus Beta**
  - `_superficie_triangulo(td)` (l. 2432): La imagen del triangulo escalada, con el vacio pintado alrededor como lo pinta el entorno (casillas con borde violeta y
  - `dibujar_suelo(ventana, b, cx, cy, ahora, colores)` (l. 2459): Lo de Arceus Beta que va en el piso, debajo de los pokemon: el triangulo de las fases 2 y 3 y los charcos, rastros y arena.
  - `_dibujar_eleccion(ventana, b, cx, cy, ahora)` (l. 2478): Los 3 circulos titilan con su color; el que pisas se va llenando hasta que queda elegido.
  - `_forma(sup, g, color, cx, cy, borde, escala)` (l. 2492): Dibuja la forma de un golpe (llena o solo el borde). 'escala' achica circulos y lineas (el aviso que se va llenando).
  - `_zigzag(ventana, desde, hasta, color, ancho, azar, partes, salto)` (l. 2508): Un rayo quebrado de desde a hasta.
  - `_dibujar_golpes(ventana, b, cx, cy, ahora, colores, suelo)` (l. 2518): Los golpes de Arceus Beta: el aviso se va llenando del color del tipo y cuando pega se pinta entero.
  - `_detalle_golpe(ventana, b, g, cx, cy, ahora, color)` (l. 2550): Lo que cae, muerde o brilla encima de cada golpe.
  - `_dibujar_tabla(ventana, centro, color, tam, brilla)` (l. 2639): Una tabla: placa del color de su tipo con un circulo en el medio.
  - `_dibujar_beta(ventana, e, x, y, cx, cy, ahora, colores, fuente)` (l. 2647): Todo lo de Arceus Beta que va arriba de los pokemon: golpes, balas, tablas, embestidas, viento, destellos y el Brillo Magico.
- **Regis**
  - `_dir(desde, hacia)` (l. 2774): Vector de largo 1 de 'desde' hacia 'hacia'.
  - `_muro_hielo(b, ctx)` (l. 2781): Pared de 3 bloques de hielo entre Regice y vos, de costado.
  - `_bloque_glaciar(b, ctx, puntos)` (l. 2794): Al final del rayo hielo de la primera fase queda un bloque de hielo para empujar con E (como mucho unos pocos a la vez).
  - `_actualizar_estalactitas(b, ctx)` (l. 2804): Estalactitas de la segunda fase: una sombra que crece en el piso y despues cae el hielo.
  - `actualizar_regice(b, ctx)` (l. 2816): Regice: muros de hielo y rayo hielo que deja escarcha. Fase 1: el rayo deja un bloque de hielo para empujar.
  - `_poner_roca(b, ctx, puntos)` (l. 2865): Deja una roca de Regirock al final de una fila (hasta un maximo por sala).
  - `_avanzar_filas(b, ctx)` (l. 2878): Roca afilada: las rocas van saliendo una detras de otra hasta chocar con algo; si no te pegaron, queda una roca al final.
  - `_en_franja(b, j, ancho)` (l. 2898): El que embiste pega en todo el ancho de su franja, no solo con el cuerpo.
  - `_dash_regirock(b, ctx)` (l. 2903): Fuerza bruta de Regirock: carga en linea recta, rompe las rocas que toca y queda aturdido si choca.
  - `_actualizar_avalancha(b, ctx)` (l. 2924): Las rocas de la avalancha vuelan, caen (lastiman si estas abajo) y quedan un rato como obstaculo.
  - `_partir_regirock(b, ctx)` (l. 2941): Tercera fase: Regirock se parte en 5 rocas rodantes (entre todas tienen la vida que le quedaba).
  - `_actualizar_rodantes(b, ctx)` (l. 2956): Las rocas rodantes rebotan en las paredes y en las rocas, tiran lanzarrocas y al quedarse sin vida explotan.
  - `actualizar_regirock(b, ctx)` (l. 2992): Regirock: fase 1 roca afilada y avalancha; fase 2 ademas Fuerza bruta y arena movediza; fase 3 se parte en 5 rocas rodantes.
  - `_actualizar_minas(b, ctx)` (l. 3033): Las minas de Registeel que se cumplen explotan y sueltan 8 balas en estrella.
  - `_actualizar_sierras(b, ctx)` (l. 3050): Las sierras rebotan en las paredes hasta que se les acaba el tiempo o te pegan.
  - `_iman(b, ctx)` (l. 3067): Iman: atrae (o aleja) al jugador y a las minas. Registeel se queda quieto mientras dura.
  - `_actualizar_foco(b, ctx)` (l. 3086): Foco Resplandor: un rayo que va siguiendo por donde estabas (no donde estas), asi se puede esquivar.
  - `_cuerpo_pesado(b, ctx)` (l. 3099): Cuerpo Pesado: Registeel salta fuera de la pantalla, su sombra te sigue, se frena y cae.
  - `actualizar_registeel(b, ctx)` (l. 3124): Registeel: fase 1 sierras; fase 2 sierras, minas e iman (atrae o aleja); fase 3 sierras, iman, Foco Resplandor y Cuerpo Pesado.
  - `_crear_torres(b, ctx)` (l. 3173): Las torres electricas de Regieleki, en ronda alrededor del centro de la arena.
  - `_rayos5(b, ctx)` (l. 3186): Regieleki dispara 5 balas electricas en abanico hacia el jugador.
  - `_ir_a_torre(b, ctx, torre)` (l. 3196): Regieleki viaja a una torre dejando una linea electrica que lastima.
  - `_salir_de_torre(b, ctx)` (l. 3204): Regieleki deja la torre (rota si le pegaron) y pasa a otra; sin torres libres empieza a teletransportarse.
  - `_jaula_voltio(b, ctx)` (l. 3220): Jaula Voltio: un cuadrado electrico alrededor del jugador. Lastima si lo tocas y se rompe con 2 ataques.
  - `_actualizar_jaula(b, ctx)` (l. 3231): Cuenta los golpes que le das a la jaula (cualquier lado) y la saca cuando se rompe o se le acaba el tiempo.
  - `actualizar_regieleki(b, ctx)` (l. 3251): Regieleki: rafagas de 5 rayos; con 3/4 de vida se esconde en torres (pegarle a la torre le pega a el);
- **Regidrago**
  - `_dash_regidrago(b, ctx)` (l. 3317): Enfado: como Fuerza Bruta pero no se aturde, y va dejando fuego.
  - `_cometa(b, ctx, puntos)` (l. 3336): Marca una lluvia de cometas de Regidrago (caen de a uno).
  - `_cometa_torre(b, ctx)` (l. 3341): Banda de meteoritos de punta a punta de la torre, a la altura donde estas.
  - `_cometa_suelo(b, ctx)` (l. 3350): Banda de meteoritos que pasa por donde estas, en cualquier direccion.
  - `_actualizar_cometas(b, ctx)` (l. 3358): Cada cuadro: los cometas de Regidrago que caen y pegan.
  - `_boca(b, ctx, pos)` (l. 3371): Pone una boca de dragón de Regidrago (dispara; en la tercera fase se le puede pegar).
  - `_boca_torre(b, ctx)` (l. 3381): Las bocas salen del vacio alrededor de la torre (arriba o a los costados).
  - `_actualizar_bocas(b, ctx)` (l. 3390): Cada boca apunta a un punto (en la torre, o cerca tuyo) y tira Dragoaliento: 3 llamaradas en abanico.
  - `_empezar_draco(b, ctx, volver)` (l. 3413): Draco Energia: se queda quieto y no recibe daño; carga 2 s y despues un rayo que te sigue 10 s.
  - `_actualizar_draco(b, ctx)` (l. 3423): Cada cuadro: el aliento de dragón de Regidrago.
  - `subir_regidrago(b, plataforma, ahora)` (l. 3444): Ya estan arriba de la torre: Regidrago flota delante, moviendose de un lado al otro.
  - `bajar_regidrago(b, centro, ahora)` (l. 3453): La torre se rompio: de vuelta en la sala, tercera fase.
  - `alfa_fundido(b, ahora)` (l. 3462): Pantalla blanca al subir y al romperse la torre.
  - `actualizar_regidrago(b, ctx)` (l. 3471): La pelea entera de Regidrago cada cuadro: fases, torre, bocas, cometas y aliento.
- **Subjefes de Arceus Beta: Giratina, Dialga y Palkia origen**
- **Efectos sobre el jugador (los lee main.py al moverte y al recibir daño)**
  - `fx(j, nombre, ahora)` (l. 3611): Si el jugador tiene ese efecto de un subjefe (invertido, lento, gravedad, vulnerable, defensa_baja, cegado).
  - `poner_fx(j, nombre, ahora, ms)` (l. 3616): Le pone un efecto al jugador por ms milisegundos (si ya lo tenia, dura hasta lo que termine mas tarde).
  - `mult_vel_fx(j, ahora)` (l. 3622): Cuanto te frenan los efectos (Cara Susto y Gravedad).
  - `mult_daño_fx(j, ahora)` (l. 3630): Cuanto mas daño recibis por los efectos (Cola Ferrea y Eco Metalico).
- **La arena**
  - `armar_arena_subjefe(ent, j, centro)` (l. 3640): Arena de los subjefes: un rectangulo de piso 'abismo' en el medio y vacio alrededor. Te pone abajo en el medio.
  - `cerrar_subjefe(b, ctx)` (l. 3663): Termino la pelea con el subjefe: vuelve el piso que rompio, se le sacan los efectos al jugador y lo suelta si estaba atrapado.
  - `_rect_arena(b)` (l. 3678): El rectángulo de la arena del jefe.
  - `_lento_sub(b, ahora)` (l. 3682): Palkia con la Gravedad puesta: sus ataques tambien van mas lentos.
  - `_limitar_sub(b, p)` (l. 3688): El punto mas cercano a p donde el subjefe entra entero en la arena.
  - `_mover_sub(b, hacia, vel)` (l. 3694): El subjefe camina (o vuela) hacia un punto. Devuelve True si llego.
  - `_poner_sub(b, pos)` (l. 3708): Mueve al jefe a un punto sin salirse de la arena.
  - `_toca_punto(j, pos, radio)` (l. 3713): Si el jugador toca un círculo.
  - `_esquivando(j, ahora)` (l. 3717): Si el jugador esta en la invulnerabilidad del esquive (los efectos sin daño tambien se esquivan).
  - `_romper_piso(b, ctx, f, c, ms)` (l. 3722): Una casilla de la arena se vuelve vacio por ms milisegundos (no la de abajo tuyo).
  - `_actualizar_grietas(b, ctx)` (l. 3735): El piso roto vuelve cuando se le acaba el tiempo.
  - `_empujar(b, j, direccion, vel, restante, pared, ahora)` (l. 3744): Empuja al jugador: 'restante' pixeles, o hasta que choca contra algo (pared=True, la Hidrobomba).
  - `_actualizar_empuje(b, ctx)` (l. 3749): Cada cuadro: el empujón que le dieron al jefe.
- **Balas, ondas y otras cosas que andan sueltas**
  - `_bala_sub(b, pos, ang, vel, radio, daño, tipo, clase, dist, dura, rebota, efecto)` (l. 3769): Agrega una bala del jefe.
  - `_envolver(p, rect)` (l. 3774): Palkia: lo que sale por un borde de la arena aparece por el otro.
  - `_actualizar_proys(b, ctx)` (l. 3784): Cada cuadro: las balas del jefe (se mueven, rebotan y pegan).
  - `_actualizar_ondas(b, ctx)` (l. 3815): Cara Susto: una onda que se agranda hasta cubrir toda la arena; si te alcanza (y no la esquivas) quedas lento.
- **Mecanica de cada sala**
  - `_mecanica_giratina(b, ctx)` (l. 3832): El mundo al reves: cada tanto la sala se da vuelta y los controles se invierten.
  - `_mecanica_dialga(b, ctx)` (l. 3844): El reloj: cada vuelta completa Dialga rebobina y volves a donde estabas unos segundos antes.
  - `_pos_hace(hist, t, defecto)` (l. 3865): Dónde estaba el jugador hace un rato (para los ataques que te persiguen con retraso).
  - `_mecanica_palkia(b, ctx)` (l. 3872): Los bordes conectados: si empujas contra un borde de la arena aparecés del otro lado (las balas tuyas tambien pasan).
- **Movimientos de Giratina**
  - `_mov_golpe_umbrio(b, ctx, a)` (l. 3903): El ataque «Golpe Umbrio», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_bola_sombra(b, ctx, a)` (l. 3926): El ataque «Bola Sombra», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_garra_dragon(b, ctx, a)` (l. 3942): El ataque «Garra Dragon», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_cometa_draco(b, ctx, a)` (l. 3974): El ataque «Cometa Draco», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_esfera_aural(b, ctx, a)` (l. 3986): El ataque «Esfera Aural», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_actualizar_esferas(b, ctx)` (l. 3994): Esfera Aural: sigue tu ultima posicion, te lastima si te toca y rompe el piso por donde pasa.
  - `_mov_cara_susto(b, ctx, a)` (l. 4009): El ataque «Cara Susto», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Movimientos de Dialga**
  - `_mov_distorsion(b, ctx, a)` (l. 4026): El ataque «Distorsion», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_pulso_dragon(b, ctx, a)` (l. 4049): El ataque «Pulso Dragon», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_actualizar_muros(b, ctx)` (l. 4067): Las ondas del Pulso Dragon avanzan; pegan salvo que estes en el hueco.
  - `_mov_cola_ferrea(b, ctx, a)` (l. 4083): El ataque «Cola Ferrea», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_foco_resplandor(b, ctx, a)` (l. 4104): El ataque «Foco Resplandor», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_actualizar_focos(b, ctx)` (l. 4115): Foco Resplandor: al explotar, el area grande te encandila (pantalla blanca medio segundo).
  - `_mov_joya_luz(b, ctx, a)` (l. 4125): El ataque «Joya Luz», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_actualizar_rocas(b, ctx)` (l. 4136): Joya de Luz: las rocas rebotan dejando hilos de luz; los hilos lastiman poquito; las rocas se rompen pegandoles.
  - `_toca_linea_hilos(j, hilos)` (l. 4165): Si el jugador toca alguno de los hilos.
  - `_mov_eco_metalico(b, ctx, a)` (l. 4170): El ataque «Eco Metalico», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Movimientos de Palkia**
  - `_mov_corte_vacio(b, ctx, a)` (l. 4187): El ataque «Corte Vacio», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_vasto_impacto(b, ctx, a)` (l. 4221): El ataque «Vasto Impacto», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_torbellino(b, ctx, a)` (l. 4265): El ataque «Torbellino», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_actualizar_remolinos(b, ctx)` (l. 4279): Torbellino: se mueven (cruzando los bordes, como todo en la sala de Palkia); si te agarran quedas girando hasta apretar E.
  - `_mov_hidrobomba(b, ctx, a)` (l. 4306): El ataque «Hidrobomba», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_trueno(b, ctx, a)` (l. 4326): El ataque «Trueno», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_mov_gravedad(b, ctx, a)` (l. 4341): El ataque «Gravedad», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
  - `_puede_sub(b, j, mov)` (l. 4363): Condiciones extra de algunos movimientos (Cola Ferrea solo si estas cerca).
  - `actualizar_subjefe(b, ctx)` (l. 4370): Giratina, Dialga o Palkia origen: la mecanica de su sala, lo que dejo suelto y un movimiento por vez (ver GIRATINA, DIALGA, PALKIA).
- **Dibujo de los subjefes**
  - `_imagen_sombra(tam)` (l. 4425): La sombra de Golpe Umbrio (assets/interfaz/sombra_giratina.png) escalada; None si no esta.
  - `_dibujar_suelo_sub(ventana, b, cx, cy, ahora, colores)` (l. 4435): Lo de los subjefes que va en el piso: tinte de la sala, reloj, piso azul, gravedad, bordes conectados, sombras y remolinos.
  - `_dibujar_reloj(capa, b, centro, ahora)` (l. 4510): El reloj de Dialga en el medio de la arena: la aguja da una vuelta por rebobinada.
  - `_dibujar_sub(ventana, e, x, y, cx, cy, ahora, colores, fuente)` (l. 4529): Lo de los subjefes que va arriba de los pokemon: balas, ondas, rocas, hilos, esferas, chorro, zarpazos y la pantalla.
  - `dibujar_pantalla_fx(ventana, j, ahora, fuente)` (l. 4624): Arriba de todo: la pantalla blanca del Foco Resplandor y los efectos que tenes encima.
  - `actualizar_jefe(b, ctx)` (l. 4635): Te sigue por el mapa de flujo, tira rafagas en abanico apuntadas y si estas cerca pisotea (todo avisado).
- **Dibujo**
  - `dibujar_sello(ventana, centro, radio, color, k, ahora)` (l. 4671): El sello de la Sentencia: circulo grande, triangulo con un circulo en cada punta, circulo interior y anillos de circulitos.
  - `_dibujar_boca(ventana, pos, ang, abierta)` (l. 4702): Cabeza de dragon de piedra, como la de Regidrago, mirando hacia ang.
  - `_dibujar_regidrago(ventana, e, x, y, cx, cy, ahora)` (l. 4715): Dibuja lo de Regidrago: cometas, bocas y aliento.
  - `dibujar_avisos(ventana, lista, cx, cy, ahora, fuente, colores)` (l. 4768): Anillos, lineas y miras que avisan cada ataque, y el '!' cuando un enemigo te descubre.

### `mecanicas.py` (1684 líneas)

> mecanicas.py - Lo que hace unico a cada linea evolutiva: una pasiva o un especial propio, inspirado en lo que dice su Pokedex.
> Las del juego original (Pikachu, Squirtle, Machop...) cambian la forma de moverse y de pelear: rodar, saltar, cargar golpes,
> teletransportarse, agarrar y revolear, esquives que cortan o dejan cosas, disparos que vuelven...
>
>     LINEAS[especie] = (clave, etapa)        etapa 1, 2 o 3: las evoluciones lo hacen mas fuerte
>     MECANICAS[clave] = {'nombre', 'desc', 'clase': 'pasiva' | 'especial', ...}
>     especial_de(especie) -> (nombre, datos) para la casilla R (o None si su mecanica es pasiva)
>     texto_de(especie) -> 'Nombre: que hace' (para la ficha, la pokedex y el glosario)
>     armar(c) -> los ganchos que llama el combate (c trae las funciones del juego que hacen falta)
>
> Balance: las pasivas son chicas y siempre estan; lo fuerte va en especiales con mucha espera (Prediccion, Control
> Mental, Ilusion...). Las de 'contacto' castigan al que te pega cuerpo a cuerpo.

- **Datos**
- `_linea(clave, *especies)` (l. 23): Arma la tabla especie -> (mecánica, etapa) de una línea evolutiva.
  - **Las lineas del juego original**
- `_p(nombre, desc, **extra)` (l. 124): Datos de una mecánica pasiva.
- `_e(nombre, desc, enfriamiento, tipo, **extra)` (l. 125): Datos de una mecánica que se usa como especial.
- **Normal**
- **Fuego**
- **Planta**
- **Hielo**
- **Veneno**
- **Tierra**
- **Volador**
- **Psiquico**
- **Bicho**
- **Roca**
- **Fantasma**
- **Dragon**
- **Siniestro**
- **Acero**
- **Hada**
- **Las lineas del juego original: formas distintas de moverse y de pelear**
- `de(especie)` (l. 271): (clave, etapa) de la mecanica de linea de la especie, o (None, 0).
- `especial_de(especie)` (l. 276): El especial propio de la especie para la casilla R: (nombre, datos) o None si su mecanica es solo pasiva.
- `texto_de(especie)` (l. 286): Lo que hace unico a esta especie, en una o dos lineas (o None).
- **Lazos de equipo**
- `lazos_de(especies, tipos_de)` (l. 355): Los lazos que tiene este equipo: [(nombre, por que, {clave: valor})]. especies: los que estan en pie; tipos_de(especie) -> sus tipos.
- `_titulo(especie)` (l. 378): Nombre lindo de una especie (con espacios y mayúsculas).
- `texto_bono(da)` (l. 381): '+6% daño, +4% velocidad' a partir de lo que da un lazo.
- `primera_de(clave)` (l. 386): El primer pokemon de la linea que tiene esa mecanica (Mudkip para 'barro'): con ese nombre se la reconoce.
- `miembros_lazo(nombre)` (l. 391): Quienes forman un lazo, en palabras: las lineas que cuentan (por su primer pokemon) y cuantas hacen falta.
- `lazos_posibles(especie, tipos)` (l. 401): Los lazos que este pokemon puede formar: [(nombre, con quien, lo que da)] (para su ficha y la pokedex).
- `suma_lazos(lazos)` (l. 417): Todo lo que dan los lazos juntos, con el tope por cosa (la energia vale el triple, como en las sinergias).
- **Logica**
- `armar(c)` (l. 427): Los ganchos del combate. c: namespace con las funciones y datos del juego (ver main.py, armar_mecanicas).
- **Ayudas**
  - `mec(j)` (l. 434): (clave, etapa) de la especie que pelea.
  - `es(j, clave)` (l. 438): Si el pokemon tiene esa mecánica (la de su línea).
  - `etapa(j)` (l. 441): En qué etapa de su línea está (1, 2 o 3): las mecánicas mejoran al evolucionar.
  - `estado(j)` (l. 444): Lo que guarda la mecanica del que pelea (se reinicia con la sala).
  - `daño(j, base, tipo, forma)` (l. 448): Daño de un golpe de mecanica escalado igual que cualquier ataque (rol, nivel, buffs, estilo).
  - `area(j, nivel, centro, radio, base, tipo, retroceso, efecto, con_objetos)` (l. 452): Golpe en un círculo hecho por una mecánica (pega a enemigos y objetos).
  - `cosa(nivel, **datos)` (l. 456): Algo que queda en la sala (bomba, nube, charco, agujero, raices, piedras, jardin, flecha...).
  - `enemigos_vivos(nivel)` (l. 462): Los enemigos de la sala que siguen en pie.
  - `debilitados(j)` (l. 465): Los enemigos vivos que tienen poca vida.
  - `cono(j, nivel, alcance, grados)` (l. 468): Enemigos (y jefe) dentro de un cono adelante del jugador.
  - `efecto_onda(nivel, x, y, radio, tipo, ms)` (l. 480): Un anillo que se abre (efecto visual de las mecánicas).
  - `poner_a(o, que, ms)` (l. 483): Le pone un estado a un enemigo (quemar, paralizar, dormir, ralentizar, confundir, veneno).
  - `golpear_a(j, o, base, tipo, retroceso, efecto)` (l. 488): Le pega a un enemigo puntual con el daño de la mecánica.
  - `objetivo_cercano(j, nivel, alcance, sin)` (l. 491): El enemigo vivo más cercano a un punto (dentro de un radio).
- **Al entrar a una sala**
  - `nueva_sala(j, nivel)` (l. 498): Lo que se reinicia con cada sala (contadores de Autoestima, Impulso, Plancha, Huida...).
  - `al_cambiar(j)` (l. 504): Cambiaste de pokemon: lo que era del que salio se va (ilusion, bajo tierra, vuelo, prediccion...).
- **Golpes tuyos**
  - `mult_golpe(j, o, datos)` (l. 516): Multiplicador del daño de un golpe del jugador segun su mecanica (antes de aplicarlo).
  - `tras_golpe(j, o, datos, hecho)` (l. 544): Despues de un golpe del jugador que conecto (o es el objetivo; hecho es el daño).
  - `remate(j, nivel, tocados)` (l. 569): El tercer golpe del combo conecto.
  - `mult_enfriamiento_combo(j)` (l. 591): Cuánto se acorta la espera entre golpes del combo (algunas líneas encadenan más rápido).
  - `mult_parry(j)` (l. 594): Cuánto dura la ventana de parry según la mecánica (Armadura fósil, Filo psíquico...).
  - `al_parry(j, nivel, atacante)` (l. 598): Hiciste parry: Croagunk envenena, Aegislash pasa a escudo.
- **Golpes que recibis**
  - `recibido(j, cuanto, tipo, atacante, evitable)` (l. 609): Modifica el daño que le llega al jugador (antes de los buffs y la defensa). Devuelve el daño nuevo.
  - `contacto(j, atacante, nivel)` (l. 659): Te pegaron cuerpo a cuerpo: lo que le pasa al atacante (veneno, frio, pinchos, el Arrokuda de Cramorant...).
  - `estado_puesto(j, que)` (l. 673): Te pusieron un estado: Sincronia se lo pasa al enemigo mas cercano.
- **Al derrotar / limpiar**
  - `derrota(j, o, nivel)` (l. 682): Lo que pasa con la mecánica cuando cae un enemigo (cargas, curas, contadores).
  - `sala_limpia(j, nivel)` (l. 691): Lo que pasa con la mecánica al limpiar una sala.
  - `mult_romper(j)` (l. 698): Cuánto más fácil sale un premio al romper cosas (Olfato: el doble).
  - `mult_iman(j)` (l. 701): Desde qué distancia vienen solas las monedas (Olfato).
  - `mult_monedas(j)` (l. 704): Monedas extra (Stoutland).
  - `objeto_roto(j)` (l. 707): Al romper un objeto: los que comen hierro se curan un poco.
  - `aviso_mult(j)` (l. 711): Cuánto antes ves los avisos de los enemigos (Premonición).
  - `regen_energia(j)` (l. 714): Cuánto más rápido se llena la energía (con sol o en el pasto, según la línea).
  - `mult_velocidad(j)` (l. 717): Multiplicador de velocidad que suma la mecánica (impulsos, sol, pasto...).
  - `mult_recarga(j)` (l. 736): Cuánto se acortan las recargas por la mecánica (impulsos).
  - `mult_recarga_especial(j, datos)` (l. 742): Bromista: los especiales que no pegan (buffs, curas, estados) recargan 30% mas rapido.
  - `ignora_solidos(j)` (l. 747): Si ahora atraviesa todo (bajo tierra, volando, en un salto).
  - `invisible(j)` (l. 751): No se dibuja el sprite (bajo tierra).
  - `altura_vuelo(j)` (l. 755): A qué altura se dibuja el pokemon (saltos en parábola, vuelo).
- **Por cuadro**
  - `cuadro(j, nivel)` (l. 766): Todo lo que la mecanica hace solo, cada cuadro (y las cosas que quedaron en la sala).
  - `lento()` (l. 838): Si el tiempo esta frenado (Prediccion de Noibat): los enemigos y sus balas se mueven a un tercio.
- **Rastro de pasto (Chikorita)**
  - `rastro_pasto(j, nivel, et)` (l. 844): Deja pasto por donde camina y lo saca cuando se vence (líneas de planta).
- **Especiales**
  - `usar(j, datos, nivel)` (l. 863): Usa el especial de mecanica (casilla R).
  - `termina_ilusion(j)` (l. 1022): Termina la ilusión o el disfraz (vuelve el sprite de siempre).
  - `dentro_jardin(nivel, j)` (l. 1028): Si el jugador está dentro de un jardín que puso una mecánica.
- **Lo que quedo en la sala**
  - `actualizar_cosas(j, nivel)` (l. 1035): Cada cuadro: las cosas que dejan las mecánicas en el piso (jardines, charcos, nieve, barro...).
- **Enemigos con mecanica**
  - `enemigo(e, j, nivel)` (l. 1082): Lo que hacen algunos enemigos por su cuenta. Devuelve True si este cuadro ya lo manejo (no corre la IA comun).
  - `golpe_enemigo(e, j, hecho)` (l. 1140): Un enemigo te pego cuerpo a cuerpo: la mordida de Mawile paraliza y arrastra.
  - `nubes_enemigas(j, nivel)` (l. 1147): Las esporas de Foongus enemigos: si estas adentro te envenenan.
- **Dibujo**
  - `circulo(ventana, x, y, radio, color, alfa, borde)` (l. 1158): Un círculo medio transparente (guardado para no armarlo cada cuadro).
  - `dibujar(nivel, j, cx, cy)` (l. 1167): Lo que dejaron las mecanicas en la sala y los avisos de los enemigos con mecanica.
  - `dibujar_hud(j, ventana, W, H, cx, cy)` (l. 1238): Flechas en el borde hacia los enemigos de afuera (Noibat), la camara lenta y lo que guarda Shuppet.
- **Mecanicas de las lineas del juego original**
  - `antes_de_atacar(j, nivel)` (l. 1269): Metido en el caparazon o rodando como bola: atacar lo saca (y ese ataque no sale). Cargando el puño tampoco ataca. True: no atacar.
  - `al_esquivar(j, nivel, costo)` (l. 1276): Recien empezo un esquive (j['esquive'] ya esta armado): planeo, estela, sustituto, doble salto, esquive gratis...
  - `al_esquive_perfecto(j, nivel)` (l. 1299): Greninja: con un esquive perfecto aparece detras del enemigo mas cercano.
  - `disparo_basico(j, datos, nivel, indice)` (l. 1312): Cubone y Marowak tiran su hueso (va y vuelve) en lugar del disparo comun. True si ya lo manejo.
  - `al_caer(j, nivel)` (l. 1321): El que pelea se quedo sin vida: Annihilape aguanta una vez por sala, Drifloon explota. True si sigue en pie.
  - `saltar(j, destino, ms, clase, **extra)` (l. 1333): Salto o picada de un punto a otro (lo mueve cuadro), en el aire no lo tocan.
  - `actualizar_salto(j, nivel, e, ahora, et)` (l. 1339): Un cuadro de un salto (picado, plancha): mueve al pokemon en arco y pega al caer.
  - `soltar_puño(j, nivel, e, ahora, et)` (l. 1368): Golett/Golurk solto R: sale propulsado con la fuerza que junto.
  - `actualizar_revoleado(nivel, o)` (l. 1375): Un enemigo que revoleo Machop: vuela en linea, le pega a los que choca y al caer queda aturdido.
  - `tocando(j, nivel, margen)` (l. 1388): Enemigos (y jefe) que estan tocando al jugador.
  - `en_cosa(nivel, j, clase)` (l. 1393): Si el jugador está parado sobre una cosa de esa clase que dejó una mecánica.
  - `cuadro_nuevo(j, nivel, ahora, clave, et, e)` (l. 1399): Lo que hacen solas cada cuadro las mecanicas de las lineas del juego original.
  - **Modos**
  - **Esquives que hacen algo**
  - **Pasivas que juntan algo**
  - **Especiales que siguen despues de usarlos**
  - `usar_nuevo(j, datos, nivel)` (l. 1502): Especiales de las lineas del juego original. True si era uno de estos.
  - `cosa_nueva(j, nivel, x, ahora)` (l. 1564): Lo que dejaron las mecanicas nuevas en la sala. True si la cosa ya se termino (hay que sacarla).
  - `dibujar_cosa_nueva(ventana, x, sx, sy, ahora)` (l. 1611): Dibuja una de las cosas que dejan las mecánicas en el piso.
  - `dibujar_jugador_nuevo(j, ventana, cx, cy)` (l. 1641): Encima del jugador: caparazon, bola de nieve, bloque de hielo, cupula de puas, velo, carga del puño, lana y furia.

### `subjefes.py` (2738 líneas)

> subjefes.py - Los subjefes de cada era: uno en la sala 10 y otro en la sala 20 (ver SUBJEFES).
>
>     import subjefes
>     subjefes.arena(nombre)                          # como se arma su sala (se la pasa a generacion.generar_arena)
>     subjefes.preparar(jefe, ent, ahora)             # al crearlo: su estilo y lo que cambia en la sala (agujeros, alcantarillas, metales...)
>     subjefes.actualizar(jefe, ctx)                  # cada frame (en vez de ia.actualizar_jefe)
>     subjefes.dibujar_suelo(...) / dibujar(...)      # lo de abajo de los pokemon y lo de arriba (oscuridad incluida)
>     subjefes.dibujar_hud(...) / dibujar_hud_jugador(...)
>     subjefes.mult_vel(j, ahora) / mult_ataque(j, ahora) / mult_recarga(j, ahora)    # lo que te hacen a vos
>     subjefes.terminar(jefe, ctx)                    # cayo: se van sus pokemon, vuelve el piso y se te van los efectos
>
>     Era Glacial         sala 10 Cramorant        sala 20 Mamoswine
>     Edad de Piedra      sala 10 Tyrantrum        sala 20 Armaldo
>     Edad de los Metales sala 10 Scizor           sala 20 Tinkaton
>     Edad Media          sala 10 Chandelure       sala 20 Samurott de Hisui
>     Edad Moderna        sala 10 Magnezone        sala 20 Muk de Alola
>
> Los pokemon que aparecen en estas peleas (Arrokuda, Pikachu, Magnemite y Grimer) no dan monedas ni experiencia y nunca quieren
> unirse; en las salas de los subjefes nadie se ofrece como amigo.
> Todos los numeros estan en SUBJEFES: tiempos en ms, velocidades en pixeles por frame, daños como multiplicador del daño del subjefe.
>
> Cada subjefe tiene sus funciones con el mismo nombre de base (las tablas que las juntan estan al final):
>     _prep_<subjefe>     al empezar la pelea: lo que cambia en la arena (PREPARAR)
>     _mec_<subjefe>      su mecanica, cada cuadro (MECANICAS)
>     _quieto_<subjefe>   que hace entre ataque y ataque (QUIETO)
>     _elegir_<subjefe>   el proximo ataque (ELEGIR)
>     _fin_<subjefe>      al terminar un ataque, si hace falta (FIN)
>     _mov_<ataque>       cada ataque paso a paso; devuelve True mientras sigue (MOVS)

- `_arena_de(**extra)` (l. 53): Cómo se arma la sala de un subjefe (vacía, con lo que pida).
- **Los numeros de cada subjefe**
- **Era Glacial**
- **Edad de Piedra**
- **Edad de los Metales**
- **Edad Media**
- **Edad Moderna**
- `arena(nombre)` (l. 269): Como se arma la sala de ese subjefe (formato de las variantes de mundos.ERAS).
- `clima(nombre)` (l. 274): El clima con el que arranca su sala (None: el que venia).
- `es_subjefe(b)` (l. 279): Si un jefe es un subjefe (tiene estilo de subjefe).
- **Utilidades**
- `_d(a, b)` (l. 285): Distancia entre dos puntos.
- `_ang(a, b)` (l. 286): Ángulo de un punto a otro.
- `_v(ang)` (l. 287): Vector (x, y) de un ángulo.
- `_dif(a, b)` (l. 288): Diferencia entre dos ángulos (entre -pi y pi).
- `_mitad(j)` (l. 289): La mitad del tamaño del jugador.
- `_datos(b)` (l. 290): Los números del subjefe (SUBJEFES).
- `_md(b, mov)` (l. 291): Los números de un ataque del subjefe.
- `_jc(ctx)` (l. 292): El centro del jugador.
- `_bc(b)` (l. 293): El centro del subjefe.
- `_solido(ent, x, y)` (l. 296): Si en ese punto hay pared, puerta o maquina (lo que frena las balas).
- `_cambiar(b, ent, f, c, nuevo)` (l. 301): Cambia una casilla y se acuerda de lo que habia (para devolverlo al terminar la pelea).
- `_paso(b, ctx, dx, dy, vel)` (l. 310): Mueve al subjefe vel pixeles en esa direccion frenando contra lo solido. Devuelve (choco en x, choco en y).
- `_ir(b, ctx, destino, vel, alejarse)` (l. 325): Camina hacia (o lejos de) un punto rodeando paredes (mapa de flujo de la ia).
- `_acercar(b, ctx, ideal, vel)` (l. 331): Se queda mas o menos a 'ideal' pixeles tuyos.
- `_poner(b, pos)` (l. 338): Mueve al subjefe a un punto sin salirse de su zona.
- `_buff(b, clave, ahora)` (l. 343): El multiplicador de un buff del subjefe (1 si no tiene).
- `_vel(b, ahora, base)` (l. 348): La velocidad del subjefe con sus buffs.
- `_quemado(j, ahora)` (l. 353): Si el jugador está quemado.
- `_efecto(ctx, ef, ms)` (l. 357): Un efecto sobre vos: quemadura, paralisis, confusion o veneno (estados del juego), congelar, o uno de FX.
- `_pegar(b, ctx, daño, tipo, ef, ms)` (l. 368): Te pega (con los buffs de ataque del subjefe). Devuelve cuanta vida te saco; si te saco algo, te pone el efecto.
- `_toca_b(b, ctx, extra)` (l. 376): Si el subjefe te esta tocando (con algo de margen).
- `_empujar(b, direccion, vel, distancia)` (l. 381): Empuja al subjefe para un lado.
- `_actualizar_empuje(b, ctx)` (l. 385): Cada cuadro: el empujón del subjefe (frena contra las paredes).
- `_tirar_jugador(b, ctx, dx, dy, clave)` (l. 399): Mueve al jugador un poquito (viento, imanes): se acumulan los decimales.
- `_arco(centro, ang, apertura, radio, n)` (l. 409): Puntos de un sector circular (abanico) para los golpes en arco.
- `_punto_area(b, margen)` (l. 415): Un punto al azar de la zona del subjefe.
- `_punto_libre(b, ctx, margen, intentos)` (l. 420): Un punto del area donde no hay nada solido para el jugador (para piedras, puas, bombas...).
- `_anillo(ent, n, profundidad, evitar_puertas)` (l. 429): n casillas repartidas parejo por el borde de adentro de la sala (lejos de las puertas). Devuelve (fila, columna).
- `_centro(ent, f, c)` (l. 449): El centro de una casilla.
- `_marca(b, ahora, clase, dura, **extra)` (l. 453): Una marca en el piso (aviso o efecto) que dura un rato.
- `_mensaje(b, texto, ms)` (l. 460): Un cartel del subjefe (lo muestra main.py).
- **Golpes en el piso (los dibuja ia._dibujar_golpes), con efectos y empujes propios**
- `_golpe(jefe, ahora, forma, aviso, tipo, daño, dura, tick, ef, ms, empuje, infortunio, **extra)` (l. 466): (el jefe no se llama b: 'b' es la punta de las lineas)
- `_actualizar_golpes(b, ctx)` (l. 473): Cada cuadro: los golpes avisados del subjefe (cuando se cumple el aviso, pegan).
- **Balas propias (rebotan, siguen, empujan o solo ponen un efecto)**
- `_bala(b, ahora, pos, ang, vel, radio, daño, tipo, clase, dist, dura, rebota, sigue, ef, ms, empuje, color, **extra)` (l. 498): Agrega una bala del subjefe.
- `_actualizar_proys(b, ctx)` (l. 508): Cada cuadro: las balas del subjefe.
- **Ondas que crecen (gritos, chispazos): pegan una vez cuando el borde te pasa por encima**
- `_onda(b, ahora, centro, dura, maximo, grosor, daño, tipo, ef, ms, color, aviso_ef)` (l. 542): Agrega una onda que se abre desde un punto.
- `_actualizar_ondas(b, ctx)` (l. 547): Cada cuadro: las ondas (pegan cuando el anillo te pasa por encima).
- **Dash: embestida en linea recta que te pega una vez**
- `_dash(b, ctx, a, vel, daño, tipo, extra, ef, ms)` (l. 566): Avanza un paso de la embestida guardada en a ('dir', 'restante'). Devuelve 'sigue', 'llego' o 'choco'.
- **Los pokemon que salen en las peleas**
- `_invocar(b, ctx, nombre, pos, clase, vida, intocable, **extra)` (l. 582): Hace salir un pokemon de la pelea (main.py lo crea como enemigo que no da premios ni se amiga). None si no se puede.
- `_sacar(m, humo)` (l. 592): El pokemon de la pelea se va (o se lo comieron).
- **Preparar, actualizar y terminar**
- `preparar(b, ent, ahora)` (l. 600): El subjefe recien creado: su estilo, su estado y lo que cambia en su sala.
- `actualizar(b, ctx)` (l. 614): Cada frame: la mecanica de su sala, lo que dejo suelto y un movimiento por vez.
- `_empezar(b, ahora, mov)` (l. 643): Arranca un ataque del subjefe.
- `_fin_accion(b, ahora, mov)` (l. 651): Termina el ataque en curso: espera hasta el próximo y su FIN si tiene.
- `_elegir(b, ctx, puede, pesos)` (l. 661): Un movimiento al azar entre los que ya estan listos (no el mismo dos veces seguidas, salvo que sea el unico).
- `terminar(b, ctx)` (l. 670): Cayo el subjefe: se van sus pokemon, vuelve el piso que cambio y se te sacan sus efectos.
- `limpiar_jugador(j)` (l. 685): Le saca al jugador lo que le dejaron los subjefes (al terminar la pelea o al entrar a otra sala).
- **Lo que te hacen a vos (main.py lo usa al moverte, al pegar y al recargar)**
- `mult_vel(j, ahora)` (l. 696): Cuánto te frena lo que te hizo el subjefe.
- `mult_ataque(j, ahora)` (l. 704): Cuánto te baja el ataque lo que te hizo el subjefe (Ojitos Tiernos).
- `mult_recarga(j, ahora)` (l. 708): Cuánto te alarga las recargas lo que te hizo el subjefe.
- `alfa(b)` (l. 712): Transparencia del sprite del subjefe (Manto Niveo de Mamoswine, Armadura Acida de Muk). None: normal.
- **Cramorant**
- `_prep_cramorant(b, ent, ahora)` (l. 719): Prepara la pelea de Cramorant: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_cramorant(b, ctx)` (l. 732): La mecánica propia de Cramorant, cada cuadro (tabla MECANICAS).
- `_reserva(b, ctx)` (l. 777): Le pegaste mientras se tragaba algo: segun cuantos tenia guardados.
- `_quieto_cramorant(b, ctx)` (l. 803): Lo que hace Cramorant entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_cramorant(b, ctx)` (l. 814): Elige el próximo ataque de Cramorant según dónde estás y qué usó antes (tabla ELEGIR).
- `_mov_buceo(b, ctx, a)` (l. 819): El ataque «Buceo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_picotaladro(b, ctx, a)` (l. 849): El ataque «Picotaladro», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_robar_baya(b, ctx, cura)` (l. 866): Picotaladro: si tenes una baya en el lugar 1 del cinturon, te la roba y se cura segun lo que cura la baya.
- `_mov_tragamisil(b, ctx, a)` (l. 880): El ataque «Tragamisil», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_onda_electrica(b, ctx, a)` (l. 900): El ataque «Onda Electrica», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Mamoswine**
- `_prep_mamoswine(b, ent, ahora)` (l. 914): Prepara la pelea de Mamoswine: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_mamoswine(b, ctx)` (l. 918): La mecánica propia de Mamoswine, cada cuadro (tabla MECANICAS).
- `_romper_casillas(b, ctx, casillas)` (l. 934): Rompe el piso en esas casillas (se vuelve agua), sin romper debajo de nadie.
- `_romper_anillo(b, ctx)` (l. 953): Hielo que se agrieta: el borde de la sala se rompe y queda agua (la sala se achica, hasta un minimo).
- `_quieto_mamoswine(b, ctx)` (l. 968): Lo que hace Mamoswine entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_mamoswine(b, ctx)` (l. 972): Elige el próximo ataque de Mamoswine según dónde estás y qué usó antes (tabla ELEGIR).
- `_rocas_mamoswine(b, ctx, cantidad, cada)` (l. 976): Poder Pasado: rocas que esperan alrededor suyo y salen de a una hacia donde estas.
- `_mov_fuerza_equina(b, ctx, a)` (l. 984): El ataque «Fuerza Equina», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_terratemblor(b, ctx, a)` (l. 1007): El ataque «Terratemblor», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_cubierto(ctx, viento, largo)` (l. 1023): Alud: si entre vos y de donde viene el viento hay algo (un objeto o una pared de adentro) que te tapa.
- `_mov_alud(b, ctx, a)` (l. 1038): El ataque «Alud», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_poder_pasado(b, ctx, a)` (l. 1057): El ataque «Poder Pasado», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_proys_que_esperan(b, ctx)` (l. 1067): Las rocas de Poder Pasado: giran alrededor de Mamoswine hasta que les toca salir, y salen hacia donde estas.
- **Tyrantrum**
- `_prep_tyrantrum(b, ent, ahora)` (l. 1083): Prepara la pelea de Tyrantrum: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_tapan_vista(ent, S)` (l. 1087): Casillas que cortan la vista de Tyrantrum (paredes y objetos solidos). Se rehace solo si cambia la sala.
- `_rayo_vista(malas, tam, origen, ang, largo, paso)` (l. 1097): Hasta dónde llega la vista del subjefe en un ángulo (para la oscuridad de Tyrantrum).
- `_mec_tyrantrum(b, ctx)` (l. 1109): La mecánica propia de Tyrantrum, cada cuadro (tabla MECANICAS).
- `_mirar(b, hacia, giro)` (l. 1135): Gira de a poco hacia donde mira el subjefe.
- `_quieto_tyrantrum(b, ctx)` (l. 1139): Lo que hace Tyrantrum entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_tyrantrum(b, ctx)` (l. 1160): Elige el próximo ataque de Tyrantrum según dónde estás y qué usó antes (tabla ELEGIR).
- `_fin_tyrantrum(b, ahora, mov)` (l. 1176): Lo que hace Tyrantrum al terminar un ataque (tabla FIN).
- `_mov_triple_colmillo(b, ctx, a)` (l. 1180): El ataque «Triple Colmillo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_danza_dragon(b, ctx, a)` (l. 1213): El ataque «Danza Dragon», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_testarazo(b, ctx, a)` (l. 1224): El ataque «Testarazo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_cola_dragon(b, ctx, a)` (l. 1247): El ataque «Cola Dragon», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Armaldo**
- `_prep_armaldo(b, ent, ahora)` (l. 1264): Prepara la pelea de Armaldo: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_armaldo(b, ctx)` (l. 1268): La mecánica propia de Armaldo, cada cuadro (tabla MECANICAS).
- `_quieto_armaldo(b, ctx)` (l. 1285): Lo que hace Armaldo entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_armaldo(b, ctx)` (l. 1289): Elige el próximo ataque de Armaldo según dónde estás y qué usó antes (tabla ELEGIR).
- `_mov_pin_misil(b, ctx, a)` (l. 1294): El ataque «Pin Misil», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_cortefuria(b, ctx, a)` (l. 1308): El ataque «Cortefuria», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_trampa_rocas(b, ctx, a)` (l. 1334): El ataque «Trampa Rocas», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_giro_rapido(b, ctx, a)` (l. 1351): El ataque «Giro Rapido», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Scizor**
- `_prep_scizor(b, ent, ahora)` (l. 1376): Prepara la pelea de Scizor: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_scizor(b, ctx)` (l. 1380): La mecánica propia de Scizor, cada cuadro (tabla MECANICAS).
- `_ataques_listos(b, ahora)` (l. 1393): Los ataques de Scizor que ya se pueden volver a usar.
- `_quieto_scizor(b, ctx)` (l. 1398): Lo que hace Scizor entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_scizor(b, ctx)` (l. 1406): Elige el próximo ataque de Scizor según dónde estás y qué usó antes (tabla ELEGIR).
- `_fin_scizor(b, ahora, mov)` (l. 1417): Lo que hace Scizor al terminar un ataque (tabla FIN).
- `_ondas_pinzas(b, ctx)` (l. 1421): Pinzas con ojos falsos: choca las pinzas y salen 2 ondas que confunden.
- `_mov_danza_espada(b, ctx, a)` (l. 1430): El ataque «Danza Espada», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_agilidad(b, ctx, a)` (l. 1442): El ataque «Agilidad», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_puño_bala(b, ctx, a)` (l. 1454): El ataque «Puño Bala», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_ida_y_vuelta(b, ctx, a)` (l. 1481): El ataque «Ida Y Vuelta», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_sobrecalentamiento(b, ctx, a)` (l. 1516): El ataque «Sobrecalentamiento», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Tinkaton**
- `_prep_tinkaton(b, ent, ahora)` (l. 1532): Prepara la pelea de Tinkaton: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_tinkaton(b, ctx)` (l. 1539): La mecánica propia de Tinkaton, cada cuadro (tabla MECANICAS).
- `_quieto_tinkaton(b, ctx)` (l. 1570): Lo que hace Tinkaton entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_tinkaton(b, ctx)` (l. 1574): Elige el próximo ataque de Tinkaton según dónde estás y qué usó antes (tabla ELEGIR).
- `_fin_tinkaton(b, ahora, mov)` (l. 1581): Lo que hace Tinkaton al terminar un ataque (tabla FIN).
- `_mov_martillo_colosal(b, ctx, a)` (l. 1586): El ataque «Martillo Colosal», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_giro_vil(b, ctx, a)` (l. 1629): El ataque «Giro Vil», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_ojitos_tiernos(b, ctx, a)` (l. 1640): El ataque «Ojitos Tiernos», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_carantoña(b, ctx, a)` (l. 1654): El ataque «Carantoña», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Chandelure**
- `_prep_chandelure(b, ent, ahora)` (l. 1692): Prepara la pelea de Chandelure: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_luz_choca(b, v, D)` (l. 1703): Si la luz de Chandelure toca una vela.
- `_mec_chandelure(b, ctx)` (l. 1707): La mecánica propia de Chandelure, cada cuadro (tabla MECANICAS).
- `_circulos_sofoco(So, Sd)` (l. 1771): Dónde están los dos círculos de Sofoco.
- `_quieto_chandelure(b, ctx)` (l. 1776): Lo que hace Chandelure entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_mov_fuego_fatuo(b, ctx, a)` (l. 1787): El ataque «Fuego Fatuo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_infortunio(b, ctx, a)` (l. 1798): El ataque «Infortunio», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_sofoco(b, ctx, a)` (l. 1815): El ataque «Sofoco», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Samurott de Hisui**
- `_prep_samurott_hisui(b, ent, ahora)` (l. 1826): Prepara la pelea de Samurott Hisui: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_samurott_hisui(b, ctx)` (l. 1830): La mecánica propia de Samurott Hisui, cada cuadro (tabla MECANICAS).
- `_quieto_samurott_hisui(b, ctx)` (l. 1852): Lo que hace Samurott Hisui entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_samurott_hisui(b, ctx)` (l. 1856): Elige el próximo ataque de Samurott Hisui según dónde estás y qué usó antes (tabla ELEGIR).
- `_mov_contraataque(b, ctx, a)` (l. 1863): El ataque «Contraataque», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_corte_metralla(b, ctx, a)` (l. 1879): El ataque «Corte Metralla», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_aqua_jet(b, ctx, a)` (l. 1904): El ataque «Aqua Jet», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_concha_filo(b, ctx, a)` (l. 1918): El ataque «Concha Filo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_megacuerno(b, ctx, a)` (l. 1929): El ataque «Megacuerno», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Magnezone**
- `_prep_magnezone(b, ent, ahora)` (l. 1946): Prepara la pelea de Magnezone: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_magnezone(b, ctx)` (l. 1950): La mecánica propia de Magnezone, cada cuadro (tabla MECANICAS).
- `_quieto_magnezone(b, ctx)` (l. 1996): Lo que hace Magnezone entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_fijado(b, ahora)` (l. 2000): Si Magnezone te tiene fijado como blanco.
- `_elegir_magnezone(b, ctx)` (l. 2004): Elige el próximo ataque de Magnezone según dónde estás y qué usó antes (tabla ELEGIR).
- `_mov_fijar_blanco(b, ctx, a)` (l. 2014): El ataque «Fijar Blanco», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_fin_magnezone(b, ahora, mov)` (l. 2026): Lo que hace Magnezone al terminar un ataque (tabla FIN).
- `_rayo_toca(j, a, c, ancho)` (l. 2031): Si un rayo toca al jugador.
- `_mov_electrocañon(b, ctx, a)` (l. 2035): El ataque «Electrocañon», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_triataque(b, ctx, a)` (l. 2066): El ataque «Triataque», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_chispazo(b, ctx, a)` (l. 2098): El ataque «Chispazo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Muk de Alola**
- `_prep_muk_alola(b, ent, ahora)` (l. 2110): Prepara la pelea de Muk Alola: lo que cambia en la arena y su estado al empezar (tabla PREPARAR).
- `_mec_muk_alola(b, ctx)` (l. 2120): La mecánica propia de Muk Alola, cada cuadro (tabla MECANICAS).
- `_quieto_muk_alola(b, ctx)` (l. 2171): Lo que hace Muk Alola entre ataque y ataque: cómo se mueve y te sigue (tabla QUIETO).
- `_elegir_muk_alola(b, ctx)` (l. 2175): Elige el próximo ataque de Muk Alola según dónde estás y qué usó antes (tabla ELEGIR).
- `_mov_bomba_lodo(b, ctx, a)` (l. 2179): El ataque «Bomba Lodo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_lanzamugre(b, ctx, a)` (l. 2195): El ataque «Lanzamugre», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_eructo(b, ctx, a)` (l. 2206): El ataque «Eructo», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- `_mov_armadura_acida(b, ctx, a)` (l. 2219): El ataque «Armadura Acida», paso a paso (aviso, golpe y cierre). Devuelve True mientras sigue.
- **Tablas**
- `_mec_mamoswine_todo(b, ctx)` (l. 2234): La mecánica de Mamoswine y sus balas que esperan.
- **Dibujo**
- `_icono(nombre, alto)` (l. 2270): Un pokemon en chiquito (el primer cuadro de su sprite), para la barra del jefe. None si no tiene sprite.
- `class _Capa` (l. 2285): Una capa transparente del tamaño de la pantalla que se crea recien cuando se dibuja algo en ella (asi no se pagan blits de mas).
  - `__init__(self, ventana)` (l. 2287): Arma la capa (todavía sin superficie).
  - `__call__(self)` (l. 2288): La superficie de la capa (la crea la primera vez).
  - `poner(self)` (l. 2291): Pega la capa transparente en la pantalla (si se usó).
- `_pt(p, cx, cy)` (l. 2295): Un punto de la sala pasado a la pantalla.
- `_oscuridad(ventana, alfa, luces, cx, cy)` (l. 2302): La sala a oscuras: una capa negra con agujeros de luz (circulos con borde suave y poligonos), sin que se pisen entre si.
- `dibujar_suelo(ventana, b, cx, cy, ahora, colores)` (l. 2335): Lo de los subjefes que va en el piso, debajo de los pokemon.
- `dibujar(ventana, b, j, cx, cy, ahora, fuente, colores)` (l. 2442): Lo de los subjefes que va arriba de los pokemon: ataques, balas, la oscuridad y el nombre del movimiento.
- **Avisos propios de cada uno**
- **La oscuridad**
- **Balas y ondas**
- `_dibujar_golpes_propios(ventana, b, cx, cy, ahora)` (l. 2665): Lo que ia._dibujar_golpes no sabe dibujar: los Arrokuda que caen, la basura de Lanzamugre y el fuego del Triataque.
- `_signo(sup, centro, signo, r)` (l. 2690): El + rojo o el - azul de la polaridad.
- `dibujar_hud(ventana, b, rb, ahora, fuente)` (l. 2700): Abajo de la barra del subjefe: los Arrokuda que se trago, los metales del martillo, la Danza Dragon...
- `dibujar_hud_jugador(ventana, j, b, barra, ahora, fuente)` (l. 2727): Abajo de tu barra de vida: tu polaridad (Magnezone) y cuanto mas tardan tus ataques (Chandelure).

### `interfaz.py` (3363 líneas)

> interfaz.py - Lo que se ve fuera de la sala: menus (ajustes, controles, trucos, glosario, equipo, ficha, mochila), dialogos,
> la rueda de curaciones, el logo y las escenas del borde del cosmos (la partida nueva y el viaje entre eras).
>
>     from interfaz import menus

- **Menus**
- `armar_menus()` (l. 23): Pantallas con el mismo estilo que los menus del juego: ajustes, controles, trucos, glosario,
  - `fuente(tam)` (l. 53): Fuente del tamaño pedido (se crea una sola vez).
- **Piezas de BW (assets/interfaz/paneles, las recorta: python herramientas.py paneles)**
  - `pieza(nombre)` (l. 60): assets/interfaz/paneles/<nombre>.png o None.
  - `caja(ventana, rect, nombre, color, borde, color_borde)` (l. 69): Una pieza de BW estirada al rect sin deformar las esquinas (las esquinas se copian, los bordes y el medio se estiran).
  - `fondo(ventana, nombre, color, estirar)` (l. 93): Fondo de BW: repetido al doble (o estirado a la pantalla si no se puede repetir). Si no esta, el color. Devuelve si habia pieza.
  - `pokeball_girando(ventana, centro, lado, ahora, alfa, vueltas_por_minuto)` (l. 112): La Pokeball grande de la pantalla tactil de BW girando despacio (lado en pixeles, alfa 0-255).
  - `ajustar_texto(texto, f, ancho)` (l. 126): Corta un texto en lineas que entren en 'ancho' pixeles.
  - `texto_que_baja(ventana, texto, rect, f, color, alto, ahora)` (l. 137): Un texto en un recuadro: si no entra, no se corta: espera un momento arriba, baja solo renglon por renglon hasta el final,
  - `dibujar_esquinas(pantalla, rect, color, margen, largo, grosor)` (l. 166): Las esquinitas que marcan la opcion elegida.
  - `boton(ventana, rect, texto, elegido, tam, valor, aparicion, variante)` (l. 175): Boton con los paneles en flecha del menu de equipo de BW: azul oscuro, y celeste corrido a la derecha el elegido.
  - `titulo(ventana, texto, x, y, tam, color)` (l. 200): Titulo grande de un menu, con la letra de los titulos del PMD (blanca con borde negro).
  - `pie(ventana, texto, color)` (l. 206): La linea de ayuda de abajo (teclas) en el mismo lugar en todos los menus, sobre una franja oscura para que se lea.
- **Logo: POKE con la letra de pokemon y MANIC en Unown**
  - `_ttf(nombre, tam)` (l. 229): Fuente .ttf de assets/interfaz/fuentes o None si no esta.
  - `_contorno(sup, color, grosor)` (l. 235): La misma superficie con un borde de color alrededor de la silueta.
  - `_letra_unown(letra, alto)` (l. 244): Una letra Unown: con unown.ttf si esta, si no dibujada (trazo negro con el ojo en el medio).
  - `_texto_pokemon(texto, alto)` (l. 265): Amarillo con borde azul y sombra, como el logo de pokemon (pokemon.ttf si esta).
  - `_partes_logo(escala)` (l. 279): El logo del juego (assets/interfaz/logo.png, lo arma 'python herramientas.py logo') cortado en 'Poké' y cada letra Unown: se
  - `dibujar_logo(ventana, alto, ahora, **donde)` (l. 309): El logo del juego: la imagen assets/interfaz/logo.png ('Poké' amarillo y MANIC en Unown) agrandada sin suavizar. Los Unown
- **Las escenas a x2**
  - `reloj_cine()` (l. 334): El reloj de las escenas: corre a la par del de verdad o, con el x2, al doble (sin saltos al cambiar).
  - `cambiar_x2(config)` (l. 342): Pasa la escena de x1 a x2 (o al reves) y lo guarda en config.
  - `tecla_x2(ev, ui)` (l. 347): Si el evento es TAB (o el boton del equipo, o un clic en el boton de x2), cambia la velocidad de la escena. True si lo uso.
  - `boton_x2(ventana)` (l. 355): El boton de la velocidad de la escena, arriba a la derecha: dos flechitas y x1 (gris) o x2 (amarillo), con la tecla al lado.
- **La mano de Celebi**
  - `_mano_verde()` (l. 383): La mano del PMD (el primer cuadro del efecto 0200, la mano abierta y quieta) pintada con los verdes de Celebi: los tonos
  - `mano(ventana, centro, lado, t)` (l. 407): Celebi te agarra: su mano (verde, quieta) aparece apenas mas grande, se cierra un poquito (aprieta), se queda y se va.
  - `animacion(ventana, nombre, centro, lado, t, ms)` (l. 424): Un efecto de assets/efectos (tira de cuadros) que pasa una sola vez: t = ms desde que arranco. False si no esta o ya termino.
  - `_logo_letras(ventana, alto, ahora, **donde)` (l. 433): El logo armado con letras (si falta la imagen): POKE con la letra de los titulos del PMD (amarilla con borde azul) y MANIC con
  - `_logo_viejo(ventana, alto, ahora, **donde)` (l. 455): El logo dibujado (por si faltan las hojas de las letras).
  - `icono_objeto(clave, lado)` (l. 474): Icono de un objeto de la tienda: assets/interfaz/objetos/<clave>.png (las MT tambien buscan mt_<tipo>.png). None si no hay.
  - `chip_tipo(ventana, tipo, x, y)` (l. 486): Etiqueta redondeada del color de un tipo. Devuelve el ancho que ocupo (para poner la siguiente al lado).
  - `barra_vida(ventana, rect, k, etiqueta)` (l. 503): Barra de vida como la de BW: verde, amarilla debajo de la mitad y roja debajo del 20%. Con etiqueta, el 'HP' verde a la izquierda.
  - `barra(ventana, rect, k, color, fondo)` (l. 524): Barra simple (fondo, relleno de 0 a 1 y borde).
- **Piezas del HUD de BW (assets/interfaz/hud, las recorta: python herramientas.py hud)**
  - `hud(nombre, escala)` (l. 541): Pieza del HUD de BW agrandada x escala (pixeles enteros) o None si no esta.
  - `_estirada(nombre, ancho, hueco, quitar)` (l. 552): La pieza con el hueco del medio estirado hasta 'ancho' (a escala 1): se repite una columna del hueco.
  - `color_vida(k)` (l. 575): (claro, oscuro) de la barra de vida de BW: verde, amarilla debajo de la mitad y roja debajo del 20%.
  - `barra_hp(ventana, x, y, ancho, k, cual, escala, nivel, fuente_nv, k_atras)` (l. 580): Barra de HP del combate de BW ('rival': la de arriba, 'jugador': la tuya con la placa oscura) de 'ancho' pixeles de pantalla.
  - `barra_exp(ventana, x, y, ancho, k, color, escala)` (l. 611): Barra fina de experiencia de BW (tambien sirve para la energia con otro color).
  - `boton_tactil(ventana, centro, radio, k_espera, acento, apagado)` (l. 624): Boton octogonal de la pantalla tactil de BW (Luchar / Mochila / Huir): textura de puntitos, borde blanco grueso.
  - `icono_estado(ventana, estado, centro, escala)` (l. 673): Icono de estado de BW (BRN, PAR, FRZ...) centrado en 'centro', con la animacion del PMD encima (la llama, la calavera...).
  - `panel_flecha(ventana, rect, variante)` (l. 689): Panel en flecha del menu de equipo de BW (fila, columna de la hoja) estirado al rect, con las puntas sin deformar.
  - `aparecer(t, retraso, dura)` (l. 711): 0 -> 1 con frenada al final (para que las cosas entren deslizandose): t = ms desde que se abrio el menu.
- **Fondo del menu principal**
  - `fondo_menu(ui, ahora, con_celebi)` (l. 722): Fondo del titulo y del menu: assets/interfaz/fondos/menu.png si existe; si no, el Templo de la Pureza dibujado (con Celebi).
- **Intro: del cielo a la isla**
  - `intro(ui, duracion)` (l. 770): Cinematica del principio: arranca en el cielo del Explorers of Sky (assets/interfaz/fondos/cielo.png y nube_<n>.png,
- **Viaje temporal: el principio de una partida nueva**
  - `_cuadros_viaje(prefijo, cantidad, W, H)` (l. 834): Los cuadros assets/interfaz/fondos/<prefijo>_<n>.png escalados a la pantalla (lista vacia si no estan).
  - `segun_genero(genero, chico, chica, otro)` (l. 845): El texto que corresponde al genero que elegiste (para los dialogos: 'bienvenido', 'bienvenida' o 'te damos la bienvenida').
  - `fondo_viaje(ui, ahora, fase)` (l. 850): El tunel del viaje temporal del Explorers of Sky: el cosmos quieto (viaje_fondo.png) y encima, medio transparente, la capa de
- **El borde del cosmos: la partida nueva y los viajes entre eras**
  - `cara_celebi(ui, emocion, lado)` (l. 891): El retrato de Celebi con esa cara (Happy, Surprised, Worried...). Si falta, el normal.
  - `portal(ventana, centro, radio, ahora, cierre)` (l. 902): El portal del tiempo: el agujero dimensional violeta del Explorers of Time/Darkness (assets/efectos/portal.png, lo arma
  - `centro_cosmos(W, H)` (l. 950): Donde esta el corazon del cosmos en la pantalla: de ahi viene todo.
  - `resplandor(lado, color, nivel, dureza)` (l. 955): Una mancha de luz redonda SIN borde (se apaga de a poco hasta el negro), lista para sumarse con BLEND_RGB_ADD.
  - `luz(ventana, centro, lado, color, nivel, dureza)` (l. 980): Suma a la pantalla una mancha de luz sin bordes (ver resplandor).
  - `mancha(ventana, centro, lado, color, alfa, dureza)` (l. 987): Como luz, pero pintada encima (no sumada): se ve de su color aunque atras haya mucha luz (lo lejano sobre el centro del cosmos).
  - `orbe(ventana, pos, esc, ahora, cola, brillo)` (l. 1010): Tu espiritu: un orbe de luz sin bordes (un halo celeste que se apaga de a poco y un nucleo blanco) que late despacio, con
  - `seguir_cola(cola, pos, esc, ahora)` (l. 1025): Agrega a la estela del orbe donde esta ahora (si se movio lo suficiente) y tira lo viejo.
  - `_mota(z)` (l. 1041): Una mota de polvo nueva: en algun lugar alrededor del centro, a lo lejos (o a una distancia al azar si es la primera vez).
  - `motas_nuevas()` (l. 1047): (ayudante interno)
  - `polvo_estelar(capa, centro, motas, dt, vel)` (l. 1051): Las motas salen del centro del cosmos y vienen hacia vos a velocidad pareja: lejos son puntitos casi quietos, de cerca se
  - `_copia_apagada(img, _cache)` (l. 1067): La copia de la estela: en gris y oscurecida (sin color ni brillo), guardada para no rehacerla.
  - `dejar_estela(estela, img, x, y, ahora)` (l. 1076): Deja una copia en la estela si ya paso un rato desde la ultima (asi nunca hay mas de dos).
  - `dibujar_estela(ventana, estela, ahora, fondo)` (l. 1082): Las copias de la estela, cada vez mas transparentes hasta que se van, corriendose hacia el fondo del cosmos.
  - `_mira(dx, dy)` (l. 1094): La direccion del sprite (0 abajo, 2 derecha, 4 arriba, 6 izquierda) para mirar hacia (dx, dy).
  - `_suave(k)` (l. 1099): Curva suave de 0 a 1 (arranca y frena despacio).
  - `_rapido(k)` (l. 1104): Arranca rapido y se pasa un poquito antes de frenar (los movimientos de golpe de Celebi).
  - `viaje_temporal(ui)` (l. 1110): Partida nueva en el borde del cosmos (unos 45 s hasta que Celebi habla). Negro, y en el centro del cosmos, lejisimos, un
  - **Dibujo**
    - `actor(a, pos, esc, direccion, anim)` (l. 1135): Dibuja un pokemon (agrandado o achicado) y devuelve (imagen, x, y).
    - `soltar(x, y, vx, vy, ahora, lado, color, vida)` (l. 1149): Suelta una chispa (polvito de luz) que se va con el cosmos y se apaga.
    - `dibujar_chispas(ahora, dt)` (l. 1154): Las chispas: se mueven, el cosmos las arrastra hacia afuera (hacia vos) y se apagan.
    - `gesto(ahora)` (l. 1164): Lo que hace Celebi con el cuerpo mientras habla, segun la cara: salta de contento, se sobresalta, se hunde de
    - `dibujar(ahora)` (l. 1179): Dibuja la escena del cosmos entera: fondo, polvo, portal, chispas, tu orbe o tu cuerpo, Celebi, el '!' y los efectos.
    - `dibujar_sombra(ahora, color, alfa, a)` (l. 1262): La sombra del pokemon que estas eligiendo (o el blanco que lo cubre al materializarse), con la transformacion al cambiar.
  - **Tiempo**
    - `correr(ms, mover)` (l. 1284): Deja correr la escena ms milisegundos llamando a mover(k, ahora) (k de 0 a 1). Una tecla la adelanta al final.
    - `ir(destino, ms, esc, anim, mira, curva, rapido)` (l. 1301): Celebi va a 'destino' en ms: suave (arranca y frena despacio) o rapido (sale disparado y se pasa un poquito).
      - `mover(k, ahora)` (l. 1306): Un paso del movimiento de Celebi en la escena (de k = 0 a 1).
    - `recorrido(puntos, ms, ritmo, mira, anim)` (l. 1313): Celebi sigue una curva redonda (Catmull-Rom) por 'puntos' (relativos a tu luz), empezando donde esta, a velocidad
      - `mover(k, ahora)` (l. 1331): Un paso por la curva.
    - `rodear(centro, ms, rx, ry, vueltas, desde, rapido)` (l. 1343): Celebi da vueltas alrededor de un punto mirandolo, desde donde esta (suave, o de golpe si es rapido).
      - `mover(k, ahora)` (l. 1348): Un paso del movimiento de Celebi en la escena (de k = 0 a 1).
  - **Dialogos**
    - `decir(texto, cara, opciones_, anim)` (l. 1357): Celebi dice algo con esa cara (letra por letra; mientras habla se mueve un poquito y hace el gesto de esa cara: salta,
    - `escribir_nombre(pregunta)` (l. 1398): Celebi te pregunta el nombre y lo escribís en la caja.
  - **Elegir tu forma (la sombra)**
    - `elegir_forma()` (l. 1424): Elegis que pokemon eras viendo su sombra donde esta tu espiritu (la sombra se encoge y crece distinta al cambiar).
  - **1. negro: en el centro del cosmos, lejisimos, aparece tu orbe (justo donde va a nacer la luz de la apertura)**
    - `a_lo_lejos(k, ahora)` (l. 1480): Negro un rato; despues aparece de a poco un puntito de luz, titilando apenas.
  - **2. se abre el tiempo (la apertura del Explorers of Time): la flecha da en tu orbe y ahi nace la luz**
    - `abrir(k, ahora)` (l. 1489): Los cuadros de la apertura; tu orbe se enciende cuando lo toca la flecha y se funde en la estrella que nace.
  - **3. tu espiritu viene del centro serpenteando (derecha, izquierda, derecha, izquierda) y se queda adelante**
    - `acercarse(k, ahora)` (l. 1501): Tu orbe se acerca en perspectiva (lejos crece despacio, cerca mas rapido) yendo y viniendo de costado, cada vez menos.
    - **4. Celebi: un brillito verde en el mismo centro, se acerca (sin tanta vuelta) y pasa de largo por abajo a la izquierda**
    - `de_lejos(k, ahora)` (l. 1520): Celebi viene desde el fondo en perspectiva: lejos casi no se mueve; cerca se agranda y pasa volando.
    - **5. vuelve: se da cuenta ("!"), te rodea con curiosidad, una vuelta rapida, barre el cosmos de la emocion y se calma**
  - **6. la charla**
    - `hablar(lineas)` (l. 1549): Varias líneas de Celebi seguidas (algunas lo mueven antes a otro lugar: despacio si esta triste o preocupado,
    - `correrse(k, ahora)` (l. 1589): Celebi se corre a un costado y tu espíritu sube un poco (antes de materializarte).
  - **6. te materializas: estrellas que giran y se juntan, un destello y tu cuerpo**
    - `materializar(k, ahora)` (l. 1604): Te materializás: estrellas que giran y se juntan, un destello y aparece tu pokemon.
  - **7. se abre el portal atras, suerte, y se van juntos (todo se apaga)**
    - `adentro(k, ahora)` (l. 1642): Celebi te lleva de la mano al portal.
    - `apagar(k, ahora)` (l. 1652): El portal se cierra y todo se apaga (queda un brillo que se va).
  - `cruzar_portal(ui, era_nombre, pokemon, duracion)` (l. 1662): Terminaste una era: Celebi te arrastra de la mano por el cosmos hasta la siguiente. Se abre desde el blanco del portal; Celebi
- **Dialogos**
  - `quien_habla(ui, texto)` (l. 1719): Si el texto empieza con 'Nombre: ' y ese nombre es un pokemon con retrato (o Celebi), (nombre, resto); si no, (None, texto).
  - `cara_de(texto)` (l. 1727): La cara de Celebi que va con lo que dice (cuando no se la dan): contenta si exclama, preocupada si duda, si no la normal.
  - `retrato_de(ui, quien, cara)` (l. 1735): El retrato de quien habla (Celebi con su cara).
  - `texto_nuevo(lineas, ahora)` (l. 1741): Un texto largo para la caja de dialogo: se escribe letra por letra y, si no entra, baja (scroll) cuando volves a tocar.
  - `texto_estado(t, ahora)` (l. 1748): (letras escritas, si ya se escribio todo lo que se ve, si queda texto mas abajo).
  - `texto_avanzar(t, ahora)` (l. 1755): Tocaste ENTER (o clic): si esta escribiendo, completa lo que se ve; si hay mas abajo, baja (queda el ultimo renglon para no
  - `texto_scroll(t)` (l. 1768): Cada cuadro: el scroll se acerca suave al renglon que toca.
  - `caja_hablada(ventana, ui, quien, lineas, cuanto, cara, detalle, ahora, alfa, flecha, desde, mas)` (l. 1775): La caja de dialogo de abajo (la misma de la intro): el retrato con su marco y su nombre, y el texto hasta 'cuanto' letras.
  - `preguntar(ui, texto, opciones_, detalle, quien, cara)` (l. 1824): Dialogo abajo de la pantalla (como en los juegos): quien habla con su retrato y su nombre, el texto letra por letra (en
- **Rueda de curaciones**
  - `rueda_curacion(ui, opciones_, mantener)` (l. 1879): Rueda de curaciones como la de Breath of the Wild: la pelea queda congelada detras y alrededor del centro estan tus curaciones
    - `mas_cerca(dx, dy)` (l. 1892): Qué lugar de la rueda está más cerca de una dirección.
- **Ajustes**
  - `ajustes(ui)` (l. 1937): Ajustes con el formato de los otros menus. El codigo Konami abre los trucos.
    - `cambiar(clave, paso)` (l. 1954): Cambia el valor de una opcion de ajustes hacia un lado (-1 o +1) y lo aplica.
  - `menu_controles(ui)` (l. 2018): Teclas configurables: Teclado / Control, 3 perfiles de cada uno, restaurar preset.
    - `dibujar_espera()` (l. 2057): Pantalla de 'apreta una tecla' mientras se reasigna un control.
  - `trucos(ui)` (l. 2092): Menu secreto (codigo Konami en ajustes o en pausa).
- **Glosario**
  - `_efecto_txt(ef)` (l. 2126): Texto de un efecto del entorno para el glosario ('daño x1.3', 'resbala'...).
  - `secciones_glosario(config)` (l. 2143): Textos del glosario armados con los mismos datos que usa el juego (asi no quedan desactualizados).
  - `glosario(ui)` (l. 2312): Glosario: secciones con terrenos, maquinas, climas, tipos y controles, con scroll.
- **Partidas guardadas**
  - `elegir_partida(ui, resumenes)` (l. 2355): Las 3 ranuras de guardado. Devuelve ('continuar' | 'nueva', ranura), None si volves o 'salir'.
- **Ataques: todos los movimientos del juego y que hacen**
  - `ataques(ui)` (l. 2418): Todos los ataques del juego por categoria (basicos, especiales, asistencias, MT): izq/der cambia de categoria,
- **Inicial**
  - `_evolucion_final(nombre)` (l. 2481): Ultima evolucion a la que puede llegar (siguiendo la primera rama), para mostrar en que se convierte.
- **Equipo (TAB)**
  - `equipo(ui, j, acc)` (l. 2494): Menu de equipo. acc tiene funciones de main.py
  - `_info_corta(ventana, m, j, x, y, ancho, activo)` (l. 2541): Nombre, nivel, vida y experiencia de un miembro.
  - `_dibujar_clasico(ui, j, sel, escena)` (l. 2555): Como el menu de equipo de los juegos: el activo grande a la izquierda y los demas en lista.
  - `_dibujar_escenario(ui, j, sel, escena)` (l. 2582): Tus pokemon parados en un escenario como en la pokedex. Si no tocas nada un rato, se duermen.
  - `_frena(k)` (l. 2624): (ayudante interno)
  - `_dibujar_vitrina(ui, j, sel, escena, acc)` (l. 2628): Menu de equipo nuevo: tus pokemon en cartas a la izquierda (entran deslizandose) y a la derecha una vitrina del elegido,
  - **Cartas del equipo**
  - **Vitrina del elegido**
  - **Botones, monedas y ayuda**
  - `_pestañas_ficha(ventana, pagina, color)` (l. 2760): Las 4 pestañas de arriba a la derecha. Devuelve sus rects (para el clic).
  - `_parrafo(ventana, texto, x, y, ancho, tam, color, max_lineas)` (l. 2773): Escribe un texto cortado en renglones y devuelve dónde terminó.
  - `_pagina_ataques(ventana, m, acc, area)` (l. 2780): Que hace cada una de las 4 casillas: tipo, forma, numeros, efecto y la explicacion completa.
  - `_pagina_habilidad(ventana, m, acc, area)` (l. 2813): La mecanica de su linea (y que cambia al evolucionar), su especial propio, el rol, lo que da desde la banca y como es de enemigo.
  - `_pagina_mt(ventana, m, j, area, scroll)` (l. 2865): Las MT que puede aprender: en que casillas van, que hacen, cuantas tenes y cual tiene puesta. Devuelve el scroll maximo.
  - `ficha(ui, j, i, acc)` (l. 2895): Ficha de un miembro: stats con IV y EV (para gastar puntos), sinergia, sus 4 movimientos (para enseñar MT), sus 2 objetos y evolucion.
    - **Panel izquierdo: el pokemon sobre su pedestal**
    - **Derecha: stats con las barras de BW, movimientos, objetos y acciones en paneles en flecha**
    - **Recuadro con la explicacion de lo elegido**
  - `_explicar(fila, m, j, acc)` (l. 3092): Lineas que explican la fila elegida de la ficha.
  - `elegir_objeto(ui, j, m, ranura)` (l. 3119): Que objeto de la mochila se pone en la ranura. Devuelve la clave, '' para sacar el que tiene, None si cancela o 'salir'.
  - `elegir_mt(ui, j, m, casilla)` (l. 3134): Lista de las MT de la mochila que este pokemon puede aprender en esa casilla, con lo que hace cada una.
  - `lista_detallada(ui, titulo_, filas, pie, elegido)` (l. 3155): Lista con scroll: cada fila tiene un nombre y abajo una linea que explica que hace. Devuelve el indice elegido, None o 'salir'.
  - `mochila(ui, j, acc)` (l. 3191): Lo que tenes: arriba el cinturon (las curaciones, como mucho 5, en el orden en que se usan con la tecla de curarse: aca se
  - `reserva(ui, j, acc)` (l. 3246): Los que se unieron con el equipo lleno (como mucho 3). Solo se cambian con el equipo en la tienda: Chikorita los cuida.
  - `animacion_evolucion(ui, nombre, antes)` (l. 3266): Evolucion como en los juegos: el pokemon brilla, se vuelve una silueta blanca que cambia entre la forma vieja y la nueva
    - `silueta(a)` (l. 3276): La silueta del pokemon que evoluciona (blanca, para el destello).

### `herramientas.py` (2156 líneas)

> herramientas.py - Programas aparte para preparar el juego (no se usan mientras jugas).
>
>     python herramientas.py descargar           baja los sprites y retratos del PMD (SpriteCollab)
>     python herramientas.py caras celebi ...    baja las demas caras del retrato (feliz, sorprendido, preocupado...) para las charlas
>     python herramientas.py animaciones [poke]  dice que hace cada animacion de los sprites y cual usa cada ataque (y lo guarda en asignacion_animaciones.json)
>     python herramientas.py sonidos             baja los gritos de todos los pokemon (PokeAPI) a assets/sonidos/gritos
>     python herramientas.py datos               arma datos_pokeapi.json desde la PokeAPI
>     python herramientas.py recortar hoja.png   recorta sprites de una hoja y los deja en assets/mundo
>     python herramientas.py hojas               baja todas las hojas (menos pokemon) de BW y los PMD a assets/hojas (via archive.org)
>     python herramientas.py tiles               arma los tilesets con bordes (autotile) y el agua animada del PMD para cada era y variante de sala
>     python herramientas.py decorados           rocas, hielo, pinos (piezas sueltas del PMD) y arbustos/arboles (Poke Transfer de BW) para los objetos
>     python herramientas.py cielo               recorta el cielo y las nubes del Explorers of Sky para la intro
>     python herramientas.py minimapa            recorta las piezas del minimapa (Map Sprites del Explorers of Time/Darkness)
>     python herramientas.py viaje               recorta el tunel del viaje temporal del Explorers of Sky para la partida nueva
>     python herramientas.py efectos             arma los efectos de golpes, proyectiles por tipo, cura, nivel... con los Attack Effects del PMD
>     python herramientas.py objetos             recorta los iconos de la tienda de la hoja 'Items' de BW a assets/interfaz/objetos
>     python herramientas.py paneles             recorta fondos, botones y paneles de los menus de BW a assets/interfaz/paneles
>     python herramientas.py hud                 recorta barras de HP, iconos de estado, la Pokeball y los paneles en flecha de BW a assets/interfaz/hud
>     python herramientas.py casas               recorta el jardin, el interior y la bandera de cada choza ('Huts' del Red Rescue Team) para el barrio del refugio
>     python herramientas.py arenas              recorta la arena ya dibujada de cada jefe ('Dungeon Boss Rooms' del Red Rescue Team) y guarda su piso
>     python herramientas.py estados             recorta los estados animados (llama, Zzz, calavera, pajaritos...) del Red Rescue Team a assets/efectos
>     python herramientas.py clima               recorta la lluvia, nieve, granizo, niebla, sol, brasas y sombras de nubes del Red Rescue Team a assets/clima
>     python herramientas.py aldea               el arbol suelto, tocon, cerca, matas, flores y las chozas de la plaza ('Huts' del Red Rescue Team)
>     python herramientas.py logo                pasa assets/typo_logo_pokemanic.png a assets/interfaz/logo.png (pixeles originales, sin fondo)
>     python herramientas.py chispas             estrellitas y brillos de los golpes ('Miscellaneous - Effects' del Red Rescue Team)
>     python herramientas.py icono               el icono de Pokemanic.exe (la cara de Celebi) para crear_exe.bat
>     python herramientas.py portal              el portal violeta de las escenas ('Dimensional Hole' del Explorers of Time/Darkness)
>     python herramientas.py espiritu            el aura redonda del espiritu ('Moonlight' del Explorers of Sky)
>     python herramientas.py salas               muestra en texto algunas salas generadas
>     python herramientas.py plan                muestra el plan de salas de una partida
>     python herramientas.py visor               ventana para mirar salas generadas sin jugar

- **Descargar assets**
- `herramienta_descargar()` (l. 53): Baja de SpriteCollab las animaciones y retratos de cada pokemon a assets/sprites/pokemones.
  - `bajar(url, intentos)` (l. 66): Baja una URL (reintenta unas veces). None si no se pudo.
  - `guardar(url, ruta)` (l. 82): Baja una URL a un archivo si todavia no esta. True si quedo guardado.
  - `descargar(nombre, datos)` (l. 95): Baja los sprites (AnimData.xml y hojas) y el retrato de un pokemon desde SpriteCollab.
  - `main()` (l. 129): Baja todo lo que falta de todos los pokemon, de a varios a la vez.
- **Analizar animaciones**
- `herramienta_animaciones(solo)` (l. 161): Lee el AnimData.xml de cada pokemon, dice que hace cada animacion y que animacion le toca a cada uno de sus ataques
  - `leer_xml(carpeta)` (l. 176): Animaciones del AnimData.xml: nombre -> (cantidad de frames, de quien es copia o None).
  - `origen(animador, movimiento, tipo, forma, elegida)` (l. 189): Por que se eligio esa animacion: por el nombre del ataque, por su tipo, por su forma o la generica.
- **Sonidos**
- `herramienta_sonidos()` (l. 249): Baja el grito de cada pokemon (los de PokeAPI: github.com/PokeAPI/cries) a assets/sonidos/gritos/<nombre>.ogg.
  - `bajar(url)` (l. 257): Baja una URL (None si falla).
  - `uno(nombre)` (l. 263): Baja el grito de un pokemon.
- **Generar datos**
- `herramienta_datos()` (l. 288): Pide a la PokeAPI stats, movimientos, descripcion y evoluciones y los guarda en datos_pokeapi.json.
  - `_json(url)` (l. 299): Pide una URL y la lee como JSON.
  - `_por_espejo(url)` (l. 304): La misma pagina desde el espejo de GitHub: ahi todo esta por numero, asi que los nombres se buscan en el indice.
  - `pedir(url)` (l. 315): JSON de la PokeAPI (una URL completa o el nombre de un pokemon). Si pokeapi.co no responde, usa el espejo de GitHub.
  - `como_evoluciona(hijo)` (l. 326): Nivel, piedra u otra condicion para evolucionar a ese hijo de la cadena.
  - `buscar_cadena(nodo, objetivo, padre)` (l. 333): Busca a un pokemon en su cadena evolutiva: (de quien viene, a quienes evoluciona, como).
  - `descripcion(especie)` (l. 344): Texto de la pokedex en castellano (o en ingles si no hay).
  - `main()` (l. 352): Arma datos_pokeapi.json con stats, movimientos, evoluciones y descripciones de todos los pokemon.
- **Recortar assets**
- `herramienta_recortar(ruta)` (l. 397): Para recortar sprites de una hoja (por ejemplo de The Spriters Resource) y dejarlos donde el juego los busca.
  - `main(ruta)` (l. 416): Ventana para recortar a mano sprites de una hoja y guardarlos como objetos o terrenos del mundo.
    - `a_hoja(pos)` (l. 430): De pixeles de la ventana a pixeles de la hoja (segun zoom y desplazamiento).
    - `recorte()` (l. 434): La seleccion achicada al borde del dibujo, con el fondo transparente.
    - `nombres_conocidos()` (l. 444): Nombres de objetos o terrenos que ya usa el juego (para sugerirlos al guardar).
- **Visor de mundos**
- `herramienta_visor()` (l. 527): Para mirar salas generadas sin jugar.
  - `generar(era, variante, tipo, semilla)` (l. 544): Sala y su entorno segun lo elegido en el visor.
  - `main()` (l. 556): Ventana para mirar salas generadas de cualquier era y variante sin jugar.
- **Pruebas**
- **Bajar las hojas de spriters-resource**
- `herramienta_hojas()` (l. 628): Baja todas las hojas (menos los pokemon) de los 4 juegos a assets/hojas/<juego>/<seccion>/.
  - `pedir(url, intentos)` (l. 639): Baja una URL (con reintentos) por archive.org.
  - `limpio(texto)` (l. 654): Nombre de archivo sin caracteres que Windows no acepta.
  - `catalogo(pagina)` (l. 658): [(seccion, id, nombre, carpeta)] de la pagina del juego, sin las secciones de pokemon.
  - `guardada(ruta, crudo)` (l. 670): Direccion de la copia que tiene archive.org (o None). Se pregunta a su API antes de bajar: asi no se le pide de mas.
  - `bajar(juego, pagina, seccion, i, nombre, carpeta)` (l. 678): Baja una hoja de spriters-resource (por archive.org) si todavia no esta.
  - `main()` (l. 695): Baja todas las hojas de BW y los PMD que faltan a assets/hojas.
- **Tiles de las mazmorras del PMD**
- `herramienta_tiles()` (l. 715): Recorta las hojas de tiles de las mazmorras del PMD (Explorers of Sky 'Dungeon Tiles' y Time/Darkness 'Dungeons', de spriters-resource)
  - `buscar_hoja(lugar)` (l. 789): Ruta de la hoja de tiles de ese lugar (en assets o cualquier subcarpeta) o None.
  - `casilla(hoja, col, fila)` (l. 797): La casilla (col, fila) de la grilla de la hoja (24x24, sin la linea).
  - `grupos(hoja)` (l. 801): Que grupo de columnas es cada cosa: {'pared': 1, 'suelo': 4, 'agua': n o None, 'brillo': n o None}.
  - `leyenda(hoja)` (l. 815): Mascara de vecinos de cada casilla de la leyenda (-1 si esta vacia).
  - `recortar(hoja, g)` (l. 827): Las 3x23 casillas del grupo sin las lineas (72x552) y que casillas tienen dibujo ('1') o estan vacias ('0').
  - `paletas(hoja)` (l. 839): Grillas de colores a la derecha de las casillas ('Water palette' y 'Water Sparkle palette'): celdas de 10 px con borde de 1 px.
  - `colores_de(img)` (l. 862): Todos los colores de una imagen (menos el magenta transparente).
  - `repartir(bloques, agua, brillo)` (l. 866): Cada grilla de colores va a la capa cuyos colores cambia (algunas hojas solo tienen la de los brillos). (paleta del agua, de los brillos).
  - `ordenar_paleta(filas, img)` (l. 876): Pone primero la fila de colores que tiene el dibujo (la casilla se recorto en ese frame). None si no tiene nada que ver.
  - `retocar_color(c, escala)` (l. 884): Un color pasado a la escala de un retoque segun que tan claro es (el magenta de los brillos no se toca).
  - `retocar_imagen(img, escala)` (l. 895): La imagen con todos sus colores pasados por el retoque.
  - `main()` (l. 904): Arma cada tileset del PLAN: piezas, variantes, paletas del agua y brillos.
  - `_juntar(a, b)` (l. 962): Pega dos imagenes una al lado de la otra.
- **Objetos del mundo (rocas, hielo, arbustos)**
- `herramienta_decorados()` (l. 973): Sprites de objetos del mundo (assets/mundo/objetos/<nombre>.png, como los lee mundo.entorno.imagen)
  - `buscar(parte)` (l. 987): Ruta de una hoja que termina con ese nombre (en assets o subcarpetas) o None.
  - `casilla(hoja, col, fila)` (l. 995): La casilla (col, fila) de la grilla de una hoja de tiles.
  - `roca(hoja)` (l. 999): Pared sin vecinos sobre el piso, con el piso borrado.
  - `main()` (l. 1026): Recorta todos los objetos de DEL_PMD y TRANSFER a assets/mundo/objetos.
- **Props del PMD (cajas, vasijas, heno...) y casas del Red Rescue Team**
- `herramienta_props()` (l. 1058): Sprites de cosas hechas a mano (assets/mundo/objetos/<nombre>.png)
  - `es_pasto(c)` (l. 1073): Pasto (verde) o piedra del borde del mapa (gris): lo que rodea a las cosas.
  - `sin_pasto(recorte)` (l. 1077): Borra el pasto desde los bordes del recorte (lo que queda encerrado por el contorno oscuro del objeto no se toca).
  - `vasija(par)` (l. 1096): Una vasija sola y entera a partir del par del mapa: la de adelante tiene la mitad izquierda sin tapar, y es simetrica.
  - `llamas(mapa)` (l. 1113): Los 4 cuadros de la fogata sin las piedras ni el pasto: queda solo el fuego (rojo, naranja y amarillo bien vivos).
  - `casa(hoja)` (l. 1136): La casa de una hoja 'Hut': sin el color de fondo y sin los carteles de texto (el pedazo mas grande).
- **Cielo de la intro**
- `herramienta_cielo()` (l. 1174): De la hoja 'Skies' del Explorers of Sky (4 paneles de 288x216) recorta para la intro (interfaz.menus.intro)
  - `main()` (l. 1181): Recorta el cielo y separa cada nube del fondo verde.
- `herramienta_minimapa()` (l. 1200): De la hoja 'Map Sprites' del Explorers of Time/Darkness (el mapa de la pantalla de arriba del PMD) recorta las piezas del minimapa
  - `main()` (l. 1212): Recorta cada pieza de la hoja y saca el verde de fondo.
- `herramienta_viaje()` (l. 1230): Lo del viaje temporal (interfaz.menus.viaje_temporal y cruzar_portal), en assets/interfaz/fondos
  - `buscar(final)` (l. 1243): La hoja que termina con ese nombre (en assets o en assets/hojas).
  - `a_cinco_tercios(hoja, x, y, ancho, alto)` (l. 1247): El cuadro (x, y, ancho, alto) recortado arriba y abajo para que quede 5:3, como la pantalla.
  - `main()` (l. 1252): Recorta el tunel y la apertura.
- **Efectos de ataque del PMD**
- `herramienta_efectos()` (l. 1282): De los 'Attack Effects' del Explorers of Sky (move_VFX/<numero>/000/<frame>.png, el zip o la carpeta assets/efectos/move_VFX)
  - `tira_de(frames)` (l. 1302): Pone frames en una tira horizontal de cuadrados (cada frame centrado en el suyo).
  - `main()` (l. 1309): Arma las tiras de todos los efectos elegidos (del zip o de la carpeta) y las de la hoja Poke Transfer.
- **Iconos de objetos de BW**
- `herramienta_objetos()` (l. 1348): De la hoja 'Items' de Blanco/Negro recorta los iconos de la tienda a assets/interfaz/objetos/<clave>.png (como los lee interfaz.icono_objeto).
  - `buscar_hoja()` (l. 1374): Ruta de la hoja 'Items' de BW o None.
  - `icono(hoja, numero)` (l. 1382): La casilla sin el fondo, recortada al dibujo y centrada en un cuadrado.
  - `main()` (l. 1395): Recorta todos los iconos de ELEGIDOS a assets/interfaz/objetos.
- **Paneles de los menus de BW**
- `herramienta_paneles()` (l. 1420): De las hojas 'Options Screen' y 'Party Screen' de Blanco/Negro recorta las piezas de los menus a assets/interfaz/paneles
  - `buscar_hoja(nombre)` (l. 1437): Ruta de una hoja de BW con ese nombre o None.
  - `sin_borde(sup)` (l. 1445): Vuelve transparente el fondo de la hoja que toca las esquinas (relleno desde las 4 esquinas, sin pasar el marco de la pieza).
  - `main()` (l. 1458): Recorta todas las PIEZAS a assets/interfaz/paneles.
- `herramienta_hud()` (l. 1478): De las hojas 'Battle HUD', 'Miscellaneous Icons' y 'Party Screen' de Blanco/Negro recorta las piezas del HUD y de los menus
  - `buscar_hoja(nombre)` (l. 1500): Busca una hoja de BW en las carpetas de assets.
  - `transparente(sup, color)` (l. 1508): El color de fondo de la hoja que toca los bordes de la pieza pasa a ser transparente (relleno desde los bordes).
  - `pokeball(sup)` (l. 1521): La Pokeball grande sin el fondo: todo lo que queda afuera del circulo es transparente.
- **Clima del Red Rescue Team**
- `_buscar_hoja(final)` (l. 1548): Ruta de la hoja (o zip) que termina con ese nombre, en assets o en cualquier subcarpeta. None si no esta.
- `herramienta_clima()` (l. 1555): De las hojas 'Weather' del Red Rescue Team arma assets/clima/<efecto>/<nn>.png (como los lee mundo.entorno.dibujar_clima)
  - `sin_fondo(sup, color)` (l. 1571): Copia con ese color transparente.
  - `del_medio(frames, parte)` (l. 1577): Los cuadros 'llenos' (con al menos esa parte de lo que tiene el mas lleno): el loop sin el arranque ni el final.
  - `guardar(nombre, frames)` (l. 1583): Deja los cuadros en assets/clima/<nombre>/00.png, 01.png...
  - `del_zip(final, filtro)` (l. 1591): Los png de un zip (los que pasan el filtro), ordenados por su numero.
- **Las chozas del Red Rescue Team (el barrio del refugio)**
- `herramienta_casas()` (l. 1629): De las hojas 'Huts' del Red Rescue Team (una por pokemon: Pikachu Hut, Mudkip Hut...) arma assets/mundo/casas/
  - `una(ruta, nombre)` (l. 1642): Recorta el jardin, el interior y la bandera de una hoja. False si la hoja tiene otra forma.
- **La aldea: arboles sueltos, flores, cercas y las chozas de la plaza**
- `_es_piso_rrt(c, margen)` (l. 1697): Si ese color es pasto, claro o arena de las hojas de chozas (o casi).
- `_suelto(hoja, caja, minimo, sombra, centro)` (l. 1702): Recorta de una hoja de chozas lo que hay en 'caja' sin el piso: desde los bordes se borra el pasto, el claro, la arena y el bosque.
- `sin_orilla(img)` (l. 1728): El borde de la sombra de la hoja (una linea opaca de 1 o 2 pixeles entre la sombra y el pasto) pasa a ser el borde suave de la
- `_sin_bosque(jardin)` (l. 1752): El jardin de una choza sin el bosque azulado que lo rodea (chocaba con el del jardin de al lado): se borra el bosque con su
- `herramienta_aldea()` (l. 1782): De las hojas 'Huts' del Red Rescue Team saca las cosas sueltas de la aldea (el fondo de pasto se vuelve transparente)
  - `hoja_de(nombre)` (l. 1795): Carga una hoja de chozas del Red Rescue Team.
  - `guardar(img, carpeta, nombre)` (l. 1798): Guarda un recorte y lo anota en la lista de lo hecho.
- **Chispas de los golpes (hoja 'Effects' del Red Rescue Team)**
- `herramienta_chispas()` (l. 1853): De la hoja 'Miscellaneous - Effects' del Red Rescue Team saca dos efectos (tiras de cuadros cuadrados, como las lee mundo.efectos)
- **El portal y el espiritu (escenas del cosmos)**
- `herramienta_portal()` (l. 1879): De 'Dimensional Hole' del Explorers of Time/Darkness arma assets/efectos/portal.png: los 8 cuadros del portal violeta
- `herramienta_espiritu()` (l. 1902): El espiritu de la partida nueva: assets/efectos/aura.png, la luz redonda del cielo de 'Moonlight' del Explorers of Sky (el
- **El icono del ejecutable**
- `herramienta_icono()` (l. 1951): Arma assets/interfaz/icono.ico (el icono de Pokemanic.exe) con la cara de Celebi del retrato del PMD, agrandada sin suavizar.
- **El logo**
- `herramienta_logo()` (l. 1969): Pasa el logo del juego (assets/typo_logo_pokemanic.png: pixel art agrandado sobre un fondo azul liso) a assets/interfaz/logo.png
  - `cortes(horizontal, fase)` (l. 1990): Cuántos cambios de color caen justo en la grilla con esa fase (para encontrar el tamaño del pixel del logo).
- **Arenas de los jefes (Dungeon Boss Rooms del Red Rescue Team)**
- `herramienta_arenas()` (l. 2026): De las hojas 'Dungeon Boss Rooms' (y dos 'Friend Areas') del Red Rescue Team arma la arena ya dibujada de cada jefe
  - `main()` (l. 2056): Recorta cada arena alrededor de su plataforma y guarda el poligono en pixeles del recorte.
- **Estados animados del Red Rescue Team**
- `herramienta_estados()` (l. 2082): De la hoja 'Status Effects' del Red Rescue Team (filas de cuadros de 16 px desde x=104; el hielo es de 32) arma las tiras
- `ver_salas()` (l. 2102): Dibuja en texto algunas salas generadas (para ver como quedan sin abrir el juego).
- `ver_plan()` (l. 2113): Dibuja el plan de una partida: T tienda, S subjefe, J semijefe, R regi, A arceus. Y el clima de las primeras salas.
