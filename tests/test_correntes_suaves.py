"""Correntes de luz do Paraíso com luz lisa e partículas subindo, sem degraus nem faíscas de pixel
(tools/arte_corrente_suave.py, tools/t181_correntes_suaves.py)."""
import json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class CorrentesSuaves(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_textura_lisa(self):
        a = np.array(Image.open(os.path.join(RAIZ, 'assets/paraiso/corrente_luz.png')).convert('RGBA')).astype(float)
        al = a[..., 3]
        # t183: a textura virou uma cor lisa (o desenho vem do KawaseBlur e do Glow; test_correntes_efeitos)
        self.assertLess(np.abs(np.diff(al, axis=1)).max(), 25, 'sem salto de um pixel para o outro')
        self.assertLess(np.abs(np.diff(al, axis=0)).max(), 25, 'sem faísca de pixel')
        self.assertLess(np.abs(al[0] - al[-1]).max(), 25, 'emenda na vertical')
        r = {x['name']: x for x in self.d['resources']['resources']}
        self.assertTrue(r['assets/paraiso/corrente_luz.png']['smoothed'])

    def test_particulas(self):
        o = m.objeto(self.d, 'corrente_faisca')
        self.assertEqual(o['textureParticleName'], 'assets/particulas/particula_luz.png')
        self.assertFalse(o['additive'], 'aditivo esbranquiça a camada do jogo (t178)')
        self.assertTrue(o['updateIfNotVisible'], 'o pé da corrente fica fora da tela e o emissor parava')
        v = {x['name'] for x in m.objeto(self.d, 'corrente_luz')['variables']}
        self.assertLessEqual({'faisca_vel', 'faisca_largura', 'faisca_angulo'}, v)
        g = tx(m.acha(m.cena(self.d, 'Paraiso')['events'], 'Correntes de luz'))
        self.assertIn('"Create"}, "parameters": ["", "corrente_faisca", "corrente_luz.CenterX()"', g)
        self.assertIn('"ParticleSystem::ParticleLifeTimeMax"}, "parameters": ["corrente_faisca", "=", "corrente_luz.Height() / corrente_luz.faisca_vel"', g)
        self.assertIn('"ParticleSystem::StartEmission"}, "parameters": ["corrente_faisca"', g)
        self.assertIn('"ParticleSystem::StopEmission"}, "parameters": ["corrente_faisca"', g)
        self.assertNotIn('ParticleSystem::SetFlow', g, 'flow 0 encerra o emissor de vez')
        self.assertIn('"SetY"}, "parameters": ["corrente_faisca", "=", "min(corrente_luz.Y() + corrente_luz.Height(), CameraCenterY(', g)


if __name__ == '__main__':
    unittest.main()
