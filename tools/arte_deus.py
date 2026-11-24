"""Arte do chefe final (Deus, o olho de luz da direção B "os três círculos"), dos canalizadores e dos efeitos.

Gerador de arte (roda uma vez; não mexe no jogo.json). Pixel art com contorno escuro e a paleta dos anjos,
desenhada na resolução nativa e ampliada com NEAREST. Todas as partes do olho têm o mesmo centro, então
no jogo basta pôr o centro de cada uma no centro do olho.
    python3 tools/arte_deus.py
"""
import math, os, random
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(RAIZ, 'assets/inimigos/ceu/deus')
CAN = os.path.join(RAIZ, 'assets/inimigos/ceu/canalizador')
P = os.path.join(RAIZ, 'assets/paraiso/deus')

C = dict(
    contorno=(36, 21, 14), escuro=(18, 13, 24),
    ouro0=(122, 74, 24), ouro1=(176, 122, 38), ouro2=(223, 174, 66), ouro3=(247, 217, 122), ouro4=(255, 243, 184),
    pena0=(90, 78, 72), pena1=(140, 127, 114), pena2=(194, 181, 162), pena3=(230, 220, 203), pena4=(251, 247, 238),
    azul0=(20, 60, 130), azul1=(47, 127, 208), azul2=(124, 198, 255), branco=(255, 255, 255),
    creme=(255, 244, 200), rosa=(255, 170, 190), rosa0=(200, 90, 120), rosa1=(255, 106, 140),
    ceu0=(60, 120, 200), ceu1=(150, 210, 255), noite0=(8, 8, 24), noite1=(18, 24, 60), noite2=(30, 46, 104),
)
OURO = [C['ouro0'], C['ouro1'], C['ouro2'], C['ouro3'], C['ouro4']]
AZUL = [C['azul0'], C['azul1'], C['azul2'], C['ceu1'], C['pena4']]
ROSA = [C['rosa0'], C['rosa1'], C['rosa'], C['creme'], C['pena4']]
ESCLERA = [C['pena2'], C['pena3'], C['creme'], C['pena4']]
CEU = [C['ceu0'], C['ceu1'], C['creme'], C['pena4']]
PEDRA = [C['pena0'], C['pena1'], C['pena2'], C['pena3']]
RAMPAS_ANEIS = {'anel_ouro': OURO, 'anel_azul': AZUL, 'anel_rosa': ROSA}


class Tela:
    def __init__(self, w, h=None, esc=3):
        h = h or w
        self.w, self.h, self.esc = w, h, esc
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(float)
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)
        self.cx, self.cy = w / 2, h / 2

    def pinta(self, m, cor):
        cor = np.asarray(cor, np.uint8)
        self.rgb[m] = cor if cor.ndim == 1 else cor[m]
        self.a |= m

    def camada(self, m, cor, contorno=True):
        if contorno:
            self.pinta(dilata(m) & ~m, C['contorno'])
        self.pinta(m, cor)

    def apaga(self, m):
        self.a &= ~m

    def d(self, cx=None, cy=None):
        return np.hypot(self.xx - (self.cx if cx is None else cx), self.yy - (self.cy if cy is None else cy))

    def ang(self, cx=None, cy=None):
        return np.arctan2(self.yy - (self.cy if cy is None else cy), self.xx - (self.cx if cx is None else cx))

    def rampa(self, v, cores, dither=True):
        v = np.clip(v, 0, 0.9999) * len(cores)
        i = np.floor(v).astype(int)
        if dither:
            chk = (self.xx.astype(int) + self.yy.astype(int)) % 2 == 0
            i = np.where((v - i > 0.75) & chk, np.minimum(i + 1, len(cores) - 1), i)
        return np.array(cores, np.uint8)[i]

    def xadrez(self, fase=0):
        return (self.xx.astype(int) + self.yy.astype(int) + fase) % 2 == 0

    def img(self):
        im = np.dstack([self.rgb, (self.a * 255).astype(np.uint8)])
        return Image.fromarray(im, 'RGBA').resize((self.w * self.esc, self.h * self.esc), Image.NEAREST)


