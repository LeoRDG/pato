"""Tarefa 173: bala que bate no terreno solta faíscas.

Antes a bala (do pato ou dos inimigos) só sumia ao tocar o terreno. Agora, antes de apagar, ela cria impacto_bala:
umas poucas faíscas de luz (particula_luz, aditivas) num cone voltado para o lado de onde a bala veio
(Angle() + 180). Cores, quantidade e força ficam no emissor, editáveis no GDevelop.
Rodar uma vez:  python3 tools/t173_impacto_bala.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import LUZ, suaves

I = 'impacto_bala'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    suaves(d, [LUZ])
    poe_objeto(d, emissor(objeto(d, 'explosao_faiscas'), I, rendererType='Quad', textureParticleName=LUZ,
                          rendererParam1=128, rendererParam2=128, tank=9, flow=3000, maxParticleNb=12,
                          emitterAngleA=0, emitterAngleB=80, emitterForceMin=140, emitterForceMax=420,
                          particleLifeTimeMin=0.1, particleLifeTimeMax=0.28, particleColor1='255;244;210',
                          particleColor2='255;150;60', particleAlpha1=255, particleAlpha2=0, particleSize1=9,
                          particleSize2=3, particleGravityY=500, zoneRadius=2, additive=True,
                          destroyWhenNoParticles=True), 'efeitos')
    g = acha(acha(folha(d, 'Combate')['events'], 'Projéteis')['events'], 'Balas no terreno')
    for bala in ('projetil', 'projetil_inimigo'):
        e = next(e for e in g['events'] if f'"CollisionNP"}}, "parameters": ["{bala}", "Terreno"' in tx(e['conditions']))
        k = next(i for i, a in enumerate(e['actions']) if a['type']['value'] == 'Delete')
        e['actions'][k:k] = [X('Create', '', I, f'{bala}.CenterX()', f'{bala}.CenterY()', '""'),
                             X('SetAngle', I, '=', f'{bala}.Angle() + 180'),
                             X('ChangePlan', I, '=', f'{bala}.ZOrder()')]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, I) is not None, 't173')
