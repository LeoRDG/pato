"""Partículas com textura no tamanho certo: o runtime desenha a textura no tamanho dela (128 px) e ignora
rendererParam, então o tamanho pensado nas t169/t170 vira o particleSize (%) (tools/t172_tamanho_particulas.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

# nome: (lado pensado na t169/t170, particleSize1 e 2 de antes)
# a explosão (explosao_fogo/fumaca/faiscas) voltou ao visual antigo na t179
ANTES = {'fogo_lanca': (57, 100, 220),
         'demonio_fumaca': (36, 100, 150), 'poeira': (26, 40, 80), 'pulso_brilho': (18, 110, 30),
         'investida_rastro': (14, 120, 30), 'estrela_rastro': (10, 100, 20), 'conv_luz': (10, 70, 130),
         'escudo_faisca': (10, 100, 30)}


class TamanhoParticulas(unittest.TestCase):
    def test_tamanhos(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        for n, (lado, s1, s2) in ANTES.items():
            o = m.objeto(d, n)
            self.assertEqual((o['rendererParam1'], o['rendererParam2']), (128, 128), n)
            self.assertAlmostEqual(o['particleSize1'], s1 * lado / 128, delta=1, msg=n)
            self.assertAlmostEqual(o['particleSize2'], s2 * lado / 128, delta=1, msg=n)


if __name__ == '__main__':
    unittest.main()
