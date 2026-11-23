"""Perfuração: cada nível do upgrade soma 1 furo (inimigo atravessado) à bala."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
PROJ = next(e for e in next(x for x in JOGO['externalEvents'] if x['name'] == 'Combate')['events'] if e.get('name') == 'Projéteis')


def glob(nome):
    return next(x for x in JOGO['variables'] if x['name'] == nome)


def test_upgrade_no_catalogo():
    itens = [{c['name']: c['value'] for c in i['children']} for i in glob('loja_catalogo')['children']]
    p = [i for i in itens if i['id'] == 'perfuracao']
    assert len(p) == 1 and p[0]['tipo'] == 'upgrade' and p[0]['nivel_max'] >= 1
    assert any(c['name'] == 'perfuracao' for c in glob('upgrades')['children'])


def test_bala_soma_o_upgrade_aos_furos_da_arma():
    nasce = next(e for e in PROJ['events'] if e.get('name') == 'Balas (alcance, queda e perfuração)')['events'][0]
    ps = [a['parameters'][:4] for a in nasce['actions']]
    base = ps.index(['projetil', 'furos', '=', 'Arma.furos'])
    assert ps.index(['projetil', 'furos', '+', 'GlobalVariable(upgrades.perfuracao)']) == base + 1
