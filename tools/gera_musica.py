"""Gera as músicas do jogo (assets/musica/*.ogg) por síntese, sem nenhuma amostra de fora.
Diferente dos tNN_*.py, este é um gerador: só escreve arquivos de áudio, nunca mexe no jogo.json. Rodar de novo gera
exatamente os mesmos arquivos (sementes fixas); para mudar uma música, mude a composição aqui e rode só ela:
    python3 tools/gera_musica.py                 # todas
    python3 tools/gera_musica.py inferno inferno_chefe --wav /tmp/x   # algumas, guardando também o .wav
Cada faixa é um loop de um número exato de compassos: o que passa do fim (notas, reverb, delay) volta para o começo,
então o loop emenda sem clique. A versão de chefe de cada fase tem o mesmo andamento, tom e tamanho da faixa normal,
com as mesmas partes e mais camadas, para o jogo trocar de uma para a outra no mesmo ponto da música.
Precisa só de numpy e do ffmpeg (libvorbis).
"""
import os, subprocess, sys, tempfile, wave
import numpy as np

SR = 44100
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, 'assets', 'musica')
QUALIDADE_OGG = '2'   # libvorbis -q:a (2 ~ 96 kbps)
rng = np.random.default_rng(0)


# ---------------------------------------------------------------- notas e acordes
PC = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
QUAL = {'': [0, 4, 7], 'm': [0, 3, 7], '5': [0, 7, 12], '7': [0, 4, 7, 10], 'm7': [0, 3, 7, 10],
        'maj7': [0, 4, 7, 11], 'm9': [0, 3, 7, 10, 14], 'maj9': [0, 4, 7, 11, 14], 'sus4': [0, 5, 7],
        'sus2': [0, 2, 7], '7sus4': [0, 5, 7, 10], 'm6': [0, 3, 7, 9], 'add9': [0, 4, 7, 14], 'madd9': [0, 3, 7, 14],
        '7b9': [0, 4, 7, 10, 13], 'maj7#11': [0, 4, 7, 11, 18], '6': [0, 4, 7, 9], 'dim': [0, 3, 6, 9],
        'm7b5': [0, 3, 6, 10], 'b9': [0, 4, 7, 13]}


def nota(s):
    """'c#4' -> midi"""
    s = s.lower()
    pc = PC[s[0]]
    i = 1
    while i < len(s) and s[i] in '#b':
        pc += 1 if s[i] == '#' else -1
        i += 1
    return pc + 12 * (int(s[i:]) + 1)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def acorde(sym):
    i = 1
    while i < len(sym) and sym[i] in '#b' and not sym[i:].startswith('b9'):
        i += 1
    raiz = nota(sym[:i] + '0') % 12
    return raiz, QUAL[sym[i:]]


def voz(sym, lo=55):
    """voicing fechado a partir de lo"""
    r, ivs = acorde(sym)
    return sorted({lo + ((r + iv - lo) % 12) for iv in ivs})


def baixo(sym, lo=36):
    r, _ = acorde(sym)
    return lo + ((r - lo) % 12)


def melodia(txt):
    """'d5/1.5 e5/.5 r f5' -> [(beat, dur, midi|None)] (dur em tempos; sem /x = 1 tempo)"""
    out, b = [], 0.0
    for tok in txt.split():
        if tok == '|':
            continue
        n, _, d = tok.partition('/')
        d = float(d) if d else 1.0
        out.append((b, d, None if n == 'r' else nota(n)))
        b += d
    return out


# ---------------------------------------------------------------- dsp básico (só numpy: filtros no domínio da frequência)
def _pot2(n):
    return 1 << int(np.ceil(np.log2(max(n, 2))))


def filtra(x, resp, circular=False):
    """aplica a resposta de módulo resp(f) (fase zero). circular=True trata x como um loop."""
    n = x.shape[0]
    N = n if circular else _pot2(n + min(n, 8192))
    X = np.fft.rfft(x, N, axis=0)
    H = resp(np.fft.rfftfreq(N, 1 / SR))
    return np.fft.irfft(X * (H[:, None] if x.ndim == 2 else H), N, axis=0)[:n]


def _lp(f, fc, o):
    return 1 / np.sqrt(1 + (f / fc) ** (2 * o))


def _hp(f, fc, o):
    return 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * o))


def lp(x, f, ordem=2):
    return filtra(x, lambda fr: _lp(fr, f, ordem))


def hp(x, f, ordem=2):
    return filtra(x, lambda fr: _hp(fr, f, ordem))


def bp(x, f1, f2, ordem=2):
    return filtra(x, lambda fr: _hp(fr, max(f1, 20), ordem) * _lp(fr, f2, ordem))


def convolve(a, b):
    N = _pot2(len(a) + len(b))
    return np.fft.irfft(np.fft.rfft(a, N) * np.fft.rfft(b, N), N)[:len(a) + len(b) - 1]


def media_movel(x, janela):
    """média móvel (janela em amostras), mesma duração"""
    c = np.cumsum(np.concatenate([np.full(janela, x[0]), x]))
    return (c[janela:] - c[:-janela]) / janela


def tv(n):
    return np.arange(n) / SR


def ruido(n):
    return rng.standard_normal(n)


def saw(ph, dt):
    """dente de serra com polyBLEP (ph em ciclos)"""
    t = ph % 1.0
    y = 2 * t - 1
    dt = np.broadcast_to(np.asarray(dt, float), t.shape)
    m = t < dt
    x = t[m] / dt[m]
    y[m] -= x + x - x * x - 1
    m = t > 1 - dt
    x = (t[m] - 1) / dt[m]
    y[m] -= x * x + x + x + 1
    return y


def env(dur, a, d, s, r):
    n_on = max(1, int(dur * SR))
    n_r = int(r * 4 * SR) + 1
    t = tv(n_on + n_r)
    on = t[:n_on]
    e = np.empty(n_on + n_r)
    e[:n_on] = np.where(on < a, on / max(a, 1e-5), s + (1 - s) * np.exp(-np.maximum(on - a, 0) / max(d, 1e-5)))
    e[n_on:] = e[n_on - 1] * np.exp(-(t[n_on:] - dur) / max(r, 1e-5))
    return e


def estereo(m, pan=0.0):
    if m.ndim == 2:
        return m
    a = (pan + 1) * np.pi / 4
    return np.stack([m * np.cos(a), m * np.sin(a)], 1) * np.sqrt(2)


def vibrato(n, taxa=5.0, prof=0.005, atraso=0.25):
    t = tv(n)
    return 1 + prof * np.sin(2 * np.pi * taxa * t + rng.random() * 6) * np.clip((t - atraso) / 0.3, 0, 1)


# ---------------------------------------------------------------- instrumentos (uma nota -> sinal)
def i_pad(f, dur, vel, corte=1800, vozes=5, det=0.12, a=0.5, r=1.0, s=0.85):
    e = env(dur, a, 0.8, s, r)
    n = len(e)
    t = tv(n)
    out = np.zeros((n, 2))
    for ch in range(2):
        acc = np.zeros(n)
        for v in range(vozes):
            c = det * 100 * ((v / (vozes - 1)) * 2 - 1 if vozes > 1 else 0) + rng.uniform(-5, 5)
            ff = f * 2 ** (c / 1200)
            acc += saw(ff * t + rng.random(), ff / SR)
        out[:, ch] = lp(acc / vozes, corte, 2)
    return out * (e * vel)[:, None]


