"""Tarefa 97: a caveira azul quica em volta do pato.

Antes ela quicava numa caixa de area_raio px em volta de onde nasceu (base_x/base_y), que ainda mudava de lugar toda
vez que ela desistia do pato: na prática ia embora e não atacava. Agora a caixa é em volta do pato: passou
area_raio px dele na horizontal ou area_alt px (variável nova, 350) na vertical, volta na direção dele. O resto fica
igual (quica nas paredes, ganha quique_ganho px/s por quique até quique_max, machuca por encostar).
Rodar uma vez:  python3 tools/t97_caveira_azul_em_volta_do_pato.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 'caveira_azul'
TROCA = {  # (eixo, op velho) -> (condição nova)
    ('PosX', '>'): (f'{C}.CenterX() - pato.CenterX()', '>', f'{C}.area_raio'),
    ('PosX', '<'): (f'{C}.CenterX() - pato.CenterX()', '<', f'-{C}.area_raio'),
    ('PosY', '>'): (f'{C}.CenterY() - pato.CenterY()', '>', f'{C}.area_alt'),
    ('PosY', '<'): (f'{C}.CenterY() - pato.CenterY()', '<', f'-{C}.area_alt'),
}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    g = next(e for e in todos(ini) if e.get('name') == 'Caveira azul (quica)')
    trocados = 0
    for e in todos(g['events']):
        for c in e.get('conditions') or []:
            t = c['type']['value']
            if t in ('PosX', 'PosY') and c['parameters'][0] == C and 'base_' in c['parameters'][2]:
                c['type'] = {'value': 'BuiltinCommonInstructions::CompareNumbers'}
                c['parameters'] = list(TROCA[(t, c['parameters'][1])])
                trocados += 1
    if trocados == 0:
        sys.exit('t97 já foi aplicada; não roda de novo.')
    assert trocados == 4, trocados
    com = next(e for e in g['events'] if e['type'].endswith('Comment'))
    com['comment'] = ('Vendo o pato, quica em diagonal sem parar em volta dele: passou area_raio px dele na horizontal '
                      'ou area_alt px na vertical, volta na direção dele. Quica nas paredes e ganha quique_ganho px/s '
                      'a cada quique (até quique_max). Machuca por encostar.')
    obj = next(o for o in d['objects'] if o['name'] == C)
    if not any(v['name'] == 'area_alt' for v in obj['variables']):
        obj['variables'].append({'name': 'area_alt', 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t97/area_alt')),
                                 'type': 'number', 'value': 350})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('caveira azul quica em volta do pato')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
