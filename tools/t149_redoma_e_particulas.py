"""Tarefa 149: redoma de invulnerável, partículas, sensação de subida e sem pulo no voo.

- Redoma: enquanto Deus não toma dano (invulneravel) a redoma (deus_escudo, arte nova de bolha com treliça) fica em
  volta dele, pulsando (escudo_opacidade, escudo_pulso, escudo_pulso_forca) e do tamanho deus.corpo_escala *
  deus.escudo_escala (menor que a órbita dos canalizadores, para não protegê-los). Ela segura as balas: faíscas
  (escudo_faisca) e a bala some; explosivos estouram nela. Quando ele abre, a redoma estoura (escudo_quebra).
- Partículas do GDevelop: escudo_faisca, escudo_quebra, deus_morte_luz (na morte) e vento_subida (riscos de vento
  descendo pela tela durante a luta). Os números ficam nas propriedades de cada emissor.
- Subida mais visível: na luta a camada Fundo (nuvens) sobe com luta_parallax_y em vez de fundo_parallax_y, e o céu
  alto e o espaço rolam com parallax maior (só se ainda estiverem no valor inicial).
- Sem pulo no voo: pato.voando fica verdadeiro na luta; os eventos de pulo, giro, cocô e dash de chão do Jogador
  só rodam com ele falso.
Só adiciona; variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t149_redoma_e_particulas.py
"""
import copy
import math
from gd_mig import *

ids = Ids('t149')
d_ = 'deus'
CX, CY = 'CameraCenterX("", 0)', 'CameraCenterY("", 0)'
PARALLAX = {'bg_ceu_alto': (0.12, 0.45), 'bg_espaco': (0.12, 0.45)}
CHAVES_PULO = ('SimulateJumpKey', 'SimulateDashKey', 'giroPulo', '"\\"Space\\""', '"Create"}, "parameters": ["", "cagada"')


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def emissor(base, nome, **props):
    e = copy.deepcopy(base)
    e.pop('persistentUuid', None)
    e.update(name=nome, variables=[], effects=[], behaviors=[], textureParticleName='', jumpForwardInTimeOnCreation=0,
             particleAngle1=0, particleAngle2=0, particleAngleRandomness1=0, particleAngleRandomness2=0,
             particleAlphaRandomness1=0, particleAlphaRandomness2=0, particleSizeRandomness1=0,
             particleSizeRandomness2=0, particleGravityX=0, emitterAngleA=0)
    e.update(props)
    for k in ('1', '2'):
        r, g, b = (int(x) for x in e['particleColor' + k].split(';'))
        e['particleRed' + k], e['particleGreen' + k], e['particleBlue' + k] = r, g, b
    return e


def emissores(base):
    return [
        emissor(base, 'escudo_faisca', rendererType='Point', rendererParam1=3, rendererParam2=1, tank=14, flow=2000,
                maxParticleNb=40, emitterAngleB=100, emitterForceMin=150, emitterForceMax=420, particleLifeTimeMin=0.2,
                particleLifeTimeMax=0.45, particleColor1='235;248;255', particleColor2='90;160;255',
                particleAlpha1=255, particleAlpha2=0, particleSize1=100, particleSize2=30, particleGravityY=0,
                zoneRadius=2, additive=True, destroyWhenNoParticles=True),
        emissor(base, 'escudo_quebra', rendererType='Line', rendererParam1=18, rendererParam2=3, tank=70, flow=6000,
                maxParticleNb=90, emitterAngleB=360, emitterForceMin=300, emitterForceMax=750, particleLifeTimeMin=0.4,
                particleLifeTimeMax=0.9, particleColor1='225;242;255', particleColor2='80;140;255',
                particleAlpha1=255, particleAlpha2=0, particleSize1=100, particleSize2=40, particleGravityY=300,
                zoneRadius=130, additive=True, destroyWhenNoParticles=True),
        emissor(base, 'deus_morte_luz', rendererType='Point', rendererParam1=6, rendererParam2=1, tank=160, flow=4000,
                maxParticleNb=200, emitterAngleB=360, emitterForceMin=200, emitterForceMax=900,
                particleLifeTimeMin=0.8, particleLifeTimeMax=1.8, particleColor1='255;250;220',
                particleColor2='255;190;60', particleAlpha1=255, particleAlpha2=0, particleSize1=120, particleSize2=20,
                particleGravityY=-100, zoneRadius=40, additive=True, destroyWhenNoParticles=True),
        emissor(base, 'vento_subida', rendererType='Line', rendererParam1=110, rendererParam2=3, tank=-1, flow=60,
                maxParticleNb=140, emitterAngleB=4, emitterForceMin=900, emitterForceMax=1500,
                particleLifeTimeMin=0.8, particleLifeTimeMax=1.3, particleColor1='255;255;255',
                particleColor2='190;215;255', particleAlpha1=60, particleAlpha2=0, particleSize1=100,
                particleSize2=100, particleGravityY=60, zoneRadius=760, additive=True, destroyWhenNoParticles=False,
                jumpForwardInTimeOnCreation=1),
    ]