def i_pluck(f, dur, vel, brilho=0.6, decai=0.6, rel=0.08, K=30):
    n = int((min(dur, decai * 4) + rel * 4) * SR)
    t = tv(n)
    y = np.zeros(n)
    for k in range(1, K + 1):
        fk = f * k * (1 + 0.0003 * k * k)
        if fk > 16000:
            break
        tau = decai / (1 + (k - 1) * (1.2 - brilho) * 0.9)
        y += np.sin(2 * np.pi * fk * t + rng.random() * 6) * np.exp(-t / tau) / k ** 1.1
    off = int(dur * SR)
    if off < n:
        y[off:] *= np.exp(-tv(n - off) / rel)
    y *= np.clip(t / 0.002, 0, 1)
    return y * vel


def i_epiano(f, dur, vel, rel=0.3):
    n = int((dur + rel * 4) * SR)
    t = tv(n)
    ind = (0.8 + 1.8 * vel) * np.exp(-t / 0.45)
    y = np.sin(2 * np.pi * f * t + ind * np.sin(2 * np.pi * f * t))
    y += 0.12 * vel * np.sin(2 * np.pi * f * 14 * t) * np.exp(-t / 0.015)
    amp = np.exp(-t / (3.0 if f < 300 else 1.8)) * np.clip(t / 0.003, 0, 1)
    off = int(dur * SR)
    amp[off:] *= np.exp(-tv(n - off) / rel)
    y *= amp * vel
    trem = 0.5 + 0.5 * np.sin(2 * np.pi * 4.5 * t + rng.random() * 6) * 0.35
    return np.stack([y * (1 - trem * 0.5), y * (0.5 + trem * 0.5)], 1)


def i_sino(f, dur, vel, tipo='sino', escala=1.0):
    if tipo == 'caixinha':     # caixinha de música
        parc = [(1, 1, 1.6), (3.0, .25, .35), (5.2, .12, .15), (2.0, .2, .6)]
    elif tipo == 'celesta':
        parc = [(1, 1, 1.2), (2, .35, .5), (3, .12, .25), (4.02, .05, .12)]
    else:
        parc = [(1, 1, 2.6), (2.0, .55, 1.5), (2.76, .4, 1.0), (4.07, .22, .6), (5.4, .14, .4), (0.5, .25, 3.0)]
    n = int(max(p[2] for p in parc) * escala * 4 * SR)
    t = tv(n)
    y = np.zeros(n)
    for r, a, d in parc:
        if f * r < 16000:
            y += a * np.sin(2 * np.pi * f * r * t + rng.random() * 6) * np.exp(-t / (d * escala))
    y *= np.clip(t / 0.001, 0, 1)
    return y * vel


def i_flauta(f, dur, vel, a=0.06, r=0.18):
    e = env(dur, a, 0.3, 0.85, r)
    n = len(e)
    ph = np.cumsum(f * vibrato(n, 5.2, 0.006, 0.2) / SR) + rng.random()
    y = np.sin(2 * np.pi * ph) + 0.22 * np.sin(4 * np.pi * ph) + 0.07 * np.sin(6 * np.pi * ph)
    y += 0.12 * bp(ruido(n), f * 1.5, min(f * 4, 15000)) * (0.4 + np.exp(-tv(n) / 0.08))
    return y * e * vel


def i_lead(f, dur, vel, corte=3200, mix_q=0.6, a=0.01, r=0.12, vib=0.006):
    e = env(dur, a, 0.25, 0.75, r)
    n = len(e)
    ff = f * vibrato(n, 5.5, vib, 0.18)
    ph = np.cumsum(ff / SR) + rng.random()
    dt = ff / SR
    sq = saw(ph, dt) - saw(ph + 0.5, dt)
    y = mix_q * sq + (1 - mix_q) * saw(ph * 1.003, dt)
    return lp(y, corte, 2) * e * vel


def i_coro(f, dur, vel, vogal='a', a=0.3, r=0.7):
    form = {'a': [(800, 1, 80), (1150, .5, 90), (2900, .25, 120)],
            'o': [(450, 1, 70), (800, .45, 80), (2830, .15, 100)],
            'u': [(325, 1, 50), (700, .3, 60), (2530, .08, 100)]}[vogal]
    e = env(dur, a, 0.6, 0.9, r)
    n = len(e)
    out = np.zeros((n, 2))
    for ch in range(2):
        src = np.zeros(n)
        for _ in range(3):
            ff = f * 2 ** (rng.uniform(-12, 12) / 1200) * vibrato(n, rng.uniform(4.5, 5.5), 0.004, 0.1)
            src += saw(np.cumsum(ff / SR) + rng.random(), ff / SR)
        y = sum(g * bp(src, F - bw, F + bw) for F, g, bw in form)
        out[:, ch] = y
    return out * (e * vel * 3)[:, None]


def i_guitarra(f, dur, vel, abafada=False):
    """power chord distorcido (raiz, quinta, oitava), dobrado em estéreo"""
    rel = 0.04 if abafada else 0.15
    e = env(dur, 0.002, 0.07 if abafada else 0.5, 0.15 if abafada else 0.7, rel)
    n = len(e)
    t = tv(n)
    out = np.zeros((n, 2))
    for ch in range(2):
        src = np.zeros(n)
        for r in (1, 1.4983, 2):
            for c in (-7, 7):
                ff = f * r * 2 ** ((c + rng.uniform(-3, 3)) / 1200)
                src += saw(ff * t + rng.random(), ff / SR)
        src = hp(src, 90) * e
        y = np.tanh(src * 5)
        y = lp(y, 1400 if abafada else 3600, 4)
        out[:, ch] = hp(y, 70)
    return out * vel


def i_metal(f, dur, vel, corte_max=4200):
    """naipe de metais"""
    e = env(dur, 0.025, 0.25, 0.8, 0.15)
    n = len(e)
    t = tv(n)
    ff = f * (1 - 0.025 * np.exp(-t / 0.04))
    src = sum(saw(np.cumsum(ff * 2 ** (c / 1200) / SR) + rng.random(), ff / SR) for c in (-8, 0, 8)) / 3
    b = np.clip(0.2 + 0.8 * vel * np.exp(-t / 0.18), 0, 1)
    y = lp(src, 700) * (1 - b) + lp(src, corte_max) * b
    return y * e * vel


def i_cordas(f, dur, vel, trem=0.0, beat=0.5, corte=2600, a=0.15, r=0.4):
    e = env(dur, a, 0.5, 0.9, r)
    n = len(e)
    out = np.zeros((n, 2))
    for ch in range(2):
        acc = np.zeros(n)
        for c in (-9, -2, 6):
            ff = f * 2 ** ((c + rng.uniform(-3, 3)) / 1200) * vibrato(n, 5.0, 0.003, 0.2)
            acc += saw(np.cumsum(ff / SR) + rng.random(), ff / SR)
        out[:, ch] = lp(acc / 3, corte, 2)
    if trem:
        ph = tv(n) / (beat / 4)
        am = 1 - trem * (0.5 - 0.5 * np.cos(2 * np.pi * ph)) ** 2
        out *= am[:, None]
    return out * (e * vel)[:, None]


def i_baixo(f, dur, vel, corte=700, sub=0.6, dist=0.0, a=0.004, s=0.6, r=0.05):
    e = env(dur, a, 0.18, s, r)
    n = len(e)
    t = tv(n)
    y = lp(saw(f * t + rng.random(), f / SR), corte, 2)
    y += sub * np.sin(2 * np.pi * f * t)
    if dist:
        y = np.tanh(y * (1 + dist * 4)) / np.tanh(1 + dist * 4)
        y = lp(y, corte * 2.5, 2)
    return y * e * vel


def i_sub(f, dur, vel, a=0.02, r=0.2):
    e = env(dur, a, 0.3, 0.9, r)
    t = tv(len(e))
    return (np.sin(2 * np.pi * f * t) + 0.15 * np.sin(4 * np.pi * f * t)) * e * vel


