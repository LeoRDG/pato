"""Ofanim guardião, barreira de luz e checkpoint do Empíreo que dá as asas (tools/t137_guardiao_e_checkpoint.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class GuardiaoCheckpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.cena = m.cena(cls.d, 'Paraiso')
        cls.cv = m.vars_cena(cls.d, 'Paraiso')
        cls.grupos = {g['name']: [x['name'] for x in g['objects']] for g in cls.d['objectsGroups']}
        cls.guard = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Ofanim guardião')
        cls.check = m.acha(cls.cena['events'], 'Checkpoint do Empíreo')

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def insts(self, nome):
        return [i for i in self.cena['instances'] if i['name'] == nome]

    def test_guardiao_e_so_a_instancia(self):
        ofs = self.insts('ofanim')
        marcados = [i for i in ofs if any(v['name'] == 'guardiao' and v['value'] is True for v in i['initialVariables'])]
        self.assertEqual(len(marcados), 1)
        self.assertIs(self.v('ofanim')['guardiao'], False)
        self.assertIn('ofanim', self.grupos['Chefes'])
        self.assertEqual(self.v('ofanim')['nome'], 'OFANIM, O GUARDIÃO')

    def test_guardiao_preparado_uma_vez(self):
        g = tx(self.guard)
        self.assertIn('"ofanim", "max_vida", "*", "ofanim.guardiao_vida_mult"', g)
        self.assertIn('"ofanim", "firme", "True"', g)
        self.assertIn('"ofanim", "barra_ativa", "True"', g)
        self.assertIn('"ofanim", "aberto_tempo", "*", "ofanim.guardiao_aberto_fator"', g)
        self.assertIn('"ofanim.max_vida * ofanim.guardiao_fase_abaixo"', g)
        prep = next(e for e in m.todos(self.guard['events']) if '"max_vida", "*"' in tx(e.get('actions', [])))
        self.assertIn('"chefe_preparado", "False"', tx(prep['conditions']))
        self.assertIn('"guardiao", "True"', tx(prep['conditions']))
        morte = next(e for e in m.todos(self.guard['events']) if '"guardiao_morto", "True"' in tx(e.get('actions', [])))
        self.assertIn('"morto", "True"', tx(morte['conditions']))
        self.assertIn('"guardiao", "True"', tx(morte['conditions']))

    def test_barra_so_com_barra_ativa(self):
        ev = m.acha(m.folha(self.d, 'HUD')['events'], 'Barras de chefe')
        chefes = m.acha(ev['events'], 'Chefes')['events'][0]
        self.assertIn(['Chefes', 'barra_ativa', 'True', ''], [c['parameters'] for c in chefes['conditions']])
        for nome in self.grupos['Chefes']:
            self.assertIn('barra_ativa', self.v(nome), nome)
        self.assertIs(self.v('demonio_chefe')['barra_ativa'], True)
        self.assertIs(self.v('cutulu')['barra_ativa'], True)
        self.assertIs(self.v('ofanim')['barra_ativa'], False)

    def test_saida_fechada_sem_guardiao(self):
        (b,) = self.insts('barreira_empireo')
        (c,) = self.insts('checkpoint_empireo')
        self.assertIn('barreira_empireo', self.grupos['Terreno'])
        self.assertIn('PlatformBehavior::PlatformBehavior', [x['type'] for x in self.o['barreira_empireo']['behaviors']])
        pato_meio = 180 / 2
        self.assertLess(b['x'] + b['width'] + pato_meio, self.cv['saida_x_min'], 'o pato não alcança a saída')
        self.assertGreater(b['x'], c['x'] + 192, 'o checkpoint fica antes da barreira')
        chao = -4096
        self.assertEqual(b['y'] + b['height'], chao)
        self.assertGreaterEqual(b['height'], 1536, 'alta demais para pular por cima')
        self.assertEqual(c['y'] + 192, chao)
        self.assertGreaterEqual(c['x'], 10624)
        apaga = [e for e in m.todos(self.cena['events']) if '"Delete"}, "parameters": ["barreira_empireo"' in tx(e.get('actions', []))]
        self.assertEqual(len(apaga), 1)
        self.assertIn('["guardiao_morto", "True", ""]', tx(apaga[0]['conditions']))
        saida = m.acha(self.cena['events'], 'Saída no Empíreo')
        cena_ev = next(e for e in m.todos(saida['events']) if '"Scene"' in tx(e['actions']))
        self.assertIn('["chefe_final_morto", "True", ""]', tx(cena_ev['conditions']))

    def test_respawn_no_checkpoint_sem_luta(self):
        g = tx(self.check)
        for campo in ('ativo', 'x', 'y', 'guardiao'):
            self.assertIn(f'waypoints[CurrentSceneName()].{campo}', g)
        inicio = next(e for e in m.todos(self.check['events']) if '"DepartScene"' in tx(e['conditions']))
        self.assertIn('waypoints[CurrentSceneName()].guardiao", "True"', tx(inicio['conditions']))
        a = tx(inicio['actions'])
        self.assertIn('["guardiao_morto", "True", ""]', a)
        self.assertIn('"pato", "asas", "True"', a)
        wp = next(v for v in self.d['variables'] if v['name'] == 'waypoints')
        par = next(c for c in wp['children'] if c['name'] == 'Paraiso')
        self.assertIn({'guardiao': False}, [{c['name']: c['value']} for c in par['children']])
        self.assertIs(self.v('pato')['asas'], False)
        pega = next(e for e in m.todos(self.check['events']) if '"CollisionNP"' in tx(e['conditions']))
        self.assertIn('["guardiao_morto", "True", ""]', tx(pega['conditions']))

    def test_variaveis_declaradas(self):
        g = tx(self.guard) + tx(self.check)
        self.assertIn('guardiao_morto', self.cv)
        for obj in ('ofanim', 'pato', 'asas_pato'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', g):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')

    def test_numeros_em_variaveis(self):
        for e in list(m.todos([self.guard, self.check])):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2'),  # 2: metade, para centralizar
                                       f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
