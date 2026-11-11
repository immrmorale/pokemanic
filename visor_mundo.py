"""
visor_mundo.py - Para mirar salas generadas sin jugar.

    python visor_mundo.py

Teclas:
    <- / ->     cambiar de era               arriba / abajo   cambiar de variante
    T           combate / tienda / arena     ESPACIO          otra semilla (otra sala)
    C           probar los climas            P                ver el plan de una partida
    S           guardar captura (visor_XXXX.png)   ESC        salir

Es lo mismo que 'python herramientas.py visor'.
"""

import herramientas

if __name__ == '__main__':
    herramientas.herramienta_visor()
