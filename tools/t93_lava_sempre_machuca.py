"""Tarefa 93: a lava machuca o pato o tempo todo, não só depois que a luta com o chefe chega na fase 2.

O evento do dano da lava (Chefe > Fase 2: o pato afunda mais de lava.dano_margem px, perde lava.dano_fase2 de vida e é
jogado para cima com lava.pulo_vel) tinha a condição fase2 = True. Ela sai; o resto do evento fica igual.
Os eventos Chefe só estão no Inferno, que é a única cena com lava. Rodar uma vez:  python3 tools/t93_lava_sempre_machuca.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    chefe = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')['events']
    ev = next(e for e in todos(chefe)
              if any(a['parameters'][:2] == ['pato', 'vida'] and 'lava.' in a['parameters'][3]
                     for a in e.get('actions') or []))
    antes = len(ev['conditions'])
    ev['conditions'] = [c for c in ev['conditions']
                        if not (c['type']['value'] == 'BooleanVariable' and c['parameters'][0] == 'fase2')]
    if len(ev['conditions']) == antes:
        sys.exit('t93 já foi aplicada (o dano da lava não depende de fase2); não roda de novo.')

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('lava machuca sempre')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
