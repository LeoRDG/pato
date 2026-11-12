"""Tarefa 15 (parte 2): troca o sprite do pato (patop.png) pelo pato amarelo animado (assets/pato_*.png) e liga as animações.

Rodar:  sh tools/t15_pato_sprites.sh   (gera os PNGs)   e depois   python3 tools/t15_pato_animacoes.py   (pode rodar de novo)
Feche o projeto no GDevelop antes (ou reabra depois sem salvar), senão ele sobrescreve o jogo.json.
Depois de rodar t13_pulo.py e t14_sensacao.py (usa o grupo "Controle do Pato").

Animações: Parado(4), Andar(4), Pulo(1), (o giro do pulo duplo é o tween de 360 graus de t13), Queda(1), Dano(2), Morte(1).
Todos os quadros têm 36x31 px (pés no fundo) e a mesma máscara de colisão (o corpo do pato parado), então a caixa não muda
entre quadros nem ao espelhar. Escala 5x: o corpo fica ~120x100 (antes 115x136).
"""
import json, os
from t13_pulo import SENT_GIRO
from t12_armas import A, C, E, comentario, grupo, procura, upsert

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'jogo.json')
PL = ('pato', 'PlatformerObject')
NOME = 'Animações do pato'
ESCALA = 5
LARG, ALT = 36 * ESCALA, 31 * ESCALA
MASCARA = [[{'x': 6, 'y': 11}, {'x': 30, 'y': 11}, {'x': 30, 'y': 31}, {'x': 6, 'y': 31}]]   # corpo do pato parado no recorte 36x31

ANIMS = [  # nome, quadros, segundos por quadro, repete
    ('Parado', ['idle_0', 'idle_1', 'idle_2', 'idle_3'], 0.18, True),
    ('Andar', ['walk_0', 'walk_1', 'walk_2', 'walk_3'], 0.09, True),
    ('Pulo', ['jump_0'], 0.1, False),
    ('Queda', ['fall_0'], 0.1, False),
    ('Dano', ['hit_0', 'hit_1'], 0.1, True),
    ('Morte', ['death_0'], 0.1, False),
]


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get('events', []))


def anim(nome, quadros, tempo, repete):
    return {'name': nome, 'useMultipleDirections': False, 'directions': [{
        'looping': repete, 'timeBetweenFrames': tempo,
        'sprites': [{'hasCustomCollisionMask': True, 'image': f'pato_{q}.png', 'points': [],
                     'originPoint': {'name': 'origine', 'x': 0, 'y': 0},
                     'centerPoint': {'automatic': False, 'name': 'centre', 'x': 18, 'y': 21},   # centro do corpo: o giro do pulo duplo gira em volta dele
                     'customCollisionMask': MASCARA} for q in quadros]}]}


def main():
    d = json.load(open(PATH, encoding='utf-8'))
    pato = [o for o in d['objects'] if o['name'] == 'pato'][0]
    pato['animations'] = [anim(*a) for a in ANIMS]

    # recursos (pixel art: sem suavização)
    res = d['resources']['resources']
    for _, quadros, _, _ in ANIMS:
        for q in quadros:
            nome = f'pato_{q}.png'
            r = {'file': f'assets/{nome}', 'kind': 'image', 'metadata': '', 'name': nome, 'smoothed': False, 'userAdded': False}
            res[:] = [x for x in res if x['name'] != nome] + [r]

    res[:] = [x for x in res if 'roll_1' not in x['name']]   # sobras da tentativa com a animação roll_1 (descartada)
    pato['variables'] = [v for v in pato['variables'] if v['name'] != 'girando']

    # instâncias: mesmo lugar (pés e centro), tamanho novo
    for lay in d['layouts']:
        for i in lay['instances']:
            if i['name'] == 'pato':
                cx, pe = i['x'] + i['width'] / 2, i['y'] + i['height']
                i.update(width=LARG, height=ALT, x=round(cx - LARG / 2), y=round(pe - ALT), customSize=True)

    # eventos
    jog = [e for e in d['externalEvents'] if e['name'] == 'Jogador'][0]
    ctrl = procura(jog['events'], 'Controle do Pato')
    ctrl['events'] = [e for e in ctrl['events'] if e.get('name') != NOME]
    anda = C('BuiltinCommonInstructions::CompareNumbers', 'abs(pato.PlatformerObject::CurrentSpeed())', '>', '20')
    ar = lambda: C('PlatformBehavior::IsOnFloor', *PL, inv=True)
    seta = lambda n: A('AnimatableCapability::AnimatableBehavior::SetName', 'pato', 'Animation', '=', f'"{n}"')
    morto = lambda v: C('BooleanObjectVariable', 'pato', 'morto', v, '')
    dano = [C('BooleanObjectVariable', 'pato', 'invencivel', 'True', ''), C('CompareObjectTimer', 'pato', '"iframes"', '<', '0.3')]
    # estados exclusivos: trocar de animação a cada quadro reiniciaria a animação (o Andar ficaria parado no 1º quadro)
    anda_nao = C('BuiltinCommonInstructions::CompareNumbers', 'abs(pato.PlatformerObject::CurrentSpeed())', '<=', '20')
    upsert(pato['variables'], 'em_dano', False)
    # pulo duplo: giro de 360 graus no ângulo (tween de t13), agora em volta do centro do corpo (ponto central dos quadros)
    for e in walk(jog['events']):
        if any(c['type']['value'] == 'AdvancedJump::AdvancedJump::CanCoyoteJump' for c in e.get('conditions', [])) and any(
                a['type']['value'] in ('Tween::TweenBehavior::AddObjectAngleTween2', 'SetBooleanObjectVariable') for a in e.get('actions', [])):
            e['actions'] = [A('Tween::TweenBehavior::AddObjectAngleTween2', 'pato', 'Tween', '"giroPuloDuplo"', f'360 * {SENT_GIRO}', '"linear"', '0.35', '')]
    edano = lambda v: C('BooleanObjectVariable', 'pato', 'em_dano', v, '')
    setb = lambda v: A('SetBooleanObjectVariable', 'pato', 'em_dano', v, '')
    ctrl['events'].append(grupo(NOME, [
        comentario('Animação do pato por estado. Os estados são exclusivos (morto > dano > no ar > andando > parado): '
                   'mandar a mesma animação todo quadro é ok, mas alternar entre duas reiniciaria os quadros. Espelhar fica no grupo Mira.'),
        E([], [setb('False')]),
        E(dano + [morto('False')], [setb('True')]),
        E([morto('True')], [seta('Morte')]),
        E([morto('False'), edano('True')], [seta('Dano')]),
        E([morto('False'), edano('False'), ar(), C('PlatformBehavior::IsJumping', *PL)], [seta('Pulo')]),
        E([morto('False'), edano('False'), ar(), C('PlatformBehavior::IsFalling', *PL)], [seta('Queda')]),
        E([morto('False'), edano('False'), C('PlatformBehavior::IsOnFloor', *PL), anda], [seta('Andar')]),
        E([morto('False'), edano('False'), C('PlatformBehavior::IsOnFloor', *PL), anda_nao], [seta('Parado')]),
    ]))
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
