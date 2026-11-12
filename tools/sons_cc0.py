"""Ferramentas para os sons CC0 do jogo: baixar do Freesound (conferindo a licença), recortar/editar e registrar as fontes.

Cada gravação baixada fica em assets/fontes_cc0/<apelido>_<id>.wav (mono, 44,1 kHz, prévia mp3 de alta qualidade do Freesound
convertida com o ffmpeg). Antes de baixar, a página do som é lida e a licença tem que ser Creative Commons 0; senão o script para.
O registro legível (autor, título, endereço, licença, que trecho foi usado) fica em assets/fontes_cc0/FONTES.txt, numa seção gerada
entre marcadores; o registro completo (para scripts) fica em assets/fontes_cc0/fontes.json.
"""
import json, os, re, subprocess, time, urllib.request, wave
import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTES = os.path.join(ROOT, 'assets', 'fontes_cc0')
UA = {'User-Agent': 'Mozilla/5.0 (jogo do pato; sons CC0)'}
CC0 = 'Creative Commons 0'


def _get(url, tentativas=5):
    for k in range(tentativas):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except (urllib.error.URLError, TimeoutError) as e:
            if k == tentativas - 1 or (isinstance(e, urllib.error.HTTPError) and e.code not in (429, 500, 502, 503, 504)):
                raise
            time.sleep(15 * (k + 1))   # o Freesound limita pedidos seguidos e às vezes demora


def info(sid):
    """Lê a página do som: autor, título, licença e a prévia mp3 (alta qualidade)."""
    html = _get(f'https://freesound.org/s/{sid}/').decode()
    lic = re.search(r'creativecommons\.org/(publicdomain/zero|licenses/[a-z-]+)/[0-9.]+', html)
    import html as h
    autor = re.search(rf'/people/([^/"]+)/sounds/{sid}/', html)[1]
    mp3 = re.search(rf'data-mp3="([^"]*/{sid}_[^"]*)"', html)[1]
    titulo = h.unescape(re.search(r'data-title="([^"]*)"', html[html.index(mp3):])[1])
    return {'id': sid, 'autor': autor, 'titulo': titulo,
            'licenca': CC0 if lic and lic[1] == 'publicdomain/zero' else (lic[0] if lic else '?'),
            'url': f'https://freesound.org/people/{autor}/sounds/{sid}/', 'mp3': mp3.replace('-lq.mp3', '-hq.mp3')}


def baixa(apelido, sid, registro):
    """Baixa (se ainda não tem) e devolve o nome do wav. Para com erro se a licença não for CC0."""
    nome = f'{apelido}_{sid}.wav'
    caminho = os.path.join(FONTES, nome)
    if nome in registro and os.path.exists(caminho):
        return nome
    i = info(sid)
    if i['licenca'] != CC0:
        raise SystemExit(f'{sid} ({i["titulo"]}) não é CC0: {i["licenca"]}')
    tmp = caminho + '.mp3'
    with open(tmp, 'wb') as f:
        f.write(_get(i['mp3']))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tmp, '-ac', '1', '-ar', str(SR), '-sample_fmt', 's16', caminho], check=True)
    os.remove(tmp)
    i['baixado'] = time.strftime('%Y-%m-%d')
    registro[nome] = i
    time.sleep(2)
    return nome


def le(nome):
    with wave.open(os.path.join(FONTES, nome)) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768


def corta(x, ini=0.0, dur=None, auto=True, limiar=0.08):
    """Trecho a partir de ini s (com auto, começa onde o som passa de limiar do pico, 5 ms antes)."""
    x = x[int(ini * SR):]
    if auto and np.abs(x).max() > 0:
        x = x[max(0, int(np.argmax(np.abs(x) > limiar * np.abs(x).max())) - int(0.005 * SR)):]
    if dur:
        x = x[:int(dur * SR)]
    return x


def filtro(x, lo=None, hi=None, ordem=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    h = np.ones_like(f)
    if lo:
        h *= 1 - 1 / np.sqrt(1 + (f / lo) ** (2 * ordem) + 1e-30)
    if hi:
        h *= 1 / np.sqrt(1 + (f / hi) ** (2 * ordem))
    return np.fft.irfft(X * h, len(x))


def tom(x, fator):
    """Muda o tom (e a duração) por reamostragem: fator 2 = uma oitava acima e metade da duração."""
    if fator == 1:
        return x
    n = int(len(x) / fator)
    return np.interp(np.arange(n) * fator, np.arange(len(x)), x)


def mixa(*partes):
    """Soma trechos (x, atraso_s, ganho) alinhados pelo início."""
    n = max(int(a * SR) + len(x) for x, a, g in partes)
    out = np.zeros(n)
    for x, a, g in partes:
        i = int(a * SR)
        out[i:i + len(x)] += g * x
    return out


def grava(x, nome, fade_in=0.003, fade_out=0.05, pico=0.7, satura=0.0):
    """Normaliza pelo pico, fade nas pontas, saturação leve opcional (tanh) e grava assets/<nome> mono 16 bits."""
    x = filtro(x, 25, None, 2)
    n = len(x)
    g = np.minimum(1, np.minimum(np.arange(n) / max(1, SR * fade_in), (n - np.arange(n)) / max(1, SR * fade_out)))
    x = x * g / (np.abs(x).max() + 1e-12)
    if satura:
        x = np.tanh(x * (1 + satura)) / np.tanh(1 + satura)
    pcm = (x / (np.abs(x).max() + 1e-12) * pico * 32767).astype('<i2')
    with wave.open(os.path.join(ROOT, 'assets', nome), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def carrega_registro():
    p = os.path.join(FONTES, 'fontes.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def salva_registro(registro, usos, titulo):
    """Grava fontes.json e reescreve a seção gerada do FONTES.txt (entre marcadores), sem mexer no resto do arquivo.
    usos: lista de (som_final, descrição, [(arquivo_fonte, trecho_usado), ...])."""
    with open(os.path.join(FONTES, 'fontes.json'), 'w', encoding='utf-8') as f:
        json.dump(registro, f, indent=2, ensure_ascii=False, sort_keys=True)
    ini, fim = f'--- início: {titulo} (gerado, não editar à mão) ---', f'--- fim: {titulo} ---'
    linhas = [ini, '']
    for som, desc, fontes in usos:
        linhas.append(f'{som} ({desc})')
        for arq, trecho in fontes:
            i = registro[arq]
            linhas.append(f'  {arq:<34} "{i["titulo"]}" por {i["autor"]} ({trecho})')
            linhas.append(f'  {"":<34} {i["url"]}   [{i["licenca"]}, baixado em {i["baixado"]}]')
        linhas.append('')
    linhas.append(fim)
    p = os.path.join(FONTES, 'FONTES.txt')
    txt = open(p, encoding='utf-8').read()
    bloco = '\n'.join(linhas)
    if ini in txt:
        txt = txt[:txt.index(ini)] + bloco + txt[txt.index(fim) + len(fim):]
    else:
        txt = txt.rstrip('\n') + '\n\n' + bloco + '\n'
    open(p, 'w', encoding='utf-8').write(txt)
