"""Tarefa 203: tela de resultado no fim de cada fase.
Ao sair pelo portal final (ou pela saída do Empíreo) com uma sessão em andamento, o jogo vai para a cena Resultado em vez
de ir direto para o hub. A cena:
- liga só o grupo "Corrida (placar)" do Jogador (link por grupo), que fecha a sessão, calcula os pontos e envia ao placar;
- mostra a fase, o tempo e os pontos (com aviso de recorde local), a conta dos pontos linha a linha e o estado do envio;
- mostra os dois placares globais da fase (mais rápidos e mais pontos, fim_tela.top_n linhas, o nome do jogador destacado)
  e a posição desta corrida em cada um; sem placar global (desligado, fora do ar ou corrida parcial) mostra o recorde local;
- volta para o hub da fase (resultado_volta) com Espaço, Enter, E ou clique, depois de fim_tela.espera segundos.
Posições, tamanhos e espaçamentos ficam em fim_tela.* (frações da largura da tela para as colunas); cores são as ui_cor_*.
Em janela mais estreita que fim_tela.ref_w, os tamanhos em pixels encolhem na mesma proporção.
O envio (t199/t200) passa a marcar corrida_fim.envio ("enviando", "ok", "erro", "parcial", "sem_placar") e o motivo de
recusa do servidor (corrida_fim.envio_erro). Sem nome, o jogador ganha um nome "Pato NNNN" (fica salvo com o progresso), para
os jogadores não se misturarem no placar.
Rodar uma vez:  python3 tools/t203_tela_de_resultado.py
"""
import copy
from gd_mig import *

NOMES = {'Inferno': 'INFERNO', 'Purgatorio': 'PURGATORIO', 'Paraiso': 'PARAISO'}
TELA = [
    ('ref_w', 1920), ('top_n', 8), ('espera', 1), ('y_titulo', 90), ('y_topo', 230), ('y_dica_base', 90),
    ('col_esq', 0.07), ('col_esq_w', 0.27), ('col_tempo', 0.42), ('col_pontos', 0.71), ('col_w', 0.24), ('col_nome_x', 64),
    ('tam_titulo', 56), ('tam_grande', 64), ('tam_rotulo', 22), ('tam_linha', 24), ('tam_dica', 22),
    ('gap_rotulo', 10), ('gap_bloco', 34), ('gap_tag', 18), ('tag_dy', 22), ('gap_tabela', 18), ('lin_h', 38),
]

