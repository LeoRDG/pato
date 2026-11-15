"""Tarefa 81: morte dos anjos sem a explosão presa no quadrado da imagem; a explosão vira um emissor de partículas.

- Animação morte de querubim, serafim, ofanim e roda_anjo (mesmos arquivos e mesma quantidade de quadros): o primeiro
  quadro é o anjo inteiro num clarão branco, e os seguintes encolhem para o centro e somem, sem nada sair da silhueta.
  O quadro base é o morte_00 atual (o anjo inteiro).
- Objeto novo anjo_morte_luz (emissor de partículas de luz, aditivo, que sobem devagar e somem; destroyWhenNoParticles),
  na pasta efeitos. Todas as propriedades dele ficam editáveis no GDevelop.
- Variáveis novas nos anjos (só se faltarem): morte_luz_raio (raio da zona de onde as partículas saem) e morte_luz_qtd
  (quantas partículas).
- Eventos (Inimigos > Céu > "Morte dos anjos (partículas de luz)"): ao morrer, uma vez (morte_feita), cria o
  anjo_morte_luz no centro do anjo com esse raio e essa quantidade.
- Acerto da t80: o grupo de eventos "Condenado em chamas (frenesi)" sai de Purgatório e vai para o fim de Inferno.
Rodar uma vez:  python3 tools/t81_anjos_morte_particulas.py
"""
import json, os, sys, uuid
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANJOS = {'querubim': dict(morte_luz_raio=30, morte_luz_qtd=55), 'serafim': dict(morte_luz_raio=30, morte_luz_qtd=55),
         'ofanim': dict(morte_luz_raio=90, morte_luz_qtd=150), 'roda_anjo': dict(morte_luz_raio=24, morte_luz_qtd=45)}
SO_JSON = False   # True só para refazer o jogo.json sem redesenhar os quadros (que já foram redesenhados)
EMISSOR = {
    'additive': True, 'assetStoreId': '', 'destroyWhenNoParticles': True, 'emitterAngleA': 0, 'emitterAngleB': 360,
    'emitterForceMax': 380, 'emitterForceMin': 90, 'flow': 3000, 'jumpForwardInTimeOnCreation': 0, 'maxParticleNb': 300,
    'name': 'anjo_morte_luz', 'particleAlpha1': 255, 'particleAlpha2': 0, 'particleAlphaRandomness1': 0,
    'particleAlphaRandomness2': 0, 'particleAngle1': 0, 'particleAngle2': 0, 'particleAngleRandomness1': 0,
    'particleAngleRandomness2': 0, 'particleBlue1': 230, 'particleBlue2': 120, 'particleColor1': '255;252;230',
    'particleColor2': '255;214;120', 'particleGravityX': 0, 'particleGravityY': -160, 'particleGreen1': 252,
    'particleGreen2': 214, 'particleLifeTimeMax': 1.1, 'particleLifeTimeMin': 0.45, 'particleRed1': 255,
    'particleRed2': 255, 'particleSize1': 110, 'particleSize2': 20, 'particleSizeRandomness1': 30,
    'particleSizeRandomness2': 0, 'rendererParam1': 5, 'rendererParam2': 1, 'rendererType': 'Point', 'tank': 60,
    'textureParticleName': '', 'type': 'ParticleSystem::ParticleEmitter', 'zoneRadius': 30, 'variables': [],
    'effects': [], 'behaviors': []}


