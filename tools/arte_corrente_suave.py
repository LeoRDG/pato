"""Textura nova das correntes de luz do Paraíso (assets/paraiso/corrente_luz.png, 128 x 128): uma coluna de luz lisa,
mais forte no meio e sumindo para os lados, com faixas largas e suaves que, rolando para cima, dão o movimento.
Sem degraus e sem faíscas de pixel (as faíscas agora são partículas: t181). Emenda na vertical.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_corrente_suave.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/paraiso/corrente_luz.png')
N = 128
OPACIDADE = 175      # no meio da coluna
FAIXAS = 2           # faixas claras por altura da textura
FAIXA_FORCA = 0.22   # quanto as faixas clareiam


def main():
    y, x = np.mgrid[0:N, 0:N].astype(float)
    d = np.abs(x - (N - 1) / 2) / (N / 2)                       # 0 no meio, 1 na borda
    perfil = np.exp(-(d / 0.5) ** 2 / 2) * np.clip((1 - d) / 0.15, 0, 1)
    faixa = 1 - FAIXA_FORCA + FAIXA_FORCA * (0.5 + 0.5 * np.sin(2 * np.pi * FAIXAS * y / N
                                                                 + 0.6 * np.sin(2 * np.pi * x / N)))
    miolo = np.exp(-(d / 0.18) ** 2 / 2)
    out = np.zeros((N, N, 4))
    out[..., 0] = 255
    out[..., 1] = 228 + 27 * miolo
    out[..., 2] = 150 + 100 * miolo
    out[..., 3] = OPACIDADE * perfil * faixa
    Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').save(ARQ)


if __name__ == '__main__':
    main()
