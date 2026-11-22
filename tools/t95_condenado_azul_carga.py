"""Tarefa 95: a investida do condenado azul termina num soco.

Antes: ruge (idle piscando), corre tocando "ataque" (6 quadros, sem repetir) uma vez e desliza parado no último quadro,
machucando por encostar; começava a até 750 px do pato e só parava na parede ou depois de carga_tempo_max s.
Agora:
- aviso (preparar): ruge e pisca em idle por carga_aviso s, como antes;
- corrida (atacar): "andando" em loop acelerada por condenado_azul.carga_anim_vel (2.5), sem dano por encostar;
- chegou no pato (a menos de soco_alcance px na frente, |dy| < carga_alt): para e toca "ataque" (estado "socar",
  firme). Em soco_impacto s (o quadro do golpe) acerta se o pato ainda está a soco_alcance na frente: carga_dano e
  empurrão carga_empurrao. No fim da animação volta a perseguir;
- passou do pato por carga_passa px (300) no sentido da corrida: para e volta a perseguir;
- parede e carga_tempo_max continuam iguais; carga_alcance 750 -> 500 (valor inicial da t78, nunca mexido).
Fora da corrida (ou morto) a velocidade da animação volta a 1.
Rodar uma vez:  python3 tools/t95_condenado_azul_carga.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 'condenado_azul'
NOVAS = [('carga_anim_vel', 'number', 2.5), ('carga_passa', 'number', 300), ('soco_alcance', 'number', 170),
         ('soco_impacto', 'number', 0.16), ('soco_feito', 'boolean', False)]


def todos(evs):
    for e in evs:
        yield e
        yield from todos(e.get('events') or [])


def acao(tipo, *p):
    return {'type': {'value': tipo}, 'parameters': list(p)}


def cond(tipo, *p, inv=False):
    t = {'value': tipo}
    if inv:
        t['inverted'] = True
    return {'type': t, 'parameters': list(p)}


def ev(conds, acoes):
    return {'type': 'BuiltinCommonInstructions::Standard', 'conditions': conds, 'actions': acoes}


ANIM = 'AnimatableCapability::AnimatableBehavior::'
VEL = lambda v: acao(ANIM + 'SetSpeedScale', C, 'Animation', '=', v)
ESTADO = lambda s: cond('StringObjectVariable', C, 'estado', '=', f'"{s}"')
NA_FRENTE = f'{C}.direcao * (pato.CenterX() - {C}.CenterX())'


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if f'{C}.carga_passa' in texto:
        sys.exit('t95 já foi aplicada; não roda de novo.')
    ini = next(x for x in d['externalEvents'] if x['name'] == 'Inimigos')['events']
    g = next(e for e in todos(ini) if e.get('name') == 'Condenado azul (investida)')
    m = next(e for e in g['events'] if e['type'].endswith('Standard'))
    c = lambda e: json.dumps(e.get('conditions') or [], ensure_ascii=False)

    # corrida: andando acelerado
    corre = next(e for e in m['events'] if 'carga_aviso' in c(e))
    for a in corre['actions']:
        if a['type']['value'].endswith('SetName') and a['parameters'][0] == C:
            assert a['parameters'][3] == '"ataque"', a
            a['parameters'][3] = '"andando"'
    corre['actions'].append(VEL(f'{C}.carga_anim_vel'))

    # sai o dano por encostar na corrida; entra o soco ao chegar
    toque = next(e for e in m['events'] if 'CollisionNP' in c(e) and 'atacar' in c(e))
    k = m['events'].index(toque)
    m['events'][k:k + 1] = [
        ev([ESTADO('atacar'),
            cond('BuiltinCommonInstructions::CompareNumbers', NA_FRENTE, '>', '0'),
            cond('BuiltinCommonInstructions::CompareNumbers', NA_FRENTE, '<', f'{C}.soco_alcance'),
            cond('BuiltinCommonInstructions::CompareNumbers', f'abs(pato.CenterY() - {C}.CenterY())', '<', f'{C}.carga_alt')],
           [acao('SetStringObjectVariable', C, 'estado', '=', '"socar"'),
            acao('ResetObjectTimer', C, '"estado"'),
            acao('SetBooleanObjectVariable', C, 'soco_feito', 'False', ''),
            acao('SetBooleanObjectVariable', C, 'firme', 'True', ''),
            acao('PlatformBehavior::PlatformerObjectBehavior::SetCurrentSpeed', C, 'PlatformerObject', '=', '0'),
            acao(ANIM + 'SetName', C, 'Animation', '=', '"ataque"'),
            VEL('1')]),
        dict(ev([ESTADO('socar'),
                 cond('CompareObjectTimer', C, '"estado"', '>', f'{C}.soco_impacto'),
                 cond('BooleanObjectVariable', C, 'soco_feito', 'False', '')],
                [acao('SetBooleanObjectVariable', C, 'soco_feito', 'True', '')]),
             events=[ev([cond('BuiltinCommonInstructions::CompareNumbers', NA_FRENTE, '>', f'-{C}.Width() / 4'),
                         cond('BuiltinCommonInstructions::CompareNumbers', NA_FRENTE, '<', f'{C}.soco_alcance'),
                         cond('BuiltinCommonInstructions::CompareNumbers', f'abs(pato.CenterY() - {C}.CenterY())', '<',
                              f'{C}.carga_alt'),
                         cond('BooleanObjectVariable', 'pato', 'invencivel', 'False', ''),
                         cond('BooleanObjectVariable', 'pato', 'morto', 'False', '')],
                        [acao('SetNumberObjectVariable', 'pato', 'vida', '-', f'{C}.carga_dano'),
                         acao('SetBooleanObjectVariable', 'pato', 'invencivel', 'True', ''),
                         acao('ResetObjectTimer', 'pato', '"iframes"'),
                         acao('SetStringObjectVariable', 'pato', 'ultimo_agressor', '=', f'"{C}"'),
                         acao('SetNumberObjectVariable', 'pato', 'coice_vx', '=', f'{C}.direcao * {C}.carga_empurrao'),
                         acao('PlaySound', '', 'som_impacto.wav', '', '70', 'RandomFloatInRange(0.95, 1.05)')])]),
        ev([ESTADO('socar'), cond(ANIM + 'HasAnimationEnded', C, 'Animation')],
           [acao('SetStringObjectVariable', C, 'estado', '=', '"perseguir"'),
            acao('ResetObjectTimer', C, '"estado"'),
            acao('ResetObjectTimer', C, '"ataque"'),
            acao('SetBooleanObjectVariable', C, 'firme', 'False', '')]),
    ]

    # passou do pato: para
    k = m['events'].index(next(e for e in m['events'] if 'carga_tempo_max' in c(e)))
    m['events'].insert(k, ev([ESTADO('atacar'),
                              cond('BuiltinCommonInstructions::CompareNumbers',
                                   f'-{NA_FRENTE}', '>', f'{C}.carga_passa')],
                             [acao('SetStringObjectVariable', C, 'estado', '=', '"perseguir"'),
                              acao('ResetObjectTimer', C, '"estado"'),
                              acao('ResetObjectTimer', C, '"ataque"')]))
    g['events'].append(ev([{'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [],
                            'subInstructions': [cond('StringObjectVariable', C, 'estado', '!=', '"atacar"'),
                                                cond('BooleanObjectVariable', C, 'morto', 'True', '')]}],
                          [VEL('1')]))
    for e in g['events']:
        if e['type'].endswith('Comment'):
            e['comment'] = ('Alinhado com o pato (a menos de carga_alcance) ruge por carga_aviso s e corre em linha reta '
                            '(andando acelerado por carga_anim_vel). Chegando a soco_alcance px dele, para e dá o soco: '
                            'em soco_impacto s acerta carga_dano e joga longe (carga_empurrao). Passou carga_passa px do '
                            'pato ou durou carga_tempo_max s: volta a perseguir. Bateu numa parede: fica tonto e '
                            'inofensivo por atordoa_tempo s.')
            break

    obj = next(o for o in d['objects'] if o['name'] == C)
    vs = {v['name']: v for v in obj['variables']}
    if vs['carga_alcance']['value'] == 750:
        vs['carga_alcance']['value'] = 500
    for nome, tipo, valor in NOVAS:
        if nome not in vs:
            obj['variables'].append({'name': nome, 'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, f'jogos/t95/{nome}')),
                                     'type': tipo, 'value': valor})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('investida do condenado azul termina num soco')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
