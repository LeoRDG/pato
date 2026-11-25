"""Tarefa 200: o jogo pega um token do placar global no começo de cada corrida e manda junto no fim.
O servidor (servidor/, Cloudflare Worker + D1) assina o token com a hora dele; no envio ele confere que o tempo da corrida não
é menor que o tempo real que passou desde o token, e que cada token só entra uma vez. Sem placar_url nada muda.
- corrida.token (texto): zerado e pedido (POST <placar_url>/comecar {nivel}) quando uma corrida nova começa.
- O envio do fim (t199) passa a mandar o token.
- O placar nunca trava o jogo: todo evento JS do placar fica dentro de try/catch, as requisições são assíncronas (o jogo não
  espera) e têm limite de 8 s; sem resposta, sem token ou com erro, a corrida só não entra no placar global.
- A resposta do servidor (pontos e posição nos dois placares) vai para corrida_fim.global_pontos/global_pos_tempo/global_pos_pontos
  (0 enquanto não chega), para a tela de resultado usar.
Rodar uma vez:  python3 tools/t200_placar_token.py
"""
from gd_mig import *

PEDE = [
    '// Placar global (t200): pede o token da corrida assim que ela começa (o servidor guarda a hora do começo).',
    'const V = runtimeScene.getGame().getVariables();',
    'const C = V.get("corrida");',
    'C.getChild("token").setString("");',
    'const url = V.get("placar_url").getAsString();',
    'if (url) {',
    '  const nivel = C.getChild("nivel").getAsString();',
    '  const limite = typeof AbortSignal !== "undefined" && AbortSignal.timeout ? { signal: AbortSignal.timeout(8000) } : {};',
    '  fetch(url + "/comecar", Object.assign({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nivel }) }, limite))',
    '    .then((r) => r.json())',
    '    .then((j) => { if (j && typeof j.token === "string" && C.getChild("nivel").getAsString() === nivel) C.getChild("token").setString(j.token); })',
    '    .catch(() => {});',
    '}',
]


def migra(d):
    ids = Ids('t200')
    corrida = next(v for v in d['variables'] if v['name'] == 'corrida')
    poe_vars(ids, corrida['children'], 'corrida', [('token', '')])
    fim = next(v for v in d['variables'] if v['name'] == 'corrida_fim')
    poe_vars(ids, fim['children'], 'corrida_fim', [('global_pontos', 0), ('global_pos_tempo', 0), ('global_pos_pontos', 0)])

    g = acha(folha(d, 'Jogador')['events'], 'Corrida (placar)')
    comeca = next(e for e in g['events'] if '"corrida.nova", "True"' in json.dumps(e))
    nova = next(e for e in comeca['events'] if e['conditions'][0]['parameters'][:2] == ['corrida.nova', 'True'])
    nova['events'].append({'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': PEDE, 'parameterObjects': '',
                           'useStrict': True, 'eventsSheetExpanded': False})

    envia = next(e for e in todos(g['events']) if e['type'] == 'BuiltinCommonInstructions::JsCode'
                 and any('placar_url' in l and 'fetch' not in l for l in e['inlineCode']) and any('fetch(url' in l for l in e['inlineCode']))
    linhas = envia['inlineCode']
    i = next(k for k, l in enumerate(linhas) if 'upgrades: V.get("upgrades").toJSObject() }, fim);' in l)
    linhas[i] = linhas[i].replace('upgrades: V.get("upgrades").toJSObject() }, fim);',
                                  'upgrades: V.get("upgrades").toJSObject(), token: V.get("corrida").getChild("token").getAsString() }, fim);')
    j = next(k for k, l in enumerate(linhas) if 'fetch(url, ' in l)
    linhas[j] = linhas[j].replace('.catch(() => {});', '').replace(
        'fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) })',
        'fetch(url, Object.assign({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) }, limite))')
    linhas[j:j] = ['  const limite = typeof AbortSignal !== "undefined" && AbortSignal.timeout ? { signal: AbortSignal.timeout(8000) } : {};']
    j += 1
    linhas[j + 1:j + 1] = [
        '    .then((r) => r.json()).then((j) => {',
        '      if (!j || j.ok !== true) return;',
        '      const F = V.get("corrida_fim");',
        '      F.getChild("global_pontos").setNumber(Number(j.pontos) || 0);',
        '      F.getChild("global_pos_tempo").setNumber(Number(j.posicao_tempo) || 0);',
        '      F.getChild("global_pos_pontos").setNumber(Number(j.posicao_pontos) || 0);',
        '    }).catch(() => {});',
    ]
    # a resposta da corrida anterior não pode aparecer na nova
    k = next(k for k, l in enumerate(linhas) if 'const fim = ' in l)
    linhas[k + 1:k + 1] = ['for (const n of ["global_pontos", "global_pos_tempo", "global_pos_pontos"]) V.get("corrida_fim").getChild(n).setNumber(0);']

    # o placar nunca trava o jogo: qualquer erro dentro dos eventos JS do placar (fetch ausente, armazenamento bloqueado,
    # resposta estranha) fica preso aqui e o jogo segue; as requisições são assíncronas e têm limite de 8 s
    for e in todos(g['events']):
        if e['type'] == 'BuiltinCommonInstructions::JsCode' and e['inlineCode'][0] != 'try {':
            e['inlineCode'] = ['try {'] + ['  ' + l for l in e['inlineCode']] + ['} catch (e) { /* placar falhou: o jogo continua */ }']


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'token' for v in d['variables'] if v['name'] == 'corrida' for c in v['children']), 't200')
