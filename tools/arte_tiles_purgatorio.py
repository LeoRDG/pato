"""Repinta o atlas do terreno do Purgatório (assets/purgatorio/tiles/tiles_purgatorio_2x.png) para combinar com os
fundos pintados (caverna da fase, serra do hub): rocha cinza-esverdeada, luz de cima à esquerda, sem pontilhado.

Parte do atlas atual e só troca pixels: a grade (17 x 9 tiles de 64 px), a transparência de cada pixel (e portanto a
forma e a colisão das peças) e o layout dos tilemaps não mudam. Trabalha na arte 1x (cada pixel do atlas é um bloco
2x2) e devolve em 2x.
- Pontilhado: onde um pixel é xadrez entre duas cores (os quatro vizinhos iguais entre si e diferentes dele), vira a
  média das duas, então as transições ficam lisas.
- Cor: os cinzas amarelados/marrons da rocha e da crosta viram cinza-esverdeado (mesma luminosidade, matiz da rocha
  dos fundos); o musgo e a grama perdem um pouco do amarelo; as raízes marrons ficam, um pouco mais apagadas.
- Miolo (o quase preto liso): ganha textura de rocha discreta e lisa, em camadas, que só depende da posição dentro
  do tile, então emenda em qualquer vizinho (miolo 144, bordas, quinas e cantos internos da t208 casam entre si).
  Continua bem mais escuro que qualquer coisa do fundo.
- Luz: em cada tile, a beira da peça virada para cima/esquerda (grama, parede esquerda) clareia e a virada para
  baixo/direita (teto, estalactites, parede direita) escurece, pelo gradiente da opacidade borrada dentro do tile.
Gerador de arte (não mexe no jogo.json); parte da versão do atlas que está no git antes desta tarefa, então rodar de
novo dá o mesmo resultado:  python3 tools/arte_tiles_purgatorio.py
"""
import io, os, subprocess
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = 'assets/purgatorio/tiles/tiles_purgatorio_2x.png'
ARQ = os.path.join(RAIZ, REL)
ORIGEM = '9e2bf35'     # commit com o atlas original (antes desta repintura)
T = 32                 # tile em pixels de arte

MIOLO = (42, 43, 37)   # cor lisa do miolo no atlas original
TOM_ROCHA = np.array([0.94, 1.04, 0.97])   # matiz cinza-esverdeado dos fundos (r, g, b relativos à luminosidade)
ROCHA_TINGE = 0.85     # quanto os cinzas/marrons de rocha vão para esse matiz
MUSGO_DESSATURA = 0.18 # quanto o musgo/grama perde de saturação (e de amarelo)
RAIZ_DESSATURA = 0.30  # quanto as raízes marrons perdem de saturação
SATURADO = 0.22        # acima desta saturação a cor é musgo ou raiz, não rocha

MIOLO_LUM = 40.0       # luminosidade média do miolo (o fundo mais escuro fica acima de ~55)
MIOLO_VAR = 2.5        # variação da textura do miolo (em níveis de 0-255)
MIOLO_CAMADAS = 1.2    # força das camadas de rocha (horizontais, onduladas)
LUZ = 0.16             # quanto a beira virada para a luz clareia (e a outra escurece)
LUZ_SIGMA = 2.0        # alcance da luz a partir da beira (px de arte)


def atlas_original():
    dados = subprocess.run(['git', '-C', RAIZ, 'show', f'{ORIGEM}:{REL}'], capture_output=True, check=True).stdout
    return np.array(Image.open(io.BytesIO(dados)).convert('RGBA'))


def sem_xadrez(rgb, alfa):
    """troca o pixel de xadrez pela média com o vizinho: é xadrez quando os dois vizinhos de um eixo são iguais entre
    si e diferentes dele, algum vizinho na diagonal é igual a ele e ele não é uma linha fina (no outro eixo algum
    vizinho também difere). Linhas de 1 px (raízes, cipós) ficam."""
    c = rgb.astype(float)
    out = c.copy()
    q = np.pad(rgb.astype(int), ((1, 1), (1, 1), (0, 0)), mode='edge')
    qa = np.pad(alfa, 1, mode='edge')
    v = lambda dy, dx: q[1 + dy:q.shape[0] - 1 + dy, 1 + dx:q.shape[1] - 1 + dx]
    va = lambda dy, dx: qa[1 + dy:qa.shape[0] - 1 + dy, 1 + dx:qa.shape[1] - 1 + dx]
    ig = lambda x, y: (x == y).all(-1)
    e, d, s_, b = v(0, -1), v(0, 1), v(-1, 0), v(1, 0)
    diag = ig(v(-1, -1), rgb) | ig(v(-1, 1), rgb) | ig(v(1, -1), rgb) | ig(v(1, 1), rgb)
    opaco = (alfa > 0) & (va(0, -1) > 0) & (va(0, 1) > 0) & (va(-1, 0) > 0) & (va(1, 0) > 0)
    hor = ig(e, d) & ~ig(e, rgb) & (~ig(s_, rgb) | ~ig(b, rgb))
    ver = ig(s_, b) & ~ig(s_, rgb) & (~ig(e, rgb) | ~ig(d, rgb))
    m = (hor | ver) & diag & opaco
    # a faixa de xadrez (os marcados e os vizinhos deles) vira a média 3x3 dos pixels da própria faixa
    faixa = m.copy()
    faixa[:, 1:] |= m[:, :-1]
    faixa[:, :-1] |= m[:, 1:]
    faixa[1:] |= m[:-1]
    faixa[:-1] |= m[1:]
    faixa &= alfa > 0
    soma = np.zeros_like(c)
    n = np.zeros(alfa.shape)
    fp = np.pad(faixa, 1)
    cp = np.pad(c, ((1, 1), (1, 1), (0, 0)))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            f = fp[1 + dy:fp.shape[0] - 1 + dy, 1 + dx:fp.shape[1] - 1 + dx]
            soma += cp[1 + dy:cp.shape[0] - 1 + dy, 1 + dx:cp.shape[1] - 1 + dx] * f[..., None]
            n += f
    out[faixa] = soma[faixa] / n[faixa][:, None]
    return out


