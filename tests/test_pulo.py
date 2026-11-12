import json, os

JOGO = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'), encoding='utf-8'))


def eventos():
    def walk(evs):
        for e in evs:
            yield e
            yield from walk(e.get('events', []))
    jog = [e for e in JOGO['externalEvents'] if e['name'] == 'Jogador'][0]
    return list(walk(jog['events']))


def test_propulsor_segue_o_pato():
    angulos = [a['parameters'][2] for e in eventos() for a in e.get('actions', [])
               if a['type']['value'] == 'SetAngle' and a['parameters'][0] == 'propulsor']
    assert len(angulos) == 1 and angulos[0].startswith('AngleBetweenPositions(')  # só o evento que acompanha o pato
