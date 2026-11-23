"""Tarefa 127: o cutulu não fica mais travado levando tiro (postura de chefe).

Em Inimigos > Estados (terrestres), todo tiro põe o terrestre em "dano" (recuo e tomou_dano por dano_duracao s) se
ele está fora de preparar/atacar e com firme = False. Esse grupo roda antes do ataque do cutulu (grupo Purgatório),
então com cadência alta ele voltava a "dano" a todo quadro, nunca atacava, e o recuo o tirava do alcance dos golpes.
Agora, no fim de cada quadro (fora de "dano"), o cutulu fica com firme = True: tiro tira vida mas não trava. Ele só
cambaleia uma vez a cada postura_frac da vida máxima perdida (perseguindo ou patrulhando): aí firme fica False por
um quadro e o próximo acerto o põe em "dano" normalmente; ao cambalear, a conta recomeça (postura_vida).
Como o pulo de parede de Inimigos > Paredes só vale com firme = False, a folha Cutulu ganha o mesmo pulo (encostado
travado_tempo s, no chão, perseguindo).
Só adiciona variáveis e eventos; o resto fica.
Rodar uma vez:  python3 tools/t127_cutulu_postura.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARS = [('postura_frac', 'number', 0.1), ('postura_vida', 'number', 0), ('postura_pronta', 'boolean', False)]
_N = [0]


def uid():
    _N[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogo/t127/{_N[0]}'))


def X(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None, tipo='Standard'):
    e = {'type': f'BuiltinCommonInstructions::{tipo}', 'conditions': conds, 'actions': acoes}
    if tipo == 'ForEach':
        e['object'] = 'cutulu'
    if filhos:
        e['events'] = filhos
    return e


def txt(v, val, op='='): return X('StringObjectVariable', 'cutulu', v, op, f'"{val}"')
def bol(v, val):         return X('BooleanObjectVariable', 'cutulu', v, 'True' if val else 'False', '')
def setb(v, val):        return X('SetBooleanObjectVariable', 'cutulu', v, 'True' if val else 'False', '')
def setn(v, op, val):    return X('SetNumberObjectVariable', 'cutulu', v, op, val)


VIVO = bol('morto', False)
CAMBALEIA = X('BuiltinCommonInstructions::CompareNumbers', 'cutulu.postura_vida - cutulu.vida', '>=',
              'cutulu.max_vida * cutulu.postura_frac')


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cut = next(o for o in d['objects'] if o['name'] == 'cutulu')
    folha = next(x for x in d['externalEvents'] if x['name'] == 'Cutulu')
    if any(e.get('name') == 'Postura' for e in folha['events']):
        sys.exit('t127 já foi aplicada; não roda de novo.')
    for n, t, v in VARS:
        if not any(x['name'] == n for x in cut['variables']):
            cut['variables'].append({'name': n, 'persistentUuid': uid(), 'type': t, 'value': v})
    eventos = [
        {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0,
         'textG': 0, 'textR': 0}, 'comment2': '',
         'comment': 'Postura: tiro tira vida mas não trava o cutulu (firme = True no fim do quadro). A cada '
                    'postura_frac da vida máxima perdida desde o último cambaleio, perseguindo ou patrulhando, '
                    'firme fica False e o próximo acerto o faz cambalear (estado "dano" de Inimigos). Com firme, o '
                    'pulo de parede de Inimigos não vale, então ele pula aqui.'},
        ev([VIVO, bol('postura_pronta', False)],
           [setb('postura_pronta', True), setn('postura_vida', '=', 'cutulu.vida')], tipo='ForEach'),
        ev([VIVO, txt('estado', 'dano')], [setn('postura_vida', '=', 'cutulu.vida')], tipo='ForEach'),
        ev([VIVO, txt('estado', 'dano', '!=')], [setb('firme', True)], [
            ev([txt('estado', 'perseguir'), CAMBALEIA], [setb('firme', False)]),
            ev([txt('estado', 'patrulha'), CAMBALEIA], [setb('firme', False)]),
        ], tipo='ForEach'),
        ev([VIVO, txt('estado', 'perseguir'), bol('voo_manual', False),
            X('CompareObjectTimer', 'cutulu', '"travado"', '>', 'cutulu.travado_tempo'),
            X('PlatformBehavior::IsOnFloor', 'cutulu', 'PlatformerObject')],
           [X('PlatformBehavior::SimulateJumpKey', 'cutulu', 'PlatformerObject'),
            X('ResetObjectTimer', 'cutulu', '"travado"')], tipo='ForEach'),
    ]
    folha['events'].append({'type': 'BuiltinCommonInstructions::Group', 'colorB': 228, 'colorG': 176,
                            'colorR': 74, 'creationTime': 0, 'name': 'Postura', 'source': '', 'parameters': [],
                            'events': eventos})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cutulu com postura')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
