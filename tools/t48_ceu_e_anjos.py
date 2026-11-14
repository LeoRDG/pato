"""Tarefa 48: tiles do céu e anjos entram no projeto como objetos prontos (sem IA ainda).

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - recursos de imagem: assets/ceu/tiles/tiles_ceu_2x.png e os quadros de assets/anjos/*;
  - tiles_ceu (terreno sólido), tiles_ceu_ponte (plataformas finas, atravessáveis por baixo) e tiles_ceu_decor
    (sem colisão), na pasta cenario/plataformas, com a mesma grade 17 x 9 de 64 px dos tiles do inferno;
  - tiles_ceu entra no grupo Terreno (tiros, laser, granada e moedas tratam como chão);
  - querubim, serafim, ofanim e roda_anjo: sprites com as animações, na pasta inimigos/anjos_sem_ia. Levam as
    variáveis de inimigo voador (cópia de cabeca_voadora) mas ficam fora dos grupos de inimigos: não têm IA.
    querubim.ferido_abaixo = fração da vida abaixo da qual a animação certa é voando_ferido.

As imagens vêm de tools/t47_ceu_tiles_sprites.py e tools/t27_anjos_sprites.py (já geradas; este script não desenha).
"""
import copy, glob, json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = 'assets/ceu/tiles/tiles_ceu_2x.png'
TILE, COLS, LINS = 64, 17, 9
PONTE = [108, 109, 110, 125, 126, 127, 142]
MOLDE = 'cabeca_voadora'
# objeto -> [(animação, laço, tempo entre quadros)]
ANJOS = {
    'querubim': [('voando', True, 0.1), ('voando_ferido', True, 0.1), ('morte', False, 0.08)],
    'serafim': [('voando', True, 0.08), ('ataque_1', False, 0.08), ('morte', False, 0.08)],
    'ofanim': [('idle', True, 0.1), ('ataque', False, 0.09), ('morte', False, 0.08)],
    'roda_anjo': [('rolando', True, 0.07), ('morte', False, 0.08)],
}
VARS_NOVAS = {'querubim': {'ferido_abaixo': 0.5}}


def uid(*partes):
    """UUID estável (o mesmo a cada execução) para o que este script cria."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t48/' + '/'.join(partes)))


def solidos():
    """Blocos de terreno: colunas 0-12, linhas 0-5 (menos os tiles vazios) + o miolo liso (144)."""
    alfa = Image.open(os.path.join(RAIZ, 'assets/ceu/tiles/tiles_ceu.png')).convert('RGBA').split()[3]
    ids = [l * COLS + c for l in range(6) for c in range(13)
           if alfa.crop((c * 32, l * 32, c * 32 + 32, l * 32 + 32)).getbbox()]
    return sorted(ids + [144])


def pasta(d, *caminho):
    no = d['objectsFolderStructure']
    for nome in caminho:
        prox = next((c for c in no.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            no['children'].append(prox)
        no = prox
    return no


def na_pasta(no, nome):
    if not any(c.get('objectName') == nome for c in no.setdefault('children', [])):
        no['children'].append({'objectName': nome})


def quadros(obj, anim):
    return sorted(os.path.relpath(f, RAIZ) for f in glob.glob(os.path.join(RAIZ, 'assets', 'anjos', obj, anim + '_[0-9][0-9].png')))


def mascara(arquivos):
    """Retângulo de colisão: a caixa do desenho do primeiro quadro, encolhida 18% de cada lado."""
    im = Image.open(os.path.join(RAIZ, arquivos[0])).convert('RGBA')
    x0, y0, x1, y1 = im.split()[3].point(lambda a: 255 if a > 40 else 0).getbbox()
    mx, my = round((x1 - x0) * .18), round((y1 - y0) * .18)
    x0, y0, x1, y1 = x0 + mx, y0 + my, x1 - mx, y1 - my
    return [[{'x': x0, 'y': y0}, {'x': x1, 'y': y0}, {'x': x1, 'y': y1}, {'x': x0, 'y': y1}]]


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    tem = {r['name'] for r in recursos}

    def recurso(rel):
        if rel not in tem:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})
            tem.add(rel)

    # ---- tiles do céu
    recurso(ATLAS)
    plataformas = pasta(d, 'cenario', 'plataformas')
    for nome, hit, tipo in (('tiles_ceu', ','.join(map(str, solidos())), 'NormalPlatform'),
                            ('tiles_ceu_ponte', ','.join(map(str, PONTE)), 'Jumpthru'),
                            ('tiles_ceu_decor', '', None)):
        if nome in objs:
            continue
        o = {'assetStoreId': '', 'name': nome, 'persistentUuid': uid(nome), 'type': 'TileMap::SimpleTileMap',
             'variables': [], 'effects': [],
             'behaviors': [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False,
                            'platformType': tipo, 'yGrabOffset': 0}] if tipo else [],
             'content': {'opacity': 255, 'atlasImage': ATLAS, 'rowCount': LINS, 'columnCount': COLS, 'tileSize': TILE,
                         'tilesWithHitBox': hit}}
        d['objects'].append(o)
        objs[nome] = o
        na_pasta(plataformas, nome)
    terreno = next((g for g in d['objectsGroups'] if g['name'] == 'Terreno'), None)
    if terreno is not None and not any(x['name'] == 'tiles_ceu' for x in terreno['objects']):
        terreno['objects'].append({'name': 'tiles_ceu'})

    # ---- anjos
    anjos = pasta(d, 'inimigos', 'anjos_sem_ia')
    for nome, anims in ANJOS.items():
        for anim, _, _ in anims:
            for f in quadros(nome, anim):
                recurso(f)
        if nome in objs:
            continue
        o = copy.deepcopy(objs[MOLDE])
        o['name'], o['persistentUuid'] = nome, uid(nome)
        for v in o['variables']:
            v['persistentUuid'] = uid(nome, v['name'])
        for k, valor in VARS_NOVAS.get(nome, {}).items():
            o['variables'].append({'name': k, 'persistentUuid': uid(nome, k), 'type': 'number', 'value': valor})
        molde_sprite = o['animations'][0]['directions'][0]['sprites'][0]
        o['animations'] = []
        for anim, laco, tempo in anims:
            arqs = quadros(nome, anim)
            assert arqs, f'sem quadros para {nome}/{anim}'
            masc = mascara(quadros(nome, anims[0][0]))
            sprites = []
            for f in arqs:
                s = copy.deepcopy(molde_sprite)
                s['image'], s['hasCustomCollisionMask'], s['customCollisionMask'] = f, True, masc
                sprites.append(s)
            o['animations'].append({'name': anim, 'useMultipleDirections': False,
                                    'directions': [{'looping': laco, 'timeBetweenFrames': tempo, 'sprites': sprites}]})
        d['objects'].append(o)
        objs[nome] = o
        na_pasta(anjos, nome)


def main(caminho):
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
