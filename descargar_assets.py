"""
descargar_assets.py - Baja los sprites y retratos de todos los pokemon (SpriteCollab) y despues analiza las animaciones:
dice que hace cada una y cual usa cada ataque (la misma eleccion que hace el juego). Guarda el reporte en asignacion_animaciones.json.

    python descargar_assets.py                  bajar lo que falta + analizar
    python descargar_assets.py analizar         solo analizar (sin bajar nada)
    python descargar_assets.py analizar pikachu solo ese pokemon

Es lo mismo que 'python herramientas.py descargar' / 'python herramientas.py animaciones'.
"""

import sys
import herramientas

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'analizar':
        herramientas.herramienta_animaciones(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        herramientas.herramienta_descargar()
