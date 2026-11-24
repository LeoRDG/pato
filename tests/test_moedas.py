import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def test_coleta_soma_cada_moeda():
    comb = next(x for x in JOGO['externalEvents'] if x['name'] == 'Combate')['events']
    coleta = [e for e in anda(comb) if any(c['type']['value'] == 'CollisionNP' and c['parameters'][:2] == ['moeda', 'pato']
                                           for c in e.get('conditions') or [])]
    assert len(coleta) == 1 and coleta[0]['type'] == 'BuiltinCommonInstructions::ForEach' and coleta[0]['object'] == 'moeda'