def I(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def quadros_morte(base, n):
    """Clarão branco do anjo inteiro e depois encolhe para o centro (da silhueta) apagando."""
    h, w = base.shape[:2]
    a = base[..., 3] > 40
    ys, xs = np.nonzero(a)
    cx, cy = xs.mean(), ys.mean()
    out = []
    for f in range(n):
        k = f / (n - 1)
        branco = 0.85 if f == 0 else max(0.0, 1.0 - 0.35 * k)
        escala = 1.0 if f == 0 else 1.0 - 0.8 * k ** 0.9
        alfa = 1.0 if f == 0 else 1.0 - 0.75 * k
        im = base.astype(float).copy()
        im[..., :3] = im[..., :3] * (1 - branco) + np.array([255, 252, 236]) * branco
        im[..., 3] *= alfa
        img = Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA')
        if escala < 1:
            nw, nh = max(1, round(w * escala)), max(1, round(h * escala))
            peq = img.resize((nw, nh), Image.NEAREST)
            img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            img.paste(peq, (round(cx - cx * escala), round(cy - cy * escala)))
        out.append(img)
    return out


def var(dono, nome, valor):
    return {'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogos/t81/{dono}/{nome}')),
            'type': 'number', 'value': valor}


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if any(o['name'] == 'anjo_morte_luz' for o in d['objects']):
        sys.exit('t81 já foi aplicada (anjo_morte_luz existe); não roda de novo.')
    rec = {r['name']: r for r in d['resources']['resources']}
    obj = {o['name']: o for o in d['objects']}

    # 1. quadros da morte
    for nome in ANJOS:
        anim = next(a for a in obj[nome]['animations'] if a['name'] == 'morte')
        arqs = [os.path.join(RAIZ, rec[s['image']]['file']) for s in anim['directions'][0]['sprites']]
        if SO_JSON:
            continue
        base = np.array(Image.open(arqs[0]).convert('RGBA'))
        for arq, im in zip(arqs, quadros_morte(base, len(arqs))):
            im.save(arq)

    # 2. emissor, no painel em efeitos
    d['objects'].append(dict(EMISSOR))
    efeitos = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'efeitos')
    efeitos['children'].append({'objectName': 'anjo_morte_luz'})

    # 3. variáveis (só as que faltam)
    for nome, vs in ANJOS.items():
        tem = {v['name'] for v in obj[nome]['variables']}
        obj[nome]['variables'] += [var(nome, k, x) for k, x in vs.items() if k not in tem]

    # 4. eventos
    evs = next(e for e in d['externalEvents'] if e['name'] == 'Inimigos')['events']
    grupo = {e.get('name'): e for e in evs if e['type'] == 'BuiltinCommonInstructions::Group'}
    morte = []
    for nome in ANJOS:
        morte.append({'type': 'BuiltinCommonInstructions::ForEach', 'object': nome,
                      'conditions': [I('BooleanObjectVariable', nome, 'morto', 'True', ''),
                                     I('BooleanObjectVariable', nome, 'morte_feita', 'False', '')],
                      'actions': [I('SetBooleanObjectVariable', nome, 'morte_feita', 'True', ''),
                                  I('Create', '', 'anjo_morte_luz', f'{nome}.CenterX()', f'{nome}.CenterY()', ''),
                                  I('ParticleSystem::ZoneRadius', 'anjo_morte_luz', '=', f'{nome}.morte_luz_raio'),
                                  I('ParticleSystem::SetTank', 'anjo_morte_luz', '=', f'{nome}.morte_luz_qtd')],
                      'events': []})
    comentario = {'type': 'BuiltinCommonInstructions::Comment',
                  'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
                  'comment': 'Ao morrer (uma vez, morte_feita) o anjo solta um estouro de luz: anjo_morte_luz no centro, com '
                             'morte_luz_raio de zona e morte_luz_qtd partículas. A animação morte só some dentro da silhueta.',
                  'comment2': ''}
    grupo['Céu']['events'].append({'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0,
                                   'name': 'Morte dos anjos (partículas de luz)', 'source': '', 'type':
                                   'BuiltinCommonInstructions::Group', 'events': [comentario] + morte, 'parameters': []})

    # 5. acerto da t80: o grupo do condenado em chamas vai para Inferno
    purg = grupo['Purgatório']['events']
    k = next((i for i, e in enumerate(purg) if e.get('name') == 'Condenado em chamas (frenesi)'), None)
    if k is not None:
        grupo['Inferno']['events'].append(purg.pop(k))

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('morte dos anjos com partículas de luz')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
