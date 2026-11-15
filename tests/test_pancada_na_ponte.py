"""O salto com pancada do demônio na lava sempre cai numa ponte (tools/t70_pancada_na_ponte.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t70_pancada_na_ponte as t70


class PancadaNaPonte(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        chefe = next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')['events']
        cls.inicio = t70.inicio_do_salto(next(e for e in chefe if e.get('name') == 'Fase 2'))
        cls.v = {x['name']: x['value'] for x in next(o for o in cls.d['objects'] if o['name'] == t70.D)['variables']}

    def codigo(self):
        js = [s for s in self.inicio.get('events') or [] if s['type'].endswith('JsCode')]
        textos = [s['inlineCode'] if isinstance(s['inlineCode'], str) else '\n'.join(s['inlineCode']) for s in js]
        return [c for c in textos if t70.MARCA in c]

    def test_corrige_o_alvo_depois_do_alvo_antigo(self):
        self.assertEqual(len(self.codigo()), 1)
        # roda como subevento: depois das ações que gravam o alvo antigo (lava_x1, lava_y1)
        nomes = [a['parameters'][1] for a in self.inicio['actions'] if a['type']['value'] == 'SetNumberObjectVariable']
        self.assertIn('lava_x1', nomes)
        self.assertIn('lava_y1', nomes)

    def test_variaveis_existem(self):
        c = self.codigo()[0]
        for k in re.findall(r'num\("([a-z_]+)"\)', c) + re.findall(r'v\.get\("([a-z_]+)"\)', c):
            self.assertIn(k, self.v)
        cena = {v['name'] for v in next(l for l in self.d['layouts'] if l['name'] == 'Inferno')['variables']}
        for k in re.findall(r'\bn\("([a-z_]+)"\)', c):
            self.assertIn(k, cena)

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t70.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
