"""Tarefa 88: a mira volta a sentir o recuo, continuando no mouse.

Com o alvo preso no mouse (t87) o recuo só girava o desenho da arma: o tiro vai do bocal para o alvo, então nem o
tiro nem a mira subiam mais. Agora o alvo é o mouse girado em volta da mão do pato pelo mesmo ângulo que o recuo gira a
arma: sem recuo fica exatamente no mouse; atirando, sobe junto com a arma e volta conforme recuo decai, e o tiro vai
para ele.
- Variável nova do alvo (só se faltar): giro (radianos; quanto o recuo gira a mira neste quadro).
- Evento Cano e alvo: antes do SetXY, alvo.giro = -mira_lado * ToRad(recuo); o SetXY gira o mouse por alvo.giro em
  volta de (pato.CenterX(), pato.Y() + pato.Height() * 0.68), o mesmo ponto em que a arma gira.
Rodar uma vez:  python3 tools/t88_alvo_recuo.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_VELHO, Y_VELHO = 'MouseX() - alvo.Width() * .5', 'MouseY() - alvo.Height() * .5'
PX, PY = 'pato.CenterX()', '(pato.Y() + pato.Height() * 0.68)'
X_NOVO = (f'{PX} + (MouseX() - {PX}) * cos(alvo.giro) - (MouseY() - {PY}) * sin(alvo.giro) - alvo.Width() * .5')
Y_NOVO = (f'{PY} + (MouseX() - {PX}) * sin(alvo.giro) + (MouseY() - {PY}) * cos(alvo.giro) - alvo.Height() * .5')
GIRO = '-mira_lado * ToRad(recuo)'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if 'alvo.giro' in txt:
        sys.exit('t88 já foi aplicada (alvo.giro já é usado); não roda de novo.')
    ev = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
    e = next(e for e in todos(ev) if any(a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo'
                                         for a in e.get('actions') or []))
    k, acao = next((i, a) for i, a in enumerate(e['actions'])
                   if a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo')
    if (acao['parameters'][2], acao['parameters'][4]) != (X_VELHO, Y_VELHO):
        sys.exit('o SetXY do alvo foi mudado no GDevelop; não mexo:\n  %s\n  %s' % (acao['parameters'][2],
                                                                                acao['parameters'][4]))
    acao['parameters'][2], acao['parameters'][4] = X_NOVO, Y_NOVO
    e['actions'].insert(k, {'type': {'value': 'SetNumberObjectVariable'}, 'parameters': ['alvo', 'giro', '=', GIRO]})
    obj = next(o for o in d['objects'] if o['name'] == 'alvo')
    if not any(v['name'] == 'giro' for v in obj['variables']):
        obj['variables'].append({'name': 'giro', 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t88/alvo/giro')),
                                 'type': 'number', 'value': 0})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('alvo no mouse, girado pelo recuo')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