def dilata(m):
    d = m.copy()
    d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    return d


def rot(x, y, ang):
    c, s = math.cos(ang), math.sin(ang)
    return x * c + y * s, -x * s + y * c


def elipse(t, cx, cy, rx, ry, ang=0.0):
    u, v = rot(t.xx - cx, t.yy - cy, ang)
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1


def amendoa(t, cx, cy, larg, alt):
    r = (larg ** 2 / 4 + alt ** 2) / (2 * alt)
    return ((t.xx - cx) ** 2 + (t.yy - (cy - alt + r)) ** 2 <= r * r) & \
           ((t.xx - cx) ** 2 + (t.yy - (cy + alt - r)) ** 2 <= r * r)


def pena(t, cx, cy, comp, larg, ang, cores):
    u, v = rot(t.xx - cx, t.yy - cy, ang)
    m = (u >= 0) & (u <= comp) & (np.abs(v) <= larg * (1 - (u / comp) ** 3 * 0.6))
    m |= (u - comp) ** 2 + v ** 2 <= (larg * 0.4) ** 2
    t.camada(m, t.rampa(0.35 + 0.65 * (1 - np.abs(v) / larg) * (0.5 + 0.5 * (u / comp)), cores))


def salva(im, pasta, nome):
    os.makedirs(pasta, exist_ok=True)
    im.save(os.path.join(pasta, nome))


def salva_anim(quadros, pasta, anim):
    for i, im in enumerate(quadros):
        salva(im, pasta, f'{anim}_{i:02d}.png')


# ---------------- o olho (esclera e pálpebras; a íris é a pupila, à parte) ----------------
N_OLHO = 220
LARG, ALT = 96, 36


def olho(aberto=1.0, pulso=0.0, branco=0.0, escuro=0.0, flash=0.0, raios=0.0):
    t = Tela(N_OLHO)
    cx, cy = t.cx, t.cy
    alt = max(1.5, ALT * aberto)
    if raios > 0:
        d, a = t.d(), t.ang()
        # raios finos que afinam até a ponta, sem contorno, com a ponta esmaecendo em xadrez
        r0, comp = 24, 22 + 62 * raios
        f = np.clip((d - r0) / comp, 0, 1)
        m = (np.abs(np.sin(a * 6)) < 0.26 * (1 - f)) & (d > r0) & (d < r0 + comp)
        m &= (f < 0.55) | t.xadrez()
        t.camada(m, t.rampa(1.05 - f, [C['ouro2'], C['ouro4'], C['creme'], C['pena4']]), contorno=False)
    lid = amendoa(t, cx, cy, LARG + 14, alt + 9)
    dl = np.hypot(t.xx - cx, (t.yy - cy) * 1.6)
    v = 0.45 + 0.6 * (1 - dl / (LARG / 2 + 7)) + 0.25 * (cy - t.yy) / (alt + 9) + pulso - escuro
    t.camada(lid, t.rampa(v, OURO))
    esc = amendoa(t, cx, cy, LARG, alt)
    v = 0.55 + 0.45 * (1 - t.d() / (LARG / 2)) + branco - escuro
    t.camada(esc, t.rampa(v, ESCLERA + [C['branco']] if branco else ESCLERA))
    if aberto < 0.2:   # a fenda fechada: uma linha de cílios dourados
        t.pinta(esc | (np.abs(t.yy - cy) < 1) & (np.abs(t.xx - cx) < LARG / 2), C['ouro4'])
    if flash > 0:
        m = t.a & (t.xadrez() | (flash > 0.6))
        t.pinta(m, C['branco'])
    return t


