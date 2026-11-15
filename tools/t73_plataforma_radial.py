"""Tarefa 73: plataforma radial do purgatório, uma roda-gigante de troncos.

Diferente da plataforma_movel do Inferno (que vai e volta numa reta, freando nas pontas), a plataforma_radial gira
sem parar num círculo em volta de um centro, sempre de pé (o tronco não vira), presa ao centro por um cipó
(plataforma_radial_corda) que sai de uma pedra-eixo musgosa (plataforma_radial_eixo) que gira junto. Várias
plataformas com o mesmo centro, raio e velocidade e ângulos diferentes formam uma roda.

Como usar no editor: ponha uma plataforma_radial e, nas variáveis da instância, escreva o centro (centro_x,
centro_y; deixado em 0, 0 vira o centro do círculo que passa por onde ela foi colocada, no ângulo `angulo`), o
`raio` (px), a velocidade `vel_ang` (graus/s; positivo gira no sentido horário, negativo no anti-horário) e o
`angulo` de partida (graus; 0 = à direita do centro, 90 = embaixo). `com_eixo` desenha a pedra do centro (ligue
em uma só plataforma de cada roda). `ancora_y` é a altura, a partir do topo da imagem, do ponto preso ao cipó.
Na pedra, `giro` multiplica o giro dela.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - imagens assets/plataforma_radial/ (tronco com musgo e cipós balançando em 4 quadros, a pedra-eixo e o cipó);
  - objetos plataforma_radial (tronco atravessável por baixo), plataforma_radial_corda (tiled sprite) e
    plataforma_radial_eixo, na pasta cenario/plataformas;
  - eventos externos "PlataformasRadiais", ligados na cena Purgatorio, e a variável de cena radial_n;
  - duas rodas no Purgatorio: uma de três troncos devagar no sentido horário entre o topo do pilar e o 2º terraço,
    e uma de dois troncos mais rápida no anti-horário no último trecho.
"""
import json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = 'assets/purgatorio/tiles/tiles_purgatorio.png'
PASTA = 'assets/plataforma_radial'
QUADROS = [f'{PASTA}/idle_{i:02d}.png' for i in range(4)]
EIXO_IMG, CORDA_IMG = f'{PASTA}/eixo.png', f'{PASTA}/corda.png'
CENA = 'Purgatorio'
T, COLS = 32, 17
W, H = 96, 28                                # tronco nativo (sai em 2x)
ESCURO, PEDRA_E, PEDRA, PEDRA_C = (27, 28, 24, 255), (59, 56, 51, 255), (80, 76, 69, 255), (105, 100, 90, 255)
MUSGO_E, MUSGO, MUSGO_C = (54, 64, 47, 255), (72, 85, 59, 255), (96, 110, 74, 255)
CASCA = (80, 63, 51, 255)
P, C, X = 'plataforma_radial', 'plataforma_radial_corda', 'plataforma_radial_eixo'
VARS_P = {'centro_x': 0, 'centro_y': 0, 'raio': 320, 'vel_ang': 30, 'angulo': 0, 'ancora_y': 14, 'com_eixo': True, 'id': 0}
VARS_C = {'id': 0}
VARS_X = {'id': 0, 'giro': 1}

# Rodas do Purgatorio: (nome, centro x, centro y, raio, vel_ang, ângulos das plataformas)
RODAS = [('roda_pilar', 2656, -5792, 320, 30, (90, 210, 330)),
         ('roda_final', 2464, -7584, 256, -40, (0, 180))]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t73/' + '/'.join(p)))


