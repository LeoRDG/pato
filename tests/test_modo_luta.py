"""Modo de luta no alto do Paraíso: voo, câmera subindo, borda queimando, camada de luz e céu virando espaço
(tools/t138_modo_luta.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g

GRUPOS = ('Começo da luta', 'Voo do pato', 'Câmera da subida', 'Borda queimando', 'Céu para o espaço', 'Fim da luta')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class ModoLuta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.cena = m.cena(cls.d, 'Paraiso')
        cls.cv = m.vars_cena(cls.d, 'Paraiso')
        cls.g = {n: m.acha(cls.cena['events'], n) for n in GRUPOS}

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def test_grupos_existem(self):
        for n, e in self.g.items():
            self.assertIsNotNone(e, n)

    def test_camada_de_luz(self):
        camadas = [c['name'] for c in self.cena['layers']]
        self.assertIn('Luz', camadas)
        self.assertLess(camadas.index('Luz'), camadas.index('HUD'))
        self.assertGreater(camadas.index('Luz'), camadas.index(''))
        luz = next(c for c in self.cena['layers'] if c['name'] == 'Luz')
        self.assertTrue(luz['isLightingLayer'])
        self.assertTrue(luz['followBaseLayerCamera'])
        self.assertFalse(luz['visibility'], 'escondida até a luta')
        self.assertEqual(self.o['luz_pato']['type'], g.OBJ_LUZ)
        self.assertEqual(set(self.o['luz_pato']['content']), set(g.CONTEUDO_LUZ))
        c = tx(self.g['Começo da luta'])
        self.assertIn(f'"{g.ACAO_MOSTRA_CAMADA}"}}, "parameters": ["", "\\"Luz\\""]', c)
        self.assertIn('"luz_ambiente_normal"', c)
        self.assertIn(f'"{g.ACAO_ESCONDE_CAMADA}"}}, "parameters": ["", "\\"Luz\\""]', tx(self.g['Fim da luta']))

    def test_comeco_exige_asas_guardiao_e_saida(self):
        (e,) = [e for e in self.g['Começo da luta']['events'] if 'luta' in tx(e['actions'])]
        c = tx(e['conditions'])
        for s in ('"pato", "asas", "True"', '["guardiao_morto", "True", ""]', '["luta", "False", ""]',
                  '["chefe_final_morto", "False", ""]', '"saida_x_min"', '"saida_x_max"', '"saida_y"'):
            self.assertIn(s, c)
        a = tx(e['actions'])
        for s in ('["luta", "True", ""]', '["deus_criar", "True", ""]', '"luta_y0"',
                  '["pato", "PlatformerObject", "no"]', '["pato", "SmoothCamera", "no"]',
                  '["pato", "SmoothPlatformerCamera", "no"]'):
            self.assertIn(s, a)

    def test_queda_para_na_luta(self):
        q = m.acha(self.cena['events'], 'Queda do céu')
        for e in q['events']:
            self.assertIn(['luta', 'False', ''], [c['parameters'] for c in e['conditions']])

    def test_voo_so_na_luta(self):
        for n in ('Voo do pato', 'Câmera da subida', 'Borda queimando', 'Céu para o espaço'):
            for e in self.g[n]['events']:
                self.assertIn(['luta', 'True', ''], [c['parameters'] for c in e['conditions']], n)
        voo = tx(self.g['Voo do pato'])
        for tecla in ('a', 'd', 'w', 's', 'LShift'):
            self.assertIn(f'"\\"{tecla}\\""', voo)
        self.assertIn('pato.voo_vel', voo)
        self.assertIn('pato.voo_dash_vel', voo)

    def test_fim_volta_ao_normal(self):
        f = tx(self.g['Fim da luta'])
        self.assertIn('["chefe_final_morto", "True", ""]', f)
        self.assertIn('["luta", "False", ""]', f)
        for b in ('PlatformerObject', 'SmoothCamera', 'SmoothPlatformerCamera'):
            self.assertIn(f'["pato", "{b}", "yes"]', f)

    def test_borda_queima(self):
        (e,) = [e for e in m.todos(self.g['Borda queimando']['events']) if '"vida", "-"' in tx(e['actions'])]
        c, a = tx(e['conditions']), tx(e['actions'])
        self.assertIn('"pato", "invencivel", "False"', c)
        self.assertIn('"pato", "morto", "False"', c)
        self.assertIn('- borda_altura"', c)
        self.assertIn('"pato", "vida", "-", "borda_dano"', a)
        self.assertIn('"pato", "invencivel", "True"', a)
        self.assertIn('"pato", "\\"iframes\\""', a)
        self.assertIn('borda_empurrao', a)

    def test_variaveis_declaradas(self):
        texto = ''.join(tx(e) for e in self.g.values())
        for nome in ('luta', 'luta_y0', 'luta_x', 'subida_vel', 'borda_dano', 'borda_empurrao', 'borda_altura',
                     'luz_ambiente_normal', 'luz_ambiente_escuro', 'luz_pato_raio', 'altura_espaco', 'deus_criar'):
            self.assertIn(nome, self.cv, nome)
        for obj in ('pato', 'queima_borda', 'bg_espaco', 'bg_ceu_alto'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')
        for nome in ('luta', 'deus_criar'):
            self.assertIn(nome, m.vars_cena(self.d, 'Teste'))

    def test_numeros_em_variaveis(self):
        for e in m.todos(list(self.g.values())):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
