"""Tarefa 124: o cutulu vira chefe de verdade, com três fases e ataques novos.

A lógica antiga (Inimigos > Purgatório > Cutulu (elite): andar, salto com anel de bile e fúria) fica como está. A folha
de eventos nova "Cutulu" é ligada no Purgatorio e no Teste logo depois do HUD (roda depois de Inimigos, e a barra de
chefe precisa vir depois do HUD, que a esconde). Ela sorteia o ataque quando o cutulu entra em "preparar" e cuida dos
estados novos:

Fase 1 (vida acima de fase2_abaixo): o salto agora também solta ondas no chão para os dois lados (ondas_*), e
  MERGULHO (mergulho_*): sobe até sair da tela, uma sombra (cutulu_sombra) segue o pato no chão, trava piscando e ele
  despenca nela: dano em área (mergulho_raio, mergulho_dano, só pega quem está no chão) e ondas. Invulnerável no alto.
Fase 2 (abaixo de fase2_abaixo): + ESPIRAL (espiral_*): sobe e paira girando braços de olhos; + CHUVA de bile
  (chuva_*): cospe bile em arco que cai em volta do pato.
Fase 3 (abaixo de fase3_abaixo): espera e aviso mais curtos (fase3_espera_fator, fase3_aviso_fator), ataques em
  combo (combo_chance, combo_max) e INVOCAÇÃO de moscas (invocar_*, no máximo invocar_max moscas na cena; as
  invocadas não soltam moedas e morrem com ele).
Ao trocar de fase ele ruge (rugido_tempo, invulnerável) e solta o anel de bile. Nunca repete o mesmo ataque seguido.
Vida: max_vida * vida_chefe_mult (3) no começo da cena, sem mexer no max_vida do editor. Barra de chefe com nome.
Só adiciona o que não existe: variáveis que já existem ficam com o valor atual.
Rodar uma vez:  python3 tools/t124_cutulu_chefe.py
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_IMG = 'assets/inimigos/purgatorio/cutulu/'
FOLHA = 'Cutulu'
CENAS = ('Purgatorio', 'Teste')

VARS = [  # (nome, tipo, valor)
    ('vida_chefe_mult', 'number', 3), ('chefe_preparado', 'boolean', False),
    ('nome', 'string', 'CUTULU, O QUE SONHA'), ('barra_dist', 'number', 1500), ('barra_largura', 'number', 720),
    ('barra_rastro_vel', 'number', 300),
    ('fase', 'number', 1), ('fase_vista', 'number', 1), ('fase2_abaixo', 'number', 0.66),
    ('fase3_abaixo', 'number', 0.33), ('rugido_tempo', 'number', 1.2),
    ('fase3_espera_fator', 'number', 0.7), ('fase3_aviso_fator', 'number', 0.8),
    ('combo_chance', 'number', 0.6), ('combo_max', 'number', 2), ('combo_n', 'number', 0),
    ('sorteado', 'boolean', False), ('ultima_escolha', 'number', 3), ('n_opcoes', 'number', 2),
    ('ultimo_estado', 'string', ''), ('fim_ataque', 'boolean', False), ('etapa', 'number', 0),
    ('voo_manual', 'boolean', False), ('chao_y', 'number', 0), ('alvo_x', 'number', 0),
    ('pes_frac', 'number', 0.857), ('boca_frac', 'number', 0.3),
    ('ondas_vel', 'number', 480), ('ondas_dano', 'number', 15), ('ondas_ttl', 'number', 1.6),
    ('ondas_escala', 'number', 1.5), ('ondas_afasta', 'number', 60),
    ('mergulho_subida_vel', 'number', 1400), ('mergulho_subida_max', 'number', 1.5),
    ('mergulho_folga', 'number', 40), ('mergulho_mira_tempo', 'number', 1.6), ('mergulho_seguir', 'number', 6),
    ('mergulho_trava_tempo', 'number', 0.45), ('mergulho_queda_vel', 'number', 2200),
    ('mergulho_alcance_x', 'number', 1600), ('mergulho_raio', 'number', 200), ('mergulho_alcance_y', 'number', 90),
    ('mergulho_dano', 'number', 30), ('mergulho_coice', 'number', 700),
    ('espiral_altura', 'number', 260), ('espiral_subida_vel', 'number', 500), ('espiral_balanco', 'number', 12),
    ('espiral_balanco_vel', 'number', 3), ('espiral_duracao', 'number', 3.5), ('espiral_intervalo', 'number', 0.12),
    ('espiral_bracos', 'number', 3), ('espiral_giro', 'number', 17), ('espiral_vel', 'number', 300),
    ('espiral_dano', 'number', 10), ('espiral_ttl', 'number', 4), ('espiral_ang', 'number', 0),
    ('chuva_qtd', 'number', 14), ('chuva_intervalo', 'number', 0.09), ('chuva_gravidade', 'number', 1400),
    ('chuva_voo_min', 'number', 0.8), ('chuva_voo_max', 'number', 1.3), ('chuva_espalha', 'number', 500),
    ('chuva_dano', 'number', 12), ('chuva_ttl', 'number', 4), ('chuva_fim', 'number', 0.4),
    ('invocar_qtd', 'number', 4), ('invocar_max', 'number', 8), ('invocar_tempo', 'number', 1),
    ('invocar_raio', 'number', 220), ('invocar_altura', 'number', 0.5),
]

_N = [0]


def uid():                                       # determinístico: rodar no mesmo arquivo dá os mesmos ids
    _N[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogo/t124/{_N[0]}'))


def X(t, *p):
    return {'type': {'value': t}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acoes}
    if filhos:
        e['events'] = filhos
    return e


def cada(conds, acoes, filhos=None):
    e = {'type': 'BuiltinCommonInstructions::ForEach', 'object': 'cutulu', 'conditions': conds, 'actions': acoes}
    if filhos:
        e['events'] = filhos
    return e


def repete(expr, acoes):
    return {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': expr, 'conditions': [],
            'actions': acoes}


def grupo(nome, evs, cor=(74, 176, 228)):
    return {'type': 'BuiltinCommonInstructions::Group', 'colorB': cor[2], 'colorG': cor[1], 'colorR': cor[0],
            'creationTime': 0, 'name': nome, 'source': '', 'parameters': [], 'events': evs}


def coment(t):
    return {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0,
            'textG': 0, 'textR': 0}, 'comment': t, 'comment2': ''}


# atalhos
def num(v, op, val):  return X('NumberObjectVariable', 'cutulu', v, op, val)
def txt(v, val, op='='):  return X('StringObjectVariable', 'cutulu', v, op, f'"{val}"')
def bol(v, val):      return X('BooleanObjectVariable', 'cutulu', v, 'True' if val else 'False', '')
def cmp(a, op, b):    return X('BuiltinCommonInstructions::CompareNumbers', a, op, b)
def timer(n, op, v):  return X('CompareObjectTimer', 'cutulu', f'"{n}"', op, v)
def setn(v, op, val): return X('SetNumberObjectVariable', 'cutulu', v, op, val)
def sets(v, val):     return X('SetStringObjectVariable', 'cutulu', v, '=', f'"{val}"')
def setb(v, val):     return X('SetBooleanObjectVariable', 'cutulu', v, 'True' if val else 'False', '')
def zera(n):          return X('ResetObjectTimer', 'cutulu', f'"{n}"')
def anim(n, o='cutulu'): return X('AnimatableCapability::AnimatableBehavior::SetName', o, 'Animation', '=', f'"{n}"')
def som(s, vol, tom='1'): return X('PlaySound', '', s, '', vol, tom)
def plataforma(liga):
    return X('ActivateBehavior', 'cutulu', 'PlatformerObject', 'yes' if liga else 'no')


VIVO = bol('morto', False)
PES = 'cutulu.Y() + cutulu.Height() * cutulu.pes_frac'


def termina():
    """volta a perseguir e avisa o fim do ataque (para o combo)."""
    return [sets('estado', 'perseguir'), zera('estado'), zera('ataque'), setb('firme', False),
            setb('fim_ataque', True), anim('caminhando')]


def projetil(anim_, x, y, angulo, vel, dano, ttl, tipo):
    return [X('Create', '', 'projetil_inimigo', x, y, ''), anim(anim_, 'projetil_inimigo'),
            X('SetXY', 'projetil_inimigo', '=', f'{x} - projetil_inimigo.Width() / 2', '=',
              f'{y} - projetil_inimigo.Height() / 2'),
            X('AddForceAL', 'projetil_inimigo', angulo, vel, '1'),
            X('SetAngle', 'projetil_inimigo', '=', angulo),
            X('SetNumberObjectVariable', 'projetil_inimigo', 'dano', '=', dano),
            X('SetStringObjectVariable', 'projetil_inimigo', 'origem', '=', '"cutulu"'),
            X('SetStringObjectVariable', 'projetil_inimigo', 'tipo', '=', f'"{tipo}"'),
            X('ResetObjectTimer', 'projetil_inimigo', '"vida"'),
            X('SetNumberObjectVariable', 'projetil_inimigo', 'ttl', '=', ttl)]


def ondas():
    """uma onda para cada lado, rente ao chão (embaixo dos pés), que se pula."""
    acoes = []
    for lado, ang in ((1, '0'), (-1, '180')):
        x = f'cutulu.CenterX() {"+" if lado > 0 else "-"} cutulu.ondas_afasta'
        acoes += [X('Create', '', 'projetil_inimigo', x, PES, ''), anim('onda', 'projetil_inimigo'),
                  X('ScalableCapability::ScalableBehavior::SetValue', 'projetil_inimigo', 'Scale', '=',
                    'cutulu.ondas_escala'),
                  X('SetXY', 'projetil_inimigo', '=', f'{x} - projetil_inimigo.Width() / 2', '=',
                    f'{PES} - projetil_inimigo.Height() - 2'),
                  X('AddForceAL', 'projetil_inimigo', ang, 'cutulu.ondas_vel', '1'),
                  X('SetAngle', 'projetil_inimigo', '=', '0'),
                  X('FlippableCapability::FlippableBehavior::FlipX', 'projetil_inimigo', 'Flippable',
                    'yes' if lado < 0 else 'no'),
                  X('SetNumberObjectVariable', 'projetil_inimigo', 'dano', '=', 'cutulu.ondas_dano'),
                  X('SetStringObjectVariable', 'projetil_inimigo', 'origem', '=', '"cutulu"'),
                  X('SetStringObjectVariable', 'projetil_inimigo', 'tipo', '=', '"onda"'),
                  X('ResetObjectTimer', 'projetil_inimigo', '"vida"'),
                  X('SetNumberObjectVariable', 'projetil_inimigo', 'ttl', '=', 'cutulu.ondas_ttl')]
    return acoes


def eventos(anel, barra):
    evs = [coment(
        'Cutulu como chefe (três fases). A lógica antiga (andar, salto com anel de bile, fúria) fica em Inimigos > '
        'Purgatório > Cutulu (elite); esta folha roda depois dela e do HUD. Quando ele entra em "preparar", sorteia '
        'o ataque (nunca o mesmo seguido): escolha 2 salto, 3 mergulho, 4 espiral de olhos, 5 chuva de bile, '
        '6 invocar moscas. Fase 1: salto e mergulho; fase 2 (vida < fase2_abaixo): + espiral e chuva; fase 3 '
        '(vida < fase3_abaixo): + invocar, espera e aviso mais curtos e ataques em combo. Todos os números são '
        'variáveis do cutulu.')]

    # ---------------------------------------------------------------- preparo e fases
    evs.append(grupo('Preparo e fases', [
        coment('No começo: vida * vida_chefe_mult. Guarda chao_y (Y no chão) para pousar do voo. A fase sobe com a '
               'vida; ao trocar de fase (só perseguindo) ele ruge rugido_tempo s, invulnerável, e solta o anel.'),
        cada([VIVO, bol('chefe_preparado', False)],
             [setb('chefe_preparado', True), setn('max_vida', '*', 'cutulu.vida_chefe_mult'),
              setn('vida', '=', 'cutulu.max_vida'), setn('vida_controle', '=', 'cutulu.vida'),
              setn('chao_y', '=', 'cutulu.Y()'), setn('alvo_x', '=', 'cutulu.CenterX()')]),
        cada([VIVO, bol('voo_manual', False), txt('estado', 'perseguir'),
              X('PlatformBehavior::IsOnFloor', 'cutulu', 'PlatformerObject')],
             [setn('chao_y', '=', 'cutulu.Y()')]),
        cada([VIVO, num('fase', '<', '2'), cmp('cutulu.vida', '<', 'cutulu.max_vida * cutulu.fase2_abaixo')],
             [setn('fase', '=', '2')]),
        cada([VIVO, num('fase', '<', '3'), cmp('cutulu.vida', '<', 'cutulu.max_vida * cutulu.fase3_abaixo')],
             [setn('fase', '=', '3')]),
        cada([VIVO, cmp('cutulu.fase', '>', 'cutulu.fase_vista'), txt('estado', 'perseguir')],
             [setn('fase_vista', '=', 'cutulu.fase'), sets('estado', 'rugido'), zera('estado'),
              setb('firme', True), setb('invulneravel', True), anim('ataque_1'),
              som('som_aviso_cutulu.wav', '90', '0.7')],
             [ev([num('fase', '=', '3')],
                 [setn('ataque_espera', '*', 'cutulu.fase3_espera_fator'),
                  setn('aviso_tempo', '*', 'cutulu.fase3_aviso_fator')])]),
        cada([VIVO, txt('estado', 'rugido'), timer('estado', '>', 'cutulu.rugido_tempo')],
             [som('som_impacto.wav', '80', '0.8'), setb('invulneravel', False)] + termina(),
             [ev([], [setn('i', '=', '0')]), anel]),
    ]))

    # ---------------------------------------------------------------- sorteio
    evs.append(grupo('Escolha do ataque', [
        coment('Ao entrar em "preparar" sorteia entre as n_opcoes da fase (2, 4 ou 5), sem repetir a última. '
               'Com invocar_max moscas na cena, troca a invocação pelo salto.'),
        cada([VIVO, txt('estado', 'preparar'), bol('sorteado', False)],
             [setb('sorteado', True), setn('n_opcoes', '=', '2')],
             [ev([num('fase', '=', '2')], [setn('n_opcoes', '=', '4')]),
              ev([num('fase', '>=', '3')], [setn('n_opcoes', '=', '5')]),
              ev([], [setn('escolha', '=', '2 + mod(cutulu.ultima_escolha - 2 + RandomInRange(1, cutulu.n_opcoes - 1)'
                                           ', cutulu.n_opcoes)')]),
              ev([num('escolha', '=', '6'), X('SceneInstancesCount', '', 'moscas', '>=', 'cutulu.invocar_max')],
                 [setn('escolha', '=', '2')]),
              ev([], [setn('ultima_escolha', '=', 'cutulu.escolha')])]),
        cada([txt('estado', 'preparar', '!=')], [setb('sorteado', False)]),
    ]))

    # ---------------------------------------------------------------- começo
    evs.append(grupo('Começo dos ataques novos', [
        coment('Depois do aviso, Inimigos põe "atacar"; com escolha >= 3 o ataque é daqui.'),
        cada([VIVO, txt('estado', 'atacar'), num('escolha', '>=', '3')],
             [setb('firme', True), zera('estado'), zera('tiro'), setn('etapa', '=', '1'), setn('i', '=', '0')],
             [ev([num('escolha', '=', '3')],
                 [sets('estado', 'mergulho'), plataforma(False), setb('voo_manual', True),
                  setb('invulneravel', True), anim('voando'), som('som_investida.wav', '70', '0.8')]),
              ev([num('escolha', '=', '4')],
                 [sets('estado', 'espiral'), plataforma(False), setb('voo_manual', True), anim('voando'),
                  setn('espiral_ang', '=', 'RandomFloat(360)'), som('som_espiral.wav', '60', '0.8')]),
              ev([num('escolha', '=', '5')], [sets('estado', 'chuva'), anim('ataque_2'), som('som_bile.wav', '60')]),
              ev([num('escolha', '=', '6')],
                 [sets('estado', 'invocar'), anim('ataque_1'), som('som_aviso_cutulu.wav', '80', '1.3')])]),
    ]))

    # ---------------------------------------------------------------- mergulho
    mira_x = ('clamp(pato.CenterX(), cutulu.base_x + cutulu.Width() / 2 - cutulu.mergulho_alcance_x, '
              'cutulu.base_x + cutulu.Width() / 2 + cutulu.mergulho_alcance_x)')
    no_alto = [X('SetXY', 'cutulu', '=', 'cutulu.alvo_x - cutulu.Width() / 2', '=',
                 'CameraBorderTop("") - cutulu.Height() - cutulu.mergulho_folga'),
               X('SetXY', 'cutulu_sombra', '=', 'cutulu.alvo_x - cutulu_sombra.Width() / 2', '=',
                 'cutulu.chao_y + cutulu.Height() * cutulu.pes_frac - cutulu_sombra.Height() / 2')]
    acerto = [X('SetNumberObjectVariable', 'pato', 'vida', '-', 'cutulu.mergulho_dano'),
              X('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
              X('ResetObjectTimer', 'pato', '"iframes"'),
              X('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', '"cutulu"'),
              X('SetNumberObjectVariable', 'pato', 'coice_vx', '=',
                'sign(pato.CenterX() - cutulu.CenterX() + 0.001) * cutulu.mergulho_coice')]
    evs.append(grupo('Mergulho', [
        coment('Sobe a mergulho_subida_vel até sair da tela (invulnerável). Uma sombra segue o pato no chão '
               '(mergulho_seguir, dentro de mergulho_alcance_x de onde ele nasceu) por mergulho_mira_tempo s, trava '
               'piscando mergulho_trava_tempo s e ele cai a mergulho_queda_vel. No pouso: mergulho_dano em quem está '
               'no chão a até mergulho_raio px, e as ondas.'),
        cada([VIVO, txt('estado', 'mergulho'), num('etapa', '=', '1')],
             [X('SetY', 'cutulu', '-', 'cutulu.mergulho_subida_vel * TimeDelta()')],
             [ev([cmp('cutulu.Y() + cutulu.Height()', '<', 'CameraBorderTop("") - cutulu.mergulho_folga')],
                 [setn('etapa', '=', '2')]),
              ev([timer('estado', '>', 'cutulu.mergulho_subida_max')], [setn('etapa', '=', '2')]),
              ev([num('etapa', '=', '2')],
                 [zera('estado'), setn('alvo_x', '=', mira_x),
                  X('Create', '', 'cutulu_sombra', 'cutulu.alvo_x', 'cutulu.chao_y', ''),
                  X('ChangePlan', 'cutulu_sombra', '=', 'cutulu.ZOrder() + 1'),
                  anim('segue', 'cutulu_sombra'), som('som_aviso_mergulhador.wav', '70', '0.7')])]),
        cada([VIVO, txt('estado', 'mergulho'), num('etapa', '=', '2')],
             [setn('alvo_x', '+', f'({mira_x} - cutulu.alvo_x) * min(1, cutulu.mergulho_seguir * TimeDelta())')]
             + no_alto,
             [ev([timer('estado', '>', 'cutulu.mergulho_mira_tempo')],
                 [setn('etapa', '=', '3'), zera('estado'), anim('trava', 'cutulu_sombra'),
                  som('som_aviso_cutulu.wav', '80', '1.4')])]),
        cada([VIVO, txt('estado', 'mergulho'), num('etapa', '=', '3')], no_alto,
             [ev([timer('estado', '>', 'cutulu.mergulho_trava_tempo')],
                 [setn('etapa', '=', '4'), zera('estado'), anim('ataque_2')])]),
        cada([VIVO, txt('estado', 'mergulho'), num('etapa', '=', '4')],
             [X('SetY', 'cutulu', '+', 'cutulu.mergulho_queda_vel * TimeDelta()')],
             [ev([X('PosY', 'cutulu', '>=', 'cutulu.chao_y')],
                 [X('SetY', 'cutulu', '=', 'cutulu.chao_y'), plataforma(True), setb('voo_manual', False),
                  setb('invulneravel', False), X('Delete', 'cutulu_sombra', ''),
                  som('som_impacto.wav', '100', '0.7')] + ondas() + termina(),
                 [ev([cmp('abs(pato.CenterX() - cutulu.CenterX())', '<', 'cutulu.mergulho_raio'),
                      cmp('pato.Y() + pato.Height()', '>', f'{PES} - cutulu.mergulho_alcance_y'),
                      X('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
                      X('BooleanObjectVariable', 'pato', 'morto', 'False', '')], acerto)])]),
    ]))

    # ---------------------------------------------------------------- espiral
    olho = projetil('olho', 'cutulu.CenterX()', 'cutulu.CenterY()',
                    'cutulu.espiral_ang + cutulu.i * 360 / max(1, cutulu.espiral_bracos)', 'cutulu.espiral_vel',
                    'cutulu.espiral_dano', 'cutulu.espiral_ttl', 'olho') + [setn('i', '+', '1')]
    evs.append(grupo('Espiral de olhos', [
        coment('Sobe espiral_altura px acima do chão e paira balançando; a cada espiral_intervalo s solta '
               'espiral_bracos olhos em volta e gira espiral_giro graus, por espiral_duracao s. Depois desce.'),
        cada([VIVO, txt('estado', 'espiral'), num('etapa', '=', '1')],
             [X('SetY', 'cutulu', '-', 'cutulu.espiral_subida_vel * TimeDelta()')],
             [ev([X('PosY', 'cutulu', '<=', 'cutulu.chao_y - cutulu.espiral_altura')],
                 [setn('etapa', '=', '2'), zera('estado'), zera('tiro')])]),
        cada([VIVO, txt('estado', 'espiral'), num('etapa', '=', '2')],
             [X('SetY', 'cutulu', '=', 'cutulu.chao_y - cutulu.espiral_altura + sin(cutulu.ObjectTimerElapsedTime('
                '"estado") * cutulu.espiral_balanco_vel) * cutulu.espiral_balanco')],
             [ev([timer('tiro', '>', 'cutulu.espiral_intervalo')],
                 [zera('tiro'), setn('i', '=', '0'), som('som_tiro_olho.wav', '25', 'RandomFloatInRange(0.9, 1.1)')]),
              ev([num('i', '=', '0')], [], [repete('cutulu.espiral_bracos', olho)]),
              ev([num('i', '>', '0')], [setn('espiral_ang', '+', 'cutulu.espiral_giro'), setn('i', '=', '-1')]),
              ev([timer('estado', '>', 'cutulu.espiral_duracao')], [setn('etapa', '=', '3'), zera('estado')])]),
        cada([VIVO, txt('estado', 'espiral'), num('etapa', '=', '3')],
             [X('SetY', 'cutulu', '+', 'cutulu.espiral_subida_vel * TimeDelta()')],
             [ev([X('PosY', 'cutulu', '>=', 'cutulu.chao_y')],
                 [X('SetY', 'cutulu', '=', 'cutulu.chao_y'), plataforma(True), setb('voo_manual', False)]
                 + termina())]),
    ]))

    # ---------------------------------------------------------------- chuva
    bx, by = 'cutulu.CenterX()', 'cutulu.Y() + cutulu.Height() * cutulu.boca_frac'
    bile = [X('Create', '', 'projetil_inimigo', bx, by, ''), anim('bile', 'projetil_inimigo'),
            X('SetXY', 'projetil_inimigo', '=', f'{bx} - projetil_inimigo.Width() / 2', '=',
              f'{by} - projetil_inimigo.Height() / 2'),
            X('AddForceAL', 'projetil_inimigo', f'ToDeg(atan2(0, cutulu.dx - ({bx})))',
              f'abs(cutulu.dx - ({bx})) / cutulu.rnd', '1'),
            X('SetNumberObjectVariable', 'projetil_inimigo', 'gravidade', '=', 'cutulu.chuva_gravidade'),
            X('SetNumberObjectVariable', 'projetil_inimigo', 'vy', '=',
              f'(pato.CenterY() - ({by}) - 0.5 * cutulu.chuva_gravidade * cutulu.rnd * cutulu.rnd) / cutulu.rnd'),
            X('SetNumberObjectVariable', 'projetil_inimigo', 'dano', '=', 'cutulu.chuva_dano'),
            X('SetStringObjectVariable', 'projetil_inimigo', 'origem', '=', '"cutulu"'),
            X('SetStringObjectVariable', 'projetil_inimigo', 'tipo', '=', '"bile"'),
            X('ResetObjectTimer', 'projetil_inimigo', '"vida"'),
            X('SetNumberObjectVariable', 'projetil_inimigo', 'ttl', '=', 'cutulu.chuva_ttl'),
            som('som_cuspe.wav', '35', 'RandomFloatInRange(0.85, 1.15)')]
    evs.append(grupo('Chuva de bile', [
        coment('Cospe chuva_qtd bolhas de bile, uma a cada chuva_intervalo s, em arco (chuva_gravidade): cada uma '
               'leva entre chuva_voo_min e chuva_voo_max s para chegar à altura do pato, a até chuva_espalha px '
               'para o lado dele.'),
        cada([VIVO, txt('estado', 'chuva')], [],
             [ev([timer('tiro', '>', 'cutulu.chuva_intervalo'), cmp('cutulu.i', '<', 'cutulu.chuva_qtd')],
                 [zera('tiro'), setn('i', '+', '1'),
                  setn('rnd', '=', 'RandomFloatInRange(cutulu.chuva_voo_min, cutulu.chuva_voo_max)'),
                  setn('dx', '=', 'pato.CenterX() + RandomFloatInRange(-cutulu.chuva_espalha, cutulu.chuva_espalha)')]
                 + bile),
              ev([cmp('cutulu.i', '>=', 'cutulu.chuva_qtd'),
                  timer('estado', '>', 'cutulu.chuva_qtd * cutulu.chuva_intervalo + cutulu.chuva_fim')],
                 termina())]),
    ]))

    # ---------------------------------------------------------------- invocação
    evs.append(grupo('Invocação', [
        coment('Depois de invocar_tempo s rugindo, aparecem invocar_qtd moscas a até invocar_raio px dele. As '
               'invocadas (invocada = True) não soltam moedas e morrem junto com ele.'),
        cada([VIVO, txt('estado', 'invocar'), timer('estado', '>', 'cutulu.invocar_tempo')],
             [som('som_olhos.wav', '70', '0.8')] + termina(),
             [repete('cutulu.invocar_qtd', [
                 X('Create', '', 'moscas',
                   'cutulu.CenterX() + RandomFloatInRange(-cutulu.invocar_raio, cutulu.invocar_raio)',
                   'cutulu.Y() + RandomFloatInRange(0, cutulu.Height() * cutulu.invocar_altura)', ''),
                 X('SetNumberObjectVariable', 'moscas', 'qtd_moedas', '=', '0'),
                 X('SetBooleanObjectVariable', 'moscas', 'invocada', 'True', ''),
                 X('SetNumberObjectVariable', 'moscas', 'base_x', '=', 'moscas.X()'),
                 X('SetNumberObjectVariable', 'moscas', 'base_y', '=', 'moscas.Y()'),
                 X('Create', '', 'sangue_gosma', 'moscas.CenterX()', 'moscas.CenterY()', '')])]),
        ev([X('SceneInstancesCount', '', 'cutulu', '=', '0')], [],
           [ev([X('BooleanObjectVariable', 'moscas', 'invocada', 'True', ''),
                X('BooleanObjectVariable', 'moscas', 'morto', 'False', '')],
               [X('SetNumberObjectVariable', 'moscas', 'vida', '=', '0')])]),
        cada([bol('morto', True)], [],
             [ev([X('BooleanObjectVariable', 'moscas', 'invocada', 'True', ''),
                  X('BooleanObjectVariable', 'moscas', 'morto', 'False', '')],
                 [X('SetNumberObjectVariable', 'moscas', 'vida', '=', '0')]),
              ev([bol('voo_manual', True)],
                 [plataforma(True), setb('voo_manual', False), X('Delete', 'cutulu_sombra', '')])]),
    ]))

    # ---------------------------------------------------------------- ondas do salto, combo, fim do quadro
    evs.append(grupo('Ondas do salto e combos', [
        coment('O salto (de Inimigos) termina quando estado vai de "atacar" a "perseguir": soltam-se as ondas. Na '
               'fase 3, ao fim de cada ataque, com chance combo_chance (até combo_max seguidos) ele já prepara o '
               'próximo sem esperar. ultimo_estado guarda o estado no fim do quadro.'),
        cada([VIVO, txt('estado', 'perseguir'), txt('ultimo_estado', 'atacar')],
             ondas() + [setb('fim_ataque', True)]),
        cada([bol('fim_ataque', True)], [setb('fim_ataque', False)],
             [ev([VIVO, num('fase', '>=', '3'), cmp('cutulu.combo_n', '<', 'cutulu.combo_max'),
                  cmp('RandomFloat(1)', '<', 'cutulu.combo_chance')],
                 [setn('combo_n', '+', '1'), sets('estado', 'preparar'), zera('estado'), setb('sorteado', False),
                  setn('direcao', '=', 'sign(pato.CenterX() - cutulu.CenterX())'), anim('ataque_1'),
                  som('som_aviso_cutulu.wav', '65', '1.15')]),
              ev([txt('estado', 'preparar', '!=')], [setn('combo_n', '=', '0')])]),
        cada([], [X('SetStringObjectVariable', 'cutulu', 'ultimo_estado', '=', 'cutulu.estado')]),
    ]))
    evs.append(barra)
    return evs


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if any(x['name'] == FOLHA for x in d['externalEvents']):
        sys.exit('t124 já foi aplicada; não roda de novo.')
    objs = {o['name']: o for o in d['objects']}
    ext = {x['name']: x for x in d['externalEvents']}

    # variáveis novas (as que já existem ficam)
    cut = objs['cutulu']
    tem = {v['name'] for v in cut['variables']}
    for n, t, v in VARS:
        if n not in tem:
            cut['variables'].append({'name': n, 'persistentUuid': uid(), 'type': t, 'value': v})
    if not any(v['name'] == 'invocada' for v in objs['moscas']['variables']):
        objs['moscas']['variables'].append({'name': 'invocada', 'persistentUuid': uid(), 'type': 'boolean',
                                            'value': False})

    # sombra do mergulho
    rec = d['resources']['resources']
    anims = []
    for nome, quadros, espera in (('segue', [1, 2, 3, 2], 0.1), ('trava', [1, 2], 0.06)):
        sprites = []
        for q in quadros:
            arq = f'{PASTA_IMG}sombra_{nome}_{q}.png'
            if not any(r['name'] == arq for r in rec):
                rec.append({'file': arq, 'kind': 'image', 'metadata': '', 'name': arq, 'smoothed': False,
                            'userAdded': True})
            sprites.append({'hasCustomCollisionMask': False, 'image': arq, 'points': [],
                            'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                            'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0},
                            'customCollisionMask': []})
        anims.append({'name': nome, 'useMultipleDirections': False,
                      'directions': [{'looping': True, 'timeBetweenFrames': espera, 'sprites': sprites}]})
    if 'cutulu_sombra' not in objs:
        d['objects'].append({'adaptCollisionMaskAutomatically': True, 'assetStoreId': '', 'name': 'cutulu_sombra',
                             'persistentUuid': uid(), 'type': 'Sprite', 'updateIfNotVisible': False,
                             'variables': [], 'effects': [], 'behaviors': [], 'animations': anims})

        def poe(no):
            for c in no.get('children', []):
                if c.get('folderName') == 'purgatorio' and any(x.get('objectName') == 'cutulu'
                                                               for x in c.get('children', [])):
                    c['children'].append({'objectName': 'cutulu_sombra'})
                    return True
                if poe(c):
                    return True
            return False
        if not poe(d['objectsFolderStructure']):
            d['objectsFolderStructure']['children'].append({'objectName': 'cutulu_sombra'})

    # pedaços reaproveitados: o anel de bile do salto e a barra do chefe do Inferno
    def acha(evs, f):
        for e in evs:
            if f(e):
                return e
            r = acha(e.get('events') or [], f)
            if r:
                return r
    g = acha(ext['Inimigos']['events'], lambda e: e.get('name') == 'Cutulu (elite)')
    anel = copy.deepcopy(acha(g['events'], lambda e: e.get('type') == 'BuiltinCommonInstructions::Repeat'))
    assert 'anel_qtd' in anel['repeatExpression']
    barra = copy.deepcopy(acha(ext['Chefe']['events'], lambda e: e.get('name') == 'Barra do chefe'))
    barra = json.loads(json.dumps(barra).replace('demonio_chefe', 'cutulu'))
    barra['events'].insert(0, coment('Barra de chefe (igual à do demônio): aparece com o pato a até barra_dist px.'))

    d['externalEvents'].append({'associatedLayout': 'Purgatorio', 'name': FOLHA, 'events': eventos(anel, barra)})
    for nome in CENAS:
        cena = next(l for l in d['layouts'] if l['name'] == nome)
        i = next(k for k, e in enumerate(cena['events']) if e.get('target') == 'HUD')
        cena['events'].insert(i + 1, {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0},
                                      'target': FOLHA})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('cutulu chefe: folha', FOLHA, 'ligada em', CENAS)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
