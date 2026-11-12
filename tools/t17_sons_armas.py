"""Tarefa 17: sons de armas sintetizados (sem samples): assets/som_pistola.wav, som_doze.wav, som_minigun.wav, som_lanca.wav, som_explosao.wav.

Terceira versão: som de perto (seco, estalo de agudos no ataque, ecos e cauda bem baixos) e pico mais baixo.
Segunda versão. A primeira soava "sub + chiado": faltava o meio (400 Hz a 2,5 kHz) e os ecos de um tiro gravado de verdade. Agora:
  1. sopro de boca: pulsos de Friedlander (salto de pressão + fase negativa), com reflexão no chão alguns décimos de ms depois;
  2. corpo em 28 bandas de ruído, cada uma com seu nível (perfil espectral cheio nos médios) e decaimento em dois estágios
     (queda rápida + cauda fraca e longa; agudos morrem antes dos graves);
  3. saturação forte do ataque (como microfone/compressor de gravação de tiro), que adensa os médios;
  4. ecos discretos (paredes/chão a 80-500 ms), cada um mais escuro e alternando de lado, e um pouco de reverb difuso estéreo;
  5. peças metálicas (ferrolho da pistola, tubo do lança-granadas) como senos amortecidos.
Os perfis foram calibrados medindo, por banda, nível e tempos de queda das gravações reais que já estavam no projeto (glock18, sawedoff, shotgun).
Semente fixa: o resultado é sempre o mesmo.   Rodar:  python3 tools/t17_sons_armas.py
"""
import os, wave
import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PF = [60, 150, 400, 1000, 2500, 6000, 14000]   # frequências de controle dos perfis


def interp(fc, vals):
    return np.interp(np.log(fc), np.log(PF), vals)


def passa(x, lo=None, hi=None, ordem=3):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    h = np.ones_like(f)
    if lo:
        h *= 1 - 1 / np.sqrt(1 + (f / lo) ** (2 * ordem) + 1e-30)
    if hi:
        h *= 1 / np.sqrt(1 + (f / hi) ** (2 * ordem))
    return np.fft.irfft(X * h, len(x))


def corpo(n, rng, perfil_db, t_rapido, cauda_db, t_cauda, nb=28):
    """Ruído em nb bandas (50 Hz a 16 kHz): nível por banda (dB) e envelope rápido + cauda, tudo interpolado nos pontos PF."""
    t = np.arange(n) / SR
    f = np.fft.rfftfreq(n, 1 / SR)
    bordas = np.geomspace(50, 16000, nb + 1)
    out = np.zeros(n)
    for lo, hi in zip(bordas[:-1], bordas[1:]):
        fc = np.sqrt(lo * hi)
        X = np.fft.rfft(rng.standard_normal(n))
        X[(f < lo) | (f >= hi)] = 0
        b = np.fft.irfft(X, n)
        b /= np.sqrt(np.mean(b ** 2)) + 1e-12
        e = np.exp(-t / interp(fc, t_rapido)) + 10 ** (interp(fc, cauda_db) / 20) * np.exp(-t / interp(fc, t_cauda))
        e *= 1 - np.exp(-t / 0.00012)
        out += b * e * 10 ** (interp(fc, perfil_db) / 20)
    return out


def friedlander(n, T, amp=1.0, atraso=0.0):
    t = np.arange(n) / SR - atraso
    p = np.where(t >= 0, (1 - t / T) * np.exp(-t / T), 0.0)
    return amp * p


def metal(n, rng, quando, freqs, tau, amp):
    t = np.arange(n) / SR - quando
    y = np.zeros(n)
    for f in freqs:
        y += np.where(t >= 0, np.sin(2 * np.pi * f * t + rng.random() * 6.28) * np.exp(-t / (tau * (0.6 + 0.8 * rng.random()))), 0)
    return amp * y / len(freqs)


def clique(n, rng, quando, lo, hi, tau, amp):
    """Peça mecânica como estalo de ruído em banda (ferrolho, culatra): sem tom, para não soar como brinquedo."""
    t = np.arange(n) / SR - quando
    return amp * passa(rng.standard_normal(n), lo, hi, 2) * np.where(t >= 0, np.exp(-t / tau), 0)


def satura(x, drive):
    x = x / np.max(np.abs(x))
    return np.tanh(x * drive) / np.tanh(drive)


