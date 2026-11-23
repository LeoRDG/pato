"""Tarefa 113: os portais finais (final = True) só aparecem depois que o chefe final da fase morre.

Variável nova chefe_final (booleana) em todos os inimigos (grupo Inimigo): True no demonio_chefe (chefe do Inferno) e
no cutulu (chefe do Purgatório), False nos outros; dá para mudar por instância. Quando um inimigo com chefe_final
morre, a variável de cena nova chefe_final_morto vira True.
Portal ganha as variáveis liberado e aberto (False no começo). Portal com final = False fica liberado logo no
começo da cena; com chefe_final_morto = True todos ficam liberados. Um portal liberado e ainda não aberto abre (cria
o nome em cima e as partículas e passa a funcionar). Antes de abrir, o portal final fica invisível e não leva a lugar
nenhum. (Não usar "ou" com uma condição de cena e uma de objeto: quando só a de cena é verdadeira, o "ou" não
escolhe nenhum portal, as ações rodam sem portal e o evento repete todo quadro criando emissores em 0,0.)
Rodar uma vez:  python3 tools/t113_portal_final_depois_do_chefe.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEFES = ('demonio_chefe', 'cutulu')
CENAS = ('Hub', 'Inferno', 'Purgatorio', 'Paraiso', 'Teste')


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t113/' + nome))


def var(dono, nome, valor):
    return {'name': nome, 'persistentUuid': uid(f'{dono}/{nome}'), 'type': 'boolean', 'value': valor}


def x(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    evs = next(e for e in d['externalEvents'] if e['name'] == 'Portais')['events']
    if 'chefe_final_morto' in json.dumps(evs):
        sys.exit('t113 já foi aplicada; não roda de novo.')
    O = {o['name']: o for o in d['objects']}
    inimigos = next(g for g in d['objectsGroups'] if g['name'] == 'Inimigo')['objects']
    for i in inimigos:
        o = O[i['name']]
        if not any(v['name'] == 'chefe_final' for v in o['variables']):
            o['variables'].append(var(o['name'], 'chefe_final', o['name'] in CHEFES))
    portal = O['portal']
    for n in ('liberado', 'aberto'):
        if not any(v['name'] == n for v in portal['variables']):
            portal['variables'].append(var('portal', n, False))
    for l in d['layouts']:
        if l['name'] in CENAS and not any(v['name'] == 'chefe_final_morto' for v in l['variables']):
            l['variables'].append(var(l['name'], 'chefe_final_morto', False))

    # o nome em cima (começo da cena) e as partículas (DepartScene) passam para o evento "abrir"
    ev_nome = next(e for e in evs if any(c['type']['value'] == 'SceneJustBegins' for c in e.get('conditions') or []))
    fe_nome = ev_nome['events'][0]
    assert fe_nome['type'].endswith('ForEach') and fe_nome['object'] == 'portal', fe_nome
    ev_part = next(e for e in evs if [c['type']['value'] for c in e.get('conditions') or []] == ['DepartScene']
                   and e['events'][0].get('object') == 'portal')
    fe_part = ev_part['events'][0]
    fase = [a for a in fe_part['actions'] if a['parameters'][:2] == ['portal', 'fase']]
    assert len(fase) == 1, fe_part['actions']
    fe_part['actions'].remove(fase[0])          # fica só a opacidade 0, para todos os portais
    abrir_filhos = fe_part.pop('events')
    evs.remove(ev_nome)

    entra = next(e for e in evs if e['type'].endswith('ForEach')
                 and any(a['type']['value'] == 'Scene' for a in e['actions']))
    entra['conditions'].append(x('BooleanObjectVariable', 'portal', 'aberto', 'True', ''))

    fora = next(e for e in evs if e['type'].endswith('ForEach')
                and any(c['type'].get('inverted') and c['type']['value'] == 'CollisionNP' for c in e['conditions']))
    k = evs.index(fora)
    evs[k:k] = [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Portal final (final = True) só abre depois que um inimigo com chefe_final morre (chefe_final_morto). '
                    'Os outros ficam liberados logo no começo da cena. Abrir (liberado e não aberto): cria o nome em cima e '
                    'as partículas e o portal passa a funcionar (aberto).'},
        {'type': 'BuiltinCommonInstructions::Standard',
         'conditions': [x('BooleanVariable', 'chefe_final_morto', 'False', ''),
                        x('BooleanObjectVariable', 'Inimigo', 'chefe_final', 'True', ''),
                        x('BooleanObjectVariable', 'Inimigo', 'morto', 'True', '')],
         'actions': [x('SetBooleanVariable', 'chefe_final_morto', 'True', '')]},
        {'type': 'BuiltinCommonInstructions::Standard',
         'conditions': [x('BooleanObjectVariable', 'portal', 'liberado', 'False', ''),
                        x('BooleanObjectVariable', 'portal', 'final', 'False', '')],
         'actions': [x('SetBooleanObjectVariable', 'portal', 'liberado', 'True', '')]},
        {'type': 'BuiltinCommonInstructions::Standard',
         'conditions': [x('BooleanVariable', 'chefe_final_morto', 'True', '')],
         'actions': [x('SetBooleanObjectVariable', 'portal', 'liberado', 'True', '')]},
        {'type': 'BuiltinCommonInstructions::ForEach', 'object': 'portal',
         'conditions': [x('BooleanObjectVariable', 'portal', 'aberto', 'False', ''),
                        x('BooleanObjectVariable', 'portal', 'liberado', 'True', '')],
         'actions': [x('SetBooleanObjectVariable', 'portal', 'aberto', 'True', '')] + fe_nome['actions'] + fase,
         'events': abrir_filhos},
    ]

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('portais finais abrem depois do chefe')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
