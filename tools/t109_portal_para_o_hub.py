"""Tarefa 109: portal que leva ao Hub, para pôr em qualquer cena.

Os eventos dos portais (gatilho, nome em cima, partículas) estavam só no Hub (grupo Portais da cena). Passam, iguais,
para eventos externos novos "Portais", ligados no mesmo lugar do Hub e também no Inferno, Purgatorio, Paraiso e
Teste: um portal posto em qualquer uma dessas cenas funciona. O evento de cair da borda do Hub (queda_y, volta_x,
volta_y são variáveis do Hub) fica no Hub, logo depois da ligação. Os valores padrão do objeto portal passam a ser os do
portal do Hub (cena e nome "Hub", cores roxo e lilás); os três portais do Hub já têm cena, nome e cores próprios nas
instâncias, então não mudam. Para pôr um portal para o Hub: arrastar o objeto portal para a cena, nada mais.
Rodar uma vez:  python3 tools/t109_portal_para_o_hub.py
"""
import copy, json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENAS = ('Inferno', 'Purgatorio', 'Paraiso', 'Teste')
PADRAO = {'cena': 'Hub', 'nome': 'Hub', 'cor_borda': '120;70;200', 'cor_centro': '240;225;255'}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(x['name'] == 'Portais' for x in d['externalEvents']):
        sys.exit('t109 já foi aplicada; não roda de novo.')
    L = {l['name']: l for l in d['layouts']}
    hub = L['Hub']
    k = next(i for i, e in enumerate(hub['events']) if e.get('name') == 'Portais')
    grupo = hub['events'][k]
    queda = [e for e in grupo['events'] if 'queda_y' in json.dumps(e.get('conditions') or [])]
    assert len(queda) == 1, queda
    d['externalEvents'].append({'associatedLayout': 'Hub', 'lastChangeTimeStamp': 0, 'name': 'Portais',
                                'events': [e for e in grupo['events'] if e is not queda[0]]})
    molde = next(e for e in hub['events'] if e['type'].endswith('Link'))
    link = copy.deepcopy(molde)
    link['target'] = 'Portais'
    hub['events'][k:k + 1] = [copy.deepcopy(link),
                              {'type': 'BuiltinCommonInstructions::Comment',
                               'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
                               'comment': 'Cair da borda do Hub (passar de queda_y) volta o pato para volta_x/volta_y.'},
                              queda[0]]
    for nome in CENAS:
        evs = L[nome]['events']
        if not any(e.get('target') == 'Portais' for e in evs):
            ultimo = max(i for i, e in enumerate(evs) if e['type'].endswith('Link'))
            evs.insert(ultimo + 1, copy.deepcopy(link))

    portal = next(o for o in d['objects'] if o['name'] == 'portal')
    for v in portal['variables']:
        if v['name'] in PADRAO:
            v['value'] = PADRAO[v['name']]
    # os portais do Hub precisam ter os próprios valores na instância (senão herdariam o padrão novo)
    for i in hub['instances']:
        if i['name'] == 'portal':
            nomes = {v['name'] for v in i['initialVariables']}
            assert set(PADRAO) <= nomes, (i['persistentUuid'], nomes)

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('portais em eventos externos; portal padrão leva ao Hub')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
