"""Tarefa 180: brasas azuis onde o fundo é azul.
- Hub: hub_brasas passa a azul (o fundo do hub é azul-escuro).
- Inferno: subindo, o fundo vira o céu azul da noite (fundo_mistura, t54). As cores das brasas (inferno_brasas)
  seguem a mesma mistura: de brasas_cor1/2 (laranja) para brasas_noite_cor1/2 (azul), variáveis da cena.
Só adiciona variáveis que não existem; a cor do hub só muda se ainda for a da t175.
Rodar uma vez:  python3 tools/t180_brasas_azuis.py
"""
from gd_mig import *

ids = Ids('t180')
HUB_AZUL = {'1': (170, 210, 255), '2': (60, 110, 220)}
CORES = {'1': ((255, 220, 120), (170, 210, 255)), '2': ((230, 70, 20), (60, 110, 220))}


def cor(o, k, rgb):
    o['particleColor' + k] = ';'.join(map(str, rgb))
    o['particleRed' + k], o['particleGreen' + k], o['particleBlue' + k] = rgb


def migra(d):
    h = objeto(d, 'hub_brasas')
    if (h['particleColor1'], h['particleColor2']) == ('255;200;90', '220;60;20'):
        for k, rgb in HUB_AZUL.items():
            cor(h, k, rgb)
    sc = cena(d, 'Inferno')
    pares = []
    for k, (dia, noite) in CORES.items():
        for c, a, b in zip('rgb', dia, noite):
            pares += [(f'brasas_cor{k}_{c}', a), (f'brasas_noite_cor{k}_{c}', b)]
    poe_vars(ids, sc['variables'], 'Inferno', pares)
    acoes = []
    for k in CORES:
        partes = ' + ";" + '.join(f'ToString(round(lerp(brasas_cor{k}_{c}, brasas_noite_cor{k}_{c}, fundo_mistura)))'
                                  for c in 'rgb')
        acoes.append(X(f'ParticleSystem::ParticleColor{k}', 'inferno_brasas', partes))
    acha(sc['events'], 'Brasas no ar')['events'].append(ev([], acoes))


if __name__ == '__main__':
    roda(migra, lambda d: 'brasas_noite_cor1_b' in json.dumps(cena(d, 'Inferno')['variables']), 't180')
