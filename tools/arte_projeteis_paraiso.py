"""Projéteis do Paraíso redesenhados para aparecer no céu claro (mesmo tamanho, então a colisão não muda):
- flecha.png (48 x 15, querubim): haste dourada com contorno escuro, ponta de ouro e penas brancas contornadas;
- luz.png (27 x 27, serafim e Deus): em vez da cruz, uma bola redonda que brilha: miolo branco, ouro e uma borda de
  ouro mais escuro que se destaca no azul, com brilho suave em volta.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_projeteis_paraiso.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets/inimigos/projeteis')

CONTORNO = (52, 38, 70, 255)
HASTE = (236, 190, 96, 255)
HASTE_LUZ = (255, 226, 150, 255)
PONTA = (255, 206, 64, 255)
PONTA_LUZ = (255, 246, 200, 255)
PENA = (250, 250, 255, 255)


def flecha():
    w, h = 48, 15
    a = np.zeros((h, w, 4), np.uint8)
    cy = h // 2
    a[cy - 1:cy + 1, 8:38] = HASTE                          # haste (2 px)
    a[cy - 1, 8:38] = HASTE_LUZ
    for i in range(7):                                       # ponta (triângulo para a direita)
        x = 46 - i
        a[cy - i // 2 - 1:cy + i // 2 + 1, x - 1:x + 1] = PONTA
    a[cy - 1, 40:46] = PONTA_LUZ
    for k in range(4):                                       # penas (atrás, em V)
        a[cy - 2 - k, 2 + 2 * k:8 + 2 * k] = PENA
        a[cy + 1 + k, 2 + 2 * k:8 + 2 * k] = PENA
    al = a[..., 3] > 0                                       # contorno de 1 px em volta de tudo
    viz = np.zeros_like(al)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            viz |= np.roll(np.roll(al, dy, 0), dx, 1)
    a[viz & ~al] = CONTORNO
    return a


def luz():
    n, c = 27, 13
    y, x = np.mgrid[0:n, 0:n].astype(float) - c
    r = np.hypot(x, y)
    a = np.zeros((n, n, 4))
    corpo = np.clip(9.5 - r, 0, 1)                           # disco de raio ~9, borda lisa
    brilho = np.exp(-(np.maximum(r - 8.5, 0) / 2.4) ** 2) * 0.55  # halo suave, por baixo do disco
    t = np.clip(r / 9, 0, 1)
    cor = np.zeros((n, n, 3))
    for i, (ti, ci) in enumerate(((0, (255, 255, 255)), (0.35, (255, 246, 205)), (0.7, (255, 205, 70)),
                                   (1.0, (214, 128, 30)))):
        if i == 0:
            cor[:] = ci
            prev_t, prev_c = ti, np.array(ci, float)
            continue
        m = np.clip((t - prev_t) / (ti - prev_t), 0, 1)[..., None] * (t > prev_t)[..., None]
        cor = cor * (1 - m) + np.array(ci, float) * m
        prev_t, prev_c = ti, np.array(ci, float)
    halo_cor = np.array([255, 215, 110], float)
    al = corpo + brilho * (1 - corpo)                        # disco por cima do halo
    a[..., :3] = (cor * corpo[..., None] + halo_cor * (brilho * (1 - corpo))[..., None]) / np.maximum(al, 1e-6)[..., None]
    a[..., 3] = al * 255 * (r <= 13.5)
    return a.clip(0, 255).astype(np.uint8)


def main():
    Image.fromarray(flecha(), 'RGBA').save(os.path.join(PASTA, 'flecha.png'))
    Image.fromarray(luz(), 'RGBA').save(os.path.join(PASTA, 'luz.png'))


if __name__ == '__main__':
    main()
