"""Tarefa 184: tira do jogo os recursos (imagens e sons) que nada usa mais: nenhum objeto, cena, evento ou propriedade
cita o nome deles. Os arquivos saem de assets/ no mesmo commit; as fontes que ferramentas e testes ainda leem (tiles 1x,
gravações originais de fontes_cc0) vão para fontes/, que fica só na develop.
Rodar uma vez:  python3 tools/t184_sem_recursos_sem_uso.py
"""
from gd_mig import *


def textos(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from textos(v)
    elif isinstance(x, list):
        for v in x:
            yield from textos(v)


def sem_uso(d):
    texto = '\n'.join(textos({k: v for k, v in d.items() if k != 'resources'}))
    return [r for r in d['resources']['resources'] if r['name'] not in texto]


def migra(d):
    fora = {id(r) for r in sem_uso(d)}
    d['resources']['resources'] = [r for r in d['resources']['resources'] if id(r) not in fora]


if __name__ == '__main__':
    roda(migra, lambda d: not sem_uso(d), 't184')
