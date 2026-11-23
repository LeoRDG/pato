import json, math, os, re
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
RES = {r['name'] for r in JOGO['resources']['resources']}
EXT = next(x for x in JOGO['externalEvents'] if x['name'] == 'Plataformas')
P = 'plataforma_movel'


def anda(evs):
    for e in evs:
        yield e
        yield from anda(e.get('events') or [])


def variaveis():
    return {v['name']: v['value'] for v in OBJ[P]['variables']}


def test_objetos_da_plataforma_movel():
    o = OBJ[P]
    assert [b['platformType'] for b in o['behaviors'] if b['type'] == 'PlatformBehavior::PlatformBehavior'] == ['Jumpthru']
    v = variaveis()
    assert v['velocidade'] > 0 and v['espera'] >= 0 and v['sentido'] == 1 and v['fase'] == 0
    assert set(v) == {'ini_x', 'ini_y', 'fim_x', 'fim_y', 'velocidade', 'espera', 'fase', 'sentido', 'espera_pato', 'pisar_folga', 'sincronia'}
    assert 'plataforma_movel_fim' not in OBJ and not any('plataforma_movel/fim' in r for r in RES)      # uma peça só
    d = o['animations'][0]['directions'][0]
    assert d['looping'] and len(d['sprites']) == 6
    for s in d['sprites']:
        assert s['image'] in RES and os.path.exists(os.path.join(RAIZ, s['image']))
        im = Image.open(os.path.join(RAIZ, s['image']))
        m = s['customCollisionMask'][0]
        assert im.size == (192, 60) and max(p['y'] for p in m) < 30 and min(p['x'] for p in m) >= 0     # colide só na laje


def test_brasa_pulsa_em_ciclo_fechado_e_o_piso_nao_muda():
    q = [np.array(Image.open(os.path.join(RAIZ, s['image'])).convert('RGBA')).astype(int)
         for s in OBJ[P]['animations'][0]['directions'][0]['sprites']]
    passo = [int((np.abs(q[i] - q[(i + 1) % 6]).sum(-1) > 0).sum()) for i in range(6)]
    assert min(passo) > 0 and passo[-1] <= 1.5 * max(passo[:-1])
    for x in q[1:]:
        assert (x[:4] == q[0][:4]).all() and (x[:10] != q[0][:10]).any(-1).mean() < .02 and ((x[..., 3] > 0) == (q[0][..., 3] > 0)).all()


def test_eventos_ligados_e_so_com_variaveis():
    cena = next(l for l in JOGO['layouts'] if l['name'] == 'Inferno')
    assert any(e['type'].endswith('::Link') and e.get('target') == 'Plataformas' for e in cena['events'])
    txt = json.dumps(EXT['events'])
    for var in set(re.findall(r'\bplataforma_movel\.([a-z_]+)\b', txt)):
        assert var in variaveis(), var
    assert 'plataforma_movel_fim' not in txt and 'PickNearest' not in txt
    # par em 0, 0 = onde foi colocada (começo e fim)
    for a, b in (('ini_x', 'ini_y'), ('fim_x', 'fim_y')):
        assert any([c['parameters'][:4] for c in e.get('conditions', [])] == [[P, a, '=', '0'], [P, b, '=', '0']]
                   and [x['parameters'] for x in e['actions']] == [[P, a, '=', P + '.X()'], [P, b, '=', P + '.Y()']] for e in anda(EXT['events']))


def test_vai_e_volta_entre_comeco_e_fim():
    """Simula os eventos de movimento com as variáveis do objeto: toca as duas pontas, espera nelas e não passa delas."""
    v = variaveis()
    ini, fim = (100.0, 500.0), (700.0, 260.0)
    percurso = math.dist(ini, fim)
    fase, sentido, parada, dt = 0.0, 1, 0.0, 1 / 60
    xs, pontas, maior_passo = [], [], 0.0
    ant = ini
    for _ in range(int(60 * (4 * percurso / v['velocidade'] + 6 * v['espera'] + 2))):
        parada += dt
        if parada > v['espera']:
            fase += sentido * v['velocidade'] * dt / max(1, percurso)
        if fase >= 1 and sentido > 0:
            fase, sentido, parada = 1.0, -1, 0.0
            pontas.append('fim')
        if fase <= 0 and sentido < 0:
            fase, sentido, parada = 0.0, 1, 0.0
            pontas.append('ini')
        s = (1 - math.cos(fase * 3.14159265)) / 2
        pos = (ini[0] + (fim[0] - ini[0]) * s, ini[1] + (fim[1] - ini[1]) * s)
        maior_passo = max(maior_passo, math.dist(pos, ant))
        ant = pos
        xs.append(pos[0])
    assert pontas[:4] == ['fim', 'ini', 'fim', 'ini']
    assert min(xs) >= ini[0] - 1e-6 and max(xs) <= fim[0] + 1e-6
    assert abs(max(xs) - fim[0]) < 0.01 and abs(xs[-1] - ini[0]) < percurso
    assert maior_passo <= v['velocidade'] * dt * math.pi / 2 + 1e-6      # sem tranco: o pico da suavização é pi/2 da média
    txt = json.dumps(EXT['events'])
    assert '(1 - cos(plataforma_movel.fase * 3.14159265)) / 2' in txt and 'plataforma_movel.velocidade * TimeDelta() / max(1, sqrt(pow(plataforma_movel.fim_x - plataforma_movel.ini_x, 2) + pow(plataforma_movel.fim_y - plataforma_movel.ini_y, 2)))' in txt