# ------------------------------------------------------------------ imagens
def tronco(fase):
    """Tronco de três tiles de ponte do atlas do purgatório e três cipós pendurados que balançam com a fase."""
    atlas = Image.open(os.path.join(RAIZ, ATLAS)).convert('RGBA')
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for k, i in enumerate((125, 126, 127)):
        im.paste(atlas.crop((i % COLS * T, i // COLS * T, i % COLS * T + T, i // COLS * T + 16)), (k * T, 0))
    px = im.load()
    for n, (cx, comp) in enumerate(((18, 9), (49, 12), (77, 7))):
        y0 = max(y for y in range(16) if px[cx, y][3] == 255)
        for k in range(1, comp + 1):
            x = cx + round(math.sin(fase * math.pi / 2 + n * 1.7) * k / comp * 1.6)
            if 0 <= x < W and y0 + k < H:
                px[x, y0 + k] = (MUSGO_C if k % 3 == 0 else MUSGO if k % 3 == 1 else MUSGO_E)
        x = cx + round(math.sin(fase * math.pi / 2 + n * 1.7) * 1.6)
        if y0 + comp + 1 < H:
            px[x, y0 + comp + 1] = MUSGO_C                                   # folhinha na ponta
    return im


def eixo():
    """Pedra redonda com musgo, um furo no meio e três sulcos que mostram o giro."""
    r = 13
    im = Image.new('RGBA', (2 * r + 2, 2 * r + 2), (0, 0, 0, 0))
    px = im.load()
    for y in range(2 * r + 2):
        for x in range(2 * r + 2):
            dx, dy = x - r - .5, y - r - .5
            d = math.hypot(dx, dy)
            if d > r + .5:
                continue
            luz = (-dx - dy) / (r * 1.4)
            cor = ESCURO if d > r - .7 else PEDRA_C if luz > .35 else PEDRA if luz > -.25 else PEDRA_E
            ang = math.degrees(math.atan2(dy, dx)) % 120
            if 3 < d < r - 2 and abs(ang - 60) < 5:
                cor = PEDRA_E                                                # sulcos
            if d < 3:
                cor = ESCURO                                                 # furo do eixo
            if d > r - 4 and d <= r - .7 and (dy < -r * .3 and (x * 7 + y * 3) % 5 < 3):
                cor = MUSGO if luz > 0 else MUSGO_E                          # musgo por cima
            px[x, y] = cor
    return im


def corda():
    """Pedaço de cipó trançado que repete na horizontal."""
    im = Image.new('RGBA', (16, 5), (0, 0, 0, 0))
    px = im.load()
    for x in range(16):
        px[x, 0] = px[x, 4] = MUSGO_E
        for y in (1, 2, 3):
            px[x, y] = MUSGO_C if (x + y) % 8 < 3 else MUSGO if (x - y) % 8 < 5 else CASCA
    return im


def desenha():
    os.makedirs(os.path.join(RAIZ, PASTA), exist_ok=True)
    for f, fase in zip(QUADROS, range(4)):
        if not os.path.exists(os.path.join(RAIZ, f)):
            tronco(fase).resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(RAIZ, f))
    for f, fn in ((EIXO_IMG, eixo), (CORDA_IMG, corda)):
        if not os.path.exists(os.path.join(RAIZ, f)):
            im = fn()
            im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(RAIZ, f))


# ------------------------------------------------------------------ jogo.json
def I(tipo, *params, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(params)}


def E(conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def para_cada(obj, conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


COS, SIN = f'cos(ToRad({P}.angulo))', f'sin(ToRad({P}.angulo))'


def eventos():
    num = lambda o, v, op, expr: I('SetNumberObjectVariable', o, v, op, expr)
    mesmo = lambda o: I('NumberObjectVariable', P, 'id', '=', f'{o}.id')
    return [
        {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Plataformas radiais (rodas de troncos). Cada plataforma_radial gira sem parar em volta de '
                    '(centro_x, centro_y) a `raio` px, a vel_ang graus/s (negativo = anti-horário), sempre de pé, a '
                    'partir de `angulo` (0 = à direita, 90 = embaixo). Centro em 0, 0 vira, no começo da cena, o '
                    'centro do círculo que passa por onde ela foi posta. No começo cada uma ganha um id, um cipó '
                    '(plataforma_radial_corda) do centro até ela e, se com_eixo, a pedra do centro '
                    '(plataforma_radial_eixo), que gira com ela vezes `giro`.'},
        {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': 'Plataformas radiais', 'source': '',
         'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': [
            E([I('SceneJustBegins', '')], [], [
                para_cada(P, [], [I('SetNumberVariable', 'radial_n', '+', '1'), num(P, 'id', '=', 'radial_n')], [
                    E([I('NumberObjectVariable', P, 'centro_x', '=', '0'), I('NumberObjectVariable', P, 'centro_y', '=', '0')],
                      [num(P, 'centro_x', '=', f'{P}.X() + {P}.Width() / 2 - {P}.raio * {COS}'),
                       num(P, 'centro_y', '=', f'{P}.Y() + {P}.ancora_y - {P}.raio * {SIN}')]),
                    E([], [I('Create', '', C, f'{P}.centro_x', f'{P}.centro_y', ''), num(C, 'id', '=', f'{P}.id'),
                           I('SetZOrder', C, '=', f'{P}.ZOrder() - 2')]),
                    E([I('BooleanObjectVariable', P, 'com_eixo', 'True', '')],
                      [I('Create', '', X, f'{P}.centro_x', f'{P}.centro_y', ''), num(X, 'id', '=', f'{P}.id'),
                       I('SetZOrder', X, '=', f'{P}.ZOrder() - 1')]),
                ]),
            ]),
            E([], [num(P, 'angulo', '+', f'{P}.vel_ang * TimeDelta()'),
                   I('SetXY', P, '=', f'{P}.centro_x + {P}.raio * {COS} - {P}.Width() / 2',
                     '=', f'{P}.centro_y + {P}.raio * {SIN} - {P}.ancora_y')]),
            para_cada(C, [], [], [E([mesmo(C)], [
                I('ResizableCapability::ResizableBehavior::SetWidth', C, 'Resizable', '=', f'{P}.raio'),
                I('SetXY', C, '=', f'{P}.centro_x + {P}.raio * {COS} / 2 - {C}.Width() / 2',
                  '=', f'{P}.centro_y + {P}.raio * {SIN} / 2 - {C}.Height() / 2'),
                I('SetAngle', C, '=', f'{P}.angulo')])]),
            para_cada(X, [], [], [E([mesmo(X)], [
                I('SetXY', X, '=', f'{P}.centro_x - {X}.Width() / 2', '=', f'{P}.centro_y - {X}.Height() / 2'),
                I('SetAngle', X, '=', f'{P}.angulo * {X}.giro')])]),
        ]},
    ]


def variaveis(nome, vs):
    out = []
    for k, v in vs.items():
        tipo = 'boolean' if isinstance(v, bool) else 'number'
        out.append({'name': k, 'persistentUuid': uid(nome, k), 'type': tipo, 'value': v})
    return out


def sprite(nome, anims, vs, comportamentos, mascara=None):
    def quadro_(f):
        q = {'hasCustomCollisionMask': mascara is not None, 'image': f, 'points': [],
             'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
             'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': mascara or []}
        return q
    return {'adaptCollisionMaskAutomatically': mascara is None, 'assetStoreId': '', 'name': nome, 'persistentUuid': uid(nome),
            'type': 'Sprite', 'updateIfNotVisible': False, 'variables': variaveis(nome, vs),
            'effects': [], 'behaviors': comportamentos,
            'animations': [{'name': n, 'useMultipleDirections': False,
                            'directions': [{'looping': laco, 'timeBetweenFrames': tempo, 'sprites': [quadro_(f) for f in arqs]}]}
                           for n, arqs, laco, tempo in anims]}


def instancias_rodas(cena):
    ja = {i.get('persistentUuid') for i in cena['instances']}
    z = max((i['zOrder'] for i in cena['instances'] if i.get('layer', '') == '' and i['name'].startswith('tiles_')), default=6) + 10
    for nome, cx, cy, raio, vel, angulos in RODAS:
        for k, ang in enumerate(angulos):
            u = uid(CENA, nome, str(k))
            if u in ja:
                continue
            a = math.radians(ang)
            vs = {'centro_x': cx, 'centro_y': cy, 'raio': raio, 'vel_ang': vel, 'angulo': ang, 'com_eixo': k == 0}
            cena['instances'].append({
                'angle': 0, 'customSize': False, 'depth': 1, 'height': 0, 'keepRatio': True, 'layer': '', 'name': P,
                'persistentUuid': u, 'width': 0,
                'x': round(cx + raio * math.cos(a) - W), 'y': round(cy + raio * math.sin(a) - VARS_P['ancora_y']),
                'zOrder': z, 'numberProperties': [], 'stringProperties': [],
                'initialVariables': [{'name': n, 'persistentUuid': uid(CENA, nome, str(k), n),
                                      'type': 'boolean' if isinstance(v, bool) else 'number', 'value': v} for n, v in vs.items()]})


def migra(d):
    objs = {o['name'] for o in d['objects']}
    recursos = d['resources']['resources']
    tem = {r['name'] for r in recursos}
    for rel in QUADROS + [EIXO_IMG, CORDA_IMG]:
        if rel not in tem:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})
    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'plataformas'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox
    mascara = [[{'x': 6, 'y': 4}, {'x': W * 2 - 6, 'y': 4}, {'x': W * 2 - 6, 'y': 24}, {'x': 6, 'y': 24}]]   # só o tronco
    novos = [
        sprite(P, [('idle', QUADROS, True, 0.18)], VARS_P,
               [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False,
                 'platformType': 'Jumpthru', 'yGrabOffset': 0}], mascara),
        sprite(X, [('idle', [EIXO_IMG], False, 0.1)], VARS_X, []),
        {'assetStoreId': '', 'height': 10, 'name': C, 'persistentUuid': uid(C), 'texture': CORDA_IMG,
         'type': 'TiledSpriteObject::TiledSprite', 'width': 64, 'variables': variaveis(C, VARS_C), 'effects': [], 'behaviors': []},
    ]
    for o in novos:
        if o['name'] not in objs:
            d['objects'].append(o)
            if not any(c.get('objectName') == o['name'] for c in pasta.setdefault('children', [])):
                pasta['children'].append({'objectName': o['name']})
    if not any(x['name'] == 'PlataformasRadiais' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': CENA, 'name': 'PlataformasRadiais', 'events': eventos()})
    cena = next((l for l in d['layouts'] if l['name'] == CENA), None)
    if cena is None:
        return
    if not any(e['type'].endswith('::Link') and e.get('target') == 'PlataformasRadiais' for e in cena['events']):
        k = max(n for n, e in enumerate(cena['events']) if e['type'].endswith('::Link')) + 1
        cena['events'].insert(k, {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0},
                                  'target': 'PlataformasRadiais'})
    if not any(v['name'] == 'radial_n' for v in cena['variables']):
        cena['variables'].append({'name': 'radial_n', 'persistentUuid': uid(CENA, 'radial_n'), 'type': 'number', 'value': 0})
    instancias_rodas(cena)


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
