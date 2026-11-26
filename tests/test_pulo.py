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


def test_giro_em_todo_pulo_no_ar_e_volta_ao_pousar():
    giros = [e for e in eventos() if any(a['type']['value'].endswith('AddObjectAngleTween2') for a in e.get('actions', []))]
    assert len(giros) == 1
    # a tecla pode estar dentro de um "ou" com o toque (t215)
    conds = {(c['type']['value'], bool(c['type'].get('inverted')))
             for k in giros[0]['conditions'] for c in [k] + (k.get('subInstructions') or [])}
    assert {('KeyFromTextJustPressed', False), ('PlatformBehavior::CanJump', False), ('PlatformBehavior::IsOnFloor', True),
            ('AdvancedJump::AdvancedJump::CanCoyoteJump', True)} <= conds
    assert giros[0]['actions'][0]['parameters'][3].startswith('360 * (round(pato.Angle() / 360) + ')   # sempre uma volta a mais
    pouso = [e for e in eventos() if any(a['type']['value'] == 'Tween::RemoveTween' and a['parameters'][0] == 'pato' for a in e.get('actions', []))]
    assert len(pouso) == 1 and any(a['parameters'] == ['pato', '=', '0'] for a in pouso[0]['actions'])
