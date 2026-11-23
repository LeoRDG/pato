"""Tarefa 103: a caveira azul não fica entalada no terreno.

Ela andava X, batia (desfazia o passo e invertia) e andava Y do mesmo jeito; isso só funciona se ela começa fora do
terreno. O tranco de bala dos voadores (SetX + kb_dir * empurrao_x) e a ondinha da patrulha podem colocá-la dentro de
uma parede, e aí todo passo bate, desfaz e inverte: fica tremendo no lugar. E com o pato atrás de uma parede, a parede
mandava ela embora e a caixa em volta do pato (area_raio / area_alt) mandava de volta no mesmo instante: ficava
prensada na parede. Agora:
- no começo do "para cada", se ela está dentro do Terreno, é empurrada para fora (SeparateFromObjects);
- bater numa parede zera o cronômetro "quique_x" (ou "quique_y") e a caixa só puxa de volta naquele eixo depois de
  quique_trava s (variável nova, 0.5): ela quica para longe da parede e volta depois.
O passo em X sai das ações do "para cada" e vira subevento depois do empurrão.
Os cronômetros começam no "Preparar inimigos" (cronômetro que nunca começou não passa em nenhuma comparação).
Rodar uma vez:  python3 tools/t103_caveira_azul_nao_entala.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 'caveira_azul'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def c(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def a(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if f'{C}.quique_trava' in texto:
        sys.exit('t103 já foi aplicada; não roda de novo.')
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    g = next(e for e in todos(ini) if e.get('name') == 'Caveira azul (quica)')
    fe = next(e for e in g['events'] if e['type'].endswith('ForEach') and e.get('object') == C)

    # bater na parede marca o eixo
    batidas = {}
    for e in fe['events']:
        acoes = e.get('actions') or []
        if any(x['type']['value'] == 'CollisionNP' for x in e.get('conditions') or []):
            eixo = 'x' if any(x['type']['value'] == 'SetX' for x in acoes) else 'y'
            acoes.append(a('ResetObjectTimer', C, f'"quique_{eixo}"'))
            batidas[eixo] = e
    assert set(batidas) == {'x', 'y'}, batidas

    # a caixa só puxa depois de quique_trava s da última batida naquele eixo
    caixa = 0
    for e in fe['events']:
        cs = e.get('conditions') or []
        if len(cs) == 1 and cs[0]['type']['value'] == 'BuiltinCommonInstructions::CompareNumbers' and 'pato.Center' in cs[0]['parameters'][0]:
            eixo = 'x' if 'CenterX' in cs[0]['parameters'][0] else 'y'
            cs.append(c('CompareObjectTimer', C, f'"quique_{eixo}"', '>', f'{C}.quique_trava'))
            caixa += 1
    assert caixa == 4, caixa

    # dentro do terreno: empurra para fora antes de andar. O passo em X era ação do próprio "para cada" (roda antes
    # dos subeventos); vira um subevento logo depois do empurrão, para a batida em X ainda ver a parede.
    passo_x = [x for x in fe['actions'] if x['type']['value'] == 'SetX']
    assert len(passo_x) == 1 and fe['actions'] == passo_x, fe['actions']
    fe['actions'] = []
    fe['events'].insert(0, {'type': 'BuiltinCommonInstructions::Standard', 'conditions': [], 'actions': passo_x})
    fe['events'].insert(0, {'type': 'BuiltinCommonInstructions::Standard',
                            'conditions': [c('CollisionNP', C, 'Terreno', '', '', '')],
                            'actions': [a('SeparateFromObjects', C, 'Terreno', '')]})

    prep = next(e for e in ini if e.get('name') == 'Preparar inimigos')
    uma_vez = next(e for e in prep['events'] if e['type'].endswith('ForEach')
                   and '"preparado", "False"' in json.dumps(e['conditions']))
    uma_vez['actions'] += [a('ResetObjectTimer', 'Inimigo', '"quique_x"'), a('ResetObjectTimer', 'Inimigo', '"quique_y"')]

    com = next(e for e in g['events'] if e['type'].endswith('Comment'))
    com['comment'] += (' Dentro do terreno (tranco de bala), é empurrada para fora; depois de bater numa parede, a caixa '
                       'só puxa de volta naquele eixo depois de quique_trava s.')
    obj = next(o for o in d['objects'] if o['name'] == C)
    if not any(v['name'] == 'quique_trava' for v in obj['variables']):
        obj['variables'].append({'name': 'quique_trava', 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t103/quique_trava')),
                                 'type': 'number', 'value': 0.5})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('caveira azul não entala')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
