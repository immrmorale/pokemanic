Pokemanic - revisión de hitboxes y animaciones

Archivos:
- main.py
- pokemones.py
- animaciones.py
- sincronizar_pokeapi.py

Controles:
- WASD: moverse
- Ctrl: sprint
- E: ataque cuerpo a cuerpo
- Q: habilidad secundaria personalizada
- F1: menú de Pokémon
- F2: menú de niveles
- F3: mostrar hitboxes del jugador, enemigos y jefe

Cambios de esta revisión:
- Restaurado el cálculo de estadísticas de juego por Pokémon, incluidas las dimensiones rectangulares de hitbox.
- Conservado sprint, energía, habilidades Q y estadísticas PokéAPI en caché.
- Restaurado el animador anterior basado en delta de tiempo, con la cadencia original de idle/walk y la duración anterior de ataque.
- Restaurados los multiplicadores de daño, alcance, área y velocidad de proyectil junto con el cooldown personalizado.

Para sincronizar datos PokéAPI en un equipo con Internet: python sincronizar_pokeapi.py
