"""Tarefa 84: moedas de verdade, criptomoedas em pixel art girando, em três valores: 1x, 5x e 10x.

- Imagens (assets/moedas): pixel art de 16 px aumentada 4x (o mesmo tamanho de pixel do pato), 6 quadros de meia volta
  cada. 1x = moeda Doge (Ð, dourada clara), 5x = Ethereum (losango em dois tons, prateada), 10x = Bitcoin (₿, laranja,
  a maior). Desenhos próprios, sem copiar os logos.
- Objeto moeda: as animações x1, x5 e x10 no lugar do bitcoin.png (o arquivo fica), máscara de colisão fixa do tamanho
  da moeda (não muda enquanto gira).
- Variáveis novas da moeda (só se faltarem): mult (1, 5 ou 10; a moeda vale valor * mult), escala (tamanho da moeda
  que cai do inimigo; antes era 0.02 fixo no evento), chance_x5 e chance_x10 (chance de a moeda que cai ser 5x / 10x) e
  sorteio (auxiliar).
- Eventos (Combate):
  - Morte do Inimigo: a escala vem de moeda.escala e cada moeda sorteia o tipo (chance_x10, depois chance_x5).
  - Moeda > Aparência: mult >= 10 mostra x10, 5..9 mostra x5, abaixo disso x1. Moeda posta na cena vira 5x ou 10x
    mudando a variável mult da instância no GDevelop.
  - Coleta: soma valor * mult e mostra +N com esse valor.
- Instâncias: as moedas postas nas cenas estavam esticadas em 103x60 (o bitcoin.png era 16:9); ficam no tamanho natural
  com o mesmo centro.
Rodar uma vez:  python3 tools/t84_moedas_cripto.py
"""
import json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = 'assets/moedas'
ESC = 4          # tamanho do pixel da arte (igual ao pato)
TELA = 16        # quadro em pixels de arte
QUADROS = 6      # meia volta: a moeda tem a mesma cara dos dois lados
TEMPO_QUADRO = 0.09
VARS = dict(mult=1, escala=1, chance_x5=0.25, chance_x10=0.08, sorteio=0)
VELHO_W, VELHO_H = 103, 60

GLIFOS = {
    'doge': ['####.',
             '.#..#',
             '###.#',
             '.#..#',
             '.#..#',
             '####.'],
    'eth': ['...#...',
            '..###..',
            '.#####.',
            '#######',
            '.#####.',
            '..###..',
            '##...##',
            '.##.##.',
            '..###..',
            '...#...'],
    'btc': ['.#.#...',
            '######.',
            '.#...#.',
            '.#...#.',
            '.#####.',
            '.#....#',
            '.#....#',
            '#######',
            '.#.#...'],
}
DIREITA = {'eth': (98, 96, 172)}   # metade direita do símbolo em outro tom

# tipo: (glifo, diâmetro em pixels de arte, contorno, borda (lado na sombra), face, face clara, brilho, símbolo,
#        sombra do símbolo)
TIPOS = {
    'x1': ('doge', 12, (58, 38, 14), (150, 110, 40), (205, 168, 72), (232, 204, 120), (255, 244, 200),
           (110, 74, 22), (240, 214, 140)),
    'x5': ('eth', 14, (30, 28, 64), (112, 114, 172), (196, 200, 238), (226, 230, 255), (255, 255, 255),
           (46, 44, 108), (150, 152, 206)),
    'x10': ('btc', 16, (90, 40, 6), (196, 104, 16), (247, 147, 26), (255, 186, 80), (255, 240, 196),
            (255, 255, 255), (186, 92, 10)),
}


