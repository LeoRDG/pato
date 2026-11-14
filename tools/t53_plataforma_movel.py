"""Tarefa 53: plataforma móvel do inferno, uma peça só, que vai e volta entre um começo e um fim dados em variáveis.

Como usar no editor: ponha uma plataforma_movel na cena e, nas variáveis da instância, escreva o começo
(ini_x, ini_y) e o fim (fim_x, fim_y) em coordenadas da cena. Ela anda a `velocidade` px/s, acelera e freia nas
pontas e espera `espera` s em cada uma. Um par deixado em 0, 0 vale "onde ela foi colocada": sem preencher nada
ela fica parada no lugar; preenchendo só o fim, ela sai de onde foi colocada.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - imagens assets/plataforma_movel/idle_NN.png (laje de pedra do próprio atlas do inferno, com a parte de baixo em
    brasa pulsando e correntes penduradas);
  - objeto plataforma_movel (sprite com comportamento de plataforma atravessável por baixo), na pasta
    cenario/plataformas;
  - eventos externos "Plataformas", ligados na cena Inferno.

Variáveis de plataforma_movel: ini_x, ini_y, fim_x, fim_y, velocidade, espera (ajustáveis) e fase, sentido
(de trabalho, mexidas pelos eventos).
"""
import json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = 'assets/gandalf_hell/tiles/tiles_inferno.png'
PASTA = 'assets/plataforma_movel'
QUADROS = [f'{PASTA}/idle_{i:02d}.png' for i in range(6)]
T, COLS = 32, 17
W, H = 96, 30                                # tamanho nativo (sai em 2x)
BRASA = [(58, 3, 12), (84, 3, 12), (112, 3, 16)]
QUENTE = [(112, 3, 16), (145, 12, 7), (204, 44, 22), (251, 60, 35), (240, 126, 32), (229, 171, 33)]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
FERRO, FERRO_L, FERRO_D = (62, 54, 59, 255), (98, 88, 92, 255), (33, 30, 35, 255)
VARS = {'ini_x': 0, 'ini_y': 0, 'fim_x': 0, 'fim_y': 0, 'velocidade': 160, 'espera': 0.6, 'fase': 0, 'sentido': 1}


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t53/' + '/'.join(p)))


