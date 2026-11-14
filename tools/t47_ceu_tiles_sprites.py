"""Tiles do céu "desolado" (pixel art gerada por código, sem assets de terceiros).

Mesma grade do atlas do inferno (17 x 9 tiles de 32 px, mesmos ids para terreno, pontes, parede de fundo e enfeites),
mas com desenho próprio: piso de mármore rachado com friso de ouro velho, paredes de blocos gastos, nuvem cinza por
baixo, ruína de alvenaria ao fundo, colunas caneladas, grades de portão, árvore morta, entulho e auréolas caídas.

Só desenha imagens: assets/ceu/tiles/tiles_ceu.png e tiles_ceu_2x.png. Não toca no jogo.json.
"""
import math, os, random
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets', 'ceu', 'tiles')
T, COLS, LINS = 32, 17, 9


def h(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


VAZIO = (0, 0, 0, 0)
NUCLEO = h('#2b2e3b')
M_HI, M_L, M_M, M_S, M_D = h('#e4e2da'), h('#c3c4c8'), h('#9a9ca8'), h('#6f7284'), h('#4a4d5e')
O_HI, O_M, O_D = h('#cdb873'), h('#a8894a'), h('#6e5a34')
N_HI, N_L, N_M, N_S, N_D = h('#d4d5dc'), h('#b3b5c0'), h('#8e91a0'), h('#686b7c'), h('#4c4f60')
K = h('#1c1d28')
F_L, F_M, F_S, F_D = h('#62667a'), h('#52566a'), h('#454859'), h('#393c4b')     # parede de fundo
CIPO = h('#5c5a48')
FERRO, FERRO_L = h('#34343f'), h('#55566a')
PAU_L, PAU_M, PAU_S = h('#b9b3a6'), h('#8c867c'), h('#5f5b58')


# ------------------------------------------------------------------ terreno
def topo(px, v, x0=0, x1=T):
    """Piso de mármore: brilho, lajes com juntas a cada 16 px, friso de ouro velho e sombra que some no núcleo."""
    r = random.Random(11 + v)
    veio = {(r.randrange(T), r.randrange(1, 5)) for _ in range(14)}
    for x in range(x0, x1):
        junta = x % 16 == 15
        for y in range(12):
            if y == 0:
                c = M_HI
            elif y < 5:
                c = M_M if (x, y) in veio else M_L
            elif y == 5:
                c = M_M
            elif y == 6:
                c = O_HI if x % 8 == 3 else (O_D if x % 8 in (6, 7) else O_M)
            elif y == 7:
                c = M_S
            elif y == 8:
                c = M_D
            else:
                c = M_D if (x + y) % 2 == 0 and y < 9 + 2 - (x % 4 == 1) else None
            if junta and y < 6:
                c = M_S if y else M_M
            if c:
                px[x, y] = c
    if v:       # variante gasta: rachaduras, friso faltando
        for risco in (((5, 0), (5, 1), (6, 2), (6, 3), (7, 4), (8, 5), (8, 6), (9, 7)),
                      ((25, 0), (24, 1), (24, 2), (23, 3), (22, 4), (22, 5)), ((26, 2), (27, 3), (28, 3))):
            for x, y in risco:
                if x0 <= x < x1:
                    px[x, y] = M_D
        for x, y in ((19, 0), (20, 0), (21, 0), (20, 1)):                # lasca na borda do piso
            if x0 <= x < x1:
                px[x, y] = VAZIO if y == 0 else M_S
        for x in range(9, 15):
            if x0 <= x < x1:
                px[x, 6] = M_S


def parede(px, lado, v, y0=0, y1=T):
    """Blocos gastos na lateral (fiadas de 8 px); lado 'L' recebe luz, 'R' fica na sombra."""
    cores = (M_M, M_L, M_L, M_M, M_M, M_S, M_D) if lado == 'L' else (M_D, M_S, M_M, M_M, M_S, M_S, M_D)
    r = random.Random(23 + v + (lado == 'R'))
    lasca = {r.randrange(T) for _ in range(5 + 3 * v)}
    for y in range(y0, y1):
        for i, c in enumerate(cores):
            x = i if lado == 'L' else T - 1 - i
            if y % 8 == 7:
                c = M_D if i < 6 else NUCLEO
            elif y % 8 == 0 and i < 5 and lado == 'L':
                c = M_HI if i in (1, 2) else c
            px[x, y] = c
        for i in (7, 8):
            if (i + y) % 2 == 0 and i - 7 < (y % 8 != 3) + 0:
                px[i if lado == 'L' else T - 1 - i, y] = M_D
        if y in lasca:
            px[0 if lado == 'L' else T - 1, y] = VAZIO
        if v and y % 16 in (2, 3, 4, 5, 6) and y // 16 % 2 == 0:      # escorrido escuro
            px[3 if lado == 'L' else T - 4, y] = M_S if lado == 'L' else M_D


BOLHAS = {0: ((3, 25, 5), (11, 24, 7), (20, 26, 5), (27, 24, 6)), 1: ((2, 24, 6), (9, 26, 5), (17, 24, 7), (26, 25, 5))}


def nuvem(px, v, base=18, x0=0, x1=T, fura=True):
    """Nuvem suja pendurada por baixo: faixa de sombra junto à pedra e gomos redondos (período de 32 px)."""
    b = [(cx + k * T, cy - 18 + base, r) for cx, cy, r in BOLHAS[v] for k in (-1, 0, 1)]
    fim = base + 14
    for x in range(x0, x1):
        for y in range(base, min(fim, T)):
            d = y - base
            dentro = [(cx, cy, r) for cx, cy, r in b if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r]
            if d < 2:
                c = N_D if (x + y) % 2 == 0 or px[x, y] != NUCLEO else None
            elif d < 4:
                c = N_D
            elif d < 6:
                c = N_S
            elif dentro:
                cx, cy, r = max(dentro, key=lambda q: q[1] + q[2])
                s = (-.5 * (x + .5 - cx) - (y + .5 - cy)) / r
                c = N_L if s > .3 else (N_M if s > -.55 else N_S)
                if s > .3 and r >= 6 and abs(x + 1.5 - cx) < 1.5 and d == 7:
                    c = N_HI
            elif d < 7:
                c = N_S
            else:
                c = VAZIO if fura else N_S
            if c is not None:
                px[x, y] = c
    for x in range(x0, x1):                 # borda de baixo mais escura
        for y in range(base + 6, min(fim, T)):
            if px[x, y][3] and px[x, y] != NUCLEO and (y == T - 1 and fim >= T or (y + 1 < T and px[x, y + 1][3] == 0) or y == fim - 1):
                px[x, y] = N_D


def celula(lados='', cantos='', v=0):
    """Um tile de terreno: lados expostos (T, B, L, R) e cantos internos ('TL', 'TR', 'BL', 'BR')."""
    im = Image.new('RGBA', (T, T), NUCLEO)
    px = im.load()
    if 'L' in lados: parede(px, 'L', v)
    if 'R' in lados: parede(px, 'R', v)
    if 'T' in lados: topo(px, v)
    if 'B' in lados: nuvem(px, v)
    if 'TL' in cantos: topo(px, v, 0, 7)
    if 'TR' in cantos: topo(px, v, T - 7, T)
    if 'BL' in cantos: nuvem(px, v, x0=0, x1=7, fura=False)
    if 'BR' in cantos: nuvem(px, v, x0=T - 7, x1=T, fura=False)
    if 'T' in lados:                                    # quina lascada
        if 'L' in lados: px[0, 0] = VAZIO
        if 'R' in lados: px[T - 1, 0] = VAZIO
    if 'B' in lados:                                    # nuvem arredonda a quina de baixo
        for x in range(6):
            for y in range(24, T):
                if (x - 6) ** 2 + (y - 25) ** 2 > 38:
                    if 'L' in lados: px[x, y] = VAZIO
                    if 'R' in lados: px[T - 1 - x, y] = VAZIO
    return im


def ponte(ponta, v):
    """Plataforma fina: laje de mármore com nuvem rala por baixo; ponta 'L', 'R', 'LR' (solta) ou ''."""
    im = Image.new('RGBA', (T, T), VAZIO)
    px = im.load()
    for x in range(T):
        for y in range(9):
            px[x, y] = NUCLEO
    topo(px, v)
    for x in range(T):
        for y in range(9, 12):
            px[x, y] = VAZIO
        px[x, 8] = M_D
    nuvem(px, v, base=5)
    topo_im = Image.new('RGBA', (T, T), VAZIO)
    topo(topo_im.load(), v)
    im.paste(topo_im.crop((0, 0, T, 9)), (0, 0))
    for lado in ponta:
        for x in range(5):
            for y in range(T):
                xx = x if lado == 'L' else T - 1 - x
                if (y < 9 and x == 0 and y in (0, 8)) or (y >= 9 and (x - 5) ** 2 + (y - 10) ** 2 > 30):
                    px[xx, y] = VAZIO
            if x == 0:
                for y in range(1, 8):
                    px[0 if lado == 'L' else T - 1, y] = M_M if lado == 'L' else M_D
    for x in range(T):                      # nada abaixo da nuvem
        for y in range(20, T):
            px[x, y] = VAZIO
    return im


# ------------------------------------------------------------------ parede de fundo (ruína de alvenaria)
def fundo_tijolo(px, x, y, borda=False):
    lin = y // 6
    xx = (x + (8 if lin % 2 else 0)) % 16
    if y % 6 == 5 or xx == 15:
        px[x, y] = F_D
    elif y % 6 == 0:
        px[x, y] = F_L if borda else F_M
    else:
        px[x, y] = F_M if (x * 7 + lin * 13) % 11 else F_S


def fundo(sheet):
    """Bloco 5x3 (com duas janelas vazias) e pilar de 1 tile: silhueta em degraus de tijolo, como muro em ruínas."""
    px = sheet.load()
    ox, oy, w, hh = 0, 6 * T, 5 * T, 3 * T
    def dentro(x, y):
        bx = (x + (8 if (y // 6) % 2 else 0)) // 16 * 16 + 8 - (8 if (y // 6) % 2 else 0)
        by = y // 6 * 6 + 3
        nx, ny = (bx - w / 2) / (w / 2), (by - hh / 2) / (hh / 2 + 2)
        return abs(nx) ** 3.2 + abs(ny) ** 3.2 <= 1.0
    for y in range(hh):
        for x in range(w):
            if dentro(x, y) and not (T <= y < 2 * T and (T <= x < 2 * T or 3 * T <= x < 4 * T)):
                viz = all(dentro(x + dx, y + dy) for dx, dy in ((0, -6), (-16, 0)) if 0 <= x + dx < w and 0 <= y + dy < hh)
                fundo_tijolo(px, ox + x, oy + y, not viz)
                px[ox + x, oy + y] = px[ox + x, oy + y]
    # pilar (coluna 5): topo em ruína, corpo reto
    r = random.Random(5)
    corte = [r.choice((2, 2, 8, 8, 14)) for _ in range(2)]
    for y in range(hh):
        for x in range(T):
            if x < 3 or x >= T - 3:
                continue
            if y < corte[0 if x < 16 else 1] + (6 if (x // 8) % 2 else 0):
                continue
            fundo_tijolo(px, 5 * T + x, oy + y, x in (3, T - 4))
            if x == 3: px[5 * T + x, oy + y] = F_L
            if x == T - 4: px[5 * T + x, oy + y] = F_D
    for y in range(T):                      # 143: miolo liso da parede de fundo
        for x in range(T):
            fundo_tijolo(px, 7 * T + x, 8 * T + y)


# ------------------------------------------------------------------ enfeites
def coluna(d, x, y0, y1, larg=14, capitel=True, base=True, quebra=None, seed=0):
    """Coluna canelada de x (centro) entre y0 e y1; quebra = lista de alturas do topo quebrado por caneladura."""
    r = random.Random(seed)
    xl = x - larg // 2
    faixa = [M_M, M_L, M_HI, M_L, M_M, M_L, M_M, M_S, M_M, M_S, M_D, M_S, M_D, M_D]
    ys = y0 + (7 if capitel else 0)
    ye = y1 - (7 if base else 0)
    for i in range(larg):
        c = faixa[int(i * len(faixa) / larg)]
        topo_i = ys + (quebra[i * len(quebra) // larg] if quebra else 0)
        d.line([(xl + i, topo_i), (xl + i, ye)], fill=c)
        if quebra:
            d.point((xl + i, topo_i), fill=M_HI if i < larg // 2 else M_M)
    for y in range(ys + 9, ye, 13):         # juntas dos tambores
        d.line([(xl, y), (xl + larg - 1, y)], fill=M_D)
        d.line([(xl, y + 1), (xl + larg // 2, y + 1)], fill=M_HI)
    for _ in range(3):                       # rachaduras
        cx, cy = xl + r.randrange(2, larg - 2), r.randrange(ys + 4, max(ys + 5, ye - 6))
        for k in range(r.randrange(3, 7)):
            d.point((cx, cy + k), fill=M_D)
            cx += r.choice((-1, 0, 1))
    d.line([(xl - 1, ys), (xl - 1, ye)], fill=K)
    d.line([(xl + larg, ys), (xl + larg, ye)], fill=K)
    if capitel:
        d.rectangle([xl - 5, y0, xl + larg + 4, y0 + 2], fill=M_L, outline=K)
        d.line([(xl - 4, y0 + 1), (xl + larg + 3, y0 + 1)], fill=M_HI)
        for sx in (xl - 4, xl + larg):       # volutas
            d.rectangle([sx, y0 + 3, sx + 3, y0 + 6], fill=M_M, outline=K)
            d.point((sx + 1, y0 + 4), fill=M_HI)
        d.rectangle([xl, y0 + 3, xl + larg - 1, y0 + 5], fill=M_M)
        d.line([(xl, y0 + 4), (xl + larg - 1, y0 + 4)], fill=O_M)
        d.line([(xl, y0 + 6), (xl + larg - 1, y0 + 6)], fill=M_D)
    if base:
        d.rectangle([xl - 2, ye + 1, xl + larg + 1, ye + 3], fill=M_M, outline=K)
        d.line([(xl - 1, ye + 2), (xl + larg // 2, ye + 2)], fill=M_L)
        d.rectangle([xl - 5, ye + 4, xl + larg + 4, y1], fill=M_S, outline=K)
        d.line([(xl - 4, ye + 5), (xl + larg, ye + 5)], fill=M_L)


def entulho(d, x0, y1, larg, alt, seed, tambor=False):
    """Monte de pedras de mármore partidas apoiado em y1."""
    r = random.Random(seed)
    n = max(3, larg * alt // 40)
    pedras = []
    for _ in range(n):
        u = r.random()
        cx = x0 + 3 + u * (larg - 6)
        topo_max = alt * (1 - abs(u - .5) * 1.7)
        cy = y1 - r.random() * max(1, topo_max - 3)
        pedras.append((cy, cx, r.randrange(3, 7), r.randrange(2, 5)))
    for cy, cx, a, b in sorted(pedras):
        b = min(b, int(y1 - cy) + 1)
        box = [max(x0, cx - a), cy - b, min(x0 + larg - 1, cx + a), min(y1, cy + b)]
        d.rectangle(box, fill=M_M, outline=K)
        d.line([(box[0] + 1, box[1] + 1), (box[2] - 1, box[1] + 1)], fill=M_HI)
        d.line([(box[0] + 1, box[1] + 2), (box[0] + 1, box[3] - 1)], fill=M_L)
        d.line([(box[2] - 1, box[1] + 2), (box[2] - 1, box[3] - 1)], fill=M_S)
        if box[3] - box[1] > 3:
            d.line([(box[0] + 2, box[3] - 1), (box[2] - 1, box[3] - 1)], fill=M_D)
    if tambor:                               # tambor de coluna tombado
        cx, cy = x0 + larg * .62, y1 - 5
        d.rectangle([cx - 8, cy - 5, cx + 6, cy + 5], fill=M_M, outline=K)
        for k, c in enumerate((M_HI, M_L, M_L, M_M, M_S, M_M, M_S, M_D, M_D)):
            d.line([(cx - 7, cy - 4 + k), (cx + 5, cy - 4 + k)], fill=c)
        d.ellipse([cx + 3, cy - 5, cx + 9, cy + 5], fill=M_S, outline=K)
        d.ellipse([cx + 5, cy - 2, cx + 7, cy + 2], fill=M_D)


def aureola(d, cx, cy, rx, ry, quebrada=False):
    for k, c in ((0, K), (1, O_M), (2, O_D)):
        d.ellipse([cx - rx + k, cy - ry + k, cx + rx - k, cy + ry - k], outline=c)
    d.arc([cx - rx + 1, cy - ry + 1, cx + rx - 1, cy + ry - 1], 180, 300, fill=O_HI)
    d.ellipse([cx - rx + 3, cy - ry + 3, cx + rx - 3, cy + ry - 3], outline=K)
    if quebrada:
        d.rectangle([cx + rx - 5, cy - ry - 1, cx + rx + 1, cy - ry + 5], fill=VAZIO)


def olho_fechado(d, cx, cy, w=5):
    d.arc([cx - w, cy - 3, cx + w, cy + 3], 0, 180, fill=M_D)
    for k in (-w + 1, 0, w - 1):
        d.point((cx + k, cy + 4 + (k == 0)), fill=M_D)


def lapides(sheet):
    d = ImageDraw.Draw(sheet)
    # 13: estátua sem cabeça nem asas sobre pedestal
    x, y = 13 * T, 0
    d.rectangle([x + 6, y + 24, x + 25, y + 31], fill=M_S, outline=K)
    d.line([(x + 7, y + 25), (x + 24, y + 25)], fill=M_L)
    d.polygon([(x + 9, y + 23), (x + 11, y + 12), (x + 21, y + 12), (x + 23, y + 23)], fill=M_M, outline=K)      # manto
    d.polygon([(x + 10, y + 12), (x + 10, y + 8), (x + 13, y + 5), (x + 19, y + 5), (x + 22, y + 8), (x + 22, y + 12)], fill=M_L, outline=K)
    d.line([(x + 14, y + 4), (x + 15, y + 3), (x + 16, y + 4), (x + 17, y + 3), (x + 18, y + 4)], fill=K)       # pescoço partido
    d.line([(x + 14, y + 5), (x + 18, y + 5)], fill=M_S)
    d.line([(x + 11, y + 9), (x + 11, y + 22)], fill=M_HI)
    for k in (14, 17, 20):
        d.line([(x + k, y + 14), (x + k - 1, y + 22)], fill=M_S)
    d.line([(x + 12, y + 13), (x + 16, y + 15), (x + 20, y + 13)], fill=M_D)                    # braços cruzados
    # 14: auréola caída, meio enterrada
    x = 14 * T
    aureola(d, x + 15, y + 22, 11, 9, quebrada=True)
    d.rectangle([x + 2, y + 27, x + 29, y + 31], fill=M_S, outline=K)
    d.line([(x + 3, y + 28), (x + 28, y + 28)], fill=M_L)
    # 30: estela com olho fechado
    x, y = 13 * T, T
    d.polygon([(x + 8, y + 31), (x + 8, y + 9), (x + 12, y + 5), (x + 20, y + 5), (x + 24, y + 9), (x + 24, y + 31)], fill=M_M, outline=K)
    d.line([(x + 9, y + 10), (x + 9, y + 30)], fill=M_L); d.line([(x + 12, y + 6), (x + 20, y + 6)], fill=M_HI)
    d.line([(x + 23, y + 10), (x + 23, y + 30)], fill=M_S)
    olho_fechado(d, x + 16, y + 14)
    for k in (19, 22, 25):
        d.line([(x + 12, y + k), (x + 20, y + k)], fill=M_S)
    d.line([(x + 21, y + 6), (x + 18, y + 11), (x + 20, y + 16)], fill=M_D)
    # 31: asa de pedra partida sobre plinto
    x = 14 * T
    d.rectangle([x + 5, y + 26, x + 26, y + 31], fill=M_S, outline=K)
    d.line([(x + 6, y + 27), (x + 25, y + 27)], fill=M_L)
    for k in range(5):
        a = math.radians(-100 + k * 17)
        comp = 19 - k * 2
        p = (x + 12 + comp * math.cos(a), y + 25 + comp * math.sin(a))
        d.line([(x + 12, y + 25), p], fill=K, width=5)
        d.line([(x + 12, y + 25), p], fill=M_L if k % 2 == 0 else M_M, width=3)
        d.line([(x + 12, y + 24), (p[0], p[1] - 1)], fill=M_HI)
    d.rectangle([x + 9, y + 21, x + 15, y + 25], fill=M_M, outline=K)


def frontao(sheet):
    """15-16: frontão triangular com olho; 32-33: friso com tríglifos e miolo do terreno por baixo."""
    d = ImageDraw.Draw(sheet)
    x, y = 15 * T, 0
    d.polygon([(x, y + 31), (x + 31, y + 4), (x + 32, y + 4), (x + 63, y + 31)], fill=M_M, outline=K)
    d.line([(x + 3, y + 30), (x + 31, y + 6)], fill=M_HI); d.line([(x + 32, y + 6), (x + 60, y + 30)], fill=M_S)
    d.polygon([(x + 12, y + 29), (x + 31, y + 13), (x + 32, y + 13), (x + 51, y + 29)], fill=M_D)
    d.ellipse([x + 26, y + 19, x + 37, y + 27], fill=M_S, outline=K)
    d.ellipse([x + 30, y + 21, x + 33, y + 25], fill=K)
    for k in range(4):
        d.line([(x + 31 + (k - 1.5) * 7, y + 29), (x + 31 + (k - 1.5) * 11, y + 16 + abs(k - 1.5) * 5)], fill=M_S)
    d.line([(x + 44, y + 15), (x + 41, y + 20), (x + 44, y + 24)], fill=K)                       # rachadura
    y = T
    d.rectangle([x, y, x + 63, y + 31], fill=NUCLEO)
    d.rectangle([x, y, x + 63, y + 3], fill=M_L, outline=K)
    d.line([(x + 1, y + 1), (x + 62, y + 1)], fill=M_HI)
    d.rectangle([x, y + 4, x + 63, y + 12], fill=M_M)
    for k in range(0, 64, 16):
        for j in (3, 6, 9):
            d.line([(x + k + j, y + 5), (x + k + j, y + 11)], fill=M_D)
    d.line([(x, y + 13), (x + 63, y + 13)], fill=O_D)
    d.line([(x, y + 14), (x + 63, y + 14)], fill=M_D)
    for xx in range(64):
        if xx % 2 == 0:
            d.point((x + xx, y + 15), fill=M_D)
    d.line([(x, y + 4), (x, y + 31)], fill=K); d.line([(x + 63, y + 4), (x + 63, y + 31)], fill=K)


def grade(sheet, cx, cy, alt, seed):
    """Grade de portão: lanças de ferro com ponta de ouro velho, uma ou outra torta ou faltando."""
    d = ImageDraw.Draw(sheet)
    r = random.Random(seed)
    x, y = cx * T, cy * T
    for i, bx in enumerate(range(3, T, 6)):
        if r.random() < .12:
            d.line([(x + bx, y + 27), (x + bx, y + 31)], fill=FERRO)
            continue
        a = alt - r.choice((0, 0, 2, 3, 5))
        topo_y = y + 31 - a
        torto = r.choice((0, 0, 0, -2, 2))
        d.line([(x + bx, y + 31), (x + bx, topo_y + 6), (x + bx + torto, topo_y + 2)], fill=FERRO)
        d.line([(x + bx + 1, y + 31), (x + bx + 1, topo_y + 6)], fill=FERRO_L)
        tx = x + bx + torto
        d.polygon([(tx, topo_y - 3), (tx - 2, topo_y + 2), (tx + 2, topo_y + 2)], fill=O_D, outline=K)
        d.point((tx, topo_y - 1), fill=O_HI)
    for yy in (y + 31 - alt // 3, y + 29):
        d.line([(x, yy), (x + 31, yy)], fill=FERRO)
        d.line([(x, yy - 1), (x + 31, yy - 1)], fill=FERRO_L)


def arvore(sheet):
    """83, 84, 100, 101: árvore morta e pálida (64 x 64)."""
    d = ImageDraw.Draw(sheet)
    x, y = 15 * T, 4 * T
    r = random.Random(42)
    def galho(px_, py, ang, comp, larg, nivel):
        ex, ey = px_ + comp * math.cos(ang), py + comp * math.sin(ang)
        d.line([(px_, py), (ex, ey)], fill=K, width=larg + 2)
        gal.append(((px_, py), (ex, ey), larg))
        if nivel:
            for s in (-1, 1):
                galho(ex, ey, ang + s * r.uniform(.35, .75), comp * r.uniform(.55, .75), max(1, larg - 1), nivel - 1)
    gal = []
    galho(x + 31, y + 63, -math.pi / 2 + .08, 22, 5, 4)
    for a, b, larg in gal:
        d.line([a, b], fill=PAU_M, width=larg)
        if larg > 1:
            d.line([(a[0] - larg // 2, a[1]), (b[0] - larg // 2, b[1])], fill=PAU_L)
            d.line([(a[0] + larg // 2, a[1]), (b[0] + larg // 2, b[1])], fill=PAU_S)
    for s_, cor in ((-1, PAU_L), (1, PAU_S)):                           # raízes
        d.line([(x + 31 + s_ * 2, y + 57), (x + 31 + s_ * 8, y + 63)], fill=K, width=4)
        d.line([(x + 31 + s_ * 2, y + 57), (x + 31 + s_ * 8, y + 63)], fill=cor, width=2)
    d.ellipse([x + 29, y + 46, x + 33, y + 51], fill=K)                 # oco


def pingente(sheet):
    """114: miolo com nuvem por baixo; 131 e 148: fiapo de nuvem escorrendo."""
    sheet.paste(celula('B', v=1), (12 * T, 6 * T))
    px = sheet.load()
    x0, y0 = 12 * T, 6 * T + 28
    r = random.Random(9)
    for y in range(56):
        meia = 9 * (1 - y / 56) ** 1.3 + 1
        desvio = 2 * math.sin(y / 6)
        for x in range(T):
            dx = x + .5 - (16 + desvio)
            if abs(dx) <= meia:
                s = dx / meia
                c = N_L if s < -.45 else (N_M if s < .25 else N_S)
                if abs(dx) > meia - 1:
                    c = N_D
                if y > 30 and (x + y) % 2 == 0 and r.random() < (y - 30) / 30:
                    continue
                px[x0 + x, y0 + y] = c


def coluna_tombada(sheet):
    """115-116, 132-133, 149-150: coluna grande inclinada e partida, cravada num monte de entulho (64 x 96)."""
    tmp = Image.new('RGBA', (40, 110), VAZIO)
    coluna(ImageDraw.Draw(tmp), 20, 4, 109, larg=18, capitel=False, base=False, quebra=[9, 6, 7, 3, 0, 2, 5, 4, 8], seed=3)
    tmp = tmp.rotate(-12, resample=Image.NEAREST, expand=True)
    x, y = 13 * T, 6 * T
    sheet.alpha_composite(tmp.crop((0, 0, tmp.width, 92)), (x + 2, y + 2))
    d = ImageDraw.Draw(sheet)
    d.rectangle([x, y + 96, x + 63, y + 100], fill=VAZIO)
    entulho(d, x + 1, y + 95, 62, 24, 7)


def enfeites(sheet):
    d = ImageDraw.Draw(sheet)
    lapides(sheet)
    frontao(sheet)
    # 47/64: coluna partida com capitel perdido; 65/82/99: coluna inteira; 81/98: toco de coluna
    coluna(d, 13 * T + 16, 2 * T + 3, 4 * T - 1, capitel=False, quebra=[5, 3, 6, 2, 0, 1, 4], seed=1)
    coluna(d, 14 * T + 16, 3 * T, 6 * T - 1, seed=2)
    coluna(d, 13 * T + 16, 4 * T + 14, 6 * T - 1, capitel=False, quebra=[0, 2, 5, 7, 10, 12, 15], seed=4)
    sheet.paste(celula('B', v=0), (14 * T, 2 * T))          # 48: miolo com nuvem por baixo
    grade(sheet, 15, 2, 22, 1); grade(sheet, 16, 2, 22, 2)
    grade(sheet, 15, 3, 30, 3); grade(sheet, 16, 3, 30, 4)
    arvore(sheet)
    pingente(sheet)
    coluna_tombada(sheet)
    d = ImageDraw.Draw(sheet)
    # 111-113: cacos baixos; 128-130: montes médios; 145: tambor; 146-147: monte grande
    entulho(d, 9 * T + 2, 7 * T - 1, 28, 5, 11)
    entulho(d, 10 * T + 4, 7 * T - 1, 24, 9, 12)
    entulho(d, 11 * T + 1, 7 * T - 1, 30, 13, 13)
    entulho(d, 9 * T + 1, 8 * T - 1, 30, 18, 14)
    entulho(d, 10 * T + 1, 8 * T - 1, 30, 14, 15, tambor=True)
    entulho(d, 11 * T + 1, 8 * T - 1, 30, 22, 16)
    entulho(d, 9 * T + 3, 9 * T - 1, 26, 8, 17, tambor=True)
    entulho(d, 10 * T + 2, 9 * T - 1, 60, 27, 18)
    aureola(d, 11 * T + 6, 9 * T - 9, 7, 6, quebrada=True)


# ------------------------------------------------------------------ atlas
def atlas():
    sheet = Image.new('RGBA', (COLS * T, LINS * T), VAZIO)
    def poe(c, l, im):
        sheet.paste(im, (c * T, l * T))
    for v in (0, 1):
        o = v * 3
        for l in range(3):
            for c in range(3):
                if (l, c) == (1, 1):
                    continue
                fora = ('T' if l == 0 else '') + ('B' if l == 2 else '') + ('L' if c == 0 else '') + ('R' if c == 2 else '')
                poe(c, o + l, celula(fora, v=v))                                  # bloco cheio (9 fatias)
                if l != 1 and c != 1:                                             # anel fino: quinas
                    poe(3 + c, o + l, celula(fora, ('B' if l == 0 else 'T') + ('R' if c == 0 else 'L'), v))
                    poe(6 + c, o + l, celula('', ('B' if l == 0 else 'T') + ('R' if c == 0 else 'L'), v))
                elif c == 1:
                    poe(4, o + l, celula('TB', v=v))
                    poe(7, o + l, celula('B' if l == 0 else 'T', v=v))
                else:
                    poe(3 + c, o + l, celula('LR', v=v))
                    poe(6 + c, o + l, celula('R' if c == 0 else 'L', v=v))
        poe(10, o, celula('TLR', v=v)); poe(9, o + 1, celula('TBL', v=v)); poe(11, o + 1, celula('TBR', v=v))
        poe(10, o + 1, celula('', 'TL TR BL BR', v))
        poe(10, o + 2, celula('BLR', v=v))
        poe(12, o, celula('TLR', v=v)); poe(12, o + 1, celula('LR', v=v)); poe(12, o + 2, celula('BLR', v=v))
        poe(6, 6 + v, ponte('L', v)); poe(7, 6 + v, ponte('', v)); poe(8, 6 + v, ponte('R', v))
    poe(6, 8, ponte('LR', 0))
    poe(8, 8, Image.new('RGBA', (T, T), NUCLEO))            # 144: miolo liso do terreno
    fundo(sheet)
    enfeites(sheet)
    return sheet


def gera():
    os.makedirs(PASTA, exist_ok=True)
    s = atlas()
    s.save(os.path.join(PASTA, 'tiles_ceu.png'))
    s.resize((s.width * 2, s.height * 2), Image.NEAREST).save(os.path.join(PASTA, 'tiles_ceu_2x.png'))
    return s


if __name__ == '__main__':
    print(gera().size)
