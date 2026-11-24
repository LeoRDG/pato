"""Tarefa 168: a lente do buraco negro mais forte (juizo_lente_negra 0.5 -> 1, juizo_lente_raio 260 -> 320).
Com 0.5 quase toda a curva ficava escondida atrás do disco preto. Só troca se ainda estiver no valor que a t164 pôs;
se o usuário já mexeu, fica o dele.
Rodar uma vez:  python3 tools/t168_lente_mais_forte.py
"""
from gd_mig import *

TROCA = {'juizo_lente_negra': (0.5, 1), 'juizo_lente_raio': (260, 320)}
feito = []


def migra(d):
    for v in objeto(d, 'deus')['variables']:
        if v['name'] in TROCA and v['value'] == TROCA[v['name']][0]:
            v['value'] = TROCA[v['name']][1]


if __name__ == '__main__':
    roda(migra, lambda d: False, 't168')
