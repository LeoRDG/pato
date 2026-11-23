"""Tarefa 121: profundidade no fundo do Purgatório, atrás do decor (parede hachurada) que já está na camada Fundo.

A camada Fundo anda com a câmera a fundo_parallax_x/y (0.15) e tem o tilemap tiles_purgatorio_decor (zOrder 1), que
só cobre a parte de baixo da subida; atrás dele era só a cor lisa da cena. Entram três TiledSprite na camada Fundo,
todos atrás do decor, no estilo do próprio tileset (a hachura da parede de fundo, picos serrilhados, musgo e raízes)
e na cor de névoa que já era a da cena (128;138;128):
- bg_purgatorio_longe (zOrder -3, assets/purgatorio/fundo/longe.png): névoa com agulhas de rocha bem distantes e
  fachos de luz diagonais. Opaco.
- bg_purgatorio_pilares (zOrder -2, assets/purgatorio/fundo/pilares.png): pilares de rocha mais perto, com musgo,
  cipós e raízes, que somem na névoa embaixo.
- bg_purgatorio_nevoa (zOrder -1, assets/purgatorio/fundo/nevoa.png): faixas de névoa que correm a vel px/s (14).
Mais longe anda mais devagar: X/YOffset = CameraCenter * parallax_extra, com parallax_extra negativo (longe -0.10
-> anda a 0.05; pilares -0.05 -> 0.10; o decor a 0.15). As texturas são contínuas nos dois sentidos.
Só adiciona o que não existe (recurso, objeto, instância, ação); valores existentes ficam.
Rodar uma vez:  python3 tools/t121_fundo_purgatorio.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = 'assets/purgatorio/fundo/'
# (objeto, textura, zOrder, variáveis)
FUNDOS = [
    ('bg_purgatorio_longe', PASTA + 'longe.png', -3, [('parallax_extra', -0.1)]),
    ('bg_purgatorio_pilares', PASTA + 'pilares.png', -2, [('parallax_extra', -0.05)]),
    ('bg_purgatorio_nevoa', PASTA + 'nevoa.png', -1, [('vel', 14)]),
]
# cobre tudo o que a camada Fundo mostra do pé ao cume (câmera da camada vai de ~(-530, -2680) a ~(440, -100))
INST = dict(x=-2048, y=-3600, w=4096, h=4400)
TEX = 1024


def uid():
    return str(uuid.uuid4())


def acao(tipo, obj, expr):
    return {'type': {'value': tipo}, 'parameters': [obj, '=', expr]}


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    cena = next(l for l in d['layouts'] if l['name'] == 'Purgatorio')
    grupo = next(e for e in cena['events'] if e.get('name') == 'Fundo em parallax')
    acoes = grupo['events'][0]['actions']
    if any(a['parameters'] and a['parameters'][0].startswith('bg_purgatorio_') for a in acoes):
        sys.exit('t121 já foi aplicada; não roda de novo.')

    recursos = d['resources']['resources']
    nomes_obj = {o['name'] for o in d['objects']}
    pasta = next((c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'cenario'), None)
    for nome, tex, z, variaveis in FUNDOS:
        if not any(r['name'] == tex for r in recursos):
            recursos.append({'file': tex, 'kind': 'image', 'metadata': '', 'name': tex, 'smoothed': False,
                             'userAdded': True})
        if nome not in nomes_obj:
            d['objects'].append({'assetStoreId': '', 'height': TEX, 'name': nome, 'persistentUuid': uid(),
                                 'texture': tex, 'type': 'TiledSpriteObject::TiledSprite', 'width': TEX,
                                 'variables': [{'name': n, 'persistentUuid': uid(), 'type': 'number', 'value': v}
                                               for n, v in variaveis],
                                 'effects': [], 'behaviors': []})
            if pasta is not None:
                pasta['children'].append({'objectName': nome})
        if not any(i['name'] == nome for i in cena['instances']):
            cena['instances'].append({'angle': 0, 'customSize': True, 'height': INST['h'], 'keepRatio': True,
                                      'layer': 'Fundo', 'name': nome, 'persistentUuid': uid(), 'width': INST['w'],
                                      'x': INST['x'], 'y': INST['y'], 'zOrder': z, 'numberProperties': [],
                                      'stringProperties': [], 'initialVariables': []})
    for nome in ('bg_purgatorio_longe', 'bg_purgatorio_pilares'):
        acoes.append(acao('TiledSpriteObject::XOffset', nome, f'CameraCenterX("", 0) * {nome}.parallax_extra'))
        acoes.append(acao('TiledSpriteObject::YOffset', nome, f'CameraCenterY("", 0) * {nome}.parallax_extra'))
    acoes.append(acao('TiledSpriteObject::XOffset', 'bg_purgatorio_nevoa', 'TimeFromStart() * bg_purgatorio_nevoa.vel'))

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('fundo do Purgatório:', [f[0] for f in FUNDOS])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
