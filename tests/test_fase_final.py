"""Fase final de Deus: anéis soltos em órbita, Três Anéis e o puxão (tools/t143_fase_final.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

ANEIS = ('deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class FaseFinal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.final = m.acha(cls.deus['events'], 'Fase final')
        cls.tres = m.acha(cls.deus['events'], 'Três anéis')
        cls.puxao = m.acha(cls.deus['events'], 'Puxão')

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def test_aneis_orbitam_na_fase_4(self):
        orb = next(e for e in self.final['events'] if 'deus.orbita_ang' in tx(e['actions']))
        self.assertIn('"deus", "fase", "=", "4"', tx(orb['conditions']))
        a = tx(orb['actions'])
        for anel in ANEIS:
            self.assertIn(f'"SetXY"}}, "parameters": ["{anel}"', a)
            self.assertIn(f'"SetAngle"}}, "parameters": ["{anel}", "+", "deus.anel_giro_final * TimeDelta()"]', a)
        tiros = [e for e in self.final['events'] if '"projetil_inimigo"' in tx(e)]
        self.assertEqual(len(tiros), 3, 'cada anel atira sozinho')
        for e in tiros:
            self.assertIn('"deus", "fase", "=", "4"', tx(e['conditions']))

    def test_tres_aneis_com_buraco(self):
        t = tx(self.tres)
        self.assertIn('"deus", "golpe", "=", "\\"aneis\\""', t)
        rep = [e for e in m.todos(self.tres['events']) if e['type'].endswith('Repeat')]
        self.assertTrue(rep)
        for r in rep:
            self.assertIn('deus.aneis_buraco_meio', r['repeatExpression'])
        self.assertIn('deus.aneis_rodadas', t)
        self.assertIn('"deus", "estado", "=", "\\"fim_golpe\\""', t)

    def test_puxao_so_na_luta(self):
        p = tx(self.puxao)
        self.assertIn('"deus", "golpe", "=", "\\"puxao\\""', p)
        puxa = next(e for e in m.todos(self.puxao['events']) if '"pato", "voo_vx", "+"' in tx(e['actions']))
        self.assertIn('["luta", "True", ""]', tx(puxa['conditions']))
        self.assertIn('deus.puxao_forca', tx(puxa['actions']))
        self.assertIn('"deus", "estado", "=", "\\"fim_golpe\\""', p)

    def test_timers_comecam_na_criacao(self):
        cria = m.acha(self.deus['events'], 'Criação')
        zerados = set(re.findall(r'"ResetObjectTimer"\}, "parameters": \["deus", "\\"(\w+)\\""', tx(cria)))
        comparados = set(re.findall(r'"CompareObjectTimer"\}, "parameters": \["deus", "\\"(\w+)\\""', tx(self.deus)))
        self.assertTrue(comparados)
        self.assertLessEqual(comparados, zerados)

    def test_variaveis(self):
        texto = tx(self.final) + tx(self.tres) + tx(self.puxao)
        for obj in ('deus', 'pato', 'projetil_inimigo'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')

    def test_numeros_em_variaveis(self):
        for e in m.todos([self.final, self.tres, self.puxao]):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters'] + [e.get('repeatExpression', '')]:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '4', '360'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
