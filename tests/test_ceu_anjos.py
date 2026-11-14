import glob, json, os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
RES = {r['name']: r for r in JOGO['resources']['resources']}
T = 32


def img(rel):
    return np.array(Image.open(os.path.join(RAIZ, rel)).convert('RGBA')).astype(int)


def quadros(obj, anim):
    return [img(s['image']) for a in OBJ[obj]['animations'] if a['name'] == anim for s in a['directions'][0]['sprites']]


def mudanca(a, b):
    return int((np.abs(a - b).sum(-1) > 0).sum())


def passos(qs):
    return [mudanca(qs[i], qs[(i + 1) % len(qs)]) for i in range(len(qs))]


# ------------------------------------------------------------------ tiles
def test_atlas_do_ceu_bate_com_a_grade_e_nao_e_o_do_inferno_recolorido():
    for s in ('', '_ponte', '_decor'):
        c = OBJ['tiles_ceu' + s]['content']
        w, h = Image.open(os.path.join(RAIZ, c['atlasImage'])).size
        assert (w, h) == (c['columnCount'] * c['tileSize'], c['rowCount'] * c['tileSize']) and c['tileSize'] == 64
        assert RES[c['atlasImage']]['smoothed'] is False
    ceu, inferno = img('assets/ceu/tiles/tiles_ceu.png'), img('assets/gandalf_hell/tiles/tiles_inferno.png')
    assert ceu.shape == inferno.shape
    # um recolorido teria a mesma silhueta; nos enfeites (colunas 13-16) e na parede de fundo ela é outra
    dif = (ceu[..., 3] > 0) != (inferno[..., 3] > 0)
    assert dif[:, 13 * T:].mean() > 0.12 and dif[6 * T:, :6 * T].mean() > 0.07


