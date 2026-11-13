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
    assert cat['type'] == 'array' and len(cat['children']) == 5
    ids = []
    for item in cat['children']:
        f = {c['name']: c['value'] for c in item['children']}
        assert {'id', 'nome', 'descricao', 'tipo', 'nivel_max', 'preco_base', 'preco_mult', 'requer'} <= set(f)
        assert f['nivel_max'] == 3 and f['preco_base'] == 50 and f['preco_mult'] == 1.6
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
    grupo = next(e for e in ext('AplicarUpgrades') if e.get('name') == 'Aplicar upgrades')
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
    assert any(a['parameters'][:3] == ['pato', 'reaplicar_upgrades', 'False'] for a in alvo['actions'])


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
