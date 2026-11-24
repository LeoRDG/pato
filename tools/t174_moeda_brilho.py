"""Tarefa 174: pegar moeda solta um brilho dourado.

Antes a coleta só tocava o som e mostrava o "+N". Agora cria moeda_brilho no centro da moeda: umas faíscas douradas
(particula_luz, aditivas) que se abrem e sobem um pouco. Cores, quantidade e força ficam no emissor.
Rodar uma vez:  python3 tools/t174_moeda_brilho.py
"""
from gd_mig import *
from t149_redoma_e_particulas import emissor
from t169_fogo_e_fumaca import LUZ, suaves

B = 'moeda_brilho'


def tx(e):
    return json.dumps(e, ensure_ascii=False)


def migra(d):
    suaves(d, [LUZ])
    poe_objeto(d, emissor(objeto(d, 'explosao_faiscas'), B, rendererType='Quad', textureParticleName=LUZ,
                          rendererParam1=128, rendererParam2=128, tank=12, flow=3000, maxParticleNb=14,
                          emitterAngleA=0, emitterAngleB=360, emitterForceMin=60, emitterForceMax=210,
                          particleLifeTimeMin=0.25, particleLifeTimeMax=0.5, particleColor1='255;246;190',
                          particleColor2='255;190;60', particleAlpha1=255, particleAlpha2=0, particleSize1=9,
                          particleSize2=2, particleGravityY=-80, zoneRadius=6, additive=True,
                          destroyWhenNoParticles=True), 'efeitos')
    g = acha(acha(folha(d, 'Combate')['events'], 'Moeda')['events'], 'Coleta')
    e = next(e for e in g['events'] if '"CollisionNP"}, "parameters": ["moeda", "pato"' in tx(e['conditions']))
    e['actions'][1:1] = [X('Create', '', B, 'moeda.CenterX()', 'moeda.CenterY()', '""'),
                         X('ChangePlan', B, '=', 'moeda.ZOrder()')]


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, B) is not None, 't174')
