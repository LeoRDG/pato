"""Brasas azuis no alto do Inferno, como o fundo (que fica azul subindo: fundo_mistura), e no hub
(tools/t180_brasas_azuis.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class BrasasAzuis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_hub_azul(self):
        o = m.objeto(self.d, 'hub_brasas')
        for k in ('1', '2'):
            self.assertGreater(o['particleBlue' + k], o['particleRed' + k])
            self.assertEqual(o['particleColor' + k], f"{o['particleRed' + k]};{o['particleGreen' + k]};{o['particleBlue' + k]}")

    def test_inferno_mistura(self):
        sc = m.cena(self.d, 'Inferno')
        v = {x['name']: x['value'] for x in sc['variables']}
        t = json.dumps(m.acha(sc['events'], 'Brasas no ar'))
        for k in ('1', '2'):
            self.assertIn(f'"ParticleSystem::ParticleColor{k}"}}, "parameters": ["inferno_brasas"', t)
            for c in 'rgb':
                self.assertIn(f'lerp(brasas_cor{k}_{c}, brasas_noite_cor{k}_{c}, fundo_mistura)', t)
                self.assertIn(f'brasas_cor{k}_{c}', v)
                self.assertIn(f'brasas_noite_cor{k}_{c}', v)
            self.assertGreater(v[f'brasas_noite_cor{k}_b'], v[f'brasas_noite_cor{k}_r'])


if __name__ == '__main__':
    unittest.main()
