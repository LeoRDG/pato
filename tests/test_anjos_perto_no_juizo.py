"""No Juízo os anjinhos param o vai e vem e ficam perto de Deus, girando em volta dele (canal_vaivem_k vai a 0 enquanto
juizo_ativo, suave, e volta a 1 depois) (tools/t166_anjos_perto_no_juizo.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnjosPertoNoJuizo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.v = {x['name']: x['value'] for x in m.objeto(cls.d, 'deus')['variables']}
        deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.rosa = m.acha(deus['events'], 'Anel rosa: amor')['events']

    def test_vaivem_multiplicado(self):
        orbita = [e for e in self.rosa if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions'])]
        self.assertGreaterEqual(len(orbita), 2)
        for e in orbita:
            t = tx(e['actions'])
            self.assertIn('deus.canal_vaivem * deus.canal_vaivem_k *', t)
            self.assertNotIn('deus.canal_vaivem * (1', t)

    def test_k_segue_o_juizo(self):
        (liga,) = [e for e in self.rosa if '"deus", "canal_vaivem_k"' in tx(e['actions'])
                   and '"deus", "juizo_ativo", "True"' in tx(e['conditions'])]
        self.assertIn('max(0, deus.canal_vaivem_k - TimeDelta() / deus.canal_vaivem_recolhe)', tx(liga['actions']))
        (volta,) = [e for e in self.rosa if '"deus", "canal_vaivem_k"' in tx(e['actions'])
                    and '"deus", "juizo_ativo", "False"' in tx(e['conditions'])]
        self.assertIn('min(1, deus.canal_vaivem_k + TimeDelta() / deus.canal_vaivem_recolhe)', tx(volta['actions']))
        i = min(self.rosa.index(liga), self.rosa.index(volta))
        j = min(i for i, e in enumerate(self.rosa) if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']))
        self.assertLess(i, j)
        self.assertEqual(self.v['canal_vaivem_k'], 1)
        self.assertGreater(self.v['canal_vaivem_recolhe'], 0)


if __name__ == '__main__':
    unittest.main()
