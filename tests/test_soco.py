import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def grupo():
    jog = [x for x in JOGO['externalEvents'] if x['name'] == 'Jogador'][0]
    g = [e for e in walk(jog['events']) if e.get('name') == 'Soco']
    assert len(g) == 1
    return g[0]


def test_soco_no_botao_direito_com_luva_e_dano_pequeno():
    evs = list(walk(grupo()['events']))
    soco = [e for e in evs if any(c['parameters'][1:2] == ['"Right"'] and c['type']['value'] == 'MouseButtonFromTextPressed' and
                                  not c['type'].get('inverted') for c in e.get('conditions', [])) and e.get('events')][0]
    conds = json.dumps(soco['conditions'])
    assert 'rmb_antes' in conds and '\\"soco\\"' in conds          # só ao apertar, com espera
    txt = json.dumps(soco, ensure_ascii=False)
    assert '"Create"' in txt and '"soco"' in txt and 'som_soco.wav' in txt
    acerto = [e for e in walk(soco['events']) if e.get('object') == 'Inimigo'][0]     # cada inimigo é testado de verdade
    dano = [a for a in acerto['actions'] if a['parameters'][:2] == ['Inimigo', 'vida']][0]['parameters'][3]
    assert 'round(12 *' in dano                                    # bem menos que a pistola (26)
    assert any(a['parameters'][:2] == ['Inimigo', 'socado'] for a in acerto['actions'])
    assert 'soco' in OBJ and os.path.exists(os.path.join(RAIZ, 'assets', 'soco_luva.png'))
    assert all(any(v['name'] == 'socado' for v in OBJ[m['name']]['variables'])
               for g in JOGO['objectsGroups'] if g['name'] == 'Inimigo' for m in g['objects'])


def test_soco_vai_na_direcao_da_mira_com_rastro():
    txt = json.dumps(grupo(), ensure_ascii=False)
    assert 'atan2(MouseY() - pato.CenterY(), MouseX() - pato.CenterX())' in txt       # ângulo até o mouse, não só esquerda/direita
    evs = list(walk(grupo()['events']))
    acerto = [e for e in evs if e.get('object') == 'Inimigo'][0]
    conds = json.dumps(acerto['conditions'])
    assert 'pato.soco_cos' in conds and 'pato.soco_sin' in conds                      # o acerto segue a direção do soco
    for nome in ('soco', 'soco_rastro'):
        assert any(a['type']['value'] == 'SetAngle' and a['parameters'][0] == nome for e in evs for a in e.get('actions', []))
        assert any(a['type']['value'] == 'Delete' and a['parameters'][0] == nome for e in evs for a in e.get('actions', []))
    quadros = OBJ['soco_rastro']['animations'][0]['directions'][0]['sprites']
    assert len(quadros) == 4 and all(os.path.exists(os.path.join(RAIZ, 'assets', q['image'])) for q in quadros)


def test_soco_no_terreno_da_velocidade_contraria_sem_usar_o_pulo():
    evs = list(walk(grupo()['events']))
    bate = [e for e in evs if any(c['type']['value'] == 'RaycastToPosition' and 'pato.soco_cos' in c['parameters'][3] and
                                  'pato.soco_sin' in c['parameters'][4] for c in e.get('conditions', []))]
    assert len(bate) == 1                                          # o raio vai na direção do soco
    vel = [a for a in bate[0]['actions'] if a['type']['value'].endswith('SetCurrentSpeed')][0]['parameters'][3]
    assert '- pato.soco_cos * pato.coice_x' in vel                           # contra a direção do soco
    vert = bate[0]['events'][0]
    assert vert['actions'][0]['parameters'][:4] == ['pato', 'soco_vy', '=', '-pato.soco_sin * pato.coice_y']
    js = [e for e in vert['events'] if e['type'] == 'BuiltinCommonInstructions::JsCode']
    assert len(js) == 1
    codigo = '\n'.join(js[0]['inlineCode'])
    assert '_currentFallSpeed = alvo' in codigo and '_setFalling()' in codigo and 'soco_vy' in codigo
    # nada de pulo, voo automático, teclas travadas ou agarrar na parede
    txt = json.dumps(grupo(), ensure_ascii=False)
    for velho in ('soltou', 'voo', 'SimulateLeftKey', 'SimulateRightKey', 'SimulateJumpKey', 'PlatformBehavior::JumpSpeed', 'JumpSustainTime',
                  'MaxFallingSpeed', 'impulso', 'agarrado', 'parede_agora', 'KeyFromTextPressed'):
        assert velho not in txt
    nomes = {v['name'] for v in OBJ['pato']['variables']}
    assert {'soco_vy', 'y_antes', 'coice_x', 'coice_y'} <= nomes   # força do coice ajustável no GDevelop
    assert {'soco_vy', 'y_antes'} <= nomes and not nomes & {'agarrado', 'parede_agora', 'pulo_base', 'pulo_restaurar', 'voo'}
    jog = [x for x in JOGO['externalEvents'] if x['name'] == 'Jogador'][0]
    assert not any(e.get('name') == 'Soco e paredes' for e in walk(jog['events']))


def test_bater_no_teto_subindo_zera_a_velocidade():
    evs = list(walk(grupo()['events']))
    teto = [e for e in evs if any('CurrentFallSpeed()' in c['parameters'][0] and c['parameters'][1:] == ['<', '0']
                                  for c in e.get('conditions', []))]
    assert len(teto) == 1 and 'pato.y_antes' in json.dumps(teto[0]['conditions'])
    assert teto[0]['actions'][0]['type']['value'].endswith('SetCurrentFallSpeed')
    ordem = [i for i, e in enumerate(grupo()['events']) if e is teto[0] or 'Right' in json.dumps(e.get('conditions', []))]
    assert grupo()['events'][ordem[0]] is teto[0]                   # confere antes do soco do quadro


def test_eventos_antigos_de_queda_nao_zeram_a_subida_do_coice():
    jog = [x for x in JOGO['externalEvents'] if x['name'] == 'Jogador'][0]
    FALL = 'pato.PlatformerObject::CurrentFallSpeed()'
    mexem = [e for e in walk(jog['events']) if any(a['type']['value'].endswith('SetCurrentFallSpeed') and FALL in a['parameters'][3]
                                                   for a in e.get('actions', []))]
    assert len(mexem) >= 1
    assert all(sum(c['parameters'][:3] == [FALL, '>=', '0'] for c in e['conditions']) == 1 for e in mexem)
