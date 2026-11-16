"""Tarefa 85: a mira (alvo) não foge mais do mouse perto do pato.

O alvo ficava na linha do cano, a DistanceBetweenPositions(bocal, mouse) do bocal. Essa distância não tem sinal: com o
mouse entre o bocal e o pato (mais perto do pato que a ponta da arma) ela volta a crescer e o alvo se afastava do
pato enquanto o mouse chegava perto, até a arma virar e o alvo pular para o outro lado.
Agora o alvo fica na projeção do mouse na linha do cano (quanto o mouse está à frente do bocal nessa linha), e nunca
mais perto do bocal que alvo.dist_min: chegando perto do pato o alvo para na frente do cano em vez de fugir.

- Variáveis novas do alvo (só se faltarem): dist_min (px) e d (auxiliar, a distância usada no quadro).
- Evento Jogador > Controle das Armas > Mira e posicionamento > Cano e alvo: antes do SetXY do alvo, d = max(dist_min,
  projeção); o SetXY usa alvo.d. Só troca se o SetXY ainda for o original.
Rodar uma vez:  python3 tools/t85_alvo_projecao.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARS = dict(dist_min=60, d=0)
DIST = 'DistanceBetweenPositions(bocal_x, bocal_y, MouseX(), MouseY())'
X_VELHO = f'bocal_x + mira_lado * cos(mira_a) * {DIST} - alvo.Width() * .5'
Y_VELHO = f'bocal_y + sin(mira_a) * {DIST} - alvo.Height() * .5'
PROJ = 'max(alvo.dist_min, (MouseX() - bocal_x) * mira_lado * cos(mira_a) + (MouseY() - bocal_y) * sin(mira_a))'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def var(nome, valor):
    return {'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogos/t85/alvo/{nome}')),
            'type': 'number', 'value': valor}


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if 'alvo.dist_min' in txt:
        sys.exit('t85 já foi aplicada (alvo.dist_min já é usado); não roda de novo.')
    ev = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
    alvo_ev = next((e for e in todos(ev) for a in e.get('actions') or []
                    if a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo'), None)
    if alvo_ev is None:
        sys.exit('não achei o SetXY do alvo')
    k, acao = next((i, a) for i, a in enumerate(alvo_ev['actions'])
                   if a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo')
    p = acao['parameters']
    if (p[2], p[4]) != (X_VELHO, Y_VELHO):
        sys.exit('o SetXY do alvo foi mudado no GDevelop; não mexo:\n  %s\n  %s' % (p[2], p[4]))
    p[2] = 'bocal_x + mira_lado * cos(mira_a) * alvo.d - alvo.Width() * .5'
    p[4] = 'bocal_y + sin(mira_a) * alvo.d - alvo.Height() * .5'
    alvo_ev['actions'].insert(k, {'type': {'value': 'SetNumberObjectVariable'},
                                  'parameters': ['alvo', 'd', '=', PROJ]})

    obj = next(o for o in d['objects'] if o['name'] == 'alvo')
    tem = {v['name'] for v in obj['variables']}
    obj['variables'] += [var(n, v) for n, v in VARS.items() if n not in tem]

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('alvo na projeção do mouse, a pelo menos alvo.dist_min do bocal')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
