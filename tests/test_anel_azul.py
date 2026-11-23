"""Anel azul: Deus pisca e tudo escurece; só os halos protegem do clarão (tools/t141_anel_azul.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnelAzul(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.azul = m.acha(deus['events'], 'Anel azul: piscar')

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def test_escuro_e_volta(self):
        a = tx(self.azul)
        self.assertIn('"deus", "golpe", "=", "\\"piscar\\""', a)
        amb = [x['parameters'] for e in m.todos(self.azul['events']) for x in e.get('actions', [])
               if x['type']['value'] == g.ACAO_LUZ_AMBIENTE]
        self.assertIn(['', '"Luz"', 'luz_ambiente_escuro'], amb)
        self.assertIn(['', '"Luz"', 'luz_ambiente_normal'], amb)
        self.assertIn(['', '"Luz"', 'deus.luz_ambiente_flash'], amb)
        self.assertIn(f'"{g.ACAO_RAIO_LUZ}"}}, "parameters": ["luz_pato", "deus.luz_pato_raio_escuro"]', a)
        self.assertIn(f'"{g.ACAO_RAIO_LUZ}"}}, "parameters": ["luz_pato", "luz_pato_raio"]', a)
        self.assertIn('"Delete"}, "parameters": ["luz_halo"', a)
        self.assertIn('"deus", "estado", "=", "\\"fim_golpe\\""', a)
        self.assertIn('"deus_olho", "Animation", "=", "\\"fechado\\""', a)

    def test_halos_nascem_e_derivam(self):
        rep = [e for e in m.todos(self.azul['events']) if e['type'].endswith('Repeat')]
        self.assertEqual([e['repeatExpression'] for e in rep], ['deus.halo_qtd'])
        self.assertIn('"Create"}, "parameters": ["", "luz_halo"', tx(rep[0]))
        self.assertIn('luz_halo.vx', tx(self.azul))

    def test_seguro_dentro_do_halo(self):
        marca = next(e for e in m.todos(self.azul['events']) if '"pato", "no_halo", "True"' in tx(e['actions']))
        self.assertEqual(marca.get('object'), 'luz_halo')
        self.assertIn('deus.halo_raio', tx(marca['conditions']))
        (q,) = [e for e in m.todos(self.azul['events']) if '"pato", "vida", "-"' in tx(e['actions'])]
        c = tx(q['conditions'])
        self.assertIn('"pato", "no_halo", "False"', c)
        self.assertIn('"pato", "invencivel", "False"', c)
        self.assertIn('"pato", "vida", "-", "deus.piscar_dano"', tx(q['actions']))

    def test_variaveis(self):
        texto = tx(self.azul)
        for obj in ('deus', 'pato', 'luz_halo'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')
        for cena in ('Paraiso', 'Teste'):
            self.assertLessEqual({'luz_ambiente_escuro', 'luz_ambiente_normal', 'luz_pato_raio', 'subida_vel'},
                                 set(m.vars_cena(self.d, cena)), cena)

    def test_numeros_em_variaveis(self):
        for e in m.todos([self.azul]):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
