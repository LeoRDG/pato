"""Espinhos (tools/t76_espinhos.py): estão no Terreno mas não dá para pisar (não são plataforma)."""
import json, os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from folhas import folha, inimigos_todos
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}


def test_objeto_no_terreno_e_nao_pisavel():
    o = OBJ['espinhos']
    assert o['type'] == 'TiledSpriteObject::TiledSprite'
    assert not any(b['type'].startswith('PlatformBehavior') for b in o['behaviors'])
    assert {v['name'] for v in o['variables']} >= {'dano', 'empurrao'}
    terreno = next(g for g in JOGO['objectsGroups'] if g['name'] == 'Terreno')
    assert 'espinhos' in [x['name'] for x in terreno['objects']]


def test_encostar_machuca_e_empurra():
    ev = json.dumps(folha(JOGO, 'Espinhos'))
    for trecho in ('"CollisionNP"}, "parameters": ["pato", "espinhos"', 'espinhos.dano', 'espinhos.empurrao', '"invencivel", "False"'):
        assert trecho in ev
    cena = next(l for l in JOGO['layouts'] if l['name'] == 'Purgatorio')
    assert 'CenarioPurgatorio' in [e.get('target') for e in cena['events']]


def test_imagem_emenda_na_horizontal():
    a = np.array(Image.open(os.path.join(RAIZ, OBJ['espinhos']['texture'])).convert('RGBA'))[..., 3] > 0
    assert a.shape == (64, 64)
    vizinhas = [(a[:, x] == a[:, x + 1]).mean() for x in range(63)]
    assert (a[:, -1] == a[:, 0]).mean() >= min(vizinhas)                   # a emenda é como duas colunas vizinhas
    assert a.mean() > .25 and a[:6].any() and a[-6:].any()                 # cheio, com espinhos até as bordas
