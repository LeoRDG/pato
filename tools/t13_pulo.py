"""Tarefa 13: giro só no segundo pulo (para a frente parado, ou no sentido em que o pato anda) e propulsor na direção do movimento.

Rodar:  python3 tools/t13_pulo.py        (pode rodar de novo)
Feche o projeto no GDevelop antes (ou reabra depois sem salvar), senão ele sobrescreve o jogo.json.
"""
import json, os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jogo.json')
# 1 = as partículas vão na mesma direção do movimento do pato; -1 = no sentido oposto (jato saindo para trás)
SENTIDO = 1

VX = 'pato.PlatformerObject::CurrentSpeed()'
VY_PULO = '-pato.PlatformerObject::JumpSpeed()'
VY = 'pato.PlatformerObject::CurrentFallSpeed()'
ang = lambda vy: f'AngleBetweenPositions(0, 0, {VX}, {vy})' + ('' if SENTIDO == 1 else ' + 180')
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
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
