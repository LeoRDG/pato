"""Tarefa 62: fumaça vermelha saindo do demônio chefe enquanto ele está em fúria.

Migração de uso único que só ADICIONA o que falta (nada que já existe é alterado):
  - usa o emissor que já existe, demonio_fumaca (fumaça vermelha que sobe), sem mudar a configuração dele: quando o
    chefe entra em fúria, os eventos criam um demonio_fumaca e o deixam contínuo (tanque infinito) com
    fluxo_continuo partículas/s nascendo num círculo de raio px em volta do corpo, apontado para angulo graus;
    ele segue o centro do chefe (mais dy px), fica z_rel atrás dele e, quando o chefe morre (ou some), para de
    emitir e se apaga sozinho quando a última partícula some (destroyWhenNoParticles);
  - variáveis em demonio_fumaca: fluxo_continuo, raio, angulo, dy, z_rel (ajustáveis) e do_chefe, parando (de
    trabalho); em demonio_chefe: fumaca_criada (de trabalho);
  - grupo "Fumaça da fúria" no fim dos eventos externos "Chefe".
Obs.: o tamanho, a cor e a duração de cada partícula são os do próprio demonio_fumaca (edite no objeto).
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, F = 'demonio_chefe', 'demonio_fumaca'
VARS_FUMACA = [('fluxo_continuo', 'number', 70), ('raio', 'number', 70), ('angulo', 'number', -90), ('dy', 'number', 0),
               ('z_rel', 'number', -1), ('do_chefe', 'boolean', False), ('parando', 'boolean', False)]
VARS_CHEFE = [('fumaca_criada', 'boolean', False)]
I, E, grupo = t59.I, t59.E, t59.grupo


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t62/' + '/'.join(p)))


def js(linhas, objetos=F):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': objetos,
            'useStrict': True, 'eventsSheetExpanded': False}


def eventos():
    meu = I('BooleanObjectVariable', F, 'do_chefe', 'True', '')
    vivo = [I('SceneInstancesCount', '', D, '>', '0'), I('BooleanObjectVariable', D, 'morto', 'False', '')]
    para = [I('SetBooleanObjectVariable', F, 'parando', 'True', '')]
    parar = js(['// para de emitir; o emissor se apaga sozinho quando a última partícula some',
                'for (const o of objects) o.stopEmission();'])
    return grupo('Fumaça da fúria', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Fumaça da fúria: quando o demônio entra em fúria, cria um demonio_fumaca contínuo (fluxo_continuo, raio, '
                    'angulo, dy e z_rel ficam no demonio_fumaca) que segue o corpo dele; quando ele morre, a fumaça para e '
                    'some sozinha.'},
        E(vivo + [I('BooleanObjectVariable', D, 'em_furia', 'True', ''),
                  I('BooleanObjectVariable', D, 'fumaca_criada', 'False', '')],
          [I('SetBooleanObjectVariable', D, 'fumaca_criada', 'True', ''),
           I('Create', '', F, f'{D}.CenterX()', f'{D}.CenterY()', ''),
           I('SetXY', F, '=', f'{D}.CenterX()', '=', f'{D}.CenterY() + {F}.dy'),
           I('SetAngle', F, '=', f'{F}.angulo'),
           I('SetZOrder', F, '=', f'{D}.ZOrder() + {F}.z_rel'),
           I('SetBooleanObjectVariable', F, 'do_chefe', 'True', '')], [
            js(['// deixa o emissor contínuo, com o fluxo e o raio das variáveis dele',
                'for (const o of objects) {',
                '  const v = o.getVariables();',
                '  o.setTank(-1);',
                '  o.setFlow(v.get("fluxo_continuo").getAsNumber());',
                '  o.setZoneRadius(v.get("raio").getAsNumber());',
                '}']),
        ]),
        E([meu, I('BooleanObjectVariable', F, 'parando', 'False', '')] + vivo,
          [I('SetXY', F, '=', f'{D}.CenterX()', '=', f'{D}.CenterY() + {F}.dy'),
           I('SetZOrder', F, '=', f'{D}.ZOrder() + {F}.z_rel')]),
        E([meu, I('BooleanObjectVariable', F, 'parando', 'False', ''), I('SceneInstancesCount', '', D, '=', '0')],
          para, [parar]),
        E([meu, I('BooleanObjectVariable', F, 'parando', 'False', ''), I('BooleanObjectVariable', D, 'morto', 'True', '')],
          para, [parar]),
    ])


def variaveis(lista, dono, existentes):
    tem = {v['name'] for v in existentes}
    for n, t, v in lista:
        if n not in tem:
            existentes.append({'name': n, 'persistentUuid': uid(dono, n), 'type': t, 'value': v})


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    variaveis(VARS_FUMACA, F, objs[F].setdefault('variables', []))
    variaveis(VARS_CHEFE, D, objs[D]['variables'])
    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not any(e.get('name') == 'Fumaça da fúria' for e in ext['events']):
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
