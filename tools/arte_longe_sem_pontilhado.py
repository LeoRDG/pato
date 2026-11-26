"""Tira o pontilhado do fundo distante do Purgatório (assets/purgatorio/fundo/longe.png).

A imagem é opaca e o pontilhado estava na cor: borda dos fachos de luz em xadrez, agulhas de rocha sumindo na névoa
em xadrez e hachura dentro das agulhas. Onde há pontilhado (pixel da arte, que é 2x, mais claro ou mais escuro que os dois vizinhos,
repetido na janela) a cor vira a média local, então os fachos e o sumiço das agulhas viram degradês suaves;
o contorno das agulhas (degrau de um lado só) fica como estava. A imagem continua emendando nos dois sentidos.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_longe_sem_pontilhado.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/purgatorio/fundo/longe.png')
JANELA = 7        # lado da janela que mede o pontilhado (px)
PICOS = 2         # picos (pixel acima/abaixo dos dois vizinhos) na janela a partir dos quais é pontilhado
LIMIAR = 1.5      # diferença mínima de luminância para contar como pico
SIGMA = 1.5       # suavidade da média que substitui o pontilhado (px da arte)
SIGMA_MASCARA = 1.0  # transição entre a parte trocada e a que fica (px da arte)
ESCALA = 2        # a arte é 2x: cada pixel dela é um bloco 2x2 na imagem; trabalha no tamanho da arte e volta


def caixa(x, r):
    s = np.zeros_like(x)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            s += np.roll(np.roll(x, dy, 0), dx, 1)
    return s


def gauss(x, sigma):
    r = int(sigma * 3)
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    out = sum(w * np.roll(x, i - r, 0) for i, w in enumerate(k))
    return sum(w * np.roll(out, i - r, 1) for i, w in enumerate(k))


def picos(lum):
    p = np.zeros_like(lum)
    for eixo in (0, 1):
        a, b = np.roll(lum, 1, eixo), np.roll(lum, -1, eixo)
        p += ((lum - a > LIMIAR) & (lum - b > LIMIAR)) | ((a - lum > LIMIAR) & (b - lum > LIMIAR))
    return p


def pontilhado(rgb):
    return caixa(picos(rgb @ [0.3, 0.59, 0.11]), JANELA // 2) >= PICOS


def main():
    a = np.array(Image.open(ARQ).convert('RGBA')).astype(float)[::ESCALA, ::ESCALA]
    rgb = a[..., :3]
    mascara = np.clip(gauss(pontilhado(rgb).astype(float), SIGMA_MASCARA) * 1.5, 0, 1)[..., None]
    liso = np.stack([gauss(rgb[..., c], SIGMA) for c in range(3)], -1)
    novo = rgb * (1 - mascara) + liso * mascara
    out = np.dstack([novo, a[..., 3]]).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(out.repeat(ESCALA, 0).repeat(ESCALA, 1), 'RGBA').save(ARQ)
    print('pixels trocados:', int((mascara[..., 0] > 0.01).sum()), 'sobrou:', int(pontilhado(out[..., :3].astype(float)).sum()))


if __name__ == '__main__':
    main()
