"""Luz de Deus por fase: bloom e cor da aura crescem a cada fase (tools/t144_luz_e_ajuste.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class LuzPorFase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.luz = m.acha(deus['events'], 'Luz por fase')

    def test_aura_tem_bloom(self):
        efeitos = {e['effectType']: e['name'] for e in self.o['deus_aura']['effects']}
        self.assertNotIn('Godray', efeitos, 'Godray num objeto pinta o retângulo inteiro dele')
        self.assertEqual(efeitos.get('AdvancedBloom'), 'Brilho')

    def test_cada_fase_usa_suas_variaveis(self):
        v = {x['name'] for x in self.o['deus']['variables']}
        for k in (1, 2, 3, 4):
            (e,) = [e for e in self.luz['events'] if f'"deus", "fase", "=", "{k}"' in tx(e['conditions'])]
            a = tx(e['actions'])
            self.assertNotIn('"Raios"', a)
            self.assertIn(f'"deus_aura", "Effect", "\\"Brilho\\"", "\\"bloomScale\\"", "deus.bloom_{k}"', a)
            self.assertIn(f'"ChangeColor"}}, "parameters": ["deus_aura", "deus.aura_cor_{k}"]', a)
            self.assertIn(g.ACAO_PARAM_EFEITO_OBJ, a)
            for nome in (f'bloom_{k}', f'aura_cor_{k}'):
                self.assertIn(nome, v)
            self.assertIn('"deus", "luz_fase", "!=", ', tx(e['conditions']), 'só aplica quando a fase muda')

    def test_numeros_em_variaveis(self):
        for e in m.todos([self.luz]):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '3', '4'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
