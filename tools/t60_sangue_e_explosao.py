"""Tarefa 60: poça de sangue (deixa o pato lento e pula menos) e a explosão de bolas de fogo do demônio chefe.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - imagens (geradas aqui, só se ainda não existem): assets/demonio_chefe/bola_fogo_NN.png (bola de fogo apontando
    para a direita, com as cores das chamas do próprio demônio, 3x);
  - a poça de sangue que já existe (objeto sangue) passa a atrasar o pato: quem encosta nela anda a
    sangue.vel_fator da velocidade e pula com sangue.pulo_fator da força (o pulo que começa no sangue fica baixo
    até o fim). Eventos externos "Sangue";
  - pato.no_sangue e pato.pulo_forca_normal (força do pulo guardada no começo da cena);
  - demonio_chefe: animação "explosao" (os 10 primeiros quadros da morte, pegando fogo, e de volta, para voltar
    inteiro à pose parada) e o ataque: a cada explosao_espera s ele explode e, no auge (explosao_disparo s), solta
    explosao_bolas bolas de fogo em círculo (ângulo inicial sorteado), a explosao_vel px/s, que nascem a
    explosao_raio px do centro, tiram explosao_dano e somem no terreno ou depois de explosao_vida s.
    Os dois ataques usam o estado "atacar" (para tiro não interromper); demonio_chefe.golpe diz qual
    ("cutelo" ou "explosao");
  - bola_fogo (sprite, pasta inimigos/chefe) e o que ela faz entram nos eventos "Chefe".
Os eventos "Chefe" só são trocados se ainda estão como tools/t59_demonio_chefe.py os deixou; se você já mexeu
neles, o script para e avisa em vez de sobrescrever.
"""
import copy, json, math, os, sys, uuid
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, B, P = 'demonio_chefe', 'bola_fogo', 'sangue'
BOLA_IMGS = [f'assets/demonio_chefe/bola_fogo_{i:02d}.png' for i in range(4)]
SANGUE = ['#1e0205', '#2f0408', '#45070d', '#600b13', '#7e1119', '#9c1a22', '#c43a40', '#e98a8a']
FOGO = ['#6c1e12', '#c1571d', '#e4c817', '#eff713']          # chamas do demônio, da mais escura à mais clara
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

VARS_POCA = [('vel_fator', 'number', 0.5), ('pulo_fator', 'number', 0.65)]
VARS_PATO = [('no_sangue', 'boolean', False), ('pulo_forca_normal', 'number', 0)]
VARS_BOLA = [('dano', 'number', 0), ('vida', 'number', 0)]
VARS_CHEFE = [('golpe', 'string', 'cutelo'), ('explosao_espera', 'number', 7), ('explosao_disparo', 'number', 0.72),
              ('explosao_bolas', 'number', 12), ('explosao_vel', 'number', 520), ('explosao_raio', 'number', 80),
              ('explosao_dano', 'number', 25), ('explosao_vida', 'number', 3), ('explosao_som_volume', 'number', 80),
              ('explosao_feita', 'boolean', False), ('explosao_angulo', 'number', 0), ('bola_i', 'number', 0)]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t60/' + '/'.join(p)))


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


# ------------------------------------------------------------------ imagens
def bola(fase):
    """20 x 12 nativo, apontando para a direita: cabeça redonda e cauda que tremula (fase 0..3)."""
    W, H = 20, 12
    cx, cy, r, L = 14.0, 5.5, 4.6, 14.0
    rnd = np.random.default_rng(60 + fase)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    ph = fase * math.pi / 2
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, (y - cy) * 1.1)
            cabeca = 1 - d / r
            cauda = 0.0
            if x < cx:
                t = (cx - x) / L
                yc = cy + 1.3 * math.sin(t * 6 - ph) * t
                meia = r * max(0.0, 1 - t) ** 0.8
                if meia > 0:
                    cauda = (1 - abs(y - yc) / meia) * (1 - t) * 0.8
            calor = max(cabeca, cauda) + (BAYER[y % 4][x % 4] / 16 - .5) * 0.12
            for lim, c in ((0.62, 3), (0.42, 2), (0.2, 1), (0.04, 0)):
                if calor > lim:
                    px[x, y] = rgb(FOGO[c])
                    break
    for _ in range(3):                                                          # fagulhas soltas atrás
        x, y = int(rnd.integers(0, 6)), int(rnd.integers(2, 10))
        px[x, y] = rgb(FOGO[int(rnd.integers(1, 3))])
    return im.resize((W * 3, H * 3), Image.NEAREST)


def desenha():
    for rel, f in [(b, (lambda i: lambda: bola(i))(i)) for i, b in enumerate(BOLA_IMGS)]:
        caminho = os.path.join(RAIZ, rel)
        if not os.path.exists(caminho):
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            f().save(caminho)


# ------------------------------------------------------------------ eventos
I, E, grupo = t59.I, t59.E, t59.grupo


def num(o, v, op, x):
    return I('SetNumberObjectVariable', o, v, op, x)


