"""Tarefa 163: atalho de teste na luta com Deus. Com deus.teste_c ligado, apertar C tira deus.teste_c_corte (0.25 = 25%)
da vida máxima de Deus. Para desligar, ponha deus.teste_c em falso no GDevelop.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t163_teste_c.py
"""
from gd_mig import *

ids = Ids('t163')
d_ = 'deus'


def migra(d):
    poe_vars(ids, objeto(d, d_)['variables'], d_, [('teste_c', True), ('teste_c_corte', 0.25)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    deus['events'].append(grupo('Teste: C tira vida', [
        ev([X('KeyFromTextJustPressed', '', '"c"'), X('SceneInstancesCount', '', d_, '>', '0'),
            bol(d_, 'teste_c', True), bol(d_, 'morto', False)],
           [setn(d_, 'vida', '-', 'deus.max_vida * deus.teste_c_corte')])]))


if __name__ == '__main__':
    roda(migra, lambda d: acha(acha(folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Teste: C tira vida') is not None,
         't163')
