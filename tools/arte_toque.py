"""Desenha os controles de toque (celular): base e alavanca dos dois analógicos e os botões (pulo, dash, recarga e usar).

Brancos com transparência (a cor e a opacidade vêm das variáveis toque.* no jogo). Tudo 256x256, desenhado 4x maior
e reduzido para a borda ficar lisa.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_toque.py
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets/toque')
LADO = 256
K = 4                      # superamostragem
FONTE = os.path.join(RAIZ, 'assets/Name Smile.otf')
BRANCO = (255, 255, 255)


def tela():
    im = Image.new('RGBA', (LADO * K, LADO * K), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def salva(im, nome):
    im.resize((LADO, LADO), Image.LANCZOS).save(os.path.join(PASTA, nome))


def circulo(d, r, **kw):
    c = LADO * K / 2
    d.ellipse([c - r * K, c - r * K, c + r * K, c + r * K], **kw)


def base():
    im, d = tela()
    circulo(d, 124, fill=BRANCO + (40,), outline=BRANCO + (200,), width=7 * K)
    salva(im, 'base.png')


def alavanca():
    im, d = tela()
    circulo(d, 120, fill=BRANCO + (170,), outline=BRANCO + (255,), width=6 * K)
    salva(im, 'alavanca.png')


def botao(nome, icone):
    im, d = tela()
    circulo(d, 122, fill=BRANCO + (55,), outline=BRANCO + (220,), width=7 * K)
    icone(d)
    salva(im, f'botao_{nome}.png')


def p(x, y):
    return (x * K, y * K)


def seta_cima(d):
    d.polygon([p(128, 58), p(196, 140), p(156, 140), p(156, 196), p(100, 196), p(100, 140), p(60, 140)],
              fill=BRANCO + (235,))


def dash(d):
    for dx in (0, 52):
        d.polygon([p(70 + dx, 70), p(134 + dx, 128), p(70 + dx, 186), p(98 + dx, 186), p(162 + dx, 128),
                   p(98 + dx, 70)], fill=BRANCO + (235,))


def recarga(d):
    c, r, w = 128 * K, 62 * K, 20 * K
    d.arc([c - r, c - r, c + r, c + r], start=40, end=330, fill=BRANCO + (235,), width=w)
    a = math.radians(330)
    x, y = c + r * math.cos(a), c + r * math.sin(a)
    d.polygon([(x - 34 * K, y - 4 * K), (x + 30 * K, y - 26 * K), (x + 10 * K, y + 40 * K)], fill=BRANCO + (235,))


def letra(t):
    def f(d):
        fonte = ImageFont.truetype(FONTE, 150 * K)
        x0, y0, x1, y1 = d.textbbox((0, 0), t, font=fonte)
        d.text(((LADO * K - (x1 - x0)) / 2 - x0, (LADO * K - (y1 - y0)) / 2 - y0), t, font=fonte, fill=BRANCO + (235,))
    return f


def main():
    os.makedirs(PASTA, exist_ok=True)
    base()
    alavanca()
    botao('pulo', seta_cima)
    botao('dash', dash)
    botao('recarga', recarga)
    botao('usar', letra('E'))
    print('controles de toque em', PASTA)


if __name__ == '__main__':
    main()
