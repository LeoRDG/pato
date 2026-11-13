"""Tarefa 34: soco no botão direito (na direção da mira, com rastro) e coice ao socar o terreno.

SOCO (botão direito, espera de COOLDOWN s): uma luva sai do pato NA DIREÇÃO DA MIRA (qualquer ângulo, do centro do pato até o
  mouse) e volta (objeto `soco`, 0,16 s), com um rastro em arco na ponta (objeto `soco_rastro`, 4 quadros).
  Todo inimigo vivo nessa direção, até ALCANCE px e a menos de LARGURA px da linha do soco, leva SOCO_DANO (× mult_dano) e é
  jogado para longe: os terrestres ganham um empurrão de SOCO_VEL px/s enquanto estão no estado "dano" (0,2 s; quem está
  avisando ou atacando leva o dano mas não é empurrado, como com as balas); os voadores são deslocados (kb_dir × 40 px).

SOCO NO TERRENO: se o soco bate no Terreno (raio do centro do pato na direção do soco, até ALCANCE_PAREDE px), o pato ganha
  velocidade na direção CONTRÁRIA à do soco, e só isso: as teclas continuam mandando normalmente.
  - para o lado: velocidade atual − cos × IMPULSO_X (até a velocidade máxima do pato); depois o pato anda e freia como sempre;
  - na vertical (|sin| > LIMIAR_Y): a velocidade vertical vira −sin × IMPULSO_Y, SEM usar o pulo. O comportamento de plataforma
    não tem ação para "velocidade para cima", então um evento JavaScript põe o pato no estado de queda e escreve a velocidade
    de queda direto (negativa = subindo); a gravidade normal faz o resto, numa parábola de verdade. Só vale se o coice for
    mais forte que o movimento que o pato já tem naquele sentido; para baixo o limite é a queda máxima do pato.
  Os eventos antigos de gravidade extra na queda e de corte ao soltar Espaço só valem com a velocidade de queda >= 0
  (a ação deles não aceita valor negativo e zeraria a subida).
  Ao bater a cabeça no teto subindo assim, a velocidade é zerada (senão o pato ficaria colado até a gravidade vencer).
  A força do coice fica nas variáveis do objeto pato, `coice_x` e `coice_y` (px/s), editáveis no GDevelop; o script só as
  cria se não existirem, nunca troca o valor.
  O coice NÃO gasta pulo: saindo do chão, o pulo do chão fica guardado (o "coyote time" do AdvancedJump, que acabaria em
  0,2 s, é mantido reiniciando o cronômetro dele) até o pato pular ou pousar; o pulo no ar continua valendo depois.
  Não funciona durante o dash. (Agarrar na parede saiu: fica para depois.)

O script não roda se jogo.json.autosave for mais novo que jogo.json (mudanças não salvas no GDevelop seriam perdidas).
Sons: som_soco.wav (golpe no ar) e som_soco_acerto.wav (acertou inimigo ou terreno), receitas em t31_sons_jogo.py.
Rodar:  python3 tools/t31_sons_jogo.py && python3 tools/t32_sons_eventos.py && python3 tools/t34_soco_parede.py
        (pode rodar de novo). Salve e feche o projeto no GDevelop antes.
"""
import json, math, os, sys, uuid
from PIL import Image
from t12_armas import A, C, E, PATH, comentario, grupo, upsert

ROOT = os.path.dirname(PATH)
NOME = 'Soco'
VELHOS = ('Soco e paredes',)   # nome do grupo nas versões anteriores
PL = ('pato', 'PlatformerObject')
COOLDOWN = 0.35
ALCANCE = 150      # px a partir do centro do pato, na direção do soco
LARGURA = 60       # px para cada lado da linha do soco (mais o raio do inimigo)
SOCO_DANO = 12
SOCO_VEL = 900     # px/s do empurrão nos terrestres
SOCO_KB = 4        # kb_dir dos voadores (× 40 px)
DUR = 0.16         # s da luva na tela
ALCANCE_PAREDE = 150   # px do centro do pato até onde o soco alcança o terreno
IMPULSO_X = 700    # valor inicial de pato.coice_x: px/s para o lado, contra a direção do soco
IMPULSO_Y = 1000   # valor inicial de pato.coice_y: px/s para cima ou para baixo, × o quanto o soco aponta na vertical (1000 para cima = 250 px de altura)
LIMIAR_Y = 0.2     # o soco precisa apontar pelo menos isso (seno) para cima/baixo para dar impulso vertical
ESCALA = 5
RASTRO_DIST = 120  # px do centro do pato até o centro do rastro

