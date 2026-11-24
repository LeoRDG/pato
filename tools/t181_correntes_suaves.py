"""Tarefa 181: correntes de luz do Paraíso com efeito em vez de desenho em degraus.

A textura da corrente (corrente_luz.png) virou uma luz lisa (tools/arte_corrente_suave.py) e passa a ser desenhada
suave (smoothed). As faíscas que eram pixels na textura viram partículas: um corrente_faisca por corrente, no pé
da corrente ou no pé da tela (o que for mais alto), soltando luzinhas (particula_luz) que sobem até o topo da
corrente (vida = distância até o topo / faisca_vel) e param quando a corrente apaga (StopEmission; flow 0 encerrava o
emissor de vez). Tudo editável no GDevelop: variáveis da corrente (faisca_vel, faisca_largura,
faisca_angulo) e as cores e tamanhos no emissor. Não é aditivo (na camada do jogo o aditivo esbranquiça tudo, t178).
A mecânica (subir, ligar e desligar, piscar) não muda.
Rodar uma vez:  python3 tools/t181_correntes_suaves.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import LUZ, suaves

ids = Ids('t181')
F = 'corrente_faisca'
C = 'corrente_luz'


def migra(d):
    suaves(d, [LUZ, 'assets/paraiso/corrente_luz.png'])
    poe_objeto(d, emissor(objeto(d, 'hub_luzes'), F, textureParticleName=LUZ, rendererType='Quad',
                          rendererParam1=128, rendererParam2=128, tank=-1, flow=12, maxParticleNb=160,
                          emitterAngleA=0, emitterAngleB=1, emitterForceMin=320, emitterForceMax=320,
                          particleLifeTimeMin=10, particleLifeTimeMax=10, particleGravityX=0, particleGravityY=0,
                          particleColor1='255;222;120', particleColor2='255;176;50', particleAlpha1=255,
                          particleAlpha2=170, particleSize1=24, particleSize2=14, zoneRadius=30, additive=False,
                          destroyWhenNoParticles=False, jumpForwardInTimeOnCreation=0), 'cenario/paraiso')
    objeto(d, F)['updateIfNotVisible'] = True     # o emissor fica no pé da corrente, quase sempre fora da tela
    poe_vars(ids, objeto(d, C)['variables'], C, [('faisca_vel', 320), ('faisca_largura', 0.22),
                                                ('faisca_angulo', 270)])
    poe_vars(ids, objeto(d, F)['variables'], F, [('cx', 0)])
    g = acha(cena(d, 'Paraiso')['events'], 'Correntes de luz')
    cria = ev([X('SceneInstancesCount', '', F, '=', '0')], [], [
        cada(C, [], [X('Create', '', F, f'{C}.CenterX()', f'{C}.Y() + {C}.Height()', '""'),
                     X('ChangePlan', F, '=', f'{C}.ZOrder()'),
                     X('SetNumberObjectVariable', F, 'cx', '=', f'{C}.CenterX()'),
                     X('SetAngle', F, '=', f'{C}.faisca_angulo'),
                     X('ParticleSystem::EmitterForceMin', F, '=', f'{C}.faisca_vel'),
                     X('ParticleSystem::EmitterForceMax', F, '=', f'{C}.faisca_vel'),
                     X('ParticleSystem::ParticleLifeTimeMin', F, '=', f'{C}.Height() / {C}.faisca_vel'),
                     X('ParticleSystem::ParticleLifeTimeMax', F, '=', f'{C}.Height() / {C}.faisca_vel'),
                     X('ParticleSystem::ZoneRadius', F, '=', f'{C}.Width() * {C}.faisca_largura')])])
    pe = f'min({C}.Y() + {C}.Height(), CameraCenterY("", 0) + CameraHeight("", 0) / 2)'
    vida = f'({F}.Y() - {C}.Y()) / {C}.faisca_vel'
    liga = cada(C, [], [], [
        ev([num(F, 'cx', '=', f'{C}.CenterX()')],
           [X('SetY', F, '=', pe),
            X('ParticleSystem::ParticleLifeTimeMin', F, '=', vida),
            X('ParticleSystem::ParticleLifeTimeMax', F, '=', vida)], [
            ev([bol(C, 'ativa', True)], [X('ParticleSystem::StartEmission', F)]),
            ev([bol(C, 'ativa', False)], [X('ParticleSystem::StopEmission', F)])])])
    g['events'] += [cria, liga]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, F) is not None, 't181')
