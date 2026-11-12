import json, os

JOGO = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'), encoding='utf-8'))


def test_camera_segura_o_chao_mais_baixo():
    def walk(evs):
        for e in evs:
            yield e
            yield from walk(e.get('events') or [])
    jog = [x for x in JOGO['externalEvents'] if x['name'] == 'Jogador'][0]
    g = [e for e in walk(jog['events']) if e.get('name') == 'Câmera não perde o chão']
    assert len(g) == 1
    acts = [a for e in walk(g[0]['events']) for a in e.get('actions', [])]
    trava = [a for a in acts if a['type']['value'] == 'SetCameraCenterY'][0]['parameters'][2]
    assert 'pato.chao_baixo' in trava and 'pato.Y()' in trava and trava.startswith('min(')   # segura o chão, mas nunca perde o pato por cima
    pato = [o for o in JOGO['objects'] if o['name'] == 'pato'][0]
    assert any(v['name'] == 'chao_baixo' and v['value'] < -99999 for v in pato['variables'])
