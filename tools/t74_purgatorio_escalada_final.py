"""Tarefa 74: escalada final do Purgatório, mais difícil, depois do cume.

O cume deixa de ser o fim: à esquerda dele abre um poço com ácido no fundo, e a subida continua até um platô bem
mais alto, onde fica a saída agora. Entra o que a primeira parte não tem:

  - plataforma_some: laje de pedra rachada; quando o pato pisa nela, treme por `aviso` s, some (sem colisão) por
    `sumida` s e volta aparecendo aos poucos (`volta_vel` de opacidade por segundo);
  - jato_fogo: fenda na rocha de onde sai o fogo que purifica (o muro de fogo do último terraço de Dante). Em ciclo,
    fica em brasa por `espera` s, avisa por `aviso` s (a fenda acende e uma língua de fogo curta, de `alcance_aviso`
    px, lambe para fora, sem machucar) e solta por `disparo` s um jato de fogo dourado (jato_fogo_chama) de `alcance`
    px para o lado `lado` (1 direita, -1 esquerda), que tira `dano` do pato; o fogo corre para fora da fenda a
    `vel_chama` px/s e `defasagem` desencontra as fendas;
  - acido: poça no fundo do poço; quem afunda mais de `margem` px perde `dano` de vida e volta para (retorno_x,
    retorno_y), a beira do poço;
  - rodas pequenas e rápidas: plataforma_radial em tamanho reduzido (instâncias com tamanho próprio e ancora_y
    proporcional), raios curtos e vel_ang alta.

O caminho: da beira do poço (à esquerda do cume), lajes que somem sobre o ácido até um ressalto no paredão da
esquerda; uma roda pequena, uma laje, outra roda pequena e um ressalto no paredão da direita, com três jatos de
fogo cruzando; duas lajes, uma roda pequena de três troncos e outro ressalto à esquerda, com mais dois jatos; e
quatro lajes até o platô do topo, debaixo de mais dois jatos.

Migração de uso único que só ADICIONA: imagens em assets/purgatorio_armadilhas/, os objetos acima, os eventos
externos "Armadilhas" ligados no Purgatorio, as variáveis de cena retorno_x, retorno_y e jato_n, e o terreno, os
troncos, os enfeites e as instâncias novas (persistentUuid fixos; o que já está lá não é tocado). A saída
(saida_x_min, saida_x_max, saida_y) só muda para o platô se ainda estiver nos valores da tarefa 72; se você já mexeu
nela, fica como está.
"""
import json, math, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENA = 'Purgatorio'
ATLAS = 'assets/purgatorio/tiles/tiles_purgatorio.png'
PASTA = 'assets/purgatorio_armadilhas'
T = 64
Y0, HMAX = -9600, 165                        # mesma grade da tarefa 72 (h conta de baixo; h 165 é a linha do topo dela)

ESCURO, PEDRA_E, PEDRA, PEDRA_C = (27, 28, 24, 255), (59, 56, 51, 255), (80, 76, 69, 255), (105, 100, 90, 255)
MUSGO_E, MUSGO, MUSGO_C = (54, 64, 47, 255), (72, 85, 59, 255), (96, 110, 74, 255)

SOME, JATO, CHAMA, ACIDO = 'plataforma_some', 'jato_fogo', 'jato_fogo_chama', 'acido'
VARS_SOME = {'aviso': 0.55, 'sumida': 2.5, 'volta_vel': 900, 'tremor': 3, 'topo': 2, 'tolerancia': 14,
             'som_volume': 45, 'estado': 0, 't': 0, 'base_x': 0}
VARS_JATO = {'espera': 1.6, 'aviso': 0.9, 'disparo': 0.7, 'defasagem': 0, 'alcance': 2112, 'alcance_aviso': 110,
             'lado': 1, 'dano': 20, 'vel_chama': 700, 'aviso_opacidade': 150, 'aviso_piscar': 25, 'boca_y': 32,
             'som_volume': 60, 'som_alcance': 1400, 'id': 0, 'estado': 0, 'estado_antes': 0, 't': 0, 'fase': 0}
VARS_CHAMA = {'id': 0, 'ativo': False, 'dano': 0}
CHAMA_ALTURA = 48                            # altura da textura do jato (16 x 24 nativo, em 2x)
VARS_ACIDO = {'dano': 25, 'margem': 30}

