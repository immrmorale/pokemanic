import os
import re
import math
import xml.etree.ElementTree as ET
import pygame


direcciones = ['sur', 'sureste', 'este', 'noreste', 'norte', 'noroeste', 'oeste', 'suroeste']
direccion_vector = {
    'sur': (0, 1),
    'suroeste': (-1, 1),
    'oeste': (-1, 0),
    'noroeste': (-1, -1),
    'norte': (0, -1),
    'noreste': (1, -1),
    'este': (1, 0),
    'sureste': (1, 1),
}


def _normalizar_nombre(nombre):
    return str(nombre).strip().lower().replace(' ', '_').replace('-', '_')


def _buscar_carpeta(nombre):
    base = os.path.join('assets', 'sprites', 'pokemones')
    objetivo = _normalizar_nombre(nombre)
    candidatos = [
        os.path.join(base, 'sprite_' + objetivo),
        os.path.join(base, objetivo),
    ]
    for ruta in candidatos:
        if os.path.isdir(ruta):
            return ruta
    if os.path.isdir(base):
        for entrada in os.listdir(base):
            ruta = os.path.join(base, entrada)
            if os.path.isdir(ruta) and _normalizar_nombre(entrada) in ('sprite_' + objetivo, objetivo):
                return ruta
    return None


def _numero_direccion(nombre):
    encontrados = re.findall(r'(\d+)', nombre)
    return int(encontrados[-1]) if encontrados else None


class AnimacionHoja:
    def __init__(self, nombre, indice, ancho, alto, duraciones, rush=None, hit=None, retorno=None, copia=None):
        self.nombre = nombre.lower()
        self.indice = indice
        self.ancho = ancho
        self.alto = alto
        self.duraciones = duraciones or [1]
        self.rush = rush
        self.hit = hit
        self.retorno = retorno
        self.copia = copia