def anim_olho():
    pasta = os.path.join(D, 'olho')
    salva_anim([olho(pulso=0.1 * math.sin(2 * math.pi * i / 8)).img() for i in range(8)], pasta, 'idle')
    abre = [1, 0.7, 0.35, 0.06, 0.06, 0.35, 0.7, 1]
    salva_anim([olho(aberto=a).img() for a in abre], pasta, 'piscar')
    salva_anim([olho(aberto=0.06).img()], pasta, 'fechado')
    salva_anim([olho(branco=0.12 * i, raios=0.1 * i).img() for i in range(8)], pasta, 'carregar')
    salva_anim([olho(branco=0.8, raios=0.3 + 0.06 * i, pulso=0.1 * (i % 2)).img() for i in range(12)], pasta, 'juizo')
    falha = [olho(branco=0.6 - 0.1 * i, escuro=0.25 * (i % 2), aberto=1 - 0.08 * i).img() for i in range(6)]
    salva_anim(falha, pasta, 'juizo_falha')
    salva_anim([olho(flash=1).img(), olho().img()], pasta, 'dano')
    fase = []
    for i in range(10):
        t = olho(pulso=0.2, flash=0.5 if i in (1, 3) else 0)
        r = 30 + 9 * i
        anel = (np.abs(t.d() - r) < 2) & ~t.a
        t.pinta(anel, C['branco'] if i < 6 else C['creme'])
        fase.append(t.img())
    salva_anim(fase, pasta, 'fase')
    morte = []
    for i in range(14):
        if i < 8:
            t = olho(aberto=1 - i / 8, escuro=0.04 * i)
        else:
            k = (i - 8) / 5
            t = Tela(N_OLHO)
            m = t.d() < 20 + 90 * k
            m &= t.xadrez() | (k < 0.5)
            m &= (np.random.RandomState(i).rand(N_OLHO, N_OLHO) > k * 0.9)
            t.pinta(m, C['branco'] if k < 0.6 else C['creme'])
            t.a[0, 0] = False
        morte.append(t.img())
    salva_anim(morte, pasta, 'morte')


# ---------------- a pupila (íris azul com raios e pupila escura) ----------------
def pupila(r_pup=0.42, giro=0.0, flash=False):
    t = Tela(60)
    r = 23
    d, a = t.d(), t.ang()
    m = d <= r
    di = d / r
    t.camada(m, t.rampa(0.15 + 0.85 * (1 - di) * 0.8 + 0.2 * ((t.yy - t.cy) / r > 0.3),
                        [C['azul0'], C['azul1'], C['azul1'], C['azul2']]))
    t.pinta(m & (di > 0.45) & (np.sin(a * 14 + giro) > 0.75), C['azul2'])
    t.pinta(d <= r * r_pup, C['escuro'])
    t.pinta(np.hypot(t.xx - (t.cx - r * 0.35), t.yy - (t.cy - r * 0.4)) <= r * 0.17, C['branco'])
    t.pinta(np.hypot(t.xx - (t.cx + r * 0.3), t.yy - (t.cy + r * 0.32)) <= r * 0.08, C['branco'])
    if flash:
        t.pinta(m & t.xadrez(), C['branco'])
    return t.img()


def anim_pupila():
    pasta = os.path.join(D, 'pupila')
    salva_anim([pupila(giro=i * math.pi / 14) for i in range(4)], pasta, 'idle')
    salva_anim([pupila(r_pup=0.42 - 0.04 * i) for i in range(6)], pasta, 'contrai')
    salva_anim([pupila(flash=True), pupila()], pasta, 'dano')


