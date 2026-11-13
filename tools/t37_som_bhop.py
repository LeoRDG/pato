"""Tarefa 37: som bem discreto quando o bunny hop encadeia.

- assets/som_bhop.wav é sintetizado aqui (som original, sem gravação): um "pip" arredondado e curto (seno com leve subida de tom,
  um pouco de oitava) com um sopro de ar filtrado bem baixo por baixo. Só é criado se ainda não existe.
- Toca a cada degrau da série (bhop_serie sobe), no volume pato.bhop_som_volume, com tom
  pato.bhop_som_tom * pato.bhop_som_passo ^ (bhop_serie - 1): cada pulo encadeado sobe um tom inteiro (escadinha).
- O recurso é pré-carregado com os outros sons no início da cena (sem atraso no primeiro toque).
Só ADICIONA: arquivo, recurso, variáveis, pré-carga e som são criados só se faltarem; valores existentes são mantidos.
Rodar:  python3 tools/t37_som_bhop.py   (uma vez). Feche o projeto no GDevelop antes.
"""
import json, os, uuid, wave
import numpy as np
from t12_armas import A, PATH

NOME = 'som_bhop.wav'
ARQ = os.path.join(os.path.dirname(PATH), 'assets', NOME)
SR = 44100

VARS = [
    ('bhop_som_volume', 18),       # bem abaixo do pulo (40)
    ('bhop_som_tom', 1),           # tom do primeiro degrau
    ('bhop_som_passo', 1.1225),    # multiplicador por degrau (1.1225 = um tom inteiro)
]
TOM = 'pato.bhop_som_tom * pow(pato.bhop_som_passo, pato.bhop_serie - 1)'


def sintetiza():
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    f = 740 * (1 + 0.04 * (1 - np.exp(-t / 0.012)))           # sobe 4% nos primeiros ms: soa "positivo"
    fase = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.045)        # ataque de 2 ms, cai em ~0.1 s
    pip = (np.sin(fase) + 0.22 * np.sin(2 * fase)) * env
    rng = np.random.default_rng(36)
    ar = np.convolve(rng.standard_normal(n), np.ones(24) / 24, mode='same')   # ruído abafado
    ar *= (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.03) * 0.25
    x = pip + ar
    x[-int(SR * 0.01):] *= np.linspace(1, 0, int(SR * 0.01))   # sem clique no fim
    x = x / np.max(np.abs(x)) * 0.7
    with wave.open(ARQ, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def main():
    if not os.path.exists(ARQ):
        sintetiza()
    d = json.load(open(PATH, encoding='utf-8'))

    res = d['resources']['resources']
    if not any(r['name'] == NOME for r in res):
        res.append({'file': f'assets/{NOME}', 'kind': 'audio', 'metadata': '', 'name': NOME, 'preloadAsMusic': False,
                    'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True})

    pato = next(o for o in d['objects'] if o['name'] == 'pato')
    tem = {v['name'] for v in pato['variables']}
    for nome, valor in VARS:
        if nome not in tem:
            pato['variables'].append({'name': nome, 'persistentUuid': str(uuid.uuid4()), 'type': 'number', 'value': valor})

    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    todos = list(walk(jog['events']))
    if not any(a['type']['value'] == 'PreloadSound' and a['parameters'][1] == NOME for e in todos for a in e.get('actions', [])):
        pre = next(e for e in todos if any(a['type']['value'] == 'PreloadSound' for a in e.get('actions', [])))
        pre['actions'].append(A('PreloadSound', '', NOME))

    bh = next(e for e in todos if e.get('name') == 'Bunny hop')
    sobe = next(e for e in walk(bh['events']) if any(
        a['type']['value'] == 'SetNumberObjectVariable' and a['parameters'][:2] == ['pato', 'bhop_serie'] and '+ 1' in a['parameters'][3]
        for a in e.get('actions', [])))
    if not any(a['type']['value'] == 'PlaySound' and a['parameters'][1] == NOME for a in sobe['actions']):
        sobe['actions'].append(A('PlaySound', '', NOME, '', 'pato.bhop_som_volume', TOM))

    for e in walk(bh['events']):
        if e['type'] == 'BuiltinCommonInstructions::Comment' and 'som_bhop' not in e['comment']:
            e['comment'] += (' Cada degrau toca som_bhop bem baixo (bhop_som_volume), um tom acima do anterior '
                             '(bhop_som_tom × bhop_som_passo por degrau).')

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
