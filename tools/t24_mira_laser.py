"""Tarefa 24: laser e mira batendo.

Antes: a arma girava na direção do `alvo` do quadro anterior (RotateTowardObject), a mira era posta no raio que sai do CENTRO
da arma, e o laser sai da BOCA (que fica um pouco acima/abaixo desse raio). Resultado: laser e mira desencontrados.
Agora, num só lugar e na ordem certa:
  1. o ângulo é calculado para que a linha do cano (deslocada bocal_f * altura do centro) passe exatamente pelo mouse:
     mira_a = ângulo(centro -> mouse) - asin(deslocamento / distância);
  2. a arma é posicionada e recebe esse ângulo direto (SetAngle), sem atraso;
  3. a boca do cano é calculada e a mira (alvo) fica sobre o laser, na distância do mouse: sem recuo ela fica no mouse;
     com recuo ela sobe junto com o laser (e as balas, que vão da boca até o alvo).
Rodar:  python3 tools/t24_mira_laser.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import A, PATH

DESLOC = 'Arma.bocal_f * Arma.Height()'
DCENTRO = 'DistanceBetweenPositions(Arma.CenterX(), Arma.CenterY(), MouseX(), MouseY())'
DBOCA = 'DistanceBetweenPositions(bocal_x, bocal_y, MouseX(), MouseY())'


OMBRO_X = 'pato.CenterX()'
OMBRO_Y = '(pato.Y() + pato.Height() * 0.68)'
RAIO = '(15 + 0.2 * Arma.Width())'
DOMBRO = f'DistanceBetweenPositions({OMBRO_X}, {OMBRO_Y}, MouseX(), MouseY())'


def acoes_posicao():
    # Mira livre (tarefa 28): a arma gira em volta de um "ombro" fixo no pato, então o ângulo não depende de onde a arma estava
    # no quadro anterior e cobre os 360 graus (o abs() em relação ao centro da arma, sobra do limite de ângulo, saiu).
    # Como o cano passa a RAIO do ombro ao longo da mira, a linha do cano fica deslocada só bocal_f * altura: o asin corrige isso.
    return [
        A('SetNumberVariable', 'mira_lado', '=', 'sign(MouseX() - pato.CenterX() + 0.001)'),
        A('SetNumberVariable', 'mira_a', '=', f'atan2(MouseY() - {OMBRO_Y}, mira_lado * (MouseX() - {OMBRO_X})) '
                                               f'- asin(clamp({DESLOC} / max({DOMBRO}, 1), -1, 1)) - ToRad(recuo)'),
        A('SetNumberVariable', 'mira_graus', '=', 'ToDeg(atan2(sin(mira_a), mira_lado * cos(mira_a)))'),
        A('SetNumberVariable', 'coice_j', '=', 'RandomFloatInRange(-1, 1) * Arma.tremor * clamp(coice / max(Arma.kick, 0.01), 0, 1)'),
        A('SetXY', 'Arma', '=', f'{OMBRO_X} + mira_lado * cos(mira_a) * ({RAIO} - coice) - sin(mira_a) * coice_j - Arma.Width() / 2', '=',
          f'{OMBRO_Y} + sin(mira_a) * ({RAIO} - coice) + mira_lado * cos(mira_a) * coice_j - Arma.Height() / 2'),
        A('SetAngle', 'Arma', '=', 'mira_graus'),
        A('SetZOrder', 'Arma', '=', 'pato.ZOrder() - 2'),
    ]


def acoes_mira():
    return [
        A('SetNumberVariable', 'bocal_x', '=', 'Arma.CenterX() + mira_lado * cos(mira_a) * Arma.Width() / 2 - mira_lado * sin(mira_a) * Arma.bocal_f * Arma.Height()'),
        A('SetNumberVariable', 'bocal_y', '=', 'Arma.CenterY() + sin(mira_a) * Arma.Width() / 2 + cos(mira_a) * Arma.bocal_f * Arma.Height()'),
        A('SetXY', 'alvo', '=', f'bocal_x + mira_lado * cos(mira_a) * {DBOCA} - alvo.Width() * .5', '=', f'bocal_y + sin(mira_a) * {DBOCA} - alvo.Height() * .5'),
        A('HideCursor', ''),
        A('SetNumberVariable', 'recuo', '*', 'pow(0.98, TimeDelta() * 60)'),
        A('SetNumberVariable', 'coice', '*', 'pow(0.000001, TimeDelta())'),
        A('OpacityCapability::OpacityBehavior::SetValue', 'alvo', 'Opacity', '=', '250'),
        A('SetNumberVariable', 'laser_x', '=', 'bocal_x + mira_lado * cos(mira_a) * 4000'),
        A('SetNumberVariable', 'laser_y', '=', 'bocal_y + sin(mira_a) * 4000'),
    ]


def aplica(jog):
    def anda(evs):
        for e in evs:
            yield e
            yield from anda(e.get('events') or [])
    todos = list(anda(jog))
    tem = lambda e, tipo, obj: any(a['type']['value'] == tipo and a['parameters'][0] == obj for a in e.get('actions') or [])
    pos = [e for e in todos if tem(e, 'SetXY', 'Arma')][0]
    mira = [e for e in todos if tem(e, 'SetXY', 'alvo')][0]
    pos['actions'] = acoes_posicao()
    mira['actions'] = acoes_mira()


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    aplica(next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events'])
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
