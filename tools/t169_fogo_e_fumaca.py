"""Tarefa 169: fogo, fumaça e poeira com textura suave.

Com o renderizador "Point" cada partícula era um disco de borda dura e a explosão parecia um monte de bolhas laranja.
Agora o fogo (explosao_fogo, fogo_lanca) usa particula_luz e a fumaça/poeira (explosao_fumaca, demonio_fumaca,
poeira) usa particula_fumaca (tools/arte_particulas.py), com o lado K vezes o raio do disco antigo (a borda da
textura some aos poucos, então ela precisa ser maior para parecer do mesmo tamanho). Cores, tempos e quantidades
ficam como estão. As texturas são suavizadas (smoothed), porque são degradês.
Rodar uma vez:  python3 tools/t169_fogo_e_fumaca.py
"""
from gd_mig import *

LUZ = 'assets/particulas/particula_luz.png'
FUMACA = 'assets/particulas/particula_fumaca.png'
QUAIS = {'explosao_fogo': LUZ, 'fogo_lanca': LUZ,
         'explosao_fumaca': FUMACA, 'demonio_fumaca': FUMACA, 'poeira': FUMACA}
K = 2.6


def suaves(d, caminhos):
    poe_recursos(d, caminhos)
    for r in d['resources']['resources']:
        if r['name'] in caminhos:
            r['smoothed'] = True


def textura(o, caminho, k=K):
    if o['rendererType'] == 'Point':
        lado = round(o['rendererParam1'] * k)
        o.update(rendererType='Quad', textureParticleName=caminho, rendererParam1=lado, rendererParam2=lado)


def migra(d):
    suaves(d, [LUZ, FUMACA])
    for nome, caminho in QUAIS.items():
        textura(objeto(d, nome), caminho)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'explosao_fogo')['rendererType'] != 'Point', 't169')
