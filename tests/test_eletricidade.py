"""Eletricidade: raios entre as balas do jogador no ar, com dano em quem encostar; upgrade na loja."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
COMB = next(x for x in JOGO['externalEvents'] if x['name'] == 'Combate')['events']


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def obj(nome):
    return next(o for o in JOGO['objects'] if o['name'] == nome)


def glob(nome):
    return next(x for x in JOGO['variables'] if x['name'] == nome)


def grupo():
    return next(e for e in COMB if e.get('name') == 'Eletricidade')


def test_upgrade_no_catalogo_e_variaveis():
    itens = [{c['name']: c['value'] for c in i['children']} for i in glob('loja_catalogo')['children']]
    assert [i['tipo'] for i in itens if i['id'] == 'eletricidade'] == ['upgrade']
    assert any(c['name'] == 'eletricidade' for c in glob('upgrades')['children'])
    pv = {x['name']: x['value'] for x in obj('pato')['variables']}
    for k in ('eletro_alcance', 'eletro_dano', 'eletro_intervalo', 'eletro_largura', 'eletro_espessura', 'eletro_tremor', 'eletro_segmentos'):
        assert pv[k] > 0, k
    assert obj('eletro_raio')['type'] == 'PrimitiveDrawing::Drawer' and obj('eletro_raio')['absoluteCoordinates']


def test_variaveis_usadas_existem():
    texto = json.dumps(grupo())
    import re
    usadas = set(re.findall(r'\beletro_[a-z0-9]+\b', texto)) - {'eletro_raio'}
    globais = {x['name'] for x in JOGO['variables']}
    pato = {x['name'] for x in obj('pato')['variables']}
    falta = {n for n in usadas if n not in globais and n not in pato}
    assert not falta, falta


def test_liga_com_a_bala_anterior_mais_proxima():
    evs = list(anda(grupo()['events']))
    por_bala = next(e for e in evs if e.get('type') == 'BuiltinCommonInstructions::ForEach' and e.get('object') == 'projetil')
    tudo = json.dumps(por_bala)
    liga = next(e for e in anda(por_bala['events']) if any(c['type']['value'] == 'PickNearest' for c in e.get('conditions') or []))
    tipos = [c['type']['value'] for c in liga['conditions']]
    assert tipos[0] == 'AjoutObjConcern' and tipos[-1] == 'PickNearest'  # repega todas antes de escolher a mais próxima
    assert any(c['parameters'][:3] == ['projetil', 'serie', '<'] for c in liga['conditions'])  # cada par uma vez só
    assert '"PrimitiveDrawing::LineV2"' in tudo and 'pato.eletro_alcance' in tudo


def test_dano_por_intervalo_em_quem_encosta():
    tudo = json.dumps(grupo())
    assert 'pato.eletro_intervalo' in tudo and 'pato.eletro_largura' in tudo
    dano = [a for e in anda(grupo()['events']) for a in e.get('actions') or [] if a['parameters'][:3] == ['Inimigo', 'vida', '-']]
    assert len(dano) == 1 and 'GlobalVariable(upgrades.eletricidade)' in dano[0]['parameters'][3]
    # só com o upgrade comprado
    assert any(c['parameters'][:3] == ['GlobalVariable(upgrades.eletricidade)', '>', '0'] for e in grupo()['events'] for c in e.get('conditions') or [])
