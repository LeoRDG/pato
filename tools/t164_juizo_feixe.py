"""Tarefa 164: o Juízo refeito, e as estrelas do céu viram objetos.

Estrelas (grupo "Estrelas"): as estrelas pintadas no fundo (bg_espaco, bg_ceu_alto) saem da arte (arte_deus.bg sem
pontos) e viram deus.estrela_qtd objetos estrela na camada Fundo, cada uma com casa (hx, hy) em relação ao centro da
tela, descendo com a subida (estrela_parallax) e piscando (estrela_pisca). Ficam tão visíveis quanto o céu escuro
(estrela_ceu_k, pela opacidade dos fundos, nunca menos que estrela_ceu_min). Estados (estrela.est): "" na casa, "vai" sendo sugada (acelera até o olho com
um rastro de partículas, estrela_rastro), "some" sugada, "volta" reaparecendo.

Juízo (grupo "Juízo: o feixe"), etapas:
- vai: Deus para embaixo no meio da tela (juizo_baixo acima da borda; a posição fica em relação à câmera, ox/oy).
- suga (juizo_sugar): as estrelas são sugadas para o olho, cada uma depois de um atraso sorteado (juizo_sugar_espalha);
  o buraco branco abre à esquerda (juizo_branco_dx/dy) e o negro, quase invisível, fica à direita (juizo_negro_dx/dy).
- aviso (juizo_aviso): o olho carrega com um som (juizo_aviso_tom).
- feixe (juizo_varrer): um feixe grosso (juizo_largura, Glow e bloom) sai do olho para a direita e gira 180° no sentido
  anti-horário (juizo_ang de 0 a -180). Mata o pato com um toque (mesmo invencível) e os anjinhos que pegar. Ao passar
  pelo buraco negro acende o horizonte de eventos nele e um clarão no branco (o aviso de que a saída é ali). O negro curva o espaço em volta com uma lente (BulgePinch, juizo_lente_negra, raio juizo_lente_raio) no fundo e
  na camada do jogo, e é um disco preto com um aro fino, sem halo; o branco é uma luz firme (Glow e bloom), sem pulsar. O horizonte só acende quando o feixe saiu
  inteiro de cima do negro (juizo_negro_livre), para que entrar no branco logo depois do aviso seja seguro. O buraco
  branco some quando o feixe passa por ele. As estrelas voltam por onde o feixe passou.
- fecha (juizo_fecha): fim; o golpe só volta depois de juizo_recarga segundos (juizo_volta_em, na Escolha do golpe).
Enquanto o branco está aberto, encostar nele leva o pato para o buraco negro, que o feixe já passou.
Sai o Juízo antigo do anel rosa (canalizadores com prazo, laços engrossando, som de aviso).
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t164_juizo_feixe.py
"""
import copy
from gd_mig import *
import gd_luz as luz
from t149_redoma_e_particulas import emissor

ids = Ids('t164')
d_ = 'deus'
E = 'estrela'
R = 'estrela_rastro'
F = 'juizo_feixe'
B = 'juizo_buracos'
N = 'juizo_negro'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
T = 'deus.ObjectTimerElapsedTime("golpe")'
PD = 'PrimitiveDrawing::'
OP = 'OpacityCapability::OpacityBehavior::SetValue'
IMG = {'p': 'assets/paraiso/deus/estrela_p.png', 'g': 'assets/paraiso/deus/estrela_g.png'}
ANG = 'ToRad(deus.juizo_ang)'
NEGRO = (f'{CX} + deus.juizo_negro_dx', f'{CY} + deus.juizo_negro_dy')
BRANCO = (f'{CX} + deus.juizo_branco_dx', f'{CY} + deus.juizo_branco_dy')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def no_feixe(x, y):
    """condições: o ponto (x, y) está na frente do olho e a menos de meia largura (+ folga) da linha do feixe."""
    dx, dy = f'({x} - deus.cx)', f'({y} - deus.cy)'
    return [cmp(f'{dx} * cos({ANG}) + {dy} * sin({ANG})', '>', '0'),
            cmp(f'abs({dy} * cos({ANG}) - {dx} * sin({ANG}))', '<', 'deus.juizo_largura / 2 + deus.juizo_folga')]


