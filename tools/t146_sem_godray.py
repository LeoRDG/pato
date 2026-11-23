"""Tarefa 146: tira o Godray da aura de Deus (correção visual).

O filtro Godray soma a névoa dele em TODO o retângulo do objeto onde está, inclusive na parte transparente
(texture + mist). Na aura (780 px, mais o espaço do bloom) isso virou uma caixa escura com raios em volta do olho.
Sai o efeito "Raios" da aura e as ações por fase que o ajustavam; o bloom ("Brilho") e a cor por fase ficam.
As variáveis raios_gain_N / raios_luz_N só saem se ainda estiverem no valor inicial (se você mudou, ficam).
Rodar uma vez:  python3 tools/t146_sem_godray.py
"""
from gd_mig import *

PADRAO = {'raios_gain_1': 0.45, 'raios_gain_2': 0.55, 'raios_gain_3': 0.65, 'raios_gain_4': 0.8,
          'raios_luz_1': 30, 'raios_luz_2': 35, 'raios_luz_3': 40, 'raios_luz_4': 50}


def migra(d):
    o = {x['name']: x for x in d['objects']}
    aura = o['deus_aura']
    aura['effects'] = [e for e in aura['effects'] if e['effectType'] != 'Godray']
    vs = o['deus']['variables']
    vs[:] = [v for v in vs if not (v['name'] in PADRAO and v.get('value') == PADRAO[v['name']])]
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    for e in todos(acha(deus['events'], 'Luz por fase')['events']):
        e['actions'] = [a for a in e.get('actions', []) if 'Raios' not in a['parameters'][:3]]


if __name__ == '__main__':
    roda(migra, lambda d: not any(e['effectType'] == 'Godray' for e in objeto(d, 'deus_aura')['effects']), 't146')