LUVA = """
.....oooooo....
...ooRRRRRRoo..
.oooRRRrrrrrro.
owwoRRrrrrrrrro
owwoRrrrrrrrrro
owsorrrrrrrrrro
owsorrrrrorrrdo
owsorrrroorrddo
.ooodrrrrrrddo.
...oodddddddo..
.....ooooooo...
""".strip().split('\n')
CORES = {'.': (0, 0, 0, 0), 'o': (51, 26, 0, 255), 'R': (238, 96, 70, 255), 'r': (205, 48, 38, 255), 'd': (140, 24, 28, 255),
         'w': (250, 240, 215, 255), 's': (200, 185, 155, 255)}

vivo = lambda: C('BooleanObjectVariable', 'pato', 'morto', 'False', '')
no_chao = lambda inv=False: C('PlatformBehavior::IsOnFloor', *PL, inv=inv)
dash = lambda inv=False: C('AdvancedJump::HorizontalDash::IsDashing', 'pato', 'HorizontalDash', '', inv=inv)
num = lambda v, op, val: C('NumberObjectVariable', 'pato', v, op, str(val))
flag = lambda v, val: C('BooleanObjectVariable', 'pato', v, 'True' if val else 'False', '')
setn = lambda v, val, op='=': A('SetNumberObjectVariable', 'pato', v, op, str(val))
setb = lambda v, val: A('SetBooleanObjectVariable', 'pato', v, 'True' if val else 'False', '')
som = lambda arq, vol, tom='1': A('PlaySound', '', arq, '', str(vol), tom)
FE = 'BuiltinCommonInstructions::ForEach'


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def desenha_luva():
    im = Image.new('RGBA', (len(LUVA[0]), len(LUVA)))
    for y, linha in enumerate(LUVA):
        for x, c in enumerate(linha):
            im.putpixel((x, y), CORES[c])
    im.save(os.path.join(ROOT, 'assets', 'soco_luva.png'))
    return im.size


# Rastro do soco: uma lua (círculo de fora menos um círculo deslocado para trás), virada para a direita, que aparece de cima
# para baixo e afina. Cada quadro: (ângulo inicial, ângulo final, recuo do círculo de dentro, opacidade).
RASTRO_TAM = (18, 34)
RASTRO_QUADROS = [(-78, -5, 5.0, 255), (-78, 78, 5.0, 255), (-35, 78, 3.4, 215), (15, 78, 2.2, 140)]
RASTRO_TEMPO = 0.04


def desenha_rastro():
    larg, alt = RASTRO_TAM
    cx, cy, r = -2.0, alt / 2, 18.0
    nomes = []
    for k, (a0, a1, recuo, alfa) in enumerate(RASTRO_QUADROS, 1):
        im = Image.new('RGBA', RASTRO_TAM)
        for y in range(alt):
            for x in range(larg):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                fora = math.hypot(dx, dy)
                dentro = math.hypot(dx + recuo, dy)
                if fora <= r and dentro > r + recuo * 0.3 and a0 <= math.degrees(math.atan2(dy, dx)) <= a1:
                    borda = fora > r - 1.2                      # a beira da frente é branca, o miolo é creme
                    im.putpixel((x, y), (255, 255, 255, alfa) if borda else (255, 232, 160, int(alfa * 0.85)))
        nomes.append(f'soco_rastro_{k}.png')
        im.save(os.path.join(ROOT, 'assets', nomes[-1]))
    return nomes


