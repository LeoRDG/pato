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


def test_squash_ancorado_nos_pes():
    a = acoes()
    assert any(t.endswith('SetHeight') and p[0] == 'pato' for t, p in a)
    assert any(t == 'SetXY' and p[0] == 'pato' and 'pe_y' in p[4] for t, p in a)


def test_giro_nao_acontece_no_pulo_de_coiote():
    jog = [e for e in JOGO['externalEvents'] if e['name'] == 'Jogador'][0]
    txt = json.dumps(jog, ensure_ascii=False)
    assert '"AdvancedJump::AdvancedJump::CanCoyoteJump"' in txt
