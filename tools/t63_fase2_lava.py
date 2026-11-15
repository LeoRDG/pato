"""Tarefa 63: segunda fase do demônio chefe, no lago de lava embaixo da arena.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - cada ataque racha o chão da arena (o piso de tiles_inferno entre quebra_x_min/quebra_x_max e
    quebra_y_min/quebra_y_max, variáveis de cena): o cutelo, no momento em que desce, arranca golpe_quebra_qtd
    tiles sorteados em golpe_quebra_raio px em volta de um ponto golpe_quebra_dx px à frente dele; a explosão arranca
    explosao_quebra_qtd sorteados em explosao_quebra_raio px em volta dele. As quebra_topo_linhas de cima do piso
    nunca quebram nesses ataques, então o chão continua inteiro por cima e aguenta até a fúria;
  - ao entrar em fúria (assim que volta a perseguir) ele faz a explosão grande (golpe "grande", a mesma animação
    explosao): no auge, todo o piso da arena some, grande_explosoes explosões estouram ao longo dele, o sangue da
    arena some, a variável de cena fase2 liga e o demônio cai (queda_vel px/s) até a lava; o pato cai junto.
    Caindo (golpe "queda") ele fica alternando os quadros queda_quadro_a e o seguinte da explosao (a cada
    queda_quadro_tempo s) e a cada queda_bola_espera s cospe queda_bolas bolas de fogo em direções sorteadas, que
    também descem a queda_vel * queda_bola_herda para acompanhar a queda; ao chegar na lava volta a perseguir;
  - cada tile quebrado solta destroco_por_tile pedaços (objeto destroco, pedras soltas recortadas do atlas do inferno) que voam
    e caem com a gravidade dele até fundo_y;
  - na lava o demônio fica afundado lava_afunda px, atrás da lava (z da lava - 1), e anda até o pato a
    velocidade * ritmo * lava_vel_fator sem sair da faixa da arena (lava_borda px das paredes); os ataques continuam,
    e o cutelo vira um salto bem avisado: de até lava_ataque_alcance px ele pula bem alto (lava_pulo_altura) para cima
    de onde o pato estava, fica lá lava_espera_t s com o cutelo erguido, despenca e crava o cutelo baixo na ponte; só
    machuca logo na batida (lava_golpe_janela s) e depois afunda de volta;
  - pontes (tiles_inferno_ponte, plataformas de passar por baixo) sobre a lava para o pato ficar;
  - na fase 2 a lava machuca o pato (lava.dano_fase2, quando ele afunda mais de lava.dano_margem px) e o joga para
    cima com lava.pulo_vel (só nesse pulo; depois volta pato.pulo_forca_normal); as plataforma_movel ficam escondidas e desligadas até o demônio morrer, para o pato não ter para onde ir.
Grupo "Fase 2" no fim dos eventos externos "Chefe" (o início da explosão grande entra logo depois do evento da
fúria, para ter prioridade sobre os outros ataques).
"""
import json, os, sys, uuid
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, DES, TM, PONTE, LAVA, PM = 'demonio_chefe', 'destroco', 'tiles_inferno', 'tiles_inferno_ponte', 'lava', 'plataforma_movel'
I, E, grupo = t59.I, t59.E, t59.grupo

ATLAS = 'assets/gandalf_hell/tiles/tiles_inferno_2x.png'
ROCHAS, COLS_ATLAS, T = [145, 146, 147, 129], 17, 64   # tiles de pedras soltas do atlas
IMGS = [f'assets/destroco/pedaco_{i:02d}.png' for i in range(4)]

VARS_CHEFE = [('golpe_quebra_dx', 'number', 220), ('golpe_quebra_raio', 'number', 110), ('golpe_quebra_qtd', 'number', 4),
              ('explosao_quebra_raio', 'number', 220), ('explosao_quebra_qtd', 'number', 8),
              ('quebra_som_volume', 'number', 45), ('grande_explosoes', 'number', 8), ('grande_som_volume', 'number', 100),
              ('grande_tom', 'number', 0.65), ('queda_vel', 'number', 1800), ('lava_afunda', 'number', 60),
              ('lava_borda', 'number', 150), ('lava_vel_fator', 'number', 1),
              ('lava_pulo_altura', 'number', 600), ('lava_y', 'number', 0),
              ('lava_ataque_alcance', 'number', 900), ('lava_golpe_baixo', 'number', 40), ('lava_golpe_dx', 'number', 170),
              ('lava_subida_t', 'number', 0.55), ('lava_espera_t', 'number', 0.6), ('lava_pancada_vel', 'number', 2600),
              ('lava_quadro_espera', 'number', 8), ('lava_quadro_golpe', 'number', 9), ('lava_golpe_janela', 'number', 0.2),
              ('lava_cravado_t', 'number', 0.4), ('lava_volta_t', 'number', 0.35),
              ('lava_x0', 'number', 0), ('lava_x1', 'number', 0), ('lava_y1', 'number', 0), ('lava_t', 'number', 0),
              ('lava_u', 'number', 0), ('lava_quadro', 'number', 0), ('lava_avisou', 'boolean', False),
              ('quebra_feita', 'boolean', False), ('grande_feita', 'boolean', False), ('grande_i', 'number', 0),
              ('no_lava', 'boolean', False),
              ('queda_quadro_a', 'number', 8), ('queda_quadro_tempo', 'number', 0.08), ('queda_bola_espera', 'number', 0.12),
              ('queda_bolas', 'number', 2), ('queda_bola_herda', 'number', 1), ('queda_quadro', 'number', 0)]
