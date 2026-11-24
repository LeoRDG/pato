"""Tarefa 175: os hubs ganham ar (eram salas paradas):
- Hub (Inferno): hub_brasas, brasinhas de luz subindo devagar atrás do chão;
- HubPurgatorio: a mesma névoa e cinzas da fase (purg_nevoa no fundo, purg_cinza na frente; t171);
- HubParaiso: hub_luzes, luzinhas douradas flutuando e subindo devagar.
Cada emissor segue o centro da câmera da sua camada e já nasce cheio. A ordem (z) de cada um é uma variável da cena
(<objeto>_z); cores, tempos e quantidades ficam nos emissores, editáveis no GDevelop.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t175_hubs_ambiente.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import LUZ, suaves

ids = Ids('t175')
# cena: [(objeto, camada, z)]
POR_CENA = {'Hub': [('hub_brasas', '', 1003)],
            'HubPurgatorio': [('purg_nevoa', 'fundo', 0), ('purg_cinza', '', 1070)],
            'HubParaiso': [('hub_luzes', '', 1003)]}


def migra(d):
    suaves(d, [LUZ])
    base = objeto(d, 'explosao_faiscas')
    comum = dict(rendererType='Quad', textureParticleName=LUZ, rendererParam1=128, rendererParam2=128, tank=-1,
                 emitterAngleA=0, emitterAngleB=360, particleAlpha2=0, zoneRadius=1100, additive=True,
                 destroyWhenNoParticles=False, jumpForwardInTimeOnCreation=8)
    poe_objeto(d, emissor(base, 'hub_brasas', flow=14, maxParticleNb=90, emitterForceMin=5, emitterForceMax=25,
                          particleLifeTimeMin=4, particleLifeTimeMax=7, particleColor1='255;200;90',
                          particleColor2='220;60;20', particleAlpha1=255, particleSize1=15, particleSize2=5,
                          particleGravityX=6, particleGravityY=-28, **comum), 'cenario/hubs')
    poe_objeto(d, emissor(base, 'hub_luzes', flow=6, maxParticleNb=60, emitterForceMin=4, emitterForceMax=16,
                          particleLifeTimeMin=6, particleLifeTimeMax=10, particleColor1='255;250;220',
                          particleColor2='255;215;140', particleAlpha1=230, particleSize1=18, particleSize2=7,
                          particleGravityX=3, particleGravityY=-10, **comum), 'cenario/hubs')
    for nome, lista in POR_CENA.items():
        sc = cena(d, nome)
        poe_vars(ids, sc['variables'], nome, [(f'{o}_z', z) for o, _, z in lista])
        evs = []
        for o, camada, _ in lista:
            x, y = f'CameraCenterX("{camada}", 0)', f'CameraCenterY("{camada}", 0)'
            evs += [ev([X('SceneInstancesCount', '', o, '=', '0')],
                       [X('Create', '', o, x, y, f'"{camada}"'), X('ChangePlan', o, '=', f'{o}_z')]),
                    ev([], [X('SetXY', o, '=', x, '=', y)])]
        k = next(i for i, e in enumerate(sc['events']) if e.get('name') == 'Fundo em parallax')
        sc['events'].insert(k + 1, grupo('Ambiente', evs))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'hub_brasas') is not None, 't175')
