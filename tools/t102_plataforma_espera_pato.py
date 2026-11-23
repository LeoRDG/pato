"""Tarefa 102: plataforma móvel que só começa a andar depois que o pato pisa nela.

Variável nova em plataforma_movel: espera_pato (False; ligada, a plataforma fica parada no começo do caminho até o pato
pisar nela pela primeira vez) e pisar_folga (8 px). Conta como pisar: o pato no chão, em cima dela na horizontal e com o pé entre
pisar_folga px acima do topo da imagem e o meio da plataforma (a máscara de colisão começa abaixo do topo da imagem,
então o pé não fica exatamente em Y()). Variável nova sincronia (texto, vazio): o pato pisando numa plataforma que espera solta também todas as que
esperam com a mesma sincronia (não vazia), e elas saem juntas. No Inferno, a plataforma do caminho
8567,184 -> 12000,184 (a mais perto do pato no começo da cena) e a que desce (7763,-2595 -> 11200,0), que já andam no
mesmo ritmo, ganham espera_pato = True e sincronia = "ponte_inferno" na instância. Variável de cena nova
plataforma_solta (texto) nas cenas com Plataformas: a sincronia da última plataforma solta. Nos eventos Plataformas: a fase só anda com espera_pato False, e um "para cada"
plataforma com espera_pato True desliga a espera quando o pato está no chão em cima dela.
Rodar uma vez:  python3 tools/t102_plataforma_espera_pato.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = 'plataforma_movel'
INSTANCIAS = ('f6969b04-1cf9-4777-8f56-c3cc745da697',   # a do caminho 8567,184 -> 12000,184
              'de54b77f-e6e5-4d90-a00c-b89991c0fb9c')   # a que desce, 7763,-2595 -> 11200,0
SINCRONIA = 'ponte_inferno'
NUM = 'BuiltinCommonInstructions::CompareNumbers'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def c(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def a(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def var(nome, tipo, valor, chave):
    return {'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t102/' + chave)),
            'type': tipo, 'value': valor}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if 'espera_pato' in texto:
        sys.exit('t102 já foi aplicada; não roda de novo.')
    pl = next(x for x in d['externalEvents'] if x['name'] == 'Plataformas')['events']
    g = next(e for e in pl if e.get('name') == 'Plataformas móveis')
    anda = [e for e in todos(g['events'])
            if json.dumps(e.get('conditions')) == json.dumps([c('CompareObjectTimer', P, '"parada"', '>', f'{P}.espera')])]
    assert len(anda) == 1, len(anda)
    anda[0]['conditions'].insert(0, c('BooleanObjectVariable', P, 'espera_pato', 'False', ''))
    k = g['events'].index(anda[0]) if anda[0] in g['events'] else 1
    g['events'].insert(k, {
        'type': 'BuiltinCommonInstructions::ForEach', 'object': P,
        'conditions': [c('BooleanObjectVariable', P, 'espera_pato', 'True', ''),
                       c('PlatformBehavior::IsOnFloor', 'pato', 'PlatformerObject'),
                       c(NUM, 'pato.Y() + pato.Height()', '>', f'{P}.Y() - {P}.pisar_folga'),
                       c(NUM, 'pato.Y() + pato.Height()', '<', f'{P}.CenterY()'),
                       c(NUM, 'pato.X() + pato.Width()', '>', f'{P}.X()'),
                       c(NUM, 'pato.X()', '<', f'{P}.X() + {P}.Width()')],
        'actions': [a('SetBooleanObjectVariable', P, 'espera_pato', 'False', ''),
                    a('ResetObjectTimer', P, '"parada"'),
                    a('SetStringVariable', 'plataforma_solta', '=', f'{P}.sincronia')]})
    g['events'].insert(k + 1, {
        'type': 'BuiltinCommonInstructions::Standard',
        'conditions': [c('BooleanObjectVariable', P, 'espera_pato', 'True', ''),
                       c('StringObjectVariable', P, 'sincronia', '!=', '""'),
                       c('StringObjectVariable', P, 'sincronia', '=', 'VariableString(plataforma_solta)')],
        'actions': [a('SetBooleanObjectVariable', P, 'espera_pato', 'False', ''),
                    a('ResetObjectTimer', P, '"parada"')]})
    com = next(e for e in pl if e['type'].endswith('Comment'))
    com['comment'] += (' Com espera_pato ligada a plataforma fica parada no começo até o pato pisar nela pela primeira vez '
                       '(no chão, em cima dela, com o pé entre pisar_folga px acima do topo e o meio dela); as que esperam com a mesma '
                       'sincronia saem junto.')

    obj = next(o for o in d['objects'] if o['name'] == P)
    obj['variables'].append(var('espera_pato', 'boolean', False, 'espera_pato'))
    obj['variables'].append(var('pisar_folga', 'number', 8, 'pisar_folga'))
    obj['variables'].append(var('sincronia', 'string', '', 'sincronia'))
    inf = next(l for l in d['layouts'] if l['name'] == 'Inferno')
    for u in INSTANCIAS:
        inst = next(i for i in inf['instances'] if i.get('persistentUuid') == u)
        assert inst['name'] == P, inst['name']
        inst.setdefault('initialVariables', []).extend([var('espera_pato', 'boolean', True, u + '/espera_pato'),
                                                        var('sincronia', 'string', SINCRONIA, u + '/sincronia')])
    for l in d['layouts']:
        if any(e.get('target') == 'Plataformas' for e in l['events']) and \
                not any(v['name'] == 'plataforma_solta' for v in l['variables']):
            l['variables'].append(var('plataforma_solta', 'string', '', l['name'] + '/plataforma_solta'))

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('plataforma espera o pato pisar')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
