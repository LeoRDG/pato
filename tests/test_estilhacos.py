"""Estilhaços (tools/t205_loja_enxuta.py): a bala que acerta (inimigo ou terreno) é marcada em vez de sumir e um bloco JS a troca
por pato.estilhaco_qtd estilhaços; estilhaço não estilhaça; números em variáveis do pato; preços mais baixos."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


class Estilhacos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.proj = m.acha(m.folha(cls.d, 'Combate')['events'], 'Projéteis')
        cls.js = m.acha(cls.proj['events'], 'Estilhaços')['events'][0]['inlineCode']

    def test_na_loja(self):
        cat = next(v for v in self.d['variables'] if v['name'] == 'loja_catalogo')
        ids = [next(c['value'] for c in it['children'] if c['name'] == 'id') for it in cat['children']]
        self.assertIn('estilhaco', ids)
        self.assertIn('estilhaco', {c['name'] for v in self.d['variables'] if v['name'] == 'upgrades' for c in v['children']})

    def test_marca_em_vez_de_apagar(self):
        s = json.dumps(self.proj)
        self.assertEqual(s.count('"estilhacou", "True"'), 2)   # inimigo e terreno, só no primeiro impacto
        self.assertIn('"fragmento", "False"', s)
        # o JS vem depois do dano e do terreno, e nunca trava o jogo
        nomes = [e.get('name') for e in self.proj['events']]
        self.assertGreater(nomes.index('Estilhaços'), nomes.index('Dano da bala'))
        self.assertEqual(self.js[0], 'try {')
        self.assertTrue(self.js[-1].startswith('} catch (e)'))
        self.assertIn('ov.get("fragmento").setBoolean(true)', '\n'.join(self.js))

    def test_numeros_em_variaveis(self):
        pato = {v['name'] for v in m.objeto(self.d, 'pato')['variables']}
        for k in set(re.findall(r'n\("([a-z_]+)"\)', '\n'.join(self.js))):
            self.assertIn(k, pato)
        proj = {v['name'] for v in m.objeto(self.d, 'projetil')['variables']}
        self.assertLessEqual({'fragmento', 'estilhacar', 'estilhaco_parede'}, proj)


if __name__ == '__main__':
    unittest.main()
