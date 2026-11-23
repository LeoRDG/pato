"""Mecânicas dos inimigos (tools/t78_inimigos_mecanicas.py): cada inimigo com o seu comportamento, tudo em variáveis."""
import json, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
EXT = {e['name']: e['events'] for e in JOGO['externalEvents']}
GRUPOS = {g['name']: [x['name'] for x in g['objects']] for g in JOGO['objectsGroups']}
RECURSOS = {r['name']: r for r in JOGO['resources']['resources']}

INIMIGOS = ['condenado_azul', 'condenado_inchado', 'arvore_condenada',
            'caveira_gigante', 'caveira_azul', 'cabeca_voadora', 'diabinho', 'moscas', 'olho_demoniaco', 'mina_demoniaca',
            'condenado_em_chamas', 'pigman', 'sapo', 'cutulu', 'voador', 'querubim', 'serafim', 'ofanim', 'roda_anjo']


def grupos_de_eventos(evs, saida=None):
    saida = {} if saida is None else saida
    for e in evs:
        if e['type'] == 'BuiltinCommonInstructions::Group':
            saida[e['name']] = e
        grupos_de_eventos(e.get('events', []), saida)
    return saida


INI = EXT['Inimigos'] + EXT['InimigosInferno'] + EXT['InimigosPurgatorio'] + EXT['InimigosParaiso']
G = grupos_de_eventos(INI)


def variaveis(nome):
    return {v['name'] for v in OBJ[nome]['variables']}


def test_folha_migrada_uma_vez_e_ligada_nas_fases():
    for cena, reino in (('Inferno', 'InimigosInferno'), ('Purgatorio', 'InimigosPurgatorio')):
        lay = next(l for l in JOGO['layouts'] if l['name'] == cena)
        alvos = [e.get('target') for e in lay['events']]
        assert alvos.index('Inimigos') + 1 == alvos.index(reino)
        assert {v['name'] for v in lay['variables']} >= {'olho_rx', 'olho_ry', 'moscas_alerta', 'moscas_alerta_x', 'moscas_alerta_y'}


def test_cada_inimigo_tem_o_seu_grupo_de_eventos():
    titulos = ' | '.join(G)
    for parte in ('Condenado azul (investida)', 'Condenado inchado', 'Árvore condenada (espinheiro)', 'Caveira azul', 'Diabinho (ladrão)', 'Mina demoníaca',
                  'Condenado em chamas (frenesi)', 'Pigman (pancada)', 'Sapo', 'Serafim', 'Projéteis dos inimigos'):
        assert parte in titulos, parte


def test_variaveis_usadas_existem_no_objeto():
    # todo `objeto.variavel` usado no grupo de um inimigo precisa existir no objeto (valor ajustável no GDevelop)
    metodos = {'X', 'Y', 'CenterX', 'CenterY', 'Width', 'Height', 'Angle', 'ObjectTimerElapsedTime', 'PlatformerObject',
               'Opacity', 'Animation', 'DistanceToPosition', 'Behavior', 'Variable', 'VariableString', 'ZOrder'}
    for nome in INIMIGOS:
        texto = json.dumps([g for t, g in G.items() if nome.replace('_', ' ') in t.lower() or nome in json.dumps(g)])
        usados = set(re.findall(r'\b' + nome + r'\.([A-Za-z_]+)\b', texto)) - metodos
        faltam = {u for u in usados if not u.startswith('PlatformerObject')} - variaveis(nome)
        assert not faltam, (nome, faltam)


def test_inimigo_criado_no_meio_da_cena_tambem_e_preparado():
    prep = json.dumps(G['Preparar inimigos'])
    assert '"preparado", "False"' in prep
    for t in ('ataque', 'estado', 'tiro', 'pulo'):
        assert f'"Inimigo", "\\"{t}\\""' in prep
    assert all('preparado' in variaveis(n) for n in INIMIGOS)


def test_bala_ricocheteia_em_invulneravel():
    comb = json.dumps(EXT['Combate'])
    assert 'som_ping.wav' in comb and '"invulneravel", "False"' in comb and '"reflete", "True"' in comb
    assert all({'invulneravel', 'reflete', 'firme'} <= variaveis(n) for n in INIMIGOS)


def test_anjos_entram_nos_grupos_de_inimigo():
    for anjo in ('querubim', 'serafim', 'ofanim', 'roda_anjo'):
        assert anjo in GRUPOS['Inimigo'] and anjo in GRUPOS['Personagem']
    assert any(b['type'] == 'PlatformBehavior::PlatformerObjectBehavior' for b in OBJ['roda_anjo']['behaviors'])


def test_projeteis_novos_e_sons_existem():
    anims = {a['name'] for a in OBJ['projetil_inimigo']['animations']}
    assert anims >= {'osso', 'espinho', 'bile', 'flecha', 'luz', 'olho', 'bomba', 'onda', 'fogo'}
    assert {'tipo', 'gravidade', 'vy', 'gira', 'ttl'} <= variaveis('projetil_inimigo')
    texto = json.dumps(INI) + json.dumps(EXT['Combate'])
    for som in set(re.findall(r'som_[a-z_]+\.wav', texto)):
        assert som in RECURSOS, som
    for a in OBJ['projetil_inimigo']['animations']:
        for d in a['directions']:
            for s in d['sprites']:
                assert os.path.exists(os.path.join(RAIZ, RECURSOS[s['image']]['file'])), s['image']
    for som in ('som_arremesso', 'som_ping', 'som_laser', 'som_roubo', 'som_levanta'):
        assert os.path.exists(os.path.join(RAIZ, RECURSOS[som + '.wav']['file']))


def test_condenado_em_chamas_no_inferno():
    assert 'zumbi' not in OBJ and 'condenado_em_chamas' in OBJ
    ini = next(c for c in JOGO['objectsFolderStructure']['children'] if c.get('folderName') == 'inimigos')
    inferno = next(c for c in ini['children'] if c.get('folderName') == 'inferno')
    assert 'condenado_em_chamas' in [c.get('objectName') for c in inferno['children']]
    assert all(RECURSOS[s['image']]['file'].startswith('assets/inimigos/inferno/condenado_em_chamas/')
               for a in OBJ['condenado_em_chamas']['animations'] for d in a['directions'] for s in d['sprites'])
    grupo = json.dumps(G['Condenado em chamas (frenesi)'])
    assert 'sangue_verde' not in grupo and 'explosao_faiscas' in grupo and 'som_espiral.wav' in grupo


def test_morte_dos_anjos_com_particulas():
    em = OBJ['anjo_morte_luz']
    assert em['type'] == 'ParticleSystem::ParticleEmitter' and em['destroyWhenNoParticles']
    grupo = json.dumps(G['Morte dos anjos (partículas de luz)'])
    for anjo in ('querubim', 'serafim', 'ofanim', 'roda_anjo'):
        assert {'morte_luz_raio', 'morte_luz_qtd'} <= variaveis(anjo)
        assert f'"{anjo}.morte_luz_raio"' in grupo and f'"{anjo}.morte_luz_qtd"' in grupo
    assert 'Condenado em chamas (frenesi)' in json.dumps([e.get('name') for e in EXT['InimigosInferno']], ensure_ascii=False)