# ------------------------------------------------------------------ imagens
def laje():
    """Três tiles de ponte do atlas (ponta, meio, ponta) viram a laje; devolve a imagem e a altura dela."""
    atlas = Image.open(os.path.join(RAIZ, ATLAS)).convert('RGBA')
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for k, i in enumerate((108, 109, 110)):
        im.paste(atlas.crop((i % COLS * T, i // COLS * T, i % COLS * T + T, i // COLS * T + 18)), (k * T, 0))
    return im


def quadro(calor):
    """Laje com a parte de baixo em brasa (calor = alcance em px) e duas correntes com peso penduradas."""
    im = laje()
    px = im.load()
    for x in range(W):
        fundo = max((y for y in range(H) if px[x, y][3] == 255), default=None)
        if fundo is None:
            continue
        for y in range(H):
            r, g, b, a = px[x, y]
            if a < 255:
                continue
            t = max(0.0, 1 - (fundo - y) / calor) * min(1.0, y / 6)          # o piso de cima fica como é
            if t <= 0:
                continue
            ruido = BAYER[y % 4][x % 4] / 16 - .5
            if max(r, g, b) < 36:
                k = int(t * 3.6 + ruido * 1.1)
                if k >= 1:
                    px[x, y] = BRASA[min(k, 3) - 1] + (255,)
            elif t > .12:
                nivel = 0 if max(r, g, b) < 50 else (1 if max(r, g, b) < 70 else (2 if max(r, g, b) < 95 else 3))
                px[x, y] = QUENTE[max(0, min(len(QUENTE) - 1, nivel + int(t * 2.6 + ruido * .8)))] + (255,)
    for cx in (20, 75):                                                       # correntes
        y0 = max(y for y in range(H) if px[cx, y][3] == 255)
        for k in range(1, 9):
            y = y0 + k
            if k % 3 == 0:
                px[cx, y] = FERRO_D
            else:
                px[cx - 1, y], px[cx + 1, y] = FERRO, FERRO_L
        for dx, dy, c in ((-1, 9, FERRO), (0, 9, FERRO_L), (1, 9, FERRO), (-1, 10, FERRO_D), (0, 10, FERRO), (1, 10, FERRO_D), (0, 11, FERRO_D)):
            px[cx + dx, y0 + dy] = c
    return im


def desenha():
    os.makedirs(os.path.join(RAIZ, PASTA), exist_ok=True)
    calores = [5, 6.5, 8, 9, 8, 6.5]                                         # pulso que fecha o ciclo
    for f, c in zip(QUADROS, calores):
        if not os.path.exists(os.path.join(RAIZ, f)):
            q = quadro(c)
            q.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(RAIZ, f))


# ------------------------------------------------------------------ jogo.json
def I(tipo, *params, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(params)}


def E(conds, acts, subs=None, tipo='BuiltinCommonInstructions::Standard', **extra):
    e = {'type': tipo, **extra, 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


P = 'plataforma_movel'
SUAVE = f'(1 - cos({P}.fase * 3.14159265)) / 2'
PERCURSO = f'sqrt(pow({P}.fim_x - {P}.ini_x, 2) + pow({P}.fim_y - {P}.ini_y, 2))'


def eventos():
    num = lambda v, op, expr: I('SetNumberObjectVariable', P, v, op, expr)
    zero = lambda a, b: [I('NumberObjectVariable', P, a, '=', '0'), I('NumberObjectVariable', P, b, '=', '0')]
    return [
        {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Plataformas móveis. Cada plataforma_movel vai e volta entre o começo (ini_x, ini_y) e o fim (fim_x, fim_y) '
                    'escritos nas variáveis da instância. Um par deixado em 0, 0 vira, no começo da cena, a posição onde ela '
                    'foi colocada. "fase" anda de 0 a 1 na velocidade dela, com espera em cada ponta, e a posição é o caminho '
                    'entre começo e fim, acelerando e freando nas pontas.'},
        {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': 'Plataformas móveis', 'source': '',
         'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': [
            E([I('SceneJustBegins', '')], [num('fase', '=', '0'), num('sentido', '=', '1'), I('ResetObjectTimer', P, '"parada"')], [
                E(zero('ini_x', 'ini_y'), [num('ini_x', '=', f'{P}.X()'), num('ini_y', '=', f'{P}.Y()')]),
                E(zero('fim_x', 'fim_y'), [num('fim_x', '=', f'{P}.X()'), num('fim_y', '=', f'{P}.Y()')]),
            ]),
            E([I('CompareObjectTimer', P, '"parada"', '>', f'{P}.espera')],
              [num('fase', '+', f'{P}.sentido * {P}.velocidade * TimeDelta() / max(1, {PERCURSO})')]),
            E([I('NumberObjectVariable', P, 'fase', '>=', '1'), I('NumberObjectVariable', P, 'sentido', '>', '0')],
              [num('fase', '=', '1'), num('sentido', '=', '-1'), I('ResetObjectTimer', P, '"parada"')]),
            E([I('NumberObjectVariable', P, 'fase', '<=', '0'), I('NumberObjectVariable', P, 'sentido', '<', '0')],
              [num('fase', '=', '0'), num('sentido', '=', '1'), I('ResetObjectTimer', P, '"parada"')]),
            E([], [I('SetXY', P, '=', f'{P}.ini_x + ({P}.fim_x - {P}.ini_x) * {SUAVE}',
                     '=', f'{P}.ini_y + ({P}.fim_y - {P}.ini_y) * {SUAVE}')]),
        ]},
    ]


def sprite(nome, anims, variaveis, comportamentos, mascara):
    def quadro_(f):
        return {'hasCustomCollisionMask': True, 'image': f, 'points': [], 'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': mascara}
    return {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': nome, 'persistentUuid': uid(nome),
            'type': 'Sprite', 'updateIfNotVisible': False,
            'variables': [{'name': k, 'persistentUuid': uid(nome, k), 'type': 'number', 'value': v} for k, v in variaveis.items()],
            'effects': [], 'behaviors': comportamentos,
            'animations': [{'name': n, 'useMultipleDirections': False,
                            'directions': [{'looping': laco, 'timeBetweenFrames': tempo, 'sprites': [quadro_(f) for f in arqs]}]}
                           for n, arqs, laco, tempo in anims]}


def migra(d):
    objs = {o['name'] for o in d['objects']}
    recursos = d['resources']['resources']
    tem = {r['name'] for r in recursos}
    for rel in QUADROS:
        if rel not in tem:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})
    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'plataformas'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox
    mascara = [[{'x': 6, 'y': 4}, {'x': W * 2 - 6, 'y': 4}, {'x': W * 2 - 6, 'y': 26}, {'x': 6, 'y': 26}]]   # só a laje
    novos = [
        sprite(P, [('idle', QUADROS, True, 0.14)], VARS,
               [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False,
                 'platformType': 'Jumpthru', 'yGrabOffset': 0}], mascara),
    ]
    for o in novos:
        if o['name'] not in objs:
            d['objects'].append(o)
            if not any(c.get('objectName') == o['name'] for c in pasta.setdefault('children', [])):
                pasta['children'].append({'objectName': o['name']})
    if not any(x['name'] == 'Plataformas' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': 'Inferno', 'name': 'Plataformas', 'events': eventos()})
    cena = next((l for l in d['layouts'] if l['name'] == 'Inferno'), None)
    if cena is not None and not any(e['type'].endswith('::Link') and e.get('target') == 'Plataformas' for e in cena['events']):
        cena['events'].append({'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'Plataformas'})


def main(caminho):
    desenha()
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