# ---------------- os três anéis (cada um deslocado do centro, como no conceito B) ----------------
def anel(nome, brilho=0.0, quebra=0.0, k_brilho=0):
    t = Tela(N_OLHO)
    k = list(RAMPAS_ANEIS).index(nome)
    a0 = -math.pi / 2 + k * 2 * math.pi / 3
    cx, cy = t.cx + math.cos(a0) * 22, t.cy + math.sin(a0) * 22
    d = t.d(cx, cy)
    m = (d <= 66) & (d > 56)
    if quebra:
        a = t.ang(cx, cy)
        seg = np.floor((a + math.pi) / (2 * math.pi) * 10).astype(int)
        rng = np.random.RandomState(k)
        desloc = rng.rand(10) * 12 * quebra
        t2 = Tela(N_OLHO)
        mm = np.zeros_like(m)
        for s in range(10):
            ac = -math.pi + (s + 0.5) * 2 * math.pi / 10
            dx, dy = math.cos(ac) * desloc[s] * 2, math.sin(ac) * desloc[s] * 2
            dd = np.hypot(t2.xx - dx - cx, t2.yy - dy - cy)
            aa = np.arctan2(t2.yy - dy - cy, t2.xx - dx - cx)
            ss = np.floor((aa + math.pi) / (2 * math.pi) * 10).astype(int)
            mm |= (dd <= 66) & (dd > 56) & (ss == s) & (np.abs(np.angle(np.exp(1j * (aa - ac)))) < math.pi / 10 * (1 - 0.3 * quebra))
        m = mm & (np.random.RandomState(int(quebra * 10)).rand(N_OLHO, N_OLHO) > quebra * 0.7)
    v = (d - 56) / 10 * 0.6 + 0.4 * (1 - (t.yy - cy + 66) / 132) + brilho
    t.camada(m, t.rampa(v, RAMPAS_ANEIS[nome]))
    if brilho:   # faíscas correndo pelo anel
        a = t.ang(cx, cy)
        t.pinta(m & (np.abs(np.angle(np.exp(1j * (a - k_brilho * math.pi / 2)))) < 0.12), C['branco'])
    return t.img()


def anim_aneis():
    for nome in RAMPAS_ANEIS:
        pasta = os.path.join(D, nome)
        salva_anim([anel(nome)], pasta, 'idle')
        salva_anim([anel(nome, brilho=0.25, k_brilho=i) for i in range(4)], pasta, 'cintila')
        salva_anim([anel(nome, quebra=(i + 1) / 8) for i in range(8)], pasta, 'quebra')


# ---------------- aura e escudo ----------------
def anim_aura():
    q = []
    for i in range(8):
        t = Tela(260)
        fase = 2 * math.pi * i / 8
        d, a = t.d(), t.ang()
        borda = 116 + 6 * (np.sin(a * 12 + fase) * 0.6 + np.sin(a * 24 + 1.3 - fase) * 0.4)
        t.camada(d <= borda, t.rampa(1 - d / np.maximum(borda, 1), CEU), contorno=False)
        rr = 126
        raio = (np.abs(np.angle(np.exp(1j * (a * 12 + fase / 2)))) * d / 12 < 5.5 * (1 - d / rr)) & (d > 78) & (d < rr)
        t.camada(raio, t.rampa(1 - d / rr, OURO[1:]))
        t.apaga(d < 70)
        q.append(t.img())
    salva_anim(q, os.path.join(D, 'aura'), 'idle')


