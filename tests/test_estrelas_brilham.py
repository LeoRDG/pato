"""Estrelas brilhando: ponto redondo com brilho suave em volta (degradê liso, sem pontilhado e sem cruz), numa camada
só delas (Estrelas, acima do Fundo) com bloom e a lente do buraco negro (tools/arte_estrelas.py,
tools/t167_estrelas_brilham.py)."""
import json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class EstrelasBrilham(unittest.TestCase):
    def test_imagens_redondas_e_suaves(self):
        for n in ('estrela_p', 'estrela_g'):
            a = np.array(Image.open(os.path.join(RAIZ, f'assets/paraiso/deus/{n}.png')).convert('RGBA'))[:, :, 3].astype(int)
            h, w = a.shape
            self.assertGreaterEqual(w, 12, n)
            self.assertGreater(len(np.unique(a)), 8, n + ': degradê liso')
            # redonda: na diagonal o brilho cai igual à reta (uma cruz teria a diagonal bem mais fraca)
            c, r = w // 2, w // 4
            reta, diag = a[c, c + r], a[c + int(r / 1.414), c + int(r / 1.414)]
            self.assertLess(abs(reta - diag), 40, n)
            self.assertEqual(a[0, 0], 0)

    def test_camada_das_estrelas(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        camadas = m.cena(d, 'Paraiso')['layers']
        nomes = [x['name'] for x in camadas]
        self.assertEqual(nomes.index('Estrelas'), nomes.index('Fundo') + 1)
        ef = {e['name']: e['effectType'] for e in camadas[nomes.index('Estrelas')]['effects']}
        self.assertEqual(ef, {'Brilho das estrelas': 'AdvancedBloom', 'Lente negra': 'BulgePinch'})
        self.assertNotIn('Brilho das estrelas', {e['name'] for e in camadas[nomes.index('Fundo')]['effects']},
                         'no fundo o bloom borrava as nuvens')
        deus = json.dumps(m.acha(m.folha(d, 'InimigosParaiso')['events'], 'Deus'), ensure_ascii=False)
        self.assertIn('"Create"}, "parameters": ["", "estrela", "0", "0", "\\"Estrelas\\""', deus)
        self.assertIn('CameraCenterX(\\"Estrelas\\", 0) + estrela.x_', deus)
        self.assertIn('"SetLayerEffectParameter"}, "parameters": ["", "\\"Estrelas\\"", "\\"Lente negra\\"", "\\"strength\\""', deus)


if __name__ == '__main__':
    unittest.main()
