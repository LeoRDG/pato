"""Teste: com deus.teste_c ligado, a tecla C tira deus.teste_c_corte da vida máxima de Deus (tools/t163_teste_c.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class TesteC(unittest.TestCase):
    def test_tecla_c(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        deus = m.acha(m.folha(d, 'InimigosParaiso')['events'], 'Deus')
        g = m.acha(deus['events'], 'Teste: C tira vida')
        (e,) = g['events']
        c = tx(e['conditions'])
        self.assertIn('"KeyFromTextJustPressed"}, "parameters": ["", "\\"c\\""]', c)
        self.assertIn('"deus", "teste_c", "True"', c)
        self.assertIn('"deus", "morto", "False"', c)
        self.assertIn('"SceneInstancesCount"}, "parameters": ["", "deus", ">", "0"]', c)
        self.assertIn('"deus", "vida", "-", "deus.max_vida * deus.teste_c_corte"', tx(e['actions']))
        v = {x['name']: x['value'] for o in d['objects'] if o['name'] == 'deus' for x in o['variables']}
        self.assertIs(v['teste_c'], True)
        self.assertEqual(v['teste_c_corte'], 0.25)


if __name__ == '__main__':
    unittest.main()
