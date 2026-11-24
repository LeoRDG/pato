"""Tarefa 151: o golpe do anel de ouro vira um pulso radial canalizado.

- Carga (etapa "carrega", deus.pulso_carga): o olho canaliza; conv_qtd emissores de partículas (conv_luz) em volta do
  olho (conv_raio, girando conv_giro) atiram luz para ele, cada vez mais rápida e densa até o pulso (conv_vel_min ->
  conv_vel_max, conv_fluxo_min -> conv_fluxo_max). A luz do olho cresce e as pedras fazem sombra.
- Pedras: no começo da carga deus.fragmento_qtd nascem logo acima da tela e mais uma a cada fragmento_intervalo;
  descem devagar e sem parar (fragmento.vy agora é a velocidade na tela, entre fragmento_vel_min e
  fragmento_vel_max, descontando a subida da câmera).
- Pulso (etapa "pulso"): um anel desenhado (pulso_anel, Shape Painter com Glow forte, como o laser) cresce do olho
  a pulso_vel até olhar_alcance, com dois anéis de rastro; a luz do olho (pulso_luz_cor) acompanha o anel
  (raio pulso_r + pulso_luz_margem), clareando tudo por onde ele passa, o anel ganha bloom e o céu clareia
  (pulso_ambiente) até o pulso acabar. As pedras que a frente do pulso alcança quebram
  (pedra_estilhaco). Quando a frente chega no pato, ele toma olhar_dano, a não ser que estivesse atrás de uma pedra
  no momento em que o pulso saiu (raio do olho até o pato).
- O feixe que varria (mira/trava/varre) sai; a troca de fase e a morte limpam conv_luz e pulso_anel.
Só adiciona variáveis; as que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t151_pulso.py
"""
from gd_mig import *
import gd_luz as luz
from t149_redoma_e_particulas import emissor

ids = Ids('t151')
d_ = 'deus'
CX, CY, CW, CH = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)', 'CameraWidth("", 0)', 'CameraHeight("", 0)'
TOPO = f'{CY} - {CH} / 2'
P = 'min(1, deus.ObjectTimerElapsedTime("golpe") / deus.pulso_carga)'
DIST_PATO = 'sqrt(pow(pato.CenterX() - deus.pulso_x, 2) + pow(pato.CenterY() - deus.pulso_y, 2))'
DIST_PEDRA = 'sqrt(pow(fragmento.CenterX() - deus.pulso_x, 2) + pow(fragmento.CenterY() - deus.pulso_y, 2))'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def pedra(y):
    return [X('Create', '', 'fragmento',
              f'RandomInRange({CX} - {CW} / 2 + deus.fragmento_folga, {CX} + {CW} / 2 - deus.fragmento_folga)', y, '""'),
            X('AnimatableCapability::AnimatableBehavior::SetName', 'fragmento', 'Animation', '=', '"f" + ToString(RandomInRange(1, 3))'),
            setn('fragmento', 'vy', '=', 'RandomFloatInRange(deus.fragmento_vel_min, deus.fragmento_vel_max)'),
            X('OpacityCapability::OpacityBehavior::SetValue', 'fragmento', 'Opacity', '=', '0'),
            X('ChangePlan', 'fragmento', '=', 'deus.fragmento_z')]