def quadro(tipo, k):
    glifo, dia, cont, borda, face, clara, brilho, simb, simb_sombra = TIPOS[tipo]
    g = GLIFOS[glifo]
    ang = k * math.pi / QUADROS              # 0 .. 180 graus
    w = abs(math.cos(ang))
    esp = round(2 * math.sin(ang))           # espessura que aparece de lado
    r = dia / 2
    cx = cy = TELA / 2
    a = r * w
    img = Image.new('RGBA', (TELA, TELA), (0, 0, 0, 0))
    px = img.load()
    lado = 1 if ang < math.pi / 2 else -1

    def dentro(x, y, desloc=0.0):
        u = x + 0.5 - cx - desloc
        v = y + 0.5 - cy
        if a < 0.5:
            return abs(u) <= 0.5 and abs(v) <= r
        return (u / a) ** 2 + (v / r) ** 2 <= 1.0

    def no_glifo(x, y, y0):
        gx = math.floor((x + 0.5 - cx) / w + len(g[0]) / 2)
        gy = y - y0
        return (0 <= gy < len(g) and 0 <= gx < len(g[0]) and g[gy][gx] == '#'), gx

    moeda = set()
    for y in range(TELA):
        for x in range(TELA):
            for t in range(1, esp + 1):
                if dentro(x, y, lado * t * 0.75):
                    px[x, y] = borda + (255,)
                    moeda.add((x, y))
    for y in range(TELA):
        for x in range(TELA):
            if dentro(x, y):
                u = (x + 0.5 - cx) / max(a, 0.5)
                v = (y + 0.5 - cy) / r
                dist = math.hypot(u, v)
                cor = face
                if dist > 0.78:
                    cor = clara if (u * 0.7 + v) < -0.2 else borda      # aro em relevo
                elif dist > 0.62 and (u + v) < -0.6:
                    cor = clara
                px[x, y] = cor + (255,)
                moeda.add((x, y))
    if w > 0.3:
        y0 = round(cy - len(g) / 2)
        for y in range(TELA):
            for x in range(TELA):
                if (x, y) not in moeda or not dentro(x, y):
                    continue
                sim, gx = no_glifo(x, y, y0)
                if sim:
                    px[x, y] = (DIREITA.get(glifo, simb) if gx >= len(g[0]) / 2 else simb) + (255,)
                    for sx, sy in ((x + 1, y), (x, y + 1)):
                        if (sx, sy) in moeda and dentro(sx, sy) and not no_glifo(sx, sy, y0)[0]:
                            px[sx, sy] = simb_sombra + (255,)
    for (x, y) in list(moeda):
        if any((x + dx, y + dy) not in moeda for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = cont + (255,)
    if k == 0:
        bx, by = round(cx - r * 0.45), round(cy - r * 0.5)
        for x, y in ((bx, by), (bx - 1, by), (bx, by - 1)):
            if (x, y) in moeda:
                px[x, y] = brilho + (255,)
    return img.resize((TELA * ESC, TELA * ESC), Image.NEAREST)


def I(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def E(conds, acts, subs=None):
    return {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts, 'events': subs or []}


def var(nome, valor):
    return {'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogos/t84/moeda/{nome}')),
            'type': 'number', 'value': valor}


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho, desenha=True):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    obj = next(o for o in d['objects'] if o['name'] == 'moeda')
    if any(a['name'] == 'x10' for a in obj['animations']):
        sys.exit('t84 já foi aplicada (moeda tem a animação x10); não roda de novo.')

    # 1. imagens e recursos
    os.makedirs(os.path.join(RAIZ, PASTA), exist_ok=True)
    tem = {r['name'] for r in d['resources']['resources']}
    anims = []
    for tipo in TIPOS:
        dia = TIPOS[tipo][1] * ESC
        m0 = (TELA * ESC - dia) / 2
        mascara = [[{'x': m0, 'y': m0}, {'x': m0 + dia, 'y': m0}, {'x': m0 + dia, 'y': m0 + dia},
                    {'x': m0, 'y': m0 + dia}]]
        sprites = []
        for k in range(QUADROS):
            arq = f'{PASTA}/{tipo}_{k:02d}.png'
            if desenha:
                quadro(tipo, k).save(os.path.join(RAIZ, arq))
            if arq not in tem:
                d['resources']['resources'].append({'file': arq, 'kind': 'image', 'metadata': '', 'name': arq,
                                                    'smoothed': False, 'userAdded': True})
            sprites.append({'hasCustomCollisionMask': True, 'image': arq, 'points': [],
                            'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                            'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0},
                            'customCollisionMask': mascara})
        anims.append({'name': tipo, 'useMultipleDirections': False,
                      'directions': [{'looping': True, 'timeBetweenFrames': TEMPO_QUADRO, 'sprites': sprites}]})

    # 2. objeto
    obj['animations'] = anims
    nomes = {v['name'] for v in obj['variables']}
    obj['variables'] += [var(k, v) for k, v in VARS.items() if k not in nomes]

    # 3. eventos
    comb = next(x for x in d['externalEvents'] if x['name'] == 'Combate')['events']
    avisos = []
    queda = next(e for e in todos(comb)
                 if any(a['type']['value'] == 'Create' and a['parameters'][1] == 'moeda' for a in e.get('actions') or []))
    for a in queda['actions']:
        if a['parameters'][:2] == ['moeda', 'Scale'] and a['parameters'][3] == '0.02':
            a['parameters'][3] = 'moeda.escala'
    queda['actions'].append(I('SetNumberObjectVariable', 'moeda', 'sorteio', '=', 'RandomFloat(1)'))
    queda.setdefault('events', []).extend([
        E([I('NumberObjectVariable', 'moeda', 'sorteio', '<', 'moeda.chance_x10')],
          [I('SetNumberObjectVariable', 'moeda', 'mult', '=', '10')]),
        E([I('NumberObjectVariable', 'moeda', 'sorteio', '>=', 'moeda.chance_x10'),
           I('NumberObjectVariable', 'moeda', 'sorteio', '<', 'moeda.chance_x10 + moeda.chance_x5')],
          [I('SetNumberObjectVariable', 'moeda', 'mult', '=', '5')]),
    ])

    grupo = next(e for e in todos(comb) if e.get('type') == 'BuiltinCommonInstructions::Group' and e.get('name') == 'Moeda')
    k = next((i + 1 for i, e in enumerate(grupo['events']) if e['type'] == 'BuiltinCommonInstructions::Comment'), 0)
    anim = lambda n: I('AnimatableCapability::AnimatableBehavior::SetName', 'moeda', 'Animation', '=', f'"{n}"')
    grupo['events'].insert(k, {
        'colorB': 26, 'colorG': 147, 'colorR': 247, 'creationTime': 0, 'name': 'Aparência', 'source': '',
        'type': 'BuiltinCommonInstructions::Group', 'parameters': [],
        'events': [
            {'type': 'BuiltinCommonInstructions::Comment',
             'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
             'comment': 'A moeda vale valor * mult. mult 10 (ou mais) é o Bitcoin (x10), 5 a 9 é o Ethereum (x5) e abaixo '
                        'disso a moeda Doge (x1). Para pôr uma moeda 5x ou 10x na cena, mude a variável mult da instância.',
             'comment2': ''},
            E([I('NumberObjectVariable', 'moeda', 'mult', '>=', '10')], [anim('x10')]),
            E([I('NumberObjectVariable', 'moeda', 'mult', '>=', '5'), I('NumberObjectVariable', 'moeda', 'mult', '<', '10')],
              [anim('x5')]),
            E([I('NumberObjectVariable', 'moeda', 'mult', '<', '5')], [anim('x1')]),
        ]})

    coleta = next(e for e in todos(comb) if e.get('type') == 'BuiltinCommonInstructions::ForEach'
                  and e.get('object') == 'moeda' and any(a['parameters'][:2] == ['pato', 'moedas'] for a in e['actions']))
    troca = {'moeda.valor': 'moeda.valor * moeda.mult',
             '"+"+moeda.valor': '"+" + ToString(moeda.valor * moeda.mult)',
             '"+" + ToString(moeda.valor)': '"+" + ToString(moeda.valor * moeda.mult)'}
    trocados = 0
    for a in coleta['actions']:
        for i, p in enumerate(a['parameters']):
            if p in troca:
                a['parameters'][i] = troca[p]
                trocados += 1
    if trocados != 4:
        avisos.append(f'coleta: {trocados} de 4 expressões trocadas (o evento foi mudado no GDevelop?)')

    # 4. instâncias esticadas no tamanho do bitcoin.png
    lado = TELA * ESC
    for l in d['layouts']:
        for i in l['instances']:
            if i['name'] == 'moeda' and i.get('customSize') and (i.get('width'), i.get('height')) == (VELHO_W, VELHO_H):
                cx, cy = i['x'] + VELHO_W / 2, i['y'] + VELHO_H / 2
                i['x'], i['y'] = cx - lado / 2, cy - lado / 2
                i['customSize'] = False
                i['width'] = i['height'] = lado

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('moedas cripto: x1, x5, x10', *avisos, sep='\n')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