def desenho(nome, base, efeitos):
    t = {k: v for k, v in copy.deepcopy(base).items() if k not in ('name', 'persistentUuid', 'effects', 'variables')}
    t.update(name=nome, persistentUuid=ids('obj/' + nome), variables=[], effects=efeitos)
    return t


def estrelas():
    k_ceu = f'max(deus.estrela_ceu_min, max(bg_espaco.Opacity(), bg_ceu_alto.Opacity() * deus.estrela_ceu) / deus.estrela_op_max)'
    pisca = '(1 - deus.estrela_pisca * (1 + sin(TimeFromStart() * deus.estrela_pisca_vel + estrela.fase)) / 2)'
    cor = 'ToString(RandomInRange(deus.estrela_cor_min, deus.estrela_cor_max))'
    casa_y = (f'mod(estrela.hy + (luta_y0 - {CY}) * deus.estrela_parallax + {CH} / 2 + deus.estrela_margem, '
              f'{CH} + 2 * deus.estrela_margem) - {CH} / 2 - deus.estrela_margem')
    bx, by = f'(deus.cx - {CX})', f'(deus.cy - {CY})'
    mesmo = [num(R, 'id', '=', 'estrela.id')]
    return grupo('Estrelas', [
        ev([cbol('luta', True), X('SceneInstancesCount', '', d_, '>', '0'), X('SceneInstancesCount', '', E, '=', '0')], [], [
            repete('deus.estrela_qtd', [
                setn(d_, 'estrela_seq', '+', '1'), X('Create', '', E, '0', '0', '"Fundo"'),
                setn(E, 'id', '=', 'deus.estrela_seq'),
                setn(E, 'hx', '=', f'RandomFloatInRange(-{CW} / 2, {CW} / 2)'),
                setn(E, 'hy', '=', f'RandomFloatInRange(-{CH} / 2 - deus.estrela_margem, {CH} / 2 + deus.estrela_margem)'),
                setn(E, 'fase', '=', 'RandomFloatInRange(0, 6)'),
                setn(E, 'brilho', '=', 'RandomFloatInRange(deus.estrela_brilho_min, deus.estrela_op_max)'),
                setn(E, 'op', '=', '1'), X('ChangePlan', E, '=', 'deus.estrela_z'),
                X('ChangeColor', E, f'{cor} + ";" + {cor} + ";" + ToString(deus.estrela_cor_max)')],
                [ev([cmp('RandomFloat(1)', '<', 'deus.estrela_g_chance')], [anim(E, 'g')])])]),
        ev([X('SceneInstancesCount', '', d_, '>', '0')], [setn(d_, 'estrela_ceu_k', '=', k_ceu)]),
        # na casa (e invisíveis enquanto sugadas): descem com a subida e dão a volta
        ev([txt(E, 'est', 'vai', '!=')], [setn(E, 'x_', '=', 'estrela.hx'), setn(E, 'y_', '=', casa_y)]),
        ev([txt(E, 'est', 'volta')], [setn(E, 'op', '=', 'min(1, estrela.op + TimeDelta() / deus.estrela_volta)')],
           [ev([num(E, 'op', '>=', '1')], [sets(E, 'est', '')])]),
        ev([txt(E, 'est', 'some')], [setn(E, 'op', '=', '0')]),
        # sugadas: cada uma no seu atraso, aceleram até o olho com rastro
        cada(E, [txt(d_, 'etapa', 'suga'), txt(E, 'est', ''), timer(d_, 'golpe', '>', 'estrela.atraso')],
             [sets(E, 'est', 'vai'), setn(E, 'v', '=', '0'),
              X('Create', '', R, f'{CX} + estrela.x_', f'{CY} + estrela.y_', '""'), setn(R, 'id', '=', 'estrela.id'),
              X('ChangePlan', R, '=', 'deus.particula_z')]),
        cada(E, [txt(E, 'est', 'vai')],
             [setn(E, 'v', '+', 'deus.juizo_sugar_acel * TimeDelta()'),
              setn(E, 'dist', '=', f'max(1, sqrt(pow({bx} - estrela.x_, 2) + pow({by} - estrela.y_, 2)))'),
              setn(E, 'x_', '+', f'({bx} - estrela.x_) / estrela.dist * min(estrela.dist, estrela.v * TimeDelta())'),
              setn(E, 'y_', '+', f'({by} - estrela.y_) / estrela.dist * min(estrela.dist, estrela.v * TimeDelta())')],
             [ev(mesmo, [X('SetXY', R, '=', f'{CX} + estrela.x_', '=', f'{CY} + estrela.y_')]),
              ev([num(E, 'dist', '<', 'deus.juizo_sugar_chega')], [sets(E, 'est', 'some'), setn(E, 'op', '=', '0')],
                 [ev(mesmo, [X('Delete', R, '')])])]),
        # devolvidas por onde o feixe passou (e todas no fim do Juízo)
        cada(E, [txt(E, 'est', 'some'), txt(d_, 'etapa', 'feixe')], [], [
            ev([cmp(f'ToDeg(atan2(estrela.y_ - {by}, estrela.x_ - {bx}))', '>', 'deus.juizo_ang')], [sets(E, 'est', 'volta')])]),
        ev([X('SceneInstancesCount', '', d_, '>', '0'), bol(d_, 'juizo_ativo', False), txt(E, 'est', 'some')], [sets(E, 'est', 'volta')]),
        ev([X('SceneInstancesCount', '', d_, '>', '0'), bol(d_, 'juizo_ativo', False), txt(E, 'est', 'vai')],
           [sets(E, 'est', 'volta'), X('Delete', R, '')]),
        # desenho
        ev([X('SceneInstancesCount', '', d_, '>', '0')],
           [X('SetXY', E, '=', 'CameraCenterX("Fundo", 0) + estrela.x_ - estrela.Width() / 2', '=',
              'CameraCenterY("Fundo", 0) + estrela.y_ - estrela.Height() / 2'),
            X(OP, E, 'Opacity', '=', f'estrela.brilho * estrela.op * {pisca} * deus.estrela_ceu_k')]),
    ])


