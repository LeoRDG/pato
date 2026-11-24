"""Partículas de luz com brilho suave (particula_luz) em vez de discos de borda dura
(tools/t170_luzes_suaves.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

LUZES = ('pulso_brilho', 'investida_rastro', 'estrela_rastro', 'conv_luz',
         'escudo_faisca', 'explosao_faiscas')


class LuzesSuaves(unittest.TestCase):
    def test_emissores(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        for n in LUZES:
            o = m.objeto(d, n)
            self.assertEqual(o['textureParticleName'], 'assets/particulas/particula_luz.png', n)
            self.assertNotIn(o['rendererType'], ('Point', 'Line'), n)
            self.assertTrue(o['additive'], n)
        self.assertEqual(m.objeto(d, 'lava_brasas')['rendererType'], 'Point', 'a lava fica sem brilho (test_lava)')
        for n in ('anjo_morte_luz', 'deus_morte_luz'):
            self.assertEqual(m.objeto(d, n)['rendererType'], 'Point', n + ': suaves e densas viravam fumaça branca')


if __name__ == '__main__':
    unittest.main()
