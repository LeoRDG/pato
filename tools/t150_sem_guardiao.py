"""Tarefa 150: o guardião (ofanim) deixa de ser obrigatório para chegar em Deus.

- A barreira do Empíreo some sempre (não espera mais guardiao_morto).
- O checkpoint do Empíreo vale sem matar o guardião.
- Começo da luta: chegar na saída basta; não exige mais asas nem guardiao_morto. Se o pato ainda não tem asas, ganha
  na hora (pato.asas e o objeto asas_pato).
O guardião continua lá como luta opcional.
Rodar uma vez:  python3 tools/t150_sem_guardiao.py
"""
from gd_mig import *

ids = Ids('t150')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def sem(conds, *trechos):
    return [c for c in conds if not any(t in tx(c) for t in trechos)]


def migra(d):
    c = cena(d, 'Paraiso')
    guarda = '["guardiao_morto", "True", ""]'
    check = acha(c['events'], 'Checkpoint do Empíreo')
    for e in todos(check['events']):
        a = tx(e.get('actions', []))
        if '"Delete"}, "parameters": ["barreira_empireo"' in a or '"CollisionNP"' in tx(e.get('conditions', [])):
            e['conditions'] = sem(e['conditions'], guarda)
    comeco = next(e for e in acha(c['events'], 'Começo da luta')['events'] if 'deus_criar' in tx(e['actions']))
    comeco['conditions'] = sem(comeco['conditions'], guarda, '"pato", "asas", "True"')
    comeco.setdefault('events', []).append(
        ev([bol('pato', 'asas', False)],
           [setb('pato', 'asas', True), X('Create', '', 'asas_pato', 'pato.X()', 'pato.Y()', '""')]))


if __name__ == '__main__':
    roda(migra, lambda d: '"pato", "asas", "False"' in tx(acha(cena(d, 'Paraiso')['events'], 'Começo da luta')), 't150')
