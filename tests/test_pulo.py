import json, os

JOGO = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'), encoding='utf-8'))


def eventos():
    def walk(evs):
        for e in evs:
            yield e
            yield from walk(e.get('events', []))
    jog = [e for e in JOGO['externalEvents'] if e['name'] == 'Jogador'][0]
    return list(walk(jog['events']))


def test_giro_so_no_pulo_no_ar():
    giros = [e for e in eventos() if any(a['type']['value'].endswith('AddObjectAngleTween2') for a in e.get('actions', []))]
    assert len(giros) == 1
    conds = {(c['type']['value'], bool(c['type'].get('inverted'))) for c in giros[0]['conditions']}
    assert ('KeyFromTextJustPressed', False) in conds and ('PlatformBehavior::IsOnFloor', True) in conds
    assert 'alvo.CenterX()' in giros[0]['actions'][0]['parameters'][3]


def test_propulsor_segue_o_vetor_de_movimento():
    angulos = [a['parameters'][2] for e in eventos() for a in e.get('actions', [])
               if a['type']['value'] == 'SetAngle' and a['parameters'][0] == 'propulsor']
    assert len(angulos) == 3  # pulo, dash e o acompanhamento a cada quadro
    assert all(x.startswith('AngleBetweenPositions(0, 0, pato.PlatformerObject::CurrentSpeed()') and x.endswith('+ 180') for x in angulos)
