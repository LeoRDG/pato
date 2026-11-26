"""Tira o resto da hachura de dentro dos pilares do fundo do Purgatório (assets/purgatorio/fundo/pilares.png).

Depois de tools/arte_pilares_sem_pontilhado.py ainda sobrava, dentro dos pilares, a hachura diagonal borrada
(listras claras e escuras de poucos tons). Só a cor muda: vira a média ponderada pela opacidade numa vizinhança
maior que o espaçamento da hachura, então o tom do pilar fica liso e o escurecer/clarear de cima para baixo continua.
No sumiço na névoa, a opacidade ainda tinha manchas do pontilhado antigo: onde ela é parcial vira uma média
maior (degradê liso); onde o pilar é sólido e na borda dele a opacidade fica como estava. A imagem continua emendando nos dois sentidos.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_pilares_sem_hachura.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/purgatorio/fundo/pilares.png')
SIGMA_COR = 7.0   # maior que o espaçamento da hachura (px)
SIGMA_SUMICO = 6.0  # suavidade da opacidade onde o pilar some na névoa (px)
SOLIDO = 0.9      # opacidade média acima da qual é o corpo sólido do pilar (não mexe)


def gauss(x, sigma):
    r = int(sigma * 3)
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    k /= k.sum()
    out = sum(w * np.roll(x, i - r, 0) for i, w in enumerate(k))
    return sum(w * np.roll(out, i - r, 1) for i, w in enumerate(k))


def main():
    a = np.array(Image.open(ARQ).convert('RGBA')).astype(float)
    al = a[..., 3] / 255
    m = gauss(al, SIGMA_COR)
    rgb = np.stack([gauss(a[..., c] * al, SIGMA_COR) for c in range(3)], -1) / np.maximum(m, 1e-6)[..., None]
    rgb = np.where(m[..., None] > 1e-4, rgb, a[..., :3])
    liso = gauss(al, SIGMA_SUMICO)
    # parcial = some na névoa (opacidade média entre 0 e SOLIDO, longe da borda nítida do corpo)
    peso = gauss(((liso > 0.02) & (liso < SOLIDO)).astype(float) * (gauss(al, 2) < SOLIDO), 2)
    novo_al = al * (1 - peso) + liso * peso
    out = np.dstack([rgb, novo_al * 255]).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(ARQ)


if __name__ == '__main__':
    main()
