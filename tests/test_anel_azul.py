"""Anel azul: a investida. Deus sai da tela e investe contra o pato investida_total vezes (entre investida_min e
investida_max), cada vez por um caminho avisado antes, acelerando e saindo pelo outro lado; os raios giram mais
rápido quanto mais rápido ele vai (t141, refeito em tools/t155_investida.py)."""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

PD = 'PrimitiveDrawing::'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnelAzul(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.azul = m.acha(cls.deus['events'], 'Anel azul: investida')
        cls.evs = list(m.todos(cls.azul['events']))
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def com(self, trecho, onde='actions'):
        return [e for e in self.evs if trecho in tx(e.get(onde, []))]

    def test_piscar_saiu(self):
        self.assertIsNone(m.acha(self.deus['events'], 'Anel azul: piscar'))
        t = tx(self.azul)
        for velho in ('luz_halo', 'halo_marca', 'luz_ambiente_escuro'):
            self.assertNotIn(velho, t)
        esc = tx(m.acha(self.deus['events'], 'Escolha do golpe'))
        self.assertIn('"deus", "golpe", "=", "\\"investida\\""', esc)
        self.assertNotIn('\\"piscar\\"', esc)

    def test_etapas(self):
        t = tx(self.azul)
        for etapa in ('sai', 'mira', 'trava', 'corre', 'volta'):
            self.assertIn(f'\\"{etapa}\\"', t)
        (comeca,) = self.com('"deus", "etapa", "=", "\\"sai\\""')
        a = tx(comeca['actions'])
        self.assertIn('"deus", "investindo", "True"', a)
        self.assertIn('"deus", "investida_total", "=", "RandomInRange(deus.investida_min, deus.investida_max)"', a)
        self.assertGreaterEqual(self.v['investida_min'], 4)
        self.assertLessEqual(self.v['investida_max'], 5)

    def test_corpo_segue_a_investida(self):
        corpo = m.acha(self.deus['events'], 'Corpo')
        (sob,) = [e for e in corpo['events'] if '"deus", "investindo", "True"' in tx(e['conditions'])]
        a = tx(sob['actions'])
        self.assertIn('"deus", "cx", "=", "CameraCenterX(\\"\\", 0) + deus.ox"', a)
        self.assertIn('"deus", "cy", "=", "CameraCenterY(\\"\\", 0) + deus.oy"', a)
        self.assertIn('"deus", "px", "="', a, 'a pupila vai junto, sem atraso')
        pos = next(i for i, e in enumerate(corpo['events']) if '"SetXY"}, "parameters": ["deus_olho"' in tx(e['actions']))
        self.assertLess(corpo['events'].index(sob), pos, 'antes de posicionar as partes')

    def test_pupila_relativa_ao_centro(self):
        """suavizar a posição no mundo deixava a pupila para trás quando o corpo voltava rápido da investida."""
        corpo = m.acha(self.deus['events'], 'Corpo')['events']
        a = tx(next(e['actions'] for e in corpo if '"deus", "pupila_ox", "+"' in tx(e['actions'])))
        self.assertIn('"deus", "pupila_ox", "+", "(cos(deus.olhar_ang) * deus.pupila_alcance - deus.pupila_ox) * min(1, deus.pupila_suave * TimeDelta())"', a)
        self.assertIn('"deus", "pupila_oy", "+", "(sin(deus.olhar_ang) * deus.pupila_alcance - deus.pupila_oy)', a)
        self.assertIn('"deus", "px", "=", "deus.cx + deus.pupila_ox"', a)
        self.assertIn('"deus", "py", "=", "deus.cy + deus.pupila_oy"', a)
        self.assertLess(a.index('pupila_ox", "+"'), a.index('"deus", "px", "="'))

    def test_caminho_avisado(self):
        t = self.o['investida_trilha']
        self.assertEqual(t['type'], 'PrimitiveDrawing::Drawer')
        self.assertIn('Glow', [e['effectType'] for e in t['effects']])
        linhas = self.com(f'"{PD}LineV2"}}, "parameters": ["investida_trilha"')
        self.assertTrue(linhas)
        txt = tx(linhas)
        self.assertIn('deus.investida_raio * 2', txt, 'a faixa mostra a largura que machuca')
        self.assertIn('\\"mira\\"', tx([e['conditions'] for e in linhas]) + tx([c for e in self.evs if any(l in e.get('events', []) for l in linhas) for c in e['conditions']]))

    def test_corrida_acelera_e_fere(self):
        (corre,) = [e for e in self.evs if '"deus", "investida_v", "="' in tx(e.get('actions', [])) and 'investida_acel' in tx(e['actions'])]
        self.assertIn('min(deus.investida_vel_max, deus.investida_v + deus.investida_acel * TimeDelta())', tx(corre['actions']))
        (fere,) = self.com('"pato", "vida", "-", "deus.investida_dano"')
        c = tx(fere['conditions'])
        for s in ('"pato", "invencivel", "False"', '"pato", "morto", "False"', 'deus.investida_raio'):
            self.assertIn(s, c)

    def test_raios_aceleram(self):
        aura = tx(m.acha(self.deus['events'], 'Aura desenhada'))
        self.assertIn('"deus", "aura_raios_ang", "+", "deus.aura_giro * deus.aura_giro_mult * TimeDelta()"', aura)
        self.assertIn('"deus", "aura_giro_mult", "=", "1 + deus.investida_giro * deus.investida_v / deus.investida_vel_max"', tx(self.azul))
        self.assertEqual(self.v['aura_giro_mult'], 1)

    def test_rastro_de_particulas(self):
        self.assertEqual(self.o['investida_rastro']['type'], 'ParticleSystem::ParticleEmitter')
        self.assertTrue(self.com('"Create"}, "parameters": ["", "investida_rastro"'))
        self.assertTrue(self.com('"Delete"}, "parameters": ["investida_rastro"'))

    def test_limpeza(self):
        evs = list(m.todos(self.deus['events']))
        troca = next(e for e in m.todos(m.acha(self.deus['events'], 'Fases')['events'])
                     if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
        morte = next(e for e in evs if '"deus", "morte_iniciada", "True"' in tx(e.get('actions', [])))
        for e in (troca, morte):
            a = tx(e['actions'])
            self.assertIn('"deus", "investindo", "False"', a)
            self.assertIn('"deus", "aura_giro_mult", "=", "1"', a)
            self.assertIn('"Delete"}, "parameters": ["investida_rastro"', a)

    def test_variaveis(self):
        for nome in set(re.findall(r'deus\.([a-z_0-9]+)\b(?!\()', tx(self.azul))):
            self.assertIn(nome, self.v, nome)


if __name__ == '__main__':
    unittest.main()
