"""Tarefa 86: três portais no Hub, um para cada fase (Inferno, Purgatório, Paraíso).

- Objeto portal (Sprite, pasta gatilhos): arco de pedra com um redemoinho girando, em pixel art de 40x56 aumentada 4x
  (o mesmo pixel do pato), 8 quadros. Uma animação por cena, com o nome da cena (Inferno, Purgatorio, Paraiso), em
  assets/portais. Máscara de colisão só no miolo do arco.
- Variáveis do portal: cena (para onde leva; também é a animação mostrada), nome (o texto em cima), espera (quantos s
  o pato fica dentro antes de entrar) e nome_altura (px acima do portal). Cada instância do Hub tem cena e nome próprios.
- Objeto portal_nome (texto, mesma fonte da HUD) criado em cima de cada portal no começo da cena.
- Eventos do Hub (grupo Portais, antes da ligação da Loja, que fica por último): no começo a animação vira portal.cena e o nome aparece; parado dentro de um portal
  por portal.espera s (e fora da loja), vai para portal.cena. Cair da borda do Hub (passar de queda_y) volta o pato para volta_x/volta_y.
- A saída provisória (andar até x > 2600 leva ao Inferno) fica desativada, não apagada.
- Instâncias: os três portais à direita do boneco, na ordem das fases, de pé no chão.
Rodar uma vez:  python3 tools/t86_portais_hub.py
"""
import json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = 'assets/portais'
ESC = 4
LW, LH = 40, 56
QUADROS = 8
TEMPO_QUADRO = 0.08
CHAO_Y = 1010                      # topo do chão do Hub
PORTAIS = [('Inferno', 'Inferno', 2080), ('Purgatorio', 'Purgatorio', 2340), ('Paraiso', 'Paraiso', 2600)]   # a fonte não tem acento
PORTAL_VARS = [('cena', 'string', 'Inferno'), ('nome', 'string', 'Inferno'), ('espera', 'number', 0.35),
               ('nome_altura', 'number', 48)]
CENA_VARS = [('queda_y', 'number', CHAO_Y + 1500), ('volta_x', 'number', 1), ('volta_y', 'number', 748)]
NOME_TAMANHO = 26
Z_PORTAL = 20
# moldura (escura, média, clara, detalhe), redemoinho (do escuro ao claro)
TEMAS = {
    'Inferno': ([(34, 24, 28), (62, 44, 48), (96, 68, 70), (200, 70, 30)],
                [(50, 6, 8), (110, 18, 12), (176, 46, 14), (230, 100, 24), (255, 176, 64), (255, 238, 160)]),
    'Purgatorio': ([(52, 54, 50), (92, 96, 86), (138, 140, 126), (120, 150, 110)],
                   [(18, 44, 46), (34, 78, 80), (64, 118, 112), (110, 166, 150), (176, 212, 190), (236, 248, 232)]),
    'Paraiso': ([(132, 130, 150), (196, 196, 214), (246, 246, 255), (226, 186, 84)],
                [(70, 104, 176), (108, 150, 218), (152, 192, 240), (204, 228, 255), (255, 246, 214), (255, 255, 255)]),
}


def arco(x, y, cx, topo, larg, base):
    """Dentro de um arco: lados retos e topo redondo."""
    r = larg / 2
    if y > base or abs(x - cx) > r:
        return False
    if y >= topo + r:
        return True
    return (x - cx) ** 2 + (y - (topo + r)) ** 2 <= r * r


