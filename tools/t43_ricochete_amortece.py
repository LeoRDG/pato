"""Tarefa 43: a granada perde velocidade a cada ricochete.

- Nova variável em cada arma: ricochete_vel = fração da velocidade que a bala mantém depois de quicar
  (lanca 0.6; pistola, doze e minigun 1 = espelho perfeito, como antes). Copiada para projetil.ricochete_vel ao nascer.
- No ricochete, a força (fx, fy) e a gravidade acumulada (gy) são multiplicadas por projetil.ricochete_vel.
Rodar uma vez:  python3 tools/t43_ricochete_amortece.py
"""
import json
from migra import carrega, salva, var, adiciona_var, objeto, externo, A

VALORES = {'pistola': 1, 'doze': 1, 'minigun': 1, 'lanca': 0.6}


def P(nome, op, valor):
    return A('SetNumberObjectVariable', 'projetil', nome, op, valor)


def main():
    d = carrega()
    proj = next(e for e in externo(d, 'Combate')['events'] if e.get('name') == 'Projéteis')['events']
    if 'ricochete_vel' in json.dumps(proj):
        print('já migrado'); return
    for arma, v in VALORES.items():
        adiciona_var(objeto(d, arma)['variables'], var('ricochete_vel', v))
    adiciona_var(objeto(d, 'projetil')['variables'], var('ricochete_vel', 1))

    nasce = next(e for e in proj if e.get('name') == 'Balas (alcance, queda e perfuração)')['events'][1]
    i = next(n for n, a in enumerate(nasce['actions']) if a['parameters'][:2] == ['projetil', 'ricochetes'])
    nasce['actions'].insert(i + 1, P('ricochete_vel', '=', 'Arma.ricochete_vel'))

    ric = next(e for e in proj if e['type'] == 'BuiltinCommonInstructions::ForEach'
               and any(c['parameters'][:3] == ['projetil', 'ricochetes', '>'] for c in e.get('conditions') or []))
    final = ric['events'][-1]['actions']
    j = next(n for n, a in enumerate(final) if a['parameters'][:2] == ['projetil', 'fy'])
    final[j + 1:j + 1] = [P('fx', '*', 'projetil.ricochete_vel'), P('fy', '*', 'projetil.ricochete_vel')]
    k = next(n for n, a in enumerate(final) if a['parameters'][:2] == ['projetil', 'gy'])
    final.insert(k + 1, P('gy', '*', 'projetil.ricochete_vel'))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
