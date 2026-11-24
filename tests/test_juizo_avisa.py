"""Os anjinhos nascem colados em Deus e se afastam aos poucos (tools/t162_juizo_avisa.py). O aviso do Juízo da t162
(laços engrossando, som) saiu com o Juízo novo (t164, test_juizo_feixe)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

RAIO = '(deus.canal_orbita_raio + deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class JuizoAvisa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.rosa = m.acha(cls.deus['events'], 'Anel rosa: amor')
        cls.evs = list(m.todos(cls.rosa['events']))
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def com(self, trecho, onde='actions'):
        return [e for e in self.evs if trecho in tx(e.get(onde, []))]

    def test_anjos_nascem_colados(self):
        cria = [e for e in m.todos(self.deus['events']) if '"Create"}, "parameters": ["", "canalizador"' in tx(e.get('actions', []))]
        self.assertEqual(len(cria), 2, 'o Juízo não cria mais anjinhos (t164)')
        for e in cria:
            self.assertIn('"canalizador", "surgir", "=", "0"', tx(e['actions']))
        orbitas = [e for e in self.rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions'])]
        self.assertEqual(len(orbitas), 2)
        for e in orbitas:
            t = tx(e['actions'])
            self.assertIn(f'canalizador.surgir * {RAIO}', t)
        self.assertIn('"canalizador", "surgir", "=", "min(1, canalizador.surgir + TimeDelta() / deus.canal_surgir)"', tx(orbitas[0]['actions']))
        self.assertIn('surgir', {x['name'] for x in self.o['canalizador']['variables']})

    def test_variaveis(self):
        self.assertIn('canal_surgir', self.v)


if __name__ == '__main__':
    unittest.main()
