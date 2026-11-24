"""Na luta com Deus as bordas da tela são paredes (Terreno invisível que acompanha a câmera), então o ricochete
funciona nelas (tools/t157_paredes_da_tela.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

P = 'parede_tela'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class ParedesDaTela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.cena = m.cena(cls.d, 'Paraiso')
        cls.g = m.acha(cls.cena['events'], 'Paredes da tela')
        cls.evs = list(m.todos(cls.g['events']))
        cls.vc = {v['name']: v['value'] for v in cls.cena['variables']}

    def test_objeto_no_terreno_sem_plataforma(self):
        p = self.o[P]
        self.assertEqual(p['type'], 'Sprite')
        self.assertEqual(p['behaviors'], [], 'não é plataforma: o voo do pato não muda')
        terreno = next(g for g in self.d['objectsGroups'] if g['name'] == 'Terreno')
        self.assertIn(P, [x['name'] for x in terreno['objects']])
        self.assertIn('lado', {v['name'] for v in p['variables']})

    def test_nascem_escondidas_na_luta(self):
        """Create junta a nova instância às já escolhidas: criar as quatro num evento só dava lado 4 a todas."""
        (pai,) = [e for e in self.evs if '"SceneInstancesCount"}, "parameters": ["", "parede_tela", "=", "0"' in tx(e.get('conditions', []))]
        self.assertIn('"luta", "True"', tx(pai['conditions']))
        self.assertIn('"parede_n", "=", "0"', tx(pai['actions']))
        (rep,) = pai['events']
        self.assertEqual(rep['type'], 'BuiltinCommonInstructions::Repeat')
        self.assertEqual(rep['repeatExpression'], '4')
        a = rep['actions']
        self.assertEqual(sum(x['type']['value'] == 'Create' for x in a), 1)
        t = tx(a)
        self.assertLess(t.index('"parede_n", "+", "1"'), t.index('"Create"'))
        self.assertIn('"parede_tela", "lado", "=", "parede_n"', t)
        self.assertIn('"Hide"}, "parameters": ["parede_tela"', t)
        self.assertIn('"parede_tela", "Resizable", "=", "parede_tamanho"', t)

    def test_seguem_a_camera(self):
        pos = {}
        for e in self.evs:
            for c in e.get('conditions', []):
                if c['parameters'][:2] == [P, 'lado']:
                    (s,) = [x for x in e['actions'] if x['type']['value'] == 'SetXY']
                    pos[c['parameters'][3]] = (s['parameters'][2], s['parameters'][4])
                    self.assertIn('"luta", "True"', tx(e['conditions']))
        self.assertEqual(pos['1'], (f'{CX} - {CW} / 2 - parede_tamanho', f'{CY} - parede_tamanho / 2'))
        self.assertEqual(pos['2'], (f'{CX} + {CW} / 2', f'{CY} - parede_tamanho / 2'))
        self.assertEqual(pos['3'], (f'{CX} - parede_tamanho / 2', f'{CY} - {CH} / 2 - parede_tamanho'))
        self.assertEqual(pos['4'], (f'{CX} - parede_tamanho / 2', f'{CY} + {CH} / 2'))

    def test_somem_fora_da_luta(self):
        (e,) = [e for e in self.evs if '"Delete"}, "parameters": ["parede_tela"' in tx(e.get('actions', []))]
        self.assertIn('"luta", "False"', tx(e['conditions']))

    def test_depois_do_voo(self):
        nomes = [e.get('name') for e in self.cena['events']]
        self.assertEqual(nomes.index('Paredes da tela'), nomes.index('Voo do pato') + 1)
        self.assertGreaterEqual(self.vc['parede_tamanho'], 1000)


if __name__ == '__main__':
    unittest.main()