def anim_escudo():
    """redoma de luz em tons de cinza (a cor vem do jogo, deus.escudo_cor): aro claro com contorno escuro, borda com xadrez (a curva da bolha), treliça triangular que
    cintila passando pela bolha e um brilho no alto à esquerda; o meio fica quase limpo para ver o olho."""
    q = []
    R = 110
    g1, g2, g3, g4, g0 = (150, 150, 150), (195, 195, 195), (228, 228, 228), (250, 250, 250), (55, 55, 60)
    for i in range(6):
        t = Tela(240)
        d, a = t.d(), t.ang()
        x, y = t.xx - t.cx, t.yy - t.cy
        dentro = d < R - 2
        # treliça: três famílias de linhas a 60 graus
        linha = np.zeros_like(d, bool)
        for th in (0, math.pi / 3, 2 * math.pi / 3):
            u = (x * math.cos(th) + y * math.sin(th)) / 18.0
            linha |= np.abs(u - np.round(u)) < 0.045
        faixa = np.sin((x * 0.6 + y) / 26.0 - i * math.pi / 3) > 0.55
        trelica = dentro & linha & (faixa | (d > R * 0.78))
        t.pinta(trelica, t.rampa(0.3 + 0.7 * d / R, [g1, g2, g3]))
        # brilho de bolha (fresnel): pontilhado ordenado que adensa para a borda; o meio fica limpo
        bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
        lim = bayer[t.yy.astype(int) % 4, t.xx.astype(int) % 4]
        dens = np.clip((d / R - 0.5) / 0.5, 0, 1) ** 1.6 * 0.8
        t.pinta(dentro & (lim < dens), t.rampa(d / R, [g2, g3]))
        # borda da bolha em xadrez
        t.pinta(dentro & (d > R - 13) & t.xadrez(i % 2), g2)
        t.pinta(dentro & (d > R - 6), g3)
        # aro e contorno
        aro = (d >= R - 3) & (d < R + 1.5)
        t.pinta(aro, t.rampa(0.5 + 0.5 * np.cos(a + 2.3), [g2, g3, g4]))
        t.pinta((d >= R + 1.5) & (d < R + 3), g0)
        # brilho no alto à esquerda
        t.pinta((d > R - 11) & (d < R - 7) & (a > -2.7) & (a < -1.7), (255, 255, 255))
        q.append(t.img())
    salva_anim(q, os.path.join(D, 'escudo'), 'idle')


# ---------------- canalizador (serafim pequeno de acento rosa) ----------------
def canalizador(bate=0.0, canal=0.0, some=0.0):
    t = Tela(64, esc=2)
    cx, cy = t.cx, t.cy
    penas = [C['pena0'], C['pena1'], C['pena2'], C['pena3'], C['pena4']]
    for lado in (-1, 1):
        for j, base in enumerate((-0.5, 0.35)):
            ang = (math.pi / 2 - lado * math.pi / 2) + lado * (base + 0.35 * bate)
            for f in range(3):
                pena(t, cx + lado * 4, cy, 20 - 3 * f - 4 * j, 4, ang + lado * (f - 1) * 0.25, penas)
    corpo = np.hypot(t.xx - cx, t.yy - cy) <= 9
    t.camada(corpo, t.rampa(0.5 + 0.5 * (1 - t.d() / 9) + canal * 0.3, ROSA))
    t.pinta(elipse(t, cx, cy, 5, 3), C['creme'])
    t.pinta(np.hypot(t.xx - cx, t.yy - cy) <= 2, C['rosa0'] if not canal else C['branco'])
    if canal:
        d, a = t.d(), t.ang()
        t.camada((np.abs(np.sin(a * 4 + canal * 3)) > 0.93) & (d > 11) & (d < 11 + 12 * canal), C['rosa'])
    if some:
        t.apaga(np.random.RandomState(int(some * 10)).rand(64, 64) < some)
        t.a[0, 0] = False
    return t.img()


def anim_canalizador():
    salva_anim([canalizador(bate=math.sin(2 * math.pi * i / 6)) for i in range(6)], CAN, 'idle')
    salva_anim([canalizador(bate=0.3 * math.sin(2 * math.pi * i / 6), canal=0.4 + 0.1 * i) for i in range(6)], CAN, 'canalizar')
    salva_anim([canalizador(bate=-0.6, canal=0.0, some=(i + 1) / 8) for i in range(8)], CAN, 'morte')


