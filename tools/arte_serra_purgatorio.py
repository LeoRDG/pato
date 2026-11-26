"""Pinta a serra ao longe do HubPurgatorio (assets/purgatorio/fundo/serra.png), na camada fundo do hub, na frente
da névoa e dos pilares e atrás do mercador e dos portais (veja tools/t211_serra_purgatorio.py).

O hub é o lado de fora da montanha (na fase Purgatorio se está dentro dela, e lá o fundo é a caverna de
tools/arte_caverna_purgatorio.py). Imagem só, arte 2x (cada pixel vira 2x2 no jogo), sem pontilhado, enquadrada
para a câmera da camada fundo do hub (que anda a 0.15 da câmera do jogo: centro x de -31 a 367, y ~123), com três
serras uma na frente da outra:
- maciço ao fundo, com o pico principal atrás dos portais; mais claro, quase névoa;
- serra do meio, um pouco mais escura, com o pico do lado do mercador;
- contrafortes na frente, logo acima do chão, mais escuros (mas bem mais claros que o terreno jogável).
Cada serra tem o cume recortado em picos (perfil fractal com seed fixa), as faces viradas para a luz (que vem de cima
à esquerda, como os fachos de longe.png) um pouco mais claras e as outras um pouco mais escuras, descendo de cada
pico e alargando; uma borda clara fina no contorno do lado da luz; textura discreta de rocha; e a parte de baixo de
cada serra some aos poucos na névoa do vale (degradê para a cor da cena, 128;138;128), o que separa uma serra da outra.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_serra_purgatorio.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/purgatorio/fundo/serra.png')

ESCALA = 2                        # arte 2x: a instância no jogo tem o dobro do tamanho da imagem
X0, Y0 = -1280, -704              # canto de cima à esquerda no mundo (camada fundo do hub), igual à t211
W, H = 1440, 720                  # tamanho da imagem em pixels de arte (2880 x 1440 no mundo)
NEVOA = np.array([128, 138, 128], float)
SEED = 211

# (cor da rocha, y do cume nas pontas (mundo), x do pico (mundo), y do pico, largura do morro, rugosidade,
#  y (mundo) onde a névoa do vale começa e onde ela cobre o máximo, quanto a névoa cobre no máximo)
SERRAS = [
    ((84, 93, 86), 40, 330, -320, 1000, 60, -160, 300, 0.85),     # maciço ao fundo, atrás dos portais
    ((70, 78, 71), 0, -650, -190, 800, 45, -10, 330, 0.75),     # serra do meio, do lado do mercador
    ((57, 63, 56), 190, 1100, 80, 700, 35, 190, 420, 0.40),       # contrafortes, logo acima do chão
]
LUZ = 0.13        # quanto a face virada para a luz clareia (e a outra escurece)
TEXTURA = 0.03    # força da textura de rocha
BORDA = 0.30      # brilho da borda do lado da luz
BORDA_PX = 2.5    # largura da borda (px de arte)


def suave(n, comp, rng):
    """ruído 1D liso: soma de oitavas interpoladas (cosseno)."""
    out = np.zeros(n)
    amp, passo = 1.0, comp
    while passo >= 2:
        k = rng.standard_normal(n // passo + 3)
        x = np.arange(n) / passo
        i = x.astype(int)
        f = (1 - np.cos((x - i) * np.pi)) / 2
        out += amp * (k[i] * (1 - f) + k[i + 1] * f)
        amp *= 0.5
        passo //= 2
    return out / 2


def ruido2d(w, h, cx, cy, oitavas, rng):
    """ruído 2D liso (bilinear com suavização), com escala cx na horizontal e cy na vertical."""
    out = np.zeros((h, w))
    amp = 1.0
    for _ in range(oitavas):
        gw, gh = w // cx + 3, h // cy + 3
        g = rng.standard_normal((gh, gw))
        y = np.arange(h) / cy
        x = np.arange(w) / cx
        iy, ix = y.astype(int), x.astype(int)
        fy = ((1 - np.cos((y - iy) * np.pi)) / 2)[:, None]
        fx = ((1 - np.cos((x - ix) * np.pi)) / 2)[None, :]
        a = g[iy][:, ix] * (1 - fx) + g[iy][:, ix + 1] * fx
        b = g[iy + 1][:, ix] * (1 - fx) + g[iy + 1][:, ix + 1] * fx
        out += amp * (a * (1 - fy) + b * fy)
        amp *= 0.5
        cx, cy = max(cx // 2, 1), max(cy // 2, 1)
    return out


def perfil(base, pico_x, pico_y, largura, rug, rng):
    """y do cume (pixels de arte) para cada coluna: um pico principal, picos menores e serrilhado."""
    xs = (np.arange(W) + 0.5) * ESCALA + X0           # x no mundo
    d = np.abs(xs - pico_x) / largura
    y = base + (pico_y - base) * np.exp(-d ** 1.3 * 2.2)  # morro principal
    y = y + rug * 2.2 * suave(W, 128, rng)              # ombros e selas
    # picos pontudos: cada um é um triângulo que sobe do perfil
    n = W // 55
    for _ in range(n):
        px = rng.uniform(0, W)
        alt = rng.uniform(0.3, 1.0) * rug
        larg = rng.uniform(18, 50)
        y = y - alt * np.clip(1 - np.abs(np.arange(W) - px) / larg, 0, None) ** 1.5
    y = y + rug * 0.18 * suave(W, 8, rng)              # serrilhado fino
    return (y - Y0) / ESCALA


def borra(v, sigma):
    """média gaussiana 1D (com a beira repetida)."""
    if sigma < 0.5:
        return v.copy()
    r = int(sigma * 3)
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    return np.convolve(np.pad(v, r, mode='edge'), k, mode='valid')


def faces(cume, prof):
    """luz das faces: abaixo do cume, a encosta segue a forma do cume cada vez mais arredondada (cada pico desce como
    uma aresta que alarga). Clara onde o cume sobe para a direita (face virada para a luz de cima à esquerda)."""
    passos = np.arange(0, 400, 8)                       # profundidade (px de arte) de cada nível
    incl = np.stack([np.gradient(borra(cume, 3 + p * 0.28)) for p in passos])
    incl = np.tanh(-incl * 1.6)
    nivel = np.clip((prof / 8).round().astype(int), 0, len(passos) - 1)
    return incl[nivel, np.arange(cume.size)[None, :]]


def main():
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    ymundo = (yy + 0.5) * ESCALA + Y0
    cor = np.zeros((H, W, 3))
    alfa = np.zeros((H, W))
    for rocha, base, pico_x, pico_y, largura, rug, nevoa_ini, nevoa_fim, nevoa_max in SERRAS:
        rocha = np.array(rocha, float)
        cume = perfil(base, pico_x, pico_y, largura, rug, rng)
        assert cume.min() > 8, 'o cume passou do topo da imagem'
        dentro = yy >= cume[None, :]
        prof = yy - cume[None, :]                       # pixels abaixo do cume

        lado = faces(cume, np.maximum(prof, 0))
        lado = lado * np.clip(1 - prof / 350, 0.35, 1)  # mais embaixo a forma vai se perdendo

        textura = ruido2d(W, H, 48, 96, 4, rng)        # ravinas: um pouco alongado na vertical
        textura = textura / (np.abs(textura).max() + 1e-9)

        lum = 1 + LUZ * lado + TEXTURA * textura
        c = rocha[None, None, :] * lum[..., None]

        # borda clara de 1 px no contorno, mais forte onde o cume sobe para a direita (virado para a luz)
        sobe = np.clip(np.tanh(-np.gradient(borra(cume, 1.0)) * 1.5) + 0.25, 0, 1)
        borda = np.clip(1 - prof / BORDA_PX, 0, 1) * (prof >= 0) * sobe[None, :]
        c = c + (NEVOA[None, None, :] * 1.15 - c) * (BORDA * borda)[..., None]

        # névoa do vale: some na cor da cena de cima para baixo
        t = np.clip((ymundo - nevoa_ini) / (nevoa_fim - nevoa_ini), 0, 1)
        t = t * t * (3 - 2 * t) * nevoa_max
        c = c + (NEVOA[None, None, :] - c) * t[..., None]

        cor = np.where(dentro[..., None], c, cor)
        alfa = np.where(dentro, 1.0, alfa)

    # o que fica atrás das serras é transparente (aparece o céu/névoa das outras camadas);
    # névoa forte vira transparência, para emendar com os fundos de trás sem degrau
    out = np.dstack([np.clip(cor, 0, 255), alfa * 255]).round().astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(ARQ, optimize=True)
    print('serra salva em', ARQ, out.shape)


if __name__ == '__main__':
    main()
