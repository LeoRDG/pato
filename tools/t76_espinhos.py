"""Tarefa 76: espinhos, um emaranhado de sarça com espinhos que dá para socar mas não para pisar.

espinhos é um tiled sprite (dois ramos de sarça trançados com espinhos claros, em cores apagadas, que emendam na
horizontal): no editor, estica-se na largura que quiser e gira-se 90 graus para virar parede. Não tem comportamento de
plataforma, então o pato não fica de pé nele: atravessa, e encostar machuca. Mas ele entra no grupo Terreno, que é o
que o soco procura, então socar os espinhos dá o mesmo coice de socar uma parede (inclusive para cima, socando para
baixo): é assim que se passa por eles.

Variáveis de espinhos: dano (vida que tira ao encostar) e empurrao (px/s com que joga o pato para o lado de fora).

Migração de uso único que só ADICIONA: a imagem assets/purgatorio_armadilhas/espinhos.png, o objeto espinhos na pasta
cenario/armadilhas, espinhos no grupo Terreno e os eventos externos "Espinhos", ligados no Purgatorio.
"""
import json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = 'assets/purgatorio_armadilhas/espinhos.png'
NOME = 'espinhos'
VARS = {'dano': 15, 'empurrao': 900}
CENAS = ['Purgatorio']

GALHO_E, GALHO, GALHO_C = (52, 38, 36, 255), (78, 56, 48, 255), (110, 82, 66, 255)
ESPINHO, ESPINHO_C = (168, 156, 132, 255), (204, 196, 170, 255)
FOLHA, FOLHA_E = (72, 85, 59, 255), (54, 64, 47, 255)


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t76/' + '/'.join(p)))


def desenho():
    """32 x 32 que emenda na horizontal: dois ramos em senoide trançados, espinhos para fora, umas folhas."""
    w = h = 32
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    ramos = [lambda x: 16 + 9 * math.sin(2 * math.pi * x / w), lambda x: 16 - 9 * math.sin(2 * math.pi * x / w + .6),
             lambda x: 16 + 3 * math.sin(4 * math.pi * x / w + 1)]
    for k, f in enumerate(ramos):                                          # ramos com 3 px de grossura e luz por cima
        for x in range(w):
            y = f(x)
            for dy in (-2, -1, 0, 1):
                yy = round(y) + dy
                frente = (x // 8) % 3 == k                                  # trançado: cada um passa na frente por vez
                if 0 <= yy < h and (frente or px[x, yy][3] == 0):
                    px[x, yy] = GALHO_C if dy == -2 else GALHO if dy < 1 else GALHO_E
    for k, f in enumerate(ramos):                                          # espinhos para fora do ramo
        for x0 in range(1 + k * 2, w, 5 if k < 2 else 8):
            y = round(f(x0))
            sobe = y <= 16
            dx = 1 if (x0 // 8) % 2 else -1
            for n in range(1, 7):
                xx, yy = (x0 + dx * (n // 3)) % w, y + (-n - 2 if sobe else n + 1)
                if 0 <= yy < h:
                    px[xx, yy] = ESPINHO_C if n >= 5 else ESPINHO
                if n <= 2 and 0 <= yy < h:                                  # base do espinho mais grossa
                    px[(xx + 1) % w, yy] = ESPINHO
            if 0 <= y + (-2 if sobe else 2) < h:
                px[x0 % w, y + (-2 if sobe else 2)] = GALHO_E
    for x0, y0 in ((6, 15), (21, 18), (28, 13)):                           # folhinhas
        for dx, dy, c in ((0, 0, FOLHA), (1, 0, FOLHA), (1, -1, FOLHA_E), (2, -1, FOLHA)):
            xx, yy = (x0 + dx) % w, y0 + dy
            if px[xx, yy][3] == 0:
                px[xx, yy] = c
    return im


def I(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def eventos():
    return [
        {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Espinhos: não dá para ficar de pé (não são plataforma), encostar tira `dano` e joga o pato para o '
                    'lado de fora a `empurrao` px/s. Estão no grupo Terreno, então socar dá o coice da parede.'},
        {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': 'Espinhos', 'source': '',
         'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': [
            {'type': 'BuiltinCommonInstructions::Standard', 'conditions': [
                I('BooleanObjectVariable', 'pato', 'morto', 'False', ''),
                I('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
                I('CollisionNP', 'pato', NOME, '', '', '')], 'actions': [
                I('SetNumberObjectVariable', 'pato', 'vida', '-', f'{NOME}.dano'),
                I('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
                I('ResetObjectTimer', 'pato', '"iframes"'),
                I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'"{NOME}"'),
                I('SetNumberObjectVariable', 'pato', 'coice_vx', '=',
                  f'sign(pato.CenterX() - {NOME}.CenterX()) * {NOME}.empurrao')]},
        ]},
    ]


def migra(d):
    if not any(r['name'] == IMG for r in d['resources']['resources']):
        d['resources']['resources'].append({'file': IMG, 'kind': 'image', 'metadata': '', 'name': IMG,
                                            'smoothed': False, 'userAdded': True})
    if not any(o['name'] == NOME for o in d['objects']):
        d['objects'].append({'assetStoreId': '', 'height': 64, 'name': NOME, 'persistentUuid': uid(NOME), 'texture': IMG,
                             'type': 'TiledSpriteObject::TiledSprite', 'width': 192,
                             'variables': [{'name': k, 'persistentUuid': uid(NOME, k), 'type': 'number', 'value': v}
                                           for k, v in VARS.items()], 'effects': [], 'behaviors': []})
        pasta = d['objectsFolderStructure']
        for nome in ('cenario', 'armadilhas'):
            prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
            if prox is None:
                prox = {'folderName': nome, 'children': []}
                pasta['children'].append(prox)
            pasta = prox
        pasta['children'].append({'objectName': NOME})
    terreno = next((g for g in d['objectsGroups'] if g['name'] == 'Terreno'), None)
    if terreno is not None and not any(o['name'] == NOME for o in terreno['objects']):
        terreno['objects'].append({'name': NOME})
    if not any(x['name'] == 'Espinhos' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': CENAS[0], 'name': 'Espinhos', 'events': eventos()})
    for nome in CENAS:
        cena = next((l for l in d['layouts'] if l['name'] == nome), None)
        if cena is not None and not any(e['type'].endswith('::Link') and e.get('target') == 'Espinhos' for e in cena['events']):
            k = max(n for n, e in enumerate(cena['events']) if e['type'].endswith('::Link')) + 1
            cena['events'].insert(k, {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0},
                                      'target': 'Espinhos'})


def main(caminho):
    if not os.path.exists(os.path.join(RAIZ, IMG)):
        im = desenho()
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(RAIZ, IMG))
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