def quadro(tema, k):
    mold, redem = TEMAS[tema]
    img = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))
    px = img.load()
    cx = LW / 2
    fase = k / QUADROS * 2 * math.pi
    for y in range(LH):
        for x in range(LW):
            X, Y = x + 0.5, y + 0.5
            if not arco(X, Y, cx, 2, 36, 52):
                continue
            if arco(X, Y, cx, 6, 28, 50):
                dx, dy = (X - cx) / 14, (Y - 32) / 22
                r = min(1.0, math.hypot(dx, dy))
                v = 0.5 + 0.5 * math.sin(math.atan2(dy, dx) * 2 + r * 9 - fase)
                n = len(redem)
                px[x, y] = redem[max(0, min(n - 1, int((v * 0.45 + (1 - r) * 0.75) * n)))] + (255,)
                continue
            ang = math.atan2(Y - 20, X - cx)
            bloco = int((ang + math.pi) / (math.pi / 7)) if Y < 20 else int(Y / 6)
            junta = (Y >= 20 and int(Y) % 6 == 0) or (Y < 20 and ((ang + math.pi) / (math.pi / 7)) % 1 < 0.12)
            cor = mold[1]
            if junta:
                cor = mold[0]
            elif not arco(X, Y, cx, 3, 34, 52) and X < cx:
                cor = mold[2]
            elif not arco(X, Y, cx, 5, 30, 51) and X > cx:
                cor = mold[2]
            elif (bloco + (1 if X > cx else 0)) % 3 == 0:
                cor = mold[2] if X < cx else mold[1]
            px[x, y] = cor + (255,)
    for y in range(2, 7):                                  # pedra de fecho
        for x in range(int(cx) - 2, int(cx) + 2):
            if img.getpixel((x, y))[3]:
                px[x, y] = mold[3] + (255,)
    for y in range(52, 56):                                # degrau
        for x in range(LW):
            if 1 <= x < LW - 1 or y > 53:
                px[x, y] = (mold[2] if y == 52 else mold[1] if y < 55 else mold[0]) + (255,)
    for s in range(5):                                     # faíscas subindo
        fx = cx - 9 + (s * 37 % 19)
        fy = 48 - ((k * 3 + s * 11) % 36)
        if arco(fx + 0.5, fy + 0.5, cx, 7, 26, 49):
            px[int(fx), int(fy)] = redem[-1] + (255,)
    alfa = [[img.getpixel((x, y))[3] for x in range(LW)] for y in range(LH)]
    for y in range(LH):                                    # contorno
        for x in range(LW):
            if alfa[y][x] and any(not (0 <= x + dx < LW and 0 <= y + dy < LH) or not alfa[y + dy][x + dx]
                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = tuple(max(0, c - 18) for c in mold[0]) + (255,)
    return img.resize((LW * ESC, LH * ESC), Image.NEAREST)


def I(t, *p, inv=False):
    tipo = {'value': t}
    if inv:
        tipo['inverted'] = True
    return {'type': tipo, 'parameters': list(p)}


def E(conds, acts, subs=None):
    return {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts, 'events': subs or []}


def FE(obj, conds, acts, subs=None):
    return {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': conds, 'actions': acts,
            'events': subs or []}


def uid(*partes):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t86/' + '/'.join(map(str, partes))))


def var(dono, nome, tipo, valor):
    return {'name': nome, 'persistentUuid': uid(dono, nome), 'type': tipo, 'value': valor}


def main(caminho, desenha=True):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if any(o['name'] == 'portal' for o in d['objects']):
        sys.exit('t86 já foi aplicada (o objeto portal existe); não roda de novo.')
    hub = next(l for l in d['layouts'] if l['name'] == 'Hub')

    # 1. imagens, recursos e objeto portal
    os.makedirs(os.path.join(RAIZ, PASTA), exist_ok=True)
    tem = {r['name'] for r in d['resources']['resources']}
    m = [[{'x': 6 * ESC, 'y': 8 * ESC}, {'x': 34 * ESC, 'y': 8 * ESC}, {'x': 34 * ESC, 'y': 52 * ESC},
          {'x': 6 * ESC, 'y': 52 * ESC}]]
    anims = []
    for cena in TEMAS:
        sprites = []
        for k in range(QUADROS):
            arq = f'{PASTA}/{cena.lower()}_{k:02d}.png'
            if desenha:
                quadro(cena, k).save(os.path.join(RAIZ, arq))
            if arq not in tem:
                d['resources']['resources'].append({'file': arq, 'kind': 'image', 'metadata': '', 'name': arq,
                                                    'smoothed': False, 'userAdded': True})
            sprites.append({'hasCustomCollisionMask': True, 'image': arq, 'points': [],
                            'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                            'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0},
                            'customCollisionMask': m})
        anims.append({'name': cena, 'useMultipleDirections': False,
                      'directions': [{'looping': True, 'timeBetweenFrames': TEMPO_QUADRO, 'sprites': sprites}]})
    d['objects'].append({'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': 'portal',
                         'persistentUuid': uid('obj', 'portal'), 'type': 'Sprite', 'updateIfNotVisible': False,
                         'variables': [var('portal', n, t, v) for n, t, v in PORTAL_VARS], 'effects': [],
                         'behaviors': [], 'animations': anims})

    # 2. texto do nome (mesmo estilo de hud_arma_nome, maior e branco)
    base = next(o for o in d['objects'] if o['name'] == 'hud_arma_nome')
    nome = json.loads(json.dumps(base))
    nome.update(name='portal_nome', persistentUuid=uid('obj', 'portal_nome'), string='', characterSize=NOME_TAMANHO,
                color={'r': 255, 'g': 255, 'b': 255}, variables=[])
    nome['content'].update(text='', characterSize=NOME_TAMANHO, color='255;255;255')
    d['objects'].append(nome)
    pasta = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'gatilhos')
    pasta.setdefault('children', []).extend([{'objectName': 'portal'}, {'objectName': 'portal_nome'}])

    # 3. variáveis do Hub
    tem_v = {v['name'] for v in hub['variables']}
    hub['variables'] += [var('Hub', n, t, v) for n, t, v in CENA_VARS if n not in tem_v]

    # 4. instâncias
    for cena, nome_txt, cx in PORTAIS:
        hub['instances'].append({
            'angle': 0, 'customSize': False, 'height': LH * ESC, 'layer': '', 'name': 'portal',
            'persistentUuid': uid('inst', cena), 'width': LW * ESC, 'x': cx - LW * ESC / 2, 'y': CHAO_Y - LH * ESC,
            'zOrder': Z_PORTAL, 'numberProperties': [], 'stringProperties': [],
            'initialVariables': [var('inst/' + cena, 'cena', 'string', cena),
                                 var('inst/' + cena, 'nome', 'string', nome_txt)]})

    # 5. eventos
    for e in hub['events']:
        if e.get('type') == 'BuiltinCommonInstructions::Group' and e.get('name') == 'Saída':
            for s in e['events']:
                if s['type'] == 'BuiltinCommonInstructions::Standard' and \
                        any(a['type']['value'] == 'Scene' for a in s.get('actions') or []):
                    s['disabled'] = True
            for s in e['events']:
                if s['type'] == 'BuiltinCommonInstructions::Comment':
                    s['comment'] = 'Desativado: agora o Hub tem os portais (grupo Portais). ' + s['comment']
    loja = [k for k, e in enumerate(hub['events']) if e['type'] == 'BuiltinCommonInstructions::Link'
            and e.get('target') == 'Loja']
    pos = loja[-1] if loja else len(hub['events'])      # a ligação da Loja fica por último
    hub['events'].insert(pos, {
        'colorB': 200, 'colorG': 120, 'colorR': 160, 'creationTime': 0, 'name': 'Portais', 'source': '',
        'type': 'BuiltinCommonInstructions::Group', 'parameters': [],
        'events': [
            {'type': 'BuiltinCommonInstructions::Comment',
             'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
             'comment': 'Um portal por fase. Cada instância tem cena (para onde leva; a animação tem o mesmo nome) e nome '
                        '(o texto em cima). Ficando dentro por portal.espera s, o pato vai para portal.cena. Cair da '
                        'borda (passar de queda_y) volta o pato para volta_x/volta_y.',
             'comment2': ''},
            E([I('SceneJustBegins', '')], [], [
                FE('portal', [], [
                    I('AnimatableCapability::AnimatableBehavior::SetName', 'portal', 'Animation', '=', 'portal.cena'),
                    I('Create', '', 'portal_nome', 'portal.CenterX()', 'portal.Y() - portal.nome_altura', ''),
                    I('TextContainerCapability::TextContainerBehavior::SetValue', 'portal_nome', 'Text', '=', 'portal.nome'),
                    I('SetX', 'portal_nome', '=', 'portal.CenterX() - portal_nome.Width() / 2'),
                    I('ChangePlan', 'portal_nome', '=', 'portal.ZOrder() + 1'),
                ])]),
            FE('portal', [I('CollisionNP', 'pato', 'portal', '', '', '', inv=True)],
               [I('ResetObjectTimer', 'portal', '"dentro"')]),
            FE('portal', [I('CollisionNP', 'pato', 'portal', '', '', ''),
                          I('CompareObjectTimer', 'portal', '"dentro"', '>', 'portal.espera'),
                          I('BooleanObjectVariable', 'pato', 'morto', 'False', ''),
                          I('BooleanObjectVariable', 'pato', 'na_loja', 'False', '')],
               [I('Scene', '', 'portal.cena', '')]),
            E([I('BuiltinCommonInstructions::CompareNumbers', 'pato.Y()', '>', 'queda_y')],
              [I('SetXY', 'pato', '=', 'volta_x', '=', 'volta_y'),
               I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed', 'pato', 'PlatformerObject', '=', '0')]),
        ]})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('portais no Hub: Inferno, Purgatório, Paraíso')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
