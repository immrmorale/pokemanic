import pygame
import os
import re
direcciones = [
    'sur',
    'sureste',
    'este',
    'noreste',
    'norte',
    'noroeste',
    'oeste',
    'suroeste'
]

direccion_vector = {
    'sur': (0, 1),
    'sureste': (1, 1),
    'este': (1, 0),
    'noreste': (1, -1),
    'norte': (0, -1),
    'noroeste': (-1, -1),
    'oeste': (-1, 0),
    'suroeste': (-1, 1)
}


class AnimadorPokemon:
    animaciones_ataque = ('strike', 'attack', 'kick', 'punch', 'slash', 'body', 'melee', 'hit')

    def __init__(self, nombre, rect, tamaño=40):
        self.nombre = nombre
        self.rect = rect
        self.animacion = 'idle'
        self.direccion = 0
        self.frame = 0
        self.tiempo_frame = 0
        self.frames = {}
        self.informacion = {}
        self.velocidad_frames = {}
        self.animacion_terminada = False
        self.repetir = True
        self.tamaño = tamaño
        self.cargar_animaciones()

    def buscar_carpeta(self):
        raiz = os.path.dirname(os.path.abspath(__file__))
        nombre = self.nombre.lower().strip()
        ruta = os.path.join(raiz, 'assets', 'sprites', 'pokemones', 'sprite_' + nombre)
        if os.path.isdir(ruta):
            return ruta
        return None

    def nombre_animacion(self, nombre):
        nombre = nombre.lower()
        if '_' in nombre:
            partes = nombre.split('_')
            if partes[-1] in ('walk', 'idle', 'strike', 'attack', 'kick', 'punch', 'slash', 'body', 'melee', 'hit'):
                return partes[-1]
        return nombre

    def cargar_animaciones(self):
        carpeta = self.buscar_carpeta()
        if carpeta is None:
            return

        for nombre_carpeta in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre_carpeta)
            if not os.path.isdir(ruta):
                continue

            animacion = self.nombre_animacion(nombre_carpeta)
            archivos = []

            for archivo in os.listdir(ruta):
                if archivo.lower().endswith('.png'):
                    nombre_archivo = os.path.splitext(archivo)[0]
                    coincidencia = re.search(r'(\d+)$', nombre_archivo)
                    if coincidencia:
                        numero = int(coincidencia.group(1))
                        archivos.append((numero, archivo))

            archivos.sort(key=lambda x: x[0])

            imagenes = []
            for _, archivo in archivos:
                try:
                    imagenes.append(pygame.image.load(os.path.join(ruta, archivo)).convert_alpha())
                except pygame.error:
                    pass

            if len(imagenes) < 8:
                continue

            cantidad_frames = len(imagenes) // 8
            imagenes = imagenes[:cantidad_frames * 8]
            tamaño_maximo = max((max(imagen.get_width(), imagen.get_height()) for imagen in imagenes), default=0)

            self.frames[animacion] = []
            self.informacion[animacion] = {
                'cantidad_sprites': len(imagenes),
                'direcciones': direcciones.copy(),
                'frames_por_direccion': cantidad_frames,
                'tamaño_maximo': tamaño_maximo
            }

            for direccion in range(8):
                inicio = direccion * cantidad_frames
                fin = inicio + cantidad_frames
                self.frames[animacion].append(imagenes[inicio:fin])

            if animacion == 'walk':
                self.velocidad_frames[animacion] = 4
            elif animacion in self.animaciones_ataque:
                self.velocidad_frames[animacion] = 4
            else:
                self.velocidad_frames[animacion] = 6

    def buscar_ataque(self):
        for nombre in self.animaciones_ataque:
            if nombre in self.frames:
                return nombre
        for nombre in self.frames:
            if nombre not in ('idle', 'walk'):
                return nombre
        return None

    def cambiar(self, animacion, direccion, repetir=True):
        if animacion not in self.frames:
            if 'idle' in self.frames:
                animacion = 'idle'
            else:
                return

        if self.animacion != animacion or self.direccion != direccion:
            self.animacion = animacion
            self.direccion = direccion
            self.frame = 0
            self.tiempo_frame = 0
            self.animacion_terminada = False

        self.repetir = repetir

    def actualizar(self):
        if self.animacion not in self.frames:
            return

        frames = self.frames[self.animacion][self.direccion]
        if not frames:
            return

        self.tiempo_frame += 1
        velocidad = self.velocidad_frames.get(self.animacion, 6)

        if self.tiempo_frame >= velocidad:
            self.tiempo_frame = 0
            self.frame += 1

            if self.frame >= len(frames):
                if self.repetir:
                    self.frame = 0
                else:
                    self.frame = len(frames) - 1
                    self.animacion_terminada = True

    def esta_terminada(self):
        return self.animacion_terminada

    def dibujar(self, ventana):
        if self.animacion in self.frames:
            frames = self.frames[self.animacion][self.direccion]

            if frames:
                imagen = frames[self.frame]
                ancho = imagen.get_width()
                alto = imagen.get_height()
                mayor = max(ancho, alto)
                tamaño_visual = self.tamaño * 2

                if mayor > 0 and tamaño_visual > 0:
                    factor = tamaño_visual / mayor
                    nuevo_ancho = max(1, round(ancho * factor))
                    nuevo_alto = max(1, round(alto * factor))
                    imagen = pygame.transform.smoothscale(imagen, (nuevo_ancho, nuevo_alto))

                posicion = imagen.get_rect(center=self.rect.center)
                ventana.blit(imagen, posicion)
                return True

        return False
