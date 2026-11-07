"""Tarefa 14: sensação do pato sem animação (pulo com buffer, pulo curto, queda mais pesada, squash & stretch, poeira, aceleração).

Rodar:  python3 tools/t14_sensacao.py        (pode rodar de novo)
Feche o projeto no GDevelop antes (ou reabra depois sem salvar), senão ele sobrescreve o jogo.json.
Depois de rodar t13_pulo.py (os dois mexem nos eventos do pato).
"""
import copy, json, os, uuid
from t12_armas import A, C, E, comentario, grupo, procura, upsert

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json')
PL = ('pato', 'PlatformerObject')
VY = 'pato.PlatformerObject::CurrentFallSpeed()'
NOME = 'Sensação do pato'

noChao = lambda inv=False: C('PlatformBehavior::IsOnFloor', *PL, inv=inv)
setvar = lambda v, val: A('SetNumberObjectVariable', 'pato', v, '=', val)
poeira = lambda x, y, ang: [A('Create', '', 'poeira', x, y, ''), A('SetAngle', 'poeira', '=', ang)]
PE = ('pato.CenterX()', 'pato.Y() + pato.Height()')


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    obj = {o['name']: o for o in d['objects']}
    jog = [e for e in d['externalEvents'] if e['name'] == 'Jogador'][0]

    # ---------------------------------------------------------- poeira (copia o propulsor e muda o visual)
    if 'poeira' not in obj:
        p = copy.deepcopy(obj['propulsor'])
        p['persistentUuid'] = str(uuid.uuid4())
        d['objects'].append(p)
        pasta = [n for n in walk_pastas(d['objectsFolderStructure']) if any(c.get('objectName') == 'propulsor' for c in n['children'])][0]
        pasta['children'].append({'objectName': 'poeira'})
    else:
        p = obj['poeira']
    p.update(name='poeira', emitterAngleA=-25, emitterAngleB=25, emitterForceMin=120, emitterForceMax=280, flow=250, tank=10,
             particleLifeTimeMin=0.2, particleLifeTimeMax=0.4, zoneRadius=8, particleAlpha1=170, particleAlpha2=0,
             particleRed1=190, particleGreen1=175, particleBlue1=150, particleRed2=140, particleGreen2=130, particleBlue2=110,
             particleColor1='190;175;150', particleColor2='140;130;110', particleSize1=100, particleSize2=40, variables=[])

    # ---------------------------------------------------------- pato: variáveis e movimento
    for k in ('larg0', 'alt0', 'imp', 'ar', 'queda_vy', 'pe_y', 'cx'):
        upsert(obj['pato']['variables'], k, 0)
    upsert(obj['pato']['variables'], 'buf_ativo', False)
    mov = [b for b in obj['pato']['behaviors'] if b['type'] == 'PlatformBehavior::PlatformerObjectBehavior'][0]
    mov.update(acceleration=4200, deceleration=2600)

    # ---------------------------------------------------------- eventos
    ctrl = procura(jog['events'], 'Controle do Pato')
    ctrl['events'] = [e for e in ctrl['events'] if e.get('name') != NOME]
    ctrl['events'].append(grupo(NOME, [
        comentario('Pulo e queda: buffer de pulo (apertou até 0,12 s antes de pousar e o pulo sai no pouso), pulo curto ao soltar o Espaço '
                   'subindo e queda mais pesada (gravidade extra descendo, fora do dash).'),
        E([C('KeyFromTextJustPressed', '', '"Space"'), C('PlatformBehavior::CanJump', *PL, inv=True)],
          [setvar_b('buf_ativo', 'True'), A('ResetObjectTimer', 'pato', '"bufpulo"')]),
        E([C('BooleanObjectVariable', 'pato', 'buf_ativo', 'True', ''), C('CompareObjectTimer', 'pato', '"bufpulo"', '>', '0.12')],
          [setvar_b('buf_ativo', 'False')]),
        E([C('BooleanObjectVariable', 'pato', 'buf_ativo', 'True', ''), noChao(), C('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
          [A('PlatformBehavior::SimulateJumpKey', *PL), setvar_b('buf_ativo', 'False'), setvar('imp', '-0.2')]),
        E([C('KeyFromTextReleased', '', '"Space"'), C('BuiltinCommonInstructions::CompareNumbers', VY, '<', '-250')],
          [A('PlatformBehavior::SetCurrentFallSpeed', *PL, '=', f'{VY} * 0.45')]),
        E([C('PlatformBehavior::IsFalling', *PL), C('AdvancedJump::HorizontalDash::IsDashing', 'pato', 'HorizontalDash', '', inv=True)],
          [A('PlatformBehavior::SetCurrentFallSpeed', *PL, '=', f'min(700, {VY} + 1400 * TimeDelta())')]),

        comentario('Squash & stretch pelo tamanho do pato, ancorado nos pés: estica ao decolar e caindo rápido, achata ao pousar. '
                   'larg0/alt0 guardam o tamanho original; imp é o impulso (decai sozinho), ar o esticado do ar.'),
        E([C('SceneJustBegins', '')], [setvar('larg0', 'pato.Width()'), setvar('alt0', 'pato.Height()')]),
        E([noChao(inv=True)], [setvar('queda_vy', VY), setvar('ar', f'-0.1 * clamp(abs({VY}) / 800, 0, 1)')]),
        E([noChao()], [setvar('ar', '0')]),
        E([C('KeyFromTextJustPressed', '', '"Space"'), C('PlatformBehavior::CanJump', *PL)], [setvar('imp', '-0.2')],
          [E([noChao()], poeira(*PE, '270'))]),
        E([noChao(), C('BuiltinCommonInstructions::Once'), C('NumberObjectVariable', 'pato', 'queda_vy', '>', '250')],
          [setvar('imp', 'clamp(pato.queda_vy / 800, 0.3, 1) * 0.3')] + poeira(*PE, '200') + poeira(*PE, '340') + [setvar('queda_vy', '0')]),
        E([C('AdvancedJump::HorizontalDash::IsDashing', 'pato', 'HorizontalDash', ''), C('BuiltinCommonInstructions::Once'),
           noChao()], poeira(*PE, '90 + 90 * sign(pato.PlatformerObject::CurrentSpeed())')),
        E([C('BooleanObjectVariable', 'pato', 'morto', 'False', '')], [
            setvar('imp', 'pato.imp * pow(0.00005, TimeDelta())'),
            setvar('cx', 'pato.CenterX()'), setvar('pe_y', 'pato.Y() + pato.Height()'),
            A('ResizableCapability::ResizableBehavior::SetHeight', 'pato', 'Resizable', '=', 'pato.alt0 * (1 - clamp(pato.imp + pato.ar, -0.3, 0.35))'),
            A('ResizableCapability::ResizableBehavior::SetWidth', 'pato', 'Resizable', '=', 'pato.larg0 * (1 + 0.8 * clamp(pato.imp + pato.ar, -0.3, 0.35))'),
            A('SetXY', 'pato', '=', 'pato.cx - pato.Width() / 2', '=', 'pato.pe_y - pato.Height()'),
        ]),
    ]))

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


def setvar_b(nome, val):
    return A('SetBooleanObjectVariable', 'pato', nome, val, '')


def walk_pastas(n):
    yield n
    for c in n.get('children', []):
        if 'children' in c:
            yield from walk_pastas(c)


if __name__ == '__main__':
    main()
