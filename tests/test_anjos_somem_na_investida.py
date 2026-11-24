"""Fase final: durante a investida os anjinhos não ficam presos às bordas (entregavam onde Deus estava fora da tela);
vão com ele (tools/t160_anjos_somem_na_investida.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnjosSomemNaInvestida(unittest.TestCase):
    def test_soltos_na_investida_da_final(self):
        d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        rosa = m.acha(m.acha(m.folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Anel rosa: amor')
        orbitas = [e for e in rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions'])]
        self.assertEqual(len(orbitas), 2)
        presa, solta = orbitas
        self.assertEqual(rosa['events'].index(solta), rosa['events'].index(presa) + 1, 'sobrescreve logo depois')
        self.assertIn('clamp(', tx(presa['actions']))
        c = [x['parameters'] for x in solta['conditions']]
        self.assertIn(['deus', 'fase', '=', '4'], c)
        self.assertTrue(any(p[:3] == ['deus', 'investindo', 'True'] for p in c))
        a = tx(solta['actions'])
        self.assertNotIn('clamp(', a)
        self.assertNotIn('"canalizador", "ang", "+"', a, 'o giro já foi feito no evento de cima')
        raio = '(deus.canal_orbita_raio + deus.canal_vaivem * deus.canal_vaivem_k * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'
        (s,) = [x for x in solta['actions'] if x['type']['value'] == 'SetXY']
        self.assertEqual(s['parameters'][2], f'deus.cx + cos(canalizador.ang) * canalizador.surgir * {raio} - canalizador.Width() / 2')
        self.assertEqual(s['parameters'][4], f'deus.cy + sin(canalizador.ang) * canalizador.surgir * {raio} - canalizador.Height() / 2')
        # parte de longe o bastante para nem o anjinho na ponta da órbita aparecer
        azul = m.acha(m.acha(m.folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Anel azul: investida')
        poe = [a['parameters'][3] for e in m.todos(azul['events']) for a in e.get('actions', [])
               if a['parameters'][:3] in (['deus', 'ox', '='], ['deus', 'oy', '=']) and 'investida_pos' in a['parameters'][3]]
        self.assertEqual(len(poe), 4)
        for x in poe:
            self.assertIn('deus.investida_longe + deus.canal_orbita_raio + deus.canal_vaivem)', x)
        for e in m.todos(azul['events']):
            a = [x['parameters'] for x in e.get('actions', [])]
            if any(p[:2] == ['deus', 'investida_pos'] for p in a):
                nomes = [p[1] for p in a]
                self.assertIn(['deus', 'cx', '=', 'CameraCenterX("", 0) + deus.ox'], a, 'sem um quadro no lugar antigo')
                self.assertIn(['deus', 'cy', '=', 'CameraCenterY("", 0) + deus.oy'], a)
                self.assertLess(nomes.index('oy'), nomes.index('cy'))


if __name__ == '__main__':
    unittest.main()
