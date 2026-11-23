"""Anel rosa: canalizadores, escudo e o Juízo (tools/t142_anel_rosa.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnelRosa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.grupos = {gr['name']: [x['name'] for x in gr['objects']] for gr in cls.d['objectsGroups']}
        deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.rosa = m.acha(deus['events'], 'Anel rosa: amor')
        cls.evs = list(m.todos(cls.rosa['events']))

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def acoes(self, s):
        return [e for e in self.evs if s in tx(e.get('actions', []))]

    def test_canalizador_inimigo_sem_moedas(self):
        self.assertIn('canalizador', self.grupos['Inimigo'])
        self.assertNotIn('canalizador', self.grupos['Voador'])
        self.assertNotIn('canalizador', self.grupos['Chefes'])
        v = self.v('canalizador')
        self.assertEqual(v['qtd_moedas'], 0)
        self.assertEqual(v['estado'], 'calmo', 'encostar nele não dá dano nem invencibilidade')
        self.assertIs(v['chefe_final'], False)
        ofanim = self.v('ofanim')
        for nome in ('vida', 'max_vida', 'morto', 'preparado', 'bala_serie', 'kb_dir', 'sangue', 'invulneravel'):
            self.assertIn(nome, v)
        self.assertEqual(self.o['laco_amor']['type'], 'PrimitiveDrawing::Drawer')

    def test_escudo_conta_instancias_vivas(self):
        conta = next(e for e in self.evs if e.get('object') == 'canalizador' and '"canal_vivos", "+"' in tx(e['actions']))
        self.assertIn('"canalizador", "morto", "False"', tx(conta['conditions']))
        (liga,) = self.acoes('"deus", "escudo", "True"')
        self.assertIn('"deus.canal_vivos", ">", "0"', tx(liga['conditions']))
        (quebra,) = self.acoes('"deus", "escudo", "False"')
        c = tx(quebra['conditions'])
        self.assertIn('"deus", "escudo", "True"', c)
        self.assertIn('"deus.canal_vivos", "=", "0"', c)
        a = tx(quebra['actions'])
        self.assertIn('"deus", "vulneravel", "True"', a)
        self.assertIn('"Hide"}, "parameters": ["deus_escudo"]', a)
        self.assertFalse([e for e in self.acoes('"deus", "vulneravel", "True"') if e is not quebra],
                         'no anel rosa só a quebra do escudo abre a pupila')

    def test_canalizadores_voltam(self):
        (volta,) = [e for e in self.evs if '"canal_respawn"' in tx(e.get('conditions', [])) or 'deus.canal_respawn' in tx(e.get('conditions', []))]
        c = tx(volta['conditions'])
        self.assertIn('"deus", "fase", ">=", "3"', c)
        self.assertIn('"deus.canal_vivos", "=", "0"', c)
        self.assertIn('"deus", "janela_amor", "False"', c)

    def test_juizo_interrompido(self):
        j = tx(self.rosa)
        self.assertIn('"deus", "golpe", "=", "\\"juizo\\""', j)
        self.assertIn('"deus_olho", "Animation", "=", "\\"juizo\\""', j)
        (falha,) = self.acoes('"deus_olho", "Animation", "=", "\\"juizo_falha\\""')
        self.assertIn('"deus.canal_vivos", "=", "0"', tx(falha['conditions']))
        (acerta,) = self.acoes('"pato", "vida", "-", "deus.juizo_dano"')
        self.assertIn('deus.juizo_tempo', tx(acerta['conditions']))
        self.assertIn('"deus.canal_vivos", ">", "0"', tx(acerta['conditions']))
        self.assertIn('"deus", "estado", "=", "\\"fim_golpe\\""', j)

    def test_lacos_desenhados(self):
        laco = next(e for e in self.evs if '"PrimitiveDrawing::LineV2"' in tx(e.get('actions', [])))
        self.assertEqual(laco.get('object'), 'canalizador')

    def test_variaveis(self):
        texto = tx(self.rosa)
        for obj in ('deus', 'pato', 'canalizador'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')

    def test_numeros_em_variaveis(self):
        for e in self.evs:
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '3', '4'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
