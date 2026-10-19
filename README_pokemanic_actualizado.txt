Pokemanic - version con sprint, energia y habilidades Q

Archivos principales:
- main.py
- pokemones.py
- animaciones.py

Sincronizacion opcional con PokéAPI:
- ejecutar `python sincronizar_pokeapi.py` con conexion a internet.
- el script guarda `datos_pokeapi.json` en esta misma carpeta.
- el juego carga ese archivo automaticamente si existe; no necesita conexion a internet durante la partida.
- si la API no esta disponible, el juego conserva sus datos locales y valores de reserva.

Controles:
- WASD: movimiento
- mantener Ctrl: sprint mientras haya energia
- E: ataque basico cuerpo a cuerpo
- Q: habilidad personalizada del Pokemon (proyectil, doble golpe, embestida o area)
- F1: menu debug de Pokemon
- F2: menu debug de niveles

La barra azul de energia aparece justo debajo de la barra de vida. La energia se consume durante el sprint y se regenera al dejar de correr.

Mundo (eras, salas, tienda, clima, IA): ver LISTA_MUNDO.md
- E en la tienda: comprar el objeto que tenes adelante
- F2: menu de salas (TAB cambia de era) para saltar a tiendas, jefes, Regis y Arceus
- python visor_mundo.py: mirar salas generadas sin jugar
- python recortar_assets.py hoja.png: recortar sprites de una hoja y guardarlos en assets/mundo
- TAB: equipo (ficha, MT, evoluciones, mochila, reserva)   E: comprar / hablar con un pokemon que quiere unirse
- Konami en ajustes o pausa: menu debug   F1 + Konami: debug de pokemon (con jefes)
