"""Aura de Deus só com efeitos: brilho de sol e raios pontudos girando desenhados num Shape Painter com Glow e bloom
(tools/t154_aura_efeitos.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

PD = 'PrimitiveDrawing::'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AuraEfeitos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.aura = m.acha(cls.deus['events'], 'Aura desenhada')
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def test_objeto_com_efeitos(self):
        a = self.o['deus_aura_luz']
        self.assertEqual(a['type'], 'PrimitiveDrawing::Drawer')
        self.assertTrue(a['clearBetweenFrames'])
        self.assertTrue(a['absoluteCoordinates'])
        tipos = {e['effectType']: e['name'] for e in a['effects']}
        self.assertIn('Glow', tipos)
        self.assertEqual(tipos.get('AdvancedBloom'), 'Brilho', 'mesmo nome do bloom da aura, para a luz por fase')
        bloom = next(e for e in a['effects'] if e['effectType'] == 'AdvancedBloom')
        self.assertGreater(bloom['doubleParameters']['padding'], 0, 'sem padding o bloom corta reto')

    def test_sprite_antigo_escondido(self):
        cria = tx(m.acha(self.deus['events'], 'Criação'))
        self.assertIn('"Hide"}, "parameters": ["deus_aura"', cria)
        self.assertIn('"Create"}, "parameters": ["", "deus_aura_luz"', cria)
        self.assertIn('"ChangePlan"}, "parameters": ["deus_aura_luz", "=", "deus.z_base + 0"', cria)

    def test_brilho_de_sol(self):
        t = tx(self.aura)
        self.assertGreaterEqual(t.count(f'"{PD}Circle"}}, "parameters": ["deus_aura_luz", "deus.cx", "deus.cy"'), 3, 'camadas')
        for nome in ('aura_raio', 'aura_pulso', 'aura_pulso_vel', 'aura_brilho_cor'):
            self.assertIn(f'deus.{nome}', t)
        self.assertIn('"SceneInstancesCount"}, "parameters": ["", "deus", ">", "0"', t)

    def test_raios_girando(self):
        (rep,) = [e for e in m.todos(self.aura['events']) if e.get('type') == 'BuiltinCommonInstructions::Repeat']
        self.assertEqual(rep['repeatExpression'], 'deus.aura_raios_qtd')
        r = tx(rep['actions'])
        self.assertNotIn('LineV2', r, 'linha grossa com glow parecia macarrão: os raios são triângulos')
        tipos = [a['type']['value'] for a in rep['actions']]
        self.assertEqual(tipos[:5], [PD + 'BeginFillPath', PD + 'PathLineTo', PD + 'PathLineTo', PD + 'closePath', PD + 'EndFillPath'])
        self.assertIn('deus.aura_raios_base', r, 'largura da base do triângulo')
        self.assertIn('deus.aura_raios_ang', r)
        self.assertIn('mod(deus.i, 2)', r, 'raios longos e curtos alternados')
        self.assertIn('"deus", "aura_raios_ang", "+", "deus.aura_giro * TimeDelta()"', tx(self.aura))

    def test_luz_por_fase_e_limpeza(self):
        evs = list(m.todos(self.deus['events']))
        for k in range(1, 5):
            self.assertTrue(any(f'"deus_aura_luz", "Effect", "\\"Brilho\\"", "\\"bloomScale\\"", "deus.bloom_{k}"' in tx(e.get('actions', []))
                                for e in evs), k)
        apagam_aura = [e for e in evs if '"Delete"}, "parameters": ["deus_aura"' in tx(e.get('actions', []))]
        self.assertTrue(apagam_aura)
        for e in apagam_aura:
            self.assertIn('"Delete"}, "parameters": ["deus_aura_luz"', tx(e['actions']))

    def test_variaveis_existem(self):
        for nome in set(re.findall(r'deus\.([a-z_0-9]+)\b(?!\()', tx(self.aura))):
            self.assertIn(nome, self.v, nome)


if __name__ == '__main__':
    unittest.main()
