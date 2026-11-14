"""Migração única: organiza os eventos de dentro do grupo "Sensação do pato" em subgrupos.

A ordem dos eventos não muda (só ganham um grupo em volta), então o jogo roda igual:
  Buffer de pulo            -> arma o buffer, expira, pula ao pousar
  Pulo curto e queda pesada -> corta o pulo ao soltar, gravidade extra, guarda queda_vy
  Poeira e pouso            -> poeira do pulo, som/poeira do pouso, poeira do dash
Comentários soltos ficam no topo do grupo. Não rode de novo.
Uso: python3 tools/t29_organiza_sensacao_pato.py [arquivo]  (padrão jogo.json)
"""
import json
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'jogo.json'


def carrega():
    s = open(PATH, encoding='utf-8').read()
    return json.loads(s, parse_float=lambda t: '\x00F' + t + '\x00')


def salva(d):
    o = json.dumps(d, indent=2, ensure_ascii=False)
    o = re.sub(r'"\\u0000F(.*?)\\u0000"', r'\1', o)
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(o + '\n')


def acha_grupo(evs, nome):
    for e in evs:
        if e.get('type') == 'BuiltinCommonInstructions::Group' and e.get('name') == nome:
            return e
        r = acha_grupo(e.get('events', []), nome)
        if r:
            return r


def cita(x, *nomes):
    s = json.dumps(x, ensure_ascii=False)
    return any(n in s for n in nomes)


def tipo(e):
    s = json.dumps(e.get('conditions', []) + e.get('actions', []), ensure_ascii=False)
    if '"bufpulo"' in s or 'buf_ativo' in s:
        return 'Buffer de pulo'
    if 'pulo_corte' in s or 'dash_gravidade' in s or ('queda_vy' in s and 'poeira' not in s):
        return 'Pulo curto e queda pesada'
    if 'poeira' in s or cita(e.get('events', []), 'poeira'):
        return 'Poeira e pouso'
    raise SystemExit('evento não reconhecido: ' + s[:200])


def main():
    d = carrega()
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    g = acha_grupo(jog['events'], 'Sensação do pato')
    assert g, 'grupo não encontrado'
    if any(e['type'].endswith('Group') for e in g['events']):
        raise SystemExit('o grupo já tem subgrupos; nada a fazer')

    soltos, ordem, grupos = [], [], {}
    for e in g['events']:
        if e['type'] == 'BuiltinCommonInstructions::Comment':
            soltos.append(e)
            continue
        t = tipo(e)
        if t not in grupos:
            ordem.append(t)
            grupos[t] = []
        grupos[t].append(e)

    # A ordem original tem que continuar a mesma depois de juntar.
    plano = [e for t in ordem for e in grupos[t]]
    original = [e for e in g['events'] if e['type'] != 'BuiltinCommonInstructions::Comment']
    assert [id(e) for e in plano] == [id(e) for e in original], 'juntar mudaria a ordem'

    novo = list(soltos)
    for t in ordem:
        novo.append({
            'colorB': g.get('colorB', 228), 'colorG': g.get('colorG', 176), 'colorR': g.get('colorR', 74),
            'creationTime': 0, 'name': t, 'source': '',
            'type': 'BuiltinCommonInstructions::Group',
            'events': grupos[t], 'parameters': [],
        })
    g['events'] = novo
    salva(d)
    print('ok:', {t: len(grupos[t]) for t in ordem})


if __name__ == '__main__':
    main()
