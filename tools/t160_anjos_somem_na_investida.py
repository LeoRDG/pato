"""Tarefa 160: na fase final, durante a investida, os anjinhos não ficam presos às bordas da tela.

Presos dentro da tela (t158), enquanto Deus esperava fora dela eles se juntavam na borda do lado dele e entregavam de
onde vinha a investida. Na fase 4, com deus.investindo, um evento logo depois da órbita põe cada um de novo em volta de
Deus sem o clamp, então eles saem da tela com ele (e o laço junto) e voltam com ele. E o ponto sorteado de onde ele
parte (t159) fica mais longe pelo alcance dos anjinhos (canal_orbita_raio + canal_vaivem), senão os que estavam na
ponta da órbita ainda apareciam na beira da tela. No quadro em que ele muda de lugar, cx/cy já vão para o lugar novo
(o Corpo roda antes), para os anjinhos não piscarem no lugar antigo.
Rodar uma vez:  python3 tools/t160_anjos_somem_na_investida.py
"""
from gd_mig import *

d_ = 'deus'
C = 'canalizador'
RAIO = '(deus.canal_orbita_raio + deus.canal_vaivem * (1 + sin(TimeFromStart() * deus.canal_vaivem_vel + canalizador.vaivem_fase)) / 2)'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def solta():
    return ev([bol(C, 'morto', False), num(d_, 'fase', '=', '4'), bol(d_, 'investindo', True)],
              [X('SetXY', C, '=', f'deus.cx + cos(canalizador.ang) * {RAIO} - canalizador.Width() / 2',
                 '=', f'deus.cy + sin(canalizador.ang) * {RAIO} - canalizador.Height() / 2')])


def rosa(d):
    return acha(acha(folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Anel rosa: amor')


def migra(d):
    r = rosa(d)
    k = next(i for i, e in enumerate(r['events']) if '"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']))
    r['events'].insert(k + 1, solta())
    azul = acha(acha(folha(d, 'InimigosParaiso')['events'], 'Deus')['events'], 'Anel azul: investida')
    for e in todos(azul['events']):
        for a in e.get('actions', []):
            if a['parameters'][:3] in (['deus', 'ox', '='], ['deus', 'oy', '=']) and 'deus.investida_longe)' in a['parameters'][3]:
                a['parameters'][3] = a['parameters'][3].replace(
                    'deus.investida_longe)', 'deus.investida_longe + deus.canal_orbita_raio + deus.canal_vaivem)')
        acts = e.get('actions', [])
        if any(a['parameters'][:2] == ['deus', 'investida_pos'] for a in acts):
            acts += [setn('deus', 'cx', '=', 'CameraCenterX("", 0) + deus.ox'),
                     setn('deus', 'cy', '=', 'CameraCenterY("", 0) + deus.oy')]


if __name__ == '__main__':
    roda(migra, lambda d: sum('"SetXY"}, "parameters": ["canalizador"' in tx(e['actions']) for e in rosa(d)['events']) > 1,
         't160')
