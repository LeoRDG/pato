"""Tarefa 144: a luz de Deus cresce a cada fase (chefe final, parte 8).

A aura ganha o efeito AdvancedBloom ("Brilho") ao lado dos raios (Godray "Raios"). Quando a fase muda
(deus.fase diferente de deus.luz_fase), os raios (raios_gain_N, raios_luz_N), o bloom (bloom_N) e a cor da
aura (aura_cor_N) passam aos valores da fase N, N de 1 a 4.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t144_luz_e_ajuste.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t144')
d_ = 'deus'


def luz_por_fase():
    evs = []
    for k in (1, 2, 3, 4):
        evs.append(ev([bol(d_, 'morto', False), num(d_, 'fase', '=', str(k)), num(d_, 'luz_fase', '!=', str(k))],
                      [setn(d_, 'luz_fase', '=', str(k)),
                       luz.acao_param_efeito_obj('deus_aura', 'Raios', 'gain', f'deus.raios_gain_{k}'),
                       luz.acao_param_efeito_obj('deus_aura', 'Raios', 'light', f'deus.raios_luz_{k}'),
                       luz.acao_param_efeito_obj('deus_aura', 'Brilho', 'bloomScale', f'deus.bloom_{k}'),
                       X('ChangeColor', 'deus_aura', f'deus.aura_cor_{k}')]))
    return grupo('Luz por fase', evs)


def migra(d):
    o = {x['name']: x for x in d['objects']}
    aura = o['deus_aura']
    if not any(e['effectType'] == 'AdvancedBloom' for e in aura['effects']):
        aura['effects'].append(efeito('AdvancedBloom', 'Brilho',
                                      {'threshold': 0.4, 'bloomScale': 1, 'brightness': 1, 'blur': 6, 'quality': 6,
                                       'padding': 0}))
    poe_vars(ids, o[d_]['variables'], d_, [
        ('luz_fase', 0),
        ('raios_gain_1', 0.45), ('raios_gain_2', 0.55), ('raios_gain_3', 0.65), ('raios_gain_4', 0.8),
        ('raios_luz_1', 30), ('raios_luz_2', 35), ('raios_luz_3', 40), ('raios_luz_4', 50),
        ('bloom_1', 1), ('bloom_2', 1.3), ('bloom_3', 1.6), ('bloom_4', 2.1),
        ('aura_cor_1', '255;255;255'), ('aura_cor_2', '255;240;200'), ('aura_cor_3', '255;215;235'),
        ('aura_cor_4', '255;190;160')])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Fases')
    deus['events'].insert(k + 1, luz_por_fase())


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Luz por fase') is not None, 't144')
