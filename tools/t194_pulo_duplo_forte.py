"""Tarefa 194: o pulo no ar sobe mais.
Medido no jogo: com a trajetória nova do comportamento de plataforma, a gravidade soma velocidade de queda enquanto o pulo
sustenta, então o pulo segurado inteiro sobe só ~155 px e o pulo no ar (que é o mesmo pulo, começando de onde o pato está)
quase não leva para cima. Agora o pulo no ar tem força própria: no quadro em que ele sai, a força do pulo vira
força * pato.pulo_ar_forca (1,25: ~230 px segurado, +50%) e volta ao valor de antes logo depois (pato.pulo_ar_salvo),
então o pulo do chão, a lava e a poça de sangue (que mudam a força do pulo) continuam iguais.
Rodar uma vez:  python3 tools/t194_pulo_duplo_forte.py
"""
from gd_mig import *

FORCA = 'pato.PlatformerObject::JumpSpeed()'


def forca(v):
    return X('PlatformBehavior::JumpSpeed', 'pato', 'PlatformerObject', '=', v)


def migra(d):
    ids = Ids('t194')
    poe_vars(ids, objeto(d, 'pato')['variables'], 'pato', [
        ('pulo_ar_forca', 1.25), ('pulo_ar_salvo', 0), ('pulo_ar_quadros', 0), ('pulo_ar_ativo', False)])
    jog = folha(d, 'Jogador')['events']
    g = acha(jog, 'pulo no ar e giro em direcao do movimento')
    e = g['events'][0]
    assert any(a['parameters'][1:2] == ['som_pulo_ar.wav'] for a in e['actions'] if a['type']['value'] == 'PlaySound')
    e['actions'] += [
        setn('pato', 'pulo_ar_salvo', '=', FORCA),
        forca(f'{FORCA} * pato.pulo_ar_forca'),
        setn('pato', 'pulo_ar_quadros', '=', '0'),
        setb('pato', 'pulo_ar_ativo', True)]
    mov = acha(jog, 'Movimento')
    # o pulo sai no começo do quadro seguinte; nos eventos desse quadro a força volta ao normal
    mov['events'].append(ev([bol('pato', 'pulo_ar_ativo', True)], [setn('pato', 'pulo_ar_quadros', '+', '1')], [
        ev([num('pato', 'pulo_ar_quadros', '>=', '2')], [forca('pato.pulo_ar_salvo'), setb('pato', 'pulo_ar_ativo', False)])]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'pulo_ar_forca' for v in objeto(d, 'pato')['variables']), 't194')