def eventos_sangue():
    em = I('CollisionNP', 'pato', P, '', '', '')
    return [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Poça de sangue: quem anda nela fica lento. O pato encostando num sangue anda a vel_fator da '
                    'velocidade máxima (a velocidade é cortada depois dos outros eventos, então bhop e upgrades continuam '
                    'valendo fora dela; o dash não é cortado) e pula com pulo_fator da força guardada em pato.pulo_forca_normal.'},
        grupo('Poça de sangue', [
            E([I('SceneJustBegins', '')], [num('pato', 'pulo_forca_normal', '=', 'pato.PlatformerObject::JumpSpeed()')]),
            E([em, I('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
              [I('SetBooleanObjectVariable', 'pato', 'no_sangue', 'True', ''),
               I('PlatformBehavior::JumpSpeed', 'pato', 'PlatformerObject', '=', f'pato.pulo_forca_normal * {P}.pulo_fator')], [
                E([I('AdvancedJump::HorizontalDash::IsDashing', 'pato', 'HorizontalDash', '', inv=True),
                   I('BuiltinCommonInstructions::CompareNumbers', 'abs(pato.PlatformerObject::CurrentSpeed())', '>',
                     f'pato.PlatformerObject::MaxSpeed() * {P}.vel_fator')],
                  [I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', 'pato', 'PlatformerObject', '=',
                     f'sign(pato.PlatformerObject::CurrentSpeed()) * pato.PlatformerObject::MaxSpeed() * {P}.vel_fator')]),
            ]),
            E([I('CollisionNP', 'pato', P, '', '', '', inv=True),
               I('BooleanObjectVariable', 'pato', 'no_sangue', 'True', '')],
              [I('SetBooleanObjectVariable', 'pato', 'no_sangue', 'False', ''),
               I('PlatformBehavior::JumpSpeed', 'pato', 'PlatformerObject', '=', 'pato.pulo_forca_normal')]),
        ]),
    ]


def acha(evs, pred):
    for e in evs:
        if pred(e):
            return e
        r = acha(e.get('events', []), pred)
        if r is not None:
            return r
    return None


def tem(e, tipo, *params):
    return any(i['type']['value'] == tipo and i['parameters'][:len(params)] == list(params)
               for i in e.get('conditions', []) + e.get('actions', []))


