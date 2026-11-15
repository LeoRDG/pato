"""Tarefa 68: as moedas do demônio chefe morto na fase 2 caem nas pontes, não na lava.

Migração de uso único que só ADICIONA o que falta:
  - quando o demônio morre com fase2 ligada, as moedas que ele acabou de soltar (criadas neste quadro pelos eventos
    de morte do Combate) são relançadas em arco, cada uma para um ponto sorteado em cima de uma ponte sorteada
    (tiles_inferno_ponte dentro da faixa quebra_x_min..quebra_x_max), chegando lá em moedas_ponte_tempo_min a
    moedas_ponte_tempo_max s, com a gravidade da própria moeda;
  - essas moedas quicam no topo da ponte delas como quicam no chão (moeda.quique, moeda.atrito_x, moeda.parada_vy),
    sem escorregar para fora dela;
  - variáveis: demonio_chefe.moedas_ponte_tempo_min, moedas_ponte_tempo_max (ajustáveis) e moedas_lancadas; moeda.
    alvo_ponte, ponte_y, ponte_x0, ponte_x1 (de trabalho); grupo "Moedas do chefe" no fim dos eventos "Chefe".
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
import t59_demonio_chefe as t59

D, M, PONTE = 'demonio_chefe', 'moeda', 'tiles_inferno_ponte'
I, E, grupo = t59.I, t59.E, t59.grupo
VARS_CHEFE = [('moedas_ponte_tempo_min', 'number', 0.7), ('moedas_ponte_tempo_max', 'number', 1.2),
              ('moedas_lancadas', 'boolean', False)]
VARS_MOEDA = [('alvo_ponte', 'boolean', False), ('ponte_y', 'number', 0), ('ponte_x0', 'number', 0), ('ponte_x1', 'number', 0)]


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t68/' + '/'.join(p)))


LANCA = [
    '// relança as moedas que o demônio acabou de soltar (timer "vida" zerado neste quadro) para cima das pontes',
    'const cena = runtimeScene.getVariables();',
    'const n = (k) => cena.get(k).getAsNumber();',
    'const pontes = runtimeScene.getObjects("tiles_inferno_ponte").filter(',
    '  (p) => p.getX() >= n("quebra_x_min") && p.getX() + p.getWidth() <= n("quebra_x_max"));',
    'if (pontes.length === 0) return;',
    'const sorteio = (a, b) => a + Math.random() * (b - a);',
    'for (const b of objects) {',
    '  const bv = b.getVariables();',
    '  const tmin = bv.get("moedas_ponte_tempo_min").getAsNumber(), tmax = bv.get("moedas_ponte_tempo_max").getAsNumber();',
    '  for (const m of runtimeScene.getObjects("moeda")) {',
    '    if (m.getTimerElapsedTimeInSeconds("vida") > 0) continue;',
    '    const v = m.getVariables();',
    '    const p = pontes[Math.floor(Math.random() * pontes.length)];',
    '    const tx = sorteio(p.getX(), p.getX() + p.getWidth() - m.getWidth());',
    '    const ty = p.getY() - m.getHeight();',
    '    const t = sorteio(tmin, tmax);',
    '    const g = v.get("gravidade").getAsNumber();',
    '    v.get("vx").setNumber((tx - m.getX()) / t);',
    '    v.get("vy").setNumber((ty - m.getY()) / t - g * t / 2);',
    '    v.get("alvo_ponte").setBoolean(true);',
    '    v.get("ponte_y").setNumber(p.getY());',
    '    v.get("ponte_x0").setNumber(p.getX());',
    '    v.get("ponte_x1").setNumber(p.getX() + p.getWidth());',
    '  }',
    '}',
]


def eventos():
    return grupo('Moedas do chefe', [
        {'type': 'BuiltinCommonInstructions::Comment',
         'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
         'comment': 'Moedas do chefe: se ele morre na lava (fase 2), as moedas que solta voam para cima das pontes '
                    '(moedas_ponte_tempo_min/max s de voo) e quicam lá em vez de cair na lava.'},
        E([I('BooleanVariable', 'fase2', 'True', ''), I('BooleanObjectVariable', D, 'morto', 'True', ''),
           I('BooleanObjectVariable', D, 'moedas_lancadas', 'False', '')],
          [I('SetBooleanObjectVariable', D, 'moedas_lancadas', 'True', '')],
          [{'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': LANCA, 'parameterObjects': D,
            'useStrict': True, 'eventsSheetExpanded': False}]),
        E([I('BooleanObjectVariable', M, 'alvo_ponte', 'True', ''), I('BooleanObjectVariable', M, 'parada', 'False', ''),
           I('NumberObjectVariable', M, 'vy', '>', '0'),
           I('BuiltinCommonInstructions::CompareNumbers', f'{M}.Y() + {M}.Height()', '>=', f'{M}.ponte_y')],
          [I('SetY', M, '=', f'{M}.ponte_y - {M}.Height()'),
           I('SetX', M, '=', f'clamp({M}.X(), {M}.ponte_x0, {M}.ponte_x1 - {M}.Width())'),
           I('SetNumberObjectVariable', M, 'vy', '*', f'-{M}.quique'),
           I('SetNumberObjectVariable', M, 'vx', '*', f'{M}.atrito_x')],
          [E([I('NumberObjectVariable', M, 'vy', '>', f'-{M}.parada_vy')],
             [I('SetBooleanObjectVariable', M, 'parada', 'True', '')])]),
    ])


def variaveis(lista, dono, existentes):
    tem = {v['name'] for v in existentes}
    for n, t, v in lista:
        if n not in tem:
            existentes.append({'name': n, 'persistentUuid': uid(dono, n), 'type': t, 'value': v})


def migra(d):
    objs = {o['name']: o for o in d['objects']}
    variaveis(VARS_CHEFE, D, objs[D]['variables'])
    variaveis(VARS_MOEDA, M, objs[M]['variables'])
    ext = next(x for x in d['externalEvents'] if x['name'] == 'Chefe')
    if not any(e.get('name') == 'Moedas do chefe' for e in ext['events']):
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
