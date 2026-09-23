from pathlib import Path

import pygame


class Animacion:
    def __init__(self, carpeta, milisegundos_por_frame=80, escala=1):
        archivos = sorted(Path(carpeta).glob("*.png"))

        if not archivos:
            raise FileNotFoundError(
                f"No se encontraron sprites PNG en: {carpeta}"
            )

        self.frames = []
        for archivo in archivos:
            imagen = pygame.image.load(archivo).convert_alpha()

            if escala != 1:
                imagen = pygame.transform.scale_by(imagen, escala)

            self.frames.append(imagen)

        self.milisegundos_por_frame = milisegundos_por_frame
        self.tiempo_acumulado = 0
        self.indice = 0

    def actualizar(self, milisegundos):
        self.tiempo_acumulado += milisegundos

        while self.tiempo_acumulado >= self.milisegundos_por_frame:
            self.tiempo_acumulado -= self.milisegundos_por_frame
            self.indice = (self.indice + 1) % len(self.frames)

    def imagen_actual(self):
        return self.frames[self.indice]

    def reiniciar(self):
        self.indice = 0
        self.tiempo_acumulado = 0