"""Tarefa 106: cena Teste, para ver o comportamento de cada inimigo, um por vez.

Uma fileira de salas de SALA_L x ALTURA tiles (chão, teto e paredes de tiles_inferno), cada parede com uma porta rente ao
chão. Cada sala tem um caso (um inimigo, ou um grupo pequeno quando o comportamento depende disso) no meio, longe
das portas: o inimigo da próxima sala fica fora da tela e atrás da parede até o pato entrar. Uma placa (rotulo_teste,
objeto de texto novo) em cada sala diz o que tem nela; o texto vem da variável de instância "texto" no começo da cena.
O pato, a HUD e as variáveis de cena são copiados do Inferno, e a cena liga os eventos Jogador, AplicarUpgrades,
Inimigos, Combate, HUD e Sangue (sem Lava, Plataformas, FundoEscuro e Chefe: o demônio chefe precisa da arena dele e
fica de fora). Tamanho de cada inimigo = o de uma instância dele já posta numa fase (senão o tamanho da imagem).
Para usar: abrir a cena Teste no GDevelop e rodar a pré-visualização dela. Só cria a cena se ela não existir.
Rodar uma vez:  python3 tools/t106_cena_teste.py
"""
import copy, json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENA, MOLDE, TILES = 'Teste', 'Inferno', 'tiles_inferno'
T = 64
SALA_L, PAREDE, ALTURA, TETO, CHAO_ESP, PORTA_ALT = 40, 2, 24, 3, 3, 5   # em tiles
H = TETO + ALTURA + CHAO_ESP
CHAO_R = TETO + ALTURA                    # primeira linha do chão
X0, Y0 = 0, -CHAO_R * T                   # o topo do chão fica em y = 0
VOO = 600                                  # voadores começam com o centro VOO px acima do chão
# (texto da placa, [(inimigo, deslocamento em tiles a partir do meio da sala, voa)])
CASOS = [
    ('Condenado em chamas', [('condenado_em_chamas', 0, False)]),
    ('Condenado azul (investida e soco)', [('condenado_azul', 4, False)]),
    ('Condenado inchado (estoura perto)', [('condenado_inchado', 0, False)]),
    ('Árvore condenada (leque)', [('arvore_condenada', 4, False)]),
    ('Pigman (salto e onda)', [('pigman', 2, False)]),
    ('Sapo (língua e cura: machuque os condenados)', [('sapo', 2, False), ('condenado_em_chamas', 8, False),
                                                       ('condenado_em_chamas', 11, False)]),
    ('Cutulu (pulo)', [('cutulu', 4, False)]),
    ('Voador (caveira de fogo)', [('voador', 0, True)]),
    ('Caveira azul (quica)', [('caveira_azul', 0, True)]),
    ('Moscas (enxame)', [('moscas', -2, True), ('moscas', 0, True), ('moscas', 2, True), ('moscas', 1, True),
                         ('moscas', -1, True)]),
    ('Olho demoníaco (raio)', [('olho_demoniaco', 4, True)]),
    ('Mina demoníaca (explode em cadeia)', [('mina_demoniaca', -3, True), ('mina_demoniaca', 0, True),
                                            ('mina_demoniaca', 3, True)]),
    ('Cabeça voadora (investida)', [('cabeca_voadora', 0, True)]),
    ('Diabinho (rouba moedas: pegue as moedas antes)', [('diabinho', 6, True)]),
    ('Caveira gigante (voa em oito e despenca)', [('caveira_gigante', 4, False)]),
    ('Querubim', [('querubim', 0, True)]),
    ('Serafim (anéis)', [('serafim', 0, True)]),
    ('Ofanim', [('ofanim', 0, True)]),
    ('Roda do anjo', [('roda_anjo', 0, True)]),
    ('Mercador (fica hostil se atacado)', [('trader', 4, False)]),
]
MOEDAS_DIABINHO = 8
LINKS = ('Jogador', 'AplicarUpgrades', 'Inimigos', 'Combate', 'HUD', 'Sangue')


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t106/' + nome))


def var(chave, nome, valor):
    tipo = 'boolean' if isinstance(valor, bool) else 'string' if isinstance(valor, str) else 'number'
    return {'name': nome, 'persistentUuid': uid(f'var/{chave}/{nome}'), 'type': tipo, 'value': valor}


def inst(nome, chave, x, y, z, camada='', w=None, h=None, variaveis=()):
    return {'angle': 0, 'customSize': w is not None, 'height': h or 0, 'keepRatio': True, 'layer': camada,
            'name': nome, 'persistentUuid': uid(chave), 'width': w or 0, 'x': round(x), 'y': round(y), 'zOrder': z,
            'numberProperties': [], 'stringProperties': [], 'initialVariables': list(variaveis)}


def autotile(s, W):
    """Mesmo encaixe de bordas e quinas do t83 (o atlas do céu e o do inferno têm o mesmo desenho)."""
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


def mapa(n_salas):
    W = PAREDE + n_salas * (SALA_L + PAREDE)
    s = set()
    for c in range(W):
        s.update((c, r) for r in range(TETO))                     # teto
        s.update((c, r) for r in range(CHAO_R, H))                # chão
    for k in range(n_salas + 1):                                  # paredes; as do meio com porta rente ao chão
        c0 = k * (SALA_L + PAREDE)
        for c in range(c0, c0 + PAREDE):
            for r in range(TETO, CHAO_R):
                porta = 0 < k < n_salas and r >= CHAO_R - PORTA_ALT
                if not porta:
                    s.add((c, r))
    return autotile(s, W)


