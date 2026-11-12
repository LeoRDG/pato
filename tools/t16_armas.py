"""Tarefa 16: sprites novos das armas (pasta ~/Game) e arma nova: lança-granadas (tecla 4, explosão em área).

gun_013 = pistola, Shotgun = doze, gun_017 = minigun, gun_016 = lança-granadas (nova).
Rodar:  sh tools/t16_armas_sprites.sh   e depois   python3 tools/t16_armas.py        (pode rodar de novo)
Feche o projeto no GDevelop antes (ou reabra depois sem salvar), senão ele sobrescreve o jogo.json.
Depois de t12_armas.py (que reconstrói o grupo de balas) e de t15_pato_animacoes.py.

Lança-granadas: a granada explode ao tocar no chão ou num inimigo e dá dano em área (100% no centro, 50% na borda do raio).
O dano normal de contato é pulado (projetil.raio > 0); quem tem raio 0 (as outras armas) continua igual.
"""
import copy, json, os, uuid
from PIL import Image
from t12_armas import A, C, E, comentario, grupo, procura, upsert, var

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'jogo.json')
FB = 'FireBullet::FireBullet'
PL = ('pato', 'PlatformerObject')

# escala (sprites de pixel art pequenos) e vitrine de cada arma
SPRITE = {'pistola': 2, 'doze': 4, 'minigun': 1.5, 'lanca': 1.5}   # tamanho aprovado (armas atrás do pato)
LANCA = dict(dano=90, balas=1, cooldown=0.9, pente=4, recarga=2.4, reserva=24, alcance=99999, queda_ini=0, queda_min=1, furos=0,
             repulsao=3, disp_min=0, disp_max=0, vel_mov=0.8, arco=20, raio=150, valocidade_bala=900, recuo=14)
KICK = {'pistola': 7, 'doze': 16, 'minigun': 3, 'lanca': 20}   # px que a arma recua a cada tiro (volta sozinha)
TREMOR = {'pistola': 0, 'doze': 0, 'minigun': 1.4, 'lanca': 0}  # px de tremida de lado enquanto atira (só a minigun)
FOGO = {   # só a lança-granadas tem fumaça (o clarão de todas é o sprite flash_<arma>.png, de t16_flash.py)
    'lanca': dict(tank=40, flow=2000, emitterForceMin=120, emitterForceMax=450, emitterAngleA=-35, emitterAngleB=35, particleLifeTimeMin=0.15,
                  particleLifeTimeMax=0.5, rendererParam1=22, zoneRadius=6, c1=(255, 200, 90), c2=(70, 70, 70), a1=230, s1=100, s2=220, additive=False),
}
# explosão da granada: três emissores de partículas (cópias da poeira), criados juntos no ponto da explosão, do fundo para a frente
EXPLOSAO = {
    'explosao_fumaca': dict(tank=35, flow=1500, emitterForceMin=40, emitterForceMax=160, particleLifeTimeMin=0.7, particleLifeTimeMax=1.4, rendererParam1=46,
                            zoneRadius=22, c1=(90, 90, 90), c2=(40, 40, 40), a1=170, s1=80, s2=220, additive=False, particleGravityY=-60),
    'explosao_fogo': dict(tank=60, flow=4000, emitterForceMin=150, emitterForceMax=520, particleLifeTimeMin=0.25, particleLifeTimeMax=0.55, rendererParam1=40,
                          zoneRadius=14, c1=(255, 230, 120), c2=(200, 50, 10), a1=255, s1=100, s2=30, additive=True, particleGravityY=0),
    'explosao_faiscas': dict(tank=40, flow=4000, emitterForceMin=400, emitterForceMax=900, particleLifeTimeMin=0.3, particleLifeTimeMax=0.7, rendererParam1=6,
                             zoneRadius=6, c1=(255, 240, 160), c2=(255, 120, 0), a1=255, s1=100, s2=40, additive=True, particleGravityY=900),
}
# "sangue" ao acertar um inimigo: um emissor por tipo (cor inicial, cor final, aditivo) e o tipo de cada inimigo
SANGUE = {
    'vermelho': ((200, 20, 20), (90, 0, 0), False),      # gente e bichos de carne
    'escuro': ((140, 10, 30), (50, 0, 10), False),       # demônios: sangue escuro
    'verde': ((110, 200, 40), (30, 90, 10), False),      # gosma verde
    'ciano': ((40, 200, 160), (10, 80, 70), False),      # icor do cutulu
    'azul': ((60, 170, 255), (10, 60, 160), True),       # ectoplasma dos azuis
    'brasa': ((255, 170, 40), (200, 40, 0), True),       # faíscas/brasas
    'lasca': ((150, 100, 60), (70, 45, 25), False),      # lascas de madeira
    'gosma': ((220, 200, 60), (110, 90, 10), False),     # tripa de inseto
    'roxo': ((160, 70, 220), (60, 20, 100), False),
}
SANGUE_DE = {
    'zumbi': 'verde', 'pigman': 'vermelho', 'boss': 'verde', 'atirador': 'vermelho', 'sapo': 'verde', 'cutulu': 'ciano', 'voador': 'brasa',
    'trader': 'roxo', 'condenado': 'vermelho', 'condenada': 'vermelho', 'condenado_torto': 'vermelho', 'condenado_inchado': 'vermelho',
    'condenado_azul': 'azul', 'caveira_azul': 'azul', 'arvore_condenada': 'lasca', 'moscas': 'gosma', 'olho_demoniaco': 'escuro',
    'mina_demoniaca': 'brasa', 'cabeca_voadora': 'escuro', 'diabinho': 'escuro', 'caveira_gigante': 'escuro',
}
FLASH_ESCALA = {'pistola': 3, 'doze': 3.5, 'minigun': 3, 'lanca': 4}   # escala do clarão (pixel art pequeno)
FLASH_VIDA = {'pistola': 0.05, 'doze': 0.07, 'minigun': 0.04, 'lanca': 0.09}   # segundos na tela
HUD_X = {1: 1640, 2: 1700, 3: 1760, 4: 1820}  # 4 slots alinhados à direita (antes 1700/1760/1820)


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events', []))


