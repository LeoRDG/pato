"""Armas escolhidas no hub (tools/t186_armas_no_hub.py): munição infinita com o mesmo pente, pedestais com as armas
nos três hubs (E pega; a arma equipada some do pedestal), troca por 1-4 desligada, pistola em jogo novo."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

ARMAS = ('pistola', 'doze', 'minigun', 'lanca')
HUBS = ('Hub', 'HubPurgatorio', 'HubParaiso')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class ArmasNoHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.grupo = m.acha(m.folha(cls.d, 'Hubs')['events'], 'Armas no hub')

    def fb(self, arma):
        return next(b for b in m.objeto(self.d, arma)['behaviors'] if b['type'] == 'FireBullet::FireBullet')

    def test_municao_infinita_mesmo_pente(self):
        pentes = {'pistola': 12, 'doze': 6, 'minigun': 100, 'lanca': 4}
        for a in ARMAS:
            self.assertTrue(self.fb(a)['UnlimitedAmmo'], a)
            self.assertEqual(self.fb(a)['ShotsPerReload'], pentes[a], a)

    def test_hud_sem_reserva_nem_slots(self):
        hud = tx(m.folha(self.d, 'HUD')['events'])
        for o in ('max_municao', 'hud_slot1', 'hud_slot2', 'hud_slot3', 'hud_slot4'):
            self.assertIn(f'"Hide"}}, "parameters": ["{o}"', hud, o)

    def test_pedestais_nos_tres_hubs(self):
        uuids = [i['persistentUuid'] for l in self.d['layouts'] for i in l['instances']]
        self.assertEqual(len(uuids), len(set(uuids)))
        for h in HUBS:
            ped = [i for i in m.cena(self.d, h)['instances'] if i['name'] == 'pedestal_arma']
            armas = sorted({v['name']: v['value'] for v in i['initialVariables']}['arma'] for i in ped)
            self.assertEqual(armas, sorted(ARMAS), h)
            trader = next(i for i in m.cena(self.d, h)['instances'] if i['name'] == 'trader')
            raio = next(v['value'] for v in m.objeto(self.d, 'trader')['variables'] if v['name'] == 'loja_raio')
            for i in ped:
                self.assertLess(i['x'] + 120, trader['x'] - raio / 2, 'longe da loja (o E abre a loja)')
        self.assertIn('Hubs', [e.get('target') for e in m.cena(self.d, 'Hub')['events']])
        for fase in ('Inferno', 'Purgatorio', 'Paraiso'):
            self.assertNotIn('Hubs', [e.get('target') for e in m.cena(self.d, fase)['events']])

    def test_expositor_some_quando_equipado(self):
        g = tx(self.grupo)
        self.assertIn('"Create"}, "parameters": ["", "expositor_arma"', g)
        self.assertIn('GlobalVariableString(arma_atual)', g)
        esconde = [e for e in m.todos(self.grupo['events'])
                   if 'GlobalVariableString(arma_atual)' in tx(e.get('conditions', []))]
        self.assertTrue(any('"Hide"}, "parameters": ["expositor_arma"' in tx(e['actions']) for e in esconde))

    def test_pegar_com_e(self):
        g = tx(self.grupo)
        self.assertIn('"KeyFromTextJustPressed"}, "parameters": ["", "\\"e\\""]', g)
        self.assertIn('"PickNearest"', g)
        for a in ARMAS:
            self.assertIn(f'"SetStringVariable"}}, "parameters": ["arma_atual", "=", "\\"{a}\\""]', g)
            self.assertIn(f'"SetBooleanObjectVariable"}}, "parameters": ["{a}", "equipada", "True", ""]', g)
        self.assertIn('pato.arma_raio', g)
        nomes = {v['name'] for v in m.objeto(self.d, 'pato')['variables']}
        self.assertLessEqual({'arma_raio', 'arma_dica_y'}, nomes)
        exp = {v['name'] for v in m.objeto(self.d, 'expositor_arma')['variables']}
        self.assertLessEqual({'arma', 'nome', 'base_y', 'fase', 'bob_alt', 'bob_vel'}, exp)

    def test_troca_por_numero_desligada(self):
        troca = m.acha(m.folha(self.d, 'Jogador')['events'], 'Troca de Arma')
        teclas = [e for e in m.todos(troca['events']) if 'KeyFromTextJustPressed' in tx(e.get('conditions', []))]
        self.assertEqual(len(teclas), 4)
        self.assertTrue(all(e.get('disabled') for e in teclas))

    def test_cena_comeca_com_a_arma_escolhida(self):
        cria = tx(m.acha(m.folha(self.d, 'Jogador')['events'], 'Criacao das Armas'))
        for a in ARMAS:
            self.assertIn(f'"StringVariable"}}, "parameters": ["arma_atual", "=", "\\"{a}\\""]', cria, a)
            self.assertIn(f'"Show"}}, "parameters": ["{a}"', cria, a)

    def test_jogo_novo_comeca_com_pistola(self):
        menu = tx(m.cena(self.d, 'Menu')['events'])
        self.assertIn('"SetStringVariable"}, "parameters": ["arma_atual", "=", "\\"pistola\\""]', menu)
        self.assertLess(menu.index('arma_atual'), menu.index('"Scene"'))

    def test_sem_numeros_soltos(self):
        for e in m.todos(self.grupo['events']):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
