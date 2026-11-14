"""Tarefa 59: demônio chefe do inferno (demonio_chefe), com cutelo, fúria e a barra de chefe do HUD.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - recursos assets/demonio_chefe/*.png (recortados por tools/t58_demonio_chefe_sprites.py);
  - objeto demonio_chefe na pasta inimigos/chefe: cópia dos comportamentos e do efeito Brilho da caveira_gigante,
    animações idle, andando, ataque (golpe de cutelo), tomou_dano e morte; máscara só no corpo (o cutelo não
    encosta: o dano dele é o golpe, abaixo). O desenho olha para a esquerda (sprite_esquerda = True);
  - entra nos grupos Inimigo, Personagem e Terrestre: leva tiro/soco/granada, morre, solta moedas, machuca ao
    encostar e usa os estados comuns dos que andam (patrulha, perseguir, recuo ao levar dano);
  - eventos externos "Chefe", ligados no Inferno depois dos outros:
      * persegue o pato andando (anda até parar_dist dele);
      * a cada ataque_espera s, com o pato a menos de ataque_alcance px na frente e ataque_alt px na altura, dá o
        golpe de cutelo: a animação inteira é o aviso (ergue o cutelo) e só entre golpe_inicio e golpe_fim s o golpe
        machuca (golpe_dano), na frente dele de golpe_x_min a golpe_x_max px do centro e só abaixo de golpe_topo
        px do topo do quadro: pular por cima do cutelo desvia;
      * recuo: os estados comuns fazem o inimigo recuar (empurrão para trás e animação de dano) a cada acerto; o
        chefe só aceita um recuo a cada atordoa_espera s (os outros acertos tiram vida sem empurrar nem
        interromper), senão tiro rápido o deixa travado;
      * fúria: abaixo de furia_abaixo da vida, fica com a cor furia_cor e tudo (passo, animação, espera entre
        golpes) acelera por furia_ritmo;
      * barra de chefe do HUD (hud_boss_*) com o nome dele (nome) quando o pato está a menos de barra_dist px.
    Ele nasce com tem_barra_de_vida = True para não ganhar a barrinha de inimigo comum em cima da cabeça.
Não põe o demônio em nenhuma cena: arraste-o do editor para onde for a arena.
"""
import copy, glob, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = 'demonio_chefe'
MOLDE = 'caveira_gigante'
GRUPOS = ('Inimigo', 'Personagem', 'Terrestre')
# animação -> (laço, tempo entre quadros)
ANIMS = {'idle': (True, 0.1), 'andando': (True, 0.08), 'ataque': (False, 0.08), 'tomou_dano': (False, 0.06),
         'morte': (False, 0.08)}
MASCARA = [[{'x': 300, 'y': 100}, {'x': 450, 'y': 100}, {'x': 450, 'y': 384}, {'x': 300, 'y': 384}]]
VARS = [  # (nome, tipo, valor)
    ('vida', 'number', 2500), ('dano', 'number', 20), ('tem_barra_de_vida', 'boolean', True),
    ('max_vida', 'number', 2500), ('vida_controle', 'number', 0), ('velocidade', 'number', 140),
    ('animacao_temp', 'number', 0), ('morto', 'boolean', False), ('qtd_moedas', 'number', 60),
    ('estado', 'string', 'patrulha'), ('base_x', 'number', 0), ('base_y', 'number', 0), ('direcao', 'number', 1),
    ('escolha', 'number', 1), ('tiros', 'number', 0), ('kb_dir', 'number', 0), ('acertado', 'boolean', False),
    ('quer_andar', 'boolean', False), ('sprite_esquerda', 'boolean', True), ('bala_serie', 'number', 0),
    ('sangue', 'string', 'escuro'), ('socado', 'number', 0), ('soco_dir', 'number', 0),
    ('empurrao_vel', 'number', 40), ('dano_duracao', 'number', 0.15), ('patrulha_fator', 'number', 0.5),
    ('patrulha_raio', 'number', 150), ('aggro_dist', 'number', 1400), ('desiste_dist', 3000),
    ('travado_tempo', 'number', 0.3), ('parar_dist', 'number', 150),
    ('ataque_espera', 'number', 1.8), ('ataque_alcance', 'number', 380), ('ataque_alt', 'number', 300),
    ('golpe_inicio', 'number', 0.72), ('golpe_fim', 'number', 0.96), ('golpe_dano', 'number', 35),
    ('golpe_x_min', 'number', -60), ('golpe_x_max', 'number', 400), ('golpe_topo', 'number', 180),
    ('golpe_empurrao', 'number', 900), ('som_volume', 'number', 70),
    ('furia_abaixo', 'number', 0.5), ('furia_ritmo', 'number', 1.4), ('furia_cor', 'string', '255;130;110'),
    ('em_furia', 'boolean', False), ('ritmo', 'number', 1),
    ('atordoa_espera', 'number', 2), ('atordoado', 'boolean', False),
    ('nome', 'string', 'DEMÔNIO DO CUTELO'), ('barra_dist', 'number', 1500), ('barra_largura', 'number', 720),
    ('barra_rastro_vel', 'number', 300),
]
VARS = [v if len(v) == 3 else (v[0], 'number', v[1]) for v in VARS]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t59/' + '/'.join(p)))


