"""Sprites dos anjos 'biblicamente corretos' (pixel art gerada por código, sem assets de terceiros).

- ofanim (chefe): rodas dentro de rodas cheias de olhos, olho central, seis asas e auréola de fogo.
- roda_anjo (fraco): roda com olhos que rola até o pato.
- serafim (voador): seis asas (duas no rosto, duas nos pés, duas para voar), um olho e fogo.
- querubim (voador): recortado de ~/Game/AngelsSpriteSheetNew.png (8 quadros de 64 px: 4 limpos e 4 ensanguentados).

Toda animação em laço fecha o ciclo (o quadro depois do último é o primeiro) e todo ataque começa e termina
na pose do quadro 0 do laço parado, para entrar e sair sem tranco.

Desenho em resolução nativa (pixel art) com um mini renderizador 3D (z-buffer) para as rodas,
depois ampliado sem suavização (ESCALA) e salvo em assets/anjos/<nome>/<anim>_NN.png.
"""
import math, os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, 'assets', 'anjos')


def hexa(c):
    c = c.lstrip('#')
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)] + [255], np.uint8)


K = hexa('#24150e')          # contorno
OURO = [hexa(c) for c in ('#4a2a10', '#7a4a18', '#b07a26', '#dfae42', '#f7d97a', '#fff4c8')]
PENA = [hexa(c) for c in ('#5a4e48', '#8c7f72', '#c2b5a2', '#e6dccb', '#fbf7ee')]
FOGO = [hexa(c) for c in ('#c8321a', '#ff6a1f', '#ffa632', '#ffd85c', '#fff3b8')]
ESCLERA, IRIS, IRIS_C, PUPILA, BRILHO = hexa('#f2ede0'), hexa('#2f7fd0'), hexa('#7cc6ff'), hexa('#120d18'), hexa('#ffffff')
LUZ = np.array([-0.45, -0.7, 0.55]); LUZ = LUZ / np.linalg.norm(LUZ)


def desloca(m, dy, dx, vazio):
    out = np.full_like(m, vazio)
    h, w = m.shape[:2]
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - 0.5


