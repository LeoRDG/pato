"""Tarefa 132: sem a folha Perigos. Espinhos (só o Purgatório tem) vai para o fim de CenarioPurgatorio e Poça de sangue
(só o Inferno tem) para o fim de CenarioInferno. Perigos era ligada logo depois da folha de cenário dessas cenas, então
a ordem dos eventos não muda; o link de Perigos sai de toda cena (no Teste não há espinhos nem sangue).
Só move os grupos como estão.
Rodar uma vez:  python3 tools/t132_perigos_nos_reinos.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = {'Espinhos': 'CenarioPurgatorio', 'Poça de sangue': 'CenarioInferno'}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    X = {x['name']: x for x in d['externalEvents']}
    if 'Perigos' not in X:
        sys.exit('t132 já foi aplicada; não roda de novo.')
    grupos = X['Perigos']['events']
    assert sorted(g['name'] for g in grupos) == sorted(DESTINO), [g.get('name') for g in grupos]
    for g in grupos:
        X[DESTINO[g['name']]]['events'].append(g)
    d['externalEvents'] = [x for x in d['externalEvents'] if x['name'] != 'Perigos']
    for l in d['layouts']:
        l['events'] = [e for e in l['events']
                       if not (e['type'].endswith('::Link') and e.get('target') == 'Perigos')]
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('Perigos repartida entre os cenários')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
