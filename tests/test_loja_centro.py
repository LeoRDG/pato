"""Loja (tools/t188_loja_centro.py): o E do mercador funciona com o pato no chão (distância na horizontal e altura
dos pés, não de centro a centro: o mercador é bem mais alto que o pato) e o painel fica no meio da tela."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class LojaCentro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.loja = json.dumps(m.folha(cls.d, 'Loja')['events'], ensure_ascii=False)

    def test_e_funciona_no_chao(self):
        self.assertNotIn('"Distance"}, "parameters": ["trader", "pato"', self.loja)
        self.assertEqual(self.loja.count('abs(trader.CenterX() - pato.CenterX())'), 2)
        self.assertEqual(self.loja.count('abs(trader.Y() + trader.Height() - pato.Y() - pato.Height())'), 2)

    def test_painel_no_meio_da_tela(self):
        self.assertNotIn('+ loja_x', self.loja)
        self.assertNotIn('+ loja_y', self.loja)
        self.assertIn('CameraWidth(\\"HUD\\")', self.loja)
        self.assertIn('CameraHeight(\\"HUD\\")', self.loja)
        for h in ('Hub', 'HubPurgatorio', 'HubParaiso'):
            nomes = {v['name'] for v in m.cena(self.d, h)['variables']}
            self.assertIn('loja_desc_alt', nomes, h)
            self.assertNotIn('loja_x', nomes, h)
            self.assertNotIn('loja_y', nomes, h)


if __name__ == '__main__':
    unittest.main()