def recolore(c):
    lum = c @ np.array([0.299, 0.587, 0.114])
    mx, mn = c.max(-1), c.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    verde = c[..., 1] >= c[..., 0]
    out = c.copy()
    rocha = sat < SATURADO
    alvo = lum[..., None] * TOM_ROCHA / (TOM_ROCHA @ np.array([0.299, 0.587, 0.114]))
    out[rocha] = c[rocha] + (alvo[rocha] - c[rocha]) * ROCHA_TINGE
    musgo = ~rocha & verde
    cinza = lum[..., None]
    out[musgo] = c[musgo] + (cinza[musgo] * np.array([0.97, 1.03, 0.98]) - c[musgo]) * MUSGO_DESSATURA
    out[musgo, 2] += 4                                  # menos amarelo
    raiz = ~rocha & ~verde
    out[raiz] = c[raiz] + (cinza[raiz] - c[raiz]) * RAIZ_DESSATURA
    return out


def textura_miolo():
    """textura periódica no tile (emenda em qualquer vizinho): manchas lisas + camadas de rocha onduladas."""
    rng = np.random.default_rng(208)
    y, x = np.mgrid[0:T, 0:T] / T * 2 * np.pi
    tx = np.zeros((T, T))
    for _ in range(9):
        fx, fy = rng.integers(-3, 4), rng.integers(1, 4)
        tx += rng.uniform(0.4, 1) * np.cos(fx * x + fy * y + rng.uniform(0, 2 * np.pi))
    tx /= np.abs(tx).max()
    onda = 0.35 * np.sin(x + 1.3) + 0.2 * np.sin(2 * x + 0.4)
    camadas = np.clip(np.cos(2 * (y + onda)) * 1.6, -1, 1)          # duas camadas por tile
    return MIOLO_VAR * tx + MIOLO_CAMADAS * camadas


def borra(a, sigma):
    r = int(sigma * 3)
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    p = np.pad(a, r, mode='edge')
    o = sum(w * p[i:i + a.shape[0], :] for i, w in enumerate(k))
    return sum(w * o[:, i:i + a.shape[1]] for i, w in enumerate(k))


def luz(alfa):
    """luz pela beira, calculada tile a tile (a beira do tile repete, então o que continua no vizinho não muda)."""
    h, w = alfa.shape
    out = np.zeros((h, w))
    for ty in range(0, h, T):
        for tx in range(0, w, T):
            a = (alfa[ty:ty + T, tx:tx + T] > 0).astype(float)
            if a.min() == a.max():
                continue
            b = borra(a, LUZ_SIGMA)
            gv, gu = np.gradient(b)
            out[ty:ty + T, tx:tx + T] = np.tanh((gu * 0.55 + gv * 0.85) * 6)
    return out


def main():
    a2 = atlas_original()
    a = a2[::2, ::2]
    assert (np.repeat(np.repeat(a, 2, 0), 2, 1) == a2).all(), 'o atlas não é arte 2x'
    rgb, alfa = a[..., :3], a[..., 3]
    miolo = (rgb == MIOLO).all(-1) & (alfa > 0)

    c = sem_xadrez(rgb, alfa)
    miolo &= (c == rgb).all(-1)                      # a faixa de xadrez que virou média não é miolo
    c = recolore(c)
    h, w = alfa.shape
    tex = np.tile(textura_miolo(), (h // T, w // T))
    lum_miolo = MIOLO_LUM + tex
    c[miolo] = lum_miolo[miolo][:, None] * TOM_ROCHA
    c = c * (1 + LUZ * luz(alfa))[..., None]

    out = np.dstack([np.clip(c, 0, 255).round(), alfa]).astype(np.uint8)
    out[alfa == 0] = 0
    out = np.repeat(np.repeat(out, 2, 0), 2, 1)
    Image.fromarray(out, 'RGBA').save(ARQ, optimize=True)
    print('atlas salvo em', ARQ, out.shape)


if __name__ == '__main__':
    main()
