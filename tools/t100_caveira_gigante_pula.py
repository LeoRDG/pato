"""Tarefa 100: a caveira gigante voa num oito em cima do pato e despenca nele, como um chefe do TBoI.

Antes ela andava a velocidade 60 (quase parada), virava para o lado errado (o desenho olha para a esquerda e
sprite_esquerda era False) e tomava tranco de bala. Agora:
- vira para o pato (sprite_esquerda = True) e é firme sempre (sem tranco; a espiral não tira mais o firme);
- perseguindo, voa (o PlatformerObject fica desligado): percorre um oito deitado (símbolo do infinito) em volta de um
  centro voo_alt px acima do pato; o centro segue o pato com voo_seguir, a fase anda voo_vel rad/s, o oito tem voo_larg
  px de meia largura e voo_amp px de meia altura, e ela desliza até o ponto do oito com voo_suave;
- despencar: vendo o pato, acima dele e a menos de slam_janela px na horizontal, a cada slam_espera s para e pisca por
  slam_aviso s, e cai reto a slam_vel px/s até o chão embaixo do pato (raio para baixo até slam_busca px; sem chão,
  a altura do pé do pato; no máximo slam_tempo_max s). Ao bater toca "ataque" (o fogo saindo de baixo), poeira e um
  anel de anel_qtd bolas de fogo a anel_vel (anel_dano cada); no fim da animação volta a voar (sobe deslizando);
- patrulhando (perdeu o pato) ou morta, o PlatformerObject volta e ela cai no chão;
- a espiral continua igual (parada no ar).
Variáveis novas na caveira_gigante: voo_t, voo_cx, voo_cy, voo_alt, voo_larg, voo_amp, voo_vel, voo_seguir, voo_suave,
slam_janela, slam_espera, slam_aviso, slam_vel, slam_busca, slam_tempo_max, chao_y, anel_qtd, anel_vel, anel_dano.
Rodar uma vez:  python3 tools/t100_caveira_gigante_pula.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 'caveira_gigante'
NOVAS = [('voo_t', 0), ('voo_cx', 0), ('voo_cy', 0), ('voo_alt', 450), ('voo_larg', 500), ('voo_amp', 130),
         ('voo_vel', 1.3), ('voo_seguir', 1.5), ('voo_suave', 4), ('slam_janela', 50), ('slam_espera', 3),
         ('slam_aviso', 0.4), ('slam_vel', 1500), ('slam_busca', 1500), ('slam_tempo_max', 2), ('chao_y', 0),
         ('anel_qtd', 12), ('anel_vel', 300), ('anel_dano', 12)]
NUM = 'BuiltinCommonInstructions::CompareNumbers'
P = 'PlatformerObject'


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def a(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def c(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def ev(conds, acoes, filhos=None, tipo='Standard', obj=None):
    e = {'type': 'BuiltinCommonInstructions::' + tipo, 'conditions': conds, 'actions': acoes}
    if obj:
        e['object'] = obj
    if filhos:
        e['events'] = filhos
    return e


EST = lambda s: c('StringObjectVariable', C, 'estado', '=', f'"{s}"')
NAO = lambda s: c('StringObjectVariable', C, 'estado', '!=', f'"{s}"')
PARA = lambda s: [a('SetStringObjectVariable', C, 'estado', '=', f'"{s}"'), a('ResetObjectTimer', C, '"estado"')]
VIVA = c('BooleanObjectVariable', C, 'morto', 'False', '')
V = lambda n: f'{C}.{n}'
SUAVE = f'(1 - exp(-{V("voo_suave")} * TimeDelta()))'
SEGUE = f'(1 - exp(-{V("voo_seguir")} * TimeDelta()))'
ALVO_X = f'{V("voo_cx")} + {V("voo_larg")} * sin({V("voo_t")})'
ALVO_Y = f'{V("voo_cy")} + {V("voo_amp")} * sin(2 * {V("voo_t")})'


def anel():
    p = 'projetil_inimigo'
    ang = f'RandomFloat(30) + {C}.i * 360 / max(1, {C}.anel_qtd)'
    return [ev([], [a('SetNumberObjectVariable', C, 'i', '=', '0')]),
            {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': f'{C}.anel_qtd', 'conditions': [], 'actions': [
                a('Create', '', p, f'{C}.CenterX()', f'{C}.Y() + {C}.Height() * 0.8', ''),
                a('AnimatableCapability::AnimatableBehavior::SetName', p, 'Animation', '=', '"fogo"'),
                a('SetXY', p, '=', f'{C}.CenterX() - {p}.Width() / 2', '=', f'{C}.Y() + {C}.Height() * 0.8 - {p}.Height() / 2'),
                a('AddForceAL', p, ang, f'{C}.anel_vel', '1'),
                a('SetAngle', p, '=', ang),
                a('SetNumberObjectVariable', p, 'dano', '=', f'{C}.anel_dano'),
                a('SetStringObjectVariable', p, 'origem', '=', f'"{C}"'),
                a('SetStringObjectVariable', p, 'tipo', '=', '"fogo"'),
                a('ResetObjectTimer', p, '"vida"'),
                a('SetNumberObjectVariable', p, 'ttl', '=', '4'),
                a('SetNumberObjectVariable', C, 'i', '+', '1')]}]


def voo():
    """Eventos novos, num "para cada" da caveira (cada uma voa no seu oito)."""
    voando = ev([NAO('patrulha')], [a('ActivateBehavior', C, P, 'no')])
    # no chão o centro do oito fica nela mesma: ao decolar sai de onde está e vai até o pato aos poucos
    pousada = ev([EST('patrulha')], [a('ActivateBehavior', C, P, 'yes'),
                                     a('SetNumberObjectVariable', C, 'voo_cx', '=', f'{C}.CenterX()'),
                                     a('SetNumberObjectVariable', C, 'voo_cy', '=', f'{C}.CenterY()'),
                                     a('SetNumberObjectVariable', C, 'voo_t', '=', '0')])
    oito = ev([EST('perseguir')], [
        a('SetNumberObjectVariable', C, 'voo_t', '+', f'{V("voo_vel")} * TimeDelta()'),
        a('SetNumberObjectVariable', C, 'voo_cx', '=', f'lerp({V("voo_cx")}, pato.CenterX(), {SEGUE})'),
        a('SetNumberObjectVariable', C, 'voo_cy', '=', f'lerp({V("voo_cy")}, pato.CenterY() - {V("voo_alt")}, {SEGUE})'),
        a('SetXY', C, '=', f'lerp({C}.X(), {ALVO_X} - {C}.Width() / 2, {SUAVE})',
          '=', f'lerp({C}.Y(), {ALVO_Y} - {C}.Height() / 2, {SUAVE})')])
    mira = ev([EST('perseguir'), c('CompareObjectTimer', C, '"ataque"', '>', V('slam_espera')),
               c('BooleanObjectVariable', C, 've_pato', 'True', ''),
               c(NUM, f'abs(pato.CenterX() - {C}.CenterX())', '<', V('slam_janela')),
               c(NUM, f'{C}.Y() + {C}.Height()', '<', 'pato.Y()')],
              PARA('preparar') + [a('PlaySound', '', 'som_aviso_caveira.wav', '', '70', 'RandomFloatInRange(0.95, 1.05)')])
    cai = ev([EST('preparar'), c('CompareObjectTimer', C, '"estado"', '>', V('slam_aviso'))],
             PARA('atacar') + [a('SetNumberObjectVariable', C, 'chao_y', '=', 'pato.Y() + pato.Height()')],
             [ev([c('RaycastToPosition', 'Terreno', 'pato.CenterX()', 'pato.CenterY()', 'pato.CenterX()',
                    f'pato.CenterY() + {V("slam_busca")}', 'visao_rx', 'visao_ry', '')],
                 [a('SetNumberObjectVariable', C, 'chao_y', '=', 'Variable(visao_ry)')])])
    descendo = ev([EST('atacar')], [a('SetXY', C, '+', '0', '+', f'{V("slam_vel")} * TimeDelta()')])
    bate = ev([EST('atacar'),
               {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
                   c(NUM, f'{C}.Y() + {C}.Height()', '>=', V('chao_y')),
                   c('CompareObjectTimer', C, '"estado"', '>', V('slam_tempo_max'))]}],
              PARA('pouso') + [a('SetXY', C, '=', f'{C}.X()', '=', f'min({C}.Y(), {V("chao_y")} - {C}.Height())'),
                               a('AnimatableCapability::AnimatableBehavior::SetName', C, 'Animation', '=', '"ataque"'),
                               a('PlaySound', '', 'som_fogo_caveira.wav', '', '80', '1'),
                               a('PlaySound', '', 'som_impacto.wav', '', '70', 'RandomFloatInRange(0.6, 0.7)'),
                               a('Create', '', 'poeira', f'{C}.CenterX()', f'{C}.Y() + {C}.Height()', '')],
              anel())
    volta = ev([EST('pouso'), c('AnimatableCapability::AnimatableBehavior::HasAnimationEnded', C, 'Animation')],
               PARA('perseguir') + [a('ResetObjectTimer', C, '"ataque"')])
    return ev([VIVA], [], [voando, pousada, oito, mira, cai, descendo, bate, volta], tipo='ForEach', obj=C)


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if f'{C}.voo_alt' in texto:
        sys.exit('t100 já foi aplicada; não roda de novo.')
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    g = next(e for e in todos(ini) if e.get('name') == 'Caveira gigante')

    modelo = next(e for e in todos(ini) if e['type'].endswith('Repeat'))
    assert 'repeatExpression' in modelo, list(modelo)

    # o evento "perseguir" anda até o pato: sai o andar, fica só a animação idle
    m = next(e for e in g['events'] if e['type'].endswith('Standard')
             and json.dumps(e['conditions']) == json.dumps([VIVA]))
    assert len(m['events']) == 1 and 'perseguir' in json.dumps(m['events'][0]['conditions']), 'caveira mudou'
    m['events'][0]['events'] = []

    k = g['events'].index(m) + 1
    g['events'].insert(k, voo())
    # morta: o PlatformerObject volta e ela cai
    g['events'].append(ev([c('BooleanObjectVariable', C, 'morto', 'True', '')], [a('ActivateBehavior', C, P, 'yes')]))

    for e in todos(g['events']):
        if e.get('actions'):
            e['actions'] = [x for x in e['actions'] if x['parameters'][:3] != [C, 'firme', 'False']]

    coms = [e for e in g['events'] if e['type'].endswith('Comment')]
    coms[0]['comment'] = ('Mini-boss firme (sem tranco). Perseguindo, voa num oito (infinito) em volta de um ponto voo_alt px '
                          'acima do pato (voo_larg, voo_amp, voo_vel, voo_seguir, voo_suave). Vendo o pato e passando em '
                          'cima dele (slam_janela), a cada slam_espera s pisca por slam_aviso s e despenca a slam_vel até '
                          'o chão: fogo embaixo e anel de anel_qtd bolas de fogo, e volta a voar. Patrulhando ou morta, '
                          'cai no chão. De espiral_espera em espiral_espera s, com o pato a menos de espiral_alcance, '
                          'para no ar e gira uma espiral de bolas de fogo por espiral_duracao s.')

    obj = next(o for o in d['objects'] if o['name'] == C)
    vs = {v['name']: v for v in obj['variables']}
    vs['sprite_esquerda']['value'] = True
    vs['firme']['value'] = True
    for nome, valor in NOVAS:
        if nome not in vs:
            obj['variables'].append({'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogos/t100/{nome}')),
                                     'type': 'number', 'value': valor})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('caveira gigante voa num oito e despenca no pato')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
