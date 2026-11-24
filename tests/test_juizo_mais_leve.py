"""O Juízo tirava 85 (quase a vida toda); agora 40, ainda o golpe mais forte da luta (tools/t161_juizo_mais_leve.py)."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class JuizoMaisLeve(unittest.TestCase):
    def test_dano(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        v = {x['name']: x['value'] for o in d['objects'] if o['name'] == 'deus' for x in o['variables']}
        self.assertEqual(v['juizo_dano'], 40)
        self.assertGreater(v['juizo_dano'], max(v['olhar_dano'], v['investida_dano'], v['laco_dano']))


if __name__ == '__main__':
    unittest.main()
