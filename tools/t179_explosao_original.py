"""Tarefa 179: a explosão volta a ser como era (o usuário preferia o visual antigo).

explosao_fogo, explosao_fumaca e explosao_faiscas voltam para o renderizador Point, com o raio e os tamanhos de antes
das t169/t170/t172. Só mexe em quem ainda está como essas tarefas deixaram (Quad com particula_luz/particula_fumaca e
rendererParam 128); os outros emissores com textura suave ficam como estão.
Rodar uma vez:  python3 tools/t179_explosao_original.py
"""
from gd_mig import *

# nome: (rendererParam1, particleSize1, particleSize2) de antes da t169
ORIGINAL = {'explosao_fogo': (40, 100, 30), 'explosao_fumaca': (46, 80, 220), 'explosao_faiscas': (6, 100, 40)}
TEXTURAS = ('assets/particulas/particula_luz.png', 'assets/particulas/particula_fumaca.png')


def migra(d):
    for n, (p1, s1, s2) in ORIGINAL.items():
        o = objeto(d, n)
        if o['rendererType'] == 'Quad' and o['textureParticleName'] in TEXTURAS and o['rendererParam1'] == 128:
            o.update(rendererType='Point', textureParticleName='', rendererParam1=p1, rendererParam2=1,
                     particleSize1=s1, particleSize2=s2)


if __name__ == '__main__':
    roda(migra, lambda d: all(objeto(d, n)['rendererType'] == 'Point' for n in ORIGINAL), 't179')
