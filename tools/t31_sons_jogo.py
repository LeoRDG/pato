"""Tarefa 31: sons do pato, das moedas, dos inimigos e da troca de arma, feitos com gravações CC0 do Freesound.

Cada som final (assets/som_*.wav) tem uma receita abaixo: de quais gravações vem, que trecho, tom e mistura. As gravações ficam em
assets/fontes_cc0/ e são baixadas sozinhas na primeira vez (o script confere na página de cada uma que a licença é CC0).
O registro das fontes (autor, título, endereço, licença, trecho usado) é regerado em assets/fontes_cc0/FONTES.txt e fontes.json.

Todo som começa já forte: grava() corta a subida lenta do começo (até 30% do pico, ou o 'ataque' da receita), senão parece atrasado.
Para trocar um som: ache outra gravação CC0 no Freesound, ponha o id em FONTES (apelido -> id) e ajuste a receita; rode de novo.
Rodar:  python3 tools/t31_sons_jogo.py   (não mexe no jogo.json; quem liga os sons nos eventos é t32_sons_eventos.py)
"""
import os
import numpy as np
from sons_cc0 import SR, baixa, carrega_registro, corta, filtro, grava, info, le, mixa, salva_registro, tom

FONTES = dict(pulo=331381, whoosh=60013, woosh=683101, impacto=364690, quack=418509, quack2=242664, moeda=402067,
              moedas_caem=17502, splat=232135, soco=118513, morte_monstro=559621, splat2=87535, porco=233177, sapo=536759,
              cuspe=52157, cuspe2=445118, rosnado=222523, grito=333832, zumbi=463721, gorgolejo=402861, rugido=469123,
              fogo=260554, magia=442872, carga=500913, energia=519415, trava=189327, projetil=193427, demonio=444445)
JA_BAIXADAS = {'rec_pistola_ferrolho_tras_276959.wav': 276959, 'rec_pistola_ferrolho_frente_276959.wav': 276959}   # da tarefa 23