def redoma():
    sem_morte = bol(d_, 'morto', False)
    em_pe = [bol(d_, 'escudo_visto', True), sem_morte]
    faisca = [X('Create', '', 'escudo_faisca', 'projetil.CenterX()', 'projetil.CenterY()', '""'),
              X('SetAngle', 'escudo_faisca', '=', 'projetil.Angle() + 180'),
              X('ChangePlan', 'escudo_faisca', '=', 'deus.particula_z')]
    bate = X('CollisionNP', 'projetil', 'deus_escudo', '', '', '')
    return [
        ev([bol(d_, 'invulneravel', True), sem_morte, bol(d_, 'escudo_visto', False)],
           [setb(d_, 'escudo_visto', True), X('Show', 'deus_escudo', '')]),
        ev(em_pe, [X('OpacityCapability::OpacityBehavior::SetValue', 'deus_escudo', 'Opacity', '=',
                     'deus.escudo_opacidade - deus.escudo_pulso_forca * (1 + sin(TimeFromStart() * deus.escudo_pulso)) / 2')]),
        ev([bol(d_, 'invulneravel', False), bol(d_, 'escudo_visto', True)],
           [setb(d_, 'escudo_visto', False), X('Hide', 'deus_escudo'),
            X('Create', '', 'escudo_quebra', 'deus.cx', 'deus.cy', '""'),
            X('ChangePlan', 'escudo_quebra', '=', 'deus.particula_z'),
            som('som_luz.wav', 'deus.som_volume', 'deus.escudo_quebra_tom')]),
        ev(em_pe + [num('projetil', 'raio', '<=', '0'), bate], faisca + [X('Delete', 'projetil', '')]),
        ev(em_pe + [num('projetil', 'raio', '>', '0'), bate], faisca + [setb('projetil', 'boom', True)]),
    ]


def vento():
    luta = cbol('luta', True)
    return grupo('Vento da subida', [
        ev([luta], [X('SetCameraCenterY', '', '=',
                      f'CameraCenterY("Fundo", 0) + ({CY} - luta_y0) * (luta_parallax_y - fundo_parallax_y)', '"Fundo"', '0')]),
        ev([luta, cbol('chefe_final_morto', False), X('SceneInstancesCount', '', 'vento_subida', '=', '0')],
           [X('Create', '', 'vento_subida', CX, CY, '""'), X('SetAngle', 'vento_subida', '=', '90'),
            X('ChangePlan', 'vento_subida', '=', 'vento_z')]),
        ev([luta], [X('SetXY', 'vento_subida', '=', CX, '=', CY)]),
        ev([cbol('chefe_final_morto', True)], [X('Delete', 'vento_subida', '')]),
    ])


def migra(d):
    o = {x['name']: x for x in d['objects']}
    poe_vars(ids, o[d_]['variables'], d_, [
        ('escudo_visto', False), ('escudo_escala', 0.75), ('escudo_opacidade', 235), ('escudo_pulso', 3),
        ('escudo_pulso_forca', 60), ('particula_z', 2640)])
    poe_vars(ids, o['pato']['variables'], 'pato', [('voando', False)])
    poe_vars(ids, cena(d, 'Paraiso')['variables'], 'Paraiso', [('luta_parallax_y', 0.45), ('vento_z', 1)])
    for n, (antes, depois) in PARALLAX.items():
        for v in o[n]['variables']:
            if v['name'] == 'parallax' and v.get('value') == antes:
                v['value'] = depois
    for e in emissores(o['explosao_faiscas']):
        poe_objeto(d, e, 'inimigos/chefe')
    # máscara redonda da redoma (arte 720x720, aro de raio 333)
    for a in o['deus_escudo']['animations']:
        for sp in a['directions'][0]['sprites']:
            sp['hasCustomCollisionMask'] = True
            sp['customCollisionMask'] = [[{'x': round(360 + 333 * math.cos(k * math.pi / 8), 1),
                                           'y': round(360 + 333 * math.sin(k * math.pi / 8), 1)} for k in range(16)]]

    deus = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')
    cria = acha(deus['events'], 'Criação')['events'][0]
    cria['actions'].append(X('ScalableCapability::ScalableBehavior::SetValue', 'deus_escudo', 'Scale', '=',
                             'deus.corpo_escala * deus.escudo_escala'))
    acha(deus['events'], 'Sinal de vulnerável')['events'] += redoma()
    morte = acha(deus['events'], 'Morte')
    inicio = next(e for e in morte['events'] if '"deus", "morte_iniciada", "True"' in tx(e['actions']))
    inicio['actions'] += [X('Create', '', 'deus_morte_luz', 'deus.cx', 'deus.cy', '""'),
                          X('ChangePlan', 'deus_morte_luz', '=', 'deus.particula_z')]

    c = cena(d, 'Paraiso')
    k = next(i for i, e in enumerate(c['events']) if e.get('name') == 'Céu para o espaço')
    c['events'].insert(k, vento())
    acha(c['events'], 'Começo da luta')['events'][0]['actions'].append(setb('pato', 'voando', True))
    fim = acha(c['events'], 'Fim da luta')['events'][0]['actions']
    fim += [setb('pato', 'voando', False), X('Delete', 'vento_subida', '')]

    for e in todos(folha(d, 'Jogador')['events']):
        if any(k in tx(e.get('conditions', []) + e.get('actions', [])) for k in CHAVES_PULO):
            e['conditions'].append(bol('pato', 'voando', False))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'vento_subida') is not None, 't149')
