"""Pulo no ar mais forte (tools/t194_pulo_duplo_forte.py): no quadro em que sai, a força do pulo vira força * pato.pulo_ar_forca
e volta ao valor salvo dois quadros depois, sem mudar o pulo do chão."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class PuloDuploForte(unittest.TestCase):
    def test_forca_do_pulo_no_ar(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        pv = {v['name']: v.get('value') for v in m.objeto(d, 'pato')['variables']}
        self.assertGreater(pv['pulo_ar_forca'], 1)
        jog = m.folha(d, 'Jogador')['events']
        e = m.acha(jog, 'pulo no ar e giro em direcao do movimento')['events'][0]
        js = [a['parameters'][3] for a in e['actions'] if a['type']['value'] == 'PlatformBehavior::JumpSpeed']
        self.assertEqual(js, ['pato.PlatformerObject::JumpSpeed() * pato.pulo_ar_forca'])
        volta = [a['parameters'][3] for x in m.todos(m.acha(jog, 'Movimento')['events']) for a in x.get('actions', [])
                 if a['type']['value'] == 'PlatformBehavior::JumpSpeed']
        self.assertIn('pato.pulo_ar_salvo', volta)


if __name__ == '__main__':
    unittest.main()
