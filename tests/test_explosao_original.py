"""A explosão volta a ser como era antes das texturas suaves (t169/t170/t172): renderizador Point
(tools/t179_explosao_original.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

ORIGINAL = {'explosao_fogo': (40, 100, 30), 'explosao_fumaca': (46, 80, 220), 'explosao_faiscas': (6, 100, 40)}


class ExplosaoOriginal(unittest.TestCase):
    def test(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        for n, (p1, s1, s2) in ORIGINAL.items():
            o = m.objeto(d, n)
            self.assertEqual((o['rendererType'], o['textureParticleName'], o['rendererParam1'], o['rendererParam2']),
                             ('Point', '', p1, 1), n)
            self.assertEqual((o['particleSize1'], o['particleSize2']), (s1, s2), n)


if __name__ == '__main__':
    unittest.main()
