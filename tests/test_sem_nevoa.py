"""A névoa do Purgatório (purg_nevoa) saiu: os tufos grandes nasciam já opacos e pareciam holofotes acendendo.
As cinzas ficam (tools/t176_sem_nevoa.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class SemNevoa(unittest.TestCase):
    def test(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        self.assertIsNone(m.objeto(d, 'purg_nevoa'))
        for n in ('Purgatorio', 'HubPurgatorio'):
            sc = m.cena(d, n)
            self.assertNotIn('purg_nevoa', json.dumps(sc), n)
            self.assertIn('"Create"}, "parameters": ["", "purg_cinza"', json.dumps(sc), n)


if __name__ == '__main__':
    unittest.main()
