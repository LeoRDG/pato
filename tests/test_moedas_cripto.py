"""Moedas cripto 1x, 5x e 10x (tools/t84_moedas_cripto.py)."""
import json, os, unittest
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class MoedasCripto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(JOGO, encoding='utf-8'))
        cls.moeda = next(o for o in cls.d['objects'] if o['name'] == 'moeda')
        cls.var = {v['name']: v['value'] for v in cls.moeda['variables']}
        cls.comb = json.dumps(next(x for x in cls.d['externalEvents'] if x['name'] == 'Combate')['events'],
                              ensure_ascii=False)

    def test_tres_animacoes_com_imagens(self):
        anims = {a['name']: a for a in self.moeda['animations']}
        self.assertEqual(list(anims), ['x1', 'x5', 'x10'])
        rec = {r['name']: r for r in self.d['resources']['resources']}
        larguras = []
        for nome, a in anims.items():
            sprites = a['directions'][0]['sprites']
            self.assertGreaterEqual(len(sprites), 4)
            self.assertTrue(a['directions'][0]['looping'])
            for s in sprites:
                r = rec[s['image']]
                self.assertFalse(r['smoothed'])
                self.assertTrue(os.path.exists(os.path.join(RAIZ, r['file'])), r['file'])
            larguras.append(sprites[0]['customCollisionMask'][0][1]['x'] - sprites[0]['customCollisionMask'][0][0]['x'])
            im = Image.open(os.path.join(RAIZ, rec[sprites[0]['image']]['file']))
            self.assertEqual(im.getpixel((im.width // 2, im.height // 2))[3], 255)
        self.assertEqual(larguras, sorted(larguras))            # 10x é a maior

    def test_numeros_em_variaveis(self):
        for v in ('mult', 'escala', 'chance_x5', 'chance_x10'):
            self.assertIn(v, self.var)
            self.assertIn(f'moeda.{v}', self.comb)
        self.assertNotIn('"0.02"', self.comb)
        self.assertIn('moeda.valor * moeda.mult', self.comb)
        self.assertNotIn('"moeda.valor"', self.comb)
        for n in ('x1', 'x5', 'x10'):
            self.assertIn(f'"\\"{n}\\""', self.comb)

    def test_moedas_postas_sem_esticar(self):
        for l in self.d['layouts']:
            for i in l['instances']:
                if i['name'] == 'moeda':
                    self.assertFalse(i.get('customSize') and (i['width'], i['height']) == (103, 60), l['name'])


if __name__ == '__main__':
    unittest.main()
