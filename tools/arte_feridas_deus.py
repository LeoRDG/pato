"""Arte do Deus sem explosão pintada e com o olho se ferindo (parte da arte de tools/arte_deus.py).

- olho/morte (14 quadros, mesmos arquivos): o olho inteiro clareia até ficar branco e depois encolhe para o centro
  e some, tudo em pixel art limpa (sem a nuvem pontilhada de antes). A explosão agora são emissores de partículas
  de luz no jogo (t214).
- anel_*/quebra (8 quadros, mesmos arquivos): o anel acende até quase branco e vira um aro fino que se abre e some,
  sem os pedaços pontilhados. Os estilhaços de luz são partículas no jogo.
- feridas/: sobreposição do olho por estágio de dano (1 a 4, cumulativos): veias que saem dos cantos e das bordas
  da esclera e avançam para o meio, e nos estágios 3 e 4 rachaduras na esclera e no aro dourado. As veias são
  claras (quase brancas) porque o jogo as tinge com deus.ferida_cor_N, que vai ficando mais vermelha; as
  rachaduras são escuras com um fio claro do lado, que o mesmo tom deixa vermelho.
  Um arquivo por (estágio, abertura do olho): a sobreposição acompanha as animações do olho quadro a quadro
  (piscar, juízo falhando etc.), recortada na esclera e no aro de cada quadro. vazio.png para os quadros em que
  o olho está fechado ou no clarão branco de dano.
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_feridas_deus.py
"""
import math, os
import numpy as np
from PIL import Image

import arte_deus as A
from arte_deus import C, Tela, amendoa, dilata, N_OLHO, LARG, ALT

D = A.D
PASTA_FERIDAS = os.path.join(D, 'feridas')
ESTAGIOS = 4

# abertura (aberto) de cada quadro das animações do olho, como em arte_deus.anim_olho; None = sem ferida (vazio)
ABERTURA = {
    'idle': [1.0] * 8,
    'piscar': [1, 0.7, 0.35, 0.06, 0.06, 0.35, 0.7, 1],
    'fechado': [0.06],
    'carregar': [1.0] * 8,
    'juizo': [1.0] * 12,
    'juizo_falha': [round(1 - 0.08 * i, 2) for i in range(6)],
    'dano': [None, 1.0],
    'fase': [1.0] * 10,
}
FECHADO_ABAIXO = 0.2   # como em arte_deus.olho: abaixo disso o olho é só a fenda

VEIA = (236, 236, 236)        # miolo da veia (o jogo tinge)
VEIA_ESCURA = (176, 176, 176)  # borda das veias grossas
RACHA = (40, 22, 22)          # fundo da rachadura
RACHA_LUZ = (255, 255, 255)   # fio de luz ao lado da rachadura (tingido)


def nome_ferida(estagio, aberto):
    return 'vazio.png' if aberto is None or aberto < FECHADO_ABAIXO else f'e{estagio}_a{round(aberto * 100):03d}.png'


# ---------------- morte do olho e quebra dos anéis ----------------
def morte_olho():
    quadros = []
    for b in (0.1, 0.3, 0.6, 1.0):                       # clareia até o branco
        quadros.append(A.olho(branco=b, pulso=0.5 * b).img())
    escalas = [1.0, 0.86, 0.72, 0.58, 0.45, 0.33, 0.22, 0.13, 0.06]
    for k, s in enumerate(escalas):                      # encolhe para o centro, branco com aro creme
        t = Tela(N_OLHO)
        tampa = amendoa(t, t.cx, t.cy, max(2, (LARG + 14) * s), max(1.5, (ALT + 9) * s))
        miolo = amendoa(t, t.cx, t.cy, max(1, LARG * s), max(1, ALT * s))
        t.pinta(tampa, C['creme'] if k < 6 else C['pena4'])
        t.pinta(miolo, C['branco'])
        if not t.a.any():
            t.pinta(t.d() < 1.5, C['branco'])
        quadros.append(t.img())
    t = Tela(N_OLHO)                                     # último quadro: nada (o estouro de luz é no jogo)
    quadros.append(t.img())
    assert len(quadros) == 14
    A.salva_anim(quadros, os.path.join(D, 'olho'), 'morte')


