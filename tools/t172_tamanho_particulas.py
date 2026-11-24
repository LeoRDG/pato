"""Tarefa 172: corrige o tamanho das partículas com textura das t169/t170.

O runtime desenha a textura da partícula no tamanho dela (particula_luz/particula_fumaca têm 128 px) e ignora
rendererParam1/2. As faíscas pensadas com 10 px saíam com 128 px (borrões brancos). Agora o tamanho pensado vai
para o particleSize (%): particleSize * lado / 128, e rendererParam fica 128, o tamanho real.
Rodar uma vez:  python3 tools/t172_tamanho_particulas.py
"""
from gd_mig import *

TEX = ('assets/particulas/particula_luz.png', 'assets/particulas/particula_fumaca.png')
REAL = 128


def migra(d):
    for o in d['objects']:
        if o['type'] == 'ParticleSystem::ParticleEmitter' and o.get('textureParticleName') in TEX \
                and o['rendererParam1'] != REAL:
            k = o['rendererParam1'] / REAL
            o['particleSize1'] = round(o['particleSize1'] * k, 1)
            o['particleSize2'] = round(o['particleSize2'] * k, 1)
            o['rendererParam1'] = o['rendererParam2'] = REAL


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'escudo_faisca')['rendererParam1'] == REAL, 't172')