DESENHA = [
    'try {',
    '  // Tela de resultado (t203): resultado da corrida (corrida_fim) e os placares da fase. Números em fim_tela.*, cores ui_cor_*.',
    '  const jogo = runtimeScene.getGame();',
    '  const V = jogo.getVariables();',
    '  const T = V.get("fim_tela");',
    '  const W = jogo.getGameResolutionWidth();',
    '  const H = jogo.getGameResolutionHeight();',
    '  // janela estreita (o jogo adapta a resolução): tamanhos e distâncias em pixels encolhem junto; frações e contagens não',
    '  const escala = Math.min(1, W / T.getChild("ref_w").getAsNumber());',
    '  const crus = ["top_n", "espera", "ref_w", "col_esq", "col_esq_w", "col_tempo", "col_pontos", "col_w"];',
    '  const n = (k) => T.getChild(k).getAsNumber() * (crus.includes(k) ? 1 : escala);',
    '  const cor = (k) => V.get(k).getAsString();',
    '  const F = V.get("corrida_fim").toJSObject();',
    '  const P = V.get("placar").toJSObject();',
    '  const fase = V.get("placar_niveis").getChild(F.nivel).toJSObject();',
    '  const st = runtimeScene.__fim || (runtimeScene.__fim = { t: 0, textos: {}, placar: null, pedido: false });',
    '  st.t += runtimeScene.getTimeManager().getElapsedTime() / 1000;',
    '  const usados = new Set();',
    '  const limpa = (s) => String(s).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toUpperCase();',
    '  const txt = (id, s, x, y, tam, c, alinha) => {',
    '    let o = st.textos[id];',
    '    if (!o) { o = runtimeScene.createObject("ui_txt"); st.textos[id] = o; }',
    '    usados.add(id);',
    '    o.setString(limpa(s));',
    '    o.setCharacterSize(tam);',
    '    o.setColor(c);',
    '    o.hide(false);',
    '    o.setX(alinha === "dir" ? x - o.getWidth() : alinha === "meio" ? x - o.getWidth() / 2 : x);',
    '    o.setY(y);',
    '    return o;',
    '  };',
    '  const tempo = (s) => { const m = Math.floor(s / 60); return String(m).padStart(2, "0") + ":" + (s - m * 60).toFixed(2).padStart(5, "0"); };',
    '  const pts = (v) => Math.round(v).toLocaleString("pt-BR");',
    '',
    '  txt("titulo", (fase.nome || F.nivel) + " CONCLUIDO", W / 2, n("y_titulo"), n("tam_titulo"), cor("ui_cor_ouro"), "meio");',
    '',
    '  // coluna da esquerda: tempo, pontos e a conta',
    '  const xe = W * n("col_esq");',
    '  let y = n("y_topo");',
    '  const grande = (id, rotulo, valor, recorde) => {',
    '    txt(id + "_r", rotulo, xe, y, n("tam_rotulo"), cor("ui_cor_rotulo"));',
    '    y += n("tam_rotulo") + n("gap_rotulo");',
    '    const o = txt(id + "_v", valor, xe, y, n("tam_grande"), cor("ui_cor_texto"));',
    '    if (recorde) txt(id + "_novo", "NOVO RECORDE", xe + o.getWidth() + n("gap_tag"), y + n("tag_dy"), n("tam_rotulo"), cor("ui_cor_verde"));',
    '    y += n("tam_grande") + n("gap_bloco");',
    '  };',
    '  grande("tempo", "TEMPO", tempo(F.tempo), F.recorde_tempo);',
    '  grande("pontos", "PONTOS", pts(F.pontos), F.recorde_pontos);',
    '  const conta = [',
    '    ["ABATES (" + F.abates + ")", F.pts_abates],',
    '    ["FASE CONCLUIDA", P.pts_conclusao],',
    '    ["BONUS DE TEMPO", Math.max(0, (fase.tempo_ref || 0) - F.tempo) * P.pts_segundo],',
    '    ["DANO RECEBIDO (" + F.dano + ")", -F.dano * P.pts_dano],',
    '    ["MORTES (" + F.mortes + ")", -F.mortes * P.pts_morte],',
    '  ];',
    '  if (F.idas_hub > 0 && P.pts_ida_hub > 0) conta.push(["IDAS AO HUB (" + F.idas_hub + ")", -F.idas_hub * P.pts_ida_hub]);',
    '  conta.forEach(([rotulo, v], i) => {',
    '    txt("conta_r" + i, rotulo, xe, y, n("tam_linha"), cor("ui_cor_rotulo"));',
    '    txt("conta_v" + i, (v < 0 ? "-" : "+") + pts(Math.abs(v)), xe + W * n("col_esq_w"), y, n("tam_linha"),',
    '      v < 0 ? cor("ui_cor_vermelho") : cor("ui_cor_verde"), "dir");',
    '    y += n("lin_h");',
    '  });',
    '  y += n("gap_bloco");',
    '',
    '  // estado do envio para o placar global',
    '  const url = V.get("placar_url").getAsString();',
    '  const estado = {',
    '    enviando: ["ENVIANDO PARA O PLACAR...", "ui_cor_dim"],',
    '    ok: ["PLACAR GLOBAL: #" + F.global_pos_tempo + " NO TEMPO, #" + F.global_pos_pontos + " NOS PONTOS", "ui_cor_creme"],',
    '    erro: ["NAO ENTROU NO PLACAR GLOBAL" + (F.envio_erro ? ": " + F.envio_erro : ""), "ui_cor_vermelho"],',
    '    parcial: ["SESSAO PARCIAL: NAO ENTRA NO PLACAR", "ui_cor_dim"],',
    '    sem_placar: ["PLACAR GLOBAL DESLIGADO", "ui_cor_dim"],',
    '  }[F.envio];',
    '  if (estado) txt("estado", estado[0], xe, y, n("tam_linha"), cor(estado[1]));',
    '',
    '  // placares da fase: pede quando o envio terminou (para esta corrida já aparecer)',
    '  if (url && !st.pedido && F.envio !== "enviando") {',
    '    st.pedido = true;',
    '    const pede = (tipo) => {',
    '      const lim = typeof AbortSignal !== "undefined" && AbortSignal.timeout ? { signal: AbortSignal.timeout(8000) } : {};',
    '      return fetch(url + "?nivel=" + encodeURIComponent(F.nivel) + "&tipo=" + tipo + "&n=" + n("top_n"), lim)',
    '        .then((r) => r.json()).then((j) => (j && Array.isArray(j.linhas) ? j.linhas : null)).catch(() => null);',
    '    };',
    '    Promise.all([pede("tempo"), pede("pontos")]).then(([a, b]) => { st.placar = { tempo: a, pontos: b }; }).catch(() => { st.placar = {}; });',
    '  }',
    '  const nome = V.get("jogador_nome").getAsString();',
    '  const local = V.get("recordes").getChild(F.nivel).toJSObject();',
    '  const coluna = (id, x0, titulo, linhas, valor, minha, minhaPos, recordeLocal) => {',
    '    let yy = n("y_topo");',
    '    const cw = W * n("col_w");',
    '    txt(id + "_t", titulo, x0, yy, n("tam_rotulo"), cor("ui_cor_ouro"));',
    '    yy += n("tam_rotulo") + n("gap_rotulo") + n("gap_tabela");',
    '    const linha = (k, a, b, c, corLinha, corPos) => {',
    '      txt(id + "_p" + k, a, x0, yy, n("tam_linha"), corPos || corLinha);',
    '      txt(id + "_n" + k, b, x0 + n("col_nome_x"), yy, n("tam_linha"), corLinha);',
    '      txt(id + "_v" + k, c, x0 + cw, yy, n("tam_linha"), corLinha, "dir");',
    '      yy += n("lin_h");',
    '    };',
    '    if (url && !st.placar) { txt(id + "_m", "CARREGANDO...", x0, yy, n("tam_linha"), cor("ui_cor_dim")); return; }',
    '    if (!linhas) {',
    '      linha("loc", "", "SEU RECORDE", recordeLocal, cor("ui_cor_texto"));',
    '      return;',
    '    }',
    '    if (!linhas.length) txt(id + "_m", "NINGUEM AINDA", x0, yy, n("tam_linha"), cor("ui_cor_dim"));',
    '    linhas.slice(0, n("top_n")).forEach((l, i) => {',
    '      const eu = l.nome === nome;',
    '      linha(i, "#" + l.posicao, l.nome, valor(l), eu ? cor("ui_cor_ouro") : cor("ui_cor_texto"), eu ? cor("ui_cor_ouro") : cor("ui_cor_dim"));',
    '    });',
    '    if (minhaPos > 0) {',
    '      yy += n("gap_tabela");',
    '      linha("eu", "#" + minhaPos, "ESTA CORRIDA", minha, cor("ui_cor_ouro"));',
    '    }',
    '  };',
    '  const pl = st.placar || {};',
    '  coluna("tab_tempo", W * n("col_tempo"), "MAIS RAPIDOS", pl.tempo, (l) => tempo(l.tempo), tempo(F.tempo), F.global_pos_tempo,',
    '    local.tempo > 0 ? tempo(local.tempo) : "-");',
    '  coluna("tab_pontos", W * n("col_pontos"), "MAIS PONTOS", pl.pontos, (l) => pts(l.pontos), pts(F.global_pontos || F.pontos),',
    '    F.global_pos_pontos, local.pontos > 0 ? pts(local.pontos) : "-");',
    '',
    '  if (st.t >= n("espera")) {',
    '    txt("dica", "ESPACO, ENTER OU CLIQUE PARA CONTINUAR", W / 2, H - n("y_dica_base"), n("tam_dica"), cor("ui_cor_dim"), "meio");',
    '  }',
    '  for (const id in st.textos) if (!usados.has(id)) st.textos[id].hide(true);',
    '} catch (e) { /* a tela falhou: a volta para o hub continua funcionando (evento seguinte) */ }',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def troca_js(linhas, velho, novo):
    texto = '\n'.join(linhas)
    assert velho in texto, velho
    return texto.replace(velho, novo).split('\n')


def migra(d):
    ids = Ids('t203')
    poe_vars(ids, d['variables'], 'global', [('resultado_volta', 'Hub')])
    if not any(v['name'] == 'fim_tela' for v in d['variables']):
        d['variables'].append({'name': 'fim_tela', 'persistentUuid': ids('var/global/fim_tela'), 'type': 'structure',
                               'children': [var(ids, 'global/fim_tela', k, v) for k, v in TELA]})
    for c in next(v for v in d['variables'] if v['name'] == 'placar_niveis')['children']:
        poe_vars(ids, c['children'], f'placar_niveis/{c["name"]}', [('nome', NOMES.get(c['name'], c['name'].upper()))])
    fim = next(v for v in d['variables'] if v['name'] == 'corrida_fim')
    poe_vars(ids, fim['children'], 'corrida_fim', [('envio', ''), ('envio_erro', '')])

    # o envio marca o estado e dá um nome a quem ainda não tem
    g = acha(folha(d, 'Jogador')['events'], 'Corrida (placar)')
    envia = next(e for e in todos(g['events']) if e['type'].endswith('JsCode') and any('fetch(url, ' in l for l in e['inlineCode']))
    L = envia['inlineCode']
    L = troca_js(L, '  const url = V.get("placar_url").getAsString();\n',
                 '  const url = V.get("placar_url").getAsString();\n'
                 '  // estado do envio para a tela de resultado (t203); sem nome, o jogador ganha um "Pato NNNN"\n'
                 '  const FE = V.get("corrida_fim");\n'
                 '  FE.getChild("envio_erro").setString("");\n'
                 '  FE.getChild("envio").setString(!fim.valida ? "parcial" : url ? "enviando" : "sem_placar");\n'
                 '  if (url && !V.get("jogador_nome").getAsString()) V.get("jogador_nome").setString("Pato " + (1000 + Math.floor(Math.random() * 9000)));\n')
    L = troca_js(L, '        if (!j || j.ok !== true) return;',
                 '        if (!j || j.ok !== true) { FE.getChild("envio").setString("erro"); FE.getChild("envio_erro").setString(String((j && j.erro) || "")); return; }')
    L = troca_js(L, '        F.getChild("global_pos_pontos").setNumber(Number(j.posicao_pontos) || 0);\n      }).catch(() => {});',
                 '        F.getChild("global_pos_pontos").setNumber(Number(j.posicao_pontos) || 0);\n'
                 '        F.getChild("envio").setString("ok");\n'
                 '      }).catch(() => { FE.getChild("envio").setString("erro"); });')
    envia['inlineCode'] = L

    # fim da fase vai para a tela de resultado (a ação de cena do subevento vem depois e vale no lugar da do portal)
    entra = acha(folha(d, 'Portais')['events'], 'Entrar no portal')['events'][1]
    final = next(e for e in entra['events'] if any(c['parameters'][:3] == ['portal', 'final', 'True'] for c in e['conditions']))
    concl = next(e for e in final['events'] if any(a['parameters'][:2] == ['corrida.concluir', 'True'] for a in e['actions']))
    concl['actions'] += [X('SetStringVariable', 'resultado_volta', '=', 'portal.cena'), X('Scene', '', '"Resultado"', '')]
    saida = acha(cena(d, 'Paraiso')['events'], 'Saída no Empíreo')['events'][1]
    concl2 = next(e for e in saida['events'] if any(a['parameters'][:2] == ['corrida.concluir', 'True'] for a in e['actions']))
    concl2['actions'] += [X('SetStringVariable', 'resultado_volta', '=', 'proxima_cena'), X('Scene', '', '"Resultado"', '')]

    # a cena
    if not any(l['name'] == 'Resultado' for l in d['layouts']):
        r = copy.deepcopy(cena(d, 'Vitoria'))
        r.update({'name': 'Resultado', 'mangledName': 'Resultado', 'r': 14, 'v': 14, 'b': 18,
                  'objects': [], 'instances': [], 'variables': [], 'objectsGroups': []})
        # toda cena que liga o Jogador tem a variável hub (a volta de verdade é resultado_volta)
        poe_vars(ids, r['variables'], 'Resultado', [('hub', 'Hub')])
        sair = ev([cmp('TimeFromStart()', '>=', 'GlobalVariable(fim_tela.espera)'),
                   {'type': {'value': 'BuiltinCommonInstructions::Or'}, 'parameters': [], 'subInstructions': [
                       X('KeyFromTextReleased', '', '"Space"'), X('KeyFromTextReleased', '', '"Return"'),
                       X('KeyFromTextReleased', '', '"e"'), X('MouseButtonFromTextReleased', '', '"Left"')]}],
                  [X('Scene', '', 'GlobalVariableString(resultado_volta)', '')])
        r['events'] = [
            {'type': 'BuiltinCommonInstructions::Link', 'include': {'includeConfig': 1, 'eventsGroup': 'Corrida (placar)'},
             'target': 'Jogador'},
            grupo('Tela de resultado', [js(DESENHA)]),
            grupo('Voltar para o hub', [sair]),
        ]
        d['layouts'].append(r)


if __name__ == '__main__':
    roda(migra, lambda d: any(l['name'] == 'Resultado' for l in d['layouts']), 't203')
