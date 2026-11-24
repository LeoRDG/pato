"""Texturas suaves para as partículas (degradê liso, brancas para a cor do emissor tingir):
- particula_luz.png: um brilho redondo (gaussiana), para fogo e luz (com mistura aditiva);
- particula_fumaca.png: um tufo de fumaça de borda macia e um pouco irregular.
Com o renderizador "Point" as partículas eram discos de borda dura e a explosão parecia um monte de bolhas.
Gerador de arte (roda uma vez; não mexe no jogo.json):  python3 tools/arte_particulas.py
"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(RAIZ, 'assets/particulas')
T = 128


def _grade():
    yy, xx = np.mgrid[0:T, 0:T].astype(float)
    c = (T - 1) / 2
    return (xx - c) / c, (yy - c) / c


def _salva(a, nome):
    rgb = np.full((T, T, 3), 255, np.uint8)
    Image.fromarray(np.dstack([rgb, (np.clip(a, 0, 1) * 255).astype(np.uint8)]), 'RGBA').save(os.path.join(P, nome))


def brilho():
    x, y = _grade()
    d = np.hypot(x, y)
    a = np.exp(-(d / 0.38) ** 2 / 2)
    a[d >= 1] = 0
    return a


def fumaca(semente=5):
    x, y = _grade()
    rng = np.random.default_rng(semente)
    ang = np.arctan2(y, x)
    borda = 0.78 + sum(rng.uniform(0.02, 0.06) * np.sin(k * ang + rng.uniform(0, 6.3)) for k in (3, 5, 7))
    d = np.hypot(x, y) / borda
    a = np.clip((1 - d) / 0.55, 0, 1) ** 1.4 * 0.9
    a[np.hypot(x, y) >= 1] = 0
    return a


if __name__ == '__main__':
    os.makedirs(P, exist_ok=True)
    _salva(brilho(), 'particula_luz.png')
    _salva(fumaca(), 'particula_fumaca.png')
    print('ok')
