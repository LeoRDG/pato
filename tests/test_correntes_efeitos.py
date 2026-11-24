"""Correntes de luz feitas com efeitos e partículas do GDevelop: a textura é só uma cor lisa, a forma vem do
desfoque (KawaseBlur) e do brilho (Glow), e o corpo da luz é um fluxo de partículas grandes e suaves subindo
(corrente_nevoa), além das faíscas (tools/t183_correntes_efeitos.py)."""
import json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class CorrentesEfeitos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_textura_lisa(self):
        a = np.array(Image.open(os.path.join(RAIZ, 'assets/paraiso/corrente_luz.png')).convert('RGBA'))
        self.assertEqual(len(np.unique(a.reshape(-1, 4), axis=0)), 1, 'uma cor só: o desenho vem dos efeitos')

    def test_efeitos(self):
        ef = {e['effectType']: e for e in m.objeto(self.d, 'corrente_luz')['effects']}
        self.assertGreater(ef['KawaseBlur']['doubleParameters']['blur'], 0)
        self.assertGreater(ef['Glow']['doubleParameters']['outerStrength'], 0)

    def test_fluxo_de_luz(self):
        o = m.objeto(self.d, 'corrente_nevoa')
        self.assertTrue(o['updateIfNotVisible'])
        self.assertFalse(o['additive'])
        self.assertGreater(o['particleSize1'], 50, 'bolhas grandes e suaves')
        g = tx(m.acha(m.cena(self.d, 'Paraiso')['events'], 'Correntes de luz'))
        self.assertIn('"Create"}, "parameters": ["", "corrente_nevoa", "corrente_luz.CenterX()"', g)
        self.assertIn('"ParticleSystem::StartEmission"}, "parameters": ["corrente_nevoa"', g)
        self.assertIn('"ParticleSystem::StopEmission"}, "parameters": ["corrente_nevoa"', g)
        self.assertIn('"SetY"}, "parameters": ["corrente_nevoa", "=", "min(corrente_luz.Y() + corrente_luz.Height(), CameraCenterY(', g)


if __name__ == '__main__':
    unittest.main()
