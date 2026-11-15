"""O salto com pancada do demônio na lava sempre cai numa ponte (tools/t70_pancada_na_ponte.py, em eventos pela t71)."""
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

    def test_corrige_o_alvo_depois_do_alvo_antigo(self):
        subs = self.inicio.get('events') or []
        cada = [i for i, s in enumerate(subs) if s.get('object') == 'tiles_inferno_ponte']
        self.assertEqual(len(cada), 1, 'um "Para cada" das pontes no começo do salto')
        # roda como subevento: depois das ações que gravam o alvo antigo (lava_x1, lava_y1), e grava o novo depois
        nomes = [a['parameters'][1] for a in self.inicio['actions'] if a['type']['value'] == 'SetNumberObjectVariable']
        self.assertIn('lava_x1', nomes)
        self.assertIn('lava_y1', nomes)
        depois = json.dumps(subs[cada[0] + 1:])
        self.assertIn('"lava_x1", "="', depois)
        self.assertIn('"lava_y1", "="', depois)

    def test_variaveis_existem(self):
        texto = json.dumps(self.inicio.get('events'))
        for k in re.findall(t70.D + r'\.([a-z_0-9]+)\b(?!\()', texto):
            self.assertIn(k, self.v)
        cena = {v['name'] for v in next(l for l in self.d['layouts'] if l['name'] == 'Inferno')['variables']}
        for k in re.findall(r'Variable\(([a-z_]+)\)', texto):
            self.assertIn(k, cena)

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t70.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