def receitas(f):
    """f(apelido) -> gravação inteira. Devolve {som: (descrição, [(apelido, trecho usado)], sinal, opções de grava)}."""
    R = {}
    R['som_pulo.wav'] = ('pulo do chão', [('pulo', 'inteiro, tom +15%')],
                         tom(corta(f('pulo')), 1.15), {})
    R['som_pulo_ar.wav'] = ('pulo no ar, com o giro', [('whoosh', 'inteiro, tom +30%'), ('pulo', 'inteiro, tom +40%, baixo')],
                            mixa((tom(corta(f('whoosh')), 1.3), 0, 1), (tom(corta(f('pulo')), 1.4), 0, 0.35)), {})
    R['som_dash.wav'] = ('dash', [('whoosh', 'inteiro, tom -15%'), ('woosh', '0,25 s a partir de 0,19 s')],
                         mixa((tom(corta(f('whoosh')), 0.85), 0, 1), (corta(f('woosh'), 0.15, 0.25), 0, 0.6)), {'fade_out': 0.08})
    R['som_pouso.wav'] = ('pouso depois de uma queda', [('impacto', '0,35 s, tom +30%, sem grave')],
                          filtro(tom(corta(f('impacto'), dur=0.45), 1.3), 120), {'fade_out': 0.1})
    R['som_pato_dano.wav'] = ('pato leva dano', [('quack', '0,22 s, tom +10%')],
                              tom(corta(f('quack'), dur=0.24), 1.1), {'fade_out': 0.04})
    R['som_pato_morte.wav'] = ('pato morre: quack grave e o demônio saindo',
                               [('quack2', 'inteiro, tom -20%'), ('demonio', '1,4 s a partir de 0,28 s, entra aos 0,25 s')],
                               mixa((tom(corta(f('quack2'), dur=0.45), 0.8), 0, 1), (corta(f('demonio'), 0.2, 1.4), 0.25, 0.8)),
                               {'fade_out': 0.6})
    R['som_moeda.wav'] = ('pegar moeda', [('moeda', 'só a primeira nota, 0,12 s, sem grave')],
                          filtro(corta(f('moeda'), dur=0.12), 600), {'fade_out': 0.07})
    R['som_moedas_soltas.wav'] = ('moedas caindo do inimigo morto', [('moedas_caem', '0,7 s a partir de 0,26 s')],
                                  corta(f('moedas_caem'), 0.2, 0.7), {'fade_out': 0.3})
    R['som_acerto.wav'] = ('bala acerta inimigo', [('splat', 'inteiro'), ('soco', '0,18 s, por baixo')],
                           mixa((corta(f('splat')), 0, 1), (filtro(corta(f('soco'), dur=0.18), None, 3000), 0, 0.5)), {'fade_out': 0.05})
    R['som_inimigo_morte.wav'] = ('inimigo morre', [('morte_monstro', '0,75 s'), ('splat2', 'inteiro, por baixo')],
                                  mixa((corta(f('morte_monstro'), dur=0.75), 0, 1), (corta(f('splat2')), 0, 0.45)), {'fade_out': 0.2})
    R['som_aviso_pigman.wav'] = ('pigman avisa a investida', [('porco', '0,8 s a partir de 0,16 s')],
                                 corta(f('porco'), 0.1, 0.8), {'fade_out': 0.15})
    R['som_aviso_atirador.wav'] = ('atirador engatilha', [('rec_pistola_ferrolho_tras_276959.wav', 'inteiro, tom -15%'),
                                                         ('rec_pistola_ferrolho_frente_276959.wav', 'inteiro, tom -15%, aos 0,14 s')],
                                   mixa((tom(f('rec_pistola_ferrolho_tras_276959.wav'), 0.85), 0, 1),
                                        (tom(f('rec_pistola_ferrolho_frente_276959.wav'), 0.85), 0.14, 1)), {})
    R['som_tiro_inimigo.wav'] = ('tiro do atirador', [('projetil', '0,3 s, tom -20%')],
                                 tom(corta(f('projetil'), dur=0.26), 0.8), {'fade_out': 0.06})
    R['som_aviso_sapo.wav'] = ('sapo coaxa antes de cuspir', [('sapo', 'inteiro')], corta(f('sapo'), dur=0.4), {'fade_out': 0.06})
    R['som_cuspe.wav'] = ('sapo cospe', [('cuspe', '0,25 s a partir de 1,05 s'), ('cuspe2', 'tom +30%, por baixo')],
                          mixa((corta(f('cuspe'), 1.0, 0.25), 0, 1), (tom(corta(f('cuspe2'), dur=0.4), 1.3), 0, 0.4)), {'fade_out': 0.06})
    R['som_cura.wav'] = ('sapo cura os inimigos perto', [('energia', '0,8 s, tom +50%')],
                         tom(corta(f('energia'), dur=1.2), 1.5), {'fade_out': 0.35, 'ataque': 0.5})
    R['som_aviso_cutulu.wav'] = ('cutulu rosna antes de atacar', [('rosnado', '0,9 s a partir de 0,32 s, tom -10%')],
                                 tom(corta(f('rosnado'), 0.25, 0.8), 0.9), {'fade_out': 0.3, 'ataque': 0.6})
    R['som_aviso_mergulhador.wav'] = ('voadores gritam antes do mergulho', [('grito', '0,55 s, tom +15%')],
                                      tom(corta(f('grito'), 0.1, 0.63), 1.15), {'fade_out': 0.25})
    R['som_aviso_condenado.wav'] = ('condenados gemem antes do bote', [('zumbi', '0,6 s')],
                                    corta(f('zumbi'), 0.05, 0.6), {'fade_out': 0.25})
    R['som_aviso_inchado.wav'] = ('condenado inchado borbulha antes de explodir', [('gorgolejo', '0,65 s')],
                                  corta(f('gorgolejo'), dur=0.65), {'fade_out': 0.15, 'ataque': 0.6})
    R['som_aviso_caveira.wav'] = ('caveira gigante ruge antes do fogo', [('rugido', '0,8 s a partir de 0,35 s')],
                                  corta(f('rugido'), 0.3, 0.8), {'fade_out': 0.3, 'satura': 0.5, 'ataque': 0.6})
    R['som_fogo_caveira.wav'] = ('explosão de fogo da caveira gigante', [('fogo', '1,3 s')],
                                 corta(f('fogo'), dur=1.3), {'fade_out': 0.5, 'ataque': 0.6})
    R['som_aviso_olho.wav'] = ('olho demoníaco carrega o tiro', [('carga', '0,55 s do começo, de trás para a frente (sobe)')],
                                corta(f('carga'), dur=0.55)[::-1].copy(), {'fade_in': 0.01, 'fade_out': 0.02, 'ataque': 0.6})
    R['som_tiro_olho.wav'] = ('tiro do olho demoníaco', [('magia', '0,6 s')], corta(f('magia'), dur=0.6), {'fade_out': 0.2})
    R['som_aviso_mina.wav'] = ('mina demoníaca apita antes de explodir', [('trava', '0,5 s, tom +20%')],
                               tom(corta(f('trava'), dur=0.6), 1.2), {'fade_out': 0.03})
    R['som_troca_arma.wav'] = ('troca de arma', [('rec_pistola_ferrolho_frente_276959.wav', 'inteiro, tom -10%')],
                               tom(f('rec_pistola_ferrolho_frente_276959.wav'), 0.9), {})
    return R


def main():
    reg = carrega_registro()
    arq = {k: baixa(k, sid, reg) for k, sid in FONTES.items()}
    for nome, sid in JA_BAIXADAS.items():
        if nome not in reg:
            reg[nome] = dict(info(sid), baixado='2026-11-12')
        arq[nome] = nome
    R = receitas(lambda k: le(arq[k]))
    usos = []
    for som, (desc, fontes, x, op) in R.items():
        grava(x, som, **op)
        usos.append((som, desc, [(arq[a], t) for a, t in fontes]))
        print(f'{som:<28} {len(x) / SR:.2f}s')
    salva_registro(reg, usos, 'sons do jogo, tools/t31_sons_jogo.py')


if __name__ == '__main__':
    main()