class Tela:
    """Imagem RGBA com z-buffer (z maior = mais perto)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.cor = np.zeros((h, w, 4), np.uint8)
        self.z = np.full((h, w), -1e9)

    def ponto(self, x, y, cor, z=0.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and z >= self.z[y, x]:
            self.cor[y, x] = cor
            self.z[y, x] = z

    def esfera(self, cx, cy, cz, r, paleta, brilho=0.0):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = x + .5 - cx, y + .5 - cy
                d2 = dx * dx + dy * dy
                if d2 <= r * r:
                    nz = math.sqrt(r * r - d2)
                    n = np.array([dx, dy, nz]) / r
                    s = np.clip(0.5 + 0.6 * n.dot(LUZ) + brilho, 0, 0.999)
                    self.ponto(x, y, paleta[int(s * len(paleta))], cz + nz)

    def contorno_interno(self, salto=2.5):
        """Pixel vizinho de algo bem mais perto vira contorno (separa as peças)."""
        z, c = self.z, self.cor.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            viz = desloca(z, dy, dx, -1e9)
            m = (viz > z + salto) & (z > -1e8)
            c[m] = K
        self.cor = c

    def contorno_externo(self):
        a = self.cor[..., 3] > 0
        borda = np.zeros_like(a)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            borda |= desloca(a, dy, dx, False)
        borda &= ~a
        self.cor[borda] = K


def anel(t, centro, raio, u, v, grossura, giro, n_olhos, olho_grande=False, sombra_tras=True):
    """Roda 3D: p(s) = c + R(u cos s + v sin s), desenhada como um tubo de esferas no z-buffer."""
    c = np.array(centro, float)
    u, v = np.array(u, float), np.array(v, float)
    n = int(raio * 14)
    for i in range(n):
        s = 2 * math.pi * i / n
        p = c + raio * (u * math.cos(s) + v * math.sin(s))
        pal = OURO if (p[2] - c[2] > -raio * 0.2 or not sombra_tras) else OURO[:-1]
        t.esfera(p[0], p[1], p[2], grossura, pal, brilho=-0.15 if p[2] < c[2] else 0.05)
    for k in range(n_olhos):
        s = 2 * math.pi * k / n_olhos + giro
        p = c + raio * (u * math.cos(s) + v * math.sin(s))
        frente = (p[2] - c[2]) / raio
        grande = olho_grande and frente > -0.2
        olho(t, p[0], p[1], p[2] + grossura + 0.5, grande)


def olho(t, x, y, z, grande=False):
    if grande:
        mapa = ['..kkkkk..',
                '.kwwbwwk.',
                'kwwbPbwwk',
                '.kwwbwwk.',
                '..kkkkk..']
    else:
        mapa = ['.kkk.',
                'kwbwk',
                'kbPbk',
                '.kkk.']
    cores = {'k': K, 'w': ESCLERA, 'b': IRIS, 'P': PUPILA}
    h, w = len(mapa), len(mapa[0])
    for j, linha in enumerate(mapa):
        for i, ch in enumerate(linha):
            if ch != '.':
                t.ponto(x - w // 2 + i, y - h // 2 + j, cores[ch], z)


def olho_central(t, cx, cy, cz, a, b, olhar=(0.0, 0.0), piscar=0.0):
    """Olho grande em elipse: esclera, íris em degradê, pupila e brilho; piscar 0..1 fecha a pálpebra."""
    bb = max(0.6, b * (1 - piscar))
    for y in range(int(cy - b - 2), int(cy + b + 3)):
        for x in range(int(cx - a - 2), int(cx + a + 3)):
            dx, dy = x + .5 - cx, y + .5 - cy
            e = (dx / a) ** 2 + (dy / bb) ** 2
            if e <= 1:
                ix, iy = dx - olhar[0] * a * .35, dy - olhar[1] * bb * .3
                ri = b * 0.78
                d = math.hypot(ix, iy)
                if d < ri * 0.42:
                    cor = PUPILA
                elif d < ri:
                    cor = IRIS_C if (iy < -ri * 0.25) else IRIS
                else:
                    cor = ESCLERA
                if -ri * .55 < ix < -ri * .2 and -ri * .6 < iy < -ri * .25 and d < ri:
                    cor = BRILHO
                if e > 0.78:
                    cor = K
                t.ponto(x, y, cor, cz)
            elif e <= 1.0 + 2.2 / max(a, 1) and piscar > 0:
                pass


def pena(t, raiz, ang, comp, larg, paleta, z):
    """Uma pena: elipse comprida da raiz até a ponta, mais clara na borda de cima, com contorno próprio."""
    rx, ry = raiz
    ca, sa = math.cos(ang), math.sin(ang)
    R = int(comp + larg + 2)
    pts = []
    for y in range(int(ry - R), int(ry + R + 1)):
        for x in range(int(rx - R), int(rx + R + 1)):
            dx, dy = x + .5 - rx, y + .5 - ry
            uu = dx * ca + dy * sa
            vv = -dx * sa + dy * ca
            if 0 <= uu <= comp:
                meia = larg * math.sqrt(max(0.0, 1 - ((uu - comp * .55) / (comp * .58)) ** 2))
                if abs(vv) <= meia:
                    borda = abs(vv) > meia - 1.0 or uu > comp - 1.2
                    pts.append((x, y, uu / comp, vv / max(meia, .1), borda))
    for x, y, fu, fv, borda in pts:
        if borda:
            cor = paleta[0]
        else:
            s = 0.35 + 0.45 * fu - 0.35 * fv
            cor = paleta[1 + int(np.clip(s, 0, .999) * (len(paleta) - 1))]
        t.ponto(x, y, cor, z)


def asa(t, raiz, ang, comp, n, abertura, larg, z, lado=1):
    """Asa em leque: n penas da de trás (mais longa e aberta) para a da frente."""
    for k in reversed(range(n)):
        a = ang + lado * abertura * k
        pena(t, raiz, a, comp * (1 - 0.12 * k), larg, PENA, z - k * 0.01)


def fogo(t, cx, cy, raio, quadro, n_quadros, rng, densidade=1.0, z=-500):
    """Auréola de chamas tremulando em volta (sempre atrás)."""
    fase = 2 * math.pi * quadro / n_quadros
    for y in range(t.h):
        for x in range(t.w):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            onda = (math.sin(ang * 7 + fase * 2) * .5 + math.sin(ang * 13 - fase * 3) * .35 + math.sin(ang * 3 + fase) * .3)
            limite = raio * (1 + 0.10 * onda + 0.22 * max(0.0, -dy / max(d, 1)) * (1 + 0.5 * onda))
            if raio * 0.5 < d < limite:
                s = 1 - (d - raio * .5) / (limite - raio * .5)
                s = np.clip(s * 1.1 + BAYER[y % 4, x % 4] * 0.35, 0, .999)
                t.ponto(x, y, FOGO[int(s * len(FOGO))], z)


def morte(base, n=8, seed=1):
    """Desfaz o sprite em partículas de luz que voam para fora e somem (quadro 0 = sprite inteiro).

    Cada pixel tem a sua hora de sumir, sorteada uma vez: nada reaparece de um quadro para o outro."""
    rng = np.random.default_rng(seed)
    h, w = base.shape[:2]
    ys, xs = np.nonzero(base[..., 3] > 40)
    cx, cy = xs.mean(), ys.mean()
    vx = (xs - cx) * rng.uniform(0.05, 0.16, len(xs)) + rng.normal(0, .7, len(xs))
    vy = (ys - cy) * rng.uniform(0.05, 0.16, len(xs)) + rng.normal(0, .7, len(xs)) - 0.6
    some = rng.uniform(0.15, 1.0, len(xs))
    quadros = []
    for f in range(n):
        im = np.zeros_like(base)
        k = f / (n - 1)
        vivo = some > k
        for x, y, ax, ay in zip(xs[vivo], ys[vivo], vx[vivo], vy[vivo]):
            nx, ny = int(round(x + ax * f * 1.6)), int(round(y + ay * f * 1.6))
            if 0 <= nx < w and 0 <= ny < h:
                c = base[y, x].astype(float)
                c[:3] = c[:3] * (1 - min(1, k * 1.6)) + np.array([255, 246, 200]) * min(1, k * 1.6)
                im[ny, nx] = c.astype(np.uint8)
        quadros.append(im)
    return quadros


def chave(vals, a):
    """Interpola quadros-chave igualmente espaçados em [0, 1), fechando o ciclo (a = 1 volta a vals[0])."""
    x = (a % 1.0) * len(vals)
    i = int(x)
    f = x - i
    f = f * f * (3 - 2 * f)
    return vals[i] * (1 - f) + vals[(i + 1) % len(vals)] * f


def rot_y(a):
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def rot_x(a):
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def rot_z(a):
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


# ------------------------------------------------------------------ roda_anjo
def roda(q, n):
    """Roda que rola para a direita: aro (8 olhos) e raios (4) giram juntos 90° por laço, a menor volta
    em que os dois voltam ao desenho do começo (com 45° os raios davam um salto no fim do laço)."""
    t = Tela(46, 46)
    c = (23, 23, 0)
    giro = (math.pi / 2) * q / n
    anel(t, c, 18.5, (1, 0, 0), (0, 1, 0), 2.8, giro, 8)
    # roda dentro da roda, atravessada (perpendicular) e virada um pouco para aparecer como elipse
    m = rot_y(math.radians(62))
    anel(t, c, 12, m @ np.array([0, 0, 1.0]), (0, 1, 0), 1.8, 0, 0)
    # raios ligando o aro ao centro
    for k in range(4):
        s = 2 * math.pi * k / 4 + giro + math.pi / 8
        for r in np.linspace(7, 16, 10):
            t.esfera(c[0] + r * math.cos(s), c[1] + r * math.sin(s), -2, 0.9, OURO[:-1])
    t.esfera(23, 23, 0, 6.5, OURO, brilho=0.1)
    olho_central(t, 23, 23, 8, 4.6, 3.2)
    t.contorno_interno(); t.contorno_externo()
    return t.cor


# ------------------------------------------------------------------ serafim
def serafim(q, n, ataque=False):
    """voando: bate as asas num ciclo inteiro, as penas abrem na descida e o corpo balança atrasado.
    ataque: ergue as asas (prepara), acende, desce de golpe e volta à pose do quadro 0 do voo."""
    t = Tela(64, 60)
    cx = 32
    a = q / n
    fase = 2 * math.pi * a
    if ataque:
        bater = chave([0, .55, 1.0, 1.15, -1.0, -.7, -.35, -.1], a)
        fogo_r = chave([13, 14, 16, 18, 20, 18, 15, 13.5], a)
        calor = chave([0, .3, .7, 1, 1, .8, .4, .1], a)
        leque = chave([.25, .24, .23, .22, .40, .36, .31, .27], a)                 # .25 = leque do quadro 0 do voo
        sobe = 1.2 * math.sin(-1.1) + chave([0, -.4, -.8, -1.0, 2.4, 1.6, .8, .2], a)
        olho_b = chave([4.4, 4.6, 5.0, 5.4, 5.4, 5.0, 4.6, 4.4], a)
    else:
        bater = math.sin(fase)
        fogo_r, calor, olho_b = 13, 0, 4.4
        leque = 0.30 - 0.05 * math.cos(fase)            # penas fecham na subida, abrem na descida
        sobe = 1.2 * math.sin(fase - 1.1)               # o corpo sobe logo depois da batida
    cy = 30 + int(round(sobe))
    fogo(t, cx, cy, fogo_r, q, n, None)
    # par do meio: voa (bate forte)
    for lado in (1, -1):
        base = 0 if lado == 1 else math.pi
        ang = base - lado * (0.25 + 0.55 * bater)
        asa(t, (cx + lado * 4, cy - 1), ang, 25, 4, leque, 3.2, z=-10, lado=lado)
    atraso = math.sin(fase - 0.9)
    if ataque:
        w = chave([0, .5, 1, 1, 1, 1, .6, .2], a)
        atraso = math.sin(-0.9) * (1 - w) + bater * .8 * w
    # par de cima: cobre o rosto (cruza por cima)
    for lado in (1, -1):
        ang = -math.pi / 2 - lado * (0.55 - 0.08 * atraso)
        asa(t, (cx + lado * 3, cy - 5), ang, 16, 3, -0.32, 2.6, z=-5, lado=lado)
    # par de baixo: cobre os pés
    for lado in (1, -1):
        ang = math.pi / 2 + lado * (0.5 - 0.08 * atraso)
        asa(t, (cx + lado * 3, cy + 5), ang, 15, 3, 0.32, 2.6, z=-5, lado=lado)
    t.esfera(cx, cy, 0, 8.6, FOGO[1:] if calor > .5 else OURO, brilho=0.15 + 0.2 * calor)
    olho_central(t, cx, cy, 10, 6.6, olho_b)
    t.contorno_interno(); t.contorno_externo()
    return t.cor


# ------------------------------------------------------------------ ofanim (chefe)
def ofanim(q, n, ataque=False):
    """idle: asas num ciclo inteiro, rodas andam um olho (1/12 de volta) por laço e o olho central passeia.
    ataque: as rodas aceleram e freiam (3 olhos = 1/4 de volta, mesmo desenho do começo), o fogo cresce,
    as asas abrem e tudo volta à pose do quadro 0 do idle."""
    t = Tela(128, 128)
    c = np.array([64.0, 66.0, 0.0])
    a = q / n
    fase = 2 * math.pi * a
    um_olho = 2 * math.pi / 12
    if ataque:
        forca = chave([0, .25, .6, .9, 1, 1, 1, .9, .7, .45, .2, .05], a)
        bater = forca
        fogo_r = 50 + 8 * forca
        passo = um_olho * 3 * (a * a * (3 - 2 * a))
        olhar = (0.0, 0.0)
        olho_b = 6.6 + 1.6 * forca
    else:
        forca = 0
        bater = math.sin(fase)
        fogo_r = 50
        passo = um_olho * a
        olhar = (0.9 * math.sin(fase), 0.5 * math.sin(2 * fase))    # o olho passeia num oito
        olho_b = 6.6
    fogo(t, 64, 66, fogo_r, q, n, None)
    # seis asas grandes atrás das rodas
    for lado in (1, -1):
        b = 0 if lado == 1 else math.pi
        asa(t, (64 + lado * 10, 52), b - lado * (0.75 + 0.12 * bater), 46, 5, 0.22, 4.6, z=-300, lado=lado)
        asa(t, (64 + lado * 12, 66), b - lado * (0.05 + 0.10 * bater), 44, 5, 0.20, 4.6, z=-301, lado=lado)
        asa(t, (64 + lado * 10, 80), b + lado * (0.70 + 0.08 * bater), 42, 5, -0.22, 4.4, z=-302, lado=lado)
    # roda grande de frente, inclinada
    m1 = rot_z(math.radians(18)) @ rot_x(math.radians(22))
    anel(t, c, 40, m1 @ [1, 0, 0], m1 @ [0, 1, 0], 4.0, passo, 12, olho_grande=True)
    # roda atravessada (wheel within a wheel)
    m2 = rot_z(math.radians(-25)) @ rot_y(math.radians(70))
    anel(t, c, 34, m2 @ [1, 0, 0], m2 @ [0, 1, 0], 3.6, -passo, 12, olho_grande=True)
    # roda de dentro, deitada
    m3 = rot_x(math.radians(72))
    anel(t, c, 25, m3 @ [1, 0, 0], m3 @ [0, 1, 0], 2.8, passo, 12)
    # núcleo com o grande olho
    t.esfera(64, 66, 0, 13, FOGO[1:] if forca > .5 else OURO, brilho=0.2 + 0.15 * forca)
    olho_central(t, 64, 66, 14, 10.5, olho_b, olhar=olhar)
    t.contorno_interno(); t.contorno_externo()
    return t.cor


# ------------------------------------------------------------------ querubim (recortado da folha do usuário)
FOLHA_QUERUBIM = os.path.expanduser('~/Game/AngelsSpriteSheetNew.png')
OLHO_QUERUBIM = (26, 29, 38, 35)        # caixa do olho (x0, y0, x1, y1) dentro do quadro de 64 px


def querubim():
    """Folha de 8 quadros de 64 px: 0-3 ensanguentado, 4-7 limpo; em cada metade: asas no meio, em cima,
    no meio de olho fechado, embaixo. O laço de voo usa duas batidas, com o olho fechando só na segunda
    (o quadro do meio com olho aberto é o de olho fechado com o olho do primeiro quadro colado por cima)."""
    folha = np.array(Image.open(FOLHA_QUERUBIM).convert('RGBA'))
    q = [folha[:, i * 64:(i + 1) * 64].copy() for i in range(8)]
    x0, y0, x1, y1 = OLHO_QUERUBIM
    def aberto(meio, fechado):
        im = fechado.copy()
        im[y0:y1, x0:x1] = meio[y0:y1, x0:x1]
        return im
    def laco(m, c, f, b):
        return [m, c, aberto(m, f), b, m, c, f, b]
    return laco(*q[4:8]), laco(*q[0:4])


ESCALA = {'roda_anjo': 2, 'serafim': 2, 'ofanim': 3, 'querubim': 2}


def salva(nome, anim, quadros):
    pasta = os.path.join(SAIDA, nome)
    os.makedirs(pasta, exist_ok=True)
    s = ESCALA[nome]
    caminhos = []
    for i, q in enumerate(quadros):
        im = Image.fromarray(q, 'RGBA')
        im = im.resize((im.width * s, im.height * s), Image.NEAREST)
        rel = f'assets/anjos/{nome}/{anim}_{i:02d}.png'
        im.save(os.path.join(RAIZ, rel))
        caminhos.append(rel)
    return caminhos


def gera():
    """Devolve {objeto: {animação: [arquivos]}}."""
    out = {}
    rd = [roda(q, 8) for q in range(8)]
    out['roda_anjo'] = {'rolando': salva('roda_anjo', 'rolando', rd),
                        'morte': salva('roda_anjo', 'morte', morte(rd[0], 7, 3))}
    sv = [serafim(q, 8) for q in range(8)]
    out['serafim'] = {'voando': salva('serafim', 'voando', sv),
                      'ataque_1': salva('serafim', 'ataque_1', [serafim(q, 8, True) for q in range(8)]),
                      'morte': salva('serafim', 'morte', morte(sv[0], 8, 4))}
    of = [ofanim(q, 12) for q in range(12)]
    out['ofanim'] = {'idle': salva('ofanim', 'idle', of),
                     'ataque': salva('ofanim', 'ataque', [ofanim(q, 12, True) for q in range(12)]),
                     'morte': salva('ofanim', 'morte', morte(of[0], 12, 5))}
    limpo, ferido = querubim()
    out['querubim'] = {'voando': salva('querubim', 'voando', limpo),
                       'voando_ferido': salva('querubim', 'voando_ferido', ferido),
                       'morte': salva('querubim', 'morte', morte(ferido[0], 8, 6))}
    return out


if __name__ == '__main__':
    r = gera()
    for o, a in r.items():
        print(o, {k: len(v) for k, v in a.items()})