def quadros(anim):
    return sorted(os.path.relpath(f, RAIZ) for f in glob.glob(os.path.join(RAIZ, 'assets', D, anim + '_[0-9][0-9].png')))


def I(tipo, *params, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(params)}


def E(conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def grupo(nome, eventos):
    return {'colorB': 60, 'colorG': 60, 'colorR': 200, 'creationTime': 0, 'name': nome, 'source': '',
            'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': eventos}


def eventos():
    num = lambda v, op, x: I('SetNumberObjectVariable', D, v, op, x)
    estado = lambda op, s: I('StringObjectVariable', D, 'estado', op, f'"{s}"')
    vai = lambda s: I('SetStringObjectVariable', D, 'estado', '=', f'"{s}"')
    anim = lambda s: I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', f'"{s}"')
    cmp = lambda a, op, b: I('BuiltinCommonInstructions::CompareNumbers', a, op, b)
    dx = f'(pato.CenterX() - {D}.CenterX())'
    vivo = I('BooleanObjectVariable', D, 'morto', 'False', '')
    pato_ok = [I('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
               I('BooleanObjectVariable', 'pato', 'morto', 'False', '')]
    andar = lambda tecla, op: E([cmp(dx, op, '0')], [I(tecla, D, 'PlatformerObject'),
                                                     I('SetBooleanObjectVariable', D, 'quer_andar', 'True', '')])
    hud = ['hud_boss_trilho', 'hud_boss_rastro', 'hud_boss_fill', 'hud_boss_nome']
    return [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Chefe do inferno: demonio_chefe. Os estados comuns (patrulha, perseguir, recuo) vêm de Inimigos > '
                    'Estados (terrestres); aqui ficam o passo, o golpe de cutelo, a fúria e a barra de chefe. Fica depois '
                    'de Inimigos e HUD na cena porque sobrescreve a velocidade e mostra a barra que o HUD esconde.'},
        grupo('Demônio chefe', [
            E([I('SceneJustBegins', '')], [I('ResetObjectTimer', D, '"atordoado"')]),
            E([vivo], [I('AnimatableCapability::AnimatableBehavior::SetSpeedScale', D, 'Animation', '=', f'{D}.ritmo')], [
                # sem travar: cada acerto marca "acertado" e um empurrão (kb_dir, socado); no quadro seguinte os estados
                # comuns (Inimigos) o jogam para trás e trocam a animação. O chefe só aceita isso uma vez a cada
                # atordoa_espera s: os outros acertos tiram vida, mas a marca e o empurrão são apagados aqui (depois de
                # Combate) antes de Inimigos ver. O soco marca antes de Inimigos; esse recuo é desfeito logo abaixo.
                # atordoado = "este acerto pode passar" (vale só neste quadro); o cronômetro "atordoado" conta desde o
                # último recuo aceito. Durante um recuo aceito os novos acertos também são apagados, para não esticá-lo.
                E([], [I('SetBooleanObjectVariable', D, 'atordoado', 'False', '')]),
                E([I('BooleanObjectVariable', D, 'acertado', 'True', ''),
                   I('CompareObjectTimer', D, '"atordoado"', '>', f'{D}.atordoa_espera')],
                  [I('SetBooleanObjectVariable', D, 'atordoado', 'True', ''), I('ResetObjectTimer', D, '"atordoado"')]),
                E([estado('=', 'dano'), I('CompareObjectTimer', D, '"atordoado"', '>', f'{D}.atordoa_espera')],
                  [I('ResetObjectTimer', D, '"atordoado"')]),
                E([I('BooleanObjectVariable', D, 'acertado', 'True', ''), I('BooleanObjectVariable', D, 'atordoado', 'False', '')],
                  [I('SetBooleanObjectVariable', D, 'acertado', 'False', ''), num('kb_dir', '=', '0'), num('socado', '=', '0')]),
                E([estado('=', 'dano'), I('CompareObjectTimer', D, '"atordoado"', '>', f'{D}.dano_duracao')],
                  [vai('perseguir'), I('ResetObjectTimer', D, '"estado"'), num('socado', '=', '0'),
                   I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', D, 'PlatformerObject', '=', '0')]),
                # fúria
                E([I('BooleanObjectVariable', D, 'em_furia', 'False', ''),
                   I('NumberObjectVariable', D, 'vida', '<=', f'{D}.max_vida * {D}.furia_abaixo')],
                  [I('SetBooleanObjectVariable', D, 'em_furia', 'True', ''), num('ritmo', '=', f'{D}.furia_ritmo')]),
                E([I('BooleanObjectVariable', D, 'em_furia', 'True', '')], [I('ChangeColor', D, f'{D}.furia_cor')]),
                # andar até o pato
                E([estado('=', 'patrulha')], [anim('andando')]),
                E([estado('=', 'perseguir')],
                  [I('PlatformBehavior::MaxSpeed', D, 'PlatformerObject', '=', f'{D}.velocidade * {D}.ritmo')], [
                    # uma animação só por quadro: trocar idle -> andando todo quadro reinicia a animação no quadro 0
                    E([cmp(f'abs{dx}', '<=', f'{D}.parar_dist')], [anim('idle')]),
                    E([cmp(f'abs{dx}', '>', f'{D}.parar_dist')], [anim('andando')], [
                        andar('PlatformBehavior::SimulateLeftKey', '<'),
                        andar('PlatformBehavior::SimulateRightKey', '>'),
                    ]),
                ]),
                # golpe de cutelo: começa
                E([estado('=', 'perseguir'),
                   I('CompareObjectTimer', D, '"ataque"', '>', f'{D}.ataque_espera / {D}.ritmo'),
                   cmp(f'abs{dx}', '<', f'{D}.ataque_alcance'),
                   cmp(f'abs(pato.CenterY() - {D}.CenterY())', '<', f'{D}.ataque_alt')],
                  [vai('atacar'), I('ResetObjectTimer', D, '"estado"'), num('direcao', '=', f'sign{dx}'), anim('ataque'),
                   I('PlaySound', '', 'som_aviso_caveira.wav', '', f'{D}.som_volume', 'RandomFloatInRange(0.75, 0.85)')]),
                # golpe de cutelo: machuca só no instante em que desce, na frente e embaixo
                E([estado('=', 'atacar'),
                   I('CompareObjectTimer', D, '"estado"', '>', f'{D}.golpe_inicio / {D}.ritmo'),
                   I('CompareObjectTimer', D, '"estado"', '<', f'{D}.golpe_fim / {D}.ritmo'),
                   cmp(f'{dx} * {D}.direcao', '>', f'{D}.golpe_x_min'),
                   cmp(f'{dx} * {D}.direcao', '<', f'{D}.golpe_x_max'),
                   cmp('pato.CenterY()', '>', f'{D}.Y() + {D}.golpe_topo'),
                   cmp('pato.Y()', '<', f'{D}.Y() + {D}.Height()')] + pato_ok,
                  [I('SetNumberObjectVariable', 'pato', 'vida', '-', f'{D}.golpe_dano'),
                   I('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
                   I('ResetObjectTimer', 'pato', '"iframes"'),
                   I('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', 'pato', 'PlatformerObject', '=',
                     f'{D}.direcao * {D}.golpe_empurrao'),
                   I('PlatformBehavior::SimulateJumpKey', 'pato', 'PlatformerObject'),
                   I('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'{D}.ObjectName()')]),
                # golpe de cutelo: termina com a animação
                E([estado('=', 'atacar'), I('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', D, 'Animation')],
                  [vai('perseguir'), I('ResetObjectTimer', D, '"estado"'), I('ResetObjectTimer', D, '"ataque"'), anim('idle')]),
            ]),
        ]),
        grupo('Barra do chefe', [
            E([I('Distance', 'pato', D, f'{D}.barra_dist', ''), vivo],
              [I('Show', h, '') for h in hud] + [
                  I('ResizableCapability::ResizableBehavior::SetWidth', 'hud_boss_fill', 'Resizable', '=',
                    f'{D}.barra_largura * clamp({D}.vida / {D}.max_vida, 0, 1)'),
                  I('TextContainerCapability::TextContainerBehavior::SetValue', 'hud_boss_nome', 'Text', '=', f'{D}.nome'),
                  I('SetXY', 'hud_boss_fill', '=', 'hud_boss_trilho.X()', '=', 'hud_boss_trilho.Y()'),
                  I('SetXY', 'hud_boss_rastro', '=', 'hud_boss_trilho.X()', '=', 'hud_boss_trilho.Y()'),
                  I('SetXY', 'hud_boss_nome', '=', f'hud_boss_trilho.X() + {D}.barra_largura / 2 - hud_boss_nome.Width() / 2',
                    '=', 'hud_boss_trilho.Y() - 30')], [
                E([cmp('hud_boss_rastro.Width()', '>', 'hud_boss_fill.Width()')],
                  [I('ResizableCapability::ResizableBehavior::SetWidth', 'hud_boss_rastro', 'Resizable', '-',
                     f'{D}.barra_rastro_vel * TimeDelta()')]),
                E([cmp('hud_boss_rastro.Width()', '<', 'hud_boss_fill.Width()')],
                  [I('ResizableCapability::ResizableBehavior::SetWidth', 'hud_boss_rastro', 'Resizable', '=',
                     'hud_boss_fill.Width()')]),
            ]),
        ]),
    ]


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    recursos = d['resources']['resources']
    tem = {r['name'] for r in recursos}
    for anim in ANIMS:
        for f in quadros(anim):
            if f not in tem:
                recursos.append({'file': f, 'kind': 'image', 'metadata': '', 'name': f, 'smoothed': False, 'userAdded': True})
                tem.add(f)

    if D not in objs:
        molde = objs[MOLDE]
        s0 = molde['animations'][0]['directions'][0]['sprites'][0]
        anims = []
        for anim, (laco, tempo) in ANIMS.items():
            arqs = quadros(anim)
            assert arqs, f'sem quadros para {anim}: rode tools/t58_demonio_chefe_sprites.py'
            sprites = []
            for f in arqs:
                s = copy.deepcopy(s0)
                s.update(image=f, points=[], hasCustomCollisionMask=True, customCollisionMask=MASCARA)
                sprites.append(s)
            anims.append({'name': anim, 'useMultipleDirections': False,
                          'directions': [{'looping': laco, 'timeBetweenFrames': tempo, 'sprites': sprites}]})
        o = {k: copy.deepcopy(v) for k, v in molde.items() if k not in ('animations', 'variables')}
        o.update(name=D, persistentUuid=uid(D), animations=anims,
                 variables=[{'name': n, 'persistentUuid': uid(D, n), 'type': t, 'value': v} for n, t, v in VARS])
        d['objects'].append(o)

        no = d['objectsFolderStructure']
        for nome in ('inimigos', 'chefe'):
            prox = next((c for c in no.setdefault('children', []) if c.get('folderName') == nome), None)
            if prox is None:
                prox = {'folderName': nome, 'children': []}
                no['children'].append(prox)
            no = prox
        no['children'].append({'objectName': D})

    for g in d['objectsGroups']:
        if g['name'] in GRUPOS and not any(x['name'] == D for x in g['objects']):
            g['objects'].append({'name': D})

    if not any(x['name'] == 'Chefe' for x in d['externalEvents']):
        d['externalEvents'].append({'associatedLayout': 'Inferno', 'name': 'Chefe', 'events': eventos()})
    cena = next((l for l in d['layouts'] if l['name'] == 'Inferno'), None)
    if cena is not None and not any(e['type'].endswith('::Link') and e.get('target') == 'Chefe' for e in cena['events']):
        cena['events'].append({'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 0}, 'target': 'Chefe'})


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
