"""Tarefa 153: a redoma de invulnerável ganha cor própria.

A arte da redoma passa a ser em tons de cinza (tools/arte_deus.py) e o jogo a tinge com deus.escudo_cor (violeta,
diferente do azul da aura), aplicada no evento que já faz a redoma pulsar.
Só adiciona; se a variável já existe, fica com o valor atual.
Rodar uma vez:  python3 tools/t153_cor_da_redoma.py
"""
from gd_mig import *

ids = Ids('t153')


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o['deus']['variables'], 'deus', [('escudo_cor', '190;130;255')])
    sinal = acha(acha(folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Sinal de vulnerável')
    pulsa = next(e for e in sinal['events']
                 if '"OpacityCapability::OpacityBehavior::SetValue"}, "parameters": ["deus_escudo"' in json.dumps(e['actions']))
    pulsa['actions'].append(X('ChangeColor', 'deus_escudo', 'deus.escudo_cor'))


if __name__ == '__main__':
    roda(migra, lambda d: '"deus_escudo", "deus.escudo_cor"' in json.dumps(acha(folha(d, 'InimigosParaiso')['events'], 'Deus')), 't153')
