"""Hubs com ar: brasas subindo no do Inferno, névoa e cinzas no do Purgatório, luzinhas flutuando no do Paraíso
(tools/t175_hubs_ambiente.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

POR_CENA = {'Hub': ['hub_brasas'], 'HubPurgatorio': ['purg_cinza'], 'HubParaiso': ['hub_luzes']}  # purg_nevoa saiu na t176


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class HubsAmbiente(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_emissores(self):
        for n in ('hub_brasas', 'hub_luzes'):
            o = m.objeto(self.d, n)
            self.assertEqual(o['tank'], -1, n)
            self.assertTrue(o['additive'], n)
            self.assertLess(o['particleGravityY'], 0, n + ': sobe')
            self.assertGreater(o['jumpForwardInTimeOnCreation'], 0, n)

    def test_cenas(self):
        for cena, objs in POR_CENA.items():
            sc = m.cena(self.d, cena)
            g = m.acha(sc['events'], 'Ambiente')
            nomes = [e.get('name') for e in sc['events']]
            self.assertGreater(nomes.index('Ambiente'), nomes.index('Fundo em parallax'), cena)
            v = {x['name'] for x in sc['variables']}
            for o in objs:
                self.assertIn(f'"Create"}}, "parameters": ["", "{o}"', tx(g), cena)
                self.assertIn(f'{o}_z', v, cena)


if __name__ == '__main__':
    unittest.main()