def objeto_sprite(d, nome, imagens, larg, alt, tempo, variaveis):
    """Sprite na pasta do jogador, sem colisão de verdade (o acerto é calculado nos eventos)."""
    objs = d['objects']
    velho = next((o for o in objs if o['name'] == nome), None)
    o = velho or {'adaptCollisionMaskAutomatically': False, 'assetStoreId': '', 'name': nome, 'persistentUuid': str(uuid.uuid4()),
                  'type': 'Sprite', 'updateIfNotVisible': False, 'variables': [], 'effects': [], 'behaviors': []}
    o['animations'] = [{'name': nome, 'useMultipleDirections': False, 'directions': [{'looping': False, 'timeBetweenFrames': tempo, 'sprites': [{
        'hasCustomCollisionMask': True, 'image': img, 'points': [], 'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
        'centerPoint': {'automatic': True, 'name': 'centre', 'x': 0, 'y': 0},
        'customCollisionMask': [[{'x': 0, 'y': 0}, {'x': larg, 'y': 0}, {'x': larg, 'y': alt}, {'x': 0, 'y': alt}]]} for img in imagens]}]}]
    o['variables'] = [v for v in o['variables'] if v['name'] in variaveis]
    for v in variaveis:
        upsert(o['variables'], v, 0)
    if not velho:
        objs.append(o)
        def pasta(n):
            for c in n.get('children', []):
                if c.get('objectName') == 'pato':
                    return n
                if 'children' in c:
                    r = pasta(c)
                    if r:
                        return r
        pasta(d['objectsFolderStructure'])['children'].append({'objectName': nome})
    res = d['resources']['resources']
    res[:] = [r for r in res if r['name'] not in imagens] + [
        {'file': f'assets/{img}', 'kind': 'image', 'metadata': '', 'name': img, 'smoothed': False, 'userAdded': True} for img in imagens]


def destrava_teclas(jog):
    """Tira a condição pato.voo = 0 que a versão anterior (voo travado) punha nos eventos de A, D e Espaço."""
    for e in walk(jog['events']):
        if e.get('name') not in (NOME,) + VELHOS and e.get('conditions'):
            e['conditions'] = [c for c in e['conditions'] if c['parameters'][:4] != ['pato', 'voo', '=', '0']]


def poupa_subida(jog):
    """Os eventos antigos que mexem na velocidade de queda (gravidade extra na queda, corte ao soltar Espaço) usam uma ação
    que não aceita valor negativo: zerariam a subida do coice. Passam a valer só com a velocidade de queda >= 0."""
    FALL = 'pato.PlatformerObject::CurrentFallSpeed()'
    for e in walk(jog['events']):
        if e.get('name') in (NOME,) + VELHOS:
            continue
        for sub in e.get('events') or []:
            if sub.get('name') in (NOME,) + VELHOS:
                continue
            if any(a['type']['value'].endswith('SetCurrentFallSpeed') and a['parameters'][0] == 'pato' and FALL in a['parameters'][3]
                   for a in sub.get('actions', [])) and not any(c['parameters'][:3] == [FALL, '>=', '0'] for c in sub['conditions']):
                sub['conditions'].append(C('BuiltinCommonInstructions::CompareNumbers', FALL, '>=', '0'))


