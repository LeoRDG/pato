import json, os

JOGO = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json'), encoding='utf-8'))


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events', []))


def grupo_bhop():
    jog = [e for e in JOGO['externalEvents'] if e['name'] == 'Jogador'][0]
    gs = [e for e in walk(jog['events']) if e.get('name') == 'Bunny hop']
    assert len(gs) == 1
    return list(walk(gs[0]['events']))


def test_variaveis_do_bhop_no_pato():
    pato = [o for o in JOGO['objects'] if o['name'] == 'pato'][0]
    nomes = {v['name'] for v in pato['variables']}
    assert {'bhop_janela', 'bhop_ganho', 'bhop_max_serie', 'bhop_vel_min', 'bhop_serie', 'bhop_vel_base', 'bhop_no_chao'} <= nomes


def test_sem_numeros_fixos_nas_regras():
    for e in grupo_bhop():
        for x in e.get('conditions', []) + e.get('actions', []):
            for p in x['parameters']:
                assert p in ('0', '') or not p.replace('.', '').isdigit(), p   # só 0 (comparar a série)


def test_pulo_logo_apos_pousar_sobe_a_serie():
    evs = grupo_bhop()
    sobe = [e for e in evs if any(a['parameters'][:2] == ['pato', 'bhop_serie'] and 'pato.bhop_serie + 1' in a['parameters'][3]
                                   for a in e.get('actions', []) if a['type']['value'] == 'SetNumberObjectVariable')]
    assert len(sobe) == 1
    conds = {c['type']['value'] for c in sobe[0]['conditions']}
    assert {'PlatformBehavior::IsJumping', 'CompareObjectTimer', 'AdvancedJump::HorizontalDash::IsDashing'} <= conds
    assert any(a['type']['value'] == 'PlatformBehavior::MaxSpeed' for a in sobe[0]['actions'])


def test_som_discreto_sobe_a_cada_degrau():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.exists(os.path.join(raiz, 'assets', 'som_bhop.wav'))
    assert any(r['name'] == 'som_bhop.wav' for r in JOGO['resources']['resources'])
    sobe = [e for e in grupo_bhop() if any('pato.bhop_serie + 1' in a['parameters'][3] for a in e.get('actions', [])
                                            if a['type']['value'] == 'SetNumberObjectVariable')][0]
    som = [a for a in sobe['actions'] if a['type']['value'] == 'PlaySound']
    assert len(som) == 1 and som[0]['parameters'][1] == 'som_bhop.wav'
    assert som[0]['parameters'][3] == 'pato.bhop_som_volume' and 'pato.bhop_som_passo' in som[0]['parameters'][4]
    pato = [o for o in JOGO['objects'] if o['name'] == 'pato'][0]
    vol = [v['value'] for v in pato['variables'] if v['name'] == 'bhop_som_volume'][0]
    assert vol < 40   # mais baixo que o pulo


def test_ficar_no_chao_zera_e_volta_a_base():
    zera = [e for e in grupo_bhop() if any(a['parameters'] == ['pato', 'bhop_serie', '=', '0'] for a in e.get('actions', []))]
    assert len(zera) == 1
    assert any(a['type']['value'] == 'PlatformBehavior::MaxSpeed' and a['parameters'][-1] == 'pato.bhop_vel_base'
               for a in zera[0]['actions'])