VARS_CENA = [('fase2', 'boolean', False), ('quebra_x_min', 'number', 11764), ('quebra_x_max', 'number', 13940),
             ('quebra_y_min', 'number', -7849), ('quebra_y_max', 'number', -7529), ('quebra_topo_linhas', 'number', 1),
             ('destroco_por_tile', 'number', 2), ('plataformas_desligadas', 'boolean', False)]
VARS_DESTROCO = [('gravidade', 'number', 2600), ('vel_x', 'number', 380), ('vel_y_min', 'number', -900),
                 ('vel_y_max', 'number', -250), ('giro', 'number', 600), ('fundo_y', 'number', 330), ('z', 'number', 2805),
                 ('vx', 'number', 0), ('vy', 'number', 0), ('va', 'number', 0)]
VARS_LAVA = [('dano_fase2', 'number', 15), ('dano_margem', 'number', 10), ('pulo_vel', 'number', 1500)]
VARS_PATO = [('lava_pulo', 'boolean', False)]
# pontes sobre a lava (x, y do topo da tábua, largura em tiles); bem acima da superfície (lava.Y + 22%): o demônio
# precisa pular para alcançar com o cutelo
PONTES = [(11800, 120, 5), (12370, 120, 5), (12940, 120, 5), (13510, 120, 5)]
Z_PONTE = 1012                      # na frente da lava (1010), atrás do pato


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t63/' + '/'.join(p)))


def js(linhas, objetos=D):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': objetos,
            'useStrict': True, 'eventsSheetExpanded': False}


# rotina comum aos três jeitos de quebrar: tira tiles do piso e solta pedaços
QUEBRA = [
    'const cena = runtimeScene.getVariables();',
    'const n = (nome) => cena.get(nome).getAsNumber();',
    'const sorteio = (a, b) => a + Math.random() * (b - a);',
    'const solta = (x, y) => {',
    '  for (let k = 0; k < n("destroco_por_tile"); k++) {',
    '    const o = runtimeScene.createObject("destroco");',
    '    if (!o) return;',
    '    const v = o.getVariables();',
    '    const num = (nome) => v.get(nome).getAsNumber();',
    f'    o.setAnimation(Math.floor(Math.random() * {len(IMGS)}));      // um dos pedaços',
    '    o.setPosition(x + sorteio(-o.getWidth(), 0), y + sorteio(-o.getHeight(), 0));',
    '    o.setZOrder(num("z"));',
    '    o.setAngle(sorteio(0, 360));',
    '    v.get("vx").setNumber(sorteio(-1, 1) * num("vel_x"));',
    '    v.get("vy").setNumber(sorteio(num("vel_y_min"), num("vel_y_max")));',
    '    v.get("va").setNumber(sorteio(-1, 1) * num("giro"));',
    '  }',
    '};',
    '// qtd: quantos tiles sólidos sortear e tirar; topo: quantas linhas de cima do piso ficam intactas',
    'const quebra = (x0, x1, qtd, topo) => {',
    '  const xa = Math.max(x0, n("quebra_x_min")), xb = Math.min(x1, n("quebra_x_max") - 1);',
    '  const ya = n("quebra_y_min"), yb = n("quebra_y_max") - 1;',
    '  if (xb < xa) return;',
    '  for (const m of runtimeScene.getObjects("tiles_inferno")) {',
    '    const [c0, r0] = m.getGridCoordinatesFromSceneCoordinates(xa, ya);',
    '    const [c1, r1] = m.getGridCoordinatesFromSceneCoordinates(xb, yb);',
    '    const inteiros = [];',
    '    for (let c = c0; c <= c1; c++)',
    '      for (let r = r0 + topo; r <= r1; r++) {',
    '        const id = m.getTileAtGridCoordinates(c, r);',
    '        if (id !== undefined && id >= 0) inteiros.push([c, r]);',
    '      }',
    '    for (let k = 0; k < qtd && inteiros.length > 0; k++) {',
    '      const [c, r] = inteiros.splice(Math.floor(Math.random() * inteiros.length), 1)[0];',
    '      m.removeTileAtGridCoordinates(c, r);',
    '      solta(m.getSceneXCoordinateOfTileCenter(c, r), m.getSceneYCoordinateOfTileCenter(c, r));',
    '    }',
    '  }',
    '};',
]


