"""Tira o pontilhado dos pilares do fundo do Purgatório (assets/purgatorio/fundo/pilares.png).

Os pilares sumiam na névoa com pontilhado (pixels ligados e desligados alternando, só opacidade 0 ou 255) e tinham
pontilhado e hachura na cor. Onde há pontilhado, a opacidade vira a média local (degradê suave); a cor fica lisa
(média dos vizinhos) e a borda fica macia, como vista através da névoa. A imagem continua emendando nos dois sentidos. Rodar de novo não muda nada
(não sobra pontilhado).
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_pilares_sem_pontilhado.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/purgatorio/fundo/pilares.png')
JANELA = 9        # lado da janela que mede o pontilhado (px)
SIGMA = 3.0       # suavidade da média que substitui o pontilhado (px)
SIGMA_COR = 3.0   # a cor de dentro também tinha pontilhado/hachura: vira um tom liso (px)
SIGMA_BORDA = 2.2 # a borda fica macia, como vista através da névoa (px)
NEVOA = np.array([128, 138, 128])  # cor da névoa da cena, atrás dos pilares
TROCAS = 4        # trocas de ligado/desligado na janela a partir das quais é pontilhado


def caixa(x, r):
    """média numa janela (2r+1)^2, emendando nas bordas."""
    s = np.zeros_like(x)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            s += np.roll(np.roll(x, dy, 0), dx, 1)
    return s / (2 * r + 1) ** 2


def gauss(x, sigma):
    r = int(sigma * 3)
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    out = sum(w * np.roll(x, i - r, 0) for i, w in enumerate(k))
    return sum(w * np.roll(out, i - r, 1) for i, w in enumerate(k))


def trocas(al):
    """quantas vezes a opacidade liga/desliga perto de cada pixel."""
    t = (al != np.roll(al, 1, 1)).astype(float) + (al != np.roll(al, 1, 0))
    return caixa(t, JANELA // 2) * JANELA ** 2


def pontilhado(a):
    al = a[..., 3] >= 128
    return trocas(al) >= TROCAS


def ruido(a):
    """quanto a imagem (sobre a cor da névoa) varia de um pixel para o vizinho: pontilhado e hachura dão muito."""
    al = a[..., 3:4] / 255
    lum = ((a[..., :3] * al + NEVOA * (1 - al)) @ [0.3, 0.59, 0.11])
    return float(np.abs(lum - gauss(lum, 1.5)).mean())


def main():
    a = np.array(Image.open(ARQ).convert('RGBA')).astype(float)
    al = a[..., 3] / 255
    mascara = gauss(pontilhado(a).astype(float), SIGMA)          # onde trocar, com transição suave
    media = gauss(al, SIGMA)
    cor = np.stack([gauss(a[..., c] * al, SIGMA) for c in range(3)], -1) / np.maximum(media, 1e-6)[..., None]
    novo_al = gauss(al * (1 - mascara) + media * mascara, SIGMA_BORDA)
    m2 = gauss(al, SIGMA_COR)
    novo_rgb = np.stack([gauss(a[..., c] * al, SIGMA_COR) for c in range(3)], -1) / np.maximum(m2, 1e-6)[..., None]
    novo_rgb = np.where(m2[..., None] > 1e-3, novo_rgb, cor)
    out = np.dstack([novo_rgb, novo_al * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(ARQ)
    print('pixels trocados:', int((mascara > 0.01).sum()))


if __name__ == '__main__':
    main()
