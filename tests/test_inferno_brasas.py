"""Inferno com ar: brasas subindo pela fase toda (inferno_brasas), seguindo a câmera (tools/t177_inferno_brasas.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class InfernoBrasas(unittest.TestCase):
    def test(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        o = m.objeto(d, 'inferno_brasas')
        self.assertEqual(o['tank'], -1)
        self.assertLess(o['particleGravityY'], 0, 'sobe')
        self.assertGreater(o['jumpForwardInTimeOnCreation'], 0)
        sc = m.cena(d, 'Inferno')
        nomes = [e.get('name') for e in sc['events']]
        self.assertGreater(nomes.index('Brasas no ar'), nomes.index('Fundo em parallax'))
        t = json.dumps(m.acha(sc['events'], 'Brasas no ar'))
        self.assertIn('"Create"}, "parameters": ["", "inferno_brasas"', t)
        self.assertIn('"inferno_brasas", "=", "inferno_brasas_z"', t)
        self.assertIn('inferno_brasas_z', {v['name'] for v in sc['variables']})


if __name__ == '__main__':
    unittest.main()
