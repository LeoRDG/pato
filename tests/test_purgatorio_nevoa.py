"""Purgatório com ar: névoa lenta no fundo e cinzas caindo na frente, emissores que seguem a câmera
(tools/t171_purgatorio_nevoa.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class PurgatorioNevoa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.sc = m.cena(cls.d, 'Purgatorio')
        cls.g = m.acha(cls.sc['events'], 'Névoa e cinzas')
        cls.v = {x['name']: x['value'] for x in cls.sc['variables']}

    def test_emissores(self):
        # a névoa (purg_nevoa) saiu na t176: os tufos acendiam de repente como holofotes (test_sem_nevoa)
        c = m.objeto(self.d, 'purg_cinza')
        self.assertEqual(c['tank'], -1)
        self.assertGreater(c['particleGravityY'], 0, 'cinza cai')

    def test_eventos(self):
        t = tx(self.g)
        self.assertIn('"Create"}, "parameters": ["", "purg_cinza", "CameraCenterX(\\"\\", 0)", "CameraCenterY(\\"\\", 0)", "\\"\\""', t)
        self.assertIn('"purg_cinza", "=", "purg_cinza_z"', t)
        nomes = [e.get('name') for e in self.sc['events']]
        self.assertGreater(nomes.index('Névoa e cinzas'), nomes.index('Fundo em parallax'))
        for k in ('purg_cinza_z',):
            self.assertIn(k, self.v)


if __name__ == '__main__':
    unittest.main()
