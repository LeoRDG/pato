"""Tarefa 201: uma sessão de placar por fase, com o tempo pausado fora dela.
- A sessão de uma fase vai de quando o pato entra nela até sair pelo portal final (aí ela é salva no placar, t199/t200).
- Sair pelo portal do meio da fase para o hub (ou morrer) pausa o tempo: placar.tempo_no_hub passa a falso (só muda se ainda
  estiver no padrão, verdadeiro). Ao voltar pelo ponto de volta, a sessão continua com o tempo que tinha.
- Cada fase guarda a própria sessão pausada (global corridas[fase]): ir do hub para outra fase não joga mais fora a sessão da
  primeira; ela fica guardada e volta quando o pato entra de novo naquela fase.
- O relógio do HUD mostra o tempo da sessão (global tempo_hud) enquanto o pato está na fase dela; fora disso, o tempo da cena.
Rodar uma vez:  python3 tools/t201_sessao_por_fase.py
"""
from gd_mig import *

TROCA = [
    'try {',
    '  // Sessão por fase (t201): a corrida da fase que o pato deixou fica guardada em corridas[fase] (pausada) e a da fase',
    '  // em que ele entra volta para corrida; se não houver, o evento seguinte começa uma nova.',
    '  const V = runtimeScene.getGame().getVariables();',
    '  const C = V.get("corrida");',
    '  const T = V.get("corridas");',
    '  const cena = runtimeScene.getName();',
    '  const antes = C.getChild("nivel").getAsString();',
    '  if (C.getChild("ativa").getAsBoolean() && antes !== cena) {',
    '    T.getChild(antes).fromJSObject(C.toJSObject());',
    '    C.getChild("ativa").setBoolean(false);',
    '  }',
    '  if (T.hasChild(cena) && T.getChild(cena).getChild("ativa").getAsBoolean()) {',
    '    C.fromJSObject(T.getChild(cena).toJSObject());',
    '    T.getChild(cena).getChild("ativa").setBoolean(false);',
    '  }',
    '} catch (e) { /* placar falhou: o jogo continua */ }',
]
NIVEIS = ('Inferno', 'Purgatorio', 'Paraiso')


def migra(d):
    ids = Ids('t201')
    if not any(v['name'] == 'corridas' for v in d['variables']):
        d['variables'].append({'name': 'corridas', 'persistentUuid': ids('var/global/corridas'), 'type': 'structure', 'children': [
            {'name': n, 'persistentUuid': ids(f'var/global/corridas/{n}'), 'type': 'structure',
             'children': [var(ids, f'global/corridas/{n}', 'ativa', False)]} for n in NIVEIS]})
    poe_vars(ids, d['variables'], 'global', [('tempo_hud', 0)])
    placar = next(v for v in d['variables'] if v['name'] == 'placar')
    t = next(c for c in placar['children'] if c['name'] == 'tempo_no_hub')
    if t['value'] is True:
        t['value'] = False

    g = acha(folha(d, 'Jogador')['events'], 'Corrida (placar)')
    comeca = next(e for e in g['events'] if any(a['parameters'][:2] == ['corrida.nova', 'True'] for a in e.get('actions', [])))
    comeca['events'].insert(0, {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': TROCA, 'parameterObjects': '',
                                'useStrict': True, 'eventsSheetExpanded': False})

    # HUD: o relógio mostra o tempo da sessão
    def procura(evs):
        for k, e in enumerate(evs):
            if any(a['parameters'][:1] == ['hud_tempo'] and 'TimerElapsedTime("tempo_cena")' in a['parameters'][3]
                   for a in e.get('actions', []) if len(a['parameters']) > 3):
                return evs, k
            r = procura(e.get('events', []))
            if r:
                return r
    evs, k = procura(folha(d, 'HUD')['events'])
    for a in evs[k]['actions']:
        if a['parameters'][:1] == ['hud_tempo'] and len(a['parameters']) > 3:
            a['parameters'][3] = a['parameters'][3].replace('TimerElapsedTime("tempo_cena")', 'GlobalVariable(tempo_hud)')
    evs.insert(k, ev([], [csetn('tempo_hud', '=', 'TimerElapsedTime("tempo_cena")')], [
        ev([cbol('corrida.ativa', True), X('StringVariable', 'corrida.nivel', '=', 'CurrentSceneName()')],
           [csetn('tempo_hud', '=', 'GlobalVariable(corrida.tempo)')])]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'corridas' for v in d['variables']), 't201')
