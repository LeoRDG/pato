import json, os, re, wave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
FONTES = os.path.join(RAIZ, 'assets', 'fontes_cc0')
REG = json.load(open(os.path.join(FONTES, 'fontes.json'), encoding='utf-8'))
TXT = open(os.path.join(FONTES, 'FONTES.txt'), encoding='utf-8').read()


def tocados():
    out = set()
    def walk(evs):
        for e in evs:
            for a in e.get('actions', []):
                if 'Sound' in a['type']['value']:
                    out.update(p for p in a['parameters'] if isinstance(p, str) and p.endswith('.wav'))
            walk(e.get('events') or [])
    for x in JOGO['externalEvents']:
        walk(x['events'])
    return out


def test_toda_fonte_registrada_e_cc0():
    arquivos = {f for f in os.listdir(FONTES) if f.endswith('.wav')}
    assert set(REG) <= arquivos
    for nome, i in REG.items():
        assert i['licenca'] == 'Creative Commons 0' and i['url'].startswith('https://freesound.org/people/')
        assert nome in TXT   # aparece no registro legível
    for f in arquivos:
        sid = re.search(r'_(\d+)\.wav$', f)[1]
        assert f in REG or f'/sounds/{sid}/' in TXT, f   # nenhuma gravação sem registro (as antigas, à mão, pelo id)


def test_sons_novos_existem_tem_receita_e_nada_provisorio():
    sons = tocados()
    assert 'test.wav' not in sons and 'hit.wav' not in sons
    res = {r['name'] for r in JOGO['resources']['resources'] if r['kind'] == 'audio'}
    for s in sons:
        assert s in res and os.path.exists(os.path.join(RAIZ, 'assets', s)), s
    receitas = set(re.findall(r'^(som_[a-z_]+\.wav) \(', TXT, re.M))
    for s in ('som_pulo.wav', 'som_pulo_ar.wav', 'som_dash.wav', 'som_pouso.wav', 'som_pato_dano.wav', 'som_pato_morte.wav',
              'som_moeda.wav', 'som_acerto.wav', 'som_inimigo_morte.wav', 'som_troca_arma.wav'):
        assert s in sons and s in receitas, s
        with wave.open(os.path.join(RAIZ, 'assets', s)) as w:
            assert w.getframerate() == 44100 and 0.1 < w.getnframes() / 44100 < 2
