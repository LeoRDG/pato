"""Tarefa 28: tira de vez as animações falsas do pato e a sobra do limite de ângulo da mira.

Animações falsas (de antes do pato ter sprites animados) que ainda estavam nos eventos:
  - squash & stretch (t14): todo quadro mudava largura/altura do pato e o reposicionava com SetXY pelos pés, brigando com o
    comportamento de plataforma e com a máscara de colisão dos quadros. Saem as variáveis larg0, alt0, imp, ar, pe_y, cx.
    A poeira, o buffer de pulo, o pulo curto e a queda pesada ficam (queda_vy continua: decide a poeira do pouso).
  - giro de 360 graus no pulo duplo (t13/t15) e o "volta a 0 ao pousar" (com jaGirou).
  - pato deitado (ângulo 90) ao morrer: a animação Morte já faz isso.
Mira: a arma passa a girar em volta de um ombro fixo no pato (ver t24_mira_laser.acoes_posicao).

Rodar:  python3 tools/t28_sem_anim_falsa.py   (pode rodar de novo). Feche o projeto no GDevelop antes.
"""
import json
from t12_armas import PATH
from t24_mira_laser import aplica as mira_laser

VARS_FALSAS = ('larg0', 'alt0', 'imp', 'ar', 'pe_y', 'cx')


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events') or [])


def acao_falsa(a):
    t, p = a['type']['value'], a['parameters']
    if t == 'SetNumberObjectVariable' and p[0] == 'pato' and p[1] in VARS_FALSAS:
        return True
    if t.startswith('ResizableCapability::') and p[0] == 'pato':
        return True
    if t == 'SetXY' and p[0] == 'pato' and 'pe_y' in p[4]:
        return True
    if t == 'Tween::TweenBehavior::AddObjectAngleTween2' and p[0] == 'pato':
        return True
    if t == 'SetAngle' and p[0] == 'pato':
        return True
    if t == 'SetNumberVariable' and p[0] == 'jaGirou':
        return True
    return False


def limpa(evs):
    novos = []
    for e in evs:
        if e['type'] == 'BuiltinCommonInstructions::Comment' and e.get('comment', '').startswith('Squash & stretch'):
            continue
        tinha = bool(e.get('actions'))
        if 'actions' in e:
            e['actions'] = [a for a in e['actions'] if not acao_falsa(a)]
        if e.get('events'):
            e['events'] = limpa(e['events'])
        if tinha and not e.get('actions') and not e.get('events'):
            continue   # o evento só fazia animação falsa
        novos.append(e)
    return novos


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    jog = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')
    jog['events'] = limpa(jog['events'])
    for e in walk(jog['events']):
        if e['type'] == 'BuiltinCommonInstructions::Comment' and e.get('comment', '').startswith('A/D andam'):
            e['comment'] = e['comment'].replace(' Giro de 360° no pulo, que volta a 0 ao pousar.', '')
    mira_laser(jog['events'])

    pato = next(o for o in d['objects'] if o['name'] == 'pato')
    pato['variables'] = [v for v in pato['variables'] if v['name'] not in VARS_FALSAS]
    for lay in d['layouts']:
        lay['variables'] = [v for v in lay['variables'] if v['name'] != 'jaGirou']

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