def ecos_e_sala(x, ecos, rt, molhado, rng, total):
    """ecos = [(atraso s, ganho dB, passa-baixas Hz)]; devolve estéreo com os ecos alternando de lado e reverb difuso."""
    n = int(SR * total)
    L = np.zeros(n); R = np.zeros(n)
    m = min(len(x), n)
    L[:m] += x[:m]; R[:m] += x[:m]
    for k, (d, g, lp) in enumerate(ecos):
        e = passa(x, 120, lp, 2) * 10 ** (g / 20)
        i = int(d * SR)
        j = min(n, i + len(e))
        pan = 0.5 + (0.28 if k % 2 == 0 else -0.28)
        L[i:j] += e[:j - i] * (1 - pan) * 1.4; R[i:j] += e[:j - i] * pan * 1.4
    if molhado > 0:
        nr = int(SR * rt * 1.3)
        tr = np.arange(nr) / SR
        seco = (L + R) / 2
        for canal in (L, R):
            ir = passa(rng.standard_normal(nr) * np.exp(-6.9 * tr / rt), 200, 4500, 2)
            ir[:int(0.012 * SR)] = 0
            ir /= np.sqrt(np.sum(ir ** 2))
            tam = n + nr
            canal += np.fft.irfft(np.fft.rfft(seco, tam) * np.fft.rfft(ir, tam), tam)[:n] * molhado
    return L, R


def grava(L, R, nome, fade=0.04, pico=0.8):
    L, R = passa(L, 30, None, 2), passa(R, 30, None, 2)
    n = len(L)
    g = np.minimum(1, (n - np.arange(n)) / (SR * fade))
    st = np.stack([L * g, R * g], 1)
    st = np.tanh(st / np.max(np.abs(st)) * 1.1) / np.tanh(1.1)   # limitador suave final
    pcm = (st / np.max(np.abs(st)) * pico * 32767).astype('<i2')
    with wave.open(os.path.join(ROOT, 'assets', nome), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def golpe(n, f0, f1, tau_f, tau_a, amp, ini=0.001):
    """Golpe grave limpo (seno que cai de f0 a f1): é o 'soco' do tiro. Fica fora da saturação para não virar chiado."""
    t = np.arange(n) / SR - ini
    tp = np.maximum(t, 0)
    f = f1 + (f0 - f1) * np.exp(-tp / tau_f)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp / tau_a) * (1 - np.exp(-tp / 0.0015))
    return amp * np.where(t >= 0, y, 0)


def satura_densa(x, drive):
    """Limitador de gravação de tiro: normaliza pelo RMS dos primeiros 20 ms e satura. Com drive > 1 o som fica colado no pico
    por tau * ln(drive) segundos antes de começar a cair: é isso que dá peso ao tiro (as gravações reais ficam a -2..-6 dB do pico por 100-200 ms)."""
    r = np.sqrt(np.mean(x[:int(0.02 * SR)] ** 2))
    y = np.tanh(x / r * drive)
    return passa(y, None, 10000, 2)


def reforca_grave(x, f, db):
    """Prateleira de graves: sobe `db` abaixo de `f` Hz (transição suave), sem acrescentar tom nenhum."""
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 + (10 ** (db / 20) - 1) / (1 + (fr / f) ** 4)
    return np.fft.irfft(X * g, len(x))


def zip_ruido(n, rng, f_ini, f_fim, tau_f, largura, tau_a, ataque=0.001):
    """Faixa estreita de ruído cujo centro desce de f_ini a f_fim: o "tfiu" do silenciador de filme (não é um seno: é ruído afinado)."""
    t = np.arange(n) / SR
    base = passa(rng.standard_normal(n), None, largura / 2, 3) + 1j * passa(rng.standard_normal(n), None, largura / 2, 3)
    fc = f_fim + (f_ini - f_fim) * np.exp(-t / tau_f)
    y = np.real(base * np.exp(2j * np.pi * np.cumsum(fc) / SR))
    y /= np.max(np.abs(y))
    return y * np.exp(-t / tau_a) * (1 - np.exp(-t / ataque))


def tiro(rng, dur_seco, T, sopro_amp, perfil, t_rapido, cauda_db, t_cauda, drive, extra=None, soco=None, denso=False, estalo=0.9):
    n = int(SR * dur_seco)
    x = corpo(n, rng, perfil, t_rapido, cauda_db, t_cauda)
    x /= np.max(np.abs(x))
    ini = 0.001
    x = np.roll(x, int(ini * SR)); x[:int(ini * SR)] = 0
    x += friedlander(n, T, sopro_amp, ini) + friedlander(n, T * 1.3, -0.55 * sopro_amp, ini + 0.0011 + T)   # sopro direto + reflexão no chão
    # estalo de perto: 1,5 ms de agudos colados no ataque (é o que some com a distância)
    tt = np.arange(n) / SR - ini
    x += passa(rng.standard_normal(n), 4000, None, 2) * np.where(tt >= 0, np.exp(-tt / 0.0015), 0) * estalo
    if extra is not None:
        x += extra(n)
    x = satura_densa(x, drive) if denso else satura(x, drive)
    if soco:
        x = x + golpe(n, *soco)
    x *= np.minimum(1, (n - np.arange(n)) / (SR * 0.05))
    return x