def eventos_chefe(base):
    """Os eventos "Chefe" de t59 com o golpe marcado ("cutelo"/"explosao"), a explosão e as bolas de fogo."""
    evs = copy.deepcopy(base)
    estado = lambda op, s: I('StringObjectVariable', D, 'estado', op, f'"{s}"')
    golpe = lambda s: I('StringObjectVariable', D, 'golpe', '=', f'"{s}"')
    anim = lambda s: I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', f'"{s}"')

    inicio = acha(evs, lambda e: tem(e, 'SceneJustBegins') and tem(e, 'ResetObjectTimer', D, '"atordoado"'))
    inicio['actions'].append(I('ResetObjectTimer', D, '"explosao"'))

    cutelo = acha(evs, lambda e: tem(e, 'AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"ataque"'))
    cutelo['actions'].append(I('SetStringObjectVariable', D, 'golpe', '=', '"cutelo"'))
    dano = acha(evs, lambda e: tem(e, 'SetNumberObjectVariable', 'pato', 'vida', '-', f'{D}.golpe_dano'))
    dano['conditions'].insert(1, golpe('cutelo'))

    pai = acha(evs, lambda e: cutelo in e.get('events', []))
    explode = [
        # começa: antes do cutelo, para os dois não começarem no mesmo quadro
        E([estado('=', 'perseguir'), I('CompareObjectTimer', D, '"explosao"', '>', f'{D}.explosao_espera / {D}.ritmo')],
          [I('SetStringObjectVariable', D, 'estado', '=', '"atacar"'), I('SetStringObjectVariable', D, 'golpe', '=', '"explosao"'),
           I('ResetObjectTimer', D, '"estado"'), I('ResetObjectTimer', D, '"explosao"'),
           I('SetBooleanObjectVariable', D, 'explosao_feita', 'False', ''), anim('explosao'),
           I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', D, 'PlatformerObject', '=', '0'),
           I('PlaySound', '', 'som_fogo_caveira.wav', '', f'{D}.explosao_som_volume', 'RandomFloatInRange(0.8, 0.9)')]),
        # no auge do fogo: bolas em círculo
        E([estado('=', 'atacar'), golpe('explosao'), I('BooleanObjectVariable', D, 'explosao_feita', 'False', ''),
           I('CompareObjectTimer', D, '"estado"', '>', f'{D}.explosao_disparo / {D}.ritmo')],
          [I('SetBooleanObjectVariable', D, 'explosao_feita', 'True', ''),
           num(D, 'explosao_angulo', '=', 'RandomFloatInRange(0, 360)'), num(D, 'bola_i', '=', '0')], [
            {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': f'{D}.explosao_bolas', 'conditions': [],
             'actions': [
                 I('Create', '', B, f'{D}.CenterX()', f'{D}.CenterY()', ''),
                 I('SetXY', B, '=', f'{D}.CenterX() + {D}.explosao_raio * cos(ToRad({D}.explosao_angulo + {D}.bola_i * 360 / {D}.explosao_bolas)) - {B}.Width() / 2',
                   '=', f'{D}.CenterY() + {D}.explosao_raio * sin(ToRad({D}.explosao_angulo + {D}.bola_i * 360 / {D}.explosao_bolas)) - {B}.Height() / 2'),
                 I('AddForceAL', B, f'{D}.explosao_angulo + {D}.bola_i * 360 / {D}.explosao_bolas', f'{D}.explosao_vel', '1'),
                 I('SetAngle', B, '=', f'{D}.explosao_angulo + {D}.bola_i * 360 / {D}.explosao_bolas'),
                 num(B, 'dano', '=', f'{D}.explosao_dano'),
                 num(B, 'vida', '=', f'{D}.explosao_vida'),
                 I('ResetObjectTimer', B, '"vida"'),
                 num(D, 'bola_i', '+', '1'),
             ]},
        ]),
    ]
    k = pai['events'].index(cutelo)
    pai['events'][k:k] = explode

    evs.append(grupo('Bolas de fogo', [
        E([I('CollisionNP', B, 'pato', '', '', ''), I('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
           I('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
          [I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'"{D}"'),
           num('pato', 'vida', '-', f'{B}.dano'),
           I('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
           I('ResetObjectTimer', 'pato', '"iframes"'),
           I('PlatformBehavior::SimulateJumpKey', 'pato', 'PlatformerObject'),
           I('Delete', B, '')]),
        E([I('CollisionNP', B, 'Terreno', '', '', '')], [I('Delete', B, '')]),
        E([I('CompareObjectTimer', B, '"vida"', '>', f'{B}.vida')], [I('Delete', B, '')]),
    ]))
    return evs


# ------------------------------------------------------------------ jogo.json
def variaveis(lista, dono, existentes):
    tem_ = {v['name'] for v in existentes}
    for n, t, v in lista:
        if n not in tem_:
            existentes.append({'name': n, 'persistentUuid': uid(dono, n), 'type': t, 'value': v})


def pasta(d, *caminho):
    no = d['objectsFolderStructure']
    for nome in caminho:
        prox = next((c for c in no.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            no['children'].append(prox)
        no = prox
    return no


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    tem_r = {r['name'] for r in recursos}
    for rel in BOLA_IMGS:
        if rel not in tem_r:
            recursos.append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel, 'smoothed': False, 'userAdded': True})

    variaveis(VARS_POCA, P, objs[P]['variables'])
    if B not in objs:
        s0 = {'hasCustomCollisionMask': True, 'points': [], 'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
              'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0},
              'customCollisionMask': [[{'x': 27, 'y': 6}, {'x': 57, 'y': 6}, {'x': 57, 'y': 30}, {'x': 27, 'y': 30}]]}
        o = {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': B, 'persistentUuid': uid(B),
             'type': 'Sprite', 'updateIfNotVisible': False, 'variables': [], 'effects': [], 'behaviors': [],
             'animations': [{'name': 'idle', 'useMultipleDirections': False,
                             'directions': [{'looping': True, 'timeBetweenFrames': 0.06,
                                             'sprites': [dict(copy.deepcopy(s0), image=f) for f in BOLA_IMGS]}]}]}
        variaveis(VARS_BOLA, B, o['variables'])
        d['objects'].append(o)
        pasta(d, 'inimigos', 'chefe')['children'].append({'objectName': B})

    variaveis(VARS_PATO, 'pato', objs['pato']['variables'])
    chefe = objs[D]
    variaveis(VARS_CHEFE, D, chefe['variables'])
    if not any(a['name'] == 'explosao' for a in chefe['animations']):
        morte = next(a for a in chefe['animations'] if a['name'] == 'morte')['directions'][0]
        ida = morte['sprites'][:10]
        chefe['animations'].append({'name': 'explosao', 'useMultipleDirections': False, 'directions': [
            {'looping': False, 'timeBetweenFrames': morte['timeBetweenFrames'],
             'sprites': copy.deepcopy(ida + ida[-2::-1])}]})

    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not acha(ext['events'], lambda e: tem(e, 'Create', '', B)):
        assert ext['events'] == t59.eventos(), ('os eventos "Chefe" foram editados depois de t59; '
                                                'este script não os sobrescreve')
        ext['events'] = eventos_chefe(ext['events'])

    if not any(x['name'] == 'Sangue' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': 'Inferno', 'name': 'Sangue', 'events': eventos_sangue()})
    cena = next((l for l in d['layouts'] if l['name'] == 'Inferno'), None)
    if cena is not None and not any(e['type'].endswith('::Link') and e.get('target') == 'Sangue' for e in cena['events']):
        cena['events'].append({'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'Sangue'})


def main(caminho):
    desenha()
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