def anel_quebra(nome, i):
    """i de 0 a 7: acende (0-2) e vira um aro fino que se abre e some (3-7)."""
    if i < 3:
        im = A.anel(nome, brilho=0.3 * (i + 1))
        if i == 2:   # quase branco: clareia a imagem inteira, mantendo a transparência
            a = np.array(im).astype(float)
            a[..., :3] = a[..., :3] * 0.35 + 255 * 0.65
            im = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
        return im
    t = Tela(N_OLHO)
    k = list(A.RAMPAS_ANEIS).index(nome)
    a0 = -math.pi / 2 + k * 2 * math.pi / 3
    cx, cy = t.cx + math.cos(a0) * 22, t.cy + math.sin(a0) * 22
    d = t.d(cx, cy)
    j = i - 3                                            # 0..4
    meio = 61 + 3 * (j + 1)
    larg = [4, 3, 2, 1.2, 0.7][j]
    m = np.abs(d - meio) <= larg
    claro = A.RAMPAS_ANEIS[nome][3] if j < 3 else A.RAMPAS_ANEIS[nome][2]
    t.pinta(m, C['branco'] if j == 0 else claro)
    return t.img()


def quebra_aneis():
    for nome in A.RAMPAS_ANEIS:
        A.salva_anim([anel_quebra(nome, i) for i in range(8)], os.path.join(D, nome), 'quebra')


# ---------------- feridas do olho ----------------
def caminho(rng, x, y, ang, passos, passo, curva):
    pts = [(x, y)]
    for _ in range(passos):
        ang += rng.uniform(-curva, curva)
        x += math.cos(ang) * passo
        y += math.sin(ang) * passo
        pts.append((x, y))
    return pts


def borda_esclera(u):
    """ponto na borda da esclera aberta (aberto=1) no ângulo u (radianos, medido no centro)."""
    t = Tela(N_OLHO)
    m = amendoa(t, t.cx, t.cy, LARG, ALT)
    r = 0.0
    while True:
        x, y = t.cx + math.cos(u) * (r + 1), t.cy + math.sin(u) * (r + 1)
        if not m[int(round(y)), int(round(x))]:
            return t.cx + math.cos(u) * r, t.cy + math.sin(u) * r
        r += 0.5


def gera_veias():
    """veias em coordenadas do olho aberto: [(estágio em que aparece, pontos, grossa, alcance por estágio)]."""
    rng = np.random.RandomState(214)
    veias = []
    # (ângulo de saída em graus, estágio, grossa): cantos primeiro, depois bordas de cima e de baixo
    saidas = [(180, 1, True), (0, 1, True), (165, 1, False), (15, 1, False),
              (195, 2, False), (345, 2, False), (150, 2, True), (30, 2, True),
              (210, 3, False), (330, 3, False), (120, 3, False), (60, 3, False), (240, 3, True), (300, 3, True),
              (100, 4, False), (80, 4, False), (260, 4, False), (280, 4, False), (135, 4, False), (225, 4, False),
              (45, 4, False), (315, 4, False)]
    for graus, est, grossa in saidas:
        u = math.radians(graus + rng.uniform(-6, 6))
        x, y = borda_esclera(u)
        ang = math.atan2(N_OLHO / 2 - y, N_OLHO / 2 - x) + rng.uniform(-0.35, 0.35)
        pts = caminho(rng, x, y, ang, 34, 1.0, 0.32)
        veias.append((est, pts, grossa))
        # galhos
        for g in range(2 if grossa else 1):
            k = rng.randint(6, 20)
            bx, by = pts[k]
            ba = ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1)
            veias.append((max(est, min(ESTAGIOS, est + 1 + g)), [(bx, by)] + caminho(rng, bx, by, ba, rng.randint(8, 16), 1.0, 0.4)[1:], False))
    return veias


