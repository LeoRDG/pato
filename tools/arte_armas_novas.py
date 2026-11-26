"""Sprites das armas novas M4, MP5 e sniper (pasta ~/Game, mesmo pacote bitVillain "Modern Pixel Guns II" da pistola,
da minigun e do lança-granadas): recorta gun_012 (M4), gun_014 (MP5) e gun_015 (sniper) em assets/arma_<nome>.png
e faz o ícone do HUD (silhueta branca em 150x56, escala inteira) em assets/hud/arma_<nome>.png, como a t16.
Imprime o bocal_f de cada uma (altura do cano em fração da altura, a partir do centro).
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_armas_novas.py [pasta das armas]
"""
import os, sys
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Game')
ARMAS = {'m4': 'gun_012', 'mp5': 'gun_014', 'sniper': 'gun_015'}


def main():
    for nome, arq in ARMAS.items():
        im = Image.open(os.path.join(SRC, arq + '.png')).convert('RGBA')
        im = im.crop(im.getbbox())
        im.save(os.path.join(RAIZ, f'assets/arma_{nome}.png'))
        a = np.array(im)[..., 3] > 0
        cols = np.where(a.any(0))[0]
        linhas = np.where(a[:, cols[-3:]].any(1))[0]          # cano: as linhas opacas nas últimas colunas
        bocal_f = ((linhas.min() + linhas.max() + 1) / 2 - im.height / 2) / im.height
        k = max(1, min(140 // im.width, 50 // im.height))
        m = im.split()[3].point(lambda v: 255 if v > 127 else 0).resize((im.width * k, im.height * k), Image.NEAREST)
        ic = Image.new('RGBA', (150, 56), (255, 255, 255, 0))
        branco = Image.new('RGBA', m.size, (255, 255, 255, 255))
        ic.paste(branco, ((150 - m.width) // 2, (56 - m.height) // 2), m)
        ic.save(os.path.join(RAIZ, f'assets/hud/arma_{nome}.png'))
        print(nome, im.size, 'bocal_f', round(bocal_f, 3))


if __name__ == '__main__':
    main()
