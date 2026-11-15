"""Tarefa 72: cena Purgatorio, uma fase de subida vertical do começo ao fim, sem chefe.

A fase é uma fenda na montanha do purgatório: um paredão à esquerda (a montanha) e outro à direita, e o pato sobe
do pé da montanha até o cume, onde fica a saída. O caminho tem quatro trechos separados por terraços largos (as
cornijas), cada um com um jeito de subir:

    pé da montanha  ->  1 encosta: ilhas de pedra e troncos em zigue-zague até o 1º terraço
                    ->  2 troncos sobre o vazio, depois a chaminé (ressaltos alternados entre o paredão e um
                          pilar de pedra, cada um 6 tiles acima do outro: pulo duplo) até o topo do pilar
                    ->  3 uma ilha e a roda do pilar (três troncos girando, tools/t73_plataforma_radial.py) até
                          os troncos que levam ao 2º terraço
                    ->  4 uma ilha, a roda final (dois troncos girando ao contrário) e a escadaria de troncos
                          até o cume

Os tiles seguem o Inferno: um tile map só para o terreno (tiles_purgatorio, com as bordas, quinas e quinas de
dentro escolhidas pelos vizinhos, o miolo com o tile liso 144), tiles_purgatorio_ponte para os troncos
(atravessáveis por baixo) e tiles_purgatorio_decor para árvores, pedras, cipós e, na camada Fundo, a serra ao
longe. A camada Fundo anda com a câmera multiplicada por fundo_parallax_x/y (mais fundo_dx/dy).

Saída: quando o pato está no cume (centro entre saida_x_min e saida_x_max, pé acima de saida_y), vai para a cena
proxima_cena. Moedas flutuantes (tem_gravidade falso) marcam o caminho.

Migração de uso único que só ADICIONA: se a cena Purgatorio já existe, não faz nada. HUD, pato, mira e companhia
são cópias das instâncias do Inferno (com persistentUuid novos); camadas e dados de comportamento também vêm de
lá. Depois de criada, a cena é sua: o script não volta nenhum valor.
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENA, MOLDE = 'Purgatorio', 'Inferno'
COR_FUNDO = (128, 138, 128)                 # céu de névoa, apagado
T = 64
W, H = 60, 166                              # colunas x linhas do mapa; h conta de baixo (0) para cima
X0 = 0
Y0 = 768 - (H - 4) * T                      # o chão do pé da montanha (h 3) fica com o topo em y 768

# Paredão da esquerda: (h_ini, h_fim, última coluna sólida). Os trechos largos são os terraços.
PAREDAO_ESQ = [(4, 11, 10), (12, 13, 19), (14, 30, 12), (31, 33, 30), (34, 51, 13), (52, 92, 16),
               (93, 118, 14), (119, 121, 26), (122, 144, 15), (145, 146, 21), (147, 159, 16), (160, 162, 24)]
RESSALTOS_ESQ = [58, 70, 82]                # ressaltos da chaminé no paredão (colunas 17-19)
# Paredão da direita: (h_ini, h_fim, primeira coluna sólida)
PAREDAO_DIR = [(0, 40, 49), (41, 90, 51), (91, 130, 53), (131, H - 1, 50)]
# Pilar da chaminé: colunas 25-30, h 58-92, com ressaltos de 22-24 do lado da chaminé
PILAR = (25, 30, 58, 92)
RESSALTOS_PILAR = [64, 76, 88]
# Ilhas de pedra soltas: (col_ini, col_fim, h_ini, h_fim)
ILHAS = [(25, 31, 7, 8), (34, 40, 26, 28), (33, 38, 96, 97), (30, 35, 126, 127)]
# Troncos (ponte, atravessável por baixo): (col_ini, col_fim, h)
TRONCOS = [(22, 26, 18), (28, 32, 22),                                       # trecho 1
           (34, 38, 38), (40, 44, 42), (33, 37, 46), (26, 30, 49), (17, 24, 52),   # trecho 2 (até a chaminé)
           (30, 34, 116),                                                     # trecho 3 (o resto é a roda do pilar)
           (24, 28, 141), (25, 29, 151), (27, 31, 156)]                       # trecho 4 (depois da roda final)
CUME_S = 163                                # linha em que o pato fica de pé no cume

# Enfeites (tiles_purgatorio_decor): (coluna, linha de pé h, desenho de baixo para cima, cada linha da esquerda p/ direita)
PINHO = [[98], [81]]
PINHO_ALTO = [[99], [82], [65]]
ARVORE = [[100, 101], [83, 84]]
ARVORE_MORTA = [[149, 150], [132, 133], [115, 116]]
TRONCO_SECO = [[64], [47]]
ENFEITES = [
    # pé da montanha
    (12, 4, PINHO_ALTO), (17, 4, [[31]]), (19, 4, [[66, 67]]), (23, 4, [[128]]), (35, 4, ARVORE), (38, 4, [[146, 147]]),
    (41, 4, [[49, 50]]), (44, 4, PINHO), (46, 4, [[30]]),
    (13, 14, [[112]]), (16, 14, [[50]]), (27, 9, [[111]]), (36, 29, [[113]]),
    # 1º terraço
    (14, 34, ARVORE_MORTA), (17, 34, [[66]]), (19, 34, PINHO), (21, 34, [[14]]), (23, 34, [[129]]), (25, 34, PINHO_ALTO),
    (27, 34, [[49, 50]]),
    # chaminé e topo do pilar
    (26, 93, TRONCO_SECO), (28, 93, [[112]]), (35, 98, [[130]]),
    # 2º terraço
    (16, 122, [[145]]), (17, 122, ARVORE), (20, 122, [[31]]), (22, 122, PINHO_ALTO), (24, 122, [[67]]),
    (31, 128, [[113]]), (18, 147, [[30]]), (20, 147, [[111]]),
    # cume
    (4, 163, PINHO_ALTO), (6, 163, ARVORE), (9, 163, [[146, 147]]), (12, 163, [[14]]), (14, 163, ARVORE_MORTA),
    (17, 163, [[66, 67]]), (20, 163, PINHO), (22, 163, [[128]]), (23, 163, [[49]]),
]
CIPO_FREQ = 3                                # um cipó a cada 3 colunas embaixo de ilhas e terraços

# Moedas flutuantes: (coluna do centro, linha h do centro)
MOEDAS = [(28, 12), (24, 22), (30, 26), (37, 32), (24, 37), (36, 42), (42, 46), (35, 50), (28, 53), (20, 56),
          (18, 63), (23, 69), (18, 75), (23, 81), (18, 87), (23, 93), (41, 99), (46, 106), (41, 113), (36, 106),
          (32, 120), (38, 129), (43, 134), (33, 136), (38, 140), (26, 145), (27, 155), (29, 160), (8, 166)]

# Serra ao longe (camada Fundo): blocos de cumeeira de 5 tiles (102-106 por cima, 119/143/121/143/123 embaixo,
# 143 até o pé), sobrepostos de FUNDO_PASSO em FUNDO_PASSO colunas, com o topo descendo FUNDO_INCLINA linha por coluna
# a partir do pico; mais uma serra baixa (FUNDO_SOPE) por toda a largura.
FUNDO_X, FUNDO_Y, FUNDO_W, FUNDO_H = -1024, -2048, 45, 44
FUNDO_PICO_COL, FUNDO_PICO_LIN, FUNDO_INCLINA, FUNDO_PASSO = 22, 6, 0.85, 3   # montanha grande: pico e inclinação
FUNDO_SOPE = 34                             # linha da serra baixa, na frente, por toda a largura
FUNDO_PARALLAX = 0.15


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t72/' + nome))


def var(nome, valor):
    tipo = 'boolean' if isinstance(valor, bool) else 'string' if isinstance(valor, str) else 'number'
    return {'name': nome, 'persistentUuid': uid('var/' + nome), 'type': tipo, 'value': valor}


def px(col, h):
    """Canto de cima à esquerda do tile (col, h)."""
    return X0 + col * T, Y0 + (H - 1 - h) * T


def solidos():
    s = set()
    for c in range(W):                                       # chão do pé da montanha
        for h in range(4):
            s.add((c, h))
    for h0, h1, borda in PAREDAO_ESQ:
        for h in range(h0, h1 + 1):
            s.update((c, h) for c in range(borda + 1))
    for h in RESSALTOS_ESQ:
        s.update((c, h) for c in range(17, 20))
    for h0, h1, borda in PAREDAO_DIR:
        for h in range(h0, h1 + 1):
            s.update((c, h) for c in range(borda, W))
    c0, c1, h0, h1 = PILAR
    s.update((c, h) for c in range(c0, c1 + 1) for h in range(h0, h1 + 1))
    for h in RESSALTOS_PILAR:
        s.update((c, h) for c in range(22, 25))
    for c0, c1, h0, h1 in ILHAS:
        s.update((c, h) for c in range(c0, c1 + 1) for h in range(h0, h1 + 1))
    return s


def autotile(s):
    """Escolhe o tile de cada célula sólida pelos vizinhos, como no atlas do Inferno (mesma grade 17 x 9)."""
    grade = [[-1] * W for _ in range(H)]
    for (c, h) in s:
        cheio = lambda dc, dh: (c + dc, h + dh) in s or not (0 <= c + dc < W) or h + dh < 0
        cima, baixo, esq, dir_ = (not cheio(0, 1)), (not cheio(0, -1)), (not cheio(-1, 0)), (not cheio(1, 0))
        var2 = (c * 7 + h * 3) % 5 == 0                       # variação fixa, sem sorteio
        if cima and baixo:
            t = 26 if esq else 28 if dir_ else 4
        elif cima:
            t = 0 if esq else 2 if dir_ else (52 if var2 else 1)
        elif baixo:
            t = 34 if esq else 36 if dir_ else (86 if var2 else 35)
        elif esq:
            t = 68 if var2 else 17
        elif dir_:
            t = 70 if var2 else 19
        elif not cheio(1, 1):
            t = 40
        elif not cheio(-1, 1):
            t = 42
        elif not cheio(1, -1):
            t = 6
        elif not cheio(-1, -1):
            t = 8
        else:
            t = 144
        grade[H - 1 - h][c] = t
    return grade


def mapa_troncos():
    grade = [[-1] * W for _ in range(H)]
    for c0, c1, h in TRONCOS:
        for c in range(c0, c1 + 1):
            grade[H - 1 - h][c] = 142 if c0 == c1 else 125 if c == c0 else 127 if c == c1 else 126
    return grade


def mapa_enfeites(s):
    grade = [[-1] * W for _ in range(H)]
    for col, h, desenho in ENFEITES:
        for dh, linha in enumerate(desenho):
            for dc, t in enumerate(linha):
                assert (col + dc, h + dh) not in s, ('enfeite dentro do terreno', col, h)
                grade[H - 1 - (h + dh)][col + dc] = t
    # cipós pendurados embaixo das ilhas, dos terraços e do pilar
    for (c, h) in s:
        if h > 4 and (c, h - 1) not in s and (c - 1, h) in s and (c + 1, h) in s and c % CIPO_FREQ == 0 \
                and grade[H - h][c] == -1 and 13 <= c <= 48:
            grade[H - h][c] = 148 if (c // CIPO_FREQ) % 2 else 131
    return grade


def mapa_fundo():
    """Serra ao longe: blocos de cumeeira de 5 tiles; o mais alto de cada coluna fica por cima."""
    g = [[-1] * FUNDO_W for _ in range(FUNDO_H)]

    def cumeeira(c0, topo):
        for k in range(5):
            c = c0 + k
            if not 0 <= c < FUNDO_W:
                continue
            for r in range(topo, FUNDO_H):
                if g[r][c] != -1:
                    break
                g[r][c] = 102 + k if r == topo else (119, 143, 121, 143, 123)[k] if r == topo + 1 else 143
    blocos = []
    for c0 in range(-4, FUNDO_W, FUNDO_PASSO):           # blocos sobrepostos: as pontas inclinadas fazem a encosta
        topo = round(FUNDO_PICO_LIN + abs(c0 + 2 - FUNDO_PICO_COL) * FUNDO_INCLINA)
        if topo < FUNDO_SOPE - 1:
            blocos.append((c0, topo))
    blocos += [(i * 5 - 2, FUNDO_SOPE) for i in range(FUNDO_W // 5 + 1)]
    for c0, topo in sorted(blocos, key=lambda b: b[1]):
        cumeeira(c0, topo)
    for r in range(FUNDO_H):                                 # o que ficou por baixo de um topo vira paredão
        for c in range(FUNDO_W):
            if g[r][c] == -1 and r > 0 and g[r - 1][c] != -1:
                g[r][c] = 143
    return g


def tilemap(grade):
    return json.dumps({'tileWidth': T, 'tileHeight': T, 'dimX': len(grade[0]), 'dimY': len(grade),
                       'layers': [{'id': 0, 'alpha': 1, 'tiles': grade}]}, separators=(',', ':'))


def inst_tilemap(nome, chave, x, y, z, grade, camada=''):
    return {'angle': 0, 'customSize': False, 'height': 0, 'keepRatio': True, 'layer': camada, 'name': nome,
            'persistentUuid': uid(chave), 'width': 0, 'x': x, 'y': y, 'zOrder': z, 'numberProperties': [],
            'stringProperties': [{'name': 'tilemap', 'value': tilemap(grade)}], 'initialVariables': []}


def evento(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::Standard',
         'conditions': [{'type': {'value': t}, 'parameters': p} for t, p in conds],
         'actions': [{'type': {'value': t}, 'parameters': p} for t, p in acoes]}
    if filhos:
        e['events'] = filhos
    return e


def grupo(nome, eventos):
    return {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': nome, 'source': '',
            'type': 'BuiltinCommonInstructions::Group', 'events': eventos, 'parameters': []}


def comentario(texto):
    return {'type': 'BuiltinCommonInstructions::Comment',
            'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0}, 'comment': texto}


def link(alvo):
    return {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': alvo}


def migra(d):
    if any(l['name'] == CENA for l in d['layouts']):
        return False
    molde = next(l for l in d['layouts'] if l['name'] == MOLDE)
    hub = next(l for l in d['layouts'] if l['name'] == 'Hub')
    s = solidos()

    # HUD, pato e companhia: as mesmas instâncias do Inferno (as que o Hub também tem), com uuid novo
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
    pato['x'], pato['y'] = px(14, 4)[0], px(0, 3)[1] - pato['height']
    alvo_i = next((i for i in instancias if i['name'] == 'alvo'), None)
    if alvo_i is not None and alvo_i.get('layer', '') == '':
        alvo_i['x'], alvo_i['y'] = pato['x'] + 300, pato['y']

    instancias.append(inst_tilemap('tiles_purgatorio_decor', 'fundo_serra', FUNDO_X, FUNDO_Y, 1, mapa_fundo(), 'Fundo'))
    instancias.append(inst_tilemap('tiles_purgatorio', 'terreno', X0, Y0, 4, autotile(s)))
    instancias.append(inst_tilemap('tiles_purgatorio_decor', 'enfeites', X0, Y0, 5, mapa_enfeites(s)))
    instancias.append(inst_tilemap('tiles_purgatorio_ponte', 'troncos', X0, Y0, 6, mapa_troncos()))

    moeda_molde = next((i for i in molde['instances'] if i['name'] == 'moeda'), None)
    mw, mh = (moeda_molde['width'], moeda_molde['height']) if moeda_molde else (103, 60)
    for k, (col, h) in enumerate(MOEDAS):
        cx, cy = X0 + col * T + T / 2, Y0 + (H - 1 - h) * T + T / 2
        instancias.append({'angle': 0, 'customSize': True, 'depth': 1, 'height': mh, 'keepRatio': True, 'layer': '',
                           'name': 'moeda', 'persistentUuid': uid(f'moeda/{k}'), 'width': mw,
                           'x': round(cx - mw / 2), 'y': round(cy - mh / 2), 'zOrder': 1004,
                           'numberProperties': [], 'stringProperties': [],
                           'initialVariables': [{'name': 'tem_gravidade', 'persistentUuid': uid(f'moeda/{k}/g'),
                                                 'type': 'boolean', 'value': False}]})

    variaveis = [copy.deepcopy(v) for v in molde['variables'] if v['name'] in ('laser_x', 'laser_y', 'exp_d', 'soco_rx', 'soco_ry')]
    cume_y = Y0 + (H - CUME_S) * T
    variaveis += [var('fundo_parallax_x', FUNDO_PARALLAX), var('fundo_parallax_y', FUNDO_PARALLAX),
                  var('fundo_dx', 0), var('fundo_dy', 0),
                  var('saida_x_min', X0 + 2 * T), var('saida_x_max', X0 + 14 * T), var('saida_y', cume_y + 8),
                  var('proxima_cena', 'Hub')]

    eventos = [
        comentario('Purgatório: subida vertical numa fenda da montanha, do pé até o cume, sem chefe. Quatro trechos '
                   'separados por terraços: encosta, troncos e chaminé (pulo duplo entre os ressaltos), ilhas até o '
                   'paredão da direita, e a escadaria final de troncos. No cume, a saída leva para proxima_cena.'),
        link('Jogador'), link('AplicarUpgrades'), link('Inimigos'), link('Combate'), link('HUD'),
        grupo('Fundo em parallax', [evento([], [
            ('SetCameraCenterX', ['', '=', 'CameraCenterX("", 0) * fundo_parallax_x + fundo_dx', '"Fundo"', '0']),
            ('SetCameraCenterY', ['', '=', 'CameraCenterY("", 0) * fundo_parallax_y + fundo_dy', '"Fundo"', '0'])])]),
        grupo('Saída no cume', [evento([
            ('BooleanObjectVariable', ['pato', 'morto', 'False', '']),
            ('BuiltinCommonInstructions::CompareNumbers', ['pato.CenterX()', '>=', 'saida_x_min']),
            ('BuiltinCommonInstructions::CompareNumbers', ['pato.CenterX()', '<=', 'saida_x_max']),
            ('BuiltinCommonInstructions::CompareNumbers', ['pato.Y() + pato.Height()', '<=', 'saida_y'])],
            [('Scene', ['', 'proxima_cena', ''])])]),
    ]

    cena = {'b': COR_FUNDO[2], 'disableInputWhenNotFocused': True, 'mangledName': CENA, 'name': CENA,
            'r': COR_FUNDO[0], 'standardSortMethod': True, 'stopSoundsOnStartup': True, 'title': '', 'v': COR_FUNDO[1],
            'uiSettings': copy.deepcopy(molde['uiSettings']), 'objectsGroups': [], 'variables': variaveis,
            'instances': instancias, 'objects': [], 'objectsFolderStructure': {'folderName': '__ROOT'},
            'events': eventos, 'layers': copy.deepcopy(molde['layers']),
            'behaviorsSharedData': copy.deepcopy(molde['behaviorsSharedData'])}
    pos = next(k for k, l in enumerate(d['layouts']) if l['name'] == MOLDE) + 1
    d['layouts'].insert(pos, cena)
    return True


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if not migra(d):
        print('cena', CENA, 'já existe; nada feito')
        return
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
