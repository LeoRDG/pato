"""Tarefa 99: inimigos mais resistentes, com um botão só.

Variável global nova vida_inimigos_mult (2). No "Preparar inimigos", quando cada inimigo é preparado (no começo da cena
ou ao ser criado depois), max_vida *= vida_inimigos_mult e vida = vida_controle = max_vida. O demônio chefe e o
mercador (trader) ficam de fora. Os valores de vida de cada inimigo no GDevelop não mudam; o multiplicador vale por
cima deles (e o que usa max_vida, como o frenesi e a fúria, acompanha).
Rodar uma vez:  python3 tools/t99_vida_inimigos_mult.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I = 'Inimigo'
FORA = ('demonio_chefe', 'trader')


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if 'vida_inimigos_mult' in texto:
        sys.exit('t99 já foi aplicada; não roda de novo.')
    d['variables'].append({'name': 'vida_inimigos_mult', 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t99/mult')),
                           'type': 'number', 'value': 2})
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    prep = next(e for e in ini if e.get('name') == 'Preparar inimigos')
    uma_vez = next(e for e in prep['events'] if e['type'].endswith('ForEach')
                   and '"preparado", "False"' in json.dumps(e['conditions']))
    uma_vez.setdefault('events', []).append({
        'type': 'BuiltinCommonInstructions::Standard',
        'conditions': [{'type': {'value': 'BuiltinCommonInstructions::CompareStrings'},
                        'parameters': [f'{I}.ObjectName()', '!=', f'"{n}"']} for n in FORA],
        'actions': [
            {'type': {'value': 'SetNumberObjectVariable'}, 'parameters': [I, 'max_vida', '*', 'GlobalVariable(vida_inimigos_mult)']},
            {'type': {'value': 'SetNumberObjectVariable'}, 'parameters': [I, 'vida', '=', f'{I}.max_vida']},
            {'type': {'value': 'SetNumberObjectVariable'}, 'parameters': [I, 'vida_controle', '=', f'{I}.vida']}]})
    for c in prep['events']:
        if c['type'].endswith('Comment'):
            c['comment'] += (' Ao preparar cada inimigo (menos o demônio chefe e o mercador), a vida é multiplicada por '
                             'vida_inimigos_mult (global).')
            break
    else:
        prep['events'].insert(0, {'type': 'BuiltinCommonInstructions::Comment',
                                  'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
                                  'comment': 'Ao preparar cada inimigo (menos o demônio chefe e o mercador), a vida é '
                                             'multiplicada por vida_inimigos_mult (global).'})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('vida dos inimigos multiplicada por vida_inimigos_mult')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
