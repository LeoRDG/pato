import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
RES = {r['name'] for r in JOGO['resources']['resources']}


def imagens(o):
    return [s['image'] for a in o['animations'] for s in a['directions'][0]['sprites']]


def test_sprites_das_armas_e_arma_nova():
    assert imagens(OBJ['pistola']) == ['arma_pistola.png'] and imagens(OBJ['doze']) == ['arma_doze.png']
    assert imagens(OBJ['minigun']) == ['arma_minigun.png'] and imagens(OBJ['lanca']) == ['arma_lanca.png']
    for n in ('pistola', 'doze', 'minigun', 'lanca'):
        assert f'arma_{n}.png' in RES and os.path.exists(os.path.join(RAIZ, 'assets', f'arma_{n}.png'))
    assert {'lanca'} <= {m['name'] for g in JOGO['objectsGroups'] if g['name'] == 'Arma' for m in g['objects']}


def test_raio_so_na_lanca():
    raio = {n: {v['name']: v['value'] for v in OBJ[n]['variables']}['raio'] for n in ('pistola', 'doze', 'minigun', 'lanca')}
    assert raio['lanca'] > 0 and raio['pistola'] == raio['doze'] == raio['minigun'] == 0


def test_explosao_e_troca_e_hud():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    for pedaco in ('Explosão da granada', 'Num4', 'armas.lanca', 'hud_slot4', 'LANCA-GRANADAS'):   # t187: sem acento
        assert pedaco in txt, pedaco
    for lay in JOGO['layouts']:
        nomes = {i['name'] for i in lay['instances']}
        if 'hud_slot3' in nomes:
            assert 'hud_slot4' in nomes
            assert max(i['x'] for i in lay['instances'] if i['name'].startswith('hud_slot')) + 52 <= 1920


def test_recursos_do_hud_existem():
    for r in ('hud/arma_lanca.png', 'hud/slot_4.png', 'hud/slot_4_sel.png', 'hud/slot_4_lock.png'):
        assert r in RES and os.path.exists(os.path.join(RAIZ, 'assets', r))


def test_tiro_e_laser_saem_do_bocal_mira_livre_e_granada_cai():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    assert 'FireTowardObject' in txt and '"bocal_x", "bocal_y", "projetil"' in txt
    assert 'LineV2", "laser", "bocal_x"' not in txt and '"laser", "bocal_x", "bocal_y"' in txt
    assert 'ToRad(55)' not in txt and '"mira_a", "=", "atan2(mira_y' in txt   # sem limite de ângulo (mira_y: mouse ou toque, t215)
    assert 'abs(MouseX() - Arma.CenterX())' not in txt   # nem a sobra dele: o ângulo sai do ombro do pato, 360 graus
    assert 'Gravidade da granada' in txt and 'projetil.gravidade * TimeDelta()' in txt


def test_coice_tremor_e_clarao_do_cano():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    nomes = {a['name'] for a in OBJ['flash_cano']['animations']}
    assert nomes == {'pistola', 'doze', 'minigun', 'lanca'}
    for n in ('pistola', 'doze', 'minigun', 'lanca'):
        assert os.path.exists(os.path.join(RAIZ, 'assets', f'flash_{n}.png')) and f'flash_{n}.png' in RES
        assert {v['name'] for v in OBJ[n]['variables']} >= {'kick', 'tremor', 'bocal_f'}
    assert 'fogo_pistola' not in OBJ and OBJ['fogo_lanca']['destroyWhenNoParticles']
    assert {v['name']: v['value'] for v in OBJ['minigun']['variables']}['tremor'] > 0
    assert 'Arma.kick' in txt and 'coice_j' in txt and 'Arma.bocal_f' in txt and 'flash_cano.dur' in txt


def test_arma_atras_do_pato():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    assert '"SetZOrder"' in txt and 'pato.ZOrder() - 2' in txt and 'pato.ZOrder() - 1' in txt


def test_sons_sintetizados_das_armas():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    for n in ('pistola', 'doze', 'minigun', 'lanca', 'explosao'):
        assert f'som_{n}.wav' in RES and os.path.exists(os.path.join(RAIZ, 'assets', f'som_{n}.wav'))
        assert f'"som_{n}.wav"' in txt
    for antigo in ('glock18-1[1].wav', '"shotgun.wav"', '"minigun.wav"', '"tiro.wav"', 'sawedoff'):
        assert antigo not in txt


