import json, os, re
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
RES = {r['name'] for r in JOGO['resources']['resources']}
LAVA = next(x for x in JOGO['externalEvents'] if x['name'] == 'Lava')
T = 32
QUENTE = {(112, 3, 16), (145, 12, 7), (204, 44, 22), (251, 60, 35), (240, 126, 32), (229, 171, 33), (58, 3, 12), (84, 3, 12)}
PALETA_LAVA = {tuple(p[:3]) for p in np.array(Image.open(os.path.join(RAIZ, 'assets/gandalf_hell/lava/idle_00.png')).convert('RGBA')).reshape(-1, 4) if p[3]}


def variaveis(nome):
    return {v['name']: v['value'] for v in OBJ[nome]['variables']}


def tile(atlas, i, lado=T):
    return atlas[i // 17 * lado:i // 17 * lado + lado, i % 17 * lado:i % 17 * lado + lado]


def test_tiles_de_margem_puxam_a_cor_da_lava_so_do_lado_dela():
    a = np.array(Image.open(os.path.join(RAIZ, 'assets/gandalf_hell/tiles/tiles_inferno.png')).convert('RGBA'))
    assert QUENTE <= PALETA_LAVA | QUENTE and len(QUENTE & PALETA_LAVA) >= 7     # as cores quentes são as da própria lava
    quente = lambda px: np.array([[tuple(p[:3]) in QUENTE and p[3] == 255 for p in linha] for linha in px])
    for dest, orig, perto, longe in ((134, 19, np.s_[:, 22:], np.s_[:, :14]), (135, 17, np.s_[:, :10], np.s_[:, 18:]),
                                     (94, 1, np.s_[:10, :], np.s_[18:, :]), (96, 52, np.s_[:10, :], np.s_[18:, :]),
                                     (151, 40, np.s_[:10, 22:], np.s_[18:, :14]), (152, 42, np.s_[:10, :10], np.s_[18:, 18:]),
                                     (117, 2, np.s_[16:, 22:], np.s_[:, :14]), (118, 0, np.s_[16:, :10], np.s_[:, 18:])):
        t, o = tile(a, dest), tile(a, orig)
        assert ((t[..., 3] > 0) == (o[..., 3] > 0)).all()                       # mesma silhueta do tile de origem
        assert quente(t[perto]).mean() > .25 and quente(t[longe]).sum() == 0
        assert (t[longe] == o[longe]).all()                                     # longe da lava é o tile original
    for dest in (117, 118):                                                     # a beira mantém o piso de cima intacto
        assert (tile(a, dest)[:5] == tile(a, {117: 2, 118: 0}[dest])[:5]).all()
    x2 = np.array(Image.open(os.path.join(RAIZ, 'assets/gandalf_hell/tiles/tiles_inferno_2x.png')).convert('RGBA'))
    for dest in (94, 96, 117, 118, 134, 135, 151, 152):
        assert (tile(x2, dest, 64)[::2, ::2] == tile(a, dest)).all()


def test_tiles_de_margem_tem_colisao():
    c = OBJ['tiles_inferno']['content']
    ids = {int(x) for x in c['tilesWithHitBox'].split(',') if x}
    if c['tileSize'] == 64 and c['columnCount'] == 17:
        assert {94, 96, 117, 118, 134, 135, 151, 152} <= ids


def test_objetos_e_variaveis_da_lava():
    v = variaveis('lava')
    assert {'anim_vel_min', 'anim_vel_max', 'superficie_frac', 'brasa_espera_min', 'brasa_espera_max', 'brasa_espera',
            'bolha_espera_min', 'bolha_espera_max', 'bolha_espera', 'bolha_afunda'} <= set(v)
    assert 0 < v['anim_vel_min'] < v['anim_vel_max'] and 0 < v['superficie_frac'] < 1
    assert 0 < v['brasa_espera_min'] < v['brasa_espera_max'] and 0 < v['bolha_espera_min'] < v['bolha_espera_max']
    assert 'lava_brilho' not in OBJ and OBJ['lava']['effects'] == []                # sem clarão nem halo
    assert not any('brilho' in r for r in RES) and 'lava_brilho' not in json.dumps(LAVA)
    bolha = OBJ['lava_bolha']['animations'][0]['directions'][0]
    assert bolha['looping'] is False and len(bolha['sprites']) == 7
    for s in bolha['sprites']:
        assert s['image'] in RES and os.path.exists(os.path.join(RAIZ, s['image']))
    brasas = OBJ['lava_brasas']
    assert brasas['type'] == 'ParticleSystem::ParticleEmitter' and brasas['destroyWhenNoParticles'] and brasas['additive']
    # o emissor atira na direção do ângulo do objeto (leque de emitterAngleB graus): o evento aponta para cima
    assert brasas['particleGravityY'] < 0 and 0 < abs(brasas['emitterAngleB']) < 90
    assert variaveis('lava')['brasa_angulo'] == -90
    txt = json.dumps(LAVA['events'])
    assert txt.index('"Create"}, "parameters": ["", "lava_brasas"') < txt.index('"SetAngle"}, "parameters": ["lava_brasas", "=", "lava.brasa_angulo"]')


def test_bolha_cresce_e_estoura():
    q = [np.array(Image.open(os.path.join(RAIZ, s['image'])).convert('RGBA'))
         for s in OBJ['lava_bolha']['animations'][0]['directions'][0]['sprites']]
    n = [int((x[..., 3] > 0).sum()) for x in q]
    assert n[0] > 0 and n[0] < n[1] < n[2] < n[3] and n[4] < n[3] and n[6] <= n[4]
    for x in q:
        assert {tuple(p[:3]) for p in x.reshape(-1, 4) if p[3]} <= PALETA_LAVA


def test_eventos_da_lava_ligados_e_sem_numero_solto():
    cena = next(l for l in JOGO['layouts'] if l['name'] == 'Inferno')
    assert any(e['type'].endswith('::Link') and e.get('target') == 'Lava' for e in cena['events'])
    txt = json.dumps(LAVA['events'])
    for obj, var in set(re.findall(r'\b(lava)\.([a-z_]+)\b', txt)):
        assert var in variaveis(obj), (obj, var)                                # toda variável usada existe no objeto
    for nome in ('lava_brasas', 'lava_bolha'):
        assert f'"Create"}}, "parameters": ["", "{nome}"' in txt
    assert 'HasAnimationEnded' in txt and '"Delete"}, "parameters": ["lava_bolha"' in txt
    js = '\n'.join(next(e for g in LAVA['events'] if g.get('events') for s in g['events'] for e in s.get('events', [])
                        if e['type'].endswith('JsCode'))['inlineCode'])
    assert 'setAnimationFrame' in js and 'setAnimationSpeedScale' in js and 'anim_vel_min' in js and 'setBlendMode' not in js
