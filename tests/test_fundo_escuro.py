import json, os, re
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
OBJ = {o['name']: o for o in JOGO['objects']}
CENA = next(l for l in JOGO['layouts'] if l['name'] == 'Inferno')
VARS = {v['name']: v['value'] for v in CENA['variables']}
EXT = next(x for x in JOGO['externalEvents'] if x['name'] == 'FundoEscuro')
TXT = json.dumps(EXT['events'])
CAMADAS = ('ceu', 'fundo', 'meio', 'frente')


def test_camadas_escuras_no_tamanho_das_normais():
    for n in CAMADAS:
        o, normal = OBJ[f'bg_inferno_noite_{n}'], OBJ[f'bg_inferno_{n}']
        assert o['type'] == 'TiledSpriteObject::TiledSprite' and (o['width'], o['height']) == (normal['width'], normal['height'])
        im = Image.open(os.path.join(RAIZ, o['texture'])).convert('RGBA')
        assert im.size == Image.open(os.path.join(RAIZ, normal['texture'])).size == (3072, 1080)
        orig = Image.open(os.path.join(RAIZ, f'assets/gandalf_hell/fundo_escuro/{n}.png')).convert('RGBA')
        assert im.crop((0, 1080 - 1038, 3072, 1080)).resize((1024, 346), Image.NEAREST).tobytes() == orig.tobytes()
        assert [v['value'] for v in o['variables'] if v['name'] == 'parallax'] and 0 < o['variables'][0]['value'] < 1
    ceu = Image.open(os.path.join(RAIZ, OBJ['bg_inferno_noite_ceu']['texture'])).convert('RGBA')
    assert ceu.getextrema()[3] == (255, 255)                        # o céu escuro cobre tudo: com mistura 1 nada do normal aparece
    assert (VARS['fundo_noite_cor_r'], VARS['fundo_noite_cor_g'], VARS['fundo_noite_cor_b']) == ceu.getpixel((0, 0))[:3]
    # os do Hub continuam como eram
    assert OBJ['bg_inferno_escuro_ceu']['texture'].endswith('fundo_escuro/ceu.png')


def test_variaveis_da_troca():
    assert VARS['fundo_troca_y_alto'] < VARS['fundo_troca_y_baixo'] and VARS['fundo_troca_suave'] > 0 and VARS['fundo_mistura'] == 0
    assert (VARS['fundo_cor_r'], VARS['fundo_cor_g'], VARS['fundo_cor_b']) == (CENA['r'], CENA['v'], CENA['b'])
    for nome in set(re.findall(r'\bfundo_[a-z_]*[a-z]\b(?!_)', TXT)):
        assert nome in VARS, nome                                   # toda variável usada nos eventos existe na cena


def test_eventos_ligados_e_camadas_por_cima():
    assert any(e['type'].endswith('::Link') and e.get('target') == 'FundoEscuro' for e in CENA['events'])
    for k, n in enumerate(CAMADAS):
        e = f'bg_inferno_noite_{n}'
        assert f'["", "{e}", "bg_inferno_{n}.X()", "bg_inferno_{n}.Y()", "\\"Fundo\\""]' in TXT
        assert f'["{e}", "=", "bg_inferno_frente.ZOrder() + {k + 1}"]' in TXT
        assert f'["{e}", "Opacity", "=", "255 * fundo_mistura"]' in TXT
        assert f'["{e}", "=", "CameraCenterX() * {e}.parallax"]' in TXT
    assert 'SceneBackground' in TXT


def test_mistura_vale_nos_dois_sentidos():
    """Simula os eventos: subindo chega a 1, descendo volta a 0, sem salto entre quadros."""
    baixo, alto, suave = VARS['fundo_troca_y_baixo'], VARS['fundo_troca_y_alto'], VARS['fundo_troca_suave']
    assert 'clamp((fundo_troca_y_baixo - pato.CenterY()) / max(1, fundo_troca_y_baixo - fundo_troca_y_alto), 0, 1)' in TXT
    assert '- fundo_mistura) * min(1, fundo_troca_suave * TimeDelta())' in TXT
    alvo = lambda y: max(0.0, min(1.0, (baixo - y) / max(1, baixo - alto)))
    assert alvo(baixo + 500) == 0 and alvo(alto - 500) == 1 and 0 < alvo((baixo + alto) / 2) < 1
    m, dt, maior = 0.0, 1 / 60, 0.0
    caminho = [baixo + 300 - 250 * i * dt for i in range(int((baixo - alto + 900) / 250 / dt))]     # sobe a 250 px/s
    for ys, fim in ((caminho, 1.0), (caminho[::-1], 0.0)):
        for y in ys:
            ant = m
            m += (alvo(y) - m) * min(1, suave * dt)
            maior = max(maior, abs(m - ant))
            assert 0 <= m <= 1
        assert abs(m - fim) < 0.02
    assert maior < 0.01                                             # menos de 1% por quadro: troca gradual
