"""Tarefa 51: lava com vida (animação dessincronizada, brasas e bolhas) e tiles de margem aquecidos.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - imagens novas: assets/lava/bolha_NN.png (bolha que cresce e estoura);
  - 8 tiles novos nas células VAZIAS do atlas tiles_inferno (.png e _2x.png), feitos dos tiles de borda do próprio
    pacote com a borda virada para a lava em brasa:
        117 / 118  beira do chão à esquerda / à direita da poça (quina de cima)
        134 / 135  parede da poça à esquerda / à direita
        151 / 152  canto de baixo à esquerda / à direita
         94 /  96  fundo da poça (duas variantes)
    e as caixas de colisão deles em tiles_inferno (só ids novos entram na lista);
  - objetos lava_bolha (sprite) e lava_brasas (partículas), na pasta cenario/perigos;
  - as variáveis que regulam tudo, no próprio objeto lava (sem clarão nem halo: foram tirados a pedido);
  - eventos externos "Lava", ligados na cena Inferno.

Todo número fica em variável: lava.anim_vel_min/max, lava.superficie_frac, lava.brasa_espera_min/max,
lava.bolha_espera_min/max, lava.bolha_afunda; as brasas se ajustam no emissor lava_brasas.
"""
import copy, json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T, COLS = 32, 17
ATLAS = 'assets/gandalf_hell/tiles/tiles_inferno'
BOLHAS = [f'assets/lava/bolha_{i:02d}.png' for i in range(7)]
# célula nova -> (tile de origem, lado virado para a lava)
MARGENS = {117: (2, 'R'), 118: (0, 'L'), 134: (19, 'R'), 135: (17, 'L'), 151: (40, 'TR'), 152: (42, 'TL'),
           94: (1, 'T'), 96: (52, 'T')}
BEIRAS = (117, 118)                       # só esquentam abaixo do piso
ALCANCE = 15                              # até onde o calor entra na pedra (px)
BRASA = [(58, 3, 12), (84, 3, 12), (112, 3, 16)]                                             # clarão no miolo escuro
QUENTE = [(112, 3, 16), (145, 12, 7), (204, 44, 22), (251, 60, 35), (240, 126, 32), (229, 171, 33)]   # crosta em brasa
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

VARS_LAVA = {'anim_vel_min': 0.7, 'anim_vel_max': 1.3, 'superficie_frac': 0.22,
             'brasa_espera_min': 0.15, 'brasa_espera_max': 0.6, 'brasa_espera': 0.3,
             'bolha_espera_min': 0.5, 'bolha_espera_max': 1.6, 'bolha_espera': 0.8, 'bolha_afunda': 10}


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t51/' + '/'.join(p)))


