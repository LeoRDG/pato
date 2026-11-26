"""Tarefa 214: o Deus morre e os anéis quebram em partículas de luz de verdade, e o olho se fere conforme perde vida.

A arte (tools/arte_feridas_deus.py) tirou a explosão pontilhada dos quadros: olho/morte agora clareia, encolhe para
o centro e some; anel_*/quebra acende e vira um aro fino que se abre e some. As animações, os tempos e os eventos que
dependem da morte (morte_tempo do olho, limpeza das partes, chefe_final_morto, portal final, fim da luta) não mudam.

Objetos novos (pasta inimigos/chefe); o clarão e as faíscas somam luz (aditivo); o anel e os
estilhaços dos anéis desenham a cor por cima, senão somem em branco no céu claro:
- deus_morte_clarao: uma partícula grande e curta com o disco macio de assets/portais/fundo.png, um clarão que se
  abre e some.
- deus_morte_anel: partículas que saem todas do centro com a mesma velocidade, um anel de luz que se expande.
- deus_morte_faiscas: riscos de luz (renderizador Line) disparados em todas as direções.
- deus_anel_luz: estilhaços de luz de um anel (pontos na cor do anel, saem em leque para fora).
- deus_feridas: sobreposição do olho com veias e rachaduras (assets/inimigos/ceu/deus/feridas), com uma animação
  "<animação do olho>_<estágio>" para cada animação do olho (mesmos quadros e tempos), tingida por estágio.
Na morte (Morte, o mesmo evento de antes) o olho solta clarão + anel + faíscas (deus_morte_luz continua); quando a
animação morte do olho termina (o olho virou um ponto) vem o estouro: outro anel, faíscas e o brilho deus_morte_luz.
Na quebra dos anéis (troca de fase e morte) cada anel solta deus.anel_luz_pontos leques de luz em volta do aro, na
cor dele. Dano visível: deus.ferida (0 a 4) sobe quando deus.vida fica abaixo de max_vida * ferida_N_abaixo; a
sobreposição segue o olho quadro a quadro e é tingida com ferida_cor_N (vermelho mais forte a cada estágio); quando o
estágio sobe sai um sopro de luz do olho.
Variáveis novas no deus_olho (o olho vive até o fim da morte; a pupila deus some antes): morte_* e estouro_*; no deus:
anel_luz_* e ferida_*. Só as que faltam são criadas.
Rodar uma vez:  python3 tools/t214_deus_luz_e_feridas.py
"""
import copy
from gd_mig import *
import arte_feridas_deus as AF

PASTA = 'inimigos/chefe'
FERIDAS = 'assets/inimigos/ceu/deus/feridas'
CLARAO = 'assets/portais/fundo.png'   # disco branco de borda macia (t210)

