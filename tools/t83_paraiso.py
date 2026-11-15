"""Tarefa 83: cena Paraiso, a subida pelas esferas do céu até o Empíreo (Dante, Paraíso).

A fase é aberta: ilhas de mármore (templos em ruína) sobre nuvens, com o céu embaixo. Vai da esquerda para a direita
subindo, em quatro trechos:

    portão  ->  1 esfera da Lua: ilhas e pontes de nuvem (tiles_ceu_ponte) em escada, querubins atirando flechas
            ->  2 esfera do Sol: um abismo atravessado nas correntes de luz (corrente_luz), com serafins
            ->  3 esfera das Estrelas: um chão comprido com rodas de anjo rolando e um ofanim por cima, e a subida
                  em nuvens até a última ilha
            ->  4 Empíreo: a última corrente de luz, a mais alta, até o terraço do templo, onde fica a saída

Mecânica nova, corrente_luz (eventos externos CorrentesDeLuz): coluna de luz (tiled sprite, estica na altura que quiser)
que, acesa, ergue o pato a forca px/s enquanto ele está dentro dela; no topo ele flutua e sai para o lado. Ela pisca em
ciclo: acesa por ligada s, apagada por desligada s, e nos últimos aviso s acesa ela tremula avisando; defasagem
desencontra as colunas. Apagada não segura nada.

Queda: o céu não tem chão. Passando de queda_y, o pato perde queda_dano e volta para o último lugar em que pisou
(retorno_x, retorno_y, guardados a cada quadro com ele no chão). Inimigo que cai some.

Tiles como no Purgatório: tiles_ceu (terreno, bordas pelos vizinhos), tiles_ceu_ponte (nuvens, atravessáveis por
baixo) e tiles_ceu_decor (colunas, cercas douradas, entulho, a árvore seca, fiapos de nuvem embaixo das ilhas e a
fachada do templo no Empíreo). Na camada Fundo, nuvens (bg_paraiso_nuvens) e a rosa de luz do Empíreo
(bg_paraiso_rosa), em parallax (fundo_parallax_x/y, fundo_dx/dy). Saída: centro entre saida_x_min e saida_x_max e pé
acima de saida_y -> proxima_cena.

Migração de uso único que só ADICIONA: se a cena Paraiso já existe, não faz nada. HUD, pato e companhia são cópias das
instâncias do Purgatório. Imagens novas em assets/paraiso.
Rodar uma vez:  python3 tools/t83_paraiso.py
"""
import copy, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENA, MOLDE = 'Paraiso', 'Purgatorio'
PASTA = 'assets/paraiso'
COR_FUNDO = (172, 196, 232)                 # céu claro
T = 64
W, H = 190, 92                              # colunas x linhas do mapa (linha 0 em cima)
X0, Y0 = 0, 768 - 82 * T                    # o chão do portão (linha 82) fica com o topo em y 768

# Ilhas de mármore: (col_ini, col_fim, linha do topo, espessura)
ILHAS = [
    (0, 16, 82, 5),                                        # portão
    (26, 33, 77, 3), (43, 52, 71, 3), (67, 78, 62, 4),     # esfera da Lua
    (86, 93, 49, 3), (101, 110, 34, 3),                    # esfera do Sol (entre as correntes)
    (113, 142, 36, 4), (156, 160, 21, 3),                  # esfera das Estrelas
    (166, 189, 6, 4),                                      # Empíreo
]
# Nuvens (ponte): (col_ini, col_fim, linha)
NUVENS = [(19, 23, 80), (36, 40, 74), (55, 58, 68), (61, 64, 64),
          (145, 148, 31), (150, 153, 26)]
# Correntes de luz: (col, largura em tiles, linha do topo, defasagem s). Vão até o fundo do mapa.
CORRENTES = [(81, 2, 46, 0.0), (96, 2, 31, 1.2), (162, 2, 3, 0.6)]
# Inimigos: (nome, coluna, linha do pé/centro)
INIMIGOS = [('querubim', 30, 70), ('querubim', 48, 63), ('querubim', 73, 53), ('serafim', 89, 41),
            ('serafim', 106, 26), ('roda_anjo', 121, 34), ('roda_anjo', 135, 34), ('ofanim', 128, 24),
            ('querubim', 152, 17), ('querubim', 172, 0)]