# ---------------- peças do Empíreo ----------------
def fragmento(n, semente):
    """lasca de pedra do céu: polígono irregular em facetas planas (luz de cima à esquerda), contorno,
    rachaduras e um veio dourado; sem ruído."""
    t = Tela(n)
    rng = np.random.RandomState(semente)
    k = 7
    angs = (np.arange(k) + 0.35 * rng.randn(k).clip(-1, 1)) * 2 * math.pi / k + rng.rand() * math.pi
    raios = n * (0.30 + 0.14 * rng.rand(k))
    vx, vy = t.cx + np.cos(angs) * raios, t.cy + np.sin(angs) * raios * 0.85
    # ponto das facetas, um pouco para cima e à esquerda (o lado iluminado fica maior)
    px, py = t.cx - n * 0.06 + rng.randn() * 1.5, t.cy - n * 0.08 + rng.randn() * 1.5
    ang = np.arctan2(t.yy + 0.5 - py, t.xx + 0.5 - px)
    dentro = np.ones((n, n), bool)
    for i in range(k):
        x0, y0, x1, y1 = vx[i], vy[i], vx[(i + 1) % k], vy[(i + 1) % k]
        dentro &= (x1 - x0) * (t.yy + 0.5 - y0) - (y1 - y0) * (t.xx + 0.5 - x0) >= 0
    luz = np.array([-0.6, -0.8])
    tons = [C['pena0'], C['pena1'], C['pena2'], C['pena3']]
    faceta = np.zeros((n, n), int)
    a_v = np.arctan2(vy - py, vx - px)
    for i in range(k):
        a0, a1 = a_v[i], a_v[(i + 1) % k]
        dentro_f = ((ang - a0) % (2 * math.pi)) < ((a1 - a0) % (2 * math.pi))
        meio = (a0 + ((a1 - a0) % (2 * math.pi)) / 2)
        brilho = np.dot([math.cos(meio), math.sin(meio)], luz)
        faceta[dentro_f] = int(np.clip(round(1.5 + 1.6 * brilho), 0, 3))
    cor = np.array(tons, np.uint8)[faceta]
    t.camada(dentro, cor)
    # arestas entre facetas, um tom abaixo
    for i in range(k):
        for f in np.linspace(0.15, 0.95, n):
            x, y = int(px + (vx[i] - px) * f), int(py + (vy[i] - py) * f)
            if 0 <= x < n and 0 <= y < n and dentro[y, x]:
                t.rgb[y, x] = tons[max(0, faceta[y, x] - 1)]
    # borda iluminada (em cima e à esquerda) mais clara
    borda = dentro & ~np.roll(dentro, 1, 0) | dentro & ~np.roll(dentro, 1, 1)
    t.pinta(borda & (faceta >= 2), C['pena4'])
    # um veio dourado atravessando
    a = rng.rand() * math.pi
    for f in np.linspace(-0.3, 0.3, n * 2):
        x = int(t.cx + math.cos(a) * f * n + math.sin(f * 9) * 1.2)
        y = int(t.cy + math.sin(a) * f * n)
        if 0 <= x < n and 0 <= y < n and dentro[y, x] and not borda[y, x]:
            t.rgb[y, x] = C['ouro2']
    return t.img()


def feixe():
    t = Tela(22)
    dx = np.abs(t.xx - t.cx + 0.5) / 11
    t.pinta(np.ones((22, 22), bool), t.rampa(1 - dx + 0.08 * np.sin(t.yy * 2 * math.pi / 22), [C['ouro3'], C['creme'], C['pena4'], C['branco']]))
    return t.img()


def halo():
    t = Tela(86)
    d = t.d() / 43
    m = (d < 1) & ((d < 0.7) | t.xadrez() & (d < 0.85) | (np.abs(d - 0.95) < 0.03))
    t.pinta(m, t.rampa(1 - d, [C['ceu1'], C['creme'], C['pena4'], C['branco']]))
    return t.img()


def anel_luz():
    t = Tela(10)
    d = t.d()
    t.camada(d < 4, t.rampa(1 - d / 4, [C['ouro3'], C['creme'], C['branco']]))
    return t.img()


