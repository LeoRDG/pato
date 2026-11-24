"""Tarefa 165: a lente do buraco negro (BulgePinch, t164) fica só na camada Fundo.

Na camada do jogo (que tem luz 3D) ela entortava os sprites, o pato e o próprio feixe e parecia defeito; no fundo ela
curva só o céu, as estrelas e as nuvens em volta do buraco, que é o efeito de um buraco negro de verdade.
Rodar uma vez:  python3 tools/t165_lente_so_no_fundo.py
"""
from gd_mig import *

LENTE = '"Lente negra"'


def migra(d):
    for l in cena(d, 'Paraiso')['layers']:
        if l['name'] == '':
            l['effects'] = [e for e in l.get('effects', []) if e['name'] != 'Lente negra']
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    for e in todos(deus['events']):
        if 'actions' in e:
            e['actions'] = [a for a in e['actions'] if not (
                a['type']['value'] == 'SetLayerEffectParameter' and a['parameters'][1] == '""' and a['parameters'][2] == LENTE)]


def ja_aplicada(d):
    l = next(x for x in cena(d, 'Paraiso')['layers'] if x['name'] == '')
    return not any(e['name'] == 'Lente negra' for e in l.get('effects', []))


if __name__ == '__main__':
    roda(migra, ja_aplicada, 't165')