# Moedas flutuantes: (coluna, linha do centro)
MOEDAS = [(8, 79), (21, 77), (29, 74), (38, 71), (47, 68), (56, 65), (62, 61), (72, 59), (82, 56), (82, 50),
          (89, 46), (97, 40), (97, 33), (105, 31), (116, 33), (124, 33), (132, 33), (140, 33), (146, 28),
          (151, 23), (158, 18), (163, 14), (163, 8), (170, 3), (178, 3)]
SAIDA = (178, 189)                          # colunas da área de saída no Empíreo

# Enfeites de tiles_ceu_decor (de baixo para cima, cada linha da esquerda para a direita) e peso no sorteio
ENFEITES = [([[111]], 6), ([[112]], 5), ([[113]], 5), ([[128]], 3), ([[129]], 3), ([[130]], 3), ([[145]], 2),
            ([[146, 147]], 2), ([[13]], 2), ([[14]], 2), ([[30]], 2), ([[31]], 2),
            ([[66, 67]], 2), ([[49]], 1), ([[50]], 1), ([[98], [81]], 2), ([[64], [47]], 2), ([[99], [82], [65]], 2),
            ([[100, 101], [83, 84]], 1.5), ([[149, 150], [132, 133], [115, 116]], 1)]
TEMPLO = [[32, 33], [15, 16]]
FIAPO = [[131], [148]]                      # fiapo de nuvem pendurado (de cima para baixo)
SEMENTE = 83
NUVENS_FUNDO = 9                            # cúmulos por ladrilho do fundo
AFUNILA = 4                                 # linhas da ponta de baixo das ilhas

CORRENTE_VARS = dict(forca=620, ligada=3.2, desligada=1.4, aviso=0.6, defasagem=0, t=0, ativa=True,
                     opacidade_ligada=230, opacidade_desligada=40, pisca_vel=28)
CENA_VARS = dict(fundo_parallax_x=0.12, fundo_parallax_y=0.12, fundo_dx=0, fundo_dy=0, queda_dano=15, queda_volume=70,
                 proxima_cena='Hub')


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t83/' + nome))


def var(dono, nome, valor):
    tipo = 'boolean' if isinstance(valor, bool) else 'string' if isinstance(valor, str) else 'number'
    return {'name': nome, 'persistentUuid': uid(f'var/{dono}/{nome}'), 'type': tipo, 'value': valor}


def px(c, r):
    return X0 + c * T, Y0 + r * T


# ---------------------------------------------------------------- imagens

def img_corrente():
    """Coluna de luz, 64 x 64 desenhada e ampliada 2x; emenda na vertical."""
    w, h = 64, 64
    x = np.arange(w)[None, :].repeat(h, 0).astype(float)
    y = np.arange(h)[:, None].repeat(w, 1).astype(float)
    d = np.abs(x - (w - 1) / 2) / (w / 2)
    a = np.clip(1 - d ** 1.6, 0, 1)
    raias = 0.75 + 0.25 * np.sin(x * 0.9 + 2 * np.sin(y * 2 * math.pi / h * 2))
    a = a * raias
    a = np.floor(a * 6) / 6                                         # degraus, cara de pixel art
    cor = np.zeros((h, w, 4))
    miolo = np.clip(1 - d * 2.2, 0, 1)
    cor[..., 0] = 255
    cor[..., 1] = 226 + 29 * miolo
    cor[..., 2] = 140 + 110 * miolo
    cor[..., 3] = a * 190
    rng = np.random.default_rng(7)
    for _ in range(26):                                             # faíscas subindo
        cx, cy = rng.integers(10, w - 10), rng.integers(0, h)
        cor[cy, cx] = (255, 255, 245, 255)
        cor[(cy + 1) % h, cx, 3] = max(cor[(cy + 1) % h, cx, 3], 150)
    im = Image.fromarray(cor.clip(0, 255).astype(np.uint8), 'RGBA')
    return im.resize((w * 2, h * 2), Image.NEAREST)


