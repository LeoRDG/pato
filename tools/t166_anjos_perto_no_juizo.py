"""Tarefa 166: no Juízo os anjinhos param o vai e vem e ficam perto de Deus, só girando em volta dele.

deus.canal_vaivem_k multiplica o vai e vem (canal_vaivem) das órbitas: desce a 0 em canal_vaivem_recolhe segundos
enquanto juizo_ativo e volta a 1 depois, para eles não pularem de lugar.
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t166_anjos_perto_no_juizo.py
"""
from gd_mig import *

ids = Ids('t166')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    poe_vars(ids, objeto(d, 'deus')['variables'], 'deus', [('canal_vaivem_k', 1), ('canal_vaivem_recolhe', 0.6)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    rosa = acha(deus['events'], 'Anel rosa: amor')['events']
    orbita = [e for e in rosa if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions'])]
    for e in orbita:
        for a in e['actions']:
            if a['type']['value'] == 'SetXY':
                a['parameters'] = [p.replace('deus.canal_vaivem * (1', 'deus.canal_vaivem * deus.canal_vaivem_k * (1')
                                   for p in a['parameters']]
    k = rosa.index(orbita[0])
    rosa[k:k] = [
        ev([X('SceneInstancesCount', '', 'deus', '>', '0'), bol('deus', 'juizo_ativo', True)],
           [setn('deus', 'canal_vaivem_k', '=', 'max(0, deus.canal_vaivem_k - TimeDelta() / deus.canal_vaivem_recolhe)')]),
        ev([X('SceneInstancesCount', '', 'deus', '>', '0'), bol('deus', 'juizo_ativo', False)],
           [setn('deus', 'canal_vaivem_k', '=', 'min(1, deus.canal_vaivem_k + TimeDelta() / deus.canal_vaivem_recolhe)')]),
    ]


if __name__ == '__main__':
    roda(migra, lambda d: 'canal_vaivem_k' in tx(objeto(d, 'deus')['variables']), 't166')
