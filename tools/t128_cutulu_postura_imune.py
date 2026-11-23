"""Tarefa 128: depois de cambalear, o cutulu fica postura_imune s sem poder cambalear de novo.

A postura (t127) deixava cambalear a cada postura_frac da vida perdida, sem espera; com dano por segundo alto isso
vinha a cada fração de segundo e ele continuava travado. Agora cambalear também exige o cronômetro "cambaleio" acima
de postura_imune (3 s), zerado ao cambalear e quando a postura começa.
Só adiciona; rodar uma vez:  python3 tools/t128_cutulu_postura_imune.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cut = next(o for o in d['objects'] if o['name'] == 'cutulu')
    if any(v['name'] == 'postura_imune' for v in cut['variables']):
        sys.exit('t128 já foi aplicada; não roda de novo.')
    cut['variables'].append({'name': 'postura_imune', 'type': 'number', 'value': 3,
                             'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogo/t128/1'))})
    folha = next(x for x in d['externalEvents'] if x['name'] == 'Cutulu')
    post = next(e for e in folha['events'] if e.get('name') == 'Postura')
    zera = {'type': {'value': 'ResetObjectTimer'}, 'parameters': ['cutulu', '"cambaleio"']}
    espera = {'type': {'value': 'CompareObjectTimer'}, 'parameters': ['cutulu', '"cambaleio"', '>',
                                                                      'cutulu.postura_imune']}
    feitos = 0
    for e in post['events']:
        s = json.dumps(e.get('actions', []))
        if '"postura_pronta", "True"' in s or ('"postura_vida", "="' in s and any(c['parameters'][1:] == ['estado', '=', '"dano"']
                                                for c in e['conditions'])):
            e['actions'].append(dict(zera))
            feitos += 1
        for f in e.get('events') or []:
            if '"firme", "False"' in json.dumps(f['actions']):
                f['conditions'].append(dict(espera))
                feitos += 1
    assert feitos == 4, feitos
    post['events'][0]['comment'] += (' Depois de cambalear fica postura_imune s sem poder cambalear de novo '
                                     '(cronômetro "cambaleio").')
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('postura com espera')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
