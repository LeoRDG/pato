"""Arte das estrelas do céu (objeto estrela): um ponto redondo e claro com brilho suave em volta, degradê liso
(sem pontilhado e sem cruz). O brilho maior vem do bloom da camada Fundo (t167).
Gerador de arte (roda uma vez; não mexe no jogo.json):  python3 tools/arte_estrelas.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(RAIZ, 'assets/paraiso/deus')


def estrela(tam, nucleo, halo):
    """tam: lado em pixels; nucleo: raio do miolo claro; halo: quanto o brilho se espalha (desvio da gaussiana)."""
    yy, xx = np.mgrid[0:tam, 0:tam].astype(float)
    c = (tam - 1) / 2
    d = np.hypot(xx - c, yy - c)
    miolo = np.clip(1 - (d - nucleo), 0, 1)
    brilho = np.exp(-(d / halo) ** 2 / 2) * 0.55
    a = np.clip(np.maximum(miolo, brilho), 0, 1)
    a[d > c] = 0
    rgb = np.ones((tam, tam, 3)) * 255
    rgb[..., 2] = 255 - 20 * (1 - miolo)  # o halo puxa um pouco para o amarelo claro; a cor final vem do ChangeColor
    return Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), 'RGBA')


if __name__ == '__main__':
    estrela(17, 1.8, 3.0).save(os.path.join(P, 'estrela_p.png'))
    estrela(27, 2.6, 4.8).save(os.path.join(P, 'estrela_g.png'))
    print('ok')