def test_explosao_de_particulas_sem_hit():
    comb = [e for e in JOGO['externalEvents'] if e['name'] == 'Combate'][0]

    def acha(evs):
        for e in evs:
            if e.get('name') == 'Explosão da granada':
                return e
            r = acha(e.get('events', []))
            if r:
                return r
    txt = json.dumps(acha(comb['events']), ensure_ascii=False)
    assert '"hit"' not in txt
    for n in ('explosao_fumaca', 'explosao_fogo', 'explosao_faiscas'):
        assert f'"{n}"' in txt and OBJ[n]['type'] == 'ParticleSystem::ParticleEmitter' and OBJ[n]['destroyWhenNoParticles']
        assert OBJ[n]['emitterAngleB'] - OBJ[n]['emitterAngleA'] == 360


def test_sangue_por_inimigo_no_lugar_do_hit():
    inimigos = [m['name'] for g in JOGO['objectsGroups'] if g['name'] == 'Inimigo' for m in g['objects']]
    tipos = set()
    for n in inimigos:
        v = {x['name']: x['value'] for x in OBJ[n]['variables']}
        assert v.get('sangue'), n
        tipos.add(v['sangue'])
    for t in tipos:
        assert OBJ[f'sangue_{t}']['type'] == 'ParticleSystem::ParticleEmitter' and OBJ[f'sangue_{t}']['destroyWhenNoParticles']
    comb = json.dumps([e for e in JOGO['externalEvents'] if e['name'] == 'Combate'][0], ensure_ascii=False)
    assert '"Create"}, "parameters": ["", "hit"' not in comb
    assert all(f'"sangue_{t}"' in comb for t in tipos)


def test_minigun_tom_normal_e_giro_dos_canos():
    ev = json.dumps([x['events'] for x in JOGO['externalEvents'] if x['name'] == 'Jogador'])
    assert '"som_minigun.wav", "1", "80", "80", "1"' in ev                 # antes: tom -40 (limitado a 0,5 = metade da velocidade)
    assert '"som_minigun_giro.wav", "5", "yes", "0", "1"' in ev and 'som_minigun_giro.wav' in RES
    assert '"SetSoundChannelVolume"' in ev and '35 * giro' in ev and any(v['name'] == 'giro' for v in JOGO['variables'])
    assert os.path.exists(os.path.join(RAIZ, 'assets', 'som_minigun_giro.wav'))


def test_minigun_so_atira_com_os_canos_girando():
    ev = json.dumps([x['events'] for x in JOGO['externalEvents'] if x['name'] == 'Jogador'])
    assert ev.count('giro + 1 - Arma.espera_giro') == 1
    espera = {n: {v['name']: v['value'] for v in OBJ[n]['variables']}['espera_giro'] for n in ('pistola', 'doze', 'minigun', 'lanca')}
    assert espera == {'pistola': 0, 'doze': 0, 'minigun': 1, 'lanca': 0}


def test_bombeada_da_doze_nova():
    ev = json.dumps([x['events'] for x in JOGO['externalEvents']])
    assert 'carrega_doze.mp3' not in ev and ev.count('"som_doze_pump.wav", "2"') == 1 and 'som_doze_pump.wav' in RES
    assert os.path.exists(os.path.join(RAIZ, 'assets', 'som_doze_pump.wav'))


def test_som_de_recarga_por_arma():
    ev = json.dumps([x['events'] for x in JOGO['externalEvents'] if x['name'] == 'Jogador'])
    assert 'carregar.mp3' not in ev
    for n in ('pistola', 'doze', 'minigun', 'lanca'):
        assert f'"som_recarga_{n}.wav", "6"' in ev and f'som_recarga_{n}.wav' in RES
        assert os.path.exists(os.path.join(RAIZ, 'assets', f'som_recarga_{n}.wav'))
        assert any(v['name'] == 'som_recarga' for v in OBJ[n]['variables'])


def test_granada_da_1_e_explosao_no_emissor_com_queda():
    lanca = {v['name']: v['value'] for v in OBJ['lanca']['variables']}
    assert lanca['dano'] == 1 and lanca['dano_explosao'] > 1
    assert {v['name'] for v in OBJ['explosao_fogo']['variables']} >= {'dano', 'raio', 'repulsao', 'aplicado'}
    comb = [x for x in JOGO['externalEvents'] if x['name'] == 'Combate'][0]

    def walk(evs):
        for e in evs:
            yield e
            yield from walk(e.get('events') or [])
    dano = [e for e in walk(comb['events']) if e.get('name') == 'Dano da explosão'][0]
    fe = [e for e in walk(dano['events']) if e['type'] == 'BuiltinCommonInstructions::ForEach']
    assert [e['object'] for e in fe] == ['explosao_fogo', 'Inimigo']   # cada inimigo é escolhido de verdade
    txt = json.dumps(dano, ensure_ascii=False)
    assert '(1 - exp_d / explosao_fogo.raio)' in txt and 'Inimigo.Width() / 2' in txt   # queda até a borda da caixa
