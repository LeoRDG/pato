"""Um hub por reino (tools/t122_hubs_por_reino.py)."""
import json, os, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.environ.get('JOGO_JSON', os.path.join(RAIZ, 'jogo.json'))


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


class Hubs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(JOGO, encoding='utf-8'))
        cls.cenas = {l['name']: l for l in cls.d['layouts']}
        cls.ext = {x['name']: x for x in cls.d['externalEvents']}

    def var(self, cena, nome):
        return next(v['value'] for v in self.cenas[cena]['variables'] if v['name'] == nome)

    def test_cada_cena_sabe_o_seu_hub(self):
        esperado = {'Hub': 'Hub', 'Inferno': 'Hub', 'Teste': 'Hub', 'Purgatorio': 'HubPurgatorio',
                    'HubPurgatorio': 'HubPurgatorio', 'Paraiso': 'HubParaiso', 'HubParaiso': 'HubParaiso'}
        for cena, hub in esperado.items():
            self.assertEqual(self.var(cena, 'hub'), hub, cena)
        # toda cena que liga Jogador ou Portais tem a variável
        for nome, l in self.cenas.items():
            if any(e.get('target') in ('Jogador', 'Portais') for e in l['events']):
                self.assertIn('hub', [v['name'] for v in l['variables']], nome)

    def test_morte_e_portais_vao_para_o_hub_da_cena(self):
        jog = json.dumps(self.ext['Jogador']['events'])
        self.assertNotIn('"\\"Hub\\""', jog)
        cenas_morte = [a['parameters'][1] for e in todos(self.ext['Jogador']['events']) for a in e.get('actions', [])
                       if a['type']['value'] == 'Scene']
        self.assertEqual(cenas_morte, ['hub'])
        port = list(todos(self.ext['Portais']['events']))
        troca = [e for e in port if any(a['type']['value'] == 'SetStringObjectVariable' and
                                        a['parameters'][:2] == ['portal', 'cena'] and a['parameters'][3] == 'hub'
                                        for a in e.get('actions', []))]
        self.assertEqual(len(troca), 1)
        self.assertIn('DepartScene', json.dumps(troca[0]['conditions']))
        wp = [e for e in port if 'waypoints[CurrentSceneName()].ativo' in json.dumps(e.get('actions', []))
              and 'True' in json.dumps(e.get('actions', []))]
        self.assertTrue(any('"cena", "=", "hub"' in json.dumps(e['conditions']) for e in wp))
        # a troca vem antes de o portal ser usado
        tipos = [json.dumps(e) for e in self.ext['Portais']['events']]
        i_troca = next(i for i, t in enumerate(tipos) if '"SetStringObjectVariable"' in t and '"hub"' in t)
        i_usa = next(i for i, t in enumerate(tipos) if '"Scene"' in t)
        self.assertLess(i_troca, i_usa)

    def test_saida_do_paraiso_vai_para_o_hub(self):
        g = next(e for e in self.cenas['Paraiso']['events'] if e.get('name') == 'Saída no Empíreo')
        self.assertIn('"proxima_cena", "=", "hub"', json.dumps(g['events'][0]['actions']))
        self.assertEqual(self.var('Paraiso', 'proxima_cena'), 'Hub')     # o valor do editor fica

    def test_hubs_novos_com_o_reino_certo(self):
        for nome, tiles, fundo, cor in [('HubPurgatorio', 'tiles_purgatorio', 'bg_purgatorio_longe', (128, 138, 128)),
                                        ('HubParaiso', 'tiles_ceu', 'bg_paraiso_nuvens', (172, 196, 232))]:
            c = self.cenas[nome]
            nomes = [i['name'] for i in c['instances']]
            self.assertIn(tiles, nomes)
            self.assertNotIn('tiles_inferno_escuro_', nomes)
            self.assertFalse(any(n.startswith('bg_inferno') for n in nomes))
            self.assertIn(fundo, nomes)
            self.assertIn('trader', nomes)
            self.assertEqual((c['r'], c['v'], c['b']), cor)
            destinos = sorted(v['value'] for i in c['instances'] if i['name'] == 'portal'
                              for v in i['initialVariables'] if v['name'] == 'cena')
            self.assertEqual(destinos, ['Inferno', 'Paraiso', 'Purgatorio'])
            alvos = [e.get('target') for e in c['events'] if e.get('type', '').endswith('Link')]
            for x in ('Jogador', 'AplicarUpgrades', 'Combate', 'HUD', 'Portais', 'Loja'):
                self.assertIn(x, alvos)
            self.assertNotIn('bg_inferno_escuro', json.dumps(c['events']))
            self.assertIn('\\"fundo\\"', json.dumps(c['events']))
            uuids = [i['persistentUuid'] for i in c['instances']]
            self.assertEqual(len(uuids), len(set(uuids)))
            hub_uuids = {i['persistentUuid'] for i in self.cenas['Hub']['instances']}
            self.assertFalse(hub_uuids & set(uuids))
            # tilemap igual ao do Hub
            tm = lambda l, n: next(p['value'] for i in l['instances'] if i['name'] == n
                                   for p in i['stringProperties'] if p['name'] == 'tilemap')
            self.assertEqual(tm(c, tiles), tm(self.cenas['Hub'], 'tiles_inferno_escuro_'))


if __name__ == '__main__':
    unittest.main()
