"""Tarefa 96: cada inimigo vira para o lado do pato.

Os eventos de virar (Estados (terrestres) e Voadores (comum)) usavam a condição PosX do pato comparando com
Terrestre.X() / Voador.X(); numa condição de outro objeto essa expressão lê só a primeira instância do grupo, então
só um inimigo de cada grupo virava certo e os outros copiavam ele. Agora os quatro eventos de cada grupo ficam dentro
de um "para cada" do grupo, comparando o centro do pato com o centro daquele inimigo (CompareNumbers), e as mesmas
regras de antes: sprite_esquerda diz para que lado o desenho olha; os terrestres não viram durante a corrida
(estado "atacar").
Rodar uma vez:  python3 tools/t96_inimigos_viram_cada_um.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def vira(e):
    return any(a['type']['value'].endswith('FlipX') for a in e.get('actions') or []) and \
        any(c['type']['value'] == 'PosX' and c['parameters'][0] == 'pato' for c in e.get('conditions') or [])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    if not any(vira(e) for e in todos(ini)):
        sys.exit('t96 já foi aplicada (nenhum evento de virar com PosX); não roda de novo.')
    feitos = 0
    for nome, grupo in (('Estados (terrestres)', 'Terrestre'), ('Voadores (comum)', 'Voador')):
        g = next(e for e in todos(ini) if e.get('name') == nome)
        pai = next(e for e in todos(g['events']) if sum(map(vira, e.get('events') or [])) == 4)
        velhos = [e for e in pai['events'] if vira(e)]
        for e in velhos:
            for c in e['conditions']:
                if c['type']['value'] == 'PosX' and c['parameters'][0] == 'pato':
                    assert c['parameters'][2] == f'{grupo}.X()', c
                    c['type'] = {'value': 'BuiltinCommonInstructions::CompareNumbers'}
                    c['parameters'] = ['pato.CenterX()', c['parameters'][1], f'{grupo}.CenterX()']
        k = pai['events'].index(velhos[0])
        pai['events'] = [e for e in pai['events'] if e not in velhos]
        pai['events'].insert(k, {'type': 'BuiltinCommonInstructions::ForEach', 'object': grupo,
                                 'conditions': [], 'actions': [], 'events': velhos})
        feitos += 1
    if 'PosX' in json.dumps([e.get('conditions') for e in todos(ini) if vira(e)]):
        sys.exit('sobrou evento de virar com PosX')
    assert feitos == 2

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cada inimigo vira para o pato')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
