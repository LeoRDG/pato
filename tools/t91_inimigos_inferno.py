"""Tarefa 91: inimigos no Inferno, só os da pasta inimigos/inferno; saem os anjos (querubim, serafim, roda_anjo, ofanim).

29 inimigos ao longo do caminho, ficando mais difíceis até o chefe:
  1. chão do começo e lava pequena: condenados em chamas, diabinhos, um voador, inchado no fosso, azul antes do poço;
  2. poço de lava com a plataforma: só voadores (cabeça voadora, voador, olho demoníaco);
  3. faixa de cima (y ~ -2,7k), voltando para a esquerda: azul, inchado, em chamas, caveira azul, olho, diabinho;
  4. subida por dentro: cabeça voadora e caveira azul;
  5. faixa com sangue e plataformas que sobem: azul, em chamas, inchado, diabinho, voador;
  6. faixa do topo até a arena: inchado, caveira gigante, azul, caveira azul, olho demoníaco.
Os de chão (condenado_em_chamas, condenado_azul, condenado_inchado, caveira_gigante) ficam de pé no Terreno; os voadores
no ar, longe das paredes. Tamanhos: os que o usuário já tinha posto no Inferno (diabinho 192x186, caveira_azul 153x153,
condenado_em_chamas 136x148, cabeca_voadora 157x184); os outros de 64 px em 160x160 e a caveira gigante em 320x320.
Não roda se já houver inimigo da pasta inferno na cena. Rodar uma vez:  python3 tools/t91_inimigos_inferno.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANJOS = {'querubim', 'serafim', 'roda_anjo', 'ofanim'}
TAM = {'diabinho': (192, 186), 'caveira_azul': (153, 153), 'condenado_em_chamas': (136, 148),
       'cabeca_voadora': (157, 184), 'voador': (160, 160), 'condenado_azul': (160, 160),
       'condenado_inchado': (160, 160), 'olho_demoniaco': (160, 160), 'caveira_gigante': (320, 320)}
CHAO = {'condenado_em_chamas', 'condenado_azul', 'condenado_inchado', 'caveira_gigante'}
# (nome, x do centro, y): de chão, y é o topo do chão onde pisa; voador, y é o centro
LISTA=[
 # 1: chão do começo e lava pequena (y ~ 0,8k)
 ('condenado_em_chamas', 1800, 791),
 ('diabinho', 1750, 150),
 ('condenado_em_chamas', 3150, 279),
 ('voador', 3400, -150),
 ('condenado_inchado', 5800, 1687),
 ('diabinho', 4500, 200),
 ('condenado_em_chamas', 6900, 279),
 ('condenado_azul', 7700, 279),
 # 2: poço de lava com a plataforma (x 8k..14k)
 ('cabeca_voadora', 9600, -350),
 ('voador', 10800, -450),
 ('olho_demoniaco', 12600, -600),
 # 3: faixa de cima (y ~ -2,7k), da direita para a esquerda
 ('diabinho', 6600, -3150),
 ('condenado_azul', 5600, -2793),
 ('caveira_azul', 4800, -3350),
 ('condenado_inchado', 3600, -2729),
 ('olho_demoniaco', 2600, -3200),
 ('condenado_em_chamas', 950, -2601),
 # 4: subida por dentro (y -3,6k .. -6k)
 ('cabeca_voadora', 1750, -4500),
 ('caveira_azul', 900, -4700),
 # 5: faixa com sangue (y ~ -6,1k) e plataformas que sobem
 ('condenado_azul', 1050, -6121),
 ('condenado_em_chamas', 3300, -6249),
 ('condenado_inchado', 5100, -6249),
 ('diabinho', 2400, -6900),
 ('voador', 4300, -8100),
 # 6: faixa do topo até a arena do chefe (y ~ -7,9k)
 ('condenado_inchado', 7100, -7913),
 ('caveira_gigante', 8700, -7913),
 ('caveira_azul', 9800, -8600),
 ('condenado_azul', 10700, -7913),
 ('olho_demoniaco', 11100, -8700),
]


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    pasta = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'inimigos')
    inferno = {c['objectName'] for c in next(c for c in pasta['children'] if c.get('folderName') == 'inferno')['children']}
    assert {n for n, _, _ in LISTA} <= inferno, {n for n, _, _ in LISTA} - inferno
    cena = next(l for l in d['layouts'] if l['name'] == 'Inferno')
    if any(i['name'] in inferno for i in cena['instances']):
        sys.exit('já há inimigos da pasta inferno no Inferno; t91 não roda de novo.')
    cena['instances'] = [i for i in cena['instances'] if i['name'] not in ANJOS]
    z = max(i.get('zOrder', 0) for i in cena['instances'])
    for k, (nome, x, y) in enumerate(LISTA):
        w, h = TAM[nome]
        topo = y - h if nome in CHAO else y - h / 2
        z += 1
        cena['instances'].append({
            'angle': 0, 'customSize': True, 'height': h, 'keepRatio': True, 'layer': '', 'name': nome,
            'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogos/t91/{k}/{nome}')),
            'width': w, 'x': round(x - w / 2), 'y': round(topo), 'zOrder': z,
            'numberProperties': [], 'stringProperties': [], 'initialVariables': []})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print(f'{len(LISTA)} inimigos do inferno postos; anjos removidos do Inferno')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
