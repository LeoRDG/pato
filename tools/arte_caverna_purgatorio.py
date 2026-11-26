"""Pinta o fundo de caverna da fase Purgatorio (assets/purgatorio/fundo/caverna.png): a subida é por dentro da
montanha, então o fundo é a caverna vista de dentro (a serra de fora fica no HubPurgatorio, tools/arte_serra_purgatorio.py).

Imagem só, arte 2x (cada pixel vira 2x2 no jogo), sem pontilhado, na camada Fundo da fase (que anda a 0.15 da câmera
do jogo), na frente de longe.png, pilares.png e nevoa.png. Três camadas de rocha, da mais longe para a mais perto:
- parede do fundo, clara e quase névoa, com terraços escavados bem apagados (os patamares do Purgatório) e frestas
  abertas para fora: nelas a imagem é transparente e aparecem a névoa, as agulhas e os fachos de luz de longe.png;
  as frestas ficam maiores subindo e, perto do cume, a parede acaba (a saída da montanha);
- paredes do poço dos dois lados, mais escuras, que se afastam subindo, com arcos de rocha atravessando (o teto de
  cada salão) e uma fresta em cada arco;
- rocha perto, a mais escura (ainda bem mais clara que o terreno jogável), só nas beiradas e nos arcos.
Toda borda de baixo de rocha ganha estalactites. A luz vem de cima à esquerda: a beira das rochas virada para ela
clareia e a outra escurece (pelo gradiente da máscara borrada), com textura de rocha lisa, e cada camada some na névoa
(128;138;128) um pouco mais quanto mais longe e quanto mais perto do cume.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_caverna_purgatorio.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/purgatorio/fundo/caverna.png')

ESCALA = 2                        # arte 2x: a instância no jogo tem o dobro do tamanho da imagem
X0, Y0 = -1664, -2752             # canto de cima à esquerda no mundo (camada Fundo), igual à t211
W, H = 1952, 1824                 # tamanho da imagem em pixels de arte (3904 x 3648 no mundo)
NEVOA = np.array([128, 138, 128], float)
SEED = 212

CENTRO_X = 200                    # x (mundo) do meio do poço
ABRE_DE, ABRE_ATE = -700, -2500   # y (mundo) onde a caverna começa a abrir e onde ela já abriu (saída perto do cume)
SAIDA_Y = -2450                   # acima disso a parede do fundo acaba (com a borda irregular)

FUNDO_COR, FUNDO_NEVOA = (96, 105, 97), 0.45        # parede do fundo
MEIO_COR, MEIO_NEVOA = (76, 84, 77), 0.18           # paredes do poço e arcos
PERTO_COR, PERTO_NEVOA = (60, 67, 60), 0.05         # rocha perto
NEVOA_SAIDA = 0.35                # névoa a mais perto da saída

FRESTA_FUNDO = (0.42, -0.30)      # limiar das frestas da parede do fundo embaixo e em cima (menor = mais aberta)
BRILHO_FRESTA = 0.22              # quanto a parede do fundo clareia em volta das frestas
TERRACO_PASSO, TERRACO_FORCA = 150, 0.06   # px de arte entre terraços na parede do fundo; força do relevo deles
# abóbadas: (y no mundo do ponto mais alto do arco, espessura e queda junto das paredes (px de arte),
#            x da fresta no mundo, largura da fresta no mundo)
ARCOS_MEIO = [(-2050, 70, 150, 450, 320), (-1150, 60, 130, -150, 240)]
ARCOS_PERTO = [(-1600, 55, 120, -520, 420)]
LUZ = 0.16                        # quanto a beira virada para a luz clareia (e a outra escurece)
TEXTURA = 0.035                   # força da textura de rocha
ESTALACTITES = (5, 16)            # espaço entre estalactites (px de arte), mínimo e máximo


def ruido2d(w, h, cx, cy, oitavas, rng):
    """ruído 2D liso (bilinear com suavização), escala cx na horizontal e cy na vertical, ~[-1, 1]."""
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for _ in range(oitavas):
        g = rng.standard_normal((h // cy + 3, w // cx + 3))
        y, x = np.arange(h) / cy, np.arange(w) / cx
        iy, ix = y.astype(int), x.astype(int)
        fy = ((1 - np.cos((y - iy) * np.pi)) / 2)[:, None]
        fx = ((1 - np.cos((x - ix) * np.pi)) / 2)[None, :]
        a = g[iy][:, ix] * (1 - fx) + g[iy][:, ix + 1] * fx
        b = g[iy + 1][:, ix] * (1 - fx) + g[iy + 1][:, ix + 1] * fx
        out += amp * (a * (1 - fy) + b * fy)
        tot += amp
        amp *= 0.5
        cx, cy = max(cx // 2, 1), max(cy // 2, 1)
    return out / tot


def ruido1d(n, comp, rng):
    return ruido2d(n, 1, comp, 1, 4, rng)[0]


def borra(a, sigma):
    """gaussiana separável com a beira repetida."""
    r = int(sigma * 3)
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    p = np.pad(a, r, mode='edge')
    out = sum(w * p[i:i + a.shape[0], :] for i, w in enumerate(k))
    out = sum(w * out[:, i:i + a.shape[1]] for i, w in enumerate(k))
    return out


def suaviza(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def arcos(lista, u, v, rng, lim_esq, lim_dir):
    """máscara das abóbadas de rocha que fecham o alto de cada salão: a parte de baixo é um arco (mais baixa junto das
    paredes, mais alta no meio) e cada uma tem uma fresta."""
    m = np.zeros(u.shape, bool)
    for y_mundo, espessura, queda, fresta_x, fresta_w in lista:
        vc = (y_mundo - Y0) / ESCALA
        meio = (lim_esq + lim_dir) / 2
        meia = np.maximum((lim_dir - lim_esq) / 2, 1)
        t = np.clip(np.abs(u - meio) / meia, 0, 1) ** 2
        baixo = vc + queda * t + 7 * ruido1d(W, 20, rng)[None, :]
        cima = vc - espessura * (0.6 + 0.4 * t) + 14 * ruido1d(W, 50, rng)[None, :]
        fx = (fresta_x - X0) / ESCALA
        torto = 18 * ruido1d(H, 40, rng)[:, None] + (v - vc) * 0.35
        fresta = np.abs(u - fx - torto) < fresta_w / ESCALA / 2 * (1 + 0.5 * np.clip((v - vc) / espessura, -1, 1))
        m |= (v >= cima) & (v <= baixo) & ~fresta
    return m


def estalactites(m, rng, maximo=40):
    """pendura estalactites (triângulos finos) em toda borda de baixo da máscara."""
    m = m.copy()
    borda = m[:-1] & ~m[1:]
    u = int(rng.integers(0, ESTALACTITES[1]))
    while u < W:
        linhas = np.nonzero(borda[:, u])[0]
        for v in linhas:
            if rng.random() < 0.75:
                comp = rng.uniform(6, maximo) * rng.uniform(0.4, 1) ** 2 + 4
                larg = rng.uniform(2, 6)
                for k in range(int(comp)):
                    hw = larg * (1 - k / comp) ** 1.3
                    a, b = int(round(u - hw)), int(round(u + hw)) + 1
                    if v + 1 + k < H and b > a:
                        m[v + 1 + k, max(a, 0):min(b, W)] = True
        u += int(rng.integers(ESTALACTITES[0], ESTALACTITES[1] + 1))
    return m


def pinta(m, cor, nevoa, ymundo, rng, extra=None):
    """cor da rocha numa máscara: luz pela beira (gradiente da máscara borrada), textura e névoa."""
    b = borra(m.astype(float), 5)
    gv, gu = np.gradient(b)
    lado = np.tanh((gu * 0.55 + gv * 0.85) * 9)          # beira virada para cima à esquerda clareia
    funda = np.clip(borra(m.astype(float), 22) - 0.5, 0, 0.5) * 2   # longe da beira, um pouco mais escuro
    textura = ruido2d(W, H, 36, 64, 4, rng)
    lum = 1 + LUZ * lado + TEXTURA * textura - 0.06 * funda
    if extra is not None:
        lum = lum + extra
    c = np.array(cor, float)[None, None, :] * lum[..., None]
    abre = suaviza((ymundo - ABRE_DE) / (ABRE_ATE - ABRE_DE))
    t = np.clip(nevoa + NEVOA_SAIDA * abre, 0, 0.95)
    return c + (NEVOA[None, None, :] - c) * t[..., None]


def main():
    rng = np.random.default_rng(SEED)
    v, u = np.mgrid[0:H, 0:W].astype(float)
    ymundo = (v + 0.5) * ESCALA + Y0
    abre = suaviza((ymundo - ABRE_DE) / (ABRE_ATE - ABRE_DE))
    cx = (CENTRO_X - X0) / ESCALA

    # parede do fundo com frestas (mais abertas subindo) e a saída no alto
    lim = FRESTA_FUNDO[0] + (FRESTA_FUNDO[1] - FRESTA_FUNDO[0]) * abre
    rf = ruido2d(W, H, 70, 260, 5, rng)      # frestas: alongadas na vertical, como rachaduras
    saida = (ymundo > SAIDA_Y + 140 * ruido1d(W, 90, rng)[None, :])
    fundo = (rf < lim) & saida
    fundo = estalactites(fundo, rng, 30)
    # terraços: patamar claro em cima, sombra embaixo, ondulando de leve
    onda = v + 10 * ruido1d(W, 120, rng)[None, :]
    fase = (onda % TERRACO_PASSO) / TERRACO_PASSO
    terraco = np.where(fase < 0.06, 1.0, 0) - np.clip(1 - np.abs(fase - 0.16) / 0.1, 0, 1)
    brilho = BRILHO_FRESTA * np.clip(1 - borra(fundo.astype(float), 14), 0, 1) ** 0.7   # luz que entra pelas frestas
    c_fundo = pinta(fundo, FUNDO_COR, FUNDO_NEVOA, ymundo, rng, TERRACO_FORCA * terraco + brilho)

    # paredes do poço: afastam-se subindo, borda irregular
    meia = 330 + 520 * abre + 40 * ruido2d(W, H, 400, 60, 4, rng)
    esq, dir_ = cx - meia - 10, cx + meia + 10
    paredes = (u < esq + 45 * ruido2d(W, H, 60, 50, 4, rng)) | (u > dir_ + 45 * ruido2d(W, H, 60, 50, 4, rng))
    meio = paredes | arcos(ARCOS_MEIO, u, v, rng, esq, dir_)
    meio = estalactites(meio, rng, 44)
    c_meio = pinta(meio, MEIO_COR, MEIO_NEVOA, ymundo, rng)

    # rocha perto: só nas beiradas e em dois arcos
    meia2 = 640 + 600 * abre
    esq2, dir2 = cx - meia2, cx + meia2
    perto = (u < esq2 + 50 * ruido2d(W, H, 70, 40, 4, rng)) | (u > dir2 + 50 * ruido2d(W, H, 70, 40, 4, rng))
    perto |= arcos(ARCOS_PERTO, u, v, rng, esq - 60, dir_ + 60)
    perto &= ymundo > ABRE_ATE + 300                     # perto da saída não há teto
    perto = estalactites(perto, rng, 56)
    c_perto = pinta(perto, PERTO_COR, PERTO_NEVOA, ymundo, rng)

    cor = np.zeros((H, W, 3))
    alfa = np.zeros((H, W))
    for m, c in ((fundo, c_fundo), (meio, c_meio), (perto, c_perto)):
        cor = np.where(m[..., None], c, cor)
        alfa = np.where(m, 1.0, alfa)
    out = np.dstack([np.clip(cor, 0, 255), alfa * 255]).round().astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(ARQ, optimize=True)
    print('caverna salva em', ARQ, out.shape)


if __name__ == '__main__':
    main()
