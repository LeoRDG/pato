"""Tarefa 116: inimigos no Purgatório (estava sem nenhum).

O nível sobe da sala de baixo (portal do Hub) pela direita, pela escada de pontes e pelo poço da direita, passa pela
borda de cima, pela caverna grande da esquerda e chega ao cume (saída). Inimigos do Purgatório espalhados nesse
caminho, só os da pasta inimigos/purgatorio: 7 pigman (pancada), 4 sapos (cura e língua), 3 árvores condenadas
(espinheiro), 3 enxames de 5 moscas e 2 trios de minas demoníacas (perto umas das outras, explodem em cadeia) no ar
das áreas abertas, e o cutulu (chefe final, chefe_final = True) no cume, longe da saída. Ninguém perto dos portais.
(moscas2 está na pasta mas em nenhum grupo de inimigo, sem eventos: fica de fora.)
Tamanho (da instância, dá para mudar no editor): pigman, sapo, moscas e mina 2x o desenho (o pigman fica com ~140 px
visíveis, como os condenados), árvore 3x (~150 px), cutulu 3x (chefe). Os pés ficam no chão pela base da máscara de
colisão de cada um; a caixa da máscara de cada um é conferida contra os tiles para ninguém nascer dentro de parede.
Só acrescenta: se o Purgatório já tem algum desses inimigos, não roda.
Rodar uma vez:  python3 tools/t116_inimigos_do_purgatorio.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESCALA = {'pigman': 2, 'sapo': 2, 'cutulu': 3, 'arvore_condenada': 3, 'moscas': 2, 'mina_demoniaca': 2}
# (inimigo, centro x, y do chão) para os de chão; (inimigo, centro x, centro y) para os do ar
CHAO = [
    ('pigman', 2700, -512),     # sala de baixo, à direita
    ('arvore_condenada', 2250, -512),
    ('sapo', 1800, -832),       # degrau da sala de baixo
    ('pigman', 1150, -2432),    # subida da direita
    ('sapo', 1300, -4928),      # ponte de cima da escada
    ('pigman', 1450, -6784),    # poço da direita
    ('pigman', 300, -9408),     # borda de cima
    ('sapo', 1200, -9408),
    ('arvore_condenada', 750, -9408),
    ('pigman', -1800, -8768),   # chão da caverna da esquerda
    ('pigman', -900, -8768),
    ('arvore_condenada', -1350, -8768),
    ('sapo', -1600, -12160),    # subida da esquerda
    ('pigman', -1000, -12224),
    ('cutulu', 2000, -14656),   # cume: chefe final
]
ENXAME = [(0, 0), (-60, -40), (60, -30), (-40, 50), (50, 45)]   # 5 moscas juntas
TRIO = [(-130, 0), (0, -40), (130, 0)]                             # 3 minas perto: explodem em cadeia
AR = ([('moscas', 2600 + dx, -1400 + dy) for dx, dy in ENXAME]       # sala de baixo
      + [('mina_demoniaca', 2300 + dx, -3300 + dy) for dx, dy in TRIO]  # ao lado da escada
      + [('moscas', 2200 + dx, -6000 + dy) for dx, dy in ENXAME]     # poço da direita
      + [('mina_demoniaca', -1500 + dx, -10200 + dy) for dx, dy in TRIO]  # caverna da esquerda
      + [('moscas', -1200 + dx, -11600 + dy) for dx, dy in ENXAME])


def uid(n):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t116/' + n))


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cena = next(l for l in d['layouts'] if l['name'] == 'Purgatorio')
    nomes = set(ESCALA)
    if any(i['name'] in nomes for i in cena['instances']):
        sys.exit('t116 já foi aplicada (o Purgatório já tem inimigos); não roda de novo.')
    O = {o['name']: o for o in d['objects']}
    R = {r['name']: r['file'] for r in d['resources']['resources']}

    solido = set()
    for i in cena['instances']:
        sp = next((s for s in i.get('stringProperties', []) if s['name'] == 'tilemap'), None)
        if sp is None or i['layer'] != '':
            continue
        t = json.loads(sp['value'])
        ts = t['tileWidth']
        for r, row in enumerate(t['layers'][0]['tiles']):
            for c, v in enumerate(row):
                if v >= 0:
                    solido.add((round(i['x'] / ts) + c, round(i['y'] / ts) + r))

    def livre(x, y, w, h):
        return not any((cx, cy) in solido for cx in range(int(x // 64), int((x + w - 1) // 64) + 1)
                       for cy in range(int(y // 64), int((y + h - 1) // 64) + 1))

    def tamanho(nome):
        from PIL import Image
        s = O[nome]['animations'][0]['directions'][0]['sprites'][0]
        w, h = Image.open(os.path.join(RAIZ, R[s['image']])).size
        m = s['customCollisionMask'][0] if s.get('customCollisionMask') else [{'x': 0, 'y': 0}, {'x': w, 'y': h}]
        return w, h, (min(p['x'] for p in m), min(p['y'] for p in m), max(p['x'] for p in m), max(p['y'] for p in m))

    z = max(i.get('zOrder', 0) for i in cena['instances'] if i['layer'] == '') + 1
    novas = []
    for k, (nome, cx, chao) in enumerate(CHAO):
        w, h, (mx0, my0, mx1, my1) = tamanho(nome)
        e = ESCALA[nome]
        W, H = w * e, h * e
        x = cx - (mx0 + mx1) / 2 * e                # o meio da máscara no centro pedido
        y = chao - my1 * e - 2                      # a base da máscara logo acima do chão
        assert livre(x + mx0 * e, y + my0 * e, (mx1 - mx0) * e, (my1 - my0) * e), (nome, cx, chao)
        novas.append((nome, x, y, W, H, k))
    for k, (nome, cx, cy) in enumerate(AR):
        w, h, (mx0, my0, mx1, my1) = tamanho(nome)
        e = ESCALA[nome]
        x, y = cx - w * e / 2, cy - h * e / 2
        assert livre(x + mx0 * e, y + my0 * e, (mx1 - mx0) * e, (my1 - my0) * e), (nome, cx, cy)
        novas.append((nome, x, y, w * e, h * e, 100 + k))
    for nome, x, y, W, H, k in novas:
        ini = []
        if nome == 'cutulu':
            ini.append({'name': 'chefe_final', 'persistentUuid': uid('cutulu/chefe_final'), 'type': 'boolean', 'value': True})
        cena['instances'].append({
            'angle': 0, 'customSize': True, 'height': H, 'keepRatio': True, 'layer': '', 'name': nome,
            'persistentUuid': uid(f'{nome}/{k}'), 'width': W, 'x': round(x), 'y': round(y), 'zOrder': z,
            'numberProperties': [], 'stringProperties': [], 'initialVariables': ini})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print(len(novas), 'inimigos no Purgatório')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
