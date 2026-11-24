"""Lente do buraco negro mais forte: com 0.5 quase toda a curva ficava escondida atrás do disco preto
(tools/t168_lente_mais_forte.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class LenteMaisForte(unittest.TestCase):
    def test_valores(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        v = {x['name']: x['value'] for x in m.objeto(d, 'deus')['variables']}
        self.assertGreaterEqual(v['juizo_lente_negra'], 0.9)
        self.assertGreaterEqual(v['juizo_lente_raio'], 300)


if __name__ == '__main__':
    unittest.main()
