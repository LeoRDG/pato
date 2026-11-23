"""Portais do Hub (tools/t86_portais_hub.py): um para cada fase."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))


class PortaisHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(JOGO, encoding='utf-8'))
        cls.hub = next(l for l in cls.d['layouts'] if l['name'] == 'Hub')
        cls.portal = next(o for o in cls.d['objects'] if o['name'] == 'portal')

    def test_um_portal_por_fase(self):
        cenas = [l['name'] for l in self.d['layouts']]
        destinos = []
        for i in self.hub['instances']:
            if i['name'] == 'portal':
                v = {x['name']: x['value'] for x in i['initialVariables']}
                self.assertIn(v['cena'], cenas)
                destinos.append(v['cena'])
        self.assertEqual(sorted(destinos), ['Inferno', 'Paraiso', 'Purgatorio'])
        anims = {a['name'] for a in self.portal['animations']}
        self.assertEqual(anims, {'Inferno', 'Purgatorio', 'Paraiso'})
        rec = {r['name']: r['file'] for r in self.d['resources']['resources']}
        for a in self.portal['animations']:
            for s in a['directions'][0]['sprites']:
                self.assertTrue(os.path.exists(os.path.join(RAIZ, rec[s['image']])))

    def test_eventos_usam_variaveis(self):
        # os eventos dos portais ficam nos eventos externos Portais (t109), ligados no Hub
        self.assertIn('Portais', [e.get('target') for e in self.hub['events']])
        portais = next(x for x in self.d['externalEvents'] if x['name'] == 'Portais')
        hubs = next(x for x in self.d['externalEvents'] if x['name'] == 'Hubs')
        self.assertIn('Hubs', [e.get('target') for e in self.hub['events']])
        ev = json.dumps(self.hub['events'] + portais['events'] + hubs['events'], ensure_ascii=False)
        self.assertIn('"Scene", "parameters": ["", "portal.cena"', ev.replace('{"value": ', '').replace('}, "parameters"', ', "parameters"'))
        for v in ('portal.espera', 'portal.nome', 'portal.nome_altura', 'queda_y', 'volta_x', 'volta_y'):
            self.assertIn(v, ev)
        nomes = {v['name'] for v in self.hub['variables']}
        self.assertLessEqual({'queda_y', 'volta_x', 'volta_y'}, nomes)
        self.assertLessEqual({'cena', 'nome', 'espera', 'nome_altura'}, {v['name'] for v in self.portal['variables']})

    def test_saida_provisoria_removida(self):
        # a saída provisória (desativada) saiu em t136; o Hub só sai pelos portais
        self.assertNotIn('Saída', [e.get('name') for e in self.hub['events']])
        self.assertNotIn('"Scene"', json.dumps(self.hub['events']))


if __name__ == '__main__':
    unittest.main()
