import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(ROOT, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}


def arma(nome):
    o = OBJ[nome]
    b = [b for b in o['behaviors'] if b['type'] == 'FireBullet::FireBullet'][0]
    v = {x['name']: x['value'] for x in o['variables']}
    return b, v


def dps(nome):
    """Dano por segundo com recarga, acertando todas as balas, sem queda de distância."""
    b, v = arma(nome)
    tiros = b['ShotsPerReload']
    tempo = (tiros - 1) * b['FireCooldown'] + b['ReloadDuration']
    return tiros * b['BulletQuantity'] * v['dano'] / tempo


def test_orcamento_de_dano_parecido():
    valores = {n: dps(n) for n in ('pistola', 'doze', 'minigun')}
    assert all(75 <= x <= 100 for x in valores.values()), valores


def test_reserva_de_municao_parecida():
    total = {}
    for n in ('pistola', 'doze', 'minigun'):
        b, v = arma(n)
        total[n] = b['MaxAmmo'] * b['BulletQuantity'] * v['dano']
    assert max(total.values()) / min(total.values()) < 1.2, total


def test_recarga_e_cooldown_base_batem_com_o_comportamento():
    for n in ('pistola', 'doze', 'minigun'):
        b, v = arma(n)
        assert v['cooldown_base'] == b['FireCooldown'] and v['recarga_base'] == b['ReloadDuration']


def test_bala_nasce_com_os_valores_da_arma():
    txt = json.dumps(JOGO['externalEvents'], ensure_ascii=False)
    for k in ('Arma.dano', 'Arma.alcance', 'Arma.queda_min', 'Arma.furos', 'Arma.repulsao'):
        assert k in txt
    assert 'projetil.dano * projetil.fator * RandomFloatInRange(0.85, 1.15)' in txt
    assert '(projetil.dano + Random(38))' not in txt


def test_inimigos_guardam_serie_da_bala():
    grupo = [g for g in JOGO['objectsGroups'] if g['name'] == 'Inimigo'][0]
    assert all(any(v['name'] == 'bala_serie' for v in OBJ[m['name']]['variables']) for m in grupo['objects'])


def test_armas_liberadas():
    armas = [v for v in JOGO['variables'] if v['name'] == 'armas'][0]
    assert all(f['value'] for f in armas['children'])
