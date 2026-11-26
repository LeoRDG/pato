"""Agulhas de rocha pontudas no fundo do Purgatório, no lugar das colunas de topo arredondado.

As colunas de longe.png (agulhas distantes) e de pilares.png (pilares mais perto) tinham corpo cilíndrico liso e
cabeça arredondada. Aqui elas são trocadas por agulhas/estalagmites afiladas: ponta fina, silhueta recortada e
assimétrica (cada lado com seus degraus e lascas, inclinação e curva próprias, às vezes com uma agulha menor grudada
do lado), clara do lado da luz (esquerda) e escura do outro, borda macia de 1 px e o pé sumindo na névoa aos poucos.
Arte 2x (cada pixel vira 2x2), sem pontilhado, e as duas texturas continuam emendando nos dois sentidos.
- longe.png: o fundo de névoa com os fachos de luz diagonais só depende de x + y (é o mesmo em cada diagonal), então
  ele é refeito sem as colunas antigas (por diagonal, o tom da névoa) e as agulhas novas são pintadas por cima.
- longe_hub.png: o mesmo fundo, só névoa e fachos, sem agulhas (o HubPurgatorio é o lado de fora, com a serra).
- pilares.png: transparente, com as agulhas maiores e mais escuras, que somem na névoa embaixo.
Parte das imagens do git de antes desta tarefa (ORIGEM), então rodar de novo dá o mesmo resultado.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_agulhas_purgatorio.py
"""
import io, os, subprocess
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = 'assets/purgatorio/fundo/'
ORIGEM = '819f6e5'
N = 512                    # lado da textura em pixels de arte (1024 no jogo)

# agulhas de longe: (x da ponta, y da ponta, altura, meia largura no pé, inclinação, com agulha do lado)
LONGE = [(20, 10, 230, 13, 0.10, False), (58, 160, 260, 17, -0.06, True), (150, 40, 250, 15, 0.05, False),
         (215, 300, 220, 12, -0.10, False), (300, 90, 280, 18, 0.08, True), (365, 250, 200, 11, -0.04, False),
         (430, 120, 270, 16, -0.08, True), (480, 330, 230, 14, 0.12, False)]
LONGE_COR = (104, 113, 105)    # cor das agulhas distantes (perto da névoa, 128;138;128)
LONGE_FORCA = 0.75             # o quanto a agulha cobre a névoa no corpo
PILARES = [(45, 60, 400, 24, 0.07, True), (180, 300, 330, 20, -0.09, False), (330, 140, 380, 26, -0.05, True)]
PILAR_COR = (86, 94, 86)       # cor dos pilares (como antes)
LUZ = 0.10                     # quanto o lado esquerdo clareia (e o direito escurece)
SUMICO = (0.45, 1.0)           # de que fração da altura até onde o pé some na névoa
BORDA = 0.9                    # meia largura da borda macia (px de arte)


def original(nome):
    dados = subprocess.run(['git', '-C', RAIZ, 'show', f'{ORIGEM}:{PASTA}{nome}'], capture_output=True, check=True).stdout
    return np.array(Image.open(io.BytesIO(dados)).convert('RGBA')).astype(float)


