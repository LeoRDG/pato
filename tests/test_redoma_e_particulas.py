"""Redoma de invulnerável, partículas, sensação de subida e sem pulo no voo (tools/t149_redoma_e_particulas.py)."""
import json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

EMISSOR = 'ParticleSystem::ParticleEmitter'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class RedomaEParticulas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.evs = list(m.todos(cls.deus['events']))
        cls.cena = m.cena(cls.d, 'Paraiso')

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def ev_com(self, evs, acao):
        return [e for e in evs if acao in tx(e.get('actions', []))]

    def test_redoma_some_e_volta_com_a_invulnerabilidade(self):
        sinal = list(m.todos(m.acha(self.deus['events'], 'Sinal de vulnerável')['events']))
        (mostra,) = self.ev_com(sinal, '"deus", "escudo_visto", "True"')
        c = tx(mostra['conditions'])
        self.assertIn('"deus", "invulneravel", "True"', c)
        self.assertIn('"deus", "morto", "False"', c)
        self.assertIn('"Show"}, "parameters": ["deus_escudo"', tx(mostra['actions']))
        (quebra,) = self.ev_com(sinal, '"deus", "escudo_visto", "False"')
        self.assertIn('"deus", "invulneravel", "False"', tx(quebra['conditions']))
        a = tx(quebra['actions'])
        self.assertIn('"Hide"}, "parameters": ["deus_escudo"', a)
        self.assertIn('"Create"}, "parameters": ["", "escudo_quebra"', a)
        self.assertIn('escudo_opacidade', tx(sinal))

    def test_cor_da_redoma(self):
        """a arte é neutra (cinzas) e a cor vem de deus.escudo_cor, que dá para trocar no GDevelop (t153)."""
        self.assertIn('escudo_cor', self.v('deus'))
        sinal = tx(m.acha(self.deus['events'], 'Sinal de vulnerável'))
        self.assertIn('"ChangeColor"}, "parameters": ["deus_escudo", "deus.escudo_cor"]', sinal)
        a = np.array(Image.open(os.path.join(RAIZ, 'assets/inimigos/ceu/deus/escudo/idle_00.png')).convert('RGBA'))
        px = a[a[:, :, 3] > 0][:, :3].astype(int)
        self.assertLessEqual(int((px.max(1) - px.min(1)).max()), 12, 'só tons de cinza, para o tingimento funcionar')

    def test_redoma_segura_as_balas(self):
        bloqueia = [e for e in self.evs if '"CollisionNP"}, "parameters": ["projetil", "deus_escudo"' in tx(e.get('conditions', []))]
        self.assertTrue(bloqueia)
        tudo = tx(bloqueia)
        self.assertIn('"deus", "escudo_visto", "True"', tudo)
        self.assertIn('"Create"}, "parameters": ["", "escudo_faisca"', tudo)
        self.assertIn('"Delete"}, "parameters": ["projetil"', tudo)
        self.assertIn('"projetil", "boom", "True"', tudo, 'explosivos estouram na redoma')
        for a in self.o['deus_escudo']['animations']:
            for sp in a['directions'][0]['sprites']:
                self.assertTrue(sp['hasCustomCollisionMask'])
                self.assertGreaterEqual(len(sp['customCollisionMask'][0]), 8, 'redonda, não o retângulo')

    def test_redoma_deixa_ver_o_olho(self):
        a = np.array(Image.open(os.path.join(RAIZ, 'assets/inimigos/ceu/deus/escudo/idle_00.png')).convert('RGBA'))[:, :, 3] > 0
        h, w = a.shape
        yy, xx = np.mgrid[0:h, 0:w]
        meio = np.hypot(xx - w / 2, yy - h / 2) < w * 0.25
        self.assertLess(a[meio].mean(), 0.25)
        aro = np.abs(np.hypot(xx - w / 2, yy - h / 2) - w * 0.458) < w * 0.01
        self.assertGreater(a[aro].mean(), 0.9)

    def test_particulas(self):
        for n in ('escudo_faisca', 'escudo_quebra', 'deus_morte_luz', 'vento_subida'):
            self.assertEqual(self.o[n]['type'], EMISSOR, n)
        self.assertEqual(self.o['vento_subida']['rendererType'], 'Line')
        self.assertEqual(self.o['vento_subida']['tank'], -1)
        morte = m.acha(self.deus['events'], 'Morte')
        inicio = next(e for e in morte['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
        self.assertIn('"Create"}, "parameters": ["", "deus_morte_luz"', tx(inicio['actions']))

    def test_vento_da_subida(self):
        vento = m.acha(self.cena['events'], 'Vento da subida')
        t = tx(vento)
        self.assertIn('"Create"}, "parameters": ["", "vento_subida"', t)
        self.assertIn('"SetXY"}, "parameters": ["vento_subida"', t)
        fim = m.acha(self.cena['events'], 'Fim da luta')
        self.assertIn('"Delete"}, "parameters": ["vento_subida"', tx(fim))
        self.assertIn('luta_parallax_y', t, 'as nuvens do Fundo sobem mais rápido na luta')
        k = [e.get('name') for e in self.cena['events']]
        self.assertLess(k.index('Vento da subida'), k.index('Céu para o espaço'))
        for n in ('bg_ceu_alto', 'bg_espaco'):
            self.assertGreaterEqual(self.v(n)['parallax'], 0.3, n)

    def test_sem_pulo_no_voo(self):
        jog = list(m.todos(m.folha(self.d, 'Jogador')['events']))
        pulo = [e for e in jog if any(k in tx(e.get('conditions', []) + e.get('actions', [])) for k in
                                      ('SimulateJumpKey', 'SimulateDashKey', 'giroPulo', '"\\"Space\\""', '"Create"}, "parameters": ["", "cagada"'))]
        self.assertGreaterEqual(len(pulo), 8)
        for e in pulo:
            self.assertIn('"pato", "voando", "False"', tx(e['conditions']), tx(e['conditions'])[:200])
        comeca = m.acha(self.cena['events'], 'Começo da luta')
        self.assertIn('"pato", "voando", "True"', tx(comeca))
        self.assertIn('"pato", "voando", "False"', tx(m.acha(self.cena['events'], 'Fim da luta')))
        self.assertIn('voando', self.v('pato'))


if __name__ == '__main__':
    unittest.main()
