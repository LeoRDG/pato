"""Correções visuais do chefe Deus vistas no jogo rodando (tools/t147_visual_deus.py, tools/arte_deus.py)."""
import glob, json, os, sys, unittest
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import gd_mig as m


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def opacos(caminho):
    return int((np.array(Image.open(caminho).convert('RGBA'))[:, :, 3] > 0).sum())


class VisualDeus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.o = {x['name']: x for x in cls.d['objects']}
        cls.deus = m.acha(m.folha(cls.d, 'InimigosParaiso')['events'], 'Deus')
        cls.evs = list(m.todos(cls.deus['events']))

    def v(self, obj):
        return {x['name']: x['value'] for x in self.o[obj]['variables']}

    def test_raios_do_olho_finos(self):
        """os raios de carregar/juízo eram blocos brancos maciços em volta do olho inteiro."""
        olho = os.path.join(RAIZ, 'assets/inimigos/ceu/deus/olho')
        base = opacos(os.path.join(olho, 'idle_00.png'))
        for f in glob.glob(os.path.join(olho, 'carregar_*.png')) + glob.glob(os.path.join(olho, 'juizo_*.png')):
            self.assertLess(opacos(f) - base, 20000, os.path.basename(f))

    def test_fragmentos_com_mascara_justa(self):
        """o obstáculo de luz usa a máscara de colisão: retângulo inteiro fazia sombra e caixa clara em volta da pedra."""
        for a in self.o['fragmento']['animations']:
            for sp in a['directions'][0]['sprites']:
                self.assertTrue(sp['hasCustomCollisionMask'], a['name'])
                (poli,) = sp['customCollisionMask']
                self.assertGreaterEqual(len(poli), 5)
                w, h = Image.open(os.path.join(RAIZ, sp['image'])).size
                xs, ys = [p['x'] for p in poli], [p['y'] for p in poli]
                self.assertTrue(min(xs) > 0 or min(ys) > 0 or max(xs) < w or max(ys) < h, 'não é o retângulo inteiro')
                self.assertTrue(0 <= min(xs) and max(xs) <= w and 0 <= min(ys) and max(ys) <= h)

    def test_halo_visivel_marca_a_zona_segura(self):
        self.assertIn('halo_marca', self.o)
        nasce = next(e for e in self.evs if '"Create"}, "parameters": ["", "luz_halo"' in tx(e.get('actions', [])))
        a = tx(nasce['actions'])
        self.assertIn('"Create"}, "parameters": ["", "halo_marca"', a)
        self.assertIn('SetWidth"}, "parameters": ["halo_marca", "Resizable", "=", "deus.halo_raio * 2"', a)
        self.assertIn('SetHeight"}, "parameters": ["halo_marca", "Resizable", "=", "deus.halo_raio * 2"', a)
        self.assertIn('"luz_halo", "id", "=", "deus.halo_seq"', a)
        self.assertIn('"halo_marca", "id", "=", "deus.halo_seq"', a)
        segue = next(e for e in self.evs if e.get('object') == 'halo_marca')
        self.assertIn('"luz_halo", "id", "=", "halo_marca.id"', tx(segue['conditions']))
        self.assertIn('"SetXY"}, "parameters": ["halo_marca"', tx(segue['actions']))
        apaga = [e for e in self.evs if '"Delete"}, "parameters": ["luz_halo"' in tx(e.get('actions', []))]
        self.assertGreaterEqual(len(apaga), 3, 'fim do piscar, troca de fase, morte')
        for e in apaga:
            self.assertIn('"Delete"}, "parameters": ["halo_marca"', tx(e['actions']))
        for nome in ('halo_seq', 'halo_marca_opacidade'):
            self.assertIn(nome, self.v('deus'))
        self.assertIn('id', self.v('halo_marca'))
        self.assertIn('id', self.v('luz_halo'))

    def test_aneis_de_luz_maiores(self):
        for g in ('Três anéis', 'Fase final'):
            cria = [e for e in m.todos(m.acha(self.deus['events'], g)['events'])
                    if '"Create"}, "parameters": ["", "projetil_inimigo"' in tx(e.get('actions', []))]
            self.assertTrue(cria, g)
            for e in cria:
                self.assertIn('"ScalableCapability::ScalableBehavior::SetValue"}, "parameters": ["projetil_inimigo", "Scale", "=", "deus.aneis_escala"]',
                              tx(e['actions']))
        self.assertIn('aneis_escala', self.v('deus'))

    def test_deus_e_canalizadores_na_tela(self):
        """com o centro 330 abaixo e órbita de 400, metade dos canalizadores ficava fora da tela, atrás da borda."""
        v = self.v('deus')
        meia_altura = self.d['properties']['windowHeight'] / 2
        atraso = 100  # Deus sobe suavizado e fica uns 80 px atrás da câmera
        self.assertLessEqual(v['distancia_baixo'] + atraso + v['canal_orbita_raio'], meia_altura)


if __name__ == '__main__':
    unittest.main()
