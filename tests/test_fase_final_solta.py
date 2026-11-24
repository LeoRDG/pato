"""Fase final: Deus solta do pé da tela e segue o pato; na investida ele sai para mais longe e parte de um ponto
sorteado em volta da tela (só na fase final) (tools/t159_fase_final_solta.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class FaseFinalSolta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.corpo = m.acha(cls.deus['events'], 'Corpo')['events']
        cls.azul = m.acha(cls.deus['events'], 'Anel azul: investida')
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def acha(self, trecho):
        return [e for e in self.corpo if trecho in tx(e['actions'])]

    def test_preso_embaixo_so_antes_da_final(self):
        (preso,) = self.acha('CameraCenterY(\\"\\", 0) + deus.distancia_baixo')
        c = tx(preso['conditions'])
        self.assertIn('"deus", "fase", "<", "4"', c)
        self.assertIn('"deus", "morto", "False"', c)
        self.assertIn('"deus", "cx", "+", "(pato.CenterX() - deus.cx)', tx(preso['actions']))

    def test_final_segue_o_pato(self):
        (solto,) = self.acha('deus.final_distancia')
        c = tx(solto['conditions'])
        self.assertIn('"deus", "fase", "=", "4"', c)
        self.assertIn('"deus", "investindo", "False"', c)
        acts = {a['parameters'][1]: a['parameters'][2:] for a in solto['actions']}
        self.assertEqual(acts['final_d'], ['=', 'max(1, sqrt(pow(deus.cx - pato.CenterX(), 2) + pow(deus.cy - pato.CenterY(), 2)))'])
        k = 'min(1, deus.final_segue * TimeDelta())'
        # em relação à câmera (ox, oy): no mundo ele ficava para trás da câmera, que sobe rápido na fase final
        self.assertEqual(acts['ox'], ['+', f'(clamp(pato.CenterX() + (deus.cx - pato.CenterX()) / deus.final_d * deus.final_distancia, '
                                           f'{CX} - {CW} / 2 + deus.final_margem, {CX} + {CW} / 2 - deus.final_margem) - {CX} - deus.ox) * {k}'])
        self.assertEqual(acts['oy'], ['+', f'(clamp(pato.CenterY() + (deus.cy - pato.CenterY()) / deus.final_d * deus.final_distancia, '
                                           f'{CY} - {CH} / 2 + deus.final_margem, {CY} + {CH} / 2 - deus.final_margem) - {CY} - deus.oy) * {k}'])
        self.assertEqual(acts['cx'], ['=', f'{CX} + deus.ox'])
        self.assertEqual(acts['cy'], ['=', f'{CY} + deus.oy'])
        nomes = list(acts)
        self.assertLess(nomes.index('final_d'), nomes.index('ox'))
        self.assertLess(nomes.index('ox'), nomes.index('cx'))

    def test_entra_na_final_de_onde_esta(self):
        final = m.acha(self.deus['events'], 'Fase final')
        (ini,) = [e for e in final['events'] if '"deus", "final_iniciado", "True"' in tx(e['actions'])]
        a = [x['parameters'] for x in ini['actions']]
        self.assertIn(['deus', 'ox', '=', f'deus.cx - {CX}'], a)
        self.assertIn(['deus', 'oy', '=', f'deus.cy - {CY}'], a)

    def test_movimento_antes_da_pupila(self):
        """a pupila usa o cx/cy deste quadro; só a investida (que já põe a pupila) vem depois."""
        mov = [i for i, e in enumerate(self.corpo) if '"deus", "cx"' in tx(e['actions'])
               and '"deus", "investindo", "True"' not in tx(e['conditions'])]
        i_pup = next(i for i, e in enumerate(self.corpo) if '"deus", "pupila_ox", "+"' in tx(e['actions']))
        self.assertEqual(len(mov), 2)
        self.assertLess(max(mov), i_pup)
        self.assertNotIn('"deus", "cx"', tx(self.corpo[i_pup]['actions']))

    def test_investida_parte_de_ponto_sorteado(self):
        # + alcance dos anjinhos: t160 (test_anjos_somem_na_investida)
        longe = f'(sqrt(pow({CW} / 2, 2) + pow({CH} / 2, 2)) + deus.investida_longe + deus.canal_orbita_raio + deus.canal_vaivem)'
        evs = [e for e in m.todos(self.azul['events']) if '"deus", "etapa", "=", "\\"mira\\""' in tx(e.get('actions', []))]
        self.assertEqual(len(evs), 2, 'depois de sair por baixo e depois de cada corrida')
        for pai in evs:
            self.assertNotIn('investida_pos', tx(pai['actions']), 'nas outras fases parte de onde saiu')
            (e,) = [f for f in pai.get('events', []) if 'investida_pos' in tx(f['actions'])]
            self.assertEqual([c['parameters'] for c in e['conditions']], [['deus', 'fase', '=', '4']], 'só na fase final')
            acts = [a['parameters'] for a in e['actions'] if a['parameters'][:1] == ['deus']]
            nomes = [a[1] for a in acts]
            self.assertIn(['deus', 'investida_pos', '=', 'ToRad(RandomFloatInRange(0, 360))'], acts)
            self.assertIn(['deus', 'ox', '=', f'cos(deus.investida_pos) * {longe}'], acts)
            self.assertIn(['deus', 'oy', '=', f'sin(deus.investida_pos) * {longe}'], acts)
            self.assertLess(nomes.index('investida_pos'), nomes.index('ox'))
        for nome in ('investida_longe', 'investida_pos', 'final_distancia', 'final_margem', 'final_segue', 'final_d'):
            self.assertIn(nome, self.v)


if __name__ == '__main__':
    unittest.main()