def quebra_em_volta(dx, raio, qtd):
    return js(QUEBRA + [
        'for (const b of objects) {',
        '  const v = b.getVariables();',
        '  const num = (nome) => v.get(nome).getAsNumber();',
        f'  const cx = b.getCenterXInScene() + {dx};',
        f'  quebra(cx - num("{raio}"), cx + num("{raio}"), num("{qtd}"), n("quebra_topo_linhas"));',
        '}'])


def eventos_inicio_grande():
    """Entra no grupo Demônio chefe, logo depois do evento da fúria."""
    return E([I('BooleanObjectVariable', D, 'em_furia', 'True', ''),
              I('BooleanObjectVariable', D, 'grande_feita', 'False', ''),
              I('StringObjectVariable', D, 'estado', '=', '"perseguir"')],
             [I('SetBooleanObjectVariable', D, 'grande_feita', 'True', ''),
              I('SetStringObjectVariable', D, 'estado', '=', '"atacar"'),
              I('SetStringObjectVariable', D, 'golpe', '=', '"grande"'),
              I('ResetObjectTimer', D, '"estado"'),
              I('ResetObjectTimer', D, '"explosao"'),
              I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"explosao"'),
              I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', D, 'PlatformerObject', '=', '0'),
              I('PlaySound', '', 'som_fogo_caveira.wav', '', f'{D}.grande_som_volume', f'{D}.grande_tom')])