class AnimadorPokemon:
    FACTOR_VELOCIDAD = 2.0
    nombres_ataque = ('attack', 'strike', 'stricke', 'quickstrike', 'quick_strike', 'kick', 'punch', 'slash', 'body', 'melee', 'hit')

    def __init__(self, pokemon, rect, tamaño=40):
        self.pokemon = _normalizar_nombre(pokemon)
        self.rect = rect
        self.tamaño = max(1, int(tamaño or 40))
        self.carpeta = _buscar_carpeta(self.pokemon)
        self.animaciones = {}
        self.sprites = {}
        self.offsets = {}
        self.sombras = {}
        self.usando_hojas = False
        self.animacion_actual = 'idle'
        self.direccion = 0
        self.indice_frame = 0
        self.acumulado = 0.0
        self.terminada = False
        self.escala = 1.0
        self._cargar()

    def _cargar(self):
        if not self.carpeta:
            return
        xml = os.path.join(self.carpeta, 'AnimData.xml')
        if os.path.isfile(xml):
            self._cargar_hojas(xml)
        if not self.usando_hojas:
            self._cargar_formato_antiguo()

    def _cargar_hojas(self, xml):
        try:
            raiz = ET.parse(xml).getroot()
        except Exception:
            return
        contenedor = raiz.find('Anims')
        if contenedor is None:
            return
        for nodo in contenedor.findall('Anim'):
            nombre = nodo.findtext('Name')
            if not nombre:
                continue
            copia = nodo.findtext('CopyOf')
            indice = nodo.findtext('Index')
            ancho = nodo.findtext('FrameWidth')
            alto = nodo.findtext('FrameHeight')
            if ancho is None or alto is None:
                self.animaciones[nombre.lower()] = AnimacionHoja(nombre, None, None, None, [], copia=copia)
                continue
            duraciones = []
            dur_node = nodo.find('Durations')
            if dur_node is not None and dur_node.text:
                for valor in dur_node.text.replace(',', ' ').split():
                    try:
                        duraciones.append(int(valor))
                    except ValueError:
                        pass
            self.animaciones[nombre.lower()] = AnimacionHoja(
                nombre,
                int(indice) if indice else 0,
                int(ancho),
                int(alto),
                duraciones,
                int(nodo.findtext('RushFrame')) if nodo.findtext('RushFrame') else None,
                int(nodo.findtext('HitFrame')) if nodo.findtext('HitFrame') else None,
                int(nodo.findtext('ReturnFrame')) if nodo.findtext('ReturnFrame') else None,
                copia,
            )
        self._resolver_copias()
        cargadas = 0
        for anim in self.animaciones.values():
            if anim.copia or anim.indice is None:
                continue
            if self._cargar_hoja(anim):
                cargadas += 1
        self.usando_hojas = cargadas > 0
        if self.usando_hojas:
            self.escala = self._calcular_escala_base()

    def _resolver_copias(self):
        for anim in self.animaciones.values():
            if not anim.copia:
                continue
            base = self.animaciones.get(anim.copia.lower())
            if base:
                anim.indice = base.indice
                anim.ancho = base.ancho
                anim.alto = base.alto
                anim.duraciones = list(base.duraciones)
                anim.rush = base.rush
                anim.hit = base.hit
                anim.retorno = base.retorno

    def _cargar_hoja(self, anim):
        prefijo = anim.nombre.title().replace('_', '')
        candidatos = [
            prefijo,
            anim.nombre,
            anim.nombre.capitalize(),
        ]
        rutas = []
        for nombre in candidatos:
            ruta = os.path.join(self.carpeta, nombre + '-Anim.png')
            if os.path.isfile(ruta):
                rutas.append((ruta, nombre))
        if not rutas and os.path.isdir(self.carpeta):
            objetivo = (anim.nombre + '-anim.png').lower()
            for archivo in os.listdir(self.carpeta):
                if archivo.lower() == objetivo:
                    rutas.append((os.path.join(self.carpeta, archivo), os.path.splitext(archivo)[0][:-5]))
                    break
        for ruta, nombre in rutas:
            try:
                hoja = pygame.image.load(ruta).convert_alpha()
            except Exception:
                continue
            columnas = max(1, hoja.get_width() // anim.ancho)
            filas = max(1, hoja.get_height() // anim.alto)
            frames = []
            for direccion in range(min(8, filas)):
                fila = []
                for frame in range(columnas):
                    x = frame * anim.ancho
                    y = direccion * anim.alto
                    fila.append(hoja.subsurface((x, y, anim.ancho, anim.alto)).copy())
                frames.append(fila)
            self.sprites[anim.nombre] = frames
            self._cargar_metadatos(anim, nombre)
            return True
        return False

    def _cargar_metadatos(self, anim, prefijo):
        for sufijo, destino in (('-Offsets.png', self.offsets), ('-Shadow.png', self.sombras)):
            ruta = os.path.join(self.carpeta, prefijo + sufijo)
            if os.path.isfile(ruta):
                try:
                    destino[anim.nombre] = pygame.image.load(ruta).convert_alpha()
                except Exception:
                    pass

    def _cargar_formato_antiguo(self):
        if not self.carpeta:
            return
        grupos = {}
        for nombre in ('idle', 'walk', 'strike', 'stricke', 'attack', 'kick', 'punch', 'slash', 'body', 'melee', 'hit'):
            ruta = os.path.join(self.carpeta, nombre)
            if not os.path.isdir(ruta):
                continue
            archivos = []
            for archivo in os.listdir(ruta):
                if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    numero = _numero_direccion(archivo)
                    archivos.append((numero if numero is not None else 999999, archivo))
            archivos.sort()
            if archivos:
                grupos[nombre] = [pygame.image.load(os.path.join(ruta, archivo)).convert_alpha() for _, archivo in archivos]
        if grupos:
            self.sprites = grupos
            self.usando_hojas = False

    def _calcular_escala_base(self):
        candidatos = []
        for nombre in ('idle', 'walk'):
            frames = self.sprites.get(nombre)
            if not frames:
                continue
            for fila in frames:
                for imagen in fila:
                    bbox = imagen.get_bounding_rect()
                    if bbox.height > 0:
                        candidatos.append(bbox.height)
        if not candidatos:
            return 1.0
        altura = max(candidatos)
        return self.tamaño / float(altura)

    def _buscar_animacion(self, nombre):
        nombre = _normalizar_nombre(nombre)
        if nombre in self.animaciones:
            return nombre
        equivalencias = {
            'idle': ('idle',),
            'walk': ('walk',),
            'attack': self.nombres_ataque,
        }
        for candidato in equivalencias.get(nombre, (nombre,)):
            if candidato in self.animaciones:
                return candidato
            if candidato in self.sprites:
                return candidato
        return None

    def buscar_ataque(self):
        for nombre in self.nombres_ataque:
            if nombre in self.animaciones or nombre in self.sprites:
                return nombre
        return None

    def cambiar(self, animacion, direccion=0, repetir=True):
        encontrada = self._buscar_animacion(animacion)
        if encontrada is None:
            return False
        if self.animacion_actual != encontrada or self.direccion != direccion:
            self.animacion_actual = encontrada
            self.direccion = max(0, min(7, direccion))
            self.indice_frame = 0
            self.acumulado = 0.0
            self.terminada = False
        else:
            self.terminada = False if repetir else self.terminada
        self.repetir = repetir
        return True

    def actualizar(self):
        frames = self._frames_actuales()
        if not frames:
            return
        duracion = self._duracion_actual()
        self.acumulado += 1.0
        if self.acumulado < duracion:
            return
        self.acumulado = 0.0
        self.indice_frame += 1
        if self.indice_frame >= len(frames):
            if self.repetir:
                self.indice_frame = 0
            else:
                self.indice_frame = len(frames) - 1
                self.terminada = True

    def _frames_actuales(self):
        if self.usando_hojas:
            anim = self.animaciones.get(self.animacion_actual)
            if not anim:
                return []
            return self.sprites.get(anim.nombre, [[] for _ in range(8)])[self.direccion]
        frames = self.sprites.get(self.animacion_actual, [])
        if frames and isinstance(frames[0], list):
            return frames[min(self.direccion, len(frames) - 1)]
        return frames

    def _duracion_actual(self):
        if self.usando_hojas:
            anim = self.animaciones.get(self.animacion_actual)
            if not anim or not anim.duraciones:
                return 1
            duracion = anim.duraciones[min(self.indice_frame, len(anim.duraciones) - 1)]
            return max(1, math.ceil(duracion * self.FACTOR_VELOCIDAD))
        return 12

    def esta_terminada(self):
        return self.terminada

    def _obtener_offset(self, imagen, animacion, direccion, frame):
        hoja = self.offsets.get(animacion)
        if hoja is None:
            return imagen.get_width() / 2, imagen.get_height() / 2
        color = None
        mejor = None
        x0 = frame * imagen.get_width()
        y0 = direccion * imagen.get_height()
        ancho = imagen.get_width()
        alto = imagen.get_height()
        for y in range(alto):
            for x in range(ancho):
                r, g, b, a = hoja.get_at((x0 + x, y0 + y))
                if a and g > 140 and g > r * 1.35 and g > b * 1.2:
                    mejor = (x, y)
                    break
            if mejor:
                break
        return mejor if mejor else (ancho / 2, alto / 2)

    def dibujar(self, ventana):
        frames = self._frames_actuales()
        if not frames or self.indice_frame >= len(frames):
            return False
        imagen = frames[self.indice_frame]
        if self.usando_hojas:
            escala = self.escala
            ancho = max(1, round(imagen.get_width() * escala))
            alto = max(1, round(imagen.get_height() * escala))
            imagen = pygame.transform.smoothscale(imagen, (ancho, alto))
            ox, oy = self._obtener_offset(frames[self.indice_frame], self.animacion_actual, self.direccion, self.indice_frame)
            ox *= escala
            oy *= escala
            posicion = (round(self.rect.centerx - ox), round(self.rect.centery - oy))
            ventana.blit(imagen, posicion)
        else:
            bbox = imagen.get_bounding_rect()
            if bbox.height > 0:
                escala = self.tamaño / bbox.height
            else:
                escala = 1.0
            imagen = pygame.transform.smoothscale(imagen, (max(1, round(imagen.get_width()*escala)), max(1, round(imagen.get_height()*escala))))
            ventana.blit(imagen, imagen.get_rect(center=self.rect.center))
        return True
