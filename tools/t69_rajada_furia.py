"""Tarefa 69: em fúria, a explosão do demônio chefe vira uma rajada giratória de bolas de fogo.

Migração de uso único que só ADICIONA o que falta. Quando ele explode em fúria (golpe "explosao" com em_furia):
  - no auge (o mesmo disparo da explosão de sempre, que solta o anel de explosao_bolas) ele fica parado no quadro
    rajada_quadro da animação explosao por rajada_duracao s;
  - a cada rajada_espera s gira a saída rajada_giro graus e solta mais um anel de explosao_bolas (mesma velocidade e
    duração das bolas de sempre);
  - todas as bolas da rajada, inclusive o primeiro anel, tiram rajada_dano (menos que explosao_dano);
  - se ele morre no meio, a animação é solta para a morte tocar.
Fora da fúria a explosão continua igual. Variáveis no demonio_chefe: rajada_duracao, rajada_espera, rajada_giro,
rajada_dano, rajada_quadro (ajustáveis) e rajada_ativa, rajada_feita, rajada_angulo (de trabalho). Grupo
"Rajada da fúria" no fim dos eventos externos "Chefe".
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, B = 'demonio_chefe', 'bola_fogo'
I, E, grupo = t59.I, t59.E, t59.grupo
VARS_CHEFE = [('rajada_duracao', 'number', 2), ('rajada_espera', 'number', 0.25), ('rajada_giro', 'number', 15),
              ('rajada_dano', 'number', 10), ('rajada_quadro', 'number', 9),
              ('rajada_ativa', 'boolean', False), ('rajada_feita', 'boolean', False), ('rajada_angulo', 'number', 0)]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t69/' + '/'.join(p)))


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': D,
            'useStrict': True, 'eventsSheetExpanded': False}


SOLTA = js(['for (const b of objects) b.resumeAnimation();'])


def anel():
    ang = f'{D}.rajada_angulo + {D}.bola_i * 360 / {D}.explosao_bolas'
    return {'type': 'BuiltinCommonInstructions::Repeat', 'repeatExpression': f'{D}.explosao_bolas', 'conditions': [],
            'actions': [
                I('Create', '', B, f'{D}.CenterX()', f'{D}.CenterY()', ''),
                I('SetXY', B, '=', f'{D}.CenterX() + {D}.explosao_raio * cos(ToRad({ang})) - {B}.Width() / 2',
                  '=', f'{D}.CenterY() + {D}.explosao_raio * sin(ToRad({ang})) - {B}.Height() / 2'),
                I('AddForceAL', B, ang, f'{D}.explosao_vel', '1'),
                I('SetAngle', B, '=', ang),
                I('SetNumberObjectVariable', B, 'dano', '=', f'{D}.rajada_dano'),
                I('SetNumberObjectVariable', B, 'vida', '=', f'{D}.explosao_vida'),
                I('ResetObjectTimer', B, '"vida"'),
                I('SetNumberObjectVariable', D, 'bola_i', '+', '1')], 'events': []}


def eventos():
    ativa = lambda v: I('BooleanObjectVariable', D, 'rajada_ativa', v, '')
    return grupo('Rajada da fúria', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Rajada da fúria: em fúria a explosão segura o auge do fogo por rajada_duracao s e a cada rajada_espera s '
                    'gira rajada_giro graus e solta mais um anel de explosao_bolas; as bolas da rajada tiram rajada_dano.'},
        E([I('StringObjectVariable', D, 'estado', '!=', '"atacar"')],
          [I('SetBooleanObjectVariable', D, 'rajada_feita', 'False', '')]),
        # começa junto com o anel normal da explosão (que acabou de sair neste quadro)
        E([I('BooleanObjectVariable', D, 'em_furia', 'True', ''), I('BooleanObjectVariable', D, 'morto', 'False', ''),
           I('StringObjectVariable', D, 'estado', '=', '"atacar"'), I('StringObjectVariable', D, 'golpe', '=', '"explosao"'),
           I('BooleanObjectVariable', D, 'explosao_feita', 'True', ''), I('BooleanObjectVariable', D, 'rajada_feita', 'False', '')],
          [I('SetBooleanObjectVariable', D, 'rajada_feita', 'True', ''),
           I('SetBooleanObjectVariable', D, 'rajada_ativa', 'True', ''),
           I('ResetObjectTimer', D, '"rajada"'),
           I('ResetObjectTimer', D, '"rajada_tiro"'),
           I('SetNumberObjectVariable', D, 'rajada_angulo', '=', f'{D}.explosao_angulo')], [
            # o primeiro anel (o da explosão de sempre) também tira menos
            E([I('CompareObjectTimer', B, '"vida"', '<=', '0')],
              [I('SetNumberObjectVariable', B, 'dano', '=', f'{D}.rajada_dano')]),
        ]),
        E([ativa('True'), I('BooleanObjectVariable', D, 'morto', 'False', '')], [], [
            js(['// segura o auge do fogo enquanto a rajada dura',
                'for (const b of objects) {',
                '  b.pauseAnimation();',
                '  b.setAnimationFrame(b.getVariables().get("rajada_quadro").getAsNumber());',
                '}']),
            E([I('CompareObjectTimer', D, '"rajada_tiro"', '>', f'{D}.rajada_espera')],
              [I('ResetObjectTimer', D, '"rajada_tiro"'),
               I('SetNumberObjectVariable', D, 'rajada_angulo', '+', f'{D}.rajada_giro'),
               I('SetNumberObjectVariable', D, 'bola_i', '=', '0')],
              [anel()]),
            E([I('CompareObjectTimer', D, '"rajada"', '>', f'{D}.rajada_duracao')],
              [I('SetBooleanObjectVariable', D, 'rajada_ativa', 'False', '')], [SOLTA]),
        ]),
        # morreu no meio da rajada: solta a animação para a morte tocar
        E([ativa('True'), I('BooleanObjectVariable', D, 'morto', 'True', '')],
          [I('SetBooleanObjectVariable', D, 'rajada_ativa', 'False', '')], [SOLTA]),
    ])


def migra(d):
    boss = next(o for o in d['objects'] if o['name'] == D)
    tem = {v['name'] for v in boss['variables']}
    for n, t, v in VARS_CHEFE:
        if n not in tem:
            boss['variables'].append({'name': n, 'persistentUuid': uid(D, n), 'type': t, 'value': v})
    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not any(e.get('name') == 'Rajada da fúria' for e in ext['events']):
        ext['events'].append(eventos())


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