# ------------------------------------------------------------------ imagens
def celula(im, i):
    return (i % COLS * T, i // COLS * T, i % COLS * T + T, i // COLS * T + T)


def aquece(tile, lado, beira):
    """Copia do tile com a borda do lado da lava em brasa: a crosta vermelha sobe para laranja e o miolo ganha clarão."""
    out = tile.copy()
    px = out.load()
    for y in range(T):
        for x in range(T):
            r, g, b, a = px[x, y]
            if a < 255:
                continue
            d = {'R': T - 1 - x, 'L': x, 'T': y, 'TR': math.hypot(T - 1 - x, y), 'TL': math.hypot(x, y)}[lado]
            t = max(0.0, 1 - d / ALCANCE)
            if beira:
                t *= max(0.0, min(1.0, (y - 5) / 9))
            if t <= 0:
                continue
            ruido = BAYER[y % 4][x % 4] / 16 - .5
            if max(r, g, b) < 36:                       # miolo quase preto: clarão pontilhado
                k = int(t * 3.6 + ruido * 1.1)
                if k >= 1:
                    px[x, y] = BRASA[min(k, 3) - 1] + (255,)
            else:                                        # crosta: sobe na rampa quente
                nivel = 0 if max(r, g, b) < 50 else (1 if max(r, g, b) < 70 else (2 if max(r, g, b) < 95 else 3))
                k = nivel + int(t * 2.6 + ruido * .8)
                if t > .12:
                    px[x, y] = QUENTE[max(0, min(len(QUENTE) - 1, k))] + (255,)
    return out


def desenha_margens():
    """Só escreve nas células ainda vazias; devolve as células que agora têm tile."""
    base = Image.open(os.path.join(RAIZ, ATLAS + '.png')).convert('RGBA')
    x2 = Image.open(os.path.join(RAIZ, ATLAS + '_2x.png')).convert('RGBA')
    mudou = False
    for dest, (orig, lado) in MARGENS.items():
        if base.crop(celula(base, dest)).split()[3].getbbox():
            continue
        novo = aquece(base.crop(celula(base, orig)), lado, dest in BEIRAS)
        base.paste(novo, celula(base, dest)[:2])
        cx, cy = celula(base, dest)[:2]
        if not x2.crop((cx * 2, cy * 2, cx * 2 + 2 * T, cy * 2 + 2 * T)).split()[3].getbbox():
            x2.paste(novo.resize((2 * T, 2 * T), Image.NEAREST), (cx * 2, cy * 2))
        mudou = True
    if mudou:
        base.save(os.path.join(RAIZ, ATLAS + '.png'))
        x2.save(os.path.join(RAIZ, ATLAS + '_2x.png'))


def desenha_bolhas():
    """Bolha de 32 px (16 px em 2x): nasce, cresce, estoura em anel e respingos."""
    if all(os.path.exists(os.path.join(RAIZ, f)) for f in BOLHAS):
        return
    os.makedirs(os.path.join(RAIZ, 'assets', 'lava'), exist_ok=True)
    esc, cla, ama, bra = (145, 12, 7, 255), (251, 60, 35, 255), (240, 126, 32, 255), (255, 228, 61, 255)
    for i, f in enumerate(BOLHAS):
        im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        px = im.load()
        if i < 4:                                           # domo crescendo
            r = (2.3, 3.2, 4.2, 5.2)[i]
            for y in range(16):
                for x in range(16):
                    dx, dy = x + .5 - 8, y + .5 - 15
                    d = math.hypot(dx, dy)
                    if d <= r and y < 15:
                        c = cla if d < r - 1.1 else esc
                        if dx < -r * .2 and dy < -r * .45 and d < r - 1.1:
                            c = ama if i < 3 else bra
                        px[x, y] = c
        else:                                               # estouro: anel se abre e respingos sobem
            k = i - 4
            for ang in range(0, 180, 20):
                a = math.radians(ang + 10)
                rr = 5 + 1.6 * k
                x, y = int(8 + rr * math.cos(a)), int(15 - rr * math.sin(a) * (1 - .2 * k))
                if 0 <= x < 16 and 0 <= y < 16 and (ang // 20 + k) % (k + 1) == 0:
                    px[x, y] = ama if k == 0 else (cla if k == 1 else esc)
            for sx, sy in ((5, 7), (8, 4), (11, 8)):
                y = sy - 2 * k
                if 0 <= y < 16 and k < 2:
                    px[sx, y] = bra if k == 0 else ama
        im.resize((32, 32), Image.NEAREST).save(os.path.join(RAIZ, f))


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


def comentario(txt):
    return {'type': 'BuiltinCommonInstructions::Comment',
            'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0}, 'comment': txt}


def para_cada(obj, conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


SUPERFICIE = 'lava.Y() + lava.Height() * lava.superficie_frac'
JS_INICIO = [
    '// Cada lava (e cada lava_chamas) começa num quadro sorteado e com velocidade própria, para as peças',
    '// lado a lado não pulsarem juntas.',
    'const num = (o, n, padrao) => o.getVariables().has(n) ? o.getVariables().get(n).getAsNumber() : padrao;',
    'for (const nome of ["lava", "lava_chamas", "lava_cascata"]) {',
    '  for (const o of runtimeScene.getObjects(nome)) {',
    '    const min = num(o, "anim_vel_min", 0.7), max = num(o, "anim_vel_max", 1.3);',
    '    o.setAnimationFrame(Math.floor(Math.random() * o.getAnimationFrameCount()));',
    '    o.setAnimationSpeedScale(min + Math.random() * (max - min));',
    '  }',
    '}',
]


def eventos():
    return [
        comentario('Lava com vida. No começo da cena as animações são dessincronizadas; depois, de tempos em tempos sorteados, cada poça solta brasas '
                   '(lava_brasas) e bolhas (lava_bolha) num ponto qualquer da superfície. Tudo se regula nas variáveis de '
                   'lava.'),
        {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': 'Lava', 'source': '',
         'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': [
            E([I('SceneJustBegins', '')], [], [
                para_cada('lava', [], [
                    I('ResetObjectTimer', 'lava', '"brasa"'),
                    I('ResetObjectTimer', 'lava', '"bolha"'),
                    I('SetNumberObjectVariable', 'lava', 'brasa_espera', '=', 'RandomFloatInRange(0, lava.brasa_espera_max)'),
                    I('SetNumberObjectVariable', 'lava', 'bolha_espera', '=', 'RandomFloatInRange(0, lava.bolha_espera_max)'),
                ]),
                {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': list(JS_INICIO), 'parameterObjects': '',
                 'useStrict': True, 'eventsSheetExpanded': False},
            ]),
            para_cada('lava', [], [], [
                E([I('CompareObjectTimer', 'lava', '"brasa"', '>', 'lava.brasa_espera')], [
                    I('Create', '', 'lava_brasas', 'lava.X() + RandomFloatInRange(0, lava.Width())', SUPERFICIE, ''),
                    I('ChangePlan', 'lava_brasas', '=', 'lava.ZOrder() + 2'),
                    I('ResetObjectTimer', 'lava', '"brasa"'),
                    I('SetNumberObjectVariable', 'lava', 'brasa_espera', '=',
                      'RandomFloatInRange(lava.brasa_espera_min, lava.brasa_espera_max)'),
                ]),
                E([I('CompareObjectTimer', 'lava', '"bolha"', '>', 'lava.bolha_espera')], [
                    I('Create', '', 'lava_bolha', 'lava.X() + RandomFloatInRange(0, max(0, lava.Width() - 32))',
                      SUPERFICIE + ' - 32 + lava.bolha_afunda', ''),
                    I('ChangePlan', 'lava_bolha', '=', 'lava.ZOrder() + 1'),
                    I('ResetObjectTimer', 'lava', '"bolha"'),
                    I('SetNumberObjectVariable', 'lava', 'bolha_espera', '=',
                      'RandomFloatInRange(lava.bolha_espera_min, lava.bolha_espera_max)'),
                ]),
            ]),
            E([I('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', 'lava_bolha', 'Animation')],
              [I('Delete', 'lava_bolha', '')]),
        ]},
    ]


def sprite(nome, anim, arquivos, laco, tempo, variaveis):
    quadro = lambda f: {'hasCustomCollisionMask': False, 'image': f, 'points': [],
                        'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                        'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': []}
    return {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': nome, 'persistentUuid': uid(nome),
            'type': 'Sprite', 'updateIfNotVisible': False,
            'variables': [{'name': k, 'persistentUuid': uid(nome, k), 'type': 'number', 'value': v} for k, v in variaveis.items()],
            'effects': [], 'behaviors': [],
            'animations': [{'name': anim, 'useMultipleDirections': False,
                            'directions': [{'looping': laco, 'timeBetweenFrames': tempo, 'sprites': [quadro(f) for f in arquivos]}]}]}


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    tem = {r['name'] for r in recursos}
    for rel in BOLHAS:
        if rel not in tem:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})

    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'perigos'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox

    def novo(o):
        if o['name'] in objs:
            return
        d['objects'].append(o)
        objs[o['name']] = o
        if not any(c.get('objectName') == o['name'] for c in pasta.setdefault('children', [])):
            pasta['children'].append({'objectName': o['name']})

    novo(sprite('lava_bolha', 'estoura', BOLHAS, False, 0.09, {}))
    if 'lava_brasas' not in objs and 'sangue_brasa' in objs:
        b = copy.deepcopy(objs['sangue_brasa'])
        b.update(name='lava_brasas', persistentUuid=uid('lava_brasas'), additive=True, destroyWhenNoParticles=True,
                 emitterAngleA=-115, emitterAngleB=-65, emitterForceMin=40, emitterForceMax=150, flow=40, tank=4,
                 maxParticleNb=8, zoneRadius=8, particleGravityX=0, particleGravityY=-70,
                 particleLifeTimeMin=0.7, particleLifeTimeMax=1.8, particleSize1=100, particleSize2=30,
                 particleColor1='255;200;80', particleRed1=255, particleGreen1=200, particleBlue1=80,
                 particleColor2='210;50;10', particleRed2=210, particleGreen2=50, particleBlue2=10,
                 particleAlpha1=255, particleAlpha2=0, rendererType='Point', rendererParam1=5, rendererParam2=1,
                 variables=[], effects=[], behaviors=[])
        novo(b)

    # lava: variáveis e halo (só o que falta)
    for nome in ('lava', 'lava_chamas', 'lava_cascata'):
        o = objs.get(nome)
        if o is None:
            continue
        vs = VARS_LAVA if nome == 'lava' else {k: VARS_LAVA[k] for k in ('anim_vel_min', 'anim_vel_max')}
        for k, v in vs.items():
            if not any(x['name'] == k for x in o['variables']):
                o['variables'].append({'name': k, 'persistentUuid': uid(nome, k), 'type': 'number', 'value': v})
    # colisão dos tiles novos em tiles_inferno, na grade que o objeto usa hoje (só ids que ainda não estão na lista)
    tiles = objs.get('tiles_inferno')
    if tiles is not None and tiles['content']['atlasImage'].startswith(ATLAS):
        c = tiles['content']
        im = Image.open(os.path.join(RAIZ, c['atlasImage'])).convert('RGBA')
        lado, cols = c['tileSize'], c['columnCount']
        escala = im.width / (COLS * T)
        ids = [x for x in c['tilesWithHitBox'].split(',') if x]
        for dest in MARGENS:
            x0, y0 = dest % COLS * T * escala, dest // COLS * T * escala
            for gy in range(int(y0 // lado), int(math.ceil((y0 + T * escala) / lado))):
                for gx in range(int(x0 // lado), int(math.ceil((x0 + T * escala) / lado))):
                    cheio = im.crop((gx * lado, gy * lado, gx * lado + lado, gy * lado + lado)).split()[3].getbbox() is not None
                    i = str(gy * cols + gx)
                    if cheio and i not in ids:
                        ids.append(i)
        c['tilesWithHitBox'] = ','.join(ids)

    # eventos
    if not any(x['name'] == 'Lava' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': 'Inferno', 'name': 'Lava', 'events': eventos()})
    cena = next((l for l in d['layouts'] if l['name'] == 'Inferno'), None)
    if cena is not None and not any(e['type'].endswith('::Link') and e.get('target') == 'Lava' for e in cena['events']):
        cena['events'].append({'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'Lava'})


def main(caminho, desenha=True):
    if desenha:
        desenha_margens(); desenha_bolhas()
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
