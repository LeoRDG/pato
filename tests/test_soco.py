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


def test_coice_deterministico_tres_raios_e_formula_unica():
    evs = list(walk(grupo()['events']))
    raios = [e for e in evs if any(c['type']['value'] == 'RaycastToPosition' and 'pato.soco_cos' in c['parameters'][3]
                                   for c in e.get('conditions', []))]
    assert len(raios) == 3 and all('soco_bateu' in json.dumps(e['actions']) for e in raios)      # três raios, qualquer um vale
    kick = [e for e in evs if any(a['parameters'][:2] == ['pato', 'coice_vx'] and 'coice_parede_x' in a['parameters'][3]
                                 for a in e.get('actions', []))]
    assert len(kick) == 1 and 'soco_bateu' in json.dumps(kick[0]['conditions'])
    acts = {a['parameters'][1]: a['parameters'][3] for a in kick[0]['actions'] if a['type']['value'] == 'SetNumberObjectVariable'}
    assert 'coice_parede_x' in acts['coice_vx'] and 'max(0, pato.soco_sin)' in acts['coice_vx']
    assert 'coice_y' in acts['soco_vy'] and 'coice_parede_y' in acts['soco_vy'] and 'abs(pato.soco_sin)' in acts['soco_vy']
    vel = [a for a in kick[0]['actions'] if a['type']['value'].endswith('SetCurrentSpeed')][0]['parameters'][3]
    assert vel == 'pato.PlatformerObject::CurrentSpeed() * (1 - abs(pato.soco_cos))'            # não soma à velocidade atual
    txt = json.dumps(grupo(), ensure_ascii=False)
    assert 'LIMIAR' not in txt and not any("'<='" in json.dumps(e['conditions']) for e in kick)       # sem faixas por ângulo
    js = [e for e in walk(kick[0]['events']) if e['type'] == 'BuiltinCommonInstructions::JsCode']
    assert len(js) == 1
    codigo = '\n'.join(js[0]['inlineCode'])
    assert '_currentFallSpeed = alvo' in codigo and '_setFalling()' in codigo and 'agora' not in codigo   # sempre sobrescreve
    # nada de pulo, voo automático, teclas travadas ou agarrar na parede
    for velho in ('soltou', 'voo', 'SimulateLeftKey', 'SimulateRightKey', 'SimulateJumpKey', 'PlatformBehavior::JumpSpeed',
                  'JumpSustainTime', 'MaxFallingSpeed', 'impulso', 'agarrado', 'parede_agora', 'KeyFromTextPressed'):
        assert velho not in txt
    mov = [e for e in evs if any(a['type']['value'] == 'SetX' and 'pato.coice_vx' in a['parameters'][2] for a in e.get('actions', []))]
    assert len(mov) == 1 and 'coice_parede_freio' in json.dumps(mov[0]['actions'])
    nomes = {v['name'] for v in OBJ['pato']['variables']}
    assert {'coice_y', 'coice_parede_x', 'coice_parede_y', 'coice_parede_freio', 'coice_vx', 'soco_vy', 'y_antes', 'soco_bateu'} <= nomes
    assert not nomes & {'coice_x', 'agarrado', 'parede_agora', 'pulo_base', 'pulo_restaurar', 'voo'}
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


def test_coice_nao_gasta_pulo():
    evs = list(walk(grupo()['events']))
    guarda = [e for e in evs if any(a['type']['value'] == 'ResetObjectTimer' and a['parameters'][1:] == ['"__CoyoteTime_CoyoteJump"']
                                    for a in e.get('actions', []))]
    assert len(guarda) == 1 and 'coice_guarda' in json.dumps(guarda[0]['conditions'])
    marca = [e for e in evs if any(a['parameters'][1:2] == ['coice_guarda'] and a['parameters'][2:3] == ['True']
                                   for a in e.get('actions', []))]
    assert len(marca) == 1 and all(any(c['type']['value'] == 'PlatformBehavior::IsOnFloor' for c in m['conditions']) for m in marca)
    assert any(v['name'] == 'coice_guarda' for v in OBJ['pato']['variables'])