def pastas(n):
    yield n
    for c in n.get('children', []):
        if 'children' in c:
            yield from pastas(c)


def clona_na_pasta(d, orig, novo):
    for p in pastas(d['objectsFolderStructure']):
        if any(c.get('objectName') == orig for c in p['children']) and not any(c.get('objectName') == novo for c in p['children']):
            p['children'].append({'objectName': novo})
            return


def recurso(d, arquivo):
    nome = arquivo.replace('assets/', '', 1)
    res = d['resources']['resources']
    res[:] = [r for r in res if r['name'] != nome] + [
        {'file': arquivo, 'kind': 'image', 'metadata': '', 'name': nome, 'smoothed': False, 'userAdded': True}]


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    obj = {o['name']: o for o in d['objects']}
    ext = lambda n: [e for e in d['externalEvents'] if e['name'] == n][0]

    # ---------------------------------------------------------- sprites das armas (todas viram pixel art)
    for n in ('pistola', 'doze', 'minigun', 'lanca'):
        recurso(d, f'assets/arma_{n}.png')
    for arq in ('hud/arma_lanca.png', 'hud/slot_4.png', 'hud/slot_4_sel.png', 'hud/slot_4_lock.png', 'hud/pip_lanca.png'):
        recurso(d, 'assets/' + arq)

    # ---------------------------------------------------------- objeto novo: lança-granadas (cópia da doze)
    if 'lanca' not in obj:
        o = copy.deepcopy(obj['doze'])
        o['name'] = 'lanca'
        o['persistentUuid'] = str(uuid.uuid4())
        d['objects'].append(o)
        obj['lanca'] = o
        clona_na_pasta(d, 'doze', 'lanca')
    for g in d['objectsGroups']:
        if g['name'] == 'Arma' and not any(m['name'] == 'lanca' for m in g['objects']):
            g['objects'].append({'name': 'lanca'})
    for n in SPRITE:
        w, h = Image.open(os.path.join(ROOT, 'assets', f'arma_{n}.png')).size
        sp = obj[n]['animations'][0]['directions'][0]['sprites'][0]
        sp.update(image=f'arma_{n}.png', hasCustomCollisionMask=True, customCollisionMask=[[{'x': 0, 'y': 0}, {'x': w, 'y': 0}, {'x': w, 'y': h}, {'x': 0, 'y': h}]])
        upsert(obj[n]['variables'], 'raio', 0)
        # altura do cano: posição vertical da ponta (últimas 3 colunas), em fração da altura da imagem a partir do meio
        px = Image.open(os.path.join(ROOT, 'assets', f'arma_{n}.png')).convert('RGBA')
        ys = [y for x in range(w - 3, w) for y in range(h) if px.getpixel((x, y))[3] > 128]
        upsert(obj[n]['variables'], 'bocal_f', round(sum(ys) / len(ys) / h - 0.5, 3))
        upsert(obj[n]['variables'], 'kick', KICK[n])
        upsert(obj[n]['variables'], 'tremor', TREMOR[n])
    L = LANCA
    o = obj['lanca']
    for k in ('dano', 'alcance', 'queda_ini', 'queda_min', 'furos', 'repulsao', 'disp_min', 'disp_max', 'vel_mov', 'raio', 'valocidade_bala', 'recuo'):
        upsert(o['variables'], k, L[k])
    upsert(o['variables'], 'cooldown_base', L['cooldown'])
    upsert(o['variables'], 'recarga_base', L['recarga'])
    upsert(o['variables'], 'equipada', False)
    b = [b for b in o['behaviors'] if b['type'] == FB][0]
    b.update(FireCooldown=L['cooldown'], BulletQuantity=L['balas'], FiringArc=L['arco'], AngleVariance=0, ShotsPerReload=L['pente'],
             ReloadDuration=L['recarga'], MaxAmmo=L['reserva'], StartingAmmo=L['reserva'])
    upsert(obj['projetil']['variables'], 'raio', 0)
    upsert(obj['projetil']['variables'], 'boom', False)

    for velho in ('fogo_pistola', 'fogo_doze', 'fogo_minigun'):   # tentativa anterior (partículas pareciam fumaça)
        d['objects'][:] = [o for o in d['objects'] if o['name'] != velho]
        obj.pop(velho, None)
        for pasta in pastas(d['objectsFolderStructure']):
            pasta['children'] = [c for c in pasta['children'] if c.get('objectName') != velho]
    for n in SPRITE:
        recurso(d, f'assets/flash_{n}.png')
    if 'flash_cano' not in obj:
        fl = {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': 'flash_cano', 'persistentUuid': str(uuid.uuid4()),
              'type': 'Sprite', 'updateIfNotVisible': False, 'variables': [var('dur', 0.05)], 'effects': [], 'behaviors': [], 'animations': []}
        d['objects'].append(fl)
        obj['flash_cano'] = fl
        clona_na_pasta(d, 'doze', 'flash_cano')
    upsert(obj['flash_cano']['variables'], 'dur', 0.05)
    obj['flash_cano']['animations'] = []
    for n in SPRITE:
        w, h = Image.open(os.path.join(ROOT, 'assets', f'flash_{n}.png')).size
        pt = {'x': 0, 'y': h / 2}
        obj['flash_cano']['animations'].append({'name': n, 'useMultipleDirections': False, 'directions': [{'looping': False, 'timeBetweenFrames': 0.08, 'sprites': [{
            'hasCustomCollisionMask': False, 'image': f'flash_{n}.png', 'points': [], 'originPoint': dict(pt, name='origine'),
            'centerPoint': dict(pt, name='centre', automatic=False), 'customCollisionMask': []}]}]})
    for n, f in FOGO.items():
        nome = f'fogo_{n}'
        if nome not in obj:
            em = copy.deepcopy(obj['poeira'])
            em['persistentUuid'] = str(uuid.uuid4())
            d['objects'].append(em)
            obj[nome] = em
            clona_na_pasta(d, 'poeira', nome)
        f = dict(f)
        c1, c2 = f.pop('c1'), f.pop('c2')
        obj[nome].update(f, name=nome, flow=f['flow'], maxParticleNb=80, additive=f['additive'], particleAlpha1=f.pop('a1'), particleAlpha2=0,
                         particleSize1=f.pop('s1'), particleSize2=f.pop('s2'), particleRed1=c1[0], particleGreen1=c1[1], particleBlue1=c1[2],
                         particleRed2=c2[0], particleGreen2=c2[1], particleBlue2=c2[2], particleColor1=';'.join(map(str, c1)),
                         particleColor2=';'.join(map(str, c2)), destroyWhenNoParticles=True, variables=[])

    for nome, f in EXPLOSAO.items():
        if nome not in obj:
            em = copy.deepcopy(obj['poeira'])
            em['persistentUuid'] = str(uuid.uuid4())
            d['objects'].append(em)
            obj[nome] = em
            clona_na_pasta(d, 'poeira', nome)
        f = dict(f)
        c1, c2 = f.pop('c1'), f.pop('c2')
        obj[nome].update(f, name=nome, emitterAngleA=0, emitterAngleB=360, maxParticleNb=120, particleAlpha1=f.pop('a1'), particleAlpha2=0,
                         particleSize1=f.pop('s1'), particleSize2=f.pop('s2'), particleRed1=c1[0], particleGreen1=c1[1], particleBlue1=c1[2],
                         particleRed2=c2[0], particleGreen2=c2[1], particleBlue2=c2[2], particleColor1=';'.join(map(str, c1)),
                         particleColor2=';'.join(map(str, c2)), particleGravityX=0, destroyWhenNoParticles=True, variables=[])

    for tipo, (c1, c2, adit) in SANGUE.items():
        nome = f'sangue_{tipo}'
        if nome not in obj:
            em = copy.deepcopy(obj['poeira'])
            em['persistentUuid'] = str(uuid.uuid4())
            d['objects'].append(em)
            obj[nome] = em
            clona_na_pasta(d, 'poeira', nome)
        obj[nome].update(name=nome, tank=14, flow=2000, emitterForceMin=150, emitterForceMax=420, emitterAngleA=-40, emitterAngleB=40,
                         particleLifeTimeMin=0.25, particleLifeTimeMax=0.5, rendererParam1=7, zoneRadius=4, maxParticleNb=40, additive=adit,
                         particleAlpha1=255, particleAlpha2=110, particleSize1=100, particleSize2=60, particleGravityX=0, particleGravityY=900,
                         particleRed1=c1[0], particleGreen1=c1[1], particleBlue1=c1[2], particleRed2=c2[0], particleGreen2=c2[1], particleBlue2=c2[2],
                         particleColor1=';'.join(map(str, c1)), particleColor2=';'.join(map(str, c2)), destroyWhenNoParticles=True, variables=[])
    for g in d['objectsGroups']:
        if g['name'] == 'Inimigo':
            for m in g['objects']:
                vs = obj[m['name']]['variables']
                velho = [v for v in vs if v['name'] == 'sangue']
                if velho:
                    velho[0].update(type='string', value=SANGUE_DE.get(m['name'], 'vermelho'))
                else:
                    vs.append({'name': 'sangue', 'persistentUuid': str(uuid.uuid4()), 'type': 'string', 'value': SANGUE_DE.get(m['name'], 'vermelho')})

    # arma liberada (como a doze e a minigun por enquanto)
    armas = [v for v in d['variables'] if v['name'] == 'armas'][0]
    if not any(c['name'] == 'lanca' for c in armas['children']):
        armas['children'].append({'name': 'lanca', 'persistentUuid': str(uuid.uuid4()), 'type': 'boolean', 'value': True})

    jog = ext('Jogador')
    # ---------------------------------------------------------- Jogador: criar, escalar, equipar, trocar
    for e in walk(jog['events']):
        acts = e.get('actions', [])
        if any(a['type']['value'] == 'Create' and a['parameters'][1] == 'minigun' for a in acts):
            # (re)escreve sempre: cria a lança depois da minigun e fixa a escala de cada arma antes de esconder todas
            acts[:] = [a for a in acts if not (a['type']['value'].endswith('ScalableBehavior::SetValue') and a['parameters'][0] in SPRITE)
                       and not (a['type']['value'] in ('Create',) and a['parameters'][1] == 'lanca') and not (a['type']['value'] == 'Hide' and a['parameters'][0] == 'lanca')]
            i = [k for k, a in enumerate(acts) if a['type']['value'] == 'Create' and a['parameters'][1] == 'minigun'][0]
            acts.insert(i + 1, A('Create', '', 'lanca', 'pato.X()', 'pato.Y()', ''))
            j = [k for k, a in enumerate(acts) if a['type']['value'] == 'Hide'][0]
            acts[j:j] = [A('ScalableCapability::ScalableBehavior::SetValue', n, 'Scale', '=', str(sc)) for n, sc in SPRITE.items()]
    ini = [e for e in walk(jog['events']) if any(a['type']['value'] == 'SetBooleanObjectVariable' and a['parameters'][:3] == ['minigun', 'equipada', 'True'] and
                                                   any(c['type']['value'] == 'StringVariable' for c in e.get('conditions', [])) for a in e.get('actions', []))][0]
    pai = [x for x in walk(jog['events']) if ini in x.get('events', [])]
    lista = (pai[0]['events'] if pai else jog['events'])
    lista[:] = [e for e in lista if not any(c['parameters'][2:3] == ['"lanca"'] for c in e.get('conditions', []))]
    lista.append(E([C('StringVariable', 'arma_atual', '=', '"lanca"')], [A('SetBooleanObjectVariable', 'lanca', 'equipada', 'True', ''), A('Show', 'lanca', '')]))

    troca = [e for e in walk(jog['events']) if e.get('name') == 'Troca de Arma'][0]
    troca['events'] = [e for e in troca['events'] if not any(c['parameters'][1:2] == ['"Num4"'] for c in e.get('conditions', []))]
    troca['events'].append(E([C('KeyFromTextJustPressed', '', '"Num4"'), C('BooleanVariable', 'armas.lanca', 'True', '')],
                             [A('SetBooleanObjectVariable', 'Arma', 'equipada', 'False', ''), A('SetBooleanObjectVariable', 'lanca', 'equipada', 'True', ''),
                              A('Hide', 'Arma', ''), A('Show', 'lanca', ''), A('SetStringVariable', 'arma_atual', '=', '"lanca"')]))

    # ---------------------------------------------------------- mira: arma menor e junto ao corpo, ângulo limitado, laser e tiro saem da boca do cano
    for k in ('bocal_x', 'bocal_y', 'mira_a', 'mira_lado', 'mira_graus', 'coice', 'coice_j'):
        upsert(d['variables'], k, 0)
    upsert(d['variables'], 'mira_lado', 1)
    equip = lambda: C('BooleanObjectVariable', 'Arma', 'equipada', 'True', '')
    MAXANG = 55   # graus acima/abaixo da horizontal
    LARG = 'Arma.Width()'
    todos = list(walk(jog['events']))
    acha = lambda f: [e for e in todos if f(e)][0]
    tem_a = lambda e, tipo, obj=None: any(a['type']['value'] == tipo and (obj is None or a['parameters'][0] == obj) for a in e.get('actions', []))
    e_pos = acha(lambda e: tem_a(e, 'SetXY', 'Arma'))
    e_pos['conditions'] = [equip()]
    # coice: a arma recua ao longo do cano por "coice" px a cada tiro; a minigun ainda treme de lado (coice_j)
    e_pos['actions'] = [A('SetNumberVariable', 'coice_j', '=', 'RandomFloatInRange(-1, 1) * Arma.tremor * clamp(coice / max(Arma.kick, 0.01), 0, 1)'),
                        A('SetXY', 'Arma', '=', f'pato.CenterX() + mira_lado * (15 + 0.2 * {LARG}) - {LARG} / 2 - mira_lado * cos(mira_a) * coice - sin(mira_a) * coice_j', '=',
                          'pato.Y() + pato.Height() * 0.68 - Arma.Height() / 2 - sin(mira_a) * coice + mira_lado * cos(mira_a) * coice_j'),
                        A('RotateTowardObject', 'Arma', 'alvo', '5000', ''),
                        # a arma fica atrás do pato (ele a segura com a outra mão); o clarão do cano fica entre os dois
                        A('SetZOrder', 'Arma', '=', 'pato.ZOrder() - 2')]
    e_esq = acha(lambda e: any(a['type']['value'].endswith('FlipX') and a['parameters'][2] == 'yes' for a in e.get('actions', [])))
    e_esq['conditions'] = [C('BuiltinCommonInstructions::CompareNumbers', 'MouseX()', '<', 'pato.CenterX()')]
    e_esq['actions'] = [a for a in e_esq['actions'] if a['type']['value'] != 'SetX']
    e_esq['events'] = []   # o lado já entra na posição (mira_lado): deslocar a arma depois de girar deixava o cano torto em relação ao laser
    e_dir = acha(lambda e: any(a['type']['value'].endswith('FlipX') and a['parameters'][2] == 'no' for a in e.get('actions', [])))
    e_dir['conditions'] = [C('BuiltinCommonInstructions::CompareNumbers', 'MouseX()', '>=', 'pato.CenterX()')]
    # ângulo de mira limitado (recuo incluso); o lado vem do mouse em relação ao centro do pato
    DIST = 'DistanceBetweenPositions(Arma.CenterX(), Arma.CenterY(), MouseX(), MouseY())'
    e_alvo = acha(lambda e: tem_a(e, 'SetXY', 'alvo'))
    e_alvo['conditions'] = [equip()]
    e_alvo['actions'] = [
        A('SetNumberVariable', 'mira_lado', '=', 'sign(MouseX() - pato.CenterX() + 0.001)'),
        A('SetNumberVariable', 'mira_a', '=', f'clamp(atan2(MouseY() - Arma.CenterY(), abs(MouseX() - Arma.CenterX())) - ToRad(recuo), -ToRad({MAXANG}), ToRad({MAXANG}))'),
        A('SetXY', 'alvo', '=', f'Arma.CenterX() + mira_lado * cos(mira_a) * {DIST} - alvo.Width() * .5', '=', f'Arma.CenterY() + sin(mira_a) * {DIST} - alvo.Height() * .5'),
        A('HideCursor', ''),
        A('SetNumberVariable', 'recuo', '*', 'pow(0.98, TimeDelta() * 60)'),
        A('SetNumberVariable', 'coice', '*', 'pow(0.000001, TimeDelta())'),
        A('SetNumberVariable', 'mira_graus', '=', 'ToDeg(atan2(sin(mira_a), mira_lado * cos(mira_a)))'),
        A('OpacityCapability::OpacityBehavior::SetValue', 'alvo', 'Opacity', '=', '250'),
        # boca do cano: ponta da arma ao longo da mira, com o cano na altura certa do sprite (bocal_f); no lado esquerdo a arma está espelhada
        A('SetNumberVariable', 'bocal_x', '=', f'Arma.CenterX() + mira_lado * cos(mira_a) * {LARG} / 2 - mira_lado * sin(mira_a) * Arma.bocal_f * Arma.Height()'),
        A('SetNumberVariable', 'bocal_y', '=', f'Arma.CenterY() + sin(mira_a) * {LARG} / 2 + cos(mira_a) * Arma.bocal_f * Arma.Height()'),
        A('SetNumberVariable', 'laser_x', '=', 'bocal_x + mira_lado * cos(mira_a) * 4000'),
        A('SetNumberVariable', 'laser_y', '=', 'bocal_y + sin(mira_a) * 4000'),
    ]
    e_ray = acha(lambda e: any(c['type']['value'] == 'RaycastToPosition' for c in e.get('conditions', [])))
    for c in e_ray['conditions']:
        if c['type']['value'] == 'RaycastToPosition':
            c['parameters'][1:3] = ['bocal_x', 'bocal_y']
    e_las = acha(lambda e: tem_a(e, 'PrimitiveDrawing::LineV2', 'laser'))
    for a in e_las['actions']:
        if a['type']['value'] == 'PrimitiveDrawing::LineV2':
            a['parameters'][1:3] = ['bocal_x', 'bocal_y']
    mira_grp = [x for x in todos if e_pos in x.get('events', [])][0]['events']
    mira_grp[:] = [x for x in mira_grp if x.get('name') != 'Clarão']
    mira_grp.append(grupo('Clarão', [
        E([], [A('SetXY', 'flash_cano', '=', 'bocal_x', '=', 'bocal_y'), A('SetAngle', 'flash_cano', '=', 'mira_graus'), A('SetZOrder', 'flash_cano', '=', 'pato.ZOrder() - 1')]),
        E([C('CompareObjectTimer', 'flash_cano', '"ttl"', '>', 'flash_cano.dur')], [A('Delete', 'flash_cano', '')]),
    ]))
    tiro = acha(lambda e: tem_a(e, FB + '::FireTowardObject'))
    for a in tiro['actions']:
        if a['type']['value'] == FB + '::FireTowardObject':
            a['parameters'][2:4] = ['bocal_x', 'bocal_y']

    # ---------------------------------------------------------- sons sintetizados (t17_sons_armas.py): um por arma + explosão, quase sem variação de tom
    for n in ('pistola', 'doze', 'minigun', 'lanca', 'explosao'):
        arq = f'assets/som_{n}.wav'
        res = d['resources']['resources']
        res[:] = [r for r in res if r['name'] != f'som_{n}.wav'] + [{'file': arq, 'kind': 'audio', 'metadata': '', 'name': f'som_{n}.wav', 'preloadAsMusic': False,
                                                                       'preloadAsSound': True, 'preloadInCache': False, 'userAdded': True}]
    TOM = {'som_pistola.wav': '.96, 1.04', 'som_doze.wav': '.97, 1.03', 'som_minigun.wav': '.95, 1.05', 'som_lanca.wav': '.97, 1.03', 'som_explosao.wav': '.95, 1.05'}
    ANTIGO = {'glock18-1[1].wav': 'som_pistola.wav', 'shotgun.wav': 'som_doze.wav', 'minigun.wav': 'som_minigun.wav', 'tiro.wav': 'som_lanca.wav',
              'sawedoff-1[1].wav': 'som_explosao.wav'}
    # ---------------------------------------------------------- som do tiro da lança-granadas
    rs = [e for e in walk(jog['events']) if any(c['type']['value'] == FB + '::HasJustFired' and c['parameters'][0] == 'minigun'
                                                                       for c in e.get('conditions', []))][0]
    pai = [x for x in walk(jog['events']) if rs in x.get('events', [])][0]['events']
    pai[:] = [e for e in pai if not any(c['parameters'][:1] == ['lanca'] for c in e.get('conditions', []))]
    rc = [e for e in walk(jog['events']) if any(c['type']['value'] == FB + '::HasJustFired' and c['parameters'][0] == 'Arma' for c in e.get('conditions', []))
          and any(a['parameters'][:1] == ['recuo'] for a in e.get('actions', []))][0]
    rc['actions'] = [a for a in rc['actions'] if a['parameters'][:1] != ['coice']] + [A('SetNumberVariable', 'coice', '=', 'Arma.kick')]
    pai[:] = [e for e in pai if e.get('name') != 'Fogo do cano']
    pai.append(grupo('Fogo do cano', [comentario('Cada tiro cria o clarão (flash_cano, animação da arma) na boca do cano, apontado na direção do tiro; '
                                                 'o grupo Clarão segue o cano e apaga o clarão em poucos centésimos de segundo.')] + [
        E([C(FB + '::HasJustFired', n, 'FireBullet', '')], [
            A('Create', '', 'flash_cano', 'bocal_x', 'bocal_y', ''), A('AnimatableCapability::AnimatableBehavior::SetName', 'flash_cano', 'Animation', '=', f'"{n}"'),
            A('SetNumberObjectVariable', 'flash_cano', 'dur', '=', str(FLASH_VIDA[n])),
            A('ResetObjectTimer', 'flash_cano', '"ttl"'),
            A('ScalableCapability::ScalableBehavior::SetValue', 'flash_cano', 'Scale', '=', f'{FLASH_ESCALA[n]} * RandomFloatInRange(0.85, 1.2)'),
            A('SetAngle', 'flash_cano', '=', 'mira_graus')] + ([A('Create', '', f'fogo_{n}', 'bocal_x', 'bocal_y', ''), A('SetAngle', f'fogo_{n}', '=', 'mira_graus')] if n in FOGO else []))
        for n in SPRITE]))
    pai.append(E([C(FB + '::HasJustFired', 'lanca', 'FireBullet', '')],
                 [A('PlaySoundOnChannel', '', 'som_lanca.wav', '1', '90', '90', '1'), A('SetSoundChannelPitch', '', '1', '=', 'RandomFloatInRange(.97, 1.03)')]))

    for e in walk(jog['events']):
        acts = e.get('actions', [])
        if any(a['type']['value'] == 'PreloadSound' for a in acts):   # pré-carrega os sons novos no lugar do antigo shotgun.wav
            acts[:] = [a for a in acts if a['type']['value'] != 'PreloadSound'] + [A('PreloadSound', '', n) for n in TOM]
        for i, a in enumerate(acts):
            if a['type']['value'] == 'PlaySoundOnChannel' and a['parameters'][1] in ANTIGO:
                novo = ANTIGO[a['parameters'][1]]
                a['parameters'][1] = novo
                if i + 1 < len(acts) and acts[i + 1]['type']['value'] == 'SetSoundChannelPitch':
                    acts[i + 1]['parameters'][3] = f'RandomFloatInRange({TOM[novo]})'
            elif a['type']['value'] == 'PlaySoundOnChannel' and a['parameters'][1] in TOM and i + 1 < len(acts) and acts[i + 1]['type']['value'] == 'SetSoundChannelPitch':
                acts[i + 1]['parameters'][3] = f'RandomFloatInRange({TOM[a["parameters"][1]]})'

    # ---------------------------------------------------------- combate: a bala copia o raio; granada explode
    proj = procura(ext('Combate')['events'], 'Projéteis')
    nasc = [e for e in walk(proj['events']) if any(a['parameters'][:2] == ['projetil', 'serie'] for a in e.get('actions', []))][0]
    nasc['actions'] = [a for a in nasc['actions'] if a['parameters'][:2] != ['projetil', 'raio']]
    nasc['actions'].insert(5, A('SetNumberObjectVariable', 'projetil', 'raio', '=', 'Arma.raio'))
    hit = [e for e in proj['events'] if e['type'] == 'BuiltinCommonInstructions::ForEach' and any(c['parameters'][:2] == ['projetil', 'Inimigo'] for c in e['conditions'])][0]
    hit['conditions'] = [c for c in hit['conditions'] if c['parameters'][:2] != ['projetil', 'raio']]
    hit['conditions'].insert(0, C('NumberObjectVariable', 'projetil', 'raio', '<=', '0'))

    # acerto: sai o sprite "hit" e entra o jorro de partículas do tipo de sangue do inimigo, na direção em que a bala ia
    hit['actions'] = [a for a in hit['actions'] if a['parameters'][:1] != ['hit'] and a['parameters'][1:2] != ['hit']]
    hit['events'] = [e for e in hit['events'] if not any(c['parameters'][:2] == ['Inimigo', 'sangue'] for c in e.get('conditions', []))]
    hit['events'][0:0] = [E([C('StringObjectVariable', 'Inimigo', 'sangue', '=', f'"{tipo}"')],
                            [A('Create', '', f'sangue_{tipo}', 'projetil.CenterX()', 'projetil.CenterY()', ''), A('SetAngle', f'sangue_{tipo}', '=', 'projetil.Angle()')])
                          for tipo in SANGUE]
    DIST = 'DistanceBetweenPositions(Inimigo.CenterX(), Inimigo.CenterY(), projetil.CenterX(), projetil.CenterY())'
    boom = lambda cond: E(cond, [A('SetBooleanObjectVariable', 'projetil', 'boom', 'True', '')], tipo='BuiltinCommonInstructions::ForEach', object='projetil')
    grupo_expl = grupo('Explosão da granada', [
        comentario('Granada (projetil.raio > 0) explode ao tocar no chão ou num inimigo: dano em área, 100% no centro e 50% na borda do raio, '
                   'repulsão para longe do centro, explosão de partículas (fumaça, fogo e faíscas) e som. Depois a granada some.'),
        boom([C('NumberObjectVariable', 'projetil', 'raio', '>', '0'), C('CollisionNP', 'projetil', 'chao', '', '', '')]),
        boom([C('NumberObjectVariable', 'projetil', 'raio', '>', '0'), C('CollisionNP', 'projetil', 'Inimigo', '', '', ''),
              C('BooleanObjectVariable', 'Inimigo', 'morto', 'False', '')]),
        E([C('BooleanObjectVariable', 'projetil', 'boom', 'True', '')], [
        ] + [A('Create', '', nome, 'projetil.CenterX()', 'projetil.CenterY()', '') for nome in EXPLOSAO] + [
            A('PlaySoundOnChannel', '', 'som_explosao.wav', '3', '90', '90', '1'),
            A('SetSoundChannelPitch', '', '3', '=', 'RandomFloatInRange(.95, 1.05)'),
        ], [
            E([C('BuiltinCommonInstructions::CompareNumbers', DIST, '<', 'projetil.raio'), C('BooleanObjectVariable', 'Inimigo', 'morto', 'False', '')], [
                A('SetNumberObjectVariable', 'Inimigo', 'vida', '-',
                  f'max(1, round(projetil.dano * (1 - 0.5 * {DIST} / projetil.raio) * RandomFloatInRange(0.9, 1.1) * GlobalVariable(mult_dano)))'),
                A('SetBooleanObjectVariable', 'Inimigo', 'acertado', 'True', ''),
                A('SetNumberObjectVariable', 'Inimigo', 'kb_dir', '=', f'sign(Inimigo.CenterX() - projetil.CenterX() + 0.001) * projetil.repulsao * (1 - 0.5 * {DIST} / projetil.raio)'),
            ]),
            E([], [A('Delete', 'projetil', '')]),
        ], tipo='BuiltinCommonInstructions::ForEach', object='projetil'),
    ])
    upsert(obj['projetil']['variables'], 'gy', 0)
    grav = grupo('Gravidade da granada', [
        comentario('Granada (projetil.raio > 0) cai em arco: gravidade alta (900 px/s2) somada à velocidade do tiro.'),
        E([C('NumberObjectVariable', 'projetil', 'raio', '>', '0'), C('BooleanObjectVariable', 'projetil', 'iniciado', 'True', '')], [
            A('SetNumberObjectVariable', 'projetil', 'gy', '+', '900 * TimeDelta()'),
            A('SetY', 'projetil', '+', 'projetil.gy * TimeDelta()'),
        ], tipo='BuiltinCommonInstructions::ForEach', object='projetil'),
    ])
    proj['events'] = [e for e in proj['events'] if e.get('name') not in ('Explosão da granada', 'Gravidade da granada')]
    i = [k for k, e in enumerate(proj['events']) if e['type'] == 'BuiltinCommonInstructions::Standard' and
         any(c['parameters'][:2] == ['projetil', 'chao'] for c in e['conditions'])][0]
    proj['events'].insert(i, grupo_expl)
    proj['events'].insert(i, grav)

    # ---------------------------------------------------------- HUD: ícone, nome, pips, slot 4
    ico = obj['hud_arma_icone']
    if not any(a['name'] == 'lanca' for a in ico['animations']):
        an = copy.deepcopy([a for a in ico['animations'] if a['name'] == 'doze'][0])
        an['name'] = 'lanca'
        an['directions'][0]['sprites'][0]['image'] = 'hud/arma_lanca.png'
        ico['animations'].append(an)
    if 'hud_pips_lanca' not in obj:
        p = copy.deepcopy(obj['hud_pips_doze'])
        p.update(name='hud_pips_lanca', persistentUuid=str(uuid.uuid4()), texture='hud/pip_lanca.png')
        d['objects'].append(p)
        clona_na_pasta(d, 'hud_pips_doze', 'hud_pips_lanca')
    if 'hud_slot4' not in obj:
        s4 = copy.deepcopy(obj['hud_slot3'])
        s4.update(name='hud_slot4', persistentUuid=str(uuid.uuid4()))
        for a in s4['animations']:
            for sp in a['directions'][0]['sprites']:
                sp['image'] = sp['image'].replace('slot_3', 'slot_4')
        d['objects'].append(s4)
        clona_na_pasta(d, 'hud_slot3', 'hud_slot4')

    hud = ext('HUD')
    for e in walk(hud['events']):
        acts = e.get('actions', [])
        conds = e.get('conditions', [])
        if conds and conds[0]['type']['value'] == 'BooleanObjectVariable' and conds[0]['parameters'][:3] == ['doze', 'equipada', 'True'] and \
                any(a['parameters'][:1] == ['hud_arma_icone'] for a in acts):
            pai = [x for x in walk(hud['events']) if e in x.get('events', [])][0]['events']
            pai[:] = [x for x in pai if not (x.get('conditions') and x['conditions'][0]['parameters'][:1] == ['lanca'])]
            nova = copy.deepcopy(e)
            nova['conditions'][0]['parameters'][0] = 'lanca'
            for a in nova['actions']:
                a['parameters'] = [str(x).replace('"doze"', '"lanca"').replace('"DOZE"', '"LANÇA-GRANADAS"').replace('hud_pips_doze', 'hud_pips_lanca')
                                   .replace('10 * Arma', '12 * Arma') for x in a['parameters']]
            pai.append(nova)
        if conds and conds[0]['parameters'][:1] == ['pistola'] and any(a['parameters'][:1] == ['hud_slot1'] for a in acts):
            pai = [x for x in walk(hud['events']) if e in x.get('events', [])][0]['events']
            pai[:] = [x for x in pai if not any(a['parameters'][:1] == ['hud_slot4'] for a in x.get('actions', []))]
            pai.append(E([C('BooleanObjectVariable', 'lanca', 'equipada', 'True', '')], [A('AnimatableCapability::AnimatableBehavior::SetName', 'hud_slot4', 'Animation', '=', '"sel"')]))
            pai.append(E([C('BooleanVariable', 'armas.lanca', 'False', '')], [A('AnimatableCapability::AnimatableBehavior::SetName', 'hud_slot4', 'Animation', '=', '"lock"')]))
        for a in acts:
            if a['type']['value'] == 'AnimatableCapability::AnimatableBehavior::SetName' and a['parameters'][0] == 'hud_slot3' and a['parameters'][-1] == '"normal"' \
                    and not any(x['parameters'][0] == 'hud_slot4' for x in acts):
                acts.append(A('AnimatableCapability::AnimatableBehavior::SetName', 'hud_slot4', 'Animation', '=', '"normal"'))
        if any(a['type']['value'] == 'Hide' and a['parameters'][0] == 'hud_pips_minigun' for a in acts) and not any(a['parameters'][0] == 'hud_pips_lanca' for a in acts):
            acts.append(A('Hide', 'hud_pips_lanca'))

    for lay in d['layouts']:
        inst = lay['instances']
        s3 = [i for i in inst if i['name'] == 'hud_slot3']
        if not s3:
            continue
        for k, nome in ((1, 'hud_slot1'), (2, 'hud_slot2'), (3, 'hud_slot3')):
            for i in inst:
                if i['name'] == nome:
                    i['x'] = HUD_X[k]
        if not any(i['name'] == 'hud_slot4' for i in inst):
            n = copy.deepcopy(s3[0])
            n.update(name='hud_slot4', x=HUD_X[4], persistentUuid=str(uuid.uuid4()))
            inst.append(n)
        if not any(i['name'] == 'hud_pips_lanca' for i in inst):
            n = copy.deepcopy([i for i in inst if i['name'] == 'hud_pips_doze'][0])
            n.update(name='hud_pips_lanca', persistentUuid=str(uuid.uuid4()))
            inst.append(n)

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
