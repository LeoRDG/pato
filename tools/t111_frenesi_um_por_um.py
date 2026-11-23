"""Tarefa 111: o frenesi do condenado em chamas vale só para quem perdeu a vida.

A condição do frenesi era "comparar dois números" (condenado_em_chamas.vida < max_vida * frenesi_abaixo), que não
filtra instâncias e lê só o primeiro condenado da lista: quando um ficava abaixo da metade, todos os vivos sem
frenesi entravam em frenesi juntos. Os sorteios do frenesi (troca de lado, ir na direção do pato, pular) também
valiam igual para todos. Os eventos do grupo "Condenado em chamas (frenesi)" passam, iguais, para dentro de um
"para cada condenado_em_chamas": cada um decide sozinho.
Rodar uma vez:  python3 tools/t111_frenesi_um_por_um.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 'condenado_em_chamas'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    g = next(e for e in todos(ini) if e.get('name') == 'Condenado em chamas (frenesi)')
    if any(e['type'].endswith('ForEach') and e.get('object') == C for e in g['events']):
        sys.exit('t111 já foi aplicada; não roda de novo.')
    comentarios = [e for e in g['events'] if e['type'].endswith('Comment')]
    resto = [e for e in g['events'] if not e['type'].endswith('Comment')]
    assert len(resto) == 3, [e['type'] for e in g['events']]
    g['events'] = comentarios + [{'type': 'BuiltinCommonInstructions::ForEach', 'object': C, 'conditions': [],
                                  'actions': [], 'events': resto}]
    if comentarios:
        comentarios[-1]['comment'] += ' Cada condenado decide sozinho (para cada).'

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('frenesi um por um')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
