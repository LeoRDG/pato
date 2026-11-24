"""Bala que bate no terreno solta faíscas (impacto_bala), voltando para o lado de onde veio; antes ela só sumia
(tools/t173_impacto_bala.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class ImpactoBala(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.g = m.acha(m.acha(m.folha(cls.d, 'Combate')['events'], 'Projéteis')['events'], 'Balas no terreno')

    def test_emissor(self):
        o = m.objeto(self.d, 'impacto_bala')
        self.assertEqual(o['type'], 'ParticleSystem::ParticleEmitter')
        self.assertTrue(o['additive'])
        self.assertTrue(o['destroyWhenNoParticles'])
        self.assertGreater(o['tank'], 0)
        self.assertLess(o['particleSize1'], 20, 'faísca pequena (a textura tem 128 px)')

    def test_eventos(self):
        for bala in ('projetil', 'projetil_inimigo'):
            (e,) = [e for e in self.g['events'] if f'"CollisionNP"}}, "parameters": ["{bala}", "Terreno"' in tx(e['conditions'])]
            tipos = [a['type']['value'] for a in e['actions']]
            self.assertLess(tipos.index('Create'), tipos.index('Delete'), bala)
            a = tx(e['actions'])
            self.assertIn(f'"Create"}}, "parameters": ["", "impacto_bala", "{bala}.CenterX()", "{bala}.CenterY()"', a)
            self.assertIn(f'"impacto_bala", "=", "{bala}.Angle() + 180"', a)


if __name__ == '__main__':
    unittest.main()
