"""Projéteis do Paraíso que se veem no céu claro: a flecha tem contorno escuro e a luz é uma bola redonda que brilha,
sem a forma de cruz (tools/arte_projeteis_paraiso.py)."""
import os, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets/inimigos/projeteis')
CEU = np.array([170, 195, 230])


def img(n):
    return np.array(Image.open(os.path.join(PASTA, n + '.png')).convert('RGBA')).astype(float)


class ProjeteisParaiso(unittest.TestCase):
    def test_mesmo_tamanho(self):
        self.assertEqual(img('flecha').shape[:2], (15, 48))
        self.assertEqual(img('luz').shape[:2], (27, 27))

    def test_flecha_contrasta_com_o_ceu(self):
        a = img('flecha')
        opaco = a[..., 3] > 200
        lum = a[..., :3] @ [0.3, 0.59, 0.11]
        self.assertGreater((opaco & (lum < 90)).sum(), 40, 'contorno escuro')

    def test_luz_redonda(self):
        a = img('luz')[..., 3]
        y, x = np.mgrid[0:27, 0:27] - 13
        r = np.hypot(x, y)
        # mesma opacidade na diagonal e no eixo, à mesma distância (cruz teria muito mais no eixo)
        ang = np.degrees(np.arctan2(y, x)) % 90
        for d in (6, 9, 11):
            anel = np.abs(r - d) < 0.75
            eixo = a[anel & ((ang < 15) | (ang > 75))].mean()
            diag = a[anel & (np.abs(ang - 45) < 15)].mean()
            self.assertLess(abs(eixo - diag), 40, d)
        self.assertGreater(len(np.unique(a)), 15, 'brilho em degradê')
        self.assertEqual(a[r > 13.5].max(), 0)


if __name__ == '__main__':
    unittest.main()
