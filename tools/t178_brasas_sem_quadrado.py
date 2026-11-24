"""Tarefa 178: conserta as brasas e os hubs.
- inferno_brasas (t177) ficou sem textura e o GDevelop desenhava quadrados: volta a particula_luz;
- hub_brasas, hub_luzes e inferno_brasas deixam de ser aditivos: na camada do jogo, que tem luz 3D, partícula
  aditiva deixava o hub todo esbranquiçado, com o terreno parecendo transparente;
- as brasas do Inferno ficam menores (16 -> 10): pareciam grandes demais.
Só mexe se ainda estiver como a t175/t177 deixou (sem textura / aditivo).
Rodar uma vez:  python3 tools/t178_brasas_sem_quadrado.py
"""
from gd_mig import *
from t169_fogo_e_fumaca import LUZ, suaves

AMBIENTE = ('hub_brasas', 'hub_luzes', 'inferno_brasas')


def migra(d):
    suaves(d, [LUZ])
    o = objeto(d, 'inferno_brasas')
    if o['rendererType'] == 'Quad' and not o.get('textureParticleName'):
        o['textureParticleName'] = LUZ
    if (o['particleSize1'], o['particleSize2']) == (16, 5):   # menores: no jogo pareciam grandes demais
        o['particleSize1'], o['particleSize2'] = 10, 4
    for n in AMBIENTE:
        objeto(d, n)['additive'] = False


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'inferno_brasas').get('textureParticleName')
         and not any(objeto(d, n)['additive'] for n in AMBIENTE), 't178')