def camadas(dur, rng, lista, drive=2.0):
    """Som em camadas de ruído filtrado. Cada camada: (lo, hi, t0, ataque, segura, queda, dB, largura[, estalos/s]).
    Começa em t0, sobe em `ataque` s, fica `segura` s no topo e cai com constante `queda` s. largura 0 = igual nos dois lados (centro),
    1 = ruído independente em cada lado. No fim, um limitador denso (tanh) cola tudo perto do pico. Devolve (L, R)."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    L, R = np.zeros(n), np.zeros(n)
    for lo, hi, t0, atk, seg, queda, db, larg, *resto in lista:
        tt = t - t0
        env = np.where(tt < 0, 0, np.where(tt < atk, (np.maximum(tt, 0) / atk) ** 2, np.where(tt < atk + seg, 1, np.exp(-(tt - atk - seg) / queda))))
        if resto:      # picotado: estalos aleatórios, cada um com decaimento de ~12 ms
            gr = np.zeros(n)
            for q in rng.uniform(t0, dur, int(resto[0] * dur)):
                gr += np.where(t >= q, np.exp(-(t - q) / 0.012), 0) * rng.uniform(0.3, 1)
            env = env * gr
        c, a, b = (passa(rng.standard_normal(n), lo, hi, 3) for _ in range(3))
        c, a, b = (v / np.sqrt(np.mean(v ** 2)) for v in (c, a, b))
        g = 10 ** (db / 20)
        L += g * env * (np.sqrt(1 - larg) * c + np.sqrt(larg) * a)
        R += g * env * (np.sqrt(1 - larg) * c + np.sqrt(larg) * b)
    r = np.sqrt(np.mean(np.concatenate([L, R]) ** 2 * np.concatenate([np.exp(-t / 0.15)] * 2)) / np.mean(np.exp(-t / 0.15)))
    return np.tanh(L / r * drive / 2.5), np.tanh(R / r * drive / 2.5)


def main():
    # ---- pistola, doze e explosão: receita em camadas (ver `camadas`), medida nos sons de um jogo de referência (só os números:
    #      duração, quanto tempo fica perto do pico, equilíbrio de graves/agudos em cada instante, largura estéreo). O que faltava:
    #        1. ordem no tempo: estalo claro (0-10 ms) -> soco médio (10-30 ms) -> onda de GRAVE que cresce depois (30-250 ms) -> cauda;
    #        2. o grave fica a 3-6 dB do pico por 100-300 ms (antes caía 14 dB em 80 ms: som "fino");
    #        3. os agudos não somem no corpo do som (ficam ~15-20 dB abaixo, o "ar"); antes iam a -30..-70 dB (som abafado);
    #        4. estéreo de verdade: ar e cauda diferentes em cada lado (antes era praticamente mono);
    #        5. cauda de 0,5-1,2 s, baixa e cheia de médios.
    #      Tudo ruído filtrado (nenhum seno: seno caindo de tom é o que dá som de brinquedo). Pico menor (0,55): estavam altos.
    rng = np.random.default_rng(7001)
    # pistola com silenciador: mesma estrutura, com o estalo e o ar mais baixos e mais escuros (é o que "abafa"), mas com soco e grave
    L, R = camadas(0.75, rng, [
        # lo,  hi,    t0,    ataque, segura, queda, dB,  largura
        (700, 3500, 0.000, 0.0005, 0.002, 0.006, -3, 0.0),     # estalo (abafado: sem nada acima de 3,5 kHz)
        (140, 600, 0.002, 0.003, 0.010, 0.022, 0, 0.0),        # soco
        (38, 115, 0.008, 0.012, 0.030, 0.050, 3, 0.0),         # grave que cresce depois
        (1500, 5000, 0.004, 0.004, 0.010, 0.035, -14, 0.8),    # ar ("pff")
        (150, 1500, 0.030, 0.030, 0.000, 0.110, -19, 1.0),     # cauda
    ], drive=1.6)
    grava(L, R, 'som_pistola.wav', fade=0.2, pico=0.5)

    # doze: estalo forte, soco, e uma onda de grave longa que segura o som perto do pico por ~200 ms; cauda de ~1 s
    L, R = camadas(1.15, rng, [
        (500, 9000, 0.000, 0.0003, 0.004, 0.008, 0, 0.0),
        (120, 500, 0.004, 0.004, 0.020, 0.040, 1, 0.1),
        (28, 95, 0.020, 0.030, 0.110, 0.110, 6, 0.0),
        (250, 2000, 0.010, 0.010, 0.050, 0.090, -8, 0.5),
        (2000, 12000, 0.006, 0.006, 0.040, 0.085, -13, 0.9),
        (120, 1800, 0.080, 0.080, 0.000, 0.230, -17, 1.0),
    ], drive=2.2)
    grava(L, R, 'som_doze.wav', fade=0.3, pico=0.55)

    # explosão: dois tempos. Estalo + soco, um respiro (~40 ms), e depois a onda de grave grande (o "BUM" chega atrasado);
    #      a cauda não escurece: tem estalidos claros (destroços) por cima do ronco
    L, R = camadas(2.2, rng, [
        (250, 9000, 0.000, 0.0005, 0.006, 0.012, 2, 0.0),
        (100, 450, 0.004, 0.004, 0.018, 0.030, 1, 0.1),
        (22, 65, 0.045, 0.045, 0.110, 0.300, 6, 0.0),
        (60, 250, 0.050, 0.050, 0.080, 0.350, -3, 0.3),
        (250, 2500, 0.030, 0.060, 0.100, 0.380, -5, 0.7),
        (2500, 12000, 0.010, 0.030, 0.080, 0.320, -8, 0.9),
        (1500, 9000, 0.200, 0.150, 0.250, 0.450, -14, 1.0, 18),   # destroços: ruído picotado (último número = estalos por segundo)
    ], drive=2.4)
    # som_explosao.wav agora vem de gravações CC0 (tools/t19_sons_cc0.py); esta versão sintetizada não é mais gravada

    # minigun (um tiro, tocado em rajada): a mesma ordem, bem curta e quase mono para a rajada não embolar.
    #      Muito grave e agudo, pouco médio (é o que deixa cada tiro "seco" e pesado); cauda mínima.
    rng = np.random.default_rng(7002)
    L, R = camadas(0.4, rng, [
        (900, 9000, 0.000, 0.0003, 0.002, 0.004, -1, 0.0),     # estalo
        (120, 420, 0.002, 0.002, 0.006, 0.014, 0, 0.0),        # soco
        (35, 110, 0.005, 0.008, 0.016, 0.028, 5, 0.0),         # grave que cresce depois
        (2500, 12000, 0.002, 0.003, 0.008, 0.022, -11, 0.3),   # ar
        (200, 2500, 0.020, 0.020, 0.000, 0.060, -22, 0.8),     # cauda
    ], drive=2.2)
    # som_minigun.wav agora vem de gravações CC0 (tools/t19_sons_cc0.py); esta versão sintetizada não é mais gravada

    # lança-granadas: o "tunc" de tubo (M79): um estouro oco e AFINADO, curto, como rolha saindo de um cano. O que dá esse som é a
    #      ressonância do tubo: um tom grave (~210 Hz caindo um pouco para ~160) com um parcial acima, que soa ~120 ms e some.
    #      Em volta: estalo abafado, soco curto, pouco grave profundo e pouca cauda (não é um "bum"), e o clique do mecanismo depois.
    rng = np.random.default_rng(7003)
    L, R = camadas(0.8, rng, [
        (300, 3000, 0.000, 0.0008, 0.003, 0.007, -4, 0.0),     # estalo abafado
        (120, 500, 0.002, 0.003, 0.012, 0.030, -2, 0.1),       # soco
        (45, 120, 0.010, 0.020, 0.030, 0.050, -2, 0.0),        # um pouco de grave
        (1200, 6000, 0.004, 0.006, 0.015, 0.045, -15, 0.8),    # ar ("fup")
        (150, 1500, 0.050, 0.050, 0.000, 0.130, -22, 1.0),     # cauda curta
    ], drive=1.8)
    n = len(L)
    tubo = golpe(n, 215, 160, 0.035, 0.060, 0.75, 0.002) + golpe(n, 520, 400, 0.030, 0.030, 0.22, 0.002)
    tubo = tubo + clique(n, rng, 0.150, 1800, 5000, 0.004, 0.06)
    # som_lanca.wav agora vem de gravações CC0 (tools/t19_sons_cc0.py); esta versão sintetizada não é mais gravada


if __name__ == '__main__':
    main()
