"""Desempenho (t220): variáveis desempenho.*, script do celular no Combate, textos da tela de atributos só quando mudam,
lente negra e "Brilho" ligados só quando usados, lava perto da câmera, fundos do Inferno e raio do laser."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))


def folha(nome):
    return next(x for x in JOGO['externalEvents'] if x['name'] == nome)


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def acoes(nome):
    return [a for e in todos(folha(nome)['events']) for a in e.get('actions') or []]


def test_variaveis():
    d = next(v for v in JOGO['variables'] if v['name'] == 'desempenho')
    val = {c['name']: c.get('value') for c in d['children']}
    assert {'forcar_celular', 'resolucao_celular', 'fps_max_celular', 'fps_min_celular', 'sem_filtros_celular',
            'fundo_corte', 'lava_margem', 'bolha_vida_max'} <= set(val)
    assert 0 < val['resolucao_celular'] <= 1 and val['fps_min_celular'] <= val['fps_max_celular']
    # no computador o fps continua o das propriedades do projeto
    assert JOGO['properties']['maxFPS'] == 60


def test_script_do_celular_em_todas_as_cenas_de_jogo():
    g = next(e for e in folha('Combate')['events'] if e.get('name') == 'Desempenho (celular)')
    codigo = '\n'.join(next(e for e in todos(g['events']) if e['type'].endswith('JsCode'))['inlineCode'])
    for trecho in ('isMobile()', 'forcar_celular', 'r.resolution = res', 'setMaximumFps', '_minFPS',
                   '"Lente negra"', '"Brilho das estrelas"', '"Menos vibrante"', '"Brilho"', '"moeda"'):
        assert trecho in codigo, trecho
    for cena in JOGO['layouts']:
        links = [e.get('target') for e in cena['events'] if e['type'].endswith('Link')]
        if 'Inimigos' in links or 'Hubs' in links:                # cenas de jogo (hubs e fases)
            assert 'Combate' in links, cena['name']


def test_textos_so_quando_mudam():
    g = next(e for e in folha('Hubs')['events'] if e.get('name') == 'Atributos')
    fe = next(e for e in g['events'] if e.get('object') == 'ui_txt')
    assert 'ui_card[ui_txt.card].vis' in json.dumps(fe['conditions'])
    # ChangeColor e WrappingWidth só dentro de um subevento que compara com o valor atual
    for e in todos(g['events']):
        for a in e.get('actions') or []:
            if a['type']['value'] in ('TextObject::ChangeColor', 'TextObject::WrappingWidth') and \
                    a['parameters'][0] == 'ui_txt':
                assert any(c['parameters'][1] in ('cor_nova', 'larg_nova') for c in e['conditions']), e


def test_efeitos_so_quando_usados():
    for nome in ('Inimigos', 'InimigosInferno', 'InimigosPurgatorio', 'InimigosParaiso'):
        for e in todos(folha(nome)['events']):
            acs = e.get('actions') or []
            for i, a in enumerate(acs):
                if a['type']['value'].endswith('SetEffectDoubleParameter') and a['parameters'][2] == '"Brilho"' \
                        and a['parameters'][3] == '"brightness"':
                    antes = acs[i - 1]
                    assert antes['type']['value'].endswith('EnableEffect')
                    assert antes['parameters'][3] == ('no' if a['parameters'][4] == '1' else 'yes')
    lente = [a for a in acoes('InimigosParaiso') if a['type']['value'] == 'EnableLayerEffect']
    assert len(lente) == 10


def test_lava_fundos_e_laser():
    txt = json.dumps(folha('CenarioInferno')['events'])
    assert 'desempenho.lava_margem' in txt and 'desempenho.bolha_vida_max' in txt and 'desempenho.fundo_corte' in txt
    ray = [e for e in todos(folha('Jogador')['events'])
           if any(c['type']['value'] == 'RaycastToPosition' for c in e.get('conditions') or [])]
    assert ray and all(e['conditions'][0]['parameters'][0] == 'GlobalVariable(upgrades.laser)' for e in ray)
