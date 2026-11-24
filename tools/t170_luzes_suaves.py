"""Tarefa 170: as partículas de luz (pulso, rastro da investida e das estrelas, conversão, faíscas do escudo e da
explosão) usam o brilho suave particula_luz em vez de discos de borda dura. São pequenas,
então o lado é K vezes o raio antigo, um pouco mais que no fogo (t169), para não ficarem apagadas.
As explosões de luz da morte (anjo_morte_luz, deus_morte_luz) ficam com os pontos: são centenas de partículas
somando luz, e suaves elas viravam uma nuvem de fumaça branca.
As brasas da lava ficam como estão (a lava é sem brilho de propósito; test_lava).
Rodar uma vez:  python3 tools/t170_luzes_suaves.py
"""
from gd_mig import *
from t169_fogo_e_fumaca import LUZ, suaves, textura

LUZES = ('pulso_brilho', 'investida_rastro', 'estrela_rastro', 'conv_luz',
         'escudo_faisca', 'explosao_faiscas')
K = 3.5


def migra(d):
    suaves(d, [LUZ])
    for n in LUZES:
        textura(objeto(d, n), LUZ, K)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'pulso_brilho')['rendererType'] != 'Point', 't170')