def i_harpa(f, dur, vel):
    return i_pluck(f, dur, vel, brilho=0.85, decai=1.2, rel=0.5)


# ---------------------------------------------------------------- bateria (amostras sintetizadas)
def d_bumbo(tom=1.0, decai=0.32):
    n = int(0.7 * SR)
    t = tv(n)
    f = 46 * tom + 120 * tom * np.exp(-t / 0.035)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decai)
    y += 0.35 * hp(ruido(n), 1800) * np.exp(-t / 0.004)
    return np.tanh(1.6 * y)


def d_caixa(tom=1.0, decai=0.14):
    n = int(0.5 * SR)
    t = tv(n)
    y = 0.55 * np.sin(2 * np.pi * 185 * tom * t) * np.exp(-t / 0.06) + 0.3 * np.sin(2 * np.pi * 330 * tom * t) * np.exp(-t / 0.035)
    y += bp(ruido(n), 1200, 9000) * np.exp(-t / decai)
    return y


def d_palma():
    n = int(0.4 * SR)
    t = tv(n)
    e = np.exp(-t / 0.12)
    for k in (0.0, 0.011, 0.022):
        e += 1.2 * np.exp(-np.maximum(t - k, 0) / 0.006) * (t >= k)
    return bp(ruido(n), 900, 4000) * e * 0.6


def d_chimbal(aberto=False):
    n = int((0.5 if aberto else 0.12) * SR)
    t = tv(n)
    met = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0))
    y = hp(0.6 * ruido(n) + 0.15 * met, 7000, 4)
    return y * np.exp(-t / (0.22 if aberto else 0.03))


def d_chocalho():
    n = int(0.15 * SR)
    t = tv(n)
    return bp(ruido(n), 4000, 11000) * np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.05)


def d_aro():
    n = int(0.12 * SR)
    t = tv(n)
    return (bp(ruido(n), 1500, 4000) * 0.7 + np.sin(2 * np.pi * 820 * t)) * np.exp(-t / 0.018)


def d_prato():
    n = int(3.5 * SR)
    t = tv(n)
    out = np.zeros((n, 2))
    for ch in range(2):
        met = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) for f in rng.uniform(3000, 9000, 12))
        out[:, ch] = hp(ruido(n) + 0.2 * met, 3500, 2) * np.exp(-t / 1.3) * np.clip(t / 0.002, 0, 1)
    return out


def d_tom(f=110):
    n = int(0.8 * SR)
    t = tv(n)
    ff = f * (1 + 0.6 * np.exp(-t / 0.05))
    return (np.sin(2 * np.pi * np.cumsum(ff) / SR) + 0.2 * lp(ruido(n), 2000) * np.exp(-t / 0.03)) * np.exp(-t / 0.28)


def d_taiko():
    n = int(1.4 * SR)
    t = tv(n)
    ff = 62 * (1 + 0.5 * np.exp(-t / 0.06))
    y = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t / 0.5)
    y += 0.5 * lp(ruido(n), 600) * np.exp(-t / 0.08)
    y += 0.25 * bp(ruido(n), 1500, 5000) * np.exp(-t / 0.01)
    return np.tanh(1.4 * y)


def d_timpano(f):
    n = int(2.5 * SR)
    t = tv(n)
    ff = f * (1 + 0.02 * np.exp(-t / 0.1))
    ph = np.cumsum(ff) / SR
    y = np.sin(2 * np.pi * ph) + 0.5 * np.sin(2 * np.pi * 1.5 * ph) * np.exp(-t / 0.5) + 0.3 * np.sin(2 * np.pi * 1.98 * ph) * np.exp(-t / 0.4)
    y += 0.3 * lp(ruido(n), 1500) * np.exp(-t / 0.02)
    return y * np.exp(-t / 0.9)


