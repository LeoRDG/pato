"""Tarefa 191: sons do pato menos irritantes.
- som_pulo.wav: o "bwoop" sintético (tom fixo a 1,7 kHz, tocava a cada pulo) vira um "fwip" de roupa curto e macio
  (gravação CC0 de roupa arrastada, sem tom). Volume em pato.pulo_som_volume (antes 40 fixo) e variação de tom
  em pato.pulo_som_variacao.
- som_pulo_ar.wav: o pulo no ar vira uma batida de asas de verdade (gravação CC0, as duas batidas); volume em
  pato.pulo_ar_som_volume (antes 45 fixo).
- Pouso: pulinhos quase não fazem som, quedas grandes continuam fortes: pato.pouso_som_min + pato.pouso_som_extra * queda
  (antes 35 + 45 * queda).
- Moedas: pegar várias no mesmo quadro tocava um som por moeda (somavam e estouravam). Agora toca um só por quadro,
  e o tom sobe em sequência enquanto o pato vai pegando moedas (moeda_combo, até moeda_combo_max passos de
  moeda_som_passo; zera depois de moeda_combo_janela s sem pegar). Volume em moeda_som_volume (antes 25 fixo).
Rodar uma vez:  python3 tools/t191_sons_pato.py
"""
import json
from gd_mig import *
from sons_cc0 import baixa, carrega_registro, corta, filtro, grava, le, mixa, salva_registro, tom

FONTES = dict(asa=389634, roupa=496188, roupa2=494797)


def faz_sons():
    reg = carrega_registro()
    f = {k: le(baixa(k, v, reg)) for k, v in FONTES.items()}
    # pulo: o começo do arrasto de roupa, curto e sem os agudos ásperos
    pulo = filtro(tom(corta(f['roupa'], dur=0.2), 1.12), 220, 5000)
    grava(pulo, 'som_pulo.wav', fade_out=0.09, pico=0.6)
    # pulo no ar: as duas batidas da asa (0,1 a 0,42 s) com um farfalhar de roupa por baixo
    asa = filtro(corta(f['asa'], 0.1, 0.34), 140, 7000)
    grava(mixa((asa, 0, 1), (filtro(corta(f['roupa2']), 300, 4000), 0.02, 0.35)), 'som_pulo_ar.wav', fade_out=0.1, pico=0.7)
    salva_registro(reg, [
        ('som_pulo.wav', 'pulo do chão; desde a t191 substitui a receita da t31',
         [('roupa_496188.wav', '0,2 s, tom +12%, sem grave e sem agudo')]),
        ('som_pulo_ar.wav', 'pulo no ar: batida de asas; desde a t191 substitui a receita da t31',
         [('asa_389634.wav', '0,34 s a partir de 0,1 s'), ('roupa2_494797.wav', 'inteiro, por baixo')]),
    ], 'sons do pato, tools/t191_sons_pato.py')


def migra(d):
    ids = Ids('t191')
    pato = objeto(d, 'pato')
    poe_vars(ids, pato['variables'], 'pato', [
        ('pulo_som_volume', 22), ('pulo_som_variacao', 0.08), ('pulo_ar_som_volume', 38),
        ('pouso_som_min', 10), ('pouso_som_extra', 55)])
    poe_vars(ids, d['variables'], 'global', [
        ('moeda_som_volume', 22), ('moeda_som_passo', 1.06), ('moeda_combo_max', 8), ('moeda_combo_janela', 0.6),
        ('moeda_combo', 0), ('moeda_combo_t', 0), ('moeda_pegou', 0)])

    jog = folha(d, 'Jogador')['events']
    for e in todos(jog):
        for a in e.get('actions', []):
            p = a['parameters']
            if a['type']['value'] != 'PlaySound':
                continue
            if p[1] == 'som_pulo.wav' and p[3] == '40':
                p[3] = 'pato.pulo_som_volume'
                p[4] = 'RandomFloatInRange(1 - pato.pulo_som_variacao, 1 + pato.pulo_som_variacao)'
            elif p[1] == 'som_pulo_ar.wav' and p[3] == '45':
                p[3] = 'pato.pulo_ar_som_volume'
                p[4] = 'RandomFloatInRange(1 - pato.pulo_som_variacao, 1 + pato.pulo_som_variacao)'
            elif p[1] == 'som_pouso.wav' and p[3].startswith('35 + 45 *'):
                p[3] = 'pato.pouso_som_min + pato.pouso_som_extra *' + p[3][len('35 + 45 *'):]

    com = folha(d, 'Combate')['events']
    coleta = acha(com, 'Coleta')
    loop = coleta['events'][0]
    i = next(k for k, a in enumerate(loop['actions']) if a['type']['value'] == 'PlaySound' and a['parameters'][1] == 'som_moeda.wav')
    loop['actions'][i] = csetn('moeda_pegou', '=', '1')
    coleta['events'] += [
        ev([], [csetn('moeda_combo_t', '+', 'TimeDelta()')]),
        ev([cmp('moeda_combo_t', '>', 'moeda_combo_janela')], [csetn('moeda_combo', '=', '0')]),
        ev([cnum('moeda_pegou', '=', '1')], [
            som('som_moeda.wav', 'moeda_som_volume', 'pow(moeda_som_passo, min(moeda_combo, moeda_combo_max)) * RandomFloatInRange(0.98, 1.02)'),
            csetn('moeda_combo', '+', '1'), csetn('moeda_combo_t', '=', '0'), csetn('moeda_pegou', '=', '0')]),
    ]


if __name__ == '__main__':
    faz_sons()
    roda(migra, lambda d: any(v['name'] == 'pulo_som_volume' for v in objeto(d, 'pato')['variables']), 't191')
