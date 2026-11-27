"""Desenha os controles de toque (celular): base e alavanca dos dois analógicos e os botões (pulo, dash e usar).

Discretos e legíveis em qualquer fundo (do Inferno vermelho ao céu claro do Paraíso): miolo escuro bem transparente,
aro branco fino com um contorno escuro por fora, ícone branco com sombra escura. A cor (tinta) e a opacidade vêm das
variáveis toque.* no jogo; o tamanho na tela também (o desenho é esticado). Tudo 256x256, desenhado 4x maior e
reduzido para a borda ficar lisa. base.png é o analógico de andar, base_mira.png o de mirar (com a mira em cruz).
Os botões de pulo e dash (t218) usam o próprio pato (pixel art ampliada sem suavizar): no pulo, o quadro de pulo com
riscos de impulso embaixo; no dash, o pato esticado na horizontal com riscos de velocidade atrás.
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


def botao_pato(nome, quadro, sx, sy, cx, cy, riscos):
    """aro + riscos brancos (com sombra) + o quadro do pato ampliado sx por sy vezes, centrado em (cx, cy)."""
    im, d = tela()
    aro(d, 122, 70, 6)
    im = Image.alpha_composite(im, com_sombra(riscos)).resize((LADO, LADO), Image.LANCZOS)
    pato = Image.open(os.path.join(RAIZ, 'assets', quadro)).convert('RGBA')
    pato = pato.crop(pato.getbbox())
    pato = pato.resize((pato.width * sx, pato.height * sy), Image.NEAREST)
    camada = Image.new('RGBA', (LADO, LADO), (0, 0, 0, 0))
    camada.paste(pato, (round(cx - pato.width / 2), round(cy - pato.height / 2)), pato)
    # sombra escura macia em volta do pato (contraste no céu claro)
    sombra = Image.new('RGBA', (LADO, LADO), ESCURO + (0,))
    sombra.putalpha(camada.getchannel('A').filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(3))
                    .point(lambda a: a * 170 // 255))
    im = Image.alpha_composite(Image.alpha_composite(im, sombra), camada)
    im.save(os.path.join(PASTA, f'botao_{nome}.png'))


def risco(d, cor, x0, y0, x1, y1, w):
    d.line([p(x0, y0), p(x1, y1)], fill=cor, width=w * K)
    for x, y in ((x0, y0), (x1, y1)):
        d.ellipse([p(x - w / 2, y - w / 2), p(x + w / 2, y + w / 2)], fill=cor)


def riscos_pulo(d, cor):
    """riscos de impulso embaixo do pato, abrindo para fora."""
    for x0, x1 in ((104, 92), (128, 128), (152, 164)):
        risco(d, cor, x0, 176, x1, 214, 11)


def riscos_dash(d, cor):
    """riscos de velocidade atrás do pato (à esquerda)."""
    for y, x0 in ((98, 40), (128, 26), (158, 40)):
        risco(d, cor, x0, y, 72, y, 11)


def p(x, y):
    return (x * K, y * K)


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
    botao_pato('pulo', 'pato_jump_0.png', 6, 6, 128, 104, riscos_pulo)
    botao_pato('dash', 'pato_walk_1.png', 7, 5, 150, 128, riscos_dash)
    botao('usar', letra('E'))
    print('controles de toque em', PASTA)


if __name__ == '__main__':
    main()