OLHO_VARS = [
    ('morte_clarao_qtd', 1), ('morte_clarao_tam', 120), ('morte_clarao_tam_fim', 320), ('morte_clarao_vida', 0.3),
    ('morte_clarao_cor', '255;255;245'), ('morte_clarao_cor_fim', '255;225;150'),
    ('morte_anel_qtd', 140), ('morte_anel_vel', 1100), ('morte_anel_vida', 0.7), ('morte_anel_tam', 200),
    ('morte_anel_tam_fim', 60), ('morte_anel_cor', '255;255;255'), ('morte_anel_cor_fim', '255;200;90'),
    ('morte_faisca_qtd', 70), ('morte_faisca_vel_min', 500), ('morte_faisca_vel_max', 1500),
    ('morte_faisca_vida_min', 0.4), ('morte_faisca_vida_max', 1), ('morte_faisca_tam', 140), ('morte_faisca_tam_fim', 30),
    ('morte_faisca_cor', '255;255;230'), ('morte_faisca_cor_fim', '255;170;60'),
    ('estouro_clarao_tam', 80), ('estouro_anel_vel', 700), ('estouro_faisca_qtd', 50),
    ('estouro_z', 0), ('estouro_feito', False),
]
DEUS_VARS = [
    ('anel_luz_pedido', False), ('anel_luz_i', 0), ('anel_luz_pontos', 16), ('anel_luz_qtd', 8),
    ('anel_luz_raio', 0.277), ('anel_luz_desloc', 0.1),
    ('anel_luz_ang_ouro', -90), ('anel_luz_ang_azul', 30), ('anel_luz_ang_rosa', 150),
    ('anel_luz_cone', 70), ('anel_luz_vel_min', 80), ('anel_luz_vel_max', 380),
    ('anel_luz_vida_min', 0.35), ('anel_luz_vida_max', 0.9), ('anel_luz_tam', 120), ('anel_luz_tam_fim', 20),
    ('anel_luz_cor_ouro', '255;230;140'), ('anel_luz_cor_ouro_fim', '255;170;40'),
    ('anel_luz_cor_azul', '170;215;255'), ('anel_luz_cor_azul_fim', '60;130;255'),
    ('anel_luz_cor_rosa', '255;185;210'), ('anel_luz_cor_rosa_fim', '255;90;140'),
    ('ferida', 0), ('ferida_vista', 0),
    ('ferida_1_abaixo', 0.85), ('ferida_2_abaixo', 0.65), ('ferida_3_abaixo', 0.45), ('ferida_4_abaixo', 0.25),
    ('ferida_cor_1', '255;135;135'), ('ferida_cor_2', '255;100;100'), ('ferida_cor_3', '235;60;60'),
    ('ferida_cor_4', '210;25;35'), ('ferida_z', 0.5),
    ('ferida_luz_qtd', 40), ('ferida_luz_raio', 60), ('ferida_luz_cor', '255;250;235'), ('ferida_luz_cor_fim', '255;110;90'),
]


def emissor(base, nome, **k):
    o = copy.deepcopy(base)
    o.update(name=nome, variables=[], effects=[], behaviors=[])
    o.pop('persistentUuid', None)
    o.update(k)
    for n in ('1', '2'):   # as cores também ficam em Red/Green/Blue (o editor lê das duas formas)
        r, g, b = (int(x) for x in o['particleColor' + n].split(';'))
        o['particleRed' + n], o['particleGreen' + n], o['particleBlue' + n] = r, g, b
    return o


