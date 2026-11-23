"""Tarefa 142: anel rosa, o amor: canalizadores, escudo e o Juízo (chefe final, parte 6).

- Canalizadores: serafins pequenos (grupo Inimigo, sem moedas, estado "calmo" para encostar não ferir) que giram em
  volta do olho, presos a ele por laços rosa (laco_amor desenha uma linha de cada um até o olho).
- Escudo: a cada quadro conta os canalizadores vivos (canal_vivos, por instância: morrer de bala, ricochete,
  explosão ou eletricidade conta igual). Com algum vivo, o escudo aparece e a pupila não abre. Quando o último
  morre, o escudo quebra e a pupila fica vulnerável por aberto_tempo (janela_amor).
- Da fase 3 em diante, sem canalizadores e fora da janela, eles voltam (canal_qtd) depois de canal_respawn s.
- Golpe "amor": mais canal_qtd_extra canalizadores. Golpe "juizo": o olho carrega o Juízo por juizo_tempo,
  nascendo um canalizador a cada canal_intervalo; se todos morrerem antes, o Juízo falha; se não, acerta o pato
  (juizo_dano, quase toda a vida) com um clarão. Os dois terminam em fim_golpe.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t142_anel_rosa.py
"""
from gd_mig import *
import gd_luz as luz

ids = Ids('t142')
d_ = 'deus'
c_ = 'canalizador'


def nasce():
    return [X('Create', '', c_, 'deus.cx', 'deus.cy', '""'),
            setn(c_, 'ang', '=', 'deus.canal_seq * deus.canal_passo'), setn(d_, 'canal_seq', '+', '1'),
            X('ChangePlan', c_, '=', 'deus.z_base + 4'), anim(c_, 'canalizar')]


