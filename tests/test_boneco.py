"""Boneco de teste das armas no Hub: leva dano de tudo, não ataca, não morre (volta à vida cheia)."""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def obj(nome):
    return next((o for o in JOGO['objects'] if o['name'] == nome), None)


def v(o, nome):
    return next(x['value'] for x in o['variables'] if x['name'] == nome)


HUB = next(l for l in JOGO['layouts'] if l['name'] == 'Hub')


def test_boneco_existe_e_e_alvo():
    b = obj('boneco')
    assert b and b['type'] == 'Sprite'
    grupos = {g['name'] for g in JOGO['objectsGroups'] if any(x['name'] == 'boneco' for x in g['objects'])}
    assert grupos == {'Inimigo', 'Personagem'}  # sem IA (Terrestre, CorpoACorpo...)
    assert v(b, 'estado') == 'calmo' and v(b, 'dano') == 0 and v(b, 'qtd_moedas') == 0
    assert v(b, 'max_vida') == v(b, 'vida') and v(b, 'regen_espera') > 0
    assert any(i['name'] == 'boneco' for i in HUB['instances'])


def test_boneco_volta_a_vida_cheia():
    grupo = next(e for e in HUB['events'] if e.get('name') == 'Boneco de teste')
    evs = list(anda([grupo]))
    assert any(any(c['type']['value'] == 'CompareObjectTimer' and c['parameters'][:4] == ['boneco', '"sem_dano"', '>', 'boneco.regen_espera']
                   for c in e.get('conditions') or [])
               and any(a['parameters'][:4] == ['boneco', 'vida', '=', 'boneco.max_vida'] for a in e['actions'])
               for e in evs)
    assert any(a['type']['value'] == 'ResetObjectTimer' and a['parameters'][:2] == ['boneco', '"sem_dano"']
               for e in evs for a in e.get('actions') or [])
    links = [e for e in HUB['events'] if e['type'] == 'BuiltinCommonInstructions::Link']
    assert HUB['events'][-1] is links[-1] and links[-1]['target'] == 'Loja'


def _eventos_boneco():
    return list(anda([next(e for e in HUB['events'] if e.get('name') == 'Boneco de teste')]))


def test_dps_janela_deslizante():
    evs = _eventos_boneco()
    b = obj('boneco')
    assert v(b, 'dps_janela') == 5 and v(b, 'dps_passo') > 0
    assert next(x for x in HUB['variables'] if x['name'] == 'dps_buf')['type'] == 'array'
    assert obj('boneco_dps') and obj('boneco_dps')['type'] == 'TextObject::Text'
    texto = json.dumps(evs)
    for velho in ('dps_total', 'dps_ativo', 'dps_tempo', 'dps_primeiro', 'dps_pausa', 'dps_min_tempo'):
        assert velho not in texto, velho
    # o dano de cada acerto entra no balde do instante atual
    assert any(a['parameters'][:3] == ['dps_buf[dps_idx]', '+', 'boneco.vida_vista - boneco.vida']
               for e in evs for a in e.get('actions') or [])
    # ao entrar num balde novo ele é zerado antes de receber dano (o balde de 5 s atrás sai da janela)
    zera = next(e for e in evs if any(a['parameters'][:2] == ['dps_buf[dps_idx]', '='] for a in e.get('actions') or []))
    assert any(c['parameters'][:2] == ['dps_idx', '!='] or c['parameters'][1:3] == ['!=', 'dps_idx_ant'] or 'dps_idx_ant' in json.dumps(c)
               for c in zera['conditions'])
    # soma dos baldes dividida pela janela
    assert any('dps_buf[dps_i]' in a['parameters'][-1] for e in evs for a in e.get('actions') or [])
    assert any(a['parameters'][-1] == '"DPS " + ToString(round(dps_soma / boneco.dps_janela))'
               for e in evs for a in e.get('actions') or [])


def test_so_dps_e_vida_alta():
    texto = json.dumps(_eventos_boneco())
    assert 'total' not in texto
    assert v(obj('boneco'), 'max_vida') == v(obj('boneco'), 'vida') == 100000
