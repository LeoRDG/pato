"""Fogo, fumaça e poeira com textura suave (antes eram discos de borda dura e a explosão parecia um monte de bolhas)
(tools/arte_particulas.py, tools/t169_fogo_e_fumaca.py)."""
import json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

FOGO = ('fogo_lanca',)  # a explosão voltou ao visual antigo na t179 (test_explosao_original)
FUMACA = ('demonio_fumaca', 'poeira')


class FogoEFumaca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_texturas_suaves(self):
        for n in ('particula_luz', 'particula_fumaca'):
            a = np.array(Image.open(os.path.join(RAIZ, f'assets/particulas/{n}.png')).convert('RGBA'))[:, :, 3]
            self.assertGreater(len(np.unique(a)), 40, n)
            self.assertEqual(a[0, 0], 0, n)

    def test_emissores(self):
        recursos = {r['name']: r['file'] for r in self.d['resources']['resources']}
        for nomes, tex in ((FOGO, 'particula_luz'), (FUMACA, 'particula_fumaca')):
            for n in nomes:
                o = m.objeto(self.d, n)
                self.assertNotIn(o['rendererType'], ('Point', 'Line'), n)
                self.assertEqual(recursos[o['textureParticleName']], f'assets/particulas/{tex}.png', n)
                self.assertEqual(o['rendererParam1'], o['rendererParam2'], n)


if __name__ == '__main__':
    unittest.main()
