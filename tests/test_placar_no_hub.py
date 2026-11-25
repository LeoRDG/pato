"""Placar no hub (tools/t206_placar_no_hub.py): portais do hub lado a lado no chão, entrada com E e as duas caixas de placar."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

HUBS = ('Hub', 'HubPurgatorio', 'HubParaiso')


class PlacarNoHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.js = m.acha(m.folha(cls.d, 'Hubs')['events'], 'Placar no portal')['events'][0]['inlineCode']

    def test_portais_no_mesmo_chao_e_com_e(self):
        for h in HUBS:
            ps = [i for i in m.cena(self.d, h)['instances'] if i['name'] == 'portal']
            self.assertEqual(len({p['y'] for p in ps}), 1, h)
            for p in ps:
                self.assertIn({'name': 'entrar_com_e', 'type': 'boolean', 'value': True}, p['initialVariables'], h)

    def test_entrada(self):
        entra = m.acha(m.folha(self.d, 'Portais')['events'], 'Entrar no portal')['events']
        auto = json.dumps(entra[1]['conditions'])
        self.assertIn('"entrar_com_e", "False"', auto)   # os portais das fases continuam entrando sozinhos
        com_e = json.dumps(entra[2])
        self.assertIn('"entrar_com_e", "True"', com_e)
        self.assertIn('KeyFromTextJustPressed', com_e)
        self.assertIn('"portal.cena"', com_e)

    def test_caixas(self):
        codigo = '\n'.join(self.js)
        self.assertEqual(self.js[0], 'try {')
        self.assertTrue(self.js[-1].startswith('} catch (e)'))
        for t in ('MAIS RAPIDOS', 'MAIS PONTOS', 'SEU RECORDE', '[E] ENTRAR', 'AbortSignal.timeout', '.catch('):
            self.assertIn(t, codigo)
        hp = {c['name'] for v in self.d['variables'] if v['name'] == 'hub_placar' for c in v['children']}
        for k in set(re.findall(r'n\("([a-z_]+)"\)', codigo)):
            self.assertIn(k, hp)


if __name__ == '__main__':
    unittest.main()