def amor():
    vivo = bol(d_, 'morto', False)
    no_golpe = lambda g: [vivo, txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', g)]
    return grupo('Anel rosa: amor', [
        ev([vivo], [setn(d_, 'canal_vivos', '=', '0')], [
            cada(c_, [bol(c_, 'morto', False)], [setn(d_, 'canal_vivos', '+', '1')])]),
        ev([num(d_, 'fase', '=', '3')], [setn(d_, 'canal_qtd', '=', 'deus.canal_qtd_3')]),
        ev([num(d_, 'fase', '=', '4')], [setn(d_, 'canal_qtd', '=', 'deus.canal_qtd_4')]),
        ev([bol(c_, 'morto', False)],
           [setn(c_, 'ang', '+', 'deus.canal_orbita_vel * TimeDelta()'),
            X('SetXY', c_, '=', 'deus.cx + cos(canalizador.ang) * deus.canal_orbita_raio - canalizador.Width() / 2', '=',
              'deus.cy + sin(canalizador.ang) * deus.canal_orbita_raio - canalizador.Height() / 2')]),
        ev([vivo, cmp('deus.canal_vivos', '>', '0'), X('SceneInstancesCount', '', 'laco_amor', '=', '0')],
           [X('Create', '', 'laco_amor', '0', '0', '""'), X('ChangePlan', 'laco_amor', '=', 'deus.z_base + 3')]),
        cada(c_, [bol(c_, 'morto', False)],
             [X('PrimitiveDrawing::LineV2', 'laco_amor', 'canalizador.CenterX()', 'canalizador.CenterY()', 'deus.cx',
                'deus.cy', 'deus.laco_espessura')]),
        ev([vivo, cmp('deus.canal_vivos', '>', '0')], [setb(d_, 'escudo', True), X('Show', 'deus_escudo', '')]),
        ev([vivo, bol(d_, 'escudo', True), cmp('deus.canal_vivos', '=', '0')],
           [setb(d_, 'escudo', False), X('Hide', 'deus_escudo'), setb(d_, 'vulneravel', True), setb(d_, 'janela_amor', True),
            zera(d_, 'janela'), anim(d_, 'contrai'), som('som_luz.wav', 'deus.som_volume', 'deus.escudo_quebra_tom')]),
        ev([vivo, bol(d_, 'janela_amor', True), timer(d_, 'janela', '>', 'deus.aberto_tempo')],
           [setb(d_, 'janela_amor', False), setb(d_, 'vulneravel', False), zera(d_, 'canal'), anim(d_, 'idle')]),
        ev([vivo, num(d_, 'fase', '>=', '3'), cmp('deus.canal_vivos', '=', '0'), bol(d_, 'janela_amor', False),
            NAO('StringObjectVariable', d_, 'estado', '=', '"fase"'), timer(d_, 'canal', '>', 'deus.canal_respawn')],
           [zera(d_, 'canal'), anim('deus_anel_rosa', 'cintila')], [repete('deus.canal_qtd', nasce())]),
        ev(no_golpe('amor') + [txt(d_, 'etapa', '')],
           [sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), anim('deus_anel_rosa', 'cintila')],
           [repete('deus.canal_qtd_extra', nasce())]),
        ev(no_golpe('juizo') + [txt(d_, 'etapa', '')],
           [sets(d_, 'etapa', 'juizo'), zera(d_, 'golpe'), zera(d_, 'canal_juizo'), anim('deus_olho', 'juizo'),
            anim('deus_anel_rosa', 'cintila'), som('som_luz.wav', 'deus.som_volume', 'deus.juizo_tom')],
           [repete('deus.juizo_canal_qtd', nasce())]),
        ev(no_golpe('juizo') + [txt(d_, 'etapa', 'juizo')], [], [
            ev([timer(d_, 'canal_juizo', '>', 'deus.canal_intervalo'), cmp('deus.canal_vivos', '<', 'deus.canal_max')],
               [zera(d_, 'canal_juizo')] + nasce()),
            ev([cmp('deus.canal_vivos', '=', '0'), timer(d_, 'golpe', '>', 'deus.juizo_graca')],
               [sets(d_, 'etapa', 'juizo_falha'), zera(d_, 'golpe'), anim('deus_olho', 'juizo_falha'),
                som('som_luz.wav', 'deus.som_volume', 'deus.juizo_falha_tom')]),
            ev([cmp('deus.canal_vivos', '>', '0'), timer(d_, 'golpe', '>', 'deus.juizo_tempo'), bol('pato', 'morto', False)],
               [setn('pato', 'vida', '-', 'deus.juizo_dano'), setb('pato', 'invencivel', True), zera('pato', 'iframes'),
                sets('pato', 'ultimo_agressor', 'deus'), sets(d_, 'etapa', 'juizo_clarao'), zera(d_, 'golpe'),
                luz.acao_luz_ambiente('"Luz"', 'deus.luz_ambiente_flash'), som('som_luz.wav', 'deus.som_volume')]),
        ]),
        ev(no_golpe('juizo') + [txt(d_, 'etapa', 'juizo_falha'),
                                X('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', 'deus_olho', 'Animation')],
           [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), anim('deus_olho', 'idle'),
            anim('deus_anel_rosa', 'idle')]),
        ev(no_golpe('juizo') + [txt(d_, 'etapa', 'juizo_clarao'), timer(d_, 'golpe', '>', 'deus.juizo_flash')],
           [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), anim('deus_olho', 'idle'),
            anim('deus_anel_rosa', 'idle'), luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_normal')]),
        ev([bol(d_, 'morto', True)], [X('Delete', 'laco_amor', '')]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    proprias = [('vida', 30), ('max_vida', 30), ('qtd_moedas', 0), ('dano', 0), ('estado', 'calmo'), ('sangue', 'azul'),
                ('tem_barra_de_vida', False), ('firme', True), ('chefe_final', False), ('invulneravel', False),
                ('reflete', False), ('ang', 0)]
    nomes = {n for n, _ in proprias}
    herdadas = [(v['name'], v['value']) for v in o['ofanim']['variables']
                if v['name'] not in nomes and 'value' in v and not v['name'].startswith('guardiao')
                and v['name'] not in ('nome', 'barra_ativa', 'barra_dist', 'barra_largura', 'barra_rastro_vel',
                                      'chefe_preparado')]
    poe_vars(ids, o[c_]['variables'], c_, proprias + herdadas)
    for gr in ('Inimigo', 'Personagem'):
        poe_no_grupo(d, gr, c_)
    laser = o['laser']
    laco = {k: v for k, v in laser.items() if k not in ('name', 'persistentUuid', 'effects', 'variables')}
    laco.update(name='laco_amor', persistentUuid=ids('obj/laco_amor'), variables=[],
                outlineColor={'r': 255, 'g': 150, 'b': 185}, outlineOpacity=200, absoluteCoordinates=True,
                clearBetweenFrames=True,
                effects=[efeito('Glow', 'Effect', {'distance': 15, 'innerStrength': 3, 'outerStrength': 5},
                                {'color': '255;120;170'})])
    poe_objeto(d, laco, 'inimigos/chefe')
    poe_vars(ids, o[d_]['variables'], d_, [
        ('canal_vivos', 0), ('canal_qtd', 3), ('canal_qtd_3', 3), ('canal_qtd_4', 4), ('canal_qtd_extra', 2),
        ('canal_respawn', 2.5), ('canal_intervalo', 1.1), ('canal_max', 8), ('canal_orbita_raio', 400),
        ('canal_orbita_vel', 0.8), ('canal_passo', 2.1), ('canal_seq', 0), ('janela_amor', False),
        ('laco_espessura', 4), ('escudo_quebra_tom', 0.8), ('juizo_tempo', 6), ('juizo_graca', 0.4),
        ('juizo_dano', 85), ('juizo_canal_qtd', 3), ('juizo_flash', 0.4), ('juizo_tom', 0.6), ('juizo_falha_tom', 1.6)])
    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Janela aberta')
    deus['events'].insert(k, amor())


if __name__ == '__main__':
    roda(migra, lambda d: acha(folha(d, 'InimigosParaiso')['events'], 'Anel rosa: amor') is not None, 't142')
