import json, os
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
RES = {r['name']: r for r in JOGO['resources']['resources']}
BASES = ('tiles_inferno', 'tiles_inferno_escuro')


def ids(nome):
    return [int(x) for x in OBJ[nome]['content']['tilesWithHitBox'].split(',') if x]


def tipo(nome):
    return [b['platformType'] for b in OBJ[nome]['behaviors'] if b['type'] == 'PlatformBehavior::PlatformBehavior']


def test_atlas_ampliado_bate_com_a_grade():
    for b in BASES:
        for s in ('', '_ponte', '_decor'):
            c = OBJ[b + s]['content']
            w, h = Image.open(os.path.join(RAIZ, c['atlasImage'])).size
            assert (w, h) == (c['columnCount'] * c['tileSize'], c['rowCount'] * c['tileSize']) and c['tileSize'] == 64
            assert RES[c['atlasImage']]['smoothed'] is False


def test_terreno_solido_ponte_atravessavel_decor_sem_colisao():
    for b in BASES:
        assert tipo(b) == ['NormalPlatform'] and tipo(b + '_ponte') == ['Jumpthru'] and tipo(b + '_decor') == []
        s = ids(b)
        assert {0, 1, 2, 40, 52, 144} <= set(s) and not {9, 18, 43} & set(s)      # blocos sim, buracos vazios não
        assert not set(s) & set(range(102, 144)) and not {13, 47, 64, 82} & set(s)  # parede de fundo, lápides e colunas não
        assert ids(b + '_ponte') == [108, 109, 110, 125, 126, 127, 142] and ids(b + '_decor') == []
        assert all(i < 17 * 9 for i in s)


def test_eventos_usam_o_grupo_terreno():
    g = {x['name']: [o['name'] for o in x['objects']] for x in JOGO['objectsGroups']}
    assert g['Terreno'] == ['chao', 'tiles_inferno', 'tiles_inferno_escuro']
    ev = json.dumps([x['events'] for x in JOGO['layouts'] + JOGO['externalEvents']])
    assert '"chao"' not in ev and ev.count('"Terreno"') == 7
