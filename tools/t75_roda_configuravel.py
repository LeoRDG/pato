"""Tarefa 75: roda de troncos montada a partir de um item só.

Antes (tarefa 73) cada tronco da roda era uma plataforma_radial posta à mão, com o centro, o raio, a velocidade e o
ângulo repetidos em cada uma. Agora o item da roda é a pedra do centro, plataforma_radial_eixo: põe-se uma no editor,
no lugar do centro, e configura-se nela

    raio        distância do centro aos troncos (px)
    vel_ang     graus/s; positivo gira no sentido horário, negativo no anti-horário
    quantidade  quantos troncos (ficam igualmente espaçados)
    angulo      ângulo do primeiro tronco no começo (graus; 0 = à direita, 90 = embaixo)
    escala      tamanho dos troncos (1 = normal; 0.6 = os pequenos da escalada final)
    giro        quanto a pedra gira junto (1 = acompanha a roda)

No começo da cena cada pedra cria os seus troncos (plataforma_radial) e os cipós (plataforma_radial_corda); depois
os eventos põem cada tronco no ângulo `angulo` + indice * 360 / quantidade, a partir do centro da pedra. Como tudo é
lido a cada quadro, mudar raio, vel_ang ou angulo da pedra durante o jogo vale na hora.

Migração de uso único:
  - a pedra ganha raio, vel_ang, quantidade, angulo e escala; o tronco passa a ter só roda, indice e ancora_y; o cipó,
    roda e indice;
  - os eventos externos PlataformasRadiais passam a montar e girar as rodas a partir das pedras (só se ainda forem os
    da tarefa 73; se você mexeu neles, o script para sem mudar nada);
  - cada roda já posta no Purgatorio (troncos com o mesmo centro) vira uma pedra com os mesmos raio, velocidade,
    quantidade, ângulo de partida e escala, e os troncos soltos saem da cena; a variável de cena radial_i entra.
"""
import json, math, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t73_plataforma_radial as t73

P, C, X = 'plataforma_radial', 'plataforma_radial_corda', 'plataforma_radial_eixo'
VARS_X = {'raio': 320, 'vel_ang': 30, 'quantidade': 3, 'angulo': 0, 'escala': 1, 'giro': 1, 'id': 0}
VARS_P = {'roda': 0, 'indice': 0, 'ancora_y': 14}
VARS_C = {'roda': 0, 'indice': 0}
CENAS = ['Purgatorio']


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t75/' + '/'.join(p)))


def I(tipo, *params):
    return {'type': {'value': tipo}, 'parameters': list(params)}