# ------------------------------------------------------------------ fase
# terreno novo: (col_ini, col_fim, h_ini, h_fim); colunas negativas ficam à esquerda do mapa da tarefa 72
SOLIDOS = [(-52, -37, 140, 250),            # paredão da esquerda do poço (grosso: a câmera não vê o céu atrás)
           (-36, -7, 140, 149),             # fundo da poça de ácido
           (-6, -1, 140, 162),              # beira do poço, emendada no cume (topo em h 162, como o cume)
           (-2, 8, 170, 244),               # paredão da direita, por cima da entrada
           (-8, -3, 242, 244),              # platô do topo (com o alto do paredão da direita)
           (-36, -34, 178, 178), (-36, -34, 221, 221),   # ressaltos do paredão da esquerda
           (-5, -3, 199, 199)]              # ressalto do paredão da direita
ACIDO_TOPO_H, ACIDO_COLS = 158, (-36, -7)   # superfície no topo da linha 158
SOMEM = [(-12, 166), (-18, 169), (-24, 172), (-30, 175),          # (coluna da esquerda, linha de pé)
         (-21, 188), (-12, 204), (-18, 208),
         (-30, 226), (-24, 230), (-18, 234), (-12, 238)]
# rodas pequenas: (nome, centro x, linha de pé no centro, raio, vel_ang, ângulos)
RODAS = [('roda_poco_1', -27 * T, 183, 192, 100, (0, 180)),
         ('roda_poco_2', -12 * T, 192, 192, -110, (0, 180)),
         ('roda_poco_3', -27 * T, 214, 224, 130, (0, 120, 240))]
PEQ_W, PEQ_H, PEQ_ANCORA = 116, 34, 8      # tronco da plataforma_radial reduzido a ~60%
# jatos de fogo: (linha h do jato, lado, defasagem)
JATOS = [(184, 1, 0), (190, 1, 1.6), (196, -1, 0.8), (211, -1, 0.4), (219, 1, 2.0), (232, 1, 1.2), (240, -1, 0.0)]
PAREDE_ESQ_X, PAREDE_DIR_X = -36 * T, -2 * T            # faces de dentro dos paredões do poço
PLATO_S = 245
MOEDAS = [(-11, 168), (-23, 174), (-29, 182), (-20, 191), (-12, 197), (-4, 202), (-17, 211), (-27, 220),
          (-35, 224), (-23, 233), (-11, 241), (0, 248)]
# enfeites: (coluna, linha de pé, desenho de baixo para cima)
ENFEITES = [(-6, 163, [[113]]), (-36, 179, [[111]]), (-36, 222, [[112]]), (-5, 200, [[50]]),
            (-7, 245, [[149, 150], [132, 133], [115, 116]]), (-4, 245, [[14]]), (-2, 245, [[66, 67]]),
            (1, 245, [[99], [82], [65]]), (3, 245, [[146, 147]]), (6, 245, [[98], [81]])]

SAIDA_ANTIGA = {'saida_x_min': 128, 'saida_x_max': 896, 'saida_y': -9400}


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t74/' + '/'.join(p)))


def topo_y(h):
    return Y0 + (HMAX - h) * T


def pe_y(s):
    """y da superfície em que o pato fica de pé na linha s."""
    return Y0 + (HMAX + 1 - s) * T