def eventos():
    CX, CY = 'pato.CenterX()', 'pato.CenterY()'
    FALL = 'pato.PlatformerObject::CurrentFallSpeed()'
    cmp = lambda a, op, b: C('BuiltinCommonInstructions::CompareNumbers', a, op, str(b))
    DXI, DYI = f'(Inimigo.CenterX() - {CX})', f'(Inimigo.CenterY() - {CY})'
    AO_LONGO = f'(pato.soco_cos * {DXI} + pato.soco_sin * {DYI})'       # distância do inimigo ao longo da direção do soco
    DE_LADO = f'abs(pato.soco_cos * {DYI} - pato.soco_sin * {DXI})'     # distância do inimigo até a linha do soco
    RAIO_I = '((Inimigo.Width() + Inimigo.Height()) / 4)'
    DIST = f'(35 + 95 * sin(ToRad(180 * min(1, soco.ObjectTimerElapsedTime("t") / {DUR}))))'

    inicio = E([C('SceneJustBegins', '')], [A('ResetObjectTimer', 'pato', '"soco"'), setn('y_antes', 'pato.Y()')])

    teto = [
        comentario('Subindo com o coice do soco (velocidade de queda negativa) e sem conseguir subir: bateu no teto, a velocidade é zerada.'),
        E([cmp(FALL, '<', 0), cmp('pato.Y()', '>=', 'pato.y_antes - 0.01')],
          [A('PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed', *PL, '=', '0')]),
    ]

    # Velocidade vertical sem o pulo: escreve a velocidade de queda direto no comportamento (negativa = para cima).
    js_vertical = {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': [
        'const pato = runtimeScene.getObjects("pato")[0];',
        'const b = pato && pato.getBehavior("PlatformerObject");',
        'if (b && b._setFalling && b._falling) {',
        '  const alvo = pato.getVariables().get("soco_vy").getAsNumber();   // px/s, negativo = para cima',
        '  const noChao = b._state === b._onFloor;',
        '  const agora = b._state === b._falling ? b._currentFallSpeed',
        '    : b._state === b._jumping ? b._currentFallSpeed - b._jumping.getCurrentJumpSpeed() : 0;',
        '  if ((alvo < 0 && alvo < agora) || (alvo > 0 && alvo > agora && !noChao)) {',
        '    const podiaPular = b._canJump;',
        '    if (b._state !== b._falling) b._setFalling();',
        '    b._canJump = podiaPular;',
        '    b._currentFallSpeed = alvo;   // para baixo, o comportamento limita na queda máxima',
        '  }',
        '}'], 'parameterObjects': '', 'useStrict': True, 'eventsSheetExpanded': False}

    # O soco bateu no terreno (raio do centro do pato, na direção do soco): o pato ganha velocidade na direção contrária.
    # Só isso: as teclas continuam mandando normalmente.
    soco_parede = E(
        [dash(inv=True), C('RaycastToPosition', 'Terreno', CX, CY, f'{CX} + pato.soco_cos * {ALCANCE_PAREDE}',
                           f'{CY} + pato.soco_sin * {ALCANCE_PAREDE}', 'soco_rx', 'soco_ry', '')],
        [setb('soco_acertou', True),
         A('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', *PL, '=',
           f'clamp(pato.PlatformerObject::CurrentSpeed() - pato.soco_cos * pato.coice_x, -pato.PlatformerObject::MaxSpeed(), pato.PlatformerObject::MaxSpeed())'),
         A('Create', '', 'poeira', 'soco_rx', 'soco_ry', ''), A('SetAngle', 'poeira', '=', 'pato.soco_ang')],
        [E([cmp('abs(pato.soco_sin)', '>', LIMIAR_Y)], [setn('soco_vy', '-pato.soco_sin * pato.coice_y')], [E([no_chao()], [setb('coice_guarda', True)]), js_vertical])])

    luva = E([], [
        A('Create', '', 'soco', CX, CY, ''),
        A('SetNumberObjectVariable', 'soco', 'ang', '=', 'pato.soco_ang'),
        A('ScalableCapability::ScalableBehavior::SetValue', 'soco', 'Scale', '=', str(ESCALA)),
        A('SetAngle', 'soco', '=', 'pato.soco_ang'),
        A('ResetObjectTimer', 'soco', '"t"'),
        A('Create', '', 'soco_rastro', CX, CY, ''),
        A('SetNumberObjectVariable', 'soco_rastro', 'ang', '=', 'pato.soco_ang'),
        A('ScalableCapability::ScalableBehavior::SetValue', 'soco_rastro', 'Scale', '=', str(ESCALA)),
        A('SetAngle', 'soco_rastro', '=', 'pato.soco_ang'),
        A('ResetObjectTimer', 'soco_rastro', '"t"'),
        som('som_soco.wav', 55, 'RandomFloatInRange(0.93, 1.07)'),
    ], [E([num('soco_cos', '<', 0)], [A('FlippableCapability::FlippableBehavior::FlipY', 'soco', 'Flippable', 'yes'),     # para a esquerda:
                                      A('FlippableCapability::FlippableBehavior::FlipY', 'soco_rastro', 'Flippable', 'yes')])])  # não fica de ponta-cabeça

    acerto = E([C('BooleanObjectVariable', 'Inimigo', 'morto', 'False', ''),
                cmp(f'{AO_LONGO} + {RAIO_I}', '>', 0),
                cmp(f'{AO_LONGO} - {RAIO_I}', '<', ALCANCE),
                cmp(DE_LADO, '<', f'{RAIO_I} + {LARGURA}')],
               [A('SetNumberObjectVariable', 'Inimigo', 'vida', '-', f'max(1, round({SOCO_DANO} * GlobalVariable(mult_dano)))'),
                A('SetBooleanObjectVariable', 'Inimigo', 'acertado', 'True', ''),
                A('SetNumberObjectVariable', 'Inimigo', 'kb_dir', '=', f'pato.soco_lado * {SOCO_KB}'),
                A('SetNumberObjectVariable', 'Inimigo', 'soco_dir', '=', 'pato.soco_lado'),
                A('SetNumberObjectVariable', 'Inimigo', 'socado', '=', '0.2'),
                setb('soco_acertou', True)],
               tipo=FE, object='Inimigo')

    soco = [
        comentario(f'Soco no botão direito (espera de {COOLDOWN} s): a luva sai na direção da mira (do centro do pato até o mouse). Se o soco bate no '
                   f'terreno (até {ALCANCE_PAREDE} px), o pato ganha velocidade na direção contrária. Depois acerta os inimigos na direção do soco.'),
        E([C('MouseButtonFromTextPressed', '', '"Right"'), flag('rmb_antes', False), vivo(),
           C('CompareObjectTimer', 'pato', '"soco"', '>', str(COOLDOWN))],
          [A('ResetObjectTimer', 'pato', '"soco"'), setn('soco_lado', f'sign(MouseX() - {CX} + 0.001)'),
           setn('soco_ang', f'ToDeg(atan2(MouseY() - {CY}, MouseX() - {CX}))'),
           setn('soco_cos', 'cos(ToRad(pato.soco_ang))'), setn('soco_sin', 'sin(ToRad(pato.soco_ang))'), setb('soco_acertou', False)],
          [soco_parede, luva, acerto,
           E([flag('soco_acertou', True)], [som('som_soco_acerto.wav', 65, 'RandomFloatInRange(0.93, 1.07)')])]),
        E([C('MouseButtonFromTextPressed', '', '"Right"')], [setb('rmb_antes', True)]),
        E([C('MouseButtonFromTextPressed', '', '"Right"', inv=True)], [setb('rmb_antes', False)]),
    ]

    depois = [
        comentario('Luva: vai e volta (seno) na direção do soco, com o rastro em arco logo à frente; os dois acompanham o pato e somem. '
                   'Empurrão do soco nos terrestres enquanto estão no estado "dano".'),
        E([], [A('SetXY', 'soco', '=', f'{CX} + {DIST} * cos(ToRad(soco.ang)) - soco.Width() / 2',
                 '=', f'{CY} + 8 + {DIST} * sin(ToRad(soco.ang)) - soco.Height() / 2'),
               A('SetZOrder', 'soco', '=', 'pato.ZOrder() + 2')]),
        E([], [A('SetXY', 'soco_rastro', '=', f'{CX} + {RASTRO_DIST} * cos(ToRad(soco_rastro.ang)) - soco_rastro.Width() / 2',
                 '=', f'{CY} + 8 + {RASTRO_DIST} * sin(ToRad(soco_rastro.ang)) - soco_rastro.Height() / 2'),
               A('SetZOrder', 'soco_rastro', '=', 'pato.ZOrder() + 1')]),
        E([C('CompareObjectTimer', 'soco', '"t"', '>', str(DUR))], [A('Delete', 'soco', '')]),
        E([C('CompareObjectTimer', 'soco_rastro', '"t"', '>', str(RASTRO_TEMPO * len(RASTRO_QUADROS)))], [A('Delete', 'soco_rastro', '')]),
        E([C('NumberObjectVariable', 'Terrestre', 'socado', '>', '0')], [A('SetNumberObjectVariable', 'Terrestre', 'socado', '-', 'TimeDelta()')],
          [E([C('StringObjectVariable', 'Terrestre', 'estado', '=', '"dano"'), C('BooleanObjectVariable', 'Terrestre', 'morto', 'False', '')],
             [A('PlatformBehavior::MaxSpeed', 'Terrestre', 'PlatformerObject', '=', str(SOCO_VEL)),
              A('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', 'Terrestre', 'PlatformerObject', '=', f'Terrestre.soco_dir * {SOCO_VEL}')])]),
        E([flag('coice_guarda', True), C('PlatformBehavior::IsFalling', *PL)],
          [A('ResetObjectTimer', 'pato', '"__CoyoteTime_CoyoteJump"')]),
        E([flag('coice_guarda', True), C('PlatformBehavior::IsFalling', *PL, inv=True)], [setb('coice_guarda', False)]),
        E([], [setn('y_antes', 'pato.Y()')]),
    ]
    return grupo(NOME, [inicio] + teto + soco + depois)


