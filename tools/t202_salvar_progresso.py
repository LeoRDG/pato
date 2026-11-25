"""Tarefa 202: o progresso fica salvo no navegador (localStorage, chave "pato_save").
Salvo: moedas (moedas_total), upgrades, armas liberadas, pontos de volta das fases (waypoints), mortes, mercador morto,
as sessões do placar (corrida e corridas, com o token) e o nome do jogador, mais o último hub (ultimo_hub).
- Quando salva: ao começar cada cena com o pato, a cada save_intervalo segundos (10) e quando a aba é escondida ou fechada.
- Quando carrega: uma vez, no Menu, antes de ir para o hub; o Menu vai para o último hub (ultimo_hub) em vez de sempre "Hub".
  O jogo continua começando com a pistola na mão (a arma atual não é salva).
- Jogo novo: abrir o jogo com ?novo no endereço apaga o save (os recordes do placar ficam).
- Salvar é opcional, como o placar: se o armazenamento estiver bloqueado ou o save estiver estragado, o jogo segue sem ele.
- Variáveis que não estão no save ficam com o valor do jogo.json (um upgrade novo, por exemplo, começa em 0).
Rodar uma vez:  python3 tools/t202_salvar_progresso.py
"""
from gd_mig import *

CHAVES = ['moedas_total', 'mortes', 'trader_morto', 'upgrades', 'armas', 'waypoints', 'corrida', 'corridas',
          'jogador_nome', 'ultimo_hub']
LISTA = '[' + ', '.join(f'"{k}"' for k in CHAVES) + ']'

CARREGA = [
    'try {',
    '  // Salvar progresso (t202): carrega o save uma vez, antes do primeiro hub. ?novo no endereço começa um jogo novo.',
    '  const jogo = runtimeScene.getGame();',
    '  const V = jogo.getVariables();',
    '  if (!jogo.__saveCarregado) {',
    '    jogo.__saveCarregado = true;',
    '    if (/[?&]novo(=|&|$)/.test(location.search)) {',
    '      localStorage.removeItem("pato_save");',
    '      // tira o ?novo do endereço: recarregar a página depois não apaga o save de novo',
    '      try { history.replaceState(null, "", location.pathname + location.hash); } catch (e) {}',
    '    }',
    '    const s = JSON.parse(localStorage.getItem("pato_save") || "null");',
    '    if (s && s.versao === 1) {',
    '      // estruturas: só os filhos que estão no save; o resto fica com o valor do jogo',
    '      const poe = (v, x) => {',
    '        if (x && typeof x === "object" && !Array.isArray(x)) { for (const k in x) poe(v.getChild(k), x[k]); }',
    '        else v.fromJSObject(x);',
    '      };',
    f'      for (const k of {LISTA}) if (k in s && k !== "ultimo_hub") poe(V.get(k), s[k]);',
    '      if (typeof s.ultimo_hub === "string" && jogo.hasScene(s.ultimo_hub)) V.get("ultimo_hub").setString(s.ultimo_hub);',
    '    }',
    '  }',
    '} catch (e) { /* save estragado ou armazenamento bloqueado: o jogo segue sem ele */ }',
]

SALVA = [
    'try {',
    '  // Salvar progresso (t202): ao começar cada cena, a cada save_intervalo s e quando a aba é escondida ou fechada.',
    '  const jogo = runtimeScene.getGame();',
    '  const V = jogo.getVariables();',
    '  const S = jogo.__save || (jogo.__save = { cena: null, t: 0 });',
    '  if (!S.salva) {',
    '    S.salva = () => {',
    '      try {',
    '        const o = { versao: 1 };',
    f'        for (const k of {LISTA}) if (V.has(k)) o[k] = V.get(k).toJSObject();',
    '        localStorage.setItem("pato_save", JSON.stringify(o));',
    '      } catch (e) {}',
    '    };',
    '    document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") S.salva(); });',
    '    window.addEventListener("pagehide", () => S.salva());',
    '  }',
    '  // o último hub: num hub, a variável de cena "hub" é o nome da própria cena',
    '  const cv = runtimeScene.getVariables();',
    '  if (cv.has("hub") && cv.get("hub").getAsString() === runtimeScene.getName()) V.get("ultimo_hub").setString(runtimeScene.getName());',
    '  S.t += runtimeScene.getTimeManager().getElapsedTime() / 1000;',
    '  if (S.cena !== runtimeScene || S.t >= V.get("save_intervalo").getAsNumber()) {',
    '    S.cena = runtimeScene;',
    '    S.t = 0;',
    '    S.salva();',
    '  }',
    '} catch (e) { /* sem armazenamento: o jogo segue sem salvar */ }',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def migra(d):
    ids = Ids('t202')
    poe_vars(ids, d['variables'], 'global', [('ultimo_hub', 'Hub'), ('save_intervalo', 10)])
    menu = cena(d, 'Menu')['events']
    menu.insert(0, grupo('Carregar progresso', [js(CARREGA)]))
    ir = acha(menu, 'Ir para o Hub')
    n = 0
    for e in todos(ir['events']):
        for a in e.get('actions', []):
            if a['type']['value'] == 'Scene' and a['parameters'][1] == '"Hub"':
                a['parameters'][1] = 'GlobalVariableString(ultimo_hub)'
                n += 1
    assert n == 1, n
    folha(d, 'Jogador')['events'].append(grupo('Salvar progresso', [js(SALVA)]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'save_intervalo' for v in d['variables']), 't202')
