"""Tarefa 158: os anjinhos (canalizadores) vão e voltam para longe de Deus, até as bordas da tela, e o laço tem a cor da redoma.

- O vai e vem da t156 ia para dentro; agora vai para fora: o raio oscila entre canal_orbita_raio e
  canal_orbita_raio + canal_vaivem (que vai a 650 se ainda estiver no valor da t156), e a posição fica presa dentro
  da tela a canal_margem das bordas, para eles encostarem nelas sem sumir.
- O laço até Deus fica da cor da redoma (deus.escudo_cor), na linha e no brilho (Glow), posta ao criar o laço.
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t158_anjos_nas_bordas.py
"""
from gd_mig import *

ids = Ids('t158')
d_ = 'deus'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
DENTRO = '(deus.canal_orbita_raio - deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'
FORA = '(deus.canal_orbita_raio + deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [('canal_margem', 90)])
    for v in o[d_]['variables']:
        if v['name'] == 'canal_vaivem' and v.get('value') == 90:
            v['value'] = 650
    rosa = acha(acha(folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Anel rosa: amor')
    orbita = next(e for e in rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']))
    for a in orbita['actions']:
        if a['type']['value'] == 'SetXY':
            a['parameters'][2] = (f'clamp(deus.cx + cos(canalizador.ang) * {FORA}, {CX} - {CW} / 2 + deus.canal_margem,'
                                  f' {CX} + {CW} / 2 - deus.canal_margem) - canalizador.Width() / 2')
            a['parameters'][4] = (f'clamp(deus.cy + sin(canalizador.ang) * {FORA}, {CY} - {CH} / 2 + deus.canal_margem,'
                                  f' {CY} + {CH} / 2 - deus.canal_margem) - canalizador.Height() / 2')
    cria = next(e for e in rosa['events'] if '"Create"}, "parameters": ["", "laco_amor"' in tx(e['actions']))
    cria['actions'] += [X('PrimitiveDrawing::OutlineColor', 'laco_amor', 'deus.escudo_cor'),
                        X('EffectCapability::EffectBehavior::SetEffectStringParameter', 'laco_amor', 'Effect',
                          '"Effect"', '"color"', 'deus.escudo_cor')]


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'canal_margem' for v in objeto(d, 'deus')['variables']), 't158')
