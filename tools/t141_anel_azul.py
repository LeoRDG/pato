"""Tarefa 141: anel azul, o piscar no escuro (chefe final, parte 5).

Golpe "piscar": o olho fecha (a pupila some), a camada de luz cai para luz_ambiente_escuro e a luz do pato encolhe
(luz_pato_raio_escuro). Nascem deus.halo_qtd halos (luzes) que derivam pela tela. Perto do fim um som avisa; o olho
abre de estalo com um clarão (luz_ambiente_flash) e queima (piscar_dano) quem não estiver dentro de um halo
(halo_raio do centro dele). Depois a luz volta ao normal, os halos somem e o golpe termina em fim_golpe.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t141_anel_azul.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t141')
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
d_ = 'deus'
ESQ, DIR = f'{CX} - {CW} / 2 + deus.halo_margem', f'{CX} + {CW} / 2 - deus.halo_margem'
TOPO, BAIXO = f'{CY} - {CH} / 2 + deus.halo_margem', f'{CY} + {CH} / 2 - deus.halo_margem'


def piscar():
    no_golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'piscar')]
    nasce = repete('deus.halo_qtd', [
        X('Create', '', 'luz_halo', f'RandomInRange({ESQ}, {DIR})', f'RandomInRange({TOPO}, {BAIXO})', '"Luz"'),
        luz.acao_raio_luz('luz_halo', 'deus.halo_raio_luz'), luz.acao_cor_luz('luz_halo', 'deus.halo_cor'),
        setn('luz_halo', 'vx', '=', 'deus.halo_vel * RandomFloatInRange(-1, 1)'),
        setn('luz_halo', 'vy', '=', 'deus.halo_vel * RandomFloatInRange(-1, 1)')])
    queima = ev([bol('pato', 'no_halo', False), bol('pato', 'invencivel', False), bol('pato', 'morto', False)],
                [setn('pato', 'vida', '-', 'deus.piscar_dano'), setb('pato', 'invencivel', True), zera('pato', 'iframes'),
                 sets('pato', 'ultimo_agressor', 'deus')])
    marca = cada('luz_halo', [cmp('sqrt(pow(pato.CenterX() - luz_halo.X(), 2) + pow(pato.CenterY() - luz_halo.Y(), 2))',
                                  '<', 'deus.halo_raio')], [setb('pato', 'no_halo', True)])
    return grupo('Anel azul: piscar', [
        ev(no_golpe + [txt(d_, 'etapa', '')],
           [sets(d_, 'etapa', 'fecha'), zera(d_, 'golpe'), anim('deus_olho', 'piscar'), anim('deus_anel_azul', 'cintila'),
            luz.acao_raio_luz('luz_olhar', '0')]),
        ev(no_golpe + [txt(d_, 'etapa', 'fecha'), timer(d_, 'golpe', '>', 'deus.piscar_fecha')],
           [sets(d_, 'etapa', 'escuro'), zera(d_, 'golpe'), anim('deus_olho', 'fechado'), X('Hide', d_),
            luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_escuro'), luz.acao_raio_luz('luz_pato', 'deus.luz_pato_raio_escuro'),
            setb(d_, 'piscar_avisou', False)], [nasce]),
        ev(no_golpe + [txt(d_, 'etapa', 'escuro')],
           [X('SetX', 'luz_halo', '+', 'luz_halo.vx * TimeDelta()'),
            X('SetY', 'luz_halo', '+', 'luz_halo.vy * TimeDelta() - subida_vel * TimeDelta()')], [
            ev([X('PosX', 'luz_halo', '<', ESQ)], [setn('luz_halo', 'vx', '=', 'abs(luz_halo.vx)')]),
            ev([X('PosX', 'luz_halo', '>', DIR)], [setn('luz_halo', 'vx', '=', '-abs(luz_halo.vx)')]),
            ev([X('PosY', 'luz_halo', '<', TOPO)], [setn('luz_halo', 'vy', '=', 'abs(luz_halo.vy)')]),
            ev([X('PosY', 'luz_halo', '>', BAIXO)], [setn('luz_halo', 'vy', '=', '-abs(luz_halo.vy)')]),
            ev([bol(d_, 'piscar_avisou', False), timer(d_, 'golpe', '>', 'deus.piscar_fechado - deus.piscar_aviso')],
               [setb(d_, 'piscar_avisou', True), som('som_luz.wav', 'deus.som_volume', 'deus.piscar_aviso_tom')]),
            ev([timer(d_, 'golpe', '>', 'deus.piscar_fechado')],
               [sets(d_, 'etapa', 'clarao'), zera(d_, 'golpe'), anim('deus_olho', 'idle'), X('Show', d_, ''),
                luz.acao_luz_ambiente('"Luz"', 'deus.luz_ambiente_flash'), setb('pato', 'no_halo', False),
                som('som_luz.wav', 'deus.som_volume')], [marca, queima]),
        ]),
        ev(no_golpe + [txt(d_, 'etapa', 'clarao'), timer(d_, 'golpe', '>', 'deus.piscar_flash')],
           [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'),
            luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_normal'), luz.acao_raio_luz('luz_pato', 'luz_pato_raio'),
            X('Delete', 'luz_halo', ''), anim('deus_anel_azul', 'idle')]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o['luz_halo']['variables'], 'luz_halo', [('vx', 0), ('vy', 0)])
    poe_vars(ids, o['pato']['variables'], 'pato', [('no_halo', False)])
    poe_vars(ids, o['deus']['variables'], 'deus', [
        ('piscar_fecha', 0.3), ('piscar_fechado', 3.2), ('piscar_aviso', 0.8), ('piscar_aviso_tom', 1.4),
        ('piscar_flash', 0.3), ('piscar_dano', 45), ('piscar_avisou', False),
        ('halo_qtd', 3), ('halo_raio', 150), ('halo_raio_luz', 190), ('halo_vel', 140), ('halo_margem', 200),
        ('halo_cor', '170;215;255'), ('luz_pato_raio_escuro', 110), ('luz_ambiente_flash', '255;255;255')])
    vals = vars_cena(d, 'Paraiso')
    poe_vars(ids, cena(d, 'Teste')['variables'], 'Teste',
             [(n, vals[n]) for n in ('luz_ambiente_escuro', 'luz_pato_raio')])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Janela aberta')
    deus['events'].insert(k, piscar())


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Anel azul: piscar') is not None, 't141')