# ------------------------------------------------------------------ imagens
def laje(rachas):
    """Laje de pedra clara rachada, feita do topo do terreno do purgatório (tiles 0, 1, 2)."""
    atlas = Image.open(os.path.join(RAIZ, ATLAS)).convert('RGBA')
    im = Image.new('RGBA', (96, 16), (0, 0, 0, 0))
    for k, i in enumerate((0, 1, 2)):
        im.paste(atlas.crop((i % 17 * 32, i // 17 * 32, i % 17 * 32 + 32, i // 17 * 32 + 16)), (k * 32, 0))
    px = im.load()
    for x in range(96):
        for y in range(16):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if y >= 13 and (x * 5 + y * 3) % 7 < 3:
                px[x, y] = (0, 0, 0, 0)                                      # borda de baixo lascada
                continue
            t = .45 if y > 5 else .2
            px[x, y] = (round(r + (150 - r) * t), round(g + (148 - g) * t), round(b + (136 - b) * t), 255)
    for x0, comp in [(22, 6), (51, 8), (74, 5), (36, 7), (63, 6)][:rachas]:  # rachas em zigue-zague
        x = x0
        for y in range(6, 6 + comp):
            if 0 <= x < 96 and y < 16:
                px[x, y] = ESCURO
            x += 1 if (y + x0) % 3 == 0 else -1 if (y + x0) % 3 == 1 else 0
    return im


def fenda(estado, quadro=0):
    """Bloco de pedra com uma fenda funda virada para a direita; o fundo dela vai de brasa a fogo branco."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = im.load()
    for y in range(2, 30):
        for x in range(0, 28):
            borda = x == 27 or y in (2, 29)
            luz = (x + (31 - y)) / 60
            px[x, y] = ESCURO if borda else PEDRA_C if luz > .7 else PEDRA if luz > .35 else PEDRA_E
    for x in range(1, 27, 6):                                               # musgo por cima
        px[x, 3], px[x + 1, 3] = MUSGO, MUSGO_C
    brilho = {'brasa': [(70, 40, 28), (120, 72, 40)],
              'aviso': [(200, 120, 50), (240, 196, 110)] if quadro == 0 else [(160, 90, 40), (214, 150, 70)],
              'fogo': [(248, 220, 150), (255, 250, 230)]}[estado]
    for y in range(8, 24):                                                  # fenda em zigue-zague, aberta para a direita
        meio = 16 + (1 if y % 6 < 3 else -1)
        abre = 6 - abs(y - 16) * .55
        if abre <= 0:
            continue
        for x in range(12, 28):                                             # só dentro da pedra
            if abs(y - meio) <= abre * (x - 10) / 17:
                quente = x > 19 and abs(y - meio) < abre * .5
                px[x, y] = (brilho[1] if quente else brilho[0]) + (255,)
    if estado == 'brasa':
        for x, y in ((24, 15), (27, 17), (21, 16)):
            px[x, y] = (150, 90, 44, 255)
    if estado == 'aviso':                                                   # fagulhas saindo
        for x, y in ((29, 9 + quadro * 2), (31, 21 - quadro * 3), (30, 13 + quadro)):
            px[x, y] = (250, 222, 150, 255)
    return im


def chama():
    """Pedaço do jato de fogo dourado que repete na horizontal: miolo branco, bordas onduladas que se apagam."""
    w, h = 32, 24
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    cores = [(255, 250, 230, 255), (252, 236, 182, 255), (246, 214, 138, 255), (232, 176, 86, 230), (206, 132, 60, 170)]
    for x in range(w):
        borda = 2.5 + 1.6 * math.sin(2 * math.pi * x / 16) + .9 * math.sin(2 * math.pi * x / 8 + 1)
        for y in range(h):
            d = min(y, h - 1 - y)                                           # distância até a borda de cima/baixo
            if d < borda:
                continue
            k = (h / 2 - d) / (h / 2 - borda)                               # 0 no miolo, 1 na borda
            ruido = ((x * 7 + y * 13) % 5) / 10
            px[x, y] = cores[max(0, min(4, int(k * 4.6 + ruido - .2)))]
    return im


def acido(fase):
    """Poça de ácido verde apagado: onda na superfície com espuma e bolhas subindo."""
    w, h = 192, 288
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    claro, espuma = (176, 194, 96), (206, 214, 150)
    cores = [(120, 150, 62), (100, 130, 54), (82, 110, 46), (66, 92, 40), (54, 76, 36)]
    for x in range(w):
        onda = 5 + 2.2 * math.sin(x / w * 4 * math.pi + fase * math.pi / 2) + math.sin(x / w * 10 * math.pi - fase * math.pi)
        topo = round(onda)
        for y in range(topo, h):
            if y < topo + 2:
                c = espuma if (x + fase * 3) % 9 < 3 else claro
            else:
                t = min(1, (y - topo) / (h * .8)) * 4 + bayer[y % 4][x % 4] / 16 - .5
                c = cores[max(0, min(4, round(t)))]
            px[x, y] = c + (255,)
    for k, (bx, vel) in enumerate([(30, 1), (88, 1.4), (140, .8), (60, 1.2), (170, 1.1)]):  # bolhas
        by = (h - 20 - (fase * 40 * vel + k * 53) % (h - 40))
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = math.hypot(dx, dy)
                if 2 <= d < 3.2:
                    x, y = int(bx + dx), int(by + dy)
                    if 0 <= x < w and 0 <= y < h and px[x, y][3]:
                        px[x, y] = claro + (255,)
    return im


QUADROS_SOME = [f'{PASTA}/laje_inteira.png', f'{PASTA}/laje_treme_0.png', f'{PASTA}/laje_treme_1.png']
QUADROS_FENDA = {'brasa': [f'{PASTA}/fenda_brasa.png'], 'aviso': [f'{PASTA}/fenda_aviso_0.png', f'{PASTA}/fenda_aviso_1.png'],
                 'fogo': [f'{PASTA}/fenda_fogo.png']}
CHAMA_IMG = f'{PASTA}/chama.png'
QUADROS_ACIDO = [f'{PASTA}/acido_{i:02d}.png' for i in range(4)]


def desenha():
    os.makedirs(os.path.join(RAIZ, PASTA), exist_ok=True)
    feitos = [(QUADROS_SOME[0], laje(2)), (QUADROS_SOME[1], laje(4)), (QUADROS_SOME[2], laje(5)),
              (QUADROS_FENDA['brasa'][0], fenda('brasa')), (QUADROS_FENDA['aviso'][0], fenda('aviso', 0)),
              (QUADROS_FENDA['aviso'][1], fenda('aviso', 1)), (QUADROS_FENDA['fogo'][0], fenda('fogo')), (CHAMA_IMG, chama())]
    feitos += [(f, acido(i)) for i, f in enumerate(QUADROS_ACIDO)]
    for f, im in feitos:
        if not os.path.exists(os.path.join(RAIZ, f)):
            im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(RAIZ, f))


# ------------------------------------------------------------------ eventos
def I(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def E(conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def para_cada(obj, conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def grupo(nome, eventos):
    return {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': nome, 'source': '',
            'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': eventos}


def comentario(texto):
    return {'type': 'BuiltinCommonInstructions::Comment',
            'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0}, 'comment': texto}


def num(o, v, op, expr):
    return I('SetNumberObjectVariable', o, v, op, expr)


def cmp(a, op, b):
    return I('BuiltinCommonInstructions::CompareNumbers', a, op, b)


def nvar(o, v, op, val):
    return I('NumberObjectVariable', o, v, op, val)


def anim(o, nome):
    return I('AnimatableCapability::AnimatableBehavior::SetName', o, 'Animation', '=', f'"{nome}"')


def opac(o, op, expr):
    return I('OpacityCapability::OpacityBehavior::SetValue', o, 'Opacity', op, expr)


def dano(fonte_dano, agressor):
    return [num('pato', 'vida', '-', fonte_dano), I('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
            I('ResetObjectTimer', 'pato', '"iframes"'), I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'"{agressor}"')]


VIVO = [I('BooleanObjectVariable', 'pato', 'morto', 'False', '')]
PODE_APANHAR = VIVO + [I('BooleanObjectVariable', 'pato', 'invencivel', 'False', '')]


def eventos():
    S, J, F = SOME, JATO, CHAMA
    ciclo = f'{J}.espera + {J}.aviso + {J}.disparo'
    return [
        comentario('Armadilhas da escalada final do Purgatório. plataforma_some: pisou, treme por aviso s, some por '
                   'sumida s e volta aparecendo (volta_vel). jato_fogo: fogo que purifica; em ciclo, em brasa por '
                   'espera s, avisa por aviso s (língua de fogo de alcance_aviso px, sem machucar) e solta por disparo s '
                   'um jato de alcance px para o lado `lado`, que tira dano; defasagem desencontra as fendas. acido: afundou mais de margem px, perde dano e volta '
                   'para (retorno_x, retorno_y).'),
        grupo('Lajes que somem', [
            E([I('SceneJustBegins', '')], [num(S, 'base_x', '=', f'{S}.X()'), num(S, 'estado', '=', '0')]),
            para_cada(S, [nvar(S, 'estado', '=', '0'), I('PlatformBehavior::IsOnFloor', 'pato', 'PlatformerObject')], [], [
                E([cmp(f'abs(pato.CenterX() - {S}.CenterX())', '<', f'({S}.Width() + pato.Width()) / 2'),
                   cmp(f'abs(pato.Y() + pato.Height() - {S}.Y() - {S}.topo)', '<', f'{S}.tolerancia')],
                  [num(S, 'estado', '=', '1'), num(S, 't', '=', '0'), anim(S, 'treme')])]),
            E([nvar(S, 'estado', '>', '0')], [num(S, 't', '+', 'TimeDelta()')]),
            E([nvar(S, 'estado', '=', '1')],
              [I('SetX', S, '=', f'{S}.base_x + RandomFloatInRange(-{S}.tremor, {S}.tremor)')]),
            E([nvar(S, 'estado', '=', '1'), nvar(S, 't', '>=', f'{S}.aviso')],
              [num(S, 'estado', '=', '2'), num(S, 't', '=', '0'), I('SetX', S, '=', f'{S}.base_x'), I('Hide', S),
               I('ActivateBehavior', S, 'Platform', 'no'), anim(S, 'inteira'),
               I('PlaySound', '', 'som_pouso.wav', '', f'{S}.som_volume', 'RandomFloatInRange(0.7, 0.8)')]),
            E([nvar(S, 'estado', '=', '2'), nvar(S, 't', '>=', f'{S}.sumida')],
              [num(S, 'estado', '=', '0'), num(S, 't', '=', '0'), opac(S, '=', '0'), I('Show', S, ''),
               I('ActivateBehavior', S, 'Platform', 'yes')]),
            E([nvar(S, 'estado', '=', '0'), I('OpacityCapability::OpacityBehavior::Value', S, 'Opacity', '<', '255')],
              [opac(S, '=', f'min(255, {S}.Opacity() + {S}.volta_vel * TimeDelta())')]),
        ]),
        grupo('Jatos de fogo purificador', [
            E([I('SceneJustBegins', '')], [], [
                para_cada(J, [], [I('SetNumberVariable', 'jato_n', '+', '1'), num(J, 'id', '=', 'jato_n'),
                                  num(J, 't', '=', f'{J}.defasagem')], [
                    E([nvar(J, 'lado', '<', '0')], [I('FlippableCapability::FlippableBehavior::FlipX', J, 'Flippable', 'yes')]),
                    E([], [I('Create', '', F, f'{J}.X()', f'{J}.Y()', ''), num(F, 'id', '=', f'{J}.id'),
                           I('SetZOrder', F, '=', f'{J}.ZOrder() - 1'), I('Hide', F)]),
                ]),
            ]),
            E([], [num(J, 't', '+', 'TimeDelta()'), num(J, 'estado_antes', '=', f'{J}.estado'),
                   num(J, 'fase', '=', f'mod({J}.t, {ciclo})'), num(J, 'estado', '=', '0')]),
            E([nvar(J, 'fase', '>=', f'{J}.espera')], [num(J, 'estado', '=', '1')]),
            E([nvar(J, 'fase', '>=', f'{J}.espera + {J}.aviso')], [num(J, 'estado', '=', '2')]),
            E([nvar(J, 'estado', '=', '0'), nvar(J, 'estado_antes', '!=', '0')], [anim(J, 'brasa')]),
            E([nvar(J, 'estado', '=', '1'), nvar(J, 'estado_antes', '!=', '1')], [anim(J, 'aviso')]),
            para_cada(J, [nvar(J, 'estado', '=', '2'), nvar(J, 'estado_antes', '!=', '2')], [
                anim(J, 'fogo'),
                I('PlaySound', '', 'som_fogo_caveira.wav', '',
                  f'{J}.som_volume * clamp(1 - {J}.DistanceToPosition(pato.CenterX(), pato.CenterY()) / {J}.som_alcance, 0, 1)',
                  'RandomFloatInRange(0.9, 1.05)')]),
            para_cada(F, [], [], [E([I('NumberObjectVariable', J, 'id', '=', f'{F}.id')], [
                num(F, 'dano', '=', f'{J}.dano'),
                I('TiledSpriteObject::XOffset', F, '=', f'-{J}.lado * mod(TimeFromStart() * {J}.vel_chama, {F}.Width() + 64)'),
            ], [
                E([nvar(J, 'estado', '=', '0')], [I('Hide', F), I('SetBooleanObjectVariable', F, 'ativo', 'False', '')]),
                E([nvar(J, 'estado', '=', '1')],
                  [I('Show', F, ''), I('SetBooleanObjectVariable', F, 'ativo', 'False', ''),
                   I('ResizableCapability::ResizableBehavior::SetWidth', F, 'Resizable', '=', f'{J}.alcance_aviso'),
                   opac(F, '=', f'{J}.aviso_opacidade + 60 * sin(TimeFromStart() * {J}.aviso_piscar)')]),
                E([nvar(J, 'estado', '=', '2')],
                  [I('Show', F, ''), I('SetBooleanObjectVariable', F, 'ativo', 'True', ''),
                   I('ResizableCapability::ResizableBehavior::SetWidth', F, 'Resizable', '=', f'{J}.alcance'),
                   opac(F, '=', '255')]),
                E([], [I('SetX', F, '=', f'{J}.CenterX() + {J}.lado * {J}.Width() / 2 + min(0, {J}.lado * {F}.Width())'),
                       I('SetY', F, '=', f'{J}.Y() + {J}.boca_y - {F}.Height() / 2')]),
            ])]),
            E(PODE_APANHAR + [I('BooleanObjectVariable', F, 'ativo', 'True', ''), I('CollisionNP', 'pato', F, '', '', '')],
              dano(f'{F}.dano', 'fogo')),
        ]),
        grupo('Ácido', [
            E(PODE_APANHAR + [I('CollisionNP', 'pato', ACIDO, '', '', ''),
                              cmp('pato.Y() + pato.Height()', '>', f'{ACIDO}.Y() + {ACIDO}.margem')],
              dano(f'{ACIDO}.dano', 'acido')),
            E(VIVO + [I('CollisionNP', 'pato', ACIDO, '', '', ''),
                      cmp('pato.Y() + pato.Height()', '>', f'{ACIDO}.Y() + {ACIDO}.margem')],
              [I('SetXY', 'pato', '=', 'retorno_x', '=', 'retorno_y'),
               I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed', 'pato', 'PlatformerObject', '=', '0'),
               I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', 'pato', 'PlatformerObject', '=', '0')]),
        ]),
    ]


# ------------------------------------------------------------------ objetos
def variaveis(nome, vs):
    return [{'name': k, 'persistentUuid': uid(nome, k), 'type': 'boolean' if isinstance(v, bool) else 'number', 'value': v}
            for k, v in vs.items()]


def sprite(nome, anims, vs, comportamentos=(), mascara=None):
    def q(f):
        return {'hasCustomCollisionMask': mascara is not None, 'image': f, 'points': [],
                'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': mascara or []}
    return {'adaptCollisionMaskAutomatically': mascara is None, 'assetStoreId': '', 'name': nome, 'persistentUuid': uid(nome),
            'type': 'Sprite', 'updateIfNotVisible': False, 'variables': variaveis(nome, vs), 'effects': [],
            'behaviors': list(comportamentos),
            'animations': [{'name': n, 'useMultipleDirections': False,
                            'directions': [{'looping': True, 'timeBetweenFrames': tempo, 'sprites': [q(f) for f in arqs]}]}
                           for n, arqs, tempo in anims]}


def objetos():
    plataforma = [{'name': 'Platform', 'type': 'PlatformBehavior::PlatformBehavior', 'canBeGrabbed': False,
                   'platformType': 'Jumpthru', 'yGrabOffset': 0}]
    return [
        sprite(SOME, [('inteira', [QUADROS_SOME[0]], 0.1), ('treme', QUADROS_SOME[1:], 0.06)], VARS_SOME, plataforma,
               [[{'x': 4, 'y': 2}, {'x': 188, 'y': 2}, {'x': 188, 'y': 24}, {'x': 4, 'y': 24}]]),
        sprite(JATO, [(n, fs, 0.08) for n, fs in QUADROS_FENDA.items()], VARS_JATO),
        {'assetStoreId': '', 'height': CHAMA_ALTURA, 'name': CHAMA, 'persistentUuid': uid(CHAMA), 'texture': CHAMA_IMG,
         'type': 'TiledSpriteObject::TiledSprite', 'width': 64, 'variables': variaveis(CHAMA, VARS_CHAMA), 'effects': [],
         'behaviors': []},
        sprite(ACIDO, [('borbulha', QUADROS_ACIDO, 0.16)], VARS_ACIDO),
    ]


# ------------------------------------------------------------------ mapa
def celulas(blocos):
    return {(c, h) for c0, c1, h0, h1 in blocos for c in range(c0, c1 + 1) for h in range(h0, h1 + 1)}


def tiles_da_cena(cena, nome):
    out = set()
    for i in cena['instances']:
        if i['name'] == nome and i.get('layer', '') == '':
            g = json.loads(next(p['value'] for p in i['stringProperties'] if p['name'] == 'tilemap'))['layers'][0]['tiles']
            c0, r0 = round(i['x'] / T), round((i['y'] - Y0) / T)
            for r, linha in enumerate(g):
                for c, t in enumerate(linha):
                    if t >= 0:
                        out.add((c0 + c, HMAX - (r0 + r)))
    return out


def autotile(novos, todos, cmin, cmax, hmin, hmax):
    """Mesmas regras da tarefa 72; vizinhos contam o terreno que já existe, para emendar sem costura."""
    cheio = lambda c, h: (c, h) in todos or c < cmin or h < hmin
    grade = [[-1] * (cmax - cmin + 1) for _ in range(hmax - hmin + 1)]
    for (c, h) in novos:
        cima, baixo, esq, dir_ = (not cheio(c, h + 1)), (not cheio(c, h - 1)), (not cheio(c - 1, h)), (not cheio(c + 1, h))
        var2 = (c * 7 + h * 3) % 5 == 0
        if cima and baixo:
            t = 26 if esq else 28 if dir_ else 4
        elif cima:
            t = 0 if esq else 2 if dir_ else (52 if var2 else 1)
        elif baixo:
            t = 34 if esq else 36 if dir_ else (86 if var2 else 35)
        elif esq:
            t = 68 if var2 else 17
        elif dir_:
            t = 70 if var2 else 19
        elif not cheio(c + 1, h + 1):
            t = 40
        elif not cheio(c - 1, h + 1):
            t = 42
        elif not cheio(c + 1, h - 1):
            t = 6
        elif not cheio(c - 1, h - 1):
            t = 8
        else:
            t = 144
        grade[hmax - h][c - cmin] = t
    return grade


def inst_tilemap(nome, chave, cmin, hmax, z, grade):
    return {'angle': 0, 'customSize': False, 'height': 0, 'keepRatio': True, 'layer': '', 'name': nome,
            'persistentUuid': uid(CENA, chave), 'width': 0, 'x': cmin * T, 'y': topo_y(hmax), 'zOrder': z,
            'numberProperties': [], 'stringProperties': [{'name': 'tilemap', 'value': json.dumps(
                {'tileWidth': T, 'tileHeight': T, 'dimX': len(grade[0]), 'dimY': len(grade),
                 'layers': [{'id': 0, 'alpha': 1, 'tiles': grade}]}, separators=(',', ':'))}], 'initialVariables': []}


def inst(nome, chave, x, y, z, vs=None, w=None, h=None):
    i = {'angle': 0, 'customSize': w is not None, 'depth': 1, 'height': h or 0, 'keepRatio': True, 'layer': '',
         'name': nome, 'persistentUuid': uid(CENA, chave), 'width': w or 0, 'x': round(x), 'y': round(y), 'zOrder': z,
         'numberProperties': [], 'stringProperties': [], 'initialVariables': []}
    for k, v in (vs or {}).items():
        i['initialVariables'].append({'name': k, 'persistentUuid': uid(CENA, chave, k),
                                      'type': 'boolean' if isinstance(v, bool) else 'number', 'value': v})
    return i


def instancias(cena):
    novas = []
    existentes = tiles_da_cena(cena, 'tiles_purgatorio')
    meus = celulas(SOLIDOS)
    assert not meus & existentes, 'terreno novo em cima do que já existe'
    cmin, cmax = min(c for c, _ in meus), max(c for c, _ in meus)
    hmin, hmax = min(h for _, h in meus), max(h for _, h in meus) + 6
    novas.append(inst_tilemap('tiles_purgatorio', 'terreno', cmin, hmax, 4,
                              autotile(meus, meus | existentes, cmin, cmax, hmin, hmax)))
    deco = [[-1] * (cmax - cmin + 1) for _ in range(hmax - hmin + 1)]
    for col, s, desenho in ENFEITES:
        for dh, linha in enumerate(desenho):
            for dc, t in enumerate(linha):
                assert (col + dc, s + dh) not in meus | existentes, ('enfeite dentro do terreno', col, s)
                deco[hmax - (s + dh)][col + dc - cmin] = t
    novas.append(inst_tilemap('tiles_purgatorio_decor', 'enfeites', cmin, hmax, 5, deco))

    for k, (c, s) in enumerate(SOMEM):
        novas.append(inst(SOME, f'laje/{k}', c * T, pe_y(s) - VARS_SOME['topo'], 20))
    for nome, cx, s, r, vel, angs in RODAS:
        cy = pe_y(s) + PEQ_ANCORA - 3
        for k, a in enumerate(angs):
            ar = math.radians(a)
            novas.append(inst('plataforma_radial', f'{nome}/{k}', cx + r * math.cos(ar) - PEQ_W / 2,
                              cy + r * math.sin(ar) - PEQ_ANCORA, 22,
                              {'centro_x': cx, 'centro_y': cy, 'raio': r, 'vel_ang': vel, 'angulo': a,
                               'ancora_y': PEQ_ANCORA, 'com_eixo': k == 0}, PEQ_W, PEQ_H))
    for k, (h, lado, defas) in enumerate(JATOS):
        x = PAREDE_ESQ_X if lado > 0 else PAREDE_DIR_X - 64
        alcance = (PAREDE_DIR_X - PAREDE_ESQ_X) - 64
        novas.append(inst(JATO, f'jato/{k}', x, topo_y(h) + 32 - VARS_JATO['boca_y'], 2950,
                          {'lado': lado, 'defasagem': defas, 'alcance': alcance}))
    a0, a1 = ACIDO_COLS
    for k, x in enumerate(range(a0 * T, (a1 + 1) * T, 384)):
        novas.append(inst(ACIDO, f'acido/{k}', x, topo_y(ACIDO_TOPO_H), 3000))
    mw, mh = 103, 60
    for k, (c, h) in enumerate(MOEDAS):
        novas.append(inst('moeda', f'moeda/{k}', c * T + 32 - mw / 2, topo_y(h) + 32 - mh / 2, 1004,
                          {'tem_gravidade': False}, mw, mh))
    ja = {i['persistentUuid'] for i in cena['instances']}
    cena['instances'] += [i for i in novas if i['persistentUuid'] not in ja]


def migra(d):
    cena = next(l for l in d['layouts'] if l['name'] == CENA)
    tem = {r['name'] for r in d['resources']['resources']}
    for rel in QUADROS_SOME + sum(QUADROS_FENDA.values(), []) + [CHAMA_IMG] + QUADROS_ACIDO:
        if rel not in tem:
            d['resources']['resources'].append({'file': rel, 'kind': 'image', 'metadata': '', 'name': rel,
                                                'smoothed': False, 'userAdded': True})
    pasta = d['objectsFolderStructure']
    for nome in ('cenario', 'armadilhas'):
        prox = next((c for c in pasta.setdefault('children', []) if c.get('folderName') == nome), None)
        if prox is None:
            prox = {'folderName': nome, 'children': []}
            pasta['children'].append(prox)
        pasta = prox
    objs = {o['name'] for o in d['objects']}
    for o in objetos():
        if o['name'] not in objs:
            d['objects'].append(o)
            pasta['children'].append({'objectName': o['name']})
    if not any(x['name'] == 'Armadilhas' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': CENA, 'name': 'Armadilhas', 'events': eventos()})
    if not any(e['type'].endswith('::Link') and e.get('target') == 'Armadilhas' for e in cena['events']):
        k = max(n for n, e in enumerate(cena['events']) if e['type'].endswith('::Link')) + 1
        cena['events'].insert(k, {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0},
                                  'target': 'Armadilhas'})
    pato = next(i for i in cena['instances'] if i['name'] == 'pato')
    vs = {v['name']: v for v in cena['variables']}
    for nome, valor in (('retorno_x', -5 * T), ('retorno_y', pe_y(163) - pato['height'] - 2), ('jato_n', 0)):
        if nome not in vs:
            cena['variables'].append({'name': nome, 'persistentUuid': uid(CENA, nome), 'type': 'number', 'value': valor})
    nova_saida = {'saida_x_min': -8 * T, 'saida_x_max': 8 * T, 'saida_y': pe_y(PLATO_S) + 8}
    if all(n in vs and vs[n]['value'] == v for n, v in SAIDA_ANTIGA.items()):
        for n, v in nova_saida.items():
            vs[n]['value'] = v
    else:
        print('saída já mexida: fica como está')
    instancias(cena)


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
