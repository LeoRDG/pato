"""Tarefa 13: giro só no segundo pulo (para a frente parado, ou no sentido em que o pato anda) e propulsor na direção do movimento.

Rodar:  python3 tools/t13_pulo.py        (pode rodar de novo)
Feche o projeto no GDevelop antes (ou reabra depois sem salvar), senão ele sobrescreve o jogo.json.
"""
import json, os, uuid

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json')
# 1 = as partículas vão na mesma direção do movimento do pato; -1 = no sentido oposto (jato saindo para trás)
SENTIDO = -1

VX = 'pato.PlatformerObject::CurrentSpeed()'
VY_PULO = '-pato.PlatformerObject::JumpSpeed()'
VY = 'pato.PlatformerObject::CurrentFallSpeed()'
# o -0.001 faz o vetor parado apontar para cima (e o jato para baixo) em vez de 0 graus
ang = lambda vy: f'AngleBetweenPositions(0, 0, {VX}, {vy} - 0.001)' + ('' if SENTIDO == 1 else ' + 180')
# sentido do giro: o do movimento; parado, o lado para onde o pato olha (a mira)
MOVENDO = f'min(1, floor(abs({VX}) / 20))'  # 1 se anda (>= 20 px/s), 0 se parado; o GDevelop não tem ?: nem comparação em expressão
SENT_GIRO = f'({MOVENDO} * sign({VX}) + (1 - {MOVENDO}) * sign(alvo.CenterX() - pato.CenterX() + 0.001))'


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events', []))


def cond(tipo, *p, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(p)}


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    jog = [e for e in d['externalEvents'] if e['name'] == 'Jogador'][0]
    for e in walk(jog['events']):
        conds = [c['type']['value'] for c in e.get('conditions', [])]
        acts = e.get('actions', [])
        # giro: era "no primeiro quadro do pulo" (jaGirou); agora só no pulo no ar (o segundo)
        if any(a['type']['value'] == 'Tween::TweenBehavior::AddObjectAngleTween2' for a in acts):
            e['conditions'] = [cond('KeyFromTextJustPressed', '', '"Space"'),
                               cond('PlatformBehavior::CanJump', 'pato', 'PlatformerObject'),
                               cond('PlatformBehavior::IsOnFloor', 'pato', 'PlatformerObject', inv=True)]
            e['actions'] = [{'type': {'value': 'Tween::TweenBehavior::AddObjectAngleTween2'},
                             'parameters': ['pato', 'Tween', '"giroPuloDuplo"', f'360 * {SENT_GIRO}', '"linear"', '0.35', '']}]
        # propulsor: ângulo do vetor de movimento (no pulo, o vetor do impulso do pulo)
        for a in acts:
            if a['type']['value'] == 'SetAngle' and a['parameters'][0] == 'propulsor':
                no_dash = 'KeyFromTextJustPressed' in conds
                a['parameters'][2] = ang(VY_PULO if no_dash else VY)
                e['actions'] = [x for x in e['actions'] if x['parameters'][:2] != ['propulsor', 'dash']]
                e['actions'].append({'type': {'value': 'SetNumberObjectVariable'},
                                     'parameters': ['propulsor', 'dash', '=', '0' if no_dash else '1']})
    # o jato dura mais (partículas vivem mais e o tanque esvazia em ~0,3 s) e o emissor acompanha o pato, sempre contra o movimento
    prop = [o for o in d['objects'] if o['name'] == 'propulsor'][0]
    prop.update(particleLifeTimeMin=0.3, particleLifeTimeMax=0.55, tank=60, flow=200)
    if not any(v['name'] == 'dash' for v in prop['variables']):
        prop['variables'].append({'name': 'dash', 'persistentUuid': str(uuid.uuid4()), 'type': 'number', 'value': 0})
    mov = [e for e in walk(jog['events']) if e.get('name') == 'Movimento'][0]
    mov['events'] = [e for e in mov['events'] if e.get('name') != 'Propulsor acompanha o pato']
    mov['events'].append({
        'type': 'BuiltinCommonInstructions::Group', 'name': 'Propulsor acompanha o pato', 'source': '', 'creationTime': 0,
        'colorR': 74, 'colorG': 176, 'colorB': 228, 'parameters': [], 'events': [{
            'type': 'BuiltinCommonInstructions::Standard', 'conditions': [], 'events': [], 'actions': [
                {'type': {'value': 'SetXY'}, 'parameters': ['propulsor', '=', 'pato.CenterX()', '=',
                                                            'pato.CenterY() + (1 - propulsor.dash) * (pato.Height() / 2 - 10)']},
                {'type': {'value': 'SetAngle'}, 'parameters': ['propulsor', '=', ang(VY)]}]}]})
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
