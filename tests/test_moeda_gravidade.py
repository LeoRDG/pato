import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
MOEDA = next(o for o in JOGO['objects'] if o['name'] == 'moeda')


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def eventos():
    for fonte in JOGO['layouts'] + JOGO['externalEvents']:
        yield from anda(fonte['events'])


def usa(e, chave, tipo, *inicio):
    return any(i['type']['value'] == tipo and i['parameters'][:len(inicio)] == list(inicio) for i in e.get(chave) or [])


def test_moeda_tem_gravidade_por_padrao():
    v = next(v for v in MOEDA['variables'] if v['name'] == 'tem_gravidade')
    assert v['type'] == 'boolean' and v['value'] is True          # as moedas dos inimigos continuam caindo


def test_so_cai_e_anda_quem_tem_gravidade():
    fisica = [e for e in eventos() if usa(e, 'actions', 'SetNumberObjectVariable', 'moeda', 'vy')
              and any('moeda.gravidade' in a['parameters'][3] for a in e['actions'] if a['parameters'][:2] == ['moeda', 'vy'])]
    assert len(fisica) == 1
    e = fisica[0]
    assert usa(e, 'conditions', 'BooleanObjectVariable', 'moeda', 'tem_gravidade', 'True')
    assert usa(e, 'conditions', 'BooleanObjectVariable', 'moeda', 'parada', 'False')
    # todo movimento por velocidade (vx, vy) está nesse mesmo evento: sem gravidade a moeda não sai do lugar
    for outro in eventos():
        if outro is not e:
            for a in outro.get('actions') or []:
                if a['type']['value'] in ('SetX', 'SetY') and a['parameters'][0] == 'moeda':
                    assert 'moeda.vx' not in a['parameters'][2] and 'moeda.vy' not in a['parameters'][2]


def test_ima_e_coleta_nao_dependem_da_gravidade():
    for e in eventos():
        if usa(e, 'conditions', 'Distance', 'moeda', 'pato') or usa(e, 'conditions', 'CollisionNP', 'moeda', 'pato'):
            assert not usa(e, 'conditions', 'BooleanObjectVariable', 'moeda', 'tem_gravidade')
