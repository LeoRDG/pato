"""Tarefa 161: o Juízo (anel rosa) tirava deus.juizo_dano = 85, quase a vida toda; passa a 40, ainda o golpe mais forte
da luta (o pulso e a investida tiram 30). Só muda se ainda estiver no valor inicial 85.
Rodar uma vez:  python3 tools/t161_juizo_mais_leve.py
"""
from gd_mig import *


def migra(d):
    for v in objeto(d, 'deus')['variables']:
        if v['name'] == 'juizo_dano' and v.get('value') == 85:
            v['value'] = 40


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'juizo_dano' and v.get('value') != 85 for v in objeto(d, 'deus')['variables']),
         't161')
