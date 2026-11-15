"""Câmera mais baixa na luta contra o demônio chefe (tools/t67_camera_chefe.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t67_camera_chefe as t67


class CameraChefe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.objs = {o['name']: o for o in cls.d['objects']}
        cls.grupo = next(e for e in next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')['events']
                         if e.get('name') == 'Câmera da luta')

    def vars(self, nome):
        return {v['name']: v['value'] for v in self.objs[nome]['variables']}

    def test_usa_a_smoothcamera_do_pato(self):
        cam = next(b for b in self.objs['pato']['behaviors'] if b['type'] == 'SmoothCamera::SmoothCamera')
        self.assertEqual(cam['name'], 'SmoothCamera')
        ext = next(x for x in self.d['eventsFunctionsExtensions'] if x['name'] == 'SmoothCamera')
        funcs = {f['name'] for b in ext['eventsBasedBehaviors'] if b['name'] == 'SmoothCamera' for f in b['eventsFunctions']}
        self.assertLessEqual({'OffsetY', 'SetOffsetYOp'}, funcs)
        self.assertEqual(self.vars('pato')['camera_offset_normal'], cam['CameraOffsetY'])

    def test_desce_na_luta_e_volta_depois(self):
        texto = json.dumps(self.grupo)
        self.assertEqual(texto.count('SetOffsetYOp'), 2)
        self.assertIn('"chefe_trancado", "True"', texto)
        self.assertIn('"chefe_trancado", "False"', texto)
        self.assertIn('pato.camera_offset_normal', texto)
        for v in re.findall(t67.D + r'\.([a-z_]+)\b(?!\()', texto):
            self.assertIn(v, self.vars(t67.D))
        # com o chefe e o pato no mesmo chão a câmera fica mais baixa do que fora da luta
        v = self.vars(t67.D)
        offset_luta = (-384 / 2 + 155 / 2) * v['camera_mistura'] + v['camera_dy']
        self.assertGreater(offset_luta, self.vars('pato')['camera_offset_normal'])

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t67.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
