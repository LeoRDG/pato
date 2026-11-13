"""Tarefa 36: bunny hop do pato.

Pular logo depois de pousar (até pato.bhop_janela s no chão, o buffer de pulo conta) andando rápido (pelo menos bhop_vel_min
da velocidade base) soma um na série (até bhop_max_serie). Cada degrau aumenta a velocidade máxima em bhop_ganho da base,
e o pato sai do pulo já nessa velocidade. Ficar no chão mais que bhop_janela zera a série e volta a velocidade base.

- A velocidade base (bhop_vel_base) é lida do comportamento enquanto a série é zero e fora do dash, então já inclui o
  upgrade de velocidade e qualquer mudança feita à mão no maxSpeed do pato.
- Nada é mexido durante o dash (a pilha de configuração do dash restaura a velocidade sozinha).
- Sair do chão sem pular (coice do soco, cair de uma borda) não conta como bunny hop.
Só ADICIONA: variáveis que já existem mantêm o valor; o grupo só é criado se ainda não existe.
Rodar:  python3 tools/t36_bunny_hop.py   (uma vez). Feche o projeto no GDevelop antes.
"""
import json, uuid
from t12_armas import A, C, E, PATH, comentario, grupo

PL = ('pato', 'PlatformerObject')
GRUPO = 'Bunny hop'

VARS = [  # (nome, tipo, valor inicial)
    ('bhop_janela', 'number', 0.1),       # s no chão em que o pulo ainda conta como bunny hop
    ('bhop_ganho', 'number', 0.12),       # fração da velocidade base somada por degrau
    ('bhop_max_serie', 'number', 5),      # degraus no máximo (5 x 0.12 = +60%)
    ('bhop_vel_min', 'number', 0.8),      # fração da velocidade base para o pulo contar
    ('bhop_serie', 'number', 0),          # estado: degrau atual
    ('bhop_vel_base', 'number', 0),       # estado: maxSpeed sem bunny hop
    ('bhop_no_chao', 'boolean', False),   # estado: estava no chão no quadro anterior
]

VEL = 'pato.bhop_vel_base * (1 + pato.bhop_ganho * pato.bhop_serie)'


def eventos():
    nao_dash = C('AdvancedJump::HorizontalDash::IsDashing', 'pato', 'HorizontalDash', '', inv=True)
    return [
        comentario('Bunny hop: pular até bhop_janela s depois de pousar, andando a pelo menos bhop_vel_min da velocidade base, '
                   'sobe a série (até bhop_max_serie) e a velocidade máxima ganha bhop_ganho da base por degrau. '
                   'Ficar no chão mais que bhop_janela zera. Fora do dash; sair do chão sem pular não conta.'),
        # base: maxSpeed do comportamento (com upgrades) enquanto não há série
        E([C('NumberObjectVariable', 'pato', 'bhop_serie', '=', '0'), nao_dash],
          [A('SetNumberObjectVariable', 'pato', 'bhop_vel_base', '=', 'pato.PlatformerObject::MaxSpeed()')]),
        # pousou
        E([C('PlatformBehavior::IsOnFloor', *PL), C('BooleanObjectVariable', 'pato', 'bhop_no_chao', 'False', '')],
          [A('SetBooleanObjectVariable', 'pato', 'bhop_no_chao', 'True', ''), A('ResetObjectTimer', 'pato', '"bhop_chao"')]),
        # saiu do chão
        E([C('PlatformBehavior::IsOnFloor', *PL, inv=True), C('BooleanObjectVariable', 'pato', 'bhop_no_chao', 'True', '')],
          [A('SetBooleanObjectVariable', 'pato', 'bhop_no_chao', 'False', '')],
          [E([C('PlatformBehavior::IsJumping', *PL),
              C('CompareObjectTimer', 'pato', '"bhop_chao"', '<=', 'pato.bhop_janela'),
              C('BuiltinCommonInstructions::CompareNumbers', 'abs(pato.PlatformerObject::CurrentSpeed())', '>=',
                'pato.bhop_vel_base * pato.bhop_vel_min'),
              C('BooleanObjectVariable', 'pato', 'morto', 'False', ''), nao_dash],
             [A('SetNumberObjectVariable', 'pato', 'bhop_serie', '=', 'min(pato.bhop_max_serie, pato.bhop_serie + 1)'),
              A('PlatformBehavior::MaxSpeed', *PL, '=', VEL),
              A('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', *PL, '=',
                f'sign(pato.PlatformerObject::CurrentSpeed()) * {VEL}')])]),
        # ficou no chão: zera
        E([C('PlatformBehavior::IsOnFloor', *PL),
           C('CompareObjectTimer', 'pato', '"bhop_chao"', '>', 'pato.bhop_janela'),
           C('NumberObjectVariable', 'pato', 'bhop_serie', '>', '0'), nao_dash],
          [A('SetNumberObjectVariable', 'pato', 'bhop_serie', '=', '0'),
           A('PlatformBehavior::MaxSpeed', *PL, '=', 'pato.bhop_vel_base')]),
    ]


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    pato = next(o for o in d['objects'] if o['name'] == 'pato')
    tem = {v['name'] for v in pato['variables']}
    for nome, tipo, valor in VARS:
        if nome not in tem:
            pato['variables'].append({'name': nome, 'persistentUuid': str(uuid.uuid4()), 'type': tipo, 'value': valor})

    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    if not any(e.get('name') == GRUPO for e in walk(jog['events'])):
        ctrl = next(e for e in walk(jog['events']) if e.get('name') == 'Controle do Pato')
        i = next(k for k, e in enumerate(ctrl['events']) if e.get('name') == 'Sensação do pato')
        ctrl['events'].insert(i + 1, grupo(GRUPO, eventos()))

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
