"""A lente do buraco negro só no fundo: na camada do jogo (com luz 3D) ela entortava os sprites, o pato e o feixe e
ficava com cara de defeito (tools/t165_lente_so_no_fundo.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class LenteSoNoFundo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.cena = m.cena(cls.d, 'Paraiso')
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')

    def efeitos(self, camada):
        (l,) = [x for x in self.cena['layers'] if x['name'] == camada]
        return {e['name']: e['effectType'] for e in l.get('effects', [])}

    def test_camadas(self):
        self.assertEqual(self.efeitos('Fundo').get('Lente negra'), 'BulgePinch')
        self.assertNotIn('Lente negra', self.efeitos(''))

    def test_eventos_so_no_fundo(self):
        t = tx(self.deus)
        self.assertIn('"SetLayerEffectParameter"}, "parameters": ["", "\\"Fundo\\"", "\\"Lente negra\\""', t)
        self.assertNotIn('"SetLayerEffectParameter"}, "parameters": ["", "\\"\\"", "\\"Lente negra\\""', t)


if __name__ == '__main__':
    unittest.main()
