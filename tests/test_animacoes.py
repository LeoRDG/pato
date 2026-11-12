import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
PATO = [o for o in JOGO['objects'] if o['name'] == 'pato'][0]
RES = {r['name'] for r in JOGO['resources']['resources']}


def test_animacoes_do_pato():
    nomes = {a['name']: a['directions'][0] for a in PATO['animations']}
    assert set(nomes) == {'Parado', 'Andar', 'Pulo', 'Queda', 'Dano', 'Morte'}
    assert len(nomes['Parado']['sprites']) == 4 and len(nomes['Andar']['sprites']) == 4


def test_quadros_existem_e_tem_a_mesma_mascara():
    masks = set()
    for a in PATO['animations']:
        for s in a['directions'][0]['sprites']:
            assert s['image'] in RES and os.path.exists(os.path.join(RAIZ, 'assets', s['image']))
            masks.add(json.dumps(s['customCollisionMask']))
    assert len(masks) == 1


def test_eventos_trocam_a_animacao():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    for n in ('Parado', 'Andar', 'Pulo', 'Queda', 'Dano', 'Morte'):
        assert 'AnimatableCapability::AnimatableBehavior::SetName' in txt and f'\\"{n}\\"' in txt
