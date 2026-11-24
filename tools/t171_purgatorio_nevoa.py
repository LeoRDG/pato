"""Tarefa 171: o Purgatório ganha ar. Era uma névoa pintada e parada; agora há:
- purg_nevoa: tufos grandes e transparentes de névoa (particula_fumaca) que passam devagar, na camada Fundo, entre a
  névoa pintada (z -1) e a decoração (z 1): purg_nevoa_z;
- purg_cinza: cinzas pequenas caindo devagar na frente de tudo (purg_cinza_z), na camada do jogo.
O tamanho da névoa vem do particleSize (em %): a textura é desenhada no tamanho dela (128 px), o runtime ignora
rendererParam. Os dois seguem o centro da câmera da sua camada e já nascem cheios (jumpForwardInTimeOnCreation). Cores, tempos e
quantidades ficam nos próprios emissores, editáveis no GDevelop.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t171_purgatorio_nevoa.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import FUMACA, suaves

ids = Ids('t171')
N, C = 'purg_nevoa', 'purg_cinza'


def migra(d):
    base = objeto(d, 'poeira')
    suaves(d, [FUMACA])
    poe_objeto(d, emissor(base, N, rendererType='Quad', textureParticleName=FUMACA, rendererParam1=128,
                          rendererParam2=128, tank=-1, flow=1.5, maxParticleNb=30, emitterAngleB=360,
                          emitterForceMin=15, emitterForceMax=45, particleLifeTimeMin=8, particleLifeTimeMax=12,
                          particleColor1='238;242;235', particleColor2='215;225;215', particleAlpha1=95,
                          particleAlpha2=0, particleSize1=860, particleSize2=1300, particleGravityX=6,
                          particleGravityY=-2, zoneRadius=1100, additive=False, destroyWhenNoParticles=False,
                          jumpForwardInTimeOnCreation=10), 'cenario/purgatorio')
    poe_objeto(d, emissor(base, C, rendererType='Point', rendererParam1=2, rendererParam2=1, tank=-1, flow=14,
                          maxParticleNb=140, emitterAngleB=360, emitterForceMin=5, emitterForceMax=30,
                          particleLifeTimeMin=6, particleLifeTimeMax=9, particleColor1='225;225;215',
                          particleColor2='160;165;155', particleAlpha1=200, particleAlpha2=0, particleSize1=100,
                          particleSize2=100, particleGravityX=8, particleGravityY=18, zoneRadius=1100,
                          additive=False, destroyWhenNoParticles=False, jumpForwardInTimeOnCreation=8),
               'cenario/purgatorio')
    sc = cena(d, 'Purgatorio')
    poe_vars(ids, sc['variables'], 'Purgatorio', [('purg_nevoa_z', 0), ('purg_cinza_z', 3020)])
    cam = {N: ('"Fundo"', 'CameraCenterX("Fundo", 0)', 'CameraCenterY("Fundo", 0)'),
           C: ('""', 'CameraCenterX("", 0)', 'CameraCenterY("", 0)')}
    evs = []
    for o, (camada, x, y) in cam.items():
        evs += [ev([X('SceneInstancesCount', '', o, '=', '0')],
                   [X('Create', '', o, x, y, camada), X('ChangePlan', o, '=', f'{o}_z')]),
                ev([], [X('SetXY', o, '=', x, '=', y)])]
    k = next(i for i, e in enumerate(sc['events']) if e.get('name') == 'Fundo em parallax')
    sc['events'].insert(k + 1, grupo('Névoa e cinzas', evs))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, N) is not None, 't171')