# ---------------------------------------------------------------- faixa (mixagem, efeitos, loop)
class Faixa:
    def __init__(self, nome, bpm, compassos, seed, swing=0.0):
        global rng
        rng = np.random.default_rng(seed)
        self.nome, self.bpm, self.compassos, self.swing = nome, bpm, compassos, swing
        self.b = 60.0 / bpm
        self.L = int(round(compassos * 4 * self.b * SR))
        self.N = self.L + 14 * SR
        self.bus = {}          # nome -> [sinal, nivel_db, rev, delay]
        self.amostras = {}

    def t(self, compasso, tempo=0.0):
        return (compasso * 4 + tempo) * self.b

    def canal(self, nome, nivel_db, rev=0.15, delay=0.0):
        if nome not in self.bus:
            self.bus[nome] = [np.zeros((self.N, 2)), nivel_db, rev, delay]

    def poe(self, bus, sinal, t, pan=0.0, ganho=1.0, humano=0.004):
        s = estereo(sinal, pan) * ganho
        i = int(round((t + (rng.uniform(-humano, humano) if humano else 0)) * SR))
        i = max(i, 0)
        n = min(len(s), self.N - i)
        if n > 0:
            self.bus[bus][0][i:i + n] += s[:n]

    def nota(self, bus, inst, midi, t, dur_tempos, vel=0.8, pan=0.0, **kw):
        self.poe(bus, inst(hz(midi), dur_tempos * self.b, vel, **kw), t, pan)

    def amostra(self, chave, fn, variantes=3):
        if chave not in self.amostras:
            self.amostras[chave] = [fn() for _ in range(variantes)]
        v = self.amostras[chave]
        return v[rng.integers(len(v))]

    def ritmo(self, bus, compasso, padrao, chave, fn, vel=0.8, pan=0.0, passos=16):
        """padrao de 16 passos: X forte, x normal, o fraco, . nada"""
        passo = 4.0 / passos
        for i, c in enumerate(padrao.replace(' ', '')):
            if c == '.':
                continue
            v = vel * {'X': 1.0, 'x': 0.75, 'o': 0.4}[c]
            tempo = i * passo + (self.swing * passo if i % 2 == 1 and passos == 16 else 0)
            self.poe(bus, self.amostra(chave, fn), self.t(compasso, tempo), pan, v * rng.uniform(0.92, 1.0))

    def continuo(self, bus, sinal_fn, pan=0.0):
        """camada contínua (vento, chiado): gera L + X e emenda o fim no começo com crossfade de potência igual"""
        X = 2 * SR
        s = estereo(sinal_fn(self.L + X), pan)
        out = s[:self.L].copy()
        f = np.linspace(0, 1, X)[:, None]
        out[:X] = s[:X] * np.sqrt(f) + s[self.L:self.L + X] * np.sqrt(1 - f)
        self.bus[bus][0][:self.L] += out

    # ---- render
    def _reverb(self, x, segundos=2.6, escuro=3500):
        n = int(segundos * SR)
        t = tv(n)
        ir = np.zeros((n, 2))
        for ch in range(2):
            r = ruido(n)
            r = lp(r, escuro, 1) * 0.6 + r * 0.4 * np.exp(-t / 0.25)
            ir[:, ch] = r * np.exp(-t / (segundos / 6.9)) * np.clip((t - 0.012) / 0.01, 0, 1)
        ir /= np.sqrt(np.sum(ir ** 2, 0))
        return np.stack([convolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)

    def _delay(self, x, tempos=0.75, fb=0.38, n=6):
        d = int(tempos * self.b * SR)
        out = np.zeros_like(x)
        y = lp(x, 3500)
        for k in range(1, n + 1):
            if k * d >= len(x):
                break
            ch = (k + 1) % 2
            out[k * d:, ch] += y[:len(x) - k * d, 0 if ch == 0 else 1] * fb ** (k - 1) * 0.7 + \
                               y[:len(x) - k * d, 1 - ch] * fb ** (k - 1) * 0.3
            y = lp(y, 5000, 1)
        return out

    def render(self, rms_alvo_db=-16.0, reverb_s=2.6, pico_db=-2.0):
        mix = np.zeros((self.N, 2))
        envio_rev = np.zeros((self.N, 2))
        envio_del = np.zeros((self.N, 2))
        for nome, (s, nivel, rev, dl) in self.bus.items():
            a = ativo_rms(s)
            if a <= 0:
                continue
            s = s * (10 ** (nivel / 20) / a)
            mix += s
            envio_rev += s * rev
            envio_del += s * dl
        mix += self._reverb(envio_rev + 0.5 * self._delay(envio_del), reverb_s) + self._delay(envio_del)
        # dobra a cauda para o começo: o loop emenda certinho
        out = np.zeros((self.L, 2))
        for i in range(0, self.N, self.L):
            p = mix[i:i + self.L]
            out[:len(p)] += p
        return master(out, rms_alvo_db, pico_db)


def ativo_rms(s, bloco=2205):
    m = s[:len(s) // bloco * bloco].reshape(-1, bloco, 2)
    r = np.sqrt(np.mean(m ** 2, axis=(1, 2)))
    if r.max() <= 0:
        return 0.0
    ativos = r[r > r.max() * 0.03]
    return float(np.sqrt(np.mean(ativos ** 2)))


def master(x, rms_alvo_db, pico_db=-2.0):
    """passa-altas, compressão suave e limitador; tudo em volta circular (o loop continua contínuo)"""
    y = filtra(x, lambda fr: _hp(fr, 28, 2), circular=True)
    # compressor de rms (janela de 50 ms, em volta circular)
    P = SR
    p = np.mean(y ** 2, 1)
    e = np.sqrt(media_movel(np.concatenate([p[-P:], p, p[:P]]), int(0.05 * SR))[P:-P].clip(1e-12))
    e = np.sqrt(np.concatenate([e[-P:] ** 2, e ** 2, e[:P] ** 2]))
    e = media_movel(media_movel(e, int(0.02 * SR)), int(0.02 * SR))[P:-P]
    g = np.minimum(1, (e / (e.mean() * 1.6)) ** -0.35)
    y = y * g[:, None]
    y *= 10 ** (rms_alvo_db / 20) / np.sqrt(np.mean(y ** 2))
    teto = 10 ** (pico_db / 20)
    lim = 0.75 * teto
    a = np.abs(y)
    acima = a > lim
    y[acima] = np.sign(y[acima]) * (lim + (teto - lim) * np.tanh((a[acima] - lim) / (teto - lim)))
    return y


# ---------------------------------------------------------------- helpers de composição
def toca_melodia(f, bus, inst, txt, compasso, vel=0.8, transp=0, pan=0.0, legato=0.95, **kw):
    for b, d, m in melodia(txt):
        if m is not None:
            f.nota(bus, inst, m + transp, f.t(compasso, b), d * legato, vel * rng.uniform(0.9, 1.0), pan, **kw)


def arpejo(f, bus, inst, sym, compasso, padrao, lo=60, passo=0.5, vel=0.6, tempos=4.0, **kw):
    notas = voz(sym, lo)
    notas = notas + [n + 12 for n in notas]
    b = 0.0
    i = 0
    while b < tempos - 1e-6:
        idx = padrao[i % len(padrao)]
        if idx is not None:
            f.nota(bus, inst, notas[idx % len(notas)], f.t(compasso, b), passo * 0.9,
                   vel * (1.0 if i % 4 == 0 else 0.8) * rng.uniform(0.9, 1.0), pan=rng.uniform(-0.3, 0.3), **kw)
        b += passo
        i += 1


def bloco(f, bus, inst, sym, compasso, tempos=4.0, lo=55, vel=0.5, inicio=0.0, **kw):
    for k, m in enumerate(voz(sym, lo)):
        f.nota(bus, inst, m, f.t(compasso, inicio), tempos, vel, pan=(k / 3 - 0.5) * 0.6, **kw)


# ================================================================ as músicas
def resultado():
    """Tela de resultado: fá maior, 84 bpm, 16 compassos. Piano elétrico, baixo macio, escovinha e sino."""
    f = Faixa('resultado', 84, 16, 2, swing=0.12)
    f.canal('ep', -18, 0.3); f.canal('baixo', -19, 0.05); f.canal('sino', -22, 0.45, 0.3)
    f.canal('aro', -28, 0.2); f.canal('chocalho', -30, 0.1); f.canal('bumbo', -21, 0.05); f.canal('pad', -26, 0.4)
    prog = ['Fmaj7', 'Am7', 'Bbmaj7', 'C7sus4', 'Dm7', 'Am7', 'Bbmaj7', 'C']
    for c in range(16):
        sym = prog[c % 8]
        for b, d, v in ((0, 1.4, 0.55), (1.5, 0.4, 0.35), (2.5, 1.4, 0.45)):
            for k, m in enumerate(voz(sym, 57)):
                f.nota('ep', i_epiano, m, f.t(c, b), d, v, pan=(k / 3 - 0.5) * 0.5)
        bloco(f, 'pad', i_pad, sym, c, 4, 60, 0.3, corte=1200, a=1.0)
        bx = baixo(sym, 36)
        f.nota('baixo', i_sub, bx, f.t(c, 0), 1.8, 0.8)
        f.nota('baixo', i_sub, bx + (7 if c % 2 else 12), f.t(c, 2.5), 1.3, 0.6)
        if c >= 2:
            f.ritmo('bumbo', c, 'x.......x.x.....', 'k', lambda: d_bumbo(0.9, 0.25))
            f.ritmo('aro', c, '....x.......x...', 'r', d_aro)
            f.ritmo('chocalho', c, 'x.oxx.oxx.oxx.ox', 'sh', d_chocalho)
    mel = ('c6/1.5 a5/.5 g5 f5 | e5/3 r | d5 f5 a5 c6 | bb5/2 g5/2 | '
           'a5/1.5 f5/.5 d5 f5 | e5/1 g5/1 c6/2 | d6/1.5 c6/.5 a5 f5 | g5/4')
    toca_melodia(f, 'sino', i_sino, mel, 8, 0.55, tipo='celesta')
    return f.render(-19)


def _hub(nome, seed, prog, mel, cfg):
    """mesmo esqueleto para os três hubs: 80 bpm, 16 compassos, batida lofi; muda o tom, o timbre e o ambiente"""
    f = Faixa(nome, 80, 16, seed, swing=0.14)
    f.canal('acordes', -18, 0.3); f.canal('baixo', -18, 0.05); f.canal('mel', -19, 0.4, 0.25)
    f.canal('pad', -25, 0.45); f.canal('bumbo', -20, 0.05); f.canal('caixa', -25, 0.3); f.canal('chimbal', -30, 0.1)
    f.canal('amb', cfg['amb_db'], 0.1)
    for c in range(16):
        sym = prog[c % 8]
        if cfg['acordes'] == 'ep':
            for b, d, v in ((0, 1.4, 0.5), (1.75, 0.5, 0.3), (2.5, 1.4, 0.4)):
                for k, m in enumerate(voz(sym, cfg['lo'])):
                    f.nota('acordes', i_epiano, m, f.t(c, b + k * 0.02), d, v, pan=(k / 3 - 0.5) * 0.5)
        else:     # harpa / caixinha arpejando
            arpejo(f, 'acordes', cfg['acordes'], sym, c, [0, 2, 1, 3, 2, 4, 3, 5], cfg['lo'], 0.5, 0.5)
        bloco(f, 'pad', cfg.get('pad', i_pad), sym, c, 4, cfg['lo'] + 5, 0.35, **cfg.get('pad_kw', {'corte': 1100, 'a': 1.2}))
        bx = baixo(sym, 36)
        f.nota('baixo', i_sub, bx, f.t(c, 0), 1.6, 0.8)
        f.nota('baixo', i_sub, bx, f.t(c, 2.5), 0.4, 0.5)
        f.nota('baixo', i_sub, bx + 7, f.t(c, 3), 0.9, 0.5)
        if c >= 2 and not (c == 15):
            f.ritmo('bumbo', c, 'x......xx.x.....', 'k', lambda: d_bumbo(0.85, 0.22))
            f.ritmo('caixa', c, '....x.......x...', 's', lambda: lp(d_caixa(1.0, 0.1), 4000))
            f.ritmo('chimbal', c, 'x.x.x.x.x.x.xox.', 'h', d_chimbal)
    toca_melodia(f, 'mel', cfg['mel_inst'], mel, 4, 0.6, **cfg.get('mel_kw', {}))
    toca_melodia(f, 'mel', cfg['mel_inst'], mel, 12, 0.55, transp=12 if cfg.get('oitava') else 0, **cfg.get('mel_kw', {}))
    f.continuo('amb', cfg['amb'])
    return f.render(-20)


def _crepita(n):
    """fogueira: estalos esparsos e um ronco grave"""
    y = lp(ruido(n), 180) * 0.6
    k = rng.random(n) < 18 / SR
    estalo = np.zeros(n)
    estalo[k] = rng.uniform(0.3, 1.0, k.sum()) * rng.choice([-1, 1], k.sum())
    y += bp(estalo, 1500, 7000) * 6
    return y


def _chuva(n):
    return bp(ruido(n), 1500, 9000) * 0.5 + lp(ruido(n), 400) * 0.3


def _brisa(n):
    t = tv(n)
    return bp(ruido(n), 600, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 9.6))


def hub_inferno():
    """Hub do Inferno: lá menor, piano elétrico quente, fogueira estalando."""
    prog = ['Am9', 'Fmaj7', 'Cmaj7', 'E7sus4', 'Am9', 'Fmaj7', 'Dm7', 'E7']
    mel = ('e5/1.5 c5/.5 b4 a4 | c5/3 r | g5/1.5 e5/.5 d5 c5 | b4/3 r | '
           'e5/1.5 c5/.5 b4 a4 | a5/2 g5 e5 | f5 e5 d5 c5 | b4/3 r')
    return _hub('hub_inferno', 11, prog, mel, dict(acordes='ep', lo=55, mel_inst=i_sino,
                                                   mel_kw=dict(tipo='sino', escala=0.6), amb=_crepita, amb_db=-30))


def hub_purgatorio():
    """Hub do Purgatório: mi menor, caixinha de música arpejando, cordas suaves e chuva."""
    prog = ['Em9', 'Cmaj7', 'Gmaj7', 'B7sus4', 'Em9', 'Cmaj7', 'Am7', 'B7']
    mel = ('b5/1.5 g5/.5 f#5 e5 | g5/3 r | d6/1.5 b5/.5 a5 g5 | f#5/3 r | '
           'b5/1.5 g5/.5 f#5 e5 | e6/2 d6 b5 | c6 b5 a5 g5 | f#5/3 r')
    return _hub('hub_purgatorio', 12, prog, mel, dict(acordes=lambda fr, d, v: i_sino(fr, d, v, 'caixinha'), lo=64,
                                                      mel_inst=i_cordas, mel_kw=dict(corte=1800, a=0.25),
                                                      pad=i_cordas, pad_kw=dict(corte=1200, a=1.0),
                                                      amb=_chuva, amb_db=-35))


def hub_paraiso():
    """Hub do Paraíso: dó maior, harpa, coro baixinho e flauta, brisa."""
    prog = ['Cmaj7', 'Am7', 'Fmaj7', 'G6', 'Cmaj7', 'Em7', 'Fmaj7', 'Gsus4']
    mel = ('g5/1.5 e5/.5 d5 c5 | e5/3 r | a5/1.5 g5/.5 f5 e5 | d5/3 r | '
           'g5/1.5 e5/.5 d5 c5 | c6/2 b5 g5 | a5 g5 f5 e5 | d5/3 r')
    return _hub('hub_paraiso', 13, prog, mel, dict(acordes=i_harpa, lo=60, mel_inst=i_flauta,
                                                   pad=lambda fr, d, v, **k: i_coro(fr, d, v * 0.7, 'u', a=0.8, r=1.0),
                                                   pad_kw={}, amb=_brisa, amb_db=-32))


def riser(segundos):
    """subida de ruído (e um tom subindo) que termina seca no tempo 1 da parte seguinte"""
    n = int(segundos * SR)
    t = tv(n)
    e = (t / segundos) ** 3
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = hp(ruido(n), 1200) * e
    ph = np.cumsum(180 * 2 ** (3 * t / segundos)) / SR
    out += (0.25 * np.sin(2 * np.pi * ph) * e)[:, None]
    return out


def intensifica(f, acordes, viradas, passo=0.25, lo=40, chimbal='xoxoXoxoxoxoXoxo', pratos=2):
    """camadas a mais só das versões de chefe: chimbal em 16 avos, ostinato de cordas, sub no tempo 1, prato a cada
    `pratos` compassos e uma subida de ruído antes de cada parte nova"""
    f.canal('x_chimbal', -25, 0.1); f.canal('x_ost', -19, 0.25); f.canal('x_sub', -17, 0.05)
    f.canal('x_prato', -23, 0.4); f.canal('x_riser', -22, 0.3)
    for c, sym in enumerate(acordes):
        f.ritmo('x_chimbal', c, chimbal, 'xh', d_chimbal)
        r = baixo(sym, lo)
        b, i = 0.0, 0
        while b < 4 - 1e-6:
            m = r + {2: 12, 3: 7}.get(i % 4, 0)
            f.nota('x_ost', i_cordas, m, f.t(c, b), passo * 0.8, 0.7 if i % 4 == 0 else 0.5, a=0.005, r=0.05, corte=3200)
            b += passo
            i += 1
        f.nota('x_sub', i_sub, baixo(sym, 28), f.t(c), 1.0, 0.9, a=0.003, r=0.3)
        if c % pratos == 0:
            f.poe('x_prato', d_prato(), f.t(c), rng.uniform(-0.5, 0.5), 0.8)
    for v in viradas:
        f.poe('x_riser', riser(4 * f.b), f.t(v - 1), humano=0)


# ---------------------------------------------------------------- fases (normal e chefe)
def inferno(chefe=False):
    """Inferno: mi menor/frígio, 140 bpm, 32 compassos. Riff de guitarra abafada, bumbo e caixa pesados, coro grave e
    lead ameaçador. Chefe: bumbo duplo, metais, cordas em trêmolo, pratos e viradas."""
    f = Faixa('inferno_chefe' if chefe else 'inferno', 140, 32, 21)
    f.canal('gtr', -17, 0.08); f.canal('baixo', -17, 0.03); f.canal('pad', -23, 0.4); f.canal('lead', -15 if chefe else -17, 0.3, 0.15)
    f.canal('bumbo', -14, 0.03); f.canal('caixa', -17, 0.25); f.canal('chimbal', -26, 0.08); f.canal('prato', -24, 0.3)
    f.canal('tom', -19, 0.3); f.canal('coro', -22, 0.5)
    if chefe:
        f.canal('metal', -18, 0.35); f.canal('trem', -22, 0.3); f.canal('bumbo2', -18, 0.02)
    E2 = nota('e2')
    riff = [(E2, 'm'), (E2, 'm'), (E2 + 1, 'a'), (E2, 'm'), (E2 + 3, 'a'), (E2, 'm'), (E2 + 2, 'a'), (E2, 'm')]
    prog = ['Em', 'C', 'Am', 'B']
    queda = ['Em', 'F', 'Em', 'B']  # parte C: meio-tempo, frígio
    lead = ('e5 g5/.5 f#5/.5 e5 b4 | c5/1.5 e5/.5 g5 f#5/.5 e5/.5 | a5 c6 b5/.5 a5/.5 g5 | f#5/1.5 d#5/.5 b4/2 | '
            'e5/.5 f#5/.5 g5 b5 a5 | c6/1.5 b5/.5 g5/2 | a5 e6 d6/.5 c6/.5 b5 | b5/3 r')
    for c in range(32):
        sec = 'intro' if c < 4 else 'A' if c < 12 else 'B' if c < 20 else 'C' if c < 28 else 'A2'
        if sec == 'C':
            sym = queda[(c - 20) % 4]
        elif sec == 'B':
            sym = prog[(c - 12) % 4]
        else:
            sym = 'Em'
        # riff / power chords
        if sec in ('intro', 'A', 'A2'):
            for k, (m, tipo) in enumerate(riff):
                f.nota('gtr', i_guitarra, m, f.t(c, k * 0.5), 0.45 if tipo == 'm' else 0.5, 0.9 if tipo == 'a' else 0.7,
                       abafada=(tipo == 'm'))
        elif sec == 'B':
            r = baixo(sym, 40)
            for k in range(8):
                f.nota('gtr', i_guitarra, r, f.t(c, k * 0.5), 0.45, 0.7 if k % 2 else 0.85, abafada=k not in (0, 3, 6))
        else:
            r = baixo(sym, 40)
            f.nota('gtr', i_guitarra, r, f.t(c, 0), 3.5, 0.9)
        # baixo segue a guitarra
        if sec != 'intro' or chefe:
            if sec == 'C':
                f.nota('baixo', i_baixo, baixo(sym, 28), f.t(c), 3.8, 0.9, corte=500, dist=0.3, s=0.8)
            else:
                for k in range(8):
                    m = riff[k][0] - 12 if sec != 'B' else baixo(sym, 28)
                    f.nota('baixo', i_baixo, m, f.t(c, k * 0.5), 0.45, 0.8, corte=650, dist=0.7 if chefe else 0.2)
        bloco(f, 'pad', i_pad, sym, c, 4, 48, 0.4, corte=900, a=0.3)
        if sec in ('B', 'C') or chefe:
            for k, m in enumerate(voz(sym, 52)[:3]):
                f.nota('coro', i_coro, m, f.t(c), 4, 0.5, pan=(k - 1) * 0.4, vogal='o' if sec == 'C' else 'a')
        # bateria
        if sec == 'intro' and not chefe:
            f.ritmo('bumbo', c, 'x.......x.......', 'k', d_bumbo)
            f.ritmo('chimbal', c, 'x.x.x.x.x.x.x.x.', 'h', d_chimbal)
        elif sec == 'C':
            f.ritmo('bumbo', c, 'x.........x.....', 'k', d_bumbo)
            f.ritmo('caixa', c, '........X.......', 's', d_caixa)
            f.ritmo('tom', c, '..x...x.....x.x.' if c % 2 else '................', 't', lambda: d_tom(80))
            f.ritmo('chimbal', c, 'x...x...x...x...', 'ho', lambda: d_chimbal(True))
        else:
            f.ritmo('bumbo', c, 'x.x...x.x.x...x.', 'k', d_bumbo)
            f.ritmo('caixa', c, '....X.......X...', 's', d_caixa)
            f.ritmo('chimbal', c, 'x.x.x.x.x.x.x.x.' if not chefe else 'xoxoxoxoxoxoxoxo', 'h', d_chimbal)
        if c % 8 == 7 and sec != 'C':
            f.ritmo('tom', c, '............xxxx', 't2', lambda: d_tom(130))
            f.ritmo('caixa', c, '............ooxx', 's', d_caixa)
        if c in (4, 12, 20, 28) or (chefe and c % 4 == 0):
            f.poe('prato', d_prato(), f.t(c), rng.uniform(-0.4, 0.4), 0.9)
        if chefe:
            f.ritmo('bumbo2', c, 'xxxxxxxxxxxxxxxx' if sec != 'C' else 'x.x.x.x.x.x.x.x.', 'k2', lambda: d_bumbo(1.1, 0.15))
            # metais: acorde no 1 e no "e" do 2
            for b, d in ((0, 1.0), (1.5, 0.5), (3.0, 0.75)):
                for k, m in enumerate(voz(sym, 55)[:3]):
                    f.nota('metal', i_metal, m, f.t(c, b), d, 0.85, pan=(k - 1) * 0.5)
            r = baixo(sym, 52)
            for m in (r, r + 12):
                f.nota('trem', i_cordas, m, f.t(c), 4, 0.6, trem=0.8, beat=f.b, corte=3500, a=0.02)
    toca_melodia(f, 'lead', i_lead, lead, 12, 0.85, corte=2800, mix_q=0.3)
    toca_melodia(f, 'lead', i_lead, lead, 28, 0.8, corte=3200, mix_q=0.3)    # A2 (4 compassos: só a 1ª metade)
    if chefe:
        toca_melodia(f, 'metal', i_metal, lead, 12, 0.7, transp=-12)
        toca_melodia(f, 'lead', i_lead, 'e6/2 f6/2 | g6/1 f6/1 e6/2 | e6/2 f6/2 | a6/1 g6/1 f6/2 | '
                     'e6/2 f6/2 | g6/1 f6/1 e6/2 | f6/2 e6/1 d#6/1 | e6/4', 20, 0.75, corte=3500)
    if chefe:
        acordes = ['Em' if c < 12 or c >= 28 else prog[(c - 12) % 4] if c < 20 else queda[(c - 20) % 4] for c in range(32)]
        intensifica(f, acordes, [4, 12, 20, 28], passo=0.25, lo=40)
    return f.render(-14 if chefe else -16, pico_db=-3.0)   # o vorbis passa ~2 dB dos picos da guitarra


def purgatorio(chefe=False):
    """Purgatório: ré menor, 90 bpm, 24 compassos. Pad escuro, caixinha/sino com reverb longo, teremim, vento e
    bateria esparsa. Chefe (Cutulu): taikos, cordas graves em trêmolo, metais dissonantes, coro e bumbo em todo tempo."""
    f = Faixa('purgatorio_chefe' if chefe else 'purgatorio', 90, 24, 31)
    f.canal('pad', -20, 0.45); f.canal('sino', -20, 0.55, 0.3); f.canal('baixo', -18, 0.05); f.canal('ter', -20, 0.5, 0.2)
    f.canal('bumbo', -18, 0.1); f.canal('aro', -26, 0.35); f.canal('chocalho', -30, 0.15); f.canal('vento', -31, 0.2)
    if chefe:
        f.canal('taiko', -14, 0.3); f.canal('trem', -20, 0.3); f.canal('metal', -18, 0.45); f.canal('coro', -21, 0.5)
        f.canal('prato', -25, 0.35); f.canal('chimbal', -27, 0.1)
    prog = ['Dmadd9', 'Bbmaj7', 'Gm6', 'A', 'Dmadd9', 'Bbmaj7', 'Gm6', 'A7']
    sino = ('a5 d6 c6 a5 | bb5/2 f5 g5 | g5/1.5 a5/.5 bb5 d6 | c#6/3 e5 | '
            'f5 a5 d6 e6 | f6/2 e6 d6 | bb5 a5 g5 e5 | a5/4')
    ter = 'd5/4 | f5/2 e5/2 | d5/2 bb4/2 | a4/4 | d5/2 e5/2 | f5/3 g5/1 | e5/2 c#5/2 | e5/4'
    for c in range(24):
        sec = 'intro' if c < 4 else 'A' if c < 12 else 'B' if c < 20 else 'A2'
        sym = prog[c % 8]
        bloco(f, 'pad', i_pad, sym, c, 4, 50, 0.45, corte=800 if sec == 'intro' else 1100, a=1.2, det=0.18, r=1.5)
        if sec != 'intro' or chefe:
            f.nota('baixo', i_sub, baixo(sym, 26), f.t(c), 3.6, 0.85, a=0.05, r=0.4)
        if sec in ('A', 'B', 'A2') and not (chefe and sec == 'B'):
            f.ritmo('bumbo', c, 'x.....x.........' if not chefe else 'x...x...x...x...', 'k', lambda: d_bumbo(0.8, 0.4))
            f.ritmo('aro', c, '........x.......', 'r', d_aro)
            f.ritmo('chocalho', c, 'x.o.x.o.x.o.x.oo' if sec == 'B' else 'x...x...x...x...', 'sh', d_chocalho)
        if chefe:
            pad_t = 'X..x..x.X..x.x.x' if sec != 'intro' else 'X.......x.......'
            f.ritmo('taiko', c, pad_t, 'tk', d_taiko)
            if sec == 'B':
                f.ritmo('bumbo', c, 'x.x.x.x.x.x.x.x.', 'k', lambda: d_bumbo(0.8, 0.4))
                f.ritmo('chimbal', c, 'xoxoxoxoxoxoxoxo', 'h', d_chimbal)
            r = baixo(sym, 38)
            for m in (r, r + 7):
                f.nota('trem', i_cordas, m, f.t(c), 4, 0.6, trem=0.9, beat=f.b, corte=2200, a=0.02)
            # metais: o trítono por cima da raiz, no 1 e no 3-e
            for b, d in ((0, 1.2), (2.5, 1.0)):
                for m in (baixo(sym, 50), baixo(sym, 50) + 6, baixo(sym, 50) + 13):
                    f.nota('metal', i_metal, m, f.t(c, b), d, 0.7 if b else 0.85, pan=rng.uniform(-0.4, 0.4), corte_max=2500)
            for k, m in enumerate(voz(sym, 48)[:3]):
                f.nota('coro', i_coro, m, f.t(c), 4, 0.6, pan=(k - 1) * 0.5, vogal='u')
            if c % 4 == 0:
                f.poe('prato', d_prato(), f.t(c), 0.3, 0.8)
    f.continuo('vento', lambda n: _brisa(n) * 0.7 + lp(ruido(n), 300) * 0.5)
    toca_melodia(f, 'sino', i_sino, sino, 4, 0.6, tipo='caixinha')
    toca_melodia(f, 'sino', i_sino, sino, 20, 0.5, tipo='caixinha')      # A2: metade
    # teremim: frase deslizando
    frase_teremim(f, 'ter', ter, 12, 0.6)
    if chefe:
        toca_melodia(f, 'sino', i_sino, sino, 12, 0.45, transp=-12, tipo='sino', escala=0.7)
    if chefe:
        intensifica(f, [prog[c % 8] for c in range(24)], [4, 12, 20], passo=0.5, lo=38)
        for c in range(3, 24, 4):     # virada de taikos no fim de cada frase
            f.ritmo('taiko', c, '........x.x.xxxx', 'tk', d_taiko, 0.8)
    return f.render(-14 if chefe else -17, pico_db=-3.0 if chefe else -2.0)


def frase_teremim(f, bus, txt, compasso, vel):
    notas = [(b, d, m) for b, d, m in melodia(txt)]
    tot = sum(d for _, d, _ in notas) * f.b + 1.5
    n = int(tot * SR)
    alvo = np.zeros(n)
    amp = np.zeros(n)
    for b, d, m in notas:
        i0, i1 = int(b * f.b * SR), int((b + d) * f.b * SR)
        alvo[i0:i1] = hz(m) if m else (alvo[i0 - 1] if i0 else 0)
        amp[i0:i1] = 1.0 if m else 0.0
    alvo[alvo == 0] = alvo[alvo > 0][0]
    j = int(0.07 * SR)
    fr = media_movel(media_movel(alvo, j), j)
    amp = media_movel(media_movel(amp, int(0.12 * SR)), int(0.12 * SR))
    fr *= vibrato(n, 6.0, 0.012, 0.0)
    ph = np.cumsum(fr / SR)
    y = (np.sin(2 * np.pi * ph) + 0.1 * np.sin(4 * np.pi * ph)) * amp * vel
    f.poe(bus, y, f.t(compasso), 0.15, humano=0)


def i_caixinha_torta(f, dur, vel, wow=0.009, desafina=20):
    """caixinha de música gasta: duas vozes um pouco desafinadas entre si e a altura oscilando devagar (fita velha)"""
    n = int(2.4 * 4 * SR)
    t = tv(n)
    y = np.zeros(n)
    lfo = 1 + wow * np.sin(2 * np.pi * rng.uniform(0.45, 0.7) * t + rng.random() * 6) \
        + 0.4 * wow * np.sin(2 * np.pi * rng.uniform(3.5, 5) * t + rng.random() * 6)
    for c, g in ((0, 1.0), (desafina + rng.uniform(-4, 4), 0.55)):
        ph = np.cumsum(f * 2 ** (c / 1200) * lfo / SR)
        for r, a, d in ((1, 1, 2.4), (3.0, .2, .35), (5.2, .08, .15), (2.0, .18, .7)):
            if f * r < 16000:
                y += g * a * np.sin(2 * np.pi * r * ph + rng.random() * 6) * np.exp(-t / d)
    return y * np.clip(t / 0.001, 0, 1) * vel


def paraiso(chefe=False):
    """Paraíso: alegria forçada. Dó "maior", 100 bpm, 24 compassos. Por cima tudo é doce (caixinha de música, harpa,
    pad aéreo, coro limpo) e a melodia é de canção de ninar em dó maior, mas os acordes descem para o fá menor e o lá
    bemol emprestados, a melodia insiste no lá natural sobre eles e termina num ré bemol que não resolve; a caixinha
    oscila como fita velha; embaixo um zumbido grave com um semitom de choque e um sino distante a cada 4 compassos;
    a batida é oca (bumbo no 1 e no 3, palma só no 4) e em três compassos tudo some e sobra o vazio. Chefe (Deus): a máscara racha. Coro grande em
    cluster, tímpanos, metais com o trítono, cordas em trêmolo e a melodia nos metais graves, em menor."""
    f = Faixa('paraiso_chefe' if chefe else 'paraiso', 100, 24, 41)
    f.canal('caixa_m', -17, 0.62, 0.3); f.canal('harpa', -24, 0.45, 0.2); f.canal('pad', -26, 0.5)
    f.canal('coro', -23, 0.6); f.canal('drone', -20, 0.3); f.canal('baixo', -19, 0.1); f.canal('sino', -25, 0.75)
    f.canal('bumbo', -18, 0.25); f.canal('palma', -23, 0.6); f.canal('chocalho', -31, 0.2)
    if chefe:
        f.canal('coro2', -17, 0.6); f.canal('timp', -15, 0.4); f.canal('metal', -16, 0.45); f.canal('trem', -21, 0.35)
        f.canal('prato', -24, 0.4); f.canal('taiko', -18, 0.35)
    prog = ['C', 'Am', 'Fm', 'Ab', 'Fm', 'Db', 'Fm6', 'Gsus4']
    mel = ('g5 e5 g5 c6 | b5/1.5 a5/.5 e5/2 | f5 a5 c6 ab5 | g5/3 eb5 | '
           'g5 e5 g5 c6 | db6/1.5 c6/.5 bb5/2 | a5 c6 d6 f6 | c6/2 db6/2')
    compassos = [b.strip() for b in mel.split('|')]
    for c in range(24):
        sec = 'intro' if c < 4 else 'A' if c < 12 else 'vazio' if c < 15 else 'B' if c < 20 else 'fim'
        sym = prog[c % 8]
        # embaixo: zumbido em dó com um ré bemol escondido (sempre, inclusive no vazio)
        f.nota('drone', i_pad, nota('c2'), f.t(c), 4.2, 0.6, corte=400, vozes=3, det=0.05, a=1.5, r=1.5)
        f.nota('drone', i_pad, nota('db3'), f.t(c), 4.2, 0.35, corte=700, vozes=3, det=0.08, a=1.5, r=1.5)
        if c % 4 == 0:   # sino distante, grave
            f.nota('sino', i_sino, nota('c3'), f.t(c), 4, 0.6, tipo='sino', escala=1.4)
        if sec == 'vazio' and not chefe:
            if c == 12:
                f.nota('caixa_m', i_caixinha_torta, nota('c6'), f.t(c, 1), 2, 0.5, wow=0.025)
            if c == 14:
                f.nota('caixa_m', i_caixinha_torta, nota('db6'), f.t(c, 2), 2, 0.35, wow=0.03)
            continue
        bloco(f, 'pad', i_pad, sym, c, 4, 64, 0.4, corte=2800, vozes=5, det=0.2, a=0.4)
        if sec != 'intro' or chefe:
            arpejo(f, 'harpa', i_pluck, sym, c, [0, 2, 1, 3, 2, 4, 3, 5], 55, 0.5, 0.5, brilho=0.55, decai=1.0, rel=0.4)
        if sec in ('B', 'fim') or chefe:
            for k, m in enumerate(voz(sym, 67)[:3]):
                f.nota('coro', i_coro, m, f.t(c), 4, 0.5, pan=(k - 1) * 0.5, vogal='u', a=0.6)
        if sec in ('A', 'B') or chefe:
            f.nota('baixo', i_sub, baixo(sym, 36), f.t(c), 1.8, 0.8)
            f.nota('baixo', i_sub, baixo(sym, 36), f.t(c, 2), 1.8, 0.6)
            f.ritmo('bumbo', c, 'x.......x.......', 'k', lambda: lp(d_bumbo(0.8, 0.3), 2500))
            f.ritmo('palma', c, '............x...', 'cl', d_palma)
            f.ritmo('chocalho', c, '..x...x...x...x.', 'sh', d_chocalho)
        if chefe:
            # a máscara racha: coro grande em cluster (acorde + semitom), tímpanos, metais com trítono, trêmolo
            notas = voz(sym, 52)[:3]
            for k, m in enumerate(notas + [notas[0] + 1]):
                f.nota('coro2', i_coro, m, f.t(c), 4, 0.7, pan=(k / 3 - 0.5), vogal='a', a=0.15)
            r = baixo(sym, 40)
            f.ritmo('timp', c, 'X.......x.....x.', 'tp%d' % (c % 8), lambda: d_timpano(hz(r)))
            f.ritmo('taiko', c, '....x.......x.xx', 'tk', d_taiko)
            for b, d in ((0, 1.5), (2.5, 1.0)):
                for m in (baixo(sym, 48), baixo(sym, 48) + 6, baixo(sym, 48) + 12):
                    f.nota('metal', i_metal, m, f.t(c, b), d, 0.8 if b == 0 else 0.65, pan=rng.uniform(-0.4, 0.4))
            for m in (r, r + 7):
                f.nota('trem', i_cordas, m, f.t(c), 4, 0.6, trem=0.85, beat=f.b, corte=3000, a=0.02)
            if c % 4 == 0:
                f.poe('prato', d_prato(), f.t(c), rng.uniform(-0.4, 0.4), 0.9)
    # a canção de ninar: sozinha no começo, inteira no A e mais aguda no B, cada vez mais torta
    toca_melodia(f, 'caixa_m', i_caixinha_torta, ' '.join(compassos[:4]), 0, 0.6, wow=0.009)
    toca_melodia(f, 'caixa_m', i_caixinha_torta, mel, 4, 0.7, wow=0.01)
    toca_melodia(f, 'caixa_m', i_caixinha_torta, ' '.join(compassos[:5]), 15, 0.65, transp=12, wow=0.016)
    toca_melodia(f, 'caixa_m', i_caixinha_torta, 'a6 c7 db7 f7 | c7/2 db7/2', 20, 0.55, wow=0.022)
    toca_melodia(f, 'caixa_m', i_caixinha_torta, 'g5 e5 g5 c6 | b5/1.5 ab5/.5 eb5/2', 22, 0.5, wow=0.026)
    if chefe:
        # a melodia nos metais graves, em menor (mi bemol e lá bemol no lugar de mi e lá)
        troca = {'e5': 'eb5', 'a5': 'ab5', 'e6': 'eb6', 'a6': 'ab6'}
        menor = ' '.join(troca.get(t.split('/')[0], t.split('/')[0]) + t[len(t.split('/')[0]):] for t in mel.split())
        toca_melodia(f, 'metal', i_metal, menor, 4, 0.65, transp=-12)
        toca_melodia(f, 'metal', i_metal, menor, 15, 0.7, transp=-12)
    if chefe:
        intensifica(f, [prog[c % 8] for c in range(24)], [4, 12, 15, 20], passo=0.5, lo=40)
        for c in range(3, 24, 4):     # rufo de tímpano no fim de cada frase
            f.ritmo('timp', c, '............xxXX', 'tp_rufo', lambda: d_timpano(hz(nota('c2'))), 0.8)
    return f.render(-14 if chefe else -17, pico_db=-3.0 if chefe else -2.0)


FAIXAS = {
    'resultado': resultado,
    'hub_inferno': hub_inferno, 'hub_purgatorio': hub_purgatorio, 'hub_paraiso': hub_paraiso,
    'inferno': inferno, 'inferno_chefe': lambda: inferno(True),
    'purgatorio': purgatorio, 'purgatorio_chefe': lambda: purgatorio(True),
    'paraiso': paraiso, 'paraiso_chefe': lambda: paraiso(True),
}


def grava(nome, y, pasta_wav=None):
    os.makedirs(SAIDA, exist_ok=True)
    pcm = np.clip(y * 32767, -32768, 32767).astype(np.int16)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(pasta_wav or tmp, nome + '.wav')
        with wave.open(wav, 'wb') as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        ogg = os.path.join(SAIDA, nome + '.ogg')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-c:a', 'libvorbis', '-q:a', QUALIDADE_OGG,
                        '-map_metadata', '-1', '-fflags', '+bitexact', ogg], check=True)
    return ogg


if __name__ == '__main__':
    args = sys.argv[1:]
    pasta_wav = None
    if '--wav' in args:
        i = args.index('--wav')
        pasta_wav = args[i + 1]
        os.makedirs(pasta_wav, exist_ok=True)
        del args[i:i + 2]
    for nome in args or list(FAIXAS):
        y = FAIXAS[nome]()
        ogg = grava(nome, y, pasta_wav)
        print(f'{nome}: {len(y) / SR:.2f}s, pico {20 * np.log10(np.abs(y).max()):.1f} dBFS, '
              f'rms {20 * np.log10(np.sqrt(np.mean(y ** 2))):.1f} dBFS -> {os.path.relpath(ogg, RAIZ)} '
              f'({os.path.getsize(ogg) // 1024} KB)')