CAMADAS = ('Fundo', '')
# só o negro tem lente: no runtime todas as BulgePinch dividem o mesmo centro, então uma segunda lente puxaria a do negro
LENTES = ('Lente negra',)


def lente_forca(nome, valor):
    return [luz.acao_param_efeito_camada(f'"{c}"', f'"{nome}"', '"strength"', valor) for c in CAMADAS]


def desliga_lentes():
    return [a for n in LENTES for a in lente_forca(n, '0')]


def lentes(nome, buraco, forca):
    """a lente (BulgePinch) do buraco, no fundo e na camada do jogo: centro em fração da tela, raio em pixels."""
    acts = []
    for c in CAMADAS:
        for par, val in (('centerX', f'({CW} / 2 + deus.{buraco}_dx) / {CW}'), ('centerY', f'({CH} / 2 + deus.{buraco}_dy) / {CH}'),
                         ('radius', 'deus.juizo_lente_raio'), ('strength', forca)):
            acts.append(luz.acao_param_efeito_camada(f'"{c}"', f'"{nome}"', f'"{par}"', val))
    return acts


def juizo():
    golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'juizo')]
    em = lambda etapa: golpe + [txt(d_, 'etapa', etapa)]
    dist_branco = f'sqrt(pow(pato.CenterX() - ({BRANCO[0]}), 2) + pow(pato.CenterY() - ({BRANCO[1]}), 2))'
    fim_x = f'deus.cx + cos({ANG}) * deus.juizo_alcance'
    fim_y = f'deus.cy + sin({ANG}) * deus.juizo_alcance'
    return grupo('Juízo: o feixe', [
        ev(em(''),
           [sets(d_, 'etapa', 'vai'), zera(d_, 'golpe'), setb(d_, 'juizo_ativo', True),
            setn(d_, 'ox', '=', f'deus.cx - {CX}'), setn(d_, 'oy', '=', f'deus.cy - {CY}'),
            setb(d_, 'juizo_branco_ativo', False), setb(d_, 'juizo_revelado', False), setn(d_, 'juizo_ang', '=', '0'),
            X('Create', '', B, '0', '0', '""'), X('ChangePlan', B, '=', 'deus.feixe_z'),
            X('Create', '', N, '0', '0', '""'), X('ChangePlan', N, '=', 'deus.feixe_z'),
            anim('deus_anel_rosa', 'cintila'), som('som_luz.wav', 'deus.som_volume', 'deus.juizo_tom')]),
        ev(em('vai') + [timer(d_, 'golpe', '>', 'deus.juizo_ir')],
           [sets(d_, 'etapa', 'suga'), zera(d_, 'golpe'), setb(d_, 'juizo_branco_ativo', True),
            setn(E, 'atraso', '=', 'RandomFloatInRange(0, deus.juizo_sugar_espalha)'),
            som('som_luz.wav', 'deus.som_volume', 'deus.juizo_tom')]),
        ev(em('suga') + [timer(d_, 'golpe', '>', 'deus.juizo_sugar')],
           [sets(d_, 'etapa', 'aviso'), zera(d_, 'golpe'), anim('deus_olho', 'juizo'),
            som('som_luz.wav', 'deus.som_volume', 'deus.juizo_aviso_tom')]),
        ev(em('aviso') + [timer(d_, 'golpe', '>', 'deus.juizo_aviso')],
           [sets(d_, 'etapa', 'feixe'), zera(d_, 'golpe'), setn(d_, 'juizo_ang', '=', '0'),
            X('Create', '', F, '0', '0', '""'), X('ChangePlan', F, '=', 'deus.feixe_z'),
            som('som_luz.wav', 'deus.som_volume', '1')]),
        # o buraco branco leva o pato para o negro (antes do feixe, no mesmo quadro)
        ev([bol(d_, 'juizo_branco_ativo', True), bol('pato', 'morto', False), cmp(dist_branco, '<', 'deus.juizo_buraco_raio')],
           [X('SetXY', 'pato', '=', f'{NEGRO[0]} - pato.Width() / 2', '=', f'{NEGRO[1]} - pato.Height() / 2'),
            setn('pato', 'voo_vx', '=', '0'), setn('pato', 'voo_vy', '=', '0'),
            X('Create', '', 'escudo_quebra', BRANCO[0], BRANCO[1], '""'), X('ChangePlan', 'escudo_quebra', '=', 'deus.particula_z'),
            X('Create', '', 'escudo_quebra', NEGRO[0], NEGRO[1], '""'), X('ChangePlan', 'escudo_quebra', '=', 'deus.particula_z'),
            som('som_dash.wav', 'deus.som_volume', 'deus.juizo_tele_tom')]),
        # o feixe
        ev(em('feixe'),
           [setn(d_, 'juizo_ang', '=', f'-180 * min(1, {T} / deus.juizo_varrer)'),
            setn(d_, 'juizo_negro_ang', '=', f'ToDeg(atan2({NEGRO[1]} - deus.cy, {NEGRO[0]} - deus.cx))'),
            setn(d_, 'juizo_branco_ang', '=', f'ToDeg(atan2({BRANCO[1]} - deus.cy, {BRANCO[0]} - deus.cx))'),
            # quanto o feixe ainda cobre do buraco negro depois que o meio dele passou (meia largura + folga + raio)
            setn(d_, 'juizo_negro_livre', '=',
                 f'ToDeg(atan2(deus.juizo_largura / 2 + deus.juizo_folga + deus.juizo_buraco_raio, '
                 f'max(1, sqrt(pow({NEGRO[0]} - deus.cx, 2) + pow({NEGRO[1]} - deus.cy, 2)))))'),
            X(PD + 'OutlineColor', F, 'deus.juizo_cor'), X(PD + 'OutlineOpacity', F, '=', 'deus.juizo_feixe_op'),
            X(PD + 'LineV2', F, 'deus.cx', 'deus.cy', fim_x, fim_y, 'deus.juizo_largura'),
            X(PD + 'OutlineColor', F, 'deus.juizo_miolo_cor'),
            X(PD + 'LineV2', F, 'deus.cx', 'deus.cy', fim_x, fim_y, 'deus.juizo_largura * deus.juizo_miolo')],
           [ev([bol('pato', 'morto', False)] + no_feixe('pato.CenterX()', 'pato.CenterY()'),
               [setn('pato', 'vida', '=', '0'), sets('pato', 'ultimo_agressor', 'deus')]),
            cada('canalizador', [bol('canalizador', 'morto', False)], [], [
                ev(no_feixe('canalizador.CenterX()', 'canalizador.CenterY()'), [setn('canalizador', 'vida', '=', '0')])]),
            # o horizonte acende quando o feixe já saiu de cima do buraco negro: dali em diante ele é seguro
            ev([bol(d_, 'juizo_revelado', False), cmp('deus.juizo_ang', '<', 'deus.juizo_negro_ang - deus.juizo_negro_livre')],
               [setb(d_, 'juizo_revelado', True), zera(d_, 'horizonte'),
                som('som_luz.wav', 'deus.som_volume', 'deus.juizo_horizonte_tom')]),
            ev([bol(d_, 'juizo_branco_ativo', True), cmp('deus.juizo_ang', '<', 'deus.juizo_branco_ang')],
               [setb(d_, 'juizo_branco_ativo', False),
                X('Create', '', 'escudo_quebra', BRANCO[0], BRANCO[1], '""'), X('ChangePlan', 'escudo_quebra', '=', 'deus.particula_z')]),
            ev([timer(d_, 'golpe', '>', 'deus.juizo_varrer')],
               [sets(d_, 'etapa', 'fecha'), zera(d_, 'golpe'), X('Delete', F, ''), anim('deus_olho', 'idle')])]),
        # os buracos
        ev([bol(d_, 'juizo_ativo', True), bol(d_, 'morto', False)],
           [setn(d_, 'juizo_flare', '=', '0'), setn(d_, 'juizo_negro_k', '=', 'deus.juizo_negro_vis')],
           [ev([bol(d_, 'juizo_revelado', True)],
               [setn(d_, 'juizo_flare', '=', 'max(0, 1 - deus.ObjectTimerElapsedTime("horizonte") / deus.juizo_horizonte_t)'),
                setn(d_, 'juizo_negro_k', '=', 'max(deus.juizo_negro_resto, deus.juizo_flare)')]),
            # o negro: disco preto com um aro fino de luz (sem halo); o que o faz parecer um buraco negro é a lente
            ev([],
               [X(PD + 'FillColor', N, 'deus.juizo_negro_cor'), X(PD + 'FillOpacity', N, '=', 'deus.juizo_buraco_op * deus.juizo_negro_k'),
                X(PD + 'OutlineColor', N, 'deus.juizo_horizonte_cor'),
                X(PD + 'OutlineOpacity', N, '=', 'deus.juizo_buraco_op * deus.juizo_negro_k'),
                X(PD + 'OutlineSize', N, '=', 'deus.juizo_horizonte_esp * (1 + deus.juizo_flare)'),
                X(PD + 'Circle', N, NEGRO[0], NEGRO[1], 'deus.juizo_buraco_raio')]
               + lentes('Lente negra', 'juizo_negro', 'deus.juizo_lente_negra')),
            ev([bol(d_, 'juizo_branco_ativo', True)],
               [X(PD + 'FillColor', B, 'deus.juizo_branco_cor'), X(PD + 'FillOpacity', B, '=', 'deus.juizo_buraco_op'),
                X(PD + 'OutlineColor', B, 'deus.juizo_horizonte_cor'), X(PD + 'OutlineOpacity', B, '=', 'deus.juizo_buraco_op * deus.juizo_flare'),
                X(PD + 'OutlineSize', B, '=', 'deus.juizo_horizonte_esp * (1 + deus.juizo_flare)'),
                X(PD + 'Circle', B, BRANCO[0], BRANCO[1], 'deus.juizo_buraco_raio * (1 + deus.juizo_flare)')])]),
        ev([X('SceneInstancesCount', '', d_, '>', '0'), bol(d_, 'juizo_ativo', False)], desliga_lentes()),
        # fim
        ev(em('fecha') + [timer(d_, 'golpe', '>', 'deus.juizo_fecha')],
           [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), setb(d_, 'juizo_ativo', False),
            setb(d_, 'juizo_branco_ativo', False), setn(d_, 'juizo_volta_em', '=', 'TimeFromStart() + deus.juizo_recarga'),
            X('Delete', B, ''), X('Delete', N, ''), X('Delete', R, ''), anim('deus_anel_rosa', 'idle')] + desliga_lentes()),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('juizo_recarga', 30), ('juizo_volta_em', 0), ('juizo_ativo', False), ('juizo_baixo', 150), ('juizo_ir_vel', 3),
        ('juizo_ir', 1.2), ('juizo_sugar', 2.4), ('juizo_sugar_espalha', 1), ('juizo_sugar_acel', 2600),
        ('juizo_sugar_chega', 40), ('juizo_aviso', 1), ('juizo_aviso_tom', 1.4), ('juizo_tom', 0.6), ('juizo_varrer', 3.5),
        ('juizo_fecha', 0.8), ('juizo_ang', 0), ('juizo_alcance', 3000), ('juizo_largura', 120), ('juizo_miolo', 0.35),
        ('juizo_folga', 16), ('juizo_cor', '255;230;170'), ('juizo_miolo_cor', '255;255;255'), ('juizo_feixe_op', 235),
        ('juizo_negro_dx', 700), ('juizo_negro_dy', -180), ('juizo_branco_dx', -700), ('juizo_branco_dy', -180),
        ('juizo_buraco_raio', 70), ('juizo_buraco_op', 235), ('juizo_branco_cor', '255;255;255'),
        ('juizo_negro_cor', '0;0;0'), ('juizo_lente_negra', 0.5), ('juizo_lente_raio', 260),
        ('juizo_horizonte_cor', '255;232;200'), ('juizo_horizonte_t', 1.6), ('juizo_horizonte_esp', 3),
        ('juizo_horizonte_tom', 0.8), ('juizo_tele_tom', 1.3), ('juizo_negro_vis', 0.06), ('juizo_negro_resto', 1),
        ('juizo_revelado', False), ('juizo_branco_ativo', False), ('juizo_negro_ang', 0), ('juizo_branco_ang', 0),
        ('juizo_flare', 0), ('juizo_negro_k', 0), ('juizo_negro_livre', 0), ('estrela_ceu_min', 0.55),
        ('estrela_qtd', 150), ('estrela_seq', 0), ('estrela_margem', 40), ('estrela_parallax', 0.45),
        ('estrela_pisca', 0.5), ('estrela_pisca_vel', 3), ('estrela_ceu', 0.35), ('estrela_ceu_k', 0),
        ('estrela_volta', 0.6), ('estrela_z', 12), ('estrela_g_chance', 0.06), ('estrela_brilho_min', 120),
        ('estrela_op_max', 255), ('estrela_cor_min', 190), ('estrela_cor_max', 255)])

    # objetos
    poe_recursos(d, list(IMG.values()))
    est = sprite(ids, E, [(k, [v], 1, 0.1, False) for k, v in IMG.items()],
                 [var(ids, E, n, v) for n, v in (('hx', 0), ('hy', 0), ('x_', 0), ('y_', 0), ('v', 0), ('atraso', 0),
                                                 ('fase', 0), ('brilho', 0), ('est', ''), ('op', 1), ('id', 0), ('dist', 0))])
    poe_objeto(d, est, 'inimigos/chefe')
    poe_objeto(d, emissor(o['explosao_faiscas'], R, rendererType='Point', rendererParam1=3, rendererParam2=1, tank=-1,
                          flow=90, maxParticleNb=60, emitterAngleB=360, emitterForceMin=0, emitterForceMax=30,
                          particleLifeTimeMin=0.2, particleLifeTimeMax=0.45, particleColor1='255;255;255',
                          particleColor2='170;150;255', particleAlpha1=230, particleAlpha2=0, particleSize1=100,
                          particleSize2=20, particleGravityY=0, zoneRadius=2, additive=True, destroyWhenNoParticles=False),
               'inimigos/chefe')
    pa = o['pulso_anel']
    poe_objeto(d, desenho(F, pa, [efeito('Glow', 'Effect', {'distance': 30, 'innerStrength': 4, 'outerStrength': 10},
                                         {'color': '255;220;150'}),
                                  efeito('AdvancedBloom', 'Brilho', {'bloomScale': 1.6, 'blur': 10, 'brightness': 1.3,
                                                                     'padding': 80, 'quality': 6, 'threshold': 0.2}, {})]),
               'inimigos/chefe')
    poe_objeto(d, desenho(B, pa, [efeito('Glow', 'Effect', {'distance': 30, 'innerStrength': 3, 'outerStrength': 8},
                                         {'color': '255;250;235'}),
                                  efeito('AdvancedBloom', 'Brilho', {'bloomScale': 1.6, 'blur': 10, 'brightness': 1.4,
                                                                     'padding': 80, 'quality': 6, 'threshold': 0.2}, {})]),
               'inimigos/chefe')
    poe_objeto(d, desenho(N, pa, []), 'inimigos/chefe')
    # as lentes dos buracos, desligadas (strength 0) até o Juízo
    for l in cena(d, 'Paraiso')['layers']:
        if l['name'] in CAMADAS:
            l.setdefault('effects', []).extend(
                efeito('BulgePinch', n, {'centerX': 0.5, 'centerY': 0.5, 'radius': 260, 'strength': 0}) for n in LENTES)

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    # sai o Juízo antigo (e o aviso da t162) do anel rosa
    rosa = acha(deus['events'], 'Anel rosa: amor')
    rosa['events'] = [e for e in rosa['events']
                      if '"deus", "golpe", "=", "\\"juizo\\""' not in tx(e['conditions'])
                      and not (e['conditions'] == [] and ('juizo_carga' in tx(e['actions'])))]
    for e in rosa['events']:
        for a in e['actions']:
            if a['type']['value'] == PD + 'LineV2' and a['parameters'][0] == 'laco_amor':
                a['parameters'][5] = 'deus.laco_espessura'
    k = deus['events'].index(rosa)
    deus['events'][k + 1:k + 1] = [juizo(), estrelas()]

    # Corpo: para embaixo no meio (e a fase final não puxa para o pato enquanto isso)
    corpo = acha(deus['events'], 'Corpo')
    for e in corpo['events']:
        if 'deus.final_distancia' in tx(e['actions']):
            e['conditions'].append(bol(d_, 'juizo_ativo', False))
    k = next(i for i, e in enumerate(corpo['events']) if '"deus", "pupila_ox", "+"' in tx(e['actions']))
    km = 'min(1, deus.juizo_ir_vel * TimeDelta())'
    corpo['events'].insert(k, ev([bol(d_, 'juizo_ativo', True), bol(d_, 'morto', False), bol(d_, 'investindo', False)],
                                 [setn(d_, 'ox', '+', f'(0 - deus.ox) * {km}'),
                                  setn(d_, 'oy', '+', f'({CH} / 2 - deus.juizo_baixo - deus.oy) * {km}'),
                                  setn(d_, 'cx', '=', f'{CX} + deus.ox'), setn(d_, 'cy', '=', f'{CY} + deus.oy')]))

    # recarga: o sorteio pula o Juízo até juizo_volta_em
    esc = acha(deus['events'], 'Escolha do golpe')
    sorteio = next(e for e in todos(esc['events']) if any(
        '"deus", "golpe", "=", "\\"juizo\\""' in tx(f.get('actions', [])) for f in e.get('events', [])))
    k = next(i for i, f in enumerate(sorteio['events']) if '"deus", "golpe", "="' in tx(f['actions']))
    sorteio['events'].insert(k, ev([num(d_, 'sorteio', '=', '4'), cmp('TimeFromStart()', '<', 'deus.juizo_volta_em')],
                                   [setn(d_, 'sorteio', '=', 'mod(deus.sorteio, deus.golpes_max) + 1')]))

    # limpeza
    troca = next(e for e in todos(acha(deus['events'], 'Fases')['events'])
                 if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
    morte = next(e for e in acha(deus['events'], 'Morte')['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
    for e in (troca, morte):
        e['actions'] += [setb(d_, 'juizo_ativo', False), setb(d_, 'juizo_branco_ativo', False),
                         X('Delete', F, ''), X('Delete', B, ''), X('Delete', N, ''), X('Delete', R, '')] + desliga_lentes()


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, F) is not None, 't164')
