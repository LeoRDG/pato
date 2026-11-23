"""Loja do Hub (catálogo de upgrades) e mercador como inimigo secreto: estrutura no jogo.json."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def glob(nome):
    return next(v for v in JOGO['variables'] if v['name'] == nome)


def obj(nome):
    return next((o for o in JOGO['objects'] if o['name'] == nome), None)


def ovar(o, nome):
    return next((v for v in o['variables'] if v['name'] == nome), None)


def ext(nome):
    return next(x for x in JOGO['externalEvents'] if x['name'] == nome)['events']


def tipos(e):
    return [c['type']['value'] for c in e.get('conditions') or []]


# ------------------------------------------------------------------ Tarefa 1: dados

def test_catalogo_tem_campos():
    cat = glob('loja_catalogo')
    assert cat['type'] == 'array' and len(cat['children']) >= 5
    ids = []
    for item in cat['children']:
        f = {c['name']: c['value'] for c in item['children']}
        assert {'id', 'nome', 'descricao', 'tipo', 'nivel_max', 'preco_base', 'preco_mult', 'requer'} <= set(f)
        assert f['nivel_max'] >= 1 and f['preco_base'] > 0 and f['preco_mult'] >= 1
        assert f['tipo'] == 'upgrade' and f['requer'] == ''
        ids.append(f['id'])
    assert sorted(ids) == sorted(c['name'] for c in glob('upgrades')['children'])


def test_trader_variaveis():
    t = obj('trader')
    assert ovar(t, 'estado')['value'] == 'calmo'
    assert ovar(t, 'paciencia')['value'] == 1
    assert ovar(t, 'multa')['value'] == 0.5
    assert ovar(t, 'max_vida')['value'] > 10
    assert glob('trader_morto')['value'] is False


def test_objetos_loja_existem():
    for nome in ('loja_painel', 'loja_linha', 'loja_desc', 'loja_dica'):
        assert obj(nome), nome
    assert ovar(obj('loja_linha'), 'indice') is not None
    # inimigos copiados no GDevelop já compartilham uuids de variáveis; só os objetos novos precisam ser únicos
    def coleta(x, uids):
        if isinstance(x, dict):
            if 'persistentUuid' in x:
                uids.append(x['persistentUuid'])
            for v in x.values():
                coleta(v, uids)
        elif isinstance(x, list):
            for v in x:
                coleta(v, uids)
        return uids
    novos = ('loja_painel', 'loja_linha', 'loja_desc', 'loja_dica')
    meus = coleta([obj(n) for n in novos], [])
    resto = coleta([o for o in JOGO['objects'] if o['name'] not in novos] + JOGO['variables'], [])
    assert len(meus) == len(set(meus)) and not set(meus) & set(resto)


# ------------------------------------------------------------------ Tarefa 2: reaplicar upgrades

def _aplicar():
    upg = next(e for e in ext('Jogador') if e.get('name') == 'Upgrades')
    grupo = next(e for e in upg['events'] if e.get('name') == 'Aplicar upgrades')
    alvo = next(e for e in grupo['events'] if any(a['type']['value'] == 'PlatformBehavior::MaxSpeed' for a in e.get('actions') or []))
    return grupo, alvo


def test_velocidade_parte_da_base():
    grupo, alvo = _aplicar()
    ms = next(a for a in alvo['actions'] if a['type']['value'] == 'PlatformBehavior::MaxSpeed')
    assert ms['parameters'][-1].startswith('pato.velocidade_base *')
    antes = grupo['events'][:grupo['events'].index(alvo)]
    assert any('SceneJustBegins' in tipos(e) and any('velocidade_base' in json.dumps(a['parameters']) for a in e['actions'])
               for e in antes)


def test_upgrades_reaplicaveis():
    _, alvo = _aplicar()
    (cond,) = alvo['conditions']
    assert cond['type']['value'] == 'BuiltinCommonInstructions::Or'
    subs = json.dumps(cond['subInstructions'])
    assert 'SceneJustBegins' in subs and 'reaplicar_upgrades' in subs
    assert any(a['parameters'][:3] == ['reaplicar_upgrades', 'False', ''] for a in alvo['actions'])


# ------------------------------------------------------------------ Tarefa 3: trava dos controles

def _entrada(c):
    t = c['type']
    return (any(k in t['value'] for k in ('Key', 'MouseButton', 'Gamepad')) and t['value'] != 'AnyKeyReleased'
            and not t.get('inverted'))


def test_toda_entrada_do_jogador_tem_trava():
    guardados = 0
    for e in anda(ext('Jogador')):
        if any(_entrada(c) for c in e.get('conditions') or []):
            assert any(c['type']['value'] == 'BooleanObjectVariable' and c['parameters'][:3] == ['pato', 'na_loja', 'False']
                       for c in e['conditions']), e['conditions']
            guardados += 1
    assert guardados > 0


# ------------------------------------------------------------------ Tarefa 4: eventos da loja

GRUPOS_LOJA = ['Dica', 'Abrir e fechar', 'Menu', 'Compra', 'Mercador']


def _grupo_loja(nome):
    return next(e for e in ext('Loja') if e.get('name') == nome)


def test_hub_liga_loja_por_ultimo():
    hub = next(l for l in JOGO['layouts'] if l['name'] == 'Hub')
    links = [e for e in hub['events'] if e['type'] == 'BuiltinCommonInstructions::Link']
    assert links[-1]['target'] == 'Loja' and hub['events'][-1] is links[-1]


def test_loja_grupos():
    assert [e['name'] for e in ext('Loja') if e['type'] == 'BuiltinCommonInstructions::Group'] == GRUPOS_LOJA


def test_loja_nao_cita_ids_do_catalogo():
    txt = json.dumps([e for e in ext('Loja') if e.get('type') != 'BuiltinCommonInstructions::Comment'])
    # 'dano' também é variável de todo inimigo; ids do catálogo só aparecem via upgrades./armas.
    for proibido in ('cadencia', 'recarga', 'velocidade', 'upgrades.', 'armas.'):
        assert proibido not in txt, proibido


def _eventos_compra():
    return list(anda([_grupo_loja('Compra')]))


def test_compra_desconta_e_reaplica():
    assert any(any(a['type']['value'] == 'SetNumberVariable' and a['parameters'][:2] == ['moedas_total', '-'] for a in e.get('actions') or [])
               and any(a['parameters'][:3] == ['reaplicar_upgrades', 'True', ''] for a in e.get('actions') or [])
               for e in _eventos_compra())


def test_compra_exige_moedas():
    ev = next(e for e in _eventos_compra()
              if any(a['parameters'][:2] == ['moedas_total', '-'] for a in e.get('actions') or []))
    assert any(c['type']['value'] == 'NumberVariable' and c['parameters'][:2] == ['moedas_total', '>='] for c in ev['conditions'])
    assert any(c['parameters'][:2] == ['loja_sel_nivel', '<'] for c in ev['conditions'])
    assert any(c['parameters'][:2] == ['loja_sel_bloq', '='] for c in ev['conditions'])


# ------------------------------------------------------------------ Tarefa 5: mercador inimigo secreto

def _grupo_dano():
    comb = ext('Combate')
    return next(e for e in anda(comb) if e.get('name') == 'Dano e invencibilidade')


def test_contato_ignora_calmo():
    contato = next(e for e in _grupo_dano()['events']
                   if any(c['type']['value'] == 'CollisionNP' and c['parameters'][:2] == ['pato', 'Inimigo'] for c in e.get('conditions') or []))
    assert any(c['type']['value'] == 'StringObjectVariable' and c['parameters'][:4] == ['Inimigo', 'estado', '!=', '"calmo"']
               for c in contato['conditions'])
    assert any(a['parameters'][:4] == ['pato', 'ultimo_agressor', '=', 'Inimigo.ObjectName()'] for a in contato['actions'])
    bala = next(e for e in _grupo_dano()['events']
                if any(c['parameters'][:2] == ['projetil_inimigo', 'pato'] for c in e.get('conditions') or [])
                and any(c['parameters'][:3] == ['pato', 'invencivel', 'False'] for c in e['conditions']))
    assert any(a['parameters'][:4] == ['pato', 'ultimo_agressor', '=', 'projetil_inimigo.origem'] for a in bala['actions'])


def test_hostil_fecha_loja():
    merc = list(anda([_grupo_loja('Mercador')]))
    vira = next(e for e in merc if any(a['parameters'][:4] == ['trader', 'estado', '=', '"hostil"'] for a in e.get('actions') or []))
    sub = list(anda([vira]))
    assert any(c['parameters'][:2] == ['loja_aberta', 'True'] for s in sub for c in s.get('conditions') or [])
    assert any(a['parameters'][:3] == ['loja_acao', '=', '"fechar"'] for s in sub for a in s.get('actions') or [])
    # quem fecha de fato (Abrir e fechar) destrava o pato
    fecha = next(e for e in anda([_grupo_loja('Abrir e fechar')])
                 if any(c['parameters'][:3] == ['loja_acao', '=', '"fechar"'] for c in e.get('conditions') or []))
    assert any(a['parameters'][:3] == ['pato', 'na_loja', 'False'] for a in fecha['actions'])
    assert any(a['parameters'][:2] == ['loja_aberta', 'False'] for a in fecha['actions'])


def test_multa_nao_negativa():
    morte = next(e for e in anda(ext('Jogador')) if e.get('name') == 'Morte do Pato')
    multa = [e for e in anda([morte]) if any(c['parameters'][:4] == ['pato', 'ultimo_agressor', '=', '"trader"']
                                             for c in e.get('conditions') or [])]
    assert len(multa) == 1
    acts = {a['parameters'][0] if a['type']['value'] == 'SetNumberVariable' else a['parameters'][1]: a['parameters'][-1]
            for a in multa[0]['actions']}
    assert 'trader.multa' in acts['moedas_perdidas']
    assert acts['moedas_total'].replace(' ', '').startswith('max(0,')


def test_ganchos_vazios():
    nomes = [e.get('name') for e in anda([_grupo_loja('Mercador')])]
    assert 'Ataques do trader' in nomes and 'Quando o trader morre' in nomes
    assert any(a['type']['value'] == 'SetBooleanVariable' and a['parameters'][:2] == ['trader_morto', 'True']
               for e in anda([_grupo_loja('Mercador')]) for a in e.get('actions') or [])


# ------------------------------------------------------------------ Revisão final

def test_clique_so_compra_sobre_linha():
    compra = list(anda([_grupo_loja('Compra')]))
    principal = next(e for e in compra if any(a['parameters'][:2] == ['moedas_total', '-'] for a in e.get('actions') or []))
    assert 'BuiltinCommonInstructions::Or' not in tipos(principal)
    assert any(c['parameters'][:3] == ['loja_comprar', '=', '1'] for c in principal['conditions'])
    clique = next(e for e in compra if 'MouseButtonFromTextReleased' in tipos(e))
    assert 'SourisSurObjet' in tipos(clique)
    assert any(c['parameters'][:2] == ['loja_lmb_ok', 'True'] for c in clique['conditions'])
    assert any(a['parameters'][:3] == ['loja_comprar', '=', '1'] for a in clique['actions'])
    # o botão já segurado quando a loja abre não vale: só uma pressão nova (borda) sobre uma linha libera o clique
    libera = next(e for e in compra if any(a['parameters'][:2] == ['loja_lmb_ok', 'True'] for a in e.get('actions') or []))
    assert any(c['parameters'][:2] == ['loja_lmb_antes', 'False'] for c in libera['conditions'])
    assert 'SourisSurObjet' in tipos(libera)


def test_requer_aceita_arma():
    menu = json.dumps(_grupo_loja('Menu'))
    assert 'armas[loja_req]' in menu


def test_barra_rastro_encolhe():
    barra = list(anda(ext('HUD')))
    assert any(a['type']['value'] == 'ResizableCapability::ResizableBehavior::SetWidth' and a['parameters'][0] == 'hud_boss_rastro'
               and a['parameters'][2] == '-' and 'trader.rastro_vel' in a['parameters'][3]
               for e in barra for a in e.get('actions') or [])


# ------------------------------------------------------------------ Bug: Or com condição de objeto filtrava o pato

def test_reaplicar_nao_filtra_o_pato():
    # Uma condição de objeto dentro do Or deixava o pato sem instâncias no início da cena (pato.* = 0, cooldown 0).
    _, alvo = _aplicar()
    (ou,) = alvo['conditions']
    for c in ou['subInstructions']:
        assert 'ObjectVariable' not in c['type']['value'], c
    assert any(c['type']['value'] == 'BooleanVariable' and c['parameters'][:2] == ['reaplicar_upgrades', 'True']
               for c in ou['subInstructions'])
    assert any(a['type']['value'] == 'SetBooleanVariable' and a['parameters'][:2] == ['reaplicar_upgrades', 'False']
               for a in alvo['actions'])
    compra = json.dumps(_grupo_loja('Compra'))
    assert '"reaplicar_upgrades", "True"' in compra and '"pato", "reaplicar_upgrades"' not in compra
    assert glob('reaplicar_upgrades')['value'] is False
