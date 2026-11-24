"""Anel de ouro: o pulso de Deus e as sombras dos fragmentos (t140, refeito em tools/t151_pulso.py).

Deus canaliza (partículas convergindo para o olho, cada vez mais rápidas), as pedras descem devagar sem parar, e ele
solta um pulso radial (anel desenhado com Glow) que quebra as pedras; o pato só se salva atrás de uma pedra.
"""
import json, os, re, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m
import gd_luz as g

EMISSOR = 'ParticleSystem::ParticleEmitter'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AnelOuro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.ouro = m.acha(cls.deus['events'], 'Anel de ouro: o pulso')
        cls.frag = m.acha(cls.deus['events'], 'Fragmentos')
        cls.evs = list(m.todos(cls.ouro['events']))

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def com(self, trecho, onde='actions'):
        return [e for e in self.evs if trecho in tx(e.get(onde, []))]

    def test_sem_feixe_antigo(self):
        self.assertIsNone(m.acha(self.deus['events'], 'Anel de ouro: o olhar'))
        self.assertNotIn('feixe_olhar', tx(self.ouro))

    def test_etapas(self):
        o = tx(self.ouro)
        for etapa in ('carrega', 'pulso'):
            self.assertIn(f'\\"{etapa}\\"', o)
        self.assertIn('"deus", "golpe", "=", "\\"olhar\\""', o)
        self.assertIn('"deus", "estado", "=", "\\"fim_golpe\\""', o)
        self.assertIn(f'"{g.ACAO_RAIO_LUZ}"}}, "parameters": ["luz_olhar"', o, 'a luz cresce na carga: as pedras fazem sombra')
        (solta,) = self.com('"deus", "etapa", "=", "\\"pulso\\""')
        self.assertIn('"CompareObjectTimer"}, "parameters": ["deus", "\\"golpe\\"", ">", "deus.pulso_carga"', tx(solta))

    def test_pedras_descem_sem_parar_durante_a_carga(self):
        self.assertIn(g.COMP_SOMBRA, [b['type'] for b in self.o['fragmento']['behaviors']])
        cria = self.com('"Create"}, "parameters": ["", "fragmento"')
        self.assertGreaterEqual(len(cria), 2, 'um lote no começo e mais a cada fragmento_intervalo')
        t = tx(cria)
        self.assertIn('"fragmento", "vy", "=", "RandomFloatInRange(deus.fragmento_vel_min, deus.fragmento_vel_max)"', t)
        self.assertIn('\\"carrega\\"', tx([e for e in self.evs if any(c in e.get('events', []) for c in cria)] + cria))
        anda = tx(self.frag)
        self.assertIn('"SetY"}, "parameters": ["fragmento", "+", "(fragmento.vy - subida_vel) * TimeDelta()"', anda,
                      'vy é a velocidade na tela: descem sempre, mesmo se a subida acelerar')
        self.assertIn('"Delete"}, "parameters": ["fragmento"', anda)
        self.assertNotIn('fragmento_queda', tx(self.ouro), 'não param nem despencam no fim do golpe')

    def test_particulas_convergindo(self):
        c = self.o['conv_luz']
        self.assertEqual(c['type'], EMISSOR)
        self.assertEqual(c['tank'], -1)
        cria = self.com('"Create"}, "parameters": ["", "conv_luz"')
        self.assertTrue(cria)
        self.assertEqual(cria[0].get('repeatExpression'), 'deus.conv_qtd')
        guia = tx(self.com('"ParticleSystem::EmitterForceMax"}, "parameters": ["conv_luz"'))
        for s in ('deus.conv_vel_min', 'deus.conv_vel_max', 'deus.pulso_carga', 'ParticleSystem::ParticleLifeTimeMax',
                  'ParticleSystem::SetFlow', 'deus.conv_raio'):
            self.assertIn(s, guia + tx(self.ouro))
        self.assertTrue(self.com('"Delete"}, "parameters": ["conv_luz"'))

    def test_anel_desenhado_com_glow(self):
        a = self.o['pulso_anel']
        self.assertEqual(a['type'], 'PrimitiveDrawing::Drawer')
        self.assertIn('Glow', [e['effectType'] for e in a['effects']])
        self.assertTrue(a['clearBetweenFrames'])
        self.assertTrue(a['absoluteCoordinates'])
        self.assertIn('"PrimitiveDrawing::Circle"}, "parameters": ["pulso_anel", "deus.pulso_x", "deus.pulso_y", "deus.pulso_r"', tx(self.ouro))

    def test_carga_longa_e_pulso_que_ilumina(self):
        self.assertGreaterEqual(self.v('deus')['pulso_carga'], 6, 'tempo para as pedras descerem')
        glow = next(e for e in self.o['pulso_anel']['effects'] if e['effectType'] == 'Glow')
        self.assertGreaterEqual(glow['doubleParameters']['outerStrength'], 12)
        (cresce,) = self.com('"deus", "pulso_r", "+"')
        a = tx(cresce['actions'])
        self.assertIn(f'"{g.ACAO_RAIO_LUZ}"}}, "parameters": ["luz_olhar", "deus.pulso_r + deus.pulso_luz_margem"', a,
                      'a luz do olho acompanha o anel')
        self.assertIn('"luz_olhar", "deus.pulso_luz_cor"', tx(self.ouro))
        self.assertIn('AdvancedBloom', [e['effectType'] for e in self.o['pulso_anel']['effects']])
        (solta,) = self.com('"deus", "etapa", "=", "\\"pulso\\""')
        self.assertIn(f'"{g.ACAO_LUZ_AMBIENTE}"}}, "parameters": ["", "\\"Luz\\"", "deus.pulso_ambiente"]', tx(solta['actions']),
                      'o céu clareia enquanto o pulso passa')
        (fim,) = self.com('"deus", "estado", "=", "\\"fim_golpe\\""')
        self.assertIn(f'"{g.ACAO_LUZ_AMBIENTE}"}}, "parameters": ["", "\\"Luz\\"", "luz_ambiente_normal"]', tx(fim['actions']))

    def test_pulso_quebra_pedras(self):
        (quebra,) = [e for e in self.evs if e.get('type') == 'BuiltinCommonInstructions::ForEach' and e.get('object') == 'fragmento']
        self.assertIn('deus.pulso_r', tx(quebra['conditions']))
        a = tx(quebra['actions'])
        self.assertIn('"Create"}, "parameters": ["", "pedra_estilhaco"', a)
        self.assertIn('"Delete"}, "parameters": ["fragmento"', a)
        self.assertEqual(self.o['pedra_estilhaco']['type'], EMISSOR)

    def test_sombra_salva_o_pato(self):
        (sombra,) = [e for e in self.evs if '"pato", "na_sombra", "True"' in tx(e['actions'])]
        (ray,) = [x for x in sombra['conditions'] if x['type']['value'] == 'RaycastToPosition']
        self.assertFalse(ray['type'].get('inverted'), 'RaycastToPosition invertido é verdadeiro quando ACERTA')
        self.assertEqual(ray['parameters'][:5], ['fragmento', 'deus.pulso_x', 'deus.pulso_y', 'pato.CenterX()', 'pato.CenterY()'])
        (q,) = self.com('"pato", "vida", "-"')
        c = tx(q['conditions'])
        for s in ('"pato", "na_sombra", "False"', '"pato", "invencivel", "False"', '"pato", "morto", "False"'):
            self.assertIn(s, c)
        self.assertIn('"pato", "vida", "-", "deus.olhar_dano"', tx(q['actions']))
        pai = next(e for e in self.evs if q in e.get('events', []))
        self.assertIn('deus.pulso_r', tx(pai['conditions']), 'só quando a frente do pulso chega no pato')
        self.assertIn('"deus", "pulso_acertou", "False"', tx(pai['conditions']), 'uma vez por pulso')

    def test_limpeza(self):
        evs = list(m.todos(self.deus['events']))
        troca = next(e for e in m.todos(m.acha(self.deus['events'], 'Fases')['events'])
                     if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
        morte = next(e for e in evs if '"deus", "morte_iniciada", "True"' in tx(e.get('actions', [])))
        for e in (troca, morte):
            for obj in ('conv_luz', 'pulso_anel'):
                self.assertIn(f'"Delete"}}, "parameters": ["{obj}"', tx(e['actions']))

    def test_variaveis(self):
        texto = tx(self.ouro) + tx(self.frag)
        for obj in ('deus', 'fragmento', 'pato', 'conv_luz'):
            for nome in re.findall(r'(?<![\w])' + obj + r'\.([a-z_0-9]+)\b(?!\()', texto):
                self.assertIn(nome, self.v(obj), f'{obj}.{nome}')
        for cena in ('Paraiso', 'Teste'):
            self.assertLessEqual({'olhar_rx', 'olhar_ry'}, set(m.vars_cena(self.d, cena)))

    def test_numeros_em_variaveis(self):
        for e in m.todos([self.ouro, self.frag]):
            for a in e.get('conditions', []) + e.get('actions', []):
                for p in a['parameters']:
                    for n in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])', re.sub(r'"[^"]*"', '', p)):
                        self.assertIn(n, ('0', '1', '2', '3', '360'), f'{a["type"]["value"]} {a["parameters"]}')


if __name__ == '__main__':
    unittest.main()
