"""Tarefa 183: correntes de luz feitas com efeitos e partículas do GDevelop, não com desenho.

- corrente_luz.png vira uma cor lisa (128 x 128, cor e opacidade abaixo). A forma da coluna vem dos efeitos do objeto
  corrente_luz: KawaseBlur ("Borda suave", desfoca as bordas) e Glow ("Brilho", halo dourado em volta). Os números dos
  efeitos ficam no objeto, editáveis no GDevelop.
- corrente_nevoa: segundo emissor por corrente, com partículas grandes e suaves (particula_luz) subindo devagar pelo
  meio da coluna, o fluxo de luz. As partículas (faíscas e fluxo) ficam um plano acima da coluna. Usa os mesmos eventos das faíscas da t181 (nasce no pé da corrente ou da tela, vive
  até o topo, para quando a corrente apaga), copiados para ele.
A mecânica (subir, ligar e desligar, piscar) não muda.
Rodar uma vez:  python3 tools/t183_correntes_efeitos.py
"""
import copy, os
import numpy as np
from PIL import Image
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import LUZ

ids = Ids('t183')
C, F, N = 'corrente_luz', 'corrente_faisca', 'corrente_nevoa'
TEXTURA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets/paraiso/corrente_luz.png')
COR = (255, 244, 214)
OPACIDADE = 70


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def textura():
    a = np.zeros((128, 128, 4), np.uint8)
    a[...] = (*COR, OPACIDADE)
    Image.fromarray(a, 'RGBA').save(TEXTURA)


def migra(d):
    o = objeto(d, C)
    nomes = {e['name'] for e in o['effects']}
    if 'Borda suave' not in nomes:
        o['effects'].append(efeito('KawaseBlur', 'Borda suave', {'blur': 14, 'quality': 4, 'pixelizeX': 1,
                                                                  'pixelizeY': 1}))
    if 'Brilho' not in nomes:
        o['effects'].append(efeito('Glow', 'Brilho', {'distance': 24, 'innerStrength': 0, 'outerStrength': 1.5},
                                   {'color': '255;236;170'}))
    poe_objeto(d, emissor(objeto(d, F), N, textureParticleName=LUZ, flow=5, maxParticleNb=120, particleSize1=95, particleSize2=70,
                          particleAlpha1=110, particleAlpha2=0, particleColor1='255;248;225',
                          particleColor2='255;220;150', zoneRadius=8), 'cenario/paraiso')
    objeto(d, N)['updateIfNotVisible'] = True
    poe_vars(ids, objeto(d, N)['variables'], N, [('cx', 0)])
    g = acha(cena(d, 'Paraiso')['events'], 'Correntes de luz')
    novos = []
    for e in g['events']:
        t = tx(e)
        if f'"{F}"' in t and f'"{N}"' not in t:
            novos.append(json.loads(t.replace(f'"{F}"', f'"{N}"').replace(f'{F}.', f'{N}.')))
    g['events'] += novos
    for a in (a for e in todos(g['events']) for a in e.get('actions', [])):   # partículas por cima da coluna
        if a['type']['value'] == 'ChangePlan' and a['parameters'][0] in (F, N) and a['parameters'][2] == f'{C}.ZOrder()':
            a['parameters'][2] = f'{C}.ZOrder() + 1'


if __name__ == '__main__':
    textura()
    roda(migra, lambda d: objeto(d, N) is not None, 't183')
