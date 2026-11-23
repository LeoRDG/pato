"""Tarefa 98: os inimigos acordam quando VEEM o pato, não por um raio fixo.

Antes: patrulha -> perseguir com o pato a menos de aggro_dist (perseguir_dist na mina), e desistiam a mais de
desiste_dist. Agora:
- grupo "Visão" no começo dos Inimigos: para cada inimigo vivo, ve_pato = está na tela (centro dentro da câmera) e
  nenhum Terreno entre o centro dele e o do pato (raio); estando na tela, zera o cronômetro "na_tela";
- terrestres, voadores e roda do anjo acordam com ve_pato e desistem depois de perde_tempo s fora da tela;
- árvore condenada só atira e mina demoníaca só vem atrás vendo o pato.
Variáveis novas em cada inimigo do grupo Inimigo: ve_pato (False) e perde_tempo (2). Variáveis de cena novas onde há
Inimigos: visao_rx, visao_ry (ponto do raio). Saem aggro_dist, desiste_dist e perseguir_dist, que ficam sem uso.
Rodar uma vez:  python3 tools/t98_inimigos_veem_o_pato.py
"""
import json, os, re, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I = 'Inimigo'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def acao(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def cond(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None, tipo='Standard', obj=None):
    e = {'type': 'BuiltinCommonInstructions::' + tipo, 'conditions': conds, 'actions': acoes}
    if obj:
        e['object'] = obj
    if filhos:
        e['events'] = filhos
    return e


def var(nome, tipo, valor, chave):
    return {'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t98/' + chave)),
            'type': tipo, 'value': valor}


NUM = 'BuiltinCommonInstructions::CompareNumbers'
VISAO = {
    'type': 'BuiltinCommonInstructions::Group', 'name': 'Visão', 'source': '', 'creationTime': 0,
    'events': [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 've_pato = o inimigo está na tela (centro dentro da câmera) e nenhum Terreno entre ele e o pato. '
                    'Na tela, zera o cronômetro "na_tela" (quem fica perde_tempo s fora da tela desiste).'},
        ev([cond('BooleanObjectVariable', I, 'morto', 'False', '')],
           [acao('SetBooleanObjectVariable', I, 've_pato', 'False', '')],
           [ev([cond(NUM, f'{I}.CenterX()', '>', 'CameraBorderLeft("")'),
                cond(NUM, f'{I}.CenterX()', '<', 'CameraBorderRight("")'),
                cond(NUM, f'{I}.CenterY()', '>', 'CameraBorderTop("")'),
                cond(NUM, f'{I}.CenterY()', '<', 'CameraBorderBottom("")')],
               [acao('ResetObjectTimer', I, '"na_tela"'),
                acao('SetBooleanObjectVariable', I, 've_pato', 'True', '')],
               [ev([cond('RaycastToPosition', 'Terreno', f'{I}.CenterX()', f'{I}.CenterY()', 'pato.CenterX()',
                         'pato.CenterY()', 'visao_rx', 'visao_ry', '')],
                   [acao('SetBooleanObjectVariable', I, 've_pato', 'False', '')])])],
           tipo='ForEach', obj=I)]}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    if any(e.get('name') == 'Visão' for e in todos(ini)):
        sys.exit('t98 já foi aplicada (grupo Visão existe); não roda de novo.')

    trocas = 0
    for e in todos(ini):
        for c in e.get('conditions') or []:
            t, p = c['type'], c['parameters']
            if t['value'] != 'Distance' or p[1] != 'pato':
                continue
            dono = p[0]
            if re.fullmatch(rf'{dono}\.(aggro_dist|perseguir_dist)', p[2]) and not t.get('inverted'):
                c['type'] = {'value': 'BooleanObjectVariable'}
                c['parameters'] = [dono, 've_pato', 'True', '']
                trocas += 1
            elif p[2] == f'{dono}.desiste_dist' and t.get('inverted'):
                c['type'] = {'value': 'CompareObjectTimer'}
                c['parameters'] = [dono, '"na_tela"', '>', f'{dono}.perde_tempo']
                trocas += 1
    assert trocas == 8, trocas

    k = next(i for i, e in enumerate(ini) if e.get('name') == 'Preparar inimigos') + 1
    ini.insert(k, VISAO)

    for e in todos(ini):
        if e['type'].endswith('Comment'):
            e['comment'] = (e['comment']
                            .replace('perseguir (pato a menos de 800 px; desiste a mais de 1000)',
                                     'perseguir (vendo o pato: na tela e sem parede no meio; desiste depois de '
                                     'perde_tempo s fora da tela)')
                            .replace('perseguem a menos de aggro_dist e desistem a mais de desiste_dist',
                                     'perseguem vendo o pato (ve_pato) e desistem depois de perde_tempo s fora da tela')
                            .replace('Com o pato a menos de aggro_dist:', 'Vendo o pato:')
                            .replace('com o pato a menos de perseguir_dist vai', 'vendo o pato vai'))

    inimigos = {o['name'] for o in next(g for g in d['objectsGroups'] if g['name'] == I)['objects']}
    usado = json.dumps([x['events'] for x in d['externalEvents']] + [l['events'] for l in d['layouts']],
                       ensure_ascii=False)
    for o in d['objects']:
        if o['name'] not in inimigos:
            continue
        nomes = {v['name'] for v in o['variables']}
        if 've_pato' not in nomes:
            o['variables'].append(var('ve_pato', 'boolean', False, o['name'] + '/ve_pato'))
        if 'perde_tempo' not in nomes:
            o['variables'].append(var('perde_tempo', 'number', 2, o['name'] + '/perde_tempo'))
        o['variables'] = [v for v in o['variables']
                          if not (v['name'] in ('aggro_dist', 'desiste_dist', 'perseguir_dist')
                                  and not re.search(rf'\b{o["name"]}\.{v["name"]}\b|\b(Terrestre|Voador|Inimigo)\.{v["name"]}\b', usado))]
    for l in d['layouts']:
        if any(e.get('target') == 'Inimigos' for e in l['events']):
            nomes = {v['name'] for v in l['variables']}
            for n in ('visao_rx', 'visao_ry'):
                if n not in nomes:
                    l['variables'].append(var(n, 'number', 0, l['name'] + '/' + n))

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('inimigos acordam vendo o pato')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
