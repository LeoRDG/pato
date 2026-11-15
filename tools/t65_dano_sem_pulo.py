"""Tarefa 65: o pato não pula sozinho quando leva dano.

Migração de uso único: nos eventos em que o pato perde vida (uma ação "pato.vida -") tira só a ação
SimulateJumpKey do pato; o resto do evento (dano, invencibilidade, empurrão para o lado, etc.) fica como está.
Fica de fora o pulo da lava da fase 2 do chefe (o evento que troca a força do pulo para lava.pulo_vel): é ele que
tira o pato do fundo da lava de volta para as pontes.
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tira_dano(acts):
    return any(a['type']['value'] == 'SetNumberObjectVariable' and a['parameters'][:3] == ['pato', 'vida', '-'] for a in acts)


def pulo(a):
    return a['type']['value'] == 'PlatformBehavior::SimulateJumpKey' and a['parameters'][0] == 'pato'


def pulo_da_lava(acts):
    return any(a['type']['value'] == 'PlatformBehavior::JumpSpeed' and a['parameters'][0] == 'pato' for a in acts)


def eventos_com_pulo_no_dano(evs):
    for e in evs:
        acts = e.get('actions') or []
        if tira_dano(acts) and any(pulo(a) for a in acts) and not pulo_da_lava(acts):
            yield e
        yield from eventos_com_pulo_no_dano(e.get('events') or [])


def folhas(d):
    for x in d['externalEvents']:
        yield x['events']
    for l in d['layouts']:
        yield l['events']


def migra(d):
    for evs in folhas(d):
        for e in eventos_com_pulo_no_dano(evs):
            e['actions'] = [a for a in e['actions'] if not pulo(a)]


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
