"""Tarefa 30: volta o giro de 360 graus, agora em todo pulo depois do primeiro (2º, 3º... se um dia houver mais pulos no ar).

- Gira quando um pulo sai no ar (CanJump e fora do chão), menos o pulo de coiote (que conta como o primeiro).
- O sentido é o do movimento; parado, o lado da mira (SENT_GIRO de t13).
- O alvo do tween é o múltiplo de 360 seguinte ao mais perto do ângulo atual: um pulo no meio de outro giro continua até
  fechar uma volta a mais, e o giro sempre termina em pé (com um alvo fixo de 360, o 3º pulo não giraria).
- Ao pousar (ou morto no chão) o tween é removido e o ângulo volta a 0. Gira em volta do centro do corpo (ponto central dos quadros).
Rodar:  python3 tools/t30_giro_pulo.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, C, E, PATH
from t13_pulo import SENT_GIRO

PL = ('pato', 'PlatformerObject')
ID = '"giroPulo"'


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def eh_giro(e):
    return any(a['parameters'][:3] == ['pato', 'Tween', ID] for a in e.get('actions', []))


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    mov = next(e for e in walk(jog['events']) if e.get('name') == 'Movimento')
    for e in walk(mov['events']):
        if e.get('events'):
            e['events'] = [x for x in e['events'] if not eh_giro(x)]
    mov['events'] = [x for x in mov['events'] if not eh_giro(x)]

    vivo = next(e for e in mov['events'] if any(c['parameters'][:2] == ['pato', 'morto'] for c in e.get('conditions', [])))
    i = next(k for k, x in enumerate(vivo['events']) if any(a['type']['value'] == 'PlatformBehavior::SimulateJumpKey' for a in x.get('actions', [])))
    vivo['events'].insert(i, E(
        [C('KeyFromTextJustPressed', '', '"Space"'), C('PlatformBehavior::CanJump', *PL),
         C('PlatformBehavior::IsOnFloor', *PL, inv=True), C('AdvancedJump::AdvancedJump::CanCoyoteJump', 'pato', 'AdvancedJump', '', inv=True)],
        [A('Tween::TweenBehavior::AddObjectAngleTween2', 'pato', 'Tween', ID, f'360 * (round(pato.Angle() / 360) + {SENT_GIRO})', '"linear"', '0.35', '')]))
    j = mov['events'].index(vivo)
    mov['events'].insert(j + 1, E(
        [C('PlatformBehavior::IsOnFloor', *PL), C('BuiltinCommonInstructions::Once')],
        [A('Tween::RemoveTween', 'pato', 'Tween', ID), A('SetAngle', 'pato', '=', '0')]))

    for e in walk(mov['events']):
        if e['type'] == 'BuiltinCommonInstructions::Comment' and e.get('comment', '').startswith('A/D andam') and 'giro de 360' not in e['comment']:
            e['comment'] = e['comment'].replace('Espaço pula.', 'Espaço pula. Todo pulo no ar (depois do primeiro) dá um giro de 360°, que volta a 0 ao pousar.')

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
