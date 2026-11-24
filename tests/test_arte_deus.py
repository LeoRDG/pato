"""Arte do chefe final: Deus, o olho de luz, canalizadores e efeitos (tools/arte_deus.py)."""
import os, unittest
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = 'assets/inimigos/ceu/deus'
P = 'assets/paraiso/deus'
CONTORNO = (36, 21, 14)

# pasta: (largura, altura, {animação: quadros})
ANIMS = {
    f'{D}/olho': (660, 660, {'idle': 8, 'piscar': 8, 'fechado': 1, 'carregar': 8, 'juizo': 12,
                             'juizo_falha': 6, 'dano': 2, 'fase': 10, 'morte': 14}),
    f'{D}/pupila': (180, 180, {'idle': 4, 'contrai': 6, 'dano': 2}),
    f'{D}/anel_ouro': (660, 660, {'idle': 1, 'cintila': 4, 'quebra': 8}),
    f'{D}/anel_azul': (660, 660, {'idle': 1, 'cintila': 4, 'quebra': 8}),
    f'{D}/anel_rosa': (660, 660, {'idle': 1, 'cintila': 4, 'quebra': 8}),
    f'{D}/aura': (780, 780, {'idle': 8}),
    f'{D}/escudo': (720, 720, {'idle': 6}),
    'assets/inimigos/ceu/canalizador': (128, 128, {'idle': 6, 'canalizar': 6, 'morte': 8}),
    f'{P}/checkpoint_empireo': (192, 192, {'idle': 8}),
    f'{P}/asas_pato': (60, 36, {'idle': 6, 'bater': 6}),
}
SOLTAS = {f'{P}/fragmento_1.png': (96, 96), f'{P}/fragmento_2.png': (126, 126), f'{P}/fragmento_3.png': (156, 156),
          f'{P}/feixe.png': (66, 66), f'{P}/halo.png': (258, 258),
          f'{P}/queima_borda.png': (192, 96), f'{P}/bg_espaco.png': (1026, 1026), f'{P}/bg_ceu_alto.png': (1026, 1026)}
OPACAS = {f'{P}/bg_espaco.png', f'{P}/bg_ceu_alto.png', f'{P}/feixe.png'}
# animações que mantêm o contorno escuro em todo quadro (os clarões de dano, fase e morte não)
COM_CONTORNO = {f'{D}/olho': ('idle', 'piscar', 'carregar'), f'{D}/pupila': ('idle', 'contrai'),
                f'{D}/anel_ouro': ('idle', 'cintila'), f'{D}/anel_azul': ('idle', 'cintila'),
                f'{D}/anel_rosa': ('idle', 'cintila'), 'assets/inimigos/ceu/canalizador': ('idle', 'canalizar')}


def quadros(pasta, anim, n):
    return [os.path.join(RAIZ, pasta, f'{anim}_{i:02d}.png') for i in range(n)]


class ArteDeus(unittest.TestCase):
    def test_quadros_e_tamanhos(self):
        for pasta, (w, h, anims) in ANIMS.items():
            for anim, n in anims.items():
                fs = quadros(pasta, anim, n)
                self.assertFalse(os.path.exists(os.path.join(RAIZ, pasta, f'{anim}_{n:02d}.png')), f'{pasta}/{anim} sobra')
                for f in fs:
                    im = Image.open(f)
                    self.assertEqual((im.size, im.mode), ((w, h), 'RGBA'), f)
                    self.assertEqual(im.getextrema()[3][0], 0, f'{f} sem transparência')
        for f, tam in SOLTAS.items():
            im = Image.open(os.path.join(RAIZ, f))
            self.assertEqual((im.size, im.mode), (tam, 'RGBA'), f)
            if f not in OPACAS:
                self.assertEqual(im.getextrema()[3][0], 0, f'{f} sem transparência')

    def test_paleta(self):
        for pasta, (w, h, anims) in ANIMS.items():
            for anim, n in anims.items():
                for f in quadros(pasta, anim, n):
                    cores = Image.open(f).getcolors(100000)
                    self.assertLessEqual(len(cores), 40, f)
                    if anim in COM_CONTORNO.get(pasta, ()):
                        self.assertIn(CONTORNO, {c[:3] for _, c in cores if c[3]}, f'{f} sem contorno')

    def test_piscar_fecha_no_meio(self):
        a = lambda f: sum(1 for _, c in Image.open(f).getcolors(100000) if c[3]) and \
            sum(n for n, c in Image.open(f).getcolors(100000) if c[3])
        fs = quadros(f'{D}/olho', 'piscar', 8)
        self.assertLess(a(fs[3]), a(fs[0]) * 0.8)
        self.assertLess(a(fs[4]), a(fs[7]) * 0.8)


if __name__ == '__main__':
    unittest.main()
