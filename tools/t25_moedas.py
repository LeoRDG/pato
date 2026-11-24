"""Tarefa 25: pegar várias moedas no mesmo quadro soma todas.

O evento de coleta pegava todas as moedas encostando no pato, mas `moeda.valor` numa expressão só lê a PRIMEIRA delas:
somava o valor de uma e apagava todas. Agora o evento é um "Para cada moeda" (as condições valem para cada uma),
então cada moeda soma o seu valor e mostra o seu +N.
Rodar:  python3 tools/t25_moedas.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import PATH


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    comb = next(x for x in d['externalEvents'] if x['name'] == 'Combate')['events']

    def anda(evs):
        for e in evs:
            yield e
            yield from anda(e.get('events') or [])
    n = 0
    for e in anda(comb):
        if any(c['type']['value'] == 'CollisionNP' and c['parameters'][:2] == ['moeda', 'pato'] for c in e.get('conditions') or []) \
                and any(a['type']['value'] == 'Delete' and a['parameters'][0] == 'moeda' for a in e.get('actions') or []):
            e['type'], e['object'] = 'BuiltinCommonInstructions::ForEach', 'moeda'
            e.setdefault('events', [])
            n += 1
    assert n == 1, n
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
