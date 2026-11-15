"""Tarefa 71: os eventos do Chefe sem blocos de JavaScript, só eventos e ações do GDevelop.

Migração de uso único: troca cada bloco JsCode dos eventos externos "Chefe" (criados pelas tarefas 62, 63, 68, 69 e
70) por eventos com o mesmo efeito. Nenhuma variável muda de valor; só entram variáveis novas (de trabalho, mais
destroco.pedacos e demonio_chefe.quebra_tentativas). Cada bloco é achado pelo conteúdo:
  - fumaça da fúria: tanque infinito, fluxo e raio -> ParticleSystem::SetTank / SetFlow / ZoneRadius; parar ->
    ParticleSystem::StopEmission;
  - segurar um quadro de animação -> PauseAnimation + ChangeSprite (quadro); soltar -> PlayAnimation;
  - quebrar o piso: as ações de tile map (TileMap::TileMapBehavior::RemoveTileAtGridCoordinates e as expressões
    GridX, GridY, TileIdAtGrid, TileCenterX, TileCenterY). Os ataques comuns sorteiam células (até
    quantidade * quebra_tentativas sorteios) abaixo das quebra_topo_linhas de cima e quebram as que têm tile; a
    explosão grande passa por todas as células da zona;
  - pedaços (destroco): criados com Create e movidos por ações com as variáveis deles;
  - moedas do chefe: Para cada moeda recém-criada, sorteia uma ponte (escolha aleatória) e calcula o arco;
  - alvo do salto: Para cada ponte da zona guarda a mais perto do pato na horizontal.
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, F, DES, TM, PONTE, M = 'demonio_chefe', 'demonio_fumaca', 'destroco', 'tiles_inferno', 'tiles_inferno_ponte', 'moeda'
I, E = t59.I, t59.E
VARS_CHEFE = [('quebra_tentativas', 'number', 4),
              ('quebra_x0', 'number', 0), ('quebra_x1', 'number', 0), ('quebra_c0', 'number', 0), ('quebra_c1', 'number', 0),
              ('quebra_r0', 'number', 0), ('quebra_r1', 'number', 0), ('quebra_c', 'number', 0), ('quebra_r', 'number', 0),
              ('quebra_qtd', 'number', 0), ('quebra_feitas', 'number', 0),
              ('alvo_dist', 'number', 0), ('alvo_d', 'number', 0), ('alvo_x0', 'number', 0), ('alvo_x1', 'number', 0),
              ('alvo_y', 'number', 0), ('alvo_px', 'number', 0), ('moeda_t', 'number', 0), ('moeda_tx', 'number', 0), ('moeda_g', 'number', 0)]
VARS_DESTROCO = [('pedacos', 'number', 4)]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t71/' + '/'.join(p)))


def num(var, op, valor, dono=D):
    return I('SetNumberObjectVariable', dono, var, op, valor)


def cmp(a, op, b):
    return I('BuiltinCommonInstructions::CompareNumbers', a, op, b)


def repete(expr, conds, acts, subs=None):
    return {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': expr, 'conditions': conds,
            'actions': acts, 'events': subs or []}


def para_cada(obj, conds, acts, subs=None):
    return {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': conds, 'actions': acts,
            'events': subs or []}


def ou(*conds):
    return {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': list(conds)}


# --------------------------------------------------------------------- animação
def pausa(quadro):
    return [E([], [I('AnimatableCapability::AnimatableBehavior::PauseAnimation', D, 'Animation'),
                   I('ChangeSprite', D, '=', f'{D}.{quadro}')])]


def solta(quadro=None):
    acts = [I('ChangeSprite', D, '=', f'{D}.{quadro}')] if quadro else []
    return [E([], acts + [I('AnimatableCapability::AnimatableBehavior::PlayAnimation', D, 'Animation')])]


def segura_queda():
    return [E([], [I('AnimatableCapability::AnimatableBehavior::SetName', D, 'Animation', '=', '"explosao"'),
                   I('AnimatableCapability::AnimatableBehavior::PauseAnimation', D, 'Animation'),
                   I('ChangeSprite', D, '=', f'{D}.queda_quadro')])]


# --------------------------------------------------------------------- fumaça
def fumaca_continua():
    return [E([], [I('ParticleSystem::SetTank', F, '=', '-1'),
                   I('ParticleSystem::SetFlow', F, '=', f'{F}.fluxo_continuo'),
                   I('ParticleSystem::ZoneRadius', F, '=', f'{F}.raio')])]


def fumaca_para():
    return [E([], [I('ParticleSystem::StopEmission', F)])]


# --------------------------------------------------------------------- piso que quebra
TILE = lambda f, *a: f'{TM}.TileMap::{f}({", ".join(a)})'
C, R = f'{D}.quebra_c', f'{D}.quebra_r'


def solta_pedacos():
    """Pedaços do tile (quebra_c, quebra_r) que acabou de sair."""
    return repete('Variable(destroco_por_tile)', [], [
        I('Create', '', DES, TILE('TileCenterX', C, R), TILE('TileCenterY', C, R), ''),
        I('AnimatableCapability::AnimatableBehavior::SetIndex', DES, 'Animation', '=', f'RandomInRange(0, {DES}.pedacos - 1)'),
        I('SetXY', DES, '=', f'{TILE("TileCenterX", C, R)} - RandomFloatInRange(0, {DES}.Width())',
          '=', f'{TILE("TileCenterY", C, R)} - RandomFloatInRange(0, {DES}.Height())'),
        I('SetZOrder', DES, '=', f'{DES}.z'),
        I('SetAngle', DES, '=', 'RandomFloatInRange(0, 360)'),
        num('vx', '=', f'RandomFloatInRange(-1, 1) * {DES}.vel_x', DES),
        num('vy', '=', f'RandomFloatInRange({DES}.vel_y_min, {DES}.vel_y_max)', DES),
        num('va', '=', f'RandomFloatInRange(-1, 1) * {DES}.giro', DES)])


def tira_tile():
    return [I('TileMap::TileMapBehavior::RemoveTileAtGridCoordinates', TM, 'TileMap', C, R)]


def solido():
    return cmp(TILE('TileIdAtGrid', C, R), '>=', '0')


def grade(x0, x1, topo):
    """Células da zona entre x0 e x1 (já dentro da zona), abaixo de topo linhas do topo do piso."""
    y0, y1 = 'Variable(quebra_y_min)', 'Variable(quebra_y_max) - 1'
    return [num('quebra_x0', '=', x0), num('quebra_x1', '=', x1),
            num('quebra_c0', '=', TILE('GridX', f'{D}.quebra_x0', y0)),
            num('quebra_c1', '=', TILE('GridX', f'{D}.quebra_x1', y0)),
            num('quebra_r0', '=', f'{TILE("GridY", f"{D}.quebra_x0", y0)} + {topo}'),
            num('quebra_r1', '=', TILE('GridY', f'{D}.quebra_x0', y1))]


def quebra_em_volta(dx, raio, qtd):
    cx = f'{D}.CenterX() + {dx}'
    return [E([], grade(f'max({cx} - {D}.{raio}, Variable(quebra_x_min))',
                        f'min({cx} + {D}.{raio}, Variable(quebra_x_max) - 1)', 'Variable(quebra_topo_linhas)')
              + [num('quebra_qtd', '=', f'{D}.{qtd}'), num('quebra_feitas', '=', '0')], [
        repete(f'{D}.quebra_qtd * {D}.quebra_tentativas',
               [cmp(f'{D}.quebra_x1', '>=', f'{D}.quebra_x0'), cmp(f'{D}.quebra_r1', '>=', f'{D}.quebra_r0')],
               [num('quebra_c', '=', f'RandomInRange({D}.quebra_c0, {D}.quebra_c1)'),
                num('quebra_r', '=', f'RandomInRange({D}.quebra_r0, {D}.quebra_r1)')], [
            E([cmp(f'{D}.quebra_feitas', '<', f'{D}.quebra_qtd'), solido()],
              tira_tile() + [num('quebra_feitas', '+', '1')], [solta_pedacos()])]),
    ])]


def quebra_tudo():
    return [E([], grade('Variable(quebra_x_min)', 'Variable(quebra_x_max) - 1', '0')
              + [num('quebra_c', '=', f'{D}.quebra_c0')], [
        repete(f'{D}.quebra_c1 - {D}.quebra_c0 + 1', [], [num('quebra_r', '=', f'{D}.quebra_r0')], [
            repete(f'{D}.quebra_r1 - {D}.quebra_r0 + 1', [], [], [
                E([solido()], tira_tile(), [solta_pedacos()]),
                E([], [num('quebra_r', '+', '1')])]),
            E([], [num('quebra_c', '+', '1')])]),
    ])]


def move_pedacos():
    return [E([], [num('vy', '+', f'{DES}.gravidade * TimeDelta()', DES),
                   I('SetX', DES, '+', f'{DES}.vx * TimeDelta()'),
                   I('SetY', DES, '+', f'{DES}.vy * TimeDelta()'),
                   I('SetAngle', DES, '+', f'{DES}.va * TimeDelta()')]),
            E([I('PosY', DES, '>', f'{DES}.fundo_y')], [I('Delete', DES, '')])]


# --------------------------------------------------------------------- pontes
def na_zona():
    return [I('PosX', PONTE, '>=', 'Variable(quebra_x_min)'), I('PosX', PONTE, '<', 'Variable(quebra_x_max)')]


def alvo_na_ponte():
    px = 'pato.CenterX()'
    return [
        E([], [num('alvo_dist', '=', '-1')]),
        para_cada(PONTE, na_zona(),
                  [num('alvo_d', '=', f'max(max({PONTE}.X() - {px}, {px} - {PONTE}.X() - {PONTE}.Width()), 0)')], [
            E([ou(cmp(f'{D}.alvo_dist', '<', '0'), cmp(f'{D}.alvo_d', '<', f'{D}.alvo_dist'))],
              [num('alvo_dist', '=', f'{D}.alvo_d'), num('alvo_x0', '=', f'{PONTE}.X()'),
               num('alvo_x1', '=', f'{PONTE}.X() + {PONTE}.Width()'), num('alvo_y', '=', f'{PONTE}.Y()')])]),
        E([cmp(f'{D}.alvo_dist', '>=', '0')], [num('alvo_px', '=', f'clamp({px}, {D}.alvo_x0, {D}.alvo_x1)')], [
            E([cmp(f'{D}.alvo_px', '!=', f'{D}.CenterX()')], [num('direcao', '=', f'sign({D}.alvo_px - {D}.CenterX())')]),
            E([], [num('lava_x1', '=', f'clamp({D}.alvo_px - {D}.direcao * {D}.lava_golpe_dx, '
                                       f'Variable(quebra_x_min) + {D}.lava_borda, Variable(quebra_x_max) - {D}.lava_borda)'),
                   num('lava_y1', '=', f'{D}.alvo_y - {D}.Height() + {D}.lava_golpe_baixo')])]),
    ]


def moedas_nas_pontes():
    t = f'{D}.moeda_t'
    return [para_cada(M, [I('CompareObjectTimer', M, '"vida"', '<=', '0')], [], [
        E(na_zona() + [I('AjoutHasard', '', PONTE)],
          [num('moeda_t', '=', f'RandomFloatInRange({D}.moedas_ponte_tempo_min, {D}.moedas_ponte_tempo_max)'),
           num('moeda_tx', '=', f'RandomFloatInRange({PONTE}.X(), {PONTE}.X() + {PONTE}.Width() - {M}.Width())'),
           num('moeda_g', '=', f'{M}.gravidade'),
           num('vx', '=', f'({D}.moeda_tx - {M}.X()) / {t}', M),
           num('vy', '=', f'({PONTE}.Y() - {M}.Height() - {M}.Y()) / {t} - {D}.moeda_g * {t} / 2', M),
           I('SetBooleanObjectVariable', M, 'alvo_ponte', 'True', ''),
           num('ponte_y', '=', f'{PONTE}.Y()', M),
           num('ponte_x0', '=', f'{PONTE}.X()', M),
           num('ponte_x1', '=', f'{PONTE}.X() + {PONTE}.Width()', M)])])]


# --------------------------------------------------------------------- troca
def codigo(e):
    c = e['inlineCode']
    return c if isinstance(c, str) else '\n'.join(c)


def troca_por(c):
    """Eventos que fazem o mesmo que o bloco JS c."""
    if 'setTank(-1)' in c:
        return fumaca_continua()
    if 'stopEmission' in c:
        return fumaca_para()
    if 'quebra(cx' in c and 'golpe_quebra_dx' in c:
        return quebra_em_volta(f'{D}.direcao * {D}.golpe_quebra_dx', 'golpe_quebra_raio', 'golpe_quebra_qtd')
    if 'quebra(cx' in c and 'explosao_quebra_raio' in c:
        return quebra_em_volta('0', 'explosao_quebra_raio', 'explosao_quebra_qtd')
    if 'Infinity, 0)' in c:
        return quebra_tudo()
    if 'queda_quadro' in c:
        return segura_queda()
    if 'o cutelo bate' in c:
        return solta('lava_quadro')
    if 'pauseAnimation' in c and 'lava_quadro' in c:
        return pausa('lava_quadro')
    if 'pauseAnimation' in c and 'rajada_quadro' in c:
        return pausa('rajada_quadro')
    if c.strip() == 'for (const b of objects) b.resumeAnimation();':
        return solta()
    if 'getObjects("destroco")' in c and 'gravidade' in c:
        return move_pedacos()
    if '// o salto sempre cai numa ponte' in c:
        return alvo_na_ponte()
    if 'relança as moedas' in c:
        return moedas_nas_pontes()
    raise ValueError('bloco JS sem tradução: ' + c[:80])


def troca(evs):
    i = 0
    while i < len(evs):
        e = evs[i]
        if e['type'] == 'BuiltinCommonInstructions::JsCode':
            novos = troca_por(codigo(e))
            evs[i:i + 1] = novos
            i += len(novos)
            continue
        if e.get('events'):
            troca(e['events'])
        i += 1


def variaveis(lista, dono, existentes):
    tem = {v['name'] for v in existentes}
    for n, t, v in lista:
        if n not in tem:
            existentes.append({'name': n, 'persistentUuid': uid(dono, n), 'type': t, 'value': v})


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    variaveis(VARS_CHEFE, D, objs[D]['variables'])
    variaveis(VARS_DESTROCO, DES, objs[DES]['variables'])
    troca(next(x for x in d['externalEvents'] if x['name'] == 'Chefe')['events'])


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
