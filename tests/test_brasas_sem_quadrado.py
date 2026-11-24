"""Partícula com textura nunca fica sem textura (sem ela o GDevelop desenha quadrados), e os emissores de ambiente
não são aditivos: na camada do jogo (com luz 3D) o modo aditivo deixava o hub inteiro esbranquiçado, como se o
terreno fosse transparente (tools/t178_brasas_sem_quadrado.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class BrasasSemQuadrado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_quad_tem_textura(self):
        sem = [o['name'] for o in self.d['objects'] if o['type'] == 'ParticleSystem::ParticleEmitter'
               and o['rendererType'] == 'Quad' and not o.get('textureParticleName')]
        self.assertEqual(sem, [])

    def test_ambiente_nao_aditivo(self):
        for n in ('hub_brasas', 'hub_luzes', 'inferno_brasas'):
            self.assertFalse(m.objeto(self.d, n)['additive'], n)

    def test_brasas_do_inferno_pequenas(self):
        self.assertLessEqual(m.objeto(self.d, 'inferno_brasas')['particleSize1'], 12)


if __name__ == '__main__':
    unittest.main()
