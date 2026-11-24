"""Os pilares do fundo do Purgatório somem na névoa em degradê, sem pontilhado nem hachura
(tools/arte_pilares_sem_pontilhado.py)."""
import os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import arte_pilares_sem_pontilhado as p

RUIDO_ORIGINAL = 0.90   # p.ruido da imagem pontilhada


class PilaresSemPontilhado(unittest.TestCase):
    def test(self):
        a = np.array(Image.open(p.ARQ).convert('RGBA')).astype(float)
        self.assertGreater(len(np.unique(a[..., 3])), 50, 'opacidade em degradê')
        self.assertLess(p.ruido(a), RUIDO_ORIGINAL / 5, 'sem pontilhado')


if __name__ == '__main__':
    unittest.main()
