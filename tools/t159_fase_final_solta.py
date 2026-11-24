"""Tarefa 159: na fase final Deus solta do pé da tela e segue o pato; a investida parte de longe, de um ponto sorteado.

- Corpo: o movimento sai do evento da pupila e vira dois eventos antes dele. Até a fase 3, o de sempre (segue o x do
  pato, preso a distancia_baixo abaixo do centro da tela). Na fase 4 (fora da investida) ele vai para um ponto a
  final_distancia do pato, do lado em que já está (final_d é a distância atual), preso dentro da tela a final_margem
  das bordas, a final_segue. A posição é suavizada em relação à câmera (deus.ox, deus.oy, como na investida), porque
  no mundo ele ficava para trás da câmera, que sobe rápido na fase final; ao entrar na fase final ox/oy partem de
  onde ele está.
- Investida, só na fase final: depois de sair por baixo e depois de cada corrida, antes de mirar, ele reaparece num
  ponto sorteado em volta da tela (ângulo investida_pos), além do canto da tela por investida_longe; mira e corre de lá.
  Nas outras fases ele parte de onde saiu, como antes.
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t159_fase_final_solta.py
"""
from gd_mig import *

ids = Ids('t159')
d_ = 'deus'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
K = 'min(1, deus.final_segue * TimeDelta())'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def alvo(eixo, centro, tam):
    p = f'pato.Center{eixo.upper()}()'
    return (f'(clamp({p} + (deus.c{eixo} - {p}) / deus.final_d * deus.final_distancia, '
            f'{centro} - {tam} / 2 + deus.final_margem, {centro} + {tam} / 2 - deus.final_margem) - {centro} - deus.o{eixo}) * {K}')


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [('final_distancia', 380), ('final_margem', 170), ('final_segue', 1.4),
                                           ('final_d', 0), ('investida_longe', 500), ('investida_pos', 0)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    corpo = acha(deus['events'], 'Corpo')
    pupila = next(e for e in corpo['events'] if '"deus", "pupila_ox", "+"' in tx(e['actions']))
    mov = [a for a in pupila['actions'] if a['parameters'][:2] in ([d_, 'cx'], [d_, 'cy'])]
    pupila['actions'] = [a for a in pupila['actions'] if a not in mov]
    k = corpo['events'].index(pupila)
    corpo['events'][k:k] = [
        ev([bol(d_, 'morto', False), num(d_, 'fase', '<', '4')], mov),
        ev([bol(d_, 'morto', False), num(d_, 'fase', '=', '4'), bol(d_, 'investindo', False)],
           [setn(d_, 'final_d', '=', 'max(1, sqrt(pow(deus.cx - pato.CenterX(), 2) + pow(deus.cy - pato.CenterY(), 2)))'),
            setn(d_, 'ox', '+', alvo('x', CX, CW)), setn(d_, 'oy', '+', alvo('y', CY, CH)),
            setn(d_, 'cx', '=', f'{CX} + deus.ox'), setn(d_, 'cy', '=', f'{CY} + deus.oy')]),
    ]
    final = acha(deus['events'], 'Fase final')
    ini = next(e for e in final['events'] if '"deus", "final_iniciado", "True"' in tx(e['actions']))
    ini['actions'] += [setn(d_, 'ox', '=', f'deus.cx - {CX}'), setn(d_, 'oy', '=', f'deus.cy - {CY}')]

    longe = f'(sqrt(pow({CW} / 2, 2) + pow({CH} / 2, 2)) + deus.investida_longe)'
    azul = acha(deus['events'], 'Anel azul: investida')
    for e in todos(azul['events']):
        a = e.get('actions', [])
        if '"deus", "etapa", "=", "\\"mira\\""' in tx(a):
            e.setdefault('events', []).append(ev([num(d_, 'fase', '=', '4')], [
                setn(d_, 'investida_pos', '=', 'ToRad(RandomFloatInRange(0, 360))'),
                setn(d_, 'ox', '=', f'cos(deus.investida_pos) * {longe}'),
                setn(d_, 'oy', '=', f'sin(deus.investida_pos) * {longe}')]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'final_distancia' for v in objeto(d, 'deus')['variables']), 't159')
