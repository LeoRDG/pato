"""Tarefa 155: o golpe do anel azul deixa de ser o piscar e vira a investida.

Deus sai por baixo da tela (investida_vel_sai) e, de fora dela, investe contra o pato investida_total vezes
(sorteado entre investida_min e investida_max). Cada investida:
- mira: um caminho avisado (investida_trilha, Shape Painter com Glow) sai dele e segue o pato por investida_mira,
  com uma faixa da largura que machuca (investida_raio * 2);
- trava: o caminho para de seguir e pisca (investida_pisca) por investida_trava;
- corre: ele acelera pelo caminho (investida_vel_ini, investida_acel, até investida_vel_max) deixando um rastro de
  partículas (investida_rastro), fere o pato que estiver a menos de investida_raio (investida_dano) e sai pelo outro
  lado (investida_fora além da borda), de onde mira a próxima.
Na corrida os raios da aura giram mais rápido (aura_giro_mult = 1 + investida_giro * velocidade / máxima). No fim
ele volta ao lugar de sempre (investida_volta). Enquanto investe, a posição dele é guardada em relação à câmera
(deus.ox, deus.oy), para a subida não o deixar para trás, e a pupila vai junto sem atraso.
O piscar (halos, escuro) sai; troca de fase e morte limpam a investida.
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t155_investida.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor

ids = Ids('t155')
d_ = 'deus'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
T = 'deus.ObjectTimerElapsedTime("golpe")'
PD = 'PrimitiveDrawing::'
TR = 'investida_trilha'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def trilha(k):
    fim_x, fim_y = 'deus.cx + cos(deus.investida_a) * deus.investida_alcance', 'deus.cy + sin(deus.investida_a) * deus.investida_alcance'
    return [X(PD + 'OutlineColor', TR, 'deus.investida_trilha_cor'),
            X(PD + 'OutlineOpacity', TR, '=', f'deus.investida_faixa_op * {k}'),
            X(PD + 'LineV2', TR, 'deus.cx', 'deus.cy', fim_x, fim_y, 'deus.investida_raio * 2'),
            X(PD + 'OutlineOpacity', TR, '=', f'deus.investida_trilha_op * {k}'),
            X(PD + 'LineV2', TR, 'deus.cx', 'deus.cy', fim_x, fim_y, 'deus.investida_trilha_larg')]


def investida():
    golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'investida')]
    em = lambda etapa: golpe + [txt(d_, 'etapa', etapa)]
    giro = '1 + deus.investida_giro * deus.investida_v / deus.investida_vel_max'
    return grupo('Anel azul: investida', [
        ev(em(''),
           [sets(d_, 'etapa', 'sai'), zera(d_, 'golpe'), setb(d_, 'investindo', True),
            setn(d_, 'ox', '=', f'deus.cx - {CX}'), setn(d_, 'oy', '=', f'deus.cy - {CY}'),
            setn(d_, 'investida_feitas', '=', '0'),
            setn(d_, 'investida_total', '=', 'RandomInRange(deus.investida_min, deus.investida_max)'),
            setn(d_, 'investida_v', '=', 'deus.investida_vel_sai'),
            X('Create', '', TR, '0', '0', '""'), X('ChangePlan', TR, '=', 'deus.feixe_z'),
            anim('deus_anel_azul', 'cintila'), som('som_luz.wav', 'deus.som_volume')]),
        # sai por baixo
        ev(em('sai'),
           [setn(d_, 'oy', '+', 'deus.investida_vel_sai * TimeDelta()'), setn(d_, 'aura_giro_mult', '=', giro)],
           [ev([cmp('deus.oy', '>', f'{CH} / 2 + deus.investida_fora')],
               [sets(d_, 'etapa', 'mira'), zera(d_, 'golpe')])]),
        # acabou: volta ao lugar
        ev(em('mira') + [cmp('deus.investida_feitas', '>=', 'deus.investida_total')],
           [sets(d_, 'etapa', 'volta'), zera(d_, 'golpe'), setb(d_, 'investindo', False), X('Delete', TR, '')]),
        # mira seguindo o pato
        ev(em('mira'),
           [setn(d_, 'aura_giro_mult', '=', '1'),
            setn(d_, 'investida_a', '=', 'atan2(pato.CenterY() - deus.cy, pato.CenterX() - deus.cx)')]
           + trilha(f'min(1, {T} / deus.investida_mira)'),
           [ev([timer(d_, 'golpe', '>', 'deus.investida_mira')],
               [sets(d_, 'etapa', 'trava'), zera(d_, 'golpe'),
                setn(d_, 'investida_dx', '=', 'cos(deus.investida_a)'), setn(d_, 'investida_dy', '=', 'sin(deus.investida_a)'),
                som('som_luz.wav', 'deus.som_volume', 'deus.investida_tom')])]),
        # trava piscando
        ev(em('trava'), trilha(f'mod(floor({T} * deus.investida_pisca) + 1, 2)'),
           [ev([timer(d_, 'golpe', '>', 'deus.investida_trava')],
               [sets(d_, 'etapa', 'corre'), zera(d_, 'golpe'), setn(d_, 'investida_v', '=', 'deus.investida_vel_ini'),
                X('Create', '', 'investida_rastro', 'deus.cx', 'deus.cy', '""'),
                X('SetAngle', 'investida_rastro', '=', 'ToDeg(deus.investida_a) + 180'),
                X('ChangePlan', 'investida_rastro', '=', 'deus.particula_z'),
                som('som_dash.wav', 'deus.som_volume')])]),
        # corre acelerando
        ev(em('corre'),
           [setn(d_, 'investida_v', '=', 'min(deus.investida_vel_max, deus.investida_v + deus.investida_acel * TimeDelta())'),
            setn(d_, 'ox', '+', 'deus.investida_dx * deus.investida_v * TimeDelta()'),
            setn(d_, 'oy', '+', 'deus.investida_dy * deus.investida_v * TimeDelta()'),
            setn(d_, 'aura_giro_mult', '=', giro),
            X('SetXY', 'investida_rastro', '=', f'{CX} + deus.ox', '=', f'{CY} + deus.oy')],
           [ev([bol('pato', 'invencivel', False), bol('pato', 'morto', False),
                cmp(f'sqrt(pow(pato.CenterX() - ({CX} + deus.ox), 2) + pow(pato.CenterY() - ({CY} + deus.oy), 2))', '<', 'deus.investida_raio')],
               [setn('pato', 'vida', '-', 'deus.investida_dano'), setb('pato', 'invencivel', True), zera('pato', 'iframes'),
                sets('pato', 'ultimo_agressor', 'deus')]),
            ev([cmp('deus.ox * deus.investida_dx + deus.oy * deus.investida_dy', '>', '0'),
                cmp(f'max(abs(deus.ox) - {CW} / 2, abs(deus.oy) - {CH} / 2)', '>', 'deus.investida_fora')],
               [X('Delete', 'investida_rastro', ''), setn(d_, 'investida_feitas', '+', '1'), zera(d_, 'golpe'),
                sets(d_, 'etapa', 'mira')])]),
        # volta
        ev(em('volta'), [setn(d_, 'aura_giro_mult', '=', '1')],
           [ev([timer(d_, 'golpe', '>', 'deus.investida_volta')],
               [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), anim('deus_anel_azul', 'idle')])]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('investindo', False), ('ox', 0), ('oy', 0), ('pupila_ox', 0), ('pupila_oy', 0), ('aura_giro_mult', 1),
        ('investida_min', 4), ('investida_max', 5), ('investida_total', 0), ('investida_feitas', 0),
        ('investida_fora', 260), ('investida_vel_sai', 900), ('investida_mira', 0.9), ('investida_trava', 0.35),
        ('investida_pisca', 12), ('investida_vel_ini', 300), ('investida_acel', 3500), ('investida_vel_max', 2200),
        ('investida_v', 0), ('investida_a', 0), ('investida_dx', 0), ('investida_dy', 0), ('investida_raio', 100),
        ('investida_dano', 30), ('investida_giro', 12), ('investida_volta', 1.5), ('investida_alcance', 3000),
        ('investida_trilha_cor', '255;90;90'), ('investida_trilha_op', 230), ('investida_faixa_op', 60),
        ('investida_trilha_larg', 3), ('investida_tom', 1.3)])
    t = {k: v for k, v in o['laco_amor'].items() if k not in ('name', 'persistentUuid', 'effects', 'variables')}
    t.update(name=TR, persistentUuid=ids('obj/' + TR), variables=[], fillOpacity=0, absoluteCoordinates=True,
             clearBetweenFrames=True, outlineColor={'r': 255, 'g': 90, 'b': 90},
             effects=[efeito('Glow', 'Effect', {'distance': 15, 'innerStrength': 1, 'outerStrength': 4}, {'color': '255;80;80'})])
    poe_objeto(d, t, 'inimigos/chefe')
    poe_objeto(d, emissor(o['explosao_faiscas'], 'investida_rastro', rendererType='Point', rendererParam1=4,
                          rendererParam2=1, tank=-1, flow=140, maxParticleNb=200, emitterAngleB=40, emitterForceMin=80,
                          emitterForceMax=260, particleLifeTimeMin=0.3, particleLifeTimeMax=0.7,
                          particleColor1='200;230;255', particleColor2='90;150;255', particleAlpha1=220,
                          particleAlpha2=0, particleSize1=120, particleSize2=30, particleGravityY=0, zoneRadius=40,
                          additive=True, destroyWhenNoParticles=False), 'inimigos/chefe')

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Anel azul: piscar')
    deus['events'][k] = investida()
    # escolha: o golpe 2 passa a ser a investida
    for e in todos(acha(deus['events'], 'Escolha do golpe')['events']):
        for a in e.get('actions', []):
            if a['parameters'][:4] == [d_, 'golpe', '=', '"piscar"']:
                a['parameters'][3] = '"investida"'
    # corpo: na investida a posição vem de ox/oy (em relação à câmera) e a pupila vai junto
    corpo = acha(deus['events'], 'Corpo')
    # pupila: suaviza o deslocamento em relação ao centro, não a posição no mundo
    for a in corpo['events'][0]['actions']:
        for eixo, f in (('x', 'cos'), ('y', 'sin')):
            if a['parameters'][:3] == [d_, 'p' + eixo, '+']:
                a['parameters'][2:4] = ['=', f'deus.c{eixo} + deus.pupila_o{eixo}']
    acts = corpo['events'][0]['actions']
    k = next(i for i, a in enumerate(acts) if a['parameters'][:2] == [d_, 'px'])
    acts[k:k] = [setn(d_, f'pupila_o{eixo}', '+', f'({f}(deus.olhar_ang) * deus.pupila_alcance - deus.pupila_o{eixo}) * min(1, deus.pupila_suave * TimeDelta())')
                 for eixo, f in (('x', 'cos'), ('y', 'sin'))]
    corpo['events'].insert(1, ev(
        [bol(d_, 'investindo', True), bol(d_, 'morto', False)],
        [setn(d_, 'cx', '=', f'{CX} + deus.ox'), setn(d_, 'cy', '=', f'{CY} + deus.oy'),
         setn(d_, 'olhar_ang', '=', 'atan2(pato.CenterY() - deus.cy, pato.CenterX() - deus.cx)'),
         setn(d_, 'pupila_ox', '=', 'cos(deus.olhar_ang) * deus.pupila_alcance'),
         setn(d_, 'pupila_oy', '=', 'sin(deus.olhar_ang) * deus.pupila_alcance'),
         setn(d_, 'px', '=', 'deus.cx + deus.pupila_ox'), setn(d_, 'py', '=', 'deus.cy + deus.pupila_oy')]))
    # raios giram mais rápido na corrida
    for e in todos(acha(deus['events'], 'Aura desenhada')['events']):
        for a in e.get('actions', []):
            if a['parameters'][:3] == [d_, 'aura_raios_ang', '+'] and a['parameters'][3] == 'deus.aura_giro * TimeDelta()':
                a['parameters'][3] = 'deus.aura_giro * deus.aura_giro_mult * TimeDelta()'
    # limpeza
    troca = next(e for e in todos(acha(deus['events'], 'Fases')['events'])
                 if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
    morte = next(e for e in acha(deus['events'], 'Morte')['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
    for e in (troca, morte):
        e['actions'] += [setb(d_, 'investindo', False), setn(d_, 'aura_giro_mult', '=', '1'),
                         X('Delete', 'investida_rastro', ''), X('Delete', TR, '')]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, TR) is not None, 't155')
