"""Desenha os controles de toque (celular): base e alavanca dos dois analógicos e os botões (pulo, dash, recarga e usar).

Discretos e legíveis em qualquer fundo (do Inferno vermelho ao céu claro do Paraíso): miolo escuro bem transparente,
aro branco fino com um contorno escuro por fora, ícone branco com sombra escura. A cor (tinta) e a opacidade vêm das
variáveis toque.* no jogo; o tamanho na tela também (o desenho é esticado). Tudo 256x256, desenhado 4x maior e
reduzido para a borda ficar lisa. base.png é o analógico de andar, base_mira.png o de mirar (com a mira em cruz).
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_toque.py
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets/toque')
LADO = 256
K = 4                      # superamostragem
FONTE = os.path.join(RAIZ, 'assets/Name Smile.otf')
BRANCO = (255, 255, 255)
ESCURO = (12, 10, 18)


def tela():
    im = Image.new('RGBA', (LADO * K, LADO * K), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def salva(im, nome):
    im.resize((LADO, LADO), Image.LANCZOS).save(os.path.join(PASTA, nome))


def circulo(d, r, **kw):
    c = LADO * K / 2
    d.ellipse([c - r * K, c - r * K, c + r * K, c + r * K], **kw)


def aro(d, r, miolo_alfa, largura=6):
    """miolo escuro transparente, contorno escuro e aro branco (lê no claro e no escuro)."""
    circulo(d, r, fill=ESCURO + (miolo_alfa,), outline=ESCURO + (150,), width=(largura + 4) * K)
    circulo(d, r - 2, outline=BRANCO + (230,), width=largura * K)


def com_sombra(desenho):
    """desenha o ícone branco com uma sombra escura macia em volta (contraste no céu claro)."""
    im, d = tela()
    desenho(d, BRANCO + (240,))
    sombra, ds = tela()
    desenho(ds, ESCURO + (200,))
    sombra = sombra.filter(ImageFilter.MaxFilter(9 * K // 2 * 2 + 1)).filter(ImageFilter.GaussianBlur(3 * K))
    return Image.alpha_composite(sombra, im)


def base():
    im, d = tela()
    aro(d, 124, 45, 5)
    salva(im, 'base.png')


def base_mira():
    im, d = tela()
    aro(d, 124, 45, 5)
    c = LADO / 2

    def cruz(dd, cor):
        for a in range(4):
            ang = math.radians(90 * a)
            x0, y0 = c + math.cos(ang) * 78, c + math.sin(ang) * 78
            x1, y1 = c + math.cos(ang) * 106, c + math.sin(ang) * 106
            dd.line([(x0 * K, y0 * K), (x1 * K, y1 * K)], fill=cor, width=8 * K)
    im = Image.alpha_composite(im, com_sombra(cruz))
    salva(im, 'base_mira.png')


def alavanca():
    im, d = tela()
    circulo(d, 118, fill=BRANCO + (150,), outline=ESCURO + (170,), width=8 * K)
    circulo(d, 104, outline=BRANCO + (235,), width=5 * K)
    salva(im, 'alavanca.png')


def botao(nome, icone):
    im, d = tela()
    aro(d, 122, 70, 6)
    im = Image.alpha_composite(im, com_sombra(icone))
    salva(im, f'botao_{nome}.png')


def p(x, y):
    return (x * K, y * K)


def seta_cima(d, cor):
    d.polygon([p(128, 60), p(190, 132), p(152, 132), p(152, 190), p(104, 190), p(104, 132), p(66, 132)], fill=cor)


def dash(d, cor):
    for dx in (0, 50):
        d.polygon([p(72 + dx, 76), p(130 + dx, 128), p(72 + dx, 180), p(98 + dx, 180), p(156 + dx, 128),
                   p(98 + dx, 76)], fill=cor)


def recarga(d, cor):
    c, r, w = 128 * K, 58 * K, 18 * K
    d.arc([c - r, c - r, c + r, c + r], start=40, end=330, fill=cor, width=w)
    a = math.radians(330)
    x, y = c + r * math.cos(a), c + r * math.sin(a)
    d.polygon([(x - 32 * K, y - 4 * K), (x + 28 * K, y - 24 * K), (x + 10 * K, y + 38 * K)], fill=cor)


def letra(t):
    def f(d, cor):
        fonte = ImageFont.truetype(FONTE, 140 * K)
        x0, y0, x1, y1 = d.textbbox((0, 0), t, font=fonte)
        d.text(((LADO * K - (x1 - x0)) / 2 - x0, (LADO * K - (y1 - y0)) / 2 - y0), t, font=fonte, fill=cor)
    return f


def main():
    os.makedirs(PASTA, exist_ok=True)
    base()
    base_mira()
    alavanca()
    botao('pulo', seta_cima)
    botao('dash', dash)
    botao('recarga', recarga)
    botao('usar', letra('E'))
    print('controles de toque em', PASTA)


if __name__ == '__main__':
    main()
