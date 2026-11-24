"""Juízo refeito: Deus para embaixo no meio da tela, suga as estrelas, abre o buraco negro (direita, quase invisível)
e o branco (esquerda, teleporta o pato para o negro) e varre a tela com um feixe que mata com um toque, girando 180°
anti-horário a partir da direita; as estrelas voltam por onde o feixe passou. Recarga de juizo_recarga segundos
(tools/t164_juizo_feixe.py)."""
import json, os, sys, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class JuizoFeixe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.j = m.acha(cls.deus['events'], 'Juízo: o feixe')
        cls.est = m.acha(cls.deus['events'], 'Estrelas')
        cls.evs = list(m.todos(cls.j['events']))
        cls.v = {x['name']: x['value'] for x in cls.o['deus']['variables']}

    def com(self, trecho, onde='actions', evs=None):
        return [e for e in (evs or self.evs) if trecho in tx(e.get(onde, []))]

    # ---------- o golpe antigo saiu ----------
    def test_juizo_antigo_saiu(self):
        rosa = m.acha(self.deus['events'], 'Anel rosa: amor')
        t = tx(rosa)
        self.assertNotIn('\\"juizo\\"', t)
        self.assertNotIn('juizo_carga', t)
        self.assertNotIn('juizo_avisou', t)
        (linha,) = [e for e in rosa['events'] if '"PrimitiveDrawing::LineV2"' in tx(e['actions'])]
        (l,) = [a for a in linha['actions'] if a['type']['value'] == 'PrimitiveDrawing::LineV2']
        self.assertEqual(l['parameters'][5], 'deus.laco_espessura')

    # ---------- etapas ----------
    def test_etapas_em_ordem(self):
        t = tx(self.j)
        for a, b, tempo in (('vai', 'suga', 'deus.juizo_ir'), ('suga', 'aviso', 'deus.juizo_sugar'),
                            ('aviso', 'feixe', 'deus.juizo_aviso'), ('feixe', 'fecha', 'deus.juizo_varrer')):
            (e,) = [e for e in self.evs if f'"deus", "etapa", "=", "\\"{b}\\""' in tx(e.get('actions', []))]
            self.assertIn(tempo, tx(e['conditions']), b)
        (fim,) = self.com('"deus", "estado", "=", "\\"fim_golpe\\""')
        a = tx(fim['actions'])
        self.assertIn('"deus", "juizo_volta_em", "=", "TimeFromStart() + deus.juizo_recarga"', a)
        self.assertIn('"deus", "juizo_ativo", "False"', a)
        self.assertIn('deus.juizo_fecha', tx(fim['conditions']))

    def test_para_embaixo_no_meio(self):
        corpo = m.acha(self.deus['events'], 'Corpo')['events']
        (para,) = [e for e in corpo if '"deus", "juizo_ativo", "True"' in tx(e['conditions'])]
        acts = {a['parameters'][1]: a['parameters'][2:] for a in para['actions']}
        k = 'min(1, deus.juizo_ir_vel * TimeDelta())'
        self.assertEqual(acts['ox'], ['+', f'(0 - deus.ox) * {k}'])
        self.assertEqual(acts['oy'], ['+', f'({CH} / 2 - deus.juizo_baixo - deus.oy) * {k}'])
        self.assertEqual(acts['cx'], ['=', f'{CX} + deus.ox'])
        i_pup = next(i for i, e in enumerate(corpo) if '"deus", "pupila_ox", "+"' in tx(e['actions']))
        self.assertLess(corpo.index(para), i_pup)
        (comeca,) = self.com('"deus", "etapa", "=", "\\"vai\\""')
        a = [x['parameters'] for x in comeca['actions']]
        self.assertIn(['deus', 'juizo_ativo', 'True', ''], a)
        self.assertIn(['deus', 'ox', '=', f'deus.cx - {CX}'], a)
        self.assertIn(['deus', 'oy', '=', f'deus.cy - {CY}'], a)

    def test_recarga_na_escolha(self):
        esc = m.acha(self.deus['events'], 'Escolha do golpe')
        sorteio = next(e for e in m.todos(esc['events']) if any(
            '"deus", "golpe", "=", "\\"juizo\\""' in tx(f.get('actions', [])) for f in e.get('events', [])))
        filhos = sorteio['events']
        (rec,) = [f for f in filhos if 'juizo_volta_em' in tx(f['conditions'])]
        c = tx(rec['conditions'])
        self.assertIn('"deus", "sorteio", "=", "4"', c)
        self.assertIn('"TimeFromStart()", "<", "deus.juizo_volta_em"', c)
        self.assertIn('"deus", "sorteio", "=", "mod(deus.sorteio, deus.golpes_max) + 1"', tx(rec['actions']))
        mapa = next(f for f in filhos if '"deus", "golpe", "=", "\\"juizo\\""' in tx(f['actions']))
        self.assertLess(filhos.index(rec), filhos.index(mapa))
        self.assertEqual(self.v['juizo_recarga'], 30)

    # ---------- feixe ----------
    def test_feixe_varre_180_anti_horario(self):
        (gira,) = self.com('"deus", "juizo_ang", "=", "-180')
        self.assertIn('"deus", "juizo_ang", "=", "-180 * min(1, deus.ObjectTimerElapsedTime(\\"golpe\\") / deus.juizo_varrer)"',
                      tx(gira['actions']))
        self.assertIn('"deus", "etapa", "=", "\\"feixe\\""', tx(gira['conditions']))
        linhas = self.com('"PrimitiveDrawing::LineV2"}, "parameters": ["juizo_feixe"')
        self.assertTrue(linhas)
        self.assertIn('deus.juizo_largura', tx(linhas))
        self.assertEqual(self.o['juizo_feixe']['type'], 'PrimitiveDrawing::Drawer')
        self.assertEqual({e['effectType'] for e in self.o['juizo_feixe']['effects']}, {'Glow', 'AdvancedBloom'})

    def test_feixe_mata_pato_e_anjos(self):
        (pato,) = self.com('"pato", "vida", "=", "0"')
        c = tx(pato['conditions'])
        self.assertIn('"pato", "morto", "False"', c)
        self.assertIn('deus.juizo_largura / 2 + deus.juizo_folga', c)
        self.assertNotIn('invencivel', c, 'mata mesmo com invencibilidade')
        anjo = next(e for e in self.evs if e.get('object') == 'canalizador')
        self.assertIn('"canalizador", "vida", "=", "0"', tx(anjo))

    # ---------- buracos ----------
    def test_buracos(self):
        (abre,) = self.com('"deus", "juizo_branco_ativo", "True"')
        self.assertIn('"deus", "etapa", "=", "\\"suga\\""', tx(abre['actions']))
        (revela,) = self.com('"deus", "juizo_revelado", "True"')
        c = tx(revela['conditions'])
        # só depois que o feixe saiu inteiro de cima do negro (senão quem entra no branco logo no aviso morre)
        self.assertIn('"deus.juizo_ang", "<", "deus.juizo_negro_ang - deus.juizo_negro_livre"', c)
        (livre,) = self.com('"deus", "juizo_negro_livre", "="')
        t = tx(livre['actions'])
        for n in ('deus.juizo_largura / 2', 'deus.juizo_folga', 'deus.juizo_buraco_raio'):
            self.assertIn(n, t)
        (fecha_branco,) = self.com('"deus", "juizo_branco_ativo", "False"', evs=[e for e in self.evs if 'juizo_branco_ang' in tx(e.get('conditions', []))])
        self.assertIn('"deus.juizo_ang", "<", "deus.juizo_branco_ang"', tx(fecha_branco['conditions']))
        (tele,) = self.com('"SetXY"}, "parameters": ["pato"')
        c = tx(tele['conditions'])
        self.assertIn('"deus", "juizo_branco_ativo", "True"', c)
        self.assertIn('deus.juizo_buraco_raio', c)
        (vai,) = [x['parameters'] for x in tele['actions'] if x['type']['value'] == 'SetXY']
        self.assertIn('deus.juizo_negro_dx', vai[2], 'vai para o buraco negro')
        self.assertIn('deus.juizo_negro_dy', vai[4])
        self.assertGreater(self.v['juizo_negro_dx'], 0, 'negro à direita')
        self.assertLess(self.v['juizo_branco_dx'], 0, 'branco à esquerda')
        self.assertEqual(self.o['juizo_buracos']['type'], 'PrimitiveDrawing::Drawer')
        # o negro: disco preto sem halo (sem Glow), num desenho à parte
        self.assertEqual(self.o['juizo_negro']['type'], 'PrimitiveDrawing::Drawer')
        self.assertEqual(self.o['juizo_negro']['effects'], [], 'sem halo')
        self.assertLess(self.v['juizo_negro_vis'], 0.1, 'quase invisível')
        # o branco não pulsa
        self.assertNotIn('pulso', tx(self.j))
        self.assertNotIn('juizo_branco_pulso', self.v)

    def test_lentes(self):
        """o negro curva o espaço: um BulgePinch no fundo e na camada do jogo, seguindo o buraco. Só ele: no runtime as
        BulgePinch dividem o mesmo centro."""
        cena = m.cena(self.d, 'Paraiso')
        for camada in ('Fundo',):  # só no fundo desde a t165
            (l,) = [x for x in cena['layers'] if x['name'] == camada]
            ef = {e['name']: e for e in l['effects']}
            self.assertNotIn('Lente branca', ef)
            for nome in ('Lente negra',):
                self.assertEqual(ef[nome]['effectType'], 'BulgePinch', (camada, nome))
                self.assertEqual(ef[nome]['doubleParameters']['strength'], 0, 'desligada fora do Juízo')
        t = tx(self.j)
        for camada in ('\\"Fundo\\"',):
            for nome, forca in (('Lente negra', 'deus.juizo_lente_negra'),):
                self.assertIn(f'"SetLayerEffectParameter"}}, "parameters": ["", "{camada}", "\\"{nome}\\"", "\\"strength\\"", "{forca}"', t)
        self.assertIn('(CameraWidth(\\"\\", 0) / 2 + deus.juizo_negro_dx) / CameraWidth(\\"\\", 0)', t)
        self.assertGreater(self.v['juizo_lente_negra'], 0)
        # o branco é luz: Glow e bloom, como o feixe
        self.assertEqual({e['effectType'] for e in self.o['juizo_buracos']['effects']}, {'Glow', 'AdvancedBloom'})

    # ---------- estrelas ----------
    def test_estrelas_objetos(self):
        e = self.o['estrela']
        self.assertEqual(e['type'], 'Sprite')
        for n in ('hx', 'hy', 'x_', 'y_', 'v', 'atraso', 'fase', 'brilho', 'est', 'op', 'id'):
            self.assertIn(n, {x['name'] for x in e['variables']}, n)
        self.assertEqual(self.o['estrela_rastro']['type'], 'ParticleSystem::ParticleEmitter')
        cria = self.com('"Create"}, "parameters": ["", "estrela"', evs=list(m.todos(self.est['events'])))
        self.assertEqual(len(cria), 1)
        self.assertIn('"\\"Fundo\\""', tx(cria[0]['actions']))

    def test_estrelas_sugadas_e_devolvidas(self):
        evs = list(m.todos(self.est['events']))
        (sai,) = self.com('"estrela", "est", "=", "\\"vai\\""', evs=evs)
        self.assertIn('"deus", "etapa", "=", "\\"suga\\""', tx(sai['conditions']) + tx([c for e in evs if sai in e.get('events', []) for c in e['conditions']]))
        self.assertTrue(self.com('"Create"}, "parameters": ["", "estrela_rastro"', evs=evs))
        (chega,) = self.com('"estrela", "est", "=", "\\"some\\""', evs=evs)
        self.assertIn('deus.juizo_sugar_chega', tx(chega['conditions']))
        volta = self.com('"estrela", "est", "=", "\\"volta\\""', evs=evs)
        self.assertTrue(any('deus.juizo_ang' in tx(e['conditions']) for e in volta), 'voltam por onde o feixe passou')

    def test_ceu_sem_estrelas_pintadas(self):
        import numpy as np
        from PIL import Image
        for n in ('bg_espaco', 'bg_ceu_alto'):
            a = np.array(Image.open(os.path.join(RAIZ, f'assets/paraiso/deus/{n}.png')).convert('RGB')).astype(int)
            lum = a.sum(axis=2)
            self.assertLess(lum.max() - np.median(lum), 120, n + ': as estrelas agora são objetos')

    def test_limpeza(self):
        troca = next(e for e in m.todos(m.acha(self.deus['events'], 'Fases')['events'])
                     if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
        morte = next(e for e in m.acha(self.deus['events'], 'Morte')['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
        for e in (troca, morte):
            a = tx(e['actions'])
            self.assertIn('"deus", "juizo_ativo", "False"', a)
            for obj in ('juizo_feixe', 'juizo_buracos', 'juizo_negro', 'estrela_rastro'):
                self.assertIn(f'"Delete"}}, "parameters": ["{obj}"', a)


if __name__ == '__main__':
    unittest.main()
