"""Tarefa 61: portão de masmorra que tranca o pato na sala do demônio chefe e abre quando ele morre.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - imagem assets/parede_chefe/portao.png (gerada aqui se não existe): grade de ferro com travessas rebitadas,
    ferrugem e pontas afiadas sujas de sangue embaixo, 2x;
  - parede_chefe (pasta inimigos/chefe): o portão, plataforma sólida. Ponha a instância onde ele fica FECHADO
    (do teto ao chão); no começo da cena ele sobe a própria altura e fica escondido dentro do teto (a instância
    fica atrás dos tiles). Pode haver vários;
  - um portão na entrada da sala do chefe no Inferno (o vão entre o teto e o chão em x 11704..11800);
  - variáveis de cena chefe_trancado, chefe_aberto e chefe_fora (de trabalho) e, em parede_chefe, descida_vel
    (px/s, desce rápido para o pato não conseguir voltar), subida_vel, som_volume, som_tom e fechado_y/fechado (de
    trabalho);
  - grupo "Arena" no fim dos eventos externos "Chefe":
      * fecha quando o pato entra no sangue (objeto sangue) estando do lado de dentro de todos os portões (do mesmo
        lado que o demônio e sem estar embaixo de nenhum) e o demônio está vivo;
      * o portão desce a descida_vel e bate no chão com som; se encostar no pato enquanto desce, empurra o pato
        para dentro da sala;
      * abre quando o demônio morre (ou some da cena): sobe a subida_vel.
"""
import json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, W, S = 'demonio_chefe', 'parede_chefe', 'sangue'
IMG = 'assets/parede_chefe/portao.png'
NW, NH = 48, 392                                         # tamanho nativo (sai em 2x: 96 x 784)
VARS_PAREDE = [('descida_vel', 'number', 3200), ('subida_vel', 'number', 600), ('som_volume', 'number', 70),
               ('som_tom', 'number', 0.55), ('fechado_y', 'number', 0), ('fechado', 'boolean', False)]
VARS_CENA = [('chefe_trancado', 'boolean', False), ('chefe_aberto', 'boolean', False), ('chefe_fora', 'number', 0)]
# portão fechado na entrada da sala: do teto (y -8681) ao chão (y -7913), entrando 8 px em cada um
ENTRADA = (11704, -8689, NW * 2, NH * 2)
Z_ATRAS_DO_TETO = 3                                      # tiles_inferno (o teto ali) tem z 4
I, E, grupo = t59.I, t59.E, t59.grupo


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t61/' + '/'.join(p)))


# ------------------------------------------------------------------ imagem
CONTORNO = (18, 14, 18, 255)
FERRO_D, FERRO, FERRO_L, FERRO_B = (33, 30, 35, 255), (62, 54, 59, 255), (98, 88, 92, 255), (132, 120, 122, 255)
FERRUGEM = [(92, 44, 32, 255), (120, 58, 38, 255)]
SANGUE = [(70, 6, 12, 255), (110, 12, 22, 255), (150, 24, 32, 255)]
BARRAS = [1, 14, 27, 40]                                 # x da esquerda de cada barra (6 px com o contorno)
TRAVESSAS = [8, 64, 120, 176, 232, 288, 344]             # y de cima de cada travessa (6 px de altura)
PONTA = 14                                               # altura das pontas embaixo


def ruido(x, y, k):
    return (x * 73856093 ^ y * 19349663 ^ k * 83492791) % 1000 / 1000