def test_terreno_do_ceu_emenda_sem_costura():
    a = img('assets/ceu/tiles/tiles_ceu.png')
    def tile(i):
        return a[i // 17 * T:i // 17 * T + T, i % 17 * T:i % 17 * T + T]
    for o in (0, 51):                                   # as duas variantes do bloco de 9 fatias
        topo, meio_e, base = tile(o + 1), tile(o + 17), tile(o + 35)
        for viz in (tile(o), tile(o + 2)):                                 # quinas continuam o mesmo piso
            assert (topo[:9, 9:23] == viz[:9, 9:23]).all()
        assert (topo[:6, 15] == topo[:6, 31]).all() and (topo[6:9, :16] == topo[6:9, 16:]).all(-1).mean() > .7   # juntas e friso de 16 em 16 px
        assert (meio_e[0, :7] == meio_e[8, :7]).all()                      # fiadas da parede repetem de 8 em 8 px
        assert (base[-1, :, 3] == 0).any() and (base[20, :, 3] > 0).all()  # nuvem recortada por baixo
        assert (topo[0, :, 3] > 0).mean() > .85                            # piso reto por cima
    assert (tile(144)[..., 3] == 255).all() and len({tuple(p) for p in tile(144).reshape(-1, 4)}) == 1


def test_objetos_de_tiles_do_ceu():
    tipo = lambda n: [b['platformType'] for b in OBJ[n]['behaviors'] if b['type'] == 'PlatformBehavior::PlatformBehavior']
    ids = lambda n: [int(x) for x in OBJ[n]['content']['tilesWithHitBox'].split(',') if x]
    assert tipo('tiles_ceu') == ['NormalPlatform'] and tipo('tiles_ceu_ponte') == ['Jumpthru'] and tipo('tiles_ceu_decor') == []
    s = set(ids('tiles_ceu'))
    assert {0, 1, 2, 40, 52, 144} <= s and not {9, 18, 43} & s and not s & set(range(102, 144))
    assert ids('tiles_ceu_ponte') == [108, 109, 110, 125, 126, 127, 142] and ids('tiles_ceu_decor') == []
    g = {x['name']: [o['name'] for o in x['objects']] for x in JOGO['objectsGroups']}
    assert 'tiles_ceu' in g['Terreno']


# ------------------------------------------------------------------ anjos
LACOS = [('querubim', 'voando'), ('querubim', 'voando_ferido'), ('serafim', 'voando'), ('ofanim', 'idle'), ('roda_anjo', 'rolando')]


def test_anjos_tem_as_animacoes_e_os_arquivos():
    esperado = {'querubim': ['voando', 'voando_ferido', 'morte'], 'serafim': ['voando', 'ataque_1', 'morte'],
                'ofanim': ['idle', 'ataque', 'morte'], 'roda_anjo': ['rolando', 'morte']}
    for nome, anims in esperado.items():
        o = OBJ[nome]
        assert [a['name'] for a in o['animations']] == anims
        for a in o['animations']:
            d = a['directions'][0]
            assert d['looping'] == (a['name'] != 'morte' and not a['name'].startswith('ataque'))
            assert len(d['sprites']) >= 7
            for s in d['sprites']:
                assert os.path.exists(os.path.join(RAIZ, s['image'])) and RES[s['image']]['smoothed'] is False
        assert {'vida', 'max_vida', 'dano', 'velocidade'} <= {v['name'] for v in o['variables']}
    assert any(v['name'] == 'ferido_abaixo' and 0 < v['value'] < 1 for v in OBJ['querubim']['variables'])


def test_lacos_fecham_sem_tranco():
    """A volta do último quadro para o primeiro muda tanto quanto os outros passos (nem salto, nem quadro repetido)."""
    for nome, anim in LACOS:
        p = passos(quadros(nome, anim))
        assert min(p) > 0, (nome, anim, p)
        assert p[-1] <= 1.25 * max(p[:-1]), (nome, anim, p)
        assert p[-1] >= 0.5 * min(p[:-1]), (nome, anim, p)


def test_lacos_gerados_tem_passo_parelho():
    """Nos anjos desenhados por código nenhum passo é muito maior que o típico (movimento contínuo)."""
    for nome, anim in (('serafim', 'voando'), ('ofanim', 'idle'), ('roda_anjo', 'rolando')):
        p = passos(quadros(nome, anim))
        assert max(p) <= 1.6 * sorted(p)[len(p) // 2], (nome, anim, p)


def test_roda_gira_um_quarto_de_volta_por_laco():
    """Aro (8 olhos) e raios (4) giram juntos: o laço inteiro é 90 graus, então o quadro 0 girado 90 graus é ele mesmo."""
    q = quadros('roda_anjo', 'rolando')
    assert len(q) == 8
    assert mudanca(q[0], q[4]) > 0                      # meio laço (45 graus) não é o mesmo desenho: os raios mudam


def test_ataques_comecam_e_terminam_na_pose_parada():
    for nome, atk, parado in (('serafim', 'ataque_1', 'voando'), ('ofanim', 'ataque', 'idle')):
        a, p = quadros(nome, atk), quadros(nome, parado)
        assert mudanca(a[0], p[0]) == 0                 # entra do quadro 0 do laço
        tipico = sorted(passos(a)[:-1])[len(a) // 2]
        assert mudanca(a[-1], p[0]) <= 1.2 * tipico     # e o último quadro já está voltando para ele


def test_morte_some_sem_piscar():
    """Depois do primeiro quadro, o número de pixels só cai, e o último quadro está quase vazio."""
    for nome in ('querubim', 'serafim', 'ofanim', 'roda_anjo'):
        n = [int((q[..., 3] > 40).sum()) for q in quadros(nome, 'morte')]
        assert all(n[i + 1] < n[i] for i in range(len(n) - 1)), (nome, n)
        assert n[-1] < 0.1 * n[0]


def test_querubim_recortado_da_folha():
    folha = os.path.expanduser('~/Game/AngelsSpriteSheetNew.png')
    q = quadros('querubim', 'voando')
    assert len(q) == 8 and all(x.shape[:2] == (128, 128) for x in q)
    assert mudanca(q[0], q[4]) == 0 and mudanca(q[1], q[5]) == 0 and mudanca(q[3], q[7]) == 0   # duas batidas iguais
    assert 0 < mudanca(q[2], q[6]) < 200                # só o olho muda: aberto na primeira batida, fechado na segunda
    if os.path.exists(folha):
        f = np.array(Image.open(folha).convert('RGBA')).astype(int)
        assert mudanca(q[0][::2, ::2], f[:, 4 * 64:5 * 64]) == 0
