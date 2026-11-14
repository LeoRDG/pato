"""Laser da mira só com o upgrade "laser"; o alvo fica escondido (mas continua sendo o ponto de mira do tiro)."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
MIRA = next(e for e in next(x for x in JOGO['externalEvents'] if x['name'] == 'Jogador')['events'] if e.get('name') == 'Mira')


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def glob(nome):
    return next(x for x in JOGO['variables'] if x['name'] == nome)


def test_upgrade_no_catalogo():
    itens = [{c['name']: c['value'] for c in i['children']} for i in glob('loja_catalogo')['children']]
    assert [(i['tipo'], i['nivel_max']) for i in itens if i['id'] == 'laser'] == [('upgrade', 1)]
    assert any(c['name'] == 'laser' for c in glob('upgrades')['children'])


def test_laser_so_com_upgrade():
    desenha = [e for e in anda(MIRA['events']) if any(a['type']['value'] == 'PrimitiveDrawing::LineV2' for a in e.get('actions') or [])]
    assert len(desenha) == 1
    assert any(c['parameters'][:3] == ['GlobalVariable(upgrades.laser)', '>', '0'] for c in desenha[0]['conditions'])


def test_alvo_escondido():
    assert any(a['type']['value'] == 'Hide' and a['parameters'][0] == 'alvo' and not e.get('conditions')
               for e in MIRA['events'] for a in e.get('actions') or [])
