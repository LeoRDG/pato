import json, os
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
CENA = next(l for l in JOGO['layouts'] if l['name'] == 'Inferno')


def test_fundo_em_parallax_no_inferno():
    assert CENA['layers'][0]['name'] == 'Fundo' and not CENA['layers'][0]['followBaseLayerCamera']
    fundo = [i for i in CENA['instances'] if i['layer'] == 'Fundo']
    assert [i['name'] for i in sorted(fundo, key=lambda i: i['zOrder'])] == ['bg_inferno_ceu', 'bg_inferno_fundo', 'bg_inferno_meio', 'bg_inferno_frente']
    assert not any(i['name'] == 'bg' for i in CENA['instances'])
    for n in ('ceu', 'fundo', 'meio', 'frente'):
        assert Image.open(os.path.join(RAIZ, OBJ[f'bg_inferno_{n}']['texture'])).size == (3072, 1080)
    ev = json.dumps(CENA['events'])
    assert ev.count('TiledSpriteObject::XOffset') == 4 and 'CameraCenterX() * 0.03' in ev and 'CameraCenterX() * 0.4' in ev


def test_pato_sem_brilho():
    assert not any(e.get('effectType') == 'AdvancedBloom' for e in OBJ['pato']['effects'])
