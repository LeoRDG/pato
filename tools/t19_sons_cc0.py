"""Tarefa 19: sons da lança-granadas e da minigun a partir de gravações reais de domínio público (CC0), em vez de síntese pura.

Fontes em assets/fontes_cc0/ (lista com endereço e licença em FONTES.txt). As gravações são curtas, mono e sem grave; por cima
entram as camadas da receita de t17 (`camadas`): grave que cresce depois do estalo, ar e cauda em estéreo.
  - som_lanca.wav  : disparo com o "tunc" de tubo bem marcado (base) + um M203 real (corpo e médios);
  - som_minigun.wav: um tiro de fuzil limpo (Lee-Enfield .303) encurtado + soco e grave densos em camadas; curto e quase mono,
                     para a rajada do jogo não embolar.
  - som_minigun_giro.wav: laço do giro dos canos, a partir de um motor elétrico real.
Volume no mesmo nível das outras armas.   Rodar:  python3 tools/t19_sons_cc0.py   (pode rodar de novo; não mexe no jogo.json)
t17_sons_armas.py não grava mais estes dois arquivos.
"""
import os, wave
import numpy as np
from t17_sons_armas import SR, ROOT, camadas, grava, passa


def le(nome):
    w = wave.open(os.path.join(ROOT, 'assets', 'fontes_cc0', nome))
    assert w.getframerate() == SR and w.getnchannels() == 1
    x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768
    ini = np.argmax(np.abs(x) > 0.1 * np.abs(x).max())      # começa no disparo
    x = x[max(ini - 30, 0):]
    return x / np.abs(x).max()


def lanca():
    dur = 0.9
    n = int(SR * dur)
    t = np.arange(n) / SR
    encaixa = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    tubo = encaixa(le('lanca_163458.wav'))                   # o "tunc"
    m203 = encaixa(le('lanca_162401.wav'))                   # corpo real
    real = tubo + 0.45 * passa(m203, 150, 9000, 2)
    real = real / np.abs(real).max()

    rng = np.random.default_rng(7019)
    L, R = camadas(dur, rng, [
        # lo, hi,   t0,    ataque, segura, queda, dB, largura
        (40, 120, 0.010, 0.020, 0.040, 0.060, 0, 0.0),        # grave que cresce depois (as gravações não têm)
        (1500, 8000, 0.004, 0.006, 0.020, 0.060, -14, 0.9),   # ar em estéreo
        (150, 1500, 0.050, 0.050, 0.000, 0.160, -16, 1.0),    # cauda em estéreo
    ], drive=1.4)
    k = 0.55 / max(np.abs(L).max(), np.abs(R).max())         # as camadas ficam abaixo da gravação
    grava(real + k * L, real + k * R, 'som_lanca.wav', fade=0.3, pico=0.55)


def minigun():
    """Base: um tiro de fuzil limpo (silêncio antes, queda lisa depois), encurtado para ~120 ms. Como a gravação é "magra"
    (cai 10 dB em 20 ms), o impacto vem das camadas densas por baixo (soco + grave perto do pico por ~50 ms) e de um limitador no fim."""
    dur = 0.35
    n = int(SR * dur)
    t = np.arange(n) / SR
    encaixa = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    tiro = encaixa(le('minigun_450853.wav')) * np.where(t < 0.015, 1, np.exp(-(t - 0.015) / 0.035))
    tiro = tiro / np.abs(tiro).max()

    rng = np.random.default_rng(7020)
    L, R = camadas(dur, rng, [
        (120, 450, 0.001, 0.002, 0.010, 0.016, 0, 0.0),       # soco
        (40, 115, 0.004, 0.008, 0.022, 0.030, 5, 0.0),        # grave que cresce depois
        (2500, 12000, 0.002, 0.003, 0.010, 0.022, -10, 0.3),  # ar
        (200, 2500, 0.025, 0.020, 0.000, 0.045, -24, 0.8),    # cauda mínima
    ], drive=2.4)
    k = 0.8 / max(np.abs(L).max(), np.abs(R).max())
    L, R = (np.tanh(1.5 * (tiro + k * v)) for v in (L, R))
    grava(L, R, 'som_minigun.wav', fade=0.1, pico=0.5)


def giro():
    """Giro dos canos da minigun, em laço: motor elétrico real (uma Dremel) tocado 3x mais devagar e com os agudos cortados em 1,3 kHz
    (sem isso o motor "mia": apito médio-agudo que sobe e desce de tom), mais um ronco grave de ruído pulsando a ~38 Hz
    (os canos passando), que é o que dá o som de tambor girando. As pontas são fundidas para o laço não estalar.
    O jogo sobe/desce o volume e o tom deste laço conforme a minigun gira (tools/t20_minigun_giro.py)."""
    w = wave.open(os.path.join(ROOT, 'assets', 'fontes_cc0', 'giro_125401.wav'))
    x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768
    lento = np.interp(np.arange(0, len(x) - 1, 1 / 3), np.arange(len(x)), x)     # um terço da velocidade
    dur, f = 2.0, int(0.25 * SR)
    n = int(SR * dur)
    trecho = passa(lento[:n + f], 70, 1300, 3)
    rampa = np.linspace(0, 1, f)
    motor = trecho[:n].copy()
    motor[:f] = trecho[:f] * rampa + trecho[n:n + f] * (1 - rampa)               # o começo continua o fim
    t = np.arange(n) / SR
    rng = np.random.default_rng(7021)
    ruido = passa(np.tile(rng.standard_normal(n // 4), 4), 60, 420, 3)           # período de 0,5 s: fecha no laço
    pulso = (0.5 + 0.5 * np.sin(2 * np.pi * 38 * t)) ** 3                        # 38 Hz x 2 s = 76 ciclos inteiros
    ronco = ruido * pulso
    laco = 0.55 * motor / np.abs(motor).max() + 1.0 * ronco / np.abs(ronco).max()
    pcm = np.repeat((laco / np.abs(laco).max() * 0.5 * 32767).astype('<i2')[:, None], 2, axis=1)
    with wave.open(os.path.join(ROOT, 'assets', 'som_minigun_giro.wav'), 'wb') as o:
        o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(pcm.tobytes())


if __name__ == '__main__':
    lanca()
    minigun()
    giro()
