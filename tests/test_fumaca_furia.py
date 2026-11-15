"""Fumaça vermelha do demônio chefe em fúria (tools/t62_fumaca_furia.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t62_fumaca_furia as t62


def eventos(evs):
    for e in evs:
        yield e
        yield from eventos(e.get('events', []))


class FumacaFuria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.objs = {o['name']: o for o in cls.d['objects']}
        cls.grupo = next(e for e in next(x for x in cls.d['externalEvents'] if x['name'] == 'Chefe')['events']
                         if e.get('name') == 'Fumaça da fúria')

    def test_reusa_o_emissor_que_ja_existe(self):
        f = self.objs[t62.F]
        self.assertEqual(f['type'], 'ParticleSystem::ParticleEmitter')
        self.assertEqual(f['tank'], 80)                          # configuração dele não muda; o evento deixa contínuo
        self.assertTrue(f['destroyWhenNoParticles'])

    def test_cria_so_na_furia_e_para_na_morte(self):
        texto = json.dumps(self.grupo)
        self.assertIn('"em_furia", "True"', texto)
        self.assertEqual(texto.count('"Create"'), 1)
        # contínuo (tanque infinito) com o fluxo e o raio das variáveis dele; para de emitir na morte (ou se o chefe some)
        self.assertIn('"ParticleSystem::SetTank"}, "parameters": ["demonio_fumaca", "=", "-1"]', texto)
        self.assertIn('"ParticleSystem::SetFlow"}, "parameters": ["demonio_fumaca", "=", "demonio_fumaca.fluxo_continuo"]', texto)
        self.assertIn('"ParticleSystem::ZoneRadius"}, "parameters": ["demonio_fumaca", "=", "demonio_fumaca.raio"]', texto)
        self.assertEqual(texto.count('"ParticleSystem::StopEmission"'), 2)
        self.assertFalse([e for e in eventos(self.grupo['events']) if e['type'].endswith('JsCode')])

    def test_variaveis_existem(self):
        texto = json.dumps(self.grupo, ensure_ascii=False)
        for dono in (t62.F, t62.D):
            nomes = {v['name'] for v in self.objs[dono]['variables']}
            for v in re.findall(dono + r'\.([a-z_]+)\b(?!\()', texto):
                self.assertIn(v, nomes, f'{dono}.{v}')
            for v in re.findall(r'v\.get\("([a-z_]+)"\)', texto):
                self.assertIn(v, {x['name'] for x in self.objs[t62.F]['variables']})

    def test_rodar_de_novo_nao_muda_nada(self):
        d = json.loads(json.dumps(self.d))
        t62.migra(d)
        self.assertEqual(json.dumps(d), json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