def gera_rachaduras():
    """rachaduras (estágio, pontos): começam fora do aro e entram pela esclera."""
    rng = np.random.RandomState(1214)
    rach = []
    for graus, est, passos in [(-118, 3, 30), (62, 3, 22), (-30, 4, 28), (152, 4, 26), (95, 4, 18)]:
        u = math.radians(graus)
        x, y = N_OLHO / 2 + math.cos(u) * 62, N_OLHO / 2 + math.sin(u) * 50
        ang = math.atan2(N_OLHO / 2 - y, N_OLHO / 2 - x) + rng.uniform(-0.2, 0.2)
        pts = []
        for _ in range(passos):   # zigue-zague: segmentos retos com quebra de ângulo
            seg = rng.randint(2, 5)
            a = ang + rng.uniform(-0.6, 0.6)
            for _ in range(seg):
                x += math.cos(a); y += math.sin(a)
                pts.append((x, y))
        rach.append((est, pts))
        # uma lasca que sai do meio
        k = len(pts) // 2
        bx, by = pts[k]
        ba = ang + rng.choice([-1, 1]) * 0.9
        rach.append((est, [(bx + math.cos(ba) * s, by + math.sin(ba) * s) for s in range(1, 9)]))
    return rach


def raster(pts, w=N_OLHO):
    m = np.zeros((w, w), bool)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for s in np.linspace(0, 1, n + 1):
            x, y = int(round(x0 + (x1 - x0) * s)), int(round(y0 + (y1 - y0) * s))
            if 0 <= x < w and 0 <= y < w:
                m[y, x] = True
    return m


def deforma(pts, aberto):
    """leva os pontos do olho aberto para um olho com essa abertura (achata em y em volta do centro)."""
    c = N_OLHO / 2
    return [(x, c + (y - c) * aberto) for x, y in pts]


def ferida(estagio, aberto, veias, rach):
    t = Tela(N_OLHO)
    alt = max(1.5, ALT * aberto)
    esc = amendoa(t, t.cx, t.cy, LARG, alt)
    tampa = amendoa(t, t.cx, t.cy, LARG + 14, alt + 9)
    # por dentro, longe do contorno escuro: as feridas não pisam nas linhas do desenho
    dentro_esc = esc & ~dilata(~esc)
    dentro_tampa = tampa & ~dilata(~tampa) & ~dilata(esc & ~dilata(~esc) | ~esc & dilata(esc))
    alcance = {1: 0.35, 2: 0.55, 3: 0.75, 4: 1.0}[estagio]
    finas = np.zeros_like(esc)
    grossas = np.zeros_like(esc)
    for est, pts, grossa in veias:
        if est > estagio:
            continue
        # cada estágio a veia avança mais; as que nasceram antes avançam mais
        frac = min(1.0, alcance + 0.15 * (estagio - est))
        n = max(2, int(len(pts) * frac))
        m = raster(deforma(pts[:n], aberto))
        if grossa and estagio >= 3:   # a parte grossa é só o tronco perto da borda (a veia afina para dentro)
            grossas |= raster(deforma(pts[:max(2, int(len(pts) * (0.25 + 0.12 * (estagio - 3))))], aberto))
        finas |= m
    grossas = dilata(grossas) & ~finas
    t.pinta(grossas & dentro_esc, VEIA_ESCURA)
    t.pinta(finas & dentro_esc, VEIA)
    for est, pts in rach:
        if est > estagio:
            continue
        p = deforma(pts, aberto)
        m = raster(p)
        luz = raster([(x + 1, y - 1) for x, y in p]) & ~m
        t.pinta(luz & dentro_esc, RACHA_LUZ)
        t.pinta(m & (dentro_esc | dentro_tampa), RACHA)
    return t.img()


def feridas():
    os.makedirs(PASTA_FERIDAS, exist_ok=True)
    veias, rach = gera_veias(), gera_rachaduras()
    Tela(N_OLHO).img().save(os.path.join(PASTA_FERIDAS, 'vazio.png'))
    feitos = set()
    for anim, ab in ABERTURA.items():
        for a in ab:
            for e in range(1, ESTAGIOS + 1):
                nome = nome_ferida(e, a)
                if nome in feitos or nome == 'vazio.png':
                    continue
                ferida(e, a, veias, rach).save(os.path.join(PASTA_FERIDAS, nome))
                feitos.add(nome)
    return feitos


if __name__ == '__main__':
    morte_olho()
    quebra_aneis()
    print(len(feridas()), 'feridas')
