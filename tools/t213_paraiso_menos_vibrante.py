"""Tarefa 213: Paraíso um pouco menos vibrante (o céu azul saturado, as nuvens e o sol).

Efeito novo "Menos vibrante" (Adjustment) na camada do fundo do Paraiso (Fundo) e do HubParaiso (fundo), onde ficam
bg_paraiso_nuvens e bg_paraiso_rosa (sol): saturação SATURACAO (1 = como era), o resto neutro. Ajuste no editor:
camada > efeitos > Menos vibrante > saturação. Personagens, anjos, tiles e HUD não mudam.
O céu atrás das nuvens é a cor de fundo da cena, que o efeito não alcança: ela fica com a mesma saturação
(tirada só se ainda for a cor original 172;196;232).
Rodar uma vez:  python3 tools/t213_paraiso_menos_vibrante.py
"""
from gd_mig import *

SATURACAO = 0.75
CENAS = {'Paraiso': 'Fundo', 'HubParaiso': 'fundo'}
CEU = (172, 196, 232)
NOME = 'Menos vibrante'


def menos_saturado(c):
    lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    return tuple(round(lum + SATURACAO * (v - lum)) for v in c)


def migra(d):
    for nome, camada in CENAS.items():
        l = cena(d, nome)
        cam = next(c for c in l['layers'] if c['name'] == camada)
        cam.setdefault('effects', []).append(efeito('Adjustment', NOME, doubles={
            'gamma': 1, 'saturation': SATURACAO, 'contrast': 1, 'brightness': 1,
            'red': 1, 'green': 1, 'blue': 1, 'alpha': 1}))
        if (l['r'], l['v'], l['b']) == CEU:
            l['r'], l['v'], l['b'] = menos_saturado(CEU)


if __name__ == '__main__':
    roda(migra, lambda d: any(e['name'] == NOME for c in cena(d, 'Paraiso')['layers'] for e in c.get('effects', [])),
         't213')
