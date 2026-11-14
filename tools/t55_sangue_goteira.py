"""Tarefa 55: goteira de sangue, um emissor de partículas para colocar na cena (teto, cano, corpo pendurado...).

sangue_goteira solta gotas sem parar: nascem quase paradas num ponto, caem com a gravidade e viram um risco
alongado no sentido da queda (o GDevelop gira a partícula na direção do movimento). Não acaba (tank -1) e não
se apaga sozinho. Tudo se ajusta nas propriedades do emissor: flow (gotas por segundo), zoneRadius (largura de
onde pingam), particleGravityY (peso), particleLifeTimeMin/Max (até onde caem), rendererParam1/2 (comprimento e
grossura da gota) e as cores.

Migração de uso único que só ADICIONA o objeto (copiando sangue_vermelho) na pasta cenario/decoracao, se ainda não existe.
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME = 'sangue_goteira'


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    if NOME in objs:
        return
    o = copy.deepcopy(objs['sangue_vermelho'])
    o.update(name=NOME, persistentUuid=str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t55/' + NOME)),
             additive=False, destroyWhenNoParticles=False, tank=-1, flow=2.5, maxParticleNb=40,
             emitterAngleA=0, emitterAngleB=30, emitterForceMin=0, emitterForceMax=18, zoneRadius=5,
             particleGravityX=0, particleGravityY=1100, particleLifeTimeMin=0.9, particleLifeTimeMax=1.4,
             particleColor1='165;12;14', particleRed1=165, particleGreen1=12, particleBlue1=14,
             particleColor2='80;0;4', particleRed2=80, particleGreen2=0, particleBlue2=4,
             particleAlpha1=255, particleAlpha2=190, particleSize1=100, particleSize2=70,
             particleAngle1=0, particleAngle2=0,                    # 0 e 0: a gota aponta para onde cai
             rendererType='Line', rendererParam1=9, rendererParam2=4, textureParticleName='',
             variables=[], effects=[], behaviors=[])
    d['objects'].append(o)
    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'decoracao'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox
    if not any(c.get('objectName') == NOME for c in pasta.setdefault('children', [])):
        pasta['children'].append({'objectName': NOME})


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
