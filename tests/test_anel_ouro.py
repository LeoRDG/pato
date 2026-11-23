"""Anel de ouro: o olhar de Deus e as sombras dos fragmentos (tools/t140_anel_ouro.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnelOuro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.ouro = m.acha(deus['events'], 'Anel de ouro: o olhar')
        cls.frag = m.acha(deus['events'], 'Fragmentos')

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def test_fragmentos_fazem_sombra(self):
        self.assertIn(g.COMP_SOMBRA, [b['type'] for b in self.o['fragmento']['behaviors']])
        f = tx(self.frag)
        self.assertIn('"Create"}, "parameters": ["", "fragmento"', f)
        self.assertIn('"Delete"}, "parameters": ["fragmento"', f)
        self.assertIn('["luta", "True", ""]', f)

    def test_queima_so_sem_sombra(self):
        (q,) = [e for e in m.todos(self.ouro['events']) if '"pato", "vida", "-"' in tx(e['actions'])]
        conds = q['conditions']
        ray = [c for c in conds if c['type']['value'] == 'RaycastToPosition']
        self.assertEqual(len(ray), 1)
        self.assertTrue(ray[0]['type'].get('inverted'))
        self.assertEqual(ray[0]['parameters'][:5], ['fragmento', 'deus.px', 'deus.py', 'pato.CenterX()', 'pato.CenterY()'])
        c = tx(conds)
        self.assertIn('"pato", "invencivel", "False"', c)
        pai = next(e for e in m.todos(self.ouro['events']) if q in e.get('events', []))
        self.assertIn('\\"varre\\"', tx(pai['conditions']), 'só queima na varredura')
        self.assertIn('deus.olhar_largura', c)
        self.assertIn('"pato", "vida", "-", "deus.olhar_dano"', tx(q['actions']))

    def test_estados_do_olhar(self):
        o = tx(self.ouro)
        for etapa in ('mira', 'trava', 'varre'):
            self.assertIn(f'\\"{etapa}\\"', o)
        self.assertIn('"deus", "golpe", "=", "\\"olhar\\""', o)
        self.assertIn('"deus", "estado", "=", "\\"fim_golpe\\""', o)
        self.assertIn(f'"{g.ACAO_RAIO_LUZ}"}}, "parameters": ["luz_olhar"', o)

    def test_raios_na_aura(self):
        ef = [e for e in self.o['deus_aura']['effects'] if e['effectType'] == 'Godray']
        self.assertEqual(len(ef), 1)
        self.assertLessEqual(set(ef[0]['doubleParameters']), set(g.EFEITOS['Godray']))

    def test_variaveis(self):
        texto = tx(self.ouro) + tx(self.frag)
        for obj in ('deus', 'fragmento', 'pato'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')
        for cena in ('Paraiso', 'Teste'):
            self.assertLessEqual({'olhar_rx', 'olhar_ry'}, set(m.vars_cena(self.d, cena)))

    def test_numeros_em_variaveis(self):
        for e in m.todos([self.ouro, self.frag]):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '3', '90'),  # 90: um quarto de volta (feixe em pé)
                                       f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