def eventos():
    estado = lambda s: I('StringObjectVariable', D, 'estado', '=', f'"{s}"')
    golpe = lambda s: I('StringObjectVariable', D, 'golpe', '=', f'"{s}"')
    fase2 = lambda v: I('BooleanVariable', 'fase2', v, '')
    vivo = I('BooleanObjectVariable', D, 'morto', 'False', '')
    timer = lambda var: I('CompareObjectTimer', D, '"estado"', '>', f'{D}.{var} / {D}.ritmo')
    feita = [I('SetBooleanObjectVariable', D, 'quebra_feita', 'True', ''),
             I('PlaySound', '', 'som_explosao.wav', '', f'{D}.quebra_som_volume', 'RandomFloatInRange(0.8, 0.9)')]
    x_min, x_max, y_min = 'Variable(quebra_x_min)', 'Variable(quebra_x_max)', 'Variable(quebra_y_min)'
    x_grande = f'{x_min} + ({x_max} - {x_min}) * ({D}.grande_i * 2 + 1) / ({D}.grande_explosoes * 2)'
    superficie = f'{LAVA}.Y() + {LAVA}.Height() * {LAVA}.superficie_frac'
    dx = f'(pato.CenterX() - {D}.CenterX())'
    plataformas = lambda ligar: [I('SetBooleanVariable', 'plataformas_desligadas', 'False' if ligar else 'True', ''),
                                 I('Show', PM, '') if ligar else I('Hide', PM),
                                 I('ActivateBehavior', PM, 'Platform', 'yes' if ligar else 'no')]
    chefe_fora = {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
        I('SceneInstancesCount', '', D, '=', '0'), I('BooleanObjectVariable', D, 'morto', 'True', '')]}
    return grupo('Fase 2', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Fase 2: cada ataque quebra blocos sorteados dentro do piso da arena (a camada de cima fica); na fúria a explosão grande quebra tudo e a luta '
                    'continua na lava lá embaixo, sobre as pontes. A zona que quebra fica nas variáveis de cena quebra_*; '
                    'o resto nas variáveis do demonio_chefe, do destroco e da lava.'},
        E([I('StringObjectVariable', D, 'estado', '!=', '"atacar"')],
          [I('SetBooleanObjectVariable', D, 'quebra_feita', 'False', '')]),
        # o cutelo bate no chão à frente dele
        E([fase2('False'), vivo, estado('atacar'), golpe('cutelo'), I('BooleanObjectVariable', D, 'quebra_feita', 'False', ''),
           timer('golpe_inicio')], feita,
          [quebra_em_volta('num("direcao") * num("golpe_quebra_dx")', 'golpe_quebra_raio', 'golpe_quebra_qtd')]),
        # a explosão comum racha o chão em volta dele
        E([fase2('False'), vivo, estado('atacar'), golpe('explosao'), I('BooleanObjectVariable', D, 'explosao_feita', 'True', ''),
           I('BooleanObjectVariable', D, 'quebra_feita', 'False', '')], feita,
          [quebra_em_volta('0', 'explosao_quebra_raio', 'explosao_quebra_qtd')]),
        # explosão grande: o piso inteiro cai
        E([fase2('False'), estado('atacar'), golpe('grande'), timer('explosao_disparo')],
          [I('SetBooleanVariable', 'fase2', 'True', ''),
           I('SetNumberObjectVariable', D, 'grande_i', '=', '0'),
           I('PlaySound', '', 'som_explosao.wav', '', f'{D}.grande_som_volume', f'{D}.grande_tom'),
           I('ActivateBehavior', D, 'PlatformerObject', 'no'),
           I('SetStringObjectVariable', D, 'golpe', '=', '"queda"'),
           I('ResetObjectTimer', D, '"queda"'), I('ResetObjectTimer', D, '"queda_bola"')], [
            {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': f'{D}.grande_explosoes', 'conditions': [],
             'actions': [I('Create', '', 'explosao_fogo', x_grande, y_min, ''),
                         I('Create', '', 'explosao_fumaca', x_grande, y_min, ''),
                         I('Create', '', 'explosao_faiscas', x_grande, y_min, ''),
                         I('SetNumberObjectVariable', D, 'grande_i', '+', '1')], 'events': []},
            js(QUEBRA + ['quebra(n("quebra_x_min"), n("quebra_x_max"), Infinity, 0);']),
            E([I('PosX', 'sangue', '>=', f'{x_min} - sangue.Width()'), I('PosX', 'sangue', '<=', x_max),
               I('PosY', 'sangue', '<', 'Variable(quebra_y_max)'), I('PosY', 'sangue', '>', f'{y_min} - sangue.Height() * 2')],
              [I('Delete', 'sangue', '')]),
        ]),
        # o demônio cai até a lava e fica afundado nela
        E([fase2('True'), I('BooleanObjectVariable', D, 'no_lava', 'False', '')],
          [I('SetY', D, '+', f'{D}.queda_vel * TimeDelta()')], [
            # caindo: fica no auge do fogo da explosão (quadros queda_quadro_a e o seguinte) cuspindo bolas de fogo
            E([vivo, golpe('queda')],
              [I('SetNumberObjectVariable', D, 'queda_quadro', '=',
                 f'{D}.queda_quadro_a + mod(floor({D}.ObjectTimerElapsedTime("queda") / {D}.queda_quadro_tempo), 2)')], [
                js(['// segura a animação explosao no quadro da variável queda_quadro',
                    'for (const b of objects) {',
                    '  if (b.getAnimationName() !== "explosao") b.setAnimationName("explosao");',
                    '  b.pauseAnimation();',
                    '  b.setAnimationFrame(b.getVariables().get("queda_quadro").getAsNumber());',
                    '}']),
                E([I('CompareObjectTimer', D, '"queda_bola"', '>', f'{D}.queda_bola_espera')],
                  [I('ResetObjectTimer', D, '"queda_bola"')], [
                    {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': f'{D}.queda_bolas', 'conditions': [],
                     'actions': [
                         I('SetNumberObjectVariable', D, 'explosao_angulo', '=', 'RandomFloatInRange(0, 360)'),
                         I('Create', '', 'bola_fogo', f'{D}.CenterX()', f'{D}.CenterY()', ''),
                         I('SetXY', 'bola_fogo', '=', f'{D}.CenterX() + {D}.explosao_raio * cos(ToRad({D}.explosao_angulo)) - bola_fogo.Width() / 2',
                           '=', f'{D}.CenterY() + {D}.explosao_raio * sin(ToRad({D}.explosao_angulo)) - bola_fogo.Height() / 2'),
                         I('AddForceAL', 'bola_fogo', f'{D}.explosao_angulo', f'{D}.explosao_vel', '1'),
                         I('AddForceXY', 'bola_fogo', '0', f'{D}.queda_vel * {D}.queda_bola_herda', '1'),
                         I('SetAngle', 'bola_fogo', '=', f'{D}.explosao_angulo'),
                         I('SetNumberObjectVariable', 'bola_fogo', 'dano', '=', f'{D}.explosao_dano'),
                         I('SetNumberObjectVariable', 'bola_fogo', 'vida', '=', f'{D}.explosao_vida'),
                         I('ResetObjectTimer', 'bola_fogo', '"vida"')], 'events': []},
                ]),
            ]),
            # morreu caindo: solta a animação para a morte tocar
            E([I('BooleanObjectVariable', D, 'morto', 'True', ''), golpe('queda')],
              [I('SetStringObjectVariable', D, 'golpe', '=', '""')],
              [js(['for (const b of objects) b.resumeAnimation();'])]),
            E([I('CollisionNP', D, LAVA, '', '', '')],
              [I('SetBooleanObjectVariable', D, 'no_lava', 'True', ''),
               I('SetY', D, '=', f'{superficie} + {D}.lava_afunda - {D}.Height()'),
               I('SetZOrder', D, '=', f'{LAVA}.ZOrder() - 1'),
               I('SetNumberObjectVariable', D, 'lava_y', '=', f'{D}.Y()')], [
                # chegou: volta a lutar
                E([vivo, golpe('queda')],
                  [I('SetStringObjectVariable', D, 'golpe', '=', '""'),
                   I('SetStringObjectVariable', D, 'estado', '=', '"perseguir"'),
                   I('ResetObjectTimer', D, '"estado"'), I('ResetObjectTimer', D, '"ataque"'),
                   I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"idle"')],
                  [js(['for (const b of objects) b.resumeAnimation();'])]),
            ]),
        ]),
        # e anda até o pato dentro da lava, sem sair da faixa da arena
        E([I('BooleanObjectVariable', D, 'no_lava', 'True', ''), vivo, estado('perseguir'),
           I('BuiltinCommonInstructions::CompareNumbers', f'abs{dx}', '>', f'{D}.parar_dist')],
          [I('SetX', D, '=', f'clamp({D}.CenterX() + sign{dx} * {D}.velocidade * {D}.ritmo * {D}.lava_vel_fator * TimeDelta(), '
                             f'{x_min} + {D}.lava_borda, {x_max} - {D}.lava_borda) - {D}.Width() / 2')]),
        # na lava o cutelo vira um salto bem avisado. De até lava_ataque_alcance px:
        #   salto   - sobe em lava_subida_t s até lava_pulo_altura acima do ponto do golpe, indo para lava_golpe_dx antes de
        #             onde o pato estava ao pular (o alvo não muda depois), erguendo o cutelo (quadros 0 a lava_quadro_espera);
        #   no alto - fica parado lá em cima lava_espera_t s com o cutelo erguido (com o som de aviso);
        #   pancada - despenca a lava_pancada_vel px/s até o pé ficar lava_golpe_baixo abaixo do pé do pato;
        #   cravado - o cutelo bate (quadro lava_quadro_golpe, faíscas e estrondo) e só machuca nos primeiros
        #             lava_golpe_janela s; fica lava_cravado_t s ali;
        #   volta   - afunda de volta na lava em lava_volta_t s e volta a perseguir.
        E([I('BooleanObjectVariable', D, 'no_lava', 'True', ''), vivo, estado('perseguir'),
           I('CompareObjectTimer', D, '"ataque"', '>', f'{D}.ataque_espera / {D}.ritmo'),
           I('BuiltinCommonInstructions::CompareNumbers', f'abs{dx}', '<', f'{D}.lava_ataque_alcance')],
          [I('SetStringObjectVariable', D, 'estado', '=', '"atacar"'),
           I('ResetObjectTimer', D, '"estado"'),
           I('SetNumberObjectVariable', D, 'direcao', '=', f'sign{dx}'),
           I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"ataque"'),
           I('SetStringObjectVariable', D, 'golpe', '=', '"cutelo"')]),
        E([I('BooleanObjectVariable', D, 'no_lava', 'True', ''), vivo, estado('atacar')], [
            I('SetNumberObjectVariable', D, 'lava_t', '=', f'{D}.ObjectTimerElapsedTime("estado") * {D}.ritmo')], [
            # qualquer cutelo na lava (de perto ou de longe) vira o salto; o alvo é onde o pato está agora
            E([golpe('cutelo')],
              [I('SetStringObjectVariable', D, 'golpe', '=', '"salto"'),
               I('ResetObjectTimer', D, '"estado"'),
               I('SetNumberObjectVariable', D, 'lava_t', '=', '0'),
               I('SetNumberObjectVariable', D, 'direcao', '=', f'sign{dx}'),
               I('SetNumberObjectVariable', D, 'lava_x0', '=', f'{D}.CenterX()'),
               I('SetNumberObjectVariable', D, 'lava_x1', '=', f'clamp(pato.CenterX() - {D}.direcao * {D}.lava_golpe_dx, '
                                                              f'{x_min} + {D}.lava_borda, {x_max} - {D}.lava_borda)'),
               I('SetNumberObjectVariable', D, 'lava_y1', '=', f'min({D}.lava_y, pato.Y() + pato.Height() - {D}.Height() + '
                                                              f'{D}.lava_golpe_baixo)'),
               I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"ataque"')]),
            E([golpe('salto')], [
                I('SetNumberObjectVariable', D, 'lava_u', '=', f'clamp({D}.lava_t / {D}.lava_subida_t, 0, 1)'),
                I('SetX', D, '=', f'{D}.lava_x0 + ({D}.lava_x1 - {D}.lava_x0) * (1 - pow(1 - {D}.lava_u, 2)) - {D}.Width() / 2'),
                I('SetY', D, '=', f'{D}.lava_y + ({D}.lava_y1 - {D}.lava_pulo_altura - {D}.lava_y) * (1 - pow(1 - {D}.lava_u, 2))'),
                I('SetNumberObjectVariable', D, 'lava_quadro', '=',
                  f'min({D}.lava_quadro_espera, floor({D}.lava_u * ({D}.lava_quadro_espera + 1)))')], [
                E([I('BooleanObjectVariable', D, 'lava_avisou', 'False', ''),
                   I('BuiltinCommonInstructions::CompareNumbers', f'{D}.lava_t', '>=', f'{D}.lava_subida_t')],
                  [I('SetBooleanObjectVariable', D, 'lava_avisou', 'True', ''),
                   I('PlaySound', '', 'som_aviso_caveira.wav', '', f'{D}.som_volume', 'RandomFloatInRange(0.75, 0.85)')]),
                E([I('BuiltinCommonInstructions::CompareNumbers', f'{D}.lava_t', '>=', f'{D}.lava_subida_t + {D}.lava_espera_t')],
                  [I('SetStringObjectVariable', D, 'golpe', '=', '"pancada"'),
                   I('SetBooleanObjectVariable', D, 'lava_avisou', 'False', ''),
                   I('ResetObjectTimer', D, '"estado"')]),
            ]),
            E([golpe('pancada')], [
                I('SetY', D, '=', f'min({D}.lava_y1, {D}.Y() + {D}.lava_pancada_vel * {D}.ritmo * TimeDelta())')], [
                E([I('BuiltinCommonInstructions::CompareNumbers', f'{D}.Y()', '>=', f'{D}.lava_y1')],
                  [I('SetStringObjectVariable', D, 'golpe', '=', '"cravado"'),
                   I('ResetObjectTimer', D, '"estado"'),
                   I('SetNumberObjectVariable', D, 'lava_t', '=', '0'),
                   I('SetNumberObjectVariable', D, 'lava_quadro', '=', f'{D}.lava_quadro_golpe'),
                   I('PlaySound', '', 'som_explosao.wav', '', f'{D}.quebra_som_volume', 'RandomFloatInRange(0.8, 0.9)'),
                   I('Create', '', 'explosao_faiscas', f'{D}.CenterX() + {D}.direcao * {D}.lava_golpe_dx',
                     f'{D}.Y() + {D}.Height() - {D}.lava_golpe_baixo', ''),
                   I('Create', '', 'explosao_fumaca', f'{D}.CenterX() + {D}.direcao * {D}.lava_golpe_dx',
                     f'{D}.Y() + {D}.Height() - {D}.lava_golpe_baixo', '')],
                  [js(['// o cutelo bate: solta a animação a partir do quadro do golpe',
                       'for (const b of objects) {',
                       '  b.setAnimationFrame(b.getVariables().get("lava_quadro").getAsNumber());',
                       '  b.resumeAnimation();',
                       '}'])]),
            ]),
            # segura o quadro enquanto sobe, espera e cai
            E([{'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
                golpe('salto'), golpe('pancada')]}], [], [
                js(['for (const b of objects) {',
                    '  b.pauseAnimation();',
                    '  b.setAnimationFrame(b.getVariables().get("lava_quadro").getAsNumber());',
                    '}'])]),
            E([golpe('cravado')], [I('SetY', D, '=', f'{D}.lava_y1')], [
                E([I('BuiltinCommonInstructions::CompareNumbers', f'{D}.lava_t', '<', f'{D}.lava_golpe_janela'),
                   I('BuiltinCommonInstructions::CompareNumbers', f'(pato.CenterX() - {D}.CenterX()) * {D}.direcao', '>', f'{D}.golpe_x_min'),
                   I('BuiltinCommonInstructions::CompareNumbers', f'(pato.CenterX() - {D}.CenterX()) * {D}.direcao', '<', f'{D}.golpe_x_max'),
                   I('BuiltinCommonInstructions::CompareNumbers', 'pato.CenterY()', '>', f'{D}.Y() + {D}.golpe_topo'),
                   I('BuiltinCommonInstructions::CompareNumbers', 'pato.Y()', '<', f'{D}.Y() + {D}.Height()'),
                   I('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
                   I('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
                  [I('SetNumberObjectVariable', 'pato', 'vida', '-', f'{D}.golpe_dano'),
                   I('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
                   I('ResetObjectTimer', 'pato', '"iframes"'),
                   I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', 'pato', 'PlatformerObject', '=',
                     f'{D}.direcao * {D}.golpe_empurrao'),
                   I('PlatformBehavior::SimulateJumpKey', 'pato', 'PlatformerObject'),
                   I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'{D}.ObjectName()')]),
                E([I('BuiltinCommonInstructions::CompareNumbers', f'{D}.lava_t', '>=', f'{D}.lava_cravado_t')],
                  [I('SetStringObjectVariable', D, 'golpe', '=', '"volta"'),
                   I('ResetObjectTimer', D, '"estado"'),
                   I('SetNumberObjectVariable', D, 'lava_t', '=', '0'),
                   I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"idle"')]),
            ]),
            E([golpe('volta')], [
                I('SetY', D, '=', f'{D}.lava_y1 + ({D}.lava_y - {D}.lava_y1) * pow(clamp({D}.lava_t / {D}.lava_volta_t, 0, 1), 2)')], [
                E([I('BuiltinCommonInstructions::CompareNumbers', f'{D}.lava_t', '>=', f'{D}.lava_volta_t')],
                  [I('SetY', D, '=', f'{D}.lava_y'),
                   I('SetStringObjectVariable', D, 'golpe', '=', '""'),
                   I('SetStringObjectVariable', D, 'estado', '=', '"perseguir"'),
                   I('ResetObjectTimer', D, '"estado"'), I('ResetObjectTimer', D, '"ataque"')]),
            ]),
        ]),
        # fora de ataque (ou morto) ele fica no nível da lava, com a animação andando
        E([I('BooleanObjectVariable', D, 'no_lava', 'True', ''),
           {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
               I('StringObjectVariable', D, 'estado', '!=', '"atacar"'), I('BooleanObjectVariable', D, 'morto', 'True', '')]}],
          [I('SetY', D, '=', f'{D}.lava_y')], [
            E([I('BooleanObjectVariable', D, 'morto', 'False', '')], [], [js(['for (const b of objects) b.resumeAnimation();'])])]),
        # o pulo forte da lava valeu (a força é lida no começo do pulo): volta a força normal do pato
        E([I('BooleanObjectVariable', 'pato', 'lava_pulo', 'True', '')],
          [I('SetBooleanObjectVariable', 'pato', 'lava_pulo', 'False', ''),
           I('PlatformBehavior::JumpSpeed', 'pato', 'PlatformerObject', '=', 'pato.pulo_forca_normal')]),
        # a lava queima o pato na fase 2 e o joga para cima com lava.pulo_vel, alto o bastante para voltar às pontes
        E([fase2('True'), I('CollisionNP', 'pato', LAVA, '', '', ''),
           I('BuiltinCommonInstructions::CompareNumbers', 'pato.Y() + pato.Height()', '>', f'{superficie} + {LAVA}.dano_margem'),
           I('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''), I('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
          [I('SetNumberObjectVariable', 'pato', 'vida', '-', f'{LAVA}.dano_fase2'),
           I('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
           I('ResetObjectTimer', 'pato', '"iframes"'),
           I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', '"lava"'),
           I('PlatformBehavior::JumpSpeed', 'pato', 'PlatformerObject', '=', f'{LAVA}.pulo_vel'),
           I('SetBooleanObjectVariable', 'pato', 'lava_pulo', 'True', ''),
           I('PlatformBehavior::SetCanJump', 'pato', 'PlatformerObject'),
           I('PlatformBehavior::SimulateJumpKey', 'pato', 'PlatformerObject')]),
        # sem plataformas móveis enquanto a luta na lava dura
        E([fase2('True'), I('BooleanVariable', 'plataformas_desligadas', 'False', ''),
           I('SceneInstancesCount', '', D, '>', '0'), vivo], plataformas(False)),
        E([I('BooleanVariable', 'plataformas_desligadas', 'True', ''), chefe_fora], plataformas(True)),
        # pedaços do chão voando e caindo
        E([I('SceneInstancesCount', '', DES, '>', '0')], [], [js([
            'const dt = runtimeScene.getTimeManager().getElapsedTime() / 1000;',
            'for (const o of runtimeScene.getObjects("destroco")) {',
            '  const v = o.getVariables();',
            '  const num = (nome) => v.get(nome).getAsNumber();',
            '  const vy = num("vy") + num("gravidade") * dt;',
            '  v.get("vy").setNumber(vy);',
            '  o.setPosition(o.getX() + num("vx") * dt, o.getY() + vy * dt);',
            '  o.setAngle(o.getAngle() + num("va") * dt);',
            '  if (o.getY() > num("fundo_y")) o.deleteFromScene();',
            '}'], '')]),
    ])


# ------------------------------------------------------------------ imagens
def recorta():
    """As pedras soltas do próprio atlas do inferno (recortadas no contorno) viram os pedaços que voam."""
    atlas = Image.open(os.path.join(RAIZ, ATLAS)).convert('RGBA')
    os.makedirs(os.path.join(RAIZ, 'assets', 'destroco'), exist_ok=True)
    for tile, caminho in zip(ROCHAS, IMGS):
        x, y = (tile % COLS_ATLAS) * T, (tile // COLS_ATLAS) * T
        pedra = atlas.crop((x, y, x + T, y + T))
        pedra.crop(pedra.getbbox()).save(os.path.join(RAIZ, caminho))


# ------------------------------------------------------------------ jogo.json
def variaveis(lista, dono, existentes):
    tem = {v['name'] for v in existentes}
    for n, t, v in lista:
        if n not in tem:
            existentes.append({'name': n, 'persistentUuid': uid(dono, n), 'type': t, 'value': v})


def acha_evento_furia(evs):
    for e in evs:
        if any(a['type']['value'] == 'SetBooleanObjectVariable' and a['parameters'][:3] == [D, 'em_furia', 'True']
               for a in e.get('actions', [])):
            return evs, evs.index(e)
        achou = acha_evento_furia(e.get('events', []))
        if achou:
            return achou
    return None


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    for img in IMGS:
        if not any(r['name'] == img for r in recursos):
            recursos.append({'file': img, 'kind': 'image', 'metadata': '', 'name': img, 'smoothed': False, 'userAdded': True})
    if DES not in objs:
        quadro = lambda img: {'hasCustomCollisionMask': False, 'image': img, 'points': [],
                              'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                              'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0}, 'customCollisionMask': []}
        d['objects'].append({
            'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': DES, 'persistentUuid': uid(DES),
            'type': 'Sprite', 'updateIfNotVisible': False, 'variables': [], 'effects': [], 'behaviors': [],
            'animations': [{'name': f'pedaco_{i}', 'useMultipleDirections': False,
                            'directions': [{'looping': False, 'timeBetweenFrames': 0.08, 'sprites': [quadro(img)]}]}
                           for i, img in enumerate(IMGS)]})
        no = d['objectsFolderStructure']
        for nome in ('inimigos', 'chefe'):
            no = next(c for c in no['children'] if c.get('folderName') == nome)
        no['children'].append({'objectName': DES})
        objs[DES] = d['objects'][-1]
    variaveis(VARS_DESTROCO, DES, objs[DES]['variables'])
    variaveis(VARS_CHEFE, D, objs[D]['variables'])
    variaveis(VARS_LAVA, LAVA, objs[LAVA].setdefault('variables', []))
    variaveis(VARS_PATO, 'pato', objs['pato']['variables'])

    cena = next(l for l in d['layouts'] if l['name'] == 'Inferno')
    variaveis(VARS_CENA, 'Inferno', cena['variables'])
    for i, (x, y, w) in enumerate(PONTES):
        if any(p.get('persistentUuid') == uid('ponte', str(i)) for p in cena['instances']):
            continue
        mapa = {'tileWidth': T, 'tileHeight': T, 'dimX': w, 'dimY': 1,
                'layers': [{'id': 0, 'alpha': 1, 'tiles': [[125] + [126] * (w - 2) + [127]]}]}
        cena['instances'].append({'angle': 0, 'customSize': False, 'height': 0, 'keepRatio': True, 'layer': '',
                                  'name': PONTE, 'persistentUuid': uid('ponte', str(i)), 'width': 0, 'x': x, 'y': y,
                                  'zOrder': Z_PONTE, 'numberProperties': [],
                                  'stringProperties': [{'name': 'tilemap', 'value': json.dumps(mapa, separators=(',', ':'))}],
                                  'initialVariables': []})

    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not any(e.get('name') == 'Fase 2' for e in ext['events']):
        lista, k = acha_evento_furia(ext['events'])
        lista.insert(k + 1, eventos_inicio_grande())
        ext['events'].append(eventos())


def main(caminho):
    recorta()
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