def img_nuvens():
    """Nuvens em fundo transparente: cúmulos soltos (bolotas sobrepostas, base reta, sombra embaixo), 512 x 512
    ampliado 2x; emenda nos dois sentidos (cada bolota é desenhada também do outro lado da borda)."""
    n = 512
    rng = np.random.default_rng(11)
    a = np.zeros((n, n))                                     # 0 vazio, 1 sombra, 2 corpo, 3 brilho
    yy, xx = np.mgrid[0:n, 0:n]
    for _ in range(NUVENS_FUNDO):
        cx, base = rng.integers(0, n), rng.integers(0, n)
        larg = rng.integers(40, 110)
        for k in range(rng.integers(3, 6)):
            bx = cx + rng.integers(-larg // 2, larg // 2)
            rr = rng.integers(12, 26) * (1.25 if k == 0 else 1)
            by = base - rr * 0.6
            for ox in (-n, 0, n):
                for oy in (-n, 0, n):
                    d = ((xx - bx - ox) ** 2 + (yy - by - oy) ** 2) / rr ** 2
                    dentro = (d < 1) & ((yy - oy) <= base)
                    a = np.where(dentro, np.maximum(a, 2), a)
                    brilho = dentro & (((xx - bx - ox + rr * 0.25) ** 2 + (yy - by - oy + rr * 0.3) ** 2) / rr ** 2 < 0.4)
                    a = np.where(brilho, 3, a)
                    sombra = dentro & ((yy - oy) > base - 5)
                    a = np.where(sombra & (a < 3), 1, a)
    cores = {1: (206, 214, 238, 150), 2: (238, 242, 252, 190), 3: (255, 253, 246, 215)}
    out = np.zeros((n, n, 4), np.uint8)
    for k, c in cores.items():
        out[a == k] = c
    return Image.fromarray(out, 'RGBA').resize((n * 2, n * 2), Image.NEAREST)


def img_rosa():
    """A rosa de luz do Empíreo: anéis de pétalas em volta de um clarão, 384 x 384 ampliado 2x."""
    n = 384
    y, x = np.mgrid[0:n, 0:n].astype(float) - (n - 1) / 2
    r = np.hypot(x, y) / (n / 2)
    th = np.arctan2(y, x)
    a = np.zeros((n, n))
    for k, (raio, petalas, giro) in enumerate(((0.32, 8, 0), (0.5, 12, 0.2), (0.68, 16, 0.1), (0.86, 24, 0.3))):
        borda = raio + 0.06 * np.cos(petalas * th + giro) ** 2
        a = np.maximum(a, np.clip(1 - np.abs(r - borda) * 30, 0, 1) * (0.9 - 0.12 * k))
    a = np.maximum(a, np.clip(1 - r / 0.3, 0, 1) ** 1.5)
    a = np.maximum(a, np.clip(1 - r, 0, 1) * 0.25)
    a = np.floor(a * 7) / 7
    out = np.zeros((n, n, 4))
    out[..., 0] = 255
    out[..., 1] = 236 + 19 * np.clip(1 - r * 2, 0, 1)
    out[..., 2] = 170 + 80 * np.clip(1 - r * 2, 0, 1)
    out[..., 3] = a * 235
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').resize((n * 2, n * 2), Image.NEAREST)


# ---------------------------------------------------------------- mapa

def solidos():
    s = set()
    for c0, c1, topo, esp in ILHAS:
        for c in range(c0, c1 + 1):
            for r in range(topo, topo + esp):
                s.add((c, r))
        a, b, r = c0, c1, topo + esp                                # embaixo a ilha afunila, como rocha flutuando
        while True:
            k = r - topo - esp
            a, b = a + 1 + k % 2, b - 1 - (k + 1) % 2
            if b - a < 1 or k >= AFUNILA:
                break
            s.update((c, r) for c in range(a, b + 1))
            r += 1
    return s


def autotile(s):
    grade = [[-1] * W for _ in range(H)]
    for (c, r) in s:
        cheio = lambda dc, dr: (c + dc, r + dr) in s
        cima, baixo, esq, dir_ = (not cheio(0, -1)), (not cheio(0, 1)), (not cheio(-1, 0)), (not cheio(1, 0))
        var2 = (c * 7 + r * 3) % 5 == 0
        if cima and baixo:
            t = 26 if esq and not dir_ else 28 if dir_ and not esq else 4
        elif cima:
            t = 0 if esq else 2 if dir_ else (52 if var2 else 1)
        elif baixo:
            t = 34 if esq else 36 if dir_ else (86 if var2 else 35)
        elif esq:
            t = 68 if var2 else 17
        elif dir_:
            t = 70 if var2 else 19
        elif not cheio(1, -1):
            t = 40
        elif not cheio(-1, -1):
            t = 42
        elif not cheio(1, 1):
            t = 6
        elif not cheio(-1, 1):
            t = 8
        else:
            t = 144
        grade[r][c] = t
    return grade


def mapa_nuvens():
    grade = [[-1] * W for _ in range(H)]
    for c0, c1, r in NUVENS:
        for c in range(c0, c1 + 1):
            grade[r][c] = 142 if c0 == c1 else 125 if c == c0 else 127 if c == c1 else 126
    return grade


def mapa_enfeites(s, ponte):
    rng = random.Random(SEMENTE)
    grade = [[-1] * W for _ in range(H)]
    usado = set()
    livre = lambda c, r: 0 <= c < W and 0 <= r < H and (c, r) not in s and (c, r) not in ponte and (c, r) not in usado

    def poe(desenho, c, r_base, para_baixo=False):
        cel = [(c + j, r_base + k if para_baixo else r_base - k, v) for k, linha in enumerate(desenho) for j, v in enumerate(linha)]
        if not all(livre(x, y) for x, y, _ in cel):
            return False
        for x, y, v in cel:
            grade[y][x] = v
            usado.add((x, y))
        return True

    # fachada do templo no Empíreo, antes da saída
    c0, c1, topo, _ = ILHAS[-1]
    for c in (SAIDA[0] - 4, SAIDA[0] - 2):
        poe(TEMPLO, c, topo - 1)
    corr = {c + k for c, w, _, _ in CORRENTES for k in range(-1, w + 1)}
    pesos = [p for _, p in ENFEITES]
    for c0, c1, topo, esp in ILHAS:
        c = c0 + rng.randint(0, 2)
        while c <= c1:
            desenho = rng.choices([d for d, _ in ENFEITES], pesos)[0]
            if c + len(desenho[0]) - 1 <= c1 and not any(c + j in corr for j in range(len(desenho[0]))) \
                    and not (ILHAS[-1][0] <= c and SAIDA[0] - 5 <= c):
                poe(desenho, c, topo - 1)
            c += len(desenho[0]) + rng.randint(1, 4)
    for (c, r) in sorted(s):                                            # fiapos embaixo das ilhas
        if (c, r + 1) not in s and (c, r - 1) in s and rng.random() < 0.18:
            poe(FIAPO, c, r + 1, para_baixo=True)
    return grade


def tilemap(grade):
    return json.dumps({'tileWidth': T, 'tileHeight': T, 'dimX': len(grade[0]), 'dimY': len(grade),
                       'layers': [{'id': 0, 'alpha': 1, 'tiles': grade}]}, separators=(',', ':'))


def inst(nome, chave, x, y, z, camada='', w=None, h=None, extra=None, variaveis=()):
    i = {'angle': 0, 'customSize': w is not None, 'height': h or 0, 'keepRatio': True, 'layer': camada, 'name': nome,
         'persistentUuid': uid(chave), 'width': w or 0, 'x': x, 'y': y, 'zOrder': z, 'numberProperties': [],
         'stringProperties': [], 'initialVariables': list(variaveis)}
    if extra:
        i.update(extra)
    return i


def inst_tilemap(nome, chave, z, grade):
    i = inst(nome, chave, X0, Y0, z)
    i['stringProperties'] = [{'name': 'tilemap', 'value': tilemap(grade)}]
    return i


# ---------------------------------------------------------------- eventos

def I(t, *p, inv=False):
    d = {'type': {'value': t}, 'parameters': list(p)}
    if inv:
        d['type']['inverted'] = True
    return d


def E(c=(), a=(), s=()):
    return {'type': 'BuiltinCommonInstructions::Standard', 'conditions': list(c), 'actions': list(a), 'events': list(s)}


def FE(obj, c=(), a=(), s=()):
    return {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': list(c), 'actions': list(a),
            'events': list(s)}


def G(nome, evs):
    return {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': nome, 'source': '',
            'type': 'BuiltinCommonInstructions::Group', 'events': evs, 'parameters': []}


def COM(txt):
    return {'type': 'BuiltinCommonInstructions::Comment',
            'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0}, 'comment': txt, 'comment2': ''}


def link(alvo):
    return {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': alvo}


def cmp(a, op, b):
    return I('BuiltinCommonInstructions::CompareNumbers', a, op, b)


def eventos_correntes():
    c = 'corrente_luz'
    fase = f'mod({c}.t + {c}.defasagem, {c}.ligada + {c}.desligada)'
    opac = lambda x: I('OpacityCapability::OpacityBehavior::SetValue', c, 'Opacity', '=', x)
    return [
        COM('Correntes de luz (corrente_luz): acesa por ligada s e apagada por desligada s, em ciclo (defasagem desencontra '
            'as colunas). Nos últimos aviso s acesa ela tremula. Acesa, ergue o pato a forca px/s enquanto ele está dentro '
            '(e zera a queda, para a gravidade não acumular); no topo ele flutua e sai para o lado.'),
        FE(c, [], [I('SetNumberObjectVariable', c, 't', '+', 'TimeDelta()')], [
            E([cmp(fase, '<', f'{c}.ligada')], [I('SetBooleanObjectVariable', c, 'ativa', 'True', ''),
                                                 opac(f'{c}.opacidade_ligada')]),
            E([cmp(fase, '>=', f'{c}.ligada')], [I('SetBooleanObjectVariable', c, 'ativa', 'False', ''),
                                                  opac(f'{c}.opacidade_desligada')]),
            E([I('BooleanObjectVariable', c, 'ativa', 'True', ''), cmp(fase, '>', f'{c}.ligada - {c}.aviso')],
              [opac(f'{c}.opacidade_ligada * (0.55 + 0.45 * sin(TimeFromStart() * {c}.pisca_vel))')]),
        ]),
        FE(c, [I('BooleanObjectVariable', c, 'ativa', 'True', ''), I('CollisionNP', 'pato', c, '', '', ''),
               I('BooleanObjectVariable', 'pato', 'morto', 'False', ''),
               cmp('pato.Y() + pato.Height()', '>', f'{c}.Y()')], [
            I('SetY', 'pato', '-', f'{c}.forca * TimeDelta()'),
            I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed', 'pato', 'PlatformerObject', '=', '0')]),
    ]


def eventos_cena():
    return [
        COM('Paraíso: a subida pelas esferas até o Empíreo. Esfera da Lua (ilhas e nuvens, querubins), do Sol (correntes '
            'de luz sobre o abismo, serafins), das Estrelas (chão comprido com rodas e um ofanim, subida em nuvens) e o '
            'Empíreo (a última corrente até o templo). Na saída vai para proxima_cena.'),
        link('Jogador'), link('AplicarUpgrades'), link('Inimigos'), link('Combate'), link('HUD'), link('CorrentesDeLuz'),
        G('Fundo em parallax', [E([], [
            I('SetCameraCenterX', '', '=', 'CameraCenterX("", 0) * fundo_parallax_x + fundo_dx', '"Fundo"', '0'),
            I('SetCameraCenterY', '', '=', 'CameraCenterY("", 0) * fundo_parallax_y + fundo_dy', '"Fundo"', '0')])]),
        G('Queda do céu', [
            COM('Com o pato no chão (e vivo), guarda onde ele pisou. Passando de queda_y perde queda_dano e volta para lá. '
                'Inimigo que passa de queda_y some.'),
            E([I('PlatformBehavior::IsOnFloor', 'pato', 'PlatformerObject'), I('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
              [I('SetNumberVariable', 'retorno_x', '=', 'pato.X()'), I('SetNumberVariable', 'retorno_y', '=', 'pato.Y()')]),
            E([cmp('pato.Y()', '>', 'queda_y'), I('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
              [I('SetNumberObjectVariable', 'pato', 'vida', '-', 'queda_dano'),
               I('ResetObjectTimer', 'pato', '"iframes"'),
               I('SetXY', 'pato', '=', 'retorno_x', '=', 'retorno_y'),
               I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed', 'pato', 'PlatformerObject', '=', '0'),
               I('PlaySound', '', 'som_pato_dano.wav', '', 'queda_volume', '1')]),
            FE('Inimigo', [cmp('Inimigo.Y()', '>', 'queda_y')], [I('Delete', 'Inimigo', '')]),
        ]),
        G('Saída no Empíreo', [E([
            I('BooleanObjectVariable', 'pato', 'morto', 'False', ''),
            cmp('pato.CenterX()', '>=', 'saida_x_min'), cmp('pato.CenterX()', '<=', 'saida_x_max'),
            cmp('pato.Y() + pato.Height()', '<=', 'saida_y')], [I('Scene', '', 'proxima_cena', '')])]),
    ]


# ---------------------------------------------------------------- migração

def recurso(caminho):
    return {'file': caminho, 'kind': 'image', 'metadata': '', 'name': caminho, 'smoothed': False, 'userAdded': True}


def sprite(nome, imagem, w, h, variaveis=()):
    return {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': nome, 'persistentUuid': uid('obj/' + nome),
            'type': 'Sprite', 'updateIfNotVisible': False, 'variables': list(variaveis), 'effects': [], 'behaviors': [],
            'animations': [{'name': 'idle', 'useMultipleDirections': False, 'directions': [{
                'looping': True, 'timeBetweenFrames': 0.1, 'sprites': [{
                    'hasCustomCollisionMask': False, 'image': imagem, 'points': [],
                    'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                    'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': []}]}]}]}


def tiled(nome, textura, w, h, variaveis=()):
    return {'assetStoreId': '', 'height': h, 'name': nome, 'persistentUuid': uid('obj/' + nome), 'texture': textura,
            'type': 'TiledSpriteObject::TiledSprite', 'width': w, 'variables': list(variaveis), 'effects': [], 'behaviors': []}


def pasta(d, caminho):
    f = d['objectsFolderStructure']
    for parte in caminho.split('/'):
        f = next(c for c in f['children'] if c.get('folderName') == parte)
    return f


def migra(d):
    if any(l['name'] == CENA for l in d['layouts']):
        return False
    molde = next(l for l in d['layouts'] if l['name'] == MOLDE)
    hub = next(l for l in d['layouts'] if l['name'] == 'Hub')
    obj = {o['name']: o for o in d['objects']}

    # recursos e objetos novos
    nomes_rec = {r['name'] for r in d['resources']['resources']}
    for arq in ('corrente_luz.png', 'bg_nuvens.png', 'bg_rosa.png'):
        if f'{PASTA}/{arq}' not in nomes_rec:
            d['resources']['resources'].append(recurso(f'{PASTA}/{arq}'))
    if 'corrente_luz' not in obj:
        d['objects'].append(tiled('corrente_luz', f'{PASTA}/corrente_luz.png', 128, 128,
                                  [var('corrente_luz', k, v) for k, v in CORRENTE_VARS.items()]))
        pasta(d, 'cenario/plataformas')['children'].append({'objectName': 'corrente_luz'})
    if 'bg_paraiso_nuvens' not in obj:
        d['objects'].append(tiled('bg_paraiso_nuvens', f'{PASTA}/bg_nuvens.png', 1024, 1024))
        d['objects'].append(sprite('bg_paraiso_rosa', f'{PASTA}/bg_rosa.png', 768, 768))
        pasta(d, 'cenario/bg')['children'] += [{'objectName': 'bg_paraiso_nuvens'}, {'objectName': 'bg_paraiso_rosa'}]
    if not any(e['name'] == 'CorrentesDeLuz' for e in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': CENA, 'lastChangeTimeStamp': 0, 'name': 'CorrentesDeLuz',
                                    'events': eventos_correntes()})

    s = solidos()
    ponte = {(c, r) for c0, c1, r in NUVENS for c in range(c0, c1 + 1)}

    # HUD, pato e companhia: cópias do Purgatório
    comuns = {i['name'] for i in hub['instances']} & {i['name'] for i in molde['instances']}
    comuns = {n for n in comuns if not n.startswith(('tiles_', 'bg_'))}
    instancias = []
    for i in molde['instances']:
        if i['name'] in comuns:
            n = copy.deepcopy(i)
            n['persistentUuid'] = uid('copia/' + i['persistentUuid'])
            for v in n.get('initialVariables', []):
                v['persistentUuid'] = uid('copia/' + i['persistentUuid'] + '/' + v['name'])
            instancias.append(n)
    pato = next(i for i in instancias if i['name'] == 'pato')
    pato['x'], pato['y'] = px(4, 0)[0], px(0, ILHAS[0][2])[1] - pato['height']
    alvo = next((i for i in instancias if i['name'] == 'alvo'), None)
    if alvo is not None and alvo.get('layer', '') == '':
        alvo['x'], alvo['y'] = pato['x'] + 300, pato['y']

    # fundo
    instancias.append(inst('bg_paraiso_nuvens', 'fundo/nuvens', -2400, -2400, 1, 'Fundo', 7200, 4800))
    instancias.append(inst('bg_paraiso_rosa', 'fundo/rosa', 1500, -700, 2, 'Fundo'))
    # terreno, nuvens e enfeites
    instancias.append(inst_tilemap('tiles_ceu_decor', 'enfeites', 3, mapa_enfeites(s, ponte)))
    instancias.append(inst_tilemap('tiles_ceu', 'terreno', 4, autotile(s)))
    instancias.append(inst_tilemap('tiles_ceu_ponte', 'nuvens', 6, mapa_nuvens()))
    # correntes de luz, do topo até o fundo do mapa
    for k, (c, w, r, defas) in enumerate(CORRENTES):
        x, y = px(c, r)
        instancias.append(inst('corrente_luz', f'corrente/{k}', x, y, 5, '', w * T, (H - r) * T,
                               variaveis=[var(f'corrente{k}', 'defasagem', defas)] if defas else []))
    # inimigos (pé na linha dada para os que andam; centro para os que voam)
    for k, (nome, c, r) in enumerate(INIMIGOS):
        x, y = px(c, r)
        if nome == 'roda_anjo':
            y -= 92
        instancias.append(inst(nome, f'inimigo/{k}', x, y, 2804))
    # moedas
    moeda = next((i for i in molde['instances'] if i['name'] == 'moeda'), None)
    mw, mh = (moeda['width'], moeda['height']) if moeda else (103, 60)
    for k, (c, r) in enumerate(MOEDAS):
        cx, cy = X0 + c * T + T / 2, Y0 + r * T + T / 2
        instancias.append(inst('moeda', f'moeda/{k}', round(cx - mw / 2), round(cy - mh / 2), 1004, '', mw, mh,
                               variaveis=[var(f'moeda{k}', 'tem_gravidade', False)], extra={'depth': 1}))

    # variáveis da cena: as que as folhas comuns usam (do Purgatório) e as desta fase
    comuns_v = ('laser_x', 'laser_y', 'exp_d', 'soco_rx', 'soco_ry', 'olho_rx', 'olho_ry', 'moscas_alerta',
                'moscas_alerta_x', 'moscas_alerta_y')
    variaveis = [copy.deepcopy(v) for v in molde['variables'] if v['name'] in comuns_v]
    topo_emp = Y0 + ILHAS[-1][2] * T
    variaveis += [var(CENA, k, v) for k, v in CENA_VARS.items()]
    variaveis += [var(CENA, 'saida_x_min', X0 + SAIDA[0] * T), var(CENA, 'saida_x_max', X0 + (SAIDA[1] + 1) * T),
                  var(CENA, 'saida_y', topo_emp + 8), var(CENA, 'queda_y', Y0 + (H + 4) * T),
                  var(CENA, 'retorno_x', pato['x']), var(CENA, 'retorno_y', pato['y'])]

    cena = {'b': COR_FUNDO[2], 'disableInputWhenNotFocused': True, 'mangledName': CENA, 'name': CENA,
            'r': COR_FUNDO[0], 'standardSortMethod': True, 'stopSoundsOnStartup': True, 'title': '', 'v': COR_FUNDO[1],
            'uiSettings': copy.deepcopy(molde['uiSettings']), 'objectsGroups': [], 'variables': variaveis,
            'instances': instancias, 'objects': [], 'objectsFolderStructure': {'folderName': '__ROOT'},
            'events': eventos_cena(), 'layers': copy.deepcopy(molde['layers']),
            'behaviorsSharedData': copy.deepcopy(molde['behaviorsSharedData'])}
    for camada in cena['layers']:
        camada['visibility'] = True          # no Purgatório a camada HUD ficou escondida no editor
    pos = next(k for k, l in enumerate(d['layouts']) if l['name'] == MOLDE) + 1
    d['layouts'].insert(pos, cena)
    return True


def main(caminho):
    os.makedirs(os.path.join(RAIZ, PASTA), exist_ok=True)
    for arq, f in (('corrente_luz.png', img_corrente), ('bg_nuvens.png', img_nuvens), ('bg_rosa.png', img_rosa)):
        destino = os.path.join(RAIZ, PASTA, arq)
        if not os.path.exists(destino):
            f().save(destino)
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if not migra(d):
        print('cena', CENA, 'já existe; nada feito')
        return
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cena', CENA, 'criada')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
