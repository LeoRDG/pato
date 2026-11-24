"""Tarefa 177: brasas subindo pela fase do Inferno (antes o ar era parado; só o hub tinha brasas, t175).

inferno_brasas: brasinhas de luz (particula_luz, aditivas) que sobem devagar e somem, espalhadas pela tela,
seguindo o centro da câmera e já cheias ao entrar. Ficam atrás do pato e na frente do fundo: inferno_brasas_z
(variável da cena). Cores, quantidade e velocidade ficam no emissor. Não é brilho de lava (test_lava).
Rodar uma vez:  python3 tools/t177_inferno_brasas.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import LUZ, suaves

ids = Ids('t177')
B = 'inferno_brasas'


def migra(d):
    suaves(d, [LUZ])
    poe_objeto(d, emissor(objeto(d, 'hub_brasas'), B, flow=16, maxParticleNb=110, particleSize1=16,
                          particleSize2=5, particleGravityY=-40, particleColor1='255;220;120',
                          particleColor2='230;70;20', jumpForwardInTimeOnCreation=8), 'cenario/inferno')
    sc = cena(d, 'Inferno')
    poe_vars(ids, sc['variables'], 'Inferno', [(f'{B}_z', 2000)])
    x, y = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)'
    evs = [ev([X('SceneInstancesCount', '', B, '=', '0')],
              [X('Create', '', B, x, y, '""'), X('ChangePlan', B, '=', f'{B}_z')]),
           ev([], [X('SetXY', B, '=', x, '=', y)])]
    k = next(i for i, e in enumerate(sc['events']) if e.get('name') == 'Fundo em parallax')
    sc['events'].insert(k + 1, grupo('Brasas no ar', evs))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, B) is not None, 't177')
