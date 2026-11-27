"""Controles de toque (t215, reformados na t216, ajustados na t218): variáveis, objetos, grupo no Jogador, teclas que
aceitam o toque e tela cheia."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))


def folha(nome):
    return next(x for x in JOGO['externalEvents'] if x['name'] == nome)


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def test_variaveis_e_objetos():
    toque = next(v for v in JOGO['variables'] if v['name'] == 'toque')
    nomes = {c['name'] for c in toque['children']}
    assert {'forcar', 'ativo', 'mov_raio', 'mira_dist', 'tiro_limiar', 'pulo_limiar', 'botao_raio', 'opacidade'} <= nomes
    # t216: posições ancoradas nas bordas (px da HUD), área de toque maior que o desenho, mira automática, tela cheia
    assert {'tela_cheia', 'opacidade_repouso', 'mov_esq', 'mov_baixo', 'mov_zona', 'segue', 'mira_dir', 'mira_baixo', 'mira_auto', 'mira_auto_alcance', 'mira_auto_espera',
            'mira_segue_andar', 'pulo_dir', 'pulo_baixo', 'pulo_raio', 'pulo_toque', 'botao_toque'} <= nomes
    for b in ('pulo', 'dash', 'usar'):
        assert {f'{b}_dir', f'{b}_baixo'} <= nomes
    # t218: pulo só pelo botão, sem botão de recarga, E só quando há o que usar, analógicos mais apagados
    assert not {'pulo_no_analogico', 'pulo_solta', 'pulo_analogico', 'recarga_dir', 'recarga_baixo', 'recarga_id'} & nomes
    assert {'usar_pode', 'opacidade_analogico'} <= nomes
    assert not {'mov_x', 'pulo_x', 'dash_y', 'folga'} & nomes          # frações da largura da t215 saíram
    val = {c['name']: c.get('value') for c in toque['children']}
    assert val['pulo_toque'] > val['pulo_raio'] and val['botao_toque'] > val['botao_raio']
    objs = {o['name']: o for o in JOGO['objects']}
    assert {'toque_base', 'toque_alavanca', 'toque_botao'} <= set(objs)
    assert [a['name'] for a in objs['toque_botao']['animations']] == ['pulo', 'dash', 'usar']
    assert [a['name'] for a in objs['toque_base']['animations']] == ['base', 'mira']
    for f in ('base', 'base_mira', 'alavanca', 'botao_pulo', 'botao_dash', 'botao_usar'):
        assert os.path.exists(os.path.join(RAIZ, f'assets/toque/{f}.png'))


def test_grupo_antes_dos_controles():
    nomes = [e.get('name') for e in folha('Jogador')['events']]
    assert nomes.index('Toque (celular)') < nomes.index('Controle do Pato') < nomes.index('Controle das Armas')
    txt = json.dumps(folha('Jogador')['events'])
    assert 'SystemInfo::IsMobile' in txt and 'StartedTouchOrMouseId' in txt and 'HasTouchEnded' in txt
    assert 'TouchSimulateMouse' in txt
    grupo = next(e for e in folha('Jogador')['events'] if e.get('name') == 'Toque (celular)')
    g = json.dumps(grupo)
    assert 'toque.pulo_dir' in g and 'toque.pulo_toque' in g and 'toque.mov_zona' in g
    assert 'PickNearest' in g and '"Inimigo"' in g                    # mira automática no inimigo mais perto
    js = ['\n'.join(e['inlineCode']) for e in todos(grupo['events']) if e['type'] == 'BuiltinCommonInstructions::JsCode']
    assert len(js) == 2
    codigo = next(c for c in js if 'touchend' in c)
    assert 'touchend' in codigo and 'setFullScreen(true)' in codigo and 'tela_cheia' in codigo
    assert 'orientation.lock("landscape")' in codigo
    # t218: desligar a simulação do mouse solta o botão preso (senão o pato atira sozinho)
    solta = next(c for c in js if 'touchSimulateMouse(false)' in c)
    assert 'onMouseButtonReleased' in solta
    evs = json.dumps(grupo['events'][1:])                                # sem o comentário
    assert 'pulo_analogico' not in evs and 'recarga_id' not in evs and '\\"recarga\\"' not in evs
    assert 'toque.usar_pode' in g


def test_teclas_aceitam_o_toque():
    soltas = [c['parameters'][1] for e in todos(folha('Jogador')['events']) for c in e.get('conditions') or []
              if c['type']['value'] == 'KeyFromTextPressed']
    assert soltas == []                                   # a, d, Space, LShift e r ficam dentro de um "ou"
    ous = [c for e in todos(folha('Jogador')['events']) for c in e.get('conditions') or []
           if c['type']['value'] == 'BuiltinCommonInstructions::Or']
    pares = {(c['subInstructions'][0]['parameters'][1], c['subInstructions'][1]['parameters'][0]) for c in ous
             if len(c.get('subInstructions') or []) == 2 and c['subInstructions'][1]['type']['value'] == 'BooleanVariable'
             and c['subInstructions'][0]['type']['value'].startswith(('Key', 'Mouse'))}
    assert {('"a"', 'toque.esquerda'), ('"d"', 'toque.direita'), ('"Space"', 'toque.pulo'),
            ('"Space"', 'toque.pulo_agora'), ('"LShift"', 'toque.dash'), ('"r"', 'toque.recarga'),
            ('"Left"', 'toque.tiro')} <= pares
    for nome in ('Portais', 'Hubs', 'Loja'):
        txt = json.dumps(folha(nome)['events'])
        assert '"toque.usar_agora"' in txt


def test_mira_le_mira_x_y():
    txt = json.dumps(folha('Jogador')['events'])
    assert 'atan2(mira_y - (pato.Y()' in txt
    assert '"mira_x", "<", "pato.CenterX()"' in txt or '"mira_x", ">=", "pato.CenterX()"' in txt
    assert '"mira_x", "=", "MouseX()"' in txt                # no computador continua sendo o mouse
