import json, os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
RES = {r['name']: r for r in JOGO['resources']['resources']}
T = 32


def img(rel):
    return np.array(Image.open(os.path.join(RAIZ, rel)).convert('RGBA')).astype(int)


A = img('fontes/purgatorio/tiles/tiles_purgatorio.png')


def tile(i):
    return A[i // 17 * T:i // 17 * T + T, i % 17 * T:i % 17 * T + T]


def test_objetos_de_tiles_do_purgatorio():
    tipo = lambda n: [b['platformType'] for b in OBJ[n]['behaviors'] if b['type'] == 'PlatformBehavior::PlatformBehavior']
    ids = lambda n: [int(x) for x in OBJ[n]['content']['tilesWithHitBox'].split(',') if x]
    for s in ('', '_ponte', '_decor'):
        c = OBJ['tiles_purgatorio' + s]['content']
        w, h = Image.open(os.path.join(RAIZ, c['atlasImage'])).size
        assert (w, h) == (c['columnCount'] * c['tileSize'], c['rowCount'] * c['tileSize']) and c['tileSize'] == 64
        assert RES[c['atlasImage']]['smoothed'] is False
    assert tipo('tiles_purgatorio') == ['NormalPlatform'] and tipo('tiles_purgatorio_ponte') == ['Jumpthru']
    assert tipo('tiles_purgatorio_decor') == []
    s = set(ids('tiles_purgatorio'))
    assert {0, 1, 2, 40, 52, 144} <= s and not {9, 18, 43} & s and not s & set(range(102, 144))
    assert ids('tiles_purgatorio_ponte') == [108, 109, 110, 125, 126, 127, 142] and ids('tiles_purgatorio_decor') == []
    g = {x['name']: [o['name'] for o in x['objects']] for x in JOGO['objectsGroups']}
    assert 'tiles_purgatorio' in g['Terreno']


def test_nao_e_o_inferno_nem_o_ceu_recolorido():
    """Silhueta diferente dos outros dois atlas nos enfeites, na parede de fundo e nas bordas do terreno."""
    assert A.shape == (288, 544, 4)
    for outro in ('fontes/gandalf_hell/tiles/tiles_inferno.png', 'fontes/ceu/tiles/tiles_ceu.png'):
        dif = (A[..., 3] > 0) != (img(outro)[..., 3] > 0)
        assert dif[:, 13 * T:].mean() > 0.12 and dif[6 * T:, :6 * T].mean() > 0.07
    assert (tile(1)[0, :, 3] == 0).any() and (tile(1)[3, :, 3] > 0).all()       # capim irregular por cima
    assert (tile(35)[-1, :, 3] == 0).any() and (tile(35)[25, :, 3] > 0).all()   # pedra lascada por baixo


def test_cores_apagadas_e_esverdeadas():
    """Nada vibrante: saturação baixa em toda a folha; o tom dominante do que tem cor é verde/terra, não vermelho vivo."""
    p = A[A[..., 3] > 0][:, :3].astype(float)
    mx, mn = p.max(1), p.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    assert sat.max() < 0.5 and sat.mean() < 0.25
    musgo = (p[:, 1] > p[:, 0]) & (p[:, 1] > p[:, 2])
    assert musgo.mean() > 0.15


def test_terreno_emenda_sem_costura():
    for o in (0, 51):
        topo = tile(o + 1)
        for viz in (tile(o), tile(o + 2)):
            assert (topo[:12, 9:23] == viz[:12, 9:23]).all()                    # quinas continuam o mesmo topo
        assert (tile(o + 17)[:16, :9] == tile(o + 17)[16:, :9]).all(-1).mean() > .5   # parede em faixas que repetem
    assert (tile(144)[..., 3] == 255).all() and len({tuple(p) for p in tile(144).reshape(-1, 4)}) == 1
    for i in (108, 109, 110, 125, 126, 127, 142):                               # troncos: finos, colados no topo do tile
        a = tile(i)[..., 3] > 0
        assert a[:14].any() and not a[14:].any()
    assert (tile(109)[4:13, 0, 3] > 0).all() and (tile(109)[4:13, -1, 3] > 0).all()   # o meio do tronco vai de borda a borda
