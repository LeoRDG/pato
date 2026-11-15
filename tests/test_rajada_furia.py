"""Rajada giratória de bolas de fogo do demônio chefe em fúria (tools/t69_rajada_furia.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t69_rajada_furia as t69


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class RajadaFuria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.boss = next(o for o in cls.d['objects'] if o['name'] == t69.D)
        cls.v = {x['name']: x['value'] for x in cls.boss['variables']}
        cls.grupo = next(e for e in next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')['events']
                         if e.get('name') == 'Rajada da fúria')

    def test_so_em_furia_na_explosao(self):
        texto = json.dumps(self.grupo)
        self.assertIn('"em_furia", "True"', texto)
        self.assertIn('"golpe", "=", "\\"explosao\\""', texto)
        self.assertIn('"explosao_feita", "True"', texto)

    def test_aneis_girando_por_dois_segundos_com_menos_dano(self):
        self.assertEqual(self.v['rajada_duracao'], 2)
        self.assertLess(self.v['rajada_dano'], self.v['explosao_dano'])
        self.assertLess(self.v['rajada_giro'], 360 / self.v['explosao_bolas'])      # o anel novo sai entre as bolas do anterior
        self.assertGreaterEqual(self.v['rajada_duracao'] / self.v['rajada_espera'], 4)
        repeats = [e for e in todos(self.grupo['events']) if e['type'] == 'BuiltinCommonInstructions::Repeat']
        self.assertEqual(len(repeats), 1)
        self.assertEqual(repeats[0]['repeatExpression'], f'{t69.D}.explosao_bolas')
        texto = json.dumps(self.grupo)
        self.assertIn('"bola_fogo", "dano", "=", "demonio_chefe.rajada_dano"', texto)
        self.assertNotIn('explosao_dano', texto)

    def test_segura_o_quadro_e_solta(self):
        anim = next(a for a in self.boss['animations'] if a['name'] == 'explosao')['directions'][0]
        self.assertLess(self.v['rajada_quadro'], len(anim['sprites']) - 1)
        texto = json.dumps(self.grupo)
        self.assertEqual(texto.count('"AnimatableCapability::AnimatableBehavior::PauseAnimation"'), 1)
        self.assertIn('"ChangeSprite"}, "parameters": ["demonio_chefe", "=", "demonio_chefe.rajada_quadro"]', texto)
        self.assertEqual(texto.count('"AnimatableCapability::AnimatableBehavior::PlayAnimation"'), 2)   # fim da rajada e morte no meio

    def test_variaveis_existem(self):
        for v in re.findall(t69.D + r'\.([a-z_]+)\b(?!\()', json.dumps(self.grupo)):
            self.assertIn(v, self.v)

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t69.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
