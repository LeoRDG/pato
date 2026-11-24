"""Tarefa 167: as estrelas brilham.

As imagens viram pontos redondos com brilho suave (tools/arte_estrelas.py) e as estrelas passam para uma camada só
delas, "Estrelas", logo acima do Fundo, com um bloom ("Brilho das estrelas"). Na mesma camada do céu o bloom
borrava as nuvens. A camada tem a mesma lente do buraco negro (BulgePinch "Lente negra"), ligada pelos mesmos eventos
do Fundo, para as estrelas também se curvarem em volta dele. A câmera dessa camada fica parada; as estrelas já se
posicionam pelo centro da câmera da camada. Os números do bloom ficam no efeito da camada, editáveis no GDevelop.
Rodar uma vez:  python3 tools/t167_estrelas_brilham.py
"""
import copy
from gd_mig import *

CAMADA = 'Estrelas'


def migra(d):
    sc = cena(d, 'Paraiso')
    fundo = next(x for x in sc['layers'] if x['name'] == 'Fundo')
    nova = {k: copy.deepcopy(v) for k, v in fundo.items() if k != 'effects'}
    nova.update(name=CAMADA, effects=[
        efeito('AdvancedBloom', 'Brilho das estrelas', {'bloomScale': 1.8, 'blur': 6, 'brightness': 1.3, 'padding': 20,
                                                        'quality': 5, 'threshold': 0.15}),
        efeito('BulgePinch', 'Lente negra', {'centerX': 0.5, 'centerY': 0.5, 'radius': 260, 'strength': 0})])
    sc['layers'].insert(sc['layers'].index(fundo) + 1, nova)

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    for e in todos(deus['events']):
        novas = []
        for a in e.get('actions', []):
            p = a['parameters']
            if a['type']['value'] == 'Create' and p[1] == 'estrela':
                p[4] = f'"{CAMADA}"'
            if a['type']['value'] == 'SetXY' and p[0] == 'estrela':
                a['parameters'] = [x.replace('CameraCenterX("Fundo", 0)', f'CameraCenterX("{CAMADA}", 0)')
                                    .replace('CameraCenterY("Fundo", 0)', f'CameraCenterY("{CAMADA}", 0)') for x in p]
            novas.append(a)
            if a['type']['value'] == 'SetLayerEffectParameter' and p[1] == '"Fundo"' and p[2] == '"Lente negra"':
                b = copy.deepcopy(a)
                b['parameters'][1] = f'"{CAMADA}"'
                novas.append(b)
        if 'actions' in e:
            e['actions'] = novas


if __name__ == '__main__':
    roda(migra, lambda d: any(x['name'] == CAMADA for x in cena(d, 'Paraiso')['layers']), 't167')
