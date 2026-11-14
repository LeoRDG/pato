"""Tarefa 50: tiles do purgatório (montanha / floresta musgosa) entram no projeto como objetos prontos para pintar.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - recurso de imagem assets/purgatorio/tiles/tiles_purgatorio_2x.png;
  - tiles_purgatorio (terreno sólido), tiles_purgatorio_ponte (troncos caídos, atravessáveis por baixo) e
    tiles_purgatorio_decor (sem colisão), na pasta cenario/plataformas, com a mesma grade 17 x 9 de 64 px
    dos tiles do inferno e do céu;
  - tiles_purgatorio entra no grupo Terreno.

A imagem vem de tools/t49_purgatorio_tiles_sprites.py (já gerada; este script não desenha).
"""
import json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'tiles_purgatorio'
ATLAS = f'assets/purgatorio/tiles/{BASE}_2x.png'
TILE, COLS, LINS = 64, 17, 9
PONTE = [108, 109, 110, 125, 126, 127, 142]


def uid(nome):
    """UUID estável (o mesmo a cada execução) para o que este script cria."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t50/' + nome))


def solidos():
    """Blocos de terreno: colunas 0-12, linhas 0-5 (menos os tiles vazios) + o miolo liso (144)."""
    alfa = Image.open(os.path.join(RAIZ, f'assets/purgatorio/tiles/{BASE}.png')).convert('RGBA').split()[3]
    ids = [l * COLS + c for l in range(6) for c in range(13)
           if alfa.crop((c * 32, l * 32, c * 32 + 32, l * 32 + 32)).getbbox()]
    return sorted(ids + [144])


def migra(d):
    objs = {o['name'] for o in d['objects']}
    recursos = d['resources']['resources']
    if not any(r['name'] == ATLAS for r in recursos):
        recursos.append({'file': ATLAS, 'kind': 'image', 'metadata': '', 'name': ATLAS, 'smoothed': False, 'userAdded': True})
    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'plataformas'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox
    for nome, hit, tipo in ((BASE, ','.join(map(str, solidos())), 'NormalPlatform'),
                            (BASE + '_ponte', ','.join(map(str, PONTE)), 'Jumpthru'),
                            (BASE + '_decor', '', None)):
        if nome in objs:
            continue
        d['objects'].append({
            'assetStoreId': '', 'name': nome, 'persistentUuid': uid(nome), 'type': 'TileMap::SimpleTileMap',
            'variables': [], 'effects': [],
            'behaviors': [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False,
                           'platformType': tipo, 'yGrabOffset': 0}] if tipo else [],
            'content': {'opacity': 255, 'atlasImage': ATLAS, 'rowCount': LINS, 'columnCount': COLS, 'tileSize': TILE,
                        'tilesWithHitBox': hit}})
        if not any(c.get('objectName') == nome for c in pasta.setdefault('children', [])):
            pasta['children'].append({'objectName': nome})
    terreno = next((g for g in d['objectsGroups'] if g['name'] == 'Terreno'), None)
    if terreno is not None and not any(x['name'] == BASE for x in terreno['objects']):
        terreno['objects'].append({'name': BASE})


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
