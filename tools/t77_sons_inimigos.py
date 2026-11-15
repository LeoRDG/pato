"""Tarefa 77: sons das mecânicas novas dos inimigos (tarefa 78), feitos com gravações CC0 do Freesound.

Como na tarefa 31: cada som final (assets/som_*.wav) tem uma receita abaixo; as gravações ficam em assets/fontes_cc0/ e são
baixadas na primeira vez (o script confere na página de cada uma que a licença é CC0). O registro das fontes é regerado em
assets/fontes_cc0/FONTES.txt (seção própria desta tarefa) e fontes.json.
Rodar:  python3 tools/t77_sons_inimigos.py   (não mexe no jogo.json; quem liga os sons nos eventos é t78_inimigos_mecanicas.py)
"""
import numpy as np
from sons_cc0 import SR, baixa, carrega_registro, corta, filtro, grava, le, mixa, salva_registro, tom

FONTES = dict(arremesso=346373, rugido_curto=132874, queda_corpo=504626, splat_molhado=495118, swosh=59988, fogo=260554,
              ricochete=30932, swing=389590, risada_diabinho=205751, moeda_obj=146723, laser_carga=588242, laser_feixe=352852,
              bomba_cai=506313, rasga=30931, impacto_pedra=513694, slurp=445974, arco=394179, magia=442774,
              magia2=241809, woosh_fundo=245932, zumbi=463721)


def receitas(f):
    R = {}
    R['som_arremesso.wav'] = ('condenada joga ossos', [('arremesso', 'inteiro, tom -10%')],
                              tom(corta(f('arremesso')), 0.9), {'fade_out': 0.05})
    R['som_carga.wav'] = ('condenado azul avisa a investida', [('rugido_curto', '0,8 s, tom -15%')],
                          tom(corta(f('rugido_curto'), dur=0.9), 0.85), {'fade_out': 0.2})
    R['som_bate_parede.wav'] = ('investida bate na parede / roda bate', [('queda_corpo', '0,5 s')],
                                corta(f('queda_corpo'), dur=0.5), {'fade_out': 0.15})
    R['som_bile.wav'] = ('bolsa de bile estoura', [('splat_molhado', 'inteiro'), ('rasga', '0,3 s, tom -20%, por baixo')],
                         mixa((corta(f('splat_molhado')), 0, 1), (tom(corta(f('rasga'), dur=0.3), 0.8), 0, 0.4)), {'fade_out': 0.1})
    R['som_espinhos.wav'] = ('árvore solta o leque de espinhos', [('swosh', 'três vezes, tons 1,3 / 1,15 / 1,45, 30 ms entre elas')],
                             mixa((tom(corta(f('swosh')), 1.3), 0, 1), (tom(corta(f('swosh')), 1.15), 0.03, 0.8),
                                  (tom(corta(f('swosh')), 1.45), 0.06, 0.7)), {'fade_out': 0.05})
    R['som_espiral.wav'] = ('caveira gigante gira a espiral de fogo', [('fogo', '1,2 s a partir de 0,2 s')],
                            corta(f('fogo'), 0.2, 1.2), {'fade_out': 0.4})
    R['som_ping.wav'] = ('bala ricocheteia em inimigo blindado', [('ricochete', '0,35 s, tom +20%')],
                         tom(corta(f('ricochete'), dur=0.42), 1.2), {'fade_out': 0.12, 'pico': 0.55})
    R['som_investida.wav'] = ('cabeça voadora / roda disparam', [('swing', 'inteiro, tom -15%')],
                              tom(corta(f('swing')), 0.85), {'fade_out': 0.06})
    R['som_roubo.wav'] = ('diabinho rouba moedas', [('moeda_obj', 'inteiro'), ('risada_diabinho', 'inteiro, entra aos 0,05 s')],
                          mixa((corta(f('moeda_obj')), 0, 0.8), (corta(f('risada_diabinho')), 0.05, 1)), {'fade_out': 0.15})
    R['som_laser_carga.wav'] = ('olho demoníaco mira o raio', [('laser_carga', 'inteiro, tom -10%')],
                                tom(corta(f('laser_carga')), 0.9), {'fade_out': 0.1, 'pico': 0.55})
    R['som_laser.wav'] = ('olho demoníaco dispara o raio', [('laser_feixe', '0,5 s, tom -20%')],
                          tom(corta(f('laser_feixe'), dur=0.42), 0.8), {'fade_out': 0.15})
    R['som_bomba.wav'] = ('voador solta bomba', [('bomba_cai', '0,7 s')],
                          corta(f('bomba_cai'), dur=0.7), {'fade_out': 0.2, 'pico': 0.5})
    R['som_arranca.wav'] = ('zumbi perde a cabeça', [('rasga', 'inteiro'), ('splat_molhado', 'inteiro, tom -20%')],
                            mixa((corta(f('rasga')), 0, 1), (tom(corta(f('splat_molhado')), 0.8), 0.02, 0.7)), {'fade_out': 0.15})
    R['som_impacto.wav'] = ('pigman cai do salto e solta as ondas', [('impacto_pedra', '0,7 s, tom -15%')],
                            tom(corta(f('impacto_pedra'), dur=0.8), 0.85), {'fade_out': 0.25})
    R['som_lingua.wav'] = ('língua do sapo', [('slurp', 'inteiro, tom -10%')],
                           tom(corta(f('slurp')), 0.9), {'fade_out': 0.05})
    R['som_flecha.wav'] = ('querubim atira a flecha', [('arco', 'inteiro')],
                           corta(f('arco')), {'fade_out': 0.06})
    R['som_luz.wav'] = ('serafim e ofanim soltam luz', [('magia', '0,7 s, tom +20%')],
                        tom(corta(f('magia'), dur=0.84), 1.2), {'fade_out': 0.25, 'pico': 0.5})
    R['som_olhos.wav'] = ('ofanim abre os olhos', [('magia2', '0,8 s, tom -20%')],
                          tom(corta(f('magia2'), dur=0.64), 0.8), {'fade_out': 0.25, 'pico': 0.55})
    R['som_roda.wav'] = ('roda do anjo acelera girando', [('woosh_fundo', '0,6 s, tom +50%')],
                         filtro(tom(corta(f('woosh_fundo'), dur=0.9), 1.5), 150), {'fade_out': 0.1})
    R['som_levanta.wav'] = ('condenado se levanta', [('zumbi', '0,9 s, tom -15%')],
                            tom(corta(f('zumbi'), dur=0.77), 0.85), {'fade_out': 0.25})
    return R


def main():
    reg = carrega_registro()
    arq = {k: baixa(k, sid, reg) for k, sid in FONTES.items()}
    R = receitas(lambda k: le(arq[k]))
    usos = []
    for som, (desc, fontes, x, op) in R.items():
        grava(x, som, **op)
        usos.append((som, desc, [(arq[a], t) for a, t in fontes]))
        print(f'{som:<26} {len(x) / SR:.2f}s')
    salva_registro(reg, usos, 'sons das mecânicas dos inimigos, tools/t77_sons_inimigos.py')


if __name__ == '__main__':
    main()