def checkpoint(i):
    t = Tela(64)
    cx, cy = t.cx, t.cy
    penas = [C['pena0'], C['pena1'], C['pena2'], C['pena3'], C['pena4']]
    bate = 0.15 * math.sin(2 * math.pi * i / 8)
    for lado in (-1, 1):
        for f in range(4):
            pena(t, cx + lado * 8, cy + 2, 22 - 3 * f, 3.5, (math.pi / 2 - lado * math.pi / 2) + lado * (-0.6 + 0.3 * f + bate), penas)
    d = t.d()
    t.camada((d <= 14) & (d > 10), t.rampa(0.6 + 0.4 * math.sin(2 * math.pi * i / 8) * np.ones_like(d), OURO))
    t.camada(d <= 8, t.rampa(1 - d / 8 + 0.25 * math.sin(2 * math.pi * i / 8), [C['ceu1'], C['creme'], C['pena4'], C['branco']]))
    return t.img()


def asas(bate):
    t = Tela(60, 36, esc=1)
    penas = [C['pena1'], C['pena2'], C['pena3'], C['pena4']]
    for lado in (-1, 1):
        for f in range(4):
            ang = (math.pi / 2 - lado * math.pi / 2) + lado * (-0.5 * bate + 0.22 * f - 0.25)
            pena(t, t.cx + lado * 5, t.cy, 22 - 3 * f, 3.2, ang, penas)
    return t.img()


def queima():
    t = Tela(64, 32)
    ondas = 6 + 4 * np.sin(t.xx * 2 * math.pi / 16) + 3 * np.sin(t.xx * 2 * math.pi / 32 + 1)
    alt = (32 - t.yy)
    m = alt <= 14 + ondas
    t.pinta(m, t.rampa(1 - alt / (14 + ondas + 1e-9) * 0.9, [C['ouro2'], C['ouro3'], C['creme'], C['pena4'], C['branco']]))
    return t.img()


def bg(estrelas, pontos=False):
    """pontos: pinta as estrelas na imagem. Desde a t164 as estrelas são objetos (estrela), então o padrão é sem."""
    t = Tela(342)
    rng = random.Random(7 if estrelas else 3)
    if estrelas:
        t.pinta(np.ones((342, 342), bool), t.rampa(0.15 + 0.1 * np.sin(t.yy * 2 * math.pi / 342) ** 2, [C['noite0'], C['noite1']]))
        for _ in range(260 if pontos else 0):
            x, y = rng.randrange(342), rng.randrange(342)
            t.rgb[y, x] = rng.choice([C['pena4'], C['ceu1'], C['creme'], C['branco']])
        for _ in range(14 if pontos else 0):
            x, y = rng.randrange(1, 341), rng.randrange(1, 341)
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                t.rgb[y + dy, x + dx] = C['branco']
    else:
        t.pinta(np.ones((342, 342), bool), t.rampa(0.45 + 0.1 * np.sin(t.xx * 2 * math.pi / 342), [C['noite2'], C['azul0'], C['ceu0']]))
        for _ in range(60 if pontos else 0):
            x, y = rng.randrange(342), rng.randrange(342)
            t.rgb[y, x] = C['ceu1']
    return t.img()


def pecas():
    for k, (n, s) in enumerate(((32, 11), (42, 12), (52, 13)), 1):
        salva(fragmento(n, s), P, f'fragmento_{k}.png')
    salva(feixe(), P, 'feixe.png')
    salva(halo(), P, 'halo.png')
    salva(anel_luz(), P, 'anel_luz.png')
    salva(queima(), P, 'queima_borda.png')
    salva(bg(True), P, 'bg_espaco.png')
    salva(bg(False), P, 'bg_ceu_alto.png')
    salva_anim([checkpoint(i) for i in range(8)], os.path.join(P, 'checkpoint_empireo'), 'idle')
    salva_anim([asas(math.sin(2 * math.pi * i / 6) * 0.3) for i in range(6)], os.path.join(P, 'asas_pato'), 'idle')
    salva_anim([asas(math.sin(2 * math.pi * i / 6)) for i in range(6)], os.path.join(P, 'asas_pato'), 'bater')


if __name__ == '__main__':
    anim_olho(); anim_pupila(); anim_aneis(); anim_aura(); anim_escudo(); anim_canalizador(); pecas()
    print('ok')