def pulso(antigos):
    golpe = [bol(d_, 'morto', False), txt(d_, 'estado', 'atacar'), txt(d_, 'golpe', 'olhar')]
    carrega = golpe + [txt(d_, 'etapa', 'carrega')]
    no_pulso = golpe + [txt(d_, 'etapa', 'pulso')]
    pe = 'ParticleSystem::'
    ang = 'deus.conv_ang + ToRad(conv_luz.k * 360 / deus.conv_qtd)'
    return grupo('Anel de ouro: o pulso', antigos + [
        # começo da carga
        ev(golpe + [txt(d_, 'etapa', '')],
           [sets(d_, 'etapa', 'carrega'), zera(d_, 'golpe'), zera(d_, 'fragmento'), setn(d_, 'i', '=', '0'),
            luz.acao_cor_luz('luz_olhar', 'deus.olhar_cor'), anim('deus_anel_ouro', 'cintila'),
            anim('deus_olho', 'carregar'), som('som_luz.wav', 'deus.som_volume'), X('Delete', 'conv_luz', '')],
           [repete('deus.fragmento_qtd', pedra(f'{TOPO} - RandomInRange(0, deus.fragmento_acima)')),
            repete('deus.conv_qtd', [X('Create', '', 'conv_luz', 'deus.px', 'deus.py', '""'),
                                     setn('conv_luz', 'k', '=', 'deus.i'), setn(d_, 'i', '+', '1'),
                                     X('ChangePlan', 'conv_luz', '=', 'deus.particula_z')])]),
        # carga: luz cresce, partículas convergem cada vez mais rápido, pedras continuam nascendo
        ev(carrega,
           [luz.acao_raio_luz('luz_olhar', f'deus.olhar_raio_idle + (deus.olhar_raio_luz - deus.olhar_raio_idle) * {P}'),
            setn(d_, 'conv_ang', '+', 'deus.conv_giro * TimeDelta()'),
            setn(d_, 'conv_v', '=', f'deus.conv_vel_min + (deus.conv_vel_max - deus.conv_vel_min) * pow({P}, 2)')],
           [cada('conv_luz', [],
                 [X('SetXY', 'conv_luz', '=', f'deus.px + cos({ang}) * deus.conv_raio', '=', f'deus.py + sin({ang}) * deus.conv_raio'),
                  X('SetAngle', 'conv_luz', '=',
                    'ToDeg(atan2(deus.py - deus.conv_raio * subida_vel / deus.conv_v - conv_luz.Y(), deus.px - conv_luz.X()))'),
                  X(pe + 'EmitterForceMin', 'conv_luz', '=', 'deus.conv_v'),
                  X(pe + 'EmitterForceMax', 'conv_luz', '=', 'deus.conv_v'),
                  X(pe + 'ParticleLifeTimeMin', 'conv_luz', '=', 'deus.conv_raio / deus.conv_v * deus.conv_vida_min'),
                  X(pe + 'ParticleLifeTimeMax', 'conv_luz', '=', 'deus.conv_raio / deus.conv_v'),
                  X(pe + 'SetFlow', 'conv_luz', '=', f'deus.conv_fluxo_min + (deus.conv_fluxo_max - deus.conv_fluxo_min) * {P}')]),
            ev([timer(d_, 'fragmento', '>', 'deus.fragmento_intervalo')],
               [zera(d_, 'fragmento')] + pedra(f'{TOPO} - deus.fragmento_folga'))]),
        # solta o pulso
        ev(carrega + [timer(d_, 'golpe', '>', 'deus.pulso_carga')],
           [sets(d_, 'etapa', 'pulso'), zera(d_, 'golpe'), setn(d_, 'pulso_r', '=', '0'), setb(d_, 'pulso_acertou', False),
            setn(d_, 'pulso_x', '=', 'deus.px'), setn(d_, 'pulso_y', '=', 'deus.py'), X('Delete', 'conv_luz', ''),
            X('Create', '', 'pulso_anel', '0', '0', '""'), X('ChangePlan', 'pulso_anel', '=', 'deus.feixe_z'),
            X('Create', '', 'pulso_brilho', 'deus.px', 'deus.py', '""'), X('ChangePlan', 'pulso_brilho', '=', 'deus.particula_z'),
            luz.acao_cor_luz('luz_olhar', 'deus.pulso_luz_cor'), luz.acao_luz_ambiente('"Luz"', 'deus.pulso_ambiente'),
            anim(d_, 'contrai'), som('som_luz.wav', 'deus.som_volume', 'deus.pulso_tom')],
           [ev([], [setb('pato', 'na_sombra', False)], [
               ev([X('RaycastToPosition', 'fragmento', 'deus.pulso_x', 'deus.pulso_y', 'pato.CenterX()', 'pato.CenterY()',
                     'olhar_rx', 'olhar_ry', '')], [setb('pato', 'na_sombra', True)])])]),
        # o pulso cresce
        ev(no_pulso,
           [setn(d_, 'pulso_x', '=', 'deus.px'), setn(d_, 'pulso_y', '=', 'deus.py'),
            setn(d_, 'pulso_r', '+', 'deus.pulso_vel * TimeDelta()'),
            luz.acao_raio_luz('luz_olhar', 'deus.pulso_r + deus.pulso_luz_margem'),
            X('PrimitiveDrawing::OutlineOpacity', 'pulso_anel', '=', 'deus.pulso_opacidade * max(0, 1 - deus.pulso_r / deus.olhar_alcance)'),
            X('PrimitiveDrawing::OutlineColor', 'pulso_anel', 'deus.pulso_rastro_cor'),
            X('PrimitiveDrawing::OutlineSize', 'pulso_anel', '=', 'deus.pulso_rastro_espessura'),
            X('PrimitiveDrawing::Circle', 'pulso_anel', 'deus.pulso_x', 'deus.pulso_y', 'max(1, deus.pulso_r - deus.pulso_rastro_passo * 2)'),
            X('PrimitiveDrawing::Circle', 'pulso_anel', 'deus.pulso_x', 'deus.pulso_y', 'max(1, deus.pulso_r - deus.pulso_rastro_passo)'),
            X('PrimitiveDrawing::OutlineColor', 'pulso_anel', 'deus.pulso_cor'),
            X('PrimitiveDrawing::OutlineSize', 'pulso_anel', '=', 'deus.pulso_espessura'),
            X('PrimitiveDrawing::Circle', 'pulso_anel', 'deus.pulso_x', 'deus.pulso_y', 'deus.pulso_r')],
           [cada('fragmento', [cmp(DIST_PEDRA, '<=', 'deus.pulso_r')],
                 [X('Create', '', 'pedra_estilhaco', 'fragmento.CenterX()', 'fragmento.CenterY()', '""'),
                  X('ChangePlan', 'pedra_estilhaco', '=', 'deus.particula_z'), X('Delete', 'fragmento', '')]),
            ev([bol(d_, 'pulso_acertou', False), cmp(DIST_PATO, '<=', 'deus.pulso_r')],
               [setb(d_, 'pulso_acertou', True)],
               [ev([bol('pato', 'na_sombra', False), bol('pato', 'invencivel', False), bol('pato', 'morto', False)],
                   [setn('pato', 'vida', '-', 'deus.olhar_dano'), setb('pato', 'invencivel', True),
                    zera('pato', 'iframes'), sets('pato', 'ultimo_agressor', 'deus')])]),
            ev([cmp('deus.pulso_r', '>', 'deus.olhar_alcance')],
               [sets(d_, 'etapa', ''), sets(d_, 'estado', 'fim_golpe'), zera(d_, 'estado'), X('Delete', 'pulso_anel', ''),
                luz.acao_cor_luz('luz_olhar', 'deus.olhar_cor'), luz.acao_luz_ambiente('"Luz"', 'luz_ambiente_normal'),
                anim(d_, 'idle'), anim('deus_olho', 'idle'), anim('deus_anel_ouro', 'idle')])]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('pulso_carga', 6), ('pulso_vel', 1800), ('pulso_r', 0), ('pulso_x', 0), ('pulso_y', 0),
        ('pulso_acertou', False), ('pulso_espessura', 14), ('pulso_cor', '255;240;190'),
        ('pulso_rastro_cor', '255;190;80'), ('pulso_rastro_passo', 50), ('pulso_rastro_espessura', 6),
        ('pulso_opacidade', 255), ('pulso_tom', 0.7), ('pulso_luz_margem', 250), ('pulso_luz_cor', '255;250;225'),
        ('pulso_ambiente', '235;225;200'),
        ('conv_qtd', 10), ('conv_raio', 420), ('conv_vel_min', 140), ('conv_vel_max', 1100), ('conv_vida_min', 0.85),
        ('conv_fluxo_min', 6), ('conv_fluxo_max', 45), ('conv_giro', 0.5), ('conv_ang', 0), ('conv_v', 140)])
    base = o['explosao_faiscas']
    conv = emissor(base, 'conv_luz', rendererType='Point', rendererParam1=3, rendererParam2=1, tank=-1, flow=6,
                   maxParticleNb=150, emitterAngleB=14, emitterForceMin=140, emitterForceMax=140,
                   particleLifeTimeMin=2.5, particleLifeTimeMax=3, particleColor1='255;236;170',
                   particleColor2='255;255;255', particleAlpha1=70, particleAlpha2=255, particleSize1=70,
                   particleSize2=130, particleGravityY=0, zoneRadius=26, additive=True, destroyWhenNoParticles=False)
    conv['variables'] = [var(ids, 'conv_luz', 'k', 0)]
    poe_objeto(d, conv, 'inimigos/chefe')
    poe_objeto(d, emissor(base, 'pedra_estilhaco', rendererType='Point', rendererParam1=4, rendererParam2=1, tank=22,
                          flow=3000, maxParticleNb=40, emitterAngleB=360, emitterForceMin=120, emitterForceMax=380,
                          particleLifeTimeMin=0.4, particleLifeTimeMax=0.9, particleColor1='194;181;162',
                          particleColor2='90;78;72', particleAlpha1=255, particleAlpha2=0, particleSize1=100,
                          particleSize2=50, particleGravityY=500, zoneRadius=12, additive=False,
                          destroyWhenNoParticles=True), 'inimigos/chefe')
    poe_objeto(d, emissor(base, 'pulso_brilho', rendererType='Point', rendererParam1=5, rendererParam2=1, tank=60,
                          flow=6000, maxParticleNb=80, emitterAngleB=360, emitterForceMin=500, emitterForceMax=1100,
                          particleLifeTimeMin=0.3, particleLifeTimeMax=0.7, particleColor1='255;250;220',
                          particleColor2='255;190;60', particleAlpha1=255, particleAlpha2=0, particleSize1=110,
                          particleSize2=30, particleGravityY=0, zoneRadius=20, additive=True,
                          destroyWhenNoParticles=True), 'inimigos/chefe')
    anel = {k: v for k, v in o['laco_amor'].items() if k not in ('name', 'persistentUuid', 'effects', 'variables')}
    anel.update(name='pulso_anel', persistentUuid=ids('obj/pulso_anel'), variables=[], fillOpacity=0,
                outlineColor={'r': 255, 'g': 240, 'b': 190}, outlineOpacity=255, outlineSize=14,
                absoluteCoordinates=True, clearBetweenFrames=True,
                effects=[efeito('Glow', 'Effect', {'distance': 30, 'innerStrength': 4, 'outerStrength': 12},
                                {'color': '255;210;120'}),
                         efeito('AdvancedBloom', 'Brilho', {'threshold': 0.2, 'bloomScale': 1.6, 'brightness': 1.3, 'blur': 10,
                                                            'quality': 6, 'padding': 80})])
    poe_objeto(d, anel, 'inimigos/chefe')

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    k = next(i for i, e in enumerate(deus['events']) if e.get('name') == 'Anel de ouro: o olhar')
    antigos = [e for e in deus['events'][k]['events'] if not e.get('conditions') or
               tx(e['conditions']) in (tx([bol(d_, 'morto', False)]), tx([bol(d_, 'morto', False), txt(d_, 'etapa', '')]))]
    assert len(antigos) == 2, antigos
    deus['events'][k] = pulso(antigos)
    # pedras andam na velocidade da tela
    for e in acha(deus['events'], 'Fragmentos')['events']:
        for a in e['actions']:
            if a['type']['value'] == 'SetY' and a['parameters'][0] == 'fragmento':
                a['parameters'][2] = '(fragmento.vy - subida_vel) * TimeDelta()'
    # limpeza na troca de fase e na morte
    troca = next(e for e in todos(acha(deus['events'], 'Fases')['events'])
                 if '"deus", "estado", "=", "\\"fase\\""' in tx(e.get('actions', [])))
    morte = next(e for e in acha(deus['events'], 'Morte')['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
    for e in (troca, morte):
        e['actions'] += [X('Delete', 'conv_luz', ''), X('Delete', 'pulso_anel', '')]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'pulso_anel') is not None, 't151')
