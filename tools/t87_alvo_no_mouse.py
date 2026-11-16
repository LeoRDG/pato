"""Tarefa 87: a mira (alvo) fica exatamente no mouse.

A t85 punha o alvo na projeção do mouse na linha do cano, a pelo menos alvo.dist_min do bocal; ainda assim o alvo não
ficava onde o mouse está. Agora o alvo é só o mouse (centrado nele), sem restrição nenhuma. A arma continua mirando
para o mouse e o tiro vai na direção do alvo.
- SetXY do alvo: MouseX()/MouseY() menos metade do tamanho do alvo; sai o cálculo de alvo.d.
- Saem as variáveis dist_min e d do alvo (criadas pela t85, sem uso agora).
Rodar uma vez:  python3 tools/t87_alvo_no_mouse.py
"""
import json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_NOVO, Y_NOVO = 'MouseX() - alvo.Width() * .5', 'MouseY() - alvo.Height() * .5'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    ev = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
    e = next(e for e in todos(ev) if any(a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo'
                                         for a in e.get('actions') or []))
    acao = next(a for a in e['actions'] if a['type']['value'] == 'SetXY' and a['parameters'][0] == 'alvo')
    if (acao['parameters'][2], acao['parameters'][4]) == (X_NOVO, Y_NOVO):
        sys.exit('t87 já foi aplicada (o alvo já está no mouse); não roda de novo.')
    acao['parameters'][2], acao['parameters'][4] = X_NOVO, Y_NOVO
    e['actions'] = [a for a in e['actions']
                    if not (a['type']['value'] == 'SetNumberObjectVariable' and a['parameters'][:2] == ['alvo', 'd'])]
    eventos = json.dumps([x['events'] for x in d['externalEvents'] + d['layouts']], ensure_ascii=False)
    obj = next(o for o in d['objects'] if o['name'] == 'alvo')
    obj['variables'] = [v for v in obj['variables'] if v['name'] not in ('dist_min', 'd')
                        or re.search(r'alvo\.' + v['name'] + r'\b', eventos)]

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('alvo no mouse')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
