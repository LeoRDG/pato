"""Sem o "Made with GDevelop" no canto do jogo (tools/t182_sem_marca_dagua.py)."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SemMarcaDagua(unittest.TestCase):
    def test(self):
        p = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))['properties']
        self.assertFalse(p['watermark']['showWatermark'])
        self.assertFalse(p['loadingScreen']['showGDevelopSplash'])


if __name__ == '__main__':
    unittest.main()
