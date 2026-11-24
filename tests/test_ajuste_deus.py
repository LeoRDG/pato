"""Ajustes do chefe Deus depois de jogar: corpo menor, sinal claro de vulnerável (os fragmentos do golpe agora estão em test_anel_ouro)
(tools/t148_ajuste_deus.py, tools/arte_deus.py)."""
import json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m

PARTES = ('deus_aura', 'deus_anel_ouro', 'deus_anel_azul', 'deus_anel_rosa', 'deus_olho', 'deus_escudo', 'deus')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


class AjusteDeus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.nomes = [e.get('name') for e in cls.deus['events']]

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def g(self, nome):
        return m.acha(self.deus['events'], nome)

    def test_corpo_menor(self):
        cria = m.acha(self.deus['events'], 'Criação')['events'][0]
        a = tx(cria['actions'])
        for p in PARTES:
            self.assertIn(f'"ScalableCapability::ScalableBehavior::SetValue"}}, "parameters": ["{p}", "Scale", "=", "deus.corpo_escala"]', a)
        v = self.v('deus')
        self.assertLess(v['corpo_escala'], 1)
        self.assertLessEqual(v['distancia_baixo'] + 100 + v['canal_orbita_raio'], self.d['properties']['windowHeight'] / 2)

    def test_sinal_de_vulneravel(self):
        self.assertIn('Glow', [e['effectType'] for e in self.o['deus']['effects'] if e['name'] == 'Aberta'])
        sinal = self.g('Sinal de vulnerável')
        self.assertEqual(self.nomes.index('Sinal de vulnerável'), self.nomes.index('Dano na pupila') + 1)
        aberta = next(e for e in sinal['events'] if '"deus", "invulneravel", "False"' in tx(e['conditions']))
        fechada = next(e for e in sinal['events'] if '"deus", "invulneravel", "True"' in tx(e['conditions']))
        a, f = tx(aberta['actions']), tx(fechada['actions'])
        self.assertIn('EnableEffect"}, "parameters": ["deus", "Effect", "\\"Aberta\\"", "yes"]', a)
        self.assertIn('EnableEffect"}, "parameters": ["deus", "Effect", "\\"Aberta\\"", "no"]', f)
        self.assertIn('"ChangeColor"}, "parameters": ["deus", "deus.cor_aberta"]', a)
        self.assertIn('"ChangeColor"}, "parameters": ["deus", "deus.cor_fechada"]', f)
        self.assertIn('"TiledSpriteObject::SetColor"}, "parameters": ["hud_boss_fill", "deus.barra_cor_aberta"]', a)
        self.assertIn('"TiledSpriteObject::SetColor"}, "parameters": ["hud_boss_fill", "deus.barra_cor_fechada"]', f)
        self.assertIn('"deus", "Effect", "\\"Aberta\\"", "\\"outerStrength\\""', a)
        for nome in ('cor_aberta', 'cor_fechada', 'barra_cor_aberta', 'barra_cor_fechada', 'brilho_forca', 'brilho_pulso'):
            self.assertIn(nome, self.v('deus'))

    def test_mascara_dos_fragmentos_bate_com_a_arte(self):
        for a in self.o['fragmento']['animations']:
            sp = a['directions'][0]['sprites'][0]
            opaco = np.array(Image.open(os.path.join(RAIZ, sp['image'])).convert('RGBA'))[:, :, 3] > 0
            h, w = opaco.shape
            for p in sp['customCollisionMask'][0]:
                x, y = int(p['x']), int(p['y'])
                viz = opaco[max(0, y - 4):min(h, y + 4), max(0, x - 4):min(w, x + 4)]
                self.assertTrue(viz.any(), f'{a["name"]} ponto {x},{y} longe da pedra')


if __name__ == '__main__':
    unittest.main()