def E(conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def para_cada(obj, conds, acts, subs=None):
    e = {'type': 'BuiltinCommonInstructions::ForEach', 'object': obj, 'conditions': conds, 'actions': acts}
    if subs:
        e['events'] = subs
    return e


def num(o, v, op, expr):
    return I('SetNumberObjectVariable', o, v, op, expr)


def da_roda(o):
    return I('NumberObjectVariable', X, 'id', '=', f'{o}.roda')


def ang(o):
    return f'ToRad({X}.angulo + {o}.indice * 360 / max(1, {X}.quantidade))'


def eventos():
    tam = lambda o, eixo, base: I(f'ResizableCapability::ResizableBehavior::Set{eixo}', o, 'Resizable', '=', f'{base} * {X}.escala')
    return [
        {'type': 'BuiltinCommonInstructions::Comment', 'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Rodas de troncos. O item da roda é a pedra do centro (plataforma_radial_eixo): no começo da cena '
                    'cada pedra cria `quantidade` troncos (plataforma_radial, do tamanho `escala`) e um cipó para cada '
                    'um. A cada quadro a pedra gira vel_ang graus/s (negativo = anti-horário) e cada tronco fica a `raio` '
                    'px do centro dela, no ângulo `angulo` + indice * 360 / quantidade, sempre de pé; a pedra gira junto '
                    'vezes `giro`.'},
        {'colorB': 228, 'colorG': 176, 'colorR': 74, 'creationTime': 0, 'name': 'Plataformas radiais', 'source': '',
         'type': 'BuiltinCommonInstructions::Group', 'parameters': [], 'events': [
            E([I('SceneJustBegins', '')], [], [
                para_cada(X, [], [I('SetNumberVariable', 'radial_n', '+', '1'), num(X, 'id', '=', 'radial_n'),
                                  I('SetNumberVariable', 'radial_i', '=', '0')], [
                    {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': f'{X}.quantidade',
                     'conditions': [], 'actions': [
                        I('Create', '', P, f'{X}.CenterX()', f'{X}.CenterY()', ''),
                        num(P, 'roda', '=', f'{X}.id'), num(P, 'indice', '=', 'radial_i'),
                        num(P, 'ancora_y', '*', f'{X}.escala'),
                        tam(P, 'Width', f'{P}.Width()'), tam(P, 'Height', f'{P}.Height()'),
                        I('SetZOrder', P, '=', f'{X}.ZOrder() + 2'),
                        I('Create', '', C, f'{X}.CenterX()', f'{X}.CenterY()', ''),
                        num(C, 'roda', '=', f'{X}.id'), num(C, 'indice', '=', 'radial_i'),
                        I('SetZOrder', C, '=', f'{X}.ZOrder() - 1'),
                        I('SetNumberVariable', 'radial_i', '+', '1')]},
                ]),
            ]),
            E([], [num(X, 'angulo', '+', f'{X}.vel_ang * TimeDelta()'), I('SetAngle', X, '=', f'{X}.angulo * {X}.giro')]),
            para_cada(P, [], [], [E([da_roda(P)], [
                I('SetXY', P, '=', f'{X}.CenterX() + {X}.raio * cos({ang(P)}) - {P}.Width() / 2',
                  '=', f'{X}.CenterY() + {X}.raio * sin({ang(P)}) - {P}.ancora_y')])]),
            para_cada(C, [], [], [E([da_roda(C)], [
                I('ResizableCapability::ResizableBehavior::SetWidth', C, 'Resizable', '=', f'{X}.raio'),
                I('SetXY', C, '=', f'{X}.CenterX() + {X}.raio * cos({ang(C)}) / 2 - {C}.Width() / 2',
                  '=', f'{X}.CenterY() + {X}.raio * sin({ang(C)}) / 2 - {C}.Height() / 2'),
                I('SetAngle', C, '=', f'ToDeg({ang(C)})')])]),
        ]},
    ]


def variaveis(nome, vs, antigas):
    """Variáveis novas do objeto; as que ficam (mesmo nome) mantêm o valor que já tinham."""
    velho = {v['name']: v for v in antigas}
    out = []
    for k, v in vs.items():
        if k in velho:
            out.append(velho[k])
        else:
            out.append({'name': k, 'persistentUuid': uid(nome, k), 'type': 'boolean' if isinstance(v, bool) else 'number',
                        'value': v})
    return out


def rodas_da_cena(cena, largura_normal, tam_eixo):
    """Agrupa os troncos soltos da tarefa 73 por roda e devolve as pedras que os substituem."""
    grupos = {}
    for i in cena['instances']:
        if i['name'] != P:
            continue
        v = {x['name']: x['value'] for x in i['initialVariables']}
        chave = (v.get('centro_x'), v.get('centro_y'), v.get('raio'), v.get('vel_ang'))
        grupos.setdefault(chave, []).append((v, i))
    pedras = []
    for (cx, cy, raio, vel), troncos in grupos.items():
        assert None not in (cx, cy, raio, vel), 'tronco sem centro: posto à mão depois da tarefa 73?'
        angulos = sorted(v.get('angulo', 0) % 360 for v, _ in troncos)
        passo = 360 / len(angulos)
        assert all(abs((a - angulos[0]) - k * passo) < 0.5 for k, a in enumerate(angulos)), ('troncos desiguais', cx, cy)
        _, inst = troncos[0]
        escala = round(inst['width'] / largura_normal, 3) if inst.get('customSize') else 1
        base = min(troncos, key=lambda t: t[1]['persistentUuid'])[1]
        pedras.append(({'angle': 0, 'customSize': False, 'depth': 1, 'height': 0, 'keepRatio': True, 'layer': '',
                        'name': X, 'persistentUuid': uid('roda', base['persistentUuid']), 'width': 0,
                        'x': round(cx - tam_eixo[0] / 2), 'y': round(cy - tam_eixo[1] / 2),
                        'zOrder': base['zOrder'] - 2, 'numberProperties': [], 'stringProperties': [],
                        'initialVariables': [{'name': k, 'persistentUuid': uid('roda', base['persistentUuid'], k),
                                              'type': 'number', 'value': val}
                                             for k, val in (('raio', raio), ('vel_ang', vel), ('quantidade', len(troncos)),
                                                            ('angulo', angulos[0]), ('escala', escala))]},
                       [i for _, i in troncos]))
    return pedras


def migra(d):
    ev = next(x for x in d['externalEvents'] if x['name'] == 'PlataformasRadiais')
    if ev['events'] == eventos():
        print('rodas já convertidas; nada feito')
        return False
    if ev['events'] != t73.eventos():
        sys.exit('os eventos PlataformasRadiais não são mais os da tarefa 73 (mexidos à mão?); nada foi mudado')
    obj = {o['name']: o for o in d['objects']}
    from PIL import Image
    tam_eixo = Image.open(os.path.join(RAIZ, t73.EIXO_IMG)).size
    largura = Image.open(os.path.join(RAIZ, t73.QUADROS[0])).size[0]
    for nome in CENAS:
        cena = next((l for l in d['layouts'] if l['name'] == nome), None)
        if cena is None:
            continue
        ja = {i['persistentUuid'] for i in cena['instances']}
        tirar = set()
        for pedra, troncos in rodas_da_cena(cena, largura, tam_eixo):
            if pedra['persistentUuid'] not in ja:
                cena['instances'].append(pedra)
            tirar.update(id(i) for i in troncos)
        cena['instances'] = [i for i in cena['instances'] if id(i) not in tirar]
        if not any(v['name'] == 'radial_i' for v in cena['variables']):
            cena['variables'].append({'name': 'radial_i', 'persistentUuid': uid(nome, 'radial_i'), 'type': 'number', 'value': 0})
    obj[X]['variables'] = variaveis(X, VARS_X, obj[X]['variables'])
    obj[P]['variables'] = variaveis(P, VARS_P, obj[P]['variables'])
    obj[C]['variables'] = variaveis(C, VARS_C, obj[C]['variables'])
    ev['events'] = eventos()
    return True


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    if not migra(d):
        return
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