def migra(d):
    ids = Ids('t214')
    base = objeto(d, 'deus_morte_luz')
    olho = objeto(d, 'deus_olho')
    deus = objeto(d, 'deus')
    poe_vars(ids, olho['variables'], 'deus_olho', OLHO_VARS)
    poe_vars(ids, deus['variables'], 'deus', DEUS_VARS)

    # ---------- emissores ----------
    poe_objeto(d, emissor(base, 'deus_morte_clarao', flow=-1, tank=1, maxParticleNb=4, emitterForceMin=0,
                          emitterForceMax=0, zoneRadius=1, rendererType='Quad', textureParticleName=CLARAO,
                          rendererParam1=128, rendererParam2=128, particleSize1=120, particleSize2=320,
                          particleLifeTimeMin=0.3, particleLifeTimeMax=0.3, particleGravityY=0, particleAlpha1=230,
                          particleAlpha2=0, particleColor1='255;255;245', particleColor2='255;225;150'), PASTA)
    poe_objeto(d, emissor(base, 'deus_morte_anel', flow=-1, additive=False, tank=140, maxParticleNb=300, emitterForceMin=1100,
                          emitterForceMax=1100, zoneRadius=1, rendererParam1=5, particleSize1=200, particleSize2=60,
                          particleLifeTimeMin=0.7, particleLifeTimeMax=0.7, particleGravityY=0,
                          particleColor1='255;255;255', particleColor2='255;200;90'), PASTA)
    poe_objeto(d, emissor(base, 'deus_morte_faiscas', flow=-1, tank=70, maxParticleNb=200, emitterForceMin=500,
                          emitterForceMax=1500, zoneRadius=10, rendererType='Line', rendererParam1=26,
                          rendererParam2=4, particleSize1=140, particleSize2=30, particleLifeTimeMin=0.4,
                          particleLifeTimeMax=1, particleGravityY=250,
                          particleColor1='255;255;230', particleColor2='255;170;60'), PASTA)
    poe_objeto(d, emissor(base, 'deus_anel_luz', flow=-1, additive=False, tank=10, maxParticleNb=60, emitterAngleA=0,
                          emitterAngleB=70, emitterForceMin=80, emitterForceMax=380, zoneRadius=6, rendererParam1=3,
                          particleSize1=120, particleSize2=20, particleLifeTimeMin=0.35, particleLifeTimeMax=0.9,
                          particleGravityY=-60, particleColor1='255;230;140', particleColor2='255;170;40'), PASTA)

    # ---------- sobreposição das feridas ----------
    anims = []
    for a in olho['animations']:
        if a['name'] not in AF.ABERTURA:
            continue
        dr = a['directions'][0]
        ab = AF.ABERTURA[a['name']]
        assert len(ab) == len(dr['sprites']), a['name']
        for e in range(1, AF.ESTAGIOS + 1):
            imgs = [f'{FERIDAS}/{AF.nome_ferida(e, x)}' for x in ab]
            anims.append((f"{a['name']}_{e}", imgs, len(imgs), dr['timeBetweenFrames'], dr['looping']))
    poe_recursos(d, sorted({i for _, imgs, *_ in anims for i in imgs}))
    poe_objeto(d, sprite(ids, 'deus_feridas', anims), PASTA)

    # ---------- eventos ----------
    evs = acha(folha(d, 'InimigosParaiso')['events'], 'Deus')['events']
    criacao = acha(evs, 'Criação')['events'][0]
    assert any(a['parameters'][:2] == ['', 'deus_olho'] for a in criacao['actions'] if a['type']['value'] == 'Create')
    FE = 'deus_feridas'
    criacao['actions'] += [
        X('Create', '', FE, 'CameraCenterX("", 0)', 'CameraCenterY("", 0) + CameraHeight("", 0)', '""'),
        X('ChangePlan', FE, '=', 'deus.z_base + 4 + deus.ferida_z'),
        X('ScalableCapability::ScalableBehavior::SetValue', FE, 'Scale', '=', 'deus.corpo_escala'),
        X('Hide', FE),
        setn('deus', 'ferida', '=', '0'),
        setn('deus', 'ferida_vista', '=', '0'),
    ]

    def luz(obj, x, y, z, qtd, cor, cor_fim, tam, tam_fim, vel_min, vel_max, vida_min, vida_max):
        return [X('Create', '', obj, x, y, '""'), X('ChangePlan', obj, '=', z),
                X('ParticleSystem::SetTank', obj, '=', qtd),
                X('ParticleSystem::ParticleColor1', obj, cor), X('ParticleSystem::ParticleColor2', obj, cor_fim),
                X('ParticleSystem::ParticleSize1', obj, '=', tam), X('ParticleSystem::ParticleSize2', obj, '=', tam_fim),
                X('ParticleSystem::EmitterForceMin', obj, '=', vel_min),
                X('ParticleSystem::EmitterForceMax', obj, '=', vel_max),
                X('ParticleSystem::ParticleLifeTimeMin', obj, '=', vida_min),
                X('ParticleSystem::ParticleLifeTimeMax', obj, '=', vida_max)]

    def estouro(x, y, z, clarao_tam, anel_vel, faisca_qtd):
        O = 'deus_olho.'
        return (luz('deus_morte_clarao', x, y, z, O + 'morte_clarao_qtd', O + 'morte_clarao_cor', O + 'morte_clarao_cor_fim',
                    clarao_tam, O + 'morte_clarao_tam_fim * ' + clarao_tam + ' / ' + O + 'morte_clarao_tam', '0', '0',
                    O + 'morte_clarao_vida', O + 'morte_clarao_vida')
                + luz('deus_morte_anel', x, y, z, O + 'morte_anel_qtd', O + 'morte_anel_cor', O + 'morte_anel_cor_fim',
                      O + 'morte_anel_tam', O + 'morte_anel_tam_fim', anel_vel, anel_vel, O + 'morte_anel_vida',
                      O + 'morte_anel_vida')
                + luz('deus_morte_faiscas', x, y, z, faisca_qtd, O + 'morte_faisca_cor', O + 'morte_faisca_cor_fim',
                      O + 'morte_faisca_tam', O + 'morte_faisca_tam_fim', O + 'morte_faisca_vel_min',
                      O + 'morte_faisca_vel_max', O + 'morte_faisca_vida_min', O + 'morte_faisca_vida_max'))

    morte = acha(evs, 'Morte')
    inicio = next(e for e in morte['events'] if '"morte_iniciada", "True"' in json.dumps(e.get('actions', [])))
    inicio['actions'] += [X('Delete', FE, ''), setb('deus', 'anel_luz_pedido', True),
                          setn('deus_olho', 'estouro_z', '=', 'deus.particula_z'),
                          setb('deus_olho', 'estouro_feito', False)] + \
        estouro('deus.cx', 'deus.cy', 'deus.particula_z', 'deus_olho.morte_clarao_tam', 'deus_olho.morte_anel_vel',
                'deus_olho.morte_faisca_qtd')
    i = morte['events'].index(inicio)
    morte['events'].insert(i + 1, ev(
        [X('SceneInstancesCount', '', 'deus_olho', '>', '0'),
         X('AnimatableCapability::AnimatableBehavior::Name', 'deus_olho', 'Animation', '=', '"morte"'),
         X('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', 'deus_olho', 'Animation'),
         bol('deus_olho', 'estouro_feito', False)],
        [setb('deus_olho', 'estouro_feito', True),
         X('Create', '', 'deus_morte_luz', 'deus_olho.CenterX()', 'deus_olho.CenterY()', '""'),
         X('ChangePlan', 'deus_morte_luz', '=', 'deus_olho.estouro_z')]
        + estouro('deus_olho.CenterX()', 'deus_olho.CenterY()', 'deus_olho.estouro_z', 'deus_olho.estouro_clarao_tam',
                  'deus_olho.estouro_anel_vel', 'deus_olho.estouro_faisca_qtd')))
    for e in morte['events']:   # a sobreposição sai junto com as outras partes
        if any(a['type']['value'] == 'Delete' and a['parameters'][0] == 'deus_olho' for a in e.get('actions', [])):
            if not any(a['type']['value'] == 'Delete' and a['parameters'][0] == FE for a in e['actions']):
                e['actions'].append(X('Delete', FE, ''))

    fases = acha(evs, 'Fases')
    troca = next(e for e in fases['events'] if '"deus_anel_ouro", "Animation", "=", "\\"quebra\\""' in json.dumps(e.get('actions', [])))
    troca['actions'].append(setb('deus', 'anel_luz_pedido', True))

    # estilhaços de luz dos anéis
    A = 'deus_anel_luz'

    def leques(anel, cor):
        cx = f'{anel}.CenterX() + cos(ToRad({anel}.Angle() + deus.anel_luz_ang_{cor})) * {anel}.Width() * deus.anel_luz_desloc'
        cy = f'{anel}.CenterY() + sin(ToRad({anel}.Angle() + deus.anel_luz_ang_{cor})) * {anel}.Width() * deus.anel_luz_desloc'
        ang = 'deus.anel_luz_i * 360 / deus.anel_luz_pontos'
        x = f'{cx} + cos(ToRad({ang})) * {anel}.Width() * deus.anel_luz_raio'
        y = f'{cy} + sin(ToRad({ang})) * {anel}.Width() * deus.anel_luz_raio'
        return [ev([X('SceneInstancesCount', '', anel, '>', '0')], [setn('deus', 'anel_luz_i', '=', '0')], [
            repete('deus.anel_luz_pontos',
                   luz(A, x, y, 'deus.particula_z', 'deus.anel_luz_qtd', f'deus.anel_luz_cor_{cor}',
                       f'deus.anel_luz_cor_{cor}_fim', 'deus.anel_luz_tam', 'deus.anel_luz_tam_fim',
                       'deus.anel_luz_vel_min', 'deus.anel_luz_vel_max', 'deus.anel_luz_vida_min',
                       'deus.anel_luz_vida_max')
                   + [X('ParticleSystem::ConeSprayAngle', A, '=', 'deus.anel_luz_cone'),
                      X('SetAngle', A, '=', ang),
                      setn('deus', 'anel_luz_i', '+', '1')])])]

    comentario = {'type': 'BuiltinCommonInstructions::Comment',
                  'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
                  'comment': 'Quando os anéis quebram (troca de fase e morte pedem com deus.anel_luz_pedido), cada anel solta '
                             'anel_luz_pontos leques de luz (deus_anel_luz) em volta do aro, na cor dele (anel_luz_cor_*). '
                             'O aro fica a anel_luz_raio da largura do anel, com o centro deslocado anel_luz_desloc no '
                             'ângulo anel_luz_ang_* (como na arte). Feridas: deus.ferida (0 a 4) pelo quanto de vida resta '
                             '(ferida_N_abaixo); deus_feridas segue o olho quadro a quadro, tingida com ferida_cor_N.',
                  'comment2': ''}
    quebra = ev([cbol_obj('deus', 'anel_luz_pedido')], [setb('deus', 'anel_luz_pedido', False)],
                leques('deus_anel_ouro', 'ouro') + leques('deus_anel_azul', 'azul') + leques('deus_anel_rosa', 'rosa'))

    vivo = [X('SceneInstancesCount', '', 'deus', '>', '0'), bol('deus', 'morto', False)]
    estagios = [ev(vivo, [setn('deus', 'ferida', '=', '0')])]
    for k in range(1, AF.ESTAGIOS + 1):
        estagios.append(ev(vivo + [cmp('deus.vida', '<', f'deus.max_vida * deus.ferida_{k}_abaixo')],
                           [setn('deus', 'ferida', '=', str(k))]))
    sopro = ev(vivo + [cmp('deus.ferida', '>', 'deus.ferida_vista')],
               [setn('deus', 'ferida_vista', '=', 'deus.ferida')]
               + luz(A, 'deus.cx', 'deus.cy', 'deus.particula_z', 'deus.ferida_luz_qtd', 'deus.ferida_luz_cor',
                     'deus.ferida_luz_cor_fim', 'deus.anel_luz_tam', 'deus.anel_luz_tam_fim', 'deus.anel_luz_vel_min',
                     'deus.anel_luz_vel_max', 'deus.anel_luz_vida_min', 'deus.anel_luz_vida_max')
               + [X('ParticleSystem::ConeSprayAngle', A, '=', '360'),
                  X('ParticleSystem::ZoneRadius', A, '=', 'deus.ferida_luz_raio')])
    segue = [ev([X('SceneInstancesCount', '', FE, '>', '0'), X('SceneInstancesCount', '', 'deus_olho', '>', '0'),
                 cmp('deus.ferida', '>', '0'),
                 NAO('AnimatableCapability::AnimatableBehavior::Name', 'deus_olho', 'Animation', '=', '"morte"')],
                [X('Show', FE),
                 X('AnimatableCapability::AnimatableBehavior::SetName', FE, 'Animation', '=',
                   'deus_olho.Animation::Name() + "_" + ToString(deus.ferida)'),
                 X('AnimatableCapability::AnimatableBehavior::SetElapsedTime', FE, 'Animation', '=',
                   'deus_olho.Animation::ElapsedTime()'),
                 X('SetXY', FE, '=', 'deus_olho.X()', '=', 'deus_olho.Y()')],
                [ev([cmp('deus.ferida', '=', str(k))], [X('ChangeColor', FE, f'deus.ferida_cor_{k}')])
                 for k in range(1, AF.ESTAGIOS + 1)]),
             ev([X('SceneInstancesCount', '', FE, '>', '0'), cmp('deus.ferida', '=', '0')], [X('Hide', FE)])]
    g = grupo('Quebra em luz e feridas', [comentario, quebra] + estagios + [sopro] + segue)
    evs.insert(evs.index(morte) + 1, g)


def cbol_obj(o, v):
    return bol(o, v, True)


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'deus_feridas') is not None, 't214')
