"""Tarefa 19: sons da lança-granadas e da minigun a partir de gravações reais de domínio público (CC0), em vez de síntese pura.

Fontes em assets/fontes_cc0/ (lista com endereço e licença em FONTES.txt). As gravações são curtas, mono e sem grave; por cima
entram as camadas da receita de t17 (`camadas`): grave que cresce depois do estalo, ar e cauda em estéreo.
  - som_lanca.wav  : disparo com o "tunc" de tubo bem marcado (base) + um M203 real (corpo e médios);
  - som_minigun.wav: um tiro de fuzil limpo (Lee-Enfield .303) encurtado + soco e grave densos em camadas; curto e quase mono,
                     para a rajada do jogo não embolar.
  - som_explosao.wav: explosão de granada feita para jogos + dinamite real, com a onda de grave atrasada por cima;
  - som_doze_pump.wav: bombeada real de uma Mossberg 590A1, com realce de presença;
  - som_recarga_<arma>.wav: recargas montadas com estalos recortados de gravações reais (rec_*.wav);
  - som_minigun_giro.wav: laço do giro dos canos, a partir de um motor elétrico real.
Volume no mesmo nível das outras armas.   Rodar:  python3 tools/t19_sons_cc0.py   (pode rodar de novo; não mexe no jogo.json)
t17_sons_armas.py não grava mais estes arquivos.
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


def le_estereo(nome):
    w = wave.open(os.path.join(ROOT, 'assets', 'fontes_cc0', nome))
    assert w.getframerate() == SR and w.getnchannels() == 2
    x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').reshape(-1, 2).astype(float) / 32768
    ini = np.argmax(np.abs(x).max(1) > 0.1 * np.abs(x).max())
    x = x[max(ini - 30, 0):]
    return x / np.abs(x).max()


def explosao():
    """Base: uma explosão de granada feita para jogos (estalo forte, corpo cheio, estéreo) + uma explosão de dinamite real (o estrondo
    e o eco de verdade). Por cima, só o que falta nas duas: a onda de grave que chega atrasada (o "BUM" depois do estalo), ar nos agudos e destroços.
    Um limitador no fim deixa o som denso (as gravações têm o estalo muito acima do resto)."""
    dur = 1.6
    n = int(SR * dur)
    t = np.arange(n) / SR
    encaixa = lambda x: np.vstack([x, np.zeros((max(0, n - len(x)), 2))])[:n]
    granada = encaixa(le_estereo('explosao_609587.wav'))
    dinamite = encaixa(le_estereo('explosao_251401.wav'))
    dinamite *= np.exp(-np.maximum(t - 0.12, 0) / 0.10)[:, None]      # só o estouro: o resto dela é eco de montanha
    real = granada + 0.7 * dinamite
    real = real / np.abs(real).max()

    rng = np.random.default_rng(7022)
    L, R = camadas(dur, rng, [
        (22, 70, 0.040, 0.045, 0.110, 0.220, 0, 0.0),         # onda de grave atrasada
        (60, 220, 0.045, 0.050, 0.080, 0.200, -8, 0.2),
        (2500, 12000, 0.000, 0.002, 0.060, 0.160, -9, 0.9),   # ar: as gravações têm pouco agudo (ficava abafado)
        (1500, 9000, 0.150, 0.100, 0.150, 0.250, -18, 1.0, 18),   # destroços estalando na cauda
    ], drive=1.6)
    k = 0.55 / max(np.abs(L).max(), np.abs(R).max())
    env = np.exp(-np.maximum(t - 0.35, 0) / 0.22)              # corta o eco das gravações: explosão seca, sem sala
    L, R = (np.tanh(2.2 * (real[:, c] * env + k * v)) for c, v in ((0, L), (1, R)))
    grava(L, R, 'som_explosao.wav', fade=0.4, pico=0.55)


def pump():
    """Bombeada da doze: gravação real de uma Mossberg 590A1 sendo bombeada ("chk... chk": ferrolho para trás e para frente,
    dois estalos metálicos secos). Sem camada grave por baixo (isso fazia soar como coisa caindo no chão) e sem eco:
    só um realce de presença (1,5-6 kHz) e um limitador leve para o som ficar forte sem perder o estalo."""
    x = le('pump_351226.wav')
    n = len(x)
    t = np.arange(n) / SR
    x = x * np.where(t < 0.55, 1, np.exp(-(t - 0.55) / 0.08))           # corta o resto depois do segundo estalo
    x = passa(x, 150, None, 2)
    x = x + 0.6 * passa(x, 1500, 6000, 2)                               # presença: metal
    x = np.tanh(1.8 * x / np.abs(x).max())
    grava(x, x, 'som_doze_pump.wav', fade=0.1, pico=0.75)


def montagem(dur, pecas, nome, pico=0.6):
    """Recarga montada com estalos recortados de gravações reais (assets/fontes_cc0/rec_*.wav).
    pecas: (arquivo ou array, início em s, ganho, velocidade). velocidade < 1 = mais lento e mais grave (peça mais pesada).
    Sem eco; limitador leve; volume abaixo dos tiros."""
    n = int(SR * dur)
    x = np.zeros(n)
    for fonte, t0, g, vel in pecas:
        y = le(fonte) if isinstance(fonte, str) else fonte
        if vel != 1:
            y = np.interp(np.arange(0, len(y) - 1, vel), np.arange(len(y)), y)
        i = int(t0 * SR)
        y = y[:n - i]
        x[i:i + len(y)] += g * y
    x = passa(x, 120, None, 2)
    x = np.tanh(1.5 * x / np.abs(x).max())
    grava(x, x, nome, fade=0.05, pico=pico)


def recargas():
    """Uma recarga por arma, com a duração da recarga de cada uma (pistola 1 s, doze 2,2 s, minigun 2,5 s, lança 2,4 s;
    o jogo acelera o som quando um upgrade encurta a recarga)."""
    montagem(1.0, [('rec_pistola_pente_sai_276959.wav', 0.02, 0.8, 1),
                   ('rec_pistola_pente_entra_276959.wav', 0.36, 1.0, 1),
                   ('rec_pistola_ferrolho_tras_276959.wav', 0.66, 0.8, 1),
                   ('rec_pistola_ferrolho_frente_276959.wav', 0.80, 1.0, 1)], 'som_recarga_pistola.wav')
    bomba = le('pump_351226.wav')
    montagem(2.2, [('rec_cartucho_379976.wav', 0.10, 0.9, 0.95),
                   ('rec_cartucho_379976.wav', 0.42, 0.8, 1.03),
                   ('rec_cartucho_379976.wav', 0.74, 0.9, 0.98),
                   ('rec_cartucho_379976.wav', 1.06, 0.8, 1.02),
                   (bomba, 1.36, 1.0, 1)], 'som_recarga_doze.wav')
    montagem(2.5, [('rec_minigun_caixa_sai_422688.wav', 0.05, 1.0, 0.8),
                   ('rec_minigun_caixa_entra_422688.wav', 0.95, 1.0, 0.8),
                   ('rec_minigun_ferrolho_tras_766165.wav', 1.70, 0.9, 0.85),
                   ('rec_minigun_ferrolho_frente_766165.wav', 2.05, 1.0, 0.85)], 'som_recarga_minigun.wav')
    montagem(2.4, [('rec_lanca_abre_52202.wav', 0.10, 1.0, 0.9),
                   ('rec_cartucho_379976.wav', 0.95, 1.0, 0.75),
                   ('rec_lanca_fecha_52202.wav', 1.85, 1.0, 0.9)], 'som_recarga_lanca.wav')


if __name__ == '__main__':
    lanca()
    minigun()
    giro()
    explosao()
    pump()
    recargas()
