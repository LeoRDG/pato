"""Tarefa 154: a aura de Deus (brilho de sol e raios girando) passa a ser só efeitos.

Um Shape Painter (deus_aura_luz, com Glow e AdvancedBloom "Brilho") desenha a cada quadro, em volta do olho:
- o brilho de sol: três círculos cheios em camadas (aura_raio, aura_cam_2, aura_cam_3; opacidades aura_op_1..3; cor
  aura_brilho_cor) que respiram (aura_pulso, aura_pulso_vel);
- os raios: aura_raios_qtd triângulos pontudos com a base em aura_raios_ini (meia largura aura_raios_base) e a ponta
  em aura_raios_fim (um sim, um não mais curtos por aura_raios_curto), girando a aura_giro graus por segundo
  (cor aura_raios_cor).
O sprite antigo (deus_aura) fica escondido; a luz por fase (bloom_N) também vale para o desenho, e ele some junto
com o resto do corpo.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t154_aura_efeitos.py
"""
import copy
from gd_mig import *

ids = Ids('t154')
d_ = 'deus'
A = 'deus_aura_luz'
PD = 'PrimitiveDrawing::'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def aura():
    r = 'deus.aura_raio + deus.aura_pulso * sin(TimeFromStart() * deus.aura_pulso_vel)'
    ang = 'ToRad(deus.aura_raios_ang + deus.i * 360 / deus.aura_raios_qtd)'
    fim = 'deus.aura_raios_fim - mod(deus.i, 2) * deus.aura_raios_curto'
    meia = '(deus.aura_raios_base / deus.aura_raios_ini)'
    return grupo('Aura desenhada', [
        ev([X('SceneInstancesCount', '', d_, '>', '0')],
           [setn(d_, 'aura_raios_ang', '+', 'deus.aura_giro * TimeDelta()'),
            X(PD + 'FillColor', A, 'deus.aura_brilho_cor'), X(PD + 'OutlineSize', A, '=', '0'),
            X(PD + 'FillOpacity', A, '=', 'deus.aura_op_1'), X(PD + 'Circle', A, 'deus.cx', 'deus.cy', r),
            X(PD + 'FillOpacity', A, '=', 'deus.aura_op_2'), X(PD + 'Circle', A, 'deus.cx', 'deus.cy', f'({r}) * deus.aura_cam_2'),
            X(PD + 'FillOpacity', A, '=', 'deus.aura_op_3'), X(PD + 'Circle', A, 'deus.cx', 'deus.cy', f'({r}) * deus.aura_cam_3'),
            X(PD + 'FillColor', A, 'deus.aura_raios_cor'), X(PD + 'FillOpacity', A, '=', 'deus.aura_raios_opacidade'),
            setn(d_, 'i', '=', '0')],
           [repete('deus.aura_raios_qtd', [
               X(PD + 'BeginFillPath', A, f'deus.cx + cos({ang} - {meia}) * deus.aura_raios_ini',
                 f'deus.cy + sin({ang} - {meia}) * deus.aura_raios_ini'),
               X(PD + 'PathLineTo', A, f'deus.cx + cos({ang}) * ({fim})', f'deus.cy + sin({ang}) * ({fim})'),
               X(PD + 'PathLineTo', A, f'deus.cx + cos({ang} + {meia}) * deus.aura_raios_ini',
                 f'deus.cy + sin({ang} + {meia}) * deus.aura_raios_ini'),
               X(PD + 'closePath', A), X(PD + 'EndFillPath', A),
               setn(d_, 'i', '+', '1')])]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('aura_raio', 200), ('aura_cam_2', 0.75), ('aura_cam_3', 0.55), ('aura_op_1', 40), ('aura_op_2', 70),
        ('aura_op_3', 110), ('aura_pulso', 8), ('aura_pulso_vel', 2.5), ('aura_brilho_cor', '110;180;255'),
        ('aura_raios_qtd', 16), ('aura_raios_ini', 150), ('aura_raios_fim', 310), ('aura_raios_curto', 70),
        ('aura_raios_base', 6), ('aura_raios_cor', '255;220;130'), ('aura_raios_opacidade', 230),
        ('aura_raios_ang', 0), ('aura_giro', 20)])
    desenho = {k: v for k, v in o['laco_amor'].items() if k not in ('name', 'persistentUuid', 'effects', 'variables')}
    desenho.update(name=A, persistentUuid=ids('obj/' + A), variables=[], fillOpacity=0, outlineSize=0,
                   absoluteCoordinates=True, clearBetweenFrames=True,
                   effects=[efeito('Glow', 'Effect', {'distance': 15, 'innerStrength': 0, 'outerStrength': 2},
                                   {'color': '130;190;255'}),
                            efeito('AdvancedBloom', 'Brilho', {'threshold': 0.7, 'bloomScale': 1, 'brightness': 1,
                                                               'blur': 8, 'quality': 6, 'padding': 80})])
    poe_objeto(d, desenho, 'inimigos/chefe')

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    cria = acha(deus['events'], 'Criação')['events'][0]
    cria['actions'] += [X('Hide', 'deus_aura', ''), X('Create', '', A, '0', '0', '""'),
                        X('ChangePlan', A, '=', 'deus.z_base + 0')]
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Corpo')
    deus['events'].insert(k + 1, aura())
    for e in todos(deus['events']):
        acts = e.get('actions', [])
        novas = []
        for a in acts:
            if a['parameters'] and a['parameters'][0] == 'deus_aura' and a['type']['value'] in (
                    'EffectCapability::EffectBehavior::SetEffectDoubleParameter', 'Delete'):
                b = copy.deepcopy(a)
                b['parameters'][0] = A
                novas.append(b)
        acts += novas


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, A) is not None, 't154')
