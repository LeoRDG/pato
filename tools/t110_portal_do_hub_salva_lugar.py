"""Tarefa 110: o portal para o Hub salva o lugar (ponto de volta) até a fase ser terminada.

Entrar num portal que leva ao Hub (portal.cena = "Hub") numa fase guarda a posição dele na variável global nova
waypoints, um filho por fase (waypoints.<cena>: ativo, x, y). Voltando para essa fase (pelo portal do Hub ou depois
de morrer, que também leva ao Hub), o pato começa no meio do último portal usado e a câmera vai junto. O lugar só é
apagado ao entrar num portal com a variável nova final = True (marcar na instância do portal do fim de cada fase).
Para o pato não ser mandado de volta ao Hub ao aparecer dentro do portal, portal só funciona depois que o pato
esteve fora dele (variável nova armado, False no começo; vira True quando o pato não toca o portal).
Rodar uma vez:  python3 tools/t110_portal_do_hub_salva_lugar.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FASES = ('Inferno', 'Purgatorio', 'Paraiso', 'Teste')
W = 'waypoints[CurrentSceneName()]'


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t110/' + nome))


def var(dono, nome, tipo, valor, **extra):
    return dict({'name': nome, 'persistentUuid': uid(f'{dono}/{nome}'), 'type': tipo, 'value': valor}, **extra)


def x(tipo, *p, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(p)}


def ev(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acoes}
    if filhos:
        e['events'] = filhos
    return e


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(v['name'] == 'waypoints' for v in d['variables']):
        sys.exit('t110 já foi aplicada; não roda de novo.')
    d['variables'].append(var('global', 'waypoints', 'structure', None, children=[
        var(f'waypoints/{f}', f, 'structure', None, children=[
            var(f'waypoints/{f}', 'ativo', 'boolean', False), var(f'waypoints/{f}', 'x', 'number', 0),
            var(f'waypoints/{f}', 'y', 'number', 0)]) for f in FASES]))
    for v in d['variables'][-1]['children']:
        del v['value']
    del d['variables'][-1]['value']

    portal = next(o for o in d['objects'] if o['name'] == 'portal')
    nomes = {v['name'] for v in portal['variables']}
    for n in ('final', 'armado'):
        if n not in nomes:
            portal['variables'].append(var('portal', n, 'boolean', False))

    evs = next(e for e in d['externalEvents'] if e['name'] == 'Portais')['events']
    fora = next(e for e in evs if e['type'].endswith('ForEach')
                and any(c['type'].get('inverted') and c['type']['value'] == 'CollisionNP' for c in e['conditions']))
    entra = next(e for e in evs if e['type'].endswith('ForEach')
                 and any(a['type']['value'] == 'Scene' for a in e['actions']))
    fora['actions'].append(x('SetBooleanObjectVariable', 'portal', 'armado', 'True'))
    entra['conditions'].append(x('BooleanObjectVariable', 'portal', 'armado', 'True', ''))
    entra.setdefault('events', []).extend([
        ev([x('BooleanObjectVariable', 'portal', 'final', 'False', ''),
            x('StringObjectVariable', 'portal', 'cena', '=', '"Hub"'),
            x('BuiltinCommonInstructions::CompareStrings', 'CurrentSceneName()', '!=', '"Hub"')],
           [x('SetBooleanVariable', f'{W}.ativo', 'True', ''),
            x('SetNumberVariable', f'{W}.x', '=', 'portal.CenterX()'),
            x('SetNumberVariable', f'{W}.y', '=', 'portal.CenterY()')]),
        ev([x('BooleanObjectVariable', 'portal', 'final', 'True', '')],
           [x('SetBooleanVariable', f'{W}.ativo', 'False', '')]),
    ])
    # volta para o último portal: antes dos outros eventos de portal (no primeiro quadro o pato já toca o portal)
    k = evs.index(fora)
    evs[k:k] = [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Ponto de volta: entrar numa fase num portal para o Hub guarda o lugar em waypoints.<fase>; voltando '
                    'para a fase (pelo Hub ou depois de morrer), o pato começa nele. Portal com final = True (o do fim '
                    'da fase) apaga o lugar. Portal só funciona depois que o pato esteve fora dele (armado).'},
        ev([x('DepartScene', ''), x('BooleanVariable', f'{W}.ativo', 'True', '')],
           [x('SetX', 'pato', '=', f'{W}.x - pato.Width() / 2'),
            x('SetY', 'pato', '=', f'{W}.y - pato.Height() / 2'),
            x('SetCameraCenterX', '', '=', 'pato.CenterX()', '""', '0'),
            x('SetCameraCenterY', '', '=', 'pato.CenterY()', '""', '0')]),
    ]

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('portal do Hub salva o lugar')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
