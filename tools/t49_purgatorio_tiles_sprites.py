"""Tiles do purgatório: montanha / floresta musgosa de cores apagadas (pixel art gerada por código).

Mesma grade dos atlas do inferno e do céu (17 x 9 tiles de 32 px, mesmos ids para terreno, pontes, parede de fundo
e enfeites), com desenho próprio: capim e musgo irregulares por cima, rocha em camadas nas laterais, pedra lascada
com raízes por baixo, tronco caído como ponte, paredão de montanha ao fundo, pinheiros, árvore torta, tocos,
samambaias, cogumelos, pedras e marcos de pedra empilhada.

Só desenha imagens: assets/purgatorio/tiles/tiles_purgatorio.png e tiles_purgatorio_2x.png. Não toca no jogo.json.
"""
import math, os, random
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets', 'purgatorio', 'tiles')
T, COLS, LINS = 32, 17, 9


def h(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


VAZIO = (0, 0, 0, 0)
K = h('#1b1c18')
NUCLEO = h('#2a2b25')
G_HI, G_L, G_M, G_S, G_D = h('#99a078'), h('#7b875d'), h('#606e4a'), h('#48553b'), h('#36402f')      # musgo / capim
R_HI, R_L, R_M, R_S, R_D = h('#a39d8e'), h('#857f72'), h('#69645a'), h('#504c45'), h('#3b3833')      # rocha
P_L, P_M, P_S, P_D = h('#8a7359'), h('#6b5744'), h('#503f33'), h('#3a2e27')                          # madeira / raiz
F_L, F_M, F_S, F_D = h('#4d5248'), h('#41463e'), h('#373b35'), h('#2f322d')                          # paredão de fundo
A_L, A_M, A_S, A_D = h('#5f6f55'), h('#4a5a47'), h('#39483b'), h('#2b3830')                          # agulhas de pinheiro
C_L, C_M = h('#c4b9a2'), h('#9a8c78')                                                              # cogumelo pálido

GRAMA = [1, 0, 2, 1, 1, 3, 1, 0, 1, 2, 1, 1, 0, 1, 3, 2, 1, 1, 0, 2, 1, 1, 2, 0, 1, 3, 1, 1, 2, 1, 0, 1]
PINGO = [0, 0, 1, 2, 1, 0, 0, 0, 1, 3, 4, 2, 0, 0, 1, 1, 0, 0, 2, 3, 1, 0, 0, 0, 1, 2, 5, 3, 1, 0, 0, 1]
LADO = [0, 0, 1, 1, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 1, 0, 0, 1, 1, 2, 1, 0, 0, 0, 0, 1, 1, 0, 0, 2, 1, 0]
BAIXO = [2, 3, 4, 3, 2, 1, 0, 1, 3, 4, 5, 4, 3, 2, 2, 3, 4, 3, 1, 0, 1, 2, 4, 5, 4, 3, 1, 0, 1, 2, 3, 2]
RAIZES = (6, 19, 27)


def gira(lista, v):
    return lista[13 * v:] + lista[:13 * v]


# ------------------------------------------------------------------ terreno
def topo(px, v, x0=0, x1=T, capim=True):
    g, p = gira(GRAMA, v), gira(PINGO, v)
    for x in range(x0, x1):
        g0 = g[x] if capim else 0
        fim = 8 + p[x]
        for y in range(16):
            if y < g0:
                c = VAZIO
            elif y == g0:
                c = G_HI if g0 < 3 else G_L
            elif y < g0 + 2:
                c = G_L
            elif y < 6:
                c = G_M if (x * 3 + y) % 7 else G_L
            elif y < fim:
                c = G_S if y < fim - 1 else G_D
            elif y < fim + 2:
                c = R_D
            elif y < fim + 4:
                c = R_D if (x + y) % 2 == 0 else None
            else:
                c = None
            if c is not None:
                px[x, y] = c
    for sx, sy in ((4, 15), (15, 17), (24, 16)) if not v else ((9, 17), (20, 15), (29, 16)):     # pedrinhas na terra
        if x0 <= sx < x1 - 1:
            px[sx, sy], px[sx + 1, sy] = R_S, R_M
            px[sx, sy + 1] = R_D
    if v:                                   # variante: cogumelos pálidos
        for mx in (7, 22):
            if x0 <= mx - 1 and mx + 1 < x1:
                y = g[mx]
                px[mx, y] = C_M
                for k in (-1, 0, 1):
                    px[mx + k, max(0, y - 1)] = C_L if k < 1 else C_M


def parede(px, lado, v, y0=0, y1=T):
    perfil = gira(LADO, v + (lado == 'R'))
    cores = (R_L, R_M, R_M, R_S, R_M, R_S, R_D) if lado == 'L' else (R_D, R_S, R_S, R_M, R_S, R_D, R_D)
    for y in range(y0, y1):
        ins = perfil[y]
        for i in range(9):
            x = i if lado == 'L' else T - 1 - i
            if i < ins:
                c = VAZIO
            elif i == ins:
                c = R_HI if lado == 'L' and y % 11 in (0, 6) else cores[0]
            elif i < 7:
                c = cores[i]
                if (y + i // 2) % 11 == 5:                      # veio da camada, levemente inclinado
                    c = R_D
                elif (y + i // 2) % 11 == 6 and lado == 'L' and i < 4:
                    c = R_L
            else:
                c = R_D if (i + y) % 2 == 0 else None
            if c is not None:
                px[x, y] = c
        if (y + 5 * v) % 16 in (2, 3, 4, 5, 6, 7):              # tufo de musgo agarrado na rocha
            larg = (1, 2, 3, 3, 2, 1)[(y + 5 * v) % 16 - 2]
            for i in range(ins, ins + larg):
                px[i if lado == 'L' else T - 1 - i, y] = (G_L if i == ins else G_M) if lado == 'L' else (G_S if i == ins else G_M)


def fundo_pedra(px, v, x0=0, x1=T, fura=True):
    b = gira(BAIXO, v)
    for x in range(x0, x1):
        fim = T - (b[x] if fura else 0)
        for y in range(19, T):
            d = y - 19
            if y >= fim:
                c = VAZIO
            elif y == fim - 1 and fura:
                c = K
            elif d < 2:
                c = R_D if (x + y) % 2 == 0 else None
            elif d < 5:
                c = R_D
            elif (x * 5 + y * 3) % 13 < 2:
                c = R_M
            else:
                c = R_S if (x // 5 + y // 4) % 2 else R_D
            if c is not None:
                px[x, y] = c
    for rx in RAIZES:                       # raízes que descem pela pedra e pendem
        rx = (rx + 13 * v) % T
        if x0 <= rx < x1:
            x = rx
            for y in range(16, T - (1 if fura else 0)):
                px[x, y] = P_M if y % 3 else P_L
                if y in (21, 26) and x0 < x < x1 - 1:
                    x += 1 if (rx + y) % 2 else -1
                    px[x, y] = P_S


def celula(lados='', cantos='', v=0):
    im = Image.new('RGBA', (T, T), NUCLEO)
    px = im.load()
    if 'L' in lados: parede(px, 'L', v)
    if 'R' in lados: parede(px, 'R', v)
    if 'B' in lados: fundo_pedra(px, v)
    if 'T' in lados: topo(px, v)
    if 'TL' in cantos: topo(px, v, 0, 7, capim=False)
    if 'TR' in cantos: topo(px, v, T - 7, T, capim=False)
    if 'BL' in cantos: fundo_pedra(px, v, 0, 7, fura=False)
    if 'BR' in cantos: fundo_pedra(px, v, T - 7, T, fura=False)
    for lado in 'LR':
        if lado not in lados:
            continue
        def X(i):
            return i if lado == 'L' else T - 1 - i
        if 'T' in lados:                                    # o musgo arredonda a quina de cima
            for i, corte in enumerate((4, 2, 1)):
                for y in range(corte):
                    px[X(i), y] = VAZIO
                px[X(i), corte] = G_HI if lado == 'L' else G_M
        if 'B' in lados:                                    # quina de baixo lascada
            for i, corte in enumerate((7, 5, 3, 2)):
                for y in range(T - corte, T):
                    px[X(i), y] = VAZIO
                px[X(i), T - corte - 1] = K
    return im


def ponte(ponta, v):
    """Tronco caído: musgo e capim por cima, casca por baixo; a ponta mostra os anéis do corte."""
    im = Image.new('RGBA', (T, T), VAZIO)
    px = im.load()
    g = gira(GRAMA, v)
    for x in range(T):
        g0 = min(g[x], 2)
        for y in range(g0, 15):
            if y == g0:
                c = G_HI
            elif y < 3:
                c = G_L if (x + y) % 3 else G_M
            elif y == 3:
                c = G_S if gira(PINGO, v)[x] < 2 else G_M
            elif y == 4:
                c = P_L if gira(PINGO, v)[x] < 2 else G_S
            elif y < 8:
                c = P_M if (x * 7 + y * 5 + v) % 11 > 1 else P_L
            elif y < 12:
                c = P_S if (x * 5 + y * 3 + v) % 9 > 1 else P_M
            elif y == 12:
                c = P_D
            elif y == 13:
                c = K
            else:
                c = VAZIO
            px[x, y] = c
        if x % 9 == 4 + v:                  # nó / rachadura da casca
            px[x, 7], px[x, 8], px[min(x + 1, T - 1), 8] = P_D, P_D, P_D
    for lado in ponta:                      # corte do tronco: contorno e anéis
        def X(i):
            return i if lado == 'L' else T - 1 - i
        for y in range(T):
            px[X(0), y] = VAZIO
            if px[X(1), y][3]:
                px[X(1), y] = K if 2 <= y <= 12 else VAZIO
        for y in range(4, 12):
            px[X(2), y] = P_L
            px[X(3), y] = P_L if y in (4, 11) else (P_M if y in (5, 10) else P_L)
        for y in (6, 7, 8, 9):
            px[X(3), y] = P_M if y in (6, 9) else P_S
        px[X(4), 4], px[X(4), 11] = P_M, P_D
    return im


# ------------------------------------------------------------------ paredão de fundo
def fundo_rocha(px, x, y, luz=False):
    c = F_M
    if (x + 2 * y) % 17 == 0 or (x + 2 * y) % 17 == 1 and y % 3:
        c = F_D                                             # fendas diagonais
    elif (3 * x - y) % 23 < 2:
        c = F_S
    elif (x * 7 + y * 13) % 29 == 0:
        c = A_D                                             # pontos de musgo
    if luz:
        c = F_L
    px[x, y] = c


def fundo(sheet):
    """Bloco 5x3 em forma de serra (picos irregulares em cima, base reta) com duas aberturas, e uma agulha de pedra."""
    px = sheet.load()
    oy, w, hh = 6 * T, 5 * T, 3 * T
    r = random.Random(31)
    picos = [(18, 20), (50, 4), (86, 12), (118, 2), (146, 16)]
    def alto(x):
        melhor = hh
        for cx, cy in picos:
            melhor = min(melhor, cy + abs(x - cx) * 1.15 + (x * 7 % 5) * .6)
        return int(min(melhor, 40))
    for x in range(w):
        a = alto(x) + (3 if x < 3 or x >= w - 3 else 0)
        for y in range(a, hh):
            if T <= y < 2 * T and (T <= x < 2 * T or 3 * T <= x < 4 * T):
                continue
            fundo_rocha(px, x, oy + y, luz=y < a + 2 or (alto(max(0, x - 1)) > y))
    # agulha de pedra (coluna 5)
    for y in range(hh):
        meia = min(13, 2 + y * .45) - (1 if (y // 5) % 2 else 0)
        for x in range(T):
            dx = x + .5 - 16
            if abs(dx) <= meia:
                fundo_rocha(px, 5 * T + x, oy + y, luz=dx < -meia + 2)
                if dx > meia - 2:
                    px[5 * T + x, oy + y] = F_D
    for y in range(T):                      # 143: miolo liso do paredão
        for x in range(T):
            fundo_rocha(px, 7 * T + x, 8 * T + y)


# ------------------------------------------------------------------ enfeites
def pedra(d, cx, base, rx, ry, musgo=True, seed=0):
    """Pedra arredondada apoiada em 'base', com luz em cima à esquerda e capa de musgo."""
    r = random.Random(seed)
    for y in range(int(base - 2 * ry), int(base) + 1):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - (base - ry)) / ry
            e = abs(nx) ** 2.4 + abs(ny) ** 2.4
            if e <= 1:
                s = -nx * .6 - ny * .8
                c = R_L if s > .45 else (R_M if s > -.1 else (R_S if s > -.6 else R_D))
                if e > .8 - .5 / max(rx, ry) * 4:
                    c = K if e > 1 - 2.2 / max(rx, ry) else c
                if musgo and ny < -.35 + .25 * math.sin(x * 1.3 + seed) and c != K:
                    c = G_L if ny < -.7 else (G_M if s > 0 else G_S)
                if c not in (K,) and (x * 5 + y * 7 + seed) % 19 == 0:
                    c = R_D
                d.point((x, y), fill=c)


def monte(d, x0, base, larg, alt, seed):
    r = random.Random(seed)
    n = max(2, larg // 9)
    ps = []
    for i in range(n):
        u = (i + .5) / n
        ry = max(2.5, alt * (1 - abs(u - .5) * 1.5) * r.uniform(.35, .55))
        ps.append((ry, x0 + 4 + u * (larg - 8) + r.uniform(-1.5, 1.5), min(ry * r.uniform(1.1, 1.6), larg / n * .8 + 2)))
    for ry, cx, rx in sorted(ps, reverse=True):
        rx = min(rx, cx - x0, x0 + larg - 1 - cx)
        pedra(d, cx, base, max(2.5, rx), ry, seed=seed + int(cx))


def capim(d, x0, base, larg, alt, seed, samambaia=False):
    r = random.Random(seed)
    for i in range(larg // (2 if not samambaia else 5)):
        x = x0 + 1 + r.randrange(larg - 2)
        a = alt * r.uniform(.45, 1)
        inc = r.uniform(-.5, .5)
        cor = r.choice((G_M, G_S, G_L, A_M))
        for k in range(int(a)):
            px_ = x + inc * k * k / max(a, 1) * .6
            if x0 <= px_ < x0 + larg:
                d.point((px_, base - k), fill=cor if k < a - 1 else G_HI)
                if samambaia and k > 2 and k % 2 == 0:
                    f = max(1, int((a - k) * .45))
                    for j in range(1, f + 1):
                        for s in (-1, 1):
                            if x0 <= px_ + s * j < x0 + larg:
                                d.point((px_ + s * j, base - k + j // 2), fill=G_S if j > 1 else cor)


def cogumelo(d, x, base, alt=4):
    d.line([(x, base), (x, base - alt)], fill=C_M)
    d.line([(x - 2, base - alt), (x + 2, base - alt)], fill=C_M)
    d.line([(x - 1, base - alt - 1), (x + 1, base - alt - 1)], fill=C_L)


def pinheiro(d, cx, topo_y, base, larg, seed=0):
    """Conífera: tronco fino e saias de agulhas em camadas, mais largas para baixo."""
    r = random.Random(seed)
    alt = base - topo_y
    d.rectangle([cx - 1, topo_y + alt * .55, cx + 1, base], fill=P_S)
    d.line([(cx - 1, topo_y + alt * .55), (cx - 1, base)], fill=P_M)
    d.line([(cx - 2, base), (cx + 2, base)], fill=P_D)
    n = max(3, int(alt / 9))
    copa = alt * .86
    for k in range(n):
        y0 = topo_y + copa * k / n * .92
        y1 = topo_y + copa * (k + 1.25) / n
        meia = 2 + (larg / 2 - 2) * (k + 1) / n
        for y in range(int(y0), int(min(y1, base - 3))):
            f = (y - y0) / (y1 - y0)
            m = 1 + meia * f
            for x in range(int(cx - m), int(cx + m) + 1):
                dx = (x - cx) / max(m, 1)
                borda = abs(x - cx) >= m - 1 or y >= int(min(y1, base - 3)) - 1
                c = A_L if dx < -.45 and f < .7 else (A_M if dx < .25 else A_S)
                if borda:
                    c = A_D if (x + y) % 3 else c
                if (x * 3 + y * 5 + seed) % 11 == 0:
                    c = A_D
                d.point((x, y), fill=c)
        for x in range(int(cx - meia), int(cx + meia) + 1, 3):          # pontas pendentes
            d.point((x + r.choice((0, 1)), int(min(y1, base - 3))), fill=A_S)
    d.point((cx, topo_y - 1), fill=A_M)


def tronco(d, cx, topo_y, base, larg, quebrado=True, seed=0):
    """Toco / tronco morto com casca, raízes abrindo na base e topo lascado."""
    r = random.Random(seed)
    for i in range(larg):
        x = cx - larg // 2 + i
        y0 = topo_y + (r.randrange(0, 5) if quebrado else 0) + abs(i - larg // 2) // 2
        c = P_L if i < larg * .25 else (P_M if i < larg * .6 else P_S)
        d.line([(x, y0), (x, base)], fill=c)
        d.point((x, y0), fill=P_L)
    d.line([(cx - larg // 2 - 1, topo_y + 4), (cx - larg // 2 - 1, base)], fill=K)
    d.line([(cx + larg - larg // 2, topo_y + 4), (cx + larg - larg // 2, base)], fill=K)
    for _ in range(max(2, (base - topo_y) // 7)):                       # sulcos da casca
        x = cx - larg // 2 + r.randrange(1, max(2, larg - 1))
        y = r.randrange(topo_y + 5, max(topo_y + 6, base - 4))
        d.line([(x, y), (x, y + r.randrange(2, 5))], fill=P_D)
    for s in (-1, 1):                                                   # raízes
        d.line([(cx + s * (larg // 2), base - 3), (cx + s * (larg // 2 + 4), base)], fill=K, width=3)
        d.line([(cx + s * (larg // 2), base - 3), (cx + s * (larg // 2 + 3), base)], fill=P_M if s < 0 else P_S)
    for x in range(cx - larg // 2, cx - larg // 2 + max(2, larg // 2)):  # musgo num lado
        d.point((x, base - 5 - (x % 2)), fill=G_M)
        d.point((x, base - 6 - (x % 2)), fill=G_L)


def marco(d, cx, base):
    """Marco de pedras empilhadas (cairn)."""
    y = base
    for k, (rx, ry) in enumerate(((9, 4), (7, 3.5), (5.5, 3), (4, 2.5), (2.5, 2))):
        pedra(d, cx + (1 if k % 2 else -1), y, rx, ry, musgo=k == 0, seed=40 + k)
        y -= int(2 * ry) - 1


def placa(d, x, y):
    """Poste torto de madeira com tabuleta apagada."""
    d.line([(x + 15, y + 31), (x + 17, y + 6)], fill=K, width=5)
    d.line([(x + 15, y + 31), (x + 17, y + 6)], fill=P_M, width=3)
    d.line([(x + 14, y + 30), (x + 16, y + 7)], fill=P_L)
    d.polygon([(x + 5, y + 9), (x + 27, y + 7), (x + 28, y + 15), (x + 6, y + 18)], fill=P_S, outline=K)
    d.line([(x + 7, y + 10), (x + 26, y + 8)], fill=P_L)
    d.line([(x + 9, y + 13), (x + 24, y + 11)], fill=P_D)
    d.line([(x + 9, y + 15), (x + 19, y + 14)], fill=P_D)
    capim(d, x + 8, y + 31, 16, 5, 3)


def arvore_grande(sheet):
    """83, 84, 100, 101: árvore velha de copa em tufos, verde apagado (64 x 64)."""
    d = ImageDraw.Draw(sheet)
    x, y = 15 * T, 4 * T
    d.polygon([(x + 27, y + 63), (x + 29, y + 34), (x + 36, y + 34), (x + 38, y + 63)], fill=P_M, outline=K)
    d.line([(x + 30, y + 36), (x + 29, y + 62)], fill=P_L)
    d.line([(x + 35, y + 36), (x + 36, y + 62)], fill=P_S); d.line([(x + 34, y + 36), (x + 35, y + 62)], fill=P_S)
    for s, c in ((-1, P_M), (1, P_S)):
        d.line([(x + 32 + s * 5, y + 59), (x + 32 + s * 12, y + 63)], fill=K, width=4)
        d.line([(x + 32 + s * 5, y + 59), (x + 32 + s * 11, y + 63)], fill=c, width=2)
        d.line([(x + 32 + s * 2, y + 40), (x + 32 + s * 14, y + 27)], fill=K, width=4)
        d.line([(x + 32 + s * 2, y + 40), (x + 32 + s * 14, y + 27)], fill=c, width=2)
    d.ellipse([x + 30, y + 46, x + 33, y + 51], fill=P_D)
    px = sheet.load()
    tufos = [(32, 16, 13), (17, 22, 11), (47, 21, 11), (25, 30, 9), (41, 31, 9), (10, 31, 7), (54, 30, 7), (32, 8, 8)]
    for cx, cy, r in sorted(tufos, key=lambda t_: -t_[2]):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                dd = math.hypot(xx + .5 - cx, yy + .5 - cy)
                if dd <= r and 0 <= xx < 64 and 0 <= yy < 64:
                    s = (-(xx - cx) * .5 - (yy - cy)) / r
                    c = G_L if s > .55 else (G_M if s > .05 else (G_S if s > -.55 else G_D))
                    if dd > r - 1.1:
                        c = K if s < .2 else G_D
                    elif (xx * 3 + yy * 7) % 13 == 0:
                        c = G_D if s < .4 else G_HI
                    px[x + xx, y + yy] = c


def arvore_torta(sheet):
    """115-116, 132-133, 149-150: árvore morta inclinada, com galhos secos, presa num monte de pedras (64 x 96)."""
    tmp = Image.new('RGBA', (60, 110), VAZIO)
    d = ImageDraw.Draw(tmp)
    tronco(d, 30, 14, 109, 12, seed=8)
    for (ax, ay), (bx, by) in (((34, 40), (52, 22)), ((26, 58), (8, 44)), ((34, 24), (46, 6)), ((27, 30), (14, 18))):
        d.line([(ax, ay), (bx, by)], fill=K, width=4)
        d.line([(ax, ay), (bx, by)], fill=P_M, width=2)
        d.line([(bx, by), (bx + (4 if bx > 30 else -4), by - 7)], fill=P_S)
    tmp = tmp.rotate(-13, resample=Image.NEAREST, expand=True)
    x, y = 13 * T, 6 * T
    sheet.alpha_composite(tmp.crop((6, 4, 70, 96)), (x, y))
    d = ImageDraw.Draw(sheet)
    monte(d, x + 2, y + 95, 60, 26, 21)
    capim(d, x + 2, y + 95, 60, 6, 5)


def enfeites(sheet):
    d = ImageDraw.Draw(sheet)
    # 13: pedra musgosa; 14: marco de pedras; 30: toco; 31: tabuleta
    pedra(d, 13 * T + 16, 31, 12, 10, seed=1)
    capim(d, 13 * T + 2, 31, 28, 4, 1)
    marco(d, 14 * T + 16, 31)
    tronco(d, 13 * T + 16, T + 17, T + 31, 14, seed=2)
    cogumelo(d, 13 * T + 25, T + 31, 5); cogumelo(d, 13 * T + 6, T + 31, 3)
    placa(d, 14 * T, T)
    # 15-16: topo de um rochedo coberto de musgo; 32-33: miolo por baixo
    for x in range(64):
        a = int(4 + 22 * abs((x - 31.5) / 32) ** 1.7 + (x * 5 % 3))
        for y in range(a, 64):
            dy = y - a
            if y >= 32:
                c = NUCLEO if dy > 12 or (dy > 9 and (x + y) % 2) else R_D
                if x < 2 or x > 61:
                    c = K if x in (0, 63) else R_S
            elif dy == 0:
                c = G_HI
            elif dy < 3:
                c = G_L if x < 34 else G_M
            elif dy < 5 + PINGO[x % 32]:
                c = G_M if x < 30 else G_S
            elif dy < 12 + PINGO[x % 32]:
                c = R_M if x < 26 else (R_S if x < 48 else R_D)
                if (x + 2 * y) % 13 == 0:
                    c = R_D
            else:
                c = R_D if dy < 15 + PINGO[x % 32] or (x + y) % 2 else NUCLEO
            sheet.putpixel((15 * T + x, y), c)
    d = ImageDraw.Draw(sheet)
    # 47/64: tronco morto alto; 65/82/99: pinheiro alto; 81/98: pinheiro novo; 48: miolo com pedra por baixo
    tronco(d, 13 * T + 16, 2 * T + 3, 4 * T - 1, 10, seed=3)
    d.line([(13 * T + 20, 2 * T + 22), (13 * T + 28, 2 * T + 12)], fill=K, width=3)
    d.line([(13 * T + 20, 2 * T + 22), (13 * T + 28, 2 * T + 12)], fill=P_M)
    pinheiro(d, 14 * T + 16, 3 * T + 2, 6 * T - 1, 28, seed=1)
    pinheiro(d, 13 * T + 16, 4 * T + 16, 6 * T - 1, 22, seed=2)
    sheet.paste(celula('B', v=0), (14 * T, 2 * T))
    d = ImageDraw.Draw(sheet)
    # 49-50: capim alto; 66-67: samambaias
    capim(d, 15 * T, 3 * T - 1, 32, 14, 6); capim(d, 16 * T, 3 * T - 1, 32, 20, 7)
    capim(d, 15 * T, 4 * T - 1, 32, 24, 8, samambaia=True); capim(d, 16 * T, 4 * T - 1, 32, 28, 9, samambaia=True)
    arvore_grande(sheet)
    # 114: miolo com pedra por baixo; 131 e 148: raízes e cipós pendurados
    sheet.paste(celula('B', v=1), (12 * T, 6 * T))
    d = ImageDraw.Draw(sheet)
    r = random.Random(12)
    for rx, comp, cor in ((5, 30, P_M), (10, 52, G_S), (15, 40, P_S), (19, 58, G_M), (24, 34, P_M), (28, 22, G_S)):
        x = 12 * T + rx
        for k in range(comp):
            y = 7 * T - 4 + k
            if k % 7 == 6:
                x += r.choice((-1, 1))
            x = max(12 * T + 1, min(13 * T - 2, x))
            d.point((x, y), fill=cor)
            if cor in (G_S, G_M) and k % 5 == 2:
                d.point((x + (1 if k % 2 else -1), y), fill=G_L)
        d.point((x, 7 * T - 4 + comp), fill=K)
    arvore_torta(sheet)
    d = ImageDraw.Draw(sheet)
    # 111-113: capim, cogumelos, pedrinhas; 128-130: pedras e moita; 145: pedra; 146-147: monte grande
    capim(d, 9 * T + 2, 7 * T - 1, 28, 6, 10)
    for cx_, a in ((6, 4), (13, 6), (21, 3), (26, 5)):
        cogumelo(d, 10 * T + cx_, 7 * T - 1, a)
    monte(d, 11 * T + 2, 7 * T - 1, 28, 12, 13)
    monte(d, 9 * T + 1, 8 * T - 1, 30, 22, 14)
    pedra(d, 10 * T + 16, 8 * T - 1, 13, 8, seed=15); capim(d, 10 * T + 1, 8 * T - 1, 30, 5, 11)
    monte(d, 11 * T + 1, 8 * T - 1, 30, 30, 16); capim(d, 11 * T + 1, 8 * T - 1, 30, 7, 12, samambaia=True)
    pedra(d, 9 * T + 16, 9 * T - 1, 11, 7, seed=17)
    monte(d, 10 * T + 2, 9 * T - 1, 60, 40, 18)
    capim(d, 10 * T + 2, 9 * T - 1, 60, 6, 13)


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
    s.save(os.path.join(PASTA, 'tiles_purgatorio.png'))
    s.resize((s.width * 2, s.height * 2), Image.NEAREST).save(os.path.join(PASTA, 'tiles_purgatorio_2x.png'))
    return s


if __name__ == '__main__':
    print(gera().size)
