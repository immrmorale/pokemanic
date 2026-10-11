import json
import os 
os.system("cls")
def devolver_ruta_carpeta_raiz():
    return os.path.dirname(__file__)
def armar_ruta(archivo):
    path = devolver_ruta_carpeta_raiz()
    file_path = os.path.join(path, archivo)
    return file_path

def leer_vida():
    ruta = armar_ruta()
    resultados = []
    with open(ruta,"r",encoding ="utf-8") as archivo :
        for line in archivo:
            enemigos = json.loads(line)
            if enemigos["enemigo"] <= 0:
                variable = False
            elif enemigos["enemigo"] > 0:
                variable = True
    return resultados

def escirbir_vida(enemigos, vidas):
    todo = {}
    ruta = armar_ruta()
    with open(ruta,"w", encoding="utf-8") as archivo:
        for enemigo in enemigos:
            for vida_e in vidas:
                todo[enemigo] = vida_e
                
