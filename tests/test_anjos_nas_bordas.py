"""Os anjinhos vão e voltam para longe, até as bordas da tela, e o laço deles tem a cor da redoma (tools/t158_anjos_nas_bordas.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnjosNasBordas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.rosa = m.acha(deus['events'], 'Anel rosa: amor')
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def test_vao_para_fora_ate_a_borda(self):
        orbita = next(e for e in self.rosa['events'] if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']))  # a presa (a solta é da t160)
        (s,) = [a for a in orbita['actions'] if a['type']['value'] == 'SetXY']
        raio = '(deus.canal_orbita_raio + deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'
        self.assertEqual(s['parameters'][2],
                         f'clamp(deus.cx + cos(canalizador.ang) * canalizador.surgir * {raio}, {CX} - {CW} / 2 + deus.canal_margem, {CX} + {CW} / 2 - deus.canal_margem) - canalizador.Width() / 2')
        self.assertEqual(s['parameters'][4],
                         f'clamp(deus.cy + sin(canalizador.ang) * canalizador.surgir * {raio}, {CY} - {CH} / 2 + deus.canal_margem, {CY} + {CH} / 2 - deus.canal_margem) - canalizador.Height() / 2')
        self.assertGreaterEqual(self.v['canal_vaivem'], 500, 'chega perto das bordas')
        self.assertIn('canal_margem', self.v)

    def test_laco_da_cor_da_redoma(self):
        (cria,) = [e for e in self.rosa['events'] if '"Create"}, "parameters": ["", "laco_amor"' in tx(e['actions'])]
        a = tx(cria['actions'])
        self.assertIn('"PrimitiveDrawing::OutlineColor"}, "parameters": ["laco_amor", "deus.escudo_cor"]', a)
        self.assertIn('"EffectCapability::EffectBehavior::SetEffectStringParameter"}, "parameters": ["laco_amor", "Effect", "\\"Effect\\"", "\\"color\\"", "deus.escudo_cor"]', a)


if __name__ == '__main__':
    unittest.main()