def portao():
    im = Image.new('RGBA', (NW, NH), (0, 0, 0, 0))
    px = im.load()
    pe = NH - PONTA
    # barras verticais (sombra à esquerda, brilho à direita), afinando em ponta no pé
    for bx in BARRAS:
        for y in range(NH):
            cheia = [(bx, CONTORNO), (bx + 1, FERRO_D), (bx + 2, FERRO_L), (bx + 3, FERRO_B), (bx + 4, FERRO),
                     (bx + 5, CONTORNO)]
            if y < pe:
                cols = cheia
            else:
                t = (y - pe) / PONTA                                         # ponta: afina até 1 px
                if t < 0.35:
                    cols = cheia
                elif t < 0.6:
                    cols = [(bx + 1, CONTORNO), (bx + 2, FERRO_L), (bx + 3, FERRO), (bx + 4, CONTORNO)]
                elif t < 0.85:
                    cols = [(bx + 2, CONTORNO), (bx + 3, FERRO_L), (bx + 4, CONTORNO)]
                else:
                    cols = [(bx + 3, CONTORNO)]
            for x, c in cols:
                if 0 <= x < NW:
                    if c in (FERRO, FERRO_D) and ruido(x, y // 2, 1) < 0.025:
                        c = FERRUGEM[int(ruido(x, y, 2) * 2)]
                    if y > pe - 14 and c not in (CONTORNO,) and ruido(x, y, 3) < (y - (pe - 14)) / 24:
                        c = SANGUE[min(2, int(ruido(x, y, 4) * 3))]          # pontas sujas de sangue
                    px[x, y] = c
    # travessas rebitadas
    for ty in TRAVESSAS:
        for x in range(NW):
            for dy, c in ((0, CONTORNO), (1, FERRO_B), (2, FERRO_L), (3, FERRO), (4, FERRO_D), (5, CONTORNO)):
                cc = c
                if c in (FERRO, FERRO_D) and ruido(x // 2, ty + dy, 5) < 0.04:
                    cc = FERRUGEM[int(ruido(x, ty, 6) * 2)]
                px[x, ty + dy] = cc
        for bx in BARRAS:                                                    # rebite em cada cruzamento
            px[bx + 2, ty + 2], px[bx + 3, ty + 2] = FERRO_B, FERRO_L
            px[bx + 2, ty + 3], px[bx + 3, ty + 3] = FERRO_L, FERRO_D
            px[bx + 1, ty + 4], px[bx + 4, ty + 4] = CONTORNO, CONTORNO
    # escorrido de sangue descendo de algumas travessas
    for k, bx in enumerate(BARRAS):
        ty = TRAVESSAS[(k * 2 + 1) % len(TRAVESSAS)] + 6
        for y in range(ty, ty + 8 + k * 4):
            if y < pe:
                px[bx + 2, y] = SANGUE[1 if y < ty + 4 else 0]
    return im.resize((NW * 2, NH * 2), Image.NEAREST)


def desenha():
    caminho = os.path.join(RAIZ, IMG)
    if not os.path.exists(caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        portao().save(caminho)


# ------------------------------------------------------------------ eventos
def eventos():
    cena = lambda v, val: I('SetBooleanVariable', v, val, '')
    vivo = [I('SceneInstancesCount', '', D, '>', '0'), I('BooleanObjectVariable', D, 'morto', 'False', '')]
    cmp = lambda a, op, b: I('BuiltinCommonInstructions::CompareNumbers', a, op, b)
    lado = f'({W}.CenterX() - pato.CenterX()) * ({W}.CenterX() - {D}.CenterX())'
    fora = {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
        cmp(lado, '<=', '0'), cmp(f'abs(pato.CenterX() - {W}.CenterX())', '<', f'({W}.Width() + pato.Width()) / 2')]}
    abre = [cena('chefe_trancado', 'False'), cena('chefe_aberto', 'True')]
    cada = lambda evs: {'type': 'BuiltinCommonInstructions::ForEach', 'object': W, 'conditions': [], 'actions': [],
                        'events': evs}
    return grupo('Arena', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Arena: cada parede_chefe (portão) foi posta onde fica FECHADA; no começo da cena sobe a própria altura '
                    'para dentro do teto. Quando o pato entra no sangue do lado de dentro de todos os portões (lado do '
                    'demônio, sem estar embaixo de nenhum) e o demônio está vivo, os portões descem a descida_vel e '
                    'empurram o pato para dentro se encostarem nele. Quando o demônio morre, sobem a subida_vel.'},
        E([I('SceneJustBegins', '')], [cena('chefe_trancado', 'False'), cena('chefe_aberto', 'False')], [
            cada([E([], [I('SetNumberObjectVariable', W, 'fechado_y', '=', f'{W}.Y()'),
                         I('SetBooleanObjectVariable', W, 'fechado', 'False', ''),
                         I('SetY', W, '=', f'{W}.fechado_y - {W}.Height()')])]),
        ]),
        # fecha
        E([I('BooleanVariable', 'chefe_trancado', 'False', ''), I('BooleanVariable', 'chefe_aberto', 'False', ''),
           I('CollisionNP', 'pato', S, '', '', '')] + vivo,
          [I('SetNumberVariable', 'chefe_fora', '=', '0')], [
            cada([E([fora], [I('SetNumberVariable', 'chefe_fora', '+', '1')])]),
            E([I('NumberVariable', 'chefe_fora', '=', '0')], [cena('chefe_trancado', 'True')]),
        ]),
        E([I('BooleanVariable', 'chefe_trancado', 'True', '')], [], [
            cada([
                E([cmp(f'{W}.Y()', '<', f'{W}.fechado_y')],
                  [I('SetY', W, '=', f'min({W}.fechado_y, {W}.Y() + {W}.descida_vel * TimeDelta())')]),
                E([cmp(f'{W}.Y()', '>=', f'{W}.fechado_y'), I('BooleanObjectVariable', W, 'fechado', 'False', '')],
                  [I('SetBooleanObjectVariable', W, 'fechado', 'True', ''),
                   I('PlaySound', '', 'som_explosao.wav', '', f'{W}.som_volume', f'{W}.som_tom')]),
                # empurra o pato para dentro da sala (o lado do demônio) se o portão encostar nele
                E([I('CollisionNP', W, 'pato', '', '', ''), cmp(f'{D}.CenterX()', '>', f'{W}.CenterX()')],
                  [I('SetX', 'pato', '=', f'{W}.X() + {W}.Width()')]),
                E([I('CollisionNP', W, 'pato', '', '', ''), cmp(f'{D}.CenterX()', '<=', f'{W}.CenterX()')],
                  [I('SetX', 'pato', '=', f'{W}.X() - pato.Width()')]),
            ]),
        ]),
        # abre
        E([I('BooleanVariable', 'chefe_trancado', 'True', ''), I('SceneInstancesCount', '', D, '=', '0')], abre),
        E([I('BooleanVariable', 'chefe_trancado', 'True', ''), I('BooleanObjectVariable', D, 'morto', 'True', '')], abre),
        E([I('BooleanVariable', 'chefe_aberto', 'True', '')], [], [
            cada([E([cmp(f'{W}.Y()', '>', f'{W}.fechado_y - {W}.Height()')],
                    [I('SetY', W, '=', f'max({W}.fechado_y - {W}.Height(), {W}.Y() - {W}.subida_vel * TimeDelta())')])]),
        ]),
    ])


