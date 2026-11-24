"""Tela de carregamento com a jornada do jogo (tools/t185_tela_carregamento.py)."""
import json, os, unittest
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TelaCarregamento(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.tela = cls.d['properties']['loadingScreen']

    def test_fundo_da_tela_de_carregamento(self):
        nome = self.tela['backgroundImageResourceName']
        (r,) = [r for r in self.d['resources']['resources'] if r['name'] == nome]
        self.assertEqual((r['kind'], r['file']), ('image', 'assets/splash/carregando.jpg'))
        self.assertTrue(r['smoothed'], 'imagem pintada: suaviza ao escalar')
        w, h = Image.open(os.path.join(RAIZ, r['file'])).size
        p = self.d['properties']
        # mais larga que 16:9: em 16:9 corta só cenário dos lados; em telas largas (~2.6:1) quase não corta em cima
        self.assertTrue(p['windowWidth'] / p['windowHeight'] < w / h < 2.4, w / h)
        self.assertGreaterEqual(h, 1080, 'em tela cheia comum ela é reduzida, não ampliada (fica nítida)')
        # a imagem é a primeira coisa baixada: precisa ser leve
        self.assertLess(os.path.getsize(os.path.join(RAIZ, r['file'])), 600 * 1024)

    def test_barra_sobre_faixa_escura(self):
        im = Image.open(os.path.join(RAIZ, 'assets/splash/carregando.jpg')).convert('L')
        w, h = im.size
        k = h / 1080                      # a barra do GDevelop fica 90-110 px acima da borda de baixo (tela de 1080)
        faixa = im.crop((w // 2 - int(110 * k), h - int(120 * k), w // 2 + int(110 * k), h - int(80 * k)))
        self.assertLess(sum(faixa.getdata()) / (faixa.width * faixa.height), 90, 'a barra branca precisa de fundo escuro')

    def test_sem_barra_desenhada_na_imagem(self):
        # a imagem veio com uma barra de carregamento desenhada embaixo; foi apagada para não ficarem duas
        im = Image.open(os.path.join(RAIZ, 'assets/splash/carregando.jpg')).convert('L')
        w, h = im.size
        linha = [im.getpixel((x, h - 20)) for x in range(w // 2 - 150, w // 2 + 150)]
        self.assertLess(max(linha) - min(linha), 60)


if __name__ == '__main__':
    unittest.main()
