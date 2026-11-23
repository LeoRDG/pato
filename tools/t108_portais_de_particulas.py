"""Tarefa 108: portais sem arco: partículas puxadas para o centro e dois braços girando, flutuando.

O sprite portal (arco de pedra com redemoinho) continua sendo o gatilho de entrar na fase e a marca no editor, mas
fica invisível no jogo (opacidade 0; a colisão continua valendo). Três emissores novos servem para todos os portais;
as cores de cada portal vêm das variáveis dele (texto "r;g;b"): cor_borda e cor_centro, postas nas instâncias do Hub
(Inferno laranja, Purgatório verde-água, Paraíso azul e creme). No começo do Hub, cada portal cria no centro dele,
cada criação num subevento próprio (para as ações valerem só para o recém-criado), e pinta com as cores dele:
- três portal_espiral (sucção), a 120 graus um do outro, que orbitam rápido a raio_disco px (giro graus/s) e atiram
  para dentro com inclina graus de desvio: saindo de pontos sorteados em volta (zona do emissor), as partículas vêm
  soltas de todos os lados, aparecem fracas na borda, encolhem e esquentam (cor_borda -> cor_centro) e somem no meio;
- dois portal_braco, a 180 graus um do outro, que orbitam mais devagar a raio_braco px (giro_braco graus/s) e atiram
  para dentro com inclina_braco graus de desvio: dois braços curvos girando e entrando no meio;
- um portal_nucleo: brilho pequeno no meio, na cor_centro.
Tudo flutua: y soma sin(tempo * flutua_vel + fase) * flutua_amp. Variáveis novas no portal: cor_borda, cor_centro,
raio_disco 110, giro 540, inclina 8, raio_braco 90, giro_braco 150, inclina_braco 15, flutua_amp 10, flutua_vel 2
e fase. As partículas andam força x vida (~100 px na sucção, ~82 px nos braços, perto do raio de cada um) e por isso
param no meio: mudando um raio, mude junto a força ou a vida delas no emissor dele. Grupo novo PortalEfeito com os
3 emissores.
Rodar uma vez:  python3 tools/t108_portais_de_particulas.py
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FASES = {  # cena: (cor do centro, cor da borda)
    'Inferno': ((255, 236, 140), (210, 60, 20)),
    'Purgatorio': ((230, 255, 240), (40, 130, 115)),
    'Paraiso': ((255, 250, 215), (90, 140, 230)),
}
PORTAL_VARS = [('raio_disco', 110), ('giro', 540), ('inclina', 8), ('raio_braco', 90), ('giro_braco', 150),
               ('inclina_braco', 15), ('flutua_amp', 10), ('flutua_vel', 2), ('fase', 0)]
EMISSOR_VARS = ['base_x', 'base_y', 'raio', 'ang_orb', 'giro', 'inclina', 'flutua_amp', 'flutua_vel', 'fase']
GRUPO = 'PortalEfeito'


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t108/' + nome))


def var(dono, nome, valor):
    return {'name': nome, 'persistentUuid': uid(f'var/{dono}/{nome}'), 'type': 'number', 'value': valor}


def cor(c):
    return ';'.join(map(str, c))


def emissor(molde, nome, c1, c2, **props):
    e = copy.deepcopy(molde)
    e.update(name=nome, persistentUuid=uid('obj/' + nome), variables=[var(nome, n, 0) for n in EMISSOR_VARS],
             behaviors=[], effects=[], additive=True, destroyWhenNoParticles=False, tank=-1,
             particleColor1=cor(c1), particleColor2=cor(c2),
             particleRed1=c1[0], particleGreen1=c1[1], particleBlue1=c1[2],
             particleRed2=c2[0], particleGreen2=c2[1], particleBlue2=c2[2],
             particleAlpha1=255, particleAlpha2=0, particleGravityX=0, particleGravityY=0, rendererType='Point',
             rendererParam2=1, particleAngle1=0, particleAngle2=0, textureParticleName='', emitterAngleA=0,
             particleSize1=100, particleSize2=100)
    e.update(props)
    return e


def a(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def c(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None, tipo='Standard', obj=None):
    e = {'type': 'BuiltinCommonInstructions::' + tipo, 'conditions': conds, 'actions': acoes}
    if obj:
        e['object'] = obj
    if filhos:
        e['events'] = filhos
    return e


def cria(obj, z, cor1, cor2, raio='0', ang='0', giro='0', inclina='0'):
    """Um subevento por criação: nele a lista do objeto só tem o recém-criado."""
    return ev([], [a('Create', '', obj, 'portal.CenterX()', 'portal.CenterY()', ''),
                   a('ParticleSystem::ParticleColor1', obj, cor1),
                   a('ParticleSystem::ParticleColor2', obj, cor2),
                   a('ChangePlan', obj, '=', f'portal.ZOrder() + {z}'),
                   a('SetNumberObjectVariable', obj, 'base_x', '=', 'portal.CenterX()'),
                   a('SetNumberObjectVariable', obj, 'base_y', '=', 'portal.CenterY()'),
                   a('SetNumberObjectVariable', obj, 'raio', '=', raio),
                   a('SetNumberObjectVariable', obj, 'ang_orb', '=', ang),
                   a('SetNumberObjectVariable', obj, 'giro', '=', giro),
                   a('SetNumberObjectVariable', obj, 'inclina', '=', inclina),
                   a('SetNumberObjectVariable', obj, 'flutua_amp', '=', 'portal.flutua_amp'),
                   a('SetNumberObjectVariable', obj, 'flutua_vel', '=', 'portal.flutua_vel'),
                   a('SetNumberObjectVariable', obj, 'fase', '=', 'portal.fase')])


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(g['name'] == GRUPO for g in d['objectsGroups']):
        sys.exit('t108 já foi aplicada; não roda de novo.')
    O = {o['name']: o for o in d['objects']}
    molde = O['lava_brasas']
    c1, c2 = FASES['Inferno']          # cores no editor; no jogo cada portal pinta com as dele
    novos = [
        emissor(molde, 'portal_espiral', c2, c1, particleAlpha1=40, particleAlpha2=255, emitterAngleB=20,
                emitterForceMin=112, emitterForceMax=136, flow=60, maxParticleNb=140, zoneRadius=20,
                particleLifeTimeMin=0.81, particleLifeTimeMax=0.81, rendererParam1=4, particleSize1=120,
                particleSize2=30, jumpForwardInTimeOnCreation=1),
        emissor(molde, 'portal_braco', c2, c1, particleAlpha1=60, particleAlpha2=200, emitterAngleB=6,
                emitterForceMin=100, emitterForceMax=112, flow=55, maxParticleNb=100, zoneRadius=3,
                particleLifeTimeMin=0.75, particleLifeTimeMax=0.8, rendererParam1=5, particleSize1=120,
                particleSize2=60, jumpForwardInTimeOnCreation=1),
        emissor(molde, 'portal_nucleo', c1, c1, particleAlpha1=200, particleAlpha2=0, emitterAngleB=360,
                emitterForceMin=0, emitterForceMax=12, flow=40, maxParticleNb=40, zoneRadius=6,
                particleLifeTimeMin=0.3, particleLifeTimeMax=0.5, rendererParam1=7, particleSize1=100,
                particleSize2=40, jumpForwardInTimeOnCreation=1)]
    d['objects'] += novos
    pasta = next(x for x in d['objectsFolderStructure']['children'] if x.get('folderName') == 'gatilhos')
    pasta['children'] += [{'objectName': o['name']} for o in novos]
    d['objectsGroups'].append({'name': GRUPO, 'objects': [{'name': o['name']} for o in novos]})

    portal = O['portal']
    nomes = {v['name'] for v in portal['variables']}
    for n, v in PORTAL_VARS:
        if n not in nomes:
            portal['variables'].append(var('portal', n, v))
    for n, v in (('cor_borda', cor(FASES['Inferno'][1])), ('cor_centro', cor(FASES['Inferno'][0]))):
        if n not in nomes:
            portal['variables'].append(dict(var('portal', n, 0), type='string', value=v))
    hub = next(l for l in d['layouts'] if l['name'] == 'Hub')
    for i in hub['instances']:
        if i['name'] != 'portal':
            continue
        cena = next(v['value'] for v in i['initialVariables'] if v['name'] == 'cena')
        nomes_i = {v['name'] for v in i['initialVariables']}
        for n, v in (('cor_borda', cor(FASES[cena][1])), ('cor_centro', cor(FASES[cena][0]))):
            if n not in nomes_i:
                i['initialVariables'].append(dict(var(i['persistentUuid'], n, 0), type='string', value=v))

    hub = next(l for l in d['layouts'] if l['name'] == 'Hub')
    g = next(e for e in hub['events'] if e.get('name') == 'Portais')
    filhos = [cria('portal_espiral', 1, 'portal.cor_borda', 'portal.cor_centro', 'portal.raio_disco', str(k * 120),
                   'portal.giro', 'portal.inclina') for k in range(3)]
    filhos += [cria('portal_braco', 1, 'portal.cor_borda', 'portal.cor_centro', 'portal.raio_braco', str(k * 180),
                    'portal.giro_braco', 'portal.inclina_braco') for k in range(2)]
    filhos.append(cria('portal_nucleo', 2, 'portal.cor_centro', 'portal.cor_centro'))
    G = GRUPO
    g['events'] += [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Portais de partículas: o sprite portal é só o gatilho (invisível no jogo). No começo, cada portal '
                    'cria, pintados com cor_borda e cor_centro dele, três emissores que orbitam rápido a raio_disco (giro) atirando para dentro com inclina graus '
                    'de desvio (partículas puxadas para o centro de todos os lados), dois braços girando (raio_braco, giro_braco, '
                    'inclina_braco) e o brilho do meio. Tudo '
                    'flutua (flutua_amp, flutua_vel). Partículas: propriedades dos emissores portal_*.'},
        ev([c('DepartScene', '')], [],
           [ev([], [a('OpacityCapability::OpacityBehavior::SetValue', 'portal', 'Opacity', '=', '0'),
                    a('SetNumberObjectVariable', 'portal', 'fase', '=', 'RandomFloat(6.28)')],
               filhos, tipo='ForEach', obj='portal')]),
        ev([], [a('SetNumberObjectVariable', G, 'ang_orb', '+', f'{G}.giro * TimeDelta()'),
                a('SetX', G, '=', f'{G}.base_x + {G}.raio * cos(ToRad({G}.ang_orb))'),
                a('SetY', G, '=', f'{G}.base_y + {G}.raio * sin(ToRad({G}.ang_orb)) + '
                                  f'sin(TimeFromStart() * {G}.flutua_vel + {G}.fase) * {G}.flutua_amp'),
                a('SetAngle', G, '=', f'{G}.ang_orb + 180 + {G}.inclina')]),
    ]

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('portais de partículas (sucção)')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