# ------------------------------------------------------------------ jogo.json
def migra(d):
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    if not any(r['name'] == IMG for r in recursos):
        recursos.append({'file': IMG, 'kind': 'image', 'metadata': '', 'name': IMG, 'smoothed': False, 'userAdded': True})
    if W not in objs:
        quadro = {'hasCustomCollisionMask': False, 'image': IMG, 'points': [],
                  'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                  'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': []}
        d['objects'].append({
            'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': W, 'persistentUuid': uid(W),
            'type': 'Sprite', 'updateIfNotVisible': False,
            'variables': [{'name': n, 'persistentUuid': uid(W, n), 'type': t, 'value': v} for n, t, v in VARS_PAREDE],
            'effects': [], 'behaviors': [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior',
                                          'canBeGrabbed': False, 'platformType': 'NormalPlatform', 'yGrabOffset': 0}],
            'animations': [{'name': 'idle', 'useMultipleDirections': False,
                            'directions': [{'looping': False, 'timeBetweenFrames': 0.08, 'sprites': [quadro]}]}]})
        no = d['objectsFolderStructure']
        for nome in ('inimigos', 'chefe'):
            no = next(c for c in no['children'] if c.get('folderName') == nome)
        no['children'].append({'objectName': W})

    cena = next(l for l in d['layouts'] if l['name'] == 'Inferno')
    tem = {v['name'] for v in cena['variables']}
    for n, t, v in VARS_CENA:
        if n not in tem:
            cena['variables'].append({'name': n, 'persistentUuid': uid('Inferno', n), 'type': t, 'value': v})
    if not any(i.get('persistentUuid') == uid('entrada') for i in cena['instances']):
        x, y, w, h = ENTRADA
        cena['instances'].append({'angle': 0, 'customSize': True, 'depth': 1, 'height': h, 'keepRatio': False, 'layer': '',
                                  'name': W, 'persistentUuid': uid('entrada'), 'width': w, 'x': x, 'y': y,
                                  'zOrder': Z_ATRAS_DO_TETO, 'numberProperties': [], 'stringProperties': [],
                                  'initialVariables': []})

    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not any(e.get('name') == 'Arena' for e in ext['events']):
        ext['events'].append(eventos())


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