def main():
    auto = PATH + '.autosave'
    if os.path.exists(auto) and os.path.getmtime(auto) > os.path.getmtime(PATH) and '--mesmo-assim' not in sys.argv:
        raise SystemExit('jogo.json.autosave é mais novo que jogo.json: há mudanças não salvas no GDevelop. Salve e feche o projeto lá antes '
                         '(ou rode com --mesmo-assim se o autosave for lixo).')
    d = json.load(open(PATH, encoding='utf-8'))
    larg, alt = desenha_luva()
    objeto_sprite(d, 'soco', ['soco_luva.png'], larg, alt, 0.08, ['ang'])
    objeto_sprite(d, 'soco_rastro', desenha_rastro(), *RASTRO_TAM, RASTRO_TEMPO, ['ang'])
    obj = {o['name']: o for o in d['objects']}
    pv = obj['pato']['variables']
    velhas = ('impulso', 'soco_f', 'sustento_restaurar', 'parede_lado', 'vel_base', 'sustento_base', 'queda_base', 'parede_agora',
              'pulo_base', 'agarrado', 'pulo_restaurar', 'voo', 'voo_dir', 'voo_f', 'voo_q', 'voo_pulou', 'voo_fim')   # das versões anteriores
    pv[:] = [v for v in pv if v['name'] not in velhas]
    for k in ('soco_lado', 'soco_ang', 'soco_cos', 'soco_sin', 'soco_vy', 'y_antes'):
        upsert(pv, k, 0)
    for k, v in (('coice_x', IMPULSO_X), ('coice_y', IMPULSO_Y)):   # força do coice: ajustável no GDevelop, o script não sobrescreve
        if not any(x['name'] == k for x in pv):
            upsert(pv, k, v)
    for k in ('rmb_antes', 'soco_acertou', 'coice_guarda'):
        upsert(pv, k, False)
    for g in d['objectsGroups']:
        if g['name'] == 'Inimigo':
            for m in g['objects']:
                upsert(obj[m['name']]['variables'], 'socado', 0)
                upsert(obj[m['name']]['variables'], 'soco_dir', 0)
    for lay in d['layouts']:
        if lay['name'] in ('Hub', 'Inferno'):   # resultado do raio (como laser_x/laser_y)
            upsert(lay['variables'], 'soco_rx', 0)
            upsert(lay['variables'], 'soco_ry', 0)

    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    ctrl = next(e for e in walk(jog['events']) if e.get('name') == 'Controle do Pato')
    ctrl['events'] = [e for e in ctrl['events'] if e.get('name') not in (NOME,) + VELHOS]
    destrava_teclas(jog)
    poupa_subida(jog)
    ctrl['events'].append(eventos())

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
