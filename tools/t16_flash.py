"""Tarefa 16 (clarões): desenha em pixel art o clarão de cano de cada arma -> assets/flash_<arma>.png.
Cada imagem aponta para a direita e o ponto de saída é o meio da borda esquerda (x=0, y=altura/2).
Rodar:  python3 tools/t16_flash.py
"""
import math, os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# arma: (largura, altura, ângulos dos raios, comprimentos dos raios, cores externa/meio/miolo, raio do núcleo)
FLASH = {
    'pistola': (16, 13, [-55, -28, 0, 28, 55], [5, 9, 15, 9, 5], 2),
    'doze': (30, 30, [-75, -55, -35, -17, 0, 17, 35, 55, 75], [8, 12, 17, 23, 29, 23, 17, 12, 8], 3),
    'minigun': (20, 11, [-20, 0, 20], [8, 19, 8], 1),
    'lanca': (32, 32, [-80, -60, -40, -20, 0, 20, 40, 60, 80], [9, 14, 20, 26, 31, 26, 20, 14, 9], 4),
}
CORES = [(255, 110, 0, 255), (255, 190, 30, 255), (255, 245, 170, 255)]   # laranja, amarelo, quase branco


def raio(dr, cy, ang, comp, larg, cor):
    a = math.radians(ang)
    tip = (comp * math.cos(a), cy + comp * math.sin(a))
    n = (-math.sin(a), math.cos(a))
    dr.polygon([(0 + n[0] * larg, cy + n[1] * larg), tip, (0 - n[0] * larg, cy - n[1] * larg)], fill=cor)


def main():
    for nome, (w, h, angs, comps, nucleo) in FLASH.items():
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        cy = h / 2 - 0.5
        for cor, esc, larg in zip(CORES, (1, 0.68, 0.38), (2.6, 1.8, 1.0)):
            for a, c in zip(angs, comps):
                raio(dr, cy, a, c * esc, larg + nucleo * 0.3, cor)
        dr.ellipse([-nucleo, cy - nucleo, nucleo, cy + nucleo], fill=(255, 255, 255, 255))
        im.save(os.path.join(ROOT, 'assets', f'flash_{nome}.png'))


if __name__ == '__main__':
    main()