def ruido1d(n, comp, rng, oitavas=3):
    out = np.zeros(n)
    amp, tot = 1.0, 0.0
    for _ in range(oitavas):
        k = rng.standard_normal(n // comp + 3)
        x = np.arange(n) / comp
        i = x.astype(int)
        f = (1 - np.cos((x - i) * np.pi)) / 2
        out += amp * (k[i] * (1 - f) + k[i + 1] * f)
        tot += amp
        amp *= 0.5
        comp = max(comp // 2, 1)
    return out / tot


def agulha(cx, ty, alt, larg, inclina, rng):
    """cobertura (0-1), luz (-1 a 1) e sumiço (0-1) de uma agulha, na textura N x N com emenda nos dois sentidos."""
    cob = np.zeros((N, N))
    luz = np.zeros((N, N))
    fade = np.zeros((N, N))
    ys = np.arange(alt)
    t = ys / alt
    w = larg * (0.04 + 0.96 * t ** 0.85)                       # ponta fina, alarga até o pé
    degrau_e = np.round(ruido1d(alt, 14, rng) * 3) / 3          # degraus e lascas de cada lado (assimétricos)
    degrau_d = np.round(ruido1d(alt, 11, rng) * 3) / 3
    we = np.maximum(w * (1 + 0.28 * degrau_e * np.clip(t * 4, 0, 1)), 0.4)
    wd = np.maximum(w * (1 + 0.28 * degrau_d * np.clip(t * 4, 0, 1)), 0.4)
    meio = cx + inclina * ys + larg * 0.3 * ruido1d(alt, 60, rng) * t
    f = np.clip((t - SUMICO[0]) / (SUMICO[1] - SUMICO[0]), 0, 1)
    some = 1 - f * f * (3 - 2 * f)
    xs = np.arange(N)
    for j in range(alt):
        y = int(ty + j) % N
        dx = (xs - meio[j] + N / 2) % N - N / 2                 # distância com a emenda horizontal
        c = np.clip((np.minimum(dx + we[j], wd[j] - dx) + BORDA) / (2 * BORDA), 0, 1)   # borda macia
        u = np.clip(dx / np.maximum(np.where(dx < 0, we[j], wd[j]), 0.5), -1, 1)
        nova = c > cob[y]
        cob[y] = np.where(nova, c, cob[y])
        luz[y] = np.where(nova, -u, luz[y])
        fade[y] = np.where(nova, some[j], fade[y])
    return cob, luz, fade


def agulhas(lista, rng):
    cob = np.zeros((N, N))
    luz = np.zeros((N, N))
    fade = np.zeros((N, N))
    for cx, ty, alt, larg, inclina, irma in lista:
        pecas = [(cx, ty, alt, larg, inclina)]
        if irma:                                                 # agulha menor grudada do lado
            lado = rng.choice([-1, 1])
            pecas.append((cx + lado * larg * 0.9, ty + alt * 0.35, int(alt * 0.55), larg * 0.6, inclina + lado * 0.08))
        for p in pecas:
            c, l, fd = agulha(*p, rng)
            m = c * fd > cob * fade
            cob = np.where(m, c, cob)
            luz = np.where(m, l, luz)
            fade = np.where(m, fd, fade)
    return cob, luz, fade


def salva(arte, nome):
    out = np.repeat(np.repeat(np.clip(arte, 0, 255).round().astype(np.uint8), 2, 0), 2, 1)
    Image.fromarray(out, 'RGBA').save(os.path.join(RAIZ, PASTA, nome), optimize=True)
    print('salvo', nome)


def main():
    rng = np.random.default_rng(213)

    # longe: névoa + fachos por diagonal (x + y), sem as colunas antigas
    a = original('longe.png')[::2, ::2]
    y, x = np.mgrid[0:N, 0:N]
    s = (x + y) % N
    fundo = np.zeros((N, N, 3))
    for k in range(3):
        canal = a[..., k]
        tom = np.array([np.percentile(canal[s == d], 85) for d in range(N)])
        fundo[..., k] = tom[s]
    opaco = np.full((N, N, 1), 255.0)
    salva(np.concatenate([fundo, opaco], -1), 'longe_hub.png')

    cob, luz, fade = agulhas(LONGE, rng)
    cor = np.array(LONGE_COR, float) * (1 + LUZ * luz)[..., None]
    t = (cob * fade * LONGE_FORCA)[..., None]
    salva(np.concatenate([fundo + (cor - fundo) * t, opaco], -1), 'longe.png')

    # pilares: transparentes, mais escuros
    cob, luz, fade = agulhas(PILARES, rng)
    cor = np.array(PILAR_COR, float) * (1 + LUZ * luz)[..., None]
    salva(np.concatenate([cor, (cob * fade * 255)[..., None]], -1), 'pilares.png')


if __name__ == '__main__':
    main()
