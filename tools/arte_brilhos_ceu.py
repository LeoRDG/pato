"""Troca os brilhos em cruz (+) soltos no céu do Paraíso (assets/paraiso/bg_nuvens.png) por brilhos redondos e
suaves (degradê liso). As nuvens e os pontinhos de um bloco ficam como estão. Rodar de novo não muda nada (não sobra
cruz para trocar).
Gerador de arte (não mexe no jogo.json):  python3 tools/arte_brilhos_ceu.py
"""
import os
from collections import deque
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, 'assets/paraiso/bg_nuvens.png')
RAIO = 7          # alcance do brilho em pixels da imagem
PICO = 225        # opacidade no centro
COR = (255, 253, 242)


def pecas_soltas(al, maximo=120):
    """componentes opacos pequenos (a imagem emenda nas bordas)."""
    h, w = al.shape
    vis = np.zeros_like(al)
    for y in range(h):
        for x in range(w):
            if al[y, x] and not vis[y, x]:
                q, pts = deque([(y, x)]), []
                vis[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = (cy + dy) % h, (cx + dx) % w
                        if al[ny, nx] and not vis[ny, nx]:
                            vis[ny, nx] = True
                            q.append((ny, nx))
                if len(pts) <= maximo:
                    yield pts


def e_cruz(a, pts):
    ys, xs = zip(*pts)
    if max(ys) - min(ys) != max(xs) - min(xs) or len(pts) * 9 != 5 * (max(ys) - min(ys) + 1) ** 2:
        return False
    return a[min(ys), min(xs), 3] == 0  # canto vazio: é cruz, não quadrado


def main():
    a = np.array(Image.open(ARQ).convert('RGBA')).astype(float)
    h, w = a.shape[:2]
    trocas = 0
    for pts in list(pecas_soltas(a[..., 3] > 0)):
        if not e_cruz(a, pts):
            continue
        for y, x in pts:
            a[y, x, 3] = 0
        cy, cx = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
        for y in range(int(cy) - RAIO - 1, int(cy) + RAIO + 2):
            for x in range(int(cx) - RAIO - 1, int(cx) + RAIO + 2):
                d = np.hypot(y - cy, x - cx)
                al = PICO * np.exp(-(d / (RAIO * 0.42)) ** 2 / 2) if d < RAIO else 0
                yy, xx = y % h, x % w
                if al > a[yy, xx, 3]:
                    a[yy, xx, :3], a[yy, xx, 3] = COR, al
        trocas += 1
    Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA').save(ARQ)
    print('cruzes trocadas:', trocas)


if __name__ == '__main__':
    main()