def tamanho(d, nome, R, O):
    for l in d['layouts']:
        for i in l['instances']:
            if i['name'] == nome and i.get('customSize'):
                return i['width'], i['height'], True
    s = O[nome]['animations'][0]['directions'][0]['sprites'][0]
    w, h = Image.open(os.path.join(RAIZ, R[s['image']])).size
    return w, h, False


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(l['name'] == CENA for l in d['layouts']):
        sys.exit('t106 já foi aplicada (cena Teste existe); não roda de novo.')
    molde = next(l for l in d['layouts'] if l['name'] == MOLDE)
    hub = next(l for l in d['layouts'] if l['name'] == 'Hub')
    O = {o['name']: o for o in d['objects']}
    R = {r['name']: r['file'] for r in d['resources']['resources']}

    # objeto novo: placa de texto
    if 'rotulo_teste' not in O:
        placa = copy.deepcopy(O['portal_nome'])
        placa['name'], placa['persistentUuid'] = 'rotulo_teste', uid('obj/rotulo_teste')
        placa['characterSize'] = placa['content']['characterSize'] = 40
        placa['textAlignment'] = placa['content']['textAlignment'] = 'center'
        placa['variables'] = [var('rotulo_teste', 'texto', '')]
        d['objects'].append(placa)
        d['objectsFolderStructure']['children'].append({'objectName': 'rotulo_teste'})

    # pato, HUD e o que mais o Hub e o Inferno têm em comum (sem tiles e fundos)
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
    pato['x'], pato['y'] = X0 + (PAREDE + 4) * T, -pato['height']
    for i in instancias:
        if i['name'] == 'alvo' and i.get('layer', '') == '':
            i['x'], i['y'] = pato['x'] + 300, pato['y']

    salas = [('TESTE: um inimigo por sala. Vá para a direita.', [])] + CASOS
    instancias.append(dict(inst(TILES, 'terreno', X0, Y0, 4), stringProperties=[{'name': 'tilemap', 'value': json.dumps(
        {'tileWidth': T, 'tileHeight': T, 'dimX': PAREDE + len(salas) * (SALA_L + PAREDE), 'dimY': H,
         'layers': [{'id': 0, 'alpha': 1, 'tiles': mapa(len(salas))}]}, separators=(',', ':'))}]))
    for k, (rotulo, inimigos) in enumerate(salas):
        x_sala = X0 + (PAREDE + k * (SALA_L + PAREDE)) * T
        meio = x_sala + SALA_L * T / 2
        instancias.append(inst('rotulo_teste', f'placa/{k}', x_sala + 4 * T, -ALTURA * T + 2 * T, 3000,
                               variaveis=[var(f'placa{k}', 'texto', f'{k}. {rotulo}' if k else rotulo)]))
        for j, (nome, dc, voa) in enumerate(inimigos):
            w, h, custom = tamanho(d, nome, R, O)
            cx = meio + dc * T
            y = -VOO - h / 2 if voa else -h
            instancias.append(inst(nome, f'inimigo/{k}/{j}', cx - w / 2, y, 2800, '', w if custom else None,
                                   h if custom else None))
            if nome == 'diabinho':
                mw, mh, mc = tamanho(d, 'moeda', R, O)
                for m in range(MOEDAS_DIABINHO):
                    instancias.append(inst('moeda', f'moeda/{k}/{m}', x_sala + (4 + 2 * m) * T, -mh - T, 1004, '',
                                           mw if mc else None, mh if mc else None))

    variaveis = []
    for v in molde['variables']:
        n = copy.deepcopy(v)
        n['persistentUuid'] = uid('var/cena/' + v['name'])
        variaveis.append(n)
    eventos = [{'type': 'BuiltinCommonInstructions::Comment',
                'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
                'comment': 'Cena de teste dos inimigos (tools/t106_cena_teste.py): um caso por sala, da esquerda para '
                           'a direita. A placa de cada sala mostra a variável "texto" da instância.'}]
    links = {e['target']: e for e in molde['events'] if e['type'].endswith('Link')}
    eventos += [copy.deepcopy(links[alvo]) for alvo in LINKS]
    eventos.append({'type': 'BuiltinCommonInstructions::ForEach', 'object': 'rotulo_teste',
                    'conditions': [{'type': {'value': 'DepartScene'}, 'parameters': ['']}],
                    'actions': [{'type': {'value': 'TextContainerCapability::TextContainerBehavior::SetValue'},
                                 'parameters': ['rotulo_teste', 'Text', '=', 'rotulo_teste.texto']}]})
    cena = {'b': 12, 'disableInputWhenNotFocused': True, 'mangledName': CENA, 'name': CENA, 'r': 40,
            'standardSortMethod': True, 'stopSoundsOnStartup': True, 'title': '', 'v': 10,
            'uiSettings': copy.deepcopy(molde['uiSettings']), 'objectsGroups': [], 'variables': variaveis,
            'instances': instancias, 'objects': [], 'objectsFolderStructure': {'folderName': '__ROOT'},
            'events': eventos, 'layers': copy.deepcopy(molde['layers']),
            'behaviorsSharedData': copy.deepcopy(molde['behaviorsSharedData'])}
    for camada in cena['layers']:
        camada['visibility'] = True
    d['layouts'].append(cena)

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cena Teste criada:', len(salas), 'salas,', len(instancias), 'instâncias')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
