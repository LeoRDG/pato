"""O céu do Paraíso não tem mais brilhos em cruz: viraram brilhos redondos e suaves (tools/arte_brilhos_ceu.py)."""
import os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import arte_brilhos_ceu as b


class BrilhosCeu(unittest.TestCase):
    def test_sem_cruz(self):
        a = np.array(Image.open(b.ARQ).convert('RGBA')).astype(float)
        cruzes = [p for p in b.pecas_soltas(a[..., 3] > 0) if b.e_cruz(a, p)]
        self.assertEqual(cruzes, [])
        self.assertGreater(len(np.unique(a[..., 3])), 20, 'brilhos com degradê')


if __name__ == '__main__':
    unittest.main()
