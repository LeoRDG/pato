"""Pedestal das armas no hub (assets/hub/pedestal_arma.png): bloco de pedra escura com friso dourado e a face de
cima brilhando, onde a arma flutua. Pixel art desenhada a 1x e salva ampliada 3x (pixels nítidos, sem pontilhado).
Rodar:  python3 tools/arte_pedestal.py
"""
import os
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, 'assets', 'hub', 'pedestal_arma.png')
W, H, ESCALA = 40, 20, 3
CONTORNO, PEDRA, PEDRA_CLARA, PEDRA_ESCURA = (18, 14, 24), (52, 46, 66), (78, 70, 98), (36, 31, 46)
OURO, OURO_CLARO, BRILHO = (176, 128, 48), (232, 186, 84), (255, 236, 170)


def desenha():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # tampo (mais largo) e base
    d.rectangle((1, 2, W - 2, 6), fill=CONTORNO)
    d.rectangle((2, 3, W - 3, 5), fill=PEDRA_CLARA)
    d.line((3, 3, W - 4, 3), fill=BRILHO)              # face de cima brilhando
    d.line((2, 5, W - 3, 5), fill=OURO)                # friso dourado
    d.point((2, 4), fill=OURO_CLARO); d.point((W - 3, 4), fill=OURO_CLARO)
    # coluna
    d.rectangle((6, 7, W - 7, H - 5), fill=CONTORNO)
    d.rectangle((7, 7, W - 8, H - 6), fill=PEDRA)
    d.line((7, 7, 7, H - 6), fill=PEDRA_CLARA)         # luz do lado esquerdo
    d.line((W - 8, 7, W - 8, H - 6), fill=PEDRA_ESCURA)
    for y in (10, 13):                                 # juntas das pedras
        d.line((9, y, W - 10, y), fill=PEDRA_ESCURA)
    # pé
    d.rectangle((3, H - 5, W - 4, H - 1), fill=CONTORNO)
    d.rectangle((4, H - 4, W - 5, H - 2), fill=PEDRA)
    d.line((4, H - 4, W - 5, H - 4), fill=OURO)
    return im.resize((W * ESCALA, H * ESCALA), Image.NEAREST)


if __name__ == '__main__':
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    desenha().save(SAIDA)
    print(SAIDA)
