import json, os

JOGO = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}


def acoes():
    def walk(evs):
        for e in evs:
            yield e
            yield from walk(e.get('events', []))
    jog = [e for e in JOGO['externalEvents'] if e['name'] == 'Jogador'][0]
    return [(a['type']['value'], a['parameters']) for e in walk(jog['events']) for a in e.get('actions', [])]


def test_poeira_existe_e_esta_numa_pasta():
    assert 'poeira' in OBJ and OBJ['poeira']['type'] == 'ParticleSystem::ParticleEmitter'
    assert '"objectName": "poeira"' in json.dumps(JOGO['objectsFolderStructure'])


def test_buffer_pulo_curto_e_queda_pesada():
    a = acoes()
    assert any(t == 'ResetObjectTimer' and p[1] == '"bufpulo"' for t, p in a)
    assert any(t == 'PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed' and '* 0.45' in p[3] for t, p in a)
    assert any(t == 'PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed' and '1400 * TimeDelta()' in p[3] for t, p in a)


def test_sem_animacao_falsa_no_pato():
    a = acoes()
    assert not any(t.startswith('ResizableCapability::') and p[0] == 'pato' for t, p in a)   # squash & stretch saiu
    assert not any(t in ('SetXY', 'SetAngle') and p[0] == 'pato' for t, p in a)              # nem reposiciona nem gira o pato
    assert not any(t.endswith('AddObjectAngleTween2') and p[0] == 'pato' for t, p in a)      # giro do pulo duplo saiu
    nomes = {v['name'] for v in OBJ['pato']['variables']}
    assert not nomes & {'larg0', 'alt0', 'imp', 'ar', 'pe_y', 'cx'} and 'queda_vy' in nomes
