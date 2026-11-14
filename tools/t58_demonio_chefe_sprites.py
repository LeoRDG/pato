"""Quadros do demônio chefe do inferno, recortados do pacote ~/Game/boss_demon_slime_FREE_v1.0 (individual sprites).

Os quadros originais têm 288 x 160 com o corpo centrado em x = 144. Todos são recortados na mesma caixa
(CAIXA, simétrica em volta do corpo, para o espelhamento não fazer o demônio pular de lugar e a ponta do cutelo
caber no golpe e na morte) e ampliados ESCALA vezes sem suavização.
Saída: assets/demonio_chefe/<animação>_NN.png (idle, andando, ataque, tomou_dano, morte). Não sobrescreve nada.
"""
import glob, os, re
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEM = os.path.expanduser('~/Game/boss_demon_slime_FREE_v1.0/individual sprites')
SAIDA = os.path.join(RAIZ, 'assets', 'demonio_chefe')
CAIXA = (20, 32, 268, 160)          # x0, y0, x1, y1 no quadro original (centro x = 144)
ESCALA = 3
ANIMS = {'idle': '01_demon_idle', 'andando': '02_demon_walk', 'ataque': '03_demon_cleave',
         'tomou_dano': '04_demon_take_hit', 'morte': '05_demon_death'}


def quadros(pasta):
    fs = glob.glob(os.path.join(ORIGEM, pasta, '*.png'))
    return sorted(fs, key=lambda f: int(re.findall(r'(\d+)\.png$', f)[0]))


def main():
    os.makedirs(SAIDA, exist_ok=True)
    for anim, pasta in ANIMS.items():
        fs = quadros(pasta)
        assert fs, f'sem quadros em {pasta}'
        for i, f in enumerate(fs):
            destino = os.path.join(SAIDA, f'{anim}_{i:02d}.png')
            if os.path.exists(destino):
                continue
            im = Image.open(f).convert('RGBA').crop(CAIXA)
            im.resize((im.width * ESCALA, im.height * ESCALA), Image.NEAREST).save(destino)


if __name__ == '__main__':
    main()
