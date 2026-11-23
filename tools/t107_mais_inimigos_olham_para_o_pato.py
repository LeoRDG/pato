"""Tarefa 107: mais inimigos que ficavam de costas para o pato.

Vistos na cena Teste: condenado em chamas, cabeça voadora e diabinho olham para a esquerda no desenho, mas estavam
com sprite_esquerda False; passam a True. O mercador (trader) olha para a direita (sprite_esquerda continua False), mas
não está em Terrestre nem em Voador, então nada o virava: entra no fim do grupo Loja > Mercador um "para cada" trader vivo que vira para o lado do pato com as
mesmas regras de sprite_esquerda dos outros.
Rodar uma vez:  python3 tools/t107_mais_inimigos_olham_para_o_pato.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLHAM_ESQUERDA = ('condenado_em_chamas', 'cabeca_voadora', 'diabinho')
TR = 'trader'


def c(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def vira(esq, op, flip):
    return {'type': 'BuiltinCommonInstructions::Standard',
            'conditions': [c('BooleanObjectVariable', TR, 'sprite_esquerda', esq, ''),
                           c('BuiltinCommonInstructions::CompareNumbers', 'pato.CenterX()', op, f'{TR}.CenterX()')],
            'actions': [{'type': {'value': 'FlippableCapability::FlippableBehavior::FlipX'},
                         'parameters': [TR, 'Flippable', flip]}]}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    loja = next(x for x in d['externalEvents'] if x['name'] == 'Loja')['events']
    m = next(e for e in loja if e.get('name') == 'Mercador')
    if any(e['type'].endswith('ForEach') and e.get('object') == TR and 'FlipX' in json.dumps(e) for e in m['events']):
        sys.exit('t107 já foi aplicada; não roda de novo.')
    for o in d['objects']:
        if o['name'] in OLHAM_ESQUERDA:
            next(v for v in o['variables'] if v['name'] == 'sprite_esquerda')['value'] = True
    m['events'].append({
        'type': 'BuiltinCommonInstructions::ForEach', 'object': TR,
        'conditions': [c('BooleanObjectVariable', TR, 'morto', 'False', '')], 'actions': [],
        'events': [vira('True', '>', 'yes'), vira('True', '<', 'no'), vira('False', '<', 'yes'), vira('False', '>', 'no')]})
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('olham para o pato:', OLHAM_ESQUERDA)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
